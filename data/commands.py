from multiprocessing.sharedctypes import Value
from constants.commands import *
import random
import args

class UniquePool:
    # the unique draw: no legal skill is dealt again while another has been dealt
    # fewer times. counts every skill dealt this seed and offers a character only
    # the least-dealt legal skills it does not already hold, so the skills go round
    # once, then again, and a skill a character had to pass over (because it held
    # it) is still first in line for the next character that can take it
    def __init__(self, legal):
        self.legal = list(legal)
        self.tracked = set(self.legal)
        self.dealt = {command : 0 for command in self.legal}

    def candidates(self, held):
        options = [command for command in self.legal if command not in held]
        if not options:
            return []
        fewest = min(self.dealt[command] for command in options)
        return [command for command in options if self.dealt[command] == fewest]

    def take(self, command):
        if command in self.dealt:
            self.dealt[command] += 1
        if command == name_id["Morph"]:
            self.retire(command) # only one character gets morph

    def give_back(self, command):
        # a dealt command was taken off its character again
        if self.dealt.get(command, 0) > 0:
            self.dealt[command] -= 1

    def retire(self, command):
        # never deal this command again
        if command in self.legal:
            self.legal.remove(command)

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
        command_set = set(name_id[name] for name in RANDOM_POSSIBLE_COMMANDS)
        command_list = list(command_set)

        allowed_commands = command_set | set([name_id["Fight"], RANDOM_COMMAND, RANDOM_UNIQUE_COMMAND, NONE_COMMAND])

        # if morph was explicitly selected remove from available command list
        morph_id = name_id["Morph"]
        for command in args.character_commands:
            if command == morph_id:
                command_list.remove(morph_id)

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

        for index, command in enumerate(args.character_commands):
            if command not in allowed_commands and (index != 0 or command != name_id["Morph"]) and (index != 12 or command != name_id["Leap"]):
                raise ValueError(f"Invalid character command {command}")
            elif command == RANDOM_COMMAND:
                args.character_commands[index] = random.choice(command_list)
                if args.character_commands[index] == morph_id:
                    command_list.remove(morph_id) # only one character gets morph
            elif command == NONE_COMMAND:
                args.character_commands[index] = name_id["None"]

            command_set.discard(args.character_commands[index])

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
        # commands available to random selection, minus the -rec exclusions
        command_list = [name_id[name] for name in RANDOM_POSSIBLE_COMMANDS]
        for exclude_command in args.random_exclude_commands:
            try:
                command_list.remove(exclude_command)
            except ValueError:
                pass
        return command_list

    def random_skills(self, characters, skill_counts, available, taken = None):
        # fill each character's skill slots independently, commands may repeat between
        # characters. `taken` maps a character to commands it already holds outside
        # this fill (the -com pr rolled commands), which must not be dealt again
        morph_id = name_id["Morph"]
        taken = taken or {}

        skills = {character : [] for character in characters}
        for character in characters:
            for _ in range(skill_counts[character]):
                # never give a character the same command twice
                candidates = [command for command in available
                              if command not in skills[character]
                              and command not in taken.get(character, ())]
                if not candidates:
                    break

                command = random.choice(candidates)
                skills[character].append(command)
                if command == morph_id:
                    available.remove(morph_id) # only one character gets morph

        return skills

    def draft_skills(self, characters, skill_counts, available, taken = None, pool = None):
        # snake draft the skill slots so commands are unique for as long as they last,
        # then go round again. `pool` is the seed's UniquePool, which already counts every
        # skill dealt elsewhere in the seed (explicit picks, rolls, random fills); without
        # one, the draft is unique among its own slots. `taken` as in
        # random_skills: commands a character already holds and must not draft again
        taken = taken or {}
        if pool is None:
            pool = UniquePool(available)

        draft_order = list(characters)
        random.shuffle(draft_order)

        skills = {character : [] for character in characters}
        for round_index in range(max(skill_counts.values(), default = 0)):
            round_order = [character for character in draft_order if skill_counts[character] > round_index]
            if round_index % 2:
                round_order.reverse() # snake back the other way every other round

            for character in round_order:
                # never give a character the same command twice
                held = set(skills[character]) | set(taken.get(character, ()))
                candidates = pool.candidates(held)
                if not candidates:
                    continue

                command = random.choice(candidates)
                pool.take(command)
                skills[character].append(command)

        return skills

    def guarantee_blitz(self, characters, held, random_fill, unique_fill, rolled, pool):
        # if suplex a train condition exists, guarantee blitz (even if blitz is in the
        # excluded commands). runs before the backfill: when no character holds blitz
        # yet (explicit pick or roll), deal it into one open backfill slot, which the
        # fills and the unique pool's counts then account for. returns the blitz dealt
        # per character, which the caller adds to that character's skills.
        import objectives
        blitz_id = name_id["Blitz"]
        forced = {character : [] for character in characters}

        if not objectives.suplex_train_condition_exists:
            return forced
        if any(blitz_id in held[character] for character in characters):
            return forced

        open_characters = [character for character in characters
                           if random_fill[character] + unique_fill[character] > 0]
        if open_characters:
            character = random.choice(open_characters)
            fill = random.choice([random_fill] * random_fill[character]
                                 + [unique_fill] * unique_fill[character])
            fill[character] -= 1
            forced[character].append(blitz_id)
            pool.take(blitz_id)
            return forced

        # every slot was rolled or picked: replace a rolled skill (not an explicit pick)
        replaceable = [(character, index) for character in characters
                       for index, command in enumerate(rolled[character])
                       if command in pool.tracked and command != name_id["Morph"]]
        if replaceable:
            character, index = random.choice(replaceable)
            pool.give_back(rolled[character][index])
            rolled[character][index] = blitz_id
            pool.take(blitz_id)
        return forced

    def roll_probability_commands(self, character, capacity, held, pool = None):
        # roll one character's slots from the declared (command, percent) list
        # (-compr/-compru, plus -comfr/-comfru folded in). more commands can be
        # declared than the character has free slots, so: group the declarations
        # by likelihood, and starting with the most likely group roll each
        # command in a random order, stopping as soon as `capacity` slots are
        # claimed. a rolled 97 (None) claims a slot and leaves it empty; a
        # rolled command the character already holds explicitly claims nothing.
        # with a UniquePool (the unique modes), a skill already dealt elsewhere
        # in the seed is skipped without a roll until every legal skill is used
        from data.characters import Characters
        fight_id = name_id["Fight"]

        by_percent = {}
        for command, percent in args.command_probabilities:
            by_percent.setdefault(percent, []).append(command)

        rolled = []
        for percent in sorted(by_percent, reverse = True):
            group = list(by_percent[percent])
            random.shuffle(group)
            for command in group:
                if len(rolled) == capacity:
                    return rolled
                # gau has no fight command in vanilla, and that is part of what
                # makes him unique -- a declared fight probability never applies
                # to him (his slot backfills instead)
                if command == fight_id and character == Characters.GAU:
                    continue
                unique = pool is not None and command in pool.tracked
                if unique and command not in pool.candidates(held | set(rolled)):
                    continue
                if random.randrange(100) < percent:
                    if command not in held:
                        rolled.append(command)
                        if unique:
                            pool.take(command)
        return rolled

    def mod_probability_random_commands(self):
        # composed command assignment (-com / -comfr(u) / -compr(u)):
        # 1. explicit -com picks claim their slots (97 holds a slot empty;
        #    99/98 mark slots for random/unique backfill)
        # 2. the declared probabilities roll into the remaining capacity
        # 3. backfill: 99-marked slots fill randomly, then 98-marked slots draft
        #    unique, and any still-unfilled slots use the family default
        #    (unique for -comfru/-compru, random otherwise)
        # unique means unique across the whole seed: one UniquePool tracks every
        # skill dealt (explicit picks, rolls, random fills, drafts), and a unique
        # draw never repeats a skill while another has been dealt fewer times.
        # in the unique modes the rolls draw from it too, so a rolled skill is
        # not rolled again by anyone else until every legal skill has been dealt.
        from data.characters import Characters
        fight_id = name_id["Fight"]
        magic_id = name_id["Magic"]
        item_id = name_id["Item"]
        none_id = name_id["None"]
        morph_id = name_id["Morph"]

        available = self.random_command_list()
        self.mod_moogle_commands(available)

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

        # a morph handed out explicitly or by its probability roll must stay out
        # of the backfill pool: the "only one character gets morph" pool rule
        # (and the draft refill's morph invariant) cannot deal a second copy
        morph_placed = (any(morph_id in commands for commands in explicit.values())
                        or any(command == morph_id for command, _ in args.command_probabilities))
        if morph_placed:
            try:
                available.remove(morph_id)
            except ValueError:
                pass

        # the seed's unique pool: every legal skill (the non--rec pool plus any
        # declared skill), minus the skills already handed out explicitly
        skill_ids = set(name_id[name] for name in RANDOM_POSSIBLE_COMMANDS)
        declared_skills = [command for command, _ in args.command_probabilities
                           if command in skill_ids and command not in available]
        pool = UniquePool(available + declared_skills)
        for character in characters:
            for command in explicit[character]:
                pool.take(command)

        # step 2: probability rolls into the remaining capacity. in the unique
        # modes the rolls share the pool, so characters roll in a random order
        # (nobody always gets first pick of the skills)
        rolled = {}
        capacity = {}
        roll_order = list(characters)
        if args.commands_unique:
            random.shuffle(roll_order)
        for character in roll_order:
            capacity[character] = (COMMAND_SLOT_COUNT - len(explicit[character])
                                   - empty_slots[character]
                                   - random_fill[character] - unique_fill[character])
            rolled[character] = self.roll_probability_commands(
                character, capacity[character], set(explicit[character]),
                pool if args.commands_unique else None)

        # step 2.5: at most one character may hold morph.  outside the unique
        # modes the rolls are independent per character, so several can win
        # the same declared morph probability, but the morph-gauge ASM only supports a single
        # holder (data/characters_asm.update_morph_character: "this assumes
        # only 1 character has morph") -- extra copies would be broken
        # commands.  every character's chance to ROLL morph is untouched:
        # one winner is chosen at random and the losers' slots return to
        # capacity for ordinary backfill.  an explicit -com morph outranks
        # every rolled one.
        morph_winners = [character for character in characters
                         if morph_id in rolled[character]]
        if any(morph_id in commands for commands in explicit.values()):
            keep = None
        elif morph_winners:
            keep = random.choice(morph_winners)
        else:
            keep = None
        for character in morph_winners:
            if character != keep:
                rolled[character].remove(morph_id)

        # rolled skills are dealt: unique draws must not repeat them. the unique
        # modes counted them as they rolled; count -comfr/-compr rolls here. a
        # declared morph is only ever dealt by its roll, never by backfill
        if not args.commands_unique:
            for character in characters:
                for command in rolled[character]:
                    pool.take(command)
        if morph_placed:
            pool.retire(morph_id)

        # step 3: backfill -- leftover capacity joins the family-default style
        for character in characters:
            leftover = capacity[character] - len(rolled[character])
            if args.commands_unique:
                unique_fill[character] += leftover
            else:
                random_fill[character] += leftover

        # suplex a train: blitz claims a backfill slot first if nobody holds it
        held = {character : explicit[character] + rolled[character] for character in characters}
        forced = self.guarantee_blitz(characters, held, random_fill, unique_fill, rolled, pool)

        # random fills first (as with -com, a 98 never repeats a 99's pick),
        # then the unique draft from whatever the pool has left
        taken = {character : explicit[character] + forced[character]
                 + [command for command in rolled[character] if command != NONE_COMMAND]
                 for character in characters}
        randomed = self.random_skills(characters, random_fill, available, taken)
        for character in characters:
            for command in randomed[character]:
                pool.take(command)
        taken = {character : taken[character] + randomed[character] for character in characters}
        drafted = self.draft_skills(characters, unique_fill, available, taken, pool)

        skills = {character : forced[character] + drafted[character] + randomed[character]
                  for character in characters}

        # apply the commands in menu order: fight -> skills -> magic -> item,
        # with explicit picks ahead of rolled skills ahead of backfilled ones
        # and empty slots at the end
        for character in characters:
            common = [command for command in rolled[character]
                      if command in (fight_id, magic_id, item_id)]
            explicit_skills = [command for command in explicit[character] if command != fight_id]
            rolled_skills = [command for command in rolled[character]
                             if command not in (fight_id, magic_id, item_id, NONE_COMMAND)]
            commands = []
            if fight_id in common or fight_id in explicit[character]:
                commands.append(fight_id)
            commands.extend(explicit_skills)
            commands.extend(rolled_skills)
            commands.extend(skills[character])
            if magic_id in common:
                commands.append(magic_id)
            if item_id in common:
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
