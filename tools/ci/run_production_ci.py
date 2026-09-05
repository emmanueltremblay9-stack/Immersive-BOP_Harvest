"""Run the explicit packaged phase chain inside the CI runner's software display."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.ci.prepare_production_runtime import prepare


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or not os.environ.get('DISPLAY'):
        raise ValueError('Production CI requires the actual CI software display')
    root = ROOT/'build/production-runtime'
    prepare(root)
    props = {}
    for line in (ROOT/'build/moddev/minecraft_assets.properties').read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            props[key] = value.replace('\\:', ':').replace('\\\\', '\\')
    if props.get('asset_index') != '17':
        raise ValueError('Unexpected asset index')
    command = [sys.executable, str(ROOT/'tools/ci/qualify_packaged_runtime.py'),
               '--root', str(root), '--assets', props['assets_root'],
               '--dependencies', str(ROOT/'build/runtime-deps'),
               '--baseline', str(ROOT/'build/qualification-baseline/immersive_bop_harvest-0.1.1-alpha.9.jar'),
               '--candidate', str(ROOT/'build/libs/immersive_bop_harvest-0.1.1-alpha.10.jar'),
               '--harness', str(ROOT/'build/qualification-harness/bop-harvest-qualification-harness-1.jar')]
    subprocess.run(command, cwd=ROOT, check=True, timeout=2400)


if __name__ == '__main__':
    main()
