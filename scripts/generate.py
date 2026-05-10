#!/usr/bin/env python3
"""
简历 PDF 生成器
从 Markdown 文件生成专业的 PDF 简历。
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import Config, get_logger, PDFGenerator, AIClient
from core.tui import (
    console, welcome_banner, step_progress, file_input_prompt,
    confirm_dialog, success_message, error_message, warning_message, info_message,
    display_results, progress_spinner
)

logger = get_logger('generate')


def main():
    import argparse

    parser = argparse.ArgumentParser(description='简历 PDF 生成器')
    parser.add_argument('input', nargs='?', help='输入 Markdown 简历文件路径')
    parser.add_argument('-o', '--output', default='resume.pdf', help='输出 PDF 文件名')
    parser.add_argument('-t', '--template', default=None, help='使用的模板文件')
    parser.add_argument('--optimize', action='store_true', help='启用 AI 优化')
    parser.add_argument('--jd', help='用于 AI 优化的职位描述文件路径')
    parser.add_argument('--provider', help='LLM 供应商，例如 openai/deepseek/siliconflow/ark/custom')
    parser.add_argument('--model', help='模型名')
    parser.add_argument('--base-url', help='OpenAI-compatible Base URL')
    parser.add_argument('--api-key', help='API Key 覆盖；未提供时读取环境变量')

    args = parser.parse_args()
    llm_overrides = _compact_llm_overrides(args.provider, args.model, args.base_url, args.api_key)

    welcome_banner()

    # 读取 JD 内容（如果提供）
    jd_content = ""
    if args.jd and os.path.exists(args.jd):
        with open(args.jd, 'r', encoding='utf-8') as f:
            jd_content = f.read()

    # 获取输入文件路径（如果没有提供则交互式获取）
    if not args.input:
        args.input = file_input_prompt(
            "📄 请输入 Markdown 简历文件路径",
            file_type="markdown",
            default_ext=".md",
            must_exist=True
        )

    # 读取 Markdown 内容
    if not os.path.exists(args.input):
        error_message(f"输入文件不存在: {args.input}")
        sys.exit(1)

    with open(args.input, 'r', encoding='utf-8') as f:
        content = f.read()

    # 如果请求了 AI 优化
    if args.optimize:
        step_progress(1, 3, "AI 简历优化")
        info_message("正在启动 AI 简历优化...")

        ai_client = AIClient(**llm_overrides)

        if ai_client.is_available():
            with progress_spinner("正在优化简历内容..."):
                content = ai_client.optimize_resume(content, jd_content)

            optimized_path = os.path.join(Config().output_dir, "optimized_resume.md")
            with open(optimized_path, 'w', encoding='utf-8') as f:
                f.write(content)
            success_message(f"优化后的简历已保存至: {optimized_path}")
        else:
            warning_message("未配置 LLM API Key，跳过优化")

    # 生成 PDF
    step_progress(2 if args.optimize else 1, 3, "生成 PDF")
    info_message("正在生成简历 PDF...")

    generator = PDFGenerator(template_name=args.template)
    output_path = generator.generate(content, output_name=args.output)

    step_progress(3, 3, "完成")
    success_message(f"简历 PDF 已生成: {output_path}")

    display_results("生成完成", {
        "输出路径": output_path,
        "使用模板": args.template or Config().default_template,
        "文件大小": f"{os.path.getsize(output_path):,} 字节"
    })


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
