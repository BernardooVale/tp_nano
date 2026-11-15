* Efeito da Porta de Polaridade Vg2 em modo n-FET e p-FET
.include "bp_ari_ngspice.lib"
Vd d 0 DC 0.8
Vs s 0 DC 0.0
Vg g 0 DC 0.0
Vg1 g1 0 DC 1.1
Vg2 g2 0 DC 0.8
X1 d g s g1 g2 ARI W=1.0
.control
set wr_vecnames
set wr_singlescale
alter Vg2 = 0.2
dc Vg -0.8 1.1 0.05
wrdata n_vg2_0d2.dat -i(Vd)
alter Vg2 = 0.4
dc Vg -0.8 1.1 0.05
wrdata n_vg2_0d4.dat -i(Vd)
alter Vg2 = 0.8
dc Vg -0.8 1.1 0.05
wrdata n_vg2_0d8.dat -i(Vd)
alter Vg2 = 1.0
dc Vg -0.8 1.1 0.05
wrdata n_vg2_1d0.dat -i(Vd)
alter Vd = -0.8
alter Vg1 = -1.5
alter Vg2 = -0.9
dc Vg -1.5 0.0 0.05
wrdata p_vg2_m0d9.dat -i(Vd)
alter Vg2 = -1.1
dc Vg -1.5 0.0 0.05
wrdata p_vg2_m1d1.dat -i(Vd)
alter Vg2 = -1.2
dc Vg -1.5 0.0 0.05
wrdata p_vg2_m1d2.dat -i(Vd)
alter Vg2 = -1.5
dc Vg -1.5 0.0 0.05
wrdata p_vg2_m1d5.dat -i(Vd)
.endc
.end
