"""Check every tracked Python source without importing it or writing bytecode."""

import ast
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[2]
    paths = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "*.py"],
        cwd=root,
    ).decode().split("\0")
    failures = []
    sources = sorted({path for path in paths if path and (root / path).is_file()})
    for path in sources:
        try:
            ast.parse((root / path).read_bytes(), filename=path)
        except (SyntaxError, UnicodeError) as exc:
            failures.append(f"{path}:{getattr(exc, 'lineno', '?')}: {exc}")
    for failure in failures:
        print(failure, file=sys.stderr)
    print(f"Checked {len(sources)} Python files; {len(failures)} syntax errors.")
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
