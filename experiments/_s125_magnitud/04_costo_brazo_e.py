# -*- coding: utf-8 -*-
"""S125/S126 — cuanto RUIDO destapa apagar el filtro contextual (brazo E).

El filtro `enable_test1_contextual_filter` se adopto para cortar el HALO NIVAL:
los pixeles tibios sobre nieve alrededor del crater, que no son anomalos contra
sus vecinos inmediatos. Apagarlo lleva la magnitud de VIIRS375 de 0,600 a 1,043
(paridad), pero la senal de alarma es el p75: 0,878 -> 2,684. La mediana mejoro
y la cola alta se disparo. Este script mide si esa cola es el halo volviendo.

Que se mide (todo sobre la INTERSECCION de pasadas control/E, nunca conteos de
series sueltas), estratificado por REGIMEN termico:

  · deteccion: pasadas nuevas en E, pasadas perdidas, y a que distancia del
    crater cae el centroide de las nuevas.
  · pixeles: n_pixels por cluster y % de clusters de 1 solo pixel, antes/despues.
  · espacial: los pixeles que E AGREGA, su distancia al crater y su contraste
    termico contra el fondo de esa misma noche. Si el halo vuelve, los agregados
    son tibios (bt cerca de t_bg) y estan en una corona, no en el crater.
  · falsos positivos: noches donde detectamos y MIROVA no publico, control vs E.
  · magnitud: ratio pareado E/control noche a noche.

Reglas: pc.vrp_mw nunca record.vrp_mw (A10) · interseccion de pasadas ·
ground truth CONS union OCR con alias completo (A11/A14) · solo pasadas
NOCTURNAS, las alertas diurnas de MIROVA son artefacto solar (A76) · numeros
persistidos, ninguno transcrito a mano (S91).

Persiste en 04_costo_brazo_e.json.
"""
import csv, io, json, math, os, statistics as st, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
CONTROL, BRAZO = "_s125_mag_control", "_s125_viirs_e"
VENTANA = ("2026-06-25", "2026-08-24")

# Regimen termico: en los nevados el halo nival es el riesgo que el filtro vino
# a cubrir; en el desierto de altura no hay halo que cortar y el filtro no
# deberia estar haciendo nada. Si el dano se concentra en los nevados, es el
# halo; si es parejo, es otro mecanismo.
VOLS = {
    "Villarrica":          {"regimen": "nevado",   "vent": (-39.420227, -71.939876), "inner": 5},
    "PlanchonPeteroa":     {"regimen": "nevado",   "vent": (-35.241099, -70.573345), "inner": 3},
    "PuyehueCordonCaulle": {"regimen": "nevado",   "vent": (-40.525499, -72.146137), "inner": 20},
    "Lascar":              {"regimen": "desierto", "vent": (-23.362930, -67.731416), "inner": 5},
}
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
}
SENSOR_MAP = {"VIIRS375": "v375", "VIIRS": "v750", "MODIS": "modis"}


def bucket(s):
    s = (s or "").upper()
    if "MODIS" in s:
        return "modis"
    if "750" in s:
        return "v750"
    if "VIIRS" in s:
        return "v375"
    return None


def haversine(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180.0
    h = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def q(xs, f):
    if not xs:
        return None
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(f * len(xs)))], 3)


def resumen(xs):
    if not xs:
        return None
    return {"n": len(xs), "mediana": round(st.median(xs), 3),
            "p25": q(xs, .25), "p75": q(xs, .75), "max": round(max(xs), 3)}


def cargar_mirova():
    """Noches con ALERTA de MIROVA, por volcan y sensor. Solo nocturnas (A76)."""
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
            b = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
            fecha = (r.get("Fecha_Satelite_UTC") or "")
            if not b or not (VENTANA[0] <= fecha[:10] <= VENTANA[1]):
                continue
            if not (3 <= int(fecha[11:13] or 12) <= 9):   # diurna: artefacto solar
                continue
            out[vol].add((fecha[:10], b))
    return out


def cargar(subdir, vol):
    """Records VIIRS375 NOCTURNOS de la ventana, indexados por pasada."""
    p = os.path.join(ROOT, "data", subdir, vol + ".json")
    recs = json.load(open(p, encoding="utf-8"))["records"]
    out = {}
    for r in recs:
        if bucket(r.get("sensor")) != "v375":
            continue
        if not (VENTANA[0] <= r["datetime_utc"][:10] <= VENTANA[1]):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is not None and sz < 90:      # pasada diurna: el pipeline es night-only
            continue
        out[(r["datetime_utc"], r.get("sensor"))] = r
    return out


mirova = cargar_mirova()
res = {"ventana": list(VENTANA), "control": CONTROL, "brazo": BRAZO,
       "por_volcan": {}, "por_regimen": {}, "global": {}}
acc = defaultdict(lambda: defaultdict(list))

print("COSTO DEL BRAZO E (filtro contextual OFF) — %s a %s" % VENTANA)
print("solo VIIRS375, solo pasadas nocturnas, sobre la interseccion de pasadas\n")

for vol, cfg in VOLS.items():
    c, e = cargar(CONTROL, vol), cargar(BRAZO, vol)
    comunes = sorted(set(c) & set(e))
    reg = cfg["regimen"]

    det_c = [k for k in comunes if (c[k].get("primary_cluster") or {}).get("vrp_mw")]
    det_e = [k for k in comunes if (e[k].get("primary_cluster") or {}).get("vrp_mw")]
    nuevas = sorted(set(det_e) - set(det_c))
    perdidas = sorted(set(det_c) - set(det_e))

    # --- donde caen las detecciones NUEVAS (distancia al crater, no al ancla) ---
    d_nuevas, fuera_inner = [], 0
    for k in nuevas:
        pc = e[k]["primary_cluster"]
        d = haversine((pc["centroid_lat"], pc["centroid_lon"]), cfg["vent"])
        d_nuevas.append(d)
        if d > cfg["inner"]:
            fuera_inner += 1

    # --- pixeles por cluster, antes y despues ---
    npx_c = [(c[k].get("primary_cluster") or {}).get("n_pixels", 0) for k in det_c]
    npx_e = [(e[k].get("primary_cluster") or {}).get("n_pixels", 0) for k in det_e]

    # --- los pixeles que E AGREGA: distancia al crater y contraste contra el fondo ---
    d_agregados, contraste_agregados = [], []
    for k in comunes:
        px_c = {(round(p["lat"], 5), round(p["lon"], 5))
                for p in (c[k].get("anomaly_pixels") or [])}
        tbg = e[k].get("t_bg_k")
        for p in (e[k].get("anomaly_pixels") or []):
            if (round(p["lat"], 5), round(p["lon"], 5)) in px_c:
                continue
            d_agregados.append(haversine((p["lat"], p["lon"]), cfg["vent"]))
            if tbg and p.get("bt_k"):
                contraste_agregados.append(p["bt_k"] - tbg)

    # --- deteccion sin contraparte MIROVA (no "FP": puede ser cat-b real, A54) ---
    noches_mir = mirova.get(vol, set())
    sin_mir_c = sum(1 for k in det_c if (k[0][:10], "v375") not in noches_mir)
    sin_mir_e = sum(1 for k in det_e if (k[0][:10], "v375") not in noches_mir)

    # --- magnitud pareada noche a noche ---
    pareado = []
    for k in set(det_c) & set(det_e):
        vc = c[k]["primary_cluster"]["vrp_mw"]
        ve = e[k]["primary_cluster"]["vrp_mw"]
        if vc:
            pareado.append(ve / vc)

    d = {
        "regimen": reg, "inner_radius_km": cfg["inner"], "pasadas_comunes": len(comunes),
        "detecciones": {"control": len(det_c), "E": len(det_e),
                        "nuevas": len(nuevas), "perdidas": len(perdidas)},
        "nuevas_dist_vent_km": resumen(d_nuevas),
        "nuevas_fuera_del_inner": fuera_inner,
        "n_pixels_cluster": {
            "control": resumen(npx_c), "E": resumen(npx_e),
            "pct_1px_control": round(100 * sum(1 for x in npx_c if x == 1) / len(npx_c), 1) if npx_c else None,
            "pct_1px_E": round(100 * sum(1 for x in npx_e if x == 1) / len(npx_e), 1) if npx_e else None},
        "pixeles_agregados": {
            "n": len(d_agregados), "dist_vent_km": resumen(d_agregados),
            "contraste_bt_menos_tbg_k": resumen(contraste_agregados),
            "pct_dentro_del_inner": round(100 * sum(1 for x in d_agregados if x <= cfg["inner"]) / len(d_agregados), 1) if d_agregados else None},
        "sin_contraparte_mirova": {"control": sin_mir_c, "E": sin_mir_e,
                                   "delta": sin_mir_e - sin_mir_c},
        "ratio_pareado_E_sobre_control": resumen(pareado),
    }
    res["por_volcan"][vol] = d

    for campo, xs in (("d_nuevas", d_nuevas), ("d_agregados", d_agregados),
                      ("contraste", contraste_agregados), ("pareado", pareado),
                      ("npx_c", npx_c), ("npx_e", npx_e)):
        acc[reg][campo] += xs
        acc["TODOS"][campo] += xs
    for campo, v in (("det_c", len(det_c)), ("det_e", len(det_e)),
                     ("nuevas", len(nuevas)), ("perdidas", len(perdidas)),
                     ("fuera_inner", fuera_inner),
                     ("sin_mir_c", sin_mir_c), ("sin_mir_e", sin_mir_e)):
        acc[reg][campo].append(v)
        acc["TODOS"][campo].append(v)

    print("=" * 78)
    print("%s  [%s]  inner=%s km   pasadas comunes: %d" % (vol, reg, cfg["inner"], len(comunes)))
    print("  detecciones      control %4d   E %4d   nuevas +%d   perdidas -%d"
          % (len(det_c), len(det_e), len(nuevas), len(perdidas)))
    if d_nuevas:
        print("  nuevas: dist al crater mediana %.2f km   fuera del inner: %d/%d"
              % (st.median(d_nuevas), fuera_inner, len(nuevas)))
    print("  n_pixels cluster mediana   control %s   E %s    1-pixel: %s%% -> %s%%"
          % (resumen(npx_c)["mediana"] if npx_c else "-",
             resumen(npx_e)["mediana"] if npx_e else "-",
             d["n_pixels_cluster"]["pct_1px_control"], d["n_pixels_cluster"]["pct_1px_E"]))
    if d_agregados:
        print("  pixeles agregados: %d   dist mediana %.2f km   dentro del inner %s%%"
              % (len(d_agregados), st.median(d_agregados),
                 d["pixeles_agregados"]["pct_dentro_del_inner"]))
        if contraste_agregados:
            print("     contraste sobre el fondo: mediana %+.2f K   p75 %+.2f K"
                  % (st.median(contraste_agregados), q(contraste_agregados, .75)))
    print("  sin contraparte MIROVA     control %4d   E %4d   delta %+d"
          % (sin_mir_c, sin_mir_e, sin_mir_e - sin_mir_c))
    if pareado:
        print("  ratio pareado E/control: mediana %.3f   p75 %s   max %.2f"
              % (st.median(pareado), q(pareado, .75), max(pareado)))

for reg in ("nevado", "desierto", "TODOS"):
    a = acc[reg]
    (res["por_regimen"] if reg != "TODOS" else res["global"])[reg] = {
        "detecciones": {"control": sum(a["det_c"]), "E": sum(a["det_e"]),
                        "nuevas": sum(a["nuevas"]), "perdidas": sum(a["perdidas"])},
        "nuevas_fuera_del_inner": sum(a["fuera_inner"]),
        "nuevas_dist_vent_km": resumen(a["d_nuevas"]),
        "pixeles_agregados_dist_km": resumen(a["d_agregados"]),
        "pixeles_agregados_contraste_k": resumen(a["contraste"]),
        "ratio_pareado": resumen(a["pareado"]),
        "sin_contraparte_mirova": {"control": sum(a["sin_mir_c"]), "E": sum(a["sin_mir_e"]),
                                   "delta": sum(a["sin_mir_e"]) - sum(a["sin_mir_c"])},
        "n_pixels_mediana": {"control": resumen(a["npx_c"])["mediana"] if a["npx_c"] else None,
                             "E": resumen(a["npx_e"])["mediana"] if a["npx_e"] else None},
    }

print("\n" + "=" * 78 + "\nPOR REGIMEN")
for reg in ("nevado", "desierto", "TODOS"):
    d = (res["por_regimen"] if reg != "TODOS" else res["global"])[reg]
    print("\n" + reg.upper())
    print("  detecciones control %d -> E %d   (+%d nuevas, -%d perdidas)   fuera del inner: %d"
          % (d["detecciones"]["control"], d["detecciones"]["E"], d["detecciones"]["nuevas"],
             d["detecciones"]["perdidas"], d["nuevas_fuera_del_inner"]))
    print("  pixeles agregados: %s" % (d["pixeles_agregados_dist_km"],))
    print("  contraste de los agregados (K): %s" % (d["pixeles_agregados_contraste_k"],))
    print("  ratio pareado E/control: %s" % (d["ratio_pareado"],))
    print("  sin contraparte MIROVA: %s" % (d["sin_contraparte_mirova"],))

dest = os.path.join(os.path.dirname(__file__), "04_costo_brazo_e.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
