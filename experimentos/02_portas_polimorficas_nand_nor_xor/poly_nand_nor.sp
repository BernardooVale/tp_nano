* Porta Polimorfica NAND/NOR de 4 Transistores BP SB-FET (Comutacao Dinamica)
.include "../00_modelo_ngspice/bp_ari_ngspice.lib"

.param supp=0.8

* Entradas A e B percorrendo 00, 01, 10, 11 em cada semi-ciclo de 20ns
Va a 0 pwl(
+ 0n 0.0   9.9n 0.0  10.0n 0.8  19.9n 0.8
+ 20.0n 0.0  29.9n 0.0  30.0n 0.8  40.0n 0.8)
Vb b 0 pwl(
+ 0n 0.0   4.9n 0.0   5.0n 0.8   9.9n 0.8  10.0n 0.0  14.9n 0.0  15.0n 0.8  19.9n 0.8
+ 20.0n 0.0  24.9n 0.0  25.0n 0.8  29.9n 0.8  30.0n 0.0  34.9n 0.0  35.0n 0.8  40.0n 0.8)

* Sinal indicador de chave (Key=0 -> 0V, Key=1 -> 0.8V)
Vkey key 0 pwl(0n 0.0 19.9n 0.0 20.0n 0.8 40.0n 0.8)

* Trilhos de alimentacao polimorficos e portas de polaridade
* Rede paralela (topo): Key=0 -> VDD=0.8V, p-FET (Vg=-0.4V); Key=1 -> VSS=0.0V, n-FET (Vg=+0.8V)
Vrtop rtop 0 pwl(0n 0.8 19.9n 0.8 20.0n 0.0 40.0n 0.0)
Vgtop gtop 0 pwl(0n -0.4 19.9n -0.4 20.0n 0.8 40.0n 0.8)

* Rede serie (base): Key=0 -> VSS=0.0V, n-FET (Vg=+0.8V); Key=1 -> VDD=0.8V, p-FET (Vg=-0.7V)
Vrbot rbot 0 pwl(0n 0.0 19.9n 0.0 20.0n 0.8 40.0n 0.8)
Vgbot gbot 0 pwl(0n 0.8 19.9n 0.8 20.0n -0.7 40.0n -0.7)

* 4 Transistores BP SB-FET
X1 out a rtop gtop gtop ARI W=1.0
X2 out b rtop gtop gtop ARI W=1.0
X3 out b n1   gbot gbot ARI W=2.0
X4 n1  a rbot gbot gbot ARI W=2.0

Cout out 0 0.3f
Cn1  n1  0 0.1f

.control
set wr_vecnames
set wr_singlescale
tran 20p 40n
wrdata poly_nand_nor.dat v(a) v(b) v(key) v(out) i(Vrtop) i(Vrbot)
.endc
.end
