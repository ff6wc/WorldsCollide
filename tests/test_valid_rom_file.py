import hashlib
import os
import tempfile
import unittest

from valid_rom_file import get_sha256_hex, valid_rom_file

class TestValidRomFile(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(delete = False) as temp_file:
            temp_file.write(b"not a rom" * 1000)
            self.temp_path = temp_file.name

    def tearDown(self):
        os.unlink(self.temp_path)

    def test_get_sha256_hex(self):
        expected = hashlib.sha256(b"not a rom" * 1000).hexdigest()
        self.assertEqual(get_sha256_hex(self.temp_path), expected)

    def test_invalid_rom_rejected(self):
        self.assertFalse(valid_rom_file(self.temp_path))

if __name__ == "__main__":
    unittest.main()
