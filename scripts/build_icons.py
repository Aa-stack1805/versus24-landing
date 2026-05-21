"""Derive favicon and Apple touch icon set from assets/appicon.png.

Re-run after replacing the master app icon. The source is treated as
authoritative — no design decisions live in this script, just
high-quality downsampling.

Outputs (all in assets/):
  favicon-16.png, favicon-32.png, favicon-48.png  – PNG favicons (cropped)
  favicon.ico                                     – multi-res 16/32/48
  apple-touch-icon.png  (180×180)                 – iOS home screen
  icon-192.png, icon-512.png                      – PWA / Android

Small browser favicons (≤48px) use a tight center crop so the hex mark
fills the canvas — at 16×16 every pixel counts and the outer glow just
becomes mud. Larger sizes keep the full-bleed design exactly as it
appears on the App Store icon.
"""
from pathlib import Path
from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SRC = ASSETS / "appicon.png"

src = Image.open(SRC).convert("RGB")  # source is opaque; flatten for portability
W, H = src.size
assert W == H, f"appicon.png must be square, got {src.size}"

# Tight crop = inner 72% — keeps hex + immediate glow, trims dark padding.
CROP_RATIO = 0.72
crop_size = int(W * CROP_RATIO)
crop_off = (W - crop_size) // 2
src_cropped = src.crop((crop_off, crop_off, crop_off + crop_size, crop_off + crop_size))


def resized(image: Image.Image, size: int) -> Image.Image:
    return image.resize((size, size), Image.LANCZOS)


# Small favicons — use the tightened crop
for sz in (16, 32, 48):
    resized(src_cropped, sz).save(ASSETS / f"favicon-{sz}.png", "PNG", optimize=True)

# Multi-resolution ICO embeds 16/32/48 PNGs in one file
resized(src_cropped, 48).save(
    ASSETS / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)]
)

# Full-bleed for app-icon-style sizes
resized(src, 180).save(ASSETS / "apple-touch-icon.png", "PNG", optimize=True)
resized(src, 192).save(ASSETS / "icon-192.png", "PNG", optimize=True)
resized(src, 512).save(ASSETS / "icon-512.png", "PNG", optimize=True)

for p in sorted(ASSETS.iterdir()):
    if p.name.startswith(("favicon", "apple-touch", "icon-")):
        print(f"  {p.name:24s} {p.stat().st_size:>7} bytes")
