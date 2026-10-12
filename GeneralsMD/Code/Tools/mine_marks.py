"""The picture a China mine is drawn with: a round steel pressure mine seen from above, sunk in a ring
of disturbed earth.  The game lays it flat on the ground at each of a mine field's eight mine bones
(ParticleSystemReforged.ini, MineFX and MineFXPurple), so it is shaded here once, lit from the top
left, and the soil ring fades out into whatever ground it lands on.

The arming light over each mine is an LED seen from above: a lens in the light's colour, red for the
standard and cluster mines and a saturated blue for the EMP mines, with a near-white hot spot in its
middle, inside a dark bezel.  It is alpha blended, not additive, so the lens keeps its colour over
grass, sand or snow and the bezel parts it from whatever ground is round it.

    python Tools/mine_marks.py            # writes Data/Art/Textures/ReforgedMine.tga and ReforgedMineLed*.tga

Drawn four times too big and brought down, which is the antialiasing."""
import math
import os
import random
import sys

from PIL import Image

DRAWN = 512
SHIPPED = 128
CENTRE = (DRAWN - 1) / 2.0
LIGHT = (-0.45, -0.55, 0.70)	# towards the light: up and to the left in the picture, mostly overhead
STEEL = (64, 68, 54)		# olive drab, darker than grey ballast so the plate stands off it
SOIL = (26, 20, 14)
SOIL_ALPHA = 0.85		# the dark ring is what tells a mine from a stone on grass at the player's camera
OUTLINE = 0.035			# a near-black edge round the steel, as a share of the half width
PLATE = 0.70			# radius of the steel, as a share of the half width
SOIL_OUT = 0.98
BOLTS = 0.55
LED_HOT = 0.10			# radius of the near-white hot spot, as a share of the half width
LED_LENS = 0.50			# radius of the lit lens in the light's colour
LED_BEZEL_OUT = 0.74		# outer edge of the dark bezel round the lens
LED_BEZEL = (10, 8, 8)
LED_BEZEL_ALPHA = 0.9
LEDS = (("Red", (255, 28, 10), (255, 235, 225)), ("Blue", (40, 110, 255), (225, 240, 255)))
OUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Data", "Art", "Textures")


def ramp(edge0, edge1, x):
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def height(x, y):
    """The steel's height at a point in half widths: a bevelled rim, a flat top with a groove, a raised
    pressure cap in the middle and four bolt heads."""
    r = math.hypot(x, y)
    h = 1.0 - ramp(PLATE - 0.08, PLATE, r)		# rim bevel down to the soil
    h -= 0.25 * (ramp(0.40, 0.42, r) - ramp(0.45, 0.47, r))	# groove round the top
    h += 0.35 * (1.0 - ramp(0.20, 0.25, r))		# pressure cap
    for k in range(4):
        angle = math.radians(45 + 90 * k)
        d = math.hypot(x - BOLTS * math.cos(angle), y - BOLTS * math.sin(angle))
        h += 0.18 * (1.0 - ramp(0.02, 0.045, d))
    return h


def main():
    out_folder = sys.argv[1] if len(sys.argv) > 1 else OUT_FOLDER
    length = math.sqrt(sum(c * c for c in LIGHT))
    light = [c / length for c in LIGHT]
    grit = random.Random(7)
    step = 2.0 / DRAWN
    image = Image.new("RGBA", (DRAWN, DRAWN))
    pixels = image.load()
    for py in range(DRAWN):
        y = (py - CENTRE) / CENTRE
        for px in range(DRAWN):
            x = (px - CENTRE) / CENTRE
            r = math.hypot(x, y)
            noise = grit.uniform(-1.0, 1.0)
            if r < PLATE:
                # slope over eight drawn pixels, scaled so a bevel tilts the normal well over
                dx = (height(x + step * 4, y) - height(x - step * 4, y)) / (step * 8) * 0.06
                dy = (height(x, y + step * 4) - height(x, y - step * 4)) / (step * 8) * 0.06
                n = (-dx, -dy, 1.0)
                nl = math.sqrt(n[0] * n[0] + n[1] * n[1] + 1.0)
                lit = max(0.0, (n[0] * light[0] + n[1] * light[1] + n[2] * light[2]) / nl)
                shade = 0.25 + 1.1 * lit + 0.05 * noise
                if r > PLATE - OUTLINE:
                    shade *= 0.35
                colour = tuple(min(255, max(0, int(c * shade))) for c in STEEL)
                pixels[px, py] = colour + (255,)
            elif r < SOIL_OUT:
                alpha = SOIL_ALPHA * (1.0 - ramp(PLATE + 0.06, SOIL_OUT, r)) * (0.85 + 0.15 * noise)
                shade = 0.9 + 0.2 * noise
                colour = tuple(min(255, max(0, int(c * shade))) for c in SOIL)
                pixels[px, py] = colour + (max(0, int(255 * alpha)),)
            else:
                pixels[px, py] = SOIL + (0,)
    path = os.path.join(out_folder, "ReforgedMine.tga")
    image.resize((SHIPPED, SHIPPED), Image.LANCZOS).save(path)
    print(path)
    for name, glow, core in LEDS:
        path = os.path.join(out_folder, "ReforgedMineLed%s.tga" % name)
        led(glow, core).resize((SHIPPED, SHIPPED), Image.LANCZOS).save(path)
        print(path)


def led(lens, hot):
    image = Image.new("RGBA", (DRAWN, DRAWN))
    pixels = image.load()
    for py in range(DRAWN):
        y = (py - CENTRE) / CENTRE
        for px in range(DRAWN):
            x = (px - CENTRE) / CENTRE
            r = math.hypot(x, y)
            lit = ramp(LED_HOT, LED_HOT + 0.08, r)
            colour = tuple(h + (l - h) * lit for h, l in zip(hot, lens))
            bezel = ramp(LED_LENS - 0.02, LED_LENS + 0.02, r)
            colour = tuple(int(c + (b - c) * bezel) for c, b in zip(colour, LED_BEZEL))
            alpha = 1.0 - ramp(LED_BEZEL_OUT - 0.04, LED_BEZEL_OUT + 0.04, r)
            alpha *= 1.0 - (1.0 - LED_BEZEL_ALPHA) * bezel
            pixels[px, py] = colour + (int(255 * alpha),)
    return image


if __name__ == "__main__":
    main()
