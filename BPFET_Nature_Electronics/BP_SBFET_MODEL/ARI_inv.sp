*
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

.param inputvoltage=0.3
.param supp=1

Vdd vdd 0 supp
Vss vss 0 0

Va a 0 pulse '0*inputvoltage' inputvoltage 1n 1p 1p 5n 12n
Vb b 0 pulse '0*inputvoltage' inputvoltage 3n 1p 1p 5n 12n

Vg1a g1a 0 0.8
Vg2a g2a 0 1.1

Vg1b 0 g1b 0.5
Vg2b 0 g2b 0.5

************************************************************************************

XARI_1 out a vdd g1b g2b ARI W=1
XARI_2 out a vss g1a g2a ARI W=1



.PRINT tran V(a) V(b) V(ctrl1) V(ctrl2) V(out) I(vdd)

.tran 1p 23ns

.measure NAND_Ipeak_00_10 max par('abs(I(vdd))') from=1n to=2n
.measure NAND_pwr_00_10 avg par('abs(I(vdd))*supp') from=1n to=2n

.measure NAND_Ipeak_10_11 max par('abs(I(vdd))') from=3n to=4n
.measure NAND_pwr_10_11 avg par('abs(I(vdd))*supp') from=3n to=4n

.measure NAND_Ipeak_11_01 max par('abs(I(vdd))') from=7n to=8n
.measure NAND_pwr_11_01 avg par('abs(I(vdd))*supp') from=7n to=8n

.measure NAND_Ipeak_01_00 max par('abs(I(vdd))') from=9n to=10n
.measure NAND_pwr_01_00 avg par('abs(I(vdd))*supp') from=9n to=10n

.measure NOR_Ipeak_00_10 max par('abs(I(vdd))') from=13n to=14n
.measure NOR_pwr_00_10 avg par('abs(I(vdd))*supp') from=13n to=14n

.measure NOR_Ipeak_10_11 max par('abs(I(vdd))') from=15n to=16n
.measure NOR_pwr_10_11 avg par('abs(I(vdd))*supp') from=15n to=16n

.measure NOR_Ipeak_11_01 max par('abs(I(vdd))') from=19n to=20n
.measure NOR_pwr_11_01 avg par('abs(I(vdd))*supp') from=19n to=20n

.measure NOR_Ipeak_01_00 max par('abs(I(vdd))') from=21n to=22n
.measure NOR_pwr_01_00 avg par('abs(I(vdd))*supp') from=21n to=22n



.end
