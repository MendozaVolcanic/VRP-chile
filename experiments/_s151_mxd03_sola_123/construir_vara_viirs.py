# Tarea 1.23, punto 2: la vara de posicion independiente, congelada ANTES de correr el probe.
# Solo lectura de data/mirova_equivalent/*.json y de la referencia de MIROVA (los mismos commits de
# Mirova-v1 que fija poblacion.json de la 1.17). Escribe vara_viirs.json en esta carpeta.
#
# POR QUE ESTA VARA. La pregunta es fisica: en una noche en que el volcan tiene un objeto caliente, donde
# esta ese objeto segun OTRO instrumento, y cual de las dos geolocalizaciones MODIS (`_interp_geo` o
# MxD03) lo pone mas cerca. VIIRS 375 m es otro sensor, en otro satelite, con su propia geolocalizacion
# por pixel (VNP03IMG / VJ103IMG, pipeline/fetch.py:198), y pasa la misma noche que Terra y Aqua. Su
# pixel es 7 veces mas chico en area que el de MODIS. No es nuestra etiqueta ni nuestro predicado sobre
# MODIS, asi que no hereda la asimetria A46 que tumbo las dos protegidas de Lascar.
#
# Que pasada VIIRS entra:
#   - VIIRS 375 (VIIRS_SNPP, VIIRS_NOAA20, VIIRS_NOAA21, sin sufijo _750; convencion A48);
#   - a 6 h o menos del granulo MODIS (la misma noche: Terra pasa ~01:30 UTC, Aqua ~06:30 a 08:00, VIIRS
#     ~05:00 a 08:00);
#   - nocturna por la misma regla con que se indexa la referencia (es_pasada_diurna_descartada);
#   - publicada por el tablero (predicado de frontend/index.html con node, A97), o sea con cumulo valido
#     dentro del inner;
#   - nivel ESTRICTO: ademas MIROVA alerto ESA pasada VIIRS (lab "pos" de banco_paridad, regla SN):
#     el arbitro externo dice que en esa pasada hay un objeto. Nivel AMPLIO: sin esa condicion.
#   - su cumulo NO viene del Test 1 (final_hotspot_source distinto de test1 y test1_roi). Con fuente
#     Test 1 el cumulo VIIRS es la componente conexa de los pixeles con exceso positivo del disco de 3 km
#     (pipeline/process_viirs.py:1972 a 2041), y con el exceso recortado a cero el ruido aporta en todo el
#     disco (S146, D30): su centroide tiende al CENTRO del disco, que es el ancla. Esa posicion la pone
#     el ancla, no el objeto, y la vara premiaria a la geolocalizacion que deje el cumulo MODIS mas cerca
#     del ancla. Se excluye.
# La posicion de cada pasada es el centroide del cumulo primario (primary_cluster.centroid_lat/lon),
# hecho con la posicion de sus pixeles. NO se usa final_hotspot_*: en VIIRS la fuente `test1_roi` lo
# pega al ancla del crater (final_hotspot_dist_km = 0,0 en Lascar, record VIIRS_NOAA20 del 2026-10-17
# 06:18), y eso no es una medida.
# La posicion de la noche es la mediana por componente (norte y este) de las pasadas que entran (A70).
#
# Uso: python construir_vara_viirs.py   (local; necesita node y red para bajar la referencia fijada)
import json
import math
import os
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
DIR_117 = AQUI.parent / "_s151_mxd03_etiquetas"
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

VENTANA_H = 6.0
VIIRS375 = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")


def enu_km(lat0, lon0, lat, lon):
    """(norte, este) en km de (lat, lon) respecto de (lat0, lon0), plano local."""
    return (lat - lat0) * 111.32, (lon - lon0) * 111.32 * math.cos(math.radians(lat0))


def mediana(xs):
    s = sorted(xs)
    n = len(s)
    return None if not n else (s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2]))


def resumir_noche(pasadas, vent):
    """Mediana por componente de las pasadas y su dispersion (mediana de la distancia de cada pasada a la
    mediana de la noche). `pasadas`: lista de dicts con lat, lon."""
    if not pasadas:
        return None
    ne = [enu_km(vent[0], vent[1], p["lat"], p["lon"]) for p in pasadas]
    n, e = mediana([x[0] for x in ne]), mediana([x[1] for x in ne])
    disp = mediana([math.hypot(x[0] - n, x[1] - e) for x in ne])
    return {"n_km": round(n, 3), "e_km": round(e, 3), "n_pasadas": len(pasadas), "dispersion_km": round(disp, 3)}


def bajar_referencia(meta, dest):
    from referencia_mirova_unificada import URL_RAW
    rutas = {}
    for nombre, clave in (("registro_vrp_consolidado.csv", "commit_cons"), ("registro_vrp_ocr.csv", "commit_ocr")):
        p = dest / nombre
        urllib.request.urlretrieve(URL_RAW.format(sha=meta["referencia"][clave], nombre=nombre), p)
        rutas[nombre] = p
    return rutas


def main():
    import banco_paridad as bp
    from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada
    from pipeline.geo_utils import get_detection_anchor
    import run_pipeline as rp
    from referencia_mirova_unificada import cargar_referencia_unificada

    pob = json.loads((DIR_117 / "poblacion.json").read_text(encoding="utf-8"))
    ventana = pob["meta"]["ventana"]
    rutas = bajar_referencia(pob["meta"], Path(tempfile.mkdtemp()))
    filas_ref = cargar_referencia_unificada(rutas["registro_vrp_consolidado.csv"], rutas["registro_vrp_ocr.csv"])
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    por_vb, ns, nv, _ = bp.indexar_referencia(filas_ref, coords, ventana, regla_minimas="SN")
    commit = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    salida = {"meta": {"commit_data": commit, "referencia": pob["meta"]["referencia"], "ventana_h": VENTANA_H,
                       "sensores": list(VIIRS375), "regla_minimas": "SN", "excluye_fuente": "test1*",
                       "posicion": "primary_cluster.centroid_lat/lon; noche = mediana por componente"},
              "granulos": {}, "resumen": {}}
    for vol, v in pob["volcanes"].items():
        volcan = rp.load_volcanoes(vol)[0]
        vent = get_detection_anchor(volcan)
        recs = json.loads((RAIZ / "data" / "mirova_equivalent" / f"{vol}.json").read_text(encoding="utf-8"))["records"]
        lo = (datetime.fromisoformat(ventana[0]) - timedelta(days=1)).strftime("%Y-%m-%d")
        hi = (datetime.fromisoformat(ventana[1]) + timedelta(days=1)).strftime("%Y-%m-%d")
        viirs = [r for r in recs if r.get("sensor") in VIIRS375 and lo <= (r.get("datetime_utc") or "")[:10] <= hi
                 and (r.get("primary_cluster") or {}).get("centroid_lat") is not None]
        for r in viirs:
            r["_dt"] = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        viirs = [r for r in viirs if not es_pasada_diurna_descartada("VIIRS375", coords[vol][0], coords[vol][1], r["_dt"])]
        casos = []
        for r in viirs:
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
        for r, p in zip(viirs, bp.correr_node(casos) if casos else []):
            r["_pub"] = int(p[4])
        t = [{"vol": vol, "b": "VIIRS375", "dt": r["_dt"], "noche": r["_dt"].strftime("%Y-%m-%d")} for r in viirs]
        bp.etiquetar(t, por_vb, ns, nv)
        for r, e in zip(viirs, t):
            r["_lab"] = e["lab"]
        res = {"granulos": len(v["muestra"]), "con_vara_estricta": 0, "con_vara_amplia": 0,
               "MODIS_pos_con_vara_estricta": 0, "MODIS_prot_con_vara_estricta": 0}
        for g in v["muestra"]:
            tg = datetime.strptime(g["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            cerca = [r for r in viirs if abs((r["_dt"] - tg).total_seconds()) <= VENTANA_H * 3600 and r["_pub"] == 1
                     and not str(r.get("final_hotspot_source") or "").startswith("test1")]
            fila = {}
            for nivel, sel in (("amplia", cerca), ("estricta", [r for r in cerca if r["_lab"] == "pos"])):
                pas = [{"lat": r["primary_cluster"]["centroid_lat"], "lon": r["primary_cluster"]["centroid_lon"],
                        "datetime_utc": r["datetime_utc"], "sensor": r["sensor"], "lab": r["_lab"],
                        "pc_vrp": r["primary_cluster"].get("vrp_mw"), "pc_n_pixels": r["primary_cluster"].get("n_pixels"),
                        "cenit": r.get("sensor_zenith_deg"),
                        "fuente": r.get("final_hotspot_source")} for r in sel]
                fila[nivel] = {"noche": resumir_noche(pas, vent), "pasadas": pas}
                if pas:
                    res["con_vara_" + nivel] += 1
            if fila["estricta"]["pasadas"]:
                res["MODIS_pos_con_vara_estricta"] += g["lab"] == "pos"
                res["MODIS_prot_con_vara_estricta"] += bool(g["prot"])
            fila.update({"vent": list(vent), "lab_modis": g["lab"], "prot": g["prot"]})
            salida["granulos"]["%s|%s" % (vol, g["clave"])] = fila
        disp = [f["estricta"]["noche"]["dispersion_km"] for k, f in salida["granulos"].items()
                if k.startswith(vol + "|") and f["estricta"]["noche"] and f["estricta"]["noche"]["n_pasadas"] >= 2]
        res["dispersion_estricta_mediana_km"] = mediana(disp)
        dist = [math.hypot(f["estricta"]["noche"]["n_km"], f["estricta"]["noche"]["e_km"])
                for k, f in salida["granulos"].items() if k.startswith(vol + "|") and f["estricta"]["noche"]]
        res["vara_estricta_al_ancla_mediana_km"] = None if not dist else round(mediana(dist), 3)
        salida["resumen"][vol] = res
        print(vol, res, flush=True)
    tot = {k: sum(r[k] for r in salida["resumen"].values() if isinstance(r[k], int))
           for k in ("granulos", "con_vara_estricta", "con_vara_amplia", "MODIS_pos_con_vara_estricta",
                     "MODIS_prot_con_vara_estricta")}
    salida["resumen"]["total"] = tot
    print("total", tot)
    (AQUI / "vara_viirs.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
