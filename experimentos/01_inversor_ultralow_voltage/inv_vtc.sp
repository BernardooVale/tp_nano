* Caracterizacao DC (VTC) do Inversor Complementar BP SB-FET (VDD = 1.0V a 0.2V)
.include "../00_modelo_ngspice/bp_ari_ngspice.lib"

.param supp=1.0
.param offn=0.0
.param offp=0.0
Vdd vdd 0 {supp}
Vss vss 0 0
Vin in 0 0

* Fontes de compensacao de banda plana (Vfb)
Egn gn 0 VOL = 'v(in) + offn'
Egp gp 0 VOL = 'v(in) + offp'

* Polarizacao nominal de g1 e g2 para p-FET (pull-up) e n-FET (pull-down)
Vg1p g1p 0 {supp - 1.5}
Vg2p g2p 0 {supp - 1.2}
Vg1n g1n 0 1.1
Vg2n g2n 0 0.8

XPU out gp vdd g1p g2p ARI W=1.0
XPD out gn vss g1n g2n ARI W=1.0

.control
set wr_vecnames
set wr_singlescale
alterparam supp = 1.0
alterparam offn = 0.0
alterparam offp = 0.0
reset
dc Vin 0 1.0 0.002
wrdata vtc_direto_vdd1d0.dat v(out)
alterparam supp = 0.8
alterparam offn = 0.0
alterparam offp = 0.0
reset
dc Vin 0 0.8 0.002
wrdata vtc_direto_vdd0d8.dat v(out)
alterparam supp = 0.6
alterparam offn = 0.0
alterparam offp = 0.0
reset
dc Vin 0 0.6 0.002
wrdata vtc_direto_vdd0d6.dat v(out)
alterparam supp = 0.4
alterparam offn = 0.0
alterparam offp = 0.0
reset
dc Vin 0 0.4 0.002
wrdata vtc_direto_vdd0d4.dat v(out)
alterparam supp = 0.2
alterparam offn = 0.0
alterparam offp = 0.0
reset
dc Vin 0 0.2 0.002
wrdata vtc_direto_vdd0d2.dat v(out)
alterparam supp = 1.0
alterparam offn = -0.5200
alterparam offp = -0.0800
reset
dc Vin 0 1.0 0.002
wrdata vtc_comp_vdd1d0.dat v(out)
alterparam supp = 0.8
alterparam offn = -0.4200
alterparam offp = -0.1800
reset
dc Vin 0 0.8 0.002
wrdata vtc_comp_vdd0d8.dat v(out)
alterparam supp = 0.6
alterparam offn = -0.3200
alterparam offp = -0.2800
reset
dc Vin 0 0.6 0.002
wrdata vtc_comp_vdd0d6.dat v(out)
alterparam supp = 0.4
alterparam offn = -0.2200
alterparam offp = -0.3800
reset
dc Vin 0 0.4 0.002
wrdata vtc_comp_vdd0d4.dat v(out)
alterparam supp = 0.2
alterparam offn = -0.1200
alterparam offp = -0.4800
reset
dc Vin 0 0.2 0.002
wrdata vtc_comp_vdd0d2.dat v(out)
.endc
.end
