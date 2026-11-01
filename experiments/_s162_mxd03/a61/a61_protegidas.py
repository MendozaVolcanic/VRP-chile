# -*- coding: utf-8 -*-
"""Auditoria espacial A61 de las protegidas cuyo cumulo se mueve con MxD03 (S162, §6 P4 del pre-registro).

Pregunta: ¿el cumulo de X (MxD03) es el MISMO calor que el de K (`_interp_geo`), reubicado, o se fue a otro objeto?
Para cada protegida (alerta de MIROVA de 1 MW o mas) que K publica:
  - posicion del cumulo primario en K y en X (lat, lon, distancia y acimut desde el crater, dentro o fuera del inner);
  - el vector K->X comparado con el corrimiento del granulo en el pixel del crater (`desplazamiento` = interp menos
    MxD03): si el cumulo son los mismos pixeles, X = K menos ese vector, residuo ~0;
  - numero de pixeles y VRP del cumulo en K y X; el pixel mas caliente por indice (`pico.pos_centro`) en las dos
    grillas y si coincide con el centroide del cumulo;
  - que dice MIROVA (VRP y `Distancia_km`, cuantizada y sin acimut) y si es compatible con K o con X;
  - la fuente independiente de la noche (A109): VIIRS 375 de otros granulos, nivel estricto de la vara, con la
    distancia de K y de X a ese objeto;
  - fragilidad: cuantas de las 20 traslaciones R apagan la publicacion.

Las dos preguntas del instrumento:
1. Si el cumulo de X se hubiera ido a otro objeto, ¿esto lo veria? Si: el residuo K->X menos el corrimiento del
   granulo saldria de kilometros, el numero de pixeles cambiaria y la distancia al objeto VIIRS crecerIa. Control
   positivo: los 17 records con cambio de publicacion K->X tienen residuos grandes (se imprimen).
2. Si el instrumento estuviera muerto (brazo X igual a K), ¿se veria distinto? Si: todos los vectores K->X darian 0
   y el hash de grilla seria el mismo (se comprueba que difiere en las 48).
Denominador: las 48 protegidas con cumulo en K y en X, de las 50 de la ventana 2026-03-01 a 2026-10-16.
"""
import collections
import csv
import io
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cargar_a61 import (NULOS, cargar_artefactos, cargar_poblacion, cargar_referencia, cargar_vara, haversine_km,  # noqa: E402
                        ne_km, parear, punto_cardinal, rumbo)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
COMPAT_KM = 1.5   # `Distancia_km` de MIROVA: una celda de ~1 km mas medio pixel (pre-registro §7)


def pos(b):
    return (b["pc_lat"], b["pc_lon"]) if b and b.get("pc_lat") is not None else None


def main():
    ok, cab, pies = cargar_artefactos()
    pob, pobf = cargar_poblacion()
    ref = cargar_referencia(pob)
    vara, vmeta = cargar_vara()
    print("artefactos: %d records ok en %d cabeceras; referencia MODIS congelada: %d filas (sha %s / %s)" % (
        len(ok), len(cab), len(ref), ref[0]["sha"], next(f["sha"] for f in ref if f["src"] == "OCR")))
    prot = [r for r in ok if r["lab"] == "protegida"]
    prot_k = [r for r in prot if r["pub"]["K"] == 1]
    con_cumulo = [r for r in prot_k if pos(r["brazos"]["K"]) and pos(r["brazos"]["X"])]
    print("protegidas: %d | K publica: %d | con cumulo en K y en X: %d | hash X != K en: %d" % (
        len(prot), len(prot_k), len(con_cumulo), sum(1 for r in con_cumulo if r["hash_grilla"]["X"] != r["hash_grilla"]["K"])))
    sin = [(r["vol"], r["dt"]) for r in prot if r["pub"]["K"] == 0]
    print("protegidas que K no publica (fuera de esta auditoria):", sin)

    filas = []
    for r in sorted(con_cumulo, key=lambda r: (r["vol"], r["dt"])):
        K, X = r["brazos"]["K"], r["brazos"]["X"]
        vlat, vlon = r["vent"]
        inner = r["inner"]
        d = r["desplazamiento"]
        pk, px = pos(K), pos(X)
        dk, dx = haversine_km(vlat, vlon, *pk), haversine_km(vlat, vlon, *px)
        azk, azx = rumbo(vlat, vlon, *pk), rumbo(vlat, vlon, *px)
        # vector K -> X y el esperado si son los mismos pixeles: X = K - (interp - MxD03)
        mn, me = ne_km(pk[0], pk[1], px[0], px[1])
        rn, re_ = mn + d["dn_km"], me + d["de_km"]
        residuo = math.hypot(rn, re_)
        # pico por indice
        pico = r.get("pico") or {}
        pc = (pico.get("pos_centro") or {})
        pico_c, pico_m = pc.get("C"), pc.get("M")
        pico_k_igual = haversine_km(pk[0], pk[1], *pico_c) if pico_c else None
        pico_x_igual = haversine_km(px[0], px[1], *pico_m) if pico_m else None
        d_pico_c = haversine_km(vlat, vlon, *pico_c) if pico_c else None
        d_pico_m = haversine_km(vlat, vlon, *pico_m) if pico_m else None
        # MIROVA
        pares = parear(ref, r["vol"], r["dt"])
        alertas = [f for f in pares if f["tipo"].startswith("ALERTA") and f["tipo"] != "ALERTA_SIN_GEOMETRIA_OCR"]
        vrp_m = max((f["vrp"] or 0) for f in alertas) if alertas else None
        dists_m = sorted({f["dist"] for f in alertas if f["dist"] is not None})
        comp_k = any(abs(dk - dm) <= COMPAT_KM for dm in dists_m) if dists_m else None
        comp_x = any(abs(dx - dm) <= COMPAT_KM for dm in dists_m) if dists_m else None
        # VIIRS de la noche (vara estricta; si no hay, amplia)
        vv = vara.get("%s|%s" % (r["vol"], r["clave"]))
        nivel, vp = None, []
        if vv:
            for nv in ("estricta", "amplia"):
                if vv[nv]["pasadas"]:
                    nivel, vp = nv, vv[nv]["pasadas"]
                    break
        if vp:
            vlat_m = statistics.median(p["lat"] for p in vp)
            vlon_m = statistics.median(p["lon"] for p in vp)
            d_v_vent = haversine_km(vlat, vlon, vlat_m, vlon_m)
            d_k_v = haversine_km(pk[0], pk[1], vlat_m, vlon_m)
            d_x_v = haversine_km(px[0], px[1], vlat_m, vlon_m)
            disp_v = max(haversine_km(vlat_m, vlon_m, p["lat"], p["lon"]) for p in vp)
        else:
            d_v_vent = d_k_v = d_x_v = disp_v = None
        r_apagan = [b for b in NULOS if r["r_nulos"] and r["pub"].get(b) == 0]
        filas.append({
            "vol": r["vol"], "dt": r["dt"], "sat": r["sensor"].replace("MODIS_", ""), "z": r["z"], "lado": r["lado"],
            "frame_crater": d["frame"], "linea_crater": d["linea"], "inner_km": inner,
            "desp_granulo_km": d["km"], "desp_dn": d["dn_km"], "desp_de": d["de_km"],
            "K_lat": pk[0], "K_lon": pk[1], "K_dist": round(dk, 3), "K_az": round(azk), "K_rumbo": punto_cardinal(azk),
            "K_in": dk <= inner, "K_dc": K["dc"], "K_vrp": K["pc_vrp"], "K_npx": K["pc_n_pixels"], "K_nanom": K["n_anom"],
            "X_lat": px[0], "X_lon": px[1], "X_dist": round(dx, 3), "X_az": round(azx), "X_rumbo": punto_cardinal(azx),
            "X_in": dx <= inner, "X_dc": X["dc"], "X_vrp": X["pc_vrp"], "X_npx": X["pc_n_pixels"], "X_nanom": X["n_anom"],
            "mov_km": round(math.hypot(mn, me), 3), "mov_az": round(math.degrees(math.atan2(me, mn)) % 360),
            "residuo_km": round(residuo, 3), "acerca_km": round(dk - dx, 3),
            "pico_exceso": pico.get("exceso"), "pico_C_dist": None if d_pico_c is None else round(d_pico_c, 3),
            "pico_M_dist": None if d_pico_m is None else round(d_pico_m, 3),
            "pico_es_pcK": None if pico_k_igual is None else pico_k_igual < 0.05,
            "pico_es_pcX": None if pico_x_igual is None else pico_x_igual < 0.05,
            "mirova_vrp": vrp_m, "mirova_dist": dists_m, "mirova_filas": len(alertas), "mirova_src": sorted({f["src"] for f in alertas}),
            "compat_K": comp_k, "compat_X": comp_x,
            "viirs_nivel": nivel, "viirs_n": len(vp), "viirs_dist_vent": None if d_v_vent is None else round(d_v_vent, 3),
            "viirs_disp": None if disp_v is None else round(disp_v, 3),
            "K_a_viirs": None if d_k_v is None else round(d_k_v, 3), "X_a_viirs": None if d_x_v is None else round(d_x_v, 3),
            "r_apagan": len(r_apagan), "r_nulos": r["r_nulos"],
            "t_bg_K": K["t_bg_k"], "t_bg_X": X["t_bg_k"], "n_fill": r.get("n_fill_mxd03", 0),
        })

    # ---------------------------------------------------------------- tabla
    cols = list(filas[0].keys())
    with open(AQUI / "a61_protegidas.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for f in filas:
            w.writerow(f)
    print("\n== TABLA (una fila por protegida; csv completo en a61_protegidas.csv)")
    print("vol dt sat | z lado frame | K: dist az rumbo in dc vrp npx | X: dist az rumbo in dc vrp npx | mov km az | desp gran km | residuo | MIROVA vrp dist compK compX | VIIRS n d_vent K->v X->v | R apagan")
    for f in filas:
        print("%s %s %s | %4.1f %s %4d | K %.2f %3d %-2s %s %s %.3f %s | X %.2f %3d %-2s %s %s %.3f %s | mov %.2f %3d | gran %.2f | res %.2f | M %s %s %s %s | V %s %s %s %s %s | R %d" % (
            f["vol"][:7], f["dt"], f["sat"][:1], f["z"], f["lado"], f["frame_crater"],
            f["K_dist"], f["K_az"], f["K_rumbo"], "in " if f["K_in"] else "OUT", f["K_dc"], f["K_vrp"], f["K_npx"],
            f["X_dist"], f["X_az"], f["X_rumbo"], "in " if f["X_in"] else "OUT", f["X_dc"], f["X_vrp"], f["X_npx"],
            f["mov_km"], f["mov_az"], f["desp_granulo_km"], f["residuo_km"],
            f["mirova_vrp"], f["mirova_dist"], f["compat_K"], f["compat_X"],
            f["viirs_nivel"], f["viirs_n"], f["viirs_dist_vent"], f["K_a_viirs"], f["X_a_viirs"], f["r_apagan"]))

    # ---------------------------------------------------------------- agregados
    n = len(filas)
    print("\n== AGREGADOS (n = %d protegidas con cumulo)" % n)
    acerca = [f["acerca_km"] for f in filas]
    print("X mas cerca del crater que K: %d de %d | acercamiento mediana %.2f km, min %.2f, max %.2f" % (
        sum(1 for a in acerca if a > 0), n, statistics.median(acerca), min(acerca), max(acerca)))
    print("dentro del inner: K %d de %d | X %d de %d | clase K->X cambia en %d" % (
        sum(f["K_in"] for f in filas), n, sum(f["X_in"] for f in filas), n, sum(1 for f in filas if f["K_dc"] != f["X_dc"])))
    print("K dist mediana %.2f km (p10 %.2f, p90 %.2f) | X dist mediana %.2f km (p10 %.2f, p90 %.2f)" % (
        statistics.median(f["K_dist"] for f in filas), sorted(f["K_dist"] for f in filas)[n // 10], sorted(f["K_dist"] for f in filas)[9 * n // 10],
        statistics.median(f["X_dist"] for f in filas), sorted(f["X_dist"] for f in filas)[n // 10], sorted(f["X_dist"] for f in filas)[9 * n // 10]))
    res = [f["residuo_km"] for f in filas]
    print("residuo (K->X menos el corrimiento del granulo en el pixel del crater): mediana %.3f km, p90 %.3f, max %.3f | < 0,3 km: %d de %d | < 1 km: %d" % (
        statistics.median(res), sorted(res)[9 * n // 10], max(res), sum(1 for x in res if x < 0.3), n, sum(1 for x in res if x < 1.0)))
    mism = sum(1 for f in filas if f["K_npx"] == f["X_npx"])
    print("mismo numero de pixeles en el cumulo K y X: %d de %d | n_anom igual: %d | pixeles del cumulo K: %s" % (
        mism, n, sum(1 for f in filas if f["K_nanom"] == f["X_nanom"]), dict(collections.Counter(f["K_npx"] for f in filas))))
    print("el pixel mas caliente por indice ES el centroide del cumulo: en K %d de %d, en X %d de %d (los cumulos de 1 pixel)" % (
        sum(1 for f in filas if f["pico_es_pcK"]), n, sum(1 for f in filas if f["pico_es_pcX"]), n))
    print("acimut del cumulo desde el crater, K: %s | X: %s" % (
        dict(collections.Counter(f["K_rumbo"] for f in filas)), dict(collections.Counter(f["X_rumbo"] for f in filas))))
    print("acimut del movimiento K->X: %s | lado del barrido: %s" % (
        dict(collections.Counter(punto_cardinal(f["mov_az"]) for f in filas)), dict(collections.Counter(f["lado"] for f in filas))))
    vk = [f for f in filas if f["mirova_dist"]]
    print("MIROVA `Distancia_km` disponible en %d de %d | compatible (±%.1f km) con K: %d, con X: %d, con ninguno: %d, con los dos: %d" % (
        len(vk), n, COMPAT_KM, sum(1 for f in vk if f["compat_K"]), sum(1 for f in vk if f["compat_X"]),
        sum(1 for f in vk if not f["compat_K"] and not f["compat_X"]), sum(1 for f in vk if f["compat_K"] and f["compat_X"])))
    print("   valores de Distancia_km de MIROVA en las protegidas:", dict(collections.Counter(dm for f in vk for dm in f["mirova_dist"])))
    vv = [f for f in filas if f["viirs_n"]]
    est = [f for f in vv if f["viirs_nivel"] == "estricta"]
    print("VIIRS de la noche (otro granulo, A109): con referencia %d de %d (estricta %d, amplia %d) | X mas cerca del objeto VIIRS que K: %d de %d (estricta %d de %d)" % (
        len(vv), n, len(est), len(vv) - len(est), sum(1 for f in vv if f["X_a_viirs"] < f["K_a_viirs"]), len(vv),
        sum(1 for f in est if f["X_a_viirs"] < f["K_a_viirs"]), len(est)))
    if vv:
        print("   distancia al objeto VIIRS: K mediana %.2f km, X mediana %.2f km | objeto VIIRS al crater mediana %.2f km, dispersion mediana %.2f km" % (
            statistics.median(f["K_a_viirs"] for f in vv), statistics.median(f["X_a_viirs"] for f in vv),
            statistics.median(f["viirs_dist_vent"] for f in vv), statistics.median(f["viirs_disp"] for f in vv)))
        lejos = [f for f in vv if f["X_a_viirs"] > 1.5]
        print("   X a mas de 1,5 km del objeto VIIRS: %d" % len(lejos), [(f["vol"], f["dt"], f["X_a_viirs"], f["K_a_viirs"]) for f in lejos])
    fr = [f for f in filas if f["r_apagan"]]
    print("fragiles (alguna R apaga la publicacion): %d de %d con R" % (len(fr), sum(1 for f in filas if f["r_nulos"])),
          [(f["vol"], f["dt"], f["r_apagan"]) for f in fr])
    print("por volcan:", dict(collections.Counter(f["vol"] for f in filas)), "| por satelite:", dict(collections.Counter(f["sat"] for f in filas)))
    print("cenit: mediana %.1f, max %.1f | >35: %d" % (statistics.median(f["z"] for f in filas), max(f["z"] for f in filas), sum(1 for f in filas if f["z"] > 35)))

    # ---------------------------------------------------------------- control positivo: los records con cambio de publicacion
    print("\n== CONTROL POSITIVO: residuo y pixeles en los records con cambio de publicacion K->X (el instrumento ve cuando el cumulo cambia)")
    camb = [r for r in ok if r["pub"]["K"] != r["pub"]["X"]]
    for r in camb:
        K, X = r["brazos"]["K"], r["brazos"]["X"]
        pk, px = pos(K), pos(X)
        d = r["desplazamiento"]
        if pk and px:
            mn, me = ne_km(pk[0], pk[1], px[0], px[1])
            res = math.hypot(mn + d["dn_km"], me + d["de_km"])
            txt = "residuo %.2f km | npx K/X %s/%s | dist K/X %.2f/%.2f" % (res, K["pc_n_pixels"], X["pc_n_pixels"],
                                                                         haversine_km(r["vent"][0], r["vent"][1], *pk), haversine_km(r["vent"][0], r["vent"][1], *px))
        else:
            txt = "cumulo solo en %s | npx K/X %s/%s" % ("K" if pk else "X", K["pc_n_pixels"], X["pc_n_pixels"])
        print("   %s %s %s z=%.1f pub K/X %d/%d | %s" % (r["vol"], r["dt"], r["lab"], r["z"], r["pub"]["K"], r["pub"]["X"], txt))
    # nulo del residuo: los 158 movidos (todos los records con cumulo en K y X)
    todos = [r for r in ok if pos(r["brazos"]["K"]) and pos(r["brazos"]["X"])]
    rr = []
    for r in todos:
        pk, px = pos(r["brazos"]["K"]), pos(r["brazos"]["X"])
        d = r["desplazamiento"]
        mn, me = ne_km(pk[0], pk[1], px[0], px[1])
        rr.append((math.hypot(mn + d["dn_km"], me + d["de_km"]), r))
    rr.sort(key=lambda x: -x[0])
    print("\n== residuo en TODOS los records con cumulo en K y X (n = %d): mediana %.3f km, p90 %.3f, > 1 km: %d, > 3 km: %d" % (
        len(rr), statistics.median(x for x, _ in rr), sorted(x for x, _ in rr)[9 * len(rr) // 10],
        sum(1 for x, _ in rr if x > 1), sum(1 for x, _ in rr if x > 3)))
    for x, r in rr[:8]:
        print("   %.2f km | %s %s %s z=%.1f npx K/X %s/%s pub %d/%d" % (x, r["vol"], r["dt"], r["lab"], r["z"],
              r["brazos"]["K"]["pc_n_pixels"], r["brazos"]["X"]["pc_n_pixels"], r["pub"]["K"], r["pub"]["X"]))


if __name__ == "__main__":
    main()
