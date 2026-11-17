"""
Compilador SPICE e motor de simulação ngspice-47 para circuitos polimórficos BP SB-FET.
Suporta compilação de grafos de Alto Nível (Portas Polimórficas configuráveis entre as 7 tuplas)
e de Baixo Nível (Transistores ARI de 5 terminais, fontes DC/PWL, capacitores e pontas de prova).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from bisect import bisect_right
from collections import defaultdict, deque
from typing import Any

from templates_catalog import TUPLE_DEFINITIONS

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NGSPICE_EXE = os.path.join(ROOT_DIR, "ngspice-47_64", "Spice64", "bin", "ngspice_con.exe")
LIB_PATH = os.path.join(ROOT_DIR, "experimentos", "00_modelo_ngspice", "bp_ari_ngspice.lib")

SHARED_SUBCKTS = """
.subckt BP_INV08 in out vdd_i vss
B_sh in_sh 0 V = (v(in) < 0.0 ? 0.0 : (v(in) > 0.8 ? 0.8 : v(in))) - 0.27
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


class CompilationError(ValueError):
    """Erro de validação ou topologia antes de chamar o ngspice."""


def _safe_id(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", str(raw or "n"))
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"n_{cleaned}"
    return cleaned


def _norm_ngspice_path(path: str) -> str:
    return path.replace("\\", "/")


def _run_ngspice_script(netlist: str) -> str:
    """Grava arquivo temporário e executa ngspice_con.exe -b, retornando stdout."""
    if not os.path.exists(NGSPICE_EXE):
        raise RuntimeError(f"Executável do ngspice não encontrado em: {NGSPICE_EXE}")
    if not os.path.exists(LIB_PATH):
        raise RuntimeError(f"Biblioteca BP SB-FET não encontrada em: {LIB_PATH}")

    work_dir = tempfile.mkdtemp(prefix="bpfet_sim_")
    sp_path = os.path.join(work_dir, "circuit.sp")
    try:
        with open(sp_path, "w", encoding="utf-8") as f:
            f.write(netlist)

        proc = subprocess.run(
            [NGSPICE_EXE, "-b", sp_path],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=90,
        )
        if proc.returncode != 0 or "aborted" in proc.stderr.lower():
            raise RuntimeError(
                f"ngspice retornou erro (código {proc.returncode}):\n"
                f"{proc.stderr.strip() or proc.stdout.strip()}"
            )
        return work_dir, proc.stdout
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise


def _parse_wrdata_file(filepath: str) -> tuple[list[str], list[list[float]]]:
    """Lê arquivo .dat gerado por wrdata (set wr_vecnames + wr_singlescale) em listas por coluna."""
    with open(filepath, "r", encoding="utf-8") as f:
        header_line = f.readline().strip()
        cols = header_line.split()
        col_data: list[list[float]] = [[] for _ in cols]
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            for idx, val in enumerate(parts):
                if idx < len(col_data):
                    col_data[idx].append(float(val))
    return cols, col_data


def _linspace(start: float, stop: float, n: int) -> list[float]:
    if n <= 1:
        return [float(start)]
    step = (stop - start) / (n - 1)
    return [start + i * step for i in range(n)]


def _interp_series(t_target: list[float], t_src: list[float], y_src: list[float]) -> list[float]:
    """Interpolação linear em Python puro para séries ordenadas no tempo."""
    n_src = len(t_src)
    if n_src == 0:
        return [0.0] * len(t_target)
    if n_src == 1:
        return [y_src[0]] * len(t_target)

    out: list[float] = []
    j = 0
    for x in t_target:
        if x <= t_src[0]:
            out.append(y_src[0])
            continue
        if x >= t_src[-1]:
            out.append(y_src[-1])
            continue
        while j + 1 < n_src and t_src[j + 1] < x:
            j += 1
        t0, t1 = t_src[j], t_src[j + 1]
        y0, y1 = y_src[j], y_src[j + 1]
        if t1 == t0:
            out.append(y0)
        else:
            frac = (x - t0) / (t1 - t0)
            out.append(y0 + frac * (y1 - y0))
    return out


def _downsample_trace(
    t_ns: list[float],
    values: list[float],
    t_grid: list[float],
    preserve_abs_peaks: bool = False,
) -> list[float]:
    """Reamostra série temporal para t_grid uniforme, preservando picos estreitos se solicitado."""
    if not preserve_abs_peaks:
        return [round(float(x), 6) for x in _interp_series(t_grid, t_ns, values)]

    out: list[float] = []
    n_grid = len(t_grid)
    n_src = len(t_ns)
    src_idx = 0
    for idx in range(n_grid):
        t_left = t_grid[0] if idx == 0 else 0.5 * (t_grid[idx - 1] + t_grid[idx])
        t_right = t_grid[-1] if idx == n_grid - 1 else 0.5 * (t_grid[idx] + t_grid[idx + 1])
        while src_idx < n_src and t_ns[src_idx] < t_left:
            src_idx += 1
        k = src_idx
        best_val = None
        best_abs = -1.0
        while k < n_src and t_ns[k] <= t_right:
            v = values[k]
            av = abs(v)
            if av > best_abs:
                best_abs = av
                best_val = v
            k += 1
        if best_val is not None:
            out.append(round(float(best_val), 6))
        else:
            pos = bisect_right(t_ns, t_grid[idx])
            val = values[min(max(pos, 0), n_src - 1)] if n_src else 0.0
            out.append(round(float(val), 6))
    return out


def _asym_pct(v0: float, v1: float) -> float:
    denom = min(abs(v0), abs(v1))
    if denom < 1e-15:
        return 0.0
    return float(abs(v0 - v1) / denom * 100.0)


def _trapezoid(y: list[float], x: list[float]) -> float:
    total = 0.0
    for i in range(len(x) - 1):
        total += 0.5 * (y[i] + y[i + 1]) * (x[i + 1] - x[i])
    return total


def _time_avg(t_s: list[float], y: list[float]) -> float:
    if not t_s:
        return 0.0
    span = float(t_s[-1] - t_s[0])
    if span <= 0:
        return float(sum(y) / len(y))
    return float(_trapezoid(y, t_s) / span)


def _mean_window(t_ns: list[float], values: list[float], t_a: float, t_b: float) -> float:
    vals = [v for t, v in zip(t_ns, values) if t_a <= t <= t_b]
    return sum(vals) / len(vals) if vals else 0.0


def _clip01(val: float) -> float:
    return 0.0 if val < 0.0 else (1.0 if val > 1.0 else val)


def _classify_ari_transistors(
    transistor_specs: list[dict[str, Any]],
    node_series_fn,
    n_points: int,
) -> dict[str, dict[str, Any]]:
    """
    Calcula o estado de cada transistor ARI ao longo da grade temporal:
    - polarity: 'p-FET' ou 'n-FET' baseado em v(g2, s) > 0.0 (idêntico à linha 103 do modelo)
    - conduction: 0.0..1.0 indicando canal aberto/conduzindo
    - v_d, v_g, v_s, v_g1, v_g2: séries de tensão dos 5 terminais
    """
    states: dict[str, dict[str, Any]] = {}
    for tr in transistor_specs:
        vd = node_series_fn(tr["d"])
        vg = node_series_fn(tr["g"])
        vs = node_series_fn(tr["s"])
        vg1 = node_series_fn(tr["g1"])
        vg2 = node_series_fn(tr["g2"])

        pol_list: list[str] = []
        cond_list: list[float] = []
        vds_list: list[float] = []

        for k in range(n_points):
            d_v, g_v, s_v, g1_v, g2_v = vd[k], vg[k], vs[k], vg1[k], vg2[k]
            is_nfet = (g2_v - s_v) > 0.0
            pol_list.append("n-FET" if is_nfet else "p-FET")
            vds_list.append(round(float(d_v - s_v), 4))

            if is_nfet:
                v_ref = min(d_v, s_v)
                v_gn = g_v - v_ref
                v_g1n = g1_v - v_ref
                g_drive = _clip01((v_gn + 0.05) / 0.55)
                g1_drive = _clip01((v_g1n + 0.05) / 0.55)
                cond = float(g_drive * g1_drive)
            else:
                v_ref = max(d_v, s_v)
                v_gp = g_v - v_ref
                v_g1p = g1_v - v_ref
                g_drive = _clip01((-v_gp - 0.35) / 0.50)
                g1_drive = _clip01((-v_g1p - 0.35) / 0.50)
                cond = float(g_drive * g1_drive)

            cond_list.append(round(cond, 3))

        states[tr["id"]] = {
            "id": tr["id"],
            "label": tr.get("label", tr["id"]),
            "w": tr.get("w", 1.0),
            "polarity": pol_list,
            "conduction": cond_list,
            "v_d": [round(float(x), 4) for x in vd],
            "v_g": [round(float(x), 4) for x in vg],
            "v_s": [round(float(x), 4) for x in vs],
            "v_g1": [round(float(x), 4) for x in vg1],
            "v_g2": [round(float(x), 4) for x in vg2],
            "v_ds": vds_list,
        }
    return states


def _build_pwl_vectors(input_nodes: list[dict[str, Any]], step_ns: float = 5.0) -> tuple[list[tuple[int, ...]], float]:
    """Gera sequência de vetores lógicos para as entradas digitais."""
    n_in = len(input_nodes)
    custom_seqs: dict[str, list[int]] = {}
    max_custom_len = 0

    for node in input_nodes:
        pat = str(node.get("props", {}).get("pattern", "auto")).strip()
        if pat and pat.lower() != "auto" and re.fullmatch(r"[01]+", pat):
            bits = [int(c) for c in pat]
            custom_seqs[node["id"]] = bits
            max_custom_len = max(max_custom_len, len(bits))

    if max_custom_len > 0:
        vectors = []
        for w_idx in range(max_custom_len):
            row = []
            for idx, node in enumerate(input_nodes):
                if node["id"] in custom_seqs:
                    bits = custom_seqs[node["id"]]
                    row.append(bits[w_idx % len(bits)])
                else:
                    row.append((w_idx >> (n_in - 1 - idx)) & 1)
            vectors.append(tuple(row))
        # Garante fechamento de transição
        duration_ns = len(vectors) * step_ns
        return vectors, duration_ns

    # Sequência exaustiva padrão + retorno a 00..0 (garante transições de subida e descida)
    if n_in <= 4:
        base = [tuple((i >> (n_in - 1 - b)) & 1 for b in range(n_in)) for i in range(1 << n_in)]
    else:
        base = [tuple((i >> (n_in - 1 - b)) & 1 for b in range(n_in)) for i in range(16)]
    vectors = base + [tuple(0 for _ in range(n_in))]
    duration_ns = len(vectors) * step_ns
    return vectors, duration_ns


def _format_pwl_points(bits: list[int], high_v: float, low_v: float = 0.0, step_ns: float = 5.0, edge_ns: float = 0.1) -> str:
    pts: list[str] = []
    n_win = len(bits)
    for idx, bit in enumerate(bits):
        val = high_v if bit == 1 else low_v
        t0 = idx * step_ns
        t1 = (idx + 1) * step_ns - (edge_ns if idx < n_win - 1 else 0.0)
        pts.append(f"{t0:.2f}n {val:.4f} {t1:.2f}n {val:.4f}")
    return " ".join(pts)


def _compute_gate_delays_and_windows(
    t_ns: list[float],
    v_out: list[float],
    vdd: float,
    step_ns: float,
    n_windows: int,
) -> tuple[list[float], list[tuple[float, float]], list[tuple[float, float]]]:
    vth = 0.5 * vdd
    bits = []
    for idx in range(n_windows):
        t_a = idx * step_ns + step_ns * 0.78
        t_b = idx * step_ns + step_ns * 0.94
        v_est = _mean_window(t_ns, v_out, t_a, t_b)
        bits.append(1 if v_est > vth else 0)

    delays: list[float] = []
    w01: list[tuple[float, float]] = []
    w10: list[tuple[float, float]] = []
    for idx in range(len(bits) - 1):
        b0, b1 = bits[idx], bits[idx + 1]
        if b0 == b1:
            continue
        t_edge = (idx + 1) * step_ns
        t_ref = t_edge - 0.05
        t_end = t_edge + 3.5
        tw = []
        vw = []
        for t, v in zip(t_ns, v_out):
            if t_ref <= t <= t_end:
                tw.append(t)
                vw.append(v)
        if not tw:
            continue
        if b0 == 0 and b1 == 1:
            for k, val in enumerate(vw):
                if val >= vth:
                    if k > 0 and vw[k] != vw[k - 1]:
                        tc = tw[k - 1] + (vth - vw[k - 1]) / (vw[k] - vw[k - 1]) * (tw[k] - tw[k - 1])
                    else:
                        tc = tw[k]
                    delays.append(max((tc - t_ref) * 1e3, 1.0))
                    break
            w01.append((t_edge - 0.15, t_edge + 2.0))
        else:
            for k, val in enumerate(vw):
                if val <= vth:
                    if k > 0 and vw[k] != vw[k - 1]:
                        tc = tw[k - 1] + (vth - vw[k - 1]) / (vw[k] - vw[k - 1]) * (tw[k] - tw[k - 1])
                    else:
                        tc = tw[k]
                    delays.append(max((tc - t_ref) * 1e3, 1.0))
                    break
            w10.append((t_edge - 0.15, t_edge + 2.0))
    return delays, w01, w10


def _compile_high_level(circuit: dict[str, Any], compare_keys: bool) -> dict[str, Any]:
    nodes = circuit.get("nodes", [])
    edges = circuit.get("edges", [])
    node_map = {n["id"]: n for n in nodes}

    input_nodes = sorted(
        [n for n in nodes if n.get("type") == "INPUT"],
        key=lambda n: (n.get("y", 0), n.get("x", 0)),
    )
    key_nodes = [n for n in nodes if n.get("type") == "KEY"]
    gate_nodes = [n for n in nodes if n.get("type") == "POLY_GATE"]
    output_nodes = sorted(
        [n for n in nodes if n.get("type") == "OUTPUT"],
        key=lambda n: (n.get("y", 0), n.get("x", 0)),
    )

    if not input_nodes:
        raise CompilationError("Adicione pelo menos uma Entrada Digital (INPUT) ao circuito.")
    if not gate_nodes:
        raise CompilationError("Adicione pelo menos uma Porta Polimórfica ao circuito.")

    # Mapeamento de conexões entrantes: (to_node_id, to_port) -> (from_node_id, from_port)
    incoming: dict[tuple[str, str], tuple[str, str]] = {}
    outgoing_consumers: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for edge in edges:
        src = edge.get("from")
        dst = edge.get("to")
        if src in node_map and dst in node_map:
            incoming[(dst, edge.get("toPort", ""))] = (src, edge.get("fromPort", ""))
            outgoing_consumers[src].append((dst, edge.get("toPort", "")))

    # Ordenação topológica das portas POLY_GATE
    in_deg = {g["id"]: 0 for g in gate_nodes}
    adj: dict[str, list[str]] = defaultdict(list)
    gate_ids = {g["id"] for g in gate_nodes}
    for g in gate_nodes:
        tdef = TUPLE_DEFINITIONS.get(g.get("props", {}).get("tupleId", "NAND_NOR"), TUPLE_DEFINITIONS["NAND_NOR"])
        for pname in tdef["inputs"]:
            src_info = incoming.get((g["id"], pname))
            if src_info and src_info[0] in gate_ids:
                adj[src_info[0]].append(g["id"])
                in_deg[g["id"]] += 1

    queue = deque([gid for gid, deg in in_deg.items() if deg == 0])
    topo_gates: list[dict[str, Any]] = []
    while queue:
        gid = queue.popleft()
        topo_gates.append(node_map[gid])
        for nxt in adj[gid]:
            in_deg[nxt] -= 1
            if in_deg[nxt] == 0:
                queue.append(nxt)

    if len(topo_gates) != len(gate_nodes):
        raise CompilationError("Ciclo combinacional detectado entre portas polimórficas.")

    # Vetores de entrada
    step_ns = 5.0
    vectors, duration_ns = _build_pwl_vectors(input_nodes, step_ns=step_ns)
    n_windows = len(vectors)

    warnings: list[str] = []
    lines: list[str] = [
        "* Netlist gerado automaticamente pelo BP-FET Studio (Alto Nivel Polimorfico)",
        f'.include "{_norm_ngspice_path(LIB_PATH)}"',
        SHARED_SUBCKTS.strip(),
        "",
        "* Trilhos de referencia comuns",
        "Vss vss 0 0.0",
        "Vgp gp  0 0.0",
        "Vgn gn  0 0.8",
        "V11_hi v11_hi 0 1.1",
        "Vdd08_cond vdd08_cond 0 0.8",
        "Vdd11_cond vdd11_cond 0 1.1",
        "",
        "* Fontes PWL das entradas digitais (niveis 0.8V e 1.1V dual-rail)",
    ]

    # Nomes SPICE das entradas
    signal_nets: dict[str, dict[str, str]] = {}
    wr_voltage_nodes: list[str] = []
    input_meta: list[dict[str, Any]] = []

    for idx, inode in enumerate(input_nodes):
        sid = _safe_id(inode["id"])
        bits = [vec[idx] for vec in vectors]
        n08 = f"{sid}_08"
        n11 = f"{sid}_11"
        nn11 = f"{sid}_n11"
        lines.append(f"V_{sid}_08  {n08}  0 pwl({_format_pwl_points(bits, 0.8, 0.0, step_ns)})")
        lines.append(f"V_{sid}_11  {n11}  0 pwl({_format_pwl_points(bits, 1.1, 0.0, step_ns)})")
        lines.append(f"V_{sid}_n11 {nn11} 0 pwl({_format_pwl_points([1 - b for b in bits], 1.1, 0.0, step_ns)})")
        signal_nets[inode["id"]] = {"08": n08, "11": n11, "n11": nn11, "raw": n08, "vdd": 0.8}
        wr_voltage_nodes.append(n08)
        input_meta.append({"id": inode["id"], "label": inode.get("label", f"In{idx+1}"), "net": n08})

    lines.append("")
    lines.append("* Parametros de chaveamento polimorfico")

    # Determina quais portas respondem à chave global na comparação Key=0 vs Key=1
    has_key_nodes = len(key_nodes) > 0
    gate_key_info: dict[str, dict[str, Any]] = {}
    param_lines: list[str] = []
    alter_k0_lines: list[str] = []
    alter_k1_lines: list[str] = []

    def _bias_for_tuple(tuple_id: str, key_val: int) -> dict[str, float]:
        tdef = TUPLE_DEFINITIONS[tuple_id]
        return tdef["key1_bias"] if key_val == 1 else tdef["key0_bias"]

    for g in topo_gates:
        gid = g["id"]
        sgid = _safe_id(gid)
        props = g.get("props", {})
        tuple_id = props.get("tupleId", "NAND_NOR")
        if tuple_id not in TUPLE_DEFINITIONS:
            tuple_id = "NAND_NOR"
        tdef = TUPLE_DEFINITIONS[tuple_id]

        src_key = incoming.get((gid, "K"))
        wired_to_key = bool(src_key and src_key[0] in node_map and node_map[src_key[0]].get("type") == "KEY")
        if wired_to_key:
            key_node = node_map[src_key[0]]
            nominal_key = 1 if int(key_node.get("props", {}).get("value", 0)) == 1 else 0
            varies_with_global_key = True
        else:
            nominal_key = 1 if int(props.get("localKey", 0)) == 1 else 0
            varies_with_global_key = not has_key_nodes

        k_run0 = 0 if (compare_keys and varies_with_global_key) else nominal_key
        k_run1 = 1 if (compare_keys and varies_with_global_key) else nominal_key

        b0 = _bias_for_tuple(tuple_id, k_run0)
        b1 = _bias_for_tuple(tuple_id, k_run1)

        gate_key_info[gid] = {
            "sgid": sgid,
            "tupleId": tuple_id,
            "tdef": tdef,
            "nominalKey": nominal_key,
            "keyRun0": k_run0,
            "keyRun1": k_run1,
            "varies": varies_with_global_key,
            "bias0": b0,
            "bias1": b1,
        }

        for pname in ("rtop", "gtop", "rbot", "gbot", "k", "kn"):
            if pname in b0:
                param_name = f"p_{sgid}_{pname}"
                param_lines.append(f".param {param_name} = {b0[pname]}")
                if b1[pname] != b0[pname]:
                    alter_k1_lines.append(f"alterparam {param_name} = {b1[pname]}")

    lines.extend(param_lines)
    lines.append("")

    # Instanciação das portas em ordem topológica + condicionamento automático
    gate_build_info: dict[str, dict[str, Any]] = {}
    total_core_t = 0
    total_all_t = 0
    total_sum_w = 0.0

    for g in topo_gates:
        gid = g["id"]
        info = gate_key_info[gid]
        sgid = info["sgid"]
        tuple_id = info["tupleId"]
        tdef = info["tdef"]

        total_core_t += tdef["core_transistors"]
        total_all_t += tdef["total_transistors"]
        total_sum_w += tdef["sum_w"]

        # Resolve pinos de entrada da porta
        resolved_inputs: dict[str, dict[str, str]] = {}
        for pname in tdef["inputs"]:
            src_info = incoming.get((gid, pname))
            if src_info and src_info[0] in signal_nets:
                resolved_inputs[pname] = signal_nets[src_info[0]]
            else:
                warnings.append(f"Pino {pname} de '{g.get('label', gid)}' desconectado (aterrado em 0V).")
                resolved_inputs[pname] = {"08": "vss", "11": "vss", "n11": "v11_hi", "raw": "vss", "vdd": 0.8}

        out_net = f"{sgid}_out"
        wr_voltage_nodes.append(out_net)

        lines.append(f"* --- Porta {g.get('label', gid)} [{tdef['name']}] ---")
        gate_rails: list[str] = []
        internal_nodes: dict[str, str] = {"Y": out_net}
        supply_sources_k0: list[str] = []
        supply_sources_k1: list[str] = []

        b0 = info["bias0"]
        b1 = info["bias1"]

        if tuple_id in ("NAND_NOR", "XOR_XNOR", "AND_OR", "NAND_XNOR", "NOR_XOR", "AOI21_OAI21"):
            for rname in ("rtop", "gtop", "rbot", "gbot"):
                v_src = f"V_{sgid}_{rname}"
                r_net = f"{sgid}_{rname}"
                lines.append(f"{v_src} {r_net} 0 {{p_{sgid}_{rname}}}")
                internal_nodes[rname] = r_net
                wr_voltage_nodes.append(r_net)
            if b0["rtop"] > 0.1:
                supply_sources_k0.append(f"i(V_{sgid}_rtop)")
            elif b0["rbot"] > 0.1:
                supply_sources_k0.append(f"i(V_{sgid}_rbot)")
            if b1["rtop"] > 0.1:
                supply_sources_k1.append(f"i(V_{sgid}_rtop)")
            elif b1["rbot"] > 0.1:
                supply_sources_k1.append(f"i(V_{sgid}_rbot)")

        if tuple_id == "NAND_NOR":
            a_net = resolved_inputs["A"]["08"]
            b_net = resolved_inputs["B"]["08"]
            n1 = f"{sgid}_n1"
            internal_nodes.update({"A": a_net, "B": b_net, "n1": n1})
            wr_voltage_nodes.append(n1)
            lines.extend([
                f"X_{sgid}_1 {out_net} {a_net} {sgid}_rtop {sgid}_gtop {sgid}_gtop ARI W=1.0",
                f"X_{sgid}_2 {out_net} {b_net} {sgid}_rtop {sgid}_gtop {sgid}_gtop ARI W=1.0",
                f"X_{sgid}_3 {out_net} {b_net} {n1}         {sgid}_gbot {sgid}_gbot ARI W=2.0",
                f"X_{sgid}_4 {n1}      {a_net} {sgid}_rbot {sgid}_gbot {sgid}_gbot ARI W=2.0",
                f"C_{sgid}_n1 {n1} 0 0.05f",
            ])

        elif tuple_id == "XOR_XNOR":
            a, an = resolved_inputs["A"]["11"], resolved_inputs["A"]["n11"]
            b, bn = resolved_inputs["B"]["11"], resolved_inputs["B"]["n11"]
            internal_nodes.update({"A": a, "An": an, "B": b, "Bn": bn})
            wr_voltage_nodes.extend([a, an, b, bn])
            lines.extend([
                f"X_{sgid}_1 {out_net} {an} {sgid}_rtop {b}  {sgid}_gtop ARI W=1.0",
                f"X_{sgid}_2 {out_net} {a}  {sgid}_rtop {bn} {sgid}_gtop ARI W=1.0",
                f"X_{sgid}_3 {out_net} {a}  {sgid}_rbot {b}  {sgid}_gbot ARI W=1.0",
                f"X_{sgid}_4 {out_net} {an} {sgid}_rbot {bn} {sgid}_gbot ARI W=1.0",
            ])

        elif tuple_id == "AND_OR":
            a_net = resolved_inputs["A"]["08"]
            b_net = resolved_inputs["B"]["08"]
            n_pre = f"{sgid}_npre"
            n1 = f"{sgid}_n1"
            vdd_net = f"{sgid}_vdd"
            lines.append(f"V_{sgid}_vdd {vdd_net} 0 0.8")
            supply_sources_k0.append(f"i(V_{sgid}_vdd)")
            supply_sources_k1.append(f"i(V_{sgid}_vdd)")
            internal_nodes.update({"A": a_net, "B": b_net, "n_pre": n_pre, "n1": n1, "vdd": vdd_net, "vss": "vss"})
            wr_voltage_nodes.extend([n_pre, n1])
            lines.extend([
                f"X_{sgid}_1 {n_pre} {a_net} {sgid}_rtop {sgid}_gtop {sgid}_gtop ARI W=1.0",
                f"X_{sgid}_2 {n_pre} {b_net} {sgid}_rtop {sgid}_gtop {sgid}_gtop ARI W=1.0",
                f"X_{sgid}_3 {n_pre} {b_net} {n1}        {sgid}_gbot {sgid}_gbot ARI W=2.0",
                f"X_{sgid}_4 {n1}    {a_net} {sgid}_rbot {sgid}_gbot {sgid}_gbot ARI W=2.0",
                f"C_{sgid}_n1   {n1}    0 0.05f",
                f"C_{sgid}_npre {n_pre} 0 0.1f",
                f"X_{sgid}_INV {n_pre} {out_net} {vdd_net} vss BP_INV08",
            ])

        elif tuple_id == "NAND_XNOR":
            a, an = resolved_inputs["A"]["11"], resolved_inputs["A"]["n11"]
            b, bn = resolved_inputs["B"]["11"], resolved_inputs["B"]["n11"]
            vdd_net = f"{sgid}_vdd"
            k_net = f"{sgid}_k"
            kn_net = f"{sgid}_kn"
            n11p = f"{sgid}_n11p"
            lines.extend([
                f"V_{sgid}_vdd {vdd_net} 0 1.5",
                f"V_{sgid}_k   {k_net}   0 {{p_{sgid}_k}}",
                f"V_{sgid}_kn  {kn_net}  0 {{p_{sgid}_kn}}",
            ])
            supply_sources_k0.append(f"i(V_{sgid}_vdd)")
            supply_sources_k1.append(f"i(V_{sgid}_vdd)")
            internal_nodes.update({"A": a, "An": an, "B": b, "Bn": bn, "Kn": kn_net, "vdd": vdd_net, "gp": "gp", "n11p": n11p})
            wr_voltage_nodes.extend([a, an, b, bn, kn_net, n11p])
            lines.extend([
                f"X_{sgid}_1 {out_net} {an}     {sgid}_rtop {b}      {sgid}_gtop ARI W=1.0",
                f"X_{sgid}_2 {out_net} {a}      {sgid}_rtop {bn}     {sgid}_gtop ARI W=1.0",
                f"X_{sgid}_3 {out_net} {a}      {vdd_net}   {b}      gp          ARI W=1.0",
                f"X_{sgid}_4 {out_net} {a}      {sgid}_rbot {b}      {sgid}_gbot ARI W=1.0",
                f"X_{sgid}_5 {out_net} {an}     {n11p}      {bn}     gp          ARI W=2.0",
                f"X_{sgid}_6 {n11p}    {kn_net} {vdd_net}   {kn_net} gp          ARI W=2.0",
                f"C_{sgid}_n11p {n11p} 0 0.05f",
            ])

        elif tuple_id == "NOR_XOR":
            a, an = resolved_inputs["A"]["11"], resolved_inputs["A"]["n11"]
            b, bn = resolved_inputs["B"]["11"], resolved_inputs["B"]["n11"]
            k_net = f"{sgid}_k"
            kn_net = f"{sgid}_kn"
            n00n = f"{sgid}_n00n"
            lines.extend([
                f"V_{sgid}_k  {k_net}  0 {{p_{sgid}_k}}",
                f"V_{sgid}_kn {kn_net} 0 {{p_{sgid}_kn}}",
            ])
            internal_nodes.update({"A": a, "An": an, "B": b, "Bn": bn, "K": k_net, "vss": "vss", "gn": "gn", "n00n": n00n})
            wr_voltage_nodes.extend([a, an, b, bn, k_net, n00n])
            lines.extend([
                f"X_{sgid}_1 {out_net} {an}    {sgid}_rbot {b}     {sgid}_gbot ARI W=1.0",
                f"X_{sgid}_2 {out_net} {a}     {sgid}_rbot {bn}    {sgid}_gbot ARI W=1.0",
                f"X_{sgid}_3 {out_net} {a}     vss         {b}     gn          ARI W=1.0",
                f"X_{sgid}_4 {out_net} {a}     {sgid}_rtop {b}     {sgid}_gtop ARI W=1.0",
                f"X_{sgid}_5 {out_net} {an}    {n00n}      {bn}    gn          ARI W=2.0",
                f"X_{sgid}_6 {n00n}    {k_net} vss         {k_net} gn          ARI W=2.0",
                f"C_{sgid}_n00n {n00n} 0 0.05f",
            ])

        elif tuple_id == "AOI21_OAI21":
            a = resolved_inputs["A"]["08"]
            b = resolved_inputs["B"]["08"]
            c = resolved_inputs["C"]["08"]
            ntop = f"{sgid}_ntop"
            nbot = f"{sgid}_nbot"
            internal_nodes.update({"A": a, "B": b, "C": c, "ntop": ntop, "nbot": nbot})
            wr_voltage_nodes.extend([ntop, nbot])
            lines.extend([
                f"X_{sgid}_1 {ntop}    {a} {sgid}_rtop {sgid}_gtop {sgid}_gtop ARI W=1.5",
                f"X_{sgid}_2 {ntop}    {b} {sgid}_rtop {sgid}_gtop {sgid}_gtop ARI W=1.5",
                f"X_{sgid}_3 {out_net} {c} {ntop}      {sgid}_gtop {sgid}_gtop ARI W=2.5",
                f"X_{sgid}_4 {out_net} {b} {nbot}      {sgid}_gbot {sgid}_gbot ARI W=2.5",
                f"X_{sgid}_5 {nbot}    {a} {sgid}_rbot {sgid}_gbot {sgid}_gbot ARI W=2.5",
                f"X_{sgid}_6 {out_net} {c} {sgid}_rbot {sgid}_gbot {sgid}_gbot ARI W=1.5",
                f"C_{sgid}_ntop {ntop} 0 0.05f",
                f"C_{sgid}_nbot {nbot} 0 0.05f",
            ])

        elif tuple_id == "MAJ3_XOR3":
            a, an = resolved_inputs["A"]["11"], resolved_inputs["A"]["n11"]
            b, bn = resolved_inputs["B"]["11"], resolved_inputs["B"]["n11"]
            c, cn = resolved_inputs["C"]["11"], resolved_inputs["C"]["n11"]
            vdd15p = f"{sgid}_vdd15p"
            vdd11p = f"{sgid}_vdd11p"
            vdd08p = f"{sgid}_vdd08p"
            vdd15c = f"{sgid}_vdd15c"
            k_net = f"{sgid}_k"
            kn_net = f"{sgid}_kn"
            rtop, gtop = f"{sgid}_rtop", f"{sgid}_gtop"
            rbot, gbot = f"{sgid}_rbot", f"{sgid}_gbot"
            p_raw, pn08, p08, p11, pn11 = f"{sgid}_praw", f"{sgid}_pn08", f"{sgid}_p08", f"{sgid}_p11", f"{sgid}_pn11"
            n1a, n1c, n3a, n3c = f"{sgid}_n1a", f"{sgid}_n1c", f"{sgid}_n3a", f"{sgid}_n3c"

            lines.extend([
                f"V_{sgid}_vdd15p {vdd15p} 0 1.5",
                f"V_{sgid}_vdd11p {vdd11p} 0 1.1",
                f"V_{sgid}_vdd08p {vdd08p} 0 0.8",
                f"V_{sgid}_vdd15c {vdd15c} 0 1.5",
                f"V_{sgid}_k      {k_net}  0 {{p_{sgid}_k}}",
                f"V_{sgid}_kn     {kn_net} 0 {{p_{sgid}_kn}}",
                f"V_{sgid}_rtop   {rtop}   0 {{p_{sgid}_rtop}}",
                f"V_{sgid}_gtop   {gtop}   0 {{p_{sgid}_gtop}}",
                f"V_{sgid}_rbot   {rbot}   0 {{p_{sgid}_rbot}}",
                f"V_{sgid}_gbot   {gbot}   0 {{p_{sgid}_gbot}}",
                # Pré-estágio P = A ^ B
                f"X_{sgid}_PRE1 {p_raw} {an} {vdd15p} {b}  gp ARI W=1.0",
                f"X_{sgid}_PRE2 {p_raw} {a}  {vdd15p} {bn} gp ARI W=1.0",
                f"X_{sgid}_PRE3 {p_raw} {a}  vss      {b}  gn ARI W=1.0",
                f"X_{sgid}_PRE4 {p_raw} {an} vss      {bn} gn ARI W=1.0",
                f"C_{sgid}_praw {p_raw} 0 0.2f",
                f"X_{sgid}_PI1 {p_raw} {pn08} {vdd08p} vss BP_INV08",
                f"X_{sgid}_PI2 {pn08}  {p08}  {vdd08p} vss BP_INV08",
                f"X_{sgid}_PI3 {p08}   {pn11} {vdd11p} vss BP_INV11",
                f"X_{sgid}_PI4 {pn08}  {p11}  {vdd11p} vss BP_INV11",
                # Núcleo 10T
                f"X_{sgid}_M2  {out_net} {p11}    {rtop}   {cn}     {gtop} ARI W=1.0",
                f"X_{sgid}_M4  {out_net} {pn11}   {rbot}   {cn}     {gbot} ARI W=1.0",
                f"X_{sgid}_M1a {out_net} {pn11}   {n1a}    {an}     gn     ARI W=2.0",
                f"X_{sgid}_M1b {n1a}     {kn_net} vss      {kn_net} gn     ARI W=2.0",
                f"X_{sgid}_M1c {out_net} {pn11}   {n1c}    {c}      gp     ARI W=2.0",
                f"X_{sgid}_M1d {n1c}     {kn_net} {vdd15c} {kn_net} gp     ARI W=2.0",
                f"X_{sgid}_M3a {out_net} {p11}    {n3a}    {an}     gp     ARI W=2.0",
                f"X_{sgid}_M3b {n3a}     {k_net}  {vdd15c} {k_net}  gp     ARI W=2.0",
                f"X_{sgid}_M3c {out_net} {p11}    {n3c}    {c}      gn     ARI W=2.0",
                f"X_{sgid}_M3d {n3c}     {k_net}  vss      {k_net}  gn     ARI W=2.0",
                f"C_{sgid}_n1a {n1a} 0 0.05f",
                f"C_{sgid}_n1c {n1c} 0 0.05f",
                f"C_{sgid}_n3a {n3a} 0 0.05f",
                f"C_{sgid}_n3c {n3c} 0 0.05f",
            ])
            if b0["rtop"] > 0.1:
                supply_sources_k0.append(f"i(V_{sgid}_rtop)")
            else:
                supply_sources_k0.append(f"i(V_{sgid}_rbot)")
            supply_sources_k0.append(f"i(V_{sgid}_vdd15c)")
            if b1["rtop"] > 0.1:
                supply_sources_k1.append(f"i(V_{sgid}_rtop)")
            else:
                supply_sources_k1.append(f"i(V_{sgid}_rbot)")
            supply_sources_k1.append(f"i(V_{sgid}_vdd15c)")

            internal_nodes.update({
                "P": p11, "Pn": pn11, "C": c, "Cn": cn, "An": an,
                "K": k_net, "Kn": kn_net, "rtop": rtop, "rbot": rbot,
                "gtop": gtop, "gbot": gbot, "vdd": vdd15c, "vss": "vss",
                "gp": "gp", "gn": "gn", "n1a": n1a, "n1c": n1c, "n3a": n3a, "n3c": n3c,
            })
            wr_voltage_nodes.extend([p11, pn11, c, cn, an, k_net, kn_net, rtop, rbot, gtop, gbot, n1a, n1c, n3a, n3c])

        elif tuple_id == "INV":
            a_net = resolved_inputs["A"]["08"]
            vdd_net = f"{sgid}_vdd"
            lines.append(f"V_{sgid}_vdd {vdd_net} 0 0.8")
            lines.append(f"X_{sgid}_INV {a_net} {out_net} {vdd_net} vss BP_INV08")
            supply_sources_k0.append(f"i(V_{sgid}_vdd)")
            supply_sources_k1.append(f"i(V_{sgid}_vdd)")
            internal_nodes.update({"A": a_net, "vdd": vdd_net, "vss": "vss"})

        # Capacitância de carga e condicionamento automático para estágios seguintes
        consumers = outgoing_consumers.get(gid, [])
        downstream_gates = [node_map[cid] for cid, _ in consumers if node_map[cid].get("type") == "POLY_GATE"]
        needs_08 = any(
            TUPLE_DEFINITIONS.get(dg.get("props", {}).get("tupleId", "NAND_NOR"), TUPLE_DEFINITIONS["NAND_NOR"])["vdd"] == 0.8
            for dg in downstream_gates
        )
        needs_11 = any(
            TUPLE_DEFINITIONS.get(dg.get("props", {}).get("tupleId", "NAND_NOR"), TUPLE_DEFINITIONS["NAND_NOR"])["dual_rail"]
            for dg in downstream_gates
        )

        # Carga padronizada na saída
        if tuple_id in ("AND_OR", "INV"):
            # BP_INV08 já tem 0.1f interno; completa até 0.3f se for saída final
            c_load = "0.2f" if not downstream_gates else "0.1f"
        else:
            c_load = "0.3f" if not downstream_gates else "0.15f"
        lines.append(f"C_{sgid}_out {out_net} 0 {c_load}")

        # Condicionamento automático para ligar qualquer tupla (0.8V <-> 1.5V) em qualquer outra
        sig_08 = out_net
        sig_11 = out_net
        sig_n11 = out_net
        if downstream_gates:
            if tdef["vdd"] == 0.8 and not needs_11:
                sig_08 = out_net
            else:
                n08_inv = f"{sgid}_cond_n08"
                n08_buf = f"{sgid}_cond_08"
                lines.extend([
                    f"X_{sgid}_C1 {out_net} {n08_inv} vdd08_cond vss BP_INV08",
                    f"X_{sgid}_C2 {n08_inv} {n08_buf} vdd08_cond vss BP_INV08",
                ])
                sig_08 = n08_buf
                if needs_11:
                    n11_inv = f"{sgid}_cond_n11"
                    n11_buf = f"{sgid}_cond_11"
                    lines.extend([
                        f"X_{sgid}_C3 {n08_buf} {n11_inv} vdd11_cond vss BP_INV11",
                        f"X_{sgid}_C4 {n08_inv} {n11_buf} vdd11_cond vss BP_INV11",
                    ])
                    sig_11 = n11_buf
                    sig_n11 = n11_inv

        signal_nets[gid] = {
            "08": sig_08,
            "11": sig_11,
            "n11": sig_n11,
            "raw": out_net,
            "vdd": tdef["vdd"],
        }

        all_gate_currents = sorted(set(supply_sources_k0 + supply_sources_k1))
        gate_build_info[gid] = {
            "info": info,
            "internal_nodes": internal_nodes,
            "supply_k0": supply_sources_k0,
            "supply_k1": supply_sources_k1,
            "all_currents": all_gate_currents,
            "out_net": out_net,
        }
        lines.append("")

    # Coleta de variáveis para wrdata
    unique_v_nodes = []
    seen_v = set()
    for vn in wr_voltage_nodes:
        if vn not in ("vss", "gp", "gn", "v11_hi", "vdd08_cond", "vdd11_cond") and vn not in seen_v:
            seen_v.add(vn)
            unique_v_nodes.append(vn)

    unique_i_exprs = []
    seen_i = set()
    for gid, gb in gate_build_info.items():
        for ic in gb["all_currents"]:
            if ic not in seen_i:
                seen_i.add(ic)
                unique_i_exprs.append(ic)

    wr_items = [f"v({vn})" for vn in unique_v_nodes] + unique_i_exprs
    wr_line = "wrdata run_k0.dat " + " ".join(wr_items)
    wr_line_k1 = "wrdata run_k1.dat " + " ".join(wr_items)

    lines.append(".control")
    lines.append("set wr_vecnames")
    lines.append("set wr_singlescale")
    lines.append(f"tran 20p {duration_ns:.2f}n")
    lines.append(wr_line)
    if compare_keys:
        lines.append("")
        lines.append("* Segunda simulacao em Key = 1 para comparacao DPA")
        lines.extend(alter_k1_lines)
        lines.append("reset")
        lines.append(f"tran 20p {duration_ns:.2f}n")
        lines.append(wr_line_k1)
    lines.append(".endc")
    lines.append(".end")

    netlist_str = "\n".join(lines)

    t0_wall = time.perf_counter()
    work_dir, _ = _run_ngspice_script(netlist_str)
    try:
        cols0, data0 = _parse_wrdata_file(os.path.join(work_dir, "run_k0.dat"))
        if compare_keys:
            cols1, data1 = _parse_wrdata_file(os.path.join(work_dir, "run_k1.dat"))
        else:
            cols1, data1 = cols0, data0
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
    elapsed_ms = int((time.perf_counter() - t0_wall) * 1000)

    return _postprocess_high_level(
        circuit=circuit,
        compare_keys=compare_keys,
        input_meta=input_meta,
        output_nodes=output_nodes,
        incoming=incoming,
        topo_gates=topo_gates,
        gate_build_info=gate_build_info,
        vectors=vectors,
        step_ns=step_ns,
        duration_ns=duration_ns,
        cols0=cols0,
        data0=data0,
        cols1=cols1,
        data1=data1,
        netlist_str=netlist_str,
        elapsed_ms=elapsed_ms,
        warnings=warnings,
        total_core_t=total_core_t,
        total_all_t=total_all_t,
        total_sum_w=total_sum_w,
    )


def _postprocess_high_level(
    circuit: dict[str, Any],
    compare_keys: bool,
    input_meta: list[dict[str, Any]],
    output_nodes: list[dict[str, Any]],
    incoming: dict[tuple[str, str], tuple[str, str]],
    topo_gates: list[dict[str, Any]],
    gate_build_info: dict[str, dict[str, Any]],
    vectors: list[tuple[int, ...]],
    step_ns: float,
    duration_ns: float,
    cols0: list[str],
    data0: list[list[float]],
    cols1: list[str],
    data1: list[list[float]],
    netlist_str: str,
    elapsed_ms: int,
    warnings: list[str],
    total_core_t: int,
    total_all_t: int,
    total_sum_w: float,
) -> dict[str, Any]:
    col_map0 = {c.lower(): idx for idx, c in enumerate(cols0)}
    col_map1 = {c.lower(): idx for idx, c in enumerate(cols1)}

    t0_s = data0[0]
    t1_s = data1[0]
    t0_ns = [t * 1e9 for t in t0_s]
    t1_ns = [t * 1e9 for t in t1_s]

    n_grid = 300
    t_grid = _linspace(0.0, duration_ns, n_grid)

    def _get_col(data: list[list[float]], cmap: dict[str, int], expr: str, const_val: float = 0.0) -> list[float]:
        key = expr.lower()
        if key in cmap:
            return data[cmap[key]]
        const_map = {
            "v(vss)": 0.0, "v(gp)": 0.0, "v(gn)": 0.8, "v(v11_hi)": 1.1,
            "v(vdd08_cond)": 0.8, "v(vdd11_cond)": 1.1,
        }
        val = const_map.get(key, const_val)
        n_rows = len(data[0]) if data else 0
        return [val] * n_rows

    def _gate_current_series(data: list[list[float]], cmap: dict[str, int], exprs: list[str]) -> list[float]:
        n_rows = len(data[0]) if data else 0
        if not exprs:
            return [0.0] * n_rows
        acc = [0.0] * n_rows
        for ex in exprs:
            col = _get_col(data, cmap, ex)
            for idx, val in enumerate(col):
                acc[idx] += abs(-val)
        return acc

    i_tot0 = [0.0] * len(t0_s)
    i_tot1 = [0.0] * len(t1_s)
    gate_currents_k0_ua: dict[str, list[float]] = {}
    gate_currents_k1_ua: dict[str, list[float]] = {}
    gate_metrics: dict[str, dict[str, Any]] = {}

    for g in topo_gates:
        gid = g["id"]
        gb = gate_build_info[gid]
        gi0 = _gate_current_series(data0, col_map0, gb["supply_k0"])
        gi1 = _gate_current_series(data1, col_map1, gb["supply_k1"])
        for i, val in enumerate(gi0):
            i_tot0[i] += val
        for i, val in enumerate(gi1):
            i_tot1[i] += val

        gate_currents_k0_ua[gid] = _downsample_trace(t0_ns, [v * 1e6 for v in gi0], t_grid, preserve_abs_peaks=True)
        gate_currents_k1_ua[gid] = _downsample_trace(t1_ns, [v * 1e6 for v in gi1], t_grid, preserve_abs_peaks=True)

        pk0 = float(max(gi0) * 1e6) if gi0 else 0.0
        pk1 = float(max(gi1) * 1e6) if gi1 else 0.0
        md0 = _time_avg(t0_s, gi0) * 1e6
        md1 = _time_avg(t1_s, gi1) * 1e6
        v_out0 = _get_col(data0, col_map0, f"v({gb['out_net']})")
        v_out1 = _get_col(data1, col_map1, f"v({gb['out_net']})")
        tdef = gb["info"]["tdef"]
        delays0, w01_0, w10_0 = _compute_gate_delays_and_windows(t0_ns, v_out0, tdef["vdd"], step_ns, len(vectors))
        delays1, w01_1, w10_1 = _compute_gate_delays_and_windows(t1_ns, v_out1, tdef["vdd"], step_ns, len(vectors))
        all_del = delays0 + delays1
        avg_del = float(sum(all_del) / len(all_del)) if all_del else 0.0
        p_med_nw = 0.5 * (md0 + md1) * 1e-6 * tdef["vdd"] * 1e9
        n_sw = max(len(w01_0) + len(w10_0) + len(w01_1) + len(w10_1), 1)
        e_sw_fj = float(((_trapezoid(gi0, t0_s) + _trapezoid(gi1, t1_s)) * tdef["vdd"] / n_sw) * 1e15)

        gate_metrics[gid] = {
            "id": gid,
            "label": g.get("label", gid),
            "tupleId": tdef["id"],
            "tupleName": tdef["name"],
            "fnK0": tdef["key0_fn"] if gb["info"]["keyRun0"] == 0 else tdef["key1_fn"],
            "fnK1": tdef["key1_fn"] if gb["info"]["keyRun1"] == 1 else tdef["key0_fn"],
            "iPeakK0_uA": round(pk0, 4),
            "iPeakK1_uA": round(pk1, 4),
            "dpaPeakPct": round(_asym_pct(pk0, pk1), 2),
            "dpaMeanPct": round(_asym_pct(md0, md1), 2),
            "delayPs": round(avg_del, 2),
            "powerNw": round(p_med_nw, 2),
            "eSwFj": round(e_sw_fj, 4),
            "pdpAj": round(p_med_nw * avg_del * 1e-3, 2),
        }

    node_voltages_k0: dict[str, list[float]] = {}
    node_voltages_k1: dict[str, list[float]] = {}

    for im in input_meta:
        v0 = _get_col(data0, col_map0, f"v({im['net']})")
        v1 = _get_col(data1, col_map1, f"v({im['net']})")
        node_voltages_k0[im["id"]] = _downsample_trace(t0_ns, v0, t_grid)
        node_voltages_k1[im["id"]] = _downsample_trace(t1_ns, v1, t_grid)

    for g in topo_gates:
        gid = g["id"]
        out_net = gate_build_info[gid]["out_net"]
        v0 = _get_col(data0, col_map0, f"v({out_net})")
        v1 = _get_col(data1, col_map1, f"v({out_net})")
        node_voltages_k0[gid] = _downsample_trace(t0_ns, v0, t_grid)
        node_voltages_k1[gid] = _downsample_trace(t1_ns, v1, t_grid)

    probe_traces = []
    for im in input_meta:
        probe_traces.append({
            "id": im["id"],
            "label": im["label"],
            "role": "input",
            "vdd": 0.8,
            "k0": node_voltages_k0[im["id"]],
            "k1": node_voltages_k1[im["id"]],
        })

    watched_outputs: list[dict[str, Any]] = []
    for onode in output_nodes:
        src = incoming.get((onode["id"], "in"))
        if src and src[0] in node_voltages_k0:
            src_id = src[0]
            vdd_ref = 0.8
            if src_id in gate_build_info:
                vdd_ref = gate_build_info[src_id]["info"]["tdef"]["vdd"]
            node_voltages_k0[onode["id"]] = node_voltages_k0[src_id]
            node_voltages_k1[onode["id"]] = node_voltages_k1[src_id]
            watched_outputs.append({"id": onode["id"], "label": onode.get("label", "Out"), "srcId": src_id, "vdd": vdd_ref})
            probe_traces.append({
                "id": onode["id"],
                "label": onode.get("label", "Out"),
                "role": "output",
                "vdd": vdd_ref,
                "k0": node_voltages_k0[onode["id"]],
                "k1": node_voltages_k1[onode["id"]],
            })

    if not watched_outputs and topo_gates:
        last_g = topo_gates[-1]
        gid = last_g["id"]
        vdd_ref = gate_build_info[gid]["info"]["tdef"]["vdd"]
        watched_outputs.append({"id": gid, "label": last_g.get("label", "Out"), "srcId": gid, "vdd": vdd_ref})
        probe_traces.append({
            "id": gid,
            "label": last_g.get("label", "Out"),
            "role": "output",
            "vdd": vdd_ref,
            "k0": node_voltages_k0[gid],
            "k1": node_voltages_k1[gid],
        })

    n_unique_vecs = min(len(vectors), 1 << min(len(input_meta), 4))
    truth_table = []
    hd_total = 0
    hd_count = 0

    for w_idx in range(n_unique_vecs):
        t_a = w_idx * step_ns + step_ns * 0.72
        t_b = w_idx * step_ns + step_ns * 0.94
        row = {
            "inputs": "".join(str(b) for b in vectors[w_idx]),
            "inputBits": list(vectors[w_idx]),
            "outputs": [],
        }
        for wo in watched_outputs:
            src_id = wo["srcId"]
            out_net = gate_build_info[src_id]["out_net"] if src_id in gate_build_info else input_meta[0]["net"]
            v_arr0 = _get_col(data0, col_map0, f"v({out_net})")
            v_arr1 = _get_col(data1, col_map1, f"v({out_net})")
            v_est0 = _mean_window(t0_ns, v_arr0, t_a, t_b)
            v_est1 = _mean_window(t1_ns, v_arr1, t_a, t_b)
            vth = 0.5 * wo["vdd"]
            b0 = 1 if v_est0 > vth else 0
            b1 = 1 if v_est1 > vth else 0
            diff = b0 != b1
            hd_total += int(diff)
            hd_count += 1
            row["outputs"].append({
                "label": wo["label"],
                "vK0": round(v_est0, 4),
                "vK1": round(v_est1, 4),
                "bitK0": b0,
                "bitK1": b1,
                "diff": diff,
            })
        truth_table.append(row)

    gate_xray: dict[str, Any] = {}
    for g in topo_gates:
        gid = g["id"]
        gb = gate_build_info[gid]
        tdef = gb["info"]["tdef"]
        inodes = gb["internal_nodes"]
        sch = tdef["internal_schematic"]

        def _make_node_resolver(data: list[list[float]], cmap: dict[str, int], bias: dict[str, float], t_grid_ref: list[float], t_ns_ref: list[float]):
            cache: dict[str, list[float]] = {}

            def resolve(term_key: str) -> list[float]:
                if term_key in cache:
                    return cache[term_key]
                fixed = {
                    "inv_g1p": -0.7, "inv_g2p": -0.4, "inv_g1n": 0.8, "inv_g2n": 0.8,
                    "gp": 0.0, "gn": 0.8, "vss": 0.0,
                }
                if term_key in fixed:
                    arr = [fixed[term_key]] * len(t_grid_ref)
                elif term_key == "A_sh":
                    raw = resolve("A")
                    arr = [max(0.0, min(0.8, x)) - 0.27 for x in raw]
                elif term_key == "n_pre_sh":
                    raw = resolve("n_pre")
                    arr = [max(0.0, min(0.8, x)) - 0.27 for x in raw]
                elif term_key in inodes:
                    sp_node = inodes[term_key]
                    raw_col = _get_col(data, cmap, f"v({sp_node})", bias.get(term_key, 0.0))
                    arr = _interp_series(t_grid_ref, t_ns_ref, raw_col)
                else:
                    arr = [bias.get(term_key, 0.0)] * len(t_grid_ref)
                cache[term_key] = arr
                return arr

            return resolve

        res0 = _make_node_resolver(data0, col_map0, gb["info"]["bias0"], t_grid, t0_ns)
        res1 = _make_node_resolver(data1, col_map1, gb["info"]["bias1"], t_grid, t1_ns)

        sch_nodes_k0 = {nd["id"]: [round(float(x), 4) for x in res0(nd["id"])] for nd in sch["nodes"]}
        sch_nodes_k1 = {nd["id"]: [round(float(x), 4) for x in res1(nd["id"])] for nd in sch["nodes"]}

        tr_k0 = _classify_ari_transistors(sch["transistors"], res0, n_grid)
        tr_k1 = _classify_ari_transistors(sch["transistors"], res1, n_grid)

        gate_xray[gid] = {
            "tupleId": tdef["id"],
            "nodeVoltagesK0": sch_nodes_k0,
            "nodeVoltagesK1": sch_nodes_k1,
            "transistorsK0": tr_k0,
            "transistorsK1": tr_k1,
        }

    i_tot0_ua = _downsample_trace(t0_ns, [v * 1e6 for v in i_tot0], t_grid, preserve_abs_peaks=True)
    i_tot1_ua = _downsample_trace(t1_ns, [v * 1e6 for v in i_tot1], t_grid, preserve_abs_peaks=True)

    pk_tot0 = float(max(i_tot0) * 1e6) if i_tot0 else 0.0
    pk_tot1 = float(max(i_tot1) * 1e6) if i_tot1 else 0.0
    md_tot0 = _time_avg(t0_s, i_tot0) * 1e6
    md_tot1 = _time_avg(t1_s, i_tot1) * 1e6

    # Se houver mais de 1 porta, destaca o pior caso DPA de estágio polimórfico variável ou a porta única
    varying_gates = [gm for gid, gm in gate_metrics.items() if gate_build_info[gid]["info"]["varies"]]
    if len(topo_gates) == 1:
        only_gm = next(iter(gate_metrics.values()))
        dpa_peak = only_gm["dpaPeakPct"]
        dpa_mean = only_gm["dpaMeanPct"]
        i_pk_0 = only_gm["iPeakK0_uA"]
        i_pk_1 = only_gm["iPeakK1_uA"]
        delay_ps = only_gm["delayPs"]
        power_nw = only_gm["powerNw"]
        pdp_aj = only_gm["pdpAj"]
    else:
        dpa_peak = round(_asym_pct(pk_tot0, pk_tot1), 2)
        dpa_mean = round(_asym_pct(md_tot0, md_tot1), 2)
        i_pk_0 = round(pk_tot0, 4)
        i_pk_1 = round(pk_tot1, 4)
        # Pior atraso entre saídas
        all_out_delays = []
        for wo in watched_outputs:
            src_id = wo["srcId"]
            if src_id in gate_metrics:
                all_out_delays.append(gate_metrics[src_id]["delayPs"])
        delay_ps = round(max(all_out_delays) if all_out_delays else 0.0, 2)
        # Potência total somada
        power_nw = round(sum(gm["powerNw"] for gm in gate_metrics.values()), 2)
        pdp_aj = round(power_nw * delay_ps * 1e-3, 2)

    # Identificador textual da janela atual para o player
    vector_labels = [
        {
            "tStart": round(i * step_ns, 2),
            "tEnd": round((i + 1) * step_ns, 2),
            "text": " ".join(f"{im['label']}={b}" for im, b in zip(input_meta, vec)),
        }
        for i, vec in enumerate(vectors)
    ]

    return {
        "ok": True,
        "mode": "high",
        "compareKeys": compare_keys,
        "elapsedMs": elapsed_ms,
        "durationNs": duration_ns,
        "stepNs": step_ns,
        "warnings": warnings,
        "tGridNs": [round(float(t), 4) for t in t_grid],
        "vectorLabels": vector_labels,
        "nodeVoltagesK0": node_voltages_k0,
        "nodeVoltagesK1": node_voltages_k1,
        "gateCurrentsK0_uA": gate_currents_k0_ua,
        "gateCurrentsK1_uA": gate_currents_k1_ua,
        "totalCurrentK0_uA": i_tot0_ua,
        "totalCurrentK1_uA": i_tot1_ua,
        "probeTraces": probe_traces,
        "truthTable": truth_table,
        "gateMetrics": gate_metrics,
        "gateXray": gate_xray,
        "metrics": {
            "coreTransistors": total_core_t,
            "totalTransistors": total_all_t,
            "sumW_um": round(total_sum_w, 2),
            "iPeakK0_uA": i_pk_0,
            "iPeakK1_uA": i_pk_1,
            "dpaPeakPct": dpa_peak,
            "dpaMeanPct": dpa_mean,
            "maxStageDpaPeakPct": round(max((gm["dpaPeakPct"] for gm in varying_gates), default=dpa_peak), 2),
            "delayPs": delay_ps,
            "powerNw": power_nw,
            "pdpAj": pdp_aj,
            "hdPct": round(100.0 * hd_total / hd_count, 2) if hd_count > 0 else 0.0,
        },
        "netlist": netlist_str,
    }


def _compile_low_level(circuit: dict[str, Any], compare_keys: bool) -> dict[str, Any]:
    nodes = circuit.get("nodes", [])
    edges = circuit.get("edges", [])
    node_map = {n["id"]: n for n in nodes}

    ari_nodes = [n for n in nodes if n.get("type") == "ARI_FET"]
    if not ari_nodes:
        raise CompilationError("Adicione pelo menos um Transistor BP SB-FET (ARI) ao esquemático.")

    # Union-Find para agrupar pinos eletricamente conectados em redes (nets)
    parent: dict[tuple[str, str], tuple[str, str]] = {}

    def find(x: tuple[str, str]) -> tuple[str, str]:
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: tuple[str, str], b: tuple[str, str]) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    # Registra todos os pinos possíveis dos nós
    for n in nodes:
        nid = n["id"]
        ntype = n.get("type")
        if ntype == "ARI_FET":
            for p in ("d", "g", "s", "g1", "g2"):
                find((nid, p))
        elif ntype in ("VDC", "VPWL"):
            find((nid, "pos"))
            find((nid, "neg"))
        elif ntype in ("CAP", "RES"):
            find((nid, "a"))
            find((nid, "b"))
        elif ntype == "GND":
            find((nid, "gnd"))
        elif ntype == "PROBE":
            find((nid, "in"))

    for edge in edges:
        src = (edge.get("from"), edge.get("fromPort", ""))
        dst = (edge.get("to"), edge.get("toPort", ""))
        if src[0] in node_map and dst[0] in node_map:
            union(src, dst)

    # Identifica o conjunto conectado a algum nó GND ou ao terminal neg desconectado (0)
    gnd_roots = {find((n["id"], "gnd")) for n in nodes if n.get("type") == "GND"}
    # Também força terminais 'neg' de fontes VDC/VPWL que não receberam nenhum fio para a referência 0
    wired_pins = set()
    for edge in edges:
        wired_pins.add((edge.get("from"), edge.get("fromPort", "")))
        wired_pins.add((edge.get("to"), edge.get("toPort", "")))

    for n in nodes:
        if n.get("type") in ("VDC", "VPWL") and (n["id"], "neg") not in wired_pins:
            gnd_roots.add(find((n["id"], "neg")))

    root_to_net: dict[tuple[str, str], str] = {}
    probe_names: dict[tuple[str, str], str] = {}
    for n in nodes:
        if n.get("type") == "PROBE":
            r = find((n["id"], "in"))
            if r not in gnd_roots and r not in probe_names:
                probe_names[r] = _safe_id(n.get("label", n["id"]))

    net_counter = 1
    all_non_gnd_nets: list[str] = []

    def net_of(nid: str, port: str) -> str:
        nonlocal net_counter
        r = find((nid, port))
        if r in gnd_roots:
            return "0"
        if r not in root_to_net:
            if r in probe_names and probe_names[r] not in root_to_net.values():
                name = probe_names[r]
            else:
                name = f"net_{net_counter}"
                net_counter += 1
            root_to_net[r] = name
            all_non_gnd_nets.append(name)
        return root_to_net[r]

    duration_ns = float(circuit.get("durationNs", 25.0))
    if duration_ns <= 0:
        duration_ns = 25.0

    lines: list[str] = [
        "* Netlist gerado automaticamente pelo BP-FET Studio (Baixo Nivel Eletrico ARI)",
        f'.include "{_norm_ngspice_path(LIB_PATH)}"',
        "",
    ]

    param_lines: list[str] = []
    alter_k1_lines: list[str] = []
    source_lines: list[str] = []
    element_lines: list[str] = []
    supply_vdc_info: list[dict[str, Any]] = []
    has_key_dependent = False
    max_vdd = 0.8

    for n in nodes:
        nid = n["id"]
        snid = _safe_id(nid)
        ntype = n.get("type")
        props = n.get("props", {})

        if ntype == "VDC":
            npos = net_of(nid, "pos")
            nneg = net_of(nid, "neg")
            v0 = float(props.get("vKey0", props.get("voltage", 0.8)))
            v1 = float(props.get("vKey1", v0)) if props.get("keyDependent", False) else v0
            if props.get("keyDependent", False):
                has_key_dependent = True
            pname = f"p_{snid}"
            param_lines.append(f".param {pname} = {v0}")
            if v1 != v0:
                alter_k1_lines.append(f"alterparam {pname} = {v1}")
            vsrc_name = f"V_{snid}"
            source_lines.append(f"{vsrc_name} {npos} {nneg} {{{pname}}}")
            max_vdd = max(max_vdd, abs(v0), abs(v1))
            if props.get("isSupply", False) or abs(v0) >= 0.7 or abs(v1) >= 0.7:
                supply_vdc_info.append({
                    "vsrc": vsrc_name,
                    "label": n.get("label", snid),
                    "v0": v0,
                    "v1": v1,
                    "isSupply": bool(props.get("isSupply", False)),
                })

        elif ntype == "VPWL":
            npos = net_of(nid, "pos")
            nneg = net_of(nid, "neg")
            pwl_str = str(props.get("pwl", "0n 0 10n 0.8 25n 0.8")).strip()
            source_lines.append(f"V_{snid} {npos} {nneg} pwl({pwl_str})")
            # Estima tensão máxima do PWL
            nums = [abs(float(m)) for m in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", pwl_str)]
            if len(nums) >= 2:
                max_vdd = max(max_vdd, max(nums[1::2]))

        elif ntype == "ARI_FET":
            w_val = float(props.get("w", 1.0))
            nd = net_of(nid, "d")
            ng = net_of(nid, "g")
            ns = net_of(nid, "s")
            ng1 = net_of(nid, "g1")
            ng2 = net_of(nid, "g2")
            element_lines.append(f"X_{snid} {nd} {ng} {ns} {ng1} {ng2} ARI W={w_val:.3g}")

        elif ntype == "CAP":
            na = net_of(nid, "a")
            nb = net_of(nid, "b")
            cap_val = str(props.get("cap", "0.3f")).strip()
            element_lines.append(f"C_{snid} {na} {nb} {cap_val}")

        elif ntype == "RES":
            na = net_of(nid, "a")
            nb = net_of(nid, "b")
            res_val = str(props.get("res", "10k")).strip()
            element_lines.append(f"R_{snid} {na} {nb} {res_val}")

    # Bleed de alta impedância para evitar nós flutuantes sem caminho DC
    bleed_lines = [f"R_bleed_{net} {net} 0 1e12" for net in all_non_gnd_nets]

    lines.extend(param_lines)
    lines.append("")
    lines.extend(source_lines)
    lines.append("")
    lines.extend(element_lines)
    lines.append("")
    lines.extend(bleed_lines)
    lines.append("")

    # Seleciona quais correntes medir como alimentação principal
    explicit_supplies = [s for s in supply_vdc_info if s["isSupply"]]
    active_supplies = explicit_supplies if explicit_supplies else supply_vdc_info

    wr_items = [f"v({net})" for net in all_non_gnd_nets] + [f"i({s['vsrc']})" for s in active_supplies]
    if not wr_items:
        raise CompilationError("Nenhuma rede elétrica ou fonte conectada para simular.")

    run_dual = bool(compare_keys and has_key_dependent and alter_k1_lines)

    lines.append(".control")
    lines.append("set wr_vecnames")
    lines.append("set wr_singlescale")
    lines.append(f"tran 20p {duration_ns:.2f}n")
    lines.append("wrdata run_k0.dat " + " ".join(wr_items))
    if run_dual:
        lines.append("")
        lines.append("* Segunda simulacao em Key = 1")
        lines.extend(alter_k1_lines)
        lines.append("reset")
        lines.append(f"tran 20p {duration_ns:.2f}n")
        lines.append("wrdata run_k1.dat " + " ".join(wr_items))
    lines.append(".endc")
    lines.append(".end")

    netlist_str = "\n".join(lines)

    t0_wall = time.perf_counter()
    work_dir, _ = _run_ngspice_script(netlist_str)
    try:
        cols0, data0 = _parse_wrdata_file(os.path.join(work_dir, "run_k0.dat"))
        if run_dual:
            cols1, data1 = _parse_wrdata_file(os.path.join(work_dir, "run_k1.dat"))
        else:
            cols1, data1 = cols0, data0
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
    elapsed_ms = int((time.perf_counter() - t0_wall) * 1000)

    col_map0 = {c.lower(): idx for idx, c in enumerate(cols0)}
    col_map1 = {c.lower(): idx for idx, c in enumerate(cols1)}

    t0_s = data0[0]
    t1_s = data1[0]
    t0_ns = [t * 1e9 for t in t0_s]
    t1_ns = [t * 1e9 for t in t1_s]
    n_grid = 300
    t_grid = _linspace(0.0, duration_ns, n_grid)

    def _get_col(data: list[list[float]], cmap: dict[str, int], expr: str) -> list[float]:
        key = expr.lower()
        if key in cmap:
            return data[cmap[key]]
        return [0.0] * (len(data[0]) if data else 0)

    pin_voltages_k0: dict[str, list[float]] = {}
    pin_voltages_k1: dict[str, list[float]] = {}
    net_series_k0: dict[str, list[float]] = {"0": [0.0] * n_grid}
    net_series_k1: dict[str, list[float]] = {"0": [0.0] * n_grid}

    for net in all_non_gnd_nets:
        v0 = _interp_series(t_grid, t0_ns, _get_col(data0, col_map0, f"v({net})"))
        v1 = _interp_series(t_grid, t1_ns, _get_col(data1, col_map1, f"v({net})"))
        net_series_k0[net] = v0
        net_series_k1[net] = v1

    for n in nodes:
        nid = n["id"]
        ntype = n.get("type")
        if ntype in ("VDC", "VPWL"):
            net = net_of(nid, "pos")
            pin_voltages_k0[nid] = [round(float(x), 4) for x in net_series_k0[net]]
            pin_voltages_k1[nid] = [round(float(x), 4) for x in net_series_k1[net]]
        elif ntype == "PROBE":
            net = net_of(nid, "in")
            pin_voltages_k0[nid] = [round(float(x), 4) for x in net_series_k0[net]]
            pin_voltages_k1[nid] = [round(float(x), 4) for x in net_series_k1[net]]
        elif ntype == "GND":
            pin_voltages_k0[nid] = [0.0] * n_grid
            pin_voltages_k1[nid] = [0.0] * n_grid
        elif ntype == "ARI_FET":
            for p in ("d", "g", "s", "g1", "g2"):
                net = net_of(nid, p)
                pin_voltages_k0[f"{nid}:{p}"] = [round(float(x), 4) for x in net_series_k0[net]]
                pin_voltages_k1[f"{nid}:{p}"] = [round(float(x), 4) for x in net_series_k1[net]]
            # Valor principal do nó ARI é o dreno
            nd = net_of(nid, "d")
            pin_voltages_k0[nid] = [round(float(x), 4) for x in net_series_k0[nd]]
            pin_voltages_k1[nid] = [round(float(x), 4) for x in net_series_k1[nd]]
        elif ntype in ("CAP", "RES"):
            na = net_of(nid, "a")
            pin_voltages_k0[nid] = [round(float(x), 4) for x in net_series_k0[na]]
            pin_voltages_k1[nid] = [round(float(x), 4) for x in net_series_k1[na]]

    # Classificação em tempo real dos transistores ARI
    ari_specs = []
    sum_w = 0.0
    for n in ari_nodes:
        w_val = float(n.get("props", {}).get("w", 1.0))
        sum_w += w_val
        ari_specs.append({
            "id": n["id"],
            "label": n.get("label", n["id"]),
            "w": w_val,
            "d": net_of(n["id"], "d"),
            "g": net_of(n["id"], "g"),
            "s": net_of(n["id"], "s"),
            "g1": net_of(n["id"], "g1"),
            "g2": net_of(n["id"], "g2"),
        })

    transistors_k0 = _classify_ari_transistors(ari_specs, lambda net: net_series_k0[net], n_grid)
    transistors_k1 = _classify_ari_transistors(ari_specs, lambda net: net_series_k1[net], n_grid)

    # Sinais para o osciloscópio (Probes + VPWLs)
    probe_traces = []
    for n in nodes:
        if n.get("type") in ("VPWL", "PROBE"):
            nid = n["id"]
            role = "input" if n.get("type") == "VPWL" else "output"
            probe_traces.append({
                "id": nid,
                "label": n.get("label", nid),
                "role": role,
                "vdd": max_vdd,
                "k0": pin_voltages_k0[nid],
                "k1": pin_voltages_k1[nid],
            })

    i_tot0 = [0.0] * len(t0_s)
    i_tot1 = [0.0] * len(t1_s)
    for s in active_supplies:
        if abs(s["v0"]) > 0.1:
            col = _get_col(data0, col_map0, f"i({s['vsrc']})")
            for idx, val in enumerate(col):
                i_tot0[idx] += abs(-val)
        if abs(s["v1"]) > 0.1:
            col = _get_col(data1, col_map1, f"i({s['vsrc']})")
            for idx, val in enumerate(col):
                i_tot1[idx] += abs(-val)

    i_tot0_ua = _downsample_trace(t0_ns, [v * 1e6 for v in i_tot0], t_grid, preserve_abs_peaks=True)
    i_tot1_ua = _downsample_trace(t1_ns, [v * 1e6 for v in i_tot1], t_grid, preserve_abs_peaks=True)

    pk0 = float(max(i_tot0) * 1e6) if i_tot0 else 0.0
    pk1 = float(max(i_tot1) * 1e6) if i_tot1 else 0.0
    md0 = _time_avg(t0_s, i_tot0) * 1e6 if i_tot0 else 0.0
    md1 = _time_avg(t1_s, i_tot1) * 1e6 if i_tot1 else 0.0
    p_med_nw = 0.5 * (md0 + md1) * 1e-6 * max_vdd * 1e9

    return {
        "ok": True,
        "mode": "low",
        "compareKeys": run_dual,
        "elapsedMs": elapsed_ms,
        "durationNs": duration_ns,
        "stepNs": 5.0,
        "warnings": [],
        "tGridNs": [round(float(t), 4) for t in t_grid],
        "vectorLabels": [],
        "nodeVoltagesK0": pin_voltages_k0,
        "nodeVoltagesK1": pin_voltages_k1,
        "transistorsK0": transistors_k0,
        "transistorsK1": transistors_k1,
        "totalCurrentK0_uA": i_tot0_ua,
        "totalCurrentK1_uA": i_tot1_ua,
        "probeTraces": probe_traces,
        "truthTable": [],
        "gateMetrics": {},
        "gateXray": {},
        "metrics": {
            "coreTransistors": len(ari_nodes),
            "totalTransistors": len(ari_nodes),
            "sumW_um": round(sum_w, 2),
            "iPeakK0_uA": round(pk0, 4),
            "iPeakK1_uA": round(pk1, 4),
            "dpaPeakPct": round(_asym_pct(pk0, pk1), 2) if run_dual else 0.0,
            "dpaMeanPct": round(_asym_pct(md0, md1), 2) if run_dual else 0.0,
            "maxStageDpaPeakPct": round(_asym_pct(pk0, pk1), 2) if run_dual else 0.0,
            "delayPs": 0.0,
            "powerNw": round(p_med_nw, 2),
            "pdpAj": 0.0,
            "hdPct": 0.0,
        },
        "netlist": netlist_str,
    }


def compile_and_simulate(payload: dict[str, Any]) -> dict[str, Any]:
    """Ponto de entrada unificado para compilar e simular no ngspice-47."""
    mode = payload.get("mode", "high")
    compare_keys = bool(payload.get("compareKeys", True))
    circuit = payload.get("circuit", payload)

    if mode == "low":
        return _compile_low_level(circuit, compare_keys)
    return _compile_high_level(circuit, compare_keys)
