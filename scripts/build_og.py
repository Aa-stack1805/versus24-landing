"""Generate 1200×630 OG link-preview images for versus24.net.

One shared homepage image (og-image.png) plus a dedicated image per key
landing page, each with its own headline and segment accent colour. Output
is committed to assets/. Re-run after brand, tagline, or headline changes:

    python3 scripts/build_og.py
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 1200, 630
BG = (0, 0, 0)              # --bg, pure black per design system
INK = (255, 255, 255)       # --text
MUTED = (168, 168, 174)     # --text-subtle
GOLD = (212, 168, 67)       # --gold (D4A843)

# Modality accents (match assets/style.css)
COMBAT = (224, 70, 62)      # --combat
STRENGTH = (228, 130, 24)   # --strength
ENDURANCE = (79, 163, 240)  # --endurance
SPORT = (34, 197, 94)       # --sport

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
F_BOLD = f"{FONT_DIR}/DejaVuSans-Bold.ttf"
F_REG = f"{FONT_DIR}/DejaVuSans.ttf"

PAD_X = 80
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def make_og(out_name, eyebrow, line1, line2, subline, accent):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img, "RGBA")

    def text_size(text, font):
        b = draw.textbbox((0, 0), text, font=font)
        return b[2] - b[0], b[3] - b[1], b[1]  # width, height, top-offset

    # Accent bar (left edge)
    draw.rectangle((0, 0, 8, H), fill=accent)

    # Eyebrow chip
    chip_font = ImageFont.truetype(F_BOLD, 22)
    cw, ch, ctop = text_size(eyebrow, chip_font)
    chip_pad_x, chip_pad_y = 18, 10
    chip_x, chip_y = PAD_X, 120
    chip_box = (chip_x, chip_y, chip_x + cw + chip_pad_x * 2, chip_y + ch + chip_pad_y * 2)
    draw.rounded_rectangle(chip_box, radius=4, fill=(*accent, 38), outline=(*accent, 95), width=1)
    draw.text((chip_x + chip_pad_x, chip_y + chip_pad_y - ctop), eyebrow, font=chip_font, fill=accent)

    # Headline: two lines, second in accent. Auto-fit so the wider line fits.
    MAX_LINE_W = W - PAD_X * 2
    size = 110
    while size > 54:
        h_font = ImageFont.truetype(F_BOLD, size)
        w1, _, _ = text_size(line1, h_font)
        w2, _, _ = text_size(line2, h_font)
        if max(w1, w2) <= MAX_LINE_W:
            break
        size -= 2
    headline_font = h_font

    y = chip_box[3] + 50
    w1, h1, t1 = text_size(line1, headline_font)
    draw.text((PAD_X, y - t1), line1, font=headline_font, fill=INK)
    y += h1 + 14
    w2, h2, t2 = text_size(line2, headline_font)
    draw.text((PAD_X, y - t2), line2, font=headline_font, fill=accent)
    y += h2 + 36

    # Subline
    sub_font = ImageFont.truetype(F_REG, 26)
    sw, sh, st = text_size(subline, sub_font)
    draw.text((PAD_X, y - st), subline, font=sub_font, fill=MUTED)

    # Wordmark bottom-right: VERSUS + accent dot, TRAINING beneath
    mark_font = ImageFont.truetype(F_BOLD, 38)
    sub_mark_font = ImageFont.truetype(F_REG, 16)
    mark, sub_mark = "VERSUS", "TRAINING"
    mw, mh, mt = text_size(mark, mark_font)
    sw2, sh2, st2 = text_size(sub_mark, sub_mark_font)
    dot_r, gap_for_dot = 7, 22
    total_w = mw + gap_for_dot
    mx = W - PAD_X - total_w
    my = H - PAD_X - mh - sh2 - 6
    draw.text((mx, my - mt), mark, font=mark_font, fill=INK)
    dot_cx = mx + mw + 12
    dot_cy = my + mh // 2 + 2
    draw.ellipse((dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r), fill=accent)
    draw.text((mx, my + mh + 4 - st2), sub_mark, font=sub_mark_font, fill=MUTED)

    # URL bottom-left
    url_font = ImageFont.truetype(F_REG, 24)
    uw, uh, ut = text_size("versus24.net", url_font)
    draw.text((PAD_X, H - PAD_X - uh - ut), "versus24.net", font=url_font, fill=MUTED)

    out = ASSETS / out_name
    out.parent.mkdir(exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"  {out_name:22s} {out.stat().st_size // 1024:>3} KB  headline={size}px")


PAGES = [
    # out_name,            eyebrow,                       line1,              line2,               subline,                                             accent
    ("og-image.png",       "THE ATHLETE'S OPERATING SYSTEM", "Train like the",  "sport demands.",    "Combat · Strength · Endurance · Sport · Recovery",  GOLD),
    ("og-fighters.png",    "FOR COMBAT ATHLETES",         "Train like",       "a fighter.",        "MMA · BJJ · Muay Thai · Boxing · Wrestling",        COMBAT),
    ("og-lifters.png",     "FOR LIFTERS",                 "Lift heavier.",    "Recover smarter.",  "PR detection · ACWR · Plateau alerts · Hevy import", STRENGTH),
    ("og-runners.png",     "FOR RUNNERS & CYCLISTS",      "Strava logs it.",  "Versus reads it.",  "HR zones · ACWR · Race taper · Strava + Garmin",    ENDURANCE),
    ("og-sports.png",      "FOR SPORT ATHLETES",          "Peak on game day.", "Not on Tuesday.",  "Basketball · Soccer · Hockey · Rugby · +12 more",   SPORT),
    ("og-hybrid.png",      "FOR HYBRID ATHLETES",         "Two sports.",      "Tracked properly.", "Cross-modality ACWR · Multi-modal programming",     GOLD),
    ("og-features.png",    "FEATURES",                    "Every feature.",   "Explained.",        "Sensei AI · Voice logging · Readiness · Apple Watch", GOLD),
    ("og-pricing.png",     "PRICING",                     "Free. Core. Elite.", "Honest pricing.", "Free forever · Core $9.99 · Elite $14.99 /mo",     GOLD),
]

if __name__ == "__main__":
    for args in PAGES:
        make_og(*args)
