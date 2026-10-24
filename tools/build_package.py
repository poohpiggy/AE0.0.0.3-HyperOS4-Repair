#!/usr/bin/env python3
"""Merge the current AE 0.0.0.3 repairs into the recorded earlier package."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'HyperOS4-AE0.0.0.3.zip'
BROWSER_HASH = '1f5e546a133a4b6530dd183e711648a6de0d0e4c78049b646c2e52bf4035d75a'


def file_hash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base-zip', type=Path, required=True, help='Recorded dd01bd45... archive, not a stock ROM')
    ap.add_argument('--work-dir', type=Path, required=True, help='New or empty path without whitespace')
    ap.add_argument('--output-dir', type=Path, required=True)
    args = ap.parse_args()
    work, output, base = args.work_dir.resolve(), args.output_dir.resolve(), args.base_zip.resolve()
    if any(c.isspace() for c in str(work)):
        ap.error('Work directory must not contain whitespace (debugfs command format).')
    if work.exists() and any(work.iterdir()):
        ap.error('Work directory must be empty.')
    if (output / NAME).exists() or (output / (NAME + '.partial')).exists():
        ap.error('Output already exists.')
    for name in ['debugfs', 'e2fsck']:
        if not shutil.which(name):
            ap.error('Missing external tool: ' + name)
    previous = json.loads((ROOT / 'manifests/history/archive-dd01bd45.json').read_text())
    if base.stat().st_size != previous['size'] or file_hash(base) != previous['sha256']:
        ap.error('Base ZIP does not match the recorded earlier package.')
    spec = importlib.util.spec_from_file_location('image_helpers', ROOT / 'tools/history/build_initial_package.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    work.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    helper.W, helper.I, helper.P = work, work / 'images', work / 'payload'
    helper.I.mkdir()
    shutil.copytree(ROOT / 'payload', helper.P)
    assets = work / 'assets'
    shutil.copytree(ROOT / 'assets', assets)
    helper.REPORT = {'scope': 'AE 0.0.0.3 guest only', 'changes': [], 'images': {}}
    with zipfile.ZipFile(base) as archive:
        for name in ['boot.img', 'system.img', 'vendor.img']:
            target = helper.I / name
            with archive.open(name) as src, target.open('wb') as dst:
                shutil.copyfileobj(src, dst, 4 * 1024 * 1024)
            if file_hash(target) != previous['members'][name]['sha256']:
                raise ValueError('Base image hash mismatch: ' + name)
    # The full init service definitions are retained; both entry points use the wrapper.
    for source in sorted(helper.P.rglob('*')):
        if source.is_file():
            path = '/' + source.relative_to(helper.P).as_posix()
            helper.install(path, source, 0o755 if source.suffix == '.sh' else 0o644)
    helper.install('/product/overlay/AEGuestRecents/AEGuestRecents.apk', assets / 'AEGuestRecents.apk')
    helper.install('/system/media/theme/default/icons', assets / 'icons.static.zip')
    dynamic = '/system/media/theme/default/dynamicicons'
    if helper.exists(dynamic):
        backup = work / 'dynamicicons.original'
        helper.dbg(f'dump {dynamic} {backup}')
        helper.install('/system/etc/aemu-compat/backups/dynamicicons.disabled-r4', backup)
        helper.dbg('rm ' + dynamic, True)
        helper.REPORT['changes'].append({'path': dynamic, 'removed_from_scan': True})
    browser = work / 'browser.apk'
    helper.dbg(f'dump /product/app/MIUIBrowserOfficial/MIUIBrowser.apk {browser}')
    if file_hash(browser) != BROWSER_HASH:
        raise ValueError('Unexpected browser APK in base package.')
    with zipfile.ZipFile(browser) as archive:
        names = [n for n in archive.namelist() if n.startswith('lib/arm64-v8a/') and n.endswith('.so')]
        if len(names) != 66 or len({Path(n).name for n in names}) != 66:
            raise ValueError('Expected 66 unique browser ARM64 libraries.')
        native = work / 'browser-libraries'
        native.mkdir()
        for name in names:
            source = native / Path(name).name
            source.write_bytes(archive.read(name))
            helper.install('/product/app/MIUIBrowserOfficial/lib/arm64/' + source.name, source)
    for name in ['system.img', 'vendor.img']:
        with (work / (name + '.fsck.log')).open('w') as log:
            subprocess.run(['e2fsck', '-fn', str(helper.I / name)], stdout=log, stderr=subprocess.STDOUT, check=True)
    for name in ['boot.img', 'system.img', 'vendor.img']:
        path = helper.I / name
        helper.REPORT['images'][name] = {'size': path.stat().st_size, 'sha256': file_hash(path)}
    helper.REPORT.update(
        filesystem_checks='system/vendor: e2fsck -fn exit 0',
        display={'adaptive_on_instance_restart': True, 'tested_profiles': [[720, 1280, 320], [1080, 2160, 403]]},
        privacy='No userdata partition, accounts or private app databases included.',
        validation='Newly rebuilt output is not covered by acceptance of the distributed archive; import-test this output separately.',
    )
    manifest = work / 'AE-INTEGRATED.json'
    manifest.write_text(json.dumps(helper.REPORT, ensure_ascii=False, indent=2) + '\n')
    guide = work / '使用说明.md'
    guide.write_text((ROOT / 'docs/import-guide.md').read_text() + '\n此文件是重新构建的输出；发布包的验收不自动覆盖这个新文件。\n')
    entries = [(n, helper.I / n) for n in ['boot.img', 'system.img', 'vendor.img']] + [('AE-INTEGRATED.json', manifest), ('使用说明.md', guide)]
    expected = {name: {'size': path.stat().st_size, 'sha256': file_hash(path)} for name, path in entries}
    partial, dest = output / (NAME + '.partial'), output / NAME
    with zipfile.ZipFile(partial, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as archive:
        for name, path in entries:
            with path.open('rb') as src, archive.open(name, 'w', force_zip64=True) as dst:
                shutil.copyfileobj(src, dst, 4 * 1024 * 1024)
    with zipfile.ZipFile(partial) as archive:
        if archive.namelist() != [n for n, _ in entries]:
            raise ValueError('Unexpected ZIP members.')
        for info in archive.infolist():
            with archive.open(info) as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if info.file_size != expected[info.filename]['size'] or digest != expected[info.filename]['sha256']:
                raise ValueError('ZIP member verification failed: ' + info.filename)
    receipt = {'archive': NAME, 'size': partial.stat().st_size, 'sha256': file_hash(partial), 'members': expected,
               'filesystem_checks': helper.REPORT['filesystem_checks'], 'fresh_import_boot_tested': False}
    partial.rename(dest)
    (output / (NAME + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    (output / (NAME + '.sha256')).write_text(receipt['sha256'] + '  ' + NAME + '\n')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
