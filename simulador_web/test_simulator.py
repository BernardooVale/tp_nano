"""
Testes automatizados ponta-a-ponta do BP-FET Studio (compilação SPICE, ngspice-47,
verificação booleana das 7 tuplas, todos os 8 templates, Raio-X e servidor HTTP).
"""

import json
import os
import sys
import threading
import urllib.request

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from server import create_server  # noqa: E402
from spice_compiler import compile_and_simulate  # noqa: E402
from templates_catalog import CIRCUIT_TEMPLATES, TUPLE_DEFINITIONS  # noqa: E402


EXPECTED_BOOLEAN = {
    "NAND_NOR": (
        lambda a, b: 1 - (a & b),
        lambda a, b: 1 - (a | b),
    ),
    "XOR_XNOR": (
        lambda a, b: a ^ b,
        lambda a, b: 1 - (a ^ b),
    ),
    "AND_OR": (
        lambda a, b: a & b,
        lambda a, b: a | b,
    ),
    "NAND_XNOR": (
        lambda a, b: 1 - (a & b),
        lambda a, b: 1 - (a ^ b),
    ),
    "NOR_XOR": (
        lambda a, b: 1 - (a | b),
        lambda a, b: a ^ b,
    ),
    "AOI21_OAI21": (
        lambda a, b, c: 1 - ((a & b) | c),
        lambda a, b, c: 1 - ((a | b) & c),
    ),
    "MAJ3_XOR3": (
        lambda a, b, c: 1 if (a + b + c) >= 2 else 0,
        lambda a, b, c: a ^ b ^ c,
    ),
    "INV": (
        lambda a: 1 - a,
        lambda a: 1 - a,
    ),
}


def test_all_tuples():
    print("[1/4] Testando todas as 7 tuplas polimórficas + INV no ngspice-47...")
    for tuple_id, tdef in TUPLE_DEFINITIONS.items():
        n_in = len(tdef["inputs"])
        nodes = []
        edges = []
        for idx, pname in enumerate(tdef["inputs"]):
            nid = f"in_{idx}"
            nodes.append({"id": nid, "type": "INPUT", "label": pname, "x": 50, "y": 50 + idx * 80, "props": {"pattern": "auto"}})
            edges.append({"id": f"e_{idx}", "from": nid, "fromPort": "out", "to": "g1", "toPort": pname})
        nodes.append({"id": "k0", "type": "KEY", "label": "Key", "x": 50, "y": 350, "props": {"value": 0}})
        nodes.append({"id": "g1", "type": "POLY_GATE", "label": tuple_id, "x": 300, "y": 150, "props": {"tupleId": tuple_id, "localKey": 0}})
        nodes.append({"id": "out1", "type": "OUTPUT", "label": "Y", "x": 600, "y": 150, "props": {}})
        edges.append({"id": "ek", "from": "k0", "fromPort": "out", "to": "g1", "toPort": "K"})
        edges.append({"id": "eo", "from": "g1", "fromPort": "Y", "to": "out1", "toPort": "in"})

        res = compile_and_simulate({"mode": "high", "compareKeys": True, "circuit": {"nodes": nodes, "edges": edges}})
        assert res["ok"] is True
        assert len(res["truthTable"]) == (1 << n_in), f"{tuple_id}: tamanho tabela {len(res['truthTable'])}"

        fn0, fn1 = EXPECTED_BOOLEAN[tuple_id]
        for row in res["truthTable"]:
            bits = row["inputBits"]
            exp0 = fn0(*bits)
            exp1 = fn1(*bits)
            got0 = row["outputs"][0]["bitK0"]
            got1 = row["outputs"][0]["bitK1"]
            assert got0 == exp0, f"{tuple_id} K=0 em {bits}: esperado {exp0}, obtido {got0} ({row['outputs'][0]['vK0']}V)"
            assert got1 == exp1, f"{tuple_id} K=1 em {bits}: esperado {exp1}, obtido {got1} ({row['outputs'][0]['vK1']}V)"

        # Valida Raio-X
        xray = res["gateXray"]["g1"]
        assert len(xray["transistorsK0"]) == tdef["core_transistors"]
        assert len(xray["transistorsK1"]) == tdef["core_transistors"]
        print(
            f"  OK {tuple_id:12s} | {tdef['core_transistors']:2d}T | "
            f"DPA Pico: {res['metrics']['dpaPeakPct']:6.2f}% | {res['elapsedMs']} ms"
        )


def test_all_templates():
    print("\n[2/4] Testando todos os 8 templates do catálogo no ngspice-47...")
    for tpl in CIRCUIT_TEMPLATES:
        res = compile_and_simulate({
            "mode": tpl["mode"],
            "compareKeys": True,
            "circuit": {
                "nodes": tpl["nodes"],
                "edges": tpl["edges"],
                "durationNs": tpl.get("durationNs", 25.0),
            },
        })
        assert res["ok"] is True

        # Verifica lógica exata dos Full Adders em Key=0
        if tpl["id"] in ("tpl_fa_perfil2", "tpl_fa_perfil3"):
            assert len(res["truthTable"]) == 8
            for row in res["truthTable"]:
                a, b, cin = row["inputBits"]
                exp_sum = a ^ b ^ cin
                exp_cout = 1 if (a + b + cin) >= 2 else 0
                got_sum = row["outputs"][0]["bitK0"]
                got_cout = row["outputs"][1]["bitK0"]
                assert got_sum == exp_sum, f"{tpl['id']} Sum({a}{b}{cin}): {got_sum} != {exp_sum}"
                assert got_cout == exp_cout, f"{tpl['id']} Cout({a}{b}{cin}): {got_cout} != {exp_cout}"

        # Verifica inversão de polaridade em baixo nível no (NAND, NOR) 4T
        if tpl["id"] == "tpl_low_nand_nor_4t":
            assert res["transistorsK0"]["x1"]["polarity"][0] == "p-FET"
            assert res["transistorsK0"]["x3"]["polarity"][0] == "n-FET"
            assert res["transistorsK1"]["x1"]["polarity"][0] == "n-FET"
            assert res["transistorsK1"]["x3"]["polarity"][0] == "p-FET"

        # Verifica colapso de memória na SRAM 6T (Módulo 04 e Apresentação v2 + Read-Assist)
        if tpl["id"] in ("tpl_low_sram_6t", "tpl_low_sram_6t_v2"):
            t_grid = res["tGridNs"]
            idx_hold = min(range(len(t_grid)), key=lambda i: abs(t_grid[i] - 11.0))
            idx_col = min(range(len(t_grid)), key=lambda i: abs(t_grid[i] - 28.0))
            q_hold = res["nodeVoltagesK0"]["pq"][idx_hold]
            qb_hold = res["nodeVoltagesK0"]["pqb"][idx_hold]
            q_col = res["nodeVoltagesK0"]["pq"][idx_col]
            qb_col = res["nodeVoltagesK0"]["pqb"][idx_col]
            assert abs(q_hold - qb_hold) > 0.7, f"{tpl['id']} falhou retenção/Read-Assist em 11ns: Q={q_hold}, QB={qb_hold}"
            assert abs(q_col - qb_col) < 0.25, f"{tpl['id']} não colapsou em 28ns: Q={q_col}, QB={qb_col}"
            assert res["transistorsK0"]["xpu1"]["polarity"][idx_hold] == "p-FET"
            assert res["transistorsK0"]["xpu1"]["polarity"][idx_col] == "n-FET"

        print(f"  OK {tpl['id']:22s} ({tpl['mode']:4s}) | {res['elapsedMs']} ms")


def test_mixed_stage_cascade():
    print("\n[3/4] Testando encadeamento misto (0.8V -> 1.5V -> 0.8V) com condicionamento automático...")
    circuit = {
        "nodes": [
            {"id": "a", "type": "INPUT", "label": "A", "x": 50, "y": 80, "props": {"pattern": "auto"}},
            {"id": "b", "type": "INPUT", "label": "B", "x": 50, "y": 180, "props": {"pattern": "auto"}},
            {"id": "g1", "type": "POLY_GATE", "label": "G1", "x": 250, "y": 80, "props": {"tupleId": "NAND_NOR", "localKey": 0}},
            {"id": "g2", "type": "POLY_GATE", "label": "G2", "x": 470, "y": 130, "props": {"tupleId": "XOR_XNOR", "localKey": 0}},
            {"id": "g3", "type": "POLY_GATE", "label": "G3", "x": 700, "y": 130, "props": {"tupleId": "AND_OR", "localKey": 0}},
            {"id": "out", "type": "OUTPUT", "label": "Y", "x": 920, "y": 150, "props": {}},
        ],
        "edges": [
            {"id": "e1", "from": "a", "fromPort": "out", "to": "g1", "toPort": "A"},
            {"id": "e2", "from": "b", "fromPort": "out", "to": "g1", "toPort": "B"},
            {"id": "e3", "from": "g1", "fromPort": "Y", "to": "g2", "toPort": "A"},
            {"id": "e4", "from": "b", "fromPort": "out", "to": "g2", "toPort": "B"},
            {"id": "e5", "from": "g2", "fromPort": "Y", "to": "g3", "toPort": "A"},
            {"id": "e6", "from": "a", "fromPort": "out", "to": "g3", "toPort": "B"},
            {"id": "e7", "from": "g3", "fromPort": "Y", "to": "out", "toPort": "in"},
        ],
    }
    res = compile_and_simulate({"mode": "high", "compareKeys": True, "circuit": circuit})
    assert res["ok"] is True
    for row in res["truthTable"]:
        a, b = row["inputBits"]
        # Key=0: G1=NAND(a,b), G2=XOR(G1,b), G3=AND(G2,a)
        # Key=1: G1=NOR(a,b),  G2=XNOR(G1,b), G3=OR(G2,a)
        exp0 = ((1 - (a & b)) ^ b) & a
        exp1 = (1 - ((1 - (a | b)) ^ b)) | a
        assert row["outputs"][0]["bitK0"] == exp0, f"Cascata mista K0 ({a},{b})"
        assert row["outputs"][0]["bitK1"] == exp1, f"Cascata mista K1 ({a},{b})"
    print(f"  OK cascata mista 0.8V <-> 1.5V validada 100% ({res['elapsedMs']} ms)")


def test_http_server():
    print("\n[4/4] Testando servidor HTTP e rotas REST...")
    srv = create_server("127.0.0.1", 0)
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{port}"
        with urllib.request.urlopen(f"{base}/") as r:
            assert r.status == 200
            html = r.read().decode("utf-8")
            assert "BP-FET Studio" in html

        with urllib.request.urlopen(f"{base}/api/tuples") as r:
            tup = json.loads(r.read().decode("utf-8"))
            assert "NAND_NOR" in tup["tuples"]

        with urllib.request.urlopen(f"{base}/api/templates") as r:
            tpls = json.loads(r.read().decode("utf-8"))
            assert len(tpls["templates"]) == 9

        first_tpl = tpls["templates"][0]
        req = urllib.request.Request(
            f"{base}/api/simulate",
            data=json.dumps({
                "mode": first_tpl["mode"],
                "compareKeys": True,
                "circuit": {"nodes": first_tpl["nodes"], "edges": first_tpl["edges"]},
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as r:
            sim = json.loads(r.read().decode("utf-8"))
            assert sim["ok"] is True
            assert sim["metrics"]["dpaPeakPct"] > 100.0  # (NAND, NOR) ~163.9%

        print(f"  OK servidor HTTP testado na porta {port} (HTML + /api/tuples + /api/templates + /api/simulate)")
    finally:
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    test_all_tuples()
    test_all_templates()
    test_mixed_stage_cascade()
    test_http_server()
    print("\nTODOS OS TESTES PASSARAM COM SUCESSO!")
