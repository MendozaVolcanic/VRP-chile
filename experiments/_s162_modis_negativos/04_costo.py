# -*- coding: utf-8 -*-
"""S162 MODIS negativos, paso 4: costo en horas de runner MEDIDO del lote S159 (run 39712862945), no estimado a ojo.

Fuentes: (1) los `segundos` por pasada de resultados_MODIS_*.json (procesar() los mide de la bajada al final, K
incluido) y los `segundos` de K (resumen_k); (2) la duracion de cada job y de cada paso desde la API de GitHub
(jobs_39712862945.json, bajado con `gh api repos/MendozaVolcanic/VRP-chile/actions/runs/39712862945/jobs`).
Lo que este script NO mide: el costo de guardar el recorte nativo (no existia en S159); se informa como SIN DATO y
se acota con la prueba sin red (05_prueba_envoltorio.py imprime cuanto tarda en guardar un recorte sintetico).

Uso: python -I 04_costo.py --art D:\\vrp-trabajo\\temporales\\s159_portes\\run_39712862945 --previos objetivos_portes.json [--n 400 --nchunks 8]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent


def t(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--nchunks", type=int, default=8)
    ap.add_argument("--previos", default="", help="objetivos_portes.json de S159, para separar neg_resto")
    a = ap.parse_args()
    clases = {}
    if a.previos:
        clases = {o["id"]: o["clase"] for o in json.loads(Path(a.previos).read_text(encoding="utf-8"))}
    res, por_chunk = [], collections.defaultdict(list)
    for f in sorted(Path(a.art).rglob("resultados_MODIS_*.json")):
        ch = int(f.stem.split("_")[-1])
        for r in json.loads(f.read_text(encoding="utf-8")):
            res.append(r)
            por_chunk[ch].append(r)
    print("pasadas MODIS en los resultados:", len(res), "| estados:", dict(collections.Counter(r.get("estado") for r in res)))
    seg = np.array([r["segundos"] for r in res if r.get("segundos") is not None])
    ks = np.array([r["K"]["segundos"] for r in res if (r.get("K") or {}).get("segundos") is not None])
    sin_seg = [(r["id"], r.get("estado")) for r in res if r.get("segundos") is None]
    print(f"segundos por pasada (procesar, K incluido): n {len(seg)}, media {seg.mean():.1f}, mediana "
          f"{np.median(seg):.1f}, p95 {np.percentile(seg, 95):.1f}, max {seg.max():.1f}, suma {seg.sum():.0f}")
    print(f"  pasadas sin `segundos` (salieron antes del final de procesar): {sin_seg}")
    print(f"segundos de K por pasada: n {len(ks)}, media {ks.mean():.2f}, mediana {np.median(ks):.2f}, max {ks.max():.1f}"
          f" -> K es {100 * ks.sum() / seg.sum():.1f} % del tiempo por pasada")
    if clases:
        nr = np.array([r["segundos"] for r in res if clases.get(r["id"]) == "neg_resto" and r.get("segundos")])
        print(f"  solo neg_resto: n {len(nr)}, media {nr.mean():.1f}")

    J = json.loads((AQUI / "jobs_39712862945.json").read_text(encoding="utf-8"))["jobs"]
    print("\njobs MODIS (API de GitHub):")
    walls, overs, pasos_fijos = [], [], collections.defaultdict(list)
    for j in sorted(J, key=lambda j: j["name"]):
        if "MODIS" not in j["name"]:
            continue
        ch = int(j["name"].split(",")[1])
        w = (t(j["completed_at"]) - t(j["started_at"])).total_seconds()
        sp = sum(r.get("segundos") or 0 for r in por_chunk[ch])
        pr = [s for s in j["steps"] if s["name"] == "Probe"][0]
        wp = (t(pr["completed_at"]) - t(pr["started_at"])).total_seconds()
        for s in j["steps"]:
            if s["name"] != "Probe" and s.get("completed_at") and s.get("started_at"):
                pasos_fijos[s["name"]].append((t(s["completed_at"]) - t(s["started_at"])).total_seconds())
        walls.append(w)
        overs.append(w - sp)
        print(f"  {j['name']:<20} {j['conclusion']:<8} job {w:>5.0f} s | paso Probe {wp:>4.0f} s | suma de pasadas "
              f"{sp:>5.1f} s ({len(por_chunk[ch])} pasadas) | fuera de las pasadas {w - sp:>5.1f} s")
    fijo = float(np.mean(overs))
    print("  pasos fijos por job (media s):", {k: round(float(np.mean(v)), 1) for k, v in pasos_fijos.items()
                                               if np.mean(v) >= 1})
    print(f"  total runner MODIS S159: {sum(walls) / 3600:.3f} h en {len(walls)} jobs; fijo por job (job menos suma de "
          f"pasadas, incluye prueba sin red e instalacion) media {fijo:.0f} s")

    print(f"\n== proyeccion para {a.n} pasadas en {a.nchunks} trozos (media y p95 por pasada medidos arriba)")
    for nombre, por in (("con K re-corrido", seg.mean()), ("sin K", seg.mean() - ks.mean())):
        total = a.n * por + a.nchunks * fijo
        wall = (a.n / a.nchunks) * por + fijo
        wall95 = (a.n / a.nchunks) * np.percentile(seg, 95) + fijo
        print(f"  {nombre:<18}: {total / 3600:.2f} h de runner; cada job ~{wall / 60:.1f} min (con p95 por pasada "
              f"{wall95 / 60:.1f} min)")
    print("  costo de guardar el recorte nativo: SIN DATO en el runner (ver 05_prueba_envoltorio_salida.txt)")


if __name__ == "__main__":
    main()
