#!/usr/bin/env python3
"""
Update a "Recently Added" section at the top of README using git log.
Shows the last 10 entries merged in the past 30 days.

Usage:
    python3 scripts/update_recently_added.py [--dry-run] [--days N] [--count N]
"""

import re
import subprocess
import argparse

README = 'README.md'

SECTION_START = '<!-- recently-added-start -->'
SECTION_END   = '<!-- recently-added-end -->'


def git_new_entries(days: int, count: int) -> list[str]:
    """Return list of new `- [...]` entry lines added in last N days."""
    result = subprocess.run(
        ['git', 'log', f'--since={days} days ago', '-p', '--', README],
        capture_output=True, text=True
    )
    entries = []
    for line in result.stdout.split('\n'):
        if line.startswith('+- [') and not line.startswith('+++'):
            raw = line[1:]  # strip leading '+'
            # Extract just name + link + brief description (first 120 chars)
            entries.append(raw.strip())
            if len(entries) >= count:
                break
    return entries


def build_section(entries: list[str], days: int) -> str:
    if not entries:
        return f'{SECTION_START}\n{SECTION_END}\n'

    lines = [
        SECTION_START,
        '',
        f'## 🆕 Recently Added (last {days} days)',
        '',
    ]
    for e in entries:
        lines.append(e)
    lines.append('')
    lines.append(SECTION_END)
    lines.append('')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--count', type=int, default=10)
    args = parser.parse_args()

    entries = git_new_entries(args.days, args.count)
    print(f'Found {len(entries)} new entries in last {args.days} days.')

    with open(README) as f:
        content = f.read()

    new_section = build_section(entries, args.days)

    if SECTION_START in content:
        # Replace existing section
        new_content = re.sub(
            re.escape(SECTION_START) + r'.*?' + re.escape(SECTION_END),
            new_section.rstrip('\n'),
            content,
            flags=re.DOTALL
        )
    else:
        # Insert after the first > [!NOTE] block (after "Server Implementations")
        new_content = content.replace(
            '## Server Implementations\n',
            '## Server Implementations\n\n' + new_section,
            1
        )

    if args.dry_run:
        print('Dry run — no write.')
        print(new_section)
        return

    with open(README, 'w') as f:
        f.write(new_content)
    print('Written.')


if __name__ == '__main__':
    main()
