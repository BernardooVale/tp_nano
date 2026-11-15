* Caracterizacao n-FET Output (Id vs Vds para multiplos Vg)
.include "bp_ari_ngspice.lib"
Vd d 0 DC 0.0
Vs s 0 DC 0.0
Vg g 0 DC 1.1
Vg1 g1 0 DC 1.1
Vg2 g2 0 DC 0.8
X1 d g s g1 g2 ARI W=1.0
.control
set wr_vecnames
set wr_singlescale
alter Vg = 0.1
dc Vd 0.0 1.2 0.02
wrdata n_output_vg0d1.dat -i(Vd)
alter Vg = 0.3
dc Vd 0.0 1.2 0.02
wrdata n_output_vg0d3.dat -i(Vd)
alter Vg = 0.5
dc Vd 0.0 1.2 0.02
wrdata n_output_vg0d5.dat -i(Vd)
alter Vg = 0.7
dc Vd 0.0 1.2 0.02
wrdata n_output_vg0d7.dat -i(Vd)
alter Vg = 0.9
dc Vd 0.0 1.2 0.02
wrdata n_output_vg0d9.dat -i(Vd)
alter Vg = 1.1
dc Vd 0.0 1.2 0.02
wrdata n_output_vg1d1.dat -i(Vd)
.endc
.end
