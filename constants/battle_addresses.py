# battle wram addresses shared across modules
# kept in constants/ (side-effect free) so data/ modules can import them without
# triggering the rom writes that importing the battle package performs

# level of each battle entity, indexed by entity slot (vanilla $3b18)
ENEMY_LEVEL = 0x3b18

# per-battle scale levels computed once by battle/scaling.py load_scale_levels_mod
LEVEL_SCALE = 0x3ecc
HP_MP_SCALE = 0x3ecd
XP_GP_SCALE = 0x3ece
