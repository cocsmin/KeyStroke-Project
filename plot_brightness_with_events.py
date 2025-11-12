# plot_brightness_with_events.py  (robust version)
# Usage:
# python plot_brightness_with_events.py brightness.csv events.csv [autolog.csv] out.png

import sys, os, re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def read_autolog_ticks(path):
    # robust: extract first integer-like token from each non-empty line
    ticks = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # find first sequence of digits (at least 4 digits to avoid tiny numbers)
            m = re.search(r'(\d{3,})', line)
            if m:
                try:
                    ticks.append(int(m.group(1)))
                except:
                    pass
    return np.array(ticks, dtype=np.int64)

if len(sys.argv) < 3:
    print("Usage: python plot_brightness_with_events.py brightness.csv events.csv [autolog.csv] out.png")
    sys.exit(1)

brightness_csv = sys.argv[1]
events_csv = sys.argv[2]
autolog = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "" else None
out_png = sys.argv[4] if len(sys.argv) > 4 else "plot_out.png"

# load brightness
df = pd.read_csv(brightness_csv)
if 'time_s' not in df.columns or 'brightness' not in df.columns:
    raise SystemExit("brightness CSV must contain 'time_s' and 'brightness' columns")

# load events (robust)
ev_times = None
if os.path.exists(events_csv):
    try:
        ev = pd.read_csv(events_csv)
        # try common column names
        if 'time_s' in ev.columns:
            ev_times = pd.to_numeric(ev['time_s'], errors='coerce').dropna().values
        elif 'tick_ms' in ev.columns:
            ev_times = pd.to_numeric(ev['tick_ms'], errors='coerce').dropna().values / 1000.0
        else:
            # fallback: try first column
            ev_times = pd.to_numeric(ev.iloc[:,0], errors='coerce').dropna().values
    except Exception as e:
        print("Warning: couldn't parse events CSV:", e)
        ev_times = None

plt.figure(figsize=(12,4))
plt.plot(df['time_s'], df['brightness'], label='brightness', linewidth=1)

if ev_times is not None and len(ev_times)>0:
    # clamp event times to brightness time range for plotting y-values
    y_ev = np.interp(ev_times, df['time_s'], df['brightness'])
    plt.scatter(ev_times, y_ev, marker='x', color='red', label='detected events')

if autolog:
    if not os.path.exists(autolog):
        print("Warning: autolog path does not exist:", autolog)
    else:
        ticks = read_autolog_ticks(autolog)
        if ticks.size == 0:
            print("Warning: no numeric ticks found in autolog file.")
        else:
            t0 = ticks[0]
            t_secs = (ticks - t0) / 1000.0
            # Clip vertical lines to brightness time range to avoid huge plots
            tmin, tmax = df['time_s'].iloc[0], df['time_s'].iloc[-1]
            for tt in t_secs:
                if tt < tmin-1 or tt > tmax+1:
                    continue
                plt.axvline(tt, color='orange', alpha=0.12)
            plt.text(0.99,0.02,"autolog ticks (relative)", transform=plt.gca().transAxes, ha='right', fontsize=8, color='orange')

plt.xlabel('time (s)')
plt.ylabel('brightness (arb. units)')
plt.legend()
plt.tight_layout()
plt.savefig(out_png, dpi=150)
print("Saved plot to", out_png)
