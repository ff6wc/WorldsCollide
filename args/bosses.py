from data.bosses import BossLocations


DEFAULT_DRAGON_PROTOCOL = BossLocations.SHUFFLE
DEFAULT_STATUE_PROTOCOL = BossLocations.MIX
def name():
    return "Bosses"

def parse(parser):
    bosses = parser.add_argument_group("Bosses")

    bosses_battles = bosses.add_mutually_exclusive_group()
    bosses_battles.add_argument("-bbs", "--boss-battles-shuffle", action = "store_true",
                        help = "Boss battles shuffled")
    bosses_battles.add_argument("-bbr", "--boss-battles-random", action = "store_true",
                        help = "Boss battles randomized")

    dragons = bosses.add_mutually_exclusive_group()
    dragons.add_argument("-drloc", "--dragon-boss-location", default = DEFAULT_DRAGON_PROTOCOL, type = str.lower, choices = BossLocations.ALL,
                        help = "Decides which locations the eight dragon encounters can be fought")
    dragons.add_argument("-bmbd", "--mix-bosses-dragons", action = "store_true",
                        help = "Shuffle/randomize bosses and dragons together")

    statues = bosses.add_mutually_exclusive_group()
    statues.add_argument("-stloc", "--statue-boss-location", default = DEFAULT_STATUE_PROTOCOL, type = str.lower, choices = BossLocations.ALL,
                        help = "Decides which locations the three statue encounters can be fought")

    bosses.add_argument("-srp3", "--shuffle-random-phunbaba3", action = "store_true",
                        help = "Apply Shuffle/Random to Phunbaba 3 (otherwise he will only appear in Mobliz WOR)")
    bosses.add_argument("-bnds", "--boss-normalize-distort-stats", action = "store_true",
                        help = "Normalize lower boss stats and apply random distortion")
    bosses.add_argument("-be", "--boss-experience", action = "store_true",
                        help = "Boss battles award experience")
    bosses.add_argument("-bnu", "--boss-no-undead", action = "store_true",
                        help = "Undead status removed from bosses")
    bosses.add_argument("-bmkl", "--boss-marshal-keep-lobos", action = "store_true",
                        help = "Don't replace the Marshal's Lobos with randomized enemies")
    bosses.add_argument("-oops", default = None, type = str,
                        help = "Oops, all <boss>! Replace all bosses with the specified boss enemy ID or name.")

def process(args):
    if args.mix_bosses_dragons:
        args.dragon_boss_location = BossLocations.MIX
        args.mix_bosses_dragons = None
    # if neither shuffling or randomizing bosses, and we try to mix the dragons/statues, simply shuffle them instead
    vanilla_locations = not (args.boss_battles_shuffle or args.boss_battles_random)
    if vanilla_locations and args.dragon_boss_location == BossLocations.MIX:
        args.dragon_boss_location = BossLocations.SHUFFLE
    if vanilla_locations and args.statue_boss_location == BossLocations.MIX:
        args.statue_boss_location = BossLocations.SHUFFLE

    if args.oops is not None:
        import data.bosses as bosses
        excluded_final_battle_ids = set(bosses.final_battle_enemy_name.keys())
        excluded_final_battle_ids.remove(298) # Keep Kefka (Final) as valid!

        try:
            # Try to parse as integer ID first
            oops_id = int(args.oops)
            if not (0 <= oops_id <= 383) or oops_id in excluded_final_battle_ids:
                raise ValueError()
            args.oops = oops_id
        except ValueError:
            # If not a valid integer ID, try to parse as normalized name
            def normalize(name):
                return "".join(c.lower() for c in name if c.isalnum())

            name_to_id = {}
            for enemy_dict in [bosses.normal_enemy_name, bosses.dragon_enemy_name, bosses.statue_enemy_name, bosses.final_battle_enemy_name]:
                for eid, name in enemy_dict.items():
                    if eid not in excluded_final_battle_ids:
                        name_to_id[normalize(name)] = eid

            normalized_input = normalize(args.oops)
            if normalized_input in name_to_id:
                args.oops = name_to_id[normalized_input]
            else:
                raise ValueError(
                    f"Invalid boss ID or name: '{args.oops}'. "
                    f"Please check the enemy maps in data/bosses.py for correct names and IDs."
                )

def flags(args):
    flags = ""

    if args.boss_battles_shuffle:
        flags += " -bbs"
    elif args.boss_battles_random:
        flags += " -bbr"

    if args.dragon_boss_location:
        flags += f" -drloc {args.dragon_boss_location}"
    elif args.mix_bosses_dragons:
        flags += f" -drloc {BossLocations.MIX}"

    if args.statue_boss_location:
        flags += f" -stloc {args.statue_boss_location}"

    if args.shuffle_random_phunbaba3:
        flags += " -srp3"
    if args.boss_normalize_distort_stats:
        flags += " -bnds"
    if args.boss_experience:
        flags += " -be"
    if args.boss_no_undead:
        flags += " -bnu"
    if args.boss_marshal_keep_lobos:
        flags += " -bmkl"
    if args.oops is not None:
        flags += f" -oops {args.oops}"

    return flags

def options(args):
    boss_battles = "Original"
    if args.boss_battles_shuffle:
        boss_battles = "Shuffle"
    elif args.boss_battles_random:
        boss_battles = "Random"

    dragon_battles = DEFAULT_DRAGON_PROTOCOL
    if args.dragon_boss_location:
        dragon_battles = args.dragon_boss_location.capitalize()

    statue_battles = DEFAULT_DRAGON_PROTOCOL
    if args.statue_boss_location:
        statue_battles = args.statue_boss_location.capitalize()

    return [
        ("Boss Battles", boss_battles, "boss_battles"),
        ("Dragons", dragon_battles, "dragon_battles"),
        ("Statues", statue_battles, "statue_battles"),
        ("Shuffle/Random Phunbaba 3", args.shuffle_random_phunbaba3, "shuffle_random_phunbaba3"),
        ("Normalize & Distort Stats", args.boss_normalize_distort_stats, "boss_normalize_distort_stats"),
        ("Boss Experience", args.boss_experience, "boss_experience"),
        ("No Undead", args.boss_no_undead, "boss_no_undead"),
        ("Marshal Keep Lobos", args.boss_marshal_keep_lobos, "boss_marshal_keep_lobos"),
        ("Oops All Boss ID", args.oops, "oops"),
    ]

def menu(args):
    entries = options(args)
    for index, entry in enumerate(entries):
        key, value, unique_name = entry

        if key == "Shuffle/Random Phunbaba 3":
            entries[index] = ("Mix Phunbaba 3", value, unique_name)
        elif key == "Normalize & Distort Stats":
            entries[index] = ("Normalize & Distort", value, unique_name)
    return (name(), entries)

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
