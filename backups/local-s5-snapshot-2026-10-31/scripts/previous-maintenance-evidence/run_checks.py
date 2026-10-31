import json,subprocess,hashlib,datetime,pathlib
root=pathlib.Path.cwd(); out=root/'build/release-evidence/maintenance-20260905'
commands=[
['python','-W','error::ResourceWarning','-m','unittest','discover','-s','tools/release','-p','test_*.py','-v'],
['python','-m','unittest','discover','-s','tools/ci','-p','test_*.py','-v'],
['python','-m','unittest','scripts/test_check_beta_release_gate.py','scripts/test_check_stable_release_gate.py','-v'],
['python','scripts/validate_specs.py'],
['python','scripts/generate_alpha_resources.py'],
['python','scripts/generate_alpha_resources.py'],
['python','scripts/qa_alpha_resources.py'],
['git','diff','--exit-code','--','src/main/resources','src/generated/resources'],
['python','scripts/check_stable_release_gate.py','--bundle','build/release-evidence/maintenance-20260905/candidate-not-created.json'],
['git','diff','--check']]
receipts=[]
for index,cmd in enumerate(commands):
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result=subprocess.run(cmd,capture_output=True,timeout=180)
    log=out/f'check-{index:02}.log'; log.write_bytes(result.stdout+result.stderr)
    receipts.append({'command':cmd,'exit_code':result.returncode,'started':start,'log':log.relative_to(root).as_posix(),'sha256':hashlib.sha256(log.read_bytes()).hexdigest()})
    print(index,result.returncode,' '.join(cmd),flush=True)
(out/'commands.json').write_text(json.dumps(receipts,indent=2)+'\n')
