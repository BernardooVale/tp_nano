*a single bp tfet device simulation
.hdl "bp_ari.va"

.OPTION POST
.option lis_new
.TEMP 27
.option ingold
.OPTION method=TRAP
.OPTION runlvl=6
.OPTION CO=132
.option measform=3
.option sampling_method = SRS
.option captab

.param supp=1.1

*gate
Vg g 0 -1.1
*source
Vs s 0 0
*drain
Vd d 0 pwl 0 '-1*supp'  4n '1*supp'
*control gates (g1 and g2)
Vg1 g1 0 -1.5
Vg2 g2 0 -1.5

************************************************************************************

XARI_P d g s g1 g2 ARI W=1

.PRINT tran V(g) I(Vd)

.tran 1p 4ns SWEEP Vg -1.1 1.1 0.2 

.end
