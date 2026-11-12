"""docs/pinout.png (Ukrainian) and docs/pinout_en.png (English) — full wiring diagram: module photos + coloured wires + every resistor.

Pins come from firmware/retro-go-overlay/components/retro-go/targets/retro-console/config.h.
Photos of the modules live in docs/parts/. Run: python docs/make_pinout.py [uk|en]  (no argument = both)
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
if len(sys.argv) < 2:
    for lang in ('uk', 'en'):
        subprocess.run([sys.executable, __file__, lang], check=True)
    sys.exit()
LANG = sys.argv[1]


def t(uk, en):
    return en if LANG == 'en' else uk

W, H, S = 3400, 2400, 2
PAPER = '#f4f1e8'
INK = '#1d1d1b'
C = {'red': '#d7332b', 'black': '#222222', 'yellow': '#f0c020', 'orange': '#ef7d22', 'green': '#2f9e4f',
     'blue': '#2a78d6', 'purple': '#8a4fc7', 'grey': '#8d9399', 'white': '#fbfbf7', 'brown': '#8b5a2b',
     'pink': '#e85c9a', 'cyan': '#19a9bf', 'teal': '#0f8f7a'}


def font(name, size):
    for n in (name, 'consola.ttf', 'DejaVuSansMono.ttf'):
        try:
            return ImageFont.truetype(n, int(size * S))
        except OSError:
            pass
    return ImageFont.load_default()


def MONO(s): return font('consola.ttf', s)
def MONOB(s): return font('consolab.ttf', s)
def HEAD(s): return font('bahnschrift.ttf', s)


img = Image.new('RGB', (W * S, H * S), PAPER)
d = ImageDraw.Draw(img)


def P(*v):
    return tuple(int(round(x * S)) for x in v)


def text(x, y, s, size=17, fill=INK, anchor='lm', bold=True, f=None):
    d.text(P(x, y), s, font=f or (MONOB if bold else MONO)(size), fill=fill, anchor=anchor)


def tag(x, y, s, anchor='lm', size=15, bg='#ffffff', fg=INK):
    f = MONOB(size)
    w = d.textlength(s, font=f) / S + 12
    x0 = x if anchor[0] == 'l' else (x - w if anchor[0] == 'r' else x - w / 2)
    d.rounded_rectangle(P(x0, y - 11, x0 + w, y + 11), 5 * S, fill=bg, outline=INK, width=S)
    d.text(P(x0 + w / 2, y), s, font=f, fill=fg, anchor='mm')


def drop_shadow(mask_at, pos):
    sh = Image.new('L', img.size, 0)
    sh.paste(mask_at.point(lambda v: int(v * 0.45)), P(pos[0] + 7, pos[1] + 9))
    img.paste(Image.new('RGB', img.size, '#3a352a'), (0, 0), sh.filter(ImageFilter.GaussianBlur(9 * S)))


# ---------- photos ----------
def photo(name, scale, pos, rot=0, box=None):
    """Paste a module photo (white background keyed out). Returns orig-pixel -> canvas mapper."""
    global d
    im = Image.open(HERE / 'parts' / f'{name}.png').convert('RGB')
    key = im.copy()
    for c in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)):
        ImageDraw.floodfill(key, c, (255, 0, 255), thresh=44)
    r, g, b = key.split()
    # magenta key = R 255, G 0, B 255
    mask = Image.eval(g, lambda v: 255 if v > 0 else 0)
    notkey = Image.eval(r, lambda v: 0 if v == 255 else 255)
    mask = Image.composite(Image.new('L', im.size, 255), mask, notkey)
    mask = mask.filter(ImageFilter.MinFilter(3))
    if box:
        keep = Image.new('L', im.size, 0)
        keep.paste(255, box)
        mask = Image.composite(mask, keep, keep)
    bx0, by0, bx1, by1 = mask.getbbox()
    im, mask = im.crop((bx0, by0, bx1, by1)), mask.crop((bx0, by0, bx1, by1))
    w, h = im.size
    if rot:
        im, mask = im.rotate(rot, expand=True), mask.rotate(rot, expand=True)
    size = (int(im.width * scale * S), int(im.height * scale * S))
    im, mask = im.resize(size, Image.LANCZOS), mask.resize(size, Image.LANCZOS)
    drop_shadow(mask, pos)
    img.paste(im, P(*pos), mask)
    d = ImageDraw.Draw(img)

    def at(x, y):
        x, y = x - bx0, y - by0
        if rot == 180:
            x, y = w - 1 - x, h - 1 - y
        elif rot == 90:
            x, y = y, w - 1 - x
        return pos[0] + x * scale, pos[1] + y * scale
    return at


# ---------- wires ----------
def rounded(pts, r=13):
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        def toward(p, q):
            L = max(1e-6, ((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2) ** .5)
            k = min(r, L / 2) / L
            return p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k
        p1, p2 = toward(b, a), toward(b, c)
        for i in range(9):
            t = i / 8
            out.append(((1 - t) ** 2 * p1[0] + 2 * t * (1 - t) * b[0] + t * t * p2[0],
                        (1 - t) ** 2 * p1[1] + 2 * t * (1 - t) * b[1] + t * t * p2[1]))
    out.append(pts[-1])
    return [P(*p) for p in out]


def wire(pts, color, width=6, pads=(True, True)):
    path = rounded(pts)
    d.line(path, fill=PAPER, width=(width + 8) * S, joint='curve')
    d.line(path, fill='#151515', width=(width + 2) * S, joint='curve')
    d.line(path, fill=C[color], width=width * S, joint='curve')
    for on, (x, y) in zip(pads, (pts[0], pts[-1])):
        if on:
            d.ellipse(P(x - 7, y - 7, x + 7, y + 7), fill='#c9ccd0', outline='#55595e', width=S)
            d.ellipse(P(x - 3, y - 3, x + 3, y + 3), fill=C[color])


def dot(x, y, color):
    d.ellipse(P(x - 8, y - 8, x + 8, y + 8), fill=C[color], outline='#151515', width=S)


# ---------- drawn parts ----------
BANDS = {'10k': ('#7a4a1e', '#111111', '#ef7d22'), '100k': ('#7a4a1e', '#111111', '#f0c020')}


def resistor(x0, y0, x1, y1, val, label_dy=-26):
    """Axial resistor with colour bands between two points (horizontal)."""
    d.line(P(x0, y0, x1, y1), fill='#9aa0a6', width=4 * S)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    L, T = 100, 30
    d.rounded_rectangle(P(cx - L / 2, cy - T / 2, cx + L / 2, cy + T / 2), 12 * S, fill='#d9c08f',
                        outline='#6e5a35', width=2 * S)
    for i, col in enumerate(BANDS[val] + ('#c9a227',)):
        o = -34 + i * 17 + (10 if i == 3 else 0)
        d.rectangle(P(cx + o - 4, cy - T / 2 + 2, cx + o + 4, cy + T / 2 - 2), fill=col)
    text(cx, cy + label_dy, val, 18, anchor='mm')


def cap(x, y0, y1, val='100n'):
    d.line(P(x, y0, x, y1), fill='#9aa0a6', width=4 * S)
    cy = (y0 + y1) / 2
    d.ellipse(P(x - 21, cy - 21, x + 21, cy + 21), fill='#e0a13a', outline='#7d5412', width=2 * S)
    text(x, cy, '104', 12, '#5a3a08', 'mm')
    text(x - 28, cy, val, 17, anchor='rm')


def button(x, y, name, gpio, label_at=None):
    """12x12 tact switch. (x, y) = top-left leg, legs 110 apart horizontally, 80 vertically.
    Wired by DIAGONAL legs (top-right / bottom-left or top-left / bottom-right): a diagonal pair is
    always the switched pair, whichever way the 4-leg button is turned."""
    for lx in (x, x + 110):
        for ly in (y, y + 80):
            d.rectangle(P(lx - 9, ly - 5, lx + 9, ly + 5), fill='#c9ccd0', outline='#55595e', width=S)
    d.rounded_rectangle(P(x + 5, y - 15, x + 105, y + 95), 6 * S, fill='#26282b', outline='#0c0c0c', width=2 * S)
    d.rounded_rectangle(P(x + 13, y - 7, x + 97, y + 87), 4 * S, fill='#b9bcc1', outline='#7a7f86', width=S)
    d.ellipse(P(x + 25, y + 5, x + 85, y + 75), fill='#e3a21a', outline='#7d5412', width=2 * S)
    d.ellipse(P(x + 33, y + 11, x + 71, y + 49), fill='#f0bb45')
    if label_at is None:
        text(x + 55, y - 38, f'{name} · GPIO{gpio}', 22, anchor='mm')
    else:
        text(label_at[0], label_at[1], f'{name} · GPIO{gpio}', 22)


# =====================================================================================
#  PHOTOS
# =====================================================================================
ESP = photo('esp32s3', 1.8, (1500, 330))
ROWY = [83, 109.5, 136, 163, 189.5, 216, 243, 270, 296, 323, 350, 376.5, 403, 429.5, 456.5, 483, 509, 536, 563,
        589.5, 616, 643]
LEFT = ['3V3a', '3V3b', 'RST', '4', '5', '6', '7', '15', '16', '17', '18', '8', '3', '46', '9', '10', '11', '12',
        '13', '14', '5V', 'Gl']
RIGHT = ['Gr', 'TX', 'RX', '1', '2', '42', '41', '40', '39', '38', '37', '36', '35', '0', '45', '48', '47', '21',
         '20', '19', 'Gr2', 'Gr3']
LX, RX = ESP(13, 0)[0], ESP(257, 0)[0]
YL = {n: ESP(0, y)[1] for n, y in zip(LEFT, ROWY)}
YR = {n: ESP(0, y)[1] for n, y in zip(RIGHT, ROWY)}

DISP = photo('display', 1.3, (230, 300), 180)
HDR = ['T_IRQ', 'T_OUT', 'T_DIN', 'T_CS', 'T_CLK', 'MISO', 'LED', 'SCK', 'MOSI', 'DC', 'RESET', 'CS', 'GND', 'VCC']
DP = {n: DISP(130, 166 + 18.93 * (i + .5)) for i, n in enumerate(HDR)}
SDP = {n: DISP(670, y) for n, y in (('SCK', 271), ('MISO', 289), ('MOSI', 307.5), ('CS', 326))}

MAX = photo('max98357a', 1.25, (640, 803), 90)
MP = {n: MAX(x, 243) for n, x in (('LRC', 21), ('BCLK', 59), ('DIN', 97), ('GAIN', 134), ('SD', 172), ('GND', 210),
                                  ('Vin', 247))}
SPK_M, SPK_P = MAX(108, 52), MAX(159, 52)

XL = photo('xl6009', 0.6, (1640, 1760), box=(170, 221, 813, 534))
XO_N, XO_P, XI_N, XI_P = XL(197, 247), XL(197, 495), XL(785, 247), XL(785, 507)
TP = photo('tp4056', 0.605, (2420, 1753.6), 180)
T_OP, T_BP, T_BN, T_ON = TP(620, 257), TP(620, 312), TP(620, 450), TP(617, 515)

# =====================================================================================
#  RAILS
# =====================================================================================
GND_Y, V33_Y = 120, 160           # top rails
GND_XL, V33_XL = 60, 100          # left trunks
GND_XR, V33_XR = 3340, 3300       # right trunks
CELL0, CELL_DY = 1210, 170
last = CELL0 + 5 * CELL_DY
SEL_Y = YR['47']

wire([(GND_XL, last + 115), (GND_XL, GND_Y), (GND_XR, GND_Y), (GND_XR, SEL_Y + 115)], 'black', 7, (False, False))
wire([(V33_XL, last), (V33_XL, V33_Y), (V33_XR, V33_Y), (V33_XR, SEL_Y)], 'red', 7, (False, False))
text(GND_XL + 80, GND_Y - 26, 'GND', 26)
text(V33_XL + 130, V33_Y + 24, '3V3', 26, C['red'])

# ESP -> rails
wire([(LX, YL['3V3a']), (LX - 45, YL['3V3a']), (LX - 45, V33_Y)], 'red', pads=(True, False))
dot(LX - 45, V33_Y, 'red')
wire([(RX, YR['Gr']), (RX + 40, YR['Gr']), (RX + 40, GND_Y)], 'black', pads=(True, False))
dot(RX + 40, GND_Y, 'black')

# =====================================================================================
#  DISPLAY + SD
# =====================================================================================
sig = [('CS', '4', 'orange', 1285), ('RESET', '5', 'brown', 1255), ('DC', '6', 'yellow', 1225),
       ('MOSI', '7', 'blue', 1195), ('SCK', '15', 'green', 1165), ('LED', '16', 'white', 1135)]
x, y = DP['VCC']
wire([(x, y), (1315, y), (1315, YL['3V3b']), (LX, YL['3V3b'])], 'red')
for n, pin, col, ch in sig:
    x, y = DP[n]
    wire([(x, y), (ch, y), (ch, YL[pin]), (LX, YL[pin])], col)
x, y = DP['GND']
wire([(x, y), (1100, y), (1100, GND_Y)], 'black', pads=(True, False))
dot(1100, GND_Y, 'black')
for n in ('VCC', 'GND', 'CS', 'RESET', 'DC', 'MOSI', 'SCK', 'LED'):
    x, y = DP[n]
    tag(x - 14, y, n, 'rm', 13)

sd = [('CS', '42', 'orange', 0), ('MISO', '41', 'green', 1), ('MOSI', '40', 'blue', 2), ('SCK', '39', 'yellow', 3)]
for n, pin, col, k in sd:
    x, y = SDP[n]
    vx, hy, rx = 200 - 14 * k, 245 - 14 * k, RX + 70 + 14 * k
    wire([(x, y), (vx, y), (vx, hy), (rx, hy), (rx, YR[pin]), (RX, YR[pin])], col, 5)
for n, _, _, _ in sd:
    x, y = SDP[n]
    tag(x + 16, y, 'SD_' + n, 'lm', 13)
text(620, 276, t('дисплей 2.4" TJCTM24024, вид ззаду · контролер ST7789 · слот SD', '2.4" display TJCTM24024, rear view · ST7789 controller · SD slot'), 21, anchor='mm')

# =====================================================================================
#  MAX98357A + speaker
# =====================================================================================
x, y = MP['Vin']
wire([(x, y), (1090, y), (1090, 770), (V33_XL, 770)], 'red', pads=(True, False))
dot(V33_XL, 770, 'red')
x, y = MP['GND']
wire([(x, y), (1110, y), (1110, 752), (GND_XL, 752)], 'black', pads=(True, False))
dot(GND_XL, 752, 'black')
x, y = MP['DIN']
wire([(x, y), (1400, y), (1400, YL['8']), (LX, YL['8'])], 'cyan')
x, y = MP['BCLK']
wire([(x, y), (1140, y), (1140, YL['17']), (LX, YL['17'])], 'purple')
x, y = MP['LRC']
wire([(x, y), (1170, y), (1170, YL['18']), (LX, YL['18'])], 'pink')
for n in ('Vin', 'GND', 'DIN', 'BCLK', 'LRC'):
    x, y = MP[n]
    tag(x - 14, y, n, 'rm', 13)
d.ellipse(P(250, 850, 490, 1090), fill='#1b1b1b', outline='#4a4a4a', width=6 * S)
d.ellipse(P(275, 875, 465, 1065), fill='#2a2a2a', outline='#3a3a3a', width=3 * S)
d.ellipse(P(330, 930, 410, 1010), fill='#141414', outline='#444444', width=3 * S)
text(370, 1112, t('динамік 3 Вт', 'speaker 3 W'), 21, anchor='mm')
wire([(480, 940), (560, 940), (560, SPK_P[1]), SPK_P], 'red', 5, (False, True))
wire([(486, 1000), (560, 1000), (560, SPK_M[1]), SPK_M], 'black', 5, (False, True))
text(812, 1142, 'MAX98357A (I2S)', 21, anchor='mm')

# =====================================================================================
#  BUTTONS — 10k from 3V3 straight onto the SIGNAL wire (the GPIO node), the button hangs
#  off that same wire to GND. Nothing depends on the button's internal leg pairs.
# =====================================================================================
BTN_DROP = 35                      # signal wire y -> top legs of the button
cells = [('OPTIONS', '9', 'white'), ('MENU', '10', 'grey'), ('X', '11', 'yellow'), ('Y', '12', 'orange'),
         ('A', '13', 'green'), ('B', '14', 'blue')]
BX = 430
for i, (name, pin, col) in enumerate(cells):
    yc = CELL0 + i * CELL_DY           # signal wire: pull-up node -> GPIO
    by = yc + BTN_DROP
    ch = 1150 + 35 * i
    wire([(V33_XL, yc), (150, yc)], 'red', 5, (False, False))
    dot(V33_XL, yc, 'red')
    resistor(150, yc, 310, yc, '10k')
    wire([(310, yc), (ch, yc), (ch, YL[pin]), (LX, YL[pin])], col)
    dot(310, yc, col)                  # pull-up joins the signal wire here
    wire([(BX + 110, yc), (BX + 110, by)], col, 5, (False, True))
    dot(BX + 110, yc, col)             # button taps the same signal wire
    wire([(BX, by + 80), (GND_XL, by + 80)], 'black', 5, (True, False))
    dot(GND_XL, by + 80, 'black')
    button(BX, by, name, pin, (BX + 150, by + 40))

# SELECT on the right: GPIO47 -> signal wire -> 10k -> 3V3, button from the wire to GND
SBX = 2560
sby = SEL_Y + BTN_DROP
wire([(RX, SEL_Y), (2830, SEL_Y)], 'purple')
dot(2830, SEL_Y, 'purple')
resistor(2830, SEL_Y, 2990, SEL_Y, '10k')
wire([(2990, SEL_Y), (V33_XR, SEL_Y)], 'red', 5, (False, False))
dot(V33_XR, SEL_Y, 'red')
wire([(SBX, SEL_Y), (SBX, sby)], 'purple', 5, (False, True))
dot(SBX, SEL_Y, 'purple')
wire([(SBX + 110, sby + 80), (GND_XR, sby + 80)], 'black', 5, (True, False))
dot(GND_XR, sby + 80, 'black')
button(SBX, sby, 'SELECT', '47', (SBX + 150, sby + 40))

# legend: how a button is wired
lx_, ly_ = 150, CELL0 + 5 * CELL_DY + 160
text(lx_, ly_, t('кнопка: 10 кОм від 3V3 на сигнальний дріт (вузол GPIO), кнопка — з цього дроту на GND;', 'button: 10k from 3V3 onto the signal wire (the GPIO node), button from that wire to GND;'), 17, '#444444', bold=False)
text(lx_, ly_ + 26, t('ніжки кнопки — по діагоналі, тоді неважливо, як її повернуто', 'use diagonal legs of the button, then its orientation does not matter'), 17, '#444444', bold=False)

# =====================================================================================
#  JOYSTICK KY-023 (drawn)
# =====================================================================================
jx, jy = 2560, 350
m = Image.new('L', P(330, 340), 255)
drop_shadow(m, (jx, jy))
d = ImageDraw.Draw(img)
d.rounded_rectangle(P(jx, jy, jx + 330, jy + 340), 10 * S, fill='#1b1d20', outline='#0c0c0c', width=2 * S)
for hx, hy in ((jx + 305, jy + 25), (jx + 305, jy + 315), (jx + 110, jy + 25), (jx + 110, jy + 315)):
    d.ellipse(P(hx - 13, hy - 13, hx + 13, hy + 13), fill=PAPER, outline='#b9bcc1', width=3 * S)
d.rounded_rectangle(P(jx + 120, jy + 70, jx + 300, jy + 270), 8 * S, fill='#c9ccd0', outline='#7a7f86', width=2 * S)
d.ellipse(P(jx + 130, jy + 90, jx + 290, jy + 250), fill='#101010', outline='#333333', width=3 * S)
d.ellipse(P(jx + 160, jy + 120, jx + 260, jy + 220), fill='#1f1f1f', outline='#3d3d3d', width=3 * S)
text(jx + 210, jy + 300, 'KY-023', 16, '#e8e8e2', 'mm')
JP = {}
for i, n in enumerate(('GND', '+5V', 'VRx', 'VRy', 'SW')):
    y = jy + 70 + i * 45
    JP[n] = (jx, y)
    d.rectangle(P(jx - 12, y - 6, jx + 14, y + 6), fill='#c9ccd0', outline='#55595e', width=S)
    text(jx + 24, y, n, 15, '#e8e8e2')
x, y = JP['GND']
wire([(x, y), (2500, y), (2500, GND_Y)], 'black', pads=(True, False))
dot(2500, GND_Y, 'black')
x, y = JP['+5V']
wire([(x, y), (2470, y), (2470, V33_Y)], 'red', pads=(True, False))
dot(2470, V33_Y, 'red')
for n, pin, col, ch in (('VRx', '1', 'blue', 2200), ('VRy', '2', 'green', 2240), ('SW', '38', 'yellow', 2280)):
    x, y = JP[n]
    wire([(x, y), (ch, y), (ch, YR[pin]), (RX, YR[pin])], col)
text(jx + 165, jy - 50, t('джойстик KY-023', 'joystick KY-023'), 21, anchor='mm')
text(jx + 165, jy - 20, t('живлення лише 3.3 В · SW = START', '3.3 V supply only · SW = START'), 19, C['red'], 'mm')

# =====================================================================================
#  POWER: 18650 -> TP4056 -> switch -> XL6009 (5 V) -> ESP
# =====================================================================================
wire([(LX, YL['Gl']), (LX - 40, YL['Gl']), (LX - 40, XO_N[1]), XO_N], 'black')
wire([(LX, YL['5V']), (LX - 75, YL['5V']), (LX - 75, XO_P[1]), XO_P], 'red')
wire([T_ON, XI_N], 'black')
sy = XI_P[1]
wire([XI_P, (2160, sy)], 'red')
wire([(2210, sy), T_OP], 'red')
d.rounded_rectangle(P(2130, sy - 80, 2290, sy - 28), 4 * S, fill='#c9ccd0', outline='#55595e', width=2 * S)
d.rectangle(P(2165, sy - 70, 2255, sy - 40), fill='#3a3d42')
d.rectangle(P(2170, sy - 104, 2205, sy - 62), fill='#151515')
for px_ in (2160, 2210, 2260):
    d.rectangle(P(px_ - 5, sy - 28, px_ + 5, sy - 8), fill='#c9ccd0', outline='#55595e', width=S)
text(2210, sy - 124, t('вимикач SS12D00', 'switch SS12D00'), 21, anchor='mm')
# battery
bx0, bx1, by = 2445, 2915, 2160
d.rounded_rectangle(P(bx0, by - 55, bx1, by + 55), 16 * S, fill='#2f6fb5', outline='#1b3f6b', width=3 * S)
d.rectangle(P(bx0 + 40, by - 53, bx0 + 60, by + 53), fill='#1b3f6b')
d.rectangle(P(bx1, by - 22, bx1 + 14, by + 22), fill='#c9ccd0', outline='#55595e', width=S)
text((bx0 + bx1) / 2 + 20, by - 10, t('18650  Li-ion 3.7 В', '18650  Li-ion 3.7 V'), 20, '#ffffff', 'mm')
text((bx0 + bx1) / 2 + 20, by + 22, t('~8 год гри', '~8 h of play'), 15, '#d6e6f7', 'mm', False)
text(bx0 + 20, by, '−', 30, '#ffffff', 'mm')
text(bx1 - 24, by, '+', 30, '#ffffff', 'mm')
wire([T_BN, (2370, T_BN[1]), (2370, by), (bx0, by)], 'black')
wire([T_BP, (2400, T_BP[1]), (2400, 2060), (2975, 2060), (2975, by), (bx1 + 14, by)], 'red')
for n, p in (('OUT−', T_ON), ('B−', T_BN), ('B+', T_BP), ('OUT+', T_OP)):
    tag(p[0] + 16, p[1], n, 'lm', 13)
for n, p, a in (('OUT−', XO_N, 'l'), (t('OUT+ 5 В', 'OUT+ 5 V'), XO_P, 'l'), ('IN−', XI_N, 'r'), ('IN+', XI_P, 'r')):
    tag(p[0] + (16 if a == 'l' else -16), p[1], n, a + 'm', 13)
text(XL(490, 211)[0], 1738, t('XL6009 DC-DC boost → 5.0 В', 'XL6009 DC-DC boost → 5.0 V'), 21, anchor='mm')
text(TP(380, 231)[0], 1990, t('TP4056 + захист DW01 (заряд USB-C)', 'TP4056 + DW01 (USB-C charger)'), 21, anchor='mm')
# battery sense divider 100k / 100k -> GPIO3
dy_ = 2290
wire([(2975, 2120), (3040, 2120), (3040, dy_), (1505, dy_), (1505, XO_N[1])], 'grey', 5, (False, False))
dot(2975, 2120, 'red')
dot(1505, XO_N[1], 'black')
resistor(2080, dy_, 2280, dy_, '100k', 30)
resistor(1700, dy_, 1900, dy_, '100k', 30)
wire([(1990, dy_), (1990, dy_ - 50), (1380, dy_ - 50), (1380, YL['3']), (LX, YL['3'])], 'teal', 5, (False, True))
dot(1990, dy_, 'teal')
text(1990, dy_ + 34, 'BAT/2 → GPIO3', 21, anchor='mm')
text(2960, dy_ + 30, 'BAT+', 19, anchor='rm')
text(1520, dy_ + 30, 'GND', 19)

def bypass(p0, p1, kind, tag_at):
    """Decoupling cap between a + point (p0) and a GND point (p1): 'e' = 470 uF electrolytic, 'c' = 100 nF."""
    cx, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    wire([p0, (cx, cy)], 'red', 5, (False, False))
    wire([(cx, cy), p1], 'black', 5, (False, False))
    dot(p0[0], p0[1], 'red')
    dot(p1[0], p1[1], 'black')
    if kind == 'e':
        r = 23
        d.ellipse(P(cx - r, cy - r, cx + r, cy + r), fill='#1d2a44', outline='#0c0c0c', width=2 * S)
        d.ellipse(P(cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6), fill='#c9ccd0', outline='#7a7f86', width=S)
        d.chord(P(cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6), 35, 145, fill='#1d2a44')
        text(cx, cy - 4, '+', 16, '#1d2a44', 'mm')
        label = t('470 мкФ', '470 µF')
    else:
        r = 19
        d.ellipse(P(cx - r, cy - r, cx + r, cy + r), fill='#e0a13a', outline='#7d5412', width=2 * S)
        text(cx, cy, '104', 12, '#5a3a08', 'mm')
        label = t('100 нФ', '100 nF')
    tag(tag_at[0], tag_at[1], label, 'mm', 13)


# decoupling on the board's power inputs: 470 uF + 100 nF on 5V-G and on 3V3-G
bypass((1550, XO_P[1]), (1550, XO_N[1]), 'e', (1550, XO_N[1] + 40))
bypass((1605, XO_P[1]), (1605, XO_N[1]), 'c', (1605, XO_P[1] - 40))
bypass((LX - 45, 268), (RX + 40, 268), 'e', (1650, 268))
bypass((LX - 45, 306), (RX + 40, 306), 'c', (1850, 306))


# =====================================================================================
#  NOTES + TITLE
# =====================================================================================
for p in ('37', '36', '35'):
    y = YR[p]
    d.line(P(RX - 10, y - 10, RX + 10, y + 10), fill='#e0221a', width=4 * S)
    d.line(P(RX - 10, y + 10, RX + 10, y - 10), fill='#e0221a', width=4 * S)
text(RX + 30, YR['37'], t('GPIO 35–37 = PSRAM,', 'GPIO 35–37 = PSRAM,'), 20, '#c0221a')
text(RX + 30, YR['36'], t('не підключати', 'do not connect'), 20, '#c0221a')

tx, ty = 2350, 800
d.rectangle(P(tx + 8, ty + 8, tx + 938, ty + 318), fill='#d8d3c4')
d.rectangle(P(tx, ty, tx + 930, ty + 310), fill='#fffdf6', outline=INK, width=3 * S)
d.text(P(tx + 30, ty + 24), 'RETRO CONSOLE', font=HEAD(66), fill=INK)
d.text(P(tx + 30, ty + 104), t('ESP32-S3 · повна схема з’єднань', 'ESP32-S3 · full wiring diagram'), font=HEAD(32), fill='#444444')
text(tx + 30, ty + 172, t('плата YD-ESP32-S3 N16R8 · прошивка Retro-Go', 'board YD-ESP32-S3 N16R8 · Retro-Go firmware'), 17, '#444444', bold=False)
text(tx + 30, ty + 204, t('резистори: 7 × 10 кОм (підтяжка кнопок), 2 × 100 кОм (дільник)', 'resistors: 7 × 10k (button pull-ups), 2 × 100k (battery divider)'), 17, '#444444', bold=False)
text(tx + 30, ty + 236, t('конденсатори: 470 мкФ + 100 нФ на входах 5V і 3V3 плати', 'capacitors: 470 µF + 100 nF on the board 5V and 3V3 inputs'), 17, '#444444', bold=False)
text(tx + 30, ty + 276, 'github.com/AlexGerUA/retro-console-esp32s3', 17)
d.text(P(W - 50, H - 36), 'Alex_Ger_UA', font=HEAD(26), fill='#77736a', anchor='rm')

img = img.resize((W, H), Image.LANCZOS)
out = HERE / ('pinout_en.png' if LANG == 'en' else 'pinout.png')
img.save(out, optimize=True)
print('saved', out, img.size)
