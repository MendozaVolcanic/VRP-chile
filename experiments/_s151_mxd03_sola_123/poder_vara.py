# Tarea 1.23: poder de la vara VIIRS, con la geometria REAL de la muestra y verdades conocidas (A110).
#
# POR QUE. Antes de correr hay que saber si la vara puede distinguir: con cuantos granulos, con que ruido
# y con que sesgo propio de la vara el estado sale bien. Se simula sobre los granulos que de verdad tienen
# vara (vara_viirs.json, nivel estricto, MODIS con alerta de MIROVA) con el corrimiento C -> M que la 1.21
# MIDIO en el crater de cada uno (no el resultado de la vara: la 1.21 no tenia vara). Cada escenario fija
# donde esta el objeto de verdad (donde dice MxD03, donde dice `_interp_geo`, o a medio camino), el ruido
# de posicion del pixel MODIS (un foco sub-pixel en un pixel de 1 km: +-0,5 km, desviacion ~0,3 km por eje)
# y del objeto VIIRS de la noche, y un sesgo constante de la vara. La funcion que decide es la misma del
# evaluador (evaluar_sola.vara y estado_vara), sin copia.
#
# Uso: python poder_vara.py <artefactos de la 1.21> [--sims 200] [--salida x.txt]
import argparse
import io
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import evaluar_sola as ES  # noqa: E402
import jobs_123 as J  # noqa: E402


def _latlon(vent, n, e):
    return [vent[0] + n / 111.32, vent[1] + e / (111.32 * math.cos(math.radians(vent[0])))]


def base(art121, tabla, pob):
    """Granulos del conjunto principal con el corrimiento medido por la 1.21 (interp - MxD03 en el crater)."""
    desp = {}
    for p in Path(art121).rglob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(d, dict) and "granulos" in d and "brazos" in d:
            for g in d["granulos"]:
                if g.get("estado") == "ok":
                    desp[(d["volcan"], g["clave"])] = (g["desplazamiento"]["dn_km"], g["desplazamiento"]["de_km"])
    filas = []
    for vol, v in pob["volcanes"].items():
        for g in v["muestra"]:
            t = tabla["granulos"].get("%s|%s" % (vol, g["clave"]))
            if t and t["estricta"]["noche"] and g["lab"] == "pos" and (vol, g["clave"]) in desp:
                filas.append(dict(g, volcan=vol, s=desp[(vol, g["clave"])], vent=t["vent"]))
    return filas


def simular(filas, verdad, sd_pix, sd_v, sesgo, rng):
    ok, tab = [], {"granulos": {}}
    for g in filas:
        sn, se = g["s"]                       # C = M + s
        x0 = (rng.gauss(0, 0.3), rng.gauss(0, 0.3))
        off = {"M": (0.0, 0.0), "C": (-sn, -se), "medio": (-sn / 2, -se / 2)}[verdad]
        m = (x0[0] + off[0] + rng.gauss(0, sd_pix), x0[1] + off[1] + rng.gauss(0, sd_pix))
        c = (m[0] + sn, m[1] + se)
        v = (x0[0] + sesgo[0] + rng.gauss(0, sd_v), x0[1] + sesgo[1] + rng.gauss(0, sd_v))
        mod = math.hypot(sn, se)
        u = rng.random()
        pos = {"C": _latlon(g["vent"], *c), "M": _latlon(g["vent"], *m)}
        for k, b in enumerate(ES.NULOS):
            a = 2 * math.pi * ((u + k / ES.K_NULOS) % 1.0)
            pos[b] = _latlon(g["vent"], c[0] + mod * math.cos(a), c[1] + mod * math.sin(a))
        ok.append({"volcan": g["volcan"], "clave": g["clave"], "lab": g["lab"], "datetime_utc": g["datetime_utc"],
                   "sensor": g["sensor"], "sensor_zenith_deg": g["sensor_zenith_deg"], "pico": {"pos": pos}})
        tab["granulos"]["%s|%s" % (g["volcan"], g["clave"])] = {
            "vent": g["vent"], "estricta": {"noche": {"n_km": v[0], "e_km": v[1]}}}
    return ES.vara(ok, tab, "pico", "estricta", "pos")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("art121")
    ap.add_argument("--sims", type=int, default=200)
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    tabla = json.loads((AQUI / "vara_viirs.json").read_text(encoding="utf-8"))
    pob = J.cargar()
    filas = base(a.art121, tabla, pob)
    buf = io.StringIO()
    p = lambda *x: print(*x, file=buf)  # noqa: E731
    sep = sorted(math.hypot(*g["s"]) for g in filas)
    p("Conjunto principal: %d granulos (%s), %d noches; corrimiento C-M medido por la 1.21: mediana %.2f km, "
      "minimo %.2f km" % (len(filas), dict(Counter(g["volcan"] for g in filas)),
                          len({(g["volcan"], g["datetime_utc"][:10]) for g in filas}), sep[len(sep) // 2], sep[0]))
    p("Satelites: %s" % dict(Counter(g["sensor"] for g in filas)))
    escenarios = [("M", 0.3, 0.15, (0, 0)), ("C", 0.3, 0.15, (0, 0)), ("medio", 0.3, 0.15, (0, 0)),
                  ("M", 0.5, 0.3, (0, 0)), ("C", 0.5, 0.3, (0, 0)),
                  ("M", 0.3, 0.15, (0.0, 0.5)), ("C", 0.3, 0.15, (0.0, 0.5)),
                  ("medio", 0.3, 0.15, (0.0, 1.0)), ("M", 0.3, 0.15, (0.0, 1.5))]
    for verdad, sp, sv, sg in escenarios:
        rng = random.Random(hash((verdad, sp, sv, sg)) & 0xFFFFFFFF)
        cnt = Counter()
        for _ in range(a.sims):
            cnt[simular(filas, verdad, sp, sv, sg, rng)["estado"]] += 1
        p("verdad %-5s ruido pixel %.1f km, vara %.2f km, sesgo de la vara (N, E) %s km: %s" % (
            verdad, sp, sv, sg, {k: round(v / a.sims, 3) for k, v in sorted(cnt.items())}))
    # cuantos granulos hacen falta: submuestras al azar del conjunto, verdad M, ruido 0,5 / 0,3
    for n in (5, 10, 20, 40):
        rng = random.Random(n)
        cnt = Counter()
        for _ in range(a.sims):
            sub = rng.sample(filas, min(n, len(filas)))
            cnt[simular(sub, "M", 0.5, 0.3, (0, 0), rng)["estado"]] += 1
        p("submuestra de %2d granulos, verdad M, ruido 0,5 / 0,3: %s" % (
            n, {k: round(v / a.sims, 3) for k, v in sorted(cnt.items())}))
    sys.stdout.write(buf.getvalue())
    if a.salida:
        Path(a.salida).write_text(buf.getvalue(), encoding="utf-8")


if __name__ == "__main__":
    main()
