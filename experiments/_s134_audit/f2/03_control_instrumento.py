# -*- coding: utf-8 -*-
"""F2/03 - CONTROL DEL INSTRUMENTO: sirve el GeoTIFF para decir DONDE?

EL FENOMENO. El TIF que publica MIROVA trae una sola banda, el infrarrojo medio crudo.
En un volcan nevado de altura ese campo lo manda el gradiente de temperatura con la
altitud, no el foco volcanico (A69): por eso S131 lo refuto como arbitro de posicion
buscando el maximo en TODO el radio de 25 km (error mediano 19,5 km con el maximo crudo).
Aca la pregunta es mas modesta y por eso puede tener respuesta: restringido al
inner_radius (5 km en Lascar), donde ya no hay salar ni valle que compita, cae el maximo
en el crater? Lascar es el control POSITIVO: es el volcan mas caliente, foco aislado sobre
roca seca, y S133 midio que hasta nuestro propio cumulo cae en el crater el 79% de las veces.
Si el TIF no encuentra el crater ACA, no lo va a encontrar en ningun lado.

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si el TIF no sirviera para posicion, esta medicion lo veria? SI: el criterio es una
   distancia absoluta al crater (<1 km) y el espacio de busqueda tiene radio 5 km, o sea
   el azar puro daria ~4% de aciertos por area (pi*1^2/pi*5^2). Un TIF ciego da ~0/5.
2. Si el instrumento estuviera muerto (TIF corrupto, georreferencia mala), se veria
   distinto de "no hay senal"? SI: control de georreferencia independiente - el semiancho
   del raster debe dar ~25 km (grilla 51x51 km de MIROVA) y el CRS debe leerse. Un TIF
   con georreferencia rota falla ESE control antes de llegar al veredicto.
CONTROL NEGATIVO agregado: la misma medicion con el maximo tomado en TODO el radius_km
(25 km). Si el restringido acierta y el amplio no, el efecto es real y ademas reproduce
a S131 en su propio terreno.
Read-only. El TIF se usa SOLO para posicion, nunca para magnitud (A24)."""
import datetime as dt, json, os, sys
import numpy as np
import f2_lib as F
from importlib import import_module
F.utf8()
P = import_module("02_emparejar") if False else None
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
_s = importlib.util.spec_from_file_location("emp", os.path.join(os.path.dirname(os.path.abspath(__file__)), "02_emparejar.py"))
emp = importlib.util.module_from_spec(_s); _s.loader.exec_module(emp)

VOL = "Lascar"
N = 5
TOL_TS = 120   # mismo satelite, misma pasada (ver 02_)

def punto_max(a, lat, lon, mask):
    f = np.where(mask & np.isfinite(a), a, -np.inf)
    if not np.isfinite(f).any(): return None
    i, j = np.unravel_index(int(np.argmax(f)), f.shape)
    return float(lat[i, j]), float(lon[i, j]), float(a[i, j])

def main():
    cat = F.catalogo()
    c = cat[VOL]
    vla, vlo = c["vent_lat"], c["vent_lon"]
    inner, rad = float(c["inner_radius_km"]), float(c["radius_km"])
    print("CONTROL DE INSTRUMENTO - %s  vent=(%.5f, %.5f)  inner=%.0f km  radius=%.0f km" %
          (VOL, vla, vlo, inner, rad))
    print("Ventana: ALERTAS MIROVA VIIRS375 desde 2026-06-01. TIF emparejado a <=%d s.\n" % TOL_TS)

    ps = [x for x in emp.pares(VOL) if x["tif"] and x["dt_tif"] <= TOL_TS]
    ps.sort(key=lambda x: x["alerta"]["_ts"], reverse=True)
    print("pasadas ALERTA+TIF disponibles (n=%d); se usan las %d mas recientes\n" % (len(ps), N))

    filas = []
    for x in ps[:N]:
        a, t = x["alerta"], x["tif"]
        try:
            arr, lat, lon, crs = F.leer_tif(t["tif_path"])
        except Exception as e:
            filas.append(dict(pasada=str(a["_ts"]), error=repr(e))); continue
        dg = F.grilla_dist_km(lat, lon, vla, vlo)
        semi_km = float(np.nanmax(dg))
        pin = punto_max(arr, lat, lon, dg <= inner)
        pam = punto_max(arr, lat, lon, dg <= rad)
        f = dict(pasada=a["_ts"].strftime("%Y-%m-%d %H:%M:%S"),
                 tif=t["tif_path"].split("/")[-1], crs=crs, shape=list(arr.shape),
                 semiancho_km=round(semi_km, 2),
                 finitos=int(np.isfinite(arr).sum()), celdas=int(arr.size),
                 dist_km_csv=a["dist_km"], vrp_mirova=a["vrp_mw"], fuente=a["source"])
        f["d_max_inner_km"] = round(F.haversine(vla, vlo, pin[0], pin[1]), 3) if pin else None
        f["d_max_radius_km"] = round(F.haversine(vla, vlo, pam[0], pam[1]), 3) if pam else None
        filas.append(f)
        print("%s | %s" % (f["pasada"], f["tif"]))
        print("   georref: CRS=%s shape=%s semiancho=%.2f km  finitos=%d/%d" %
              (crs, arr.shape, semi_km, f["finitos"], f["celdas"]))
        print("   d(max dentro de inner=%.0fkm -> crater) = %s km   [CONTROL NEG d(max en 25 km) = %s km]" %
              (inner, f["d_max_inner_km"], f["d_max_radius_km"]))
        print("   MIROVA CSV: dist_km=%s  vrp=%s MW  (%s)\n" % (f["dist_km_csv"], f["vrp_mirova"], f["fuente"]))

    ok = [f for f in filas if f.get("d_max_inner_km") is not None]
    aciertos = sum(1 for f in ok if f["d_max_inner_km"] < 1.0)
    neg = sum(1 for f in ok if f.get("d_max_radius_km") is not None and f["d_max_radius_km"] < 1.0)
    print("=" * 78)
    print("VEREDICTO: %d de %d pasadas con el maximo del TIF a <1 km del crater (criterio: >=4 de 5)"
          % (aciertos, len(ok)))
    print("CONTROL NEGATIVO (sin restringir, 25 km): %d de %d a <1 km  <- S131 midio esto y lo refuto"
          % (neg, len(ok)))
    print("VEREDICTO =", "PASA - el TIF sirve para POSICION dentro del inner" if aciertos >= 4
          else "NO PASA - el TIF no sirve como arbitro de posicion")
    print("=" * 78)
    out = dict(volcan=VOL, criterio="d_max_inner < 1 km en >=4 de 5", n=len(ok),
               aciertos=aciertos, control_negativo_25km=neg,
               pasa=bool(aciertos >= 4), tol_emparejamiento_s=TOL_TS,
               pasadas_disponibles=len(ps), filas=filas)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_instrumento.json"),
                        "w", encoding="utf-8"), indent=1, ensure_ascii=False)

main()
