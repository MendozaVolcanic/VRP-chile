# -*- coding: utf-8 -*-
"""Publicacion en negativos limpios de pasadas PARTIDAS (volcan en dos granulos) contra ENTERAS, por sensor y
detector (C0 / K / sin_marca, regla del auto-audit), variante orbita, ventana 2026-01-10 a 2026-10-21.
Pregunta 1: si las partidas publicaran igual que las enteras, lo veria? Si: misma etiqueta, mismo predicado.
Pregunta 2: el confusor obvio es el detector (C0 publica 30 veces mas que K en V375, A104): por eso se separa.
Tambien el cenit: se informa la mediana de cenit de cada grupo."""
import collections, statistics, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import variantes
bp, aaw = variantes.cargar(sys.argv[1])
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
ventana = ("2026-01-10", "2026-10-21")
coords = aaw._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana)
variantes.aplicar(bp, aaw, "orbita", {})
recs = bp.cargar_nuestros(coords, inner, ventana)
bp.etiquetar(recs, por_vb, ns, nv)
fr = aaw.leer_frontera_k()
c = collections.defaultdict(lambda: [0, 0, []])
for r in recs:
    if r["lab"] != "neg_limpio":
        continue
    k = (r["b"], aaw._detector_banco(r, fr), "partida" if r["n_cadena"] == 2 else "entera")
    c[k][0] += r["pub"]; c[k][1] += 1; c[k][2].append(r["z"] if r["z"] is not None else float("nan"))
print("frontera K:", fr)
for k in sorted(c):
    p, n, z = c[k]
    zz = [x for x in z if x == x]
    print(f"{k}: publica {p}/{n} = {100*p/n:.1f} %  cenit mediano {statistics.median(zz) if zz else None}")

# detalle de las partidas que publican en negativos limpios: que miembro publica y que fraccion del anillo tiene
import json
from scipy.stats import fisher_exact
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    pe, ne = c[(b, "K", "entera")][:2]; pp, npar = c[(b, "K", "partida")][:2]
    print(b, "Fisher partida vs entera:", fisher_exact([[pp, npar - pp], [pe, ne - pe]]))
cache = {}
def rec_de(vol, sensor, dt):
    if vol not in cache:
        cache[vol] = {(r["sensor"], r["datetime_utc"][:16]): r for r in
                      json.load(open(Path(sys.argv[1]) / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]}
    return cache[vol][(sensor, dt.strftime("%Y-%m-%d %H:%M"))]
quien = collections.Counter()
for r in recs:
    if r["lab"] == "neg_limpio" and r["n_cadena"] == 2 and r["pub"]:
        m = [rec_de(r["vol"], r["sensor"], h) for h in r["horas_cadena"]]
        anillos = [x.get("diag_n_bg_anillo") or 0 for x in m]
        i = r["pub_por_hora"].index(1)
        menor = anillos[i] <= min(anillos)
        quien[(r["b"], "publica_el_de_anillo_menor" if menor else "publica_el_de_anillo_mayor")] += 1
        print(f"  {r['b']} {r['vol']} {[h.strftime('%Y-%m-%d %H:%M') for h in r['horas_cadena']]} pub {r['pub_por_hora']} "
              f"anillo {anillos} pc_vrp {[(x.get('primary_cluster') or {}).get('vrp_mw') for x in m]} "
              f"dist {[(x.get('primary_cluster') or {}).get('centroid_dist_km') for x in m]} sigma_dnti {[x.get('diag_sd_dnti') for x in m]}")
print("quien publica:", dict(quien))
