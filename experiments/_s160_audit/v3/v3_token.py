"""V3, hallazgo 247. (a) estado_token con entradas sintéticas (vacío, basura, JWT a 5 y 30 días, vencido);
(b) auth() de SHA_MAIN con EARTHDATA_TOKEN vacío y sin netrc: cuenta llamadas a earthaccess.login y suma de
sleeps, con el probe TCP forzado a True (NASA arriba). Control: con token 'x' debe hacer 1 login y 0 s.
Uso: python -I v3_token.py <arbol_main>"""
import base64, json, os, sys, time
from datetime import datetime, timezone, timedelta
arbol = sys.argv[1]; sys.path.insert(0, arbol); sys.path.insert(0, arbol + "/scripts")
import token_edad as te
ahora = datetime(2026, 10, 22, 4, 0, tzinfo=timezone.utc)
def jwt(d):
    c = base64.urlsafe_b64encode(json.dumps({"exp": int((ahora + timedelta(days=d)).timestamp())}).encode()).decode().rstrip("=")
    return "aaa." + c + ".bbb"
for n, t in [("vacio", ""), ("basura", "abc"), ("jwt+5d", jwt(5)), ("jwt+30d", jwt(30)), ("jwt-1d", jwt(-1))]:
    print("estado_token", n, te.estado_token(t, ahora))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import pipeline.fetch as fetch
os.path.exists_orig = os.path.exists
LOG = []; SL = []
fetch.earthaccess.login = lambda strategy=None, **k: (LOG.append(strategy), (_ for _ in ()).throw(RuntimeError("invalid_credentials")) if not os.environ.get("EARTHDATA_TOKEN","").strip() else True)[1]
fetch._probe_nasa_auth = lambda timeout=5.0: True
time.sleep = lambda s: SL.append(s)
_ex = os.path.exists
os.path.exists = lambda p: False if str(p).endswith(("netrc",)) else _ex(p)
for tok in ["x", ""]:
    os.environ["EARTHDATA_TOKEN"] = tok; LOG.clear(); SL.clear(); err = None
    try: fetch.auth()
    except Exception as e: err = f"{type(e).__name__}: {str(e)[:60]}"
    print(f"auth token={'vacio' if not tok else 'x'}: logins={len(LOG)} estrategias={set(LOG)} sleeps_s={sum(SL)} excepcion={err}")
