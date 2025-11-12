# Usage:
# python ff_frames_to_brightness.py raw_videos\yourvideo.mp4 frames\yourvideo_frames brightness\yourvideo_brightness.csv

import subprocess, json, sys, os, cv2, numpy as np, csv

if len(sys.argv) < 4:
    print("Usage: python ff_frames_to_brightness.py input.mp4 frames_dir out_brightness.csv")
    sys.exit(1)

input_mp4 = sys.argv[1]
frames_dir = sys.argv[2]
out_csv = sys.argv[3]

os.makedirs(frames_dir, exist_ok=True)
os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)

print("1) Running ffprobe to get frame timestamps...")
cmd = ['ffprobe','-v','error','-select_streams','v','-show_frames','-print_format','json', input_mp4]
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if proc.returncode != 0:
    print("ffprobe failed:", proc.stderr[:500])
    sys.exit(1)

j = json.loads(proc.stdout)
frames = j.get('frames', [])
if not frames:
    print("No frames info from ffprobe. Aborting.")
    sys.exit(1)

times = []
for f in frames:
    t = f.get('pkt_pts_time')
    if t is None:
        t = f.get('best_effort_timestamp_time')
    # fallback
    if t is None:
        t = f.get('pts_time')
    if t is None:
        times.append(None)
    else:
        times.append(float(t))

print(f"ffprobe found {len(times)} frames.")

print("2) Extracting frames with ffmpeg (this may take some time)...")
# frames will be named frame_000001.png ... in order
ff_out_pattern = os.path.join(frames_dir, "frame_%06d.png")
cmd2 = ['ffmpeg','-y','-i', input_mp4, '-vsync','0', ff_out_pattern]
proc2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if proc2.returncode != 0:
    print("ffmpeg extraction failed; stderr (first 500 chars):", proc2.stderr[:500])
    # still try to continue if files exist
else:
    print("Frames extraction finished.")

# Now iterate and compute brightness using cv2
print("3) Computing brightness per frame...")
rows = []
missing = 0
for i, t in enumerate(times):
    fname = os.path.join(frames_dir, f"frame_{i+1:06d}.png")
    if not os.path.exists(fname):
        missing += 1
        # skip but keep placeholder
        continue
    img = cv2.imread(fname)
    if img is None:
        missing += 1
        continue
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    br = float(np.mean(gray))
    rows.append((i, times[i] if times[i] is not None else (i*1.0), br))

print(f"Processed {len(rows)} frames, missing {missing} frames (if >0 check ffmpeg output).")
print("4) Saving CSV:", out_csv)
with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['frame','time_s','brightness'])
    for r in rows:
        writer.writerow([r[0], r[1], r[2]])

print("Done.")
