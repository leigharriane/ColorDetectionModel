"""HSV colour thresholds shared by every camera script.

OpenCV's HSV encoding is used throughout: hue 0-179, saturation 0-255,
value 0-255.  A ``ColorRange`` bundles the lower/upper HSV bounds for one
colour with the waste category it maps to and the BGR colour used when
drawing it on screen.

Two threshold *profiles* are kept so earlier results stay reproducible:

``original``
    The first hand-tuned set, used by the earliest detection scripts.
``tuned`` (default)
    A later re-tune of blue, black and grey.  Blue was widened to any hue
    from 86 upward with no saturation or value floor, black was raised to
    V <= 80 (S <= 80), and grey was given a value floor of 83 so it stops
    overlapping black.  Be aware that this blue window also matches most
    whites and light greys, so multi-colour mode will box neutral objects
    as "blue"; tighten the saturation floor if that becomes a problem.

To find new values interactively run ``hsv_tuner.py`` and paste the printed
bounds here.  Nothing else in the project hard-codes thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Waste categories that a detected colour is mapped to.
RECYCLE = "Recycle"
GARBAGE = "Garbage"

HSV = tuple[int, int, int]
BGR = tuple[int, int, int]


@dataclass
class ColorRange:
    """One detectable colour: its HSV window, category and on-screen colour."""

    name: str
    lower: HSV
    upper: HSV
    category: str
    draw_bgr: BGR
    # Bounds pre-converted for cv2.inRange (built once, not once per frame).
    lower_np: np.ndarray = field(init=False, repr=False)
    upper_np: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.lower_np = np.array(self.lower, dtype=np.uint8)
        self.upper_np = np.array(self.upper, dtype=np.uint8)

    @property
    def label(self) -> str:
        """Text drawn next to a detection, e.g. ``GREEN -> Recycle``."""
        return f"{self.name.upper()} -> {self.category}"


# BGR colours used to draw boxes and labels for each detected colour.
_DRAW: dict[str, BGR] = {
    "green": (0, 255, 0),
    "blue": (255, 0, 0),
    "black": (0, 0, 0),
    "brown": (35, 86, 50),
    "grey": (128, 128, 128),
}


def _profile(*ranges: ColorRange) -> dict[str, ColorRange]:
    return {r.name: r for r in ranges}


PROFILES: dict[str, dict[str, ColorRange]] = {
    "original": _profile(
        ColorRange("green", (25, 56, 75), (102, 255, 255), RECYCLE, _DRAW["green"]),
        ColorRange("blue", (93, 134, 7), (144, 255, 255), RECYCLE, _DRAW["blue"]),
        ColorRange("black", (0, 0, 0), (180, 255, 40), GARBAGE, _DRAW["black"]),
        ColorRange("brown", (7, 60, 30), (70, 255, 255), GARBAGE, _DRAW["brown"]),
        ColorRange("grey", (0, 0, 0), (180, 50, 200), GARBAGE, _DRAW["grey"]),
    ),
    "tuned": _profile(
        ColorRange("green", (25, 56, 75), (102, 255, 255), RECYCLE, _DRAW["green"]),
        ColorRange("blue", (86, 0, 0), (179, 255, 255), RECYCLE, _DRAW["blue"]),
        ColorRange("black", (0, 0, 0), (179, 80, 80), GARBAGE, _DRAW["black"]),
        ColorRange("brown", (7, 60, 30), (70, 255, 255), GARBAGE, _DRAW["brown"]),
        ColorRange("grey", (0, 0, 83), (179, 50, 180), GARBAGE, _DRAW["grey"]),
    ),
}

DEFAULT_PROFILE = "tuned"


def get_profile(name: str = DEFAULT_PROFILE) -> dict[str, ColorRange]:
    """Return the colour table for ``name`` (see ``PROFILES``)."""
    try:
        return PROFILES[name]
    except KeyError:
        raise ValueError(
            f"unknown profile {name!r}; choose from {sorted(PROFILES)}"
        ) from None
