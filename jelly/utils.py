from enum import IntFlag
from math import sqrt
from random import randrange, random
from colorsys import hls_to_rgb
from pygame import Surface, Color, font, gfxdraw


class Direction(IntFlag):
    NONE = 0
    LEFT = 1
    UP = 2
    RIGHT = 4
    DOWN = 8


class InvalidData(RuntimeError):
    """Raised when the data provided by a client is not valid"""
    pass


def assert_nick(nick: str) -> None:
    """Checks if there are only printable characters in `nick`. If not, raises an exception."""
    if not nick.isprintable():
        raise InvalidData("Nickname '{}' isn't valid because is contains a "
                          "non-printable character".format(nick))


def distance(a: (int, int), b: (int, int)) -> float:
    """Calculate distance between `a` and `b`."""
    return sqrt(pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2))


# https://stackoverflow.com/a/43437435
def random_color() -> (int, int, int):
    """Returns a random color in RGB format"""
    h, s, l = random(), 0.5 + random() / 2.0, 0.4 + random() / 5.0
    return [int(256 * i) for i in hls_to_rgb(h, l, s)]


# https://stackoverflow.com/a/62480486
def draw_circle(window: Surface, xy: (int, int), radius: int, color: Color):
    """Draws a circle at `xy` point with radius `radius` and color `color` on `window` using antialiasing."""
    gfxdraw.aacircle(window, xy[0], xy[1], radius, color)
    gfxdraw.filled_circle(window, xy[0], xy[1], radius, color)


def draw_text(surface: Surface, f: font.Font, text: str, color=(0, 0, 0), **kwargs):
    image = f.render(text, True, color)
    rect = image.get_rect(**kwargs)
    surface.blit(image, rect)


def is_circle_on_screen(xy: (int, int), r: int, width_height: (int, int)):
    """Returns True, if a circle with radius `r` and center at (`x`, `y`) is
    on the screen with width `w` and height `h`. Assume each point (`i`, `j`) is on the screen
    iff 0 <= i < w and 0 <= j < h."""
    p = (0 <= xy[0] + r < width_height[0]) or (0 <= xy[0] - r < width_height[0])
    q = (0 <= xy[1] + r < width_height[1]) or (0 <= xy[1] - r < width_height[1])
    return p and q


def offset(world_xy: (int, int), screen_width_height: (int, int)):
    """
    Calculates offset so that we can draw the player in the center of the screen.

    :param world_xy: player's xy coordinates in the world (not screen)
    :param screen_width_height: width and height of the screen
    :returns: a pair of integers k & m such that world_to_screen(world_xy, (k, m))) returns the center of the screen.
    """
    return world_xy[0] - screen_width_height[0] // 2, world_xy[1] - screen_width_height[1] // 2


def world2screen(xy: (int, int), offset_xy: (int, int)):
    """
    Translates coordinates in the world to screen coordinates.

    :param xy: player's xy coordinates in the world (not screen)
    :param offset_xy: a pair of values calculated by calculate_offset() function
    :return: coordinates in terms of the screen applying the offset.
    """
    return xy[0] - offset_xy[0], xy[1] - offset_xy[1]
