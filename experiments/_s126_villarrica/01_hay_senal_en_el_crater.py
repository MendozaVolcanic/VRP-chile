# -*- coding: utf-8 -*-
"""S126 — en Villarrica, ?hay senal en el crater que elegimos mal, o no hay senal?

LA PREGUNTA. S126 probo que el cluster que publicamos para Villarrica esta a 2,74 km
del crater INCLUSO en las noches que MIROVA confirma, con el pixel 4,74 K mas FRIO que
el fondo de la escena. Pero eso no dice cual es el arreglo, porque hay dos mundos
posibles y piden cosas opuestas:

  (A) EL CRATER SI EMITE y lo estamos eligiendo mal. Entonces existe un pixel al crater
      mas caliente que su entorno inmediato, y el problema es de SELECCION/ANCLA: el
      pipeline se va al maximo del gradiente topografico en vez de al foco. Arreglo:
      cambiar como se elige el pixel.

  (B) EL CRATER NO EMITE lo suficiente para 375 m. Entonces no hay nada que elegir, el
      lava lake de Villarrica es sub-pixel a esta resolucion, y lo honesto es decir "sin
      senal en este instrumento" (A77: el canal correcto seria SWIR de alta resolucion,
      Landsat/Sentinel-2, no MIR). Arreglo: dejar de reportar un numero que no viene del
      volcan.

COMO SE SEPARAN. El brazo E (filtro contextual apagado) conserva ~50 pixeles por pasada
cubriendo el disco de 3 km, asi que trae pixeles DEL CRATER que el operacional descarta.
Para cada pasada se compara:

  · el pixel mas cercano al crater (<0,5 km) contra la mediana de su corona local;
  · ese mismo contraste para el pixel que HOY publicamos (el de 2,8 km).

Si el crater tiene contraste local positivo y comparable, es el mundo (A).
Si el crater es indistinguible de su entorno mientras el de 2,8 km destaca, es (B) —
y lo que destaca no es el volcan.

Se estratifica por noches que MIROVA confirma, que es donde el mundo (A) tendria que
notarse mas.

Persiste en 01_hay_senal_en_el_crater.json.
"""
import io
import json
import math
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _s126_lib import (ROOT, VENTS, cargar_brazo, cargar_mirova,   # noqa: E402
                       haversine, resumen)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

VENTANA = ("2026-06-25", "2026-08-24")
VOL = "Villarrica"
VENT = VENTS[VOL]
R_CRATER = 0.5        # "en el crater": el pixel de 375 m que lo contiene
R_CORONA = 0.8        # corona local para el contraste (vecinos inmediatos)

# Lascar entra como CONTROL POSITIVO: ahi el foco es real y esta al crater (0,18 km,
# +7,8 K), asi que el metodo tiene que verlo. Si no lo ve en Lascar, el metodo no sirve
# y el resultado de Villarrica no significa nada.
CONTROLES = {"Lascar": VENTS["Lascar"], "PlanchonPeteroa": VENTS["PlanchonPeteroa"]}

mir, _ = cargar_mirova(VENTANA)
res = {"ventana": list(VENTANA), "r_crater_km": R_CRATER, "r_corona_km": R_CORONA,
       "por_volcan": {}}


def contraste_local(px, centro, todos, r_corona=R_CORONA):
    """bt del pixel menos la mediana de los pixeles de su corona local."""
    vec = [q["bt_k"] for q in todos
           if q is not px and q.get("bt_k") is not None
           and haversine((q["lat"], q["lon"]), centro) <= r_corona]
    if len(vec) < 3:
        return None
    return px["bt_k"] - st.median(vec)


print("?HAY SENAL EN EL CRATER? — pixeles del brazo E (filtro contextual apagado),")
print("que conserva el disco de 3 km entero. %s a %s\n" % VENTANA)
print("%-20s %-16s %6s %14s %16s %14s" %
      ("volcan", "noches", "n", "px al crater", "contraste crater", "contraste 2,8km"))

for vol, vent in [(VOL, VENT)] + list(CONTROLES.items()):
    e = cargar_brazo("_s125_viirs_e", vol, VENTANA)
    c = cargar_brazo("_s125_mag_control", vol, VENTANA)
    if not e or not c:
        print("%-20s (sin datos)" % vol)
        continue
    noches_mir = {f for (f, b) in (mir.get(vol) or {}) if b == "v375"}
    grupos = {"MIROVA confirma": {"cr": [], "pub": [], "hay": 0, "n": 0},
              "sin alerta": {"cr": [], "pub": [], "hay": 0, "n": 0}}

    for k in sorted(set(c) & set(e)):
        ap = [p for p in (e[k].get("anomaly_pixels") or []) if p.get("bt_k") is not None]
        if len(ap) < 6:
            continue
        g = grupos["MIROVA confirma" if k[0][:10] in noches_mir else "sin alerta"]
        g["n"] += 1

        # (1) el pixel mas cercano al crater, si hay alguno dentro de R_CRATER
        cerca = [p for p in ap if haversine((p["lat"], p["lon"]), vent) <= R_CRATER]
        if cerca:
            g["hay"] += 1
            px = min(cerca, key=lambda p: haversine((p["lat"], p["lon"]), vent))
            v = contraste_local(px, (px["lat"], px["lon"]), ap)
            if v is not None:
                g["cr"].append(v)

        # (2) el pixel que HOY publicamos (el del cluster del control)
        pc = c[k].get("primary_cluster") or {}
        if pc.get("centroid_lat") is not None:
            cen = (pc["centroid_lat"], pc["centroid_lon"])
            pub = min(ap, key=lambda p: haversine((p["lat"], p["lon"]), cen))
            v = contraste_local(pub, (pub["lat"], pub["lon"]), ap)
            if v is not None:
                g["pub"].append(v)

    d = {}
    for gn, g in grupos.items():
        if g["n"] < 3:
            continue
        d[gn] = {"pasadas": g["n"],
                 "pct_con_pixel_al_crater": round(100 * g["hay"] / g["n"], 1),
                 "contraste_crater_k": resumen(g["cr"], 2),
                 "contraste_publicado_k": resumen(g["pub"], 2)}
        print("%-20s %-16s %6d %13.0f%% %16s %14s"
              % (vol if gn.startswith("MIROVA") else "", gn, g["n"],
                 d[gn]["pct_con_pixel_al_crater"],
                 ("%+.2f" % d[gn]["contraste_crater_k"]["mediana"]) if d[gn]["contraste_crater_k"] else "-",
                 ("%+.2f" % d[gn]["contraste_publicado_k"]["mediana"]) if d[gn]["contraste_publicado_k"] else "-"))
    res["por_volcan"][vol] = d

print("\n" + "=" * 84)
print("LECTURA")
la = res["por_volcan"].get("Lascar", {}).get("MIROVA confirma")
if la and la["contraste_crater_k"]:
    print("  CONTROL POSITIVO (Lascar, foco real al crater): contraste al crater %+.2f K"
          % la["contraste_crater_k"]["mediana"])
    print("  Si este numero no es claramente positivo, el metodo no sirve y lo de abajo no vale.")
vi = res["por_volcan"].get(VOL, {}).get("MIROVA confirma")
if vi:
    cr = vi["contraste_crater_k"]["mediana"] if vi["contraste_crater_k"] else None
    pu = vi["contraste_publicado_k"]["mediana"] if vi["contraste_publicado_k"] else None
    print("\n  VILLARRICA en noches que MIROVA confirma:")
    print("    contraste del pixel AL CRATER      : %s K" % (("%+.2f" % cr) if cr is not None else "sin dato"))
    print("    contraste del pixel QUE PUBLICAMOS : %s K" % (("%+.2f" % pu) if pu is not None else "sin dato"))
    if cr is not None and pu is not None:
        if cr > 0.5 and cr >= pu:
            print("    -> MUNDO (A): el crater emite y lo estamos eligiendo mal. Arreglo de ANCLA.")
        elif cr <= 0.5 and pu > cr:
            print("    -> MUNDO (B): el crater es indistinguible de su entorno y lo que destaca")
            print("       esta a 2,8 km. VIIRS375 no ve el lava lake; el canal correcto es")
            print("       SWIR de alta resolucion (A77). Reportar un numero de ahi es inventar.")
        else:
            print("    -> mixto: ninguno de los dos mundos domina; hace falta mas evidencia.")

dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "01_hay_senal_en_el_crater.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
