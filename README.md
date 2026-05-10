# 项目D：可信投递系统 / 简历 PDF 生成器

这个项目现在是唯一主项目，已经吸收旧的 `resume-pdf-builder`。

主项目路径：

`/Users/mahaoxuan/Desktop/AI产品经理/项目D-简历PDF生成器`

旧项目已移入：

`legacy/resume-pdf-builder/`

## 一句话定位

这个项目帮助用户基于自己的真实经历素材和目标岗位 JD，生成更贴合岗位、更符合个人画像、可直接投递的定制简历 PDF。

它不是单纯“生成漂亮 PDF”，而是一个 JD 驱动的可信投递系统：

```text
JD输入
  ↓
原始简历 + 事实材料库
  ↓
材料解析与事实抽取
  ↓
事实索引 / 证据库
  ↓
JD岗位解析
  ↓
JD要求 ↔ 个人事实 匹配矩阵
  ↓
简历改写策略
  ↓
结构化简历数据 YAML/JSON
  ↓
ATS投递版 + 正式带照片版 + 展示阅读版
  ↓
PDF渲染
  ↓
PDF技术核查 + 视觉检查 + 独立检查Agent核查
  ↓
用户确认清单
  ↓
最终可投递版本
```

## 当前最重要成果

### 1. 普通用户版网页 MVP

文件：

`web/resume_mvp_app.py`

当前服务入口：

`http://127.0.0.1:8776/`

运行方式：

```bash
cd '/Users/mahaoxuan/Desktop/AI产品经理/项目D-简历PDF生成器'
/usr/bin/python3 web/resume_mvp_app.py
```

页面流程：

- 粘贴目标岗位 JD。
- 上传或粘贴个人材料。
- 点击“生成适配简历”。
- 查看 JD 摘要、候选人摘要、匹配说明、Resume JSON、source_notes 和简历预览。
- 下载真实 PDF。

当前 API：

```text
GET  /api/health
POST /api/analyze-jd
POST /api/upload-materials
POST /api/generate-resume
GET  /api/preview?resume_id=...
GET  /api/download-pdf?resume_id=...
```

当前支持材料格式：

- 直接粘贴文本。
- `.txt`。
- `.md` / `.markdown`。

实现说明：

- 第一版使用本地启发式规则，不调用 LLM。
- 文件上传由浏览器读取 txt / Markdown 为文本，再通过 JSON 提交，不依赖 `python-multipart`。
- 后端围绕 `Resume JSON` 生成预览和 PDF。
- PDF 由 PyMuPDF 生成，下载接口返回真实 `application/pdf`。
- 运行期文件写入 `output/resume_mvp_runtime/`。

可信事实边界：

- `source_notes` 是核心输出，不是附加说明。
- 没有来源的内容不能写成确定事实。
- 弱来源或自动推断内容应标注为 `medium` 或 `low`，后续需要用户确认。
- 当前版本只根据用户输入 JD 和上传 / 粘贴材料生成，不应虚构公司、岗位、项目成果、工具能力或商业化指标。

当前限制：

- 本地单用户演示，不含登录、数据库、多用户、云部署。
- 数据暂存在内存中，服务重启后生成记录会丢失。
- Word / PDF 文件上传解析尚未完整开放。
- 匹配分和摘要是启发式结果，只用于产品闭环验证，不能当作正式评估。
- 后续需要替换为真实材料解析、LLM JD 匹配、用户确认流程和多模板 PDF Builder。

### 2. 可信投递系统 Demo

文件：

`web/可信投递系统Demo.py`

当前服务入口：

`http://127.0.0.1:8766/`

运行方式：

```bash
cd '/Users/mahaoxuan/Desktop/AI产品经理/项目D-简历PDF生成器'
python3 web/可信投递系统Demo.py
```

页面包含：

- JD 输入区。
- 真实材料来源。
- 产品闭环：材料库 → JD解析 → 事实匹配 → 模板选择 → 核查确认。
- 模板切换。
- 简历预览图。
- PDF / HTML / 预览图入口。
- PDF验证区。
- 事实核查与用户确认。
- Markdown报告入口。

### 3. 当前正式投递主推版本

中文主文件：

`output/正式候选版_带照片_AI研发产品线_v2/中文版本/第1版_推荐优先看_AI研发产品线_正式投递带照片版_v2.pdf`

主PDF：

`output/正式候选版_带照片_AI研发产品线_v2/05_正式投递带照片版_v2.pdf`

已核查：

- 1页。
- 1张照片。
- 文本可抽取。
- 包含姓名、邮箱、AI Agent、AIGC、招商银行、海坤、chrome-md-editor、battery-takeover 等关键词。
- 不虚构 PRD。
- 不虚构 ToB/SaaS 产品实习。

### 3. 可信投递 Demo 数据目录

`output/jd_experiment_route_b_consulting_ai_strategy/`

该目录现在也包含 `formal_v2/`，用于网页 Demo 打开最新正式投递带照片版。

## 项目结构

```text
项目D-简历PDF生成器/
  core/                         # 简历解析、PDF生成等核心模块
  scripts/                      # 生成脚本、可信投递实验脚本
  web/                          # Web入口；可信投递系统Demo在这里
  tests/                        # PDF生成与照片提取测试
  templates/                    # HTML模板库
  output/                       # 所有实验输出、PDF、预览图、报告
  legacy/resume-pdf-builder/    # 旧resume-pdf-builder完整归档
  README.md                     # 当前说明
  PROJECT_POSITIONING.md        # 产品定位
  合并方案.md                   # 两项目合并方案
  合并完成说明.md               # 合并记录
```

## 旧项目保留内容

旧 `resume-pdf-builder` 没有删除内容，而是完整移入：

`legacy/resume-pdf-builder/`

里面保留：

- 早期 README。
- HTML模板：default / modern / ats-friendly / classic。
- 早期 CLI 脚本。
- 早期 Web main.py。
- 示例简历和 demo 输出。

后续如果要做“模板库”，可以从 legacy 中逐步抽取这些 HTML 模板。

## 关键事实边界

当前用户已确认：

- `/Users/mahaoxuan/Desktop/马浩宣简历.pdf` 是原始简历模板。
- 正式投递需要带照片版本。
- AIGC调研报告由用户基本主导，用户是副负责人。
- 当前没有可展示的 PRD。
- 当前没有 ToB/SaaS 产品实习经历。
- 网页端 Markdown 插件和 Mac 电池管理 App 可以公开展示并给仓库链接。

公开项目链接：

- `chrome-md-editor`: https://github.com/yishu-ziyu/chrome-md-editor
- `battery-takeover`: https://github.com/yishu-ziyu/battery-takeover

## 注意事项

1. 海坤招聘数字仍有口径冲突：
   - 原始模板：28份 / 2名。
   - 春招简历：30份 / 3名。
   - 最终确认前不要写具体数字。

2. 不要写：
   - 独立撰写完整 PRD。
   - ToB/SaaS 产品实习。
   - 熟练 SQL / Tableau / PowerBI。
   - 商业化收入增长指标。

3. 每次输出具体数字前，需要独立检查Agent核查原文位置。
