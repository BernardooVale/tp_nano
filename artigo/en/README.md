# Scientific Paper in LaTeX — English Version (`artigo/en/`)

This directory contains the English-language LaTeX project documenting all work developed in the `tp_nano` repository.

## Structure

- `main.tex`: master LaTeX file compatible with **MiKTeX / TeX Live / Overleaf**, title/author/abstract placeholders, and modular section includes:
  1. **Introduction** (`sections/01_introduction.tex`) — *structural placeholder (pending drafting).*
  2. **Theoretical Background** (`sections/02_theoretical_background.tex`) — *structural placeholder (pending drafting).*
  3. **Methodology** (`sections/03_methodology.tex`) — **fully written.**
  4. **Results** (`sections/04_results.tex`) — **fully written.**
  5. **Conclusion** (`sections/05_conclusion.tex`) — **fully written.**
  6. **References** (`references.bib`) — contains the baseline device/LUT reference (`wu2020reconfigurable`) and a commented template for future additions.
- `figures/`: self-contained copy of all 23 figures generated in modules `00` to `07` (`m00_*.png` to `m07_*.png`), ready for direct Overleaf upload or local compilation.

## Local Compilation (PowerShell)

```powershell
cd c:\Users\Plusb\Documents\tp_nano\artigo\en
pdflatex --disable-installer -interaction=nonstopmode main.tex
bibtex main
pdflatex --disable-installer -interaction=nonstopmode main.tex
pdflatex --disable-installer -interaction=nonstopmode main.tex
```

The compiled PDF is generated at `artigo/en/main.pdf`.
