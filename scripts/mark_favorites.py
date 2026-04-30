#!/usr/bin/env python3
"""
Tag entries with >= N stars as community favorites (🌟).
Uses scripts/.stars_cache.json — run sort_by_stars.py first.
Idempotent: skips entries already tagged.

Usage:
    python3 scripts/mark_favorites.py [--dry-run] [--threshold N]
"""

import json, re, sys, argparse
from pathlib import Path
from readme_parser import parse_readme, render_readme

README = 'README.md'
CACHE_FILE = 'scripts/.stars_cache.json'
TAG = '🌟'
TAG_RE = re.compile(r'🌟')
LAST_LINK_RE = re.compile(r'\]\([^)]+\)')


def insert_tag_before_dash(raw, tag):
    last_end = 0
    for m in LAST_LINK_RE.finditer(raw):
        last_end = m.end()
    idx = raw.find(' - ', last_end)
    if idx == -1:
        return raw + ' ' + tag
    return raw[:idx] + ' ' + tag + raw[idx:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--threshold', type=int, default=500)
    args = ap.parse_args()

    if not Path(CACHE_FILE).exists():
        print(f'Cache missing: {CACHE_FILE}. Run sort_by_stars.py first.', file=sys.stderr)
        sys.exit(1)

    with open(CACHE_FILE) as f:
        cache = json.load(f)

    with open(README) as f:
        content = f.read()

    pre, sections = parse_readme(content)
    marked = 0

    for sec in sections:
        for entry in sec.entries:
            if not entry.owner or not entry.repo:
                continue
            stars = cache.get(f'{entry.owner}/{entry.repo}', 0)
            if not isinstance(stars, int) or stars < args.threshold:
                continue
            if TAG_RE.search(entry.raw):
                continue
            entry.raw = insert_tag_before_dash(entry.raw, TAG)
            sec.sync_entry(entry)
            marked += 1

    print(f'Marked {marked} community favorites (>={args.threshold} stars).')
    if not args.dry_run and marked > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
