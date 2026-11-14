# -*- coding: utf-8 -*-
"""F4T (S175), instrumento 1: ¿el clasificador de «credencial muerta» de pipeline/fetch.py ve el rechazo
tal como earthaccess lo lanza en la DESCARGA?

Las dos preguntas del instrumento:
1. Si estuviera roto (la descarga con 401 no se clasifica como credencial muerta), ¿se ve? Sí: la
   fila «DownloadFailure 401» daría dead=False y download_granules saldría con RuntimeError genérico
   tras 4 intentos, no con EarthdataCredentialError.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Sí: el control positivo (la forma de CMR
   que usan los tests de S123, RuntimeError con __cause__.response 401) tiene que dar dead=True; si
   diera False el instrumento está roto, no el código.

Formas construidas a partir del código fuente leído:
- CMR: earthaccess/search.py (0.17.0 instalado y 0.19.0 de PyPI, l. 79 y 464): `raise RuntimeError(ex.response.text) from ex`.
- Descarga: earthaccess/store.py::_download_file (0.17.0 instalado; 0.19.0 l. 934-935):
  `DownloadFailure(f"Download failed for {url}. Status code: {r.status_code}")`, sin atributo response
  y sin __cause__.
Sin red: ninguna llamada sale de este proceso (se bloquea socket por si acaso).
"""
from __future__ import annotations

import io
import os
import socket
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\f4t\repo_base")
sys.path.insert(0, str(REPO))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
os.environ["EARTHDATA_TOKEN"] = "no-es-un-jwt"  # cualquier texto no vacío: el clasificador no lo mira


def _bloquear_red(*a, **k):
    raise OSError("RED BLOQUEADA POR EL INSTRUMENTO F4T")


socket.socket.connect = _bloquear_red  # type: ignore[assignment]
socket.create_connection = _bloquear_red  # type: ignore[assignment]

import requests  # noqa: E402
import earthaccess  # noqa: E402
from earthaccess.exceptions import DownloadFailure, EulaNotAccepted  # noqa: E402

import pipeline.fetch as fetch  # noqa: E402

URL = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD021KM/2026/307/MOD021KM.A2026307.0500.061.hdf"


def forma_cmr(status: int, body: bytes) -> BaseException:
    resp = requests.Response()
    resp.status_code = status
    resp._content = body
    try:
        resp.raise_for_status()
    except requests.HTTPError as ex:
        return _con_causa(ex)
    raise AssertionError("raise_for_status no levantó")


def _con_causa(ex: requests.HTTPError) -> RuntimeError:
    e = RuntimeError(ex.response.text)
    e.__cause__ = ex
    return e


def forma_descarga(status: int) -> BaseException:
    # Texto idéntico en earthaccess 0.17.0 (instalado) y 0.19.0 (PyPI, store.py l. 934)
    return DownloadFailure(f"Download failed for {URL}. Status code: {status}")


FILAS = [
    ("CONTROL+ CMR 401 token expirado (forma de tests S123)", forma_cmr(401, b'{"errors":["Token [ABC] has expired. Please get a new token"]}'), True),
    ("CMR 401 cuerpo vacío", forma_cmr(401, b""), True),
    ("CMR 401 'Token does not exist' (texto sin expired/invalid/unauthorized)", forma_cmr(401, b'{"errors":["Token does not exist"]}'), True),
    ("CMR 401 'Token [x] is invalid'", forma_cmr(401, b'{"errors":["Token [x] is invalid"]}'), True),
    ("CMR 403 EULA (no debe abortar)", forma_cmr(403, b'{"errors":["User does not have permission to access collection"]}'), False),
    ("DESCARGA DownloadFailure 401 (earthaccess real)", forma_descarga(401), None),
    ("DESCARGA DownloadFailure 403 (earthaccess real)", forma_descarga(403), None),
    ("DESCARGA EulaNotAccepted (403 con eula)", EulaNotAccepted(f"Eula Acceptance Failure for {URL}"), False),
    ("DESCARGA DownloadFailure 500", forma_descarga(500), False),
]

print(f"earthaccess instalado: {earthaccess.__version__}")
print(f"_CRED_DEAD_PAT: {fetch._CRED_DEAD_PAT.pattern!r}")
# Por qué el status nunca llega: `resp or getattr(exc, "response", None)` (fetch.py, _is_credential_dead) evalúa la
# verdad de un requests.Response, que es `resp.ok`; un 401 es falso y el `or` lo descarta.
_r = requests.Response(); _r.status_code = 401
print(f"bool(requests.Response con status 401) = {bool(_r)}  (requests.Response.__bool__ devuelve self.ok)")
_cmr = forma_cmr(401, b'{"errors":["Token does not exist"]}')
print(f"__cause__.response.status_code de la forma CMR = {_cmr.__cause__.response.status_code}; "
      f"_is_credential_dead la clasifica como {fetch._is_credential_dead(_cmr)}")
print()
print("| forma del error | dead | status recuperado | esperado |")
print("|---|---|---|---|")
for nombre, exc, esperado in FILAS:
    dead, code = fetch._is_credential_dead(exc)
    esp = "—" if esperado is None else ("True" if esperado else "False")
    marca = "" if esperado is None or dead == esperado else "  <-- NO COINCIDE"
    print(f"| {nombre} | {dead} | {code} | {esp} |{marca}")

# Ahora el camino completo de descarga con la forma real de earthaccess.
print()
print("download_granules con earthaccess.download que lanza la forma REAL (DownloadFailure 401):")
intentos = {"n": 0}


def descarga_401(*a, **k):
    intentos["n"] += 1
    raise forma_descarga(401)


class Granulo(dict):
    def data_links(self):
        return [URL]


fetch.earthaccess.download = descarga_401
_sleep = time.sleep
time.sleep = lambda *_: None
dest = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\f4t\tmp_01")
try:
    fetch.download_granules([Granulo({"umm": {"GranuleUR": "MOD021KM.A2026307.0500"}})], dest)
    print("  RESULTADO: no levantó nada (inesperado)")
except fetch.EarthdataCredentialError as e:
    print(f"  RESULTADO: EarthdataCredentialError tras {intentos['n']} intento(s): {str(e)[:120]}")
except Exception as e:  # noqa: BLE001
    print(f"  RESULTADO: {type(e).__name__} genérico tras {intentos['n']} intento(s): {str(e)[:140]}")
    print("  => el guard S124 del camino de descarga NO clasifica la forma real; fetch_for_volcano lo tragará como WARN")
finally:
    time.sleep = _sleep

print()
print("Control positivo del mismo camino con la forma de CMR (la que usa tests/test_fetch_credential_dead_s123.py):")
intentos["n"] = 0


def descarga_cmr_401(*a, **k):
    intentos["n"] += 1
    raise forma_cmr(401, b'{"errors":["Token [ABC] has expired. Please get a new token"]}')


fetch.earthaccess.download = descarga_cmr_401
time.sleep = lambda *_: None
try:
    fetch.download_granules([Granulo({"umm": {"GranuleUR": "x"}})], dest)
except fetch.EarthdataCredentialError as e:
    print(f"  RESULTADO: EarthdataCredentialError tras {intentos['n']} intento(s) (el test de S124 pasa con ESTA forma)")
except Exception as e:  # noqa: BLE001
    print(f"  RESULTADO inesperado: {type(e).__name__}")
finally:
    time.sleep = _sleep
