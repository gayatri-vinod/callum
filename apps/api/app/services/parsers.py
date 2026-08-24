"""Deterministic document parsing with page-level provenance."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz

from app.models.schemas import DocumentModality


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    width: float | None = None
    height: float | None = None
    image_count: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedChunk:
    ordinal: int
    page_start: int
    page_end: int
    text: str
    section: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedReference:
    ordinal: int
    raw_text: str
    title: str | None = None
    doi: str | None = None
    url: str | None = None


@dataclass
class ExtractedAsset:
    page_number: int | None
    kind: str
    filename: str
    content_type: str
    data: bytes
    width: int | None = None
    height: int | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    title: str | None
    authors: list[str]
    abstract: str | None
    pages: list[ExtractedPage]
    chunks: list[ExtractedChunk]
    references: list[ExtractedReference]
    assets: list[ExtractedAsset]
    meta: dict[str, Any] = field(default_factory=dict)


class ParseError(RuntimeError):
    pass


_HEADING = re.compile(
    r"^(?:\d+(?:\.\d+)*[.)]?\s+)?"
    r"(abstract|introduction|background|related work|method(?:s|ology)?|"
    r"materials and methods|experiments?|results?|discussion|limitations?|"
    r"conclusion(?:s)?|future work|acknowledg(?:e)?ments?|references|appendix)\s*$",
    re.IGNORECASE,
)
_DOI = re.compile(
    r"\b(?:https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE
)
_URL = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)
_REFERENCE_START = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)[.)])\s+")


def _clean_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _metadata_authors(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r"\s*(?:;|, and | and )\s*", value)
    return [part.strip() for part in parts if part.strip()]


def _infer_title(metadata_title: str | None, first_page: fitz.Page, fallback: str) -> str:
    if metadata_title and metadata_title.strip():
        return metadata_title.strip()
    blocks = first_page.get_text("dict").get("blocks", [])
    candidates: list[tuple[float, str]] = []
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            spans = line.get("spans", [])
            text = " ".join(span.get("text", "").strip() for span in spans).strip()
            if text and len(text) >= 5:
                size = max((float(span.get("size", 0)) for span in spans), default=0)
                candidates.append((size, text))
    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1][:512]
    return Path(fallback).stem.replace("_", " ")


def _section_for_line(line: str, current: str | None) -> str | None:
    match = _HEADING.match(line.strip())
    return match.group(1).lower() if match else current


def _chunks_from_pages(
    pages: list[ExtractedPage], target_chars: int = 1800, overlap_chars: int = 240
) -> list[ExtractedChunk]:
    chunks: list[ExtractedChunk] = []
    ordinal = 0
    section: str | None = None

    for page in pages:
        raw_paragraphs: list[str] = []
        lines: list[str] = []
        for line in page.text.splitlines():
            stripped = line.strip()
            if not stripped:
                if lines:
                    raw_paragraphs.append(" ".join(lines))
                    lines = []
                continue
            if _HEADING.match(stripped):
                if lines:
                    raw_paragraphs.append(" ".join(lines))
                    lines = []
                raw_paragraphs.append(stripped)
            else:
                lines.append(stripped)
        if lines:
            raw_paragraphs.append(" ".join(lines))

        paragraphs = [
            re.sub(r"\s+", " ", paragraph).strip()
            for paragraph in raw_paragraphs
            if paragraph.strip()
        ]
        if not paragraphs and page.text.strip():
            paragraphs = [re.sub(r"\s+", " ", page.text).strip()]

        buffer = ""
        chunk_section = section
        for paragraph in paragraphs:
            first_line = paragraph.splitlines()[0].strip()
            next_section = _section_for_line(first_line, section)
            if next_section != section:
                section = next_section
                if len(paragraph) < 120:
                    continue
            if not buffer:
                chunk_section = section
            candidate = f"{buffer}\n\n{paragraph}".strip()
            if len(candidate) <= target_chars:
                buffer = candidate
                continue

            if buffer:
                chunks.append(
                    ExtractedChunk(
                        ordinal=ordinal,
                        page_start=page.page_number,
                        page_end=page.page_number,
                        text=buffer,
                        section=chunk_section,
                    )
                )
                ordinal += 1
                overlap = buffer[-overlap_chars:].lstrip()
                buffer = f"{overlap}\n\n{paragraph}".strip()
            else:
                start = 0
                while start < len(paragraph):
                    end = min(start + target_chars, len(paragraph))
                    piece = paragraph[start:end].strip()
                    if piece:
                        chunks.append(
                            ExtractedChunk(
                                ordinal=ordinal,
                                page_start=page.page_number,
                                page_end=page.page_number,
                                text=piece,
                                section=section,
                            )
                        )
                        ordinal += 1
                    if end >= len(paragraph):
                        break
                    start = max(end - overlap_chars, start + 1)
                buffer = ""

        if buffer:
            chunks.append(
                ExtractedChunk(
                    ordinal=ordinal,
                    page_start=page.page_number,
                    page_end=page.page_number,
                    text=buffer,
                    section=chunk_section,
                )
            )
            ordinal += 1
    return chunks


def _extract_abstract(pages: list[ExtractedPage]) -> str | None:
    text = "\n".join(page.text for page in pages[:3])
    match = re.search(
        r"(?:^|\n)\s*abstract\s*(?:\n|[:—-])\s*(.+?)(?=\n\s*"
        r"(?:keywords?|1[.)]?\s+introduction|introduction)\b)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()[:4000]
    return None


def _extract_references(pages: list[ExtractedPage]) -> list[ExtractedReference]:
    full_text = "\n".join(page.text for page in pages)
    heading = re.search(r"(?:^|\n)\s*references\s*(?:\n|$)", full_text, re.IGNORECASE)
    if not heading:
        return []
    raw = full_text[heading.end() :].strip()
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines() if line.strip()]
    entries: list[str] = []
    current = ""
    for line in lines:
        if _REFERENCE_START.match(line):
            if current:
                entries.append(current)
            current = _REFERENCE_START.sub("", line)
        elif current:
            current = f"{current} {line}"
        else:
            current = line
    if current:
        entries.append(current)

    references: list[ExtractedReference] = []
    for index, entry in enumerate(entries[:500], start=1):
        doi_match = _DOI.search(entry)
        url_match = _URL.search(entry)
        references.append(
            ExtractedReference(
                ordinal=index,
                raw_text=entry,
                doi=doi_match.group(1).rstrip(".,;)") if doi_match else None,
                url=url_match.group(0).rstrip(".,;)") if url_match else None,
            )
        )
    return references


def parse_pdf(data: bytes, filename: str) -> ParsedDocument:
    try:
        pdf = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ParseError(f"invalid or unreadable PDF: {exc}") from exc
    if pdf.page_count == 0:
        pdf.close()
        raise ParseError("PDF has no pages")

    try:
        metadata = pdf.metadata or {}
        title = _infer_title(metadata.get("title"), pdf[0], filename)
        authors = _metadata_authors(metadata.get("author"))
        pages: list[ExtractedPage] = []
        assets: list[ExtractedAsset] = []
        seen_xrefs: set[int] = set()

        for page_index, page in enumerate(pdf):
            page_number = page_index + 1
            text = _clean_text(page.get_text("text", sort=True))
            images = page.get_images(full=True)
            pages.append(
                ExtractedPage(
                    page_number=page_number,
                    text=text,
                    width=float(page.rect.width),
                    height=float(page.rect.height),
                    image_count=len(images),
                    meta={"word_count": len(text.split())},
                )
            )
            for image_index, image in enumerate(images, start=1):
                xref = int(image[0])
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                extracted = pdf.extract_image(xref)
                image_bytes = extracted.get("image")
                if not image_bytes:
                    continue
                extension = str(extracted.get("ext") or "bin").lower()
                content_type = f"image/{'jpeg' if extension in {'jpg', 'jpeg'} else extension}"
                assets.append(
                    ExtractedAsset(
                        page_number=page_number,
                        kind="figure",
                        filename=f"figure-p{page_number}-{image_index}.{extension}",
                        content_type=content_type,
                        data=image_bytes,
                        width=extracted.get("width"),
                        height=extracted.get("height"),
                        meta={"xref": xref},
                    )
                )

        text_pages = sum(bool(page.text.strip()) for page in pages)
        if text_pages == 0:
            raise ParseError("PDF contains no extractable text; OCR is required")

        chunks = _chunks_from_pages(pages)
        abstract = _extract_abstract(pages)
        references = _extract_references(pages)
        return ParsedDocument(
            title=title,
            authors=authors,
            abstract=abstract,
            pages=pages,
            chunks=chunks,
            references=references,
            assets=assets,
            meta={
                "parser": "pymupdf",
                "page_count": pdf.page_count,
                "text_page_count": text_pages,
                "chunk_count": len(chunks),
                "reference_count": len(references),
                "figure_count": len(assets),
                "pdf_metadata": {
                    key: value
                    for key, value in metadata.items()
                    if value
                    and key in {"title", "author", "subject", "keywords", "creator", "producer"}
                },
            },
        )
    finally:
        pdf.close()


def parse_text(data: bytes, filename: str) -> ParsedDocument:
    try:
        text = _clean_text(data.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ParseError("text document is not valid UTF-8") from exc
    if not text:
        raise ParseError("document is empty")
    page = ExtractedPage(page_number=1, text=text, meta={"word_count": len(text.split())})
    return ParsedDocument(
        title=Path(filename).stem.replace("_", " "),
        authors=[],
        abstract=None,
        pages=[page],
        chunks=_chunks_from_pages([page]),
        references=[],
        assets=[],
        meta={"parser": "utf8", "page_count": 1},
    )


def parse_document(data: bytes, filename: str, modality: DocumentModality) -> ParsedDocument:
    if modality == DocumentModality.pdf:
        return parse_pdf(data, filename)
    if modality in {DocumentModality.markdown, DocumentModality.code}:
        return parse_text(data, filename)
    raise ParseError(f"no parser is available for modality: {modality.value}")
