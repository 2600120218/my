# -*- coding: utf-8 -*-
"""第二份：桂电 电气工程及其自动化 大一男生 · 工业自动化方向职业规划
   同一模板，不同内容；背景在 restyle2.py 中替换为石墨+琥珀。"""
import copy
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.chart.data import CategoryChartData

OUTFILE = "职业生涯规划-电气工程及其自动化-轨道交通供电方向.pptx"
FONT = "微软雅黑"
NAVY = RGBColor(0x1B, 0x24, 0x30)
AMBER = RGBColor(0xC0, 0x50, 0x3F)
DEEP = RGBColor(0xA6, 0x3E, 0x30)
GREY = RGBColor(0x5C, 0x5A, 0x55)

prs = Presentation("template.pptx")


# ---------------------------------------------------------------- helpers
def iter_shapes(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:
            yield from iter_shapes(sh.shapes)


def find_all(slide, path):
    parts = path.split("/")
    cur = [slide.shapes]
    acc = list(slide.shapes)
    for p in parts:
        nxt = []
        for parent in cur:
            for sh in parent:
                if sh.name == p:
                    nxt.append(sh)
        if not nxt:
            raise KeyError(f"{path} -> {p}")
        cur = [x.shapes for x in nxt if x.shape_type == 6]
        acc = nxt
    return acc


def find(slide, path, n=0):
    return find_all(slide, path)[n]


def _seq(v):
    if v is None:
        return None
    return list(v) if isinstance(v, (list, tuple)) else [v]


def set_lines(shape, lines, sizes=None, colors=None, bolds=None,
              aligns=None, wrap=None):
    sizes, colors, bolds, aligns = _seq(sizes), _seq(colors), _seq(bolds), _seq(aligns)
    tf = shape.text_frame
    while len(tf.paragraphs) < len(lines):
        last = tf.paragraphs[-1]
        newp = copy.deepcopy(last._p)
        last._p.addnext(newp)
    while len(tf.paragraphs) > len(lines):
        p = tf.paragraphs[-1]._p
        p.getparent().remove(p)
    for i, line in enumerate(lines):
        para = tf.paragraphs[i]
        runs = para.runs
        if runs:
            runs[0].text = line
            for r in runs[1:]:
                r._r.getparent().remove(r._r)
        else:
            para.add_run().text = line
        r0 = para.runs[0]
        if sizes and i < len(sizes) and sizes[i]:
            r0.font.size = Pt(sizes[i])
        if colors and i < len(colors) and colors[i] is not None:
            r0.font.color.rgb = colors[i]
        if bolds and i < len(bolds) and bolds[i] is not None:
            r0.font.bold = bolds[i]
        if aligns and i < len(aligns) and aligns[i] is not None:
            para.alignment = aligns[i]
    if wrap is not None:
        tf.word_wrap = wrap


def delete_shape(slide, path, n=0):
    sh = find(slide, path, n)
    el = sh._element
    el.getparent().remove(el)


def fix_rpr(rPr, name):
    latin = rPr.find(qn('a:latin'))
    if latin is None:
        latin = rPr.makeelement(qn('a:latin'), {})
        rPr.insert(0, latin)
    latin.set('typeface', name)
    for tag in ('a:ea', 'a:cs'):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set('typeface', name)


def apply_font(run, name=FONT):
    run.font.name = name
    fix_rpr(run._r.get_or_add_rPr(), name)


def set_font_all(shape, name=FONT):
    if not shape.has_text_frame:
        return
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            apply_font(r, name)
        pPr = p._p.find(qn('a:pPr'))
        if pPr is not None:
            d = pPr.find(qn('a:defRPr'))
            if d is not None:
                fix_rpr(d, name)


def box(slide, path, left=None, top=None, width=None, height=None, n=0):
    sh = find(slide, path, n)
    if left is not None:
        sh.left = Inches(left)
    if top is not None:
        sh.top = Inches(top)
    if width is not None:
        sh.width = Inches(width)
    if height is not None:
        sh.height = Inches(height)
    return sh


# ---------------------------------------------------------------- content
E = {}
D = {}

# 封面
E[1] = [
    ('标题 1', ['电气工程及其自动化', '大学生职业生涯规划'], None, None, None, None, False),
    ('副标题 2', ['成长赛道 ｜ 一条通往地铁供电段的路线'], [18], None, None, None, False),
    ('文本占位符 4', ['汇报人：　　　　　　学号：　　　　　'], [17], None, None, PP_ALIGN.RIGHT, False),
    ('文本占位符 3', ['汇报时间：2026 年 11 月'], [17], None, None, PP_ALIGN.RIGHT, False),
]

# 目录
E[2] = [
    ('文本框 2', ['自我认知']),
    ('文本框 10', ['环境分析']),
    ('文本框 11', ['职业定位']),
    ('文本框 12', ['行动路线']),
    ('文本框 16', ['评估调整']),
]

E[3] = [('文本框 22', ['01', '自我认知'])]

# 个人简介
E[4] = [
    ('矩形: 圆角 13', ['＿＿＿＿']),
    ('矩形: 圆角 19', ['2026级 · 大一']),
    ('组合 20/文本框 23', ['桂林电子科技大学']),
    ('组合 24/文本框 27', ['电气工程及其自动化']),
    ('组合 28/矩形: 圆角 29', ['当前状态']),
    ('组合 28/文本框 31', ['方向：轨道交通供电']),
    ('组合 32/文本框 36', ['地铁 / 铁路 供电检修']),
    ('文本框 42', ['身体是本钱：视力、色觉、体能都得过关',
                   '选电气是因为喜欢"看得见的大设备"；大二体检自查之后，我把目标收窄到地铁和铁路的供电岗。'],
     [20, 14]),
]

# 实践经历
D[5] = ['文本框 9']
E[5] = [
    ('文本框 27', ['院学生会 权益部 干事']),
    ('文本框 29', ['校红十字会 急救员培训']),
    ('文本框 31', ['校运会 · 迎新志愿者']),
    ('文本框 38', ['(1) 校内实践'], [17], None, None, None, False),
    ('文本框 58', ['寒假打算：去南宁看两天设备'], [15]),
    ('文本框 55', ['大一没有实习，也谈不上项目。',
                   '2027 年寒假打算去南宁，跟着在地铁做检修的亲戚看两天站内设备——先看看倒班是什么滋味。'],
     [16, 14]),
    ('文本框 4104', ['课外：照照片画了一张单线图'], [13]),
    ('文本框 4107', ['① 把主变、断路器、隔离开关画成单线图，画到第三遍才顺。'], [13]),
    ('文本框 4108', ['② 最大的感受是"图上一根线，现场一大片"，对规程有了点敬畏。'], [13]),
]

# 能力盘点（自定义）
D[6] = ['文本框 16', '文本框 18', '椭圆 3', '图片 5', '图片 7', '图片 22']
E[6] = [('文本框 8', ['3.能力盘点'])]

E[7] = [('文本框 5', ['02', '环境分析'])]

# 政策背景
E[8] = [
    ('文本框 81', ['“到 2035 年，基本建成交通强国。”'], [24]),
    ('文本框 82', ['——《交通强国建设纲要》，2019 年 9 月'], [13]),
    ('矩形 77', ['城轨运营里程逐年增长'], [16]),
    ('矩形 78', ['2023 年末达 1.02 万公里'], [15]),
    ('文本框 73', ['2019—2023 年全国城轨运营里程（公里）'], [11]),
    ('文本框 40', ['线路越修越多，设备总得有人守'], [19]),
    ('文本框 42', ['24 小时', '设备不停运，人就得分班'], [17, 11]),
    ('组合 62/文本框 65', ['岗位较稳定']),
    ('组合 62/文本框 66', ['01'], [14], None, None, None, False),
    ('组合 54/文本框 57', ['体检卡得严']),
    ('组合 54/文本框 58', ['02'], [14], None, None, None, False),
    ('组合 46/文本框 49', ['倒班是常态']),
    ('组合 46/文本框 50', ['03'], [14], None, None, None, False),
    ('组合 74/文本框 76', ['这行不缺岗位，缺的是"身体过关、肯倒班"的人。']),
    ('椭圆 83', ['缺口', '稳定']),
    ('椭圆 84', ['体检', '先拦人']),
]

# 就业环境
E[9] = [
    ('文本框 22', ['2.出路对比']),
    ('文本框 89', ['轨道交通供电是"设备不停、人不停"的活：白天检修要申请天窗点，夜里干活是常态。']),
    ('组合 90/文本框 92', ['5 条'], [30], None, None, None, False),
    ('组合 90/文本框 91', ['南宁地铁', '已开通线路'], [12, 12]),
    ('文本框 95', ['三个去处：地铁公司求"稳"、铁路局求"编"、施工单位求"快"。']),
    ('文本框 103', ['地铁公司'], [16], None, None, None, False),
    ('文本框 104', ['铁路局供电段'], [15], None, None, None, False),
    ('文本框 105', ['施工维保企业'], [15], None, None, None, False),
    ('文本框 97', ['南宁、广州、深圳的地铁都在招电气本科，五险一金齐全，倒班，但稳定。']),
    ('文本框 98', ['南宁局、广铁集团每年校招，通用专业名额少，竞争比地铁更狠。']),
    ('文本框 99', ['中铁电气化局这类单位跟着项目跑，收入高些，但常年在外。']),
]

E[10] = [('文本框 5', ['03', '职业定位'])]

# 职业测评
E[11] = [
    ('组合 103/PPT世界-6-4', ['01. 霍兰德职业兴趣测试'], [18]),
    ('组合 103/组合 24/文本框 51', ['测评结果：现实型 R']),
    ('组合 103/组合 26/文本框 27', ['喜欢按规程做事、动手能力强；对"必须按标准来"的岗位不反感；不爱临时变卦。']),
    ('组合 103/组合 26/文本框 29', ['适配：供电检修、变电值班、设备维护。']),
    ('组合 92/PPT世界-6-4', ['02. MBTI 职业性格测评'], [18]),
    ('组合 92/文本框 84', ['1. 做事讲究流程，不喜欢跳步骤。',
                            '2. 答应的事一定做到，讨厌放鸽子。',
                            '3. 对突发状况不慌，但讨厌计划被打乱。',
                            '4. 不太会来事，升职可能比别人慢。']),
    ('组合 92/组合 88/文本框 90', ['测评结果：', 'ISTJ'], [10, 20]),
    ('组合 92/文本框 91', ['适配方向：检修、值班、安全监督']),
    ('文本框 99', ['两次测评都指向"守规矩、能执行"的类型。这类人适合有标准作业卡的岗位——地铁供电正好是。'
                   '但要承认：我还没真正在夜里干过活，能不能扛住倒班，得试过才知道。'], [22]),
    ('组合 101/文本框 69', ['守规矩']),
    ('组合 105/文本框 107', ['耐得住']),
]

# 行业现状
D[12] = ['图表 3']
E[12] = [
    ('文本框 27', ['2.行业现状及背景']),
    ('文本框 109', ['Rail Transit'], [38]),
    ('文本框 23', ['2015 年至今'], [26]),
    ('文本框 20', ['国内城轨从"修一条线"进入"组一张网"：线路越多，供电设备越多，检修和值班的人手就越紧。'], [13]),
    ('文本框 34', ['2023 年末全国城轨运营里程'], [15]),
    ('文本框 44', ['1.02 万公里'], [26]),
    ('文本框 56', ['80%'], [30]),
    ('文本框 68', ['　　　　　　　　　　城轨线路集中在人口密集的城市，客流稳定，运营维护是长期需求'], [11]),
    ('矩形: 圆角 88', ['变电所']),
    ('矩形: 圆角 89', ['接触网']),
    ('矩形: 圆角 90', ['电力监控']),
    ('文本框 98', ['把高压降成列车能用的电，值班、倒闸、巡视，一样不能少。']),
    ('文本框 99', ['给列车送电的架空线，高空作业，天窗点里干，最考验人。']),
    ('文本框 100', ['盯着全线供电状态，故障时第一个知道，也第一个被叫起来。']),
]

# 招聘节奏
E[13] = [
    ('文本框 34', ['3.招聘节奏']),
    ('文本框 13', ['轨道交通的招聘有固定节奏，错过就要再等一年：'], [22]),
    ('文本框 40', ['地铁与铁路局校招大致时间（以官方公告为准）'], [13]),
    ('组合 35/矩形: 圆角 19', ['9 月']),
    ('组合 35/矩形: 圆角 28', ['地铁公司网申开始']),
    ('组合 11/矩形: 圆角 22', ['10 月']),
    ('组合 11/矩形: 圆角 29', ['铁路局校招宣讲']),
    ('组合 8/矩形: 圆角 26', ['11 月']),
    ('组合 8/矩形: 圆角 30', ['笔试 + 面试']),
    ('组合 33/矩形: 圆角 32', ['次年 3 月']),
    ('组合 33/矩形: 圆角 31', ['补录 / 春招']),
    ('矩形 51', ['提前体检'], [11]),
    ('矩形 55', ['简历写证书'], [10]),
    ('矩形 54', ['别只投一家'], [11]),
]

# 薪资与胜任标准
E[14] = [
    ('文本框 14', ['起薪不高，胜在稳定和五险一金'], [19]),
    ('文本框 17', ['南宁地铁检修岗本科起薪 5—7 千/月，加夜班补贴和绩效；铁路局略高但名额少；广深地铁 7—9 千。'], [13]),
    ('文本框 28', ['硬门槛：矫正视力 4.9 以上、无色盲色弱、身高体重要求、无纹身——这些比成绩更早卡人。'], [10.5]),
    ('文本框 95', ['证书：', '低压电工证、高处作业证是加分项；入职后还要考接触网工 / 变电检修工等级证。'], [13, 12]),
    ('文本框 100', ['技能：', '看得懂供电系统图，会用万用表、绝缘电阻表，能照着作业卡一步一步做。'], [13, 12]),
    ('文本框 25', ['身体与心态：', '能爬杆、能负重、能连着上夜班；突发故障时不慌，先按规程来。'], [13, 12]),
]

# 信息与体验
E[15] = [
    ('文本框 30', ['5.信息与体验']),
    ('文本框 22', ['去南宁坐地铁时特意在站台多看了两眼：牵引变电所就在站厅边上，铁门一关什么也看不见。'], [11]),
    ('文本框 24', ['现场看不到什么'], [16]),
    ('文本框 95', ['问了在地铁做检修的亲戚，他们最常说的一句话是"按票干活，别自己发挥"。'], [11]),
    ('文本框 98', ['规程比技术重要'], [15]),
    ('文本框 109', ['查招聘公告才发现，体检标准写得很细：色盲色弱直接刷，矫正视力不到 4.9 也刷。'], [11]),
    ('文本框 112', ['体检先卡人'], [15]),
    ('文本框 119', ['最大的收获：这行的门槛不在分数，在身体和能不能熬。这两条我现在都还不确定。'], [11]),
    ('文本框 125', ['先体检，再谈规划'], [15]),
]

E[16] = [('文本框 5', ['04', '行动路线'])]

# 短期
E[17] = [
    ('文本框 17', ['1.短期计划（大一—大二）'], [20]),
    ('文本框 30', ['先把体检搞明白', '再考电工证'], [24, 24]),
    ('文本框 8', ['不等到大四才体检：大二开学去做一次视力、色觉检查，有问题早处理；同时把电路、电机学明白。'], [15]),
    ('文本框 2048', ['大二考低压电工证，暑假报高处作业证；平时练体能，1000 米和引体向上别落下。'], [15]),
]

# 中期
E[18] = [
    ('文本框 9', ['2.中期计划（大三）'], [20]),
    ('文本框 8', ['进一次现场，确认自己受不受得了倒班'], [24]),
    ('文本框 2060', ['大三暑期争取地铁公司实习或供电施工单位跟岗，哪怕只是递工具；'
                     '同时把继电保护和牵引供电看一遍，面试问得最多。'], [14]),
    ('文本框 19', ['实习'], [52], None, None, None, False),
    ('文本框 27', ['跟班'], [46], None, None, None, False),
]

# 长期
E[19] = [
    ('文本框 16', ['3.长期计划（大四—入职）'], [20]),
    ('组合 6/文本框 2047', ['供'], [42]),
    ('组合 6/文本框 2048', ['电'], [42]),
    ('组合 6/文本框 2049', ['检'], [42]),
    ('组合 6/文本框 2050', ['修'], [42]),
    ('组合 6/文本框 2051', ['上'], [42]),
    ('组合 6/文本框 2052', ['岗'], [42]),
    ('文本框 42', ['9—11 月：地铁、铁路局、施工单位三条线同时投；体检、政审材料提前备齐。'], [13]),
    ('文本框 13', ['入职第 1 年：跟班学作业票，能独立完成一次倒闸、一次接触网巡检。'], [13]),
]

E[20] = [('文本框 5', ['05', '评估调整'])]

# 评估调整
E[21] = [
    ('组合 74/PA-文本框 81', ['短期（大一—大二）'], [11], None, None, None, False),
    ('组合 74/组合 77/PA-圆角矩形 88', ['视力/色觉不过关'], [9], None, None, None, None, 0),
    ('组合 74/组合 77/PA-圆角矩形 88', ['电工证没考下来'], [9], None, None, None, None, 1),
    ('组合 74/组合 77/PA-圆角矩形 97', ['体检复查了吗？'], [8], None, None, None, None, 0),
    ('组合 74/组合 77/PA-圆角矩形 97', ['证到手了吗？'], [8], None, None, None, None, 1),
    ('组合 84/PA-文本框 81', ['中期（大三）'], [11], None, None, None, False),
    ('组合 84/组合 87/PA-圆角矩形 88', ['实习没找到'], [9], None, None, None, None, 0),
    ('组合 84/组合 87/PA-圆角矩形 88', ['扛不住夜班'], [9], None, None, None, None, 1),
    ('组合 84/组合 87/PA-圆角矩形 97', ['有跟岗证明吗？'], [8], None, None, None, None, 0),
    ('组合 84/组合 87/PA-圆角矩形 97', ['连上三天夜班行不行？'], [8], None, None, None, None, 1),
    ('组合 95/PA-文本框 81', ['长期（大四—入职）'], [11], None, None, None, False),
    ('组合 95/组合 98/PA-圆角矩形 88', ['校招没进'], [9], None, None, None, None, 0),
    ('组合 95/组合 98/PA-圆角矩形 88', ['入职后想跑'], [9], None, None, None, None, 1),
    ('组合 95/组合 98/PA-圆角矩形 97', ['面试能说清岗位吗？'], [8], None, None, None, None, 0),
    ('组合 95/组合 98/PA-圆角矩形 97', ['还能坚持倒班吗？'], [8], None, None, None, None, 1),
    ('文本框 134', ['大二上做完体检，有问题先矫正',
                    '电工证没过，寒假回来补考',
                    '体能每周练三次，别等面试前突击'], [10]),
    ('文本框 135', ['实习投 8 家：地铁、铁路局、施工单位',
                    '跟岗时主动问夜班怎么排',
                    '真扛不住就转设备维保，不硬撑'], [10]),
    ('文本框 136', ['三条线同时投，别只等地铁',
                    '没进就先去施工单位干两年再考',
                    '入职第一年先熬住，别急着跳'], [10]),
]

E[22] = [
    ('标题 1', ['感谢聆听']),
    ('副标题 2', ['愿几年后，我能在地铁停运的那四个小时里把设备修好'], [20], None, None, None, False),
    ('文本占位符 4', ['汇报人：'], [18], None, None, PP_ALIGN.RIGHT, False),
    ('文本占位符 3', ['2026 年 11 月'], [18], None, None, PP_ALIGN.RIGHT, False),
]

# ---------------------------------------------------------------- apply text
for idx, edits in E.items():
    slide = prs.slides[idx - 1]
    for item in edits:
        path, lines = item[0], item[1]
        sizes = item[2] if len(item) > 2 else None
        colors = item[3] if len(item) > 3 else None
        bolds = item[4] if len(item) > 4 else None
        aligns = item[5] if len(item) > 5 else None
        wrap = item[6] if len(item) > 6 else None
        occ = item[7] if len(item) > 7 else 0
        set_lines(find(slide, path, occ if isinstance(occ, int) else 0),
                  lines, sizes, colors, bolds, aligns, wrap)

for idx, paths in D.items():
    slide = prs.slides[idx - 1]
    for p in paths:
        delete_shape(slide, p)

# ---------------------------------------------------------------- geometry
box(prs.slides[3], '文本框 42', left=0.54, top=5.58, width=5.55, height=1.30)
box(prs.slides[8], '组合 90/文本框 91', left=10.30, top=2.85, width=1.85, height=1.35)
box(prs.slides[11], '文本框 68', left=0.70, top=6.14, width=3.05, height=0.85)
box(prs.slides[13], '文本框 98', left=4.55, top=4.28, width=1.10, height=0.58)
box(prs.slides[17], '文本框 27', left=9.55, top=1.55, width=2.70, height=1.50)

# ---------------------------------------------------------------- global font
for slide in prs.slides:
    for sh in iter_shapes(slide.shapes):
        if sh.has_text_frame:
            set_font_all(sh)
        if getattr(sh, "has_chart", False) and sh.has_chart:
            try:
                sh.chart.font.name = FONT
            except Exception:
                pass


# ---------------------------------------------------------------- charts
def chart_on(slide, name):
    for sh in iter_shapes(slide.shapes):
        if sh.name == name and getattr(sh, "has_chart", False) and sh.has_chart:
            return sh.chart
    raise KeyError(name)


c = chart_on(prs.slides[7], '图表 72')
cd = CategoryChartData()
cd.categories = ['2019', '2020', '2021', '2022', '2023']
cd.add_series('运营里程（公里）', (6736, 7545, 8708, 9584, 10165))
c.replace_data(cd)
c.has_title = False
for sr in c.series:
    sr.format.fill.solid()
    sr.format.fill.fore_color.rgb = RGBColor(0xC0, 0x50, 0x3F)
    sr.format.line.fill.background()
try:
    va = c.value_axis
    va.minimum_scale = None
    va.maximum_scale = None
    va.major_unit = None
except Exception as e:
    print("axis reset skipped:", e)

c = chart_on(prs.slides[7], '图表 85')
cd = CategoryChartData()
cd.categories = ['变电', '接触网', '监控', '其他']
cd.add_series('岗位构成', (40, 35, 15, 10))
c.replace_data(cd)
c.has_title = False


# ---------------------------------------------------------------- slide 6
def add_text(slide, x, y, w, h, lines, size=15, color=NAVY, bold=False,
             align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        apply_font(r)
    return tb


s6 = prs.slides[5]
add_text(s6, 1.05, 1.62, 4.6, 0.5, ['我已经有的'], 24, NAVY, True)
add_text(s6, 7.05, 1.62, 4.6, 0.5, ['我还缺的'], 24, NAVY, True)

for x in (1.05, 7.05):
    bar = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(2.12),
                              Inches(0.95), Inches(0.07))
    bar.fill.solid()
    bar.fill.fore_color.rgb = DEEP
    bar.line.fill.background()
    bar.shadow.inherit = False

left_items = [
    ('身体底子好', '1000 米不喘，搬东西不怵'),
    ('守规矩', '说好的时间从不迟到'),
    ('能熬夜', '赶作业通宵过，第二天照常'),
    ('问得出口', '不懂就追着人问'),
]
right_items = [
    ('视力临界', '左眼 4.8，得先查清楚'),
    ('没碰过强电', '只在实验课上接过 220V'),
    ('图纸看不懂', '供电系统图还是一团线'),
    ('急了会毛躁', '一催就容易跳步骤'),
]

for col, items in ((1.05, left_items), (7.05, right_items)):
    y = 2.45
    for tag, desc in items:
        dot = s6.shapes.add_shape(MSO_SHAPE.OVAL, Inches(col), Inches(y + 0.08),
                                  Inches(0.30), Inches(0.30))
        dot.fill.solid()
        dot.fill.fore_color.rgb = AMBER
        dot.line.fill.background()
        dot.shadow.inherit = False
        add_text(s6, col + 0.45, y - 0.02, 4.3, 0.38, [tag], 17, NAVY, True)
        add_text(s6, col + 0.45, y + 0.36, 4.8, 0.36, [desc], 13, GREY)
        y += 0.92

band = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.05), Inches(6.42),
                           Inches(11.25), Inches(0.56))
band.fill.solid()
band.fill.fore_color.rgb = AMBER
band.line.fill.background()
band.shadow.inherit = False
tf = band.text_frame
tf.margin_top = 0
tf.margin_bottom = 0
p = tf.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = '这 8 条，就是接下来三年要一条条处理的'
r.font.size = Pt(15)
r.font.bold = True
r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
apply_font(r)

add_text(prs.slides[16], 0.60, 2.36, 1.02, 0.45, ['01'], 26, DEEP, True, PP_ALIGN.CENTER)

prs.save(OUTFILE)
print("saved", OUTFILE)
