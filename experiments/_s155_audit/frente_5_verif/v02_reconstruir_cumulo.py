# -*- coding: utf-8 -*-
"""Verificador F5, paso 2: separar SELECCION de cumulo y MODO DE UN PIXEL, pasada por pasada.

Metodo (no reconstruye la conectividad a mano): el cumulo primario se identifica EXACTAMENTE
buscando entre los anomaly_pixels el subconjunto de n_pixels cuyo centroide (media de lat/lon,
redondeada a 5 decimales como en el codigo) coincide con primary_cluster.centroid_lat/lon. Si
hay 0 o >1 subconjuntos que calzan, la pasada queda AMBIGUA y no se cuenta.
Despues: suma_cumulo, max_cumulo, otros (pixeles alertados fuera del cumulo), y se verifica
que el valor publicado sea max (single_pixel_mode=True) o suma (False). Si no calza ninguno, la
pasada se marca NO_CALZA (otra etapa: focal MODIS, D9, etc.).

Preguntas del instrumento:
1. Si la identificacion del cumulo estuviera rota, lo veria? Si: se comprueba que el publicado
   reproduzca max o suma del subconjunto encontrado (control interno por pasada).
2. Instrumento muerto: un record sin anomaly_pixels sale SIN_PIXELES, no como perdida 0.
Control positivo: 2026-10-10 06:30 V750 debe dar perdida grande (publicado 4,33 frente a 25,89).
"""
import io, json, math, os, sys, itertools, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
VLAT, VLON = -36.863, -71.377


def hav(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def main():
    pares = json.load(open(os.path.join(AQUI, "pares_remoto.json"), encoding="utf-8"))
    d = json.load(open(os.path.join(AQUI, "..", "..", "..", "data", "mirova_equivalent", "NevadosDeChillan.json"), encoding="utf-8"))
    idx = {(r["datetime_utc"][:16], r["sensor"]): r for r in d["records"]}
    out = []
    print("pasada           sens   zen  n_px clus  pc_n  publ  suma_c max_c  otros  mejor_otro dist_otro_km  modo  mir  sel_x  spm_x  total_x  anchor_ok")
    for f in pares:
        if f["b"] == "VIIRS375" or f["pc_n"] is None:
            continue
        r = idx[(f["t"], f["sensor"])]
        pc = r["primary_cluster"]; ap = r.get("anomaly_pixels") or []
        n = pc["n_pixels"]
        if not ap:
            print(f["t"], "SIN_PIXELES"); continue
        if r.get("n_anomalous_pixels") != len(ap):
            print(f["t"], "AVISO n_anomalous=%s y anomaly_pixels=%d" % (r.get("n_anomalous_pixels"), len(ap)))
        hits = []
        for comb in itertools.combinations(range(len(ap)), n):
            la = round(sum(ap[i]["lat"] for i in comb) / n, 5); lo = round(sum(ap[i]["lon"] for i in comb) / n, 5)
            if abs(la - pc["centroid_lat"]) <= 1.5e-5 and abs(lo - pc["centroid_lon"]) <= 1.5e-5:
                hits.append(comb)
        if len(hits) != 1:
            print(f["t"], f["b"], "AMBIGUA hits=%d" % len(hits)); out.append(dict(t=f["t"], b=f["b"], estado="AMBIGUA")); continue
        comb = hits[0]
        suma_c = sum(ap[i]["vrp_mw"] for i in comb); max_c = max(ap[i]["vrp_mw"] for i in comb)
        otros = [ap[i] for i in range(len(ap)) if i not in comb]
        s_otros = sum(p["vrp_mw"] for p in otros)
        pub = pc["vrp_mw"]
        if abs(pub - round(max_c, 3)) <= 0.0015 and pc.get("single_pixel_mode"):
            modo = "MAX"
        elif abs(pub - round(suma_c, 3)) <= 0.0015:
            modo = "SUMA"
        else:
            modo = "NO_CALZA"
        mejor = max(otros, key=lambda p: p["vrp_mw"]) if otros else None
        d_otro = min(hav(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]) for p in otros) if otros else float("nan")
        # ancla del ranking: el pc.centroid_dist_km se mide desde (vent_lat, vent_lon) del caller
        d_vent = hav(pc["centroid_lat"], pc["centroid_lon"], VLAT, VLON)
        anchor_ok = abs(d_vent - pc["centroid_dist_km"]) < 0.01
        total = suma_c + s_otros
        sel_x = (total / suma_c) if suma_c else float("nan")      # cuanto multiplica sumar los otros cumulos
        spm_x = (suma_c / pub) if pub else float("nan")           # cuanto multiplica sumar en vez de max
        tot_x = (total / pub) if pub else float("nan")
        print("%s %-5s %5.1f %4d %4s %5d %6.2f %6.2f %6.2f %6.2f %8.2f %10.2f %7s %6.2f %5.2f %5.2f %6.2f  %s" % (
            f["t"], "V750" if f["b"] == "VIIRS750" else "MODIS", f["zen"], len(ap), r.get("n_hotspots_clustered"), n, pub, suma_c, max_c,
            s_otros, mejor["vrp_mw"] if mejor else 0, d_otro, modo, f["mir"], sel_x, spm_x, tot_x, anchor_ok))
        out.append(dict(t=f["t"], b=f["b"], zen=f["zen"], pub=pub, suma_c=suma_c, max_c=max_c, otros=s_otros,
                        mejor_otro=mejor["vrp_mw"] if mejor else 0, d_otro=d_otro, modo=modo, mir=f["mir"],
                        sel_x=sel_x, spm_x=spm_x, tot_x=tot_x, n_otros=len(otros), estado="OK",
                        dist_otros_vent=[hav(p["lat"], p["lon"], VLAT, VLON) for p in otros],
                        dist_otros_c=[hav(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]) for p in otros],
                        bt_otros=[p["bt_k"] for p in otros], pc_d=pc["centroid_dist_km"]))
    json.dump(out, open(os.path.join(AQUI, "cumulos.json"), "w", encoding="utf-8"), indent=0)
    for b in ("VIIRS750", "MODIS"):
        ok = [o for o in out if o["b"] == b and o["estado"] == "OK"]
        print("\n== %s: pasadas con cumulo identificado=%d de %d" % (b, len(ok), len([o for o in out if o["b"] == b])))
        from collections import Counter
        print("modo:", Counter(o["modo"] for o in ok))
        afect = [o for o in ok if o["tot_x"] > 1.001]
        print("afectadas (publicado < suma de todo lo alertado): %d" % len(afect))
        print("  solo seleccion (otros>0, modo SUMA): %d" % sum(1 for o in afect if o["otros"] > 0 and o["modo"] == "SUMA"))
        print("  solo max (otros=0, modo MAX): %d" % sum(1 for o in afect if o["otros"] == 0 and o["modo"] == "MAX"))
        print("  ambas: %d" % sum(1 for o in afect if o["otros"] > 0 and o["modo"] == "MAX"))
        print("  otros cumulos con MAS energia que el publicado (mejor_otro > suma_c): %d" % sum(1 for o in afect if o["mejor_otro"] > o["suma_c"]))
        print("  otros cumulos cuya SUMA supera al cumulo: %d" % sum(1 for o in afect if o["otros"] > o["suma_c"]))
        for lo, hi in ((0, 30), (30, 45), (45, 60), (60, 90)):
            e = [o for o in afect if lo <= o["zen"] < hi]
            todos = [o for o in ok if lo <= o["zen"] < hi]
            if todos:
                print("  cenit %2d-%2d: afectadas %d de %d; factor total mediano afectadas=%s" % (
                    lo, hi, len(e), len(todos), ("%.2f" % statistics.median(o["tot_x"] for o in e)) if e else "-"))
        if afect:
            print("  factor total mediano (todas las afectadas) = %.2f" % statistics.median(o["tot_x"] for o in afect))
        ds = [x for o in afect for x in o["dist_otros_c"]]
        if ds:
            print("  distancia de pixeles 'otros' al centroide publicado: min %.2f mediana %.2f max %.2f km (n=%d)" % (min(ds), statistics.median(ds), max(ds), len(ds)))
        dv = [x for o in afect for x in o["dist_otros_vent"]]
        if dv:
            print("  distancia de pixeles 'otros' al crater: max %.2f km (inner=5)" % max(dv))


if __name__ == "__main__":
    main()
