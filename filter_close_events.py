import pandas as pd, sys
infile = sys.argv[1]  # events file (csv with time_s column)
outfile = sys.argv[2]
min_ms = int(sys.argv[3]) if len(sys.argv)>3 else 40

ev = pd.read_csv(infile)
if 'time_s' not in ev.columns:
    ev.columns = ['time_s']
ev['time_ms'] = (ev['time_s']*1000).astype(int)
keep = [0]
for i in range(1, len(ev)):
    if ev['time_ms'].iloc[i] - ev['time_ms'].iloc[keep[-1]] >= min_ms:
        keep.append(i)
ev_filtered = ev.iloc[keep].copy()
ev_filtered[['time_s']].to_csv(outfile, index=False)
print("Filtered from", len(ev), "to", len(ev_filtered))
