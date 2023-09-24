ITEM_COUNT = 256
EMPTY = 0xff

BREAKABLE_RODS = range(53, 59)
ELEMENTAL_SHIELDS = range(96, 99)
DIRKS = range(0, 10)
SWORDS = range(10, 29)
LANCES = range(29, 37)
KNIVES = range(37, 43)
KATANAS = range(43, 51)
RODS = range(51, 61)
BRUSHES = range(61, 65)
STARS = range(65, 68)
SPECIAL = range(68, 77)
GAMBLER = range(77, 83)
CLAWS = range(83, 90)
SHIELDS = range(90, 105)
HELMETS = range(105, 132)
ARMORS = range(132, 163)
TOOLS = range(163, 171)
SKEANS = range(171, 176)
RELICS = range(176, 231)


id_name = {
    0   : "Dirk",
    1   : "MithrilKnife",
    2   : "Guardian",
    3   : "Air Lancet",
    4   : "ThiefKnife",
    5   : "Assassin",
    6   : "Man Eater",
    7   : "SwordBreaker",
    8   : "Graedus",
    9   : "ValiantKnife",
    10  : "MithrilBlade",
    11  : "RegalCutlass",
    12  : "Rune Edge",
    13  : "Flame Sabre",
    14  : "Blizzard",
    15  : "ThunderBlade",
    16  : "Epee",
    17  : "Break Blade",
    18  : "Drainer",
    19  : "Enhancer",
    20  : "Crystal",
    21  : "Falchion",
    22  : "Soul Sabre",
    23  : "Ogre Nix",
    24  : "Excalibur",
    25  : "Scimitar",
    26  : "Illumina",
    27  : "Ragnarok",
    28  : "Atma Weapon",
    29  : "Mithril Pike",
    30  : "Trident",
    31  : "Stout Spear",
    32  : "Partisan",
    33  : "Pearl Lance",
    34  : "Gold Lance",
    35  : "Aura Lance",
    36  : "Imp Halberd",
    37  : "Imperial",
    38  : "Kodachi",
    39  : "Blossom",
    40  : "Hardened",
    41  : "Striker",
    42  : "Stunner",
    43  : "Ashura",
    44  : "Kotetsu",
    45  : "Forged",
    46  : "Tempest",
    47  : "Murasame",
    48  : "Aura",
    49  : "Strato",
    50  : "Sky Render",
    51  : "Heal Rod",
    52  : "Mithril Rod",
    53  : "Fire Rod",
    54  : "Ice Rod",
    55  : "Thunder Rod",
    56  : "Poison Rod",
    57  : "Pearl Rod",
    58  : "Gravity Rod",
    59  : "Punisher",
    60  : "Magus Rod",
    61  : "Chocobo Brsh",
    62  : "DaVinci Brsh",
    63  : "Magical Brsh",
    64  : "Rainbow Brsh",
    65  : "Shuriken",
    66  : "Ninja Star",
    67  : "Tack Star",
    68  : "Flail",
    69  : "Full Moon",
    70  : "Morning Star",
    71  : "Boomerang",
    72  : "Rising Sun",
    73  : "Hawk Eye",
    74  : "Bone Club",
    75  : "Sniper",
    76  : "Wing Edge",
    77  : "Cards",
    78  : "Darts",
    79  : "Doom Darts",
    80  : "Trump",
    81  : "Dice",
    82  : "Fixed Dice",
    83  : "MetalKnuckle",
    84  : "Mithril Claw",
    85  : "Kaiser",
    86  : "Poison Claw",
    87  : "Fire Knuckle",
    88  : "Dragon Claw",
    89  : "Tiger Fangs",
    90  : "Buckler",
    91  : "Heavy Shld",
    92  : "Mithril Shld",
    93  : "Gold Shld",
    94  : "Aegis Shld",
    95  : "Diamond Shld",
    96  : "Flame Shld",
    97  : "Ice Shld",
    98  : "Thunder Shld",
    99  : "Crystal Shld",
    100 : "Genji Shld",
    101 : "TortoiseShld",
    102 : "Cursed Shld",
    103 : "Paladin Shld",
    104 : "Force Shld",
    105 : "Leather Hat",
    106 : "Hair Band",
    107 : "Plumed Hat",
    108 : "Beret",
    109 : "Magus Hat",
    110 : "Bandana",
    111 : "Iron Helmet",
    112 : "Coronet",
    113 : "Bard's Hat",
    114 : "Green Beret",
    115 : "Head Band",
    116 : "Mithril Helm",
    117 : "Tiara",
    118 : "Gold Helmet",
    119 : "Tiger Mask",
    120 : "Red Cap",
    121 : "Mystery Veil",
    122 : "Circlet",
    123 : "Regal Crown",
    124 : "Diamond Helm",
    125 : "Dark Hood",
    126 : "Crystal Helm",
    127 : "Oath Veil",
    128 : "Cat Hood",
    129 : "Genji Helmet",
    130 : "Thornlet",
    131 : "Titanium",
    132 : "LeatherArmor",
    133 : "Cotton Robe",
    134 : "Kung Fu Suit",
    135 : "Iron Armor",
    136 : "Silk Robe",
    137 : "Mithril Vest",
    138 : "Ninja Gear",
    139 : "White Dress",
    140 : "Mithril Mail",
    141 : "Gaia Gear",
    142 : "Mirage Vest",
    143 : "Gold Armor",
    144 : "Power Sash",
    145 : "Light Robe",
    146 : "Diamond Vest",
    147 : "Red Jacket",
    148 : "Force Armor",
    149 : "DiamondArmor",
    150 : "Dark Gear",
    151 : "Tao Robe",
    152 : "Crystal Mail",
    153 : "Czarina Gown",
    154 : "Genji Armor",
    155 : "Imp's Armor",
    156 : "Minerva",
    157 : "Tabby Suit",
    158 : "Chocobo Suit",
    159 : "Moogle Suit",
    160 : "Nutkin Suit",
    161 : "BehemothSuit",
    162 : "Snow Muffler",
    163 : "NoiseBlaster",
    164 : "Bio Blaster",
    165 : "Flash",
    166 : "Chain Saw",
    167 : "Debilitator",
    168 : "Drill",
    169 : "Air Anchor",
    170 : "AutoCrossbow",
    171 : "Fire Skean",
    172 : "Water Edge",
    173 : "Bolt Edge",
    174 : "Inviz Edge",
    175 : "Shadow Edge",
    176 : "Goggles",
    177 : "Star Pendant",
    178 : "Peace Ring",
    179 : "Amulet",
    180 : "White Cape",
    181 : "Jewel Ring",
    182 : "Fairy Ring",
    183 : "Barrier Ring",
    184 : "MithrilGlove",
    185 : "Guard Ring",
    186 : "RunningShoes",
    187 : "Wall Ring",
    188 : "Cherub Down",
    189 : "Cure Ring",
    190 : "True Knight",
    191 : "DragoonBoots",
    192 : "Zephyr Cape",
    193 : "Czarina Ring",
    194 : "Cursed Ring",
    195 : "Earrings",
    196 : "Atlas Armlet",
    197 : "Blizzard Orb",
    198 : "Rage Ring",
    199 : "Sneak Ring",
    200 : "Pod Bracelet",
    201 : "Hero Ring",
    202 : "Ribbon",
    203 : "Muscle Belt",
    204 : "Crystal Orb",
    205 : "Gold Hairpin",
    206 : "Economizer",
    207 : "Thief Glove",
    208 : "Gauntlet",
    209 : "Genji Glove",
    210 : "Hyper Wrist",
    211 : "Offering",
    212 : "Beads",
    213 : "Black Belt",
    214 : "Coin Toss",
    215 : "FakeMustache",
    216 : "Gem Box",
    217 : "Dragon Horn",
    218 : "Merit Award",
    219 : "Memento Ring",
    220 : "Safety Bit",
    221 : "Relic Ring",
    222 : "Moogle Charm",
    223 : "Charm Bangle",
    224 : "Marvel Shoes",
    225 : "Back Guard",
    226 : "Gale Hairpin",
    227 : "Sniper Sight",
    228 : "Exp. Egg",
    229 : "Tintinabar",
    230 : "Sprint Shoes",
    231 : "Rename Card",
    232 : "Tonic",
    233 : "Potion",
    234 : "X-Potion",
    235 : "Tincture",
    236 : "Ether",
    237 : "X-Ether",
    238 : "Elixir",
    239 : "Megalixir",
    240 : "Fenix Down",
    241 : "Revivify",
    242 : "Antidote",
    243 : "Eyedrop",
    244 : "Soft",
    245 : "Remedy",
    246 : "Sleeping Bag",
    247 : "Tent",
    248 : "Green Cherry",
    249 : "Magicite",
    250 : "Super Ball",
    251 : "Echo Screen",
    252 : "Smoke Bomb",
    253 : "Warp Stone",
    254 : "Dried Meat",
    255 : "Empty",
}
name_id = {v: k for k, v in id_name.items()}

good_items = [
    "ValiantKnife",
    "Illumina",
    "Ragnarok",
    "Atma Weapon",
    "Pearl Lance",
    "Aura Lance",
    "Magus Rod",
    "Fixed Dice",
    "Aegis Shld",
    "Flame Shld",
    "Ice Shld",
    "Thunder Shld",
    "Genji Shld",
    "Paladin Shld",
    "Force Shld",
    "Red Cap",
    "Cat Hood",
    "Genji Helmet",
    "Force Armor",
    "Genji Armor",
    "Minerva",
    "BehemothSuit",
    "Snow Muffler",
    "Economizer",
    "Genji Glove",
    "Offering",
    "Gem Box",
    "Dragon Horn",
    "Marvel Shoes",
    "Exp. Egg",
]

better_items = [
    "ValiantKnife",
    "Illumina",
    "Ragnarok",
    "Atma Weapon",
    "Fixed Dice",
    "Flame Shld",
    "Ice Shld",
    "Thunder Shld",
    "Paladin Shld",
    "Minerva",
    "Genji Glove",
    "Offering",
    "Exp. Egg",
]

