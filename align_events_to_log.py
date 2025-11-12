# Usage: python align_events_to_log_scaled.py events.csv logs/auto_log.csv [out_mapped.csv]
import sys, pandas as pd, numpy as np, re, os
from sklearn.linear_model import LinearRegression

if len(sys.argv) < 3:
    print("Usage: python align_events_to_log_scaled.py events.csv logs/auto_log.csv [out_mapped.csv]")
    sys.exit(1)

events_csv = sys.argv[1]
autolog_csv = sys.argv[2]
out_csv = sys.argv[3] if len(sys.argv) > 3 else "events_mapped_scaled.csv"

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

if len(ticks) < 5:
    raise SystemExit("Not enough numeric ticks found in autolog file.")

al = pd.DataFrame({'tick': ticks})

# choose matching samples for regression:
# use first N pairs where both events and autolog exist
N = min(len(ev), len(al))
# prepare X (video time in ms relative to video start) and y (autolog ticks relative to autolog start)
X = (ev['time_s'].iloc[:N].values.reshape(-1,1) * 1000.0)  # ms
y = (al['tick'].iloc[:N].values.reshape(-1,1) - al['tick'].iloc[0])  # ms relative

# fit linear model y = b * X + a (we include intercept)
model = LinearRegression().fit(X, y)
b = float(model.coef_[0][0])
a_rel = float(model.intercept_[0])
# convert to global form: mapped_tick = al_first_tick + a_rel + b * time_s*1000
al_first = int(al['tick'].iloc[0])

print(f"Linear fit: mapped_rel = a_rel + b * time_ms   (a_rel={a_rel:.3f} ms, b={b:.6f})")
print(f"al_first_tick = {al_first}")

# compute mapped ticks
ev['tick_ms_mapped'] = (al_first + a_rel + b * (ev['time_s'].values * 1000.0)).round().astype(int)

# compute residuals for fitted samples
mapped_for_fit = al_first + a_rel + b * (ev['time_s'].iloc[:N].values * 1000.0)
residuals = al['tick'].iloc[:N].values - mapped_for_fit
print("Residuals (autolog - mapped) for first N samples: mean=%.2f ms  std=%.2f ms  max_abs=%.1f ms" %
      (np.mean(residuals), np.std(residuals), np.max(np.abs(residuals))))
# print first 10 comparisons
print("Comparing first 10 pairs (autolog_tick vs mapped_tick vs diff_ms):")
for i in range(min(10,N)):
    mapped_i = int(round(mapped_for_fit[i]))
    print(i, int(al['tick'].iloc[i]), mapped_i, int(al['tick'].iloc[i] - mapped_i))

# save mapped events
ev.to_csv(out_csv, index=False)
print("Saved mapped events to", out_csv)
