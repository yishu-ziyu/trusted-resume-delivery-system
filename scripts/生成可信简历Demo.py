# -*- coding: utf-8 -*-
"""生成 JD 驱动的可信简历 Demo。

这个脚本不调用大模型，先用已核查的本地材料做一个可打开、可检查的最小闭环：
JD → 结构化数据 → 事实索引 → 匹配矩阵 → ATS/展示版 Typst/PDF → PNG 预览 → 核查报告。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import fitz

PROJECT_DIR = Path('/Users/mahaoxuan/Desktop/AI产品经理/项目D-简历PDF生成器')
OUT = PROJECT_DIR / 'output' / '新版可信简历Demo_AI研发产品线'
SRC_RESUME = Path('/Users/mahaoxuan/Desktop/春招/马浩宣简历.pdf')
PHOTO = Path('/Users/mahaoxuan/Desktop/春招/00-个人材料/照片/证件照.jpg')

JD_TEXT = '''主要职责
制定研发类产品线的版本迭代计划,参与产品路线图的梳理与落地执行,确保产品演进与业务目标保持一致。
深入业务一线,参与需求的调研、收集与整理;撰写产品需求文档(PRD)和用户故事,协同开发、测试团队推动求高质量交付。
跟踪AI技术(如大模型、NLP、智能体等)发展动态,结合业务场景开展调研与竞品分析,协助设计智能化产品功能。
负责产品核心数据的日常跟踪与基础分析,收集并整理用户反馈,输出分析报告,为产品迭代优化提供数据支撑。
任职要求
本科及以上学历,应届毕业生或1-2年ToB/SaaS产品相关经验者均可,有相关实习或项目作品者优先。
具备良好的逻辑思维与业务理解能力,能熟练使用各种AI工具,平台。
具备优秀的沟通表达能力和团队协作意识,能够主动与业务方、研发团队保持高效沟通,推进事项落地。
对用户体验有敏锐感知,具备较强的同理心和用户视角;自驱力强、学习能力强,能快速理解业务逻辑并转化为产品方案。
对AI技术有浓厚兴趣和基础认知,了解主流大模型能力及常见应用场景;有AI相关产品实践、课题研究或个人探索项目者尤佳。'''

FACTS = [
    ('F01', '华侨大学经济学本科，汉语言文学辅修，毕业时间 2026.06。', '原始简历PDF；春招/01-求职材料/简历/草稿版/简历.txt', '高'),
    ('F02', '总绩点排名专业前15%，近一年排名前5%。', '原始简历PDF；草稿简历TXT', '高'),
    ('F03', '主修课程包括社会经济调研、经济博弈论、经济分析与预测等。', '原始简历PDF；草稿简历TXT', '高'),
    ('F04', '深圳海坤投资管理有限公司行研分析师代理组长，独立撰写《中国AI Agent投资机会分析报告》《科大讯飞出海研究及落地路径分析》。', '原始简历PDF；既有事实清单', '高'),
    ('F05', '海坤经历包含 JD 制定、简历筛选、候选人跟进、结构化面试评估；春招主简历写为完成30份简历筛选、转化3名候选人入职。', '春招/马浩宣简历.pdf', '中：桌面旧简历为28份/2名，需用户最终确认'),
    ('F06', '招商银行泉州分行战略部实习：财务更新、异常成本核算、财报交叉比对、合同要素提取、股权结构图梳理。', '原始简历PDF；既有事实清单', '高'),
    ('F07', '辩论队队长：统筹全校辩论联赛，涉及11个参赛班级；负责校队30位成员训练与复盘。', '原始简历PDF；草稿简历TXT', '高'),
    ('F08', '商务谈判竞赛全国总决赛一等奖，负责技术指标体系、协议区间、阶梯式扣款和价格博弈策略。', '原始简历PDF；草稿简历TXT', '高'),
    ('F09', '三创赛福建赛区省级二等奖，负责商业计划书数据挖掘模块，使用行业历史交易数据与竞品存活周期修正销量假设。', '原始简历PDF；草稿简历TXT', '高'),
    ('F10', '营销模拟决策赛道全国决赛二等奖，负责数据分析与策略制定，使用历史销售数据和 Excel 测算收益与成本。', '草稿简历TXT', '高'),
    ('F11', 'AIGC 技术接受度调研报告：围绕 AIGC 采纳意愿、自我控制、比较焦虑、感知有用性进行问卷和模型分析，使用 SPSS PROCESS。', '春招/01-求职材料/作品集/AIGC 技术接受度相关调研报告.pdf；既有事实清单', '高'),
    ('F12', '个人 AI/产品实践：通过 vibe coding 搭建个人网站，做过网页 markdown 插件、Mac 电池管理 APP 等小工具。', '原始简历PDF', '中：具体功能完整度需用户确认'),
    ('F13', '技能包括 Stata、SPSS、Excel、AI IDE/Vibe Coding、Prompt Engineering、AI Agent/AIGC 相关研究。', '原始简历PDF；AI产品岗位技能分析材料', '高'),
]

RESUME_LINES = [
    ('教育经历', [
        '华侨大学｜经济学本科，汉语言文学辅修｜2022.09 - 2026.06',
        '总绩点排名专业前15%，近一年排名前5%；课程包含社会经济调研、经济博弈论、经济分析与预测等。',
    ]),
    ('实习经历', [
        '深圳海坤投资管理有限公司｜行研分析师代理组长｜2026.01 - 至今',
        '跟踪 AI Agent、企业出海与产业应用场景，独立撰写《中国AI Agent投资机会分析报告》《科大讯飞出海研究及落地路径分析》。',
        '围绕趋势判断、竞品格局、商业化路径与落地约束沉淀研究框架，可支持 AI 功能调研、竞品分析与路线图讨论。',
        '参与投资团队实习生招聘，从 JD 制定、简历筛选、候选人跟进到结构化面试评估，训练需求拆解、沟通推进与流程管理能力。',
        '招商银行泉州分行战略部｜实习生｜2026.02 - 2026.03',
        '参与存量客户财务更新、异常成本核算和国企项目财报交叉比对，从复杂材料中提取关键要素并支持业务判断。',
    ]),
    ('AI / 产品化项目', [
        'AIGC 技术接受度调研：基于技术接受模型研究 AIGC 采纳意愿，使用问卷数据与 SPSS PROCESS 进行模型分析，输出研究摘要、假设、数据分析和产品启示。',
        '个人 AI 工具实践：使用 AI IDE / vibe coding 搭建个人网站，并探索网页 markdown 插件、Mac 电池管理 APP 等小工具原型。',
        'AI 产品岗位研究：整理 AI Agent、LLM API、Prompt Engineering、需求分析、PRD 与 B 端产品能力要求，形成岗位技能分析材料。',
    ]),
    ('组织与项目推进', [
        '华侨大学校辩论队 / 经济与金融学院辩论队｜队长｜2023.06 - 2025.06',
        '统筹全校辩论联赛，协调11个参赛班级的赛程、评审标准、场地与评委资源；负责30位队员训练、战术拆解和复盘。',
        '商务谈判竞赛全国总决赛一等奖：负责技术指标体系与博弈策略设计，推动团队形成可执行谈判方案。',
    ]),
    ('技能关键词', [
        '产品与协作：需求调研、竞品分析、用户故事、PRD、路线图讨论、跨团队沟通、结构化表达。',
        'AI 与数据：AI Agent、AIGC 用户研究、Prompt Engineering、Stata、SPSS、Excel、AI IDE / Vibe Coding。',
    ]),
]

MATCH_ROWS = [
    ('版本迭代 / 路线图', '海坤 AI Agent/科大讯飞出海研究；辩论队赛事推进', 'F04, F07', '可写成“参与路线图讨论/产品演进调研”的潜力，不写正式产品负责人'),
    ('需求调研 / PRD / 用户故事', 'AIGC 技术接受度调研；岗位技能分析；个人工具原型', 'F11, F12, F13', 'PRD 经验需谨慎，建议写“具备需求拆解与文档化基础”'),
    ('AI技术跟踪 / 智能化功能', 'AI Agent 投资机会分析、科大讯飞出海研究、Prompt/Agent 学习材料', 'F04, F13', '强匹配，可放在核心定位'),
    ('数据跟踪与分析报告', '招商银行财务更新；AIGC问卷模型；商业竞赛数据分析', 'F06, F10, F11', '强匹配，可突出分析报告输出'),
    ('沟通协作 / 推进落地', '辩论队队长；海坤招聘流程；商务谈判竞赛', 'F05, F07, F08', '强匹配，可转化为跨角色沟通与事项推进'),
    ('ToB/SaaS 经验', '招商银行对公业务、B端产品学习材料', 'F06, F13', '中等匹配，不能写已有 SaaS 产品实习'),
]

TYPOGRAPHY = '''#set document(title: "马浩宣_AI研发产品线_可信简历Demo")
#set page(paper: "a4", margin: (x: 1.35cm, y: 1.2cm))
#set text(font: ("PingFang SC", "Noto Sans CJK SC", "Source Han Sans SC", "Arial"), size: 8.8pt, lang: "zh")
#set par(justify: false, leading: 0.43em)
#let accent = rgb("1f4e79")
#let muted = rgb("5b6770")
#let section(title) = [#v(0.28em)#text(fill: accent, weight: "bold", size: 10.2pt)[#title]#line(length: 100%, stroke: (paint: accent, thickness: 0.5pt))#v(0.18em)]
#let item(body) = [#pad(left: 0.35em)[• #body]#v(0.1em)]
'''

ATS_TYP = TYPOGRAPHY + r'''
#align(center)[#text(size: 18pt, weight: "bold")[马浩宣]]
#align(center)[#text(fill: muted)[AI研发产品线 / AI产品助理 / 数据与需求分析方向]]
#align(center)[电话：13310838384 ｜ 邮箱：yishuziyu\@foxmail.com ｜ 个人网站：yishuziyu.cn ｜ GitHub：github.com/yishu-ziyu]

#section("求职定位")
#item[经济学训练 + AI Agent / AIGC 研究 + 数据分析与组织推进经历，目标匹配研发类产品线中“需求调研、AI能力跟踪、竞品分析、数据反馈、跨团队交付推进”的初级产品岗位。]
#item[优势不是已有完整 SaaS 产品负责人经历，而是能够把业务问题、用户反馈、研究材料和数据证据整理成可讨论、可迭代的产品文档与分析结论。]

#section("教育经历")
#item[华侨大学｜经济学本科，汉语言文学辅修｜2022.09 - 2026.06]
#item[总绩点排名专业前15%，近一年排名前5%；课程包含社会经济调研、经济博弈论、经济分析与预测等。]

#section("实习经历")
#item[#strong[深圳海坤投资管理有限公司｜行研分析师代理组长｜2026.01 - 至今]]
#item[跟踪 AI Agent、企业出海与产业应用场景，独立撰写《中国AI Agent投资机会分析报告》《科大讯飞出海研究及落地路径分析》。]
#item[围绕趋势判断、竞品格局、商业化路径与落地约束沉淀研究框架，可支持 AI 功能调研、竞品分析与路线图讨论。]
#item[参与投资团队实习生招聘，从 JD 制定、简历筛选、候选人跟进到结构化面试评估，训练需求拆解、沟通推进与流程管理能力。]
#item[#strong[招商银行泉州分行战略部｜实习生｜2026.02 - 2026.03]]
#item[参与存量客户财务更新、异常成本核算和国企项目财报交叉比对，从复杂材料中提取关键要素并支持业务判断。]

#section("AI / 产品化项目")
#item[#strong[AIGC 技术接受度调研]：基于技术接受模型研究 AIGC 采纳意愿，使用问卷数据与 SPSS PROCESS 进行模型分析，输出研究摘要、假设、数据分析和产品启示。]
#item[#strong[个人 AI 工具实践]：使用 AI IDE / vibe coding 搭建个人网站，并探索网页 markdown 插件、Mac 电池管理 APP 等小工具原型。]
#item[#strong[AI 产品岗位研究]：整理 AI Agent、LLM API、Prompt Engineering、需求分析、PRD 与 B 端产品能力要求，形成岗位技能分析材料。]

#section("组织与项目推进")
#item[华侨大学校辩论队 / 经济与金融学院辩论队｜队长｜2023.06 - 2025.06]
#item[统筹全校辩论联赛，协调11个参赛班级的赛程、评审标准、场地与评委资源；负责30位队员训练、战术拆解和复盘。]
#item[商务谈判竞赛全国总决赛一等奖：负责技术指标体系与博弈策略设计，推动团队形成可执行谈判方案。]

#section("技能关键词")
#item[产品与协作：需求调研、竞品分析、用户故事、PRD、路线图讨论、跨团队沟通、结构化表达。]
#item[AI 与数据：AI Agent、AIGC 用户研究、Prompt Engineering、Stata、SPSS、Excel、AI IDE / Vibe Coding。]
'''

SHOWCASE_TYP = TYPOGRAPHY + r'''
#set page(paper: "a4", margin: (x: 1.15cm, y: 1.05cm), fill: rgb("fbfcff"))
#let card(body) = box(width: 100%, inset: 7pt, radius: 5pt, fill: white, stroke: rgb("d9e3f0"))[#body]
#grid(columns: (2.2cm, 1fr), gutter: 0.8cm,
  image("assets/证件照.jpg", width: 2.1cm),
  [#text(size: 20pt, weight: "bold", fill: accent)[马浩宣]
   #v(0.15em)
   #text(fill: muted)[AI研发产品线 / AI产品助理 / 数据与需求分析方向]
   #v(0.25em)
   电话：13310838384 ｜ 邮箱：yishuziyu\@foxmail.com ｜ yishuziyu.cn ｜ github.com/yishu-ziyu]
)
#v(0.5em)
#card[
#text(weight: "bold", fill: accent)[JD匹配定位]
#v(0.15em)
经济学训练 + AI Agent / AIGC 研究 + 数据分析与组织推进经历。适合切入研发类产品线中的需求调研、AI能力跟踪、竞品分析、数据反馈与跨团队交付推进。
]
#v(0.45em)
#grid(columns: (1fr, 1fr), gutter: 0.55cm,
[
#section("核心证据")
#item[海坤：AI Agent 投资机会、科大讯飞出海研究，支持 AI 功能调研与竞品分析。]
#item[AIGC调研：问卷、模型假设、SPSS PROCESS，支撑用户洞察与数据分析。]
#item[招商银行战略部：财务更新、异常成本核算、合同要素提取，训练业务理解。]
#item[辩论队队长：推进赛事、协调资源、复盘训练，证明沟通与项目推进。]

#section("教育与技能")
#item[华侨大学｜经济学本科，汉语言文学辅修｜2022.09 - 2026.06]
#item[总绩点专业前15%，近一年前5%。]
#item[AI Agent、Prompt Engineering、AIGC用户研究、Stata、SPSS、Excel、AI IDE / Vibe Coding。]
],
[
#section("面向JD的改写重点")
#item[将“行研报告”转写为“AI技术跟踪 + 竞品/商业化调研 + 产品路线讨论素材”。]
#item[将“辩论队/招聘推进”转写为“跨角色沟通、用户故事式拆解、流程推进”。]
#item[将“AIGC调研/商业竞赛”转写为“用户反馈、核心数据、分析报告”。]
#item[保守处理 SaaS/PRD：写作“具备需求拆解和文档化基础”，不虚构正式 SaaS 产品实习。]

#section("代表经历")
#item[深圳海坤投资｜行研分析师代理组长｜2026.01 - 至今]
#item[招商银行泉州分行战略部｜实习生｜2026.02 - 2026.03]
#item[AIGC技术接受度调研｜问卷与模型分析]
#item[商务谈判竞赛全国总决赛一等奖；三创赛福建赛区省级二等奖。]
]
)
#v(0.4em)
#text(fill: muted, size: 7.7pt)[注：本版本为可信简历Demo，增强表述均应回溯到事实索引；涉及招聘转化人数、PRD深度、可到岗时间等需用户最终确认。]
'''


def extract_pdf_text(path: Path) -> str:
    doc = fitz.open(path)
    return '\n'.join(page.get_text('text') for page in doc)


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def render_pdf(typ_path: Path):
    subprocess.run(['typst', 'compile', str(typ_path), str(typ_path.with_suffix('.pdf'))], check=True)


def render_png(pdf_path: Path, png_path: Path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False)
    pix.save(str(png_path))


def pdf_stats(pdf_path: Path):
    doc = fitz.open(pdf_path)
    text = '\n'.join(page.get_text('text') for page in doc)
    images = sum(len(page.get_images(full=True)) for page in doc)
    return len(doc), images, len(text), text


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / 'assets').mkdir()
    if PHOTO.exists():
        shutil.copy2(PHOTO, OUT / 'assets' / '证件照.jpg')

    source_text = extract_pdf_text(SRC_RESUME)
    write(OUT / 'source_extracts' / '原始简历PDF文本.txt', source_text)
    write(OUT / '01_目标岗位JD_原文.md', '# 目标岗位JD_原文\n\n' + JD_TEXT + '\n')

    resume_yaml = '''candidate:\n  name: 马浩宣\n  target_role: AI研发产品线 / AI产品助理 / 数据与需求分析方向\n  phone: "13310838384"\n  email: yishuziyu@foxmail.com\n  website: yishuziyu.cn\n  github: https://github.com/yishu-ziyu\n  education:\n    school: 华侨大学\n    degree: 经济学本科\n    minor: 汉语言文学\n    period: 2022.09-2026.06\n  positioning: >\n    经济学训练 + AI Agent/AIGC研究 + 数据分析与组织推进经历，匹配研发类产品线中需求调研、AI能力跟踪、竞品分析、数据反馈和跨团队交付推进。\nsections:\n'''
    for sec, lines in RESUME_LINES:
        resume_yaml += f'  - title: {sec}\n    items:\n'
        for line in lines:
            resume_yaml += f'      - {line}\n'
    write(OUT / '02_结构化简历数据.yaml', resume_yaml)

    fact_md = '# 事实索引\n\n| ID | 事实 | 来源 | 风险等级 |\n|---|---|---|---|\n'
    for fid, fact, src, risk in FACTS:
        fact_md += f'| {fid} | {fact} | {src} | {risk} |\n'
    write(OUT / '03_事实索引.md', fact_md)

    jd_analysis = '''# JD岗位解析\n\n## 岗位类型\n研发类产品线 / AI产品助理 / ToB或内部平台产品方向。\n\n## 核心任务\n1. 版本迭代计划与产品路线图梳理。\n2. 深入业务一线做需求调研、需求整理、PRD和用户故事。\n3. 跟踪大模型、NLP、智能体等AI技术，结合业务场景做竞品分析和智能化功能设计。\n4. 跟踪核心数据、收集用户反馈、输出分析报告。\n5. 和业务、开发、测试团队协作，推动高质量交付。\n\n## 简历策略\n- 强化“AI Agent研究 + AIGC用户研究 + 数据分析报告 + 组织推进”组合。\n- 谨慎处理“PRD / SaaS / ToB产品经验”：只写可由材料支持的需求拆解、文档化、业务理解和产品化原型，不虚构正式产品实习。\n- ATS版优先覆盖关键词：AI Agent、大模型、NLP、需求调研、PRD、用户故事、竞品分析、数据分析、跨团队协作。\n'''
    write(OUT / '04_JD岗位解析.md', jd_analysis)

    matrix = '# JD匹配矩阵\n\n| JD要求 | 支撑事实 | 事实ID | 使用决策 |\n|---|---|---|---|\n'
    for row in MATCH_ROWS:
        matrix += f'| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n'
    write(OUT / '05_JD匹配矩阵.md', matrix)

    resume_md = '# 可信改写简历_草稿\n\n# 马浩宣\n\n电话：13310838384｜邮箱：yishuziyu@foxmail.com｜个人网站：yishuziyu.cn｜GitHub：github.com/yishu-ziyu\n\n## 求职定位\n经济学训练 + AI Agent / AIGC 研究 + 数据分析与组织推进经历，目标匹配研发类产品线中“需求调研、AI能力跟踪、竞品分析、数据反馈、跨团队交付推进”的初级产品岗位。\n\n'
    for sec, lines in RESUME_LINES:
        resume_md += f'## {sec}\n\n'
        for line in lines:
            resume_md += f'- {line}\n'
        resume_md += '\n'
    write(OUT / '06_可信改写简历_草稿.md', resume_md)

    truth = '''# 事实核查与用户确认清单\n\n## 可直接使用\n- 华侨大学经济学本科、汉语言文学辅修、2026.06毕业。\n- AI Agent、科大讯飞出海、AIGC技术接受度调研、招商银行战略部、辩论队队长、商务谈判竞赛、三创赛等经历。\n- Stata、SPSS、Excel、AI IDE/Vibe Coding、Prompt Engineering 等能力表述。\n\n## 需要用户确认\n1. 海坤招聘数字最终使用“30份/3名”还是桌面旧简历中的“28份/2名”。Demo中正文回避具体数字，事实索引中保留冲突说明。\n2. 是否真的有可对外展示的 PRD 或用户故事文档；若没有，最终版应写“需求拆解/文档化基础”，不要写“独立撰写完整PRD”。\n3. 是否有 ToB/SaaS 产品实习经历；当前材料不足，最终版不能写成已有 SaaS 产品实习。\n4. 是否接受保留照片版；ATS正式投递建议优先无照片版本。\n5. 可到岗时间、实习周期、每周出勤天数需要用户补充。\n\n## 禁止写入\n- 不写“熟练 SQL / Tableau / PowerBI”，除非用户补充证据。\n- 不写“负责正式产品路线图”或“主导研发交付”，只能写“参与/支持/形成路线图讨论素材”。\n- 不写“AI产品商业化落地带来收入增长”，除非有真实数据证明。\n'''
    write(OUT / '07_事实核查与用户确认清单.md', truth)

    write(OUT / '08_ATS投递版.typ', ATS_TYP)
    write(OUT / '09_展示阅读版.typ', SHOWCASE_TYP)

    render_pdf(OUT / '08_ATS投递版.typ')
    render_pdf(OUT / '09_展示阅读版.typ')
    render_png(OUT / '08_ATS投递版.pdf', OUT / '08_ATS投递版_预览图.png')
    render_png(OUT / '09_展示阅读版.pdf', OUT / '09_展示阅读版_预览图.png')

    ats_pages, ats_images, ats_chars, ats_text = pdf_stats(OUT / '08_ATS投递版.pdf')
    show_pages, show_images, show_chars, show_text = pdf_stats(OUT / '09_展示阅读版.pdf')
    report = f'''# 生成核查报告\n\n## 输出文件\n- ATS投递版：08_ATS投递版.pdf\n- 展示阅读版：09_展示阅读版.pdf\n- 预览图：08_ATS投递版_预览图.png；09_展示阅读版_预览图.png\n\n## PDF基础检查\n| 文件 | 页数 | 图片数 | 可抽取文本字符数 | 关键词检查 |\n|---|---:|---:|---:|---|\n| 08_ATS投递版.pdf | {ats_pages} | {ats_images} | {ats_chars} | {'通过' if all(k in ats_text for k in ['马浩宣','AI Agent','招商银行','AIGC']) else '需检查'} |\n| 09_展示阅读版.pdf | {show_pages} | {show_images} | {show_chars} | {'通过' if all(k in show_text for k in ['马浩宣','AI Agent','招商银行','AIGC']) else '需检查'} |\n\n## 当前Demo判断\n- 本次验证重点是“可信投递系统闭环”，不是最终视觉设计。\n- 已生成结构化数据、事实索引、JD解析、匹配矩阵、可信改写草稿、确认清单、两份Typst/PDF和预览图。\n- ATS版无照片，适合作为机器可读投递基线。\n- 展示版包含证件照，适合人工阅读预览。\n'''
    write(OUT / '10_生成核查报告.md', report)
    print(OUT)
    print(report)


if __name__ == '__main__':
    main()
