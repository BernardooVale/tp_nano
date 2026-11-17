* Testbench Padronizado para Tuplas Polimorficas de 3 Entradas (Cload = 0.3 fF)
* Tuplas: (AOI21, OAI21) 6T e (MAJ3, XOR3) 10T estagio / 18T c/ gerador P=A^B
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


.param prtop_aoi = 0.8
.param pgtop_aoi = -0.5
.param prbot_aoi = 0.0
.param pgbot_aoi = 0.8

.param pk_mx     = 0.0
.param pkn_mx    = 1.1
.param prtop_mx  = 0.0
.param pgtop_mx  = 0.8
.param prbot_mx  = 1.5
.param pgbot_mx  = 0.0

* Entradas de 3 bits (000..111 -> 000 em 45 ns)
Va08 a08 0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.0000 9.90n 0.0000 10.00n 0.0000 14.90n 0.0000 15.00n 0.0000 19.90n 0.0000 20.00n 0.8000 24.90n 0.8000 25.00n 0.8000 29.90n 0.8000 30.00n 0.8000 34.90n 0.8000 35.00n 0.8000 39.90n 0.8000 40.00n 0.0000 45.00n 0.0000)
Vb08 b08 0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.0000 9.90n 0.0000 10.00n 0.8000 14.90n 0.8000 15.00n 0.8000 19.90n 0.8000 20.00n 0.0000 24.90n 0.0000 25.00n 0.0000 29.90n 0.0000 30.00n 0.8000 34.90n 0.8000 35.00n 0.8000 39.90n 0.8000 40.00n 0.0000 45.00n 0.0000)
Vc08 c08 0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.8000 9.90n 0.8000 10.00n 0.0000 14.90n 0.0000 15.00n 0.8000 19.90n 0.8000 20.00n 0.0000 24.90n 0.0000 25.00n 0.8000 29.90n 0.8000 30.00n 0.0000 34.90n 0.0000 35.00n 0.8000 39.90n 0.8000 40.00n 0.0000 45.00n 0.0000)

Va11  a11  0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.0000 9.90n 0.0000 10.00n 0.0000 14.90n 0.0000 15.00n 0.0000 19.90n 0.0000 20.00n 1.1000 24.90n 1.1000 25.00n 1.1000 29.90n 1.1000 30.00n 1.1000 34.90n 1.1000 35.00n 1.1000 39.90n 1.1000 40.00n 0.0000 45.00n 0.0000)
Van11 an11 0 pwl(0.00n 1.1000 4.90n 1.1000 5.00n 1.1000 9.90n 1.1000 10.00n 1.1000 14.90n 1.1000 15.00n 1.1000 19.90n 1.1000 20.00n 0.0000 24.90n 0.0000 25.00n 0.0000 29.90n 0.0000 30.00n 0.0000 34.90n 0.0000 35.00n 0.0000 39.90n 0.0000 40.00n 1.1000 45.00n 1.1000)
Vb11  b11  0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.0000 9.90n 0.0000 10.00n 1.1000 14.90n 1.1000 15.00n 1.1000 19.90n 1.1000 20.00n 0.0000 24.90n 0.0000 25.00n 0.0000 29.90n 0.0000 30.00n 1.1000 34.90n 1.1000 35.00n 1.1000 39.90n 1.1000 40.00n 0.0000 45.00n 0.0000)
Vbn11 bn11 0 pwl(0.00n 1.1000 4.90n 1.1000 5.00n 1.1000 9.90n 1.1000 10.00n 0.0000 14.90n 0.0000 15.00n 0.0000 19.90n 0.0000 20.00n 1.1000 24.90n 1.1000 25.00n 1.1000 29.90n 1.1000 30.00n 0.0000 34.90n 0.0000 35.00n 0.0000 39.90n 0.0000 40.00n 1.1000 45.00n 1.1000)
Vc11  c11  0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 1.1000 9.90n 1.1000 10.00n 0.0000 14.90n 0.0000 15.00n 1.1000 19.90n 1.1000 20.00n 0.0000 24.90n 0.0000 25.00n 1.1000 29.90n 1.1000 30.00n 0.0000 34.90n 0.0000 35.00n 1.1000 39.90n 1.1000 40.00n 0.0000 45.00n 0.0000)
Vcn11 cn11 0 pwl(0.00n 1.1000 4.90n 1.1000 5.00n 0.0000 9.90n 0.0000 10.00n 1.1000 14.90n 1.1000 15.00n 0.0000 19.90n 0.0000 20.00n 1.1000 24.90n 1.1000 25.00n 0.0000 29.90n 0.0000 30.00n 1.1000 34.90n 1.1000 35.00n 0.0000 39.90n 0.0000 40.00n 1.1000 45.00n 1.1000)

Vss  vss  0 0.0
Vgp  gp   0 0.0
Vgn  gn   0 0.8

* 6) Tupla (AOI21, OAI21) - 6T (VDD=0.8V)
Vrtop_aoi rtop_aoi 0 {prtop_aoi}
Vgtop_aoi gtop_aoi 0 {pgtop_aoi}
Vrbot_aoi rbot_aoi 0 {prbot_aoi}
Vgbot_aoi gbot_aoi 0 {pgbot_aoi}

XAOI1 ntop_aoi a08 rtop_aoi gtop_aoi gtop_aoi ARI W=1.5
XAOI2 ntop_aoi b08 rtop_aoi gtop_aoi gtop_aoi ARI W=1.5
XAOI3 out_aoi  c08 ntop_aoi gtop_aoi gtop_aoi ARI W=2.5
XAOI4 out_aoi  b08 nbot_aoi gbot_aoi gbot_aoi ARI W=2.5
XAOI5 nbot_aoi a08 rbot_aoi gbot_aoi gbot_aoi ARI W=2.5
XAOI6 out_aoi  c08 rbot_aoi gbot_aoi gbot_aoi ARI W=1.5
Cnt_aoi  ntop_aoi 0 0.05f
Cnb_aoi  nbot_aoi 0 0.05f
Cout_aoi out_aoi  0 0.3f

* 7) Tupla (MAJ3, XOR3) - Gerador P=A^B (8T) + Nucleo Polimorfico 10T (VDD=1.5V, Vin=1.1V)
Vdd15_pre vdd15_pre 0 1.5
Vdd11_pre vdd11_pre 0 1.1
Vdd08_pre vdd08_pre 0 0.8
Vdd15_mx  vdd15_mx  0 1.5
Vk_mx     k_mx      0 {pk_mx}
Vkn_mx    kn_mx     0 {pkn_mx}
Vrtop_mx  rtop_mx   0 {prtop_mx}
Vgtop_mx  gtop_mx   0 {pgtop_mx}
Vrbot_mx  rbot_mx   0 {prbot_mx}
Vgbot_mx  gbot_mx   0 {pgbot_mx}

XX_PRE a11 an11 b11 bn11 p_raw vdd15_pre gp vss gn POLY_XOR
Cp_raw p_raw 0 0.2f
XI_P1  p_raw pn08 vdd08_pre vss BP_INV08
XI_P2  pn08  p08  vdd08_pre vss BP_INV08
XI_P3  p08   pn11 vdd11_pre vss BP_INV11
XI_P4  pn08  p11  vdd11_pre vss BP_INV11

* Nucleo polimorfico 10T quad-simetrico (Key=0 -> MAJ3, Key=1 -> XOR3)
XM2  out_mx p11  rtop_mx  cn11  gtop_mx ARI W=1.0
XM4  out_mx pn11 rbot_mx  cn11  gbot_mx ARI W=1.0
XM1a out_mx pn11 n1a_mx   an11  gn      ARI W=2.0
XM1b n1a_mx kn_mx vss     kn_mx gn      ARI W=2.0
XM1c out_mx pn11 n1c_mx   c11   gp      ARI W=2.0
XM1d n1c_mx kn_mx vdd15_mx kn_mx gp     ARI W=2.0
XM3a out_mx p11  n3a_mx   an11  gp      ARI W=2.0
XM3b n3a_mx k_mx vdd15_mx k_mx  gp      ARI W=2.0
XM3c out_mx p11  n3c_mx   c11   gn      ARI W=2.0
XM3d n3c_mx k_mx vss      k_mx  gn      ARI W=2.0
Cn1a_mx n1a_mx 0 0.05f
Cn1c_mx n1c_mx 0 0.05f
Cn3a_mx n3a_mx 0 0.05f
Cn3c_mx n3c_mx 0 0.05f
Cout_mx out_mx 0 0.3f

.control
set wr_vecnames
set wr_singlescale

* Key = 0 (AOI21 e MAJ3)
tran 20p 45n
wrdata t3_k0.dat v(a08) v(b08) v(c08) v(a11) v(b11) v(c11)
+ v(out_aoi) i(Vrtop_aoi) i(Vrbot_aoi)
+ v(out_mx)  i(Vrtop_mx)  i(Vrbot_mx) i(Vdd15_mx) i(Vdd15_pre) i(Vdd11_pre) i(Vdd08_pre)

* Key = 1 (OAI21 e XOR3)
alterparam prtop_aoi = 0.0
alterparam pgtop_aoi = 0.8
alterparam prbot_aoi = 0.8
alterparam pgbot_aoi = -0.7

alterparam pk_mx     = 1.1
alterparam pkn_mx    = 0.0
alterparam prtop_mx  = 1.5
alterparam pgtop_mx  = 0.0
alterparam prbot_mx  = 0.0
alterparam pgbot_mx  = 0.8
reset
tran 20p 45n
wrdata t3_k1.dat v(a08) v(b08) v(c08) v(a11) v(b11) v(c11)
+ v(out_aoi) i(Vrtop_aoi) i(Vrbot_aoi)
+ v(out_mx)  i(Vrtop_mx)  i(Vrbot_mx) i(Vdd15_mx) i(Vdd15_pre) i(Vdd11_pre) i(Vdd08_pre)
.endc
.end

