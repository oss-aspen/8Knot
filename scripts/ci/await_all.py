#!/usr/bin/env python3
"""
await_all.py: Waits for all regex patterns to match from stdin input.

Usage:
    python await_all.py <patterns_file>

- <patterns_file> should be a text file with one regex pattern per line.
- Reads lines from stdin, echoing each line to stdout.
- Prints a match message to stdout when a pattern matches a line.
- Exits with success (0) when all patterns have matched at least once.
- Exits with failure (1) if end of input is reached and not all patterns matched.

Example:
    python await_all.py patterns.txt < input.txt

    where patterns.txt contains:
      ^ERROR
      ^WARNING
      ^INFO

    and input.txt contains:
      INFO: All systems operational
      ... other lines ...
      WARNING: Low disk space
      ERROR: Disk failure
"""

import sys
import re

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <patterns_file>", file=sys.stderr)
    sys.exit(2)

patterns_file = sys.argv[1]

# Read regex patterns from the file
with open(patterns_file, 'r') as f:
    pattern_lines = [line.strip() for line in f if line.strip()]

if not pattern_lines:
    print("No patterns found in the file.", file=sys.stderr)
    sys.exit(2)

patterns = [(i, re.compile(p)) for i, p in enumerate(pattern_lines)]
matched = set()

try:
    for line in sys.stdin:
        print(line, end='')  # Copy to stdout immediately
        for idx, regex in patterns:
            if regex.search(line):
                print(f"✅✅✅ MATCH pattern {idx+1}: '{pattern_lines[idx]}'")
                matched.add(idx)
        if len(matched) == len(patterns):
            # All patterns matched, exit early
            break
except KeyboardInterrupt:
    pass

unmatched = [pattern_lines[i] for i in range(len(patterns)) if i not in matched]
if unmatched:
    print("❌❌❌❌❌ Did not match all patterns. ❌❌❌❌❌\nUnmatched patterns:")
    for p in unmatched:
        print(f"❌ - {p}")
    sys.exit(1)
else:
    print("✅✅✅✅✅ All patterns matched. ✅✅✅✅✅")
    sys.exit(0)
