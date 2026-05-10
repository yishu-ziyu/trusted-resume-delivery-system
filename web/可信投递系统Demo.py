#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可信投递系统 - 简易网页 Demo

目标：先把 JD 驱动可信投递闭环做成可打开、可点击、可验证的网页原型。
当前版本复用已经生成并验证过的 Route B 实验产物，不在页面里现场调用大模型。
"""

from pathlib import Path
from typing import Dict, Any
import json

import fitz
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_DIR = ROOT / "output" / "jd_experiment_route_b_consulting_ai_strategy"
PREVIEW_DIR = EXPERIMENT_DIR / "preview_png"
MATERIAL_DIR = Path("/Users/mahaoxuan/Desktop/春招")

app = FastAPI(
    title="可信投递系统 Demo",
    description="JD 驱动的可信简历生成系统最小网页 Demo",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMPLATES: Dict[str, Dict[str, str]] = {
    "formal_v2": {
        "name": "正式带照片版 v2",
        "scene": "当前 AI研发产品线正式投递主推版本",
        "risk": "已吸收用户确认：AIGC副负责人/基本主导；不虚构PRD、ToB/SaaS实习",
        "pdf": "formal_v2/正式投递带照片版_v2.pdf",
        "html": "formal_v2/正式投递带照片版_v2.html",
        "preview": "formal_v2/正式投递带照片版_v2_预览图.png",
    },
    "ats": {
        "name": "ATS 无照片版",
        "scene": "网申 / ATS 系统 / 机器解析优先",
        "risk": "视觉表达最弱，但最稳、最机器可读",
        "pdf": "resume_route_b_ats.pdf",
        "html": "resume_route_b_ats.html",
        "preview": "preview_png/resume_route_b_ats_p1.png",
    },
    "single": {
        "name": "单栏带照片正式版",
        "scene": "正式邮件 / 咨询、金融、研究岗投递",
        "risk": "旧Route B候选模板，保留用于模板对比",
        "pdf": "resume_route_b_showcase_single_column.pdf",
        "html": "resume_route_b_showcase_single_column.html",
        "preview": "preview_png/resume_route_b_showcase_single_column_p1.png",
    },
    "double": {
        "name": "双栏带照片展示版",
        "scene": "熟人内推 / 面试官直接阅读 / 展示型材料",
        "risk": "信息密度更高，字号偏小，适合人工阅读不适合 ATS",
        "pdf": "resume_route_b_showcase.pdf",
        "html": "resume_route_b_showcase.html",
        "preview": "preview_png/resume_route_b_showcase_p1.png",
    },
}

REPORT_FILES = {
    "JD 解析": "jd_analysis.md",
    "事实清单": "fact_inventory.md",
    "匹配矩阵": "match_matrix.md",
    "简历策略": "resume_strategy.md",
    "事实核查": "truthfulness_check.md",
    "用户确认清单": "user_confirmation_checklist.md",
    "验证报告": "verification_report.md",
}


def read_text(name: str, fallback: str = "") -> str:
    path = EXPERIMENT_DIR / name
    if not path.exists():
        return fallback
    return path.read_text(encoding="utf-8")


def pdf_stats(relative_name: str) -> Dict[str, Any]:
    path = EXPERIMENT_DIR / relative_name
    if not path.exists():
        return {"exists": False, "page_count": 0, "image_count": 0, "text_chars": 0}
    doc = fitz.open(path)
    text = "".join(page.get_text("text") for page in doc)
    image_count = sum(len(page.get_images(full=True)) for page in doc)
    return {
        "exists": True,
        "page_count": len(doc),
        "image_count": image_count,
        "text_chars": len(text),
        "has_name": "马浩宣" in text,
        "has_email": "yishuziyu@foxmail.com" in text,
        "has_haikun": "海坤" in text,
        "has_cmb": "招商银行" in text,
        "has_ai": "AI" in text or "Agent" in text,
    }


def safe_experiment_path(relative: str) -> Path:
    candidate = (EXPERIMENT_DIR / relative).resolve()
    base = EXPERIMENT_DIR.resolve()
    if not str(candidate).startswith(str(base)):
        raise HTTPException(status_code=400, detail="非法路径")
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return candidate


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    return HTML


@app.get("/api/demo-data")
async def demo_data() -> Dict[str, Any]:
    templates = []
    for key, item in TEMPLATES.items():
        templates.append({"id": key, **item, "stats": pdf_stats(item["pdf"])})

    reports = []
    for title, filename in REPORT_FILES.items():
        reports.append({"title": title, "filename": filename, "content": read_text(filename)})

    input_jd = read_text("input_jd.md")
    confirmation = read_text("user_confirmation_checklist.md")
    truth = read_text("truthfulness_check.md")

    return {
        "status": "ok",
        "experiment_dir": str(EXPERIMENT_DIR),
        "material_dir": str(MATERIAL_DIR),
        "input_jd": input_jd,
        "templates": templates,
        "reports": reports,
        "risk_items": extract_risk_items(confirmation, truth),
        "material_sources": [
            "春招/01-求职材料/简历/草稿版/简历.txt",
            "春招/马浩宣简历.pdf",
            "春招/01-求职材料/简历/最终版/华侨大学 马浩宣.pdf",
            "春招/01-求职材料/作品集/AIGC 技术接受度相关调研报告.pdf",
            "春招/01-求职材料/作品集/0418项目报告书 云端竞逐——大疆领航竞争格局与数据驱动洞察.pdf",
            "春招/00-个人材料/照片/证件照.jpg",
        ],
    }


def extract_risk_items(confirmation: str, truth: str):
    joined = confirmation + "\n" + truth
    defaults = [
        "海坤投资招聘筛选与入职数字存在口径差异，最终投递前需要确认。",
        "毕业时间存在 2026.06 / 2026.07 口径差异，最终投递前需要确认。",
        "PPT 输出、数据可视化、图表制作等表述需要确认具体贡献边界。",
        "到岗时间、每周出勤天数、可持续实习周期需要用户确认。",
        "SQL / Tableau / PowerBI / 商业化收入指标当前不写入确定事实。",
    ]
    hits = []
    for item in defaults:
        key = item.split("，")[0]
        if key[:4] in joined or len(hits) < 5:
            hits.append(item)
    return hits


@app.get("/asset/{relative_path:path}")
async def asset(relative_path: str):
    path = safe_experiment_path(relative_path)
    media_type = None
    if path.suffix.lower() == ".png":
        media_type = "image/png"
    elif path.suffix.lower() == ".pdf":
        media_type = "application/pdf"
    elif path.suffix.lower() == ".html":
        media_type = "text/html"
    return FileResponse(path, media_type=media_type, filename=path.name)


@app.get("/report/{filename}", response_class=PlainTextResponse)
async def report(filename: str) -> str:
    if filename not in REPORT_FILES.values():
        raise HTTPException(status_code=404, detail="报告不存在")
    return read_text(filename)


HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>可信投递系统 Demo</title>
  <style>
    :root {
      --bg:#f6f7f9; --panel:#ffffff; --text:#111827; --muted:#6b7280; --line:#e5e7eb;
      --blue:#1d4ed8; --blue-soft:#eff6ff; --green:#047857; --amber:#b45309; --red:#b91c1c;
      --shadow:0 12px 34px rgba(15,23,42,.08);
    }
    *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif}
    header{background:#0f172a;color:white;border-bottom:1px solid rgba(255,255,255,.08)}
    .wrap{max-width:1220px;margin:0 auto;padding:24px}.hero{display:grid;grid-template-columns:1.4fr .8fr;gap:28px;align-items:end}
    h1{font-size:30px;margin:0 0 8px;letter-spacing:-.03em}.sub{color:#cbd5e1;margin:0;max-width:760px}.badge{display:inline-flex;gap:8px;align-items:center;border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:6px 10px;color:#dbeafe;margin-bottom:14px;font-size:12px}
    .hero-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:16px}.hero-card b{display:block;font-size:13px;color:#dbeafe}.hero-card span{display:block;color:#cbd5e1;font-size:12px;margin-top:5px}
    main.wrap{display:grid;grid-template-columns:320px 1fr;gap:18px;align-items:start}.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow)}.panel.pad{padding:18px}
    .section-title{font-size:15px;margin:0 0 12px;display:flex;justify-content:space-between;align-items:center}.muted{color:var(--muted)}
    textarea{width:100%;min-height:190px;border:1px solid var(--line);border-radius:12px;padding:12px;background:#fbfdff;resize:vertical;color:#1f2937;font:12px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace}
    .source-list{display:grid;gap:8px;margin-top:10px}.source{font-size:12px;color:#374151;border:1px solid var(--line);border-radius:10px;padding:8px 10px;background:#fafafa;word-break:break-all}
    .tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}.tab{border:1px solid var(--line);background:#fff;border-radius:12px;padding:12px;text-align:left;cursor:pointer;transition:.16s}.tab:hover{border-color:#93c5fd}.tab.active{border-color:var(--blue);background:var(--blue-soft);box-shadow:0 0 0 2px rgba(29,78,216,.08)}.tab b{display:block}.tab small{display:block;color:var(--muted);margin-top:4px;line-height:1.35}
    .grid{display:grid;grid-template-columns:1fr 300px;gap:16px}.preview-box{background:#e5e7eb;border:1px solid var(--line);border-radius:14px;overflow:hidden;min-height:600px;display:flex;align-items:flex-start;justify-content:center}.preview-box img{max-width:100%;height:auto;display:block;background:white}.side{display:grid;gap:12px}.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.stat{border:1px solid var(--line);border-radius:12px;padding:10px;background:#fafafa}.stat .num{font-size:18px;font-weight:700}.stat .lab{font-size:12px;color:var(--muted)}
    .actions{display:grid;gap:8px}.btn{display:flex;align-items:center;justify-content:center;border-radius:10px;padding:10px 12px;text-decoration:none;border:1px solid var(--line);color:#111827;background:white;font-weight:650}.btn.primary{background:#111827;color:white;border-color:#111827}.btn:hover{filter:brightness(.98)}
    .risk{border-left:3px solid var(--amber);padding:9px 10px;background:#fffbeb;border-radius:8px;color:#4b3520;margin-bottom:8px}.ok{color:var(--green)}.warn{color:var(--amber)}.no{color:var(--red)}
    .reports{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.report{border:1px solid var(--line);border-radius:12px;background:#fff;padding:12px}.report h3{margin:0 0 8px;font-size:14px}.report pre{white-space:pre-wrap;max-height:150px;overflow:auto;background:#f9fafb;border-radius:8px;padding:10px;margin:0;font-size:12px;color:#374151}.report a{font-size:12px;color:var(--blue);text-decoration:none}
    .flow{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}.step{border:1px solid var(--line);border-radius:12px;padding:10px;background:#fafafa}.step b{display:block;font-size:13px}.step span{font-size:12px;color:var(--muted)}
    @media(max-width:980px){main.wrap,.hero,.grid{grid-template-columns:1fr}.preview-box{min-height:auto}.flow,.reports{grid-template-columns:1fr}.tabs{grid-template-columns:1fr}}
  </style>
</head>
<body>
<header><div class="wrap hero"><div><div class="badge">可信投递系统 · Route B 实验网页化</div><h1>JD 驱动的可信简历生成 Demo</h1><p class="sub">不是只生成漂亮 PDF，而是把“真实材料库 + JD 解析 + 事实匹配 + 多模板输出 + 核查确认”放到同一个可操作界面里。</p></div><div class="hero-card"><b>当前版本</b><span>已接入最新正式带照片版 v2，同时保留 ATS、单栏、双栏模板用于对比。下一步再接入实时生成接口。</span></div></div></header>
<main class="wrap">
  <aside class="panel pad">
    <h2 class="section-title">1. 输入 JD <span class="muted">可编辑演示</span></h2>
    <textarea id="jd"></textarea>
    <h2 class="section-title" style="margin-top:18px">2. 真实材料来源</h2>
    <div id="materialDir" class="muted" style="font-size:12px;word-break:break-all"></div>
    <div id="sources" class="source-list"></div>
  </aside>

  <section style="display:grid;gap:18px">
    <div class="panel pad">
      <h2 class="section-title">产品闭环</h2>
      <div class="flow">
        <div class="step"><b>材料库</b><span>只从真实材料取事实</span></div>
        <div class="step"><b>JD 解析</b><span>拆岗位要求和关键词</span></div>
        <div class="step"><b>事实匹配</b><span>每条表达有来源</span></div>
        <div class="step"><b>模板选择</b><span>正式v2 / ATS / 单栏 / 双栏</span></div>
        <div class="step"><b>核查确认</b><span>风险项交给用户确认</span></div>
      </div>
    </div>

    <div class="panel pad">
      <h2 class="section-title">3. 选择输出模板 <span class="muted" id="selectedScene"></span></h2>
      <div class="tabs" id="templateTabs"></div>
      <div class="grid">
        <div class="preview-box"><img id="preview" alt="简历预览图" /></div>
        <div class="side">
          <div class="panel pad" style="box-shadow:none"><h2 class="section-title">PDF 验证</h2><div class="stat-grid" id="stats"></div></div>
          <div class="panel pad" style="box-shadow:none"><h2 class="section-title">下载 / 查看</h2><div class="actions"><a class="btn primary" id="downloadPdf" target="_blank">打开 PDF</a><a class="btn" id="openHtml" target="_blank">打开 HTML</a><a class="btn" id="openPreview" target="_blank">打开预览图</a></div></div>
          <div class="panel pad" style="box-shadow:none"><h2 class="section-title">适用说明</h2><div id="templateNote" class="muted"></div></div>
        </div>
      </div>
    </div>

    <div class="panel pad">
      <h2 class="section-title">4. 事实核查与用户确认</h2>
      <div id="risks"></div>
    </div>

    <div class="panel pad">
      <h2 class="section-title">5. 报告入口 <span class="muted">点击可打开原始 Markdown</span></h2>
      <div class="reports" id="reports"></div>
    </div>
  </section>
</main>
<script>
let DATA=null; let selected='formal_v2';
const esc=s=>(s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function asset(p){return '/asset/'+encodeURI(p)}
function statClass(v){return v?'ok':'no'}
function render(){
  const t=DATA.templates.find(x=>x.id===selected) || DATA.templates[0];
  document.getElementById('selectedScene').textContent=t.scene;
  document.getElementById('preview').src=asset(t.preview);
  document.getElementById('downloadPdf').href=asset(t.pdf);
  document.getElementById('openHtml').href=asset(t.html);
  document.getElementById('openPreview').href=asset(t.preview);
  document.getElementById('templateNote').innerHTML='<b>'+esc(t.name)+'</b><br>'+esc(t.risk);
  const s=t.stats||{};
  document.getElementById('stats').innerHTML=`
    <div class="stat"><div class="num ${statClass(s.exists)}">${s.exists?'存在':'缺失'}</div><div class="lab">文件状态</div></div>
    <div class="stat"><div class="num">${s.page_count}</div><div class="lab">页数</div></div>
    <div class="stat"><div class="num">${s.image_count}</div><div class="lab">图片数</div></div>
    <div class="stat"><div class="num">${s.text_chars}</div><div class="lab">可提取文本字符</div></div>
    <div class="stat"><div class="num ${statClass(s.has_name)}">${s.has_name?'是':'否'}</div><div class="lab">包含姓名</div></div>
    <div class="stat"><div class="num ${statClass(s.has_email)}">${s.has_email?'是':'否'}</div><div class="lab">包含邮箱</div></div>`;
}
fetch('/api/demo-data').then(r=>r.json()).then(data=>{
  DATA=data; document.getElementById('jd').value=data.input_jd || '';
  document.getElementById('materialDir').textContent=data.material_dir;
  document.getElementById('sources').innerHTML=data.material_sources.map(x=>'<div class="source">'+esc(x)+'</div>').join('');
  document.getElementById('templateTabs').innerHTML=data.templates.map(t=>`<button class="tab ${t.id===selected?'active':''}" data-id="${t.id}"><b>${esc(t.name)}</b><small>${esc(t.scene)}</small></button>`).join('');
  document.querySelectorAll('.tab').forEach(btn=>btn.onclick=()=>{selected=btn.dataset.id;document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));btn.classList.add('active');render();});
  document.getElementById('risks').innerHTML=data.risk_items.map(x=>'<div class="risk">'+esc(x)+'</div>').join('');
  document.getElementById('reports').innerHTML=data.reports.map(r=>`<div class="report"><h3>${esc(r.title)}</h3><pre>${esc((r.content||'').slice(0,520))}${(r.content||'').length>520?'...':''}</pre><a href="/report/${encodeURIComponent(r.filename)}" target="_blank">打开 ${esc(r.filename)}</a></div>`).join('');
  render();
}).catch(e=>{document.body.innerHTML='<pre>Demo 数据加载失败：'+e.message+'</pre>'});
</script>
</body>
</html>'''


if __name__ == "__main__":
    print("=" * 72)
    print("可信投递系统 Demo")
    print("访问地址: http://127.0.0.1:8766")
    print("=" * 72)
    uvicorn.run(app, host="127.0.0.1", port=8766)
