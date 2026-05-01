#!/usr/bin/env python3
"""
Add shields.io GitHub stars and last-commit badges to each entry.
Re-entrant: strips and re-inserts on every run so position is always correct.

Usage:
    python3 scripts/add_shields_badges.py [--dry-run]
"""

import re, argparse
from readme_parser import parse_readme, render_readme, find_description_separator

README = 'README.md'

# Matches one shields badge with its leading space
SHIELDS_BADGE_RE = re.compile(
    r' \[!\[(?:Stars|Last Commit)\]'
    r'\(https://img\.shields\.io/github/[^)]+\)\]'
    r'\(https://github\.com/[^)]+\)'
)
GLAMA_LINK_RE = re.compile(r'\]\(https://glama\.ai/[^\s)]+\)')
GITHUB_LINK_RE = re.compile(r'\]\(https://github\.com/[^\s)]+\)')


def strip_shields(raw):
    return SHIELDS_BADGE_RE.sub('', raw)


def find_insert_pos(raw):
    """
    Insert shields badges after the last Glama link that appears BEFORE ' - '.
    Falls back to first GitHub link (entry link) if no qualifying Glama link.
    """
    sep = find_description_separator(raw)
    # Last Glama link that is in the header area (before separator)
    last_glama_end = 0
    for m in GLAMA_LINK_RE.finditer(raw):
        if sep != -1 and m.end() > sep:
            break
        last_glama_end = m.end()
    if last_glama_end:
        return last_glama_end
    # First GitHub link (the entry link itself)
    m = GITHUB_LINK_RE.search(raw)
    if m and (sep == -1 or m.end() <= sep):
        return m.end()
    return 0


def make_badges(owner, repo):
    base = f'https://github.com/{owner}/{repo}'
    stars = (f'[![Stars](https://img.shields.io/github/stars/{owner}/{repo}'
             f'?style=flat-square)]({base})')
    commit = (f'[![Last Commit](https://img.shields.io/github/last-commit/{owner}/{repo}'
              f'?style=flat-square)]({base})')
    return stars + ' ' + commit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    with open(README) as f:
        content = f.read()

    pre, sections = parse_readme(content)
    updated = 0

    for sec in sections:
        for entry in sec.entries:
            if not entry.owner or not entry.repo:
                continue
            cleaned = strip_shields(entry.raw)
            pos = find_insert_pos(cleaned)
            if not pos:
                continue
            new_raw = cleaned[:pos] + ' ' + make_badges(entry.owner, entry.repo) + cleaned[pos:]
            if new_raw != entry.raw:
                entry.raw = new_raw
                sec.sync_entry(entry)
                updated += 1

    print(f'Updated {updated} entries.')
    if not args.dry_run and updated > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
