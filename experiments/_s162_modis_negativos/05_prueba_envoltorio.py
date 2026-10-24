# -*- coding: utf-8 -*-
"""S162 MODIS: prueba SIN RED y sin HDF del envoltorio del recorte nativo (envoltorio_nativo.py).

Que demuestra:
  1. IDENTIDAD: con y sin envoltorio, probe_portes.procesar da el mismo resultado del port en las 5 variantes
     (npix, VRP, pixeles, umbrales: el JSON entero) y la misma grilla guardada. El port tiene que encender
     (npix > 0 en la caja fisica), si no la identidad seria trivial.
  2. INDICES: el recorte guardado coincide pixel a pixel con el granulo sintetico completo leido en (linea, frame)
     para las 7 capas (b21, b22, b31, lat y lon de 5 km, lat y lon del MxD03), las lineas y frames son contiguos y
     empiezan donde dicen las rebanadas, y el pixel caliente del volcan esta dentro.
  3. TRANSPARENCIA para K: read_modis_l1b fuera de leer_modis devuelve el mismo objeto y no anota nada.
  4. MUTACIONES: seis defectos plausibles del envoltorio; cada uno tiene que caer por ASERCION de esta prueba (no por
     una excepcion cualquiera, S156). Si alguno pasa, la prueba falla.

El granulo sintetico: 300 lineas x 280 frames de 1 km, rotado 10 grados (la orbita no va al norte), volcan en
(linea 170, frame 100) para que el recorte no empiece en 0; fondo 265 K con ruido, foco x3 en MIR a < 0,7 km del
punto de referencia de MIROVA, B22 saturada (NaN) en un pixel del foco para que actue merge_mir_bands. No simula el
bow tie: lo que se prueba es que los indices guardados identifican el pixel del granulo.

Uso: python -I 05_prueba_envoltorio.py   (con VRP_S159_PORTES apuntando a experiments/_s159/portes del commit base
     si no se corre en un checkout que lo tenga)
"""
from __future__ import annotations

import copy
import io
import json
import os
import sys
import tempfile
import time
import types
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

L, F, L0, F0, ROT = 300, 280, 170, 100, np.radians(10.0)


# ---------------------------------------------------------------- pyhdf falso (antes de importar nada del pipeline)
class _DS:
    def __init__(self, a, attrs):
        self.a, self.at = a, attrs

    def get(self):
        return self.a.copy()

    def attributes(self):
        return dict(self.at)

    def endaccess(self):
        pass


GEO = {}


class _SD:
    def __init__(self, path, mode):
        self.path = path

    def select(self, nombre):
        return GEO[nombre]

    def end(self):
        pass


_m = types.ModuleType("pyhdf")
_ms = types.ModuleType("pyhdf.SD")
_ms.SD, _ms.SDC = _SD, types.SimpleNamespace(READ=1)
_m.SD = _ms
sys.modules["pyhdf"], sys.modules["pyhdf.SD"] = _m, _ms

import envoltorio_nativo as E  # noqa: E402
import pipeline.process_modis as PM  # noqa: E402

P, MP, ORA = E.P, E.P.MP, E.P.ORA


def granulo(g):
    from pyproj import Transformer
    rng = np.random.default_rng(7)
    ll, ff = np.meshgrid(np.arange(L), np.arange(F), indexing="ij")
    du, dv = (ff - F0) * 1000.0, (ll - L0) * 1000.0
    x = g["X0"] + du * np.cos(ROT) + dv * np.sin(ROT)
    y = g["Y0"] - dv * np.cos(ROT) + du * np.sin(ROT)
    t = Transformer.from_crs(f"EPSG:{g['epsg']}", "EPSG:4326", always_xy=True)
    lon, lat = t.transform(x, y)
    lat, lon = np.asarray(lat, np.float32), np.asarray(lon, np.float32)
    cfg = MP.SENSORES["MODIS"]
    T = 265 + rng.normal(0, 0.4, (L, F))
    b31 = ORA.temperatura_a_radiancia(T, cfg["lam_tir"]).astype(np.float32)
    mir = ORA.temperatura_a_radiancia(T - 3, cfg["lam_mir"])
    foco = np.hypot(x - g["X0"], y - g["Y0"]) < 700
    mir[foco] *= 3.0
    b22 = mir.astype(np.float32)
    b21 = (mir * (1 + rng.normal(0, 1e-3, (L, F)))).astype(np.float32)
    b22[L0, F0] = np.nan                      # B22 saturada en el pixel del volcan: entra B21 (D21)
    full = {"band21": b21, "band22": b22, "band31": b31, "lat": lat + np.float32(0.004),
            "lon": lon - np.float32(0.003), "angles": {}}
    geo = {"Latitude": _DS(lat, {}), "Longitude": _DS(lon, {}),
           # angulos que varian con linea y frame (un campo constante no ve un indice corrido ni un intercambio,
           # verificador VCD-08)
           "SensorZenith": _DS((1500 + 3 * np.arange(L)[:, None] + 7 * np.arange(F)[None, :]).astype(np.int16),
                               {"scale_factor": 0.01}),
           "SensorAzimuth": _DS((8000 - 5 * np.arange(L)[:, None] + 2 * np.arange(F)[None, :]).astype(np.int16),
                                {"scale_factor": 0.01}),
           "SolarZenith": _DS(np.full((L, F), 12000, np.int16), {"scale_factor": 0.01}),
           "SolarAzimuth": _DS(np.full((L, F), -9000, np.int16), {"scale_factor": 0.01})}
    return full, geo, int(foco.sum())


def preparar():
    obj = json.loads((AQUI / "objetivos_neg_resto_modis.json").read_text(encoding="utf-8"))
    o = copy.deepcopy(next(x for x in obj if x["volcan"] == "Lascar" and x["clase"] == "neg_resto"))
    full, geo, nfoco = granulo(o["grilla"])
    GEO.clear()
    GEO.update(geo)
    PM.read_modis_l1b = lambda path: full     # el L1B "leido": siempre el mismo objeto

    def bajar_par(granule, lat, lon, destino):
        destino.mkdir(parents=True, exist_ok=True)
        a, b = destino / "MOD021KM.A2026100.0300.061.sint.hdf", destino / "MOD03.A2026100.0300.061.sint.hdf"
        a.write_bytes(b"x")
        b.write_bytes(b"x")
        return (a, b), None

    P.bajar_par = bajar_par
    return o, full, geo, nfoco


def cargar(f):
    """np.load sin dejar el archivo abierto (en Windows impide borrar el temporal)."""
    with np.load(f) as z:
        return {k: z[k] for k in z.files}


def correr(o, base, nombre):
    out = base / nombre
    out.mkdir()
    r = P.procesar(copy.deepcopy(o), base / "granulos", out, sin_k=True)
    return r, out


def comprobar(r0, out0, r1, out1, o, full, geo):
    """Todas las aserciones. Devuelve un resumen; lanza AssertionError con un mensaje si algo falla."""
    assert r0["estado"] == "ok" and r1["estado"] == "ok", f"estados {r0['estado']} / {r1['estado']}"
    assert r0["port"]["fisica"]["npix"] > 0, "el port no enciende: la identidad seria trivial"
    j0 = json.dumps(r0["port"], sort_keys=True, default=float)
    j1 = json.dumps(r1["port"], sort_keys=True, default=float)
    assert j0 == j1, "IDENTIDAD: el envoltorio cambia el resultado del port"
    for k in ("geometria_centro", "saturados", "dayflag", "sunglint", "archivos"):
        assert r0.get(k) == r1.get(k), f"IDENTIDAD: cambia {k}"
    g0 = cargar(out0 / f"grilla_{o['id']:03d}.npz")
    g1 = cargar(out1 / f"grilla_{o['id']:03d}.npz")
    assert sorted(g0) == sorted(g1)
    for k in g0:
        assert np.array_equal(g0[k], g1[k], equal_nan=True), f"IDENTIDAD: la grilla guardada cambia en {k}"
    nv = r1.get("nativo") or {}
    assert nv.get("guardado"), f"no se guardo el recorte: {nv.get('motivo')}"
    z = cargar(out1 / nv["archivo"])
    ra, rb, ca, cb = (int(v) for v in z["rebanadas"])
    assert [ra, rb, ca, cb] == nv["rebanadas"] and ra > 0 and ca > 0, "rebanadas inconsistentes o triviales"
    lin, fra = z["linea"], z["frame"]
    assert lin.shape == (rb - ra, cb - ca) == fra.shape == z["b22"].shape, "formas distintas"
    assert np.array_equal(lin[:, 0], np.arange(ra, rb)) and np.all(lin == lin[:, :1]), "INDICES: linea"
    assert np.array_equal(fra[0, :], np.arange(ca, cb)) and np.all(fra == fra[:1, :]), "INDICES: frame"
    assert tuple(z["forma_granulo"]) == (L, F), "forma del granulo"
    lat3 = geo["Latitude"].a.astype(np.float64)
    lon3 = geo["Longitude"].a.astype(np.float64)
    pares = (("b21", full["band21"]), ("b22", full["band22"]), ("b31", full["band31"]), ("lat_5km", full["lat"]),
             ("lon_5km", full["lon"]), ("lat_mxd03", lat3), ("lon_mxd03", lon3))
    for k, A in pares:
        assert np.array_equal(z[k], A[lin, fra], equal_nan=True), f"INDICES: {k} no es el pixel (linea, frame)"
    for k, nm in (("sensor_zenith", "SensorZenith"), ("sensor_azimuth", "SensorAzimuth")):     # VCD-08
        A = (geo[nm].a.astype(np.float64) * 0.01).astype(np.float32)
        assert np.allclose(z[k], A[lin, fra], atol=1e-4), f"ANGULOS: {k} no es el del pixel (linea, frame)"
    assert ra <= L0 < rb and ca <= F0 < cb, "el pixel del volcan no esta en el recorte"
    i, j = L0 - ra, F0 - ca
    assert np.isnan(z["b22"][i, j]) and np.isfinite(z["b21"][i, j]), "el pixel saturado no esta donde dice"
    return {"forma": nv["forma"], "bytes": nv["bytes"], "segundos_guardar": nv["segundos_guardar"],
            "npix_fisica": r1["port"]["fisica"]["npix"], "vrp_fisica": r1["port"]["fisica"]["vrp_mw"]}


def main():
    o, full, geo, nfoco = preparar()
    print(f"granulo sintetico {L} x {F}, volcan en (linea {L0}, frame {F0}), foco de {nfoco} pixeles; objetivo "
          f"{o['id']} {o['volcan']} {o['hora_utc']}")
    fallas = []
    with tempfile.TemporaryDirectory(prefix="s162_env_") as td:
        base = Path(td)
        r0, out0 = correr(o, base, "sin_envoltorio")
        E.instalar()
        try:
            # 3. transparencia para K: fuera de leer_modis la envoltura no anota nada
            d = PM.read_modis_l1b("cualquiera")
            assert d is full and E._CTX["d"] is None and E._CTX["w"] is None, "read_modis_l1b no es transparente"
            r1, out1 = correr(o, base, "con_envoltorio")
            res = comprobar(r0, out0, r1, out1, o, full, geo)
            npx = res["forma"][0] * res["forma"][1]
            print("CONTROL (sin mutacion): PASA |", res, f"| {res['bytes'] / npx:.1f} bytes por pixel comprimido "
                  f"({npx} pixeles)")
            print("  port fisica sin envoltorio: npix", r0["port"]["fisica"]["npix"], "vrp", r0["port"]["fisica"]["vrp_mw"])
            z = cargar(out1 / r1["nativo"]["archivo"])
            crudo = sum(v.nbytes for v in z.values())
            print(f"  bytes sin comprimir del recorte: {crudo} ({crudo / npx:.1f} por pixel); capas y tipos:",
                  {k: str(v.dtype) for k, v in z.items()})
            print("\nMUTACIONES (cada una tiene que caer por asercion de esta prueba):")
            for m in ("linea_mas_uno", "frame_al_reves", "b21_como_b22", "lat5_como_mxd03", "altera_recorte",
                      "recorte_corrido", "angulos_intercambiados", "cenit_corrido"):
                E._MUTACION = m
                try:
                    rm, outm = correr(o, base, f"mut_{m}")
                    comprobar(r0, out0, rm, outm, o, full, geo)
                    print(f"  {m:<16} NO ATRAPADA")
                    fallas.append(m)
                except AssertionError as e:
                    print(f"  {m:<16} atrapada por asercion: {e}")
                except Exception as e:  # noqa: BLE001
                    print(f"  {m:<16} CAE sin asercion ({type(e).__name__}: {e}): no cuenta como atrapada")
                    fallas.append(m)
                finally:
                    E._MUTACION = ""
        finally:
            E.desinstalar()
    if fallas:
        print("PRUEBA FALLA: mutaciones no atrapadas por asercion:", fallas)
        return 1
    print("PRUEBA OK: identidad, indices, angulos, transparencia y 8 de 8 mutaciones atrapadas por asercion")
    return 0


if __name__ == "__main__":
    t0 = time.time()
    rc = main()
    print(f"({time.time() - t0:.1f} s)")
    sys.exit(rc)
