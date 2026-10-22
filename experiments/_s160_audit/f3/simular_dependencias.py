"""F3 (S160): cómo falla el NRT cuando cae cada dependencia externa de la cadena de descarga.

Sin red: earthaccess.search_data, earthaccess.login, earthaccess.download, time.sleep y el probe TCP se
reemplazan en memoria. Se llama al fetch_for_volcano REAL del árbol que se pase (instantánea de main o
de la rama de PR #889) y después a run_pipeline.informar_cobertura, como hace run_pipeline.main (NRT no
usa --estricto-cobertura). No escribe en data/: tmp_dir es la CARPETA y la descarga está simulada.

Uso: python -I simular_dependencias.py <arbol> > salida.txt

Pregunta 1 (por escenario): si esa dependencia cayera y el pipeline lo viera, aparecería una falla de
cobertura, una incidencia, una excepción o un código de salida distinto de 0.
Pregunta 2 (instrumento): los controles positivos del plan tienen que reproducirse ANTES de leer el
resto: SNPP vacío = «Cobertura: completa» y código 0; SNPP timeout = «Cobertura INCOMPLETA» y código 0;
todo vacío = «completa» (R2-9); L1B sin geo = descartado sin falla (VB-1). Si no se reproducen, el
simulador no está midiendo el código real y la salida no vale.
Control de contraste: con todo vivo salen las 8 plataformas.

Escenarios (dependencia que cae):
  vivo                    control de contraste
  snpp_vacio              Suomi NPP cesa (2026-11-02): VNP* devuelve []
  snpp_timeout            control positivo del plan: VNP* lanza ConnectTimeout
  noaa21_version_cambia   CMR deja de servir VJ2* en version 2.1 (solo se pide esa)
  noaa20_vacio            NOAA-20 calla (sin cese anunciado)
  modis61_decomiso        MOD/MYD 6.1 Standard []; 6.1NRT sigue: cae al NRT
  modis61_y_nrt_vacios    la 6.1 muere entera (Standard y NRT)
  todo_vacio              CMR responde vacio para todo (R2-9, como el 2026-10-18)
  cmr_http500             CMR devuelve HTTP 500 en cada busqueda
  cmr_timeout             CMR en Timeout: cortacircuito S116
  descarga_timeout        host de descarga (nrt3.modaps, A64) en ConnectTimeout
  l1b_sin_geo             L1B con 2 granulos y GEO con 1 (VB-1)
  cred_401                NASA rechaza la credencial (token vencido) en la descarga
  token_vacio             EARTHDATA_TOKEN vacio: auth cae al par usuario y clave (vencido, A71)
"""
import io
import os
import sys
import time
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve()
os.chdir(ARBOL)
sys.path.insert(0, str(ARBOL))
sys.path.insert(0, str(ARBOL / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
os.environ["EARTHDATA_TOKEN"] = "x"
os.environ["EARTHDATA_USERNAME"] = "x"
os.environ["EARTHDATA_PASSWORD"] = "x"
os.environ.pop("GITHUB_ACTIONS", None)
os.environ.pop("GITHUB_STEP_SUMMARY", None)

import requests  # noqa: E402
from pipeline import fetch  # noqa: E402
import run_pipeline  # noqa: E402

TMP = Path(os.environ.get("F3_TMP", str(ARBOL.parent / "tmp_sim")))
TMP.mkdir(parents=True, exist_ok=True)

LLAMADAS = Counter()
LOGINS = Counter()
SLEEPS = []
ESC = {"modo": "vivo"}


def granulo(t, host="https://ladsweb.modaps.eosdis.nasa.gov/x.nc"):
    return {"umm": {"TemporalExtent": {"RangeDateTime": {"BeginningDateTime": t, "EndingDateTime": t}},
                    "GranuleUR": f"g{t}", "RelatedUrls": [{"URL": host, "Type": "GET DATA"}]}}


class _Resp:
    def __init__(self, code):
        self.status_code = code


def _error_http(code, texto):
    e = RuntimeError(texto)
    causa = requests.exceptions.HTTPError(texto)
    causa.response = _Resp(code)
    e.__cause__ = causa
    return e


def falso_search(short_name, version, bounding_box, temporal, count):
    LLAMADAS[(short_name, str(version))] += 1
    m = ESC["modo"]
    es_nrt = "NRT" in short_name or "NRT" in str(version)
    es_snpp = short_name.startswith("VNP")
    es_n20 = short_name.startswith("VJ1")
    es_n21 = short_name.startswith("VJ2")
    es_modis = short_name.startswith(("MOD", "MYD"))
    t = f"{temporal[0]}T05:00:00.000Z"
    if m == "cmr_http500":
        raise _error_http(500, "<html>500 Internal Server Error</html>")
    if m == "cmr_timeout":
        raise requests.exceptions.ReadTimeout("simulado CMR")
    if m == "todo_vacio":
        return []
    if m == "snpp_vacio" and es_snpp:
        return []
    if m == "snpp_timeout" and es_snpp:
        raise requests.exceptions.ConnectTimeout("simulado")
    if m == "noaa21_version_cambia" and es_n21:
        return []          # CMR ya no sirve "2.1"; el codigo no pide otra
    if m == "noaa20_vacio" and es_n20:
        return []
    if m == "modis61_decomiso" and es_modis and not es_nrt:
        return []          # Standard 6.1 decomisado; NRT 6.1 sigue
    if m == "modis61_y_nrt_vacios" and es_modis:
        return []
    if m == "l1b_sin_geo":
        if "03" in short_name:
            return [granulo(t)]
        return [granulo(t), granulo(f"{temporal[0]}T06:30:00.000Z")]
    if es_nrt:
        return []          # el Standard respondio: no se consulta el NRT (como en dias viejos)
    return [granulo(t)]


def falso_download(granules, local_path=None):
    m = ESC["modo"]
    if m == "descarga_timeout":
        raise requests.exceptions.ConnectTimeout("simulado nrt3.modaps")
    if m == "cred_401":
        raise _error_http(401, '{"error":"Token has expired"}')
    out = []
    for g in granules:
        p = Path(local_path) / (g["umm"]["GranuleUR"].replace(":", "-") + ".nc")
        p.write_bytes(b"")
        out.append(str(p))
    return out


def falso_login(strategy=None, **kw):
    LOGINS[strategy] += 1
    if ESC["modo"] == "token_vacio":
        raise RuntimeError("Authentication with Earthdata Login failed with:\ninvalid_credentials")
    return True


fetch.earthaccess.search_data = falso_search
fetch.earthaccess.download = falso_download
fetch.earthaccess.login = falso_login
fetch._probe_nasa_auth = lambda timeout=5.0: True
fetch._probe_download_host = lambda h: False
time.sleep = lambda s: SLEEPS.append(s)

volcan = {"name": "Villarrica", "lat": -39.42, "lon": -71.94, "radius_km": 25}
fecha = datetime(2026, 11, 5)
ESCENARIOS = ["vivo", "snpp_vacio", "snpp_timeout", "noaa21_version_cambia", "noaa20_vacio",
              "modis61_decomiso", "modis61_y_nrt_vacios", "todo_vacio", "cmr_http500", "cmr_timeout",
              "descarga_timeout", "l1b_sin_geo", "cred_401", "token_vacio"]

tiene_incidencias = hasattr(fetch, "incidencias_de_cobertura")
print(f"arbol={ARBOL}  incidencias_de_cobertura={'si' if tiene_incidencias else 'no'}")
print("escenario | plataformas con resultado | fallas | incidencias | excepcion | mensaje cobertura | codigo NRT | codigo estricto | logins | sleeps_s")
for modo in ESCENARIOS:
    ESC["modo"] = modo
    LLAMADAS.clear(); LOGINS.clear(); SLEEPS.clear()
    fetch.limpiar_fallas()
    fetch.reset_transient_breakers()
    fetch.reiniciar_ventana()
    if modo == "token_vacio":
        os.environ["EARTHDATA_TOKEN"] = ""
    else:
        os.environ["EARTHDATA_TOKEN"] = "x"
    exc = ""
    res = {}
    try:
        res = fetch.fetch_for_volcano(volcan, fecha, TMP / modo, nighttime_only=False)
    except Exception as e:
        exc = f"{type(e).__name__}: {str(e)[:70]}"
    fallas = fetch.fallas_de_cobertura()
    inc = fetch.incidencias_de_cobertura() if tiene_incidencias else []
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        kw = {"incidencias": inc} if tiene_incidencias else {}
        cod = run_pipeline.informar_cobertura(fallas, ruta_json=None, estricto=False, **kw)
        cod_e = run_pipeline.informar_cobertura(fallas, ruta_json=None, estricto=True, **kw)
    finally:
        sys.stdout = old
    msg = buf.getvalue().splitlines()[0] if buf.getvalue() else "?"
    # Si fetch_for_volcano lanzo, run_pipeline no llega a informar_cobertura: el proceso muere con traceback.
    cod_real = "traceback (exit 1)" if exc else cod
    plats = sorted(k for k, v in res.items() if v)
    print(f"{modo} | {len(plats)}: {','.join(p.replace('VIIRS_', 'V').replace('MODIS_', 'M') for p in plats)} | "
          f"{len(fallas)} | {len(inc)} {[i['tipo'] for i in inc][:4]} | {exc or '-'} | {msg[:60]} | "
          f"{cod_real} | {cod_e} | {dict(LOGINS)} | {sum(SLEEPS):.0f}")
    if modo == "l1b_sin_geo":
        n_l1b = sum(1 for k in LLAMADAS if "02" in k[0] or "021KM" in k[0])
        print(f"    l1b_sin_geo detalle: archivos devueltos por plataforma = "
              f"{ {k: len(v) for k, v in res.items()} }")
    if modo in ("modis61_decomiso",):
        print(f"    consultas MODIS: { {k: v for k, v in LLAMADAS.items() if k[0].startswith(('MOD', 'MYD'))} }")
    if modo == "noaa21_version_cambia":
        print(f"    consultas VJ2*: { {k: v for k, v in LLAMADAS.items() if k[0].startswith('VJ2')} }")
