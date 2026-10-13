import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# -sli pack sizes per item category, checked without a rom: relics are sold as
# singles except earrings (1-2, a pair stacks)
RELIC_PACKS = """
import sys
sys.argv = ["wc.py", "-i", "rom.smc", "-sli"]
import args
from data.shops import Shops
from constants.items import RELICS, name_id

shops = Shops.__new__(Shops)
earrings = name_id["Earrings"]
for relic in RELICS:
    sizes = {shops.get_pack_size(relic) for _ in range(200)}
    if relic == earrings:
        assert sizes == {1, 2}, f"earrings packs {sizes}"
    else:
        assert sizes == {1}, f"relic {relic} packs {sizes}"
print("ok")
"""

class TestShopLimitedInventory(unittest.TestCase):
    def test_relics_are_singles(self):
        result = subprocess.run([sys.executable, "-c", RELIC_PACKS], cwd = REPO_ROOT,
                                capture_output = True, text = True, timeout = 120)
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("ok", result.stdout)

if __name__ == "__main__":
    unittest.main()
