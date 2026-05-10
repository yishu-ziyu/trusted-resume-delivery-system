"""Generate ATS and showcase PDF resume versions from one Markdown source."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

import subprocess
import markdown


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read_markdown(path: Path) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def _extract_title(md: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "简历"


def _markdown_body_html(md: str) -> str:
    # Drop the first H1 because templates render the name explicitly.
    lines = md.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    content = "\n".join(lines).strip()
    return markdown.markdown(content, extensions=["tables", "fenced_code"])


def _contact_line(md: str) -> str:
    for line in md.splitlines()[:8]:
        if "邮箱" in line or "电话" in line or "yishuziyu" in line:
            return line.replace("**", "").strip()
    return "电话：13310838384｜邮箱：yishuziyu@foxmail.com｜个人网站：yishuziyu.cn"


def _write_pdf_from_html_file(html_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if not chrome.exists():
        raise FileNotFoundError("Google Chrome not found for headless PDF rendering")
    subprocess.run(
        [
            str(chrome),
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={output_path}",
            html_path.resolve().as_uri(),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return output_path


def _ats_html(md: str) -> str:
    name = _extract_title(md)
    contact = _contact_line(md)
    body = _markdown_body_html(md)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
@page {{ size: A4; margin: 14mm 15mm; }}
body {{ font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; color: #111827; font-size: 10.2px; line-height: 1.45; }}
h1 {{ margin: 0 0 3px; font-size: 24px; letter-spacing: 1px; color: #111827; }}
.contact {{ font-size: 9.5px; color: #374151; margin-bottom: 8px; padding-bottom: 7px; border-bottom: 1.4px solid #1f4e79; }}
h2 {{ font-size: 13px; color: #1f4e79; margin: 8px 0 4px; padding-bottom: 2px; border-bottom: 1px solid #d8dee9; }}
h3 {{ font-size: 11px; margin: 5px 0 2px; color: #111827; }}
p {{ margin: 3px 0; }}
ul {{ margin: 2px 0 4px 16px; padding: 0; }}
li {{ margin: 1.5px 0; }}
strong {{ color: #111827; }}
</style>
</head>
<body>
<h1>{name}</h1>
<div class="contact">{contact}</div>
{body}
</body>
</html>"""


def _showcase_html(md: str, portrait_path: Path) -> str:
    name = _extract_title(md)
    contact = _contact_line(md)
    body = _markdown_body_html(md)
    portrait_uri = Path(portrait_path).resolve().as_uri()
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; color: #1f2937; background: #f5f7fb; }}
.page {{ width: 210mm; min-height: 297mm; display: grid; grid-template-columns: 58mm 1fr; background: #fbfcff; }}
.sidebar {{ background: linear-gradient(180deg, #10233f, #18385f); color: #eef7ff; padding: 12mm 7mm; }}
.photo {{ width: 29mm; height: 38mm; object-fit: cover; border-radius: 10px; border: 2px solid rgba(255,255,255,.72); display: block; margin: 0 auto 6mm; box-shadow: 0 8px 18px rgba(0,0,0,.22); }}
.name {{ font-size: 25px; font-weight: 800; text-align: center; letter-spacing: 3px; margin: 0 0 2mm; }}
.role {{ text-align: center; color: #aee8ff; font-size: 10px; line-height: 1.5; border: 1px solid rgba(174,232,255,.45); border-radius: 999px; padding: 1.6mm 2mm; margin-bottom: 6mm; }}
.side-title {{ color: #7ee2ff; font-size: 12px; margin: 5mm 0 2mm; font-weight: 800; }}
.side-text {{ font-size: 9px; line-height: 1.65; color: #eef7ff; }}
.tag-cloud {{ display: flex; flex-wrap: wrap; gap: 1.4mm; margin-top: 1mm; }}
.tag {{ font-size: 8.5px; padding: 1mm 1.6mm; border-radius: 6px; background: rgba(255,255,255,.11); }}
.main {{ padding: 11mm 11mm 8mm 12mm; background-image: linear-gradient(rgba(31,78,121,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(31,78,121,.035) 1px, transparent 1px); background-size: 8mm 8mm; }}
.header-line {{ height: 4px; background: linear-gradient(90deg, #1f4e79, #00a6c8, #73d13d); border-radius: 999px; margin-bottom: 5mm; }}
.content {{ background: rgba(255,255,255,.72); border: 1px solid #dce7f2; border-radius: 14px; padding: 5mm 6mm; box-shadow: 0 10px 28px rgba(16,35,63,.08); }}
h1 {{ display: none; }}
h2 {{ font-size: 14px; color: #0d47a1; margin: 6mm 0 2.2mm; padding-bottom: 1.5mm; border-bottom: 1px solid #b9dbea; }}
h2:first-child {{ margin-top: 0; }}
h3 {{ font-size: 10.7px; margin: 3mm 0 1mm; color: #17233d; }}
p {{ margin: 2mm 0; font-size: 9.2px; line-height: 1.5; }}
ul {{ margin: 1mm 0 2mm 4mm; padding: 0; }}
li {{ font-size: 9.05px; line-height: 1.43; margin: .8mm 0; }}
strong {{ color: #0d47a1; }}
</style>
</head>
<body>
<div class="page">
  <aside class="sidebar">
    <img class="photo" src="{portrait_uri}" alt="portrait">
    <div class="name">{name}</div>
    <div class="role">AI 产品 / 经营分析 / 业务推动</div>
    <div class="side-title">联系方式</div>
    <div class="side-text">{contact}</div>
    <div class="side-title">关键词</div>
    <div class="tag-cloud">
      <span class="tag">AI Agent</span><span class="tag">经营分析</span><span class="tag">投研</span><span class="tag">产品化</span><span class="tag">数据分析</span><span class="tag">知识库</span>
    </div>
    <div class="side-title">版本定位</div>
    <div class="side-text">展示版：保留照片和视觉层级，适合内推、面试官和个人网站阅读。</div>
  </aside>
  <main class="main">
    <div class="header-line"></div>
    <div class="content">{body}</div>
  </main>
</div>
</body>
</html>"""


def _compact_ats_html() -> str:
    """Hand-compressed ATS HTML for the first one-page validation.

    This intentionally controls content before touching complex layout rules.
    The goal is to validate whether content compression is a cheaper path to a
    one-page resume than aggressive visual/template changes.
    """
    return """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
@page { size: A4; margin: 10mm 11mm; }
body { font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; color: #111827; font-size: 8.9px; line-height: 1.28; }
h1 { margin: 0 0 2px; font-size: 21px; letter-spacing: .8px; }
.contact { font-size: 8.6px; color: #374151; margin-bottom: 5px; padding-bottom: 5px; border-bottom: 1.2px solid #1f4e79; }
h2 { font-size: 11.5px; color: #1f4e79; margin: 5.2px 0 2.5px; padding-bottom: 1.5px; border-bottom: .8px solid #d8dee9; }
h3 { font-size: 9.4px; margin: 3px 0 1px; color: #111827; }
p { margin: 2px 0; }
ul { margin: 1px 0 2px 13px; padding: 0; }
li { margin: .8px 0; }
.row { display: flex; justify-content: space-between; gap: 8px; }
.date { color: #526071; white-space: nowrap; }
strong { color: #111827; }
</style>
</head>
<body>
<h1>马浩宣</h1>
<div class="contact">电话：13310838384｜邮箱：yishuziyu@foxmail.com｜个人网站：yishuziyu.cn｜华侨大学 经济学本科 / 汉语言文学辅修｜2026.06 毕业</div>

<h2>个人定位</h2>
<p>AI 产品 / 经营分析 / 业务推动方向。具备经济学训练、辩论队管理、投研与金融实习、AI Agent 工作流实践，擅长把复杂问题拆成结构化分析框架，并转化为产品、研究或业务动作。</p>

<h2>核心能力</h2>
<ul>
<li><strong>业务分析：</strong>从业务目标、约束条件、数据证据和利益相关方出发，搭建分析框架并输出行动建议。</li>
<li><strong>AI 产品化：</strong>使用 Agent、Markdown、自动化脚本、知识库和网页工具，将个人研究、投研、简历生成等需求转成可运行小产品。</li>
<li><strong>数据与研究：</strong>掌握 Stata、SPSS、Python 基础分析；具备经济学、产业研究、商业计划书和投资报告写作经验。</li>
<li><strong>沟通推动：</strong>长期辩论训练和团队管理经验，能够完成赛事统筹、成员训练、跨角色协调和复杂信息表达。</li>
</ul>

<h2>教育经历</h2>
<div class="row"><h3>华侨大学｜经济学 本科｜汉语言文学 辅修</h3><span class="date">2022.09 - 2026.06</span></div>
<ul>
<li>总绩点排名专业前 15%，近一年排名前 5%；社会经济调研 96、经济博弈论 94、经济分析与预测 95。</li>
<li>荣誉：校优秀学生、国家三级运动员、大学英语六级。</li>
</ul>

<h2>实习与组织经历</h2>
<div class="row"><h3>深圳海坤投资管理有限公司｜行研分析师代理组长</h3><span class="date">2026.01 - 至今</span></div>
<ul>
<li>独立撰写《中国 AI Agent 投资机会分析报告》《科大讯飞出海研究及落地路径分析》，围绕趋势、竞争格局、商业化路径和落地约束形成研究判断。</li>
<li>负责投资团队实习生招聘，从 JD 制定、简历筛选、候选人跟进到结构化面试评估，完成 28 份简历筛选与匹配，转化 2 名候选人入职。</li>
<li>将投研资料、持仓跟踪和行业信息沉淀为个人投资知识库，探索自动化脚本和 LLM Wiki 方法提升研究复用效率。</li>
</ul>

<div class="row"><h3>招商银行泉州分行战略部｜实习生</h3><span class="date">2026.02 - 2026.03</span></div>
<ul>
<li>辅助完成存量客户财务更新与异常成本核算；在国企项目中通过交叉比对财报，识别账面亏损主要来自大额折旧。</li>
<li>参与资产重组项目，从复杂业务合同中提取关键要素，并梳理基础股权结构图。</li>
</ul>

<div class="row"><h3>华侨大学校辩论队 / 经金学院辩论队｜队长</h3><span class="date">2023.06 - 2025.06</span></div>
<ul>
<li>统筹全校辩论联赛，负责赛制、评审标准、赛程推进、评委协调与现场流程控制，覆盖 11 个参赛班级。</li>
<li>负责校队 30 位成员日常运营与训练体系，组织模拟辩论、战术拆解、赛后复盘和对外赛事出征。</li>
</ul>

<h2>AI / 产品化实践</h2>
<ul>
<li><strong>个人网站与 Vibe Coding：</strong>搭建 yishuziyu.cn，并围绕真实需求开发网页 Markdown 插件、Mac 电池管理 App 等小工具。</li>
<li><strong>PDF 简历生成器：</strong>推进“JD → 定制简历 → PDF 输出”项目，探索 BDD/TDD、PDF 可编辑性诊断、模板克隆、ATS 排版和防编造事实守卫。</li>
<li><strong>学术与投研自动化：</strong>围绕机器人与劳动力市场进行论文精读；搭建投资知识库自动化系统，沉淀电网设备、物流、AI Agent 等方向素材。</li>
</ul>

<h2>数据分析与商业竞赛</h2>
<ul>
<li>2024 全国高校商业精英挑战赛商务谈判竞赛｜全国总决赛一等奖：担任技术顾问，研究矿渣及矿渣微粉技术指标，提出“打包置换”方案打破价格僵局。</li>
<li>2025 第十五届全国大学生电子商务“三创赛”福建赛区｜省级二等奖：负责商业计划书数据挖掘模块，通过历史交易数据和竞品周期修正销量假设。</li>
<li>2024 全国大学生英语翻译大赛｜大学英语组省级三等奖。</li>
</ul>

<h2>技能关键词</h2>
<p>AI Agent｜经营分析｜数据分析｜业务推动｜投研分析｜知识库｜Prompt Engineering｜Python｜Stata｜SPSS｜商业分析｜结构化表达｜跨团队协作</p>
</body>
</html>"""


def generate_compact_ats_version(resume_md: Path, output_dir: Path) -> Path:
    """Generate a one-page compact ATS PDF by controlling content first."""
    resume_md = Path(resume_md)
    if not resume_md.exists():
        raise FileNotFoundError(str(resume_md))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "mahaoxuan_ai_pm_resume_ats_compact_onepage.html"
    pdf_path = output_dir / "mahaoxuan_ai_pm_resume_ats_compact_onepage.pdf"
    html_path.write_text(_compact_ats_html(), encoding="utf-8")
    _write_pdf_from_html_file(html_path, pdf_path)
    return pdf_path


def _onepage_photo_html(portrait_path: Path) -> str:
    portrait_uri = Path(portrait_path).resolve().as_uri()
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; color: #111827; background: #ffffff; }}
.page {{ width: 210mm; height: 297mm; padding: 10mm 11mm; background: #fff; }}
.header {{ display: grid; grid-template-columns: 25mm 1fr; gap: 7mm; align-items: center; padding-bottom: 5mm; border-bottom: 1.3px solid #1f4e79; }}
.photo {{ width: 23mm; height: 30mm; object-fit: cover; border-radius: 6px; border: 1px solid #cbd5e1; }}
h1 {{ margin: 0 0 2mm; font-size: 22px; letter-spacing: 1.2px; }}
.role {{ color: #1f4e79; font-size: 10px; font-weight: 700; margin-bottom: 1.5mm; }}
.contact {{ font-size: 8.4px; color: #374151; line-height: 1.45; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; column-gap: 6mm; margin-top: 4mm; }}
h2 {{ font-size: 11.2px; color: #1f4e79; margin: 4.6px 0 2.2px; padding-bottom: 1.2px; border-bottom: .8px solid #d8dee9; }}
h3 {{ font-size: 9.1px; margin: 3px 0 1px; color: #111827; }}
p {{ font-size: 8.45px; line-height: 1.3; margin: 1.6px 0; }}
ul {{ margin: 1px 0 2px 12px; padding: 0; }}
li {{ font-size: 8.35px; line-height: 1.25; margin: .6px 0; }}
.full {{ grid-column: 1 / -1; }}
.row {{ display: flex; justify-content: space-between; gap: 6px; }}
.date {{ color: #526071; white-space: nowrap; font-size: 8px; }}
strong {{ color: #111827; }}
.footer {{ margin-top: 2mm; font-size: 7.8px; color: #64748b; }}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <img class="photo" src="{portrait_uri}" alt="portrait">
    <div>
      <h1>马浩宣</h1>
      <div class="role">AI 产品 / 经营分析 / 业务推动</div>
      <div class="contact">电话：13310838384｜邮箱：yishuziyu@foxmail.com｜个人网站：yishuziyu.cn<br>华侨大学｜经济学本科，汉语言文学辅修｜2026.06 毕业</div>
    </div>
  </div>

  <div class="grid">
    <section class="full">
      <h2>个人定位</h2>
      <p>经济学训练 + 辩论队管理 + 投研/经营分析实习 + AI Agent 工作流实践。擅长把复杂问题拆成结构化分析框架，并转化为产品、研究或业务动作。</p>
    </section>

    <section>
      <h2>核心能力</h2>
      <ul>
        <li><strong>业务分析：</strong>从业务目标、数据证据和利益相关方出发，输出行动建议。</li>
        <li><strong>AI 产品化：</strong>用 Agent、Markdown、自动化脚本和知识库，把真实需求转成可运行小产品。</li>
        <li><strong>数据研究：</strong>Stata、SPSS、Python 基础分析；具备投研报告和商业计划书写作经验。</li>
        <li><strong>沟通推动：</strong>长期辩论训练和团队管理，擅长结构化表达与跨角色协调。</li>
      </ul>
    </section>

    <section>
      <h2>教育经历</h2>
      <h3>华侨大学｜经济学 本科｜汉语言文学 辅修</h3>
      <p class="date">2022.09 - 2026.06</p>
      <ul>
        <li>总绩点专业前 15%，近一年排名前 5%。</li>
        <li>社会经济调研 96、经济博弈论 94、经济分析与预测 95。</li>
        <li>校优秀学生、国家三级运动员、大学英语六级。</li>
      </ul>
    </section>

    <section class="full">
      <h2>实习与组织经历</h2>
      <div class="row"><h3>深圳海坤投资管理有限公司｜行研分析师代理组长</h3><span class="date">2026.01 - 至今</span></div>
      <ul>
        <li>独立撰写《中国 AI Agent 投资机会分析报告》《科大讯飞出海研究及落地路径分析》，围绕产业趋势、竞争格局、商业化路径形成判断。</li>
        <li>负责投资团队实习生招聘，从 JD 制定、简历筛选到结构化面试评估，完成 28 份简历筛选与匹配，转化 2 名候选人入职。</li>
        <li>将投研资料、持仓跟踪和行业信息沉淀为投资知识库，探索自动化脚本和 LLM Wiki 方法提升研究复用效率。</li>
      </ul>
      <div class="row"><h3>招商银行泉州分行战略部｜实习生</h3><span class="date">2026.02 - 2026.03</span></div>
      <ul>
        <li>辅助完成存量客户财务更新与异常成本核算；通过交叉比对财报，识别账面亏损主要来自大额折旧。</li>
        <li>参与资产重组项目，从复杂业务合同中提取关键要素，并梳理基础股权结构图。</li>
      </ul>
      <div class="row"><h3>华侨大学校辩论队 / 经金学院辩论队｜队长</h3><span class="date">2023.06 - 2025.06</span></div>
      <ul>
        <li>统筹全校辩论联赛，负责赛制、评审标准、赛程推进和现场流程控制，覆盖 11 个参赛班级。</li>
        <li>负责校队 30 位成员日常运营与训练体系，组织模拟辩论、战术拆解、赛后复盘和对外赛事出征。</li>
      </ul>
    </section>

    <section>
      <h2>AI / 产品化实践</h2>
      <ul>
        <li><strong>个人网站：</strong>搭建 yishuziyu.cn，并开发网页 Markdown 插件、Mac 电池管理 App 等小工具。</li>
        <li><strong>PDF 简历生成器：</strong>推进“JD → 定制简历 → PDF 输出”项目，探索 BDD/TDD、模板克隆、ATS 排版和事实守卫。</li>
        <li><strong>研究自动化：</strong>围绕机器人与劳动力市场做论文精读，搭建投研知识库自动化系统。</li>
      </ul>
    </section>

    <section>
      <h2>竞赛与技能</h2>
      <ul>
        <li>2024 全国高校商业精英挑战赛商务谈判竞赛｜全国总决赛一等奖。</li>
        <li>2025 第十五届全国大学生电子商务“三创赛”福建赛区｜省级二等奖。</li>
        <li>2024 全国大学生英语翻译大赛｜省级三等奖。</li>
      </ul>
      <p><strong>关键词：</strong>AI Agent｜经营分析｜数据分析｜业务推动｜投研分析｜Prompt Engineering｜Python｜Stata｜SPSS｜结构化表达</p>
    </section>
  </div>
  <div class="footer">一页带照片克制版：面向国内投递、内推与邮件发送；内容以真实经历和项目素材为边界。</div>
</div>
</body>
</html>"""


def generate_onepage_photo_version(resume_md: Path, portrait_path: Path, output_dir: Path) -> Path:
    """Generate a one-page restrained resume version with portrait."""
    resume_md = Path(resume_md)
    portrait_path = Path(portrait_path)
    if not resume_md.exists():
        raise FileNotFoundError(str(resume_md))
    if not portrait_path.exists():
        raise FileNotFoundError(str(portrait_path))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "mahaoxuan_ai_pm_resume_onepage_with_photo.html"
    pdf_path = output_dir / "mahaoxuan_ai_pm_resume_onepage_with_photo.pdf"
    html_path.write_text(_onepage_photo_html(portrait_path), encoding="utf-8")
    _write_pdf_from_html_file(html_path, pdf_path)
    return pdf_path


def _onepage_photo_striped_html(portrait_path: Path) -> str:
    """Restrained one-page photo version with very subtle stripe texture."""
    html = _onepage_photo_html(portrait_path)
    html = html.replace(
        "body { margin: 0; font-family: \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", sans-serif; color: #111827; background: #ffffff; }",
        "body { margin: 0; font-family: \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", sans-serif; color: #111827; background: #f8fafc; }",
    )
    html = html.replace(
        ".page { width: 210mm; height: 297mm; padding: 10mm 11mm; background: #fff; }",
        ".page { width: 210mm; height: 297mm; padding: 10.5mm 11.5mm; background: repeating-linear-gradient(135deg, #ffffff 0, #ffffff 7px, #f4f8fc 7px, #f4f8fc 9px); }",
    )
    html = html.replace(
        ".header { display: grid; grid-template-columns: 25mm 1fr; gap: 7mm; align-items: center; padding-bottom: 5mm; border-bottom: 1.3px solid #1f4e79; }",
        ".header { display: grid; grid-template-columns: 25mm 1fr; gap: 7mm; align-items: center; padding-bottom: 5mm; border-bottom: 1.2px solid #2f5f8f; background: rgba(255,255,255,.72); }",
    )
    html = html.replace(
        "h2 { font-size: 11.2px; color: #1f4e79; margin: 4.6px 0 2.2px; padding-bottom: 1.2px; border-bottom: .8px solid #d8dee9; }",
        "h2 { font-size: 11.6px; color: #1f4e79; margin: 5.1px 0 2.6px; padding-bottom: 1.3px; border-bottom: .8px solid #d8dee9; }",
    )
    html = html.replace(
        "p { font-size: 8.45px; line-height: 1.3; margin: 1.6px 0; }",
        "p { font-size: 8.7px; line-height: 1.35; margin: 1.9px 0; }",
    )
    html = html.replace(
        "li { font-size: 8.35px; line-height: 1.25; margin: .6px 0; }",
        "li { font-size: 8.55px; line-height: 1.31; margin: .75px 0; }",
    )
    return html


def generate_onepage_photo_striped_version(resume_md: Path, portrait_path: Path, output_dir: Path) -> Path:
    """Generate v2: one-page restrained resume with portrait and subtle stripes."""
    resume_md = Path(resume_md)
    portrait_path = Path(portrait_path)
    if not resume_md.exists():
        raise FileNotFoundError(str(resume_md))
    if not portrait_path.exists():
        raise FileNotFoundError(str(portrait_path))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "mahaoxuan_ai_pm_resume_onepage_with_photo_striped_v2.html"
    pdf_path = output_dir / "mahaoxuan_ai_pm_resume_onepage_with_photo_striped_v2.pdf"
    html_path.write_text(_onepage_photo_striped_html(portrait_path), encoding="utf-8")
    _write_pdf_from_html_file(html_path, pdf_path)
    return pdf_path


def _onepage_photo_print_html(portrait_path: Path) -> str:
    """v3: lighter stripe texture and print-oriented micro-typography."""
    html = _onepage_photo_html(portrait_path)
    html = html.replace(
        "body { margin: 0; font-family: \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", sans-serif; color: #111827; background: #ffffff; }",
        "body { margin: 0; font-family: \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", sans-serif; color: #111827; background: #fbfdff; -webkit-print-color-adjust: exact; print-color-adjust: exact; }",
    )
    html = html.replace(
        ".page { width: 210mm; height: 297mm; padding: 10mm 11mm; background: #fff; }",
        ".page { width: 210mm; height: 297mm; padding: 9.6mm 10.6mm; background: #ffffff; position: relative; overflow: hidden; }\n.page::before { content: \"\"; position: absolute; right: -24mm; top: -18mm; width: 92mm; height: 58mm; background: repeating-linear-gradient(135deg, transparent 0, transparent 14px, rgba(37, 99, 235, 0.008) 14px, rgba(37, 99, 235, 0.008) 15px); pointer-events: none; }\n.page::after { content: \"\"; position: absolute; left: -28mm; bottom: -16mm; width: 98mm; height: 58mm; background: repeating-linear-gradient(135deg, transparent 0, transparent 14px, rgba(37, 99, 235, 0.008) 14px, rgba(37, 99, 235, 0.008) 15px); pointer-events: none; }\n.header, .grid, .footer { position: relative; z-index: 1; }",
    )
    html = html.replace(
        ".header { display: grid; grid-template-columns: 25mm 1fr; gap: 7mm; align-items: center; padding-bottom: 5mm; border-bottom: 1.3px solid #1f4e79; }",
        ".header { display: grid; grid-template-columns: 25mm 1fr; gap: 7mm; align-items: center; padding-bottom: 4.8mm; border-bottom: 1.05px solid #2f5f8f; background: rgba(255,255,255,.82); }",
    )
    html = html.replace(
        "h2 { font-size: 11.2px; color: #1f4e79; margin: 4.6px 0 2.2px; padding-bottom: 1.2px; border-bottom: .8px solid #d8dee9; }",
        "h2 { font-size: 11.7px; color: #1f4e79; margin: 4.9px 0 2.4px; padding-bottom: 1.2px; border-bottom: .75px solid #d8dee9; }",
    )
    html = html.replace(
        "h3 { font-size: 9.1px; margin: 3px 0 1px; color: #111827; }",
        "h3 { font-size: 9.35px; margin: 3px 0 1px; color: #111827; }",
    )
    html = html.replace(
        "p { font-size: 8.45px; line-height: 1.3; margin: 1.6px 0; }",
        "p { font-size: 8.9px; line-height: 1.38; margin: 1.85px 0; }",
    )
    html = html.replace(
        "li { font-size: 8.35px; line-height: 1.25; margin: .6px 0; }",
        "li { font-size: 8.65px; line-height: 1.32; margin: .66px 0; }",
    )
    html = html.replace(
        ".footer { margin-top: 2mm; font-size: 7.8px; color: #64748b; }",
        ".footer { margin-top: 2.2mm; font-size: 7.9px; color: #64748b; }",
    )
    html = html.replace(
        "一页带照片克制版：面向国内投递、内推与邮件发送；内容以真实经历和项目素材为边界。",
        "第1版 v3：更淡条纹 + 打印可读性优化；面向国内投递、内推与邮件发送。",
    )
    return html


def generate_onepage_photo_print_version(resume_md: Path, portrait_path: Path, output_dir: Path) -> Path:
    """Generate v3: one-page portrait resume with lighter stripes and print readability tweaks."""
    resume_md = Path(resume_md)
    portrait_path = Path(portrait_path)
    if not resume_md.exists():
        raise FileNotFoundError(str(resume_md))
    if not portrait_path.exists():
        raise FileNotFoundError(str(portrait_path))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "mahaoxuan_ai_pm_resume_onepage_with_photo_print_v3.html"
    pdf_path = output_dir / "mahaoxuan_ai_pm_resume_onepage_with_photo_print_v3.pdf"
    html_path.write_text(_onepage_photo_print_html(portrait_path), encoding="utf-8")
    _write_pdf_from_html_file(html_path, pdf_path)
    return pdf_path


def generate_resume_versions(resume_md: Path, portrait_path: Path, output_dir: Path) -> Dict[str, Path]:
    """Generate ATS and showcase PDF versions from one Markdown resume."""
    resume_md = Path(resume_md)
    portrait_path = Path(portrait_path)
    output_dir = Path(output_dir)
    if not portrait_path.exists():
        raise FileNotFoundError(str(portrait_path))

    md = _read_markdown(resume_md)
    output_dir.mkdir(parents=True, exist_ok=True)

    ats_html_path = output_dir / "mahaoxuan_ai_pm_resume_ats.html"
    showcase_html_path = output_dir / "mahaoxuan_ai_pm_resume_showcase_with_photo.html"
    ats_pdf = output_dir / "mahaoxuan_ai_pm_resume_ats.pdf"
    showcase_pdf = output_dir / "mahaoxuan_ai_pm_resume_showcase_with_photo.pdf"

    ats_html = _ats_html(md)
    showcase_html = _showcase_html(md, portrait_path)
    ats_html_path.write_text(ats_html, encoding="utf-8")
    showcase_html_path.write_text(showcase_html, encoding="utf-8")

    _write_pdf_from_html_file(ats_html_path, ats_pdf)
    _write_pdf_from_html_file(showcase_html_path, showcase_pdf)

    return {
        "ats_html": ats_html_path,
        "showcase_html": showcase_html_path,
        "ats_pdf": ats_pdf,
        "showcase_pdf": showcase_pdf,
    }


if __name__ == "__main__":
    portrait = PROJECT_ROOT / "output" / "assets" / "original_p1_img5.jpeg"
    if not portrait.exists():
        from core.photo_extractor import extract_portrait_candidate
        portrait = extract_portrait_candidate(
            Path("/Users/mahaoxuan/Desktop/马浩宣简历.pdf"),
            PROJECT_ROOT / "output" / "assets",
        ).path
    outputs = generate_resume_versions(
        PROJECT_ROOT / "output" / "mahaoxuan_ai_pm_resume.md",
        portrait,
        PROJECT_ROOT / "output" / "versions",
    )
    for key, value in outputs.items():
        print(f"{key}: {value}")
