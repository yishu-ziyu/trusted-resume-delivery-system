# 简历PDF自动生成器
一个AI驱动的简历优化和PDF生成工具，帮你快速生成专业级简历。

## ✨ 核心功能
### 🎯 完整工作流（完全自动化）
`用户上传PDF简历 + 招聘JD → AI智能分析匹配度 → 自动优化简历内容 → 直接输出优化后的PDF`

1. **PDF直接读取**：支持直接上传PDF格式简历，无需手动转格式
2. **JD智能匹配**：AI深度分析招聘JD要求，精准匹配简历关键词
3. **ATS优化**：自动优化简历内容，最大化通过ATS筛选概率
4. **匹配度报告**：生成详细的匹配度分析报告和优化建议
5. **一键生成PDF**：自动排版生成高质量PDF，无需手动调整格式
6. **多模板支持**：内置多款专业简历模板，支持自定义样式

## 🚀 使用方法

### ⚠️  交互原则（严格执行）
> 系统**绝对不会预判用户意图**，所有操作必须等待用户明确确认信号：
> 1. 缺少任何必要材料（PDF简历、招聘JD）时，自动提示用户上传，不推进下一步
> 2. 所有材料齐全后，必须等待用户最终确认才会执行优化
> 3. 任何时候用户取消，立即终止流程

### 🔥 最常用：交互式引导（推荐）
无需记参数，直接运行脚本即可，系统会一步步提示你上传材料：
```bash
# 配置OpenAI密钥
export OPENAI_API_KEY="你的OpenAI API密钥"

# 直接运行，跟随引导操作
python scripts/optimize_pdf_resume.py
```

### ⚡ 命令行模式（适合自动化）
```bash
python scripts/optimize_pdf_resume.py 你的简历.pdf 招聘JD.txt -o 优化后简历.pdf
```
即使提供了所有参数，系统也会再次确认后才执行

### 📝 基础用法：Markdown生成PDF
1. 把你的简历内容保存为`input/resume.md`（markdown格式）
2. 运行生成脚本：`python scripts/generate.py input/resume.md`
3. 生成的PDF会自动保存到`output/`目录

### 🧠 开启AI内容优化
```bash
python scripts/generate.py input/resume.md --optimize --jd 招聘JD.txt
```

## 📁 项目结构
```
resume-pdf-builder/
├── templates/      # 简历模板（HTML/CSS格式）
├── scripts/        # 核心脚本
├── input/          # 输入的简历源文件
├── examples/       # 示例简历
├── output/         # 生成的PDF输出
└── README.md
```

## 🛠️ 依赖安装
```bash
pip install markdown weasyprint jinja2 openai PyPDF2 pdfrw
```
