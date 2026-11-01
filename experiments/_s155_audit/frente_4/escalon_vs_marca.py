# -*- coding: utf-8 -*-
"""¿Donde cae el escalon C0 -> K en la serie que ve el operador, y donde lo marca el tablero?
frontend/cambio_detector.js dibuja la linea vertical en CAMBIO_DETECTOR_UTC (hora del merge de #850),
sobre el eje de la fecha de OBSERVACION. Pero los records se reprocesaron con K hacia atras (ventana
2026-09-18 a 2026-10-18 y el historico por trozos de #852). Este script cuenta, por dia de observacion,
la fraccion de pasadas nocturnas VIIRS 375 que el tablero publica (predicado node de banco_paridad) y
la fraccion de records con processed_utc posterior al merge (= detector K), para 14 dias alrededor
de 2026-09-18 y de 2026-10-18.
P1: si la marca estuviera bien puesta, el escalon de publicacion y el cambio de detector caerian en la
fecha de la marca; si no, caen en otra y el script lo muestra. P2: la columna 'fraccion K' es el
control: debe saltar de ~0 a ~1 en algun dia; si diera 0 en todos, el lector de processed_utc
estaria muerto.
"""
import sys, io, json, collections
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402
import re
js = (ROOT / "frontend" / "cambio_detector.js").read_text(encoding="utf-8")
marca = re.search(r'CAMBIO_DETECTOR_UTC = "([^"]+)"', js).group(1)
print("marca del tablero (cambio_detector.js):", marca)
MERGE = "2026-10-18T09:57:30"
coords = B._coords_por_volcan(); inner = B.inner_desde_html()
assert B.control_identidad_predicado() == ([0, 1, 1, 1, 0], [1, 0])
proc = {}
for v in B.VOLS:
    for r in json.load(open(B.DATA / f"{v}.json", encoding="utf-8"))["records"]:
        proc[(v, r.get("datetime_utc"), B.bucket(r.get("sensor")), r.get("sensor"))] = (r.get("processed_utc") or "")[:19] >= MERGE
for centro in ("2026-09-18", "2026-10-18"):
    c0 = datetime.strptime(centro, "%Y-%m-%d")
    ven = ((c0 - timedelta(days=7)).strftime("%Y-%m-%d"), (c0 + timedelta(days=6)).strftime("%Y-%m-%d"))
    recs = B.cargar_nuestros(coords, inner, ven)
    pk = {}
    for (v, dt, b, s), k in proc.items():
        if b == "VIIRS375" and dt and ven[0] <= dt[:10] <= ven[1]:
            pk.setdefault(dt[:10], []).append(k)
    por_dia = collections.defaultdict(lambda: [0, 0])
    for r in recs:
        if r["b"] == "VIIRS375":
            d = r["noche"]; por_dia[d][0] += r["pub"]; por_dia[d][1] += 1
    print(f"\n== alrededor de {centro}: dia | VIIRS375 nocturnas publicadas | fraccion de records V375 con detector K")
    for d in sorted(por_dia):
        p, n = por_dia[d]; ks = pk.get(d, [])
        print(f"   {d}  {p:3d}/{n:3d} = {p/n:5.2f}   K {sum(ks)}/{len(ks)}")
