# LLM Developer Guide for Final Fantasy VI Worlds Collide

This guide is designed for LLMs (such as Claude, GPT-4, Cursor, Gemini, Copilot) to understand the codebase structure, coding paradigms, core abstractions, and constraints of the Final Fantasy VI Worlds Collide randomizer project.

> [!IMPORTANT]
> **SELF-UPDATE MANDATE**: If any changes you make to the codebase during your work affect existing patterns, add new modules, change core APIs, or introduce new paradigms, you **MUST** update this file (`llms.md`) and `agents.md` as part of your changes to keep future AI agents correctly instructed.

---

## 1. Repository Blueprint

The repository is modular and structured as follows:

- **Root Directory**:
  - [wc.py](wc.py): Central entry point. Orchestrates memory loading, parsing, modding, and writing.
  - [seed.py](seed.py): Manages random number generation and seeding based on seed strings and flags.
  - [sprite_hash.py](sprite_hash.py): Generates validation hashes based on settings and versions.
- [args/](args/): Flag and argument parsing. Every gameplay subsystem has a corresponding file here (e.g. `items.py`, `bosses.py`, `scaling.py`).
- [memory/](memory/): Core ROM memory abstractions. Manages memory range reservations, heap allocations, and bank writing.
- [data/](data/): Data modeling representing ROM records (characters, items, spells, shops, bosses). Parses bytes into objects, modifies them, and writes them back.
- [instruction/](instruction/):
  - [asm.py](instruction/asm.py): Python wrappers for 65816 CPU assembly instructions.
  - [field/instructions.py](instruction/field/instructions.py): Python classes for SNES map event script bytecodes.
  - [field/custom.py](instruction/field/custom.py): Dynamically generated assembly-level custom event commands.
- [event/](event/): Game event logic. Each key quest/location has its own script (e.g. `airship.py`, `daryl_tomb.py`).
- [battle/](battle/): Battle logic, level scaling math, and multipliers.
- [bug_fixes/](bug_fixes/): Assembly-level bug fixes for the original game engine (e.g. Magic Evade bug).
- [settings/](settings/): Handles specific gameplay patches (e.g. speed-up/sprint mechanics, permadeath).
- [utils/](utils/): Helper functions for compression, random weightings, and lists.

---

## 2. Dynamic Option Processing (`args/`)

All CLI options must be declared inside a module in `args/` and registered in [arguments.py](args/arguments.py).

### How to Add a New Option
Every module in `args/` (e.g., `args/misc.py`) must implement three key hook functions:

1. `parse(parser)`: Register command-line arguments using standard `argparse` options.
2. `process(args)`: Validate options and assign computed properties to the `args` object.
3. `flags(args)`: Return the string flags corresponding to the active setting (crucial for seed RNG hash consistency).

#### Example Module Pattern:
```python
# args/my_new_subsystem.py
def parse(parser):
    group = parser.add_argument_group("My Subsystem Settings")
    group.add_argument("-mns", "--my-new-setting", action="store_true", help="Enable awesome new feature")

def process(args):
    # args is the global Arguments object
    if args.my_new_setting:
        # Perform computation or set internal flags
        args.calculated_setting_value = 42

def flags(args):
    # Return string representation of settings for the seed generator
    if args.my_new_setting:
        return " -mns"
    return ""
```

---

## 3. ROM Space & Allocation Abstractions (`memory/`)

Worlds Collide manages ROM modifications through the `Space` class in [memory/space.py](memory/space.py). **Never** write bytes directly to raw offsets manually.

### Core Functions:
- `Reserve(start_address, end_address, description, clear_value = None)`: Claims a static block of the original ROM. Useful for overwriting/hooking vanilla code.
- `Allocate(bank, size, description, clear_value = None)`: Dynamically allocates an unused chunk of the specified size in a designated SNES bank (e.g. `Bank.C0`, `Bank.C4`, `Bank.F0`).
- `Write(destination, data, description)`: Wraps `Reserve` or `Allocate` depending on whether `destination` is a bank or an address, flatly writing the instruction array.
- `Read(start_address, end_address)`: Extracts a list of raw bytes from the ROM.

> [!CAUTION]
> **Space Conflicts**: The `Space` framework asserts that no two spaces overlap. Overlapping address reservations will raise a `RuntimeError` immediately upon randomizer execution. Always use `Allocate` when writing new subroutines to let the memory manager handle addresses safely.

---

## 4. 65816 Assembly Engine (`instruction/asm.py`)

When modifying the game engine's assembly, use the instruction classes defined in [instruction/asm.py](instruction/asm.py) rather than raw bytes or custom compiler scripts.

### Basic Assembly Example:
```python
import instruction.asm as asm
from memory.space import Bank, Write

src = [
    asm.A8(),                   # Set 8-bit accumulator register mode
    asm.LDA(0x1F60, asm.ABS),   # Load byte from RAM address $1F60
    asm.XOR(0xFF, asm.IMM8),    # Bitwise XOR with $FF
    asm.STA(0x1F60, asm.ABS),   # Store byte back to RAM address $1F60
    asm.RTS(),                  # Return from subroutine
]

# Dynamically allocate this subroutine in Bank C0
space = Write(Bank.C0, src, "my custom memory toggle routine")
subroutine_address = space.start_address
```

### Register Modes & Width Modifiers:
- `A8()`, `XY8()`, `AXY8()`: Sets register sizes to 8-bit.
- `A16()`, `XY16()`, `AXY16()`: Sets register sizes to 16-bit.
- Always match the operand widths in instruction wrappers (`asm.IMM8` vs `asm.IMM16`, `asm.ABS` vs `asm.LNG_X`).
- Use labels inside source lists for branches to avoid hardcoded byte counts:
  ```python
  src = [
      asm.LDA(0x0200, asm.ABS),
      asm.BNE("SKIP_ACTION"),  # Branch to label string
      asm.INC(),
      "SKIP_ACTION",            # Label declaration
      asm.RTS(),
  ]
  ```

---

## 5. Event and Custom Opcode Scripting

Worlds Collide handles quest and dialogue scripting using SNES map event bytecodes.

### 5.1 Standard Field Scripting (`instruction/field/instructions.py`)
Field scripts represent in-game engine scripts. Standard instructions mapped to Python classes include:
- `SetEventBit(bit)`, `ClearEventBit(bit)`
- `BranchIfEventBitSet(bit, destination)`, `BranchIfEventBitClear(bit, destination)`
- `Dialog(dialog_id)`, `AddItem(item_id)`, `AddEsper(esper_id)`
- `LoadMap(map_id, direction, default_music, x, y)`, `FadeLoadMap(...)`

> [!WARNING]
> Every script path **MUST** terminate with `Return()` or `End()` (or transfer control permanently). Failing to terminate a script path results in the SNES engine executing subsequent memory bytes as garbage instructions, crashing the emulator.

### 5.2 Dynamic Custom Field Opcodes (`instruction/field/custom.py`)
If a script feature requires complex logic not supported by vanilla FF6 event scripting, Worlds Collide compiles custom assembly, registers it as a new event bytecode, and binds it to an unused opcode in the SNES event interpreter:

```python
# instruction/field/custom.py
class RecruitCharacter(_Instruction):
    def __init__(self, character):
        recruit_character_function = START_ADDRESS_SNES + c0.recruit_character
        src = [
            asm.JSL(recruit_character_function),
            asm.LDA(0x02, asm.IMM8),        # 2-byte event command size (opcode + arg)
            asm.JMP(0x9b5c, asm.ABS),       # Return control to field interpreter
        ]
        space = Write(Bank.C0, src, "custom recruit_character command")
        address = space.start_address

        # Register the bytecode $76 to point to our newly compiled custom assembly routine
        opcode = 0x76
        _set_opcode_address(opcode, address)

        # Initialize base bytecode instruction
        super().__init__(opcode, character)
```

---

## 6. Dynamic Import Guardrails

To prevent circular dependency locks (since subsystems like `args`, `data`, `event`, and `instruction` rely on each other), Worlds Collide frequently imports files inside local methods rather than globally at the top of the file:

```python
# Preferred pattern in event/ or data/ modules
def mod(self):
    from log import section  # Local import prevents startup circular reference crashes
    import random
    ...
```

Keep imports localized to functions unless you are confident the module is a leaf-node helper.

---

## 7. Test Data Isolation

All generated test data, output ROMs, log text files, and metadata manifests generated during manual/automated testing **MUST** be placed in a dedicated `tests/` directory at the root of the workspace.

- **Rule**: Never save output test artifacts (e.g., test ROMs or generated log files) directly to the workspace root.
- **Directory**: `tests/`
- **Output Paths**: Ensure files are explicitly targeted to the isolated subdirectory, for example:
  - Output test ROM: `tests/test_output.smc`
  - Output test Log: `tests/test_output.txt`
  - Manifest file: `tests/test_manifest.json`

---

## 8. Cosmetic Flag Modifications & WRAM / Sprite Hooks

When implementing visual-only overrides (such as "Who's There?" `-who` / `--who-there` mode):
- **Name Obfuscation**: Modify name fields in `data/enemies.py` directly. The data layer will serialize and write the modified text bytes to the ROM during serialization.
- **Visual Sprite Loader Hooking**: Patch the graphics loader logic at ROM offset `0x01207B` (Bank `C1`) using `Reserve` to intercept the check for monster status effects (e.g. WRAM Imp Graphics flags `$62C2,Y` indexed by slot ID). A custom assembly routine in Bank `F0` (via `Allocate`) evaluates conditions (e.g., `-who` flag status and looking up the active monster's ID directly from WRAM `$812F,Y` (indexed by slot * 2) after clearing the Accumulator's high byte using `TDC` (`0x7B`) immediately after `PHX` to avoid index register pollution, against a 384-byte `boss_table` of boss IDs using 24-bit absolute opcodes `0xAF`/`0xBF`). The subroutine redirects rendering to the Imp sprite dynamically without applying the actual status, while strictly preserving Index Register X (`PHX`/`PLX`) to ensure standard graphics rendering for all other enemies remains perfectly intact.
- **Python 3.14 Compatibility**: When selecting random items/espers from a `set` pool (such as `self.available_espers` in `data/espers.py`), never pass the `set` directly to `random.sample()`, as Python 3.9+ deprecates and Python 3.11+ (including Python 3.14) throws `TypeError`. Instead, convert the set to a tuple: `random.sample(tuple(set_pool), 1)[0]`. This satisfies Python's sequence checks while maintaining 100% identical random state consumption and seed choice sequence compatibility with all older Python versions.
- **Character Gating & Reward Types**: In `event/event_reward.py`, `single_possible_type(self)` checks if a reward slot allows only a single type. Because Python's `Flag` allows checking membership for compound flag combinations (`RewardType.CHARACTER | RewardType.ESPER in RewardType` evaluates to `True`), checking `possible_types in RewardType` was a major bug that caused compound slots to be treated as single-type slots. This lead to gating deadlocks (`AssertionError` in `choose_reward`) under specific seed/flag configurations. The fix is to explicitly check against exact single-member flags: `return self.possible_types in (RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM)`.
