def name():
    return "Starting Gold/Items"

def parse(parser):
    starting_gold_items = parser.add_argument_group("Starting Gold/Items")

    starting_gold_items.add_argument("-gp", "--gold", default = 0, type = int, choices = range(0, 1000000), metavar = "COUNT",
                                     help = "Start game with %(metavar)s gold [0-999999], default %(default)s")

    starting_gold_items.add_argument("-smc", "--start-moogle-charms", default = 0, type = int, choices = range(4), metavar = "COUNT",
                                     help = "Start game with %(metavar)s Moogle Charms. Overrides No Moogle Charms option")
    starting_gold_items.add_argument("-sshoes", "--start-sprint-shoes", default = 0, type = int, choices = range(4), metavar = "COUNT",
                                     help = "Start game with %(metavar)s Sprint Shoes. Overrides No Sprint Shoes option")

    starting_gold_items.add_argument("-sws", "--start-warp-stones", default = 0, type = int, choices = range(11), metavar = "COUNT",
                                     help = "Start game with %(metavar)s Warp Stones")
    starting_gold_items.add_argument("-sfd", "--start-fenix-downs", default = 0, type = int, choices = range(11), metavar = "COUNT",
                                     help = "Start game with %(metavar)s Fenix Downs")
    starting_gold_items.add_argument("-sto", "--start-tools", default = 0, type = int, choices = range(9), metavar = "COUNT",
                                     help = "Start game with %(metavar)s different random tools"),
    starting_gold_items.add_argument("-sj", "--start-junk", default = 0, type = int, choices = range(25), metavar = "COUNT",
                                     help = "Start game with %(metavar)s unique low tier items. Includes weapons, armors, helmets, shields, and relics"),
    starting_gold_items.add_argument("-si", "--start-items", default = None, type = str, help = "Start game with custom items.")

def process(args):
    class Item:
        def __init__(self, _id, count):
            self.id = _id
            self.count = count
    args.start_items_list = []
    if args.start_items != None:
        values = args.start_items.split(".")
        if len(values) % 2 == 1:
            import sys
            args.parser.print_usage()
            print(f"{sys.argv[0]}: error: start-items: Invalid number of entries, they must come in pairs 'item_id.item_count'")
            sys.exit(1)
        for index in range(0, len(values), 2):
            item_id = 0
            try:
                item_id = int(values[index])
            except:
                import sys
                args.parser.print_usage()
                print(f"{sys.argv[0]}: error: start-items: Failed to convert value into an int '{values[index]}'")
                sys.exit(1)
            if item_id < 0 or item_id >= 255:
                import sys
                args.parser.print_usage()
                print(f"{sys.argv[0]}: error: start-items: '{item_id}' is an invalid value for an item id. It must be between 0-254")
                sys.exit(1)

            item_count = 0
            try:
                item_count = int(values[index + 1])
            except:
                import sys
                args.parser.print_usage()
                print(f"{sys.argv[0]}: error: start-items: Failed to convert value into an int '{values[index+1]}'")
                sys.exit(1)
            if item_count <= 0 or item_count > 99:
                import sys
                args.parser.print_usage()
                print(f"{sys.argv[0]}: error: start-items: '{item_count}' is an invalid count for an item. It must be between 1-99")
                sys.exit(1)

            item = Item(item_id, item_count)
            args.start_items_list.append(item)

def flags(args):
    flags = ""

    if args.gold != 0:
        flags += f" -gp {args.gold}"
    if args.start_moogle_charms != 0:
        flags += f" -smc {args.start_moogle_charms}"
    if args.start_sprint_shoes != 0:
        flags += f" -sshoes {args.start_sprint_shoes}"
    if args.start_warp_stones != 0:
        flags += f" -sws {args.start_warp_stones}"
    if args.start_fenix_downs != 0:
        flags += f" -sfd {args.start_fenix_downs}"
    if args.start_tools != 0:
        flags += f" -sto {args.start_tools}"
    if args.start_junk != 0:
        flags += f" -sj {args.start_junk}"
    if args.start_items != None:
        flags += f" -si {args.start_items}"

    return flags

def options(args):
    opts = [
        ("Start Gold", args.gold, "gold"),
        ("Start Moogle Charms", args.start_moogle_charms, "start_moogle_charms"),
        ("Start Sprint Shoes", args.start_sprint_shoes, "start_sprint_shoes"),
        ("Start Warp Stones", args.start_warp_stones, "start_warp_stones"),
        ("Start Fenix Downs", args.start_fenix_downs, "start_fenix_downs"),
        ("Start Tools", args.start_tools, "start_tools"),
    ]
    
    if args.start_junk != 0:
        opts += [
            ("Start Junk", args.start_junk, "start_junk")
        ]

    for item in args.start_items_list:
        from constants.items import id_name
        item_name = id_name[item.id]
        opts += [
            (f"Start {item_name}", item.count, "start_items")
        ]

    return opts

def menu(args):
    return (name(), options(args))

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
