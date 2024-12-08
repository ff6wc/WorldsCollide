def name():
    return "Balance Adjustments"

def parse(parser):
    balance_adjustments = parser.add_argument_group("Balance Adjustments")
    balance_adjustments.add_argument("-bqf", "--quick-freeze", action="store_true", help="Freeze effect is shortened")

def process(args):
    pass

def flags(args):
    flags = ""

    if args.quick_freeze:
        flags += " -bqf"

    return flags

def options(args):
    return [
        ("Quick Freeze", args.quick_freeze, "quick_freeze"),
    ]

def menu(args):
    return name(), options(args)

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
