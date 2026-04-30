#!/usr/bin/env python3
"""
Add pricing/auth tags to entries based on description keywords.

Tags added:
  🔑  API key / token required (keyword match on description)

💰 Paid and 🆓 Free are NOT auto-tagged — insufficient signal from
description text alone; those require manual curation.

Idempotent: skips entries already tagged.

Usage:
    python3 scripts/add_pricing_tags.py [--dry-run]
"""

import re, argparse
from readme_parser import parse_readme, render_readme

README = 'README.md'

LAST_LINK_RE = re.compile(r'\]\([^)]+\)')
KEY_TAG = '🔑'
KEY_TAG_RE = re.compile(r'🔑')

KEY_PATTERNS = re.compile(
    r'api\s+key|api\s+token|personal\s+access\s+token'
    r'|requires?\s+\w*\s*(key|token|auth|credential)'
    r'|needs?\s+\w*\s*(key|token|auth|credential)'
    r'|authentication\s+required'
    r'|\bpat\b.*required|\brequires?\s+pat\b',
    re.IGNORECASE,
)


def get_description(raw, last_link_end):
    idx = raw.find(' - ', last_link_end)
    return raw[idx + 3:] if idx != -1 else ''


def last_link_end(raw):
    pos = 0
    for m in LAST_LINK_RE.finditer(raw):
        pos = m.end()
    return pos


def insert_tag_before_dash(raw, tag, link_end):
    idx = raw.find(' - ', link_end)
    if idx == -1:
        return raw + ' ' + tag
    return raw[:idx] + ' ' + tag + raw[idx:]


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
            link_end = last_link_end(entry.raw)
            desc = get_description(entry.raw, link_end)
            if not desc:
                continue

            if not KEY_TAG_RE.search(entry.raw) and KEY_PATTERNS.search(desc):
                entry.raw = insert_tag_before_dash(entry.raw, KEY_TAG, link_end)
                sec.sync_entry(entry)
                tagged += 1

    print(f'Tagged {tagged} entries with 🔑.')
    if not args.dry_run and tagged > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
