import base64
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient
import fitz

from web.resume_mvp_app import app


def _make_pdf_bytes(tmp_path: Path, body: str) -> bytes:
    html_path = tmp_path / "source.html"
    pdf_path = tmp_path / "source.pdf"
    html_path.write_text(f"<html><meta charset='utf-8'><body>{body}</body></html>", encoding="utf-8")
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if chrome.exists():
        subprocess.run(
            [
                str(chrome),
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}",
                html_path.resolve().as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return pdf_path.read_bytes()
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "mahaoxuan AI Agent resume")
    doc.save(pdf_path)
    doc.close()
    return pdf_path.read_bytes()


def test_resume_mvp_generates_resume_json_preview_and_pdf(tmp_path):
    client = TestClient(app)

    jd = """
    AI产品实习生：负责AI Agent产品调研、用户需求分析、竞品分析、原型协作、项目推进，要求能输出结构化报告。
    """.strip()
    material = """
    马浩宣｜华侨大学经济学本科｜yishuziyu@foxmail.com｜13310838384
    经历：深圳海坤投资管理有限公司，参与AI Agent投资机会研究与行业研究报告。
    项目：AIGC技术接受度调研，负责问卷设计、访谈整理、数据分析与报告撰写。
    项目：chrome-md-editor Markdown网页插件；battery-takeover Mac电池管理App。
    技能：Python、Stata、SPSS、Excel、Prompt Engineering、AI IDE。
    """.strip()

    home_resp = client.get("/")
    assert home_resp.status_code == 200
    assert "简历预览" in home_resp.text
    assert "等待生成简历预览" in home_resp.text
    assert "PDF 简历" in home_resp.text
    assert "读取本机材料文件夹" in home_resp.text
    assert "正式带照片版" in home_resp.text
    assert "ATS 无照片版" in home_resp.text
    assert "双栏带照片展示版" in home_resp.text
    assert "沿用上传简历信息" in home_resp.text
    assert "使用系统模板" in home_resp.text

    analyze_resp = client.post("/api/analyze-jd", json={"jd_text": jd})
    assert analyze_resp.status_code == 200
    assert "AI" in analyze_resp.json()["target_role"]

    upload_resp = client.post(
        "/api/upload-materials",
        json={"filename": "个人材料.md", "content": material, "content_type": "text/markdown"},
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["material_id"]
    assert upload_data["filename"] == "个人材料.md"

    pdf_bytes = _make_pdf_bytes(
        tmp_path,
        "马浩宣 华侨大学本科 yishuziyu@foxmail.com AI Agent 产品调研 项目推进",
    )
    pdf_upload_resp = client.post(
        "/api/upload-materials",
        json={
            "filename": "原始PDF简历.pdf",
            "content_base64": base64.b64encode(pdf_bytes).decode("ascii"),
            "content_type": "application/pdf",
        },
    )
    assert pdf_upload_resp.status_code == 200
    pdf_upload_data = pdf_upload_resp.json()
    assert pdf_upload_data["diagnostics"]["pages"] >= 1
    assert pdf_upload_data["diagnostics"]["extractable_chars"] > 0

    local_dir = tmp_path / "材料库"
    local_dir.mkdir()
    (local_dir / "作品集.md").write_text("项目：本机文件夹导入材料，AI Agent 作品集。", encoding="utf-8")
    (local_dir / "原简历.pdf").write_bytes(pdf_bytes)
    (local_dir / "身份证明.md").write_text("个人材料：身份证号 440000000000000000，仅用于身份核验，不应进入简历。", encoding="utf-8")
    folder_resp = client.post(
        "/api/import-local-folder",
        json={"folder_path": str(local_dir), "max_files": 5},
    )
    assert folder_resp.status_code == 200
    folder_data = folder_resp.json()
    assert folder_data["imported_count"] == 3
    assert len(folder_data["material_ids"]) == 3
    imported_by_name = {item["filename"]: item for item in folder_data["imported_materials"]}
    assert imported_by_name["原简历.pdf"]["material_type"] == "resume_template"
    assert imported_by_name["原简历.pdf"]["default_selected"] is True
    assert imported_by_name["作品集.md"]["material_type"] == "evidence"
    assert imported_by_name["作品集.md"]["default_selected"] is True
    assert imported_by_name["身份证明.md"]["material_type"] == "private_or_certificate"
    assert imported_by_name["身份证明.md"]["default_selected"] is False
    selected_folder_ids = [item["material_id"] for item in folder_data["imported_materials"] if item["default_selected"]]

    generate_resp = client.post(
        "/api/generate-resume",
        json={
            "jd_text": jd,
            "material_ids": [upload_data["material_id"], pdf_upload_data["material_id"]] + selected_folder_ids,
        },
    )
    assert generate_resp.status_code == 200
    data = generate_resp.json()
    assert data["status"] == "ok"
    assert data["resume_json"]["source_notes"]
    assert data["resume_json"]["resume"]["name"] == "马浩宣"
    assert data["resume_json"]["resume_mode"] == "improve_existing"
    assert data["resume_json"]["template_source"] == "uploaded_resume"
    assert data["resume_json"]["candidate_summary"]
    assert all(not item.startswith("经历：") for item in data["resume_json"]["resume"]["projects"])
    resume_blob = str(data["resume_json"]["resume"])
    assert "身份证" not in resume_blob
    assert "440000000000000000" not in resume_blob
    claims = [note["claim"] for note in data["resume_json"]["source_notes"]]
    assert len(claims) == len(set(claims))

    preview_resp = client.get("/api/preview", params={"resume_id": data["resume_id"]})
    assert preview_resp.status_code == 200
    assert "马浩宣" in preview_resp.text
    assert "source_notes" not in preview_resp.text
    assert "来源说明" not in preview_resp.text

    pdf_resp = client.get("/api/download-pdf", params={"resume_id": data["resume_id"]})
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"].startswith("application/pdf")
    assert pdf_resp.content[:4] == b"%PDF"
    doc = fitz.open(stream=pdf_resp.content, filetype="pdf")
    extracted_text = "".join(page.get_text("text") for page in doc)
    assert "马浩宣" in extracted_text
    assert "source_notes" not in extracted_text
    assert "来源说明" not in extracted_text


def test_template_selection_and_pdf_photo_reuse_from_original_resume():
    client = TestClient(app)
    source_pdf = Path("/Users/mahaoxuan/Desktop/马浩宣简历.pdf")
    assert source_pdf.exists()
    jd = "AI产品实习生：负责AI Agent调研、竞品分析、项目推进。"
    upload_resp = client.post(
        "/api/upload-materials",
        json={
            "filename": "马浩宣简历.pdf",
            "content_base64": base64.b64encode(source_pdf.read_bytes()).decode("ascii"),
            "content_type": "application/pdf",
        },
    )
    assert upload_resp.status_code == 200
    material_id = upload_resp.json()["material_id"]
    assert upload_resp.json()["diagnostics"]["photo_candidate"] is True

    formal_resp = client.post(
        "/api/generate-resume",
        json={"jd_text": jd, "material_ids": [material_id], "template_id": "formal_photo"},
    )
    assert formal_resp.status_code == 200
    formal = formal_resp.json()
    assert formal["resume_json"]["template"]["id"] == "formal_photo"
    assert formal["resume_json"]["photo_data_uri"].startswith("data:image/")
    formal_preview = client.get("/api/preview", params={"resume_id": formal["resume_id"]})
    assert 'data-template="formal_photo"' in formal_preview.text
    assert '<img class="avatar"' in formal_preview.text

    ats_resp = client.post(
        "/api/generate-resume",
        json={"jd_text": jd, "material_ids": [material_id], "template_id": "ats"},
    )
    assert ats_resp.status_code == 200
    ats = ats_resp.json()
    assert ats["resume_json"]["template"]["id"] == "ats"
    assert ats["resume_json"]["photo_data_uri"] is None
    ats_preview = client.get("/api/preview", params={"resume_id": ats["resume_id"]})
    assert 'data-template="ats"' in ats_preview.text
    assert '<img class="avatar"' not in ats_preview.text

    showcase_resp = client.post(
        "/api/generate-resume",
        json={"jd_text": jd, "material_ids": [material_id], "template_id": "showcase_photo"},
    )
    assert showcase_resp.status_code == 200
    showcase = showcase_resp.json()
    showcase_preview = client.get("/api/preview", params={"resume_id": showcase["resume_id"]})
    assert 'data-template="showcase_photo"' in showcase_preview.text
    assert '<img class="avatar"' in showcase_preview.text

    system_template_resp = client.post(
        "/api/generate-resume",
        json={
            "jd_text": jd,
            "material_ids": [material_id],
            "template_id": "formal_photo",
            "resume_mode": "new_from_materials",
            "template_source": "system_template",
        },
    )
    assert system_template_resp.status_code == 200
    system_template = system_template_resp.json()["resume_json"]
    assert system_template["resume_mode"] == "new_from_materials"
    assert system_template["template_source"] == "system_template"
    assert system_template["photo_data_uri"] is None
