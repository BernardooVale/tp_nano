# Roteiro de Apresentação e Preparação (Q&A)

**Apresentação:** *SRAM 6T Polimórfica com Transistores 2D para Segurança de Hardware*  
**Estrutura:** 4 Seções · 12 Slides

---

## 0. O que TODOS devem saber (Base Comum do Grupo)

Independentemente de qual seção você vai apresentar, todo integrante do grupo precisa dominar os conceitos abaixo para garantir coesão na fala e segurança na banca de perguntas (Q&A):

- **Qual é o problema e qual é a solução?**
  - **Problema:** A SRAM CMOS tradicional é vulnerável a ataques físicos (*Cold-Boot*/remanência de carga, *Delayering* óptico/SEM que distingue nMOS de pMOS pela dopagem, e *Supply-Pin Clamping* que neutraliza o corte de energia).
  - **Solução:** Uma célula **SRAM 6T polimórfica** baseada em transistores 2D de Fósforo Negro (**BP SB-FET**), que permite alternar dinamicamente entre retenção normal (`Key=0`) e autodestruição/bloqueio (`Key=1`) **sem adicionar transistores extras** e **mantendo $V_{DD} = 1{,}0\text{ V}$ e $V_{SS} = 0{,}0\text{ V}$ fixos**.
- **Como funciona o transistor BP SB-FET (5 terminais)?**
  - Canal intrínseco de Fósforo Negro (sem dopagem química fixa) com contatos Schottky (Cr/Au).
  - Porta principal ($g$) controla a condução; porta auxiliar ($g_1$) atua no controle eletrostático/acoplamento; **porta de polaridade ($g_2$)** define se o dispositivo se comporta como n-FET ou p-FET:
    - $V(g_2, s) > 0 \Rightarrow \text{n-FET}$ (condução por elétrons).
    - $V(g_2, s) \le 0 \Rightarrow \text{p-FET}$ (condução por lacunas).
- **Como funciona a chave `Key=0` vs. `Key=1` (Mecanismo B)?**
  - **`Key=0` (Modo Seguro / Retenção):** `PU` atua como p-FET e `PD` como n-FET (inversores CMOS acoplados em cruz, biestáveis, $\text{SNM} > 0$).
  - **`Key=1` (Modo Autodestruição / Bloqueio):** `PU` e `PD` invertem suas polaridades (`PU` vira n-FET e `PD` vira p-FET). Os inversores viram seguidores de fonte sem ganho regenerativo, colapsando a célula para um estado monostável ($\text{SNM} = 0\text{ mV}$) e apagando o dado.
- **Números-chave que todos devem ter na ponta da língua:**
  - **Precisão do modelo aberto (`ngspice-47 v2`):** redução de **$196\times$** no RMSE de saída p-FET em $V_{g2} = -1{,}5\text{ V}$ ($R^2 = 0{,}99977$).
  - **Transiente de apagamento:** retenção estável $\Delta V = 0{,}975\text{ V}$ em `Key=0`; ao ativar `Key=1`, colapso **$>91\%$ em $<3\text{ ns}$** ($\Delta V = 0{,}084\text{ V}$), com bloqueio de novas escritas ($0{,}076\text{ V}$).
  - **Estabilidade (SNM):** $\text{SNM}_{\text{Hold}} = 167{,}1\text{ mV}$ (após sintonia de $V_{g2,PU} = -0{,}2\text{ V}$); *Read-Assist* com *WL Underdrive* ($WL = 0{,}30\text{ V}$) recupera **$\text{SNM}_{\text{Read}} = 66{,}2\text{ mV}$** (contra $0\text{ mV}$ em $WL = 1{,}0\text{ V}$).
- **Dinâmica de equipe e Q&A:**
  - Ao terminar sua seção, faça uma **transição explícita** para o próximo colega (ex.: *"Agora que vimos a motivação e a física do dispositivo, o [Nome] vai mostrar como isso se compara aos trabalhos relacionados..."*).
  - Se uma pergunta da banca cair sobre outra seção, responda o conceito geral e convide o responsável pela seção para detalhar os números.

---

## 1. Introdução e Background (Slides 1, 2 e 3)

### O que o apresentador desta seção deve saber (Conteúdo Aprofundado)
- **Ameaças detalhadas à SRAM CMOS convencional:**
  - *Remanência / Cold-Boot*: mesmo após desligar a alimentação, cargas residuais nos nós de armazenamento permanecem por segundos ou minutos em baixas temperaturas, permitindo extrair chaves criptográficas.
  - *Delayering Óptico / SEM*: um atacante remove camadas do chip e usa microscopia eletrônica para identificar regiões dopadas $n^+$ e $p^+$, revelando a função lógica fixa da célula. No BP SB-FET não há dopagem química — `PU` e `PD` são fisicamente idênticos até a polarização de $g_2$, garantindo **camuflagem física**.
  - *Supply-Pin Clamping*: se a defesa depender de cortar $V_{DD}$ ou aterrar $V_{SS}$, o atacante pode grampear os pinos externos do encapsulamento para forçar a alimentação e manter o dado vivo. Nossa célula não desliga os trilhos: a zeroização ocorre internamente via $g_2$.
- **Física do BP SB-FET 2D (5 terminais) e por que ele é ideal:**
  - Contatos Schottky (Cr/Au) sobre canal intrínseco de Fósforo Negro (BP) permitem injeção ambipolar (elétrons ou lacunas) dependendo da altura da barreira modulada por $g_2$.
  - Papel de cada terminal: dreno ($d$), fonte ($s$), porta principal ($g$), porta auxiliar ($g_1$) e porta de polaridade ($g_2$).
- **Mecanismo B na SRAM 6T (por que a célula colapsa em `Key=1`):**
  - Em `Key=0`: `PU` = p-FET e `PD` = n-FET. O par de inversores tem ganho de tensão $>1$ na região de transição, gerando os dois lóbulos abertos na curva borboleta ($\text{SNM} > 0$).
  - Em `Key=1`: `PU` = n-FET e `PD` = p-FET. Ambos passam a operar como seguidores de fonte (ganho $<1$), eliminando a realimentação positiva. As duas curvas características se cruzam em um único ponto estável ($\text{SNM} = 0\text{ mV}$), forçando os nós $Q$ e $QB$ a convergirem e destruindo o bit armazenado.

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

### O que o apresentador desta seção deve saber (Conteúdo Aprofundado)
- **Evolução histórica e contexto tecnológico:**
  - *RFETs 1D (CNTFETs e nanofios de Si/Ge)*: foram os pioneiros em transistores reconfiguráveis por campo elétrico, mas sofrem com controle de alinhamento de nanotubos/nanofios, variabilidade de contatos e dificuldade de integração em arranjos densos de memória.
  - *Materiais 2D (TMDs como WSe₂, MoTe₂ e Fósforo Negro - BP)*: possuem espessura atômica uniforme e superfícies livres de *dangling bonds* (ligações pendentes), o que reduz armadilhas de interface, melhora o controle eletrostático e viabiliza integração 2D/3D em SRAMs.
  - *Segurança Polimórfica*: combina *logic locking* (travamento por chave) e camuflagem de layout para mitigar ataques SAT, *delayering* e análise de potência diferencial (DPA).
- **Diferenciais diretos frente à literatura (especialmente Wu et al. / fluxo HSPICE):**
  - **Ferramentas:** literatura depende de simuladores proprietários (HSPICE); este trabalho entrega um fluxo 100% open-source (`ngspice-47` + Python).
  - **Modelo 4D em $V_{g2} = -1{,}5\text{ V}$:** modelos anteriores extrapolavam mal essa região; a inclusão do plano real reduziu o erro em $196\times$.
  - **Análise completa da SRAM:** além do modelo do dispositivo, este trabalho entrega o protocolo transiente em 4 fases ($30\text{ ns}$), a análise estática de SNM com sintonia de banda plana ($\Delta V_{fb}$) e a mitigação de *Read Disturb* via *WL Underdrive*.

### O que falar
- **Slide 4:** Resumir a linha evolutiva nos 3 cards superiores (1D $\rightarrow$ 2D $\rightarrow$ Segurança Polimórfica) e usar a tabela inferior para mostrar claramente o que faltava na literatura e o que este trabalho entrega de novo em cada aspecto técnico.

### Perguntas prováveis e como responder
- **"Qual a principal vantagem de migrar de nanofios 1D para materiais 2D como o Fósforo Negro?"**  
  *Resposta:* Materiais 2D oferecem espessura atômica uniforme sem *dangling bonds* na interface, reduzindo a variabilidade de contato e permitindo melhor escalabilidade em arranjos de memória.
- **"O que o trabalho de vocês faz que o modelo original de Wu et al. não fazia?"**  
  *Resposta:* Além de portar tudo para um fluxo aberto (`ngspice-47`), corrigimos a extrapolação em $V_{g2} = -1{,}5\text{ V}$ com a superfície 4D real, quantificamos a SNM estática considerando o desvio de banda plana e resolvemos o *Read Disturb* com *WL Underdrive*.

---

## 3. Metodologia (Slides 5 e 6)

### O que o apresentador desta seção deve saber (Conteúdo Aprofundado)
- **Pipeline de tradução do modelo 4D (`bp_ari_ngspice.lib v2`):**
  - **Entrada:** tabelas experimentais 4D (`BP_ARI_dataN.txt` e `BP_ARI_dataP.txt`) indexadas por $(V_{ds}, V_{gs}, V_{g1s}, V_{g2s})$.
  - **Referência bilateral de fonte (`min/max`):** em transistores simétricos de acesso (*pass-gates* `PG`), a corrente muda de sentido entre leitura e escrita. O modelo usa `min(Vd, Vs)` como referência de fonte para n-FET e `max(Vd, Vs)` para p-FET, garantindo continuidade física quando dreno e fonte trocam de papel.
  - **Superfície 4D completa:** inclui explicitamente o plano experimental de $V_{g2} = -1{,}5\text{ V}$, capturando o desvio de banda plana ($\Delta V_{fb} = -0{,}25\text{ V}$) sem extrapolação linear grosseira.
  - **Estabilidade numérica (MNA):** limites monotônicos ($\pm 1000\text{ V}$) e resistência parasita controlada evitam matrizes singulares e falhas de convergência no método de Newton-Raphson do SPICE.
  - **Capacitâncias externas:** como as tabelas experimentais são quase-estáticas, adicionamos capacitâncias nodais fixas ($C_q = C_{qb} = 1{,}0\text{ fF}$) nos nós de armazenamento para capturar a dinâmica transiente.
- **Arquitetura 6T e Protocolos de Simulação:**
  - **Dimensionamento relativo:** `PU` ($W=1{,}0$), `PD` ($W=2{,}0$), `PG` ($W=1{,}5$). Note que `PD` é mais forte que `PG` ($2{,}0 > 1{,}5$) para tentar preservar o `0` na leitura, mas ainda assim precisa de *Read-Assist* em $WL=1{,}0\text{ V}$.
  - **Protocolo transiente de 30 ns (4 fases):**
    1. *Escrita* (`0–6 ns`): `Key=0`, escreve dado na célula.
    2. *Retenção* (`6–15 ns`): `WL=0`, verifica estabilidade do dado armazenado.
    3. *Auto-Destruição* (`15–20 ns`): ativa `Key=1`, observa o colapso de $\Delta V$.
    4. *Bloqueio de Escrita* (`20–30 ns`): tenta sobrescrever novo dado com `Key=1` ativo, provando que a célula permanece travada.
  - **Varredura DC de Curva Borboleta (SNM):** realizada para `Key ∈ {0, 1}` e `WL ∈ {0; 0,30; 1,0} V` para quantificar *Hold*, *Read* e *Read-Assist*.

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

### O que o apresentador desta seção deve saber (Conteúdo Aprofundado)
- **Validação Cruzada (Slide 7):**
  - Comparação direta entre `ngspice-47 v2` e Synopsys HSPICE: redução de **$196\times$** no RMSE de saída p-FET em $V_{g2} = -1{,}5\text{ V}$, atingindo **$R^2 = 0{,}99977$**. Isso prova que o fluxo open-source reproduz com fidelidade o simulador comercial.
- **Física de $V_{g2}$ e Banda Plana (Slide 8):**
  - Erro médio frente às LUTs experimentais: **$0{,}062\%$** (n-FET) e **$0{,}003\%$** (p-FET).
  - *Por que sintonizar $V_{g2,PU} = -0{,}2\text{ V}$?* Em $V_{g2} = -1{,}5\text{ V}$, o p-FET sofre um deslocamento de banda plana ($\Delta V_{fb} \approx -0{,}25\text{ V}$) que reduz sua força de condução e desbalanceia o inversor. Sintonizar para $V_{g2,PU} = -0{,}2\text{ V}$ restaura a simetria entre `PU` e `PD`.
- **Transiente de 30 ns (Slide 9):**
  - Na fase de retenção (`Key=0`), a célula sustenta $\Delta V = 0{,}975\text{ V}$ (praticamente o $V_{DD}$ completo).
  - Ao ativar `Key=1` em $15\text{ ns}$, $\Delta V$ colapsa **$>91\%$ em $<3\text{ ns}$** (caindo para $0{,}084\text{ V}$).
  - Na fase de bloqueio (`20–30 ns`), tentativas de escrita falham ($\Delta V = 0{,}076\text{ V}$), confirmando que `Key=1` impede tanto a retenção quanto a gravação de novos dados.
- **Curvas Borboleta e Read-Assist (Slide 10):**
  - A sintonia de $V_{g2,PU}$ de $-0{,}5\text{ V}$ para $-0{,}2\text{ V}$ mais que triplica a margem de retenção: $\text{SNM}_{\text{Hold}}$ sobe de **$49{,}4\text{ mV}$ para $167{,}1\text{ mV}$**.
  - Na leitura padrão ($WL = 1{,}0\text{ V}$), ocorre *Read Disturb* ($\text{SNM} = 0\text{ mV}$), pois o *pass-gate* ($W_{PG}=1{,}5$) puxa o nó armazenado em `0` acima do limiar de chaveamento do inversor.
  - Aplicando *Wordline Underdrive* ($WL = 0{,}30\text{ V}$), enfraquecemos o *pass-gate* durante a leitura e recuperamos **$\text{SNM}_{\text{Read-Assist}} = 66{,}2\text{ mV}$** sem adicionar nenhum transistor.
  - Em `Key=1`, a SNM é **$0{,}00\text{ mV}$** em todos os regimes (*Hold* e *Read*).
- **Matriz Consolidada e Conclusões (Slides 11 e 12):**
  - Todas as metas de aceitação foram cumpridas.
  - *Limitações reconhecidas:* escopo quase-estático (capacitâncias fixas externas) e lacuna experimental nas tabelas originais para $V(g_2, s) \in (-0{,}90; +0{,}20)\text{ V}$.
  - *Trabalhos futuros:* modelagem de redes capacitivas parasitas dependentes de polarização, análise de variabilidade estatística (Monte Carlo) e simulação de arranjos multi-célula (2×2, 4×4).

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
