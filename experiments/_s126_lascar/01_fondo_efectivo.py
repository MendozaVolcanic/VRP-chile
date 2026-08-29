# -*- coding: utf-8 -*-
"""S126 — recuperar el fondo que el pipeline USO realmente, invirtiendo Wooster.

Lascar es el sub-reporte que quedo vivo: 0,434 contra MIROVA, el 45 % de los pares
de la muestra, y ninguno de los brazos E/F/G lo mueve. Y no es un problema de
posicion: en las noches que MIROVA confirma medimos a 0,18 km del crater con el
pixel +7,8 K sobre el fondo. Es magnitud pura sobre una deteccion correcta.

EL TRUCO. Para un cluster de UN pixel la magnitud es exactamente

    vrp_mw = A_pix * WOOSTER * (L(bt) - L_bg) / 1e6

y todo salvo L_bg esta persistido en el record. Despejando:

    L_bg = L(bt) - vrp_mw * 1e6 / (A_pix * WOOSTER)

o sea que se puede RECUPERAR el `effective_L_bg` que el pipeline uso esa noche, y
convertirlo a temperatura. Eso destapa una variable que no se persiste y que es el
corazon del problema: contra que fondo se esta midiendo cada volcan.

QUE SE ESPERA VER (escrito antes de correr):

  · Villarrica (artefacto): el fondo efectivo deberia estar MUY cerca del propio
    pixel — es una fluctuacion medida contra su propia corona.
  · Lascar (foco real que sub-reporta): si el anillo [1,5-3] km cae sobre el halo
    geotermal cronico de un crater permanentemente activo, el fondo efectivo
    deberia salir MAS CALIENTE que el fondo global 5-25 km. Fondo caliente -> dL
    chico -> VRP baja. Seria la misma enfermedad que Villarrica pero con el signo
    opuesto: alla el anillo esta frio de mas, aca caliente de mas.

Si Lascar da fondo efectivo > fondo global, la corona Eq.6 tampoco lo va a curar
(sus vecinos inmediatos tambien estan tibios) y el criterio 3 del pre-registro
—Lascar no puede caer mas de 20 %— esta en riesgo. Conviene saberlo ANTES de leer
el A/B, no despues.

Persiste en 01_fondo_efectivo.json.
"""
import io, json, math, os, statistics as st, sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.process_viirs import bt_to_spectral_radiance, I04_LAMBDA, WOOSTER_COEFF

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
VENTANA = ("2026-06-25", "2026-08-24")
A_PIX_M2 = 140625.0
K = A_PIX_M2 * WOOSTER_COEFF / 1e6      # MW por unidad de radiancia
RING = (1.5, 3.0)

VOLS = {
    "Lascar":              {"vent": (-23.362930, -67.731416), "reg": "desierto, crater activo"},
    "Villarrica":          {"vent": (-39.420227, -71.939876), "reg": "nevado"},
    "PlanchonPeteroa":     {"vent": (-35.241099, -70.573345), "reg": "nevado"},
    "PuyehueCordonCaulle": {"vent": (-40.525499, -72.146137), "reg": "nevado"},
}
C1, C2 = 1.19104e8, 1.43877e4            # constantes de Planck, mismas que vrp_regimes


def radiancia_a_bt(L, lam=I04_LAMBDA):
    """Inversa de Planck: de radiancia espectral a temperatura de brillo."""
    if L <= 0:
        return float("nan")
    return C2 / (lam * math.log1p(C1 / (lam ** 5 * L)))


def hav(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180.0
    h = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def resumen(xs):
    if not xs:
        return None
    xs = sorted(xs)
    return {"n": len(xs), "mediana": round(st.median(xs), 2),
            "p25": round(xs[len(xs) // 4], 2), "p75": round(xs[3 * len(xs) // 4], 2)}


res = {"ventana": list(VENTANA), "metodo": "L_bg despejado de la formula de Wooster "
       "sobre clusters de 1 pixel", "por_volcan": {}}

print("EL FONDO QUE EL PIPELINE USO REALMENTE (despejado, no estimado)")
print("VIIRS375 nocturno, %s a %s, clusters de 1 pixel\n" % VENTANA)
print("%-22s %5s %11s %11s %11s %12s" %
      ("volcan", "n", "bt pixel", "fondo EFECT", "fondo glob", "efect-glob"))

for vol, cfg in VOLS.items():
    recs = json.load(open(os.path.join(ROOT, "data", "_s125_mag_control", vol + ".json"),
                          encoding="utf-8"))["records"]
    bts, tbk_ef, tbg_g, delta, dist = [], [], [], [], []
    for r in recs:
        s = (r.get("sensor") or "").upper()
        if "VIIRS" not in s or "750" in s or "MODIS" in s:
            continue
        if not (VENTANA[0] <= r["datetime_utc"][:10] <= VENTANA[1]):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is not None and sz < 90:
            continue
        pc = r.get("primary_cluster") or {}
        ap = r.get("anomaly_pixels") or []
        # solo clusters de 1 pixel: ahi la inversion es exacta
        if pc.get("n_pixels") != 1 or len(ap) != 1 or not pc.get("vrp_mw"):
            continue
        bt = ap[0].get("bt_k")
        if not bt or not r.get("t_bg_k"):
            continue
        L_pix = float(bt_to_spectral_radiance(np.float64(bt), I04_LAMBDA))
        L_bg = L_pix - pc["vrp_mw"] / K
        t_bk = radiancia_a_bt(L_bg)
        if not math.isfinite(t_bk):
            continue
        bts.append(bt)
        tbk_ef.append(t_bk)
        tbg_g.append(r["t_bg_k"])
        delta.append(t_bk - r["t_bg_k"])
        dist.append(hav((ap[0]["lat"], ap[0]["lon"]), cfg["vent"]))

    if not bts:
        print("%-22s (sin clusters de 1 pixel)" % vol)
        continue
    d = {"regimen": cfg["reg"], "bt_pixel": resumen(bts),
         "fondo_efectivo_k": resumen(tbk_ef), "fondo_global_k": resumen(tbg_g),
         "efectivo_menos_global_k": resumen(delta),
         "dist_al_crater_km": resumen(dist),
         "contraste_contra_el_fondo_efectivo_k": resumen(
             [b - t for b, t in zip(bts, tbk_ef)])}
    res["por_volcan"][vol] = d
    print("%-22s %5d %11.2f %11.2f %11.2f %+12.2f"
          % (vol, d["bt_pixel"]["n"], d["bt_pixel"]["mediana"],
             d["fondo_efectivo_k"]["mediana"], d["fondo_global_k"]["mediana"],
             d["efectivo_menos_global_k"]["mediana"]))

print("\n" + "=" * 78)
print("LECTURA — el signo de (fondo efectivo - fondo global) dice la enfermedad")
for vol, d in res["por_volcan"].items():
    dd = d["efectivo_menos_global_k"]["mediana"]
    ct = d["contraste_contra_el_fondo_efectivo_k"]["mediana"]
    if dd > 0.5:
        diag = "anillo CALIENTE de mas -> dL chico -> SUB-reporta"
    elif dd < -0.5:
        diag = "anillo FRIO de mas -> dL inflado -> SOBRE-reporta"
    else:
        diag = "anillo alineado con el fondo global"
    print("  %-22s %+6.2f K   contraste efectivo %+5.2f K   %s"
          % (vol, dd, ct, diag))

dest = os.path.join(os.path.dirname(__file__), "01_fondo_efectivo.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
