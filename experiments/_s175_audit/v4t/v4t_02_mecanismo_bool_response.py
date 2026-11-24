# -*- coding: utf-8 -*-
"""V4T, instrumento 2: ¿por qué se pierde el status HTTP en pipeline/fetch.py::_is_credential_dead (752d348bc)?

Hipótesis a refutar: `resp = (getattr(exc.__cause__, "response") or getattr(exc, "response"))` descarta el
Response de un 401 porque requests.Response.__bool__ devuelve `self.ok` (falso para status >= 400).

Las dos preguntas del instrumento:
1. Si el mecanismo fuera otro, ¿se vería? Sí: el PLACEBO fuerza Response.__bool__ = True; si el status
   siguiera perdido, la hipótesis cae. Si con el placebo el 401 se clasifica, el `or` es la causa.
2. Si el instrumento estuviera muerto: el control con cuerpo «Token [ABC] has expired» tiene que dar
   dead=True por texto en las dos variantes, y el 401 de cuerpo vacío tiene que cambiar de False a True
   sólo con el placebo.
La excepción la arma earthaccess REAL (0.17.0 instalado) desde una respuesta sintética de transporte.
"""
from __future__ import annotations

import io
import os
import socket
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
TMP = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\v4t")
if len(sys.argv) > 1 and sys.argv[1] == "019":
    sys.path.insert(0, str(TMP / "ea0190"))
sys.path.insert(0, str(TMP / "repo_base"))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
os.environ["EARTHDATA_TOKEN"] = "v4t-sintetico-no-es-un-token"


def _b(*a, **k):
    raise OSError("RED BLOQUEADA POR V4T")


socket.socket.connect = _b
socket.create_connection = _b
import requests  # noqa: E402
from requests.adapters import HTTPAdapter  # noqa: E402
from requests.structures import CaseInsensitiveDict  # noqa: E402

BODY = {"vacio": b"", "noexist": b'{"errors":["Token does not exist"]}',
        "expired": b'{"errors":["Token [ABC] has expired. Please get a new token"]}'}
actual = {"body": b""}


def _send(self, req, **kw):
    r = requests.Response()
    r.request, r.url, r.encoding = req, req.url, "utf-8"
    if "cmr.earthdata" in req.url:
        r.status_code, r._content = 401, actual["body"]
    else:
        r.status_code, r._content = 404, b""
    r.headers = CaseInsensitiveDict({})
    return r


HTTPAdapter.send = _send
import earthaccess  # noqa: E402
import pipeline.fetch as fetch  # noqa: E402

print("earthaccess", earthaccess.__version__)
fetch.auth()


def excepcion_real(nombre):
    actual["body"] = BODY[nombre]
    try:
        earthaccess.search_data(short_name="MOD021KM", version="6.1", temporal=("2026-11-03", "2026-11-03"),
                                bounding_box=(-68, -24, -67, -23), count=10)
    except Exception as e:  # noqa: BLE001
        return e
    return None


print("| cuerpo | tipo exc | tipo __cause__ | __cause__.response.status_code | bool(__cause__.response) "
      "| _is_credential_dead normal | con PLACEBO Response.__bool__=True |")
print("|---|---|---|---|---|---|---|")
orig_bool = requests.Response.__bool__
for nombre in BODY:
    e = excepcion_real(nombre)
    c = e.__cause__
    r = getattr(c, "response", None)
    normal = fetch._is_credential_dead(e)
    requests.Response.__bool__ = lambda self: True
    placebo = fetch._is_credential_dead(e)
    requests.Response.__bool__ = orig_bool
    print(f"| {nombre} | {type(e).__name__} | {type(c).__name__} | {getattr(r, 'status_code', None)} | {bool(r)} "
          f"| {normal} | {placebo} |")
