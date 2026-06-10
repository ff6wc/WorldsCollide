import unittest

from memory.label import Label, LabelPointer

class TestLabelPointer(unittest.TestCase):
    def _pointer(self, label_address, pointer_address, mode, offset = 0):
        label = Label("TEST")
        label.address = label_address
        pointer = LabelPointer(label, pointer_address, mode)
        pointer.offset = offset
        return pointer

    def test_absolute(self):
        pointer = self._pointer(0x1234, 0x100, LabelPointer.ABSOLUTE)
        self.assertEqual(int(pointer), 0x1234)

    def test_absolute_with_offset(self):
        pointer = self._pointer(0x1234, 0x100, LabelPointer.ABSOLUTE)
        pointer = pointer + 4
        self.assertEqual(int(pointer), 0x1238)
        pointer = pointer - 8
        self.assertEqual(int(pointer), 0x1230)

    def test_relative(self):
        pointer = self._pointer(0x110, 0x100, LabelPointer.RELATIVE)
        self.assertEqual(int(pointer), 0x10)

        pointer = self._pointer(0x100, 0x110, LabelPointer.RELATIVE)
        self.assertEqual(int(pointer), -0x10)

    def test_absolute_relative(self):
        pointer = self._pointer(0x100, 0x110, LabelPointer.ABSOLUTE_RELATIVE)
        self.assertEqual(int(pointer), 0x10)

    # 65c816 branch offsets are relative to the program counter after the
    # one-byte operand, so the encoded value is (distance - 1) mod 256
    def test_branch_relative_forward(self):
        pointer = self._pointer(0x110, 0x100, LabelPointer.BRANCH_RELATIVE)
        self.assertEqual(int(pointer), 0x0f)

    def test_branch_relative_backward(self):
        pointer = self._pointer(0x100, 0x110, LabelPointer.BRANCH_RELATIVE)
        self.assertEqual(int(pointer), 0xef) # two's complement of -0x11

    def test_branch_relative_backward_minimal(self):
        # branching to the previous byte: distance -1, encoded offset -2 (0xfe)
        pointer = self._pointer(0x0ff, 0x100, LabelPointer.BRANCH_RELATIVE)
        self.assertEqual(int(pointer), 0xfe)

    def test_branch_relative_out_of_range_raises(self):
        pointer = self._pointer(0x200, 0x100, LabelPointer.BRANCH_RELATIVE)
        with self.assertRaises(ValueError):
            int(pointer)

        pointer = self._pointer(0x100, 0x200, LabelPointer.BRANCH_RELATIVE)
        with self.assertRaises(ValueError):
            int(pointer)

    def test_to_bytes_little_endian(self):
        pointer = self._pointer(0x1234, 0x100, LabelPointer.ABSOLUTE)
        self.assertEqual(pointer.to_bytes(2, "little"), b"\x34\x12")

    def test_comparisons_use_pointed_to_address(self):
        pointer = self._pointer(0x1234, 0x100, LabelPointer.ABSOLUTE)
        self.assertTrue(pointer < 0x1235)
        self.assertTrue(pointer <= 0x1234)
        self.assertTrue(pointer > 0x1233)
        self.assertTrue(pointer >= 0x1234)

if __name__ == "__main__":
    unittest.main()
