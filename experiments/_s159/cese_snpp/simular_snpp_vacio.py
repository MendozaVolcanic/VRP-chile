"""S159 cese SNPP: que hace fetch_for_volcano + informar_cobertura cuando Suomi NPP da cero granulos.

Sin red: earthaccess.search_data, auth y download_granules se reemplazan en memoria.
Uso: python -I simular_snpp_vacio.py <arbol_origin_main>   (arbol = git archive origin/main pipeline scripts ...)

Pregunta 1: si el pipeline avisara de una plataforma vacia, este escenario lo mostraria
(fallas_de_cobertura no vacia, o una excepcion, o un mensaje en informar_cobertura).
Pregunta 2: control positivo: la misma corrida con SNPP lanzando ConnectTimeout DEBE dejar falla de
cobertura; si no la deja, el instrumento esta muerto. Control de contraste: con SNPP vivo deben
aparecer las claves VIIRS_SNPP y VIIRS_SNPP_750 en el resultado.
"""
import sys, io, os
from datetime import datetime
from pathlib import Path
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ARBOL))
sys.path.insert(0, str(ARBOL / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
os.environ["EARTHDATA_TOKEN"] = "x"  # nunca se usa: auth() se reemplaza

import requests
from pipeline import fetch

LLAMADAS = Counter()
MODO = {"snpp": "vacio"}


def falso_granulo(t):
    return {"umm": {"TemporalExtent": {"RangeDateTime": {"BeginningDateTime": t, "EndingDateTime": t}}}}


def falso_search(short_name, version, bounding_box, temporal, count):
    LLAMADAS[(short_name, version)] += 1
    if short_name.startswith("VNP"):
        if MODO["snpp"] == "vacio":
            return []
        if MODO["snpp"] == "timeout":
            raise requests.exceptions.ConnectTimeout("simulado")
    # Standard: devuelve un granulo; asi no se consulta el NRT (igual que hoy en dias viejos)
    if "NRT" in short_name or "NRT" in str(version):
        return []
    return [falso_granulo(f"{temporal[0]}T05:00:00.000Z")]


fetch.earthaccess.search_data = falso_search
fetch.auth = lambda: None
fetch.download_granules = lambda gs, d: [Path(d) / "falso.hdf"]

import run_pipeline  # noqa: E402  (scripts/run_pipeline.py, para informar_cobertura)

volcan = {"name": "Villarrica", "lat": -39.42, "lon": -71.94, "radius_km": 25}
fecha = datetime(2026, 11, 5)
for modo in ("vivo", "vacio", "timeout"):
    MODO["snpp"] = modo
    LLAMADAS.clear()
    fetch.limpiar_fallas()
    fetch.reset_transient_breakers()
    fetch.reiniciar_ventana()  # sin ventana: camino por dia (dias recientes del NRT)
    res = fetch.fetch_for_volcano(volcan, fecha, Path("."), nighttime_only=False)
    fallas = fetch.fallas_de_cobertura()
    vnp = {k: v for k, v in LLAMADAS.items() if k[0].startswith("VNP")}
    print(f"\n=== SNPP {modo} ===")
    print("plataformas con resultado:", sorted(res))
    print("consultas CMR a VNP*:", dict(vnp), "| total consultas:", sum(LLAMADAS.values()))
    print("fallas de cobertura:", len(fallas), [(f['plataforma'], f['motivo'][:40]) for f in fallas])
    codigo = run_pipeline.informar_cobertura(fallas, ruta_json=None, estricto=False)
    print("codigo de salida informar_cobertura:", codigo)
