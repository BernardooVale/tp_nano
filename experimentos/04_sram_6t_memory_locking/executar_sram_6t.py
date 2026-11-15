"""
Módulo 04 — Célula SRAM 6T Reconfigurável com Bloqueio de Retenção por Inversão de Polaridade (Mecanismo B).

Implementa e valida integralmente no ngspice-47 a arquitetura proposta em tp_nano.md:
1. Simulação transiente de 30 ns (ARI_sram_mecB_ngspice.sp) com 4 fases temporais:
   - Fase 1 (0-6 ns, Key=0): Escrita do bit '1' (WL=1.0V, BL=1.0V, BLB=0.0V).
   - Fase 2 (6-15 ns, Key=0): Retenção bem-sucedida após fechamento de WL (critério DeltaV_Key0 > 0.80V em 12ns).
   - Fase 3 (15-20 ns, Key=1): Acionamento da chave incorreta mantendo VDD=1.0V e VSS=0.0V fixos,
     invertendo PU (p-FET -> n-FET) e PD (n-FET -> p-FET) e destruindo o dado (DeltaV_Collapse1 < 0.15V em 18ns).
   - Fase 4 (20-30 ns, Key=1): Tentativa de escrita do bit '0' (20-24ns) e colapso da retenção após WL=0
     (critério DeltaV_Key1 < 0.15V em 28ns).
2. Extração DC da Curva Borboleta (Butterfly Curve) e Static Noise Margin (SNM_Hold e SNM_Read)
   para Key=0 (biestável) vs. Key=1 (colapso de biestabilidade).
"""

import os
import subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
NGSPICE_EXE = os.path.join(ROOT_DIR, "ngspice-47_64", "Spice64", "bin", "ngspice_con.exe")
LIB_REL = "../00_modelo_ngspice/bp_ari_ngspice.lib"


def run_ngspice(sp_filename):
    """Executa netlist no ngspice_con.exe e retorna stdout."""
    sp_path = os.path.join(BASE_DIR, sp_filename)
    proc = subprocess.run(
        [NGSPICE_EXE, "-b", sp_path],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def build_and_run_transient_30ns():
    """Gera e executa ARI_sram_mecB_ngspice.sp seguindo exatamente tp_nano.md."""
    net = f"""* ============================================================================
* PROJETO: Celula SRAM 6T Reconfiguravel com Transistores 2D de Fosforo Negro
* ARQUITETURA: Mecanismo B - Bloqueio de Retencao por Inversao de Polaridade
* Traducao para ngspice-47 da especificacao em tp_nano.md
* ============================================================================
.include "{LIB_REL}"

.param supp=1.0

* 1. FONTES DE ALIMENTACAO FIXAS
Vdd vdd 0 {{supp}}
Vss vss 0 0

* 2. SINAIS DE POLARIDADE CONTROLADOS PELA CHAVE (KEY)
* 0ns a 15ns -> Key = 0 (Modo SRAM Normal: PU = p-FET, PD = n-FET)
* 15ns a 30ns -> Key = 1 (Modo Colapso: PU = n-FET, PD = p-FET)
Vg1_pu g1_pu 0 pwl(0n -0.5 14.9n -0.5 15.1n 1.8 30n 1.8)
Vg2_pu g2_pu 0 pwl(0n -0.2 14.9n -0.2 15.1n 2.1 30n 2.1)

Vg1_pd g1_pd 0 pwl(0n 0.8 14.9n 0.8 15.1n -1.5 30n -1.5)
Vg2_pd g2_pd 0 pwl(0n 1.1 14.9n 1.1 15.1n -1.5 30n -1.5)

* Polaridade Fixa dos Pass-Gates (Sempre em modo n-FET)
Vg1_pg g1_pg 0 1.8
Vg2_pg g2_pg 0 2.1

* 3. SINAIS DE CONTROLE E DADOS DA MEMORIA (WL, BL, BLB)
Vwl  wl  0 pwl(0n 0 1.9n 0 2.0n 1.0 6.0n 1.0 6.1n 0 19.9n 0 20.0n 1.0 24.0n 1.0 24.1n 0 30n 0)
Vbl  bl  0 pwl(0n 1.0 19.9n 1.0 20.0n 0.0 24.0n 0.0 24.1n 1.0 30n 1.0)
Vblb blb 0 pwl(0n 0.0 19.9n 0.0 20.0n 1.0 24.0n 1.0 24.1n 0.0 30n 0.0)

* 4. INSTANCIACAO DOS 6 TRANSISTORES DA CELULA SRAM (ordem: d g s g1 g2)
XPU1 q  qb vdd g1_pu g2_pu ARI W=1.0
XPD1 q  qb vss g1_pd g2_pd ARI W=2.0
XPU2 qb q  vdd g1_pu g2_pu ARI W=1.0
XPD2 qb q  vss g1_pd g2_pd ARI W=2.0
XPG1 q  wl bl  g1_pg g2_pg ARI W=1.5
XPG2 qb wl blb g1_pg g2_pg ARI W=1.5

Cq  q  vss 1f
Cqb qb vss 1f

* 5. SIMULACAO TRANSIENTE E EXTRACAO DE METRICAS (meas + wrdata)
.control
set wr_vecnames
set wr_singlescale
tran 10p 30n

meas tran Vq_Hold_Key0     FIND v(q)  AT=12n
meas tran Vqb_Hold_Key0    FIND v(qb) AT=12n
let DeltaV_Key0 = abs(Vq_Hold_Key0 - Vqb_Hold_Key0)
print DeltaV_Key0

meas tran Vq_Collapse1     FIND v(q)  AT=18n
meas tran Vqb_Collapse1    FIND v(qb) AT=18n
let DeltaV_Collapse1 = abs(Vq_Collapse1 - Vqb_Collapse1)
print DeltaV_Collapse1

meas tran Vq_Hold_Key1     FIND v(q)  AT=28n
meas tran Vqb_Hold_Key1    FIND v(qb) AT=28n
let DeltaV_Key1 = abs(Vq_Hold_Key1 - Vqb_Hold_Key1)
print DeltaV_Key1

wrdata sram_tran_30ns.dat v(wl) v(bl) v(blb) v(q) v(qb) v(g2_pu) v(g2_pd) i(Vdd)
.endc
.end
"""
    with open(os.path.join(BASE_DIR, "ARI_sram_mecB_ngspice.sp"), "w", encoding="utf-8") as f:
        f.write(net)
    stdout = run_ngspice("ARI_sram_mecB_ngspice.sp")

    # Parse .meas and print outputs
    meas = {}
    for line in stdout.splitlines():
        if "=" in line and any(k in line.lower() for k in ["vq_", "vqb_", "deltav_"]):
            parts = line.split("=")
            key = parts[0].strip().lower()
            val = float(parts[1].strip().split()[0])
            meas[key] = val
    return meas


def build_and_run_butterfly_snm():
    """Gera e executa sram_butterfly_snm.sp para Hold e Read em Key=0 e Key=1."""
    net = f"""* Curva Borboleta (Butterfly Curve / SNM) da SRAM 6T BP SB-FET (Key=0 vs Key=1)
.include "{LIB_REL}"

.param pg1_pu=-0.5
.param pg2_pu=-0.2
.param pg1_pd=0.8
.param pg2_pd=1.1
.param pwl=0.0

Vdd vdd 0 1.0
Vss vss 0 0.0
Vin in_qb 0 0.0

Vg1_pu g1_pu 0 {{pg1_pu}}
Vg2_pu g2_pu 0 {{pg2_pu}}
Vg1_pd g1_pd 0 {{pg1_pd}}
Vg2_pd g2_pd 0 {{pg2_pd}}
Vg1_pg g1_pg 0 1.8
Vg2_pg g2_pg 0 2.1

Vwl wl 0 {{pwl}}
Vbl bl 0 1.0

* Half-cell 1 da SRAM
XPU1 q in_qb vdd g1_pu g2_pu ARI W=1.0
XPD1 q in_qb vss g1_pd g2_pd ARI W=2.0
XPG1 q wl    bl  g1_pg g2_pg ARI W=1.5

.control
set wr_vecnames
set wr_singlescale

* 1) Key=0, Hold (WL=0V)
alterparam pg1_pu = -0.5
alterparam pg2_pu = -0.2
alterparam pg1_pd = 0.8
alterparam pg2_pd = 1.1
alterparam pwl = 0.0
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key0_hold.dat v(q)

* 2) Key=0, Read c/ Wordline Underdrive Read-Assist (WL=0.30V, BL=1.0V)
alterparam pwl = 0.30
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key0_read_assist.dat v(q)

* 3) Key=0, Read s/ Assist (WL=1.0V, BL=1.0V - Read Disturb)
alterparam pwl = 1.0
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key0_read.dat v(q)

* 4) Key=1, Hold (WL=0V) - Inversao de Polaridade
alterparam pg1_pu = 1.8
alterparam pg2_pu = 2.1
alterparam pg1_pd = -1.5
alterparam pg2_pd = -1.5
alterparam pwl = 0.0
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key1_hold.dat v(q)

* 5) Key=1, Read c/ Read-Assist (WL=0.30V, BL=1.0V)
alterparam pwl = 0.30
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key1_read_assist.dat v(q)

* 6) Key=1, Read s/ Assist (WL=1.0V, BL=1.0V)
alterparam pwl = 1.0
reset
dc Vin 0 1.0 0.005
wrdata butterfly_key1_read.dat v(q)
.endc
.end
"""
    with open(os.path.join(BASE_DIR, "sram_butterfly_snm.sp"), "w", encoding="utf-8") as f:
        f.write(net)
    run_ngspice("sram_butterfly_snm.sp")


def compute_snm_and_square(x_curve, y_curve):
    """
    Calcula o Static Noise Margin (SNM) pelo método do maior quadrado inscrito
    no lobo superior da curva borboleta (eixo horizontal V_qb, eixo vertical V_q).
    Para um quadrado alinhado aos eixos entre a curva direta y=f(x) e a espelhada x=f(y),
    no lobo superior esquerdo (y > x) um vértice está em (x0, f(x0)) e o oposto em (f(y0), y0).
    """
    # Garante monotonia crescente para interpolação em coordenadas rotacionadas a 45 graus
    s2 = np.sqrt(2.0)
    u1 = (x_curve - y_curve) / s2
    v1 = (x_curve + y_curve) / s2

    # Curva espelhada (x2 = y_curve, y2 = x_curve) -> u2 = -u1, v2 = v1
    u2 = -u1
    v2 = v1

    # Ordena por u para interpolação
    idx1 = np.argsort(u1)
    u1_s, v1_s = u1[idx1], v1[idx1]
    idx2 = np.argsort(u2)
    u2_s, v2_s = u2[idx2], v2[idx2]

    u_grid = np.linspace(-0.7, 0.7, 2000)
    v1_i = np.interp(u_grid, u1_s, v1_s)
    v2_i = np.interp(u_grid, u2_s, v2_s)

    # No lobo esquerdo (u < 0 -> x < y), queremos v1 > v2 (se f for inversora)
    # Verifica se há mais de 1 cruzamento (biestabilidade)
    diff = v1_i - v2_i
    mask_lobe = (u_grid < 0.0) & (diff > 0.0)
    if not np.any(mask_lobe):
        return 0.0, None

    # Contíguo a partir do último cruzamento próximo a u=0 até o ponto estável lateral
    best_idx = int(np.argmax(np.where(mask_lobe, diff, -1.0)))
    snm = float(diff[best_idx] / s2)
    u_opt = float(u_grid[best_idx])
    v_top = float(v1_i[best_idx])
    v_bot = float(v2_i[best_idx])

    # Converte os cantos do quadrado de volta para (x, y) originais:
    # Canto superior esquerdo: (u_opt, v_top), canto inferior direito: (u_opt, v_bot)?
    # Nota: em rotação de 45 deg, uma reta vertical em u (u constante) é x - y = const.
    # O segmento de tamanho diff conecta (x1, y1) em C1 a (x2, y2) em C2 ao longo da diagonal do quadrado!
    x_tl = (u_opt + v_top) / s2
    y_tl = (v_top - u_opt) / s2
    x_br = (u_opt + v_bot) / s2
    y_br = (v_bot - u_opt) / s2
    sq_x = min(x_tl, x_br)
    sq_y = min(y_tl, y_br)
    return snm, (sq_x, sq_y, snm)


def analyze_and_plot(meas):
    """Valida critérios de aceitação e gera figuras da SRAM 6T."""
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})

    tr = np.loadtxt(os.path.join(BASE_DIR, "sram_tran_30ns.dat"), skiprows=1)
    t_ns = tr[:, 0] * 1e9
    wl = tr[:, 1]
    bl = tr[:, 2]
    blb = tr[:, 3]
    vq = tr[:, 4]
    vqb = tr[:, 5]
    vg2_pu = tr[:, 6]
    vg2_pd = tr[:, 7]
    idd_ua = -tr[:, 8] * 1e6
    delta_v = np.abs(vq - vqb)

    # --- Figura 1: Simulação Transiente 30ns ---
    fig, axes = plt.subplots(4, 1, figsize=(12, 9.5), sharex=True)

    # Regiões de fase
    phase_bounds = [(0, 6, "#e8f4f8", "Fase 1: Escrita '1'\n(Key=0)"),
                    (6, 15, "#e8f8e8", "Fase 2: Retenção\n(Key=0)"),
                    (15, 20, "#fde8e8", "Fase 3: Bloqueio\n(Key=1)"),
                    (20, 30, "#fff2e0", "Fase 4: Falha Escrita/Retenção\n(Key=1)")]
    for x0, x1, bg, lbl in phase_bounds:
        for ax in axes:
            ax.axvspan(x0, x1, color=bg, alpha=0.45)
        axes[0].text(0.5 * (x0 + x1), 1.15, lbl, ha="center", va="center", fontsize=8.5, fontweight="bold")

    axes[0].plot(t_ns, wl, "#08519c", lw=2.0, label="WL (Wordline)")
    axes[0].plot(t_ns, bl, "#31a354", lw=1.6, ls="--", label="BL")
    axes[0].plot(t_ns, blb, "#e6550d", lw=1.6, ls=":", label="BLB")
    axes[0].set_ylabel("Sinais Externos (V)")
    axes[0].set_ylim(-0.08, 1.32)
    axes[0].legend(loc="center", bbox_to_anchor=(0.35, 0.48), ncol=3, fontsize=8.5, framealpha=0.92)

    axes[1].plot(t_ns, vg2_pu, "#6a51a3", lw=2.0, label="$V(g2_{\\mathrm{PU}})$ (Pull-Up)")
    axes[1].plot(t_ns, vg2_pd, "#cb181d", lw=2.0, ls="--", label="$V(g2_{\\mathrm{PD}})$ (Pull-Down)")
    axes[1].axvline(15.0, color="red", ls="-.", lw=1.2)
    axes[1].set_ylabel("Chave Polaridade (V)")
    axes[1].set_ylim(-2.0, 2.6)
    axes[1].legend(loc="upper right", fontsize=8.5)

    axes[2].plot(t_ns, vq, "#08519c", lw=2.3, label="$V(q)$ (Nó Verdadeiro)")
    axes[2].plot(t_ns, vqb, "#e6550d", lw=2.3, label="$V(qb)$ (Nó Complementar)")
    axes[2].axvline(15.0, color="red", ls="-.", lw=1.2)
    axes[2].set_ylabel("Armazenamento (V)")
    axes[2].set_ylim(-0.08, 1.12)
    axes[2].legend(loc="upper right", fontsize=8.5)

    axes[3].plot(t_ns, delta_v, "#111111", lw=2.2, label="$\\Delta V = |V(q) - V(qb)|$")
    axes[3].axhline(0.80, color="#238b45", ls="--", lw=1.3, label="Critério Retenção ($> 0,80\\,\\mathrm{V}$)")
    axes[3].axhline(0.15, color="#cb181d", ls="--", lw=1.3, label="Critério Bloqueio ($< 0,15\\,\\mathrm{V}$)")
    axes[3].scatter([12.0, 18.0, 28.0],
                    [meas["deltav_key0"], meas["deltav_collapse1"], meas["deltav_key1"]],
                    color=["#238b45", "#cb181d", "#cb181d"], s=60, zorder=5)
    axes[3].annotate(f"{meas['deltav_key0']:.3f} V", (12.0, meas["deltav_key0"]), xytext=(10.2, 0.85), fontweight="bold", color="#238b45")
    axes[3].annotate(f"{meas['deltav_collapse1']:.3f} V", (18.0, meas["deltav_collapse1"]), xytext=(16.5, 0.23), fontweight="bold", color="#cb181d")
    axes[3].annotate(f"{meas['deltav_key1']:.3f} V", (28.0, meas["deltav_key1"]), xytext=(26.2, 0.22), fontweight="bold", color="#cb181d")
    axes[3].axvline(15.0, color="red", ls="-.", lw=1.2)
    axes[3].set_ylabel("$\\Delta V$ Diferencial (V)")
    axes[3].set_xlabel("Tempo (ns)")
    axes[3].set_ylim(-0.05, 1.12)
    axes[3].legend(loc="upper right", fontsize=8.5)

    fig.suptitle("SRAM 6T BP SB-FET (Mecanismo B): Retenção em Key=0 e Colapso em Key=1 ($V_{DD}=1,0\\,\\mathrm{V}$ fixo)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(BASE_DIR, "fig1_sram_transiente_30ns.png"), dpi=200)
    plt.close(fig)

    # --- Figura 2: Curva Borboleta e SNM ---
    k0_h = np.loadtxt(os.path.join(BASE_DIR, "butterfly_key0_hold.dat"), skiprows=1)
    k0_ra = np.loadtxt(os.path.join(BASE_DIR, "butterfly_key0_read_assist.dat"), skiprows=1)
    k0_r = np.loadtxt(os.path.join(BASE_DIR, "butterfly_key0_read.dat"), skiprows=1)
    k1_h = np.loadtxt(os.path.join(BASE_DIR, "butterfly_key1_hold.dat"), skiprows=1)
    k1_ra = np.loadtxt(os.path.join(BASE_DIR, "butterfly_key1_read_assist.dat"), skiprows=1)
    k1_r = np.loadtxt(os.path.join(BASE_DIR, "butterfly_key1_read.dat"), skiprows=1)

    snm_k0_hold, sq_h = compute_snm_and_square(k0_h[:, 0], k0_h[:, 1])
    snm_k0_ra, sq_ra = compute_snm_and_square(k0_ra[:, 0], k0_ra[:, 1])
    snm_k0_read, _ = compute_snm_and_square(k0_r[:, 0], k0_r[:, 1])
    snm_k1_hold, _ = compute_snm_and_square(k1_h[:, 0], k1_h[:, 1])
    snm_k1_ra, _ = compute_snm_and_square(k1_ra[:, 0], k1_ra[:, 1])
    snm_k1_read, _ = compute_snm_and_square(k1_r[:, 0], k1_r[:, 1])

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.6))

    # Painel Esquerdo: Key = 0 (Biestável em Hold e Read c/ Assist; Read Disturb em WL=1.0V)
    axes[0].plot(k0_h[:, 0], k0_h[:, 1], "#08519c", lw=2.2, label="Hold ($\\mathrm{WL}=0\\,\\mathrm{V}$): $V_q=f(V_{qb})$")
    axes[0].plot(k0_h[:, 1], k0_h[:, 0], "#3182bd", lw=2.0, ls="--", label="Hold ($\\mathrm{WL}=0\\,\\mathrm{V}$): $V_{qb}=f(V_q)$")
    axes[0].plot(k0_ra[:, 0], k0_ra[:, 1], "#238b45", lw=2.0, label="Read Assist ($\\mathrm{WL}=0,30\\,\\mathrm{V}$): $V_q$")
    axes[0].plot(k0_ra[:, 1], k0_ra[:, 0], "#74c476", lw=1.8, ls="--", label="Read Assist ($\\mathrm{WL}=0,30\\,\\mathrm{V}$): $V_{qb}$")
    axes[0].plot(k0_r[:, 0], k0_r[:, 1], "#e6550d", lw=1.6, ls=":", label="Read s/ Assist ($\\mathrm{WL}=1,0\\,\\mathrm{V}$, Disturb)")
    axes[0].plot(k0_r[:, 1], k0_r[:, 0], "#fdae6b", lw=1.4, ls=":", alpha=0.9)
    if sq_h is not None:
        rect_h = patches.Rectangle((sq_h[0], sq_h[1]), sq_h[2], sq_h[2], linewidth=1.8, edgecolor="#08519c", facecolor="#9ecae1", alpha=0.45, label=f"$\\mathrm{{SNM}}_{{\\mathrm{{Hold}}}}={snm_k0_hold*1e3:.1f}\\,\\mathrm{{mV}}$")
        axes[0].add_patch(rect_h)
    if sq_ra is not None:
        rect_ra = patches.Rectangle((sq_ra[0], sq_ra[1]), sq_ra[2], sq_ra[2], linewidth=1.8, edgecolor="#238b45", facecolor="#a1d99b", alpha=0.55, label=f"$\\mathrm{{SNM}}_{{\\mathrm{{Read,Assist}}}}={snm_k0_ra*1e3:.1f}\\,\\mathrm{{mV}}$")
        axes[0].add_patch(rect_ra)
    axes[0].set_title("$\\mathrm{Key} = 0$ (Biestável + Read-Assist vs. Read Disturb)")
    axes[0].set_xlabel("$V(qb)\\ (\\mathrm{V})$")
    axes[0].set_ylabel("$V(q)\\ (\\mathrm{V})$")
    axes[0].set_xlim(-0.02, 1.02)
    axes[0].set_ylim(-0.02, 1.02)
    axes[0].set_aspect("equal")
    axes[0].legend(fontsize=7.3, loc="upper right", framealpha=0.92)

    # Painel Direito: Key = 1 (Colapso)
    axes[1].plot(k1_h[:, 0], k1_h[:, 1], "#cb181d", lw=2.2, label="Hold Key=1 ($\\mathrm{WL}=0\\,\\mathrm{V}$): $V_q$")
    axes[1].plot(k1_h[:, 1], k1_h[:, 0], "#fb6a4a", lw=2.0, ls="--", label="Hold Key=1 ($\\mathrm{WL}=0\\,\\mathrm{V}$): $V_{qb}$")
    axes[1].plot(k1_ra[:, 0], k1_ra[:, 1], "#238b45", lw=1.8, label="Read Assist Key=1 ($\\mathrm{WL}=0,30\\,\\mathrm{V}$)")
    axes[1].plot(k1_r[:, 0], k1_r[:, 1], "#6a51a3", lw=1.8, label="Read Key=1 ($\\mathrm{WL}=1,0\\,\\mathrm{V}$)")
    axes[1].plot(k1_r[:, 1], k1_r[:, 0], "#9e9ac8", lw=1.6, ls="--")
    # Ponto fixo único em Key=1 Hold
    idx_eq = int(np.argmin(np.abs(k1_h[:, 0] - k1_h[:, 1])))
    axes[1].scatter([k1_h[idx_eq, 0]], [k1_h[idx_eq, 1]], color="black", s=70, zorder=6, label=f"Ponto Único Inválido ($\\approx {k1_h[idx_eq, 1]:.2f}\\,\\mathrm{{V}}$)")
    axes[1].set_title(f"$\\mathrm{{Key}} = 1$ (Colapso Total: $\\mathrm{{SNM}} = {snm_k1_hold*1e3:.1f}\\,\\mathrm{{mV}}$)")
    axes[1].set_xlabel("$V(qb)\\ (\\mathrm{V})$")
    axes[1].set_ylabel("$V(q)\\ (\\mathrm{V})$")
    axes[1].set_xlim(-0.02, 1.02)
    axes[1].set_ylim(-0.02, 1.02)
    axes[1].set_aspect("equal")
    axes[1].legend(fontsize=7.6, loc="upper left", framealpha=0.92)

    fig.suptitle("Curva Borboleta (Butterfly Curve) da SRAM 6T: Retenção/Read-Assist em Key=0 vs. Colapso em Key=1", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(BASE_DIR, "fig2_sram_curva_borboleta_snm.png"), dpi=200)
    plt.close(fig)

    # Salva tabela de métricas e valida critérios de tp_nano.md + análise SNM
    rows = [
        {"Metrica": "Vq_Hold_Key0 (t=12ns)", "Valor": meas["vq_hold_key0"], "Unidade": "V", "Criterio": "> 0.80 V", "Passou": meas["vq_hold_key0"] > 0.80},
        {"Metrica": "Vqb_Hold_Key0 (t=12ns)", "Valor": meas["vqb_hold_key0"], "Unidade": "V", "Criterio": "< 0.20 V", "Passou": meas["vqb_hold_key0"] < 0.20},
        {"Metrica": "DeltaV_Key0 (t=12ns)", "Valor": meas["deltav_key0"], "Unidade": "V", "Criterio": "> 0.80 V", "Passou": meas["deltav_key0"] > 0.80},
        {"Metrica": "DeltaV_Collapse1 (t=18ns)", "Valor": meas["deltav_collapse1"], "Unidade": "V", "Criterio": "< 0.15 V", "Passou": meas["deltav_collapse1"] < 0.15},
        {"Metrica": "DeltaV_Key1 (t=28ns)", "Valor": meas["deltav_key1"], "Unidade": "V", "Criterio": "< 0.15 V", "Passou": meas["deltav_key1"] < 0.15},
        {"Metrica": "SNM_Hold (Key=0, WL=0V)", "Valor": snm_k0_hold * 1e3, "Unidade": "mV", "Criterio": "> 150 mV", "Passou": snm_k0_hold * 1e3 > 150.0},
        {"Metrica": "SNM_Read_Unassisted (Key=0, WL=1.0V)", "Valor": snm_k0_read * 1e3, "Unidade": "mV", "Criterio": "== 0 mV (Read Disturb)", "Passou": snm_k0_read == 0.0},
        {"Metrica": "SNM_Read_Assist (Key=0, WL=0.30V)", "Valor": snm_k0_ra * 1e3, "Unidade": "mV", "Criterio": "> 50 mV", "Passou": snm_k0_ra * 1e3 > 50.0},
        {"Metrica": "SNM_Hold (Key=1, WL=0V)", "Valor": snm_k1_hold * 1e3, "Unidade": "mV", "Criterio": "== 0 mV", "Passou": snm_k1_hold == 0.0},
        {"Metrica": "SNM_Read_Assist (Key=1, WL=0.30V)", "Valor": snm_k1_ra * 1e3, "Unidade": "mV", "Criterio": "== 0 mV", "Passou": snm_k1_ra == 0.0},
        {"Metrica": "SNM_Read_Unassisted (Key=1, WL=1.0V)", "Valor": snm_k1_read * 1e3, "Unidade": "mV", "Criterio": "== 0 mV", "Passou": snm_k1_read == 0.0},
    ]
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(BASE_DIR, "metricas_sram_6t.csv"), index=False)
    print(df.to_string(index=False))

    if not df["Passou"].all():
        raise RuntimeError("Falha em um ou mais criterios de aceitacao da SRAM 6T!")


def main():
    meas = build_and_run_transient_30ns()
    build_and_run_butterfly_snm()
    analyze_and_plot(meas)
    print("Modulo 04 concluido com sucesso.")


if __name__ == "__main__":
    main()
