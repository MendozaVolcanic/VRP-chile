# -*- coding: utf-8 -*-
"""S158: alertas de MIROVA en VIIRS 750 que el detector K no publica, una por una y por mecanismo.

POR QUE. El auto-audit (#864) marco el recall de VIIRS 750 en 73,3 % y el banco de paridad con K da 0,77 por pasada
contra 0,93 en VIIRS 375. Antes de buscar una palanca hay que saber en QUE etapa se pierde cada alerta: si el detector
no vio nada, si vio algo pero lejos del crater, o si vio el crater y el tablero lo oculto. Y el probe de #880 dejo una
sospecha sin verificar: pixeles con M15 en sentinela y M13 sano, que el lector deja en NaN, y sin M15 el pixel no tiene
NTI y no puede alertar.

QUE HACE (sin red, referencia del snapshot del repo, la misma del banco de paridad):
  1. Etiqueta igual que `scripts/banco_paridad.py` (mismas funciones, importadas): pasada positiva = record nuestro
     con fila ALERTA nocturna de MIROVA (consolidado u OCR) a +-2 min. Lectura A: ALERTA_SIN_GEOMETRIA_OCR no es
     alerta (estrato aparte). Regla SN (D-9) aplicada de forma explicita; en VIIRS 750 no cambia nada porque la regla
     solo toca VIIRS 375, y el script lo comprueba.
  2. "Publica" = predicado del tablero EJECUTADO con node desde frontend/index.html (A97), cada condicion por
     separado: isSummitDetection, isValidDetection, isThermalArtifact, mirovaEqVrpDisplay > 0.
  3. Clasifica cada positiva no publicada por la PRIMERA condicion que falla, en el orden en que el tablero las pide,
     y la subclasifica con los campos del record (pixeles alertados, distancia del cumulo, t_max, NTI maximo).
  4. Lista aparte las alertas sin record nuestro a +-2 min (cobertura, no deteccion).
  5. Escribe `perdidas_v750.json` (insumo del probe L1B) y un resumen por stdout.

Uso:  python experiments/_s158_v750/listar_perdidas.py [--inicio 2026-03-01] [--fin 2026-10-21]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

import banco_paridad as bp  # noqa: E402
from clase_mirova import UMBRAL_PROTEGIDA_MW, aplicar_regla_minimas  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402

B = "VIIRS750"
EXTRA = ("granule", "n_anomalous_pixels", "t_max_k", "t_bg_k", "nti_max", "diag_nti_max", "diag_nti_bg",
         "diag_nti_std", "diag_n_first_pass_pixels", "diag_n_second_pass_recapture", "diag_n_dnti_ctx_path",
         "diag_t_max_dist_km", "diag_sigma_bg_k", "final_hotspot_dist_km", "final_hotspot_source",
         "sensor_zenith_deg", "product_version", "discarded_reason", "vrp_mw")


def cargar_v750(coords, inner, ventana):
    """Como banco_paridad.cargar_nuestros, solo VIIRS 750, guardando las cinco salidas del predicado."""
    recs, casos = [], []
    for vol in bp.VOLS:
        with open(bp.DATA / f"{vol}.json", encoding="utf-8") as fh:
            d = json.load(fh)
        for r in d["records"]:
            if bp.bucket(r.get("sensor")) != B or not (ventana[0] <= r.get("datetime_utc", "")[:10] <= ventana[1]):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada(B, lat, lon, dt):
                continue
            pc = r.get("primary_cluster") or {}
            rec = {"vol": vol, "b": B, "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "sensor": r.get("sensor"),
                   "dc": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km"),
                   "pc_npx": pc.get("n_pixels"), "z": r.get("sensor_zenith_deg"),
                   "sha": (r.get("regimen") or {}).get("codigo_sha"), "inner": inner[vol]}
            rec.update({k: r.get(k) for k in EXTRA})
            px = r.get("anomaly_pixels") or []
            rec["px_bt_max"] = max((q.get("bt_k") for q in px if q.get("bt_k") is not None), default=None)
            rec["px_vrp_max"] = max((q.get("vrp_mw") for q in px if q.get("vrp_mw") is not None), default=None)
            # BT del pixel alertado mas cercano al crater (el del cumulo summit; un pixel lejano puede tener energia).
            cerca = min((q for q in px if q.get("dist_km") is not None), key=lambda q: q["dist_km"], default=None)
            rec["px_bt_crater"] = cerca.get("bt_k") if cerca else None
            recs.append(rec)
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos) if casos else []
    for rec, p in zip(recs, pred):
        rec["summit"], rec["valid"], rec["art"], rec["disp"], rec["pub"] = p
    return recs


def mecanismo(r):
    """Primera condicion del predicado del tablero que falla, mas una subclase fisica desde el record."""
    npx = r.get("n_anomalous_pixels") or 0
    if npx == 0 and not r.get("pc_vrp"):
        return "M1_detector_no_alerta_ningun_pixel"
    if not r["summit"]:
        return "M2_alerta_solo_lejos_del_crater"
    if not r["valid"]:
        return "M3_summit_sin_cumulo_valido"
    if r["art"]:
        return "M4_artefacto_del_tablero"
    if not r["disp"]:
        return "M5_cumulo_fuera_del_inner"
    return "publica"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inicio", default=bp.INICIO_DEFECTO)
    ap.add_argument("--fin", default="2026-10-21")
    ap.add_argument("--out", default=str(HERE / "perdidas_v750.json"))
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    identidad = bp.control_identidad_predicado()
    assert identidad == ([0, 1, 1, 1, 0], [1, 0]), identidad   # P2 del banco: el predicado es el del tablero

    filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
    sn = aplicar_regla_minimas(filas, "SN")
    toca_v750 = sum(1 for k in sn.minimas if k[1] == B)
    assert toca_v750 == 0, "la regla SN toco pasadas de VIIRS 750: %d" % toca_v750
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, ventana, regla_minimas="SN")
    recs = cargar_v750(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    sin_record = bp.alertas_sin_record(por_vb, recs)

    pos = [r for r in recs if r["lab"] == "pos"]
    perd = [r for r in pos if not r["pub"]]
    # Coherencia con el banco: mismo recall por pasada que banco_paridad.metricas sobre el mismo denominador.
    p_banco, n_banco = bp.metricas(recs, sin_record, bp._filtro(b=B))
    salida = []
    for r in sorted(perd, key=lambda x: (x["vol"], x["dt"])):
        refs = [f for f in bp.parear(por_vb.get((r["vol"], B), []), r["dt"]) if bp.es_alerta(f["tipo"])]
        vrp_m = max((f["vrp_mw"] or 0) for f in refs) if refs else None
        dist_m = [f["dist_km"] for f in refs if f["dist_km"] is not None]
        e = {k: (v.strftime("%Y-%m-%d %H:%M") if k == "dt" else v) for k, v in r.items()}
        e.update({"mecanismo": mecanismo(r), "mirova_vrp_mw": vrp_m,
                  "mirova_dist_km": min(dist_m) if dist_m else None,
                  "mirova_fuentes": sorted({f["source"] for f in refs}),
                  "protegida": bool(vrp_m is not None and vrp_m >= UMBRAL_PROTEGIDA_MW)})
        salida.append(e)
    # Alertas sin record (cobertura): una por pasada de MIROVA.
    nuestros = collections.defaultdict(list)
    for r in recs:
        nuestros[r["vol"]].append(r["dt"])
    cobertura = []
    vistos = set()
    for (vol, b), lista in sorted(por_vb.items()):
        if b != B:
            continue
        for dt, f in lista:
            k = (vol, f["fecha_utc"][:16])
            if not bp.es_alerta(f["tipo"]) or k in vistos:
                continue
            vistos.add(k)
            if not any(abs((t - dt).total_seconds()) <= bp.TOL_S for t in nuestros.get(vol, [])):
                cobertura.append({"vol": vol, "fecha_utc": f["fecha_utc"], "mirova_vrp_mw": f["vrp_mw"],
                                  "mirova_dist_km": f["dist_km"], "fuente": f["source"],
                                  "protegida": bool((f["vrp_mw"] or 0) >= UMBRAL_PROTEGIDA_MW)})

    # Control del mismo instrumento sobre las positivas que SI publicamos (A110: el subclasificador no es ciego).
    publicadas = [r for r in pos if r["pub"]]
    mec_pub = collections.Counter(mecanismo(r) for r in publicadas)

    out = {"meta": {"ventana": list(ventana), "sha_index_html": bp.sha_git(bp.HTML),
                    "sha_cons": bp.sha_git(SNAP_CONS), "sha_ocr": bp.sha_git(SNAP_OCR),
                    "regla_minimas": "SN (sin efecto en VIIRS 750, comprobado)", "lectura": "A",
                    "n_records_v750_nocturnos": len(recs),
                    "n_records_sin_marca_k": sum(1 for r in recs if not r["sha"]),
                    "n_pos": len(pos), "n_pos_publicadas": len(publicadas), "n_pos_perdidas": len(perd),
                    "recall_pasada": round(len(publicadas) / len(pos), 4) if pos else None,
                    "banco_recall_pasada": p_banco["recall_pos"], "banco_n_pos": p_banco["n_pos"],
                    "n_alertas_sin_record": len(cobertura)},
           "perdidas": salida, "sin_record": cobertura,
           "publicadas": [{k: (v.strftime("%Y-%m-%d %H:%M") if k == "dt" else v) for k, v in r.items()}
                          for r in sorted(publicadas, key=lambda x: (x["vol"], x["dt"]))],
           "control_publicadas_mecanismo": dict(mec_pub)}
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")

    m = out["meta"]
    print(f"ventana {ventana[0]} a {ventana[1]} | records V750 nocturnos {m['n_records_v750_nocturnos']} "
          f"(sin marca K: {m['n_records_sin_marca_k']})")
    print(f"positivas {m['n_pos']} | publicadas {m['n_pos_publicadas']} | perdidas {m['n_pos_perdidas']} | "
          f"recall {m['recall_pasada']} (banco: {m['banco_recall_pasada']}, n {m['banco_n_pos']})")
    print(f"alertas sin record a +-2 min (cobertura): {len(cobertura)} "
          f"(protegidas {sum(c['protegida'] for c in cobertura)})")
    print("control: mecanismo de las positivas publicadas:", dict(mec_pub))
    c = collections.Counter(e["mecanismo"] for e in salida)
    cp = collections.Counter(e["mecanismo"] for e in salida if e["protegida"])
    print("perdidas por mecanismo (todas | protegidas >= 1 MW):")
    for k in sorted(c):
        print(f"  {k:40s} {c[k]:3d} | {cp[k]:3d}")
    print("perdidas por volcan:", dict(collections.Counter(e["vol"] for e in salida)))
    print("perdidas por satelite:", dict(collections.Counter(e["sensor"] for e in salida)))
    print("positivas por satelite (todas):", dict(collections.Counter(r["sensor"] for r in pos)))
    print("perdidas por mes:", dict(sorted(collections.Counter(e["dt"][:7] for e in salida).items())))
    print("\ndetalle (vol, hora, sat, cenit, mecanismo, MIROVA MW y km, nuestro pc MW y km, n px, t_max, nti_max):")
    for e in salida:
        print(f"  {e['vol']:20s} {e['dt']} {e['sensor']:17s} z={e['z']!s:6s} {e['mecanismo']:38s} "
              f"M={e['mirova_vrp_mw']!s:5s}@{e['mirova_dist_km']!s:5s} pc={e['pc_vrp']!s:8.8s}@{e['pc_dist']!s:6.6s} "
              f"npx={e['n_anomalous_pixels']!s:3s} tmax={e['t_max_k']!s:7s} nti={e['nti_max']!s:9.9s} {e['dc']}")
    print("\nsin record:")
    for c_ in cobertura:
        print(f"  {c_['vol']:20s} {c_['fecha_utc']} M={c_['mirova_vrp_mw']}@{c_['mirova_dist_km']} {c_['fuente']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
