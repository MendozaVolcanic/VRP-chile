# -*- coding: utf-8 -*-
"""S126 — cuanto le cuesta `single_pixel_mode` a Lascar, que es a quien no deberia tocar.

EL PROBLEMA. `pipeline/single_pixel_mode.py` reporta max(per_pixel_vrp) en vez de la
suma cuando el cluster cae en regimen sub-MW (vrp < 5 MW y n_pixels <= 3). Nacio para
DESINFLAR volcanes que sobre-reportaban (Tupungatito 30x, Chaiten 2,5x) y su propio
docstring dice, textual: "Volcanes NO afectados ... Lascar ...".

Pero esta activo en los 110 de 110 records de Lascar. Y Lascar es justo el volcan al
que le FALTA un pixel: el script 02 mostro que necesita ~2 y sumamos 1, y que el fondo
esta descartado (haria falta 248 K cuando el pixel mas frio del disco era 275,6 K).
O sea que el modo esta trabajando en contra del unico volcan al que no deberia tocar.

POR QUE ESTE CALCULO ES EXACTO Y NO UN PREVIEW (A18). El modo se aplica DESPUES de la
seleccion del cluster y solo cambia el numero reportado: no toca deteccion, ni posicion,
ni que cluster gana. Asi que revertirlo sobre los records persistidos da el valor que
habria salido, no una estimacion. A18 advierte sobre previews que filtran records ya
seleccionados con el parametro viejo — no es el caso.

IDENTIFICAR LOS PIXELES DEL CLUSTER. `anomaly_pixels` es el top-100 de la ESCENA, no el
cluster. Se toman los `n_pixels` mas cercanos al centroide del cluster, que es contiguo.
El metodo se VALIDA contra los clusters de 1 pixel, donde el resultado tiene que
coincidir exactamente con `pc.vrp_mw`: si la validacion falla, el resto no vale.

Persiste en 03_costo_single_pixel_mode.json.
"""
import csv, io, json, math, os, statistics as st, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
VENTANA = ("2026-06-25", "2026-08-24")
VOLS = ["Lascar", "Villarrica", "PlanchonPeteroa", "PuyehueCordonCaulle"]
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
}


def hav(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180.0
    h = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def mirova():
    out = defaultdict(dict)
    for f in ("latest_consolidado.csv",
              "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            if (r.get("Sensor") or "").strip().upper() != "VIIRS375":
                continue
            fe = (r.get("Fecha_Satelite_UTC") or "")
            if not (VENTANA[0] <= fe[:10] <= VENTANA[1]) or not (3 <= int(fe[11:13] or 12) <= 9):
                continue
            try:
                v = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            if v > 0:
                out[vol][fe[:10]] = max(out[vol].get(fe[:10], 0), v)
    return out


def pixeles_del_cluster(pc, ap):
    """Los n_pixels de `anomaly_pixels` mas cercanos al centroide del cluster."""
    n = pc.get("n_pixels") or 0
    if not n or len(ap) < n:
        return None
    c = (pc["centroid_lat"], pc["centroid_lon"])
    orden = sorted(ap, key=lambda p: hav((p["lat"], p["lon"]), c))
    return orden[:n]


mir = mirova()
res = {"ventana": list(VENTANA), "validacion": {}, "por_volcan": {}}

# ---- VALIDACION del metodo sobre clusters de 1 pixel ----
ok = err = 0
peor = 0.0
for vol in VOLS:
    for r in json.load(open(os.path.join(ROOT, "data", "_s125_mag_control", vol + ".json"),
                            encoding="utf-8"))["records"]:
        s = (r.get("sensor") or "").upper()
        if "VIIRS" not in s or "750" in s or "MODIS" in s:
            continue
        pc, ap = r.get("primary_cluster") or {}, r.get("anomaly_pixels") or []
        if pc.get("n_pixels") != 1 or not pc.get("vrp_mw") or not ap:
            continue
        px = pixeles_del_cluster(pc, ap)
        if not px:
            continue
        d = abs((px[0].get("vrp_mw") or 0) - pc["vrp_mw"])
        peor = max(peor, d)
        if d <= 0.0011:            # los vrp se persisten con 4 decimales, pc con 3
            ok += 1
        else:
            err += 1
res["validacion"] = {"clusters_1px_probados": ok + err, "coinciden": ok,
                     "no_coinciden": err, "peor_desvio_mw": round(peor, 5)}
print("VALIDACION DEL METODO (clusters de 1 pixel: el pixel hallado debe dar pc.vrp_mw)")
print("  %d de %d coinciden, peor desvio %.5f MW\n"
      % (ok, ok + err, peor))
if err > ok * 0.02:
    print("  !! la identificacion de pixeles no es fiable: no seguir.")
    sys.exit(1)

# ---- COSTO del modo ----
print("COSTO DE single_pixel_mode — ratio contra MIROVA con el modo ON y revertido")
print("un par por noche (max de ambos lados), %s a %s\n" % VENTANA)
print("%-22s %5s %11s %13s %10s %9s" %
      ("volcan", "noches", "ratio HOY", "ratio sin modo", "recuperaria", "n tocadas"))

for vol in VOLS:
    recs = json.load(open(os.path.join(ROOT, "data", "_s125_mag_control", vol + ".json"),
                          encoding="utf-8"))["records"]
    mejor = {}
    for r in recs:
        s = (r.get("sensor") or "").upper()
        if "VIIRS" not in s or "750" in s or "MODIS" in s:
            continue
        f = r["datetime_utc"][:10]
        if not (VENTANA[0] <= f <= VENTANA[1]):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is not None and sz < 90:
            continue
        v = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
        if v > mejor.get(f, (0, None))[0]:
            mejor[f] = (v, r)

    hoy, sin_modo, tocadas = [], [], 0
    for f, (_, r) in sorted(mejor.items()):
        vm = mir.get(vol, {}).get(f)
        pc, ap = r.get("primary_cluster") or {}, r.get("anomaly_pixels") or []
        if not vm or not pc.get("vrp_mw"):
            continue
        v_hoy = pc["vrp_mw"]
        v_rev = v_hoy
        if pc.get("single_pixel_mode") and (pc.get("n_pixels") or 0) > 1:
            px = pixeles_del_cluster(pc, ap)
            if px:
                suma = sum((p.get("vrp_mw") or 0) for p in px)
                if suma > v_hoy:
                    v_rev = suma
                    tocadas += 1
        hoy.append(v_hoy / vm)
        sin_modo.append(v_rev / vm)

    if len(hoy) < 3:
        print("%-22s %5d  (muestra insuficiente)" % (vol, len(hoy)))
        continue
    rh, rs = st.median(hoy), st.median(sin_modo)
    res["por_volcan"][vol] = {
        "noches": len(hoy), "ratio_hoy": round(rh, 3), "ratio_sin_modo": round(rs, 3),
        "recupera": round(rs - rh, 3), "noches_tocadas_por_el_modo": tocadas}
    print("%-22s %5d %11.3f %13.3f %+10.3f %9d"
          % (vol, len(hoy), rh, rs, rs - rh, tocadas))

print("\nLECTURA")
for vol, d in res["por_volcan"].items():
    if d["noches_tocadas_por_el_modo"] == 0:
        print("  %-22s el modo no toca ninguna de sus noches emparejadas" % vol)
    else:
        print("  %-22s el modo le saca %.3f de ratio en %d de %d noches"
              % (vol, -d["recupera"], d["noches_tocadas_por_el_modo"], d["noches"]))

dest = os.path.join(os.path.dirname(__file__), "03_costo_single_pixel_mode.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
