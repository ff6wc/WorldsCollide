from event.event import *

class PhantomTrain(Event):
    def name(self):
        return "Phantom Train"

    def character_gate(self):
        return self.characters.SABIN

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def init_event_bits(self, space):
        space.write(
            field.SetEventBit(event_bit.FOUND_PHANTOM_TRAIN),
            field.ClearEventBit(npc_bit.GHOST_SHOP_PHANTOM_FOREST),
        )

    def mod(self):
        self._load_world_map()
        self.forest_spring_mod()
        self.ghost_shop_forest_mod()
        self.find_train_mod()
        self.enter_train_mod()
        self.recruit_ghosts_mod()
        self.engineer_switch_mod()
        self.escape_ghosts_mod()
        self.restaurant_mod()
        self.ziegfried_mod()
        self.ghosts_leave_mod()
        self.phantom_train_battle_mod()
        self.phantom_train_mod()
        self.random_forest_mod()

        if self.args.character_gating:
            self.add_gating_condition()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        self.log_reward(self.reward)

    def add_gating_condition(self):
        # use deleted auto walk to forest spring event
        space = Reserve(0xba3d1, 0xba3e3, "phantom forest auto recovery spring", field.NOP())
        space.copy_from(0xba3ca, 0xba3d0) # load train station and return

        space = Reserve(0xba3ca, 0xba3d0, "phantom forest exit condition", field.NOP())
        space.write(
            field.ReturnIfEventBitClear(event_bit.character_recruited(self.character_gate())),
        )


    def _load_world_map(self):
        src = [
            field.FadeOutSong(32),
            field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.LoadMap(0x00, direction.DOWN, default_music = False, x = 178, y = 94, airship = True),
            vehicle.SetPosition(178, 94),
            vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            vehicle.LoadMap(0x00, direction.DOWN, default_music = True, x = 178, y = 93),
            world.Turn(direction.DOWN),
            world.End(),
        ]
        space = Write(Bank.CB, src, "phantom train move airship and return to world map")
        self.load_world_map = space.start_address

    def esper_item_mod(self, esper_item_instructions):
        ghost_npc_id = 0x10

        src = [
            esper_item_instructions,

            field.HideEntity(ghost_npc_id),
            field.RefreshEntities(),
            field.SetEventBit(event_bit.GOT_PHANTOM_TRAIN_REWARD),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "phantom train caboose esper item receive reward")
        receive_reward = space.start_address

        space = Reserve(0xbaafe, 0xbab08, "phantom train caboose esper/item", field.NOP())
        space.write(
            field.Call(receive_reward),
            field.Return(),
        )

        space = Reserve(0xbaca0, 0xbacec, "phantom train hide ghost if got esper/item", field.NOP())
        inside_last_car_entrance_event = space.next_address
        space.write(
            field.ReturnIfEventBitClear(event_bit.GOT_PHANTOM_TRAIN_REWARD),
            field.HideEntity(ghost_npc_id),
            field.RefreshEntities(),
            field.Return(),
        )
        self.maps.set_entrance_event(0x98, inside_last_car_entrance_event - EVENT_CODE_START)

    def esper_mod(self, esper):
        self.esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def item_mod(self, item):
        self.esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def character_mod(self, character):
        ghost_npc_id = 0x10
        ghost_npc = self.maps.get_npc(0x98, ghost_npc_id)
        ghost_npc.sprite = character
        ghost_npc.palette = self.characters.get_palette(character)

        self.dialogs.set_text(716, "Bring it along?<line><choice>(Sure)<line><choice>(No way)<end>")

        space = Reserve(0xbaca0, 0xbacce, "phantom train add character", field.NOP())
        space.write(
            field.RecruitAndSelectParty(character),
            field.HideEntity(ghost_npc_id),
            field.SetEventBit(event_bit.GOT_PHANTOM_TRAIN_REWARD),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        )

        space = Reserve(0xbaccf, 0xbacec, "phantom train hide character if recruited", field.NOP())
        inside_last_car_entrance_event = space.next_address
        space.write(
            field.ReturnIfEventBitClear(event_bit.character_available(character)),
            field.HideEntity(ghost_npc_id),
            field.Return(),
        )
        self.maps.set_entrance_event(0x98, inside_last_car_entrance_event - EVENT_CODE_START)

    def forest_spring_mod(self):
        # do not automatically walk char to spring
        self.maps.delete_event(0x85, 3, 12)

    def ghost_shop_forest_mod(self):
        # select a location at random where ghost shop will appear in forest
        import random
        from collections import namedtuple
        ForestPos = namedtuple("ForestPos", ["map_id", "x", "y"])
        possible_positions = [ForestPos(0x84, 10, 9), ForestPos(0x84, 17, 9), ForestPos(0x84, 27, 10),
                              ForestPos(0x85, 3, 9), ForestPos(0x85, 13, 10), ForestPos(0x85, 18, 9),
                              ForestPos(0x86, 5, 10), ForestPos(0x86, 7, 9), ForestPos(0x86, 13, 9)]
        forest_pos = random.choice(possible_positions)

        from data.npc import NPC
        ghost_shop_npc = NPC()
        ghost_shop_npc.x = forest_pos.x
        ghost_shop_npc.y = forest_pos.y
        ghost_shop_npc.direction = random.randrange(4)
        ghost_shop_npc.speed = NPC.SLOWEST
        ghost_shop_npc.movement = NPC.RANDOM_MOVE
        ghost_shop_npc.sprite = 20
        ghost_shop_npc.palette = 0
        ghost_shop_npc.background_layer = 2 # causes ghost to be above some leaves but doesn't get clipped
        ghost_shop_npc.event_byte = npc_bit.event_byte(npc_bit.GHOST_SHOP_PHANTOM_FOREST)
        ghost_shop_npc.event_bit = npc_bit.event_bit(npc_bit.GHOST_SHOP_PHANTOM_FOREST)

        ghost_shop_npc_id = self.maps.append_npc(forest_pos.map_id, ghost_shop_npc)
        ghost_shop_npc.set_event_address(0xbad44)

    def find_train_mod(self):
        space = Reserve(0xba864, 0xba8e6, "phantom train skip find train event", field.NOP())
        space.write(field.Return())

    def enter_train_mod(self):
        ghost_train_pack = self.enemies.packs.get_id("GhostTrain")
        ghost_train_battle_background = 33

        space = Reserve(0xba8f1, 0xba8f9, "phantom train dialog hey we can get in", field.NOP())

        space = Reserve(0xba8fc, 0xba8fc, "phantom train move party to door")
        space.write(field_entity.PARTY0)

        space = Reserve(0xba901, 0xba951, "phantom train skip enter event", field.NOP())
        space.write(
            # clear this event bit in case lump of metal chest already done
            field.ClearEventBit(event_bit.LUMP_CHEST_DOOR_GHOST_PHANTOM_TRAIN),
            field.Branch(space.end_address + 1), # skip nops
        )

        # do not to set layering priority to 3 like it does for sabin
        space = Reserve(0xba95b, 0xba961, "phantom train have party enter door", field.NOP())
        space.write(
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.SetSpeed(field_entity.Speed.NORMAL),
                field_entity.Move(direction.UP, 1),
            ),
        )

        space = Reserve(0xba962, 0xba977, "phantom train skip cyan/shadow follow in", field.NOP())
        space.write(
            field.FadeOutScreen(8),
        )

        space = Reserve(0xba980, 0xba983, "phantom train do not remove npc/interceptor from gau's fathers' house", field.NOP())

        space = Reserve(0xba98c, 0xbaa25, "phantom train entered event", field.NOP())
        space.write(
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.Move(direction.UP, 3),
            ),
            field.BranchIfEventBitClear(event_bit.DEFEATED_PHANTOM_TRAIN, "BOARD_TRAIN"),

            # if already finished phantom train event, invoke battle with phantom train
            field.PlaySoundEffect(146),
            field.Pause(1.5),
            field.InvokeBattleType(ghost_train_pack, field.BattleType.BACK, ghost_train_battle_background),
            field.Branch(self.load_world_map),

            "BOARD_TRAIN",
        )
        space.copy_from(0xbaa91, 0xbaaa4)
        space.write(
            field.Return(),
        )

        # remove sabin's name from won't open dialog
        self.dialogs.set_text(709, "Won't open!<end>")

        space = Reserve(0xbaa26, 0xbaaae, "phantom train skip trying to leave event", field.NOP())
        space.write(
            field.Return(),
        )

    def recruit_ghosts_mod(self):
        # do not allow recruiting ghosts since they replace strago/relm
        space = Reserve(0xbaad9, 0xbaafd, "phantom train ignore ghosts", field.Return())
        space = Reserve(0xbab09, 0xbac9f, "phantom train ignore ghosts2", field.Return())

    def engineer_switch_mod(self):
        space = Reserve(0xbaf03, 0xbaf05, "phantom train be these the schedules?", field.NOP())

        space = Reserve(0xbaf12, 0xbb00f, "phantom train clear engineer switch scene", field.NOP())
        space.write(field.Return())

    def escape_ghosts_mod(self):
        space = Reserve(0xbb267, 0xbb269, "phantom train ghost blocking exit no escape", field.NOP())

        space = Reserve(0xbb276, 0xbb397, "phantom train ghosts surround party event", field.NOP())
        space.write(
            field.LoadMap(0x08e, direction.DOWN, default_music = True, x = 40, y = 9, fade_in = False),
        )

        # skip ghosts surrounding party cutscene and instead place every ghost in final position immediately when map loads
        ghosts = [
            (0x10, (37, 9), direction.RIGHT), (0x11, (36, 9), direction.RIGHT), (0x12, (35, 9), direction.RIGHT),
            (0x13, (34, 9), direction.DOWN),  (0x14, (34, 8), direction.DOWN),  (0x15, (33, 8), direction.DOWN),
            (0x18, (41, 9), direction.LEFT),  (0x19, (42, 9), direction.LEFT),
            (0x1a, (43, 9), direction.DOWN),  (0x1b, (43, 8), direction.DOWN),  (0x1c, (44, 8), direction.DOWN),
        ]
        for ghost in ghosts:
            space.write(
                field.ShowEntity(ghost[0]),
                field.EntityAct(ghost[0], True,
                    field_entity.SetPosition(ghost[1][0], ghost[1][1]),
                    field_entity.Turn(ghost[2]),
                ),
            )

        space.write(
            field.FadeInScreen(),
            field.Return(),
        )

        space = Reserve(0xbb3f4, 0xbb4d3, "phantom train ladder event, ghosts move closer", field.NOP())
        space.write(
            field.Return(),
        )

        space = Reserve(0xbb4e1, 0xbb549, "phantom train skip pre-jumping scene", field.NOP())
        space.write(
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.Move(direction.RIGHT, 7),
                field_entity.Turn(direction.LEFT),
            ),
            field.Branch(space.end_address + 1), # skip nops
        )

        # change sabin jumping to party jumping
        space = Reserve(0xbb54a, 0xbb54a, "phantom train jump1")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbb551, 0xbb551, "phantom train jump2")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbb55d, 0xbb55d, "phantom train jump3")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbb564, 0xbb564, "phantom train jump4")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbb580, 0xbb580, "phantom train jump5")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbb586, 0xbb586, "phantom train jump6")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbb58c, 0xbb58c, "phantom train jump7")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbb59c, 0xbb59c, "phantom train jump8")
        space.write(field_entity.PARTY0)

        # make the ghost following party on appear roof immediately after falling from jump
        space = Reserve(0xbb5b5, 0xbb5b5, "phantom train return before ghost follows event tiles", field.NOP())

        space = Reserve(0xbb5bc, 0xbb5ef, "phantom train escaping ghosts face ghosts", field.NOP())
        space.write(
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.Turn(direction.RIGHT),
            ),
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xbb5fc, 0xbb639, "phantom train skip deciding to detach cars", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xbb665, 0xbb6b8, "phantom train go outside, trains detach", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )
        space = Reserve(0xbb6bb, 0xbb7be, "phantom train train rolls back out of screen", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xbb7c3, 0xbb7c5, "phantom train skip can't follow us now dialog", field.NOP())
        space = Reserve(0xbb7c6, 0xbb7ce, "phantom train do not require flipping switch a second time", field.NOP())

    def restaurant_mod(self):
        space = Reserve(0xbb04e, 0xbb050, "phantom train skip one moment please dialog", field.NOP())

        space = Reserve(0xbb193, 0xbb193, "phantom train restaurant center party")
        space.write(field_entity.PARTY0)

        space = Reserve(0xbb197, 0xbb19a, "phantom train restaurant do not hide party", field.NOP())

        space = Reserve(0xbb19c, 0xbb19c, "phantom train restaurant party demand food")
        space.write(field_entity.PARTY0)

        space = Reserve(0xbb1a7, 0xbb1a9, "phantom train restaurant food! food! dialog", field.NOP())

        space = Reserve(0xbb1aa, 0xbb1aa, "phantom train restaurant party demand food2")
        space.write(field_entity.PARTY0)

        space = Reserve(0xbb1d1, 0xbb1d1, "phantom train restaurant turn party down")
        space.write(field_entity.PARTY0)

        space = Reserve(0xbb1e0, 0xbb248, "phantom train restaurant cyan's reaction", field.NOP())
        space = Reserve(0xbb24f, 0xbb25e, "phantom train restaurant finished eating", field.NOP())

        # when eating a second time it looks like sabin/cyan/shadow events can trigger
        # skip them
        #space = Reserve(0xbb088, 0xbb09a, "phantom train restaurant skip other scenes")
        #space.clear(field.NOP())

        if self.args.no_free_heals:
            self.ruination_restaurant_mod()

    def ziegfried_mod(self):
        space = Reserve(0xbb809, 0xbb862, "phantom train before ziegfried appears", field.NOP())

        space = Reserve(0xbb871, 0xbb885, "phantom train face ziegfriend", field.NOP())
        space.write(
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.Turn(direction.RIGHT)
            ),
        )

        space = Reserve(0xbb888, 0xbb8a6, "phantom train before ziegfried attacks", field.NOP())
        space = Reserve(0xbb8cd, 0xbb8cf, "phantom train ziegfried what a bag of wind", field.NOP())
        space = Reserve(0xbb8d4, 0xbb8d6, "phantom train ziegfried impossible", field.NOP())
        space = Reserve(0xbb900, 0xbb902, "phantom train ziegfried uwa, ha, ha", field.NOP())

    def ghosts_leave_mod(self):
        space = Reserve(0xbad52, 0xbaee2, "phantom train ghosts leave party event before the last two cars", field.NOP())
        self.maps.delete_event(0x8d, 55, 8)

    def phantom_train_battle_mod(self):
        boss_pack_id = self.get_boss("GhostTrain")
        battle_background = 33 # ghost train tracks

        battle_type = field.BattleType.BACK
        if boss_pack_id == self.enemies.packs.get_id("SrBehemoth"):
            battle_type = field.BattleType.FRONT

        space = Reserve(0xbb9ff, 0xbba05, "phantom train invoke battle ghosttrain", field.NOP())
        space.write(
            field.InvokeBattleType(boss_pack_id, battle_type, battle_background),
        )

    def phantom_train_mod(self):
        # remove cyan/shadow from final phantom train scene on platform
        self.maps.remove_npc(0x89, 0x10) # cyan
        self.maps.remove_npc(0x89, 0x10) # shadow

        space = Reserve(0xba6b9, 0xba6bb, "phantom train gotta stop this thing", field.NOP())
        space = Reserve(0xbb9e6, 0xbb9e8, "phantom train press this switch", field.NOP())
        space = Reserve(0xbb9f4, 0xbb9f6, "phantom train so you've been slowing", field.NOP())
        space = Reserve(0xbb9fb, 0xbb9fe, "phantom train sound and delay before fight", field.NOP())

        src = []
        if self.reward.type == RewardType.CHARACTER:
            src += [
                field.BranchIfEventBitSet(event_bit.GOT_PHANTOM_TRAIN_REWARD, "AFTER_REWARD"),
                field.RecruitAndSelectParty(self.reward.id),
                field.SetEventBit(event_bit.GOT_PHANTOM_TRAIN_REWARD),
                field.FadeInScreen(),
                field.FinishCheck(),
            ]
        elif self.reward.type == RewardType.ESPER:
            src += [
                field.FadeInScreen(),
                field.BranchIfEventBitSet(event_bit.GOT_PHANTOM_TRAIN_REWARD, "AFTER_REWARD"),
                field.AddEsper(self.reward.id),
                field.Dialog(self.espers.get_receive_esper_dialog(self.reward.id)),
                field.SetEventBit(event_bit.GOT_PHANTOM_TRAIN_REWARD),
                field.FinishCheck(),
            ]
        elif self.reward.type == RewardType.ITEM:
            src += [
                field.FadeInScreen(),
                field.BranchIfEventBitSet(event_bit.GOT_PHANTOM_TRAIN_REWARD, "AFTER_REWARD"),
                field.AddItem(self.reward.id),
                field.Dialog(self.items.get_receive_dialog(self.reward.id)),
                field.SetEventBit(event_bit.GOT_PHANTOM_TRAIN_REWARD),
                field.FinishCheck(),
            ]

        src += [
            "AFTER_REWARD",
            field.SetEventBit(event_bit.DEFEATED_PHANTOM_TRAIN),
            field.SetEventBit(npc_bit.GHOST_SHOP_PHANTOM_FOREST),
            field.ClearEventBit(npc_bit.PHANTOM_TRAIN_SAVE_POINT),
            field.ClearEventBit(npc_bit.ATTACK_GHOSTS_PHANTOM_TRAIN),
            field.ClearEventBit(event_bit.SIEGFRIED_LUMP_OF_METAL_CHESTS),
            field.Branch(self.load_world_map),
        ]
        space = Write(Bank.CB, src, "phantom train ensure reward and exit forest")
        end_event = space.start_address

        space = Reserve(0xbba06, 0xbba0b, "phantom train defeated call ensure reward and exit froest", field.NOP())
        space.write(
            field.Branch(end_event),
        )

    def random_forest_mod(self):
        # after completing phantom train, allow for finding it again
        # northeast path in crossroads randomly leads to phantom train or a random map

        random_destinations = [
            field.FadeLoadMap(0x084, direction.RIGHT, True, 1, 9, fade_in = True),  # map 1 west
            field.FadeLoadMap(0x084, direction.DOWN, True, 28, 8, fade_in = True),  # map 1 east
            field.FadeLoadMap(0x085, direction.UP, True, 3, 13, fade_in = True),    # map 2 west
            field.FadeLoadMap(0x085, direction.UP, True, 20, 13, fade_in = True),   # map 2 east
            field.FadeLoadMap(0x086, direction.DOWN, True, 5, 8, fade_in = True),   # map 3 northwest
            field.FadeLoadMap(0x086, direction.UP, True, 12, 11, fade_in = True),   # map 3 southeast
        ]

        addresses = []
        for destination in random_destinations:
            src = [
                destination,
                field.Return(),
            ]
            space = Write(Bank.CB, src, "phantom forest random destination")
            addresses.append(space.start_address)

        src = [
            field.BranchChance(2 / 3, "RANDOMLY_EXIT"),
            field.FadeLoadMap(0x087, direction.UP, True, 3, 12, fade_in = True),    # path to phantom train
            field.Return(),

            "RANDOMLY_EXIT",
            field.BranchChance(5 / 6, "RANDOM_DESTINATION"),
            field.Return(),                                                         # path to world map

            "RANDOM_DESTINATION",
        ]

        count = len(addresses)
        for i in range(count):
            probability = (count / (count - i)) / count
            src += [
                field.BranchChance(probability, addresses[i]),
            ]
        src += [
            field.Return(),
        ]
        space = Write(Bank.CB, src, "phantom forest randomly find phantom train or a random map")
        random_destination = space.start_address

        space = Reserve(0xba3c4, 0xba3c9, "phantom forest last map branch if finished phantom train", field.NOP())
        space.write(
            field.BranchIfEventBitSet(event_bit.STOPPED_PHANTOM_TRAIN, random_destination),
        )
    def ruination_restaurant_mod(self):
        """
        Modifies the Phantom Train restaurant for ruination mode.
        Offers three meal choices with different effects:
        - Cheap Meal (10 GP): Random effect (HP, MP, status cure, or negative status)
        - Filling Meal (500 GP): Full HP, but 1/4 chance of poison/imp per character
        - Chef's Special (2000 GP): Full heal (HP, MP, status)
        """
        import random as rng

        # Prices
        CHEAP_MEAL_PRICE = 10
        FILLING_MEAL_PRICE = 500
        CHEFS_SPECIAL_PRICE = 2000

        # Dialog IDs
        MENU_DIALOG_ID = 653
        NOT_ENOUGH_GP_DIALOG = 2748
        CHEAP_MEAL_DIALOG = 655
        FILLING_MEAL_DIALOG = 656
        CHEFS_SPECIAL_DIALOG = 657

        # Party members
        PARTY = [field_entity.PARTY0, field_entity.PARTY1, field_entity.PARTY2, field_entity.PARTY3]

        # Status effects for healing
        HEAL_STATUS = (field.Status.DEATH | field.Status.PETRIFY | field.Status.IMP |
                       field.Status.VANISH | field.Status.POISON | field.Status.ZOMBIE |
                       field.Status.DARKNESS)

        # Set the dialog text for the 3-choice menu
        # f"Care for something?<line>"
        self.dialogs.set_text(MENU_DIALOG_ID,
            f"<choice> Cheap Meal ({CHEAP_MEAL_PRICE} GP)<line>"
            f"<choice> Filling Meal ({FILLING_MEAL_PRICE} GP)<line>"
            f"<choice> Chef's Special ({CHEFS_SPECIAL_PRICE} GP)<line><choice> No, thanks<end>")

        # Set common dialog texts
        # self.dialogs.set_text(NOT_ENOUGH_GP_DIALOG, "You don't have enough GP!<end>")
        self.dialogs.set_text(FILLING_MEAL_DIALOG, "HP restored!<end>")
        self.dialogs.set_text(CHEFS_SPECIAL_DIALOG, "HP, MP, and status restored!<end>")

        # Randomly pick the cheap meal effect at compile time (same as recovery springs, minus full heal)
        CHEAP_MEAL_EFFECTS = {
            "RECOVER_HP": ("HP restored!<end>", field.Flash.WHITE),
            "RECOVER_MP": ("MP restored!<end>", field.Flash.BLUE),
            "RECOVER_STATUS": ("Status ailments cured!<end>", field.Flash.WHITE),
            "POISON": ("The food was poisoned!<end>", field.Flash.GREEN),
            "IMP": ("The food turned you into Imps!<end>", field.Flash.GREEN),
            "ZOMBIE": ("The food was cursed!<end>", field.Flash.GREEN),
            "STONE": ("The food is petrifying!<end>", field.Flash.WHITE),
            "REDUCE_TO_1_HP": ("The food drained your strength!<end>", field.Flash.RED),
        }
        cheap_meal_effect = rng.choice(list(CHEAP_MEAL_EFFECTS.keys()))
        cheap_meal_message, flash_color = CHEAP_MEAL_EFFECTS[cheap_meal_effect]
        self.dialogs.set_text(CHEAP_MEAL_DIALOG, cheap_meal_message)

        # Build the cheap meal effect instructions
        cheap_meal_instructions = []

        if cheap_meal_effect == "RECOVER_HP":
            for p in PARTY:
                cheap_meal_instructions.append(field.RestoreHp(p, 0x7f))

        elif cheap_meal_effect == "RECOVER_MP":
            for p in PARTY:
                cheap_meal_instructions.append(field.RestoreMp(p, 0x7f))

        elif cheap_meal_effect == "RECOVER_STATUS":
            for p in PARTY:
                cheap_meal_instructions.append(field.RemoveStatusEffects(p, HEAL_STATUS))

        elif cheap_meal_effect == "POISON":
            cheap_meal_instructions.append(field.AddStatusEffects(field_entity.PARTY0, field.Status.POISON))
            cheap_meal_instructions.extend([
                field.BranchRandomly("SKIP_P1_POISON"),
                field.AddStatusEffects(field_entity.PARTY1, field.Status.POISON),
                "SKIP_P1_POISON",
                field.BranchRandomly("SKIP_P2_POISON"),
                field.AddStatusEffects(field_entity.PARTY2, field.Status.POISON),
                "SKIP_P2_POISON",
                field.BranchRandomly("SKIP_P3_POISON"),
                field.AddStatusEffects(field_entity.PARTY3, field.Status.POISON),
                "SKIP_P3_POISON",
            ])

        elif cheap_meal_effect == "IMP":
            cheap_meal_instructions.append(field.AddStatusEffects(field_entity.PARTY0, field.Status.IMP))
            cheap_meal_instructions.extend([
                field.BranchRandomly("SKIP_P1_IMP"),
                field.AddStatusEffects(field_entity.PARTY1, field.Status.IMP),
                "SKIP_P1_IMP",
                field.BranchRandomly("SKIP_P2_IMP"),
                field.AddStatusEffects(field_entity.PARTY2, field.Status.IMP),
                "SKIP_P2_IMP",
                field.BranchRandomly("SKIP_P3_IMP"),
                field.AddStatusEffects(field_entity.PARTY3, field.Status.IMP),
                "SKIP_P3_IMP",
            ])

        elif cheap_meal_effect == "ZOMBIE":
            cheap_meal_instructions.append(field.AddStatusEffects(field_entity.PARTY0, field.Status.ZOMBIE))
            cheap_meal_instructions.extend([
                field.BranchRandomly("SKIP_P1_ZOMBIE"),
                field.AddStatusEffects(field_entity.PARTY1, field.Status.ZOMBIE),
                "SKIP_P1_ZOMBIE",
                field.BranchRandomly("SKIP_P2_ZOMBIE"),
                field.AddStatusEffects(field_entity.PARTY2, field.Status.ZOMBIE),
                "SKIP_P2_ZOMBIE",
                field.BranchRandomly("SKIP_P3_ZOMBIE"),
                field.AddStatusEffects(field_entity.PARTY3, field.Status.ZOMBIE),
                "SKIP_P3_ZOMBIE",
            ])

        elif cheap_meal_effect == "STONE":
            cheap_meal_instructions.append(field.AddStatusEffects(field_entity.PARTY0, field.Status.PETRIFY))
            cheap_meal_instructions.extend([
                field.BranchRandomly("SKIP_P1_STONE"),
                field.AddStatusEffects(field_entity.PARTY1, field.Status.PETRIFY),
                "SKIP_P1_STONE",
                field.BranchRandomly("SKIP_P2_STONE"),
                field.AddStatusEffects(field_entity.PARTY2, field.Status.PETRIFY),
                "SKIP_P2_STONE",
                field.BranchRandomly("SKIP_P3_STONE"),
                field.AddStatusEffects(field_entity.PARTY3, field.Status.PETRIFY),
                "SKIP_P3_STONE",
            ])

        elif cheap_meal_effect == "REDUCE_TO_1_HP":
            # Subtract 2^14 HP (16384), which reduces to 1 HP minimum
            for p in PARTY:
                cheap_meal_instructions.append(field.RestoreHp(p, 0x80 | 0x0e))

        # Build shared "not enough money" event first
        waiter_leaves_addr = 0xbb03d
        not_enough_money_src = [
            field.ClearEventBit(event_bit.NOT_ENOUGH_GP),
            field.Dialog(NOT_ENOUGH_GP_DIALOG),
            field.Call(waiter_leaves_addr),
            field.FreeMovement(),
            field.Return(),
        ]
        space = Write(Bank.CB, not_enough_money_src, "ruination restaurant not enough money")
        not_enough_money_addr = space.start_address

        # Build CHEAP MEAL event code
        cheap_meal_src = [
            field.RemoveGP(CHEAP_MEAL_PRICE),
            field.BranchIfEventBitSet(event_bit.NOT_ENOUGH_GP, not_enough_money_addr),
            field.FlashScreen(flash_color),
            field.PlaySoundEffect(233),
            field.PauseUnits(30),
            *cheap_meal_instructions,
            field.Dialog(CHEAP_MEAL_DIALOG),
            field.Call(waiter_leaves_addr),
            field.FreeMovement(),
            field.Return(),
        ]
        space = Write(Bank.CB, cheap_meal_src, "ruination restaurant cheap meal")
        cheap_meal_addr = space.start_address

        # Build FILLING MEAL event code (full HP, 1/4 chance poison or imp per character)
        filling_meal_src = [
            field.RemoveGP(FILLING_MEAL_PRICE),
            field.BranchIfEventBitSet(event_bit.NOT_ENOUGH_GP, not_enough_money_addr),
            field.FlashScreen(field.Flash.WHITE),
            field.PlaySoundEffect(233),
            field.PauseUnits(30),
            # Restore HP
            field.RestoreHp(field_entity.PARTY0, 0x7f),
            field.RestoreHp(field_entity.PARTY1, 0x7f),
            field.RestoreHp(field_entity.PARTY2, 0x7f),
            field.RestoreHp(field_entity.PARTY3, 0x7f),

            # 1/4 chance to apply poison or imp to each character
            # Party member 0
            field.BranchChance(0.75, "SKIP_P0_FILLING"),
            field.BranchRandomly("P0_IMP"),
            field.AddStatusEffects(field_entity.PARTY0, field.Status.POISON),
            field.Branch("SKIP_P0_FILLING"),
            "P0_IMP",
            field.AddStatusEffects(field_entity.PARTY0, field.Status.IMP),
            "SKIP_P0_FILLING",

            # Party member 1
            field.BranchChance(0.75, "SKIP_P1_FILLING"),
            field.BranchRandomly("P1_IMP"),
            field.AddStatusEffects(field_entity.PARTY1, field.Status.POISON),
            field.Branch("SKIP_P1_FILLING"),
            "P1_IMP",
            field.AddStatusEffects(field_entity.PARTY1, field.Status.IMP),
            "SKIP_P1_FILLING",

            # Party member 2
            field.BranchChance(0.75, "SKIP_P2_FILLING"),
            field.BranchRandomly("P2_IMP"),
            field.AddStatusEffects(field_entity.PARTY2, field.Status.POISON),
            field.Branch("SKIP_P2_FILLING"),
            "P2_IMP",
            field.AddStatusEffects(field_entity.PARTY2, field.Status.IMP),
            "SKIP_P2_FILLING",

            # Party member 3
            field.BranchChance(0.75, "SKIP_P3_FILLING"),
            field.BranchRandomly("P3_IMP"),
            field.AddStatusEffects(field_entity.PARTY3, field.Status.POISON),
            field.Branch("SKIP_P3_FILLING"),
            "P3_IMP",
            field.AddStatusEffects(field_entity.PARTY3, field.Status.IMP),
            "SKIP_P3_FILLING",

            field.Dialog(FILLING_MEAL_DIALOG),
            field.Call(waiter_leaves_addr),
            field.FreeMovement(),
            field.Return(),
        ]
        space = Write(Bank.CB, filling_meal_src, "ruination restaurant filling meal")
        filling_meal_addr = space.start_address

        # Build CHEF'S SPECIAL event code (full heal - calls original heal subroutine)
        # The original heal subroutine is at $CACFBD
        FULL_HEAL_SUBROUTINE = 0xCACFBD
        chefs_special_src = [
            field.RemoveGP(CHEFS_SPECIAL_PRICE),
            field.BranchIfEventBitSet(event_bit.NOT_ENOUGH_GP, not_enough_money_addr),
            field.FlashScreen(field.Flash.WHITE),
            field.PlaySoundEffect(233),
            field.PauseUnits(30),
            field.Call(FULL_HEAL_SUBROUTINE),
            field.Dialog(CHEFS_SPECIAL_DIALOG),
            field.Call(waiter_leaves_addr),
            field.FreeMovement(),
            field.Return(),
        ]
        space = Write(Bank.CB, chefs_special_src, "ruination restaurant chef's special")
        chefs_special_addr = space.start_address

        # Now patch the original restaurant dialog (at 0xBB032) to use our new menu
        # Original: CB/B032 displays dialog 0x028C and then branches at CB/B035
        # We need to replace this with our 4-choice dialog and branch
        new_menu_src = [
            field.DialogBranch(MENU_DIALOG_ID,
                               dest1=cheap_meal_addr,
                               dest2=filling_meal_addr,
                               dest3=chefs_special_addr,
                               dest4=waiter_leaves_addr),
            field.Return()
        ]
        space = Write(Bank.CB, new_menu_src, "phantom train ruination restaurant menu")
        new_menu_addr = space.start_address
        
        space = Reserve(0xbb032, 0xbb03c, "phantom train ruination restaurant redirect", field.NOP())
        space.write(
            field.DialogBranch(0x28C,
                               dest1=new_menu_addr,
                               dest2=waiter_leaves_addr,
                               top_of_screen=False,
                               wait_for_input=True)
        )

        # Make the first waiter visit also branch to here, after arms animation.
        space = Reserve(0xbb1b6, 0xbb1be, description='phantom train restaurant override first event')  # CB/B1B6: 10    Begin action queue for character $10 (NPC $10), 5 bytes long (Wait until complete)
        src = [
            field.SetEventBit(0x19d),  # Record that the first event happened
            field.Branch(0xbb022),     # Go back to repeat event code
            field.Return()
        ]
        space.write(src)
        


