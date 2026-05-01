#!/usr/bin/env python3
"""
Add 🔑 tag to entries whose descriptions mention API key / token requirements.
Re-entrant: strips and re-checks on every run.

💰 Paid and 🆓 Free are not auto-tagged — insufficient signal from descriptions.

Usage:
    python3 scripts/add_pricing_tags.py [--dry-run]
"""

import re, argparse
from readme_parser import parse_readme, render_readme

README = 'README.md'

KEY_TAG = '🔑'
TAG_STRIP_RE = re.compile(r' 🔑')

KEY_PATTERNS = re.compile(
    r'api\s+key|api\s+token|personal\s+access\s+token'
    r'|requires?\s+\w*\s*(key|token|auth|credential)'
    r'|needs?\s+\w*\s*(key|token|auth|credential)'
    r'|authentication\s+required'
    r'|\bpat\b.*required|\brequires?\s+pat\b',
    re.IGNORECASE,
)


def find_separator(raw):
    """
    Find ' - ' separator using bracket-depth tracking so description
    links don't mislead the search. Returns -1 if not found.
    """
    sq = pa = 0
    link_seen = False
    for i, c in enumerate(raw):
        if c == '[':
            sq += 1
        elif c == ']':
            if sq > 0:
                sq -= 1
        elif c == '(':
            pa += 1
        elif c == ')':
            if pa > 0:
                pa -= 1
            if pa == 0 and sq == 0:
                link_seen = True
        if link_seen and sq == 0 and pa == 0 and raw[i:i+3] == ' - ':
            return i
    return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    with open(README) as f:
        content = f.read()

    pre, sections = parse_readme(content)
    tagged = 0

    for sec in sections:
        for entry in sec.entries:
            cleaned = TAG_STRIP_RE.sub('', entry.raw)
            sep = find_separator(cleaned)
            desc = cleaned[sep + 3:] if sep != -1 else ''

            qualifies = bool(KEY_PATTERNS.search(desc))

            if not qualifies:
                if cleaned != entry.raw:
                    entry.raw = cleaned
                    sec.sync_entry(entry)
                continue

            if sep == -1:
                new_raw = cleaned + ' ' + KEY_TAG
            else:
                new_raw = cleaned[:sep] + ' ' + KEY_TAG + cleaned[sep:]

            if new_raw != entry.raw:
                entry.raw = new_raw
                sec.sync_entry(entry)
                tagged += 1

    print(f'Tagged {tagged} entries with 🔑.')
    if not args.dry_run and tagged > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
