"""Text PDFs only. No network calls, OCR, or silent page truncation."""

import hashlib
import io
from pathlib import Path
from typing import Literal

from pypdf import PdfReader

from .models import Block, Document

MAX_PDF_BYTES = 30 * 1024 * 1024
MAX_PAGES = 250


class ParseError(ValueError):
    pass


def parse_pdf(data: bytes, filename: str, role: Literal["main", "supplement"] = "main") -> Document:
    if not data.startswith(b"%PDF-"):
        raise ParseError("不是有效的 PDF 文件 / Invalid PDF header.")
    if len(data) > MAX_PDF_BYTES:
        raise ParseError("PDF 超过 30 MB，请先拆分。")
    digest = hashlib.sha256(data).hexdigest()
    doc_id = digest[:20]
    warnings: list[str] = []
    blocks: list[Block] = []
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ParseError("加密 PDF 暂不支持，请提供解锁后的副本。")
        if len(reader.pages) > MAX_PAGES:
            raise ParseError(f"PDF 超过 {MAX_PAGES} 页，请先拆分。")
        for page_no, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text() or ""
            except Exception:
                warnings.append(f"第 {page_no} 页解析失败，未参与提取。")
                continue
            if len(text.strip()) < 20:
                warnings.append(f"第 {page_no} 页文字过少，可能是扫描页或图像，未参与提取。")
                continue
            # Keep a full page together so table rows and adjacent sentences retain context.
            blocks.append(Block(id=f"{doc_id}:p{page_no}", page=page_no, text=text))
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError("无法读取 PDF；文件可能损坏或格式不受支持。") from exc
    if not blocks:
        raise ParseError("没有可提取的文本页。首版不支持纯扫描件；请先在本地完成 OCR。")
    return Document(
        id=doc_id,
        filename=Path(filename.replace("\\", "/")).name,
        sha256=digest,
        role=role,
        page_count=len(reader.pages),
        blocks=blocks,
        warnings=warnings,
    )
