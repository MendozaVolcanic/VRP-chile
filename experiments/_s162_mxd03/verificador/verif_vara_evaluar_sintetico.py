# -*- coding: utf-8 -*-
"""Verificador S162 MxD03, afirmacion A5 (--evaluar) y la cadena P3 del evaluador: vara_mxd03.evaluar lee filas del
arnes (campo `pico`), llama a evaluar_sola.vara (lectura 3) sobre la vara congelada vara_viirs_mxd03.json, escribe
vara_resultado.json, y evaluar_mxd03.vara_desde_estado lo traduce a DETIENE / SESGO POR SATELITE / NO DETIENE.
Ninguna prueba del auditor recorre esa cadena entera. Aqui se fabrican filas del arnes para las alertas con vara estricta
y cenit <= 35 de la vara REAL (65 granulos, Terra 31 y Aqua 34), con el pico MODIS puesto a proposito:
  caso A  M (MxD03) a 0,3 km del objeto VIIRS de la noche y C (interp) a 2,3 km, mismo signo en Terra y Aqua;
          los 20 nulos en un circulo de 2 km alrededor de C. Esperado: MXD03 MAS CERCA -> NO DETIENE.
  caso B  al reves (C cerca, M lejos). Esperado: INTERP MAS CERCA -> DETIENE. Es el control positivo de que la cadena
          PUEDE detener (si no pudiera, la regla «la vara detiene» del §10 seria inalcanzable).
  caso C  C cerca en Terra y M cerca en Aqua. Esperado: SESGO POR SATELITE -> no detiene, pero marcado.
  caso D  sin filas: SIN VARA -> NO DETIENE (el evaluador lo lee asi; la marca queda en vara_cruda).
Uso: cd experiments/_s162_mxd03 && PYTHONIOENCODING=utf-8 python verificador/verif_vara_evaluar_sintetico.py
"""
import json
import math
import os
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
AB = AQUI.parent
RAIZ = AB.parents[1]
for p in (AB, RAIZ / "experiments/_s151_mxd03_sola_123", RAIZ / "experiments/_s151_mxd03_cumulo_121",
          RAIZ / "experiments/_s151_mxd03_etiquetas", RAIZ / "scripts", RAIZ):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import vara_mxd03 as V  # noqa: E402
import importlib.util  # noqa: E402
import hashlib  # noqa: E402
# import por ruta explicita: experiments/_s151_mxd03_etiquetas/evaluar_mxd03.py es un HOMONIMO (el de la 1.17) y
# vara_mxd03 pone esa carpeta antes en sys.path (hallazgo del verificador, ver informe)
_spec = importlib.util.spec_from_file_location("evaluar_mxd03_s162", AB / "evaluar_mxd03.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

NULOS = tuple("R%02d" % k for k in range(20))


def latlon_desde(vent, n_km, e_km):
    return [vent[0] + n_km / 111.32, vent[1] + e_km / (111.32 * math.cos(math.radians(vent[0])))]


def filas(tabla, pob, modo):
    rec = {"%s|%s" % (f["vol"], g["clave"]): f for g in pob["granulos"] for f in g["records"]}
    out = []
    for k, t in tabla["granulos"].items():
        f = rec[k]
        if not t["estricta"]["pasadas"] or f["z"] is None or f["z"] > 35:
            continue
        vent = t["vent"]
        v = (t["estricta"]["noche"]["n_km"], t["estricta"]["noche"]["e_km"])
        terra = f["sensor"] == "MODIS_TERRA"
        c_cerca = {"A": False, "B": True, "C": terra}[modo]
        cerca, lejos = (v[0] + 0.3, v[1]), (v[0] + 2.3, v[1])
        pc, pm_ = (cerca, lejos) if c_cerca else (lejos, cerca)
        pos = {"C": latlon_desde(vent, *pc), "M": latlon_desde(vent, *pm_)}
        # fase al azar FIJA POR GRANULO, como hace el arnes (sal + clave): con una misma fase en todos los
        # granulos las medianas de los pares (k, k+4) no se anulan y la lectura 3 da INDECIDIBLE siempre
        fase = int(hashlib.sha1(("verif" + k).encode()).hexdigest()[:8], 16) / float(16 ** 8)
        for i, b in enumerate(NULOS):
            a = math.radians(360.0 * ((i / 20.0 + fase) % 1.0))
            pos[b] = latlon_desde(vent, pc[0] + 2.0 * math.cos(a), pc[1] + 2.0 * math.sin(a))
        out.append({"tipo": "record", "estado": "ok", "vol": f["vol"], "clave": g_clave(k), "lab": f["lab"],
                    "sensor": f["sensor"], "dt": f["dt"], "z": f["z"],
                    "pico": {"linea": 1, "frame": 1, "exceso": 1.0, "pos": pos, "pos_centro": pos}})
    return out


def g_clave(k):
    return k.split("|", 1)[1]


def correr(modo):
    tabla = json.load(open(AB / "vara_viirs_mxd03.json", encoding="utf-8"))
    pob = json.load(open(AB / "poblacion.json", encoding="utf-8"))
    fs = [] if modo == "D" else filas(tabla, pob, modo)
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "parte").mkdir()
        with open(d / "parte" / "ab_parte00.jsonl", "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"tipo": "cabecera", "parte": 0}) + "\n")
            for r in fs:
                fh.write(json.dumps(r) + "\n")
        V.evaluar(str(d))
        res = json.load(open(d / "vara_resultado.json", encoding="utf-8"))
    dec = res["decide_le35"]
    return res["estado"], E.vara_desde_estado(res["estado"]), dec.get("n"), dec.get("n_noches"), dec.get("por_satelite")


def main():
    esperado = {"A": ("MXD03 MAS CERCA", "NO DETIENE"), "B": ("INTERP MAS CERCA", "DETIENE"),
                "C": ("SESGO POR SATELITE", "SESGO POR SATELITE"), "D": ("SIN VARA", "NO DETIENE")}
    fallas = []
    for modo in "ABCD":
        est, ev, n, nn, sat = correr(modo)
        ok = (est, ev) == esperado[modo]
        print(f"caso {modo}: evaluar_sola -> {est!r}; evaluador -> {ev!r}; n={n} noches={nn} "
              f"sat={ {k: (v['n'], v['dd_mediana_km']) for k, v in (sat or {}).items()} } "
              f"{'OK' if ok else 'INESPERADO, esperaba ' + str(esperado[modo])}")
        if not ok:
            fallas.append(modo)
    print("RESULTADO:", "LIMPIO: la cadena puede DETENER, marcar SESGO y leer SIN VARA" if not fallas else f"fallas en {fallas}")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
