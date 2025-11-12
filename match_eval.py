import pandas as pd, numpy as np, sys, os
autolog = "logs\\auto_log.csv"
mapped = "events\\auto_100ms_01_events_mapped.csv"
# tolerance in ms
tol_ms = 200

# load mapped ticks
me = pd.read_csv(mapped)
if 'tick_ms_mapped' in me.columns:
    mapped_ticks = me['tick_ms_mapped'].values
elif 'tick_ms' in me.columns:
    mapped_ticks = me['tick_ms'].values
else:
    mapped_ticks = me.iloc[:,0].values

# load autolog ticks robustly
ticks=[]
import re
with open(autolog,'r',encoding='utf-8',errors='ignore') as f:
    for line in f:
        s=line.strip()
        if not s: continue
        m=re.search(r'(\d{3,})',s)
        if m: ticks.append(int(m.group(1)))
ticks=np.array(ticks)

# match: for each autolog tick find nearest mapped tick and check abs diff
matches = []
for t in ticks:
    if len(mapped_ticks)==0: break
    idx = np.argmin(np.abs(mapped_ticks - t))
    diff = int(mapped_ticks[idx] - t)
    matches.append((t, mapped_ticks[idx], diff))
matches = np.array(matches, dtype=object)

# compute stats
diffs = np.array([m[2] for m in matches])
absdiffs = np.abs(diffs)
tp = np.sum(absdiffs <= tol_ms)
fn = np.sum(absdiffs > tol_ms)  # autolog events without close mapped
# false positives: mapped ticks that are not matched to any autolog within tol
mapped_used = set(matches[np.where(absdiffs <= tol_ms)][:,1])
fp = np.sum([1 for mt in mapped_ticks if mt not in mapped_used])

print("N_autolog:", len(ticks), "N_mapped:", len(mapped_ticks))
print(f"Tolerance = {tol_ms} ms")
print("TP (autolog matched within tol):", tp)
print("FN (autolog unmatched):", fn)
print("FP (mapped with no autolog near):", fp)
print("diffs mean/std/median/90p:", diffs.mean(), diffs.std(), np.median(diffs), np.percentile(np.abs(diffs),90))
