"""M2. Casos de scripts/revisar_sombra.py::revisar (arbol de 16d9e894d) llamado directo, con la estructura REAL de
cobertura de pipeline/fetch.py (plataformas con con_granulos/sin_granulos/retirada/cese_desde; incidencias con tipo,
fecha, plataforma).
PREGUNTAS DEL INSTRUMENTO
1) Si revisar estuviera roto (cuenta toda la ventana), ¿esta medicion lo veria? Si: el caso B (corrida vacia) tiene que dar
   FALLA; el caso A (sana) tiene que dar OK. Los dos controles se imprimen primero.
2) Si el instrumento estuviera muerto (siempre OK o siempre FALLA) el conjunto A..L se veria constante; no lo es.
Denominador: 12 casos sinteticos; ventana 2026-11-03..2026-11-06; sin datos de produccion."""
import sys, json
sys.path.insert(0, "D:/vrp-trabajo/temporales/s169_ver_vigilancia/arbol/scripts")
import revisar_sombra as R

FIN, INI = "2026-11-06", "2026-11-03"
DESDE = "2026-11-06T15:00:05Z"
SHA = "S" * 40
SENS = {"MODIS": "MODIS_AQUA", "VIIRS750": "VIIRS_NOAA20_750", "VIIRS375": "VIIRS_NOAA20"}

def rec(dia, fam, proc, via=True, sha=SHA, hora="06:12"):
    return {"datetime_utc": f"2026-11-{dia:02d} {hora}", "sensor": SENS[fam], "via_codigo_mirova": via,
            "processed_utc": proc, "regimen": {"codigo_sha": sha}}

def nuevos(dia=6, fams=("MODIS", "VIIRS750", "VIIRS375")):
    return [rec(dia, f, f"2026-11-06T15:20:{i:02d}Z") for i, f in enumerate(fams)]

PL = ["MODIS_TERRA", "MODIS_AQUA", "VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"]
def cob(vacias=(), fallas=0, plataformas=None, fecha=FIN):
    plat = {}
    for p in PL:
        if "SNPP" in p:
            plat[p] = {"con_granulos": 0, "sin_granulos": 0, "retirada": 4, "cese_desde": "2026-11-02T13:00:00Z"}
        else:
            plat[p] = {"con_granulos": 4, "sin_granulos": 0, "retirada": 0, "cese_desde": None}
    inc = [{"tipo": "sin_granulos", "cuenta_estricto": False, "volcan": "Lascar", "fecha": fecha, "plataforma": p, "motivo": ""} for p in vacias]
    return {"fallas": [{"volcan": None, "fecha": FIN, "plataforma": "x", "producto": "x", "etapa": "busqueda", "motivo": "t"}] * fallas,
            "plataformas": plat if plataformas is None else plataformas, "incidencias": inc}

def run(nombre, regs, cobertura, desde=DESDE, log=""):
    ok, res = R.revisar(regs, log, INI, FIN, desde, cobertura, sha=SHA)
    print(f"--- {nombre}: {'OK' if ok else 'FALLA'}\n{res}\n")
    return ok

todos_vacios = ["MODIS_TERRA", "MODIS_AQUA", "VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"]
old = lambda dia, fam, proc: rec(dia, fam, proc)
run("A control sano", nuevos(), cob())
run("B control corrida vacia (records de ayer, ninguno nuevo)", [rec(5, f, "2026-11-05T15:20:00Z") for f in SENS], cob())
run("C FUGA: ningun record de hoy, pero 3 NRT->standard de dias 3 y 4 reescritos hoy", [rec(3, "MODIS", "2026-11-06T15:30:00Z"), rec(4, "VIIRS750", "2026-11-06T15:30:01Z"), rec(4, "VIIRS375", "2026-11-06T15:30:02Z")], cob())
run("D SNPP retirada + V750 sin granulos en NOAA20 y NOAA21 (miro y no hubo)", nuevos(fams=("MODIS", "VIIRS375")), cob(vacias=["VIIRS_NOAA20_750", "VIIRS_NOAA21_750"]))
run("D2 V750: NOAA20 vacia pero NOAA21 con granulos y sin record", nuevos(fams=("MODIS", "VIIRS375")), cob(vacias=["VIIRS_NOAA20_750"]))
run("E CATALOGO VACIO (R2-13): todas las plataformas vivas responden [] en los 3 sensores", [rec(5, f, "2026-11-05T15:20:00Z") for f in SENS], cob(vacias=todos_vacios))
run("F cobertura con plataformas vacio {} (instrumento muerto)", nuevos(fams=("MODIS", "VIIRS375")), cob(plataformas={}))
run("H incidencia sin_granulos de OTRO dia (no fin)", nuevos(fams=("MODIS", "VIIRS375")), cob(vacias=["VIIRS_NOAA20_750", "VIIRS_NOAA21_750"], fecha="2026-11-05"))
run("J record con processed_utc == desde exacto", [rec(6, f, DESDE) for f in SENS], cob())
run("K1 B3: record de K de ayer (processed antes de desde)", nuevos() + [rec(5, "MODIS", "2026-11-05T15:20:09Z", via="geo_distinta")], cob())
run("K2 B3: record de K de hoy", nuevos() + [rec(6, "MODIS", "2026-11-06T15:21:09Z", via="geo_distinta", hora="05:00")], cob())
run("L K viejo reescrito hoy por upgrade NRT->standard", nuevos() + [rec(3, "MODIS", "2026-11-06T15:30:09Z", via="geo_distinta")], cob())
run("M fallas de busqueda en cobertura (1)", nuevos(), cob(fallas=1))
try:
    R.revisar(nuevos(), "", INI, FIN, "", cob(), sha=SHA)
except Exception as e:
    print("--- N desde-utc vacio:", type(e).__name__, e)
