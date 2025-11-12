# Usage:
# python extract_brightness.py C:\keystroke_project\KeyStroke-Project\raw_videos\video.mp4 --roi X Y W H --out C:\keystroke_project\KeyStroke-Project\brightness\out.csv

import cv2, argparse, csv, numpy as np

p = argparse.ArgumentParser()
p.add_argument('video')
p.add_argument('--roi', nargs=4, type=int, default=None)
p.add_argument('--out', default='brightness.csv')
args = p.parse_args()

cap = cv2.VideoCapture(args.video)
if not cap.isOpened():
    raise SystemExit("Cannot open video: "+args.video)
fps = cap.get(cv2.CAP_PROP_FPS) or 240.0
rows = []
idx = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    if args.roi:
        x,y,w,h = args.roi
        frame = frame[y:y+h, x:x+w]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    br = float(np.mean(gray))
    t = idx / fps
    rows.append((idx, t, br))
    idx += 1
cap.release()
with open(args.out, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['frame','time_s','brightness'])
    writer.writerows(rows)
print("Saved", args.out, "frames:", idx, "fps:", fps)
