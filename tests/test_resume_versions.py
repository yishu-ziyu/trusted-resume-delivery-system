from pathlib import Path

import fitz

from scripts.generate_resume_versions import (
    generate_compact_ats_version,
    generate_onepage_photo_striped_version,
    generate_onepage_photo_version,
    generate_onepage_photo_print_version,
    generate_resume_versions,
)

PROJECT = Path(__file__).resolve().parents[1]
RESUME_MD = PROJECT / "output" / "mahaoxuan_ai_pm_resume.md"
PORTRAIT = PROJECT / "output" / "assets" / "original_p1_img5.jpeg"
OUTPUT_DIR = PROJECT / "output" / "versions"


def _pdf_text(path: Path) -> str:
    doc = fitz.open(path)
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


def test_generates_ats_and_showcase_pdf_versions():
    """BDD: Given 同一份增强内容，When 生成双版本，Then 两个 PDF 都存在且核心文本可复制。"""
    outputs = generate_resume_versions(RESUME_MD, PORTRAIT, OUTPUT_DIR)

    ats_pdf = outputs["ats_pdf"]
    showcase_pdf = outputs["showcase_pdf"]

    assert ats_pdf.exists()
    assert showcase_pdf.exists()
    assert ats_pdf.stat().st_size > 50_000
    assert showcase_pdf.stat().st_size > 50_000

    for pdf in [ats_pdf, showcase_pdf]:
        doc = fitz.open(pdf)
        try:
            assert 1 <= doc.page_count <= 2
        finally:
            doc.close()
        text = _pdf_text(pdf)
        assert "马浩宣" in text
        assert "yishuziyu@foxmail.com" in text
        assert "AI Agent" in text


def test_showcase_version_contains_portrait_image():
    """BDD: Given 原 PDF 已提取头像，When 生成展示版，Then 展示版 PDF 包含图片资源。"""
    outputs = generate_resume_versions(RESUME_MD, PORTRAIT, OUTPUT_DIR)
    doc = fitz.open(outputs["showcase_pdf"])
    try:
        image_count = sum(len(page.get_images(full=True)) for page in doc)
    finally:
        doc.close()

    assert image_count >= 1


def test_ats_version_is_more_text_first_than_showcase():
    """BDD: Then ATS 版更偏结构标准，不依赖照片；展示版可包含照片。"""
    outputs = generate_resume_versions(RESUME_MD, PORTRAIT, OUTPUT_DIR)
    ats_doc = fitz.open(outputs["ats_pdf"])
    show_doc = fitz.open(outputs["showcase_pdf"])
    try:
        ats_images = sum(len(page.get_images(full=True)) for page in ats_doc)
        show_images = sum(len(page.get_images(full=True)) for page in show_doc)
    finally:
        ats_doc.close()
        show_doc.close()

    assert ats_images == 0
    assert show_images >= 1


def test_generates_one_page_compact_ats_version():
    """BDD: Given 内容需要压缩，When 生成紧凑 ATS 版，Then 输出应为 1 页且核心文本仍可复制。"""
    compact_pdf = generate_compact_ats_version(RESUME_MD, OUTPUT_DIR)

    assert compact_pdf.exists()
    assert compact_pdf.stat().st_size > 50_000
    doc = fitz.open(compact_pdf)
    try:
        assert doc.page_count == 1
    finally:
        doc.close()

    text = _pdf_text(compact_pdf)
    assert "马浩宣" in text
    assert "yishuziyu@foxmail.com" in text
    assert "AI Agent" in text
    assert "深圳海坤投资管理有限公司" in text


def test_generates_one_page_photo_version():
    """BDD: Given 用户希望保留照片，When 生成一页克制版，Then PDF 应为 1 页且包含照片。"""
    photo_pdf = generate_onepage_photo_version(RESUME_MD, PORTRAIT, OUTPUT_DIR)

    assert photo_pdf.exists()
    assert photo_pdf.stat().st_size > 50_000
    doc = fitz.open(photo_pdf)
    try:
        assert doc.page_count == 1
        assert sum(len(page.get_images(full=True)) for page in doc) >= 1
    finally:
        doc.close()

    text = _pdf_text(photo_pdf)
    assert "马浩宣" in text
    assert "yishuziyu@foxmail.com" in text
    assert "AI Agent" in text
    assert "深圳海坤投资管理有限公司" in text


def test_generates_one_page_photo_striped_version():
    """BDD: Given 用户喜欢淡条纹背景，When 生成 v2，Then PDF 保持一页、带照片且核心文本可复制。"""
    striped_pdf = generate_onepage_photo_striped_version(RESUME_MD, PORTRAIT, OUTPUT_DIR)

    assert striped_pdf.exists()
    assert striped_pdf.stat().st_size > 50_000
    doc = fitz.open(striped_pdf)
    try:
        assert doc.page_count == 1
        assert sum(len(page.get_images(full=True)) for page in doc) >= 1
    finally:
        doc.close()

    text = _pdf_text(striped_pdf)
    assert "马浩宣" in text
    assert "yishuziyu@foxmail.com" in text
    assert "AI Agent" in text
    assert "深圳海坤投资管理有限公司" in text


def test_generates_one_page_photo_print_version():
    """BDD: Given v2 条纹略明显且打印可读性要更好，When 生成 v3，Then 条纹更淡、字号更适合打印且仍为一页带照片。"""
    print_pdf = generate_onepage_photo_print_version(RESUME_MD, PORTRAIT, OUTPUT_DIR)

    assert print_pdf.exists()
    assert print_pdf.stat().st_size > 50_000
    assert "print_v3" in print_pdf.name

    html = print_pdf.with_suffix(".html").read_text(encoding="utf-8")
    assert "rgba(37, 99, 235, 0.008)" in html
    assert "font-size: 8.9px" in html
    assert "line-height: 1.38" in html

    doc = fitz.open(print_pdf)
    try:
        assert doc.page_count == 1
        assert sum(len(page.get_images(full=True)) for page in doc) >= 1
    finally:
        doc.close()

    text = _pdf_text(print_pdf)
    assert "马浩宣" in text
    assert "yishuziyu@foxmail.com" in text
    assert "AI Agent" in text
    assert "深圳海坤投资管理有限公司" in text
