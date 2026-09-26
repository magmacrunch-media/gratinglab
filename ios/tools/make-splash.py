#!/usr/bin/env python3
"""The launch image: a grating, mid-diffraction, an instant before the app.

    python ios/tools/make-splash.py              # write the three splash files
    python ios/tools/make-splash.py --crops out.png   # see what a device shows

## What it draws

The app's own opening frame, reduced to what survives a launch image: the
gold-coated blazed grating, the orders leaving one facet, the blaze order thick
and amber, and the incident ray arriving from the other side. The still
therefore hands over to a running app that continues from where it left off
rather than cutting from a splash to something else.

The publisher's mark sits below it, derived from the one logo in the website
repo rather than copied, so there is one definition of the mark.

## The square is mostly cropped away, on BOTH axes here

`LaunchScreen.storyboard` aspect-fills one square, so the view's shorter side
decides how much survives on that axis:

    a portrait  view (W < H)  ->  full height, W/H of the WIDTH
    a landscape view (W > H)  ->  full width,  H/W of the HEIGHT

`Info.plist` allows portrait and both landscapes on the phone, so **both**
happen and both are at the narrowest phone ratio. That is the difference from
crunchscope, which is portrait-only on the phone and therefore only ever loses
width. Anything that must be seen lives in the central 46% square; the grating
band and the rays deliberately run past it and get cut, which is what they do in
the app too.

`hypnopompia/tools/check-launch-crop.mjs` ties CROP_WIDTH and CROP_HEIGHT below
to the orientations in Info.plist, so flipping an orientation cannot silently
invalidate them. It reads the names, not the assertions -- a named constant is a
thing this declares, an `if` is a thing it does.

## No wordmark text

The games and crunchscope set "magmacrunch media" in PressStart2P. That is the
arcade's voice and this app's is IBM Plex, of which the only copies to hand are
woff2, which Pillow cannot read. The mark alone is the honest version; adding
the line back is a font away.
"""

import argparse
import os
from pathlib import Path

from PIL import Image, ImageDraw

IOS = Path(__file__).resolve().parent.parent
REPO = IOS.parent
SPLASH = IOS / "App" / "App" / "App" / "Assets.xcassets" / "Splash.imageset"

SIZE = 2732

#: The fraction of each axis a device can still show, narrowest current phone
#: (1320 x 2868 -> 0.460). Both axes, because Info.plist allows both
#: orientations on the phone. Checked by hypnopompia's check-launch-crop.mjs.
CROP_WIDTH = 0.460
CROP_HEIGHT = 0.460

#: The app's own ground, from :root in app/index.html.
SKY_TOP = (16, 26, 45)
SKY_EDGE = (6, 9, 16)
GOLD = (228, 168, 54)
GOLD_EDGE = (255, 214, 128)
ORDER = (77, 196, 255)
BLAZE = (255, 194, 51)
INCIDENT = (150, 168, 204)

TEETH = 14
PEAK_Y, TROUGH_Y, BAND_BOTTOM = 0.468, 0.505, 0.521
STRIKE = (0.500, 0.487)
ORDERS = (25.0, 52.0, 78.0, 104.0, 128.0)
BLAZE_ORDER = 52.0
INCIDENT_ANGLE = 149.0
RAY_LEN, INCIDENT_LEN = 0.62, 0.42

# 300 is about as large as the mark goes: its foot then sits at y = 0.695
# against a safe box that ends at 0.730, and the assertion below is what
# says so rather than my eye.
MARK_HEIGHT = 300
MARK_TOP = 0.585

FILES = ["splash-2732x2732.png", "splash-2732x2732-1.png", "splash-2732x2732-2.png"]

SOURCE_CANDIDATES = [
    Path(os.environ["WEBSITE"]) if os.environ.get("WEBSITE") else None,
    REPO.parent / "website",
    REPO.parent.parent / "web" / "website",
]


def website():
    for candidate in SOURCE_CANDIDATES:
        if candidate and (candidate / "assets" / "logos" / "MClogoNoText.png").exists():
            return candidate
    raise SystemExit(
        "website checkout not found; set WEBSITE=<path>.\n"
        "Only this script needs it -- ios/package.mjs deliberately does not."
    )


def mark(height):
    """The publisher mark, redrawn white from the source's alpha.

    The source is a 2500x2650 PNG of pure black on transparency: only the alpha
    carries the drawing, and black is invisible on this ground, so the mark is
    rebuilt from the alpha and the black discarded. Same treatment crunchscope
    and george-boole give the same file.
    """
    art = Image.open(website() / "assets" / "logos" / "MClogoNoText.png").convert("RGBA")
    alpha = art.getchannel("A")
    box = alpha.point(lambda v: 255 if v > 20 else 0).getbbox()
    if not box:
        raise SystemExit("the logo source is entirely transparent")
    alpha = alpha.crop(box)
    width = max(1, round(alpha.width * height / alpha.height))
    alpha = alpha.resize((width, height), Image.LANCZOS)

    out = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
    out.putalpha(alpha)
    return out


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def draw_splash():
    img = Image.new("RGB", (SIZE, SIZE), SKY_EDGE)
    d = ImageDraw.Draw(img, "RGBA")

    # A radial wash toward the top centre, as the app's stage has.
    cx, cy = SIZE * 0.5, SIZE * 0.12
    far = max(SIZE, SIZE)
    for r in range(int(far), 0, -12):
        t = min(1.0, r / far)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=lerp(SKY_TOP, SKY_EDGE, t))

    ox, oy = STRIKE[0] * SIZE, STRIKE[1] * SIZE

    def ray(deg, length, width, colour):
        import math
        th = math.radians(deg)
        d.line([(ox, oy), (ox + length * SIZE * math.cos(th),
                           oy - length * SIZE * math.sin(th))], fill=colour, width=width)

    ray(INCIDENT_ANGLE, INCIDENT_LEN, round(SIZE * 0.0055), INCIDENT)
    for deg in ORDERS:
        blaze = deg == BLAZE_ORDER
        ray(deg, RAY_LEN, round(SIZE * (0.0105 if blaze else 0.0058)),
            BLAZE if blaze else ORDER)

    # The grating: a thin band across the frame, blazed, cut off at both sides
    # exactly as the app's patch is.
    peak, trough, bottom = PEAK_Y * SIZE, TROUGH_Y * SIZE, BAND_BOTTOM * SIZE
    step = SIZE / TEETH
    pts = [(0, trough)]
    for i in range(TEETH):
        pts.append(((i + 1) * step, peak))
        pts.append(((i + 1) * step, trough))
    pts += [(SIZE, bottom), (0, bottom)]
    d.polygon(pts, fill=GOLD)
    d.line(pts[: 2 * TEETH + 1], fill=GOLD_EDGE, width=round(SIZE * 0.0025))

    logo = mark(MARK_HEIGHT)
    left, top = (SIZE - logo.width) // 2, round(MARK_TOP * SIZE)
    img.paste(logo, (left, top), logo)

    # What must be seen has to be inside the box every device keeps. The band
    # and the rays are meant to be cut; the mark is not.
    lo_x, hi_x = (1 - CROP_WIDTH) / 2, (1 + CROP_WIDTH) / 2
    lo_y, hi_y = (1 - CROP_HEIGHT) / 2, (1 + CROP_HEIGHT) / 2
    for name, (x0, y0, x1, y1) in {
        "the publisher mark": (left / SIZE, top / SIZE,
                               (left + logo.width) / SIZE, (top + logo.height) / SIZE),
        "the strike point": (STRIKE[0], STRIKE[1], STRIKE[0], STRIKE[1]),
    }.items():
        if not (lo_x <= x0 and x1 <= hi_x and lo_y <= y0 and y1 <= hi_y):
            raise SystemExit(
                f"{name} leaves the safe box: x {x0:.3f}-{x1:.3f}, y {y0:.3f}-{y1:.3f}, "
                f"box x {lo_x:.3f}-{hi_x:.3f}, y {lo_y:.3f}-{hi_y:.3f}"
            )
    return img


def crops(path):
    """What aspect-fill actually shows. Both phone orientations, because both
    are allowed here and they crop opposite axes."""
    screens = [
        ("iPhone portrait", 1206, 2622),
        ("iPhone landscape", 2622, 1206),
        ("iPad portrait", 2064, 2752),
    ]
    img = draw_splash()
    shots = []
    for name, w, h in screens:
        scale = max(w / SIZE, h / SIZE)
        big = img.resize((round(SIZE * scale), round(SIZE * scale)), Image.LANCZOS)
        left, top = (big.width - w) // 2, (big.height - h) // 2
        shot = big.crop((left, top, left + w, top + h))
        shots.append((name, shot.resize((round(w * 340 / h), 340), Image.LANCZOS)))

    gap = 26
    out = Image.new("RGB", (sum(s.width for _, s in shots) + gap * (len(shots) + 1),
                            340 + gap * 2), (40, 40, 44))
    x = gap
    for _, s in shots:
        out.paste(s, (x, gap))
        x += s.width + gap
    out.save(path)
    print("crops ", path, " ", ", ".join(n for n, _ in shots))


def main():
    ap = argparse.ArgumentParser(description="Draw the gratinglab launch image.")
    ap.add_argument("--crops", help="render what each device shows")
    args = ap.parse_args()

    if args.crops:
        crops(args.crops)
        return

    img = draw_splash()
    SPLASH.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        img.save(SPLASH / name)
        print("wrote", SPLASH / name)


if __name__ == "__main__":
    main()
