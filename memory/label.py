class Label:
    def __init__(self, name: str):
        self.name = name
        self.address = None

    def __repr__(self):
        return f"{self.name} ({hex(self.address)})"

class LabelPointer:
    ABSOLUTE, ABSOLUTE16, ABSOLUTE24, RELATIVE, ABSOLUTE_RELATIVE, BRANCH_RELATIVE = range(6)

    def __init__(self, label, address, mode):
        self.label = label          # reference to the label pointed to
        self.offset = 0             # offset to apply to label (i.e. pointer arithmetic)
        self.address = address      # address of the pointer itself
        self.mode = mode            # absolute, relative, branch_relative

    def __int__(self) -> int:
        value = self.label.address + self.offset
        if self.mode == self.RELATIVE:
            return value - self.address
        elif self.mode == self.ABSOLUTE_RELATIVE:
            return abs(value - self.address)
        elif self.mode == self.BRANCH_RELATIVE:
            value -= self.address
            # branch offsets are relative to the pc after the one byte operand,
            # so the encoded offset is (distance - 1) in two's complement and
            # the reachable distance range is [-127, 128]
            if value > 128 or value < -127:
                raise ValueError(f"Error on Branch to label {self.label.name}. Branch distance: {value} not in [-127, 128]")
            return (value - 1) % 256
        return value

    def to_bytes(self, length: int, byteorder: str, *, signed: bool = False) -> bytes:
        return int(self).to_bytes(length, byteorder, signed = signed)

    def __index__(self):
        return int(self)

    def __add__(self, value):
        self.offset += value
        return self

    def __sub__(self, value):
        self.offset -= value
        return self

    # compares the place pointed to
    def __lt__(self, other):
        return int(self) < other

    def __le__(self, other):
        return int(self) <= other

    def __gt__(self, other):
        return int(self) > other

    def __ge__(self, other):
        return int(self) >= other

    def __repr__(self):
        return f"{hex(int(self))}, *{hex(self.address)} = {repr(self.label)} + {hex(self.offset)}"
