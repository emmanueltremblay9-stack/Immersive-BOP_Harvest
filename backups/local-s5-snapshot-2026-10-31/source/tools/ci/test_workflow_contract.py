"""Static protocol regressions complement actionlint; they are not live CI proof."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[2]

class WorkflowContractTests(unittest.TestCase):
    def setUp(self):
        self.text=(ROOT/'.github/workflows/publish-curseforge.yml').read_text()
    def test_dispatch_is_manual_and_defaults_safe(self):
        self.assertIn('  workflow_dispatch:',self.text)
        self.assertNotIn('\n  push:',self.text)
        self.assertNotIn('\n  pull_request:',self.text)
        self.assertRegex(self.text,r'dry_run:[\s\S]*?default: true')
        self.assertIn('      manifest_path:',self.text)
    def test_permissions_and_concurrency(self):
        self.assertIn('permissions:\n  contents: read\n  actions: read',self.text)
        self.assertIn('group: curseforge-${{ inputs.tag }}',self.text)
        self.assertIn('cancel-in-progress: false',self.text)
        self.assertNotIn('write-all',self.text)
    def test_token_only_prepare_and_submit(self):
        parts=re.split(r'      - name: ',self.text)[1:]
        token_steps=[part.splitlines()[0] for part in parts if 'secrets.CURSEFORGE_API_TOKEN' in part]
        self.assertEqual(['Prepare exact upload intent without posting','Submit exact persisted request once'],token_steps)
    def test_exact_protocol_step_and_tests_before_upload(self):
        self.assertIn('"CurseForge ${{ inputs.tag }} ::',self.text)
        tests=self.text.index('Test publisher failure and idempotency paths')
        prepare=self.text.index('Prepare exact upload intent without posting')
        persist=self.text.index('Persist upload intent before any POST')
        submit=self.text.index('Submit exact persisted request once')
        self.assertLess(tests,prepare);self.assertLess(prepare,persist);self.assertLess(persist,submit)
        self.assertIn("steps.persist-intent.outcome == 'success'",self.text)
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
        import json,sys
        sys.path.insert(0,str(ROOT/'tools/release'))
        import publish_curseforge as pub
        with self.assertRaises(pub.PublicationError) as raised:
            pub.load_manifest(ROOT/'tools/release/curseforge_release_TEMPLATE.json')
        self.assertEqual('TEMPLATE_NOT_PUBLISHABLE',raised.exception.status)
        self.assertFalse((ROOT/'tools/release/curseforge_release_0.1.1-alpha.9.json').exists())
if __name__=='__main__':unittest.main()
