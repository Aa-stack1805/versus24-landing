"""Generate og-image.png (1200×630) for versus24.net link previews.

Re-run after brand or tagline changes. Output is committed to assets/.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 1200, 630
BG = (0, 0, 0)              # --bg, pure black per design system
INK = (255, 255, 255)       # --text
MUTED = (168, 168, 174)     # --text-subtle
ACCENT = (212, 168, 67)     # --gold (D4A843)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
F_BOLD = f"{FONT_DIR}/DejaVuSans-Bold.ttf"
F_REG = f"{FONT_DIR}/DejaVuSans.ttf"

PAD_X = 80

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img, "RGBA")

def text_size(text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1], b[1]  # width, height, top-offset

# Amber accent bar (left edge)
draw.rectangle((0, 0), fill=ACCENT) if False else draw.rectangle((0, 0, 8, H), fill=ACCENT)

# Eyebrow chip
chip_font = ImageFont.truetype(F_BOLD, 22)
chip_text = "THE ATHLETE'S OPERATING SYSTEM"
cw, ch, ctop = text_size(chip_text, chip_font)
chip_pad_x, chip_pad_y = 18, 10
chip_x, chip_y = PAD_X, 120
chip_box = (chip_x, chip_y, chip_x + cw + chip_pad_x * 2, chip_y + ch + chip_pad_y * 2)
draw.rounded_rectangle(chip_box, radius=4, fill=(232, 163, 61, 40), outline=(232, 163, 61, 90), width=1)
draw.text((chip_x + chip_pad_x, chip_y + chip_pad_y - ctop), chip_text, font=chip_font, fill=ACCENT)

# Headline — two lines, second amber. Pick a size that fits in the column.
MAX_LINE_W = W - PAD_X * 2
line1, line2 = "Train like the", "sport demands."
# Auto-fit: shrink font until the longer of the two lines fits.
size = 110
while size > 60:
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
draw.text((PAD_X, y - t2), line2, font=headline_font, fill=ACCENT)
y += h2 + 36

# Subline
sub_font = ImageFont.truetype(F_REG, 26)
sub_text = "Combat · Strength · Endurance · Sport · Recovery"
sw, sh, st = text_size(sub_text, sub_font)
draw.text((PAD_X, y - st), sub_text, font=sub_font, fill=MUTED)

# Wordmark bottom-right: VERSUS + amber dot
mark_font = ImageFont.truetype(F_BOLD, 40)
mark = "VERSUS"
mw, mh, mt = text_size(mark, mark_font)
mx = W - PAD_X - mw - 24  # leave room for dot
my = H - PAD_X - mh
draw.text((mx, my - mt), mark, font=mark_font, fill=INK)
dot_r = 8
dot_cx = mx + mw + 16
dot_cy = my + mh // 2 + 2
draw.ellipse((dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r), fill=ACCENT)

# URL bottom-left
url_font = ImageFont.truetype(F_REG, 24)
uw, uh, ut = text_size("versus24.net", url_font)
draw.text((PAD_X, H - PAD_X - uh - ut), "versus24.net", font=url_font, fill=MUTED)

out = Path(__file__).resolve().parent.parent / "assets" / "og-image.png"
out.parent.mkdir(exist_ok=True)
img.save(out, "PNG", optimize=True)
print(f"Wrote {out} ({out.stat().st_size // 1024} KB) headline={size}px")
