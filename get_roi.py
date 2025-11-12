# Usage: python get_roi.py path\to\video.mp4
# Click two points on the frame image to get x,y,w,h for ROI.
import cv2, sys

if len(sys.argv) < 2:
    print("Usage: python get_roi.py path\\to\\video.mp4")
    sys.exit(1)

video = sys.argv[1]
cap = cv2.VideoCapture(video)
ret, frame = cap.read()
if not ret:
    print("Cannot read frame from", video); sys.exit(1)

frame_small = frame.copy()
# show frame; click two corners
pts = []
def on_mouse(e,x,y,flags,param):
    global pts, frame_small
    if e==cv2.EVENT_LBUTTONDOWN:
        pts.append((x,y))
        cv2.circle(frame_small,(x,y),5,(0,255,0),-1)
        cv2.imshow("frame", frame_small)

cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("frame", on_mouse)
cv2.imshow("frame", frame_small)
print("Click top-left then bottom-right of ROI (press ESC to finish).")
while True:
    k = cv2.waitKey(0) & 0xFF
    if k==27:
        break
cv2.destroyAllWindows()
cap.release()

if len(pts) < 2:
    print("You did not click two points. Exiting.")
    sys.exit(1)

(x1,y1) = pts[0]; (x2,y2) = pts[1]
x = min(x1,x2); y = min(y1,y2); w = abs(x2-x1); h = abs(y2-y1)
print("ROI:", x, y, w, h)
print("Use --roi {} {} {} {}".format(x,y,w,h))
