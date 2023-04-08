def name():
    return "Chests"

def parse(parser):
    chests = parser.add_argument_group("Chests")

    chests_contents = chests.add_mutually_exclusive_group()
    chests_contents.add_argument("-ccsr", "--chest-contents-shuffle-random", default = None, type = int,
                                 metavar = "PERCENT", choices = range(101),
                                 help = "Chest contents shuffled and given percent randomized")
    chests_contents.add_argument("-ccrt", "--chest-contents-random-tiered", action = "store_true",
                                 help = "Chest contents randomized by tier")
    chests_contents.add_argument("-ccrs", "--chest-contents-random-scaled", action = "store_true",
                                 help = "Chest contents randomized by tier. Probability of higher tiers begins low and increases as more chests are opened")
    chests_contents.add_argument("-cce", "--chest-contents-empty", action = "store_true",
                                 help = "Chest contents empty")
    chests_contents.add_argument("-cam", "--chest-all-monsters", default = None, type = int,
                                 metavar = "PERCENT", choices = range(101),
                                 help="Chest contents all monster-in-a-boxes and given percent bosses")

    chests.add_argument("-cms", "--chest-monsters-shuffle", action = "store_true",
                        help = "Monsters-in-a-box shuffled but locations unchanged")

def process(args):
    if args.chest_contents_shuffle_random is not None:
        args.chest_contents_shuffle_random_percent = args.chest_contents_shuffle_random
        args.chest_contents_shuffle_random = True
    if args.chest_all_monsters is not None:
        args.chest_all_monsters_boss_percent = args.chest_all_monsters
        args.chest_all_monsters = True
        args.chest_mosters_shuffle = False  # Chest_all_monsters supercedes chest_monsters_shuffle

def flags(args):
    flags = ""

    if args.chest_contents_shuffle_random:
        flags += f" -ccsr {args.chest_contents_shuffle_random_percent}"
    elif args.chest_contents_random_tiered:
        flags += " -ccrt"
    elif args.chest_contents_random_scaled:
        flags += " -ccrs"
    elif args.chest_contents_empty:
        flags += " -cce"
    elif args.chest_all_monsters:
        flags += f" -cam {args.chest_all_monsters_boss_percent}"

    if args.chest_monsters_shuffle:
        flags += " -cms"

    return flags

def options(args):
    result = []

    contents_value = "Original"
    if args.chest_contents_shuffle_random:
        contents_value = "Shuffle + Random"
    elif args.chest_contents_random_tiered:
        contents_value = "Random Tiered"
    elif args.chest_contents_random_scaled:
        contents_value = "Random Scaled"
    elif args.chest_contents_empty:
        contents_value = "Empty"
    elif args.chest_all_monsters:
        contents_value = "All MiaB"

    result.append(("Contents", contents_value))
    if args.chest_contents_shuffle_random:
        result.append(("Random Percent", f"{args.chest_contents_shuffle_random_percent}%"))
    elif args.chest_all_monsters:
        result.append(("Boss Percent", f"{args.chest_all_monsters_boss_percent}%"))

    if not args.chest_all_monsters:
        result.append(("MIAB Shuffled", args.chest_monsters_shuffle))

    return result

def menu(args):
    entries = options(args)

    if args.chest_contents_shuffle_random:
        entries[0] = ("Shuffle + Random", entries[1][1]) # put percent on same line
        del entries[1]                                   # delete random percent line
    else:
        entries[0] = (entries[0][1], "")
    
    return (name(), entries)

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
