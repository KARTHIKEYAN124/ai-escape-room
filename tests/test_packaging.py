from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from scripts.build_submission import SUBMISSION_FILES, submission_payloads

class PackagingTests(unittest.TestCase):
    def populate(self, root):
        for name in SUBMISSION_FILES:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'example content')

    def test_excludes_unlisted_private_temporary_and_dataset_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.populate(root)
            for name in ('.env', 'docs/live-comparison.json', 'docs/debug.txt',
                         'docs/dataset.csv', 'docs/backup.zip', 'submission-manifest.json'):
                (root / name).write_text('private content', encoding='utf-8')
            report = root / 'docs/report.md'
            original = '# Report\nSubmitted By: Private Name\nSupervised By: Private Mentor\n\nDesign details.'
            report.write_text(original, encoding='utf-8')
            with patch('scripts.build_submission.ROOT', root):
                files = submission_payloads()
            self.assertEqual(set(files), set(SUBMISSION_FILES))
            self.assertNotIn(b'Private Name', files['docs/report.md'])
            self.assertNotIn(b'Private Mentor', files['docs/report.md'])
            self.assertIn(b'Design details', files['docs/report.md'])
            self.assertEqual(report.read_text(encoding='utf-8'), original)

    def test_blocks_accidental_credential_in_an_allowed_file(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.populate(root)
            (root / 'README.md').write_text('AIza' + 'a' * 35, encoding='utf-8')
            with patch('scripts.build_submission.ROOT', root):
                with self.assertRaisesRegex(RuntimeError, 'Possible credentials'):
                    submission_payloads()

    def test_rejects_oversized_allowed_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.populate(root)
            (root / 'docs/architecture-v1.jpg').write_bytes(b'x' * (5 * 1024 * 1024 + 1))
            with patch('scripts.build_submission.ROOT', root):
                with self.assertRaisesRegex(RuntimeError, 'exceeds 5 MB'):
                    submission_payloads()
