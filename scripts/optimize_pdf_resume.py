#!/usr/bin/env python3
"""
JD-智能简历优化器
分析职位描述并优化简历以获得更好的 ATS 匹配度。
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import Config, get_logger, PDFGenerator, AIClient
from core.tui import (
    console, welcome_banner, step_progress, file_input_prompt,
    confirm_dialog, success_message, error_message, warning_message, info_message,
    display_results, display_files_summary, progress_spinner
)
from rich.panel import Panel
from rich import box
import pdfplumber

logger = get_logger('optimize_pdf_resume')


def extract_text_from_pdf(pdf_path: str) -> str:
    """从 PDF 简历中提取文本内容。"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def interactive_mode():
    """交互式引导模式进行简历优化。"""
    welcome_banner()
    info_message("简历优化工具 - 交互模式")
    console.print()

    config = Config()

    from core.tui import get_text_input

    # 1. 选择大模型来源
    provider = get_text_input("🤖 请输入 LLM 供应商", config.llm_provider)
    model = get_text_input("🧠 请输入模型名", config.llm_model)
    base_url = get_text_input("🌐 请输入 Base URL（OpenAI-compatible）", config.llm_base_url)
    api_key = get_text_input("🔑 API Key 覆盖（留空使用环境变量）", "")
    llm_overrides = _compact_llm_overrides(provider, model, base_url, api_key)

    if not (api_key.strip() or config.llm_api_key):
        error_message("请先配置 LLM_API_KEY 或对应供应商的 API Key 环境变量")
        console.print("   [cyan]export LLM_API_KEY=\"your_api_key\"[/cyan]")
        sys.exit(1)

    # 2. 获取简历 PDF 路径
    resume_path = file_input_prompt(
        "📄 请输入 PDF 简历文件路径",
        file_type="PDF 简历",
        default_ext=".pdf",
        must_exist=True
    )

    # 3. 获取 JD 文件路径
    jd_path = file_input_prompt(
        "📋 请输入职位描述文本文件路径",
        file_type="职位描述",
        default_ext=".txt",
        must_exist=True
    )

    # 4. 获取输出文件名
    output_name = get_text_input("📤 请输入输出 PDF 文件名", "optimized_resume.pdf")
    if not output_name.strip():
        output_name = "optimized_resume.pdf"

    # 5. 确认
    console.print()
    display_results("确认信息", {
        "简历": resume_path,
        "职位描述": jd_path,
        "输出文件": output_name,
        "LLM": f"{provider} / {model}"
    })

    if not confirm_dialog("开始优化？", default=False):
        warning_message("操作已取消")
        sys.exit(0)

    return resume_path, jd_path, output_name, llm_overrides


def process_resume_workflow(
    pdf_resume_path: str,
    jd_path: str,
    output_name: str = "optimized_resume.pdf",
    llm_overrides=None,
):
    """
    简历优化的完整工作流程。

    Args:
        pdf_resume_path: PDF 简历路径。
        jd_path: 职位描述文件路径。
        output_name: 输出 PDF 文件名。
    """
    config = Config()

    step_progress(1, 4, "读取文件")
    info_message("正在读取 PDF 简历和职位描述...")

    # 读取简历内容
    resume_text = extract_text_from_pdf(pdf_resume_path)

    # 读取 JD 内容
    with open(jd_path, 'r', encoding='utf-8') as f:
        jd_text = f.read()

    step_progress(2, 4, "AI 分析")
    with progress_spinner("AI 正在分析职位匹配度并优化简历..."):
        ai_client = AIClient(**(llm_overrides or {}))
        suggestions, optimized_resume = ai_client.analyze_jd_match(jd_text, resume_text)

    # 保存分析报告
    report_path = os.path.join(config.output_dir, "resume_analysis_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 简历匹配度分析报告\n\n")
        f.write(suggestions)
        f.write("\n\n## 优化后的简历内容\n\n")
        f.write(optimized_resume)
    logger.info(f"分析报告已保存: {report_path}")
    info_message(f"分析报告已保存: {report_path}")

    step_progress(3, 4, "生成 PDF")
    info_message("正在生成优化后的 PDF 简历...")

    generator = PDFGenerator()
    output_path = generator.generate(optimized_resume, output_name)

    step_progress(4, 4, "完成")

    # 显示摘要
    display_files_summary([
        {"name": "优化后的简历 PDF", "path": output_path},
        {"name": "分析报告", "path": report_path}
    ])

    console.print()
    success_message("简历优化完成！")
    console.print()
    console.print("[bold yellow]📋 优化建议:[/bold yellow]")
    console.print(Panel(suggestions, box=box.SIMPLE))

    return output_path, suggestions


def main():
    import argparse

    parser = argparse.ArgumentParser(description='JD-智能简历优化器')
    parser.add_argument('resume_pdf', nargs='?', help='输入 PDF 简历文件路径')
    parser.add_argument('jd', nargs='?', help='职位描述文本文件路径')
    parser.add_argument('-o', '--output', default='optimized_resume.pdf', help='输出 PDF 文件名')
    parser.add_argument('--no-interactive', action='store_true', help='禁用交互模式')
    parser.add_argument('--provider', help='LLM 供应商，例如 openai/deepseek/siliconflow/ark/custom')
    parser.add_argument('--model', help='模型名')
    parser.add_argument('--base-url', help='OpenAI-compatible Base URL')
    parser.add_argument('--api-key', help='API Key 覆盖；未提供时读取环境变量')

    args = parser.parse_args()

    config = Config()
    llm_overrides = _compact_llm_overrides(args.provider, args.model, args.base_url, args.api_key)
    ai_client = AIClient(**llm_overrides)

    if args.no_interactive:
        # 非交互模式，严格检查参数
        if not args.resume_pdf or not args.jd:
            error_message("非交互模式需要提供简历和职位描述路径")
            console.print("用法: python optimize_pdf_resume.py resume.pdf jd.txt [-o output.pdf]")
            sys.exit(1)

        if not ai_client.is_available():
            error_message("请配置 LLM_API_KEY 或对应供应商的 API Key")
            sys.exit(1)

        welcome_banner()
        output_path, suggestions = process_resume_workflow(
            args.resume_pdf, args.jd, args.output, llm_overrides
        )

    else:
        # 交互模式
        if not args.resume_pdf or not args.jd:
            resume_path, jd_path, output_name, llm_overrides = interactive_mode()
            output_path, suggestions = process_resume_workflow(
                resume_path, jd_path, output_name, llm_overrides
            )
        else:
            # 有参数，请求确认
            display_results("确认信息", {
                "简历": args.resume_pdf,
                "职位描述": args.jd,
                "输出文件": args.output,
                "LLM": f"{ai_client.provider} / {ai_client.model}"
            })

            if confirm_dialog("开始优化？", default=True):
                output_path, suggestions = process_resume_workflow(
                    args.resume_pdf, args.jd, args.output, llm_overrides
                )
            else:
                warning_message("操作已取消")
                sys.exit(0)


def _compact_llm_overrides(provider=None, model=None, base_url=None, api_key=None):
    overrides = {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
    }
    return {key: value for key, value in overrides.items() if value}


if __name__ == "__main__":
    main()
