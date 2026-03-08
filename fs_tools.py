"""
fs_tools.py – File-system helper utilities for an LLM-powered assistant.

Provides:
    read_file     – extract text from PDF / TXT / DOCX files
    list_files    – list directory contents with optional extension filter
    write_file    – write text content to a file (creates dirs as needed)
    search_in_file – case-insensitive keyword search with surrounding context
"""

from __future__ import annotations

import os
import re
import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------

def read_file(filepath: str) -> dict:
    """Read a file (PDF, TXT, or DOCX) and return its text content plus metadata.

    Parameters
    ----------
    filepath : str
        Path to the file to read.

    Returns
    -------
    dict
        {
            "status": "success" | "error",
            "filepath": str,
            "content": str,          # extracted text (empty on error)
            "metadata": {
                "filename": str,
                "extension": str,
                "size_bytes": int,
                "modified": str,     # ISO-8601 timestamp
            },
            "error": str | None,
        }
    """
    filepath = os.path.abspath(filepath)
    result: dict = {
        "status": "error",
        "filepath": filepath,
        "content": "",
        "metadata": {},
        "error": None,
    }

    try:
        if not os.path.isfile(filepath):
            result["error"] = f"File not found: {filepath}"
            return result

        stat = os.stat(filepath)
        ext = Path(filepath).suffix.lower()

        result["metadata"] = {
            "filename": os.path.basename(filepath),
            "extension": ext,
            "size_bytes": stat.st_size,
            "modified": datetime.datetime.fromtimestamp(
                stat.st_mtime
            ).isoformat(),
        }

        # --- Extract text based on extension ---
        if ext == ".pdf":
            result["content"] = _read_pdf(filepath)
        elif ext == ".docx":
            result["content"] = _read_docx(filepath)
        elif ext in {".txt", ".text", ".md", ".csv", ".log", ".json"}:
            result["content"] = _read_text(filepath)
        else:
            # Best-effort: try reading as plain text
            result["content"] = _read_text(filepath)

        result["status"] = "success"

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


def _read_pdf(filepath: str) -> str:
    """Extract text from a PDF using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
    except ImportError as exc:
        raise ImportError(
            "PyPDF2 is required to read PDF files. "
            "Install it with:  pip install PyPDF2"
        ) from exc

    reader = PdfReader(filepath)
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def _read_docx(filepath: str) -> str:
    """Extract text from a DOCX using python-docx."""
    try:
        from docx import Document
    except ImportError as exc:
        raise ImportError(
            "python-docx is required to read DOCX files. "
            "Install it with:  pip install python-docx"
        ) from exc

    doc = Document(filepath)
    return "\n".join(para.text for para in doc.paragraphs)


def _read_text(filepath: str) -> str:
    """Read a plain-text file with automatic encoding detection."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(filepath, "r", encoding=encoding) as fh:
                return fh.read()
        except (UnicodeDecodeError, ValueError):
            continue
    # Last resort – binary safe
    with open(filepath, "rb") as fh:
        return fh.read().decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# list_files
# ---------------------------------------------------------------------------

def list_files(directory: str, extension: Optional[str] = None) -> list[dict]:
    """List files in *directory*, optionally filtered by extension.

    Parameters
    ----------
    directory : str
        Path to the directory to scan.
    extension : str, optional
        File extension filter (e.g. ``".pdf"``). A leading dot is added
        automatically if missing. ``None`` returns all files.

    Returns
    -------
    list[dict]
        Each dict:
        {
            "name": str,
            "path": str,
            "size_bytes": int,
            "modified": str,   # ISO-8601
        }
        Returns an empty list when the directory does not exist.
    """
    directory = os.path.abspath(directory)

    if not os.path.isdir(directory):
        return []

    # Normalise extension
    if extension is not None:
        extension = extension.lower()
        if not extension.startswith("."):
            extension = f".{extension}"

    files: list[dict] = []
    for entry in os.scandir(directory):
        if not entry.is_file():
            continue

        if extension and not entry.name.lower().endswith(extension):
            continue

        stat = entry.stat()
        files.append(
            {
                "name": entry.name,
                "path": entry.path,
                "size_bytes": stat.st_size,
                "modified": datetime.datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat(),
            }
        )

    # Sort alphabetically for deterministic output
    files.sort(key=lambda f: f["name"].lower())
    return files


# ---------------------------------------------------------------------------
# write_file
# ---------------------------------------------------------------------------

def write_file(filepath: str, content: str) -> dict:
    """Write *content* to *filepath*, creating parent directories as needed.

    Parameters
    ----------
    filepath : str
        Destination file path.
    content : str
        Text content to write.

    Returns
    -------
    dict
        {
            "status": "success" | "error",
            "filepath": str,
            "bytes_written": int,
            "error": str | None,
        }
    """
    filepath = os.path.abspath(filepath)
    result: dict = {
        "status": "error",
        "filepath": filepath,
        "bytes_written": 0,
        "error": None,
    }

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            result["bytes_written"] = fh.write(content)
        result["status"] = "success"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


# ---------------------------------------------------------------------------
# search_in_file
# ---------------------------------------------------------------------------

_CONTEXT_CHARS = 80  # characters of surrounding context per match

def search_in_file(filepath: str, keyword: str) -> dict:
    """Perform a case-insensitive keyword search inside a file.

    Parameters
    ----------
    filepath : str
        Path to the file to search (supports PDF, DOCX, and text).
    keyword : str
        Search term (plain text, case-insensitive).

    Returns
    -------
    dict
        {
            "status": "success" | "error",
            "filepath": str,
            "keyword": str,
            "match_count": int,
            "matches": [
                {
                    "position": int,       # character offset in full text
                    "context": str,         # surrounding snippet
                    "matched_text": str,    # exact text that matched
                }
            ],
            "error": str | None,
        }
    """
    filepath = os.path.abspath(filepath)
    result: dict = {
        "status": "error",
        "filepath": filepath,
        "keyword": keyword,
        "match_count": 0,
        "matches": [],
        "error": None,
    }

    try:
        # Re-use read_file to extract text transparently
        read_result = read_file(filepath)
        if read_result["status"] != "success":
            result["error"] = read_result["error"]
            return result

        text = read_result["content"]
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)

        matches: list[dict] = []
        for match in pattern.finditer(text):
            start = max(match.start() - _CONTEXT_CHARS, 0)
            end = min(match.end() + _CONTEXT_CHARS, len(text))

            # Build context snippet with ellipsis markers
            prefix = ("..." if start > 0 else "") + text[start : match.start()]
            suffix = text[match.end() : end] + ("..." if end < len(text) else "")
            context = f"{prefix}[{match.group()}]{suffix}"

            matches.append(
                {
                    "position": match.start(),
                    "context": context,
                    "matched_text": match.group(),
                }
            )

        result["matches"] = matches
        result["match_count"] = len(matches)
        result["status"] = "success"

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result
