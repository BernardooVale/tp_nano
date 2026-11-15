import os
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
NGSPICE_EXE = os.path.join(ROOT_DIR, "ngspice-47_64", "Spice64", "bin", "ngspice_con.exe")
LIB_REL = "../00_modelo_ngspice/bp_ari_ngspice.lib"

KEYS = [
    ("00", 0, 0, "K=00 (XOR + NAND — Correta)"),
    ("01", 0, 1, "K=01 (XNOR + NAND)"),
    ("10", 1, 0, "K=10 (XOR + NOR)"),
    ("11", 1, 1, "K=11 (XNOR + NOR)"),
]


def run_ngspice(sp_filename):
    """Executa netlist SPICE no ngspice em modo batch e valida saída."""
    proc = subprocess.run(
        [NGSPICE_EXE, "-b", sp_filename],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ngspice falhou ({proc.returncode}) em {sp_filename}:\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    if "Transient analysis" in proc.stdout or "Doing analysis" in proc.stdout:
        if "aborted" in proc.stderr.lower():
            raise RuntimeError(f"Simulação abortada pelo ngspice:\n{proc.stderr}")
    return proc.stdout


def build_and_run_full_adder():
    """Gera e simula full_adder_polimorfico.sp para todas as 4 chaves K1K0."""
    net = f"""* Somador Completo (Full Adder 1-bit) Polimorfico com Ofuscacao Logica 2-bits (K1, K0)
* Arquitetura: 2x XOR/XNOR 4T + 4x Inversores 2T de Condicionamento + 3x NAND/NOR 4T (28 BP SB-FETs)
.include "{LIB_REL}"

* Parametros padrao correspondentes a Chave Correta K1=0 (NAND), K0=0 (XOR)
.param pxrtop1 = 1.5
.param pxgtop1 = 0.0
.param pxrbot1 = 0.0
.param pxgbot1 = 0.8

.param pnrtop  = 0.8
.param pngtop  = -0.4
.param pnrbot  = 0.0
.param pngbot  = 0.8

* --- Subcircuitos Polimorficos e de Condicionamento ---
.subckt POLY_XOR a an b bn out rtop gtop rbot gbot
X1 out an rtop b  gtop ARI W=1.0
X2 out a  rtop bn gtop ARI W=1.0
X3 out a  rbot b  gbot ARI W=1.0
X4 out an rbot bn gbot ARI W=1.0
Cout out 0 0.2f
.ends POLY_XOR

.subckt POLY_NAND_NOR a b out rtop gtop rbot gbot
X1 out a rtop gtop gtop ARI W=1.0
X2 out b rtop gtop gtop ARI W=1.0
X3 out b n1   gbot gbot ARI W=2.0
X4 n1  a rbot gbot gbot ARI W=2.0
Cout out 0 0.2f
Cn1  n1  0 0.05f
.ends POLY_NAND_NOR

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

* Alimentacoes principais
Vdd08 vdd08 0 0.8
Vdd11 vdd11 0 1.1
Vss   vss   0 0.0

* Trilhos e polarizacoes das chaves K0 (XXOR1) e K1 (XG1..XG3)
Vxrtop1 xrtop1 0 {{pxrtop1}}
Vxgtop1 xgtop1 0 {{pxgtop1}}
Vxrbot1 xrbot1 0 {{pxrbot1}}
Vxgbot1 xgbot1 0 {{pxgbot1}}

Vxrtop2 xrtop2 0 1.5
Vxgtop2 xgtop2 0 0.0
Vxrbot2 xrbot2 0 0.0
Vxgbot2 xgbot2 0 0.8

Vnrtop  nrtop  0 {{pnrtop}}
Vngtop  ngtop  0 {{pngtop}}
Vnrbot  nrbot  0 {{pnrbot}}
Vngbot  ngbot  0 {{pngbot}}

* Padrao exaustivo de 8 vetores (A, B, Cin) de 5ns cada -> 40ns totais
Va11  a11  0 pwl(0n 0 19.9n 0 20.0n 1.1 40n 1.1)
Van11 an11 0 pwl(0n 1.1 19.9n 1.1 20.0n 0 40n 0)
Vb11  b11  0 pwl(0n 0 9.9n 0 10.0n 1.1 19.9n 1.1 20.0n 0 29.9n 0 30.0n 1.1 40n 1.1)
Vbn11 bn11 0 pwl(0n 1.1 9.9n 1.1 10.0n 0 19.9n 0 20.0n 1.1 29.9n 1.1 30.0n 0 40n 0)
Vc11  c11  0 pwl(0n 0 4.9n 0 5.0n 1.1 9.9n 1.1 10.0n 0 14.9n 0 15.0n 1.1 19.9n 1.1 20.0n 0 24.9n 0 25.0n 1.1 29.9n 1.1 30.0n 0 34.9n 0 35.0n 1.1 40n 1.1)
Vcn11 cn11 0 pwl(0n 1.1 4.9n 1.1 5.0n 0 9.9n 0 10.0n 1.1 14.9n 1.1 15.0n 0 19.9n 0 20.0n 1.1 24.9n 1.1 25.0n 0 29.9n 0 30.0n 1.1 34.9n 1.1 35.0n 0 40n 0)

Va08  a08  0 pwl(0n 0 19.9n 0 20.0n 0.8 40n 0.8)
Vb08  b08  0 pwl(0n 0 9.9n 0 10.0n 0.8 19.9n 0.8 20.0n 0 29.9n 0 30.0n 0.8 40n 0.8)
Vc08  c08  0 pwl(0n 0 4.9n 0 5.0n 0.8 9.9n 0.8 10.0n 0 14.9n 0 15.0n 0.8 19.9n 0.8 20.0n 0 24.9n 0 25.0n 0.8 29.9n 0.8 30.0n 0 34.9n 0 35.0n 0.8 40n 0.8)

* Estagio 1: XXOR1 polimorfico (K0=0 -> XOR, K0=1 -> XNOR) + Condicionamento p/ 0.8V e 1.1V
XXOR1 a11 an11 b11 bn11 p_raw xrtop1 xgtop1 xrbot1 xgbot1 POLY_XOR
XINV1 p_raw pn08 vdd08 vss BP_INV08
XINV2 pn08  p08  vdd08 vss BP_INV08
XINV3 p08   pn11 vdd11 vss BP_INV11
XINV4 pn08  p11  vdd11 vss BP_INV11

* Estagio 2: Soma Sum = P (+) Cin
XXOR2 p11 pn11 c11 cn11 sum_out xrtop2 xgtop2 xrbot2 xgbot2 POLY_XOR

* Estagio 3: Arvore Carry-Out com 3 portas NAND/NOR polimorficas (K1=0 -> NAND, K1=1 -> NOR)
XG1 a08    b08    g1_out   nrtop ngtop nrbot ngbot POLY_NAND_NOR
XG2 p08    c08    g2_out   nrtop ngtop nrbot ngbot POLY_NAND_NOR
XG3 g1_out g2_out cout_out nrtop ngtop nrbot ngbot POLY_NAND_NOR

.control
set wr_vecnames
set wr_singlescale

* 1) Chave K1K0 = 00 (XOR + NAND -> Somador Completo Exato)
tran 20p 40n
wrdata fa_k00.dat v(a08) v(b08) v(c08) v(p08) v(sum_out) v(cout_out) i(Vxrtop1) i(Vnrtop)

* 2) Chave K1K0 = 01 (XNOR + NAND)
alterparam pxrtop1 = 0.0
alterparam pxgtop1 = 0.8
alterparam pxrbot1 = 1.5
alterparam pxgbot1 = 0.0
reset
tran 20p 40n
wrdata fa_k01.dat v(a08) v(b08) v(c08) v(p08) v(sum_out) v(cout_out) i(Vxrtop1) i(Vnrtop)

* 3) Chave K1K0 = 10 (XOR + NOR)
alterparam pxrtop1 = 1.5
alterparam pxgtop1 = 0.0
alterparam pxrbot1 = 0.0
alterparam pxgbot1 = 0.8
alterparam pnrtop  = 0.0
alterparam pngtop  = 0.8
alterparam pnrbot  = 0.8
alterparam pngbot  = -0.7
reset
tran 20p 40n
wrdata fa_k10.dat v(a08) v(b08) v(c08) v(p08) v(sum_out) v(cout_out) i(Vxrtop1) i(Vnrtop)

* 4) Chave K1K0 = 11 (XNOR + NOR)
alterparam pxrtop1 = 0.0
alterparam pxgtop1 = 0.8
alterparam pxrbot1 = 1.5
alterparam pxgbot1 = 0.0
reset
tran 20p 40n
wrdata fa_k11.dat v(a08) v(b08) v(c08) v(p08) v(sum_out) v(cout_out) i(Vxrtop1) i(Vnrtop)
.endc
.end
"""
    sp_path = os.path.join(BASE_DIR, "full_adder_polimorfico.sp")
    with open(sp_path, "w", encoding="utf-8") as f:
        f.write(net)
    run_ngspice("full_adder_polimorfico.sp")


def analyze_and_plot():
    """Analisa tabelas-verdade, distâncias de Hamming e gera gráficos."""
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})

    datasets = {}
    rows = []
    hamming_summary = []

    oracle_sum = []
    oracle_cout = []
    for i in range(8):
        a = (i >> 2) & 1
        b = (i >> 1) & 1
        cin = i & 1
        oracle_sum.append(a ^ b ^ cin)
        oracle_cout.append((a & b) | (cin & (a ^ b)))

    for key_str, k1, k0, key_lbl in KEYS:
        dat = np.loadtxt(os.path.join(BASE_DIR, f"fa_k{key_str}.dat"), skiprows=1)
        t_ns = dat[:, 0] * 1e9
        datasets[key_str] = dat

        hd_sum = 0
        hd_cout = 0
        vsum_list, vcout_list = [], []
        bsum_list, bcout_list = [], []

        for i in range(8):
            t_start = i * 5.0 + 3.5
            t_end = i * 5.0 + 4.8
            mask = (t_ns >= t_start) & (t_ns <= t_end)
            va = float(np.mean(dat[mask, 1]))
            vb = float(np.mean(dat[mask, 2]))
            vc = float(np.mean(dat[mask, 3]))
            vp = float(np.mean(dat[mask, 4]))
            vsum = float(np.mean(dat[mask, 5]))
            vcout = float(np.mean(dat[mask, 6]))

            a_in = 1 if va > 0.4 else 0
            b_in = 1 if vb > 0.4 else 0
            c_in = 1 if vc > 0.4 else 0
            s_bit = 1 if vsum > 0.75 else 0
            co_bit = 1 if vcout > 0.40 else 0

            exp_s = a_in ^ b_in ^ c_in
            exp_co = (a_in & b_in) | (c_in & (a_in ^ b_in))
            err_s = int(s_bit != exp_s)
            err_co = int(co_bit != exp_co)
            hd_sum += err_s
            hd_cout += err_co

            vsum_list.append(vsum)
            vcout_list.append(vcout)
            bsum_list.append(s_bit)
            bcout_list.append(co_bit)

            rows.append({
                "Chave_K1K0": key_str,
                "K1": k1,
                "K0": k0,
                "A": a_in,
                "B": b_in,
                "Cin": c_in,
                "Mintermo": f"{a_in}{b_in}{c_in}",
                "V_P (V)": round(vp, 4),
                "V_Sum (V)": round(vsum, 4),
                "V_Cout (V)": round(vcout, 4),
                "Sum_Sim": s_bit,
                "Cout_Sim": co_bit,
                "Sum_Oraculo": exp_s,
                "Cout_Oraculo": exp_co,
                "Erro_Sum": err_s,
                "Erro_Cout": err_co,
                "Correto": (err_s == 0) and (err_co == 0),
            })

        hd_tot = hd_sum + hd_cout
        hamming_summary.append({
            "Chave_K1K0": key_str,
            "Descricao": key_lbl,
            "HD_Sum_Bits": hd_sum,
            "HD_Sum_%": 100.0 * hd_sum / 8.0,
            "HD_Cout_Bits": hd_cout,
            "HD_Cout_%": 100.0 * hd_cout / 8.0,
            "HD_Total_Bits": hd_tot,
            "HD_Total_%": 100.0 * hd_tot / 16.0,
            "Acuracia_FA_%": 100.0 * (16 - hd_tot) / 16.0,
        })

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(BASE_DIR, "tabelas_verdade_full_adder.csv"), index=False)
    df_hd = pd.DataFrame(hamming_summary)
    print(df_hd.to_string(index=False))

    # Validações estritas
    k00 = df[df["Chave_K1K0"] == "00"]
    assert k00["Correto"].all(), "Chave K=00 nao reproduziu 100% da tabela-verdade do Full Adder!"
    vsum_00_hi = k00[k00["Sum_Sim"] == 1]["V_Sum (V)"].min()
    vsum_00_lo = k00[k00["Sum_Sim"] == 0]["V_Sum (V)"].max()
    vcout_00_hi = k00[k00["Cout_Sim"] == 1]["V_Cout (V)"].min()
    vcout_00_lo = k00[k00["Cout_Sim"] == 0]["V_Cout (V)"].max()
    print(f"K=00 niveis analogicos: Sum=('0'<={vsum_00_lo:.3f}V, '1'>={vsum_00_hi:.3f}V), "
          f"Cout=('0'<={vcout_00_lo:.3f}V, '1'>={vcout_00_hi:.3f}V)")

    for row in hamming_summary:
        if row["Chave_K1K0"] != "00":
            assert row["HD_Total_Bits"] > 0, f"Chave incorreta {row['Chave_K1K0']} nao ofuscou o circuito!"

    # --- Figura 1: Formas de onda transientes (Entradas + 4 chaves) ---
    fig, axes = plt.subplots(5, 1, figsize=(12.5, 10.5), sharex=True)
    d00 = datasets["00"]
    t0 = d00[:, 0] * 1e9

    # Painel 0: Entradas A, B, Cin
    axes[0].plot(t0, d00[:, 1], "#08519c", lw=2.0, label="$A$ ($0,8\\,\\mathrm{V}$)")
    axes[0].plot(t0, d00[:, 2], "#31a354", lw=1.8, ls="--", label="$B$")
    axes[0].plot(t0, d00[:, 3], "#e6550d", lw=1.5, ls=":", label="$C_{\\mathrm{in}}$")
    axes[0].set_ylabel("Entradas (V)")
    axes[0].set_ylim(-0.08, 1.15)
    axes[0].legend(loc="lower center", bbox_to_anchor=(0.5, 1.03), ncol=3, fontsize=8.8, framealpha=0.95)
    for i in range(8):
        lbl = f"{(i>>2)&1}{(i>>1)&1}{i&1}"
        axes[0].text(i * 5.0 + 2.5, 0.98, lbl, ha="center", va="center", fontsize=8.5, fontweight="bold",
                     bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#bbbbbb", alpha=0.88))
        if i > 0:
            for ax in axes:
                ax.axvline(i * 5.0, color="#aaaaaa", ls=":", lw=0.8)

    for idx_k, (key_str, _, _, key_lbl) in enumerate(KEYS):
        ax = axes[idx_k + 1]
        d = datasets[key_str]
        t = d[:, 0] * 1e9
        ax.plot(t, d[:, 5], "#08519c", lw=2.1, label="$V(\\mathrm{Sum})$ (Domínio $1,5\\,\\mathrm{V}$)")
        ax.plot(t, d[:, 6], "#cb181d", lw=2.0, ls="--", label="$V(C_{\\mathrm{out}})$ (Domínio $0,8\\,\\mathrm{V}$)")
        ax.set_ylabel(f"$K={key_str}$\nTensão (V)")
        ax.set_ylim(-0.08, 1.72)

        sub = df[df["Chave_K1K0"] == key_str].reset_index(drop=True)
        for i, r in sub.iterrows():
            ok = r["Correto"]
            bg = "#e8f8e8" if ok else "#fde0dd"
            ax.axvspan(i * 5.0, (i + 1) * 5.0, color=bg, alpha=0.35, zorder=0)
            tag = f"S={r['Sum_Sim']},C={r['Cout_Sim']}"
            txt_color = "#1b7837" if ok else "#a50f15"
            ax.text(i * 5.0 + 2.5, 1.56, tag, ha="center", va="center", fontsize=7.8, fontweight="bold", color=txt_color)

        if idx_k == 0:
            ax.legend(loc="lower left", ncol=2, fontsize=8.2, framealpha=0.92)
        ax.set_title(key_lbl, loc="right", fontsize=9.2, fontweight="bold", pad=2)

    axes[-1].set_xlabel("Tempo (ns) — Vetores de Teste Exaustivos $(A, B, C_{\\mathrm{in}}) = 000 \\rightarrow 111$")
    axes[-1].set_xlim(0.0, 40.0)
    fig.suptitle("Somador Completo Polimórfico (28 BP SB-FETs): Operação Correta em $K=00$ vs. Ofuscação em $K \\in \\{01, 10, 11\\}$",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.945])
    fig.savefig(os.path.join(BASE_DIR, "fig1_full_adder_waveforms.png"), dpi=200)
    plt.close(fig)

    # --- Figura 2: Matriz de Tabela-Verdade e Distância de Hamming ---
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.4), gridspec_kw={"width_ratios": [1.35, 1.0]})

    # Painel Esquerdo: Tabela visual colorida (8 mintermos x 4 chaves, 2 bits cada)
    col_labels = ["Oráculo\n(S, Co)", "K=00\n(S, Co)", "K=01\n(S, Co)", "K=10\n(S, Co)", "K=11\n(S, Co)"]
    row_labels = [f"{(i>>2)&1} {(i>>1)&1} {i&1}" for i in range(8)]
    color_mat = np.zeros((8, 5))
    text_mat = [["" for _ in range(5)] for _ in range(8)]

    for i in range(8):
        os_b, oc_b = oracle_sum[i], oracle_cout[i]
        color_mat[i, 0] = 0.0  # neutro oráculo
        text_mat[i][0] = f"({os_b}, {oc_b})"
        for col_idx, (key_str, _, _, _) in enumerate(KEYS, start=1):
            r = df[(df["Chave_K1K0"] == key_str)].iloc[i]
            s_b, c_b = int(r["Sum_Sim"]), int(r["Cout_Sim"])
            errs = int(r["Erro_Sum"]) + int(r["Erro_Cout"])
            color_mat[i, col_idx] = 1.0 if errs == 0 else (-1.0 if errs == 1 else -2.0)
            mark = "OK" if errs == 0 else ("1 err" if errs == 1 else "2 err")
            text_mat[i][col_idx] = f"({s_b}, {c_b}) {mark}"

    axes[0].grid(False)
    for r_idx in range(8):
        for c_idx in range(5):
            val = color_mat[r_idx, c_idx]
            if c_idx == 0:
                fc = "#deebf7"
                tc = "#08306b"
            elif val > 0:
                fc = "#c7e9c0"
                tc = "#00441b"
            elif val == -1.0:
                fc = "#fcbba1"
                tc = "#67000d"
            else:
                fc = "#fb6a4a"
                tc = "#ffffff"
            rect = patches.Rectangle((c_idx - 0.5, r_idx - 0.5), 1, 1, facecolor=fc, edgecolor="white", lw=1.5)
            axes[0].add_patch(rect)
            axes[0].text(c_idx, r_idx, text_mat[r_idx][c_idx], ha="center", va="center", fontsize=8.5, fontweight="bold", color=tc)

    axes[0].set_xlim(-0.5, 4.5)
    axes[0].set_ylim(7.5, -0.5)
    axes[0].set_xticks(range(5))
    axes[0].set_xticklabels(col_labels, fontsize=9, fontweight="bold")
    axes[0].set_yticks(range(8))
    axes[0].set_yticklabels(row_labels, fontsize=9, fontweight="bold")
    axes[0].set_ylabel("Entradas $(A\\ B\\ C_{\\mathrm{in}})$")
    axes[0].set_title("Matriz Tabela-Verdade $(S, C_{\\mathrm{out}})$ por Chave Criptográfica")

    # Painel Direito: Distância de Hamming por chave
    keys_x = [r["Chave_K1K0"] for r in hamming_summary]
    x = np.arange(len(keys_x))
    w = 0.27
    hd_s_pct = [r["HD_Sum_%"] for r in hamming_summary]
    hd_c_pct = [r["HD_Cout_%"] for r in hamming_summary]
    hd_t_pct = [r["HD_Total_%"] for r in hamming_summary]

    b1 = axes[1].bar(x - w, hd_s_pct, width=w, color="#2171b5", label="HD em $\\mathrm{Sum}$ (/8 bits)")
    b2 = axes[1].bar(x, hd_c_pct, width=w, color="#cb181d", label="HD em $C_{\\mathrm{out}}$ (/8 bits)")
    b3 = axes[1].bar(x + w, hd_t_pct, width=w, color="#6a51a3", label="HD Combinada (/16 bits)")

    for bars in [b1, b2, b3]:
        for bar in bars:
            h = bar.get_height()
            lbl_txt = "0%" if h == 0.0 else f"{h:.1f}%"
            axes[1].text(bar.get_x() + bar.get_width() / 2.0, h + 1.8, lbl_txt, ha="center", va="bottom", fontsize=7.6, fontweight="bold")

    axes[1].axhline(50.0, color="#555555", ls="--", lw=1.2, label="Alvo Criptográfico (50%)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([f"K={k}\n({'Correta' if k=='00' else 'Errada'})" for k in keys_x], fontweight="bold")
    axes[1].set_ylabel("Distância de Hamming / Taxa de Erro (%)")
    axes[1].set_ylim(0, 134)
    axes[1].set_title("Corrupção Funcional (Distância de Hamming)")
    axes[1].legend(loc="upper center", ncol=2, fontsize=7.8, framealpha=0.95)

    fig.suptitle("Avaliação de Ofuscação Lógica em Somador Completo 2D (Chave $(K_1, K_0)$)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(BASE_DIR, "fig2_matriz_tabelas_verdade_hamming.png"), dpi=200)
    plt.close(fig)


def main():
    build_and_run_full_adder()
    analyze_and_plot()
    print("Modulo 05 concluido com sucesso.")


if __name__ == "__main__":
    main()
