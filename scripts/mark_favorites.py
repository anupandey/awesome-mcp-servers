#!/usr/bin/env python3
"""
Tag entries with >= N stars as community favorites (🌟).
Re-entrant: strips and re-inserts tag on every run.
Uses scripts/.stars_cache.json — run sort_by_stars.py first.

Usage:
    python3 scripts/mark_favorites.py [--dry-run] [--threshold N]
"""

import json, re, sys, argparse
from pathlib import Path
from readme_parser import parse_readme, render_readme, find_description_separator

README = 'README.md'
CACHE_FILE = 'scripts/.stars_cache.json'
TAG = '🌟'
TAG_STRIP_RE = re.compile(r' 🌟')


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
    marked = removed = 0

    for sec in sections:
        for entry in sec.entries:
            if not entry.owner or not entry.repo:
                continue
            stars = cache.get(f'{entry.owner}/{entry.repo}', 0)
            qualifies = isinstance(stars, int) and stars >= args.threshold

            cleaned = TAG_STRIP_RE.sub('', entry.raw)

            if not qualifies:
                if cleaned != entry.raw:
                    entry.raw = cleaned
                    sec.sync_entry(entry)
                    removed += 1
                continue

            sep = find_description_separator(cleaned)
            if sep == -1:
                new_raw = cleaned + ' ' + TAG
            else:
                new_raw = cleaned[:sep] + ' ' + TAG + cleaned[sep:]

            if new_raw != entry.raw:
                entry.raw = new_raw
                sec.sync_entry(entry)
                marked += 1

    print(f'Marked {marked} community favorites (>={args.threshold} stars), removed {removed}.')
    if not args.dry_run and (marked + removed) > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
