# T3. Pregunta 1: si main() soltara traceback con un insumo malo, ¿esto lo veria? Si: busca "Traceback" en stderr.
# Pregunta 2: instrumento muerto = el control positivo (insumo sano) tiene que dar rc 0 y los controles de falla conocida rc 1;
# si el script de la medicion no corriera, rc seria otro y el caso se marca ERROR_INSTRUMENTO.
# Denominador: N casos declarados abajo. Sobre scripts/revisar_sombra.py de cd8b7074f (arbol/).
import json, subprocess, sys, os, tempfile, pathlib
PY = sys.executable
ARB = "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/arbol"
TMP = pathlib.Path("D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/medidas/fuzz_tmp"); TMP.mkdir(exist_ok=True)
SHA = "abc123"
def rec(dia, sensor, via=True):
    return {"datetime_utc": f"{dia}T05:00:00Z", "sensor": sensor, "via_codigo_mirova": via,
            "processed_utc": "2026-11-04T15:05:00Z", "regimen": {"codigo_sha": SHA}}
sano = {"records": [rec(d, s) for d in ("2026-11-03", "2026-11-04") for s in ("MODIS_AQUA", "VIIRS_NOAA20", "VIIRS_NOAA20_750")]}
cob_ok = {"fallas": [], "plataformas": {}, "incidencias": [], "n": 0}
def escribir(nombre, contenido, binario=False):
    p = TMP / nombre
    if isinstance(contenido, (bytes, bytearray)): p.write_bytes(contenido)
    elif isinstance(contenido, str): p.write_text(contenido, encoding="utf-8")
    else: p.write_text(json.dumps(contenido), encoding="utf-8")
    return str(p)
def correr(nombre, js, cob, desde="2026-11-04T15:00:00Z", ini="2026-11-03", fin="2026-11-04", log=None):
    if isinstance(js, pathlib.Path): jsp = str(js)
    elif js == "AUSENTE": jsp = str(TMP / "no_existe.json")
    else: jsp = escribir(nombre + "_js.json", js)
    if cob == "AUSENTE": cp = str(TMP / "no_existe_cob.json")
    elif isinstance(cob, pathlib.Path): cp = str(cob)
    else: cp = escribir(nombre + "_cob.json", cob)
    lg = log or escribir(nombre + ".log", "")
    r = subprocess.run([PY, "-B", ARB + "/scripts/revisar_sombra.py", "--json", jsp, "--log", lg, "--cobertura-json", cp,
                        "--ini", ini, "--fin", fin, "--desde-utc", desde, "--sha", SHA],
                       capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r
d_js = TMP / "dir_js"; d_js.mkdir(exist_ok=True)
casos = [
 ("CONTROL_sano", sano, cob_ok, {}, 0),
 ("CONTROL_sin_records_de_hoy", {"records": []}, cob_ok, {}, 1),
 ("json_truncado", '{"records": [', cob_ok, {}, 1),
 ("json_vacio_0bytes", "", cob_ok, {}, 1),
 ("json_raiz_lista", [], cob_ok, {}, 1),
 ("json_bytes_basura", b"\xff\xfe\x00\x81garbage", cob_ok, {}, 1),
 ("json_records_null", {"records": None}, cob_ok, {}, 1),
 ("json_records_dict", {"records": {"a": 1}}, cob_ok, {}, 1),
 ("json_records_con_null", {"records": [None]}, cob_ok, {}, 1),
 ("json_records_con_int", {"records": [1]}, cob_ok, {}, 1),
 ("json_records_con_str", {"records": ["x"]}, cob_ok, {}, 1),
 ("json_datetime_int", {"records": [{"datetime_utc": 5, "sensor": "MODIS_AQUA", "via_codigo_mirova": True}]}, cob_ok, {}, 1),
 ("json_regimen_str", {"records": [{"datetime_utc": "2026-11-04T05:00:00Z", "sensor": "MODIS_AQUA", "via_codigo_mirova": True, "processed_utc": "2026-11-04T15:05:00Z", "regimen": "x"}]}, cob_ok, {}, 1),
 ("json_es_directorio", d_js, cob_ok, {}, 1),
 ("cob_truncada", sano, '{"fallas": [', {}, 1),
 ("cob_vacia", sano, "", {}, 1),
 ("cob_lista", sano, [], {}, 1),
 ("cob_plataformas_lista", sano, {"plataformas": [], "incidencias": []}, {}, None),
 ("cob_plataformas_null_valor", sano, {"plataformas": {"MODIS_AQUA": None}, "incidencias": []}, {}, None),
 ("cob_incidencias_con_null", sano, {"plataformas": {}, "incidencias": [None]}, {}, None),
 ("cob_incidencias_str", sano, {"plataformas": {}, "incidencias": ["x"]}, {}, None),
 ("cob_fallas_con_null", sano, {"fallas": [None]}, {}, None),
 ("cob_fallas_con_str", sano, {"fallas": ["x"]}, {}, None),
 ("cob_fallas_fecha_null", sano, {"fallas": [{"fecha": None}]}, {}, 1),
 ("cob_fallas_fecha_int", sano, {"fallas": [{"fecha": 5}]}, {}, None),
 ("cob_plataformas_cese_int", sano, {"plataformas": {"VIIRS_SNPP": {"retirada": 1, "cese_desde": 5}}, "incidencias": []}, {}, None),
 ("cob_ausente", sano, "AUSENTE", {}, 1),
 ("desde_vacio", sano, cob_ok, {"desde": ""}, 1),
 ("desde_basura", sano, cob_ok, {"desde": "ayer"}, 1),
 ("ini_vacio", sano, cob_ok, {"ini": ""}, None),
 ("fin_basura", sano, cob_ok, {"fin": "hoy"}, None),
 ("ini_fin_invertidos", sano, cob_ok, {"ini": "2026-11-04", "fin": "2026-11-03"}, None),
 ("log_es_directorio", sano, cob_ok, {"log": str(d_js)}, None),
]
tot = 0; tb = []
filas = []
for nombre, js, cob, kw, esperado in casos:
    r = correr(nombre, js, cob, **kw)
    traceback = "Traceback" in r.stderr
    kline = "K caídos en la ventana" in r.stdout
    falla = "FALLA" in r.stdout
    estado = ("TRACEBACK" if traceback else "sin traceback")
    if esperado is not None and r.returncode != esperado and not traceback:
        estado += f" | RC {r.returncode} (esperado {esperado})"
    if nombre.startswith("CONTROL") and r.returncode != esperado:
        estado = "ERROR_INSTRUMENTO"
    filas.append((nombre, r.returncode, traceback, kline, falla, estado))
    print(f"{nombre:34s} rc={r.returncode} traceback={traceback!s:5} linea_K={kline!s:5} FALLA_en_stdout={falla!s:5} {estado}")
    if traceback:
        print("      ultima linea stderr:", r.stderr.strip().splitlines()[-1][:150])
print("N casos:", len(casos), "| con traceback:", sum(1 for f in filas if f[2]))
