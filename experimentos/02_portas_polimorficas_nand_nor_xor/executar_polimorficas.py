"""
Módulo 02 — Portas Lógicas Polimórficas (NAND/NOR e XOR/XNOR) no Ngspice.

Implementa e simula em regime transiente (com comutação dinâmica de chave em tempo real)
as duas primitivas de segurança de hardware baseadas em BP SB-FET:
1. Porta Polimórfica NAND/NOR de 4 transistores (VDD = 0.8 V):
   - 0 ns a 20 ns (Key = 0): Modo NAND
   - 20 ns a 40 ns (Key = 1): Modo NOR (inversão de trilhos + inversão de polaridade)
2. Porta Polimórfica XOR/XNOR de 4 transistores (VDD = 1.5 V, Vin = 1.1 V, conforme ari_xor_poly.sp):
   - 0 ns a 20 ns (Key = 0): Modo XOR
   - 20 ns a 40 ns (Key = 1): Modo XNOR

Extrai tensões estacionárias para todas as combinações da tabela-verdade, correntes de pico,
potências médias e gera gráficos comparativos das formas de onda.
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


def build_and_run_nand_nor():
    """Gera e executa poly_nand_nor.sp (Key=0 -> NAND, Key=1 -> NOR)."""
    # 8 janelas de 5ns (total 40ns): Key=0 em 0..20ns, Key=1 em 20..40ns
    net = f"""* Porta Polimorfica NAND/NOR de 4 Transistores BP SB-FET (Comutacao Dinamica)
.include "{LIB_REL}"

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
"""
    with open(os.path.join(BASE_DIR, "poly_nand_nor.sp"), "w", encoding="utf-8") as f:
        f.write(net)
    run_ngspice("poly_nand_nor.sp")


def build_and_run_xor_xnor():
    """Gera e executa poly_xor_xnor.sp (Key=0 -> XOR, Key=1 -> XNOR)."""
    # Configuracao fiel a ari_xor_poly.sp / ari_xnor_poly.sp (VDD=1.5V, Vin=1.1V)
    net = f"""* Porta Polimorfica XOR/XNOR de 4 Transistores BP SB-FET (Comutacao Dinamica)
.include "{LIB_REL}"

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
"""
    with open(os.path.join(BASE_DIR, "poly_xor_xnor.sp"), "w", encoding="utf-8") as f:
        f.write(net)
    run_ngspice("poly_xor_xnor.sp")


def sample_window(t_ns, sig, t_start, t_end):
    """Retorna valor estacionário no fim da janela e pico na janela."""
    mask = (t_ns >= t_start) & (t_ns <= t_end)
    return float(sig[mask][-1]), float(np.max(np.abs(sig[mask])))


def analyze_and_plot():
    """Verifica todas as tabelas-verdade, calcula métricas e gera gráficos."""
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})

    d_nn = np.loadtxt(os.path.join(BASE_DIR, "poly_nand_nor.dat"), skiprows=1)
    d_xx = np.loadtxt(os.path.join(BASE_DIR, "poly_xor_xnor.dat"), skiprows=1)

    t_nn = d_nn[:, 0] * 1e9
    t_xx = d_xx[:, 0] * 1e9

    windows = [
        ("Key=0", "00", 0.0, 4.8),
        ("Key=0", "01", 5.0, 9.8),
        ("Key=0", "10", 10.0, 14.8),
        ("Key=0", "11", 15.0, 19.8),
        ("Key=1", "00", 20.0, 24.8),
        ("Key=1", "01", 25.0, 29.8),
        ("Key=1", "10", 30.0, 34.8),
        ("Key=1", "11", 35.0, 39.8),
    ]

    expected_nn = {
        ("Key=0", "00"): 1, ("Key=0", "01"): 1, ("Key=0", "10"): 1, ("Key=0", "11"): 0,
        ("Key=1", "00"): 1, ("Key=1", "01"): 0, ("Key=1", "10"): 0, ("Key=1", "11"): 0,
    }
    expected_xx = {
        ("Key=0", "00"): 0, ("Key=0", "01"): 1, ("Key=0", "10"): 1, ("Key=0", "11"): 0,
        ("Key=1", "00"): 1, ("Key=1", "01"): 0, ("Key=1", "10"): 0, ("Key=1", "11"): 1,
    }

    rows = []
    for key_lbl, ab, t0, t1 in windows:
        v_out_nn, _ = sample_window(t_nn, d_nn[:, 4], t0, t1)
        _, i_pk_top_nn = sample_window(t_nn, d_nn[:, 5], t0, t1)
        _, i_pk_bot_nn = sample_window(t_nn, d_nn[:, 6], t0, t1)
        logic_nn = 1 if v_out_nn > 0.4 else 0
        func_nn = "NAND" if key_lbl == "Key=0" else "NOR"
        rows.append({
            "Porta": "NAND/NOR (0.8V)",
            "Chave": key_lbl,
            "Funcao": func_nn,
            "Entradas_AB": ab,
            "Vout_V": v_out_nn,
            "Bit_Medido": logic_nn,
            "Bit_Esperado": expected_nn[(key_lbl, ab)],
            "Correto": logic_nn == expected_nn[(key_lbl, ab)],
            "I_pico_uA": max(i_pk_top_nn, i_pk_bot_nn) * 1e6,
        })

        v_out_xx, _ = sample_window(t_xx, d_xx[:, 4], t0, t1)
        _, i_pk_top_xx = sample_window(t_xx, d_xx[:, 5], t0, t1)
        _, i_pk_bot_xx = sample_window(t_xx, d_xx[:, 6], t0, t1)
        logic_xx = 1 if v_out_xx > 0.75 else 0
        func_xx = "XOR" if key_lbl == "Key=0" else "XNOR"
        rows.append({
            "Porta": "XOR/XNOR (1.5V)",
            "Chave": key_lbl,
            "Funcao": func_xx,
            "Entradas_AB": ab,
            "Vout_V": v_out_xx,
            "Bit_Medido": logic_xx,
            "Bit_Esperado": expected_xx[(key_lbl, ab)],
            "Correto": logic_xx == expected_xx[(key_lbl, ab)],
            "I_pico_uA": max(i_pk_top_xx, i_pk_bot_xx) * 1e6,
        })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(BASE_DIR, "metricas_polimorficas.csv"), index=False)
    print(df.to_string(index=False))

    if not df["Correto"].all():
        raise RuntimeError("Falha na verificacao da tabela-verdade das portas polimorficas!")

    # --- Figura 1: NAND / NOR ---
    fig, axes = plt.subplots(5, 1, figsize=(11.5, 9), sharex=True)
    axes[0].plot(t_nn, d_nn[:, 1], "k", lw=1.8)
    axes[0].set_ylabel("$V(A)\\ (\\mathrm{V})$")
    axes[0].set_ylim(-0.1, 1.0)
    axes[0].set_title("Transmutação Dinâmica em Tempo Real: Porta Polimórfica NAND ($\\mathrm{Key}=0$) $\\leftrightarrow$ NOR ($\\mathrm{Key}=1$)", fontweight="bold")

    axes[1].plot(t_nn, d_nn[:, 2], "k", lw=1.8)
    axes[1].set_ylabel("$V(B)\\ (\\mathrm{V})$")
    axes[1].set_ylim(-0.1, 1.0)

    axes[2].plot(t_nn, d_nn[:, 3], "#6a51a3", lw=2.0)
    axes[2].set_ylabel("$\\mathrm{Key}\\ (\\mathrm{V})$")
    axes[2].set_ylim(-0.1, 1.0)
    axes[2].text(10.0, 0.45, "Key = 0 → Modo NAND", color="#08519c", fontweight="bold", ha="center")
    axes[2].text(30.0, 0.45, "Key = 1 → Modo NOR", color="#a50f15", fontweight="bold", ha="center")

    axes[3].plot(t_nn, d_nn[:, 4], "#08519c", lw=2.2)
    axes[3].axvline(20.0, color="gray", ls="--", lw=1.2)
    axes[3].set_ylabel("$V(\\mathrm{out})\\ (\\mathrm{V})$")
    axes[3].set_ylim(-0.1, 1.0)

    axes[4].plot(t_nn, np.abs(d_nn[:, 5]) * 1e6, "#08519c", lw=1.5, label="$|I(\\mathrm{rail}_{\\mathrm{top}})|$")
    axes[4].plot(t_nn, np.abs(d_nn[:, 6]) * 1e6, "#e6550d", lw=1.5, ls="--", label="$|I(\\mathrm{rail}_{\\mathrm{bot}})|$")
    axes[4].axvline(20.0, color="gray", ls="--", lw=1.2)
    axes[4].set_ylabel("Corrente ($\\mu\\mathrm{A}$)")
    axes[4].set_xlabel("Tempo (ns)")
    axes[4].legend(loc="upper right", fontsize=8.5)

    fig.tight_layout()
    fig.savefig(os.path.join(BASE_DIR, "fig1_nand_nor_dinamico.png"), dpi=200)
    plt.close(fig)

    # --- Figura 2: XOR / XNOR ---
    fig, axes = plt.subplots(5, 1, figsize=(11.5, 9), sharex=True)
    axes[0].plot(t_xx, d_xx[:, 1], "k", lw=1.8)
    axes[0].set_ylabel("$V(A)\\ (\\mathrm{V})$")
    axes[0].set_ylim(-0.1, 1.35)
    axes[0].set_title("Transmutação Dinâmica em Tempo Real: Porta Polimórfica XOR ($\\mathrm{Key}=0$) $\\leftrightarrow$ XNOR ($\\mathrm{Key}=1$)", fontweight="bold")

    axes[1].plot(t_xx, d_xx[:, 2], "k", lw=1.8)
    axes[1].set_ylabel("$V(B)\\ (\\mathrm{V})$")
    axes[1].set_ylim(-0.1, 1.35)

    axes[2].plot(t_xx, d_xx[:, 3], "#6a51a3", lw=2.0)
    axes[2].set_ylabel("$\\mathrm{Key}\\ (\\mathrm{V})$")
    axes[2].set_ylim(-0.15, 1.75)
    axes[2].text(10.0, 0.85, "Key = 0 → Modo XOR", color="#08519c", fontweight="bold", ha="center")
    axes[2].text(30.0, 0.85, "Key = 1 → Modo XNOR", color="#238b45", fontweight="bold", ha="center")

    axes[3].plot(t_xx, d_xx[:, 4], "#238b45", lw=2.2)
    axes[3].axvline(20.0, color="gray", ls="--", lw=1.2)
    axes[3].set_ylabel("$V(\\mathrm{out})\\ (\\mathrm{V})$")
    axes[3].set_ylim(-0.15, 1.75)

    axes[4].plot(t_xx, np.abs(d_xx[:, 5]) * 1e6, "#08519c", lw=1.5, label="$|I(\\mathrm{rail}_{\\mathrm{top}})|$")
    axes[4].plot(t_xx, np.abs(d_xx[:, 6]) * 1e6, "#e6550d", lw=1.5, ls="--", label="$|I(\\mathrm{rail}_{\\mathrm{bot}})|$")
    axes[4].axvline(20.0, color="gray", ls="--", lw=1.2)
    axes[4].set_ylabel("Corrente ($\\mu\\mathrm{A}$)")
    axes[4].set_xlabel("Tempo (ns)")
    axes[4].legend(loc="upper right", fontsize=8.5)

    fig.tight_layout()
    fig.savefig(os.path.join(BASE_DIR, "fig2_xor_xnor_dinamico.png"), dpi=200)
    plt.close(fig)


def main():
    build_and_run_nand_nor()
    build_and_run_xor_xnor()
    analyze_and_plot()
    print("Modulo 02 concluido com sucesso.")


if __name__ == "__main__":
    main()
