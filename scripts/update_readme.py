"""Refreshes the auto-generated sections of README.md.

NOW       <- now.md
FEATURED  <- featured.json
REPOS     <- the GitHub API (public repos, most recently pushed first)

usage:  python scripts/update_readme.py [--repos-file sample.json]
Only the standard library is used. GITHUB_TOKEN (optional) raises the API rate limit.
"""
import json
import os
import re
import sys
import urllib.request

USER = os.environ.get("PROFILE_USER", "Adithya7664")
MAX_REPOS = 5
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def replace_section(text, tag, body):
    pattern = re.compile(rf"(<!-- {tag}:START -->)(.*?)(<!-- {tag}:END -->)", re.S)
    if not pattern.search(text):
        sys.exit(f"markers for {tag} not found in README.md")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body.strip()}\n{m.group(3)}", text, count=1)


def fetch_repos():
    if "--repos-file" in sys.argv:
        with open(sys.argv[sys.argv.index("--repos-file") + 1], encoding="utf-8") as f:
            return json.load(f)
    url = f"https://api.github.com/users/{USER}/repos?sort=pushed&direction=desc&per_page=50&type=owner"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-bot"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def render_repos(repos):
    rows = []
    for r in repos:
        if r.get("fork") or r.get("archived") or r["name"].lower() == USER.lower():
            continue
        desc = (r.get("description") or "").strip()
        bits = [b for b in (r.get("language"), f"updated {r['pushed_at'][:10]}" if r.get("pushed_at") else None) if b]
        if r.get("stargazers_count"):
            bits.append(f"{r['stargazers_count']} stars")
        line = f"- [**{r['name']}**]({r['html_url']})"
        if desc:
            line += f" - {desc}"
        if bits:
            line += f"  \n  <sub>{' · '.join(bits)}</sub>"
        rows.append(line)
        if len(rows) == MAX_REPOS:
            break
    return "\n".join(rows) or "_Nothing public yet._"


def render_featured(items):
    out = []
    for p in items:
        links = [f"[Code]({p['repo']})"]
        if p.get("demo"):
            links.insert(0, f"[Live demo]({p['demo']})")
        tags = " ".join(f"`{t}`" for t in p.get("tags", []))
        out.append(f"### {p['name']}\n{p.get('description', '')}\n\n{' · '.join(links)}" + (f"  \n{tags}" if tags else ""))
    return "\n\n".join(out)


def main():
    readme = read("README.md")
    readme = replace_section(readme, "NOW", read("now.md"))
    readme = replace_section(readme, "FEATURED", render_featured(json.loads(read("featured.json"))))
    readme = replace_section(readme, "REPOS", render_repos(fetch_repos()))
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(readme)
    print("README.md refreshed")


if __name__ == "__main__":
    main()
