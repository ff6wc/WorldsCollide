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

class TestStartLevelRandom(unittest.TestCase):
    def parse_flags(self, *flags):
        return subprocess.run(
            [sys.executable, os.path.join("args", "arguments.py"), "-i", "rom.smc", *flags],
            cwd = REPO_ROOT,
            capture_output = True,
            text = True,
            timeout = 60,
        )

    def test_valid_bounds(self):
        result = self.parse_flags("-stlr", "10", "50")
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("-stlr 10 50", result.stdout)

    def test_reversed_bounds_normalized(self):
        result = self.parse_flags("-stlr", "50", "10")
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("-stlr 10 50", result.stdout)

    def test_identical_bounds(self):
        result = self.parse_flags("-stlr", "20", "20")
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("-stlr 20 20", result.stdout)

    def test_mutually_exclusive_with_stl(self):
        result = self.parse_flags("-stl", "10", "-stlr", "20", "30")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not allowed with argument -stl", result.stderr)

    def test_out_of_bounds_rejected(self):
        # Minimum level is 3, maximum is 99
        for bounds in [("2", "50"), ("10", "100"), ("0", "10")]:
            result = self.parse_flags("-stlr", *bounds)
            self.assertNotEqual(result.returncode, 0, msg = f"Expected failure for bounds {bounds}")

    def test_options_formatting(self):
        script = """
import sys
sys.argv = ["wc.py", "-i", "rom.smc", "-stlr", "15", "45"]
import args
import args.characters as char_args
opts = dict((name, val) for name, val, _ in char_args.options(args))
assert opts["Start Level"] == "Random 15-45", f"Unexpected option: {opts.get('Start Level')}"
assert args.start_level_random_min == 15
assert args.start_level_random_max == 45
print("ok")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd = REPO_ROOT,
            capture_output = True,
            text = True,
            timeout = 60,
        )
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("ok", result.stdout)

if __name__ == "__main__":
    unittest.main()

