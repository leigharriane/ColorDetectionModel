import cv2
import numpy as np

# ---------- Config (defined once) ----------
COLOR_DEFS = {
    "green": {
        "lower": (25, 56, 75),
        "upper": (102, 255, 255),
        "box_color": (255, 0, 0),
        "label": "Recycle",
    },
    "blue": {
        "lower": (93, 134, 7),
        "upper": (144, 255, 255),
        "box_color": (255, 0, 0),
        "label": "Recycle",
    },
    "black": {
        "lower": (0, 0, 0),
        "upper": (180, 255, 40),
        "box_color": (0, 0, 0),
        "label": "Garbage",
    },
    "brown": {
        "lower": (7, 60, 30),
        "upper": (70, 255, 255),
        "box_color": (0, 0, 0),
        "label": "Garbage",
    },
    "grey": {
        "lower": (0, 0, 0),
        "upper": (180, 50, 200),
        "box_color": (0, 0, 0),
        "label": "Garbage",
    },
}

# Convert tuples -> numpy arrays once (faster than doing it per frame)
for c in COLOR_DEFS.values():
    c["lower"] = np.array(c["lower"], dtype=np.uint8)
    c["upper"] = np.array(c["upper"], dtype=np.uint8)

KERNEL = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

MIN_AREA = 300
WINDOW_NAME = "Multiple Color Detection in Real-Time"


def draw_detections(frame_bgr, hsv_frame, color_def):
    """Create mask, clean it up, find contours, draw boxes/labels."""
    mask = cv2.inRange(hsv_frame, color_def["lower"], color_def["upper"])

    # Usually better than pure dilate: removes noise then grows remaining blobs
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL, iterations=1)
    mask = cv2.dilate(mask, KERNEL, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        if cv2.contourArea(cnt) < MIN_AREA:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), color_def["box_color"], 2)
        cv2.putText(
            frame_bgr,
            color_def["label"],
            (x, max(0, y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            color_def["box_color"],
            2,
            cv2.LINE_AA,
        )


def main():
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        raise RuntimeError("Could not open webcam.")

    try:
        while True:
            ok, frame = webcam.read()
            if not ok:
                break

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Run detection for each configured color
            for _, defs in COLOR_DEFS.items():
                draw_detections(frame, hsv, defs)

            cv2.imshow(WINDOW_NAME, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        webcam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()