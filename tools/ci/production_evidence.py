"""Check packaged runtime evidence integrity; only the caller can authenticate CI execution."""
from __future__ import annotations

import io
import json
import math
from pathlib import Path
import re
import stat
import struct
import tomllib
import uuid
import zipfile
import zlib

from tools.ci.candidate_evidence import jar_identity, read_json, require, sha
from tools.ci import qualification_report
from tools.ci.prepare_production_runtime import INSTALLER_SHA256, METADATA_SHA256
from tools.ci.build_qualification_baseline import COMMIT as BASELINE_COMMIT, TREE as BASELINE_TREE

SERVER_PHASES = ('baseline-create', 'baseline-restart', 'candidate-upgrade', 'candidate-restart', 'multiplayer')
CLIENT_PHASES = ('client-one', 'client-two')
PHASES = SERVER_PHASES + CLIENT_PHASES
MOD = 'immersive_bop_harvest'
HARNESS = 'bop_harvest_qa'
DEPENDENCIES = {'biomesoplenty', 'glitchcore', 'terrablender', 'farmersdelight', 'immersiveengineering'}
BOARD_OUTPUT = {'biomesoplenty:stripped_fir_log': 1, 'farmersdelight:tree_bark': 1}
SCREENSHOTS = {
    'client-one': ('title', 'world-and-formed-sawmills', 'singleplayer-board-result', 'sawmill-client-result-singleplayer', 'harvest-client-result-singleplayer',
                   'multiplayer-board-result', 'sawmill-client-result-multiplayer', 'harvest-client-result-multiplayer', 'reconnect-complete'),
    'client-two': ('title', 'multiplayer-board-result', 'reconnect-complete'),
}


def equal(actual, expected):
    # Python otherwise treats true, 1 and 1.0 as interchangeable receipt values.
    return json.dumps(actual, sort_keys=True, allow_nan=False) == json.dumps(expected, sort_keys=True, allow_nan=False)


def path(value):
    require(type(value) is str and bool(value) and '\x00' not in value, 'Invalid evidence path')
    value = value.replace('\\', '/')
    require(value.startswith('/') or re.match(r'^[A-Za-z]:/', value), 'Evidence path is not absolute')
    require(not any(part in {'.', '..'} for part in value.split('/')), 'Traversing evidence path')
    return value.rstrip('/')


def observed(rows):
    require(type(rows) is list and bool(rows), 'Missing observed assertions')
    checks = {}
    for row in rows:
        require(type(row) is dict and set(row) == {'check', 'actual', 'expected'}, 'Malformed observed assertion')
        require(type(row['check']) is str and bool(row['check']) and row['check'] not in checks, 'Duplicate/invalid observed check')
        if row['check'] == 'all real clients sent board interactions':
            for players in (row['actual'], row['expected']):
                require(type(players) is list and bool(players) and all(type(player) is str and player in {'BopQaOne', 'BopQaTwo'} for player in players)
                        and len(players) == len(set(players)), 'Invalid/duplicate observed client identities')
            require(set(row['actual']) == set(row['expected']), 'Failed observed client identity set')
        else:
            require(equal(row['actual'], row['expected']), 'Failed observed assertion: ' + row['check'])
        checks[row['check']] = row['actual']
    return checks


def expect(checks, label, value):
    require(label in checks and equal(checks[label], value), 'Missing/wrong observation: ' + label)


def positive(value):
    return type(value) in {int, float} and math.isfinite(value) and value > 0


def png(raw):
    require(raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw) > 1000, 'Missing actual PNG screenshot')
    offset = 8
    chunks = []
    dimensions = None
    while offset < len(raw):
        require(offset + 12 <= len(raw), 'Truncated PNG chunk')
        size, kind = struct.unpack('>I4s', raw[offset:offset + 8])
        end = offset + 12 + size
        require(end <= len(raw), 'Truncated PNG payload')
        payload = raw[offset + 8:end - 4]
        require(zlib.crc32(kind + payload) == int.from_bytes(raw[end - 4:end], 'big'), 'PNG chunk CRC mismatch')
        if not chunks:
            require(kind == b'IHDR' and size == 13, 'Missing PNG dimensions')
            dimensions = struct.unpack('>II', payload[:8])
            require(all(0 < dimension <= 16384 for dimension in dimensions), 'Invalid PNG dimensions')
        chunks.append(kind)
        offset = end
    require(chunks.count(b'IHDR') == 1 and b'IDAT' in chunks and chunks[-1] == b'IEND' and chunks.count(b'IEND') == 1, 'Incomplete PNG image')
    return dimensions


def collect(runtime_root: Path, destination: Path, *, baseline_build: Path) -> dict[str, bytes]:
    """Copy a fixed flat evidence inventory, without following receipt-controlled paths."""
    root = runtime_root.absolute()
    def read_file(source):
        source = source.absolute()
        for item in [source, *source.parents]:
            require(not item.is_symlink() and not (getattr(item.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT), 'Linked evidence input')
        require(source.is_file(), 'Missing regular evidence input')
        return source.read_bytes()
    def read(relative):
        return read_file(root / relative)
    files = {}
    for phase in PHASES:
        for suffix in ('.json', '.log'):
            files['production-' + phase + suffix] = read('receipts/' + phase + suffix)
    for name in ('preparation.json', 'orchestration.json', 'alpha9-world-backup.json', 'installer-server.log', 'installer-client.log'):
        files['production-' + name] = read(name)
    for phase in CLIENT_PHASES:
        files['production-' + phase + '-common.json'] = read(phase + '/bop-qa-result.json')
        files['production-' + phase + '-exit.json'] = read(phase + '/bop-qa-client-exit.json')
        for stage in SCREENSHOTS[phase]:
            files['production-' + phase + '-' + stage + '.png'] = read(phase + '/screenshots/bop-qa-' + stage + '.png')
    loaded = read_json(files['production-multiplayer.json'])['runtime']['loadedJarIdentities']
    harness = [row for row in loaded if row['modId'] == HARNESS]
    require(len(harness) == 1, 'Missing unique packaged harness')
    name = path(harness[0]['path']).rsplit('/', 1)[1]
    files['production-harness.jar'] = read('server/mods/' + name)
    require(sha(files['production-harness.jar']) == harness[0]['sha256'], 'Harness bytes changed after execution')
    for source, name in (('baseline-build.json', 'baseline-build.json'), ('baseline-build.log', 'baseline-build.log'),
                         ('immersive_bop_harvest-0.1.1-alpha.9.jar', 'baseline.jar')):
        files['production-' + name] = read_file(baseline_build / source)
    for item in [destination.absolute(), *destination.absolute().parents]:
        if item.exists():
            require(not item.is_symlink() and not (getattr(item.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT), 'Linked evidence destination')
    destination.mkdir(parents=True, exist_ok=True)
    require(not any((destination / name).exists() for name in files), 'Production evidence destination already contains captured files')
    for name, raw in files.items():
        with (destination / name).open('xb') as output:
            output.write(raw)
    return files


def machine_checks(checks, specs):
    families = specs['wood_families']['families']
    require(len(families) == 13, 'Unexpected 52-machine scope')
    expect(checks, 'formed machine count', 52)
    for index, (family, key) in enumerate((family, key) for family in families for key in ('log', 'wood', 'stripped_log', 'stripped_wood')):
        for label in ('formed', 'blade interaction', 'blade consumed from hand', 'power port accepts energy', 'simulated insertion accepted', 'simulation leaves queue empty', 'actual insertion consumed'):
            expect(checks, f'{label} {index}', True)
        expect(checks, f'blade installed {index}', 'immersiveengineering:sawblade')
        expect(checks, f'one queued input {index}', 1)
        source = family[key]
        expect(checks, 'primary port ' + source, {family['planks']: 6})
        expect(checks, 'secondary port ' + source, {'immersiveengineering:dust_wood': 1 if key.startswith('stripped_') else 2})
        expect(checks, 'consumed energy ' + source, 800 if key.startswith('stripped_') else 1600)
        expect(checks, 'blade wear ' + source, 5)
        expect(checks, 'empty process queue ' + source, True)
        expect(checks, 'no stray machine output ' + source, 0)


def snapshot(runtime, specs, checks):
    saved = runtime['savedSnapshot']
    require(type(saved) is dict and set(saved) == {'barrel', 'marker', 'boardInput', 'formedMachines'}, 'Malformed saved snapshot')
    require(equal(saved['barrel'], {'minecraft:apple': 7, 'biomesoplenty:fir_log': 1}) and saved['marker'] == 'minecraft:diamond_block'
            and equal(saved['boardInput'], {'item': 'biomesoplenty:fir_log', 'count': 1}), 'Retained world/inventory/board fixture differs')
    machines = saved['formedMachines']
    require(type(machines) is list and len(machines) == 52, 'Incomplete formed-machine snapshot')
    for index, machine in enumerate(machines):
        require(type(machine) is dict and set(machine) == {'index', 'primary', 'secondary', 'energy', 'bladeDamage', 'processes', 'redstoneEnabled'}, 'Malformed machine snapshot')
        require(type(machine['index']) is int and machine['index'] == index and type(machine['energy']) is int and machine['energy'] > 0
                and type(machine['bladeDamage']) is int and machine['bladeDamage'] > 0 and type(machine['redstoneEnabled']) is bool, 'Invalid machine state/types')
        if index:
            family = specs['wood_families']['families'][index // 4]
            stripped = index % 4 >= 2
            require(equal(machine['primary'], {family['planks']: 6}) and equal(machine['secondary'], {'immersiveengineering:dust_wood': 1 if stripped else 2})
                    and machine['processes'] == [] and machine['redstoneEnabled'] is True and machine['bladeDamage'] == 5
                    and machine['energy'] == (31200 if stripped else 30400), 'Saved formed-machine outputs differ')
    first = machines[0]
    require(type(first['processes']) is list and len(first['processes']) == 1, 'Missing in-flight real machine process')
    queued = first['processes'][0]
    require(type(queued) is dict and set(queued) == {'tick', 'stripped', 'sawed', 'input', 'count'} and type(queued['tick']) is int
            and 40 <= queued['tick'] < 80 and queued['stripped'] is True and queued['sawed'] is False
            and queued['input'] == 'biomesoplenty:fir_log' and type(queued['count']) is int and queued['count'] == 1
            and first['redstoneEnabled'] is False, 'Saved process is not a paused in-flight fir input')
    for label, value in {'continuity begins with empty real queue': True, 'continuity real input accepted': True, 'real redstone pauses machine': False,
                         'paused queue still contains input': 1, 'redstone preserves queued progress': queued['tick'], 'redstone preserves stored energy': first['energy'],
                         'save fixture board retains log': 'biomesoplenty:fir_log', 'save fixture board input count': 1}.items():
        expect(checks, label, value)
    return saved


def resumed(checks, previous, current, phase):
    expect(checks, 'persisted world state', previous)
    for label, value in {'restored queue has exactly one input': 1, 'restored machine remains redstone paused': False,
                         'restored queued input': 'biomesoplenty:fir_log', 'restored machine enabled by removing real redstone': True,
                         'restored board processes retained input': True, 'restored board consumes retained input': True,
                         'restored board actual output': BOARD_OUTPUT, 'restored blade wear': 5}.items():
        expect(checks, label, value)
    old = previous['formedMachines'][0]
    primary = {'biomesoplenty:fir_planks': old['primary']['biomesoplenty:fir_planks'] + 6}
    secondary = {'immersiveengineering:dust_wood': old['secondary']['immersiveengineering:dust_wood'] + 1}
    expect(checks, 'restored primary output', primary)
    expect(checks, 'restored secondary output without duplicate stripping', secondary)
    expect(checks, 'restored remaining energy consumption', (80 - old['processes'][0]['tick']) * 20)
    if phase.endswith('restart'):
        expected = json.loads(json.dumps(previous))
        first = expected['formedMachines'][0]
        first['primary'] = primary
        first['secondary']['immersiveengineering:dust_wood'] += 2
        first['energy'] -= 1600
        first['bladeDamage'] += 5
        require(equal(current, expected), 'Restart did not retain exact queued-machine transition')


def scoped(runtime, specs):
    require(type(runtime['scopedCases']) is list and len(runtime['scopedCases']) == 302, 'Missing 302 actual scoped case receipts')
    envelope = {key: runtime[key] for key in ('schemaVersion', 'executionMode', 'candidateVersion')}
    envelope.update(cases=runtime['scopedCases'], assertions=runtime['scopedAssertions'])
    require(type(runtime['scopedAssertions']) is dict, 'Missing scoped observations')
    for rows in runtime['scopedAssertions'].values():
        require(type(rows) is list and all(type(row) is dict and ('comparison' in row or equal(row.get('actual'), row.get('expected'))) for row in rows), 'Incorrect scoped assertion types/values')
    result = qualification_report.validate(json.dumps(envelope).encode(), specs, runtime['candidateVersion'], expected_mode='packaged-production')
    require(type(runtime['scopedDurationNanos']) is int and runtime['scopedDurationNanos'] > 0
            and type(runtime['repeatedDurationNanos']) is int and runtime['repeatedDurationNanos'] > 0
            and type(runtime['repeatedBoardOperations']) is int and runtime['repeatedBoardOperations'] == 100, 'Missing measured bounded repeated operations')
    repeated = runtime['repeatedAssertions']
    require(type(repeated) is dict and set(repeated) == {f'repeat_board_{index}' for index in range(100)}, 'Incomplete repeated-operation observations')
    for rows in repeated.values():
        # The decoded recipe contains two equal "guaranteed result" observations.
        require(type(rows) is list and all(type(row) is dict and set(row) == {'check', 'actual', 'expected'} and equal(row['actual'], row['expected']) for row in rows), 'Failed repeated actual operation')
        for label, value in {'actual emitted outputs': BOARD_OUTPUT, 'consumes exactly one input': True, 'tool durability': 1, 'no repeat output': {}, 'wrong tool operation rejects': False}.items():
            matches = [row for row in rows if row['check'] == label]
            require(len(matches) == 1 and equal(matches[0]['actual'], value), 'Missing repeated board operation: ' + label)
    return result


def validate(files: dict[str, bytes], specs: dict, candidate: dict) -> dict:
    """Derive bounded capabilities. This function cannot authenticate submitted/local files."""
    require(candidate == {**jar_identity(files['candidate.jar']), 'name': f"immersive_bop_harvest-{candidate['version']}.jar", 'size': len(files['candidate.jar']), 'sha256': sha(files['candidate.jar'])}
            and candidate['version'] == '0.1.1-alpha.10' and type(candidate['size']) is int, 'Wrong candidate raw-byte identity')
    dependencies = read_json(files['runtime-dependencies.json'])
    require(dependencies.get('status') == 'PASS' and type(dependencies.get('dependencies')) is list and len(dependencies['dependencies']) == 5, 'Missing exact five dependency identities')
    locked = {row['modId']: row for row in dependencies['dependencies']}
    require(set(locked) == DEPENDENCIES, 'Duplicate/wrong dependency identities')
    harness_raw = files['production-harness.jar']
    with zipfile.ZipFile(io.BytesIO(harness_raw)) as archive:
        require(archive.namelist().count('META-INF/neoforge.mods.toml') == 1, 'Ambiguous harness metadata')
        metadata = tomllib.loads(archive.read('META-INF/neoforge.mods.toml').decode())
        require([row['modId'] for row in metadata['mods']] == [HARNESS], 'Harness is not a separate packaged mod')
        for name in qualification_report.SPEC_FILES:
            require(equal(read_json(archive.read('bop_qa/spec/' + name + '.json')), specs[name]), 'Harness embeds another source specification')
    receipts, runtimes, all_checks, nonces, qualification = {}, {}, {}, set(), {}
    baseline_raw = files['production-baseline.jar']
    require(jar_identity(baseline_raw)['version'] == '0.1.1-alpha.9', 'Wrong baseline raw JAR version')
    baseline = {'sha256': sha(baseline_raw), 'size': len(baseline_raw)}
    for phase in PHASES:
        receipt = read_json(files['production-' + phase + '.json'])
        log_raw = files['production-' + phase + '.log']
        require(receipt.get('passed') is True and type(receipt.get('exitCode')) is int and receipt['exitCode'] == 0
                and receipt.get('timeout') is False and receipt.get('aborted') is False and positive(receipt.get('durationSeconds')), 'Unsuccessful/aborted phase: ' + phase)
        require(receipt.get('logSha256') == sha(log_raw) and type(receipt.get('logBytes')) is int and receipt['logBytes'] == len(log_raw) > 0
                and path(receipt['log']).endswith('/' + phase + '.log'), 'Changed/misbound phase log: ' + phase)
        command = receipt['command']
        require(type(command) is list and all(type(arg) is str for arg in command) and command[0] == 'java'
                and command.count('-Dbop.qa.phase=' + phase) == 1, 'Wrong actual production launch command')
        runtime = receipt['runtime'] if phase in SERVER_PHASES else read_json(files['production-' + phase + '-common.json'])
        require(type(runtime.get('schemaVersion')) is int and runtime['schemaVersion'] == 1 and runtime.get('executionMode') == 'packaged-production'
                and runtime.get('phase') == phase and runtime.get('testHarnessIsSeparate') is True and runtime.get('error') is None, 'Wrong packaged phase/schema')
        nonce = runtime['nonce']
        require(type(nonce) is str and str(uuid.UUID(nonce)) == nonce and nonce not in nonces, 'Missing/duplicate phase nonce')
        nonces.add(nonce)
        require(runtime.get('phaseStatus') == ('STARTED' if phase == 'client-two' else 'PASS'), 'Incomplete actual runtime phase')
        require(runtime.get('candidateVersion') == ('0.1.1-alpha.9' if phase.startswith('baseline-') else candidate['version']), 'Wrong phase candidate version')
        checks = observed(runtime['checks'])
        for label, value in {'owned disposable instance': nonce, 'explicit launch profile': phase, 'production loader': True, 'exact staged mod jar count': 7}.items():
            expect(checks, label, value)
        rows = runtime['loadedJarIdentities']
        require(type(rows) is list and len(rows) == 7 and {row['modId'] for row in rows} == DEPENDENCIES | {MOD, HARNESS}, 'Incomplete/duplicate loaded JARs')
        for row in rows:
            require(set(row) == {'modId', 'path', 'sha256', 'size'} and type(row['size']) is int and row['size'] > 0
                    and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'Malformed loaded JAR identity')
            mod = row['modId']
            if mod in locked:
                expected = locked[mod]
                require(row['sha256'] == expected['sha256'] and equal(row['size'], expected['size']), 'Loaded dependency differs from source-locked receipt')
                name = expected['filename']
            elif mod == HARNESS:
                require(row['sha256'] == sha(harness_raw) and row['size'] == len(harness_raw), 'Harness changed between comparable phases')
                name = 'bop-harvest-qualification-harness-1.jar'
            else:
                name = 'immersive_bop_harvest-' + runtime['candidateVersion'] + '.jar'
                identity = {'sha256': row['sha256'], 'size': row['size']}
                if phase.startswith('baseline-'):
                    require(identity == baseline, 'Baseline changed across restart')
                else:
                    require(identity == {key: candidate[key] for key in ('sha256', 'size')}, 'Candidate changed between phases')
            require(path(row['path']) == path(receipt['cwd']) + '/mods/' + name, 'Loaded JAR is outside the named production mods directory')
            for label, value in {'regular packaged mod ': True, 'packaged mod path ': row['path'], 'packaged mod hash ': row['sha256'], 'packaged mod size ': row['size']}.items():
                expect(checks, label + mod, value)
        if phase in SERVER_PHASES:
            text = log_raw.decode('utf-8')
            require(all(marker in text for marker in ('Done (', 'Stopping server', 'All dimensions are saved', 'BOP_QA: production server started profile=' + phase)), 'Missing clean production-server lifecycle log')
            require(runtime.get('dedicatedServer') is True and runtime.get('serverStarted') is True and runtime.get('saveCalled') is True
                    and type(runtime.get('serverTicks')) is int and 0 < runtime['serverTicks'] <= 6000, 'Missing actual dedicated-server save')
            index = SERVER_PHASES.index(phase)
            if not index:
                require(receipt.get('predecessor') is None, 'Baseline creation has a predecessor')
            else:
                previous = SERVER_PHASES[index - 1]
                binding = receipt['predecessor']
                require(binding['phase'] == previous and binding['nonce'] == runtimes[previous]['nonce']
                        and binding['sha256'] == sha(files['production-' + previous + '.json']) and path(binding['path']).endswith('/' + previous + '.json')
                        and path(receipt['cwd']) == path(receipts[previous]['cwd']), 'Broken phase predecessor chain')
        if phase in ('baseline-create', 'candidate-upgrade', 'client-one'):
            machine_checks(checks, specs)
            qualification[phase] = scoped(runtime, specs)
            expect(checks, 'datapack reload', True)
        if phase not in ('multiplayer', 'client-two'):
            saved = snapshot(runtime, specs, checks)
            require(runtime.get('saveCalled') is True, 'Missing completed snapshot save')
            if phase in ('baseline-create', 'candidate-upgrade', 'client-one'):
                first = saved['formedMachines'][0]
                require(equal(first['primary'], {'biomesoplenty:fir_planks': 6}) and equal(first['secondary'], {'immersiveengineering:dust_wood': 3})
                        and first['energy'] == 30400 - first['processes'][0]['tick'] * 20 and first['bladeDamage'] == 5, 'New fixture did not preserve initial real queue outputs')
            if phase in ('baseline-restart', 'candidate-upgrade', 'candidate-restart'):
                resumed(checks, runtimes[SERVER_PHASES[SERVER_PHASES.index(phase) - 1]]['savedSnapshot'], saved, phase)
        if phase == 'multiplayer':
            expected = json.loads(json.dumps(runtimes['candidate-restart']['savedSnapshot']))
            machine = expected['formedMachines'][1]
            machine['primary']['biomesoplenty:fir_planks'] += 6
            machine['secondary']['immersiveengineering:dust_wood'] += 2
            machine['energy'] -= 1600
            machine['bladeDamage'] = 5
            require(equal(runtime['savedSnapshot'], expected), 'Multiplayer changed more than the observed client sawmill operation')
        receipts[phase], runtimes[phase], all_checks[phase] = receipt, runtime, checks
    _validate_clients(files, receipts, runtimes, all_checks)
    _validate_preparation(files, receipts)
    return {'authenticatedExecution': False, 'stableReady': False, 'status': 'INTEGRITY_ONLY_PACKAGED_EXECUTION',
            'mode': 'packaged-production', 'phases': list(PHASES), 'packagedRuntime': True, 'client': True, 'multiplayer': True,
            'saveReload': True, 'formedSawmillPorts': 52, 'inFlightMachineResume': True, 'restoredBoardOperations': True,
            'clientSawmillInteraction': True, 'clientHarvestInteraction': True,
            'repeatedBoardOperationsPerFullPhase': 100, 'scopedCompatibility': qualification,
            'phaseMeasurements': {phase: {'durationSeconds': receipts[phase]['durationSeconds'], 'logBytes': receipts[phase]['logBytes'],
                                         **{key: runtimes[phase][key] for key in ('serverTicks', 'scopedDurationNanos', 'repeatedDurationNanos') if key in runtimes[phase]}}
                                  for phase in PHASES},
            'candidateUpgradeToBaselineCreateDurationRatio': receipts['candidate-upgrade']['durationSeconds'] / receipts['baseline-create']['durationSeconds'],
            'harnessSha256': sha(harness_raw), 'baseline': baseline, 'remaining': ['authenticated-service-provenance', 'full-acceptance', 'final-stable-version']}


def _validate_clients(files, receipts, runtimes, all_checks):
    for phase in CLIENT_PHASES:
        client = receipts[phase]['client']
        require(client.get('phaseStatus') == 'PASS' and client.get('phase') == phase and client.get('nonce') == runtimes[phase]['nonce']
                and client.get('error') is None and path(receipts[phase]['cwd']).endswith('/' + phase), 'Wrong/stale client receipt')
        flags = ['titleScreen', 'joinedDedicatedServer', 'multiplayerAuthoritativeBoardResult', 'serverConfirmedReconnect', 'cleanDisconnect']
        if phase == 'client-one':
            flags += ['createdWorld', 'integratedServer', 'singleplayerAuthoritativeBoardResult', 'cleanSingleplayerDisconnect', 'actualSawmillInteraction', 'actualHarvestInteraction']
            require(runtimes[phase].get('dedicatedServer') is False and runtimes[phase].get('serverStarted') is True, 'No actual integrated server')
        require(all(client.get(flag) is True for flag in flags), 'Missing actual client action')
        exit_receipt = read_json(files['production-' + phase + '-exit.json'])
        require(type(exit_receipt.get('state')) is int and exit_receipt['state'] == 99 and exit_receipt.get('stopRequestedByHarness') is True, 'Client did not complete its harness exit hook')
        screenshots = client['screenshots']
        require(type(screenshots) is list and len(screenshots) == len(SCREENSHOTS[phase]) and [row['stage'] for row in screenshots] == list(SCREENSHOTS[phase]), 'Incomplete/duplicate client screenshot stages')
        for row in screenshots:
            require(row['file'] == 'bop-qa-' + row['stage'] + '.png', 'Wrong screenshot filename')
            raw = files['production-' + phase + '-' + row['stage'] + '.png']
            require(type(row['size']) is int and row['size'] == len(raw) and row['sha256'] == sha(raw), 'Changed screenshot bytes')
            png(raw)
    for phase, players in (('client-one', {'BopQaOne'}), ('multiplayer', {'BopQaOne', 'BopQaTwo'})):
        checks = all_checks[phase]
        for label, value in {'client board single input': True, 'concurrent board input consumed': True,
                             'concurrent board original input consumed': True, 'concurrent output before tool retrieval': BOARD_OUTPUT,
                             'concurrent tools conserved including board': len(players), 'concurrent durability before tool retrieval': 1,
                             'authoritative combined client and ground outputs': BOARD_OUTPUT, 'only one actual tool use consumes durability': 1,
                             'all client tools conserved after retrieval': len(players), 'all tools returned to client inventories': len(players)}.items():
            expect(checks, label, value)
        actual_players = checks.get('all real clients sent board interactions')
        require(type(actual_players) is list and len(actual_players) == len(players) and set(actual_players) == players, 'Missing distinct real client board packets')
        interactions = runtimes[phase]['clientInteractions']
        require(interactions.get('verified') is True and type(interactions.get('maxConcurrentPlayers')) is int and interactions['maxConcurrentPlayers'] == len(players)
                and type(interactions.get('finishedClients')) is int and interactions['finishedClients'] == len(players), 'Missing authoritative completed client observations')
        require(equal(interactions.get('extraChecks'), {'sawmill': True, 'harvest': True}), 'Missing authoritative client IE/harvest completion')
        before = runtimes['candidate-restart' if phase == 'multiplayer' else 'client-one']['savedSnapshot']['formedMachines'][1]
        for label, value in {'additional interactions use observed client-one': True, 'client saw fixture starts idle': True,
                             'real client saw interaction packet': True, 'client installed real sawblade': 'immersiveengineering:sawblade',
                             'client blade consumed from inventory': True, 'client installed blade machine accepts real input': True,
                             'client harvest follows observed saw result': True, 'client webbing fixture is supported': True,
                             'client harvest stage': 4, 'real client harvest uses knife tag': True,
                             'client saw primary port delta': {'biomesoplenty:fir_planks': before['primary']['biomesoplenty:fir_planks'] + 6},
                             'client saw secondary port delta': {'immersiveengineering:dust_wood': before['secondary']['immersiveengineering:dust_wood'] + 2},
                             'client saw energy consumed': 1600, 'client saw blade wear': 5, 'actual client broke supported webbing': True,
                             'actual client harvest output': {'minecraft:string': 1}, 'real client IE and harvest completed': {'sawmill': True, 'harvest': True}}.items():
            expect(checks, label, value)
        events = interactions['events']
        require(type(events) is list and bool(events) and all(type(event.get('tick')) is int and event['tick'] >= 0 and event.get('player') in players for event in events), 'Invalid server-owned client event log')
        require([event['tick'] for event in events] == sorted(event['tick'] for event in events), 'Reordered server client events')
        for player in players:
            lifecycle = []
            for action in ('ready', 'clicked', 'observed', 'finished'):
                rows = [event for event in events if event['player'] == player and event['event'] == action]
                require(len(rows) == 1 and type(rows[0].get('uuid')) is str, 'Missing/duplicate actual client lifecycle event')
                lifecycle.append(rows[0])
            require(len({event['uuid'] for event in lifecycle}) == 1 and str(uuid.UUID(lifecycle[0]['uuid'])) == lifecycle[0]['uuid']
                    and all(first['tick'] <= second['tick'] for first, second in zip(lifecycle, lifecycle[1:])), 'Changed identity/reordered client lifecycle')
            uses = [event for event in events if event['player'] == player and event['event'] == 'actual-use-item-packet']
            require(any(event.get('item') == 'minecraft:iron_axe' for event in uses)
                    and all(event.get('item') in {'minecraft:iron_axe', 'minecraft:air'} and lifecycle[0]['tick'] <= event['tick'] <= lifecycle[1]['tick'] for event in uses), 'Missing actual client use-item packets')
            expect(checks, 'client observed server result ' + player, True)
            expect(checks, 'finished client observed output ' + player, True)
        retrieved = [event for event in events if event['event'] == 'actual-board-retrieve-packet']
        cleared = [event for event in events if event['event'] == 'cleared']
        retrieval_labels = ('real client retrieved parked tool', 'parked tool retrieval uses empty hand')
        if retrieved or cleared or any(label in checks for label in retrieval_labels):
            require(len(retrieved) == len(cleared) == 1, 'Missing/duplicate parked-tool retrieval packet or command')
            packet, command = retrieved[0], cleared[0]
            clicked = next(event for event in events if event['player'] == 'BopQaOne' and event['event'] == 'clicked')
            acknowledged = next(event for event in events if event['player'] == 'BopQaOne' and event['event'] == 'observed')
            require(packet['player'] == command['player'] == 'BopQaOne' and packet.get('item') == 'minecraft:air'
                    and command.get('uuid') == clicked['uuid'] and clicked['tick'] < packet['tick'] <= command['tick'] < acknowledged['tick']
                    and events.index(packet) < events.index(command), 'Invalid parked-tool retrieval actor/item/lifecycle')
            for label in retrieval_labels:
                expect(checks, label, True)
        extra_events = {}
        for action in ('extras', 'fixture-blade-removed', 'actual-sawmill-use-item-packet', 'saw-clicked', 'harvest-ready', 'actual-harvest-break-packet', 'harvested'):
            rows = [event for event in events if event['event'] == action]
            require(len(rows) == 1 and rows[0]['player'] == 'BopQaOne', 'Missing actual client IE/harvest event: ' + action)
            extra_events[action] = rows[0]
        require(all(first['tick'] <= second['tick'] for first, second in zip(list(extra_events.values()), list(extra_events.values())[1:])), 'Reordered client IE/harvest events')
        removed = extra_events['fixture-blade-removed']
        require(removed.get('item') == 'immersiveengineering:sawblade' and type(removed.get('damage')) is int and removed['damage'] == before['bladeDamage']
                and extra_events['actual-harvest-break-packet'].get('block') == 'biomesoplenty:webbing', 'Wrong actual removed blade/harvested block')
        if phase == 'multiplayer':
            require(interactions.get('reconnected') is True, 'No authoritative reconnect')
            expect(checks, 'two concurrent real clients', 2)
            expect(checks, 'real client reconnect', True)
            expect(checks, 'client reconnect after observed result', True)
            ready = next(event for event in events if event['player'] == 'BopQaOne' and event['event'] == 'ready')
            rejoined = [event for event in events if event['player'] == 'BopQaOne' and event['event'] == 'rejoined']
            require(len(rejoined) == 1 and ready['uuid'] == rejoined[0]['uuid'], 'Reconnected player identity changed')
            expect(checks, 'reconnected original identity', ready['uuid'])
            inventory = checks.get('reconnected saved inventory')
            require(type(inventory) is list and len(inventory) == 36 and all(type(row) is dict and set(row) == {'slot', 'item', 'count', 'damage'}
                    and type(row['slot']) is int and row['slot'] == index and type(row['item']) is str and re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_./-]+', row['item'])
                    and type(row['count']) is int and row['count'] >= 0 and type(row['damage']) is int and row['damage'] >= 0 for index, row in enumerate(inventory)), 'Missing observed reconnect inventory')
            require(sum(row['count'] for row in inventory if row['item'] == 'farmersdelight:iron_knife') == 1, 'Reconnect lost the actual client harvest tool')
            require(any(event['player'] == 'BopQaOne' and event['event'] == 'logout' and extra_events['harvested']['tick'] < event['tick'] < rejoined[0]['tick'] for event in events), 'Reconnect lacks intervening logout')


def _validate_preparation(files, receipts):
    baseline = read_json(files['production-baseline-build.json'])
    raw, log = files['production-baseline.jar'], files['production-baseline-build.log']
    require(type(baseline.get('schemaVersion')) is int and baseline['schemaVersion'] == 1
            and baseline.get('sourceCommit') == BASELINE_COMMIT and baseline.get('sourceTree') == BASELINE_TREE
            and type(baseline.get('sourceArchiveSha256')) is str and re.fullmatch('[0-9a-f]{64}', baseline['sourceArchiveSha256']), 'Wrong fixed baseline source/build identity')
    require(type(baseline.get('exitCode')) is int and baseline['exitCode'] == 0 and baseline.get('logSha256') == sha(log)
            and type(baseline.get('logBytes')) is int and baseline['logBytes'] == len(log) > 0 and b'BUILD SUCCESSFUL' in log
            and type(baseline.get('command')) is list and all(arg in baseline['command'] for arg in ('clean', 'build', '--stacktrace')), 'Missing clean baseline build evidence')
    require(equal(baseline['candidate'], {**jar_identity(raw), 'name': 'immersive_bop_harvest-0.1.1-alpha.9.jar', 'size': len(raw), 'sha256': sha(raw)}), 'Baseline build/JAR bytes differ')
    preparation = read_json(files['production-preparation.json'])
    require(preparation.get('installerSha256') == INSTALLER_SHA256 and preparation.get('metadataSha256') == METADATA_SHA256
            and type(preparation.get('commands')) is list and len(preparation['commands']) == 2, 'Wrong pinned production preparation')
    for kind, row in zip(('server', 'client'), preparation['commands']):
        require(type(row.get('exitCode')) is int and row['exitCode'] == 0 and positive(row.get('durationSeconds'))
                and '--install' + kind.title() in row['command'] and row['logSha256'] == sha(files['production-installer-' + kind + '.log'])
                and bool(files['production-installer-' + kind + '.log']), 'Incomplete official installer execution')
    ledger = read_json(files['production-orchestration.json'])
    require(type(ledger) is list and len(ledger) == 7, 'Incomplete orchestration phase inventory')
    for phase, row in zip(PHASES, ledger):
        command = row['command']
        require(type(row.get('exitCode')) is int and row['exitCode'] == 0 and type(command) is list and command.count('--phase') == 1
                and command[command.index('--phase') + 1] == phase, 'Missing successful orchestrated phase')
    raw = files['production-alpha9-world-backup.json']
    backup = read_json(raw)
    require(receipts['candidate-upgrade']['predecessor']['backupManifest']['sha256'] == sha(raw), 'Upgrade backup binding changed')
    require(backup.get('hashMatch') is True and path(backup['source']) == path(receipts['baseline-restart']['cwd']) + '/world'
            and type(backup.get('fileCount')) is int and backup['fileCount'] == len(backup['sha256']) > 0 and 'level.dat' in backup['sha256'], 'Missing verified pre-upgrade world inventory')
    require(all(type(name) is str and not name.startswith('/') and '\\' not in name and ':' not in name and all(part not in {'', '.', '..'} for part in name.split('/'))
                and type(value) is str and re.fullmatch('[0-9a-f]{64}', value) for name, value in backup['sha256'].items()), 'Malformed backup file inventory')
