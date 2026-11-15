* Porta Polimorfica XOR/XNOR de 4 Transistores BP SB-FET (Comutacao Dinamica)
.include "../00_modelo_ngspice/bp_ari_ngspice.lib"

.param supp=1.5
.param vin=1.1

Va  a  0 pwl(
+ 0n 0.0   9.9n 0.0  10.0n 1.1  19.9n 1.1
+ 20.0n 0.0  29.9n 0.0  30.0n 1.1  40.0n 1.1)
Van an 0 pwl(
+ 0n 1.1   9.9n 1.1  10.0n 0.0  19.9n 0.0
+ 20.0n 1.1  29.9n 1.1  30.0n 0.0  40.0n 0.0)

Vb  b  0 pwl(
+ 0n 0.0   4.9n 0.0   5.0n 1.1   9.9n 1.1  10.0n 0.0  14.9n 0.0  15.0n 1.1  19.9n 1.1
+ 20.0n 0.0  24.9n 0.0  25.0n 1.1  29.9n 1.1  30.0n 0.0  34.9n 0.0  35.0n 1.1  40.0n 1.1)
Vbn bn 0 pwl(
+ 0n 1.1   4.9n 1.1   5.0n 0.0   9.9n 0.0  10.0n 1.1  14.9n 1.1  15.0n 0.0  19.9n 0.0
+ 20.0n 1.1  24.9n 1.1  25.0n 0.0  29.9n 0.0  30.0n 1.1  34.9n 1.1  35.0n 0.0  40.0n 0.0)

Vkey key 0 pwl(0n 0.0 19.9n 0.0 20.0n 1.5 40.0n 1.5)

* Key=0 (0..20ns -> XOR):  rtop=1.5V (p-FET: gtop=0.0V), rbot=0.0V (n-FET: gbot=0.8V)
* Key=1 (20..40ns -> XNOR): rtop=0.0V (n-FET: gtop=0.8V), rbot=1.5V (p-FET: gbot=0.0V)
Vrtop rtop 0 pwl(0n 1.5 19.9n 1.5 20.0n 0.0 40.0n 0.0)
Vgtop gtop 0 pwl(0n 0.0 19.9n 0.0 20.0n 0.8 40.0n 0.8)
Vrbot rbot 0 pwl(0n 0.0 19.9n 0.0 20.0n 1.5 40.0n 1.5)
Vgbot gbot 0 pwl(0n 0.8 19.9n 0.8 20.0n 0.0 40.0n 0.0)

X1 out an rtop b  gtop ARI W=1.0
X2 out a  rtop bn gtop ARI W=1.0
X3 out a  rbot b  gbot ARI W=1.0
X4 out an rbot bn gbot ARI W=1.0

Cout out 0 0.3f

.control
set wr_vecnames
set wr_singlescale
tran 20p 40n
wrdata poly_xor_xnor.dat v(a) v(b) v(key) v(out) i(Vrtop) i(Vrbot)
.endc
.end
