"""
Módulo 00 — Geração do Modelo BP SB-FET Refinado (Superfície 4D) para Ngspice,
Caracterização do Dispositivo 2D e Validação Cruzada Quantitativa contra HSPICE.

Melhorias da Versão 2 (Superfície 4D Refinada):
1. Interpolação bilinear 2D completa em (Vg1, Vg2) nas fatias de transferência
   (28 curvas n-FET em 7x4 e 32 curvas p-FET em 8x4, incluindo explicitamente Vg2 = -1,5 V).
2. Saturação / região tríodo 2D (Vtg, Vds) específica por porta extraída diretamente
   das varreduras experimentais de saída (fds_n e fds_p como PWL ímpares contínuas,
   eliminando o tanh(2.5*Vds) 1D global e preservando g_ds > 0 na origem e simetria bilateral).
3. Validação cruzada quantitativa automática comparando Modelo v1 (1D + tanh) vs.
   Modelo v2 (Superfície 4D Refinada) diretamente contra os arquivos .printtr0 do HSPICE
   original (results_ari_N_transfer, P_transfer, N_output, P_output).
"""

import os
import re
import shutil
import subprocess
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DATA_DIR = os.path.join(ROOT_DIR, "BPFET_Nature_Electronics", "BP_SBFET_MODEL")
NGSPICE_EXE = os.path.join(ROOT_DIR, "ngspice-47_64", "Spice64", "bin", "ngspice_con.exe")
LIB_PATH = os.path.join(BASE_DIR, "bp_ari_ngspice.lib")


def load_tables():
    """Carrega as tabelas experimentais originais n-FET e p-FET."""
    data_n = np.loadtxt(os.path.join(DATA_DIR, "BP_ARI_dataN.txt"), skiprows=1)
    data_p = np.loadtxt(os.path.join(DATA_DIR, "BP_ARI_dataP.txt"), skiprows=1)
    return data_n, data_p


def build_hat_pwl(grid, idx, clamp_bound=1000.0):
    """Constrói os pares (x, peso) de uma função-chapéu 1D com travamento plano externo."""
    val = grid[idx]
    if idx == 0:
        pts = [(-clamp_bound, 1.0), (val, 1.0), (grid[idx + 1], 0.0), (clamp_bound, 0.0)]
    elif idx == len(grid) - 1:
        pts = [(-clamp_bound, 0.0), (grid[idx - 1], 0.0), (val, 1.0), (clamp_bound, 1.0)]
    else:
        pts = [
            (-clamp_bound, 0.0),
            (grid[idx - 1], 0.0),
            (val, 1.0),
            (grid[idx + 1], 0.0),
            (clamp_bound, 0.0),
        ]
    return ", ".join(f"{x:g}, {y:g}" for x, y in pts)


def make_odd_pwl(pos_pts, clamp_bound=1000.0):
    """Constrói PWL ímpar estritamente monotônica em Vds com travamento plano externo."""
    neg_pts = [(-clamp_bound, -pos_pts[-1][1])] + [(-x, -y) for x, y in reversed(pos_pts[1:])]
    full = neg_pts + pos_pts + [(clamp_bound, pos_pts[-1][1])]
    return ", ".join(f"{x:g}, {y:g}" for x, y in full)


def generate_ngspice_library_v1(data_n, data_p, out_path):
    """Gera a biblioteca v1 (1D + tanh) apenas para comparação cruzada com a v2."""
    vg1_n_list = [-0.1, 0.1, 0.3, 0.5, 0.7, 0.9, 1.1]
    vg1_p_list = [-1.5, -1.3, -1.1, -0.9, -0.7, -0.5, -0.3, -0.1]
    scale_p_m11_to_m12 = 1.79e-6 / 1.44e-6

    lines = [
        "* Biblioteca Comportamental BP SB-FET v1 (Baseline 1D + tanh)",
        ".subckt ARI d g s g1 g2 W=1.0",
        "B_vgn  vgn  0 V = v(g)  - min(v(d), v(s))",
        "B_vg1n vg1n 0 V = v(g1) - min(v(d), v(s))",
        "B_vgp  vgp  0 V = v(g)  - max(v(d), v(s))",
        "B_vg1p vg1p 0 V = v(g1) - max(v(d), v(s))",
    ]
    n_terms = []
    for i, g1v in enumerate(vg1_n_list):
        sub = data_n[
            np.isclose(data_n[:, 0], g1v)
            & np.isclose(data_n[:, 1], 0.8)
            & np.isclose(data_n[:, 3], 0.8)
        ]
        sub = sub[np.argsort(sub[:, 2])]
        pwl_str = ", ".join(f"{r[2]:g}, {max(r[4], 0.0):g}" for r in sub)
        lines.append(f"B_in_{i} in_n_{i} 0 V = pwl(v(vgn), {pwl_str})")
        n_terms.append(f"(pwl(v(vg1n), {build_hat_pwl(vg1_n_list, i, 10.0)}) * v(in_n_{i}))")
    lines.append("B_in_tot in_n 0 V = " + " + ".join(n_terms))
    lines.append(
        "B_gn2 gn2 0 V = pwl(v(g2,s), 0.0, 0.0, 0.05, 0.5, 0.2, 0.6182, 0.4, 0.8364, 0.8, 1.0, 1.0, 1.2545, 2.5, 1.2545)"
    )

    p_terms = []
    for i, g1v in enumerate(vg1_p_list):
        vg2_ref = -1.2 if g1v <= -0.5 else -1.1
        scale = 1.0 if g1v <= -0.5 else scale_p_m11_to_m12
        sub = data_p[
            np.isclose(data_p[:, 0], g1v)
            & np.isclose(data_p[:, 1], vg2_ref)
            & np.isclose(data_p[:, 3], -0.8)
        ]
        sub = sub[np.argsort(sub[:, 2])]
        pwl_str = ", ".join(f"{r[2]:g}, {abs(r[4]) * scale:g}" for r in sub)
        lines.append(f"B_ip_{i} in_p_{i} 0 V = pwl(v(vgp), {pwl_str})")
        p_terms.append(f"(pwl(v(vg1p), {build_hat_pwl(vg1_p_list, i, 10.0)}) * v(in_p_{i}))")
    lines.append("B_ip_tot in_p 0 V = " + " + ".join(p_terms))
    lines.append(
        "B_gp2 gp2 0 V = pwl(v(g2,s), -2.5, 1.15, -1.5, 1.10, -1.2, 1.0, -1.1, 0.8045, -0.9, 0.5547, -0.05, 0.4, 0.0, 0.0)"
    )
    lines.extend([
        "B_fds fds 0 V = tanh(2.5*v(d,s))/tanh(2.0)",
        "B_id d s I = W * ((v(g2,s) > 0.0) ? (v(in_n) * v(gn2) * v(fds)) : (v(in_p) * v(gp2) * v(fds)))",
        "R_gmin d s 1e12",
        ".ends ARI",
        "",
    ])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path


def generate_ngspice_library(data_n, data_p, out_path=LIB_PATH):
    """Gera a biblioteca refinada v2 (Superfície 4D completa) compatível com ngspice-47."""
    vg1_n = [-0.1, 0.1, 0.3, 0.5, 0.7, 0.9, 1.1]
    vg2_n = [0.2, 0.4, 0.8, 1.0]
    vg1_p = [-1.5, -1.3, -1.1, -0.9, -0.7, -0.5, -0.3, -0.1]
    vg2_p = [-1.5, -1.2, -1.1, -0.9]

    lines = [
        "* Biblioteca Comportamental BP SB-FET v2 (Superficie 4D Refinada)",
        "* Traducao nativa para ngspice-47 a partir de bp_ari.va, BP_ARI_dataN.txt e BP_ARI_dataP.txt",
        "* Superficie 2D completa (Vg1, Vg2) + curvas de saturacao 2D (Vtg, Vds) incl. Vg2=-1.5V",
        "* Ordem estrita dos terminais: (d g s g1 g2) e parametro de largura W",
        ".subckt ARI d g s g1 g2 W=1.0",
        "",
        "* Referencia efetiva de fonte bilateral para pass-gates, SRAM e seguidores de fonte",
        "B_vgn  vgn  0 V = v(g)  - min(v(d), v(s))",
        "B_vg1n vg1n 0 V = v(g1) - min(v(d), v(s))",
        "B_vgp  vgp  0 V = v(g)  - max(v(d), v(s))",
        "B_vg1p vg1p 0 V = v(g1) - max(v(d), v(s))",
        "",
        "* 1) Superficie 2D de transferencia n-FET (Vds=+0.8V) em 4 planos Vg2 x 7 fatias Vg1",
    ]

    for k, g2v in enumerate(vg2_n):
        lines.append(f"B_in_p_{k} in_p_{k} 0 V = 0")
        for i, g1v in enumerate(vg1_n):
            sub = data_n[
                np.isclose(data_n[:, 0], g1v)
                & np.isclose(data_n[:, 1], g2v)
                & np.isclose(data_n[:, 3], 0.8)
            ]
            sub = sub[np.argsort(sub[:, 2])]
            xs, ys = sub[:, 2], np.maximum(sub[:, 4], 0.0)
            pts = [(-1000.0, ys[0])] + list(zip(xs, ys)) + [(1000.0, ys[-1])]
            pwl_str = ", ".join(f"{x:g}, {y:g}" for x, y in pts)
            hat_str = build_hat_pwl(vg1_n, i)
            lines.append(f"+ + (pwl(v(vg1n), {hat_str}) * pwl(v(vgn), {pwl_str}))")

    lines.append(
        "B_in_tot in_n 0 V = "
        "pwl(v(g2,s), -1000, 0, 0.0, 0.0, 0.2, 1.0, 0.4, 0.0, 1000, 0)*v(in_p_0) + "
        "pwl(v(g2,s), -1000, 0, 0.2, 0.0, 0.4, 1.0, 0.8, 0.0, 1000, 0)*v(in_p_1) + "
        "pwl(v(g2,s), -1000, 0, 0.4, 0.0, 0.8, 1.0, 1.0, 0.0, 1000, 0)*v(in_p_2) + "
        "pwl(v(g2,s), -1000, 0, 0.8, 0.0, 1.0, 1.0, 1000, 1.0)*v(in_p_3)"
    )

    lines.append("")
    lines.append("* 2) Superficie 2D de transferencia p-FET (Vds=-0.8V) em 4 planos Vg2 (incl. -1.5V) x 8 Vg1")

    sub_p_m15 = data_p[
        np.isclose(data_p[:, 0], -1.5)
        & np.isclose(data_p[:, 1], -1.5)
        & np.isclose(data_p[:, 3], -0.8)
    ]
    sub_p_m15 = sub_p_m15[np.argsort(sub_p_m15[:, 2])]
    sub_p_m12_ref = data_p[
        np.isclose(data_p[:, 0], -1.5)
        & np.isclose(data_p[:, 1], -1.2)
        & np.isclose(data_p[:, 3], -0.8)
    ]
    sub_p_m12_ref = sub_p_m12_ref[np.argsort(sub_p_m12_ref[:, 2])]
    ratio_m07 = abs(sub_p_m15[-1, 4]) / abs(np.interp(-0.7, sub_p_m12_ref[:, 2], sub_p_m12_ref[:, 4]))
    tail_m15 = sub_p_m12_ref[sub_p_m12_ref[:, 2] > -0.7]
    vtg_m15_full = np.concatenate([sub_p_m15[:, 2], tail_m15[:, 2]])
    val_m15_full = np.concatenate([np.abs(sub_p_m15[:, 4]), np.abs(tail_m15[:, 4]) * ratio_m07])
    ratios_15_12 = np.interp(sub_p_m12_ref[:, 2], vtg_m15_full, val_m15_full) / np.maximum(
        np.abs(sub_p_m12_ref[:, 4]), 1e-12
    )

    s_m05_12 = data_p[
        np.isclose(data_p[:, 0], -0.5) & np.isclose(data_p[:, 1], -1.2) & np.isclose(data_p[:, 3], -0.8)
    ]
    s_m05_11 = data_p[
        np.isclose(data_p[:, 0], -0.5) & np.isclose(data_p[:, 1], -1.1) & np.isclose(data_p[:, 3], -0.8)
    ]
    r_12_11 = float(np.max(np.abs(s_m05_12[:, 4])) / np.max(np.abs(s_m05_11[:, 4])))

    for k, g2v in enumerate(vg2_p):
        lines.append(f"B_ip_p_{k} ip_p_{k} 0 V = 0")
        for i, g1v in enumerate(vg1_p):
            if g2v == -1.5:
                if g1v == -1.5:
                    vtg_arr, val_arr = vtg_m15_full, val_m15_full
                elif g1v <= -0.5:
                    s12 = data_p[
                        np.isclose(data_p[:, 0], g1v)
                        & np.isclose(data_p[:, 1], -1.2)
                        & np.isclose(data_p[:, 3], -0.8)
                    ]
                    s12 = s12[np.argsort(s12[:, 2])]
                    vtg_arr, val_arr = s12[:, 2], np.abs(s12[:, 4]) * ratios_15_12
                else:
                    s11 = data_p[
                        np.isclose(data_p[:, 0], g1v)
                        & np.isclose(data_p[:, 1], -1.1)
                        & np.isclose(data_p[:, 3], -0.8)
                    ]
                    s11 = s11[np.argsort(s11[:, 2])]
                    vtg_arr, val_arr = s11[:, 2], np.abs(s11[:, 4]) * r_12_11 * ratios_15_12
            elif g2v == -1.2 and g1v > -0.5:
                s11 = data_p[
                    np.isclose(data_p[:, 0], g1v)
                    & np.isclose(data_p[:, 1], -1.1)
                    & np.isclose(data_p[:, 3], -0.8)
                ]
                s11 = s11[np.argsort(s11[:, 2])]
                vtg_arr, val_arr = s11[:, 2], np.abs(s11[:, 4]) * r_12_11
            else:
                sub = data_p[
                    np.isclose(data_p[:, 0], g1v)
                    & np.isclose(data_p[:, 1], g2v)
                    & np.isclose(data_p[:, 3], -0.8)
                ]
                sub = sub[np.argsort(sub[:, 2])]
                vtg_arr, val_arr = sub[:, 2], np.abs(sub[:, 4])

            pts = [(-1000.0, val_arr[0])] + list(zip(vtg_arr, val_arr)) + [(1000.0, val_arr[-1])]
            pwl_str = ", ".join(f"{x:g}, {y:g}" for x, y in pts)
            hat_str = build_hat_pwl(vg1_p, i)
            lines.append(f"+ + (pwl(v(vg1p), {hat_str}) * pwl(v(vgp), {pwl_str}))")

    lines.append(
        "B_ip_tot in_p 0 V = "
        "pwl(v(g2,s), -1000, 1.0, -1.5, 1.0, -1.2, 0.0, 1000, 0)*v(ip_p_0) + "
        "pwl(v(g2,s), -1000, 0, -1.5, 0.0, -1.2, 1.0, -1.1, 0.0, 1000, 0)*v(ip_p_1) + "
        "pwl(v(g2,s), -1000, 0, -1.2, 0.0, -1.1, 1.0, -0.9, 0.0, 1000, 0)*v(ip_p_2) + "
        "pwl(v(g2,s), -1000, 0, -1.1, 0.0, -0.9, 1.0, 0.0, 0.0, 1000, 0)*v(ip_p_3)"
    )

    lines.append("")
    lines.append("* 3) Fatores de saturacao 2D experimentais (Vtg, Vds) normalizados em |Vds|=0.8V")
    vtg_out_n = [0.1, 0.3, 0.5, 0.7, 0.9, 1.1]
    vds_n_knots = [0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10, 1.20]
    lines.append("B_fdsn_tot fds_n 0 V = 0")
    for j, vtg in enumerate(vtg_out_n):
        sub = data_n[
            np.isclose(data_n[:, 0], 1.1)
            & np.isclose(data_n[:, 1], 0.8)
            & np.isclose(data_n[:, 2], vtg)
        ]
        sub = sub[np.argsort(sub[:, 3])]
        mask_no08 = ~np.isclose(sub[:, 3], 0.80)
        vc, ic = sub[mask_no08, 3], sub[mask_no08, 4]
        i08 = float(np.interp(0.80, vc, ic))
        pts = [(0.0, 0.0)]
        for vk in vds_n_knots:
            val = max(float(np.interp(vk, vc, ic)) / i08, pts[-1][1] + 1e-4)
            pts.append((vk, val))
        slope = max(1e-3, (pts[-1][1] - pts[-2][1]) / 0.1)
        pts.append((1.50, pts[-1][1] + slope * 0.30))
        hat_str = build_hat_pwl(vtg_out_n, j)
        lines.append(f"+ + (pwl(v(vgn), {hat_str}) * pwl(v(d,s), {make_odd_pwl(pts)}))")

    vtg_out_p = [-1.5, -1.3, -1.1, -0.9, -0.7]
    vds_p_knots = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10, 1.20]
    lines.append("B_fdsp_tot fds_p 0 V = 0")
    for j, vtg in enumerate(vtg_out_p):
        sub = data_p[
            np.isclose(data_p[:, 0], -1.5)
            & np.isclose(data_p[:, 1], -1.5)
            & np.isclose(data_p[:, 2], vtg)
        ]
        sub = sub[np.argsort(sub[:, 3])]
        vc, ic = -sub[::-1, 3], np.abs(sub[::-1, 4])
        ic[0] = 0.0
        i08 = float(np.interp(0.80, vc, ic))
        pts = [(0.0, 0.0)]
        for vk in vds_p_knots:
            val = max(float(np.interp(vk, vc, ic)) / i08, pts[-1][1] + 1e-4)
            pts.append((vk, val))
        slope = max(1e-3, (pts[-1][1] - pts[-2][1]) / 0.1)
        pts.append((1.50, pts[-1][1] + slope * 0.30))
        hat_str = build_hat_pwl(vtg_out_p, j)
        lines.append(f"+ + (pwl(v(vgp), {hat_str}) * pwl(v(d,s), {make_odd_pwl(pts)}))")

    lines.extend([
        "",
        "* Fonte de corrente principal controlada pela porta de polaridade g2",
        "B_id d s I = W * ((v(g2,s) > 0.0) ? (v(in_n) * v(fds_n)) : (v(in_p) * v(fds_p)))",
        "R_gmin d s 1e12",
        ".ends ARI",
        "",
    ])

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path


def run_ngspice(sp_filename, work_dir=BASE_DIR):
    """Executa um arquivo .sp no ngspice_con.exe no diretório especificado."""
    sp_path = os.path.join(work_dir, sp_filename)
    proc = subprocess.run(
        [NGSPICE_EXE, "-b", sp_path],
        cwd=work_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout, proc.stderr


def run_characterization_suite(work_dir=BASE_DIR, lib_include="bp_ari_ngspice.lib", prefix=""):
    """Gera e executa as 5 netlists de caracterização no ngspice em `work_dir`."""
    vg1_n_list = [-0.1, 0.1, 0.3, 0.5, 0.7, 0.9, 1.1]
    vg1_p_list = [-1.5, -1.3, -1.1, -0.9, -0.7, -0.5, -0.3, -0.1]

    # 1. N Transfer (Vds=0.8V, Vg2=0.8V)
    lines_nt = [
        "* Caracterizacao n-FET Transfer (Id vs Vg para multiplos Vg1)",
        f'.include "{lib_include}"',
        "Vd d 0 DC 0.8",
        "Vs s 0 DC 0.0",
        "Vg g 0 DC 0.0",
        "Vg1 g1 0 DC 1.1",
        "Vg2 g2 0 DC 0.8",
        "X1 d g s g1 g2 ARI W=1.0",
        ".control",
        "set wr_vecnames",
        "set wr_singlescale",
    ]
    for g1v in vg1_n_list:
        tag = f"{g1v:+.1f}".replace("+", "p").replace("-", "m").replace(".", "d")
        lines_nt.append(f"alter Vg1 = {g1v}")
        lines_nt.append("dc Vg -0.8 1.1 0.05")
        lines_nt.append(f"wrdata {prefix}n_transfer_{tag}.dat -i(Vd)")
    lines_nt.extend([".endc", ".end", ""])
    with open(os.path.join(work_dir, "sim_N_transfer.sp"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines_nt))
    run_ngspice("sim_N_transfer.sp", work_dir)

    # 2. P Transfer (Vds=-0.8V, Vg2=-1.2V)
    lines_pt = [
        "* Caracterizacao p-FET Transfer (Id vs Vg para multiplos Vg1)",
        f'.include "{lib_include}"',
        "Vd d 0 DC -0.8",
        "Vs s 0 DC 0.0",
        "Vg g 0 DC 0.0",
        "Vg1 g1 0 DC -1.5",
        "Vg2 g2 0 DC -1.2",
        "X1 d g s g1 g2 ARI W=1.0",
        ".control",
        "set wr_vecnames",
        "set wr_singlescale",
    ]
    for g1v in vg1_p_list:
        tag = f"{g1v:+.1f}".replace("+", "p").replace("-", "m").replace(".", "d")
        lines_pt.append(f"alter Vg1 = {g1v}")
        lines_pt.append("dc Vg -1.5 0.0 0.05")
        lines_pt.append(f"wrdata {prefix}p_transfer_{tag}.dat -i(Vd)")
    lines_pt.extend([".endc", ".end", ""])
    with open(os.path.join(work_dir, "sim_P_transfer.sp"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines_pt))
    run_ngspice("sim_P_transfer.sp", work_dir)

    # 3. N Output (Vg1=1.1V, Vg2=0.8V)
    vg_n_out = [0.1, 0.3, 0.5, 0.7, 0.9, 1.1]
    lines_no = [
        "* Caracterizacao n-FET Output (Id vs Vds para multiplos Vg)",
        f'.include "{lib_include}"',
        "Vd d 0 DC 0.0",
        "Vs s 0 DC 0.0",
        "Vg g 0 DC 1.1",
        "Vg1 g1 0 DC 1.1",
        "Vg2 g2 0 DC 0.8",
        "X1 d g s g1 g2 ARI W=1.0",
        ".control",
        "set wr_vecnames",
        "set wr_singlescale",
    ]
    for vgv in vg_n_out:
        tag = f"{vgv:.1f}".replace(".", "d")
        lines_no.append(f"alter Vg = {vgv}")
        lines_no.append("dc Vd 0.0 1.2 0.02")
        lines_no.append(f"wrdata {prefix}n_output_vg{tag}.dat -i(Vd)")
    lines_no.extend([".endc", ".end", ""])
    with open(os.path.join(work_dir, "sim_N_output.sp"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines_no))
    run_ngspice("sim_N_output.sp", work_dir)

    # 4. P Output (Vg1=-1.5V, Vg2=-1.5V -> identico a ari_P_output.sp no HSPICE!)
    vg_p_out = [-1.5, -1.3, -1.1, -0.9, -0.7]
    lines_po = [
        "* Caracterizacao p-FET Output (Id vs Vds para multiplos Vg, Vg1=-1.5V, Vg2=-1.5V)",
        f'.include "{lib_include}"',
        "Vd d 0 DC 0.0",
        "Vs s 0 DC 0.0",
        "Vg g 0 DC -1.5",
        "Vg1 g1 0 DC -1.5",
        "Vg2 g2 0 DC -1.5",
        "X1 d g s g1 g2 ARI W=1.0",
        ".control",
        "set wr_vecnames",
        "set wr_singlescale",
    ]
    for vgv in vg_p_out:
        tag = f"{vgv:+.1f}".replace("-", "m").replace(".", "d")
        lines_po.append(f"alter Vg = {vgv}")
        lines_po.append("dc Vd -1.2 0.0 0.02")
        lines_po.append(f"wrdata {prefix}p_output_vg{tag}.dat -i(Vd)")
    lines_po.extend([".endc", ".end", ""])
    with open(os.path.join(work_dir, "sim_P_output.sp"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines_po))
    run_ngspice("sim_P_output.sp", work_dir)

    if prefix == "":
        # 5. Varredura de Vg2 (Porta de Polaridade)
        lines_pg = [
            "* Efeito da Porta de Polaridade Vg2 em modo n-FET e p-FET",
            f'.include "{lib_include}"',
            "Vd d 0 DC 0.8",
            "Vs s 0 DC 0.0",
            "Vg g 0 DC 0.0",
            "Vg1 g1 0 DC 1.1",
            "Vg2 g2 0 DC 0.8",
            "X1 d g s g1 g2 ARI W=1.0",
            ".control",
            "set wr_vecnames",
            "set wr_singlescale",
        ]
        for vg2v in [0.2, 0.4, 0.8, 1.0]:
            tag = f"{vg2v:.1f}".replace(".", "d")
            lines_pg.append(f"alter Vg2 = {vg2v}")
            lines_pg.append("dc Vg -0.8 1.1 0.05")
            lines_pg.append(f"wrdata n_vg2_{tag}.dat -i(Vd)")
        lines_pg.extend(["alter Vd = -0.8", "alter Vg1 = -1.5"])
        for vg2v in [-0.9, -1.1, -1.2, -1.5]:
            tag = f"{vg2v:.1f}".replace("-", "m").replace(".", "d")
            lines_pg.append(f"alter Vg2 = {vg2v}")
            lines_pg.append("dc Vg -1.5 0.0 0.05")
            lines_pg.append(f"wrdata p_vg2_{tag}.dat -i(Vd)")
        lines_pg.extend([".endc", ".end", ""])
        with open(os.path.join(work_dir, "sim_polarity_gate.sp"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines_pg))
        run_ngspice("sim_polarity_gate.sp", work_dir)


def read_wrdata(filename, work_dir=BASE_DIR):
    """Lê arquivo gerado por wrdata do ngspice (pula cabeçalho textual)."""
    return np.loadtxt(os.path.join(work_dir, filename), skiprows=1)


def parse_hspice_printtr0(path):
    """Faz o parsing dos arquivos .printtr0 gerados pelo HSPICE original."""
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    blocks = []
    cur_param = None
    in_data = False
    cols = []
    rows = []
    suf = {"m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15, "k": 1e3}

    def pnum(tok):
        return float(tok[:-1]) * suf[tok[-1].lower()] if tok[-1].lower() in suf else float(tok)

    for line in lines:
        s = line.strip()
        m = re.search(r"0:(vg1|vg)\s*=\s*([-\d.eE+]+)", s)
        if m:
            if cur_param is not None and rows:
                blocks.append((cur_param, np.array(rows)))
            cur_param, in_data, cols, rows = float(m.group(2)), False, [], []
            continue
        if s == "x":
            in_data = True
            continue
        if s == "y":
            if cur_param is not None and rows:
                blocks.append((cur_param, np.array(rows)))
                rows = []
            in_data = False
            continue
        if in_data and s:
            parts = s.split()
            if not cols and any(c.isalpha() for c in parts[0]):
                cols = parts
                continue
            if parts[0][0].isdigit() or parts[0][0] == "-":
                try:
                    rows.append([pnum(p) for p in parts])
                except Exception:
                    pass
    if cur_param is not None and rows:
        blocks.append((cur_param, np.array(rows)))
    return blocks


def compute_ss_mv_dec(vg, abs_id):
    """Calcula a menor inclinação de sublimiar (Subthreshold Swing) em mV/dec."""
    mask = abs_id > 1e-11
    vg_m = vg[mask]
    log_id = np.log10(abs_id[mask])
    best_ss = np.inf
    for i in range(len(vg_m) - 2):
        dv = abs(vg_m[i + 2] - vg_m[i])
        dlog = abs(log_id[i + 2] - log_id[i])
        if dlog > 0.25:
            ss = (dv / dlog) * 1000.0
            if 55.0 < ss < best_ss:
                best_ss = ss
    return best_ss


def compute_fit_metrics(y_pred, y_ref):
    """Retorna RMSE (uA), MAE (uA), MaxErr (uA) e R^2."""
    diff = y_pred - y_ref
    rmse_ua = float(np.sqrt(np.mean(diff**2)) * 1e6)
    mae_ua = float(np.mean(np.abs(diff)) * 1e6)
    max_ua = float(np.max(np.abs(diff)) * 1e6)
    ss_res = float(np.sum(diff**2))
    ss_tot = float(np.sum((y_ref - np.mean(y_ref)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-30 else 1.0
    return rmse_ua, mae_ua, max_ua, r2


def run_hspice_cross_validation(data_n, data_p):
    """Executa validação cruzada v1 vs. v2 contra os resultados oficiais HSPICE (.printtr0)."""
    tmp_v1 = os.path.join(BASE_DIR, "_tmp_v1_cv")
    os.makedirs(tmp_v1, exist_ok=True)
    try:
        v1_lib = os.path.join(tmp_v1, "bp_ari_v1.lib")
        generate_ngspice_library_v1(data_n, data_p, v1_lib)
        run_characterization_suite(work_dir=tmp_v1, lib_include="bp_ari_v1.lib", prefix="v1_")

        rows = []

        # 1) N_transfer (-0.1 .. +1.1 V)
        nt_h = parse_hspice_printtr0(os.path.join(DATA_DIR, "results_ari_N_transfer.printtr0"))
        y_all_ref, y_all_v1, y_all_v2 = [], [], []
        for g1v, arr in nt_h:
            tag = f"{g1v:+.1f}".replace("+", "p").replace("-", "m").replace(".", "d")
            s1 = read_wrdata(f"v1_n_transfer_{tag}.dat", tmp_v1)
            s2 = read_wrdata(f"n_transfer_{tag}.dat", BASE_DIR)
            vh, ih = arr[:, 1], -arr[:, 2]
            i1 = np.interp(vh, s1[:, 0], s1[:, 1])
            i2 = np.interp(vh, s2[:, 0], s2[:, 1])
            y_all_ref.append(ih); y_all_v1.append(i1); y_all_v2.append(i2)
            r1 = compute_fit_metrics(i1, ih)
            r2 = compute_fit_metrics(i2, ih)
            rows.append({
                "Regime": "N_transfer", "Curva": f"Vg1={g1v:+.1f}V",
                "RMSE_v1_uA": r1[0], "RMSE_v2_uA": r2[0],
                "MAE_v1_uA": r1[1], "MAE_v2_uA": r2[1],
                "MaxErr_v1_uA": r1[2], "MaxErr_v2_uA": r2[2],
                "R2_v1": r1[3], "R2_v2": r2[3],
            })
        r1g = compute_fit_metrics(np.concatenate(y_all_v1), np.concatenate(y_all_ref))
        r2g = compute_fit_metrics(np.concatenate(y_all_v2), np.concatenate(y_all_ref))
        rows.append({
            "Regime": "N_transfer", "Curva": "AGREGADO (7 curvas)",
            "RMSE_v1_uA": r1g[0], "RMSE_v2_uA": r2g[0],
            "MAE_v1_uA": r1g[1], "MAE_v2_uA": r2g[1],
            "MaxErr_v1_uA": r1g[2], "MaxErr_v2_uA": r2g[2],
            "R2_v1": r1g[3], "R2_v2": r2g[3],
        })

        # 2) P_transfer (-1.1 .. -0.5 V medidos em Vg2=-1.2V)
        pt_h = parse_hspice_printtr0(os.path.join(DATA_DIR, "results_ari_P_transfer.printtr0"))
        y_all_ref, y_all_v1, y_all_v2 = [], [], []
        for g1v, arr in pt_h:
            if g1v > -0.45:
                continue
            tag = f"{g1v:+.1f}".replace("+", "p").replace("-", "m").replace(".", "d")
            s1 = read_wrdata(f"v1_p_transfer_{tag}.dat", tmp_v1)
            s2 = read_wrdata(f"p_transfer_{tag}.dat", BASE_DIR)
            vh, ih = arr[:, 1], -arr[:, 2]
            i1 = np.interp(vh, s1[:, 0], s1[:, 1])
            i2 = np.interp(vh, s2[:, 0], s2[:, 1])
            y_all_ref.append(ih); y_all_v1.append(i1); y_all_v2.append(i2)
            r1 = compute_fit_metrics(i1, ih)
            r2 = compute_fit_metrics(i2, ih)
            rows.append({
                "Regime": "P_transfer", "Curva": f"Vg1={g1v:+.1f}V",
                "RMSE_v1_uA": r1[0], "RMSE_v2_uA": r2[0],
                "MAE_v1_uA": r1[1], "MAE_v2_uA": r2[1],
                "MaxErr_v1_uA": r1[2], "MaxErr_v2_uA": r2[2],
                "R2_v1": r1[3], "R2_v2": r2[3],
            })
        r1g = compute_fit_metrics(np.concatenate(y_all_v1), np.concatenate(y_all_ref))
        r2g = compute_fit_metrics(np.concatenate(y_all_v2), np.concatenate(y_all_ref))
        rows.append({
            "Regime": "P_transfer", "Curva": "AGREGADO (4 curvas Vg2=-1.2V)",
            "RMSE_v1_uA": r1g[0], "RMSE_v2_uA": r2g[0],
            "MAE_v1_uA": r1g[1], "MAE_v2_uA": r2g[1],
            "MaxErr_v1_uA": r1g[2], "MaxErr_v2_uA": r2g[2],
            "R2_v1": r1g[3], "R2_v2": r2g[3],
        })

        # 3) N_output (Vg=0.1..1.1V, Vd=[0, 1.2V])
        no_h = parse_hspice_printtr0(os.path.join(DATA_DIR, "results_ari_N_output.printtr0"))
        y_all_ref, y_all_v1, y_all_v2 = [], [], []
        n_out_curves = {}
        for vgv, arr in no_h:
            tag = f"{vgv:.1f}".replace(".", "d")
            s1 = read_wrdata(f"v1_n_output_vg{tag}.dat", tmp_v1)
            s2 = read_wrdata(f"n_output_vg{tag}.dat", BASE_DIR)
            vd_h = -1.5 + (3.0 / 4e-9) * arr[:, 0]
            id_h = -arr[:, 2]
            m = (vd_h >= 0.0) & (vd_h <= 1.2)
            vh, ih = vd_h[m], id_h[m]
            i1 = np.interp(vh, s1[:, 0], s1[:, 1])
            i2 = np.interp(vh, s2[:, 0], s2[:, 1])
            y_all_ref.append(ih); y_all_v1.append(i1); y_all_v2.append(i2)
            n_out_curves[vgv] = (vh, ih, s1, s2)
            r1 = compute_fit_metrics(i1, ih)
            r2 = compute_fit_metrics(i2, ih)
            rows.append({
                "Regime": "N_output", "Curva": f"Vg={vgv:+.1f}V",
                "RMSE_v1_uA": r1[0], "RMSE_v2_uA": r2[0],
                "MAE_v1_uA": r1[1], "MAE_v2_uA": r2[1],
                "MaxErr_v1_uA": r1[2], "MaxErr_v2_uA": r2[2],
                "R2_v1": r1[3], "R2_v2": r2[3],
            })
        r1g = compute_fit_metrics(np.concatenate(y_all_v1), np.concatenate(y_all_ref))
        r2g = compute_fit_metrics(np.concatenate(y_all_v2), np.concatenate(y_all_ref))
        rows.append({
            "Regime": "N_output", "Curva": "AGREGADO (6 curvas)",
            "RMSE_v1_uA": r1g[0], "RMSE_v2_uA": r2g[0],
            "MAE_v1_uA": r1g[1], "MAE_v2_uA": r2g[1],
            "MaxErr_v1_uA": r1g[2], "MaxErr_v2_uA": r2g[2],
            "R2_v1": r1g[3], "R2_v2": r2g[3],
        })

        # 4) P_output (Vg=-1.1..-0.7V, Vg2=-1.5V, Vd=[-1.2, 0.0V])
        po_h = parse_hspice_printtr0(os.path.join(DATA_DIR, "results_ari_P_output.printtr0"))
        y_all_ref, y_all_v1, y_all_v2 = [], [], []
        p_out_curves = {}
        for vgv, arr in po_h:
            if vgv > -0.65:
                continue
            tag = f"{vgv:+.1f}".replace("-", "m").replace(".", "d")
            s1 = read_wrdata(f"v1_p_output_vg{tag}.dat", tmp_v1)
            s2 = read_wrdata(f"p_output_vg{tag}.dat", BASE_DIR)
            vd_h = -1.5 + (3.0 / 4e-9) * arr[:, 0]
            id_h = -arr[:, 2]
            m = (vd_h >= -1.2) & (vd_h <= 0.0)
            vh, ih = vd_h[m], id_h[m]
            i1 = np.interp(vh, s1[:, 0], s1[:, 1])
            i2 = np.interp(vh, s2[:, 0], s2[:, 1])
            y_all_ref.append(ih); y_all_v1.append(i1); y_all_v2.append(i2)
            p_out_curves[vgv] = (vh, ih, s1, s2)
            r1 = compute_fit_metrics(i1, ih)
            r2 = compute_fit_metrics(i2, ih)
            rows.append({
                "Regime": "P_output", "Curva": f"Vg={vgv:+.1f}V",
                "RMSE_v1_uA": r1[0], "RMSE_v2_uA": r2[0],
                "MAE_v1_uA": r1[1], "MAE_v2_uA": r2[1],
                "MaxErr_v1_uA": r1[2], "MaxErr_v2_uA": r2[2],
                "R2_v1": r1[3], "R2_v2": r2[3],
            })
        r1g = compute_fit_metrics(np.concatenate(y_all_v1), np.concatenate(y_all_ref))
        r2g = compute_fit_metrics(np.concatenate(y_all_v2), np.concatenate(y_all_ref))
        rows.append({
            "Regime": "P_output", "Curva": "AGREGADO (3 curvas Vg2=-1.5V)",
            "RMSE_v1_uA": r1g[0], "RMSE_v2_uA": r2g[0],
            "MAE_v1_uA": r1g[1], "MAE_v2_uA": r2g[1],
            "MaxErr_v1_uA": r1g[2], "MaxErr_v2_uA": r2g[2],
            "R2_v1": r1g[3], "R2_v2": r2g[3],
        })

        df_cv = pd.DataFrame(rows)
        df_cv.to_csv(os.path.join(BASE_DIR, "validacao_cruzada_hspice.csv"), index=False)

        # --- Figura 4: Validacao Cruzada Quantitativa vs. HSPICE (.printtr0) ---
        plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})
        fig, axes = plt.subplots(2, 2, figsize=(13, 9.5))

        # Painel A: P_output HSPICE vs v1 vs v2
        colors_p = ["#99000d", "#ef3b2c", "#fb6a4a"]
        for idx_c, vgv in enumerate([-1.1, -0.9, -0.7]):
            vh, ih, s1, s2 = p_out_curves[vgv]
            col = colors_p[idx_c]
            axes[0, 0].plot(vh[::40], np.abs(ih[::40]) * 1e6, "o", color=col, ms=3.8, alpha=0.85, label=f"HSPICE $V_g={vgv:+.1f}\\,\\mathrm{{V}}$" if idx_c == 0 else None)
            axes[0, 0].plot(s1[:, 0], np.abs(s1[:, 1]) * 1e6, "--", color=col, lw=1.4, alpha=0.75, label="v1 (1D + tanh)" if idx_c == 0 else None)
            axes[0, 0].plot(s2[:, 0], np.abs(s2[:, 1]) * 1e6, "-", color=col, lw=2.2, label=f"v2 4D ($V_g={vgv:+.1f}\\,\\mathrm{{V}}$)")
        axes[0, 0].set_title("Saída p-FET ($V_{g2}=-1,5\\,\\mathrm{V}$): HSPICE vs. v1 vs. v2")
        axes[0, 0].set_xlabel("$V_{ds}\\ (\\mathrm{V})$")
        axes[0, 0].set_ylabel("$|I_d|\\ (\\mu\\mathrm{A}/\\mu\\mathrm{m})$")
        axes[0, 0].legend(fontsize=7.8, ncol=2)

        # Painel B: N_output HSPICE vs v1 vs v2
        colors_n = ["#08306b", "#2171b5", "#6baed6"]
        for idx_c, vgv in enumerate([1.1, 0.7, 0.3]):
            vh, ih, s1, s2 = n_out_curves[vgv]
            col = colors_n[idx_c]
            axes[0, 1].plot(vh[::40], ih[::40] * 1e6, "o", color=col, ms=3.8, alpha=0.85, label=f"HSPICE $V_g={vgv:.1f}\\,\\mathrm{{V}}$" if idx_c == 0 else None)
            axes[0, 1].plot(s1[:, 0], s1[:, 1] * 1e6, "--", color=col, lw=1.4, alpha=0.75, label="v1 (1D + tanh)" if idx_c == 0 else None)
            axes[0, 1].plot(s2[:, 0], s2[:, 1] * 1e6, "-", color=col, lw=2.2, label=f"v2 4D ($V_g={vgv:.1f}\\,\\mathrm{{V}}$)")
        axes[0, 1].set_title("Saída n-FET ($V_{g2}=+0,8\\,\\mathrm{V}$): HSPICE vs. v1 vs. v2")
        axes[0, 1].set_xlabel("$V_{ds}\\ (\\mathrm{V})$")
        axes[0, 1].set_ylabel("$I_d\\ (\\mu\\mathrm{A}/\\mu\\mathrm{m})$")
        axes[0, 1].legend(fontsize=7.8, ncol=2)

        # Painel C: N_transfer e P_transfer Paridade Ngspice v2 vs. HSPICE
        nt_ref, nt_v2 = [], []
        for g1v, arr in nt_h:
            tag = f"{g1v:+.1f}".replace("+", "p").replace("-", "m").replace(".", "d")
            s2 = read_wrdata(f"n_transfer_{tag}.dat", BASE_DIR)
            nt_ref.append((-arr[::80, 2]) * 1e6)
            nt_v2.append(np.interp(arr[::80, 1], s2[:, 0], s2[:, 1]) * 1e6)
        pt_ref, pt_v2 = [], []
        for g1v, arr in pt_h:
            if g1v > -0.45:
                continue
            tag = f"{g1v:+.1f}".replace("+", "p").replace("-", "m").replace(".", "d")
            s2 = read_wrdata(f"p_transfer_{tag}.dat", BASE_DIR)
            pt_ref.append((arr[::80, 2]) * 1e6)
            pt_v2.append(np.interp(arr[::80, 1], s2[:, 0], np.abs(s2[:, 1])) * 1e6)
        nt_r, nt_p = np.concatenate(nt_ref), np.concatenate(nt_v2)
        pt_r, pt_p = np.concatenate(pt_ref), np.concatenate(pt_v2)
        axes[1, 0].scatter(nt_r, nt_p, s=16, alpha=0.8, color="#2171b5", label="N_transfer (7 curvas $V_{g1}$)")
        axes[1, 0].scatter(pt_r, pt_p, s=16, alpha=0.8, color="#cb181d", label="P_transfer (4 curvas $V_{g1}$)")
        lim = 1.75
        axes[1, 0].plot([0, lim], [0, lim], "k--", lw=1.2, label="Identidade ($y = x$)")
        axes[1, 0].set_title("Paridade de Transferência: Ngspice v2 vs. HSPICE (.printtr0)")
        axes[1, 0].set_xlabel("$|I_d|$ HSPICE ($\\mu\\mathrm{A}/\\mu\\mathrm{m}$)")
        axes[1, 0].set_ylabel("$|I_d|$ Ngspice v2 ($\\mu\\mathrm{A}/\\mu\\mathrm{m}$)")
        axes[1, 0].set_xlim(-0.05, lim)
        axes[1, 0].set_ylim(-0.05, lim)
        axes[1, 0].legend(fontsize=8.5)

        # Painel D: Comparacao Agregada RMSE (v1 vs v2 contra HSPICE)
        agg = df_cv[df_cv["Curva"].str.startswith("AGREGADO")].copy()
        x_pos = np.arange(len(agg))
        w_bar = 0.34
        b1 = axes[1, 1].bar(x_pos - w_bar / 2, agg["RMSE_v1_uA"], width=w_bar, color="#fcae91", edgecolor="#cb181d", label="Modelo v1 (1D + tanh)")
        b2 = axes[1, 1].bar(x_pos + w_bar / 2, agg["RMSE_v2_uA"], width=w_bar, color="#6baed6", edgecolor="#08519c", label="Modelo v2 (Superfície 4D)")
        axes[1, 1].set_xticks(x_pos)
        axes[1, 1].set_xticklabels(agg["Regime"])
        axes[1, 1].set_ylabel("RMSE Global vs. HSPICE ($\\mu\\mathrm{A}/\\mu\\mathrm{m}$)")
        axes[1, 1].set_title("Redução do Erro Global (RMSE vs. HSPICE .printtr0)")
        axes[1, 1].legend(fontsize=8.5)
        for rect in b1:
            h = rect.get_height()
            axes[1, 1].text(rect.get_x() + rect.get_width() / 2, h + 0.008, f"{h:.4f}", ha="center", va="bottom", fontsize=7.5)
        for rect in b2:
            h = rect.get_height()
            axes[1, 1].text(rect.get_x() + rect.get_width() / 2, h + 0.008, f"{h:.4f}", ha="center", va="bottom", fontsize=7.5, fontweight="bold")
        axes[1, 1].set_ylim(0, float(agg["RMSE_v1_uA"].max()) * 1.22)

        fig.suptitle("Validação Cruzada Quantitativa: Ngspice v1 vs. v2 (4D Refinado) vs. HSPICE Original", fontsize=13, fontweight="bold")
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        fig.savefig(os.path.join(BASE_DIR, "fig4_validacao_cruzada_hspice.png"), dpi=200)
        plt.close(fig)

        print("\n=== Validação Cruzada Agregada vs. HSPICE (.printtr0) ===")
        print(agg[["Regime", "RMSE_v1_uA", "RMSE_v2_uA", "MaxErr_v1_uA", "MaxErr_v2_uA", "R2_v1", "R2_v2"]].to_string(index=False))
    finally:
        shutil.rmtree(tmp_v1, ignore_errors=True)


def compute_metrics_and_plots(data_n, data_p):
    """Calcula todas as métricas e gera as 3 figuras de caracterização do dispositivo."""
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})

    vg1_n_list = [-0.1, 0.1, 0.3, 0.5, 0.7, 0.9, 1.1]
    vg1_p_list = [-1.5, -1.3, -1.1, -0.9, -0.7, -0.5, -0.3, -0.1]

    s_m05_12 = data_p[np.isclose(data_p[:, 0], -0.5) & np.isclose(data_p[:, 1], -1.2) & np.isclose(data_p[:, 3], -0.8)]
    s_m05_11 = data_p[np.isclose(data_p[:, 0], -0.5) & np.isclose(data_p[:, 1], -1.1) & np.isclose(data_p[:, 3], -0.8)]
    r_12_11 = float(np.max(np.abs(s_m05_12[:, 4])) / np.max(np.abs(s_m05_11[:, 4])))

    # --- Figura 1: Transferência N e P (Linear e Log) ---
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    colors_n = plt.cm.Blues(np.linspace(0.35, 0.95, len(vg1_n_list)))
    colors_p = plt.cm.Reds(np.linspace(0.35, 0.95, len(vg1_p_list)))

    n_rel_errors = []
    for i, g1v in enumerate(vg1_n_list):
        tag = f"{g1v:+.1f}".replace("+", "p").replace("-", "m").replace(".", "d")
        sim = read_wrdata(f"n_transfer_{tag}.dat")
        ref = data_n[np.isclose(data_n[:, 0], g1v) & np.isclose(data_n[:, 1], 0.8) & np.isclose(data_n[:, 3], 0.8)]
        ref = ref[np.argsort(ref[:, 2])]
        sim_interp = np.interp(ref[:, 2], sim[:, 0], sim[:, 1])
        mask_on = ref[:, 4] > 1e-8
        if np.any(mask_on):
            rel_err = np.mean(np.abs(sim_interp[mask_on] - ref[mask_on, 4]) / ref[mask_on, 4]) * 100.0
            n_rel_errors.append(rel_err)
        lbl = f"$V_{{g1}}={g1v:.1f}\\,\\mathrm{{V}}$"
        axes[0, 0].plot(sim[:, 0], sim[:, 1] * 1e6, color=colors_n[i], lw=1.8, label=lbl)
        axes[0, 0].scatter(ref[::2, 2], ref[::2, 4] * 1e6, color=colors_n[i], s=14, alpha=0.8)
        axes[1, 0].semilogy(sim[:, 0], np.maximum(np.abs(sim[:, 1]), 1e-12), color=colors_n[i], lw=1.8, label=lbl)
        axes[1, 0].scatter(ref[::2, 2], np.abs(ref[::2, 4]), color=colors_n[i], s=14, alpha=0.8)

    p_rel_errors = []
    for i, g1v in enumerate(vg1_p_list):
        tag = f"{g1v:+.1f}".replace("+", "p").replace("-", "m").replace(".", "d")
        sim = read_wrdata(f"p_transfer_{tag}.dat")
        vg2_ref = -1.2 if g1v <= -0.5 else -1.1
        scale = 1.0 if g1v <= -0.5 else r_12_11
        ref = data_p[np.isclose(data_p[:, 0], g1v) & np.isclose(data_p[:, 1], vg2_ref) & np.isclose(data_p[:, 3], -0.8)]
        ref = ref[np.argsort(ref[:, 2])]
        sim_interp = np.interp(ref[:, 2], sim[:, 0], np.abs(sim[:, 1]))
        ref_abs = np.abs(ref[:, 4]) * scale
        mask_on = ref_abs > 1e-8
        if np.any(mask_on):
            rel_err = np.mean(np.abs(sim_interp[mask_on] - ref_abs[mask_on]) / ref_abs[mask_on]) * 100.0
            p_rel_errors.append(rel_err)
        lbl = f"$V_{{g1}}={g1v:.1f}\\,\\mathrm{{V}}$"
        axes[0, 1].plot(sim[:, 0], np.abs(sim[:, 1]) * 1e6, color=colors_p[i], lw=1.8, label=lbl)
        axes[0, 1].scatter(ref[::2, 2], ref_abs[::2] * 1e6, color=colors_p[i], s=14, alpha=0.8)
        axes[1, 1].semilogy(sim[:, 0], np.maximum(np.abs(sim[:, 1]), 1e-12), color=colors_p[i], lw=1.8, label=lbl)
        axes[1, 1].scatter(ref[::2, 2], ref_abs[::2], color=colors_p[i], s=14, alpha=0.8)

    axes[0, 0].set_title("Modo n-FET ($V_{ds}=+0,8\\,\\mathrm{V},\\ V_{g2}=+0,8\\,\\mathrm{V}$) — Linear")
    axes[0, 0].set_xlabel("$V_g\\ (\\mathrm{V})$")
    axes[0, 0].set_ylabel("$I_d\\ (\\mu\\mathrm{A}/\\mu\\mathrm{m})$")
    axes[0, 0].legend(fontsize=7.5, ncol=2)

    axes[1, 0].set_title("Modo n-FET — Escala Log (Ngspice v2 vs. Tabela)")
    axes[1, 0].set_xlabel("$V_g\\ (\\mathrm{V})$")
    axes[1, 0].set_ylabel("$|I_d|\\ (\\mathrm{A}/\\mu\\mathrm{m})$")
    axes[1, 0].set_ylim(1e-10, 1e-5)

    axes[0, 1].set_title("Modo p-FET ($V_{ds}=-0,8\\,\\mathrm{V},\\ V_{g2}=-1,2\\,\\mathrm{V}$) — Linear")
    axes[0, 1].set_xlabel("$V_g\\ (\\mathrm{V})$")
    axes[0, 1].set_ylabel("$|I_d|\\ (\\mu\\mathrm{A}/\\mu\\mathrm{m})$")
    axes[0, 1].legend(fontsize=7.5, ncol=2)

    axes[1, 1].set_title("Modo p-FET — Escala Log (Ngspice v2 vs. Tabela)")
    axes[1, 1].set_xlabel("$V_g\\ (\\mathrm{V})$")
    axes[1, 1].set_ylabel("$|I_d|\\ (\\mathrm{A}/\\mu\\mathrm{m})$")
    axes[1, 1].set_ylim(1e-10, 1e-5)

    fig.suptitle("Caracterização de Transferência BP SB-FET: Dados Experimentais vs. Modelo Ngspice v2 (4D)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(BASE_DIR, "fig1_transfer_NP_log_lin.png"), dpi=200)
    plt.close(fig)

    # --- Figura 2: Saída N e P ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    vg_n_out = [0.1, 0.3, 0.5, 0.7, 0.9, 1.1]
    colors_no = plt.cm.viridis(np.linspace(0.15, 0.9, len(vg_n_out)))
    for i, vgv in enumerate(vg_n_out):
        tag = f"{vgv:.1f}".replace(".", "d")
        sim = read_wrdata(f"n_output_vg{tag}.dat")
        ref = data_n[np.isclose(data_n[:, 0], 1.1) & np.isclose(data_n[:, 1], 0.8) & np.isclose(data_n[:, 2], vgv)]
        ref = ref[np.argsort(ref[:, 3])]
        axes[0].plot(sim[:, 0], sim[:, 1] * 1e6, color=colors_no[i], lw=2.0, label=f"$V_g={vgv:.1f}\\,\\mathrm{{V}}$")
        axes[0].scatter(ref[::8, 3], ref[::8, 4] * 1e6, color=colors_no[i], s=18, marker="o", alpha=0.8)

    vg_p_out = [-1.5, -1.3, -1.1, -0.9, -0.7]
    colors_po = plt.cm.plasma(np.linspace(0.15, 0.85, len(vg_p_out)))
    for i, vgv in enumerate(vg_p_out):
        tag = f"{vgv:+.1f}".replace("-", "m").replace(".", "d")
        sim = read_wrdata(f"p_output_vg{tag}.dat")
        ref = data_p[np.isclose(data_p[:, 0], -1.5) & np.isclose(data_p[:, 1], -1.5) & np.isclose(data_p[:, 2], vgv)]
        ref = ref[np.argsort(ref[:, 3])]
        axes[1].plot(sim[:, 0], sim[:, 1] * 1e6, color=colors_po[i], lw=2.0, label=f"$V_g={vgv:.1f}\\,\\mathrm{{V}}$")
        axes[1].scatter(ref[::2, 3], ref[::2, 4] * 1e6, color=colors_po[i], s=18, marker="o", alpha=0.8)

    axes[0].set_title("Curvas de Saída n-FET ($V_{g1}=+1,1\\,\\mathrm{V},\\ V_{g2}=+0,8\\,\\mathrm{V}$)")
    axes[0].set_xlabel("$V_{ds}\\ (\\mathrm{V})$")
    axes[0].set_ylabel("$I_d\\ (\\mu\\mathrm{A}/\\mu\\mathrm{m})$")
    axes[0].legend(fontsize=8.5)

    axes[1].set_title("Curvas de Saída p-FET ($V_{g1}=-1,5\\,\\mathrm{V},\\ V_{g2}=-1,5\\,\\mathrm{V}$)")
    axes[1].set_xlabel("$V_{ds}\\ (\\mathrm{V})$")
    axes[1].set_ylabel("$I_d\\ (\\mu\\mathrm{A}/\\mu\\mathrm{m})$")
    axes[1].legend(fontsize=8.5)

    fig.suptitle("Curvas Características de Saída ($I_d \\times V_{ds}$): Ngspice v2 (4D) vs. LUT", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(BASE_DIR, "fig2_output_NP.png"), dpi=200)
    plt.close(fig)

    # --- Figura 3: Efeito da Porta de Polaridade Vg2 ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for vg2v, col in zip([0.2, 0.4, 0.8, 1.0], ["#9ecae1", "#4292c6", "#08519c", "#08306b"]):
        tag = f"{vg2v:.1f}".replace(".", "d")
        sim = read_wrdata(f"n_vg2_{tag}.dat")
        ref = data_n[np.isclose(data_n[:, 0], 1.1) & np.isclose(data_n[:, 1], vg2v) & np.isclose(data_n[:, 3], 0.8)]
        ref = ref[np.argsort(ref[:, 2])]
        axes[0].semilogy(sim[:, 0], np.maximum(np.abs(sim[:, 1]), 1e-12), color=col, lw=2.0, label=f"Ngspice v2 $V_{{g2}}={vg2v:.1f}\\,\\mathrm{{V}}$")
        axes[0].scatter(ref[::2, 2], np.abs(ref[::2, 4]), color=col, s=16, alpha=0.8)

    for vg2v, col in zip([-0.9, -1.1, -1.2, -1.5], ["#fc9272", "#ef3b2c", "#cb181d", "#67000d"]):
        tag = f"{vg2v:.1f}".replace("-", "m").replace(".", "d")
        sim = read_wrdata(f"p_vg2_{tag}.dat")
        ref = data_p[np.isclose(data_p[:, 0], -1.5) & np.isclose(data_p[:, 1], vg2v) & np.isclose(data_p[:, 3], -0.8)]
        ref = ref[np.argsort(ref[:, 2])]
        step = 1 if vg2v == -1.5 else 2
        axes[1].semilogy(sim[:, 0], np.maximum(np.abs(sim[:, 1]), 1e-12), color=col, lw=2.0, label=f"Ngspice v2 $V_{{g2}}={vg2v:.1f}\\,\\mathrm{{V}}$")
        axes[1].scatter(ref[::step, 2], np.abs(ref[::step, 4]), color=col, s=18, alpha=0.85)

    axes[0].set_title("Modulação da Porta de Polaridade $V_{g2}$ (Modo n-FET)")
    axes[0].set_xlabel("$V_g\\ (\\mathrm{V})$")
    axes[0].set_ylabel("$|I_d|\\ (\\mathrm{A}/\\mu\\mathrm{m})$")
    axes[0].set_ylim(1e-10, 1e-5)
    axes[0].legend(fontsize=8.2)

    axes[1].set_title("Modulação da Porta de Polaridade $V_{g2}$ (Modo p-FET)")
    axes[1].set_xlabel("$V_g\\ (\\mathrm{V})$")
    axes[1].set_ylabel("$|I_d|\\ (\\mathrm{A}/\\mu\\mathrm{m})$")
    axes[1].set_ylim(1e-10, 1e-5)
    axes[1].legend(fontsize=8.2)

    fig.suptitle("Controle Eletrostático da Barreira Schottky via Porta de Polaridade ($V_{g2}$)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(BASE_DIR, "fig3_efeito_porta_polaridade.png"), dpi=200)
    plt.close(fig)

    # --- Métricas Quantitativas ---
    sim_n_nom = read_wrdata("n_transfer_p0d9.dat")
    sim_n_max = read_wrdata("n_transfer_p1d1.dat")
    sim_p_nom = read_wrdata("p_transfer_m1d5.dat")

    ss_n_nom = compute_ss_mv_dec(sim_n_nom[:, 0], np.abs(sim_n_nom[:, 1]))
    ss_n_max = compute_ss_mv_dec(sim_n_max[:, 0], np.abs(sim_n_max[:, 1]))
    ss_p_nom = compute_ss_mv_dec(sim_p_nom[:, 0], np.abs(sim_p_nom[:, 1]))

    ion_n = float(np.max(sim_n_max[:, 1]))
    ioff_n = float(np.min(np.abs(sim_n_max[:, 1])))
    ion_p = float(np.max(np.abs(sim_p_nom[:, 1])))
    ioff_p = float(np.min(np.abs(sim_p_nom[:, 1])))

    metrics = [
        {"Modo": "n-FET (Vg1=1.1V, Vg2=0.8V)", "Ion_uA_um": ion_n * 1e6, "Ioff_nA_um": ioff_n * 1e9, "Ion_Ioff_ratio": ion_n / ioff_n, "SS_min_mV_dec": ss_n_max, "Erro_Medio_LUT_pct": float(np.mean(n_rel_errors))},
        {"Modo": "n-FET (Vg1=0.9V, Vg2=0.8V)", "Ion_uA_um": float(np.max(sim_n_nom[:, 1])) * 1e6, "Ioff_nA_um": float(np.min(np.abs(sim_n_nom[:, 1]))) * 1e9, "Ion_Ioff_ratio": float(np.max(sim_n_nom[:, 1])) / float(np.min(np.abs(sim_n_nom[:, 1]))), "SS_min_mV_dec": ss_n_nom, "Erro_Medio_LUT_pct": float(np.mean(n_rel_errors))},
        {"Modo": "p-FET (Vg1=-1.5V, Vg2=-1.2V)", "Ion_uA_um": ion_p * 1e6, "Ioff_nA_um": ioff_p * 1e9, "Ion_Ioff_ratio": ion_p / ioff_p, "SS_min_mV_dec": ss_p_nom, "Erro_Medio_LUT_pct": float(np.mean(p_rel_errors))},
    ]
    df = pd.DataFrame(metrics)
    df.to_csv(os.path.join(BASE_DIR, "metricas_dispositivo.csv"), index=False)
    print(df.to_string(index=False))


def main():
    data_n, data_p = load_tables()
    lib_path = generate_ngspice_library(data_n, data_p)
    print("Biblioteca refinada (v2) gerada em:", lib_path)
    run_characterization_suite(work_dir=BASE_DIR, lib_include="bp_ari_ngspice.lib", prefix="")
    compute_metrics_and_plots(data_n, data_p)
    run_hspice_cross_validation(data_n, data_p)
    print("Modulo 00 concluido com sucesso.")


if __name__ == "__main__":
    main()
