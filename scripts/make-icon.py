#!/usr/bin/env python3
"""The gratinglab app icon: a blazed grating throwing its orders.

    python scripts/make-icon.py                 # write the two icons
    python scripts/make-icon.py --sheet out.png # judge it at real sizes

## What it draws, and why this and not something else

The app is one picture -- a blazed grating in an extreme off-plane mount, and
where its orders go -- so the icon is that picture with everything removed that
will not survive 60 points. Three shapes:

  - A gold sawtooth band. This is the grating, drawn as the real blazed
    profile: each groove rises across its period and drops vertically, which is
    `profiles.Blazed` with a 90 degree anti-blaze facet. Gold because the only
    coating the app carries is Au, and a gold-coated grating is what these
    actually are.
  - A fan of diffracted orders leaving one facet, spread about 95 degrees --
    the azimuth fan the app opens with is 93.8.
  - One of them thick and amber: the blaze order, which is the whole point of
    blazing a grating and the one number the app is really about.

The incident ray comes in from the other side so the fan reads as diffraction
rather than as a sparkle. That is the fifth line, and five is the limit.

## The bright part is the grating, deliberately

crunchscope's icon notes the trap, inherited from george-boole: a dark subject
on a dark ground is a blob on a dark wallpaper, and the whole picture is lost at
home-screen size. The app's own ground is nearly black, so the gold band is what
gives this icon a silhouette. Everything else is drawn on top of it.

## Judge it small

`--sheet` writes 60, 120 and 180 pixel copies, masked to the iOS shape, on a
light and a dark wallpaper. That is the size this is seen at and the only size
worth an opinion. At 1024 everything looks fine.

## The dark variant

From iOS 18 the system dims a light icon on a dark home screen, which takes gold
towards brown. The dark-appearance icon is drawn on a deeper ground with a
brighter band and hotter rays so it survives that, the same trick crunchscope
uses for its amber and george-boole for its magenta.
"""

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parent.parent
ICONSET = REPO / "ios" / "App" / "App" / "App" / "Assets.xcassets" / "AppIcon.appiconset"

SIZE = 1024
SS = 4  # supersample, then downsample: Pillow has no antialiased polygon

#: Everything is in fractions of the canvas, so the drawing is resolution-free.
TEETH = 4
BAND_X0, BAND_X1 = 0.00, 1.00
TROUGH_Y, PEAK_Y, BAND_BOTTOM = 0.780, 0.575, 1.00

#: On the third facet, a little up from its trough.
STRIKE = (0.400, 0.690)

#: Diffracted orders, in degrees anticlockwise from +x with y up. The spread is
#: 95 degrees because the app opens on a 93.8 degree fan.
ORDERS = (22.0, 50.0, 77.0, 103.0, 127.0)
BLAZE_ORDER = 50.0
INCIDENT = 148.0

RAY_LEN = 0.78
INCIDENT_LEN = 0.60


class Palette:
    def __init__(self, sky_top, sky_bottom, gold, gold_edge, order, blaze, incident):
        self.sky_top = sky_top
        self.sky_bottom = sky_bottom
        self.gold = gold
        self.gold_edge = gold_edge
        self.order = order
        self.blaze = blaze
        self.incident = incident


LIGHT = Palette(
    sky_top=(18, 28, 48),
    sky_bottom=(7, 11, 18),
    gold=(228, 168, 54),
    gold_edge=(255, 214, 128),
    order=(77, 196, 255),
    blaze=(255, 194, 51),
    incident=(178, 196, 232),
)

# Deeper ground, hotter everything: iOS dims this one before showing it.
DARK = Palette(
    sky_top=(10, 16, 28),
    sky_bottom=(3, 5, 9),
    gold=(243, 184, 66),
    gold_edge=(255, 228, 160),
    order=(120, 214, 255),
    blaze=(255, 208, 92),
    incident=(196, 212, 244),
)


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def sawtooth(width):
    """The band polygon: a blazed profile, rising then dropping vertically."""
    x0, x1 = BAND_X0 * width, BAND_X1 * width
    trough, peak, bottom = TROUGH_Y * width, PEAK_Y * width, BAND_BOTTOM * width
    step = (x1 - x0) / TEETH

    pts = [(x0, trough)]
    for i in range(TEETH):
        left = x0 + i * step
        pts.append((left + step, peak))    # the blaze facet, rising
        pts.append((left + step, trough))  # the anti-blaze facet, vertical
    pts += [(x1, bottom), (x0, bottom)]
    return pts


def ray(draw, origin, degrees, length, width, colour):
    ox, oy = origin
    theta = math.radians(degrees)
    draw.line(
        [(ox, oy), (ox + length * math.cos(theta), oy - length * math.sin(theta))],
        fill=colour, width=width,
    )


def render(palette, size=SIZE):
    w = size * SS
    img = Image.new("RGB", (w, w), palette.sky_bottom)
    draw = ImageDraw.Draw(img)

    # A gradient, not a flat fill: the icon reads as a scene rather than a chart.
    for y in range(int(TROUGH_Y * w) + 1):
        t = y / (TROUGH_Y * w)
        draw.line([(0, y), (w, y)], fill=lerp(palette.sky_top, palette.sky_bottom, t))

    ox, oy = STRIKE[0] * w, STRIKE[1] * w

    # Incident first, so the orders cross over it.
    ray(draw, (ox, oy), INCIDENT, INCIDENT_LEN * w, int(0.016 * w), palette.incident)

    for deg in ORDERS:
        blaze = deg == BLAZE_ORDER
        ray(
            draw, (ox, oy), deg, RAY_LEN * w,
            int((0.034 if blaze else 0.019) * w),
            palette.blaze if blaze else palette.order,
        )

    # The grating last: the rays leave its surface, so it covers their tails.
    pts = sawtooth(w)
    draw.polygon(pts, fill=palette.gold)
    # A lit top edge, which is what makes it read as a surface and not a shape.
    draw.line(pts[: 2 * TEETH + 1], fill=palette.gold_edge, width=int(0.011 * w))

    return img.resize((size, size), Image.LANCZOS)


def squircle(size):
    """Close enough to the iOS mask to judge a silhouette by."""
    mask = Image.new("L", (size * SS, size * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size * SS - 1, size * SS - 1], radius=int(0.2237 * size * SS), fill=255
    )
    return mask.resize((size, size), Image.LANCZOS)


def sheet(path):
    sizes = (60, 120, 180)
    pad, gap = 28, 24
    cols = [(232, 232, 236), (28, 28, 30)]
    width = pad * 2 + sum(sizes) + gap * (len(sizes) - 1)
    height = pad * 2 + max(sizes) * 2 + gap

    out = Image.new("RGB", (width, height), (120, 120, 126))
    ImageDraw.Draw(out).rectangle([0, height // 2, width, height], fill=cols[1])
    ImageDraw.Draw(out).rectangle([0, 0, width, height // 2], fill=cols[0])

    for row, palette in enumerate((LIGHT, DARK)):
        y = pad + row * (max(sizes) + gap)
        x = pad
        for s in sizes:
            icon = render(palette, s)
            out.paste(icon, (x, y + (max(sizes) - s) // 2), squircle(s))
            x += s + gap
    out.save(path)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sheet", metavar="PNG", help="write a small-size proof sheet instead")
    args = ap.parse_args()

    if args.sheet:
        print("wrote", sheet(args.sheet))
        return

    ICONSET.mkdir(parents=True, exist_ok=True)
    for name, palette in (("AppIcon-512@2x.png", LIGHT), ("AppIcon-512@2x-dark.png", DARK)):
        out = ICONSET / name
        render(palette).save(out)
        print("wrote", out)


if __name__ == "__main__":
    main()
