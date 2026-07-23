"""Assemble the static site from src/ into the repo root.

The site is plain static HTML served directly by GitHub Pages — there is no
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
files — re-run and commit whenever src/ changes.

    python3 scripts/build_site.py
"""
import re
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
    "support":   ("support/index.html",    None,       False),
    "terms":     ("terms/index.html",      None,       False),
}

NAV_ITEMS = ("features", "pricing", "faq", "about")
SCRIPT_TAG = '<script src="/assets/script.js" defer></script>'

# Legal pages ship without the analytics block (marked in head-common.html) —
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


def main():
    check = "--check" in sys.argv[1:]
    partials = (
        load(PARTIALS / "head-common.html"),
        load(PARTIALS / "footer.html"),
        load(PARTIALS / "waitlist-form.html"),
        load(PARTIALS / "nav.html"),
    )

    drifted = []
    for name, (out_rel, active, is_home) in SITE.items():
        page = render(name, active, is_home, partials)
        out = ROOT / out_rel
        if check:
            if not out.exists() or out.read_text() != page:
                drifted.append(out_rel)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page)
        print(f"  {out_rel}")

    if check:
        if drifted:
            print("stale (rebuild with: python3 scripts/build_site.py):")
            for rel in drifted:
                print(f"  {rel}")
            raise SystemExit(1)
        print("built output matches src/ — no drift")


if __name__ == "__main__":
    main()
