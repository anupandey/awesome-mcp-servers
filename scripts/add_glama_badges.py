#!/usr/bin/env python3
"""
Add missing Glama score badges to entries that have a GitHub URL but no Glama badge.

Usage:
    python3 scripts/add_glama_badges.py [--dry-run] [--limit N]
"""

import re, argparse
from readme_parser import parse_readme, render_readme

README = 'README.md'
GLAMA_RE = re.compile(r'glama\.ai/mcp/servers/')
FIRST_LINK_RE = re.compile(r'\]\(https?://[^)]+\)')


def make_badge(owner, repo):
    score = f'https://glama.ai/mcp/servers/{owner}/{repo}/badges/score.svg'
    link  = f'https://glama.ai/mcp/servers/{owner}/{repo}'
    return f'[![{owner}/{repo} MCP server]({score})]({link})'


def insert_after_first_link(raw, badge):
    m = FIRST_LINK_RE.search(raw)
    if m:
        pos = m.end()
        return raw[:pos] + ' ' + badge + raw[pos:]
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    with open(README) as f:
        content = f.read()

    pre, sections = parse_readme(content)
    added = 0

    for sec in sections:
        if args.limit and added >= args.limit:
            break
        for entry in sec.entries:
            if args.limit and added >= args.limit:
                break
            if not entry.owner or not entry.repo:
                continue
            if GLAMA_RE.search(entry.raw):
                continue
            entry.raw = insert_after_first_link(entry.raw, make_badge(entry.owner, entry.repo))
            sec.sync_entry(entry)
            added += 1

    print(f'Added {added} Glama badges.')

    if not args.dry_run and added > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
