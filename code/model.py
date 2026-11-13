"""建模、调优、评估、可解释性与成本敏感分析"""
import json, os, warnings
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, StackingClassifier
from sklearn.metrics import (roc_auc_score, average_precision_score, roc_curve, precision_recall_curve,
                             f1_score, precision_score, recall_score, brier_score_loss, confusion_matrix)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.base import clone
import xgboost as xgb
import lightgbm as lgb
import optuna
from imblearn.over_sampling import SMOTE

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RNG = 42

def load():
    df = pd.read_csv(os.path.join(BASE, "data", "cohort2011.csv"), index_col=0)
    y = df.pop("churn").values
    return df, y

def metrics(y, p, thr=0.5):
    auc = roc_auc_score(y, p)
    ap = average_precision_score(y, p)
    pred = (p >= thr).astype(int)
    fpr, tpr, _ = roc_curve(y, p)
    ks = float(np.max(tpr - fpr))
    n = len(y)
    k = max(1, int(0.1 * n))
    top = np.argsort(-p)[:k]
    prec10 = y[top].mean()
    rec10 = y[top].sum() / y.sum()
    lift10 = prec10 / y.mean()
    return dict(auc=float(auc), pr_auc=float(ap), ks=ks,
                f1=float(f1_score(y, pred)), precision=float(precision_score(y, pred, zero_division=0)),
                recall=float(recall_score(y, pred)), brier=float(brier_score_loss(y, p)),
                rec10=float(rec10), lift10=float(lift10), prec10=float(prec10))

def ks_stat(y, p):
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(tpr - fpr))

def delong(y, p1, p2):
    """DeLong 检验：两个 AUC 的差异显著性"""
    pos, neg = p1[y == 1], p1[y == 0]
    qpos, qneg = p2[y == 1], p2[y == 0]
    m, n = len(pos), len(neg)
    def midrank(x):
        r = stats.rankdata(np.concatenate([x, np.concatenate([pos, neg])]))
        return r[:len(x)]
    def comp(z, other):
        return np.array([(z > o).mean() + 0.5 * (z == o).mean() for o in other])
    v10 = comp(pos, neg); v01 = comp(qpos, qneg)
    s10 = v10.mean(); s01 = v01.mean()
    cov = np.cov(np.vstack([v10, v01]))
    var = (cov[0, 0] / m + cov[1, 1] / n) / 2
    z = (s10 - s01) / np.sqrt(max(var, 1e-12))
    return float(2 * (1 - stats.norm.cdf(abs(z)))), float(s10), float(s01)

def build_models():
    return {
        "LR": Pipeline([("sc", StandardScaler()),
                        ("clf", LogisticRegression(max_iter=3000, C=1.0, class_weight="balanced"))]),
        "RF": RandomForestClassifier(n_estimators=600, max_depth=8, min_samples_leaf=5,
                                     class_weight="balanced_subsample", n_jobs=-1, random_state=RNG),
        "HGB": HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06, max_depth=6,
                                             l2_regularization=1.0, random_state=RNG),
        "XGB": xgb.XGBClassifier(n_estimators=600, learning_rate=0.05, max_depth=4,
                                subsample=0.8, colsample_bytree=0.8, reg_lambda=1.5,
                                eval_metric="auc", n_jobs=6, random_state=RNG),
        "LGBM": lgb.LGBMClassifier(n_estimators=600, learning_rate=0.05, num_leaves=15,
                                  min_child_samples=20, subsample=0.8, colsample_bytree=0.8,
                                  reg_lambda=1.0, n_jobs=6, random_state=RNG, verbose=-1),
    }

def tune(name, X, y, n_trials=30):
    skf = StratifiedKFold(3, shuffle=True, random_state=RNG)
    def obj(t):
        if name == "XGB":
            m = xgb.XGBClassifier(
                n_estimators=t.suggest_int("n_estimators", 200, 900, step=100),
                learning_rate=t.suggest_float("learning_rate", 0.02, 0.15, log=True),
                max_depth=t.suggest_int("max_depth", 3, 7),
                subsample=t.suggest_float("subsample", 0.6, 1.0),
                colsample_bytree=t.suggest_float("colsample_bytree", 0.5, 1.0),
                reg_lambda=t.suggest_float("reg_lambda", 0.5, 10, log=True),
                min_child_weight=t.suggest_int("min_child_weight", 1, 10),
                eval_metric="auc", n_jobs=6, random_state=RNG)
        else:
            m = lgb.LGBMClassifier(
                n_estimators=t.suggest_int("n_estimators", 200, 900, step=100),
                learning_rate=t.suggest_float("learning_rate", 0.02, 0.15, log=True),
                num_leaves=t.suggest_int("num_leaves", 7, 40, log=True),
                min_child_samples=t.suggest_int("min_child_samples", 10, 60),
                subsample=t.suggest_float("subsample", 0.6, 1.0),
                colsample_bytree=t.suggest_float("colsample_bytree", 0.5, 1.0),
                reg_lambda=t.suggest_float("reg_lambda", 0.5, 10, log=True),
                n_jobs=6, random_state=RNG, verbose=-1)
        scores = []
        for tr, va in skf.split(X, y):
            m.fit(X.iloc[tr], y[tr])
            scores.append(roc_auc_score(y[va], m.predict_proba(X.iloc[va])[:, 1]))
        return float(np.mean(scores))
    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RNG))
    st.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    return st.best_params, st.best_value

if __name__ == "__main__":
    X, y = load()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=RNG)
    res = {"n_train": len(Xtr), "n_test": len(Xte), "pos_train": int(ytr.sum()), "pos_test": int(yte.sum())}

    res["tuning"] = {}
    models = build_models()
    for name in ["XGB", "LGBM"]:
        bp, bv = tune(name, Xtr, ytr)
        res["tuning"][name] = {"best_params": bp, "cv_auc": bv}
        models[name].set_params(**bp)

    skf = StratifiedKFold(5, shuffle=True, random_state=RNG)
    stack = StackingClassifier(
        estimators=[("lr", models["LR"]), ("rf", models["RF"]), ("hgb", models["HGB"]),
                    ("xgb", models["XGB"]), ("lgbm", models["LGBM"])],
        final_estimator=LogisticRegression(max_iter=2000), cv=skf, n_jobs=1, passthrough=False)
    models["Stacking"] = stack

    oof = {}
    preds = {}
    for name, m in models.items():
        m.fit(Xtr, ytr)
        preds[name] = m.predict_proba(Xte)[:, 1]
        oof[name] = cross_val_predict(clone(m), Xtr, ytr, cv=skf, method="predict_proba", n_jobs=1)[:, 1]

    thr = {}
    for name in models:
        pr = precision_recall_curve(ytr, oof[name])
        f1s = 2 * pr[0] * pr[1] / np.clip(pr[0] + pr[1], 1e-9, None)
        thr[name] = float(pr[2][int(np.nanargmax(f1s[:-1]))])

    res["holdout"] = {}
    for name in models:
        mt = metrics(yte, preds[name], thr[name])
        mt["threshold"] = thr[name]
        n_boot = 1000
        aucs = []
        rng = np.random.default_rng(RNG)
        for _ in range(n_boot):
            idx = rng.integers(0, len(yte), len(yte))
            if len(np.unique(yte[idx])) < 2: continue
            aucs.append(roc_auc_score(yte[idx], preds[name][idx]))
        mt["auc_ci"] = [float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))]
        mt["cv_auc_mean"] = None
        res["holdout"][name] = mt

    cvres = {}
    for name in models:
        aucs, aps = [], []
        for tr, va in skf.split(Xtr, ytr):
            aucs.append(roc_auc_score(ytr[va], oof[name][va]))
            aps.append(average_precision_score(ytr[va], oof[name][va]))
        cvres[name] = {"auc_mean": float(np.mean(aucs)), "auc_std": float(np.std(aucs)),
                       "pr_mean": float(np.mean(aps)), "pr_std": float(np.std(aps))}
    res["cv"] = cvres

    best = max(res["holdout"], key=lambda k: res["holdout"][k]["auc"])
    res["best_model"] = best
    res["delong"] = {}
    for name in models:
        if name == best: continue
        z, a1, a2 = delong(yte, preds[best], preds[name])
        res["delong"][name] = {"p_value": z, "auc_best": a1, "auc_other": a2}

    imb = {}
    lgb_params = {k: v for k, v in res["tuning"]["LGBM"]["best_params"].items()}
    base = lgb.LGBMClassifier(**lgb_params, n_jobs=6, random_state=RNG, verbose=-1)
    base.fit(Xtr, ytr)
    imb["none"] = metrics(yte, base.predict_proba(Xte)[:, 1])
    cw = lgb.LGBMClassifier(**lgb_params, class_weight="balanced", n_jobs=6, random_state=RNG, verbose=-1)
    cw.fit(Xtr, ytr)
    imb["class_weight"] = metrics(yte, cw.predict_proba(Xte)[:, 1])
    sm = SMOTE(random_state=RNG, k_neighbors=5)
    Xs, ys = sm.fit_resample(Xtr, ytr)
    smm = lgb.LGBMClassifier(**lgb_params, n_jobs=6, random_state=RNG, verbose=-1).fit(Xs, ys)
    imb["smote"] = metrics(yte, smm.predict_proba(Xte)[:, 1])
    res["imbalance"] = imb

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
    abl = {"full": res["holdout"]["LGBM"]["auc"]}
    for gname, cols in groups.items():
        keep = [c for c in X.columns if c not in cols]
        m = lgb.LGBMClassifier(**lgb_params, n_jobs=6, random_state=RNG, verbose=-1).fit(Xtr[keep], ytr)
        abl["drop_" + gname] = float(roc_auc_score(yte, m.predict_proba(Xte[keep])[:, 1]))
    for gname, cols in groups.items():
        m = lgb.LGBMClassifier(**lgb_params, n_jobs=6, random_state=RNG, verbose=-1).fit(Xtr[cols], ytr)
        abl["only_" + gname] = float(roc_auc_score(yte, m.predict_proba(Xte[cols])[:, 1]))
    res["ablation"] = abl

    d10 = pd.read_csv(os.path.join(BASE, "data", "cohort2010.csv"), index_col=0)
    y10 = d10.pop("churn").values
    cross = {}
    for name in ["LR", "RF", "HGB", "XGB", "LGBM"]:
        m = build_models()[name]
        m.fit(X, y); p = m.predict_proba(d10[X.columns])[:, 1]
        cross[name] = {"train_2011_test_2010": float(roc_auc_score(y10, p))}
        m2 = build_models()[name]; m2.fit(d10[X.columns], y10)
        cross[name]["train_2010_test_2011"] = float(roc_auc_score(yte, m2.predict_proba(Xte)[:, 1]))
    res["cross_period"] = cross

    c_fp, c_fn = 20.0, 200.0
    cost = {}
    for name in [best, "LR"]:
        p = preds[name]
        grid = np.linspace(0.01, 0.99, 99)
        value = []
        for t in grid:
            pred = p >= t
            tp = int(((pred == 1) & (yte == 1)).sum()); fp = int(((pred == 1) & (yte == 0)).sum())
            value.append(int(tp) * c_fn - int(pred.sum()) * c_fp)
        value = np.array(value)
        imax = int(np.argmax(value))
        cost[name] = {"curve": {"threshold": grid.round(3).tolist(), "profit": value.round(1).tolist()},
                      "optimal_threshold": float(grid[imax]), "max_profit": float(value[imax]),
                      "profit_at_05": float(value[list(grid).index(min(grid, key=lambda g: abs(g - 0.5)))]),
                      "target_rate": float((p >= grid[imax]).mean()),
                      "recall": float(((p >= grid[imax]) & (yte == 1)).sum() / yte.sum())}
    n = len(yte)
    for rate in [0.1, 0.2, 0.3, 0.5]:
        k = int(rate * n)
        cost[f"random_{int(rate*100)}"] = {"profit": float(yte.sum() * rate * c_fn - k * c_fp)}
    cost["all"] = {"profit": float(yte.sum() * c_fn - n * c_fp)}
    res["cost"] = {"C_FN": c_fn, "C_FP": c_fp, **cost}
    sens = {}
    for v in [50, 100, 200, 400, 800]:
        best_v, best_t = -1e9, 0
        for t in np.linspace(0.01, 0.99, 99):
            pred = preds[best] >= t
            tp = int(((pred == 1) & (yte == 1)).sum())
            val = tp * v - int(pred.sum()) * c_fp
            if val > best_v: best_v, best_t = val, t
        sens[v] = {"profit": best_v, "threshold": float(best_t)}
    res["cost_sensitivity"] = sens

    cal = {}
    for name in [best, "LGBM", "LR"]:
        cal[name] = {"brier_raw": float(brier_score_loss(yte, preds[name]))}
    iso = CalibratedClassifierCV(lgb.LGBMClassifier(**lgb_params, n_jobs=6, random_state=RNG, verbose=-1),
                                method="isotonic", cv=5).fit(Xtr, ytr)
    p_iso = iso.predict_proba(Xte)[:, 1]
    cal["isotonic"] = {"brier_raw": float(brier_score_loss(yte, preds["LGBM"])),
                      "brier_iso": float(brier_score_loss(yte, p_iso)),
                      "auc_iso": float(roc_auc_score(yte, p_iso))}
    res["calibration"] = cal

    q = pd.qcut(Xte["monetary"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    seg = {}
    for name in [best]:
        for lab in ["Q1", "Q2", "Q3", "Q4"]:
            idx = (q == lab).values
            seg[lab] = {"n": int(idx.sum()), "churn": float(yte[idx].mean()),
                        "auc": float(roc_auc_score(yte[idx], preds[name][idx])),
                        "recall": float(((preds[name][idx] >= thr[name]) & (yte[idx] == 1)).sum() / max(1, yte[idx].sum()))}
    res["segment"] = seg

    np.savez(os.path.join(BASE, "results", "preds.npz"), y_test=yte, y_train=ytr,
             X_test=Xte.values, X_train=Xtr.values,
             feature_names=np.array(X.columns), thr=np.array([thr[k] for k in models]),
             model_names=np.array(list(models)), **{f"p_{k}": v for k, v in preds.items()},
             **{f"oof_{k}": v for k, v in oof.items()})
    Xte.assign(y=yte).to_csv(os.path.join(BASE, "results", "test_set.csv"))
    with open(os.path.join(BASE, "results", "metrics.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({k: res[k] for k in ["best_model", "tuning", "holdout", "cv", "ablation",
                                          "cross_period", "imbalance"]}, ensure_ascii=False, indent=2, default=str))
