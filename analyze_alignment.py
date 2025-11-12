import pandas as pd, numpy as np, matplotlib.pyplot as plt, sys, os

events_mapped = "events\\auto_100ms_01_events_mapped.csv"  # sau mapped_scaled dacă ai folosit align_events_to_log_scaled.py
autolog = "logs\\auto_log.csv"

# load mapped events
ev = pd.read_csv(events_mapped)
if 'tick_ms' in ev.columns:
    ev_ticks = ev['tick_ms'].values
elif 'tick_ms_mapped' in ev.columns:
    ev_ticks = ev['tick_ms_mapped'].values
else:
    # fallback: if mapped was in tick_ms_mapped or tick_ms
    names = [c for c in ev.columns if 'tick' in c]
    ev_ticks = ev[names[0]].values

# load autolog ticks robustly
ticks = []
with open(autolog, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        s=line.strip()
        if not s: continue
        import re
        m = re.search(r'(\d{3,})', s)
        if m:
            ticks.append(int(m.group(1)))
ticks = np.array(ticks, dtype=np.int64)

# align lengths
N = min(len(ticks), len(ev_ticks))
ticks = ticks[:N]
ev_ticks = ev_ticks[:N]

res = ticks - ev_ticks  # positive => autolog later than mapped (autolog - mapped)
print("N pairs:", N)
print("Residuals ms: mean=%.2f std=%.2f median=%.2f p90=%.2f max=%.1f min=%.1f" %
      (res.mean(), res.std(), np.median(res), np.percentile(np.abs(res),90), res.max(), res.min()))

# save residuals
pd.DataFrame({'autolog':ticks, 'mapped':ev_ticks, 'res_ms':res}).to_csv("analysis\\residuals_autolog_mapped.csv", index=False)

# plot residuals vs time
plt.figure(figsize=(10,4))
plt.plot((ev_ticks - ev_ticks[0]) / 1000.0, res, marker='.', linestyle='-', markersize=3)
plt.axhline(0, color='k', linewidth=0.6)
plt.xlabel('mapped time (s)')
plt.ylabel('autolog - mapped (ms)')
plt.title('Residuals over time')
plt.grid(alpha=0.3)
plt.tight_layout()
os.makedirs("analysis", exist_ok=True)
plt.savefig("analysis\\residuals.png", dpi=150)
print("Saved analysis\\residuals.png")

# plot brightness with autolog converted to mapped seconds
# we attempt to load brightness
brightness_file = "frames\\auto_100ms_01_brightness.csv"
if os.path.exists(brightness_file):
    b = pd.read_csv(brightness_file)
    plt.figure(figsize=(12,4))
    plt.plot(b['time_s'], b['brightness'], label='brightness')
    # map autolog ticks to seconds relative mapped first event
    t0 = ev_ticks[0]
    autolog_rel_s = (ticks - t0) / 1000.0
    plt.vlines(autolog_rel_s, ymin=b['brightness'].min(), ymax=b['brightness'].max(), colors='orange', alpha=0.15)
    plt.scatter((ev_ticks - t0)/1000.0, np.interp((ev_ticks - ev_ticks[0])/1000.0, b['time_s'], b['brightness']), color='red', s=10, label='mapped events (red x)')
    plt.legend()
    plt.xlabel('time (s)')
    plt.ylabel('brightness')
    plt.tight_layout()
    plt.savefig("analysis\\aligned_events.png", dpi=150)
    print("Saved analysis\\aligned_events.png")
else:
    print("Brightness file not found:", brightness_file)
