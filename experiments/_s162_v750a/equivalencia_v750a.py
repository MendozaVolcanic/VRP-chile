# -*- coding: utf-8 -*-
"""S162 V750-A §4.1: prueba de equivalencia local entre la vía «código MIROVA» del pipeline y el oráculo.

POR QUÉ. Antes de adoptar el paquete del código de MIROVA, la implementación que viva en pipeline/ tiene que hacer
EXACTAMENTE lo que hace el oráculo validado contra Octave (S159 O1): la misma máscara índice por índice, el mismo VRP y
la misma grilla. Esta prueba se escribe antes de la implementación (TDD): hoy el módulo no existe y la prueba sale roja.

Interfaz que el módulo candidato tiene que exponer (contrato para el PR de la fase 3):
  detectar_mirova(m13, m15, box, dayflag, sunglint) -> máscara bool (67 x 67)
  vrp_mirova(m13, mascara) -> dict con "VRP_MW" y "npix"
  remuestrear_grilla(lat, lon, m13, m15, grilla) -> (m13g, m15g); grilla = {"epsg", "ul_x", "ul_y", "centro_lat",
      "centro_lon"}, 67 x 67 celdas de 750 m, interpolación lineal sobre los píxeles a menos de 45 km del centro.

Pruebas:
  E1 detección y VRP: las 510 grillas de N (S159) con la caja del .m y con la sensible de 21 x 21: máscara idéntica y VRP
     a 1e-9 relativo contra mirova_v750_r2.
  E3 remuestreo: los 10 recortes nativos de R2 (S158): la grilla del candidato contra la grilla lineal que guardó el
     runner, a 1e-9 donde las dos son finitas y con el mismo patrón de celdas sin dato.
Mutaciones con control (--mutaciones): el candidato se reemplaza por el oráculo con una pieza cambiada (K1 y mínimos de K,
media de 8 vecinos, fondo sin halo, recorte a cero, fondo de anillo, remuestreo por vecino más cercano). Cada una tiene
que fallar POR ASERCIÓN; la mutación de control lanza una excepción y tiene que salir como «caída», no como «atrapada».
Uso: python equivalencia_v750a.py --insumos <de extraer_insumos.sh de V750-C> --grillas D:/vrp-trabajo/temporales/s159_n
     --recortes <carpeta con recorte_*.npz y objetivos.json de R2> [--modulo pipeline.mirova_v750_codigo] [--mutaciones]
Salida: 0 si todo pasa; 1 si alguna prueba falla por aserción; 2 si el candidato no existe o se cae.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import types
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "experiments/_s158_audit_r2/oraculo"))
sys.path.insert(0, str(RAIZ / "experiments/_s158_audit_r2/granulos"))
sys.path.insert(0, str(RAIZ / "experiments/_s162_v750c"))
import mirova_v750_r2 as ORA  # noqa: E402
import oraculo_ablacion as OA  # noqa: E402
sys.path.insert(0, str(RAIZ / "experiments/_s163_o2alt"))
import delaunay_perturbado as DP  # noqa: E402

# S162 (relevo VIIRS 750 2, tras O2 en MATLAB): el fillmissing2 del oráculo era el de Qhull, que no es el de MATLAB
# (41 de 84 fondos). El de MATLAB es un Delaunay con desempate simbólico (S163, experiments/_s163_o2alt/INFORME.md H1:
# 166 de 166 VRP de O2). La referencia de esta prueba usa esa regla, tomada del módulo INDEPENDIENTE del subagente de
# S163 (no del port del pipeline), así que E1 compara dos implementaciones de la misma regla, no una consigo misma.
ORA._fillmissing2_lineal = lambda A, jitter=0.0, semilla=0: DP.rellenar(A, "xy_fila_col")[0]

N, CELDA = 67, 750.0
RUNS = ("run_39682867040", "run_39693661527", "run_39680724047")


class Falla(AssertionError):
    pass


def caja(sensible):
    b = np.zeros((N, N))
    b[23:44, 23:44] = 1
    b[30:37, 30:37] = 2
    if sensible:
        b[b == 1] = 2
    return b


def remuestrear_referencia(lat, lon, m13, m15, g, metodo="linear"):
    from pyproj import Transformer
    from scipy.interpolate import griddata
    dlat, dlon = np.radians(lat - g["centro_lat"]), np.radians(lon - g["centro_lon"])
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat)) * np.cos(np.radians(g["centro_lat"])) * np.sin(dlon / 2) ** 2
    sel = np.isfinite(lat) & (6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1))) < 45.0)
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    x, y = t.transform(lon[sel], lat[sel])
    X, Y = np.meshgrid(g["ul_x"] + CELDA * (np.arange(N) + 0.5), g["ul_y"] - CELDA * (np.arange(N) + 0.5))
    out = []
    for v in (m13[sel], m15[sel]):
        ok = np.isfinite(v)
        out.append(griddata(np.column_stack([x[ok], y[ok]]), v[ok], (X, Y), method=metodo))
    return tuple(out)


def adaptador_oraculo():
    """El oráculo con la interfaz del contrato: la prueba tiene que pasar contra sí mismo (identidad)."""
    m = types.SimpleNamespace()
    m.detectar_mirova = lambda m13, m15, box, dayflag, sg: ORA.detectar(m13, m15, box, dayflag, sg)[0]
    m.vrp_mirova = lambda m13, mask: ORA.vrp(m13, mask)
    m.remuestrear_grilla = remuestrear_referencia
    return m


def mutante(pieza):
    """El oráculo con una pieza cambiada (vía oraculo_ablacion de V750-C, o el remuestreo por vecino)."""
    m = adaptador_oraculo()
    if pieza == "remuestreo_vecino":
        m.remuestrear_grilla = lambda la, lo, a, b, g: remuestrear_referencia(la, lo, a, b, g, "nearest")
        return m
    if pieza == "control_que_se_cae":
        def caer(*_a, **_k):
            raise RuntimeError("mutación de control: el programa se cae")
        m.detectar_mirova = caer
        return m
    P = dict(OA.PIEZAS_MIROVA)
    P.update({"k1_y_minimos": {"umbrales_k": True}, "ocho_vecinos": {"ocho_vecinos": True},
              "fondo_sin_halo": {"fondo": "sin_halo"}, "recorte": {"recorte": True},
              "fondo_anillo": {"fondo": "anillo"}}[pieza])
    # oraculo_ablacion arma su propia caja: se le pasa la del caso por un atributo del módulo durante la llamada
    def det(m13, m15, box, dayflag, sg):
        tipo = "sens" if (box == 2).sum() > 49 else "def"
        return OA.detectar(m13, m15, dayflag, sg, dict(P, caja=tipo))
    m.detectar_mirova = det
    m.vrp_mirova = lambda m13, mask: OA.vrp(m13, mask, P, inner_km=5.0)
    return m


def e1(cand, ins, grillas):
    res = {}
    for f in sorted((ins / "n").rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    n = 0
    for i, r in sorted(res.items()):
        if r.get("estado") != "ok" or r.get("dayflag") != 0 or not r.get("oraculo"):
            continue
        gp = next((p for run in RUNS for p in sorted((grillas / run).glob(f"*/grilla_{i:03d}.npz"))), None)
        if gp is None:
            continue
        z = np.load(gp)
        for sens in (False, True):
            box = caja(sens)
            ref_m, _l = ORA.detectar(z["m13"], z["m15"], box, 0, r["sunglint"])
            ref_v = ORA.vrp(z["m13"], ref_m)
            m = np.asarray(cand.detectar_mirova(z["m13"], z["m15"], box, 0, r["sunglint"]), bool)
            if not np.array_equal(m, ref_m):
                raise Falla(f"E1 máscara distinta: id {i} {r['volcan']} {r['hora_utc']} caja {'sens' if sens else 'def'}")
            v = cand.vrp_mirova(z["m13"], m)
            if ref_v["npix"] and not np.isclose(v["VRP_MW"], ref_v["VRP_MW"], rtol=1e-9, atol=0):
                raise Falla(f"E1 VRP distinto: id {i} {v['VRP_MW']} contra {ref_v['VRP_MW']}")
            n += 1
    if n < 1000:
        raise Falla(f"E1 con sólo {n} casos: el instrumento no vio las grillas")
    return n


def e3(cand, recortes):
    objs = {(o["volcan"], o["hora_utc"].replace(" ", "_").replace(":", "")): o
            for o in json.loads((recortes / "objetivos.json").read_text(encoding="utf-8"))}
    n = 0
    for p in sorted(recortes.glob("recorte_*.npz")):
        clave = tuple(p.stem[len("recorte_"):].rsplit("_", 2)[0:1]) + ("_".join(p.stem.split("_")[-2:]),)
        o = objs.get(clave)
        if o is None:
            continue
        z = np.load(p)
        g = o["grilla"]
        a13, a15 = cand.remuestrear_grilla(z["lat"], z["lon"], z["m13"], z["m15"], g)
        for nom, a, ref in (("M13", a13, z["grilla_linear_M13"]), ("M15", a15, z["grilla_linear_M15"])):
            if not np.array_equal(np.isfinite(a), np.isfinite(ref)):
                raise Falla(f"E3 celdas sin dato distintas: {p.name} {nom}")
            ok = np.isfinite(ref)
            if not np.allclose(a[ok], ref[ok], rtol=1e-9, atol=0):
                raise Falla(f"E3 grilla distinta: {p.name} {nom} máx dif {np.nanmax(np.abs(a[ok] - ref[ok]))}")
        n += 1
    if n < 10:
        raise Falla(f"E3 con sólo {n} recortes: el instrumento no vio los recortes")
    return n


def correr(cand, a):
    return e1(cand, a.insumos, a.grillas), e3(cand, a.recortes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insumos", required=True, type=Path)
    ap.add_argument("--grillas", required=True, type=Path)
    ap.add_argument("--recortes", required=True, type=Path)
    ap.add_argument("--modulo", default="pipeline.mirova_v750_codigo")
    ap.add_argument("--mutaciones", action="store_true")
    a = ap.parse_args()
    if a.mutaciones:
        n1, n3 = correr(adaptador_oraculo(), a)
        print(f"identidad (oráculo contra sí mismo): PASA, E1 {n1} casos, E3 {n3} recortes")
        malo = 0
        for pieza in ("k1_y_minimos", "ocho_vecinos", "fondo_sin_halo", "recorte", "fondo_anillo",
                      "remuestreo_vecino", "control_que_se_cae"):
            try:
                correr(mutante(pieza), a)
                estado = "NO ATRAPADA"
            except Falla as e:
                estado = f"atrapada por aserción ({str(e)[:90]})"
            except Exception as e:  # noqa: BLE001
                estado = f"caída ({type(e).__name__})"
            esperado = "caída" if pieza == "control_que_se_cae" else "atrapada"
            malo += not estado.startswith(esperado)
            print(f"   mutación {pieza:20s} {estado}")
        print("mutaciones:", "TODAS COMO SE ESPERA" if not malo else f"{malo} FUERA DE LO ESPERADO")
        return 0 if not malo else 1
    try:
        cand = importlib.import_module(a.modulo)
    except ImportError as e:
        print(f"ROJA: el módulo {a.modulo} no existe todavía ({e})")
        return 2
    try:
        n1, n3 = correr(cand, a)
    except Falla as e:
        print(f"ROJA: {e}")
        return 1
    print(f"VERDE: E1 {n1} casos, E3 {n3} recortes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
