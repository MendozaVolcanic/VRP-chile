# -*- coding: utf-8 -*-
"""S173 (decisión 4 de tasks/BLOQUE_ARRANQUE_S173.md §b): las sombras y guardias no van al sitio público ni disparan
el deploy de GitHub Pages.

POR QUÉ. Nadie las lee como operador (el tablero lee data/mirova_equivalent, data/mirova, data/experimental_v2 y
data/alerts) y cada carpeta nueva achica el margen de 1 GB del sitio. La lista NO se fija aquí: sale de los perfiles
pipeline/profiles/sombra*.yaml y guardia*.yaml (su `output.data_subdir`), así que una sombra nueva que no se agregue
al deploy pone esta prueba en rojo (A117: se vigila la relación, no un valor).

CÓMO. (1) En `on.push.paths`, cada carpeta lleva un patrón negado `!data/<carpeta>/**` DESPUÉS de `data/**` (docs de
GitHub: un negativo que calza después de un positivo excluye la ruta), y se simula ese orden sobre rutas de ejemplo.
(2) En el paso que arma el sitio, se ejecuta de verdad la copia y el borrado (con bash, sobre una carpeta temporal)
y se mira qué quedó (A116: el efecto, no el texto). Los nombres se buscan con frontera de palabra (A92).
Control: data/mirova_equivalent sigue copiándose y disparando.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "pages-deploy.yml"
PERFILES = ROOT / "pipeline" / "profiles"


def carpetas_de_sombras():
    out = set()
    for p in sorted(PERFILES.glob("*.yaml")):
        if p.stem.startswith(("sombra", "guardia")):
            sub = ((yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("output") or {}).get("data_subdir")
            assert sub, f"{p.name} no declara output.data_subdir"
            out.add(sub)
    return sorted(out)


def _wf():
    return yaml.safe_load(WF.read_text(encoding="utf-8"))


def _paths():
    return list(_wf()["on"]["push"]["paths"])


def _glob_re(patron):
    r = re.escape(patron).replace(r"\*\*", "\0").replace(r"\*", "[^/]*").replace("\0", ".*")
    return re.compile("^" + r + "$")


def dispara(ruta, patrones):
    """Semántica de on.push.paths: se recorren en orden; un positivo que calza incluye, un negativo que calza excluye."""
    incluida = False
    for p in patrones:
        neg = p.startswith("!")
        if _glob_re(p[1:] if neg else p).match(ruta):
            incluida = not neg
    return incluida


def _paso_del_sitio():
    pasos = _wf()["jobs"]["build"]["steps"]
    return next(s["run"] for s in pasos if s.get("name") == "Prepare Pages artifact")


def test_la_lista_derivada_trae_las_tres_de_hoy():
    # ancla de cordura: si el glob dejara de encontrar perfiles, las demás pruebas pasarían en vacío
    assert {"sombra_34", "sombra_codigo_mirova", "guardia_k_modis"} <= set(carpetas_de_sombras())


@pytest.mark.parametrize("sub", carpetas_de_sombras())
def test_cada_sombra_no_dispara_el_deploy(sub):
    pats = _paths()
    assert "data/**" in pats
    neg = f"!data/{sub}/**"
    assert neg in pats and pats.index(neg) > pats.index("data/**"), f"{neg} falta o va antes de data/**"
    assert not dispara(f"data/{sub}/Antuco.json", pats)


@pytest.mark.parametrize("sub", carpetas_de_sombras())
def test_cada_sombra_se_borra_del_sitio_en_el_texto(sub):
    run = _paso_del_sitio()
    lineas = run.splitlines()
    i_cp = next(i for i, ln in enumerate(lineas) if ln.strip() == "cp -r data _site/data")
    token = re.compile(r"(?<![\w/])_site/data/" + re.escape(sub) + r"(?![\w])")
    assert any(ln.strip().startswith("rm -rf ") and token.search(ln) for ln in lineas[i_cp + 1:]), sub


def test_control_mirova_equivalent_sigue_disparando_y_copiandose():
    pats = _paths()
    for ruta in ("data/mirova_equivalent/Villarrica.json", "data/mirova/x.json", "data/experimental_v2/Lascar.json",
                 "frontend/index.html"):
        assert dispara(ruta, pats), ruta
    assert not any(p.startswith("!") and "mirova_equivalent" in p for p in pats)
    run = _paso_del_sitio()
    assert not re.search(r"rm -rf[^\n]*(?<![\w/])_site/data/mirova_equivalent(?![\w])", run)
    assert not re.search(r"rm -rf[^\n]*(?<![\w/])_site/data(?![\w/])", run)   # no borra data entero


@pytest.mark.skipif(shutil.which("bash") is None, reason="sin bash")
def test_el_efecto_del_paso_real_sobre_una_carpeta_temporal(tmp_path):
    """Ejecuta las líneas `cp -r data _site/data` y los `rm -rf _site/data/...` del paso, tal cual, y mira qué quedó."""
    subs = carpetas_de_sombras()
    for d in ["mirova_equivalent", "mirova", "experimental_v2", *subs]:
        (tmp_path / "data" / d).mkdir(parents=True)
        (tmp_path / "data" / d / "x.json").write_text("{}", encoding="utf-8")
    lineas = [ln.strip() for ln in _paso_del_sitio().splitlines()]
    script = "set -e\nmkdir -p _site\n" + "\n".join(
        ln for ln in lineas if ln == "cp -r data _site/data" or ln.startswith("rm -rf _site/data/")) + "\n"
    subprocess.run(["bash", "-c", script], cwd=tmp_path, check=True)
    quedan = {p.name for p in (tmp_path / "_site" / "data").iterdir()}
    assert {"mirova_equivalent", "mirova", "experimental_v2"} <= quedan
    assert not (set(subs) & quedan), set(subs) & quedan
