"""Interactive HSV range finder for calibrating ``color_ranges.py``.

Six trackbars set the lower and upper hue, saturation and value bounds.
Three windows update live: the camera frame with boxes around blobs that
match the current range, the binary mask, and the frame with everything
outside the mask blacked out.  Start from an existing colour with
``--preset`` to fine-tune it, or from the full range to explore.

Press ``p`` to print the current bounds to the terminal and ``q`` to quit
(the bounds are printed on exit as well).  Copy the printed numbers into
the matching ``ColorRange`` in ``color_ranges.py``.

Usage::

    python hsv_tuner.py [--preset black] [--profile tuned|original] [--camera N]
"""

from __future__ import annotations

import argparse

import cv2
import numpy as np

from color_ranges import PROFILES, get_profile
from common import KERNEL, add_common_arguments, frames, open_camera, put_label

CONTROLS_WINDOW = "HSV Tuner"
FULL_RANGE = ((0, 0, 0), (179, 255, 255))
MIN_AREA = 300  # px^2; smaller matching blobs are not boxed in the preview
BOX_BGR = (0, 255, 255)  # yellow stands out against most targets

# (trackbar name, maximum).  Order matches (lower H, S, V, upper H, S, V).
TRACKBARS = (
    ("L-H", 179),
    ("L-S", 255),
    ("L-V", 255),
    ("U-H", 179),
    ("U-S", 255),
    ("U-V", 255),
)

Bounds = tuple[np.ndarray, np.ndarray]


def _noop(_: int) -> None:
    """Trackbar callback; values are polled each frame instead."""


def create_trackbars(lower: tuple[int, int, int], upper: tuple[int, int, int]) -> None:
    cv2.namedWindow(CONTROLS_WINDOW)
    for (name, maximum), value in zip(TRACKBARS, (*lower, *upper)):
        cv2.createTrackbar(name, CONTROLS_WINDOW, min(value, maximum), maximum, _noop)


def read_bounds() -> Bounds:
    values = [cv2.getTrackbarPos(name, CONTROLS_WINDOW) for name, _ in TRACKBARS]
    return np.array(values[:3], dtype=np.uint8), np.array(values[3:], dtype=np.uint8)


def format_bounds(lower: np.ndarray, upper: np.ndarray) -> str:
    """Render bounds as a line that can be pasted into ``color_ranges.py``."""
    return f"lower={tuple(int(v) for v in lower)}, upper={tuple(int(v) for v in upper)}"


def draw_matches(frame_bgr: np.ndarray, mask: np.ndarray) -> None:
    """Box every blob of ``mask`` larger than ``MIN_AREA`` on ``frame_bgr``."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        if cv2.contourArea(contour) < MIN_AREA:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), BOX_BGR, 2)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = add_common_arguments(argparse.ArgumentParser(description=__doc__.split("\n\n")[0]))
    presets = sorted({name for profile in PROFILES.values() for name in profile})
    parser.add_argument(
        "--preset",
        choices=presets,
        help="start the trackbars at this colour's current range instead of the full range",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.preset:
        color = get_profile(args.profile)[args.preset]
        lower, upper = color.lower, color.upper
    else:
        lower, upper = FULL_RANGE

    cap = open_camera(args.camera)
    create_trackbars(lower, upper)
    try:
        for frame in frames(cap):
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lo, hi = read_bounds()

            mask = cv2.dilate(cv2.inRange(hsv, lo, hi), KERNEL)
            result = cv2.bitwise_and(frame, frame, mask=mask)

            preview = frame.copy()
            draw_matches(preview, mask)
            put_label(preview, format_bounds(lo, hi), (10, 25), BOX_BGR, scale=0.6)

            cv2.imshow("Frame", preview)
            cv2.imshow("Mask", mask)
            cv2.imshow("Result", result)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("p"):
                print(format_bounds(lo, hi))
            elif key == ord("q"):
                break
    finally:
        lo, hi = read_bounds()
        print("Final range:", format_bounds(lo, hi))
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
