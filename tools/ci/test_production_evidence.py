"""Synthetic parser fixtures only: these tests do not execute or certify Minecraft."""
import copy
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import uuid
import zipfile
import zlib

from tools.ci import production_evidence as evidence
from tools.ci import qualification_report


def encoded(value):
    return json.dumps(value).encode()


def assertion(label, value):
    return {'check': label, 'actual': copy.deepcopy(value), 'expected': copy.deepcopy(value)}


def archive(mod, version, specs=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as jar:
        jar.writestr('META-INF/neoforge.mods.toml', f'license="All Rights Reserved"\n[[mods]]\nmodId="{mod}"\nversion="{version}"\n')
        for name, value in (specs or {}).items():
            jar.writestr('bop_qa/spec/' + name + '.json', encoded(value))
    return output.getvalue()


def screenshot(width=1):
    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, 1, 8, 2, 0, 0, 0))
            + chunk(b'tEXt', b'Synthetic parser fixture\x00' + b'x' * 1100)
            + chunk(b'IDAT', zlib.compress(b'\0\xff\0\0')) + chunk(b'IEND', b''))


def scoped_assertions(specs):
    result = {}
    for name in qualification_report.catalog(specs):
        if name.startswith('cutting_'):
            values = {'actual emitted outputs': evidence.BOARD_OUTPUT, 'consumes exactly one input': True, 'tool durability': 1,
                      'no repeat output': {}, 'wrong tool operation rejects': False}
        elif name.startswith('sawmill_'):
            values = {'base energy': 1600, 'real process output reload=false': {}, 'real process output reload=true': {},
                      'real process secondaries reload=true': {}, 'no energy cannot advance': True}
        elif name.startswith('harvest_'):
            values = {'foreign table cannot trigger addon': {}, 'explosion native only': {}}
            values.update({tool + ' roll=' + roll: {} for tool in ('hand', 'wrong', 'knife', 'sword', 'shears', 'silk', 'fortune') for roll in ('0.13', '0.91')})
            if name == 'harvest_barley': values['upper barley native only'] = {}
            if name == 'harvest_webbing': values['six faces at most one string'] = 1
        elif name.startswith('native_'):
            values = {f'native invariant {tool} roll={roll}': {} for tool in ('hand', 'knife', 'sword', 'shears', 'silk', 'fortune') for roll in ('0.13', '0.91')}
            if name.startswith('native_potted_'): values['pot and correct content remain'] = True
        elif name.startswith('cascade_'):
            values = {'three actual segments placed': 3, 'real player destroys attached segment': True,
                      'bonus bounded by three destroyed segments': 3, 'all three segments removed by scheduled cascade': True}
        else:
            values = {'native shears tag': True}
            values.update({f"tag {row['tag']} accepts {item}": True for row in specs['tag_integrations']['integrations'] for item in row['values']})
        result[name] = [assertion(label, value) for label, value in values.items()]
    return result


def saved_snapshot(specs, restart=False):
    machines = []
    for index in range(52):
        family, stripped = specs['wood_families']['families'][index // 4], index % 4 >= 2
        machines.append({'index': index, 'primary': {family['planks']: 6}, 'secondary': {'immersiveengineering:dust_wood': 1 if stripped else 2},
                         'energy': 31200 if stripped else 30400, 'bladeDamage': 5, 'processes': [], 'redstoneEnabled': True})
    machines[0].update(primary={'biomesoplenty:fir_planks': 12 if restart else 6}, secondary={'immersiveengineering:dust_wood': 5 if restart else 3},
                       energy=28000 if restart else 29600, bladeDamage=10 if restart else 5, redstoneEnabled=False,
                       processes=[{'tick': 40, 'stripped': True, 'sawed': False, 'input': 'biomesoplenty:fir_log', 'count': 1}])
    return {'barrel': {'minecraft:apple': 7, 'biomesoplenty:fir_log': 1}, 'marker': 'minecraft:diamond_block',
            'boardInput': {'item': 'biomesoplenty:fir_log', 'count': 1}, 'formedMachines': machines}


def fixture(specs):
    files = {'candidate.jar': archive(evidence.MOD, '0.1.1-alpha.10'), 'production-baseline.jar': archive(evidence.MOD, '0.1.1-alpha.9'),
             'production-harness.jar': archive(evidence.HARNESS, '1', specs)}
    candidate = {**evidence.jar_identity(files['candidate.jar']), 'name': 'immersive_bop_harvest-0.1.1-alpha.10.jar',
                 'size': len(files['candidate.jar']), 'sha256': evidence.sha(files['candidate.jar'])}
    deps = [{'modId': mod, 'filename': mod + '.jar', 'size': 10, 'sha256': evidence.sha(mod.encode())} for mod in sorted(evidence.DEPENDENCIES)]
    files['runtime-dependencies.json'] = encoded({'status': 'PASS', 'dependencies': deps})
    files['production-alpha9-world-backup.json'] = encoded({'source': '/synthetic/runtime/server/world', 'backup': '/synthetic/runtime/alpha9-world-backup',
                                                          'fileCount': 1, 'hashMatch': True, 'sha256': {'level.dat': 'a' * 64}})
    for phase_index, phase in enumerate(evidence.PHASES):
        baseline = phase.startswith('baseline-')
        version = '0.1.1-alpha.9' if baseline else candidate['version']
        raw = files['production-baseline.jar'] if baseline else files['candidate.jar']
        cwd = '/synthetic/runtime/' + (phase if phase in evidence.CLIENT_PHASES else 'server')
        identities = deps + [{'modId': evidence.MOD, 'filename': 'immersive_bop_harvest-' + version + '.jar', 'size': len(raw), 'sha256': evidence.sha(raw)},
                             {'modId': evidence.HARNESS, 'filename': 'bop-harvest-qualification-harness-1.jar', 'size': len(files['production-harness.jar']), 'sha256': evidence.sha(files['production-harness.jar'])}]
        runtime = {'schemaVersion': 1, 'executionMode': 'packaged-production', 'phase': phase, 'nonce': str(uuid.UUID(int=phase_index + 1)),
                   'candidateVersion': version, 'testHarnessIsSeparate': True, 'phaseStatus': 'STARTED' if phase == 'client-two' else 'PASS',
                   'checks': [], 'loadedJarIdentities': [], 'dedicatedServer': phase in evidence.SERVER_PHASES,
                   'serverStarted': phase != 'client-two', 'saveCalled': phase != 'client-two', 'serverTicks': 500}
        checks = runtime['checks']
        def add(label, value): checks.append(assertion(label, value))
        for label, value in {'owned disposable instance': runtime['nonce'], 'explicit launch profile': phase, 'production loader': True, 'exact staged mod jar count': 7}.items(): add(label, value)
        for identity in identities:
            row = {key: identity[key] for key in ('modId', 'size', 'sha256')}
            row['path'] = cwd + '/mods/' + identity['filename']
            runtime['loadedJarIdentities'].append(row)
            for label, value in {'regular packaged mod ': True, 'packaged mod path ': row['path'], 'packaged mod hash ': row['sha256'], 'packaged mod size ': row['size']}.items(): add(label + row['modId'], value)
        if phase in ('baseline-create', 'candidate-upgrade', 'client-one'):
            observations = scoped_assertions(specs)
            runtime.update(scopedCases=[{'id': name, 'passed': True, 'required': True} for name in observations], scopedAssertions=observations,
                           scopedDurationNanos=100, repeatedDurationNanos=100, repeatedBoardOperations=100,
                           repeatedAssertions={f'repeat_board_{index}': copy.deepcopy(observations['cutting_fir_log']) for index in range(100)})
            add('formed machine count', 52)
            for index, (family, key) in enumerate((family, key) for family in specs['wood_families']['families'] for key in ('log', 'wood', 'stripped_log', 'stripped_wood')):
                for label in ('formed', 'blade interaction', 'blade consumed from hand', 'power port accepts energy', 'simulated insertion accepted', 'simulation leaves queue empty', 'actual insertion consumed'): add(f'{label} {index}', True)
                add(f'blade installed {index}', 'immersiveengineering:sawblade')
                add(f'one queued input {index}', 1)
                for label, value in {'primary port ': {family['planks']: 6}, 'secondary port ': {'immersiveengineering:dust_wood': 1 if key.startswith('stripped_') else 2},
                                     'consumed energy ': 800 if key.startswith('stripped_') else 1600, 'blade wear ': 5, 'empty process queue ': True, 'no stray machine output ': 0}.items(): add(label + family[key], value)
            add('datapack reload', True)
        if phase != 'client-two':
            runtime['savedSnapshot'] = saved_snapshot(specs, phase.endswith('restart') or phase == 'multiplayer')
            if phase == 'multiplayer':
                runtime['savedSnapshot']['formedMachines'][1].update(primary={'biomesoplenty:fir_planks': 12}, secondary={'immersiveengineering:dust_wood': 4}, energy=28800)
        if phase not in ('multiplayer', 'client-two'):
            first = runtime['savedSnapshot']['formedMachines'][0]
            for label, value in {'continuity begins with empty real queue': True, 'continuity real input accepted': True, 'real redstone pauses machine': False,
                                 'paused queue still contains input': 1, 'redstone preserves queued progress': 40, 'redstone preserves stored energy': first['energy'],
                                 'save fixture board retains log': 'biomesoplenty:fir_log', 'save fixture board input count': 1}.items(): add(label, value)
            if phase in ('baseline-restart', 'candidate-upgrade', 'candidate-restart'):
                previous = saved_snapshot(specs, phase == 'candidate-upgrade')
                add('persisted world state', previous)
                for label, value in {'restored queue has exactly one input': 1, 'restored machine remains redstone paused': False,
                                     'restored queued input': 'biomesoplenty:fir_log', 'restored machine enabled by removing real redstone': True,
                                     'restored board processes retained input': True, 'restored board consumes retained input': True,
                                     'restored board actual output': evidence.BOARD_OUTPUT, 'restored blade wear': 5,
                                     'restored primary output': {'biomesoplenty:fir_planks': 18 if phase == 'candidate-upgrade' else 12},
                                     'restored secondary output without duplicate stripping': {'immersiveengineering:dust_wood': 6 if phase == 'candidate-upgrade' else 4},
                                     'restored remaining energy consumption': 800}.items(): add(label, value)
        if phase in ('multiplayer', 'client-one'):
            players = ['BopQaOne', 'BopQaTwo'] if phase == 'multiplayer' else ['BopQaOne']
            for label, value in {'client board single input': True, 'concurrent board input consumed': True, 'authoritative combined client and ground outputs': evidence.BOARD_OUTPUT,
                                 'only one actual tool use consumes durability': 1, 'all real clients sent board interactions': players,
                                 'concurrent board original input consumed': True, 'concurrent output before tool retrieval': evidence.BOARD_OUTPUT,
                                 'concurrent tools conserved including board': len(players), 'concurrent durability before tool retrieval': 1,
                                 'all client tools conserved after retrieval': len(players), 'all tools returned to client inventories': len(players)}.items(): add(label, value)
            for label, value in {'additional interactions use observed client-one': True, 'client saw fixture starts idle': True,
                                 'real client saw interaction packet': True, 'client installed real sawblade': 'immersiveengineering:sawblade',
                                 'client blade consumed from inventory': True, 'client installed blade machine accepts real input': True,
                                 'client harvest follows observed saw result': True, 'client webbing fixture is supported': True,
                                 'client harvest stage': 4, 'real client harvest uses knife tag': True,
                                 'client saw primary port delta': {'biomesoplenty:fir_planks': 12},
                                 'client saw secondary port delta': {'immersiveengineering:dust_wood': 4},
                                 'client saw energy consumed': 1600, 'client saw blade wear': 5, 'actual client broke supported webbing': True,
                                 'actual client harvest output': {'minecraft:string': 1}, 'real client IE and harvest completed': {'sawmill': True, 'harvest': True}}.items(): add(label, value)
            events = []
            extras = ('extras', 'fixture-blade-removed', 'actual-sawmill-use-item-packet', 'saw-clicked', 'harvest-ready', 'actual-harvest-break-packet', 'harvested')
            for action in ('ready', 'actual-use-item-packet', 'clicked', 'actual-board-retrieve-packet', 'cleared', 'observed', *extras, 'logout', 'rejoined', 'finished'):
                for player in players:
                    if action in ('logout', 'rejoined') and (player != 'BopQaOne' or phase != 'multiplayer'): continue
                    if action in ('actual-board-retrieve-packet', 'cleared') and (player != 'BopQaOne' or phase != 'multiplayer'): continue
                    if action in extras and player != 'BopQaOne': continue
                    events.append({'player': player, 'event': action, 'tick': len(events) + 1, 'uuid': str(uuid.UUID(int=1 if player == 'BopQaOne' else 2)), 'item': 'minecraft:iron_axe'})
                    if action == 'actual-board-retrieve-packet': events[-1]['item'] = 'minecraft:air'
                    if action == 'fixture-blade-removed': events[-1].update(item='immersiveengineering:sawblade', damage=5)
                    if action == 'actual-harvest-break-packet': events[-1]['block'] = 'biomesoplenty:webbing'
            for player in players:
                add('client observed server result ' + player, True)
                add('finished client observed output ' + player, True)
            runtime['clientInteractions'] = {'verified': True, 'maxConcurrentPlayers': len(players), 'finishedClients': len(players), 'reconnected': phase == 'multiplayer', 'events': events,
                                             'extraChecks': {'sawmill': True, 'harvest': True}}
            if phase == 'multiplayer':
                for label, value in {'two concurrent real clients': 2, 'real client reconnect': True, 'client reconnect after observed result': True,
                                     'real client retrieved parked tool': True, 'parked tool retrieval uses empty hand': True,
                                     'reconnected original identity': str(uuid.UUID(int=1)), 'reconnected saved inventory': [{'slot': i, 'item': 'minecraft:air' if i else 'farmersdelight:iron_knife', 'count': 0 if i else 1, 'damage': 0} for i in range(36)]}.items(): add(label, value)
        log = ('Synthetic parser log\nDone (\nStopping server\nAll dimensions are saved\nBOP_QA: production server started profile=' + phase).encode()
        receipt = {'passed': True, 'exitCode': 0, 'timeout': False, 'aborted': False, 'durationSeconds': 20, 'command': ['java', '-Dbop.qa.phase=' + phase],
                   'cwd': cwd, 'log': '/synthetic/runtime/receipts/' + phase + '.log', 'logSha256': evidence.sha(log), 'logBytes': len(log), 'predecessor': None}
        if phase in evidence.SERVER_PHASES: receipt['runtime'] = runtime
        else:
            files['production-' + phase + '-common.json'] = encoded(runtime)
            client = {'phase': phase, 'nonce': runtime['nonce'], 'phaseStatus': 'PASS', 'screenshots': []}
            for flag in ('titleScreen', 'joinedDedicatedServer', 'multiplayerAuthoritativeBoardResult', 'serverConfirmedReconnect', 'cleanDisconnect'): client[flag] = True
            if phase == 'client-one':
                for flag in ('createdWorld', 'integratedServer', 'singleplayerAuthoritativeBoardResult', 'cleanSingleplayerDisconnect', 'actualSawmillInteraction', 'actualHarvestInteraction'): client[flag] = True
            for stage in evidence.SCREENSHOTS[phase]:
                image = screenshot()
                files['production-' + phase + '-' + stage + '.png'] = image
                client['screenshots'].append({'stage': stage, 'file': 'bop-qa-' + stage + '.png', 'size': len(image), 'sha256': evidence.sha(image)})
            receipt['client'] = client
            files['production-' + phase + '-exit.json'] = encoded({'state': 99, 'stopRequestedByHarness': True})
        files['production-' + phase + '.json'], files['production-' + phase + '.log'] = encoded(receipt), log
    commands = []
    for kind in ('server', 'client'):
        log = b'Synthetic successful installer output'
        files['production-installer-' + kind + '.log'] = log
        commands.append({'exitCode': 0, 'durationSeconds': 1, 'command': ['java', '--install' + kind.title()], 'logSha256': evidence.sha(log)})
    files['production-preparation.json'] = encoded({'installerSha256': evidence.INSTALLER_SHA256, 'metadataSha256': evidence.METADATA_SHA256, 'commands': commands})
    files['production-orchestration.json'] = encoded([{'exitCode': 0, 'command': ['python', 'synthetic-runner.py', '--phase', phase]} for phase in evidence.PHASES])
    files['production-baseline-build.log'] = b'Synthetic parser log: BUILD SUCCESSFUL'
    baseline = files['production-baseline.jar']
    files['production-baseline-build.json'] = encoded({'schemaVersion': 1, 'sourceCommit': evidence.BASELINE_COMMIT, 'sourceTree': evidence.BASELINE_TREE,
        'sourceArchiveSha256': 'b' * 64, 'command': ['gradlew', 'clean', 'build', '--stacktrace'], 'exitCode': 0,
        'logSha256': evidence.sha(files['production-baseline-build.log']), 'logBytes': len(files['production-baseline-build.log']),
        'candidate': {**evidence.jar_identity(baseline), 'name': 'immersive_bop_harvest-0.1.1-alpha.9.jar', 'size': len(baseline), 'sha256': evidence.sha(baseline)}})
    rechain(files)
    return files, candidate


def rechain(files):
    for phase, previous in zip(evidence.SERVER_PHASES[1:], evidence.SERVER_PHASES):
        name = 'production-' + phase + '.json'
        row, old = json.loads(files[name]), json.loads(files['production-' + previous + '.json'])
        row['predecessor'] = {'phase': previous, 'nonce': old['runtime']['nonce'], 'sha256': evidence.sha(files['production-' + previous + '.json']),
                              'path': '/synthetic/runtime/receipts/' + previous + '.json'}
        if phase == 'candidate-upgrade': row['predecessor']['backupManifest'] = {'path': '/synthetic/runtime/alpha9-world-backup.json', 'sha256': evidence.sha(files['production-alpha9-world-backup.json'])}
        files[name] = encoded(row)


class ProductionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs = qualification_report.load_specs(Path(__file__).resolve().parents[2])
        cls.original, cls.candidate = fixture(cls.specs)

    def setUp(self):
        self.files = copy.deepcopy(self.original)

    def validate(self):
        return evidence.validate(self.files, self.specs, self.candidate)

    def edit(self, name, change):
        row = json.loads(self.files[name])
        change(row)
        self.files[name] = encoded(row)
        rechain(self.files)

    def check(self, phase, label, value):
        def mutate(receipt):
            runtime = receipt if phase in evidence.CLIENT_PHASES else receipt['runtime']
            row = next(row for row in runtime['checks'] if row['check'] == label)
            row['actual'] = row['expected'] = value
        self.edit('production-' + phase + ('-common' if phase in evidence.CLIENT_PHASES else '') + '.json', mutate)

    def test_synthetic_envelope_cannot_authenticate_or_claim_stable_ready(self):
        with patch.object(qualification_report, 'validate', wraps=qualification_report.validate) as scoped:
            result = self.validate()
        self.assertFalse(result['authenticatedExecution'])
        self.assertFalse(result['stableReady'])
        self.assertEqual('INTEGRITY_ONLY_PACKAGED_EXECUTION', result['status'])
        self.assertEqual(20, result['phaseMeasurements']['client-one']['durationSeconds'])
        self.assertEqual(1, result['candidateUpgradeToBaselineCreateDurationRatio'])
        self.assertEqual(3, scoped.call_count)
        self.assertTrue(all(call.kwargs['expected_mode'] == 'packaged-production' for call in scoped.call_args_list))

    def test_missing_or_unsuccessful_phase_never_qualifies(self):
        for phase in evidence.PHASES:
            for field, value in (('passed', 1), ('exitCode', False), ('timeout', True), ('aborted', True), ('durationSeconds', 0)):
                self.files = copy.deepcopy(self.original)
                self.edit('production-' + phase + '.json', lambda row: row.update({field: value}))
                with self.subTest(phase=phase, field=field), self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        self.edit('production-baseline-create.json', lambda row: row.pop('aborted'))
        with self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        self.files.pop('production-client-two.json')
        with self.assertRaises(KeyError): self.validate()

    def test_log_bytes_and_chain_are_bound(self):
        self.files['production-candidate-upgrade.log'] += b'changed'
        with self.assertRaisesRegex(ValueError, 'log'): self.validate()
        self.files = copy.deepcopy(self.original)
        row = json.loads(self.files['production-candidate-upgrade.json'])
        row['predecessor']['sha256'] = '0' * 64
        self.files['production-candidate-upgrade.json'] = encoded(row)
        with self.assertRaisesRegex(ValueError, 'predecessor'): self.validate()

    def test_duplicate_nonce_and_wrong_phase_are_rejected(self):
        for key, value in (('nonce', str(uuid.UUID(int=1))), ('phase', 'candidate-upgrade'), ('schemaVersion', True)):
            self.files = copy.deepcopy(self.original)
            self.edit('production-candidate-restart.json', lambda row: row['runtime'].update({key: value}))
            with self.subTest(key=key), self.assertRaises(ValueError): self.validate()

    def test_changed_candidate_harness_or_dependency_is_rejected_even_with_matching_checks(self):
        for mod in (evidence.MOD, evidence.HARNESS, 'farmersdelight'):
            self.files = copy.deepcopy(self.original)
            def mutate(receipt):
                runtime = receipt['runtime']
                next(row for row in runtime['loadedJarIdentities'] if row['modId'] == mod)['sha256'] = '0' * 64
                row = next(row for row in runtime['checks'] if row['check'] == 'packaged mod hash ' + mod)
                row['actual'] = row['expected'] = '0' * 64
            self.edit('production-candidate-upgrade.json', mutate)
            with self.subTest(mod=mod), self.assertRaises(ValueError): self.validate()

    def test_duplicate_loaded_identity_and_external_mod_path_rejected(self):
        self.edit('production-client-two-common.json', lambda row: row['loadedJarIdentities'].__setitem__(0, row['loadedJarIdentities'][1]))
        with self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        self.edit('production-candidate-upgrade.json', lambda row: row['runtime']['loadedJarIdentities'][0].update(path='/other/mod.jar'))
        with self.assertRaises(ValueError): self.validate()

    def test_fixed_baseline_source_build_and_raw_bytes_are_required(self):
        self.edit('production-baseline-build.json', lambda row: row.update(sourceCommit='0' * 40))
        with self.assertRaisesRegex(ValueError, 'baseline'): self.validate()
        self.files = copy.deepcopy(self.original)
        self.files['production-baseline.jar'] = archive(evidence.MOD, '0.1.1-alpha.10')
        with self.assertRaisesRegex(ValueError, 'baseline'): self.validate()

    def test_false_saved_board_and_machine_outputs_cannot_be_self_attested(self):
        for label, value in (('restored board actual output', {}), ('restored primary output', {'biomesoplenty:fir_planks': 600}),
                             ('restored secondary output without duplicate stripping', {'immersiveengineering:dust_wood': 99}), ('restored remaining energy consumption', True)):
            self.files = copy.deepcopy(self.original)
            self.check('candidate-restart', label, value)
            with self.subTest(label=label), self.assertRaises(ValueError): self.validate()

    def test_missing_inflight_state_and_changed_snapshot_rejected(self):
        self.edit('production-candidate-restart.json', lambda row: row['runtime']['savedSnapshot']['formedMachines'][0].update(processes=[]))
        with self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        self.edit('production-candidate-restart.json', lambda row: row['runtime']['savedSnapshot']['formedMachines'][0]['primary'].update({'biomesoplenty:fir_planks': 18}))
        with self.assertRaisesRegex(ValueError, 'transition'): self.validate()

    def test_formed_machine_counts_and_semantic_ports_are_required(self):
        for label, value in (('formed machine count', 51), ('primary port biomesoplenty:fir_log', True), ('one queued input 0', True)):
            self.files = copy.deepcopy(self.original)
            self.check('candidate-upgrade', label, value)
            with self.subTest(label=label), self.assertRaises(ValueError): self.validate()

    def test_scoped_and_repeated_observations_are_not_aggregate_pass_lists(self):
        self.edit('production-candidate-upgrade.json', lambda row: row['runtime']['scopedAssertions'].pop('cutting_fir_log'))
        with self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        self.edit('production-candidate-upgrade.json', lambda row: row['runtime']['repeatedAssertions'].pop('repeat_board_99'))
        with self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        def mutate(row):
            value = next(value for value in row['runtime']['repeatedAssertions']['repeat_board_0'] if value['check'] == 'actual emitted outputs')
            value['actual'] = value['expected'] = True
        self.edit('production-candidate-upgrade.json', mutate)
        with self.assertRaises(ValueError): self.validate()

    def test_client_flags_exit_hook_and_screenshots_required(self):
        self.edit('production-client-one.json', lambda row: row['client'].update(cleanSingleplayerDisconnect=1))
        with self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        self.edit('production-client-one-exit.json', lambda row: row.update(stopRequestedByHarness=False))
        with self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        self.files['production-client-two-title.png'] += b'changed'
        with self.assertRaisesRegex(ValueError, 'screenshot'): self.validate()
        self.files = copy.deepcopy(self.original)
        raw = screenshot(width=0)
        self.files['production-client-two-title.png'] = raw
        self.edit('production-client-two.json', lambda row: row['client']['screenshots'][0].update(size=len(raw), sha256=evidence.sha(raw)))
        with self.assertRaisesRegex(ValueError, 'dimensions'): self.validate()

    def test_client_pass_flags_cannot_replace_server_owned_packet_events(self):
        def mutate(row):
            interactions = row['runtime']['clientInteractions']
            interactions['events'] = [event for event in interactions['events'] if event['event'] != 'actual-use-item-packet']
        self.edit('production-multiplayer.json', mutate)
        with self.assertRaisesRegex(ValueError, 'packets'): self.validate()
        self.files = copy.deepcopy(self.original)
        self.check('multiplayer', 'authoritative combined client and ground outputs', {'biomesoplenty:stripped_fir_log': 2, 'farmersdelight:tree_bark': 2})
        with self.assertRaises(ValueError): self.validate()

    def test_board_accepts_late_empty_hand_and_unordered_java_player_set(self):
        def mutate(row):
            runtime = row['runtime']
            check = next(check for check in runtime['checks'] if check['check'] == 'all real clients sent board interactions')
            check['actual'].reverse()
            events = runtime['clientInteractions']['events']
            clicked = next(event for event in events if event['event'] == 'clicked' and event['player'] == 'BopQaOne')
            events.append({'event': 'actual-use-item-packet', 'player': 'BopQaOne', 'tick': clicked['tick'], 'item': 'minecraft:air'})
            events.sort(key=lambda event: event['tick'])
        self.edit('production-multiplayer.json', mutate)
        self.assertEqual('INTEGRITY_ONLY_PACKAGED_EXECUTION', self.validate()['status'])

    def test_only_exact_board_identity_label_has_unordered_semantics(self):
        for label in ('other ordered observation', 'all real clients sent board interactions '):
            row = assertion(label, ['BopQaOne', 'BopQaTwo'])
            row['actual'].reverse()
            with self.subTest(label=label), self.assertRaises(ValueError): evidence.observed([row])
        with self.assertRaises(ValueError): evidence.observed([{'check': 'other typed observation', 'actual': True, 'expected': 1}])

    def test_board_identity_sets_reject_unknown_duplicate_and_mismatched_players(self):
        for value in (['BopQaOne', 'UnknownPlayer'], ['BopQaOne', 'BopQaOne'], [True], []):
            with self.subTest(value=value, side='both'), self.assertRaises(ValueError):
                evidence.observed([assertion('all real clients sent board interactions', value)])
            for side in ('actual', 'expected'):
                row = assertion('all real clients sent board interactions', ['BopQaOne', 'BopQaTwo'])
                row[side] = value
                with self.subTest(value=value, side=side), self.assertRaises(ValueError): evidence.observed([row])
        with self.assertRaises(ValueError):
            evidence.observed([{'check': 'all real clients sent board interactions', 'actual': ['BopQaOne'], 'expected': ['BopQaTwo']}])

    def test_board_packet_item_actor_and_event_window_remain_strict(self):
        for change in ('wrong-item', 'unknown-player', 'air-only', 'before-ready', 'after-clicked', 'duplicate-ready'):
            self.files = copy.deepcopy(self.original)
            def mutate(row):
                events = row['runtime']['clientInteractions']['events']
                use = next(event for event in events if event['event'] == 'actual-use-item-packet' and event['player'] == 'BopQaOne')
                ready = next(event for event in events if event['event'] == 'ready' and event['player'] == 'BopQaOne')
                clicked = next(event for event in events if event['event'] == 'clicked' and event['player'] == 'BopQaOne')
                if change == 'wrong-item': events.append({**use, 'item': 'minecraft:diamond_sword'})
                elif change == 'unknown-player': events.append({**use, 'player': 'UnknownPlayer'})
                elif change == 'air-only': use['item'] = 'minecraft:air'
                elif change == 'before-ready': use['tick'] = ready['tick'] - 1
                elif change == 'after-clicked': use['tick'] = clicked['tick'] + 1
                else: events.append(copy.deepcopy(ready))
                events.sort(key=lambda event: event['tick'])
            self.edit('production-multiplayer.json', mutate)
            with self.subTest(change=change), self.assertRaises(ValueError): self.validate()

    def test_board_requires_measured_outputs_durability_and_tool_conservation_before_and_after(self):
        labels = ('concurrent board original input consumed', 'concurrent output before tool retrieval', 'concurrent tools conserved including board',
                  'concurrent durability before tool retrieval', 'all client tools conserved after retrieval', 'all tools returned to client inventories')
        for phase in ('client-one', 'multiplayer'):
            for label in labels:
                self.files = copy.deepcopy(self.original)
                def mutate(row):
                    runtime = row if phase == 'client-one' else row['runtime']
                    runtime['checks'] = [check for check in runtime['checks'] if check['check'] != label]
                self.edit('production-' + phase + ('-common' if phase == 'client-one' else '') + '.json', mutate)
                with self.subTest(phase=phase, label=label), self.assertRaises(ValueError): self.validate()
        for label, value in (('concurrent output before tool retrieval', {}), ('concurrent tools conserved including board', 3),
                             ('concurrent durability before tool retrieval', 2), ('all client tools conserved after retrieval', True), ('all tools returned to client inventories', 1)):
            self.files = copy.deepcopy(self.original)
            self.check('multiplayer', label, value)
            with self.subTest(label=label, value=value), self.assertRaises(ValueError): self.validate()

    def test_board_without_parked_tool_needs_no_retrieval_event_or_claim(self):
        def mutate(row):
            runtime = row['runtime']
            runtime['checks'] = [check for check in runtime['checks'] if check['check'] not in ('real client retrieved parked tool', 'parked tool retrieval uses empty hand')]
            interactions = runtime['clientInteractions']
            interactions['events'] = [event for event in interactions['events'] if event['event'] not in ('actual-board-retrieve-packet', 'cleared')]
        self.edit('production-multiplayer.json', mutate)
        self.assertEqual('INTEGRITY_ONLY_PACKAGED_EXECUTION', self.validate()['status'])

    def test_parked_tool_retrieval_requires_one_real_empty_hand_packet_and_paired_command(self):
        changes = ('wrong-player', 'nonempty-hand', 'before-clicked', 'after-observed', 'duplicate-packet', 'missing-packet',
                   'missing-command', 'duplicate-command', 'wrong-command-player', 'wrong-command-uuid', 'command-before-packet',
                   'missing-empty-hand-check', 'false-retrieval-check')
        for change in changes:
            self.files = copy.deepcopy(self.original)
            def mutate(row):
                runtime = row['runtime']
                events = runtime['clientInteractions']['events']
                packet = next(event for event in events if event['event'] == 'actual-board-retrieve-packet')
                command = next(event for event in events if event['event'] == 'cleared')
                if change == 'wrong-player': packet['player'] = 'BopQaTwo'
                elif change == 'nonempty-hand': packet['item'] = 'minecraft:iron_axe'
                elif change == 'before-clicked': packet['tick'] = next(event['tick'] for event in events if event['event'] == 'clicked' and event['player'] == 'BopQaOne')
                elif change == 'after-observed': packet['tick'] = next(event['tick'] for event in events if event['event'] == 'observed' and event['player'] == 'BopQaOne')
                elif change == 'duplicate-packet': events.append(copy.deepcopy(packet))
                elif change == 'missing-packet': events.remove(packet)
                elif change == 'missing-command': events.remove(command)
                elif change == 'duplicate-command': events.append(copy.deepcopy(command))
                elif change == 'wrong-command-player': command['player'] = 'BopQaTwo'
                elif change == 'wrong-command-uuid': command['uuid'] = str(uuid.UUID(int=3))
                elif change == 'command-before-packet': command['tick'] = packet['tick'] - 1
                elif change == 'missing-empty-hand-check': runtime['checks'] = [check for check in runtime['checks'] if check['check'] != 'parked tool retrieval uses empty hand']
                else:
                    check = next(check for check in runtime['checks'] if check['check'] == 'real client retrieved parked tool')
                    check['actual'] = check['expected'] = False
                events.sort(key=lambda event: event['tick'])
            self.edit('production-multiplayer.json', mutate)
            with self.subTest(change=change), self.assertRaises(ValueError): self.validate()

    def test_reconnect_requires_observed_identity_and_intervening_logout(self):
        def mutate(row):
            events = row['runtime']['clientInteractions']['events']
            next(event for event in events if event['event'] == 'rejoined')['uuid'] = str(uuid.UUID(int=3))
        self.edit('production-multiplayer.json', mutate)
        with self.assertRaisesRegex(ValueError, 'identity'): self.validate()

    def test_client_ie_harvest_flags_require_actual_packets_and_measured_outputs(self):
        for action in ('actual-sawmill-use-item-packet', 'actual-harvest-break-packet'):
            self.files = copy.deepcopy(self.original)
            def mutate(row):
                interactions = row['runtime']['clientInteractions']
                interactions['events'] = [event for event in interactions['events'] if event['event'] != action]
            self.edit('production-multiplayer.json', mutate)
            with self.subTest(action=action), self.assertRaisesRegex(ValueError, 'event'): self.validate()
        self.files = copy.deepcopy(self.original)
        self.check('client-one', 'actual client harvest output', {'minecraft:string': 2})
        with self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        self.edit('production-multiplayer.json', lambda row: row['runtime']['savedSnapshot']['formedMachines'][0].update(energy=1))
        with self.assertRaisesRegex(ValueError, 'more than'): self.validate()

    def test_installer_orchestration_and_backup_are_bound(self):
        self.edit('production-preparation.json', lambda row: row['commands'][0].update(exitCode=False))
        with self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        self.edit('production-orchestration.json', lambda row: row.pop())
        with self.assertRaises(ValueError): self.validate()
        self.files = copy.deepcopy(self.original)
        self.edit('production-alpha9-world-backup.json', lambda row: row.update(source='/other/world'))
        with self.assertRaises(ValueError): self.validate()

    def test_collect_exports_exact_raw_files_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root, baseline, destination = (Path(directory) / name for name in ('runtime', 'baseline', 'evidence'))
            for name, raw in self.files.items():
                if not name.startswith('production-'): continue
                short = name.removeprefix('production-')
                if short in ('baseline.jar', 'baseline-build.json', 'baseline-build.log'):
                    target = baseline / ('immersive_bop_harvest-0.1.1-alpha.9.jar' if short == 'baseline.jar' else short)
                elif short == 'harness.jar': target = root / 'server/mods/bop-harvest-qualification-harness-1.jar'
                elif any(short == phase + suffix for phase in evidence.PHASES for suffix in ('.json', '.log')): target = root / 'receipts' / short
                elif any(short == phase + '-common.json' for phase in evidence.CLIENT_PHASES): target = root / short.removesuffix('-common.json') / 'bop-qa-result.json'
                elif any(short == phase + '-exit.json' for phase in evidence.CLIENT_PHASES): target = root / short.removesuffix('-exit.json') / 'bop-qa-client-exit.json'
                elif short.endswith('.png'):
                    phase = next(phase for phase in evidence.CLIENT_PHASES if short.startswith(phase + '-'))
                    target = root / phase / 'screenshots' / ('bop-qa-' + short.removeprefix(phase + '-'))
                else: target = root / short
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            collected = evidence.collect(root, destination, baseline_build=baseline)
            self.assertEqual({name: raw for name, raw in self.files.items() if name.startswith('production-')}, collected)
            self.assertEqual(collected, {p.name: p.read_bytes() for p in destination.iterdir()})
            with self.assertRaisesRegex(ValueError, 'already contains'): evidence.collect(root, destination, baseline_build=baseline)


if __name__ == '__main__':
    unittest.main()
