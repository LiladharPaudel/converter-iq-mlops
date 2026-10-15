"""Read raw documents from input-datasets/. Supports .txt, .md and .pdf.
Each document becomes {"source": filename, "text": str}."""
from pathlib import Path
from typing import Iterator
from pypdf import PdfReader
from .config import INPUT_DIR


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def load_documents(input_dir: Path = INPUT_DIR) -> Iterator[dict]:
    for path in sorted(input_dir.iterdir()):
        if path.name.startswith("."):
            continue
        if path.suffix.lower() == ".pdf":
            text = _read_pdf(path)
        elif path.suffix.lower() in (".txt", ".md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
        else:
            continue
        text = " ".join(text.split())  # normalise whitespace
        if text:
            yield {"source": path.name, "text": text}
