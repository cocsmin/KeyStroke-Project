# Usage: python align_events_to_log.py events.csv logs/auto_log.csv out_mapped.csv
import sys, pandas as pd, numpy as np, os

if len(sys.argv) < 3:
    print("Usage: python align_events_to_log.py events.csv logs/auto_log.csv [out_mapped.csv]")
    sys.exit(1)

events_csv = sys.argv[1]
autolog_csv = sys.argv[2]
out_csv = sys.argv[3] if len(sys.argv)>3 else "events_mapped.csv"

ev = pd.read_csv(events_csv)
# load autolog robustly
try:
    al = pd.read_csv(autolog_csv, names=['tick','key'], sep=r"\s+", engine="python")
except Exception:
    al = pd.read_csv(autolog_csv, names=['tick','key'], header=None)

# normalize column names
if 'time_s' not in ev.columns and ev.shape[1] >= 1:
    ev.columns = ['time_s'] if ev.shape[1]==1 else ev.columns

if len(ev)==0 or len(al)==0:
    print("Empty events or autolog. ev:", len(ev), "al:", len(al)); sys.exit(1)

first_ev_s = ev['time_s'].iloc[0]
first_tick = int(al['tick'].iloc[0])
offset_ms = first_tick - first_ev_s*1000.0
ev['tick_ms'] = (ev['time_s']*1000.0 + offset_ms).round().astype(int)
print("First event (video) s:", first_ev_s)
print("First autolog tick ms:", first_tick)
print("Computed offset (ms):", offset_ms)

n = min(len(ev), len(al))
print("Comparing first", n, "events (autolog_tick vs mapped_event_tick vs diff_ms):")
for i in range(n):
    print(i, int(al['tick'].iloc[i]), int(ev['tick_ms'].iloc[i]), int(al['tick'].iloc[i] - ev['tick_ms'].iloc[i]))

ev.to_csv(out_csv, index=False)
print("Saved mapped events to", out_csv)
