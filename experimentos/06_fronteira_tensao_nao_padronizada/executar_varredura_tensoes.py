"""
Módulo 06 — Fronteira Operacional sob Tensões Não-Padronizadas (Ngspice-47).

Investiga a hipótese experimental de comportamento fora das tensões nominais
estritamente dentro da janela validada pelas tabelas experimentais
(BP_ARI_dataN.txt: Vg2 in [0.2, 1.0] V; BP_ARI_dataP.txt: Vg2 in [-1.5, -0.9] V):

1. Porta Polimórfica NAND/NOR (4T):
   - Varredura 2D VDD (0,25..1,10 V) x Regime de Polaridade na LUT, sob Key=0 (NAND) e Key=1 (NOR).
   - Mapa de Assimetria V(g2,s)_n x V(g2,s)_p em VDD = 0,80 V.
2. Porta Polimórfica XOR/XNOR (4T):
   - Varredura 2D VDD (0,60..1,50 V) x Vin (0,40..1,30 V) sob polaridade nominal e sub-polarizada,
     além de comparação com Vgtop fixo em 0 V (VDD em [0,90..1,50 V]).

Classifica cada ponto operacional nas três categorias da hipótese:
- CORRETA: mantém a função booleana nominal com níveis lógicos válidos (V/VDD <= 0,25 ou >= 0,75).
- OUTRA_FUNCAO: níveis digitais válidos, mas altera a tabela-verdade para outra função booleana.
- INDEFINIDO_ANALOGICO: ao menos uma entrada colapsa para nível intermediário (0,25 < V/VDD < 0,75).
"""

import os
import subprocess
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
NGSPICE_EXE = os.path.join(ROOT_DIR, "ngspice-47_64", "Spice64", "bin", "ngspice_con.exe")
LIB_REL = "../00_modelo_ngspice/bp_ari_ngspice.lib"

BOOL_NAMES = {
    "0000": "CONST_0",
    "0001": "AND",
    "0010": "A_AND_NOT_B",
    "0011": "BUF_A",
    "0100": "NOT_A_AND_B",
    "0101": "BUF_B",
    "0110": "XOR",
    "0111": "OR",
    "1000": "NOR",
    "1001": "XNOR",
    "1010": "NOT_B",
    "1011": "A_IMP_B",
    "1100": "NOT_A",
    "1101": "B_IMP_A",
    "1110": "NAND",
    "1111": "CONST_1",
}


def run_ngspice(sp_filename):
    """Executa uma netlist no ngspice_con.exe e retorna stdout."""
    sp_path = os.path.join(BASE_DIR, sp_filename)
    proc = subprocess.run(
        [NGSPICE_EXE, "-b", sp_path],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def build_staircase_pwl(values, step_ns=10.0, edge_ns=0.2):
    """Gera string PWL em escada com degraus constantes de duração `step_ns`."""
    lines = []
    for k, val in enumerate(values):
        t0 = k * step_ns
        t1 = (k + 1) * step_ns - edge_ns
        lines.append(f"+ {t0:.2f}n {val:.6g}  {t1:.2f}n {val:.6g}")
    t_end = len(values) * step_ns
    lines.append(f"+ {t_end:.2f}n {values[-1]:.6g}")
    return "\n".join(lines)


def classify_truth_table(v_outs, vdd, target_bits, low_th=0.25, high_th=0.75):
    """Classifica 4 saídas (00, 01, 10, 11) em CORRETA, OUTRA_FUNCAO ou INDEFINIDO_ANALOGICO."""
    norms = [v / vdd for v in v_outs]
    bits = []
    for vn in norms:
        if vn >= high_th:
            bits.append("1")
        elif vn <= low_th:
            bits.append("0")
        else:
            bits.append("X")
    pattern = "".join(bits)

    ones = [v_outs[i] for i, b in enumerate(target_bits) if b == "1"]
    zeros = [v_outs[i] for i, b in enumerate(target_bits) if b == "0"]
    swing_alvo_norm = (min(ones) - max(zeros)) / vdd if ones and zeros else 0.0

    if "X" in pattern:
        categoria = "INDEFINIDO_ANALOGICO"
        func_eq = "INDEFINIDO"
    elif pattern == target_bits:
        categoria = "CORRETA"
        func_eq = BOOL_NAMES[pattern]
    else:
        categoria = "OUTRA_FUNCAO"
        func_eq = BOOL_NAMES.get(pattern, f"PAT_{pattern}")

    return pattern, categoria, func_eq, swing_alvo_norm


def sample_windows(t_ns, data_cols, n_windows, step_ns=10.0):
    """Extrai média estacionária no fim de cada janela [k*step+8.8, k*step+9.6] ns."""
    out = np.zeros((n_windows, data_cols.shape[1]))
    for k in range(n_windows):
        t_lo = k * step_ns + 8.8
        t_hi = k * step_ns + 9.6
        mask = (t_ns >= t_lo) & (t_ns <= t_hi)
        if not np.any(mask):
            idx = int(np.argmin(np.abs(t_ns - (k * step_ns + 9.2))))
            out[k, :] = data_cols[idx, :]
        else:
            out[k, :] = np.mean(data_cols[mask, :], axis=0)
    return out


def run_nand_nor_4t_sweep(sp_name, dat_name, cases):
    """Monta e simula 4 células NAND/NOR paralelas (00, 01, 10, 11) para lista de casos."""
    n_cases = len(cases)
    step_ns = 10.0
    t_end = n_cases * step_ns

    rtop_pwl = build_staircase_pwl([c["rtop"] for c in cases], step_ns)
    rbot_pwl = build_staircase_pwl([c["rbot"] for c in cases], step_ns)
    gtop_pwl = build_staircase_pwl([c["gtop"] for c in cases], step_ns)
    gbot_pwl = build_staircase_pwl([c["gbot"] for c in cases], step_ns)
    vhi_pwl = build_staircase_pwl([c["vdd"] for c in cases], step_ns)

    net = f"""* Varredura de Tensoes Nao-Padronizadas — Porta Polimorfica NAND/NOR 4T
.include "{LIB_REL}"

Vrtop rtop 0 pwl(
{rtop_pwl})
Vrbot rbot 0 pwl(
{rbot_pwl})
Vgtop gtop 0 pwl(
{gtop_pwl})
Vgbot gbot 0 pwl(
{gbot_pwl})
Vvhi vhi 0 pwl(
{vhi_pwl})
Vlo vlo 0 0.0

* Padrao 00 (A=0, B=0)
X00_1 out00 vlo rtop gtop gtop ARI W=1.0
X00_2 out00 vlo rtop gtop gtop ARI W=1.0
X00_3 out00 vlo n00  gbot gbot ARI W=2.0
X00_4 n00   vlo rbot gbot gbot ARI W=2.0
C00_o out00 0 0.2f
C00_n n00   0 0.1f

* Padrao 01 (A=0, B=VDD)
X01_1 out01 vlo rtop gtop gtop ARI W=1.0
X01_2 out01 vhi rtop gtop gtop ARI W=1.0
X01_3 out01 vhi n01  gbot gbot ARI W=2.0
X01_4 n01   vlo rbot gbot gbot ARI W=2.0
C01_o out01 0 0.2f
C01_n n01   0 0.1f

* Padrao 10 (A=VDD, B=0)
X10_1 out10 vhi rtop gtop gtop ARI W=1.0
X10_2 out10 vlo rtop gtop gtop ARI W=1.0
X10_3 out10 vlo n10  gbot gbot ARI W=2.0
X10_4 n10   vhi rbot gbot gbot ARI W=2.0
C10_o out10 0 0.2f
C10_n n10   0 0.1f

* Padrao 11 (A=VDD, B=VDD)
X11_1 out11 vhi rtop gtop gtop ARI W=1.0
X11_2 out11 vhi rtop gtop gtop ARI W=1.0
X11_3 out11 vhi n11  gbot gbot ARI W=2.0
X11_4 n11   vhi rbot gbot gbot ARI W=2.0
C11_o out11 0 0.2f
C11_n n11   0 0.1f

.control
set wr_vecnames
set wr_singlescale
tran 100p {t_end:.1f}n
wrdata {dat_name} v(out00) v(out01) v(out10) v(out11) i(Vrtop) i(Vrbot)
.endc
.end
"""
    with open(os.path.join(BASE_DIR, sp_name), "w", encoding="utf-8") as f:
        f.write(net)
    run_ngspice(sp_name)

    raw = np.loadtxt(os.path.join(BASE_DIR, dat_name), skiprows=1)
    t_ns = raw[:, 0] * 1e9
    sampled = sample_windows(t_ns, raw[:, 1:], n_cases, step_ns)

    rows = []
    for k, c in enumerate(cases):
        vouts = [float(sampled[k, i]) for i in range(4)]
        i_static_uA = max(abs(float(sampled[k, 4])), abs(float(sampled[k, 5]))) * 1e6
        target_bits = "1110" if c["key"] == 0 else "1000"
        target_name = "NAND" if c["key"] == 0 else "NOR"
        pattern, categoria, func_eq, swing_norm = classify_truth_table(
            vouts, c["vdd"], target_bits
        )
        rows.append(
            {
                "Experimento": c["exp"],
                "Porta_Alvo": target_name,
                "Key": c["key"],
                "VDD_V": c["vdd"],
                "Regime_Polaridade": c["pol_label"],
                "Vg2s_N_V": c["vg2n"],
                "Vg2s_P_V": c["vg2p"],
                "V00_V": round(vouts[0], 4),
                "V01_V": round(vouts[1], 4),
                "V10_V": round(vouts[2], 4),
                "V11_V": round(vouts[3], 4),
                "Padrao_Bits": pattern,
                "Categoria": categoria,
                "Funcao_Equivalente": func_eq,
                "Margem_Norm": round(swing_norm, 4),
                "I_estatica_uA": round(i_static_uA, 4),
            }
        )
    return pd.DataFrame(rows)


def run_xor_xnor_4t_sweep(sp_name, dat_name, cases):
    """Monta e simula 4 células XOR/XNOR paralelas (00, 01, 10, 11) para lista de casos."""
    n_cases = len(cases)
    step_ns = 10.0
    t_end = n_cases * step_ns

    rtop_pwl = build_staircase_pwl([c["rtop"] for c in cases], step_ns)
    rbot_pwl = build_staircase_pwl([c["rbot"] for c in cases], step_ns)
    gtop_pwl = build_staircase_pwl([c["gtop"] for c in cases], step_ns)
    gbot_pwl = build_staircase_pwl([c["gbot"] for c in cases], step_ns)
    vin_pwl = build_staircase_pwl([c["vin"] for c in cases], step_ns)

    # Em poly_xor_xnor:
    # X1 out an rtop b  gtop
    # X2 out a  rtop bn gtop
    # X3 out a  rbot b  gbot
    # X4 out an rbot bn gbot
    net = f"""* Varredura de Tensoes Nao-Padronizadas — Porta Polimorfica XOR/XNOR 4T
.include "{LIB_REL}"

Vrtop rtop 0 pwl(
{rtop_pwl})
Vrbot rbot 0 pwl(
{rbot_pwl})
Vgtop gtop 0 pwl(
{gtop_pwl})
Vgbot gbot 0 pwl(
{gbot_pwl})
Vahi ahi 0 pwl(
{vin_pwl})
Valo alo 0 0.0

* Padrao 00 (A=0, AN=Vin, B=0, BN=Vin)
X00_1 out00 ahi rtop alo gtop ARI W=1.0
X00_2 out00 alo rtop ahi gtop ARI W=1.0
X00_3 out00 alo rbot alo gbot ARI W=1.0
X00_4 out00 ahi rbot ahi gbot ARI W=1.0
C00 out00 0 0.2f

* Padrao 01 (A=0, AN=Vin, B=Vin, BN=0)
X01_1 out01 ahi rtop ahi gtop ARI W=1.0
X01_2 out01 alo rtop alo gtop ARI W=1.0
X01_3 out01 alo rbot ahi gbot ARI W=1.0
X01_4 out01 ahi rbot alo gbot ARI W=1.0
C01 out01 0 0.2f

* Padrao 10 (A=Vin, AN=0, B=0, BN=Vin)
X10_1 out10 alo rtop alo gtop ARI W=1.0
X10_2 out10 ahi rtop ahi gtop ARI W=1.0
X10_3 out10 ahi rbot alo gbot ARI W=1.0
X10_4 out10 alo rbot ahi gbot ARI W=1.0
C10 out10 0 0.2f

* Padrao 11 (A=Vin, AN=0, B=Vin, BN=0)
X11_1 out11 alo rtop ahi gtop ARI W=1.0
X11_2 out11 ahi rtop alo gtop ARI W=1.0
X11_3 out11 ahi rbot ahi gbot ARI W=1.0
X11_4 out11 alo rbot alo gbot ARI W=1.0
C11 out11 0 0.2f

.control
set wr_vecnames
set wr_singlescale
tran 100p {t_end:.1f}n
wrdata {dat_name} v(out00) v(out01) v(out10) v(out11) i(Vrtop) i(Vrbot)
.endc
.end
"""
    with open(os.path.join(BASE_DIR, sp_name), "w", encoding="utf-8") as f:
        f.write(net)
    run_ngspice(sp_name)

    raw = np.loadtxt(os.path.join(BASE_DIR, dat_name), skiprows=1)
    t_ns = raw[:, 0] * 1e9
    sampled = sample_windows(t_ns, raw[:, 1:], n_cases, step_ns)

    rows = []
    for k, c in enumerate(cases):
        vouts = [float(sampled[k, i]) for i in range(4)]
        i_static_uA = max(abs(float(sampled[k, 4])), abs(float(sampled[k, 5]))) * 1e6
        target_bits = "0110" if c["key"] == 0 else "1001"
        target_name = "XOR" if c["key"] == 0 else "XNOR"
        pattern, categoria, func_eq, swing_norm = classify_truth_table(
            vouts, c["vdd"], target_bits
        )
        rows.append(
            {
                "Experimento": c["exp"],
                "Porta_Alvo": target_name,
                "Key": c["key"],
                "VDD_V": c["vdd"],
                "Vin_V": c["vin"],
                "Regime_Polaridade": c["pol_label"],
                "Vg2s_N_V": c["vg2n"],
                "Vg2s_P_V": c["vg2p"],
                "V00_V": round(vouts[0], 4),
                "V01_V": round(vouts[1], 4),
                "V10_V": round(vouts[2], 4),
                "V11_V": round(vouts[3], 4),
                "Padrao_Bits": pattern,
                "Categoria": categoria,
                "Funcao_Equivalente": func_eq,
                "Margem_Norm": round(swing_norm, 4),
                "I_estatica_uA": round(i_static_uA, 4),
            }
        )
    return pd.DataFrame(rows)


def build_cases_nand_nor():
    """Constrói grade (VDD x Polaridade) e grade assimétrica (Vg2n x Vg2p)."""
    # Experimento 1: VDD x Regime de Polaridade dentro da LUT
    vdds = [0.25, 0.35, 0.50, 0.65, 0.80, 0.95, 1.10]
    pol_regimes = [
        ("Sub-pol Min (+0,2/-0,9V)", 0.20, -0.90),
        ("Sub-pol Mod (+0,4/-1,1V)", 0.40, -1.10),
        ("Nom. NAND (+0,8/-1,2V)", 0.80, -1.20),
        ("Nom. NOR (+0,8/-1,5V)", 0.80, -1.50),
        ("Sobre-pol (+1,0/-1,5V)", 1.00, -1.50),
    ]
    cases_vdd = []
    for key in [0, 1]:
        for label, vg2n, vg2p in pol_regimes:
            for vdd in vdds:
                if key == 0:
                    rtop, rbot = vdd, 0.0
                    gtop, gbot = vdd + vg2p, vg2n
                else:
                    rtop, rbot = 0.0, vdd
                    gtop, gbot = vg2n, vdd + vg2p
                cases_vdd.append(
                    {
                        "exp": "NAND_NOR_VDD_x_Pol",
                        "key": key,
                        "vdd": vdd,
                        "pol_label": label,
                        "vg2n": vg2n,
                        "vg2p": vg2p,
                        "rtop": rtop,
                        "rbot": rbot,
                        "gtop": gtop,
                        "gbot": gbot,
                    }
                )

    # Experimento 2: Assimetria Vg2s_n x Vg2s_p em VDD = 0,80 V
    vg2n_grid = [0.20, 0.30, 0.40, 0.60, 0.80, 1.00]
    vg2p_grid = [-0.90, -1.00, -1.10, -1.20, -1.35, -1.50]
    cases_asym = []
    vdd_nom = 0.80
    for key in [0, 1]:
        for vg2n in vg2n_grid:
            for vg2p in vg2p_grid:
                if key == 0:
                    rtop, rbot = vdd_nom, 0.0
                    gtop, gbot = vdd_nom + vg2p, vg2n
                else:
                    rtop, rbot = 0.0, vdd_nom
                    gtop, gbot = vg2n, vdd_nom + vg2p
                cases_asym.append(
                    {
                        "exp": "NAND_NOR_Assimetria_PN",
                        "key": key,
                        "vdd": vdd_nom,
                        "pol_label": f"N={vg2n:+.2f}V / P={vg2p:+.2f}V",
                        "vg2n": vg2n,
                        "vg2p": vg2p,
                        "rtop": rtop,
                        "rbot": rbot,
                        "gtop": gtop,
                        "gbot": gbot,
                    }
                )
    return cases_vdd, cases_asym


def build_cases_xor_xnor():
    """Constrói grade VDD x Vin para XOR/XNOR dentro da faixa medida da LUT."""
    vdds = [0.60, 0.80, 1.00, 1.20, 1.50]
    vins = [0.40, 0.60, 0.80, 1.10, 1.30]
    pol_modes = [
        ("Nominal (+0,8/-1,5V)", 0.80, -1.50),
        ("Sub-pol Min (+0,2/-0,9V)", 0.20, -0.90),
    ]
    cases_xor = []
    for label, vg2n, vg2p in pol_modes:
        for key in [0, 1]:
            for vdd in vdds:
                for vin in vins:
                    if key == 0:
                        # rtop = VDD (p-FET), rbot = 0 (n-FET)
                        rtop, rbot = vdd, 0.0
                        gtop, gbot = vdd + vg2p, vg2n
                    else:
                        # rtop = 0 (n-FET), rbot = VDD (p-FET)
                        rtop, rbot = 0.0, vdd
                        gtop, gbot = vg2n, vdd + vg2p
                    cases_xor.append(
                        {
                            "exp": "XOR_XNOR_VDD_x_Vin",
                            "key": key,
                            "vdd": vdd,
                            "vin": vin,
                            "pol_label": label,
                            "vg2n": vg2n,
                            "vg2p": vg2p,
                            "rtop": rtop,
                            "rbot": rbot,
                            "gtop": gtop,
                            "gbot": gbot,
                        }
                    )

    # Tambem testar caso realista de controle fixo (Vg_p = 0V => V(g2,s) = -VDD, para VDD em [0.9..1.5]V)
    for key in [0, 1]:
        for vdd in [0.90, 1.00, 1.20, 1.35, 1.50]:
            for vin in vins:
                if key == 0:
                    rtop, rbot = vdd, 0.0
                    gtop, gbot = 0.0, 0.80
                else:
                    rtop, rbot = 0.0, vdd
                    gtop, gbot = 0.80, 0.0
                cases_xor.append(
                    {
                        "exp": "XOR_XNOR_VgFixo_0V",
                        "key": key,
                        "vdd": vdd,
                        "vin": vin,
                        "pol_label": f"Vg_p=0V (Vg2s=-{vdd:.2f}V)",
                        "vg2n": 0.80,
                        "vg2p": -vdd,
                        "rtop": rtop,
                        "rbot": rbot,
                        "gtop": gtop,
                        "gbot": gbot,
                    }
                )
    return cases_xor


def categoria_to_code(cat):
    if cat == "CORRETA":
        return 0
    if cat == "OUTRA_FUNCAO":
        return 1
    return 2  # INDEFINIDO_ANALOGICO


def plot_nand_nor_maps(df_vdd, df_asym):
    """Gera fig1 (VDD x Polaridade) e fig2 (Assimetria Vg2n x Vg2p) com anotações."""
    plt.rcParams.update({"font.size": 9.5})
    cmap = ListedColormap(["#2ca02c", "#ff7f0e", "#d62728"])  # Verde, Laranja, Vermelho
    legend_handles = [
        Patch(facecolor="#2ca02c", edgecolor="black", label="CORRETA (Função Alvo)"),
        Patch(facecolor="#ff7f0e", edgecolor="black", label="OUTRA_FUNCAO (Virou outra porta)"),
        Patch(facecolor="#d62728", edgecolor="black", label="INDEFINIDO_ANALOGICO (X)"),
    ]

    # --- FIGURA 1: VDD x Polaridade ---
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), sharey=True)
    vdds = sorted(df_vdd["VDD_V"].unique())
    pols = list(dict.fromkeys(df_vdd["Regime_Polaridade"].tolist()))

    for ax, porta in zip(axes, ["NAND", "NOR"]):
        sub = df_vdd[df_vdd["Porta_Alvo"] == porta]
        mat = np.zeros((len(pols), len(vdds)))
        for i, p in enumerate(pols):
            for j, vdd in enumerate(vdds):
                row = sub[(sub["Regime_Polaridade"] == p) & (sub["VDD_V"] == vdd)].iloc[0]
                mat[i, j] = categoria_to_code(row["Categoria"])
                txt = (
                    f"{row['Funcao_Equivalente']}\n({row['Margem_Norm']*100:.0f}%)"
                    if row["Categoria"] == "CORRETA"
                    else f"{row['Funcao_Equivalente']}\n[{row['Padrao_Bits']}]"
                )
                color_txt = "white" if row["Categoria"] != "OUTRA_FUNCAO" else "black"
                ax.text(j, i, txt, ha="center", va="center", fontsize=7.5, color=color_txt, fontweight="bold")

        ax.imshow(mat, cmap=cmap, vmin=0, vmax=2, aspect="auto")
        ax.set_xticks(range(len(vdds)))
        ax.set_xticklabels([f"{v:.2f}V" for v in vdds])
        ax.set_yticks(range(len(pols)))
        ax.set_yticklabels(pols)
        ax.set_xlabel("Tensão de Alimentação $V_{DD}$")
        ax.set_title(f"Porta Alvo: {porta} ($K={'0' if porta=='NAND' else '1'}$)")
        ax.set_xticks(np.arange(-0.5, len(vdds), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(pols), 1), minor=True)
        ax.grid(which="minor", color="white", linestyle="-", linewidth=1.5)
        ax.tick_params(which="minor", bottom=False, left=False)

    fig.legend(handles=legend_handles, loc="lower center", ncol=3, frameon=True, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(
        "Fronteira Operacional NAND/NOR: $V_{DD}$ vs. Polaridade dentro da LUT Experimental",
        fontsize=12,
        fontweight="bold",
    )
    plt.tight_layout(rect=[0, 0.06, 1, 0.94])
    plt.savefig(os.path.join(BASE_DIR, "fig1_nand_nor_mapa_vdd_polaridade.png"), dpi=180, bbox_inches="tight")
    plt.close()

    # --- FIGURA 2: Assimetria Vg2n x Vg2p (VDD = 0.8V) ---
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), sharey=True)
    vg2n_vals = sorted(df_asym["Vg2s_N_V"].unique())
    vg2p_vals = sorted(df_asym["Vg2s_P_V"].unique())  # -1.50 .. -0.90

    for ax, porta in zip(axes, ["NAND", "NOR"]):
        sub = df_asym[df_asym["Porta_Alvo"] == porta]
        mat = np.zeros((len(vg2p_vals), len(vg2n_vals)))
        for i, vp in enumerate(vg2p_vals):
            for j, vn in enumerate(vg2n_vals):
                row = sub[(sub["Vg2s_P_V"] == vp) & (sub["Vg2s_N_V"] == vn)].iloc[0]
                mat[i, j] = categoria_to_code(row["Categoria"])
                txt = (
                    f"{row['Margem_Norm']*100:.0f}%\n{row['I_estatica_uA']:.2f}uA"
                    if row["Categoria"] == "CORRETA"
                    else f"{row['Funcao_Equivalente']}\n[{row['Padrao_Bits']}]"
                )
                color_txt = "white" if row["Categoria"] != "OUTRA_FUNCAO" else "black"
                ax.text(j, i, txt, ha="center", va="center", fontsize=7.5, color=color_txt, fontweight="bold")

        ax.imshow(mat, cmap=cmap, vmin=0, vmax=2, aspect="auto")
        ax.set_xticks(range(len(vg2n_vals)))
        ax.set_xticklabels([f"+{v:.2f}V" for v in vg2n_vals])
        ax.set_yticks(range(len(vg2p_vals)))
        ax.set_yticklabels([f"{v:.2f}V" for v in vg2p_vals])
        ax.set_xlabel("$V(g2,s)$ n-FET (Pull-down/up N)")
        if ax is axes[0]:
            ax.set_ylabel("$V(g2,s)$ p-FET (Pull-up/down P)")
        ax.set_title(f"{porta} ($V_{{DD}} = 0,80\\ V$) — Margem e Corrente Estática")
        ax.set_xticks(np.arange(-0.5, len(vg2n_vals), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(vg2p_vals), 1), minor=True)
        ax.grid(which="minor", color="white", linestyle="-", linewidth=1.5)
        ax.tick_params(which="minor", bottom=False, left=False)

    fig.legend(handles=legend_handles, loc="lower center", ncol=3, frameon=True, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(
        "Mapa de Assimetria $V(g2,s)_n \\times V(g2,s)_p$ em $V_{DD} = 0,80\\ V$",
        fontsize=12,
        fontweight="bold",
    )
    plt.tight_layout(rect=[0, 0.06, 1, 0.94])
    plt.savefig(os.path.join(BASE_DIR, "fig2_nand_nor_assimetria_vg2.png"), dpi=180, bbox_inches="tight")
    plt.close()


def plot_xor_xnor_maps(df_xor):
    """Gera fig3 (XOR/XNOR VDD x Vin sob polaridade nominal vs sub-polarizada)."""
    plt.rcParams.update({"font.size": 9.5})
    cmap = ListedColormap(["#2ca02c", "#ff7f0e", "#d62728"])
    legend_handles = [
        Patch(facecolor="#2ca02c", edgecolor="black", label="CORRETA (XOR/XNOR)"),
        Patch(facecolor="#ff7f0e", edgecolor="black", label="OUTRA_FUNCAO (Virou outra porta)"),
        Patch(facecolor="#d62728", edgecolor="black", label="INDEFINIDO_ANALOGICO (X)"),
    ]

    sub_main = df_xor[df_xor["Experimento"] == "XOR_XNOR_VDD_x_Vin"]
    vdds = sorted(sub_main["VDD_V"].unique())
    vins = sorted(sub_main["Vin_V"].unique())
    panels = [
        ("XOR", "Nominal (+0,8/-1,5V)"),
        ("XNOR", "Nominal (+0,8/-1,5V)"),
        ("XOR", "Sub-pol Min (+0,2/-0,9V)"),
        ("XNOR", "Sub-pol Min (+0,2/-0,9V)"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(13.0, 9.0), sharex=True, sharey=True)
    for ax, (porta, pol) in zip(axes.flat, panels):
        sub = sub_main[(sub_main["Porta_Alvo"] == porta) & (sub_main["Regime_Polaridade"] == pol)]
        mat = np.zeros((len(vins), len(vdds)))
        for i, vin in enumerate(vins):
            for j, vdd in enumerate(vdds):
                row = sub[(sub["Vin_V"] == vin) & (sub["VDD_V"] == vdd)].iloc[0]
                mat[i, j] = categoria_to_code(row["Categoria"])
                txt = (
                    f"{row['Funcao_Equivalente']}\n({row['Margem_Norm']*100:.0f}%)"
                    if row["Categoria"] == "CORRETA"
                    else f"{row['Funcao_Equivalente']}\n[{row['Padrao_Bits']}]"
                )
                color_txt = "white" if row["Categoria"] != "OUTRA_FUNCAO" else "black"
                ax.text(j, i, txt, ha="center", va="center", fontsize=7.5, color=color_txt, fontweight="bold")

        ax.imshow(mat, cmap=cmap, vmin=0, vmax=2, aspect="auto")
        ax.set_xticks(range(len(vdds)))
        ax.set_xticklabels([f"{v:.2f}V" for v in vdds])
        ax.set_yticks(range(len(vins)))
        ax.set_yticklabels([f"{v:.2f}V" for v in vins])
        ax.set_title(f"{porta} | {pol}")
        ax.set_xticks(np.arange(-0.5, len(vdds), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(vins), 1), minor=True)
        ax.grid(which="minor", color="white", linestyle="-", linewidth=1.5)
        ax.tick_params(which="minor", bottom=False, left=False)

    axes[1, 0].set_xlabel("$V_{DD}$")
    axes[1, 1].set_xlabel("$V_{DD}$")
    axes[0, 0].set_ylabel("$V_{in}$ (Amplitude das entradas A, B)")
    axes[1, 0].set_ylabel("$V_{in}$ (Amplitude das entradas A, B)")
    fig.legend(handles=legend_handles, loc="lower center", ncol=3, frameon=True, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle(
        "Fronteira Operacional XOR/XNOR: Casamento $V_{DD} \\times V_{in}$ (Nominal vs. Sub-Polarizada)",
        fontsize=12.5,
        fontweight="bold",
    )
    plt.tight_layout(rect=[0, 0.04, 1, 0.95])
    plt.savefig(os.path.join(BASE_DIR, "fig3_xor_xnor_mapa_vdd_vin.png"), dpi=180, bbox_inches="tight")
    plt.close()


def main():
    cases_vdd, cases_asym = build_cases_nand_nor()
    cases_xor = build_cases_xor_xnor()

    df_vdd = run_nand_nor_4t_sweep("sweep_nand_nor_vdd_pol.sp", "sweep_nand_nor_vdd_pol.dat", cases_vdd)
    df_asym = run_nand_nor_4t_sweep("sweep_nand_nor_asym.sp", "sweep_nand_nor_asym.dat", cases_asym)
    df_xor = run_xor_xnor_4t_sweep("sweep_xor_xnor_vdd_vin.sp", "sweep_xor_xnor_vdd_vin.dat", cases_xor)

    df_nn = pd.concat([df_vdd, df_asym], ignore_index=True)
    df_nn.to_csv(os.path.join(BASE_DIR, "mapa_tensoes_nand_nor.csv"), index=False)
    df_xor.to_csv(os.path.join(BASE_DIR, "mapa_tensoes_xor_xnor.csv"), index=False)

    plot_nand_nor_maps(df_vdd, df_asym)
    plot_xor_xnor_maps(df_xor)

    print("=== RESUMO FRONTEIRA DE TENSOES NAO-PADRONIZADAS ===")
    for name, df in [("NAND/NOR (VDD x Pol)", df_vdd), ("NAND/NOR (Assimetria)", df_asym), ("XOR/XNOR", df_xor)]:
        counts = df["Categoria"].value_counts().to_dict()
        outras = df[df["Categoria"] == "OUTRA_FUNCAO"]["Funcao_Equivalente"].value_counts().to_dict()
        print(f"{name}: total={len(df)} | {counts} | outras_funcoes={outras}")


if __name__ == "__main__":
    main()
