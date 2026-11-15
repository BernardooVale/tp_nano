* Curva Borboleta (Butterfly Curve / SNM) da SRAM 6T BP SB-FET (Key=0 vs Key=1)
.include "../00_modelo_ngspice/bp_ari_ngspice.lib"

.param pg1_pu=-0.5
.param pg2_pu=-0.2
.param pg1_pd=0.8
.param pg2_pd=1.1
.param pwl=0.0

Vdd vdd 0 1.0
Vss vss 0 0.0
Vin in_qb 0 0.0

Vg1_pu g1_pu 0 {pg1_pu}
Vg2_pu g2_pu 0 {pg2_pu}
Vg1_pd g1_pd 0 {pg1_pd}
Vg2_pd g2_pd 0 {pg2_pd}
Vg1_pg g1_pg 0 1.8
Vg2_pg g2_pg 0 2.1

Vwl wl 0 {pwl}
Vbl bl 0 1.0

* Half-cell 1 da SRAM
XPU1 q in_qb vdd g1_pu g2_pu ARI W=1.0
XPD1 q in_qb vss g1_pd g2_pd ARI W=2.0
XPG1 q wl    bl  g1_pg g2_pg ARI W=1.5

.control
set wr_vecnames
set wr_singlescale

* 1) Key=0, Hold (WL=0V)
alterparam pg1_pu = -0.5
alterparam pg2_pu = -0.2
alterparam pg1_pd = 0.8
alterparam pg2_pd = 1.1
alterparam pwl = 0.0
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key0_hold.dat v(q)

* 2) Key=0, Read c/ Wordline Underdrive Read-Assist (WL=0.30V, BL=1.0V)
alterparam pwl = 0.30
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key0_read_assist.dat v(q)

* 3) Key=0, Read s/ Assist (WL=1.0V, BL=1.0V - Read Disturb)
alterparam pwl = 1.0
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key0_read.dat v(q)

* 4) Key=1, Hold (WL=0V) - Inversao de Polaridade
alterparam pg1_pu = 1.8
alterparam pg2_pu = 2.1
alterparam pg1_pd = -1.5
alterparam pg2_pd = -1.5
alterparam pwl = 0.0
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key1_hold.dat v(q)

* 5) Key=1, Read c/ Read-Assist (WL=0.30V, BL=1.0V)
alterparam pwl = 0.30
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key1_read_assist.dat v(q)

* 6) Key=1, Read s/ Assist (WL=1.0V, BL=1.0V)
alterparam pwl = 1.0
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key1_read.dat v(q)
.endc
.end
