"""Assemble an offline loopback QA client from the official installed version metadata."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, re, subprocess, sys, time, urllib.request, urllib.parse, uuid, zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.ci.run_packaged_qualification import stage,digest,guarded_directory

def rule_context():
    if platform.machine().lower() not in ('amd64','x86_64'):raise ValueError('Qualification launcher requires x64')
    system={'Windows':'windows','Linux':'linux'}.get(platform.system())
    if not system:raise ValueError('Unsupported qualification client platform')
    return {'name':system,'arch':platform.machine().lower(),'version':platform.release(),'features':{}}

def allowed(rules,context=None):
    context=rule_context() if context is None else context
    if not rules:return True
    result=False
    for rule in rules:
        os_rule=rule.get('os',{})
        if 'name' in os_rule and os_rule['name']!=context['name']:continue
        if 'arch' in os_rule and os_rule['arch']!=context['arch']:continue
        if 'version' in os_rule and not re.search(os_rule['version'],context['version']):continue
        if any(context['features'].get(name,False)!=expected for name,expected in rule.get('features',{}).items()):continue
        result=rule['action']=='allow'
    return result

def arguments(rows,values):
    output=[]
    for row in rows:
        if isinstance(row,dict):
            if not allowed(row['rules']):continue
            row=row['value']
        for value in row if isinstance(row,list) else [row]:
            value=re.sub(r'\$\{([^}]+)\}',lambda m:values[m.group(1)],value)
            if '${' in value:raise ValueError('Unresolved launcher placeholder')
            output.append(value)
    return output


def library(launcher,row):
    name=row['path']
    if PurePosixPath(name).is_absolute() or '\\' in name or ':' in name or any(part in {'','.','..'} for part in name.split('/')):raise ValueError('Unsafe launcher library path')
    path=launcher/'libraries'/name
    guarded_directory(path.parent)
    if not path.exists():
        if urllib.parse.urlparse(row['url']).netloc not in {'libraries.minecraft.net','maven.neoforged.net'} or row['size']>64*1024*1024:raise ValueError('Unexpected official launcher dependency')
        with urllib.request.urlopen(row['url'],timeout=60) as response:raw=response.read(row['size']+1)
        if len(raw)!=row['size'] or hashlib.sha1(raw).hexdigest()!=row['sha1']:raise ValueError('Downloaded launcher library mismatch')
        path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
        try:
            with temporary.open('xb') as stream:stream.write(raw)
            # Peer clients can only observe complete, hash-checked bytes.
            try:os.replace(temporary,path)
            except PermissionError:
                # On Windows a peer can already be reading the completed target.
                # Accept only the exact bytes that both writers independently verified.
                if not path.is_file() or path.stat().st_size!=row['size'] or hashlib.sha1(path.read_bytes()).hexdigest()!=row['sha1']:raise
        finally:
            if temporary.exists():temporary.unlink()
    if hashlib.sha1(path.read_bytes()).hexdigest()!=row['sha1']:raise ValueError('Invalid launcher library '+str(path))
    return path

def command(launcher:Path,home:Path,assets:Path,phase:str):
    launcher=guarded_directory(launcher)
    if launcher!=home.parent/'client' or not (home.parent/'.bop-qualification-owner').is_file():raise ValueError('Launcher must be the prepared sibling of the owned client instance')
    context=rule_context()
    child=json.loads((launcher/'versions/neoforge-21.1.233/neoforge-21.1.233.json').read_text())
    parent=json.loads((launcher/'versions/1.21.1/1.21.1.json').read_text())
    libs={}
    for lib in parent['libraries']+child['libraries']:
        if not allowed(lib.get('rules',[]),context) or any(classifier in lib['name'] for classifier in ('natives-windows-arm64','natives-windows-x86','natives-linux-arm64','natives-linux-arm32')):continue
        coordinate=lib['name'].split(':');key=tuple(coordinate[:2]+coordinate[3:]);libs[key]=lib
    cp=[];natives=home/'natives';natives.mkdir(exist_ok=True)
    for lib in libs.values():
        path=library(launcher,lib['downloads']['artifact'])
        cp.append(str(path))
        if 'natives-'+context['name'] in lib['name']:
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    if info.filename.lower().endswith('.dll') or re.search(r'\.so(?:\.\d+)*$',info.filename):
                        target=natives/Path(info.filename).name
                        if target.exists() and target.read_bytes()!=archive.read(info):raise ValueError('Ambiguous native library')
                        target.write_bytes(archive.read(info))
    # ModLauncher discovers the official generated client at this Maven coordinate.
    gamejar=launcher/'libraries/net/neoforged/neoforge/21.1.233/neoforge-21.1.233-client.jar'
    if not gamejar.is_file():raise ValueError('Official installer did not produce the NeoForge client JAR')
    # The production client provider loads this generated JAR itself. Adding it
    # to the legacy classpath creates a second module named neoforge.
    index=assets/'indexes'/ (parent['assetIndex']['id']+'.json')
    if hashlib.sha1(index.read_bytes()).hexdigest()!=parent['assetIndex']['sha1']:raise ValueError('Invalid official asset index')
    player='BopQaOne' if phase=='client-one' else 'BopQaTwo'
    offline=uuid.UUID(bytes=hashlib.md5(('OfflinePlayer:'+player).encode()).digest(),version=3)
    values={'auth_player_name':player,'version_name':child['id'],'game_directory':str(home),'assets_root':str(assets),'assets_index_name':parent['assetIndex']['id'],'auth_uuid':offline.hex,'auth_access_token':'0','clientid':'','auth_xuid':'','user_type':'legacy','version_type':'release','natives_directory':str(natives),'launcher_name':'bop-disposable-qualification','launcher_version':'1','classpath':os.pathsep.join(cp),'library_directory':str(launcher/'libraries'),'classpath_separator':os.pathsep}
    return ['java','-Xmx3G','-Dbop.qa.phase='+phase]+arguments(parent['arguments']['jvm']+child['arguments']['jvm'],values)+[child['mainClass']]+arguments(parent['arguments']['game']+child['arguments']['game'],values)+['--width','1280','--height','720']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['launcher','home','assets','dependencies','candidate','harness','evidence']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--phase',choices=['client-one','client-two'],required=True)
    p.add_argument('--hide-window',action='store_true',help='Keep rendering and screenshots active without a foreground test window')
    a=p.parse_args();a.launcher=guarded_directory(a.launcher);a.home=guarded_directory(a.home);a.evidence=guarded_directory(a.evidence)
    a.home.mkdir(exist_ok=True);a.evidence.mkdir(parents=True,exist_ok=True)
    log=a.evidence/(a.phase+'.log');receipt=a.evidence/(a.phase+'.json')
    if log.exists() or receipt.exists():raise ValueError('Client evidence already exists')
    plan=stage(a.home,a.dependencies,a.candidate,a.harness,a.phase)
    options=a.home/'options.txt'
    if not options.exists():options.write_text('autoJump:false\nfullscreen:false\nrenderDistance:6\nsimulationDistance:5\nmaxFps:30\nonboardAccessibility:false\njoinedFirstServer:true\npauseOnLostFocus:false\n')
    cmd=command(a.launcher,a.home,a.assets.resolve(),a.phase)
    if a.hide_window:cmd.insert(1,'-Dbop.qa.hideClient=true')
    started=time.time();timeout=False;aborted=False
    with log.open('wb') as output:
        with subprocess.Popen(cmd,cwd=a.home,stdout=output,stderr=subprocess.STDOUT) as proc:
            print('Started real production client',a.phase,'PID',proc.pid,flush=True)
            cancel=a.home/('.bop-qa-cancel-'+plan['nonce'])
            while proc.poll() is None and time.time()-started<900 and not cancel.exists():
                try:proc.wait(timeout=1)
                except subprocess.TimeoutExpired:pass
            if proc.poll() is None:
                aborted=cancel.exists();timeout=not aborted
                if aborted:
                    # The client tick hook observes the same scoped cancellation.
                    try:code=proc.wait(timeout=20)
                    except subprocess.TimeoutExpired:proc.kill();code=proc.wait()
                else:proc.kill();code=proc.wait()
            else:code=proc.returncode
    result=json.loads((a.home/'bop-qa-client.json').read_text()) if (a.home/'bop-qa-client.json').is_file() else None
    passed=code==0 and not timeout and not aborted and result and result.get('nonce')==plan['nonce'] and result.get('phaseStatus')=='PASS'
    data={'command':cmd,'cwd':str(a.home),'exitCode':code,'timeout':timeout,'aborted':aborted,'durationSeconds':round(time.time()-started,3),'log':str(log),'logSha256':digest(log),'logBytes':log.stat().st_size,'client':result,'passed':bool(passed)}
    receipt.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({k:v for k,v in data.items() if k not in ['command','client']}),flush=True)
    if not passed:print(log.read_text(errors='replace')[-5000:]);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
