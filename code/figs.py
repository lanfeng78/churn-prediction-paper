"""生成论文全部插图（灰度、单栏 8cm、600dpi）"""
import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score
from sklearn.calibration import calibration_curve

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "figs")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Noto Serif CJK SC"],
    "axes.unicode_minus": False,
    "font.size": 7,
    "axes.titlesize": 7,
    "axes.labelsize": 7,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6,
    "figure.dpi": 600,
    "savefig.dpi": 600,
    "axes.linewidth": 0.6,
    "grid.linewidth": 0.4,
    "grid.color": "#bbbbbb",
})
W, H = 3.15, 2.25   # 8cm 宽

def save(fig, name):
    fig.savefig(os.path.join(FIG, name), dpi=600, bbox_inches="tight", pad_inches=0.02,
                facecolor="white")
    plt.close(fig)

M = json.load(open(os.path.join(BASE, "results", "metrics.json")))
A = json.load(open(os.path.join(BASE, "results", "analysis2.json")))
DS = json.load(open(os.path.join(BASE, "results", "dataset_stats.json")))
d = np.load(os.path.join(BASE, "results", "preds.npz"), allow_pickle=True)
yte = d["y_test"]
names = list(d["model_names"])
preds = {n: d[f"p_{n}"] for n in names}
STY = {"LR": ("#111111", "--", "o"), "RF": ("#333333", "-.", "s"), "HGB": ("#555555", ":", "^"),
       "XGB": ("#000000", "-", "D"), "LGBM": ("#777777", "-", "v"), "Stacking": ("#999999", "-.", "P")}

# ---------- 图1 技术路线 ----------
fig, ax = plt.subplots(figsize=(W, 2.55))
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
steps = [("原始交易日志\n(106.7万条)", 8.3), ("数据清洗\n去重·退货·缺失", 6.7),
         ("双窗口样本构造\n观察窗9个月/标签窗3个月", 5.1), ("特征工程\n7组31维行为特征", 3.5),
         ("模型训练与调优\n5类模型+堆叠集成", 1.9), ("评估与决策\n判别·校准·收益·解释", 0.3)]
for txt, y in steps:
    ax.add_patch(plt.Rectangle((2.2, y), 5.6, 1.15, facecolor="#efefef", edgecolor="#000000", lw=0.6))
    ax.text(5.0, y + 0.575, txt, ha="center", va="center")
for i in range(len(steps) - 1):
    y0 = steps[i][1]; y1 = steps[i + 1][1] + 1.15
    ax.annotate("", xy=(5.0, y1), xytext=(5.0, y0),
                arrowprops=dict(arrowstyle="-|>", color="#000000", lw=0.7, shrinkA=0, shrinkB=0))
ax.text(0.25, 7.0, "数据层", rotation=90, va="center", fontsize=6.5, color="#444444")
ax.text(0.25, 2.0, "决策层", rotation=90, va="center", fontsize=6.5, color="#444444")
save(fig, "fig1_pipeline.png")

# ---------- 图2 双窗口标签构造 ----------
fig, ax = plt.subplots(figsize=(W, 2.05))
ax.set_xlim(0, 12); ax.set_ylim(0, 5.2); ax.axis("off")
ax.add_patch(Rectangle((0.3, 2.0), 7.3, 2.3, facecolor="#e6e6e6", edgecolor="#000000", lw=0.6))
ax.add_patch(Rectangle((7.95, 2.0), 3.75, 2.3, facecolor="#ffffff", edgecolor="#000000", lw=0.9, hatch="//"))
ax.text(3.95, 3.95, "观察窗口 O", ha="center", va="center", fontsize=6.0)
ax.text(3.95, 3.3, "2010-10-01 — 2011-06-30", ha="center", va="center", fontsize=5.6)
ax.text(3.95, 2.65, "9 个月", ha="center", va="center", fontsize=5.6)
ax.text(9.82, 3.95, "标签窗口 L", ha="center", va="center", fontsize=5.8,
        bbox=dict(facecolor="white", edgecolor="none", pad=1.2))
ax.text(9.82, 3.3, "2011.07—09", ha="center", va="center", fontsize=5.6,
        bbox=dict(facecolor="white", edgecolor="none", pad=1.2))
ax.text(9.82, 2.65, "3 个月", ha="center", va="center", fontsize=5.6,
        bbox=dict(facecolor="white", edgecolor="none", pad=1.2))
ax.annotate("", xy=(7.95, 1.55), xytext=(0.3, 1.55),
            arrowprops=dict(arrowstyle="<|-|>", color="#000000", lw=0.6, shrinkA=0, shrinkB=0))
ax.text(3.95, 0.8, "特征提取区间（9 个月）", ha="center", fontsize=5.4)
ax.annotate("", xy=(11.7, 1.55), xytext=(7.95, 1.55),
            arrowprops=dict(arrowstyle="<|-|>", color="#000000", lw=0.6, shrinkA=0, shrinkB=0))
ax.text(9.9, 0.72, "判定复购\n无购买 → 流失", ha="center", fontsize=5.4, linespacing=1.35)
ax.plot([7.95, 7.95], [1.8, 4.5], color="#000000", lw=0.7, ls=":")
ax.text(8.1, 4.75, "预测起点 t$_0$", fontsize=5.6)
save(fig, "fig2_window.png")

# ---------- 图3 分组流失率 ----------
fig, axes = plt.subplots(1, 2, figsize=(W, 1.95))
for ax, key, xlab in [(axes[0], "churn_by_monetary", "累计消费四分位"),
                      (axes[1], "churn_by_tenure", "客户生命周期 / 天")]:
    dd = DS[key]
    k = list(dd.keys()); v = [dd[i] * 100 for i in k]
    bars = ax.bar(range(len(k)), v, color=["#111111", "#444444", "#777777", "#a5a5a5"][:len(k)],
                  edgecolor="black", linewidth=0.5, width=0.68)
    for i, val in enumerate(v):
        ax.text(i, val + 1.5, f"{val:.1f}", ha="center", fontsize=6)
    ax.set_xticks(range(len(k))); ax.set_xticklabels([str(i) for i in k])
    ax.set_xlabel(xlab); ax.set_ylim(0, max(v) * 1.18)
    ax.grid(axis="y", ls=":", lw=0.4)
    ax.set_axisbelow(True)
axes[0].set_ylabel("流失率 / %")
axes[0].set_title("(a) 按客户价值分层", fontsize=6.8)
axes[1].set_title("(b) 按生命周期分层", fontsize=6.8)
fig.tight_layout()
save(fig, "fig3_churn_segments.png")

# ---------- 图4 相关性热力图 ----------
X = pd.read_csv(os.path.join(BASE, "results", "test_set.csv"), index_col=0)
feats = [c for c in X.columns if c != "y"]
cor = X[feats + ["y"]].corr()
top = cor["y"].abs().drop("y").sort_values(ascending=False).head(11).index.tolist()
cm = cor.loc[top + ["y"], top + ["y"]].values
fig, ax = plt.subplots(figsize=(W, 2.5))
im = ax.imshow(cm, cmap="Greys", vmin=-1, vmax=1)
ax.set_xticks(range(len(top) + 1)); ax.set_yticks(range(len(top) + 1))
ax.set_xticklabels(top + ["churn"], rotation=60, ha="right", fontsize=5.6)
ax.set_yticklabels(top + ["churn"], fontsize=5.6)
cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
cb.ax.tick_params(labelsize=5.5)
save(fig, "fig4_corr.png")

# ---------- 图5 ROC ----------
fig, ax = plt.subplots(figsize=(W, 2.3))
ax.plot([0, 1], [0, 1], ls=":", color="#999999", lw=0.7)
for n in names:
    fpr, tpr, _ = roc_curve(yte, preds[n])
    auc = roc_auc_score(yte, preds[n])
    ax.plot(fpr, tpr, color=STY[n][0], ls=STY[n][1], lw=0.9, label=f"{n} ({auc:.3f})")
ax.set_xlabel("假正例率 FPR"); ax.set_ylabel("真正例率 TPR")
ax.legend(loc="lower right", frameon=False, handlelength=1.6, labelspacing=0.25)
ax.grid(ls=":", lw=0.4); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
save(fig, "fig5_roc.png")

# ---------- 图6 PR ----------
fig, ax = plt.subplots(figsize=(W, 2.3))
base = yte.mean()
ax.axhline(base, ls=":", color="#999999", lw=0.7)
for n in names:
    pr, rc, _ = precision_recall_curve(yte, preds[n])
    ap = M["holdout"][n]["pr_auc"]
    ax.plot(rc, pr, color=STY[n][0], ls=STY[n][1], lw=0.9, label=f"{n} ({ap:.3f})")
ax.text(0.55, base + 0.03, f"基线 {base:.3f}", fontsize=6, color="#666666")
ax.set_xlabel("召回率 Recall"); ax.set_ylabel("精确率 Precision")
ax.legend(loc="upper right", frameon=False, handlelength=1.6, labelspacing=0.25)
ax.grid(ls=":", lw=0.4); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
save(fig, "fig6_pr.png")

# ---------- 图7 累计增益 ----------
fig, ax = plt.subplots(figsize=(W, 2.25))
for n in ["XGB", "LR"]:
    s = np.argsort(-preds[n]); cum = np.cumsum(yte[s]) / yte.sum()
    ax.plot(np.arange(1, len(yte) + 1) / len(yte), cum, color=STY[n][0], ls=STY[n][1], lw=0.9, label=n)
ax.plot([0, 1], [0, 1], ls=":", color="#999999", lw=0.7, label="随机")
ax.set_xlabel("累计触达客户比例"); ax.set_ylabel("累计捕获流失客户比例")
ax.legend(loc="lower right", frameon=False, handlelength=1.6)
ax.grid(ls=":", lw=0.4)
save(fig, "fig7_gain.png")

# ---------- 图8 校准曲线 ----------
fig, ax = plt.subplots(figsize=(W, 2.2))
ax.plot([0, 1], [0, 1], ls=":", color="#999999", lw=0.7, label="理想校准")
for n in ["XGB", "LGBM"]:
    fr, mp = calibration_curve(yte, preds[n], n_bins=8, strategy="quantile")
    ax.plot(mp, fr, color=STY[n][0], ls=STY[n][1], marker="o", ms=2.6, lw=0.8,
            label=f"{n} (Brier={M['holdout'][n]['brier']:.3f})")
ax.set_xlabel("预测流失概率"); ax.set_ylabel("实际流失比例")
ax.legend(loc="upper left", frameon=False, handlelength=1.6)
ax.grid(ls=":", lw=0.4)
save(fig, "fig8_calibration.png")

# ---------- 图9 预算约束收益 ----------
fig, ax = plt.subplots(figsize=(W, 2.25))
c = A["budget"]["curve"]
ax.plot(np.array(c["coverage"]) * 100, c["model"], color="#000000", lw=1.0, ls="-", label="模型排序触达")
ax.plot(np.array(c["coverage"]) * 100, c["random"], color="#888888", lw=0.9, ls="--", label="随机触达")
ax.axhline(0, color="#bbbbbb", lw=0.6, ls=":")
for cov in [0.1, 0.2, 0.3]:
    v = A["budget"]["at"][str(cov)]
    ax.annotate(f"{v['lift']:.2f}×", xy=(cov * 100, v["profit"]), xytext=(cov * 100 - 2, v["profit"] + 3500),
                fontsize=5.6, arrowprops=dict(arrowstyle="-", lw=0.4, color="#555555"))
ax.set_xlabel("触达比例 / %"); ax.set_ylabel("期望净收益")
ax.legend(loc="upper left", frameon=False, handlelength=1.6)
ax.grid(ls=":", lw=0.4)
save(fig, "fig9_budget.png")

# ---------- 图10 SHAP 蜂群 ----------
sv = np.load(os.path.join(BASE, "results", "shap_values.npy"))
Xte = pd.read_csv(os.path.join(BASE, "results", "X_test.csv"))
imp = pd.read_csv(os.path.join(BASE, "results", "shap_importance.csv"))
top = imp.head(10)["feature"].tolist()[::-1]
fig, ax = plt.subplots(figsize=(W, 2.3))
rng = np.random.default_rng(1)
for i, f in enumerate(top):
    v = sv[:, list(Xte.columns).index(f)]
    fv = Xte[f].values.astype(float)
    fv = (fv - fv.min()) / (fv.max() - fv.min() + 1e-9)
    yj = i + rng.uniform(-0.22, 0.22, len(v))
    sc = ax.scatter(v, yj, c=fv, cmap="Greys", s=2.6, edgecolors="#222222", linewidths=0.15, vmin=0, vmax=1)
ax.axvline(0, color="#000000", lw=0.6, ls=":")
ax.set_yticks(range(len(top))); ax.set_yticklabels(top, fontsize=6.4)
ax.set_xlabel("SHAP 值（对流失概率的贡献）")
cb = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02, ticks=[0, 1])
cb.ax.set_yticklabels(["低", "高"], fontsize=5.5)
save(fig, "fig10_shap.png")

# ---------- 图11 SHAP 依赖 ----------
fig, axes = plt.subplots(1, 2, figsize=(W, 1.85))
for ax, f in zip(axes, ["late_orders", "recency"]):
    j = list(Xte.columns).index(f)
    x = Xte[f].values
    ax.scatter(x, sv[:, j], c="#666666", s=1.6, edgecolors="none", alpha=0.55)
    ax.axhline(0, color="#000000", lw=0.5, ls=":")
    ax.set_xlabel(f); ax.set_ylabel("SHAP 值")
    ax.grid(ls=":", lw=0.35)
axes[0].set_title("(a) 近三月订单数", fontsize=6.5)
axes[1].set_title("(b) 最近购买间隔", fontsize=6.5)
fig.tight_layout()
save(fig, "fig11_dependence.png")

# ---------- 图12 消融 ----------
abl = A["ablation_cv"]
full = abl["full"][0]
gs = ["RFM核心", "消费强度", "购买节奏", "趋势变化", "结构多样性", "退货行为", "时间偏好"]
drop = [abl["drop_" + g][0] - full for g in gs]
only = [abl["only_" + g][0] - full for g in gs]
fig, ax = plt.subplots(figsize=(W, 2.35))
x = np.arange(len(gs)); wd = 0.36
ax.bar(x - wd / 2, drop, wd, color="#222222", edgecolor="black", lw=0.4, label="剔除该组")
ax.bar(x + wd / 2, only, wd, color="#bbbbbb", edgecolor="black", lw=0.4, label="仅用该组")
ax.axhline(0, color="black", lw=0.5)
ax.set_xticks(x); ax.set_xticklabels(gs, rotation=32, ha="right", fontsize=6)
ax.set_ylabel("ΔAUC（相对全特征）")
ax.legend(frameon=False, loc="lower left", handlelength=1.4)
ax.grid(axis="y", ls=":", lw=0.4); ax.set_axisbelow(True)
save(fig, "fig12_ablation.png")

# ---------- 图13 跨期泛化 ----------
cross = M["cross_period"]
ms = ["LR", "RF", "HGB", "XGB", "LGBM"]
v1 = [cross[m]["train_2011_test_2010"] for m in ms]
v2 = [cross[m]["train_2010_test_2011"] for m in ms]
fig, ax = plt.subplots(figsize=(W, 2.1))
x = np.arange(len(ms)); wd = 0.35
ax.bar(x - wd / 2, v1, wd, color="#222222", edgecolor="black", lw=0.4, label="2011训练→2010测试")
ax.bar(x + wd / 2, v2, wd, color="#bbbbbb", edgecolor="black", lw=0.4, label="2010训练→2011测试")
for i, (a1, a2) in enumerate(zip(v1, v2)):
    ax.text(i - wd / 2, a1 + 0.004, f"{a1:.3f}", ha="center", fontsize=5.2, rotation=90, va="bottom")
    ax.text(i + wd / 2, a2 + 0.004, f"{a2:.3f}", ha="center", fontsize=5.2, rotation=90, va="bottom")
ax.set_xticks(x); ax.set_xticklabels(ms, fontsize=6.5)
ax.set_ylabel("AUC"); ax.set_ylim(0.6, 0.85)
ax.legend(frameon=False, loc="upper left", fontsize=5.2, handlelength=1.2, ncol=1)
ax.grid(axis="y", ls=":", lw=0.4); ax.set_axisbelow(True)
save(fig, "fig13_cross.png")

# ---------- 图14 阈值—收益曲线 ----------
cost = M["cost"]
fig, ax = plt.subplots(figsize=(W, 2.05))
for n, ls in [("XGB", "-"), ("LR", "--")]:
    cv = cost[n]["curve"]
    ax.plot(cv["threshold"], cv["profit"], color="#000000" if n == "XGB" else "#888888", ls=ls, lw=0.9, label=n)
ax.set_xlabel("判定阈值"); ax.set_ylabel("测试集净收益")
ax.legend(frameon=False, loc="upper right", handlelength=1.6)
ax.grid(ls=":", lw=0.4)
save(fig, "fig14_threshold.png")

# ---------- 图15 模型综合指标 ----------
ms2 = ["LR", "RF", "HGB", "XGB", "LGBM", "Stacking"]
metric_keys = [("auc", "AUC"), ("pr_auc", "PR-AUC"), ("ks", "KS"), ("f1", "F1")]
fig, ax = plt.subplots(figsize=(W, 2.2))
x = np.arange(len(ms2)); wd = 0.2
for i, (k, lab) in enumerate(metric_keys):
    vals = [M["holdout"][m][k] for m in ms2]
    ax.bar(x + (i - 1.5) * wd, vals, wd, label=lab,
           color=["#111111", "#555555", "#999999", "#cccccc"][i], edgecolor="black", lw=0.35)
ax.set_xticks(x); ax.set_xticklabels(ms2, fontsize=6.2)
ax.set_ylim(0, 0.85); ax.set_ylabel("指标取值")
ax.legend(frameon=False, ncol=4, loc="upper center", fontsize=5.6, handlelength=1.0, columnspacing=1.0)
ax.grid(axis="y", ls=":", lw=0.4); ax.set_axisbelow(True)
save(fig, "fig15_metrics.png")
print("figures done:", sorted(os.listdir(FIG)))
