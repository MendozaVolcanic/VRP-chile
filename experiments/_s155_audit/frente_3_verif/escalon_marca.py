#!/usr/bin/env python3
"""F3-03: donde esta el escalon en los datos publicados (predicado real del tablero, node).
P1: si la marca estuviera en la fecha correcta, el escalon caeria en 10-18; se mide en que fecha cae.
P2: n por tramo impreso; tramo con n=0 = SIN DATO. Control positivo: el tramo C0 (9-01..9-17) debe
reproducir el 86,5 % de simular_cron (corrida C0)."""
import os, sys, json, collections
from pathlib import Path
AQUI = Path(__file__).resolve().parent; REPO = AQUI.parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts")); sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp, auto_audit_weekly as aw
from referencia_mirova_unificada import cargar_referencia_unificada
from pathlib import Path as P
win = ("2026-09-01", "2026-10-19")
coords = aw._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(P(AQUI / "ref_fresca/registro_vrp_consolidado.csv"), P(AQUI / "ref_fresca/registro_vrp_ocr.csv"),
                                    historico_path=P(AQUI / "historico_combinado.csv"))
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, win)
recs = bp.cargar_nuestros(coords, inner, win); bp.etiquetar(recs, por_vb, ns, nv)
def tramo(n): return "A_0901_0917" if n < "2026-09-18" else ("B_0918_1017" if n < "2026-10-18" else "C_1018_1019")
t = collections.defaultdict(lambda: [0, 0])
for r in recs:
    for clave in [("V375_neg_limpio", r["b"] == "VIIRS375" and r["lab"] == "neg_limpio"),
                  ("Chillan_todas", r["vol"] == "NevadosDeChillan"),
                  ("Chillan_neg_limpio", r["vol"] == "NevadosDeChillan" and r["lab"] == "neg_limpio"),
                  ("V375_todas", r["b"] == "VIIRS375")]:
        if clave[1]:
            k = (clave[0], tramo(r["noche"])); t[k][0] += 1; t[k][1] += r["pub"]
for k in sorted(t):
    n, p = t[k]; print(k, f"n={n} publica={p} pct={100*p/n:.1f}" if n else "SIN DATO")
