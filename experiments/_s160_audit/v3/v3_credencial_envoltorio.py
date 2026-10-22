"""V3, hallazgo 252. Con earthaccess REAL instalado (version impresa), un 401 de CMR pasa por get_results y
llega a fetch._is_credential_dead de SHA_MAIN. Luego se simulan envoltorios alternativos (como podria hacerlo
otra version): sin __cause__, sin .response, con y sin palabras clave en el cuerpo. Control: un ReadTimeout
no debe marcarse como credencial muerta.
Uso: python -I v3_credencial_envoltorio.py <arbol_main>"""
import json, os, sys
sys.path.insert(0, sys.argv[1]); os.environ["VRP_PROFILE"] = "mirova_equivalent"
import requests, earthaccess
import pipeline.fetch as fetch
print("earthaccess", earthaccess.__version__)
class R:
    def __init__(s, c, b): s.status_code=c; s.text=b; s.headers={"CMR-Hits":"0"}
    def json(s): return json.loads(s.text)
    def raise_for_status(s):
        if s.status_code>=400:
            e=requests.exceptions.HTTPError(str(s.status_code)); e.response=s; raise e
for cuerpo in ['{"errors":["Token has expired"]}', '{"errors":["Request rejected"]}']:
    requests.Session.get = lambda self, url, *a, **k: R(401, cuerpo)
    try:
        earthaccess.search_data(short_name="VNP02IMG", version="2", temporal=("2026-10-10","2026-10-10"), bounding_box=(-72,-40,-71,-39), count=5)
        print("sin excepcion?")
    except Exception as e:
        print(f"real 0.17, 401 cuerpo={cuerpo!r}: tipo={type(e).__name__} cause={type(e.__cause__).__name__} -> {fetch._is_credential_dead(e)}")
alts = {
 "RuntimeError sin __cause__, cuerpo con 'Token has expired'": RuntimeError('{"errors":["Token has expired"]}'),
 "RuntimeError sin __cause__, cuerpo neutro": RuntimeError('{"errors":["Request rejected"]}'),
 "excepcion propia con .status_code (no .response), cuerpo neutro": type("E", (Exception,), {"status_code": 401})("x"),
 "control ReadTimeout": requests.exceptions.ReadTimeout("read timed out"),
}
for n, e in alts.items(): print(n, "->", fetch._is_credential_dead(e))
