"""Package the reviewed source-required delta for Switch and emulator layouts."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    'README.md', 'NOTICE.md', 'requirements.txt', 'Build-Patch.ps1', 'Build-Patch.cmd',
    'apply_patch.py', 'delta_engine.py', 'png_container.py', 'source-profile.json',
    'docs/RELEASE-NOTES.md', 'LICENSES/Pretendard-OFL.txt',
    'verification/expected-output.json', 'verification/release.json',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True, help='Reviewed manifest.json and payloads.zip folder')
    parser.add_argument('--output', type=Path, required=True, help='New package output folder')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Output already exists')
    release = json.loads((ROOT / 'verification/release.json').read_text('utf-8'))
    if release['source_to_output_roundtrip'] != 'PASS':
        raise ValueError('Source-to-output verification must pass before packaging')
    manifest = (args.bundle / 'manifest.json').read_bytes()
    payload = (args.bundle / 'payloads.zip').read_bytes()
    if sha(manifest) != release['public_manifest_sha256'] or sha(payload) != release['payload_archive_sha256']:
        raise ValueError('Reviewed delta data changed')
    common = {name: (ROOT / name).read_bytes() for name in FILES}
    common['patch-data/manifest.json'] = manifest
    common['patch-data/payloads.zip'] = payload
    args.output.mkdir(parents=True)
    rows = []
    for target, label in [('switch', 'Switch'), ('emulator', 'Emulator')]:
        name = 'Iwakura-Aria-Korean-v0.5.1-' + label + '-Patch'
        files = dict(common)
        files['package.json'] = encode(dict(schema=1, version='0.5.1', target=target,
                                          format='source-required-public-prerelease', game_id='01009BD0209D8000'))
        files['SHA256SUMS.txt'] = ''.join(sha(data) + '  ' + rel + '\n' for rel, data in sorted(files.items())).encode('utf-8')
        archive = args.output / (name + '.zip')
        with zipfile.ZipFile(archive, 'x') as z:
            for rel, data in sorted(files.items()):
                info = zipfile.ZipInfo(name + '/' + rel, date_time=(2026, 11, 5, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED if rel.endswith('.zip') else zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, data, compresslevel=6)
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None or set(z.namelist()) != {name + '/' + rel for rel in files}:
                raise ValueError('ZIP membership/CRC failure')
            for rel, data in files.items():
                if z.read(name + '/' + rel) != data:
                    raise ValueError('ZIP readback failure: ' + rel)
        rows.append(dict(file=archive.name, bytes=archive.stat().st_size, sha256=sha(archive.read_bytes()),
                         target=target, file_count=len(files), zip_readback='PASS'))
    (args.output / 'SHA256SUMS.txt').write_text(''.join(r['sha256'] + '  ' + r['file'] + '\n' for r in rows), encoding='utf-8')
    (args.output / 'release-assets.json').write_bytes(encode(dict(version='0.5.1', assets=rows)))
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
