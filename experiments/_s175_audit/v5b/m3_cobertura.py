# -*- coding: utf-8 -*-
"""m3 (V5B): cobertura de laminas Latest10NTI desde el 2026-09-22, por otro camino que p10.

Fenomeno: si un dia no hay lamina puede ser que el poller no capturo, que MIROVA no actualizo, o que la fila se
omitio porque ya estaba guardada. Y una lamina lleva 10 paneles: una pasada de un dia sin lamina puede salir en la
lamina siguiente. El indice se lee por captured_at_utc (cuando corrio el poller) y por last_modified_utc (cuando
MIROVA la genero), y se separan las filas omitidas.

Pregunta 1: si los huecos fueran un artefacto del indice, otros tipos de archivo del mismo poller tambien faltarian
esos dias. Pregunta 2: el conteo de dias presentes prueba que el instrumento ve dias con datos.
Control positivo: los dias con lamina de VIIRS en la misma ventana; ventana: 2026-09-22 a 2026-11-06, 46 dias, indice
congelado en insumos/png_index.csv (ola 0, ultima captura 2026-11-07). Salida: stdout.
"""
import csv, collections, datetime as dt, sys
sys.stdout.reconfigure(encoding="utf-8")
INS = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
rows = list(csv.DictReader(open(INS + r"\png_index.csv", encoding="utf-8")))
dias = [(dt.date(2026, 9, 22) + dt.timedelta(d)).isoformat() for d in range(46)]
L10 = [r for r in rows if r["kind"] == "Latest10NTI" and r["last_modified_utc"] >= "2026-09-22"]
print("filas Latest10NTI desde 09-22:", len(L10), "omitido:", collections.Counter(r["omitido"] for r in L10))
print("omitidas por dia (sensor):", sorted(collections.Counter((r["last_modified_utc"][:10], r["sensor"], r["omitido"]) for r in L10 if r["omitido"]).items())[:60])
for sensor in ("MODIS", "VIIRS375", "VIIRS750"):
    porvol = collections.defaultdict(set)
    porvol_cap = collections.defaultdict(set)
    for r in L10:
        if r["sensor"] == sensor and r["png_path"]:
            porvol[r["volcano"]].add(r["last_modified_utc"][:10])
            porvol_cap[r["volcano"]].add(r["captured_at_utc"][:10])
    falt = {v: sorted(set(dias) - s) for v, s in porvol.items()}
    comunes = set.intersection(*[set(x) for x in falt.values()])
    print(f"{sensor}: {len(porvol)} volcanes; dias sin lamina (con archivo) por last_modified: minimo {min(len(x) for x in falt.values())}, maximo {max(len(x) for x in falt.values())}; comunes a todos: {sorted(comunes)}")
    falt_c = {v: sorted(set(dias) - s) for v, s in porvol_cap.items()}
    print(f"   por captured_at: minimo {min(len(x) for x in falt_c.values())}, maximo {max(len(x) for x in falt_c.values())}; ejemplo Lascar: {falt_c.get('Lascar')}")
print("Otros tipos MODIS (VRP, logVRP, Dist con sensor MODIS o COMB) con last_modified en los huecos 09-23..09-30 y 10-08..10-11:")
huecos = [d for d in dias if "2026-09-23" <= d <= "2026-09-30" or "2026-10-08" <= d <= "2026-10-11"]
c = collections.Counter((r["kind"], r["sensor"]) for r in rows if r["last_modified_utc"][:10] in huecos)
print(sorted(c.items()))
print("Por dia, filas de cualquier tipo capturadas (captured_at) por sensor MODIS en los huecos:")
c2 = collections.Counter((r["captured_at_utc"][:10], r["kind"], r["sensor"]) for r in rows if r["captured_at_utc"][:10] in huecos and r["sensor"] == "MODIS")
print(sorted(c2.items())[:40])
print("Filas Latest10NTI MODIS capturadas en los huecos (cualquier last_modified):", sum(1 for r in rows if r["kind"] == "Latest10NTI" and r["sensor"] == "MODIS" and r["captured_at_utc"][:10] in huecos))
print("Latest10NTI VIIRS375 capturadas por dia en los huecos, Lascar:", sorted(collections.Counter(r["captured_at_utc"][:10] for r in rows if r["kind"] == "Latest10NTI" and r["sensor"] == "VIIRS375" and r["volcano"] == "Lascar" and r["captured_at_utc"][:10] in huecos).items()))
for vol in ("ChillanNevadosde", "Lascar"):
    ls = sorted([r for r in rows if r["kind"] == "Latest10NTI" and r["sensor"] == "MODIS" and r["volcano"] == vol and "2026-09-20" <= r["last_modified_utc"][:10] <= "2026-10-16"], key=lambda r: r["last_modified_utc"])
    print(vol, "laminas MODIS por last_modified (ultima antes de cada hueco y primeras despues):")
    for r in ls:
        d = r["last_modified_utc"][:10]
        if "2026-09-22" <= d <= "2026-10-02" or "2026-10-06" <= d <= "2026-10-13":
            print("  ", r["last_modified_utc"], r["captured_at_utc"][:19], r["png_path"], r["omitido"])
tabla = list(csv.DictReader(open(INS + r"\snapshot_consolidado_base.csv", encoding="utf-8")))
print("columnas tabla:", list(tabla[0].keys()))
mo = [r for r in tabla if r["Sensor"] == "MODIS" and r["Fecha_Satelite_UTC"][:10] in huecos]
print("Filas MODIS de la tabla de MIROVA con fecha en los huecos:", len(mo), collections.Counter(r["Fecha_Satelite_UTC"][:10] for r in mo))
print("Chillan MODIS alrededor de 10-10:", [(r["Fecha_Satelite_UTC"], r["VRP_MW"], r["Distancia_km"], r["Tipo_Registro"]) for r in tabla if r["Volcan"].lower().startswith("nevados") and r["Sensor"] == "MODIS" and "2026-10-09" <= r["Fecha_Satelite_UTC"][:10] <= "2026-10-12"][:40])
