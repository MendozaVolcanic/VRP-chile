"""V3 (verificador F3, hallazgo 241). Camino distinto al del auditor:
- se corre scripts/run_pipeline.py::main() entero (con su ventana de busqueda S157 y process_date),
  no fetch_for_volcano suelto;
- el parche va a la capa HTTP (requests.Session.get sobre cmr.earthdata.nasa.gov/search/granules),
  asi que earthaccess.search_data, DataGranules y get_results corren de verdad.
Pregunta 1 del instrumento: si el silencio por plataforma SI se detectara, la linea de cobertura
diria INCOMPLETA y el codigo estricto seria 3; el escenario de control (HTTP 500 en SNPP) prueba que
el instrumento ve ese caso. Pregunta 2: si el parche no se aplicara, se irian consultas a la red real
(se cuentan y se exige que todas pasen por el parche).
Uso: python -I v3_e2e_cmr_http.py <arbol> <escenario> [--estricto]
"""
import io, json, os, runpy, sys, collections
from urllib.parse import urlparse, parse_qs
arbol, esc = sys.argv[1], sys.argv[2]
estricto = "--estricto" in sys.argv
os.environ["VRP_PROFILE"] = "mirova_equivalent"
os.environ["VRP_TMP_DIR"] = os.path.join(arbol, "tmp_" + esc)
os.environ["EARTHDATA_TOKEN"] = "x"
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, arbol)
import requests
CONSULTAS = collections.Counter()
NO_PARCHADAS = []
_orig_get = requests.Session.get

class Resp:
    def __init__(self, code, body):
        self.status_code = code; self._b = body; self.headers = {"CMR-Hits": str(len(body.get("items", [])))}; self.text = json.dumps(body)
    def json(self): return self._b
    def raise_for_status(self):
        if self.status_code >= 400:
            e = requests.exceptions.HTTPError(f"{self.status_code}"); e.response = self; raise e

def falso_get(self, url, *a, **kw):
    if "cmr.earthdata.nasa.gov/search/granules" in url:
        q = parse_qs(urlparse(url).query)
        sn = (q.get("short_name") or ["?"])[0]; ver = (q.get("version") or ["?"])[0]
        CONSULTAS[(sn, ver)] += 1
        if esc == "control_snpp_http500" and sn.startswith("VNP"):
            return Resp(500, {"errors": ["simulado 500"]})
        return Resp(200, {"hits": 0, "items": []})
    NO_PARCHADAS.append(url)
    raise RuntimeError("V3: consulta fuera del parche bloqueada: " + url[:80])
requests.Session.get = falso_get

import pipeline.fetch as fetch
fetch.auth = lambda *a, **k: None
sys.argv = ["run_pipeline.py", "--profile", "mirova_equivalent", "--volcano", "Villarrica"] + os.environ.get("V3_ARGS", "").split() + (["--estricto-cobertura"] if estricto else [])
buf = io.StringIO(); old = sys.stdout; sys.stdout = buf
codigo = None
try:
    runpy.run_path(os.path.join(arbol, "scripts", "run_pipeline.py"), run_name="__main__")
except SystemExit as e:
    codigo = e.code
finally:
    sys.stdout = old
salida = buf.getvalue()
lineas_cob = [l for l in salida.splitlines() if "Cobertura" in l]
vnp = {k: v for k, v in CONSULTAS.items() if k[0].startswith("VNP")}
print(f"escenario={esc} estricto={estricto} codigo_salida={codigo}")
print(f"linea_cobertura={lineas_cob}")
print(f"consultas_cmr_total={sum(CONSULTAS.values())} productos_distintos={len(CONSULTAS)} consultas_VNP={vnp}")
print(f"consultas_no_parchadas={len(NO_PARCHADAS)}")
print("diag_ventana=", [l for l in salida.splitlines() if "VENTANA" in l][:3])
print("fechas_procesadas=", [l.strip() for l in salida.splitlines() if l.startswith(">>>")])
