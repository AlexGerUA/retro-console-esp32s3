"""docs/pinout.png — wiring drawn like a maker's bench: cutting mat, PCB, dupont wires.

YD-ESP32-S3 has the same header order as ESP32-S3-DevKitC-1. Pins come from
firmware/retro-go-overlay/components/retro-go/targets/retro-console/config.h.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, S = 2400, 1820, 2
random.seed(7)

MAT, GRID, GRID2 = '#245446', '#2f6a59', '#3b7e6b'
PCB, PCB_EDGE, PAD, SILK = '#15181c', '#2a2f36', '#d9a637', '#e8e8e2'
WIRE = {'red': '#d7332b', 'black': '#202020', 'yellow': '#f2c12e', 'orange': '#ef7d22',
        'green': '#3aa655', 'blue': '#2e7fd8', 'purple': '#8a4fc7', 'grey': '#9aa0a6',
        'white': '#efefe9', 'brown': '#8b5a2b', 'pink': '#e85c9a', 'cyan': '#2bb5c9'}


def font(name, size):
    for n in (name, 'consola.ttf', 'DejaVuSansMono.ttf'):
        try:
            return ImageFont.truetype(n, size * S)
        except OSError:
            pass
    return ImageFont.load_default()


MONO = lambda s: font('consola.ttf', s)          # noqa: E731
MONOB = lambda s: font('consolab.ttf', s)        # noqa: E731
HEAD = lambda s: font('bahnschrift.ttf', s)      # noqa: E731

img = Image.new('RGB', (W * S, H * S), MAT)
d = ImageDraw.Draw(img)


def P(*v):
    return tuple(x * S for x in v)


# ---------- cutting mat ----------
for x in range(0, W, 20):
    d.line(P(x, 0, x, H), fill=GRID2 if x % 100 == 0 else GRID, width=(2 if x % 100 == 0 else 1) * S)
for y in range(0, H, 20):
    d.line(P(0, y, W, y), fill=GRID2 if y % 100 == 0 else GRID, width=(2 if y % 100 == 0 else 1) * S)
for x in range(0, W, 100):
    d.text(P(x + 4, 4), str(x // 10), font=MONO(12), fill=GRID2)
noise = Image.effect_noise((W * S // 4, H * S // 4), 18).resize((W * S, H * S)).convert('L')
img = Image.composite(img, Image.new('RGB', img.size, '#1f4a3d'), noise.point(lambda v: 200 + v // 5))
d = ImageDraw.Draw(img)


def shadow_box(box, radius, fill, outline=None, width=0):
    x0, y0, x1, y1 = box
    sh = Image.new('L', img.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle(P(x0 + 8, y0 + 10, x1 + 8, y1 + 10), radius * S, fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(12 * S))
    img.paste(Image.new('RGB', img.size, '#0e211b'), (0, 0), sh)
    d.rounded_rectangle(P(*box), radius * S, fill=fill, outline=outline, width=width * S)


def wire(pts, color, width=7):
    """Smooth wire through points (Catmull-Rom), dark outline like real insulation."""
    path = []
    pts = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for t in [k / 24 for k in range(25)]:
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            path.append((x * S, y * S))
    d.line(path, fill='#0b0b0b', width=(width + 3) * S, joint='curve')
    d.line(path, fill=WIRE[color], width=width * S, joint='curve')
    hi = tuple(min(255, int(c, 16) + 70) for c in (WIRE[color][1:3], WIRE[color][3:5], WIRE[color][5:7]))
    d.line([(x - S, y - 2 * S) for x, y in path], fill='#%02x%02x%02x' % hi, width=max(1, width // 3) * S)


def tag(x, y, text, color, align='l'):
    fnt = MONOB(17)
    w = d.textlength(text, font=fnt) / S + 14
    x0, x1 = (x, x + w) if align == 'l' else (x - w, x)
    d.rectangle(P(x0, y - 13, x1, y + 13), fill=WIRE[color])
    d.text(P((x0 + x1) / 2, y), text, font=fnt, fill='#111111' if color in ('yellow', 'white', 'cyan') else '#ffffff',
           anchor='mm')
    return x0, x1


def label(x, y, text, size=18, color=SILK, anchor='lm', bold=False):
    d.text(P(x, y), text, font=(MONOB if bold else MONO)(size), fill=color, anchor=anchor)


# ---------- board ----------
CX, TOP, PITCH = 1200, 360, 45
LX, RX = CX - 88, CX + 88
ROWS = [TOP + i * PITCH for i in range(22)]
LEFT = ['3V3', '3V3', 'RST', '4', '5', '6', '7', '15', '16', '17', '18', '8', '3', '46', '9', '10', '11', '12',
        '13', '14', '5V', 'G']
RIGHT = ['G', 'TX', 'RX', '1', '2', '42', '41', '40', '39', '38', '37', '36', '35', '0', '45', '48', '47', '21',
         '20', '19', 'G', 'G']
YL = dict((lab, y) for lab, y in zip(LEFT, ROWS) if lab.isdigit())
YR = dict((lab, y) for lab, y in zip(RIGHT, ROWS) if lab.isdigit())

bx0, bx1, by0, by1 = CX - 130, CX + 130, TOP - 90, ROWS[-1] + 85
shadow_box((bx0, by0, bx1, by1), 10, PCB, PCB_EDGE, 3)
d.rectangle(P(CX - 50, by0 - 60, CX + 50, by0 + 230), fill='#262a30')
d.rectangle(P(CX - 42, by0 - 6, CX + 42, by0 + 216), fill='#b9bcc1')
for i in range(3):
    xx = CX - 36 + i * 27
    d.line(P(xx, by0 - 48, xx, by0 - 18), fill='#d9a637', width=4 * S)
    d.line(P(xx, by0 - 48, xx + 15, by0 - 48), fill='#d9a637', width=4 * S)
label(CX, by0 + 95, 'ESP32', 15, '#33373d', 'mm', True)
label(CX, by0 + 120, '-S3', 15, '#33373d', 'mm', True)
label(CX, by0 + 147, 'N16R8', 13, '#33373d', 'mm')
label(CX, ROWS[18], 'YD-ESP32', 13, SILK, 'mm', True)
label(CX, ROWS[19], 'S3', 13, SILK, 'mm', True)
d.ellipse(P(CX - 9, ROWS[16] - 9, CX + 9, ROWS[16] + 9), fill='#f4f4f4')
label(CX, ROWS[16] + 22, 'RGB 48', 13, '#9aa0a6', 'mm')
for ux, lab in ((CX - 58, 'UART'), (CX + 58, 'USB')):
    d.rectangle(P(ux - 30, by1 - 26, ux + 30, by1 + 12), fill='#b9bcc1')
    label(ux, by1 - 40, lab, 13, SILK, 'mm', True)
for labs, x, side in ((LEFT, LX, 1), (RIGHT, RX, -1)):
    for lab, y in zip(labs, ROWS):
        d.rectangle(P(x - 11, y - 11, x + 11, y + 11), fill=PAD)
        d.ellipse(P(x - 5, y - 5, x + 5, y + 5), fill='#3a2a08')
        label(x + side * 20, y, lab, 15, SILK, 'lm' if side == 1 else 'rm', True)
for p in ('35', '36', '37'):
    y = YR[p]
    d.line(P(RX - 9, y - 9, RX + 9, y + 9), fill='#ff4d4d', width=3 * S)
    d.line(P(RX - 9, y + 9, RX + 9, y - 9), fill='#ff4d4d', width=3 * S)
label(RX + 28, YR['36'], 'PSRAM — не чіпати', 16, '#ff8a80')


def to_left(pin, x_from, y_from, color, bend=None):
    y = YL[pin]
    pts = [(x_from, y_from), (x_from + 60, y_from), (LX - 70, y), (LX, y)] if bend is None else bend + [(LX, y)]
    wire(pts, color)


def to_right(pin, x_from, y_from, color, bend=None):
    y = YR[pin]
    pts = [(x_from, y_from), (x_from - 60, y_from), (RX + 70, y), (RX, y)] if bend is None else bend + [(RX, y)]
    wire(pts, color)


# ---------- display (left top) ----------
shadow_box((130, 300, 640, 700), 8, '#c8332e', '#8f1f1b', 2)
d.rectangle(P(170, 340, 520, 620), fill='#101418')
d.rectangle(P(182, 352, 508, 608), fill='#27313a')
label(345, 480, '2.4" 320×240', 22, '#8fa3b3', 'mm', True)
label(345, 512, 'ST7789 (на платі «ILI9341»)', 15, '#8fa3b3', 'mm')
label(150, 670, 'TJCTM24024', 15, '#ffd9d6', 'lm', True)
disp = [('CS', '4', 'orange'), ('RST', '5', 'brown'), ('DC', '6', 'yellow'), ('MOSI', '7', 'blue'),
        ('SCK', '15', 'green'), ('LED', '16', 'white')]
for i, (sig, pin, col) in enumerate(disp):
    y = 360 + i * 42
    d.rectangle(P(600, y - 9, 618, y + 9), fill=PAD)
    label(592, y, sig, 15, '#ffffff', 'rm', True)
    to_left(pin, 618, y, col)

# ---------- audio (left middle) ----------
shadow_box((300, 760, 640, 905), 8, '#5b2a86', '#3a1958', 2)
label(320, 790, 'MAX98357A', 20, '#f1e6ff', 'lm', True)
label(320, 818, 'I2S · 3 Вт', 15, '#cdb6ea', 'lm')
d.ellipse(P(150, 765, 270, 885), fill='#1b1b1b', outline='#555555', width=4 * S)
d.ellipse(P(185, 800, 235, 850), fill='#333333')
wire([(270, 840), (300, 860)], 'red', 5)
for i, (sig, pin, col) in enumerate((('BCLK', '17', 'purple'), ('LRC', '18', 'pink'), ('DIN', '8', 'cyan'))):
    y = 790 + i * 40
    d.rectangle(P(605, y - 9, 623, y + 9), fill=PAD)
    label(597, y, sig, 15, '#ffffff', 'rm', True)
    to_left(pin, 623, y, col)

# ---------- power (left bottom) ----------
shadow_box((130, 960, 640, 1360), 8, '#1d2125', '#3a3f46', 2)
label(150, 990, 'ЖИВЛЕННЯ', 20, SILK, 'lm', True)
d.rounded_rectangle(P(160, 1020, 220, 1300), 26 * S, fill='#4f7fbf', outline='#2b4f80', width=3 * S)
d.rectangle(P(175, 1012, 205, 1022), fill='#c0c0c0')
label(190, 1160, '18650', 16, '#ffffff', 'mm', True)
blocks = [('TP4056+DW01', 1040, '#1f5fa8'), ('SS12D00', 1120, '#555b63'), ('BOOST → 5V', 1200, '#a83232')]
for text, y, col in blocks:
    d.rectangle(P(260, y, 470, y + 52), fill=col)
    label(365, y + 26, text, 16, '#ffffff', 'mm', True)
for y0, y1 in ((1092, 1120), (1172, 1200)):
    d.line(P(365, y0, 365, y1), fill='#ffffff', width=3 * S)
d.line(P(220, 1066, 260, 1066), fill='#ffffff', width=3 * S)
label(260, 1290, 'заряд: USB-C на TP4056', 14, '#9aa0a6')
# divider 100k/100k for battery sense
rx = 545
label(rx, 1010, 'BAT+', 14, SILK, 'mm', True)
d.line(P(rx, 1022, rx, 1040), fill=SILK, width=3 * S)
for yy, txt in ((1040, '100k'), (1130, '100k')):
    d.rectangle(P(rx - 11, yy, rx + 11, yy + 56), outline=SILK, width=3 * S)
    label(rx + 18, yy + 28, txt, 14, SILK, 'lm', True)
d.line(P(rx, 1096, rx, 1130), fill=SILK, width=3 * S)
d.line(P(rx, 1186, rx, 1206), fill=SILK, width=3 * S)
for k in range(3):
    d.line(P(rx - 14 + 5 * k, 1206 + 6 * k, rx + 14 - 5 * k, 1206 + 6 * k), fill=SILK, width=3 * S)
d.ellipse(P(rx - 6, 1107, rx + 6, 1119), fill=SILK)
wire([(rx, 1113), (600, 1113), (760, 1000), (900, YL['3']), (LX - 60, YL['3']), (LX, YL['3'])], 'grey', 6)
d.rectangle(P(605, 1236, 623, 1254), fill=PAD)
label(597, 1245, '5V', 15, '#ffffff', 'rm', True)
d.rectangle(P(605, 1291, 623, 1309), fill=PAD)
label(597, 1300, 'GND', 15, '#ffffff', 'rm', True)
d.line(P(470, 1226, 520, 1226, 520, 1245, 605, 1245), fill='#ffffff', width=3 * S)
to_left('5V' if '5V' in YL else '3', 623, 1245, 'red', [(623, 1245), (700, 1245), (LX - 70, ROWS[20])]) \
    if False else wire([(623, 1245), (700, 1245), (LX - 70, ROWS[20]), (LX, ROWS[20])], 'red')
wire([(623, 1300), (700, 1300), (LX - 70, ROWS[21]), (LX, ROWS[21])], 'black')

# ---------- SD (right middle) ----------
shadow_box((1560, 540, 1880, 760), 8, '#c8332e', '#8f1f1b', 2)
d.rectangle(P(1600, 575, 1760, 725), fill='#b9bcc1', outline='#7a7f86', width=3 * S)
label(1680, 650, 'SD', 30, '#5d6168', 'mm', True)
label(1580, 742, 'на звороті дисплея', 13, '#ffd9d6', 'lm')
for i, (sig, pin, col) in enumerate((('CS', '42', 'orange'), ('MISO', '41', 'green'), ('MOSI', '40', 'blue'),
                                     ('SCK', '39', 'yellow'))):
    y = 590 + i * 40
    d.rectangle(P(1577, y - 9, 1595, y + 9), fill=PAD)
    label(1773, y, sig, 15, '#ffffff', 'lm', True)
    to_right(pin, 1577, y, col)

# ---------- joystick (right top) ----------
shadow_box((1900, 300, 2250, 640), 8, '#1d1f22', '#3a3f46', 2)
d.rectangle(P(1950, 350, 2110, 510), fill='#e9e9e3')
d.ellipse(P(1975, 375, 2085, 485), fill='#1a1a1a')
d.ellipse(P(2000, 400, 2060, 460), fill='#2c2c2c')
label(2130, 360, 'KY-023', 18, SILK, 'lm', True)
label(2130, 388, 'лише 3.3 В!', 15, '#ffcf6a', 'lm', True)
for i, (sig, pin, col) in enumerate((('VRx', '1', 'blue'), ('VRy', '2', 'green'), ('SW', '38', 'yellow'))):
    y = 545 + i * 34
    d.rectangle(P(1917, y - 9, 1935, y + 9), fill=PAD)
    label(1945, y, sig, 15, '#ffffff', 'lm', True)
wire([(1917, 545), (1860, 545), (1560, 470), (1400, YR['1']), (RX, YR['1'])], 'blue')
wire([(1917, 579), (1840, 579), (1540, 515), (1400, YR['2']), (RX, YR['2'])], 'green')
wire([(1917, 613), (1890, 640), (1900, 790), (1600, 800), (1400, YR['38']), (RX, YR['38'])], 'yellow')
label(2000, 613, '= START', 14, '#ffcf6a', 'lm')

# ---------- buttons (bottom) ----------
shadow_box((780, 1450, 1980, 1760), 8, '#1a1c1f', '#3a3f46', 2)
label(800, 1478, 'КНОПКИ', 20, SILK, 'lm', True)


def button(x, y, name, cap, pin):
    d.rectangle(P(x - 26, y - 26, x + 26, y + 26), fill='#c9c9c3')
    d.ellipse(P(x - 19, y - 19, x + 19, y + 19), fill=cap, outline='#111', width=2 * S)
    label(x, y + 44, name, 15, SILK, 'mm', True)
    label(x, y + 64, f'GPIO{pin}', 13, '#9aa0a6', 'mm')


under = [('SELECT', '47', 940), ('MENU', '10', 1040), ('OPTIONS', '9', 1140)]
for name, pin, x in under:
    button(x, 1560, name, '#e3a21a', pin)
dia = [('X', '11', 1600, 1530), ('Y', '12', 1530, 1590), ('A', '13', 1670, 1590), ('B', '14', 1600, 1650)]
for name, pin, x, y in dia:
    button(x, y, name, '#e3a21a' if name in 'XA' else '#2b2b2b', pin)
# pull-up schematic, once
sx = 1820
label(sx - 10, 1500, 'на кожну:', 14, '#9aa0a6', 'lm')
label(sx + 40, 1528, '3V3', 14, SILK, 'mm', True)
d.line(P(sx + 40, 1540, sx + 40, 1552), fill=SILK, width=3 * S)
d.rectangle(P(sx + 29, 1552, sx + 51, 1600), outline=SILK, width=3 * S)
label(sx + 58, 1576, '10k', 14, SILK, 'lm', True)
d.line(P(sx + 40, 1600, sx + 40, 1640), fill=SILK, width=3 * S)
d.ellipse(P(sx + 34, 1614, sx + 46, 1626), fill=SILK)
d.line(P(sx + 40, 1620, sx - 10, 1620), fill=SILK, width=3 * S)
label(sx - 14, 1620, 'GPIO', 13, SILK, 'rm', True)
d.line(P(sx + 24, 1640, sx + 56, 1640), fill=SILK, width=3 * S)
d.line(P(sx + 24, 1650, sx + 56, 1650), fill=SILK, width=3 * S)
label(sx + 62, 1645, '100n', 14, SILK, 'lm', True)
d.line(P(sx + 40, 1650, sx + 40, 1668), fill=SILK, width=3 * S)
for k in range(3):
    d.line(P(sx + 28 + 4 * k, 1668 + 6 * k, sx + 52 - 4 * k, 1668 + 6 * k), fill=SILK, width=3 * S)
label(sx - 10, 1712, 'кнопка → GND', 14, '#9aa0a6', 'lm')

# button wires: left pins go down the left channel, SELECT down the right one
cols = {'9': 'white', '10': 'grey', '11': 'yellow', '12': 'orange', '13': 'green', '14': 'blue', '47': 'purple'}
targets = {'9': (1140, 1534), '10': (1040, 1534), '11': (1600, 1504), '12': (1530, 1564), '13': (1670, 1564),
           '14': (1600, 1624), '47': (940, 1534)}
for k, pin in enumerate(('9', '10', '11', '12', '13', '14')):
    y = YL[pin]
    cx_ = 1030 - k * 13
    tx, ty = targets[pin]
    wire([(LX, y), (cx_, y + 4), (cx_, 1390 + k * 6), (tx, 1420 + k * 4), (tx, ty)], cols[pin], 6)
wire([(RX, YR['47']), (1360, YR['47'] + 6), (1380, 1300), (1250, 1420), (940, 1440), (940, 1534)], 'purple', 6)

# ---------- title ----------
d.rectangle(P(40, 40, 900, 210), fill='#f1efe6')
d.rectangle(P(40, 40, 900, 210), outline='#1a1a1a', width=3 * S)
d.text(P(64, 62), 'RETRO CONSOLE', font=HEAD(54), fill='#1a1a1a')
d.text(P(64, 128), 'ESP32-S3 · wiring', font=HEAD(30), fill='#555555')
d.text(P(64, 170), 'github.com/AlexGerUA/retro-console-esp32s3', font=MONO(18), fill='#555555')
d.text(P(W - 60, H - 40), 'Alex_Ger_UA', font=HEAD(26), fill='#cfe8dd', anchor='rm')
d.text(P(60, H - 40), 'модулі живляться від 3V3 плати · GPIO 35–37 = PSRAM', font=MONO(16), fill='#cfe8dd', anchor='lm')

img = img.resize((W, H), Image.LANCZOS)
out = Path(__file__).with_name('pinout.png')
img.save(out, optimize=True)
print('saved', out, img.size)
