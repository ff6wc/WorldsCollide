import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from data import level_cap

def parse_flags(*flags):
    # args/arguments.py parses the given flags and prints the canonical flag string
    return subprocess.run(
        [sys.executable, os.path.join("args", "arguments.py"), "-i", "rom.smc", *flags],
        cwd = REPO_ROOT,
        capture_output = True,
        text = True,
        timeout = 60,
    )

# a stand-in for the rom's table (no rom needed): grows like the real one, from
# 4 (32 experience) at level 1 to ~11,000 (~88,000 experience) at level 98
BASE = [4 + (level * level * 115) // 100 for level in range(level_cap.EXP_TABLE_COUNT)]

class TestLevelCapFlag(unittest.TestCase):
    def assert_accepted(self, *flags, expected):
        result = parse_flags(*flags)
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn(expected, result.stdout)

    def assert_rejected(self, *flags, expected):
        result = parse_flags(*flags)
        self.assertNotEqual(result.returncode, 0, msg = result.stdout)
        self.assertIn(expected, result.stderr)

    def test_hard_and_soft(self):
        self.assert_accepted("-lc", "30", expected = "-lc 30")
        self.assert_accepted("-lc", "40", "5", expected = "-lc 40 5")
        self.assert_accepted("-lc", "99", "99", expected = "-lc 99 99")
        # the width may have one decimal place, written back without a trailing .0
        self.assert_accepted("-lc", "40", "2.5", expected = "-lc 40 2.5")
        self.assert_accepted("-lc", "40", "2.0", expected = "-lc 40 2 ")
        self.assert_accepted("-lc", "40", ".5", expected = "-lc 40 0.5")
        self.assert_accepted("-lc", "40", "0.1", expected = "-lc 40 0.1")

    def test_no_flag(self):
        result = parse_flags()
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertNotIn("-lc", result.stdout)

    def test_rejected(self):
        self.assert_rejected("-lc", "1", expected = "from 2 to 98")
        self.assert_rejected("-lc", "99", expected = "from 2 to 98")
        # levels are whole numbers; the width allows one decimal place
        self.assert_rejected("-lc", "30.5", expected = "whole number from 2 to 98")
        self.assert_rejected("-lc", "40.5", "2", expected = "whole number from 1 to 99")
        self.assert_rejected("-lc", "40", "2.55", expected = "at most one decimal place")
        self.assert_rejected("-lc", "40", "0", expected = "width '0' must be from 0.1 to 99")
        self.assert_rejected("-lc", "40", "100", expected = "width '100' must be from 0.1 to 99")
        self.assert_rejected("-lc", "0", "5", expected = "mean '0' must be a whole number from 1 to 99")
        self.assert_rejected("-lc", "a", expected = "whole number from 2 to 98")
        self.assert_rejected("-lc", "1", "2", "3", expected = "expected LEVEL")

class TestLevelCapTable(unittest.TestCase):
    def test_hard_cap(self):
        # the battle experience cap is exactly the total for the cap level: that
        # level is reachable, the next one is not, and it fits the 24-bit cap
        totals = level_cap.totals(BASE)
        for cap in range(2, 99):
            experience = level_cap.hard_cap_experience(BASE, cap)
            self.assertEqual(experience, totals[cap - 1])
            self.assertLess(experience, totals[cap], f"cap {cap}: next level reachable")
            self.assertLessEqual(experience, level_cap.BATTLE_EXP_CAP)
            self.assertEqual(len(experience.to_bytes(3, "little")), 3)

    def test_soft_cap(self):
        table = level_cap.capped_table(BASE, mean = 40, width = 5)
        # doubles from mean to mean + 1, untouched far below, never below default where reachable
        self.assertEqual(table[40 - 1], 2 * BASE[40 - 1])
        # base 10: one width past the mean, the step is 1 + 10 = 11 times default
        self.assertEqual(table[45 - 1], 11 * BASE[45 - 1])
        self.assertEqual(table[:10], BASE[:10])
        totals = level_cap.totals(table)
        self.assertTrue(all(value >= default for level, (value, default) in enumerate(zip(table, BASE), start = 1)
                            if totals[level] <= level_cap.BATTLE_EXP_CAP))
        # steeper for smaller widths
        narrow = level_cap.capped_table(BASE, mean = 40, width = 2)
        self.assertGreater(narrow[45 - 1], table[45 - 1])
        # one-decimal widths: half a level per tenfold step
        half = level_cap.capped_table(BASE, mean = 40, width = 0.5)
        self.assertEqual(half[40 - 1], 2 * BASE[40 - 1])
        self.assertEqual(half[41 - 1], level_cap.STEP_MAX)
        # extreme widths do not overflow
        level_cap.capped_table(BASE, mean = 2, width = 0.1)
        level_cap.capped_table(BASE, mean = 99, width = 99)

    def test_highest_level(self):
        # the soft cap's last reachable level: its total fits under the battle
        # cap and the next level's does not (or it is 99)
        for mean, width in ((40, 5), (40, 1), (60, 10), (20, 0.5), (99, 99)):
            table = level_cap.capped_table(BASE, mean = mean, width = width)
            totals = level_cap.totals(table)
            highest = level_cap.highest_level(table, level_cap.BATTLE_EXP_CAP)
            self.assertLessEqual(totals[highest - 1], level_cap.BATTLE_EXP_CAP)
            if highest < 99:
                self.assertGreater(totals[highest], level_cap.BATTLE_EXP_CAP)
        # a hard cap's highest level is the cap itself
        for cap in (2, 30, 98):
            self.assertEqual(level_cap.highest_level(BASE, level_cap.hard_cap_experience(BASE, cap)), cap)

    def test_total_never_wraps(self):
        # battle stops experience at 15,000,000, but -stl/-stlr/-sal can place a
        # character on any level; the 24-bit total must not wrap on the way to 99
        tables = [level_cap.capped_table(BASE, mean = mean, width = width)
                  for mean in range(1, 100, 7) for width in (0.1, 0.5, 1, 2.5, 3, 10, 99)]
        tables += [level_cap.capped_table([level_cap.STEP_MAX] * 98, mean = 2, width = 1)]
        for table in tables:
            self.assertLess(sum(table), level_cap.SUM_LIMIT)
            self.assertTrue(all(0 < value <= level_cap.STEP_MAX for value in table))

    def test_reachable_levels_unchanged_by_guard(self):
        # the guard only touches levels battle can no longer reach
        raw = level_cap.soft_cap(BASE, 30, 1)
        guarded = level_cap.guard_wrap(raw)
        totals = level_cap.totals(guarded)
        for level in range(1, 99):
            if totals[level] <= level_cap.BATTLE_EXP_CAP:
                self.assertEqual(guarded[level - 1], raw[level - 1])

if __name__ == "__main__":
    unittest.main()
