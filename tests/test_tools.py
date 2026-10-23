import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify = load('verify_archive').verify_archive
join = load('join_release').join_release


class ArchiveChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def archive(self, entries):
        path = self.root / 'test.zip'
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, content in entries:
                z.writestr(name, content)
        receipt = {
            'size': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'members': {name: {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                        for name, data in entries},
        }
        return path, receipt

    def test_valid_archive(self):
        path, receipt = self.archive([('system.img', b'example image'), ('manifest.json', b'{}')])
        self.assertEqual(verify(path, receipt)['members_verified'], 2)

    def test_modified_archive_rejected(self):
        path, receipt = self.archive([('system.img', b'example')])
        path.write_bytes(path.read_bytes() + b'x')
        with self.assertRaisesRegex(ValueError, 'size mismatch'):
            verify(path, receipt)

    def test_wrong_member_hash_rejected(self):
        path, receipt = self.archive([('system.img', b'example')])
        receipt['members']['system.img']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Member SHA-256'):
            verify(path, receipt)

    def test_unexpected_member_rejected(self):
        path, receipt = self.archive([('system.img', b'example'), ('extra', b'x')])
        del receipt['members']['extra']
        with self.assertRaisesRegex(ValueError, 'Member set'):
            verify(path, receipt)

    def test_missing_member_rejected(self):
        path, receipt = self.archive([('system.img', b'example')])
        receipt['members']['missing'] = {'size': 0, 'sha256': hashlib.sha256(b'').hexdigest()}
        with self.assertRaisesRegex(ValueError, 'Member set'):
            verify(path, receipt)

    def test_path_traversal_rejected(self):
        path, receipt = self.archive([('../outside', b'example')])
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            verify(path, receipt)

    def test_duplicate_members_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            path, receipt = self.archive([('same', b'a'), ('same', b'b')])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            verify(path, receipt)

    def split_manifest(self):
        parts = [b'example ', b'archive bytes']
        records = []
        for i, content in enumerate(parts):
            name = f'example.zip.part{i + 1:03}'
            (self.root / name).write_bytes(content)
            records.append({'name': name, 'size': len(content), 'sha256': hashlib.sha256(content).hexdigest()})
        content = b''.join(parts)
        data = {'archive': {'name': 'example.zip', 'size': len(content), 'sha256': hashlib.sha256(content).hexdigest()}, 'parts': records}
        path = self.root / 'parts.json'
        path.write_text(json.dumps(data))
        return path, data, content

    def test_join_restores_bytes(self):
        path, _, content = self.split_manifest()
        self.assertEqual(join(path).read_bytes(), content)

    def test_join_corrupt_part_rejected_and_partial_cleaned(self):
        path, data, _ = self.split_manifest()
        (self.root / data['parts'][0]['name']).write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'Part verification'):
            join(path)
        self.assertFalse((self.root / 'example.zip.partial').exists())
        self.assertFalse((self.root / 'example.zip').exists())

    def test_join_preserves_existing_output(self):
        path, _, _ = self.split_manifest()
        dest = self.root / 'example.zip'
        dest.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            join(path)
        self.assertEqual(dest.read_bytes(), b'keep')

    def test_join_preserves_existing_partial(self):
        path, _, _ = self.split_manifest()
        dest = self.root / 'example.zip.partial'
        dest.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            join(path)
        self.assertEqual(dest.read_bytes(), b'keep')


if __name__ == '__main__':
    unittest.main()
