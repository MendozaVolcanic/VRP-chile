# FICHA (SDA, CPLT 372): diagnóstico de sólo lectura. No es detección de producción; no escribe en data/, no commitea.
"""S192, falla «No points given» de la vía MODIS (run 44768057665, trozo 28 de la tanda 7 de la historia de los 34).

Baja MOD021KM.A2026213.0300 y su MOD03, y para Melimoyu (pasó, control), Mentolat, MacaCay y Hudson (fallaron) mide,
dentro del recorte de 45 km de la grilla de MIROVA: cuántos píxeles tienen posición (lo que cuenta el filtro de
cobertura de calcular_vrp_granulo), cuántos tienen además MIR y TIR válidos (lo que interpola remuestrear_grilla), y los
DN crudos de las bandas 21, 22 y 31 (cuántos son sentinelas > 32767 y cuáles). Corre calcular_vrp_granulo y anota la
excepción. Guarda un recorte npz chico por volcán (lat, lon, MIR, TIR, DN crudos) para la prueba de regresión.

Uso: python experiments/_s192_no_points/diag_granulo.py --out out
"""
import argparse
import json
import sys
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

SELLO = "A2026213.0300"
VOLCANES = {"Melimoyu": (-44.08, -72.88), "Mentolat": (-44.7, -73.08),
            "MacaCay": (-45.10501, -73.169326), "Hudson": (-45.9, -72.97)}


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g.get("umm", {}).get("GranuleUR", g))[:160]


def bajar(clave, lat, lon, destino):
    from pipeline.fetch import download_granules, search_granules
    dt = datetime.strptime(SELLO[1:], "%Y%j.%H%M")
    grs = [g for g in search_granules(clave, lat, lon, 25, dt) if SELLO in gname(g)]
    print(clave, "candidatos:", [gname(g) for g in grs], flush=True)
    got = [Path(p) for p in download_granules(grs[:1], destino) if SELLO in Path(p).name]
    return got[0] if got else None


def dn_crudos(ruta):
    from pyhdf.SD import SD, SDC
    sd = SD(str(ruta), SDC.READ)
    s = sd.select("EV_1KM_Emissive")
    bandas = [b.strip() for b in str(s.attributes()["band_names"]).split(",")]
    data = s.get()
    sd.end()
    return {b: data[bandas.index(b)] for b in ("21", "22", "31")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--tmp", default=None)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(a.tmp or (out / "_tmp"))
    tmp.mkdir(parents=True, exist_ok=True)
    from pipeline.fetch import auth
    auth()
    lat0, lon0 = VOLCANES["Mentolat"]
    l1b = bajar("MODIS_TERRA_L1B", lat0, lon0, tmp)
    geo = bajar("MODIS_TERRA_GEO", lat0, lon0, tmp)
    print("L1B", l1b, "GEO", geo, flush=True)
    if l1b is None or geo is None:
        print("falta un archivo")
        return 2

    from pipeline import mirova_v750_codigo as MV
    rad = MV.leer_radiancia_modis(l1b)
    lat, lon, ang = MV.leer_geo_mxd03(geo)
    dn = dn_crudos(l1b)
    res = {"l1b": l1b.name, "geo": geo.name, "forma_l1b": list(rad["MIR"].shape), "forma_geo": list(lat.shape),
           "lat_rango_granulo": [float(np.nanmin(lat)), float(np.nanmax(lat))], "volcanes": {}}
    # perfil por fila de escaneo: fracción de MIR válido en cada línea (ver si faltan escaneos enteros)
    fila_mir_ok = np.isfinite(rad["MIR"]).mean(axis=1)
    fila_geo_ok = np.isfinite(lat).mean(axis=1)
    res["filas_sin_mir"] = int((fila_mir_ok == 0).sum())
    res["filas_sin_geo"] = int((fila_geo_ok == 0).sum())
    res["tramos_filas_sin_mir"] = [int(i) for i in np.flatnonzero(np.diff(np.r_[0, (fila_mir_ok == 0).astype(int), 0]))]
    for nombre, (vl, vo) in VOLCANES.items():
        g = MV.grilla_del_volcan(nombre, paso_m=MV.FAMILIAS["MODIS"]["paso_m"], clave_roi=MV.FAMILIAS["MODIS"]["clave_roi"])
        d = MV._haversine(lat, lon, g["centro_lat"], g["centro_lon"])
        sel = np.isfinite(d) & (d < MV.RADIO_RECORTE_KM)
        r = {"n_con_posicion": int(sel.sum()),
             "n_mir_valido": int((sel & np.isfinite(rad["MIR"])).sum()),
             "n_tir_valido": int((sel & np.isfinite(rad["TIR"])).sum()),
             "dist_min_km": float(np.nanmin(d))}
        for b, arr in dn.items():
            v = arr[sel]
            r[f"dn_b{b}_sentinelas"] = {str(k): int(c) for k, c in Counter(v[v > 32767].tolist()).most_common(8)}
            r[f"dn_b{b}_validos"] = int((v <= 32767).sum())
        if sel.any():
            filas = np.flatnonzero(sel.any(axis=1))
            cols = np.flatnonzero(sel.any(axis=0))
            r["filas"] = [int(filas[0]), int(filas[-1])]
            r["cols"] = [int(cols[0]), int(cols[-1])]
            w = (slice(filas[0], filas[-1] + 1), slice(cols[0], cols[-1] + 1))
            np.savez_compressed(out / f"recorte_{nombre}.npz", lat=lat[w], lon=lon[w], MIR=rad["MIR"][w],
                                TIR=rad["TIR"][w], dn21=dn["21"][w], dn22=dn["22"][w], dn31=dn["31"][w],
                                fila0=filas[0], col0=cols[0])
        try:
            rec = MV.calcular_vrp_granulo(rad, lat, lon, ang, nombre, vl, vo, 5.0, "MODIS_TERRA", familia="MODIS")
            r["resultado"] = "None" if rec is None else {"vrp_mw": rec.get("vrp_mw"),
                                                        "motivo_vacio": rec.get("motivo_vacio")}
        except Exception as e:
            r["resultado"] = f"{type(e).__name__}: {e}"
            r["traza"] = traceback.format_exc()[-1500:]
        res["volcanes"][nombre] = r
        print(nombre, json.dumps({k: v for k, v in r.items() if k != "traza"}, ensure_ascii=False), flush=True)
    (out / "diag_s192_no_points.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
