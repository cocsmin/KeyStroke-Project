# Usage: python align_piecewise.py events.csv logs/auto_log.csv n_segments out_mapped.csv
import sys, pandas as pd, numpy as np, re, os
from sklearn.linear_model import LinearRegression

if len(sys.argv) < 5:
    print("Usage: python align_piecewise.py events.csv logs/auto_log.csv n_segments out_mapped.csv")
    sys.exit(1)

events_csv = sys.argv[1]
autolog_csv = sys.argv[2]
n_segments = int(sys.argv[3])
out_csv = sys.argv[4]

# load events
ev = pd.read_csv(events_csv)
if 'time_s' not in ev.columns:
    if ev.shape[1] == 1:
        ev.columns = ['time_s']
    else:
        ev['time_s'] = pd.to_numeric(ev.iloc[:,0], errors='coerce')
ev['time_s'] = pd.to_numeric(ev['time_s'], errors='coerce')
ev = ev.dropna(subset=['time_s']).reset_index(drop=True)

# parse autolog
ticks = []
with open(autolog_csv, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        s=line.strip()
        if not s: continue
        m = re.search(r'(\d{3,})', s)
        if m: ticks.append(int(m.group(1)))
al = np.array(ticks, dtype=np.int64)
if len(al) < 3:
    raise SystemExit("Not enough autolog ticks for piecewise alignment")

N = min(len(ev), len(al))
mapped_ticks = np.zeros(len(ev), dtype=np.int64)
al_first = int(al[0])

# determine segment boundaries using N (only within overlapping region)
for seg in range(n_segments):
    i0 = int(seg * N / n_segments)
    i1 = int((seg+1) * N / n_segments) if seg < n_segments-1 else N
    if i1 - i0 < 3:
        # not enough samples in this segment, copy linear fallback
        continue
    X = (ev['time_s'].iloc[i0:i1].values.reshape(-1,1) * 1000.0)
    y = (al[i0:i1].reshape(-1,1) - al_first)
    lr = LinearRegression().fit(X, y)
    a_rel = float(lr.intercept_[0]) if hasattr(lr.intercept_, "__len__") else float(lr.intercept_)
    b = float(lr.coef_[0][0]) if hasattr(lr.coef_, "__len__") else float(lr.coef_)
    print(f"seg {seg}: idx {i0}-{i1}  a_rel={a_rel:.2f}  b={b:.6f}")
    mapped_ticks[i0:i1] = (al_first + a_rel + b * (ev['time_s'].iloc[i0:i1].values * 1000.0)).round().astype(int)

# for samples outside 0..N-1 (if ev longer), extend mapping by last segment linear extrapolation
if N < len(ev):
    # use last segment params
    last_seg = min(n_segments-1, n_segments-1)
    # find last fitted segment params from printed segments (recompute last)
    i0 = int((n_segments-1) * N / n_segments)
    i1 = N
    X = (ev['time_s'].iloc[i0:i1].values.reshape(-1,1) * 1000.0)
    lr = LinearRegression().fit(X, (al[i0:i1].reshape(-1,1) - al_first))
    a_rel = float(lr.intercept_[0]) if hasattr(lr.intercept_, "__len__") else float(lr.intercept_)
    b = float(lr.coef_[0][0]) if hasattr(lr.coef_, "__len__") else float(lr.coef_)
    mapped_ticks[N:] = (al_first + a_rel + b * (ev['time_s'].iloc[N:].values * 1000.0)).round().astype(int)

ev['tick_ms_mapped'] = mapped_ticks
ev.to_csv(out_csv, index=False)
print("Saved piecewise mapped to", out_csv)
