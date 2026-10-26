# S159 frente M: efecto de la geolocalizacion MODIS sobre lo publicado. Corre la funcion de produccion
# (process_modis.calculate_vrp + store.append_record) dos veces por record: brazo A con la geolocalizacion de
# produccion (_interp_geo sobre la grilla de 5 km del L1B) y brazo B con lat/lon por pixel de MxD03 (con
# correccion de terreno). Nada mas cambia entre brazos. Criterio sellado en PREREGISTRO_M.md antes de correr.
#
# Solo lectura: no escribe en data/ (store.DATA_DIR se redirige a un temporal), no commitea, borra cada HDF.
# Uso (Linux, con pyhdf): EARTHDATA_TOKEN=... VRP_PROFILE=mirova_equivalent \
#     python probe_m.py --objetivos objetivos.json --out out --parte 0 --de 4
# Sale con codigo 2 si falta algun granulo o falla algun record.
import argparse
import copy
import importlib.util
import json
import math
import os
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))

# Instrumento de S151 (no se reescribe: mismo nucleo `comparar` que ya paso su prueba sintetica y su verificador)
_spec = importlib.util.spec_from_file_location("probe151", RAIZ / "experiments/_s151_probe_mod03/probe_mod03.py")
P151 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P151)

CAMPOS_REC = ("vrp_mw", "n_anomalous_pixels", "distance_class", "final_hotspot_lat", "final_hotspot_lon",
              "final_hotspot_dist_km", "final_hotspot_source", "hotspot_lat", "hotspot_lon", "hotspot_dist_km",
              "t_bg_k", "t_max_k", "diag_L_bg_w_m2_sr_um", "diag_n_bg_anillo", "diag_sigma_bg_k",
              "diag_n_first_pass_pixels", "diag_n_first_pass_summit", "diag_n_second_pass_recapture",
              "diag_n_dnti_ctx_path", "diag_n_eti_path", "diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti",
              "diag_sd_deti", "diag_t_max_dist_km", "sensor_zenith_deg", "sensor_azimuth_deg", "geo_class")


def ne_km(lat0, lon0, lat, lon):
    return ((lat - lat0) * 111.32, (lon - lon0) * 111.32 * math.cos(math.radians((lat + lat0) / 2)))


def rumbo(dn, de):
    return round((math.degrees(math.atan2(de, dn)) + 360) % 360, 1)


def ubicar(lat_arr, lon_arr, lat, lon, ventana=None):
    """(i, j) del pixel cuya posicion en (lat_arr, lon_arr) es la mas cercana a (lat, lon), y esa distancia."""
    d = np.hypot((lat_arr - lat) * 111.32, (lon_arr - lon) * 111.32 * math.cos(math.radians(lat)))
    if ventana is not None:
        d = np.where(ventana, d, np.inf)
    k = np.unravel_index(np.nanargmin(d), d.shape)
    return int(k[0]), int(k[1]), float(d[k])


def desplazamiento_pixeles(pix, ilat, ilon, glat, glon, ventana):
    """Para cada pixel de la lista (posiciones del brazo A), su (i, j) en la grilla interpolada y cuanto lo mueve
    MxD03: (dn, de) = MxD03 menos _interp_geo, en km. Devuelve filas y el (i, j) de cada una."""
    out = []
    for p in pix:
        i, j, err = ubicar(ilat, ilon, p["lat"], p["lon"], ventana)
        dn, de = ne_km(float(ilat[i, j]), float(ilon[i, j]), float(glat[i, j]), float(glon[i, j]))
        out.append({"i": i, "j": j, "err_ubicar_km": round(err, 4), "dn_km": round(dn, 3), "de_km": round(de, 3),
                    "d_km": round(math.hypot(dn, de), 3), "rumbo": rumbo(dn, de), "bt_k": p.get("bt_k"),
                    "vrp_mw": p.get("vrp_mw")})
    return out


def ij_de(pix, glat, glon, ventana):
    return [list(ubicar(glat, glon, p["lat"], p["lon"], ventana)[:2]) for p in pix]


def resumen_rec(r):
    if r is None:
        return None
    pc = r.get("primary_cluster") or {}
    out = {k: r.get(k) for k in CAMPOS_REC}
    out["pc"] = {k: pc.get(k) for k in ("n_pixels", "vrp_mw", "centroid_lat", "centroid_lon", "centroid_dist_km",
                                        "geo_class", "single_pixel_mode", "d9_capped")} if pc else None
    out["anomaly_pixels"] = (r.get("anomaly_pixels") or [])[:80]
    out["n_anomaly_pixels_total"] = len(r.get("anomaly_pixels") or [])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objetivos", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--parte", type=int, default=0)
    ap.add_argument("--de", type=int, default=1)
    args = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el probe no usa usuario y clave (A71).")

    import yaml
    from pipeline import process_modis, store
    from pipeline import profile as vrp_profile
    from pipeline.fetch import auth
    from pipeline.geo_utils import get_detection_anchor

    vols = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
    vf_path = RAIZ / "pipeline" / "volcanic_features.yaml"
    VF = (yaml.safe_load(open(vf_path, encoding="utf-8")) or {}) if vf_path.exists() else {}

    objetivos = json.load(open(args.objetivos, encoding="utf-8"))
    granulos = sorted({o["granulo"] for o in objetivos})
    mios = [g for k, g in enumerate(granulos) if k % args.de == args.parte]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    auth()
    ORIG = process_modis.read_modis_l1b
    salida = open(out / f"probe_m_parte{args.parte}.jsonl", "w", encoding="utf-8")
    faltan = 0

    def _bajar_una(short, pat, dest):
        r = P151._bajar(short, pat, dest)
        if r is not None:
            return r, "6.1"
        import earthaccess
        from pipeline.fetch import download_granules
        res = earthaccess.search_data(short_name=short, version="6.1NRT", granule_name=f"{short}.{pat}*")
        if not res:
            return None, None
        p = download_granules(res[:1], dest)
        return (p[0] if p else None), "6.1NRT"

    def bajar(short, pat, dest):
        # Run 39679594869: un ReadTimeout de CMR (60 s) mato las 4 partes. Reintento con espera; si igual falla,
        # el granulo queda como error (el script sale 2), no se cae la corrida entera.
        import time
        for intento in range(4):
            try:
                return _bajar_una(short, pat, dest)
            except Exception as e:
                print(f"  CMR/descarga fallo intento {intento} {short}.{pat}: {e!r}"[:300], flush=True)
                time.sleep(20 * (intento + 1))
        return None, None

    for g in mios:
        short, pat = g.split(".")[0], ".".join(g.split(".")[1:3])
        geo_short = short.replace("021KM", "03")
        objs = [o for o in objetivos if o["granulo"] == g]
        l1b, ver_l1b = bajar(short, pat, out / "hdf")
        geo, ver_geo = bajar(geo_short, pat, out / "hdf")
        if l1b is None or geo is None:
            for o in objs:
                salida.write(json.dumps({"objetivo": o, "error": f"no bajado l1b={l1b} geo={geo}"}) + "\n")
                faltan += 1
            salida.flush()
            continue
        try:
            glat, glon, saz, szen = P151._leer_geo(geo)
            latc, lonc, _rad = P151._leer_l1b(l1b)
            n_fill = int(np.sum((glat < -90) | (glat > 90)))
            glat32, glon32 = glat.astype(np.float32), glon.astype(np.float32)
        except Exception as e:
            for o in objs:
                salida.write(json.dumps({"objetivo": o, "error": f"lectura: {e!r}"}) + "\n")
                faltan += 1
            continue

        for o in objs:
            fila = {"objetivo": o, "version_l1b": ver_l1b, "version_geo": ver_geo, "n_fill_mxd03": n_fill}
            try:
                v = vols[o["volcan"]]
                alat, alon = get_detection_anchor(v)
                vent = (alat, alon)
                # Geometria en el crater (instrumento S151, mismo nucleo) y su nulo (interp contra si misma)
                fila["geo_crater"] = P151.comparar(glat, glon, latc, lonc, saz, szen, process_modis._interp_geo,
                                                   None, vent=vent)
                ilat = process_modis._interp_geo(latc, glat.shape[0], glat.shape[1]).astype(np.float64)
                ilon = process_modis._interp_geo(lonc, glat.shape[0], glat.shape[1]).astype(np.float64)
                nulo = P151.comparar(ilat, ilon, latc, lonc, saz, szen, process_modis._interp_geo, None, vent=vent)
                fila["nulo_geo_crater_km"] = round(math.hypot(nulo["obs_barrido_km"], nulo["obs_traza_km"]), 6)
                ventana = np.hypot((glat - alat) * 111.32, (glon - alon) * 111.32 * math.cos(math.radians(alat))) < 60
                fila["n_lineas"], fila["n_frames"] = int(glat.shape[0]), int(glat.shape[1])

                resultados = {}
                for brazo in ("A", "A2", "B"):
                    def lector(path, _b=brazo):
                        d = ORIG(path)
                        if _b == "B":
                            if d["lat"].shape != glat32.shape:
                                raise RuntimeError(f"forma distinta {d['lat'].shape} {glat32.shape}")
                            d["lat"], d["lon"] = glat32.copy(), glon32.copy()
                        return d
                    process_modis.read_modis_l1b = lector
                    try:
                        res = process_modis.calculate_vrp(
                            Path(l1b), Path(geo), v["lat"], v["lon"], v["radius_km"],
                            vent_lat=alat, vent_lon=alon,
                            vent_radius_km=v.get("vent_radius_km", 4.0),
                            inner_radius_km=v.get("inner_radius_km"),
                            exclude_zones=v.get("exclude_zones"),
                            active_water_bodies=v.get("active_water_bodies"),
                            lbg_global_compatible=v.get("lbg_global_compatible", False),
                            local_kernel_bg_compatible=v.get("local_kernel_bg", False),
                        )
                    finally:
                        process_modis.read_modis_l1b = ORIG
                    crudo = copy.deepcopy(res)
                    publicado = None
                    if res:
                        with tempfile.TemporaryDirectory() as td:
                            store.DATA_DIR = Path(td)
                            store.append_record(v["name"], res, volcano_lat=v["lat"], volcano_lon=v["lon"],
                                                overwrite=True, max_hotspot_dist_km=v.get("radius_km"),
                                                enable_pixel_level_distance_filter=vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                                                max_cluster_pixels=v.get("max_cluster_pixels"),
                                                inner_radius_km=v.get("inner_radius_km"),
                                                volcanic_features=VF.get(v["name"]))
                            p = Path(td) / f"{v['name']}.json"
                            if p.exists():
                                recs = json.load(open(p))["records"]
                                publicado = recs[-1] if recs else None
                    resultados[brazo] = (crudo, publicado)
                    fila[f"rec_{brazo}"] = resumen_rec(publicado)
                    fila[f"crudo_{brazo}_none"] = crudo is None

                # Nulo de ejecucion: A contra A2 (mismo brazo dos veces) debe ser identico
                fila["nulo_A_A2_identico"] = (json.dumps(fila["rec_A"], sort_keys=True, default=str)
                                              == json.dumps(fila["rec_A2"], sort_keys=True, default=str))
                del fila["rec_A2"]
                # Desplazamiento puro de los pixeles de A (mismos (i, j), otra geolocalizacion)
                pa = (fila["rec_A"] or {}).get("anomaly_pixels") or []
                fila["desp_pixeles_A"] = desplazamiento_pixeles(pa, ilat, ilon, glat, glon, ventana) if pa else []
                pb = (fila["rec_B"] or {}).get("anomaly_pixels") or []
                fila["ij_A"] = [[d["i"], d["j"]] for d in fila["desp_pixeles_A"]]
                fila["ij_B"] = ij_de(pb, glat, glon, ventana) if pb else []
                # Pixel del crater segun cada geolocalizacion (el mas cercano al ancla)
                ia, ja, _ = ubicar(ilat, ilon, alat, alon, ventana)
                ib, jb, _ = ubicar(glat, glon, alat, alon, ventana)
                fila["pixel_crater_interp_ij"], fila["pixel_crater_mxd03_ij"] = [ia, ja], [ib, jb]
            except Exception as e:
                fila["error"] = repr(e)
                fila["traza"] = traceback.format_exc()[-1500:]
                faltan += 1
            salida.write(json.dumps(fila, ensure_ascii=False, default=str) + "\n")
            salida.flush()
            a = fila.get("rec_A") or {}
            b = fila.get("rec_B") or {}
            print(o["volcan"], g, o["estrato"], "A:", a.get("distance_class"), (a.get("pc") or {}).get("vrp_mw"),
                  "B:", b.get("distance_class"), (b.get("pc") or {}).get("vrp_mw"),
                  "geo:", (fila.get("geo_crater") or {}).get("obs_hacia_sensor_km"), fila.get("error", ""), flush=True)
        for p in (l1b, geo):
            Path(p).unlink(missing_ok=True)
    salida.close()
    print("FALTAN:", faltan)
    sys.exit(2 if faltan else 0)


if __name__ == "__main__":
    main()
