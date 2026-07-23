def name():
    return "Starting Party"

def parse(parser):
    starting_party = parser.add_argument_group("Starting Party")

    from data.characters import Characters
    character_options = [name.lower() for name in Characters.DEFAULT_NAME]
    character_options.append("random")
    character_options.append("randomngu")

    starting_party.add_argument("-sc1", "--start-char1", default = "", type = str.lower, choices = character_options,
                                help = "Starting party member")
    starting_party.add_argument("-sc2", "--start-char2", default = "", type = str.lower, choices = character_options,
                                help = "Starting party member")
    starting_party.add_argument("-sc3", "--start-char3", default = "", type = str.lower, choices = character_options,
                                help = "Starting party member")
    starting_party.add_argument("-sc4", "--start-char4", default = "", type = str.lower, choices = character_options,
                                help = "Starting party member")

_RANDOM_TOKENS = ("random", "randomngu")

def process(args):
    # canonical required-character list (-rc/--require-characters): de-duplicate concrete names
    # but keep each random/randomngu token, since each is a distinct slot.
    required = []
    required_concrete = set()
    for char in (getattr(args, "require_characters", None) or []):
        if char in _RANDOM_TOKENS:
            required.append(char)
        elif char not in required_concrete:
            required_concrete.add(char)
            required.append(char)
    args.require_characters = required

    # explicit starting characters from the -scN flags (tokens preserved)
    explicit = [c for c in (args.start_char1, args.start_char2, args.start_char3, args.start_char4) if c]

    # ensure no duplicate concrete starting characters (random/randomngu may repeat)
    start_chars_found = set()
    for char in explicit:
        if char not in _RANDOM_TOKENS and char in start_chars_found:
            args.parser.error(f"starting-party: duplicate starting character '{char}'")
        start_chars_found.add(char)

    # required characters are compatible with the starting characters: a required character that is
    # not already a starting character occupies an additional starting slot, and the combined party
    # must fit in the four slots.
    combined = list(explicit)
    for char in required:
        if char in _RANDOM_TOKENS or char not in combined:
            combined.append(char)
    if len(combined) > 4:
        args.parser.error("starting-party: at most 4 starting + required characters are allowed")

    args._starting_party_explicit = explicit
    # provisional starting party; resolve_required_characters() (called once the rng is seeded)
    # replaces any random required characters with concrete choices and finalizes the list.
    args.start_chars = combined if combined else ["random"]

def resolve_required_characters(args):
    # Resolve the required characters (-rc) into concrete character ids, choosing random /
    # randomngu tokens now that the rng is seeded.  Each random choice excludes every named
    # (concrete) starting or required character and any previously chosen random, regardless of
    # order; randomngu additionally excludes Gogo and Umaro.  Also computes the party-select
    # "unmovable" bitmask and finalizes the starting party.
    #
    # Must run after seeding and before any event code is generated (the unmovable mask and the
    # required-character party placement are baked into the field event code) -- see args/arguments.py.
    from data.characters import Characters
    name_to_id = {name.lower(): char_id for char_id, name in enumerate(Characters.DEFAULT_NAME)}
    gogo_umaro = (name_to_id["gogo"], name_to_id["umaro"])

    explicit = getattr(args, "_starting_party_explicit", [])
    required = getattr(args, "require_characters", None) or []

    # base exclusion: every named (concrete) starting or required character
    taken = set()
    for char in explicit + required:
        if char not in _RANDOM_TOKENS:
            taken.add(name_to_id[char])

    import random
    required_ids = []
    for token in required:
        if token == "random":
            char_id = _choose_random_character(taken)
        elif token == "randomngu":
            char_id = _choose_random_character(taken, exclude = gogo_umaro)
        else:
            char_id = name_to_id[token]
        if char_id not in required_ids:
            required_ids.append(char_id)
        taken.add(char_id)

    args.required_character_ids = required_ids
    args.required_character_unmovable = sum(1 << char_id for char_id in required_ids)

    # finalize the starting party: explicit characters (random tokens preserved, resolved later
    # when the party is created) followed by the resolved required characters
    required_names = [Characters.DEFAULT_NAME[char_id].lower() for char_id in required_ids]
    start_chars = list(explicit)
    for char_name in required_names:
        if char_name not in start_chars:
            start_chars.append(char_name)
    args.start_chars = start_chars if start_chars else ["random"]

def _choose_random_character(taken, exclude = ()):
    from data.characters import Characters
    import random
    candidates = [char_id for char_id in range(Characters.CHARACTER_COUNT)
                  if char_id not in taken and char_id not in exclude]
    return random.choice(candidates)


def flags(args):
    flags = ""

    if args.start_char1:
        flags += f" -sc1 {args.start_char1}"
    if args.start_char2:
        flags += f" -sc2 {args.start_char2}"
    if args.start_char3:
        flags += f" -sc3 {args.start_char3}"
    if args.start_char4:
        flags += f" -sc4 {args.start_char4}"

    return flags

def options(args):
    result = []
    start_chars = [args.start_char1, args.start_char2, args.start_char3, args.start_char4]
    for i, start_char in enumerate(start_chars):
        value = "None"
        if start_char == "randomngu":
            value = "Random (No Gogo/Umaro)"
        elif start_char:
            value = start_char.capitalize()

        result.append((f"Start Character {i+1}", value, f"start_char{i+1}"))
    return result

def menu(args):
    entries = options(args)
    for index, entry in enumerate(entries):
        entries[index] = (entry[1], "", entry[2])
    return (name(), entries)

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
