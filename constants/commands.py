id_name = {
    0   : "Fight",
    1   : "Item",
    2   : "Magic",
    3   : "Morph",
    4   : "Revert",
    5   : "Steal",
    6   : "Capture",
    7   : "SwdTech",
    8   : "Throw",
    9   : "Tools",
    10  : "Blitz",
    11  : "Runic",
    12  : "Lore",
    13  : "Sketch",
    14  : "Control",
    15  : "Slot",
    16  : "Rage",
    17  : "Leap",
    18  : "Mimic",
    19  : "Dance",
    20  : "Row",
    21  : "Def",
    22  : "Jump",
    23  : "X Magic",
    24  : "GP Rain",
    25  : "Summon",
    26  : "Health",
    27  : "Shock",
    28  : "Possess",
    29  : "MagiTek",
    30  : "Empty?", # broken? selecting with cursor crashes game
    31  : "Empty",  # cursor can hover over empty but not select
    255 : "None",
}
name_id = {v: k for k, v in id_name.items()}

# random/none arguments (not actual command ids)
RANDOM_COMMAND = 99
RANDOM_UNIQUE_COMMAND = 98
NONE_COMMAND = 97   # none command id is 3 digits in base 10 (255), use a custom 2 digit value for args

# retired -com meta-mode prefixes ('-com fr 10.50.90'), recognized only to
# print a migration error pointing at -comr/-comru/-comw
RETIRED_COM_MODES = ["fr", "fru", "pr", "pru"]

# retired flags (replaced by -comr/-comru/-comw) and their value counts, recognized
# only to print a migration error
RETIRED_COMMAND_FLAGS = {"-comfr": None, "-comfru": None, "-compr": 2, "-compru": 2, "-rec": None}

# -comw: named weights (relative to a standard skill's 1), and the guarantee keyword
WEIGHT_TIERS = {
    "common": 1.0,
    "uncommon": 0.5,
    "rare": 0.25,
    "veryrare": 0.1,
    "legendary": 0.03,
    "never": 0.0,
}
ALWAYS = "always"
# -comw group for every skill no other entry names ('dance:1,other:0')
OTHER = "other"
# -comw group of N skills drawn per seed from the unnamed ones ('random3:1,other:0')
RANDOM_GROUP = "random"

# every character has four command slots in their initialization data ($ed7ca2 - $ed7ca5)
COMMAND_SLOT_COUNT = 4

# commands with a fixed position in the battle menu (fight -> skills -> magic -> item),
# in the order their percent chances are given to the full random modes
COMMON_COMMANDS = ["Fight", "Magic", "Item"]

COMMAND_OPTIONS = ["Morph", "Steal", "SwdTech", "Throw", "Tools", "Blitz", "Runic", "Lore", "Sketch", "Slot", "Dance", "Rage", "Leap"]
EXCLUDE_COMMANDS = ["Item", "Magic", "Revert", "Leap", "Mimic", "Row", "Def", "Summon", "Empty", "Empty?", "None"]

RANDOM_POSSIBLE_COMMANDS = [option for option in sorted(name_id.keys()) if option not in EXCLUDE_COMMANDS and option != "Fight"]
RANDOM_EXCLUDE_COMMANDS = [NONE_COMMAND] + [name_id[option] for option in RANDOM_POSSIBLE_COMMANDS]
