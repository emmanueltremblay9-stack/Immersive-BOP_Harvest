"""Envelope regressions only; synthetic fixtures never certify Minecraft."""
import copy
import json
from pathlib import Path
import unittest

from tools.ci import qualification_report as report


class QualificationReportTests(unittest.TestCase):
    def setUp(self):
        self.specs = {
            'wood_families': {'families': []}, 'flower_cutting_recipes': {'recipes': [{'source': 'biomesoplenty:rose'}]},
            'plant_cutting_recipes': {'recipes': []}, 'direct_harvest_rules': {'rules': [{'blocks': ['biomesoplenty:barley', 'biomesoplenty:webbing']}]},
            'tag_integrations': {'integrations': [{'tag':'c:crops/grain', 'values':['biomesoplenty:barley']}]},
            'coverage_inventory': {'potted_plants': [{'id': 'biomesoplenty:potted_rose'}]}}
        self.fixture = {'schemaVersion': 1, 'candidateVersion': '0.1.1-alpha.10', 'executionMode': 'development-classpath', 'cases': [], 'assertions': {}}
        for name in report.catalog(self.specs):
            self.fixture['cases'].append({'id': 'bop_qa.'+name, 'passed': True, 'required': True, 'error': None})
            if name.startswith('cutting_'):
                labels=['actual emitted outputs', 'consumes exactly one input', 'tool durability', 'no repeat output', 'wrong tool operation rejects']
            elif name.startswith('harvest_'):
                labels=['foreign table cannot trigger addon','explosion native only']+[tool+' roll='+roll for tool in ('hand','wrong','knife','sword','shears','silk','fortune') for roll in ('0.2','0.5')]
                labels += ['upper barley native only'] if name=='harvest_barley' else ['six faces at most one string']
            elif name.startswith('native_'):
                labels=[f'native invariant {tool} roll={roll}' for tool in ('hand','knife','sword','shears','silk','fortune') for roll in ('0.13','0.91')]+['pot and correct content remain']
            elif name.startswith('cascade_'):
                labels=['three actual segments placed','real player destroys attached segment','bonus bounded by three destroyed segments','all three segments removed by scheduled cascade']
            else: labels=['tag c:crops/grain accepts biomesoplenty:barley','native shears tag']
            self.fixture['assertions'][name]=[{'check':label,'actual':True,'expected':True} for label in labels]

    def validate(self):
        return report.validate(json.dumps(self.fixture).encode(), self.specs, '0.1.1-alpha.10')

    def test_scope_envelope_never_claims_packaged_or_formed_machine_proof(self):
        result=self.validate()
        self.assertFalse(result['packagedRuntime'])
        self.assertFalse(result['formedSawmillPorts'])
        self.assertEqual(len(report.catalog(self.specs)),result['cases'])

    def test_missing_duplicate_optional_failed_and_stale_cases_rejected(self):
        original=copy.deepcopy(self.fixture)
        for change in ('missing','duplicate','optional','failed','version','schema'):
            self.fixture=copy.deepcopy(original)
            if change=='missing':self.fixture['cases'].pop()
            elif change=='duplicate':self.fixture['cases'].append(self.fixture['cases'][0])
            elif change=='optional':self.fixture['cases'][0]['required']=False
            elif change=='failed':self.fixture['cases'][0]['passed']=False
            elif change=='version':self.fixture['candidateVersion']='0.1.1-alpha.9'
            else:self.fixture['schemaVersion']=True
            with self.subTest(change=change), self.assertRaises(ValueError):self.validate()

    def test_false_or_missing_actual_interaction_assertions_rejected(self):
        original=copy.deepcopy(self.fixture)
        for change in ('wrong-output','missing-operation','missing-observations','empty-case'):
            self.fixture=copy.deepcopy(original)
            checks=self.fixture['assertions']['cutting_rose']
            if change=='wrong-output':checks[0]['actual']=False
            elif change=='missing-operation':checks.pop(0)
            elif change=='missing-observations':self.fixture['assertions'].pop('cutting_rose')
            else:checks.clear()
            with self.subTest(change=change),self.assertRaises(ValueError):self.validate()

    def test_omitted_tags_barley_webbing_and_repeated_native_assertions_rejected(self):
        original=copy.deepcopy(self.fixture)
        for name,label in [('runtime_tags','tag c:crops/grain accepts biomesoplenty:barley'),('harvest_barley','upper barley native only'),('harvest_webbing','six faces at most one string')]:
            self.fixture=copy.deepcopy(original)
            self.fixture['assertions'][name]=[row for row in self.fixture['assertions'][name] if row['check']!=label]
            with self.subTest(name=name),self.assertRaises(ValueError):self.validate()
        self.fixture=copy.deepcopy(original)
        checks=self.fixture['assertions']['native_potted_rose']
        self.fixture['assertions']['native_potted_rose']=[checks[0]]*12+[checks[-1]]
        with self.assertRaises(ValueError):self.validate()


if __name__=='__main__':unittest.main()
