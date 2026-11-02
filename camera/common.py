"""Helpers shared by the camera scripts: CLI flags, camera setup, masking, text."""

from __future__ import annotations

import argparse
from collections.abc import Iterator

import cv2
import numpy as np

from color_ranges import DEFAULT_PROFILE, PROFILES, ColorRange

QUIT_KEY = ord("q")

# 5x5 structuring element used for every morphological clean-up.
KERNEL = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))


def add_common_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Add the ``--camera`` and ``--profile`` flags every script accepts."""
    parser.add_argument(
        "--camera", type=int, default=0, help="OpenCV camera index (default: 0)"
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default=DEFAULT_PROFILE,
        help=f"HSV threshold profile from color_ranges.py (default: {DEFAULT_PROFILE})",
    )
    return parser


def open_camera(index: int) -> cv2.VideoCapture:
    """Open camera ``index`` or raise a clear error instead of reading blank frames."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera {index}.")
    return cap


def frames(cap: cv2.VideoCapture) -> Iterator[np.ndarray]:
    """Yield BGR frames until the camera stops delivering them."""
    while True:
        ok, frame = cap.read()
        if not ok:
            return
        yield frame


def color_mask(hsv: np.ndarray, color: ColorRange, clean: bool = True) -> np.ndarray:
    """Binary mask of ``hsv`` pixels inside ``color``'s window.

    With ``clean`` the mask is opened (speckle removed) and then dilated
    (surviving blobs re-grown) so contours come out as solid regions.
    """
    mask = cv2.inRange(hsv, color.lower_np, color.upper_np)
    if clean:
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL)
        mask = cv2.dilate(mask, KERNEL)
    return mask


def put_label(
    frame: np.ndarray,
    text: str,
    origin: tuple[int, int],
    bgr: tuple[int, int, int],
    scale: float = 0.8,
) -> None:
    """Draw anti-aliased ``text`` with its bottom-left corner at ``origin``."""
    cv2.putText(frame, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, bgr, 2, cv2.LINE_AA)


def quit_requested(delay_ms: int = 1) -> bool:
    """Pump the GUI event loop and report whether ``q`` was pressed."""
    return (cv2.waitKey(delay_ms) & 0xFF) == QUIT_KEY
