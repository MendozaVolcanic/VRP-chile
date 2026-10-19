# -*- coding: utf-8 -*-
"""Verificador F5, paso 6: geometria de los fragmentos (F5-02) y duplicados de bow-tie (F5-09).

Fisica: dentro de UN barrido de VIIRS dos pixeles vecinos estan separados al menos un paso de muestreo
(I-band ~0,37 km, M-band ~0,74 km en nadir, mas en el borde). Dos centros de pixel mas cerca que eso no
pueden ser vecinos del mismo barrido: son huellas que se SOLAPAN en el terreno, lo que en VIIRS pasa entre
barridos consecutivos (bow-tie). En el arreglo esos dos pixeles quedan separados por las filas que el
L1B borra (Bowtie_Deleted = 65533 -> NaN, pipeline/process_viirs_mod.py:68 y :248), asi que la
conectividad 8 de clustering.py los pone en cumulos distintos aunque en el suelo esten encima.
Segunda prueba, independiente: si la separacion es entre barridos, el desplazamiento entre fragmentos va
a lo largo del VUELO, o sea casi perpendicular al acimut del sensor (que en vista oblicua apunta a lo
ancho del barrido). Se imprime el angulo entre desplazamiento y acimut (0 = a lo ancho, 90 = a lo largo).

Pregunta 1: si los fragmentos fueran fuentes separadas reales, las distancias serian >= 1 paso y el angulo
seria cualquiera: lo veria. Pregunta 2: sin fragmentos, imprime 0 con denominador.
Duplicados: pares de pixeles del MISMO record a menos de la mitad del paso de nadir (I 0,19 km, M 0,37 km);
se reporta cuanta energia de lo publicado cae en el segundo miembro del par.
"""
import io, json, math, os, sys, itertools, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))


def hav(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def rumbo(a, b, c, d):
    y = math.sin(math.radians(d - b)) * math.cos(math.radians(c))
    x = math.cos(math.radians(a)) * math.sin(math.radians(c)) - math.sin(math.radians(a)) * math.cos(math.radians(c)) * math.cos(math.radians(d - b))
    return math.degrees(math.atan2(y, x)) % 360


def identificar(ap, pc):
    n = pc["n_pixels"]
    hits = []
    for comb in itertools.combinations(range(len(ap)), n):
        la = round(sum(ap[i]["lat"] for i in comb) / n, 5); lo = round(sum(ap[i]["lon"] for i in comb) / n, 5)
        if abs(la - pc["centroid_lat"]) <= 1.5e-5 and abs(lo - pc["centroid_lon"]) <= 1.5e-5:
            hits.append(comb)
    return hits[0] if len(hits) == 1 else None


def main():
    pares = json.load(open(os.path.join(AQUI, "pares_remoto.json"), encoding="utf-8"))
    d = json.load(open(os.path.join(AQUI, "..", "..", "..", "data", "mirova_equivalent", "NevadosDeChillan.json"), encoding="utf-8"))
    idx = {(r["datetime_utc"][:16], r["sensor"]): r for r in d["records"]}
    frag = {"VIIRS750": [], "VIIRS375": [], "MODIS": []}
    dup = {"VIIRS750": [0, 0, 0.0, 0.0], "VIIRS375": [0, 0, 0.0, 0.0]}   # records, pares, energia_2do, energia_total
    mitad = {"VIIRS750": 0.37, "VIIRS375": 0.19}
    for f in pares:
        r = idx[(f["t"], f["sensor"])]
        pc, ap = r.get("primary_cluster"), r.get("anomaly_pixels") or []
        if not pc or len(ap) < 2 or len(ap) > 14:
            continue
        comb = identificar(ap, pc)
        if comb is None:
            continue
        az = r.get("sensor_azimuth_deg")
        for i in range(len(ap)):
            if i in comb:
                continue
            j = min(comb, key=lambda j: hav(ap[i]["lat"], ap[i]["lon"], ap[j]["lat"], ap[j]["lon"]))
            dd = hav(ap[i]["lat"], ap[i]["lon"], ap[j]["lat"], ap[j]["lon"])
            ang = abs(((rumbo(ap[j]["lat"], ap[j]["lon"], ap[i]["lat"], ap[i]["lon"]) - az) + 90) % 180 - 90) if az is not None else float("nan")
            frag[f["b"]].append((f["t"], f["zen"], dd, ang, ap[i]["vrp_mw"]))
        if f["b"] in dup:
            ds = dup[f["b"]]
            hubo = False
            for a, b in itertools.combinations(range(len(ap)), 2):
                if hav(ap[a]["lat"], ap[a]["lon"], ap[b]["lat"], ap[b]["lon"]) < mitad[f["b"]]:
                    ds[1] += 1; ds[2] += min(ap[a]["vrp_mw"], ap[b]["vrp_mw"]); hubo = True
            ds[0] += hubo; ds[3] += sum(p["vrp_mw"] for p in ap)
    for b, L in frag.items():
        print("== %s: pixeles fuera del cumulo primario (en records pareados con cumulo identificado): %d" % (b, len(L)))
        for t, z, dd, ang, v in sorted(L, key=lambda x: x[2]):
            print("   %s cenit %4.1f  dist_al_vecino_del_cumulo %.2f km  angulo_con_acimut %5.1f deg  vrp %.2f" % (t, z, dd, ang, v))
        if L:
            print("   mediana dist %.2f km; angulo mediano %.0f deg; con angulo > 60: %d de %d" % (
                statistics.median(x[2] for x in L), statistics.median(x[3] for x in L), sum(1 for x in L if x[3] > 60), len(L)))
    for b, ds in dup.items():
        print("== duplicados %s (<%.2f km): records con par=%d, pares=%d, energia del miembro menor=%.2f MW de %.2f MW guardados (%.1f %%)" % (
            b, mitad[b], ds[0], ds[1], ds[2], ds[3], 100 * ds[2] / ds[3] if ds[3] else 0))


if __name__ == "__main__":
    main()
