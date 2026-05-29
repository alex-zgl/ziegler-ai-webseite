# OG-Bild (1200x630) im Champagne-Gold-Look – passend zur Website
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
import random, os

W, H = 1200, 630

# ── Gold-Palette (aus index.html) ─────────────────────────────────────────────
GOLD_HI = np.array([243, 201, 105], dtype=np.float32)   # #f3c969
GOLD    = np.array([224, 169,  63], dtype=np.float32)   # #e0a93f
COPPER  = np.array([224, 163,  90], dtype=np.float32)   # #e0a35a

def grad2(t):
    """Linearer Verlauf Gold-Hell -> Kupfer entlang t in [0,1]."""
    t = t[:, np.newaxis]
    return GOLD_HI * (1 - t) + COPPER * t

# ══════════════════════════════════════════════════════════════════════════════
# 1. HINTERGRUND – Tiefschwarz mit dezenten Gold-Lichtpools + feinem Raster
# ══════════════════════════════════════════════════════════════════════════════
Y, X = np.ogrid[:H, :W]
BASE = np.array([8, 8, 10], dtype=np.float32)            # #08080a
base = np.broadcast_to(BASE, (H, W, 3)).copy()

# Feines technisches Gitter (sehr schwach)
gx = (X % 66 == 0).astype(np.float32)
gy = (Y % 66 == 0).astype(np.float32)
grid = np.maximum(gx, gy)[:, :, np.newaxis]
base += grid * np.array([4.0, 4.0, 5.0])

def glow(cx, cy, rx, ry, col, strength, power=2.2):
    d = np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2)
    t = np.clip(1 - d, 0, 1)[:, :, np.newaxis] ** power
    return col * (t * strength)

g = np.zeros((H, W, 3), dtype=np.float32)
g += glow(W * 0.15, H * 0.10, W * 0.42, H * 0.5, np.array([66, 52, 22]), 1.0, 2.2)
g += glow(W * 0.88, H * 0.88, W * 0.44, H * 0.55, np.array([58, 42, 18]), 0.85, 2.4)
base += g
base = np.clip(base, 0, 255).astype(np.uint8)
img = Image.fromarray(base, 'RGB').convert('RGBA')

# Gold-Partikel (sehr subtil)
dbg = ImageDraw.Draw(img)
random.seed(7)
for _ in range(42):
    px = random.randint(20, W - 20)
    py = random.randint(20, H - 20)
    pr = random.uniform(0.6, 1.8)
    pa = random.randint(15, 55)
    dbg.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(243, 201, 105, pa))

# ══════════════════════════════════════════════════════════════════════════════
# 2. Z-SYMBOL (Form aus favicon.svg) – per Supersampling scharf gerendert
# ══════════════════════════════════════════════════════════════════════════════
Z_SIZE = 140
SS = 4                      # Supersampling-Faktor fuer hohe Schaerfe
ZS = Z_SIZE * SS
f = ZS / 38.0
p_tl = (11 * f, 13 * f); p_tr = (27 * f, 13 * f)
p_bl = (11 * f, 25 * f); p_br = (27 * f, 25 * f)
dot_r = 2.6 * f
lw = max(2, int(2.0 * f))

def draw_z(drw, color, lw, dr):
    drw.line([p_tl, p_tr], fill=color, width=lw)
    drw.line([p_tr, p_bl], fill=color, width=lw)
    drw.line([p_bl, p_br], fill=color, width=lw)
    for cx, cy in [p_tl, p_tr, p_bl, p_br]:
        drw.ellipse([cx - dr, cy - dr, cx + dr, cy + dr], fill=color)

# In hoher Aufloesung zeichnen ...
z_mask_hi = Image.new('L', (ZS, ZS), 0)
draw_z(ImageDraw.Draw(z_mask_hi), 255, lw, dot_r)

Xi = np.arange(ZS, dtype=np.float32)
x_l = p_tl[0] - dot_r; x_r = p_tr[0] + dot_r
t_x = np.clip((Xi - x_l) / max(x_r - x_l, 1), 0, 1)
grad_rgb = grad2(t_x).astype(np.uint8)
grad_z = np.zeros((ZS, ZS, 4), dtype=np.uint8)
grad_z[:, :, :3] = grad_rgb[np.newaxis, :, :]
grad_z[:, :, 3] = 255
z_hi = Image.fromarray(grad_z, 'RGBA')
z_hi.putalpha(z_mask_hi)

# ... und sauber auf Zielgroesse herunterskalieren (LANCZOS = scharfe Kanten)
z_sharp = z_hi.resize((Z_SIZE, Z_SIZE), Image.LANCZOS)

def blurred(src, radius, alpha_scale):
    b = src.copy().filter(ImageFilter.GaussianBlur(radius))
    a = np.array(b, dtype=np.float32)
    a[:, :, 3] = np.clip(a[:, :, 3] * alpha_scale, 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')

z_canvas = Image.new('RGBA', (Z_SIZE, Z_SIZE), (0, 0, 0, 0))
z_canvas = Image.alpha_composite(z_canvas, blurred(z_sharp, 16, 0.5))
z_canvas = Image.alpha_composite(z_canvas, blurred(z_sharp, 6, 0.7))
z_canvas = Image.alpha_composite(z_canvas, z_sharp)

# ══════════════════════════════════════════════════════════════════════════════
# 3. SCHRIFTEN (Serif fuer Titel = Website-Look, Sans fuer Untertitel)
# ══════════════════════════════════════════════════════════════════════════════
FD = "C:/Windows/Fonts"
def load_font(names, size):
    for n in names:
        p = os.path.join(FD, n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

title_font = load_font(("georgiab.ttf", "timesbd.ttf", "arialbd.ttf"), 108)
sub_font   = load_font(("segoeui.ttf", "arial.ttf"), 28)

# ── Vertikales Layout (mittig als Block) ──────────────────────────────────────
z_x = (W - Z_SIZE) // 2
z_y = 140
img.paste(z_canvas, (z_x, z_y), z_canvas)

# ── Titel: Weiss, zentriert ───────────────────────────────────────────────────
TITLE = "Ziegler AI"
bb = title_font.getbbox(TITLE)
tw = bb[2] - bb[0]; th = bb[3] - bb[1]
tx = (W - tw) // 2 - bb[0]
top = z_y + Z_SIZE + 34          # gewuenschte sichtbare Oberkante
ty = top - bb[1]

# Dezenter weicher Glow
glow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow_layer).text((tx, ty), TITLE, font=title_font, fill=(255, 255, 255, 55))
img = Image.alpha_composite(img, glow_layer.filter(ImageFilter.GaussianBlur(16)))

# Weisser Titel
ddraw = ImageDraw.Draw(img)
ddraw.text((tx, ty), TITLE, font=title_font, fill=(255, 255, 255, 255))

# ── Untertitel: gesperrt, zentriert, dezent ───────────────────────────────────
SUB = "KI-AUTOMATISIERUNG FÜR UNTERNEHMEN"
track = 5
def spaced_width(s, font, track):
    return sum(font.getlength(ch) + track for ch in s) - track
sw = spaced_width(SUB, sub_font, track)
cx = (W - sw) / 2
sy = top + th + 30
for ch in SUB:
    ddraw.text((cx, sy), ch, font=sub_font, fill=(188, 178, 152, 255))
    cx += sub_font.getlength(ch) + track

# ══════════════════════════════════════════════════════════════════════════════
# 4. SPEICHERN
# ══════════════════════════════════════════════════════════════════════════════
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "og-image.png")
img.convert('RGB').save(out, 'PNG', optimize=True)
print(f"OG-Bild gespeichert: {out}  |  {W}x{H} px")
