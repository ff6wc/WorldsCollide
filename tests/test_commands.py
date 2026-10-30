import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_flags(*flags):
    # args/arguments.py parses the given flags and prints the canonical flag string,
    # which exercises the whole command interface without needing a rom
    return subprocess.run(
        [sys.executable, os.path.join("args", "arguments.py"), "-i", "rom.smc", *flags],
        cwd = REPO_ROOT,
        capture_output = True,
        text = True,
        timeout = 60,
    )

def run_script(script, timeout = 300):
    return subprocess.run([sys.executable, "-c", script], cwd = REPO_ROOT,
                          capture_output = True, text = True, timeout = timeout)

# runs the command assignment SEEDS times on fake characters (no rom needed) and
# hands every seed's menus to CHECK, then FINISH. FLAGS, SEEDS, SUPLEX, CHECK and
# FINISH are filled in per test
HARNESS = """
import sys, types, collections, random
sys.argv = ["wc.py", "-i", "rom.smc"] + FLAGS
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = SUPLEX

from constants.commands import name_id, id_name, RANDOM_POSSIBLE_COMMANDS
from data.commands import Commands

FIGHT, MAGIC, ITEM, NONE = name_id["Fight"], name_id["Magic"], name_id["Item"], name_id["None"]
COMMON = {FIGHT, MAGIC, ITEM, NONE}
SKILLS = {name_id[name] for name in RANDOM_POSSIBLE_COMMANDS}
GAU = 11

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

PICKS = list(args.character_commands)   # mod_commands rewrites the list in place

def build():
    args.character_commands[:] = PICKS
    args.group_modules["commands"].resolve_random_weights(args)    # each seed draws its own
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    if args.commands_probability_mode:
        c.mod_probability_random_commands()
        return [chars[i].commands for i in c.full_random_characters()]
    c.mod_commands()
    return [[chars[i].commands[1]] for i in range(11)] + [chars[GAU].commands[:2]]

random.seed(SEED)
state = collections.Counter()
for trial in range(SEEDS):
    menus = build()
    CHECK
FINISH
print("ok")
"""

def harness(flags, check, finish = "", seeds = 300, suplex = False, seed = 1):
    indent = lambda code: code.replace("\n", "\n    ")
    script = HARNESS.replace("CHECK", indent(check)).replace("FINISH", finish)
    return (script.replace("FLAGS", repr(flags)).replace("SEEDS", str(seeds))
            .replace("SUPLEX", str(suplex)).replace("SEED", str(seed)))

# every menu: four slots, no command twice, Gau never Fight, Morph on one character at most
BASIC_CHECKS = """
for index, menu in enumerate(menus):
    real = [x for x in menu if x != NONE]
    assert len(real) == len(set(real)), f"command twice: {menu}"
    if index == GAU and args.commands_probability_mode:
        assert FIGHT not in menu, f"gau got fight: {menu}"
assert sum(name_id["Morph"] in menu for menu in menus) <= 1, f"morph twice: {menus}"
"""

# no skill repeats while another legal skill is unused
UNIQUE_CHECK = """
skills = collections.Counter(x for menu in menus for x in menu if x in SKILLS)
legal = [s for s in SKILLS if args.command_weights_map[s] > 0]
if len(skills) < len(legal):
    assert max(skills.values()) == 1, f"skill dealt twice early: {skills}"
"""

# seed (or per character) frequency of every skill, printed as KEY=value for the test to read
def frequency_finish(per_character = False):
    return f"""
for skill in sorted(SKILLS):
    print(f"{{id_name[skill]}}={{state[skill] / SEEDS / {12 if per_character else 1}:.5f}}")
"""

COUNT_SEED = "state.update({x for menu in menus for x in menu})"
COUNT_CHARACTER = "state.update(x for menu in menus for x in menu)"

def frequencies(output):
    return {line.split("=")[0] : float(line.split("=")[1]) for line in output.splitlines() if "=" in line}


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

    def assert_script(self, script):
        result = run_script(script)
        self.assertEqual(result.returncode, 0, msg = result.stderr[-3000:])
        self.assertIn("ok", result.stdout)
        return result.stdout

    # --- -com --------------------------------------------------------------

    def test_character_command_ids(self):
        self.assert_accepted("-com", "03050708091011121315191617", expected = "-com 03050708091011121315191617")
        self.assert_accepted("-com", "99999999999999999999999999", expected = "-com 99999999999999999999999999")

    def test_character_command_ids_rejected_at_parse(self):
        # ids generation can't honor must fail at parse time: Magic (02) and Item (01)
        # aren't explicit picks, and Leap (17) is only legal in Gau's second slot
        self.assert_rejected("-com", "02" + "99" * 12, expected = "not a valid command id")
        self.assert_rejected("-com", "01" + "99" * 12, expected = "not a valid command id")
        self.assert_rejected("-com", "17" + "99" * 12, expected = "not a valid command id")
        self.assert_accepted("-com", "99" * 12 + "17", expected = "-com " + "99" * 12 + "17")
        self.assert_rejected("-com", "0305070809", expected = "must be 26 digits")

    def test_no_commands_flag(self):
        self.assertNotIn("-com", self.assert_accepted())
        self.assertNotIn("-com", self.assert_accepted("-com"))

    # --- -comr / -comru ----------------------------------------------------

    def test_random_modes(self):
        self.assert_accepted("-comr", "10.50.90", expected = "-comr 10.50.90")
        self.assert_accepted("-comru", "0.0.0", expected = "-comru 0")
        # one percent covers all three, and three equal percents print as one
        self.assert_accepted("-comru", "90", expected = "-comru 90")
        self.assert_accepted("-comr", "90.90.90", expected = "-comr 90")
        out = self.assert_accepted("-com", "05999999999999999999999999", "-comr", "50")
        self.assertIn("-com 05999999999999999999999999", out)
        self.assertIn("-comr 50", out)

    def test_random_modes_rejected(self):
        self.assert_rejected("-comr", "10", "-comru", "10", expected = "-comr and -comru are incompatible")
        self.assert_rejected("-comr", "10.50", expected = "one percent chance or 3")
        self.assert_rejected("-comr", "10.50.101", expected = "must be between 0 and 100")
        self.assert_rejected("-comru", "10.50.abc", expected = "not a valid percent chance")

    def test_retired_flags_rejected(self):
        # the dev-only flags these replace point at the new form
        self.assert_rejected("-comfr", "10.50.90", expected = "use -comr")
        self.assert_rejected("-comfru", "10.50.90", expected = "use -comru")
        self.assert_rejected("-compr", "0.28", "50.100", expected = "-compr has been replaced")
        self.assert_rejected("-compru", "28", "100", expected = "-compru has been replaced")
        self.assert_rejected("-rec", "28.27", expected = "use -comw NAME:0")
        self.assert_rejected("-com", "fr", "10.50.90", expected = "has been replaced")

    # --- -comw -------------------------------------------------------------

    def test_weights_parse(self):
        # names ignore case and punctuation, ids work too; canonical form groups by
        # weight (always first, then heaviest), skills in id order, names compacted
        self.assert_accepted("-comru", "90", "-comw", "Shock.Possess:0.5", expected = "-comw shock.possess:0.5")
        self.assert_accepted("-comru", "90", "-comw", "28.27:0.5", expected = "-comw shock.possess:0.5")
        self.assert_accepted("-comr", "90", "-comw", "jump:always,blitz.runic:5,shock.possess:0.1",
                             expected = "-comw jump:always,blitz.runic:5,shock.possess:0.1")
        self.assert_accepted("-comr", "90", "-comw", "jump:always:0.5", expected = "-comw jump:always:0.5")
        self.assert_accepted("-comr", "90", "-comw", "X-Magic.GPRain:rare,magitek:never",
                             expected = "-comw xmagic.gprain:0.25,magitek:0")
        self.assert_accepted("-comr", "90", "-comw", "none:0.5", expected = "-comw none:0.5")
        # a weight of 1 is the default and drops out
        self.assertNotIn("-comw", self.assert_accepted("-comr", "90", "-comw", "jump:1,lore:common"))
        # -comw also applies to -com's random slots on its own
        self.assert_accepted("-com", "99" * 13, "-comw", "slot:0", expected = "-comw slot:0")

    def test_weights_other(self):
        # other weighs every skill no entry names, wherever it is listed; the canonical
        # form is the shortest, so the long list and its other form print (and seed) the same
        from constants.commands import RANDOM_POSSIBLE_COMMANDS
        everything_but_dance = ".".join(name for name in RANDOM_POSSIBLE_COMMANDS if name != "Dance")
        for weights in ("dance:1,other:0", "other:never,dance:common", everything_but_dance + ":0"):
            self.assert_accepted("-comru", "75", "-comw", weights, expected = "-comw dance:1,other:0")
        self.assert_accepted("-comr", "90", "-comw", "jump:always,blitz:5,other:rare",
                             expected = "-comw jump:always,blitz:5,other:0.25")
        # a few off-default skills stay a plain list; other:1 is the default
        self.assert_accepted("-comr", "90", "-comw", "shock.possess:rare,other:1",
                             expected = "-comw shock.possess:0.25")
        self.assertNotIn("other", self.assert_accepted("-comr", "90", "-comw", "shock.possess:rare"))
        # -recN exclusions are named too
        self.assert_accepted("-rec1", "28", "-comw", "jump:1,other:2", expected = "-comw jump:1,possess:0,other:2")
        # ... but not the empty slot
        self.assert_accepted("-comr", "90", "-comw", "other:0.5,none:0.5", expected = "-comw none:0.5,other:0.5")

    def test_weights_other_rejected(self):
        self.assert_rejected("-comw", "other.jump:0", expected = "must be a group of its own")
        self.assert_rejected("-comw", "other:0,other:1", expected = "other is given a weight twice")
        self.assert_rejected("-comw", "other:always", expected = "other cannot be always")
        self.assert_rejected("-comw", "other:0", expected = "cannot give every")

    def test_weights_rejected(self):
        self.assert_rejected("-comw", "jump", expected = "must be GROUP:WEIGHT")
        self.assert_rejected("-comw", "jump:abc", expected = "is not a weight")
        self.assert_rejected("-comw", "jump:-1", expected = "must be a number >= 0")
        self.assert_rejected("-comw", "summon:2", expected = "not a randomizable skill")
        self.assert_rejected("-comw", "fight:2", expected = "set its chance with -comr/-comru")
        self.assert_rejected("-comw", "00:2", expected = "set its chance with -comr/-comru")
        self.assert_rejected("-comw", "jump:2,jump:3", expected = "given a weight twice")
        self.assert_rejected("-comw", "none:always", expected = "cannot be always")
        from constants.commands import RANDOM_POSSIBLE_COMMANDS, name_id
        everything = ".".join(f"{name_id[name]:02}" for name in RANDOM_POSSIBLE_COMMANDS)
        self.assert_rejected("-comw", everything + ":0", expected = "cannot give every")

    def test_weights_random(self):
        # randomN: N skills drawn per seed from the unnamed ones; the flag keeps the group,
        # named skills stay listed (naming one keeps it out of the draws), other:1 drops out
        self.assert_accepted("-comru", "75", "-comw", "random:1,other:0", expected = "-comw random:1,other:0")
        self.assert_accepted("-comru", "75", "-comw", "Random-3:1,other:0", expected = "-comw random3:1,other:0")
        self.assert_accepted("-comr", "90", "-comw", "random:1,random2:1,other:0", expected = "-comw random3:1,other:0")
        self.assert_accepted("-comr", "90", "-comw", "other:0,random2:rare,random:always,jump:1",
                             expected = "-comw jump:1,random:always,random2:0.25,other:0")
        self.assert_accepted("-comr", "90", "-comw", "random20:0", expected = "-comw random20:0")
        self.assert_accepted("-comr", "90", "-comw", "random:0,other:1", expected = "-comw random:0")
        self.assert_accepted("-rec1", "28", "-comw", "random:2", expected = "-comw possess:0,random:2")

    def test_weights_random_rejected(self):
        self.assert_rejected("-comw", "random.jump:0", expected = "random must be a group of its own")
        self.assert_rejected("-comw", "random0:1", expected = "must draw at least one skill")
        self.assert_rejected("-comw", "random22:0", expected = "draw 22 skills but only 21")
        self.assert_rejected("-comw", "jump:1,random21:0", expected = "draw 21 skills but only 20")
        self.assert_rejected("-comw", "random21:0", expected = "cannot give every")
        self.assert_rejected("-comw", "random:0,other:0", expected = "cannot give every")

    def test_legacy_exclusions(self):
        # main's -recN flags still parse, as weight 0
        self.assert_accepted("-rec1", "28", "-rec2", "27", expected = "-comw shock.possess:0")
        self.assert_accepted("-rec3", "10", "-comw", "jump:2", expected = "-comw jump:2,blitz:0")
        self.assert_rejected("-rec1", "28", "-comw", "possess:2", expected = "also excluded by -rec1")

    # --- generation --------------------------------------------------------

    def test_random_one_skill_for_everyone(self):
        # random:1,other:0: every character's skill is the seed's one pick, which varies
        # by seed and is never morph (one character only: everyone else would be empty)
        check = BASIC_CHECKS + """
skills = {x for menu in menus for x in menu if x in SKILLS}
assert skills == set(args.command_random_picks[0]), (skills, args.command_random_picks)
assert all(set(menu) & skills for menu in menus), menus
state.update(skills)
"""
        finish = """
assert name_id["Morph"] not in state, state
assert len(state) == 20, state
"""
        self.assert_script(harness(["-comru", "75.0.100", "-comw", "random:1,other:0"], check, finish, seeds = 600))
        # random20:0 leaves one skill the same way
        check = """
dealable = [s for s in SKILLS if args.command_weights_map[s] > 0]
assert len(dealable) == 1 and dealable != [name_id["Morph"]], dealable
"""
        self.assert_script(harness(["-comru", "75", "-comw", "random20:0"], check, seeds = 600))

    def test_random_pool_may_hold_morph(self):
        # random2:1,other:0: morph can be one of the two (the other fills the rest)
        check = BASIC_CHECKS + """
picks = set(args.command_random_picks[0])
assert len(picks) == 2 and {x for menu in menus for x in menu if x in SKILLS} <= picks, (picks, menus)
state.update(picks)
"""
        self.assert_script(harness(["-comru", "75", "-comw", "random2:1,other:0"], check,
                                   'assert state[name_id["Morph"]] > 0, state', seeds = 600))

    def test_random_draws_follow_the_seed(self):
        # the seed decides the picks: same seed, same picks; the flag string never changes
        script = """
import sys, io, contextlib
sys.argv = ["wc.py", "-i", "rom.smc", "-s", sys.argv[1], "-comru", "75", "-comw", "random3:1,other:0"]
with contextlib.redirect_stdout(io.StringIO()):
    import args
from constants.commands import name_id
assert "-comw random3:1,other:0" in args.flags, args.flags
assert args.blitz_command_possible == (name_id["Blitz"] in args.command_random_picks[0])
print("picks", args.command_random_picks)
"""
        def picks(seed):
            result = subprocess.run([sys.executable, "-c", script, seed], cwd = REPO_ROOT,
                                    capture_output = True, text = True, timeout = 60)
            self.assertEqual(result.returncode, 0, msg = result.stderr[-3000:])
            return result.stdout.strip().splitlines()[-1]
        self.assertEqual(picks("alpha"), picks("alpha"))
        self.assertGreater(len({picks(seed) for seed in ("alpha", "beta", "gamma", "delta")}), 1)

    def test_unique_invariants(self):
        for flags in (["-comru", "90"], ["-comru", "0", "-comw", "possess:0"],
                      ["-comru", "100", "-comw", "jump:always,shock.possess:0.1,slot:0"]):
            with self.subTest(flags):
                check = BASIC_CHECKS + UNIQUE_CHECK + """
assert all(NONE not in menu for menu in menus), f"slot left empty: {menus}"
assert not any(x in SKILLS and args.command_weights_map[x] == 0 for menu in menus for x in menu), menus
for skill in args.command_always:
    assert any(skill in menu for menu in menus), f"always skill missing: {menus}"
"""
                self.assert_script(harness(flags, check))

    def test_repeat_invariants(self):
        check = BASIC_CHECKS + """
assert any(name_id["Jump"] in menu for menu in menus), "always jump missing"
"""
        self.assert_script(harness(["-comr", "90", "-comw", "jump:always:0.5"], check))

    def test_composed_with_com(self):
        # terra: explicit steal + three drawn; locke: 97 (empty) + 98 + basics; cyan..: 99s
        check = BASIC_CHECKS + """
terra, locke, cyan = menus[0], menus[1], menus[2]
assert name_id["Steal"] in terra, f"explicit steal missing: {terra}"
assert len([x for x in terra if x != NONE]) == 4, f"terra not full: {terra}"
assert len([x for x in locke if x != NONE]) == 3, f"locke's 97 slot not empty: {locke}"
assert len([x for x in cyan if x != NONE]) == 4, f"cyan not full: {cyan}"
"""
        self.assert_script(harness(["-com", "05979899999999999999999999", "-comr", "100"], check))
        # 98 slots never repeat an explicit pick or each other while skills remain
        check = """
skills = [x for menu in menus for x in menu if x in SKILLS]
assert len(skills) == 13, skills
early = [x for menu in menus[:2] for x in menu if x in SKILLS]
drafted = [x for menu in menus[2:] for x in menu if x in SKILLS]
assert len(set(drafted)) == len(drafted), f"98 draws repeated: {drafted}"
assert not set(drafted) & set(early), f"98 repeated an earlier pick: {skills}"
"""
        self.assert_script(harness(["-com", "05999898989898989898989898", "-comru", "100"], check))

    def test_unique_cycles_when_slots_exceed_skills(self):
        # 48 skill slots from 20 skills: every skill dealt before any is dealt a third time
        check = """
skills = collections.Counter(x for menu in menus for x in menu if x in SKILLS)
assert max(skills.values()) - min(skills.values()) <= 1 or name_id["Morph"] in skills, skills
assert all(NONE not in menu for menu in menus[:11]), menus
"""
        self.assert_script(harness(["-comru", "0", "-comw", "possess:0"], check))

    def test_unique_weights_are_shares(self):
        # weight 0.5 => half the seeds (within sampling noise), as long as the seed has room
        out = self.assert_script(harness(["-comru", "100", "-comw", "shock.possess:0.5"], COUNT_SEED,
                                         frequency_finish(), seeds = 3000))
        freq = frequencies(out)
        others = sum(freq[name] for name in ("Steal", "Jump", "Lore", "Blitz", "Tools")) / 5
        self.assertAlmostEqual(freq["Shock"] / others, 0.5, delta = 0.05)
        self.assertAlmostEqual(freq["Possess"] / others, 0.5, delta = 0.05)

    def test_repeat_weights_are_per_character_ratios(self):
        out = self.assert_script(harness(["-comr", "100", "-comw", "shock.possess:0.5,blitz:2"],
                                         COUNT_CHARACTER, frequency_finish(True), seeds = 3000))
        freq = frequencies(out)
        others = sum(freq[name] for name in ("Steal", "Jump", "Lore", "Tools", "Sketch")) / 5
        self.assertAlmostEqual(freq["Shock"] / others, 0.5, delta = 0.08)
        self.assertAlmostEqual(freq["Blitz"] / others, 2.0, delta = 0.25)

    def test_scaling_all_weights_changes_nothing(self):
        # the same rng stream gives the same seed when every weight doubles
        from constants.commands import RANDOM_POSSIBLE_COMMANDS
        names = [name for name in RANDOM_POSSIBLE_COMMANDS if name not in ("Shock", "Possess")]
        skill_key = lambda name: "".join(c for c in name.lower() if c.isalnum())
        doubled = ".".join(skill_key(name) for name in names) + ":2,shock.possess:1"
        for mode in ("-comr", "-comru"):
            with self.subTest(mode):
                outputs = []
                for weights in ("shock.possess:0.5", doubled):
                    out = self.assert_script(harness([mode, "90", "-comw", weights], "print(menus)", seeds = 50))
                    outputs.append(out)
                self.assertEqual(outputs[0], outputs[1])

    def test_empty_slot_weight(self):
        check = "state['empty'] += sum(menu.count(NONE) for menu in menus)"
        out = self.assert_script(harness(["-comr", "100", "-comw", "none:2"], check,
                                         "print(f\"empty={state['empty'] / SEEDS}\")", seeds = 2000))
        # 13 skill slots (Gau has two), each empty with chance 2 / (2 + 20 skills)
        self.assertAlmostEqual(frequencies(out)["empty"], 13 * 2 / 23, delta = 0.12)

    def test_com_random_slots_use_weights(self):
        out = self.assert_script(harness(["-com", "98" * 13, "-comw", "shock.possess:0.5"], COUNT_SEED,
                                         frequency_finish(), seeds = 3000))
        freq = frequencies(out)
        others = sum(freq[name] for name in ("Steal", "Jump", "Lore", "Blitz", "Tools")) / 5
        self.assertAlmostEqual(freq["Shock"] / others, 0.5, delta = 0.05)

    def test_suplex_train_blitz(self):
        # suplex a train guarantees one blitz -- even at weight 0 -- but never a
        # second one on a character, and unique seeds stay unique
        cases = (
            (["-com", "10989898989898989898989898", "-comru", "100"], True),   # explicit blitz
            (["-comru", "100", "-comw", "blitz:0"], True),                       # weight 0: still forced
            (["-comr", "100", "-comw", "blitz:0"], True),
            (["-comr", "100"], False),                                           # repeats: several holders fine
        )
        for flags, one_holder in cases:
            with self.subTest(flags):
                check = BASIC_CHECKS + f"""
holders = [menu.count(name_id["Blitz"]) for menu in menus if name_id["Blitz"] in menu]
assert holders, f"no blitz: {{menus}}"
assert max(holders) == 1, f"blitz twice on one character: {{menus}}"
if {one_holder}:
    assert len(holders) == 1, f"blitz on {{len(holders)}} characters: {{menus}}"
"""
                self.assert_script(harness(flags, check, suplex = True))

if __name__ == "__main__":
    unittest.main()
