#!/usr/bin/env python3
"""
Strip Glama score badges from all README entries.
Re-entrant: safe to run multiple times.

Usage:
    python3 scripts/remove_glama_badges.py [--dry-run]
"""

import re, argparse
from readme_parser import parse_readme, render_readme

README = 'README.md'

GLAMA_BADGE_RE = re.compile(
    r'\s*\[!\[[^\]]*\]\(https://glama\.ai/mcp/servers/[^)]+/badges/score\.svg\)\]'
    r'\(https://glama\.ai/mcp/servers/[^)]+\)'
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    with open(README) as f:
        content = f.read()

    pre, sections = parse_readme(content)
    removed = 0

    for sec in sections:
        for entry in sec.entries:
            cleaned = GLAMA_BADGE_RE.sub('', entry.raw)
            if cleaned != entry.raw:
                entry.raw = cleaned
                sec.sync_entry(entry)
                removed += 1

    print(f'Removed Glama badges from {removed} entries.')
    if not args.dry_run and removed > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
