# T1. Pregunta 1: si el control por dia estuviera roto, ¿se veria? Si: hay escenarios con veredicto esperado distinto
# (ok / FALLA) y el script imprime ESPERADO vs OBTENIDO; un revisar() que siempre diera ok o siempre FALLA fallaria en al menos uno.
# Pregunta 2: instrumento muerto -> si importar revisar fallara, el script no imprime nada (no es ok implicito).
# Sobre scripts/revisar_sombra.py de cd8b7074f. Ventanas sinteticas del 2026-11-03 al 11-05; denominador: 15 escenarios.
import sys
sys.path.insert(0, "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/arbol")
from scripts.revisar_sombra import revisar
SHA = "s"
DESDE = "2026-11-05T15:00:00Z"
S = {"MODIS": ["MODIS_AQUA"], "VIIRS750": ["VIIRS_NOAA20_750"], "VIIRS375": ["VIIRS_NOAA20"]}
def rec(d, sensor, via=True, hora="05:00:00", proc="2026-11-05T15:10:00Z"):
    return {"datetime_utc": f"{d}T{hora}Z", "sensor": sensor, "via_codigo_mirova": via, "processed_utc": proc, "regimen": {"codigo_sha": SHA}}
def todos(dias, omit=()):
    return [rec(d, s) for d in dias for s in ("MODIS_AQUA", "VIIRS_NOAA20", "VIIRS_NOAA20_750") if (d, s) not in omit]
PLAT_REAL = {p: {"con_granulos": 3, "sin_granulos": 0, "retirada": 0, "cese_desde": None} for p in
             ["MODIS_TERRA","MODIS_AQUA","VIIRS_NOAA20","VIIRS_NOAA21","VIIRS_NOAA20_750","VIIRS_NOAA21_750"]}
PLAT_REAL.update({p: {"con_granulos": 0, "sin_granulos": 0, "retirada": 3, "cese_desde": "2026-11-02T13:00:00Z"} for p in ["VIIRS_SNPP","VIIRS_SNPP_750"]})
def cob(inc=(), fallas=()):
    return {"fallas": list(fallas), "plataformas": PLAT_REAL, "incidencias": list(inc)}
def sg(d, *plats, tipo="sin_granulos"): return [{"tipo": tipo, "fecha": d, "plataforma": p} for p in plats]
D = ["2026-11-03", "2026-11-04", "2026-11-05"]
esc = [
 ("01 todo presente", todos(D), cob(), "2026-11-03", "2026-11-05", True),
 ("02 dia medio sin MODIS, sin prueba", todos(D, {("2026-11-04","MODIS_AQUA")}), cob(), "2026-11-03", "2026-11-05", False),
 ("03 dia medio sin MODIS, Terra y Aqua sin granulos", todos(D, {("2026-11-04","MODIS_AQUA")}), cob(sg("2026-11-04","MODIS_TERRA","MODIS_AQUA")), "2026-11-03", "2026-11-05", True),
 ("04 dia medio sin MODIS, solo Aqua sin granulos (Terra tuvo granulos de dia)", todos(D, {("2026-11-04","MODIS_AQUA")}), cob(sg("2026-11-04","MODIS_AQUA")), "2026-11-03", "2026-11-05", False),
 ("05 primer dia sin MODIS, sin prueba", todos(D, {("2026-11-03","MODIS_AQUA")}), cob(), "2026-11-03", "2026-11-05", False),
 ("06 ultimo dia sin MODIS, sin prueba", todos(D, {("2026-11-05","MODIS_AQUA")}), cob(), "2026-11-03", "2026-11-05", False),
 ("07 prueba de otro dia no vale", todos(D, {("2026-11-04","MODIS_AQUA")}), cob(sg("2026-11-05","MODIS_TERRA","MODIS_AQUA")), "2026-11-03", "2026-11-05", False),
 ("08 otro tipo de incidencia no es prueba", todos(D, {("2026-11-04","MODIS_AQUA")}), cob(sg("2026-11-04","MODIS_TERRA","MODIS_AQUA", tipo="sin_geolocalizacion")), "2026-11-03", "2026-11-05", False),
 ("09 V750 y V375 vacios el mismo dia (SNPP retirada): catalogo vacio", todos(D, {("2026-11-04","VIIRS_NOAA20"),("2026-11-04","VIIRS_NOAA20_750")}),
    cob(sg("2026-11-04","VIIRS_NOAA20","VIIRS_NOAA21","VIIRS_NOAA20_750","VIIRS_NOAA21_750")), "2026-11-03", "2026-11-05", False),
 ("10 solo V375 vacio con NOAA20 y NOAA21 sin granulos y SNPP retirada: NOTA", todos(D, {("2026-11-04","VIIRS_NOAA20")}),
    cob(sg("2026-11-04","VIIRS_NOAA20","VIIRS_NOAA21")), "2026-11-03", "2026-11-05", True),
 ("11 solo V375 vacio, NOAA21 si tuvo granulos", todos(D, {("2026-11-04","VIIRS_NOAA20")}),
    cob(sg("2026-11-04","VIIRS_NOAA20")), "2026-11-03", "2026-11-05", False),
 ("12 dia con solo un K es dia perdido", [r for r in todos(D) if not (r["datetime_utc"].startswith("2026-11-04") and r["sensor"]=="MODIS_AQUA")] + [rec("2026-11-04","MODIS_AQUA",via=False,proc="2026-11-04T15:10:00Z")], cob(), "2026-11-03", "2026-11-05", False),
 ("13 dias anteriores a la fecha minima no se juzgan (ini=2026-10-30)", todos(D), cob(), "2026-10-30", "2026-11-05", True),
 ("14 ventana de un solo dia, MODIS falta", todos(["2026-11-03"], {("2026-11-03","MODIS_AQUA")}), cob(), "2026-11-03", "2026-11-03", False),
 ("15 corrida que no escribio nada (todo con processed_utc anterior)", [dict(r, processed_utc="2026-11-04T15:10:00Z") for r in todos(D)], cob(), "2026-11-03", "2026-11-05", False),
]
mal = 0
for nombre, regs, c, ini, fin, esperado in esc:
    ok, res = revisar(regs, "", ini, fin, DESDE, c, sha=SHA)
    marca = "ok   " if ok == esperado else "DISTINTO"
    mal += ok != esperado
    print(f"[{marca}] {nombre}: esperado {'verde' if esperado else 'FALLA'}, obtenido {'verde' if ok else 'FALLA'}")
    for ln in res.splitlines():
        if "FALLA" in ln or "NOTA" in ln: print("      ", ln.strip()[:200])
print("escenarios distintos de lo esperado:", mal, "de", len(esc))
