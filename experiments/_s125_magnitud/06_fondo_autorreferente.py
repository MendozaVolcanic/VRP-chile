# -*- coding: utf-8 -*-
"""S126 — la prueba del fondo AUTORREFERENTE, y por que G no es igual a E.

MECANISMO PROPUESTO (leido del codigo, process_viirs.py:1729):

    t1_delta_L = np.maximum(t1_L - effective_L_bg, 0.0)

Con ENABLE_TEST1_INTERMEDIATE_BG=True, `effective_L_bg` es la radiancia de la
media del anillo [1,5-3] km. Y los pixeles del Test 1 viven, en su mayoria, en
ESE MISMO anillo. O sea: se mide el exceso de una poblacion contra su propia
media, y el clip a 0 se queda con la mitad de arriba. Sumar esa mitad da una VRP
que crece con la cantidad de pixeles, no con la energia del volcan.

El filtro contextual era lo unico que impedia que ese anillo entrara a la suma.

PREDICCIONES FALSABLES (si el mecanismo es este, tienen que cumplirse las 3):

  P1. En E los pixeles agregados deben ocupar el anillo entero y cortarse justo
      en su borde exterior (3,0 km), con perfil creciente hacia afuera — firma
      de area, no de foco. [ya medido en 05; se re-verifica el corte]
  P2. En G, que apaga el anillo intermedio y vuelve al fondo global 5-25 km (mas
      CALIENTE por el gradiente topografico A69), el mismo clip debe borrar la
      mayoria de esos pixeles frios -> menos pixeles y menos VRP espuria que E.
  P3. El efecto debe escalar con el AREA del anillo disponible, no con la
      actividad: los volcanes con mas pixeles agregados son los que mas inflan.

Si P2 falla, el mecanismo propuesto es falso y hay que buscar otro.

Persiste en 06_fondo_autorreferente.json.
"""
import io, json, math, os, statistics as st, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
VENTANA = ("2026-06-25", "2026-08-24")
BRAZOS = {"control": "_s125_mag_control", "E": "_s125_viirs_e",
          "F": "_s125_viirs_f", "G": "_s125_viirs_g"}
VOLS = {
    "Villarrica":          (-39.420227, -71.939876),
    "PlanchonPeteroa":     (-35.241099, -70.573345),
    "PuyehueCordonCaulle": (-40.525499, -72.146137),
    "Lascar":              (-23.362930, -67.731416),
}
RING = (1.5, 3.0)   # TEST1_INTERMEDIATE_BG_RING_KM


def haversine(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180.0
    h = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


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


res = {"ventana": list(VENTANA), "anillo_km": list(RING), "por_brazo": {},
       "por_volcan": {}, "predicciones": {}}
tot = defaultdict(lambda: defaultdict(float))

print("EL FONDO AUTORREFERENTE — anillo intermedio [%.1f, %.1f] km" % RING)
print("VIIRS375 nocturno, %s a %s\n" % VENTANA)
print("%-8s %10s %10s %12s %12s %10s" %
      ("brazo", "px/pasada", "% en el", "VRP cluster", "VRP escena", "% px"))
print("%-8s %10s %10s %12s %12s %10s" %
      ("", "(mediana)", "anillo", "mediana MW", "mediana MW", ">1.5km"))
print("-" * 68)

datos = {}
for nom, sub in BRAZOS.items():
    if not os.path.isdir(os.path.join(ROOT, "data", sub)):
        continue
    datos[nom] = {v: cargar(sub, v) for v in VOLS}

comunes = {v: set.intersection(*[set(datos[n][v]) for n in datos]) for v in VOLS}

for nom in datos:
    npx, vpc, vsc, en_anillo, mas15 = [], [], [], [], []
    for vol, vent in VOLS.items():
        for k in sorted(comunes[vol]):
            r = datos[nom][vol][k]
            ap = r.get("anomaly_pixels") or []
            pc = r.get("primary_cluster") or {}
            if not pc.get("vrp_mw"):
                continue
            npx.append(len(ap))
            vpc.append(pc["vrp_mw"])
            vsc.append(sum((p.get("vrp_mw") or 0) for p in ap))
            ds = [haversine((p["lat"], p["lon"]), vent) for p in ap]
            if ds:
                en_anillo.append(100 * sum(1 for d in ds if RING[0] <= d <= RING[1]) / len(ds))
                mas15.append(100 * sum(1 for d in ds if d > RING[0]) / len(ds))
    res["por_brazo"][nom] = {
        "n_pasadas": len(npx),
        "px_por_pasada_mediana": round(st.median(npx), 1) if npx else None,
        "px_por_pasada_total": sum(npx),
        "pct_px_en_el_anillo": round(st.median(en_anillo), 1) if en_anillo else None,
        "pct_px_mas_de_1_5km": round(st.median(mas15), 1) if mas15 else None,
        "vrp_cluster_mediana": round(st.median(vpc), 4) if vpc else None,
        "vrp_escena_mediana": round(st.median(vsc), 4) if vsc else None,
    }
    d = res["por_brazo"][nom]
    print("%-8s %10s %9s%% %12s %12s %9s%%" %
          (nom, d["px_por_pasada_mediana"], d["pct_px_en_el_anillo"],
           d["vrp_cluster_mediana"], d["vrp_escena_mediana"], d["pct_px_mas_de_1_5km"]))

# --- P2: G contra E, el mismo clip con fondo global (mas caliente) ---
print("\n" + "=" * 68)
print("P2 — G (fondo global 5-25 km) contra E (fondo del propio anillo)")
if "E" in datos and "G" in datos:
    e, g = res["por_brazo"]["E"], res["por_brazo"]["G"]
    ratio_px = g["px_por_pasada_total"] / e["px_por_pasada_total"] if e["px_por_pasada_total"] else None
    ratio_vrp = g["vrp_cluster_mediana"] / e["vrp_cluster_mediana"] if e["vrp_cluster_mediana"] else None
    res["predicciones"]["P2"] = {
        "px_G_sobre_E": round(ratio_px, 3) if ratio_px else None,
        "vrp_G_sobre_E": round(ratio_vrp, 3) if ratio_vrp else None,
        "cumple": bool(ratio_px is not None and ratio_px < 1.0),
    }
    print("  pixeles totales   G/E = %.3f" % ratio_px)
    print("  VRP cluster mediana G/E = %.3f" % ratio_vrp)
    print("  P2 %s — el fondo mas caliente %s pixeles de la suma"
          % ("SE CUMPLE" if ratio_px < 1 else "FALLA",
             "borra" if ratio_px < 1 else "NO borra"))

# --- P3: el efecto escala con el area disponible, no con la actividad ---
print("\n" + "=" * 68)
print("P3 — ?el aumento escala con la cantidad de pixeles agregados?")
print("%-22s %12s %14s" % ("volcan", "px agregados", "ratio E/control"))
puntos = []
for vol, vent in VOLS.items():
    add, ratios = 0, []
    for k in sorted(comunes[vol]):
        rc, re_ = datos["control"][vol][k], datos["E"][vol][k]
        px_c = {(round(p["lat"], 5), round(p["lon"], 5))
                for p in (rc.get("anomaly_pixels") or [])}
        add += sum(1 for p in (re_.get("anomaly_pixels") or [])
                   if (round(p["lat"], 5), round(p["lon"], 5)) not in px_c)
        vc = (rc.get("primary_cluster") or {}).get("vrp_mw") or 0
        ve = (re_.get("primary_cluster") or {}).get("vrp_mw") or 0
        if vc and ve:
            ratios.append(ve / vc)
    m = round(st.median(ratios), 3) if ratios else None
    res["por_volcan"][vol] = {"px_agregados": add, "ratio_mediano_E_control": m}
    puntos.append((add, m))
    print("%-22s %12d %14s" % (vol, add, m))

ok = all(a[1] >= b[1] for a, b in zip(sorted(puntos, reverse=True),
                                      sorted(puntos, reverse=True)[1:])
         if a[1] is not None and b[1] is not None)
res["predicciones"]["P3"] = {"monotona": bool(ok)}
print("  P3 %s: el orden por pixeles agregados %s el orden por inflado"
      % ("SE CUMPLE" if ok else "FALLA", "coincide con" if ok else "no coincide con"))

dest = os.path.join(os.path.dirname(__file__), "06_fondo_autorreferente.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
