from balance_adjustments.quick_freeze import QuickFreeze

__all__ = ["BalanceAdjustments"]
class BalanceAdjustments:
    def __init__(self):
        self.quick_freeze = QuickFreeze()