# shared implementation of the asm-based objective conditions
# (see _battle_condition.py and _menu_condition.py for the public variants)
#
# the battle and menu variants must remain distinct classes even though the
# generated code is identical: _CachedFunction caches written routines per
# class, and each variant must write its own copy of a routine. module
# subclasses only set `condition_type`, used in the space descriptions

from memory.space import Bank, Write
import instruction.asm as asm
from objectives._cached_function import _CachedFunction

import data.event_bit as event_bit
import data.battle_bit as battle_bit
import data.event_word as event_word

class _Condition(_CachedFunction, asm.JSR):
    condition_type = None # "battle" or "menu", set by module subclasses

    def __init__(self, *args, **kwargs):
        _CachedFunction.__init__(self, *args, **kwargs)
        asm.JSR.__init__(self, self.address(*args, **kwargs), asm.ABS)

class _BitCondition(_Condition):
    def write(self, address, bit, true, false):
        if true is None:
            true = []
        if false is None:
            false = []

        src = [
            asm.LDA(address, asm.ABS),
            asm.AND(2 ** bit, asm.IMM8),
            asm.BEQ("FALSE"),

            true,
            asm.RTS(),

            "FALSE",
            false,
            asm.RTS(),
        ]
        return Write(Bank.F0, src, f"{self.condition_type} bit condition {hex(address)} {hex(bit)}")

class _EventBitCondition(_BitCondition):
    def write(self, bit, true = None, false = None):
        return super().write(event_bit.address(bit), event_bit.bit(bit), true, false)

class _BattleBitCondition(_BitCondition):
    def write(self, bit, true = None, false = None):
        return super().write(battle_bit.address(bit), battle_bit.bit(bit), true, false)

class _CharacterCondition(_BitCondition):
    def write(self, character, true = None, false = None):
        return super().write(event_bit.address(event_bit.character_recruited(character)), character % 8, true, false)

class _EsperCondition(_BitCondition):
    def write(self, esper, true = None, false = None):
        return super().write(0x1a69 + esper // 8, esper % 8, true, false)

class _EventWordCondition(_Condition):
    def write(self, word, count, ge = None, lt = None):
        if ge is None:
            ge = []
        if lt is None:
            lt = []

        src = [
            asm.LDA(event_word.address(word), asm.ABS),
            asm.CMP(count, asm.IMM8),
            asm.BLT("LT"),

            ge,
            asm.RTS(),

            "LT",
            lt,
            asm.RTS(),
        ]
        return Write(Bank.F0, src, f"{self.condition_type} word condition {hex(word)} {count}")
