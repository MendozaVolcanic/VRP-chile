# -*- coding: utf-8 -*-
"""Batería sin red del arnés de MOD-D fase 4 (probe_f4.py). Corre el pipeline REAL de este checkout (K y V con
process_modis.calculate_vrp, la vía de pipeline/mirova_v750_codigo.py, store.append_record y el predicado de
frontend/index.html con node) sobre escenas sintéticas de Láscar. Lo único que se reemplaza es la LECTURA del HDF
(process_modis.read_modis_l1b) y del MxD03 (mirova_v750_codigo.leer_geo_mxd03), porque pyhdf no corre en Windows; la
descarga se reemplaza por funciones falsas y la re-corrida en el codigo_sha por un espía.

POR QUÉ. El evaluador sellado sólo ve filas; si el arnés escribe mal el contrato, el veredicto mide otra cosa. Cada
escenario fija una cosa que el arnés TIENE que dar y la comprueba fila por fila contra evaluar_f4.cargar,
evaluar_f4.evaluable y los controles del evaluador que se pueden correr sobre una fila (§8.1, §8.3, §8.9):
  ESCENA    un píxel débil a ~0,9 km del cráter y una fuente radiante alargada desde ~3 km hacia afuera: las tres
            distancias son distintas y dan clases distintas (radiante far; cercano y pico summit); V no publica y
            V-cercano y V-pico sí; la distancia radiante del arnés reproduce centroid_dist_km y la clase del record de V
            (§8.9a, con control_posicion del evaluador); el predicado del evaluador sobre los slim da lo mismo que el del
            runner sobre los records completos en los cuatro brazos; la fila calza con cargar/evaluable; la grilla npz
            re-corrida con procesar_grilla da el mismo record; la captura no altera a V (V con y sin envoltorio, igual).
  FUERA     el gránulo no cubre el volcán: motivo volcan_fuera_del_granulo, sin npz, pub_runner de K presente.
  INVALIDA  TIR bajo 200 K en toda la escena: motivo escena_invalida (sale del denominador sellado).
  NADA      sin fuente: la vía corre (marca True), sin alertadas, dist None, V no publica, evaluable.
  SIN_GRILLA la vía no tiene grilla: sigue K y la marca sin_grilla sale como falla de la vía.
  KPROD     k_difiere_de_guardado False contra un record guardado igual (sin re-corrida) y True contra uno distinto
            (re-corrida con el codigo_sha del guardado; k_reproducida_en_su_sha copia lo que dijo la re-corrida).
  BAJAR     por nombre: el pedido (otro_granulo False), el vigente (True), nada (None), reintento tras una excepción.
  PARTES    las partes de la población cubren todo sin repetir; --de distinto falla; el humo sin una pasada falla.
  HUMO      humo_f4.txt trae 25 pasadas distintas con Láscar 2026-04-25 07:35 y Chillán 2026-10-25 07:20.
  DATA      registro_guardado encuentra el record de Láscar 2026-04-25 07:35 en data/ del checkout.
  ARBOL     extraer_arbol saca con git archive sólo pipeline, scripts y volcanoes.yaml (nada de data/).
  CABECERA  la cabecera trae commit, sha256 del tablero y de la población, flags apagados y el blob de evaluar_d25.
  DESCARGA  (S168, P2-01; los cinco escenarios de probar_descarga_f4.py, contra el breaker REAL de pipeline/fetch.py)
            un ConnectTimeout con el host recuperado no pierde más que el gránulo de la caída; sin reset sí se pierden
            (control); con el host caído la parte se corta tras 3 gránulos con filas no_bajado escritas con flush y
            código de salida distinto de 0; una falla que no es de host corta la racha; el error del breaker no duerme.
MUTACIONES del arnés (copias del archivo con un cambio; cada una tiene que hacer fallar al menos una aserción y NINGÚN
escenario puede caer, VS-01; control de identidad VIVA, de caída CAE y de mutación rota ROTA; si un control no sale
como debe la batería escribe «NO VALE» y sale con código 1).

LO QUE ESTA BATERÍA NO PRUEBA (queda para el humo en el runner): la lectura real del HDF y del MxD03 con pyhdf, la
búsqueda y descarga por nombre contra CMR y LAADS, la re-corrida real en un codigo_sha (k_en_sha.py) y la cobertura de
la población real.
Uso: python probar_probe_f4.py [--sin-mutaciones]   (sale 1 si algo falla; necesita node)
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path
from unittest.mock import patch

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (RAIZ, RAIZ / "scripts", AQUI):
    sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import evaluar_f4 as E  # noqa: E402
import probar_descarga_f4 as D  # noqa: E402  (S168, P2-01: breaker real de fetch.py, reset por intento y tope)

L1B = "MYD021KM.A2026115.0735.061.2026115190927.hdf"
GEO = "MYD03.A2026115.0735.061.2026115184805.hdf"
PASADA = {"vol": "Lascar", "dt": "2026-04-25 07:35", "noche": "2026-04-25", "inner": 5, "clave": "MYD021KM.A2026115.0735",
          "l1b": L1B, "geo": GEO}
CONTRATO = ("vol", "dt", "sensor", "z", "estado", "motivo", "v_marca", "inner", "k_slim", "v_slim", "vcerc_slim",
            "vpico_slim", "store_descarto", "dist", "pub_runner", "k_difiere_de_guardado", "k_reproducida_en_su_sha")


# ------------------------------------------------------------------ escenas
def escena(A, tipo="dos_fuentes", desplazar_celdas=0, semilla=7):
    """Gránulo sintético de 81 x 81 píxeles de 1 km en los centros de la grilla de MIROVA de Láscar (griddata lineal
    los reproduce exactos), noche (cenit solar 130°). Devuelve (datos de read_modis_l1b, (lat, lon, ángulos) de
    leer_geo_mxd03, celda del cráter)."""
    from pyproj import Transformer
    MV, pm = A.MV, A.pm
    v = A_volcan(A)
    vent = A.get_detection_anchor(v)
    g = MV.grilla_del_volcan("Lascar", paso_m=1000.0, clave_roi="roi_modis")
    pos = MV.posicion_de(g, *vent)
    cr = (int(round(pos[0])), int(round(pos[1])))
    idx = np.arange(-15, 66)
    F, C = np.meshgrid(idx, idx + desplazar_celdas, indexing="ij")
    t = Transformer.from_crs(f"EPSG:{g['epsg']}", "EPSG:4326", always_xy=True)
    lon, lat = t.transform(g["ul_x"] + 1000.0 * (C + 0.5), g["ul_y"] - 1000.0 * (F + 0.5))
    rng = np.random.default_rng(semilla)
    bm = rng.normal(262.0, 0.4, F.shape)
    bt = rng.normal(261.0, 0.4, F.shape)

    def cel(f, c):
        return f + 15, c + 15
    if tipo == "dos_fuentes":
        bm[cel(cr[0], cr[1] - 1)] = 345.0                                        # el débil, junto al cráter
        for k, T in zip(range(3, 10), (480, 440, 420, 400, 380, 370, 360)):     # el radiante, desde ~3 km hacia el E
            bm[cel(cr[0], cr[1] + k)] = T
    elif tipo == "invalida":
        bt[:] = 190.0
    elif tipo not in ("nada", "fuera"):
        raise ValueError(tipo)
    datos = {"band21": pm.bt_to_radiance(bm, pm.BAND21_LAMBDA).astype(np.float32),
             "band22": pm.bt_to_radiance(bm, pm.BAND22_LAMBDA).astype(np.float32),
             "band31": pm.bt_to_radiance(bt, pm.BAND31_LAMBDA).astype(np.float32),
             "lat": lat.astype(np.float32), "lon": lon.astype(np.float32), "angles": {}}
    ang = {"sensor_zenith": np.full(F.shape, 20.0), "sensor_azimuth": np.full(F.shape, 100.0),
           "solar_zenith": np.full(F.shape, 130.0), "solar_azimuth": np.full(F.shape, 90.0)}
    return datos, (lat.astype(float), lon.astype(float), ang), cr


def A_volcan(A):
    import run_pipeline as rp
    return rp.load_volcanoes("Lascar")[0]


class Lectores:
    """Reemplaza SÓLO las lecturas de archivo (pyhdf no corre en Windows); todo lo demás es el pipeline real."""

    def __init__(self, A, datos, geo):
        self.p = [patch.object(A.pm, "read_modis_l1b", lambda _p: A.P._copia(datos)),
                  patch.object(A.MV, "leer_geo_mxd03", lambda _p: (geo[0].copy(), geo[1].copy(), geo[2]))]

    def __enter__(self):
        for x in self.p:
            x.start()

    def __exit__(self, *a):
        for x in reversed(self.p):
            x.stop()


def espia_recorrer(resultado):
    llamadas = []

    def f(sha, l1b, geo, vol, guardado, pub_de, inner, arboles):
        llamadas.append({"sha": sha, "vol": vol, "l1b": str(l1b)})
        return dict(resultado)
    return f, llamadas


def medir(A, tipo="dos_fuentes", guardado="real", recorrer_res=None, extra=(), **kw):
    """medir_pasada sobre una escena; guardado: "real" (data/ del checkout) o un record (o None)."""
    datos, geo, _cr = escena(A, tipo, **kw)
    v = A_volcan(A)
    rec, llam = espia_recorrer(recorrer_res or {"estado": "reproduce", "reproduce": True})
    parches = list(extra)
    if guardado != "real":
        parches.append(patch.object(A, "registro_guardado", lambda *_a, **_k: copy.deepcopy(guardado)))
    with tempfile.TemporaryDirectory() as out, Lectores(A, datos, geo):
        for x in parches:
            x.start()
        try:
            fila = A.medir_pasada(dict(PASADA), v, None, L1B, GEO, datos, Path(out), Path(out) / "arb", recorrer=rec)
            npz = None
            if fila.get("grilla_npz"):
                with np.load(Path(out) / fila["grilla_npz"]) as z:
                    npz = {k: z[k] for k in z.files}
        finally:
            for x in reversed(parches):
                x.stop()
    return fila, npz, llam


def evaluar_fila(fila):
    """La fila pasada por evaluable y por la tabla del evaluador (predicado con node sobre los slim)."""
    f = json.loads(json.dumps(fila, default=float))
    f["_evaluable"], f["_motivo"] = E.evaluable(f)
    if f["_evaluable"]:
        E.armar_tabla([f], E.predicado_node)
    return f


_CACHE = {}


def escena_principal(A):
    if id(A) not in _CACHE:
        _CACHE[id(A)] = medir(A)
    return _CACHE[id(A)]


# ------------------------------------------------------------------ escenarios
def t_escena_contrato(A):
    fila, _npz, _l = escena_principal(A)
    assert fila["estado"] == "ok", fila.get("error")
    faltan = [k for k in CONTRATO if k not in fila]
    assert not faltan, f"faltan campos del contrato: {faltan}"
    assert fila["v_marca"] is True and fila["motivo"] is None
    assert isinstance(fila["k_difiere_de_guardado"], bool)
    assert set(fila["pub_runner"]) >= {"K"} and fila["pub_runner"]["K"] in (0, 1)
    assert set(fila["store_descarto"]) == set(E.BRAZOS_V)
    assert fila["noche"] == PASADA["noche"] and fila["inner"] == 5 and fila["sensor"] == "MODIS_AQUA"
    assert fila["z_fuente"] == "mxd03_crater" and abs(fila["z"] - 20.0) < 1e-9
    # cargar del evaluador, tal cual lo lee la lectura
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sub" / "f4_parte00.jsonl"
        p.parent.mkdir()
        p.write_text(json.dumps({"tipo": "cabecera", "parte": 0}) + "\n" + json.dumps(fila, default=float) + "\n" +
                     json.dumps({"tipo": "pie"}) + "\n", encoding="utf-8")
        filas, cab = E.cargar(d)
    assert len(filas) == 1 and len(cab) == 1
    assert E.evaluable(filas[0]) == (True, None), E.evaluable(filas[0])


def t_escena_tres_distancias(A):
    fila, _npz, _l = escena_principal(A)
    d = fila.get("dist")
    assert isinstance(d, dict) and set(d) == {"radiante", "cercano", "pico"}, d
    for c in ("v_slim", "vcerc_slim", "vpico_slim"):
        assert isinstance((fila.get(c) or {}).get("primary_cluster"), dict), f"{c} sin primary_cluster"
    assert len({round(x, 6) for x in d.values()}) == 3, d
    assert d["cercano"] < d["pico"] < d["radiante"], d
    clases = {k: E.clase_dc(x, 5) for k, x in d.items()}
    assert clases == {"radiante": "far", "cercano": "summit", "pico": "summit"}, clases
    assert fila["v_slim"]["distance_class"] == "far"
    assert fila["vcerc_slim"]["distance_class"] == "summit" and fila["vpico_slim"]["distance_class"] == "summit"
    assert abs(fila["vcerc_slim"]["primary_cluster"]["centroid_dist_km"] - round(d["cercano"], 3)) < 1e-9
    assert abs(fila["vpico_slim"]["primary_cluster"]["centroid_dist_km"] - round(d["pico"], 3)) < 1e-9
    assert fila["pub_runner"]["V"] == 0 and fila["pub_runner"]["V-cercano"] == 1 and fila["pub_runner"]["V-pico"] == 1


def t_escena_controles_del_evaluador(A):
    """§8.9a con control_posicion; §8.3 con control_marca; §8.1 con control_k_produccion; y el predicado del evaluador
    sobre los slim igual al del runner sobre los records completos en los cuatro brazos."""
    fila, _npz, _l = escena_principal(A)
    f = evaluar_fila(fila)
    assert f["_evaluable"]
    cp = E.control_posicion([f])
    assert cp["estado"] == "OK" and cp["n_con_alertados"] == 1, cp
    assert E.control_marca([f])["estado"] == "OK"
    ck = E.control_k_produccion([f])
    assert ck["estado"] == "OK", ck
    for b in ("K", "V", "V-cercano", "V-pico"):
        assert f["_t"][b]["pub"] == fila["pub_runner"][b], (b, f["_t"][b], fila["pub_runner"])


def t_escena_grilla_npz(A):
    """La grilla guardada re-corrida con procesar_grilla da el mismo record de la vía (mismas alertadas, mismo VRP,
    misma distancia): identidad_f4.py puede usarla."""
    fila, npz, _l = escena_principal(A)
    assert npz is not None and fila["grilla_npz"].startswith("grillas/grilla_Lascar_202604250735")
    assert int(npz["mascara"].sum()) == fila["n_alertadas"] == 8
    g = {"epsg": int(npz["epsg"]), "ul_x": float(npz["ul_x"]), "ul_y": float(npz["ul_y"]), "paso": float(npz["paso"]),
         "n": int(npz["n"])}
    r = A.MV.procesar_grilla(npz["mir"], npz["tir"], g, npz["box"], int(npz["dayflag"]), float(npz["sunglint"]),
                             tuple(npz["pos_crater"]), float(npz["inner_km"]), "MODIS_AQUA", familia="MODIS")
    assert r["vrp_mw"] == float(npz["vrp_mw"])
    assert sorted((p["fila"], p["col"]) for p in r["anomaly_pixels"]) == A.celdas_de(npz["mascara"])
    assert isinstance((fila.get("v_slim") or {}).get("primary_cluster"), dict), "v_slim sin primary_cluster"
    assert r["primary_cluster"]["centroid_dist_km"] == fila["v_slim"]["primary_cluster"]["centroid_dist_km"]
    assert fila["captura"]["pos_crater_es_el_ancla"] is True


def t_envoltorio_no_altera(A):
    """V con la captura y V sin ella dan el mismo record (A75: el envoltorio es de sólo lectura)."""
    datos, geo, _ = escena(A)
    v = A_volcan(A)
    with Lectores(A, datos, geo):
        r1, cap = A.correr_v(L1B, GEO, v)
        with patch.object(A.pm, "ENABLE_MODIS_CODIGO_MIROVA", True):
            r2 = A.pm.calculate_vrp(Path(L1B), Path(GEO), v["lat"], v["lon"], v["radius_km"],
                                    **A.P.argumentos_calculate_vrp(v))
    assert len(cap.grilla) == 1 and len(cap.granulo) == 1 and len(cap.deteccion) == 1
    assert json.dumps(r1, sort_keys=True, default=float) == json.dumps(r2, sort_keys=True, default=float)


def t_fuera(A):
    fila, npz, _l = medir(A, "fuera", desplazar_celdas=80)
    assert fila["estado"] == "ok", fila.get("error")
    assert fila["motivo"] == "volcan_fuera_del_granulo" and fila["v_marca"] is True, (fila["motivo"], fila["v_marca"])
    assert npz is None and fila["grilla_npz"] is None and fila["dist"] is None
    assert "K" in fila["pub_runner"] and fila["captura"]["devolvio_none"] is True
    assert E.evaluable(fila) == (False, "volcan_fuera_del_granulo")


def t_invalida(A):
    fila, npz, _l = medir(A, "invalida")
    assert fila["estado"] == "ok", fila.get("error")
    assert fila["motivo"] == "escena_invalida" and fila["v_marca"] is True, (fila["motivo"], fila["v_marca"])
    assert npz is not None and fila["n_alertadas"] == 0
    assert E.evaluable(fila) == (False, "escena_invalida")


def t_nada(A):
    fila, _npz, _l = medir(A, "nada")
    assert fila["estado"] == "ok" and fila["v_marca"] is True and fila["motivo"] is None
    assert fila["dist"] is None and fila["n_alertadas"] == 0
    assert (fila["v_slim"] or {}).get("primary_cluster") is None
    assert fila["pub_runner"]["V"] == 0
    f = evaluar_fila(fila)
    assert f["_evaluable"] and E.control_marca([f])["estado"] == "OK"


def t_sin_grilla(A):
    fila, _npz, _l = medir(A, "nada", extra=[patch.object(A.MV, "grilla_del_volcan", lambda *a, **k: None)])
    assert fila["estado"] == "ok" and fila["v_marca"] == "sin_grilla", fila.get("v_marca")
    assert E.evaluable(fila) == (False, "falla_via_sin_grilla")


def _rk(A):
    datos, geo, _ = escena(A)
    with Lectores(A, datos, geo):
        return A.correr_k(L1B, GEO, A_volcan(A), None, datos)


def t_kprod_igual(A):
    rk = _rk(A)
    fila, _npz, llam = medir(A, guardado=rk)
    assert fila["k_difiere_de_guardado"] is False and fila["k_reproducida_en_su_sha"] is None and not llam


def t_kprod_distinto(A):
    rk = _rk(A) or {}
    otro = copy.deepcopy(rk)
    otro["primary_cluster"] = dict(otro.get("primary_cluster") or {}, vrp_mw=((otro.get("primary_cluster") or {})
                                                                               .get("vrp_mw") or 0) + 0.5)
    otro["regimen"] = {"codigo_sha": "a" * 40}
    for res, esperado in (({"estado": "reproduce", "reproduce": True}, True),
                          ({"estado": "no_reproduce", "reproduce": False}, False)):
        fila, _npz, llam = medir(A, guardado=otro, recorrer_res=res)
        assert fila["k_difiere_de_guardado"] is True
        assert len(llam) == 1 and llam[0]["sha"] == "a" * 40 and llam[0]["vol"] == "Lascar", llam
        assert fila["k_reproducida_en_su_sha"] is esperado and fila["k_sha"]["estado"] == res["estado"]
        f = evaluar_fila(fila)
        assert (E.control_k_produccion([f])["estado"] == "OK") is esperado


def t_bajar(A):
    with tempfile.TemporaryDirectory() as d:
        catalogo = {"exacto": [L1B], "patron": ["MYD021KM.A2026115.0735.061.2099999999999.hdf"]}

        def buscar_con(exacto, patron, falla=None):
            def buscar(short_name, version, granule_name):
                if falla and falla.pop():
                    raise ConnectionError("CMR caído")
                assert short_name == "MYD021KM"
                if granule_name.endswith("*"):
                    assert granule_name == "MYD021KM.A2026115.0735*" and version == "6.1"
                    return list(patron)
                assert granule_name == L1B and version == "6.1"
                return list(exacto)
            return buscar

        def descargar(res, dest):
            dest.mkdir(parents=True, exist_ok=True)
            out = []
            for n in res:
                (dest / n).write_bytes(b"x")
                out.append(dest / n)
            return out
        p, otro = A.bajar_por_nombre(L1B, Path(d), buscar_con(catalogo["exacto"], catalogo["patron"]), descargar)
        assert p.name == L1B and otro is False
        p, otro = A.bajar_por_nombre(L1B, Path(d), buscar_con([], catalogo["patron"]), descargar)
        assert p.name != L1B and otro is True
        p, otro = A.bajar_por_nombre(L1B, Path(d), buscar_con([], []), descargar)
        assert p is None and otro is None
        p, otro = A.bajar_por_nombre(L1B, Path(d), buscar_con([L1B], [], falla=[True]), descargar, espera=0)
        assert p.name == L1B and otro is False


def t_partes(A):
    pas = [{"vol": v, "dt": f"2026-03-0{i} 0{h}:00", "clave": f"MOD021KM.A202606{i}.0{h}00"}
           for i in range(1, 6) for h in range(1, 4) for v in ("Lascar", "Isluga")]
    claves = sorted({p["clave"] for p in pas})
    pob = {"pasadas": pas, "partes": [claves[0::3], claves[1::3], claves[2::3]]}
    vistas = []
    for i in range(3):
        g = A.pasadas_de_la_parte(pob, i, 3)
        assert set(g) == set(pob["partes"][i])
        vistas += [(p["vol"], p["dt"]) for v in g.values() for p in v]
    assert sorted(vistas) == sorted((p["vol"], p["dt"]) for p in pas) and len(vistas) == len(set(vistas))
    try:
        A.pasadas_de_la_parte(pob, 0, 24)
        raise AssertionError("--de distinto de las partes de la población no falló")
    except Exception as e:  # noqa: BLE001
        assert isinstance(e, ValueError), repr(e)
    try:
        A.pasadas_de_la_parte(pob, 0, 3, humo=[("Lascar", "2026-03-01 01:00"), ("Lascar", "1999-01-01 00:00")])
        raise AssertionError("un humo con una pasada fuera de la población no falló")
    except Exception as e:  # noqa: BLE001
        assert isinstance(e, ValueError), repr(e)
    sin = A.pasadas_de_la_parte({"pasadas": pas}, 1, 2)
    assert set(sin) == set(claves[1::2])


def t_humo(A):
    h = A.leer_humo(AQUI / "humo_f4.txt")
    assert len(h) == 25 and len(set(h)) == 25, len(h)
    assert ("Lascar", "2026-04-25 07:35") in h and ("NevadosDeChillan", "2026-10-25 07:20") in h


def t_data(A):
    r = A.registro_guardado("Lascar", "2026-04-25 07:35", "MODIS_AQUA", raiz=RAIZ)
    assert r is not None and r.get("primary_cluster") and r["datetime_utc"] == "2026-04-25 07:35"
    assert A.registro_guardado("Lascar", "1999-01-01 00:00", "MODIS_AQUA", raiz=RAIZ) is None


def t_arbol(A):
    import subprocess
    sha = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory() as d:
        t = A.extraer_arbol(sha, d, raiz=RAIZ)
        assert (t / "pipeline/process_modis.py").exists() and (t / "scripts/run_pipeline.py").exists()
        assert (t / "volcanoes.yaml").exists()
        assert not (t / "data").exists() and not (t / "experiments").exists() and not (t / "frontend").exists()


def t_cabecera(A):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "pob.json"
        p.write_text(json.dumps({"pasadas": []}), encoding="utf-8")
        c = A.cabecera(3, 24, "completo", 10, 2, p)
    assert c["tipo"] == "cabecera" and c["parte"] == 3 and c["de"] == 24 and c["modo"] == "completo"
    assert c["commit"] and c["sha256_frontend_index"] == A.sha256_lf(RAIZ / "frontend/index.html")
    assert c["sha256_poblacion"] and c["blob_evaluar_d25"] == E.D25_BLOB
    assert all(c["flags"][f] is False for f in A.FLAGS_APAGADOS), c["flags"]


def t_motivo_y_marca(A):
    assert A.motivo_y_marca(None, {"n_granulo": 1, "devolvio_none": True}) == ("volcan_fuera_del_granulo", True)
    assert A.motivo_y_marca(None, {"n_granulo": 0}) == (None, "sin_record_ni_via")
    assert A.motivo_y_marca({"via_codigo_mirova": "sin_mxd03"}, {}) == (None, "sin_mxd03")
    assert A.motivo_y_marca({"via_codigo_mirova": True, "diag_codigo_mirova": {"motivo_vacio": "sunglint"}}, {}) == \
        (None, True)
    assert A.motivo_y_marca({}, {}) == (None, "sin_marca")


def t_descarga_m01b(A):
    D.t_m01b(A)


def t_descarga_control(A):
    D.t_m01b_control(A)


def t_descarga_tope(A):
    D.t_tope(A)


def t_descarga_cadena(A):
    D.t_cadena(A)


def t_descarga_breaker(A):
    D.t_breaker(A)


ESCENARIOS = [t_escena_contrato, t_escena_tres_distancias, t_escena_controles_del_evaluador, t_escena_grilla_npz,
              t_envoltorio_no_altera, t_fuera, t_invalida, t_nada, t_sin_grilla, t_kprod_igual, t_kprod_distinto,
              t_bajar, t_partes, t_humo, t_data, t_arbol, t_cabecera, t_motivo_y_marca,
              t_descarga_m01b, t_descarga_control, t_descarga_tope, t_descarga_cadena, t_descarga_breaker]


def correr(A, verbose=True):
    _CACHE.clear()      # id() se reutiliza entre copias mutadas: la escena se recalcula para cada módulo
    res = {}
    for t in ESCENARIOS:
        t0 = time.time()
        try:
            t(A)
            res[t.__name__] = ("OK", "")
        except AssertionError as e:
            res[t.__name__] = ("FALLA", str(e)[:300])
        except Exception as e:  # noqa: BLE001
            res[t.__name__] = ("CAE", f"{type(e).__name__}: {e}"[:300] + " | " + traceback.format_exc()[-400:])
        if verbose:
            print(f"  {res[t.__name__][0]:5s} {t.__name__:34s} {time.time() - t0:5.1f} s  {res[t.__name__][1]}",
                  flush=True)
    return res


# ------------------------------------------------------------------ mutaciones del arnés
MUTACIONES = [
    ("MA01 V-cercano y V-pico con la regla radiante",
     "variantes[b] = E.variante_posicion(rv, E.REGLA_DE[b], dist, inner)",
     "variantes[b] = E.variante_posicion(rv, \"radiante\", dist, inner)"),
    ("MA02 V sin el flag de la vía encendido",
     'with patch.object(pm, "ENABLE_MODIS_CODIGO_MIROVA", True), cap:',
     'with patch.object(pm, "ENABLE_MODIS_CODIGO_MIROVA", False), cap:'),
    ("MA03 escena inválida no se reconoce",
     '.get("motivo_vacio") == "escena_invalida":', '.get("motivo_vacio") == "escena_invalidaX":'),
    ("MA04 k_difiere siempre False",
     "return bool(PB.difiere_de_guardado(", "return False and bool(PB.difiere_de_guardado("),
    ("MA05 el vigente no se marca otro_granulo",
     "return Path(ps[0]), Path(ps[0]).name != nombre", "return Path(ps[0]), False"),
    ("MA06 el slim pierde primary_cluster",
     'if k != "anomaly_pixels"}\n    s["anomaly_pixels"]', 'if k not in ("anomaly_pixels", "primary_cluster")}\n'
                                                            '    s["anomaly_pixels"]'),
    ("MA07 distancias medidas desde la esquina de la grilla, no desde el cráter",
     'ent["pos_crater"], paso_km, MV._cumulo', '(0.0, 0.0), paso_km, MV._cumulo'),
    ("MA08 volcán fuera del gránulo sin motivo",
     'return "volcan_fuera_del_granulo", True', 'return None, True'),
    ("MA09 k_reproducida siempre True",
     'fila["k_reproducida_en_su_sha"] = bool(r.get("reproduce"))', 'fila["k_reproducida_en_su_sha"] = True'),
    ("MA10 todas las partes son la parte 0",
     'claves = set(pob["partes"][parte])', 'claves = set(pob["partes"][0])'),
    ("MA11 el humo no comprueba la población",
     "        if faltan:\n            raise ValueError", "        if False:\n            raise ValueError"),
    ("MA12 pub_runner de K sale del primer brazo de V",
     '"pub_runner": {"K": int(pub_k),', '"pub_runner": {"K": int(pubs[1]),'),
    ("MA13 la re-corrida usa el sha del arnés, no el del guardado",
     'sha = (fila["k_guardado"] or {}).get("codigo_sha")', 'sha = "b" * 40'),
    ("MA14 el npz no guarda la máscara",
     "        mascara[f, c] = True\n", "        pass\n"),
    ("MA15 git archive sin ruta",
     '"archive", "--format=tar", sha, "--", "pipeline", "scripts",\n                        "volcanoes.yaml"]',
     '"archive", "--format=tar", sha]'),
    ("MA16 el cenit sale del record de K aunque haya MxD03",
     'z = diag.get("z_crater")', 'z = None'),
    # S168, P2-01: la descarga
    ("MA17 sin reset del breaker antes de la descarga del pedido",
     "                reset()\n                ps = descargar(res[:1], Path(dest))\n                if ps and",
     "                ps = descargar(res[:1], Path(dest))\n                if ps and"),
    ("MA18 sin tope de caídas de host",
     "                if seguidas >= tope:\n", "                if False:\n"),
    ("MA19 duerme también con el error del breaker",
     "            if not es_error_del_breaker(e):\n                time.sleep",
     "            if True:\n                time.sleep"),
    ("MA20 las filas no se escriben con flush",
     "        salida.flush()\n", "        pass\n"),
]
CONTROL_IDENTIDAD = ("CONTROL identidad (sin mutación)", None, None)
CONTROL_CAIDA = ("CONTROL caída", '    publica = publica or P.publica\n',
                 '    raise RuntimeError("caída inyectada")\n')
CONTROL_ROTA = ("CONTROL rota", "def medir_pasada(", "def medir_pasada((")


def cargar_copia(texto, d):
    p = Path(d) / "probe_f4.py"
    p.write_text(texto, encoding="utf-8")
    nombre = "probe_f4_mut_%d" % abs(hash(texto))
    spec = importlib.util.spec_from_file_location(nombre, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def medir_mutacion(nombre, viejo, nuevo, original):
    if viejo is not None and viejo not in original:
        return "NO APLICA", {}
    texto = original if viejo is None else original.replace(viejo, nuevo, 1)
    with tempfile.TemporaryDirectory() as d:
        try:
            mod = cargar_copia(texto, d)
        except Exception:  # noqa: BLE001
            return "ROTA", {}
        res = correr(mod, verbose=False)
    fallan = [k for k, v in res.items() if v[0] == "FALLA"]
    caen = [k for k, v in res.items() if v[0] == "CAE"]
    if caen and not fallan:
        return "CAE", res
    if caen:
        return "CON CAÍDAS", res        # VS-01: no se cuenta como atrapada si algún escenario cae
    return ("ATRAPADA" if fallan else "VIVA"), res


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-mutaciones", action="store_true")
    a = ap.parse_args()
    import probe_f4 as A
    print("batería del arnés probe_f4.py (sha256 LF %s)" % A.sha256_lf(AQUI / "probe_f4.py"))
    res = correr(A)
    ok = all(v[0] == "OK" for v in res.values())
    print(f"escenarios: {sum(v[0] == 'OK' for v in res.values())} de {len(res)} OK")
    if a.sin_mutaciones:
        sys.exit(0 if ok else 1)
    os.environ["F4_RAIZ"] = str(RAIZ)
    original = (AQUI / "probe_f4.py").read_text(encoding="utf-8")
    print("\nmutaciones del arnés (cada una contra la batería entera; ATRAPADA = al menos una aserción falla y ningún "
          "escenario cae)")
    cuenta = {}
    for nombre, viejo, nuevo in MUTACIONES:
        est, r = medir_mutacion(nombre, viejo, nuevo, original)
        cuenta[est] = cuenta.get(est, 0) + 1
        fallan = [k for k, v in r.items() if v[0] == "FALLA"]
        caen = [k for k, v in r.items() if v[0] == "CAE"]
        print(f"  {est:10s} {nombre} | fallan: {','.join(fallan) or '-'} | caen: {','.join(caen) or '-'}", flush=True)
    controles = {}
    for (nombre, viejo, nuevo), debe in ((CONTROL_IDENTIDAD, "VIVA"), (CONTROL_CAIDA, "CAE"), (CONTROL_ROTA, "ROTA")):
        est, r = medir_mutacion(nombre, viejo, nuevo, original)
        controles[nombre] = (est, debe)
        caen = [k for k, v in r.items() if v[0] == "CAE"]
        print(f"  {est:10s} {nombre} (debe {debe}) | caen: {len(caen)}")
    n = len(MUTACIONES)
    print(f"mutaciones: {cuenta.get('ATRAPADA', 0)} de {n} atrapadas por aserción sin caídas | "
          f"{', '.join(f'{k} {v}' for k, v in sorted(cuenta.items()))}")
    vale = all(e == d for e, d in controles.values())
    if not vale:
        print("NO VALE: algún control del medidor no salió como debe")
    sys.exit(0 if ok and vale and cuenta.get("ATRAPADA", 0) == n else 1)


if __name__ == "__main__":
    main()
