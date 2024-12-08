from memory.space import Reserve
import args

class QuickFreeze:
    def __init__(self):
        if args.quick_freeze:
            self.quick_freeze_mod()

    def quick_freeze_mod(self):
        Reserve(0x24695, 0x24695, "Freeze time", 0x10)

