"""
Módulo 03 — Análise de Segurança Física (Canal Lateral DPA), Robustez 3D e Retenção Flutuante.

Substitui integralmente os scripts MATLAB originais (example.m, simulation_waveforms.m,
graph_from_simulations.m, histogram_ex.m) em Python puro e executa validação paramétrica
adicional no ngspice-47:
1. Análise de Differential Power Analysis (DPA) usando nand_nor_waveforms.csv e xor_xnor_waveforms.csv.
2. Análise 3D de robustez Monte Carlo (250 amostras de ruído em VDD e VSS) a partir de
   robustness_nand.csv, robustness_nor.csv, robustness_xor.csv e robustness_xnor.csv.
3. Simulação paramétrica de ruído de fonte no ngspice-47 (sim_supply_noise.sp) para validação cruzada.
4. Análise temporal de degradação/retenção em nós flutuantes (100ns, 250ns, 500ns).
"""

import os
import subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
MCODE_DIR = os.path.join(ROOT_DIR, "BPFET_Nature_Electronics", "m_code")
NGSPICE_EXE = os.path.join(ROOT_DIR, "ngspice-47_64", "Spice64", "bin", "ngspice_con.exe")
LIB_REL = "../00_modelo_ngspice/bp_ari_ngspice.lib"


def run_ngspice_supply_sweep():
    """Roda varredura paramétrica de ruído em VDD e VSS na porta NAND no ngspice."""
    vdd_grid = [0.65, 0.725, 0.80, 0.875, 0.95]
    vss_grid = [-0.10, -0.05, 0.00, 0.05, 0.10]

    lines = [
        "* Varredura Parametrica de Ruido de Fonte (VDD x VSS) na Porta NAND BP SB-FET",
        f'.include "{LIB_REL}"',
        ".param pvdd=0.8",
        ".param pvss=0.0",
        "Vrtop rtop 0 {pvdd}",
        "Vrbot rbot 0 {pvss}",
        "Vgtop gtop 0 -0.4",
        "Vgbot gbot 0 0.8",
        "Va a 0 0.0",
        "Vb b 0 0.0",
        "X1 out a rtop gtop gtop ARI W=1.0",
        "X2 out b rtop gtop gtop ARI W=1.0",
        "X3 out b n1   gbot gbot ARI W=2.0",
        "X4 n1  a rbot gbot gbot ARI W=2.0",
        ".control",
        "set wr_vecnames",
        "set wr_singlescale",
    ]
    results = []
    # Salva cada ponto via print op
    for vdd in vdd_grid:
        for vss in vss_grid:
            tag = f"v{vdd:.3f}_s{vss:+.3f}".replace(".", "d").replace("+", "p").replace("-", "m")
            lines.extend([
                f"alterparam pvdd = {vdd}",
                f"alterparam pvss = {vss}",
                "reset",
                "alter Va = 0.0",
                "alter Vb = 0.0",
                "op",
                f"wrdata sweep_00_{tag}.dat v(out)",
                f"alter Va = {vdd}",
                f"alter Vb = {vdd}",
                "op",
                f"wrdata sweep_11_{tag}.dat v(out)",
            ])
    lines.extend([".endc", ".end", ""])

    sp_path = os.path.join(BASE_DIR, "sim_supply_noise.sp")
    with open(sp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    subprocess.run(
        [NGSPICE_EXE, "-b", sp_path],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=True,
    )

    for vdd in vdd_grid:
        for vss in vss_grid:
            tag = f"v{vdd:.3f}_s{vss:+.3f}".replace(".", "d").replace("+", "p").replace("-", "m")
            v00 = float(np.loadtxt(os.path.join(BASE_DIR, f"sweep_00_{tag}.dat"), skiprows=1)[1])
            v11 = float(np.loadtxt(os.path.join(BASE_DIR, f"sweep_11_{tag}.dat"), skiprows=1)[1])
            results.append({
                "VDD_V": vdd,
                "VSS_V": vss,
                "Vout_00_V": v00,
                "Vout_11_V": v11,
                "Margem_V": v00 - v11,
            })
    df_sweep = pd.DataFrame(results)
    df_sweep.to_csv(os.path.join(BASE_DIR, "ngspice_supply_sweep.csv"), index=False)
    return df_sweep


def analyze_dpa_waveforms():
    """Analisa formas de onda de potência/corrente para ataque DPA (NAND/NOR vs XOR/XNOR)."""
    df_nn = pd.read_csv(os.path.join(MCODE_DIR, "nand_nor_waveforms.csv"))
    df_xx = pd.read_csv(os.path.join(MCODE_DIR, "xor_xnor_waveforms.csv")).dropna(axis=1, how="all")

    # Nota: em nand_nor_waveforms.csv, as colunas 3..6 correspondem a NAND e NOR (conforme simulation_waveforms.m)
    t_nn_us = df_nn.iloc[:, 0].values * 1e6
    va_nn = np.abs(df_nn.iloc[:, 1].values)
    vb_nn = np.abs(df_nn.iloc[:, 2].values)
    v_nand = np.abs(df_nn.iloc[:, 3].values)
    v_nor = np.abs(df_nn.iloc[:, 4].values)
    i_nand = np.abs(df_nn.iloc[:, 5].values)
    i_nor = np.abs(df_nn.iloc[:, 6].values)

    t_xx_us = df_xx.iloc[:, 0].values * 1e6
    va_xx = np.abs(df_xx.iloc[:, 1].values)
    vb_xx = np.abs(df_xx.iloc[:, 2].values)
    v_xor = np.abs(df_xx.iloc[:, 3].values)
    v_xnor = np.abs(df_xx.iloc[:, 4].values)
    i_xor = np.abs(df_xx.iloc[:, 5].values)
    i_xnor = np.abs(df_xx.iloc[:, 6].values)

    # Janela de interesse 0..30 us
    m_nn = t_nn_us <= 30.0
    m_xx = t_xx_us <= 30.0

    # Métricas de assimetria DPA
    diff_nn = np.abs(i_nand[m_nn] - i_nor[m_nn])
    diff_xx = np.abs(i_xor[m_xx] - i_xnor[m_xx])

    dpa_stats = [
        {
            "Familia": "NAND / NOR",
            "I_pico_modo0_uA": float(np.max(i_nand[m_nn]) * 1e6),
            "I_pico_modo1_uA": float(np.max(i_nor[m_nn]) * 1e6),
            "I_medio_modo0_uA": float(np.mean(i_nand[m_nn]) * 1e6),
            "I_medio_modo1_uA": float(np.mean(i_nor[m_nn]) * 1e6),
            "Assimetria_Media_DPA_uA": float(np.mean(diff_nn) * 1e6),
            "Assimetria_Pico_DPA_uA": float(np.max(diff_nn) * 1e6),
            "Correlacao_I0_I1": float(np.corrcoef(i_nand[m_nn], i_nor[m_nn])[0, 1]),
        },
        {
            "Familia": "XOR / XNOR",
            "I_pico_modo0_uA": float(np.max(i_xor[m_xx]) * 1e6),
            "I_pico_modo1_uA": float(np.max(i_xnor[m_xx]) * 1e6),
            "I_medio_modo0_uA": float(np.mean(i_xor[m_xx]) * 1e6),
            "I_medio_modo1_uA": float(np.mean(i_xnor[m_xx]) * 1e6),
            "Assimetria_Media_DPA_uA": float(np.mean(diff_xx) * 1e6),
            "Assimetria_Pico_DPA_uA": float(np.max(diff_xx) * 1e6),
            "Correlacao_I0_I1": float(np.corrcoef(i_xor[m_xx], i_xnor[m_xx])[0, 1]),
        },
    ]

    # Figura 1: Comparação DPA lado a lado
    fig, axes = plt.subplots(5, 2, figsize=(13, 10), sharex=True)
    # Esquerda: NAND / NOR
    axes[0, 0].plot(t_nn_us[m_nn], va_nn[m_nn], "k", lw=1.5)
    axes[0, 0].set_title("Portas Polimórficas NAND / NOR (Dados Experimentais HSPICE)")
    axes[0, 0].set_ylabel("$V(A)\\ (\\mathrm{V})$")
    axes[1, 0].plot(t_nn_us[m_nn], vb_nn[m_nn], "k", lw=1.5)
    axes[1, 0].set_ylabel("$V(B)\\ (\\mathrm{V})$")
    axes[2, 0].plot(t_nn_us[m_nn], v_nand[m_nn], "#08519c", lw=1.6)
    axes[2, 0].set_ylabel("$V_{\\mathrm{NAND}}\\ (\\mathrm{V})$")
    axes[3, 0].plot(t_nn_us[m_nn], v_nor[m_nn], "#cb181d", lw=1.6)
    axes[3, 0].set_ylabel("$V_{\\mathrm{NOR}}\\ (\\mathrm{V})$")
    axes[4, 0].plot(t_nn_us[m_nn], i_nand[m_nn] * 1e6, "#08519c", lw=1.4, label="$|I(\\mathrm{NAND})|$")
    axes[4, 0].plot(t_nn_us[m_nn], i_nor[m_nn] * 1e6, "#cb181d", lw=1.4, alpha=0.85, label="$|I(\\mathrm{NOR})|$")
    axes[4, 0].set_ylabel("$|I_{DD}|\\ (\\mu\\mathrm{A})$")
    axes[4, 0].set_xlabel("Tempo ($\\mu\\mathrm{s}$)")
    axes[4, 0].legend(fontsize=8.5)

    # Direita: XOR / XNOR
    axes[0, 1].plot(t_xx_us[m_xx], va_xx[m_xx], "k", lw=1.5)
    axes[0, 1].set_title("Portas Polimórficas XOR / XNOR (Maior Simetria contra DPA)")
    axes[0, 1].set_ylabel("$V(A)\\ (\\mathrm{V})$")
    axes[1, 1].plot(t_xx_us[m_xx], vb_xx[m_xx], "k", lw=1.5)
    axes[1, 1].set_ylabel("$V(B)\\ (\\mathrm{V})$")
    axes[2, 1].plot(t_xx_us[m_xx], v_xor[m_xx], "#08519c", lw=1.6)
    axes[2, 1].set_ylabel("$V_{\\mathrm{XOR}}\\ (\\mathrm{V})$")
    axes[3, 1].plot(t_xx_us[m_xx], v_xnor[m_xx], "#cb181d", lw=1.6)
    axes[3, 1].set_ylabel("$V_{\\mathrm{XNOR}}\\ (\\mathrm{V})$")
    axes[4, 1].plot(t_xx_us[m_xx], i_xor[m_xx] * 1e6, "#08519c", lw=1.4, label="$|I(\\mathrm{XOR})|$")
    axes[4, 1].plot(t_xx_us[m_xx], i_xnor[m_xx] * 1e6, "#cb181d", lw=1.4, alpha=0.85, label="$|I(\\mathrm{XNOR})|$")
    axes[4, 1].set_ylabel("$|I_{DD}|\\ (\\mu\\mathrm{A})$")
    axes[4, 1].set_xlabel("Tempo ($\\mu\\mathrm{s}$)")
    axes[4, 1].legend(fontsize=8.5)

    for ax in axes.ravel():
        ax.grid(True, alpha=0.3)
    for r in range(4):
        axes[r, 0].set_ylim(-0.1, 1.1)
        axes[r, 1].set_ylim(-0.1, 1.1)

    fig.suptitle("Análise de Canal Lateral (DPA): Assinatura de Corrente NAND/NOR vs. XOR/XNOR", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(BASE_DIR, "fig1_dpa_assinatura_corrente.png"), dpi=200)
    plt.close(fig)

    return dpa_stats


def plot_3d_robustness_pair(df1, name1, df2, name2, out_filename, suptitle):
    """Gera painel 2x4 com gráficos 3D (equivalente Python ao scatterbar3.m) para um par polimórfico."""
    fig = plt.figure(figsize=(15, 7.5))
    inputs = ["00", "01", "10", "11"]

    for row_idx, (df, gname) in enumerate([(df1, name1), (df2, name2)]):
        cols = df.columns.tolist()
        x = df[cols[0]].values
        y = df[cols[1]].values
        for col_idx, inp in enumerate(inputs):
            ax = fig.add_subplot(2, 4, row_idx * 4 + col_idx + 1, projection="3d")
            z = df[cols[2 + col_idx]].values
            sc = ax.scatter(x, y, z, c=z, cmap="viridis", vmin=-0.1, vmax=1.0, s=18, alpha=0.85)
            ax.set_title(f"{gname} — Entrada {inp}", fontsize=9.5, fontweight="bold")
            ax.set_xlabel("$V_{\\mathrm{rail,top}}$ (V)", fontsize=8)
            ax.set_ylabel("$V_{\\mathrm{rail,bot}}$ (V)", fontsize=8)
            ax.set_zlabel("$V_{\\mathrm{OUT}}$ (V)", fontsize=8)
            ax.set_zlim(-0.1, 1.1)
            ax.tick_params(labelsize=7)

    fig.subplots_adjust(right=0.90, wspace=0.25, hspace=0.28, top=0.90)
    cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.70])
    fig.colorbar(sc, cax=cbar_ax, label="$V_{\\mathrm{OUT}}$ (V)")
    fig.suptitle(suptitle, fontsize=13, fontweight="bold")
    fig.savefig(os.path.join(BASE_DIR, out_filename), dpi=200)
    plt.close(fig)


def analyze_robustness_and_floating(df_sweep):
    """Analisa Monte Carlo 3D, histogramas e curvas de nó flutuante."""
    df_nand = pd.read_csv(os.path.join(MCODE_DIR, "robustness_nand.csv"), sep="\t")
    df_nor = pd.read_csv(os.path.join(MCODE_DIR, "robustness_nor.csv"), sep="\t")
    df_xor = pd.read_csv(os.path.join(MCODE_DIR, "robustness_xor.csv"), sep=",")
    df_xnor = pd.read_csv(os.path.join(MCODE_DIR, "robustness_xnor.csv"), sep=",")

    plot_3d_robustness_pair(
        df_nand, "NAND", df_nor, "NOR",
        "fig2_robustez_3d_nand_nor.png",
        "Robustez a Flutuações de Fonte (250 Amostras Monte Carlo): NAND e NOR",
    )
    plot_3d_robustness_pair(
        df_xor, "XOR", df_xnor, "XNOR",
        "fig3_robustez_3d_xor_xnor.png",
        "Robustez a Flutuações de Fonte (250 Amostras Monte Carlo): XOR e XNOR",
    )

    # Estatísticas de Monte Carlo para todas as 4 portas
    mc_stats = []
    expected_map = {
        "NAND": [1, 1, 1, 0],
        "NOR": [1, 0, 0, 0],
        "XOR": [0, 1, 1, 0],
        "XNOR": [1, 0, 0, 1],
    }
    for gname, df in [("NAND", df_nand), ("NOR", df_nor), ("XOR", df_xor), ("XNOR", df_xnor)]:
        cols = df.columns.tolist()
        high_vals, low_vals = [], []
        correct_count = 0
        total_count = 0
        for idx, exp in enumerate(expected_map[gname]):
            vals = df[cols[2 + idx]].values
            total_count += len(vals)
            if exp == 1:
                high_vals.extend(vals)
                correct_count += int(np.sum(vals > 0.4))
            else:
                low_vals.extend(vals)
                correct_count += int(np.sum(vals < 0.4))
        mc_stats.append({
            "Porta": gname,
            "Amostras": len(df),
            "V_nivel_1_medio_V": float(np.mean(high_vals)),
            "V_nivel_1_std_mV": float(np.std(high_vals) * 1e3),
            "V_nivel_0_medio_V": float(np.mean(low_vals)),
            "V_nivel_0_std_mV": float(np.std(low_vals) * 1e3),
            "Taxa_Acerto_Logico_pct": float(correct_count / total_count * 100.0),
        })

    # Figura 4: Histogramas Monte Carlo + Validação Ngspice + Curvas de Nó Flutuante
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.5))

    # [0,0] Histograma de VDD e VSS (como histogram_ex.m)
    vdd_mc = df_nand.iloc[:, 0].values
    vss_mc = df_nand.iloc[:, 1].values
    axes[0, 0].hist(vdd_mc, bins=18, color="#3182bd", alpha=0.8, edgecolor="k", label=f"$V_{{DD}}$ ($\\mu={np.mean(vdd_mc):.3f}\\,\\mathrm{{V}}$)")
    axes[0, 0].hist(vss_mc, bins=18, color="#31a354", alpha=0.8, edgecolor="k", label=f"$V_{{SS}}$ ($\\mu={np.mean(vss_mc):.3f}\\,\\mathrm{{V}}$)")
    axes[0, 0].set_title("Distribuição Monte Carlo nos Trilhos ($n=250$)")
    axes[0, 0].set_xlabel("Tensão (V)")
    axes[0, 0].set_ylabel("Ocorrências")
    axes[0, 0].legend(fontsize=8.5)
    axes[0, 0].grid(True, alpha=0.3)

    # [0,1] Separação de níveis '0' e '1' em XOR/XNOR vs NAND/NOR sob ruído
    xor_vals_0 = np.concatenate([df_xor["XOR_00"].values, df_xor["XOR_11"].values])
    xor_vals_1 = np.concatenate([df_xor["XOR_01"].values, df_xor["XOR_10"].values])
    axes[0, 1].hist(xor_vals_0, bins=18, color="#e6550d", alpha=0.8, edgecolor="k", label=f"Nível '0' ($\\mu={np.mean(xor_vals_0):.3f}\\,\\mathrm{{V}}$)")
    axes[0, 1].hist(xor_vals_1, bins=18, color="#756bb1", alpha=0.8, edgecolor="k", label=f"Nível '1' ($\\mu={np.mean(xor_vals_1):.3f}\\,\\mathrm{{V}}$)")
    axes[0, 1].axvline(0.4, color="red", ls="--", lw=1.2, label="Limiar $0,4\\,\\mathrm{V}$")
    axes[0, 1].set_title("Separação de Margem Lógica (XOR sob Ruído de Fonte)")
    axes[0, 1].set_xlabel("$V_{\\mathrm{OUT}}$ (V)")
    axes[0, 1].set_ylabel("Ocorrências")
    axes[0, 1].legend(fontsize=8.5)
    axes[0, 1].grid(True, alpha=0.3)

    # [1,0] Mapa de calor da varredura paramétrica Ngspice (VDD x VSS -> Margem)
    piv = df_sweep.pivot(index="VSS_V", columns="VDD_V", values="Margem_V")
    im = axes[1, 0].imshow(piv.values, origin="lower", aspect="auto", cmap="YlGnBu")
    axes[1, 0].set_xticks(range(len(piv.columns)))
    axes[1, 0].set_xticklabels([f"{c:.2f}" for c in piv.columns])
    axes[1, 0].set_yticks(range(len(piv.index)))
    axes[1, 0].set_yticklabels([f"{r:+.2f}" for r in piv.index])
    axes[1, 0].set_xlabel("$V_{DD}$ (V)")
    axes[1, 0].set_ylabel("$V_{SS}$ (V)")
    axes[1, 0].set_title("Validação Ngspice: Margem $(V_{00}-V_{11})$ vs. $(V_{DD}, V_{SS})$")
    for r_i in range(piv.shape[0]):
        for c_i in range(piv.shape[1]):
            axes[1, 0].text(c_i, r_i, f"{piv.values[r_i, c_i]:.2f}", ha="center", va="center", color="white" if piv.values[r_i, c_i] > 0.7 else "black", fontsize=8)
    fig.colorbar(im, ax=axes[1, 0], label="Margem (V)")

    # [1,1] Curvas de Retenção/Decaimento de Tensão Flutuante (100ns, 250ns, 500ns)
    float_files = [
        ("100ns_high_floating_voltage.csv", "Pulso 100 ns (Alto)", "#08519c"),
        ("250ns_medium_floating_voltage.csv", "Pulso 250 ns (Médio)", "#31a354"),
        ("500ns_low_floating_voltage.csv", "Pulso 500 ns (Baixo)", "#cb181d"),
    ]
    for fn, lbl, clr in float_files:
        df_fl = pd.read_csv(os.path.join(MCODE_DIR, fn))
        t_us = df_fl["bblc1 X"].values * 1e6
        v_fl = df_fl["bblc1 Y"].values
        # Subamostragem suave para plotagem limpa (janela pós-pulso)
        axes[1, 1].plot(t_us[::15], v_fl[::15], color=clr, lw=1.4, label=f"{lbl} (final={v_fl[-1]:.2f} V)")
    axes[1, 1].set_title("Dinâmica de Nó Flutuante (100 ns, 250 ns, 500 ns)")
    axes[1, 1].set_xlabel("Tempo ($\\mu\\mathrm{s}$)")
    axes[1, 1].set_ylabel("Tensão do Nó Flutuante `bblc1` (V)")
    axes[1, 1].legend(fontsize=8)
    axes[1, 1].grid(True, alpha=0.3)

    fig.suptitle("Estatística Monte Carlo, Validação Ngspice e Retenção em Nós Flutuantes", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(BASE_DIR, "fig4_histogramas_e_retencao.png"), dpi=200)
    plt.close(fig)

    return mc_stats


def main():
    df_sweep = run_ngspice_supply_sweep()
    dpa_stats = analyze_dpa_waveforms()
    mc_stats = analyze_robustness_and_floating(df_sweep)

    df_dpa = pd.DataFrame(dpa_stats)
    df_mc = pd.DataFrame(mc_stats)
    df_dpa.to_csv(os.path.join(BASE_DIR, "metricas_dpa.csv"), index=False)
    df_mc.to_csv(os.path.join(BASE_DIR, "metricas_seguranca_robustez.csv"), index=False)

    print("=== Metricas DPA ===")
    print(df_dpa.to_string(index=False))
    print("\n=== Metricas Monte Carlo (250 amostras por porta) ===")
    print(df_mc.to_string(index=False))
    print("\n=== Varredura Ngspice VDD x VSS ===")
    print(f"Margem minima={df_sweep['Margem_V'].min():.3f}V, Margem maxima={df_sweep['Margem_V'].max():.3f}V")
    print("Modulo 03 concluido com sucesso.")


if __name__ == "__main__":
    main()
