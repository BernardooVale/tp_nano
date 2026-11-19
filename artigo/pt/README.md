# Artigo Científico em LaTeX (`artigo/`)

Esta pasta reúne o projeto LaTeX estruturado para documentar todo o trabalho desenvolvido no repositório `tp_nano`.

## Estrutura do Documento

- `main.tex`: arquivo mestre com preâmbulo compatível com **MiKTeX / TeX Live / Overleaf**, cabeçalho, resumo reservado e inclusão modular das seções na ordem:
  1. **Introdução** (`secoes/01_introducao.tex`) — *placeholder estrutural (aguardando redação).*
  2. **Referencial Teórico** (`secoes/02_referencial_teorico.tex`) — *placeholder estrutural (aguardando redação).*
  3. **Metodologia** (`secoes/03_metodologia.tex`) — **redigida integralmente.**
  4. **Resultados** (`secoes/04_resultados.tex`) — **redigida integralmente.**
  5. **Conclusão** (`secoes/05_conclusao.tex`) — **redigida integralmente.**
  6. **Referências Bibliográficas** (`referencias.bib`) — contém a referência-base do dispositivo/LUT (`wu2020reconfigurable`) e modelo comentado para expansão conjunta com as seções pendentes.
- `figuras/`: cópia autocontida das 23 figuras geradas nos módulos `00` a `07` (`m00_*.png` a `m07_*.png`), tornando a pasta pronta para upload direto no Overleaf ou compilação local.

## Como Compilar Localmente

No PowerShell, a partir da pasta `artigo/`:

```powershell
pdflatex --disable-installer -interaction=nonstopmode main.tex
bibtex main
pdflatex --disable-installer -interaction=nonstopmode main.tex
pdflatex --disable-installer -interaction=nonstopmode main.tex
```

O PDF compilado será gerado em `artigo/main.pdf`.
