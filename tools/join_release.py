#!/usr/bin/env python3
"""Join raw release parts and verify every part and the restored archive."""
import argparse
import hashlib
import json
from pathlib import Path


def join_release(manifest_path, output_dir=None):
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    folder = manifest_path.parent
    output_dir = Path(output_dir) if output_dir else folder
    record = manifest['archive']
    names = [record['name']] + [p['name'] for p in manifest['parts']]
    if any(Path(n).name != n or '/' in n or '\\' in n or ':' in n for n in names):
        raise ValueError('Manifest must contain plain file names')
    if len({p['name'] for p in manifest['parts']}) != len(manifest['parts']):
        raise ValueError('Duplicate parts')
    if not manifest['parts'] or sum(p['size'] for p in manifest['parts']) != record['size']:
        raise ValueError('Invalid part sizes')
    dest = output_dir / record['name']
    partial = output_dir / (record['name'] + '.partial')
    if dest.exists():
        raise FileExistsError('Output already exists: ' + str(dest))
    output_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0
    try:
        with partial.open('xb') as out:
            for part in manifest['parts']:
                count = 0
                checksum = hashlib.sha256()
                with (folder / part['name']).open('rb') as src:
                    while data := src.read(8 * 1024 * 1024):
                        out.write(data); checksum.update(data); digest.update(data)
                        count += len(data); total += len(data)
                if count != part['size'] or checksum.hexdigest() != part['sha256']:
                    raise ValueError('Part verification failed: ' + part['name'])
            if total != record['size'] or digest.hexdigest() != record['sha256']:
                raise ValueError('Restored ZIP verification failed')
        if dest.exists():
            raise FileExistsError('Output appeared while joining')
        partial.rename(dest)
    except Exception:
        # Never delete a pre-existing partial that we did not create.
        if 'out' in locals():
            partial.unlink(missing_ok=True)
        raise
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('manifest', nargs='?', type=Path, default=Path(__file__).resolve().parent / 'parts.json')
    ap.add_argument('--output-dir', type=Path)
    args = ap.parse_args()
    try:
        dest = join_release(args.manifest, args.output_dir)
    except (OSError, ValueError, KeyError) as exc:
        ap.exit(1, str(exc) + '\n')
    print('Verified ZIP: ' + str(dest))


if __name__ == '__main__':
    main()
