"""S190: auditoría del centro de los 45 volcanes de volcanoes.yaml contra la RNVV de SERNAGEOMIN y el GVP.

POR QUÉ. El centro de cada volcán decide dos cosas en la vía «código MIROVA»: (1) dónde se apoya la grilla UTM de
51 x 51 km y su caja ROI (pipeline/grillas_mirova.yaml, x0/y0), o sea qué píxeles se miran con más sensibilidad, y
(2) desde dónde se mide la distancia de cada alerta, que en el tablero separa «cumbre» de «lejos» (los 34 no tienen
inner_radius_km en el yaml; frontend/index.html les asigna 5 km). Nicolás notó que Mentolat está corrido unos 3 km
al norte del volcán. Los centros de los 34 entraron en d1d8952f7 (2026-04-05) sin fuente declarada; este script
los compara con dos fuentes externas y cuenta cuántas alertas ya guardadas cambiarían de clase.

FUENTES (orden de autoridad):
  1. 11 Tier A: KMZ/TIF de MIROVA (A5, ya adoptado). Sólo se comprueba que yaml, vent, mirova_center y grilla son
     coherentes con lo documentado (experiments/mirova_centroids.md, cabecera de pipeline/grillas_mirova.yaml).
  2. 34 restantes: ficha RNVV (WEBRNVV/fichas_nuevas_json/_lista.json, campos latitud/longitud) contrastada con el
     GVP (WFS público GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes, por Volcano_Number = gvp_id del yaml).

CLASE. Para cada record con vrp_mw > 0 de data/historia_34 y data/sombra_34 se toma el centroide del cúmulo
(primary_cluster.centroid_lat/lon; si falta, final_hotspot_lat/lon) y se mide su distancia al centro viejo y al
propuesto; «cumbre» si <= 5 km (RADIO_CUMBRE_KM, el inner que el tablero da a los 34). Control: la distancia al
centro viejo recalculada debe parecerse a la guardada (centroid_dist_km); se imprime la diferencia máxima.

Uso:
  git show db04d930c:volcanoes.yaml > volcanoes_antes.yaml
  python experiments/_s190_coordenadas/auditar_centros.py --volcanes volcanoes_antes.yaml
      --gvp gvp_chile.json gvp_caja.json gvp_falt_Pleistocene.json --rnvv WEBRNVV/fichas_nuevas_json/_lista.json
      --md tabla.md [--json salida.json]
Las consultas WFS del GVP (2026-11-17) están en experiments/_s190_coordenadas/INFORME.md.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import math
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
RADIO_CUMBRE_KM = 5.0
UMBRAL_KM = 1.0

# Nuestro nombre -> id de la ficha RNVV (None: no está en la RNVV). Pares fusionados: el id del edificio que da el
# nombre principal (Macá en MacaCay, Yate en YateHornopiren); el otro se informa aparte.
RNVV_ID = {
    "PuyehueCordonCaulle": 15, "Villarrica": 2, "Lascar": 35, "Antuco": 21, "Copahue": 3,
    "DescabezadoGrande": 20, "CerroAzulQuizapu": None, "LagunaDelMaule": 10, "NevadoDeLongavi": 40,
    "NevadosDeChillan": 13, "Callaqui": 23, "Lonquimay": 6, "Tolhuaca": None, "Llaima": 4, "Sollipulli": 45,
    "Quetrupillan": 16, "Lanin": 33, "MochoChoshuenco": 12, "CarranLosVenados": 7, "AntillancaCasablanca": 8,
    "Osorno": 42, "Calbuco": 1, "YateHornopiren": 49, "Huequi": 30, "Michinmahuida": 39, "Chaiten": 25,
    "CorcovadoYanteles": 9, "Melimoyu": 37, "Mentolat": 38, "MacaCay": 36, "Hudson": 5, "Tinguiririca": 46,
    "PlanchonPeteroa": 14, "Lastarria": None, "Isluga": 32, "Taapaca": 18, "Parinacota": 43, "Guallatiri": 27,
    "Irruputuncu": 31, "OlcaParuma": None, "Ollague": 41, "SanPedro": 44, "Putana": None, "SanJose": 17,
    "Tupungatito": 47,
}
RNVV_PAREJA = {"YateHornopiren": 28, "MacaCay": 24}  # Hornopirén, Cay
# gvp_id del yaml que no apunta al volcán (consulta WFS del 2026-11-17): MacaCay trae 358055 (Cay) y su centro es el
# de Macá (358056); Tolhuaca y AntillancaCasablanca traen números que el GVP ya no tiene (357106 y 358001).
GVP_CORRECTO = {"MacaCay": 358056, "Tolhuaca": 357093, "AntillancaCasablanca": 357153}
# Regla de recomendación: cambiar sólo si la RNVV está a más de UMBRAL_KM del centro actual Y la RNVV y el GVP están a
# UMBRAL_KM o menos entre sí (dos fuentes independientes de acuerdo). RNVV lejos y GVP en desacuerdo: DUDOSO.


def dist_km(lat1, lon1, lat2, lon2):
    r = math.pi / 180
    x = math.sin((lat2 - lat1) * r / 2) ** 2 + math.cos(lat1 * r) * math.cos(lat2 * r) * math.sin((lon2 - lon1) * r / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def rumbo(lat1, lon1, lat2, lon2):
    """Rumbo de 1 a 2 en grados (0 = N) y en 8 puntos."""
    r = math.pi / 180
    y = math.sin((lon2 - lon1) * r) * math.cos(lat2 * r)
    x = math.cos(lat1 * r) * math.sin(lat2 * r) - math.sin(lat1 * r) * math.cos(lat2 * r) * math.cos((lon2 - lon1) * r)
    b = (math.degrees(math.atan2(y, x)) + 360) % 360
    return b, ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][int((b + 22.5) // 45) % 8]


def decimales(s):
    s = str(s).rstrip("0")
    return len(s.split(".")[1]) if "." in s else 0


def centroide(r):
    pc = r.get("primary_cluster") or {}
    if pc.get("centroid_lat") is not None:
        return pc["centroid_lat"], pc["centroid_lon"], pc.get("centroid_dist_km")
    if r.get("final_hotspot_lat") is not None:
        return r["final_hotspot_lat"], r["final_hotspot_lon"], r.get("final_hotspot_dist_km")
    return None


def contar_clase(nombre, viejo, nuevo):
    """Records con vrp_mw > 0 en historia_34 y sombra_34 que cambian de clase al pasar del centro viejo al nuevo."""
    out = {"n_alertas": 0, "a_cumbre": 0, "a_lejos": 0, "control_max_km": 0.0, "por_carpeta": {}}
    for carpeta in ("historia_34", "sombra_34"):
        f = REPO / "data" / carpeta / f"{nombre}.json"
        if not f.exists():
            continue
        n = c_in = c_out = 0
        for r in json.loads(f.read_text(encoding="utf-8")).get("records", []):
            if not (r.get("vrp_mw") or 0) > 0:
                continue
            c = centroide(r)
            if c is None:
                continue
            n += 1
            d0 = dist_km(viejo[0], viejo[1], c[0], c[1])
            if c[2] is not None:
                out["control_max_km"] = max(out["control_max_km"], abs(d0 - float(c[2])))
            if nuevo is None:
                continue
            d1 = dist_km(nuevo[0], nuevo[1], c[0], c[1])
            k0, k1 = d0 <= RADIO_CUMBRE_KM, d1 <= RADIO_CUMBRE_KM
            c_in += (not k0) and k1
            c_out += k0 and not k1
        out["por_carpeta"][carpeta] = {"n_alertas": n, "a_cumbre": c_in, "a_lejos": c_out}
        out["n_alertas"] += n
        out["a_cumbre"] += c_in
        out["a_lejos"] += c_out
    out["control_max_km"] = round(out["control_max_km"], 3)
    return out


def _n(x, d=2):
    return "" if x is None else f"{x:.{d}f}".replace(".", ",")


def tabla_md(filas):
    """Tabla del informe. Coma decimal; «alertas» = records con vrp_mw > 0 en historia_34 + sombra_34."""
    out = ["| Volcán | Nuestro centro | RNVV | GVP | Nuestro a RNVV (km, rumbo) | Nuestro a GVP (km) | RNVV a GVP (km) "
           "| Alertas | A cumbre | A lejos | Recomendación |", "|" + "---|" * 11]
    for f in filas:
        r = f"{_n(f['rnvv_lat'], 4)}; {_n(f['rnvv_lon'], 4)}" if "rnvv_lat" in f else "no está"
        g = f"{_n(f['gvp_lat'], 3)}; {_n(f['gvp_lon'], 3)}" if f.get("gvp_lat") is not None else "sin dato"
        cl = f.get("clase") or {}
        rec = "Tier A: KMZ de MIROVA, no se toca" if f["tier_a"] else f["recomendacion"]
        out.append(f"| {f['volcan']} | {_n(f['lat'], 4)}; {_n(f['lon'], 4)} | {r} | {g} | "
                   f"{_n(f.get('d_rnvv_km'))} {f.get('rumbo_rnvv', '')} | {_n(f.get('d_gvp_km'))} | "
                   f"{_n(f.get('d_rnvv_gvp_km'))} | {cl.get('n_alertas', '')} | {cl.get('a_cumbre', '')} | "
                   f"{cl.get('a_lejos', '')} | {rec} |")
    return chr(10).join(out) + chr(10)


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--gvp", required=True, nargs="+", help="uno o más GeoJSON del WFS del GVP (Holocene, Pleistocene)")
    ap.add_argument("--rnvv", required=True)
    ap.add_argument("--json")
    ap.add_argument("--volcanes", default=str(REPO / "volcanoes.yaml"),
                    help="volcanoes.yaml a auditar; para la tabla del informe, el de origin/main antes del cambio")
    ap.add_argument("--md", help="escribe la tabla en Markdown (la del INFORME.md)")
    a = ap.parse_args(argv)

    volcanes = yaml.safe_load(Path(a.volcanes).read_text(encoding="utf-8"))["volcanoes"]
    grillas = yaml.safe_load((REPO / "pipeline" / "grillas_mirova.yaml").read_text(encoding="utf-8"))["volcanes"]
    gvp = {}
    for ruta in a.gvp:
        for f in json.load(open(ruta, encoding="utf-8"))["features"]:
            gvp.setdefault(f["properties"]["Volcano_Number"], f["properties"])
    rnvv = {x["id"]: x for x in json.load(open(a.rnvv, encoding="utf-8"))}
    assert set(RNVV_ID) == {v["name"] for v in volcanes}, "el mapeo no cubre exactamente a los 45"

    filas = []
    for v in volcanes:
        n = v["name"]
        lat, lon = float(v["lat"]), float(v["lon"])
        g = gvp.get(GVP_CORRECTO.get(n, v.get("gvp_id")))
        fila = {"volcan": n, "tier_a": "inner_radius_km" in v, "lat": lat, "lon": lon, "gvp_id": v.get("gvp_id"),
                "gvp_nombre": g["Volcano_Name"] if g else None,
                "gvp_lat": g["Latitude"] if g else None, "gvp_lon": g["Longitude"] if g else None}
        if g:
            fila["d_gvp_km"] = round(dist_km(lat, lon, g["Latitude"], g["Longitude"]), 2)
            fila["rumbo_gvp"] = rumbo(lat, lon, g["Latitude"], g["Longitude"])[1]
        rid = RNVV_ID[n]
        if rid is not None:
            x = rnvv[rid]
            rl, ro = float(x["latitud"]), float(x["longitud"])
            fila.update({"rnvv_id": rid, "rnvv_nombre": x["nombre"], "rnvv_lat": rl, "rnvv_lon": ro,
                         "rnvv_decimales": min(decimales(x["latitud"]), decimales(x["longitud"])),
                         "d_rnvv_km": round(dist_km(lat, lon, rl, ro), 2)})
            b, p = rumbo(lat, lon, rl, ro)
            fila["rumbo_rnvv"] = f"{p} ({b:.0f}°)"
            if g:
                fila["d_rnvv_gvp_km"] = round(dist_km(rl, ro, g["Latitude"], g["Longitude"]), 2)
        if n in RNVV_PAREJA:
            y = rnvv[RNVV_PAREJA[n]]
            fila["pareja"] = {"rnvv_nombre": y["nombre"], "lat": float(y["latitud"]), "lon": float(y["longitud"]),
                              "d_km": round(dist_km(lat, lon, float(y["latitud"]), float(y["longitud"])), 2)}
        gr = grillas.get(n)
        if gr:
            fila["d_grilla_centro_km"] = round(dist_km(lat, lon, gr["centro_lat"], gr["centro_lon"]), 3)
        if fila["tier_a"]:
            fila["vent"] = (v.get("vent_lat"), v.get("vent_lon"))
            if v.get("mirova_center_lat") is not None:
                fila["d_kmz_km"] = round(dist_km(lat, lon, v["mirova_center_lat"], v["mirova_center_lon"]), 2)
        else:
            nuevo = (fila["rnvv_lat"], fila["rnvv_lon"]) if rid is not None else None
            fila["clase"] = contar_clase(n, (lat, lon), nuevo)
        if not fila["tier_a"]:
            dr, rg = fila.get("d_rnvv_km"), fila.get("d_rnvv_gvp_km")
            fila["recomendacion"] = ("sin RNVV: se queda" if dr is None else
                                     "se queda" if dr <= UMBRAL_KM else
                                     "CAMBIAR a RNVV" if rg is not None and rg <= UMBRAL_KM else "DUDOSO: se queda")
        filas.append(fila)

    print(f"{'volcán':22s} {'yaml':>17s} {'RNVV':>19s} {'dR':>5s} {'rumbo':>10s} {'GVP':>17s} {'dG':>5s} "
          f"{'R-G':>5s} {'dec':>3s} alertas →cumbre →lejos ctl")
    for f in filas:
        r = f"{f['rnvv_lat']:.4f},{f['rnvv_lon']:.4f}" if "rnvv_lat" in f else "-"
        gg = f"{f['gvp_lat']:.3f},{f['gvp_lon']:.3f}" if f.get("gvp_lat") is not None else "-"
        cl = f.get("clase") or {}
        print(f"{f['volcan']:22s} {f['lat']:.4f},{f['lon']:.4f} {r:>19s} {f.get('d_rnvv_km', ''):>5} "
              f"{f.get('rumbo_rnvv', ''):>10s} {gg:>17s} {f.get('d_gvp_km', ''):>5} {f.get('d_rnvv_gvp_km', ''):>5} "
              f"{f.get('rnvv_decimales', ''):>3} {cl.get('n_alertas', ''):>7} {cl.get('a_cumbre', ''):>7} "
              f"{cl.get('a_lejos', ''):>6} {cl.get('control_max_km', '')} "
              f"{'TierA' if f['tier_a'] else f['recomendacion']} | {f.get('gvp_nombre') or ''}")
    for f in filas:
        if "pareja" in f:
            print(f"pareja {f['volcan']}: {f['pareja']}")
        if f["tier_a"]:
            print(f"TierA {f['volcan']}: d(yaml, centro de la grilla) = {f.get('d_grilla_centro_km')} km; "
                  f"d(yaml, KMZ) = {f.get('d_kmz_km')} km; vent = {f['vent']}")
    # Resumen que cita el INFORME.md (ningún número a mano)
    no_a = [f for f in filas if not f["tier_a"]]
    cambian = [f["volcan"] for f in no_a if f["recomendacion"] == "CAMBIAR a RNVV"]
    print()
    print(f"RESUMEN fichas RNVV: {len(rnvv)}; con 2 decimales o menos en lat y lon: "
          f"{sum(max(decimales(x['latitud']), decimales(x['longitud'])) <= 2 for x in rnvv.values())}")
    print(f"RESUMEN no Tier A: {len(no_a)}; a 0,0 km del GVP: {sum(f.get('d_gvp_km') == 0.0 for f in no_a)}")
    print(f"RESUMEN cambian: {cambian}; dudosos: {[f['volcan'] for f in no_a if f['recomendacion'].startswith('DUDOSO')]}")
    for f in no_a:
        if f["volcan"] in cambian:
            print(f"RESUMEN clase {f['volcan']}: {f['clase']}")
    print(f"RESUMEN control máx (km): {max(f['clase']['control_max_km'] for f in no_a)}")
    if a.md:
        Path(a.md).write_text(tabla_md(filas), encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
