# Tarea 1.23, punto 4: cuantos granulos de la poblacion son "como Chillan Aqua 2026-10-12 07:20", o
# sea, donde mover la geolocalizacion hace que la seleccion anclada al crater elija OTRO cumulo (otro
# objeto, no el mismo corrido). Medido sobre los artefactos ya guardados de la 1.21, sin reprocesar.
#
# POR QUE ASI. En el volcan, el calor no se mueve: si con MxD03 el cumulo publicado sale a mas distancia
# del de produccion que el propio corrimiento de la grilla (mas 1,5 km de tolerancia, la misma de
# `tipos_de_cambio` del evaluador de la 1.21), los pixeles no son los mismos y la seleccion cambio de
# objeto. Eso es un efecto de POSICION de verdad (la cerca del inner y el ancla deciden con la posicion),
# a diferencia de las dos perdidas de Lascar, que son de etiqueta. Se compara con el brazo R de la 1.21
# (un solo rumbo al azar del mismo tamano en km) para ver si MxD03 salta mas o menos que el azar, por
# cenit, porque el pixel MODIS se ensancha hacia el borde del barrido.
#
# La seleccion del cumulo no depende de la etiqueta (el flag de la 1.21 solo cambia derivar_distance_class),
# asi que M y MC tienen el mismo cumulo salvo en la rama del Test 1; aca se usa M (etiqueta de produccion),
# y para el caso de Chillan se muestra tambien MC.
#
# Uso: python saltos_de_cumulo_121.py <carpeta con los <job>.json de la 1.21> [--salida x.txt]
import argparse
import io
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TOL_KM = 1.5
BINS = ((0, 20), (20, 35), (35, 50), (50, 90))
CHILLAN = ("NevadosDeChillan", "MYD021KM.A2026285.0720")


def _km(a, b):
    return math.hypot((a["pc_lat"] - b["pc_lat"]) * 111.32,
                      (a["pc_lon"] - b["pc_lon"]) * 111.32 * math.cos(math.radians(a["pc_lat"])))


def _med(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def tipo(a, b, corr_km):
    """Que le paso al cumulo publicado del brazo Y (a) al X (b)."""
    if (a or {}).get("pc_lat") is None and (b or {}).get("pc_lat") is None:
        return "sin cumulo en los dos"
    if (a or {}).get("pc_lat") is None or (b or {}).get("pc_lat") is None:
        return "aparece o desaparece"
    d = _km(a, b)
    if d > corr_km + TOL_KM:
        return "otro objeto (salta mas que el corrimiento + 1,5 km)"
    va, vb = a.get("pc_vrp") or 0.0, b.get("pc_vrp") or 0.0
    if a.get("pc_n_pixels") == b.get("pc_n_pixels") and abs(va - vb) <= 0.01 * max(abs(va), 1e-9):
        return "el mismo, reubicado"
    return "cerca, con otros pixeles o magnitud"


def _bin(c):
    for lo, hi in BINS:
        if c is not None and lo <= c < hi:
            return "%d-%d" % (lo, hi)
    return "?"


def analizar(carpeta):
    cuenta = {x: defaultdict(lambda: defaultdict(int)) for x in ("M", "R")}
    pub = {x: defaultdict(int) for x in ("M", "R")}
    chillan, casos = None, []
    direccion = defaultdict(list)    # vector C -> M en el crater (MxD03 menos `_interp_geo`), por satelite y cenit
    for p in sorted(Path(carpeta).rglob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if not (isinstance(d, dict) and "granulos" in d and "brazos" in d):
            continue
        for g in d["granulos"]:
            if g.get("estado") != "ok":
                continue
            b = g["brazos"]
            cen = (b.get("C") or {}).get("cenit")
            corr = g["desplazamiento"]["km"]
            if cen is not None:
                direccion[(g["clave"][:3], "bajo 35" if cen < 35 else "35 o mas")].append(
                    (-g["desplazamiento"]["dn_km"], -g["desplazamiento"]["de_km"]))
            for x in ("M", "R"):
                t = tipo(b.get("C"), b.get(x), corr)
                cuenta[x][_bin(cen)][t] += 1
                cuenta[x]["todos"][t] += 1
                if t.startswith("otro objeto"):
                    pub[x]["pub C->%s %d->%d" % (x, g["pub"]["C"], g["pub"][x])] += 1
                    if x == "M":
                        casos.append({"volcan": d["volcan"], "clave": g["clave"], "cenit": cen, "corr_km": corr,
                                      "C": [b["C"].get(k) for k in ("pc_dist", "pc_n_pixels", "pc_vrp")],
                                      "M": [b["M"].get(k) for k in ("pc_dist", "pc_n_pixels", "pc_vrp")],
                                      "salto_km": round(_km(b["C"], b["M"]), 2),
                                      "pub": g["pub"]})
            if (d["volcan"], g["clave"]) == CHILLAN:
                chillan = {"cenit": cen, "frame": g["desplazamiento"]["frame"], "corr_km": corr,
                           **{x: {k: (b.get(x) or {}).get(k) for k in ("pc_dist", "pc_n_pixels", "pc_vrp", "dc")}
                              for x in ("C", "M", "MC", "R", "CC", "RC")}, "pub": g["pub"],
                           "tipo_M": tipo(b.get("C"), b.get("M"), corr), "tipo_R": tipo(b.get("C"), b.get("R"), corr)}
    return {"cuenta": {x: {k: dict(v) for k, v in c.items()} for x, c in cuenta.items()},
            "publicacion_en_saltos": {x: dict(v) for x, v in pub.items()}, "chillan": chillan,
            "casos_M": sorted(casos, key=lambda c: -(c["cenit"] or 0)),
            "direccion_C_a_M": {"%s, cenit %s" % k: {"n": len(v), "norte_km_mediana": round(_med([x[0] for x in v]), 3),
                                                     "este_km_mediana": round(_med([x[1] for x in v]), 3)}
                                for k, v in sorted(direccion.items())}}


def imprimir(r, fh):
    p = lambda *a: print(*a, file=fh)  # noqa: E731
    for x in ("M", "R"):
        p("Cumulo publicado, C contra %s (tolerancia: corrimiento medido en el crater + %.1f km)" % (x, TOL_KM))
        for b in ("todos",) + tuple("%d-%d" % bb for bb in BINS):
            if b in r["cuenta"][x]:
                p("  cenit %-6s %s" % (b, dict(sorted(r["cuenta"][x][b].items()))))
        p("  publicacion de produccion en los saltos: %s" % r["publicacion_en_saltos"][x])
    p("\nGranulos donde M elige otro objeto (pc_dist, n_pixels, pc_vrp de C y de M):")
    for c in r["casos_M"]:
        p("  %-20s %s cenit %5.1f corr %.2f km | C %s | M %s | salto %.2f km | pub %s" % (
            c["volcan"], c["clave"], c["cenit"], c["corr_km"], c["C"], c["M"], c["salto_km"], c["pub"]))
    p("\nDireccion C -> M en el crater (MOD = Terra, MYD = Aqua): %s" % json.dumps(r["direccion_C_a_M"]))
    p("\nChillan Aqua 2026-10-12 07:20 (%s): %s" % (CHILLAN[1], json.dumps(r["chillan"], ensure_ascii=False)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    buf = io.StringIO()
    imprimir(analizar(a.carpeta), buf)
    sys.stdout.write(buf.getvalue())
    if a.salida:
        Path(a.salida).write_text(buf.getvalue(), encoding="utf-8")


if __name__ == "__main__":
    main()
