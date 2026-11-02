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
import shutil
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


def test_las_34_entradas_son_exactamente_las_de_la_regla():
    """VS34-02 (mutación G4: roi_v750 de un volcán nuevo cambiado a sens pasaba en verde): cada entrada de los 34 es
    exactamente la que da el generador (epsg, X0, Y0, centro y roi_v750 def), sin claves de más."""
    import generar_grillas_34 as G
    refs = MV._referencias()
    for v in _los_34():
        assert refs[v["name"]] == G.entrada(v), v["name"]


# --------------------------------------------------------------------------------------------- 2b. vecinos
def test_vecinos_dentro_de_la_grilla_son_los_de_vecinos_yaml():
    """VS34-01 y VS34-07: la lista de volcanes con otro volcán dentro de su grilla, con la clase de caja en que cae,
    se recalcula con la geometría de la vía y tiene que ser la de experiments/_s172_sombra34/vecinos.yaml. Fija además
    los cuatro con un vecino de los 11 y que ninguno de esos vecinos cae en la caja sensible ni en el anillo."""
    import vecinos_en_la_grilla as VE
    fijado = yaml.safe_load((ROOT / "experiments" / "_s172_sombra34" / "vecinos.yaml").read_text(encoding="utf-8"))
    calc = VE.vecinos()
    assert calc == fijado["volcanes"]
    assert len(calc) == 13
    con_tier_a = sorted(n for n, lista in calc.items() if any(e["tier_a"] for e in lista))
    assert con_tier_a == ["AntillancaCasablanca", "Callaqui", "Michinmahuida", "Quetrupillan"]
    for n in con_tier_a:
        for e in calc[n]:
            if e["tier_a"]:
                assert set(e["caja"].values()) == {0}, (n, e)
    # control positivo del instrumento: Calbuco cae en el borde de la grilla V750 de Osorno (VS34-07)
    assert calc["Osorno"][0]["vecino"] == "Calbuco" and calc["Osorno"][0]["caja"]["VIIRS750"] == "borde"


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


MOLDE = ROOT / ".github" / "workflows" / "sombra-codigo-mirova.yml"


def _normalizar(x):
    s = json.dumps(x, sort_keys=True, ensure_ascii=False)
    return s.replace("sombra_codigo_mirova", "sombra_34").replace("sombra34-", "sombra-")


def test_workflow_es_el_molde_paso_a_paso_salvo_lo_declarado():
    """VS34-02 (mutaciones W8, W9, W11 y W12 pasaban en verde): cada paso de sombra-34.yml tiene, fuera de su `run`,
    lo mismo que el paso correspondiente de la sombra de los 11 (if con always(), id, uses, with, env y timeouts), y
    el job el mismo runs-on, timeout, permisos y fail-fast. Sólo se permiten distintos el nombre de perfil y carpeta,
    el nombre del artefacto, la matriz, el paralelismo, el cron y el grupo (probados aparte)."""
    a = _wf()["jobs"]["process"]
    b = yaml.safe_load(MOLDE.read_text(encoding="utf-8"))["jobs"]["process"]
    for clave in ("runs-on", "timeout-minutes", "permissions"):
        assert a[clave] == b[clave], clave
    assert a["strategy"]["fail-fast"] == b["strategy"]["fail-fast"]
    assert len(a["steps"]) == len(b["steps"])
    for pa, pb in zip(a["steps"], b["steps"]):
        assert _normalizar(pa.get("name")) == _normalizar(pb.get("name"))
        resto_a = {k: v for k, v in pa.items() if k not in ("run", "name")}
        resto_b = {k: v for k, v in pb.items() if k not in ("run", "name")}
        assert _normalizar(resto_a) == _normalizar(resto_b), pa.get("name")
        assert ("run" in pa) == ("run" in pb), pa.get("name")


_CRON = re.compile(r"^(\d{1,2}) (\d{1,2}) \* \* \*$")


@pytest.mark.parametrize("wf", [WF, WF_VIG], ids=["sombra", "vigilancia"])
def test_cron_diario_valido(wf):
    """VS34-02 (mutación VW3: un cron del 31 de febrero no dispara nunca y pasaba en verde): un solo cron, diario, con
    minuto y hora posibles."""
    d = yaml.safe_load(wf.read_text(encoding="utf-8"))
    crones = [c["cron"] for c in d["on"]["schedule"]]
    assert len(crones) == 1
    m = _CRON.match(crones[0])
    assert m and int(m.group(1)) < 60 and int(m.group(2)) < 24, crones


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


def test_workflow_de_vigilancia_forma():
    texto = WF_VIG.read_text(encoding="utf-8")
    d = yaml.safe_load(texto)
    assert "on" in d and True not in d and d["on"]["schedule"] and "workflow_dispatch" in d["on"]
    assert d["permissions"] == {"contents": "read", "issues": "write"}
    assert "git push" not in texto                       # no escribe en el repo: G4 no aplica
    job = d["jobs"]["vigilar"]
    checkout = next(p for p in job["steps"] if str(p.get("uses", "")).startswith("actions/checkout"))
    assert checkout["with"]["ref"] == "main"             # VS34-02, mutación VW4: lee los datos de main
    assert next(p for p in job["steps"] if p.get("name") == "Open issue")["if"] == "always()"


def test_cli_de_la_vigilancia_sale_1_en_ciega(tmp_path):
    """VS34-02 (mutación V5): el código de salida dice el veredicto (CIEGA 1, OK 0)."""
    ahora = datetime(2026, 11, 20, 23, 30, tzinfo=timezone.utc)
    wf = tmp_path / "wf.yml"
    wf.write_text(yaml.safe_dump({"jobs": {"process": {"strategy": {"matrix": {"volcano": ["A"]}}}}}),
                  encoding="utf-8")
    datos = tmp_path / "d"
    datos.mkdir()
    for t, rc in ((ahora - timedelta(hours=5), 0), (ahora - timedelta(hours=60), 1)):
        (datos / "A.json").write_text(json.dumps({"records": [_record(t)]}), encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "vigilar_sombra_34.py"), "--dir", str(datos),
                            "--workflow", str(wf), "--ahora", ahora.strftime("%Y-%m-%dT%H:%M:%SZ")],
                           capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == rc, (rc, r.stdout, r.stderr)


# Los pasos REALES del workflow de vigilancia, ejecutados con bash y un `gh` falso que anota lo que le piden
# (VS34-02: la prueba anterior buscaba subcadenas y `OK|ESPERA|CIEGA)` pasaba en verde).
_GH_FALSO = """#!/usr/bin/env bash
echo "$*" | tr '\\n' ' ' >> "$GH_LOG"
echo >> "$GH_LOG"
exit 0
"""


def _paso_vig(nombre):
    return next(p for p in yaml.safe_load(WF_VIG.read_text(encoding="utf-8"))["jobs"]["vigilar"]["steps"]
                if p.get("name") == nombre)


def _correr_vigilancia(tmp_path, ahora, viejo=None, script_roto=False):
    """Arma un repo de juguete, corre los pasos «Vigilancia» y «Open issue» tal como están en el workflow, y devuelve
    lo que se le pidió a gh. Señuelo: data/sombra_codigo_mirova/ tiene lo contrario que data/sombra_34/ (fresco donde
    éste está viejo y al revés), así que un --dir equivocado cambia el resultado (mutación VW2)."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("sin bash")
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / ".github" / "workflows").mkdir(parents=True)
    shutil.copy(WF, repo / ".github" / "workflows" / "sombra-34.yml")
    if script_roto:
        (repo / "scripts" / "vigilar_sombra_34.py").write_text("raise SystemExit(3)\n", encoding="utf-8")
    else:
        shutil.copy(ROOT / "scripts" / "vigilar_sombra_34.py", repo / "scripts" / "vigilar_sombra_34.py")
    fresco, rancio = ahora - timedelta(hours=5), ahora - timedelta(hours=60)
    for carpeta, invertir in (("sombra_34", False), ("sombra_codigo_mirova", True)):
        (repo / "data" / carpeta).mkdir(parents=True)
        for n in _matriz(WF):
            es_viejo = (n == viejo) != invertir if viejo else invertir
            (repo / "data" / carpeta / f"{n}.json").write_text(
                json.dumps({"records": [_record(rancio if es_viejo else fresco)]}), encoding="utf-8")
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    (bin_ / "gh").write_text(_GH_FALSO, encoding="utf-8", newline="\n")
    os.chmod(bin_ / "gh", 0o755)
    rt = tmp_path / "rt"
    rt.mkdir()
    log = tmp_path / "gh.log"
    log.write_text("", encoding="utf-8")
    env = dict(os.environ, RUNNER_TEMP=rt.as_posix(), GH_LOG=log.as_posix(), GITHUB_SERVER_URL="https://x",
               GITHUB_REPOSITORY="o/r", GITHUB_RUN_ID="1", PYTHONIOENCODING="utf-8",
               VIGILAR_SOMBRA_34_AHORA=ahora.strftime("%Y-%m-%dT%H:%M:%SZ"),
               PATH=os.pathsep.join([str(bin_), os.path.dirname(sys.executable), os.environ.get("PATH", "")]))
    vig = re.sub(r"\$\{\{\s*steps\.alta\.outputs\.alta\s*\}\}", "", _paso_vig("Vigilancia")["run"])
    assert "${{" not in vig
    (tmp_path / "vig.sh").write_text(vig, encoding="utf-8", newline="\n")
    r = subprocess.run([bash, "-e", (tmp_path / "vig.sh").as_posix()], cwd=repo, env=env, capture_output=True,
                       text=True, encoding="utf-8")
    env["OUTCOME"] = "success" if r.returncode == 0 else "failure"
    issue = _paso_vig("Open issue")
    for clave in issue.get("env", {}):
        assert clave in ("GH_TOKEN", "OUTCOME"), clave
    (tmp_path / "issue.sh").write_text(issue["run"], encoding="utf-8", newline="\n")
    r2 = subprocess.run([bash, "-e", (tmp_path / "issue.sh").as_posix()], cwd=repo, env=env, capture_output=True,
                        text=True, encoding="utf-8")
    assert r2.returncode == 0, r2.stderr
    # split("\n") y no splitlines(): en Windows la salida de Python trae \r dentro del cuerpo del issue
    return [ln for ln in log.read_bytes().decode("utf-8").split("\n") if ln.startswith("issue create")]


AHORA_VIG = datetime(2026, 11, 20, 23, 30, tzinfo=timezone.utc)


def test_pasos_reales_todo_fresco_no_abre_issue(tmp_path):
    assert _correr_vigilancia(tmp_path, AHORA_VIG) == []


def test_pasos_reales_un_volcan_viejo_abre_issue_de_vigilancia_ciega(tmp_path):
    creados = _correr_vigilancia(tmp_path, AHORA_VIG, viejo="Hudson")
    assert len(creados) == 1 and "--title Sombra de los 34: vigilancia ciega: " in creados[0], creados
    assert "Hudson" in creados[0]


def test_pasos_reales_antes_de_empezar_espera_sin_issue(tmp_path):
    assert _correr_vigilancia(tmp_path, datetime(2026, 11, 4, 12, tzinfo=timezone.utc), viejo="Hudson") == []


def test_pasos_reales_sin_veredicto_abre_issue_de_falla(tmp_path):
    creados = _correr_vigilancia(tmp_path, AHORA_VIG, script_roto=True)
    assert len(creados) == 1 and "--title Sombra de los 34: la vigilancia fallo: " in creados[0], creados


# --------------------------------------------------------------------------------------------- 6. quién vigila a la vigilancia
JS = ROOT / "scripts" / "nrt_monitor_decision.js"
MONITOR = ROOT / ".github" / "workflows" / "nrt-monitor.yml"


def _ausencia(runs, ahora, fijo_nombre, alta):
    codigo = ("const M = require(%s); console.log(JSON.stringify(M.decidirAusencia(%s, Date.parse(%s), M[%s], %s)));"
              % (json.dumps(str(JS)), json.dumps(runs), json.dumps(ahora), json.dumps(fijo_nombre), json.dumps(alta)))
    out = subprocess.run(["node", "-e", codigo], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def _corrida(creada, conclusion, evento="schedule", estado="completed"):
    return {"created_at": creada, "conclusion": conclusion, "event": evento, "status": estado, "html_url": "u"}


def test_ausencia_de_la_sombra_34():
    """VS34-04: verde reciente da ok; la última verde de hace más de 26 h alerta; sin corridas alerta; antes del alta
    más 30 h (o de la fecha fija) no decide; una manual no cuenta."""
    alta = "2026-11-10T20:00:00Z"
    assert _ausencia([], "2026-11-11T12:00:00Z", "SOMBRA_34_DESDE", alta)["accion"] == "inactivo"
    assert _ausencia([], "2026-11-12T12:00:00Z", "SOMBRA_34_DESDE", alta)["accion"] == "alerta"
    ok = [_corrida("2026-11-12T13:07:00Z", "success")]
    assert _ausencia(ok, "2026-11-12T18:30:00Z", "SOMBRA_34_DESDE", alta)["accion"] == "ok"
    assert _ausencia(ok, "2026-11-13T18:30:00Z", "SOMBRA_34_DESDE", alta)["accion"] == "alerta"
    manual = [_corrida("2026-11-12T13:07:00Z", "success", evento="workflow_dispatch")]
    assert _ausencia(manual, "2026-11-12T18:30:00Z", "SOMBRA_34_DESDE", alta)["accion"] == "alerta"
    # sin dato del alta, la fecha fija
    assert _ausencia([], "2026-11-03T12:00:00Z", "SOMBRA_34_DESDE", None)["accion"] == "inactivo"
    assert _ausencia([], "2026-11-04T12:00:00Z", "VIGILANCIA_34_DESDE", None)["accion"] == "alerta"


def test_nrt_monitor_vigila_la_sombra_34_y_su_vigilancia():
    d = yaml.safe_load(MONITOR.read_text(encoding="utf-8"))
    pasos = [p for p in d["jobs"]["check"]["steps"] if "decidirAusencia" in str((p.get("with") or {}).get("script"))]
    assert len(pasos) == 1
    p = pasos[0]
    assert p.get("if") == "always()"
    s = p["with"]["script"]
    for wf in ("'sombra-34.yml'", "'vigilancia-sombra-34.yml'"):
        assert wf in s
    assert "issues.create" in s and "state: 'closed'" in s and "getWorkflow" in s
    assert re.search(r"if \(d\.accion === 'inactivo' \|\| d\.accion === 'pendiente'\) continue;", s)
    # los workflows que nombra existen
    assert WF.exists() and WF_VIG.exists()


def test_cadencia_cuenta_la_sombra_34_y_su_vigilancia_una_vez_al_dia():
    from scripts.medir_cadencia_cron import ESPERADO_POR_DIA
    for wf in (WF, WF_VIG):
        nombre = yaml.safe_load(wf.read_text(encoding="utf-8"))["name"]
        assert ESPERADO_POR_DIA.get(nombre) == 1, nombre


# --------------------------------------------------------------------------------------------- 7. Pages
def test_pages_trata_a_la_sombra_34_como_a_las_otras_sombras():
    """VS34-03: pages-deploy copia data/ entero (`cp -r data _site/data`), así que hoy publica data/experimental_v2/
    (que lee frontend/experimental/index.html) y data/sombra_codigo_mirova/ (que no lee nadie). La sombra de los 34
    recibe el mismo trato: si alguien excluye una sombra del artefacto, esta prueba obliga a decidir la otra."""
    run = next(p for p in yaml.safe_load((ROOT / ".github/workflows/pages-deploy.yml").read_text(encoding="utf-8"))
               ["jobs"]["build"]["steps"] if p.get("name") == "Prepare Pages artifact")["run"]
    excluye_11 = "sombra_codigo_mirova" in run
    excluye_34 = "sombra_34" in run
    assert excluye_11 == excluye_34, "pages-deploy trata distinto a las dos sombras"
