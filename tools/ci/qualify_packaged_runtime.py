"""Execute a full disposable phase chain using one immutable harness and candidate."""
from pathlib import Path
import argparse,json,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.ci.run_packaged_qualification import guarded_directory,digest

def backup_world(home,root):
    source=guarded_directory(home/'world');target=root/'alpha9-world-backup'
    if target.exists():raise ValueError('Backup already exists')
    def inventory(path):return {p.relative_to(path).as_posix():digest(p) for p in path.rglob('*') if p.is_file()}
    before=inventory(source);shutil.copytree(source,target)
    if before!=inventory(target):raise ValueError('Backup hash mismatch')
    manifest=root/'alpha9-world-backup.json'
    manifest.write_text(json.dumps({'source':str(source),'backup':str(target),'sha256':before,'fileCount':len(before),'hashMatch':True},indent=2)+'\n')
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['root','assets','dependencies','baseline','candidate','harness']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--hide-windows',action='store_true')
    args=parser.parse_args();root=guarded_directory(args.root);home=root/'server';evidence=root/'receipts';evidence.mkdir(exist_ok=False)
    shared=['--dependencies',str(args.dependencies.resolve()),'--harness',str(args.harness.resolve()),'--evidence',str(evidence)]
    ledger=[]
    def server_command(phase,candidate,previous=None,backup=None):
        command=[sys.executable,str(ROOT/'tools/ci/run_packaged_qualification.py'),'--server-home',str(home),'--phase',phase,'--candidate',str(candidate.resolve())]+shared
        if previous:command+=['--expected-result',str(evidence/(previous+'.json'))]
        if backup:command+=['--backup-manifest',str(backup)]
        return command
    def run(command):
        result=subprocess.run(command,cwd=ROOT);ledger.append({'command':command,'exitCode':result.returncode})
        (root/'orchestration.json').write_text(json.dumps(ledger,indent=2)+'\n')
        if result.returncode:raise ValueError('Qualification phase failed; retained raw logs are authoritative')
    run(server_command('baseline-create',args.baseline))
    run(server_command('baseline-restart',args.baseline,'baseline-create'))
    backup=backup_world(home,root)
    run(server_command('candidate-upgrade',args.candidate,'baseline-restart',backup))
    run(server_command('candidate-restart',args.candidate,'candidate-upgrade'))
    processes=[];commands=[server_command('multiplayer',args.candidate,'candidate-restart')]
    def cancel_peers(reason):
        for instance,process in zip([home,root/'client-one',root/'client-two'],processes):
            plan_path=instance/'bop-qa-plan.json'
            if process.poll() is None and plan_path.is_file():
                plan=json.loads(plan_path.read_text())
                (instance/('.bop-qa-cancel-'+plan['nonce'])).write_text(reason+'\n')
    for phase in ['client-one','client-two']:
        command=[sys.executable,str(ROOT/'tools/ci/production_client.py'),'--launcher',str(root/'client'),'--home',str(root/phase),'--assets',str(args.assets.resolve()),'--phase',phase,'--candidate',str(args.candidate.resolve())]+shared
        if args.hide_windows:command.append('--hide-window')
        commands.append(command)
    try:
        processes.append(subprocess.Popen(commands[0],cwd=ROOT));deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            log=evidence/'multiplayer.log'
            if processes[0].poll() is not None:raise ValueError('Multiplayer server exited before client launch')
            if log.exists() and 'Done (' in log.read_text(errors='replace'):break
            time.sleep(1)
        else:raise ValueError('Multiplayer server readiness budget exhausted')
        for command in commands[1:]:processes.append(subprocess.Popen(command,cwd=ROOT))
        while any(p.poll() is None for p in processes):
            if any(p.poll() is not None and p.returncode!=0 for p in processes):
                cancel_peers('A peer qualification process failed')
            time.sleep(1)
        for command,process in zip(commands,processes):ledger.append({'command':command,'exitCode':process.returncode})
        (root/'orchestration.json').write_text(json.dumps(ledger,indent=2)+'\n')
        if any(p.returncode for p in processes):raise ValueError('Actual client/server multiplayer qualification failed')
    finally:
        cancel_peers('Controller cleanup')
        for process in processes:
            if process.poll() is None:
                process.wait(timeout=90)
    print('DISPOSABLE PRODUCTION PHASES PASSED; independent evidence verification still required')

if __name__=='__main__':main()
