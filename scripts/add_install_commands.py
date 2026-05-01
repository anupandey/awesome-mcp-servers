#!/usr/bin/env python3
"""
Add/update install command sub-items for entries listed in scripts/install_commands.json.
Re-entrant: strips and re-inserts on every run.

Format added below matching entries:
  - **Install:** `npx @playwright/mcp@latest`

Usage:
    python3 scripts/add_install_commands.py [--dry-run]
"""

import json, argparse
from pathlib import Path
from readme_parser import parse_readme, render_readme

README = 'README.md'
COMMANDS_FILE = 'scripts/install_commands.json'


def is_install_line(line: str) -> bool:
    return line.strip().startswith('- **Install:**')


def make_install_line(cmd: str) -> str:
    return f'  - **Install:** `{cmd}`'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if not Path(COMMANDS_FILE).exists():
        print(f'Commands file not found: {COMMANDS_FILE}')
        return

    with open(COMMANDS_FILE) as f:
        raw = json.load(f)
    commands = {k: v for k, v in raw.items() if not k.startswith('_')}

    with open(README) as f:
        content = f.read()

    pre, sections = parse_readme(content)
    added = updated = removed = 0

    for sec in sections:
        entries = sec.entries
        # Reverse order: insertions/deletions don't shift later line_idx values
        for entry in sorted(entries, key=lambda e: e.line_idx, reverse=True):
            if not entry.owner or not entry.repo:
                continue
            key = f'{entry.owner}/{entry.repo}'
            cmd = commands.get(key)
            next_idx = entry.line_idx + 1
            has_install = (
                next_idx < len(sec.body_lines)
                and is_install_line(sec.body_lines[next_idx])
            )

            if cmd is None:
                if has_install:
                    sec.body_lines.pop(next_idx)
                    removed += 1
                continue

            new_line = make_install_line(cmd)
            if has_install:
                if sec.body_lines[next_idx] != new_line:
                    sec.body_lines[next_idx] = new_line
                    updated += 1
            else:
                sec.body_lines.insert(next_idx, new_line)
                added += 1

    print(f'Install commands: {added} added, {updated} updated, {removed} removed.')
    if not args.dry_run and (added + updated + removed) > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
