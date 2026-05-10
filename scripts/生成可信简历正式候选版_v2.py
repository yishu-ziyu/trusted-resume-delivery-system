# -*- coding: utf-8 -*-
"""基于用户确认信息生成 AI研发产品线 正式投递带照片候选版 v2。"""
from pathlib import Path
import shutil, subprocess
import fitz

PROJECT = Path('/Users/mahaoxuan/Desktop/AI产品经理/项目D-简历PDF生成器')
OUT = PROJECT / 'output' / '正式候选版_带照片_AI研发产品线_v2'
CHINESE = OUT / '中文版本'
PHOTO = Path('/Users/mahaoxuan/Desktop/春招/00-个人材料/照片/证件照.jpg')
SRC_TEMPLATE = Path('/Users/mahaoxuan/Desktop/马浩宣简历.pdf')
SPRING_RESUME = Path('/Users/mahaoxuan/Desktop/春招/马浩宣简历.pdf')

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

FACTS = '''# 事实索引_v2_已吸收用户确认

## 用户本轮确认
- /Users/mahaoxuan/Desktop/马浩宣简历.pdf 是原始简历模板。
- AIGC 技术接受度调研报告由用户基本主导，用户身份是副负责人。
- 当前没有可对外展示的 PRD；后续可能会有，因此本版不写“已独立撰写完整PRD”。
- 当前没有 ToB / SaaS 产品实习经历，因此本版不写“ToB/SaaS产品实习”。
- 网页端 Markdown 插件和 Mac 电池管理 App 可展示、可公开仓库链接。
- 正式岗位投递需要带照片版本。

## 可公开项目链接
- 网页端 Markdown 插件：chrome-md-editor，https://github.com/yishu-ziyu/chrome-md-editor
- Mac 电池管理 App：battery-takeover，https://github.com/yishu-ziyu/battery-takeover

## 仍需谨慎
- 海坤招聘数字存在两个模板口径：桌面原始模板为 28份/2名；春招简历为 30份/3名。本版正文继续回避具体数字。
- PRD/用户故事只作为 JD 对齐能力方向写“需求拆解、文档化、原型/项目沉淀”，不写已产出正式 PRD。
- 不写 ToB/SaaS 产品实习，只写“对研发产品线、业务流程、AI工具化场景有理解”。
'''

MATCH = '''# JD匹配矩阵_v2

| JD要求 | 本版使用的真实支撑 | 改写策略 |
|---|---|---|
| 版本迭代计划 / 路线图 | AI Agent 投资机会报告、科大讯飞出海研究、个人工具项目 | 写“支持路线图讨论的调研材料”，不写正式负责人 |
| 需求调研 / PRD / 用户故事 | AIGC调研、AI产品岗位技能分析、Markdown插件和电池管理App | 写“需求拆解、用户反馈整理、文档化基础”，不写已展示PRD |
| AI技术跟踪 | AI Agent、大模型、AIGC采纳、Prompt/Agent岗位技能整理 | 强化为核心定位 |
| 数据跟踪 / 分析报告 | 招行战略部、AIGC调研、商业竞赛数据分析 | 强化“数据—结论—报告”能力 |
| 沟通协作 / 推进落地 | 辩论队队长、海坤招聘流程、商务谈判竞赛 | 强化跨角色沟通和事项推进 |
| ToB/SaaS经验 | 无正式实习 | 明确不写，只写业务理解和工具型产品探索 |
'''

TRUTH = '''# 事实核查与确认状态_v2

## 已由用户确认
- AIGC 调研：用户基本主导，且为副负责人。
- 没有可展示 PRD：本版不写“独立撰写完整PRD”。
- 没有 ToB/SaaS 产品实习：本版不写该经历。
- Markdown 插件和 Mac 电池管理 App 可公开展示仓库链接。
- 正式投递需要带照片版本。

## 本版已规避
- 海坤招聘数字冲突：正文不写具体 28/2 或 30/3。
- SaaS/ToB 实习：不写。
- 正式 PRD：不写。
- SQL/Tableau/PowerBI：不写。

## 后续可补充
- 如果后续产出 PRD，可将“需求拆解与文档化基础”升级为“PRD/用户故事作品”。
- 如果确认海坤招聘数字，可加入一条量化成果。
'''

TYP = r'''#set document(title: "马浩宣_AI研发产品线_正式投递带照片版_v2")
#set page(paper: "a4", margin: (x: 1.05cm, y: 0.95cm), fill: rgb("fbfcff"))
#set text(font: ("PingFang SC", "Arial"), size: 8.45pt, lang: "zh")
#set par(justify: false, leading: 0.36em)
#let navy = rgb("173b63")
#let blue = rgb("2563a8")
#let muted = rgb("596674")
#let rule_color = rgb("d7e3f1")
#let section(t) = [#v(0.25em)#text(fill: blue, weight: "bold", size: 9.7pt)[#t]#line(length: 100%, stroke: (paint: rule_color, thickness: 0.45pt))#v(0.16em)]
#let bullet(x) = [#pad(left: 0.18em)[• #x]#v(0.08em)]
#let small(x) = text(size: 7.6pt, fill: muted)[#x]

#grid(columns: (4.2cm, 1fr), gutter: 0.72cm,
[
  #rect(width: 100%, height: 27.6cm, fill: rgb("eef5fc"), radius: 6pt, inset: 9pt)[
    #align(center)[#image("assets/证件照.jpg", width: 2.55cm)]
    #v(0.35em)
    #align(center)[#text(size: 16.5pt, weight: "bold", fill: navy)[马浩宣]]
    #align(center)[#text(size: 8.2pt, fill: muted)[AI研发产品线 / AI产品助理]]
    #v(0.45em)
    #text(weight: "bold", fill: navy)[基本信息]
    #line(length: 100%, stroke: (paint: rule_color, thickness: 0.45pt))
    #small[电话：13310838384]
    #small[邮箱：yishuziyu\@foxmail.com]
    #small[网站：yishuziyu.cn]
    #small[GitHub：github.com/yishu-ziyu]
    #v(0.55em)
    #text(weight: "bold", fill: navy)[核心关键词]
    #line(length: 100%, stroke: (paint: rule_color, thickness: 0.45pt))
    #small[AI Agent / AIGC]
    #small[Prompt Engineering]
    #small[需求拆解 / 用户调研]
    #small[竞品分析 / 技术跟踪]
    #small[数据分析 / 反馈整理]
    #small[跨团队沟通 / 推进]
    #v(0.55em)
    #text(weight: "bold", fill: navy)[工具与方法]
    #line(length: 100%, stroke: (paint: rule_color, thickness: 0.45pt))
    #small[Stata / SPSS / Excel]
    #small[AI IDE / Vibe Coding]
    #small[问卷研究 / PROCESS]
    #small[行业研究 / 结构化写作]
    #v(0.55em)
    #text(weight: "bold", fill: navy)[公开项目]
    #line(length: 100%, stroke: (paint: rule_color, thickness: 0.45pt))
    #small[chrome-md-editor]
    #small[github.com/yishu-ziyu/chrome-md-editor]
    #v(0.1em)
    #small[battery-takeover]
    #small[github.com/yishu-ziyu/battery-takeover]
    #v(0.55em)
    #text(weight: "bold", fill: navy)[教育]
    #line(length: 100%, stroke: (paint: rule_color, thickness: 0.45pt))
    #small[华侨大学｜经济学本科]
    #small[汉语言文学辅修]
    #small[2022.09 - 2026.06]
    #small[专业前15%，近一年前5%]
  ]
],
[
  #text(size: 13.2pt, weight: "bold", fill: navy)[面向 AI 研发产品线的可信投递简历]
  #v(0.18em)
  #text(fill: muted)[经济学训练 + AI Agent/AIGC研究 + 数据分析 + 可公开AI工具项目。当前无正式 ToB/SaaS 产品实习、无可展示PRD，因此本版以“需求拆解、调研分析、文档化基础、工具原型与协作推进”做保守匹配。]

  #section("求职定位")
  #bullet[匹配研发类产品线中“业务调研、AI技术跟踪、竞品分析、用户反馈整理、数据分析、跨团队交付推进”的初级产品岗位。]
  #bullet[能将复杂材料拆解为结构化结论：从行业/技术资料、问卷数据、业务材料中提炼问题、约束、机会和后续迭代建议。]

  #section("实习经历")
  #text(weight: "bold")[深圳海坤投资管理有限公司｜行研分析师代理组长] #h(1fr) #text(fill: muted)[2026.01 - 至今]
  #bullet[跟踪 AI Agent、企业出海与产业应用场景，独立撰写《中国AI Agent投资机会分析报告》《科大讯飞出海研究及落地路径分析》。]
  #bullet[围绕趋势判断、竞品格局、商业化路径与落地约束沉淀研究框架，可为 AI 功能规划、竞品分析和路线图讨论提供输入。]
  #bullet[参与投资团队实习生招聘流程，从 JD 制定、简历筛选、候选人跟进到结构化面试评估，训练需求拆解、沟通推进和流程管理能力。]
  #v(0.16em)
  #text(weight: "bold")[招商银行泉州分行战略部｜实习生] #h(1fr) #text(fill: muted)[2026.02 - 2026.03]
  #bullet[参与存量客户财务更新、异常成本核算、国企项目财报交叉比对，从复杂材料中提取关键要素并支持业务判断。]
  #bullet[参与资产重组相关项目，负责合同要素提取与基础股权结构梳理，形成“业务材料—结构化信息—判断依据”的工作习惯。]

  #section("AI / 产品化项目")
  #text(weight: "bold")[AIGC技术接受度调研｜副负责人 / 基本主导]
  #bullet[围绕 AIGC 采纳意愿、自我控制、比较焦虑、感知有用性构建研究问题，组织问卷与模型分析，并使用 SPSS PROCESS 输出研究结论。]
  #bullet[将调研结论转化为产品/教育场景启示，体现用户视角、反馈分析和数据支撑能力。]
  #v(0.12em)
  #text(weight: "bold")[个人AI工具实践｜可公开展示]
  #bullet[网页端 Markdown 插件 chrome-md-editor：面向网页编辑与文本处理场景，沉淀个人效率工具。]
  #bullet[Mac 电池管理 App battery-takeover：围绕电池监控、阈值控充、日报复盘和 Dashboard 做工具型产品探索。]

  #section("组织与项目推进")
  #text(weight: "bold")[华侨大学校辩论队 / 经济与金融学院辩论队｜队长] #h(1fr) #text(fill: muted)[2023.06 - 2025.06]
  #bullet[统筹全校辩论联赛，协调11个参赛班级的赛程、评审标准、场地与评委资源；负责30位队员训练、战术拆解和复盘。]
  #bullet[长期训练观点拆解、证据组织、冲突沟通和团队协作能力，可迁移到产品需求澄清与跨角色推进。]
  #v(0.12em)
  #text(weight: "bold")[商业竞赛与数据分析]
  #bullet[商务谈判竞赛全国总决赛一等奖：负责技术指标体系、协议区间与价格博弈策略设计。]
  #bullet[三创赛福建赛区省级二等奖：负责商业计划书数据挖掘模块，基于行业交易数据与竞品生命周期修正销量假设。]

  #section("能力边界说明")
  #bullet[已具备 AI 工具使用、调研分析、需求拆解和文档化基础；目前没有可公开展示的完整 PRD，因此不夸大为“独立负责PRD”。]
  #bullet[没有 ToB/SaaS 产品实习经历；本版以业务理解、数据分析、工具原型和协作推进能力对齐岗位。]
]
)
'''


def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8')

def render(pdf_typ: Path):
    subprocess.run(['typst','compile',str(pdf_typ),str(pdf_typ.with_suffix('.pdf'))], check=True)

def preview(pdf: Path, png: Path):
    doc=fitz.open(pdf); pix=doc[0].get_pixmap(matrix=fitz.Matrix(1.8,1.8), alpha=False); pix.save(str(png))

def stats(pdf: Path):
    doc=fitz.open(pdf)
    text='\n'.join(p.get_text('text') for p in doc)
    imgs=sum(len(p.get_images(full=True)) for p in doc)
    return len(doc), imgs, len(text), text

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT/'assets').mkdir(parents=True)
    CHINESE.mkdir(parents=True)
    shutil.copy2(PHOTO, OUT/'assets'/'证件照.jpg')
    write(OUT/'01_目标岗位JD_原文.md', '# 目标岗位JD_原文\n\n'+JD_TEXT+'\n')
    write(OUT/'02_事实索引_v2_已确认.md', FACTS)
    write(OUT/'03_JD匹配矩阵_v2.md', MATCH)
    write(OUT/'04_事实核查与确认状态_v2.md', TRUTH)
    write(OUT/'05_正式投递带照片版_v2.typ', TYP)
    render(OUT/'05_正式投递带照片版_v2.typ')
    preview(OUT/'05_正式投递带照片版_v2.pdf', OUT/'05_正式投递带照片版_v2_预览图.png')
    shutil.copy2(OUT/'05_正式投递带照片版_v2.pdf', CHINESE/'第1版_推荐优先看_AI研发产品线_正式投递带照片版_v2.pdf')
    shutil.copy2(OUT/'05_正式投递带照片版_v2_预览图.png', CHINESE/'第1版_预览图.png')
    pages, imgs, chars, text = stats(OUT/'05_正式投递带照片版_v2.pdf')
    keys=['马浩宣','AI Agent','AIGC','chrome-md-editor','battery-takeover','招商银行','海坤']
    report=f'''# 生成核查报告_v2\n\n## 主文件\n- {OUT/'05_正式投递带照片版_v2.pdf'}\n- {CHINESE/'第1版_推荐优先看_AI研发产品线_正式投递带照片版_v2.pdf'}\n\n## 技术指标（PyMuPDF口径）\n- 页数：{pages}\n- 图片数：{imgs}\n- 可抽取文本字符数：{chars}\n- 关键词检查：{', '.join(k for k in keys if k in text)}\n\n## 本版策略\n- 正式投递主线采用带照片版本。\n- 写入 AIGC 调研“副负责人 / 基本主导”。\n- 写入两个可公开项目仓库：chrome-md-editor 与 battery-takeover。\n- 明确能力边界：无可展示完整 PRD、无 ToB/SaaS 产品实习，因此不虚构。\n- 海坤招聘数字冲突尚未最终确认，正文回避具体数字。\n'''
    write(OUT/'06_生成核查报告_v2.md', report)
    write(CHINESE/'版本说明.md', f'''# 中文版本说明\n\n优先查看：第1版_推荐优先看_AI研发产品线_正式投递带照片版_v2.pdf\n\n这是吸收用户确认后的正式投递候选版：\n- 带照片；\n- 保守匹配 AI 研发产品线 JD；\n- 不写不存在的 PRD / ToB / SaaS 产品实习；\n- 写入 AIGC 调研副负责人、基本主导；\n- 写入两个可公开 GitHub 项目链接。\n\n技术指标见：../06_生成核查报告_v2.md\n''')
    print(report)

if __name__ == '__main__': main()
