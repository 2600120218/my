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

OUTFILE = "职业生涯规划-电气工程及其自动化-考研升学方向.pptx"
FONT = "微软雅黑"
NAVY = RGBColor(0x1E, 0x2B, 0x26)
AMBER = RGBColor(0x0F, 0x3B, 0x33)
DEEP = RGBColor(0xC9, 0xA2, 0x27)
GREY = RGBColor(0x54, 0x64, 0x5C)

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
    ('副标题 2', ['成长赛道 ｜ 一个想考研的人，该怎么过这四年'], [18], None, None, None, False),
    ('文本占位符 4', ['汇报人：　　　　　　学号：　　　　　'], [17], None, None, PP_ALIGN.RIGHT, False),
    ('文本占位符 3', ['汇报时间：2026 年 11 月'], [17], None, None, PP_ALIGN.RIGHT, False),
]

# 目录
E[2] = [
    ('文本框 2', ['自我认知']),
    ('文本框 10', ['环境分析']),
    ('文本框 11', ['升学定位']),
    ('文本框 12', ['备考路线']),
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
    ('组合 28/文本框 31', ['想考研，方向还没定死']),
    ('组合 32/文本框 36', ['电气工程 专硕研究生']),
    ('文本框 42', ['话不多，爱琢磨：一道题想不通会一直想',
                   '选电气是家里建议，也因为我确实喜欢"能把原理讲清楚"的东西；比起动手，我更愿意先把"为什么"弄明白。'],
     [20, 14]),
]

# 实践经历
D[5] = ['文本框 9']
E[5] = [
    ('文本框 27', ['电子设计协会 会员']),
    ('文本框 29', ['院学生会 宣传部 干事']),
    ('文本框 31', ['校运会 · 迎新志愿者']),
    ('文本框 38', ['(1) 校内实践'], [17], None, None, None, False),
    ('文本框 58', ['寒假打算：留校啃完一门网课'], [15]),
    ('文本框 55', ['大一没有实习，也谈不上项目。',
                   '2027 年寒假打算留校，跟着学长把一门电路网课刷完；如果家里有事，就把书带回去看。'],
     [16, 14]),
    ('文本框 4104', ['课外：用 Multisim 仿了个整流电路'], [12.5]),
    ('文本框 4107', ['① 照着教材把半波整流的波形跑出来，第一次觉得公式是能看见的。'], [13]),
    ('文本框 4108', ['② 也发现自己只会照抄——参数一改，波形变成什么样就说不清了。'], [13]),
]

# 能力盘点（自定义）
D[6] = ['文本框 16', '文本框 18', '椭圆 3', '图片 5', '图片 7', '图片 22']
E[6] = [('文本框 8', ['3.能力盘点'])]

E[7] = [('文本框 5', ['02', '环境分析'])]

# 政策背景
E[8] = [
    ('文本框 81', ['“到 2025 年，硕士专业学位研究生招生规模扩大到总规模的三分之二左右。”'], [17]),
    ('文本框 82', ['——《专业学位研究生教育发展方案（2020—2025）》'], [13]),
    ('矩形 77', ['考研报名人数先涨后落'], [16]),
    ('矩形 78', ['2025 年 388 万'], [15]),
    ('文本框 73', ['2019—2025 年全国考研报名人数（万人）'], [11]),
    ('文本框 40', ['整体在降温，电气依然挤'], [19]),
    ('文本框 42', ['专硕占 2/3', '应用型方向机会更多'], [17, 11]),
    ('组合 62/文本框 65', ['总量仍很大']),
    ('组合 62/文本框 66', ['01'], [14], None, None, None, False),
    ('组合 54/文本框 57', ['电气分不低']),
    ('组合 54/文本框 58', ['02'], [14], None, None, None, False),
    ('组合 46/文本框 49', ['二战的人多']),
    ('组合 46/文本框 50', ['03'], [14], None, None, None, False),
    ('组合 74/文本框 76', ['考研不是避风港：先想清楚为什么考，再决定考不考。']),
    ('椭圆 83', ['理性', '报考']),
    ('椭圆 84', ['别', '跟风']),
]

# 就业环境
E[9] = [
    ('文本框 22', ['2.出路对比']),
    ('文本框 89', ['本科和硕士，在电气这行的起点差别是实打实的：研发岗基本要硕士，运维和现场岗本科就够。']),
    ('组合 90/文本框 92', ['2/3'], [34], None, None, None, False),
    ('组合 90/文本框 91', ['专硕招生', '占比目标'], [12, 12]),
    ('文本框 95', ['同一个专业，三条路：本科就业、考研、考公，各有各的代价，没有哪条是稳赚。']),
    ('文本框 103', ['本科就业'], [16], None, None, None, False),
    ('文本框 104', ['读研三年'], [16], None, None, None, False),
    ('文本框 105', ['考公考编'], [16], None, None, None, False),
    ('文本框 97', ['进设备厂、集成商做调试和维护，起薪一般，但能早三年挣钱、早三年攒经验。']),
    ('文本框 98', ['多读三年，进研发或测试岗，起薪高一截；代价是三年时间和一次失败的风险。']),
    ('文本框 99', ['电气对口的岗位不多，多在三不限里；竞争比考研还狠，得先有心理准备。']),
]

E[10] = [('文本框 5', ['03', '升学定位'])]

# 职业测评
E[11] = [
    ('组合 103/PPT世界-6-4', ['01. 霍兰德职业兴趣测试'], [18]),
    ('组合 103/组合 24/文本框 51', ['测评结果：研究型 I']),
    ('组合 103/组合 26/文本框 27', ['喜欢琢磨原理、追根问底；不爱应酬，独处效率高；对"为什么"的兴趣大于"怎么用"。']),
    ('组合 103/组合 26/文本框 29', ['适配：研发、测试、设计、研究所辅助岗。']),
    ('组合 92/PPT世界-6-4', ['02. MBTI 职业性格测评'], [18]),
    ('组合 92/文本框 84', ['1. 喜欢把问题拆开看本质，不爱背结论。',
                            '2. 对不感兴趣的事，很难装出热情。',
                            '3. 想清楚了才行动，容易想太久。',
                            '4. 不爱管人，也不爱被人管。']),
    ('组合 92/组合 88/文本框 90', ['测评结果：', 'INTP'], [10, 20]),
    ('组合 92/文本框 91', ['适配方向：研发、测试、仿真分析']),
    ('文本框 99', ['两次测评都偏"研究型"：适合把一件事钻深，不适合天天跑现场应酬。'
                   '但要提醒自己：研究型不等于适合读研——读研要能忍受长时间的枯燥和不确定，这一点我还没验证过。'
                   '所以大二必须进一次实验室。'], [21]),
    ('组合 101/文本框 69', ['钻研能力']),
    ('组合 105/文本框 107', ['耐得住']),
]

# 行业现状
D[12] = ['图表 3']
D[17] = ['组合 7/图片 23']
E[12] = [
    ('文本框 27', ['2.行业现状及背景']),
    ('文本框 109', ['Power Electronics'], [34]),
    ('文本框 23', ['2020 年至今'], [26]),
    ('文本框 20', ['新能源和储能把电力电子推到了台前：光伏逆变器、储能变流器、车载电源，核心都是"把电变来变去"，'
                   '正好是电气与电子的交叉地带。'], [13]),
    ('文本框 34', ['2024 年我国光伏新增装机约'], [15]),
    ('文本框 44', ['277 GW'], [30]),
    ('文本框 56', ['一半'], [26]),
    ('文本框 68', ['　　　　　　　　　　全球光伏组件有一半以上产自中国，配套的逆变器、变流器需求同步增长'], [11]),
    ('矩形: 圆角 88', ['光伏逆变']),
    ('矩形: 圆角 89', ['储能变流']),
    ('矩形: 圆角 90', ['车载电源']),
    ('文本框 98', ['把直流变交流并网，效率每提高 0.5% 都是钱；重拓扑、重控制。']),
    ('文本框 99', ['电池充放电要双向变换，对安全性和响应速度要求高。']),
    ('文本框 100', ['车规级要求最严，认证周期长，但市场大、岗位多。']),
]

# 升学需求 → 院校梯度
E[13] = [
    ('文本框 34', ['3.升学目标']),
    ('文本框 13', ['电气专硕不是"想考就能上"，先把目标分成三档：'], [22]),
    ('文本框 40', ['专业课多为电路或电力系统分析，各校自命题，务必以当年招生简章为准'], [13]),
    ('组合 35/矩形: 圆角 19', ['冲']),
    ('组合 35/矩形: 圆角 28', ['广西大学 · 电气专硕']),
    ('组合 11/矩形: 圆角 22', ['稳']),
    ('组合 11/矩形: 圆角 29', ['桂林电子科技大学 · 本校']),
    ('组合 8/矩形: 圆角 26', ['保']),
    ('组合 8/矩形: 圆角 30', ['桂林理工 / 广西科技']),
    ('组合 33/矩形: 圆角 32', ['备']),
    ('组合 33/矩形: 圆角 31', ['二战一年，或直接就业']),
    ('矩形 51', ['本校最稳'], [11]),
    ('矩形 55', ['真题要早拿'], [10]),
    ('矩形 54', ['别只报一所'], [11]),
]

# 薪资与胜任标准
E[14] = [
    ('文本框 14', ['多读三年，值不值这笔账'], [19]),
    ('文本框 17', ['电力电子方向本科 6—8 千/月，硕士 10—14 千/月。三年时间成本，加上可能的一次二战，'
                   '这笔账得自己算，别人替不了。'], [13]),
    ('文本框 28', ['初试四门：政治、英语、数学、专业课（电路或电力系统分析）。数学和专业课决定上限。'], [10.5]),
    ('文本框 95', ['复试看什么：', '导师关心的是"能不能干活"——会不会仿真、读不读得懂英文文献、进没进过实验室。'], [13, 12]),
    ('文本框 100', ['英语：', '四级是底线，六级是加分；不少学校复试要当场读英文摘要。'], [13, 12]),
    ('文本框 25', ['心态：', '备考是十个月的独处，中途会反复怀疑自己，得提前想好"考不上怎么办"。'], [13, 12]),
]

# 信息与体验
E[15] = [
    ('文本框 30', ['5.信息与体验']),
    ('文本框 22', ['在 B 站和知乎刷了一个学期的考研经验贴，最大的感受是：成功经验都相似，失败原因各不相同。'], [11]),
    ('文本框 24', ['别只看上岸帖'], [16]),
    ('文本框 95', ['找了一位考上本校的学长聊：他说专业课真题要早拿，数学别拖到暑假，英语每天都要碰。'], [11]),
    ('文本框 98', ['学长的话最有用'], [15]),
    ('文本框 109', ['去听了一场校内宣讲，才发现同一所学校，学硕和专硕的考试科目、学费、培养方式都不一样。'], [11]),
    ('文本框 112', ['学硕专硕要分清'], [15]),
    ('文本框 119', ['最大的收获是知道了自己的短板在哪：英语和数学，都不是靠突击能解决的。'], [11]),
    ('文本框 125', ['先认清短板'], [16]),
]

E[16] = [('文本框 5', ['04', '备考路线'])]

# 短期
E[17] = [
    ('文本框 17', ['1.短期计划（大一—大二）'], [20]),
    ('文本框 30', ['数学别欠账', '英语天天碰'], [26, 26]),
    ('文本框 8', ['不追求一次学透：高数、线代跟着课走，课后题自己做一遍；不会的先记下来，别攒到考前。'], [15]),
    ('文本框 2048', ['英语从背单词开始，每天 30 个，坚持比强度更重要；大二争取进实验室，帮师兄焊板子、跑仿真也行。'], [15]),
]

# 中期
E[18] = [
    ('文本框 9', ['2.中期计划（大三）'], [20]),
    ('文本框 8', ['定校、定专业课，把复习拉成十个月的长线'], [24]),
    ('文本框 2060', ['大三上确定三档院校，想办法拿到目标校真题；3 月开始数学和英语长线，暑假留校不回家。'
                     '专业课按目标校指定教材走，别贪多买一堆资料。'], [14]),
    ('文本框 19', ['定校'], [52], None, None, None, False),
    ('文本框 27', ['真题'], [46], None, None, None, False),
]

# 长期
E[19] = [
    ('文本框 16', ['3.长期计划（大四—上岸）'], [20]),
    ('组合 6/文本框 2047', ['电'], [42]),
    ('组合 6/文本框 2048', ['气'], [42]),
    ('组合 6/文本框 2049', ['专'], [42]),
    ('组合 6/文本框 2050', ['硕'], [42]),
    ('组合 6/文本框 2051', ['上'], [42]),
    ('组合 6/文本框 2052', ['岸'], [42]),
    ('文本框 42', ['9—12 月：每天固定 8 小时，数学真题两遍、英语真题三遍、专业课真题三遍，周末按考试时间模考。'], [13]),
    ('文本框 13', ['次年 3—4 月复试：提前准备自我介绍和英文问答；同时投几家区内企业，留一条 Plan B。'], [13]),
]

E[20] = [('文本框 5', ['05', '评估调整'])]

# 评估调整
E[21] = [
    ('组合 74/PA-文本框 81', ['短期（大一—大二）'], [11], None, None, None, False),
    ('组合 74/组合 77/PA-圆角矩形 88', ['单词三天打鱼'], [9], None, None, None, None, 0),
    ('组合 74/组合 77/PA-圆角矩形 88', ['数学越攒越多'], [9], None, None, None, None, 1),
    ('组合 74/组合 77/PA-圆角矩形 97', ['连续打卡几天？'], [8], None, None, None, None, 0),
    ('组合 74/组合 77/PA-圆角矩形 97', ['课后题做完了没？'], [8], None, None, None, None, 1),
    ('组合 84/PA-文本框 81', ['中期（大三）'], [11], None, None, None, False),
    ('组合 84/组合 87/PA-圆角矩形 88', ['定校反复改'], [9], None, None, None, None, 0),
    ('组合 84/组合 87/PA-圆角矩形 88', ['复习进度落后'], [9], None, None, None, None, 1),
    ('组合 84/组合 87/PA-圆角矩形 97', ['真题到手了吗？'], [8], None, None, None, None, 0),
    ('组合 84/组合 87/PA-圆角矩形 97', ['每月进度对得上？'], [8], None, None, None, None, 1),
    ('组合 95/PA-文本框 81', ['长期（大四—上岸）'], [11], None, None, None, False),
    ('组合 95/组合 98/PA-圆角矩形 88', ['考前崩心态'], [9], None, None, None, None, 0),
    ('组合 95/组合 98/PA-圆角矩形 88', ['复试被刷'], [9], None, None, None, None, 1),
    ('组合 95/组合 98/PA-圆角矩形 97', ['模考能过国家线？'], [8], None, None, None, None, 0),
    ('组合 95/组合 98/PA-圆角矩形 97', ['Plan B 准备好了？'], [8], None, None, None, None, 1),
    ('文本框 134', ['单词用 App 打卡，断了当天补',
                    '数学每周日清一次欠账',
                    '学不进去就换自习室，别硬熬'], [10]),
    ('文本框 135', ['三档院校只改一次，改完不再动',
                    '每月 1 号对一次进度表',
                    '进度落后就砍资料，不砍时间'], [10]),
    ('文本框 136', ['模考低于国家线 20 分，开始投简历',
                    '复试被刷，先工作一年再决定二战',
                    '不管结果如何，给自己留三个月缓冲'], [10]),
]

E[22] = [
    ('标题 1', ['感谢聆听']),
    ('副标题 2', ['愿四年后，我能在实验室里把那个波形调出来'], [20], None, None, None, False),
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
cd.categories = ['2019', '2020', '2021', '2022', '2023', '2024', '2025']
cd.add_series('报名人数（万人）', (290, 341, 377, 457, 474, 438, 388))
c.replace_data(cd)
c.has_title = False
for sr in c.series:
    sr.format.fill.solid()
    sr.format.fill.fore_color.rgb = RGBColor(0x0F, 0x3B, 0x33)
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
cd.categories = ['学术型', '专业型', '推免', '其他']
cd.add_series('构成', (35, 45, 15, 5))
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
    ('坐得住', '一道题能磨一下午'),
    ('爱刨根问底', '不搞懂原理不舒服'),
    ('自学还行', '网课、公开课能自己啃'),
    ('不太受干扰', '目标单一，认死理'),
]
right_items = [
    ('英语是硬伤', '四级还没过，考研更难过'),
    ('动手一般', '焊板子手抖，实验靠同学'),
    ('没进过实验室', '不知道科研是什么样'),
    ('消息不灵通', '容易错过报名和时间点'),
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
