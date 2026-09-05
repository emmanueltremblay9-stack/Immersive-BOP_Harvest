"""Install pinned official production launchers into a new disposable root."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,time,urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.ci.run_packaged_qualification import guarded_directory,digest

INSTALLER_URL='https://maven.neoforged.net/releases/net/neoforged/neoforge/21.1.233/neoforge-21.1.233-installer.jar'
INSTALLER_SHA256='311475c8315ed0be6b5f1dbbf5a377b6c0976457c0bd5aa6d19b0fe25fd77148'
METADATA_URL='https://piston-meta.mojang.com/v1/packages/b2175d7cf605de8e31ee9298e14113f847e6bb35/1.21.1.json'
METADATA_SHA256='7817aa7bdbdb2cd723791761fd7d8c2646f0b520d12c0deec18a7fa459265d5d'

def fetch(url,target,expected,algorithm='sha256',size=None,cache=None):
    if cache and cache.is_file():raw=cache.read_bytes()
    elif target.is_file():raw=target.read_bytes()
    else:
        with urllib.request.urlopen(url,timeout=90) as response:raw=response.read((size or 64*1024*1024)+1)
    if (size is not None and len(raw)!=size) or len(raw)>64*1024*1024 or hashlib.new(algorithm,raw).hexdigest()!=expected:raise ValueError('Pinned official input bytes differ: '+target.name)
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);return raw

def prepare(root,installer_cache=None,metadata_cache=None,vanilla_cache=None,library_cache=None):
    root=guarded_directory(root)
    if root.exists() and any(root.iterdir()):raise ValueError('Production preparation requires a new empty disposable root')
    root.mkdir(parents=True,exist_ok=True);(root/'.bop-qualification-owner').write_text('bop-production-qualification-v1\n')
    installer=root/'neoforge-21.1.233-installer.jar'
    fetch(INSTALLER_URL,installer,INSTALLER_SHA256,cache=installer_cache)
    raw=fetch(METADATA_URL,root/'minecraft-1.21.1.json',METADATA_SHA256,size=38408,cache=metadata_cache);parent=json.loads(raw)
    with zipfile.ZipFile(installer) as archive:
        profile=json.loads(archive.read('install_profile.json'));child=json.loads(archive.read('version.json'))
    receipts=[]
    for kind in ['server','client']:
        home=root/kind;home.mkdir()
        if library_cache:
            for library in profile['libraries']+child['libraries']+(parent['libraries'] if kind=='client' else []):
                row=library.get('downloads',{}).get('artifact')
                if row and (library_cache/row['path']).is_file():fetch(row['url'],home/'libraries'/row['path'],row['sha1'],'sha1',row.get('size'),library_cache/row['path'])
        if kind=='client':
            version=home/'versions/1.21.1';version.mkdir(parents=True)
            (version/'1.21.1.json').write_bytes(raw);row=parent['downloads']['client']
            fetch(row['url'],version/'1.21.1.jar',row['sha1'],'sha1',row['size'],vanilla_cache)
            (home/'launcher_profiles.json').write_text('{"profiles":{}}\n')
        command=['java','-jar',str(installer),'--install'+kind.title(),str(home)]
        log=root/('installer-'+kind+'.log');started=time.time()
        with log.open('wb') as output:result=subprocess.run(command,cwd=root,stdout=output,stderr=subprocess.STDOUT,timeout=1200)
        receipts.append({'command':command,'exitCode':result.returncode,'durationSeconds':round(time.time()-started,3),'logSha256':digest(log)})
        (root/'preparation.json').write_text(json.dumps({'installerSha256':INSTALLER_SHA256,'metadataSha256':METADATA_SHA256,'commands':receipts},indent=2)+'\n')
        if result.returncode:raise ValueError('Official '+kind+' installer failed; inspect retained log')
        print('Pinned official',kind,'installer passed',flush=True)
    return root

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    for name in ['installer-cache','metadata-cache','vanilla-cache','library-cache']:parser.add_argument('--'+name,type=Path)
    args=parser.parse_args();prepare(args.root,args.installer_cache,args.metadata_cache,args.vanilla_cache,args.library_cache)

if __name__=='__main__':main()
