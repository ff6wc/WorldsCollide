def name():
    return "Experience, Magic Points, Gold"

def parse(parser):
    xpmpgp = parser.add_argument_group("Experience, Magic Points, Gold")

    xpmpgp.add_argument("-xpm", "--xp-mult", default = 1, type = int, choices = range(0, 256), metavar = "VALUE",
                        help = "Multiply experience by %(metavar)s [0-255], default %(default)s")
    xpmpgp.add_argument("-mpm", "--mp-mult", default = 1, type = int, choices = range(0, 256), metavar = "VALUE",
                        help = "Multiply magic points by %(metavar)s [0-255], default %(default)s")
    xpmpgp.add_argument("-gpm", "--gp-mult", default = 1, type = int, choices = range(0, 256), metavar = "VALUE",
                        help = "Multiply gold by %(metavar)s [0-255], default %(default)s.")
    xpmpgp.add_argument("-nxppd", "--no-exp-party-divide", action = "store_true",
                        help = "Do not divide experience by number of surviving party members")
    xpmpgp.add_argument("-lc", "--level-cap", default = None, type = int, nargs = "+",
                        metavar = ("LEVEL|MEAN", "WIDTH"),
                        help = "Level cap. One value LEVEL: hard cap, every level from LEVEL on costs the "
                               "most experience the game allows (524,280). Two values MEAN WIDTH: soft cap, "
                               "experience to next level is multiplied by 1 + exp((level - MEAN) / WIDTH), "
                               "doubling from MEAN to MEAN + 1. All values are whole numbers")

def process(args):
    args.level_cap_hard = None
    args.level_cap_mean = None
    args.level_cap_width = None
    if args.level_cap is None:
        return

    if len(args.level_cap) > 2:
        args.parser.error("-lc: expected LEVEL (hard cap) or MEAN WIDTH (soft cap)")

    if len(args.level_cap) == 1:
        level = args.level_cap[0]
        if not 2 <= level <= 98:
            args.parser.error(f"-lc: hard cap level '{level}' must be from 2 to 98")
        args.level_cap_hard = level
    else:
        mean, width = args.level_cap
        if not 1 <= mean <= 99:
            args.parser.error(f"-lc: soft cap mean '{mean}' must be from 1 to 99")
        if not 1 <= width <= 99:
            args.parser.error(f"-lc: soft cap width '{width}' must be from 1 to 99")
        args.level_cap_mean = mean
        args.level_cap_width = width

def flags(args):
    flags = ""

    if args.xp_mult != 1:
        flags += f" -xpm {args.xp_mult}"
    if args.mp_mult != 1:
        flags += f" -mpm {args.mp_mult}"
    if args.gp_mult != 1:
        flags += f" -gpm {args.gp_mult}"

    if args.no_exp_party_divide:
        flags += " -nxppd"

    if args.level_cap_hard is not None:
        flags += f" -lc {args.level_cap_hard}"
    elif args.level_cap_mean is not None:
        flags += f" -lc {args.level_cap_mean} {args.level_cap_width}"

    return flags

def options(args):
    return [
        ("Experience Multiplier", args.xp_mult, "xp_mult"),
        ("Magic Points Multiplier", args.mp_mult, "mp_mult"),
        ("Gold Multiplier", args.gp_mult, "gp_mult"),
        ("No Exp Party Divide", args.no_exp_party_divide, "no_exp_party_divide"),
        ("Level Cap", _level_cap_value(args), "level_cap"),
    ]

def _level_cap_value(args):
    if args.level_cap_hard is not None:
        return args.level_cap_hard
    if args.level_cap_mean is not None:
        return f"Soft {args.level_cap_mean}/{args.level_cap_width}"
    return "None"

def menu(args):
    short_name = "Exp, MP, GP"

    entries = options(args)
    for index in range(3):
        key, value, unique_name = entries[index]

        key = key.replace(" Multiplier", "")
        value = str(value) + 'x'

        entries[index] = (key, value, unique_name)

    return (short_name, entries)

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
