"""Afirmación 3: ¿una búsqueda que devuelve 0 gránulos se registra como «Cobertura: completa»?
Reproducción SIN RED: se parchea earthaccess.search_data (lo que fetch.search_granules llama) y
se traza (a) 0 gránulos en todas las versiones, (b) Timeout de CMR con el breaker ON (producción),
(c) Timeout con el breaker OFF, (d) búsqueda por ventana que devuelve 0 para el día.
Después se llama scripts.run_pipeline.informar_cobertura con lo que fetch registró, que es lo que
escribe el log y el resumen del job.
Pregunta 1: si el registro de fallas estuviera roto, el caso (b) daría también «completa»: ese es
el control positivo (debe dar INCOMPLETA). Pregunta 2: el instrumento es el propio código; si el
parche no se aplicara, search_data intentaría la red y fallaría con otra excepción (se vería)."""
import sys, io, os, types
from datetime import datetime
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
from pipeline import fetch
import run_pipeline as rp
from requests.exceptions import ReadTimeout

vol = {"name": "Chaiten", "display_name": "Chaitén", "lat": -42.833, "lon": -72.646, "radius_km": 25, "sensors": ["VIIRS"]}
fecha = datetime(2026, 10, 18)
fetch.auth = lambda: True   # sin red
fetch._diag = lambda *a, **k: None

def caso(nombre, search_impl, breaker=None, ventana=False):
    fetch.limpiar_fallas(); fetch.reiniciar_ventana(); fetch.reset_transient_breakers()
    fetch._CMR_SEARCH_DOWN = False
    if breaker is not None:
        fetch.ENABLE_CMR_SEARCH_BREAKER = breaker
    fetch.earthaccess.search_data = search_impl
    if ventana:
        ok = fetch.configurar_ventana([fecha], ventana=("2026-10-16", "2026-10-18"), ahora=datetime(2026, 10, 21))
    res = fetch.fetch_for_volcano(vol, fecha, Path(os.environ.get("TEMP", ".")) / "rb_cero", nighttime_only=True)
    fallas = fetch.fallas_de_cobertura()
    n_paths = sum(len(v) for v in res.values())
    print(f"\n--- {nombre}: plataformas devueltas={list(res)} archivos={n_paths} fallas_registradas={len(fallas)}")
    for f in fallas[:3]: print("    falla:", f)
    codigo = rp.informar_cobertura(fallas, estricto=True)
    print(f"    informar_cobertura(estricto=True) -> codigo de salida {codigo}")
    return len(fallas), codigo

llamadas = []
def cero(**kw):
    llamadas.append((kw.get("short_name"), kw.get("version"), kw.get("temporal"))); return []
def timeout(**kw):
    raise ReadTimeout("simulado: CMR no responde")

r_a = caso("(a) 0 granulos en todas las versiones, breaker ON", cero, breaker=True)
print("    search_data llamada", len(llamadas), "veces; primeras:", llamadas[:4])
r_b = caso("(b) CONTROL POSITIVO: ReadTimeout de CMR, breaker ON (produccion)", timeout, breaker=True)
r_c = caso("(c) ReadTimeout de CMR, breaker OFF", timeout, breaker=False)
r_d = caso("(d) busqueda por VENTANA con 0 granulos para el dia", cero, breaker=True, ventana=True)
print("\nFlag efectivo ENABLE_CMR_SEARCH_BREAKER en el perfil:", __import__("pipeline.profile", fromlist=["x"]).ENABLE_CMR_SEARCH_BREAKER if hasattr(__import__("pipeline.profile", fromlist=["x"]), "ENABLE_CMR_SEARCH_BREAKER") else "no esta en profile; valor en fetch=" + str(fetch.ENABLE_CMR_SEARCH_BREAKER))
print("\nRESUMEN (fallas_registradas, codigo_salida_estricto):", {"a_cero": r_a, "b_timeout_breakerON": r_b, "c_timeout_breakerOFF": r_c, "d_ventana_cero": r_d})
