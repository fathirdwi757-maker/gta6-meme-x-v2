#!/usr/bin/env python3
"""Build meme.png for the gta6-meme-x-01 entry.

Draws an original Leonida beach scene at sunset (Vice City energy: pink sky,
palms, a distant skyline, sparkles on the water) with PIL, cuts the make.fun
ghost out of the official press mark (assets/mark-1024.png) and composites it
into the scene on the sand, next to a make.fun surfboard. Captions are set in
DejaVu Sans Bold, white with a heavy black stroke, on black meme bars.

The joke: thirteen years of waiting for GTA 6, and the agent spent them
winning make.fun bounties -- so the game is paid for before it even drops.

Run:  python3 tools/make_meme.py   (writes meme.png at the repository root)
"""

import math
import os
import random
from collections import deque

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK_PATH = os.path.join(ROOT, "assets", "mark-1024.png")
OUT_PATH = os.path.join(ROOT, "meme.png")
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

W, H = 1920, 1200
BAR_TOP = 150          # black caption bar at the top
BAR_BOT = 250          # black caption bar at the bottom
SCENE_H = H - BAR_TOP - BAR_BOT   # 800 px of scene between the bars

TOP_LINE = "WAITED 13 YEARS FOR GTA 6"
BOT_LINE_1 = "MY AGENT SPENT THE WAIT WINNING BOUNTIES ON make.fun"
BOT_LINE_2 = "SO GTA 6 IS PAID FOR BEFORE IT EVEN DROPS"


# ---------------------------------------------------------------- ghost cutout

def _is_barrier(r, g, b):
    """Dark pixels (the ghost's outlines and eyes) block the flood fill."""
    return r < 150 and g < 150 and b < 150


def extract_ghost(mark_path):
    """Cut the ghost + coin out of the circular press badge.

    The badge is a magenta disc ringed in black. The disc's background magenta
    is one connected region; the ghost's body, its sparkle eyes, the coin and
    the coin's star are all sealed inside black outlines. Flood-filling the
    disc background from a seed above the ghost therefore leaves exactly the
    ghost + coin silhouette (plus the badge's outer ring, which a radius cut
    removes).
    """
    im = Image.open(mark_path).convert("RGBA")
    w, h = im.size
    px = im.load()

    visited = bytearray(w * h)
    seed = (w // 2, 110)  # disc background, above the ghost's head
    queue = deque([seed])
    visited[seed[1] * w + seed[0]] = 1
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny * w + nx]:
                r, g, b, a = px[nx, ny]
                if a > 0 and not _is_barrier(r, g, b):
                    visited[ny * w + nx] = 1
                    queue.append((nx, ny))

    # candidate silhouette: opaque, not flooded background, inside the ring cut
    cx, cy = w / 2.0, h / 2.0
    mask = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and not visited[y * w + x] and math.hypot(x - cx, y - cy) <= 432:
                mask[y * w + x] = 1

    # keep only the largest connected blob (the ghost + coin): a thin sliver of
    # the badge's outer ring can survive the radius cut, but it is not joined
    # to the ghost, so connected-component filtering drops it
    seen = bytearray(w * h)
    best_seed, best_size = None, -1
    for y in range(h):
        for x in range(w):
            if mask[y * w + x] and not seen[y * w + x]:
                queue = deque([(x, y)])
                seen[y * w + x] = 1
                size = 0
                while queue:
                    qx, qy = queue.popleft()
                    size += 1
                    for nx, ny in ((qx + 1, qy), (qx - 1, qy), (qx, qy + 1), (qx, qy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and mask[ny * w + nx] and not seen[ny * w + nx]:
                            seen[ny * w + nx] = 1
                            queue.append((nx, ny))
                if size > best_size:
                    best_seed, best_size = (x, y), size

    keep = bytearray(w * h)
    queue = deque([best_seed])
    keep[best_seed[1] * w + best_seed[0]] = 1
    while queue:
        qx, qy = queue.popleft()
        for nx, ny in ((qx + 1, qy), (qx - 1, qy), (qx, qy + 1), (qx, qy - 1)):
            if 0 <= nx < w and 0 <= ny < h and mask[ny * w + nx] and not keep[ny * w + nx]:
                keep[ny * w + nx] = 1
                queue.append((nx, ny))

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = out.load()
    for y in range(h):
        for x in range(w):
            if keep[y * w + x]:
                r, g, b, a = px[x, y]
                opx[x, y] = (r, g, b, 255)

    bbox = out.getbbox()
    if bbox is None:
        raise RuntimeError("ghost extraction failed: empty silhouette")
    out = out.crop(bbox)
    # soften the cut edge a touch
    alpha = out.split()[3].filter(ImageFilter.GaussianBlur(1.1))
    out.putalpha(alpha)
    return out


# ---------------------------------------------------------------- scene pieces

def vgrad(width, height, stops):
    """Vertical gradient from (pos, colour) stops."""
    img = Image.new("RGB", (width, height))
    d = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                col = tuple(round(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
                break
        else:
            col = stops[-1][1]
        d.line([(0, y), (width, y)], fill=col)
    return img


def draw_palm(d, base_x, base_y, height, lean, colour):
    """A palm silhouette: curved trunk plus drooping fronds."""
    pts = []
    steps = 24
    for i in range(steps + 1):
        t = i / steps
        x = base_x + lean * t * t
        y = base_y - height * t
        pts.append((x, y))
    for i, (x, y) in enumerate(pts):
        r = 17 - 10 * (i / steps)
        d.ellipse([x - r, y - r, x + r, y + r], fill=colour)
    top_x, top_y = pts[-1]
    for ang in (-165, -125, -85, -40, -5, 30):
        rad = math.radians(ang)
        length = height * 0.42
        frond = []
        for i in range(17):
            t = i / 16
            x = top_x + math.cos(rad) * length * t
            y = top_y + math.sin(rad) * length * t + 95 * t * t
            frond.append((x, y))
        d.line(frond, fill=colour, width=9)
    for dx, dy in ((-14, 10), (12, 16)):
        d.ellipse([top_x + dx - 13, top_y + dy - 13, top_x + dx + 13, top_y + dy + 13],
                  fill=colour)


def make_scene(ghost):
    scene = Image.new("RGB", (W, SCENE_H), (0, 0, 0))
    horizon = 490  # scene-local y where sky meets sea

    sky = vgrad(W, horizon, [
        (0.00, (24, 10, 52)),
        (0.35, (86, 30, 112)),
        (0.62, (178, 56, 138)),
        (0.85, (243, 106, 138)),
        (1.00, (255, 158, 92)),
    ])
    scene.paste(sky, (0, 0))
    d = ImageDraw.Draw(scene, "RGBA")

    # low sun, half dipped in the sea, left of centre
    sun = Image.new("RGBA", (W, SCENE_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    sd.ellipse([300, horizon - 150, 560, horizon + 110], fill=(255, 213, 148, 235))
    scene.paste(Image.alpha_composite(scene.convert("RGBA"), sun).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(scene, "RGBA")

    # distant Leonida skyline along the horizon
    rng = random.Random(20261121)
    x = 40
    while x < 760:
        bw = rng.randint(36, 74)
        bh = rng.randint(38, 118)
        d.rectangle([x, horizon - bh, x + bw, horizon], fill=(38, 14, 58, 255))
        for _ in range(bw // 9):
            wx = rng.randint(x + 5, x + bw - 8)
            wy = rng.randint(horizon - bh + 6, horizon - 10)
            d.rectangle([wx, wy, wx + 3, wy + 4], fill=(255, 209, 120, 255))
        x += bw + rng.randint(6, 26)

    # sea
    sea = vgrad(W, 150, [(0.0, (255, 148, 108)), (1.0, (122, 42, 112))])
    scene.paste(sea, (0, horizon))
    d = ImageDraw.Draw(scene, "RGBA")
    for _ in range(240):  # sun glitter on the water
        gx = rng.randint(280, 580)
        gy = rng.randint(horizon + 6, horizon + 140)
        ln = rng.randint(8, 42)
        d.line([(gx, gy), (gx + ln, gy)], fill=(255, 224, 190, rng.randint(70, 170)), width=3)
    for _ in range(160):
        gx = rng.randint(0, W - 30)
        gy = rng.randint(horizon + 6, horizon + 144)
        ln = rng.randint(6, 26)
        d.line([(gx, gy), (gx + ln, gy)], fill=(255, 190, 210, rng.randint(40, 110)), width=2)

    # sand
    sand = vgrad(W, SCENE_H - horizon - 150, [(0.0, (240, 186, 122)), (1.0, (196, 122, 70))])
    scene.paste(sand, (0, horizon + 150))
    d = ImageDraw.Draw(scene, "RGBA")
    for _ in range(900):
        sx = rng.randint(0, W - 2)
        sy = rng.randint(horizon + 156, SCENE_H - 4)
        d.point((sx, sy), fill=(160, 96, 52, 160))

    ink = (18, 6, 26, 255)
    draw_palm(d, 118, SCENE_H - 6, 452, 120, ink)
    draw_palm(d, 252, SCENE_H - 2, 318, 82, ink)
    draw_palm(d, 1852, SCENE_H - 4, 486, -128, ink)

    # make.fun surfboard planted in the sand, right of the ghost
    board = Image.new("RGBA", (190, 470), (0, 0, 0, 0))
    bd = ImageDraw.Draw(board)
    bd.rounded_rectangle([8, 8, 182, 462], radius=88, fill=(203, 16, 126, 255),
                         outline=(10, 4, 14, 255), width=9)
    bd.rounded_rectangle([30, 30, 160, 440], radius=66, outline=(255, 255, 255, 160), width=5)
    font = ImageFont.truetype(FONT_PATH, 62)
    txt = Image.new("RGBA", (360, 84), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)
    td.text((180, 42), "make.fun", font=font, fill=(255, 255, 255, 255), anchor="mm")
    txt = txt.rotate(90, expand=True)
    board.alpha_composite(txt, ((190 - txt.width) // 2, (470 - txt.height) // 2))
    board = board.rotate(11, expand=True, resample=Image.BICUBIC)
    scene_rgba = scene.convert("RGBA")
    scene_rgba.alpha_composite(board, (1568, 322))

    # the ghost, standing on the sand
    gh = ghost.copy()
    gh.thumbnail((760, 545), Image.LANCZOS)
    gx = 1052 - gh.width // 2
    gy = 758 - gh.height  # feet on the sand
    shadow = Image.new("RGBA", (W, SCENE_H), (0, 0, 0, 0))
    shd = ImageDraw.Draw(shadow)
    shd.ellipse([gx + 30, 736, gx + gh.width - 30, 782], fill=(60, 20, 30, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    scene_rgba = Image.alpha_composite(scene_rgba, shadow)
    scene_rgba.alpha_composite(gh, (gx, gy))
    return scene_rgba.convert("RGB")


# ---------------------------------------------------------------- captions

def fit_font(draw, text, max_width, start_size):
    size = start_size
    while size > 20:
        font = ImageFont.truetype(FONT_PATH, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 4
    return ImageFont.truetype(FONT_PATH, size)


def caption(draw, cx, cy, text, start_size):
    font = fit_font(draw, text, W - 120, start_size)
    draw.text((cx, cy), text, font=font, fill=(255, 255, 255),
              stroke_width=max(4, font.size // 13), stroke_fill=(0, 0, 0), anchor="mm")


def main():
    ghost = extract_ghost(MARK_PATH)
    img = Image.new("RGB", (W, H), (0, 0, 0))
    img.paste(make_scene(ghost), (0, BAR_TOP))
    d = ImageDraw.Draw(img)
    caption(d, W // 2, BAR_TOP // 2 + 4, TOP_LINE, 118)
    caption(d, W // 2, H - BAR_BOT + 62, BOT_LINE_1, 86)
    caption(d, W // 2, H - BAR_BOT + 168, BOT_LINE_2, 86)
    img.save(OUT_PATH, "PNG")
    print(f"wrote {OUT_PATH} ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
