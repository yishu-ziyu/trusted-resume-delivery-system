from pathlib import Path

from core.photo_extractor import extract_portrait_candidate

PROJECT = Path(__file__).resolve().parents[1]
SOURCE_PDF = Path("/Users/mahaoxuan/Desktop/马浩宣简历.pdf")
ASSET_DIR = PROJECT / "output" / "assets"


def test_extracts_portrait_candidate_from_original_resume_pdf():
    """BDD: Given 原 PDF 包含证件照，When 提取图片资源，Then 保存最可能的头像图片。"""
    result = extract_portrait_candidate(SOURCE_PDF, ASSET_DIR)

    assert result.path.exists()
    assert result.path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    assert result.width > 200
    assert result.height > 200
    assert result.kind == "portrait_candidate"
