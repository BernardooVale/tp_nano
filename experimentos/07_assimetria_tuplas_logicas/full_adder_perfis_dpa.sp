* Benchmark em Sistema: Full Adder 1-bit em 3 Perfis Arquiteturais BP SB-FET
* Perfil 1: Baseline Comum (20T nucleo, sem logic locking, sem protecao DPA)
* Perfil 2: Focado em Custo/Desempenho (28T nucleo, Cout em 3x NAND/NOR + Sum em XOR/XNOR)
* Perfil 3: Focado em Baixa Assimetria DPA (26T nucleo, Sum em XOR/XNOR + Cout em MAJ3/XOR3 10T)
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


Va11  a11  0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.0000 9.90n 0.0000 10.00n 0.0000 14.90n 0.0000 15.00n 0.0000 19.90n 0.0000 20.00n 1.1000 24.90n 1.1000 25.00n 1.1000 29.90n 1.1000 30.00n 1.1000 34.90n 1.1000 35.00n 1.1000 40.00n 1.1000)
Van11 an11 0 pwl(0.00n 1.1000 4.90n 1.1000 5.00n 1.1000 9.90n 1.1000 10.00n 1.1000 14.90n 1.1000 15.00n 1.1000 19.90n 1.1000 20.00n 0.0000 24.90n 0.0000 25.00n 0.0000 29.90n 0.0000 30.00n 0.0000 34.90n 0.0000 35.00n 0.0000 40.00n 0.0000)
Vb11  b11  0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.0000 9.90n 0.0000 10.00n 1.1000 14.90n 1.1000 15.00n 1.1000 19.90n 1.1000 20.00n 0.0000 24.90n 0.0000 25.00n 0.0000 29.90n 0.0000 30.00n 1.1000 34.90n 1.1000 35.00n 1.1000 40.00n 1.1000)
Vbn11 bn11 0 pwl(0.00n 1.1000 4.90n 1.1000 5.00n 1.1000 9.90n 1.1000 10.00n 0.0000 14.90n 0.0000 15.00n 0.0000 19.90n 0.0000 20.00n 1.1000 24.90n 1.1000 25.00n 1.1000 29.90n 1.1000 30.00n 0.0000 34.90n 0.0000 35.00n 0.0000 40.00n 0.0000)
Vc11  c11  0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 1.1000 9.90n 1.1000 10.00n 0.0000 14.90n 0.0000 15.00n 1.1000 19.90n 1.1000 20.00n 0.0000 24.90n 0.0000 25.00n 1.1000 29.90n 1.1000 30.00n 0.0000 34.90n 0.0000 35.00n 1.1000 40.00n 1.1000)
Vcn11 cn11 0 pwl(0.00n 1.1000 4.90n 1.1000 5.00n 0.0000 9.90n 0.0000 10.00n 1.1000 14.90n 1.1000 15.00n 0.0000 19.90n 0.0000 20.00n 1.1000 24.90n 1.1000 25.00n 0.0000 29.90n 0.0000 30.00n 1.1000 34.90n 1.1000 35.00n 0.0000 40.00n 0.0000)

Va08  a08  0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.0000 9.90n 0.0000 10.00n 0.0000 14.90n 0.0000 15.00n 0.0000 19.90n 0.0000 20.00n 0.8000 24.90n 0.8000 25.00n 0.8000 29.90n 0.8000 30.00n 0.8000 34.90n 0.8000 35.00n 0.8000 40.00n 0.8000)
Vb08  b08  0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.0000 9.90n 0.0000 10.00n 0.8000 14.90n 0.8000 15.00n 0.8000 19.90n 0.8000 20.00n 0.0000 24.90n 0.0000 25.00n 0.0000 29.90n 0.0000 30.00n 0.8000 34.90n 0.8000 35.00n 0.8000 40.00n 0.8000)
Vc08  c08  0 pwl(0.00n 0.0000 4.90n 0.0000 5.00n 0.8000 9.90n 0.8000 10.00n 0.0000 14.90n 0.0000 15.00n 0.8000 19.90n 0.8000 20.00n 0.0000 24.90n 0.0000 25.00n 0.8000 29.90n 0.8000 30.00n 0.0000 34.90n 0.0000 35.00n 0.8000 40.00n 0.8000)

Vss vss 0 0.0
Vgp gp  0 0.0
Vgn gn  0 0.8

* --- PERFIL 1: BASELINE COMUM (20T nucleo: 2x XOR 4T + 4x INV 2T + 1x MAJ3 4T fixo) ---
Vdd15_p1 vdd15_p1 0 1.5
Vdd11_p1 vdd11_p1 0 1.1
Vdd08_p1 vdd08_p1 0 0.8

XX1_p1 a11 an11 b11 bn11 praw_p1 vdd15_p1 gp vss gn POLY_XOR
Cp_p1  praw_p1 0 0.2f
XI1_p1 praw_p1 pn08_p1 vdd08_p1 vss BP_INV08
XI2_p1 pn08_p1 p08_p1  vdd08_p1 vss BP_INV08
XI3_p1 p08_p1  pn11_p1 vdd11_p1 vss BP_INV11
XI4_p1 pn08_p1 p11_p1  vdd11_p1 vss BP_INV11
XX2_p1 p11_p1 pn11_p1 c11 cn11 sum_p1 vdd15_p1 gp vss gn POLY_XOR
Csum_p1 sum_p1 0 0.3f

XM1_p1 cout_p1 pn11_p1 vss      an11 gn ARI W=1.0
XM2_p1 cout_p1 p11_p1  vss      cn11 gn ARI W=1.0
XM3_p1 cout_p1 p11_p1  vdd15_p1 an11 gp ARI W=1.0
XM4_p1 cout_p1 pn11_p1 vdd15_p1 cn11 gp ARI W=1.0
Ccout_p1 cout_p1 0 0.3f

* --- PERFIL 2: FOCADO EM CUSTO/DESEMPENHO (28T nucleo: NAND/NOR em Cout + XOR/XNOR em Sum) ---
.param p2_xrtop = 1.5
.param p2_xgtop = 0.0
.param p2_xrbot = 0.0
.param p2_xgbot = 0.8
.param p2_nrtop = 0.8
.param p2_ngtop = -0.4
.param p2_nrbot = 0.0
.param p2_ngbot = 0.8

Vdd15_p2  vdd15_p2 0 1.5
Vdd11_p2  vdd11_p2 0 1.1
Vdd08_p2  vdd08_p2 0 0.8
Vxrtop_p2 xrtop_p2 0 {p2_xrtop}
Vxgtop_p2 xgtop_p2 0 {p2_xgtop}
Vxrbot_p2 xrbot_p2 0 {p2_xrbot}
Vxgbot_p2 xgbot_p2 0 {p2_xgbot}
Vnrtop_p2 nrtop_p2 0 {p2_nrtop}
Vngtop_p2 ngtop_p2 0 {p2_ngtop}
Vnrbot_p2 nrbot_p2 0 {p2_nrbot}
Vngbot_p2 ngbot_p2 0 {p2_ngbot}

XX1_p2 a11 an11 b11 bn11 praw_p2 vdd15_p2 gp vss gn POLY_XOR
Cp_p2  praw_p2 0 0.2f
XI1_p2 praw_p2 pn08_p2 vdd08_p2 vss BP_INV08
XI2_p2 pn08_p2 p08_p2  vdd08_p2 vss BP_INV08
XI3_p2 p08_p2  pn11_p2 vdd11_p2 vss BP_INV11
XI4_p2 pn08_p2 p11_p2  vdd11_p2 vss BP_INV11
XX2_p2 p11_p2 pn11_p2 c11 cn11 sum_p2 xrtop_p2 xgtop_p2 xrbot_p2 xgbot_p2 POLY_XOR
Csum_p2 sum_p2 0 0.3f

XG1_p2 a08    b08    g1_p2   nrtop_p2 ngtop_p2 nrbot_p2 ngbot_p2 POLY_NAND_NOR
XG2_p2 p08_p2 c08    g2_p2   nrtop_p2 ngtop_p2 nrbot_p2 ngbot_p2 POLY_NAND_NOR
XG3_p2 g1_p2  g2_p2  cout_p2 nrtop_p2 ngtop_p2 nrbot_p2 ngbot_p2 POLY_NAND_NOR
Cg1_p2   g1_p2   0 0.1f
Cg2_p2   g2_p2   0 0.1f
Ccout_p2 cout_p2 0 0.3f

* --- PERFIL 3: FOCADO EM BAIXA ASSIMETRIA DPA (26T nucleo: XOR/XNOR + MAJ3/XOR3 10T) ---
.param p3_k     = 0.0
.param p3_kn    = 1.1
.param p3_xrtop = 1.5
.param p3_xgtop = 0.0
.param p3_xrbot = 0.0
.param p3_xgbot = 0.8
.param p3_mrtop = 0.0
.param p3_mgtop = 0.8
.param p3_mrbot = 1.5
.param p3_mgbot = 0.0

Vdd15_p3  vdd15_p3 0 1.5
Vdd15_c3  vdd15_c3 0 1.5
Vdd11_p3  vdd11_p3 0 1.1
Vdd08_p3  vdd08_p3 0 0.8
Vk_p3     k_p3     0 {p3_k}
Vkn_p3    kn_p3    0 {p3_kn}
Vxrtop_p3 xrtop_p3 0 {p3_xrtop}
Vxgtop_p3 xgtop_p3 0 {p3_xgtop}
Vxrbot_p3 xrbot_p3 0 {p3_xrbot}
Vxgbot_p3 xgbot_p3 0 {p3_xgbot}
Vmrtop_p3 mrtop_p3 0 {p3_mrtop}
Vmgtop_p3 mgtop_p3 0 {p3_mgtop}
Vmrbot_p3 mrbot_p3 0 {p3_mrbot}
Vmgbot_p3 mgbot_p3 0 {p3_mgbot}

XX1_p3 a11 an11 b11 bn11 praw_p3 vdd15_p3 gp vss gn POLY_XOR
Cp_p3  praw_p3 0 0.2f
XI1_p3 praw_p3 pn08_p3 vdd08_p3 vss BP_INV08
XI2_p3 pn08_p3 p08_p3  vdd08_p3 vss BP_INV08
XI3_p3 p08_p3  pn11_p3 vdd11_p3 vss BP_INV11
XI4_p3 pn08_p3 p11_p3  vdd11_p3 vss BP_INV11
XX2_p3 p11_p3 pn11_p3 c11 cn11 sum_p3 xrtop_p3 xgtop_p3 xrbot_p3 xgbot_p3 POLY_XOR
Csum_p3 sum_p3 0 0.3f

XM2_p3  cout_p3 p11_p3  mrtop_p3 cn11  mgtop_p3 ARI W=1.0
XM4_p3  cout_p3 pn11_p3 mrbot_p3 cn11  mgbot_p3 ARI W=1.0
XM1a_p3 cout_p3 pn11_p3 n1a_p3   an11  gn       ARI W=2.0
XM1b_p3 n1a_p3  kn_p3   vss      kn_p3 gn       ARI W=2.0
XM1c_p3 cout_p3 pn11_p3 n1c_p3   c11   gp       ARI W=2.0
XM1d_p3 n1c_p3  kn_p3   vdd15_c3 kn_p3 gp       ARI W=2.0
XM3a_p3 cout_p3 p11_p3  n3a_p3   an11  gp       ARI W=2.0
XM3b_p3 n3a_p3  k_p3    vdd15_c3 k_p3  gp       ARI W=2.0
XM3c_p3 cout_p3 p11_p3  n3c_p3   c11   gn       ARI W=2.0
XM3d_p3 n3c_p3  k_p3    vss      k_p3  gn       ARI W=2.0
Cn1a_p3  n1a_p3  0 0.05f
Cn1c_p3  n1c_p3  0 0.05f
Cn3a_p3  n3a_p3  0 0.05f
Cn3c_p3  n3c_p3  0 0.05f
Ccout_p3 cout_p3 0 0.3f

.control
set wr_vecnames
set wr_singlescale

* Chave K = 00 (Modo Funcional Correto para todos os perfis)
tran 20p 40n
wrdata fa_p1.dat    v(a08) v(b08) v(c08) v(sum_p1) v(cout_p1) i(Vdd15_p1) i(Vdd11_p1) i(Vdd08_p1)
wrdata fa_p2_k0.dat v(a08) v(b08) v(c08) v(sum_p2) v(cout_p2) i(Vdd15_p2) i(Vdd11_p2) i(Vdd08_p2) i(Vxrtop_p2) i(Vxrbot_p2) i(Vnrtop_p2) i(Vnrbot_p2)
wrdata fa_p3_k0.dat v(a08) v(b08) v(c08) v(sum_p3) v(cout_p3) i(Vdd15_p3) i(Vdd11_p3) i(Vdd08_p3) i(Vxrtop_p3) i(Vxrbot_p3) i(Vmrtop_p3) i(Vmrbot_p3) i(Vdd15_c3)

* Chave K = 11 (Modo Oposto para Perfil 2 e Perfil 3)
alterparam p2_xrtop = 0.0
alterparam p2_xgtop = 0.8
alterparam p2_xrbot = 1.5
alterparam p2_xgbot = 0.0
alterparam p2_nrtop = 0.0
alterparam p2_ngtop = 0.8
alterparam p2_nrbot = 0.8
alterparam p2_ngbot = -0.7

alterparam p3_k     = 1.1
alterparam p3_kn    = 0.0
alterparam p3_xrtop = 0.0
alterparam p3_xgtop = 0.8
alterparam p3_xrbot = 1.5
alterparam p3_xgbot = 0.0
alterparam p3_mrtop = 1.5
alterparam p3_mgtop = 0.0
alterparam p3_mrbot = 0.0
alterparam p3_mgbot = 0.8
reset
tran 20p 40n
wrdata fa_p2_k1.dat v(a08) v(b08) v(c08) v(sum_p2) v(cout_p2) i(Vdd15_p2) i(Vdd11_p2) i(Vdd08_p2) i(Vxrtop_p2) i(Vxrbot_p2) i(Vnrtop_p2) i(Vnrbot_p2)
wrdata fa_p3_k1.dat v(a08) v(b08) v(c08) v(sum_p3) v(cout_p3) i(Vdd15_p3) i(Vdd11_p3) i(Vdd08_p3) i(Vxrtop_p3) i(Vxrbot_p3) i(Vmrtop_p3) i(Vmrbot_p3) i(Vdd15_c3)
.endc
.end
