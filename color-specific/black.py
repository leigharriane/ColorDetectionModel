import cv2
import numpy as np

def nothing(x):
    pass

cap = cv2.VideoCapture(0)
cv2.namedWindow("Trackbars")

cv2.createTrackbar("L-H", "Trackbars", 0, 180, nothing)
cv2.createTrackbar("L-S", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("L-V", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("U-H", "Trackbars", 180, 180, nothing)
cv2.createTrackbar("U-S", "Trackbars", 81, 255, nothing)
cv2.createTrackbar("U-V", "Trackbars", 40, 255, nothing)

while True:
    _, frame = cap.read()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Get values from trackbars
    l_h = cv2.getTrackbarPos("L-H", "Trackbars")
    l_s = cv2.getTrackbarPos("L-S", "Trackbars")
    l_v = cv2.getTrackbarPos("L-V", "Trackbars")
    u_h = cv2.getTrackbarPos("U-H", "Trackbars")
    u_s = cv2.getTrackbarPos("U-S", "Trackbars")
    u_v = cv2.getTrackbarPos("U-V", "Trackbars")

    lower_bound = np.array([l_h, l_s, l_v])
    upper_bound = np.array([u_h, u_s, u_v])
    black_mask = cv2.inRange(hsv, lower_bound, upper_bound) 

    kernel = np.ones((5, 5), "uint8") 
    
    black_mask = cv2.dilate(black_mask, kernel) 
    res_black = cv2.bitwise_and(frame, frame, 
							  mask = black_mask)
    
    # Create mask
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    result = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)
    cv2.imshow("Result", result)
    
    
    contours, hierarchy = cv2.findContours(black_mask, 
										cv2.RETR_TREE, 
										cv2.CHAIN_APPROX_SIMPLE) 
    for pic, contour in enumerate(contours): 
      area = cv2.contourArea(contour) 
      if(area > 300): 
        x, y, w, h = cv2.boundingRect(contour) 
        frame = cv2.rectangle(frame, (x, y), 
									(x + w, y + h), 
									(0, 0, 0), 2) 
        cv2.putText(frame, "garbage", (x, y), 
						cv2.FONT_HERSHEY_SIMPLEX, 
						1.0, (0, 0, 0)) 
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    

    cv2.imshow("Multiple Color Detection in Real-TIme", frame) 
    if cv2.waitKey(10) & 0xFF == ord('q'): 
      cap.release() 
      cv2.destroyAllWindows()
      break

cap.release()
cv2.destroyAllWindows()