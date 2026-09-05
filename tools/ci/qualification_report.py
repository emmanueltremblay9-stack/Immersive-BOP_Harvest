"""Validate actual harness assertions against the checked-in scope inventory."""
from pathlib import Path
import json

SPEC_FILES = ('wood_families', 'flower_cutting_recipes', 'plant_cutting_recipes', 'direct_harvest_rules', 'coverage_inventory', 'tag_integrations')


def load_specs(root: Path) -> dict:
    return {name: json.loads((root / 'spec' / (name + '.json')).read_text(encoding='utf-8')) for name in SPEC_FILES}


def catalog(sources: dict | Path) -> set[str]:
    if isinstance(sources, Path):
        sources = load_specs(sources)
    def spec(name):
        return sources[name]
    def path(name):
        return name.split(':', 1)[1]
    result = set()
    for family in spec('wood_families')['families']:
        result.update('cutting_' + path(family[key]) for key in ('log', 'wood'))
        result.update('sawmill_' + path(family[key]) for key in ('log', 'wood', 'stripped_log', 'stripped_wood'))
    for name in ('flower_cutting_recipes', 'plant_cutting_recipes'):
        result.update('cutting_' + path(row['source']) for row in spec(name)['recipes'])
    harvest = {block for row in spec('direct_harvest_rules')['rules'] for block in row['blocks']}
    result.update('harvest_' + path(block) for block in harvest)
    excluded = {row['id'] for value in spec('coverage_inventory').values() if isinstance(value, list) for row in value} - harvest
    result.update('native_' + path(block) for block in excluded)
    result.update('cascade_' + name for name in ('high_grass', 'glowworm_silk', 'hanging_cobweb', 'flesh_tendons'))
    result.add('runtime_tags')
    return result


def validate(raw: bytes, sources: dict | Path, version: str) -> dict:
    from tools.ci.candidate_evidence import read_json, require
    if isinstance(sources, Path):
        sources = load_specs(sources)
    report = read_json(raw)
    require(type(report.get('schemaVersion')) is int and report['schemaVersion'] == 1 and report.get('executionMode') == 'development-classpath', 'Wrong harness report schema/mode')
    require(report.get('candidateVersion') == version, 'Harness report belongs to another candidate version')
    expected = catalog(sources)
    rows = report['cases']
    names = [row['id'] for row in rows]
    require(len(names) == len(set(names)), 'Duplicate reported test execution')
    require({name.removeprefix('bop_qa.') for name in names if name.startswith('bop_qa.')} == expected, 'Incomplete scoped runtime cases')
    require(all(row.get('passed') is True and row.get('required') is True and row.get('error') is None for row in rows), 'Failed/optional runtime cases')
    assertions = report['assertions']
    require(set(assertions) == expected, 'Missing per-case observed assertions')
    total = 0
    for name, checks in assertions.items():
        require(isinstance(checks, list) and bool(checks), 'Empty runtime assertions')
        for row in checks:
            if row.get('comparison') == 'atMost':
                require(set(row) == {'check', 'actual', 'expected', 'comparison'} and type(row['actual']) is int
                        and type(row['expected']) is int and 0 <= row['actual'] <= row['expected'], 'Failed bounded output assertion')
            else:
                require(set(row) == {'check', 'actual', 'expected'} and row['actual'] == row['expected'], 'Failed/malformed actual assertion')
        labels = {row['check'] for row in checks}
        if name.startswith('cutting_'):
            require({'actual emitted outputs', 'consumes exactly one input', 'tool durability', 'no repeat output', 'wrong tool operation rejects'} <= labels, 'Missing actual board operation assertions')
        elif name.startswith('sawmill_'):
            require({'base energy', 'real process output reload=false', 'real process output reload=true', 'real process secondaries reload=true', 'no energy cannot advance'} <= labels, 'Missing sawmill process assertions')
        elif name.startswith('harvest_'):
            require({'foreign table cannot trigger addon', 'explosion native only'} <= labels and all(sum(label.startswith(tool + ' roll=') for label in labels) == 2 for tool in ('hand', 'wrong', 'knife', 'sword', 'shears', 'silk', 'fortune')), 'Missing distinct harvest tool/context assertions')
            if name == 'harvest_barley':
                require('upper barley native only' in labels, 'Missing upper barley exclusion')
            if name == 'harvest_webbing':
                require('six faces at most one string' in labels, 'Missing webbing face bound')
        elif name.startswith('cascade_'):
            require({'three actual segments placed', 'real player destroys attached segment', 'bonus bounded by three destroyed segments', 'all three segments removed by scheduled cascade'} <= labels, 'Missing actual scheduled segment destruction assertions')
        elif name.startswith('native_'):
            required={f'native invariant {tool} roll={roll}' for tool in ('hand','knife','sword','shears','silk','fortune') for roll in ('0.13','0.91')}
            require(required <= labels, 'Missing distinct native tool/roll invariance assertions')
            if name.startswith('native_potted_'):
                require('pot and correct content remain' in labels, 'Missing actual potted contents')
        elif name == 'runtime_tags':
            required = {'native shears tag'} | {f"tag {row['tag']} accepts {value}" for row in sources['tag_integrations']['integrations'] for value in row['values']}
            require(required <= labels and all(row['actual'] is True and row['expected'] is True for row in checks), 'Missing actual required tag memberships')
        total += len(checks)
    return {'cases': len(expected), 'assertions': total, 'mode': 'development-classpath',
            'cuttingBoardOperations': True, 'sawmillProcessLogic': True, 'harvestLoot': True,
            'placedSegmentDestruction': True, 'nativeLootInvariance': True,
            'formedSawmillPorts': False, 'packagedRuntime': False}
