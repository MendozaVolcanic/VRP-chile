# -*- coding: utf-8 -*-
"""F4T (S175), instrumento 3: corre scripts/run_pipeline.py de la base (copia privada en repo_base) con la red
interceptada, y mide qué código de salida y qué log deja el pipeline cuando NASA rechaza la credencial, en cada
una de las formas que earthaccess puede entregar. Después aplica a ese resultado los pasos siguientes de nrt.yml
(leídos del YAML de la base) para decir de qué color queda el job.

Las dos preguntas:
1. Si el pipeline quedara verde sin producir, ¿se ve? Sí: exit 0 + «Cobertura INCOMPLETA» + 0 records escritos.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Sí: el control positivo rojo («cmr401_expired», la
   forma que el proyecto ya midió en octubre de 2026) tiene que salir con exit 1 y EARTHDATA_CREDENTIAL_INVALID; y el
   control «descarga_ok_archivo_falso» tiene que llegar hasta el procesador (líneas «ERROR processing»).

Red: socket.connect y socket.getaddrinfo quedan parchados en sitecustomize (ninguna consulta DNS ni conexión sale);
earthaccess.search_data y earthaccess.download se reemplazan por dobles. Ningún token real: los tokens son texto
inventado o un JWT sintético. time.sleep es no-op (los 22 min de reintentos se vuelven segundos).
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\f4t\repo_base")
TMP = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\f4t\tmp_03")
CARPETA = Path(__file__).resolve().parent
TMP.mkdir(parents=True, exist_ok=True)
PARCHE = TMP / "parche"
PARCHE.mkdir(exist_ok=True)

SITECUSTOMIZE = r'''
# sitecustomize del instrumento F4T: se carga antes que el pipeline (PYTHONPATH). Decide por F4T_ESCENARIO.
import os, socket, time, json
from pathlib import Path

ESC = os.environ.get("F4T_ESCENARIO", "")
MARCAS = Path(os.environ["F4T_MARCAS"])

def _marca(linea):
    with open(MARCAS, "a", encoding="utf-8") as fh:
        fh.write(linea + "\n")

# --- red: nada sale. DNS devuelve 127.0.0.1; connect falla, salvo el probe TCP a URS si F4T_PROBE_OK=1 ---
def _getaddrinfo(host, port, *a, **k):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", int(port) if port else 0))]
socket.getaddrinfo = _getaddrinfo

class _Dummy:
    def close(self): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False

_orig_create = socket.create_connection
def _create_connection(address, *a, **k):
    host, port = address[0], address[1]
    if os.environ.get("F4T_PROBE_OK") == "1" and port == 443 and "urs.earthdata" in str(host):
        _marca(f"PROBE_TCP_SIMULADO_OK {host}:{port}")
        return _Dummy()
    _marca(f"RED_BLOQUEADA create_connection {host}:{port}")
    raise OSError("RED BLOQUEADA POR EL INSTRUMENTO F4T")
socket.create_connection = _create_connection

def _connect(self, address):
    _marca(f"RED_BLOQUEADA connect {address}")
    raise OSError("RED BLOQUEADA POR EL INSTRUMENTO F4T")
socket.socket.connect = _connect

time.sleep = lambda *_a, **_k: None

# --- earthaccess: dobles ---
import requests
import earthaccess
from earthaccess.exceptions import DownloadFailure

URL = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD021KM/2026/307/MOD021KM.A2026307.0500.061.hdf"

class Granulo(dict):
    def data_links(self):
        return [URL]
    def __hash__(self):
        return id(self)

def _granulo(short_name):
    return Granulo({"umm": {"GranuleUR": f"{short_name}.A2026307.0500.061.2026307120000",
                            "TemporalExtent": {"RangeDateTime": {"BeginningDateTime": "2026-11-03T05:00:00.000Z",
                                                                 "EndingDateTime": "2026-11-03T05:05:00.000Z"}}}})

def _cmr_error(status, body):
    resp = requests.Response(); resp.status_code = status; resp._content = body
    try:
        resp.raise_for_status()
    except requests.HTTPError as ex:
        e = RuntimeError(ex.response.text); e.__cause__ = ex
        return e

def search_data(short_name=None, version=None, **k):
    _marca(f"SEARCH {short_name} v{version}")
    if ESC == "cmr401_expired":
        raise _cmr_error(401, b'{"errors":["Token [ABC] has expired. Please get a new token"]}')
    if ESC == "cmr401_noexist":
        raise _cmr_error(401, b'{"errors":["Token does not exist"]}')
    return [_granulo(short_name)]

def download(granules, local_path=None, **k):
    _marca(f"DOWNLOAD n={len(granules)}")
    if ESC in ("descarga401", "descarga401_jwt_vencido"):
        raise DownloadFailure(f"Download failed for {URL}. Status code: 401")
    if ESC == "descarga403":
        raise DownloadFailure(f"Download failed for {URL}. Status code: 403")
    if ESC == "descarga_ok_archivo_falso":
        out = []
        Path(local_path).mkdir(parents=True, exist_ok=True)
        for g in granules:
            p = Path(local_path) / (g["umm"]["GranuleUR"].split(".061.")[0] + ".061.hdf")
            p.write_bytes(b"NO ES UN HDF")
            out.append(str(p))
        return out
    raise RuntimeError("escenario sin regla de descarga: " + ESC)

_login_real = earthaccess.login
def login(*a, **k):
    _marca(f"LOGIN strategy={k.get('strategy', a[0] if a else '?')} token_vacio={os.environ.get('EARTHDATA_TOKEN','')==''}")
    return _login_real(*a, **k)

earthaccess.search_data = search_data
earthaccess.download = download
earthaccess.login = login
'''
(PARCHE / "sitecustomize.py").write_text(SITECUSTOMIZE, encoding="utf-8")


def jwt_sintetico(exp: datetime) -> str:
    def b64(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return b64({"alg": "RS256", "typ": "JWT"}) + "." + b64({"exp": int(exp.timestamp()), "uid": "f4t-sintetico"}) + ".firma-falsa"


ESCENARIOS = [
    # (nombre, token, probe_ok, descripción)
    ("cmr401_expired", "no-es-un-jwt", "0", "CONTROL+ ROJO: CMR responde 401 'Token has expired' (lo visto el 2026-10-03, AUDITOR_A S150)"),
    ("cmr401_noexist", "no-es-un-jwt", "0", "CMR responde 401 'Token does not exist' (texto fuera del regex)"),
    ("descarga401", "no-es-un-jwt", "0", "CMR acepta la búsqueda; la descarga responde 401 (forma real DownloadFailure)"),
    ("descarga401_jwt_vencido", jwt_sintetico(datetime(2026, 10, 3, 7, 18, tzinfo=timezone.utc)), "0", "igual, con un JWT sintético vencido el 2026-10-03: ¿el pipeline mira exp?"),
    ("descarga403", "no-es-un-jwt", "0", "la descarga responde 403 sin texto de credencial"),
    ("descarga_ok_archivo_falso", "no-es-un-jwt", "0", "CONTROL+ PROCESADOR: la descarga 'funciona' y deja un archivo que no es HDF"),
    ("token_vacio_pre894", "", "1", "LÍNEA BASE ROJA (1) a nivel Python: token vacío llega a auth(); usuario y clave falsos; probe TCP simulado OK"),
]

PASO_A57_RE = re.compile(r"Assert Tier A records fresh")


def correr(nombre: str, token: str, probe_ok: str) -> dict:
    marcas = TMP / f"{nombre}_marcas.txt"
    log = TMP / f"{nombre}_pipeline.log"
    cob = TMP / f"{nombre}_cobertura.json"
    for p in (marcas, log, cob):
        if p.exists():
            p.unlink()
    datos = REPO / "data" / "mirova_equivalent"
    if datos.exists():
        shutil.rmtree(datos)
    tmpdir = TMP / f"{nombre}_tmp"
    env = dict(os.environ)
    env.update({
        "PYTHONPATH": str(PARCHE), "PYTHONIOENCODING": "utf-8",
        "F4T_ESCENARIO": nombre, "F4T_MARCAS": str(marcas), "F4T_PROBE_OK": probe_ok,
        "EARTHDATA_TOKEN": token,
        "EARTHDATA_USERNAME": "usuario-falso" if token == "" else "",
        "EARTHDATA_PASSWORD": "clave-falsa" if token == "" else "",
        "VRP_TMP_DIR": str(tmpdir), "GITHUB_ACTIONS": "true",
        "GITHUB_STEP_SUMMARY": str(TMP / f"{nombre}_summary.md"),
    })
    for k in ("VRP_CACHE_BUSQUEDA_DIR", "VRP_VENTANA_BUSQUEDA"):
        env.pop(k, None)
    env["HOME"] = str(TMP / "home_sin_netrc"); (TMP / "home_sin_netrc").mkdir(exist_ok=True)
    env["USERPROFILE"] = env["HOME"]
    t0 = time.time()
    r = subprocess.run([sys.executable, "scripts/run_pipeline.py", "--profile", "mirova_equivalent", "--volcano", "Lascar",
                        "--date", "2026-11-03", "--cobertura-json", str(cob)],
                       cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    texto = r.stdout + "\n" + r.stderr
    log.write_text(texto, encoding="utf-8")
    m = marcas.read_text(encoding="utf-8") if marcas.exists() else ""
    res = {
        "escenario": nombre, "exit": r.returncode, "segundos": round(time.time() - t0, 1),
        "logins": m.count("LOGIN "), "busquedas": m.count("SEARCH "), "descargas": m.count("DOWNLOAD "),
        "red_bloqueada": m.count("RED_BLOQUEADA"), "probe_sim": m.count("PROBE_TCP_SIMULADO_OK"),
        "cred_invalid": "EARTHDATA_CREDENTIAL_INVALID" in texto,
        "warn_fetch": texto.count("WARN: Failed to fetch"),
        "cobertura_incompleta": "Cobertura INCOMPLETA" in texto,
        "cobertura_completa": "Cobertura: completa" in texto,
        "error_processing": texto.count("ERROR processing"),
        "traceback": "Traceback" in texto,
        "records_escritos": 0,
    }
    js = datos / "Lascar.json"
    if js.exists():
        try:
            res["records_escritos"] = len(json.loads(js.read_text(encoding="utf-8")).get("records", []))
        except Exception:  # noqa: BLE001
            res["records_escritos"] = -1
    # Pasos siguientes de nrt.yml (base) aplicados al resultado.
    # revisar_errores_modis_nrt: corre si el paso del pipeline terminó (éxito o falla).
    rv = subprocess.run([sys.executable, "scripts/revisar_errores_modis_nrt.py", "--log", str(log), "--volcan", "Lascar"],
                        cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    res["revisar_errores_modis_exit"] = rv.returncode
    # revisar_guardia_modis (lo que haría guardia-k-modis.yml con la misma cobertura y el mismo log)
    if cob.exists():
        rg = subprocess.run([sys.executable, "scripts/revisar_guardia_modis.py", "--json", str(datos / "Lascar.json"),
                             "--log", str(log), "--cobertura-json", str(cob), "--ini", "2026-11-03", "--fin", "2026-11-03",
                             "--desde-utc", "2026-11-03T00:00:00Z", "--sha", "0" * 40],
                            cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
        res["revisar_guardia_exit"] = rg.returncode
        res["revisar_guardia_linea"] = (rg.stdout.strip().splitlines() or [""])[-1][:160]
    else:
        res["revisar_guardia_exit"] = None
        res["revisar_guardia_linea"] = "sin cobertura.json (el proceso murió antes de escribirla)"
    return res


def color_nrt(res: dict) -> str:
    """Color del job de nrt.yml (base) según los pasos leídos del YAML: pipeline (exit) -> A57 (sólo avisa; JSON ausente
    sale 0) -> commit (sin cambios sale 0) -> revisar errores MODIS (rojo sólo con ERROR processing de MOD/MYD021KM)."""
    if res["exit"] != 0:
        return "ROJO (el paso del pipeline falló)"
    if res["revisar_errores_modis_exit"] != 0:
        return "ROJO (revisar_errores_modis_nrt: gránulo MODIS con ERROR processing)"
    return "VERDE"


print("Escenarios (run_pipeline.py --profile mirova_equivalent --volcano Lascar --date 2026-11-03, base 752d348bc, red interceptada)\n")
filas = []
for nombre, token, probe, desc in ESCENARIOS:
    print(f"== {nombre}: {desc}")
    res = correr(nombre, token, probe)
    res["color_nrt"] = color_nrt(res)
    filas.append(res)
    print(f"   exit={res['exit']} en {res['segundos']}s | logins={res['logins']} búsquedas={res['busquedas']} descargas={res['descargas']} "
          f"| red bloqueada={res['red_bloqueada']} probe sim={res['probe_sim']}")
    print(f"   CREDENTIAL_INVALID={res['cred_invalid']} traceback={res['traceback']} WARN fetch={res['warn_fetch']} "
          f"cobertura incompleta={res['cobertura_incompleta']} completa={res['cobertura_completa']} ERROR processing={res['error_processing']} records={res['records_escritos']}")
    print(f"   nrt.yml quedaría: {res['color_nrt']} | revisar_errores_modis exit={res['revisar_errores_modis_exit']} "
          f"| revisar_guardia_modis exit={res['revisar_guardia_exit']}: {res['revisar_guardia_linea']}")
    print()

(CARPETA / "f4t_03_pipeline_simulado_resultados.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
print("Tabla:")
print("| escenario | exit | logins | WARN fetch | cobertura incompleta | records | nrt.yml | guardia/sombra (revisor) |")
print("|---|---|---|---|---|---|---|---|")
for f in filas:
    print(f"| {f['escenario']} | {f['exit']} | {f['logins']} | {f['warn_fetch']} | {f['cobertura_incompleta']} | {f['records_escritos']} | "
          f"{f['color_nrt']} | {'ROJO' if f['revisar_guardia_exit'] else ('VERDE' if f['revisar_guardia_exit'] == 0 else 'ROJO (sin cobertura)')} |")
print(f"\nLogs y marcas por escenario en {TMP}")
