def name():
    return "Characters"

def parse(parser):
    characters = parser.add_argument_group("Characters")

    characters.add_argument("-sal", "--start-average-level", action = "store_true",
                            help = "Recruited characters start at the average character level")
    start_level = characters.add_mutually_exclusive_group()
    start_level.add_argument("-stl", "--start-level", default = 3, type = int, choices = range(3, 100), metavar = "COUNT",
                            help = "Start game at level %(metavar)s.")
    start_level.add_argument("-stlr", "--start-level-random", default = None, type = int, nargs = 2,
                            metavar = ("MIN", "MAX"), choices = range(3, 100),
                            help = "Each character starts at a random level between MIN and MAX (inclusive). "
                                   "With -sal, recruits are still raised to the party's average level if it is higher")
    characters.add_argument("-sn", "--start-naked", action = "store_true",
                            help = "Recruited characters start with no equipment")
    characters.add_argument("-eu", "--equipable-umaro", action = "store_true",
                            help = "Umaro can access equipment menu")
    characters.add_argument("-csrp", "--character-stat-random-percent", default = [100, 100], type = int,
                            nargs = 2, metavar = ("MIN", "MAX"), choices = range(201),
                            help = "Each character stat set to random percent of original within given range ")

def process(args):
    args._process_min_max("character_stat_random_percent")
    args._process_min_max("start_level_random")

def flags(args):
    flags = ""

    if args.start_average_level:
        flags += " -sal"
    if args.start_level != 3:
        flags += f" -stl {args.start_level}"
    if args.start_level_random:
        flags += f" -stlr {args.start_level_random_min} {args.start_level_random_max}"
    if args.start_naked:
        flags += " -sn"
    if args.equipable_umaro:
        flags += " -eu"
    if args.character_stat_random_percent_min != 100 or args.character_stat_random_percent_max != 100:
        flags += f" -csrp {args.character_stat_random_percent_min} {args.character_stat_random_percent_max}"

    return flags

def options(args):
    character_stats = f"{args.character_stat_random_percent_min}-{args.character_stat_random_percent_max}%"
    start_level = args.start_level
    if args.start_level_random:
        start_level = f"Random {args.start_level_random_min}-{args.start_level_random_max}"

    return [
        ("Start Average Level", args.start_average_level, "start_average_level"),
        ("Start Level", start_level, "start_level"),
        ("Start Naked", args.start_naked, "start_naked"),
        ("Equipable Umaro", args.equipable_umaro, "equipable_umaro"),
        ("Character Stats", character_stats, "character_stats"),
    ]

def menu(args):
    entries = options(args)
    for index, entry in enumerate(entries):
        key, value, unique_name = entry
        if key == "Character Stats":
            entries[index] = ("Stats", entry[1], unique_name)
    return (name(), entries)

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
