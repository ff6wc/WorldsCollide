# menu variants of the asm objective conditions
# implementation shared with _battle_condition.py, see _asm_condition.py

import objectives.conditions._asm_condition as _asm_condition

class EventBitCondition(_asm_condition._EventBitCondition):
    condition_type = "menu"

class BattleBitCondition(_asm_condition._BattleBitCondition):
    condition_type = "menu"

class CharacterCondition(_asm_condition._CharacterCondition):
    condition_type = "menu"

class EsperCondition(_asm_condition._EsperCondition):
    condition_type = "menu"

class EventWordCondition(_asm_condition._EventWordCondition):
    condition_type = "menu"
