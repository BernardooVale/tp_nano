# Proposta de Exploração: Assimetria de Potência (DPA) em Tuplas de Portas Polimórficas com BP SB-FET

## 1. Motivação
Nos experimentos atuais (`02_portas_polimorficas_nand_nor_xor` e `03_seguranca_dpa_e_robustez`), observou-se um contraste marcante entre duas tuplas polimórficas baseadas em transistores **BP SB-FET**:
- **`(NAND, NOR)`:** assimetria de consumo de **50,3%** (vulnerável a análise diferencial de potência — DPA).
- **`(XOR, XNOR)`:** assimetria de consumo de **0,56%** (alta resistência a DPA).

Enquanto `(XOR, XNOR)` oferece excelente proteção por sua simetria topológica e tabela-verdade balanceada, ela não é funcionalmente completa sozinha. Já `(NAND, NOR)` é universal, mas expõe o modo de operação pelo consumo na linha de alimentação (`VDD`).

O objetivo desta proposta é **mapear sistematicamente o *trade-off* entre segurança (assimetria DPA) e custo de hardware** em diferentes tuplas de portas lógicas polimórficas úteis em síntese digital e segurança de hardware.

---

## 2. Tuplas Candidatas para Avaliação

| Tupla Polimórfica | Relevância / Aplicação | Expectativa de Assimetria |
| :--- | :--- | :--- |
| `(NAND, NOR)` | Referência base; portas universais de baixo custo | Alta (já medida: `50,3%`) |
| `(XOR, XNOR)` | Referência segura; cifras, mascaramento e *logic locking* | Muito baixa (já medida: `0,56%`) |
| `(AND, OR)` | Lógica de controle e caminhos de dados | Alta (tabela-verdade desbalanceada) |
| `(NAND, XNOR)` / `(NOR, XOR)` | *Logic locking* misto (confunde engenharia reversa entre lógica universal e aritmética) | Média/Alta (a investigar) |
| `(AOI, OAI)` | Células compostas padrão em síntese ASIC (economia de transistores) | Média (a investigar) |
| `(MAJ, XOR)` | Núcleo de somadores (*Full Adders*) ofuscados | Média/Baixa (a investigar) |

---

## 3. Métricas a Coletar por Tupla
Para cada tupla implementada em `ngspice` com o modelo `bp_ari_ngspice.lib`, coletar:
1. **Corretude funcional:** verificação das $2^n$ combinações de entrada para cada modo da chave (`g2`).
2. **Assimetria de potência (`DPA_asym`):** variação relativa da corrente/potência média e de pico puxada de `VDD` entre os dois modos e entre transições `0→1` / `1→0`.
3. **Custo em área:** número de transistores BP SB-FET necessários.
4. **Eficiência energética e desempenho:** potência estática, energia por chaveamento e atraso (quando capacitâncias de carga forem padronizadas).
5. **Robustez (Monte Carlo):** taxa de acerto sob variações aleatórias de parâmetros do dispositivo.

---

## 4. Plano de Implementação Sugerido
1. **Criar módulo `experimentos/07_assimetria_tuplas_logicas/`** seguindo o padrão dos módulos `02` e `03`.
2. **Definir um testbench padrão em Python + `ngspice`:** mesma tensão de alimentação (`VDD`), mesma carga capacitiva de saída e mesma rotina de extração de `I(VDD)`.
3. **Implementar as netlists** das tuplas selecionadas usando transistores `bp_ari` (`d, g, s, g1, g2`).
4. **Gerar tabela comparativa e gráfico de Pareto** (`Assimetria DPA × Nº de Transistores`), identificando quais tuplas oferecem o melhor equilíbrio entre universalidade, área e resistência a ataques de canal lateral.

---

## 5. Benchmark em Sistema: Full Adder em Três Perfis
Como extensão para circuito aritmético (aproveitando a base do módulo `05_circuito_combinacional_cripto`), avaliar três implementações de um **Full Adder** sob as mesmas condições de simulação:

| Perfil | Arquitetura | Objetivo |
| :--- | :--- | :--- |
| **1. Baseline (Comum)** | Full Adder convencional sem portas polimórficas | Referência mínima de área, atraso e energia (sem *logic locking* nem proteção DPA) |
| **2. Focado em Desempenho/Custo** | Full Adder polimórfico com tuplas compactas (ex.: `NAND/NOR`) | *Logic locking* com baixo *overhead* de transistores e atraso, aceitando maior assimetria DPA |
| **3. Focado em Baixa Assimetria** | Full Adder construído apenas com tuplas balanceadas (ex.: `XOR/XNOR`) | Máxima resistência a DPA, quantificando o custo extra em área (nº de transistores), atraso e PDP |

**Análise esperada:** comparar os três perfis em **Nº de Transistores × Atraso/PDP × Assimetria DPA**, evidenciando na prática o custo real de tornar um circuito aritmético resistente a ataques de canal lateral.
