* Somador Completo (Full Adder 1-bit) Polimorfico com Ofuscacao Logica 2-bits (K1, K0)
* Arquitetura: 2x XOR/XNOR 4T + 4x Inversores 2T de Condicionamento + 3x NAND/NOR 4T (28 BP SB-FETs)
.include "../00_modelo_ngspice/bp_ari_ngspice.lib"

* Parametros padrao correspondentes a Chave Correta K1=0 (NAND), K0=0 (XOR)
.param pxrtop1 = 1.5
.param pxgtop1 = 0.0
.param pxrbot1 = 0.0
.param pxgbot1 = 0.8

.param pnrtop  = 0.8
.param pngtop  = -0.4
.param pnrbot  = 0.0
.param pngbot  = 0.8

* --- Subcircuitos Polimorficos e de Condicionamento ---
.subckt POLY_XOR a an b bn out rtop gtop rbot gbot
X1 out an rtop b  gtop ARI W=1.0
X2 out a  rtop bn gtop ARI W=1.0
X3 out a  rbot b  gbot ARI W=1.0
X4 out an rbot bn gbot ARI W=1.0
Cout out 0 0.2f
.ends POLY_XOR

.subckt POLY_NAND_NOR a b out rtop gtop rbot gbot
X1 out a rtop gtop gtop ARI W=1.0
X2 out b rtop gtop gtop ARI W=1.0
X3 out b n1   gbot gbot ARI W=2.0
X4 n1  a rbot gbot gbot ARI W=2.0
Cout out 0 0.2f
Cn1  n1  0 0.05f
.ends POLY_NAND_NOR

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

* Alimentacoes principais
Vdd08 vdd08 0 0.8
Vdd11 vdd11 0 1.1
Vss   vss   0 0.0

* Trilhos e polarizacoes das chaves K0 (XXOR1) e K1 (XG1..XG3)
Vxrtop1 xrtop1 0 {pxrtop1}
Vxgtop1 xgtop1 0 {pxgtop1}
Vxrbot1 xrbot1 0 {pxrbot1}
Vxgbot1 xgbot1 0 {pxgbot1}

Vxrtop2 xrtop2 0 1.5
Vxgtop2 xgtop2 0 0.0
Vxrbot2 xrbot2 0 0.0
Vxgbot2 xgbot2 0 0.8

Vnrtop  nrtop  0 {pnrtop}
Vngtop  ngtop  0 {pngtop}
Vnrbot  nrbot  0 {pnrbot}
Vngbot  ngbot  0 {pngbot}

* Padrao exaustivo de 8 vetores (A, B, Cin) de 5ns cada -> 40ns totais
Va11  a11  0 pwl(0n 0 19.9n 0 20.0n 1.1 40n 1.1)
Van11 an11 0 pwl(0n 1.1 19.9n 1.1 20.0n 0 40n 0)
Vb11  b11  0 pwl(0n 0 9.9n 0 10.0n 1.1 19.9n 1.1 20.0n 0 29.9n 0 30.0n 1.1 40n 1.1)
Vbn11 bn11 0 pwl(0n 1.1 9.9n 1.1 10.0n 0 19.9n 0 20.0n 1.1 29.9n 1.1 30.0n 0 40n 0)
Vc11  c11  0 pwl(0n 0 4.9n 0 5.0n 1.1 9.9n 1.1 10.0n 0 14.9n 0 15.0n 1.1 19.9n 1.1 20.0n 0 24.9n 0 25.0n 1.1 29.9n 1.1 30.0n 0 34.9n 0 35.0n 1.1 40n 1.1)
Vcn11 cn11 0 pwl(0n 1.1 4.9n 1.1 5.0n 0 9.9n 0 10.0n 1.1 14.9n 1.1 15.0n 0 19.9n 0 20.0n 1.1 24.9n 1.1 25.0n 0 29.9n 0 30.0n 1.1 34.9n 1.1 35.0n 0 40n 0)

Va08  a08  0 pwl(0n 0 19.9n 0 20.0n 0.8 40n 0.8)
Vb08  b08  0 pwl(0n 0 9.9n 0 10.0n 0.8 19.9n 0.8 20.0n 0 29.9n 0 30.0n 0.8 40n 0.8)
Vc08  c08  0 pwl(0n 0 4.9n 0 5.0n 0.8 9.9n 0.8 10.0n 0 14.9n 0 15.0n 0.8 19.9n 0.8 20.0n 0 24.9n 0 25.0n 0.8 29.9n 0.8 30.0n 0 34.9n 0 35.0n 0.8 40n 0.8)

* Estagio 1: XXOR1 polimorfico (K0=0 -> XOR, K0=1 -> XNOR) + Condicionamento p/ 0.8V e 1.1V
XXOR1 a11 an11 b11 bn11 p_raw xrtop1 xgtop1 xrbot1 xgbot1 POLY_XOR
XINV1 p_raw pn08 vdd08 vss BP_INV08
XINV2 pn08  p08  vdd08 vss BP_INV08
XINV3 p08   pn11 vdd11 vss BP_INV11
XINV4 pn08  p11  vdd11 vss BP_INV11

* Estagio 2: Soma Sum = P (+) Cin
XXOR2 p11 pn11 c11 cn11 sum_out xrtop2 xgtop2 xrbot2 xgbot2 POLY_XOR

* Estagio 3: Arvore Carry-Out com 3 portas NAND/NOR polimorficas (K1=0 -> NAND, K1=1 -> NOR)
XG1 a08    b08    g1_out   nrtop ngtop nrbot ngbot POLY_NAND_NOR
XG2 p08    c08    g2_out   nrtop ngtop nrbot ngbot POLY_NAND_NOR
XG3 g1_out g2_out cout_out nrtop ngtop nrbot ngbot POLY_NAND_NOR

.control
set wr_vecnames
set wr_singlescale

* 1) Chave K1K0 = 00 (XOR + NAND -> Somador Completo Exato)
tran 20p 40n
wrdata fa_k00.dat v(a08) v(b08) v(c08) v(p08) v(sum_out) v(cout_out) i(Vxrtop1) i(Vnrtop)

* 2) Chave K1K0 = 01 (XNOR + NAND)
alterparam pxrtop1 = 0.0
alterparam pxgtop1 = 0.8
alterparam pxrbot1 = 1.5
alterparam pxgbot1 = 0.0
reset
tran 20p 40n
wrdata fa_k01.dat v(a08) v(b08) v(c08) v(p08) v(sum_out) v(cout_out) i(Vxrtop1) i(Vnrtop)

* 3) Chave K1K0 = 10 (XOR + NOR)
alterparam pxrtop1 = 1.5
alterparam pxgtop1 = 0.0
alterparam pxrbot1 = 0.0
alterparam pxgbot1 = 0.8
alterparam pnrtop  = 0.0
alterparam pngtop  = 0.8
alterparam pnrbot  = 0.8
alterparam pngbot  = -0.7
reset
tran 20p 40n
wrdata fa_k10.dat v(a08) v(b08) v(c08) v(p08) v(sum_out) v(cout_out) i(Vxrtop1) i(Vnrtop)

* 4) Chave K1K0 = 11 (XNOR + NOR)
alterparam pxrtop1 = 0.0
alterparam pxgtop1 = 0.8
alterparam pxrbot1 = 1.5
alterparam pxgbot1 = 0.0
reset
tran 20p 40n
wrdata fa_k11.dat v(a08) v(b08) v(c08) v(p08) v(sum_out) v(cout_out) i(Vxrtop1) i(Vnrtop)
.endc
.end
