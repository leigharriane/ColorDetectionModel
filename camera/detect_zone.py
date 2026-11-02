"""Single-zone detector: decides ONE colour for whatever sits inside a centre box.

A fixed region of interest (ROI) is drawn in the middle of the frame.  For
each colour in the profile the script measures what fraction of the ROI's
pixels fall inside that colour's HSV window (its *coverage*).  The colour
with the highest coverage wins, provided it clears ``--min-coverage``;
otherwise the result is "Unknown".  When a colour wins, the largest blob of
it inside the ROI is also boxed on the full frame.

This is the mode intended for a sorting station: hold an item in the box
and read one answer.

Usage::

    python detect_zone.py [--profile tuned|original] [--camera N]
                          [--roi WIDTH HEIGHT] [--min-coverage 0.15]
                          [--min-area 300]

Press ``q`` in the video window to quit.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

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

WINDOW_NAME = "Single-Zone Colour Detection"
DEFAULT_ROI = (200, 200)  # width, height in pixels
DEFAULT_MIN_COVERAGE = 0.15  # 15 % of ROI pixels must match to count
DEFAULT_MIN_AREA = 300  # px^2; smaller winning blobs are not boxed

WHITE = (255, 255, 255)

Rect = tuple[int, int, int, int]


@dataclass
class ZoneResult:
    """Outcome for one frame: winning colour (or None), its coverage, and a box."""

    color: ColorRange | None
    coverage: float
    box: Rect | None  # x, y, w, h in full-frame coordinates


def centered_roi(frame_shape: tuple[int, ...], roi_w: int, roi_h: int) -> Rect:
    """Return (x1, y1, x2, y2) of a ``roi_w`` x ``roi_h`` box centred in the frame."""
    frame_h, frame_w = frame_shape[:2]
    roi_w, roi_h = min(roi_w, frame_w), min(roi_h, frame_h)
    x1 = (frame_w - roi_w) // 2
    y1 = (frame_h - roi_h) // 2
    return x1, y1, x1 + roi_w, y1 + roi_h


def classify_roi(
    hsv_roi: np.ndarray,
    colors: dict[str, ColorRange],
    min_coverage: float = DEFAULT_MIN_COVERAGE,
    min_area: int = DEFAULT_MIN_AREA,
) -> ZoneResult:
    """Pick the colour covering most of ``hsv_roi``; box is in ROI coordinates."""
    roi_area = hsv_roi.shape[0] * hsv_roi.shape[1]

    best: ColorRange | None = None
    best_coverage = 0.0
    best_mask: np.ndarray | None = None
    for color in colors.values():
        mask = color_mask(hsv_roi, color)
        coverage = cv2.countNonZero(mask) / roi_area
        if coverage > best_coverage:
            best, best_coverage, best_mask = color, coverage, mask

    if best is None or best_mask is None or best_coverage < min_coverage:
        return ZoneResult(None, best_coverage, None)

    box: Rect | None = None
    contours, _ = cv2.findContours(best_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) >= min_area:
            box = cv2.boundingRect(largest)
    return ZoneResult(best, best_coverage, box)


def annotate_frame(
    frame_bgr: np.ndarray,
    colors: dict[str, ColorRange],
    roi_size: tuple[int, int] = DEFAULT_ROI,
    min_coverage: float = DEFAULT_MIN_COVERAGE,
    min_area: int = DEFAULT_MIN_AREA,
) -> ZoneResult:
    """Classify the centre ROI of ``frame_bgr`` and draw the ROI, result and box."""
    x1, y1, x2, y2 = centered_roi(frame_bgr.shape, *roi_size)
    hsv_roi = cv2.cvtColor(frame_bgr[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
    result = classify_roi(hsv_roi, colors, min_coverage, min_area)

    cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), WHITE, 2)

    if result.color is None:
        banner = f"Unknown ({result.coverage * 100:.1f}%)"
    else:
        banner = f"{result.color.label} ({result.coverage * 100:.1f}%)"
        if result.box is not None:
            bx, by, bw, bh = result.box
            fx, fy = x1 + bx, y1 + by  # ROI -> full-frame coordinates
            cv2.rectangle(frame_bgr, (fx, fy), (fx + bw, fy + bh), result.color.draw_bgr, 2)
            result.box = (fx, fy, bw, bh)

    put_label(frame_bgr, banner, (20, 40), WHITE, scale=0.9)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = add_common_arguments(argparse.ArgumentParser(description=__doc__.split("\n\n")[0]))
    parser.add_argument(
        "--roi",
        type=int,
        nargs=2,
        metavar=("WIDTH", "HEIGHT"),
        default=DEFAULT_ROI,
        help=f"size of the centre detection box in pixels (default: {DEFAULT_ROI[0]} {DEFAULT_ROI[1]})",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=DEFAULT_MIN_COVERAGE,
        help=f"fraction of ROI pixels a colour must cover to be reported (default: {DEFAULT_MIN_COVERAGE})",
    )
    parser.add_argument(
        "--min-area",
        type=int,
        default=DEFAULT_MIN_AREA,
        help=f"only box the winning blob if it is at least this many pixels (default: {DEFAULT_MIN_AREA})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    colors = get_profile(args.profile)
    cap = open_camera(args.camera)
    try:
        for frame in frames(cap):
            annotate_frame(frame, colors, tuple(args.roi), args.min_coverage, args.min_area)
            cv2.imshow(WINDOW_NAME, frame)
            if quit_requested():
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
