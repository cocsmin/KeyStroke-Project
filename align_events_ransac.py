# Usage:
# python align_events_ransac.py events.csv logs/auto_log.csv [out_mapped.csv] [residual_threshold_ms]

import sys, pandas as pd, numpy as np, re, os
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import RANSACRegressor

def make_ransac(base_estimator, min_samples, residual_threshold, random_state=0):
    # try both parameter names for compatibility
    try:
        r = RANSACRegressor(estimator=base_estimator, min_samples=min_samples,
                            residual_threshold=residual_threshold, random_state=random_state)
        return r
    except TypeError:
        # older sklearn may expect base_estimator
        try:
            r = RANSACRegressor(base_estimator=base_estimator, min_samples=min_samples,
                                residual_threshold=residual_threshold, random_state=random_state)
            return r
        except Exception as e:
            raise

if len(sys.argv) < 3:
    print("Usage: python align_events_ransac.py events.csv logs/auto_log.csv [out_mapped.csv] [residual_threshold_ms]")
    sys.exit(1)

events_csv = sys.argv[1]
autolog_csv = sys.argv[2]
out_csv = sys.argv[3] if len(sys.argv) > 3 else "events_mapped_ransac.csv"
residual_threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 800.0  # ms default

# load events
ev = pd.read_csv(events_csv)
if 'time_s' not in ev.columns:
    if ev.shape[1] == 1:
        ev.columns = ['time_s']
    else:
        ev['time_s'] = pd.to_numeric(ev.iloc[:,0], errors='coerce')
ev['time_s'] = pd.to_numeric(ev['time_s'], errors='coerce')
ev = ev.dropna(subset=['time_s']).reset_index(drop=True)

# parse autolog ticks robustly (extract integers)
ticks = []
with open(autolog_csv, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        s = line.strip()
        if not s:
            continue
        m = re.search(r'(\d{3,})', s)
        if m:
            try:
                ticks.append(int(m.group(1)))
            except:
                pass

if len(ticks) < 10:
    raise SystemExit("Not enough numeric ticks found in autolog file.")

al = np.array(ticks, dtype=np.int64)

# prepare X and y for fitting (use first N pairs)
N = min(len(ev), len(al))
X = (ev['time_s'].iloc[:N].values.reshape(-1,1) * 1000.0)  # ms
y = (al[:N].reshape(-1,1) - al[0])  # ms relative to first autolog tick

base_estimator = LinearRegression()
min_samples = max(10, int(0.3 * N))

# build ransac robustly
ransac = make_ransac(base_estimator, min_samples=min_samples, residual_threshold=residual_threshold, random_state=0)
ransac.fit(X, y.ravel())

# Extract linear parameters from the underlying estimator
est = ransac.estimator_
# handle shapes
coef = est.coef_
intercept = est.intercept_
try:
    b = float(coef[0]) if hasattr(coef, "__len__") else float(coef)
except:
    b = float(coef)
try:
    a_rel = float(intercept) if hasattr(intercept, "__len__") == False else float(intercept[0])
except:
    a_rel = float(intercept)

inlier_mask = ransac.inlier_mask_
print("RANSAC fit a_rel=%.3f ms, b=%.6f, inliers=%d/%d, residual_threshold=%.1f ms" %
      (a_rel, b, int(inlier_mask.sum()), N, residual_threshold))

al_first = int(al[0])
# compute mapped ticks for all events
ev['tick_ms_mapped'] = (al_first + a_rel + b * (ev['time_s'].values * 1000.0)).round().astype(int)

# compute residuals for pairs used in fit
mapped_for_fit = al_first + a_rel + b * (ev['time_s'].iloc[:N].values * 1000.0)
residuals = al[:N] - mapped_for_fit
residuals_all = np.array(residuals)
res_in = residuals_all[inlier_mask]
print("Residuals (autolog - mapped) for first N samples: mean=%.2f ms  std=%.2f ms  max_abs=%.1f ms" %
      (residuals_all.mean(), residuals_all.std(), np.max(np.abs(residuals_all))))
if len(res_in) > 0:
    print("Residuals (inliers only): mean=%.2f ms  std=%.2f ms  max_abs=%.1f ms" %
          (res_in.mean(), res_in.std(), np.max(np.abs(res_in))))

# save mapped events
ev.to_csv(out_csv, index=False)
print("Saved mapped events to", out_csv)
