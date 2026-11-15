* Simulacao Transiente do Inversor Complementar BP SB-FET
.include "../00_modelo_ngspice/bp_ari_ngspice.lib"

.param supp=1.0
.param offn=-0.32
.param offp=-0.18
Vdd vdd 0 {supp}
Vss vss 0 0
Vin in 0 pwl(0n 0 2n 0 2.2n {supp} 8n {supp} 8.2n 0 14n 0)

Egn gn 0 VOL = 'v(in) + offn'
Egp gp 0 VOL = 'v(in) + offp'

Vg1p g1p 0 {supp - 1.5}
Vg2p g2p 0 {supp - 1.2}
Vg1n g1n 0 1.1
Vg2n g2n 0 0.8

XPU out gp vdd g1p g2p ARI W=1.0
XPD out gn vss g1n g2n ARI W=1.0
Cload out 0 0.5f

.control
set wr_vecnames
set wr_singlescale
alterparam supp = 1.0
alterparam offn = -0.5200
alterparam offp = -0.0800
reset
tran 20p 14n
wrdata inv_tran_vdd1d0.dat v(in) v(out) i(Vdd)
alterparam supp = 0.6
alterparam offn = -0.3200
alterparam offp = -0.2800
reset
tran 20p 14n
wrdata inv_tran_vdd0d6.dat v(in) v(out) i(Vdd)
.endc
.end
