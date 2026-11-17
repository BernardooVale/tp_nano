* Testbench Padronizado para Tuplas Polimorficas de 2 Entradas (Cload = 0.3 fF)
* Tuplas: (NAND, NOR), (XOR, XNOR), (AND, OR), (NAND, XNOR), (NOR, XOR)
.include "../00_modelo_ngspice/bp_ari_ngspice.lib"

.subckt POLY_NAND_NOR a b out rtop gtop rbot gbot
X1 out a rtop gtop gtop ARI W=1.0
X2 out b rtop gtop gtop ARI W=1.0
X3 out b n1   gbot gbot ARI W=2.0
X4 n1  a rbot gbot gbot ARI W=2.0
Cn1 n1 0 0.05f
.ends POLY_NAND_NOR

.subckt POLY_XOR a an b bn out rtop gtop rbot gbot
X1 out an rtop b  gtop ARI W=1.0
X2 out a  rtop bn gtop ARI W=1.0
X3 out a  rbot b  gbot ARI W=1.0
X4 out an rbot bn gbot ARI W=1.0
.ends POLY_XOR

.subckt BP_INV08 in out vdd_i vss
B_sh in_sh 0 V = (v(in) > 0.8 ? 0.8 : v(in)) - 0.27
Vg1p g1p 0 -0.7
Vg2p g2p 0 -0.4
Vg1n g1n 0 0.8
Vg2n g2n 0 0.8
XP out in_sh vdd_i g1p g2p ARI W=2.0
XN out in_sh vss   g1n g2n ARI W=1.0
Cout out 0 0.1f
.ends BP_INV08

.subckt BP_INV11 in out vdd11 vss
B_sh in_sh 0 V = v(in) - 0.27
Vg1p g1p 0 -0.4
Vg2p g2p 0 -0.1
Vg1n g1n 0 1.1
Vg2n g2n 0 0.8
XP out in_sh vdd11 g1p g2p ARI W=2.0
XN out in_sh vss   g1n g2n ARI W=1.0
Cout out 0 0.1f
.ends BP_INV11


* Parametros de chaveamento (padrao Key=0)
.param prtop08 = 0.8
.param pgtop08 = -0.4
.param prbot08 = 0.0
.param pgbot08 = 0.8

.param prtop15 = 1.5
.param pgtop15 = 0.0
.param prbot15 = 0.0
.param pgbot15 = 0.8

.param pk11  = 0.0
.param pkn11 = 1.1

* Fontes de entrada padrao (00 -> 01 -> 10 -> 11 -> 00 em 25 ns)
Va08 a08 0 pwl(0.00n 0.0000 9.90n 0.0000 10.00n 0.8000 19.90n 0.8000 20.00n 0.0000 25.00n 0.0000)
Vb08 b08 0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.8000 9.90n 0.8000 10.00n 0.0000 14.90n 0.0000 15.00n 0.8000 19.90n 0.8000 20.00n 0.0000 25.00n 0.0000)
Va11  a11  0 pwl(0.00n 0.0000 9.90n 0.0000 10.00n 1.1000 19.90n 1.1000 20.00n 0.0000 25.00n 0.0000)
Van11 an11 0 pwl(0.00n 1.1000 9.90n 1.1000 10.00n 0.0000 19.90n 0.0000 20.00n 1.1000 25.00n 1.1000)
Vb11  b11  0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 1.1000 9.90n 1.1000 10.00n 0.0000 14.90n 0.0000 15.00n 1.1000 19.90n 1.1000 20.00n 0.0000 25.00n 0.0000)
Vbn11 bn11 0 pwl(0.00n 1.1000 4.90n 1.1000 5.00n 0.0000 9.90n 0.0000 10.00n 1.1000 14.90n 1.1000 15.00n 0.0000 19.90n 0.0000 20.00n 1.1000 25.00n 1.1000)

Vss  vss  0 0.0
Vgp  gp   0 0.0
Vgn  gn   0 0.8
Vk   k    0 {pk11}
Vkn  kn   0 {pkn11}

* 1) Tupla (NAND, NOR) - 4T (VDD=0.8V)
Vrtop_nn rtop_nn 0 {prtop08}
Vgtop_nn gtop_nn 0 {pgtop08}
Vrbot_nn rbot_nn 0 {prbot08}
Vgbot_nn gbot_nn 0 {pgbot08}
X_NN a08 b08 out_nn rtop_nn gtop_nn rbot_nn gbot_nn POLY_NAND_NOR
Cout_nn out_nn 0 0.3f

* 2) Tupla (XOR, XNOR) - 4T nucleo (VDD=1.5V, Vin=1.1V)
Vrtop_xx rtop_xx 0 {prtop15}
Vgtop_xx gtop_xx 0 {pgtop15}
Vrbot_xx rbot_xx 0 {prbot15}
Vgbot_xx gbot_xx 0 {pgbot15}
X_XX a11 an11 b11 bn11 out_xx rtop_xx gtop_xx rbot_xx gbot_xx POLY_XOR
Cout_xx out_xx 0 0.3f

* 3) Tupla (AND, OR) - 6T = POLY_NAND_NOR(4T) + BP_INV08(2T) (VDD=0.8V)
Vrtop_ao rtop_ao 0 {prtop08}
Vgtop_ao gtop_ao 0 {pgtop08}
Vrbot_ao rbot_ao 0 {prbot08}
Vgbot_ao gbot_ao 0 {pgbot08}
Vdd_ao   vdd_ao  0 0.8
X_AO_PRE a08 b08 n_ao rtop_ao gtop_ao rbot_ao gbot_ao POLY_NAND_NOR
X_AO_INV n_ao out_ao vdd_ao vss BP_INV08
Cn_ao   n_ao   0 0.1f
Cout_ao out_ao 0 0.2f

* 4) Tupla (NAND, XNOR) - 6T nucleo (VDD=1.5V, Vin=1.1V)
Vrtop_nx rtop_nx 0 {prtop15}
Vgtop_nx gtop_nx 0 {pgtop15}
Vrbot_nx rbot_nx 0 {prbot15}
Vgbot_nx gbot_nx 0 {pgbot15}
Vdd_nx   vdd_nx  0 1.5
XNX1 out_nx an11 rtop_nx b11  gtop_nx ARI W=1.0
XNX2 out_nx a11  rtop_nx bn11 gtop_nx ARI W=1.0
XNX3 out_nx a11  vdd_nx  b11  gp      ARI W=1.0
XNX4 out_nx a11  rbot_nx b11  gbot_nx ARI W=1.0
XNX5 out_nx an11 n11p_nx bn11 gp     ARI W=2.0
XNX6 n11p_nx kn  vdd_nx  kn   gp     ARI W=2.0
Cn11p_nx n11p_nx 0 0.05f
Cout_nx  out_nx  0 0.3f

* 5) Tupla (NOR, XOR) - 6T nucleo (VDD=1.5V, Vin=1.1V)
Vrtop_rx rtop_rx 0 {prtop15}
Vgtop_rx gtop_rx 0 {pgtop15}
Vrbot_rx rbot_rx 0 {prbot15}
Vgbot_rx gbot_rx 0 {pgbot15}
XRX1 out_rx an11 rbot_rx b11  gbot_rx ARI W=1.0
XRX2 out_rx a11  rbot_rx bn11 gbot_rx ARI W=1.0
XRX3 out_rx a11  vss     b11  gn      ARI W=1.0
XRX4 out_rx a11  rtop_rx b11  gtop_rx ARI W=1.0
XRX5 out_rx an11 n00n_rx bn11 gn     ARI W=2.0
XRX6 n00n_rx k   vss     k    gn     ARI W=2.0
Cn00n_rx n00n_rx 0 0.05f
Cout_rx  out_rx  0 0.3f

.control
set wr_vecnames
set wr_singlescale

* Simulacao Key = 0
tran 20p 25n
wrdata t2_k0.dat v(a08) v(b08) v(a11) v(b11)
+ v(out_nn) i(Vrtop_nn) i(Vrbot_nn)
+ v(out_xx) i(Vrtop_xx) i(Vrbot_xx)
+ v(out_ao) i(Vrtop_ao) i(Vrbot_ao) i(Vdd_ao)
+ v(out_nx) i(Vrtop_nx) i(Vrbot_nx) i(Vdd_nx)
+ v(out_rx) i(Vrtop_rx) i(Vrbot_rx)

* Simulacao Key = 1
alterparam prtop08 = 0.0
alterparam pgtop08 = 0.8
alterparam prbot08 = 0.8
alterparam pgbot08 = -0.7

alterparam prtop15 = 0.0
alterparam pgtop15 = 0.8
alterparam prbot15 = 1.5
alterparam pgbot15 = 0.0

alterparam pk11  = 1.1
alterparam pkn11 = 0.0
reset
tran 20p 25n
wrdata t2_k1.dat v(a08) v(b08) v(a11) v(b11)
+ v(out_nn) i(Vrtop_nn) i(Vrbot_nn)
+ v(out_xx) i(Vrtop_xx) i(Vrbot_xx)
+ v(out_ao) i(Vrtop_ao) i(Vrbot_ao) i(Vdd_ao)
+ v(out_nx) i(Vrtop_nx) i(Vrbot_nx) i(Vdd_nx)
+ v(out_rx) i(Vrtop_rx) i(Vrbot_rx)
.endc
.end
