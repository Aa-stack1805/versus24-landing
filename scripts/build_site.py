"""Assemble the static site from src/ into the repo root.

The site is plain static HTML served directly by GitHub Pages, so there is no
runtime framework. To avoid hand-duplicating the <head> boilerplate, nav,
footer, and waitlist form across 16 pages, each page lives in src/pages/ as
its own per-page <head> meta + body, with tokens for the shared regions:

    {{HEAD_COMMON}}     constant <head> tags (favicons, fonts, manifest, css)
    {{NAV}}             site header (active link + home-anchor prefix per page)
    {{WAITLIST_FORM}}   the email capture form
    {{FOOTER}}          site footer
    {{SCRIPT}}          deferred site script

Shared markup lives once in src/partials/. Run this script after editing any
partial or page; it regenerates the committed root HTML (index.html,
features/index.html, ...). Output is committed so Pages keeps serving static
files, so re-run and commit whenever src/ changes.

    python3 scripts/build_site.py
"""
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PARTIALS = SRC / "partials"
PAGES = SRC / "pages"

# name -> (output path, active nav item or None, is_home)
SITE = {
    "index":     ("index.html",            None,       True),
    "features":  ("features/index.html",   "features", False),
    "pricing":   ("pricing/index.html",    "pricing",  False),
    "faq":       ("faq/index.html",        "faq",      False),
    "about":     ("about/index.html",      "about",    False),
    "fighters":  ("fighters/index.html",   None,       False),
    "lifters":   ("lifters/index.html",    None,       False),
    "runners":   ("runners/index.html",    None,       False),
    "sports":    ("sports/index.html",     None,       False),
    "hybrid":    ("hybrid/index.html",     None,       False),
    "android":   ("android/index.html",    None,       False),
    "changelog": ("changelog/index.html",  None,       False),
    "dmca":      ("dmca/index.html",       None,       False),
    "press":     ("press/index.html",      None,       False),
    "privacy":   ("privacy/index.html",    None,       False),
    "r":         ("r/index.html",          None,       False),
    "support":   ("support/index.html",    None,       False),
    "terms":     ("terms/index.html",      None,       False),
}

NAV_ITEMS = ("features", "pricing", "faq", "about")
SCRIPT_TAG = '<script src="/assets/script.js" defer></script>'

# sitemap.xml is generated from SITE so a new page can never be forgotten.
# Anything absent from these maps falls back to monthly / 0.5.
SITE_URL = "https://versus24.net/"
# /r/ is a per-invite landing page, not a search result. It is noindex, so
# listing it would only ask Google to crawl something it must then ignore.
SITEMAP_EXCLUDE = {"r"}
LASTMOD = re.compile(r"<lastmod>[^<]*</lastmod>")
SITEMAP_FREQ = {"index": "weekly", "changelog": "weekly", "dmca": "yearly"}
SITEMAP_PRIORITY = {
    "index": "1.0",
    "fighters": "0.9", "lifters": "0.9", "runners": "0.9", "sports": "0.9",
    "pricing": "0.9",
    "hybrid": "0.8", "features": "0.8",
    "android": "0.7",
    "faq": "0.6", "about": "0.6",
    "support": "0.5", "changelog": "0.5",
    "press": "0.4", "privacy": "0.4", "terms": "0.4",
    "dmca": "0.2",
}

# Legal pages ship without the analytics block (marked in head-common.html):
# no tracking on the pages where people read the privacy terms.
NO_ANALYTICS = {"privacy", "terms", "dmca"}
ANALYTICS_BLOCK = re.compile(r"[ \t]*<!-- analytics:start -->\n.*?<!-- analytics:end -->\n", re.S)
ANALYTICS_MARKER = re.compile(r"[ \t]*<!-- analytics:(?:start|end) -->\n")
LEFTOVER_TOKEN = re.compile(r"\{\{[A-Z_]+\}\}")


def load(path):
    return path.read_text().rstrip("\n")


def render_nav(template, active, is_home, has_form):
    out = template
    # #audiences only exists on the home page; #waitlist exists on any page
    # that renders the waitlist form, so each anchor links in-page where the
    # target section exists and cross-page (to home) where it doesn't.
    out = out.replace("{{AUDIENCES_HREF}}", "#audiences" if is_home else "/#audiences")
    out = out.replace("{{WAITLIST_HREF}}", "#waitlist" if has_form else "/#waitlist")
    for item in NAV_ITEMS:
        out = out.replace("{{A_%s}}" % item.upper(), " active" if active == item else "")
    return out


def substitute(text, token, content):
    """Replace a line that is just {{TOKEN}} with content, preserving the
    token line's indentation on every line of the inserted block."""
    pattern = re.compile(r"^([ \t]*)\{\{%s\}\}[ \t]*$" % re.escape(token), re.M)

    def repl(m):
        indent = m.group(1)
        return "\n".join(indent + line if line else line for line in content.split("\n"))

    return pattern.sub(repl, text)


def render(name, active, is_home, partials):
    head_common, footer, waitlist, nav_tmpl = partials
    page = load(PAGES / f"{name}.html")
    has_form = "{{WAITLIST_FORM}}" in page
    page = substitute(page, "HEAD_COMMON", head_common)
    page = substitute(page, "NAV", render_nav(nav_tmpl, active, is_home, has_form))
    page = substitute(page, "WAITLIST_FORM", waitlist)
    page = substitute(page, "FOOTER", footer)
    page = substitute(page, "SCRIPT", SCRIPT_TAG)

    if name in NO_ANALYTICS:
        page = ANALYTICS_BLOCK.sub("", page)
    else:
        page = ANALYTICS_MARKER.sub("", page)

    leftover = LEFTOVER_TOKEN.search(page)
    if leftover:
        raise SystemExit(f"error: unreplaced token {leftover.group(0)} in {name}.html "
                         "(tokens must sit alone on their own line)")
    return page + "\n"


def git(*args):
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                         text=True, timeout=10)
    return out.stdout.strip() if out.returncode == 0 else ""


def page_lastmod(name):
    """Date a page's source last changed, so <lastmod> is a real signal rather
    than a number someone remembered to bump.

    Uncommitted edits stamp today: the sitemap is generated before the commit
    that contains it, so today's date is what that commit will carry, and
    --check stays green afterwards. Clean sources keep their commit date, which
    is why editing one page does not bump <lastmod> on the other sixteen.
    """
    src = PAGES / f"{name}.html"
    try:
        if git("status", "--porcelain", "--", str(src)):
            return datetime.date.today().isoformat()
        stamp = git("log", "-1", "--format=%cs", "--", str(src))
        if stamp:
            return stamp
    except Exception:
        pass
    return datetime.date.fromtimestamp(src.stat().st_mtime).isoformat()


def published_lastmods():
    """<lastmod> dates already published, so a rebuild can never move one back.

    page_lastmod() mixes two clocks: git's %cs is the committer's local date,
    date.today() is the builder's. A machine an hour behind the last committer
    (or just west of them) therefore computes yesterday for a page that already
    went out stamped today, and a <lastmod> that walks backwards tells crawlers
    the page was un-edited. Floor each date at what is already in sitemap.xml.
    """
    try:
        published = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    except OSError:
        return {}
    return dict(re.findall(r"<loc>([^<]*)</loc>\s*<lastmod>([^<]*)</lastmod>",
                           published))


def render_sitemap():
    rows = []
    floor = published_lastmods()
    for name, (out_rel, _active, is_home) in SITE.items():
        if name in SITEMAP_EXCLUDE:
            continue
        loc = SITE_URL + ("" if is_home else out_rel.replace("index.html", ""))
        lastmod = max(page_lastmod(name), floor.get(loc, ""))
        rows.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{SITEMAP_FREQ.get(name, 'monthly')}</changefreq>\n"
            f"    <priority>{SITEMAP_PRIORITY.get(name, '0.5')}</priority>\n"
            "  </url>"
        )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(rows) + "\n</urlset>\n")


def check_universal_links():
    """Assert the Universal Link file is still publishable.

    Nothing here builds it, but losing it breaks every /r/ invite link and it
    fails silently: links keep working in a browser and simply stop opening the
    app. Two ways it has actually gone missing on GitHub Pages: deleting
    .nojekyll (Jekyll refuses to publish directories starting with a dot), and
    switching Pages from branch deploys to the Actions flow (the
    upload-pages-artifact action excludes dotfiles by default).

    Editing the file is expensive: Apple's CDN takes up to a day to reach new
    installs and about a week to reach existing ones, with no way to purge. So
    it is worth catching a mistake here rather than after the wait.
    """
    problems = []
    if not (ROOT / ".nojekyll").exists():
        problems.append(".nojekyll is missing, so Pages will not publish /.well-known/")

    aasa = ROOT / ".well-known" / "apple-app-site-association"
    if not aasa.exists():
        problems.append("missing .well-known/apple-app-site-association")
    else:
        if aasa.suffix:
            problems.append("the file must have no extension, Apple looks for it by exact name")
        try:
            data = json.loads(aasa.read_text())
        except ValueError as exc:
            problems.append(f"apple-app-site-association is not valid JSON: {exc}")
        else:
            details = data.get("applinks", {}).get("details", [])
            paths = [c.get("/") for d in details for c in d.get("components", [])]
            paths += [p for d in details for p in d.get("paths", [])]
            # Bare /r matters: strip the trailing slash, which shorteners and
            # some messaging apps do, and a /r/* pattern no longer matches.
            for wanted in ("/r", "/r/", "/r/*"):
                if wanted not in paths:
                    problems.append(f"apple-app-site-association does not cover {wanted}")
            if any("appID" in d and "appIDs" in d for d in details):
                problems.append("do not mix the appID/paths and appIDs/components forms")

    if problems:
        print("universal links:")
        for p in problems:
            print(f"  {p}")
        raise SystemExit(1)


FIGURE = re.compile(r"<figure\b.*?</figure>", re.S)
FIG_ALT = re.compile(r'\balt="([^"]*)"')
FIG_CAPTION = re.compile(r"<figcaption>(.*?)</figcaption>", re.S)
STEP_NUM = re.compile(r'<span class="step-num">.*?</span>', re.S)
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def check_captions(pages):
    """A caption that quotes a screenshot has to still be true of it.

    Alt text drifting from its image is invisible. A visible caption saying
    "87, Optimal, ACWR 1.04" beside a screenshot that no longer says that is a
    public error, so every number in a caption must also appear in the alt text
    of the image it sits with. That is not proof the alt matches the pixels, but
    it does mean the two descriptions cannot drift apart silently.
    """
    problems = []
    for name, page in pages.items():
        for fig in FIGURE.findall(page):
            alt = FIG_ALT.search(fig)
            cap = FIG_CAPTION.search(fig)
            if not alt or not cap:
                continue
            text = re.sub(r"<[^>]+>", " ", STEP_NUM.sub(" ", cap.group(1)))
            for number in NUMBER.findall(text):
                if number not in alt.group(1):
                    problems.append(f"{name}: caption says {number}, the alt beside it does not")
    if problems:
        print("captions:")
        for p in problems:
            print(f"  {p}")
        raise SystemExit(1)


def main():
    check = "--check" in sys.argv[1:]
    partials = (
        load(PARTIALS / "head-common.html"),
        load(PARTIALS / "footer.html"),
        load(PARTIALS / "waitlist-form.html"),
        load(PARTIALS / "nav.html"),
    )

    drifted = []
    rendered = {}
    for name, (out_rel, active, is_home) in SITE.items():
        page = render(name, active, is_home, partials)
        rendered[out_rel] = page
        out = ROOT / out_rel
        if check:
            if not out.exists() or out.read_text() != page:
                drifted.append(out_rel)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page)
        print(f"  {out_rel}")

    sitemap = render_sitemap()
    sitemap_out = ROOT / "sitemap.xml"
    stale_dates = False
    if check:
        if not sitemap_out.exists():
            drifted.append("sitemap.xml")
        elif sitemap_out.read_text() != sitemap:
            # <lastmod> cannot be checked reproducibly: the sitemap is built
            # before the commit that carries it, so it stamps today's local
            # date, while the commit it lands in gets a committer date from
            # whatever machine makes it. A squash merge crossing midnight UTC
            # is enough to put the two a day apart. Structure still has to
            # match exactly; a date-only difference is worth reporting, not
            # worth failing a build over.
            bare = lambda s: LASTMOD.sub("<lastmod/>", s)
            if bare(sitemap_out.read_text()) != bare(sitemap):
                drifted.append("sitemap.xml")
            else:
                stale_dates = True
    else:
        sitemap_out.write_text(sitemap)
        print("  sitemap.xml")

    check_universal_links()
    check_captions(rendered)

    if check:
        if drifted:
            print("stale (rebuild with: python3 scripts/build_site.py):")
            for rel in drifted:
                print(f"  {rel}")
            raise SystemExit(1)
        if stale_dates:
            print("sitemap.xml: same URLs, some <lastmod> dates behind "
                  "(rebuild to refresh them)")
        print("built output matches src/, no drift")


if __name__ == "__main__":
    main()
