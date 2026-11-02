# -*- coding: utf-8 -*-
"""S172: sombra de los 34 volcanes fuera del NRT (grillas, perfil, workflow y vigilancia ciega).

POR QUÉ. La sombra de los 34 corre las tres vías «código MIROVA» en volcanes que MIROVA no vigila. Si un volcán no
tuviera grilla, la vía caería a K en silencio (`via_codigo_mirova: "sin_grilla"`) y la sombra mediría otra cosa
(A118); si el perfil no resolviera el mismo detector que la sombra de los 11, la comparación entre los dos grupos no
valdría; si el workflow corriera con otro perfil o escribiera en otra carpeta, contaminaría producción; y si dejara de
producir, nadie lo notaría (un vigilante ciego da verde). Cada bloque de abajo fija una de esas cosas.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Mide lo que dice? Las grillas se prueban corriendo la vía de punta a punta
sobre un gránulo sintético sin red, con un foco en el cráter, y exigiendo que la vía lo encuentre en el cráter; el
perfil se lee desde pipeline.profile (A89), nunca del YAML. (2) ¿Puede fallar? Rojo visto antes del verde en el commit
(grilla de main: 34 rojos; sin perfil ni workflow: rojos por archivo ausente), y la vigilancia tiene control negativo
y positivo con datos armados.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments" / "_s172_sombra34"))

from pipeline import mirova_v750_codigo as MV  # noqa: E402

WF = ROOT / ".github" / "workflows" / "sombra-34.yml"
WF_VIG = ROOT / ".github" / "workflows" / "vigilancia-sombra-34.yml"
NRT = ROOT / ".github" / "workflows" / "nrt.yml"
GRILLAS = ROOT / "pipeline" / "grillas_mirova.yaml"
# pipeline/grillas_mirova.yaml de main 14fb62030 (tag pre-s172-sombra-34), con saltos de línea LF: 3.805 bytes.
# Las 11 entradas de los Tier A y la cabecera tienen que seguir siendo esos bytes, al comienzo del archivo.
GRILLAS_MAIN_LEN = 3805
GRILLAS_MAIN_SHA256 = "da755f3e7fc70bfec052bee7a35bcecc6a685e9f3b3c3b5a2c61c5e398c42636"


def _volcanes():
    return yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]


def _matriz(wf):
    d = yaml.safe_load(wf.read_text(encoding="utf-8"))
    return list(d["jobs"]["process"]["strategy"]["matrix"]["volcano"])


def _los_34():
    nrt = set(_matriz(NRT))
    return [v for v in _volcanes() if v.get("active", True) and v["name"] not in nrt]


# --------------------------------------------------------------------------------------------- 1. la lista
def test_los_34_son_volcanoes_yaml_menos_el_nrt():
    nombres = [v["name"] for v in _los_34()]
    assert len(nombres) == 34 and len(set(nombres)) == 34
    assert sorted(_matriz(WF)) == sorted(nombres)
    assert not set(_matriz(WF)) & set(_matriz(NRT))


# --------------------------------------------------------------------------------------------- 2. la grilla
def test_las_11_entradas_de_main_no_cambiaron_ni_un_byte():
    b = GRILLAS.read_bytes().replace(b"\r\n", b"\n")
    assert len(b) > GRILLAS_MAIN_LEN
    assert hashlib.sha256(b[:GRILLAS_MAIN_LEN]).hexdigest() == GRILLAS_MAIN_SHA256


def test_la_grilla_tiene_los_45_y_nada_mas():
    refs = MV._referencias()
    assert set(refs) == {v["name"] for v in _volcanes()}


def test_la_regla_reproduce_a_los_8_tier_a_con_punto_del_yaml():
    """Control de la regla con que se generaron los 34: en los 8 Tier A cuyo punto de MIROVA es el del yaml, la regla
    da su (X0, Y0) a menos de 1,5 m (lo medido: 0,0 m en X y 0,9 a 1,0 m en Y, redondeo del TIF)."""
    import generar_grillas_34 as G
    refs = MV._referencias()
    tier_a = {k: refs[k] for k in _matriz(NRT)}
    ctl = G.control_8(_volcanes(), tier_a)
    assert len(ctl) == 8
    for nombre, dx, dy, epsg_igual in ctl:
        assert epsg_igual and abs(dx) <= 1.5 and abs(dy) <= 1.5, (nombre, dx, dy)


@pytest.mark.parametrize("familia", ["VIIRS750", "VIIRS375", "MODIS"])
def test_cada_uno_de_los_34_tiene_grilla_centrada_en_su_crater(familia):
    """Grilla de cada sensor, zona UTM por longitud, y el lat/lon del yaml cae justo en (X0, Y0) (a 0,01 celda): la
    vía reconoce el volcán por sus coordenadas y lo pone donde corresponde. (X0, Y0) está a 25 km de la primera
    columna y de la última fila, que en 375 y 750 m no es la celda central: 66,67 y 33,33 celdas, como en los 11.)"""
    cfg = MV.FAMILIAS[familia]
    for v in _los_34():
        nombre = v["name"]
        assert MV.volcan_por_coordenadas(v["lat"], v["lon"]) == nombre
        g = MV.grilla_del_volcan(nombre, paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
        assert g is not None, nombre
        assert g["n"] == MV.n_celdas(cfg["paso_m"]) and g["roi"] in MV.TIPOS_ROI
        assert g["epsg"] == (32718 if v["lon"] < -72.0 else 32719), nombre
        fila, col = MV.posicion_de(g, v["lat"], v["lon"])
        k = MV.MEDIA_GRILLA_M / cfg["paso_m"]
        assert abs(col - k) < 0.01 and abs(fila - (g["n"] - 1 - k)) < 0.01, (nombre, fila, col)


def _granulo_sintetico(lat0, lon0, familia, t_foco=600.0, n=81, span=0.3):
    """Gránulo de barrido inventado (sin red): fondo de 270 K en MIR y 265 K en TIR con ruido fijo, de noche, y un
    píxel caliente en el cráter. Cubre ±33 km, más que la grilla de 51 x 51 km."""
    cfg = MV.FAMILIAS[familia]
    la = lat0 + np.linspace(-span, span, n)
    lo = lon0 + np.linspace(-span, span, n) / np.cos(np.radians(lat0))
    LO, LA = np.meshgrid(lo, la[::-1])
    rng = np.random.default_rng(172)
    tm = 270.0 + rng.normal(0, 0.3, LA.shape)
    tt = 265.0 + rng.normal(0, 0.3, LA.shape)
    i, j = np.unravel_index(np.argmin((LA - lat0) ** 2 + ((LO - lon0) * np.cos(np.radians(lat0))) ** 2), LA.shape)
    tm[i, j] = t_foco
    b_mir, b_tir = cfg["bandas"]
    rad = {b_mir: MV.temperatura_a_radiancia(tm, cfg["lam_mir"]), b_tir: MV.temperatura_a_radiancia(tt, cfg["lam_tir"])}
    ang = {k: np.full(LA.shape, val) for k, val in (("solar_zenith", 120.0), ("sensor_zenith", 10.0),
                                                     ("solar_azimuth", 0.0), ("sensor_azimuth", 90.0))}
    return rad, LA, LO, ang


@pytest.mark.parametrize("i", range(34))
def test_la_via_acepta_la_grilla_y_encuentra_el_foco_en_el_crater(i):
    """De punta a punta, sin red: la vía corre (no devuelve None ni cae a K) y el foco puesto en el cráter sale a
    menos de 1 km de él. Los sensores rotan entre los 34 (cada familia en 11 o 12 volcanes) para que la prueba siga
    siendo chica; la geometría de las tres familias en los 34 la cubre la prueba anterior."""
    v = _los_34()[i]
    familia = ("VIIRS750", "VIIRS375", "MODIS")[i % 3]
    rad, LA, LO, ang = _granulo_sintetico(v["lat"], v["lon"], familia)
    rec = MV.calcular_vrp_granulo(rad, LA, LO, ang, v["name"], v["lat"], v["lon"], None, "SINTETICO",
                                  familia=familia)
    assert rec is not None, (v["name"], familia)
    assert rec["via_codigo_mirova"] is True
    assert rec["vrp_mw"] > 0 and rec["n_anomalous_pixels"] >= 1, (v["name"], familia, rec["diag_codigo_mirova"])
    assert rec["final_hotspot_dist_km"] < 1.0, (v["name"], familia, rec["final_hotspot_dist_km"])
    assert rec["distance_class"] is None   # sin inner_radius_km en el yaml (perfil sombra_34, cabecera)


def test_control_un_granulo_sin_foco_no_publica():
    """Control negativo del instrumento anterior: sin foco el mismo gránulo no da magnitud (la prueba puede fallar)."""
    v = _los_34()[0]
    rad, LA, LO, ang = _granulo_sintetico(v["lat"], v["lon"], "VIIRS750", t_foco=270.0)
    rec = MV.calcular_vrp_granulo(rad, LA, LO, ang, v["name"], v["lat"], v["lon"], None, "SINTETICO",
                                  familia="VIIRS750")
    assert rec is not None and rec["vrp_mw"] == 0.0


# --------------------------------------------------------------------------------------------- 3. el perfil
def _constantes(perfil):
    """Todas las constantes en mayúsculas de pipeline.profile, resueltas con VRP_PROFILE (A89)."""
    codigo = ("import json, pipeline.profile as p; "
              "print(json.dumps({k: getattr(p, k) for k in dir(p) if k.isupper()}, default=repr, sort_keys=True))")
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_el_perfil_resuelve_las_tres_vias_sin_mxd03_y_su_carpeta():
    c = _constantes("sombra_34")
    assert c["PROFILE_NAME"] == "sombra_34" and c["DATA_SUBDIR"] == "sombra_34"
    assert c["ENABLE_V750_CODIGO_MIROVA"] and c["ENABLE_V375_CODIGO_MIROVA"] and c["ENABLE_MODIS_CODIGO_MIROVA"]
    assert not (c["ENABLE_MODIS_GEO_MXD03"] or c["ENABLE_MODIS_CRATER_SIN_DATO"] or c["ENABLE_MODIS_DIST_DESDE_CRATER"])
    assert c["SENSOR_MODIS"] and c["SENSOR_VIIRS_375"] and c["SENSOR_VIIRS_750"]
    assert c["VOLCANO_OVERRIDES"] == {}


def test_el_perfil_es_el_detector_de_la_sombra_de_los_11():
    """Mismo detector: todas las constantes resueltas iguales a sombra_codigo_mirova salvo nombre y carpeta.
    VALID_PROFILES (la lista de perfiles del directorio, un conjunto cuyo orden de impresión cambia entre procesos)
    no es del perfil y se excluye."""
    a, b = _constantes("sombra_34"), _constantes("sombra_codigo_mirova")
    for c in (a, b):
        c.pop("VALID_PROFILES")
    distintas = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    assert distintas == ["DATA_SUBDIR", "PROFILE_NAME"], distintas


# --------------------------------------------------------------------------------------------- 4. el workflow
def _wf():
    return yaml.safe_load(WF.read_text(encoding="utf-8"))


def _paso(nombre):
    for p in _wf()["jobs"]["process"]["steps"]:
        if p.get("name") == nombre:
            return p
    raise AssertionError(nombre)


def test_workflow_on_entre_comillas_con_schedule_y_dispatch():
    d = _wf()
    assert "on" in d and True not in d          # A43: "on" quedó como texto, no como booleano
    assert "workflow_dispatch" in d["on"]
    crones = [c["cron"] for c in d["on"]["schedule"]]
    assert crones == ["7 13 * * *"]
    hora = int(crones[0].split()[1])
    assert not 1 <= hora <= 12                  # fuera de los despachos del NRT (:10 de las 01 a las 12 UTC)


def test_workflow_grupo_propio_y_paralelismo():
    d = _wf()
    assert d["concurrency"]["group"] == "sombra-34" and d["concurrency"]["cancel-in-progress"] is False
    s = d["jobs"]["process"]["strategy"]
    assert s["max-parallel"] == 8 and s["fail-fast"] is False


def test_workflow_solo_token_y_corta_si_viene_vacio():
    texto = WF.read_text(encoding="utf-8")
    assert "EARTHDATA_USERNAME" not in texto and "EARTHDATA_PASSWORD" not in texto
    run = _paso("Run VRP pipeline, perfil sombra_34")["run"]
    assert run.index('-z "$EARTHDATA_TOKEN"') < run.index("run_pipeline.py")


def test_workflow_corre_el_perfil_y_su_asercion_pasa():
    """La aserción del paso se ejecuta tal cual con VRP_PROFILE=sombra_34 y pasa; con el perfil de la sombra de los
    11 falla (control: la aserción puede fallar)."""
    run = _paso("Run VRP pipeline, perfil sombra_34")["run"]
    assert "run_pipeline.py --profile sombra_34" in run
    m = re.search(r'VRP_PROFILE=sombra_34 python -c "([^"]+)"', run)
    assert m, "no está la aserción del perfil"
    for perfil, esperado in (("sombra_34", 0), ("sombra_codigo_mirova", 1)):
        env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, "-c", m.group(1)], cwd=ROOT, env=env, capture_output=True, text=True,
                           encoding="utf-8")
        assert (r.returncode != 0) == bool(esperado), (perfil, r.stdout, r.stderr)


def test_workflow_commitea_solo_su_carpeta_con_reintento_y_revisa():
    run = _paso("Commit sombra data")["run"]
    adds = [ln.strip() for ln in run.splitlines() if ln.strip().startswith("git add")]
    assert adds == ['git add "data/sombra_34/${{ matrix.volcano }}.json" 2>/dev/null'], adds
    assert "git pull --rebase" in run and "for attempt in 1 2 3 4 5" in run
    rev = _paso("Revisar que salieron records de la via")["run"]
    assert 'scripts/revisar_sombra.py --json "data/sombra_34/${{ matrix.volcano }}.json"' in rev


# --------------------------------------------------------------------------------------------- 5. vigilancia ciega
def _record(t, via=True, perfil="sombra_34"):
    return {"via_codigo_mirova": via, "regimen": {"perfil": perfil}, "processed_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ")}


def test_vigilancia_espera_ok_y_ciega(tmp_path):
    import vigilar_sombra_34 as VG
    ahora = datetime(2026, 11, 20, 23, 30, tzinfo=timezone.utc)
    fresco = {"records": [_record(ahora - timedelta(hours=10))]}
    viejo = {"records": [_record(ahora - timedelta(hours=60))]}
    de_k = {"records": [_record(ahora - timedelta(hours=1), via="sin_mxd03")]}
    otro_perfil = {"records": [_record(ahora - timedelta(hours=1), perfil="mirova_equivalent")]}
    for nombre, d in (("A", fresco), ("B", viejo), ("C", de_k), ("D", otro_perfil)):
        (tmp_path / f"{nombre}.json").write_text(json.dumps(d), encoding="utf-8")
    (tmp_path / "F.json").write_text("{no es json", encoding="utf-8")
    # control positivo: todo fresco da OK
    assert VG.vigilar(tmp_path, ["A"], ahora)["veredicto"] == "OK"
    # control negativo: viejo, sólo K, otro perfil, sin archivo e ilegible son ciegos
    d = VG.vigilar(tmp_path, ["A", "B", "C", "D", "E", "F"], ahora)
    assert d["veredicto"] == "CIEGA"
    assert sorted(c["volcano"] for c in d["ciegos"]) == ["B", "C", "D", "E", "F"]
    # antes de la fecha mínima más 48 h, o antes de 48 h desde el alta, espera
    assert VG.vigilar(tmp_path, ["E"], datetime(2026, 11, 4, 12, tzinfo=timezone.utc))["veredicto"] == "ESPERA"
    assert VG.vigilar(tmp_path, ["E"], ahora, alta=ahora - timedelta(hours=20))["veredicto"] == "ESPERA"
    # matriz vacía: ciega, no verde
    assert VG.vigilar(tmp_path, [], ahora)["veredicto"] == "CIEGA"


def test_vigilancia_lee_la_matriz_del_workflow_de_la_sombra():
    import vigilar_sombra_34 as VG
    assert VG.volcanes_de_la_matriz(WF) == _matriz(WF)


def test_workflow_de_vigilancia_abre_issue():
    texto = WF_VIG.read_text(encoding="utf-8")
    d = yaml.safe_load(texto)
    assert "on" in d and True not in d and d["on"]["schedule"] and "workflow_dispatch" in d["on"]
    assert d["permissions"]["issues"] == "write"
    assert "git push" not in texto                       # no escribe en el repo: G4 no aplica
    assert "scripts/vigilar_sombra_34.py" in texto and "gh issue create" in texto
    assert "CIEGA)" in texto and "--workflow .github/workflows/sombra-34.yml" in texto
