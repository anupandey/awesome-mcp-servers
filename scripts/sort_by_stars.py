#!/usr/bin/env python3
"""
Sort entries within each README category by GitHub stars (descending).
Official entries (🎖️) are always pinned to top. No-GitHub entries go last.

Usage:
    python3 scripts/sort_by_stars.py [--dry-run] [--section ANCHOR]

Set GITHUB_TOKEN env var for 5000 req/hr (vs 60 unauthenticated).
"""

import os, re, sys, json, time, argparse, urllib.request, urllib.error
from readme_parser import parse_readme, render_readme

README = 'README.md'
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
CACHE_FILE = 'scripts/.stars_cache.json'


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def fetch_stars(owner, repo, cache):
    key = f'{owner}/{repo}'
    if key in cache:
        return cache[key]
    url = f'https://api.github.com/repos/{owner}/{repo}'
    for attempt in range(3):
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github+json')
        req.add_header('X-GitHub-Api-Version', '2022-11-28')
        if GITHUB_TOKEN:
            req.add_header('Authorization', f'Bearer {GITHUB_TOKEN}')
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                stars = json.loads(resp.read()).get('stargazers_count', 0)
                cache[key] = stars
                return stars
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cache[key] = -1
                return -1
            if e.code == 403:
                wait = 60 * (attempt + 1)
                print(f'  Rate limited. Sleeping {wait}s...', file=sys.stderr)
                time.sleep(wait)
                continue
            break
        except Exception as ex:
            print(f'  Error {key}: {ex}', file=sys.stderr)
            break
    cache[key] = 0
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--section', help='Only process this anchor')
    args = ap.parse_args()

    cache = load_cache()

    with open(README) as f:
        content = f.read()

    pre, sections = parse_readme(content)
    total = sum(len(s.entries) for s in sections)
    print(f'Parsed {len(sections)} sections, {total} entries')

    for sec in sections:
        if args.section and sec.anchor != args.section:
            continue
        if not sec.entries:
            continue
        print(f'  [{sec.anchor}] {len(sec.entries)} entries...', end=' ', flush=True)
        for entry in sec.entries:
            if entry.owner and entry.repo and not args.dry_run:
                entry.stars = fetch_stars(entry.owner, entry.repo, cache)
                time.sleep(0.05)
        sec.sort_entries_by_stars()
        print('done')

    save_cache(cache)

    if not args.dry_run:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')
    else:
        print('Dry run — no write.')


if __name__ == '__main__':
    main()
