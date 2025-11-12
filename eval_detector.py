# Usage:
# python eval_detector.py --features_glob "C:\keystroke_project\KeyStroke-Project\features\*_features.csv" --labels C:\keystroke_project\KeyStroke-Project\labels.csv --score_col cv_iki

import argparse, glob, os, pandas as pd, numpy as np
from sklearn.metrics import roc_curve, auc, precision_recall_fscore_support, confusion_matrix

p = argparse.ArgumentParser()
p.add_argument('--features_glob', required=True)
p.add_argument('--labels', required=True)
p.add_argument('--score_col', default='cv_iki')
args = p.parse_args()

labels_df = pd.read_csv(args.labels)
labels = dict(zip(labels_df['filename'], labels_df['label']))
files = glob.glob(args.features_glob)
X=[]; y=[]; names=[]
for f in files:
    name = os.path.basename(f)
    if name not in labels:
        continue
    df = pd.read_csv(f)
    score = float(df.loc[0, args.score_col]) if args.score_col in df.columns else float(df.loc[0,'mu_iki_s'])
    X.append(score); y.append(int(labels[name])); names.append(name)

if len(X) == 0:
    print("No matched feature files with labels. Check filenames.")
    raise SystemExit(0)

fpr,tpr,thr = roc_curve(y, X)
roc_auc = auc(fpr, tpr)
print("AUC:", roc_auc)
thr0 = np.median(X)
preds = [1 if s>=thr0 else 0 for s in X]
precision, recall, f1, _ = precision_recall_fscore_support(y, preds, average='binary')
cm = confusion_matrix(y, preds)
print("Threshold (median):", thr0)
print("Precision, Recall, F1:", precision, recall, f1)
print("Confusion matrix:\n", cm)
