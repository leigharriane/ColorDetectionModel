import numpy as np
import cv2

# Capturing video through webcam
webcam = cv2.VideoCapture(0)

# ROI (detection box) settings
ROI_W, ROI_H = 200, 200   # box size
MIN_COVERAGE = 0.15       # % of ROI pixels required to count as detected (tweak)
kernel = np.ones((5, 5), "uint8")  # define once (more efficient)

# Color ranges (HSV)
green_lower = np.array([25, 56, 75], np.uint8)
green_upper = np.array([102, 255, 255], np.uint8)

blue_lower = np.array([93, 134, 7], np.uint8)
blue_upper = np.array([144, 255, 255], np.uint8)

black_lower = np.array([0, 0, 0], np.uint8)
black_upper = np.array([180, 255, 40], np.uint8)

brown_lower = np.array([7, 60, 30], np.uint8)
brown_upper = np.array([70, 255, 255], np.uint8)

grey_lower = np.array([0, 0, 0], np.uint8)
grey_upper = np.array([180, 50, 200], np.uint8)

while True:
    # Reading the video from the webcam in image frames
    ok, imageFrame = webcam.read()
    if not ok:
        break

    h, w = imageFrame.shape[:2]

    # ROI centered (move these if you want the box somewhere else)
    x1 = (w - ROI_W) // 2
    y1 = (h - ROI_H) // 2
    x2 = x1 + ROI_W
    y2 = y1 + ROI_H

    # Crop ROI and convert ONLY ROI to HSV (faster + focused)
    roi_bgr = imageFrame[y1:y2, x1:x2]
    hsvROI = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

    # --- Create masks (ROI only) ---
    green_mask = cv2.inRange(hsvROI, green_lower, green_upper)
    blue_mask  = cv2.inRange(hsvROI, blue_lower, blue_upper)
    black_mask = cv2.inRange(hsvROI, black_lower, black_upper)
    brown_mask = cv2.inRange(hsvROI, brown_lower, brown_upper)
    grey_mask  = cv2.inRange(hsvROI, grey_lower, grey_upper)

    # --- Dilation (same logic you used) ---
    green_mask = cv2.dilate(green_mask, kernel)
    blue_mask  = cv2.dilate(blue_mask, kernel)
    black_mask = cv2.dilate(black_mask, kernel)
    brown_mask = cv2.dilate(brown_mask, kernel)
    grey_mask  = cv2.dilate(grey_mask, kernel)

    # --- Decide ONE color at a time based on coverage in the ROI ---
    roi_area = ROI_W * ROI_H
    cov_green = cv2.countNonZero(green_mask) / roi_area
    cov_blue  = cv2.countNonZero(blue_mask)  / roi_area
    cov_black = cv2.countNonZero(black_mask) / roi_area
    cov_brown = cv2.countNonZero(brown_mask) / roi_area
    cov_grey  = cv2.countNonZero(grey_mask)  / roi_area

    coverages = [
        ("green", cov_green, green_mask, (0, 255, 0), "Recycle"),
        ("blue",  cov_blue,  blue_mask,  (255, 0, 0), "Recycle"),
        ("black", cov_black, black_mask, (0, 0, 0),   "garbage"),
        ("brown", cov_brown, brown_mask, (35, 86, 50),"garbage"),
        ("grey",  cov_grey,  grey_mask,  (128, 128, 128), "garbage"),
    ]

    best_name, best_cov, best_mask, best_color, best_label = max(coverages, key=lambda x: x[1])

    # Draw the ROI box on the main frame
    cv2.rectangle(imageFrame, (x1, y1), (x2, y2), (255, 255, 255), 2)

    # If it's confident enough, find contours inside ROI and draw ONE detection
    if best_cov >= MIN_COVERAGE:
        contours, _ = cv2.findContours(best_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Choose largest contour (one color / one object focus)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)

            if area > 300:  # same threshold idea you used
                rx, ry, rw, rh = cv2.boundingRect(largest)

                # Convert ROI coords -> full-frame coords
                fx, fy = x1 + rx, y1 + ry

                # Draw bounding box + label on full frame
                cv2.rectangle(imageFrame, (fx, fy), (fx + rw, fy + rh), best_color, 2)
                cv2.putText(imageFrame,
                            f"{best_name.upper()} -> {best_label} ({best_cov*100:.1f}%)",
                            (fx, max(0, fy - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, best_color, 2)

    else:
        cv2.putText(imageFrame,
                    f"Unknown ({best_cov*100:.1f}%)",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    # Show output
    cv2.imshow("Single-Zone Color Detection", imageFrame)

    # Program Termination
    if cv2.waitKey(10) & 0xFF == ord('q'):
        webcam.release()
        cv2.destroyAllWindows()
        break
