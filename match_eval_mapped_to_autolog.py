# match_eval_mapped_to_autolog.py
# Usage: python match_eval_mapped_to_autolog.py mapped.csv logs\auto_log.csv
import sys, numpy as np, pandas as pd, re
if len(sys.argv) < 3:
    print("Usage: python match_eval_mapped_to_autolog.py mapped.csv logs\\auto_log.csv")
    sys.exit(1)

mapped_file = sys.argv[1]
log_file = sys.argv[2]

# load mapped ticks
me = pd.read_csv(mapped_file)
tick_cols = [c for c in me.columns if 'tick' in c.lower()]
if len(tick_cols)>0:
    mapped = me[tick_cols[0]].values.astype(int)
else:
    mapped = me.iloc[:,0].values.astype(int)

# load autolog ticks
ticks=[]
with open(log_file,'r',encoding='utf-8',errors='ignore') as f:
    for line in f:
        s=line.strip()
        if not s: continue
        m=re.search(r'(\d{3,})', s)
        if m: ticks.append(int(m.group(1)))
ticks = np.array(ticks, dtype=np.int64)

# greedy match mapped -> nearest autolog (bijective)
used = np.zeros(len(ticks), dtype=bool)
matches=[]
for i, mt in enumerate(mapped):
    # find closest autolog index not used yet
    idxs = np.where(~used)[0]
    if len(idxs)==0:
        break
    j_rel = np.argmin(np.abs(ticks[idxs] - mt))
    j = idxs[j_rel]
    diff = mt - ticks[j]
    matches.append((i, j, int(diff)))
    used[j] = True

matches = np.array(matches, dtype=object)
diffs = np.array([m[2] for m in matches]) if len(matches)>0 else np.array([])
print("N_autolog:", len(ticks), "N_mapped:", len(mapped), "N_matches_made:", len(matches))
for tol in [100,200,300,500]:
    tp = np.sum(np.abs(diffs) <= tol)
    fn = len(ticks) - tp
    fp = len(mapped) - tp
    prec = tp / (tp + fp) if (tp + fp)>0 else 0.0
    rec = tp / (tp + fn) if (tp + fn)>0 else 0.0
    print(f"tol {tol} ms -> TP {tp}, FN {fn}, FP {fp}, Precision {prec:.3f}, Recall {rec:.3f}")
if diffs.size>0:
    print("diffs stats (ms): mean=%.1f std=%.1f median=%.1f p90=%.1f min=%d max=%d" %
          (diffs.mean(), diffs.std(), np.median(diffs), np.percentile(np.abs(diffs),90), diffs.min(), diffs.max()))
# save pairs for inspection
import pandas as pd
pd.DataFrame(matches, columns=['mapped_idx','autolog_idx','diff_ms']).to_csv("analysis\\matches_mapped_to_autolog.csv", index=False)
print("Saved analysis\\matches_mapped_to_autolog.csv")
