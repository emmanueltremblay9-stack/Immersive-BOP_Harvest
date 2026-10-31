"""Read-only PR artifact inspection; never canonical-main authentication."""
import argparse
import base64
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--run', type=int, required=True)
parser.add_argument('--head', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.repo))
from tools.ci.candidate_evidence import (GitHub, REPOSITORY, REQUIRED_STEPS,
    WINDOWS_STEPS, PRODUCTION_STEPS, sha, contents, read_json, require,
    report_capabilities, check_dependency_receipt, jar_identity)
from tools.ci.qualification_report import SPEC_FILES

api = GitHub()
run = api.get(f'actions/runs/{args.run}/attempts/1')
require(run['head_sha'] == args.head and run['event'] == 'pull_request'
        and run['status'] == 'completed' and run['conclusion'] == 'success', 'PR run identity/result mismatch')
jobs = api.get(f'actions/runs/{args.run}/attempts/1/jobs?per_page=100')
by_name = {j['name']: j for j in jobs['jobs']}
require(jobs['total_count'] == 2 and set(by_name) == {'Gradle validation', 'Windows manifest regressions'}, 'Wrong jobs')
for name, expected in {'Gradle validation': REQUIRED_STEPS | PRODUCTION_STEPS,
                       'Windows manifest regressions': WINDOWS_STEPS}.items():
    require(by_name[name]['conclusion'] == 'success' and expected <=
        {s['name'] for s in by_name[name]['steps'] if s['conclusion'] == 'success'}, 'Missing mandatory successful step')
head = api.get(f'git/commits/{args.head}')
artifacts = api.get(f'actions/runs/{args.run}/artifacts?per_page=100')
matches = [a for a in artifacts['artifacts'] if a['name'] == f'candidate-evidence-{args.run}-1']
require(len(matches) == 1 and matches[0]['expired'] is False, 'Missing unique artifact')
artifact = matches[0]
require(artifact['workflow_run']['id'] == args.run and artifact['workflow_run']['head_sha'] == args.head, 'Wrong artifact run')
archive = api.get(f'actions/artifacts/{artifact["id"]}/zip', binary=True)
require(artifact['digest'] == 'sha256:' + sha(archive), 'Artifact service digest mismatch')
files = contents(archive)
receipt = read_json(files.pop('receipt.json'))
require(receipt['sourceTree'] == head['tree']['sha'] and receipt['event'] == 'pull_request'
        and receipt['runId'] == args.run and receipt['runAttempt'] == 1, 'Receipt not bound to reviewed PR tree')
require(api.get(f'git/commits/{receipt["sourceCommit"]}')['tree']['sha'] == head['tree']['sha'], 'Checkout merge tree differs')
require(receipt['files'] == {name: {'size': len(raw), 'sha256': sha(raw)} for name, raw in files.items()}, 'Inventory differs')
source = lambda name: base64.b64decode(api.get(f'contents/{name}?ref={args.head}')['content'])
lock = source('tools/ci/runtime-dependencies.lock.json')
require(receipt['dependencyLockSha256'] == sha(lock), 'Wrong lock identity')
check_dependency_receipt(files['runtime-dependencies.json'], lock)
specs = {name: read_json(source(f'spec/{name}.json')) for name in SPEC_FILES}
capabilities = report_capabilities(files, specs=specs)
raw = files['candidate.jar']
candidate = {**jar_identity(raw), 'name': 'immersive_bop_harvest-0.1.1-alpha.10.jar', 'size': len(raw), 'sha256': sha(raw)}
require(receipt['candidate'] == candidate and receipt['capabilities'] == capabilities, 'Receipt claims differ from validated evidence')
args.output.mkdir(parents=True, exist_ok=False)
(args.output/'artifact.zip').write_bytes(archive)
flat = args.output/'files'
flat.mkdir()
for name, raw in files.items():
    require('/' not in name, 'Unexpected nested export')
    (flat/name).write_bytes(raw)
(flat/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
result = {'status': 'PASS_PR_PACKET_READBACK', 'canonicalMainAuthenticated': False,
          'stableReady': False, 'runId': args.run, 'attempt': 1, 'head': args.head,
          'tree': head['tree']['sha'], 'checkoutCommit': receipt['sourceCommit'],
          'artifactId': artifact['id'], 'archiveSha256': sha(archive),
          'candidate': candidate, 'capabilities': capabilities}
for name, value in [('readback', result), ('run', run), ('jobs', jobs), ('artifacts', artifacts)]:
    (args.output/(name+'.json')).write_text(json.dumps(value, indent=2)+'\n')
print(json.dumps(result, indent=2))
