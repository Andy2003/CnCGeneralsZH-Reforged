"""The picture a China mine is drawn with: a round steel pressure mine seen from above, sunk in a ring
of disturbed earth.  The game lays it flat on the ground at each of a mine field's eight mine bones
(ParticleSystemReforged.ini, MineFX and MineFXPurple), so it is shaded here once, lit from the top
left, and the soil ring fades out into whatever ground it lands on.

The arming light over each mine is an LED seen from above: a hard, nearly white core a fifth of the
picture across inside a small glow in the light's colour, red for the standard and cluster mines and
a cold blue-violet for the EMP mines.  It is drawn additively, so black is nothing.

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
LED_CORE = 0.18			# radius of the hard core, as a share of the half width
LED_GLOW = 0.17			# the glow falls off as exp(-(r - core) / this)
LED_GLOW_PEAK = 0.7		# the glow's strength just outside the core, against the core's 1
LEDS = (("Red", (255, 18, 8), (255, 190, 170)), ("Blue", (80, 100, 255), (200, 215, 255)))
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


def led(glow, core):
    image = Image.new("RGBA", (DRAWN, DRAWN))
    pixels = image.load()
    for py in range(DRAWN):
        y = (py - CENTRE) / CENTRE
        for px in range(DRAWN):
            x = (px - CENTRE) / CENTRE
            r = math.hypot(x, y)
            if r < LED_CORE:
                colour = core
            else:
                strength = LED_GLOW_PEAK * math.exp(-(r - LED_CORE) / LED_GLOW) * (1.0 - ramp(0.8, 1.0, r))
                colour = tuple(int(c * strength) for c in glow)
            pixels[px, py] = colour + (max(colour),)
    return image


if __name__ == "__main__":
    main()
