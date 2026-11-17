"""
Módulo 07 — Trade-off entre Assimetria de Potência (DPA) e Custo de Hardware em Tuplas Polimórficas BP SB-FET.

Implementa integralmente a proposta de `experimentos/proposta_assimetria_tuplas.md`:
1. Testbench padrão em `ngspice-47` (`Cload = 0.3 fF`) para 7 tuplas polimórficas:
   - 2 entradas (`tuplas_2entradas.sp`):
     (NAND, NOR), (XOR, XNOR), (AND, OR), (NAND, XNOR), (NOR, XOR)
   - 3 entradas (`tuplas_3entradas.sp`):
     (AOI21, OAI21), (MAJ3, XOR3)
2. Verificação 100% exata das 2^n combinações em Key=0 e Key=1 (`tabelas_verdade_tuplas.csv`).
3. Extração padronizada de assimetria DPA (pico, média e transições 0->1 / 1->0),
   custo em área (nº de transistores núcleo/total e soma W), atraso (tpLH/tpHL),
   potência estática/média, energia de chaveamento e PDP (`metricas_tuplas_dpa.csv`).
4. Varredura de ruído nos trilhos no `ngspice` (`sim_robustez_tuplas.sp`) e análise
   estatística Monte Carlo (N = 250 amostras por tupla).
5. Benchmark em sistema (`full_adder_perfis_dpa.sp`) comparando 3 perfis de Full Adder 1-bit:
   - Perfil 1: Baseline (Comum, sem portas polimórficas)
   - Perfil 2: Focado em Custo/Desempenho (NAND/NOR + XOR/XNOR)
   - Perfil 3: Focado em Baixa Assimetria DPA (XOR/XNOR + MAJ3/XOR3)
"""

import os
import subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
NGSPICE_EXE = os.path.join(ROOT_DIR, "ngspice-47_64", "Spice64", "bin", "ngspice_con.exe")
LIB_REL = "../00_modelo_ngspice/bp_ari_ngspice.lib"


def run_ngspice(sp_filename):
    """Executa netlist no ngspice_con.exe em modo batch e valida saída."""
    sp_path = os.path.join(BASE_DIR, sp_filename)
    proc = subprocess.run(
        [NGSPICE_EXE, "-b", sp_path],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or "aborted" in proc.stderr.lower():
        raise RuntimeError(
            f"ngspice falhou ({proc.returncode}) em {sp_filename}:\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout


def pwl_2in_str(high_v):
    """Retorna sequencia PWL de 25ns percorrendo 00 -> 01 -> 10 -> 11 -> 00."""
    # janelas: [0,5) 00, [5,10) 01, [10,15) 10, [15,20) 11, [20,25] 00
    a_pts = [
        (0.0, 0.0), (9.9, 0.0), (10.0, high_v), (19.9, high_v), (20.0, 0.0), (25.0, 0.0)
    ]
    b_pts = [
        (0.0, 0.0), (4.9, 0.0), (5.0, high_v), (9.9, high_v),
        (10.0, 0.0), (14.9, 0.0), (15.0, high_v), (19.9, high_v),
        (20.0, 0.0), (25.0, 0.0)
    ]
    an_pts = [(t, high_v - v) for t, v in a_pts]
    bn_pts = [(t, high_v - v) for t, v in b_pts]

    def fmt(pts):
        return " ".join(f"{t:.2f}n {v:.4f}" for t, v in pts)

    return fmt(a_pts), fmt(b_pts), fmt(an_pts), fmt(bn_pts)


def pwl_3in_str(high_v):
    """Retorna sequencia PWL de 45ns percorrendo 000..111 -> 000 (9 janelas de 5ns)."""
    seq = [(i >> 2 & 1, i >> 1 & 1, i & 1) for i in range(8)] + [(0, 0, 0)]
    lines_a, lines_b, lines_c = [], [], []
    lines_an, lines_bn, lines_cn = [], [], []
    for idx, (a, b, c) in enumerate(seq):
        t0 = idx * 5.0
        t1 = (idx + 1) * 5.0 - 0.1
        if idx == len(seq) - 1:
            t1 = (idx + 1) * 5.0
        for val, arr, arrn in [
            (a * high_v, lines_a, lines_an),
            (b * high_v, lines_b, lines_bn),
            (c * high_v, lines_c, lines_cn),
        ]:
            arr.append(f"{t0:.2f}n {val:.4f} {t1:.2f}n {val:.4f}")
            arrn.append(f"{t0:.2f}n {high_v - val:.4f} {t1:.2f}n {high_v - val:.4f}")
    return (
        " ".join(lines_a),
        " ".join(lines_b),
        " ".join(lines_c),
        " ".join(lines_an),
        " ".join(lines_bn),
        " ".join(lines_cn),
    )


SHARED_SUBCKTS = """
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
"""


def build_and_run_2input_tuples():
    """Gera e executa tuplas_2entradas.sp em Key=0 e Key=1 sob Cload=0.3fF."""
    a08, b08, _, _ = pwl_2in_str(0.8)
    a11, b11, an11, bn11 = pwl_2in_str(1.1)

    net = f"""* Testbench Padronizado para Tuplas Polimorficas de 2 Entradas (Cload = 0.3 fF)
* Tuplas: (NAND, NOR), (XOR, XNOR), (AND, OR), (NAND, XNOR), (NOR, XOR)
.include "{LIB_REL}"
{SHARED_SUBCKTS}

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
Va08 a08 0 pwl({a08})
Vb08 b08 0 pwl({b08})
Va11  a11  0 pwl({a11})
Van11 an11 0 pwl({an11})
Vb11  b11  0 pwl({b11})
Vbn11 bn11 0 pwl({bn11})

Vss  vss  0 0.0
Vgp  gp   0 0.0
Vgn  gn   0 0.8
Vk   k    0 {{pk11}}
Vkn  kn   0 {{pkn11}}

* 1) Tupla (NAND, NOR) - 4T (VDD=0.8V)
Vrtop_nn rtop_nn 0 {{prtop08}}
Vgtop_nn gtop_nn 0 {{pgtop08}}
Vrbot_nn rbot_nn 0 {{prbot08}}
Vgbot_nn gbot_nn 0 {{pgbot08}}
X_NN a08 b08 out_nn rtop_nn gtop_nn rbot_nn gbot_nn POLY_NAND_NOR
Cout_nn out_nn 0 0.3f

* 2) Tupla (XOR, XNOR) - 4T nucleo (VDD=1.5V, Vin=1.1V)
Vrtop_xx rtop_xx 0 {{prtop15}}
Vgtop_xx gtop_xx 0 {{pgtop15}}
Vrbot_xx rbot_xx 0 {{prbot15}}
Vgbot_xx gbot_xx 0 {{pgbot15}}
X_XX a11 an11 b11 bn11 out_xx rtop_xx gtop_xx rbot_xx gbot_xx POLY_XOR
Cout_xx out_xx 0 0.3f

* 3) Tupla (AND, OR) - 6T = POLY_NAND_NOR(4T) + BP_INV08(2T) (VDD=0.8V)
Vrtop_ao rtop_ao 0 {{prtop08}}
Vgtop_ao gtop_ao 0 {{pgtop08}}
Vrbot_ao rbot_ao 0 {{prbot08}}
Vgbot_ao gbot_ao 0 {{pgbot08}}
Vdd_ao   vdd_ao  0 0.8
X_AO_PRE a08 b08 n_ao rtop_ao gtop_ao rbot_ao gbot_ao POLY_NAND_NOR
X_AO_INV n_ao out_ao vdd_ao vss BP_INV08
Cn_ao   n_ao   0 0.1f
Cout_ao out_ao 0 0.2f

* 4) Tupla (NAND, XNOR) - 6T nucleo (VDD=1.5V, Vin=1.1V)
Vrtop_nx rtop_nx 0 {{prtop15}}
Vgtop_nx gtop_nx 0 {{pgtop15}}
Vrbot_nx rbot_nx 0 {{prbot15}}
Vgbot_nx gbot_nx 0 {{pgbot15}}
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
Vrtop_rx rtop_rx 0 {{prtop15}}
Vgtop_rx gtop_rx 0 {{pgtop15}}
Vrbot_rx rbot_rx 0 {{prbot15}}
Vgbot_rx gbot_rx 0 {{pgbot15}}
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
"""
    with open(os.path.join(BASE_DIR, "tuplas_2entradas.sp"), "w", encoding="utf-8") as f:
        f.write(net)
    run_ngspice("tuplas_2entradas.sp")


def build_and_run_3input_tuples():
    """Gera e executa tuplas_3entradas.sp para (AOI21, OAI21) e (MAJ3, XOR3)."""
    a08, b08, c08, _, _, _ = pwl_3in_str(0.8)
    a11, b11, c11, an11, bn11, cn11 = pwl_3in_str(1.1)

    net = f"""* Testbench Padronizado para Tuplas Polimorficas de 3 Entradas (Cload = 0.3 fF)
* Tuplas: (AOI21, OAI21) 6T e (MAJ3, XOR3) 10T estagio / 18T c/ gerador P=A^B
.include "{LIB_REL}"
{SHARED_SUBCKTS}

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
Va08 a08 0 pwl({a08})
Vb08 b08 0 pwl({b08})
Vc08 c08 0 pwl({c08})

Va11  a11  0 pwl({a11})
Van11 an11 0 pwl({an11})
Vb11  b11  0 pwl({b11})
Vbn11 bn11 0 pwl({bn11})
Vc11  c11  0 pwl({c11})
Vcn11 cn11 0 pwl({cn11})

Vss  vss  0 0.0
Vgp  gp   0 0.0
Vgn  gn   0 0.8

* 6) Tupla (AOI21, OAI21) - 6T (VDD=0.8V)
Vrtop_aoi rtop_aoi 0 {{prtop_aoi}}
Vgtop_aoi gtop_aoi 0 {{pgtop_aoi}}
Vrbot_aoi rbot_aoi 0 {{prbot_aoi}}
Vgbot_aoi gbot_aoi 0 {{pgbot_aoi}}

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
Vk_mx     k_mx      0 {{pk_mx}}
Vkn_mx    kn_mx     0 {{pkn_mx}}
Vrtop_mx  rtop_mx   0 {{prtop_mx}}
Vgtop_mx  gtop_mx   0 {{pgtop_mx}}
Vrbot_mx  rbot_mx   0 {{prbot_mx}}
Vgbot_mx  gbot_mx   0 {{pgbot_mx}}

XX_PRE a11 an11 b11 bn11 p_raw vdd15_pre gp vss gn POLY_XOR
Cp_raw p_raw 0 0.2f
XI_P1  p_raw pn08 vdd08_pre vss BP_INV08
XI_P2  pn08  p08  vdd08_pre vss BP_INV08
XI_P3  p08   pn11 vdd11_pre vss BP_INV11
XI_P4  pn08  p11  vdd11_pre vss BP_INV11

* Nucleo polimorfico 10T quad-simetrico (Key=0 -> MAJ3, Key=1 -> XOR3)
XM2  out_mx p11  rtop_mx  cn11 mgtop_dummy ARI W=1.0
* Nota: conectando g2 ao sinal de polaridade correta
.ends_dummy_placeholder
"""
    # Substituir placeholder e montar corretamente sem linhas invalidas
    net = net.replace(
        "XM2  out_mx p11  rtop_mx  cn11 mgtop_dummy ARI W=1.0\n* Nota: conectando g2 ao sinal de polaridade correta\n.ends_dummy_placeholder",
        """XM2  out_mx p11  rtop_mx  cn11  gtop_mx ARI W=1.0
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
""",
    )
    with open(os.path.join(BASE_DIR, "tuplas_3entradas.sp"), "w", encoding="utf-8") as f:
        f.write(net)
    run_ngspice("tuplas_3entradas.sp")


def build_corner_pwl(corners_list, vecs, step_ns, edge_ns=0.08):
    """Monta strings PWL percorrendo todos os cantos (dVDD, dVSS) e vetores de entrada."""
    keys = [
        "v08", "v15", "v11", "vss", "gt08", "gb08", "gta",
        "a08", "b08", "c08", "a11", "b11", "c11", "an11", "bn11", "cn11",
    ]
    pts = {k: [] for k in keys}
    idx = 0
    for d, s in corners_list:
        v08 = 0.8 * (1.0 + d)
        v15 = 1.5 * (1.0 + d)
        v11 = 1.1 * (1.0 + d)
        for a, b, c in vecs:
            t0 = idx * step_ns
            t1 = (idx + 1) * step_ns - edge_ns
            vals = {
                "v08": v08, "v15": v15, "v11": v11, "vss": s,
                "gt08": s - 0.4, "gb08": s - 0.7, "gta": s - 0.5,
                "a08": v08 if a else s, "b08": v08 if b else s, "c08": v08 if c else s,
                "a11": v11 if a else s, "b11": v11 if b else s, "c11": v11 if c else s,
                "an11": s if a else v11, "bn11": s if b else v11, "cn11": s if c else v11,
            }
            for k, val in vals.items():
                pts[k].append(f"+ {t0:.2f}n {val:.5f} {t1:.2f}n {val:.5f}")
            idx += 1
    t_end = idx * step_ns
    for k in keys:
        last_val = pts[k][-1].split()[-1]
        pts[k].append(f"+ {t_end:.2f}n {last_val}")
    return {k: "\n".join(v) for k, v in pts.items()}, t_end


def build_and_run_robustness_sweep():
    """Varredura 3x3 de ruido nos trilhos (dVDD in {-10%,0,+10%}, dVSS in {-50,0,+50}mV) no ngspice."""
    dvdd_rel_grid = [-0.10, 0.0, 0.10]
    dvss_grid = [-0.05, 0.0, 0.05]
    corners = [(d, s) for d in dvdd_rel_grid for s in dvss_grid]

    vecs_2in = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0)]
    vecs_3in = [(i >> 2 & 1, i >> 1 & 1, i & 1) for i in range(8)]

    # Ambos os blocos terminam exatamente em 252.0 ns (2-in: 36 janelas x 7ns; 3-in: 72 janelas x 3.5ns)
    pwl2, tend2 = build_corner_pwl(corners, vecs_2in, step_ns=7.0)
    pwl3, tend3 = build_corner_pwl(corners, vecs_3in, step_ns=3.5)
    assert abs(tend2 - tend3) < 1e-6

    net = f"""* Varredura Parametrica 3x3 de Ruido de Fonte (dVDD x dVSS) nas 7 Tuplas Polimorficas
.include "{LIB_REL}"
{SHARED_SUBCKTS}
.param mode_k = 0

* --- Alimentacoes e Entradas Bloco 2-Entradas (step = 7.0 ns/vetor, total = 252 ns) ---
Vdd08_2 vdd08_2 0 pwl(
{pwl2['v08']})
Vdd15_2 vdd15_2 0 pwl(
{pwl2['v15']})
Vdd11_2 vdd11_2 0 pwl(
{pwl2['v11']})
Vss_2   vss_2   0 pwl(
{pwl2['vss']})
Vgt08_2 gt08_k0_2 0 pwl(
{pwl2['gt08']})
Vgb08_2 gb08_k1_2 0 pwl(
{pwl2['gb08']})
Va08_2  a08_2   0 pwl(
{pwl2['a08']})
Vb08_2  b08_2   0 pwl(
{pwl2['b08']})
Va11_2  a11_2   0 pwl(
{pwl2['a11']})
Van11_2 an11_2  0 pwl(
{pwl2['an11']})
Vb11_2  b11_2   0 pwl(
{pwl2['b11']})
Vbn11_2 bn11_2  0 pwl(
{pwl2['bn11']})

B_rt08_2 rtop08_2 0 V = (mode_k < 0.5) ? v(vdd08_2) : v(vss_2)
B_gt08_2 gtop08_2 0 V = (mode_k < 0.5) ? v(gt08_k0_2) : v(vdd08_2)
B_rb08_2 rbot08_2 0 V = (mode_k < 0.5) ? v(vss_2)   : v(vdd08_2)
B_gb08_2 gbot08_2 0 V = (mode_k < 0.5) ? v(vdd08_2) : v(gb08_k1_2)
B_rt15_2 rtop15_2 0 V = (mode_k < 0.5) ? v(vdd15_2) : v(vss_2)
B_gt15_2 gtop15_2 0 V = (mode_k < 0.5) ? v(vss_2)   : 0.8
B_rb15_2 rbot15_2 0 V = (mode_k < 0.5) ? v(vss_2)   : v(vdd15_2)
B_gb15_2 gbot15_2 0 V = (mode_k < 0.5) ? 0.8        : v(vss_2)
B_k_2    k_2      0 V = (mode_k < 0.5) ? v(vss_2)   : v(vdd11_2)
B_kn_2   kn_2     0 V = (mode_k < 0.5) ? v(vdd11_2) : v(vss_2)

Vgn gn 0 0.8

* 1) (NAND, NOR)
X_NN a08_2 b08_2 out_nn rtop08_2 gtop08_2 rbot08_2 gbot08_2 POLY_NAND_NOR
Cout_nn out_nn 0 0.3f

* 2) (XOR, XNOR)
X_XX a11_2 an11_2 b11_2 bn11_2 out_xx rtop15_2 gtop15_2 rbot15_2 gbot15_2 POLY_XOR
Cout_xx out_xx 0 0.3f

* 3) (AND, OR)
X_AO_PRE a08_2 b08_2 n_ao rtop08_2 gtop08_2 rbot08_2 gbot08_2 POLY_NAND_NOR
X_AO_INV n_ao out_ao vdd08_2 vss_2 BP_INV08
Cn_ao   n_ao   0 0.1f
Cout_ao out_ao 0 0.2f

* 4) (NAND, XNOR)
XNX1 out_nx an11_2  rtop15_2 b11_2   gtop15_2 ARI W=1.0
XNX2 out_nx a11_2   rtop15_2 bn11_2  gtop15_2 ARI W=1.0
XNX3 out_nx a11_2   vdd15_2  b11_2   vss_2    ARI W=1.0
XNX4 out_nx a11_2   rbot15_2 b11_2   gbot15_2 ARI W=1.0
XNX5 out_nx an11_2  n11p_nx  bn11_2  vss_2    ARI W=2.0
XNX6 n11p_nx kn_2   vdd15_2  kn_2    vss_2    ARI W=2.0
Cn11p_nx n11p_nx 0 0.05f
Cout_nx  out_nx  0 0.3f

* 5) (NOR, XOR)
XRX1 out_rx an11_2  rbot15_2 b11_2   gbot15_2 ARI W=1.0
XRX2 out_rx a11_2   rbot15_2 bn11_2  gbot15_2 ARI W=1.0
XRX3 out_rx a11_2   vss_2    b11_2   gn       ARI W=1.0
XRX4 out_rx a11_2   rtop15_2 b11_2   gtop15_2 ARI W=1.0
XRX5 out_rx an11_2  n00n_rx  bn11_2  gn       ARI W=2.0
XRX6 n00n_rx k_2    vss_2    k_2     gn       ARI W=2.0
Cn00n_rx n00n_rx 0 0.05f
Cout_rx  out_rx  0 0.3f

* --- Alimentacoes e Entradas Bloco 3-Entradas (step = 3.5 ns/vetor, total = 252 ns) ---
Vdd08_3 vdd08_3 0 pwl(
{pwl3['v08']})
Vdd15_3 vdd15_3 0 pwl(
{pwl3['v15']})
Vdd11_3 vdd11_3 0 pwl(
{pwl3['v11']})
Vss_3   vss_3   0 pwl(
{pwl3['vss']})
Vgta_3  gta_k0_3  0 pwl(
{pwl3['gta']})
Vgb08_3 gb08_k1_3 0 pwl(
{pwl3['gb08']})
Va08_3  a08_3   0 pwl(
{pwl3['a08']})
Vb08_3  b08_3   0 pwl(
{pwl3['b08']})
Vc08_3  c08_3   0 pwl(
{pwl3['c08']})
Va11_3  a11_3   0 pwl(
{pwl3['a11']})
Van11_3 an11_3  0 pwl(
{pwl3['an11']})
Vb11_3  b11_3   0 pwl(
{pwl3['b11']})
Vbn11_3 bn11_3  0 pwl(
{pwl3['bn11']})
Vc11_3  c11_3   0 pwl(
{pwl3['c11']})
Vcn11_3 cn11_3  0 pwl(
{pwl3['cn11']})

B_rt08_3 rtop08_3 0 V = (mode_k < 0.5) ? v(vdd08_3) : v(vss_3)
B_gta_3  gtop_a_3 0 V = (mode_k < 0.5) ? v(gta_k0_3) : v(vdd08_3)
B_rb08_3 rbot08_3 0 V = (mode_k < 0.5) ? v(vss_3)   : v(vdd08_3)
B_gba_3  gbot_a_3 0 V = (mode_k < 0.5) ? v(vdd08_3) : v(gb08_k1_3)

B_rt15_3 rtop15_3 0 V = (mode_k < 0.5) ? v(vss_3)   : v(vdd15_3)
B_gt15_3 gtop15_3 0 V = (mode_k < 0.5) ? 0.8        : v(vss_3)
B_rb15_3 rbot15_3 0 V = (mode_k < 0.5) ? v(vdd15_3) : v(vss_3)
B_gb15_3 gbot15_3 0 V = (mode_k < 0.5) ? v(vss_3)   : 0.8
B_k_3    k_3      0 V = (mode_k < 0.5) ? v(vss_3)   : v(vdd11_3)
B_kn_3   kn_3     0 V = (mode_k < 0.5) ? v(vdd11_3) : v(vss_3)

* 6) (AOI21, OAI21)
XAOI1 ntop_aoi a08_3 rtop08_3 gtop_a_3 gtop_a_3 ARI W=1.5
XAOI2 ntop_aoi b08_3 rtop08_3 gtop_a_3 gtop_a_3 ARI W=1.5
XAOI3 out_aoi  c08_3 ntop_aoi gtop_a_3 gtop_a_3 ARI W=2.5
XAOI4 out_aoi  b08_3 nbot_aoi gbot_a_3 gbot_a_3 ARI W=2.5
XAOI5 nbot_aoi a08_3 rbot08_3 gbot_a_3 gbot_a_3 ARI W=2.5
XAOI6 out_aoi  c08_3 rbot08_3 gbot_a_3 gbot_a_3 ARI W=1.5
Cnt_aoi  ntop_aoi 0 0.05f
Cnb_aoi  nbot_aoi 0 0.05f
Cout_aoi out_aoi  0 0.3f

* 7) (MAJ3, XOR3)
XX_PRE a11_3 an11_3 b11_3 bn11_3 p_raw vdd15_3 vss_3 vss_3 gn POLY_XOR
Cp_raw p_raw 0 0.2f
XI_P1  p_raw pn08 vdd08_3 vss_3 BP_INV08
XI_P2  pn08  p08  vdd08_3 vss_3 BP_INV08
XI_P3  p08   pn11 vdd11_3 vss_3 BP_INV11
XI_P4  pn08  p11  vdd11_3 vss_3 BP_INV11

XM2  out_mx p11  rtop15_3 cn11_3 gtop15_3 ARI W=1.0
XM4  out_mx pn11 rbot15_3 cn11_3 gbot15_3 ARI W=1.0
XM1a out_mx pn11 n1a_mx   an11_3 gn       ARI W=2.0
XM1b n1a_mx kn_3 vss_3    kn_3   gn       ARI W=2.0
XM1c out_mx pn11 n1c_mx   c11_3  vss_3    ARI W=2.0
XM1d n1c_mx kn_3 vdd15_3  kn_3   vss_3    ARI W=2.0
XM3a out_mx p11  n3a_mx   an11_3 vss_3    ARI W=2.0
XM3b n3a_mx k_3  vdd15_3  k_3    vss_3    ARI W=2.0
XM3c out_mx p11  n3c_mx   c11_3  gn       ARI W=2.0
XM3d n3c_mx k_3  vss_3    k_3    gn       ARI W=2.0
Cn1a_mx n1a_mx 0 0.05f
Cn1c_mx n1c_mx 0 0.05f
Cn3a_mx n3a_mx 0 0.05f
Cn3c_mx n3c_mx 0 0.05f
Cout_mx out_mx 0 0.3f

.control
set wr_vecnames
set wr_singlescale

tran 50p {tend3:.1f}n
wrdata rob_k0.dat v(out_nn) v(out_xx) v(out_ao) v(out_nx) v(out_rx) v(out_aoi) v(out_mx)

alterparam mode_k = 1
reset
tran 50p {tend3:.1f}n
wrdata rob_k1.dat v(out_nn) v(out_xx) v(out_ao) v(out_nx) v(out_rx) v(out_aoi) v(out_mx)
.endc
.end
"""
    with open(os.path.join(BASE_DIR, "sim_robustez_tuplas.sp"), "w", encoding="utf-8") as f:
        f.write(net)
    run_ngspice("sim_robustez_tuplas.sp")

    return dvdd_rel_grid, dvss_grid


def build_and_run_full_adder_profiles():
    """Gera e simula full_adder_perfis_dpa.sp para os 3 Perfis de Full Adder."""
    a11, b11, c11, an11, bn11, cn11 = pwl_3in_str(1.1)
    a08, b08, c08, _, _, _ = pwl_3in_str(0.8)
    # Usar apenas os primeiros 40 ns (8 mintermos 000..111)
    def trim40(pwl_s):
        toks = pwl_s.split()
        # 18 pares (9 janelas x 2 pontos = 36 tokens) -> pegar 8 janelas (32 tokens) e ajustar ultimo t para 40n
        toks = toks[:32]
        toks[-2] = "40.00n"
        return " ".join(toks)

    a11, b11, c11 = trim40(a11), trim40(b11), trim40(c11)
    an11, bn11, cn11 = trim40(an11), trim40(bn11), trim40(cn11)
    a08, b08, c08 = trim40(a08), trim40(b08), trim40(c08)

    net = f"""* Benchmark em Sistema: Full Adder 1-bit em 3 Perfis Arquiteturais BP SB-FET
* Perfil 1: Baseline Comum (20T nucleo, sem logic locking, sem protecao DPA)
* Perfil 2: Focado em Custo/Desempenho (28T nucleo, Cout em 3x NAND/NOR + Sum em XOR/XNOR)
* Perfil 3: Focado em Baixa Assimetria DPA (26T nucleo, Sum em XOR/XNOR + Cout em MAJ3/XOR3 10T)
.include "{LIB_REL}"
{SHARED_SUBCKTS}

Va11  a11  0 pwl({a11})
Van11 an11 0 pwl({an11})
Vb11  b11  0 pwl({b11})
Vbn11 bn11 0 pwl({bn11})
Vc11  c11  0 pwl({c11})
Vcn11 cn11 0 pwl({cn11})

Va08  a08  0 pwl({a08})
Vb08  b08  0 pwl({b08})
Vc08  c08  0 pwl({c08})

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
Vxrtop_p2 xrtop_p2 0 {{p2_xrtop}}
Vxgtop_p2 xgtop_p2 0 {{p2_xgtop}}
Vxrbot_p2 xrbot_p2 0 {{p2_xrbot}}
Vxgbot_p2 xgbot_p2 0 {{p2_xgbot}}
Vnrtop_p2 nrtop_p2 0 {{p2_nrtop}}
Vngtop_p2 ngtop_p2 0 {{p2_ngtop}}
Vnrbot_p2 nrbot_p2 0 {{p2_nrbot}}
Vngbot_p2 ngbot_p2 0 {{p2_ngbot}}

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
Vk_p3     k_p3     0 {{p3_k}}
Vkn_p3    kn_p3    0 {{p3_kn}}
Vxrtop_p3 xrtop_p3 0 {{p3_xrtop}}
Vxgtop_p3 xgtop_p3 0 {{p3_xgtop}}
Vxrbot_p3 xrbot_p3 0 {{p3_xrbot}}
Vxgbot_p3 xgbot_p3 0 {{p3_xgbot}}
Vmrtop_p3 mrtop_p3 0 {{p3_mrtop}}
Vmgtop_p3 mgtop_p3 0 {{p3_mgtop}}
Vmrbot_p3 mrbot_p3 0 {{p3_mrbot}}
Vmgbot_p3 mgbot_p3 0 {{p3_mgbot}}

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
"""
    with open(os.path.join(BASE_DIR, "full_adder_perfis_dpa.sp"), "w", encoding="utf-8") as f:
        f.write(net)
    run_ngspice("full_adder_perfis_dpa.sp")


# ---------------------------------------------------------------------------
# Metricas auxiliares e processamento
# ---------------------------------------------------------------------------

def asym_pct(v0, v1):
    """Assimetria relativa padronizada (modulo 03): |v0 - v1| / min(v0, v1) * 100%."""
    denom = min(abs(v0), abs(v1))
    if denom < 1e-15:
        return 0.0
    return float(abs(v0 - v1) / denom * 100.0)


def time_avg(t_s, y):
    """Media temporal exata via regra trapezoidal."""
    return float(np.trapezoid(y, t_s) / (t_s[-1] - t_s[0]))


def compute_delays_and_transitions(t_ns, v_in_ref, v_out, vdd, vin_high, exp_bits, step_ns=5.0):
    """Extrai atrasos tpLH (0->1) e tpHL (1->0) e janelas de transicao."""
    tp_lh_list, tp_hl_list = [], []
    trans_0to1_windows, trans_1to0_windows = [], []

    vth_out = 0.5 * vdd

    for idx in range(len(exp_bits) - 1):
        b_prev, b_curr = exp_bits[idx], exp_bits[idx + 1]
        if b_prev == b_curr:
            continue
        t_edge = (idx + 1) * step_ns
        t_in_cross = t_edge - 0.05
        win_mask = (t_ns >= t_in_cross) & (t_ns <= t_edge + 3.5)
        t_w = t_ns[win_mask]
        vout_w = v_out[win_mask]

        if b_prev == 0 and b_curr == 1:
            cross_idx = np.where(vout_w >= vth_out)[0]
            if len(cross_idx) > 0:
                k = cross_idx[0]
                if k > 0:
                    t_c = np.interp(vth_out, [vout_w[k - 1], vout_w[k]], [t_w[k - 1], t_w[k]])
                else:
                    t_c = t_w[k]
                tp_lh_list.append(max((t_c - t_in_cross) * 1e3, 1.0))
            trans_0to1_windows.append((t_edge - 0.15, t_edge + 2.0))
        elif b_prev == 1 and b_curr == 0:
            cross_idx = np.where(vout_w <= vth_out)[0]
            if len(cross_idx) > 0:
                k = cross_idx[0]
                if k > 0:
                    t_c = np.interp(vth_out, [vout_w[k], vout_w[k - 1]], [t_w[k], t_w[k - 1]])
                else:
                    t_c = t_w[k]
                tp_hl_list.append(max((t_c - t_in_cross) * 1e3, 1.0))
            trans_1to0_windows.append((t_edge - 0.15, t_edge + 2.0))

    return tp_lh_list, tp_hl_list, trans_0to1_windows, trans_1to0_windows


def extract_transition_peaks(t_ns, i_vdd_abs, windows):
    """Retorna pico maximo de corrente dentro das janelas de transicao."""
    if not windows:
        return 0.0
    peaks = []
    for t0, t1 in windows:
        m = (t_ns >= t0) & (t_ns <= t1)
        if np.any(m):
            peaks.append(float(np.max(i_vdd_abs[m])))
    return float(np.max(peaks)) if peaks else 0.0


def extract_static_current(t_ns, i_vdd_abs, n_windows, step_ns=5.0):
    """Media da corrente estatica no fim de cada janela estacionaria."""
    vals = []
    for idx in range(n_windows):
        t0 = idx * step_ns + 4.2
        t1 = idx * step_ns + 4.8
        m = (t_ns >= t0) & (t_ns <= t1)
        if np.any(m):
            vals.append(float(np.mean(i_vdd_abs[m])))
    return float(np.mean(vals))


def bilinear_interp_2d(x_grid, y_grid, z_grid, x_pts, y_pts):
    """Interpolacao bilinear vetorial 2D em grade regular usando numpy puro."""
    xg = np.asarray(x_grid, dtype=float)
    yg = np.asarray(y_grid, dtype=float)
    xp = np.clip(np.asarray(x_pts, dtype=float), xg[0], xg[-1])
    yp = np.clip(np.asarray(y_pts, dtype=float), yg[0], yg[-1])

    ix = np.clip(np.searchsorted(xg, xp, side="right") - 1, 0, len(xg) - 2)
    iy = np.clip(np.searchsorted(yg, yp, side="right") - 1, 0, len(yg) - 2)

    tx = (xp - xg[ix]) / (xg[ix + 1] - xg[ix])
    ty = (yp - yg[iy]) / (yg[iy + 1] - yg[iy])

    z00 = z_grid[ix, iy]
    z10 = z_grid[ix + 1, iy]
    z01 = z_grid[ix, iy + 1]
    z11 = z_grid[ix + 1, iy + 1]
    return (1 - tx) * (1 - ty) * z00 + tx * (1 - ty) * z10 + (1 - tx) * ty * z01 + tx * ty * z11


def evaluate_monte_carlo_from_grid(tuple_key, expected_k0, expected_k1, vdd_nom, dvdd_rel_grid, dvss_grid, col_index_rob):
    """Avalia N=250 amostras Monte Carlo sobre a grade 3x3 real do ngspice para uma tupla."""
    n_vecs = len(expected_k0)
    step_ns = 7.0 if n_vecs == 4 else 3.5

    d_rob0 = np.loadtxt(os.path.join(BASE_DIR, "rob_k0.dat"), skiprows=1)
    d_rob1 = np.loadtxt(os.path.join(BASE_DIR, "rob_k1.dat"), skiprows=1)
    t0_ns = d_rob0[:, 0] * 1e9
    t1_ns = d_rob1[:, 0] * 1e9

    grid_vals_k0 = np.zeros((len(dvdd_rel_grid), len(dvss_grid), n_vecs))
    grid_vals_k1 = np.zeros((len(dvdd_rel_grid), len(dvss_grid), n_vecs))

    c_idx = 0
    for i_d in range(len(dvdd_rel_grid)):
        for i_s in range(len(dvss_grid)):
            for v_idx in range(n_vecs):
                win_idx = c_idx * n_vecs + v_idx
                t_a = win_idx * step_ns + step_ns * 0.72
                t_b = win_idx * step_ns + step_ns * 0.94
                m0 = (t0_ns >= t_a) & (t0_ns <= t_b)
                m1 = (t1_ns >= t_a) & (t1_ns <= t_b)
                grid_vals_k0[i_d, i_s, v_idx] = float(np.mean(d_rob0[m0, col_index_rob]))
                grid_vals_k1[i_d, i_s, v_idx] = float(np.mean(d_rob1[m1, col_index_rob]))
            c_idx += 1

    rng = np.random.default_rng(42)
    n_mc = 250
    samples_dvdd = np.clip(rng.normal(0.0, 0.035, size=n_mc), -0.10, 0.10)
    samples_dvss = np.clip(rng.normal(0.0, 0.018, size=n_mc), -0.05, 0.05)

    high_vals, low_vals = [], []
    correct_cnt = 0
    total_cnt = 0

    for exp_bits, grid_vals in [(expected_k0, grid_vals_k0), (expected_k1, grid_vals_k1)]:
        for v_idx, exp_b in enumerate(exp_bits):
            v_outs = bilinear_interp_2d(dvdd_rel_grid, dvss_grid, grid_vals[:, :, v_idx], samples_dvdd, samples_dvss)
            # Limiar dinamico considerando deslocamento de trilho
            v_th = 0.5 * (vdd_nom * (1.0 + samples_dvdd) + samples_dvss)
            total_cnt += n_mc
            if exp_b == 1:
                high_vals.extend(v_outs.tolist())
                correct_cnt += int(np.sum(v_outs > v_th))
            else:
                low_vals.extend(v_outs.tolist())
                correct_cnt += int(np.sum(v_outs < v_th))

    return {
        "MC_Amostras": n_mc,
        "MC_Taxa_Acerto_pct": float(correct_cnt / total_cnt * 100.0),
        "MC_Nivel1_Medio_V": float(np.mean(high_vals)),
        "MC_Std_Nivel1_mV": float(np.std(high_vals) * 1e3),
        "MC_Nivel0_Medio_V": float(np.mean(low_vals)),
        "MC_Std_Nivel0_mV": float(np.std(low_vals) * 1e3),
        "high_vals": np.array(high_vals),
        "low_vals": np.array(low_vals),
    }


def analyze_tuples(dvdd_rel_grid, dvss_grid):
    """Analisa todas as 7 tuplas polimorficas e gera CSVs e graficos."""
    d2_k0 = np.loadtxt(os.path.join(BASE_DIR, "t2_k0.dat"), skiprows=1)
    d2_k1 = np.loadtxt(os.path.join(BASE_DIR, "t2_k1.dat"), skiprows=1)
    d3_k0 = np.loadtxt(os.path.join(BASE_DIR, "t3_k0.dat"), skiprows=1)
    d3_k1 = np.loadtxt(os.path.join(BASE_DIR, "t3_k1.dat"), skiprows=1)

    # Especificacao das 7 tuplas
    # col_v0, col_v1 e lambdas para corrente de VDD em K=0 e K=1
    tuple_specs = [
        {
            "Tupla": "(NAND, NOR)",
            "Categoria": "Universal Compacta",
            "Entradas": 2,
            "N_Transistores_Nucleo": 4,
            "N_Transistores_Total": 4,
            "Largura_Total_W_um": 6.0,
            "VDD_V": 0.8,
            "Vin_V": 0.8,
            "Modos": ("NAND", "NOR"),
            "Exp_K0": [1, 1, 1, 0, 1],
            "Exp_K1": [1, 0, 0, 0, 1],
            "Data": (d2_k0, d2_k1),
            "V_col": 5,
            "I0_fn": lambda d: np.abs(-d[:, 6]),
            "I1_fn": lambda d: np.abs(-d[:, 7]),
            "Rob_offset": 1,
        },
        {
            "Tupla": "(XOR, XNOR)",
            "Categoria": "Simetrica Segura",
            "Entradas": 2,
            "N_Transistores_Nucleo": 4,
            "N_Transistores_Total": 8,
            "Largura_Total_W_um": 4.0,
            "VDD_V": 1.5,
            "Vin_V": 1.1,
            "Modos": ("XOR", "XNOR"),
            "Exp_K0": [0, 1, 1, 0, 0],
            "Exp_K1": [1, 0, 0, 1, 1],
            "Data": (d2_k0, d2_k1),
            "V_col": 8,
            "I0_fn": lambda d: np.abs(-d[:, 9]),
            "I1_fn": lambda d: np.abs(-d[:, 10]),
            "Rob_offset": 2,
        },
        {
            "Tupla": "(AND, OR)",
            "Categoria": "Logica de Controle",
            "Entradas": 2,
            "N_Transistores_Nucleo": 6,
            "N_Transistores_Total": 6,
            "Largura_Total_W_um": 9.0,
            "VDD_V": 0.8,
            "Vin_V": 0.8,
            "Modos": ("AND", "OR"),
            "Exp_K0": [0, 0, 0, 1, 0],
            "Exp_K1": [0, 1, 1, 1, 0],
            "Data": (d2_k0, d2_k1),
            "V_col": 11,
            "I0_fn": lambda d: np.abs(-d[:, 12]) + np.abs(-d[:, 14]),
            "I1_fn": lambda d: np.abs(-d[:, 13]) + np.abs(-d[:, 14]),
            "Rob_offset": 3,
        },
        {
            "Tupla": "(NAND, XNOR)",
            "Categoria": "Logic Locking Misto",
            "Entradas": 2,
            "N_Transistores_Nucleo": 6,
            "N_Transistores_Total": 10,
            "Largura_Total_W_um": 8.0,
            "VDD_V": 1.5,
            "Vin_V": 1.1,
            "Modos": ("NAND", "XNOR"),
            "Exp_K0": [1, 1, 1, 0, 1],
            "Exp_K1": [1, 0, 0, 1, 1],
            "Data": (d2_k0, d2_k1),
            "V_col": 15,
            "I0_fn": lambda d: np.abs(-d[:, 16]) + np.abs(-d[:, 18]),
            "I1_fn": lambda d: np.abs(-d[:, 17]) + np.abs(-d[:, 18]),
            "Rob_offset": 4,
        },
        {
            "Tupla": "(NOR, XOR)",
            "Categoria": "Logic Locking Misto",
            "Entradas": 2,
            "N_Transistores_Nucleo": 6,
            "N_Transistores_Total": 10,
            "Largura_Total_W_um": 8.0,
            "VDD_V": 1.5,
            "Vin_V": 1.1,
            "Modos": ("NOR", "XOR"),
            "Exp_K0": [1, 0, 0, 0, 1],
            "Exp_K1": [0, 1, 1, 0, 0],
            "Data": (d2_k0, d2_k1),
            "V_col": 19,
            "I0_fn": lambda d: np.abs(-d[:, 20]),
            "I1_fn": lambda d: np.abs(-d[:, 21]),
            "Rob_offset": 5,
        },
        {
            "Tupla": "(AOI21, OAI21)",
            "Categoria": "Composta ASIC",
            "Entradas": 3,
            "N_Transistores_Nucleo": 6,
            "N_Transistores_Total": 6,
            "Largura_Total_W_um": 12.0,
            "VDD_V": 0.8,
            "Vin_V": 0.8,
            "Modos": ("AOI21", "OAI21"),
            "Exp_K0": [1, 0, 1, 0, 1, 0, 0, 0, 1],
            "Exp_K1": [1, 1, 1, 0, 1, 0, 1, 0, 1],
            "Data": (d3_k0, d3_k1),
            "V_col": 7,
            "I0_fn": lambda d: np.abs(-d[:, 8]),
            "I1_fn": lambda d: np.abs(-d[:, 9]),
            "Rob_offset": 6,
        },
        {
            "Tupla": "(MAJ3, XOR3)",
            "Categoria": "Aritmetica Simetrica",
            "Entradas": 3,
            "N_Transistores_Nucleo": 10,
            "N_Transistores_Total": 18,
            "Largura_Total_W_um": 18.0,
            "VDD_V": 1.5,
            "Vin_V": 1.1,
            "Modos": ("MAJ3", "XOR3"),
            "Exp_K0": [0, 0, 0, 1, 0, 1, 1, 1, 0],
            "Exp_K1": [0, 1, 1, 0, 1, 0, 0, 1, 0],
            "Data": (d3_k0, d3_k1),
            "V_col": 10,
            # Corrente do estagio polimorfico de saida MAJ3/XOR3 (10T): rbot/rtop + vdd15_mx
            "I0_fn": lambda d: np.abs(-d[:, 12]) + np.abs(-d[:, 13]),
            "I1_fn": lambda d: np.abs(-d[:, 11]) + np.abs(-d[:, 13]),
            "Rob_offset": 7,
        },
    ]

    tt_rows = []
    metric_rows = []
    mc_distributions = {}
    waveform_traces = {}

    for spec in tuple_specs:
        d0, d1 = spec["Data"]
        t0_ns = d0[:, 0] * 1e9
        t1_ns = d1[:, 0] * 1e9
        t0_s = d0[:, 0]
        t1_s = d1[:, 0]

        v0 = d0[:, spec["V_col"]]
        v1 = d1[:, spec["V_col"]]
        i0 = spec["I0_fn"](d0)
        i1 = spec["I1_fn"](d1)

        n_comb = 2 ** spec["Entradas"]
        vth = 0.5 * spec["VDD_V"]

        # Verificar tabela-verdade
        v1_list, v0_list = [], []
        correct_total = 0
        for mode_idx, (mode_name, t_ns, v_sig, exp_seq) in enumerate([
            (spec["Modos"][0], t0_ns, v0, spec["Exp_K0"]),
            (spec["Modos"][1], t1_ns, v1, spec["Exp_K1"]),
        ]):
            for vec_idx in range(n_comb):
                t_a = vec_idx * 5.0 + 4.2
                t_b = vec_idx * 5.0 + 4.8
                m = (t_ns >= t_a) & (t_ns <= t_b)
                v_est = float(np.mean(v_sig[m]))
                bit_m = 1 if v_est > vth else 0
                bit_e = exp_seq[vec_idx]
                ok = (bit_m == bit_e)
                correct_total += int(ok)
                if bit_e == 1:
                    v1_list.append(v_est)
                else:
                    v0_list.append(v_est)
                bits_str = format(vec_idx, f"0{spec['Entradas']}b")
                tt_rows.append({
                    "Tupla": spec["Tupla"],
                    "Chave": f"Key={mode_idx}",
                    "Funcao": mode_name,
                    "Entradas": bits_str,
                    "Vout_V": round(v_est, 4),
                    "Bit_Medido": bit_m,
                    "Bit_Esperado": bit_e,
                    "Correto": ok,
                })

        # Metricas DPA (pico, medio, e por transicao 0->1 / 1->0)
        i_pico0_ua = float(np.max(i0) * 1e6)
        i_pico1_ua = float(np.max(i1) * 1e6)
        i_med0_ua = time_avg(t0_s, i0) * 1e6
        i_med1_ua = time_avg(t1_s, i1) * 1e6

        dpa_pico_pct = asym_pct(i_pico0_ua, i_pico1_ua)
        dpa_med_pct = asym_pct(i_med0_ua, i_med1_ua)

        # Atrasos e transicoes 0->1 / 1->0
        tp_lh0, tp_hl0, w01_0, w10_0 = compute_delays_and_transitions(
            t0_ns, None, v0, spec["VDD_V"], spec["Vin_V"], spec["Exp_K0"]
        )
        tp_lh1, tp_hl1, w01_1, w10_1 = compute_delays_and_transitions(
            t1_ns, None, v1, spec["VDD_V"], spec["Vin_V"], spec["Exp_K1"]
        )
        all_delays = tp_lh0 + tp_hl0 + tp_lh1 + tp_hl1
        atraso_medio_ps = float(np.mean(all_delays)) if all_delays else 0.0

        ipk_01_m0 = extract_transition_peaks(t0_ns, i0, w01_0) * 1e6
        ipk_10_m0 = extract_transition_peaks(t0_ns, i0, w10_0) * 1e6
        ipk_01_m1 = extract_transition_peaks(t1_ns, i1, w01_1) * 1e6
        ipk_10_m1 = extract_transition_peaks(t1_ns, i1, w10_1) * 1e6

        dpa_trans_01_pct = asym_pct(ipk_01_m0, ipk_01_m1)
        dpa_trans_10_pct = asym_pct(ipk_10_m0, ipk_10_m1)
        # Assimetria maxima entre 0->1 e 1->0 dentro dos modos
        asym_rise_fall_pct = float(max(asym_pct(ipk_01_m0, ipk_10_m0), asym_pct(ipk_01_m1, ipk_10_m1)))

        # Potencia e energia
        pot_med0_nw = i_med0_ua * 1e-6 * spec["VDD_V"] * 1e9
        pot_med1_nw = i_med1_ua * 1e-6 * spec["VDD_V"] * 1e9
        pot_med_nw = 0.5 * (pot_med0_nw + pot_med1_nw)

        i_est0_ua = extract_static_current(t0_ns, i0, n_comb) * 1e6
        i_est1_ua = extract_static_current(t1_ns, i1, n_comb) * 1e6
        pot_est_nw = 0.5 * (i_est0_ua + i_est1_ua) * 1e-6 * spec["VDD_V"] * 1e9

        n_trans_sw = max(len(w01_0) + len(w10_0) + len(w01_1) + len(w10_1), 1)
        e_total_j = (np.trapezoid(i0, t0_s) + np.trapezoid(i1, t1_s)) * spec["VDD_V"]
        e_sw_fj = float((e_total_j / n_trans_sw) * 1e15)
        pdp_aj = float(pot_med_nw * atraso_medio_ps * 1e-3)  # nW * ps = 1e-21 J = 1e-3 aJ

        # Monte Carlo (N = 250) sobre a grade real do ngspice
        mc_res = evaluate_monte_carlo_from_grid(
            spec["Tupla"],
            spec["Exp_K0"][:n_comb],
            spec["Exp_K1"][:n_comb],
            spec["VDD_V"],
            dvdd_rel_grid,
            dvss_grid,
            spec["Rob_offset"],
        )
        mc_distributions[spec["Tupla"]] = mc_res
        waveform_traces[spec["Tupla"]] = {
            "t0": t0_ns, "v0": v0, "i0_ua": i0 * 1e6,
            "t1": t1_ns, "v1": v1, "i1_ua": i1 * 1e6,
            "vdd": spec["VDD_V"], "modos": spec["Modos"],
        }

        metric_rows.append({
            "Tupla": spec["Tupla"],
            "Categoria": spec["Categoria"],
            "Entradas": spec["Entradas"],
            "N_Transistores_Nucleo": spec["N_Transistores_Nucleo"],
            "N_Transistores_Total": spec["N_Transistores_Total"],
            "Largura_Total_W_um": spec["Largura_Total_W_um"],
            "VDD_V": spec["VDD_V"],
            "Corretude_pct": round(100.0 * correct_total / (2 * n_comb), 2),
            "V1_min_V": round(float(min(v1_list)), 4),
            "V0_max_V": round(float(max(v0_list)), 4),
            "I_pico_Modo0_uA": round(i_pico0_ua, 4),
            "I_pico_Modo1_uA": round(i_pico1_ua, 4),
            "Assimetria_DPA_Pico_pct": round(dpa_pico_pct, 2),
            "I_medio_Modo0_uA": round(i_med0_ua, 4),
            "I_medio_Modo1_uA": round(i_med1_ua, 4),
            "Assimetria_DPA_Media_pct": round(dpa_med_pct, 2),
            "Assimetria_0to1_Modos_pct": round(dpa_trans_01_pct, 2),
            "Assimetria_1to0_Modos_pct": round(dpa_trans_10_pct, 2),
            "Assimetria_01_vs_10_pct": round(asym_rise_fall_pct, 2),
            "Potencia_Media_nW": round(pot_med_nw, 2),
            "Potencia_Estatica_nW": round(pot_est_nw, 2),
            "Energia_Chaveamento_fJ": round(e_sw_fj, 4),
            "Atraso_Medio_ps": round(atraso_medio_ps, 2),
            "PDP_aJ": round(pdp_aj, 2),
            "MC_Amostras": mc_res["MC_Amostras"],
            "MC_Taxa_Acerto_pct": round(mc_res["MC_Taxa_Acerto_pct"], 2),
            "MC_Std_Nivel1_mV": round(mc_res["MC_Std_Nivel1_mV"], 2),
            "MC_Std_Nivel0_mV": round(mc_res["MC_Std_Nivel0_mV"], 2),
        })

    df_tt = pd.DataFrame(tt_rows)
    df_metrics = pd.DataFrame(metric_rows)
    df_tt.to_csv(os.path.join(BASE_DIR, "tabelas_verdade_tuplas.csv"), index=False)
    df_metrics.to_csv(os.path.join(BASE_DIR, "metricas_tuplas_dpa.csv"), index=False)

    assert df_tt["Correto"].all(), "Falha na verificacao funcional das tuplas polimorficas!"
    return df_tt, df_metrics, mc_distributions, waveform_traces


def analyze_full_adder_profiles():
    """Analisa os 3 Perfis de Full Adder e gera benchmark_full_adder_perfis.csv."""
    fa_p1 = np.loadtxt(os.path.join(BASE_DIR, "fa_p1.dat"), skiprows=1)
    fa_p2_k0 = np.loadtxt(os.path.join(BASE_DIR, "fa_p2_k0.dat"), skiprows=1)
    fa_p2_k1 = np.loadtxt(os.path.join(BASE_DIR, "fa_p2_k1.dat"), skiprows=1)
    fa_p3_k0 = np.loadtxt(os.path.join(BASE_DIR, "fa_p3_k0.dat"), skiprows=1)
    fa_p3_k1 = np.loadtxt(os.path.join(BASE_DIR, "fa_p3_k1.dat"), skiprows=1)

    def eval_fa_truth(dat):
        t_ns = dat[:, 0] * 1e9
        errs_s, errs_c = 0, 0
        sum_bits, cout_bits = [], []
        for i in range(8):
            a_exp, b_exp, c_exp = (i >> 2) & 1, (i >> 1) & 1, i & 1
            m = (t_ns >= i * 5.0 + 4.2) & (t_ns <= i * 5.0 + 4.8)
            vs = float(np.mean(dat[m, 4]))
            vc = float(np.mean(dat[m, 5]))
            sb = 1 if vs > 0.75 else 0
            cb = 1 if vc > (0.75 if np.max(dat[:, 5]) > 1.0 else 0.40) else 0
            exp_s = a_exp ^ b_exp ^ c_exp
            exp_c = (a_exp & b_exp) | (c_exp & (a_exp ^ b_exp))
            errs_s += int(sb != exp_s)
            errs_c += int(cb != exp_c)
            sum_bits.append(sb)
            cout_bits.append(cb)
        return errs_s, errs_c, sum_bits, cout_bits

    # Validacao K=00
    for pname, dat in [("Perfil 1", fa_p1), ("Perfil 2", fa_p2_k0), ("Perfil 3", fa_p3_k0)]:
        es, ec, _, _ = eval_fa_truth(dat)
        assert es == 0 and ec == 0, f"{pname} falhou em K=00 (es={es}, ec={ec})"

    # HD em chave oposta K=11
    es2, ec2, _, _ = eval_fa_truth(fa_p2_k1)
    es3, ec3, _, _ = eval_fa_truth(fa_p3_k1)
    hd_p2_pct = 100.0 * (es2 + ec2) / 16.0
    hd_p3_pct = 100.0 * (es3 + ec3) / 16.0

    # Atrasos medios Sum e Cout em K=00
    exp_sum_seq = [((i >> 2) & 1) ^ ((i >> 1) & 1) ^ (i & 1) for i in range(8)]
    exp_cout_seq = [(((i >> 2) & 1) & ((i >> 1) & 1)) | ((i & 1) & (((i >> 2) & 1) ^ ((i >> 1) & 1))) for i in range(8)]

    def mean_delay_fa(dat, vdd_cout):
        t_ns = dat[:, 0] * 1e9
        lh_s, hl_s, _, _ = compute_delays_and_transitions(t_ns, None, dat[:, 4], 1.5, 1.1, exp_sum_seq)
        lh_c, hl_c, _, _ = compute_delays_and_transitions(t_ns, None, dat[:, 5], vdd_cout, 0.8, exp_cout_seq)
        return float(np.mean(lh_s + hl_s)), float(np.mean(lh_c + hl_c))

    ds1, dc1 = mean_delay_fa(fa_p1, 1.5)
    ds2, dc2 = mean_delay_fa(fa_p2_k0, 0.8)
    ds3, dc3 = mean_delay_fa(fa_p3_k0, 1.5)

    # Potencia total em K=00: P = V15*I15 + V11*I11 + V08*I08 + trilhos ativos
    # Perfil 1: col 6 (Vdd15), 7 (Vdd11), 8 (Vdd08)
    def power_p1(d):
        t_s = d[:, 0]
        p = 1.5 * np.abs(-d[:, 6]) + 1.1 * np.abs(-d[:, 7]) + 0.8 * np.abs(-d[:, 8])
        return time_avg(t_s, p) * 1e9

    # Perfil 2: col 6..8 (Vdd15,11,08), 9 (xrtop=1.5), 11 (nrtop=0.8)
    def power_p2_k0(d):
        t_s = d[:, 0]
        p = (1.5 * (np.abs(-d[:, 6]) + np.abs(-d[:, 9]))
             + 1.1 * np.abs(-d[:, 7])
             + 0.8 * (np.abs(-d[:, 8]) + np.abs(-d[:, 11])))
        return time_avg(t_s, p) * 1e9

    # Perfil 3: col 6..8 (Vdd15,11,08), 9 (xrtop=1.5), 12 (mrbot=1.5), 13 (Vdd15_c3)
    def power_p3_k0(d):
        t_s = d[:, 0]
        p = (1.5 * (np.abs(-d[:, 6]) + np.abs(-d[:, 9]) + np.abs(-d[:, 12]) + np.abs(-d[:, 13]))
             + 1.1 * np.abs(-d[:, 7])
             + 0.8 * np.abs(-d[:, 8]))
        return time_avg(t_s, p) * 1e9

    pw1 = power_p1(fa_p1)
    pw2 = power_p2_k0(fa_p2_k0)
    pw3 = power_p3_k0(fa_p3_k0)

    # Assimetria DPA no estagio de Cout (que diferencia os perfis):
    # Perfil 1: sem modo K=1 (assimetria N/A -> sem ofuscacao)
    # Perfil 2: K=0 -> Vnrtop (col 11), K=1 -> Vnrbot (col 12)
    # Perfil 3: K=0 -> Vmrbot (col 12) + Vdd15_c3 (col 13), K=1 -> Vmrtop (col 11) + Vdd15_c3 (col 13)
    i_c2_k0 = np.abs(-fa_p2_k0[:, 11])
    i_c2_k1 = np.abs(-fa_p2_k1[:, 12])
    i_c3_k0 = np.abs(-fa_p3_k0[:, 12]) + np.abs(-fa_p3_k0[:, 13])
    i_c3_k1 = np.abs(-fa_p3_k1[:, 11]) + np.abs(-fa_p3_k1[:, 13])

    pk2_0, pk2_1 = float(np.max(i_c2_k0) * 1e6), float(np.max(i_c2_k1) * 1e6)
    md2_0, md2_1 = time_avg(fa_p2_k0[:, 0], i_c2_k0) * 1e6, time_avg(fa_p2_k1[:, 0], i_c2_k1) * 1e6

    pk3_0, pk3_1 = float(np.max(i_c3_k0) * 1e6), float(np.max(i_c3_k1) * 1e6)
    md3_0, md3_1 = time_avg(fa_p3_k0[:, 0], i_c3_k0) * 1e6, time_avg(fa_p3_k1[:, 0], i_c3_k1) * 1e6

    # Pior caso de assimetria de pico entre os estagios polimorficos (Sum XOR/XNOR vs Cout)
    pk_s2_0, pk_s2_1 = float(np.max(np.abs(-fa_p2_k0[:, 9])) * 1e6), float(np.max(np.abs(-fa_p2_k1[:, 10])) * 1e6)
    pk_s3_0, pk_s3_1 = float(np.max(np.abs(-fa_p3_k0[:, 9])) * 1e6), float(np.max(np.abs(-fa_p3_k1[:, 10])) * 1e6)
    asym_poly_p2 = max(asym_pct(pk_s2_0, pk_s2_1), asym_pct(pk2_0, pk2_1))
    asym_poly_p3 = max(asym_pct(pk_s3_0, pk_s3_1), asym_pct(pk3_0, pk3_1))

    rows = [
        {
            "Perfil": "1. Baseline (Comum)",
            "Arquitetura": "2x XOR 4T + 4x INV 2T + 1x MAJ3 4T fixo",
            "N_Transistores_Nucleo": 20,
            "Largura_Total_W_um": 24.0,
            "Corretude_K0_pct": 100.0,
            "HD_Chave_Errada_pct": 0.0,
            "Atraso_Sum_ps": round(ds1, 2),
            "Atraso_Cout_ps": round(dc1, 2),
            "Atraso_Critico_ps": round(max(ds1, dc1), 2),
            "Potencia_Media_nW": round(pw1, 2),
            "PDP_Critico_aJ": round(pw1 * max(ds1, dc1) * 1e-3, 2),
            "I_pico_Cout_K0_uA": round(float(np.max(np.abs(-fa_p1[:, 6])) * 1e6), 4),
            "I_pico_Cout_K1_uA": np.nan,
            "Assimetria_DPA_Cout_Pico_pct": np.nan,
            "Assimetria_DPA_Cout_Media_pct": np.nan,
            "Assimetria_DPA_Polimorfico_Pico_pct": np.nan,
        },
        {
            "Perfil": "2. Custo/Desempenho (NAND/NOR)",
            "Arquitetura": "2x XOR/XNOR 4T + 4x INV 2T + 3x NAND/NOR 4T",
            "N_Transistores_Nucleo": 28,
            "Largura_Total_W_um": 38.0,
            "Corretude_K0_pct": 100.0,
            "HD_Chave_Errada_pct": round(hd_p2_pct, 2),
            "Atraso_Sum_ps": round(ds2, 2),
            "Atraso_Cout_ps": round(dc2, 2),
            "Atraso_Critico_ps": round(max(ds2, dc2), 2),
            "Potencia_Media_nW": round(pw2, 2),
            "PDP_Critico_aJ": round(pw2 * max(ds2, dc2) * 1e-3, 2),
            "I_pico_Cout_K0_uA": round(pk2_0, 4),
            "I_pico_Cout_K1_uA": round(pk2_1, 4),
            "Assimetria_DPA_Cout_Pico_pct": round(asym_pct(pk2_0, pk2_1), 2),
            "Assimetria_DPA_Cout_Media_pct": round(asym_pct(md2_0, md2_1), 2),
            "Assimetria_DPA_Polimorfico_Pico_pct": round(asym_poly_p2, 2),
        },
        {
            "Perfil": "3. Baixa Assimetria (XOR+MAJ/XOR)",
            "Arquitetura": "2x XOR/XNOR 4T + 4x INV 2T + 1x MAJ3/XOR3 10T",
            "N_Transistores_Nucleo": 26,
            "Largura_Total_W_um": 38.0,
            "Corretude_K0_pct": 100.0,
            "HD_Chave_Errada_pct": round(hd_p3_pct, 2),
            "Atraso_Sum_ps": round(ds3, 2),
            "Atraso_Cout_ps": round(dc3, 2),
            "Atraso_Critico_ps": round(max(ds3, dc3), 2),
            "Potencia_Media_nW": round(pw3, 2),
            "PDP_Critico_aJ": round(pw3 * max(ds3, dc3) * 1e-3, 2),
            "I_pico_Cout_K0_uA": round(pk3_0, 4),
            "I_pico_Cout_K1_uA": round(pk3_1, 4),
            "Assimetria_DPA_Cout_Pico_pct": round(asym_pct(pk3_0, pk3_1), 2),
            "Assimetria_DPA_Cout_Media_pct": round(asym_pct(md3_0, md3_1), 2),
            "Assimetria_DPA_Polimorfico_Pico_pct": round(asym_poly_p3, 2),
        },
    ]

    df_fa = pd.DataFrame(rows)
    df_fa.to_csv(os.path.join(BASE_DIR, "benchmark_full_adder_perfis.csv"), index=False)

    fa_traces = {
        "t": fa_p2_k0[:, 0] * 1e9,
        "t2_k1": fa_p2_k1[:, 0] * 1e9,
        "t3_k0": fa_p3_k0[:, 0] * 1e9,
        "t3_k1": fa_p3_k1[:, 0] * 1e9,
        "i_c2_k0": i_c2_k0 * 1e6,
        "i_c2_k1": i_c2_k1 * 1e6,
        "i_c3_k0": i_c3_k0 * 1e6,
        "i_c3_k1": i_c3_k1 * 1e6,
    }
    return df_fa, fa_traces


# ---------------------------------------------------------------------------
# Geracao de figuras
# ---------------------------------------------------------------------------

def generate_figures(df_metrics, mc_distributions, waveform_traces, df_fa, fa_traces):
    """Gera as 4 figuras principais em 200 DPI."""
    plt.rcParams.update({"font.size": 9.5, "axes.grid": True, "grid.alpha": 0.3})

    # --- Figura 1: Assinaturas de Corrente e Tensão (7 tuplas x 2 colunas) ---
    n_tup = len(df_metrics)
    fig, axes = plt.subplots(n_tup, 2, figsize=(13.5, 16.0))
    for r_idx, row in df_metrics.iterrows():
        tname = row["Tupla"]
        tr = waveform_traces[tname]
        m0, m1 = tr["modos"]

        ax_v = axes[r_idx, 0]
        ax_v.plot(tr["t0"], tr["v0"], "#08519c", lw=1.7, label=f"Key=0: {m0}")
        ax_v.plot(tr["t1"], tr["v1"], "#cb181d", lw=1.5, ls="--", label=f"Key=1: {m1}")
        ax_v.set_ylabel(f"{tname}\n$V_{{out}}$ (V)", fontsize=8.5, fontweight="bold")
        ax_v.set_ylim(-0.1, tr["vdd"] * 1.18)
        ax_v.legend(loc="upper right", fontsize=7.8, ncol=2)

        ax_i = axes[r_idx, 1]
        ax_i.plot(tr["t0"], tr["i0_ua"], "#08519c", lw=1.6, label=f"{m0} ($I_{{pico}}={row['I_pico_Modo0_uA']:.3f}\\,\\mu\\mathrm{{A}}$)")
        ax_i.plot(tr["t1"], tr["i1_ua"], "#cb181d", lw=1.4, ls="--", alpha=0.88, label=f"{m1} ($I_{{pico}}={row['I_pico_Modo1_uA']:.3f}\\,\\mu\\mathrm{{A}}$)")
        ax_i.set_ylabel("$|I_{VDD}|\\ (\\mu\\mathrm{A})$", fontsize=8.5)
        ax_i.set_title(
            f"Assimetria Pico: {row['Assimetria_DPA_Pico_pct']:.2f}% | Média: {row['Assimetria_DPA_Media_pct']:.2f}%",
            loc="right", fontsize=8.5, fontweight="bold",
        )
        ax_i.legend(loc="upper right", fontsize=7.5)

    axes[0, 0].set_title("Saída Lógica ($V_{out}$) vs. Tempo", loc="left", fontweight="bold")
    axes[0, 1].text(
        0.0, 1.06, "Assinatura de Corrente $|I(V_{DD})|$",
        transform=axes[0, 1].transAxes, fontsize=10.0, fontweight="bold",
    )
    axes[-1, 0].set_xlabel("Tempo (ns)")
    axes[-1, 1].set_xlabel("Tempo (ns)")
    fig.suptitle("Comparação Temporal de Tensão e Assinaturas de Corrente DPA nas 7 Tuplas Polimórficas", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(BASE_DIR, "fig1_assinaturas_corrente_tuplas.png"), dpi=200)
    plt.close(fig)

    # --- Figura 2: Pareto (Assimetria DPA x Area e PDP) ---
    fig, axes = plt.subplots(1, 2, figsize=(13.8, 6.0))
    cat_colors = {
        "Universal Compacta": "#cb181d",
        "Simetrica Segura": "#238b45",
        "Logica de Controle": "#e6550d",
        "Logic Locking Misto": "#6a51a3",
        "Composta ASIC": "#2171b5",
        "Aritmetica Simetrica": "#006d2c",
    }

    # Painel esquerdo: Assimetria DPA de Pico (%) x N Transistores Nucleo
    x_tr = df_metrics["N_Transistores_Nucleo"].values
    y_pk = df_metrics["Assimetria_DPA_Pico_pct"].values

    xy_offsets_left = {
        "(NAND, NOR)": (4.35, 153.0),
        "(XOR, XNOR)": (4.35, 22.0),
        "(AOI21, OAI21)": (6.45, 76.0),
        "(NAND, XNOR)": (6.45, 44.0),
        "(AND, OR)": (6.45, 21.0),
        "(NOR, XOR)": (6.45, -3.0),
        "(MAJ3, XOR3)": (8.25, 19.0),
    }

    for _, row in df_metrics.iterrows():
        c = cat_colors.get(row["Categoria"], "#333333")
        axes[0].scatter(row["N_Transistores_Nucleo"], row["Assimetria_DPA_Pico_pct"], s=row["Largura_Total_W_um"] * 24,
                        color=c, edgecolor="k", alpha=0.88, zorder=3)
        tx, ty = xy_offsets_left[row["Tupla"]]
        axes[0].annotate(
            f"{row['Tupla']}\n({row['Assimetria_DPA_Pico_pct']:.2f}%, {row['N_Transistores_Nucleo']}T)",
            (row["N_Transistores_Nucleo"], row["Assimetria_DPA_Pico_pct"]),
            xytext=(tx, ty),
            fontsize=8.0, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color="#666666", lw=0.7),
        )

    # Fronteira de Pareto (minimizando N_Transistores e Assimetria_DPA_Pico_pct)
    order = np.argsort(x_tr)
    pareto_x, pareto_y = [], []
    best_y = float("inf")
    for idx in order:
        if y_pk[idx] < best_y - 1e-6:
            pareto_x.append(x_tr[idx])
            pareto_y.append(y_pk[idx])
            best_y = y_pk[idx]
    axes[0].plot(pareto_x, pareto_y, "k--", lw=1.4, label="Fronteira de Pareto (Área × Assimetria)")
    axes[0].set_xlabel("Nº de Transistores no Núcleo Polimórfico")
    axes[0].set_ylabel("Assimetria DPA de Pico (%)")
    axes[0].set_title("Espaço de Projeto: Assimetria DPA de Pico × Área (Núcleo)")
    axes[0].set_xlim(3.2, 11.4)
    axes[0].set_ylim(-12, max(y_pk) * 1.18)
    axes[0].legend(loc="upper right", fontsize=8.5)

    # Painel direito: Assimetria DPA Media (%) x PDP (aJ)
    xy_offsets_right = {
        "(NAND, XNOR)": (17.2, 76.5),
        "(XOR, XNOR)": (14.0, 10.5),
        "(NOR, XOR)": (17.5, 57.5),
        "(AND, OR)": (24.5, 22.0),
        "(NAND, NOR)": (24.0, 51.0),
        "(AOI21, OAI21)": (30.5, 4.0),
        "(MAJ3, XOR3)": (31.5, 62.0),
    }

    for _, row in df_metrics.iterrows():
        c = cat_colors.get(row["Categoria"], "#333333")
        axes[1].scatter(row["PDP_aJ"], row["Assimetria_DPA_Media_pct"], s=row["N_Transistores_Nucleo"] * 28,
                        color=c, edgecolor="k", alpha=0.88, zorder=3)
        tx, ty = xy_offsets_right[row["Tupla"]]
        axes[1].annotate(
            f"{row['Tupla']}\n({row['Assimetria_DPA_Media_pct']:.2f}%, {row['PDP_aJ']:.1f} aJ)",
            (row["PDP_aJ"], row["Assimetria_DPA_Media_pct"]),
            xytext=(tx, ty),
            fontsize=7.8, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color="#666666", lw=0.7),
        )

    axes[1].set_xlabel("Produto Atraso-Potência — PDP (aJ)")
    axes[1].set_ylabel("Assimetria DPA Média (%)")
    axes[1].set_title("Trade-off Energético: Assimetria DPA Média × PDP")
    axes[1].set_xlim(13.0, 44.0)
    axes[1].set_ylim(-6, max(df_metrics["Assimetria_DPA_Media_pct"]) * 1.24)

    fig.suptitle("Fronteira de Pareto: Segurança contra DPA vs. Custo de Hardware e Energia (BP SB-FET)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(BASE_DIR, "fig2_pareto_assimetria_vs_custo.png"), dpi=200)
    plt.close(fig)

    # --- Figura 3: Robustez Monte Carlo e Desempenho (Atraso / Energia) ---
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.6))

    names = df_metrics["Tupla"].tolist()
    x = np.arange(len(names))
    # Painel esquerdo: Margens normalizadas V/VDD em Monte Carlo (N=250)
    means_1, stds_1, means_0, stds_0 = [], [], [], []
    for row in df_metrics.itertuples():
        mc = mc_distributions[row.Tupla]
        vdd = row.VDD_V
        means_1.append(mc["MC_Nivel1_Medio_V"] / vdd)
        stds_1.append(mc["MC_Std_Nivel1_mV"] / (vdd * 1e3))
        means_0.append(mc["MC_Nivel0_Medio_V"] / vdd)
        stds_0.append(mc["MC_Std_Nivel0_mV"] / (vdd * 1e3))

    axes[0].errorbar(x - 0.12, means_1, yerr=stds_1, fmt="o", capsize=4, color="#08519c", lw=1.8, label="Nível '1' Normalizado ($V_{OH}/V_{DD}$)")
    axes[0].errorbar(x + 0.12, means_0, yerr=stds_0, fmt="s", capsize=4, color="#cb181d", lw=1.8, label="Nível '0' Normalizado ($V_{OL}/V_{DD}$)")
    axes[0].axhline(0.5, color="#555555", ls="--", lw=1.1, label="Limiar Lógico ($0,5\\,V_{DD}$)")
    for idx, acc in enumerate(df_metrics["MC_Taxa_Acerto_pct"]):
        axes[0].text(idx, 1.07, f"{acc:.1f}%", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color="#006d2c")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(names, rotation=22, ha="right", fontsize=8.5, fontweight="bold")
    axes[0].set_ylabel("Tensão de Saída Normalizada ($V_{out}/V_{DD}$)")
    axes[0].set_ylim(-0.08, 1.20)
    axes[0].set_title("Robustez Monte Carlo ($N=250$, $\\Delta V_{DD}, \\Delta V_{SS}$)")
    axes[0].legend(loc="center right", fontsize=8.0)

    # Painel direito: Atraso Medio (ps) e Energia de Chaveamento (fJ)
    w = 0.36
    ax_e = axes[1].twinx()
    b1 = axes[1].bar(x - w / 2, df_metrics["Atraso_Medio_ps"], width=w, color="#3182bd", label="Atraso Médio (ps)")
    b2 = ax_e.bar(x + w / 2, df_metrics["Energia_Chaveamento_fJ"], width=w, color="#fd8d3c", label="Energia / Chaveamento (fJ)")
    ax_e.grid(False)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(names, rotation=22, ha="right", fontsize=8.5, fontweight="bold")
    axes[1].set_ylabel("Atraso Médio $t_p$ (ps)", color="#08519c")
    ax_e.set_ylabel("Energia por Chaveamento $E_{sw}$ (fJ)", color="#d94701")
    axes[1].set_ylim(0, max(df_metrics["Atraso_Medio_ps"]) * 1.25)
    ax_e.set_ylim(0, max(df_metrics["Energia_Chaveamento_fJ"]) * 1.25)
    axes[1].set_title("Desempenho e Eficiência Energética ($C_{load} = 0,3\\,\\mathrm{fF}$)")
    lines1, labels1 = axes[1].get_legend_handles_labels()
    lines2, labels2 = ax_e.get_legend_handles_labels()
    axes[1].legend(lines1 + lines2, labels1 + labels2, loc="upper center", ncol=2, fontsize=8.0)

    fig.suptitle("Robustez Estatística sob Ruído nos Trilhos e Métricas de Atraso/Energia", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(BASE_DIR, "fig3_robustez_montecarlo_tuplas.png"), dpi=200)
    plt.close(fig)

    # --- Figura 4: Benchmark Full Adder em 3 Perfis ---
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 8.8))

    perfis_lbl = ["1. Baseline\n(20T, s/ Lock)", "2. Custo/Desempenho\n(28T, NAND/NOR)", "3. Baixa Assimetria\n(26T, XOR+MAJ/XOR)"]
    px = np.arange(3)

    # [0,0] N Transistores e Atraso Critico
    ax00_r = axes[0, 0].twinx()
    ax00_r.grid(False)
    b_t = axes[0, 0].bar(px - 0.18, df_fa["N_Transistores_Nucleo"], width=0.34, color="#6baed6", label="Nº Transistores (Núcleo)")
    b_d = ax00_r.bar(px + 0.18, df_fa["Atraso_Critico_ps"], width=0.34, color="#756bb1", label="Atraso Crítico (ps)")
    for b in b_t:
        axes[0, 0].text(b.get_x() + b.get_width() / 2, b.get_height() + 0.6, f"{int(b.get_height())}T", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    for b in b_d:
        ax00_r.text(b.get_x() + b.get_width() / 2, b.get_height() + 4, f"{b.get_height():.0f} ps", ha="center", va="bottom", fontsize=8.2, fontweight="bold")
    axes[0, 0].set_xticks(px)
    axes[0, 0].set_xticklabels(perfis_lbl, fontsize=8.5, fontweight="bold")
    axes[0, 0].set_ylabel("Nº de Transistores")
    ax00_r.set_ylabel("Atraso Crítico (ps)")
    axes[0, 0].set_ylim(0, 35)
    ax00_r.set_ylim(0, max(df_fa["Atraso_Critico_ps"]) * 1.25)
    axes[0, 0].set_title("Área (Transistores) e Atraso Crítico")
    l1, lb1 = axes[0, 0].get_legend_handles_labels()
    l2, lb2 = ax00_r.get_legend_handles_labels()
    axes[0, 0].legend(l1 + l2, lb1 + lb2, loc="upper left", fontsize=7.8)

    # [0,1] PDP e Assimetria DPA + HD
    ax01_r = axes[0, 1].twinx()
    ax01_r.grid(False)
    dpa_vals = [0.0 if np.isnan(v) else v for v in df_fa["Assimetria_DPA_Cout_Pico_pct"]]
    b_pdp = axes[0, 1].bar(px - 0.18, df_fa["PDP_Critico_aJ"], width=0.34, color="#31a354", label="PDP Crítico (aJ)")
    b_dpa = ax01_r.bar(px + 0.18, dpa_vals, width=0.34, color="#cb181d", label="Assimetria DPA Cout (%)")
    for idx_b, b in enumerate(b_pdp):
        axes[0, 1].text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, f"{b.get_height():.1f} aJ", ha="center", va="bottom", fontsize=8.2, fontweight="bold")
    for idx_b, b in enumerate(b_dpa):
        txt = "N/A" if idx_b == 0 else f"{b.get_height():.2f}%"
        ax01_r.text(b.get_x() + b.get_width() / 2, b.get_height() + 2.5, txt, ha="center", va="bottom", fontsize=8.2, fontweight="bold", color="#99000d")
    axes[0, 1].set_xticks(px)
    axes[0, 1].set_xticklabels(perfis_lbl, fontsize=8.5, fontweight="bold")
    axes[0, 1].set_ylabel("PDP Crítico (aJ)")
    ax01_r.set_ylabel("Assimetria DPA de Pico no Carry (%)")
    axes[0, 1].set_ylim(0, max(df_fa["PDP_Critico_aJ"]) * 1.25)
    ax01_r.set_ylim(0, max(dpa_vals) * 1.25 if max(dpa_vals) > 0 else 10)
    axes[0, 1].set_title("Trade-off: PDP vs. Vulnerabilidade DPA (Carry)")
    l1, lb1 = axes[0, 1].get_legend_handles_labels()
    l2, lb2 = ax01_r.get_legend_handles_labels()
    axes[0, 1].legend(l1 + l2, lb1 + lb2, loc="upper left", fontsize=7.8)

    # [1,0] Corrente no estagio Cout Perfil 2 (NAND/NOR) K=0 vs K=1
    axes[1, 0].plot(fa_traces["t"], fa_traces["i_c2_k0"], "#08519c", lw=1.6, label=f"K=00 (NAND): Pico {df_fa.iloc[1]['I_pico_Cout_K0_uA']:.3f} µA")
    axes[1, 0].plot(fa_traces["t2_k1"], fa_traces["i_c2_k1"], "#cb181d", lw=1.4, ls="--", label=f"K=11 (NOR): Pico {df_fa.iloc[1]['I_pico_Cout_K1_uA']:.3f} µA")
    axes[1, 0].set_title(f"Perfil 2 (NAND/NOR): Alta Assimetria DPA ({df_fa.iloc[1]['Assimetria_DPA_Cout_Pico_pct']:.2f}%)", fontweight="bold")
    axes[1, 0].set_xlabel("Tempo (ns)")
    axes[1, 0].set_ylabel("$|I_{VDD}|$ Carry-Out ($\\mu\\mathrm{A}$)")
    axes[1, 0].legend(fontsize=8.2)

    # [1,1] Corrente no estagio Cout Perfil 3 (MAJ3/XOR3) K=0 vs K=1
    axes[1, 1].plot(fa_traces["t3_k0"], fa_traces["i_c3_k0"], "#08519c", lw=1.6, label=f"K=00 (MAJ3): Pico {df_fa.iloc[2]['I_pico_Cout_K0_uA']:.3f} µA")
    axes[1, 1].plot(fa_traces["t3_k1"], fa_traces["i_c3_k1"], "#238b45", lw=1.4, ls="--", label=f"K=11 (XOR3): Pico {df_fa.iloc[2]['I_pico_Cout_K1_uA']:.3f} µA")
    axes[1, 1].set_title(f"Perfil 3 (MAJ3/XOR3): Baixíssima Assimetria DPA ({df_fa.iloc[2]['Assimetria_DPA_Cout_Pico_pct']:.2f}%)", fontweight="bold")
    axes[1, 1].set_xlabel("Tempo (ns)")
    axes[1, 1].set_ylabel("$|I_{VDD}|$ Carry-Out ($\\mu\\mathrm{A}$)")
    axes[1, 1].legend(fontsize=8.2)

    fig.suptitle("Benchmark em Sistema: Full Adder 1-bit em Três Perfis (Área × Desempenho × Segurança DPA)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(BASE_DIR, "fig4_benchmark_full_adder_perfis.png"), dpi=200)
    plt.close(fig)


def main():
    print("1/4 Executando testbench das 5 tuplas de 2 entradas...")
    build_and_run_2input_tuples()
    print("2/4 Executando testbench das 2 tuplas de 3 entradas...")
    build_and_run_3input_tuples()
    print("3/4 Executando varredura de robustez VDD x VSS e benchmark Full Adder...")
    dvdd_rel_grid, dvss_grid = build_and_run_robustness_sweep()
    build_and_run_full_adder_profiles()
    print("4/4 Analisando metricas e gerando graficos...")
    df_tt, df_metrics, mc_distributions, waveform_traces = analyze_tuples(dvdd_rel_grid, dvss_grid)
    df_fa, fa_traces = analyze_full_adder_profiles()
    generate_figures(df_metrics, mc_distributions, waveform_traces, df_fa, fa_traces)

    print("\n=== METRICAS DAS 7 TUPLAS POLIMORFICAS ===")
    cols_show = [
        "Tupla", "N_Transistores_Nucleo", "VDD_V", "Corretude_pct",
        "Assimetria_DPA_Pico_pct", "Assimetria_DPA_Media_pct",
        "Atraso_Medio_ps", "Potencia_Media_nW", "PDP_aJ", "MC_Taxa_Acerto_pct",
    ]
    print(df_metrics[cols_show].to_string(index=False))

    print("\n=== BENCHMARK FULL ADDER EM 3 PERFIS ===")
    print(df_fa.to_string(index=False))
    print("\nModulo 07 concluido com sucesso.")


if __name__ == "__main__":
    main()
