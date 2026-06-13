from data.shop import Shop
from data.structures import DataArray
from constants.items import id_name, name_id

OFFSET = 64   # OFFSETs up to 1212 should be ok...
PACK_SIZE_TABLE_START = 0x47fa8 + OFFSET      # 8 bytes per shop * 86 shops = 688 bytes
PACK_SIZE_TABLE_END   = 0x48257 + OFFSET
TRACK_PTR_TABLE_START = 0x48258 + OFFSET      # 2 bytes per shop * 86 shops = 172 bytes
TRACK_PTR_TABLE_END   = 0x48303 + OFFSET

class Shops():
    DATA_START = 0x47ac0
    DATA_END = 0x47f3f
    DATA_SIZE = 9

    def __init__(self, rom, args, items):
        self.rom = rom
        self.args = args
        self.items = items

        self.shop_data = DataArray(self.rom, self.DATA_START, self.DATA_END, self.DATA_SIZE)

        self.shops = []
        self.all_shops = [] # includes inaccesible shops (used for writing out data)
        self.type_shops = {Shop.WEAPON : [], Shop.ARMOR : [], Shop.ITEM : [], Shop.RELIC : [], Shop.VENDOR : []}

        for shop_index in range(len(self.shop_data)):
            shop = Shop(shop_index, self.shop_data[shop_index])
            self.all_shops.append(shop)

            # exclude shops that are inaccesible from shops and type_shops lists
            if shop.type != Shop.EMPTY and shop.accessible():
                self.shops.append(shop)
                self.type_shops[shop.type].append(shop)

    def __len__(self):
        return len(self.shops)

    def shuffle(self):
        # shuffle all shops (except empty ones)
        # keeps weapons in weapon shops, armors in armor shops, items in item shops, etc...

        # to prevent duplicates, get list of items for each shop type and sort it by their frequency
        # picking least frequent last prevents ending up with multiple of same item and only one shop to distribute them to
        # randomly pick shops of the given type until find one without the item and add it
        # once the shop has as many items as its shuffled count remove it from the available pool

        type_items = {Shop.WEAPON : [], Shop.ARMOR : [], Shop.ITEM : [], Shop.RELIC : [], Shop.VENDOR : []}
        for shop in self.shops:
            for item_index in range(shop.item_count):
                type_items[shop.type].append(shop.items[item_index])

        # shuffle vendor shops with item shops
        # add vendor shops to list of item shops and vendor shop inventories to list of items in item shops
        type_shops = {
            Shop.WEAPON : self.type_shops[Shop.WEAPON],
            Shop.ARMOR  : self.type_shops[Shop.ARMOR],
            Shop.ITEM   : self.type_shops[Shop.ITEM] + self.type_shops[Shop.VENDOR],
            Shop.RELIC  : self.type_shops[Shop.RELIC],
        }
        type_items[Shop.ITEM].extend(type_items[Shop.VENDOR])

        import random
        import collections
        for shop_type in range(1, Shop.SHOP_TYPE_COUNT - 1): # skip EMPTY and VENDOR shop types
            frequencies = collections.Counter(item for item in type_items[shop_type])
            items = sorted(type_items[shop_type], key = lambda item : frequencies[item])

            # get item counts and pool of available shops and clear the inventory they have now
            item_counts = []
            shop_indices = []
            for shop_index, shop in enumerate(type_shops[shop_type]):
                item_counts.append(shop.item_count)
                shop.clear()
                shop_indices.append(shop_index)

            random.shuffle(item_counts)

            while len(items) > 0:
                shop_index = random.choice(shop_indices)
                shop = type_shops[shop_type][shop_index]
                if not shop.contains(items[-1]):
                    item = items.pop()
                    shop.append(item)
                    if shop.item_count == item_counts[shop_index]:
                        shop_indices.remove(shop_index)

    def random_tiered(self):
        def get_item(item_type, exclude = None):
            import random
            from utils.weighted_random import weighted_random
            from data.shop_item_tiers import tiers, weights

            if exclude is None:
                exclude = []

            random_tier = weighted_random(weights[item_type])
            possible_items = [item_id for item_id in tiers[item_type][random_tier] if item_id not in exclude]
            while not possible_items:
                # no more items left in chosen tier, pick a different one
                weights[item_type][random_tier] = 0
                assert(any(weights[item_type])) # ensure tier left which has not been tried

                random_tier = weighted_random(weights[item_type])
                possible_items = [item_id for item_id in tiers[item_type][random_tier] if item_id not in exclude]

            random_item_index = random.randrange(len(possible_items))
            return possible_items[random_item_index]

        self.shuffle()

        exclude = self.items.get_excluded()
        for shop in self.shops:
            items_added = []
            for item_index in range(shop.item_count):
                item_type = self.items.get_type(shop.items[item_index])

                random_item_id = get_item(item_type, items_added + exclude)
                shop.items[item_index] = random_item_id
                items_added.append(random_item_id)

    def shuffle_random(self):
        self.shuffle()
        if self.args.shop_inventory_shuffle_random_percent == 0:
            return

        total_item_count = 0
        for shop in self.shops:
            total_item_count += shop.item_count

        import random
        random_percent = self.args.shop_inventory_shuffle_random_percent / 100.0
        num_random_items = int(total_item_count * random_percent)
        sorted_random_indices = sorted(random.sample(range(total_item_count), num_random_items), reverse = True)

        total_index = 0
        for shop in self.shops:
            for item_index in range(shop.item_count):
                if total_index == sorted_random_indices[-1]:
                    item_type = self.items.get_type(shop.items[item_index])
                    shop.items[item_index] = self.items.get_random(shop.items.copy(), item_type)

                    sorted_random_indices.pop()
                    if not sorted_random_indices:
                        return
                total_index += 1

    def clear_inventories(self):
        for shop in self.shops:
            shop.clear()

    def assign_dried_meats(self):
        dried_meat_id = self.items.get_id("Dried Meat")
        dried_meat_type = self.items.get_type(dried_meat_id)
        excluded_shops = ["Figaro Castle WOR (Left)","Figaro Castle WOR (Right)","Phantom Train"]

        dried_meat_shops = []
        no_dried_meat_shops = []

        for shop in self.shops:
            if shop.name() in excluded_shops:
                if shop.contains(dried_meat_id):
                    shop.remove(dried_meat_id)
            elif shop.contains(dried_meat_id):
                dried_meat_shops.append(shop)
            elif shop.type == Shop.ITEM or shop.type == Shop.VENDOR:
                no_dried_meat_shops.append(shop)
        number_shops_with_dried_meat = len(dried_meat_shops)

        import random
        if number_shops_with_dried_meat > self.args.shop_dried_meat:
            # too many shops have dried meat, randomly remove extras
            for index in range(self.args.shop_dried_meat, number_shops_with_dried_meat):
                random_shop = random.choice(dried_meat_shops)
                random_shop.remove(dried_meat_id)
                dried_meat_shops.remove(random_shop)
        elif number_shops_with_dried_meat < self.args.shop_dried_meat:
            # too few shops have dried meat, choose random shops and
            # add a dried meat if space, otherwise replace a random item with dried meat
            for index in range(number_shops_with_dried_meat, self.args.shop_dried_meat):
                if not no_dried_meat_shops:
                    break
                random_shop = random.choice(no_dried_meat_shops)

                if not random_shop.full():
                    random_shop.append(dried_meat_id)
                else:
                    random_index = random.randrange(random_shop.item_count)
                    random_shop.items[random_index] = dried_meat_id
                no_dried_meat_shops.remove(random_shop)
                dried_meat_shops.append(random_shop)


    def remove_excluded_items(self):
        exclude = self.items.get_excluded()
        if self.args.shops_no_breakable_rods:
            for rod in self.items.BREAKABLE_RODS:
                exclude.append(rod)
        if self.args.shops_no_elemental_shields:
            for shield in self.items.ELEMENTAL_SHIELDS:
                exclude.append(shield)
        if self.args.shops_no_super_balls:
            exclude.append(self.items.get_id("Super Ball"))
        if self.args.shops_no_exp_eggs:
            exclude.append(self.items.get_id("Exp. Egg"))
        if self.args.shops_no_illuminas:
            exclude.append(self.items.get_id("Illumina"))

        for shop in self.shops:
            for item in exclude:
                if shop.contains(item):
                    shop.remove(item)

    # ROM addresses for limited inventory data (in unused space at C47FA8-C487BF)
    SHOP_COUNT            = 86            # Total shops in ROM (including inaccessible)

    # SNES addresses (for ASM long addressing)
    PACK_SIZE_TABLE_SNES  = 0xc00000 + PACK_SIZE_TABLE_START
    TRACK_PTR_TABLE_SNES  = 0xc00000 + TRACK_PTR_TABLE_START

    # Save RAM regions for limited inventory tracking bytes (1 byte per shop, 8 item slots as bits).
    # Non-contiguous regions of unused SRAM, totalling 103 bytes (enough for all 86 shops).
    SRAM_REGIONS = [
        (0x1CF8, 0x1D27),   # SwdTech names (unused in English version), 48 bytes
        (0x1DC9, 0x1DCE),   # Unused battle variable bytes, 6 bytes
        (0x1DD6, 0x1DDC),   # Unused battle variable bytes, 7 bytes
        (0x1E1D, 0x1E3F),   # Previously used SLI range, 35 bytes
        (0x1FF7, 0x1FFD),   # Unused bit range before checksum, 7 bytes
    ]

    # Special relics that should always be sold as singles
    SPECIAL_RELICS = {
        name_id["Economizer"], name_id["Offering"], name_id["Hero Ring"],
        name_id["Dragon Horn"], name_id["Gem Box"], name_id["Merit Award"],
        name_id["Exp. Egg"], name_id["Marvel Shoes"], name_id["Ribbon"],
        name_id["Genji Glove"], name_id["Gauntlet"], name_id["Moogle Charm"],
    }

    # Basic healing items: larger packs (3-10)
    BASIC_HEALING = {
        name_id["Tonic"], name_id["Potion"], name_id["Fenix Down"],
        name_id["Revivify"], name_id["Antidote"], name_id["Eyedrop"],
        name_id["Soft"], name_id["Echo Screen"], name_id["Green Cherry"],
        name_id["Sleeping Bag"], name_id["Tincture"],
    }

    # High healing items: moderate packs (1-3)
    HIGH_HEALING = {
        name_id["X-Potion"], name_id["Ether"],
        name_id["X-Ether"], name_id["Tent"], name_id["Remedy"],
    }

    def get_pack_size(self, item_id):
        """Determine pack size for an item based on its type/category."""
        import random
        from constants.items import (WEAPONS, SHIELDS, HELMETS, ARMORS, TOOLS, STARS, SKEANS, RELICS,
                                     junk_weapons, id_name, junk_armor)

        if item_id == Shop.NO_ITEM:
            return 0

        # Throwables
        if item_id in STARS or item_id in SKEANS:
            if item_id == name_id['Shuriken']:
                return random.randint(5, 30)  # Allow more shuriken, they're relatively weak
            else:
                return random.randint(3, 10)

        # Other weapons, shields, helmets, armors, tools: always singles
        if item_id in WEAPONS or item_id in SHIELDS or item_id in HELMETS or \
           item_id in ARMORS or item_id in TOOLS:
            if id_name[item_id] in junk_weapons:
                return random.randint(2, 8)      # Allow more, they're probably just throwables
            elif id_name[item_id] in junk_armor:
                return random.randint(2, 4)      # Allow more, they're probably just backup
            else:
                return 1

        # Relics: 1-4, except special relics which are singles
        if item_id in RELICS:
            if item_id in self.SPECIAL_RELICS:
                return 1
            return random.randint(1, 4)

        # Basic healing items: 1-5 for Fenix Down, 3-8 for everything else
        if item_id in self.BASIC_HEALING:
            if item_id == name_id["Fenix Down"]:
                return random.randint(1, 5)
            else:
                return random.randint(3, 8)

        # High healing items: 1-3
        if item_id in self.HIGH_HEALING:
            return random.randint(1, 3)

        # Elixir, Megalixir: singles
        if item_id in (name_id["Elixir"], name_id["Megalixir"]):
            return 1

        # Default for other consumables (Smoke Bomb, Warp Stone, Dried Meat, Super Ball, etc.)
        return random.randint(1, 3)

    def compute_pack_sizes(self):
        """Compute pack sizes for all items in all shops."""
        self.pack_sizes = {}
        for shop in self.all_shops:
            sizes = []
            for item_id in shop.items:
                sizes.append(self.get_pack_size(item_id))
            self.pack_sizes[shop.id] = sizes

    def _update_pack_sizes_for_shops(self, *shops):
        """Recompute pack sizes for specific shops after item changes.

        Called when items are swapped/replaced after initial compute_pack_sizes().
        No-op if pack_sizes hasn't been computed yet (limited inventory not active).
        """
        if not hasattr(self, 'pack_sizes'):
            return
        for shop in shops:
            sizes = []
            for item_id in shop.items:
                sizes.append(self.get_pack_size(item_id))
            self.pack_sizes[shop.id] = sizes

    def enable_limited_shops(self, shop_ids):
        """Assign SRAM tracking bytes to shops and patch new-game init to clear them.

        Args:
            shop_ids: List of shop IDs to enable limited inventory for.
        """
        # Build a flat list of available SRAM addresses from the non-contiguous regions
        sram_addresses = []
        for start, end in self.SRAM_REGIONS:
            for addr in range(start, end + 1):
                sram_addresses.append(addr)

        self.limited_shop_ids = shop_ids
        self.limited_shop_sram = {}
        unique_shop_ids = sorted(set(shop_ids))
        for i, shop_id in enumerate(unique_shop_ids):
            if i >= len(sram_addresses):
                print(f"Warning: Too many limited shops ({len(unique_shop_ids)}), max {len(sram_addresses)}. Skipping shop {shop_id}")
                break
            self.limited_shop_sram[shop_id] = sram_addresses[i]

        # Patch new-game initialization to zero all SLI SRAM regions.
        # The vanilla treasure-chest zeroing subroutine at C0/BB18 zeroes $1E40-$1E6F.
        # We extend it to also cover $1E1D-$1E3F (contiguous with chests), and write
        # a new wrapper subroutine that zeroes the other non-contiguous regions first,
        # then falls through to the (extended) chest zeroing.
        from memory.space import Bank, Reserve, Write
        import instruction.asm as asm

        # Step 1: Extend the chest-zeroing loop to also cover $1E1D-$1E3F.
        # Vanilla: STZ $1E40,X / CPX #$0030 → zeroes $1E40..$1E6F
        # Patched: STZ $1E1D,X / CPX #$0053 → zeroes $1E1D..$1E6F
        space = Reserve(0x00bb1b, 0x00bb1b, "SLI tracking: lower chest-zeroing base to $1E1D")
        space.write(0x1d)
        space = Reserve(0x00bb1f, 0x00bb1f, "SLI tracking: extend chest-zeroing count to $53")
        space.write(0x53)

        # Step 2: Write a new subroutine that zeroes the non-contiguous SRAM regions
        # that fall outside the $1E1D-$1E6F range, then jumps to the original
        # chest-zeroing subroutine (BB18) which handles $1E1D-$1E6F.
        extra_regions = [(s, e) for s, e in self.SRAM_REGIONS
                         if not (s >= 0x1E1D and e <= 0x1E3F)]

        src = []
        for start, end in extra_regions:
            size = end - start + 1
            if size >= 8:
                # Use a loop for larger regions
                src.extend([
                    asm.LDX(0x0000, asm.IMM16),
                    f"LOOP_{start:04X}",
                    asm.STZ(start, asm.ABS_X),
                    asm.INX(),
                    asm.CPX(size, asm.IMM16),
                    asm.BNE(f"LOOP_{start:04X}"),
                ])
            else:
                # Individual STZ for small regions
                for addr in range(start, end + 1):
                    src.append(asm.STZ(addr, asm.ABS))

        # Jump to the original (patched) chest-zeroing subroutine.
        # Its RTS will return to the caller at C0/BE90.
        src.append(asm.JMP(0xBB18, asm.ABS))

        space = Write(Bank.C0, src, "SLI tracking: zero non-contiguous SRAM regions on new game")
        new_zeroing_addr = space.start_address

        # Step 3: Redirect the JSR $BB18 at C0/BE8D to our new subroutine.
        # C0/BE8D: 20 18 BB → 20 <lo> <hi>
        space = Reserve(0x00be8e, 0x00be8f, "SLI tracking: redirect chest-zeroing JSR to new sub")
        space.write((new_zeroing_addr & 0xffff).to_bytes(2, "little"))

    def write_limited_inventory_data(self):
        """Write pack size table and tracking pointer table to ROM."""
        from memory.space import Reserve

        # Write pack sizes: 8 bytes per shop (1 byte per item slot)
        space = Reserve(PACK_SIZE_TABLE_START, PACK_SIZE_TABLE_END,
                       "shop limited inventory pack sizes")
        for shop_id in range(self.SHOP_COUNT):
            if shop_id in self.pack_sizes:
                for size in self.pack_sizes[shop_id]:
                    space.write(size)
            else:
                for _ in range(8):
                    space.write(0)

        # Write tracking pointers: 2 bytes per shop (Save RAM address or 0x0000)
        space = Reserve(TRACK_PTR_TABLE_START, TRACK_PTR_TABLE_END,
                       "shop limited inventory tracking pointers")
        for shop_id in range(self.SHOP_COUNT):
            if hasattr(self, 'limited_shop_sram') and shop_id in self.limited_shop_sram:
                addr = self.limited_shop_sram[shop_id]
                space.write(addr.to_bytes(2, "little"))
            else:
                space.write((0).to_bytes(2, "little"))

    # Direct page addresses used for limited inventory compaction buffers.
    # These addresses are verified unused during shop menu operations (Bank C3).
    # $78-$7F: compact_items (available items packed into first N slots, rest $FF)
    # $B8-$BF: slot_map (display position -> original shop slot index)
    # $25: compact mode flag (0 = normal shop, 1 = limited shop with valid buffers)
    # $30: limited mode flag / pack size for order menu quantity lock
    COMPACT_ITEMS_DP  = 0x78   # 8 bytes: $78-$7F
    SLOT_MAP_DP       = 0xb8   # 8 bytes: $B8-$BF
    COMPACT_FLAG_DP   = 0x25   # 1 byte
    LIMITED_MODE_DP   = 0x30   # 1 byte (pack size during buy, or 0 for unlimited)

    def disable_buy_if_empty(self):
        # in shops with no items scrolling breaks and you can buy "Empty" items
        # this function will not allow the buy menu to be selected if the shop type is empty
        from memory.space import Bank, Reserve, Write
        import instruction.asm as asm

        if self.args.shop_limited_inventory:
            # Write the compact_init subroutine first (builds compacted item list
            # for limited shops so purchased items don't leave gaps in the menu)
            compact_src = self._build_compact_init_asm()
            compact_space = Write(Bank.C3, compact_src, "limited inventory: compact init subroutine")
            compact_init_addr = compact_space.start_address

            src = [
                # Check if first ROM item is empty (catches genuinely empty shops)
                asm.LDX(0x67, asm.DIR),         # x = shop index
                asm.INX(),                      # skip shop flags byte
                asm.LDA(0xc47ac0, asm.LNG_X),   # load first item byte
                asm.CMP(0xff, asm.IMM8),        # is first item slot empty?
                asm.BNE("OPEN_BUY_MENU"),       # branch if not
                asm.JSR(0xb66f, asm.ABS),       # buzzer
                asm.JMP(0xb760, asm.ABS),       # return to main shop menu

                "OPEN_BUY_MENU",
                asm.STZ(self.LIMITED_MODE_DP, asm.DIR),  # clear limited inventory mode flag ($30)
                asm.JSR(compact_init_addr, asm.ABS),  # build compacted item list
                # For limited shops, check if all items have been purchased
                asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),
                asm.BEQ("GO"),                  # normal shop, skip check
                asm.LDA(self.COMPACT_ITEMS_DP, asm.DIR),  # first compact item
                asm.CMP(0xff, asm.IMM8),        # all purchased?
                asm.BNE("GO"),
                asm.JSR(0xb66f, asm.ABS),       # buzzer
                asm.JMP(0xb760, asm.ABS),       # return to main shop menu
                "GO",
                asm.JMP(0xb7a3, asm.ABS),       # normal buy menu initialization
            ]
        else:
            src = [
                asm.LDX(0x67, asm.DIR),         # x = shop index
                asm.INX(),                      # skip shop flags byte
                asm.LDA(0xc47ac0, asm.LNG_X),   # load first item byte
                asm.CMP(0xff, asm.IMM8),        # is first item slot empty?
                asm.BNE("OPEN_BUY_MENU"),       # branch if not
                asm.JSR(0xb66f, asm.ABS),       # buzzer
                asm.JMP(0xb760, asm.ABS),       # return to main shop menu

                "OPEN_BUY_MENU",
                asm.STZ(self.LIMITED_MODE_DP, asm.DIR),  # clear limited inventory mode flag ($30)
                asm.JMP(0xb7a3, asm.ABS),        # normal buy menu initialization
            ]

        space = Write(Bank.C3, src, "shops handle buy menu empty shop")
        check_empty_shop = space.start_address

        space = Reserve(0x3b79a, 0x3b79b, "shops initialize buy menu address")
        space.write(
            (check_empty_shop & 0xffff).to_bytes(2, "little"),
        )

        if self.args.shop_limited_inventory:
            # Hook JSR $B986 at B7BC so compact_init runs before every buy list
            # redraw (including post-purchase returns, not just first entry).
            # B7BC is reached both from initial buy menu setup (B7A3 path) and
            # from post-purchase return (state 28 → B7B3 → B7BC).
            redraw_src = [
                asm.JSR(compact_init_addr, asm.ABS),  # rebuild compact buffers

                # If limited shop and all items now bought, exit to main shop menu
                asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),  # $25 compact mode?
                asm.BEQ("DRAW"),                       # normal shop, just draw
                asm.LDA(self.COMPACT_ITEMS_DP, asm.DIR), # first compact item
                asm.CMP(0xff, asm.IMM8),               # all purchased?
                asm.BNE("DRAW"),                       # still have items
                # All items bought: pop the JSR return address and exit to main menu
                asm.PLA(),                             # discard return address low byte
                asm.PLA(),                             # discard return address high byte
                asm.JMP(0xb760, asm.ABS),              # return to main shop menu

                "DRAW",
                asm.JMP(0xb986, asm.ABS),              # draw all text (original target)
            ]
            redraw_space = Write(Bank.C3, redraw_src, "limited inventory: redraw trampoline")
            redraw_addr = redraw_space.start_address

            # Replace address in JSR $B986 at B7BC (opcode at B7BC, address at B7BD-B7BE)
            space = Reserve(0x3b7bd, 0x3b7be, "shop buy menu draw text hook")
            space.write(
                (redraw_addr & 0xffff).to_bytes(2, "little"),
            )

    def _build_compact_init_asm(self):
        """Build ASM for the compact_init subroutine.

        Scans all 8 shop item slots, skips empty and purchased items,
        and packs available items into $78-$7F with a slot mapping at $B8-$BF.
        Sets $25 = 1 if this is a limited shop (compact buffers valid).

        Register contract: preserves X, Y. Uses A freely.
        Entry: 8-bit A, 16-bit X/Y (standard menu state).
        """
        import instruction.asm as asm

        return [
            # Save caller's registers
            asm.PHX(),
            asm.PHY(),

            # Clear compact mode flag
            asm.STZ(self.COMPACT_FLAG_DP, asm.DIR),  # $25 = 0

            # Fill compact_items ($78-$7F) with $FF
            asm.LDA(0xff, asm.IMM8),
            asm.LDX(0x0007, asm.IMM16),
            "CLEAR_ITEMS",
            asm.STA(self.COMPACT_ITEMS_DP, asm.DIR_X),  # STA $78,X
            asm.DEX(),
            asm.BPL("CLEAR_ITEMS"),

            # Fill slot_map ($B8-$BF) with $FF
            asm.LDX(0x0007, asm.IMM16),
            "CLEAR_MAP",
            asm.STA(self.SLOT_MAP_DP, asm.DIR_X),       # STA $B8,X
            asm.DEX(),
            asm.BPL("CLEAR_MAP"),

            # Check if this is a limited shop
            asm.REP(0x20),                              # 16-bit A
            asm.LDA(0x7e0201, asm.LNG),                 # shop number
            asm.AND(0x00ff, asm.IMM16),                  # clean high byte
            asm.ASL(),                                   # *2 for pointer table
            asm.TAX(),                                   # X = table offset
            asm.LDA(self.TRACK_PTR_TABLE_SNES, asm.LNG_X),  # tracking pointer
            asm.TAX(),                                   # X = SRAM address (or 0)
            asm.SEP(0x20),                               # 8-bit A
            # Z flag from TAX: set if pointer was 0 (normal shop)
            asm.BEQ("DONE"),

            # Limited shop: set flag and load tracking byte
            asm.LDA(0x01, asm.IMM8),
            asm.STA(self.COMPACT_FLAG_DP, asm.DIR),      # $25 = 1
            asm.LDA(0x7e0000, asm.LNG_X),               # tracking byte from SRAM
            asm.STA(0x36, asm.DIR),                      # save tracking byte (temp, $36 is unused)

            # Scan slots: Y = scan_slot (0-7), X = write_pos (0-N)
            asm.LDX(0x0000, asm.IMM16),                  # write_pos = 0
            asm.LDY(0x0000, asm.IMM16),                  # scan_slot = 0

            "SCAN",
            # Load item from ROM at scan_slot Y
            # ROM index = scan_slot + $67 (16-bit shop base) + 1
            asm.PHX(),                                   # save write_pos
            asm.REP(0x20),                               # 16-bit A
            asm.TYA(),                                   # A = scan_slot (16-bit, 0-7)
            asm.CLC(),
            asm.ADC(0x67, asm.DIR),                      # A += shop base index ($67-$68, 16-bit)
            asm.INC(),                                   # A += 1 (skip flags byte)
            asm.TAX(),                                   # X = ROM data offset
            asm.SEP(0x20),                               # 8-bit A
            asm.LDA(0xc47ac0, asm.LNG_X),               # load item from ROM
            asm.PLX(),                                   # restore write_pos

            # Check if empty in ROM
            asm.CMP(0xff, asm.IMM8),
            asm.BEQ("NEXT"),                             # skip empty slots

            # Save item ID
            asm.STA(0x37, asm.DIR),                      # temp item ID ($37 is unused)

            # Check tracking bit for scan_slot Y
            asm.LDA(0x36, asm.DIR),                      # tracking byte
            asm.PHY(),                                   # save scan_slot
            asm.CPY(0x0000, asm.IMM16),                  # slot 0?
            asm.BEQ("TESTBIT"),                          # no shifting needed
            "SHIFT",
            asm.LSR(),                                   # shift tracking byte right
            asm.DEY(),                                   # decrement counter
            asm.BNE("SHIFT"),                            # loop until done
            "TESTBIT",
            asm.PLY(),                                   # restore scan_slot
            asm.AND(0x01, asm.IMM8),                     # test lowest bit
            asm.BNE("NEXT"),                             # bit set = purchased, skip

            # Item is available: add to compact list
            asm.LDA(0x37, asm.DIR),                      # item ID
            asm.STA(self.COMPACT_ITEMS_DP, asm.DIR_X),   # compact_items[write_pos] ($78,X)
            asm.TYA(),                                   # A = scan_slot
            asm.STA(self.SLOT_MAP_DP, asm.DIR_X),        # slot_map[write_pos] ($B8,X)
            asm.INX(),                                   # write_pos++

            "NEXT",
            asm.INY(),                                   # scan_slot++
            asm.CPY(0x0008, asm.IMM16),                  # done 8 slots?
            asm.BNE("SCAN"),                             # loop if not

            "DONE",
            asm.PLY(),                                   # restore caller's Y
            asm.PLX(),                                   # restore caller's X
            asm.RTS(),
        ]

    def mod(self):
        self.disable_buy_if_empty()

        if self.args.shop_inventory_shuffle_random:
            self.shuffle_random()
        elif self.args.shop_inventory_random_tiered:
            self.random_tiered()
        elif self.args.shop_inventory_empty:
            self.clear_inventories()

        self.assign_dried_meats()
        self.remove_excluded_items()

        # Compute pack sizes after inventory is finalized
        if self.args.shop_limited_inventory:
            self.compute_pack_sizes()
            all_shop_ids = [shop.id for shop in self.shops]
            self.enable_limited_shops(all_shop_ids)

    def log(self):
        from log import section_entries, format_option

        lentries = []
        rentries = []
        for shop_index, shop in enumerate(self.shops):
            limited = hasattr(self, 'limited_shop_sram') and shop.id in self.limited_shop_sram
            label = f"{shop.name()} {shop.get_type_string()}"
            if limited:
                label += " [Limited]"
            entry = [label]
            for item_index, item in enumerate(shop.items):
                if item != Shop.NO_ITEM:
                    item_name = self.items.get_name(item)
                    item_price = self.items.get_price(item)
                    if limited and shop.id in self.pack_sizes:
                        pack = self.pack_sizes[shop.id][item_index]
                        entry.append(format_option(f"{item_name} x{pack}", str(item_price * pack)))
                    else:
                        entry.append(format_option(item_name, str(item_price)))

            if shop_index % 2:
                rentries.append(entry)
            else:
                lentries.append(entry)

        section_entries("Shops", lentries, rentries)

    def write(self):
        if self.args.spoiler_log:
            self.log()

        for shop_index in range(len(self.all_shops)):
            self.shop_data[shop_index] = self.all_shops[shop_index].data()

        self.shop_data.write()

        if self.args.shop_limited_inventory:
            self.write_limited_inventory_data()

    def print(self):
        for shop in self.shops:
            shop.print()
