# Usage:
# python stats_tests.py path/to/human_ikis.csv path/to/auto_ikis.csv
import sys
import pandas as pd
from scipy.stats import ks_2samp, mannwhitneyu

if len(sys.argv) < 3:
    print("Usage: python stats_tests.py human_ikis.csv auto_ikis.csv")
    sys.exit(1)

h = pd.read_csv(sys.argv[1])['iki_s'].values
a = pd.read_csv(sys.argv[2])['iki_s'].values

print("Human n:", len(h), "Auto n:", len(a))
print("Human mean/std:", h.mean(), h.std(ddof=1))
print("Auto  mean/std:", a.mean(), a.std(ddof=1))

ks = ks_2samp(h,a)
mw = mannwhitneyu(h,a, alternative='two-sided')
print("KS test statistic=%.4f p=%.4g" % (ks.statistic, ks.pvalue))
print("Mann-Whitney U statistic=%.4f p=%.4g" % (mw.statistic, mw.pvalue))
