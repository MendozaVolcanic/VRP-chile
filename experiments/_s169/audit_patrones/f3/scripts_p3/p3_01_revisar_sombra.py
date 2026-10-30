# -*- coding: utf-8 -*-
"""Sondas sobre scripts/revisar_sombra.py (arbol cc3887290). Solo importa y llama a revisar(); no escribe en el arbol.

PREGUNTA 1 (si lo medido estuviera roto, lo veria?): cada caso trae un control positivo (la misma funcion SI da
FALLA cuando corresponde). PREGUNTA 2 (si el instrumento estuviera muerto?): un `revisar` que devolviera siempre
(True, ...) daria distinto en los controles, asi que no esta muerto.
Ventana de los datos: sinteticos, 2026-11-03 a 2026-11-10 (el rango que usaria el workflow el 2026-11-10).
"""
import sys
sys.path.insert(0, r"D:/vrp-trabajo/temporales/s169_audit_patrones/f3_comun/arbol/scripts")
from revisar_sombra import revisar

def rec(dia, hora, sensor, via=True):
    return {"datetime_utc": f"{dia} {hora}", "sensor": sensor, "via_codigo_mirova": via}

# Estado del JSON el 2026-11-10 a las 15:00 UTC: dias 03..09 ya commiteados por corridas anteriores (los tres sensores).
previos = []
for d in range(3, 10):
    dia = f"2026-11-{d:02d}"
    previos += [rec(dia, "05:10", "VIIRS_NOAA20"), rec(dia, "05:20", "VIIRS_NOAA20_750"), rec(dia, "02:30", "MODIS_AQUA")]

print("== CASO A: HOY la corrida no produjo NADA (NASA caido: log con Cobertura INCOMPLETA, 0 records nuevos)")
log_vacio = "Cobertura INCOMPLETA: 40 busquedas o descargas fallidas.\nDone.\n"
ok, res = revisar(previos, log_vacio, "2026-11-03", "2026-11-10")
print("   ok =", ok, "|", res)
print("   (esperado por el diseño: ok=False, 'cero es una falla, aunque sea de NASA')")

print("== CONTROL A: primer dia (11-03), mismo log vacio y sin records previos")
ok, res = revisar([], log_vacio, "2026-11-03", "2026-11-03")
print("   ok =", ok, "|", res)

print("== CASO B: la corrida solo produjo VIIRS 375; MODIS y VIIRS 750 no produjeron ningun record en 8 dias")
solo375 = [r for r in previos if r["sensor"] == "VIIRS_NOAA20"]
ok, res = revisar(solo375, "", "2026-11-03", "2026-11-10")
print("   ok =", ok, "|", res)

print("== CASO C: record anterior a la fecha minima dentro del json (11-02 23:57), ventana 11-03..11-10")
ok, res = revisar(previos + [rec("2026-11-02", "23:57", "MODIS_TERRA")], "", "2026-11-03", "2026-11-10")
print("   ok =", ok, "|", res)

print("== CASO D: log con 'Cobertura NO COMPLETA' + 'sin_geolocalizacion' (MODIS sin MOD03) y 'faltan plataformas'")
log_inc = ("Cobertura: faltan plataformas enteras (nota, no es busqueda fallida).\n"
           "Cobertura NO COMPLETA: 22 incidencias (ninguna busqueda ni descarga fallida).\n"
           "  L1B sin geolocalizacion (descartados sin procesar); cuenta en modo estricto:\n")
ok, res = revisar(previos, log_inc, "2026-11-03", "2026-11-10")
print("   ok =", ok, "|", res)

print("== CONTROL de instrumento: un 'ERROR processing' si se ve")
ok, res = revisar(previos, "  ERROR processing VNP02IMG.A2026314.0510: No module named 'pyproj'", "2026-11-03", "2026-11-10")
print("   ok =", ok, "|", res)
