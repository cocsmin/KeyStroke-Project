import pandas as pd
f = pd.read_csv("features\\auto_100ms_01_features.csv")
n = int(f['n_events'].iloc[0])
mu = float(f['mu_iki_s'].iloc[0])
print("n_events:", n, "mu_iki_s:", mu, "estimated_total_s:", n*mu)
