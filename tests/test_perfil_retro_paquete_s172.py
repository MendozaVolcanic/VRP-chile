# -*- coding: utf-8 -*-
"""S172/S173, prueba retrospectiva del paquete (pre-registro sellado `s173-prereg-retro-sellado`,
experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md §10.1; plan 2026-11-02-nrt-34-volcanes Tarea 0.2).

POR QUÉ. La retrospectiva tiene que medir EL MISMO detector que la sombra de las vías (si no, su veredicto no dice nada
de lo que la sombra y los 34 van a correr), en una carpeta que nadie más lea (si el tablero o el lector de la sombra la
leyeran, una pasada de 2025 contaminaría la vista operacional o el control de claves de la sombra, A47). Y `extends`
resuelve UN solo nivel (pipeline/profile.py, `_load_profile`), así que si producción cambia un flag de las vías o de
MxD03, un perfil que no lo escriba lo heredaría en silencio (A117, VR172-02): la prueba muta el padre en un directorio
temporal y exige que los seis flags que definen los brazos sigan en el valor escrito.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Mide lo que dice? Los flags se leen desde `pipeline.profile` en un proceso
aparte (A89), nunca del YAML a ojo, y la identidad se compara sobre TODAS las constantes en mayúsculas del módulo.
(2) ¿Puede fallar? Rojo visto antes del verde (perfil ausente: «is not a known profile»), y el control negativo de la
herencia muestra que un perfil que NO escribe los flags sí cambia cuando se muta el padre.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PERFILES = ROOT / "pipeline" / "profiles"
RETRO = "_s172_retro_paquete"
RETRO_K = "_s172_retro_k"
SOMBRA = "sombra_codigo_mirova"
VIAS = ("enable_v750_codigo_mirova", "enable_v375_codigo_mirova", "enable_modis_codigo_mirova")
MXD03 = ("enable_modis_geo_mxd03", "enable_modis_crater_sin_dato", "enable_modis_dist_desde_crater")
SEIS = VIAS + MXD03

# Los conjuntos se vuelcan ordenados: su repr cambia de un proceso a otro (hash aleatorio de str) y daría una
# diferencia falsa en VALID_PROFILES (visto en el primer verde).
_VOLCAR = ("import json, pipeline.profile as p; "
           "f = lambda v: sorted(v) if isinstance(v, (set, frozenset)) else "
           "(v if isinstance(v, (bool, int, float, str, type(None), list, dict)) else repr(v)); "
           "print('@@' + json.dumps({k: f(v) for k, v in vars(p).items() if k.isupper()}, sort_keys=True, default=repr))")


def _constantes(perfil):
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-c", _VOLCAR], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads([x for x in r.stdout.splitlines() if x.startswith("@@")][0][2:])


def _puede_diferir(nombre):
    """Sólo la identidad del perfil y su carpeta (plan, Tarea 0.2 paso 2)."""
    return nombre.startswith("PROFILE") or nombre == "DATA_SUBDIR"


# ------------------------------------------------------------------------------------------- 1. identidad
def test_retro_igual_a_sombra_salvo_nombre_y_carpeta():
    sombra = _constantes(SOMBRA)
    retro = _constantes(RETRO)
    distintas = {k for k in sombra.keys() | retro.keys()
                 if sombra.get(k) != retro.get(k) and not _puede_diferir(k)}
    assert distintas == set(), distintas
    assert retro["DATA_SUBDIR"] == RETRO and retro["PROFILE_NAME"] == RETRO
    assert retro["ENABLE_V750_CODIGO_MIROVA"] and retro["ENABLE_V375_CODIGO_MIROVA"]
    assert retro["ENABLE_MODIS_CODIGO_MIROVA"]
    assert not (retro["ENABLE_MODIS_GEO_MXD03"] or retro["ENABLE_MODIS_CRATER_SIN_DATO"]
                or retro["ENABLE_MODIS_DIST_DESDE_CRATER"])


def test_retro_k_es_retro_con_las_tres_vias_apagadas():
    """§10.1: `_s172_retro_k` es lo mismo con las tres vías en false (brazo K-gemelo, control C-K y nulo de runner)."""
    retro = _constantes(RETRO)
    k = _constantes(RETRO_K)
    vias = {"ENABLE_V750_CODIGO_MIROVA", "ENABLE_V375_CODIGO_MIROVA", "ENABLE_MODIS_CODIGO_MIROVA"}
    distintas = {x for x in retro.keys() | k.keys() if retro.get(x) != k.get(x) and not _puede_diferir(x)}
    assert distintas == vias, distintas
    assert not any(k[v] for v in vias)
    assert k["DATA_SUBDIR"] == RETRO_K


# ------------------------------------------------------------------------------------------- 2. herencia
def _resolver_con_padre_mutado(tmp_path, perfil, mutacion):
    """Copia los perfiles a un directorio temporal, muta el padre y resuelve `perfil` con el MISMO cargador del
    pipeline (pipeline.profile._load_profile, apuntado al directorio temporal). Devuelve la sección thresholds."""
    import shutil
    d = tmp_path / "profiles"
    d.mkdir()
    for f in PERFILES.glob("*.yaml"):
        shutil.copy(f, d / f.name)
    padre = yaml.safe_load((d / "mirova_equivalent.yaml").read_text(encoding="utf-8"))
    padre["thresholds"].update(mutacion)
    (d / "mirova_equivalent.yaml").write_text(yaml.safe_dump(padre, allow_unicode=True), encoding="utf-8")
    codigo = ("import json, sys, pathlib, pipeline.profile as p; "
              "p.PROFILES_DIR = pathlib.Path(sys.argv[1]); p.VALID_PROFILES = {x.stem for x in p.PROFILES_DIR.glob('*.yaml')}; "
              "import os; os.environ['VRP_PROFILE'] = sys.argv[2]; "
              "print('@@' + json.dumps(p._load_profile()['thresholds'], default=repr))")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-c", codigo, str(d), perfil], cwd=ROOT, env=env, capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads([x for x in r.stdout.splitlines() if x.startswith("@@")][0][2:])


MUTACION_PADRE = {"enable_v750_codigo_mirova": False, "enable_v375_codigo_mirova": True,
                  "enable_modis_codigo_mirova": False, "enable_modis_geo_mxd03": True,
                  "enable_modis_crater_sin_dato": True, "enable_modis_dist_desde_crater": True}


@pytest.mark.parametrize("perfil,esperado", [
    (RETRO, {**{v: True for v in VIAS}, **{m: False for m in MXD03}}),
    (RETRO_K, {**{v: False for v in VIAS}, **{m: False for m in MXD03}}),
])
def test_los_seis_flags_no_siguen_al_padre(tmp_path, perfil, esperado):
    t = _resolver_con_padre_mutado(tmp_path, perfil, MUTACION_PADRE)
    assert {k: t.get(k) for k in SEIS} == esperado


def test_control_negativo_un_perfil_que_no_escribe_los_flags_si_los_hereda(tmp_path):
    """Si el instrumento no pudiera ver la herencia, el test de arriba pasaría por construcción. La sombra no escribe
    los tres de MxD03: con el padre mutado, los hereda encendidos."""
    t = _resolver_con_padre_mutado(tmp_path, SOMBRA, MUTACION_PADRE)
    assert all(t.get(m) is True for m in MXD03), {m: t.get(m) for m in MXD03}


def test_los_seis_flags_estan_escritos_en_thresholds_del_yaml_propio():
    for perfil in (RETRO, RETRO_K):
        d = yaml.safe_load((PERFILES / f"{perfil}.yaml").read_text(encoding="utf-8"))
        assert d.get("extends") == "mirova_equivalent", perfil
        assert set(SEIS) <= set((d.get("thresholds") or {})), perfil


# ------------------------------------------------------------------------------------------- 3. aislamiento
def test_la_carpeta_no_la_lee_el_tablero_ni_el_lector_de_la_sombra():
    """Ningún archivo del sitio (frontend/), de los workflows que publican, del revisor de la sombra ni del lector de
    V375-E nombra la carpeta. Se busca el prefijo `_s172_retro` para cubrir las dos (paquete y K)."""
    vigilados = list((ROOT / "frontend").rglob("*.html")) + list((ROOT / "frontend").rglob("*.js"))
    vigilados += [ROOT / ".github" / "workflows" / n for n in ("pages-deploy.yml", "nrt.yml", "sombra-codigo-mirova.yml",
                                                               "sombra-34.yml")]
    vigilados += [ROOT / "scripts" / "revisar_sombra.py", ROOT / "scripts" / "banco_paridad.py"]
    vigilados += list((ROOT / "experiments" / "_s168").rglob("*.py"))
    assert len([p for p in vigilados if p.exists()]) >= 8
    lo_leen = [str(p.relative_to(ROOT)) for p in vigilados if p.exists()
               and "_s172_retro" in p.read_text(encoding="utf-8", errors="replace")]
    assert lo_leen == [], lo_leen


def test_ninguna_otra_definicion_escribe_en_las_carpetas_de_la_retro():
    duenos = {}
    for f in PERFILES.glob("*.yaml"):
        sub = ((yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("output") or {}).get("data_subdir")
        duenos.setdefault(sub, []).append(f.stem)
    assert duenos.get(RETRO) == [RETRO]
    assert duenos.get(RETRO_K) == [RETRO_K]
