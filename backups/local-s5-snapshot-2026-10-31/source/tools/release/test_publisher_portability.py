"""Portability regressions; all network traffic is loopback fixture traffic."""
from __future__ import annotations
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.request
import zipfile
import test_publish_curseforge as legacy
import publish_curseforge as pub


class PortabilityTests(unittest.TestCase):
    setUp = legacy.PublisherTests.setUp
    tearDown = legacy.PublisherTests.tearDown
    run_publisher = legacy.PublisherTests.run_publisher
    prepare_and_persist = legacy.PublisherTests.prepare_and_persist
    publish_from_intent = legacy.PublisherTests.publish_from_intent
    record_persisted_intent_step = legacy.PublisherTests.record_persisted_intent_step

    def publisher(self):
        client = pub.HttpClient(timeout=2, get_attempts=1)
        original = client.get_json
        def get_json(url, **kwargs):
            if url == self.base_url + f'/api/v1/mods/{legacy.PROJECT_ID}':
                return {'data': {'id': legacy.PROJECT_ID, 'slug': 'sample-mod'}}
            return original(url, **kwargs)
        client.get_json = get_json
        return pub.Publisher(self.repo_root, self.manifest, http=client,
                             github_api=self.base_url,
                             curseforge_public_api=self.base_url+'/api/v1',
                             curseforge_upload_api=self.base_url)

    def schema2(self, mode='firstPublication'):
        self.manifest = copy.deepcopy(self.manifest)
        self.manifest['schemaVersion'] = 2
        self.manifest['curseforge'].pop('previousPublicFileId')
        self.manifest['curseforge']['projectSlug'] = 'sample-mod'
        self.manifest['baseline'] = {'mode': mode}
        if mode == 'previousPublicFile':
            self.manifest['baseline']['previousPublicFileId'] = legacy.PREVIOUS_FILE_ID

    def test_zero_relations_first_publication_submits_empty_projects_once(self):
        self.schema2()
        self.manifest['curseforge']['uploadRelations'] = []
        self.manifest['curseforge']['expectedPublicRelations'] = []
        with mock.patch.object(legacy, 'UPLOAD_RELATIONS', []), mock.patch.object(legacy, 'public_relations', return_value=[]):
            intent, artifact = self.prepare_and_persist()
            self.state.publish_visible = True
            report = self.publish_from_intent(intent, artifact)
        self.assertEqual('PUBLISHED_VERIFIED', report['status'])
        self.assertEqual(1, self.state.post_count)
        self.assertEqual([], report['publicReadback']['relations'])

    def test_duplicate_public_game_labels_are_not_exact_readback(self):
        self.state.files[legacy.NEW_FILE_ID] = self.state.current_file()
        self.state.files[legacy.NEW_FILE_ID]['gameVersions'].append('Client')
        self.state.downloads[legacy.NEW_FILE_ID] = self.jar_bytes
        with self.assertRaises(pub.PublicationError) as got:
            self.run_publisher(mode='publish', resume_file_id=legacy.NEW_FILE_ID)
        self.assertEqual('CURSEFORGE_PUBLIC_GAME_VERSIONS_MISMATCH',got.exception.status)

    def test_cli_ignores_ambient_curseforge_secret_on_dry_run_and_resume(self):
        path = self.repo_root/'manifest.json'
        path.write_text(json.dumps(self.manifest))
        for options in [['--dry-run'], ['--publish','--resume-file-id',str(legacy.NEW_FILE_ID)]]:
            with mock.patch.dict(pub.os.environ, {'CURSEFORGE_API_TOKEN':'must-not-propagate'}, clear=True), mock.patch.object(pub.Publisher, 'run', return_value={'status':'FIXTURE_ONLY','verdict':'PASS'}) as run, mock.patch('sys.stdout',new_callable=io.StringIO):
                exit_code = pub.main(options+['--repo-root',str(self.repo_root),'--manifest',str(path),'--tag',legacy.TAG])
                self.assertEqual(0,exit_code)
                self.assertEqual('',run.call_args.kwargs['curseforge_token'])

    def test_first_publication_dry_run_has_no_fake_baseline(self):
        self.schema2()
        report = self.run_publisher(token='ignored-secret')
        self.assertEqual('AUTOMATION_READY_DRY_RUN', report['status'])
        self.assertEqual(0, report['curseForgeBaseline']['initialPublicFileCount'])
        self.assertNotIn('previousFileId', report['curseForgeBaseline'])
        self.assertEqual('', self.state.game_version_token)
        self.assertEqual(0, self.state.post_count)

    def test_first_publication_prepare_and_single_publish(self):
        self.schema2()
        intent, artifact = self.prepare_and_persist()
        self.assertEqual(0, self.state.post_count)
        self.state.publish_visible = True
        report = self.publish_from_intent(intent, artifact)
        self.assertEqual('PUBLISHED_VERIFIED', report['status'])
        self.assertEqual(1, self.state.post_count)

    def test_first_publication_existing_file_resumes_without_cf_token(self):
        self.schema2()
        self.state.files[legacy.NEW_FILE_ID] = self.state.current_file()
        self.state.downloads[legacy.NEW_FILE_ID] = self.jar_bytes
        report = self.run_publisher(mode='publish', resume_file_id=legacy.NEW_FILE_ID)
        self.assertEqual('RESUMED_PUBLICATION_VERIFIED', report['status'])
        self.assertEqual(0, self.state.post_count)
        self.assertEqual('', self.state.game_version_token)

    def test_first_publication_nonempty_project_blocks(self):
        self.schema2()
        self.state.files[legacy.PREVIOUS_FILE_ID] = self.state.prior_file()
        with self.assertRaises(pub.PublicationError) as got:
            self.run_publisher()
        self.assertEqual('FIRST_PUBLICATION_PROJECT_NOT_EMPTY', got.exception.status)
        self.assertEqual(0, self.state.post_count)

    def test_first_publication_never_skips_unknown_prior_intent(self):
        self.schema2()
        self.record_persisted_intent_step('99-1')
        with self.assertRaises(pub.PublicationError) as got:
            self.run_publisher(mode='prepare-publish', token='secret', github_token='read-only', run_key='100-1')
        self.assertEqual('UPLOAD_OUTCOME_UNKNOWN', got.exception.status)
        self.assertEqual(0, self.state.post_count)

    def test_previous_public_file_schema2_retains_exact_parent(self):
        self.schema2('previousPublicFile')
        report = self.run_publisher()
        self.assertEqual(legacy.PREVIOUS_FILE_ID, report['curseForgeBaseline']['previousFileId'])

    def test_previous_public_file_requires_real_positive_id(self):
        self.schema2('previousPublicFile')
        for invalid in [None, 0, -1, True, '100002']:
            with self.subTest(value=invalid):
                self.manifest['baseline']['previousPublicFileId'] = invalid
                with self.assertRaises(pub.PublicationError):
                    self.publisher()

    def test_first_publication_rejects_any_parent_field(self):
        self.schema2()
        for invalid in [None, 0, legacy.PREVIOUS_FILE_ID]:
            self.manifest['baseline']['previousPublicFileId'] = invalid
            with self.assertRaises(pub.PublicationError):
                self.publisher()

    def test_zero_relations_complete_public_readback(self):
        self.schema2()
        self.manifest['curseforge']['uploadRelations'] = []
        self.manifest['curseforge']['expectedPublicRelations'] = []
        self.state.publish_visible = True
        with mock.patch.object(legacy, 'public_relations', return_value=[]):
            report = self.run_publisher(mode='publish', resume_file_id=legacy.NEW_FILE_ID)
        self.assertEqual([], report['publicReadback']['relations'])
        self.assertEqual(0, self.state.post_count)

    def test_zero_relations_rejects_unexpected_public_relation(self):
        self.schema2()
        self.manifest['curseforge']['uploadRelations'] = []
        self.manifest['curseforge']['expectedPublicRelations'] = []
        self.state.publish_visible = True
        with self.assertRaises(pub.PublicationError) as got:
            self.run_publisher(mode='publish', resume_file_id=legacy.NEW_FILE_ID)
        self.assertEqual('CURSEFORGE_RELATION_MISMATCH', got.exception.status)

    def test_empty_relations_previous_publication_succeeds(self):
        self.schema2('previousPublicFile')
        self.manifest['curseforge']['uploadRelations'] = []
        self.manifest['curseforge']['expectedPublicRelations'] = []
        self.state.project_relations = []
        with mock.patch.object(legacy, 'public_relations', return_value=[]):
            report = self.run_publisher()
        self.assertEqual('AUTOMATION_READY_DRY_RUN', report['status'])

    def test_absent_relation_arrays_are_not_empty_relations(self):
        for field in ['uploadRelations', 'expectedPublicRelations']:
            manifest = copy.deepcopy(self.manifest)
            manifest['curseforge'].pop(field)
            with self.assertRaises(pub.PublicationError):
                pub.validate_manifest(manifest)

    def test_lossy_tag_sanitization_cannot_mix_artifacts(self):
        self.assertNotEqual(pub.state_artifact_prefix('v1/a'), pub.state_artifact_prefix('v1-a'))
        self.assertEqual(pub.state_artifact_prefix('v1/a'), pub.state_artifact_prefix('v1/a'))
        self.manifest['release']['tag'] = 'v1/a'
        p = self.publisher()
        self.state.artifacts.append({'id': 900, 'name': pub.state_artifact_prefix('v1-a')+'98-1--intent--abcd', 'expired':False})
        self.record_persisted_intent_step('98-1', tag='v1-a')
        self.assertIsNone(p._prior_durable_state_resume_id('read-only', '100-1'))

    def test_malformed_history_missing_steps_fails_closed(self):
        self.record_persisted_intent_step('98-1')
        self.state.workflow_jobs[(98, 1)] = [{}]
        with self.assertRaises(pub.PublicationError) as got:
            self.publisher()._prior_durable_state_resume_id('read-only', '100-1')
        self.assertEqual('GITHUB_WORKFLOW_JOBS_INVALID', got.exception.status)

    def test_same_run_second_post_blocked_by_local_claim(self):
        intent, artifact = self.prepare_and_persist()
        with self.assertRaises(pub.PublicationError):
            self.publish_from_intent(intent, artifact)
        self.assertEqual(1, self.state.post_count)
        with self.assertRaises(pub.PublicationError) as got:
            self.publish_from_intent(intent, artifact)
        self.assertEqual('UPLOAD_OUTCOME_UNKNOWN', got.exception.status)
        self.assertEqual(1, self.state.post_count)

    def test_accepted_file_id_written_before_poll(self):
        intent, artifact = self.prepare_and_persist()
        p = self.publisher()
        path = self.repo_root/'result.json'
        def poll(*args):
            report = json.loads(path.read_text())
            self.assertEqual(legacy.NEW_FILE_ID, report['fileId'])
            self.assertEqual('UPLOADED_PROCESSING', report['status'])
            self.assertNotIn('valid-secret', path.read_text())
            raise pub.PublicationError('UPLOADED_PROCESSING','fixture',pub.EXIT_PROCESSING)
        with mock.patch.object(p, '_poll_public', side_effect=poll):
            with self.assertRaises(pub.PublicationError):
                p.run(mode='publish',curseforge_token='valid-secret',github_token='github-secret',
                      resume_file_id=None,poll_attempts=1,poll_interval=0,run_key=intent['runKey'],
                      intent_report=intent,intent_artifact_id=artifact,result_path=path)
        self.assertEqual(1, self.state.post_count)

    def test_manifest_change_invalidates_intent(self):
        intent, artifact = self.prepare_and_persist()
        intent['manifestSha256'] = '0'*64
        with self.assertRaises(pub.PublicationError) as got:
            self.publish_from_intent(intent, artifact)
        self.assertEqual('UPLOAD_INTENT_REPORT_MISMATCH', got.exception.status)
        self.assertEqual(0, self.state.post_count)

    def test_wrong_project_identity_blocks_before_post(self):
        self.schema2()
        self.manifest['curseforge']['projectSlug'] = 'wrong-slug'
        with self.assertRaises(pub.PublicationError) as got:
            self.run_publisher()
        self.assertEqual('CURSEFORGE_PROJECT_IDENTITY_MISMATCH', got.exception.status)

    def test_jar_version_must_belong_to_target_mod(self):
        text = '[[mods]]\nmodId="sample_mod"\nversion="wrong"\n[[mods]]\nmodId="other_mod"\nversion="'+legacy.VERSION+'"\n'
        path = self.repo_root/'bad.jar'
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('META-INF/neoforge.mods.toml',text)
        with self.assertRaises(pub.PublicationError) as got:
            self.publisher()._validate_jar_identity(path)
        self.assertEqual('JAR_VERSION_MISMATCH', got.exception.status)

    def test_false_boolean_project_identity_is_rejected(self):
        self.manifest['curseforge']['projectId'] = True
        with self.assertRaises(pub.PublicationError):
            self.publisher()

    def test_missing_project_configuration_blocks(self):
        self.manifest['curseforge']['projectId'] = None
        with self.assertRaises(pub.PublicationError) as got:
            self.publisher()
        self.assertEqual('BLOCKED_BY_MISSING_CURSEFORGE_PROJECT_CONFIGURATION',got.exception.status)

    def test_filename_and_changelog_traversal_rejected(self):
        for key, value in [('assetName','../bad.jar'), ('assetName','bad".jar'), ('changelogPath','../secret')]:
            manifest = copy.deepcopy(self.manifest)
            manifest['release'][key] = value
            with self.assertRaises(pub.PublicationError):
                pub.validate_manifest(manifest)


class PureSafetyTests(unittest.TestCase):
    def test_duplicate_manifest_keys_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'manifest.json'
            path.write_text('{"schemaVersion":1,"schemaVersion":2}')
            with self.assertRaises(pub.PublicationError):
                pub.load_manifest(path)

    def test_report_redacts_actual_secret_in_nested_values_and_keys(self):
        value = {'secret123': ['prefix-secret123-suffix', {'message':'github789'}]}
        out = json.dumps(pub.sanitized_report(value, ('secret123','github789')))
        self.assertNotIn('secret123',out)
        self.assertNotIn('github789',out)
        self.assertIn('[REDACTED]',out)

    def test_active_publisher_has_no_reference_identity(self):
        text = Path(pub.__file__).read_text()
        forbidden = ['IE'+'DCT', 'iedct'+'-cf-', 'immersive_engineer_decor_'+'controls_tool_reforged', '155'+'5214', '881'+'0946', '874'+'4461', '842'+'0050']
        for marker in forbidden:
            self.assertNotIn(marker,text)

    def test_credential_redirects_are_refused(self):
        request=urllib.request.Request('https://example.invalid/source', headers={'X-Api-Token':'fake-token'})
        self.assertIsNone(pub.NoCredentialRedirect().redirect_request(request, io.BytesIO(),302,'Moved',{},'https://other.invalid/'))

    def test_post_redirects_are_never_replayed(self):
        request=urllib.request.Request('https://example.invalid/source',data=b'x',method='POST')
        self.assertIsNone(pub.NoCredentialRedirect().redirect_request(request,io.BytesIO(),307,'Moved',{},'https://other.invalid/'))


if __name__ == '__main__':
    unittest.main()
