# -*- coding: utf-8 -*-
"""S126 — la particion que decide: lo que E agrega, ?es senal o es halo?

El script 04 mostro que apagar el filtro contextual multiplica la magnitud por
16x en Villarrica, agregando ~26.000 pixeles que estan a 1,5-3 km del crater y
son 6,6 K MAS FRIOS que el fondo. Falta la prueba que separa las dos lecturas
posibles:

  · SENAL: el filtro estaba recortando energia volcanica real. Entonces el
    aumento tiene que concentrarse en las noches que MIROVA confirma, donde hay
    actividad de verdad.
  · HALO: el filtro estaba cortando ruido nival. Entonces el aumento tiene que
    ser IGUAL o MAYOR en las noches sin actividad, porque ahi no hay foco que
    domine la suma y el anillo tibio se la queda entera.

Es el mismo criterio de A83: no basta con que la mediana global mejore; hay que
ver si la mejora viene del lado correcto de la particion.

Se mide ademas cuanta de la VRP nueva aportan los pixeles agregados, y su
distribucion radial, para ver si forman una CORONA (firma del halo) o si se
apinan en el crater (firma del foco).

Persiste en 05_es_halo_o_senal.json.
"""
import csv, io, json, math, os, statistics as st, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
CONTROL, BRAZO = "_s125_mag_control", "_s125_viirs_e"
VENTANA = ("2026-06-25", "2026-08-24")

VOLS = {
    "Villarrica":          {"regimen": "nevado",   "vent": (-39.420227, -71.939876)},
    "PlanchonPeteroa":     {"regimen": "nevado",   "vent": (-35.241099, -70.573345)},
    "PuyehueCordonCaulle": {"regimen": "nevado",   "vent": (-40.525499, -72.146137)},
    "Lascar":              {"regimen": "desierto", "vent": (-23.362930, -67.731416)},
}
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
}


def haversine(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180.0
    h = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def q(xs, f):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(f * len(xs)))], 3) if xs else None


def resumen(xs):
    if not xs:
        return None
    return {"n": len(xs), "mediana": round(st.median(xs), 3),
            "p25": q(xs, .25), "p75": q(xs, .75), "max": round(max(xs), 3)}


def noches_mirova():
    """Fechas con ALERTA nocturna de MIROVA en VIIRS375 (A76: diurnas fuera)."""
    out = defaultdict(set)
    for fname in ("latest_consolidado.csv",
                  "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
        p = os.path.join(ROOT, fname)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            if (r.get("Sensor") or "").strip().upper() != "VIIRS375":
                continue
            f = (r.get("Fecha_Satelite_UTC") or "")
            if not (VENTANA[0] <= f[:10] <= VENTANA[1]):
                continue
            if not (3 <= int(f[11:13] or 12) <= 9):
                continue
            out[vol].add(f[:10])
    return out


def cargar(subdir, vol):
    recs = json.load(open(os.path.join(ROOT, "data", subdir, vol + ".json"),
                          encoding="utf-8"))["records"]
    out = {}
    for r in recs:
        s = (r.get("sensor") or "").upper()
        if "VIIRS" not in s or "750" in s or "MODIS" in s:
            continue
        if not (VENTANA[0] <= r["datetime_utc"][:10] <= VENTANA[1]):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is not None and sz < 90:
            continue
        out[(r["datetime_utc"], r.get("sensor"))] = r
    return out


mir = noches_mirova()
res = {"ventana": list(VENTANA), "por_volcan": {}, "particion_global": {}}
glob = {"conf": [], "noconf": []}
radial_glob = defaultdict(list)
aporte_glob = []

print("?SENAL O HALO? — reparto del aumento del brazo E segun confirme MIROVA")
print("VIIRS375 nocturno, %s a %s, interseccion de pasadas\n" % VENTANA)

for vol, cfg in VOLS.items():
    c, e = cargar(CONTROL, vol), cargar(BRAZO, vol)
    comunes = sorted(set(c) & set(e))
    conf, noconf = [], []
    aporte, radial = [], []

    for k in comunes:
        vc = (c[k].get("primary_cluster") or {}).get("vrp_mw") or 0
        ve = (e[k].get("primary_cluster") or {}).get("vrp_mw") or 0
        if not vc or not ve:
            continue
        r = ve / vc
        (conf if k[0][:10] in mir.get(vol, set()) else noconf).append(r)

        # cuanta VRP aportan los pixeles que E agrega, y donde estan
        px_c = {(round(p["lat"], 5), round(p["lon"], 5))
                for p in (c[k].get("anomaly_pixels") or [])}
        v_add = 0.0
        for p in (e[k].get("anomaly_pixels") or []):
            if (round(p["lat"], 5), round(p["lon"], 5)) in px_c:
                continue
            v_add += p.get("vrp_mw") or 0
            radial.append(haversine((p["lat"], p["lon"]), cfg["vent"]))
        v_tot = sum((p.get("vrp_mw") or 0) for p in (e[k].get("anomaly_pixels") or []))
        if v_tot > 0:
            aporte.append(100 * v_add / v_tot)

    d = {"regimen": cfg["regimen"],
         "ratio_E_control_noches_MIROVA": resumen(conf),
         "ratio_E_control_noches_SIN_MIROVA": resumen(noconf),
         "pct_vrp_de_pixeles_agregados": resumen(aporte),
         "radial_agregados_km": resumen(radial)}
    res["por_volcan"][vol] = d
    glob["conf"] += conf
    glob["noconf"] += noconf
    aporte_glob += aporte
    for x in radial:
        radial_glob[cfg["regimen"]].append(x)

    print("=" * 78)
    print("%s  [%s]" % (vol, cfg["regimen"]))
    print("  ratio E/control en noches que MIROVA CONFIRMA : %s" % (resumen(conf),))
    print("  ratio E/control en noches SIN alerta MIROVA   : %s" % (resumen(noconf),))
    print("  %% de la VRP que aportan los pixeles agregados : %s" % (resumen(aporte),))

res["particion_global"] = {
    "noches_MIROVA": resumen(glob["conf"]),
    "noches_SIN_MIROVA": resumen(glob["noconf"]),
    "pct_vrp_de_pixeles_agregados": resumen(aporte_glob),
}

print("\n" + "=" * 78 + "\nGLOBAL")
print("  noches que MIROVA confirma : %s" % (resumen(glob["conf"]),))
print("  noches SIN alerta MIROVA   : %s" % (resumen(glob["noconf"]),))
print("  %% de la VRP aportado por lo agregado: %s" % (resumen(aporte_glob),))

# perfil radial: ?corona o crater?
print("\nPERFIL RADIAL de los pixeles agregados (km al crater)")
bins = [(0, .5), (.5, 1), (1, 1.5), (1.5, 2), (2, 2.5), (2.5, 3), (3, 99)]
res["perfil_radial"] = {}
for reg, xs in radial_glob.items():
    fila = {}
    print("  %s (n=%d)" % (reg, len(xs)))
    for lo, hi in bins:
        n = sum(1 for x in xs if lo <= x < hi)
        fila["%.1f-%.1f" % (lo, hi)] = n
        if n:
            print("     %4.1f-%4.1f km : %6d  %5.1f%%  %s"
                  % (lo, hi, n, 100 * n / len(xs), "#" * int(60 * n / len(xs))))
    res["perfil_radial"][reg] = fila

dest = os.path.join(os.path.dirname(__file__), "05_es_halo_o_senal.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
