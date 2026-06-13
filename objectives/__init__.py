"""On import this package replaces itself with an Objectives instance.

`import objectives` therefore yields an object, not a module:

    import objectives
    for objective in objectives:        # iterate Objective instances
        ...
    objectives.results["Add Boss Levels"] # objectives grouped by result name

The instance is built from args.objectives, so this import (like most of
the codebase) requires `args` to be importable. See objectives/objectives.py
for the class definition and llms.md for how to add new objective
conditions/results.
"""
import sys
module = sys.modules[__name__]

from objectives.objectives import Objectives
sys.modules[__name__] = Objectives()
