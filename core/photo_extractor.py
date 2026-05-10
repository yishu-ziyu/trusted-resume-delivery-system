"""Extract reusable portrait/photo assets from a PDF resume."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import fitz


@dataclass(frozen=True)
class PortraitCandidate:
    path: Path
    width: int
    height: int
    page: int
    bbox: Tuple[float, float, float, float]
    kind: str = "portrait_candidate"


def _score_image(width: int, height: int, rect: fitz.Rect) -> float:
    """Heuristic score for a resume portrait candidate.

    A portrait is usually medium sized, roughly vertical, and not a full-page
    background or horizontal divider. The original resume photo is 310x414 and
    placed near the upper-left area, so this intentionally favors vertical
    images with human-photo proportions.
    """
    if width <= 0 or height <= 0:
        return -1
    aspect = width / height
    area = width * height
    rect_area = max(rect.width * rect.height, 1)

    score = 0.0
    if 0.55 <= aspect <= 0.9:
        score += 50
    if 150 <= width <= 900 and 180 <= height <= 1200:
        score += 30
    if 5_000 <= area <= 1_000_000:
        score += 20
    if rect.y0 < 220:
        score += 10
    if rect_area > 10_000:
        score += 5
    # Penalize full-page background and long horizontal decorations.
    if aspect > 2.0:
        score -= 80
    if rect.width > 300 and rect.height > 300:
        score -= 60
    return score


def extract_portrait_candidate(pdf_path: Path, output_dir: Path) -> PortraitCandidate:
    """Extract the most likely portrait image from a PDF resume.

    Args:
        pdf_path: Source PDF path.
        output_dir: Directory where the image should be saved.

    Returns:
        PortraitCandidate with saved image path and metadata.

    Raises:
        FileNotFoundError: if pdf_path does not exist.
        ValueError: if no image candidate is found.
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    if not pdf_path.exists():
        raise FileNotFoundError(str(pdf_path))
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    candidates: List[Tuple[float, int, int, int, int, int, fitz.Rect, bytes, str]] = []
    try:
        for page_index, page in enumerate(doc):
            for image_index, image in enumerate(page.get_images(full=True)):
                xref = image[0]
                info = doc.extract_image(xref)
                width = int(info.get("width") or 0)
                height = int(info.get("height") or 0)
                ext = str(info.get("ext") or "png")
                data = info.get("image")
                if not data:
                    continue
                rects = page.get_image_rects(xref)
                for rect in rects:
                    score = _score_image(width, height, rect)
                    candidates.append((score, page_index, image_index, xref, width, height, rect, data, ext))
    finally:
        doc.close()

    if not candidates:
        raise ValueError(f"No images found in PDF: {pdf_path}")

    candidates.sort(key=lambda item: item[0], reverse=True)
    score, page_index, image_index, xref, width, height, rect, data, ext = candidates[0]
    if score < 0:
        raise ValueError(f"No suitable portrait candidate found in PDF: {pdf_path}")

    suffix = "jpg" if ext.lower() == "jpeg" else ext.lower()
    out_path = output_dir / f"portrait_candidate_p{page_index + 1}_xref{xref}.{suffix}"
    out_path.write_bytes(data)

    return PortraitCandidate(
        path=out_path,
        width=width,
        height=height,
        page=page_index + 1,
        bbox=(float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)),
    )
