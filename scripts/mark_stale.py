#!/usr/bin/env python3
"""
Mark stale and archived repos in README entries.
- Archived → prepends ⚠️ **[Archived]** to description
- No commit in >N months → prepends ⚠️ **[Stale: Xmo]** to description
- Re-run safe: strips previous markers before re-applying

Usage:
    python3 scripts/mark_stale.py [--dry-run] [--stale-months N]

Set GITHUB_TOKEN env var.
"""

import os, re, sys, json, time, argparse, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
from readme_parser import parse_readme, render_readme

# Load .env from repo root if present
_env = Path(__file__).parent.parent / '.env'
if _env.exists():
    for _line in _env.read_text().splitlines():
        if '=' in _line and not _line.startswith('#'):
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip())

README = 'README.md'
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
CACHE_FILE = 'scripts/.meta_cache.json'
MARKER_RE  = re.compile(r'⚠️ \*\*\[(?:Archived|Stale:[^\]]*)\]\*\* ')


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def fetch_meta(owner, repo, cache):
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
                d = json.loads(resp.read())
                meta = {'archived': d.get('archived', False), 'pushed_at': d.get('pushed_at', '')}
                cache[key] = meta
                return meta
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cache[key] = {'not_found': True}
                return cache[key]
            if e.code == 403:
                wait = 60 * (attempt + 1)
                print(f'  Rate limited. Sleeping {wait}s...', file=sys.stderr)
                time.sleep(wait)
                continue
            break
        except Exception as ex:
            print(f'  Error {owner}/{repo}: {ex}', file=sys.stderr)
            break
    cache[key] = {}
    return {}


def months_since(iso_date):
    if not iso_date:
        return 0
    try:
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        return int((datetime.now(timezone.utc) - dt).days / 30)
    except Exception:
        return 0


_LAST_LINK_RE = re.compile(r'\]\([^)]+\)')

def apply_marker(raw, marker):
    # Find ' - ' only in the portion after all badge/link tokens to avoid
    # matching dashes inside URLs or mid-description dashes.
    last_link = None
    for m in _LAST_LINK_RE.finditer(raw):
        last_link = m
    search_from = last_link.end() if last_link else 0
    idx = raw.find(' - ', search_from)
    if idx == -1:
        return raw + f' {marker}'
    return raw[:idx + 3] + marker + ' ' + raw[idx + 3:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--stale-months', type=int, default=12)
    args = ap.parse_args()

    cache = load_cache()

    with open(README) as f:
        content = f.read()

    pre, sections = parse_readme(content)
    changed = 0

    for sec in sections:
        for entry in sec.entries:
            if not entry.owner or not entry.repo:
                continue
            meta = fetch_meta(entry.owner, entry.repo, cache)
            time.sleep(0.05)

            clean = MARKER_RE.sub('', entry.raw)
            new_raw = clean

            if meta.get('archived'):
                new_raw = apply_marker(clean, '⚠️ **[Archived]**')
            else:
                mo = months_since(meta.get('pushed_at', ''))
                if mo >= args.stale_months:
                    new_raw = apply_marker(clean, f'⚠️ **[Stale: {mo}mo]**')

            if new_raw != entry.raw:
                entry.raw = new_raw
                sec.sync_entry(entry)
                changed += 1

    save_cache(cache)
    print(f'Marked {changed} entries.')

    if not args.dry_run and changed > 0:
        with open(README, 'w') as f:
            f.write(render_readme(pre, sections))
        print('Written.')


if __name__ == '__main__':
    main()
