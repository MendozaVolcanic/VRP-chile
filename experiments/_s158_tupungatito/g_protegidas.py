# -*- coding: utf-8 -*-
"""S158. Todas las alertas «protegidas» (1 MW o más, lectura A) de MIROVA en Tupungatito VIIRS 375, nocturnas,
en la serie K con referencia (2026-02-14 a --hasta), y qué hizo nuestro record de la misma pasada.

POR QUÉ: #864 marcó dos protegidas perdidas que resultaron ser anomalías a 22,6 y 9,6 km (b_series_mirova.py).
Antes de decir que no se pierde ninguna de cráter hay que mirarlas todas, con la fuente de cada una (tabla u OCR)
y la distancia de NUESTRO record en esa pasada, que es independiente del OCR.

Uso: python -I g_protegidas.py --dest <temporal> [--hasta 2026-10-20]
"""
import argparse
import io
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import banco_paridad as bp  # noqa: E402
from auto_audit_weekly import _coords_por_volcan  # noqa: E402
from referencia_mirova_unificada import bajar_remoto, cargar_referencia_unificada  # noqa: E402

VOL, B = "Tupungatito", "VIIRS375"
ap = argparse.ArgumentParser()
ap.add_argument("--dest", required=True)
ap.add_argument("--hasta", default="2026-10-20")
a = ap.parse_args()
ventana = ("2026-02-14", a.hasta)
info = bajar_remoto(Path(a.dest))
filas = cargar_referencia_unificada(Path(info["registro_vrp_consolidado.csv"]["path"]),
                                    Path(info["registro_vrp_ocr.csv"]["path"]))
bp.VOLS = [VOL]
coords = _coords_por_volcan()
inner = bp.inner_desde_html()[VOL]
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana)
recs = [r for r in bp.cargar_nuestros(coords, {VOL: inner}, ventana) if r["b"] == B]
bp.etiquetar(recs, por_vb, ns, nv)
pub_noche = {r["noche"] for r in recs if r["pub"]}
import json  # noqa: E402
crudos = {(r["sensor"], r["datetime_utc"]): r
          for r in json.load(open(bp.DATA / f"{VOL}.json", encoding="utf-8"))["records"]}
L = [f"{VOL} {B} {ventana}; commit consolidado {info['registro_vrp_consolidado.csv']['sha']}, "
     f"OCR {info['registro_vrp_ocr.csv']['sha']}",
     "pasada            plataforma     fuente tipo                 VRP   dist_fila | nuestro: pub  clase  dist_cúmulo  VRP_cúmulo | noche publicada"]
n = 0
for dt, f in por_vb.get((VOL, B), []):
    if not (bp.es_alerta(f["tipo"]) and (f["vrp_mw"] or 0) >= 1.0):
        continue
    n += 1
    nuestro = [r for r in recs if abs((r["dt"] - dt).total_seconds()) <= bp.TOL_S]
    if nuestro:
        r = nuestro[0]
        crudo = crudos[(r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))]
        lejos = [p_ for p_ in (crudo.get("anomaly_pixels") or []) if p_["dist_km"] > inner]
        pl = max(lejos, key=lambda p_: p_["vrp_mw"]) if lejos else None
        txt = (f"{str(r['pub']):5s} {str(r['dc']):6s} {r['pc_dist']}  {r['pc_vrp']}  | píxeles alertados fuera de "
               f"{inner} km: {len(lejos)}" + (f", el mayor a {pl['dist_km']} km del cráter, {pl['vrp_mw']} MW, "
                                            f"{pl['bt_k']} K" if pl else ""))
        plat = r["sensor"]
    else:
        txt, plat = "sin record en ±120 s", "-"
    L.append(f"{dt:%Y-%m-%d %H:%M}  {plat:14s} {f['source']:5s}  {f['tipo']:20s} {f['vrp_mw']:5.2f} {f['dist_km']} | {txt} | "
             f"{dt.strftime('%Y-%m-%d') in pub_noche}")
L.append(f"total protegidas nocturnas: {n}")
txt = "\n".join(L)
print(txt)
(AQUI / "g_protegidas_salida.txt").write_text(txt + "\n", encoding="utf-8")
