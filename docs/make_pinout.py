"""Draws docs/pinout.png in the style of Espressif's DevKitC-1 pinout.

YD-ESP32-S3 has the same header order as ESP32-S3-DevKitC-1. Pin functions come from
firmware/retro-go-overlay/components/retro-go/targets/retro-console/config.h.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 2200, 1900
S = 2  # supersampling for smooth edges
BG, INK, MUTED = '#ffffff', '#1f2328', '#6b7280'
BOARD, PAD, TRACE = '#2b2f36', '#f5c518', '#3a3f48'

# group -> (fill, text)
G = {
    'gpio': ('#3fae49', '#ffffff'), 'disp': ('#1e88e5', '#ffffff'), 'sd': ('#8e44ad', '#ffffff'),
    'audio': ('#e91e78', '#ffffff'), 'btn': ('#16a34a', '#ffffff'), 'joy': ('#f59e0b', '#1f2328'),
    'pwr': ('#d32f2f', '#ffffff'), 'gnd': ('#111111', '#ffffff'), 'free': ('#cfd4da', '#1f2328'),
    'sys': ('#7a8089', '#ffffff'), 'psram': ('#ffd6d6', '#b00020'), 'usb': ('#7dd3fc', '#0c4a6e'),
    'led': ('#a78bfa', '#ffffff'),
}

# (pin label on board, gpio-chip text or None, [(group, text), ...])
LEFT = [
    ('3V3', None, [('pwr', '3V3')]),
    ('3V3', None, [('pwr', '3V3 → модулі')]),
    ('RST', None, [('sys', 'RST')]),
    ('4', 'GPIO4', [('disp', 'LCD CS')]),
    ('5', 'GPIO5', [('disp', 'LCD RESET')]),
    ('6', 'GPIO6', [('disp', 'LCD DC')]),
    ('7', 'GPIO7', [('disp', 'LCD MOSI')]),
    ('15', 'GPIO15', [('disp', 'LCD SCK')]),
    ('16', 'GPIO16', [('disp', 'LCD LED PWM')]),
    ('17', 'GPIO17', [('audio', 'I2S BCLK')]),
    ('18', 'GPIO18', [('audio', 'I2S LRCK')]),
    ('8', 'GPIO8', [('audio', 'I2S DIN')]),
    ('3', 'GPIO3', [('pwr', 'VBAT ½')]),
    ('46', 'GPIO46', [('free', 'вільний')]),
    ('9', 'GPIO9', [('btn', 'OPTIONS')]),
    ('10', 'GPIO10', [('btn', 'MENU')]),
    ('11', 'GPIO11', [('btn', 'X · турбо A')]),
    ('12', 'GPIO12', [('btn', 'Y · турбо B')]),
    ('13', 'GPIO13', [('btn', 'A')]),
    ('14', 'GPIO14', [('btn', 'B')]),
    ('5V', None, [('pwr', '5V ← boost')]),
    ('G', None, [('gnd', 'GND')]),
]
RIGHT = [
    ('G', None, [('gnd', 'GND')]),
    ('TX', 'GPIO43', [('sys', 'UART TX')]),
    ('RX', 'GPIO44', [('sys', 'UART RX')]),
    ('1', 'GPIO1', [('joy', 'JOY X')]),
    ('2', 'GPIO2', [('joy', 'JOY Y')]),
    ('42', 'GPIO42', [('sd', 'SD CS')]),
    ('41', 'GPIO41', [('sd', 'SD MISO')]),
    ('40', 'GPIO40', [('sd', 'SD MOSI')]),
    ('39', 'GPIO39', [('sd', 'SD SCK')]),
    ('38', 'GPIO38', [('joy', 'JOY SW = START')]),
    ('37', 'GPIO37', [('psram', 'PSRAM — не чіпати')]),
    ('36', 'GPIO36', [('psram', 'PSRAM — не чіпати')]),
    ('35', 'GPIO35', [('psram', 'PSRAM — не чіпати')]),
    ('0', 'GPIO0', [('sys', 'BOOT')]),
    ('45', 'GPIO45', [('free', 'strap')]),
    ('48', 'GPIO48', [('led', 'RGB LED')]),
    ('47', 'GPIO47', [('btn', 'SELECT')]),
    ('21', 'GPIO21', [('free', 'вільний')]),
    ('20', 'GPIO20', [('usb', 'USB D+')]),
    ('19', 'GPIO19', [('usb', 'USB D−')]),
    ('G', None, [('gnd', 'GND')]),
    ('G', None, [('gnd', 'GND')]),
]


def f(size, bold=False):
    names = ('segoeuib.ttf', 'DejaVuSans-Bold.ttf') if bold else ('segoeui.ttf', 'DejaVuSans.ttf')
    for n in names:
        try:
            return ImageFont.truetype(n, size * S)
        except OSError:
            pass
    return ImageFont.load_default()


img = Image.new('RGB', (W * S, H * S), BG)
d = ImageDraw.Draw(img)


def P(*xy):
    return tuple(v * S for v in xy)


def chip(x, y, text, group, align, size=19):
    """Rounded tag; align 'r' = grows to the left from x, 'l' = grows to the right."""
    fill, color = G[group]
    fnt = f(size, True)
    w = d.textlength(text, font=fnt) / S + 22
    h = 30
    x0, x1 = (x - w, x) if align == 'r' else (x, x + w)
    d.rounded_rectangle(P(x0, y - h / 2, x1, y + h / 2), radius=7 * S, fill=fill)
    if group == 'psram':
        d.rounded_rectangle(P(x0, y - h / 2, x1, y + h / 2), radius=7 * S, outline=color, width=2 * S)
    d.text(P((x0 + x1) / 2, y), text, font=fnt, fill=color, anchor='mm')
    return x0 if align == 'r' else x1


# title
d.text(P(60, 40), 'Retro console · ESP32-S3', font=f(56), fill='#4b5563')
d.text(P(60, 118), 'YD-ESP32-S3 N16R8 · розкладка як у ESP32-S3-DevKitC-1 · піни з config.h прошивки',
       font=f(24), fill=MUTED)

# board
cx, top = W / 2, 200
bw, pitch = 300, 44
bx0, bx1 = cx - bw / 2, cx + bw / 2
by0 = top
rows_y = [top + 70 + i * pitch for i in range(22)]
by1 = rows_y[-1] + 70
d.rounded_rectangle(P(bx0, by0, bx1, by1), radius=14 * S, fill=BOARD)
# module + antenna
d.rectangle(P(cx - 80, by0 - 70, cx + 80, by0 + 10), fill='#3b3f47')
for i in range(5):
    xx = cx - 68 + i * 30
    d.line(P(xx, by0 - 55, xx, by0 - 15), fill='#c9cdd3', width=4 * S)
    d.line(P(xx, by0 - 55, xx + 17, by0 - 55), fill='#c9cdd3', width=4 * S)
d.rounded_rectangle(P(cx - 80, by0 + 20, cx + 80, by0 + 330), radius=6 * S, fill='#d8dbe0')
d.rounded_rectangle(P(cx - 68, by0 + 35, cx + 68, by0 + 315), radius=6 * S, fill='#c4c8ce')
d.text(P(cx, by0 + 175), 'ESP32-S3\nWROOM-1\nN16R8', font=f(21, True), fill='#4b5563', anchor='mm', align='center')
# usb ports
for ux, lab in ((cx - 70, 'UART'), (cx + 70, 'USB')):
    d.rounded_rectangle(P(ux - 34, by1 - 30, ux + 34, by1 + 18), radius=8 * S, fill='#c9cdd3')
    d.text(P(ux, by1 - 48), lab, font=f(16, True), fill='#e5e7eb', anchor='mm')
d.text(P(cx, rows_y[11]), 'RGB · GPIO48', font=f(16, True), fill='#e5e7eb', anchor='mm')

PIN_X_L, PIN_X_R = bx0 + 24, bx1 - 24
for (lab, gpio, tags), y in zip(LEFT, rows_y):
    d.ellipse(P(PIN_X_L - 10, y - 10, PIN_X_L + 10, y + 10), fill=PAD)
    d.text(P(PIN_X_L + 22, y), lab, font=f(15, True), fill='#e5e7eb', anchor='lm')
    x = bx0 - 30
    d.line(P(bx0, y, x, y), fill=TRACE, width=3 * S)
    if gpio:
        x = chip(x, y, gpio, 'gpio', 'r') - 6
    for grp, text in tags:
        x = chip(x, y, text, grp, 'r') - 6
for (lab, gpio, tags), y in zip(RIGHT, rows_y):
    d.ellipse(P(PIN_X_R - 10, y - 10, PIN_X_R + 10, y + 10), fill=PAD)
    d.text(P(PIN_X_R - 22, y), lab, font=f(15, True), fill='#e5e7eb', anchor='rm')
    x = bx1 + 30
    d.line(P(bx1, y, x, y), fill=TRACE, width=3 * S)
    if gpio:
        x = chip(x, y, gpio, 'gpio', 'l') + 6
    for grp, text in tags:
        x = chip(x, y, text, grp, 'l') + 6

# ---------- schematics strip ----------
sy = by1 + 70
d.text(P(60, sy), 'Обв\'язка', font=f(30, True), fill=INK)
sy += 60
LINE = '#374151'


def wire(*pts, color=LINE):
    d.line(P(*[v for p in pts for v in p]), fill=color, width=3 * S, joint='curve')


def dot(x, y, color=LINE):
    d.ellipse(P(x - 6, y - 6, x + 6, y + 6), fill=color)


def resistor_v(x, y0, y1, label):
    m = (y0 + y1) / 2
    wire((x, y0), (x, m - 28))
    d.rectangle(P(x - 12, m - 28, x + 12, m + 28), outline=LINE, width=3 * S, fill='#ffffff')
    wire((x, m + 28), (x, y1))
    d.text(P(x + 22, m), label, font=f(18, True), fill=INK, anchor='lm')


def cap_v(x, y0, y1, label):
    m = (y0 + y1) / 2
    wire((x, y0), (x, m - 6))
    wire((x - 20, m - 6), (x + 20, m - 6))
    wire((x - 20, m + 6), (x + 20, m + 6))
    wire((x, m + 6), (x, y1))
    d.text(P(x + 28, m), label, font=f(18, True), fill=INK, anchor='lm')


def gnd(x, y):
    wire((x - 18, y), (x + 18, y))
    wire((x - 11, y + 7), (x + 11, y + 7))
    wire((x - 4, y + 14), (x + 4, y + 14))


def rail(x, y, text, group='pwr'):
    chip(x, y, text, group, 'l', 17)


def panel(x0, title, color):
    d.rounded_rectangle(P(x0, sy, x0 + 500, sy + 440), radius=16 * S, outline=color, width=3 * S)
    d.text(P(x0 + 24, sy + 18), title, font=f(22, True), fill=color)


# 1. button
x0 = 60
panel(x0, 'Кнопка (×7)', G['btn'][0])
bx = x0 + 150
rail(bx - 30, sy + 95, '3V3')
resistor_v(bx, sy + 110, sy + 250, '10 кОм')
dot(bx, sy + 250)
wire((bx, sy + 250), (bx + 190, sy + 250))
chip(bx + 190, sy + 250, 'GPIO', 'gpio', 'l', 17)
cap_v(bx, sy + 250, sy + 360, '100 нФ')
gnd(bx, sy + 360)
# switch
sx = x0 + 70
wire((bx, sy + 250), (sx, sy + 250))
wire((sx, sy + 250), (sx, sy + 290))
wire((sx, sy + 290), (sx - 22, sy + 325))
wire((sx, sy + 335), (sx, sy + 360))
gnd(sx, sy + 360)
d.text(P(x0 + 24, sy + 405), 'Натиснута = 0. Довгі дроти → зовнішня підтяжка.', font=f(16), fill=MUTED)

# 2. battery divider
x0 = 600
panel(x0, 'Заряд батареї', G['pwr'][0])
bx = x0 + 150
rail(bx - 30, sy + 95, 'BAT+')
resistor_v(bx, sy + 110, sy + 230, '100 кОм')
dot(bx, sy + 230)
wire((bx, sy + 230), (bx + 190, sy + 230))
chip(bx + 190, sy + 230, 'GPIO3', 'gpio', 'l', 17)
resistor_v(bx, sy + 230, sy + 350, '100 кОм')
gnd(bx, sy + 350)
d.text(P(x0 + 24, sy + 405), 'Дільник ½: 4.2 В → 2.1 В на АЦП.', font=f(16), fill=MUTED)

# 3. power path
x0 = 1140
panel(x0, 'Живлення', G['pwr'][0])
yy = sy + 90
for i, (txt, grp) in enumerate((('18650', 'pwr'), ('TP4056 + DW01', 'sys'), ('вимикач SS12D00', 'sys'),
                                 ('boost → 5 В', 'pwr'), ('пін 5V плати', 'pwr'))):
    chip(x0 + 40, yy + i * 62, txt, grp, 'l', 18)
    if i:
        wire((x0 + 60, yy + i * 62 - 46), (x0 + 60, yy + i * 62 - 16))
d.text(P(x0 + 24, sy + 405), 'Заряд — через USB-C на TP4056.', font=f(16), fill=MUTED)

# 4. module power
x0 = 1680
panel(x0, 'Модулі від 3V3', G['joy'][0])
yy = sy + 90
chip(x0 + 40, yy, 'пін 3V3 плати', 'pwr', 'l', 18)
for i, (txt, grp) in enumerate((('дисплей + SD', 'disp'), ('MAX98357A', 'audio'), ('джойстик — лише 3.3 В!', 'joy'))):
    wire((x0 + 60, yy + 16 + i * 62), (x0 + 60, yy + 46 + i * 62))
    chip(x0 + 40, yy + 62 + i * 62, txt, grp, 'l', 18)
d.text(P(x0 + 24, sy + 405), 'SW джойстика: 10 кОм на 3V3 (пад R1).', font=f(16), fill=MUTED)

img = img.resize((W, H), Image.LANCZOS)
out = Path(__file__).with_name('pinout.png')
img.save(out, optimize=True)
print('saved', out, img.size)
