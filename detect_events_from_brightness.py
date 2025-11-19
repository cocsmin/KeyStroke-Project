# usage:
# python detect_events_from_brightness.py frames\\auto_100ms_01_brightness.csv events\\auto_detected.csv --min_interval_ms 33 --height_factor 0.30 --smooth_win 3

import sys, pandas as pd, numpy as np
from scipy.signal import savgol_filter, find_peaks
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('brightness_csv')
parser.add_argument('out_events_csv')
parser.add_argument('--min_interval_ms', type=int, default=33)
parser.add_argument('--height_factor', type=float, default=0.30)
parser.add_argument('--smooth_win', type=int, default=3)
parser.add_argument('--fps', type=float, default=30.0)
args = parser.parse_args()

b = pd.read_csv(args.brightness_csv)
time_s = b['time_s'].values
brightness = b['brightness'].values

# smoothing (savgol)
win = args.smooth_win if args.smooth_win%2==1 else args.smooth_win+1
if win < 3: win = 3
if len(brightness) >= win:
    try:
        sg = savgol_filter(brightness, win, 2)
    except:
        sg = brightness
else:
    sg = brightness

# dynamic threshold
mu = np.mean(sg)
sd = np.std(sg)
height = mu + args.height_factor * sd

# find peaks (peaks in brightness)
min_samples = max(1, int(np.round(args.min_interval_ms * args.fps / 1000.0)))
peaks, props = find_peaks(sg, height=height, distance=min_samples)
events = pd.DataFrame({'frame': peaks, 'time_s': time_s[peaks]})
events.to_csv(args.out_events_csv, index=False)
print("Detected", len(events), "events ->", args.out_events_csv)
