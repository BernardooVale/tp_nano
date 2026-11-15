* Caracterizacao p-FET Output (Id vs Vds para multiplos Vg, Vg1=-1.5V, Vg2=-1.5V)
.include "bp_ari_ngspice.lib"
Vd d 0 DC 0.0
Vs s 0 DC 0.0
Vg g 0 DC -1.5
Vg1 g1 0 DC -1.5
Vg2 g2 0 DC -1.5
X1 d g s g1 g2 ARI W=1.0
.control
set wr_vecnames
set wr_singlescale
alter Vg = -1.5
dc Vd -1.2 0.0 0.02
wrdata p_output_vgm1d5.dat -i(Vd)
alter Vg = -1.3
dc Vd -1.2 0.0 0.02
wrdata p_output_vgm1d3.dat -i(Vd)
alter Vg = -1.1
dc Vd -1.2 0.0 0.02
wrdata p_output_vgm1d1.dat -i(Vd)
alter Vg = -0.9
dc Vd -1.2 0.0 0.02
wrdata p_output_vgm0d9.dat -i(Vd)
alter Vg = -0.7
dc Vd -1.2 0.0 0.02
wrdata p_output_vgm0d7.dat -i(Vd)
.endc
.end
