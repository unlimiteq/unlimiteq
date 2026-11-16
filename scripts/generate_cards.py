"""Generate themed SVG cards (stats, languages, featured projects) for the profile README.

Runs in GitHub Actions daily (see .github/workflows/profile.yml) using only the standard
library. Locally:  GITHUB_TOKEN=$(gh auth token) python scripts/generate_cards.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import textwrap
import urllib.request
from xml.sax.saxutils import escape

LOGIN = os.environ.get("PROFILE_USER", "unlimiteq")
FEATURED = ["SideScreen", "osutab"]
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "dist"

THEMES = {
    "dark": {
        "bg": "#0d1117", "border": "#30363d", "title": "#e6edf3", "text": "#9198a1",
        "muted": "#6e7681", "accent": "#a78bfa", "track": "#21262d",
    },
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "title": "#1f2328", "text": "#59636e",
        "muted": "#818b98", "accent": "#7c3aed", "track": "#eaeef2",
    },
}

FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif"

# GitHub Octicons (16px), MIT licensed.
ICONS = {
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z",
    "star": "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z",
    "fork": "M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z",
    "commit": "M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z",
    "pr": "M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z",
    "calendar": "M4.75 0a.75.75 0 0 1 .75.75V2h5V.75a.75.75 0 0 1 1.5 0V2h1.25c.966 0 1.75.784 1.75 1.75v10.5A1.75 1.75 0 0 1 13.25 16H2.75A1.75 1.75 0 0 1 1 14.25V3.75C1 2.784 1.784 2 2.75 2H4V.75A.75.75 0 0 1 4.75 0ZM2.5 7.5v6.75c0 .138.112.25.25.25h10.5a.25.25 0 0 0 .25-.25V7.5Zm10.75-4H2.75a.25.25 0 0 0-.25.25V6h11V3.75a.25.25 0 0 0-.25-.25Z",
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        name description url stargazerCount forkCount
        primaryLanguage { name color }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def fetch() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is not set")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        sys.exit(f"GraphQL errors: {payload['errors']}")
    return payload["data"]["user"]


# ---------- helpers ----------

def icon(name: str, x: float, y: float, color: str, size: int = 16) -> str:
    s = size / 16
    return f'<path transform="translate({x},{y}) scale({s})" fill="{color}" d="{ICONS[name]}"/>'


def frame(w: int, h: int, t: dict, body: str, title: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>
  text {{ font-family: {FONT}; }}
  .fade {{ opacity: 0; animation: fade .6s ease-out forwards; }}
  @keyframes fade {{ to {{ opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{ .fade {{ animation: none; opacity: 1; }} }}
</style>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t['bg']}" stroke="{t['border']}"/>
{body}
</svg>
"""


def fmt(n: int) -> str:
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def streaks(user: dict) -> tuple[int, int]:
    days = [d for w in user["contributionsCollection"]["contributionCalendar"]["weeks"]
            for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    today = dt.date.today().isoformat()
    days = [d for d in days if d["date"] <= today]
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    current = 0
    rev = list(reversed(days))
    if rev and rev[0]["contributionCount"] == 0:  # today not counted yet; don't break streak
        rev = rev[1:]
    for d in rev:
        if d["contributionCount"] == 0:
            break
        current += 1
    return current, longest


# ---------- cards ----------

def stats_card(user: dict, t: dict) -> str:
    cc = user["contributionsCollection"]
    repos = user["repositories"]
    stars = sum(r["stargazerCount"] for r in repos["nodes"])
    current, longest = streaks(user)
    rows = [
        ("calendar", "Contributions (past year)", cc["contributionCalendar"]["totalContributions"]),
        ("commit", "Commits (past year)", cc["totalCommitContributions"]),
        ("pr", "Pull requests (past year)", cc["totalPullRequestContributions"]),
        ("repo", "Public repositories", repos["totalCount"]),
        ("star", "Stars earned", stars),
    ]
    body = [f'<text x="28" y="40" font-size="16" font-weight="600" fill="{t["title"]}">GitHub activity</text>']
    for i, (ic, label, val) in enumerate(rows):
        y = 72 + i * 25
        body.append(
            f'<g class="fade" style="animation-delay:{0.1 + i * 0.08:.2f}s">'
            f'{icon(ic, 28, y - 12, t["accent"])}'
            f'<text x="54" y="{y}" font-size="13" fill="{t["text"]}">{label}</text>'
            f'<text x="270" y="{y}" font-size="13" font-weight="600" fill="{t["title"]}" text-anchor="end">{fmt(val)}</text></g>'
        )
    # streak ring
    cx, cy, r = 360, 110, 44
    circ = 2 * 3.14159 * r
    frac = 1 if current and current >= longest else (current / longest if longest else 0)
    frac = max(frac, 0.04) if current else 0
    body.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["track"]}" stroke-width="7"/>')
    body.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["accent"]}" stroke-width="7" stroke-linecap="round" '
        f'stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ:.1f}" transform="rotate(-90 {cx} {cy})">'
        f'<animate attributeName="stroke-dashoffset" from="{circ:.1f}" to="{circ * (1 - frac):.1f}" dur="1s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.2 1" keyTimes="0;1"/></circle>'
    )
    body.append(f'<text x="{cx}" y="{cy + 2}" font-size="26" font-weight="700" fill="{t["title"]}" text-anchor="middle">{current}</text>')
    body.append(f'<text x="{cx}" y="{cy + 20}" font-size="11" fill="{t["text"]}" text-anchor="middle">day streak</text>')
    body.append(f'<text x="{cx}" y="{cy + 68}" font-size="11" fill="{t["muted"]}" text-anchor="middle">Best: {longest} days</text>')
    return frame(440, 210, t, "\n".join(body), "GitHub activity")


def languages_card(user: dict, t: dict) -> str:
    totals: dict[str, list] = {}
    for repo in user["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            name, color = e["node"]["name"], e["node"]["color"] or "#8b949e"
            totals.setdefault(name, [0, color])[0] += e["size"]
    top = sorted(totals.items(), key=lambda kv: -kv[1][0])[:6]
    total = sum(v[0] for _, v in top) or 1
    body = [f'<text x="28" y="40" font-size="16" font-weight="600" fill="{t["title"]}">Most used languages</text>']
    bar_x, bar_w = 28, 384
    body.append(f'<clipPath id="bar"><rect x="{bar_x}" y="60" width="{bar_w}" height="10" rx="5"/></clipPath>')
    body.append(f'<rect x="{bar_x}" y="60" width="{bar_w}" height="10" rx="5" fill="{t["track"]}"/>')
    x = bar_x
    segs = []
    for name, (size, color) in top:
        w = bar_w * size / total
        segs.append(f'<rect x="{x:.2f}" y="60" width="{w + 0.5:.2f}" height="10" fill="{color}"/>')
        x += w
    body.append(f'<g clip-path="url(#bar)" class="fade">{"".join(segs)}</g>')
    for i, (name, (size, color)) in enumerate(top):
        col, row = i % 2, i // 2
        lx, ly = 28 + col * 200, 104 + row * 32
        pct = 100 * size / total
        body.append(
            f'<g class="fade" style="animation-delay:{0.15 + i * 0.08:.2f}s">'
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>'
            f'<text x="{lx + 18}" y="{ly}" font-size="13" fill="{t["title"]}">{escape(name)}</text>'
            f'<text x="{lx + 180}" y="{ly}" font-size="13" fill="{t["text"]}" text-anchor="end">{pct:.1f}%</text></g>'
        )
    return frame(440, 210, t, "\n".join(body), "Most used languages")


def project_card(repo: dict, t: dict) -> str:
    desc = repo["description"] or ""
    lines = textwrap.wrap(desc, 58)[:3]
    if len(textwrap.wrap(desc, 58)) > 3:
        lines[-1] = lines[-1].rstrip(".,; ") + "…"
    body = [
        icon("repo", 24, 24, t["text"]),
        f'<text x="48" y="37" font-size="16" font-weight="600" fill="{t["accent"]}">{escape(repo["name"])}</text>',
    ]
    for i, line in enumerate(lines):
        body.append(f'<text class="fade" style="animation-delay:{0.1 + i * 0.06:.2f}s" x="24" y="{66 + i * 20}" font-size="13" fill="{t["text"]}">{escape(line)}</text>')
    fy = 136
    x = 24
    lang = repo["primaryLanguage"]
    if lang:
        body.append(f'<circle cx="{x + 6}" cy="{fy - 4}" r="6" fill="{lang["color"] or t["muted"]}"/>')
        body.append(f'<text x="{x + 18}" y="{fy}" font-size="12" fill="{t["text"]}">{escape(lang["name"])}</text>')
        x += 30 + len(lang["name"]) * 7.5
    body.append(icon("star", x, fy - 12, t["text"], 14))
    body.append(f'<text x="{x + 20}" y="{fy}" font-size="12" fill="{t["text"]}">{fmt(repo["stargazerCount"])}</text>')
    x += 48
    body.append(icon("fork", x, fy - 12, t["text"], 14))
    body.append(f'<text x="{x + 20}" y="{fy}" font-size="12" fill="{t["text"]}">{fmt(repo["forkCount"])}</text>')
    return frame(440, 160, t, "\n".join(body), repo["name"])


def main() -> None:
    user = fetch()
    os.makedirs(OUT_DIR, exist_ok=True)
    by_name = {r["name"]: r for r in user["repositories"]["nodes"]}
    outputs = {}
    for theme, t in THEMES.items():
        outputs[f"stats-{theme}.svg"] = stats_card(user, t)
        outputs[f"languages-{theme}.svg"] = languages_card(user, t)
        for name in FEATURED:
            if name in by_name:
                outputs[f"project-{name.lower()}-{theme}.svg"] = project_card(by_name[name], t)
    for fname, svg in outputs.items():
        with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
    print(f"Wrote {len(outputs)} cards to {OUT_DIR}/")


if __name__ == "__main__":
    main()
