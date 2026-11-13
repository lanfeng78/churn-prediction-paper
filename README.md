# 基于双窗口行为特征与集成学习的电商客户流失预测

《数据科学与大数据综合实验设计》课程论文 —— 代码、结果与图表复现仓库。

- 作者：申奥（SHEN Ao），华南师范大学 数据科学与工程学院，23 级大数据 2 班
- 学号：20238131012　指导教师：陈纪龙
- 论文题目：基于双窗口行为特征与集成学习的电商客户流失预测

## 研究概要

电商属非合约场景，客户流失没有显式取消事件，只能由长期无购买推断。本文构建
**观察窗口（9 个月）+ 标签窗口（3 个月）分离的双窗口样本生成方法**，在 UCI
Online Retail II 的 1 067 371 条真实交易记录上提取 7 组 31 维行为特征，比较
逻辑回归、随机森林、直方图梯度提升、XGBoost、LightGBM 与堆叠集成，并完成
Optuna 调参、不平衡处理、特征消融、跨期泛化、概率校准、预算约束收益、
SHAP 解释与客群分层等 9 组实验。

## 数据

原始数据来自 UCI Machine Learning Repository 的 **Online Retail II**（公开数据集），
本仓库不附带 91 MB 原始 CSV，请先执行：

```bash
python data/download_data.py     # 下载到 data/retail_ii.csv
```

脚本使用 Hugging Face 镜像（`attik/Online-Retail-II-UCI`），UCI 原站直连存在限速。

## 复现流程

```bash
pip install -r requirements.txt

python code/build_dataset.py   # 清洗 + 双窗口样本 + 31 维特征 -> data/cohort*.csv
python code/model.py           # Optuna 调参、五折堆叠、留出集评估 -> results/metrics.json
python code/analysis.py        # 消融/跨期/校准/代价收益/分层 -> results/analysis2.json
python code/figs.py            # 15 幅灰度插图 -> figs/
python code/build_paper.py     # 按附件格式生成 Word -> 论文 docx
```

## 主要结果（均来自实际运行）

| 模型 | AUC | 95% CI | PR-AUC | KS | Brier |
|---|---|---|---|---|---|
| 逻辑回归 | 0.738 7 | 0.701 7~0.775 1 | 0.653 2 | 0.389 2 | 0.210 9 |
| 随机森林 | 0.758 2 | 0.723 0~0.792 0 | 0.676 7 | 0.395 4 | 0.199 7 |
| 直方图梯度提升 | 0.745 2 | 0.709 2~0.782 4 | 0.666 9 | 0.405 2 | 0.221 0 |
| XGBoost | **0.760 8** | 0.725 5~0.794 9 | **0.684 6** | 0.392 4 | 0.196 8 |
| LightGBM | 0.760 4 | 0.725 6~0.794 4 | 0.675 4 | 0.395 6 | 0.197 1 |
| 堆叠集成 | 0.753 6 | 0.718 0~0.788 5 | 0.676 1 | 0.400 5 | 0.200 3 |

样本：主样本 2 327 名客户（1 628 / 699 训练测试切分），流失率 43.36%；
对照样本 2 037 名客户，流失率 29.46%。

其他结论：趋势类特征单独使用即可达 AUC 0.771 5；10% 触达预算下命中率
74.29%、相对随机提升 1.71 倍；跨期 AUC 下降 0.03~0.06，主因是基率漂移。

## 目录结构

```
code/       建模与出图脚本（build_dataset / model / analysis / figs / build_paper）
data/       数据下载脚本与派生样本（原始 CSV 不入库）
results/    指标 JSON、重要度 CSV 等可核查结果
figs/       论文 15 幅灰度插图
```

## 许可

仅用于课程学习与复现交流。
