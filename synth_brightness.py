# synth_brightness.py
# Quick synthetic generator to test pipeline.
import numpy as np, csv, argparse

def generate(iki_list, fs=240, A=20.0, h_dur=0.02, noise_std=1.0):
    t = np.cumsum(np.concatenate(([0.0], np.array(iki_list))))
    T = t[-1] + 1.0; N = int(T*fs); y = np.zeros(N)
    tt = np.arange(int(h_dur*fs))/fs; h = np.exp(-((tt-h_dur/2)**2)/(2*((h_dur/6)**2)))
    for tk in t:
        idx = int(round(tk*fs))
        if idx+len(h) < N:
            y[idx:idx+len(h)] += A*h
    y += np.random.normal(0, noise_std, size=y.shape); times = np.arange(N)/fs
    return times, y

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--out', default='synthetic_brightness.csv'); p.add_argument('--iki_ms', nargs='+', type=float, default=[100,120,110,100,95,105,130,120]); args = p.parse_args()
    ikis = [v/1000.0 for v in args.iki_ms]
    times,y = generate(ikis)
    with open(args.out,'w',newline='') as f:
        w = csv.writer(f); w.writerow(['frame','time_s','brightness'])
        for i,t in enumerate(times):
            w.writerow([i,t,float(y[i])])
    print("Saved", args.out)
