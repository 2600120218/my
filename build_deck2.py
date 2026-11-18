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

OUTFILE = "职业生涯规划-电气工程及其自动化-工业自动化方向.pptx"
FONT = "微软雅黑"
NAVY = RGBColor(0x24, 0x20, 0x1A)
AMBER = RGBColor(0xE0, 0x8A, 0x3C)
DEEP = RGBColor(0xC4, 0x6B, 0x17)
GREY = RGBColor(0x6B, 0x5F, 0x50)

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
    ('副标题 2', ['成长赛道 ｜ 一个电气生的车间路线图'], [18], None, None, None, False),
    ('文本占位符 4', ['汇报人：　　　　　　学号：　　　　　'], [17], None, None, PP_ALIGN.RIGHT, False),
    ('文本占位符 3', ['汇报时间：2026 年 11 月'], [17], None, None, PP_ALIGN.RIGHT, False),
]

# 目录
E[2] = [
    ('文本框 2', ['自我认知']),
    ('文本框 10', ['环境分析']),
    ('文本框 11', ['职业选择']),
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
    ('组合 28/矩形: 圆角 29', ['学业情况']),
    ('组合 28/文本框 31', ['绩点 3.0 / 4.0（中游）']),
    ('组合 32/文本框 36', ['自动化设备 电气工程师']),
    ('文本框 42', ['坐不住但手不闲：比起啃书，我更想动手',
                   '高考志愿是被"电气"两个字骗进来的——后来发现，我确实喜欢让设备动起来。'],
     [20, 14]),
]

# 实践经历
D[5] = ['文本框 9']
E[5] = [
    ('文本框 27', ['机器人协会 干事']),
    ('文本框 29', ['院学生会 体育部 干事']),
    ('文本框 31', ['校运会 · 迎新志愿者']),
    ('文本框 38', ['(1) 校内实践'], [17], None, None, None, False),
    ('文本框 58', ['寒假跟表哥进厂看了三天'], [15]),
    ('文本框 55', ['大一没有实习，也谈不上项目。',
                   '2027 年寒假跟着在厂里做电工的表哥上了三天班：认了几种断路器，也知道配电柜里不能乱伸手。'],
     [16, 14]),
    ('文本框 4104', ['课外：修好一台旧电风扇'], [14]),
    ('文本框 4107', ['① 风扇不转，拆开发现是启动电容鼓了，换了一个，转起来了。'], [13]),
    ('文本框 4108', ['② 第一次发现"看得懂图"和"修得好东西"是两回事，也第一次觉得这事有意思。'], [13]),
]

# 能力盘点（自定义）
D[6] = ['文本框 16', '文本框 18', '椭圆 3', '图片 5', '图片 7', '图片 22']
E[6] = [('文本框 8', ['3.能力盘点'])]

E[7] = [('文本框 5', ['02', '环境分析'])]

# 政策背景
E[8] = [
    ('文本框 81', ['“到 2025 年，制造业机器人密度较 2020 年实现翻番。”'], [21]),
    ('文本框 82', ['——《“机器人+”应用行动实施方案》，2023 年 1 月'], [13]),
    ('矩形 77', ['工业机器人产量逐年走高'], [16]),
    ('矩形 78', ['2024 年达 55.6 万台'], [16]),
    ('文本框 73', ['2019—2024 年我国工业机器人产量（万台）'], [11]),
    ('文本框 40', ['制造业在换人，也在换"懂电气的人"'], [19]),
    ('文本框 42', ['超 4 成', '自动化岗位要求"会调试"'], [17, 11]),
    ('组合 62/文本框 65', ['绘图不够用']),
    ('组合 62/文本框 66', ['01'], [14], None, None, None, False),
    ('组合 54/文本框 57', ['还得会编程']),
    ('组合 54/文本框 58', ['02'], [14], None, None, None, False),
    ('组合 46/文本框 49', ['现场得出差']),
    ('组合 46/文本框 50', ['03'], [14], None, None, None, False),
    ('组合 74/文本框 76', ['这行不缺岗位，缺的是"来了就能上手"的人。']),
    ('椭圆 83', ['岗位', '不少']),
    ('椭圆 84', ['门槛', '在抬高']),
]

# 就业环境
E[9] = [
    ('文本框 89', ['工业自动化是"项目制"的行业：一个项目接一个项目，人跟着设备走，经验攒得比坐办公室快。']),
    ('组合 90/文本框 92', ['29%'], [34], None, None, None, False),
    ('组合 90/文本框 91', ['2024 年', '产量同比增速'], [12, 12]),
    ('文本框 95', ['三个方向吸纳电气类毕业生：设备制造求"专"、系统集成求"快"、终端工厂求"稳"。']),
    ('文本框 103', ['设备制造'], [16], None, None, None, False),
    ('文本框 104', ['系统集成'], [16], None, None, None, False),
    ('文本框 105', ['终端工厂'], [16], None, None, None, False),
    ('文本框 97', ['汇川、埃斯顿、拓斯达这类做整机和核心部件，要求懂原理、会调试。出差多，但成长快。']),
    ('文本框 98', ['集成商把设备拼成产线，一个项目三五个月，现场改图纸是家常便饭，最能练人。']),
    ('文本框 99', ['柳工、玉柴、五菱这类终端厂，电气岗偏设备维护，节奏慢、稳定，但技术更新也慢。']),
]

E[10] = [('文本框 5', ['03', '职业选择'])]

# 职业测评
E[11] = [
    ('组合 103/PPT世界-6-4', ['01. 霍兰德职业兴趣测试'], [18]),
    ('组合 103/组合 24/文本框 51', ['测评结果：现实型 R']),
    ('组合 103/组合 26/文本框 27', ['喜欢动手、和工具设备打交道；不爱长时间坐着看理论；做事讲实际，对空谈没什么耐心。']),
    ('组合 103/组合 26/文本框 29', ['适配：设备调试、电气维修、产线电控、现场技术支持。']),
    ('组合 92/PPT世界-6-4', ['02. MBTI 职业性格测评'], [18]),
    ('组合 92/文本框 84', ['1. 喜欢自己动手解决问题，不太爱听人指挥。',
                            '2. 对能拆开的机械、电路天然有兴趣。',
                            '3. 现场出故障时反而冷静，不慌。',
                            '4. 不爱做长期计划，容易临时抱佛脚。']),
    ('组合 92/组合 88/文本框 90', ['测评结果：', 'ISTP 鉴赏家']),
    ('组合 92/文本框 91', ['适配方向：设备调试、现场服务、电气维修']),
    ('文本框 99', ['两次测评都指向"动手型"：适合在现场解决问题，不适合长时间坐办公室做研究。'
                   '但测评只是参考——它说的是"我喜欢怎么干活"，不是"我能干好什么"。'
                   '能不能干好，得看大三那次实习。'], [22]),
    ('组合 101/文本框 69', ['动手能力']),
    ('组合 105/文本框 107', ['临场反应']),
]

# 行业现状
D[12] = ['图表 3']
D[17] = ['组合 7/图片 23']
E[12] = [
    ('文本框 27', ['2.行业现状及背景']),
    ('文本框 109', ['Industrial Automation'], [34]),
    ('文本框 23', ['2015 年至今'], [26]),
    ('文本框 20', ['国产自动化品牌这几年起来了：汇川、埃斯顿、雷赛在中低端市场替代进口，价格战打得凶，'
                   '对"能调现场"的工程师需求反而更大。'], [13]),
    ('文本框 34', ['2024 年我国工业机器人产量约'], [15]),
    ('文本框 44', ['55.6 万台'], [30]),
    ('文本框 56', ['40%'], [30]),
    ('文本框 68', ['中低端产线的国产化率已过半，外资品牌仍在高端市场占优'], [11]),
    ('矩形: 圆角 88', ['设备制造']),
    ('矩形: 圆角 89', ['系统集成']),
    ('矩形: 圆角 90', ['终端工厂']),
    ('文本框 98', ['做整机与核心部件，重原理和调试能力；出差多，成长快。']),
    ('文本框 99', ['把设备拼成产线，重现场应变；项目紧、加班多。']),
    ('文本框 100', ['设备维护为主，重稳定性；技术更新慢，天花板低。']),
]

# 就业需求
E[13] = [
    ('文本框 13', ['工业机器人产量逐年抬升，背后是成倍的调试与维护岗位：'], [22]),
    ('文本框 40', ['2021—2024 年我国工业机器人产量（万台，公开资料整理）'], [14]),
    ('组合 35/矩形: 圆角 19', ['2021 年']),
    ('组合 35/矩形: 圆角 28', ['36.6 万台']),
    ('组合 11/矩形: 圆角 22', ['2022 年']),
    ('组合 11/矩形: 圆角 29', ['44.3 万台']),
    ('组合 8/矩形: 圆角 26', ['2023 年']),
    ('组合 8/矩形: 圆角 30', ['42.9 万台']),
    ('组合 33/矩形: 圆角 32', ['2024 年']),
    ('组合 33/矩形: 圆角 31', ['55.6 万台']),
    ('矩形 51', ['本科可投'], [11]),
    ('矩形 55', ['电气/自动化'], [10]),
    ('矩形 54', ['珠三角最多'], [11]),
]

# 薪资与胜任标准
E[14] = [
    ('文本框 14', ['自动化电气工程师：起薪一般，涨得快'], [19]),
    ('文本框 17', ['珠三角本科应届 6—9 千/月，出差补贴 100—200 元/天；干满三年能独立带项目，普遍到 12—18 千。'
                   '广西本地 5—7 千，胜在离家近。'], [13]),
    ('文本框 28', ['专业知识：电工电子、电机与拖动、PLC 原理、传感器——重点在"会用"，不在"背得出"。'], [10.5]),
    ('文本框 95', ['软件与图纸：', '会用 CAD / EPLAN 画电气图，会西门子 S7-1200 或三菱 FX 编程，能调变频器和伺服。'], [13, 12]),
    ('文本框 100', ['证书与门槛：', '低压电工作业证是硬门槛；四级不是必需，但看 datasheet 得能对付。'], [13, 12]),
    ('文本框 25', ['现场能力：', '能在车间站着调一天设备，能跟装配师傅和客户把话说清楚，出差半个月不抱怨。'], [13, 12]),
]

# 职业体验
E[15] = [
    ('文本框 22', ['跟着表哥在厂里待了三天：车间噪音大、油污重，师傅们蹲在设备边上改线，一蹲就是半天。',
                   '和"坐办公室画图"完全是两种活法。',
                   '但设备重新转起来那一刻，确实挺爽。'], [11]),
    ('文本框 24', ['现场比想象中更"糙"'], [16]),
    ('文本框 95', ['和一位做集成的学长聊过：一年有半年在客户厂里，项目紧的时候连轴转。',
                   '他说这行前三年靠"跑"，跑得多、见得才多。'], [11]),
    ('文本框 98', ['出差是常态'], [16]),
    ('文本框 109', ['师傅带徒弟，先让你接线、认元件、递工具，半年后才让你碰程序。',
                    '急不得，但学到的东西是自己的。'], [11]),
    ('文本框 112', ['师徒制，靠现场堆'], [15]),
    ('文本框 119', ['入行门槛不算高：本科加电工证就能进。但想涨薪，得能独立带项目。',
                    '这行不看你学校多好，看你能不能把设备调好。'], [11]),
    ('文本框 125', ['门槛不高，靠自己'], [16]),
]

E[16] = [('文本框 5', ['04', '行动路线'])]

# 短期
E[17] = [
    ('文本框 17', ['1.短期计划（大一—大二）'], [20]),
    ('文本框 30', ['先不挂科', '拿下电工证'], [26, 26]),
    ('文本框 8', ['不跟人比绩点：先把高数、电路、C 语言稳住不挂，绩点保 3.0 以上，别在大二被分流。'], [15]),
    ('文本框 2048', ['进机器人协会，从接线、焊板、写单片机开始；大二考低压电工证，暑假去表哥厂里再待两周。'], [15]),
]

# 中期
E[18] = [
    ('文本框 9', ['2.中期计划（大三）'], [20]),
    ('文本框 8', ['把 PLC 摸熟，做一条能演示的小产线'], [24]),
    ('文本框 2060', ['大三主攻西门子 S7-1200：自己搭一条"上料—检测—分拣"的小线，能跑通就写进简历。'
                     '暑期争取去自动化集成商实习，哪怕不给钱。'], [14]),
    ('文本框 19', ['实习'], [52], None, None, None, False),
    ('文本框 27', ['PLC'], [46], None, None, None, False),
]

# 长期
E[19] = [
    ('文本框 16', ['3.长期计划（大四—入职）'], [20]),
    ('组合 6/文本框 2047', ['自'], [46]),
    ('组合 6/文本框 2048', ['动'], [46]),
    ('组合 6/文本框 2049', ['化'], [46]),
    ('组合 6/文本框 2050', ['工'], [46]),
    ('组合 6/文本框 2051', ['程'], [46]),
    ('组合 6/文本框 2052', ['师'], [46]),
    ('文本框 42', ['入职第 1 年：跟着师傅跑现场，能独立完成一台设备的接线和简单调试。'], [14]),
    ('文本框 13', ['入职 2—3 年：能独立负责一个小项目，会改图、会改程序、能跟客户对接。'], [14]),
]

E[20] = [('文本框 5', ['05', '评估调整'])]

# 评估调整
E[21] = [
    ('组合 74/PA-文本框 81', ['短期（大一—大二）'], [11], None, None, None, False),
    ('组合 74/组合 77/PA-圆角矩形 88', ['高数、电路挂科'], [9], None, None, None, None, 0),
    ('组合 74/组合 77/PA-圆角矩形 88', ['电工证没考下来'], [9], None, None, None, None, 1),
    ('组合 74/组合 77/PA-圆角矩形 97', ['这学期有没有挂科？'], [8], None, None, None, None, 0),
    ('组合 74/组合 77/PA-圆角矩形 97', ['证到手了吗？'], [8], None, None, None, None, 1),
    ('组合 84/PA-文本框 81', ['中期（大三）'], [11], None, None, None, False),
    ('组合 84/组合 87/PA-圆角矩形 88', ['PLC 学不下去'], [9], None, None, None, None, 0),
    ('组合 84/组合 87/PA-圆角矩形 88', ['暑期实习没着落'], [9], None, None, None, None, 1),
    ('组合 84/组合 87/PA-圆角矩形 97', ['小产线跑通了没？'], [8], None, None, None, None, 0),
    ('组合 84/组合 87/PA-圆角矩形 97', ['实习证明有没有？'], [8], None, None, None, None, 1),
    ('组合 95/PA-文本框 81', ['长期（大四—入职）'], [11], None, None, None, False),
    ('组合 95/组合 98/PA-圆角矩形 88', ['秋招没拿到 offer'], [9], None, None, None, None, 0),
    ('组合 95/组合 98/PA-圆角矩形 88', ['干半年就想跑'], [9], None, None, None, None, 1),
    ('组合 95/组合 98/PA-圆角矩形 97', ['面试能讲清项目吗？'], [8], None, None, None, None, 0),
    ('组合 95/组合 98/PA-圆角矩形 97', ['还能不能长期出差？'], [8], None, None, None, None, 1),
    ('文本框 134', ['每学期末看一次成绩单，有挂科立刻补',
                    '大二上没考出电工证，寒假回来就报',
                    '协会活动挑一个深做，别都浅尝'] , [10]),
    ('文本框 135', ['大三上学期必须把 PLC 摸到能写程序',
                    '实习投 10 家，集成商、设备厂都投',
                    '做不出小产线，就改成"能讲清原理"'], [10]),
    ('文本框 136', ['先把现场跑满两年，别急着跳',
                    '每年更新一次简历，记下做过的项目',
                    '三年还带不了项目，就转售后或考编'], [10]),
]

E[22] = [
    ('标题 1', ['感谢聆听']),
    ('副标题 2', ['愿几年后，我能让一条产线稳稳地转起来'], [20], None, None, None, False),
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
box(prs.slides[8], '组合 90/文本框 91', left=10.35, top=2.85, width=1.80, height=1.35)
box(prs.slides[11], '文本框 68', left=0.70, top=6.14, width=3.15, height=0.85)
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
cd.categories = ['2019', '2020', '2021', '2022', '2023', '2024']
cd.add_series('产量（万台）', (18.7, 21.2, 36.6, 44.3, 42.9, 55.6))
c.replace_data(cd)
c.has_title = False
for sr in c.series:
    sr.format.fill.solid()
    sr.format.fill.fore_color.rgb = RGBColor(0xE0, 0x8A, 0x3C)
    sr.format.line.fill.background()
# 模板的数值轴锁死了旧数据的刻度，换成新数据后柱子会被压成一条线
try:
    va = c.value_axis
    va.minimum_scale = None
    va.maximum_scale = None
    va.major_unit = None
except Exception as e:
    print("axis reset skipped:", e)

c = chart_on(prs.slides[7], '图表 85')
cd = CategoryChartData()
cd.categories = ['设备制造', '系统集成', '终端工厂', '其他']
cd.add_series('去向占比', (30, 30, 30, 10))
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
    bar.fill.fore_color.rgb = AMBER
    bar.line.fill.background()
    bar.shadow.inherit = False

left_items = [
    ('手不闲', '拆装、焊板、接线，愿意上手'),
    ('不怕脏累', '搬设备、下车间不排斥'),
    ('问得出口', '不懂就问，不怕露怯'),
    ('认准就不换', '决定的事能扛到底'),
]
right_items = [
    ('文化课不稳', '高数、电路都在中游'),
    ('英语差', '四级没过，看 datasheet 费劲'),
    ('编程零基础', 'C 语言刚会皮毛，PLC 没碰过'),
    ('三分钟热度', '兴趣来得快，去得也快'),
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
r.text = '这 8 条，就是接下来三年要动手改的'
r.font.size = Pt(15)
r.font.bold = True
r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
apply_font(r)

# 第 17 页圆环里放编号
add_text(prs.slides[16], 0.60, 2.36, 1.02, 0.45, ['01'], 26, AMBER, True, PP_ALIGN.CENTER)

prs.save(OUTFILE)
print("saved", OUTFILE)
