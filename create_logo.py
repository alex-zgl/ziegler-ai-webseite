# Logo im Aurora-Engineering-Stil (basiert auf favicon.svg) – hochaufloesend
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import os

SS = 4                      # Supersampling-Faktor fuer glatte Kanten
S  = 1024                   # finale Logo-Groesse
N  = S * SS                 # Arbeitsaufloesung

# ── Aurora-Farben ─────────────────────────────────────────────────────────────
LIME_HI = np.array([212, 255,  79], dtype=np.float32)   # #d4ff4f
LIME    = np.array([138, 255,  61], dtype=np.float32)   # #8aff3d
BLUE    = np.array([ 94, 179, 255], dtype=np.float32)   # #5eb3ff

def grad3(t):
    """Lerp LIME_HI -> LIME -> BLUE ueber t in [0,1]."""
    t = np.asarray(t, dtype=np.float32)[:, np.newaxis]
    a = LIME_HI * (1 - np.clip(t*2, 0, 1))   + LIME * np.clip(t*2, 0, 1)
    b = LIME    * (1 - np.clip(t*2-1, 0, 1)) + BLUE * np.clip(t*2-1, 0, 1)
    return np.where(t >= 0.5, b, a)

# ══════════════════════════════════════════════════════════════════════════════
# 1. KREIS-HINTERGRUND  (radial: #0e1a08 Mitte -> #06060a Rand)
# ══════════════════════════════════════════════════════════════════════════════
Y, X = np.ogrid[:N, :N]
cx = cy = N / 2
R   = N / 2                                  # Aussenradius
dist = np.sqrt((X - cx)**2 + (Y - cy)**2) / R

INNER = np.array([14, 26, 8],  dtype=np.float32)   # #0e1a08
OUTER = np.array([ 6,  6, 10], dtype=np.float32)   # #06060a
t = np.clip(dist, 0, 1)[:, :, np.newaxis]
rgb = INNER * (1 - t) + OUTER * t

circle = np.zeros((N, N, 4), dtype=np.uint8)
circle[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
# Alpha = 255 innerhalb des Kreises, mit schmalem weichem Antialias-Saum am Rand
circle[:, :, 3] = (np.clip((1.0 - dist) / (1.5 / R), 0, 1) * 255).astype(np.uint8)
base = Image.fromarray(circle, 'RGBA')

# Lime-Ring (stroke #d4ff4f, opacity 0.6) knapp innerhalb des Randes
ring = Image.new('RGBA', (N, N), (0, 0, 0, 0))
dr = ImageDraw.Draw(ring)
ring_w = int(0.8 / 38 * N)                          # 0.8 von 38 (Favicon-Skala)
inset  = int(1.0 / 38 * N)
dr.ellipse([inset, inset, N - inset, N - inset],
           outline=(212, 255, 79, 153), width=max(ring_w, 2))
base = Image.alpha_composite(base, ring)

# ══════════════════════════════════════════════════════════════════════════════
# 2. Z-SYMBOL  (M11 13 H27 L11 25 H27 + Punkte an 4 Ecken), Favicon-Koordinaten
# ══════════════════════════════════════════════════════════════════════════════
f = N / 38.0                                        # Favicon-ViewBox = 38
p_tl = (11*f, 13*f);  p_tr = (27*f, 13*f)
p_bl = (11*f, 25*f);  p_br = (27*f, 25*f)
dot_r = 2.5 * f                                     # r=2.5 im Favicon
lw    = max(int(1.8 * f), 4)                        # stroke-width 1.8

def draw_z(drw, color, lw, dr_):
    drw.line([p_tl, p_tr], fill=color, width=lw)
    drw.line([p_tr, p_bl], fill=color, width=lw)
    drw.line([p_bl, p_br], fill=color, width=lw)
    # runde Linienenden / Knoten
    for cx_, cy_ in [p_tl, p_tr, p_bl, p_br]:
        drw.ellipse([cx_-dr_, cy_-dr_, cx_+dr_, cy_+dr_], fill=color)

# Maske der Z-Form
z_mask = Image.new('L', (N, N), 0)
draw_z(ImageDraw.Draw(z_mask), 255, lw, dot_r)

# Horizontaler Gradient LIME_HI -> LIME -> BLUE
x_l = p_tl[0] - dot_r;  x_r = p_tr[0] + dot_r
Xi  = np.arange(N, dtype=np.float32)
t_x = np.clip((Xi - x_l) / max(x_r - x_l, 1), 0, 1)
gcol = grad3(t_x).astype(np.uint8)
g_arr = np.zeros((N, N, 4), dtype=np.uint8)
g_arr[:, :, :3] = gcol[np.newaxis, :, :]
g_arr[:, :, 3]  = 255
z_sharp = Image.fromarray(g_arr, 'RGBA')
z_sharp.putalpha(z_mask)

def blurred(src, radius, alpha_scale):
    b = src.copy().filter(ImageFilter.GaussianBlur(radius))
    a = np.array(b, dtype=np.float32)
    a[:, :, 3] = np.clip(a[:, :, 3] * alpha_scale, 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')

# Glow (entspricht feGaussianBlur-Filter im Favicon) + scharfes Z
gr = 0.045 * N
base = Image.alpha_composite(base, blurred(z_sharp, gr,        0.55))
base = Image.alpha_composite(base, blurred(z_sharp, gr * 0.45, 0.75))
base = Image.alpha_composite(base, z_sharp)

# ══════════════════════════════════════════════════════════════════════════════
# 3. DOWNSAMPLE + SPEICHERN
# ══════════════════════════════════════════════════════════════════════════════
logo = base.resize((S, S), Image.LANCZOS)
out  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
logo.save(out, 'PNG', optimize=True)
print(f"Logo gespeichert: {out}  |  {S}x{S} px (transparenter Rand)")
