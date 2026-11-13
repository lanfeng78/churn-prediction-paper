"""补充分析：CV 口径消融、预算约束收益、SHAP、置换重要性"""
import json, os, warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.inspection import permutation_importance
import lightgbm as lgb
import shap

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RNG = 42

df = pd.read_csv(os.path.join(BASE, "data", "cohort2011.csv"), index_col=0)
y = df.pop("churn").values
X = df
params = json.load(open(os.path.join(BASE, "results", "metrics.json")))["tuning"]["LGBM"]["best_params"]

groups = {
    "RFM核心": ["recency", "frequency", "monetary", "aov"],
    "消费强度": ["items_per_order", "n_sku", "max_order_amount", "median_order_amount",
             "std_order_amount", "amount_cv", "unit_price_mean"],
    "购买节奏": ["gap_mean", "gap_std", "gap_cv", "max_dark_gap", "active_month_ratio",
             "tenure_days", "first_purchase_gap"],
    "趋势变化": ["early_orders", "late_orders", "trend_ratio", "month_slope",
             "recent30_amount_ratio", "month_amount_growth"],
    "结构多样性": ["price_entropy", "repeat_sku_ratio"],
    "退货行为": ["return_qty_ratio", "has_return"],
    "时间偏好": ["weekend_ratio", "working_hour_ratio", "is_uk"],
}

def cv_auc(cols):
    skf = StratifiedKFold(5, shuffle=True, random_state=RNG)
    aucs = []
    for tr, va in skf.split(X[cols], y):
        m = lgb.LGBMClassifier(**params, n_jobs=6, random_state=RNG, verbose=-1)
        m.fit(X[cols].iloc[tr], y[tr])
        aucs.append(roc_auc_score(y[va], m.predict_proba(X[cols].iloc[va])[:, 1]))
    return float(np.mean(aucs)), float(np.std(aucs))

abl = {}
abl["full"] = cv_auc(list(X.columns))
for g, cols in groups.items():
    abl["drop_" + g] = cv_auc([c for c in X.columns if c not in cols])
    abl["only_" + g] = cv_auc(cols)

# 预算约束收益（固定触达比例，按模型排序 vs 随机排序）
C_FN, C_FP = 200.0, 50.0
d = np.load(os.path.join(BASE, "results", "preds.npz"), allow_pickle=True)
yte = d["y_test"]; p = d["p_XGB"]
order = np.argsort(-p)
curve = {"coverage": [], "model": [], "random": []}
rng = np.random.default_rng(RNG)
for cov in np.arange(0.02, 1.001, 0.02):
    k = max(1, int(round(cov * len(yte))))
    tp = yte[order[:k]].sum(); fp = k - tp
    curve["coverage"].append(float(cov))
    curve["model"].append(float(tp * C_FN - k * C_FP))
    rr = []
    for _ in range(200):
        s = rng.choice(len(yte), k, replace=False)
        rr.append(yte[s].sum() * C_FN - k * C_FP)
    curve["random"].append(float(np.mean(rr)))
budget = {"C_FN": C_FN, "C_FP": C_FP, "curve": curve,
          "at": {}}
for cov in [0.1, 0.2, 0.3, 0.5]:
    k = int(round(cov * len(yte)))
    tp = yte[order[:k]].sum()
    budget["at"][str(cov)] = {"coverage": cov, "targets": k, "tp": int(tp),
                              "precision": float(tp / k), "recall": float(tp / yte.sum()),
                              "lift": float((tp / k) / yte.mean()),
                              "profit": float(tp * C_FN - k * C_FP),
                              "random_profit": float(yte.mean() * k * C_FN - k * C_FP)}

# SHAP
Xtr = d["X_train"]; Xte = d["X_test"]
feats = list(d["feature_names"])
m = lgb.LGBMClassifier(**params, n_jobs=6, random_state=RNG, verbose=-1).fit(Xtr, d["y_train"])
expl = shap.TreeExplainer(m)
sv = expl.shap_values(Xte)
if isinstance(sv, list): sv = sv[1]
sv = np.array(sv)
imp = pd.DataFrame({"feature": feats, "mean_abs_shap": np.abs(sv).mean(0)}).sort_values("mean_abs_shap", ascending=False)
# 置换重要性
perm = permutation_importance(m, Xte, yte, n_repeats=10, random_state=RNG, scoring="roc_auc")
pimp = pd.DataFrame({"feature": feats, "mean": perm.importances_mean, "std": perm.importances_std}).sort_values("mean", ascending=False)

np.save(os.path.join(BASE, "results", "shap_values.npy"), sv)
pd.DataFrame(Xte, columns=feats).to_csv(os.path.join(BASE, "results", "X_test.csv"), index=False)
imp.to_csv(os.path.join(BASE, "results", "shap_importance.csv"), index=False)
pimp.to_csv(os.path.join(BASE, "results", "perm_importance.csv"), index=False)

out = {"ablation_cv": abl, "budget": budget,
       "shap_top": imp.head(15).round(4).to_dict("records"),
       "perm_top": pimp.head(10).round(4).to_dict("records")}
json.dump(out, open(os.path.join(BASE, "results", "analysis2.json"), "w"), ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in abl.items()}, indent=1))
print("budget", json.dumps(budget["at"], indent=1))
print(imp.head(12).to_string(index=False))
print(pimp.head(8).to_string(index=False))
