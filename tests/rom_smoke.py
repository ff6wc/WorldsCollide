"""Roll real seeds against a ROM to catch crashes the unit tests can't see.

Not part of the unittest suite (it needs a ROM, which is never committed).
CI runs it when the FF3_ROM_URL secret is set; locally:

    python tests/rom_smoke.py --rom ff3.smc

Every on/off flag is rolled on its own, plus the flagstrings in EXTRA_FLAGS.
A roll that the parser rejects (exit code 2, e.g. a flag that needs another
flag) is reported as skipped; any other non-zero exit is a failure.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

WC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXTRA_FLAGS = [
    "",
    "-cg",
    "-open",
    "-nfh -cg",
    "-nfh -sli -cg",
    "-comru 90 -comw shock.possess:0.5",
    "-comr 80.90.100 -comw jump:always:0.5,blitz.runic:5,none:0.3",
    "-com 05999898989898989898989898 -comru 100 -comw slot:never -scc",
]

# builds the real parser, then prints its on/off flags instead of parsing sys.argv
DUMP_FLAGS_SCRIPT = """
import argparse, json, sys
sys.path.insert(0, ".")
class _Done(Exception):
    pass
def _dump(self, *args, **kwargs):
    flags = set()
    for action in self._actions:
        if action.nargs == 0 and action.option_strings and action.dest != "help":
            flags.add(min(action.option_strings, key = len))
    print(json.dumps(sorted(flags)))
    raise _Done
argparse.ArgumentParser.parse_args = _dump
try:
    from args.arguments import Arguments
    Arguments()
except _Done:
    pass
"""

def on_off_flags():
    result = subprocess.run([sys.executable, "-c", DUMP_FLAGS_SCRIPT], cwd = WC_DIR,
                            capture_output = True, text = True, check = True)
    return json.loads(result.stdout.strip().splitlines()[-1])

def roll(rom, flags, out_dir, seed):
    output = os.path.join(out_dir, "smoke.smc")
    command = [sys.executable, "wc.py", "-i", rom, "-o", output, "-s", seed] + flags.split()
    return subprocess.run(command, cwd = WC_DIR, capture_output = True, text = True, timeout = 300)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom", required = True, help = "Path to the unheadered FF3 US 1.0 ROM")
    parser.add_argument("--seed", default = "romsmoke", help = "RNG seed used for every roll")
    args = parser.parse_args()

    flagstrings = EXTRA_FLAGS + on_off_flags()
    failures = []
    skipped = []
    with tempfile.TemporaryDirectory() as out_dir:
        for flags in flagstrings:
            result = roll(args.rom, flags, out_dir, args.seed)
            label = flags or "(no flags)"
            if result.returncode == 0:
                print(f"ok      {label}")
            elif result.returncode == 2:
                skipped.append(label)
                print(f"skipped {label}: {result.stderr.strip().splitlines()[-1]}")
            else:
                failures.append((label, result.stderr or result.stdout))
                print(f"FAILED  {label}")

    print(f"\n{len(flagstrings) - len(failures) - len(skipped)} ok, {len(skipped)} skipped, {len(failures)} failed")
    for label, output in failures:
        print(f"\n===== {label} =====\n{output.strip()}")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
