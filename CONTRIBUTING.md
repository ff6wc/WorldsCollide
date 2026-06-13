# Contributing to Worlds Collide

Worlds Collide is community-maintained. This guide covers what you need to
know to make changes safely. For deeper architectural reference (memory
model, assembly hooks, troubleshooting), see [llms.md](llms.md) and
[agents.md](agents.md).

## Requirements

- Python 3.9+ (CI tests 3.9 through 3.13), standard library only.
  Exception: the optional PNG conversion tools in `graphics/tools/` need
  Pillow.
- An unheadered FFIII US v1.0 ROM (3,145,728 bytes) for generating seeds.
  **Never commit a ROM** — `.gitignore` and CI both guard against it, for
  legal reasons.

## Running and testing

```sh
python3 wc.py -i ff3.smc -o tests/test_output.smc   # roll a seed
python3 wc.py -h                                     # exercise all flag parsing
python3 -m unittest discover -s tests                # unit tests (no ROM needed)
```

Generated artifacts (`.smc`, logs) belong in `tests/`, which is gitignored
for everything except the unit test sources. CI runs the unit tests, a
syntax check, and `wc.py -h` on every push/PR.

## The two cardinal rules

1. **Seed reproducibility.** The same seed + flags must produce the same ROM,
   forever. The flag string seeds Python's global `random`, so the *order and
   number of RNG calls* is effectively part of the seed format. Reordering
   loops, filtering before shuffling, adding an early `random.*` call — all
   of these silently change every seed. When changing code near `random`
   calls, verify before/after builds of the same seed are byte-identical
   (`cmp old.smc new.smc`). Behavior-changing fixes are sometimes warranted,
   but must be deliberate and called out in the PR.

2. **Flags are forever.** Old flagsets must keep working with new versions,
   so flags are never removed or renamed. New behavior gets a new flag.

## How a seed is built

`wc.py` runs the phases in order (see `wc.py:main`):

1. `import args` — parses the command line (every module in
   `args/arguments.py`'s group list), builds the canonical flag string, and
   seeds the RNG. This happens at *import time*; see `args/__init__.py`.
2. `import log` — creates the spoiler log (also at import time).
3. `Memory()` — loads and validates the input ROM into `Space.rom`.
4. `Data()` — reads game data structures (characters, espers, items, …)
   from the ROM, applies flag-driven randomization (`mod()` methods).
5. `Events()` — discovers `event/*.py` by naming convention, distributes
   character/esper/item rewards, rewrites event scripts.
6. `Menus()`, `Battle()`, `Settings()`, `BugFixes()` — menu rewrites,
   battle assembly patches, bug fixes.
7. `data.write()` / `memory.write()` — serialize everything back and write
   the output ROM.

ROM writes go through the memory model in `memory/space.py`: `Reserve()`
fixed vanilla ranges, or `Allocate()`/`Write()` dynamic space freed by
`Free()`. Overflowing a space raises `RomSpaceError` — see agents.md
("Memory Overflow / Bank Exhaustion") for resolutions.

## Adding things

**A flag:** each module in `args/` implements the same interface, called by
`args/arguments.py` and the menu/log systems: `parse(parser)` (add argparse
arguments), `process(args)` (validate/derive values), `flags(args)` (rebuild
the canonical flag string), `options(args)`, `menu(args)`, `log(args)`, and
`name()`. Copy an existing small module (e.g. `args/sketch_control.py`) as a
template, and register new modules in `Arguments.groups`. The flag's
behavior is then implemented in `data/`, `event/`, etc. by checking
`self.args.<dest>`.

**An event:** create `event/<location>.py` containing a class whose name is
the module name with underscores removed (e.g. `mt_kolts.py` → `MtKolts`),
subclassing `Event`. A mismatched class name is *silently skipped*. If you
add or remove character/esper reward slots, update
`CHARACTER_ESPER_ONLY_REWARDS` (see agents.md).

**An objective condition/result:** add the constant in
`constants/objectives/`, then the implementation under
`objectives/conditions/` or `objectives/results/`, following an existing
pair like `quest.py`/`quests.py`.

**Tests:** new ROM-independent logic (pure Python helpers, encodings,
allocation) should come with unit tests in `tests/test_*.py`.

## Style

- Match the surrounding code. The codebase uses 4-space indents,
  `snake_case`, and `key = value` spacing in calls.
- Name magic ROM/WRAM addresses, or comment what they are — future readers
  cannot grep for `0x3b18` and know it's the enemy level table.
- Prefer raising descriptive exceptions over `assert` for anything that can
  fail at seed-generation time (asserts vanish under `python -O`).
- If your change affects module structure, core APIs, or the patterns
  documented in `llms.md`/`agents.md`, update those files in the same PR.
