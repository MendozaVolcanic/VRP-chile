# -*- coding: utf-8 -*-
"""S165, Tarea 4 del plan 2026-10-25-flag-mxd03-modis: ¿el flag `enable_modis_geo_mxd03` reproduce el brazo X de MOD-B,
record por record?

POR QUÉ. El A/B MOD-B (S162, 5.465 pasadas) midió el MxD03 con un arnés que REEMPLAZABA la lat/lon del lector antes de
`calculate_vrp` (brazo X; experiments/_s162_mxd03/probe_mxd03_ab.py). El flag hace lo mismo dentro de pipeline/. Si
el flag no da lo mismo que el brazo X, lo que se midió no es lo que se adoptaría. Es la misma función con el mismo
insumo: sin tolerancia en la publicación, y `pc.vrp_mw` a 0,001 MW (la tolerancia de MOD-B, §8 control 4).

QUÉ CORRE, en Linux (pyhdf) y con EARTHDATA_TOKEN, sobre los 5 gránulos del humo (4 del humo de MOD-B y uno con relleno
de geolocalización, MOD021KM.A2026113.0150) y todos sus records de la población de MOD-B:
  ON   producción + ENABLE_MODIS_GEO_MXD03 (los otros dos apagados)   -> tiene que ser el brazo X;
  OFF  producción tal cual                                             -> tiene que ser el brazo K (control negativo:
       en los records donde K y X difieren, OFF da K y no X; si no, el arnés no ve el flag);
  SD   ON + ENABLE_MODIS_CRATER_SIN_DATO                               -> cuenta los records que pasan a «sin dato».
La referencia (brazos K y X, publicación) son los 18 records de esos gránulos extraídos de los artefactos de MOD-B
(runs 40122029477 y 40126381034) a `referencia_mod_b.jsonl`, con su procedencia.
EQUIVALENTE exige, en los 18: misma publicación, `pc.vrp_mw` a 0,001 MW y además el resumen del record idéntico al del
brazo (ON contra X, OFF contra K). POR QUÉ el resumen: en 14 de los 18 records K y X ya coinciden en publicación y en
`pc.vrp_mw`, así que con esos dos criterios solos el flag podría no hacer nada y salir equivalente (verificador S165,
V165-02); en el resumen K y X difieren en los 18.

Uso (lo despacha la coordinadora con .github/workflows/probe-mxd03-equivalencia.yml):
    python experiments/_s165_mxd03_flag/equivalencia.py --out out
"""
import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

GRANULOS = ("MYD021KM.A2026073.0705", "MYD021KM.A2026086.0710", "MYD021KM.A2026283.0740", "MOD021KM.A2026284.0140",
            "MOD021KM.A2026113.0150")
RELLENO = "MOD021KM.A2026113.0150"
TOL_VRP = 0.001


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


def comparar(res, ref):
    """(misma publicación y pc.vrp a 0,001, resumen idéntico, campos distintos)."""
    if res is None or ref is None:
        return res is None and ref is None, res is None and ref is None, [] if res is ref else ["record"]
    distintos = sorted(k for k in set(res) | set(ref) if res.get(k) != ref.get(k))
    a, b = res.get("pc_vrp"), ref.get("pc_vrp")
    vrp_ok = (a is None) == (b is None) and (a is None or abs(a - b) <= TOL_VRP)
    return vrp_ok, not distintos, distintos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--referencia", default=str(AQUI / "referencia_mod_b.jsonl"))
    a = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: no se usa usuario y clave (A71).")
    M = _cargar("probe_mxd03_ab", "experiments/_s162_mxd03/probe_mxd03_ab.py")
    P = M.P
    from pipeline import process_modis as pm
    import run_pipeline as rp
    from pipeline.fetch import auth
    auth()

    ref = {}
    for linea in open(a.referencia, encoding="utf-8"):
        r = json.loads(linea)
        if r.get("tipo") == "record":
            ref[(r["clave"], r["vol"])] = r
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    salida = open(out / "equivalencia.jsonl", "w", encoding="utf-8")
    t0, tot = time.time(), {"n": 0, "on_pub_vrp": 0, "on_resumen": 0, "off_pub_vrp": 0, "off_resumen": 0,
                            "kx_difieren": 0, "control_negativo_ok": 0, "sd_none": 0, "errores": 0}
    for clave in GRANULOS:
        prod, patron = clave.split(".", 1)
        l1b = M.bajar(prod, patron, out / "hdf")
        geo = M.bajar(prod.replace("021KM", "03"), patron, out / "hdf")
        if l1b is None or geo is None:
            tot["errores"] += 1
            salida.write(json.dumps({"clave": clave, "estado": "no_bajado"}) + "\n")
            continue
        datos = pm.read_modis_l1b(l1b)
        for (c, vol), fila in sorted(ref.items()):
            if c != clave:
                continue
            tot["n"] += 1
            v = rp.load_volcanoes(vol)[0]
            feats = rp.VOLCANIC_FEATURES.get(v["name"])
            lector = (lambda _p: P._copia(datos))
            try:
                with patch.object(pm, "ENABLE_MODIS_GEO_MXD03", True):
                    r_on = P.procesar_brazo(l1b, geo, v, None, feats, lector)
                r_off = P.procesar_brazo(l1b, geo, v, None, feats, lector)
                with patch.object(pm, "ENABLE_MODIS_GEO_MXD03", True), \
                        patch.object(pm, "ENABLE_MODIS_CRATER_SIN_DATO", True):
                    r_sd = P.procesar_brazo(l1b, geo, v, None, feats, lector)
                pub_on, pub_off = P.publica([r_on, r_off], v.get("inner_radius_km"))
                s_on, s_off = M.resumen(r_on), M.resumen(r_off)
                on_vrp, on_id, on_dif = comparar(s_on, fila["brazos"]["X"])
                off_vrp, off_id, off_dif = comparar(s_off, fila["brazos"]["K"])
                on_pub_vrp = on_vrp and pub_on == fila["pub"]["X"]
                off_pub_vrp = off_vrp and pub_off == fila["pub"]["K"]
                kx = fila["brazos"]["K"] != fila["brazos"]["X"]
                tot["on_pub_vrp"] += on_pub_vrp
                tot["on_resumen"] += on_id
                tot["off_pub_vrp"] += off_pub_vrp
                tot["off_resumen"] += off_id
                tot["kx_difieren"] += kx
                tot["control_negativo_ok"] += kx and off_id and not comparar(s_off, fila["brazos"]["X"])[1]
                tot["sd_none"] += r_sd is None
                reg = {"clave": clave, "vol": vol, "estado": "ok", "geo_fuente_on": (r_on or {}).get("geo_fuente"),
                       "on_pub_vrp": on_pub_vrp, "on_resumen_identico": on_id, "on_distintos": on_dif,
                       "off_pub_vrp": off_pub_vrp, "off_resumen_identico": off_id, "off_distintos": off_dif,
                       "k_x_difieren": kx, "sin_dato": r_sd is None}
            except Exception as e:  # noqa: BLE001
                tot["errores"] += 1
                reg = {"clave": clave, "vol": vol, "estado": "error", "error": f"{type(e).__name__}: {e}"}
            salida.write(json.dumps(reg, ensure_ascii=False) + "\n")
            print(json.dumps(reg, ensure_ascii=False), flush=True)
        for p in (l1b, geo):
            Path(p).unlink(missing_ok=True)
    tot["minutos"] = round((time.time() - t0) / 60, 1)
    salida.write(json.dumps({"tipo": "pie", **tot}) + "\n")
    salida.close()
    print(json.dumps(tot, ensure_ascii=False))
    ok = (tot["errores"] == 0 and tot["n"] == len(ref) and tot["on_pub_vrp"] == tot["n"]
          and tot["off_pub_vrp"] == tot["n"] and tot["on_resumen"] == tot["n"] and tot["off_resumen"] == tot["n"]
          and tot["control_negativo_ok"] == tot["kx_difieren"])
    print("EQUIVALENTE" if ok else "NO EQUIVALENTE: revisar equivalencia.jsonl")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
