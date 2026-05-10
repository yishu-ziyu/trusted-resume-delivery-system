"""
Resume information extractor.
Extracts structured data from markdown resumes.
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ResumeData:
    """Structured resume data."""
    name: str
    phone: str = ''
    email: str = ''
    location: str = ''
    github: str = ''
    linkedin: str = ''
    content: str = ''
    raw_text: str = ''


class ResumeExtractor:
    """Extracts structured information from resume text."""

    # Regex patterns
    EMAIL_PATTERN = r'[\w\.-]+@[\w\.-]+\.\w+'
    PHONE_PATTERNS = [
        r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'(\+?\d{1,3}[-.\s]?)?\(?\d{2,3}\)?[-.\s]?\d{4,5}[-.\s]?\d{4}',
    ]
    GITHUB_PATTERN = r'github\.com/[\w\-\.]+'
    LINKEDIN_PATTERN = r'linkedin\.com/in/[\w\-\.]+'

    @classmethod
    def extract(cls, markdown_content: str) -> ResumeData:
        """
        Extract structured data from markdown resume content.

        Args:
            markdown_content: Raw markdown content of the resume.

        Returns:
            ResumeData object with extracted information.
        """
        lines = markdown_content.split('\n')

        # Extract name (usually first # heading)
        name = cls._extract_name(lines)

        # Extract contact info
        phone = cls._extract_phone(lines)
        email = cls._extract_email(lines)
        location = cls._extract_location(lines)
        github = cls._extract_github(lines)
        linkedin = cls._extract_linkedin(lines)

        # Get content after headers (skip first few lines that are name/contact)
        content = cls._extract_main_content(lines)

        return ResumeData(
            name=name,
            phone=phone,
            email=email,
            location=location,
            github=github,
            linkedin=linkedin,
            content=content,
            raw_text=markdown_content
        )

    @classmethod
    def _extract_name(cls, lines: list) -> str:
        """Extract name from first heading."""
        for line in lines[:5]:
            if line.startswith('#'):
                return line.lstrip('#').strip()
        return '简历'

    @classmethod
    def _extract_phone(cls, lines: list) -> str:
        """Extract phone number from lines."""
        for line in lines[:15]:
            if any(kw in line.lower() for kw in ['电话', '手机', 'tel', 'phone']):
                # Try to extract after colon
                if ':' in line or '：' in line:
                    parts = re.split(r'[:：]', line, 1)
                    if len(parts) > 1:
                        return parts[1].strip()
            # Also try regex on the whole line
            for pattern in cls.PHONE_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    return match.group()
        return ''

    @classmethod
    def _extract_email(cls, lines: list) -> str:
        """Extract email from lines."""
        for line in lines[:15]:
            if any(kw in line.lower() for kw in ['邮箱', 'email', 'mail']):
                if ':' in line or '：' in line:
                    parts = re.split(r'[:：]', line, 1)
                    if len(parts) > 1:
                        return parts[1].strip()
            # Also try regex
            match = re.search(cls.EMAIL_PATTERN, line)
            if match:
                return match.group()
        return ''

    @classmethod
    def _extract_location(cls, lines: list) -> str:
        """Extract location from lines."""
        for line in lines[:15]:
            if any(kw in line for kw in ['地址', '所在地', 'location', '城市']):
                if ':' in line or '：' in line:
                    parts = re.split(r'[:：]', line, 1)
                    if len(parts) > 1:
                        return parts[1].strip()
        return ''

    @classmethod
    def _extract_github(cls, lines: list) -> str:
        """Extract GitHub URL from lines."""
        for line in lines[:15]:
            if 'github' in line.lower():
                match = re.search(cls.GITHUB_PATTERN, line.lower())
                if match:
                    return f"https://{match.group()}"
                if ':' in line or '：' in line:
                    parts = re.split(r'[:：]', line, 1)
                    if len(parts) > 1:
                        return parts[1].strip()
        return ''

    @classmethod
    def _extract_linkedin(cls, lines: list) -> str:
        """Extract LinkedIn URL from lines."""
        for line in lines[:15]:
            if 'linkedin' in line.lower():
                match = re.search(cls.LINKEDIN_PATTERN, line.lower())
                if match:
                    return f"https://{match.group()}"
        return ''

    @classmethod
    def _extract_main_content(cls, lines: list) -> str:
        """Extract main content after contact info (skip first ~10 lines)."""
        # Skip initial lines that contain name/contact info
        skip_count = 0
        for i, line in enumerate(lines[:12]):
            if any(kw in line.lower() for kw in ['电话', '手机', '邮箱', 'email', '地址', 'github', 'linkedin', '电话']):
                skip_count = i + 1

        return '\n'.join(lines[skip_count:])
