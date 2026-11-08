# -*- coding: utf-8 -*-
"""V4T, instrumento 3: con EARTHDATA_TOKEN vacío (secret ausente en Actions = cadena vacía, no variable
ausente) y el par usuario/clave presente, ¿earthaccess hace login con el par? ¿cuántos?

Pregunta de la afirmación 386 del F4t («8 logins por job con el par vencido»). Se cuenta cada POST a
urs.earthdata.nasa.gov (find_or_create_token es el login con usuario y clave en earthaccess 0.17/0.19).

Las dos preguntas del instrumento:
1. Si earthaccess sí cayera al par con token vacío, ¿se vería? Sí: n_login_urs > 0 en el modo «vacio».
2. Si el contador estuviera muerto, ¿se vería distinto? CONTROL POSITIVO: el modo «ausente» (variable
   EARTHDATA_TOKEN no definida) tiene que hacer logins al par (urs responde 401 = par vencido). Si ese modo
   diera 0, el contador no sirve.
Sin red (socket bloqueado); usuario, clave y token son textos sintéticos.
Uso: python v4t_03_token_vacio_logins.py --ea 017|019 --modo vacio|ausente|espacios --salida f.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--ea", choices=["017", "019"], required=True)
ap.add_argument("--modo", choices=["vacio", "ausente", "espacios"], required=True)
ap.add_argument("--salida", required=True)
a = ap.parse_args()
TMP = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\v4t")
if a.ea == "019":
    sys.path.insert(0, str(TMP / "ea0190"))
sys.path.insert(0, str(TMP / "repo_base"))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
os.environ["EARTHDATA_USERNAME"] = "v4t-usuario-sintetico"
os.environ["EARTHDATA_PASSWORD"] = "v4t-clave-sintetica"
if a.modo == "vacio":
    os.environ["EARTHDATA_TOKEN"] = ""
elif a.modo == "espacios":
    os.environ["EARTHDATA_TOKEN"] = "   "
else:
    os.environ.pop("EARTHDATA_TOKEN", None)


def _b(*x, **k):
    raise OSError("RED BLOQUEADA POR V4T")


socket.socket.connect = _b
socket.create_connection = _b
import requests  # noqa: E402
from requests.adapters import HTTPAdapter  # noqa: E402
from requests.structures import CaseInsensitiveDict  # noqa: E402

LOG = []


def _send(self, req, **kw):
    host = req.url.split("/")[2]
    LOG.append({"host": host, "metodo": req.method, "url": req.url[:90],
                "authorization": (req.headers.get("Authorization") or None)})
    r = requests.Response()
    r.request, r.url, r.encoding, r.headers = req, req.url, "utf-8", CaseInsensitiveDict({})
    if "urs.earthdata" in host:
        r.status_code, r._content = 401, b'{"error":"invalid_credentials"}'
    elif "cmr.earthdata" in host:
        r.status_code, r._content = 401, b'{"errors":["Token does not exist"]}'
    else:
        r.status_code, r._content = 404, b""
    return r


HTTPAdapter.send = _send
time.sleep = lambda *_: None
out = {"ea": a.ea, "modo": a.modo}
import earthaccess  # noqa: E402
import pipeline.fetch as fetch  # noqa: E402
fetch._probe_nasa_auth = lambda timeout=5.0: True  # el probe TCP abriría socket; se fija en «host vivo»
out["earthaccess"] = earthaccess.__version__
try:
    fetch.auth()
    out["auth"] = "OK"
except Exception as e:  # noqa: BLE001
    out["auth"] = f"{type(e).__name__}: {str(e)[:160]}"
out["token_en_earthaccess"] = repr(getattr(earthaccess.__auth__, "token", None))[:80]
out["n_login_urs_tras_auth"] = sum(1 for x in LOG if "urs.earthdata" in x["host"])
if out["auth"] == "OK":
    fetch.limpiar_fallas()
    try:
        fetch.fetch_for_volcano({"name": "Lascar", "lat": -23.37, "lon": -67.73, "radius_km": 25,
                                 "sensors": ["MODIS"]}, datetime(2026, 11, 3), TMP / "tmp_03")
        out["fetch"] = "VOLVIO_SIN_EXCEPCION"
    except Exception as e:  # noqa: BLE001
        out["fetch"] = f"{type(e).__name__}: {str(e)[:160]}"
out["n_login_urs_total"] = sum(1 for x in LOG if "urs.earthdata" in x["host"])
out["authorization_en_cmr"] = sorted({repr(x["authorization"]) for x in LOG if "cmr.earthdata" in x["host"]})
out["n_peticiones"] = len(LOG)
out["urs_detalle"] = sorted({(x["metodo"], x["url"].split("?")[0], (x["authorization"] or "SIN").split(" ")[0]) for x in LOG if "urs.earthdata" in x["host"]})
out["urs_con_basic"] = sum(1 for x in LOG if "urs.earthdata" in x["host"] and (x["authorization"] or "").startswith("Basic"))
Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False))
