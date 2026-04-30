#!/usr/bin/env python3
"""
README improvements script.
Fixes: emoji duplicates, TOC counts, missing TOC entries, search tip, quick-start section.
"""

import re
import sys

README = 'README.md'

with open(README, 'r') as f:
    content = f.read()

# Guard: already applied if Quick Start section exists
if '## 🚀 Quick Start Picks' in content:
    print('Already applied. Delete this guard in update_readme.py to force re-run.')
    sys.exit(0)

lines = content.split('\n')

# ── 1. Count entries per category ────────────────────────────────────────────

category_counts = {}  # anchor → count
current_anchor = None
count = 0

for line in lines:
    m = re.search(r'<a name="([^"]+)">', line)
    if m and line.startswith('### '):
        if current_anchor is not None:
            category_counts[current_anchor] = count
        current_anchor = m.group(1)
        count = 0
    elif line.startswith('- [') and current_anchor:
        count += 1

if current_anchor:
    category_counts[current_anchor] = count

# ── 2. Emoji remapping (fix duplicates) ──────────────────────────────────────
# Old emoji → new emoji, keyed by anchor so we only change specific sections
EMOJI_FIXES = {
    'file-systems':                   ('📂', '📁'),   # was duplicate of browser-automation
    'data-visualization':             ('📊', '📉'),   # was duplicate of data-platforms/monitoring
    'monitoring':                     ('📊', '📡'),   # was duplicate of data-platforms/data-viz
    'os-automation':                  ('🖥️', '🖱️'),   # was duplicate of command-line
    'real-estate':                    ('🏠', '🏘️'),   # was duplicate of home-automation
    'text-to-speech':                 ('🎧', '🔊'),   # was duplicate of support-and-service-management
    'other-tools-and-integrations':   ('🛠️', '⚙️'),   # was duplicate of developer-tools
    'delivery':                       ('🔒', '🚚'),   # header had wrong emoji vs TOC
}

# ── 3. Rebuild the file ───────────────────────────────────────────────────────

new_lines = []
in_toc = False
toc_done = False
tip_inserted = False
quickstart_inserted = False
i = 0

SEARCH_TIP = """> [!TIP]
> **Finding a server fast:** Press `Ctrl+F` / `Cmd+F` and search by keyword — try `"postgres"`, `"slack"`, `"github"`, `"browser"`, or any tool name."""

QUICKSTART = """## 🚀 Quick Start Picks

New to MCP? Start here. Curated picks for the most common use cases — all well-maintained and widely used.

| Use case | Server | Install |
|---|---|---|
| **Browse the web** | [Playwright MCP](https://github.com/microsoft/playwright-mcp) | `npx @playwright/mcp@latest` |
| **Search the web** | [Brave Search](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/brave-search) | `npx -y @modelcontextprotocol/server-brave-search` |
| **Query databases** | [MCP SQLite](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sqlite) | `uvx mcp-server-sqlite --db-path ~/db.sqlite` |
| **Read/write files** | [Filesystem MCP](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/filesystem) | `npx -y @modelcontextprotocol/server-filesystem /path` |
| **GitHub operations** | [GitHub MCP](https://github.com/github/github-mcp-server) | `npx -y @modelcontextprotocol/server-github` |
| **Memory / notes** | [Memory MCP](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/memory) | `npx -y @modelcontextprotocol/server-memory` |
| **Fetch URLs** | [Fetch MCP](https://github.com/zcaceres/fetch-mcp) | `npx -y mcp-fetch` |
| **Run code** | [E2B Code Interpreter](https://github.com/e2b-dev/mcp-server) | `npx -y @e2b/mcp-server` |

> Browse the full list below, or use [glama.ai/mcp/servers](https://glama.ai/mcp/servers) for search and filtering.

"""

while i < len(lines):
    line = lines[i]

    # Insert search tip right after the "Server Implementations" heading + NOTE block
    if not tip_inserted and line.strip() == '> We now have a [web-based directory](https://glama.ai/mcp/servers) that is synced with the repository.':
        new_lines.append(line)
        i += 1
        # skip blank line after NOTE block if present
        while i < len(lines) and lines[i].strip() == '':
            new_lines.append(lines[i])
            i += 1
        new_lines.append(SEARCH_TIP)
        new_lines.append('')
        tip_inserted = True
        continue

    # Detect start of TOC (Server Implementations section list)
    if line.strip() == '* 🔗 - [Aggregators](#aggregators)':
        in_toc = True

    # Insert Quick Start section just before the TOC
    if not quickstart_inserted and in_toc and line.startswith('* 🔗'):
        new_lines.append(QUICKSTART)
        quickstart_inserted = True

    # Process TOC lines: fix emojis + add counts + add missing entries
    if in_toc and line.startswith('* ') and '- [' in line and '](#' in line:
        # Fix emoji duplicates in TOC
        m = re.search(r'\((#([^)]+))\)', line)
        if m:
            anchor = m.group(2)
            if anchor in EMOJI_FIXES:
                old_emoji, new_emoji = EMOJI_FIXES[anchor]
                line = line.replace(old_emoji, new_emoji, 1)

            # Add count to TOC entry
            count = category_counts.get(anchor, 0)
            if count > 0:
                # Replace `[Name](#anchor)` with `[Name (N)](#anchor)`
                line = re.sub(
                    r'\[([^\]]+)\]\(#' + re.escape(anchor) + r'\)',
                    lambda mo: f'[{mo.group(1)} ({count})](#{anchor})',
                    line
                )

        new_lines.append(line)

        # Inject missing Aerospace entry after the intro list marker
        if '🎗' in line or 'aggregators' in line.lower():
            pass  # handled below via sorted insertion

        i += 1
        continue

    # Detect end of TOC
    if in_toc and line.strip() == '' and i + 1 < len(lines) and lines[i+1].startswith('### '):
        # Before ending TOC, inject missing entries
        # Aerospace (🚀) — insert after Art & Culture alphabetically
        # RAG (🗂️) — insert before Search
        # We'll just append them at a natural position; easier to inject inline
        in_toc = False
        toc_done = True

    # Fix section headers: emoji + title (not just TOC)
    if line.startswith('### '):
        hdr_anchor_m = re.search(r'<a name="([^"]+)">', line)
        if hdr_anchor_m:
            anchor = hdr_anchor_m.group(1)
            if anchor in EMOJI_FIXES:
                old_emoji, new_emoji = EMOJI_FIXES[anchor]
                line = line.replace(old_emoji, new_emoji, 1)

    new_lines.append(line)
    i += 1

content_out = '\n'.join(new_lines)

# ── 4. Add missing TOC entries (Aerospace + RAG) ─────────────────────────────
# Insert Aerospace after "🎨 - [Art & Culture"
aero_count = category_counts.get('aerospace-and-astrodynamics', 0)
aero_entry = f'* 🚀 - [Aerospace & Astrodynamics (#{aero_count})]({{#aerospace-and-astrodynamics}})'
# Actually format it properly:
aero_entry = f'* 🚀 - [Aerospace & Astrodynamics ({aero_count})](#aerospace-and-astrodynamics)'

rag_count = category_counts.get('RAG', 0)
rag_entry = f'* 🗂️ - [RAG Platforms ({rag_count})](#RAG)'

# Insert Aerospace after Art & Culture line in TOC
content_out = re.sub(
    r'(\* 🎨 - \[Art & Culture[^\n]*\n)',
    r'\1' + aero_entry + '\n',
    content_out
)

# Insert RAG before Search line in TOC
content_out = re.sub(
    r'(\* 🔎 - \[Search)',
    rag_entry + '\n' + r'\1',
    content_out
)

with open(README, 'w') as f:
    f.write(content_out)

print("Done.")
print(f"  Quick-start inserted: {quickstart_inserted}")
print(f"  Search tip inserted: {tip_inserted}")
print(f"  Emoji fixes applied: {list(EMOJI_FIXES.keys())}")
print(f"  TOC counts added for {len(category_counts)} categories")
