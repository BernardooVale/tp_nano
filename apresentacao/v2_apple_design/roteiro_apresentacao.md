# Roteiro de Apresentação e Preparação (Q&A)

**Apresentação:** *SRAM 6T Polimórfica com Transistores 2D para Segurança de Hardware*  
**Estrutura:** 4 Seções · 12 Slides

---

## 1. Introdução e Background (Slides 1, 2 e 3)

### O que estudar
- **Ameaças à SRAM CMOS convencional:**
  - *Remanência / Cold-Boot*: retenção residual de carga permite extrair chaves criptográficas por resfriamento ou microprobing.
  - *Delayering Óptico / SEM*: a dopagem química fixa (nMOS vs. pMOS) revela a função lógica da célula sob microscopia.
  - *Supply-Pin Clamping*: fixar os pinos externos de alimentação ($V_{DD}$ / $V_{SS}$) neutraliza defesas baseadas em corte de energia.
- **Física do BP SB-FET 2D (5 terminais):**
  - Canal intrínseco de Fósforo Negro (BP) sem dopagem química, com contatos Schottky (Cr/Au).
  - Papel das portas: porta principal ($g$), porta auxiliar ($g_1$) e porta de polaridade ($g_2$).
  - Regra de polaridade: $V(g_2, s) > 0 \Rightarrow \text{n-FET}$ (elétrons); $V(g_2, s) \le 0 \Rightarrow \text{p-FET}$ (lacunas).
- **Mecanismo B na SRAM 6T:**
  - Trilhos $V_{DD} = 1{,}0\text{ V}$ e $V_{SS} = 0{,}0\text{ V}$ permanecem fixos.
  - `Key=0`: `PU` = p-FET e `PD` = n-FET (operação CMOS biestável, $\text{SNM} > 0$).
  - `Key=1`: `PU` = n-FET e `PD` = p-FET (seguidores de fonte, sem ganho regenerativo, $\text{SNM} = 0\text{ mV}$).

### O que falar
- **Slide 1 (Capa):** Apresentar o título, os autores (UFMG), a ideia central (usar transistores 2D reconfiguráveis para proteger dados em SRAM 6T sem área extra) e o roteiro das 4 seções.
- **Slide 2 (Motivação e Contribuições):** Explicar as 3 falhas da SRAM CMOS tradicional e contrastar na tabela como a SRAM 6T 2D resolve isso mantendo trilhos fixos, zero transistores extras e camuflagem física. Fechar com as 3 contribuições principais (modelo aberto, *retention locking* e *read-assist*).
- **Slide 3 (Física do Dispositivo):** Apontar no diagrama do BP SB-FET como a porta $g_2$ define o tipo de portador sem dopagem. Em seguida, contrastar `Key=0` (lóbulos abertos) com `Key=1` (inversão de `PU`/`PD` levando ao colapso monostável).

### Perguntas prováveis e como responder
- **"Por que não usar simplesmente corte de alimentação (power gating) para apagar a SRAM?"**  
  *Resposta:* Um atacante físico pode grampear os pinos externos de $V_{DD}/V_{SS}$ (*supply-pin clamping*) ou resfriar o chip (*cold-boot*). Como nossa célula mantém $V_{DD}$ e $V_{SS}$ fixos e apaga o dado internamente pela porta $g_2$, o bloqueio de pinos externos não impede a zeroização.
- **"Há custo de área por célula?"**  
  *Resposta:* Não. A topologia continua sendo exatamente 6 transistores (6T), sem transistores adicionais nem lógica de limpeza por célula.

---

## 2. Trabalhos Relacionados (Slide 4)

### O que estudar
- **Evolução histórica:**
  - *RFETs 1D (CNTFETs e nanofios de Si/Ge)*: provaram o conceito de transistor reconfigurável, mas sofrem com alinhamento e variabilidade de contatos em memórias densas.
  - *Materiais 2D (TMDs, WSe₂, MoTe₂, BP)*: canais atômicos sem *dangling bonds*, melhor controle eletrostático e viabilidade para SRAM 2D/3D.
  - *Segurança Polimórfica*: integração de *logic locking* e camuflagem de layout contra ataques SAT, *delayering* e DPA.
- **Diferenciais diretos frente à literatura (especialmente Wu et al. / fluxo HSPICE):**
  - Fluxo 100% open-source (`ngspice-47` + Python) vs. ferramentas proprietárias.
  - Modelo 4D completo em $V_{g2} = -1{,}5\text{ V}$ (redução de $196\times$ no erro).
  - Protocolo transiente completo em 4 fases, análise estática de SNM com sintonia de banda plana ($\Delta V_{fb}$) e mitigação de *Read Disturb* via *WL Underdrive*.

### O que falar
- **Slide 4:** Resumir a linha evolutiva nos 3 cards superiores (1D $\rightarrow$ 2D $\rightarrow$ Segurança Polimórfica) e usar a tabela inferior para mostrar claramente o que faltava na literatura e o que este trabalho entrega de novo em cada aspecto técnico.

### Perguntas prováveis e como responder
- **"Qual a principal vantagem de migrar de nanofios 1D para materiais 2D como o Fósforo Negro?"**  
  *Resposta:* Materiais 2D oferecem espessura atômica uniforme sem *dangling bonds* na interface, reduzindo a variabilidade de contato e permitindo melhor escalabilidade em arranjos de memória.
- **"O que o trabalho de vocês faz que o modelo original de Wu et al. não fazia?"**  
  *Resposta:* Além de portar tudo para um fluxo aberto (`ngspice-47`), corrigimos a extrapolação em $V_{g2} = -1{,}5\text{ V}$ com a superfície 4D real, quantificamos a SNM estática considerando o desvio de banda plana e resolvemos o *Read Disturb* com *WL Underdrive*.

---

## 3. Metodologia (Slides 5 e 6)

### O que estudar
- **Pipeline de tradução do modelo 4D (`bp_ari_ngspice.lib v2`):**
  - Entrada: tabelas experimentais 4D (`BP_ARI_dataN.txt` e `BP_ARI_dataP.txt`).
  - Referência bilateral de fonte: usa `min(Vd, Vs)` para n-FET e `max(Vd, Vs)` para p-FET, garantindo simetria quando dreno e fonte trocam de papel nos *pass-gates* (`PG`).
  - Superfície 4D completa: inclui o plano real de $V_{g2} = -1{,}5\text{ V}$, capturando o desvio de banda plana ($\Delta V_{fb} = -0{,}25\text{ V}$).
  - Estabilidade numérica (MNA): limites monotônicos ($\pm 1000\text{ V}$) e resistência parasita controlada evitam falhas de convergência no SPICE.
- **Arquitetura 6T e Protocolos:**
  - Dimensionamento relativo: `PU` ($W=1{,}0$), `PD` ($W=2{,}0$), `PG` ($W=1{,}5$).
  - Protocolo transiente de 30 ns em 4 fases: Escrita (`0–6 ns`), Retenção (`6–15 ns`), Auto-Destruição (`15–20 ns`) e Bloqueio de Escrita (`20–30 ns`).
  - Varredura DC de Curva Borboleta (SNM) para `Key ∈ {0, 1}` e `WL ∈ {0; 0,30; 1,0} V`.

### O que falar
- **Slide 5 (Pipeline 4D):** Explicar os 4 passos no topo (Tabelas $\rightarrow$ Simetria $\rightarrow$ Superfície 4D $\rightarrow$ `.subckt ARI v2`) e destacar nos 3 cards inferiores por que o modelo funciona na SRAM: simetria em *pass-gates*, captura real de $-1{,}5\text{ V}$ e convergência estável.
- **Slide 6 (Arquitetura 6T):** Mostrar no esquemático que os trilhos $V_{DD}/V_{SS}$ são fixos e a chave atua só em $g_1/g_2$. Apontar na tabela a troca de polaridade entre `Key=0` e `Key=1` e resumir as 4 fases do teste de 30 ns + análise de SNM.

### Perguntas prováveis e como responder
- **"Por que a referência bilateral (`min/max`) é tão importante na SRAM?"**  
  *Resposta:* Nos transistores de acesso (*pass-gates*), o sentido da corrente muda entre leitura e escrita, trocando qual terminal é fonte e qual é dreno. Sem a referência bilateral, haveria descontinuidade numérica e erro físico na simulação.
- **"O modelo inclui capacitâncias intrínsecas?"**  
  *Resposta:* As tabelas experimentais originais são quase-estáticas. Para a simulação transiente, compensamos com capacitâncias nodais externas fixas ($C_q = C_{qb} = 1{,}0\text{ fF}$).

---

## 4. Resultados e Conclusão (Slides 7, 8, 9, 10, 11 e 12)

### O que estudar
- **Validação Cruzada (Slide 7):**
  - `ngspice-47 v2` vs. Synopsys HSPICE: redução de $196\times$ no RMSE de saída p-FET em $-1{,}5\text{ V}$ ($R^2 = 0{,}99977$).
- **Física de $V_{g2}$ e Banda Plana (Slide 8):**
  - Erro médio vs. LUTs: $0{,}062\%$ (n-FET) e $0{,}003\%$ (p-FET).
  - Em $V_{g2} = -1{,}5\text{ V}$, o p-FET sofre deslocamento $\Delta V_{fb} \approx -0{,}25\text{ V}$ e perde força; sintonizar para $V_{g2,PU} = -0{,}2\text{ V}$ recupera a simetria.
- **Transiente de 30 ns (Slide 9):**
  - `Key=0` retém $\Delta V = 0{,}975\text{ V}$.
  - Ao ativar `Key=1` em $15\text{ ns}$, $\Delta V$ colapsa $>91\%$ em $<3\text{ ns}$ ($0{,}084\text{ V}$) e novas tentativas de escrita falham ($0{,}076\text{ V}$).
- **Curvas Borboleta e Read-Assist (Slide 10):**
  - Sintonia de $V_{g2,PU}$ de $-0{,}5\text{ V}$ para $-0{,}2\text{ V}$ eleva $\text{SNM}_{\text{Hold}}$ de $49{,}4\text{ mV}$ para $167{,}1\text{ mV}$.
  - Leitura com $WL = 1{,}0\text{ V}$ causa *Read Disturb* ($\text{SNM} = 0\text{ mV}$); reduzir para $WL = 0{,}30\text{ V}$ (*Wordline Underdrive*) recupera $66{,}2\text{ mV}$.
  - Em `Key=1`, a SNM é $0{,}00\text{ mV}$ em todos os regimes.
- **Matriz Consolidada e Conclusões (Slides 11 e 12):**
  - Todas as metas de aceitação foram cumpridas.
  - Limitações: escopo quase-estático e lacuna experimental em $V(g_2, s) \in (-0{,}90; +0{,}20)\text{ V}$.
  - Trabalhos futuros: redes capacitivas parasitas, variabilidade estatística e arranjos multi-célula (2×2, 4×4).

### O que falar
- **Slide 7:** Destacar no gráfico a sobreposição quase perfeita com o HSPICE e a redução de $196\times$ no erro de saída p-FET.
- **Slide 8:** Mostrar nos dois gráficos a aderência às tabelas experimentais e explicar o impacto do $\Delta V_{fb}$ na escolha de $V_{g2,PU} = -0{,}2\text{ V}$.
- **Slide 9:** Percorrer visualmente o gráfico de 30 ns da esquerda para a direita: escrita $\rightarrow$ retenção estável $\rightarrow$ queda abrupta em $<3\text{ ns}$ ao ligar `Key=1` $\rightarrow$ tentativa de sobrescrita bloqueada.
- **Slide 10:** Mostrar no gráfico os lóbulos abertos em `Key=0` (Hold e Read-Assist com $WL = 0{,}30\text{ V}$) contrastando com o colapso total em `Key=1` ($\text{SNM} = 0$).
- **Slide 11:** Usar a tabela resumida para confirmar que todos os critérios passaram e reforçar os 3 ganhos de segurança (zero área extra, imunidade a *clamping* e apagamento $<3\text{ ns}$).
- **Slide 12:** Fechar com a síntese dos 3 resultados principais, reconhecer com transparência as 2 limitações atuais e apontar os próximos passos.

### Perguntas prováveis e como responder
- **"Por que ocorre Read Disturb com WL = 1,0 V e como o Read-Assist resolve sem transistores extras?"**  
  *Resposta:* Como os *pass-gates* têm largura $W_{PG}=1{,}5$, eles são fortes o suficiente para puxar o nó armazenado em `0` durante a leitura com $WL=1{,}0\text{ V}$. Reduzir $WL$ para $0{,}30\text{ V}$ enfraquece a condução do *pass-gate* apenas o necessário para preservar o dado, recuperando $66{,}2\text{ mV}$ de SNM sem alterar a célula.
- **"Qual é o próximo passo mais importante para validar o conceito em circuito maior?"**  
  *Resposta:* Simular arranjos multi-célula (2×2 e 4×4) com capacitâncias parasitas dependentes de polarização para avaliar *Write Margin*, atraso de leitura e possíveis correntes parasitas em linhas de bits (*sneak paths*).
