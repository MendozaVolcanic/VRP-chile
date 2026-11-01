# -*- coding: utf-8 -*-
"""S159 frente PORTES, paso 1: población de pasadas VIIRS 375 y MODIS nocturnas (alertas de MIROVA y negativos
limpios) para portar el código de VIIRS 750 de MIROVA a esos dos sensores.

POR QUÉ. MIROVA publicó en OSF su código sólo para VIIRS 750, y el frente N mostró que en la grilla de GEO reproduce
su magnitud (razón 0,999). Para VIIRS 375 y MODIS no hay código ni paper que describa la detección (P2, P3). Esta
población es la vara contra la que se mide si el MISMO código, cambiando sólo bandas, grilla y coeficiente, reproduce
lo que MIROVA publicó (A115: la decisión se mide contra MIROVA, no se elige).

Etiquetas: scripts/banco_paridad.py (etiquetar, pareo a +-120 s) con la regla D-9 en modo SN (en VIIRS 375 una alerta
de 0,05 MW o menos cuenta como «MIROVA no vio nada»; clase_mirova.SENSORES_MINIMA = VIIRS375). Protegida = lectura A
(clase_mirova.alerta_protegida). Ventanas (A119): VIIRS 375 por pasada desde 2026-04-01; MODIS desde 2026-03-01;
hasta 2026-10-21. Los días 17 a 20 de octubre se excluyen en la selección (paso 2), no aquí.

Pasada partida: otro record nuestro del mismo volcán y la misma plataforma a 7 min o menos (el gránulo vecino). El
verificador del pareo MODIS (experiments/_s159/pareo_modis/verificador/INFORME.md) midió que MIROVA lista el gránulo
sur y sólo alerta si el cráter está en él; esas pasadas se marcan y se informan aparte.

Las dos preguntas del instrumento.
P1 (si la etiqueta estuviera rota, ¿se vería?): toda pasada pos tiene que tener una alerta de MIROVA con VRP > 0
(control todo o nada, se imprime) y las alertas de la referencia sin record nuestro se cuentan aparte.
P2 (instrumento muerto): sin records o sin referencia los conteos dan 0 y el script aborta.

Fuente de records: data/mirova_equivalent de origin/main 533398f8f extraída por el frente N a
D:\\vrp-trabajo\\temporales\\s159_n\\data_main (desde entonces sólo hay commits «NRT update» de pasadas posteriores al
2026-10-21; verificado con git log 533398f8f..origin/main -- data/mirova_equivalent).
Uso: python -I 01_poblacion.py --data D:\\vrp-trabajo\\temporales\\s159_n\\data_main --ref-dest D:\\vrp-trabajo\\temporales\\s159_portes\\ref
"""
from __future__ import annotations

import argparse
import collections
import json
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

VENTANAS = {"VIIRS375": ("2026-04-01", "2026-10-21"), "MODIS": ("2026-03-01", "2026-10-21")}
FRONTERA_OCR = "2026-06-13"   # A119: antes, la alerta que decide es la de la tabla sola
PARTIDA_S = 7 * 60


def estrato_cenit(z):
    if z is None:
        return "z?"
    return "z<=40" if z <= 40 else "z>40"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--ref-dest", required=True)
    a = ap.parse_args()

    info = bajar_remoto(Path(a.ref_dest))
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    print("referencia remota:", {k: v["sha"] for k, v in info.items()})
    coords = B._coords_por_volcan()
    inner = B.inner_desde_html()
    filas = cargar_referencia_unificada(cons, ocr)
    vent_total = ("2026-03-01", "2026-10-21")
    por_vb, ns, nv, n_ref = B.indexar_referencia(filas, coords, vent_total, regla_minimas="SN")
    recs = B.cargar_nuestros(coords, inner, vent_total, data=a.data)
    assert n_ref > 0 and recs, "instrumento muerto: sin referencia o sin records"

    extra = {}
    for vol in B.VOLS:
        d = json.loads((Path(a.data) / f"{vol}.json").read_text(encoding="utf-8"))
        for r in d["records"]:
            if B.bucket(r.get("sensor")) not in VENTANAS:
                continue
            pc = r.get("primary_cluster") or {}
            extra[(vol, r.get("sensor"), r.get("datetime_utc"))] = {
                "granule": r.get("granule"), "pc_n": pc.get("n_pixels"), "vrp_mw": r.get("vrp_mw"),
                "n_px": r.get("n_anomalous_pixels"), "pc_dist": pc.get("centroid_dist_km"),
                "f5_core": r.get("f5_core_vrp_mw"), "sha": (r.get("regimen") or {}).get("codigo_sha")}

    B.etiquetar(recs, por_vb, ns, nv)
    # pasadas partidas: otro record del mismo volcán y la misma plataforma a <= 7 min
    por_vs = collections.defaultdict(list)
    for r in recs:
        por_vs[(r["vol"], r["sensor"])].append(r["dt"])
    out = []
    for r in recs:
        b = r["b"]
        if b not in VENTANAS:
            continue
        v0, v1 = VENTANAS[b]
        if not (v0 <= r["noche"] <= v1) or r["lab"] not in ("pos", "neg_limpio"):
            continue
        ref = B.parear(por_vb.get((r["vol"], b), []), r["dt"])
        ex = extra.get((r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")), {})
        alertas = [f for f in ref if B.es_alerta(f["tipo"])]
        prot = any(alerta_protegida(f) for f in ref)
        tabla = any(f["source"] == "CONS" for f in alertas)
        vecinos = [abs((t - r["dt"]).total_seconds()) for t in por_vs[(r["vol"], r["sensor"])]]
        partida = any(0 < s <= PARTIDA_S for s in vecinos)
        out.append({
            "volcan": r["vol"], "hora_utc": r["dt"].strftime("%Y-%m-%d %H:%M"), "sensor": r["sensor"], "b": b,
            "lab": r["lab"], "protegida": prot, "alerta_tabla": tabla,
            "decide": (r["lab"] == "neg_limpio") or tabla or b == "MODIS" or r["noche"] >= FRONTERA_OCR,
            "mirova": [{k: f[k] for k in ("fecha_utc", "tipo", "vrp_mw", "dist_km", "source")} for f in ref],
            "mirova_vrp": max([f["vrp_mw"] or 0 for f in alertas], default=0.0),
            "z": r["z"], "estrato_z": estrato_cenit(r["z"]), "pub_prod": r["pub"], "dc": r["dc"],
            "pc_vrp": r["pc_vrp"], "partida": partida,
            **{k: ex.get(k) for k in ("granule", "pc_n", "vrp_mw", "n_px", "pc_dist", "f5_core", "sha")},
        })
    sin_rec = B.alertas_sin_record(por_vb, recs)
    for b in VENTANAS:
        o_b = [o for o in out if o["b"] == b]
        pos = [o for o in o_b if o["lab"] == "pos"]
        neg = [o for o in o_b if o["lab"] == "neg_limpio"]
        print(f"\n== {b} ventana {VENTANAS[b]}: pos {len(pos)} (protegidas {sum(o['protegida'] for o in pos)}, "
              f"deciden {sum(o['decide'] for o in pos)}), neg limpios {len(neg)}")
        print("  P1: pos con VRP de MIROVA > 0:", sum(o["mirova_vrp"] > 0 for o in pos), "de", len(pos))
        print("  alertas de MIROVA sin record nuestro (+-120 s, ventana total):",
              sum(v for k, v in sin_rec.items() if k[1] == b))
        print("  partidas: pos", sum(o["partida"] for o in pos), "neg", sum(o["partida"] for o in neg))
        print("  sin granule: pos", sum(1 for o in pos if not o["granule"]), "neg", sum(1 for o in neg if not o["granule"]))
        for nombre, lst in (("pos", pos), ("neg", neg)):
            c = collections.Counter((o["volcan"], o["estrato_z"]) for o in lst)
            print(f"  {nombre} por volcan y cenit:", dict(sorted(c.items())))
            print(f"  {nombre} publica produccion:", sum(bool(o["pub_prod"]) for o in lst), "de", len(lst))
        prot = [o for o in pos if o["protegida"]]
        print("  protegidas publicadas por produccion:", sum(bool(o["pub_prod"]) for o in prot), "de", len(prot))
        print("  sha de los records (pos+neg):", dict(collections.Counter(o["sha"] for o in o_b).most_common(4)))

    Path(AQUI / "poblacion_completa.json").write_text(json.dumps(
        {"meta": {"ventanas": VENTANAS, "referencia": {k: v["sha"] for k, v in info.items()},
                  "data_records": "origin/main 533398f8f", "tol_pareo_s": 120,
                  "regla_minimas": "SN", "lectura_protegida": "A"},
         "pasadas": out}, ensure_ascii=False, indent=0, default=str), encoding="utf-8")
    print("\nescrito poblacion_completa.json:", len(out))


if __name__ == "__main__":
    main()
