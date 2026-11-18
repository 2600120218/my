# -*- coding: utf-8 -*-
"""用模板重建：桂电 电气工程及其自动化 大一 职业规划 PPT"""
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

FONT = "微软雅黑"
NAVY = RGBColor(0x19, 0x2A, 0x45)
CYAN = RGBColor(0x19, 0xB9, 0xD8)
BLUE = RGBColor(0x00, 0x99, 0xFF)
GREY = RGBColor(0x5A, 0x6B, 0x7B)

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
    if isinstance(v, (list, tuple)):
        return list(v)
    return [v]


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
            r = para.add_run()
            r.text = line
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
    tf = shape.text_frame
    for p in tf.paragraphs:
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

E[1] = [
    ('标题 1', ['电气工程及其自动化', '大学生职业生涯规划'], None, None, None, None, False),
    ('副标题 2', ['成长赛道 ｜ 一个普通电气生的四年路线图'], [18], None, None, None, False),
    ('文本占位符 4', ['汇报人：骆绍杰　学号：2600120218'], [17], None, None, PP_ALIGN.RIGHT, False),
    ('文本占位符 3', ['汇报时间：2026 年 11 月'], [17], None, None, PP_ALIGN.RIGHT, False),
]

E[2] = [
    ('文本框 2', ['自我认知']),
    ('文本框 10', ['环境分析']),
    ('文本框 11', ['职业定位']),
    ('文本框 12', ['行动路径']),
    ('文本框 16', ['评估调整']),
]

E[3] = [('文本框 22', ['01', '自我认知'])]

E[4] = [
    ('矩形: 圆角 13', ['骆绍杰']),
    ('矩形: 圆角 19', ['2026级 大一']),
    ('组合 20/文本框 23', ['桂林电子科技大学']),
    ('组合 24/文本框 27', ['电气工程及其自动化']),
    ('组合 28/矩形: 圆角 29', ['学业情况']),
    ('组合 28/文本框 31', ['绩点 3.2 / 4.0（大一上）']),
    ('组合 32/文本框 36', ['南方电网 地市局 运维岗']),
    ('文本框 42', ['求稳，但不躺平：想做看得见结果的技术活',
                   '志愿填电气，图的是"学得会、用得上"；一学期下来，我更愿意和电路、设备打交道。'],
     [20, 14]),
]

# --- S5 实践经历
D[5] = ['文本框 9']
E[5] = [
    ('文本框 27', ['电子设计协会 干事']),
    ('文本框 29', ['院学生会 学习部 干事']),
    ('文本框 31', ['校运会 · 迎新志愿者']),
    ('文本框 38', ['(1) 校内实践'], [17], None, None, None, False),
    ('文本框 58', ['寒假打算：县供电所跟岗一周'], [15]),
    ('文本框 55', ['大一还没有正式实习。',
                   '2027 年寒假回家乡，到县供电所跟岗一周——先看清楚这份工作每天在干什么。'],
     [16, 14]),
    ('文本框 4104', ['模电课设：±5V 直流稳压电源'], [14]),
    ('文本框 4107', ['① 独立完成 原理图 → PCB 焊接 → 调试，把输出纹波从 80mV 压到 25mV。'], [13]),
    ('文本框 4108', ['② 第一次体会"仿真对、实物不对"：查了两天，问题出在地线上。'], [13]),
]

# --- S6 能力盘点（自定义重绘）
D[17] = ['组合 7/图片 23']
D[6] = ['文本框 16', '文本框 18', '椭圆 3', '图片 5', '图片 7', '图片 22']
E[6] = [('文本框 8', ['3.能力盘点'])]

E[7] = [('文本框 5', ['02', '环境分析'])]

# --- S8 政策背景
E[8] = [
    ('文本框 81', ['“构建以新能源为主体的新型电力系统。”'], [22]),
    ('文本框 82', ['——2021 年 3 月，中央财经委员会第九次会议'], [14]),
    ('矩形 77', ['毕业生规模逐年走高'], [16]),
    ('矩形 78', ['2025 届达 1222 万'], [16]),
    ('文本框 73', ['2015—2025 届高校毕业生人数（万人）'], [11]),
    ('文本框 40', ['就业总量压力仍在'], [20]),
    ('文本框 42', ['超 60%', '担心"专业不对口"'], [18, 12]),
    ('组合 62/文本框 65', ['报考人数多']),
    ('组合 62/文本框 66', ['01'], [14], None, None, None, False),
    ('组合 54/文本框 57', ['名额增幅慢']),
    ('组合 54/文本框 58', ['02'], [14], None, None, None, False),
    ('组合 46/文本框 49', ['基层要下站所']),
    ('组合 46/文本框 50', ['03'], [14], None, None, None, False),
    ('组合 74/文本框 76', ['电气是"窄门但稳"：早规划一年，选择权就多一分。']),
    ('椭圆 83', ['竞争', '激烈']),
    ('椭圆 84', ['毕业生', '持续增长']),
]

# --- S9 就业环境
E[9] = [
    ('文本框 89', ['电力行业是典型的"重资产、长周期"行业：技术积累不会白费，入行越久越值钱。']),
    ('组合 90/文本框 92', ['6.8%'], [36], None, None, None, False),
    ('组合 90/文本框 91', ['2024 年', '用电量增速'], [12, 12]),
    ('文本框 95', ['三个方向吸纳了电气类约八成毕业生：电网求"稳"、发电求"新"、装备制造求"快"。']),
    ('文本框 103', ['电网系统'], [16], None, None, None, False),
    ('文本框 104', ['发电与新能源'], [16], None, None, None, False),
    ('文本框 105', ['电气装备制造'], [16], None, None, None, False),
    ('文本框 97', ['南方电网、国家电网每年统考招聘，岗位覆盖变电运维、配电运检、调度等。本科可报，但地市局竞争激烈，县级公司机会更多。']),
    ('文本框 98', ['五大发电与新能源企业（华能、国家能源、光伏与储能厂商）需求增长快。作业环境偏现场，适合能吃苦、接受倒班的年轻人。']),
    ('文本框 99', ['汇川、南瑞、许继、正泰等做设备与控制，看项目经验和动手能力。起薪弹性大，但出差和加班多。']),
]

E[10] = [('文本框 5', ['03', '职业定位'])]

# --- S11 职业测评
E[11] = [
    ('组合 103/PPT世界-6-4', ['01. 霍兰德职业兴趣测试'], [18]),
    ('组合 103/组合 24/文本框 51', ['测评结果：现实型 R']),
    ('组合 103/组合 26/文本框 27', ['愿意动手，喜欢和工具设备打交道；偏好规则明确、结果可验证的事，对空泛的讨论兴趣不大。']),
    ('组合 103/组合 26/文本框 29', ['适配：变电运维、配电运检、设备调试、电气绘图。']),
    ('组合 92/PPT世界-6-4', ['02. MBTI 职业性格测评'], [18]),
    ('组合 92/文本框 84', ['1. 做事有计划，答应的事会按时交。',
                            '2. 守规矩、认死理，适合有标准流程的岗位。',
                            '3. 不爱出风头，团队里更像"干活的那个"。',
                            '4. 遇到突发状况会先紧张，需要刻意练习。']),
    ('组合 92/组合 88/文本框 90', ['测评结果：', 'ISTJ 物流师']),
    ('组合 92/文本框 91', ['适配方向：运维检修、二次调试、工程设计']),
    ('文本框 99', ['两次测评指向同一类工作：有明确标准、能动手、结果可验证——这和变电运维的日常高度吻合。'
                   '但要说清楚：测评只是镜子，不是判决书。它说明"我大概是这样的人"，不能证明"我一定适合这份工作"。'
                   '真正的判断，得靠大三那次实习。'], [22]),
    ('组合 101/文本框 69', ['动手能力']),
    ('组合 105/文本框 107', ['稳定性']),
]

# --- S12 行业现状
D[12] = ['图表 3']
E[12] = [
    ('文本框 27', ['2.行业现状及背景']),
    ('文本框 109', ['Power System'], [40]),
    ('文本框 23', ['2021 年至今'], [26]),
    ('文本框 20', ['“双碳”目标下，电力系统正从"源随荷动"转向"源网荷储协同"，新能源装机占比快速提升，'
                   '电网侧对运维、调度、二次设备的人才需求持续存在。'], [13]),
    ('文本框 34', ['中电联数据：2024 年全社会用电量同比增长'], [15]),
    ('文本框 44', ['6.8%'], [36]),
    ('文本框 56', ['80%'], [30]),
    ('文本框 68', ['电气类本科毕业生进入电力及相关行业的比例，长期稳定在八成以上'], [11]),
    ('矩形: 圆角 88', ['电网系统']),
    ('矩形: 圆角 89', ['发电与新能源']),
    ('矩形: 圆角 90', ['电气装备制造']),
    ('文本框 98', ['统考招聘，岗位稳定、福利完善；缺点是地域固定、晋升按资历排。']),
    ('文本框 99', ['风光储装机高速扩张，现场作业多、成长快；缺点是项目地偏远、流动性大。']),
    ('文本框 100', ['重项目与动手能力，起薪弹性大；缺点是出差多、节奏快。']),
]

# --- S13 就业需求
E[13] = [
    ('文本框 13', ['广西电网及区内电气岗位需求，近几年大致如此：'], [24]),
    ('文本框 40', ['2022—2025 年南方电网校园招聘规模（估算）'], [15]),
    ('组合 35/矩形: 圆角 19', ['2022 年']),
    ('组合 35/矩形: 圆角 28', ['约 8000 人']),
    ('组合 11/矩形: 圆角 22', ['2023 年']),
    ('组合 11/矩形: 圆角 29', ['约 8300 人']),
    ('组合 8/矩形: 圆角 26', ['2024 年']),
    ('组合 8/矩形: 圆角 30', ['约 8600 人']),
    ('组合 33/矩形: 圆角 32', ['2025 年']),
    ('组合 33/矩形: 圆角 31', ['约 8800 人']),
    ('矩形 51', ['本科可报'], [11]),
    ('矩形 55', ['电气类为主'], [11]),
    ('矩形 54', ['县公司机会多'], [11]),
]

# --- S14 薪资与胜任标准
E[14] = [
    ('文本框 14', ['电网起薪不算高，胜在稳定与福利'], [20]),
    ('文本框 17', ['广西地市供电局本科转正后，年到手约 8—10 万元（含绩效与福利）；'
                   '装备制造企业本科起薪 6—9 千/月，出差补贴另计。'], [14]),
    ('文本框 28', ['专业知识：电路、电机学、电力系统分析、继电保护、高电压技术——这五门是电网统考的核心。'], [11]),
    ('文本框 98', ['01'], [40]),
    ('文本框 95', ['工具与技能：', '会用 CAD 画图、会用 MATLAB/Simulink 仿真、能读懂二次接线图，会用万用表与继保测试仪。'], [14, 13]),
    ('文本框 100', ['证书与门槛：', '英语四级、低压电工作业证、计算机二级；还要通过统一笔试和面试。'], [14, 13]),
    ('文本框 25', ['沟通与抗压：', '能倒班、能出抢修、能在班前会上把问题讲清楚；被师傅批评时不玻璃心。'], [14, 13]),
]

# --- S15 职业体验
E[15] = [
    ('文本框 22', ['在县城变电站跟岗一天：设备区噪音大、夏天闷热，安全帽和绝缘鞋一穿就是半天。',
                   '和"坐在办公室看屏幕"完全是两回事。',
                   '回来的路上我在想：这样的环境，我能待十年吗？'], [11]),
    ('文本框 24', ['现场脏、吵、热'], [16]),
    ('文本框 95', ['和两位在电网工作的学长聊过：运维是 24 小时值班加倒班，夜里抢修是常态。',
                   '他们说前三年最难熬的不是技术，是作息。',
                   '这一点我得提前接受，而不是入职后才发现。'], [11]),
    ('文本框 98', ['倒班与应急是常态'], [16]),
    ('文本框 109', ['师傅带徒弟，前三年主要靠"跟"和"记"：跟班、记票、背规程。',
                    '想快也快不了，急也没用。',
                    '能沉住气的人，反而走得远。'], [11]),
    ('文本框 112', ['师徒制，靠时间积累'], [16]),
    ('文本框 119', ['门槛是硬的：统考笔试加面试，证书缺一样都卡。',
                    '但一旦进去，职业寿命长、抗风险强。',
                    '这和我"求稳"的性格是匹配的。'], [11]),
    ('文本框 125', ['门槛硬但稳'], [16]),
]

E[16] = [('文本框 5', ['04', '行动路径'])]

# --- S17 短期
E[17] = [
    ('文本框 17', ['1.短期计划（大一—大二）'], [20]),
    ('文本框 30', ['绩点冲前 30%', '先过英语四级'], [26, 26]),
    ('文本框 8', ['不贪多：先把高数、电路、C 语言三门地基打牢，绩点从 3.2 提到 3.5 以上，专业排名进前 30%。'], [15]),
    ('文本框 2048', ['加入电子设计协会，从焊板子、写单片机开始；2027 年参加一次校电子设计竞赛，先攒"独立做完一个东西"的经验。'], [15]),
]

# --- S18 中期
E[18] = [
    ('文本框 9', ['2.中期计划（大三）'], [20]),
    ('文本框 8', ['考下低压电工证，拿到一次真正的暑期实习'], [24]),
    ('文本框 2060', ['大三暑期争取南方电网"实习生计划"或区内电气企业实习；同时把继电保护和电力系统分析学扎实——'
                     '这两门是统考大头，也是面试最常问的。'], [14]),
    ('文本框 19', ['实习'], [52], None, None, None, False),
    ('文本框 27', ['考证'], [52], None, None, None, False),
]

# --- S19 长期
E[19] = [
    ('文本框 16', ['3.长期计划（大四—入职）'], [20]),
    ('组合 6/文本框 2047', ['变'], [46]),
    ('组合 6/文本框 2048', ['电'], [46]),
    ('组合 6/文本框 2049', ['运'], [46]),
    ('组合 6/文本框 2050', ['维'], [46]),
    ('组合 6/文本框 2051', ['技'], [46]),
    ('组合 6/文本框 2052', ['师'], [46]),
    ('文本框 42', ['入职第 1 年：跟班学习，能独立完成一次倒闸操作、写一份规范的作业卡。'], [14]),
    ('文本框 13', ['入职 2—3 年：考取高级工，参加一次公司技能竞赛，争取进班组技术骨干序列。'], [14]),
]

E[20] = [('文本框 5', ['05', '评估调整'])]

# --- S21 评估调整
E[21] = [
    ('组合 74/PA-文本框 81', ['短期（大一—大二）'], [11], None, None, None, False),
    ('组合 74/组合 77/PA-圆角矩形 88', ['绩点掉到中下游'], [9], None, None, None, None, 0),
    ('组合 74/组合 77/PA-圆角矩形 88', ['电赛/协会半途而废'], [9], None, None, None, None, 1),
    ('组合 74/组合 77/PA-圆角矩形 97', ['每学期绩点 ≥ 3.3 ？'], [8], None, None, None, None, 0),
    ('组合 74/组合 77/PA-圆角矩形 97', ['能独立做完一个项目？'], [8], None, None, None, None, 1),
    ('组合 84/PA-文本框 81', ['中期（大三）'], [11], None, None, None, False),
    ('组合 84/组合 87/PA-圆角矩形 88', ['实习和证书没拿到'], [9], None, None, None, None, 0),
    ('组合 84/组合 87/PA-圆角矩形 88', ['统考笔试不过线'], [9], None, None, None, None, 1),
    ('组合 84/组合 87/PA-圆角矩形 97', ['有实习证明 + 低压证？'], [8], None, None, None, None, 0),
    ('组合 84/组合 87/PA-圆角矩形 97', ['模拟卷稳定过线？'], [8], None, None, None, None, 1),
    ('组合 95/PA-文本框 81', ['长期（大四—入职）'], [11], None, None, None, False),
    ('组合 95/组合 98/PA-圆角矩形 88', ['被分到偏远站所'], [9], None, None, None, None, 0),
    ('组合 95/组合 98/PA-圆角矩形 88', ['三年后还在原地打转'], [9], None, None, None, None, 1),
    ('组合 95/组合 98/PA-圆角矩形 97', ['还能接受倒班？'], [8], None, None, None, None, 0),
    ('组合 95/组合 98/PA-圆角矩形 97', ['有没有可迁移的技能？'], [8], None, None, None, None, 1),
    ('文本框 134', ['每学期末复盘绩点与排名，掉出前 50% 就减社团',
                    '协会任务按周打卡，最多只接 2 个',
                    '看不进去的科目，换自习地点和时段'], [10]),
    ('文本框 135', ['大三上结束前拿证，没拿到就寒假补',
                    '实习投 10 家，从县公司开始投',
                    '统考刷题从大三下开始，每周 2 套'], [10]),
    ('文本框 136', ['入职前两年不考虑跳槽，先把规程吃透',
                    '每年更新一次简历和技能清单',
                    '若三年无成长，转设备厂商或考研'], [10]),
]

E[22] = [
    ('标题 1', ['感谢聆听']),
    ('副标题 2', ['愿四年后，我能亲手合上那个开关'], [20], None, None, None, False),
    ('文本占位符 4', ['汇报人：骆绍杰'], [18], None, None, PP_ALIGN.RIGHT, False),
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
        shape = find(slide, path, occ if isinstance(occ, int) else 0)
        set_lines(shape, lines, sizes, colors, bolds, aligns, wrap)

for idx, paths in D.items():
    slide = prs.slides[idx - 1]
    for p in paths:
        delete_shape(slide, p)


# ---------------------------------------------------------------- geometry
box(prs.slides[3], '文本框 42', left=0.54, top=5.58, width=5.55, height=1.30)
box(prs.slides[8], '组合 90/文本框 91', left=10.55, top=2.85, width=1.60, height=1.35)
box(prs.slides[11], '文本框 68', left=0.70, top=6.14, width=3.15, height=0.85)
box(prs.slides[13], '文本框 98', left=4.55, top=4.28, width=1.10, height=0.58)
box(prs.slides[17], '文本框 27', left=9.62, top=1.55, width=2.70, height=1.50)

# replace slide 18 photo with a more relevant one, keeping z-order
s18 = prs.slides[17]
pic_el = None
for sh in s18.shapes:
    if sh.name == '图片 2':
        pic_el = sh._element
        geom = (sh.left, sh.top, sh.width, sh.height)
        break
parent = pic_el.getparent()
pos_index = parent.index(pic_el)
parent.remove(pic_el)
newpic = s18.shapes.add_picture('media/image15.jpeg', geom[0], geom[1], geom[2], geom[3])
parent.remove(newpic._element)
parent.insert(pos_index, newpic._element)

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
cd.categories = [str(y) for y in range(2015, 2026)]
cd.add_series('毕业生人数（万人）', (749, 765, 795, 820, 834, 874, 909, 1076, 1158, 1179, 1222))
c.replace_data(cd)
c.has_title = False

c = chart_on(prs.slides[7], '图表 85')
cd = CategoryChartData()
cd.categories = ['电网系统', '电气装备', '发电与新能源', '其他']
cd.add_series('去向占比', (35, 30, 25, 10))
c.replace_data(cd)
c.has_title = False


# ---------------------------------------------------------------- slide 6 rebuild
def add_text(slide, x, y, w, h, lines, size=15, color=NAVY, bold=False,
             align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
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
    bar.fill.fore_color.rgb = CYAN
    bar.line.fill.background()
    bar.shadow.inherit = False

left_items = [
    ('能坐得住', '焊板子、调电路，一坐一下午不烦'),
    ('肯问', '不懂就问学长老师，不怕露怯'),
    ('手不笨', '万用表、示波器、电烙铁上手快'),
    ('目标清楚', '认准电气，暂时不摇摆'),
]
right_items = [
    ('绩点不够看', '3.2，离专业前 30% 还有距离'),
    ('英语是短板', '四级还没过，是硬门槛'),
    ('零项目', '没独立做完过一个完整作品'),
    ('怕表达', '当着一屋子人讲话会紧张'),
]

for col, items in ((1.05, left_items), (7.05, right_items)):
    y = 2.45
    for tag, desc in items:
        dot = s6.shapes.add_shape(MSO_SHAPE.OVAL, Inches(col), Inches(y + 0.08),
                                  Inches(0.30), Inches(0.30))
        dot.fill.solid()
        dot.fill.fore_color.rgb = CYAN
        dot.line.fill.background()
        dot.shadow.inherit = False
        add_text(s6, col + 0.45, y - 0.02, 4.3, 0.38, [tag], 17, NAVY, True)
        add_text(s6, col + 0.45, y + 0.36, 4.6, 0.36, [desc], 13, GREY)
        y += 0.92

band = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.05), Inches(6.42),
                           Inches(11.25), Inches(0.56))
band.fill.solid()
band.fill.fore_color.rgb = CYAN
band.line.fill.background()
band.shadow.inherit = False
tf = band.text_frame
tf.margin_top = 0
tf.margin_bottom = 0
p = tf.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = '这 8 条，就是未来三年要一条条划掉的清单'
r.font.size = Pt(15)
r.font.bold = True
r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
apply_font(r)

# slide 17: put "01" inside the emptied ring
add_text(prs.slides[16], 0.60, 2.36, 1.02, 0.45, ['01'], 26, CYAN, True, PP_ALIGN.CENTER)

prs.save("骆绍杰-电气工程及其自动化-职业生涯规划.pptx")
print("saved")
