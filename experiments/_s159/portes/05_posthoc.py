# -*- coding: utf-8 -*-
"""S159 PORTES, lecturas POST HOC (no estaban pre-registradas; se declaran así en el informe). Nacen de mirar las 6
protegidas de VIIRS 375 que el port «pierde» en 04_analizar: las 6 son alertas sólo OCR, 5 de Suomi NPP antes del
2026-10-09, el tramo en que A119 avisa que la distancia y la clase de esas filas pueden ser de OTRA pasada (el VRP sí
es de la suya), y el port las detecta con un VRP igual al de MIROVA pero con los píxeles a 9 a 24 km del cráter.

(a) Etiqueta depurada: se sacan del recall las alertas cuya única fila es OCR de Suomi NPP antes del 2026-10-09
    (calidad_referencia_mirova, hito 2026-10-09). Se recalculan R1 y R2.
(b) Record sintético alternativo: summit si ALGÚN alertado está a inner_radius_km o menos (en vez del centroide).
(c) Detalle: negativos limpios que el port publica, alertas que no publica, saturación y escena inválida.
Pregunta 1: si la depuración no cambiara nada, (a) daría lo mismo que 04; se imprime el antes y el después.
Uso: python -I 05_posthoc.py --art D:\\vrp-trabajo\\temporales\\s159_portes\\run_39712862945
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(AQUI))
import banco_paridad as B  # noqa: E402
import importlib.util  # noqa: E402

_s = importlib.util.spec_from_file_location("an", AQUI / "04_analizar.py")
AN = importlib.util.module_from_spec(_s)
_s.loader.exec_module(AN)
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def fila_dudosa(o):
    """Toda fila de alerta de la pasada es OCR de Suomi NPP anterior al 2026-10-09 (hito A119)."""
    al = [m for m in o["mirova"] if B.es_alerta(m["tipo"])]
    return bool(al) and o["sensor"] == "VIIRS_SNPP" and o["hora_utc"][:10] < "2026-10-09" and all(
        m["source"] == "OCR" for m in al)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.loads((AQUI / "objetivos_portes.json").read_text(encoding="utf-8"))}
    res = {}
    for f in sorted(Path(a.art).rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            res[r["id"]] = r
    inner = B.inner_desde_html()
    ok = [i for i, r in res.items() if r.get("estado") == "ok" and obj[i]["b"] != "VIIRS750"]
    casos, idx = [], []
    for i in ok:
        o, r = obj[i], res[i]
        for m in ("fisica", "sensible"):
            p = r["port"][m]
            if p.get("npix"):
                p["_dcen"] = AN.dist_centroide(p, o["grilla"])
            for regla in ("centroide", "minimo"):
                rp = AN.record_port(p, inner[o["volcan"]], o["sensor"])
                if regla == "minimo" and p.get("npix"):
                    dmin = min(q[3] for q in p["pixeles"])
                    rp["distance_class"] = "summit" if dmin <= inner[o["volcan"]] else "far"
                    rp["primary_cluster"]["centroid_dist_km"] = round(dmin, 3)
                rp = {k: x for k, x in rp.items() if not k.startswith("_")}
                casos.append([AN.slim(rp), inner[o["volcan"]]])
                idx.append((i, m, regla))
    P = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))}
    for b in ("VIIRS375", "MODIS"):
        ids = [i for i in ok if obj[i]["b"] == b]
        pos = [i for i in ids if obj[i]["lab"] == "pos"]
        dud = [i for i in pos if fila_dudosa(obj[i])]
        pr(f"\n== {b}: alertas de la muestra {len(pos)}, con fila dudosa (sólo OCR de Suomi NPP antes del 2026-10-09) "
           f"{len(dud)} (protegidas {sum(obj[i]['clase'] == 'pos_prot' for i in dud)})")
        for m in ("fisica", "sensible"):
            for regla in ("centroide", "minimo"):
                for nombre, lst in (("todas", pos), ("depuradas", [i for i in pos if i not in dud])):
                    prot = [i for i in lst if obj[i]["clase"] == "pos_prot"]
                    bajo = [i for i in lst if obj[i]["clase"] == "pos_bajo"]
                    perd = [i for i in prot if obj[i]["pub_prod"] and not P[(i, m, regla)]]
                    wp = sum(obj[i]["peso"] for i in prot)
                    wb = sum(obj[i]["peso"] for i in bajo)
                    rp = sum(obj[i]["peso"] for i in prot if P[(i, m, regla)]) / wp if wp else float("nan")
                    rb = sum(obj[i]["peso"] for i in bajo if P[(i, m, regla)]) / wb if wb else float("nan")
                    kp = sum(obj[i]["peso"] for i in prot if obj[i]["pub_prod"]) / wp if wp else float("nan")
                    kb = sum(obj[i]["peso"] for i in bajo if obj[i]["pub_prod"]) / wb if wb else float("nan")
                    pr(f"  {m:8s} {regla:9s} {nombre:9s}: protegidas perdidas contra K {len(perd)} de "
                       f"{sum(bool(obj[i]['pub_prod']) for i in prot)}; recall pond. prot {rp:.3f} (K {kp:.3f}), "
                       f"bajo {rb:.3f} (K {kb:.3f}); n prot {len(prot)}, bajo {len(bajo)}"
                       + (f"; perdidas {[(obj[i]['volcan'], obj[i]['hora_utc']) for i in perd]}" if perd else ""))
            neg = [i for i in ids if obj[i]["lab"] == "neg_limpio"]
            for regla in ("centroide", "minimo"):
                w = sum(obj[i]["peso"] for i in neg)
                t = sum(obj[i]["peso"] for i in neg if P[(i, m, regla)]) / w
                pr(f"  {m:8s} {regla:9s} negativos limpios publicados: {sum(P[(i, m, regla)] for i in neg)} de {len(neg)} "
                   f"crudo, ponderado {t:.4f}")
        # detalle
        pr(f"\n  {b} negativos que el port (física, centroide) publica:")
        for i in ids:
            o = obj[i]
            if o["lab"] == "neg_limpio" and P[(i, "fisica", "centroide")]:
                p = res[i]["port"]["fisica"]
                pr("    ", i, o["volcan"], o["hora_utc"], o["clase"], "K pub" if o["pub_prod"] else "K no",
                   "npix", p["npix"], "vrp", round(p["vrp_mw"], 3), "banda", [round(x, 3) for x in p.get("vrp_banda", [])],
                   "dist", [q[3] for q in p["pixeles"]][:6], "MIROVA", [(m["tipo"], m["vrp_mw"]) for m in o["mirova"]])
        pr(f"  {b} alertas que el port (física, centroide) NO publica:")
        for i in pos:
            o = obj[i]
            if not P[(i, "fisica", "centroide")]:
                p = res[i]["port"]["fisica"]
                pr("    ", i, o["volcan"], o["hora_utc"], o["clase"], "K pub" if o["pub_prod"] else "K no",
                   "npix", p["npix"], "vrp", None if p["vrp_mw"] is None else round(p["vrp_mw"], 3),
                   "MIROVA", o["mirova_vrp"], [(m["source"], m["dist_km"]) for m in o["mirova"] if B.es_alerta(m["tipo"])],
                   "dist port", sorted(q[3] for q in p["pixeles"])[:4], "motivo", p["motivo_vacio"],
                   "dudosa" if fila_dudosa(o) else "")
        sat = [(obj[i]["volcan"], obj[i]["hora_utc"], res[i].get("saturados")) for i in ids
               if any((v or 0) > 0 for v in (res[i].get("saturados") or {}).values())]
        pr(f"  {b} pasadas con píxeles saturados en el recorte:", sat[:15])
    # Chillán grandes: razón por magnitud de MIROVA
    pr("\n== razón port/MIROVA por tamaño de la alerta de MIROVA (física, alertas que el port publica):")
    for b in ("VIIRS375", "MODIS"):
        ids = [i for i in ok if obj[i]["b"] == b and obj[i]["lab"] == "pos" and P[(i, "fisica", "centroide")]]
        for lo, hi in ((0, 1), (1, 3), (3, 100)):
            rr = [res[i]["port"]["fisica"]["vrp_mw"] / obj[i]["mirova_vrp"] for i in ids if lo <= obj[i]["mirova_vrp"] < hi]
            if rr:
                q = np.percentile(rr, [25, 50, 75])
                pr(f"  {b} MIROVA {lo} a {hi} MW: mediana {q[1]:.3f} [{q[0]:.3f}, {q[2]:.3f}] n {len(rr)}")
    (AQUI / "05_posthoc_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
