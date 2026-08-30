# Trusted Resume Delivery System

> JD 驱动的可信简历生成系统：从真实材料出发，生成可核查、可投递的定制简历 PDF。

基于真实经历素材与目标岗位 JD，生成贴合岗位、事实可溯源、可直接投递的简历 PDF。核心不是"生成漂亮 PDF"，而是把**可信**做进流程：每一句简历内容都能回到具体来源。

## 核心理念：可信事实边界

AI 生成简历的最大风险是虚构。本系统把事实边界做成一等公民：

- **`source_notes` 是核心输出，不是附加说明**——每条简历内容都绑定来源
- 没有来源的内容不能写成确定事实
- 弱来源或自动推断内容标注为 `medium` / `low`，由用户确认后才可使用
- 系统不虚构公司、岗位、项目成果、工具能力或商业化指标
- 具体数字在投递前经过独立核查步骤

## 生成流水线

```text
JD 输入
  ↓
原始简历 + 事实材料库
  ↓
材料解析与事实抽取
  ↓
事实索引 / 证据库
  ↓
JD 岗位解析
  ↓
JD 要求 ↔ 个人事实 匹配矩阵
  ↓
简历改写策略
  ↓
结构化简历数据（YAML/JSON）
  ↓
ATS 投递版 / 正式版 / 展示阅读版
  ↓
PDF 渲染
  ↓
PDF 技术核查 + 视觉检查 + 独立检查 Agent
  ↓
用户确认清单
  ↓
最终可投递版本
```

## 网页 MVP

本地运行：

```bash
python3 web/resume_mvp_app.py
# 打开 http://127.0.0.1:8776/
```

页面流程：粘贴目标 JD → 上传/粘贴材料（纯文本 / `.txt` / `.md`）→ 生成适配简历 → 查看 JD 摘要、匹配说明、Resume JSON、`source_notes` 与预览 → 下载 PDF。

API：

```text
GET  /api/health
POST /api/analyze-jd
POST /api/upload-materials
POST /api/generate-resume
GET  /api/preview?resume_id=...
GET  /api/download-pdf?resume_id=...
```

另有一个完整产品闭环 Demo（`web/可信投递系统Demo.py`）：材料库 → JD 解析 → 事实匹配 → 模板选择 → PDF 验证 → 事实核查与用户确认。

## 技术实现

| 模块 | 说明 |
|---|---|
| JD 解析与匹配 | 第一版本地启发式规则，不调用 LLM；预留 LLM 匹配接入位 |
| 材料读取 | 浏览器端读取文本类文件经 JSON 提交，无 `python-multipart` 依赖 |
| 简历数据 | 结构化 `Resume JSON`，预览与 PDF 均以它为唯一事实源 |
| PDF 生成 | PyMuPDF，下载接口返回真实 `application/pdf` |
| 测试 | PDF 生成与照片提取测试（`tests/`） |

当前为本地单用户 MVP：无登录、无数据库、内存态存储；Word/PDF 上传解析与多模板 PDF Builder 在路线图中。

## 项目结构

```text
core/                 # 简历解析、PDF 生成核心模块
web/                  # Web 入口（MVP + 完整 Demo）
templates/            # HTML 模板库（继承自 legacy 模板体系）
tests/                # PDF 生成与照片提取测试
scripts/              # 生成与实验脚本
legacy/resume-pdf-builder/   # 前身项目完整归档（HTML 模板库来源）
```

## License

MIT
