"""Exporta v1_classica/index.html e v2_apple_design/index.html para PDFs 16:9.

Usa Microsoft Edge ou Google Chrome em modo headless, respeitando as regras
@page { size: 1280px 720px; margin: 0; } definidas em cada styles.css.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

EXPORTS = [
    (BASE_DIR / "v1_classica" / "index.html", BASE_DIR / "v1_classica" / "apresentacao_sram_2d.pdf"),
    (BASE_DIR / "v2_apple_design" / "index.html", BASE_DIR / "v2_apple_design" / "apresentacao_sram_2d_apple.pdf"),
]

BROWSER_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_browser() -> str:
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    for cmd in ("msedge", "chrome", "google-chrome", "chromium"):
        found = shutil.which(cmd)
        if found:
            return found
    raise FileNotFoundError("Microsoft Edge ou Google Chrome não encontrado para exportação PDF.")


def export_pdf(browser: str, html_path: Path, pdf_path: Path) -> None:
    if not html_path.exists():
        raise FileNotFoundError(f"Arquivo HTML não encontrado: {html_path}")
    uri = html_path.as_uri()
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--print-to-pdf-no-header",
        f"--print-to-pdf={pdf_path}",
        uri,
    ]
    print("Executando:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"Falha ao gerar PDF ({res.returncode}): {res.stderr}")
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"Arquivo PDF gerado está ausente ou vazio: {pdf_path}")
    print(f"PDF gerado com sucesso: {pdf_path} ({pdf_path.stat().st_size:,} bytes)")


def main() -> None:
    browser = find_browser()
    for html_path, pdf_path in EXPORTS:
        export_pdf(browser, html_path, pdf_path)


if __name__ == "__main__":
    main()
