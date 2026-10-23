#!/usr/bin/env python3
"""Verify an AE ZIP against its recorded receipt; never extracts onto disk."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def digest_file(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_archive(path, receipt):
    path = Path(path)
    if path.stat().st_size != receipt['size']:
        raise ValueError('Archive size mismatch')
    if digest_file(path) != receipt['sha256']:
        raise ValueError('Archive SHA-256 mismatch')
    expected = receipt['members']
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names):
            raise ValueError('Duplicate member paths')
        for name in names:
            posix = PurePosixPath(name)
            if posix.is_absolute() or '..' in posix.parts or '\\' in name or ':' in name:
                raise ValueError('Unsafe member path: ' + name)
        if set(names) != set(expected):
            raise ValueError('Member set mismatch')
        for info in archive.infolist():
            record = expected[info.filename]
            if info.file_size != record['size']:
                raise ValueError('Member size mismatch: ' + info.filename)
            with archive.open(info) as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if digest != record['sha256']:
                raise ValueError('Member SHA-256 mismatch: ' + info.filename)
    return {'archive': path.name, 'members_verified': len(expected), 'sha256': receipt['sha256']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive', type=Path)
    ap.add_argument('--receipt', type=Path, required=True)
    args = ap.parse_args()
    try:
        result = verify_archive(args.archive, json.loads(args.receipt.read_text(encoding='utf-8')))
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as exc:
        ap.exit(1, str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
