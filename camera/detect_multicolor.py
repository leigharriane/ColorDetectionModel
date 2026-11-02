"""Live multi-colour detector: boxes every matching region in the webcam feed.

Every colour in the selected profile is searched independently across the
whole frame, so several objects (and several colours) can be boxed at once.
Each box is labelled ``COLOUR -> Category`` so the sorting decision is
visible on screen.

Usage::

    python detect_multicolor.py [--profile tuned|original] [--camera N]
                                [--min-area PIXELS]

Press ``q`` in the video window to quit.

Use ``detect_zone.py`` instead when you want a single decision for one
object held in front of the camera.
"""

from __future__ import annotations

import argparse

import cv2
import numpy as np

from color_ranges import ColorRange, get_profile
from common import (
    add_common_arguments,
    color_mask,
    frames,
    open_camera,
    put_label,
    quit_requested,
)

WINDOW_NAME = "Multi-Colour Detection"
DEFAULT_MIN_AREA = 300  # contour area in px^2 below which a blob is ignored


def draw_detections(
    frame_bgr: np.ndarray, hsv: np.ndarray, color: ColorRange, min_area: int
) -> int:
    """Box every region of ``color`` on ``frame_bgr``; return how many were drawn."""
    mask = color_mask(hsv, color)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    drawn = 0
    for contour in contours:
        if cv2.contourArea(contour) < min_area:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), color.draw_bgr, 2)
        put_label(frame_bgr, color.label, (x, max(0, y - 8)), color.draw_bgr)
        drawn += 1
    return drawn


def annotate_frame(
    frame_bgr: np.ndarray,
    colors: dict[str, ColorRange],
    min_area: int = DEFAULT_MIN_AREA,
) -> dict[str, int]:
    """Run every colour over ``frame_bgr`` in place; return detections per colour."""
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    return {
        name: draw_detections(frame_bgr, hsv, color, min_area)
        for name, color in colors.items()
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = add_common_arguments(argparse.ArgumentParser(description=__doc__.split("\n\n")[0]))
    parser.add_argument(
        "--min-area",
        type=int,
        default=DEFAULT_MIN_AREA,
        help=f"ignore blobs smaller than this many pixels (default: {DEFAULT_MIN_AREA})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    colors = get_profile(args.profile)
    cap = open_camera(args.camera)
    try:
        for frame in frames(cap):
            annotate_frame(frame, colors, args.min_area)
            cv2.imshow(WINDOW_NAME, frame)
            if quit_requested():
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
