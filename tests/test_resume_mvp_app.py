from fastapi.testclient import TestClient

from web.resume_mvp_app import app


def test_resume_mvp_generates_resume_json_preview_and_pdf():
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

    generate_resp = client.post(
        "/api/generate-resume",
        json={"jd_text": jd, "material_ids": [upload_data["material_id"]]},
    )
    assert generate_resp.status_code == 200
    data = generate_resp.json()
    assert data["status"] == "ok"
    assert data["resume_json"]["source_notes"]
    assert data["resume_json"]["resume"]["name"] == "马浩宣"
    assert data["resume_json"]["candidate_summary"]

    preview_resp = client.get("/api/preview", params={"resume_id": data["resume_id"]})
    assert preview_resp.status_code == 200
    assert "马浩宣" in preview_resp.text
    assert "来源说明" in preview_resp.text

    pdf_resp = client.get("/api/download-pdf", params={"resume_id": data["resume_id"]})
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"].startswith("application/pdf")
    assert pdf_resp.content[:4] == b"%PDF"
