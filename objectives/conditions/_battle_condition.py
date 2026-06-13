# battle variants of the asm objective conditions
# implementation shared with _menu_condition.py, see _asm_condition.py

import objectives.conditions._asm_condition as _asm_condition

class EventBitCondition(_asm_condition._EventBitCondition):
    condition_type = "battle"

class BattleBitCondition(_asm_condition._BattleBitCondition):
    condition_type = "battle"

class CharacterCondition(_asm_condition._CharacterCondition):
    condition_type = "battle"

class EsperCondition(_asm_condition._EsperCondition):
    condition_type = "battle"

class EventWordCondition(_asm_condition._EventWordCondition):
    condition_type = "battle"
