# -*- coding: utf-8 -*-
"""Lectura del A/B de D18 — la geometria del ROI1.

Escrita ANTES de que termine el reproceso (A16). Aplica los criterios CONGELADOS
en docs/s130/PREREGISTRO_AB_D18.md y no los reinterpreta.

Las cuatro firmas, y por que F4 es la que arbitra: la caja del paper va a recortar
detecciones — eso no esta en duda, es la direccion del cambio. Lo que hay que saber
es si recorta ARTEFACTO o SENAL. Si recorta el sesgo topografico A69, el cluster
deberia ACERCARSE al crater en los nevados, porque lo que se va es la cola difusa
ladera abajo. Si recorta cat-b real (Lazufre, lacolito), se pierden detecciones sin
que la posicion mejore.

Estratificado por volcan SIEMPRE (A83 p.3, feedback_s126_estratificar_por_volcan):
la mediana agrupada de los seis promedia regimenes opuestos y esconde el veredicto.

Uso:
    python experiments/_s130_d18/veredicto_d18.py --dir <artefactos_ordenados>
"""
import argparse
import io
import json
import os
import statistics as st
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments"))

from _s126_lib import bucket, cargar_mirova                       # noqa: E402

BRAZOS = ["_s130_d18_circulo", "_s130_d18_caja"]
REGIMEN = {
    "Lascar": "focal",
    "Lastarria": "focal (CANARIO cat-b)",
    "Llaima": "nevado",
    "Copahue": "nevado",
    "Villarrica": "nevado",
    "PuyehueCordonCaulle": "difuso (lacolito real)",
}


def cargar(d, brazo):
    out = {}
    base = os.path.join(d, brazo)
    if not os.path.isdir(base):
        return out
    for fn in sorted(os.listdir(base)):
        if fn.endswith(".json"):
            doc = json.load(open(os.path.join(base, fn), encoding="utf-8"))
            out[fn[:-5]] = doc.get("records", doc) if isinstance(doc, dict) else doc
    return out


def valida(r):
    """isValidDetection() del frontend — index.html:1372."""
    return (r.get("vrp_mw") or 0) > 0 or r.get("triggered_test1") is True


def summit(r):
    """isSummitDetection() del frontend — index.html:1378."""
    v = r.get("vrp_mw") or 0
    if v == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
        return False
    dc = r.get("distance_class")
    if dc == "summit":
        return True
    if dc == "far":
        return False
    return (r.get("vrp_vent_mw") or 0) > 0


def firmas(recs, mir, vol, pasadas):
    """Las cuatro firmas para un volcan y un brazo, sobre las pasadas comunes."""
    n_det = 0
    offsets = []
    ratios = []
    noches_ok = set()
    for r in recs:
        dt = r.get("datetime_utc") or ""
        if dt[:16] not in pasadas:
            continue
        if not (valida(r) and summit(r)):
            continue
        n_det += 1
        pc = r.get("primary_cluster") or {}
        d = pc.get("centroid_dist_km")
        if d is None:
            d = r.get("final_hotspot_dist_km")
        if d is not None:
            offsets.append(d)
        b = bucket(r.get("sensor"))
        m = (mir.get(vol) or {}).get((dt[:10], b))
        v = pc.get("vrp_mw") or 0
        if m and m > 0 and v > 0:
            ratios.append(v / m)
            noches_ok.add((dt[:10], b))
    return {
        "n_detecciones": n_det,                                              # F3
        "offset_mediano_km": round(st.median(offsets), 3) if offsets else None,   # F4
        "ratio_mediano": round(st.median(ratios), 3) if ratios else None,         # F2
        "noches_mirova": noches_ok,                                          # F1
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="dir con _s130_d18_<brazo>/ dentro")
    args = ap.parse_args()

    datos = {b: cargar(args.dir, b) for b in BRAZOS}
    mir, _ = cargar_mirova(("2026-01-01", "2026-12-31"))

    print("=" * 78)
    print("A/B S130 - D18: la geometria del ROI1 (circulo per-volcan vs caja 5x5 km)")
    print("=" * 78)
    print("Criterios congelados: docs/s130/PREREGISTRO_AB_D18.md\n")

    # CONTROL DE INSTRUMENTO primero: si los brazos no difieren, no hay nada que leer.
    # Es la leccion del A/B de los fondos, que dio cuatro firmas identicas porque sus
    # flags no tenian sustrato (docs/s130/AB_FONDOS_SIN_SUSTRATO.md).
    total_dif = 0
    for vol in sorted(REGIMEN):
        a = {(r.get("datetime_utc"), r.get("sensor")): r
             for r in datos[BRAZOS[0]].get(vol, [])}
        b = {(r.get("datetime_utc"), r.get("sensor")): r
             for r in datos[BRAZOS[1]].get(vol, [])}
        for k in set(a) & set(b):
            va = (a[k].get("primary_cluster") or {}).get("vrp_mw") or 0
            vb = (b[k].get("primary_cluster") or {}).get("vrp_mw") or 0
            if va != vb:
                total_dif += 1
    print(f"CONTROL DE INSTRUMENTO - records con pc.vrp distinto entre brazos: {total_dif}")
    if total_dif == 0:
        print("  CERO. Los brazos son el mismo brazo: INCONCLUSO, no leer mas.")
        print("  Es el escenario del A/B de los fondos, docs/s130/AB_FONDOS_SIN_SUSTRATO.md")
        return 1
    print()

    res = {}
    for vol in sorted(REGIMEN, key=lambda v: REGIMEN[v]):
        recs_c = datos[BRAZOS[0]].get(vol, [])
        recs_j = datos[BRAZOS[1]].get(vol, [])
        if not recs_c or not recs_j:
            print(f"[falta data] {vol}")
            continue
        # Interseccion de pasadas: sin esto, un brazo que vio mas granules "detecta
        # mas" sin que el flag tenga nada que ver.
        p_c = {(r.get("datetime_utc") or "")[:16] for r in recs_c}
        p_j = {(r.get("datetime_utc") or "")[:16] for r in recs_j}
        comunes = p_c & p_j
        f_c = firmas(recs_c, mir, vol, comunes)
        f_j = firmas(recs_j, mir, vol, comunes)
        perdidas = f_c["noches_mirova"] - f_j["noches_mirova"]
        res[vol] = {
            "regimen": REGIMEN[vol],
            "n_pasadas_comunes": len(comunes),
            "circulo": {k: v for k, v in f_c.items() if k != "noches_mirova"},
            "caja": {k: v for k, v in f_j.items() if k != "noches_mirova"},
            "noches_mirova_perdidas": len(perdidas),
            "pct_detecciones_perdidas": round(
                100 * (f_c["n_detecciones"] - f_j["n_detecciones"])
                / f_c["n_detecciones"], 1) if f_c["n_detecciones"] else None,
        }

    print(f"{'volcan':22s} {'regimen':24s} {'det circ':>9s} {'det caja':>9s} "
          f"{'% pierde':>9s} {'off circ':>9s} {'off caja':>9s} {'MIROVA perd':>12s}")
    print("-" * 112)
    for vol, d in res.items():
        c, j = d["circulo"], d["caja"]
        print(f"{vol:22s} {d['regimen']:24s} {c['n_detecciones']:9d} "
              f"{j['n_detecciones']:9d} {str(d['pct_detecciones_perdidas']) + '%':>9s} "
              f"{str(c['offset_mediano_km']):>9s} {str(j['offset_mediano_km']):>9s} "
              f"{d['noches_mirova_perdidas']:12d}")

    print()
    print("F4 ES LA QUE ARBITRA: si el offset BAJA en los nevados, la caja recorto")
    print("artefacto topografico (A69). Si no baja y ademas se pierden detecciones,")
    print("recorto senal.")
    print()
    print("LIMITES DEL PRE-REGISTRO (no adoptar si se cruzan):")
    for vol, lim in (("Lastarria", 20), ("PuyehueCordonCaulle", 50)):
        if vol in res:
            p = res[vol]["pct_detecciones_perdidas"]
            ok = "OK" if (p is not None and p <= lim) else "CRUZADO"
            print(f"  {vol:22s} pierde {p}% (limite {lim}%)  -> {ok}")

    out = os.path.join(HERE, "veredicto_d18.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
