# Usage:
# python plot_brightness_with_autolog.py frames\\auto_100ms_01_brightness.csv events\\auto_detected_v4b_filt40.csv logs\\auto_log.csv a_rel b out.png
# a_rel in ms, b scale factor (from RANSAC)
import sys, pandas as pd, numpy as np, re, matplotlib.pyplot as plt

if len(sys.argv) < 7:
    print("Usage: python plot_brightness_with_autolog.py brightness.csv events.csv autolog.csv a_rel_ms b out.png")
    sys.exit(1)

bright_f = sys.argv[1]
events_f = sys.argv[2]
autolog_f = sys.argv[3]
a_rel = float(sys.argv[4])    # ms (RANSAC)
b = float(sys.argv[5])        # scale (RANSAC)
out_png = sys.argv[6]

bdf = pd.read_csv(bright_f)
edf = pd.read_csv(events_f)
# load autolog ticks
ticks=[]
with open(autolog_f,'r',encoding='utf-8',errors='ignore') as f:
    for line in f:
        s=line.strip()
        if not s or s.lower().startswith("time"): continue
        m=re.search(r'(\d{3,})', s)
        if m: ticks.append(int(m.group(1)))
if len(ticks)==0:
    print("No autolog ticks found")
    sys.exit(1)

al_first = ticks[0]
# map autolog ticks to video time (seconds): ev_time_s = (tick - al_first - a_rel) / (b*1000)
ticks = np.array(ticks)
video_times = (ticks - al_first - a_rel) / (b * 1000.0)

plt.figure(figsize=(12,4))
plt.plot(bdf['time_s'], bdf['brightness'], label='brightness')
# plot detected events
if 'time_s' in edf.columns:
    plt.vlines(edf['time_s'], ymin=bdf['brightness'].min(), ymax=bdf['brightness'].max(), color='r', alpha=0.6, label='detected events')
else:
    print("Events file has no time_s column")
# plot autolog mapped times
plt.vlines(video_times, ymin=bdf['brightness'].min(), ymax=bdf['brightness'].max(), color='g', alpha=0.5, label='autolog (mapped)')
plt.xlim(0, min(bdf['time_s'].max(), video_times.max()+1))
plt.xlabel('time (s)')
plt.legend()
plt.tight_layout()
plt.savefig(out_png, dpi=150)
print("Saved", out_png)
