# -*- coding: utf-8 -*-
"""S157 - Desde que lado mira el satelite: ¿cambia la magnitud, la de MIROVA, o la razon?

POR QUE. S130 (experiments/_s130_cenital/medir_gradiente_cenital.py) mostro que, con el
angulo CENITAL del sensor, la magnitud de MIROVA queda plana y la nuestra cae. Nicolas
pregunto si tambien hay un efecto de AZIMUT: un crater profundo visto desde el este deja
oculta una pared distinta que visto desde el oeste. Ese efecto fisico lo sufren igual
MIROVA y nosotros (mismo granulo), asi que la RAZON no deberia depender del lado. Si
depende, la causa es de procesamiento: bow tie, orientacion del pixel estirado respecto
del remuestreo de MIROVA (D17), o la geolocalizacion MODIS corrida hacia el nadir.

EL LADO. Cada record persiste `sensor_azimuth_deg` (S122, scan_geometry.observation_geometry,
pixel mas cercano al hotspot). Convencion verificada en este mismo script de dos formas:
  (1) contra el banner de MIROVA (`Azimut_Sat_deg` del CSV OCR), misma pasada a +-120 s;
  (2) por orden orbital: en una misma noche y plataforma la PRIMERA pasada tiene la traza
      mas al este (cada orbita siguiente cruza mas al oeste), y debe salir con azimut > 0.
Con eso: azimut > 0 = el satelite esta al ESTE del volcan ("mira desde el este").
Se usa sin(azimut): > +0,3 ESTE, < -0,3 OESTE, el resto (cerca del nadir, azimut sin
sentido) queda fuera.

DEFINICIONES, dentro de la afirmacion (A90):
  · nuestro valor = `primary_cluster.vrp_mw` (A10, con su rebaja S147: es el campo de S130,
    se usa para que el pareo sea el mismo; NO es lo que el tablero publica en VIIRS 375);
  · MIROVA = alertas CONS union OCR con el cargador de S126/S130 (mismos alias, mismos
    filtros: Tipo con ALERTA, VRP > 0, hora UTC 3 a 9);
  · nuestras pasadas nocturnas (solar_zenith >= 90), 11 Tier A, ventana 2026;
  · detector por record (auto_audit_weekly.detector_de_record: K si trae codigo_sha) y,
    para C0, el tramo de A104 (antes de #535 / desde #535 hasta K). `sin_marca` fuera;
  · dos pareos:
      PASADA: nuestro record contra la alerta de MIROVA de la MISMA pasada (+-120 s, el
              TOL del banco de paridad). Es el pareo limpio para el lado: numerador y
              denominador salen del mismo granulo, asi que tienen el mismo azimut.
      S130:   literal de medir_gradiente_cenital.py: CADA record nuestro contra el maximo
              de MIROVA de la fecha y sensor (ojo: el docstring de S130 dice "un par por
              noche, maximo de cada lado", pero el codigo no toma maximo del nuestro).
              Con dos pasadas por noche, una de cada lado, ambas se comparan contra el
              mismo maximo, que salio de UNA de ellas: el lado queda mezclado.
  · tramos de cenit de S130: 0-15, 15-25, 25-35, 35-50, 50+.

NULO. El efecto de lado es la diferencia ESTE menos OESTE de la mediana de log10, calculada
dentro de cada celda (volcan x tramo de cenit) y promediada con peso nE*nO/(nE+nO). Se
sortea el lado dentro de cada celda (permutacion, 2000 veces; 500 por volcan; semilla fija) y se reporta
el intervalo del 95 % del efecto bajo azar. Mismo calculo para numerador, denominador y
razon por separado.
"""
import csv
import json
import math
import os
import statistics as st
import sys
from collections import Counter, defaultdict
from datetime import datetime

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)

from _s126_lib import ALIAS, FUENTES_GT, SENSOR_MAP, bucket       # noqa: E402
import auto_audit_weekly as aa                                     # noqa: E402

OUT = os.path.join(HERE, "resultado_lado.json")
VOLS = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
        "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "Tupungatito", "Villarrica"]
VENTANA = ("2026-01-01", "2026-12-31")
BINS = ["0-15", "15-25", "25-35", "35-50", "50+"]
TOL_S = aa.TOL_PASADA_S
MIN_N = 15            # mediana por estrato
MIN_CELDA = 3         # por lado, para que una celda (volcan x tramo) entre al efecto
N_PERM = 2000
N_PERM_VOLCAN = 500
SEMILLA = 20261020
SENSORES = ("v375", "v750", "modis")
GRUPOS = ("K", "C0", "C0_antes_535", "C0_535_a_K")


def bin_de(sz):
    a = abs(sz)
    if a < 15:
        return "0-15"
    if a < 25:
        return "15-25"
    if a < 35:
        return "25-35"
    if a < 50:
        return "35-50"
    return "50+"


def lado_de(az):
    s = math.sin(math.radians(az))
    if s > 0.3:
        return "E"
    if s < -0.3:
        return "O"
    return None


def grupos_de(rec, frontera):
    det = aa.detector_de_record(rec, frontera)
    if det == "K":
        return ["K"]
    if det != "C0":
        return []
    reg = aa.regimen_de_pasada(rec["datetime_utc"][:16], frontera)
    return ["C0", "C0_antes_535" if reg == "antes_535" else "C0_535_a_K"]


def cargar_alertas():
    """Mismos filtros que _s126_lib.cargar_mirova, pero conservando la hora de cada pasada."""
    pas = defaultdict(dict)        # (vol, bk) -> {datetime: vrp}
    for fname in FUENTES_GT:
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            b = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
            fecha = r.get("Fecha_Satelite_UTC") or ""
            if not b or not (VENTANA[0] <= fecha[:10] <= VENTANA[1]):
                continue
            try:
                v = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            if v <= 0 or not (3 <= int(fecha[11:13] or 12) <= 9):
                continue
            t = datetime.fromisoformat(fecha[:19])
            pas[(vol, b)][t] = max(pas[(vol, b)].get(t, 0), v)
    noche = defaultdict(float)     # (vol, fecha, bk) -> max
    for (vol, b), d in pas.items():
        for t, v in d.items():
            k = (vol, t.strftime("%Y-%m-%d"), b)
            noche[k] = max(noche[k], v)
    return pas, noche


def verificar_convencion(registros):
    """(1) contra el banner de MIROVA; (2) por orden orbital."""
    banner = defaultdict(list)
    path = os.path.join(ROOT, FUENTES_GT[1])
    for r in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
        nom = (r.get("Volcan") or "").strip()
        vol = next((v for v, al in ALIAS.items() if nom in al), None)
        b = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
        try:
            az = float(r["Azimut_Sat_deg"])
        except (KeyError, TypeError, ValueError):
            continue
        if vol and b:
            banner[(vol, b)].append((datetime.fromisoformat(r["Fecha_Satelite_UTC"][:19]), az))
    mismo, total, difs = 0, 0, []
    orden = Counter()
    por_noche = defaultdict(set)
    for g in registros:
        for tm, am in banner.get((g["vol"], g["bk"]), []):
            if abs((g["t"] - tm).total_seconds()) <= TOL_S and lado_de(am) and g["lado"]:
                total += 1
                mismo += (lado_de(am) == g["lado"])
                difs.append(abs(g["az"] - am))
        if g["lado"]:
            por_noche[(g["vol"], g["sensor"], g["t"].strftime("%Y-%m-%d"))].add((g["t"], g["lado"]))
    for _k, s in por_noche.items():
        s = sorted(s)
        if len(s) >= 2 and (s[-1][0] - s[0][0]).total_seconds() > 3600:
            orden[f"primera_{s[0][1]}_ultima_{s[-1][1]}"] += 1
    return {"banner_mismo_lado": mismo, "banner_pares": total,
            "banner_mediana_abs_dif_azimut_deg": round(st.median(difs), 2) if difs else None,
            "orden_orbital_noches": dict(orden)}


COBERTURA = Counter()   # nocturnos en ventana: con y sin azimut, por sensor


def leer_registros(frontera):
    out = []
    COBERTURA.clear()
    for v in VOLS:
        p = os.path.join(ROOT, "data", "mirova_equivalent", v + ".json")
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            bk = bucket(r.get("sensor"))
            dt = r.get("datetime_utc") or ""
            if bk is None or not (VENTANA[0] <= dt[:10] <= VENTANA[1]):
                continue
            sol = r.get("solar_zenith_deg")
            if sol is not None and sol < 90:
                continue
            sen, az = r.get("sensor_zenith_deg"), r.get("sensor_azimuth_deg")
            COBERTURA[f"{bk}|{'con' if az is not None else 'sin'}_azimut"] += 1
            pcv = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if sen is None or az is None or pcv <= 0:
                continue
            out.append({"vol": v, "bk": bk, "sensor": r.get("sensor"), "dt": dt,
                        "t": datetime.fromisoformat(dt[:16]), "sz": sen, "az": az,
                        "lado": lado_de(az), "bin": bin_de(sen), "pcv": pcv,
                        "grupos": grupos_de(r, frontera)})
    return out


def parear(registros, pas, noche):
    pares = {"PASADA": [], "S130": []}
    for g in registros:
        if g["lado"] is None or not g["grupos"]:
            continue
        m = noche.get((g["vol"], g["dt"][:10], g["bk"]))
        if m:
            pares["S130"].append(dict(g, mir=m))
        cand = [(abs((g["t"] - t).total_seconds()), v)
                for t, v in pas.get((g["vol"], g["bk"]), {}).items()
                if abs((g["t"] - t).total_seconds()) <= TOL_S]
        if cand:
            pares["PASADA"].append(dict(g, mir=min(cand)[1]))
    return pares


def med(xs):
    return round(st.median(xs), 3) if len(xs) >= MIN_N else None


def _celdas(filas, campo):
    """Celdas (volcan x tramo) con sus log10 y sus etiquetas de lado, como arreglos."""
    d = defaultdict(lambda: ([], []))
    for f in filas:
        d[(f["vol"], f["bin"])][0].append(math.log10(campo(f)))
        d[(f["vol"], f["bin"])][1].append(f["lado"] == "E")
    out = []
    for x, e in d.values():
        e = np.array(e)
        if e.sum() >= MIN_CELDA and (~e).sum() >= MIN_CELDA:
            out.append((np.array(x), e))
    return out


def efecto(celdas, rng=None):
    """Diferencia E-O de la mediana de log10 por celda, promedio ponderado nE*nO/(nE+nO).
    Con `rng`, el lado se sortea DENTRO de cada celda (permutacion)."""
    num = den = 0.0
    for x, e in celdas:
        if rng is not None:
            e = rng.permutation(e)
        ne, no = e.sum(), (~e).sum()
        w = ne * no / (ne + no)
        num += w * (np.median(x[e]) - np.median(x[~e]))
        den += w
    return (num / den) if den else None


CAMPOS = {"nuestro": lambda f: f["pcv"], "mirova": lambda f: f["mir"],
          "razon": lambda f: f["pcv"] / f["mir"]}


def con_nulo(filas, seed, n_perm=N_PERM):
    out = {}
    for nom, c in CAMPOS.items():
        cel = _celdas(filas, c)
        obs = efecto(cel)
        if obs is None:
            out[nom] = None
            continue
        rng = np.random.default_rng(seed)
        nul = np.sort([efecto(cel, rng) for _ in range(n_perm)])
        p = float(np.mean(np.abs(nul) >= abs(obs) - 1e-12))
        out[nom] = {"efecto_log10_E_menos_O": round(float(obs), 4),
                    "factor_E_sobre_O": round(10 ** float(obs), 3),
                    "nulo_ic95": [round(float(nul[int(0.025 * n_perm)]), 4),
                                  round(float(nul[int(0.975 * n_perm) - 1]), 4)],
                    "p_dos_colas": round(p, 4), "n_perm": n_perm}
    cel = _celdas(filas, CAMPOS["razon"])
    out["n_pares"] = len(filas)
    out["n_en_celdas_validas"] = int(sum(len(x) for x, _ in cel))
    out["n_celdas_validas"] = len(cel)
    return out


def tabla(filas, clave):
    d = defaultdict(list)
    for f in filas:
        d[clave(f)].append(f)
    res = {}
    for k, fs in sorted(d.items()):
        res["|".join(k)] = {
            "n": len(fs),
            "nuestro_mediano_mw": med([f["pcv"] for f in fs]),
            "mirova_mediano_mw": med([f["mir"] for f in fs]),
            "razon_mediana": med([f["pcv"] / f["mir"] for f in fs]),
            "cenit_mediano": med([abs(f["sz"]) for f in fs]),
        }
    return res


def main():
    frontera = aa.leer_frontera_k()
    pas, noche = cargar_alertas()
    regs = leer_registros(frontera)
    pares = parear(regs, pas, noche)
    res = {"frontera_k": frontera, "tol_s": TOL_S, "ventana": VENTANA,
           "convencion": verificar_convencion(regs),
           "nocturnos_en_ventana": dict(sorted(COBERTURA.items())),
           "lado_fuera_por_nadir": sum(1 for g in regs if g["lado"] is None),
           "pareos": {}}
    for pareo, filas in pares.items():
        rp = {}
        for gr in GRUPOS:
            for bk in SENSORES:
                fs = [f for f in filas if gr in f["grupos"] and f["bk"] == bk]
                if not fs:
                    continue
                seed = SEMILLA + 7 * GRUPOS.index(gr) + SENSORES.index(bk)
                rp[f"{gr}|{bk}"] = {
                    "efecto_estratificado": con_nulo(fs, seed),
                    "por_tramo_y_lado": tabla(fs, lambda f: (f["bin"], f["lado"])),
                    "por_volcan_y_lado": tabla(fs, lambda f: (f["vol"], f["lado"])),
                    "efecto_por_volcan": {
                        v: con_nulo([f for f in fs if f["vol"] == v], seed + 1000 + i, N_PERM_VOLCAN)
                        for i, v in enumerate(VOLS)
                        if sum(1 for f in fs if f["vol"] == v) >= 2 * MIN_CELDA},
                }
        res["pareos"][pareo] = rp

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)

    c = res["convencion"]
    print(f"Convencion: banner MIROVA mismo lado {c['banner_mismo_lado']}/{c['banner_pares']}, "
          f"|dif azimut| mediana {c['banner_mediana_abs_dif_azimut_deg']} deg; "
          f"orden orbital {c['orden_orbital_noches']}")
    print(f"nocturnos en ventana: {res['nocturnos_en_ventana']}")
    print(f"records con lado indefinido (cerca del nadir): {res['lado_fuera_por_nadir']}")
    for pareo, rp in res["pareos"].items():
        print(f"\n=== PAREO {pareo} ===")
        print(f"{'grupo|sensor':20s} {'n':>5s} {'n_cel':>6s}  "
              f"{'nuestro E/O (IC95 nulo, p)':>34s}  {'MIROVA E/O':>30s}  {'razon E/O':>30s}")
        for k, d in rp.items():
            e = d["efecto_estratificado"]
            def fmt(x):
                if not x:
                    return f"{'s/d':>30s}"
                a, b = x["nulo_ic95"]
                return f"{x['factor_E_sobre_O']:6.3f} [{10**a:5.3f},{10**b:5.3f}] p{x['p_dos_colas']:.3f}"
            print(f"{k:20s} {e['n_pares']:5d} {e['n_en_celdas_validas']:6d}  "
                  f"{fmt(e['nuestro']):>34s}  {fmt(e['mirova']):>30s}  {fmt(e['razon']):>30s}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
