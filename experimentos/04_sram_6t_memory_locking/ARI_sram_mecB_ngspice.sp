* ============================================================================
* PROJETO: Celula SRAM 6T Reconfiguravel com Transistores 2D de Fosforo Negro
* ARQUITETURA: Mecanismo B - Bloqueio de Retencao por Inversao de Polaridade
* Traducao para ngspice-47 da especificacao em tp_nano.md
* ============================================================================
.include "../00_modelo_ngspice/bp_ari_ngspice.lib"

.param supp=1.0

* 1. FONTES DE ALIMENTACAO FIXAS
Vdd vdd 0 {supp}
Vss vss 0 0

* 2. SINAIS DE POLARIDADE CONTROLADOS PELA CHAVE (KEY)
* 0ns a 15ns -> Key = 0 (Modo SRAM Normal: PU = p-FET, PD = n-FET)
* 15ns a 30ns -> Key = 1 (Modo Colapso: PU = n-FET, PD = p-FET)
Vg1_pu g1_pu 0 pwl(0n -0.5 14.9n -0.5 15.1n 1.8 30n 1.8)
Vg2_pu g2_pu 0 pwl(0n -0.2 14.9n -0.2 15.1n 2.1 30n 2.1)

Vg1_pd g1_pd 0 pwl(0n 0.8 14.9n 0.8 15.1n -1.5 30n -1.5)
Vg2_pd g2_pd 0 pwl(0n 1.1 14.9n 1.1 15.1n -1.5 30n -1.5)

* Polaridade Fixa dos Pass-Gates (Sempre em modo n-FET)
Vg1_pg g1_pg 0 1.8
Vg2_pg g2_pg 0 2.1

* 3. SINAIS DE CONTROLE E DADOS DA MEMORIA (WL, BL, BLB)
Vwl  wl  0 pwl(0n 0 1.9n 0 2.0n 1.0 6.0n 1.0 6.1n 0 19.9n 0 20.0n 1.0 24.0n 1.0 24.1n 0 30n 0)
Vbl  bl  0 pwl(0n 1.0 19.9n 1.0 20.0n 0.0 24.0n 0.0 24.1n 1.0 30n 1.0)
Vblb blb 0 pwl(0n 0.0 19.9n 0.0 20.0n 1.0 24.0n 1.0 24.1n 0.0 30n 0.0)

* 4. INSTANCIACAO DOS 6 TRANSISTORES DA CELULA SRAM (ordem: d g s g1 g2)
XPU1 q  qb vdd g1_pu g2_pu ARI W=1.0
XPD1 q  qb vss g1_pd g2_pd ARI W=2.0
XPU2 qb q  vdd g1_pu g2_pu ARI W=1.0
XPD2 qb q  vss g1_pd g2_pd ARI W=2.0
XPG1 q  wl bl  g1_pg g2_pg ARI W=1.5
XPG2 qb wl blb g1_pg g2_pg ARI W=1.5

Cq  q  vss 1f
Cqb qb vss 1f

* 5. SIMULACAO TRANSIENTE E EXTRACAO DE METRICAS (meas + wrdata)
.control
set wr_vecnames
set wr_singlescale
tran 10p 30n

meas tran Vq_Hold_Key0     FIND v(q)  AT=12n
meas tran Vqb_Hold_Key0    FIND v(qb) AT=12n
let DeltaV_Key0 = abs(Vq_Hold_Key0 - Vqb_Hold_Key0)
print DeltaV_Key0

meas tran Vq_Collapse1     FIND v(q)  AT=18n
meas tran Vqb_Collapse1    FIND v(qb) AT=18n
let DeltaV_Collapse1 = abs(Vq_Collapse1 - Vqb_Collapse1)
print DeltaV_Collapse1

meas tran Vq_Hold_Key1     FIND v(q)  AT=28n
meas tran Vqb_Hold_Key1    FIND v(qb) AT=28n
let DeltaV_Key1 = abs(Vq_Hold_Key1 - Vqb_Hold_Key1)
print DeltaV_Key1

wrdata sram_tran_30ns.dat v(wl) v(bl) v(blb) v(q) v(qb) v(g2_pu) v(g2_pd) i(Vdd)
.endc
.end
