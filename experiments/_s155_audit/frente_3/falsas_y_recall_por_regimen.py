#!/usr/bin/env python3
"""F3: la métrica de falsas publicaciones y el recall del auto-audit, partidos por régimen.

Usa EXACTAMENTE las funciones del auto-audit (medir_falsas_ventana -> banco_paridad con node) y
estratifica las pasadas por régimen (C0: fecha < 2026-09-18; K: desde esa fecha, frontera medida en
regimen_por_ventana.py), sensor y ángulo cenital (zbin del banco). Variante D-9 (regla SN) aparte.

P1: si K no cambiara la publicación en negativos limpios, C0 y K darían lo mismo; la medición lo vería.
    Control positivo conocido: REGLA_ADOPCION / _s153_fk_v2 dicen V375 85-88 % (C0) -> 2,5-3,7 % (K).
P2: estratos con n = 0 -> SIN DATO. El control todo_publica/nada_publica del banco no se corre acá
    (lo trae banco_paridad.controles); acá se imprime n de cada estrato.
También compara el predicado 'dash' del auto-audit (reconstruido en Python) contra el predicado del
tablero ejecutado con node, por noche con alerta.
"""
import sys, os, json, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aw  # noqa: E402
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

FRONTERA = "2026-09-18"

def tasa(sel):
    n = len(sel); p = sum(r["pub"] for r in sel)
    return {"n": n, "pub": p, "pct": round(100 * p / n, 1) if n else "SIN DATO"}

def correr(win, modo):
    coords = aw._coords_por_volcan(); inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(aw.CONS, aw.OCR)
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, win, regla_minimas=modo)
    recs = bp.cargar_nuestros(coords, inner, win)
    bp.etiquetar(recs, por_vb, ns, nv)
    return recs

def main():
    win = ("2026-09-01", "2026-10-19")
    res = {"ventana": win}
    for modo in ("original", "SN"):
        recs = correr(win, modo)
        for r in recs:
            r["reg"] = "C0" if r["noche"] < FRONTERA else "K"
        out = {}
        for s in aw.SENSORS:
            neg = [r for r in recs if r["b"] == s and r["lab"] == "neg_limpio"]
            pos = [r for r in recs if r["b"] == s and r["lab"] == "pos"]
            out[s] = {"neg_todo": tasa(neg),
                      "neg_C0": tasa([r for r in neg if r["reg"] == "C0"]),
                      "neg_K": tasa([r for r in neg if r["reg"] == "K"]),
                      "pos_C0": tasa([r for r in pos if r["reg"] == "C0"]),
                      "pos_K": tasa([r for r in pos if r["reg"] == "K"])}
            if s == "VIIRS375":
                for reg in ("C0", "K"):
                    for zb in ("z<30", "z30-50", "z50-60", "z>=60"):
                        out[s][f"neg_{reg}_{zb}"] = tasa([r for r in neg if r["reg"] == reg and bp.zbin(r["z"]) == zb])
        res[modo] = out
        print(f"\n== modo D-9 {modo}, ventana {win}")
        for s, d in out.items():
            print(" ", s, {k: (v["n"], v["pct"]) for k, v in d.items()})
        if modo == "original":
            # predicado del auto-audit vs tablero (node) por noche con pasada pos
            noches = collections.defaultdict(lambda: {"node": 0, "audit": 0})
            for r in recs:
                if r["lab"] != "pos":
                    continue
                k = (r["vol"], r["b"], r["noche"])
                noches[k]["node"] = max(noches[k]["node"], r["pub"])
                v = r["pc_vrp"] or 0.0; cd = r["pc_dist"]
                ok = (0 < v <= aw.CAP) and cd is not None and cd <= aw.INNER[r["vol"]] and (not r["dc"] or r["dc"] == "summit")
                noches[k]["audit"] = max(noches[k]["audit"], int(ok))
            c = collections.Counter((s_, d["audit"], d["node"]) for (v_, s_, n_), d in noches.items())
            print("  noches pos (sensor, audit_dash, node_pub):", dict(sorted(c.items())))
            res["predicado_audit_vs_node"] = {f"{k[0]}|audit{k[1]}|node{k[2]}": n for k, n in c.items()}
    json.dump(res, open(os.path.join(os.path.dirname(__file__), "falsas_y_recall_por_regimen.json"), "w", encoding="utf-8"), indent=1)

main()
