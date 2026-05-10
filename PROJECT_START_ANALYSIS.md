# 项目D：JD 驱动的简历 PDF 生成器 - 启动分析

> 目标：把“每个岗位手工做一版简历”变成“用户提供基础简历 + 目标 JD，系统自动生成一版针对该 JD 的 PDF 简历”。

当前项目已有雏形：

- `scripts/optimize_pdf_resume.py`：PDF 简历 + JD → AI 分析 → Markdown 简历 → PDF
- `scripts/generate.py`：Markdown 简历 → PDF，可选 AI 优化
- `core/ai_client.py`：OpenAI-compatible LLM 调用
- `core/pdf_generator.py`：Markdown → HTML 模板 → WeasyPrint PDF
- `core/resume_extractor.py`：从 Markdown 中抽取姓名、联系方式等基础字段
- `templates/*.html`：多套 HTML 简历模板

但如果要成为一个可靠产品，需要重新定义“用户输入、系统中间状态、确认机制、测试体系”。

---

## 1. 这个产品真正要解决的问题

用户原来的流程：

1. 看到一个岗位 JD。
2. 打开自己的通用简历。
3. 手工挑选相关经历。
4. 手工改关键词、项目描述、技能顺序。
5. 手工排版导出 PDF。
6. 担心改过头、编造、格式乱、ATS 不通过。

目标流程：

1. 用户上传一份“基础真实简历”。
2. 用户粘贴或上传目标岗位 JD。
3. 系统解析 JD 要求。
4. 系统解析用户经历库存。
5. 系统给出匹配分析与修改方案。
6. 用户确认修改边界。
7. 系统生成针对该 JD 的新版简历 PDF。
8. 用户拿到 PDF + 修改报告 + 可编辑 Markdown/JSON 源文件。

核心价值不是“AI 改文案”，而是：

- 帮用户从真实经历中选择最相关内容。
- 帮用户把经历表述对齐 JD 语言。
- 帮用户保证不编造、不漏关键信息、不破坏 PDF 格式。
- 帮用户把每个岗位的简历版本自动沉淀下来。

---

## 2. 用户需要提供什么，才能得到可用反馈

### 最小可用输入 MVP

用户必须提供：

1. 基础简历
   - PDF、Markdown、DOCX 三选一；MVP 可以先支持 PDF + Markdown。
   - 内容必须包含教育、经历、项目、技能、联系方式。

2. 目标岗位 JD
   - 文本粘贴或 `.txt` 文件。
   - 最好包含岗位职责、任职要求、加分项、公司/岗位名称。

3. 用户确认信号
   - 系统不能直接最终改简历。
   - 必须先展示“匹配分析 + 拟修改点 + 风险提示”，用户确认后再生成最终 PDF。

### 强烈建议提供的增强输入

为了生成更准确的简历，用户最好额外提供：

1. 目标岗位名称
   - 例如“AI 产品经理”“数据产品经理”“LLM 应用 PM”。

2. 投递场景
   - 校招 / 社招 / 转岗 / 实习 / 海外 / 猎头。

3. 用户偏好
   - 简历页数：1 页 / 2 页。
   - 语言：中文 / 英文 / 双语。
   - 风格：ATS 优先 / 视觉美观 / 咨询风 / 技术风。

4. 不可修改边界
   - 不允许编造公司、职位、学历、项目。
   - 不允许新增不存在的数据指标。
   - 可以优化表达，但必须保留事实。

5. 经历素材库
   - 如果用户基础简历太短，系统应该允许用户追加“项目素材库”。
   - 例如每个项目的背景、任务、行动、结果、技术栈、指标。

### 系统应该返回什么

不要只返回 PDF。应该返回四类结果：

1. `optimized_resume.pdf`
   - 可直接投递的 PDF。

2. `optimized_resume.md`
   - 可编辑源文件。

3. `resume_analysis_report.md`
   - JD 匹配度报告。
   - 包括命中关键词、缺失关键词、风险点、优化说明。

4. `change_log.json`
   - 结构化修改记录。
   - 每一处修改都标记：原文、改后、原因、对应 JD 条款、是否涉及事实增强。

---

## 3. 技术上最困难的地方

### 难点 1：PDF 简历不是可靠的数据源，也不一定可编辑

当前项目用 `pdfplumber` 从 PDF 提取文本。问题是：

- PDF 是排版结果，不是结构化简历。
- 多栏布局会导致阅读顺序错乱。
- 图标、表格、时间线、分栏可能被错误提取。
- 中文 PDF 可能出现空格、换行、字体编码问题。
- PDF 里的文字可能是真正的 text object，也可能只是扫描图片。

这里要区分三类 PDF：

1. 文本型 PDF
   - PDF 内部有可提取文字。
   - 可以读取文本、定位文字块、做一定程度的覆盖/替换。
   - 但仍然不是 Word 那种“段落可重排”文档，直接编辑会破坏布局。

2. 图片型/扫描型 PDF
   - 每页本质上是一张图片。
   - 没有真正可编辑文本。
   - 只能 OCR 识别文字，再重新生成一份新的简历 PDF。
   - 不能可靠地在原 PDF 上直接替换某一行文字。

3. 混合型 PDF
   - 有些区域是文字，有些区域是图片或矢量元素。
   - 可做局部抽取，但直接编辑仍然风险很高。

产品策略建议：

- 不要把“直接编辑原 PDF”作为默认路线。
- 更稳的路线是“参考原 PDF 的视觉风格，生成一份新的 PDF”。
- 如果用户提供的是文本型 PDF，可以抽取文本和布局信息，用来还原模板。
- 如果用户提供的是图片型 PDF，只能 OCR + 重新排版，不能承诺原位编辑。
- 最佳长期方案：用户维护一份结构化主简历 JSON/Markdown，PDF 只是输出。

### 难点 2：JD 解析要结构化，不应只把全文丢给 LLM

JD 至少应解析成：

- 岗位标题
- 核心职责
- 必备技能
- 加分技能
- 行业/业务关键词
- 经验年限
- 工具/方法论
- 隐含偏好，例如“增长”“数据驱动”“跨部门协作”

否则系统无法稳定判断“哪些经历最相关”。

### 难点 3：不能编造经历，但 LLM 天然会美化过度

这是产品可信度的核心风险。

需要做三层控制：

1. Prompt 约束：禁止虚构事实。
2. 结构约束：只能从用户 Resume IR 的事实字段中取材料。
3. Diff 审计：每个新增数字、工具、项目名、成果指标都必须能追溯到原始简历或用户补充素材。

如果无法追溯，必须标记为“需要用户确认”，不能直接进入最终 PDF。

### 难点 4：ATS 优化和人类可读性之间有冲突

ATS 需要关键词完整、结构清晰、少图形化。
人类面试官需要重点突出、语言自然、不要堆关键词。

所以系统应该有模式选择：

- ATS 模式：关键词覆盖、标准标题、简洁排版。
- 人读模式：表达更自然，突出业务影响。
- 平衡模式：默认。

### 难点 5：PDF 生成质量和一页控制

简历 PDF 最难的是：

- 一页/两页控制。
- 中文字体和英文混排。
- 项目描述长度控制。
- 页边距、行高、字号。
- 长链接、长技能列表溢出。

当前 WeasyPrint + HTML 模板可行，但需要增加：

- PDF 预检：页数检测。
- 过长内容自动压缩。
- 模板约束：ATS 模板、现代模板、紧凑模板。

### 难点 6：LLM 输出不可控，需要结构化输出

当前 `AIClient.analyze_jd_match()` 让模型返回自由文本，然后用 `'# '` 粗糙切分 suggestions 和 optimized resume。
这会不稳定。

建议改成严格 JSON 输出：

```json
{
  "match_report": {
    "score": 82,
    "matched_keywords": [],
    "missing_keywords": [],
    "risks": [],
    "recommendations": []
  },
  "change_plan": [
    {
      "section": "项目经验",
      "original": "...",
      "revised": "...",
      "reason": "匹配 JD 中的数据分析要求",
      "source_evidence": "原简历第 X 段",
      "needs_user_confirmation": false
    }
  ],
  "optimized_resume_markdown": "..."
}
```

---

## 4. 推荐的产品操作流程

### 流程 A：交互式 CLI / TUI

适合当前项目快速落地。

用户操作：

1. 运行：`python scripts/optimize_pdf_resume.py`
2. 选择模型配置。
3. 上传/输入基础简历。
4. 粘贴/上传 JD。
5. 选择简历目标：ATS / 人读 / 平衡。
6. 系统展示分析报告：
   - 匹配度
   - JD 关键词
   - 简历命中点
   - 缺失点
   - 拟修改列表
7. 用户确认：
   - 全部接受
   - 逐条接受/拒绝
   - 补充素材后重新生成
8. 系统输出 PDF + Markdown + 报告 + 修改记录。

### 流程 B：Web 应用

适合产品化。

页面结构：

1. 首页：上传简历 + 粘贴 JD。
2. 分析页：匹配报告 + 修改建议。
3. 编辑页：左侧原简历，右侧优化简历，中间 diff。
4. 预览页：PDF 预览 + 模板切换。
5. 导出页：PDF / Markdown / JSON 下载。

---

## 5. 两套系统：TDD 与 BDD

你说的“两套系统”可以这样定义：

### TDD：保证底层功能正确

TDD 面向开发者，测试对象是函数、模块、数据转换。

它回答：

- PDF 文本能不能提取？
- JD 能不能解析成结构化字段？
- Resume IR 是否符合 schema？
- LLM JSON 输出能不能被校验？
- Markdown 能不能生成 PDF？
- 页数检测是否准确？
- 禁止编造规则是否能拦截新增事实？

建议 TDD 覆盖模块：

1. `core/jd_parser.py`
   - 输入 JD 文本，输出结构化 JDProfile。

2. `core/resume_ir.py`
   - 定义 ResumeIR、Experience、Project、Skill 等 schema。

3. `core/fact_guard.py`
   - 检查优化稿是否新增了未授权事实。

4. `core/change_plan.py`
   - 管理修改计划和用户确认状态。

5. `core/pdf_preflight.py`
   - 检查 PDF 页数、文件大小、文本可提取性。

6. `core/render_pipeline.py`
   - ResumeIR / Markdown → HTML → PDF。

TDD 的基本原则：

- 先写失败测试。
- 再写最小实现。
- 每个行为一个测试。
- LLM 调用不能直接进单元测试；要用固定 fixture 或 fake client。

### BDD：保证用户流程符合预期

BDD 面向产品行为，测试对象是完整用户场景。

它回答：

- 用户只有简历、没有 JD 时，系统是否提示上传 JD？
- 用户提供简历 + JD 后，系统是否先展示分析报告而不是直接生成？
- 用户拒绝某条修改后，最终 PDF 是否不包含这条修改？
- 用户要求“一页简历”时，系统是否在超过一页时提示压缩或换模板？
- 用户基础简历缺少某个 JD 关键词时，系统是否提示“缺失”，而不是编造？

BDD 可以使用 Gherkin 风格：

```gherkin
Feature: 根据 JD 生成定制简历

Scenario: 用户提供基础简历和 JD 后，系统先生成修改计划
  Given 用户上传了一份基础简历
  And 用户提供了一份 AI 产品经理 JD
  When 用户点击“分析匹配度”
  Then 系统展示匹配度报告
  And 系统展示拟修改列表
  And 系统不会直接生成最终 PDF

Scenario: 系统不能编造用户没有提供的指标
  Given 用户简历中没有“提升转化率 30%”这个事实
  And JD 强调增长转化能力
  When 系统生成修改计划
  Then 修改计划不能直接加入“提升转化率 30%”
  And 系统应提示用户补充相关数据
```

BDD 的价值：

- 防止产品流程跑偏。
- 让“用户到底需要提供什么”变成可测试规则。
- 让开发不是只做功能，而是做完整体验。

---

## 6. 推荐架构

建议把系统拆成 7 层：

1. Input Layer
   - 负责接收 PDF/Markdown/DOCX/JD 文本。

2. Parsing Layer
   - PDF/Markdown → ResumeIR
   - JD 文本 → JDProfile

3. Matching Layer
   - JDProfile × ResumeIR → MatchReport

4. Planning Layer
   - MatchReport → ChangePlan
   - 标记每条修改是否需要用户确认。

5. Guard Layer
   - FactGuard 检查是否编造事实。
   - PrivacyGuard 检查敏感信息。

6. Rendering Layer
   - Confirmed ChangePlan → Optimized Resume Markdown/HTML/PDF

7. Product Layer
   - CLI/TUI/Web API
   - 管理用户确认、文件输出、历史版本。

---

## 7. MVP 范围建议

不要一开始做太大。第一版建议只做：

### 必做

1. 支持 PDF 简历输入。
2. 支持 JD `.txt` 输入。
3. 输出结构化匹配报告。
4. 输出修改计划，而不是直接盲改。
5. 用户确认后生成 Markdown + PDF。
6. 保存修改记录。
7. 至少一个 ATS-friendly 模板。

### 暂不做

1. 不做账号系统。
2. 不做在线支付。
3. 不做复杂 Web 编辑器。
4. 不做多轮求职管理系统。
5. 不做自动投递。
6. 不做花哨模板市场。

---

## 8. 接下来第一阶段开发顺序

### Phase 1：数据结构和测试底座

1. 新建 `tests/`。
2. 新建 `core/resume_ir.py`。
3. 新建 `core/jd_parser.py`。
4. 新建 `core/fact_guard.py`。
5. 建立 fixture：样例简历、样例 JD、样例 LLM 输出。

### Phase 2：结构化 LLM 输出

1. 改造 `AIClient.analyze_jd_match()`。
2. 从自由文本输出改为 JSON 输出。
3. 增加 JSON schema 校验。
4. LLM 输出失败时给出可恢复错误。

### Phase 3：修改计划和确认流程

1. 新增 ChangePlan 数据结构。
2. CLI/TUI 展示每条修改。
3. 用户可以接受/拒绝。
4. 只有确认后的修改进入最终简历。

### Phase 4：PDF 质量控制

1. 生成 PDF 后检查页数。
2. 检查文本可提取性。
3. 超过页数时提示压缩或换模板。

### Phase 5：BDD 场景测试

1. 写 `features/jd_resume_generation.feature`。
2. 覆盖缺材料、确认流程、防编造、一页约束等场景。

---

## 9. 当前代码的关键改造点

### `core/ai_client.py`

当前问题：

- Prompt 输出是自由文本。
- `'# '` 切分很脆弱。
- 无 JSON schema。
- 无事实追踪。

改造方向：

- 新增 `generate_change_plan(jd_profile, resume_ir)`。
- 返回结构化 JSON。
- LLM 调用和解析分离，便于 TDD。

### `scripts/optimize_pdf_resume.py`

当前问题：

- 读取 PDF → AI 优化 → 直接生成 PDF。
- 用户没有机会逐条确认修改。
- 中间状态没有结构化保存。

改造方向：

- 拆成 analyze / review / render 三步。
- 默认必须经过 review。
- `--no-interactive` 下也要有 `--auto-approve` 才能直接生成。

### `core/pdf_generator.py`

当前问题：

- 只负责生成，没有质量预检。

改造方向：

- 输出 PDF 后跑 preflight。
- 返回页数、文件大小、可提取文本长度。

---

## 10. 一句话结论

这个项目技术上可行，但真正难点不在“生成 PDF”，而在：

1. 把简历和 JD 结构化。
2. 防止 LLM 编造事实。
3. 让用户确认每一类关键修改。
4. 控制 PDF 版式和页数。
5. 用 TDD 保证底层模块正确，用 BDD 保证用户流程正确。

建议下一步先做“结构化 IR + JD 解析 + 修改计划 + 防编造守卫”，然后再继续优化 PDF 模板和 Web 体验。
