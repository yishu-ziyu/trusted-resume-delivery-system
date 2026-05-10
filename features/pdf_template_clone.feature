Feature: 复用原 PDF 简历模板生成新简历

  Scenario: 文本型 PDF 可以进入模板复刻流程
    Given 用户上传了一份可复制文字的 PDF 简历
    When 系统执行 PDF 诊断
    Then 系统应判断该 PDF 为 text_based
    And 系统应提取文本块、字体、字号、颜色和坐标
    And 系统应给出“可尝试原风格复刻”的建议

  Scenario: 图片型 PDF 不能承诺原位编辑
    Given 用户上传了一份扫描版 PDF 简历
    When 系统执行 PDF 诊断
    Then 系统应判断该 PDF 为 image_based 或 scanned
    And 系统应提示“不能直接编辑原 PDF”
    And 系统应提供“OCR 后重建新版 PDF”的选项

  Scenario: 替换成不相关内容后仍保持原模板风格
    Given 用户上传了一份成型 PDF 简历
    And 用户提供了一套完全不相关的新简历内容
    When 系统生成 cloned_resume.pdf
    Then 新 PDF 的页面尺寸应与原 PDF 一致
    And 新 PDF 的主字体、字号、颜色应接近原 PDF
    And 新 PDF 的主要区块位置应接近原 PDF
    And 新 PDF 不应出现文本重叠
    And 新 PDF 不应出现页面溢出
