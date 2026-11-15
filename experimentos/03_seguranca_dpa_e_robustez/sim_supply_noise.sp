* Varredura Parametrica de Ruido de Fonte (VDD x VSS) na Porta NAND BP SB-FET
.include "../00_modelo_ngspice/bp_ari_ngspice.lib"
.param pvdd=0.8
.param pvss=0.0
Vrtop rtop 0 {pvdd}
Vrbot rbot 0 {pvss}
Vgtop gtop 0 -0.4
Vgbot gbot 0 0.8
Va a 0 0.0
Vb b 0 0.0
X1 out a rtop gtop gtop ARI W=1.0
X2 out b rtop gtop gtop ARI W=1.0
X3 out b n1   gbot gbot ARI W=2.0
X4 n1  a rbot gbot gbot ARI W=2.0
.control
set wr_vecnames
set wr_singlescale
alterparam pvdd = 0.65
alterparam pvss = -0.1
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d650_sm0d100.dat v(out)
alter Va = 0.65
alter Vb = 0.65
op
wrdata sweep_11_v0d650_sm0d100.dat v(out)
alterparam pvdd = 0.65
alterparam pvss = -0.05
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d650_sm0d050.dat v(out)
alter Va = 0.65
alter Vb = 0.65
op
wrdata sweep_11_v0d650_sm0d050.dat v(out)
alterparam pvdd = 0.65
alterparam pvss = 0.0
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d650_sp0d000.dat v(out)
alter Va = 0.65
alter Vb = 0.65
op
wrdata sweep_11_v0d650_sp0d000.dat v(out)
alterparam pvdd = 0.65
alterparam pvss = 0.05
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d650_sp0d050.dat v(out)
alter Va = 0.65
alter Vb = 0.65
op
wrdata sweep_11_v0d650_sp0d050.dat v(out)
alterparam pvdd = 0.65
alterparam pvss = 0.1
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d650_sp0d100.dat v(out)
alter Va = 0.65
alter Vb = 0.65
op
wrdata sweep_11_v0d650_sp0d100.dat v(out)
alterparam pvdd = 0.725
alterparam pvss = -0.1
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d725_sm0d100.dat v(out)
alter Va = 0.725
alter Vb = 0.725
op
wrdata sweep_11_v0d725_sm0d100.dat v(out)
alterparam pvdd = 0.725
alterparam pvss = -0.05
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d725_sm0d050.dat v(out)
alter Va = 0.725
alter Vb = 0.725
op
wrdata sweep_11_v0d725_sm0d050.dat v(out)
alterparam pvdd = 0.725
alterparam pvss = 0.0
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d725_sp0d000.dat v(out)
alter Va = 0.725
alter Vb = 0.725
op
wrdata sweep_11_v0d725_sp0d000.dat v(out)
alterparam pvdd = 0.725
alterparam pvss = 0.05
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d725_sp0d050.dat v(out)
alter Va = 0.725
alter Vb = 0.725
op
wrdata sweep_11_v0d725_sp0d050.dat v(out)
alterparam pvdd = 0.725
alterparam pvss = 0.1
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d725_sp0d100.dat v(out)
alter Va = 0.725
alter Vb = 0.725
op
wrdata sweep_11_v0d725_sp0d100.dat v(out)
alterparam pvdd = 0.8
alterparam pvss = -0.1
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d800_sm0d100.dat v(out)
alter Va = 0.8
alter Vb = 0.8
op
wrdata sweep_11_v0d800_sm0d100.dat v(out)
alterparam pvdd = 0.8
alterparam pvss = -0.05
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d800_sm0d050.dat v(out)
alter Va = 0.8
alter Vb = 0.8
op
wrdata sweep_11_v0d800_sm0d050.dat v(out)
alterparam pvdd = 0.8
alterparam pvss = 0.0
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d800_sp0d000.dat v(out)
alter Va = 0.8
alter Vb = 0.8
op
wrdata sweep_11_v0d800_sp0d000.dat v(out)
alterparam pvdd = 0.8
alterparam pvss = 0.05
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d800_sp0d050.dat v(out)
alter Va = 0.8
alter Vb = 0.8
op
wrdata sweep_11_v0d800_sp0d050.dat v(out)
alterparam pvdd = 0.8
alterparam pvss = 0.1
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d800_sp0d100.dat v(out)
alter Va = 0.8
alter Vb = 0.8
op
wrdata sweep_11_v0d800_sp0d100.dat v(out)
alterparam pvdd = 0.875
alterparam pvss = -0.1
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d875_sm0d100.dat v(out)
alter Va = 0.875
alter Vb = 0.875
op
wrdata sweep_11_v0d875_sm0d100.dat v(out)
alterparam pvdd = 0.875
alterparam pvss = -0.05
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d875_sm0d050.dat v(out)
alter Va = 0.875
alter Vb = 0.875
op
wrdata sweep_11_v0d875_sm0d050.dat v(out)
alterparam pvdd = 0.875
alterparam pvss = 0.0
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d875_sp0d000.dat v(out)
alter Va = 0.875
alter Vb = 0.875
op
wrdata sweep_11_v0d875_sp0d000.dat v(out)
alterparam pvdd = 0.875
alterparam pvss = 0.05
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d875_sp0d050.dat v(out)
alter Va = 0.875
alter Vb = 0.875
op
wrdata sweep_11_v0d875_sp0d050.dat v(out)
alterparam pvdd = 0.875
alterparam pvss = 0.1
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d875_sp0d100.dat v(out)
alter Va = 0.875
alter Vb = 0.875
op
wrdata sweep_11_v0d875_sp0d100.dat v(out)
alterparam pvdd = 0.95
alterparam pvss = -0.1
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d950_sm0d100.dat v(out)
alter Va = 0.95
alter Vb = 0.95
op
wrdata sweep_11_v0d950_sm0d100.dat v(out)
alterparam pvdd = 0.95
alterparam pvss = -0.05
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d950_sm0d050.dat v(out)
alter Va = 0.95
alter Vb = 0.95
op
wrdata sweep_11_v0d950_sm0d050.dat v(out)
alterparam pvdd = 0.95
alterparam pvss = 0.0
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d950_sp0d000.dat v(out)
alter Va = 0.95
alter Vb = 0.95
op
wrdata sweep_11_v0d950_sp0d000.dat v(out)
alterparam pvdd = 0.95
alterparam pvss = 0.05
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d950_sp0d050.dat v(out)
alter Va = 0.95
alter Vb = 0.95
op
wrdata sweep_11_v0d950_sp0d050.dat v(out)
alterparam pvdd = 0.95
alterparam pvss = 0.1
reset
alter Va = 0.0
alter Vb = 0.0
op
wrdata sweep_00_v0d950_sp0d100.dat v(out)
alter Va = 0.95
alter Vb = 0.95
op
wrdata sweep_11_v0d950_sp0d100.dat v(out)
.endc
.end
