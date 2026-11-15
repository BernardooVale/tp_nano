* Caracterizacao p-FET Transfer (Id vs Vg para multiplos Vg1)
.include "bp_ari_ngspice.lib"
Vd d 0 DC -0.8
Vs s 0 DC 0.0
Vg g 0 DC 0.0
Vg1 g1 0 DC -1.5
Vg2 g2 0 DC -1.2
X1 d g s g1 g2 ARI W=1.0
.control
set wr_vecnames
set wr_singlescale
alter Vg1 = -1.5
dc Vg -1.5 0.0 0.05
wrdata p_transfer_m1d5.dat -i(Vd)
alter Vg1 = -1.3
dc Vg -1.5 0.0 0.05
wrdata p_transfer_m1d3.dat -i(Vd)
alter Vg1 = -1.1
dc Vg -1.5 0.0 0.05
wrdata p_transfer_m1d1.dat -i(Vd)
alter Vg1 = -0.9
dc Vg -1.5 0.0 0.05
wrdata p_transfer_m0d9.dat -i(Vd)
alter Vg1 = -0.7
dc Vg -1.5 0.0 0.05
wrdata p_transfer_m0d7.dat -i(Vd)
alter Vg1 = -0.5
dc Vg -1.5 0.0 0.05
wrdata p_transfer_m0d5.dat -i(Vd)
alter Vg1 = -0.3
dc Vg -1.5 0.0 0.05
wrdata p_transfer_m0d3.dat -i(Vd)
alter Vg1 = -0.1
dc Vg -1.5 0.0 0.05
wrdata p_transfer_m0d1.dat -i(Vd)
.endc
.end
