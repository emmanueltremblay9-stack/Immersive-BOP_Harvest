"""Run an explicit disposable production-server qualification phase; never touch Prism."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, stat, subprocess, sys, time, tomllib, uuid, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.ci.prepare_runtime import validate_bytes, validate_lock, properties

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def guarded_directory(path: Path):
    """Reject linked ancestors and descendants before any launcher can write there."""
    for candidate in [path,*path.parents]:
        if candidate.exists() and (candidate.is_symlink() or getattr(candidate.lstat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError('Linked/reparse write path is forbidden')
    absolute=path.resolve()
    if path.exists():
        for candidate in path.rglob('*'):
            if candidate.is_symlink() or getattr(candidate.lstat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT or not candidate.resolve().is_relative_to(absolute):
                raise ValueError('Linked or escaping instance content is forbidden')
    return absolute

def candidate_version(candidate: Path):
    with zipfile.ZipFile(candidate) as archive:
        metadata=tomllib.loads(archive.read('META-INF/neoforge.mods.toml').decode())
    rows=[m for m in metadata['mods'] if m['modId']=='immersive_bop_harvest']
    if len(rows)!=1:raise ValueError('Ambiguous candidate identity')
    return rows[0]['version']

def validate_chain(phase: str, predecessor: Path | None, home: Path, candidate: Path, harness: Path, backup: Path | None):
    links={'baseline-restart':('baseline-create','0.1.1-alpha.9'),
           'candidate-upgrade':('baseline-restart','0.1.1-alpha.9'),
           'candidate-restart':('candidate-upgrade','0.1.1-alpha.10'),
           'multiplayer':('candidate-restart','0.1.1-alpha.10')}
    version=candidate_version(candidate)
    if version!=('0.1.1-alpha.9' if phase.startswith('baseline-') else '0.1.1-alpha.10'):raise ValueError('Phase candidate version mismatch')
    if phase=='baseline-create':
        if predecessor is not None or (home/'world').exists():raise ValueError('Baseline creation requires a fresh disposable world')
        return None,None
    if predecessor is None or not (home/'world/level.dat').is_file():raise ValueError('Continuation requires an existing world and predecessor receipt')
    previous=json.loads(predecessor.read_text());runtime=previous['runtime'];expected_phase,expected_version=links[phase]
    if (previous.get('passed') is not True or type(previous.get('exitCode')) is not int or previous['exitCode']!=0
            or previous.get('timeout') is not False or previous.get('aborted') is not False or runtime.get('phaseStatus')!='PASS'):raise ValueError('Predecessor did not pass')
    if runtime.get('phase')!=expected_phase or runtime.get('candidateVersion')!=expected_version or Path(previous['cwd']).resolve()!=home:raise ValueError('Wrong predecessor phase/version/instance')
    if digest(Path(previous['log']))!=previous['logSha256']:raise ValueError('Predecessor log bytes changed')
    old_plan=json.loads((home/'bop-qa-plan.json').read_text())
    if runtime['nonce']!=old_plan['nonce'] or runtime.get('saveCalled') is not True:raise ValueError('Stale predecessor or missing save')
    loaded={m['modId']:m for m in runtime['loadedJarIdentities']}
    if loaded['bop_harvest_qa']['sha256']!=digest(harness):raise ValueError('Harness changed inside comparable phase chain')
    if phase!='candidate-upgrade' and loaded['immersive_bop_harvest']['sha256']!=digest(candidate):raise ValueError('Candidate changed inside restart phase')
    binding={'path':str(predecessor.resolve()),'sha256':digest(predecessor),'phase':expected_phase,'nonce':runtime['nonce']}
    if phase=='candidate-upgrade':
        if backup is None:raise ValueError('Upgrade requires verified pre-upgrade backup')
        record=json.loads(backup.read_text());backup_dir=guarded_directory(Path(record['backup']))
        if Path(record['source']).resolve()!=home/'world':raise ValueError('Backup belongs to another world')
        world=(home/'world').resolve()
        if backup_dir.is_relative_to(world) or world.is_relative_to(backup_dir):raise ValueError('Backup must be a separate copy outside the active world')
        def inventory(root):return {p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file()}
        if (record.get('hashMatch') is not True or type(record.get('fileCount')) is not int or record['fileCount']!=len(record['sha256']) or not record['fileCount']
                or inventory(backup_dir)!=record['sha256'] or inventory(home/'world')!=record['sha256']):raise ValueError('Pre-upgrade backup/current world mismatch')
        binding['backupManifest']={'path':str(backup.resolve()),'sha256':digest(backup)}
    return runtime['savedSnapshot'],binding

def stage(home: Path, dependencies: Path, candidate: Path, harness: Path, phase: str, snapshot: dict | None=None):
    # The installer parent marker is created only by the explicit disposable setup.
    home=guarded_directory(home)
    if not (home.parent/'.bop-qualification-owner').is_file():
        raise ValueError('Server/client home lacks the disposable setup ownership marker')
    if home.is_symlink() or home.name not in {'server','client-one','client-two'}:
        raise ValueError('Not a named disposable production instance')
    lock=json.loads((ROOT/'tools/ci/runtime-dependencies.lock.json').read_text())
    rows=validate_lock(lock,properties(ROOT/'gradle.properties'))
    sources=[]
    for row in rows:
        path=dependencies/row['filename'];validate_bytes(row,path.read_bytes());sources.append((row['modId'],path))
    sources.extend([('immersive_bop_harvest',candidate),('bop_harvest_qa',harness)])
    mods=home/'mods';mods.mkdir(exist_ok=True)
    old_plan=home/'bop-qa-plan.json'
    old=json.loads(old_plan.read_text()) if old_plan.exists() else None
    actual=list(mods.iterdir())
    if old is None and actual: raise ValueError('Refusing an unowned nonempty mods directory')
    if old:
        expected={m['name']:m for m in old['mods']}
        if {p.name for p in actual}!=set(expected):raise ValueError('Unexpected files in owned mods directory')
        for path in actual:
            if not path.is_file() or path.is_symlink() or digest(path)!=expected[path.name]['sha256']:raise ValueError('Staged bytes changed outside this runner')
    staged=[]
    for mod,source in sources:
        with zipfile.ZipFile(source) as archive:
            data=tomllib.loads(archive.read('META-INF/neoforge.mods.toml').decode())
        if len([m for m in data['mods'] if m['modId']==mod])!=1:raise ValueError('Wrong staged mod identity')
        staged.append({'modId':mod,'name':source.name,'sha256':digest(source),'size':source.stat().st_size})
    # Every replacement is a previously inventoried file, inside this owned instance.
    for path in actual:
        if not path.resolve().is_relative_to(mods.resolve()):raise ValueError('Mod path escapes instance')
        if any(row['name']==path.name and row['sha256']==digest(path) for row in staged):continue
        print('Replacing verified staged JAR:',path.name,flush=True)
        path.unlink()
    for (_,source),row in zip(sources,staged):
        if not (mods/source.name).exists():shutil.copyfile(source,mods/source.name)
        if digest(mods/source.name)!=row['sha256']:raise ValueError('Installed hash differs')
    nonce=str(uuid.uuid4())
    plan={'schemaVersion':1,'nonce':nonce,'phase':phase,'mods':staged,'dependencyLockSha256':digest(ROOT/'tools/ci/runtime-dependencies.lock.json')}
    if snapshot is not None:plan['expectedSnapshot']=snapshot
    (home/'.bop-qa-owner').write_text(nonce+'\n')
    old_plan.write_text(json.dumps(plan,indent=2)+'\n')
    return plan

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('server-home','dependencies','candidate','harness','evidence'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--phase',choices=['baseline-create','baseline-restart','candidate-upgrade','candidate-restart','multiplayer'],required=True)
    parser.add_argument('--expected-result',type=Path)
    parser.add_argument('--backup-manifest',type=Path)
    parser.add_argument('--port',type=int,default=25575)
    args=parser.parse_args()
    home=guarded_directory(args.server_home);evidence=guarded_directory(args.evidence);evidence.mkdir(parents=True,exist_ok=True)
    result_path=evidence/(args.phase+'.json'); log=evidence/(args.phase+'.log')
    if result_path.exists() or log.exists():raise ValueError('Evidence phase already exists; choose a new evidence attempt directory')
    snapshot,predecessor=validate_chain(args.phase,args.expected_result,home,args.candidate,args.harness,args.backup_manifest)
    plan=stage(home,args.dependencies,args.candidate,args.harness,args.phase,snapshot)
    (home/'eula.txt').write_text('eula=true\n')
    (home/'server.properties').write_text('\n'.join([
        'server-ip=127.0.0.1','server-port='+str(args.port),'online-mode=false','enforce-secure-profile=false',
        'level-name=world','level-type=minecraft:flat','level-seed=9052026','generate-structures=false',
        'generator-settings={"layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:dirt","height":2},{"block":"minecraft:grass_block","height":1}],"biome":"minecraft:plains"}',
        'spawn-protection=0','view-distance=5','simulation-distance=5','difficulty=peaceful','max-players=2','max-tick-time=60000','enable-rcon=false','enable-query=false'])+'\n')
    command=['java','-Xmx3G','-Dbop.qa.phase='+args.phase,'@libraries/net/neoforged/neoforge/21.1.233/'+('win_args.txt' if os.name=='nt' else 'unix_args.txt'),'nogui']
    started=time.time();timed_out=False;aborted=False
    with log.open('wb') as output:
        with subprocess.Popen(command,cwd=home,stdout=output,stderr=subprocess.STDOUT,stdin=subprocess.PIPE) as process:
            print('Started explicit production phase',args.phase,'PID',process.pid,flush=True)
            cancel=home/('.bop-qa-cancel-'+plan['nonce'])
            while process.poll() is None and time.time()-started<600 and not cancel.exists():
                try:process.wait(timeout=1)
                except subprocess.TimeoutExpired:pass
            if process.poll() is None:
                aborted=cancel.exists();timed_out=not aborted
                try:process.stdin.write(b'stop\n');process.stdin.flush();code=process.wait(timeout=30)
                except (OSError,subprocess.TimeoutExpired):process.kill();code=process.wait()
            else:code=process.returncode
    text=log.read_text(encoding='utf-8',errors='replace')
    runtime=json.loads((home/'bop-qa-result.json').read_text()) if (home/'bop-qa-result.json').exists() else None
    passed=(code==0 and not timed_out and not aborted and runtime and runtime.get('nonce')==plan['nonce'] and runtime.get('phaseStatus')=='PASS'
            and 'Stopping server' in text and 'All dimensions are saved' in text)
    receipt={'command':command,'cwd':str(home),'predecessor':predecessor,'exitCode':code,'timeout':timed_out,'aborted':aborted,'durationSeconds':round(time.time()-started,3),'log':str(log),'logSha256':digest(log),'logBytes':log.stat().st_size,'runtime':runtime,'passed':bool(passed)}
    result_path.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='runtime'}),flush=True)
    if not passed:
        print(text[-7000:]);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
