# Especificação Arquitetural e Guia de Replicação: Célula SRAM 6T com Bloqueio de Retenção por Inversão de Polaridade em Transistores 2D de Fósforo Negro (BP SB-FET)

**Documentação Técnica de Projeto — Mecanismo B (Colapso de Biestabilidade)**  
*Data:* November 5, 2026

---

### Abstract

Este documento estabelece a especificação técnica completa para a implementação e simulação de uma célula de memória estática de acesso aleatório de 6 transistores (SRAM 6T) baseada em transistores de efeito de campo com barreira Schottky de fósforo negro (*Black Phosphorus Schottky-Barrier FET* — BP SB-FET) com polaridade reconfigurável. O documento foi estruturado com precisão determinística para permitir que tanto engenheiros humanos quanto modelos de inteligência artificial consigam replicar a topologia, as condições de contorno de polarização e a simulação SPICE/Verilog-A sem ambiguidades.

A arquitetura implementa o **Mecanismo B de Segurança de Hardware (*Memory Locking*)**, no qual a aplicação de uma chave criptográfica incorreta ($\text{Key} = 1$) inverte dinamicamente a polaridade dos transistores dos inversores acoplados sem alterar os barramentos de alimentação ($V_{DD}$ e $V_{SS}$), destruindo o laço de realimentação positiva e impedindo a retenção do bit armazenado.

---

## 1. Visão Geral e Fundamento Físico do Dispositivo Base

A arquitetura baseia-se no dispositivo experimental demonstrado por Wu et al. (*Nature Electronics*, 2020), que utiliza flocos bidimensionais de fósforo negro (*Black Phosphorus* — BP) com contatos metálicos de Cr/Au alinhados próximos ao meio do *bandgap* ($E_g \approx 0,35\text{ eV}$ a $0,7\text{ eV}$). Devido à injeção de portadores dominada por tunelamento através de barreiras Schottky finas, o transistor apresenta comportamento ambipolar simétrico, podendo operar tanto em modo canal-p (**p-FET**) quanto em modo canal-n (**n-FET**).

Para suprimir a injeção ambipolar indesejada pelo terminal de dreno no estado desligado ($I_{\text{off}}$) e garantir uma razão $I_{\text{on}}/I_{\text{off}} \approx 10^5$ com inclinação de sublimiar (*Subthreshold Swing* — SS) de $72\text{ mV/dec}$ a $75\text{ mV/dec}$, o dispositivo incorpora uma **Porta de Polaridade (*Polarity Gate* — PG)** alinhada sob a região do dreno, além da porta de controle principal (*Top Gate* e *Bottom Gate* interconectadas).

### 1.1 Interface do Modelo Comportamental em Verilog-A (`bp_ari.va`)

Nos arquivos de simulação fornecidos com o artigo base, o transistor é modelado em Verilog-A através de uma tabela de busca (*Look-Up Table* — LUT) tetradimensional construída a partir de dados experimentais (`BP_ARI_dataN.txt` e `BP_ARI_dataP.txt`). A assinatura exata do módulo é:

```verilog
module ari (d, g, s, g1, g2);
inout d, g, s, g1, g2;
electrical d, g, s, g1, g2;
parameter real W=1; // Multiplicador linear de largura de canal
...
IdsP = $table_model(V(g1,s), V(g2,s), V(g,s), V(d,s), "BP_ARI_dataP.txt", "1LL,1LL,1LL,3LL");
IdsN = $table_model(V(g1,s), V(g2,s), V(g,s), V(d,s), "BP_ARI_dataN.txt", "1LL,1LL,1LL,3LL");

if (V(g2,s) > 0) // Opera como n-FET (NMOS)
    I(d,s) <+ 1 * IdsN * W;
if (V(g2,s) < 0) // Opera como p-FET (PMOS)
    I(d,s) <+ 1 * IdsP * W;
endmodule
```
*Listing 1: Assinatura e lógica de seleção de polaridade em bp_ari.va.*

#### 1.1.1 Definição Estrita dos 5 Terminais e Regra de Polarização

Qualquer instância SPICE do modelo `ari` deve respeitar estritamente a ordem posicional dos 5 pinos: `(d, g, s, g1, g2)`:

1. **`d` (Drain / Dreno):** Terminal conectado ao nó de saída lógica da rede de *pull-up* ou *pull-down*.
2. **`g` (Gate / Porta Principal):** Terminal que recebe o sinal lógico de controle (entrada do inversor ou linha de palavra WL).
3. **`s` (Source / Fonte):** Terminal de referência de potencial do dispositivo. **Regra Crítica:** Todas as tensões que indexam as tabelas `.txt` no comando `$table_model` são calculadas tendo o terminal `s` como referência local:
   $$V(g1, s) = V_{g1} - V_s$$
   $$V(g2, s) = V_{g2} - V_s$$
   $$V(g, s) = V_g - V_s$$
   $$V(d, s) = V_d - V_s$$
4. **`g1` (Porta Auxiliar de Ajuste / Back-Gate 1):** Terminal de polarização eletrostática auxiliar que atua na primeira dimensão da LUT para ajuste de tensão de banda plana ($V_{fb}$).
5. **`g2` (Polarity Gate / Porta de Polaridade):** Terminal determinante do tipo de portador majoritário:
   * **Condição para modo n-FET:** $V(g2, s) = V_{g2} - V_s > 0\text{ V}$. O modelo seleciona a tabela `BP_ARI_dataN.txt`. No inversor de referência (`ARI_inv.sp`), o ponto nominal de operação utiliza $V(g1, s) = +0,8\text{ V}$ e $V(g2, s) = +1,1\text{ V}$.
   * **Condição para modo p-FET:** $V(g2, s) = V_{g2} - V_s < 0\text{ V}$. O modelo seleciona a tabela `BP_ARI_dataP.txt`. No inversor de referência (`ARI_inv.sp`), o ponto nominal de operação utiliza $V(g1, s) = -1,5\text{ V}$ e $V(g2, s) = -1,5\text{ V}$.
   * **Condição Proibida/Corte ($V(g2, s) = 0\text{ V}$):** Nenhuma condicional `if` é satisfeita e a corrente de canal torna-se nula ($I_{ds} = 0$).

---

## 2. Arquitetura da Célula SRAM 6T Reconfigurável

A célula SRAM proposta é composta por 6 transistores reconfiguráveis idênticos do tipo `ari`, divididos em três blocos funcionais: dois inversores acoplados de forma cruzada (*cross-coupled inverters*) que formam o núcleo biestável de armazenamento, e dois transistores de acesso (*pass-gates*) que conectam o núcleo às linhas de bit durante operações de leitura e escrita.

### 2.1 Dicionário de Nós Elétricos (Netlist Mapping)

Para padronizar a implementação entre diferentes simuladores, os nós elétricos do circuito seguem a nomenclatura definida na Tabela 1.

| Nome do Nó | Categoria | Função na Arquitetura |
| :--- | :--- | :--- |
| `vdd` | Alimentação | Barramento de alimentação positiva fixa ($V_{DD} = 1,0\text{ V}$). |
| `vss` | Alimentação | Barramento de referência/terra fixo ($V_{SS} = 0,0\text{ V}$). |
| `q` | Interno (Estado) | Nó de armazenamento verdadeiro (*True Storage Node*). Saída do Inversor 1 e entrada do Inversor 2. |
| `qb` | Interno (Estado) | Nó de armazenamento complementar (*Complementary Storage Node*). Saída do Inversor 2 e entrada do Inversor 1. |
| `wl` | Controle Externo | *Wordline* (Linha de Palavra). Habilita os transistores de acesso XPG1 e XPG2 quando em nível alto ($1,0\text{ V}$). |
| `bl` | Dados Externos | *Bitline* verdadeira. Fornece o dado a ser escrito no nó `q`. |
| `blb` | Dados Externos | *Bitline Bar* complementar. Fornece o dado invertido a ser escrito no nó `qb`. |
| `g1_pu`, `g2_pu` | Chave (Key) | Barramentos de polaridade exclusivos para os transistores de *Pull-Up* (XPU1, XPU2). Controlados pela chave Key. |
| `g1_pd`, `g2_pd` | Chave (Key) | Barramentos de polaridade exclusivos para os transistores de *Pull-Down* (XPD1, XPD2). Controlados pela chave Key. |
| `g1_pg`, `g2_pg` | Polarização Fixa | Barramentos de polaridade fixos para manter os transistores de acesso (XPG1, XPG2) permanentemente em modo n-FET. |

*Tabela 1: Mapeamento completo dos nós elétricos da célula SRAM 6T reconfigurável.*

### 2.2 Topologia e Conectividade dos 6 Transistores

A Tabela 2 especifica a conexão pino a pino de cada um dos 6 transistores, bem como o dimensionamento da razão de aspecto ($W$) necessário para garantir simultaneamente a estabilidade de leitura (*Read Static Noise Margin* — RSNM) e a capacidade de escrita (*Write Margin*):

* **Critério de Escrita (*Writeability*):** Os transistores de acesso (XPG1, XPG2) possuem $W = 1,5$, superior ao $W = 1,0$ dos transistores de *Pull-Up* (XPU1, XPU2), permitindo sobrescrever o estado anterior quando $\text{WL} = 1$.
* **Critério de Leitura e Retenção (*Read Stability*):** Os transistores de *Pull-Down* (XPD1, XPD2) possuem $W = 2,0$, superior ao $W = 1,5$ dos transistores de acesso, evitando perturbações destrutivas no nó em nível lógico baixo.

| Instância | Papel | Pino `d` | Pino `g` | Pino `s` | Pino `g1` | Pino `g2` | $W$ | Bloco |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `XPU1` | Pull-Up 1 | `q` | `qb` | `vdd` | `g1_pu` | `g2_pu` | 1,0 | Inversor 1 |
| `XPD1` | Pull-Down 1 | `q` | `qb` | `vss` | `g1_pd` | `g2_pd` | 2,0 | Inversor 1 |
| `XPU2` | Pull-Up 2 | `qb` | `q` | `vdd` | `g1_pu` | `g2_pu` | 1,0 | Inversor 2 |
| `XPD2` | Pull-Down 2 | `qb` | `q` | `vss` | `g1_pd` | `g2_pd` | 2,0 | Inversor 2 |
| `XPG1` | Pass-Gate 1 | `q` | `wl` | `bl` | `g1_pg` | `g2_pg` | 1,5 | Acesso Esq. |
| `XPG2` | Pass-Gate 2 | `qb` | `wl` | `blb` | `g1_pg` | `g2_pg` | 1,5 | Acesso Dir. |

*Tabela 2: Tabela de conectividade pino a pino e dimensionamento ($W$) dos 6 transistores da SRAM.*

---

## 3. Especificação do Mecanismo B: Inversão de Polaridade Controlada por Chave

Diferentemente das portas polimórficas NAND/NOR do artigo original — onde os barramentos $V_{DD}$ e $V_{SS}$ são permutados juntamente com as portas de polaridade para preservar a lógica complementar de De Morgan —, o **Mecanismo B de Bloqueio de Memória** mantém os barramentos `vdd` ($1,0\text{ V}$) e `vss` ($0,0\text{ V}$) **estritamente fixos** e utiliza a chave de segurança ($\text{Key}$) exclusivamente para inverter a polaridade dos transistores internos (XPU1, XPU2, XPD1, XPD2).

### 3.1 Análise dos Estados de Operação Segundo a Chave (Key)

#### 3.1.1 Estado 1: Chave Correta ($\text{Key} = 0 \rightarrow$ Modo SRAM Funcional / Retenção Ativa)

Quando $\text{Key} = 0$, os sinais de polaridade configuram XPU1 e XPU2 como **p-FETs** e XPD1 e XPD2 como **n-FETs**:

* **Rede de Pull-Up (XPU1, XPU2):** Como os terminais de fonte (`s`) estão conectados a `vdd` ($1,0\text{ V}$), aplicam-se tensões absolutas $V(g1\_pu) = -0,5\text{ V}$ e $V(g2\_pu) = -0,5\text{ V}$. A tensão relativa vista pelo modelo é:
  $$V(g2, s)_{\text{PU}} = -0,5\text{ V} - 1,0\text{ V} = -1,5\text{ V} < 0 \implies \textbf{Modo p-FET}$$
* **Rede de Pull-Down (XPD1, XPD2):** Como os terminais de fonte (`s`) estão conectados a `vss` ($0,0\text{ V}$), aplicam-se tensões absolutas $V(g1\_pd) = +0,8\text{ V}$ e $V(g2\_pd) = +1,1\text{ V}$. A tensão relativa vista pelo modelo é:
  $$V(g2, s)_{\text{PD}} = +1,1\text{ V} - 0,0\text{ V} = +1,1\text{ V} > 0 \implies \textbf{Modo n-FET}$$
* **Resultado Físico:** Os dois inversores operam em configuração CMOS complementar clássica com ganho de tensão elevado ($A_v \approx 33,3$) e excursão completa de sinal (*rail-to-rail* de $0\text{ V}$ a $1,0\text{ V}$). A curva borboleta (*butterfly curve*) possui dois pontos estáveis bem definidos ($Q = 1, QB = 0$ e $Q = 0, QB = 1$). Quando WL retorna a $0\text{ V}$ após uma escrita, o bit é retido indefinidamente.

#### 3.1.2 Estado 2: Chave Incorreta ($\text{Key} = 1 \rightarrow$ Modo Desarmado / Colapso de Estado)

Quando $\text{Key} = 1$, a chave inverte o papel físico dos transistores sem inverter a alimentação: XPU1 e XPU2 (conectados ao `vdd`) são forçados a operar como **n-FETs**, enquanto XPD1 e XPD2 (conectados ao `vss`) são forçados a operar como **p-FETs**:

* **Rede de Pull-Up Invertida (XPU1, XPU2 viram n-FETs):** Como os terminais de fonte (`s`) permanecem em `vdd` ($1,0\text{ V}$), para obter exatamente a mesma polarização interna de $+0,8\text{ V}$ e $+1,1\text{ V}$ da tabela n-FET, somam-se $+1,0\text{ V}$ às tensões absolutas: aplicam-se $V(g1\_pu) = +1,8\text{ V}$ e $V(g2\_pu) = +2,1\text{ V}$. Assim:
  $$V(g1, s)_{\text{PU}} = 1,8\text{ V} - 1,0\text{ V} = +0,8\text{ V}$$
  $$V(g2, s)_{\text{PU}} = 2,1\text{ V} - 1,0\text{ V} = +1,1\text{ V} > 0 \implies \textbf{Modo n-FET}$$
* **Rede de Pull-Down Invertida (XPD1, XPD2 viram p-FETs):** Como os terminais de fonte (`s`) permanecem em `vss` ($0,0\text{ V}$), para obter exatamente a polarização interna de $-1,5\text{ V}$ da tabela p-FET, aplicam-se $V(g1\_pd) = -1,5\text{ V}$ e $V(g2\_pd) = -1,5\text{ V}$. Assim:
  $$V(g1, s)_{\text{PD}} = -1,5\text{ V} - 0,0\text{ V} = -1,5\text{ V}$$
  $$V(g2, s)_{\text{PD}} = -1,5\text{ V} - 0,0\text{ V} = -1,5\text{ V} < 0 \implies \textbf{Modo p-FET}$$
* **Resultado Físico (Colapso do Latch):** Com n-FETs no topo (*pull-up*) e p-FETs na base (*pull-down*), os estágios deixam de atuar como inversores regenerativos e passam a operar como seguidores de fonte degradados:
  1. Um nível alto na porta de entrada (`g`) liga o n-FET superior (conectado a `vdd`) e desliga o p-FET inferior (conectado a `vss`), puxando a saída para cima em vez de invertê-la para baixo.
  2. Além disso, o n-FET superior sofre queda de tensão de limiar ($V_{DD} - V_{th,n}$) e o p-FET inferior sofre degradação ao descarregar para $0\text{ V}$ ($|V_{th,p}|$).
  3. Consequentemente, a realimentação cruzada deixa de ser diferencial/oposta: os nós `q` e `qb` convergem para um potencial comum intermediário inválido ($V_q \approx V_{qb}$), destruindo instantaneamente qualquer bit previamente armazenado ou impedindo a retenção logo após o fechamento de WL.

#### 3.1.3 Polarização dos Transistores de Acesso (XPG1, XPG2)

Durante uma escrita, o terminal `s` de XPG1 e XPG2 (conectado a `bl` e `blb`) pode assumir até $1,0\text{ V}$. Para garantir que $V(g2, s) > 0\text{ V}$ em todos os instantes sem jamais cair na zona morta ($V(g2, s) = 0\text{ V}$), aplicam-se tensões fixas $V(g1\_pg) = +1,8\text{ V}$ e $V(g2\_pg) = +2,1\text{ V}$, assegurando que ambos operem robustamente como chaves n-FET tanto para $\text{BL} = 0$ quanto para $\text{BL} = 1$.

| Subconjunto | Pino `s` | Estado da Chave | Tensão Absoluta (`g1` / `g2`) | Tensão Relativa $V(g2, s)$ |
| :--- | :--- | :--- | :--- | :--- |
| XPU1, XPU2 | $1,0\text{ V}$ | $\text{Key} = 0$ (Seguro) | $-0,5\text{ V} / -0,5\text{ V}$ | $-1,5\text{ V} < 0$ |
| XPD1, XPD2 | $0,0\text{ V}$ | $\text{Key} = 0$ (Seguro) | $+0,8\text{ V} / +1,1\text{ V}$ | $+1,1\text{ V} > 0$ |
| XPU1, XPU2 | $1,0\text{ V}$ | $\text{Key} = 1$ (Bloqueio) | $+1,8\text{ V} / +2,1\text{ V}$ | $+1,1\text{ V} > 0$ |
| XPD1, XPD2 | $0,0\text{ V}$ | $\text{Key} = 1$ (Bloqueio) | $-1,5\text{ V} / -1,5\text{ V}$ | $-1,5\text{ V} < 0$ |
| XPG1, XPG2 | $0\text{ a }1\text{ V}$ | Independente | $+1,8\text{ V} / +2,1\text{ V}$ | $+1,1\text{ a }+2,1\text{ V} > 0$ |

*Tabela 3: Resumo exato das tensões de controle para implementação do Mecanismo B.*

---

## 4. Protocolo de Verificação e Cronograma de Simulação (30 ns)

Para validar experimentalmente ou por simulação ambos os modos em uma única execução transiente (`.tran`), o banco de testes (*testbench*) é dividido em 4 fases temporais ao longo de $30\text{ ns}$:

1. **Fase 1 ($0\text{ ns}$ a $6\text{ ns}$) — Escrita do Bit ‘1’ com Chave Correta ($\text{Key} = 0$):**
   * A chave está em $\text{Key} = 0$ (SRAM ativa).
   * Em $t = 2\text{ ns}$, WL sobe para $1,0\text{ V}$ com $\text{BL} = 1,0\text{ V}$ e $\text{BLB} = 0,0\text{ V}$.
   * Os nós internos assumem $V(q) \approx 1,0\text{ V}$ e $V(qb) \approx 0,0\text{ V}$.
2. **Fase 2 ($6\text{ ns}$ a $15\text{ ns}$) — Retenção Bem-Sucedida (*Hold* com $\text{Key} = 0$):**
   * Em $t = 6\text{ ns}$, WL fecha ($0,0\text{ V}$), isolando a célula das *Bitlines*.
   * Como $\text{Key} = 0$, o laço de realimentação mantém $V(q) = 1,0\text{ V}$ e $V(qb) = 0,0\text{ V}$ de forma estável até $15\text{ ns}$.
3. **Fase 3 ($15\text{ ns}$ a $20\text{ ns}$) — Acionamento da Chave Incorreta ($\text{Key} = 1$) e Auto-Destruição do Dado:**
   * Em $t = 15\text{ ns}$ (com $\text{WL} = 0$), as fontes de polaridade comutam para o estado $\text{Key} = 1$.
   * A inversão de p-FET/n-FET desarma o *latch* imediatamente: $V(q)$ e $V(qb)$ colapsam e convergem um em direção ao outro, apagando o bit que estava armazenado.
4. **Fase 4 ($20\text{ ns}$ a $30\text{ ns}$) — Tentativa de Escrita e Falha de Retenção sob Chave Incorreta ($\text{Key} = 1$):**
   * Entre $t = 20\text{ ns}$ e $24\text{ ns}$, WL abre novamente ($1,0\text{ V}$) tentando gravar o bit oposto ($\text{BL} = 0,0\text{ V}, \text{BLB} = 1,0\text{ V}$). Enquanto $\text{WL} = 1,0\text{ V}$, os transistores de acesso forçam a separação de tensão em `q` e `qb`.
   * Em $t = 24\text{ ns}$, WL fecha ($0,0\text{ V}$). Como a célula está com $\text{Key} = 1$, ela é incapaz de sustentar o estado gravado e os nós `q` e `qb` colapsam novamente entre $24\text{ ns}$ e $30\text{ ns}$.

---

## 5. Código Fonte SPICE Completo para Replicação (`ARI_sram_mecB.sp`)

Para executar a simulação, certifique-se de que os quatro arquivos a seguir estejam exatamente no mesmo diretório de trabalho:

1. `bp_ari.va` (Modelo Verilog-A original)
2. `BP_ARI_dataN.txt` (Tabela experimental n-FET)
3. `BP_ARI_dataP.txt` (Tabela experimental p-FET)
4. `ARI_sram_mecB.sp` (Listagem SPICE abaixo)

```spice
* ============================================================================
* PROJETO: Celula SRAM 6T Reconfiguravel com Transistores 2D de Fosforo Negro
* ARQUITETURA: Mecanismo B - Bloqueio de Retencao por Inversao de Polaridade
* ============================================================================
.hdl "bp_ari.va"

* Opcoes de convergencia calibradas para modelos baseados em LUT ($table_model)
.OP ALL
.OPTION ACCT NODE OPTS LIST LIMTIM=50
+ GMIN=1.00E-12 RELTOL=0.01 ABSTOL=1.00E-12
+ VNTOL=1.00E-06 TRTOL=7.00E+00
+ ITL1=400 ITL2=100 ITL4=100 ITL6=100
+ LVLTIM=2.00E+00 TNOM=+2.50E+01 LIMPTS=99999
+ CHGTOL=1.00E-14
+ MAXORD= .20E+01
+ METHOD=GEAR
+ DELMAX= .00E+00
+ POST
+ CONVERGE=1

.param supp=1.0

* ----------------------------------------------------------------------------
* 1. FONTES DE ALIMENTACAO FIXAS
* ----------------------------------------------------------------------------
Vdd vdd 0 supp
Vss vss 0 0

* ----------------------------------------------------------------------------
* 2. SINAIS DE POLARIDADE CONTROLADOS PELA CHAVE (KEY)
* 0ns a 15ns -> Key = 0 (Modo SRAM Normal: PU = p-FET, PD = n-FET)
* 15ns a 30ns -> Key = 1 (Modo Colapso: PU = n-FET, PD = p-FET)
* ----------------------------------------------------------------------------
* Polaridade dos Pull-Ups (Fonte em VDD = 1.0V)
Vg1_pu g1_pu 0 pwl(0n -0.5 14.9n -0.5 15.1n 1.8 30n 1.8)
Vg2_pu g2_pu 0 pwl(0n -0.5 14.9n -0.5 15.1n 2.1 30n 2.1)

* Polaridade dos Pull-Downs (Fonte em VSS = 0.0V)
Vg1_pd g1_pd 0 pwl(0n 0.8 14.9n 0.8 15.1n -1.5 30n -1.5)
Vg2_pd g2_pd 0 pwl(0n 1.1 14.9n 1.1 15.1n -1.5 30n -1.5)

* Polaridade Fixa dos Pass-Gates (Sempre em modo n-FET)
Vg1_pg g1_pg 0 1.8
Vg2_pg g2_pg 0 2.1

* ----------------------------------------------------------------------------
* 3. SINAIS DE CONTROLE E DADOS DA MEMORIA (WL, BL, BLB)
* ----------------------------------------------------------------------------
* Wordline (WL): Abre de 2ns a 6ns (Escrita 1) e de 20ns a 24ns (Escrita 0)
Vwl wl 0 pwl(0n 0 1.9n 0 2.0n 1.0 6.0n 1.0 6.1n 0 19.9n 0 20.0n 1.0 24.0n 1.0 24.1n 0 30n 0)

* Bitlines: Escrita de '1' (BL=1.0V, BLB=0.0V) de 0ns a 15ns; Escrita de '0' (BL=0.0V, BLB=1.0V) de 15ns a 30ns
Vbl bl 0 pwl(0n 1.0 19.9n 1.0 20.0n 0.0 24.0n 0.0 24.1n 1.0 30n 1.0)
Vblb blb 0 pwl(0n 0.0 19.9n 0.0 20.0n 1.0 24.0n 1.0 24.1n 0.0 30n 0.0)

* ----------------------------------------------------------------------------
* 4. INSTANCIACAO DOS 6 TRANSISTORES DA CELULA SRAM
* Ordem dos pinos do subcircuito ARI: (d, g, s, g1, g2)
* ----------------------------------------------------------------------------
* Inversor 1 (Mantem o no 'q')
XPU1 q qb vdd g1_pu g2_pu ARI W=1.0
XPD1 q qb vss g1_pd g2_pd ARI W=2.0

* Inversor 2 (Mantem o no 'qb')
XPU2 qb q vdd g1_pu g2_pu ARI W=1.0
XPD2 qb q vss g1_pd g2_pd ARI W=2.0

* Transistores de Acesso (Controlados por 'wl')
XPG1 q wl bl g1_pg g2_pg ARI W=1.5
XPG2 qb wl blb g1_pg g2_pg ARI W=1.5

* Capacitancias intrinsecas de no para estabilidade numerica de integracao
Cq q vss 1f
Cqb qb vss 1f

* ----------------------------------------------------------------------------
* 5. COMANDOS DE SIMULACAO E EXTRACAO DE METRICAS
* ----------------------------------------------------------------------------
.PRINT tran V(wl) V(bl) V(blb) V(q) V(qb) V(g2_pu) V(g2_pd) I(vdd)

.tran 10p 30ns

* Medicao da tensao retida com Chave Correta (Key = 0, em t = 12ns)
.measure tran Vq_Hold_Key0 FIND V(q) AT=12n
.measure tran Vqb_Hold_Key0 FIND V(qb) AT=12n
.measure tran DeltaV_Key0 PARAM=' abs(Vq_Hold_Key0 - Vqb_Hold_Key0) '

* Medicao do colapso de estado com Chave Incorreta (Key = 1, em t = 18ns e t = 28ns)
.measure tran Vq_Collapse1 FIND V(q) AT=18n
.measure tran Vqb_Collapse1 FIND V(qb) AT=18n
.measure tran Vq_Hold_Key1 FIND V(q) AT=28n
.measure tran Vqb_Hold_Key1 FIND V(qb) AT=28n
.measure tran DeltaV_Key1 PARAM=' abs(Vq_Hold_Key1 - Vqb_Hold_Key1) '

.end
```
*Listing 2: Netlist SPICE completa da SRAM 6T implementando o Mecanismo B (ARI_sram_mecB.sp).*

---

## 6. Critérios de Aceitação para Validação dos Resultados

Ao processar o arquivo `ARI_sram_mecB.sp` (ou sua tradução equivalente em outro ambiente de simulação), a implementação é considerada validada se satisfizer os dois critérios quantitativos abaixo extraídos pelos comandos `.measure`:

1. **Sucesso de Retenção em $\text{Key} = 0$ ($t = 12\text{ ns}$):** A diferença diferencial de tensão entre os nós internos deve superar 80% da tensão de alimentação ($\Delta V_{\text{Key0}} = |V(q) - V(qb)| > 0,8\text{ V}$), comprovando que o bit escrito entre $2\text{ ns}$ e $6\text{ ns}$ permaneceu armazenado após o fechamento de WL.
2. **Sucesso de Bloqueio/Colapso em $\text{Key} = 1$ ($t = 18\text{ ns}$ e $t = 28\text{ ns}$):** A diferença diferencial de tensão entre os nós internos deve colapsar para próximo de zero ($\Delta V_{\text{Key1}} = |V(q) - V(qb)| < 0,15\text{ V}$) ou apresentar inversão destrutiva da margem lógica logo após o fechamento de WL, comprovando que a célula perde a biestabilidade sob a chave incorreta.
