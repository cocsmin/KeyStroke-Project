import sys, cv2
path = r"raw_videos\auto_20ms_laptopA_run01.mp4"
cap = cv2.VideoCapture(path)
print("cap.isOpened():", cap.isOpened())
print("FRAME_COUNT:", cap.get(cv2.CAP_PROP_FRAME_COUNT))
print("FPS:", cap.get(cv2.CAP_PROP_FPS))
cap.release()