# -*- coding: utf-8 -*-
"""V4T (verificador S175), instrumento 1: earthaccess REAL y pipeline/fetch.py REAL (752d348bc), con la red
interceptada en el transporte (requests.adapters.HTTPAdapter.send). No construye la excepción a mano, como
hacen el auditor F4t y los tests S123/S124: deja que earthaccess la arme con su propio código, desde una
respuesta HTTP sintética. Así mide por otro camino que el auditor.

Las dos preguntas del instrumento:
1. Si lo medido estuviera roto (un rechazo de credencial no aborta), ¿se ve? Sí: la columna «resultado»
   de fetch_for_volcano dice si salió EarthdataCredentialError (aborta, job rojo) o volvió con listas
   vacías y fallas en la cobertura (job verde).
2. Si el instrumento estuviera muerto, ¿se vería distinto? Sí: hay un CONTROL POSITIVO (CMR 401 con texto
   «Token [...] has expired», que el regex sí reconoce) que tiene que dar EarthdataCredentialError, y un
   CONTROL DE VIDA (CMR 200 + descarga 200) que tiene que devolver un archivo en disco. Además se cuentan
   las peticiones que pasaron por el transporte: si fueran 0, el mock no estaba en el camino.

Sin red: se bloquean socket.connect y socket.create_connection; ningún token real (texto sintético).
Uso: python v4t_01_transporte_real.py --ea 017|019 --escenario NOMBRE --salida archivo.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import socket
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--ea", choices=["017", "019"], required=True)
ap.add_argument("--escenario", required=True)
ap.add_argument("--salida", required=True)
ap.add_argument("--token", default="v4t-sintetico-no-es-un-token")
args = ap.parse_args()

TMP = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\v4t")
REPO = TMP / "repo_base"
if args.ea == "019":
    sys.path.insert(0, str(TMP / "ea0190"))
sys.path.insert(0, str(REPO))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
os.environ["EARTHDATA_TOKEN"] = args.token
for k in ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD"):
    os.environ.pop(k, None)
# Que no haya netrc que confunda el camino de auth (sólo se lee, no se crea nada).
HAS_NETRC = os.path.exists(os.path.expanduser("~/.netrc")) or os.path.exists(os.path.expanduser("~/_netrc"))


def _bloquear(*a, **k):
    raise OSError("RED BLOQUEADA POR V4T")


socket.socket.connect = _bloquear  # type: ignore[assignment]
socket.create_connection = _bloquear  # type: ignore[assignment]

import requests  # noqa: E402
from requests.adapters import HTTPAdapter  # noqa: E402
from requests.structures import CaseInsensitiveDict  # noqa: E402

FECHA = datetime(2026, 11, 3)
T0 = "2026-11-03T05:00:00.000Z"
T1 = "2026-11-03T05:04:59.000Z"
DL_L1B = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD021KM/2026/307/MOD021KM.A2026307.0500.061.NRT.hdf"
DL_GEO = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD03/2026/307/MOD03.A2026307.0500.061.NRT.hdf"

ESC = {
    # nombre: (cmr_status, cmr_body, dl_status, dl_body)
    "vida": (200, None, 200, b"HDF-FALSO"),
    "control_cmr401_expired": (401, b'{"errors":["Token [ABC] has expired. Please get a new token"]}', 200, b""),
    "cmr401_noexist": (401, b'{"errors":["Token does not exist"]}', 200, b""),
    "cmr401_vacio": (401, b"", 200, b""),
    "cmr401_jwt_malformado": (401, b'{"errors":["Token is not a valid JWT"]}', 200, b""),
    "cmr401_token_x_invalid": (401, b'{"errors":["Token [x] is invalid"]}', 200, b""),
    "cmr403_eula": (403, b'{"errors":["User does not have permission to access collection"]}', 200, b""),
    "descarga401": (200, None, 401, b"HTTP Basic: Access denied.\n"),
    "descarga401_unauthorized": (200, None, 401, b"Unauthorized"),
    "descarga403": (200, None, 403, b"Forbidden"),
    "descarga403_eula": (200, None, 403, b"Please accept the EULA"),
    "descarga500": (200, None, 500, b"Internal Server Error"),
}
cmr_status, cmr_body, dl_status, dl_body = ESC[args.escenario]
LOG = {"peticiones": [], "por_host": {}}


def _granulo(short, url):
    return {
        "meta": {"concept-id": f"G-{short}-V4T", "provider-id": "LAADS", "native-id": short},
        "umm": {
            "GranuleUR": f"{short}.A2026307.0500.061.NRT",
            "TemporalExtent": {"RangeDateTime": {"BeginningDateTime": T0, "EndingDateTime": T1}},
            "RelatedUrls": [{"URL": url, "Type": "GET DATA"}],
            "SpatialExtent": {}, "CollectionReference": {"ShortName": short, "Version": "61"},
            "DataGranule": {"ArchiveAndDistributionInformation": [{"Size": 1.0, "SizeUnit": "MB"}]},
        },
    }


def _resp(req, status, body, headers=None):
    r = requests.Response()
    r.status_code = status
    r._content = body if body is not None else b""
    r.headers = CaseInsensitiveDict(headers or {})
    r.url = req.url
    r.request = req
    r.reason = {200: "OK", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found", 500: "Server Error"}.get(status, "")
    r.encoding = "utf-8"
    import io as _io
    r.raw = _io.BytesIO(r._content)
    return r


def _send(self, request, **kw):
    url = request.url
    host = url.split("/")[2]
    LOG["peticiones"].append({"metodo": request.method, "url": url[:160],
                              "auth": "Authorization" in request.headers})
    LOG["por_host"][host] = LOG["por_host"].get(host, 0) + 1
    if "cmr.earthdata.nasa.gov" in host:
        if cmr_status != 200:
            return _resp(request, cmr_status, cmr_body, {"Content-Type": "application/json"})
        geo = "MOD03" in url
        g = _granulo("MOD03" if geo else "MOD021KM", DL_GEO if geo else DL_L1B)
        body = json.dumps({"hits": 1, "items": [g]}).encode()
        return _resp(request, 200, body, {"CMR-Hits": "1", "Content-Type": "application/json"})
    if "ladsweb" in host:
        return _resp(request, dl_status, dl_body, {})
    # metadatos de nube (169.254.169.254), urs, etc.: 404 sin cuerpo útil
    return _resp(request, 404, b"", {})


HTTPAdapter.send = _send  # type: ignore[assignment]

out = {"ea": args.ea, "escenario": args.escenario, "netrc_presente": HAS_NETRC}
try:
    import earthaccess  # noqa: E402
    out["earthaccess_version"] = earthaccess.__version__
    out["earthaccess_file"] = earthaccess.__file__
    import pipeline.fetch as fetch  # noqa: E402
    time.sleep = lambda *_: None  # los retrasos de reintento no aportan
    # Volcán mínimo: Láscar, sólo MODIS, para que el escenario sea corto.
    volcan = {"name": "Lascar", "lat": -23.37, "lon": -67.73, "radius_km": 25, "sensors": ["MODIS"]}
    dest = TMP / "tmp_01" / f"{args.ea}_{args.escenario}"
    dest.mkdir(parents=True, exist_ok=True)
    fetch.limpiar_fallas()
    try:
        res = fetch.fetch_for_volcano(volcan, FECHA, dest)
        out["resultado"] = "VOLVIO_SIN_EXCEPCION"
        out["archivos_por_plataforma"] = {k: [str(p) for p in v] for k, v in res.items()}
        out["n_archivos"] = sum(len(v) for v in res.values())
    except fetch.EarthdataCredentialError as e:
        out["resultado"] = "EarthdataCredentialError"
        out["mensaje"] = str(e)[:300]
    except Exception as e:  # noqa: BLE001
        out["resultado"] = f"OTRA_EXCEPCION:{type(e).__name__}"
        out["mensaje"] = str(e)[:300]
        out["tb"] = traceback.format_exc()[-1500:]
    out["fallas_cobertura"] = [{k: f.get(k) for k in ("plataforma", "etapa", "motivo")}
                               for f in fetch.fallas_de_cobertura()]
    # Lo que haría run_pipeline con esas fallas (NRT, sin --estricto-cobertura).
    if out["resultado"] == "VOLVIO_SIN_EXCEPCION":
        sys.path.insert(0, str(REPO / "scripts"))
        try:
            import run_pipeline  # noqa: E402
            out["codigo_salida_run_pipeline"] = run_pipeline.informar_cobertura(
                fetch.fallas_de_cobertura(), plataformas=fetch.cobertura_por_plataforma(),
                incidencias=fetch.incidencias_de_cobertura())
        except Exception as e:  # noqa: BLE001
            out["codigo_salida_run_pipeline"] = f"NO_MEDIDO:{type(e).__name__}:{str(e)[:120]}"
    else:
        out["codigo_salida_run_pipeline"] = "excepcion no atrapada en process_date => exit 1"
except Exception as e:  # noqa: BLE001
    out["resultado"] = f"INSTRUMENTO_FALLO:{type(e).__name__}:{str(e)[:200]}"
    out["tb"] = traceback.format_exc()[-2000:]
out["n_peticiones"] = len(LOG["peticiones"])
out["por_host"] = LOG["por_host"]
out["muestra_peticiones"] = LOG["peticiones"][:6]
Path(args.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: out.get(k) for k in ("ea", "escenario", "resultado", "n_archivos", "codigo_salida_run_pipeline",
                                           "n_peticiones", "por_host")}, ensure_ascii=False))
