# -*- coding: utf-8 -*-
"""S157: probe de sólo lectura de SATURACIÓN del sensor en Nevados de Chillán. ESCRITO ANTES DE CORRER.

POR QUÉ. Con el sensor oblicuo nuestra magnitud de Chillán en erupción queda muy bajo la de MIROVA (VIIRS 750, 06:48
del 2026-10-18: 2,84 contra 22,85 MW). El probe de #871 mostró que ni el fondo (D25) ni la selección de vecinos
cierran ese déficit, y dejó dos candidatos: D17 (área, remuestreo) o SATURACIÓN. La saturación pesa por cómo la trata
el pipeline: un píxel saturado no entra con un valor tope, se BORRA (NaN) en `read_viirs_l1b` y `read_viirs_mod_l1b`
(bit de Saturation de los quality flags, techo de la LUT, techo de Campus 2022 en las bandas M) y en MODIS
(`calibrate` descarta todo SI > 32767, que incluye 65533 «Detector is saturated»). Y basta que sature la banda TÉRMICA
(I05, M15, B31) para que el NTI quede en NaN y el píxel nunca se alerte, aunque su MIR esté sano. Si eso pasa en el
píxel más caliente del cráter, la energía que falta es justo la del foco. Este probe cuenta cuántos píxeles del
entorno del cráter se pierden así en cada pasada y acota cuánta energía falta por eso.

QUÉ HACE, por pasada de `pasadas.json` (de `seleccionar_pasadas.py`):
  1. Baja el gránulo y corre el control de #871 (K tal cual, `probe_chillan.correr(..., "control")`) para tener el
     cúmulo publicado, el anillo (t_bg) y el área; C-P1 de #871 compara con el record persistido.
  2. Lee el L1B CRUDO con h5py / pyhdf (DN, quality flags, LUT) y, aparte, la BT tal como la deja el lector del
     pipeline. Píxel PERDIDO = la BT cruda es finita y la del pipeline es NaN, en la banda MIR o en la TIR.
  3. Ventana: píxeles a <= inner_radius_km (5 km) del ancla de detección, más los 8 vecinos del cúmulo publicado;
     y, para contexto, a <= 2 * inner.
  4. Cuenta por banda: bit 4 (Saturation), bit 2 (Out_of_Range), bit 128 (Some_Saturation, sólo bandas de doble
     ganancia), BT cruda en el tope de la LUT (>= máximo - 0,5 K), y en MODIS los códigos SI > 32767 (65533 aparte).
  5. Cota de energía faltante: por píxel perdido, k·A·max(L_MIR_crudo - L_anillo, 0). Es una cota INFERIOR: si la
     MIR saturó, su radiancia cruda es el tope del rango y la verdadera es mayor; si sólo saturó la TIR, la MIR es
     buena y el número es lo que ese píxel sumaría. Los píxeles del cúmulo con la MIR en el tope (entran recortados)
     se cuentan aparte: su energía faltante no se puede acotar por arriba.
  Los atributos `flag_masks` y `flag_meanings` del SDS de quality flags se guardan tal cual vienen en el archivo,
  para verificar el bit contra el producto y no sólo contra el UserGuide.

CONTROLES (fijados antes de correr):
  C-0   pasadas del grupo C (casi a nadir, noche fría, sin alerta): 0 píxeles perdidos y 0 con bit 4 en la ventana.
  C-POS el gránulo MODIS de Planchón Peteroa del 2026-03-18 08:05 (F28: 113 píxeles con SI = 65533) tiene que dar
        > 0 códigos 65533 a <= 25 km del volcán. Si da 0, el contador está ciego.
  C-SIN `prueba_saturacion.py`: el contador sobre arreglos sintéticos con bits y topes puestos a mano.
  C-P1  de #871 (el control reproduce el record persistido). Si falla, la pasada se informa y no se interpreta.

Uso (Actions, sólo EARTHDATA_TOKEN, A71):
  python probe_saturacion.py --job V375 --out out
  python probe_saturacion.py --job V750_MODIS --out out
Sale 2 si alguna pasada falla (S141).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROBE871 = ROOT / "experiments" / "_s157_prereg_d25" / "probe_l1b"
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, str(PROBE871))
import probe_chillan as p871  # noqa: E402  (instala sys.path, el perfil y store._save no-op)
import numpy as np  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from pipeline.scan_geometry import haversine_km  # noqa: E402

FLAG_DNS_VIIRS = (65532, 65533, 65534, 65535)
BIT_OOR, BIT_SAT, BIT_SOMESAT = 2, 4, 128
POSITIVO = {"grupo": "POS", "volcan": "PlanchonPeteroa", "sensor": "MODIS_AQUA",
            "granulo": "MYD021KM.A2026077.0805.061.2026078200542.hdf"}


def es_job(sensor, job):
    if job == "V375":
        return sensor.startswith("VIIRS") and not sensor.endswith("_750")
    return sensor.endswith("_750") or sensor.startswith("MODIS")


def planck(bt, lam):
    """Radiancia espectral W m-2 sr-1 um-1 (constantes de process_viirs.bt_to_spectral_radiance)."""
    from pipeline.process_viirs import bt_to_spectral_radiance
    return np.asarray(bt_to_spectral_radiance(np.asarray(bt, dtype=np.float64), lam), dtype=np.float64)


# ---------------------------------------------------------------------------------------------------------------
# Lectura cruda
# ---------------------------------------------------------------------------------------------------------------
def crudo_viirs(l1b, bandas):
    import h5py
    out = {}
    with h5py.File(l1b, "r") as f:
        obs = f["observation_data"]
        for b in bandas:
            dn = obs[b][:].astype(np.int64)
            qfk = b + "_quality_flags"
            qf = obs[qfk][:].astype(np.int64) if qfk in obs else None
            lut = np.asarray(obs[b + "_brightness_temperature_lut"][:], dtype=np.float64)
            lut_ok = lut[np.isfinite(lut) & (lut > 0)]
            bt = lut[np.clip(dn, 0, len(lut) - 1)]
            bt = np.where(np.isin(dn, FLAG_DNS_VIIRS) | (bt <= 0), np.nan, bt)
            at = {}
            if qf is not None:
                for k, v in obs[qfk].attrs.items():
                    at[k] = v.tolist() if hasattr(v, "tolist") else (v.decode() if isinstance(v, bytes) else str(v))
            out[b] = {"dn": dn, "qf": qf, "bt": bt, "lut_max": float(lut_ok.max()), "qf_attrs": at,
                      "valid_max": (obs[b].attrs.get("valid_max").tolist() if "valid_max" in obs[b].attrs else None)}
    return out


def contar_viirs(raw, pipe, mir, tir, ventana, cumulo, vecinos):
    """Cuenta por banda en la ventana y en el cúmulo. Devuelve también la máscara de perdidos (MIR o TIR)."""
    res = {}
    perdido = np.zeros(ventana.shape, dtype=bool)
    for b in (mir, tir):
        r = raw[b]
        qf = r["qf"] if r["qf"] is not None else np.zeros_like(r["dn"])
        tope = np.isfinite(r["bt"]) & (r["bt"] >= r["lut_max"] - 0.5)
        lost = np.isfinite(r["bt"]) & ~np.isfinite(pipe[b])
        perdido |= lost
        d = {}
        for nombre, m in (("ventana", ventana), ("cumulo", cumulo), ("vecinos_cumulo", vecinos)):
            d[nombre] = {"n": int(m.sum()), "bit4_sat": int(((qf & BIT_SAT) != 0)[m].sum()),
                         "bit2_oor": int(((qf & BIT_OOR) != 0)[m].sum()),
                         "bit128_somesat": int(((qf & BIT_SOMESAT) != 0)[m].sum()),
                         "tope_lut": int(tope[m].sum()), "perdidos_pipeline": int(lost[m].sum()),
                         "sentinela": int(np.isin(r["dn"], FLAG_DNS_VIIRS)[m].sum())}
        d["lut_max_k"] = r["lut_max"]
        d["qf_attrs"] = r["qf_attrs"]
        d["valid_max_dn"] = r["valid_max"]
        res[b] = d
    return res, perdido


def crudo_modis(hdf, pm):
    from pyhdf.SD import SD, SDC
    sd = SD(str(hdf), SDC.READ)
    s = sd.select("EV_1KM_Emissive")
    data = s.get().astype(np.int64)
    at = s.attributes()
    s.endaccess()
    sd.end()
    out = {}
    for nombre, idx, lam in (("B21", pm.BAND21_IDX, pm.BAND21_LAMBDA), ("B22", pm.BAND22_IDX, pm.BAND22_LAMBDA),
                             ("B31", pm.BAND31_IDX, pm.BAND31_LAMBDA)):
        si = data[idx]
        sc, of = float(at["radiance_scales"][idx]), float(at["radiance_offsets"][idx])
        rad = (si - of) * sc
        out[nombre] = {"si": si, "rad": np.where(si > 32767, np.nan, rad), "rad_tope": (32767 - of) * sc, "lam": lam}
    return out


def contar_modis(raw, ventana, cumulo, vecinos):
    res = {}
    for b, r in raw.items():
        si = r["si"]
        d = {}
        for nombre, m in (("ventana", ventana), ("cumulo", cumulo), ("vecinos_cumulo", vecinos)):
            v = si[m]
            d[nombre] = {"n": int(m.sum()), "si_65533_sat": int((v == 65533).sum()),
                         "si_invalido": int((v > 32767).sum()),
                         "codigos": {str(int(c)): int((v == c).sum()) for c in np.unique(v[v > 32767])},
                         "tope_32767": int((v == 32767).sum())}
        res[b] = d
    # perdido: sin MIR utilizable (B22 y B21 inválidas) o sin TIR (B31 inválida) -> NTI NaN
    perdido = (~np.isfinite(raw["B22"]["rad"]) & ~np.isfinite(raw["B21"]["rad"])) | ~np.isfinite(raw["B31"]["rad"])
    return res, perdido


# ---------------------------------------------------------------------------------------------------------------
def mascaras(shape, dist, inner, c0):
    ventana = dist <= inner
    ventana2 = dist <= 2 * inner
    cumulo = np.zeros(shape, dtype=bool)
    for i, j in c0:
        cumulo[i, j] = True
    vec = np.zeros(shape, dtype=bool)
    for i, j in c0:
        vec[max(i - 1, 0):i + 2, max(j - 1, 0):j + 2] = True
    vec &= ~cumulo
    return ventana | vec | cumulo, ventana2, cumulo, vec


def cota_viirs(raw, mir, perdido, ventana, t_bg, lam, k_area, dist):
    filas = []
    if t_bg is None or k_area is None:
        return [{"error": "sin t_bg o sin área", "n": int((perdido & ventana).sum())}]
    L_bg = float(planck(np.array([t_bg]), lam)[0])
    for i, j in zip(*np.where(perdido & ventana)):
        bt = raw[mir]["bt"][i, j]
        base = bt if np.isfinite(bt) else raw[mir]["lut_max"]
        L = float(planck(np.array([base]), lam)[0])
        filas.append({"ij": [int(i), int(j)], "dist_km": round(float(dist[i, j]), 3), "bt_mir_crudo": float(bt),
                      "qf_mir": int(raw[mir]["qf"][i, j]) if raw[mir]["qf"] is not None else None,
                      "mw": max(L - L_bg, 0.0) * k_area / 1e6})
    return filas


def cota_modis(raw, perdido, ventana, t_bg, k_area, dist, pm):
    filas = []
    lam = pm.BAND21_LAMBDA
    if t_bg is None or k_area is None:
        return [{"error": "sin t_bg o sin área", "n": int((perdido & ventana).sum())}]
    L_bg = pm.C1 / (lam ** 5 * (np.exp(pm.C2 / (lam * t_bg)) - 1))
    for i, j in zip(*np.where(perdido & ventana)):
        r22, r21 = raw["B22"]["rad"][i, j], raw["B21"]["rad"][i, j]
        L = r22 if np.isfinite(r22) else (r21 if np.isfinite(r21) else raw["B21"]["rad_tope"])
        filas.append({"ij": [int(i), int(j)], "dist_km": round(float(dist[i, j]), 3), "L_mir": float(L),
                      "si": {b: int(raw[b]["si"][i, j]) for b in raw}, "mw": max(float(L) - L_bg, 0.0) * k_area / 1e6})
    return filas


LAADS = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData"


def bajar_laads(sensor, nombre, dest):
    """Respaldo cuando CMR no indexa el gránulo (2026-10-20 22:58 UTC: CMR devolvía 0 gránulos VIIRS y 5 MODIS del
    2026-10-18, que el probe de #871 encontró ese mismo día a las 13:16; el archivo de LAADS sí los lista). Baja el
    L1B y la GEO desde el listado del archivo de LAADS, con el token de Earthdata (A71). Mismo archivo: el nombre del
    L1B es el del record; la GEO es la del mismo instante y la misma versión."""
    import re
    import requests
    from pipeline.fetch import PRODUCTS
    tok = os.environ.get("EARTHDATA_TOKEN", "")
    stamp = ".".join(nombre.split(".")[1:3])
    ver = nombre.split(".")[3]
    col = {"002": "5200", "021": "5201", "061": "61"}[ver]
    ydoy = stamp[1:5], stamp[5:8]
    dest.mkdir(parents=True, exist_ok=True)
    try:   # la sesión de earthaccess ya autenticada (auth()) conserva el token en la redirección a URS
        import earthaccess
        sesion = earthaccess.get_requests_https_session()
    except Exception:  # noqa: BLE001
        sesion = requests.Session()
    sesion.headers.setdefault("Authorization", "Bearer " + tok)
    out = []
    for key in p871.PRODUCTO[sensor]:
        if key is None:
            out.append(None)
            continue
        sn = PRODUCTS[key]["short_name"]
        url_dir = "%s/%s/%s/%s/%s" % (LAADS, col, sn, ydoy[0], ydoy[1])
        lst = requests.get(url_dir + ".json", timeout=120).text
        nombres = [n for n in re.findall(r'"name":\s*"([^"]+)"', lst) if n.startswith(sn + "." + stamp + ".")]
        if key.endswith("_L1B") and nombre in nombres:
            nombres = [nombre]
        if not nombres:
            return None, "LAADS sin %s %s" % (sn, stamp)
        f = dest / nombres[0]
        # Primero earthaccess.download con la URL (el mismo manejo de la autenticación que usa el NRT);
        # si no deja el archivo, la sesión con el token.
        try:
            import earthaccess
            earthaccess.download(["%s/%s" % (url_dir, nombres[0])], str(dest))
        except Exception as e:  # noqa: BLE001
            print("   earthaccess.download: %s" % e, flush=True)
        if f.exists() and f.stat().st_size > 1_000_000:
            out.append(f)
            continue
        for intento in range(3):
            try:
                with sesion.get("%s/%s" % (url_dir, nombres[0]), stream=True, timeout=300) as r:
                    r.raise_for_status()
                    with open(f, "wb") as fh:
                        for ch in r.iter_content(1 << 20):
                            fh.write(ch)
                break
            except Exception as e:  # noqa: BLE001
                if intento == 2:
                    return None, "LAADS descarga fallida %s: %s" % (nombres[0], e)
        if f.stat().st_size < 1_000_000 or f.read_bytes()[:8].lstrip().startswith(b"<"):
            return None, "LAADS devolvió algo que no es el archivo (%d bytes): %s | %r" % (
                f.stat().st_size, nombres[0], f.read_bytes()[:600])
        out.append(f)
    nota = "bajado del archivo de LAADS (CMR no lo indexaba)" + (
        "" if out[0].name == nombre else "; L1B reprocesado: %s en lugar de %s" % (out[0].name, nombre))
    return tuple(out), nota


def procesar(p, mods, vols, dest):
    sensor, nombre = p["sensor"], p["granulo"]
    vol = vols[p.get("volcan", p871.VOLCAN)]
    par, nota = p871.bajar(vol, sensor, nombre, dest)
    if par is None:
        print("   CMR: %s -> respaldo LAADS" % nota, flush=True)
        par, nota = bajar_laads(sensor, nombre, dest)
    if par is None:
        raise RuntimeError(nota)
    res = {"pasada": p, "nota_granulo": nota}
    modis = sensor.startswith("MODIS")
    if modis:
        mod = mods["modis"]
    else:
        mod = mods["750"] if sensor.endswith("_750") else mods["375"]
    if p["grupo"] == "POS":
        geo_lat = geo_lon = None
    else:
        r = p871.correr(mod, "MODIS" if modis else "VIIRS", vol, par, "control")
        res["control"] = {k: r.get("record", {}).get(k) for k in ("primary_cluster", "f5_core_vrp_mw", "t_bg_k",
                                                                  "t_max_k", "sensor_zenith_deg", "n_anomalous_pixels")}
        res["C_P1"] = p871.control_p1(p871.persistido(par[0].name) or p871.persistido(nombre), r.get("record") or {})
        res["_anom"] = [(a["lat"], a["lon"]) for a in ((r.get("record") or {}).get("anomaly_pixels") or [])]
    est = p871.ESTADO
    c0 = (est.get("cumulos") or {}).get("c0") or [] if p["grupo"] != "POS" else []
    alat, alon = get_detection_anchor(vol)
    inner = float(vol.get("inner_radius_km") or 5.0)
    if modis:
        pm = mod
        g = pm.read_modis_l1b(par[0])
        lat, lon = g["lat"], g["lon"]
        dist = haversine_km(alat, alon, lat, lon)
        raw = crudo_modis(par[0], pm)
        if p["grupo"] == "POS":
            m25 = haversine_km(vol["lat"], vol["lon"], lat, lon) <= 25.0
            res["C_POS"] = {b: {"si_65533_25km": int((raw[b]["si"][m25] == 65533).sum()),
                                "si_invalido_25km": int((raw[b]["si"][m25] > 32767).sum())} for b in raw}
            return res
        ven, ven2, cum, vec = mascaras(lat.shape, dist, inner, c0)
        res["conteos"], perdido = contar_modis(raw, ven, cum, vec)
        res["conteos_2inner"], _ = contar_modis(raw, ven2, cum, vec)
        k_area = pm.WOOSTER_COEFF * float(np.nanmedian(est["areas"])) if est.get("areas") is not None else None
        res["perdidos"] = cota_modis(raw, perdido, ven, res["control"]["t_bg_k"], k_area, dist, pm)
    else:
        mir, tir = ("M13", "M15") if sensor.endswith("_750") else ("I04", "I05")
        lam = mod.M13_LAMBDA if mir == "M13" else mod.I04_LAMBDA
        geo = mod.read_viirs_mod_geo(par[1]) if mir == "M13" else mod.read_viirs_geo(par[1])
        lat, lon = geo["lat"], geo["lon"]
        dist = haversine_km(alat, alon, lat, lon)
        pipe = mod.read_viirs_mod_l1b(par[0]) if mir == "M13" else mod.read_viirs_l1b(par[0])
        raw = crudo_viirs(par[0], (mir, tir))
        if raw[mir]["bt"].shape != lat.shape:
            raise RuntimeError("forma L1B %s distinta de la GEO %s" % (raw[mir]["bt"].shape, lat.shape))
        ven, ven2, cum, vec = mascaras(lat.shape, dist, inner, c0)
        res["conteos"], perdido = contar_viirs(raw, pipe, mir, tir, ven, cum, vec)
        res["conteos_2inner"], _ = contar_viirs(raw, pipe, mir, tir, ven2, cum, vec)
        k_area = mod.WOOSTER_COEFF * float(np.nanmedian(est["areas"])) if est.get("areas") is not None else None
        res["perdidos"] = cota_viirs(raw, mir, perdido, ven, res["control"]["t_bg_k"], lam, k_area, dist)
        res["bt_cruda_max_ventana"] = {b: float(np.nanmax(np.where(ven, raw[b]["bt"], np.nan))) for b in (mir, tir)}
        res["bt_pipeline_max_ventana"] = {b: float(np.nanmax(np.where(ven, pipe[b], np.nan))) for b in (mir, tir)}
    # C-IDX: los índices del cúmulo capturado caen sobre los píxeles anómalos del record (misma grilla, mismo
    # gránulo). Si no, la ventana del cúmulo está mal puesta y la pasada no se interpreta.
    anom = res.pop("_anom", [])
    cum_ll = [(float(lat[i, j]), float(lon[i, j])) for i, j in c0]
    res["C_IDX"] = {"shape_cumulos": list((est.get("cumulos") or {}).get("lat", np.zeros(0)).shape),
                    "shape_geo": list(lat.shape),
                    "cumulo_en_anomalos": sum(1 for a in cum_ll if any(abs(a[0] - b[0]) < 2e-4 and abs(a[1] - b[1]) < 2e-4 for b in anom)),
                    "n_cumulo": len(c0)}
    res["k_area"] = k_area
    res["n_cumulo"] = len(c0)
    res["n_perdidos_ventana"] = int((perdido & ven).sum())
    res["cota_inferior_mw"] = (None if any("error" in f for f in res["perdidos"])
                               else float(sum(f["mw"] for f in res["perdidos"])))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", choices=("V375", "V750_MODIS"), required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--min-mirova", type=float, default=1.0)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    todas = json.loads((HERE / "pasadas.json").read_text(encoding="utf-8"))
    # Grupo B: sólo alertas de MIROVA de 1 MW o más (las protegidas del criterio, docs/MISSION.md): ahí vive el déficit.
    pas = [p for p in todas if es_job(p["sensor"], a.job)
           and (p["grupo"] != "B" or (p.get("mirova_mw") or 0) >= a.min_mirova)]
    if a.job == "V750_MODIS":
        pas.append(POSITIVO)
    # Orden: C, B, POS y al final A. El 2026-10-20 CMR no indexaba el 2026-10-18 (runs 39511561148 y 39512351523
    # abortaron en las dos primeras pasadas, que eran del grupo A); C y B sí están en CMR, así que el corte de las
    # dos primeras fallas vuelve a medir un defecto del probe y no la caída de CMR.
    pas.sort(key=lambda p: {"C": 0, "B": 1, "POS": 2, "A": 3}[p["grupo"]])
    print("job %s: %d pasadas" % (a.job, len(pas)), flush=True)
    from pipeline.fetch import auth
    from run_pipeline import load_volcanoes
    familias = {"V375": ["VIIRS"], "V750_MODIS": ["VIIRS", "MODIS"]}[a.job]
    mods = {}
    for fam in familias:
        mods.update(p871.instalar(fam))
    auth()
    vols = {v["name"]: v for v in load_volcanoes()}
    dest = Path(os.environ.get("VRP_TMP_DIR", str(HERE / "granulos")))
    faltan = 0
    for p in pas:
        print("\n== %s %s %s" % (p["grupo"], p["sensor"], p["granulo"]), flush=True)
        try:
            res = procesar(p, mods, vols, dest)
            res["ok"] = True
            c = res.get("conteos") or res.get("C_POS")
            print("   cota %s MW | C-P1 %s | %s" % (res.get("cota_inferior_mw"), res.get("C_P1"),
                                                   json.dumps({b: (v.get("ventana") if isinstance(v, dict) and "ventana" in v else v)
                                                               for b, v in (c or {}).items()}, default=str)[:600]), flush=True)
        except Exception as e:  # noqa: BLE001
            res = {"pasada": p, "ok": False, "error": "%s: %s" % (type(e).__name__, e), "traceback": traceback.format_exc()}
            print("   ERROR", res["error"], flush=True)
            faltan += 1
            if faltan == 2 and pas.index(p) == 1:   # las dos primeras cayeron: defecto del probe, no de la red
                print(res["traceback"], flush=True)
                print("las dos primeras pasadas fallaron: se aborta para no bajar el resto", flush=True)
                return 3
        finally:
            shutil.rmtree(dest, ignore_errors=True)
        tag = "%s_%s_%s" % (p["grupo"], p["sensor"], ".".join(p["granulo"].split(".")[1:3]))
        (out / (tag + ".json")).write_text(json.dumps(res, default=p871.a_json, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    print("\nfaltan %d de %d" % (faltan, len(pas)))
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
