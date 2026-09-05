# -*- coding: utf-8 -*-
"""F2 - Donde pone MIROVA su cumulo, en la MISMA pasada. Evidencia exogena.

EL FENOMENO. S133 midio que nuestro cumulo VIIRS 375 m se sienta a 2,3-2,8 km del crater
en 9 de los 11 Tier A. La lectura natural es que MIROVA integra la celda del crater y
nosotros el flanco, y que por eso las magnitudes no comparan. Pero esa lectura supone algo
que nadie habia mirado: que MIROVA efectivamente pone SU cumulo en el crater. Este script
va a buscar esa respuesta a la imagen que MIROVA publico de la MISMA pasada.

QUE SE MIDE, por pasada (ALERTA MIROVA VIIRS375, TIF a <=120 s, record nuestro a <=120 s):
  - del TIF: celda de maxima radiancia dentro del inner_radius, y centroide ponderado de
    las celdas sobre el percentil 99 dentro del inner. Distancia al crater (vent_lat/lon).
  - del TIF: la misma distancia medida a las 3 anclas posibles, para ver cual reproduce la
    Distancia_km que MIROVA declara.
  - nuestro: centroide del primary_cluster y pixel de maximo vrp_mw, ambos al crater.
  - MIROVA CSV: dist_km (cuantizada a celda, D15).
El TIF se usa SOLO para POSICION, jamas para magnitud (A24).
Ancla SIEMPRE vent_lat/vent_lon, nunca lat/lon del catalogo (A13).
Read-only sobre el repo canonico; escribe solo en experiments/_s134_audit/."""
import datetime as dt, json, os, importlib.util
import numpy as np
import f2_lib as F
F.utf8()
_d = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("emp", os.path.join(_d, "02_emparejar.py"))
emp = importlib.util.module_from_spec(_s); _s.loader.exec_module(emp)

TOL_TS = 120
VOLS = ["Chaiten","Copahue","Isluga","Lascar","Lastarria","Llaima","NevadosDeChillan",
        "PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito","Villarrica"]
# Regimen segun S133 (docs/s133/ANILLO_TIER_A.md) + A69/A20
REGIMEN = {"Lascar":"focal","Isluga":"focal","Lastarria":"fumarolico",
           "PuyehueCordonCaulle":"difuso",
           "Villarrica":"nevado_debil","Llaima":"nevado_debil","Copahue":"nevado_debil",
           "Chaiten":"nevado_debil","NevadosDeChillan":"nevado_debil",
           "PlanchonPeteroa":"nevado_debil","Tupungatito":"nevado_debil"}

def pmax(a, lat, lon, mask):
    f = np.where(mask & np.isfinite(a), a, -np.inf)
    if not np.isfinite(f).any(): return None
    i, j = np.unravel_index(int(np.argmax(f)), f.shape)
    return float(lat[i, j]), float(lon[i, j])

def pcentroide(a, lat, lon, mask, q=99.0):
    v = a[mask & np.isfinite(a)]
    if v.size < 10: return None
    u = np.nanpercentile(v, q)
    sel = mask & np.isfinite(a) & (a >= u)
    w = a[sel].astype(float)
    if w.size == 0 or not np.isfinite(w).any(): return None
    w = w - np.nanmin(w) + 1e-9          # peso positivo; solo pondera POSICION
    return float(np.sum(lat[sel]*w)/np.sum(w)), float(np.sum(lon[sel]*w)/np.sum(w))

def main():
    cat = F.catalogo()
    filas, errores = [], []
    for v in VOLS:
        c = cat[v]
        vla, vlo = c["vent_lat"], c["vent_lon"]
        anclas = {"vent": (vla, vlo), "gvp": (c["lat"], c["lon"]),
                  "mirova_center": (c.get("mirova_center_lat"), c.get("mirova_center_lon"))}
        inner = float(c["inner_radius_km"])
        ps = [x for x in emp.pares(v) if x["tif"] and x["dt_tif"] <= TOL_TS and x["rec"]]
        for x in ps:
            a, t, r = x["alerta"], x["tif"], x["rec"]
            try:
                arr, lat, lon, crs = F.leer_tif(t["tif_path"])
            except Exception as e:
                errores.append(dict(vol=v, tif=t["tif_path"], err=repr(e))); continue
            dg = F.grilla_dist_km(lat, lon, vla, vlo)
            m = dg <= inner
            f = dict(volcan=v, regimen=REGIMEN[v],
                     pasada_utc=a["_ts"].strftime("%Y-%m-%d %H:%M:%S"),
                     sensor_nuestro=r.get("sensor"), fuente_mirova=a["source"],
                     tif=t["tif_path"].split("/")[-1], inner_km=inner,
                     semiancho_diag_km=round(float(np.nanmax(dg)), 2),
                     celdas_en_inner=int(m.sum()),
                     dist_km_mirova=a["dist_km"], vrp_mirova=a["vrp_mw"],
                     solar_zenith_deg=r.get("solar_zenith_deg"))
            pm = pmax(arr, lat, lon, m)
            pc = pcentroide(arr, lat, lon, m)
            f["d_max_tif_km"] = round(F.haversine(vla, vlo, *pm), 3) if pm else None
            f["d_centroide_tif_km"] = round(F.haversine(vla, vlo, *pc), 3) if pc else None
            if pm:
                for na, (la0, lo0) in anclas.items():
                    f["d_max_tif_a_%s" % na] = (round(F.haversine(la0, lo0, *pm), 3)
                                                if la0 is not None else None)
            # nuestro
            p = r.get("primary_cluster") or {}
            if p.get("centroid_lat") is not None:
                f["d_crater_nuestro_km"] = round(
                    F.haversine(vla, vlo, p["centroid_lat"], p["centroid_lon"]), 3)
                f["pc_n_pixels"] = p.get("n_pixels")
                f["pc_vrp_mw"] = p.get("vrp_mw")
            f["f5_core_vrp_mw"] = r.get("f5_core_vrp_mw")
            f["distance_class"] = r.get("distance_class")
            ap = r.get("anomaly_pixels") or []
            ap = [q for q in ap if q.get("vrp_mw") is not None and q.get("lat") is not None]
            if ap:
                b = max(ap, key=lambda q: q["vrp_mw"])
                f["d_pico_nuestro_km"] = round(F.haversine(vla, vlo, b["lat"], b["lon"]), 3)
                f["n_anomaly_pixels_persistidos"] = len(ap)
            f["n_anomalous_pixels"] = r.get("n_anomalous_pixels")
            filas.append(f)
        print("  %-22s pares=%d" % (v, len(ps)))
    json.dump(dict(generado=dt.datetime.now(dt.timezone.utc).isoformat(),
                   tol_emparejamiento_s=TOL_TS, ventana="ALERTAS MIROVA VIIRS375 >= 2026-06-01",
                   n=len(filas), errores=errores, filas=filas),
              open(os.path.join(_d, "resultados.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print("\nfilas=%d  errores=%d -> resultados.json" % (len(filas), len(errores)))

main()
