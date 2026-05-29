# Brand-Assets im Champagne-Gold-Look (passend zu og-image.png)
#   - instagram_logo.png  : 1080x1080  (umkreistes Z, Profilbild)
#   - linkedin_banner.png : 1584x396   (umkreistes Z + Schriftzug + Untertitel)
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
import random, os

HERE = os.path.dirname(os.path.abspath(__file__))

# ── Gold-Palette (aus index.html) ─────────────────────────────────────────────
GOLD_HI = np.array([243, 201, 105], dtype=np.float32)   # #f3c969
COPPER  = np.array([224, 163,  90], dtype=np.float32)   # #e0a35a

def grad2(t):
    t = t[:, np.newaxis]
    return GOLD_HI * (1 - t) + COPPER * t

# ── Schriften ─────────────────────────────────────────────────────────────────
FD = "C:/Windows/Fonts"
def load_font(names, size):
    for n in names:
        p = os.path.join(FD, n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()
SERIF = ("georgiab.ttf", "timesbd.ttf", "arialbd.ttf")
SANS  = ("segoeui.ttf", "arial.ttf")

# ══════════════════════════════════════════════════════════════════════════════
# Hintergrund: Tiefschwarz + dezente Gold-Lichtpools + feines Raster + Partikel
# ══════════════════════════════════════════════════════════════════════════════
def make_bg(W, H, seed=7):
    Y, X = np.ogrid[:H, :W]
    base = np.broadcast_to(np.array([8, 8, 10], dtype=np.float32), (H, W, 3)).copy()
    gx = (X % 66 == 0).astype(np.float32)
    gy = (Y % 66 == 0).astype(np.float32)
    grid = np.maximum(gx, gy)[:, :, np.newaxis]
    base += grid * np.array([4.0, 4.0, 5.0])

    def glow(cx, cy, rx, ry, col, strength, power=2.2):
        d = np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2)
        t = np.clip(1 - d, 0, 1)[:, :, np.newaxis] ** power
        return col * (t * strength)

    g = np.zeros((H, W, 3), dtype=np.float32)
    g += glow(W * 0.15, H * 0.12, W * 0.42, H * 0.55, np.array([66, 52, 22]), 1.0, 2.2)
    g += glow(W * 0.88, H * 0.88, W * 0.44, H * 0.55, np.array([58, 42, 18]), 0.85, 2.4)
    base += g
    base = np.clip(base, 0, 255).astype(np.uint8)
    img = Image.fromarray(base, 'RGB').convert('RGBA')

    d = ImageDraw.Draw(img)
    random.seed(seed)
    for _ in range(int(W * H / 18000)):
        px = random.randint(20, W - 20); py = random.randint(20, H - 20)
        pr = random.uniform(0.6, 1.9); pa = random.randint(15, 55)
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(243, 201, 105, pa))
    return img

# ══════════════════════════════════════════════════════════════════════════════
# Z-Symbol (Form aus favicon.svg) mit Gold-Verlauf, in beliebiger Pixelgroesse
# ══════════════════════════════════════════════════════════════════════════════
def make_z(size):
    f = size / 38.0
    p_tl = (11 * f, 13 * f); p_tr = (27 * f, 13 * f)
    p_bl = (11 * f, 25 * f); p_br = (27 * f, 25 * f)
    dot_r = 2.6 * f
    lw = max(2, int(2.0 * f))
    mask = Image.new('L', (size, size), 0)
    dm = ImageDraw.Draw(mask)
    dm.line([p_tl, p_tr], fill=255, width=lw)
    dm.line([p_tr, p_bl], fill=255, width=lw)
    dm.line([p_bl, p_br], fill=255, width=lw)
    for cx, cy in [p_tl, p_tr, p_bl, p_br]:
        dm.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=255)
    Xi = np.arange(size, dtype=np.float32)
    x_l = p_tl[0] - dot_r; x_r = p_tr[0] + dot_r
    t = np.clip((Xi - x_l) / max(x_r - x_l, 1), 0, 1)
    cols = grad2(t).astype(np.uint8)
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[:, :, :3] = cols[np.newaxis, :, :]
    arr[:, :, 3] = 255
    z = Image.fromarray(arr, 'RGBA')
    z.putalpha(mask)
    return z

def make_z_tight(target_h, big=900):
    """Z auf seine sichtbare Flaeche zugeschnitten und auf Zielhoehe skaliert."""
    z = make_z(big)
    z = z.crop(z.getbbox())
    ratio = target_h / z.height
    return z.resize((max(1, int(round(z.width * ratio))), target_h), Image.LANCZOS)

# ══════════════════════════════════════════════════════════════════════════════
# Umkreistes Z: zwei Gold-Ringe (Orbit-Look) + kleiner Orbit-Punkt + Z in Mitte
# (per Supersampling scharf gerendert)
# ══════════════════════════════════════════════════════════════════════════════
def make_encircled_z(d, ss=4):
    D = d * ss
    canvas = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    cd = ImageDraw.Draw(canvas)
    cx = cy = D / 2.0

    r1 = D * 0.47                                   # aeusserer Ring (kraeftig)
    cd.ellipse([cx - r1, cy - r1, cx + r1, cy + r1],
               outline=(243, 201, 105, 175), width=max(2, int(D * 0.0075)))
    r2 = D * 0.40                                   # innerer Ring (dezent)
    cd.ellipse([cx - r2, cy - r2, cx + r2, cy + r2],
               outline=(243, 201, 105, 75), width=max(1, int(D * 0.004)))

    dotr = D * 0.017                                # Orbit-Punkt oben auf dem Ring
    cd.ellipse([cx - dotr, cy - r1 - dotr, cx + dotr, cy - r1 + dotr],
               fill=(243, 201, 105, 255))

    z = make_z(int(D * 0.42))                       # Z mittig
    canvas.alpha_composite(z, (int(cx - z.width / 2), int(cy - z.height / 2)))
    return canvas.resize((d, d), Image.LANCZOS)

# ── gesperrter (Letter-Spacing) Text ──────────────────────────────────────────
def spaced_width(s, font, track):
    return sum(font.getlength(ch) + track for ch in s) - track
def draw_spaced(draw, xy, s, font, fill, track):
    x, y = xy
    for ch in s:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + track

def soft_glow(W, H, cx, cy, r, color, alpha, blur):
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, alpha))
    return g.filter(ImageFilter.GaussianBlur(blur))

# ══════════════════════════════════════════════════════════════════════════════
# 1) INSTAGRAM-PROFILBILD  1080x1080
# ══════════════════════════════════════════════════════════════════════════════
W = H = 1080
img = make_bg(W, H, seed=7)
z_h = 410                                   # ausgewogen: weder zu gross noch zu klein
zimg = make_z_tight(z_h)
zw = zimg.width
cx, cy = W // 2, H // 2
img = Image.alpha_composite(img, soft_glow(W, H, cx, cy, z_h * 0.85, (243, 201, 105), 40, 60))
img.alpha_composite(zimg, (int(cx - zw / 2), int(cy - z_h / 2)))
out_ig = os.path.join(HERE, "instagram_logo.png")
img.convert('RGB').save(out_ig, 'PNG', optimize=True)
print(f"Instagram-Logo gespeichert: {out_ig}  |  {W}x{H} px")

# ══════════════════════════════════════════════════════════════════════════════
# 2) LINKEDIN-BANNER  1584x396  (freies Z neben dem Schriftzug, Untertitel mittig)
# ══════════════════════════════════════════════════════════════════════════════
W, H = 1584, 396
img = make_bg(W, H, seed=7)

title_font = load_font(SERIF, 96)
sub_font   = load_font(SANS, 30)
TITLE = "Ziegler AI"
SUB   = "KI-AUTOMATISIERUNGEN FÜR UNTERNEHMEN"
track = 5

bbT = title_font.getbbox(TITLE)
tw, th = bbT[2] - bbT[0], bbT[3] - bbT[1]
bbS = sub_font.getbbox("Ag")
sh = bbS[3] - bbS[1]
sw = spaced_width(SUB, sub_font, track)

# Freies Z (ohne Kreis) in aehnlicher Groesse wie der Schriftzug
z_h = int(th * 1.05)
zimg = make_z_tight(z_h)
zw = zimg.width

gap   = 42                                  # Abstand Z <-> Schriftzug
gap_v = 24                                  # Abstand Zeile <-> Untertitel
row_w = zw + gap + tw
row_h = max(z_h, th)
block_h = row_h + gap_v + sh
cy = H // 2
top = cy - block_h / 2
row_cy = top + row_h / 2
gx0 = int((W - row_w) // 2)                 # Gruppe (Z + Schriftzug) horizontal zentriert

# Freies Z mit dezentem Schein, vertikal an der Zeilenmitte ausgerichtet
img = Image.alpha_composite(img, soft_glow(W, H, gx0 + zw / 2, row_cy, z_h * 0.7, (243, 201, 105), 34, 38))
img.alpha_composite(zimg, (gx0, int(row_cy - z_h / 2)))

# Schriftzug "Ziegler AI" in Weiss, rechts neben dem Z
text_x = gx0 + zw + gap
ty = int(row_cy - th / 2) - bbT[1]
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).text((text_x, ty), TITLE, font=title_font, fill=(255, 255, 255, 55))
img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(14)))
draw = ImageDraw.Draw(img)
draw.text((text_x, ty), TITLE, font=title_font, fill=(255, 255, 255, 255))

# Untertitel symmetrisch unter der gesamten Gruppe (Z + Schriftzug) zentriert
sub_x = (W - sw) / 2
sub_y = top + row_h + gap_v
draw_spaced(draw, (sub_x, sub_y), SUB, sub_font, (188, 178, 152, 255), track)

out_li = os.path.join(HERE, "linkedin_banner.png")
img.convert('RGB').save(out_li, 'PNG', optimize=True)
print(f"LinkedIn-Banner gespeichert: {out_li}  |  {W}x{H} px")
