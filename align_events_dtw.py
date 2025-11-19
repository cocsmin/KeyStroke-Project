# Usage: python align_events_dtw.py events.csv logs\auto_log.csv out_mapped.csv
# Simple DTW on event timestamp sequences (ms). Produces mapped ticks for each video event.

import sys, pandas as pd, numpy as np, re, os

def load_events_csv(ev_csv):
    ev = pd.read_csv(ev_csv)
    if 'time_s' not in ev.columns:
        if ev.shape[1] == 1:
            ev.columns = ['time_s']
        else:
            ev['time_s'] = pd.to_numeric(ev.iloc[:,0], errors='coerce')
    ev['time_s'] = pd.to_numeric(ev['time_s'], errors='coerce')
    ev = ev.dropna(subset=['time_s']).reset_index(drop=True)
    ev_ms = (ev['time_s'].values * 1000.0).astype(float)
    return ev, ev_ms

def load_autolog_ticks(log_csv):
    ticks=[]
    with open(log_csv, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            s=line.strip()
            if not s: continue
            m=re.search(r'(\d{3,})', s)
            if m: ticks.append(int(m.group(1)))
    return np.array(ticks, dtype=np.int64)

def dtw_path(x, y):
    # x: length n, y: length m
    n = len(x); m = len(y)
    INF = 10**18
    D = np.full((n+1,m+1), INF, dtype=np.float64)
    D[0,0] = 0.0
    for i in range(1,n+1):
        for j in range(1,m+1):
            cost = abs(x[i-1] - y[j-1])
            D[i,j] = cost + min(D[i-1,j], D[i,j-1], D[i-1,j-1])
    # backtrack
    i=n; j=m
    path=[]
    while i>0 and j>0:
        path.append((i-1,j-1))
        # choose predecessor
        prev = np.argmin([D[i-1,j], D[i,j-1], D[i-1,j-1]])
        if prev == 0:
            i -= 1
        elif prev == 1:
            j -= 1
        else:
            i -= 1; j -= 1
    # if any left, add them
    while i>0:
        i-=1; path.append((i,0))
    while j>0:
        j-=1; path.append((0,j))
    path.reverse()
    return path

if len(sys.argv) < 4:
    print("Usage: python align_events_dtw.py events.csv logs\\auto_log.csv out_mapped.csv")
    sys.exit(1)

ev_csv = sys.argv[1]
log_csv = sys.argv[2]
out_csv = sys.argv[3]

ev, ev_ms = load_events_csv(ev_csv)
autolog_ticks = load_autolog_ticks(log_csv)
if len(autolog_ticks) < 3 or len(ev_ms) < 3:
    raise SystemExit("Not enough events or autolog ticks for DTW")

# Convert autolog ticks to relative ms (relative to first tick) to compare with video ms relative to first video ms
autolog_rel = (autolog_ticks - autolog_ticks[0]).astype(float)
ev_rel = ev_ms - ev_ms[0]

# compute DTW path (cost = abs(time diff))
path = dtw_path(ev_rel, autolog_rel)
# path is list of (i_ev, j_aut)
# For each ev index, collect all matched aut indices and set mapped tick = mean(autolog_ticks[j])
from collections import defaultdict
map_dict = defaultdict(list)
for i_ev, j_aut in path:
    map_dict[i_ev].append(j_aut)

mapped_ticks = np.zeros(len(ev), dtype=np.int64)
for i in range(len(ev)):
    js = map_dict.get(i, [])
    if len(js) == 0:
        # fallback: nearest autolog index by absolute time
        j = np.argmin(np.abs(autolog_rel - ev_rel[i]))
        mapped_ticks[i] = autolog_ticks[j]
    else:
        mapped_ticks[i] = int(np.round(np.mean(autolog_ticks[js])))

ev['tick_ms_mapped'] = mapped_ticks
ev.to_csv(out_csv, index=False)
print("Saved DTW-mapped events to", out_csv)
# print summary
diffs = autolog_ticks[:min(len(autolog_ticks), len(mapped_ticks))] - mapped_ticks[:min(len(autolog_ticks), len(mapped_ticks))]
print("DTW mapping done, sample diffs (first 10):", diffs[:10])
