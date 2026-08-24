from memory.space import Bank, Reserve, Write
import instruction.asm as asm

# With probability-randomized commands (-comfr/-compr) a character's whole
# menu can be commands that are illegal while Imped (only Fight, Item,
# Magic, Revert, Mimic, Row, Def, Jump, X-Magic, Health and Shock carry
# the imp-usable bit in the CF/FE00 command info table).  The per-turn
# menu routine C2/527D then grays all four slots, and the C1 command
# window's cursor engine hangs: its row-validity check (C1/7A4E: bit 7 of
# the slot's second byte at the menu block) is consumed by three unbounded
# skip-invalid loops - the initial settle (C1/7AEF) and the second
# layout's up/down navigation (C1/7BE9 dec, C1/7BF3 inc) - which spin
# forever when zero rows are valid.  Vanilla can never produce that state
# because Fight and Item are always available.  Symptoms: menu
# drawn, hand cursor never placed, ATB stalled, battle hard-locked.
#
# Fix, preserving the gameplay rule that an Imped character may not use
# imp-illegal commands:
# 1. bound each loop: walk all four rows once around, exactly as vanilla
#    would; if none is valid, restore the row the cursor started on and
#    continue.  The hand position is only computed once per frame from
#    the final cursor memory (C1/7BB2/7C23), so the in-frame walk is
#    invisible: with any selectable row the result is bit-identical to
#    vanilla (including "wrap around and stay put" when the current row
#    is the only one), and with none the hand simply rests motionless on
#    the remembered row while the per-frame input handling keeps running,
#    so the player keeps their real options: Row/Def, L+R to run, and Y
#    to switch to another ready character.
# 2. vanilla has NO confirm-time validity check - the confirm path
#    (C1/7CC8) dispatches whatever the cursor rests on, because vanilla's
#    cursor can only ever rest on valid rows.  With a resting cursor that
#    invariant is gone, so both A-press sites (C1/7BAA, C1/7BFF) now
#    re-check the row via C1/7A4E and swallow the press when it is
#    invalid (the confirm click/state counters $96/$2F41 only advance on
#    a real confirm).

ROW_VALID = 0x7a4e      # C1: carry clear = cursor-memory row selectable
CURSOR_MEMORY = 0x890f  # C1: per-character remembered row, ,X = char index
CONFIRM = 0x7cc8        # C1: A-press command dispatch

def _scan(step):
    # step through all four rows looking for a selectable one; nothing
    # valid -> put the entry row back so the cursor never comes to rest
    # anywhere it did not start.  (An earlier version parked on row 0
    # after three tries, which briefly rested the cursor on the wrong
    # row whenever the only selectable row was the one the cursor
    # already occupied - the next frame's settle then walked it back,
    # so the hand visibly hopped.)  a is scratch (callers reload from
    # $04/$05); x = character index and y = menu base are preserved by
    # C1/7A4E.  C1/7A4E masks cursor memory to 0-3 on every call, so
    # the fourth step always re-tests the entry row itself.
    src = [
        asm.LDA(CURSOR_MEMORY, asm.ABS_X),
        asm.PHA(),                          # remember the entry row
    ]
    for _ in range(4):
        src += [
            step(CURSOR_MEMORY, asm.ABS_X),
            asm.JSR(ROW_VALID, asm.ABS),
            asm.BCC("FOUND"),
        ]
    src += [
        asm.PLA(),                          # no row selectable anywhere:
        asm.STA(CURSOR_MEMORY, asm.ABS_X),  # rest on the entry row
        asm.RTS(),
        "FOUND",
        asm.PLA(),                          # discard the saved row
        asm.RTS(),
    ]
    return src

def mod():
    import args
    if not args.commands_probability_mode:
        return

    inc_scan = Write(Bank.C1, _scan(asm.INC),
                     "command menu: bounded skip-invalid scan (inc)")
    dec_scan = Write(Bank.C1, _scan(asm.DEC),
                     "command menu: bounded skip-invalid scan (dec)")

    src = [
        asm.JSR(ROW_VALID, asm.ABS),    # carry set = row invalid: deny
        asm.BCS("DENY"),
        asm.INC(0x96, asm.DIR),         # displaced confirm click/state
        asm.INC(0x2f41, asm.ABS),       # increments (valid confirms only)
        "DENY",
        asm.RTS(),
    ]
    confirm_guard = Write(Bank.C1, src, "command menu: deny confirm on invalid row")

    # the three unbounded loops: INC/DEC $890F,X / JSR $7A4E / BCS back
    for addr, helper, name in ((0x17aef, inc_scan, "settle"),
                               (0x17be9, dec_scan, "nav up"),
                               (0x17bf3, inc_scan, "nav down/settle")):
        space = Reserve(addr, addr + 7, f"command menu {name}: bounded scan", asm.NOP())
        space.write(
            asm.JSR(helper.start_address, asm.ABS),
        )

    # both A-press sites: INC $96 / INC $2F41 / JMP $7CC8 becomes a guarded
    # confirm - carry set skips the dispatch, falling through to the
    # "A not pressed" handling exactly as if the press had not happened
    for addr in (0x17baa, 0x17bff):
        space = Reserve(addr, addr + 7, "command menu: guarded confirm")
        space.write(
            asm.JSR(confirm_guard.start_address, asm.ABS),
            asm.BCS("SKIP"),
            asm.JMP(CONFIRM, asm.ABS),
            "SKIP",
        )

mod()
