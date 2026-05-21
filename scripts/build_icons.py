"""Generate favicon and Apple touch icon assets for versus24.net.

Outputs:
  assets/favicon-16.png
  assets/favicon-32.png
  assets/favicon-48.png
  assets/favicon.ico            (multi-res 16/32/48)
  assets/apple-touch-icon.png   (180×180, iOS home screen)
  assets/icon-192.png           (PWA / Android)
  assets/icon-512.png           (PWA / Android, maskable-safe)

Design: dark background, bold white "V", amber dot — echoes the
VERSUS• wordmark used on the OG image and matches --bg / --accent.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

BG = (11, 13, 17)            # --bg, exact value used in theme-color
INK = (245, 245, 247)        # --ink
ACCENT = (232, 163, 61)      # --accent

F_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)


def render_icon(size: int, *, dot: bool = True) -> Image.Image:
    """Render a square icon at the given pixel size.

    Designed at high resolution (size × scale) then downsampled with
    LANCZOS so small sizes stay sharp.
    """
    scale = 4 if size <= 64 else 2 if size <= 256 else 1
    S = size * scale
    img = Image.new("RGB", (S, S), BG)
    draw = ImageDraw.Draw(img)

    # Font size: V occupies ~72% of the icon height
    font = ImageFont.truetype(F_BOLD, int(S * 0.78))
    b = draw.textbbox((0, 0), "V", font=font)
    tw, th = b[2] - b[0], b[3] - b[1]
    # Center; nudge up slightly to account for typographic descender area
    nudge_x = -2 if size <= 32 else 0  # tiny optical centering at tab size
    x = (S - tw) // 2 - b[0] + (nudge_x * scale)
    y = (S - th) // 2 - b[1] - int(S * 0.04)
    draw.text((x, y), "V", font=font, fill=INK)

    # Amber dot — sits at the bottom-right of the V, mirroring VERSUS•
    if dot and size >= 32:
        r = max(2, int(S * 0.07))
        cx = int(S * 0.78)
        cy = int(S * 0.74)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ACCENT)

    if scale > 1:
        img = img.resize((size, size), Image.LANCZOS)
    return img


# Standard favicons
for sz in (16, 32, 48):
    render_icon(sz, dot=(sz >= 32)).save(ASSETS / f"favicon-{sz}.png", "PNG", optimize=True)

# Multi-resolution ICO — Pillow packs all sizes into one .ico
ico_base = render_icon(48, dot=True)
ico_base.save(
    ASSETS / "favicon.ico",
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48)],
)

# Apple touch icon (iOS home screen)
render_icon(180, dot=True).save(ASSETS / "apple-touch-icon.png", "PNG", optimize=True)

# PWA / Android
render_icon(192, dot=True).save(ASSETS / "icon-192.png", "PNG", optimize=True)
render_icon(512, dot=True).save(ASSETS / "icon-512.png", "PNG", optimize=True)

for p in sorted(ASSETS.glob("favicon*")) + sorted(ASSETS.glob("apple-touch-*")) + sorted(ASSETS.glob("icon-*")):
    print(f"  {p.name:28s} {p.stat().st_size:>6} bytes")
