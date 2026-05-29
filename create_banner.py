# LinkedIn-Banner im Aurora-Engineering-Stil (Lime-Akzente)
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
import random, os

W, H = 1584, 396

# ── Aurora-Farben (aus index.html / favicon.svg) ──────────────────────────────
LIME_HI = np.array([212, 255,  79], dtype=np.float32)   # #d4ff4f
LIME    = np.array([138, 255,  61], dtype=np.float32)   # #8aff3d
BLUE    = np.array([ 94, 179, 255], dtype=np.float32)   # #5eb3ff

# ══════════════════════════════════════════════════════════════════════════════
# 1. HINTERGRUND – fast-schwarz mit grünlichem Aurora-Schimmer
# ══════════════════════════════════════════════════════════════════════════════
Y, X = np.ogrid[:H, :W]

BASE = np.array([6, 6, 10], dtype=np.float32)            # #06060a
base = np.broadcast_to(BASE, (H, W, 3)).copy()

# Sehr subtiler links→rechts Gradient (Hauch mehr Grün rechts)
base[:, :, 1] += (X / W * 3).astype(np.float32)

# Feines technisches Gitter (vektorisiert, sehr schwach)
gx = (X % 60 == 0).astype(np.float32)
gy = (Y % 60 == 0).astype(np.float32)
grid = np.maximum(gx, gy)[:, :, np.newaxis]
base += grid * np.array([3.0, 5.0, 2.5])                 # leicht grünstichig

# Zentraler grün-schwarzer Orb (wie radial-gradient im Favicon: #0e1a08)
ORB_COL = np.array([14, 26, 8], dtype=np.float32)
cx_orb = W * 0.58
dist_orb = np.sqrt(((X - cx_orb) / (W * 0.45))**2 + ((Y - H/2) / (H * 0.80))**2)
t_orb = np.clip(1 - dist_orb, 0, 1)[:, :, np.newaxis] ** 2.0
base = base * (1 - t_orb * 0.80) + ORB_COL * (t_orb * 0.80)

# Lime-Akzent oben rechts (sehr subtil)
ACC_COL = np.array([26, 34, 10], dtype=np.float32)
dist_a = np.sqrt(((X - W*0.90) / (W*0.28))**2 + ((Y + H*0.10) / (H*0.55))**2)
t_a = np.clip(1 - dist_a, 0, 1)[:, :, np.newaxis] ** 2.5
base = base * (1 - t_a * 0.40) + ACC_COL * (t_a * 0.40)

# Blau-Akzent unten links (sehr subtil)
BLU_COL = np.array([8, 16, 30], dtype=np.float32)
dist_c = np.sqrt(((X - 0) / (W*0.22))**2 + ((Y - H) / (H*0.55))**2)
t_c = np.clip(1 - dist_c, 0, 1)[:, :, np.newaxis] ** 3.0
base = base * (1 - t_c * 0.30) + BLU_COL * (t_c * 0.30)

base = np.clip(base, 0, 255).astype(np.uint8)
img = Image.fromarray(base, 'RGB').convert('RGBA')

# Partikel im Lime/Blau-Farbspektrum
draw_bg = ImageDraw.Draw(img)
random.seed(17)
colors_int = [(212,255,79), (138,255,61), (94,179,255), (180,255,120)]
for _ in range(55):
    px = random.randint(12, W - 12)
    py = random.randint(6,  H - 6)
    pr = random.uniform(0.6, 1.9)
    pa = random.randint(18, 70)
    c  = random.choice(colors_int)
    draw_bg.ellipse([px-pr, py-pr, px+pr, py+pr], fill=(*c, pa))

# ══════════════════════════════════════════════════════════════════════════════
# 2. Z-SYMBOL  (Form aus favicon.svg: M11 13 H27 L11 25 H27, Punkte an 4 Ecken)
# ══════════════════════════════════════════════════════════════════════════════
Z_SIZE = 195
f = Z_SIZE / 38.0

p_tl = (11*f, 13*f);  p_tr = (27*f, 13*f)
p_bl = (11*f, 25*f);  p_br = (27*f, 25*f)
dot_r = 3.0 * f
lw = max(7, int(2.2 * f))

def draw_z(drw, color, lw, dr):
    drw.line([p_tl, p_tr], fill=color, width=lw)   # oben
    drw.line([p_tr, p_bl], fill=color, width=lw)   # diagonal
    drw.line([p_bl, p_br], fill=color, width=lw)   # unten
    for cx, cy in [p_tl, p_tr, p_bl, p_br]:
        drw.ellipse([cx-dr, cy-dr, cx+dr, cy+dr], fill=color)

# Maske (weiß = Z-Form)
z_mask = Image.new('L', (Z_SIZE, Z_SIZE), 0)
draw_z(ImageDraw.Draw(z_mask), 255, lw, dot_r)

# Gradient LIME_HI → LIME → BLUE (diagonal-ähnlich über x)
x_l = int(p_tl[0] - dot_r);  x_r = int(p_tr[0] + dot_r)
Xi  = np.arange(Z_SIZE, dtype=np.float32)
t_x = np.clip((Xi - x_l) / max(x_r - x_l, 1), 0, 1)
# zweistufiger Lerp: 0→0.5 LIME_HI→LIME, 0.5→1 LIME→BLUE
def grad3(t):
    t = t[:, np.newaxis]
    a = LIME_HI * (1 - np.clip(t*2, 0, 1)) + LIME * np.clip(t*2, 0, 1)
    b = LIME    * (1 - np.clip(t*2-1, 0, 1)) + BLUE * np.clip(t*2-1, 0, 1)
    m = (t >= 0.5)
    return np.where(m, b, a)
grad_rgb = grad3(t_x).astype(np.uint8)                   # (Z,3)
grad_z = np.zeros((Z_SIZE, Z_SIZE, 4), dtype=np.uint8)
grad_z[:, :, :3] = grad_rgb[np.newaxis, :, :]
grad_z[:, :, 3]  = 255
z_sharp = Image.fromarray(grad_z, 'RGBA')
z_sharp.putalpha(z_mask)

def blurred(src, radius, alpha_scale):
    b = src.copy().filter(ImageFilter.GaussianBlur(radius))
    a = np.array(b, dtype=np.float32)
    a[:, :, 3] = np.clip(a[:, :, 3] * alpha_scale, 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')

z_canvas = Image.new('RGBA', (Z_SIZE, Z_SIZE), (0,0,0,0))
z_canvas = Image.alpha_composite(z_canvas, blurred(z_sharp, 20, 0.55))
z_canvas = Image.alpha_composite(z_canvas, blurred(z_sharp,  8, 0.70))
z_canvas = Image.alpha_composite(z_canvas, blurred(z_sharp,  3, 0.85))
z_canvas = Image.alpha_composite(z_canvas, z_sharp)

# ══════════════════════════════════════════════════════════════════════════════
# 3. TEXT  (Inter Bold, fällt auf Segoe/Arial zurück)
# ══════════════════════════════════════════════════════════════════════════════
FD = "C:/Windows/Fonts"
def load_font(size):
    for name in ("Inter-Bold.ttf", "Inter-SemiBold.ttf", "segoeuib.ttf", "arialbd.ttf"):
        p = os.path.join(FD, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.truetype(os.path.join(FD, "arialbd.ttf"), size)

font = load_font(118)
TITLE = "Ziegler AI"
bb = font.getbbox(TITLE)
tw = bb[2] - bb[0]

# ══════════════════════════════════════════════════════════════════════════════
# 4. LAYOUT – gemeinsam zentriert, leicht über Bannermitte
# ══════════════════════════════════════════════════════════════════════════════
SEP_GAP = 34;  SEP_W = 2;  TEXT_GAP = 34
total_w = Z_SIZE + SEP_GAP + SEP_W + TEXT_GAP + tw
start_x = (W - total_w) // 2

z_x    = start_x
sep_x  = z_x + Z_SIZE + SEP_GAP
text_x = sep_x + SEP_W + TEXT_GAP

VERT_OFF = -10
z_y    = (H - Z_SIZE) // 2 + VERT_OFF
text_y = H // 2 - (bb[1] + bb[3]) // 2 + VERT_OFF

# ══════════════════════════════════════════════════════════════════════════════
# 5. ZUSAMMENSETZEN
# ══════════════════════════════════════════════════════════════════════════════
img.paste(z_canvas, (z_x, z_y), z_canvas)

# Trennlinie (vertikal, Gradient transparent→lime→transparent)
SEP_HALF = 62
sep_arr = np.zeros((H, SEP_W, 4), dtype=np.uint8)
for y in range(H):
    dy2 = abs(y - H//2)
    if dy2 < SEP_HALF:
        a = int(120 * (1 - dy2 / SEP_HALF) ** 0.55)
        sep_arr[y, :] = [138, 255, 61, a]
img.paste(Image.fromarray(sep_arr, 'RGBA'), (sep_x, 0),
          Image.fromarray(sep_arr, 'RGBA'))

# Text-Glow (lime)
glow = Image.new('RGBA', (W, H), (0,0,0,0))
ImageDraw.Draw(glow).text((text_x, text_y), TITLE, font=font,
                          fill=(138, 255, 61, 80))
img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(13)))

# Gradient-Text LIME_HI → BLUE
t_mask = Image.new('L', (W, H), 0)
ImageDraw.Draw(t_mask).text((text_x, text_y), TITLE, font=font, fill=255)

Xi2  = np.arange(W, dtype=np.float32)
t_x2 = np.clip((Xi2 - text_x) / max(tw, 1), 0, 1)
gcol = grad3(t_x2).astype(np.uint8)
g_arr = np.zeros((H, W, 4), dtype=np.uint8)
g_arr[:, :, :3] = gcol[np.newaxis, :, :]
g_arr[:, :, 3]  = 255
g_img = Image.fromarray(g_arr, 'RGBA')
g_img.putalpha(t_mask)
img = Image.alpha_composite(img, g_img)

# ══════════════════════════════════════════════════════════════════════════════
# 6. SPEICHERN
# ══════════════════════════════════════════════════════════════════════════════
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "linkedin_banner.png")
img.convert('RGB').save(out, 'PNG', optimize=True)
print(f"Banner gespeichert: {out}  |  {W}x{H} px")
