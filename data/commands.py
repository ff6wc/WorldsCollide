from constants.commands import *
import math
import random
import args

def weighted_choice(candidates, weights):
    # one candidate, chance proportional to weight. equal weights draw exactly as
    # random.choice did, so seeds without -comw weights are unchanged
    candidate_weights = [weights.get(command, 1.0) for command in candidates]
    if len(set(candidate_weights)) <= 1:
        return random.choice(candidates)
    return random.choices(candidates, weights = candidate_weights)[0]

def inclusion_probabilities(candidates, weights, count):
    # each candidate's chance of being among `count` distinct draws: min(1, c * weight),
    # with c set so the chances sum to count (the heaviest saturate at 1 first)
    chances = {}
    fixed = set()
    while True:
        free = [command for command in candidates if command not in fixed]
        total = sum(weights[command] for command in free)
        scale = (count - len(fixed)) / total if total else 0.0
        saturated = [command for command in free if scale * weights[command] >= 1]
        if not saturated:
            for command in free:
                chances[command] = scale * weights[command]
            for command in fixed:
                chances[command] = 1.0
            return chances
        fixed.update(saturated)

def share_sample(candidates, weights, count):
    # `count` distinct candidates, each included with chance proportional to its
    # weight (capped at certainty): systematic sampling over a random order, whose
    # inclusion chances are exact. drawing one at a time by weight would not be:
    # the likelier skills run out mid-draw and the rare ones get the late picks
    candidates = [command for command in candidates if weights[command] > 0]
    count = min(count, len(candidates))
    if count <= 0:
        return []
    chances = inclusion_probabilities(candidates, weights, count)
    order = list(candidates)
    random.shuffle(order)
    start = random.random()
    chosen = []
    total = 0.0
    for command in order:
        low, total = total, total + chances[command]
        if math.floor(total - start + 1e-9) > math.floor(low - start + 1e-9):
            chosen.append(command)
    # float rounding can leave the sum a hair off count: settle on exactly count
    rest = sorted((command for command in order if command not in chosen),
                  key = lambda command: -chances[command])
    while len(chosen) < count:
        chosen.append(rest.pop(0))
    while len(chosen) > count:
        chosen.remove(min(chosen, key = lambda command: chances[command]))
    return chosen

class Commands:
    def __init__(self, characters):
        self.characters = characters

    def mod_moogle_commands(self, command_list):
        from data.characters import Characters

        # Give the Moogles for Moogle Defense randomized commands
        # Copy the list minus any exclusions
        possible_moogle_commands = command_list.copy()
        # randomize commands for Moogles during Moogle Defense from the non-excluded set
        # Remove Morph to ensure only 1 character gets Morph
        # Remove Rage to avoid any issues with Randomized Atma weapon
        # Remove X-Magic as they won't have any Magic
        # Remove Blitz, SwdTech, Dance, and Lore because they won't have abilities within unless a party member does
        moogle_exclusions = [name_id["Morph"], name_id["Rage"], name_id["X Magic"], name_id["Blitz"], name_id["SwdTech"], name_id["Lore"], name_id["Dance"]]
        for exclude in moogle_exclusions:
            try:
                possible_moogle_commands.remove(exclude)
            except ValueError:
                pass
        if len(possible_moogle_commands) > 0:
            for index in range(Characters.FIRST_MOOGLE, Characters.LAST_MOOGLE + 1):
                self.characters[index].commands[1] = random.choice(possible_moogle_commands)

    def mod_commands(self):
        weights = args.command_weights_map
        command_set = set(name_id[name] for name in RANDOM_POSSIBLE_COMMANDS)
        command_list = list(command_set)

        allowed_commands = command_set | set([name_id["Fight"], RANDOM_COMMAND, RANDOM_UNIQUE_COMMAND, NONE_COMMAND])

        # if morph was explicitly selected remove from available command list
        morph_id = name_id["Morph"]
        for command in args.character_commands:
            if command == morph_id:
                command_list.remove(morph_id)

        # skills of weight 0 (-comw NAME:0, legacy -recN) are never drawn
        for exclude_command in args.random_exclude_commands:
            try:
                command_set.discard(exclude_command)
                command_list.remove(exclude_command)
            except ValueError:
                pass

        from data.characters import Characters
        self.mod_moogle_commands(command_list)

        # if suplex a train condition exists, guarantee blitz
        import objectives
        blitz_id = name_id["Blitz"]
        if objectives.suplex_train_condition_exists and blitz_id not in args.character_commands:
            # try to replace a random "Random" or "Random Unique" command with Blitz (even if blitz in excluded commands)
            possible_indices = []
            for index, command in enumerate(args.character_commands):
                if command == RANDOM_COMMAND or command == RANDOM_UNIQUE_COMMAND:
                    possible_indices.append(index)

            if not possible_indices:
                # suplex a train explicitly picked and all commands explicitly picked (but none are blitz)
                # force a random command to be blitz instead
                possible_indices = list(range(len(args.character_commands)))

            random_index = random.choice(possible_indices)
            args.character_commands[random_index] = blitz_id
            command_set.discard(blitz_id)

        # -comw always: a skill nobody was given takes a random/random unique slot
        for command in args.command_always:
            possible_indices = [index for index, value in enumerate(args.character_commands)
                                if value in (RANDOM_COMMAND, RANDOM_UNIQUE_COMMAND)]
            if command in args.character_commands or not possible_indices:
                continue
            args.character_commands[random.choice(possible_indices)] = command
            command_set.discard(command)
            if command == morph_id and morph_id in command_list:
                command_list.remove(morph_id)

        # -comw none: a random slot is left empty with the empty slot's share of the weight
        for index, command in enumerate(args.character_commands):
            if command in (RANDOM_COMMAND, RANDOM_UNIQUE_COMMAND) and self.empty_slot(command_list):
                args.character_commands[index] = NONE_COMMAND

        for index, command in enumerate(args.character_commands):
            if command not in allowed_commands and (index != 0 or command != name_id["Morph"]) and (index != 12 or command != name_id["Leap"]):
                raise ValueError(f"Invalid character command {command}")
            elif command == RANDOM_COMMAND:
                args.character_commands[index] = weighted_choice(command_list, weights)
                if args.character_commands[index] == morph_id:
                    command_list.remove(morph_id) # only one character gets morph
            elif command == NONE_COMMAND:
                args.character_commands[index] = name_id["None"]

            command_set.discard(args.character_commands[index])

        # random unique slots: with uneven weights the slots take their skills together,
        # by weight share (equal weights draw one at a time, exactly as before)
        unique_indices = [index for index, command in enumerate(args.character_commands)
                          if command == RANDOM_UNIQUE_COMMAND]
        if unique_indices and len(set(weights[command] for command in command_set)) > 1:
            picks = share_sample(sorted(command_set), weights, len(unique_indices))
            random.shuffle(picks)
            for index, command in zip(unique_indices, picks):
                args.character_commands[index] = command
                command_set.discard(command)

        for index, command in enumerate(args.character_commands):
            if command == RANDOM_UNIQUE_COMMAND:
                args.character_commands[index] = random.choice(tuple(command_set))
                command_set.discard(args.character_commands[index])

        # apply the commands to the characters
        for index in range(len(args.character_commands[ : -2])):
            self.characters[index].commands[1] = args.character_commands[index]
        self.characters[Characters.GAU].commands[0] = args.character_commands[-2] # rage
        self.characters[Characters.GAU].commands[1] = args.character_commands[-1] # leap

    def full_random_characters(self):
        # the characters the -com flag controls: terra through mog, plus gau
        from data.characters import Characters
        return list(range(Characters.GAU + 1))

    def random_command_list(self):
        # commands random draws may deal: every randomizable skill of weight above 0
        command_list = [name_id[name] for name in RANDOM_POSSIBLE_COMMANDS]
        for exclude_command in args.random_exclude_commands:
            try:
                command_list.remove(exclude_command)
            except ValueError:
                pass
        return command_list

    def empty_slot(self, legal):
        # -comw none: a drawn slot stays empty with the empty slot's share of the weight
        none_weight = args.command_weights_map[NONE_COMMAND]
        if none_weight <= 0:
            return False
        total = none_weight + sum(args.command_weights_map[command] for command in legal)
        return random.random() * total < none_weight

    def always_skills(self):
        # skills at least one character must hold: -comw always, plus Blitz when a
        # Suplex A Train objective needs it (even at weight 0)
        import objectives
        always = list(args.command_always)
        blitz_id = name_id["Blitz"]
        if objectives.suplex_train_condition_exists and blitz_id not in always:
            always.append(blitz_id)
        return always

    def deal_always(self, characters, held, fills):
        # an always skill nobody holds takes one open slot (of the `fills` slot counts)
        # of a random character that has one
        dealt = {character : [] for character in characters}
        for command in self.always_skills():
            if any(command in held[character] or command in dealt[character] for character in characters):
                continue
            open_characters = [character for character in characters
                               if sum(fill[character] for fill in fills) > 0]
            if not open_characters:
                continue
            character = random.choice(open_characters)
            fill = random.choice([fill for fill in fills for _ in range(fill[character])])
            fill[character] -= 1
            dealt[character].append(command)
        return dealt

    def repeat_skills(self, characters, slot_counts, legal, held, dealt):
        # -comr slots and -com 99 slots: each draws a skill by weight among the legal
        # skills its character lacks. skills may repeat between characters (morph once)
        weights = args.command_weights_map
        morph_id = name_id["Morph"]
        skills = {character : [] for character in characters}
        for character in characters:
            for _ in range(slot_counts[character]):
                if self.empty_slot(legal):
                    continue
                candidates = [command for command in legal
                              if command not in held[character] and command not in skills[character]
                              and not (command == morph_id and dealt[morph_id])]
                if not candidates:
                    break
                command = weighted_choice(candidates, weights)
                skills[character].append(command)
                dealt[command] += 1
        return skills

    def place_skills(self, chosen, slots, held, skills):
        # match the chosen skills to open slots (a character id per slot) so that no
        # character gets a skill it already has; returns {slot index: skill}
        order = list(range(len(slots)))
        random.shuffle(order)
        match = {}

        def fits(command, index):
            character = slots[index]
            return command not in held[character] and command not in skills[character]

        def assign(command, seen):
            for index in order:
                if index in seen or not fits(command, index):
                    continue
                seen.add(index)
                if index not in match or assign(match[index], seen):
                    match[index] = command
                    return True
            return False

        for command in chosen:
            assign(command, set())
        return match

    def unique_skills(self, characters, slot_counts, legal, held, dealt):
        # -comru slots and -com 98 slots take distinct skills: the least-dealt legal skills
        # go first (so none repeats until every one is used), each round's skills chosen
        # together by weight share
        weights = args.command_weights_map
        morph_id = name_id["Morph"]
        skills = {character : [] for character in characters}
        slots = [character for character in characters for _ in range(slot_counts[character])]
        slots = [character for character in slots if not self.empty_slot(legal)]
        random.shuffle(slots)
        while slots:
            usable = [command for command in legal
                      if not (command == morph_id and dealt[morph_id])
                      and any(command not in held[character] and command not in skills[character]
                              for character in slots)]
            if not usable:
                break
            fewest = min(dealt[command] for command in usable)
            chosen = share_sample([command for command in usable if dealt[command] == fewest],
                                  weights, len(slots))
            match = self.place_skills(chosen, slots, held, skills)
            if not match:
                break
            for index, command in match.items():
                skills[slots[index]].append(command)
                dealt[command] += 1
            slots = [character for index, character in enumerate(slots) if index not in match]
        return skills

    def mod_probability_random_commands(self):
        # -comr/-comru (with any -com picks and marks):
        # 1. explicit -com picks claim their slots (97 holds a slot empty;
        #    99/98 mark slots for repeat/unique draws)
        # 2. Fight/Magic/Item roll at their percents into the remaining slots
        #    (Gau never gets Fight)
        # 3. every other slot takes a skill: -comw always skills first, then 99 and
        #    -comr slots draw by weight (repeats allowed), then 98 and -comru slots
        #    take distinct skills by weight share
        from collections import Counter
        from data.characters import Characters
        fight_id = name_id["Fight"]
        magic_id = name_id["Magic"]
        item_id = name_id["Item"]
        none_id = name_id["None"]
        morph_id = name_id["Morph"]

        legal = self.random_command_list()
        self.mod_moogle_commands(list(legal))

        characters = self.full_random_characters()

        # step 1: explicit traditional picks and slot marks
        explicit = {character : [] for character in characters}
        random_fill = {character : 0 for character in characters}
        unique_fill = {character : 0 for character in characters}
        empty_slots = {character : 0 for character in characters}
        if args.character_commands:
            # same explicit-command rules as mod_commands: the random pool plus
            # fight anywhere, morph only in terra's slot, leap only in gau's
            leap_id = name_id["Leap"]
            allowed = set(name_id[name] for name in RANDOM_POSSIBLE_COMMANDS) | {fight_id}
            character_picks = {character : [args.character_commands[character]]
                               for character in characters if character != Characters.GAU}
            character_picks[Characters.GAU] = [args.character_commands[-2], args.character_commands[-1]]
            for character, picks in character_picks.items():
                for command in picks:
                    if command == RANDOM_COMMAND:
                        random_fill[character] += 1
                    elif command == RANDOM_UNIQUE_COMMAND:
                        unique_fill[character] += 1
                    elif command == NONE_COMMAND:
                        empty_slots[character] += 1
                    elif (command in allowed
                          or (command == morph_id and character == 0)
                          or (command == leap_id and character == Characters.GAU)):
                        explicit[character].append(command)
                    else:
                        raise ValueError(f"Invalid character command {command}")

        # every skill handed out counts toward uniqueness (and morph's one holder)
        dealt = Counter()
        for character in characters:
            dealt.update(explicit[character])

        # step 2: Fight/Magic/Item, in a random order, into the free slots; what is
        # left joins the family's draw (unique for -comru, repeats for -comr)
        basics = {}
        for character in characters:
            capacity = (COMMAND_SLOT_COUNT - len(explicit[character]) - empty_slots[character]
                        - random_fill[character] - unique_fill[character])
            rolled = []
            order = list(args.command_basics)
            random.shuffle(order)
            for command, percent in order:
                if len(rolled) == capacity:
                    break
                # gau has no fight command in vanilla, and that is part of what makes him unique
                if command == fight_id and character == Characters.GAU:
                    continue
                if command in explicit[character]:
                    continue
                if random.randrange(100) < percent:
                    rolled.append(command)
            basics[character] = rolled
            leftover = capacity - len(rolled)
            if args.commands_unique:
                unique_fill[character] += leftover
            else:
                random_fill[character] += leftover

        # step 3: skills -- always first, then repeat draws (as with -com, a 98 never
        # repeats a 99's pick), then the unique draws
        held = {character : list(explicit[character]) for character in characters}
        forced = self.deal_always(characters, held, [random_fill, unique_fill])
        for character in characters:
            dealt.update(forced[character])
            held[character] += forced[character]
        randomed = self.repeat_skills(characters, random_fill, legal, held, dealt)
        for character in characters:
            held[character] += randomed[character]
        drafted = self.unique_skills(characters, unique_fill, legal, held, dealt)

        # apply the commands in menu order: fight -> skills -> magic -> item, with
        # explicit picks ahead of drawn skills and empty slots at the end
        for character in characters:
            explicit_skills = [command for command in explicit[character] if command != fight_id]
            commands = []
            if fight_id in basics[character] or fight_id in explicit[character]:
                commands.append(fight_id)
            commands.extend(explicit_skills)
            commands.extend(forced[character] + drafted[character] + randomed[character])
            if magic_id in basics[character]:
                commands.append(magic_id)
            if item_id in basics[character]:
                commands.append(item_id)
            commands.extend([none_id] * (COMMAND_SLOT_COUNT - len(commands)))

            self.characters[character].commands = commands

    def shuffle_full_random_commands(self):
        # commands are already random, so shuffle whole command sets between characters
        # instead of single slots to keep each character's menu order intact
        characters = self.full_random_characters()

        command_sets = [self.characters[character].commands for character in characters]
        random.shuffle(command_sets)

        for index, character in enumerate(characters):
            self.characters[character].commands = command_sets[index]

    def shuffle_commands(self):
        from data.characters import Characters

        commands = []
        for index in range(len(COMMAND_OPTIONS) - 1):
            commands.append(self.characters[index].commands[1])
        commands.append(self.characters[Characters.GAU].commands[0]) # rage

        random.shuffle(commands)

        for index in range(len(COMMAND_OPTIONS) - 1):
            self.characters[index].commands[1] = commands[index]
        self.characters[Characters.GAU].commands[0] = commands[-1] # rage

    def mod(self):
        import data.characters_asm as characters_asm
        from data.characters import Characters

        if args.commands_probability_mode:
            self.mod_probability_random_commands()
        elif args.commands:
            self.mod_commands()
        if args.shuffle_commands:
            if args.commands_probability_mode:
                self.shuffle_full_random_commands()
            else:
                self.shuffle_commands()

        if args.commands or args.commands_probability_mode or args.shuffle_commands:
            characters_asm.update_morph_character(self.characters[ : Characters.CHARACTER_COUNT])

    def log(self):
        from log import section, format_option
        from data.characters import Characters

        if args.commands_probability_mode:
            # every slot can be randomized, so log each character's full command menu
            lcolumn = []
            for character in self.full_random_characters():
                commands = [id_name[command] for command in self.characters[character].commands
                            if command != name_id["None"]]
                lcolumn.append(format_option(Characters.DEFAULT_NAME[character].capitalize(), ", ".join(commands)))

            section("Commands", lcolumn, [])
            return

        lcolumn = []
        for index, option in enumerate(COMMAND_OPTIONS[ : -2]):
            lcolumn.append(format_option(option, id_name[self.characters[index].commands[1]]))
        lcolumn.append(format_option(COMMAND_OPTIONS[-2], id_name[self.characters[Characters.GAU].commands[0]]))
        lcolumn.append(format_option(COMMAND_OPTIONS[-1], id_name[self.characters[Characters.GAU].commands[1]]))

        section("Commands", lcolumn, [])
