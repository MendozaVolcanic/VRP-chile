# Tarea 1.17 del loop: poblacion y muestra del probe que re-etiqueta MODIS con MxD03.
# Solo lectura de data/mirova_equivalent/. Escribe poblacion.json en esta carpeta, que es lo que el
# workflow lee (asi el runner no necesita los JSON del corpus y la muestra queda fijada en git antes
# de correr). Criterio y justificacion de los topes: README.md.
#
# POR QUE ESTA POBLACION. La etiqueta summit/far de MODIS sale del `final_hotspot` (flag
# ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER apagado) y la publicacion en el tablero exige ademas que
# el centroide del `primary_cluster` caiga dentro del inner (`mirovaEqVrp`, frontend/index.html).
# Un corrimiento de 1 a 3 km solo puede cambiar alguna de las dos cosas si la posicion que la decide
# esta a 3 km o menos del limite. Por eso:
#   A       = el hotspot final esta a 3 km o menos del limite (puede cambiar la etiqueta);
#   B       = solo el cumulo esta a 3 km o menos (puede cambiar la publicacion, no la etiqueta);
#   control = todas las distancias a mas de 6 km del limite (no deberia cambiar nada por reubicacion).
# La banda de 3 a 6 km queda fuera de la muestra y se cuenta como "medio".
#
# Uso: python seleccionar_mxd03.py   (local; necesita node para el predicado del tablero)
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]

BANDA_KM = 3.0
MARGEN_CONTROL_KM = 6.0
VENTANA = ("2026-03-01", "2026-10-12")   # A119: MODIS completo desde marzo; Standard L1B ya publicado
TOPES = {"A": 30, "B": 8, "control": 6}
SAL = "s151-tarea-1.17"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]


def distancias(rec):
    """(distancia del hotspot final, distancia del centroide del cumulo); None donde no hay."""
    pc = rec.get("primary_cluster") or {}
    return rec.get("final_hotspot_dist_km"), pc.get("centroid_dist_km")


def estrato(rec, inner, banda=BANDA_KM, margen=MARGEN_CONTROL_KM):
    final, pc = distancias(rec)
    ds = [d for d in (final, pc) if d is not None]
    if not ds:
        return None
    if final is not None and abs(final - inner) <= banda:
        return "A"
    if pc is not None and abs(pc - inner) <= banda:
        return "B"
    if all(abs(d - inner) > margen for d in ds):
        return "control"
    return None


def clave_granulo(rec):
    """'MYD021KM.A2026073.0705': producto y hora del granulo, sin version ni fecha de proceso."""
    g = rec.get("granule")
    if g:
        partes = g.split(".")
        if len(partes) >= 3 and partes[0] in ("MOD021KM", "MYD021KM"):
            return ".".join(partes[:3])
    sensor = rec.get("sensor") or ""
    prod = {"MODIS_TERRA": "MOD021KM", "MODIS_AQUA": "MYD021KM"}.get(sensor)
    try:
        dt = datetime.strptime(rec.get("datetime_utc", ""), "%Y-%m-%d %H:%M")
    except ValueError:
        return None
    if prod is None:
        return None
    return "%s.A%s.%s" % (prod, dt.strftime("%Y%j"), dt.strftime("%H%M"))


def muestrear(items, n, sal=SAL, clave=lambda x: x):
    """Los n primeros segun sha1(sal + clave): uniforme, determinista y sin depender del orden."""
    orden = sorted(items, key=lambda x: hashlib.sha1((sal + clave(x)).encode()).hexdigest())
    return orden[:n]


def construir_poblacion(records_por_volcan, inner, ventana=VENTANA, topes=TOPES):
    out = {}
    for vol, recs in records_por_volcan.items():
        vistos = {}
        for r in recs:
            if not (r.get("sensor") or "").startswith("MODIS"):
                continue
            if not (ventana[0] <= (r.get("datetime_utc") or "")[:10] <= ventana[1]):
                continue
            k = clave_granulo(r)
            if k is not None:
                vistos.setdefault(k, r)
        N = {"A": 0, "B": 0, "control": 0, "medio": 0, "sin_distancia": 0, "total": len(vistos)}
        por_estrato = {"A": [], "B": [], "control": []}
        for k, r in vistos.items():
            e = estrato(r, inner[vol])
            if e is None:
                N["sin_distancia" if not [d for d in distancias(r) if d is not None] else "medio"] += 1
                continue
            N[e] += 1
            por_estrato[e].append(k)
        muestra = []
        for e in ("A", "B", "control"):
            for k in muestrear(por_estrato[e], topes[e]):
                r = vistos[k]
                final, pc = distancias(r)
                muestra.append({"clave": k, "estrato": e, "datetime_utc": r.get("datetime_utc"),
                                "sensor": r.get("sensor"), "sensor_zenith_deg": r.get("sensor_zenith_deg"),
                                "dc_guardada": r.get("distance_class"), "final_dist_guardada": final,
                                "pc_dist_guardada": pc})
        out[vol] = {"inner_radius_km": inner[vol], "N": N, "muestra": muestra, "_records": vistos}
    return out


def main():
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    sys.path.insert(0, str(RAIZ / "scripts"))
    sys.path.insert(0, str(RAIZ))
    import banco_paridad as bp   # predicado del tablero ejecutado con node (A97), no reconstruido
    inner = bp.inner_desde_html()
    recs = {}
    for vol in VOLS:
        with open(RAIZ / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8") as fh:
            recs[vol] = json.load(fh)["records"]
    pob = construir_poblacion(recs, inner)
    for vol, v in pob.items():
        todos = list(v.pop("_records").items())
        casos = []
        for _, r in todos:
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
        pub = {k: p[4] for (k, _), p in zip(todos, bp.correr_node(casos))}
        v["n_pub_tramo"] = int(sum(pub.values()))
        for g in v["muestra"]:
            g["pub_guardada"] = pub[g["clave"]]
        print(vol, v["N"], "publicadas", v["n_pub_tramo"], "muestra", len(v["muestra"]))
    meta = {"ventana": VENTANA, "banda_km": BANDA_KM, "margen_control_km": MARGEN_CONTROL_KM,
            "topes": TOPES, "sal": SAL, "fuente": "data/mirova_equivalent/*.json (origin/main)"}
    with open(AQUI / "poblacion.json", "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "volcanes": pob}, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
