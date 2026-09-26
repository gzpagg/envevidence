"""Display translations only: never rewrite evidence or user-authored content."""

import re
from contextvars import ContextVar

LANGUAGE = ContextVar("language", default="en")


def t(en, zh):
    return zh if LANGUAGE.get() == "zh" else en


def fixed_format(function):
    """Keep widget option labels in the language of the render that created them."""
    language = LANGUAGE.get()

    def format_value(value):
        token = LANGUAGE.set(language)
        try:
            return function(value)
        finally:
            LANGUAGE.reset(token)

    return format_value


# Chinese keys also recognize diagnostics persisted by version 0.1.
CATALOG = {
    "从一组论文开始": "Start with a set of papers",
    "每篇主文献建立独立研究记录，补充材料显式关联。先在本地解析，再决定是否发送模型。": "Each main paper has its own study record and explicitly linked supplements. Parse locally before sending text to a model.",
    "解析并建立项目": "Parse and create project",
    "资料与提取": "Documents & extraction",
    "开始 / 继续提取": "Start / resume extraction",
    "证据核验": "Evidence review",
    "自动检查原句是否存在。人工核验还需确认数值、单位、处理条件与指标对应。": "Quote matching checks text location. Human review must also check the value, unit, condition and endpoint.",
    "选择实验条件": "Select experimental condition",
    "选择字段": "Select field",
    "导出与记录": "Export & history",
    "导出保留模型原值、当前值、核验状态、出处与修订历史。未核验字段不会被标成已确认。": "Exports retain model values, current values, review status, sources and revision history. Unreviewed fields remain unverified.",
    "下载 Excel 工作簿": "Download Excel workbook",
    "下载 CSV 证据表": "Download evidence CSV",
    "下载完整 JSON": "Download full JSON",
    "完整 JSON 包含已解析原文。对外分享前请确认资料的分发权限。": "Full JSON includes parsed source text. Check redistribution rights before sharing.",
    "**运行记录**": "**Run history**",
    "新建提取项目": "New evidence project",
    "载入离线演示": "Load evidence demo",
    "项目名称": "Project name",
    "主文献 PDF（可多选）": "Main PDFs (multiple allowed)",
    "补充材料 PDF（可选）": "Supplementary PDFs (optional)",
    "支持文本型 PDF，每份最多 30 MB / 250 页。扫描页、图片和复杂表格可能无法解析，会明确提示。": "Text PDFs, up to 30 MB / 250 pages each. Scans, images and complex tables may not parse; warnings will be shown.",
    "模型服务": "Model provider",
    "模型名称": "Model ID",
    "水处理字段模板": "Water-treatment fields",
    "自定义字段（可选）": "Custom fields (optional)",
    "查看本地解析文本与页码": "Inspect parsed text and page numbers",
    "来源文件": "Source file",
    "PDF 页码": "PDF page",
    "这是预录的合成案例，用于演示与回归测试，未调用模型，也不是实际研究结果。": "Recorded synthetic example for demos and regression tests. No model was called; these are not scientific findings.",
    "下载示例主文献": "Download example main paper",
    "下载示例补充材料": "Download example supplement",
    "本项目提取已完成，请到证据核验中检查结果。": "Extraction is complete. Review the results in Evidence review.",
    "API 密钥（仅本次会话）": "API key (this session only)",
    "我已检查缺失页面，接受仅提取成功解析的页面。": "I reviewed missing pages and accept extracting only successfully parsed pages.",
    "尚无实验记录。先完成提取；已完成但没有记录的论文可在运行记录中查看。": "No experiment records yet. Extract first; consult run history for completed studies with no records.",
    "**原文证据**": "**Source evidence**",
    "**人工核验与修订**": "**Human review & corrections**",
    "已保存的项目": "Saved projects",
    "打开项目": "Open project",
    "我的文献证据表": "My evidence table",
    "填写你账户中可用且支持结构化输出的模型 ID。": "Enter an available model ID that supports structured output.",
    "temperature | 温度 | 本实验的反应温度 | unit\ncatalyst | 催化剂 | 催化剂名称和组成": "temperature | Temperature | Reaction temperature for this condition | unit\ncatalyst | Catalyst | Catalyst name and composition",
    "每行：英文键名 | 中文名称 | 提取说明 | unit（需要单位时填写）": "Each line: key | label | extraction instruction | unit (if required)",
    "研究": "Study",
    "文件": "File",
    "类型": "Role",
    "PDF 页数": "PDF pages",
    "已解析页": "Parsed pages",
    "提示": "Warnings",
    "准备提取…": "Preparing extraction…",
    "实验": "Experiment",
    "字段": "Field",
    "当前值": "Current value",
    "单位": "Unit",
    "出处": "Source",
    "人工核验": "Human review",
    "在已导入且成功解析的资料中未找到对应出处。": "No source found in the imported, successfully parsed material.",
    "模型原始记录与检查提示": "Model record & validation warnings",
    "核验状态": "Review status",
    "核验人": "Reviewer",
    "核验说明 / 修改理由": "Review note / reason",
    "替换出处（不勾选则保留现有全部出处）": "Replace sources (otherwise retain all current sources)",
    "替换为哪一页？": "Replacement source page",
    "替换用的原文片段": "Replacement verbatim quote",
    "保存核验记录": "Save review",
    "请选择字段，并确保英文键名不重复。": "Select fields and use unique keys.",
    "请填写项目名称和模型名称；创建项目时不调用 API。": "Enter a project name and model ID. Creating a project does not call the API.",
    "正在本地解析 PDF…": "Parsing PDFs locally…",
    "主文献": "Main",
    "补充材料": "Supplement",
    "已定位": "Located",
    "未定位 / 未找到": "Unlocated / missing",
    "模型原值": "Model value",
    "模型单位": "Model unit",
    "提取状态": "Extraction status",
    "例如：对照 Trial A 的条件核验，85% 为污染物去除率，20% 为 TOC 去除率。": "For example: checked Trial A; 85% is pollutant removal and 20% is TOC removal.",
    "从原文完整复制，不要改写。": "Copy verbatim from the source; do not paraphrase.",
    "论文": "Paper",
    "状态": "Status",
    "输入 tokens": "Input tokens",
    "输出 tokens": "Output tokens",
    "错误": "Error",
    "开始时间": "Started at",
    "未知来源": "Unknown source",
    "自定义字段格式：key | 名称 | 说明 | unit（第四项可省略）。": "Custom field format: key | label | instruction | unit (last segment optional).",
    "项目无法读取或版本不兼容。原文件未修改。": "Cannot read this project or its version is incompatible. The source file was not changed.",
    "检测到重复 PDF，请移除重复文件后重试。": "Duplicate PDFs detected. Remove duplicates and retry.",
    "待核验": "Pending",
    "人工确认": "Verified",
    "不采纳": "Rejected",
    "污染物": "Pollutant",
    "水体类型": "Water matrix",
    "初始浓度": "Initial concentration",
    "处理工艺": "Treatment process",
    "投加剂量": "Reagent dose",
    "反应时间": "Reaction time",
    "污染物去除率": "Pollutant removal",
    "矿化率 / TOC 去除率": "Mineralization / TOC removal",
    "离线演示仅支持附带的合成资料；真实论文请选择 API 提取。": "The offline demo only accepts the supplied synthetic files. Use API extraction for real papers.",
    "这组主文献及补充材料超过 160,000 字符；请拆分后重试，未截断或发送内容。": "This study exceeds 160,000 characters. Split it and retry. No text was truncated or sent.",
    "请在本机配置 API 密钥和支持结构化输出的模型名称。": "Provide an API key and a model that supports structured output.",
    "网络或 API 超时；已完成论文保留，可重试未完成论文。": "Network/API timeout. Completed studies are saved; retry unfinished studies.",
    "API 密钥认证失败。": "API key authentication failed.",
    "账户没有此 API 或模型的访问权限。": "The account cannot access this API or model.",
    "API 限流或额度不足，请检查账户后重试。": "API rate or quota limit. Check your account and retry.",
    "API 拒绝请求，请检查模型是否支持结构化输出及上下文长度。": "API rejected the request. Check structured-output support and context limits.",
    "模型输出未完整完成，未保存该论文的部分结果。": "Model output is incomplete; partial results for this study were not saved.",
    "模型拒绝了本次请求。": "The model refused this request.",
    "模型输出被截断或未正常结束，未保存该论文的部分结果。": "Model output was truncated or did not finish normally; partial results were not saved.",
    "模型返回内容不符合证据表结构，该论文未标记完成。": "The response does not match the evidence schema. This study is not marked complete.",
    "模型返回了重复、未知或缺失字段，结果未保存。": "The response has duplicate, unknown or missing fields; results were not saved.",
    "在已导入且成功解析的资料中未找到；不代表论文没有报告。": "Not found in imported, parsed material; this does not mean the paper did not report it.",
    "未找到的字段包含数值或出处，返回结果不一致。": "A missing field contains a value or source; the response is inconsistent.",
    "原文定位未通过，请核对来源。": "Source matching failed. Check the source.",
    "字段有标记但没有可用值。": "The field is marked present but has no usable value.",
    "缺少单位，不执行自动推断或换算。": "Missing unit. No inference or conversion is performed.",
    "上下文存在歧义，需人工判断。": "Ambiguous context; human judgment is needed.",
    "请填写核验人和修订理由。": "Enter a reviewer and a revision reason.",
    "确认字段前，需要非空值和能定位的原文出处。": "Verification requires a nonempty value and matching source quotations.",
    "不是有效的 PDF 文件 / Invalid PDF header.": "Invalid PDF header.",
    "PDF 超过 30 MB，请先拆分。": "PDF exceeds 30 MB. Split it first.",
    "加密 PDF 暂不支持，请提供解锁后的副本。": "Encrypted PDFs are not supported. Provide an unlocked copy.",
    "无法读取 PDF；文件可能损坏或格式不受支持。": "Cannot read the PDF. It may be damaged or unsupported.",
    "没有可提取的文本页。首版不支持纯扫描件；请先在本地完成 OCR。": "No extractable text pages. Scans require local OCR before import.",
    "至少选择一个字段，且字段名不能重复。": "Select at least one field with unique keys.",
    "上次运行中断，可重试。": "The previous run was interrupted. You can retry.",
    "提取或结构校验失败；未保存此篇部分结果。": "Extraction or schema validation failed; partial results were not saved.",
}

# Only application-generated messages call tr(); user text is never passed here.
PATTERNS = {
    r"(.+) 属于哪篇主文献？": "Which main paper does {0} belong to?",
    r"服务：(.+) · 模型：(.+) · 待提取：([0-9]+) 篇。已完成的论文不会重复发送。": "Provider: {0} · Model: {1} · Pending: {2}. Completed papers are not sent again.",
    r"(.+)：待发送约 ([0-9,]+) 字符（非 token 数；费用以服务商账单为准）。": "{0}: about {1} characters to send (not tokens; provider billing applies).",
    r"也可配置本机环境变量 (.+)。不会写入项目或日志。": "Or set the local {0} environment variable. Never saved to projects or logs.",
    r"我同意将这些已解析文本发送至 (.+)，并使用自己的 API 额度。": "I agree to send this parsed text to {0} using my own API quota.",
    r"(.+) · PDF 第 (.+) 页": "{0} · PDF page {1}",
    r"原句已定位 · (.+)": "Quote located · {0}",
    r"原句未通过定位 · (.+)": "Quote not located · {0}",
    r"查看整页上下文 · (.+)": "Full page context · {0}",
    r"(.+) · 第 ([0-9]+) 页": "{0} · page {1}",
    r"修订历史（([0-9]+) 条）": "Revision history ({0})",
    r"模型服务返回 HTTP ([0-9]+)，请稍后重试。": "Model service returned HTTP {0}. Retry later.",
    r"PDF 超过 ([0-9]+) 页，请先拆分。": "PDF exceeds {0} pages. Split it first.",
    r"第 ([0-9]+) 页解析失败，未参与提取。": "Page {0} failed to parse and was excluded.",
    r"第 ([0-9]+) 页文字过少，可能是扫描页或图像，未参与提取。": "Page {0} has too little text (possibly a scan or image) and was excluded.",
}


def tr(message):
    if LANGUAGE.get() == "zh":
        return message
    if message in CATALOG:
        return CATALOG[message]
    for pattern, template in PATTERNS.items():
        match = re.fullmatch(pattern, message, flags=re.DOTALL)
        if match:
            return template.format(*match.groups())
    return message


def field_label(key, label):
    from .templates import water_treatment_fields

    for spec in water_treatment_fields():
        if key == spec.key and label in (spec.label, CATALOG.get(spec.label)):
            return spec.label if LANGUAGE.get() == "zh" else CATALOG.get(spec.label, spec.label)
    return label


def state_label(value):
    states = {
        "pending": ("Pending", "待核验"),
        "verified": ("Verified", "人工确认"),
        "rejected": ("Rejected", "不采纳"),
        "found": ("Found", "已找到"),
        "not_found": ("Not found", "未找到"),
        "unclear": ("Unclear", "有歧义"),
        "completed": ("Completed", "已完成"),
        "running": ("Running", "运行中"),
        "failed": ("Failed", "失败"),
    }
    return t(*states[value]) if value in states else value
