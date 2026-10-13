# level caps (-lc).
#
# hard cap (-lc LEVEL): lower battle's experience cap. C2/6235 adds battle
# experience and clamps the 24-bit total to the constant at C2/6276
# (15,000,000). setting it to the total for LEVEL lets a character reach LEVEL
# but never the total the level-up check (C2/606D) needs for LEVEL + 1. the
# experience table stays vanilla.
#
# soft cap (-lc MEAN WIDTH): rewrite the experience progression table so
# levels past MEAN cost far more experience. the table at ED/8220 holds 98
# 16-bit words; entry i is the experience needed to go from level i + 1 to
# level i + 2, divided by 8. the game never stores a total: battle (C2/606D),
# the menu (C3/60CA) and "set experience for level" (C0/A235) all sum the
# entries in 24 bits and multiply by 8.

import math

EXP_TABLE_START = 0x2d8220
EXP_TABLE_END = 0x2d82e3
EXP_TABLE_COUNT = 98

STEP_MAX = 0xffff               # 524,280 experience per level, the most one entry can hold
BATTLE_EXP_CAP = 15000000       # C2/6276: battle never raises experience past this
BATTLE_EXP_CAP_START = 0x026276 # the cap's 3 bytes (24-bit little endian)
BATTLE_EXP_CAP_END = 0x026278
SUM_LIMIT = 1 << 21             # summed entries at which the 24-bit total (x 8) wraps around

def hard_cap_experience(table, cap):
    # battle experience cap for a hard cap at level `cap`: exactly the total for
    # that level, so it can be reached and the next level never can
    return totals(table)[cap - 1]

def soft_cap(table, mean, width):
    # exp_to_next(L) = min(max, default(L) * (1 + 10 ** ((L - mean) / width))):
    # double the default from `mean` to `mean + 1`; every `width` levels past
    # that multiplies the extra cost by ten (base 10 rather than e, so even the
    # smallest width, 1, turns on sharply: x2, x11, x101...)
    result = []
    for level, value in enumerate(table, start = 1):
        exponent = (level - mean) / width
        if exponent >= 5:      # 1 + 10^5 times any entry (>= 1) is past the maximum
            result.append(STEP_MAX)
            continue
        # round to nearest (rounding up would add a whole step to tiny early entries), never below default
        scaled = math.floor(value * (1 + 10 ** exponent) + 0.5)
        result.append(min(STEP_MAX, max(value, scaled)))
    return result

def guard_wrap(table):
    # experience cannot exceed BATTLE_EXP_CAP in battle, so levels whose total is
    # past it are unreachable there. a character can still be placed on one
    # (-stl, -stlr, -sal), and once the summed entries reach SUM_LIMIT the 24-bit
    # total wraps to a small number: the character's experience is set to garbage
    # and battle would level them straight to 99. keep the sum below the limit by
    # making the unreachable levels cost almost nothing
    result = []
    total = 0
    for value in table:
        if total * 8 > BATTLE_EXP_CAP:
            value = 1
        result.append(value)
        total += value
    assert total < SUM_LIMIT
    return result

def capped_table(table, mean, width):
    return guard_wrap(soft_cap(table, mean, width))

def totals(table):
    # total experience at each level 1..99
    result = [0]
    for value in table:
        result.append(result[-1] + value * 8)
    return result
