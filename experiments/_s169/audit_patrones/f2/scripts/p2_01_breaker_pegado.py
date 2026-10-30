# -*- coding: utf-8 -*-
"""P-E/P-F: el circuit-breaker de hosts de descarga de pipeline/fetch.py es estado del PROCESO. probe_f4.main nunca
llama fetch.reset_transient_breakers(). Una vez marcado un host caido, todo download_granules siguiente lanza
RuntimeError al instante y bajar_por_nombre (probe_f4.py) lo traga con 4 intentos y sleep(20*(i+1)).

PREGUNTA 1 (si lo que mido estuviera roto, lo veria?): el control positivo es la misma llamada con el breaker limpio:
tiene que NO lanzar (llega a earthaccess.download, que aqui se reemplaza por un doble que devuelve un archivo).
PREGUNTA 2 (si el instrumento estuviera muerto): se imprime el numero de segundos de espera acumulados por el sleep
parchado, no un 0 por defecto; y se imprime el valor devuelto por bajar_por_nombre.
Sin red: el host nunca se contacta (el breaker corta antes) y el control positivo usa un doble de earthaccess.download."""
import ast, sys, types, time
from pathlib import Path

ARBOL = Path("D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol")
sys.path.insert(0, str(ARBOL))
from pipeline import fetch  # noqa: E402

# extraer bajar_por_nombre de probe_f4.py sin importar el modulo entero (necesita archivos que el arbol no trae)
src = (ARBOL / "experiments/_s166_modd_f4/probe_f4.py").read_text(encoding="utf-8")
tree = ast.parse(src)
fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "bajar_por_nombre"][0]
codigo = ast.get_source_segment(src, fn)

dormido = []
ns = {"Path": Path, "time": types.SimpleNamespace(sleep=lambda s: dormido.append(s))}
exec("from pathlib import Path\n" + codigo, ns)
bajar = ns["bajar_por_nombre"]


class G:  # granulo falso: solo expone data_links() como el DataGranule de earthaccess
    def data_links(self):
        return ["https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MYD021KM/x.hdf"]


buscar = lambda **k: [G()]
HOST = "ladsweb.modaps.eosdis.nasa.gov"
NOMBRE = "MYD021KM.A2026060.0735.061.2026060163012.hdf"

print("== control positivo: breaker limpio, earthaccess.download sustituido por un doble")
fetch.reset_transient_breakers()
llamadas = []
def doble_download(granulos, local_path):
    llamadas.append(local_path)
    p = Path(local_path) / NOMBRE
    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b"x"); return [str(p)]
fetch.earthaccess.download = doble_download
import tempfile
with tempfile.TemporaryDirectory() as d:
    r = bajar(NOMBRE, d, buscar=buscar, descargar=fetch.download_granules)
    print("   devuelve:", (r[0].name if r[0] else None), r[1], "| llamadas al doble:", len(llamadas), "| sleep acumulado:", sum(dormido))

print("== caso: host marcado caido por un ConnectTimeout anterior en el MISMO proceso (nadie llama reset_transient_breakers)")
dormido.clear()
fetch._DOWN_DOWNLOAD_HOSTS.add(HOST)
llamadas.clear()
with tempfile.TemporaryDirectory() as d:
    r = bajar(NOMBRE, d, buscar=buscar, descargar=fetch.download_granules)
print("   devuelve:", r, "| llamadas al doble:", len(llamadas), "| sleep acumulado por L1B:", sum(dormido), "s",
      "| esperas:", dormido)
print("   por gránulo main() pide L1B y MxD03 (sin cortocircuito): %d s de espera sin bajar nada" % (2 * sum(dormido)))
print("   gránulos por parte en poblacion_f4.json: ver p2_02; con el timeout de 240 min del job:",
      "alcanzan %d gránulos antes del corte" % (240 * 60 // (2 * sum(dormido))))
print("== grep: quien llama reset_transient_breakers en el arnés y en el workflow")
for p in ("experiments/_s166_modd_f4/probe_f4.py", ".github/workflows/probe-s168-modd-f4.yml"):
    print("  ", p, "->", (ARBOL / p).read_text(encoding="utf-8").count("reset_transient_breakers"), "apariciones")
