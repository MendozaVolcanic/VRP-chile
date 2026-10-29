# -*- coding: utf-8 -*-
"""S167: perfil de sombra prospectiva de las tres vías «código MIROVA» y su workflow, preparados APAGADOS.

POR QUÉ. Los tres pre-registros de fase 4 (V750-A §4.3, V375-E §3.3 y §8.8, MOD-D fase 4 §12.6) piden correr las vías
hacia adelante desde el 2026-11-03 en un perfil con carpeta propia, sin tocar lo que publica producción. Nicolás
aprobó prepararlo (2026-10-29, tag pre-s167-perfil-sombra) y encenderlo sólo con otro sí. Estas pruebas fijan las
cuatro cosas que pueden fallar en silencio:
  1. que el perfil difiera de producción SOLO en las tres vías y la carpeta (si heredara otro cambio, la sombra
     mediría otro paquete que el que los pre-registros sellan), leído como lo lee el código (A89);
  2. que los 11 volcanes del workflow tengan grilla de MIROVA en los tres sensores (sin grilla, la vía cae a K y la
     carpeta de sombra se llenaría de K: A118);
  3. que la sombra no escriba antes del 2026-11-03 (otro régimen) y corra sola sólo una vez al día (encendida en S168
     con el sí de Nicolás; antes no tenía schedule);
  4. que, corriendo de punta a punta, escriba sólo en data/sombra_codigo_mirova/ y deje data/mirova_equivalent/ bit
     a bit igual, con los tres brazos de posición legibles desde el record (V375-E §8.8).
Cada grupo tiene su control: el mismo instrumento sobre producción tiene que dar distinto.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

PERFIL = "sombra_codigo_mirova"
WF = ROOT / ".github" / "workflows" / "sombra-codigo-mirova.yml"
NRT = ROOT / ".github" / "workflows" / "nrt.yml"
VIAS = {"ENABLE_V750_CODIGO_MIROVA", "ENABLE_V375_CODIGO_MIROVA", "ENABLE_MODIS_CODIGO_MIROVA"}
MXD03 = {"ENABLE_MODIS_GEO_MXD03", "ENABLE_MODIS_CRATER_SIN_DATO", "ENABLE_MODIS_DIST_DESDE_CRATER"}


def _resuelto(perfil):
    """Todas las constantes de pipeline.profile, resueltas en un proceso aparte con VRP_PROFILE (A89: nunca el YAML)."""
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    # VALID_PROFILES es el conjunto de archivos de profiles/, no un valor del perfil, y su repr cambia de orden entre
    # procesos (hash aleatorio de str): va ordenado para que el diff mida el perfil y no el azar.
    codigo = ("import json, pipeline.profile as p; "
              "print(json.dumps({k: repr(sorted(v) if isinstance(v, (set, frozenset)) else v) "
              "for k, v in ((k, getattr(p, k)) for k in dir(p) if k.isupper())}, sort_keys=True))")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


# ------------------------------------------------------------------------------------- 1. el perfil
def test_el_perfil_difiere_de_produccion_solo_en_las_tres_vias_y_la_carpeta():
    prod, sombra = _resuelto("mirova_equivalent"), _resuelto(PERFIL)
    distintas = {k for k in set(prod) | set(sombra) if prod.get(k) != sombra.get(k)}
    assert distintas == VIAS | {"DATA_SUBDIR", "PROFILE_NAME"}, sorted(distintas)
    # control: en producción las tres vías están apagadas y en la sombra encendidas (si no, el diff de arriba
    # podría coincidir por otra razón)
    assert all(prod[k] == "False" for k in VIAS) and all(sombra[k] == "True" for k in VIAS)
    assert sombra["DATA_SUBDIR"] == repr(PERFIL) and prod["DATA_SUBDIR"] == repr("mirova_equivalent")
    # los flags de MxD03 van aparte (programa §12.3 punto 4): apagados en los dos
    assert all(prod[k] == sombra[k] == "False" for k in MXD03)


def test_ningun_otro_perfil_escribe_en_la_carpeta_de_la_sombra():
    """La carpeta es de la sombra sola (A47); el guard general de S124 lo vigila para todos, aquí el caso propio."""
    otros = []
    for f in sorted((ROOT / "pipeline" / "profiles").glob("*.yaml")):
        cfg = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if f.stem != PERFIL and ((cfg.get("output") or {}).get("data_subdir") == PERFIL):
            otros.append(f.stem)
    assert not otros


# ------------------------------------------------------------------------------------- 2. grillas
def _matriz(wf):
    d = yaml.safe_load(wf.read_text(encoding="utf-8"))
    return list(d["jobs"]["process"]["strategy"]["matrix"]["volcano"])


def test_los_volcanes_de_la_sombra_son_los_del_nrt():
    assert sorted(_matriz(WF)) == sorted(_matriz(NRT)) and len(_matriz(WF)) == 11


@pytest.mark.parametrize("familia", ["VIIRS750", "VIIRS375", "MODIS"])
def test_cada_volcan_de_la_sombra_tiene_grilla_de_miroVA_en_cada_sensor(familia):
    """Sin grilla la vía devuelve K con `via_codigo_mirova: "sin_grilla"` y la sombra mediría K (A118)."""
    from pipeline import mirova_v750_codigo as MV
    vols = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    cfg = MV.FAMILIAS[familia]
    for nombre in _matriz(WF):
        v = vols[nombre]
        assert MV.volcan_por_coordenadas(v["lat"], v["lon"]) == nombre
        assert MV.grilla_del_volcan(nombre, paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"]) is not None, nombre
    # control: un volcán fuera de la lista de MIROVA no tiene grilla (el instrumento puede dar None)
    fuera = [n for n in vols if MV.grilla_del_volcan(n, paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"]) is None]
    assert fuera


# ------------------------------------------------------------------------------------- 3. fechas y encendido
def test_ventana_respeta_la_fecha_minima():
    from ventana_sombra import FECHA_MINIMA, ventana
    assert FECHA_MINIMA == date(2026, 11, 3)
    assert ventana(date(2026, 11, 2)) is None                                   # Suomi NPP aún vivo: no corre
    assert ventana(date(2026, 11, 3)) == (date(2026, 11, 3), date(2026, 11, 3))
    assert ventana(date(2026, 11, 6)) == (date(2026, 11, 3), date(2026, 11, 6))
    assert ventana(date(2026, 11, 20)) == (date(2026, 11, 13), date(2026, 11, 20))   # 8 días, como el NRT
    assert ventana(date(2026, 11, 20), "2026-11-05", "2026-11-06") == (date(2026, 11, 5), date(2026, 11, 6))
    with pytest.raises(ValueError):
        ventana(date(2026, 11, 20), "2026-11-01", "2026-11-06")                 # rellenar antes del régimen: no
    with pytest.raises(ValueError):
        ventana(date(2026, 11, 20), "2026-11-06", None)
    # modo medir: ventana pasada tal cual (no commitea), y exige fechas explícitas
    assert ventana(date(2026, 10, 29), "2026-10-20", "2026-10-21", medir=True) == (date(2026, 10, 20),
                                                                                    date(2026, 10, 21))
    with pytest.raises(ValueError):
        ventana(date(2026, 10, 29), medir=True)


def test_ventana_por_linea_de_comandos_como_la_llama_el_workflow():
    def correr(*args):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "ventana_sombra.py"), *args], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        return r.returncode, r.stdout.strip()
    assert correr("--hoy", "2026-10-29") == (0, "")
    assert correr("--hoy", "2026-11-10") == (0, "2026-11-03 2026-11-10")
    assert correr("--hoy", "2026-11-10", "--start", "2026-10-30", "--end", "2026-11-01")[0] == 2
    assert correr("--hoy", "2026-11-10", "--medir", "--start", "2026-10-20", "--end", "2026-10-20") == (
        0, "2026-10-20 2026-10-20")


def _wf():
    txt = WF.read_text(encoding="utf-8")
    return txt, yaml.safe_load(txt)


def test_el_workflow_corre_una_vez_al_dia():
    # S168: encendida con el sí de Nicolás (tag pre-s168-encender-sombra). Un solo cron diario y ningún otro
    # disparador automático (push o pull_request la correrían en cada commit del NRT). En el schedule no hay inputs:
    # medir llega vacío, así que commitea, y la ventana es la de ventana_sombra.py (nada antes del 2026-11-03).
    txt, d = _wf()
    assert "on" in d and True not in d, "'on' entre comillas (A43)"
    assert set(d["on"]) == {"workflow_dispatch", "schedule"}, "sólo despacho manual y el cron diario"
    assert d["on"]["schedule"] == [{"cron": "0 15 * * *"}], "una vez al día, 15:00 UTC"
    assert d["on"]["workflow_dispatch"]["inputs"]["medir"]["default"] is False


def test_el_workflow_corta_por_token_vacio_e_instala_pyproj():
    txt, d = _wf()
    paso = next(s for s in d["jobs"]["process"]["steps"] if "run_pipeline.py" in s.get("run", ""))
    run = paso["run"]
    assert '-z "$EARTHDATA_TOKEN"' in run and run.index('-z "$EARTHDATA_TOKEN"') < run.index("run_pipeline.py")
    assert set(paso["env"]) >= {"EARTHDATA_TOKEN"}
    assert "EARTHDATA_USERNAME" not in txt and "EARTHDATA_PASSWORD" not in txt       # A71: sólo token
    assert "--profile sombra_codigo_mirova" in run and "scripts/ventana_sombra.py" in run
    assert "set -o pipefail" in run
    instalar = next(s for s in d["jobs"]["process"]["steps"] if "pip install earthaccess" in s.get("run", ""))
    assert "pyproj" in instalar["run"].split()                  # remuestrear_grilla lo importa; el NRT no lo trae
    # A15 sobre el peor job OBSERVADO del NRT (56 min, comentario de nrt.yml), no sobre la estimación de COSTO.md §3,
    # porque el costo de la vía en el runner no está medido
    assert "56 min" in NRT.read_text(encoding="utf-8")
    assert paso["timeout-minutes"] >= 1.3 * 56 and d["jobs"]["process"]["timeout-minutes"] > paso["timeout-minutes"]


def test_el_workflow_commitea_solo_la_carpeta_de_la_sombra_y_con_grupo_propio():
    txt, d = _wf()
    commit = next(s for s in d["jobs"]["process"]["steps"] if "git push" in s.get("run", ""))
    adds = re.findall(r'git add "([^"]+)"', commit["run"])
    assert adds == ["data/sombra_codigo_mirova/${{ matrix.volcano }}.json"]
    assert not [ln for ln in commit["run"].splitlines()
                if "mirova_equivalent" in ln and not ln.strip().startswith("#")]   # el comentario lo nombra, el código no
    assert commit["if"] == "steps.correr.outputs.commit == 'true'"               # medir=true no commitea
    grupo = d["concurrency"]["group"]
    otros = {(yaml.safe_load(p.read_text(encoding="utf-8")).get("concurrency") or {}).get("group")
             for p in (ROOT / ".github" / "workflows").glob("*.yml") if p != WF}
    assert grupo not in otros and grupo != "push-main" and d["concurrency"]["cancel-in-progress"] is False
    assert "for attempt in 1 2 3 4 5" in commit["run"]


def test_revisar_sombra_falla_si_la_corrida_queda_verde_sin_la_via():
    """run_pipeline sale 0 aunque cada gránulo dé error (sin pyproj, por ejemplo): la revisión tiene que ponerlo rojo."""
    from revisar_sombra import revisar
    via = {"datetime_utc": "2026-11-05T06:30:00Z", "via_codigo_mirova": True}
    k = {"datetime_utc": "2026-11-05T07:10:00Z", "via_codigo_mirova": "sin_mxd03"}
    viejo = {"datetime_utc": "2026-11-01T06:30:00Z", "via_codigo_mirova": "sin_grilla"}   # fuera de la ventana
    assert revisar([via, viejo], "  VIIRS_NOAA20 (375m) | ...", "2026-11-03", "2026-11-05")[0] is True
    assert revisar([], "", "2026-11-03", "2026-11-05")[0] is False                      # vacía: zombie
    assert revisar([via], "  ERROR processing VJ102IMG...: No module named 'pyproj'", "2026-11-03",
                   "2026-11-05")[0] is False
    ok, resumen = revisar([via, k], "", "2026-11-03", "2026-11-05")
    assert ok is False and "sin_mxd03" in resumen                                        # cayó a K: se ve


def test_la_revision_corre_despues_del_commit_aunque_algo_falle():
    txt, d = _wf()
    pasos = d["jobs"]["process"]["steps"]
    nombres = [s["name"] for s in pasos]
    i_commit = next(i for i, s in enumerate(pasos) if "git push" in s.get("run", ""))
    i_rev = next(i for i, s in enumerate(pasos) if "scripts/revisar_sombra.py" in s.get("run", ""))
    assert i_rev > i_commit, nombres
    assert pasos[i_rev]["if"].startswith("always()") and "steps.correr.outputs.corrio == 'true'" in pasos[i_rev]["if"]
    assert "data/sombra_codigo_mirova/${{ matrix.volcano }}.json" in pasos[i_rev]["run"]
    correr = next(s for s in pasos if s.get("id") == "correr")["run"]
    assert 'echo "corrio=true"' in correr and correr.index('echo "corrio=true"') < correr.index("run_pipeline.py")


def test_produccion_no_nombra_la_sombra():
    """nrt.yml y el perfil operacional no la tocan: la sombra no cambia lo que publica producción."""
    assert PERFIL not in NRT.read_text(encoding="utf-8")
    assert PERFIL not in (ROOT / "pipeline" / "profiles" / "mirova_equivalent.yaml").read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------- 4. de punta a punta
_DRIVER = r'''
import json, sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import numpy as np
raiz = Path(sys.argv[1]); fixture = Path(sys.argv[2]); pid = int(sys.argv[3])
sys.path.insert(0, str(raiz))
import importlib.util
spec = importlib.util.spec_from_file_location("run_pipeline", raiz / "scripts" / "run_pipeline.py")
rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)
from pipeline import mirova_v750_codigo as MV, store
import yaml
vol = {v["name"]: v for v in yaml.safe_load((raiz / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
v = vol["NevadosDeChillan"]
g = MV.grilla_del_volcan("NevadosDeChillan", paso_m=375.0, clave_roi="roi_v375")
z = np.load(fixture / f"grilla_{pid}.npz"); mir, tir = z["mir"].astype(float), z["tir"].astype(float)
lat = np.empty(mir.shape); lon = np.empty(mir.shape)
for f, k in zip(*np.indices(mir.shape).reshape(2, -1)):
    lat[f, k], lon[f, k] = MV.latlon_de(g, f, k)
ang = {"sensor_zenith": np.zeros(mir.shape), "solar_zenith": np.full(mir.shape, 120.0),
       "sensor_azimuth": np.zeros(mir.shape), "solar_azimuth": np.zeros(mir.shape)}
tmp = raiz / "granulos"; tmp.mkdir()
l1b = tmp / "VJ102IMG.A2026283.0654.021.2026283120000.nc"; geo = tmp / "VJ103IMG.A2026283.0654.021.2026283120000.nc"
l1b.write_text("x"); geo.write_text("x")
with patch.object(rp.fetch, "fetch_for_volcano", return_value={"VIIRS_NOAA20": [l1b, geo]}), \
        patch.object(MV, "leer_radiancia_l1b", return_value={"I04": mir, "I05": tir}), \
        patch.object(MV, "leer_geo_l1b", return_value=(lat, lon, ang)):
    rp.process_date(v, datetime(2026, 10, 10), nighttime_only=True)
print(json.dumps({"data_dir": str(store.DATA_DIR)}))
'''


def _copia_minima(destino):
    """Lo que run_pipeline y la vía leen por ruta relativa a su archivo: pipeline/, el script, sus insumos."""
    shutil.copytree(ROOT / "pipeline", destino / "pipeline", ignore=shutil.ignore_patterns("__pycache__"))
    (destino / "scripts").mkdir()
    for f in ("run_pipeline.py", "ceses_esperados.json"):
        if (ROOT / "scripts" / f).exists():
            shutil.copy2(ROOT / "scripts" / f, destino / "scripts" / f)
    shutil.copy2(ROOT / "volcanoes.yaml", destino / "volcanoes.yaml")
    prod = destino / "data" / "mirova_equivalent"
    prod.mkdir(parents=True)
    (prod / "NevadosDeChillan.json").write_text(json.dumps({"volcano": "NevadosDeChillan", "records": [
        {"datetime_utc": "2026-10-01T00:00:00Z", "sensor": "VIIRS_NOAA20", "marca": "produccion"}]}), encoding="utf-8")


def _huellas(data):
    return {str(p.relative_to(data)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(data.rglob("*")) if p.is_file()}


def _correr(raiz, perfil, pid=1305):
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8", VRP_TMP_DIR=str(raiz / "tmp"))
    env.pop("GITHUB_SHA", None)
    driver = raiz / "driver.py"
    driver.write_text(_DRIVER, encoding="utf-8")
    r = subprocess.run([sys.executable, str(driver), str(raiz), str(ROOT / "tests" / "datos_s165_v375"), str(pid)],
                       cwd=raiz, env=env, capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    return r.stdout


def test_de_punta_a_punta_la_sombra_escribe_solo_en_su_carpeta_y_produccion_queda_igual(tmp_path):
    raiz = tmp_path / "repo"
    _copia_minima(raiz)
    antes = _huellas(raiz / "data")
    salida = _correr(raiz, PERFIL)
    despues = _huellas(raiz / "data")
    # producción bit a bit igual y ningún archivo nuevo fuera de la carpeta de la sombra
    assert {k: v for k, v in despues.items() if k.startswith("mirova_equivalent/")} == antes
    assert set(despues) - set(antes) == {"sombra_codigo_mirova/NevadosDeChillan.json"}, salida[-1500:]
    recs = json.loads((raiz / "data" / PERFIL / "NevadosDeChillan.json").read_text(encoding="utf-8"))["records"]
    assert len(recs) == 1
    r = recs[0]
    esperado = next(p for p in json.loads((ROOT / "tests/datos_s165_v375/esperado.json").read_text(
        encoding="utf-8"))["pasadas"] if p["id"] == 1305)
    assert r["via_codigo_mirova"] is True and r["n_anomalous_pixels"] == esperado["npix"] == 20
    assert r["regimen"]["perfil"] == PERFIL                                     # marca de régimen del almacén
    # los tres brazos de posición de V375-E §8.8, desde el record tal como lo guardó el almacén
    radiante = r["primary_cluster"]["centroid_dist_km"]
    pico = r["hotspot_dist_km"]
    cercano = min(p["dist_km"] for p in r["anomaly_pixels"])
    assert len(r["anomaly_pixels"]) == esperado["npix"]
    # el pico es un píxel alertado, así que el cercano no puede quedar más lejos (el centroide sí puede quedar más cerca)
    assert all(isinstance(x, float) for x in (radiante, pico, cercano)) and cercano <= pico + 0.01
    assert r["distance_class"] in ("summit", "far")


def test_control_el_mismo_camino_con_produccion_no_toma_la_via(tmp_path):
    """Control del de arriba: con mirova_equivalent la vía está apagada, K intenta leer el gránulo de mentira y no
    escribe nada; ni la carpeta de la sombra aparece ni producción cambia. Si este diera lo mismo que la sombra, la
    prueba de arriba no estaría midiendo el flag."""
    raiz = tmp_path / "repo"
    _copia_minima(raiz)
    antes = _huellas(raiz / "data")
    salida = _correr(raiz, "mirova_equivalent")
    assert _huellas(raiz / "data") == antes
    assert not (raiz / "data" / PERFIL).exists()
    assert json.loads(salida.strip().splitlines()[-1])["data_dir"].replace("\\", "/").endswith("data/mirova_equivalent")
