"""Alpha-to-stable transition uses loopback fixtures only, never production."""
import copy
import unittest
from unittest import mock
import test_publish_curseforge as legacy
import test_publisher_portability as portability
import publish_curseforge as pub


class TransitionTests(unittest.TestCase):
    setUp = legacy.PublisherTests.setUp
    tearDown = legacy.PublisherTests.tearDown
    run_publisher = legacy.PublisherTests.run_publisher
    publisher = portability.PortabilityTests.publisher
    schema2 = portability.PortabilityTests.schema2
    prepare_and_persist = legacy.PublisherTests.prepare_and_persist
    publish_from_intent = legacy.PublisherTests.publish_from_intent
    record_persisted_intent_step = legacy.PublisherTests.record_persisted_intent_step

    def transition(self):
        self.schema2('previousPublicFile')
        self.manifest['schemaVersion'] = 3
        self.manifest['baseline'].update(releaseType='alpha', gameVersionNames=['1.21.1','NeoForge','Client'])
        previous = legacy.FakeState.prior_file()
        previous.update(releaseType=3, gameVersions=['1.21.1','NeoForge','Client'])
        return previous

    def test_legacy_alpha_to_release_fails_closed(self):
        self.schema2('previousPublicFile')
        previous = legacy.FakeState.prior_file()
        previous['releaseType'] = 3
        with mock.patch.object(legacy.FakeState, 'prior_file', return_value=previous):
            with self.assertRaises(pub.PublicationError) as got:
                self.run_publisher()
        self.assertEqual('CURSEFORGE_BASELINE_RELEASE_TYPE_DRIFTED',got.exception.status)
        self.assertEqual(0,self.state.post_count)

    def test_explicit_alpha_to_release_has_exact_new_target_readback(self):
        previous = self.transition()
        with mock.patch.object(legacy.FakeState, 'prior_file', return_value=previous):
            intent, artifact = self.prepare_and_persist()
            self.state.publish_visible = True
            report = self.publish_from_intent(intent, artifact)
        self.assertEqual('PUBLISHED_VERIFIED',report['status'])
        self.assertEqual(1,self.state.post_count)  # Local fixture POST only.
        self.assertEqual('release',legacy.parse_metadata(self.state.upload_body,self.state.upload_content_type)['releaseType'])

    def test_wrong_historical_identity_type_status_or_labels_rejected(self):
        original = self.transition()
        for key, value in [('id',3),('projectId',4),('status',1),('releaseType',1),('releaseType',True),('gameVersions',['1.21.1'])]:
            previous = copy.deepcopy(original); previous[key] = value
            with self.subTest(key=key,value=value), mock.patch.object(legacy.FakeState,'prior_file',return_value=previous):
                with self.assertRaises(pub.PublicationError):
                    self.run_publisher()
        self.assertEqual(0,self.state.post_count)

    def test_missing_or_invalid_transition_fields_rejected(self):
        self.transition()
        original = copy.deepcopy(self.manifest)
        for key, value in [('releaseType',None),('releaseType','stable'),('releaseType',[]),('gameVersionNames',[]),('gameVersionNames',['Client','Client']),('gameVersionNames','Client')]:
            self.manifest = copy.deepcopy(original)
            if value is None: self.manifest['baseline'].pop(key)
            else: self.manifest['baseline'][key]=value
            with self.subTest(key=key,value=value), self.assertRaises(pub.PublicationError):
                self.publisher()
        self.manifest = copy.deepcopy(original)
        self.manifest['curseforge']['releaseType']='stable'
        with self.assertRaises(pub.PublicationError): self.publisher()

    def test_transition_does_not_relax_missing_relations(self):
        previous = self.transition()
        self.state.project_relations=[]
        with mock.patch.object(legacy.FakeState,'prior_file',return_value=previous):
            with self.assertRaises(pub.PublicationError) as got: self.run_publisher()
        self.assertEqual('CURSEFORGE_PROJECT_RELATION_MISMATCH',got.exception.status)
        self.assertEqual(0,self.state.post_count)

    def test_transition_fields_are_bound_into_intent(self):
        previous = self.transition()
        with mock.patch.object(legacy.FakeState,'prior_file',return_value=previous):
            intent, artifact = self.prepare_and_persist()
            self.manifest['baseline']['releaseType']='beta'
            with self.assertRaises(pub.PublicationError): self.publish_from_intent(intent,artifact)
        self.assertEqual(0,self.state.post_count)

    def test_schema3_first_publication_still_requires_empty_inventory(self):
        self.schema2(); self.manifest['schemaVersion']=3
        self.state.files[legacy.PREVIOUS_FILE_ID]=self.state.prior_file()
        with self.assertRaises(pub.PublicationError) as got: self.run_publisher()
        self.assertEqual('FIRST_PUBLICATION_PROJECT_NOT_EMPTY',got.exception.status)

    def test_schema3_zero_relations_remains_supported_explicitly(self):
        previous=self.transition()
        self.manifest['curseforge']['uploadRelations']=[]
        self.manifest['curseforge']['expectedPublicRelations']=[]
        self.state.project_relations=[]
        with mock.patch.object(legacy.FakeState,'prior_file',return_value=previous), mock.patch.object(legacy,'public_relations',return_value=[]):
            self.assertEqual('AUTOMATION_READY_DRY_RUN', self.run_publisher()['status'])
