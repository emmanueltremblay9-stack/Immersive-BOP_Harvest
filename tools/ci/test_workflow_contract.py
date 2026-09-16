"""Static protocol regressions complement actionlint; they are not live CI proof."""
from pathlib import Path
import hashlib
import re
import unittest
ROOT=Path(__file__).resolve().parents[2]

class WorkflowContractTests(unittest.TestCase):
    def setUp(self):
        self.text=(ROOT/'.github/workflows/publish-curseforge.yml').read_text()
    def test_workflow_run_and_manual_dry_run_are_both_bounded(self):
        self.assertIn('  workflow_run:',self.text)
        self.assertIn('      - Build and validate',self.text)
        self.assertIn('      - completed',self.text)
        self.assertIn('  workflow_dispatch:',self.text)
        self.assertNotIn('\n  push:',self.text)
        self.assertNotIn('\n  pull_request:',self.text)
        self.assertRegex(self.text,r'dry_run:[\s\S]*?default: true')
        self.assertIn('      manifest_path:',self.text)
    def test_permissions_and_concurrency(self):
        self.assertIn('permissions:\n  contents: read\n  actions: read',self.text)
        automatic=self.text.split('\n  auto-publish:',1)[1].split('\n  publish:',1)[0]
        self.assertIn('permissions:\n      contents: write\n      actions: read',automatic)
        self.assertIn('group: curseforge-stable-${{',self.text)
        self.assertIn("github.event_name == 'workflow_run' && 'v0.1.1'",self.text)
        self.assertIn("startsWith(inputs.tag, 'v')",self.text)
        self.assertNotIn("format('source-{0}-{1}'",self.text)
        self.assertIn('cancel-in-progress: false',self.text)
        self.assertNotIn('write-all',self.text)
    def test_token_only_runtime_preflight_prepare_and_submit(self):
        parts=re.split(r'      - name: ',self.text)[1:]
        token_steps=[part.splitlines()[0] for part in parts if 'secrets.CURSEFORGE_API_TOKEN' in part]
        self.assertEqual([
            'Check CurseForge credential availability',
            'Check CurseForge credential availability for exact preflight',
            'Prepare exact CurseForge upload intent without posting',
            'Submit automatic exact persisted request once',
            'Prepare exact upload intent without posting',
            'Submit exact persisted request once',
        ],token_steps)
    def test_exact_protocol_step_and_tests_before_upload(self):
        self.assertIn('run-name: "CurseForge ${{',self.text)
        self.assertIn(' }} :: publish"',self.text)
        manual=self.text.split('\n  publish:',1)[1]
        tests=manual.index('Test publisher failure and idempotency paths')
        prepare=manual.index('Prepare exact upload intent without posting')
        persist=manual.index('Persist upload intent before any POST')
        submit=manual.index('Submit exact persisted request once')
        self.assertLess(tests,prepare);self.assertLess(prepare,persist);self.assertLess(persist,submit)
        self.assertIn("steps.persist-intent.outcome == 'success'",self.text)

    def test_source_gate_pins_upstream_and_evaluates_without_mutation(self):
        for marker in (
            "github.event.workflow_run.name == 'Build and validate'",
            "github.event.workflow_run.path == '.github/workflows/build.yml'",
            "github.event.workflow_run.head_repository.full_name == github.repository",
            "github.event.workflow_run.event == 'push'",
            "github.event.workflow_run.head_branch == 'main'",
            "github.event.workflow_run.conclusion == 'success'",
            "ref: ${{ github.event.workflow_run.head_sha }}",
            "python tools/release/stable_autopublish.py",
            "--credential-available",
            "auto_publish_eligible=",
        ):
            self.assertIn(marker,self.text)
        source=self.text.split('  source-readiness:',1)[1].split('\n  auto-publish:',1)[0]
        self.assertIn('CURSEFORGE_API_TOKEN',source)
        evaluation=source.split('      - name: Evaluate exact stable runtime gates without mutation',1)[1]
        self.assertNotIn('CURSEFORGE_API_TOKEN',evaluation)
        self.assertNotIn('publish_curseforge.py',source)
        self.assertNotIn('stable_publish.py',source)
        self.assertNotIn('upload-artifact',source)
        self.assertNotIn('PUBLICATION_AUTHORITY_NOT_GRANTED',source)
        self.assertNotIn('--method POST',source)

    def test_automatic_path_is_exactly_gated_ordered_and_secret_bounded(self):
        automatic=self.text.split('\n  auto-publish:',1)[1].split('\n  publish:',1)[0]
        for marker in (
            'needs: source-readiness',
            "needs.source-readiness.outputs.auto_publish_eligible == 'true'",
            'contents: write',
            'actions: read',
            'ref: ${{ github.event.workflow_run.head_sha }}',
            'persist-credentials: false',
            'Re-evaluate exact stable gates immediately before mutation',
            'Reconcile or create exact GitHub tag Release and asset',
            'Prepare exact CurseForge upload intent without posting',
            'Persist upload intent before any POST',
            'Submit automatic exact persisted request once',
            'Persist accepted CurseForge file ID before polling',
            'Resume accepted file without a token or second POST',
            'Build final receipt after fresh public readbacks',
            'Read deterministic receipt reconciliation state',
            'Persist deterministic final publication receipt',
            'Read back exact persisted final receipt',
        ):
            self.assertIn(marker,automatic)
        ordered=[
            automatic.index('Re-evaluate exact stable gates immediately before mutation'),
            automatic.index('Reconcile or create exact GitHub tag Release and asset'),
            automatic.index('Prepare exact CurseForge upload intent without posting'),
            automatic.index('Persist upload intent before any POST'),
            automatic.index('Submit automatic exact persisted request once'),
            automatic.index('Persist accepted CurseForge file ID before polling'),
            automatic.index('Resume accepted file without a token or second POST'),
            automatic.index('Build final receipt after fresh public readbacks'),
            automatic.index('Read deterministic receipt reconciliation state'),
            automatic.index('Persist deterministic final publication receipt'),
            automatic.index('Read back exact persisted final receipt'),
        ]
        self.assertEqual(sorted(ordered),ordered)
        github_step=automatic.split(
            '      - name: Reconcile or create exact GitHub tag Release and asset',1
        )[1].split('\n      - name:',1)[0]
        finalize_step=automatic.split(
            '      - name: Build final receipt after fresh public readbacks',1
        )[1].split('\n      - name:',1)[0]
        self.assertNotIn('CURSEFORGE_API_TOKEN',github_step)
        self.assertNotIn('CURSEFORGE_API_TOKEN',finalize_step)
        resume_step=automatic.split(
            '      - name: Resume accepted file without a token or second POST',1
        )[1].split('\n      - name:',1)[0]
        self.assertNotIn('CURSEFORGE_API_TOKEN',resume_step)
        self.assertIn('--resume-file-id',resume_step)
        self.assertIn('--submit',automatic)
        self.assertIn('--receipt-state-report',automatic)
        self.assertIn('stable_publish.py verify-receipt',automatic)
        self.assertNotIn('modrinth',automatic.lower())

    def test_manual_non_dry_mutation_requires_exceptional_authority(self):
        self.assertIn('MANUAL_EXCEPTIONAL_AUTHORITY: NOT_GRANTED',self.text)
        manual=self.text.split('\n  publish:',1)[1]
        for name in (
            'Prepare exact upload intent without posting',
            'Persist upload intent before any POST',
            'Submit exact persisted request once',
            'Resume an accepted file without a token or second POST',
        ):
            part=manual.split(f'      - name: {name}',1)[1].split('\n      - name:',1)[0]
            self.assertIn("env.MANUAL_EXCEPTIONAL_AUTHORITY == 'GRANTED'",part)
        self.assertIn('EXCEPTIONAL_MANUAL_AUTHORITY_REQUIRED',self.text)
        self.assertNotIn('PUBLICATION_AUTHORITY_NOT_GRANTED',self.text)
    def test_all_actions_are_full_sha_pinned(self):
        for p in (ROOT/'.github/workflows').glob('*.yml'):
            for action in re.findall(r'uses:\s*(\S+)',p.read_text()):
                self.assertRegex(action,r'^[^@]+@[0-9a-f]{40}$')
    def test_shared_state_prefix_and_separate_result_paths(self):
        self.assertIn('from publish_curseforge import state_artifact_prefix',self.text)
        self.assertIn('PREPARE_REPORT_PATH=',self.text)
        self.assertIn('RESULT_REPORT_PATH=',self.text)
        self.assertIn('retention-days: 90',self.text)
        self.assertNotIn('iedct'+'-cf-',self.text)
    def test_template_is_not_an_approved_manifest(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools/release'))
        import publish_curseforge as pub
        with self.assertRaises(pub.PublicationError) as raised:
            pub.load_manifest(ROOT/'tools/release/curseforge_release_TEMPLATE.json')
        self.assertEqual('TEMPLATE_NOT_PUBLISHABLE',raised.exception.status)
        self.assertFalse((ROOT/'tools/release/curseforge_release_0.1.1-alpha.9.json').exists())
        stable_path=ROOT/'tools/release/curseforge_release_0.1.1.json'
        stable=pub.load_manifest(stable_path)
        notes=(ROOT/stable['release']['changelogPath']).read_bytes()
        self.assertEqual(hashlib.sha256(notes).hexdigest(),stable['release']['changelogSha256'])
        self.assertEqual(3,len(stable['baseline']['previousFileRelations']))
        self.assertEqual([],stable['baseline']['projectRelations'])
        self.assertEqual(5,len(stable['curseforge']['uploadRelations']))
        self.assertEqual(5,len(stable['curseforge']['expectedPublicRelations']))
if __name__=='__main__':unittest.main()
