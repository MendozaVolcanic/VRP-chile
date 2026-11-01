# -*- coding: utf-8 -*-
"""S157: el job `merge` de reproc-chunked.yml conserva lo que main ya tiene.

Corre el `run:` REAL del paso de union (extraido del yml, sin copiarlo) contra
un repositorio de origen local. Lo que protege:

1. Relanzar un trozo de un volcan no borra el resto de su historico en main
   (el defecto de S157 con NevadosDeChillan).
2. La base se lee de main al momento de unir, no del checkout del despacho:
   si main cambio despues del despacho, el merge parte de la version nueva.
3. Si main se mueve entre el fetch y el push, el push se rechaza y el intento
   siguiente vuelve a leer la base (no se une contra una base vieja).

Se salta si no hay `bash` o `git` (el CI de ubuntu tiene los dos).
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
WF = RAIZ / ".github" / "workflows" / "reproc-chunked.yml"
PASO = "Unir con lo que main ya tiene y subir"

pytestmark = pytest.mark.skipif(
    not (shutil.which("bash") and shutil.which("git")), reason="falta bash o git")


def _git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          cwd=cwd, check=True, capture_output=True, text=True).stdout


def _rec(dt, vrp):
    return {"datetime_utc": dt, "sensor": "VIIRS_SNPP", "vrp_mw": vrp}


def _dump(path, records, updated="2026-10-01T00:00:00Z"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"volcano": "V", "updated": updated, "records": records}, f, indent=2)


ABRIL = [_rec("2026-04-02T05:00:00Z", 0.1)]
MAYO = [_rec("2026-05-03T05:00:00Z", 0.3)]
JUNIO = [_rec("2026-06-07T05:00:00Z", 0.5)]


def _script_del_paso():
    wf = yaml.safe_load(WF.read_text(encoding="utf-8"))
    pasos = [s for s in wf["jobs"]["merge"]["steps"] if s.get("name") == PASO]
    assert len(pasos) == 1, f"no encuentro el paso {PASO!r} en el job merge"
    return pasos[0]["run"]


@pytest.fixture
def repo(tmp_path):
    """origen bare con data/P/V.json (abril+mayo+junio) y el script de merge."""
    origen = tmp_path / "origen.git"
    semilla = tmp_path / "semilla"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origen))
    _git(tmp_path, "clone", "-q", str(origen), str(semilla))
    (semilla / "scripts").mkdir()
    shutil.copy(RAIZ / "scripts" / "merge_chunk_stores.py", semilla / "scripts")
    _dump(semilla / "data" / "P" / "V.json", ABRIL + MAYO + JUNIO)
    _git(semilla, "add", "-A")
    _git(semilla, "commit", "-q", "-m", "semilla")
    _git(semilla, "push", "-q", "origin", "HEAD:main")
    return tmp_path, origen, semilla


def _despacho(tmp_path, origen, nombre="job"):
    """Checkout del sha del despacho (como actions/checkout) + trozo de mayo."""
    job = tmp_path / nombre
    _git(tmp_path, "clone", "-q", str(origen), str(job))
    _dump(job / "chunks" / "chunk-V-2-2026-05-01_2026-05-31" / "V.json",
          [_rec("2026-05-03T05:00:00Z", 9.3)], updated="2026-10-20T00:00:00Z")
    return job


def _correr(tmp_path, job, hook=None, debe_fallar=False, hook_nombre="pre-push"):
    rt = tmp_path / "runner_temp"
    rt.mkdir(exist_ok=True)
    sh = rt / "paso.sh"
    sh.write_text(_script_del_paso(), encoding="utf-8", newline="\n")
    if hook:
        h = job / ".git" / "hooks" / hook_nombre
        h.write_text(hook, encoding="utf-8", newline="\n")
        h.chmod(0o755)
    env = dict(os.environ, PROFILE="P", VOLCANOES="V", VRP_START="2026-05-01",
               VRP_END="2026-05-31", RUNNER_TEMP=rt.as_posix(),
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    # `bash -e`: es lo que usa GitHub para un `run:` sin `shell:` declarado
    r = subprocess.run(["bash", "-e", sh.as_posix()], cwd=job, env=env,
                       capture_output=True, text=True, timeout=180)
    # PASO_CAYO / DEBIO_FALLAR: etiquetas que lee la bateria de mutaciones
    # (experiments/_s157_merge_conserva/) para separar una caida del paso de una
    # asercion sobre el resultado.
    if debe_fallar:
        assert r.returncode != 0, "DEBIO_FALLAR: " + r.stdout + r.stderr
    else:
        assert r.returncode == 0, "PASO_CAYO: " + r.stdout + r.stderr
    return r


def _main_de(origen, tmp_path):
    ver = tmp_path / "ver"
    if ver.exists():
        shutil.rmtree(ver)
    _git(tmp_path, "clone", "-q", str(origen), str(ver))
    st = json.loads((ver / "data" / "P" / "V.json").read_text(encoding="utf-8"))
    return [(r["datetime_utc"][:7], r["vrp_mw"]) for r in st["records"]]


def test_relanzar_un_trozo_no_borra_el_resto_del_historico(repo):
    tmp_path, origen, _ = repo
    job = _despacho(tmp_path, origen)

    _correr(tmp_path, job)

    assert _main_de(origen, tmp_path) == [("2026-04", 0.1), ("2026-05", 9.3), ("2026-06", 0.5)]


def test_la_base_sale_de_main_y_no_del_checkout_del_despacho(repo):
    tmp_path, origen, semilla = repo
    job = _despacho(tmp_path, origen)          # despacho con el main viejo
    # despues del despacho, otra corrida escribe julio en main
    _dump(semilla / "data" / "P" / "V.json",
          ABRIL + MAYO + JUNIO + [_rec("2026-07-01T05:00:00Z", 0.7)])
    _git(semilla, "commit", "-q", "-am", "julio")
    _git(semilla, "push", "-q", "origin", "HEAD:main")

    _correr(tmp_path, job)

    assert _main_de(origen, tmp_path) == [("2026-04", 0.1), ("2026-05", 9.3),
                                          ("2026-06", 0.5), ("2026-07", 0.7)]


@pytest.mark.parametrize("hook_nombre", ["post-checkout", "pre-push"])
def test_si_main_se_mueve_antes_del_push_se_relee_la_base(repo, hook_nombre):
    """Otra copia empuja agosto a main, SOLO la primera vez, en dos momentos:

    - post-checkout: justo despues del fetch, mientras se une. Nuestro push
      no es avance rapido; un `push -f` aca borraria agosto (mutacion Y3).
    - pre-push: justo al empujar. El servidor rechaza la actualizacion porque
      la referencia ya no esta donde el cliente creia, incluso con -f.

    En los dos casos el intento siguiente tiene que releer la base."""
    tmp_path, origen, semilla = repo
    job = _despacho(tmp_path, origen)
    marca = (tmp_path / "ya_empuje").as_posix()
    otra = (tmp_path / "otra").as_posix()
    hook = f"""#!/bin/sh
[ -f "{marca}" ] && exit 0
touch "{marca}"
git clone -q "{origen.as_posix()}" "{otra}"
cd "{otra}"
python - <<'PY'
import json
p = "data/P/V.json"
st = json.load(open(p, encoding="utf-8"))
st["records"].append({{"datetime_utc": "2026-08-01T05:00:00Z", "sensor": "VIIRS_SNPP", "vrp_mw": 0.8}})
json.dump(st, open(p, "w", encoding="utf-8"), indent=2)
PY
git -c user.name=t -c user.email=t@t commit -q -am agosto
git push -q origin HEAD:main
exit 0
"""
    r = _correr(tmp_path, job, hook=hook, hook_nombre=hook_nombre)

    assert "push rechazado" in r.stdout
    assert _main_de(origen, tmp_path) == [("2026-04", 0.1), ("2026-05", 9.3),
                                          ("2026-06", 0.5), ("2026-08", 0.8)]


def test_volcan_sin_trozos_deja_main_intacto(repo):
    tmp_path, origen, _ = repo
    job = tmp_path / "job"
    _git(tmp_path, "clone", "-q", str(origen), str(job))
    (job / "chunks").mkdir()

    r = _correr(tmp_path, job)

    assert "no changes" in r.stdout
    assert _main_de(origen, tmp_path) == [("2026-04", 0.1), ("2026-05", 0.3), ("2026-06", 0.5)]


def test_si_el_merge_falla_no_se_sube_nada(repo):
    """Un trozo de OTRO volcan con el nombre de V: el script se niega (base de
    otro volcan) y el paso tiene que fallar sin tocar main."""
    tmp_path, origen, _ = repo
    job = _despacho(tmp_path, origen)
    p = job / "chunks" / "chunk-V-2-2026-05-01_2026-05-31" / "V.json"
    st = json.loads(p.read_text(encoding="utf-8"))
    st["volcano"] = "OTRO"
    p.write_text(json.dumps(st), encoding="utf-8")

    _correr(tmp_path, job, debe_fallar=True)

    assert _main_de(origen, tmp_path) == [("2026-04", 0.1), ("2026-05", 0.3), ("2026-06", 0.5)]


def test_perfil_sin_archivo_en_main_se_crea_como_antes(repo):
    """Sin base (perfil o volcan nuevo), el resultado es lo que traen los trozos."""
    tmp_path, origen, _ = repo
    job = _despacho(tmp_path, origen)
    destino = job / "chunks" / "chunk-W-1-2026-05-01_2026-05-31" / "W.json"
    destino.parent.mkdir(parents=True)
    destino.write_text(json.dumps({"volcano": "W", "updated": "2026-10-20T00:00:00Z",
                                   "records": [_rec("2026-05-04T05:00:00Z", 4.4)]}), encoding="utf-8")
    env_vols = "V,W"

    rt = tmp_path / "runner_temp"
    rt.mkdir(exist_ok=True)
    sh = rt / "paso.sh"
    sh.write_text(_script_del_paso(), encoding="utf-8", newline="\n")
    env = dict(os.environ, PROFILE="P", VOLCANOES=env_vols, VRP_START="2026-05-01",
               VRP_END="2026-05-31", RUNNER_TEMP=rt.as_posix(),
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    r = subprocess.run(["bash", "-e", sh.as_posix()], cwd=job, env=env,
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, "PASO_CAYO: " + r.stdout + r.stderr

    ver = tmp_path / "ver_w"
    _git(tmp_path, "clone", "-q", str(origen), str(ver))
    w = json.loads((ver / "data" / "P" / "W.json").read_text(encoding="utf-8"))
    assert [(x["datetime_utc"], x["vrp_mw"]) for x in w["records"]] == [("2026-05-04T05:00:00Z", 4.4)]
    assert _main_de(origen, tmp_path) == [("2026-04", 0.1), ("2026-05", 9.3), ("2026-06", 0.5)]


def test_perfil_nuevo_sin_ningun_trozo_no_falla(tmp_path):
    """Ni carpeta del perfil en main ni trozos: `git add` no encuentra nada y el
    paso tiene que terminar en 'no changes', no caerse por el `bash -e`."""
    origen = tmp_path / "origen.git"
    semilla = tmp_path / "semilla"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origen))
    _git(tmp_path, "clone", "-q", str(origen), str(semilla))
    (semilla / "scripts").mkdir()
    shutil.copy(RAIZ / "scripts" / "merge_chunk_stores.py", semilla / "scripts")
    _git(semilla, "add", "-A")
    _git(semilla, "commit", "-q", "-m", "semilla")
    _git(semilla, "push", "-q", "origin", "HEAD:main")
    job = tmp_path / "job"
    _git(tmp_path, "clone", "-q", str(origen), str(job))
    (job / "chunks").mkdir()

    r = _correr(tmp_path, job)

    assert "no changes" in r.stdout
