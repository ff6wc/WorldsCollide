import unittest

import memory.space
from memory.errors import RomSpaceError
from memory.heap import Heap
from memory.space import Allocate, Bank, Free, Reserve, Space, Write

class FakeRom:
    """Stand-in for memory.rom.ROM backed by a plain list (no ROM file needed)."""
    def __init__(self, size = 0x20000):
        self.data = [0] * size

    def set_bytes(self, address, values):
        self.data[address : address + len(values)] = values
        return address + len(values)

    def get_bytes(self, address, count):
        return self.data[address : address + count]

    def get_byte(self, address):
        return self.data[address]

class SpaceTestCase(unittest.TestCase):
    """Space uses class-level shared state; isolate and restore it per test."""
    def setUp(self):
        self._saved_rom = Space.rom
        self._saved_heaps = Space.heaps
        self._saved_spaces = Space.spaces

        self.rom = FakeRom()
        Space.rom = self.rom
        Space.heaps = { bank : Heap() for bank in Bank }
        Space.spaces = []

    def tearDown(self):
        Space.rom = self._saved_rom
        Space.heaps = self._saved_heaps
        Space.spaces = self._saved_spaces

class TestSpaceWrite(SpaceTestCase):
    def test_write_within_bounds(self):
        space = Space(0x100, 0x10f, "test space")
        space.write(1, 2, 3)
        self.assertEqual(self.rom.get_bytes(0x100, 3), [1, 2, 3])
        self.assertEqual(space.next_address, 0x103)

    def test_writes_are_sequential(self):
        space = Space(0x100, 0x10f, "test space")
        space.write([1, 2])
        space.write([3, 4])
        self.assertEqual(self.rom.get_bytes(0x100, 4), [1, 2, 3, 4])

    def test_write_nested_values_are_flattened(self):
        space = Space(0x100, 0x10f, "test space")
        space.write([1, [2, 3]], (4, 5), b"\x06")
        self.assertEqual(self.rom.get_bytes(0x100, 6), [1, 2, 3, 4, 5, 6])

    def test_write_exactly_full(self):
        space = Space(0x100, 0x103, "test space")
        space.write([1, 2, 3, 4])
        self.assertEqual(self.rom.get_bytes(0x100, 4), [1, 2, 3, 4])

    def test_write_overflow_raises(self):
        space = Space(0x100, 0x103, "test space")
        with self.assertRaises(RomSpaceError):
            space.write([1, 2, 3, 4, 5])

    def test_write_overflow_does_not_modify_rom(self):
        # regression test: overflow used to be detected only after the
        # out-of-bounds bytes had already been written to the rom buffer
        self.rom.data[0x104] = 0xaa # byte just past the end of the space
        space = Space(0x100, 0x103, "test space")
        with self.assertRaises(RomSpaceError):
            space.write([1, 2, 3, 4, 5])
        self.assertEqual(self.rom.get_byte(0x104), 0xaa)
        self.assertEqual(self.rom.get_bytes(0x100, 4), [0, 0, 0, 0])

    def test_overflow_error_is_a_memory_error_for_backward_compatibility(self):
        space = Space(0x100, 0x103, "test space")
        with self.assertRaises(MemoryError):
            space.write([1, 2, 3, 4, 5])

class TestSpaceLabels(SpaceTestCase):
    def test_backward_branch_label_resolution(self):
        space = Space(0x100, 0x10f, "test space")
        space.write(
            "LOOP",
            0xea, 0xea,                     # 2 placeholder bytes
            0x80, space.branch_distance("LOOP"), # BRA LOOP
        )
        # branch operands stay as LabelPointer objects in the rom buffer and
        # resolve via __index__; distance -3, encoded as (distance - 1) mod 256
        self.assertEqual(int(self.rom.get_byte(0x103)), 0xfc)

    def test_duplicate_label_raises(self):
        space = Space(0x100, 0x10f, "test space")
        space.write("LABEL", 0xea)
        with self.assertRaises(ValueError):
            space.write("LABEL", 0xea)

class TestSpaceClear(SpaceTestCase):
    def test_clear_with_single_value(self):
        space = Space(0x100, 0x103, "test space", clear_value = 0xff)
        self.assertEqual(self.rom.get_bytes(0x100, 4), [0xff] * 4)

    def test_clear_with_instruction_value(self):
        # multi-byte clear values are callables with a len(), like the
        # instruction objects from instruction/ (e.g. space.clear(field.NOP()))
        class FakeInstruction:
            def __len__(self):
                return 2
            def __call__(self, space):
                return [1, 2]

        space = Space(0x100, 0x103, "test space", clear_value = FakeInstruction())
        self.assertEqual(self.rom.get_bytes(0x100, 4), [1, 2, 1, 2])

class TestSpaceConflicts(SpaceTestCase):
    def test_overlapping_spaces_raise(self):
        Space(0x100, 0x1ff, "first")
        with self.assertRaises(RuntimeError):
            Space(0x180, 0x280, "second")

    def test_adjacent_spaces_allowed(self):
        Space(0x100, 0x1ff, "first")
        Space(0x200, 0x2ff, "second") # must not raise

class TestAllocateReserveFree(SpaceTestCase):
    def test_allocate_after_free(self):
        Free(0x2000, 0x2fff)
        space = Allocate(Bank["C0"], 0x100, "test allocation")
        self.assertEqual(space.start_address, 0x2000)
        self.assertEqual(len(space), 0x100)

    def test_allocate_without_free_space_raises(self):
        with self.assertRaises(RomSpaceError):
            Allocate(Bank["C0"], 0x100, "test allocation")

    def test_reserve_excludes_range_from_allocation(self):
        Free(0x2000, 0x20ff)
        Reserve(0x2000, 0x207f, "reserved range")
        space = Allocate(Bank["C0"], 0x80, "test allocation")
        self.assertEqual(space.start_address, 0x2080)

    def test_write_helper_allocates_and_writes(self):
        Free(0x2000, 0x2fff)
        space = Write(Bank["C0"], [1, 2, 3], "test write")
        self.assertEqual(len(space), 3)
        self.assertEqual(self.rom.get_bytes(space.start_address, 3), [1, 2, 3])

if __name__ == "__main__":
    unittest.main()
