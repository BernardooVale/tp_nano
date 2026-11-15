* Caracterizacao n-FET Transfer (Id vs Vg para multiplos Vg1)
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
alter Vg1 = -0.1
dc Vg -0.8 1.1 0.05
wrdata n_transfer_m0d1.dat -i(Vd)
alter Vg1 = 0.1
dc Vg -0.8 1.1 0.05
wrdata n_transfer_p0d1.dat -i(Vd)
alter Vg1 = 0.3
dc Vg -0.8 1.1 0.05
wrdata n_transfer_p0d3.dat -i(Vd)
alter Vg1 = 0.5
dc Vg -0.8 1.1 0.05
wrdata n_transfer_p0d5.dat -i(Vd)
alter Vg1 = 0.7
dc Vg -0.8 1.1 0.05
wrdata n_transfer_p0d7.dat -i(Vd)
alter Vg1 = 0.9
dc Vg -0.8 1.1 0.05
wrdata n_transfer_p0d9.dat -i(Vd)
alter Vg1 = 1.1
dc Vg -0.8 1.1 0.05
wrdata n_transfer_p1d1.dat -i(Vd)
.endc
.end
