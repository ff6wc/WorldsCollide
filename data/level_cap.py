# level caps (-lc): rewrite the experience progression table so levels past
# the cap cost far more experience.
#
# the table at ED/8220 holds 98 16-bit words; entry i is the experience needed
# to go from level i + 1 to level i + 2, divided by 8. the game never stores a
# total: battle (C2/606D), the menu (C3/60CA) and "set experience for level"
# (C0/A235) all sum the entries in 24 bits and multiply by 8.

import math

EXP_TABLE_START = 0x2d8220
EXP_TABLE_END = 0x2d82e3
EXP_TABLE_COUNT = 98

STEP_MAX = 0xffff               # 524,280 experience per level, the most one entry can hold
BATTLE_EXP_CAP = 15000000       # C2/6276: battle never raises experience past this
SUM_LIMIT = 1 << 21             # summed entries at which the 24-bit total (x 8) wraps around

def hard_cap(table, cap):
    # once a character reaches level `cap`, every further level costs the maximum
    return [value if level < cap else STEP_MAX
            for level, value in enumerate(table, start = 1)]

def soft_cap(table, mean, width):
    # exp_to_next(L) = min(max, default(L) * (1 + exp((L - mean) / width))):
    # double the default from `mean` to `mean + 1`, steeper for smaller widths
    result = []
    for level, value in enumerate(table, start = 1):
        exponent = (level - mean) / width
        if exponent >= 50:     # past e^50 every entry is at the maximum anyway
            result.append(STEP_MAX)
            continue
        # round to nearest (rounding up would add a whole step to tiny early entries), never below default
        scaled = math.floor(value * (1 + math.exp(exponent)) + 0.5)
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

def capped_table(table, cap = None, mean = None, width = None):
    if cap is not None:
        table = hard_cap(table, cap)
    else:
        table = soft_cap(table, mean, width)
    return guard_wrap(table)

def totals(table):
    # total experience at each level 1..99
    result = [0]
    for value in table:
        result.append(result[-1] + value * 8)
    return result
