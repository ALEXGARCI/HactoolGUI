import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from extract import validate_key_file, nca_info

class KeyValidationTests(unittest.TestCase):
    def test_prod_accepts_named_hex(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'prod.keys';p.write_text('master_key_00 = '+'a'*32+'\n')
            self.assertEqual(validate_key_file(p,'prod'),1)
    def test_title_accepts_rights(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'title.keys';p.write_text('a'*32+' = '+'b'*32+'\n')
            self.assertEqual(validate_key_file(p,'title'),1)
    def test_reject_wrong_filename(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'title.keys';p.write_text('master_key_00 = '+'a'*32+'\n')
            with self.assertRaises(ValueError): validate_key_file(p,'prod')
    def test_reject_malformed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'prod.keys';p.write_text('not keys')
            with self.assertRaises(ValueError): validate_key_file(p,'prod')
if __name__=='__main__':unittest.main()
