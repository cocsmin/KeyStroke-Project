import pandas as pd, re
me = pd.read_csv("events\\auto_100ms_01_events_mapped_dtw_interp.csv")
ticks=[]
with open("logs\\auto_log.csv",'r',encoding='utf-8',errors='ignore') as f:
    for line in f:
        s=line.strip()
        if not s: continue
        m=re.search(r'(\d{3,})', s)
        if m: ticks.append(int(m.group(1)))
print("mapped first 20:")
print(me.head(20).to_string(index=False))
print("\\nautolog first 20:")
print(ticks[:20])