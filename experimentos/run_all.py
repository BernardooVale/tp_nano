import os
import sys
import time
import subprocess
from pathlib import Path

ROOT_EXP = Path(__file__).resolve().parent

MODULES = [
    {
        "dir": "00_modelo_ngspice",
        "script": "gerar_modelo_e_validar.py",
        "expected": [
            "bp_ari_ngspice.lib",
            "sim_N_transfer.sp",
            "sim_P_transfer.sp",
            "sim_N_output.sp",
            "sim_P_output.sp",
            "sim_polarity_gate.sp",
            "metricas_dispositivo.csv",
            "validacao_cruzada_hspice.csv",
            "fig1_transfer_NP_log_lin.png",
            "fig2_output_NP.png",
            "fig3_efeito_porta_polaridade.png",
            "fig4_validacao_cruzada_hspice.png",
            "README.md",
        ],
    },
    {
        "dir": "01_inversor_ultralow_voltage",
        "script": "executar_inversor.py",
        "expected": [
            "inv_vtc.sp",
            "inv_tran.sp",
            "metricas_inversor.csv",
            "fig1_inversor_vtc_ganho.png",
            "fig2_inversor_transiente.png",
            "README.md",
        ],
    },
    {
        "dir": "02_portas_polimorficas_nand_nor_xor",
        "script": "executar_polimorficas.py",
        "expected": [
            "poly_nand_nor.sp",
            "poly_xor_xnor.sp",
            "metricas_polimorficas.csv",
            "fig1_nand_nor_dinamico.png",
            "fig2_xor_xnor_dinamico.png",
            "README.md",
        ],
    },
    {
        "dir": "03_seguranca_dpa_e_robustez",
        "script": "analisar_dpa_e_robustez.py",
        "expected": [
            "sim_supply_noise.sp",
            "metricas_dpa.csv",
            "metricas_seguranca_robustez.csv",
            "ngspice_supply_sweep.csv",
            "fig1_dpa_assinatura_corrente.png",
            "fig2_robustez_3d_nand_nor.png",
            "fig3_robustez_3d_xor_xnor.png",
            "fig4_histogramas_e_retencao.png",
            "README.md",
        ],
    },
    {
        "dir": "04_sram_6t_memory_locking",
        "script": "executar_sram_6t.py",
        "expected": [
            "ARI_sram_mecB_ngspice.sp",
            "sram_butterfly_snm.sp",
            "metricas_sram_6t.csv",
            "fig1_sram_transiente_30ns.png",
            "fig2_sram_curva_borboleta_snm.png",
            "README.md",
        ],
    },
    {
        "dir": "05_circuito_combinacional_cripto",
        "script": "executar_full_adder.py",
        "expected": [
            "full_adder_polimorfico.sp",
            "tabelas_verdade_full_adder.csv",
            "fig1_full_adder_waveforms.png",
            "fig2_matriz_tabelas_verdade_hamming.png",
            "README.md",
        ],
    },
    {
        "dir": "06_fronteira_tensao_nao_padronizada",
        "script": "executar_varredura_tensoes.py",
        "expected": [
            "sweep_nand_nor_vdd_pol.sp",
            "sweep_nand_nor_asym.sp",
            "sweep_xor_xnor_vdd_vin.sp",
            "mapa_tensoes_nand_nor.csv",
            "mapa_tensoes_xor_xnor.csv",
            "fig1_nand_nor_mapa_vdd_polaridade.png",
            "fig2_nand_nor_assimetria_vg2.png",
            "fig3_xor_xnor_mapa_vdd_vin.png",
            "README.md",
        ],
    },
    {
        "dir": "07_assimetria_tuplas_logicas",
        "script": "executar_assimetria_tuplas.py",
        "expected": [
            "tuplas_2entradas.sp",
            "tuplas_3entradas.sp",
            "sim_robustez_tuplas.sp",
            "full_adder_perfis_dpa.sp",
            "tabelas_verdade_tuplas.csv",
            "metricas_tuplas_dpa.csv",
            "benchmark_full_adder_perfis.csv",
            "fig1_assinaturas_corrente_tuplas.png",
            "fig2_pareto_assimetria_vs_custo.png",
            "fig3_robustez_montecarlo_tuplas.png",
            "fig4_benchmark_full_adder_perfis.png",
            "README.md",
        ],
    },
]


def main():
    total_t0 = time.perf_counter()
    print("=" * 78)
    print("EXECUCAO INTEGRADA DA SUITE DE EXPERIMENTOS BP SB-FET (ngspice-47 + Python)")
    print("=" * 78)

    results = []
    for mod in MODULES:
        mod_dir = ROOT_EXP / mod["dir"]
        script_path = mod_dir / mod["script"]
        if not script_path.exists():
            raise FileNotFoundError(f"Script nao encontrado: {script_path}")

        print(f"\n>>> Executando [{mod['dir']}] {mod['script']} ...")
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(mod_dir),
            capture_output=True,
            text=True,
        )
        dt = time.perf_counter() - t0
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            raise RuntimeError(f"Modulo {mod['dir']} falhou com codigo {proc.returncode}")

        missing = [
            f for f in mod["expected"]
            if not (mod_dir / f).exists() or (mod_dir / f).stat().st_size == 0
        ]
        if missing:
            raise RuntimeError(f"Arquivos ausentes ou vazios em {mod['dir']}: {missing}")

        print(f"[OK] {mod['dir']} concluido em {dt:.2f}s ({len(mod['expected'])} artefatos validados).")
        results.append((mod["dir"], dt, len(mod["expected"])))

    total_dt = time.perf_counter() - total_t0
    print("\n" + "=" * 78)
    print("RESUMO FINAL DE VERIFICACAO")
    print("=" * 78)
    for name, dt, n_art in results:
        print(f"  [PASS] {name:<40s} | {dt:6.2f}s | {n_art:2d} artefatos OK")
    print("-" * 78)
    print(f"TODOS OS {len(results)} MODULOS PASSARAM EM {total_dt:.2f}s.")


if __name__ == "__main__":
    main()
