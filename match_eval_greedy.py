# Usage: python match_eval_greedy.py mapped_file.csv logs\auto_log.csv
import numpy as np, pandas as pd, re, sys, os

if len(sys.argv) < 3:
    print("Usage: python match_eval_greedy.py mapped_file.csv logs\\auto_log.csv")
    sys.exit(1)

mapped_file = sys.argv[1]
autolog_file = sys.argv[2]

# load mapped ticks (any column with 'tick' in name)
me = pd.read_csv(mapped_file)
tick_cols = [c for c in me.columns if 'tick' in c]
if len(tick_cols) == 0:
    mapped_ticks = me.iloc[:,0].values.astype(int)
else:
    mapped_ticks = me[tick_cols[0]].values.astype(int)

# load autolog robustly
ticks = []
with open(autolog_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        s=line.strip()
        if not s: continue
        m = re.search(r'(\d{3,})', s)
        if m: ticks.append(int(m.group(1)))
ticks = np.array(ticks, dtype=np.int64)

# greedy matching: for each autolog tick, find nearest mapped tick not already used
mapped_used = np.zeros(len(mapped_ticks), dtype=bool)
matches = []  # tuples (autolog_idx, mapped_idx, diff_ms)
for i, t in enumerate(ticks):
    if len(mapped_ticks)==0: break
    # compute distances to unmapped mapped ticks
    idxs = np.where(~mapped_used)[0]
    if len(idxs)==0:
        break
    dists = np.abs(mapped_ticks[idxs] - t)
    j = np.argmin(dists)
    mapped_idx = idxs[j]
    diff = mapped_ticks[mapped_idx] - t
    matches.append((i, mapped_idx, int(diff)))
    # mark as used if within a practical cap (we still mark used to preserve bijection)
    mapped_used[mapped_idx] = True

# create arrays
matches = np.array(matches, dtype=object)
diffs = np.array([m[2] for m in matches]) if len(matches)>0 else np.array([])

# evaluate for multiple tolerances
tol_list = [100,200,300,500]
print("N_autolog:", len(ticks), "N_mapped:", len(mapped_ticks), "N_matches_made:", len(matches))
for tol in tol_list:
    tp = np.sum(np.abs(diffs) <= tol)
    fn = len(ticks) - tp
    fp = len(mapped_ticks) - tp
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    print(f"tol {tol} ms -> TP {tp}, FN {fn}, FP {fp}, Precision {prec:.3f}, Recall {rec:.3f}")

print("Matched diffs stats (ms): mean=%.1f std=%.1f median=%.1f p90=%.1f" %
      (diffs.mean() if diffs.size>0 else 0, diffs.std() if diffs.size>0 else 0, np.median(diffs) if diffs.size>0 else 0, np.percentile(np.abs(diffs),90) if diffs.size>0 else 0))
# save matches for inspection
out_df = pd.DataFrame(matches, columns=['autolog_idx','mapped_idx','diff_ms'])
out_df.to_csv("analysis\\matches_greedy.csv", index=False)
print("Saved analysis\\matches_greedy.csv")
