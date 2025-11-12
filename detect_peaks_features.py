# Usage:
# python detect_peaks_features.py C:\keystroke_project\KeyStroke-Project\brightness\out.csv --out C:\keystroke_project\KeyStroke-Project\features\file_features.csv --events_out C:\keystroke_project\KeyStroke-Project\events\events.csv

import argparse, pandas as pd, numpy as np, csv, os
from scipy.signal import find_peaks, medfilt

p = argparse.ArgumentParser()
p.add_argument('brightness_csv')
p.add_argument('--out', default='features.csv')
p.add_argument('--events_out', default=None)
p.add_argument('--min_interval_ms', type=float, default=8.0)
p.add_argument('--smooth', type=int, default=3)
args = p.parse_args()

df = pd.read_csv(args.brightness_csv)
times = df['time_s'].values; br = df['brightness'].values
if args.smooth>1:
    from scipy.signal import medfilt
    b = medfilt(br, kernel_size=args.smooth if args.smooth%2==1 else args.smooth+1)
else:
    b = br
fps = 1.0 / (times[1]-times[0])
distance = max(1, int((args.min_interval_ms/1000.0)*fps))
peaks, props = find_peaks(b, distance=distance, height=np.mean(b)+0.25*np.std(b))
event_times = times[peaks]
if args.events_out:
    pd.DataFrame({'time_s': event_times}).to_csv(args.events_out, index=False)

if len(event_times) < 2:
    # write empty feature file
    with open(args.out,'w',newline='') as f:
        writer = csv.writer(f); writer.writerow(['n_events','mu_iki_s','std_iki_s','cv_iki']); writer.writerow([0,0,0,0])
    print("Not enough events detected; wrote", args.out)
    raise SystemExit(0)

ikis = np.diff(event_times)
mu = float(np.mean(ikis)); sigma = float(np.std(ikis, ddof=1))
cv = sigma/mu if mu>0 else float('nan')
feats = {'n_events': int(len(event_times)), 'mu_iki_s': mu, 'std_iki_s': sigma, 'cv_iki': cv}
with open(args.out,'w',newline='') as f:
    writer = csv.writer(f); writer.writerow(list(feats.keys())); writer.writerow([feats[k] for k in feats.keys()])

ikis_path = os.path.splitext(args.out)[0] + '_ikis.csv'
with open(ikis_path,'w',newline='') as f:
    w = csv.writer(f); w.writerow(['iki_s']); [w.writerow([v]) for v in ikis]
print("Saved features:", args.out, "and ikis:", ikis_path)
