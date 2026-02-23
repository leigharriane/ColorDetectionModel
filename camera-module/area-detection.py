import cv2
import numpy as np

# ---------- Color thresholds (HSV) ----------
COLOR_DEFS = {
    "green":  {"lower": (25, 56, 75),  "upper": (102, 255, 255), "label": "Recycle"},
    "blue":   {"lower": (93, 134, 7),  "upper": (144, 255, 255), "label": "Recycle"},
    "black":  {"lower": (0, 0, 0),     "upper": (180, 255, 40),  "label": "Garbage"},
    "brown":  {"lower": (7, 60, 30),   "upper": (70, 255, 255),  "label": "Garbage"},
    "grey":   {"lower": (0, 0, 0),     "upper": (180, 50, 200),  "label": "Garbage"},
}

# Convert once
for c in COLOR_DEFS.values():
    c["lower"] = np.array(c["lower"], dtype=np.uint8)
    c["upper"] = np.array(c["upper"], dtype=np.uint8)

KERNEL = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

# ---------- Detection zone (ROI) ----------
# Box in the center by default. You can change ROI_W/ROI_H or move it.
ROI_W, ROI_H = 200, 200

# How confident it must be (percentage of ROI pixels matching a color)
MIN_COVERAGE = 0.15  # 15%


def best_color_in_roi(hsv_roi):
    """Return (color_name, coverage) for the single best-matching color in ROI."""
    roi_area = hsv_roi.shape[0] * hsv_roi.shape[1]

    best_name = None
    best_cov = 0.0

    for name, defs in COLOR_DEFS.items():
        mask = cv2.inRange(hsv_roi, defs["lower"], defs["upper"])

        # Clean noise a bit (optional but helps)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL, iterations=1)

        coverage = cv2.countNonZero(mask) / float(roi_area)

        if coverage > best_cov:
            best_cov = coverage
            best_name = name

    if best_cov < MIN_COVERAGE:
        return None, best_cov

    return best_name, best_cov


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            h, w = frame.shape[:2]

            # ROI centered (edit these to move the box wherever you want)
            x1 = (w - ROI_W) // 2
            y1 = (h - ROI_H) // 2
            x2 = x1 + ROI_W
            y2 = y1 + ROI_H

            roi_bgr = frame[y1:y2, x1:x2]
            hsv_roi = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

            color_name, coverage = best_color_in_roi(hsv_roi)

            # Draw ROI box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)

            # Display result (one color at a time)
            if color_name is None:
                text = f"Color: Unknown ({coverage*100:.1f}%)"
            else:
                label = COLOR_DEFS[color_name]["label"]
                text = f"Color: {color_name.upper()} -> {label} ({coverage*100:.1f}%)"

            cv2.putText(frame, text, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.imshow("Single-Zone Color Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
