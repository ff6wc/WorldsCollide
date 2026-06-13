"""Command line arguments, parsed and processed at import time.

The first `import args` runs the full pipeline: parse sys.argv (every flag
module listed in Arguments.groups), process/validate values, build the
canonical flag string, seed the global random module (see seed.py), and
compute the sprite hash. The resulting attributes are then injected into
this module's namespace so flag values read as plain module attributes:

    import args
    if args.open_world:
        ...

Because parsing happens at import, importing this module (or any module
that imports it, e.g. `log`) requires valid command line arguments —
at minimum `-i INPUT_FILE`.
"""
from args.arguments import Arguments
arguments = Arguments()

import sys
module = sys.modules[__name__]
for name, value in arguments.__dict__.items():
    setattr(module, name, value)
from args.log import log
