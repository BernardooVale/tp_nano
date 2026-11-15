# Contexto do Projeto (`tp_nano`) — Guia Rápido para LLM

Este arquivo resume o repositório para dar contexto mínimo e preciso a uma LLM (sem acesso ao agente local) auxiliar na continuidade do desenvolvimento.

## 1. Objetivo e Origem
- **Tema:** Simulação e validação de circuitos digitais e de segurança de hardware baseados em transistores **Black Phosphorus Schottky-Barrier FET (BP SB-FET)** de polaridade reconfigurável (`d, g, s, g1, g2`).
- **Base teórica:** Artigo em `two-dimensional-transistors-reconfigurable-polarities.md` e proposta do grupo em `tp_nano.md`.
- **Adaptação de ferramentas:** Os arquivos originais em `BPFET_Nature_Electronics/` dependem de **HSPICE + Verilog-A (`bp_ari.va` com `$table_model` 4D)** e **MATLAB** (indisponíveis). Tudo foi portado para **Python + `ngspice-47`** (portátil em `ngspice-47_64/`).

## 2. Estrutura do Repositório
- `two-dimensional-transistors-reconfigurable-polarities.md`: artigo de referência (Nature Electronics).
- `tp_nano.md`: ideia e escopo inicial do trabalho.
- `BPFET_Nature_Electronics/`: dados experimentais (`BP_ARI_dataN.txt`, `BP_ARI_dataP.txt`), modelo Verilog-A (`bp_ari.va`), netlists HSPICE e saídas `.printtr0` de referência.
- `ngspice-47_64/`: executável do simulador (`Spice64/bin/ngspice_con.exe`).
- `requirements.txt` e `.venv/`: ambiente Python isolado (`numpy`, `pandas`, `matplotlib`).
- `experimentos/`: suíte completa em Python + `ngspice`. Comando mestre: `.venv\Scripts\python.exe experimentos/run_all.py` (executa todos os 6 módulos e valida 45 artefatos).
  - `00_modelo_ngspice/`: `gerar_modelo_e_validar.py` gera `bp_ari_ngspice.lib` (modelo v2: superfície bilinear 2D `(Vg1, Vg2)` + curvas `pwl(Vds)` por `Vtg`) e faz validação cruzada automática contra `.printtr0` do HSPICE (`validacao_cruzada_hspice.csv`, `R² > 0,9997` em `N_transfer`, `P_transfer` e `P_output`; `0,928` em `N_output` devido a deslocamento de lote nos próprios dados `BP_ARI_dataN.txt`).
  - `01_inversor_ultralow_voltage/`: inversor `0,2–1,0 V` (versão compensada atinge ganho `54,69` em `1,0 V` e excursão `≥ 89,75%` até `0,2 V`).
  - `02_portas_polimorficas_nand_nor_xor/`: portas NAND/NOR (`0,8 V`) e XOR/XNOR (`1,5 V`), `16/16` casos corretos.
  - `03_seguranca_dpa_e_robustez/`: análise DPA (`0,56%` assimetria em XOR/XNOR vs. `50,3%` em NAND/NOR), Monte Carlo (`100%` acerto em `N=250`/célula) e varredura `VDD × VSS` no `ngspice`.
  - `04_sram_6t_memory_locking/`: SRAM 6T com *memory locking* por polaridade (`Key=0` com `Vg2_pu=-0,2 V` dá `SNM_Hold=167,12 mV` e `SNM_Read_Assist=66,23 mV`; `Key=1` colapsa retenção para `0,0 mV`).
  - `05_circuito_combinacional_cripto/`: Full Adder 28T com *logic locking* (`K=00` 100% correto; `K!=00` gera `HD` entre `18,75%` e `68,75%`).

## 3. Regras e Restrições Técnicas (Importante ao Modificar Código)
1. **Execução:** sempre validar mudanças rodando `python experimentos/run_all.py`. Cada pasta `00`..`05` possui seu próprio `README.md` detalhado e CSVs de métricas.
2. **Edição do modelo:** nunca editar `bp_ari_ngspice.lib` diretamente; alterar `experimentos/00_modelo_ngspice/gerar_modelo_e_validar.py` e rodar o gerador.
3. **Convergência no `ngspice-47`:** manter *clamping* plano em `±1000 V` nas funções `pwl(...)`, inclinação não nula em `Vds=0` e evitar criar nós `B` intermediários extras em circuitos grandes (como o Full Adder 28T) para não inflar a matriz MNA.
4. **Limitação conhecida do modelo original:** `bp_ari.va` é quase-estático (modela apenas `I(d,s)`, sem capacitâncias intrínsecas); tempos transitórios dependem das capacitâncias de carga adicionadas nos testbenches.

## 4. Como Rodar os Experimentos
No PowerShell, na raiz `tp_nano`:
```powershell
# 1. Criar/ativar venv (apenas na primeira vez em outra máquina)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Rodar toda a suíte (6 módulos + checagem dos 45 artefatos)
.\.venv\Scripts\python.exe experimentos\run_all.py

# 3. Ou rodar um módulo isolado (ex.: módulo 04)
.\.venv\Scripts\python.exe experimentos\04_sram_6t_memory_locking\executar_sram_6t.py
```

## 5. Pontos de Adição, Melhorias e Exploração
- **Capacitâncias e Métricas Dinâmicas (`00`, `01`, `02`):** adicionar capacitâncias parasitas (`Cgs`, `Cgd`, `Cg2s`) no modelo para extrair atraso (`tpLH`/`tpHL`), energia por chaveamento e PDP realistas.
- **SRAM em Matriz e Escrita (`04`):** medir *Write Margin* (além de Hold/Read SNM) e expandir a célula 6T para uma matriz (`2×2` ou `4×4`) verificando *sneak paths* e retenção sob `Key=0/1`.
- **DPA e Monte Carlo 100% no `ngspice` (`03`):** converter a análise DPA de XOR/XNOR e a variação estatística para simulações transientes nativas no `ngspice` com variabilidade de `Vfb` e `W`.
- **Escala Lógica e Ataques (`05`):** encadear o Full Adder 28T em um somador *ripple-carry* de 4 bits ou ULA polimórfica, e testar resistência a ataques de sensibilização/SAT com chaves maiores.
- **Exploração Paramétrica:** varrer razão de larguras `W`, temperatura (`.temp`) e *sub-threshold* (`VDD < 0,4 V`) para mapear fronteiras de operação.
