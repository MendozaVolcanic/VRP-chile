# -*- coding: utf-8 -*-
"""Los cuatro seguimientos del verificador (S162, MxD03), medidos sobre los artefactos de las tres tandas.

1. Relleno -999: los 36 records en 8 granulos con `n_fill_mxd03 > 0`. Que forma tiene el relleno (escaneos enteros de
   10 lineas?), donde quedo el pixel del crater en K (`desplazamiento`), y si K conserva mas pixeles que X en el
   anillo de fondo (lo que diria que X pierde y K no) o menos (lo que diria que la interpolacion del relleno le
   quita a K los vecinos del bloque).
2. Borde del barrido: el corrimiento interp menos MxD03 contra el frame y el cenit, y contra el modelo de desfase de
   indice de `_interp_geo` (+2 pixeles en el frame 0, -1 en el 1353) multiplicado por el ancho del pixel MODIS a
   ese angulo (geometria esferica, R = 6371 km, h = 705 km, IFOV = 1 km / 705 km).
3. Cenit imposible: records con cenit sobre 65,6 grados (el maximo fisico de MODIS en el borde del barrido) y en que
   granulos caen.
4. Control del modulo de R: `control_r_modulo` del evaluador aceptaria un modulo de 25.742 km; se mide cuantos records
   marcaria un tope fisico de 20 km (control positivo) y cual es el modulo maximo real fuera de los granulos con
   relleno.

Las dos preguntas del instrumento, por seccion, estan en cada encabezado impreso.
"""
import collections
import io
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cargar_a61 import NULOS, cargar_artefactos, cargar_poblacion, haversine_km  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
NS = 1354
R_T, H, IFOV = 6371.0, 705.0, 1.0 / 705.0


def ancho_pixel_km(zenit_deg):
    """Ancho a lo largo del barrido del pixel MODIS de 1 km a ese cenit (sin bow tie), por geometria esferica."""
    zr = math.radians(zenit_deg)
    s = math.sin(zr) * R_T / (R_T + H)
    ts = math.asin(min(1.0, s))
    return IFOV * R_T * (((R_T + H) / R_T) * math.cos(ts) / math.cos(zr) - 1.0)


def main():
    ok, cab, pies = cargar_artefactos()
    pob, pobf = cargar_poblacion()
    print("records ok:", len(ok))

    # ---------------------------------------------------------------- 1. relleno
    print("\n== 1. RELLENO -999 EN MxD03")
    print("   P1: si X no perdiera nada con relleno, n_fill seria 0 en todos; P2: si el contador estuviera muerto, nunca seria > 0.")
    rell = [r for r in ok if (r.get("n_fill_mxd03") or 0) > 0]
    por_g = collections.defaultdict(list)
    for r in rell:
        por_g[r["clave"]].append(r)
    print("   records con relleno: %d en %d granulos | etiquetas: %s" % (len(rell), len(por_g), dict(collections.Counter(r["lab"] for r in rell))))
    print("   n_fill por granulo, en lineas enteras de 1.354 pixeles (un escaneo MODIS = 10 lineas):")
    for g, rs in sorted(por_g.items(), key=lambda kv: -kv[1][0]["n_fill_mxd03"]):
        nf = rs[0]["n_fill_mxd03"]
        print("     %s n_fill %6d = %.2f lineas = %.2f escaneos | records %d (%s)" % (
            g, nf, nf / NS, nf / NS / 10, len(rs), ", ".join("%s z=%.0f desp=%.1f" % (r["vol"][:6], r["z"], r["desplazamiento"]["km"]) for r in rs)))
    # anillo de fondo K contra X: nulo sobre los records sin relleno
    def dif_anillo(r):
        K, X = r["brazos"]["K"], r["brazos"]["X"]
        return (K["diag_n_bg_anillo"] or 0) - (X["diag_n_bg_anillo"] or 0)
    sin = [dif_anillo(r) for r in ok if (r.get("n_fill_mxd03") or 0) == 0 and r["brazos"]["K"] and r["brazos"]["X"]]
    con = [(dif_anillo(r), r) for r in rell if r["brazos"]["K"] and r["brazos"]["X"]]
    sin_s = sorted(sin)
    print("   pixeles del anillo de fondo, K menos X: SIN relleno (n %d) mediana %d, p5 %d, p95 %d, min %d, max %d" % (
        len(sin), statistics.median(sin), sin_s[len(sin) // 20], sin_s[19 * len(sin) // 20], min(sin), max(sin)))
    print("   CON relleno (n %d):" % len(con))
    for dfa, r in sorted(con, key=lambda x: -abs(x[0])):
        K, X = r["brazos"]["K"], r["brazos"]["X"]
        print("     %-19s %s z=%4.1f %-10s | anillo K %5s X %5s dif %+5d | n_anom K/X %s/%s | pc_vrp K/X %s/%s | pub %d/%d | desp crater %.1f km (linea %d)" % (
            r["vol"], r["dt"], r["z"], r["lab"], K["diag_n_bg_anillo"], X["diag_n_bg_anillo"], dfa, K["n_anom"], X["n_anom"],
            K["pc_vrp"], X["pc_vrp"], r["pub"]["K"], r["pub"]["X"], r["desplazamiento"]["km"], r["desplazamiento"]["linea"]))
    fuera = [(d, r) for d, r in con if abs(d) > max(abs(sin_s[len(sin) // 20]), abs(sin_s[19 * len(sin) // 20]))]
    print("   records con relleno cuya diferencia de anillo sale del rango p5-p95 del nulo: %d de %d" % (len(fuera), len(con)),
          [(r["vol"], r["dt"], d) for d, r in fuera])
    print("   lectura: dif > 0 = K tiene mas pixeles de fondo que X (X perdio los del relleno); dif < 0 = K perdio mas (vecinos del bloque con posicion absurda).")
    # los dos records con el crater contaminado
    abs_ = [r for r in ok if r["desplazamiento"]["km"] > 100]
    print("   records con el pixel del crater de K en posicion absurda (desp > 100 km): %d" % len(abs_))
    for r in abs_:
        K, X = r["brazos"]["K"], r["brazos"]["X"]
        print("     %s %s z=%.1f %s | K: n_anom %s t_bg %s anillo %s t_max %s | X: n_anom %s t_bg %s anillo %s t_max %s | record K existe: %s" % (
            r["vol"], r["dt"], r["z"], r["lab"], K["n_anom"], K["t_bg_k"], K["diag_n_bg_anillo"], K["t_max_k"],
            X["n_anom"], X["t_bg_k"], X["diag_n_bg_anillo"], X["t_max_k"], K is not None))
        g = pobf[(r["vol"], r["dt"])]
        print("       en data/ (poblacion): pub_guardada %s, pc_vrp_guardada %s, dc_guardada %s, codigo_sha %s" % (
            g["pub_guardada"], g["pc_vrp_guardada"], g["dc_guardada"], g["codigo_sha"][:9]))

    # ---------------------------------------------------------------- 2. borde del barrido
    print("\n== 2. CORRIMIENTO EN EL BORDE DEL BARRIDO contra el modelo de desfase de indice")
    print("   P1: si `_interp_geo` no tuviera desfase, el corrimiento no creceria con el frame hacia 0; P2: el modelo se compara con el dato, no consigo mismo.")
    print("   ancho del pixel por geometria: z 0 -> %.2f km, 30 -> %.2f, 45 -> %.2f, 55 -> %.2f, 60 -> %.2f, 65 -> %.2f, 65.5 -> %.2f" % tuple(
        ancho_pixel_km(z) for z in (0, 30, 45, 55, 60, 65, 65.5)))
    limpios = [r for r in ok if (r.get("n_fill_mxd03") or 0) == 0]
    bins = [(0, 10), (10, 40), (40, 100), (100, 300), (300, 600), (600, 902), (902, 1100), (1100, 1300), (1300, 1340), (1340, 1354)]
    print("   frame del pixel del crater | n | cenit mediana | corrimiento mediano (km) | p90 | modelo: |desfase| px * ancho(z mediana)")
    for lo, hi in bins:
        sel = [r for r in limpios if lo <= r["desplazamiento"]["frame"] < hi]
        if not sel:
            continue
        zs = statistics.median(r["z"] for r in sel)
        km = sorted(r["desplazamiento"]["km"] for r in sel)
        fm = statistics.median(r["desplazamiento"]["frame"] for r in sel)
        desfase = 2.0 - 3.0 * fm / 1353.0          # +2 en el frame 0, 0 en el 902, -1 en el 1353
        print("   [%4d,%4d) | %4d | %5.1f | %5.2f | %5.2f | %.2f px * %.2f km = %.2f km" % (
            lo, hi, len(sel), zs, statistics.median(km), km[9 * len(km) // 10], abs(desfase), ancho_pixel_km(zs), abs(desfase) * ancho_pixel_km(zs)))
    print("   nota: el modelo no incluye el desfase a lo largo de la traza (±2 lineas, 1 a 2 km) ni el bow tie; es una cota del termino dominante.")
    borde = sorted([r for r in limpios if r["desplazamiento"]["km"] > 8], key=lambda r: -r["desplazamiento"]["km"])
    print("   records SIN relleno con corrimiento > 8 km: %d | todos con frame < 100: %s | cenit min %.1f" % (
        len(borde), all(r["desplazamiento"]["frame"] < 100 for r in borde), min(r["z"] for r in borde)))
    print("   lados: %s | etiquetas: %s | alguno publica en K o X: %s" % (
        dict(collections.Counter(r["lado"] for r in borde)), dict(collections.Counter(r["lab"] for r in borde)),
        any(r["pub"]["K"] or r["pub"]["X"] for r in borde)))

    # ---------------------------------------------------------------- 3. cenit imposible
    print("\n== 3. CENIT SOBRE EL MAXIMO FISICO DE MODIS (65,6 grados en el borde del barrido)")
    print("   P1: si los angulos interpolados no se contaminaran, no habria ninguno; P2: el cenit sale del record de K en data/, no de este script.")
    raros = sorted([r for r in ok if r["z"] > 65.6], key=lambda r: -r["z"])
    print("   records con z > 65,6: %d | con relleno en su granulo: %d | granulos: %s" % (
        len(raros), sum(1 for r in raros if (r.get("n_fill_mxd03") or 0) > 0), sorted({r["clave"] for r in raros})))
    for r in raros:
        print("     %s %s z=%.2f frame %d linea %d n_fill %d | cenit X %s | desp %.1f km" % (
            r["vol"], r["dt"], r["z"], r["desplazamiento"]["frame"], r["desplazamiento"]["linea"], r.get("n_fill_mxd03", 0),
            r["brazos"]["X"]["cenit"] if r["brazos"]["X"] else None, r["desplazamiento"]["km"]))
    zmax_limpio = max(r["z"] for r in limpios)
    print("   cenit maximo en los records sin relleno: %.2f" % zmax_limpio)

    # ---------------------------------------------------------------- 4. control del modulo de R
    print("\n== 4. CONTROL DEL MODULO DE R (evaluar_mxd03.py:324-334 solo exige aplicado = pedido a 10 m)")
    print("   P1: con un tope fisico, un modulo de 25.742 km sale marcado; P2: sin tope, el control de hoy no marca nada (se reproduce).")
    con_r = [r for r in ok if r["r_nulos"]]
    malos_hoy, malos_tope = [], []
    TOPE = 20.0
    for r in con_r:
        ns = r["nulos"]
        if any(abs(n["km_aplicado"] - n["km_pedido"]) > 0.010 for n in ns) or len(ns) != 20:
            malos_hoy.append((r["vol"], r["dt"]))
        if any(n["km_pedido"] > TOPE for n in ns):
            malos_tope.append((r["vol"], r["dt"], ns[0]["km_pedido"]))
    print("   records con R: %d | control de hoy marca: %d | con tope de %.0f km marca: %d %s" % (len(con_r), len(malos_hoy), TOPE, len(malos_tope), malos_tope))
    mods = sorted(((r["nulos"][0]["km_pedido"], r["vol"], r["dt"], r.get("n_fill_mxd03", 0)) for r in con_r), reverse=True)
    print("   modulos mayores (km, vol, dt, n_fill):", mods[:5])
    print("   modulo maximo entre records SIN relleno: %.2f km" % max(m for m, _, _, nf in mods if nf == 0))
    nones = [(r["vol"], r["dt"], sum(1 for b in NULOS if r["brazos"].get(b) is None)) for r in con_r if any(r["brazos"].get(b) is None for b in NULOS)]
    print("   records con brazos R None:", nones)


if __name__ == "__main__":
    main()
