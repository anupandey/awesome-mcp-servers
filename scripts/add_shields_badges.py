#!/usr/bin/env python3
"""
Add shields.io GitHub stars and last-commit badges to each entry.
Idempotent: skips entries that already have shields badges.

Usage:
    python3 scripts/add_shields_badges.py [--dry-run]
"""

import re, argparse
from readme_parser import parse_readme, render_readme

README = 'README.md'
SHIELDS_RE = re.compile(r'img\.shields\.io/github/stars/')
LAST_LINK_RE = re.compile(r'\]\([^)]+\)')


def make_badges(owner, repo):
    base = f'https://github.com/{owner}/{repo}'
    stars = (f'[![Stars](https://img.shields.io/github/stars/{owner}/{repo}'
             f'?style=flat-square)]({base})')
    commit = (f'[![Last Commit](https://img.shields.io/github/last-commit/{owner}/{repo}'
              f'?style=flat-square)]({base})')
    return stars + ' ' + commit


def insert_after_last_link(raw, text):
    last_end = 0
    for m in LAST_LINK_RE.finditer(raw):
        last_end = m.end()
    if not last_end:
        return raw
    return raw[:last_end] + ' ' + text + raw[last_end:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    with open(README) as f:
        content = f.read()

    pre, sections = parse_readme(content)
    added = 0

    for sec in sections:
        for entry in sec.entries:
            if not entry.owner or not entry.repo:
                continue
            if SHIELDS_RE.search(entry.raw):
                continue
            new_raw = insert_after_last_link(entry.raw, make_badges(entry.owner, entry.repo))
            if new_raw != entry.raw:
                entry.raw = new_raw
                sec.sync_entry(entry)
                added += 1

    print(f'Added shields badges to {added} entries.')
    if not args.dry_run and added > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
