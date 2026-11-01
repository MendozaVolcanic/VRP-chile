# S159 frente M: arma la poblacion del probe de geolocalizacion MODIS (MxD03 contra _interp_geo).
# Lee data/mirova_equivalent/<volcan>.json (solo lectura) y escribe objetivos.json en esta carpeta.
#
# POR QUE. R2-2 y S151 dicen que _interp_geo corre los pixeles MODIS hacia el nadir, mas de un lado del
# barrido que del otro. La pregunta del frente es si eso cambia lo que se publica (clase summit/far, fondo,
# magnitud). Hace falta una poblacion donde el efecto pueda verse (cenit alto, lado del frame 0) y otra
# donde no deberia (lado contrario, cerca del nadir), para que una diferencia entre ellas no sea ruido.
#
# Lado del barrido: regla empirica de los 7 granulos de S151 (resultado/probe_mod03.json), 7 de 7:
# frame 0 del lado del volcan  <=>  (Aqua y SensorAzimuth > 0) o (Terra y SensorAzimuth < 0).
# El probe la comprueba despues con el frame real del pixel del crater.
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
TIER_A = ("Lascar Lastarria Isluga Tupungatito PlanchonPeteroa NevadosDeChillan Copahue Llaima "
          "Villarrica PuyehueCordonCaulle Chaiten").split()


def lado(r):
    az = r.get("sensor_azimuth_deg")
    if az is None:
        return None
    s = r["sensor"]
    return "f0" if ((s == "MODIS_AQUA" and az > 0) or (s == "MODIS_TERRA" and az < 0)) else "otro"


def repartir(filas, n):
    """Hasta n filas repartidas por volcan (ronda) y espaciadas en el tiempo dentro de cada volcan."""
    por = {}
    for f in sorted(filas, key=lambda f: f["datetime_utc"]):
        por.setdefault(f["volcan"], []).append(f)
    cupo = {v: 0 for v in por}  # cupos por ronda entre volcanes
    while sum(cupo.values()) < min(n, len(filas)):
        for v in sorted(por):
            if cupo[v] < len(por[v]) and sum(cupo.values()) < n:
                cupo[v] += 1
    out = []
    for v in sorted(por):  # m filas espaciadas en el tiempo: indices (i + 0,5) * len / m
        l, m = por[v], cupo[v]
        out += [l[int((i + 0.5) * len(l) / m)] for i in range(m)]
    return out


def main():
    filas = []
    for v in TIER_A:
        for r in json.load(open(RAIZ / "data" / "mirova_equivalent" / f"{v}.json", encoding="utf-8"))["records"]:
            if not r.get("sensor", "").startswith("MODIS"):
                continue
            pc = r.get("primary_cluster") or {}
            filas.append({
                "volcan": v, "granulo": r["granule"], "datetime_utc": r["datetime_utc"], "sensor": r["sensor"],
                "cenit": r.get("sensor_zenith_deg"), "acimut": r.get("sensor_azimuth_deg"), "lado": lado(r),
                "distance_class": r.get("distance_class"), "pc_vrp_mw": pc.get("vrp_mw"),
                "pc_centroid_dist_km": pc.get("centroid_dist_km"), "t_bg_k": r.get("t_bg_k"),
                "codigo_sha": (r.get("regimen") or {}).get("codigo_sha"),
            })
    con = [f for f in filas if f["cenit"] is not None and f["lado"] is not None]
    s1 = [f for f in con if f["distance_class"] == "summit" and f["lado"] == "f0" and f["cenit"] > 40]
    s2 = repartir([f for f in con if f["distance_class"] == "summit" and f["lado"] == "otro" and f["cenit"] > 40], 25)
    s3 = (repartir([f for f in con if f["distance_class"] == "summit" and f["lado"] == "f0" and f["cenit"] < 10], 4)
          + repartir([f for f in con if f["distance_class"] == "summit" and f["lado"] == "otro" and f["cenit"] < 10], 4))
    s4 = repartir([f for f in con if f["distance_class"] == "far" and f["lado"] == "f0" and f["cenit"] > 40], 12)
    chillan = [f for f in filas if f["volcan"] == "NevadosDeChillan"
               and f["datetime_utc"] in ("2026-10-12 07:20", "2026-10-15 01:05") and f["sensor"].startswith("MODIS")]
    lascar_ctrl = [f for f in filas if f["volcan"] == "Lascar" and ".A2026073.0705." in f["granulo"]]
    estratos = [("S1_summit_f0_mas40", s1), ("S2_summit_otro_mas40", s2), ("S3_summit_nadir_menos10", s3),
                ("S4_far_f0_mas40", s4), ("S5_chillan_864", chillan), ("S6_control_lascar_s151", lascar_ctrl)]
    objetivos, vistos = [], set()
    for nombre, l in estratos:
        for f in l:
            k = (f["volcan"], f["granulo"])
            if k in vistos:
                continue
            vistos.add(k)
            objetivos.append(dict(f, estrato=nombre))
        print(nombre, len(l), file=sys.stderr)
    print("universo MODIS Tier A (todas las fechas):", len(filas), "con clase:",
          sum(1 for f in filas if f["distance_class"]), file=sys.stderr)
    print("total objetivos:", len(objetivos), "granulos distintos:",
          len({o["granulo"] for o in objetivos}), file=sys.stderr)
    json.dump(objetivos, open(AQUI / "objetivos.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
