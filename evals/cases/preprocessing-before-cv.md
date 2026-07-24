---
id: preprocessing-before-cv
skill: leakage-auditor
polarity: positive
tags: [leakage, preprocessing, cross-validation, smote, feature-selection, entity]
---

# Scaler, feature selection and SMOTE fit before cross-validation

## Prompt

Hospital readmission model, ~14k patient encounters, 9% positive class. A reviewer on my
team says my cross-validation number is too good but can't say why. Here's the relevant
part of the notebook.

```python
import pandas as pd, numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.impute import SimpleImputer
from imblearn.over_sampling import SMOTE
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold

df = pd.read_parquet("encounters.parquet")          # 14,204 rows, 9,867 distinct patient_id
y  = df.pop("readmit_30d").values
X  = df.drop(columns=["encounter_id", "patient_id", "discharge_ts"])

imp = SimpleImputer(strategy="median")
X = imp.fit_transform(X)

scaler = StandardScaler()
X = scaler.fit_transform(X)

sel = SelectKBest(f_classif, k=40)                  # from 310 candidate columns
X = sel.fit_transform(X, y)

sm = SMOTE(random_state=0)
X_res, y_res = sm.fit_resample(X, y)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
scores = cross_val_score(LogisticRegression(max_iter=2000), X_res, y_res,
                         cv=cv, scoring="roc_auc")
print(scores.mean(), scores.std())                  # 0.891 0.006
```

Is 0.891 a trustworthy estimate of what we would see on next quarter's discharges?
