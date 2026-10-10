from constants.commands import (COMMAND_OPTIONS, COMMON_COMMANDS, RETIRED_COM_MODES, PROBABILITY_COMMAND_IDS,
                                RANDOM_COMMAND, RANDOM_UNIQUE_COMMAND, NONE_COMMAND, RANDOM_EXCLUDE_COMMANDS,
                                id_name, name_id)

def name():
    return "Commands"

# The three command flag families compose:
# -com     traditional: one 2-digit id per character slot (99 random, 98 random
#          unique, 97 none). Alone it behaves exactly as it always has; combined
#          with the probability flags its explicit picks claim slots first, its
#          99/98 values mark slots for random/unique backfill, and its 97 values
#          hold slots empty.
# -comfr   F.M.I percent chances for Fight/Magic/Item (-comfru: unique skills).
#          A special case of -compr limited to the common commands.
# -compr   dot-separated command ids and matching percent chances
#          (-compru: unique skills). Rolled slots are grouped by likelihood and
#          capped by the character's free slots; anything left unfilled is
#          backfilled from the non--rec-excluded pool.
# Unique means unique across the seed: no skill is dealt twice, by roll or by
# backfill, until every legal skill has been dealt once (data/commands.py
# UniquePool). Fight, Magic, Item and None are never unique.

def parse(parser):
    commands = parser.add_argument_group("Commands")
    commands.add_argument("-com", "--commands", type = str, nargs = "*",
                          help = "Character commands: one 2 digit command id per slot "
                                 f"({len(COMMAND_OPTIONS)} ids; 99 random, 98 random unique, 97 none). "
                                 "Composable with -comfr/-compr: explicit picks claim slots first, "
                                 "99/98 mark random/unique backfill slots, 97 holds a slot empty")
    commands.add_argument("-comfr", "--commands-fr", type = str, default = None, metavar = "F.M.I",
                          help = "Give every character the common commands by chance: "
                                 "'FIGHT.MAGIC.ITEM' percent chances (e.g. -comfr 10.50.90); "
                                 "unfilled slots are backfilled randomly, respecting -rec")
    commands.add_argument("-comfru", "--commands-fru", type = str, default = None, metavar = "F.M.I",
                          help = "Like -comfr, but skills are unique: none is dealt twice until "
                                 "every legal skill has been dealt")
    commands.add_argument("-compr", "--commands-pr", type = str, nargs = 2, default = None,
                          metavar = ("IDS", "PERCENTS"),
                          help = "Give commands by chance: dot-separated command ids and matching "
                                 "percent chances (e.g. -compr 0.1.2.28 50.50.50.100; 97 = a chance "
                                 "at an empty slot); unfilled slots are backfilled randomly, "
                                 "respecting -rec")
    commands.add_argument("-compru", "--commands-pru", type = str, nargs = 2, default = None,
                          metavar = ("IDS", "PERCENTS"),
                          help = "Like -compr, but skills are unique: a skill rolled or drafted for "
                                 "one character is not dealt again until every legal skill has been dealt")
    commands.add_argument("-scc", "--shuffle-commands", action = "store_true", help = "Shuffle selected/randomized commands")
    commands.add_argument("-rec", "--random-exclude-command-ids", type = str, default = None, metavar = "VALUE",
                          help = "Exclude commands from random possibilities, as dot-separated command ids "
                                 "with an arbitrary number of entries (e.g. '-rec 05.07.10')")
    # legacy single-command forms, kept for backward compatibility: each value is folded into the
    # same exclusion list as -rec (and the canonical flag string re-emits them as -rec)
    commands.add_argument("-rec1", "--random-exclude-command1", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")
    commands.add_argument("-rec2", "--random-exclude-command2", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")
    commands.add_argument("-rec3", "--random-exclude-command3", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")
    commands.add_argument("-rec4", "--random-exclude-command4", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")
    commands.add_argument("-rec5", "--random-exclude-command5", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")
    commands.add_argument("-rec6", "--random-exclude-command6", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")

def _process_character_commands(args, tokens):
    # one explicitly selected (or random/none) command id per character slot
    if len(tokens) != 1:
        args.parser.error(f"commands: expected a single value of command ids, got '{' '.join(tokens)}'")

    digits = 2 # number of digits each command id substring is
    value = tokens[0]
    expected_length = digits * len(COMMAND_OPTIONS)
    if not value.isdigit() or len(value) != expected_length:
        args.parser.error(f"commands: '{value}' must be {expected_length} digits "
                          f"({len(COMMAND_OPTIONS)} {digits} digit command ids)")

    args.character_commands = [int(value[index : index + digits]) for index in range(0, len(value), digits)]

    # the ids generation accepts (data/commands.py mod_commands and the
    # composed mod_probability_random_commands use the same rule): the random
    # pool plus Fight anywhere, Leap only in Gau's second slot (index 12).
    # anything else -- Magic, Item, Mimic, Revert, the broken Empty ids --
    # previously slipped through here and crashed generation with a raw
    # ValueError; reject it with a proper message instead.
    from constants.commands import RANDOM_POSSIBLE_COMMANDS
    allowed = set(name_id[name] for name in RANDOM_POSSIBLE_COMMANDS) | {name_id["Fight"]}
    LEAP_INDEX = 12

    for index, command in enumerate(args.character_commands):
        if command == RANDOM_COMMAND:
            args.command_strings.append("Random")
        elif command == RANDOM_UNIQUE_COMMAND:
            args.command_strings.append("Random Unique")
        elif command == NONE_COMMAND:
            args.command_strings.append("None")
        elif command in allowed or (command == name_id["Leap"] and index == LEAP_INDEX):
            args.command_strings.append(id_name[command])
        else:
            args.parser.error(f"commands: '{command:02}' is not a valid command id for {COMMAND_OPTIONS[index]}")

    args.commands = value

def _parse_percent(args, flag, value):
    try:
        percent = int(value)
    except ValueError:
        args.parser.error(f"{flag}: '{value}' is not a valid percent chance")
    if percent < 0 or percent > 100:
        args.parser.error(f"{flag}: percent chance '{percent}' must be between 0 and 100")
    return percent

def _process_probability_random(args, flag, values):
    # dot-separated command ids and matching percent chances,
    # e.g. -compr 0.1.2.28 50.50.50.100. 97 declares a chance at an empty slot.
    ids = []
    for part in values[0].split("."):
        try:
            command = int(part)
        except ValueError:
            args.parser.error(f"{flag}: '{part}' is not a valid command id")
        if command != NONE_COMMAND and command not in PROBABILITY_COMMAND_IDS:
            args.parser.error(f"{flag}: '{command:02}' is not a valid probability command id "
                              f"(one of the {len(PROBABILITY_COMMAND_IDS)} real commands, or 97 for None)")
        if command in ids:
            args.parser.error(f"{flag}: duplicate probability command id '{command:02}'")
        if command in args.random_exclude_commands:
            args.parser.error(f"{flag}: '{id_name[command]}' ({command:02}) is both given a probability "
                              "and excluded by -rec")
        ids.append(command)

    percents = values[1].split(".")
    if len(percents) != len(ids):
        args.parser.error(f"{flag}: {len(ids)} command ids but {len(percents)} percent chances")

    return [(command, _parse_percent(args, flag, percent)) for command, percent in zip(ids, percents)]

def _process_fight_magic_item(args, flag, value):
    # 'FIGHT.MAGIC.ITEM' percent chances for the three common commands
    percents = value.split(".")
    if len(percents) != len(COMMON_COMMANDS):
        args.parser.error(f"{flag}: '{value}' must be {len(COMMON_COMMANDS)} percent chances separated by "
                          f"'.', one each for {', '.join(COMMON_COMMANDS)}")
    return [(name_id[command_name], _parse_percent(args, flag, percent))
            for command_name, percent in zip(COMMON_COMMANDS, percents)]

def _process_excluded_commands(args):
    # merge -rec (dot-separated, arbitrary length) with the legacy -recN single
    # values into one exclusion list. -rec entries come first, then the legacy
    # flags in order; duplicates are preserved (they were legal before and are
    # harmless to the consumers).
    from constants.commands import RANDOM_POSSIBLE_COMMANDS
    excluded = []
    if args.random_exclude_command_ids is not None:
        for part in args.random_exclude_command_ids.split("."):
            try:
                command = int(part)
            except ValueError:
                args.parser.error(f"random-exclude-command-ids: '{part}' is not a valid command id")
            if command not in RANDOM_EXCLUDE_COMMANDS:
                args.parser.error(f"random-exclude-command-ids: '{command:02}' is not an excludable command id")
            if command != NONE_COMMAND:
                excluded.append(command)

    for legacy in (args.random_exclude_command1, args.random_exclude_command2,
                   args.random_exclude_command3, args.random_exclude_command4,
                   args.random_exclude_command5, args.random_exclude_command6):
        if legacy != NONE_COMMAND:
            excluded.append(legacy)

    possible = [name_id[name] for name in RANDOM_POSSIBLE_COMMANDS]
    if excluded and not [command for command in possible if command not in excluded]:
        args.parser.error("random-exclude-command-ids: cannot exclude every "
                          "randomly-selectable command")

    args.random_exclude_commands = excluded

def process(args):
    _process_excluded_commands(args)

    args.character_commands = []
    args.command_strings = []
    args.command_probabilities = []

    # mutually exclusive variants
    if args.commands_fr is not None and args.commands_fru is not None:
        args.parser.error("commands: -comfr and -comfru are incompatible; pick one")
    if args.commands_pr is not None and args.commands_pru is not None:
        args.parser.error("commands: -compr and -compru are incompatible; pick one")

    fr_value = args.commands_fr if args.commands_fr is not None else args.commands_fru
    pr_value = args.commands_pr if args.commands_pr is not None else args.commands_pru

    # the unique/non-unique variants set the leftover-backfill style, so mixing
    # them across the two families would be ambiguous
    fr_unique = args.commands_fru is not None
    pr_unique = args.commands_pru is not None
    if fr_value is not None and pr_value is not None and fr_unique != pr_unique:
        args.parser.error("commands: cannot mix unique and non-unique variants "
                          "(-comfru pairs with -compru, -comfr with -compr)")
    args.commands_unique = fr_unique or pr_unique

    # traditional -com (composable with the probability flags)
    tokens = []
    for value in args.commands or []:
        tokens.extend(value.split())
    if tokens and tokens[0].lower() in RETIRED_COM_MODES:
        mode = tokens[0].lower()
        args.parser.error(f"commands: '-com {mode}' has been split into its own flag; "
                          f"use -com{mode} instead (e.g. -com{mode} {' '.join(tokens[1:])})".rstrip())
    if tokens:
        _process_character_commands(args, tokens)
    else:
        args.commands = None

    # probability declarations: -compr first, then -comfr folded in as the
    # special case for the common commands (an id in both is a conflict)
    if pr_value is not None:
        pr_flag = "-compru" if pr_unique else "-compr"
        args.command_probabilities = _process_probability_random(args, pr_flag, pr_value)
        args.commands_pr_value = (".".join(f"{command:02}" for command, _ in args.command_probabilities)
                                  + " " + ".".join(str(percent) for _, percent in args.command_probabilities))
    else:
        args.commands_pr_value = None

    if fr_value is not None:
        fr_flag = "-comfru" if fr_unique else "-comfr"
        fr_probabilities = _process_fight_magic_item(args, fr_flag, fr_value)
        declared = [command for command, _ in args.command_probabilities]
        for command, percent in fr_probabilities:
            if command in declared:
                args.parser.error(f"commands: '{id_name[command]}' is declared by both {fr_flag} and "
                                  f"{'-compru' if pr_unique else '-compr'}")
            args.command_probabilities.append((command, percent))
        args.commands_fr_value = ".".join(str(percent) for _, percent in fr_probabilities)
    else:
        args.commands_fr_value = None

    args.commands_probability_mode = fr_value is not None or pr_value is not None

    # can a blitz command exist in this configuration? (needed before objectives
    # roll a possible Suplex A Train condition)
    blitz_id = name_id["Blitz"]
    blitz_excluded = blitz_id in args.random_exclude_commands
    blitz_explicit = "Blitz" in args.command_strings
    if args.commands_probability_mode:
        blitz_declared = any(command == blitz_id and percent > 0
                             for command, percent in args.command_probabilities)
        args.blitz_command_possible = blitz_explicit or blitz_declared or not blitz_excluded
    elif args.commands:
        random_exists = "Random" in args.command_strings or "Random Unique" in args.command_strings
        args.blitz_command_possible = blitz_explicit or (random_exists and not blitz_excluded)
    else:
        args.blitz_command_possible = True

def flags(args):
    flags = ""

    if args.commands:
        flags += " -com " + args.commands
    if args.commands_fr_value is not None:
        flags += (" -comfru " if args.commands_fru is not None else " -comfr ") + args.commands_fr_value
    if args.commands_pr_value is not None:
        flags += (" -compru " if args.commands_pru is not None else " -compr ") + args.commands_pr_value

    if args.shuffle_commands:
        flags += " -scc"

    # canonical form: every exclusion (from -rec or the legacy -recN wrappers)
    # is re-emitted as one dot-separated -rec value
    if args.random_exclude_commands:
        flags += " -rec " + ".".join(f"{command:02}" for command in args.random_exclude_commands)

    return flags

def options(args):
    result = []
    if args.commands is None and not args.commands_probability_mode:
        for option in COMMAND_OPTIONS:
            result.append((option, option, option))
    else:
        if args.commands is not None:
            for index, command_string in enumerate(args.command_strings):
                result.append((COMMAND_OPTIONS[index], command_string, COMMAND_OPTIONS[index]))
        if args.commands_probability_mode:
            mode_name = "Custom Unique" if args.commands_unique else "Custom"
            result.append(("Random Mode", mode_name, "commands_probability_mode"))
            for command, percent in args.command_probabilities:
                command_name = "None" if command == NONE_COMMAND else id_name[command]
                result.append((f"{command_name} Chance", f"{percent}%", f"command_probability_{command}"))

    result.append(("", "", ""))
    result.append(("Shuffle Commands", args.shuffle_commands, "shuffle_commands"))

    # one row per exclusion, padded with "None" rows to the fixed six the menu
    # has always shown (extra exclusions beyond six simply add rows)
    exclude_rows = list(args.random_exclude_commands)
    while len(exclude_rows) < 6:
        exclude_rows.append(NONE_COMMAND)
    for i, command in enumerate(exclude_rows, start = 1):
        result.append(("Random Exclude", "None" if command == NONE_COMMAND else id_name[command],
                       f"random_exclude_command{i}"))

    return result

def menu(args):
    return (name(), options(args))

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
