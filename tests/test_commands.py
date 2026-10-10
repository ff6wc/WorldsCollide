import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_flags(*flags):
    # args/arguments.py parses the given flags and prints the canonical flag string,
    # which exercises the whole -com interface without needing a rom
    return subprocess.run(
        [sys.executable, os.path.join("args", "arguments.py"), "-i", "rom.smc", *flags],
        cwd = REPO_ROOT,
        capture_output = True,
        text = True,
        timeout = 60,
    )

# drafts 24 skill slots out of a pool of 5 commands, which forces repeated refills and,
# often, a refill triggered by a leftover the drafting character already has
DRAFT_INVARIANTS = """
import sys, types, collections
sys.argv = ["wc.py", "-i", "rom.smc", "-comfru", "0.0.0"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

MORPH = name_id["Morph"]
POOL = [MORPH] + list(range(100, 104))
CHARACTERS, SLOTS = list(range(6)), 4

for trial in range(2000):
    skills = Commands([]).draft_skills(CHARACTERS, {c : SLOTS for c in CHARACTERS}, list(POOL))
    for character in CHARACTERS:
        drafted = skills[character]
        assert len(drafted) == SLOTS, f"dropped a slot: {drafted}"
        assert len(set(drafted)) == SLOTS, f"duplicate command: {drafted}"
        assert all(command in POOL for command in drafted), drafted
    assert sum(MORPH in skills[c] for c in CHARACTERS) <= 1, "morph drafted more than once"
print("ok")
"""

# behavioral invariants for the -com pr/pru probability modes, run against fake
# characters (no rom needed). declared: fight/item/magic/possess at 100%, blitz
# at 0%; rage excluded via -rec. every character must therefore hold exactly
# fight/possess/magic/item in menu order, with nothing backfilled.
PR_INVARIANTS = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc", "-compr", "0.1.2.28.10", "100.100.100.100.0", "-rec", "16"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

GAU = 11

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    for i in c.full_random_characters():
        cmds = chars[i].commands
        if i == GAU:
            # gau never gets fight from a probability roll, even at 100%; the
            # freed slot backfills and the rest keep their menu order
            assert 0 not in cmds and cmds[0] == 28 and cmds[2:] == [2, 1], \
                f"gau menu order broken: {cmds}"
        else:
            assert cmds == [0, 28, 2, 1], f"menu order broken: {cmds}"
print("ok")
"""

# six declarations at equal likelihood: each character rolls exactly four of the
# six (the group cap), never a -rec excluded command, and never a duplicate.
PR_CAP_INVARIANTS = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc", "-compru", "0.1.2.27.28.29", "50.50.50.50.50.50", "-rec", "16"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

DECLARED = {0, 1, 2, 27, 28, 29}
NONE = name_id["None"]
RAGE = name_id["Rage"]

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

seen_over_four = False
for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    for i in c.full_random_characters():
        cmds = chars[i].commands
        real = [x for x in cmds if x != NONE]
        assert len(cmds) == 4, cmds
        assert len(set(real)) == len(real), f"duplicate command: {cmds}"
        assert RAGE not in real, f"excluded command dealt: {cmds}"
        declared_held = [x for x in real if x in DECLARED]
        assert len(declared_held) <= 4, f"cap exceeded: {cmds}"
print("ok")
"""

# a declared None (97) claims a slot and stays empty: with none at 100% and
# three 100% commands, every character has exactly one empty slot, no backfill.
PR_NONE_INVARIANTS = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc", "-compr", "5.7.13.97", "100.100.100.100"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

NONE = name_id["None"]

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    for i in c.full_random_characters():
        cmds = chars[i].commands
        real = [x for x in cmds if x != NONE]
        assert sorted(real) == [5, 7, 13], f"expected steal/swdtech/sketch + empty: {cmds}"
print("ok")
"""

# a declared morph is dealt only by its roll: at 50% morph plus unique backfill,
# no character may ever hold two morphs and backfill must never add one.
PR_MORPH_INVARIANTS = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc", "-compru", "3", "50"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

MORPH = name_id["Morph"]
NONE = name_id["None"]

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    morph_total = 0
    for i in c.full_random_characters():
        cmds = chars[i].commands
        real = [x for x in cmds if x != NONE]
        assert len(real) == 4, f"pru backfill left a hole: {cmds}"
        assert cmds.count(MORPH) <= 1, f"double morph: {cmds}"
        morph_total += cmds.count(MORPH)
    assert morph_total <= 1, f"morph on {morph_total} characters"
print("ok")
"""


# at 100% every character WINS the morph roll; exactly one may keep it and
# the rest must backfill to a full menu.
PR_MORPH_PARTYWIDE = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc", "-compru", "3", "100"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

MORPH = name_id["Morph"]
NONE = name_id["None"]

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

keepers = set()
for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    morph_total = 0
    for i in c.full_random_characters():
        cmds = chars[i].commands
        real = [x for x in cmds if x != NONE]
        assert len(real) == 4, f"backfill left a hole after morph strip: {cmds}"
        if MORPH in cmds:
            morph_total += cmds.count(MORPH)
            keepers.add(i)
    assert morph_total == 1, f"expected exactly one morph, got {morph_total}"
assert len(keepers) > 1, f"morph keeper should vary by roll, always {keepers}"
print("ok")
"""


# composed mode: -com explicit picks + -compr rolls + backfill. terra gets an
# explicit steal, locke holds a slot empty (97), cyan marks a unique-backfill
# slot (98), everyone else is 99; possess is declared at 100%.
COMPOSED_INVARIANTS = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc",
            "-com", "05979899999999999999999999", "-compr", "28", "100"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

STEAL = name_id["Steal"]
POSSESS = name_id["Possess"]
NONE = name_id["None"]

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    for i in c.full_random_characters():
        cmds = chars[i].commands
        real = [x for x in cmds if x != NONE]
        assert len(set(real)) == len(real), f"duplicate: {cmds}"
        assert POSSESS in real, f"100% possess missing: {cmds}"
    terra, locke, cyan = chars[0].commands, chars[1].commands, chars[2].commands
    assert STEAL in terra, f"explicit steal missing: {terra}"
    assert len([x for x in terra if x != NONE]) == 4, f"terra not full: {terra}"
    assert len([x for x in locke if x != NONE]) == 3, f"locke 97 slot not empty: {locke}"
    assert len([x for x in cyan if x != NONE]) == 4, f"cyan not full: {cyan}"
print("ok")
"""


# unique is unique across the seed. every skill declared (morph roll-only),
# possess excluded: 13 skill slots from 19 backfillable skills, so no skill may
# ever sit on two characters -- rolled or backfilled.
PRU_SEED_UNIQUE = """
import sys, types, collections
sys.argv = ["wc.py", "-i", "rom.smc", "-compru",
            "00.02.01.10.06.14.19.24.26.22.12.29.03.16.11.27.13.15.05.07.08.09.23",
            "100.100.100.12.10.10.12.12.10.12.12.12.11.12.10.2.10.12.10.12.12.12.12", "-rec", "28"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

COMMON = {name_id["Fight"], name_id["Magic"], name_id["Item"], name_id["None"]}

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(500):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    skills = collections.Counter(x for i in c.full_random_characters()
                                 for x in chars[i].commands if x not in COMMON)
    assert sum(skills.values()) == 13, skills
    assert max(skills.values()) == 1, f"skill dealt twice: {skills}"
    assert name_id["Possess"] not in skills, skills
print("ok")
"""

# a 100% skill under -compru goes to one character (until the pool runs dry),
# not to everyone; the characters roll in a random order, so the holder varies.
PRU_ROLLED_ONCE = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc", "-compru", "0.2.1.5", "100.100.100.100"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

STEAL = name_id["Steal"]

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

holders = set()
for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    with_steal = [i for i in c.full_random_characters() if STEAL in chars[i].commands]
    assert len(with_steal) == 1, f"steal on {with_steal}"
    holders.update(with_steal)
assert len(holders) > 1, f"steal holder should vary, always {holders}"
print("ok")
"""

# 48 skill slots (-comfru 0.0.0) from 21 skills: the pool cycles, and no skill
# is dealt again while another legal skill has been dealt fewer times.
FRU_POOL_CYCLES = """
import sys, types, collections
sys.argv = ["wc.py", "-i", "rom.smc", "-comfru", "0.0.0", "-rec", "28"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id, RANDOM_POSSIBLE_COMMANDS
from data.commands import Commands

MORPH, NONE = name_id["Morph"], name_id["None"]
LEGAL = {name_id[n] for n in RANDOM_POSSIBLE_COMMANDS} - {name_id["Possess"], MORPH}

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    skills = collections.Counter(x for i in c.full_random_characters()
                                 for x in chars[i].commands if x != NONE)
    assert skills[MORPH] <= 1, skills
    counts = [skills[x] for x in LEGAL]
    assert max(counts) - min(counts) <= 1, f"a skill was dealt again before another caught up: {skills}"
print("ok")
"""

# rolls and draft share one count: five skills at 100% roll first, the draft
# fills the rest of the 48 slots, and every legal skill stays within one deal
# of every other (a rolled skill counted twice would fall behind).
PRU_POOL_CYCLES = """
import sys, types, collections
sys.argv = ["wc.py", "-i", "rom.smc", "-compru", "5.6.7.8.9", "100.100.100.100.100",
            "-comfru", "0.0.0", "-rec", "28"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id, RANDOM_POSSIBLE_COMMANDS
from data.commands import Commands

MORPH, NONE = name_id["Morph"], name_id["None"]
LEGAL = {name_id[n] for n in RANDOM_POSSIBLE_COMMANDS} - {name_id["Possess"], MORPH}

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    skills = collections.Counter(x for i in c.full_random_characters()
                                 for x in chars[i].commands if x != NONE)
    counts = [skills[x] for x in LEGAL]
    assert max(counts) - min(counts) <= 1, f"rolled and drafted skills out of step: {skills}"
print("ok")
"""

# unique slots never repeat any skill already in the seed: terra's explicit
# steal and locke's random (99) pick are both off limits to the 98 draws.
COMPOSED_UNIQUE = """
import sys, types, collections
sys.argv = ["wc.py", "-i", "rom.smc",
            "-com", "05999898989898989898989898", "-comfru", "100.100.100"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

COMMON = {name_id["Fight"], name_id["Magic"], name_id["Item"], name_id["None"]}

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    skills = [x for i in c.full_random_characters() for x in chars[i].commands if x not in COMMON]
    assert len(skills) == 13, skills
    terra_and_locke = [x for i in (0, 1) for x in chars[i].commands if x not in COMMON]
    drafted = [x for i in c.full_random_characters()[2:] for x in chars[i].commands if x not in COMMON]
    assert len(set(drafted)) == len(drafted), f"98 draws repeated: {drafted}"
    assert not set(drafted) & set(terra_and_locke), f"98 repeated an earlier pick: {skills}"
print("ok")
"""


# suplex a train guarantees one blitz, but never a second one: blitz already
# rolled or picked explicitly counts, the forced blitz takes a backfill slot (so
# unique seeds stay unique), and with no backfill slot left a rolled skill gives
# way. run with the objective switched on; FLAGS and ONE_HOLDER are filled in.
SUPLEX_BLITZ = """
import sys, types, collections
sys.argv = ["wc.py", "-i", "rom.smc"] + FLAGS
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = True

from constants.commands import name_id
from data.commands import Commands

BLITZ, NONE = name_id["Blitz"], name_id["None"]
COMMON = {name_id["Fight"], name_id["Magic"], name_id["Item"], NONE}

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    menus = [chars[i].commands for i in c.full_random_characters()]
    holders = [menu.count(BLITZ) for menu in menus if BLITZ in menu]
    assert holders, f"no blitz: {menus}"
    assert max(holders) == 1, f"blitz twice on one character: {menus}"
    if ONE_HOLDER:
        assert len(holders) == 1, f"blitz on {len(holders)} characters: {menus}"
    assert all(NONE not in menu for menu in menus), f"slot left empty: {menus}"
    if UNIQUE:
        skills = collections.Counter(x for menu in menus for x in menu if x not in COMMON)
        assert max(skills.values()) == 1, f"skill dealt twice: {skills}"
print("ok")
"""

SUPLEX_CASES = (
    # declared blitz at 100% under -compru: rolled once, never forced again
    ("rolled", ["-compru", "10", "100", "-comfru", "100.100.100"], True, True),
    # explicit -com blitz for terra plus unique backfill
    ("explicit", ["-com", "10989898989898989898989898", "-comfru", "100.100.100"], True, True),
    # blitz excluded from backfill is still forced in, into a backfill slot
    ("excluded", ["-comfru", "100.100.100", "-rec", "10"], True, True),
    # every slot rolled at 100%: a rolled skill gives way to the forced blitz
    ("no_backfill", ["-compr", "00.02.01.05.06", "100.100.100.100.100", "-rec", "10"], True, False),
    # -compr rolls blitz independently (several holders are fine), never twice on one menu
    ("compr_rolls", ["-compr", "10", "50", "-comfr", "100.100.100"], False, False),
)


class TestCommandsFlag(unittest.TestCase):
    def assert_accepted(self, *flags, expected = None):
        result = parse_flags(*flags)
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        if expected is not None:
            self.assertIn(expected, result.stdout)
        return result.stdout

    def assert_rejected(self, *flags, expected = None):
        result = parse_flags(*flags)
        self.assertNotEqual(result.returncode, 0, msg = result.stdout)
        if expected is not None:
            self.assertIn(expected, result.stderr)

    def test_character_command_ids(self):
        self.assert_accepted("-com", "03050708091011121315191617", expected = "-com 03050708091011121315191617")
        self.assert_accepted("-com", "99999999999999999999999999", expected = "-com 99999999999999999999999999")

    def test_character_command_ids_rejected_at_parse(self):
        # ids generation can't honor must fail at parse time, not as a raw
        # ValueError mid-build: Magic (02) and Item (01) aren't explicit picks,
        # and Leap (17) is only legal in Gau's second slot (index 12)
        self.assert_rejected("-com", "02" + "99" * 12, expected = "not a valid command id")
        self.assert_rejected("-com", "01" + "99" * 12, expected = "not a valid command id")
        self.assert_rejected("-com", "17" + "99" * 12, expected = "not a valid command id")
        self.assert_accepted("-com", "99" * 12 + "17", expected = "-com " + "99" * 12 + "17")

    def test_full_random_modes(self):
        self.assert_accepted("-comfr", "10.50.90", expected = "-comfr 10.50.90")
        self.assert_accepted("-comfru", "0.0.0", expected = "-comfru 0.0.0")

    def test_retired_com_modes_rejected(self):
        # the old '-com fr/pr ...' meta-mode syntax points at the new flags
        self.assert_rejected("-com", "fr", "10.50.90", expected = "use -comfr")
        self.assert_rejected("-com", "pru", "3", "50", expected = "use -compru")

    def test_no_commands_flag(self):
        self.assertNotIn("-com", self.assert_accepted())
        self.assertNotIn("-com", self.assert_accepted("-com"))

    def test_family_composition(self):
        # -com composes with the probability flags; each emits its own flag
        out = self.assert_accepted("-com", "05999999999999999999999999", "-comfr", "50.50.50")
        self.assertIn("-com 05999999999999999999999999", out)
        self.assertIn("-comfr 50.50.50", out)
        # -comfr folds into -compr as extra declarations; both still emitted
        out = self.assert_accepted("-compr", "28", "100", "-comfr", "50.50.50")
        self.assertIn("-compr 28 100", out)
        self.assertIn("-comfr 50.50.50", out)
        # unique variants pair up
        self.assert_accepted("-compru", "28", "100", "-comfru", "50.50.50")

    def test_family_conflicts_rejected(self):
        self.assert_rejected("-comfr", "10.50.90", "-comfru", "10.50.90",
                             expected = "-comfr and -comfru are incompatible")
        self.assert_rejected("-compr", "28", "100", "-compru", "28", "100",
                             expected = "-compr and -compru are incompatible")
        self.assert_rejected("-comfr", "10.50.90", "-compru", "28", "100",
                             expected = "cannot mix unique and non-unique")
        # an id declared by both -comfr and -compr is a conflict
        self.assert_rejected("-comfr", "10.50.90", "-compr", "0.28", "100.100",
                             expected = "declared by both")

    def test_unique_draft_refills(self):
        result = subprocess.run(
            [sys.executable, "-c", DRAFT_INVARIANTS],
            cwd = REPO_ROOT,
            capture_output = True,
            text = True,
            timeout = 120,
        )
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("ok", result.stdout)

    def test_invalid_values_rejected(self):
        self.assert_rejected("-com", "0305070809", expected = "must be 26 digits")
        self.assert_rejected("-com", "03050708091011121315191650", expected = "not a valid command id")
        self.assert_rejected("-comfr", "10.50", expected = "3 percent chances")
        self.assert_rejected("-comfr", "10.50.101", expected = "must be between 0 and 100")
        self.assert_rejected("-comfru", "10.50.abc", expected = "not a valid percent chance")

    def test_probability_modes(self):
        # ids are canonicalized to two digits; percents kept as given
        self.assert_accepted("-compr", "0.1.2.28", "50.50.50.100",
                             expected = "-compr 00.01.02.28 50.50.50.100")
        self.assert_accepted("-compru", "0.1.2.27.28.29", "50.50.50.50.50.50",
                             expected = "-compru 00.01.02.27.28.29 50.50.50.50.50.50")
        # 97 declares a chance at an empty slot
        self.assert_accepted("-compr", "97.10", "50.100", expected = "-compr 97.10 50.100")

    def test_probability_invalid_rejected(self):
        self.assert_rejected("-compr", "0.1.2", expected = "expected 2 arguments")
        self.assert_rejected("-compr", "0.1.2", "50.50", expected = "3 command ids but 2 percent chances")
        self.assert_rejected("-compr", "0.25", "50.50", expected = "not a valid probability command id")  # Summon
        self.assert_rejected("-compr", "0.0", "50.50", expected = "duplicate probability command id")
        self.assert_rejected("-compr", "0.abc", "50.50", expected = "not a valid command id")
        self.assert_rejected("-compr", "0.1", "50.101", expected = "must be between 0 and 100")
        self.assert_rejected("-comfr", "50.50", expected = "3 percent chances")
        # a command cannot both have a probability and be excluded by -rec
        self.assert_rejected("-compr", "0.16", "50.50", "-rec", "16",
                             expected = "both given a probability and excluded by -rec")

    def test_probability_invariants(self):
        for name, script in (("pr", PR_INVARIANTS), ("cap", PR_CAP_INVARIANTS),
                             ("none", PR_NONE_INVARIANTS), ("morph", PR_MORPH_INVARIANTS),
                             ("morph_partywide", PR_MORPH_PARTYWIDE),
                             ("composed", COMPOSED_INVARIANTS),
                             ("pru_seed_unique", PRU_SEED_UNIQUE), ("pru_rolled_once", PRU_ROLLED_ONCE),
                             ("fru_pool_cycles", FRU_POOL_CYCLES), ("pru_pool_cycles", PRU_POOL_CYCLES), ("composed_unique", COMPOSED_UNIQUE)):
            with self.subTest(name):
                result = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd = REPO_ROOT,
                    capture_output = True,
                    text = True,
                    timeout = 120,
                )
                self.assertEqual(result.returncode, 0, msg = result.stderr)
                self.assertIn("ok", result.stdout)

    def test_suplex_train_blitz(self):
        for name, flags, one_holder, unique in SUPLEX_CASES:
            with self.subTest(name):
                script = (f"FLAGS = {flags!r}\nONE_HOLDER = {one_holder}\nUNIQUE = {unique}\n"
                          + SUPLEX_BLITZ)
                result = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd = REPO_ROOT,
                    capture_output = True,
                    text = True,
                    timeout = 120,
                )
                self.assertEqual(result.returncode, 0, msg = result.stderr)
                self.assertIn("ok", result.stdout)

    def test_random_exclude_dot_list(self):
        # arbitrary-length dot-separated exclusions, re-emitted canonically
        self.assert_accepted("-rec", "28.27", expected = "-rec 28.27")
        self.assert_accepted("-rec", "05.07.10.16.13", expected = "-rec 05.07.10.16.13")
        # single-digit input normalizes to two-digit canonical form
        self.assert_accepted("-rec", "5.7", expected = "-rec 05.07")
        # the none id (97) is dropped from the canonical string
        self.assertNotIn("-rec", self.assert_accepted("-rec", "97"))

    def test_random_exclude_legacy_wrappers(self):
        # legacy -recN flags still parse and fold into the canonical -rec form
        self.assert_accepted("-rec1", "28", "-rec2", "27", expected = "-rec 28.27")
        self.assert_accepted("-rec3", "10", expected = "-rec 10")
        # mixed usage: -rec values first, then the legacy flags in order
        self.assert_accepted("-rec", "05", "-rec1", "28", expected = "-rec 05.28")

    def test_random_exclude_invalid_rejected(self):
        self.assert_rejected("-rec", "28.abc", expected = "not a valid command id")
        self.assert_rejected("-rec", "01", expected = "not an excludable command id")  # Item
        # excluding the whole random pool is rejected (would empty every draw)
        from constants.commands import RANDOM_POSSIBLE_COMMANDS, name_id
        everything = ".".join(f"{name_id[name]:02}" for name in RANDOM_POSSIBLE_COMMANDS)
        self.assert_rejected("-rec", everything, expected = "cannot exclude every")

if __name__ == "__main__":
    unittest.main()
