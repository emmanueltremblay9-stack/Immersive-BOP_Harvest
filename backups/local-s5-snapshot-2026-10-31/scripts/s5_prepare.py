"""Prepare disposable production launchers from pinned official installer inputs."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, time, zipfile

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'production-runtime'
CACHE=Path(os.environ['APPDATA'])/'PrismLauncher/libraries'
ARTIFACTS=Path.home()/'.gradle/caches/neoformruntime/artifacts'
INSTALLER=CACHE/'net/neoforged/neoforge/21.1.233/neoforge-21.1.233-installer.jar'
EXPECTED='311475c8315ed0be6b5f1dbbf5a377b6c0976457c0bd5aa6d19b0fe25fd77148'

def copied(source, dest, sha1=None):
    data=source.read_bytes()
    if sha1 and hashlib.sha1(data).hexdigest()!=sha1:
        raise ValueError('Cache hash mismatch: '+str(source))
    if not dest.resolve().is_relative_to(BASE.resolve()):
        raise ValueError('Destination escapes owned runtime')
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and dest.read_bytes()!=data:
        raise ValueError('Refusing to overwrite different staged bytes: '+str(dest))
    if not dest.exists(): dest.write_bytes(data)

def main():
    assert hashlib.sha256(INSTALLER.read_bytes()).hexdigest()==EXPECTED
    if not BASE.exists():
        BASE.mkdir()
        (BASE/'.bop-qualification-owner').write_text('qualification-20260905\n')
    assert (BASE/'.bop-qualification-owner').read_text()=='qualification-20260905\n'
    with zipfile.ZipFile(INSTALLER) as archive:
        profile=json.loads(archive.read('install_profile.json'))
        child=json.loads(archive.read('version.json'))
    parent=json.loads((ARTIFACTS/'minecraft_1.21.1_version_manifest.json').read_text())
    for kind in sys.argv[1:] or ['server','client']:
        target=BASE/kind
        target.mkdir(exist_ok=True)
        seen=set(); copied_count=0
        for lib in profile['libraries']+child['libraries']+(parent['libraries'] if kind=='client' else []):
            row=lib.get('downloads',{}).get('artifact')
            if not row or row['path'] in seen: continue
            seen.add(row['path'])
            source=CACHE/row['path']
            if source.is_file():
                copied(source,target/'libraries'/row['path'],row.get('sha1'));copied_count+=1
        if kind=='client':
            vanilla=ARTIFACTS/'minecraft_1.21.1_client.jar'
            if not vanilla.is_file():
                matches=[p for p in ARTIFACTS.glob('*client*.jar') if p.stat().st_size==parent['downloads']['client']['size']]
                assert len(matches)==1,matches
                vanilla=matches[0]
            copied(vanilla,target/'versions/1.21.1/1.21.1.jar',parent['downloads']['client']['sha1'])
            (target/'versions/1.21.1/1.21.1.json').write_text(json.dumps(parent))
            (target/'launcher_profiles.json').write_text('{"profiles":{}}\n')
        command=['java','-jar',str(INSTALLER),'--install'+kind.title(),str(target)]
        log=ROOT/('s5-installer-'+kind+'.log')
        started=time.time()
        print('Installing',kind,'with',copied_count,'verified cached libraries',flush=True)
        with log.open('wb') as stream:
            result=subprocess.run(command,cwd=BASE,stdout=stream,stderr=subprocess.STDOUT,timeout=1200)
        receipt={'command':command,'exitCode':result.returncode,'durationSeconds':round(time.time()-started,3),'log':str(log),'logSha256':hashlib.sha256(log.read_bytes()).hexdigest(),'installerSha256':EXPECTED}
        (ROOT/('s5-installer-'+kind+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(receipt),flush=True)
        if result.returncode: raise SystemExit(result.returncode)

if __name__=='__main__': main()
