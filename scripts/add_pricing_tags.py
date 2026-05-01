#!/usr/bin/env python3
"""
Add 🔑 tag to entries whose descriptions mention API key / token requirements.
Re-entrant: strips and re-checks on every run.

💰 Paid and 🆓 Free are not auto-tagged — insufficient signal from descriptions.

Usage:
    python3 scripts/add_pricing_tags.py [--dry-run]
"""

import re, argparse
from readme_parser import parse_readme, render_readme, find_description_separator

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

# Negation phrases that precede a keyword match — flip qualifies to False
NEGATION_RE = re.compile(
    r'\b(no|without|doesn.t\s+(?:need|require)|not\s+require|free[,\s].*(?:key|token))\b',
    re.IGNORECASE,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    with open(README) as f:
        content = f.read()

    pre, sections = parse_readme(content)
    tagged = removed = 0

    for sec in sections:
        for entry in sec.entries:
            cleaned = TAG_STRIP_RE.sub('', entry.raw)
            sep = find_description_separator(cleaned)
            desc = cleaned[sep + 3:] if sep != -1 else ''

            qualifies = bool(KEY_PATTERNS.search(desc)) and not NEGATION_RE.search(desc)

            if not qualifies:
                if cleaned != entry.raw:
                    entry.raw = cleaned
                    sec.sync_entry(entry)
                    removed += 1
                continue

            if sep == -1:
                new_raw = cleaned + ' ' + KEY_TAG
            else:
                new_raw = cleaned[:sep] + ' ' + KEY_TAG + cleaned[sep:]

            if new_raw != entry.raw:
                entry.raw = new_raw
                sec.sync_entry(entry)
                tagged += 1

    print(f'Tagged {tagged} entries with 🔑, removed {removed}.')
    if not args.dry_run and (tagged + removed) > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
