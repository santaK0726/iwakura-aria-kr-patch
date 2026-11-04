"""Reconstruct and verify the source-required Iwakura Aria Korean patch."""
import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import PIL
from PIL import features
import delta_engine as engine

ROOT = Path(__file__).resolve().parent
TITLE = '01009BD0209D8000'
MOD = 'Iwakura-Aria-Korean-v0.5.1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text('utf-8'))


def layouts(target):
    switch = Path('atmosphere/contents') / TITLE / 'romfs'
    emulator = Path(MOD) / 'romfs'
    if target == 'switch':
        return [switch]
    if target == 'emulator':
        return [emulator]
    return [Path('Switch') / switch, Path('Emulator') / emulator]


def run(args):
    bundle = args.bundle.resolve()
    source = args.source_romfs.resolve()
    release = read_json(ROOT / 'verification/release.json')
    plan_bytes = (bundle / 'manifest.json').read_bytes()
    require(engine.sha(plan_bytes) == release['public_manifest_sha256'], 'Patch manifest hash mismatch')
    plan = json.loads(plan_bytes)
    require(plan['schema'] == 2 and plan['game_id'] == TITLE, 'Unsupported patch schema or title')
    require(plan['policy'] == 'source-required-public-prerelease', 'Unsupported distribution policy')
    profile = read_json(ROOT / 'source-profile.json')
    require(plan['archives'] == profile['archives'], 'Source profile mismatch')
    expected = {r['name']: r for r in read_json(ROOT / 'verification/expected-output.json')['archives']}
    names = {r['name'] for r in plan['archives']}
    require(len(names) == 7 and names == set(expected), 'Archive set mismatch')
    require(engine.sha((bundle / 'payloads.zip').read_bytes()) == plan['payload_archive_sha256'],
            'Patch payload hash mismatch')
    require(PIL.__version__ == plan['runtime']['pillow'],
            'Pillow version mismatch; install requirements.txt')
    require(features.version('webp') == plan['runtime']['libwebp'],
            'libwebp version mismatch; use the official Pillow 13.0.0 wheel (libwebp 1.6.0)')
    originals = {}
    for row in plan['archives']:
        name = row['name']
        require(Path(name).name == name and name.endswith('.mpk'), 'Invalid archive name')
        raw = (source / name).read_bytes()
        require(len(raw) == row['source_size'] and engine.sha(raw) == row['source_sha256'],
                name + ': unsupported source. Use unmodified Japanese v1.0.3 RomFS')
        engine.index(raw)
        originals[name] = raw
    print('Source revision and patch integrity: PASS (7 archives)', flush=True)
    if args.verify_only:
        return
    require(args.output is not None, '--output is required when building')
    target = args.target
    if target is None:
        package = ROOT / 'package.json'
        require(package.exists(), 'Choose --target switch, emulator or both')
        target = read_json(package)['target']
    require(target in {'switch', 'emulator', 'both'}, 'Invalid target')
    output = args.output.resolve()
    require(not output.exists(), 'Output already exists; choose a new folder')
    for protected in [source, bundle, ROOT]:
        require(output != protected and output not in protected.parents and protected not in output.parents,
                'Output must not overlap the source or patch package')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.' + output.name + '-', dir=output.parent)).resolve()
    require(temporary.parent == output.parent and temporary != output, 'Invalid temporary path')
    try:
        report = dict(version='0.5.1', game_id=TITLE, revision=plan['revision'], target=target,
                      source_qa='SOURCE_HASHES_PASS', static_binary_qa='PASS', rc_readback_qa='PASS',
                      runtime_smoke='NOT RUN', distribution='source-required-public-prerelease',
                      limitations=plan['limits'], archives=[])
        destination_paths = layouts(target)
        for rel in destination_paths:
            (temporary / rel).mkdir(parents=True)
        for row in plan['archives']:
            name = row['name']
            original = originals.pop(name)
            indexed = {r['name']: r for r in engine.index(original)}
            replacements = {}
            for recipe in plan['members']:
                if recipe['archive'] != name:
                    continue
                member = recipe['member']
                require(member in indexed and member not in replacements, 'Missing or duplicate member: ' + member)
                item = indexed[member]
                raw = original[item['offset']:item['offset'] + item['size']]
                replacements[member] = engine.reconstruct(raw, recipe, bundle)
            built, writes = engine.pack(original, replacements)
            wanted = expected[name]
            require(len(built) == wanted['output_size'] and engine.sha(built) == wanted['output_sha256'],
                    name + ': output differs from frozen v0.5.1')
            for rel in destination_paths:
                path = temporary / rel / name
                path.write_bytes(built)
                require(engine.sha(path.read_bytes()) == wanted['output_sha256'], name + ': readback failed')
            report['archives'].append(dict(name=name, size=len(built), sha256=engine.sha(built),
                                           changed_members=len(writes), protected_prefix_verified=True,
                                           all_members_read_back=True))
            print(name + ': reconstructed and read back (' + str(len(writes)) + ' changed members)', flush=True)
        (temporary / 'BUILD-RESULT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        shutil.copyfile(ROOT / 'README.md', temporary / 'README.md')
        shutil.copytree(ROOT / 'LICENSES', temporary / 'LICENSES')
        require(not output.exists(), 'Output appeared while building; refusing to overwrite')
        os.rename(temporary, output)
        print('PASS: ' + str(output), flush=True)
        print('Copy the generated platform folder as described in README.md. Saves and installed mods were not changed.')
    finally:
        for archive in engine._PAYLOAD_ARCHIVES.values():
            archive.close()
        engine._PAYLOAD_ARCHIVES.clear()
        if temporary.exists():
            require(temporary.parent == output.parent and temporary.name.startswith('.' + output.name + '-'),
                    'Refusing unexpected cleanup path')
            shutil.rmtree(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-romfs', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--target', choices=['switch', 'emulator', 'both'])
    parser.add_argument('--bundle', type=Path, default=ROOT / 'patch-data')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    try:
        run(args)
    except Exception as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
