"""Gera o esquemático de alta resolução da célula SRAM 6T polimórfica (Mecanismo B).

Salva em ``figuras/sram6t_polimorfica.png`` e ``sram6t_polimorfica.png`` para uso
na apresentação web e no artigo ``artigo.tex``.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "figuras"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def draw_fet_symbol(ax, x, y, orientation="right", label="", sublabel="", color="#1d4ed8", accent="#0ea5e9"):
    """Desenha um símbolo limpo de transistor SB-FET 2D (canal, porta principal g e porta de polaridade g2)."""
    sign = 1 if orientation == "right" else -1
    ax.plot([x, x], [y - 0.52, y + 0.52], color=color, lw=2.8, solid_capstyle="round", zorder=4)
    ax.plot([x, x], [y + 0.52, y + 0.92], color="#334155", lw=1.8, zorder=3)
    ax.plot([x, x], [y - 0.52, y - 0.92], color="#334155", lw=1.8, zorder=3)

    # Porta principal (g)
    gx = x - sign * 0.28
    ax.plot([gx, gx], [y - 0.40, y + 0.40], color=color, lw=2.1, zorder=4)
    ax.plot([gx, gx - sign * 0.42], [y, y], color="#334155", lw=1.8, zorder=3)

    # Porta de polaridade (g2) + auxiliar (g1)
    pg_x = x + sign * 0.24
    ax.plot([pg_x, pg_x], [y - 0.30, y + 0.30], color=accent, lw=2.2, ls=(0, (2, 1.2)), zorder=4)
    ax.plot([pg_x, pg_x + sign * 0.34], [y + 0.16, y + 0.16], color=accent, lw=1.4, zorder=3)
    ax.plot([pg_x, pg_x + sign * 0.34], [y - 0.16, y - 0.16], color="#64748b", lw=1.2, ls=":", zorder=3)

    lbl_x = x + sign * 0.68
    ha = "left" if sign > 0 else "right"
    ax.text(lbl_x, y + 0.16, label, fontsize=10.5, fontweight="bold", color="#0f172a", ha=ha, va="center", zorder=5)
    if sublabel:
        ax.text(lbl_x, y - 0.16, sublabel, fontsize=8.5, color="#475569", ha=ha, va="center", zorder=5)


def draw_pass_gate(ax, x, y, label="", sublabel=""):
    """Desenha um pass-gate horizontal conectado entre BL/BLB e o nó interno q/qb."""
    ax.plot([x - 0.50, x + 0.50], [y, y], color="#0f766e", lw=2.8, solid_capstyle="round", zorder=4)
    ax.plot([x - 0.50, x - 1.05], [y, y], color="#334155", lw=1.8, zorder=3)
    ax.plot([x + 0.50, x + 1.05], [y, y], color="#334155", lw=1.8, zorder=3)

    # Porta principal (WL) acima
    ax.plot([x - 0.40, x + 0.40], [y + 0.26, y + 0.26], color="#0f766e", lw=2.1, zorder=4)
    ax.plot([x, x], [y + 0.26, y + 0.85], color="#334155", lw=1.8, zorder=3)

    # Polaridade fixa PG abaixo
    ax.plot([x - 0.32, x + 0.32], [y - 0.24, y - 0.24], color="#14b8a6", lw=2.1, ls=(0, (2, 1.2)), zorder=4)
    ax.plot([x, x], [y - 0.24, y - 0.58], color="#0d9488", lw=1.3, zorder=3)
    ax.text(x, y - 0.72, "g1=+1.8V\ng2=+2.1V", fontsize=7.6, color="#0f766e", ha="center", va="top",
            bbox=dict(boxstyle="round,pad=0.20", facecolor="#f0fdfa", edgecolor="#99f6e4", lw=0.8), zorder=5)
    ax.text(x + 0.16, y + 0.42, f"{label}\n{sublabel}", fontsize=8.8, fontweight="bold", color="#0f172a",
            ha="left", va="bottom", zorder=5)


def draw_capacitor(ax, x, y, label="1.0 fF", text_side="left"):
    """Desenha capacitor nodal até VSS sem colidir com pass-gates ou portas."""
    ax.plot([x, x], [y, y - 0.38], color="#475569", lw=1.5, zorder=3)
    ax.plot([x - 0.24, x + 0.24], [y - 0.38, y - 0.38], color="#0f172a", lw=2.0, zorder=4)
    ax.plot([x - 0.24, x + 0.24], [y - 0.50, y - 0.50], color="#0f172a", lw=2.0, zorder=4)
    ax.plot([x, x], [y - 0.50, y - 0.82], color="#475569", lw=1.5, zorder=3)
    for w, dy in [(0.24, 0.0), (0.15, -0.09), (0.06, -0.18)]:
        ax.plot([x - w, x + w], [y - 0.82 + dy, y - 0.82 + dy], color="#334155", lw=1.6)
    if text_side == "left":
        ax.text(x - 0.32, y - 0.44, label, fontsize=8.4, color="#334155", va="center", ha="right", fontweight="bold")
    else:
        ax.text(x + 0.32, y - 0.44, label, fontsize=8.4, color="#334155", va="center", ha="left", fontweight="bold")


def draw_junction(ax, x, y, color="#0f172a", radius=0.075):
    ax.add_patch(patches.Circle((x, y), radius, facecolor=color, edgecolor="white", lw=0.7, zorder=6))


def main():
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(12.4, 7.0), dpi=300)
    ax.set_xlim(-0.4, 16.4)
    ax.set_ylim(-0.6, 10.1)
    ax.axis("off")
    fig.patch.set_facecolor("#ffffff")

    # Título principal acima de tudo
    ax.text(8.0, 9.72, "Célula SRAM 6T Polimórfica — BP SB-FET 2D (ARI 5 Terminais)",
            fontsize=13.0, fontweight="bold", color="#0f172a", ha="center", va="center")

    # Fundo sutil para a célula central
    cell_box = FancyBboxPatch((3.65, 1.15), 8.70, 6.95, boxstyle="round,pad=0.18,rounding_size=0.25",
                              facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.4, ls="--", zorder=0)
    ax.add_patch(cell_box)

    # Trilhos fixos VDD e VSS
    ax.plot([3.85, 12.15], [7.55, 7.55], color="#b91c1c", lw=2.8, zorder=3)
    ax.text(8.0, 7.72, "VDD = 1.0 V (Estritamente Fixo)", fontsize=9.0, fontweight="bold",
            color="#b91c1c", ha="center", va="bottom",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#fef2f2", edgecolor="#fecaca", lw=1.0))

    ax.plot([3.85, 12.15], [1.55, 1.55], color="#1e293b", lw=2.8, zorder=3)
    ax.text(8.0, 1.38, "VSS = 0.0 V (Estritamente Fixo)", fontsize=9.0, fontweight="bold",
            color="#1e293b", ha="center", va="top",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#f1f5f9", edgecolor="#cbd5e1", lw=1.0))

    x_left, x_right = 6.0, 10.0
    y_pu, y_pd = 6.05, 3.05
    y_mid = 4.55

    # Conexões verticais VDD -> PU e PD -> VSS
    ax.plot([x_left, x_left], [7.55, y_pu + 0.92], color="#334155", lw=1.8, zorder=3)
    ax.plot([x_right, x_right], [7.55, y_pu + 0.92], color="#334155", lw=1.8, zorder=3)
    draw_junction(ax, x_left, 7.55, "#b91c1c")
    draw_junction(ax, x_right, 7.55, "#b91c1c")

    ax.plot([x_left, x_left], [1.55, y_pd - 0.92], color="#334155", lw=1.8, zorder=3)
    ax.plot([x_right, x_right], [1.55, y_pd - 0.92], color="#334155", lw=1.8, zorder=3)
    draw_junction(ax, x_left, 1.55, "#1e293b")
    draw_junction(ax, x_right, 1.55, "#1e293b")

    # Dreno PU <-> Dreno PD formando nós q e qb
    ax.plot([x_left, x_left], [y_pd + 0.92, y_pu - 0.92], color="#0f172a", lw=2.2, zorder=3)
    ax.plot([x_right, x_right], [y_pd + 0.92, y_pu - 0.92], color="#0f172a", lw=2.2, zorder=3)

    # Transistores dos inversores
    draw_fet_symbol(ax, x_left, y_pu, orientation="right", label="XPU1", sublabel="W = 1.0",
                    color="#7c3aed", accent="#a855f7")
    draw_fet_symbol(ax, x_left, y_pd, orientation="right", label="XPD1", sublabel="W = 2.0",
                    color="#2563eb", accent="#3b82f6")
    draw_fet_symbol(ax, x_right, y_pu, orientation="left", label="XPU2", sublabel="W = 1.0",
                    color="#7c3aed", accent="#a855f7")
    draw_fet_symbol(ax, x_right, y_pd, orientation="left", label="XPD2", sublabel="W = 2.0",
                    color="#2563eb", accent="#3b82f6")

    # Barramento das portas dos inversores
    gx_l = x_left - 0.70
    ax.plot([gx_l, gx_l], [y_pd, y_pu], color="#334155", lw=1.8, zorder=3)
    draw_junction(ax, gx_l, y_mid)

    gx_r = x_right + 0.70
    ax.plot([gx_r, gx_r], [y_pd, y_pu], color="#334155", lw=1.8, zorder=3)
    draw_junction(ax, gx_r, y_mid)

    # Acoplamento cruzado
    ax.plot([x_left, gx_r], [y_mid + 0.24, y_mid + 0.24], color="#1d4ed8", lw=2.0, zorder=3)
    ax.plot([gx_r, gx_r], [y_mid, y_mid + 0.24], color="#1d4ed8", lw=2.0, zorder=3)
    draw_junction(ax, x_left, y_mid + 0.24, "#1d4ed8", radius=0.085)

    ax.plot([x_right, gx_l], [y_mid - 0.24, y_mid - 0.24], color="#ea580c", lw=2.0, zorder=3)
    ax.plot([gx_l, gx_l], [y_mid, y_mid - 0.24], color="#ea580c", lw=2.0, zorder=3)
    draw_junction(ax, x_right, y_mid - 0.24, "#ea580c", radius=0.085)

    # Etiquetas dos nós q e qb
    ax.text(x_left + 0.16, y_mid + 0.48, "q", fontsize=12.5, fontweight="bold", color="#1d4ed8",
            bbox=dict(boxstyle="circle,pad=0.22", facecolor="#eff6ff", edgecolor="#3b82f6", lw=1.2), zorder=7)
    ax.text(x_right - 0.16, y_mid - 0.50, "qb", fontsize=11.5, fontweight="bold", color="#ea580c", ha="right",
            bbox=dict(boxstyle="circle,pad=0.18", facecolor="#fff7ed", edgecolor="#f97316", lw=1.2), zorder=7)

    # Capacitâncias nodais Cq e Cqb deslocadas para fora do núcleo sem colisão
    y_cap = 2.68
    ax.plot([x_left, 4.30], [y_cap, y_cap], color="#475569", lw=1.3, zorder=2)
    draw_junction(ax, x_left, y_cap, "#475569", radius=0.06)
    draw_capacitor(ax, 4.30, y_cap, "Cq = 1.0 fF", text_side="left")

    ax.plot([x_right, 11.70], [y_cap, y_cap], color="#475569", lw=1.3, zorder=2)
    draw_junction(ax, x_right, y_cap, "#475569", radius=0.06)
    draw_capacitor(ax, 11.70, y_cap, "Cqb = 1.0 fF", text_side="right")

    # Pass-gates XPG1 e XPG2
    y_pg = y_mid + 0.24
    ax.plot([x_left, 3.65], [y_pg, y_pg], color="#334155", lw=1.8, zorder=3)
    draw_pass_gate(ax, 2.60, y_pg, label="XPG1", sublabel="W = 1.5")
    ax.plot([1.55, 0.75], [y_pg, y_pg], color="#334155", lw=1.8, zorder=3)
    ax.plot([0.75, 0.75], [1.55, 7.95], color="#0f766e", lw=2.8, zorder=3)
    draw_junction(ax, 0.75, y_pg, "#0f766e", radius=0.085)
    ax.text(0.75, 8.15, "BL", fontsize=12, fontweight="bold", color="#0f766e", ha="center", va="bottom",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#f0fdfa", edgecolor="#14b8a6", lw=1.2))

    y_pg2 = y_mid - 0.24
    ax.plot([x_right, 12.35], [y_pg2, y_pg2], color="#334155", lw=1.8, zorder=3)
    draw_pass_gate(ax, 13.40, y_pg2, label="XPG2", sublabel="W = 1.5")
    ax.plot([14.45, 15.25], [y_pg2, y_pg2], color="#334155", lw=1.8, zorder=3)
    ax.plot([15.25, 15.25], [1.55, 7.95], color="#0f766e", lw=2.8, zorder=3)
    draw_junction(ax, 15.25, y_pg2, "#0f766e", radius=0.085)
    ax.text(15.25, 8.15, "BLB", fontsize=12, fontweight="bold", color="#0f766e", ha="center", va="bottom",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#f0fdfa", edgecolor="#14b8a6", lw=1.2))

    # Linha de palavra (WL) bem abaixo do título
    y_wl = 8.85
    ax.plot([2.60, 13.40], [y_wl, y_wl], color="#0284c7", lw=2.4, zorder=3)
    ax.plot([2.60, 2.60], [y_pg + 0.85, y_wl], color="#0284c7", lw=1.8, zorder=3)
    ax.plot([13.40, 13.40], [y_pg2 + 0.85, y_wl], color="#0284c7", lw=1.8, zorder=3)
    draw_junction(ax, 2.60, y_wl, "#0284c7")
    draw_junction(ax, 13.40, y_wl, "#0284c7")
    ax.text(8.0, y_wl + 0.14, "WL (Wordline): 1.0 V Escrita  |  0.30 V Read-Assist  |  0.0 V Hold",
            fontsize=9.6, fontweight="bold", color="#0369a1", ha="center", va="bottom",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#e0f2fe", edgecolor="#38bdf8", lw=1.0))

    # Bloco inferior de controle de chave (Mecanismo B) com margem confortável
    key_box = FancyBboxPatch((0.15, -0.45), 15.70, 1.32, boxstyle="round,pad=0.10,rounding_size=0.18",
                             facecolor="#eff6ff", edgecolor="#93c5fd", lw=1.3, zorder=2)
    ax.add_patch(key_box)
    ax.text(0.45, 0.50, "Controle de Polaridade (Mecanismo B — Key):", fontsize=10.0, fontweight="bold",
            color="#1e3a8a", ha="left", va="center")
    ax.text(0.45, 0.10,
            "Key = 0 (Autorizado):  PU = p-FET (Vg1 = -0.5 V, Vg2 = -0.2 V)  |  PD = n-FET (Vg1 = +0.8 V, Vg2 = +1.1 V)   =>  Inversores Biestáveis (SNM = 167.1 mV)",
            fontsize=7.8, color="#166534", fontweight="bold", ha="left", va="center")
    ax.text(0.45, -0.22,
            "Key = 1 (Bloqueado):   PU = n-FET (Vg1 = +1.8 V, Vg2 = +2.1 V)  |  PD = p-FET (Vg1 = -1.5 V, Vg2 = -1.5 V)  =>  Seguidores de Fonte (Colapso SNM = 0.0 mV)",
            fontsize=7.8, color="#991b1b", fontweight="bold", ha="left", va="center")

    plt.tight_layout(pad=0.25)
    for target in (FIG_DIR / "sram6t_polimorfica.png", OUT_DIR / "sram6t_polimorfica.png"):
        fig.savefig(target, dpi=300, bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    print("Esquematico salvo em:", FIG_DIR / "sram6t_polimorfica.png")


if __name__ == "__main__":
    main()
