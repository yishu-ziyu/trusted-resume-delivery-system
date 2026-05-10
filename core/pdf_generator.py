"""
PDF generator for resume creation.
Converts markdown to PDF using templates and WeasyPrint.
"""

import os
import markdown
from pathlib import Path
from jinja2 import Template
from typing import Optional

from .config import Config
from .resume_extractor import ResumeExtractor, ResumeData
from .logger import get_logger, LoggerMixin


class PDFGenerator(LoggerMixin):
    """Generates PDF resumes from markdown content."""

    def __init__(self, template_name: Optional[str] = None):
        """
        Initialize PDF generator.

        Args:
            template_name: Template filename to use. If None, uses default.
        """
        self.config = Config()
        self.template_name = template_name or self.config.default_template
        self.templates_dir = Path(self.config.templates_dir)
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, markdown_content: str, output_name: str = "resume.pdf",
                 template_name: Optional[str] = None) -> str:
        """
        Generate PDF from markdown content.

        Args:
            markdown_content: Resume content in markdown format.
            output_name: Output filename for the PDF.
            template_name: Optional template override.

        Returns:
            Path to generated PDF file.
        """
        template_name = template_name or self.template_name
        template_path = self.templates_dir / template_name

        if not template_path.exists():
            self.logger.warning(f"Template {template_name} not found, using default")
            template_path = self.templates_dir / self.config.default_template

        # Extract resume data
        resume_data = ResumeExtractor.extract(markdown_content)

        # Convert markdown to HTML
        html_content = markdown.markdown(
            resume_data.content,
            extensions=['tables', 'fenced_code']
        )

        # Load and render template
        with open(template_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())

        rendered_html = template.render(
            name=resume_data.name,
            phone=resume_data.phone,
            email=resume_data.email,
            location=resume_data.location,
            github=resume_data.github,
            linkedin=resume_data.linkedin,
            content=html_content
        )

        # Generate PDF
        output_path = self.output_dir / output_name
        self._render_pdf(rendered_html, output_path)

        self.logger.info(f"PDF generated: {output_path}")
        return str(output_path)

    def generate_from_file(self, markdown_path: str, output_name: str = "resume.pdf",
                          template_name: Optional[str] = None) -> str:
        """
        Generate PDF from a markdown file.

        Args:
            markdown_path: Path to markdown file.
            output_name: Output filename for the PDF.
            template_name: Optional template override.

        Returns:
            Path to generated PDF file.
        """
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.generate(content, output_name, template_name)

    def _render_pdf(self, html_content: str, output_path: Path):
        """
        Render HTML to PDF using WeasyPrint.

        Args:
            html_content: Rendered HTML string.
            output_path: Path where PDF will be saved.
        """
        from weasyprint import HTML

        HTML(string=html_content).write_pdf(str(output_path))

    def list_templates(self) -> list[str]:
        """List available template files."""
        if not self.templates_dir.exists():
            return []

        return [
            f.name for f in self.templates_dir.iterdir()
            if f.suffix in ('.html', '.htm')
        ]
