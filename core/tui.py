"""
Rich TUI Components for Resume PDF Builder.
Interactive terminal UI using the rich library.
"""

import os
import sys
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align
from rich.text import Text
from rich.theme import Theme

# Custom theme for resume builder
custom_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "bold red",
    "header": "bold cyan",
    "path": "blue",
})

# Global console instance
console = Console(theme=custom_theme)


def welcome_banner() -> None:
    """Display welcome banner for the application."""
    banner_text = Text("""
╔═══════════════════════════════════════════════════════════════╗
║          简历 PDF 生成器 - ATS 智能优化                          ║
║                    AI 驱动的简历优化工具                         ║
╚═══════════════════════════════════════════════════════════════╝
    """.strip(), style="header")

    console.print(banner_text)
    console.print()


def step_progress(current: int, total: int, step_name: str) -> None:
    """
    Display a step progress indicator.

    Args:
        current: Current step number (1-based)
        total: Total number of steps
        step_name: Name of the current step
    """
    steps_icons = ["📄", "📋", "🧠", "✨", "📊"]
    icon = steps_icons[min(current - 1, len(steps_icons) - 1)]

    panel = Panel(
        f"[bold cyan]{icon} 第 {current}/{total} 步:[/bold cyan] [white]{step_name}[/white]",
        box=box.DOUBLE,
        style="cyan"
    )
    console.print(panel)


def file_input_prompt(
    prompt_text: str,
    file_type: str = "文件",
    default_ext: Optional[str] = None,
    must_exist: bool = True
) -> str:
    """
    Prompt user for a file path with validation.

    Args:
        prompt_text: The prompt message
        file_type: Description of file type (e.g., "PDF resume", "JD text")
        default_ext: Expected file extension (e.g., ".pdf", ".txt")
        must_exist: Whether the file must already exist

    Returns:
        Validated file path from user input
    """
    while True:
        path = Prompt.ask(f"[cyan]{prompt_text}[/cyan]")

        if not path.strip():
            console.print("[yellow]⚠ 路径不能为空[/yellow]")
            continue

        path = os.path.expanduser(path.strip())

        if must_exist:
            if not os.path.exists(path):
                console.print(f"[red]✖ 文件不存在: {path}[/red]")
                continue

            if default_ext and not path.endswith(default_ext):
                console.print(f"[red]✖ 请提供 {default_ext} 格式的文件[/red]")
                continue

        return path


def confirm_dialog(message: str, default: bool = False) -> bool:
    """
    Show a confirmation dialog.

    Args:
        message: Confirmation message
        default: Default value (True for yes, False for no)

    Returns:
        User's confirmation choice
    """
    return Confirm.ask(f"[cyan]{message}[/cyan]", default=default)


def success_message(message: str) -> None:
    """Display a success message."""
    console.print(f"[success]✓ {message}[/success]")


def error_message(message: str) -> None:
    """Display an error message."""
    console.print(f"[error]✖ {message}[/error]")


def warning_message(message: str) -> None:
    """Display a warning message."""
    console.print(f"[warning]⚠ {message}[/warning]")


def info_message(message: str) -> None:
    """Display an info message."""
    console.print(f"[info]ℹ {message}[/info]")


def display_results(
    title: str,
    data: Dict[str, Any],
    suggestions: Optional[str] = None
) -> None:
    """
    Display results in a formatted table.

    Args:
        title: Table title
        data: Dictionary of key-value pairs to display
        suggestions: Optional text suggestions to display
    """
    table = Table(title=title, box=box.ROUNDED, show_header=False)

    for key, value in data.items():
        table.add_row(f"[bold cyan]{key}:[/bold cyan]", str(value))

    console.print(table)

    if suggestions:
        console.print()
        console.print("[bold yellow]📋 优化建议:[/bold yellow]")
        console.print(Panel(suggestions, box=box.SIMPLE))


def display_files_summary(files: List[Dict[str, str]]) -> None:
    """
    Display a summary table of files.

    Args:
        files: List of dicts with 'name' and 'path' keys
    """
    table = Table(title="生成的文件", box=box.ROUNDED)
    table.add_column("类型", style="cyan")
    table.add_column("路径", style="path")

    for f in files:
        table.add_row(f.get("name", "文件"), f.get("path", ""))

    console.print(table)


def progress_spinner(message: str):
    """
    Create a progress spinner context manager.

    Args:
        message: Message to display next to spinner

    Returns:
        Progress context manager
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    )


def get_text_input(prompt_text: str, default: Optional[str] = None) -> str:
    """
    Get text input from user.

    Args:
        prompt_text: The prompt message
        default: Default value if user enters nothing

    Returns:
        User's input text
    """
    prompt_str = f"[cyan]{prompt_text}[/cyan]"
    if default:
        prompt_str += f" [{default}]"
    return console.input(prompt_str).strip() or default or ""


def display_markdown(content: str, title: str = "内容") -> None:
    """
    Display markdown-style content in a panel.

    Args:
        content: Content to display
        title: Panel title
    """
    console.print(Panel(content, title=title, box=box.SIMPLE))


def clear_screen() -> None:
    """Clear the console screen."""
    console.clear()


def pause(message: str = "按回车键继续...") -> None:
    """
    Pause and wait for user to press Enter.

    Args:
        message: Message to display
    """
    Prompt.ask(f"[dim]{message}[/dim]")
