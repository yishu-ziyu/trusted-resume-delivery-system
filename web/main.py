#!/usr/bin/env python3
"""
简历 PDF 生成器 - Web 界面
FastAPI Web 应用提供简历生成和 ATS 优化功能。
"""

import sys
import os
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from core import Config, get_logger, PDFGenerator, AIClient

# Initialize FastAPI app
app = FastAPI(
    title="简历 PDF 生成器",
    description="AI 驱动的简历生成与 ATS 优化工具",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get logger and config
logger = get_logger('web')
config = Config()

# Paths
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# HTML Frontend
HTML_CONTENT = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>简历 PDF 生成器 - ATS 智能优化</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        .form-group textarea,
        .form-group select,
        .form-group input[type="text"],
        .form-group input[type="password"] {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .form-group textarea:focus,
        .form-group select:focus,
        .form-group input[type="text"]:focus,
        .form-group input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .form-group textarea {
            min-height: 200px;
            font-family: "SF Mono", Monaco, monospace;
            resize: vertical;
        }
        .file-upload {
            border: 2px dashed #ccc;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .file-upload:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        .file-upload input {
            display: none;
        }
        .file-upload .icon {
            font-size: 3em;
            margin-bottom: 10px;
        }
        .btn {
            padding: 14px 32px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        .button-group {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 25px;
        }
        .template-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }
        .template-option {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .template-option:hover {
            border-color: #667eea;
        }
        .template-option.selected {
            border-color: #667eea;
            background: #f0f4ff;
        }
        .template-option .preview {
            height: 60px;
            border-radius: 4px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .template-option .name {
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        .loading.show {
            display: block;
        }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .result {
            display: none;
            text-align: center;
            padding: 30px;
        }
        .result.show {
            display: block;
        }
        .result .icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        .result a {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
        }
        .error {
            background: #ffe0e0;
            border: 1px solid #ffcccc;
            color: #d32f2f;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            display: none;
        }
        .error.show {
            display: block;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .checkbox-group input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            border: none;
            background: #f0f0f0;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .status-bar {
            background: #f8f9ff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status-bar .api-status {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-bar .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #ccc;
        }
        .status-bar .dot.green {
            background: #4caf50;
        }
        .status-bar .dot.red {
            background: #f44336;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 简历 PDF 生成器</h1>
            <p>AI 驱动的 ATS 智能优化工具</p>
        </div>

        <div class="card">
            <div class="status-bar">
                <span>功能状态</span>
                <div class="api-status">
                    <span class="dot" id="apiDot"></span>
                    <span id="apiStatus">检查中...</span>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📝 输入简历内容</h2>

            <div class="tabs">
                <button class="tab active" onclick="switchTab('paste')">粘贴文本</button>
                <button class="tab" onclick="switchTab('upload')">上传文件</button>
            </div>

            <div id="pasteTab" class="tab-content active">
                <div class="form-group">
                    <label for="resumeContent">简历内容 (Markdown 格式)</label>
                    <textarea id="resumeContent" placeholder="在此粘贴您的简历内容..."></textarea>
                </div>
            </div>

            <div id="uploadTab" class="tab-content">
                <div class="form-group">
                    <label>上传简历文件</label>
                    <div class="file-upload" onclick="document.getElementById('fileInput').click()">
                        <div class="icon">📁</div>
                        <div>点击选择文件或拖拽文件到此处</div>
                        <div style="font-size: 12px; color: #888; margin-top: 5px;">支持 .md, .txt 格式</div>
                        <input type="file" id="fileInput" accept=".md,.txt" onchange="handleFileSelect(event)">
                    </div>
                    <div id="fileName" style="margin-top: 10px; color: #667eea; font-weight: 600;"></div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🎨 选择模板</h2>
            <div class="template-grid">
                <div class="template-option selected" onclick="selectTemplate('default.html', this)">
                    <div class="preview" style="background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);"></div>
                    <div class="name">默认模板</div>
                </div>
                <div class="template-option" onclick="selectTemplate('modern.html', this)">
                    <div class="preview" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"></div>
                    <div class="name">现代风格</div>
                </div>
                <div class="template-option" onclick="selectTemplate('classic.html', this)">
                    <div class="preview" style="background: linear-gradient(180deg, #f5f5f5 0%, #e0e0e0 100%);"></div>
                    <div class="name">经典风格</div>
                </div>
                <div class="template-option" onclick="selectTemplate('ats-friendly.html', this)">
                    <div class="preview" style="background: #fff; border: 1px solid #e0e0e0;"></div>
                    <div class="name">ATS 友好</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>✨ ATS 优化 (可选)</h2>
            <div class="form-group checkbox-group">
                <input type="checkbox" id="enableOptimization">
                <label for="enableOptimization" style="margin: 0;">启用 AI 优化</label>
            </div>

            <div id="optimizationSection" style="display: none; margin-top: 20px;">
                <div class="form-group">
                    <label for="jdContent">职位描述 (Job Description)</label>
                    <textarea id="jdContent" placeholder="粘贴职位描述内容，AI 将根据此内容优化简历..." style="min-height: 120px;"></textarea>
                </div>
                <div class="form-group">
                    <label for="llmProvider">模型来源</label>
                    <select id="llmProvider" onchange="applyProviderPreset()">
                        <option value="openai">OpenAI</option>
                        <option value="deepseek">DeepSeek</option>
                        <option value="siliconflow">硅基流动</option>
                        <option value="ark">火山引擎 Ark</option>
                        <option value="custom">自定义 OpenAI-compatible</option>
                    </select>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div class="form-group">
                        <label for="llmModel">模型</label>
                        <input type="text" id="llmModel" placeholder="例如 gpt-4o / deepseek-chat">
                    </div>
                    <div class="form-group">
                        <label for="llmApiKey">API Key 覆盖</label>
                        <input type="password" id="llmApiKey" placeholder="留空使用服务端环境变量">
                    </div>
                </div>
                <div class="form-group">
                    <label for="llmBaseUrl">Base URL</label>
                    <input type="text" id="llmBaseUrl" placeholder="https://.../v1">
                </div>
            </div>
        </div>

        <div class="card">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div>正在生成简历 PDF...</div>
            </div>

            <div class="result" id="result">
                <div class="icon">✅</div>
                <h3>简历 PDF 生成成功！</h3>
                <p id="resultMessage"></p>
                <a id="downloadLink" href="#" download>下载 PDF</a>
            </div>

            <div class="error" id="error"></div>

            <div class="button-group" id="buttonGroup">
                <button class="btn btn-primary" onclick="generatePDF()">
                    <span>🚀</span> 生成 PDF
                </button>
            </div>
        </div>
    </div>

    <script>
        let selectedTemplate = 'default.html';
        let uploadedFileContent = null;
        const llmPresets = {
            openai: { model: 'gpt-4o', baseUrl: 'https://api.openai.com/v1' },
            deepseek: { model: 'deepseek-chat', baseUrl: 'https://api.deepseek.com' },
            siliconflow: { model: 'Qwen/Qwen2.5-72B-Instruct', baseUrl: 'https://api.siliconflow.cn/v1' },
            ark: { model: 'kimi-k2.5', baseUrl: 'https://ark.cn-beijing.volces.com/api/v3' },
            custom: { model: '', baseUrl: '' }
        };

        // Check API status on load
        window.onload = function() {
            applyProviderPreset();
            checkApiStatus();
        };

        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            if (tab === 'paste') {
                document.querySelector('.tab:first-child').classList.add('active');
                document.getElementById('pasteTab').classList.add('active');
            } else {
                document.querySelector('.tab:last-child').classList.add('active');
                document.getElementById('uploadTab').classList.add('active');
            }
        }

        function selectTemplate(template, element) {
            document.querySelectorAll('.template-option').forEach(o => o.classList.remove('selected'));
            element.classList.add('selected');
            selectedTemplate = template;
        }

        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                document.getElementById('fileName').textContent = '已选择: ' + file.name;
                const reader = new FileReader();
                reader.onload = function(e) {
                    uploadedFileContent = e.target.result;
                    document.getElementById('resumeContent').value = uploadedFileContent;
                };
                reader.readAsText(file);
            }
        }

        document.getElementById('enableOptimization').addEventListener('change', function() {
            document.getElementById('optimizationSection').style.display = this.checked ? 'block' : 'none';
        });

        async function checkApiStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                const dot = document.getElementById('apiDot');
                const status = document.getElementById('apiStatus');
                if (data.llm_configured) {
                    dot.className = 'dot green';
                    status.textContent = 'API 已配置 · ' + data.provider + ' / ' + data.model;
                } else {
                    dot.className = 'dot red';
                    status.textContent = 'API 未配置 (优化功能不可用)';
                }
            } catch (e) {
                document.getElementById('apiDot').className = 'dot red';
                document.getElementById('apiStatus').textContent = '状态检查失败';
            }
        }

        function applyProviderPreset() {
            const provider = document.getElementById('llmProvider').value;
            const preset = llmPresets[provider] || llmPresets.openai;
            document.getElementById('llmModel').value = preset.model;
            document.getElementById('llmBaseUrl').value = preset.baseUrl;
        }

        async function generatePDF() {
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const error = document.getElementById('error');
            const buttonGroup = document.getElementById('buttonGroup');

            // Hide previous states
            result.classList.remove('show');
            error.classList.remove('show');

            // Get resume content
            let resumeContent = document.getElementById('resumeContent').value.trim();
            if (!resumeContent) {
                error.textContent = '请输入简历内容或上传文件';
                error.classList.add('show');
                return;
            }

            // Get JD content if optimization is enabled
            const enableOptimization = document.getElementById('enableOptimization').checked;
            let jdContent = null;
            if (enableOptimization) {
                jdContent = document.getElementById('jdContent').value.trim();
            }

            // Show loading
            loading.classList.add('show');
            buttonGroup.style.display = 'none';

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        resume_content: resumeContent,
                        template: selectedTemplate,
                        optimize: enableOptimization,
                        jd_content: jdContent,
                        llm_config: {
                            provider: document.getElementById('llmProvider').value,
                            model: document.getElementById('llmModel').value.trim(),
                            base_url: document.getElementById('llmBaseUrl').value.trim(),
                            api_key: document.getElementById('llmApiKey').value.trim()
                        }
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    document.getElementById('downloadLink').href = '/api/download/' + data.filename;
                    document.getElementById('resultMessage').textContent = '文件已生成: ' + data.filename;
                    result.classList.add('show');
                } else {
                    error.textContent = data.detail || '生成失败';
                    error.classList.add('show');
                }
            } catch (e) {
                error.textContent = '请求失败: ' + e.message;
                error.classList.add('show');
            } finally {
                loading.classList.remove('show');
                buttonGroup.style.display = 'flex';
            }
        }
    </script>
</body>
</html>
'''


@app.get("/")
async def root():
    """Serve the main HTML page."""
    return HTMLResponse(content=HTML_CONTENT, status_code=200)


@app.get("/api/status")
async def get_status():
    """Check API and LLM configuration status."""
    config = Config()
    return {
        "status": "ok",
        "openai_configured": bool(config.llm_api_key),
        "llm_configured": bool(config.llm_api_key),
        "provider": config.llm_provider,
        "model": config.llm_model,
    }


@app.post("/api/generate")
async def generate_resume(data: dict):
    """
    Generate a resume PDF.

    Request body:
    - resume_content: str - Markdown resume content
    - template: str - Template filename
    - optimize: bool - Whether to enable AI optimization
    - jd_content: str or None - Job description for optimization
    """
    try:
        resume_content = data.get("resume_content", "").strip()
        if not resume_content:
            raise HTTPException(status_code=400, detail="简历内容不能为空")

        template = data.get("template", "default.html")
        optimize = data.get("optimize", False)
        jd_content = data.get("jd_content", "")
        llm_config = data.get("llm_config") or {}

        logger.info(f"Generating resume with template: {template}, optimize: {optimize}")

        # AI optimization if requested and API key is configured
        if optimize and jd_content:
            ai_client = AIClient(**_compact_llm_overrides(llm_config))
            if ai_client.is_available():
                logger.info("Optimizing resume with AI...")
                resume_content = ai_client.optimize_resume(resume_content, jd_content)
                # Save optimized version
                optimized_path = OUTPUT_DIR / "web_optimized_resume.md"
                optimized_path.write_text(resume_content, encoding='utf-8')
                logger.info(f"Optimized resume saved to: {optimized_path}")

        # Generate PDF
        generator = PDFGenerator(template_name=template)
        output_name = f"resume_{int(time.time())}.pdf"
        output_path = generator.generate(resume_content, output_name=output_name)

        logger.info(f"PDF generated: {output_path}")

        return {
            "status": "success",
            "filename": os.path.basename(output_path),
            "path": output_path
        }

    except Exception as e:
        logger.error(f"Error generating resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _compact_llm_overrides(raw: dict):
    return {
        key: raw.get(key)
        for key in ("provider", "model", "base_url", "api_key")
        if raw.get(key)
    }


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download a generated PDF file."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 简历 PDF 生成器 Web 界面")
    print("=" * 60)
    print("📍 访问地址: http://localhost:8765")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8765)
