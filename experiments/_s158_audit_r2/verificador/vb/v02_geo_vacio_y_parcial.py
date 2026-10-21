"""VB v02: dos variantes del hallazgo 2 que el auditor no probo, sin red.

(e) L1B encontrado pero el archivo de geolocalizacion (MOD03 / VNP03) devuelve 0: _match_granules
    descarta todo en silencio. Para MODIS ademas el MOD03 ni se usa.
(f) Dia parcial: CMR devuelve 1 de 4 granulos del dia (el resto aun no indexado). Nada lo distingue
    de un dia completo.
Control positivo: (g) Timeout de CMR (registra falla, codigo 3 con estricto).
Pregunta 1: si el registro de fallas viera estos casos, (e) y (f) darian INCOMPLETA como (g).
Pregunta 2: si el parche no se aplicara, search_data iria a la red: lo detecto contando llamadas
(si da 0 llamadas, el resultado es SIN DATO).
No descarga nada: download_granules se reemplaza por una funcion que cuenta y devuelve rutas falsas.
"""
import sys, io, os
from datetime import datetime
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "scripts"))
from pipeline import fetch
import run_pipeline as rp
from requests.exceptions import ReadTimeout

vol = {"name": "Lascar", "lat": -23.37, "lon": -67.73, "radius_km": 25, "sensors": ["MODIS"]}
fecha = datetime(2026, 10, 18)
fetch.auth = lambda: True
fetch._diag = lambda *a, **k: None
fetch._filter_nighttime_granules = lambda g, lat, lon, **k: g   # sin filtro solar: el caso es de catalogo
bajadas = []
fetch.download_granules = lambda gs, d: (bajadas.extend(gs) or [Path(f"falso_{i}") for i in range(len(gs))])

def gran(t):
    return {"umm": {"TemporalExtent": {"RangeDateTime": {"BeginningDateTime": t, "EndingDateTime": t}}}}

llamadas = []
def busq(geo_vacio=False, parcial=False, timeout=False):
    def f(**kw):
        llamadas.append(kw.get("short_name"))
        if timeout:
            raise ReadTimeout("simulado")
        sn = kw.get("short_name")
        if sn.endswith("03"):
            return [] if geo_vacio else [gran("2026-10-18T05:35:00Z")] + ([] if parcial else [gran("2026-10-18T17:20:00Z")])
        return [gran("2026-10-18T05:35:00Z")] + ([] if parcial else [gran("2026-10-18T17:20:00Z")])
    return f

for nombre, impl in (("(e) L1B presente, geolocalizacion vacia", busq(geo_vacio=True)),
                     ("(f) dia parcial: 1 de 2 granulos por plataforma", busq(parcial=True)),
                     ("(g) CONTROL POSITIVO timeout de CMR", busq(timeout=True))):
    fetch.limpiar_fallas(); fetch.reiniciar_ventana(); fetch.reset_transient_breakers()
    fetch._CMR_SEARCH_DOWN = False
    fetch.earthaccess.search_data = impl
    llamadas.clear(); bajadas.clear()
    res = fetch.fetch_for_volcano(vol, fecha, Path(os.environ.get("TEMP", ".")) / "vb_v02", nighttime_only=True)
    fallas = fetch.fallas_de_cobertura()
    print(f"\n--- {nombre}: llamadas a search_data={len(llamadas)} granulos 'bajados'={len(bajadas)} "
          f"archivos por plataforma={ {k: len(v) for k, v in res.items()} } fallas={len(fallas)}")
    print("    codigo con --estricto-cobertura:", rp.informar_cobertura(fallas, estricto=True))
