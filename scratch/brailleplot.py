# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import math
import time
import collections

PY2 = sys.version < "3"

if PY2:
    import __builtin__ as builtins
else:
    import builtins

if PY2:
    chr = builtins.unichr
    range = builtins.xrange
else:
    chr = builtins.chr
    range = builtins.range


# https://github.com/asciimoo/drawille/
# https://blog.jverkamp.com/2014/05/30/braille-unicode-pixelation/

# braille unicode characters starts at 0x2800
PIX_OFFSET = 0x2800

PIX_MAP = (
    0x01, 0x08,
    0x02, 0x10,
    0x04, 0x20,
    0x40, 0x80,
)

PixBuf = collections.namedtuple('PixBuf', [
    'buffer', 'width', 'height'
])


def mk_pixbuf(buf, width, height):
    if width * height != len(buf):
        msg_fmt = "Invalid pixbuf size {} for {}x{}"
        raise ValueError(msg_fmt.format(len(buf), width, height))
    return PixBuf(buf, width, height)


def avg(vals, l_idx, r_idx):
    if l_idx == r_idx:
        return vals[l_idx]
    sample = vals[l_idx:r_idx]
    return sum(sample) / (r_idx - l_idx)


def render(pixbuf):
    # TODO (mb 2016-09-16): deal with
    #   width non divisible by 2
    #   height non divisible by 4
    width = pixbuf.width
    height = pixbuf.height
    buf = pixbuf.buffer

    chars = []
    for char_y in range(0, height, 4):
        for char_x in range(0, width, 2):
            chars.append(chr(
                PIX_OFFSET +
                (0x01 * buf[char_x + 0 + (char_y + 0) * width]) |
                (0x08 * buf[char_x + 1 + (char_y + 0) * width]) |
                (0x02 * buf[char_x + 0 + (char_y + 1) * width]) |
                (0x10 * buf[char_x + 1 + (char_y + 1) * width]) |
                (0x04 * buf[char_x + 0 + (char_y + 2) * width]) |
                (0x20 * buf[char_x + 1 + (char_y + 2) * width]) |
                (0x40 * buf[char_x + 0 + (char_y + 3) * width]) |
                (0x80 * buf[char_x + 1 + (char_y + 3) * width]) |
                0
            ))
        chars.append("\n")

    return "".join(chars).encode('utf-8')


def plot(vals, char_width=200, char_height=30, style='line'):
    if style not in ('line', 'fill'):
        msg = "Invalid value '{}' for parameter style.".format(style)
        raise ValueError(msg)

    width = char_width * 2
    height = char_height * 4

    min_val = min(vals)
    max_val = max(vals)
    scale = max_val - min_val
    y_zero = 0   # y value of val=0
    print(min_val, max_val, scale, y_zero)

    scaled_vals = [height * (v - min_val) / scale for v in vals]

    buf = [0] * (width * height)
    print(
        width, height, len(buf),
        len(scaled_vals), min(scaled_vals), max(scaled_vals)
    )

    step_size = len(vals) / width
    half_step = max(1, step_size // 2)
    min_idx = 0
    max_idx = len(vals) - 1
    for x in range(width):
        l_idx = x * step_size
        r_idx = x * step_size + step_size

        l_sample = int(round(avg(
            scaled_vals,
            max(min_idx, int(math.floor(l_idx - half_step))),
            min(max_idx, int(math.ceil(l_idx + half_step)))
        )))
        r_sample = int(round(avg(
            scaled_vals,
            max(min_idx, int(math.floor(r_idx - half_step))),
            min(max_idx, int(math.ceil(r_idx + half_step)))
        )))
        lo_sample = min((l_sample, r_sample))
        hi_sample = max((l_sample, r_sample))

        if lo_sample == hi_sample:
            if hi_sample == height:
                lo_sample -= 1
            else:
                hi_sample += 1

        for y in range(lo_sample, hi_sample):
            buf[y * width + x] = 1

    return mk_pixbuf(buf, width, height)


# print(plot([n for n in range(80)]))
# print(plot([n for n in range(80, 0, -1)]))
# print(plot([n for n in range(160)]))

print(render(mk_pixbuf([
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1,
    1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
], 16, 16)))

print(render(mk_pixbuf(sum(list(
    map(int, "{:08b}".format(n)) for n in range(256)
), []), 64, 32)))


while 0:
    t0 = time.time()
    pixbuf = plot([
        math.sin(6 * t0 / 13 + n / 100)
        for n in range(0, 500)
    ])
    t1 = time.time()
    out_buf = render(pixbuf)
    t2 = time.time()
    sys.stdout.write("\033c" + out_buf)
    t3 = time.time()
    print((t1 - t0) * 1000)
    print((t2 - t1) * 1000)
    print((t3 - t2) * 1000)
    time.sleep(.3)