# -*- coding: utf-8 -*-
"""Prueba sin red del arnés de MOD-D (probe_paquete.py), con la escena sintética de la 1.17 (81 x 81 píxeles de 1 km
alrededor del cráter de Láscar) que pasa por el pipeline REAL de este checkout (calculate_vrp + store.append_record +
predicado del tablero con node) y por probe_portes.procesar SIN MODIFICAR (sólo su lector de HDF se reemplaza por uno
que entrega la misma escena, porque pyhdf no corre en Windows).

Casos (cada uno con lo que el arnés TIENE que dar; si no, sale 1):
  FOCO     un píxel de 335 K en el cráter, con B22 saturada en ese píxel (entra B21: D33), y la
           geolocalización interpolada corrida 2 km al sur de MxD03. K publica; K33 difiere de K (el parche de D33
           actúa); el PM (`fisica`) detecta con npix >= 1 y es IGUAL a mirova_port.correr sobre la misma grilla armada
           aparte (identidad del envoltorio); las 5 variantes están; la grilla quedó guardada con el id de la pasada; el
           S-1 sale "ok" con identidad contra el oráculo; la fila y el frame del cráter son los del píxel MxD03 más
           cercano (40, 40: costura); los archivos originales siguen y no quedan enlaces.
  VACIO    foco a 35 km, fuera del ROI y de la grilla: K no publica y el PM no tiene píxeles.
  PURAS    id_pasada da un índice distinto a cada una de las 5.465 pasadas; grillas.json trae los 11 volcanes con la
           grilla de S159.
MUTACIONES del arnés (cada una tiene que hacer fallar al menos una aserción; se cuentan sólo si la falla es una
aserción de este archivo, no una excepción, S156; control de caída: se informa aparte si una mutación hace caer el
arnés):
  M1  bajar_par devuelve (geo, l1b) al revés          M2  K33 parchea el flag en el módulo equivocado
  M3  resumen_port pierde vrp_mw                       M4  el cráter se busca en la geolocalización interpolada
  M5  correr_port no borra los enlaces                 M6  id_pasada usa sólo el volcán
Uso: python probar_probe_paquete.py   (sale 1 si algo falla; necesita node)
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for p in (RAIZ, RAIZ / "experiments/_s151_mxd03_etiquetas", AQUI):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probe_paquete as A  # noqa: E402
import probar_probe_mxd03 as T  # noqa: E402  (escena de la 1.17)

sys.path.insert(0, str(AQUI))
PP, MP, pm, P = A.PP, A.MP, A.pm, A.P
GRILLA = json.load(open(AQUI / "grillas.json", encoding="utf-8"))["Lascar"]


def fila_pob(lab="protegida"):
    return {"vol": T.VOLCAN["name"], "dt": "2026-03-14 07:05", "noche": "2026-03-14", "sensor": "MODIS_AQUA",
            "z": 20.0, "lab": lab, "inner": 5.0, "pub_guardada": 1, "pc_vrp_guardada": 1.0, "expuesta": False,
            "granule": T.L1B.name, "codigo_sha": "abc"}


def lector_falso(datos, latlon_m):
    """Hace lo que probe_portes.leer_modis hace con el HDF (radiancias por merge_mir_bands, MxD03 y la interpolada de
    5 km), sobre la escena sintética. Exige el orden de los archivos (L1B primero), como el probe."""
    def leer(l1b, geo, lat0, lon0):
        if not Path(l1b).name.startswith("MYD021KM") or not Path(geo).name.startswith("geo"):
            return None, None
        b21, b22, b31 = (np.asarray(datos[k], np.float64) for k in ("band21", "band22", "band31"))
        n = b21.shape
        crop = {"lat": np.asarray(latlon_m[0], np.float64), "lon": np.asarray(latlon_m[1], np.float64),
                "lat5": np.asarray(datos["lat"], np.float64), "lon5": np.asarray(datos["lon"], np.float64),
                "mir": pm.merge_mir_bands(b21, b22, True), "mir_b21": pm.merge_mir_bands(b21, b22, False),
                "tir": b31, "sat": {"b22_nan_con_b21": int((np.isnan(b22) & np.isfinite(b21)).sum())},
                "sensor_zenith": np.full(n, 20.0), "sensor_azimuth": np.full(n, 90.0),
                "solar_zenith": np.full(n, 120.0), "solar_azimuth": np.full(n, 0.0)}
        return crop, None
    return leer


def caso(foco):
    verdad = T.escena(foco_km_norte=0.0) if foco else T.escena(foco_km_norte=35.0)
    if foco:
        k = T.N // 2
        verdad["band22"] = verdad["band22"].copy()
        verdad["band22"][k, k] = np.nan    # B22 saturada en el foco (el pixel del crater)
    interp = dict(verdad)
    interp["lat"] = (verdad["lat"] - 2.0 / 111.32).astype(np.float32)
    latlon_m = (verdad["lat"].copy(), verdad["lon"].copy())
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        l1b, geo = d / T.L1B.name, d / "geo.hdf"
        l1b.write_bytes(b"l1b")
        geo.write_bytes(b"geo")
        destino = d / "destino"
        destino.mkdir()
        out = d / "out"
        out.mkdir()
        o = {"id": 7, "volcan": T.VOLCAN["name"], "hora_utc": "2026-03-14 07:05", "b": "MODIS", "granule": T.L1B.name,
             "grilla": GRILLA}
        with patch.object(PP, "leer_modis", lector_falso(interp, latlon_m)):
            r = A.medir_record(l1b, geo, T.VOLCAN, None, interp, latlon_m, fila_pob(), "MYD021KM.A2026073.0705", o,
                               destino, out)
            crop, _ = PP.leer_modis(l1b, geo, 0, 0)
        mir, tir = PP.grillar(crop, GRILLA, GRILLA["epsg"])
        directo = MP.correr(mir, tir, GRILLA, GRILLA["X0"], GRILLA["Y0"], 0, r.get("sunglint") or 180.0,
                            MP.SENSORES["MODIS"], modo="fisica", semillas=PP.SEMILLAS)
        r["_directo"] = directo
        r["_originales"] = l1b.exists() and geo.exists()
        r["_sobrantes"] = sorted(str(q.relative_to(destino)) for q in destino.rglob("*"))
        r["_grilla_guardada"] = (out / "grilla_007.npz").exists()
    return r


def aserciones(rf, rv, ids, grillas):
    f = []

    def exige(cond, msg):
        if not cond:
            f.append(msg)

    exige(rf["port_estado"] == "ok", "FOCO: el probe no termino ok (%s)" % rf["port_estado"])
    exige(rf["pub"]["K"] == 1, "FOCO: K no publica el foco del crater")
    exige(rf["k33_igual_k"] is False, "FOCO: K33 igual a K con B22 saturada (el parche de D33 no actua)")
    exige(rf["saturados"] == {"b22_nan_con_b21": 1}, "FOCO: el probe no conto el pixel con B21 (%s)" % rf["saturados"])
    port = rf.get("port") or {}
    exige(set(port) == set(A.VARIANTES), "FOCO: variantes del port %s" % sorted(port))
    pmr = port.get("fisica") or {}
    exige((pmr.get("npix") or 0) >= 1, "FOCO: el PM no detecta el foco")
    d = rf["_directo"]
    exige(pmr.get("npix") == d["npix"] and pmr.get("vrp_mw") is not None and d["vrp_mw"] is not None
          and abs(pmr["vrp_mw"] - d["vrp_mw"]) < 1e-9, "FOCO: el PM del arnes no es mirova_port.correr directo "
          "(%s, %s contra %s, %s)" % (pmr.get("npix"), pmr.get("vrp_mw"), d["npix"], d["vrp_mw"]))
    exige(rf["_grilla_guardada"], "FOCO: la grilla no quedo guardada como grilla_007.npz")
    s1 = rf.get("s1") or {}
    exige(s1.get("estado") == "ok" and s1.get("identidad_ok") is True, "FOCO: S-1 %s" % s1.get("estado"))
    c = rf["crater_mxd03"]
    exige(c["linea"] == T.N // 2 and c["frame"] == T.N // 2 and c["costura"] is True,
          "FOCO: crater en MxD03 (%s, %s, costura %s), esperado (40, 40, True)" % (c["linea"], c["frame"], c["costura"]))
    exige(rf["_originales"], "FOCO: el arnes borro los archivos originales")
    exige(rf["_sobrantes"] == [], "FOCO: quedaron archivos del port en el destino: %s" % rf["_sobrantes"][:4])
    exige(rf["k_slim"] is not None and "primary_cluster" in rf["k_slim"], "FOCO: falta el record slim de K")

    exige(rv["port_estado"] == "ok", "VACIO: el probe no termino ok")
    exige(rv["pub"]["K"] == 0, "VACIO: K publica sin foco")
    exige(((rv.get("port") or {}).get("fisica") or {}).get("npix") == 0, "VACIO: el PM tiene pixeles sin foco")

    exige(len(ids) == 5465 and len(set(ids.values())) == 5465, "PURAS: id_pasada no da 5.465 indices distintos")
    o = json.load(open(RAIZ / "experiments/_s159/portes/objetivos_portes.json", encoding="utf-8"))
    g159 = {x["volcan"]: x["grilla"] for x in o if x["b"] == "MODIS"}
    exige(grillas == g159 and len(grillas) == 11, "PURAS: grillas.json distinta de la de S159")
    return f


def correr():
    pob = json.load(open(A.POBLACION, encoding="utf-8"))
    grillas = json.load(open(A.GRILLAS, encoding="utf-8"))
    return caso(True), caso(False), A.id_pasada(pob), grillas


MUTACIONES = {
    "M1_bajar_al_reves": lambda: patch.object(A, "correr_port", _correr_port_al_reves),
    "M2_k33_modulo_equivocado": lambda: patch.object(A, "k33", _k33_muerto),
    "M3_resumen_sin_vrp": lambda: patch.object(A, "resumen_port", _resumen_sin_vrp),
    "M4_crater_en_interpolada": lambda: patch.object(P, "desplazamiento_crater", _desp_interpolada),
    "M5_no_borra_enlaces": lambda: patch.object(A, "correr_port", _correr_port_sin_borrar),
    "M6_id_por_volcan": lambda: patch.object(A, "id_pasada", _id_por_volcan),
}
_ORIG = {"correr_port": A.correr_port, "resumen_port": A.resumen_port, "desp": P.desplazamiento_crater}


def _correr_port_al_reves(o, l1b, geo, destino, outdir):
    return _ORIG["correr_port"](o, geo, l1b, destino, outdir)


def _k33_muerto(l1b, geo, volcan, feats, datos):
    import pipeline.profile as prof
    with patch.object(prof, "ENABLE_MODIS_MIR_LAMBDA_POR_BANDA", True):
        return A.PB.brazo(l1b, geo, volcan, feats, datos)[0]


def _resumen_sin_vrp(p):
    r = _ORIG["resumen_port"](p)
    if r:
        r.pop("vrp_mw")
    return r


def _desp_interpolada(lat_i, lon_i, lat_m, lon_m, vent):
    return _ORIG["desp"](lat_m, lon_m, lat_i, lon_i, vent)


def _correr_port_sin_borrar(o, l1b, geo, destino, outdir):
    tmp = Path(tempfile.mkdtemp(prefix="modd_", dir=destino))
    enl = []
    for p in (l1b, geo):
        q = tmp / Path(p).name
        q.write_bytes(Path(p).read_bytes())
        enl.append(q)
    with patch.object(PP, "bajar_par", lambda *_a, **_k: (tuple(enl), None)):
        r = PP.procesar(o, destino, outdir, sin_k=True)
    (tmp / "sobra.txt").write_text("x")
    return r


def _id_por_volcan(pob):
    return {(f["vol"], f["dt"]): hash(f["vol"]) % 100000 for g in pob["granulos"] for f in g["records"]}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rf, rv, ids, grillas = correr()
    f = aserciones(rf, rv, ids, grillas)
    print("PM foco:", {k: (rf["port"]["fisica"] or {}).get(k) for k in ("npix", "vrp_mw")}, "| directo:",
          {k: rf["_directo"].get(k) for k in ("npix", "vrp_mw")}, "| K pub", rf["pub"], "| S-1",
          {k: rf["s1"].get(k) for k in ("estado", "identidad_ok", "n2_g", "n2_roi1")})
    print("SIN MUTAR:", "OK" if not f else f)
    atrapadas, caidas, vivas = [], [], []
    for nombre, fab in MUTACIONES.items():
        try:
            with fab():
                g = aserciones(*correr())
        except Exception as e:  # noqa: BLE001
            caidas.append((nombre, f"{type(e).__name__}: {e}"[:160]))
            continue
        (atrapadas if g else vivas).append((nombre, g[:2]))
    for x in atrapadas:
        print("  atrapada por asercion:", x)
    for x in caidas:
        print("  CAE (no cuenta como atrapada):", x)
    for x in vivas:
        print("  VIVA:", x)
    ok = not f and not vivas and not caidas
    print("RESULTADO:", "OK" if ok else "FALLA", f"| atrapadas {len(atrapadas)} de {len(MUTACIONES)}, caen {len(caidas)}, "
          f"vivas {len(vivas)}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
