"""Draws docs/pinout.png — wiring of the console (source of truth: firmware config.h)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 1200
BG, CARD, INK, MUTED, LINE = '#16181d', '#22252c', '#eef0f3', '#9aa1ad', '#3a3f4a'
COLORS = {'disp': '#38bdf8', 'sd': '#a78bfa', 'audio': '#f472b6', 'joy': '#fbbf24',
          'btn': '#4ade80', 'pwr': '#f87171'}


def font(size, bold=False):
    for name in (('segoeuib.ttf', 'DejaVuSans-Bold.ttf') if bold else ('segoeui.ttf', 'DejaVuSans.ttf')):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


img = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(img)
d.text((60, 40), 'Retro console ESP32-S3 — wiring', font=font(46, True), fill=INK)
d.text((60, 100), 'github.com/AlexGerUA/retro-console-esp32s3 · pins from firmware config.h',
       font=font(24), fill=MUTED)

# board in the centre
bx0, by0, bx1, by1 = 620, 230, 980, 1020
d.rounded_rectangle((bx0, by0, bx1, by1), 24, fill=CARD, outline=INK, width=3)
d.text((800, 560), 'YD-ESP32-S3', font=font(34, True), fill=INK, anchor='mm')
d.text((800, 605), 'N16R8 · 16 MB flash', font=font(22), fill=MUTED, anchor='mm')
d.text((800, 635), '8 MB octal PSRAM', font=font(22), fill=MUTED, anchor='mm')
d.text((800, 985), 'GPIO 33–37 = PSRAM, never use', font=font(20), fill='#f87171', anchor='mm')


def block(x0, y0, x1, title, sub, color, rows, side):
    h = 70 + 34 * len(rows)
    d.rounded_rectangle((x0, y0, x1, y0 + h), 18, fill=CARD, outline=color, width=3)
    d.text((x0 + 22, y0 + 14), title, font=font(26, True), fill=color)
    d.text((x0 + 22, y0 + 46), sub, font=font(18), fill=MUTED)
    for i, (sig, gpio) in enumerate(rows):
        y = y0 + 84 + 34 * i
        d.text((x0 + 22, y), sig, font=font(22), fill=INK, anchor='lm')
        d.text((x1 - 22, y), f'GPIO {gpio}' if isinstance(gpio, int) else gpio,
               font=font(22, True), fill=color, anchor='rm')
        bx = bx0 if side == 'L' else bx1
        sx = x1 if side == 'L' else x0
        d.line((sx, y, bx, y), fill=color, width=3)
        d.ellipse((bx - 6, y - 6, bx + 6, y + 6), fill=color)
    return y0 + h


# left side
block(60, 180, 520, 'Display 2.4" ST7789', 'SPI2 · 320×240 · touch not used', COLORS['disp'],
      [('CS', 4), ('RESET', 5), ('DC', 6), ('MOSI', 7), ('SCK', 15), ('LED (PWM)', 16)], 'L')
block(60, 520, 520, 'SD card (on display module)', 'separate SPI3 bus', COLORS['sd'],
      [('SCK', 39), ('MOSI', 40), ('MISO', 41), ('CS', 42)], 'L')
block(60, 780, 520, 'Audio MAX98357A', 'I2S → 3 W speaker', COLORS['audio'],
      [('BCLK', 17), ('LRCK / WS', 18), ('DIN', 8)], 'L')

# right side
block(1080, 180, 1540, 'Buttons (to GND)', '10 kΩ pull-up + 100 nF each', COLORS['btn'],
      [('A', 13), ('B', 14), ('X  (NES: turbo A)', 11), ('Y  (NES: turbo B)', 12),
       ('SELECT', 47), ('MENU', 10), ('OPTIONS', 9)], 'R')
block(1080, 580, 1540, 'Joystick KY-023', 'power it from 3.3 V only!', COLORS['joy'],
      [('X axis (ADC1)', 1), ('Y axis (ADC1)', 2), ('Press = START', 38)], 'R')
block(1080, 830, 1540, 'Power', '18650 → TP4056 → switch → boost 5 V', COLORS['pwr'],
      [('Board 5V pin', '5V'), ('Battery sense ½', 3), ('RGB LED (on board)', 48)], 'R')

d.text((60, 1130), 'Modules (display, audio, joystick) are powered from the board 3V3. GPL-2.0 · Retro-Go port.',
       font=font(20), fill=MUTED)
out = Path(__file__).with_name('pinout.png')
img.save(out, optimize=True)
print('saved', out, img.size)
