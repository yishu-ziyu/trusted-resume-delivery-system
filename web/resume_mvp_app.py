# -*- coding: utf-8 -*-
"""
普通用户版简历生成网页 MVP。

目标：粘贴 JD、上传/粘贴材料、生成 Resume JSON、HTML 预览和真实 PDF 下载。
第一版使用可解释的本地启发式规则，不调用 LLM；所有事实通过 source_notes 标注来源。
"""

import html
import re
import subprocess
import textwrap
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "output" / "resume_mvp_runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="用户版简历生成 MVP",
    description="JD 驱动的可信简历生成本地网页 MVP",
    version="0.1.0",
)

MATERIAL_STORE: Dict[str, Dict[str, str]] = {}
RESUME_STORE: Dict[str, Dict[str, Any]] = {}


class JDRequest(BaseModel):
    jd_text: str = Field(..., min_length=1)


class MaterialUploadRequest(BaseModel):
    filename: str = Field(default="粘贴材料.txt")
    content: str = Field(..., min_length=1)
    content_type: str = Field(default="text/plain")


class GenerateResumeRequest(BaseModel):
    jd_text: str = Field(..., min_length=1)
    material_ids: List[str] = Field(default_factory=list)
    pasted_material: Optional[str] = None


KEYWORD_GROUPS = {
    "AI产品/Agent": ["AI", "Agent", "AIGC", "大模型", "LLM", "Prompt", "AI IDE"],
    "调研分析": ["调研", "研究", "访谈", "问卷", "竞品", "行业", "报告", "分析"],
    "项目推进": ["项目", "推进", "协作", "管理", "统筹", "落地", "原型"],
    "数据分析": ["数据", "Python", "Stata", "SPSS", "Excel", "可视化", "计量"],
    "商业/金融": ["投资", "金融", "战略", "咨询", "商业", "财报", "估值"],
}


HOME_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>用户版简历生成 MVP</title>
  <style>
    :root { --ink:#111827; --muted:#6b7280; --line:#d8dee8; --blue:#1d4ed8; --bg:#f7f8fb; }
    * { box-sizing: border-box; }
    body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",Arial,sans-serif; color:var(--ink); background:var(--bg); }
    header { background:#fff; border-bottom:1px solid var(--line); padding:24px 32px; }
    h1 { margin:0 0 8px; font-size:26px; }
    p { line-height:1.65; }
    main { max-width:1180px; margin:24px auto 48px; padding:0 20px; }
    .grid { display:grid; grid-template-columns:1fr 1fr; gap:18px; align-items:start; }
    .card { background:#fff; border:1px solid var(--line); border-radius:14px; padding:18px; }
    label { display:block; font-weight:700; margin-bottom:8px; }
    textarea { width:100%; min-height:260px; resize:vertical; border:1px solid var(--line); border-radius:10px; padding:12px; font:14px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace; }
    input[type=file] { width:100%; padding:10px; border:1px dashed var(--line); border-radius:10px; background:#fafafa; }
    button { border:0; background:var(--blue); color:#fff; border-radius:10px; padding:11px 16px; font-weight:700; cursor:pointer; }
    button.secondary { background:#374151; }
    button:disabled { opacity:.55; cursor:not-allowed; }
    .muted { color:var(--muted); font-size:13px; }
    .actions { margin-top:14px; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
    .status { margin-top:14px; padding:10px 12px; border-radius:10px; background:#eef2ff; color:#1e3a8a; white-space:pre-wrap; }
    .result { margin-top:18px; display:none; }
    .preview-shell { margin-top:18px; display:grid; grid-template-columns:360px 1fr; gap:18px; align-items:start; }
    .preview-panel { background:#e5e7eb; border:1px solid var(--line); border-radius:14px; padding:18px; min-height:720px; display:flex; justify-content:center; align-items:flex-start; }
    .resume-preview { width:100%; max-width:760px; min-height:680px; border:1px solid #cfd6e2; border-radius:6px; background:#fff; padding:28px; box-shadow:0 16px 38px rgba(15,23,42,.12); }
    .placeholder { color:var(--muted); text-align:center; margin-top:260px; line-height:1.8; }
    .notes { margin:0; padding-left:20px; }
    .two { display:grid; grid-template-columns:1fr; gap:14px; }
    @media (max-width: 860px) { .grid,.two { grid-template-columns:1fr; } }
  </style>
</head>
<body>
<header>
  <h1>JD 驱动的可信简历生成 MVP</h1>
  <p class="muted">本地可访问版本：粘贴岗位 JD、上传 txt/Markdown 材料，生成 Resume JSON、来源说明、简历预览和可下载 PDF。当前版本使用本地启发式规则，不虚构无来源事实。</p>
</header>
<main>
  <section class="grid">
    <div class="card">
      <label for="jd">1. 粘贴目标岗位 JD</label>
      <textarea id="jd">AI产品实习生：负责AI Agent产品调研、用户需求分析、竞品分析、原型协作、项目推进，要求能输出结构化报告。</textarea>
    </div>
    <div class="card">
      <label for="materialText">2. 上传或粘贴个人材料</label>
      <input id="file" type="file" accept=".txt,.md,.markdown" />
      <p class="muted">当前优先支持 txt / Markdown。文件会在浏览器本地读取成文本后提交给后端 JSON 接口，不依赖 multipart。</p>
      <textarea id="materialText">马浩宣｜华侨大学经济学本科｜yishuziyu@foxmail.com｜13310838384
经历：深圳海坤投资管理有限公司，参与AI Agent投资机会研究与行业研究报告。
项目：AIGC技术接受度调研，负责问卷设计、访谈整理、数据分析与报告撰写。
项目：chrome-md-editor Markdown网页插件；battery-takeover Mac电池管理App。
技能：Python、Stata、SPSS、Excel、Prompt Engineering、AI IDE。</textarea>
      <div class="actions">
        <button id="generate">生成适配简历</button>
        <button id="download" class="secondary" disabled>下载 PDF</button>
      </div>
      <div id="status" class="status">等待输入。</div>
    </div>
  </section>

  <section class="preview-shell">
    <div id="result" class="result card">
      <h2>生成结果</h2>
      <div class="two">
        <div>
          <h3>匹配说明</h3>
          <p id="summary"></p>
          <pre id="json" style="white-space:pre-wrap;background:#f9fafb;border:1px solid var(--line);border-radius:10px;padding:12px;max-height:360px;overflow:auto;"></pre>
        </div>
        <div>
          <h3>source_notes / 来源说明</h3>
          <ul id="notes" class="notes"></ul>
        </div>
      </div>
    </div>
    <div class="card">
      <h2>简历预览</h2>
      <p class="muted">这里始终保留 A4 预览区。生成前显示占位说明，生成后显示真实简历 HTML，下载 PDF 与此预览使用同一份 Resume JSON。</p>
      <div class="preview-panel">
        <div id="preview" class="resume-preview"><div class="placeholder">等待生成简历预览<br>粘贴 JD 和个人材料后点击“生成适配简历”</div></div>
      </div>
    </div>
  </section>
</main>
<script>
const fileInput = document.getElementById('file');
const materialText = document.getElementById('materialText');
const jd = document.getElementById('jd');
const statusEl = document.getElementById('status');
const generateBtn = document.getElementById('generate');
const downloadBtn = document.getElementById('download');
const result = document.getElementById('result');
let currentResumeId = null;

fileInput.addEventListener('change', async () => {
  const file = fileInput.files[0];
  if (!file) return;
  if (!/[.](txt|md|markdown)$/i.test(file.name)) {
    statusEl.textContent = '当前 MVP 仅支持 txt / md / markdown。';
    return;
  }
  materialText.value = await file.text();
  statusEl.textContent = `已读取文件：${file.name}`;
});

generateBtn.addEventListener('click', async () => {
  try {
    generateBtn.disabled = true;
    statusEl.textContent = '正在上传材料...';
    const filename = fileInput.files[0]?.name || '粘贴材料.md';
    const upload = await fetch('/api/upload-materials', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({filename, content: materialText.value, content_type:'text/markdown'})
    }).then(r => r.json());
    statusEl.textContent = '正在分析 JD 并生成 Resume JSON...';
    const gen = await fetch('/api/generate-resume', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({jd_text: jd.value, material_ids:[upload.material_id]})
    }).then(r => r.json());
    currentResumeId = gen.resume_id;
    const preview = await fetch(`/api/preview?resume_id=${encodeURIComponent(currentResumeId)}`).then(r => r.text());
    document.getElementById('preview').innerHTML = preview;
    document.getElementById('summary').textContent = `${gen.resume_json.jd_summary}｜${gen.resume_json.candidate_summary}｜匹配分：${gen.resume_json.match_score}`;
    document.getElementById('json').textContent = JSON.stringify(gen.resume_json, null, 2);
    const notes = document.getElementById('notes');
    notes.innerHTML = '';
    gen.resume_json.source_notes.forEach(n => {
      const li = document.createElement('li');
      li.textContent = `${n.claim} — ${n.source}（${n.confidence}）`;
      notes.appendChild(li);
    });
    result.style.display = 'block';
    downloadBtn.disabled = false;
    statusEl.textContent = '已生成，可预览并下载 PDF。';
  } catch (err) {
    statusEl.textContent = '生成失败：' + err;
  } finally {
    generateBtn.disabled = false;
  }
});

downloadBtn.addEventListener('click', () => {
  if (!currentResumeId) return;
  window.location.href = `/api/download-pdf?resume_id=${encodeURIComponent(currentResumeId)}`;
});
</script>
</body>
</html>
"""


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _keyword_hits(text: str) -> List[str]:
    hits: List[str] = []
    for group, words in KEYWORD_GROUPS.items():
        if any(word.lower() in text.lower() for word in words):
            hits.append(group)
    return hits


def analyze_jd_text(jd_text: str) -> Dict[str, Any]:
    text = _clean_text(jd_text)
    hits = _keyword_hits(text)
    if "产品" in text and ("AI" in text or "Agent" in text or "AIGC" in text):
        target_role = "AI产品相关岗位"
    elif "咨询" in text or "战略" in text:
        target_role = "咨询/战略分析相关岗位"
    elif "数据" in text:
        target_role = "数据分析相关岗位"
    else:
        target_role = "目标岗位"
    summary = "、".join(hits[:4]) if hits else text[:80]
    return {"target_role": target_role, "jd_summary": f"岗位重点：{summary}", "keywords": hits}


def _extract_contact(material_text: str) -> Dict[str, Any]:
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", material_text)
    phone_match = re.search(r"(?<!\d)(1[3-9]\d{9})(?!\d)", material_text)
    name = ""
    for candidate in ["马浩宣"]:
        if candidate in material_text:
            name = candidate
            break
    if not name:
        first_line = material_text.strip().splitlines()[0] if material_text.strip() else "候选人"
        name = re.split(r"[｜|,，\s]", first_line)[0][:12] or "候选人"
    return {
        "name": name,
        "contact": {
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(1) if phone_match else "",
        },
    }


def _find_lines(material_text: str, words: List[str], limit: int) -> List[str]:
    lines = []
    seen = set()
    for raw in material_text.splitlines():
        line = raw.strip(" -\t")
        if not line:
            continue
        if any(w.lower() in line.lower() for w in words) and line not in seen:
            lines.append(line)
            seen.add(line)
        if len(lines) >= limit:
            break
    return lines


def _dedupe_lines(lines: List[str]) -> List[str]:
    result = []
    seen = set()
    for line in lines:
        if line and line not in seen:
            result.append(line)
            seen.add(line)
    return result


def _build_resume_json(jd_text: str, materials: List[Dict[str, str]]) -> Dict[str, Any]:
    jd_info = analyze_jd_text(jd_text)
    material_text = "\n".join(m["content"] for m in materials)
    contact = _extract_contact(material_text)
    material_hits = _keyword_hits(material_text)
    jd_hits = jd_info["keywords"]
    overlap = [x for x in jd_hits if x in material_hits]
    score = min(95, 45 + len(overlap) * 12 + min(len(material_text) // 180, 18))

    education_lines = _find_lines(material_text, ["大学", "本科", "硕士", "专业", "毕业"], 2)
    experience_lines = _find_lines(material_text, ["经历", "实习", "公司", "银行", "投资", "岗位"], 4)
    project_lines = [
        line for line in _find_lines(material_text, ["项目", "调研", "报告", "Agent", "AIGC", "插件", "App"], 8)
        if line not in experience_lines
    ][:5]
    skill_lines = _find_lines(material_text, ["技能", "Python", "Stata", "SPSS", "Excel", "Prompt"], 3)

    filename = materials[0]["filename"] if materials else "粘贴材料"
    source_notes = [
        {"claim": f"姓名：{contact['name']}", "source": f"上传材料：{filename}", "confidence": "high"},
        {"claim": jd_info["jd_summary"], "source": "用户粘贴 JD", "confidence": "high"},
    ]
    for line in _dedupe_lines(education_lines + experience_lines + project_lines + skill_lines)[:8]:
        source_notes.append({"claim": line[:120], "source": f"上传材料：{filename}", "confidence": "medium"})

    return {
        "target_role": jd_info["target_role"],
        "jd_summary": jd_info["jd_summary"],
        "candidate_summary": "候选材料与岗位关键词的交集：" + ("、".join(overlap) if overlap else "暂未发现强交集，建议补充更具体材料"),
        "match_score": score,
        "resume": {
            "name": contact["name"],
            "contact": contact["contact"],
            "education": education_lines,
            "experiences": experience_lines,
            "projects": project_lines,
            "skills": skill_lines,
            "awards": _find_lines(material_text, ["奖", "一等奖", "二等奖", "三等奖", "竞赛"], 3),
        },
        "source_notes": source_notes,
    }


def _render_resume_html(resume_json: Dict[str, Any]) -> str:
    resume = resume_json["resume"]

    def section(title: str, items: List[str]) -> str:
        escaped_items = "".join(f"<li>{html.escape(item)}</li>" for item in items) or "<li>暂无可确认材料，建议补充来源。</li>"
        return f"<section><h3>{html.escape(title)}</h3><ul>{escaped_items}</ul></section>"

    notes = "".join(
        f"<li>{html.escape(n['claim'])}<br><small>来源：{html.escape(n['source'])}｜可信度：{html.escape(n['confidence'])}</small></li>"
        for n in resume_json["source_notes"]
    )
    return f"""
    <article class="resume-doc">
      <style>
        .resume-doc {{ font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',Arial,sans-serif; color:#111827; line-height:1.55; }}
        .resume-doc h2 {{ margin:0 0 6px; font-size:24px; }}
        .resume-doc .meta {{ color:#4b5563; border-bottom:1px solid #d8dee8; padding-bottom:10px; margin-bottom:12px; }}
        .resume-doc h3 {{ margin:14px 0 6px; font-size:15px; color:#1d4ed8; }}
        .resume-doc ul {{ margin:0; padding-left:18px; }}
        .resume-doc li {{ margin:4px 0; }}
        .resume-doc small {{ color:#6b7280; }}
      </style>
      <h2>{html.escape(resume['name'])}</h2>
      <div class="meta">{html.escape(resume['contact'].get('email',''))} ｜ {html.escape(resume['contact'].get('phone',''))} ｜ 目标：{html.escape(resume_json['target_role'])}</div>
      <p><strong>岗位匹配摘要：</strong>{html.escape(resume_json['candidate_summary'])}</p>
      {section('教育背景', resume['education'])}
      {section('经历', resume['experiences'])}
      {section('项目', resume['projects'])}
      {section('技能', resume['skills'])}
      {section('奖项/证书', resume['awards'])}
      <section><h3>来源说明</h3><ul>{notes}</ul></section>
    </article>
    """


def _write_pdf(resume_id: str, resume_json: Dict[str, Any]) -> Path:
    """Render PDF from HTML with Chrome so Chinese text is not garbled."""
    pdf_path = RUNTIME_DIR / f"{resume_id}.pdf"
    html_path = RUNTIME_DIR / f"{resume_id}.html"
    html_path.write_text(_render_pdf_document(resume_json), encoding="utf-8")

    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if chrome.exists():
        subprocess.run(
            [
                str(chrome),
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}",
                html_path.resolve().as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return pdf_path

    return _write_pdf_with_pymupdf_fallback(resume_id, resume_json)


def _render_pdf_document(resume_json: Dict[str, Any]) -> str:
    preview = _render_resume_html(resume_json)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <style>
    @page {{ size: A4; margin: 14mm; }}
    body {{ margin:0; background:#fff; }}
    .resume-doc {{ font-size:12px; }}
    .resume-doc h2 {{ font-size:22px !important; }}
    .resume-doc h3 {{ break-after:avoid; }}
    .resume-doc li {{ break-inside:avoid; }}
  </style>
</head>
<body>{preview}</body>
</html>"""


def _write_pdf_with_pymupdf_fallback(resume_id: str, resume_json: Dict[str, Any]) -> Path:
    """Last-resort fallback. On macOS this may not render CJK correctly; Chrome path is preferred."""
    pdf_path = RUNTIME_DIR / f"{resume_id}.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    margin = 48
    y = 48
    resume = resume_json["resume"]
    title = resume["name"] or "候选人"
    page.insert_text((margin, y), title, fontsize=20, fontname="helv", color=(0.05, 0.09, 0.16))
    y += 26
    meta = f"{resume['contact'].get('email','')}  {resume['contact'].get('phone','')}  目标：{resume_json['target_role']}"
    y = _insert_wrapped(page, meta, margin, y, 500, 9, color=(0.25, 0.30, 0.38)) + 8
    y = _insert_wrapped(page, "岗位匹配摘要：" + resume_json["candidate_summary"], margin, y, 500, 10) + 8
    for title, key in [("教育背景", "education"), ("经历", "experiences"), ("项目", "projects"), ("技能", "skills"), ("奖项/证书", "awards")]:
        y = _insert_wrapped(page, title, margin, y + 4, 500, 12, color=(0.11, 0.31, 0.85)) + 2
        items = resume.get(key) or ["暂无可确认材料，建议补充来源。"]
        for item in items[:5]:
            y = _insert_wrapped(page, "• " + item, margin + 8, y, 492, 9) + 2
            if y > 760:
                page = doc.new_page(width=595, height=842)
                y = 48
    y = _insert_wrapped(page, "来源说明", margin, y + 8, 500, 12, color=(0.11, 0.31, 0.85)) + 2
    for note in resume_json["source_notes"][:10]:
        text = f"• {note['claim']}｜来源：{note['source']}｜可信度：{note['confidence']}"
        y = _insert_wrapped(page, text, margin + 8, y, 492, 8, color=(0.25, 0.30, 0.38)) + 2
        if y > 780:
            break
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def _insert_wrapped(page: fitz.Page, text: str, x: float, y: float, width: float, fontsize: int, color=(0, 0, 0)) -> float:
    safe_text = _clean_text(text)
    approx_chars = max(18, int(width / max(fontsize * 0.55, 4)))
    lines = []
    for chunk in re.split(r"(?<=[。；;])", safe_text):
        chunk = chunk.strip()
        if not chunk:
            continue
        lines.extend(textwrap.wrap(chunk, width=approx_chars, break_long_words=False, replace_whitespace=False) or [chunk])
    for line in lines[:20]:
        page.insert_text((x, y), line, fontsize=fontsize, fontname="helv", color=color)
        y += fontsize * 1.45
    return y


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return HOME_HTML


@app.post("/api/analyze-jd")
def analyze_jd(req: JDRequest) -> Dict[str, Any]:
    return analyze_jd_text(req.jd_text)


@app.post("/api/upload-materials")
def upload_materials(req: MaterialUploadRequest) -> Dict[str, Any]:
    material_id = uuid.uuid4().hex
    MATERIAL_STORE[material_id] = {
        "filename": req.filename,
        "content": req.content,
        "content_type": req.content_type,
    }
    return {"status": "ok", "material_id": material_id, "filename": req.filename, "chars": len(req.content)}


@app.post("/api/generate-resume")
def generate_resume(req: GenerateResumeRequest) -> Dict[str, Any]:
    materials: List[Dict[str, str]] = []
    for material_id in req.material_ids:
        if material_id not in MATERIAL_STORE:
            raise HTTPException(status_code=404, detail=f"material_id not found: {material_id}")
        materials.append(MATERIAL_STORE[material_id])
    if req.pasted_material:
        materials.append({"filename": "粘贴材料", "content": req.pasted_material, "content_type": "text/plain"})
    if not materials:
        raise HTTPException(status_code=400, detail="请先上传或粘贴至少一份个人材料")

    resume_json = _build_resume_json(req.jd_text, materials)
    resume_id = uuid.uuid4().hex
    preview_html = _render_resume_html(resume_json)
    pdf_path = _write_pdf(resume_id, resume_json)
    RESUME_STORE[resume_id] = {"resume_json": resume_json, "preview_html": preview_html, "pdf_path": str(pdf_path)}
    return {"status": "ok", "resume_id": resume_id, "resume_json": resume_json}


@app.get("/api/preview", response_class=HTMLResponse)
def preview(resume_id: str = Query(...)) -> str:
    data = RESUME_STORE.get(resume_id)
    if not data:
        raise HTTPException(status_code=404, detail="resume_id not found")
    return data["preview_html"]


@app.get("/api/download-pdf")
def download_pdf(resume_id: str = Query(...)) -> Response:
    data = RESUME_STORE.get(resume_id)
    if not data:
        raise HTTPException(status_code=404, detail="resume_id not found")
    pdf_path = Path(data["pdf_path"])
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    return Response(
        pdf_path.read_bytes(),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="resume_mvp.pdf"'},
    )


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8776)
