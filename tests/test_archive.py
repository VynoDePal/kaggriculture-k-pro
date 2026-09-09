"""Integrity and import checks only; no environment or network execution."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ArchiveTests(unittest.TestCase):
    def test_original_source_hashes(self):
        hashes=json.loads((ROOT/'SOURCE_HASHES.json').read_text())
        for name,expected in hashes.items():
            with self.subTest(file=name):
                raw=(ROOT/name).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),expected)
                compile(raw,name,'exec')

    def test_autonomous_files_load_and_expose_a_callable(self):
        for name in ('k_pro1.py','k_pro2.py','k_pro3.py','k_pro4_loader_fixed.py','k_pro6.py'):
            with self.subTest(file=name):
                scope={'__name__':'archive_validation'}
                exec(compile((ROOT/'k_pro'/name).read_text(),name,'exec'),scope)
                entry=scope.get('kaggle_agent',scope.get('agent'))
                self.assertTrue(callable(entry))

if __name__=='__main__':unittest.main()
