"""Format or check CSS source without changing CSS rule order."""

import argparse
from pathlib import Path

import cssbeautifier

parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1] / "app" / "static"
failed = []
for path in sorted(root.rglob("*.css")):
    options = cssbeautifier.default_options()
    options.indent_size = 2
    options.end_with_newline = True
    original = path.read_text()
    formatted = cssbeautifier.beautify(original, options)
    if original != formatted:
        if args.check:
            failed.append(str(path.relative_to(root)))
        else:
            path.write_text(formatted)
if failed:
    raise SystemExit("Formatting required: " + ", ".join(failed))
