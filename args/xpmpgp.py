import re

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
    level_cap = xpmpgp.add_argument("-lc", "--level-cap", default = None, type = str, nargs = "+",
                        metavar = ("LEVEL|MEAN", "WIDTH"),
                        help = "Level cap. One value LEVEL: hard cap, characters stop gaining experience "
                               "once they reach LEVEL (the status menu shows 0 to the next level, as at 99); "
                               "LEVEL must be at least the starting level (-stl, or -stlr's MAX). Two values "
                               "MEAN WIDTH: soft cap, experience to next level is multiplied by "
                               "1 + 10^((level - MEAN) / WIDTH): double from MEAN to MEAN + 1, and every "
                               "WIDTH levels past that multiply the extra cost by 10. LEVEL and MEAN are "
                               "whole numbers; WIDTH may have one decimal place (e.g. 2.5)")
    level_cap.max_values = 2    # usage reads "-lc LEVEL|MEAN [WIDTH]"; process() rejects a third value

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
        # 3 is the lowest starting level (-stl/-stlr); 99 is no cap at all
        if not level.isdigit() or not 3 <= int(level) <= 98:
            args.parser.error(f"-lc: hard cap level '{level}' must be a whole number from 3 to 98")
        args.level_cap_hard = int(level)
        # nobody may start above a hard cap (the characters group is processed first)
        start = args.start_level_random_max if args.start_level_random else args.start_level
        start_flag = "-stlr" if args.start_level_random else "-stl"
        if start > args.level_cap_hard:
            args.parser.error(f"-lc: hard cap level {level} is below the starting level "
                              f"({start_flag} {start}); raise the cap or lower the starting level")
    else:
        mean, width = args.level_cap
        if not mean.isdigit() or not 1 <= int(mean) <= 99:
            args.parser.error(f"-lc: soft cap mean '{mean}' must be a whole number from 1 to 99")
        # at most one decimal place: keeps the flag string and the flags menu row short
        if not re.fullmatch(r"\d+(\.\d)?|\.\d", width) or not 0.1 <= float(width) <= 99:
            args.parser.error(f"-lc: soft cap width '{width}' must be from 0.1 to 99, "
                              "with at most one decimal place")
        args.level_cap_mean = int(mean)
        args.level_cap_width = float(width)

def _format_width(width):
    # 5.0 -> "5", 2.5 -> "2.5"
    return f"{width:g}"

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
        flags += f" -lc {args.level_cap_mean} {_format_width(args.level_cap_width)}"

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
        return f"Soft {args.level_cap_mean}/{_format_width(args.level_cap_width)}"
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
