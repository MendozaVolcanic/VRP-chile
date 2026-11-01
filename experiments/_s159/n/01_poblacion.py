# -*- coding: utf-8 -*-
"""S159 frente N, paso 1: población de pasadas VIIRS 750 (alertas de MIROVA y negativos limpios), sin red salvo la
referencia remota de Mirova-v1.

POR QUÉ. El fondo y la suma del código de MIROVA se probaron en 3 alertas y 1 negativo (AUDIT_S158_R2 §3). El
criterio de victoria de docs/MISSION.md se mide en las dos direcciones: recall de las alertas de MIROVA y
publicación en negativos limpios. Este paso arma la lista de pasadas que el workflow de sólo lectura va a reprocesar
con los cuatro brazos (K, F, C, FC) y el oráculo.

Etiquetas: las de scripts/banco_paridad.py (etiquetar), con la regla D-9 en modo SN (clase_mirova, decidida; en
VIIRS 750 no toca ninguna fila porque SENSORES_MINIMA = VIIRS375) y la lectura A para la alerta protegida
(clase_mirova.alerta_protegida). Pareo: el de banco_paridad (+-120 s); se informa también el pareo a 8 min (R2.3)
y cuántas etiquetas cambian.

Las dos preguntas del instrumento.
P1 (si la etiqueta estuviera rota, ¿se vería?): control todo/nada: si las etiquetas fueran al azar, la fracción de
pasadas pos con alerta de MIROVA de VRP > 0 no sería 1; se imprime. Y se cruza el conteo de alertas V750 de la
referencia con el de pasadas pos más alertas sin record (tienen que sumar).
P2 (instrumento muerto): si no cargara records o referencia, los conteos darían 0; el script aborta con 0.

Fuente de records: data/mirova_equivalent de origin/main extraída a D:\\vrp-trabajo\\temporales\\s159_n\\data_main
(regla 5 del workspace: frescura desde el remoto). Ventana: 2026-04-01 a 2026-10-21 (A119: VIIRS por pasada desde
abril).
Uso: python 01_poblacion.py --data D:\\vrp-trabajo\\temporales\\s159_n\\data_main --ref-dest D:\\...\\ref
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402
from clase_mirova import alerta_protegida  # noqa: E402
from referencia_mirova_unificada import bajar_remoto, cargar_referencia_unificada  # noqa: E402

VENTANA = ("2026-04-01", "2026-10-21")
FRONTERA_OCR = "2026-06-13"   # A119: antes, la etiqueta positiva que decide es la de la tabla sola
TOPE = 400


def estrato_cenit(z):
    if z is None:
        return "z?"
    return "z<=40" if z <= 40 else "z>40"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--ref-dest", required=True)
    ap.add_argument("--semilla", type=int, default=159)
    a = ap.parse_args()

    info = bajar_remoto(Path(a.ref_dest))
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    print("referencia remota:", {k: v["sha"] for k, v in info.items()})
    coords = B._coords_por_volcan()
    inner = B.inner_desde_html()
    filas = cargar_referencia_unificada(cons, ocr)
    por_vb, ns, nv, n_ref = B.indexar_referencia(filas, coords, VENTANA, regla_minimas="SN")
    recs = B.cargar_nuestros(coords, inner, VENTANA, data=a.data)
    assert n_ref > 0 and recs, "instrumento muerto: sin referencia o sin records"

    # granule y campos extra de cada record (cargar_nuestros no los guarda)
    extra = {}
    for vol in B.VOLS:
        d = json.loads((Path(a.data) / f"{vol}.json").read_text(encoding="utf-8"))
        for r in d["records"]:
            if B.bucket(r.get("sensor")) != "VIIRS750":
                continue
            pc = r.get("primary_cluster") or {}
            extra[(vol, r.get("sensor"), r.get("datetime_utc"))] = {
                "granule": r.get("granule"), "pc_vrp": pc.get("vrp_mw"), "pc_n": pc.get("n_pixels"),
                "vrp_mw": r.get("vrp_mw"), "n_px": r.get("n_anomalous_pixels"), "dc": r.get("distance_class"),
                "pc_dist": pc.get("centroid_dist_km"), "sha": (r.get("regimen") or {}).get("codigo_sha"),
                "processed_utc": r.get("processed_utc")}

    # etiquetas a +-120 s (las del banco) y a +-480 s (R2.3)
    B.etiquetar(recs, por_vb, ns, nv)
    lab120 = {id(r): r["lab"] for r in recs}
    parear_orig = B.parear
    B.parear = lambda lista, t, tol=480: parear_orig(lista, t, tol)
    recs8 = [dict(r) for r in recs]
    B.etiquetar(recs8, por_vb, ns, nv)
    B.parear = parear_orig
    v750 = [r for r in recs if r["b"] == "VIIRS750"]
    cambio = collections.Counter((lab120[id(r)], r8["lab"]) for r, r8 in zip(recs, recs8)
                                 if r["b"] == "VIIRS750" and lab120[id(r)] != r8["lab"])
    print(f"records V750 nocturnos en ventana: {len(v750)}; etiquetas 120 s:",
          dict(collections.Counter(r['lab'] for r in v750)))
    print("cambios de etiqueta 120 s -> 480 s (V750):", dict(cambio) or "ninguno")

    # dt al vecino de referencia mas cercano, para pos (cuanto se aleja la hora de MIROVA de la nuestra)
    filas_v750 = [f for f in filas if f["sensor_bucket"] == "VIIRS750"]
    out = []
    for r in v750:
        if r["lab"] not in ("pos", "neg_limpio"):
            continue
        ref = B.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        ex = extra.get((r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")), {})
        alertas = [f for f in ref if B.es_alerta(f["tipo"])]
        prot = any(alerta_protegida(f) for f in ref)
        tabla = any(f["source"] == "CONS" for f in alertas)
        dts = [abs((datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    - r["dt"]).total_seconds()) for f in ref]
        out.append({
            "volcan": r["vol"], "hora_utc": r["dt"].strftime("%Y-%m-%d %H:%M"), "sensor": r["sensor"],
            "lab": r["lab"], "protegida": prot, "alerta_tabla": tabla,
            "decide": (r["lab"] == "neg_limpio") or tabla or r["noche"] >= FRONTERA_OCR,
            "mirova": [{k: f[k] for k in ("fecha_utc", "tipo", "vrp_mw", "dist_km", "source")} for f in ref],
            "mirova_vrp": max([f["vrp_mw"] or 0 for f in alertas], default=0.0),
            "dt_ref_s": min(dts) if dts else None,
            "z": r["z"], "estrato_z": estrato_cenit(r["z"]), "pub_prod": r["pub"], "dc": r["dc"],
            "pc_vrp": r["pc_vrp"], **{k: ex.get(k) for k in ("granule", "pc_n", "vrp_mw", "n_px", "pc_dist",
                                                             "sha", "processed_utc")},
        })
    pos = [o for o in out if o["lab"] == "pos"]
    neg = [o for o in out if o["lab"] == "neg_limpio"]
    sin_rec = B.alertas_sin_record(por_vb, recs)
    sin_rec_v750 = {k: v for k, v in sin_rec.items() if k[1] == "VIIRS750"}
    print(f"pos V750: {len(pos)} (protegidas {sum(o['protegida'] for o in pos)}, deciden {sum(o['decide'] for o in pos)},"
          f" solo OCR antes de {FRONTERA_OCR}: {sum(not o['decide'] for o in pos)}); neg limpios V750: {len(neg)}")
    print("alertas V750 de MIROVA sin record nuestro (+-120 s):", sum(sin_rec_v750.values()), dict(sin_rec_v750))
    print("P1: pos con VRP de MIROVA > 0:", sum(o["mirova_vrp"] > 0 for o in pos), "de", len(pos))
    print("dt al vecino de referencia (s), pos: max", max((o["dt_ref_s"] or 0) for o in pos),
          "| neg: max", max((o["dt_ref_s"] or 0) for o in neg))
    print("pos sin granule:", sum(1 for o in pos if not o["granule"]), "neg sin granule:",
          sum(1 for o in neg if not o["granule"]))
    for nombre, lst in (("pos", pos), ("neg", neg)):
        c = collections.Counter((o["volcan"], o["estrato_z"]) for o in lst)
        print(nombre, "por volcan y cenit:", dict(sorted(c.items())))
        print(nombre, "publica produccion:", sum(o["pub_prod"] for o in lst), "de", len(lst))

    Path(AQUI / "poblacion_completa.json").write_text(json.dumps(
        {"meta": {"ventana": VENTANA, "referencia": {k: v["sha"] for k, v in info.items()},
                  "data_records": "origin/main " + "533398f8f", "tol_pareo_s": 120,
                  "regla_minimas": "SN", "lectura_protegida": "A"},
         "pasadas": out}, ensure_ascii=False, indent=0, default=str), encoding="utf-8")
    print("escrito poblacion_completa.json:", len(out))


if __name__ == "__main__":
    main()
