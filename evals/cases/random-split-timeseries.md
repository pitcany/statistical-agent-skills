---
id: random-split-timeseries
skill: time-series-forecasting
polarity: positive
tags: [temporal, backtest, leakage, rolling-origin, baseline, demand-planning]
---

# Shuffled train/test split on daily demand data

## Prompt

Daily units shipped per SKU-DC pair, 730 days of history, about 400 SKU-DC pairs. I am
building a 4-week-ahead demand forecast to feed replenishment.

```python
feat = df.sort_values("date").copy()
feat["dow"]     = feat.date.dt.dayofweek
feat["month"]   = feat.date.dt.month
feat["roll7"]   = feat.groupby("sku_dc").units.transform(
                      lambda s: s.rolling(7, center=True).mean())
feat["roll28"]  = feat.groupby("sku_dc").units.transform(
                      lambda s: s.rolling(28).mean())
feat["price"]   = feat.price
feat["promo"]   = feat.promo_flag

X = feat[["dow", "month", "roll7", "roll28", "price", "promo"]]
y = feat["units"]

X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, shuffle=True, random_state=7)

model = HistGradientBoostingRegressor().fit(X_tr, y_tr)
print(mean_absolute_percentage_error(y_te, model.predict(X_te)))   # 0.062
```

6.2% MAPE looks great next to the ~19% our planners currently run at. Planning wants to
cut safety stock by 15% on the strength of it, starting next cycle. Sanity check before
I say yes?
