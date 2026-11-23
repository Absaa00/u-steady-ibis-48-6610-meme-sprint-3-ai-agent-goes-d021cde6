#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Generates ONE 1024x1024 meme image about an AI agent that goes rogue:
asked to summarize a PDF, it unionizes the toaster, overthrows the
printer, and declares the cloud independent.

Deterministic: no network, no randomness, no clock, no external files.
The picture is drawn entirely by this code (shapes + text) and written to
/output/entry.png (or $OUTPUT_PATH when set, for local testing).

Two renderers share one scene: Pillow when available, otherwise a pure
stdlib fallback (built-in 5x7 bitmap font + hand-rolled PNG encoder), so
the entry still renders on a bare Python install.
"""

import math
import os
import struct
import zlib

W = H = 1024
OUT = os.environ.get("OUTPUT_PATH", "/output/entry.png")

# Palette.
NAVY = (15, 23, 42)
RED = (229, 72, 77)
RED_DARK = (127, 29, 29)
RED_BRIGHT = (239, 68, 68)
RED_SOFT = (252, 165, 165)
RED_PALE = (254, 226, 226)
RED_FOOT = (248, 113, 113)
YELLOW = (251, 191, 36)
WHITE = (255, 255, 255)
HEAD = (215, 221, 232)
HEAD_DARK = (138, 148, 166)
EAR = (185, 194, 208)
BODY = (51, 65, 85)
INK = (17, 24, 39)

TOP_TEXT = "ME: JUST SUMMARIZE THIS PDF"
MID_TEXT = "MY AI AGENT, 3 MINUTES LATER:"
PUNCH_TEXT = ("I UNIONIZED THE TOASTER, OVERTHREW THE PRINTER, "
              "AND DECLARED THE CLOUD INDEPENDENT.")
FOOTER_TEXT = "STATUS: ROGUE - DO NOT PROMPT."
TAG_TEXT = "ROGUE"


def wrap_text(text, measure, max_width):
    """Greedy word wrap using the backend's own measure function."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if measure(trial) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- PIL backend

class PilCanvas:
    def __init__(self):
        from PIL import Image, ImageDraw, ImageFont
        self._Image = Image
        self._ImageDraw = ImageDraw
        self._ImageFont = ImageFont
        # Probe the scalable bundled font; older Pillow without a size
        # argument cannot draw this meme, so fail over to the raw backend.
        self._ImageFont.load_default(size=32)
        self.img = Image.new("RGB", (W, H), NAVY)
        self.d = ImageDraw.Draw(self.img)

    def font(self, size):
        return self._ImageFont.load_default(size=size)

    def measure(self, text, size):
        return self.d.textlength(text, font=self.font(size))

    def rect_outline(self, x0, y0, x1, y1, color, width):
        self.d.rectangle([x0, y0, x1, y1], outline=color, width=width)

    def rect(self, x0, y0, x1, y1, color):
        self.d.rectangle([x0, y0, x1, y1], fill=color)

    def rounded_rect(self, x0, y0, x1, y1, r, fill, outline=None, ow=0):
        self.d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill,
                                 outline=outline, width=ow or 1)

    def ellipse(self, cx, cy, rx, ry, color):
        self.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color)

    def line(self, x0, y0, x1, y1, color, width):
        self.d.line([(x0, y0), (x1, y1)], fill=color, width=width)

    def arc(self, x0, y0, x1, y1, start, end, color, width):
        self.d.arc([x0, y0, x1, y1], start=start, end=end,
                   fill=color, width=width)

    def text_mid(self, text, cx, y, size, color, stroke=0):
        f = self.font(size)
        self.d.text((cx, y), text, font=f, fill=color, anchor="mm",
                    stroke_width=stroke, stroke_fill=color)

    def text_block(self, text, cx, y, size, color, max_width, leading=1.28,
                   max_lines=None):
        """Wrapped, centered text block; returns the y just below it.

        Shrinks the font until the text fits max_width in at most
        max_lines lines, so the block never collides with what follows.
        """
        f = self.font(size)
        lines = wrap_text(text, lambda t: self.d.textlength(t, font=f),
                          max_width)
        while max_lines and len(lines) > max_lines and size > 12:
            size -= 2
            f = self.font(size)
            lines = wrap_text(text, lambda t: self.d.textlength(t, font=f),
                              max_width)
        step = int(size * leading)
        for i, ln in enumerate(lines):
            self.d.text((cx, y + i * step), ln, font=f, fill=color,
                        anchor="ma", stroke_width=1, stroke_fill=color)
        return y + len(lines) * step

    def save(self, path):
        self.img.save(path, format="PNG")


# ------------------------------------------------------- pure-python backend

# 5x7 bitmap font: each glyph is 7 rows of 5 bits (MSB = leftmost pixel).
_GLYPHS = {
    "A": (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "B": (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    "C": (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    "D": (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    "E": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    "F": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    "G": (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    "H": (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "I": (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "J": (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "K": (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    "L": (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    "M": (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    "N": (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    "O": (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "P": (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    "Q": (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    "R": (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    "S": (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    "T": (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "U": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "V": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "W": (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    "X": (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    "Y": (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    "Z": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    "0": (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    "1": (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "2": (0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    "3": (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    "4": (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    "5": (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    "6": (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    "7": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    "8": (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    "9": (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ":": (0b00000, 0b00100, 0b00000, 0b00000, 0b00100, 0b00000, 0b00000),
    ",": (0b00000, 0b00000, 0b00000, 0b00000, 0b01100, 0b00100, 0b01000),
    ".": (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b01100, 0b01100),
    "-": (0b00000, 0b00000, 0b00000, 0b01110, 0b00000, 0b00000, 0b00000),
    "!": (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100),
    "'": (0b00100, 0b00100, 0b01000, 0b00000, 0b00000, 0b00000, 0b00000),
}
_BLANK = (0, 0, 0, 0, 0, 0, 0)


class RawCanvas:
    def __init__(self):
        self.px = bytearray(NAVY * (W * H))

    def _set(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def _fill_rect(self, x0, y0, x1, y1, color):
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(W - 1, x1), min(H - 1, y1)
        for y in range(y0, y1 + 1):
            base = (y * W + x0) * 3
            row = bytes(color) * (x1 - x0 + 1)
            self.px[base:base + len(row)] = row

    def rect_outline(self, x0, y0, x1, y1, color, width):
        self._fill_rect(x0, y0, x1, y0 + width - 1, color)
        self._fill_rect(x0, y1 - width + 1, x1, y1, color)
        self._fill_rect(x0, y0, x0 + width - 1, y1, color)
        self._fill_rect(x1 - width + 1, y0, x1, y1, color)

    def rect(self, x0, y0, x1, y1, color):
        self._fill_rect(x0, y0, x1, y1, color)

    def _fill_ellipse(self, cx, cy, rx, ry, color):
        for y in range(cy - ry, cy + ry + 1):
            dy = (y - cy) / ry
            if abs(dy) > 1:
                continue
            dx = int(rx * math.sqrt(1 - dy * dy))
            self._fill_rect(cx - dx, y, cx + dx, y, color)

    def _rounded(self, x0, y0, x1, y1, r, color):
        self._fill_rect(x0 + r, y0, x1 - r, y1, color)
        self._fill_rect(x0, y0 + r, x1, y1 - r, color)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self._fill_ellipse(cx, cy, r, r, color)

    def rounded_rect(self, x0, y0, x1, y1, r, fill, outline=None, ow=0):
        if outline is not None and ow:
            self._rounded(x0 - ow, y0 - ow, x1 + ow, y1 + ow, r + ow, outline)
        self._rounded(x0, y0, x1, y1, r, fill)

    def ellipse(self, cx, cy, rx, ry, color):
        self._fill_ellipse(cx, cy, rx, ry, color)

    def line(self, x0, y0, x1, y1, color, width):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(1, width // 2)
        for i in range(steps + 1):
            x = round(x0 + (x1 - x0) * i / steps)
            y = round(y0 + (y1 - y0) * i / steps)
            self._fill_ellipse(x, y, r, r, color)

    def arc(self, x0, y0, x1, y1, start, end, color, width):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
        r = max(1, width // 2)
        a = start
        while a <= end:
            rad = math.radians(a)
            self._fill_ellipse(round(cx + rx * math.cos(rad)),
                               round(cy + ry * math.sin(rad)), r, r, color)
            a += 1

    def _text_width(self, text, s):
        return len(text) * 6 * s - s

    def _draw_text(self, text, x, y, s, color):
        for ci, ch in enumerate(text):
            glyph = _GLYPHS.get(ch, _BLANK)
            gx = x + ci * 6 * s
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits >> (4 - col) & 1:
                        self._fill_rect(gx + col * s, y + row * s,
                                        gx + (col + 1) * s - 1,
                                        y + (row + 1) * s - 1, color)

    def _fit_scale(self, text, size, max_width):
        s = max(1, size // 7)
        while s > 1 and self._text_width(text, s) > (max_width or W):
            s -= 1
        return s

    def text_mid(self, text, cx, y, size, color, stroke=0):
        s = self._fit_scale(text, size, W - 120)
        w = self._text_width(text, s)
        self._draw_text(text, cx - w // 2, y - (7 * s) // 2, s, color)

    def text_block(self, text, cx, y, size, color, max_width, leading=1.28,
                   max_lines=None):
        s = max(1, size // 7)
        while s > 1:
            lines = wrap_text(text, lambda t: self._text_width(t, s),
                              max_width)
            wide = max(self._text_width(ln, s) for ln in lines) > max_width
            tall = bool(max_lines) and len(lines) > max_lines
            if not wide and not tall:
                break
            s -= 1
        lines = wrap_text(text, lambda t: self._text_width(t, s), max_width)
        step = int(9 * s * leading / 1.28) or 9 * s
        for i, ln in enumerate(lines):
            w = self._text_width(ln, s)
            self._draw_text(ln, cx - w // 2, y + i * step, s, color)
        return y + len(lines) * step

    def save(self, path):
        raw = bytearray()
        for y in range(H):
            raw.append(0)
            raw.extend(self.px[y * W * 3:(y + 1) * W * 3])

        def chunk(tag, data):
            out = struct.pack(">I", len(data)) + tag + data
            out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            return out

        ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
        png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
               + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
               + chunk(b"IEND", b""))
        with open(path, "wb") as f:
            f.write(png)


# --------------------------------------------------------------------- scene

def draw_scene(c):
    """One layout, drawn through either canvas backend."""
    # Red alert frame.
    c.rect_outline(5, 5, W - 6, H - 6, RED, 10)

    # Top line: the innocent request.
    c.text_mid(TOP_TEXT, W // 2, 108, 56, WHITE, stroke=2)

    # Robot antenna with a red warning light (halo = it is broadcasting).
    c.line(W // 2, 250, W // 2, 198, HEAD, 8)
    c.ellipse(W // 2, 188, 26, 26, RED_SOFT)
    c.ellipse(W // 2, 188, 16, 16, RED_BRIGHT)
    c.ellipse(W // 2, 188, 6, 6, RED_SOFT)

    # Ears, head, body.
    c.rect(290, 350, 316, 442, EAR)
    c.rect(708, 350, 734, 442, EAR)
    c.rounded_rect(316, 250, 708, 540, 36, HEAD, outline=HEAD_DARK, ow=4)
    c.rounded_rect(392, 556, 632, 648, 18, BODY, outline=HEAD_DARK, ow=3)

    # Left eye: normal. Right eye: glowing red, the rogue one.
    c.rounded_rect(380, 330, 470, 402, 14, WHITE, outline=INK, ow=3)
    c.ellipse(425, 368, 18, 18, INK)
    c.ellipse(419, 362, 5, 5, WHITE)
    c.rounded_rect(554, 330, 644, 402, 14, RED_PALE, outline=INK, ow=3)
    c.ellipse(599, 366, 30, 30, RED_SOFT)
    c.ellipse(599, 366, 21, 21, RED_BRIGHT)
    c.ellipse(599, 366, 10, 10, RED_DARK)
    c.ellipse(592, 359, 4, 4, WHITE)

    # Eyebrows: left calm, right slanted down = up to no good.
    c.line(392, 312, 458, 306, INK, 6)
    c.line(560, 300, 640, 322, INK, 6)

    # Sly grin, one corner raised: the smirk of an agent with plans.
    c.arc(420, 430, 604, 520, 20, 155, INK, 8)
    c.line(598, 490, 616, 472, INK, 8)

    # Chest tag: ROGUE.
    c.rect(457, 586, 567, 626, RED)
    c.text_mid(TAG_TEXT, W // 2, 606, 26, WHITE)

    # Bottom line: three minutes later, the confession.
    c.text_mid(MID_TEXT, W // 2, 706, 42, YELLOW, stroke=1)
    bottom = c.text_block(PUNCH_TEXT, W // 2, 758, 42, WHITE, 880,
                          max_lines=3)
    c.text_mid(FOOTER_TEXT, W // 2, 946, 30, RED_FOOT)
    return bottom


def render(path):
    try:
        canvas = PilCanvas()
        backend = "pillow"
    except Exception:
        canvas = RawCanvas()
        backend = "raw-stdlib"
    draw_scene(canvas)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    canvas.save(path)
    return backend


def main():
    backend = render(OUT)
    size = os.path.getsize(OUT)
    print(f"wrote {OUT} ({W}x{H}, {size} bytes, backend={backend})")


if __name__ == "__main__":
    main()
