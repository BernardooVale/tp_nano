# Transistores Bidimensionais com Polaridade Reconfigurável para Circuitos Seguros

## 1. Visão Geral e Fundamentos de Segurança em Hardware

A segurança em nível de hardware emergiu como um pilar crítico no desenvolvimento de circuitos integrados modernos. Nas tecnologias de semicondutores complementares de óxido metálico (CMOS) convencionais baseadas em silício, a funcionalidade de cada bloco lógico é determinada de maneira imutável durante o processo de fabricação. A polaridade dos transistores de efeito de campo de canal n (n-FETs) e de canal p (p-FETs) depende do dopamento substitucional estático das regiões de fonte, dreno e canal. Consequentemente, as redes de elevação (*pull-up*) e de descida (*pull-down*) que compõem portas estáticas permanecem fixas, permitindo que adversários com acesso a técnicas avançadas de engenharia reversa — tais como microscopia eletrônica de transmissão (TEM) e imageamento tridimensional não destrutivo por raios X em nanoescala — extraiam o leiaute do chip e reconstruam completamente a sua funcionalidade lógica.

Para mitigar a vulnerabilidade contra a pirataria de circuitos integrados e a cópia não autorizada, abordagens tradicionais de segurança implementam técnicas como o travamento lógico (*logic locking*) e a camuflagem de circuitos integrados (*IC camouflaging*). Contudo, a realização dessas defesas em silício padrão impõe penalidades substanciais de área e consumo de energia. O travamento lógico tradicional depende da inserção de multiplexadores ou portas XOR adicionais distribuídos estrategicamente pelo circuito, exigindo no mínimo $8N$ transistores suplementares para uma chave de ativação secreta de $N$ bits. Do mesmo modo, técnicas consolidadas de camuflagem de circuitos baseadas em células de ofuscação (como contatos falsos e variação de dopagem) exigem redundância extrema; a camuflagem de uma tabela de substituição (S-Box) do padrão de criptografia avançada (AES) com células de ofuscação baseadas em portas NAND convencionais chega a demandar um acréscimo de 154% no número total de portas lógicas do circuito original.

A investigação conduzida por Peng Wu, Dayane Reis, Xiaobo Sharon Hu e Joerg Appenzeller, publicada na *Nature Electronics* (doi: 10.1038/s41928-020-00511-7), estabelece uma mudança de paradigma ao transferir a segurança do nível de arquitetura para o nível intrínseco do dispositivo. Ao explorar propriedades de transporte eletrostático em semicondutores bidimensionais (2D) em camadas — especificamente o fósforo negro (*black phosphorus* - BP) —, os pesquisadores desenvolveram transistores de efeito de campo com barreira de Schottky (SB-FETs) cuja polaridade de condução pode ser reconfigurada dinamicamente entre p-FET e n-FET em tempo de execução. Essa reconfigurabilidade eletrostática viabiliza portas lógicas polimórficas (como NAND/NOR e XOR/XNOR) capazes de alternar sua função mediante a inversão dos trilhos de polarização ($V_{DD}$ e GND) controlada por um bit de chave, eliminando completamente a sobrecarga adicional de contagem de transistores associada ao travamento lógico e à camuflagem física.

---

## 2. Física e Desafios de Dispositivos SB-FET Reconfiguráveis

O funcionamento dos transistores baseados em semicondutores bidimensionais difere fundamentalmente dos dispositivos de silício convencionais dopados por difusão. Em canais atômica ou molecularmente finos, a injeção de portadores de carga ocorre predominantemente por tunelamento e emissão termoiônica através de barreiras de Schottky formadas nas interfaces metal-semicondutor entre os contatos de fonte/dreno e o material do canal. Devido ao comprimento de blindagem geométrica reduzido ($\lambda$) característico dos corpos ultrafinos, os transistores 2D apresentam uma ambipolaridade inerente, na qual tanto elétrons quanto lacunas podem ser injetados no canal de acordo com a modulação eletrostática das portas.

### Alinhamento de Fermi e Corrente de Tunelamento

A simetria de condução entre os ramos de elétrons e lacunas é um pré-requisito indispensável para a viabilidade de circuitos complementares e reconfiguráveis. Para que as correntes em estado ligado ($I_{on}$) nos modos p-FET e n-FET sejam equivalentes, o nível de Fermi ($E_F$) do metal de contato deve alinhar-se próximo ao centro da banda proibida (*mid-gap*) do semicondutor, estabelecendo alturas de barreira de Schottky equilibradas para lacunas e elétrons:

$$\Phi_{SB,p} \approx \Phi_{SB,n} \approx \frac{E_g}{2}$$

Como a injeção de portadores em canais ultrafinos com barreiras de Schottky é dominada pelo tunelamento através da barreira eletrostática ($I_{tunnel}$), a corrente ligada $I_{on}$ pode ser descrita analiticamente por meio da aproximação de Wentzel–Kramers–Brillouin (WKB):

$$I_{on} \propto \exp\left(-\frac{4\lambda\sqrt{2m^*\Phi_{SB}}}{3\hbar}\right) \approx \exp\left(-\frac{4\lambda\sqrt{2m^*(E_g/2)}}{3\hbar}\right)$$

Nesta relação, $m^*$ representa a massa efetiva dos portadores (lacunas para o ramo p e elétrons para o ramo n), $\lambda$ é o comprimento de blindagem geométrica, $E_g$ é a largura da banda proibida do semicondutor e $\hbar$ é a constante de Planck reduzida. A formulação estabelece que materiais com banda proibida estreita ($E_g$ reduzido) e massas efetivas diminutas são essenciais para maximizar a corrente em estado ligado e permitir o escalonamento da tensão de alimentação operacional para níveis sub-1 V.

### O Dilema da Tensão de Limiar e da Corrente de Fuga Ambipolar

Embora a utilização de materiais com banda proibida larga (como nanofios de silício com $E_g \approx 1,1\text{ eV}$, dissulfeto de tungstênio $\text{WSe}_2$ com $E_g \approx 1,8\text{ eV}$ ou ditelureto de molibdênio $\text{MoTe}_2$ com $E_g \approx 1,1\text{ eV}$) tenha sido amplamente explorada em estudos anteriores de transistores reconfiguráveis, essas soluções enfrentam barreiras intransponíveis quanto à tensão de operação. Supondo um controle eletrostático ideal da porta, as tensões de limiar dos ramos p e n ($V_{th,p}$ e $V_{th,n}$) encontram-se espaçadas por uma magnitude não inferior a $E_g/q$. Em tecnologias CMOS tradicionais, o ajuste independente das tensões de limiar de n-FETs e p-FETs é solucionado pelo emprego de metais de porta com diferentes funções de trabalho. Em dispositivos reconfiguráveis, contudo, os transistores devem ser fisicamente idênticos e intercambiáveis, compartilhando a mesma pilha de materiais de porta. Dessa forma, a tensão de limiar $V_{th}$ não pode ser escalonada abaixo de $E_g/2q$ em materiais com grande banda proibida, impedindo a operação em baixas tensões.

Por outro lado, a adoção direta de semicondutores de banda proibida estreita acarreta uma degradação severa da corrente de desligamento ($I_{off}$). No estado desligado do modo n-FET ($V_g = 0\text{ V}$, $V_{ds} > 0\text{ V}$), a tensão entre a porta e o dreno torna-se negativa ($V_{gd} = V_g - V_d < 0\text{ V}$). Essa condição de campo elétrico habilita uma injeção espúria de lacunas proveniente do dreno. À medida que a tensão dreno-fonte $V_{ds}$ cresce, o ramo de condução do tipo p desloca-se lateralmente por uma grandeza $\Delta V_{ds}$. Em semicondutores com $E_g$ estreito, a proximidade dos ramos p e n faz com que a corrente no ponto de interseção aumente drasticamente, elevando a corrente de fuga e colapsando a razão de corrente ligado/desligado ($I_{on}/I_{off}$).

---

## 3. Arquitetura do Dispositivo e Engenharia da Porta de Polaridade

Para solucionar a incompatibilidade entre alta corrente no estado ligado e baixa corrente de fuga em materiais de banda estreita, a equipe de pesquisa projetou uma arquitetura física com eletrodos de porta desacoplados, implementada em fósforo negro (BP). O fósforo negro em camadas apresenta propriedades de transporte excepcionais para transistores reconfiguráveis, reunindo uma banda proibida direta ajustável com a espessura (variando entre $0,35\text{ eV}$ e $0,7\text{ eV}$ para lâminas com espessuras de $5\text{ nm}$ a $16\text{ nm}$, e até $0,3\text{ a }2\text{ eV}$ no regime limite) e massas efetivas baixas ($0,15 m_0$, onde $m_0$ é a massa de repouso do elétron).

### Estrutura Física e Pilha Dielétrica

O dispositivo protótipo é fabricado sobre um substrato de silício com óxido de silício térmico ($\text{Si}/\text{SiO}_2$) e incorpora uma estrutura de porta dupla assimétrica:

* **Canal Semicondutor:** Flocos esfoliados de fósforo negro com espessuras controladas entre $5\text{ nm}$ e $16\text{ nm}$ e comprimento de canal de aproximadamente $1\ \mu\text{m}$.
* **Contatos de Fonte e Dreno:** Pilha metálica de cromo e ouro ($\text{Cr}/\text{Au}$), selecionada por promover um alinhamento do nível de Fermi próximo ao meio da banda proibida do fósforo negro, permitindo injeção equilibrada de elétrons e lacunas.
* **Porta Superior (*Top Gate* - TG):** Eletrodo de modulação do canal isolado por um dielétrico de alta constante dielétrica (high-$\kappa$) de óxido de alumínio ($\text{Al}_2\text{O}_3$) com $4\text{ nm}$ de espessura.
* **Portas Inferiores Segmentadas:** Eletrodos metálicos inferiores isolados por uma camada de $7\text{ nm}$ de óxido de háfnio ($\text{HfO}_2$), divididos fisicamente em:
  * **Porta Inferior (*Bottom Gate* - BG):** Conectada eletricamente à porta superior para formar o terminal principal de porta de controle ($G$).
  * **Porta de Polaridade (*Polarity Gate* - PG):** Eletrodo independente posicionado exclusivamente sob a extremidade do canal que se sobrepõe ao contato de dreno ($D$).

### Mecanismo de Supressão Eletrostática da Injeção Ambipolar

A introdução da porta de polaridade que se sobrepõe ao dreno altera drasticamente o perfil das bandas de energia nas imediações do contato dreno-semicondutor:

* **Modo p-FET ($V_{pg} < 0\text{ V}$):** Quando a porta de controle é polarizada negativamente ($V_g < 0\text{ V}$), portadores do tipo lacuna são injetados pela fonte e transitam pelo canal ligado. No estado desligado ($V_g = 0\text{ V}$, $V_{ds} < 0\text{ V}$), a interface com a fonte permanece em bandas planas, cessando o fluxo de lacunas. Ao mesmo tempo, a aplicação de uma tensão negativa na porta de polaridade ($V_{pg} < 0\text{ V}$) curva as bandas na borda do dreno para cima, criando uma barreira eletrostática espessa que impede a injeção ambipolar de elétrons pelo dreno.
* **Modo n-FET ($V_{pg} > 0\text{ V}$):** Quando a porta de controle é polarizada positivamente ($V_g > 0\text{ V}$), elétrons são injetados pela fonte e ligam o transistor. No estado desligado ($V_g = 0\text{ V}$, $V_{ds} > 0\text{ V}$), o potencial positivo aplicado à porta de polaridade ($V_{pg} > 0\text{ V}$) flexiona as bandas de energia no dreno para baixo, bloqueando o tunelamento espúrio de lacunas pelo dreno.

Caso a magnitude das tensões aplicadas à porta de polaridade seja excessivamente elevada em valores absolutos, o dobramento acentuado das bandas pode induzir correntes indesejadas por tunelamento banda a banda (*band-to-band tunneling*), delimitando a janela ótima de operação.

---

## 4. Caracterização Elétrica Experimental dos Transistores BP

As medições elétricas dos transistores de fósforo negro com porta de polaridade revelam desempenho de chaveamento e simetria de condução em temperatura ambiente.

A tabela a seguir consolida as métricas experimentais obtidas para um mesmo transistor sob os modos de operação p-FET e n-FET:

| Parâmetro Experimental | Modo p-FET ($V_{pg} = -2\text{ V}$) | Modo n-FET ($V_{pg} = 2\text{ V}$) | Condições de Ensaio |
| :--- | :--- | :--- | :--- |
| **Subthreshold Swing ($SS$) a Baixa Tensão** | $75\text{ mV/dec}$ | $72\text{ mV/dec}$ | $|V_{ds}| = 0,1\text{ V}$ |
| **Subthreshold Swing ($SS$) a Tensão Intermediária** | $85\text{ mV/dec}$ | $73\text{ mV/dec}$ | $|V_{ds}| = 0,4\text{ V}$ |
| **Subthreshold Swing ($SS$) a Alta Tensão** | $93\text{ mV/dec}$ | $80\text{ mV/dec}$ | $|V_{ds}| = 0,7\text{ V}$ |
| **Razão de Corrente ($I_{on}/I_{off}$)** | $10^5$ | $10^5$ | $|V_{ds}| = 0,7\text{ V}$ |
| **Densidade de Corrente Ligada ($I_{on}$)** | $\sim 10\ \mu\text{A}/\mu\text{m}$ | $\sim 10\ \mu\text{A}/\mu\text{m}$ | $|V_{ds}| = 0,7\text{ V}$, $|V_g - V_{fb}| = 1,2\text{ V}$ |
| **Comprimento de Canal ($L$)** | $\sim 1\ \mu\text{m}$ | $\sim 1\ \mu\text{m}$ | Dimensão física do protótipo |

Os valores de inclinação de sublimiar próximos ao limite termodinâmico de $60\text{ mV/dec}$ em temperatura ambiente demonstram o acoplamento eletrostático propiciado pela geometria de dupla porta associada aos dielétricos high-$\kappa$ finos. Adicionalmente, as curvas características de saída ($I_d$ versus $V_{ds}$) evidenciam comportamento de saturação de corrente bem definido e simetria rigorosa entre os quadrantes de condução de elétrons e lacunas, propriedade basilar para a integração de circuitos lógicos complementares balanceados.

---

## 5. Inversor Lógico Complementar de Baixa Tensão

A validação dos dispositivos em circuitos integrados iniciou-se com a fabricação monolítica de um inversor lógico complementar constituído por dois transistores reconfiguráveis de fósforo negro interconectados no mesmo chip. Um dos dispositivos é configurado permanentemente no modo p-FET via polarização da sua porta de polaridade ($V_{pg,s} = -V_{DD}$), enquanto o outro opera no modo n-FET ($V_{pg,s} = V_{DD}$).

As características de transferência de tensão ($V_{out} \times V_{in}$) revelam os seguintes atributos funcionais:

* **Excursão Completa de Sinal (*Rail-to-Rail Swing*):** O inversor atinge oscilação completa de saída, variando de $V_{DD}$ absoluto até $0\text{ V}$ em todo o espectro avaliado de tensões de alimentação, compreendido entre $V_{DD} = 1,0\text{ V}$ e $V_{DD} = 0,2\text{ V}$.
* **Operação Ultrabaixa Tensão:** O circuito mantém funcionalidade lógica e chaveamento abrupto mesmo em uma tensão de alimentação extrema de $V_{DD} = 0,2\text{ V}$, viabilizado pela inclinação de sublimiar acentuada dos transistores individuais.
* **Ganho de Tensão Elevado:** A derivada máxima $|dV_{out}/dV_{in}|$ atinge um pico de ganho de tensão de $33,3$ sob $V_{DD} = 1,0\text{ V}$. Sob tensões reduzidas de $0,8\text{ V}$, $0,6\text{ V}$, $0,4\text{ V}$ e $0,2\text{ V}$, o inversor sustenta ganhos bem acima da unidade, garantindo margens de ruído estáveis para o chaveamento em cascata.
* **Compensação de Tensão de Bandas Planas:** Nas curvas experimentais, a tensão de entrada foi deslocada por $V_{in,shift} = V_{in} + 0,27\text{ V}$ para compensar a tensão de bandas planas ($V_{fb}$) não nula decorrente das cargas fixas presentes nas interfaces dielétricas.

---

## 6. Primitivas de Segurança de Hardware: Portas Lógicas Polimórficas

A aplicação central dos transistores 2D com polaridade ajustável reside na construção de portas lógicas polimórficas, cuja função booleana se transmuta com base no estado de um bit de controle associado à chave de ativação.

### Demonstração Experimental da Porta Polimórfica NAND/NOR

Uma porta polimórfica com duas entradas ($A$ e $B$) foi implementada monoliticamente conectando quatro transistores reconfiguráveis de fósforo negro:

* **Configuração com $\text{Key}_i = 0$ (Modo NAND):**
  * O trilho superior é polarizado em $V_{DD}$ e o trilho inferior em GND.
  * As portas de polaridade dos dois transistores superiores são configuradas para o modo p-FET, compondo a rede de *pull-up* em paralelo conectada a $V_{DD}$.
  * As portas de polaridade dos dois transistores inferiores são polarizadas para o modo n-FET, estruturando a rede de *pull-down* em série ligada a GND.
  * A saída $V_{out}$ produz a função lógica booleana $\overline{A \cdot B}$ (NAND).
* **Configuração com $\text{Key}_i = 1$ (Modo NOR):**
  * As atribuições dos trilhos de polarização são invertidas: o trilho superior é comutado para GND e o trilho inferior para $V_{DD}$.
  * As polaridades eletrostáticas dos transistores são intervertidas: os dois dispositivos superiores operam como n-FETs e assumem o papel de rede de *pull-down* para GND.
  * Os dois dispositivos inferiores operam como p-FETs, tornando-se a rede de *pull-up* para $V_{DD}$.
  * A saída $V_{out}$ comuta dinamicamente para a função booleana $\overline{A + B}$ (NOR).

Medições elétricas com tensões de alimentação variando de $V_{DD} = 0,4\text{ V}$ a $1,0\text{ V}$ comprovaram que a mesma célula física executa as tabelas-verdade completas das funções NAND e NOR de acordo com a seleção da chave, mantendo os níveis lógicos de saída padronizados ('0' correspondente a $0\text{ V}$ e '1' correspondente a $V_{DD}$).

### Simulação da Porta Polimórfica XOR/XNOR e Resiliência a Canais Laterais

Para circuitos criptográficos que empregam extensivamente mascaramento com cifras de fluxo, foi projetada e simulada uma porta polimórfica XOR/XNOR utilizando um modelo comportamental em Verilog-A baseado em tabelas de busca (*look-up table* - LUT) construído a partir das medições empíricas dos dispositivos.

A topologia da porta XOR/XNOR com transistores reconfiguráveis apresenta simetria estrutural rigorosa em seu leiaute. A simulação transiente das formas de onda sob $V_{DD} = 0,8\text{ V}$ demonstra transições limpas entre a funcionalidade XOR e a funcionalidade XNOR conforme os trilhos de suprimento são alternados. Além da ausência de penalidade de área, o monitoramento das correntes de alimentação revela que os perfis de corrente $|I(V_{DD})|$ e $|I(V_{SS})|$ são consideravelmente mais simétricos do que os observados na porta NAND/NOR. Essa homogeneidade na corrente consumida reduz drasticamente as assinaturas transitórias correlacionadas aos dados processados, oferecendo resistência intrínseca superior contra ataques de canal lateral baseados em análise diferencial de potência (*Differential Power Analysis* - DPA).

### Robustez a Variações de Tensão de Alimentação

Como as portas de polaridade dos transistores são ligadas diretamente aos nós de distribuição de potência, ruídos e flutuações nas tensões dos trilhos ($V_{DD}$ e $V_{SS}$) alteram as tensões relativas porta de polaridade-fonte ($V_{pg-s}$) e porta de polaridade-dreno ($V_{pg-d}$). Para avaliar a confiabilidade operacional frente a essas perturbações, foram conduzidas simulações estatísticas de Monte Carlo. Os resultados computacionais demonstraram que tanto as portas NAND/NOR quanto as portas XOR/XNOR preservam margens de ruído funcionais e integridade estática mesmo sob flutuações nominais acentuadas nas linhas de tensão de alimentação.

---

## 7. Procedimentos de Fabricação e Metodologia Experimental

Os procedimentos experimentais e de modelagem adotados no artigo compreendem etapas específicas de síntese em nanoescala e caracterização criogênico-atmosférica:

1. **Esfoliação e Transferência:** Flocos de fósforo negro foram obtidos por esfoliação mecânica a partir de cristais de BP de alta pureza e transferidos para substratos oxidados de $\text{Si}/\text{SiO}_2$.
2. **Definição Litográfica e Contatos:** Os padrões de eletrodos das portas inferiores (BG e PG) e dos contatos de fonte e dreno foram definidos por litografia por feixe de elétrons (EBL), seguidos da deposição de filmes metálicos de cromo e ouro ($\text{Cr}/\text{Au}$).
3. **Deposição de Dielétricos High-$\kappa$:** As camadas dielétricas foram sintetizadas por deposição em camada atômica (ALD), compreendendo $7\text{ nm}$ de $\text{HfO}_2$ sobre os eletrodos inferiores e $4\text{ nm}$ de $\text{Al}_2\text{O}_3$ como dielétrico da porta superior.
4. **Caracterização Elétrica:** As medições em corrente contínua (DC) e transientes foram executadas à temperatura ambiente em uma estação de pontas de prova de alto vácuo LakeShore FWPX, sob níveis de pressão residual inferiores a $10^{-5}\text{ Torr}$, utilizando um analisador de parâmetros semicondutores Agilent 4156C.
5. **Modelagem Computacional em Verilog-A:** Para a validação em nível de circuito, os pesquisadores codificaram um modelo Verilog-A que consulta tabelas de busca quadridimensionais alimentadas diretamente pelos dados experimentais de correntes de dreno em função de $V_{g1,s}$, $V_{g2,s}$, $V_{g,s}$ e $V_{d,s}$, possibilitando a simulação transiente precisa de células lógicas e cadeias polimórficas complexas.
