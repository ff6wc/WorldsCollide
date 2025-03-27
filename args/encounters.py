def name():
    return "Encounters"

def parse(parser):
    encounters = parser.add_argument_group("Encounters")

    random = encounters.add_mutually_exclusive_group()
    random.add_argument("-res", "--random-encounters-shuffle", action = "store_true",
                        help = "Random encounters are shuffled")
    random.add_argument("-rer", "--random-encounters-random",
                        default = None, type = int, metavar = "PERCENT", choices = range(101),
                        help = "Random encounters are randomized")
    random.add_argument("-rechu", "--random-encounters-chupon", action = "store_true",
                        help = "All Random Encounters are replaced with Chupon (Coliseum)")
    random.add_argument("-rews", "--random-encounters-world-shuffle", action = "store_true",
                        help = "Random encounters are shuffled by world")
    random.add_argument("-rewr", "--random-encounters-world-random",
                        default = None, type = int, metavar = "PERCENT", choices = range(101),
                        help = "Random encounters are randomized with encounters from the same world")

    fixed = encounters.add_mutually_exclusive_group()
    fixed.add_argument("-fer", "--fixed-encounters-random",
                       default = None, type = int, metavar = "PERCENT", choices = range(101),
                       help = "Fixed encounters are randomized. Lete River, Serpent Trench, Mine Cart, Imperial Camp, ...")
    fixed.add_argument("-fewr", "--fixed-encounters-world-random",
                       default = None, type = int, metavar = "PERCENT", choices = range(101),
                       help = "Fixed encounters are randomized with encounters from the same world. Lete River, Serpent Trench, Mine Cart, Imperial Camp, ...")

    escapable = encounters.add_mutually_exclusive_group()
    escapable.add_argument("-escr", "--encounters-escapable-random",
                           default = None, type = int, metavar = "PERCENT", choices = range(101),
                           help = "Percent of random encounters escapable including with warp or smoke bombs")

def process(args):
    args.random_encounters_original = not args.random_encounters_shuffle and args.random_encounters_random is None \
          and not args.random_encounters_world_shuffle and args.random_encounters_world_random is None
    args.fixed_encounters_original = args.fixed_encounters_random is None and args.fixed_encounters_world_random is None
    args.encounters_escapable_original = args.encounters_escapable_random is None

def flags(args):
    flags = ""

    if args.random_encounters_shuffle:
        flags += " -res"
    elif args.random_encounters_random is not None:
        flags += f" -rer {args.random_encounters_random}"
    elif args.random_encounters_chupon:
        flags += " -rechu"
    elif args.random_encounters_world_shuffle:
        flags += " -rews"
    elif args.fixed_encounters_world_random is not None:
        flags += f" -rewr {args.fixed_encounters_world_random}"

    if args.fixed_encounters_random is not None:
        flags += f" -fer {args.fixed_encounters_random}"
    elif args.fixed_encounters_world_random is not None:
        flags += f" -fewr {args.fixed_encounters_world_random}"


    if args.encounters_escapable_random is not None:
        flags += f" -escr {args.encounters_escapable_random}"

    return flags

def options(args):
    result = []

    random_encounters = "Original"
    if args.random_encounters_shuffle:
        random_encounters = "Shuffle"
    elif args.random_encounters_random is not None:
        random_encounters = "Random"
    elif args.random_encounters_chupon:
        random_encounters = "Chupon"
    elif args.random_encounters_world_shuffle:
        random_encounters = "WShuffle"
    elif args.fixed_encounters_world_random is not None:
        random_encounters = "WRandom"

    result.append(("Random Encounters", random_encounters, "random_encounters"))
    if args.random_encounters_random is not None:
        result.append(("Boss Percent", f"{args.random_encounters_random}%", "random_encounters_random"))
    elif args.fixed_encounters_world_random is not None:
        result.append(("Boss Percent", f"{args.fixed_encounters_world_random}%", "fixed_encounters_world_random"))

    fixed_encounters = "Original"
    if args.fixed_encounters_random is not None:
        fixed_encounters = "Random"
    elif args.fixed_encounters_world_random is not None:
        fixed_encounters = "WRandom"

    result.append(("Fixed Encounters", fixed_encounters, "fixed_encounters"))
    if args.fixed_encounters_random is not None:
        result.append(("Boss Percent", f"{args.fixed_encounters_random}%", "fixed_encounters_random"))

    escapable = "Original"
    if args.encounters_escapable_random is not None:
        escapable = f"{args.encounters_escapable_random}%"

    result.append(("Escapable", escapable, "escapable"))
    return result

def menu(args):
    entries = options(args)
    for index, entry in enumerate(entries):
        key, value, unique_name = entry
        if key == "Random Encounters":
            entries[index] = ("Random", value, unique_name)
        elif key == "Fixed Encounters":
            entries[index] = ("Fixed", value, unique_name)
    return (name(), entries)

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log

