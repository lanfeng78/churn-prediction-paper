"""Online Retail II -> 客户流失建模数据集构造"""
import json, os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "retail_ii.csv")

def load_raw():
    df = pd.read_csv(RAW, dtype={"Invoice": str, "StockCode": str}, parse_dates=["InvoiceDate"])
    df["Customer ID"] = pd.to_numeric(df["Customer ID"], errors="coerce")
    return df

def clean_funnel(df):
    stats = {}
    stats["raw_rows"] = int(len(df))
    stats["raw_customers"] = int(df["Customer ID"].nunique(dropna=True))
    d1 = df.dropna(subset=["Customer ID"])
    stats["after_custid"] = int(len(d1)); stats["drop_custid"] = int(len(df) - len(d1))
    d2 = d1[d1["Price"] > 0]
    stats["after_price"] = int(len(d2)); stats["drop_price"] = int(len(d1) - len(d2))
    d3 = d2.drop_duplicates(subset=["Invoice", "StockCode", "Quantity", "InvoiceDate", "Price", "Customer ID"])
    stats["after_dup"] = int(len(d3)); stats["drop_dup"] = int(len(d2) - len(d3))
    d4 = d3.copy()
    d4["is_cancel"] = d4["Invoice"].str.upper().str.startswith("C")
    d4["is_return"] = (~d4["is_cancel"]) & (d4["Quantity"] < 0)
    stats["cancel_rows"] = int(d4["is_cancel"].sum())
    stats["return_rows"] = int(d4["is_return"].sum())
    stats["date_min"] = str(d4["InvoiceDate"].min()); stats["date_max"] = str(d4["InvoiceDate"].max())
    stats["n_invoices"] = int(d4["Invoice"].nunique())
    stats["n_skus"] = int(d4["StockCode"].nunique())
    stats["n_countries"] = int(d4["Country"].nunique())
    return d4, stats

def build_cohort(d, o_start, o_end, l_end, name):
    o = d[(d["InvoiceDate"] >= o_start) & (d["InvoiceDate"] < o_end)]
    l = d[(d["InvoiceDate"] >= o_end) & (d["InvoiceDate"] < l_end)]
    pur = o[(o["Quantity"] > 0) & (~o["is_cancel"])]
    ret = o[o["is_cancel"] | (o["Quantity"] < 0)]
    buyers = pur.groupby("Customer ID").agg(
        n_inv=("Invoice", "nunique"),
        qty=("Quantity", "sum"),
        amount=("amount", "sum"),
    )
    buyers = buyers[buyers["n_inv"] >= 2]          # 至少2笔订单，保证行为特征可观测
    keep = buyers.index
    pur = pur[pur["Customer ID"].isin(keep)]
    ret = ret[ret["Customer ID"].isin(keep)]
    lab_buyers = set(l[l["Quantity"] > 0]["Customer ID"].dropna().unique())
    y = pd.Series([0 if c in lab_buyers else 1 for c in keep], index=keep, name="churn")

    g = pur.groupby("Customer ID")
    inv = pur.groupby(["Customer ID", "Invoice"]).agg(amount=("amount", "sum"),
                                                      qty=("Quantity", "sum"),
                                                      t=("InvoiceDate", "min")).reset_index()
    ci = inv.groupby("Customer ID")
    feat = pd.DataFrame(index=keep)
    feat["recency"] = (o_end - g["InvoiceDate"].max()).dt.days
    feat["frequency"] = g["Invoice"].nunique()
    feat["monetary"] = g["amount"].sum()
    feat["aov"] = feat["monetary"] / feat["frequency"]
    feat["items_per_order"] = g["Quantity"].sum() / feat["frequency"]
    feat["n_sku"] = g["StockCode"].nunique()
    feat["unit_price_mean"] = g["amount"].sum() / g["Quantity"].sum()
    feat["max_order_amount"] = ci["amount"].max()
    feat["median_order_amount"] = ci["amount"].median()
    feat["std_order_amount"] = ci["amount"].std().fillna(0)
    feat["amount_cv"] = (feat["std_order_amount"] / feat["aov"]).replace([np.inf, -np.inf], 0).fillna(0)
    feat["first_purchase_gap"] = (g["InvoiceDate"].min().sub(pd.Timestamp(o_start)).dt.days)
    feat["tenure_days"] = (g["InvoiceDate"].max() - g["InvoiceDate"].min()).dt.days + 1
    active_months = pur.groupby("Customer ID")["InvoiceDate"].apply(lambda s: s.dt.to_period("M").nunique())
    feat["active_month_ratio"] = (active_months.reindex(keep) /
                                  np.maximum(1, np.ceil(feat["tenure_days"] / 30.0))).clip(upper=1)

    # 购买间隔
    iv = inv.sort_values(["Customer ID", "t"])[["Customer ID", "t"]]
    iv["gap"] = iv.groupby("Customer ID")["t"].diff().dt.days
    gg = iv.groupby("Customer ID")["gap"]
    feat["gap_mean"] = gg.mean()
    feat["gap_std"] = gg.std().fillna(0)
    feat["gap_cv"] = (feat["gap_std"] / feat["gap_mean"]).replace([np.inf, -np.inf], 0).fillna(0)
    feat["max_dark_gap"] = gg.max().fillna(0)

    # 趋势特征：前后三个月对比
    mid = o_start + (o_end - o_start) / 2
    early = pur[pur["InvoiceDate"] < mid].groupby("Customer ID")["Invoice"].nunique()
    late = pur[pur["InvoiceDate"] >= mid].groupby("Customer ID")["Invoice"].nunique()
    feat["early_orders"] = early.reindex(keep).fillna(0)
    feat["late_orders"] = late.reindex(keep).fillna(0)
    feat["trend_ratio"] = (feat["late_orders"] + 1) / (feat["early_orders"] + 1)
    # 月度订单量线性斜率（标准化）
    mth = pur.copy(); mth["m"] = mth["InvoiceDate"].dt.month
    mo = mth.groupby(["Customer ID", "m"])["Invoice"].nunique().unstack(fill_value=0).reindex(keep).fillna(0)
    x = np.arange(mo.shape[1]); xc = x - x.mean()
    slope = (mo.values * xc).sum(1) / (xc ** 2).sum()
    feat["month_slope"] = slope / (mo.values.mean(1) + 1e-6)

    # 价格带多样性熵
    pur2 = pur.copy()
    bins = pd.qcut(pur2["Price"], 4, labels=False, duplicates="drop")
    pur2["pb"] = bins.values
    amt = pur2.groupby(["Customer ID", "pb"])["amount"].sum()
    tot = amt.groupby("Customer ID").transform("sum")
    p = (amt / tot).clip(lower=1e-9)
    ent = (-(p * np.log(p)).groupby("Customer ID").sum()) / np.log(4)
    feat["price_entropy"] = ent.reindex(keep).fillna(0)

    # 复购商品占比
    sku = pur.groupby(["Customer ID", "StockCode"]).size()
    feat["repeat_sku_ratio"] = (sku[(sku >= 2)].groupby("Customer ID").size() /
                                sku.groupby("Customer ID").size()).reindex(keep).fillna(0)

    # 退货行为
    rq = g["Quantity"].sum()
    feat["return_qty_ratio"] = (-ret.groupby("Customer ID")["Quantity"].sum() /
                                rq.replace(0, np.nan)).reindex(keep).fillna(0).clip(0, 5)
    feat["has_return"] = ret.groupby("Customer ID").size().reindex(keep).fillna(0).gt(0).astype(int)

    # 时间偏好
    feat["weekend_ratio"] = (pur[pur["InvoiceDate"].dt.dayofweek >= 5].groupby("Customer ID")["Invoice"].nunique() /
                             feat["frequency"]).reindex(keep).fillna(0)
    hr = pur["InvoiceDate"].dt.hour
    feat["working_hour_ratio"] = (pur[(hr >= 9) & (hr <= 18)].groupby("Customer ID")["Invoice"].nunique() /
                                  feat["frequency"]).reindex(keep).fillna(0)
    feat["is_uk"] = pur.groupby("Customer ID")["Country"].agg(lambda s: int((s == "United Kingdom").mode().iloc[0]))

    # 订单金额增长
    last_m = pur[pur["InvoiceDate"] >= o_end - pd.Timedelta(days=30)].groupby("Customer ID")["amount"].sum()
    first_m = pur[pur["InvoiceDate"] < o_start + pd.Timedelta(days=30)].groupby("Customer ID")["amount"].sum()
    feat["recent30_amount_ratio"] = (last_m.reindex(keep).fillna(0) / feat["monetary"]).clip(0, 1)
    feat["month_amount_growth"] = ((last_m.reindex(keep).fillna(0) + 1) /
                                   (first_m.reindex(keep).fillna(0) + 1))

    feat = feat.replace([np.inf, -np.inf], np.nan)
    feat = feat.fillna(feat.median(numeric_only=True))
    feat["churn"] = y
    feat["cohort"] = name
    return feat, stats_cohort(pur, ret, y, name)

def stats_cohort(pur, ret, y, name):
    return {
        "cohort": name,
        "customers": int(len(y)),
        "churn_rate": float(y.mean()),
        "orders": int(pur["Invoice"].nunique()),
        "amount": float(pur["amount"].sum()),
        "rows": int(len(pur)),
        "return_rows": int(len(ret)),
        "avg_orders": float(pur.groupby("Customer ID")["Invoice"].nunique().mean()),
        "avg_amount": float(pur.groupby("Customer ID")["amount"].sum().mean()),
        "median_amount": float(pur.groupby("Customer ID")["amount"].sum().median()),
    }

if __name__ == "__main__":
    df = load_raw()
    d, stats = clean_funnel(df)
    d["amount"] = d["Quantity"] * d["Price"]

    f11, s11 = build_cohort(d, pd.Timestamp("2010-10-01"), pd.Timestamp("2011-07-01"),
                            pd.Timestamp("2011-10-01"), "2011H1")
    f10, s10 = build_cohort(d, pd.Timestamp("2009-12-01"), pd.Timestamp("2010-09-01"),
                            pd.Timestamp("2010-12-01"), "2010H1")
    f11.drop(columns=["cohort"]).to_csv(os.path.join(BASE, "data", "cohort2011.csv"))
    f10.drop(columns=["cohort"]).to_csv(os.path.join(BASE, "data", "cohort2010.csv"))
    stats["cohort2011"] = s11; stats["cohort2010"] = s10
    stats["n_features"] = int(f11.shape[1] - 1)
    # 分群流失率
    q = pd.qcut(f11["monetary"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    stats["churn_by_monetary"] = f11.groupby(q, observed=True)["churn"].mean().round(4).to_dict()
    t = pd.cut(f11["tenure_days"], [0, 30, 90, 180, 10000], labels=["<30", "30-90", "90-180", ">180"])
    stats["churn_by_tenure"] = f11.groupby(t, observed=True)["churn"].mean().round(4).to_dict()
    stats["feature_cols"] = list(f11.columns[:-1])
    with open(os.path.join(BASE, "results", "dataset_stats.json"), "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({k: v for k, v in stats.items() if k != "feature_cols"}, ensure_ascii=False, indent=2, default=str))
