# -*- coding: utf-8 -*-
"""
普通用户版简历生成网页 MVP。

目标：粘贴 JD、上传/粘贴材料、生成 Resume JSON、HTML 预览和真实 PDF 下载。
第一版使用可解释的本地启发式规则，不调用 LLM；所有事实通过 source_notes 标注来源。
"""

import base64
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

MATERIAL_STORE: Dict[str, Dict[str, Any]] = {}
RESUME_STORE: Dict[str, Dict[str, Any]] = {}
SUPPORTED_TEXT_SUFFIXES = {".txt", ".md", ".markdown"}
SUPPORTED_PDF_SUFFIXES = {".pdf"}
SUPPORTED_IMPORT_SUFFIXES = SUPPORTED_TEXT_SUFFIXES | SUPPORTED_PDF_SUFFIXES
MAX_IMPORT_FILES = 20


class JDRequest(BaseModel):
    jd_text: str = Field(..., min_length=1)


class MaterialUploadRequest(BaseModel):
    filename: str = Field(default="粘贴材料.txt")
    content: Optional[str] = None
    content_base64: Optional[str] = None
    content_type: str = Field(default="text/plain")


class LocalFolderImportRequest(BaseModel):
    folder_path: str = Field(..., min_length=1)
    max_files: int = Field(default=MAX_IMPORT_FILES, ge=1, le=50)


class GenerateResumeRequest(BaseModel):
    jd_text: str = Field(..., min_length=1)
    material_ids: List[str] = Field(default_factory=list)
    pasted_material: Optional[str] = None
    template_id: str = Field(default="formal_photo")
    resume_mode: str = Field(default="improve_existing")
    template_source: str = Field(default="uploaded_resume")


KEYWORD_GROUPS = {
    "AI产品/Agent": ["AI", "Agent", "AIGC", "大模型", "LLM", "Prompt", "AI IDE"],
    "调研分析": ["调研", "研究", "访谈", "问卷", "竞品", "行业", "报告", "分析"],
    "项目推进": ["项目", "推进", "协作", "管理", "统筹", "落地", "原型"],
    "数据分析": ["数据", "Python", "Stata", "SPSS", "Excel", "可视化", "计量"],
    "商业/金融": ["投资", "金融", "战略", "咨询", "商业", "财报", "估值"],
}

TEMPLATE_OPTIONS = {
    "formal_photo": {
        "name": "正式带照片版",
        "description": "默认推荐：一页正式投递，保留头像，适合邮件投递、内推、咨询/金融/产品岗人工阅读。",
        "with_photo": True,
        "layout": "formal",
    },
    "ats": {
        "name": "ATS 无照片版",
        "description": "机器解析优先：无头像、单栏、弱装饰，适合网申系统和简历库解析。",
        "with_photo": False,
        "layout": "ats",
    },
    "showcase_photo": {
        "name": "双栏带照片展示版",
        "description": "展示阅读优先：双栏、头像和更强层级，适合熟人内推、面试官直接阅读。",
        "with_photo": True,
        "layout": "showcase",
    },
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
    input[type=file], input[type=text] { width:100%; padding:10px; border:1px dashed var(--line); border-radius:10px; background:#fafafa; }
    input[type=text] { border-style:solid; margin-top:8px; }
    button { border:0; background:var(--blue); color:#fff; border-radius:10px; padding:11px 16px; font-weight:700; cursor:pointer; }
    button.secondary { background:#374151; }
    button:disabled { opacity:.55; cursor:not-allowed; }
    .muted { color:var(--muted); font-size:13px; }
    .actions { margin-top:14px; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
    .template-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:12px 0 4px; }
    .template-card { text-align:left; border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:12px; padding:12px; min-height:112px; cursor:pointer; }
    .template-card strong { display:block; margin-bottom:5px; }
    .template-card span { display:block; color:var(--muted); font-size:12px; line-height:1.45; }
    .template-card.active { border:2px solid var(--blue); background:#eff6ff; padding:11px; }
    .template-card .tag { display:inline-block; margin-top:8px; color:#1d4ed8; font-size:12px; font-weight:700; }
    .material-list { margin-top:10px; display:grid; gap:8px; max-height:170px; overflow:auto; }
    .material-item { border:1px solid var(--line); border-radius:10px; padding:9px 10px; background:#fbfdff; font-size:12px; display:grid; grid-template-columns:auto 1fr; gap:8px; align-items:start; }
    .material-item strong { display:block; font-size:13px; margin-bottom:3px; }
    .mode-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:10px 0 12px; }
    .mode-card { text-align:left; border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:12px; padding:11px; cursor:pointer; }
    .mode-card.active { border:2px solid #0f766e; background:#f0fdfa; padding:10px; }
    .source-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:10px 0 12px; }
    .source-card { text-align:left; border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:12px; padding:11px; cursor:pointer; }
    .source-card.active { border:2px solid #7c3aed; background:#f5f3ff; padding:10px; }
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
  <p class="muted">本地可访问版本：粘贴岗位 JD、上传原 PDF 简历 / txt / Markdown，或读取本机材料文件夹，生成 Resume JSON、来源说明、简历预览和可下载 PDF。当前版本使用本地启发式规则，不虚构无来源事实。</p>
</header>
<main>
  <section class="grid">
    <div class="card">
      <label for="jd">1. 粘贴目标岗位 JD</label>
      <textarea id="jd">AI产品实习生：负责AI Agent产品调研、用户需求分析、竞品分析、原型协作、项目推进，要求能输出结构化报告。</textarea>
    </div>
    <div class="card">
      <label for="materialText">2A. 上传你想改进的原简历 / 模板</label>
      <input id="file" type="file" accept=".pdf,.txt,.md,.markdown,application/pdf,text/plain,text/markdown" multiple />
      <p class="muted">如果用户已有自己做好的简历，请先上传这份简历；系统会优先从它提取姓名、联系方式、教育/经历和头像。没有模板时，可直接使用下面的系统模板。</p>
      <div class="mode-grid" role="radiogroup" aria-label="选择生成方式">
        <button class="mode-card active" type="button" data-mode="improve_existing"><strong>基于已有简历改进</strong><span class="muted">推荐：上传原简历/模板后，再用材料库补充证据。</span></button>
        <button class="mode-card" type="button" data-mode="new_from_materials"><strong>没有模板，生成新简历</strong><span class="muted">只基于材料库和 JD 生成系统模板。</span></button>
      </div>
      <div class="source-grid" role="radiogroup" aria-label="选择模板来源">
        <button class="source-card active" type="button" data-source="uploaded_resume"><strong>沿用上传简历信息</strong><span class="muted">优先复用上传 PDF 的姓名、联系方式、头像和基础事实，不承诺像素级克隆。</span></button>
        <button class="source-card" type="button" data-source="system_template"><strong>使用系统模板</strong><span class="muted">不依赖原简历版式，用系统内置正式/ATS/展示模板重排。</span></button>
      </div>
      <label for="folderPath">2B. 补充事实材料库</label>
      <input id="folderPath" type="text" placeholder="可选：输入本机材料文件夹路径，例如 /Users/mahaoxuan/Desktop/春招" />
      <div class="actions"><button id="importFolder" class="secondary" type="button">读取本机材料文件夹</button></div>
      <p class="muted">导入后会显示可勾选材料，默认优先选中“简历/高相关材料”，避免把文件夹里所有资料无差别塞进简历。</p>
      <div id="materialList" class="material-list"></div>
      <label>3. 选择输出模板</label>
      <div class="template-grid" role="radiogroup" aria-label="选择输出模板">
        <button class="template-card active" type="button" data-template="formal_photo"><strong>正式带照片版</strong><span>默认推荐：正式投递、内推、人工阅读；会优先复用原 PDF 头像。</span><em class="tag">带头像</em></button>
        <button class="template-card" type="button" data-template="ats"><strong>ATS 无照片版</strong><span>网申/机器解析优先；单栏、无头像、弱装饰。</span><em class="tag">无头像</em></button>
        <button class="template-card" type="button" data-template="showcase_photo"><strong>双栏带照片展示版</strong><span>熟人内推、面试官直接阅读；更强视觉层级。</span><em class="tag">带头像</em></button>
      </div>
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
const folderPath = document.getElementById('folderPath');
const importFolderBtn = document.getElementById('importFolder');
const jd = document.getElementById('jd');
const statusEl = document.getElementById('status');
const generateBtn = document.getElementById('generate');
const downloadBtn = document.getElementById('download');
const result = document.getElementById('result');
const materialList = document.getElementById('materialList');
let currentResumeId = null;
let uploadedMaterialIds = [];
let selectedMaterialIds = new Set();
let selectedTemplateId = 'formal_photo';
let selectedMode = 'improve_existing';
let selectedTemplateSource = 'uploaded_resume';

function addMaterialItem(item, checked=true) {
  if (checked) selectedMaterialIds.add(item.material_id);
  const label = document.createElement('label');
  label.className = 'material-item';
  label.innerHTML = `<input type="checkbox" ${checked ? 'checked' : ''} data-id="${item.material_id}">
    <span><strong>${item.filename}</strong><span class="muted">${item.material_type || 'material'}｜相关度${item.relevance_score ?? '-'}｜${item.diagnostics?.summary || item.chars + '字'}</span></span>`;
  label.querySelector('input').addEventListener('change', (event) => {
    if (event.target.checked) selectedMaterialIds.add(item.material_id);
    else selectedMaterialIds.delete(item.material_id);
  });
  materialList.appendChild(label);
}

document.querySelectorAll('.template-card').forEach(card => {
  card.addEventListener('click', () => {
    selectedTemplateId = card.dataset.template;
    document.querySelectorAll('.template-card').forEach(x => x.classList.remove('active'));
    card.classList.add('active');
    statusEl.textContent = `已选择模板：${card.querySelector('strong').textContent}`;
  });
});

document.querySelectorAll('.mode-card').forEach(card => {
  card.addEventListener('click', () => {
    selectedMode = card.dataset.mode;
    document.querySelectorAll('.mode-card').forEach(x => x.classList.remove('active'));
    card.classList.add('active');
    statusEl.textContent = `已选择生成方式：${card.querySelector('strong').textContent}`;
  });
});

document.querySelectorAll('.source-card').forEach(card => {
  card.addEventListener('click', () => {
    selectedTemplateSource = card.dataset.source;
    document.querySelectorAll('.source-card').forEach(x => x.classList.remove('active'));
    card.classList.add('active');
    statusEl.textContent = `已选择模板来源：${card.querySelector('strong').textContent}`;
  });
});

function arrayBufferToBase64(buffer) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

async function uploadFile(file) {
  const isPdf = /[.]pdf$/i.test(file.name) || file.type === 'application/pdf';
  const payload = {filename: file.name, content_type: file.type || (isPdf ? 'application/pdf' : 'text/plain')};
  if (isPdf) {
    payload.content_base64 = arrayBufferToBase64(await file.arrayBuffer());
  } else if (/[.](txt|md|markdown)$/i.test(file.name)) {
    payload.content = await file.text();
  } else {
    throw new Error(`暂不支持的文件类型：${file.name}`);
  }
  const resp = await fetch('/api/upload-materials', {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}

fileInput.addEventListener('change', async () => {
  const files = Array.from(fileInput.files || []);
  if (!files.length) return;
  try {
    statusEl.textContent = `正在读取 ${files.length} 个文件...`;
    uploadedMaterialIds = [];
    selectedMaterialIds = new Set();
    materialList.innerHTML = '';
    const summaries = [];
    for (const file of files) {
      const data = await uploadFile(file);
      uploadedMaterialIds.push(data.material_id);
      addMaterialItem(data, true);
      summaries.push(`${data.filename}（${data.chars}字${data.diagnostics ? '，' + data.diagnostics.summary : ''}）`);
    }
    statusEl.textContent = `已导入：${summaries.join('；')}`;
    if (files.length === 1 && /[.](txt|md|markdown)$/i.test(files[0].name)) {
      materialText.value = await files[0].text();
    }
  } catch (err) {
    statusEl.textContent = '文件导入失败：' + err;
  }
});

importFolderBtn.addEventListener('click', async () => {
  try {
    const path = folderPath.value.trim();
    if (!path) { statusEl.textContent = '请先输入本机材料文件夹路径。'; return; }
    importFolderBtn.disabled = true;
    statusEl.textContent = '正在读取本机材料文件夹...';
    const resp = await fetch('/api/import-local-folder', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({folder_path:path, max_files:20})
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || JSON.stringify(data));
    uploadedMaterialIds = uploadedMaterialIds.concat(data.material_ids);
    (data.imported_materials || []).forEach((item) => addMaterialItem(item, item.default_selected));
    statusEl.textContent = `已从文件夹导入 ${data.imported_count} 份材料，默认选中 ${selectedMaterialIds.size} 份高相关/简历材料。请在材料列表中勾选后再生成。`;
  } catch (err) {
    statusEl.textContent = '读取文件夹失败：' + err;
  } finally {
    importFolderBtn.disabled = false;
  }
});

generateBtn.addEventListener('click', async () => {
  try {
    generateBtn.disabled = true;
    statusEl.textContent = '正在整理材料并生成 Resume JSON...';
    let materialIds = Array.from(selectedMaterialIds);
    const pasted = materialText.value.trim();
    if (pasted) {
      const upload = await fetch('/api/upload-materials', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({filename:'粘贴材料.md', content:pasted, content_type:'text/markdown'})
      }).then(r => r.json());
      materialIds.push(upload.material_id);
      if (!selectedMaterialIds.has(upload.material_id)) addMaterialItem(upload, true);
    }
    if (!materialIds.length) throw new Error('请先上传 PDF/txt/Markdown、读取本机文件夹，或粘贴个人材料。');
    statusEl.textContent = `正在分析 JD，并基于 ${materialIds.length} 份材料生成 Resume JSON...`;
    const gen = await fetch('/api/generate-resume', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({jd_text: jd.value, material_ids:materialIds, template_id:selectedTemplateId, resume_mode:selectedMode, template_source:selectedTemplateSource})
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


def _normalize_extracted_text(value: str) -> str:
    lines = []
    for line in (value or "").splitlines():
        cleaned = _clean_text(line)
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def _extract_portrait_data_uri(doc: fitz.Document) -> Optional[str]:
    """Pick the largest portrait-like embedded image from an uploaded PDF."""
    best: Optional[Dict[str, Any]] = None
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                info = doc.extract_image(xref)
            except Exception:
                continue
            width = int(info.get("width") or 0)
            height = int(info.get("height") or 0)
            if width < 40 or height < 40:
                continue
            aspect = width / max(height, 1)
            area = width * height
            portrait_bonus = 1.25 if 0.55 <= aspect <= 1.35 else 1.0
            score = area * portrait_bonus
            if not best or score > best["score"]:
                ext = (info.get("ext") or "png").lower()
                mime = "jpeg" if ext in {"jpg", "jpeg"} else "png"
                best = {"score": score, "mime": mime, "image": info.get("image", b"")}
    if not best or not best["image"]:
        return None
    return f"data:image/{best['mime']};base64," + base64.b64encode(best["image"]).decode("ascii")


def _extract_pdf_text_and_diagnostics(pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"PDF 无法打开：{filename}｜{exc}") from exc

    page_texts: List[str] = []
    image_count = 0
    for page in doc:
        page_texts.append(page.get_text("text") or "")
        image_count += len(page.get_images(full=True))
    photo_data_uri = _extract_portrait_data_uri(doc)
    text = _normalize_extracted_text("\n".join(page_texts))
    diagnostics = {
        "pages": len(doc),
        "images": image_count,
        "extractable_chars": len(text),
        "summary": f"PDF {len(doc)}页，可提取{text and len(text) or 0}字，图片{image_count}张" + ("，已提取候选头像" if photo_data_uri else ""),
        "needs_ocr": len(text) < 30,
        "photo_candidate": bool(photo_data_uri),
    }
    doc.close()
    if diagnostics["needs_ocr"]:
        text = text or "[PDF文本层过少：可能是扫描版或图片型PDF，后续需要OCR后才能作为强证据。]"
    return {"content": text, "diagnostics": diagnostics, "photo_data_uri": photo_data_uri}


def _classify_material(filename: str, content: str, diagnostics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    text = f"{filename}\n{content}".lower()
    diagnostics = diagnostics or {}
    if "简历" in filename or "resume" in text or ("@" in content and "大学" in content and ("经历" in content or "项目" in content)):
        material_type = "resume_template"
        score = 100
    elif any(word in text for word in ["作品集", "portfolio", "项目", "报告", "调研", "prd"]):
        material_type = "evidence"
        score = 75
    elif any(word in text for word in ["证书", "成绩单", "身份证", "个人材料"]):
        material_type = "private_or_certificate"
        score = 35
    else:
        material_type = "background_material"
        score = 55
    if diagnostics.get("needs_ocr"):
        score = min(score, 25)
    return {"material_type": material_type, "relevance_score": score, "default_selected": score >= 55}


def _material_from_upload(filename: str, content_type: str, content: Optional[str], content_base64: Optional[str]) -> Dict[str, Any]:
    suffix = Path(filename).suffix.lower()
    if content_base64 or suffix == ".pdf" or content_type == "application/pdf":
        if not content_base64:
            raise HTTPException(status_code=400, detail="PDF 上传需要 content_base64")
        try:
            pdf_bytes = base64.b64decode(content_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"base64 解码失败：{exc}") from exc
        extracted = _extract_pdf_text_and_diagnostics(pdf_bytes, filename)
        material = {
            "filename": filename,
            "content": extracted["content"],
            "content_type": "application/pdf",
            "diagnostics": extracted["diagnostics"],
            "photo_data_uri": extracted.get("photo_data_uri"),
        }
        material.update(_classify_material(filename, extracted["content"], extracted["diagnostics"]))
        return material

    text = (content or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="上传材料内容为空")
    material = {
        "filename": filename,
        "content": text,
        "content_type": content_type or "text/plain",
        "diagnostics": {"summary": f"文本{len(text)}字"},
    }
    material.update(_classify_material(filename, text, material["diagnostics"]))
    return material


def _read_supported_file(path: Path) -> Dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_TEXT_SUFFIXES:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return _material_from_upload(path.name, "text/plain", text, None)
    if suffix in SUPPORTED_PDF_SUFFIXES:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return _material_from_upload(path.name, "application/pdf", None, encoded)
    raise HTTPException(status_code=400, detail=f"暂不支持的文件类型：{path.name}")


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


def _clean_resume_item(line: str) -> str:
    line = _clean_text(line).strip("-• ")
    line = re.sub(r"^(经历|项目|技能|教育|奖项|证书|实习|工作)[:：]\s*", "", line)
    return line


def _find_lines(material_text: str, words: List[str], limit: int) -> List[str]:
    lines = []
    seen = set()
    for raw in material_text.splitlines():
        line = raw.strip(" -\t")
        if not line:
            continue
        if any(w.lower() in line.lower() for w in words) and line not in seen:
            cleaned = _clean_resume_item(line)
            if cleaned and cleaned not in seen:
                lines.append(cleaned)
                seen.add(cleaned)
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


def _build_resume_json(
    jd_text: str,
    materials: List[Dict[str, Any]],
    template_id: str = "formal_photo",
    resume_mode: str = "improve_existing",
    template_source: str = "uploaded_resume",
) -> Dict[str, Any]:
    if template_id not in TEMPLATE_OPTIONS:
        raise HTTPException(status_code=400, detail=f"未知模板：{template_id}")
    template = TEMPLATE_OPTIONS[template_id]
    jd_info = analyze_jd_text(jd_text)
    material_text = "\n".join(m["content"] for m in materials)
    photo_data_uri = next((m.get("photo_data_uri") for m in materials if m.get("photo_data_uri")), None)
    contact = _extract_contact(material_text)
    material_hits = _keyword_hits(material_text)
    jd_hits = jd_info["keywords"]
    overlap = [x for x in jd_hits if x in material_hits]
    score = min(95, 45 + len(overlap) * 12 + min(len(material_text) // 180, 18))

    education_lines = _find_lines(material_text, ["大学", "本科", "硕士", "专业", "毕业"], 2)
    education_lines = ["｜".join(part for part in line.split("｜") if any(k in part for k in ["大学", "本科", "硕士", "专业", "毕业"])) or line for line in education_lines]
    experience_lines = _find_lines(material_text, ["经历", "实习", "公司", "银行", "投资", "岗位"], 4)
    project_lines = [
        line for line in _find_lines(material_text, ["项目", "调研", "报告", "Agent", "AIGC", "插件", "App"], 8)
        if line not in experience_lines
    ][:5]
    skill_lines = _find_lines(material_text, ["技能", "Python", "Stata", "SPSS", "Excel", "Prompt"], 3)

    source_names = "、".join(m["filename"] for m in materials[:3]) + ("等" if len(materials) > 3 else "")
    source_notes = [
        {"claim": f"姓名：{contact['name']}", "source": f"上传/导入材料：{source_names}", "confidence": "high"},
        {"claim": jd_info["jd_summary"], "source": "用户粘贴 JD", "confidence": "high"},
    ]
    for material in materials:
        diagnostics = material.get("diagnostics") or {}
        if diagnostics.get("summary"):
            confidence = "low" if diagnostics.get("needs_ocr") else "medium"
            source_notes.append({"claim": f"{material['filename']}：{diagnostics['summary']}", "source": f"材料诊断：{material['filename']}", "confidence": confidence})
    for line in _dedupe_lines(education_lines + experience_lines + project_lines + skill_lines)[:8]:
        source_notes.append({"claim": line[:120], "source": f"上传/导入材料：{source_names}", "confidence": "medium"})

    return {
        "target_role": jd_info["target_role"],
        "jd_summary": jd_info["jd_summary"],
        "candidate_summary": "匹配方向：" + ("、".join(overlap) if overlap else "需要用户补充更具体的岗位相关材料"),
        "match_score": score,
        "template": {"id": template_id, **template},
        "template_source": template_source,
        "resume_mode": resume_mode,
        "photo_data_uri": photo_data_uri if template.get("with_photo") and template_source == "uploaded_resume" else None,
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
    template = resume_json.get("template") or TEMPLATE_OPTIONS["formal_photo"]
    template_id = template.get("id", "formal_photo")
    photo_data_uri = resume_json.get("photo_data_uri")

    def section(title: str, items: List[str], max_items: int = 5) -> str:
        shown = (items or [])[:max_items]
        escaped_items = "".join(f"<li>{html.escape(item)}</li>" for item in shown) or "<li>暂无可确认材料，建议补充来源。</li>"
        return f"<section><h3>{html.escape(title)}</h3><ul>{escaped_items}</ul></section>"

    notes = "".join(
        f"<li>{html.escape(n['claim'])}<br><small>来源：{html.escape(n['source'])}｜可信度：{html.escape(n['confidence'])}</small></li>"
        for n in resume_json["source_notes"][:8]
    )
    photo_html = f'<img class="avatar" src="{photo_data_uri}" alt="候选头像" />' if photo_data_uri else ''
    contact = f"{html.escape(resume['contact'].get('email',''))} ｜ {html.escape(resume['contact'].get('phone',''))} ｜ 目标：{html.escape(resume_json['target_role'])}"
    common_style = """
        .resume-doc { font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',Arial,sans-serif; color:#111827; line-height:1.48; }
        .resume-doc h2 { margin:0 0 6px; font-size:24px; letter-spacing:.04em; }
        .resume-doc h3 { margin:13px 0 6px; font-size:14px; color:#1d4ed8; border-bottom:1px solid #d8dee8; padding-bottom:3px; }
        .resume-doc ul { margin:0; padding-left:17px; }
        .resume-doc li { margin:3px 0; }
        .resume-doc small { color:#6b7280; }
        .resume-doc .meta { color:#4b5563; font-size:12px; }
        .resume-doc .avatar { width:76px; height:92px; object-fit:cover; border-radius:10px; border:1px solid #d8dee8; background:#f3f4f6; }
        .resume-doc .placeholder-avatar { display:flex; align-items:center; justify-content:center; color:#9ca3af; font-size:12px; }
        .resume-doc .source-hint { color:#6b7280; font-size:11px; margin-top:10px; border-top:1px dashed #d8dee8; padding-top:6px; }
    """
    if template_id == "ats":
        return f"""
    <article class="resume-doc resume-ats" data-template="ats">
      <style>{common_style}
        .resume-ats {{ background:#fff; }}
        .resume-ats .meta {{ border-bottom:1px solid #d8dee8; padding-bottom:10px; margin-bottom:12px; }}
      </style>
      <h2>{html.escape(resume['name'])}</h2>
      <div class="meta">{contact}</div>
      <p><strong>岗位匹配摘要：</strong>{html.escape(resume_json['candidate_summary'])}</p>
      {section('教育背景', resume['education'])}
      {section('经历', resume['experiences'])}
      {section('项目', resume['projects'])}
      {section('技能', resume['skills'])}
      {section('奖项/证书', resume['awards'])}
    </article>
    """
    if template_id == "showcase_photo":
        return f"""
    <article class="resume-doc resume-showcase" data-template="showcase_photo">
      <style>{common_style}
        .resume-showcase {{ display:grid; grid-template-columns:31% 1fr; min-height:100%; border:1px solid #d8dee8; }}
        .resume-showcase .side {{ background:#eef4ff; padding:18px 14px; }}
        .resume-showcase .main {{ padding:18px 20px; }}
        .resume-showcase .avatar {{ width:88px; height:108px; margin-bottom:10px; }}
        .resume-showcase h3 {{ color:#1e3a8a; }}
      </style>
      <aside class="side">{photo_html}<h2>{html.escape(resume['name'])}</h2><div class="meta">{contact}</div>{section('技能', resume['skills'], 4)}</aside>
      <main class="main"><p><strong>岗位匹配摘要：</strong>{html.escape(resume_json['candidate_summary'])}</p>{section('教育背景', resume['education'])}{section('经历', resume['experiences'])}{section('项目', resume['projects'])}{section('奖项/证书', resume['awards'])}</main>
    </article>
    """
    return f"""
    <article class="resume-doc resume-formal" data-template="formal_photo">
      <style>{common_style}
        .resume-formal {{ border:1px solid #d8dee8; padding:18px 20px; position:relative; overflow:hidden; }}
        .resume-formal:before {{ content:""; position:absolute; right:-30px; top:-30px; width:150px; height:150px; background:linear-gradient(135deg, rgba(37,99,235,.08), transparent); border-radius:999px; }}
        .resume-formal .head {{ display:grid; grid-template-columns:{'92px 1fr' if photo_data_uri else '1fr'}; gap:14px; align-items:center; position:relative; z-index:1; border-bottom:1px solid #d8dee8; padding-bottom:12px; margin-bottom:10px; }}
        .resume-formal .body {{ display:grid; grid-template-columns:1fr 1fr; gap:0 20px; position:relative; z-index:1; }}
        .resume-formal .full {{ grid-column:1 / -1; }}
      </style>
      <div class="head">{photo_html}<div><h2>{html.escape(resume['name'])}</h2><div class="meta">{contact}</div><p><strong>岗位匹配摘要：</strong>{html.escape(resume_json['candidate_summary'])}</p></div></div>
      <div class="body">{section('教育背景', resume['education'])}{section('技能', resume['skills'])}<div class="full">{section('经历', resume['experiences'])}</div><div class="full">{section('项目', resume['projects'])}</div>{section('奖项/证书', resume['awards'])}</div>
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
    material = _material_from_upload(req.filename, req.content_type, req.content, req.content_base64)
    material_id = uuid.uuid4().hex
    MATERIAL_STORE[material_id] = material
    return {
        "status": "ok",
        "material_id": material_id,
        "filename": material["filename"],
        "chars": len(material["content"]),
        "diagnostics": material.get("diagnostics", {}),
        "material_type": material.get("material_type"),
        "relevance_score": material.get("relevance_score"),
        "default_selected": material.get("default_selected", True),
    }


@app.post("/api/import-local-folder")
def import_local_folder(req: LocalFolderImportRequest) -> Dict[str, Any]:
    folder = Path(req.folder_path).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"文件夹不存在：{folder}")

    candidates = [p for p in sorted(folder.rglob("*")) if p.is_file() and p.suffix.lower() in SUPPORTED_IMPORT_SUFFIXES]
    if not candidates:
        raise HTTPException(status_code=400, detail="该文件夹中没有可导入的 txt / Markdown / PDF 文件")

    imported_ids: List[str] = []
    imported_files: List[str] = []
    imported_materials: List[Dict[str, Any]] = []
    skipped_files: List[str] = []
    for path in candidates[: req.max_files]:
        try:
            material = _read_supported_file(path)
        except Exception as exc:
            skipped_files.append(f"{path.name}: {exc}")
            continue
        material["filename"] = str(path)
        material_id = uuid.uuid4().hex
        MATERIAL_STORE[material_id] = material
        imported_ids.append(material_id)
        imported_files.append(path.name)
        imported_materials.append({
            "material_id": material_id,
            "filename": path.name,
            "chars": len(material.get("content", "")),
            "diagnostics": material.get("diagnostics", {}),
            "material_type": material.get("material_type"),
            "relevance_score": material.get("relevance_score"),
            "default_selected": material.get("default_selected", False),
        })

    if not imported_ids:
        raise HTTPException(status_code=400, detail="找到文件但均未能成功读取")

    return {
        "status": "ok",
        "folder_path": str(folder),
        "material_ids": imported_ids,
        "imported_count": len(imported_ids),
        "imported_files": imported_files,
        "imported_materials": sorted(imported_materials, key=lambda x: x.get("relevance_score") or 0, reverse=True),
        "skipped_files": skipped_files,
        "limited": len(candidates) > req.max_files,
    }


@app.post("/api/generate-resume")
def generate_resume(req: GenerateResumeRequest) -> Dict[str, Any]:
    materials: List[Dict[str, Any]] = []
    for material_id in req.material_ids:
        if material_id not in MATERIAL_STORE:
            raise HTTPException(status_code=404, detail=f"material_id not found: {material_id}")
        materials.append(MATERIAL_STORE[material_id])
    if req.pasted_material:
        materials.append({"filename": "粘贴材料", "content": req.pasted_material, "content_type": "text/plain"})
    if not materials:
        raise HTTPException(status_code=400, detail="请先上传或粘贴至少一份个人材料")

    resume_json = _build_resume_json(
        req.jd_text,
        materials,
        template_id=req.template_id,
        resume_mode=req.resume_mode,
        template_source=req.template_source,
    )
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
