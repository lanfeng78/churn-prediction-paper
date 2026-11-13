# -*- coding: utf-8 -*-
"""生成课程论文 Word 文档：封面 + 单栏题名摘要 + 双栏正文"""
import os, copy
import docx
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "figs")
TPL = "/home/user/.doubao/agent_mode/workspace/.sessions/38453638782544642/attachments/说明书或论文的封面.docx"
OUT = os.path.join(BASE, "数据科学与大数据综合实验设计_论文_申奥.docx")

TITLE = "基于双窗口行为特征与集成学习的电商客户流失预测"
TITLE_EN = "E-commerce Customer Churn Prediction Based on Dual-Window Behavioral Features and Ensemble Learning"
AUTHOR = "申奥"
AUTHOR_EN = "SHEN Ao"

doc = Document(TPL)
# ---------- 封面 ----------
FIELDS = {
    "题    目：": TITLE,
    "指导老师：": "陈纪龙",
    "学    号：": "20238131012",
    "姓    名：": "申奥",
    "班    级：": "23级大数据2班",
    "时    间：": "2026年11月13日",
}
for para in doc.paragraphs:
    t = para.text.strip()
    for lab, val in FIELDS.items():
        if t.startswith(lab.strip()):
            for r in list(para.runs):
                r._element.getparent().remove(r._element)
            r1 = para.add_run(lab)
            r1.font.name = "Times New Roman"; r1.font.size = Pt(14)
            r1._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "宋体")
            sz = 12 if lab == "题    目：" else 14
            r2 = para.add_run((" " if lab == "题    目：" else "　") + val + "　")
            r2.font.name = "Times New Roman"; r2.font.size = Pt(sz); r2.underline = True
            r2._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "宋体")

# 收紧封面底部空段，确保“学院”名称留在首页
_idx = None
for i, para in enumerate(doc.paragraphs):
    if para.text.strip().startswith("时    间") or para.text.strip().startswith("时 间"):
        _idx = i
if _idx is not None:
    for para in list(doc.paragraphs[_idx + 1:]):
        if para.text.strip() == "" or para.text.strip() == "   ":
            para._element.getparent().remove(para._element)
        else:
            break
for para in doc.paragraphs:
    if para.text.strip() == "数据科学与工程学院":
        para.paragraph_format.space_before = Pt(72)

def set_cn(run, cn="宋体", en="Times New Roman", size=9, bold=False, italic=False):
    run.font.name = en
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rPr.append(rf)
    rf.set(qn("w:ascii"), en); rf.set(qn("w:hAnsi"), en); rf.set(qn("w:eastAsia"), cn)

def par(text="", size=9, bold=False, cn="宋体", en="Times New Roman", align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        indent=True, before=0, after=0, spacing=1.12, keep=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.space_before = Pt(before); pf.space_after = Pt(after)
    pf.line_spacing = spacing
    if indent:
        pf.first_line_indent = Pt(size * 2)
    pf.keep_with_next = keep
    if text:
        r = p.add_run(text); set_cn(r, cn, en, size, bold)
    return p

def h1(text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(7); pf.space_after = Pt(3); pf.line_spacing = 1.1
    pf.keep_with_next = True
    r = p.add_run(text); set_cn(r, "黑体", "Times New Roman", 10.5)
    return p

def h2(text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(4); pf.space_after = Pt(2); pf.line_spacing = 1.1
    pf.keep_with_next = True
    r = p.add_run(text); set_cn(r, "黑体", "Times New Roman", 9, bold=True)
    return p

def h3(text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(3); pf.space_after = Pt(1); pf.line_spacing = 1.1
    pf.keep_with_next = True
    r = p.add_run(text); set_cn(r, "楷体", "Times New Roman", 9, bold=False)
    return p

def formula(segments, num, size=9):
    """segments: [(text, italic)]，居中并在右侧标注编号"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.space_before = Pt(3); pf.space_after = Pt(3); pf.line_spacing = 1.0
    pf.tab_stops.add_tab_stop(Cm(3.85), WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Cm(7.7), WD_TAB_ALIGNMENT.RIGHT)
    r = p.add_run("\t"); set_cn(r, "宋体", "Times New Roman", size)
    for txt, mode in segments:
        table_mode = {"i": (True, False, None), "ib": (True, True, None), "n": (False, False, None),
                      "sub": (False, False, "sub"), "sup": (False, False, "sup")}
        m = table_mode[mode] if isinstance(mode, str) else (mode, False, None)
        r = p.add_run(txt)
        set_cn(r, "宋体", "Times New Roman", size, italic=m[0], bold=m[1])
        if m[1] == "sub":
            r.font.subscript = True
        elif m[1] == "sup":
            r.font.superscript = True
    r = p.add_run("\t（%d）" % num); set_cn(r, "宋体", "Times New Roman", size)
    return p

def figure(fname, cn_cap, en_cap, width=7.6):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.space_before = Pt(4); pf.space_after = Pt(1); pf.line_spacing = 1.0
    pf.keep_with_next = True
    p.add_run().add_picture(os.path.join(FIG, fname), width=Cm(width))
    c1 = doc.add_paragraph(); c1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c1.paragraph_format.space_before = Pt(0); c1.paragraph_format.space_after = Pt(0)
    c1.paragraph_format.line_spacing = 1.0; c1.paragraph_format.keep_with_next = True
    r = c1.add_run(cn_cap); set_cn(r, "宋体", "Times New Roman", 7.5)
    c2 = doc.add_paragraph(); c2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c2.paragraph_format.space_before = Pt(0); c2.paragraph_format.space_after = Pt(4)
    c2.paragraph_format.line_spacing = 1.0
    r = c2.add_run(en_cap); set_cn(r, "宋体", "Times New Roman", 7.5)

def _cell_margins(tbl):
    tblPr = tbl._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, v in (("top", 18), ("left", 45), ("bottom", 18), ("right", 45)):
        el = OxmlElement("w:" + side); el.set(qn("w:w"), str(v)); el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)

def _borders(tbl):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0"); el.set(qn("w:color"), "000000")
        b.append(el)
    tblPr.append(b)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)

def table(cn_cap, en_cap, header, rows, widths, align_first_left=True, size=7):
    c1 = doc.add_paragraph(); c1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c1.paragraph_format.space_before = Pt(5); c1.paragraph_format.space_after = Pt(0)
    c1.paragraph_format.line_spacing = 1.0; c1.paragraph_format.keep_with_next = True
    r = c1.add_run(cn_cap); set_cn(r, "宋体", "Times New Roman", 7.5)
    c2 = doc.add_paragraph(); c2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c2.paragraph_format.space_before = Pt(0); c2.paragraph_format.space_after = Pt(2)
    c2.paragraph_format.line_spacing = 1.0; c2.paragraph_format.keep_with_next = True
    r = c2.add_run(en_cap); set_cn(r, "宋体", "Times New Roman", 7.5)

    t = doc.add_table(rows=len(rows) + 1, cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _borders(t); _cell_margins(t)
    total_tw = int(sum(widths) / 2.54 * 1440)
    tblW = OxmlElement("w:tblW"); tblW.set(qn("w:w"), str(total_tw)); tblW.set(qn("w:type"), "dxa")
    t._tbl.tblPr.append(tblW)
    grid = t._tbl.tblGrid
    for gc, w in zip(grid.gridCol_lst, widths):
        gc.set(qn("w:w"), str(int(w / 2.54 * 1440)))
    for j, w in enumerate(widths):
        for cell in t.columns[j].cells:
            cell.width = Cm(w)
    # 表头
    for j, h in enumerate(header):
        cell = t.rows[0].cells[j]
        cell.width = Cm(widths[j])
        p = cell.paragraphs[0]
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(h); set_cn(r, "宋体", "Times New Roman", size, bold=True)
        shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "F2F2F2")
        cell._tc.get_or_add_tcPr().append(shd)
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    # 数据
    for i, row in enumerate(rows, start=1):
        trPr = t.rows[i]._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit"); trPr.append(cs)
        for j, val in enumerate(row):
            cell = t.rows[i].cells[j]
            cell.width = Cm(widths[j])
            p = cell.paragraphs[0]
            p.paragraph_format.alignment = (WD_ALIGN_PARAGRAPH.LEFT if (j == 0 and align_first_left)
                                            else WD_ALIGN_PARAGRAPH.CENTER)
            p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(str(val)); set_cn(r, "宋体", "Times New Roman", size)
    for row in t.rows[:-1]:
        for cell in row.cells:
            for pp in cell.paragraphs:
                pp.paragraph_format.keep_with_next = True
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
    rr = p.add_run(""); rr.font.size = Pt(1)
    return t

# ================= 第 2 节：题名与摘要（单栏） =================
sec1 = doc.add_section(WD_SECTION.NEW_PAGE)
sec1.left_margin = Cm(2.4); sec1.right_margin = Cm(2.4)
sec1.top_margin = Cm(2.4); sec1.bottom_margin = Cm(2.4)
sec1.page_width = Cm(21); sec1.page_height = Cm(29.7)

p = doc.add_paragraph(); p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(6)
p.paragraph_format.line_spacing = 1.0
r = p.add_run(TITLE); set_cn(r, "黑体", "Times New Roman", 16)

p = doc.add_paragraph(); p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(8)
r = p.add_run(AUTHOR); set_cn(r, "宋体", "Times New Roman", 10.5, bold=True)

abs_cn = ("针对电商非合约场景缺乏显式流失事件、静态 RFM 特征难以刻画客户活跃度衰减的问题，"
          "构建观察窗口与标签窗口分离的样本生成方法，并以 UCI Online Retail II 数据集的 106.7 万条真实交易记录为基础，"
          "提取覆盖价值、强度、节奏、趋势、结构、退货与偏好 7 组共 31 维行为特征。在 2 327 名客户构成的样本上，"
          "采用贝叶斯超参数优化训练逻辑回归、随机森林、直方图梯度提升、XGBoost 与 LightGBM 五类模型，"
          "并以五折袋外预测构建堆叠集成。实验表明：XGBoost 在留出集上取得最优判别性能，AUC 为 0.760 8"
          "（95% 置信区间 0.725 5~0.794 9），PR-AUC 为 0.684 6，KS 为 0.392 4；堆叠集成在交叉验证中 AUC 达 0.787 9。"
          "在 10% 触达比例的预算约束下，模型可捕获 17.2% 的流失客户，相对随机触达提升 1.71 倍，"
          "期望净收益由 2 569 元提高至 6 900 元。消融实验显示，趋势类特征单独使用时 AUC 已达 0.771 5，"
          "与 RFM 核心组合后为 0.775 6；跨期验证的 AUC 下降 0.03~0.06，基率漂移是模型退化的主要原因。"
          "SHAP 分析表明，近三个月订单数、累计消费金额与最近购买间隔是主导因素。结果说明，"
          "时间加权的行为趋势特征比静态价值分层更能识别电商客户的流失倾向，而代价敏感阈值与分层运营是模型落地的关键。")

p = doc.add_paragraph(); pf = p.paragraph_format
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; pf.space_before = Pt(0); pf.space_after = Pt(2)
pf.line_spacing = 1.15; pf.first_line_indent = Pt(0)
r = p.add_run("摘　要　"); set_cn(r, "黑体", "Times New Roman", 9, bold=True)
r = p.add_run(abs_cn); set_cn(r, "宋体", "Times New Roman", 9)

p = doc.add_paragraph(); pf = p.paragraph_format
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; pf.space_before = Pt(0); pf.space_after = Pt(12)
pf.line_spacing = 1.1
r = p.add_run("关键词："); set_cn(r, "黑体", "Times New Roman", 9, bold=True)
r = p.add_run("客户流失预测；行为特征工程；梯度提升树；堆叠集成；SHAP 可解释性；代价敏感学习")
set_cn(r, "宋体", "Times New Roman", 9)

p = doc.add_paragraph(); p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(2)
p.paragraph_format.line_spacing = 1.0
r = p.add_run(TITLE_EN); set_cn(r, "宋体", "Times New Roman", 14, bold=True)

p = doc.add_paragraph(); p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(8)
r = p.add_run(AUTHOR_EN); set_cn(r, "宋体", "Times New Roman", 10.5)

abs_en = ("E-commerce platforms face a dilemma in which churn leaves no explicit cancellation signal, "
          "so that static RFM (recency, frequency, monetary) descriptors fail to capture the decay of customer activity. "
          "This paper develops a dual-window sampling procedure that strictly separates a nine-month observation window "
          "from a three-month label window, and extracts 31 behavioural features organised into seven groups: value, "
          "intensity, rhythm, trend, structure, return behaviour and temporal preference. Using 1 067 371 real transactions "
          "from the UCI Online Retail II dataset, a cohort of 2 327 customers is constructed with a churn rate of 43.36%. "
          "Five learners, namely logistic regression, random forest, histogram gradient boosting, XGBoost and LightGBM, "
          "are tuned by Bayesian optimisation, and a stacking ensemble is built from five-fold out-of-fold predictions. "
          "XGBoost achieves the best discriminative performance on the hold-out set, with an AUC of 0.760 8 "
          "(95% confidence interval 0.725 5 to 0.794 9), a PR-AUC of 0.684 6 and a KS statistic of 0.392 4, whereas the "
          "stacking ensemble reaches an AUC of 0.787 9 under cross-validation. Under a budget constraint that covers only "
          "10% of customers, the model captures 17.2% of churners, which is 1.71 times the random baseline, and raises the "
          "expected net revenue from 2 569 CNY to 6 900 CNY. Ablation experiments show that trend features alone attain an "
          "AUC of 0.771 5 and that the full feature set reaches 0.775 6, indicating that part of the RFM information is "
          "reconstructed by time-weighted descriptors. Cross-period validation degrades the AUC by 0.03 to 0.06, mainly "
          "because the base rate shifts from 29.46% to 43.36%. SHAP analysis identifies the number of orders in the last "
          "three months, the cumulative monetary value and the recency gap as the dominant factors. The results suggest that "
          "time-weighted behavioural trends are more informative than static value tiers for churn screening, while "
          "cost-sensitive thresholds and segment-specific operation policies are essential for practical deployment.")

p = doc.add_paragraph(); pf = p.paragraph_format
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; pf.space_before = Pt(0); pf.space_after = Pt(2)
pf.line_spacing = 1.06
r = p.add_run("Abstract　"); set_cn(r, "宋体", "Times New Roman", 9, bold=True)
r = p.add_run(abs_en); set_cn(r, "宋体", "Times New Roman", 9)

p = doc.add_paragraph(); pf = p.paragraph_format
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; pf.space_before = Pt(0); pf.space_after = Pt(6)
pf.line_spacing = 1.06
r = p.add_run("Keywords　"); set_cn(r, "宋体", "Times New Roman", 9, bold=True)
r = p.add_run("customer churn prediction; behavioural feature engineering; gradient boosting tree; "
              "stacking ensemble; SHAP interpretability; cost-sensitive learning")
set_cn(r, "宋体", "Times New Roman", 9)

# ================= 第 3 节：正文（双栏） =================
sec2 = doc.add_section(WD_SECTION.NEW_PAGE)
sec2.page_width = Cm(21); sec2.page_height = Cm(29.7)
sec2.left_margin = Cm(2.2); sec2.right_margin = Cm(2.2)
sec2.top_margin = Cm(2.2); sec2.bottom_margin = Cm(2.2)
sec2.header_distance = Cm(1.3); sec2.footer_distance = Cm(1.3)
cols = sec2._sectPr.find(qn("w:cols"))
if cols is None:
    cols = OxmlElement("w:cols"); sec2._sectPr.append(cols)
cols.set(qn("w:num"), "2"); cols.set(qn("w:space"), "425")
cols.set(qn("w:equalWidth"), "1")

# ---------- 1 引言 ----------
h1("1　引言")
par("随着线上零售竞争加剧，电商平台的获客成本持续攀升，而维系既有客户所投入的边际成本显著低于新客获取，"
    "客户留存已成为影响平台盈利能力的关键环节[1]。在订阅制业务中，客户退订即构成明确的流失事件；"
    "但在电商这类非合约场景中，客户无需办理任何解约手续便可停止购买，流失只能通过购买行为的长期沉寂间接推断[2]。"
    "这种“无事件”特征使流失标签的构造本身成为一项需要设计的研究问题：标签窗口过短会把季节性休眠误判为流失，"
    "过长则会使预测失去干预价值。")
par("准确识别即将流失的客户，一方面可使有限的营销预算集中于高风险人群，另一方面可避免对高活跃客户的过度打扰。"
    "然而电商流失预测面临四方面困难：其一，标签依赖观察窗口与预测窗口的划分，窗口长度直接改变正负样本比例；"
    "其二，可用于刻画客户行为的维度众多，价值、频次、节奏与趋势彼此相关，累计指标难以反映活跃度的衰减过程；"
    "其三，流失客户占比不高，类别不平衡会使以准确率为目标的模型退化为“全部判为留存”；"
    "其四，模型输出必须可解释、可执行，运营人员需要知道“为什么该客户会流失”以及“预算有限时应当优先联系谁”。")
par("针对上述问题，本文以 UCI 在线零售数据集 Online Retail II 的 106.7 万条真实交易记录为基础，"
    "构建观察窗口与标签窗口分离的样本生成方法，提取覆盖价值、强度、节奏、趋势、结构、退货与偏好 7 组共 31 维行为特征；"
    "在此基础上比较逻辑回归、随机森林、直方图梯度提升、XGBoost 与 LightGBM 五类模型，"
    "并以五折袋外预测构建堆叠集成，采用贝叶斯优化确定超参数。评估不局限于 AUC，还引入 KS、PR-AUC、Brier 分数、"
    "预算约束下的期望净收益、跨期泛化与分层鲁棒性五个视角，并使用 SHAP 方法解释特征贡献。")
par("实验结果表明：（1）XGBoost 在独立测试集上取得最优判别性能，AUC 为 0.760 8（95% 置信区间 0.725 5~0.794 9），"
    "PR-AUC 为 0.684 6，KS 为 0.392 4；（2）堆叠集成在交叉验证中 AUC 达到 0.787 9，但在留出集上与单模型差异不显著"
    "（p=0.599），说明在本样本规模下模型结构的边际收益有限；（3）在仅触达 10% 客户的预算约束下，"
    "模型可捕获 17.2% 的流失客户，相对随机投放提升 1.71 倍，期望净收益由 2 569 元升至 6 900 元；"
    "（4）消融实验显示趋势类特征单独使用即可达到 0.771 5 的 AUC，静态 RFM 特征的作用可被时间加权特征部分替代；"
    "（5）跨期验证中 AUC 下降 0.03~0.06，基率漂移是模型退化的主因。")
par("全文结构如下：第 2 节梳理客户流失预测的相关研究；第 3 节说明数据来源、样本构造与特征体系；"
    "第 4 节给出建模方法与评估设计；第 5 节报告实验结果并讨论；第 6 节总结全文并指出局限与后续方向。")

# ---------- 2 相关工作 ----------
h1("2　相关工作")
h2("2.1　客户流失预测的建模脉络")
par("客户流失预测早期以统计模型为主。Coussement 等[3]在订阅服务场景中比较了支持向量机与两种参数选择策略，"
    "发现非线性模型在小样本条件下并不稳定优于逻辑回归。Huang 等[4]在电信数据上系统比较了决策树、神经网络与集成方法，"
    "指出特征质量对结果的影响大于分类器选择。Verbeke 等[5]进一步引入利润驱动的评价框架，认为以准确率为优化目标会偏离业务目标，"
    "应以期望利润选择模型与阈值。Ahmad 等[6]将梯度提升树部署于大数据平台，验证了集成模型在百万级样本上的可扩展性。"
    "上述工作多以电信、银行等具备合约关系的场景为对象，客户解约行为有明确记录；而电商场景的流失是“沉默式”的，"
    "标签必须由行为窗口推断，相关研究相对较少。")
par("在非合约场景中，研究者多沿用 RFM 框架刻画客户价值，并结合 BG/NBD 等概率模型估计客户的存活概率[2]。"
    "这类方法假设购买间隔服从特定分布，对促销驱动的非平稳行为适应性有限。近年来，基于行为序列的深度模型"
    "（如循环神经网络、Transformer）被用于捕捉购买节奏的变化，但其参数规模大、可解释性弱，在样本量有限的场景中容易过拟合。")
par("从特征工程的角度看，非合约场景的流失研究大致经历三个阶段：以 RFM 为代表的静态汇总阶段、"
    "以购买间隔与生命周期为核心的节奏刻画阶段，以及以滑动窗口对比为手段的趋势建模阶段。"
    "静态汇总只回答“客户过去值多少”，节奏刻画回答“客户多久来一次”，趋势建模回答“客户是否正在变冷”。"
    "三者依次递进，但已有工作多停留在前两个阶段，对第三阶段的量化评估不足。")
h2("2.2　集成学习与不平衡处理")
par("集成学习是表格型流失预测的主流方案。Breiman[7]提出的随机森林通过样本与特征的双重随机化降低方差；"
    "Chen 等[8]提出的 XGBoost 在损失函数中引入一阶与二阶梯度信息并施加显式正则；"
    "Ke 等[9]提出的 LightGBM 采用直方图分裂与 leaf-wise 生长策略，在大规模稀疏特征上具有更高的训练效率。"
    "Wolpert[10]提出的堆叠泛化通过元学习器融合多个基学习器的输出，理论上可降低单一假设空间的偏差。")
par("类别不平衡是流失预测的固有难题。Chawla 等[11]提出的 SMOTE 通过近邻插值合成少数类样本，被广泛用于改善召回率。"
    "但已有研究表明，过采样在提升排序能力方面的作用有限，其主要效果是改变概率输出的位置，从而影响固定阈值下的精确率与召回率[5]。"
    "因此，代价敏感学习与阈值移动逐渐被视为更可靠的替代方案。")
h2("2.3　可解释性与评估体系")
par("在业务落地层面，模型的可解释性与判别能力同等重要。Lundberg 等[12]提出的 SHAP 基于博弈论的 Shapley 值，"
    "为每个特征分配可加性的贡献值，已成为表格模型解释的事实标准。超参数搜索方面，Akiba 等[13]提出的 Optuna "
    "采用树结构 Parzen 估计器进行贝叶斯优化，在相同预算下通常优于网格搜索。模型比较方面，DeLong 等[14]提出的非参数检验"
    "为相关 ROC 曲线的 AUC 差异提供了显著性判断依据。")
h2("2.4　研究空白与本文定位")
par("综合来看，现有研究存在三点不足：一是电商非合约场景下的标签构造缺乏统一规范，窗口长度对样本分布的影响少有量化讨论；"
    "二是多数工作以静态 RFM 特征为主，对购买节奏与趋势衰减的刻画不足；三是评估多停留在 AUC 等排序指标，"
    "缺少预算约束下的收益分析、跨期稳定性检验与分层鲁棒性分析。本文围绕这三点展开，主要贡献在于："
    "（1）给出可复现的双窗口样本构造流程，并量化两期样本的基率差异；（2）构建包含趋势与节奏的 31 维特征体系，"
    "通过消融实验识别各类特征的边际贡献；（3）在统一实验框架下同时报告判别、校准、收益、跨期与可解释性五类证据。")

# ---------- 3 数据与样本 ----------
h1("3　数据与样本构造")
h2("3.1　数据来源与清洗")
par("实验数据来自 UCI 机器学习库公开的 Online Retail II 数据集，记录了一家英国在线零售商 2009 年 12 月 1 日至"
    "2011 年 12 月 9 日的全部交易流水，共 1 067 371 条记录、5 942 名可识别客户、4 646 种商品与 44 870 张发票，"
    "客户分布于 41 个国家或地区。")
par("原始数据存在四类质量问题：客户编号缺失、价格非正、记录完全重复以及取消订单。清洗规则如下："
    "（1）剔除客户编号为空的记录，此类记录无法归属到具体个体，共 243 007 条，占 22.77%；"
    "（2）剔除单价小于等于 0 的记录 71 条；（3）按发票号、商品编码、数量、时间与价格五元组去重，剔除 26 480 条；"
    "（4）将发票号以“C”开头的记录识别为取消订单，共 18 390 条，此类记录不参与购买次数与金额统计，但用于计算退货率。"
    "清洗后保留 797 813 条有效记录。表 1 汇总了清洗过程。")
table("表1　数据集概况与清洗过程", "Table 1　Dataset overview and cleaning results",
      ["项目", "数量或取值"],
      [["原始交易记录", "1 067 371"], ["客户编号缺失记录", "243 007（22.77%）"],
       ["单价非正记录", "71"], ["完全重复记录", "26 480"], ["取消订单记录", "18 390"],
       ["清洗后有效记录", "797 813"], ["可识别客户", "5 942"], ["商品种类", "4 646"],
       ["发票数", "44 870"], ["国家或地区", "41"], ["时间跨度", "2009-12-01—2011-12-09"]],
      [3.7, 4.2])
par("需要说明的是，退货在原始数据中以负数量记录，其金额为负。为避免退货冲减导致消费金额失真，"
    "本文在计算金额类特征时仅使用正数量记录，退货行为单独作为一类特征刻画。")

h2("3.2　双窗口样本构造")
par("流失标签的构造依赖两个互不重叠的时间窗口：观察窗口用于提取特征，标签窗口用于判定客户是否留存。"
    "本文将观察窗口设为 9 个月、标签窗口设为 3 个月，如图 1 所示。选择 3 个月作为判定期的依据是："
    "该零售商的平均购买间隔约为 40 天，3 个月约为两个平均复购周期，若客户在此期间完全没有购买，可较有把握地判定为沉默客户。")
figure("fig2_window.png", "图1　双窗口样本构造示意", "Fig.1　Dual-window sample construction")
par("具体构造步骤如下：以预测起点 t0 为界，t0 之前 9 个月为观察窗口 O，t0 之后 3 个月为标签窗口 L。"
    "对在 O 内产生至少 2 笔有效订单的客户，提取其特征向量 x；若该客户在 L 内没有任何正数量交易，则标记为流失（y=1），"
    "否则标记为留存（y=0）。要求至少 2 笔订单的原因是：仅有一笔订单的客户无法计算购买间隔与趋势类特征，"
    "且此类客户多为一次性尝试者，其行为模式与复购客户存在本质差异。")
par("按上述规则，以 2011 年 7 月 1 日为预测起点构造的主样本包含 2 327 名客户、12 001 笔订单，交易总额 557.92 万元，"
    "人均消费 2 397.60 元，中位数 1 033.13 元，流失率 43.36%。为检验模型的跨期稳定性，以 2010 年 9 月 1 日为预测起点"
    "构造对照样本，包含 2 037 名客户、10 744 笔订单，交易总额 503.08 万元，流失率 29.46%。两期样本的基率相差 13.9 个百分点，"
    "主要原因是标签窗口所处的季节不同：2010 期标签窗口覆盖第四季度旺季，客户购买活跃；2011 期标签窗口位于夏季淡季，"
    "沉默比例更高。这一差异为后文的跨期实验提供了天然的分布偏移场景。表 2 列出两期样本的概况。")
table("表2　两期样本概况", "Table 2　Profiles of the two cohorts",
      ["指标", "2011 期（主样本）", "2010 期（对照样本）"],
      [["观察窗口", "2010-10—2011-06", "2009-12—2010-08"],
       ["标签窗口", "2011-07—2011-09", "2010-09—2010-11"],
       ["客户数", "2 327", "2 037"], ["订单数", "12 001", "10 744"],
       ["交易金额/万元", "557.92", "503.08"], ["人均消费/元", "2 397.60", "2 469.70"],
       ["流失率/%", "43.36", "29.46"]],
      [1.85, 3.0, 3.0])
par("图 2 给出主样本中流失率随客户价值与生命周期变化的分布。按累计消费金额四分位分组，流失率由最低组的 67.35% "
    "单调下降至最高组的 16.84%；按生命周期分组，注册不足 30 天的客户流失率高达 74.47%，而超过 180 天的老客户仅为 27.58%。"
    "这表明客户价值与关系长度对流失具有显著的分层效应，也提示单一全局阈值在不同客群上的适用性存在差异。")
figure("fig3_churn_segments.png", "图2　不同客群的流失率分布", "Fig.2　Churn rate by customer value and tenure")

h2("3.3　特征体系")
par("特征体系由 7 组共 31 维构成，如表 3 所示。全部特征仅使用观察窗口内的数据，且以预测起点 t0 为时间基准，"
    "确保与标签窗口严格隔离，避免未来信息泄漏。")
table("表3　行为特征体系", "Table 3　Feature system",
      ["组别（维数）", "代表特征", "刻画内容"],
      [["RFM 核心（4）", "recency、 frequency、 monetary", "客户价值与近期活跃水平"],
       ["消费强度（7）", "items_per_order、 n_sku 等", "购买规模与金额稳定性"],
       ["购买节奏（7）", "gap_mean、 gap_cv、 tenure_days", "复购间隔规律与活跃密度"],
       ["趋势变化（6）", "late_orders、 trend_ratio 等", "活跃度的方向与衰减速度"],
       ["结构多样性（2）", "price_entropy、 repeat_sku_ratio", "需求分散程度与转换成本"],
       ["退货行为（2）", "return_qty_ratio、 has_return", "履约质量与客户满意度"],
       ["时间偏好（3）", "weekend_ratio、 is_uk 等", "购买时点习惯与地域属性"]],
      [1.85, 3.4, 2.45], size=5.8)
par("（1）RFM 核心组。recency 为最近一次购买距 t0 的天数；frequency 为观察窗口内的不重复发票数；"
    "monetary 为累计消费金额；aov 为客单价，即 monetary 与 frequency 之比。recency 的计算如式（1）所示：")
formula([("R", "i"), (" = (", "n"), ("t", "i"), ("0", "sub"), (" − ", "n"), ("t", "i"), ("last", "sub"),
         (")/1 d", "n")], 1)
par("（2）消费强度组。包括单笔平均商品件数、不重复商品数、平均单价、最大单笔金额、单笔金额中位数、"
    "单笔金额标准差以及金额变异系数，用以刻画客户的购买规模与稳定性。")
par("（3）购买节奏组。以相邻发票的时间差构造购买间隔序列，统计其均值、标准差、变异系数与最大空档期；"
    "同时引入生命周期长度、首购距观察窗口起点的天数以及活跃月份占比，刻画客户的活跃密度。")
par("（4）趋势变化组。将观察窗口按中点划分为前后两段，计算后段与前段订单数之比 trend_ratio；"
    "以月度订单量对月份序号做最小二乘回归，取斜率除以月均订单数得到标准化趋势斜率 month_slope；"
    "并计算最近 30 天消费金额占总额之比与首末月金额增长比。该类特征直接刻画活跃度的方向与速度。")
par("（5）结构多样性组。将商品单价按四分位分箱，计算客户消费额在各价格带上的分布熵，如式（2）所示；"
    "并统计重复购买商品占全部商品的比例。熵值越高说明客户需求越分散，替换成本越低。")
formula([("H", "i"), (" = −(", "n"), ("Σ", "n"), ("k=1", "sub"), (")", "n"),
         ("p", "i"), ("k", "sub"), (" ln ", "n"), ("p", "i"), ("k", "sub"), (" / ln ", "n"), ("K", "i")], 2)
par("（6）退货行为组。退货率定义为取消订单的商品件数绝对值与正数量商品件数之比，并设置是否发生退货的二值指示。")
par("（7）时间偏好组。包括周末订单占比、工作时段（9 时至 18 时）订单占比以及是否为英国本土客户，"
    "用于刻画购买习惯的地域与时间特征。")
par("图 3 给出与流失标签相关性最强的 11 个特征及标签之间的相关系数矩阵。late_orders 与 recency 的相关系数为 −0.62，"
    "monetary 与 frequency 的相关系数为 0.78，说明价值与频次高度共线；late_orders 与 recency 呈显著负相关，"
    "二者从不同角度度量同一潜在变量——近期活跃度。这一观察为后文消融实验中 RFM 组可被替代的现象提供了直接证据。")
figure("fig4_corr.png", "图3　主要特征与流失标签的相关系数", "Fig.3　Correlation heatmap of top features")
par("在特征处理方面，树模型对单调变换不敏感，故未作归一化；逻辑回归使用 Z 分数标准化。"
    "对高度共线的特征（如 monetary 与 frequency），本文未作剔除，原因有二：树模型的分裂基于单特征阈值，"
    "共线性对其影响有限；剔除会削弱模型在单一维度缺失时的鲁棒性。作为对照，5.4 节的消融实验给出了"
    "剔除整组特征后的性能变化。此外，全部特征在构造时统一缺失值填补为中位数，避免个别缺失样本被整体丢弃。")

# ---------- 4 方法 ----------
h1("4　方法设计")
h2("4.1　整体框架")
par("整体流程如图 4 所示，分为数据层与决策层两部分。数据层完成清洗、样本构造与特征提取；"
    "决策层完成模型训练、超参数优化、集成融合、评估与业务决策。算法 1 给出可复现的执行流程。")
figure("fig1_pipeline.png", "图4　整体技术路线", "Fig.4　Overall framework of the proposed method")
par("本文未采用时间序列交叉验证，原因是样本在时间上仅有两期，滑动窗口会显著减少可用正例；"
    "跨期稳定性改由 5.5 节的两期互测实验检验。")
par("算法 1　双窗口样本构造与流失预测流程", size=9, bold=True, indent=False, before=3, after=1, keep=True)
alg = ["输入：交易流水 D，观察窗口长度 To，标签窗口长度 Tl",
       "输出：流失概率 p(x)，决策阈值 τ*",
       "1. 清洗 D：剔除缺失客户编号、非正价格与完全重复记录；",
       "2. 标记取消订单，分离购买记录与退货记录；",
       "3. 以预测起点 t0 划分 O=[t0−To, t0) 与 L=[t0, t0+Tl)；",
       "4. 对 O 内订单数不少于 2 的客户构造标签 y 与特征 x；",
       "5. 按 7:3 分层划分训练集与测试集，连续特征标准化；",
       "6. 以 TPE 搜索超参数，五折袋外预测训练元学习器；",
       "7. 在训练集袋外预测上按式（6）确定阈值 τ*；",
       "8. 在测试集计算 AUC、PR-AUC、KS、Brier 与前 k% 增益；",
       "9. 以 SHAP 计算特征贡献，按客群分层复核阈值；",
       "10. 输出模型、阈值与分层运营建议。"]
for line in alg:
    p = doc.add_paragraph(); pf = p.paragraph_format
    pf.space_before = Pt(0); pf.space_after = Pt(0); pf.line_spacing = 1.05
    pf.left_indent = Pt(12); pf.first_line_indent = Pt(-12)
    r = p.add_run(line); set_cn(r, "宋体", "Times New Roman", 8)

h2("4.2　基学习器")
par("为兼顾线性与非线性假设，本文选择五类基学习器。逻辑回归作为线性基准，输入经标准化处理，并以类别权重平衡正负样本，"
    "其输出形式如式（3）所示：")
formula([("p", "i"), ("(", "n"), ("y", "i"), (" = 1 | ", "n"), ("x", "i"), (") = 1 / (1 + exp(−(", "n"),
         ("w", "ib"), ("T", "sup"), ("x", "i"), (" + ", "n"), ("b", "i"), (")))", "n")], 3)
par("随机森林[7]通过自助采样训练多棵决策树并对概率取平均，对特征尺度不敏感，可作为稳健的树模型基准。"
    "直方图梯度提升对连续特征分箱后逐轮拟合负梯度，训练速度快，适合作为中等强度的对照。"
    "XGBoost[8]在目标函数中同时使用一阶与二阶梯度，并加入对叶子权重与树复杂度的正则项，其目标函数如式（4）所示：")
formula([("L", "i"), (" = ", "n"), ("Σ", "n"), ("i", "sub"), (" ", "n"), ("l", "i"), ("(", "n"),
         ("y", "i"), ("i", "sub"), (", ", "n"), ("ŷ", "i"), ("i", "sub"), (") + ", "n"), ("Σ", "n"),
         ("k", "sub"), (" ", "n"), ("Ω", "i"), ("(", "n"), ("f", "i"), ("k", "sub"), ("),   ", "n"),
         ("Ω", "i"), ("(", "n"), ("f", "i"), (") = ", "n"), ("γT", "i"), (" + (", "n"),
         ("λ", "i"), ("/2)", "n"), ("‖", "n"), ("w", "ib"), ("‖", "n"), ("2", "sup")], 4)
par("LightGBM[9]采用直方图算法与带深度限制的 leaf-wise 生长策略，并通过单边梯度采样减少样本量，"
    "在中小规模表格数据上通常具有与 XGBoost 相当的精度和更低的训练开销。上述模型的实现细节可参考相关教材[15-16]。")

h2("4.3　堆叠集成与概率校准")
par("堆叠泛化的核心是利用基学习器的袋外预测训练元学习器[10]。本文将训练集划分为 5 折，对每个基学习器在每折上训练"
    "并在留出折上预测，得到与训练集一一对应的袋外概率矩阵 Z；再以 Z 为输入、以真实标签为目标训练逻辑回归元学习器，"
    "其输出如式（5）所示：")
formula([("ŷ", "i"), (" = ", "n"), ("σ", "i"), ("(", "n"), ("Σ", "n"), ("m", "sub"), (" ", "n"),
         ("β", "i"), ("m", "sub"), (" ", "n"), ("p", "i"), ("m", "sub"), ("(", "n"), ("x", "i"),
         (") + ", "n"), ("β", "i"), ("0", "sub"), (")", "n")], 5)
par("元学习器选择逻辑回归而非树模型，是因其参数少、可解释性强，且在五折袋外概率矩阵上不易过拟合；"
    "若改用非线性元学习器，基模型输出之间的微小差异容易被放大为方差，反而削弱集成的稳定性。")
par("该做法保证元学习器看到的是基模型在未见样本上的输出，避免因基模型在训练集上过拟合而导致元学习器权重失真。"
    "为检验概率输出的可用性，本文同时使用等温回归对 LightGBM 的输出进行校准，并以 Brier 分数评价校准效果。")

h2("4.4　代价敏感决策")
par("判别指标最优并不等于业务收益最优。设漏判一名流失客户的代价为 CFN（损失的未来利润），"
    "误判一名留存客户并对其投放挽留资源的代价为 CFP（优惠与触达成本），则在阈值 τ 下的期望净收益如式（6）所示：")
formula([("Π", "i"), ("(", "n"), ("τ", "i"), (") = ", "n"), ("C", "i"), ("FN", "sub"), (" · ", "n"),
         ("TP", "i"), ("(", "n"), ("τ", "i"), (") − ", "n"), ("C", "i"), ("FP", "sub"), (" · ", "n"),
         ("N", "i"), ("t", "sub"), ("(", "n"), ("τ", "i"), (")", "n")], 6)
par("其中 TP(τ) 为被正确识别且成功挽留的流失客户数，Nt(τ) 为被触达的客户总数。对 τ 在 (0,1) 上搜索即可得到收益最优阈值。"
    "考虑到实际投放往往受预算上限约束，本文进一步在固定触达比例 k 下比较按模型概率排序与随机排序的收益差异，"
    "该场景更贴近运营实践。")

h2("4.5　评估指标")
par("本文从五个维度评价模型。排序能力采用 AUC 与 PR-AUC，AUC 定义为正负样本对中正例得分高于负例的比例，如式（7）所示；"
    "KS 统计正负样本累计分布的最大间距，如式（8）所示：")
formula([("AUC", "n"), (" = (1/", "n"), ("P", "i"), ("N", "i"), (") ", "n"), ("Σ", "n"),
         ("i∈P", "sub"), (" ", "n"), ("Σ", "n"), ("j∈N", "sub"), (" [", "n"), ("I", "i"),
         ("(", "n"), ("f", "i"), ("i", "sub"), (">", "n"), ("f", "i"), ("j", "sub"),
         (")+0.5", "n"), ("I", "i"), ("(", "n"), ("f", "i"), ("i", "sub"), ("=", "n"),
         ("f", "i"), ("j", "sub"), (")]", "n")], 7, size=8)
formula([("KS", "n"), (" = ", "n"), ("max", "n"), ("τ", "sub"), (" |", "n"), ("TPR", "n"),
         ("(", "n"), ("τ", "i"), (") − ", "n"), ("FPR", "n"), ("(", "n"), ("τ", "i"),
         (")|", "n")], 8)
par("概率质量采用 Brier 分数，即预测概率与真实标签之差的均方。业务价值采用前 k% 人群的命中率、召回率、"
    "提升倍数与期望净收益。模型间 AUC 差异采用 DeLong 检验[14]判断显著性，AUC 的置信区间由 1 000 次自助重采样估计。"
    "为避免单次划分的偶然性，同时报告五折交叉验证的均值与标准差。")

# ---------- 5 实验 ----------
h1("5　实验与结果分析")
h2("5.1　实验设置")
par("主样本按 7:3 分层划分为训练集与测试集，分别为 1 628 与 699 例，正例数为 706 与 303。"
    "超参数搜索采用 Optuna[13] 的 TPE 采样器，XGBoost 与 LightGBM 各搜索 30 组配置，以 3 折交叉验证的 AUC 为优化目标；"
    "其余模型采用经预实验确定的固定配置。表 4 列出最优超参数。实验环境为 Python 3.12、scikit-learn 1.9.1、"
    "XGBoost 3.4.1、LightGBM 4.7.0，随机种子固定为 42。")
table("表4　最优超参数", "Table 4　Optimal hyperparameters",
      ["模型", "主要超参数取值", "交叉验证 AUC"],
      [["XGBoost", "n_estimators=200, learning_rate=0.021 5, max_depth=3, subsample=0.715, "
                   "colsample_bytree=0.531, reg_lambda=1.313, min_child_weight=9", "0.787 0"],
       ["LightGBM", "n_estimators=200, learning_rate=0.021 6, num_leaves=7, min_child_samples=17, "
                    "subsample=0.785, colsample_bytree=0.550, reg_lambda=9.607", "0.784 2"]],
      [1.3, 5.25, 1.25], size=6.0)
par("需要指出，30 组试验对 6~7 维的搜索空间仍属有限预算，最优配置可能并非全局最优；"
    "但两组配置的交叉验证 AUC 已接近随机森林水平，说明在当前样本规模下进一步扩大搜索预算的边际收益很小。")

h2("5.2　判别性能")
par("表 5 与图 5 给出六种模型在独立测试集上的表现。XGBoost 的 AUC 最高，为 0.760 8（95% 置信区间 0.725 5~0.794 9），"
    "PR-AUC 为 0.684 6，Brier 分数为 0.196 8；LightGBM 的 AUC 为 0.760 4，两者几乎持平。随机森林为 0.758 2，"
    "堆叠集成为 0.753 6，直方图梯度提升为 0.745 2，逻辑回归最低，为 0.738 7。")
table("表5　模型判别性能对比", "Table 5　Model comparison",
      ["模型", "AUC（95%CI）", "PR-AUC", "KS", "F1", "Brier"],
      [["逻辑回归", "0.738 7（0.701 7~0.775 1）", "0.653 2", "0.389 2", "0.672 9", "0.210 9"],
       ["随机森林", "0.758 2（0.723 0~0.792 0）", "0.676 7", "0.395 4", "0.672 2", "0.199 7"],
       ["直方图梯度提升", "0.745 2（0.709 2~0.782 4）", "0.666 9", "0.405 2", "0.665 8", "0.221 0"],
       ["XGBoost", "0.760 8（0.725 5~0.794 9）", "0.684 6", "0.392 4", "0.677 5", "0.196 8"],
       ["LightGBM", "0.760 4（0.725 6~0.794 4）", "0.675 4", "0.395 6", "0.683 6", "0.197 1"],
       ["堆叠集成", "0.753 6（0.718 0~0.788 5）", "0.676 1", "0.400 5", "0.672 5", "0.200 3"]],
      [1.72, 2.7, 1.0, 0.8, 0.75, 0.78], size=5.8)
figure("fig15_metrics.png", "图5　各模型评价指标对比", "Fig.5　Comparison of evaluation metrics", width=7.4)
par("值得注意的是，堆叠集成在五折交叉验证中取得最高 AUC（0.787 9±0.015 3），但在留出集上反而低于两个梯度提升模型。"
    "DeLong 检验显示，XGBoost 与 LightGBM 的差异不显著（p=0.979），与随机森林亦不显著（p=0.852），"
    "仅相对逻辑回归的 2.2 个百分点提升接近但未达到显著水平（p=0.108）。这一结果说明：在 699 例测试样本下，"
    "检验的统计功效有限，2 个百分点左右的差异难以与抽样波动区分；同时也意味着当前任务的判别上限更多由特征决定，"
    "而非分类器结构。")
figure("fig5_roc.png", "图6　ROC 曲线", "Fig.6　ROC curves", width=7.4)
figure("fig6_pr.png", "图7　精确率—召回率曲线", "Fig.7　Precision-recall curves", width=7.4)
par("从精确率与召回率的权衡看，各模型在最优 F1 阈值下的召回率均高于 0.83，精确率介于 0.53 与 0.57 之间。"
    "这说明在流失率 43% 的样本中，模型倾向于以较高的召回率换取可接受的误判，与“宁可多触达、不可漏判”"
    "的业务偏好一致；但该偏好是否成立取决于漏判与误判代价的实际比值，5.7 节对此作进一步讨论。")
par("图 6 的 ROC 曲线与图 7 的 PR 曲线呈现一致的排序，但 PR 曲线更能反映不平衡条件下的实际表现："
    "当召回率固定在 0.5 时，XGBoost 的精确率约为 0.70，而逻辑回归约为 0.66。图 8 的累计增益曲线显示，"
    "按模型得分排序触达前 10% 客户可捕获 17.2% 的流失客户，前 30% 可捕获约 49%，均显著高于随机基线。")
figure("fig7_gain.png", "图8　累计增益曲线", "Fig.8　Cumulative gain curves", width=7.4)

h2("5.3　类别不平衡处理")
par("为检验不平衡处理的实际作用，以 LightGBM 为载体比较三种策略：不处理、类别权重、SMOTE 过采样，结果如表 6 所示。"
    "三者的 AUC 分别为 0.760 4、0.760 0 与 0.757 6，差异在 0.003 以内；PR-AUC 亦基本一致。"
    "差异主要体现在固定 0.5 阈值下的召回率：不处理时为 0.646 9，类别权重提升至 0.726 1，SMOTE 为 0.709 6，"
    "相应地精确率由 0.657 7 下降至 0.616 2 与 0.626 8。")
table("表6　类别不平衡策略对比", "Table 6　Comparison of imbalance strategies",
      ["策略", "AUC", "PR-AUC", "召回率", "精确率", "Brier"],
      [["不处理", "0.760 4", "0.675 4", "0.646 9", "0.657 7", "0.197 1"],
       ["类别权重", "0.760 0", "0.677 3", "0.726 1", "0.616 2", "0.200 0"],
       ["SMOTE 过采样", "0.757 6", "0.675 3", "0.709 6", "0.626 8", "0.200 8"]],
      [1.85, 1.15, 1.15, 1.15, 1.15, 1.1], size=6.4)
par("这说明过采样与加权并未改善模型对正负样本的排序能力，其作用是整体抬高预测概率，使固定阈值下的判定偏向正类。"
    "由于本任务的决策阈值本就应依据代价结构确定（见 4.4 节），此类“通过移动概率分布换取召回”的做法并不能带来额外收益，"
    "反而会破坏概率的可校准性，Brier 分数由 0.197 1 上升至 0.200 8。因此主流程不采用重采样，"
    "仅以类别权重处理逻辑回归的线性偏移。")

h2("5.4　消融实验")
par("为识别各组特征的边际贡献，采用两种消融方式：一是剔除某一组特征后重新训练，二是仅使用某一组特征训练，"
    "均以五折交叉验证 AUC 为度量，结果如表 7 与图 9 所示。全特征基线为 0.775 6±0.018 4。")
table("表7　特征组消融结果", "Table 7　Ablation results",
      ["特征组", "剔除后 AUC", "仅用该组 AUC", "剔除变化 ΔAUC"],
      [["全特征（基线）", "0.775 6", "—", "—"],
       ["RFM 核心", "0.777 7", "0.764 0", "+0.002 1"],
       ["消费强度", "0.775 5", "0.673 3", "−0.000 1"],
       ["购买节奏", "0.773 9", "0.760 0", "−0.001 7"],
       ["趋势变化", "0.774 2", "0.771 5", "−0.001 4"],
       ["结构多样性", "0.775 7", "0.643 9", "+0.000 1"],
       ["退货行为", "0.775 2", "0.591 6", "−0.000 4"],
       ["时间偏好", "0.775 6", "0.598 5", "0.000 0"]],
      [2.0, 1.9, 1.9, 1.9], size=6.6)
par("剔除单组特征后，AUC 变化均在 0.002 以内，且多数落在一个标准差范围之内。剔除 RFM 核心组后 AUC 反而微升至 0.777 7，"
    "剔除结构多样性组后为 0.775 7，说明这些特征的信息与其他组存在较强重叠，单组剔除不会造成实质损失。"
    "相对而言，剔除购买节奏组（0.773 9）与趋势变化组（0.774 2）的下降幅度最大，但仍不显著。")
figure("fig12_ablation.png", "图9　特征组消融结果", "Fig.9　Ablation results", width=7.4)
par("仅用单组特征时，趋势变化组表现最强，AUC 达 0.771 5，已接近全特征水平；RFM 核心组为 0.764 0；"
    "购买节奏组为 0.760 0；消费强度组为 0.673 3；结构多样性、退货行为与时间偏好三组均低于 0.65。"
    "这一结果与图 3 的相关性分析相互印证：late_orders 与 recency 高度相关，趋势组实际上以时间加权的方式重构了"
    "“近期活跃度”这一核心信号，因此单独使用即可获得较高判别力；而退货与时间偏好属于弱信号，只在特定客群中提供增量信息。")
par("该结论对特征工程实践具有直接含义：在交易流水可得的场景中，优先构造近期窗口的订单计数与趋势斜率，"
    "比精细刻画商品结构或退货行为更具性价比；但弱信号组的保留仍有价值，因为它们在树模型的交互分裂中"
    "可能提供非线性的补充，且不增加显著的计算开销。")

h2("5.5　跨期泛化")
par("为检验模型在不同时间段的稳定性，将两期样本互为训练集与测试集，结果如表 8 与图 10 所示。"
    "以 2011 期训练、2010 期测试时，五个模型的 AUC 介于 0.692 3 与 0.711 6；以 2010 期训练、2011 期测试时，"
    "AUC 介于 0.690 6 与 0.743 0。相较同期测试的 0.74~0.76，跨期 AUC 下降约 0.03~0.06。")
table("表8　跨期泛化结果", "Table 8　Cross-period generalization results",
      ["模型", "2011 训练→2010 测试", "2010 训练→2011 测试", "两者均值"],
      [["逻辑回归", "0.708 5", "0.738 4", "0.723 5"],
       ["随机森林", "0.711 6", "0.743 0", "0.727 3"],
       ["直方图梯度提升", "0.692 3", "0.690 6", "0.691 4"],
       ["XGBoost", "0.693 5", "0.691 5", "0.692 5"],
       ["LightGBM", "0.693 9", "0.705 4", "0.699 6"]],
      [1.9, 2.05, 2.05, 1.6], size=6.6)
par("随机森林在两个方向上都最为稳定（0.711 6 与 0.743 0），而梯度提升模型的下降更为明显（最低至 0.690 6）。"
    "这一现象可从两方面解释：其一，两期样本的流失基率相差 13.9 个百分点，概率输出的整体偏移会削弱以排序为基础的指标；"
    "其二，树模型的分裂点对训练期的特征分布高度敏感，当促销节奏与季节结构变化时，分裂阈值随之失效，"
    "而随机森林的 bagging 机制在一定程度上平滑了这种敏感性。")
figure("fig13_cross.png", "图10　跨期泛化性能对比", "Fig.10　Cross-period generalization", width=7.4)
par("该结果提示，跨期部署时不能直接沿用旧模型的概率输出，至少需要在新窗口数据上重新校准基率；"
    "若业务方能够获得少量新期标注样本，采用增量微调或分层重加权比完全重训更具成本优势。")

h2("5.6　概率校准")
par("图 11 比较了 XGBoost 与 LightGBM 的可靠性曲线。两条曲线整体贴近对角线，在 0.2~0.6 区间仅有轻微低估，"
    "Brier 分数分别为 0.196 8 与 0.197 1，优于逻辑回归的 0.210 9。对 LightGBM 施加等温回归校准后，"
    "Brier 分数反而由 0.197 1 升至 0.199 2，AUC 由 0.760 4 微降至 0.759 1。")
figure("fig8_calibration.png", "图11　概率校准曲线", "Fig.11　Calibration curves", width=7.4)
par("校准未带来改进的原因在于样本规模：等温回归需要在训练集内部再划分校准集，699 例测试样本对应的可靠性曲线"
    "每个分箱仅有数十个观测，分箱边界的估计误差被放大。因此，当树模型本身已输出较为平滑的概率时，"
    "额外校准在小样本上更容易引入方差而非降低偏差。这一负结果与部分文献中“校准总能改善概率质量”的经验并不一致，"
    "说明校准方法的收益依赖于样本量与模型族的匹配。")

h2("5.7　预算约束下的收益分析")
par("按 4.4 节的代价设定（CFN=200 元，CFP=50 元），在测试集上以 0.01 为步长搜索全局最优阈值，得到 τ*=0.10，"
    "对应触达比例 87.8%、召回率 98.3%，期望净收益 47 320 元；而全量触达的净收益为 46 620 元，两者仅相差 700 元。"
    "原因在于漏判代价是误判代价的 4 倍，而样本流失率高达 43.36%，此时对任意客户投放的期望收益均为正，"
    "全局最优自然退化为近似广覆盖。")
par("这一退化现象恰恰说明：当流失率较高且挽留成本较低时，“是否投放”不再是核心问题，“投放给谁、投多少”才是。"
    "图 12 给出固定触达比例下的收益曲线：在 10% 预算下，按模型排序触达的净收益为 6 900 元，随机触达仅为 2 569 元，"
    "前者是后者的 2.69 倍；触达比例放宽至 30% 时，两者分别为 19 300 元与 7 706 元，倍数为 2.50。"
    "随着触达比例上升，模型的边际优势递减，这是因为高概率人群被优先覆盖后，新增触达对象的流失概率迅速向基率回归。")
table("表9　不同触达比例下的收益对比", "Table 9　Net revenue under different coverage ratios",
      ["触达比例", "命中率/%", "召回率/%", "提升倍数", "模型净收益/元", "随机净收益/元"],
      [["10%", "74.29", "17.16", "1.71", "6 900", "2 569"],
       ["20%", "73.57", "33.99", "1.70", "13 600", "5 137"],
       ["30%", "70.95", "49.17", "1.64", "19 300", "7 706"],
       ["50%", "62.29", "71.95", "1.44", "26 100", "12 843"]],
      [1.05, 1.3, 1.3, 1.25, 1.4, 1.35], size=6.2)
figure("fig9_budget.png", "图12　预算约束下的期望净收益", "Fig.12　Net revenue under budget constraints", width=7.4)
par("图 13 给出阈值与净收益的关系。曲线在 0.05~0.15 区间存在一个宽阔的平台，说明在代价比例给定的条件下，"
    "阈值的小幅波动不会显著改变收益，这为运营侧的阈值调整留出了容错空间。敏感性分析进一步显示：当 CFN 由 50 元"
    "增至 800 元时，最优阈值由 0.35 下降至 0.05，最优净收益由 4 020 元增至 228 660 元，即漏判代价越高，"
    "越应放宽触达门槛。")
figure("fig14_threshold.png", "图13　阈值与期望净收益的关系", "Fig.13　Net revenue versus decision threshold", width=7.4)
par("此外，模型收益对代价参数的敏感度高于对模型结构的敏感度：当漏判代价由 200 元增至 400 元时，"
    "最优净收益由 47 320 元增至 107 460 元，而更换分类器带来的 AUC 差异不足 0.03，折算到收益上约为数百元。"
    "这提示业务侧应优先标定毛利与挽留成功率，而非反复调整模型结构。")

h2("5.8　可解释性与分层分析")
par("图 14 给出 LightGBM 在测试集上的 SHAP 蜂群图，按平均绝对贡献排序展示前 10 个特征，表 10 列出具体数值的数值。"
    "late_orders 的贡献最大（0.368 4），其后依次为 monetary（0.322 5）、recency（0.198 2）与 frequency（0.151 2），"
    "四者合计解释了大部分判别信号。")
table("表10　特征重要度（平均绝对 SHAP 值）", "Table 10　Top-10 features by mean absolute SHAP value",
      ["排名", "特征", "平均绝对 SHAP 值", "与流失标签相关系数"],
      [["1", "late_orders", "0.368 4", "−0.335"],
       ["2", "monetary", "0.322 5", "−0.132"],
       ["3", "recency", "0.198 2", "0.326"],
       ["4", "frequency", "0.151 2", "−0.307"],
       ["5", "items_per_order", "0.086 8", "−0.063"],
       ["6", "repeat_sku_ratio", "0.086 4", "−0.179"],
       ["7", "month_slope", "0.084 4", "0.105"],
       ["8", "tenure_days", "0.080 0", "−0.313"],
       ["9", "gap_mean", "0.065 2", "0.112"],
       ["10", "month_amount_growth", "0.059 1", "0.035"]],
      [0.85, 2.5, 2.2, 2.15], size=6.4)
figure("fig10_shap.png", "图14　SHAP 特征贡献蜂群图", "Fig.14　SHAP summary plot", width=7.3)
par("图 15 的两个依赖图揭示了具体的作用方向：近三个月订单数越少，SHAP 值越正，即越倾向于被判为流失，"
    "且在 0~2 笔区间内边际效应最陡；最近购买间隔越长，SHAP 值越正，超过 60 天后增速放缓，"
    "说明“两个月未购”是一个重要的行为拐点。两者共同刻画了同一条时间轴上的活跃度衰减，"
    "这也解释了为何剔除 RFM 组不会造成性能损失——其信息已被趋势与节奏特征以更细的粒度重建。")
figure("fig11_dependence.png", "图15　典型特征的 SHAP 依赖图", "Fig.15　SHAP dependence plots", width=7.4)
par("分层分析显示模型的判别能力并不均匀：按测试集消费金额四分位分组，最高价值组的 AUC 为 0.798 2，"
    "而最低两组仅为 0.645 3 与 0.644 6。原因在于低价值客户的订单稀疏、行为序列短，可用于区分的信息有限，"
    "其预测概率普遍偏高；在 τ=0.263 的判定阈值下，最低两组的召回率均达到 100%，意味着该客群几乎被全量触达。"
    "若不加区分地使用单一阈值，低价值客群将消耗大量触达预算。因此，实践中应按客群分层设定阈值："
    "高价值客群收紧阈值以控制误伤，低价值客群则结合低成本自动化触达策略。")

h2("5.9　讨论")
par("综合上述结果，可以得到三点认识。第一，特征的时间结构比特征的维度数量更重要。本文构建的 31 维特征中，"
    "真正提供主要判别力的是围绕“近期活跃度”构造的 6 维趋势特征与 7 维节奏特征，这与 RFM 框架的经典结论一致，"
    "但实现方式从静态累计转向了窗口对比与斜率拟合。")
par("第二，模型复杂度与样本规模需要匹配。在 2 327 名客户、31 维特征的规模下，梯度提升相对逻辑回归的提升约为 "
    "2.2 个百分点且未达统计显著，堆叠集成虽然在交叉验证中占优，但在留出集上并未超越单模型。"
    "这说明在该规模下继续增加模型复杂度收益有限，投入应更多转向特征与标签质量。")
par("第三，评估体系必须与决策场景对齐。AUC 只能回答“排序是否合理”，无法回答“预算有限时该联系谁”“跨期是否仍然可靠”。"
    "本文引入的预算约束收益、跨期泛化与分层鲁棒性三项证据，揭示了单一指标掩盖的问题："
    "全局最优阈值在高低价值客群上的行为截然不同，跨期部署必须重新校准。")
par("与既有研究报告的 0.75~0.85 的 AUC 区间相比，本文结果处于中位水平。差异主要来自任务难度而非模型能力："
    "公开数据集中客户的购买行为呈明显批发特征，单笔金额大、复购周期长，行为序列噪声更强；"
    "同时本文采用严格的时间隔离标签，未使用任何跨窗口的聚合信息。若放宽标签定义或引入外部特征，"
    "指标仍有上升空间，但这会削弱结论的可复现性。")
par("本文的局限主要有四点：（1）数据来自单一英国在线零售商，客户以批发型采购为主，商品结构与时序模式与国内平台存在差异，"
    "结论的外部有效性有待验证；（2）标签窗口固定为 3 个月，未讨论窗口长度对基率与特征重要性的影响；"
    "（3）未引入基于行为序列的深度模型与生存分析，无法刻画购买间隔的分布形态；"
    "（4）代价参数 CFN 与 CFP 为假设值，真实场景需结合毛利与挽留成功率标定。")

# ---------- 6 结束语 ----------
h1("6　结束语")
par("本文以电商非合约场景的客户流失预测为对象，构建了观察窗口与标签窗口分离的样本生成方法，提取了 7 组 31 维行为特征，"
    "并在 2 327 名客户的真实交易数据上比较了五类模型与堆叠集成。主要结论如下：XGBoost 在独立测试集上取得最优判别性能，"
    "AUC 为 0.760 8，PR-AUC 为 0.684 6；趋势类特征单独使用即可达到 0.771 5 的 AUC，静态 RFM 特征的部分信息"
    "可被时间加权特征替代；在 10% 预算约束下，模型相对随机投放将期望净收益提升 1.69 倍；"
    "跨期验证中 AUC 下降 0.03~0.06，基率漂移与分裂阈值失效是主要原因。")
par("后续工作可从四个方向展开：一是将购买序列建模为事件流，引入带时间衰减的循环网络或 Transformer，"
    "与树模型做互补融合；二是采用生存分析刻画客户流失的风险函数，输出随时间变化的流失概率而非单一二分类标签；"
    "三是引入 uplift 模型区分“自然留存”与“因干预而留存”的客户，避免对无响应人群的无效投放；"
    "四是构建在线学习机制，以滑动窗口持续更新特征分布与决策阈值，缓解概念漂移。")

# ---------- 参考文献 ----------
h1("参考文献")
refs = [
 "GUPTA S, LEHMANN D R, STUART J A. Valuing customers[J]. Journal of Marketing Research, 2004, 41(1): 7-18.",
 "FADER P S, HARDIE B G S, LEE K L. “Counting your customers” the easy way: An alternative to the Pareto/NBD model[J]. "
 "Marketing Science, 2005, 24(2): 275-284.",
 "COUSSEMENT K, VAN DEN POEL D. Churn prediction in subscription services: An application of support vector machines "
 "while comparing two parameter-selection techniques[J]. Expert Systems with Applications, 2008, 34(1): 313-327.",
 "HUANG B, KECHADI M T, BUCKLEY B. Customer churn prediction in telecommunications[J]. Expert Systems with Applications, "
 "2012, 39(1): 1414-1425.",
 "VERBEKE W, DEJAEGER K, MARTENS D, et al. New insights into churn prediction in the telecommunication sector: "
 "A profit driven data mining approach[J]. European Journal of Operational Research, 2012, 218(1): 211-229.",
 "AHMAD A K, JAFAR A, ALJOUMA A K. Customer churn prediction in telecom using machine learning in big data platform[J]. "
 "Journal of Big Data, 2019, 6(1): 28.",
 "BREIMAN L. Random forests[J]. Machine Learning, 2001, 45(1): 5-32.",
 "CHEN T, GUESTRIN C. XGBoost: A scalable tree boosting system[C]//Proceedings of the 22nd ACM SIGKDD International "
 "Conference on Knowledge Discovery and Data Mining. New York: ACM, 2016: 785-794.",
 "KE G, MENG Q, FINLEY T, et al. LightGBM: A highly efficient gradient boosting decision tree[C]//Advances in Neural "
 "Information Processing Systems 30. 2017: 3146-3154.",
 "WOLPERT D H. Stacked generalization[J]. Neural Networks, 1992, 5(2): 241-259.",
 "CHAWLA N V, BOWYER K W, HALL L O, et al. SMOTE: Synthetic minority over-sampling technique[J]. Journal of Artificial "
 "Intelligence Research, 2002, 16: 321-357.",
 "LUNDBERG S M, LEE S I. A unified approach to interpreting model predictions[C]//Advances in Neural Information "
 "Processing Systems 30. 2017: 4765-4774.",
 "AKIBA T, SANO S, YANASE T, et al. Optuna: A next-generation hyperparameter optimization framework[C]//Proceedings of "
 "the 25th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. New York: ACM, 2019: 2623-2631.",
 "DELONG E R, DELONG D M, CLARKE-PEARSON D L. Comparing the areas under two or more correlated receiver operating "
 "characteristic curves: A nonparametric approach[J]. Biometrics, 1988, 44(3): 837-845.",
 "周志华. 机器学习[M]. 北京: 清华大学出版社, 2016.",
 "李航. 统计学习方法[M]. 2版. 北京: 清华大学出版社, 2019.",
]
for i, ref in enumerate(refs, start=1):
    p = doc.add_paragraph(); pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.space_before = Pt(0); pf.space_after = Pt(1); pf.line_spacing = 1.05
    pf.left_indent = Pt(21); pf.first_line_indent = Pt(-21)
    r = p.add_run("[%d]　%s" % (i, ref)); set_cn(r, "宋体", "Times New Roman", 8)

# ---------- 页脚页码（封面不编号，摘要页起为第 1 页） ----------
def _page_field(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)
    run = p.add_run()
    r = run._r
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = " PAGE "
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t"); t.text = "1"
    f3 = OxmlElement("w:fldChar"); f3.set(qn("w:fldCharType"), "end")
    for el in (f1, it, f2, t, f3):
        r.append(el)
    set_cn(run, "宋体", "Times New Roman", 9)

cover, abst, body = doc.sections[0], doc.sections[1], doc.sections[2]
cover.footer.is_linked_to_previous = False
for pp in cover.footer.paragraphs:
    for rr in list(pp.runs):
        rr._r.getparent().remove(rr._r)
abst.footer.is_linked_to_previous = False
_page_field(abst)
pg = OxmlElement("w:pgNumType"); pg.set(qn("w:start"), "1")
abst._sectPr.append(pg)
body.footer.is_linked_to_previous = True

doc.save(OUT)

# ---- 字数统计（仅用于确认是否满足 8000 字要求，统计正文中文字符） ----
import re
alltext = "\n".join(p.text for p in doc.paragraphs)
cjk = len(re.findall("[\u4e00-\u9fff]", alltext))
print("saved:", OUT)
print("中文字符数（含题名摘要正文参考文献）:", cjk)
print("总段落:", len(doc.paragraphs), "表格:", len(doc.tables))
