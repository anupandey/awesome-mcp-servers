"""
README parser that preserves exact file structure.

Sections are stored with all their lines intact. Entries are annotated
by index into the section's body_lines list, so sort/modify operations
can work without breaking surrounding blank lines or non-entry content.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


GITHUB_RE = re.compile(r'https://github\.com/([^/\s\)]+)/([^/\s\)#]+)')
ENTRY_RE  = re.compile(r'^-\s+\[')


@dataclass
class Entry:
    line_idx: int           # index into section.body_lines
    raw: str                # current text of this line
    owner: Optional[str] = None
    repo: Optional[str] = None
    github_url: Optional[str] = None
    stars: int = 0
    archived: bool = False
    last_commit_days: Optional[int] = None


@dataclass
class Section:
    header_line: str
    anchor: str
    description_lines: list = field(default_factory=list)  # non-entry header prose
    body_lines: list = field(default_factory=list)          # everything after description
    _entries: list = field(default_factory=list, repr=False)
    _entries_built: bool = field(default=False, repr=False)

    @property
    def entries(self) -> list:
        if not self._entries_built:
            self._build_entries()
        return self._entries

    def _build_entries(self):
        self._entries = []
        for i, line in enumerate(self.body_lines):
            if ENTRY_RE.match(line):
                owner, repo = _parse_github_url(line)
                entry = Entry(
                    line_idx=i,
                    raw=line,
                    owner=owner,
                    repo=repo,
                    github_url=f'https://github.com/{owner}/{repo}' if owner and repo else None,
                )
                self._entries.append(entry)
        self._entries_built = True

    def sync_entry(self, entry: Entry):
        """Write entry.raw back to body_lines at entry.line_idx."""
        self.body_lines[entry.line_idx] = entry.raw

    def sort_entries_by_stars(self):
        """
        Re-order entry lines within body_lines by stars (desc).
        Officials (🎖️) go first. No-github entries go last.
        Non-entry lines (blanks, etc.) between entries are dropped
        only if sorting changes order; otherwise preserved as-is.
        """
        entries = self.entries
        if len(entries) <= 1:
            return

        # Check if any entry ordering would change
        officials  = [e for e in entries if '🎖️' in e.raw]
        with_gh    = [e for e in entries if '🎖️' not in e.raw and e.github_url]
        without_gh = [e for e in entries if '🎖️' not in e.raw and not e.github_url]

        with_gh.sort(key=lambda e: e.stars, reverse=True)
        desired_order = officials + with_gh + without_gh

        if [e.line_idx for e in desired_order] == [e.line_idx for e in entries]:
            return  # already sorted

        # Collect the body lines that ARE entries vs. non-entries
        entry_idx_set = {e.line_idx for e in entries}
        non_entry_lines = [(i, l) for i, l in enumerate(self.body_lines) if i not in entry_idx_set]

        # Build new body: place non-entry lines at their original relative positions
        # Strategy: interleave non-entry lines back between entry blocks at same ratio
        new_body = [e.raw for e in desired_order]

        # Re-insert non-entry lines at their original fractional positions
        total_old = len(self.body_lines)
        for orig_idx, line in sorted(non_entry_lines, key=lambda x: x[0]):
            frac = orig_idx / max(total_old - 1, 1)
            insert_pos = min(int(frac * len(new_body)), len(new_body))
            new_body.insert(insert_pos, line)

        self.body_lines = new_body
        self._entries_built = False  # invalidate cache


def _parse_github_url(line: str):
    m = GITHUB_RE.search(line)
    if m:
        owner = m.group(1)
        repo = m.group(2).rstrip(')')
        if repo and not repo.startswith(('tree', 'blob', 'wiki', 'releases', 'issues')):
            return owner, repo
    return None, None


def parse_readme(content: str):
    """
    Returns (pre_lines, sections).
    pre_lines: list of lines before any ### heading
    sections: list of Section objects (each stores body_lines verbatim)
    """
    lines = content.split('\n')
    pre_lines = []
    sections = []
    current = None
    in_entries = False

    for line in lines:
        if line.startswith('### '):
            if current is not None:
                sections.append(current)
            m = re.search(r'<a name="([^"]+)">', line)
            anchor = m.group(1) if m else ''
            current = Section(header_line=line, anchor=anchor)
            in_entries = False
        elif current is not None:
            if ENTRY_RE.match(line):
                in_entries = True
                current.body_lines.append(line)
            elif in_entries:
                current.body_lines.append(line)
            else:
                current.description_lines.append(line)
        else:
            pre_lines.append(line)

    if current is not None:
        sections.append(current)

    return pre_lines, sections


def render_readme(pre_lines: list, sections: list) -> str:
    """Reconstruct README string from parsed components."""
    out = list(pre_lines)
    for sec in sections:
        out.append(sec.header_line)
        out.extend(sec.description_lines)
        out.extend(sec.body_lines)
    return '\n'.join(out)
