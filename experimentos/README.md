# Experimentos em Eletrônica 2D Reconfigurável (BP SB-FET) — Suíte Completa em `ngspice-47` + Python

Esta pasta reúne **8 módulos experimentais autônomos** executados integralmente com software aberto disponível localmente (`ngspice-47` e Python científico: `numpy`, `pandas`, `matplotlib`), substituindo integralmente a dependência original de **Synopsys HSPICE (Verilog-A)** e **MATLAB** sem perda de fidelidade física.

A suíte cobre desde a tradução do dispositivo experimental de fósforo negro de duas portas (**BP SB-FET**, Wu et al., *Nature Electronics*, 2020 — dados em [`../BPFET_Nature_Electronics`](../BPFET_Nature_Electronics) e resumo em [`../two-dimensional-transistors-reconfigurable-polarities.md`](../two-dimensional-transistors-reconfigurable-polarities.md)) até aplicações de lógica polimórfica, segurança contra ataques por canal lateral (DPA), robustez a ruído de alimentação, **SRAM 6T com bloqueio por inversão de polaridade (Mecanismo B de [`../tp_nano.md`](../tp_nano.md))** e um **Somador Completo criptográfico multiestágio**.

---

## Mapa dos Módulos Experimentais

| Pasta | Tema e Objetivo | Principais Entregas | Script |
| :--- | :--- | :--- | :--- |
| [`00_modelo_ngspice`](./00_modelo_ngspice/README.md) | Tradução da tabela Verilog-A (`bp_ari.va` + LUTs experimentais) para superfície 4D nativa em `ngspice-47` e validação cruzada vs. HSPICE (`.printtr0`). | `bp_ari_ngspice.lib`, 5 netlists `.sp`, 2 CSVs, 4 figuras | [`gerar_modelo_e_validar.py`](./00_modelo_ngspice/gerar_modelo_e_validar.py) |
| [`01_inversor_ultralow_voltage`](./01_inversor_ultralow_voltage/README.md) | Inversor CMOS 2D complementar (*VTC* e transiente) escalado de $V_{DD}=1{,}0\ \text{V}$ até $0{,}2\ \text{V}$, comparando operação direta vs. compensação $V_{fb}$. | `inv_vtc.sp`, `inv_tran.sp`, `metricas_inversor.csv`, 2 figuras | [`executar_inversor.py`](./01_inversor_ultralow_voltage/executar_inversor.py) |
| [`02_portas_polimorficas_nand_nor_xor`](./02_portas_polimorficas_nand_nor_xor/README.md) | Portas reconfiguráveis em tempo real de 4 transistores: **NAND ↔ NOR** ($0{,}8\ \text{V}$) e **XOR ↔ XNOR** ($1{,}5\ \text{V}$). | `poly_nand_nor.sp`, `poly_xor_xnor.sp`, `metricas_polimorficas.csv`, 2 figuras | [`executar_polimorficas.py`](./02_portas_polimorficas_nand_nor_xor/executar_polimorficas.py) |
| [`03_seguranca_dpa_e_robustez`](./03_seguranca_dpa_e_robustez/README.md) | Segurança contra **DPA** (assinaturas de corrente), robustez Monte Carlo 3D ($N=250$/porta), retenção temporal de tensões flutuantes e varredura $V_{DD} \times V_{SS}$ no `ngspice`. | `sim_supply_noise.sp`, 3 CSVs, 4 figuras (substituindo `m_code/*.m`) | [`analisar_dpa_e_robustez.py`](./03_seguranca_dpa_e_robustez/analisar_dpa_e_robustez.py) |
| [`04_sram_6t_memory_locking`](./04_sram_6t_memory_locking/README.md) | Implementação do **Mecanismo B de `tp_nano.md`**: SRAM 6T ($30\ \text{ns}$, 4 fases), curvas borboleta / SNM em `Key=0` vs. `Key=1`, diagnóstico de *Read Disturb* e recuperação via *Wordline Read-Assist*. | `ARI_sram_mecB_ngspice.sp`, `sram_butterfly_snm.sp`, `metricas_sram_6t.csv`, 2 figuras | [`executar_sram_6t.py`](./04_sram_6t_memory_locking/executar_sram_6t.py) |
| [`05_circuito_combinacional_cripto`](./05_circuito_combinacional_cripto/README.md) | **Somador Completo 1-bit polimórfico (28 transistores)** com ofuscação por chave de 2 bits $(K_1, K_0)$, matriz de tabela-verdade e Distância de Hamming. | `full_adder_polimorfico.sp`, `tabelas_verdade_full_adder.csv`, 2 figuras | [`executar_full_adder.py`](./05_circuito_combinacional_cripto/executar_full_adder.py) |
| [`06_fronteira_tensao_nao_padronizada`](./06_fronteira_tensao_nao_padronizada/README.md) | Varredura de tensões não-padronizadas ($V_{DD} \times V_{in} \times V(g2,s)$ dentro da LUT medida) em **NAND/NOR** e **XOR/XNOR** para mapear conversão de função, travamentos e região indefinida. | `3` netlists `.sp`, `2` CSVs (`292` pontos), `3` mapas de fase PNG | [`executar_varredura_tensoes.py`](./06_fronteira_tensao_nao_padronizada/executar_varredura_tensoes.py) |
| [`07_assimetria_tuplas_logicas`](./07_assimetria_tuplas_logicas/README.md) | Mapeamento sistemático de *trade-off* (**Assimetria DPA × Área × Atraso/PDP × Monte Carlo**) em **7 tuplas polimórficas** + Benchmark de **Full Adder 1-bit em 3 Perfis**. | `4` netlists `.sp`, `3` CSVs, `4` figuras (Pareto, DPA, MC, Perfis FA) | [`executar_assimetria_tuplas.py`](./07_assimetria_tuplas_logicas/executar_assimetria_tuplas.py) |

---

## Resumo Consolidado dos Resultados Validados

| Módulo | Indicador Principal | Resultado Obtido |
| :--- | :--- | :--- |
| **00 — Modelo `ngspice` (v2 4D)** | Erro vs. LUTs + Validação Cruzada vs. HSPICE (`.printtr0`) | LUT: **`0,0621%`** (*n*) / **`0,0032%`** (*p*); HSPICE `P_output` $\text{RMSE}$ caiu **196×** ($0{,}5901 \to \mathbf{0{,}0030\ \mu\text{A}}$, $R^2=0{,}99977$); `N/P_transfer` $R^2 \ge 0{,}99994$ |
| **00 — Dispositivo** | $I_{\mathrm{on}}$, $I_{\mathrm{off}}$ e $SS_{\min}$ | *n-FET* ($V_{g1}=1{,}1\ \text{V}$): $1{,}65\ \mu\text{A}/\mu\text{m}$, $0{,}596\ \text{nA}/\mu\text{m}$, $106{,}59\ \text{mV/dec}$<br>*p-FET* ($V_{g1}=-1{,}5\ \text{V}$): $1{,}79\ \mu\text{A}/\mu\text{m}$, $2{,}811\ \text{nA}/\mu\text{m}$, $148{,}08\ \text{mV/dec}$ |
| **01 — Inversor 2D** | Ganho DC máximo e excursão com alinhamento $V_{fb}$ | Ganho **`54,69`** ($1{,}0\ \text{V}$) até **`2,71`** ($0{,}2\ \text{V}$); excursão **`99,6%`** ($1{,}0\ \text{V}$) a **`89,8%`** ($0{,}2\ \text{V}$) |
| **02 — Portas Polimórficas** | Acurácia em comutação dinâmica ($4 \times 4 = 16$ vetores) | **`16/16` (100%)**: NAND/NOR em $0{,}8\ \text{V}$ (`'1'` $\ge 0{,}701\ \text{V}$, `'0'` $\le 0{,}013\ \text{V}$); XOR/XNOR em $1{,}5\ \text{V}$ (`'1'` $=1{,}465\ \text{V}$, `'0'` $=0{,}002\ \text{V}$) |
| **03 — DPA & Robustez** | Camuflagem de corrente, Monte Carlo ($N=250$) e ruído $V_{DD}\times V_{SS}$ | Pico DPA XOR vs. XNOR: `1,80 µA` vs. `1,79 µA` (**`0,56%`** de diferença); **`100%`** MC; margem `ngspice` $0{,}531\text{–}1{,}012\ \text{V}$ ($0{,}153\ \text{V}$ no canto extremo $0{,}65/{-}0{,}10\ \text{V}$) |
| **04 — SRAM 6T (Mec. B)** | Retenção `Key=0` ($V_{g2,\mathrm{PU}}=-0{,}2\ \text{V}$), Colapso `Key=1`, Hold/Read SNM | $\Delta V_{\mathrm{Key0}} = \mathbf{0{,}975\ \text{V}}$ ($>0{,}80\ \text{V}$); $\Delta V_{\mathrm{Collapse1}} = \mathbf{0{,}084\ \text{V}}$ e $\Delta V_{\mathrm{Key1}} = \mathbf{0{,}076\ \text{V}}$ ($<0{,}15\ \text{V}$); $\mathrm{SNM}_{\mathrm{Hold}} = \mathbf{167{,}1\ \text{mV}}$; *Read-Assist* $\mathrm{WL}=0{,}30\ \text{V}$ ($\mathbf{66{,}2\ \text{mV}}$) |
| **05 — Full Adder Cripto** | Tabela-verdade em `K=00` e Distância de Hamming | **`100%` exato** em `K=00` (`Sum` $\ge 1{,}413\ \text{V}$ / $\le 0{,}001\ \text{V}$; `Cout` $\ge 0{,}753\ \text{V}$ / $\le 0{,}012\ \text{V}$); corrupção em todas as chaves erradas (`HD_Total` = **`68,75%`** em `01`, **`18,75%`** em `10`, **`50,0%`** em `11` com `HD_Sum = 100%`) |
| **06 — Fronteira de Tensões** | Classificação booleana fora do ponto nominal (`292` pontos) | Conversão espontânea **`NAND → NOR`** em $V_{DD}=0{,}65\ \text{V}$ (`+0,4/-1,1 V`); travamentos `CONST_0`/`CONST_1` e fronteiras analógicas `X`; faixa ótima P/N em $V(g2,s)_p \in \{-1{,}35;\ -1{,}20\}\ \text{V}$ |
| **07 — Assimetria em Tuplas & FA** | Fronteira de Pareto DPA (`7` tuplas) e Full Adder (`3` perfis) | `100%` tabela-verdade (`72/72`); DPA pico: **`0,00%`** `(XOR, XNOR)`, **`0,04%`** `(MAJ3, XOR3)`, **`1,16%`** `(NOR, XOR)` vs. **`163,91%`** `(NAND, NOR)`; FA Perfil 3 reduz DPA no *carry* de **`113,83% → 0,04%`** com PDP **`3,01×`** menor que Perfil 2 |

---

## Metodologia de Substituição de Ferramentas (HSPICE + MATLAB → `ngspice-47` + Python)
1. **Verilog-A `$table_model` → Superfície 4D PWL Refinada em `ngspice-47`:**
   O modelo original [`bp_ari.va`](../BPFET_Nature_Electronics/BP_SBFET_MODEL/bp_ari.va) interpolava tabelas experimentais (`BP_ARI_dataN.txt`, `BP_ARI_dataP.txt`) via `$table_model`, recurso restrito ao HSPICE. No Módulo `00`, reconstruímos integralmente as superfícies 2D $(V_{g1}, V_{g2})$ (28 fatias n-FET e 32 fatias p-FET, incluindo o regime $V_{g2}=-1{,}5\ \text{V}$) e fatores 2D $(V_{tg}, V_{ds})$ contínuos e ímpares com detecção bilateral de fonte (`min(v(d),v(s))` e `max(v(d),v(s))`), preservando exatamente os 5 pinos `(d g s g1 g2)` e o parâmetro `W` com validação cruzada direta contra os arquivos `.printtr0` do HSPICE.
2. **Scripts `.m` de Pós-Processamento → Python Científico:**
   Todos os gráficos e métricas estatísticas originalmente descritos em `BPFET_Nature_Electronics/m_code/*.m` foram reproduzidos e corrigidos quanto a inconsistências de cabeçalho/delimitadores diretamente em Python (`numpy`, `pandas`, `matplotlib`).

---

## Como Reproduzir Toda a Suíte
A partir da raiz do projeto (`tp_nano`), execute o orquestrador único:

```powershell
python experimentos/run_all.py
```

O script executa sequencialmente os módulos `00` a `07`, re-simula todos os netlists no `ngspice_con.exe`, recalcula métricas/figuras e valida automaticamente a presença e integridade dos 66 artefatos principais gerados nas subpastas.

---

## Estrutura de Pastas

```text
experimentos/
├── run_all.py
├── README.md
├── 00_modelo_ngspice/
├── 01_inversor_ultralow_voltage/
├── 02_portas_polimorficas_nand_nor_xor/
├── 03_seguranca_dpa_e_robustez/
├── 04_sram_6t_memory_locking/
├── 05_circuito_combinacional_cripto/
├── 06_fronteira_tensao_nao_padronizada/
└── 07_assimetria_tuplas_logicas/
```
