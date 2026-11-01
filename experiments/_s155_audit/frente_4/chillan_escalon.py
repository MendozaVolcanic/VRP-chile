# -*- coding: utf-8 -*-
"""Nevados de Chillan (en erupcion) alrededor del escalon C0 -> K del 2026-09-18: por dia, pasadas
nocturnas publicadas y suma de magnitud publicada (mirovaEqVrpDisplay por node), todos los sensores,
contra la suma de VRP de las ALERTAS de MIROVA de ese dia (referencia snapshot). Es lo que el operador
ve en la tendencia. P1: si el escalon fuera del volcan, MIROVA tambien bajaria ese dia. P2: la columna
de MIROVA es el control externo; la de 'K' (processed_utc posterior al merge) es el control de regimen."""
import sys, io, json, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402
coords = B._coords_por_volcan(); inner = B.inner_desde_html()
assert B.control_identidad_predicado() == ([0, 1, 1, 1, 0], [1, 0])
ven = ("2026-09-04", "2026-10-02")
filas = B.cargar_referencia_unificada(B.SNAP_CONS, B.SNAP_OCR)
por_vb, ns, nv, _ = B.indexar_referencia(filas, coords, ven)
recs = [r for r in B.cargar_nuestros(coords, inner, ven) if r["vol"] == "NevadosDeChillan"]
mir = collections.defaultdict(lambda: [0, 0.0])
for (vol, b), lista in por_vb.items():
    if vol != "NevadosDeChillan": continue
    for dt, f in lista:
        if B.es_alerta(f["tipo"]):
            mir[f["fecha_utc"][:10]][0] += 1; mir[f["fecha_utc"][:10]][1] += f["vrp_mw"] or 0
d = collections.defaultdict(lambda: [0, 0, 0.0])
for r in recs:
    x = d[r["noche"]]; x[0] += 1; x[1] += r["pub"]; x[2] += (r["disp"] or 0) if r["pub"] else 0
print("dia | pasadas noct | publicadas | suma MW publicada | MIROVA alertas | suma MW MIROVA")
for k in sorted(d):
    n, p, s = d[k]; m = mir.get(k, [0, 0.0])
    print(f"{k}  {n:3d}  {p:3d}  {s:7.2f}   {m[0]:3d}  {m[1]:7.2f}")
