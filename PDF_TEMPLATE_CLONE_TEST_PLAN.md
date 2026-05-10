# PDF 简历模板克隆压力测试方案

> 目的：验证“基于一份成型 PDF 简历，在完全替换内容后，是否仍能输出一份版式高度相似的新 PDF”。

这个测试不是为了马上做完整产品，而是为了回答一个关键产品问题：

**我们到底能不能把用户已有的好看简历模板复用起来？**

如果这个测试过不了，就说明产品不应该主打“原模板复刻”，而应该主打“ATS 稳定模板重排”。

---

## 1. 核心判断

你的判断是对的：

即使我们有 PDF 解析、OCR、布局分析、HTML/Typst 渲染这些技术，**做出一份和原简历一样好看的模板依然很难**。

原因不是 AI 不够强，而是 PDF 本身不是可编辑源文件。PDF 只告诉我们“页面上某个坐标画了什么”，不告诉我们：

- 这是标题还是正文？
- 这是一个项目块还是两段独立文本？
- 哪些元素应该一起移动？
- 内容变长后应该怎么换行？
- 两栏之间如何自动平衡？
- 某个图标和文字是否属于同一条信息？

所以必须用测试来判断“这条路线可不可产品化”。

---

## 2. 测试定义

### 测试名称

PDF Template Clone Stress Test

### 测试输入

用户提供：

1. 一份成型 PDF 简历
   - 最好是用户觉得“模板好看、想保留”的那种。
   - 可以是 1 页或 2 页。

2. 一套完全不相干的新内容
   - 为了测试模板复刻能力，新内容故意和原简历无关。
   - 例如把产品经理简历改成咖啡店店长、篮球教练、图书管理员、宠物医院运营等。

### 测试输出

系统输出：

1. `diagnosis.json`
   - PDF 是否文本型
   - 是否扫描型
   - 文本提取质量
   - 页面尺寸
   - 字体列表
   - 主要字号
   - 颜色列表
   - 文本块数量
   - 图片/矢量元素数量
   - 是否多栏
   - 预估可复刻等级

2. `layout_spec.json`
   - 页面尺寸、边距、栏结构、文本块、字体、颜色、坐标。

3. `replacement_resume.md`
   - 完全替换后的新简历内容。

4. `cloned_resume.pdf`
   - 使用原模板风格重新生成的新 PDF。

5. `clone_report.md`
   - 自动评估报告。
   - 包括版式相似度、页数变化、溢出情况、文字可读性、人工复核点。

---

## 3. 这不是“直接编辑 PDF”测试

这个测试不应该叫“PDF 编辑测试”，而应该叫“模板克隆 + 重新渲染测试”。

原因：

- 原位编辑 PDF 只能处理非常简单的短文本替换。
- 简历内容一旦变长或变短，就需要重排。
- PDF 没有 Word 那种段落流和自动布局能力。

所以正确路线是：

```text
原 PDF
→ 诊断可编辑/可复刻程度
→ 抽取布局和样式
→ 生成 Layout Spec
→ 将新内容映射到原来的版式槽位
→ 重新渲染新 PDF
→ 自动评估相似度和可读性
```

---

## 4. BDD：用户行为验收标准

BDD 负责回答：这个能力从用户视角是否成立？

### Feature: 复用原 PDF 简历模板生成新简历

#### Scenario 1: 文本型 PDF 可以进入模板复刻流程

```gherkin
Given 用户上传了一份可复制文字的 PDF 简历
When 系统执行 PDF 诊断
Then 系统应判断该 PDF 为 text_based
And 系统应提取文本块、字体、字号、颜色和坐标
And 系统应给出“可尝试原风格复刻”的建议
```

#### Scenario 2: 图片型 PDF 不能承诺原位编辑

```gherkin
Given 用户上传了一份扫描版 PDF 简历
When 系统执行 PDF 诊断
Then 系统应判断该 PDF 为 image_based 或 scanned
And 系统应提示“不能直接编辑原 PDF”
And 系统应提供“OCR 后重建新版 PDF”的选项
```

#### Scenario 3: 替换成不相关内容后仍保持原模板风格

```gherkin
Given 用户上传了一份成型 PDF 简历
And 用户提供了一套完全不相关的新简历内容
When 系统生成 cloned_resume.pdf
Then 新 PDF 的页面尺寸应与原 PDF 一致
And 新 PDF 的主字体、字号、颜色应接近原 PDF
And 新 PDF 的主要区块位置应接近原 PDF
And 新 PDF 不应出现文本重叠
And 新 PDF 不应出现页面溢出
```

#### Scenario 4: 内容过长时系统不能硬塞进模板

```gherkin
Given 原 PDF 是一页简历
And 替换内容明显超过一页容量
When 系统尝试生成 cloned_resume.pdf
Then 系统应检测到内容溢出风险
And 系统应提供压缩内容、缩小字号、改为两页、切换模板四个选项
And 系统不能直接输出一份严重重叠的 PDF
```

#### Scenario 5: 复刻失败时系统要诚实降级

```gherkin
Given 用户上传的 PDF 布局复杂，包含大量图形、图标、图片和多栏
When 系统完成诊断
Then 系统应给出低复刻置信度
And 系统应推荐使用 ATS 标准模板重排
And 系统不能承诺“完全一样模板”
```

---

## 5. TDD：底层技术测试标准

TDD 负责回答：每个底层模块是否可验证？

### Module 1: PDF 诊断器 `core/pdf_diagnoser.py`

目标：判断 PDF 类型和可复刻程度。

测试点：

- `test_detects_text_based_pdf_when_text_blocks_exist`
- `test_detects_scanned_pdf_when_page_has_large_image_and_no_text`
- `test_reports_page_size_and_page_count`
- `test_reports_font_size_color_statistics`
- `test_assigns_cloneability_score`

输出结构建议：

```json
{
  "pdf_type": "text_based",
  "page_count": 1,
  "page_size": {"width": 595.28, "height": 841.89},
  "text_block_count": 86,
  "image_count": 1,
  "font_families": ["PingFangSC", "Helvetica"],
  "dominant_font_size": 10.5,
  "is_multi_column": true,
  "cloneability_score": 78,
  "recommended_route": "original_style_regeneration"
}
```

### Module 2: Layout Spec 提取器 `core/layout_extractor.py`

目标：把 PDF 页面转成可渲染布局描述。

测试点：

- `test_extracts_text_spans_with_coordinates`
- `test_normalizes_coordinates_to_top_left_origin`
- `test_groups_spans_into_lines`
- `test_groups_lines_into_sections`
- `test_detects_left_and_right_columns`
- `test_extracts_style_tokens`

关键注意：

- PyMuPDF 坐标和 PDF 坐标容易混淆。
- 内部统一使用 top-left 坐标系。

### Module 3: Content Slot Mapper `core/content_mapper.py`

目标：把新简历内容映射到原模板槽位。

测试点：

- `test_maps_name_to_header_slot`
- `test_maps_contact_info_to_contact_slot`
- `test_maps_experience_items_to_experience_section`
- `test_preserves_section_order_from_template`
- `test_detects_unmapped_content`

### Module 4: Overflow Detector `core/overflow_detector.py`

目标：检测文字是否超出槽位、页面或发生重叠。

测试点：

- `test_detects_text_block_overflow`
- `test_detects_vertical_overlap_between_blocks`
- `test_detects_page_overflow`
- `test_suggests_compression_when_overflow_is_small`
- `test_suggests_two_pages_when_overflow_is_large`

### Module 5: Renderer `core/template_renderer.py`

目标：根据 Layout Spec + New Content 重新渲染 PDF。

测试点：

- `test_renders_pdf_with_same_page_size`
- `test_renders_header_at_expected_position`
- `test_renders_section_titles_with_expected_style`
- `test_outputs_text_extractable_pdf`
- `test_does_not_render_empty_required_sections`

### Module 6: Similarity Evaluator `core/similarity_evaluator.py`

目标：自动评估新 PDF 和原 PDF 是否“足够像”。

测试点：

- `test_page_size_similarity`
- `test_font_similarity`
- `test_color_similarity`
- `test_block_position_similarity`
- `test_visual_snapshot_similarity_if_available`

评分建议：

```json
{
  "page_size_score": 100,
  "font_score": 82,
  "color_score": 90,
  "block_position_score": 76,
  "no_overlap": true,
  "page_overflow": false,
  "overall_score": 84
}
```

---

## 6. 第一次实验的最小闭环

第一次测试不要做太复杂，只做一页 PDF。

### 输入

- `tests/fixtures/original_resume.pdf`
- `tests/fixtures/replacement_resume.md`

### 输出

- `output/clone_test/diagnosis.json`
- `output/clone_test/layout_spec.json`
- `output/clone_test/cloned_resume.pdf`
- `output/clone_test/clone_report.md`

### 验收标准

第一轮不要追求 100% 一样。先用下面标准：

1. 页面尺寸一致。
2. 新 PDF 可复制文字。
3. 主色调接近。
4. 标题、联系方式、主要 section 的位置接近。
5. 没有明显文字重叠。
6. 没有内容超出页面。
7. 人眼看起来像同一个模板家族。

如果这七条都能满足，再提高要求。

---

## 7. 推荐项目目录结构

```text
core/
  pdf_diagnoser.py
  layout_extractor.py
  content_mapper.py
  overflow_detector.py
  template_renderer.py
  similarity_evaluator.py

tests/
  fixtures/
    original_resume.pdf
    replacement_resume.md
  test_pdf_diagnoser.py
  test_layout_extractor.py
  test_content_mapper.py
  test_overflow_detector.py
  test_template_renderer.py
  test_similarity_evaluator.py

features/
  pdf_template_clone.feature

scripts/
  clone_resume_template.py
```

---

## 8. 实验成功/失败如何决策

### 如果实验成功

说明产品可以主打：

“上传你的原简历 PDF，系统保留原模板风格，为不同 JD 生成定制版本。”

之后开发重点：

- 增强 Layout Spec。
- 增强模板槽位识别。
- 增强 PDF 相似度评估。
- 增加用户确认和微调。

### 如果实验失败

说明产品不要承诺模板复刻。

应该转成：

“上传原简历提取内容，系统使用高质量 ATS 模板重新生成。”

之后开发重点：

- 做几套稳定漂亮的模板。
- 做结构化内容优化。
- 做一页/两页自适应。
- 做 JD 匹配和事实守卫。

---

## 9. 下一步执行方式

用户把一份 PDF 简历放到：

```text
tests/fixtures/original_resume.pdf
```

然后我们准备一份完全不相关的替换内容：

```text
tests/fixtures/replacement_resume.md
```

之后开始第一轮 TDD：

1. 写 `test_pdf_diagnoser.py`。
2. 实现 `core/pdf_diagnoser.py`。
3. 写 `test_layout_extractor.py`。
4. 实现 `core/layout_extractor.py`。
5. 生成第一版 `layout_spec.json`。
6. 再决定是否进入渲染阶段。

这个顺序很重要：先证明 PDF 可诊断、可抽取布局，再谈“复刻模板”。
