"""P2-01, simulación SIN RED del camino real: pipeline/fetch.download_granules del árbol 743e89c48 y
probe_f4.bajar_por_nombre (fuente extraída del árbol con ast, sin importar probe_f4 entero). earthaccess se reemplaza
por un módulo falso; requests.ConnectTimeout se lanza en la descarga del gránulo 1 y en los siguientes la descarga
FUNCIONARÍA (host recuperado). time.sleep se intercepta y se suma (no se duerme).
Pregunta 1: si el breaker se reseteara por gránulo, los gránulos 2..N bajarían y el sueño sería ~0: se vería.
Pregunta 2: control positivo: con fetch.reset_transient_breakers() antes de cada gránulo, los gránulos 2..N tienen que
bajar; si no bajan, la simulación está rota.
No escribe nada fuera de esta carpeta; no abre sockets (el probe TCP se reemplaza por False)."""
import ast, sys, types
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARB = Path("D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol")
import requests
estado = {"n_desc": 0, "fallar_en": {1}}
class G(dict):
    def __init__(self, n): super().__init__(umm={"GranuleUR": n}); self.n = n
    def data_links(self): return [f"https://ladsweb.modaps.eosdis.nasa.gov/x/{self.n}"]
fake = types.ModuleType("earthaccess")
def download(gs, local_path):
    estado["n_desc"] += 1
    if estado["n_desc"] in estado["fallar_en"]:
        raise requests.exceptions.ConnectTimeout("simulado")
    p = Path(local_path) / gs[0].n; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("x")
    return [str(p)]
fake.download = download; fake.search_data = lambda **k: []; fake.login = lambda **k: None
fake.__path__ = []
store = types.ModuleType("earthaccess.store")
class Store:
    def set_requests_session(self, url, *a, **k): return None
store.Store = Store
fake.store = store
sys.modules["earthaccess"] = fake
sys.modules["earthaccess.store"] = store
sys.path.insert(0, str(ARB))
import pipeline.fetch as F
F._probe_download_host = lambda h, timeout=5.0: False
F._diag = lambda *a, **k: None
src = (ARB / "experiments/_s166_modd_f4/probe_f4.py").read_text(encoding="utf-8")
fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "bajar_por_nombre")
dormido = []
tmod = types.SimpleNamespace(sleep=lambda s: dormido.append(s))
ns = {"time": tmod, "Path": Path}
exec(compile(ast.Module([fn], []), "bajar_por_nombre", "exec"), ns)
bajar = ns["bajar_por_nombre"]
buscar = lambda short_name, version, granule_name: [G(granule_name)]
dest = Path(__file__).resolve().parent / "m01b_dest"
def corrida(reset):
    estado["n_desc"] = 0; dormido.clear(); F.reset_transient_breakers()
    out = []
    for i in range(6):
        if reset: F.reset_transient_breakers()
        for tipo in ("MOD021KM", "MOD03"):
            nombre = f"{tipo}.A2026100.0{100+i}.061.x.hdf"
            r, otro = bajar(nombre, dest, buscar=buscar, descargar=F.download_granules)
            out.append((i, tipo, r is not None))
    return out, sum(dormido)
o1, s1 = corrida(False)
print("SIN reset (arnés tal cual): gránulos bajados", [x for x in o1], "segundos de sueño", s1)
print("  por gránulo (L1B+MxD03) tras la caída: sueño =", s1 / 6, "s promedio; hosts caídos:", sorted(F._DOWN_DOWNLOAD_HOSTS))
o2, s2 = corrida(True)
print("CON reset por gránulo (control positivo): bajados", [x for x in o2], "segundos de sueño", s2)
