*
.hdl "bp_ari.va"
.ic V(out)=0

.OP ALL
.OPTION ACCT NODE OPTS LIST LIMTIM=50
+ GMIN=1.00E-12 RELTOL=0.01 ABSTOL=1.00E-12
+ VNTOL=1.00E-06 TRTOL=7.00E+00
+ ITL1=400 ITL2=100 ITL4=100 ITL6=100
+ LVLTIM=2.00E+00 TNOM=+2.50E+01 LIMPTS=99999
+ CHGTOL=1.00E-14
+ MAXORD= .20E+01
+ DELMAX= .00E+00
+ METHOD=GEAR
+ POST
+ CONVERGE=1

.param inputvoltage=1.1
.param supp=1.5

Vdd vdd 0 supp
Vss vss 0 0

Va a 0 pulse '0*inputvoltage' inputvoltage 1n 10p 10p 5n 12n
Vb b 0 pulse '0*inputvoltage' inputvoltage 4n 10p 10p 5n 12n

Van an 0 pulse inputvoltage '0*inputvoltage' 1n 10p 10p 5n 12n
Vbn bn 0 pulse inputvoltage '0*inputvoltage' 4n 10p 10p 5n 12n


Vg2a g2a 0 0
Vg2b g2b 0 .8

************************************************************************************
XARI_1 out an vdd b g2a ARI W=1
XARI_2 out a vdd bn g2a ARI W=1

XARI_3 out a vss b g2b ARI W=1
XARI_4 out an vss bn g2b ARI W=1


*Cout out vss 10f



.PRINT tran V(a) V(b) V(out) I(vdd)

.tran 10p 23ns

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
