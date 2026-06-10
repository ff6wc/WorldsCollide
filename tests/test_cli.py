import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestCli(unittest.TestCase):
    def test_help_exits_successfully(self):
        # smoke test: importing args parses all 30+ flag modules, so -h
        # exercises the entire argument interface without needing a ROM
        result = subprocess.run(
            [sys.executable, "wc.py", "-h"],
            cwd = REPO_ROOT,
            capture_output = True,
            text = True,
            timeout = 60,
        )
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("usage", result.stdout)

if __name__ == "__main__":
    unittest.main()
