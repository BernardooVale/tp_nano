"""
Módulo 01 — Inversor Lógico Complementar 2D BP SB-FET em Ultra-Baixa Tensão (1.0 V até 0.2 V).

Simula no ngspice-47 o inversor complementar baseado na biblioteca bp_ari_ngspice.lib:
1. Análise DC (Curva de Transferência de Tensão - VTC) para VDD = 1.0, 0.8, 0.6, 0.4 e 0.2 V:
   - Configuração A (Sem compensação de banda plana Vfb): entrada direta V(in).
   - Configuração B (Com compensação eletrostática de banda plana Vfb): alinhamento simétrico
     das tensões de limiar dos ramos n-FET e p-FET para viabilizar operação sub-0.4 V até 0.2 V.
2. Análise de ganho diferencial |dVout/dVin|, tensão de inversão V_M e margens de ruído (NM_H, NM_L).
3. Análise transiente de chaveamento sob VDD = 1.0 V e VDD = 0.6 V (tempos de subida/descida e I_DD).
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

VDD_LIST = [1.0, 0.8, 0.6, 0.4, 0.2]


def run_ngspice(sp_filename):
    """Executa uma netlist no ngspice_con.exe."""
    sp_path = os.path.join(BASE_DIR, sp_filename)
    subprocess.run(
        [NGSPICE_EXE, "-b", sp_path],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=True,
    )


def build_and_run_vtc():
    """Gera e executa inv_vtc.sp para todas as tensões VDD (sem e com compensação Vfb)."""
    lines = [
        "* Caracterizacao DC (VTC) do Inversor Complementar BP SB-FET (VDD = 1.0V a 0.2V)",
        f'.include "{LIB_REL}"',
        "",
        ".param supp=1.0",
        ".param offn=0.0",
        ".param offp=0.0",
        "Vdd vdd 0 {supp}",
        "Vss vss 0 0",
        "Vin in 0 0",
        "",
        "* Fontes de compensacao de banda plana (Vfb)",
        "Egn gn 0 VOL = 'v(in) + offn'",
        "Egp gp 0 VOL = 'v(in) + offp'",
        "",
        "* Polarizacao nominal de g1 e g2 para p-FET (pull-up) e n-FET (pull-down)",
        "Vg1p g1p 0 {supp - 1.5}",
        "Vg2p g2p 0 {supp - 1.2}",
        "Vg1n g1n 0 1.1",
        "Vg2n g2n 0 0.8",
        "",
        "XPU out gp vdd g1p g2p ARI W=1.0",
        "XPD out gn vss g1n g2n ARI W=1.0",
        "",
        ".control",
        "set wr_vecnames",
        "set wr_singlescale",
    ]

    # Configuracao A: Sem compensacao Vfb (porta comum direta)
    for vdd in VDD_LIST:
        tag = f"{vdd:.1f}".replace(".", "d")
        lines.extend([
            f"alterparam supp = {vdd}",
            "alterparam offn = 0.0",
            "alterparam offp = 0.0",
            "reset",
            f"dc Vin 0 {vdd} 0.002",
            f"wrdata vtc_direto_vdd{tag}.dat v(out)",
        ])

    # Configuracao B: Com compensacao eletrostatica Vfb (alinhando no regime de sublimiar maximo)
    for vdd in VDD_LIST:
        tag = f"{vdd:.1f}".replace(".", "d")
        # Alinhamento para que em Vin=VDD/2: Vgs_n_eff = -0.02V e Vgs_p_eff = -0.58V
        offn = -0.02 - 0.5 * vdd
        offp = 0.5 * vdd - 0.58
        lines.extend([
            f"alterparam supp = {vdd}",
            f"alterparam offn = {offn:.4f}",
            f"alterparam offp = {offp:.4f}",
            "reset",
            f"dc Vin 0 {vdd} 0.002",
            f"wrdata vtc_comp_vdd{tag}.dat v(out)",
        ])

    lines.extend([".endc", ".end", ""])
    with open(os.path.join(BASE_DIR, "inv_vtc.sp"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    run_ngspice("inv_vtc.sp")


def build_and_run_transient():
    """Gera e executa inv_tran.sp para chaveamento transiente a VDD=1.0V e VDD=0.6V."""
    lines = [
        "* Simulacao Transiente do Inversor Complementar BP SB-FET",
        f'.include "{LIB_REL}"',
        "",
        ".param supp=1.0",
        ".param offn=-0.32",
        ".param offp=-0.18",
        "Vdd vdd 0 {supp}",
        "Vss vss 0 0",
        "Vin in 0 pwl(0n 0 2n 0 2.2n {supp} 8n {supp} 8.2n 0 14n 0)",
        "",
        "Egn gn 0 VOL = 'v(in) + offn'",
        "Egp gp 0 VOL = 'v(in) + offp'",
        "",
        "Vg1p g1p 0 {supp - 1.5}",
        "Vg2p g2p 0 {supp - 1.2}",
        "Vg1n g1n 0 1.1",
        "Vg2n g2n 0 0.8",
        "",
        "XPU out gp vdd g1p g2p ARI W=1.0",
        "XPD out gn vss g1n g2n ARI W=1.0",
        "Cload out 0 0.5f",
        "",
        ".control",
        "set wr_vecnames",
        "set wr_singlescale",
    ]
    for vdd in [1.0, 0.6]:
        tag = f"{vdd:.1f}".replace(".", "d")
        offn = -0.02 - 0.5 * vdd
        offp = 0.5 * vdd - 0.58
        lines.extend([
            f"alterparam supp = {vdd}",
            f"alterparam offn = {offn:.4f}",
            f"alterparam offp = {offp:.4f}",
            "reset",
            "tran 20p 14n",
            f"wrdata inv_tran_vdd{tag}.dat v(in) v(out) i(Vdd)",
        ])
    lines.extend([".endc", ".end", ""])
    with open(os.path.join(BASE_DIR, "inv_tran.sp"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    run_ngspice("inv_tran.sp")


def extract_vtc_metrics(vin, vout, vdd):
    """Extrai VTC metrics: V_M, ganho máximo, NM_L, NM_H e excursão."""
    dv = np.gradient(vout, vin)
    gain = np.abs(dv)
    max_gain = float(np.max(gain))
    idx_vm = int(np.argmin(np.abs(vout - vin)))
    vm = float(vin[idx_vm])
    swing_pct = float((vout[0] - vout[-1]) / vdd * 100.0)

    # Pontos onde derivada dVout/dVin = -1 (para NM_L e NM_H)
    idx_slope = np.where(dv <= -1.0)[0]
    if len(idx_slope) >= 2:
        vil = float(vin[idx_slope[0]])
        voh = float(vout[idx_slope[0]])
        vih = float(vin[idx_slope[-1]])
        vol = float(vout[idx_slope[-1]])
        nml = vil - vol
        nmh = voh - vih
    else:
        nml = 0.0
        nmh = 0.0
    return {
        "Vout_0_V": float(vout[0]),
        "Vout_VDD_V": float(vout[-1]),
        "Excursao_pct": swing_pct,
        "V_M_V": vm,
        "Ganho_Max": max_gain,
        "NM_L_V": float(max(nml, 0.0)),
        "NM_H_V": float(max(nmh, 0.0)),
    }


def analyze_and_plot():
    """Analisa os arquivos gerados pelo ngspice e produz figuras e CSV."""
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})
    rows_metrics = []

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 9))
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(VDD_LIST)))

    for idx, vdd in enumerate(VDD_LIST):
        tag = f"{vdd:.1f}".replace(".", "d")

        # Sem compensação
        d_dir = np.loadtxt(os.path.join(BASE_DIR, f"vtc_direto_vdd{tag}.dat"), skiprows=1)
        m_dir = extract_vtc_metrics(d_dir[:, 0], d_dir[:, 1], vdd)
        m_dir.update({"Configuracao": "Direto (Sem compensacao Vfb)", "VDD_V": vdd})
        rows_metrics.append(m_dir)

        gain_dir = np.abs(np.gradient(d_dir[:, 1], d_dir[:, 0]))
        axes[0, 0].plot(d_dir[:, 0], d_dir[:, 1], color=colors[idx], lw=2.0, label=f"$V_{{DD}}={vdd:.1f}\\,\\mathrm{{V}}$")
        axes[1, 0].plot(d_dir[:, 0], gain_dir, color=colors[idx], lw=2.0, label=f"$V_{{DD}}={vdd:.1f}\\,\\mathrm{{V}}$ (máx={m_dir['Ganho_Max']:.2f})")

        # Com compensação
        d_cmp = np.loadtxt(os.path.join(BASE_DIR, f"vtc_comp_vdd{tag}.dat"), skiprows=1)
        m_cmp = extract_vtc_metrics(d_cmp[:, 0], d_cmp[:, 1], vdd)
        m_cmp.update({"Configuracao": "Compensado (Alinhamento Vfb)", "VDD_V": vdd})
        rows_metrics.append(m_cmp)

        gain_cmp = np.abs(np.gradient(d_cmp[:, 1], d_cmp[:, 0]))
        axes[0, 1].plot(d_cmp[:, 0], d_cmp[:, 1], color=colors[idx], lw=2.0, label=f"$V_{{DD}}={vdd:.1f}\\,\\mathrm{{V}}$")
        axes[1, 1].plot(d_cmp[:, 0], gain_cmp, color=colors[idx], lw=2.0, label=f"$V_{{DD}}={vdd:.1f}\\,\\mathrm{{V}}$ (máx={m_cmp['Ganho_Max']:.2f})")

    axes[0, 0].set_title("VTC Direto (Sem Compensação $V_{fb}$)")
    axes[0, 0].set_xlabel("$V_{\\mathrm{in}}\\ (\\mathrm{V})$")
    axes[0, 0].set_ylabel("$V_{\\mathrm{out}}\\ (\\mathrm{V})$")
    axes[0, 0].legend(fontsize=8.5)

    axes[0, 1].set_title("VTC com Compensação Eletrostática de $V_{fb}$ ($0,2\\text{ a }1,0\\,\\mathrm{V}$)")
    axes[0, 1].set_xlabel("$V_{\\mathrm{in}}\\ (\\mathrm{V})$")
    axes[0, 1].set_ylabel("$V_{\\mathrm{out}}\\ (\\mathrm{V})$")
    axes[0, 1].legend(fontsize=8.5)

    axes[1, 0].set_title("Ganho de Tensão $|dV_{\\mathrm{out}}/dV_{\\mathrm{in}}|$ (Direto)")
    axes[1, 0].set_xlabel("$V_{\\mathrm{in}}\\ (\\mathrm{V})$")
    axes[1, 0].set_ylabel("Ganho $|A_v|$")
    axes[1, 0].axhline(1.0, color="red", ls="--", lw=1.0, alpha=0.7, label="Limite $A_v=1$")
    axes[1, 0].legend(fontsize=8)

    axes[1, 1].set_title("Ganho de Tensão $|dV_{\\mathrm{out}}/dV_{\\mathrm{in}}|$ (Compensado)")
    axes[1, 1].set_xlabel("$V_{\\mathrm{in}}\\ (\\mathrm{V})$")
    axes[1, 1].set_ylabel("Ganho $|A_v|$")
    axes[1, 1].axhline(1.0, color="red", ls="--", lw=1.0, alpha=0.7, label="Limite $A_v=1$")
    axes[1, 1].legend(fontsize=8)

    fig.suptitle("Inversor Complementar BP SB-FET: Escalonamento de Tensão ($V_{DD} = 1,0\\,\\mathrm{V}$ até $0,2\\,\\mathrm{V}$)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(BASE_DIR, "fig1_inversor_vtc_ganho.png"), dpi=200)
    plt.close(fig)

    # --- Figura 2: Transiente ---
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for col_idx, (vdd, clr) in enumerate([(1.0, "#08519c"), (0.6, "#2ca25f")]):
        tag = f"{vdd:.1f}".replace(".", "d")
        tr = np.loadtxt(os.path.join(BASE_DIR, f"inv_tran_vdd{tag}.dat"), skiprows=1)
        t_ns = tr[:, 0] * 1e9
        vin = tr[:, 1]
        vout = tr[:, 2]
        idd_ua = -tr[:, 3] * 1e6

        axes[0, col_idx].plot(t_ns, vin, "k--", lw=1.5, label="$V_{\\mathrm{in}}(t)$")
        axes[0, col_idx].plot(t_ns, vout, color=clr, lw=2.2, label="$V_{\\mathrm{out}}(t)$")
        axes[0, col_idx].set_title(f"Chaveamento Lógico ($V_{{DD}}={vdd:.1f}\\,\\mathrm{{V}}$)")
        axes[0, col_idx].set_ylabel("Tensão (V)")
        axes[0, col_idx].set_ylim(-0.08, vdd + 0.15)
        axes[0, col_idx].legend(fontsize=8.5)

        axes[1, col_idx].plot(t_ns, idd_ua, color="#d95f0e", lw=1.8, label="$I(V_{DD})$")
        axes[1, col_idx].set_title(f"Corrente de Alimentação ($I_{{\\mathrm{{pico}}}}={np.max(idd_ua):.2f}\\,\\mu\\mathrm{{A}}$)")
        axes[1, col_idx].set_xlabel("Tempo (ns)")
        axes[1, col_idx].set_ylabel("$I_{DD}\\ (\\mu\\mathrm{A})$")
        axes[1, col_idx].legend(fontsize=8.5)

    fig.suptitle("Resposta Transiente e Consumo Dinâmico do Inversor BP SB-FET", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(BASE_DIR, "fig2_inversor_transiente.png"), dpi=200)
    plt.close(fig)

    df = pd.DataFrame(rows_metrics)[
        ["Configuracao", "VDD_V", "Vout_0_V", "Vout_VDD_V", "Excursao_pct", "V_M_V", "Ganho_Max", "NM_L_V", "NM_H_V"]
    ]
    df.to_csv(os.path.join(BASE_DIR, "metricas_inversor.csv"), index=False)
    print(df.to_string(index=False))


def main():
    build_and_run_vtc()
    build_and_run_transient()
    analyze_and_plot()
    print("Modulo 01 concluido com sucesso.")


if __name__ == "__main__":
    main()
