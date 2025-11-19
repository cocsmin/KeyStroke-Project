# Usage:
# python align_events_dtw_interp.py events.csv logs\auto_log.csv out_mapped.csv
# This does DTW (simple) to obtain path, then builds monotonic mapping by interpolation.

import sys, pandas as pd, numpy as np, re, os

def load_events(ev_csv):
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

def load_autolog(log_csv):
    ticks=[]
    with open(log_csv, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            s=line.strip()
            if not s: continue
            m = re.search(r'(\d{3,})', s)
            if m: ticks.append(int(m.group(1)))
    return np.array(ticks, dtype=np.int64)

def dtw_path(x, y):
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
        prev = np.argmin([D[i-1,j], D[i,j-1], D[i-1,j-1]])
        if prev == 0:
            i -= 1
        elif prev == 1:
            j -= 1
        else:
            i -= 1; j -= 1
    while i>0:
        i-=1; path.append((i,0))
    while j>0:
        j-=1; path.append((0,j))
    path.reverse()
    return path

if len(sys.argv) < 4:
    print("Usage: python align_events_dtw_interp.py events.csv logs\\auto_log.csv out_mapped.csv")
    sys.exit(1)

ev_csv = sys.argv[1]
log_csv = sys.argv[2]
out_csv = sys.argv[3]

ev, ev_ms = load_events(ev_csv)
autolog_ticks = load_autolog(log_csv)
if len(ev_ms) < 2 or len(autolog_ticks) < 2:
    raise SystemExit("Not enough events or autolog ticks")

# use relative times for DTW cost but keep absolute autolog ticks
ev_rel = ev_ms - ev_ms[0]
autolog_rel = (autolog_ticks - autolog_ticks[0]).astype(float)

path = dtw_path(ev_rel, autolog_rel)
# build mapping lists: for each ev index collect matched autolog indices
from collections import defaultdict
map_dict = defaultdict(list)
for i_ev, j_aut in path:
    map_dict[i_ev].append(j_aut)

# create arrays of representative pairs (ev_time_ms -> autolog_tick_abs)
ev_pairs = []
aut_pairs = []
for i in range(len(ev_ms)):
    js = map_dict.get(i, [])
    if len(js) == 0:
        # fallback nearest autolog index
        j = int(np.argmin(np.abs(autolog_rel - ev_rel[i])))
        ev_pairs.append(ev_ms[i])
        aut_pairs.append(int(autolog_ticks[j]))
    else:
        # use median of corresponding autolog absolute ticks to be robust
        vals = autolog_ticks[js]
        ev_pairs.append(ev_ms[i])
        aut_pairs.append(int(np.round(np.median(vals))))

ev_pairs = np.array(ev_pairs)
aut_pairs = np.array(aut_pairs)

# Now we have potentially many points; ensure monotonic mapping by sorting and removing duplicates
order = np.argsort(ev_pairs)
ev_pairs = ev_pairs[order]
aut_pairs = aut_pairs[order]

# Remove duplicates in ev_pairs by keeping the first occurrence (or median of aut_pairs for that ev)
uniq_ev = []
uniq_aut = []
i = 0
while i < len(ev_pairs):
    j = i
    # group equal ev (rare)
    group_idx = [i]
    while j+1 < len(ev_pairs) and abs(ev_pairs[j+1] - ev_pairs[i]) < 1e-6:
        j += 1
        group_idx.append(j)
    uniq_ev.append(ev_pairs[i])
    uniq_aut.append(int(np.round(np.median(aut_pairs[group_idx]))))
    i = j+1

uniq_ev = np.array(uniq_ev)
uniq_aut = np.array(uniq_aut)

# Use numpy.interp to map every ev_ms to autolog absolute ticks (monotonic piecewise-linear)
mapped_ticks_interp = np.interp(ev_ms, uniq_ev, uniq_aut, left=uniq_aut[0], right=uniq_aut[-1]).round().astype(int)

ev['tick_ms_mapped'] = mapped_ticks_interp
ev.to_csv(out_csv, index=False)
print("Saved DTW-interpolated mapped events to", out_csv)
print("Sample pairs (first 10):")
for i in range(min(10,len(uniq_ev))):
    print(i, "ev_ms=%.3f -> aut_tick=%d" % (uniq_ev[i], uniq_aut[i]))
