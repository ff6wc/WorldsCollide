from event.event import *

class NarsheWOB(Event):
    def name(self):
        return "Narshe WOB"

    def init_event_bits(self, space):
        space.write(
            field.SetEventBit(event_bit.MET_ARVIS),
            field.SetEventBit(event_bit.NARSHE_GUARDS_SAW_TERRA_ON_BRIDGE),
            field.SetEventBit(event_bit.NARSHE_SECRET_ENTRANCE_ACCESS),
            field.SetEventBit(event_bit.TERRA_AGREED_TO_OPEN_SEALED_GATE),

            field.ClearEventBit(npc_bit.BACK_DOOR_ARVIS_HOUSE),
            field.ClearEventBit(npc_bit.SOLDIER_DOORWAY_ARVIS_HOUSE),
        )

        if self.args.no_free_heals:
            # Initialize the Narshe school bucket drink counter to 3 drinks.
            # Two event bits encode the remaining drinks: (SCHOOL_LIMITED_HEALS_1,
            # SCHOOL_LIMITED_HEALS_2) = (1,1)=3, (1,0)=2, (0,1)=1, (0,0)=0.
            space.write(
                field.SetEventBit(event_bit.SCHOOL_LIMITED_HEALS_1),
                field.SetEventBit(event_bit.SCHOOL_LIMITED_HEALS_2),
            )

    def mod(self):
        self.terra_elder_scene_mod()
        self.security_checkpoint_mod()
        self.shop_mod()

        if self.args.no_free_heals:
            self.limited_heals()

    def end_terra_scenario(self):
        # delete the end of terra's scenario event in arvis' house
        self.maps.delete_event(0x01e, 66, 35)

        # also put a return at the beginning of it just to be safe
        space = Reserve(0xcb3fa, 0xcb3ff, "banon's party reaches end in 3 scenarios", field.NOP())
        space.write(field.Return())

    def terra_elder_scene_mod(self):
        space = Reserve(0xc7083, 0xc7096, "narshe wob left trigger scene where terra agrees to open sealed gate", field.NOP())
        space.write(field.Return())
        space = Reserve(0xc7097, 0xc70aa, "narshe wob right trigger scene where terra agrees to open sealed gate", field.NOP())
        space.write(field.Return())

        # NOTE: the end of this space is where the soldiers are removed from imperial base near sealed gate
        space = Reserve(0xc70ab, 0xc72b9, "narshe wob scene where terra agrees to open sealed gate", field.NOP())
        space.write(field.Return())

    def security_checkpoint_mod(self):
        # remove explanation event and use the 0x2d8 flag bit for objective condition instead
        space = Reserve(0xcda09, 0xcda0f, "narshe wob security checkpoint explanation", field.NOP())
        space.write(field.Return())

        Free(0xcda10, 0xcda49)  # explanation event

        src = [
            Read(0xce3fa, 0xce3fd), # set first checkpoint event word to 0

            # return if checkpoint event not started (i.e. came in from the exit)
            field.ReturnIfEventBitClear(event_bit.multipurpose_map(0)),

            field.SetEventBit(event_bit.FINISHED_NARSHE_CHECKPOINT),
            field.CheckObjectives(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "narshe wob security checkpoint check objectives")
        check_objectives = space.start_address

        space = Reserve(0xce3fa, 0xce3fd, "narshe wob security checkpoint clear first event word", field.NOP())
        space.write(
            field.Call(check_objectives),
        )

    def shop_mod(self):
        # do not change shops after defeating cranes, always use ones after cranes
        space = Reserve(0xcd253, 0xcd258, "narshe wob weapon shop defeated cranes branch")
        space.add_label("INVOKE_SHOP", 0xcd25c)
        space.write(
            field.Branch("INVOKE_SHOP"),
        )
        space = Reserve(0xcd268, 0xcd26d, "narshe wob armor shop defeated cranes branch")
        space.add_label("INVOKE_SHOP", 0xcd271)
        space.write(
            field.Branch("INVOKE_SHOP"),
        )
        space = Reserve(0xcd27d, 0xcd282, "narshe wob relic shop defeated cranes branch")
        space.add_label("INVOKE_SHOP", 0xcd286)
        space.write(
            field.Branch("INVOKE_SHOP"),
        )
        space = Reserve(0xcd292, 0xcd297, "narshe wob item shop defeated cranes branch")
        space.add_label("INVOKE_SHOP", 0xcd29b)
        space.write(
            field.Branch("INVOKE_SHOP"),
        )

    def limited_heals(self):
        """Limit the Narshe school heal bucket to 3 uses (gated by -nfh).

        Two event bits track remaining drinks: (SCHOOL_LIMITED_HEALS_1,
        SCHOOL_LIMITED_HEALS_2) = (1,1)=3, (1,0)=2, (0,1)=1, (0,0)=0. The bits
        are initialized to (1,1) in ``init_event_bits`` when -nfh is active.
        """
        school_map_id = 0x068
        pot_heal_address = 0xc33ae

        three_id = 1470
        two_id = 1469
        one_id = 1468
        empty_id = 1467

        self.dialogs.set_text(three_id, "Drink from the bucket?<line>(3 drinks left)<line><choice> Yes<line><choice> No<end>")
        self.dialogs.set_text(two_id, "Drink from the bucket?<line>(2 drinks left)<line><choice> Yes<line><choice> No<end>")
        self.dialogs.set_text(one_id, "Drink from the bucket?<line>(1 drink left)<line><choice> Yes<line><choice> No<end>")
        self.dialogs.set_text(empty_id, "The bucket is empty.<end>")

        drink_src = [
            field.BranchIfEventBitClear(event_bit.SCHOOL_LIMITED_HEALS_1, "TOP_CLEAR"),
            field.BranchIfEventBitClear(event_bit.SCHOOL_LIMITED_HEALS_2, "TWO_DRINKS"),
            # (1,1) = 3 drinks
            field.DialogBranch(three_id, dest1="DRINK_3_TO_2", dest2="RETURN"),
            "TWO_DRINKS",
            # (1,0) = 2 drinks
            field.DialogBranch(two_id, dest1="DRINK_2_TO_1", dest2="RETURN"),
            "TOP_CLEAR",
            field.BranchIfEventBitClear(event_bit.SCHOOL_LIMITED_HEALS_2, "EMPTY"),
            # (0,1) = 1 drink
            field.DialogBranch(one_id, dest1="DRINK_1_TO_0", dest2="RETURN"),
            "EMPTY",
            # (0,0) = 0 drinks
            field.Dialog(empty_id),
            "RETURN",
            field.Return(),

            # 3 -> 2 drinks: (1,1) -> (1,0), clear bottom
            "DRINK_3_TO_2",
            field.ClearEventBit(event_bit.SCHOOL_LIMITED_HEALS_2),
            field.Branch("HEAL"),
            # 2 -> 1 drinks: (1,0) -> (0,1), clear top, set bottom
            "DRINK_2_TO_1",
            field.ClearEventBit(event_bit.SCHOOL_LIMITED_HEALS_1),
            field.SetEventBit(event_bit.SCHOOL_LIMITED_HEALS_2),
            field.Branch("HEAL"),
            # 1 -> 0 drinks: (0,1) -> (0,0), clear bottom
            "DRINK_1_TO_0",
            field.ClearEventBit(event_bit.SCHOOL_LIMITED_HEALS_2),
            # fallthrough
            "HEAL",
            field.Call(pot_heal_address),
            field.Return(),
        ]
        space = Write(Bank.CC, drink_src, "Limited use pot heal")

        pot_npc_id = 0x12
        pot_npc = self.maps.get_npc(school_map_id, pot_npc_id)
        pot_npc.event_address = space.start_address - EVENT_CODE_START
