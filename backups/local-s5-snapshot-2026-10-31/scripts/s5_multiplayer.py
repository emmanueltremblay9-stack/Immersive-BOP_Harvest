from pathlib import Path
import json,os,subprocess,time,sys

root=Path(__file__).resolve().parent
repo=Path.cwd(); runtime=root/'production-runtime'; evidence=root/'s5-attempt3'
shared=['--dependencies',str(root/'locked-dependencies'),'--candidate',str(root/'reference/immersive_bop_harvest-0.1.1-alpha.10.jar'),'--harness',str(repo/'build/qualification-harness/bop-harvest-qualification-harness-1.jar'),'--evidence',str(evidence)]
commands=[['python','tools/ci/run_packaged_qualification.py','--server-home',str(runtime/'server'),'--phase','multiplayer']+shared]
for phase in ['client-one','client-two']:
    commands.append(['python','tools/ci/production_client.py','--launcher',str(runtime/'client'),'--home',str(runtime/phase),'--assets',str(Path.home()/'.gradle/caches/neoformruntime/assets'),'--phase',phase]+shared)
processes=[]
try:
    processes.append(subprocess.Popen(commands[0]))
    deadline=time.time()+120
    while time.time()<deadline:
        log=evidence/'multiplayer.log'
        if processes[0].poll() is not None:raise RuntimeError('Multiplayer server stopped before client launch')
        if log.exists() and 'Done (' in log.read_text(errors='replace'):break
        time.sleep(1)
    else:raise RuntimeError('Production multiplayer server startup exceeded budget')
    for command in commands[1:]:processes.append(subprocess.Popen(command))
    codes=[p.wait() for p in processes]
    (evidence/'orchestrator.json').write_text(json.dumps({'commands':commands,'exitCodes':codes},indent=2)+'\n')
    raise SystemExit(0 if codes==[0,0,0] else 1)
finally:
    # Each child runner enforces its own bounded Java shutdown and captures failure.
    for process in processes:
        if process.poll() is None:process.wait()
