"""Derive optimized WebP screenshots from the raster sources in assets/screens/.

Re-run after adding or replacing a screenshot. Source captures (PNG/JPEG) are
treated as authoritative — drop the full-resolution capture into assets/screens/,
run this script, commit the generated .webp, and the heavy source can then be
removed from the working tree (it stays recoverable in git history).

App screenshots ship inside small CSS frames (the phone mockup is 280px wide, so
a shot never paints wider than ~260 CSS px — ~780px even at 3x DPR). Serving the
full 1170–1206px captures wasted 1–2MB each. Downscaling to MAX_W and encoding as
WebP brings every shot to ~35–65KB with no visible loss at display size.

WebP only — favicons and the social/OG image stay PNG/ICO (handled by
build_icons.py / build_og.py) because social scrapers don't all accept WebP.
"""
from pathlib import Path
from PIL import Image

SCREENS = Path(__file__).resolve().parent.parent / "assets" / "screens"
SOURCE_EXTS = {".png", ".jpg", ".jpeg"}

MAX_W = 900      # retina-safe for every on-page display context
QUALITY = 82     # visually lossless for flat app UI; ~95% smaller than source
METHOD = 6       # slowest/best WebP compression search


def main() -> None:
    sources = sorted(p for p in SCREENS.iterdir() if p.suffix.lower() in SOURCE_EXTS)
    if not sources:
        print("No raster sources in assets/screens/ — nothing to build.")
        return

    for src in sources:
        im = Image.open(src).convert("RGB")
        w, h = im.size
        if w > MAX_W:
            im = im.resize((MAX_W, round(h * MAX_W / w)), Image.LANCZOS)
        out = src.with_suffix(".webp")
        im.save(out, "WEBP", quality=QUALITY, method=METHOD)
        print(f"  {out.name:38s} {im.size[0]}x{im.size[1]:<5} {out.stat().st_size // 1024:>4}KB")


if __name__ == "__main__":
    main()
