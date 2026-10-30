"""How often each command appears, for a set of command flags.

usage: python3 tools/command_odds.py [-n SEEDS] [--suplex] -- COMMAND FLAGS...
  e.g. python3 tools/command_odds.py -- -comru 90 -comw shock.possess:0.5

Runs the real command assignment (data/commands.py) SEEDS times on stand-in
characters -- no rom needed -- and prints, per command, the share of seeds that
have it on at least one character and the share of characters that have it.
--suplex switches on a Suplex A Train objective (Blitz guaranteed)."""
import collections
import os
import random
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    argv = sys.argv[1:]
    if "--" not in argv:
        sys.exit(__doc__)
    split = argv.index("--")
    options, flags = argv[:split], argv[split + 1:]
    seeds = int(options[options.index("-n") + 1]) if "-n" in options else 10000

    sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    sys.argv = ["wc.py", "-i", "rom.smc"] + flags
    sys.modules["objectives"] = types.ModuleType("objectives")
    sys.modules["objectives"].suplex_train_condition_exists = "--suplex" in options
    import args
    from constants.commands import id_name
    from data.commands import Commands

    class StandIn:
        def __init__(self):
            self.commands = [0, 0, 0, 0]

    picks = list(args.character_commands)
    random.seed(0)
    in_seed, on_character = collections.Counter(), collections.Counter()
    characters = 0
    for _ in range(seeds):
        args.character_commands[:] = picks
        args.group_modules["commands"].resolve_random_weights(args)
        stand_ins = [StandIn() for _ in range(0x20)]
        commands = Commands(stand_ins)
        if args.commands_probability_mode:
            commands.mod_probability_random_commands()
            menus = [stand_ins[index].commands for index in commands.full_random_characters()]
        elif args.commands:
            commands.mod_commands()
            menus = [[stand_ins[index].commands[1]] for index in range(11)] + [stand_ins[11].commands[:2]]
        else:
            sys.exit("no command randomization in these flags")
        characters += len(menus)
        in_seed.update({command for menu in menus for command in menu})
        on_character.update(command for menu in menus for command in set(menu))

    print(f"{'command':10s} {'seeds':>7s} {'characters':>11s}   ({seeds} seeds)")
    for command, count in sorted(in_seed.items(), key = lambda item: (-item[1], id_name[item[0]])):
        print(f"{id_name[command]:10s} {100 * count / seeds:6.1f}% {100 * on_character[command] / characters:10.1f}%")


if __name__ == "__main__":
    main()
