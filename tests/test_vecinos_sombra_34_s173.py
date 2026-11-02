# -*- coding: utf-8 -*-
"""S173 (decisión 3 de tasks/BLOQUE_ARRANQUE_S173.md §b): la lectura de la sombra de los 34 separa las pasadas con un
alertado o el cúmulo a menos de 4 km de un volcán vecino de la grilla.

POR QUÉ. La vía suma todos los alertados de la grilla de 51 x 51 km; en 13 de los 34 hay otro volcán dentro
(experiments/_s172_sombra34/vecinos.yaml) y su calor se lee como del volcán propio. Lo aprobado: darlas aparte desde
el primer día. Las pruebas usan records sintéticos con la forma que escribe
pipeline/mirova_v750_codigo.py::procesar_grilla (`anomaly_pixels[].lat/lon`, `primary_cluster.centroid_lat/lon`),
porque todavía no hay records reales de la sombra de los 34.

Las dos preguntas del instrumento: la pasada a 3 km se marca y la de 5 km no (el instrumento puede dar los dos
resultados); y en un volcán sin vecino la salida de la revisión es idéntica byte a byte a la de una carpeta que no
activa la separación (la marca no cambia nada donde no aplica).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import vecinos_sombra_34 as VS  # noqa: E402
from revisar_sombra import revisar  # noqa: E402

pyproj = pytest.importorskip("pyproj")
GEOD = pyproj.Geod(ellps="WGS84")


def punto_a(lat, lon, km, az=90.0):
    lon2, lat2, _ = GEOD.fwd(lon, lat, az, km * 1000.0)
    return lat2, lon2


def rec(pixeles=(), centroide=None, dia="2026-10-20", hora="06:12"):
    r = {"datetime_utc": f"{dia}T{hora}:00Z", "sensor": "VIIRS_NOAA20_750", "via_codigo_mirova": True,
         "processed_utc": "2026-10-21T10:00:00Z", "regimen": {"perfil": "sombra_34", "codigo_sha": "abc"},
         "anomaly_pixels": [{"lat": la, "lon": lo, "dist_km": 1.0} for la, lo in pixeles],
         "primary_cluster": None}
    if centroide is not None:
        r["primary_cluster"] = {"centroid_lat": centroide[0], "centroid_lon": centroide[1], "vrp_mw": 0.3}
    return r


@pytest.fixture(scope="module")
def tabla():
    return VS.cargar_vecinos()


def test_la_lista_es_la_de_s172_trece_y_cuatro_con_tier_a(tabla):
    assert len(tabla) == 13
    assert {"Quetrupillan", "Michinmahuida", "AntillancaCasablanca", "Callaqui"} <= set(tabla)
    assert "Villarrica" in tabla["Quetrupillan"] and "Lanin" in tabla["Quetrupillan"]
    assert "Antuco" not in tabla


def test_posicion_del_vecino_es_el_crater_si_existe(tabla):
    # Villarrica trae vent_lat/vent_lon en volcanoes.yaml: se usa el cráter, no el punto nominal
    assert tabla["Quetrupillan"]["Villarrica"] == pytest.approx((-39.420227, -71.939876))


def test_pixel_a_3_km_del_vecino_se_marca(tabla):
    vla, vlo = tabla["Quetrupillan"]["Villarrica"]
    m = VS.marca_vecino(rec([punto_a(vla, vlo, 3.0)]), tabla["Quetrupillan"])
    assert m is not None and m["vecino"] == "Villarrica" and m["km"] == pytest.approx(3.0, abs=0.01)


def test_pixel_a_5_km_del_vecino_no_se_marca(tabla):
    vla, vlo = tabla["Quetrupillan"]["Villarrica"]
    assert VS.marca_vecino(rec([punto_a(vla, vlo, 5.0)]), tabla["Quetrupillan"]) is None


def test_el_cumulo_publicado_tambien_marca(tabla):
    vla, vlo = tabla["Michinmahuida"]["Chaiten"]
    assert VS.marca_vecino(rec(centroide=punto_a(vla, vlo, 2.0, az=0.0)), tabla["Michinmahuida"])["vecino"] == "Chaiten"


def test_volcan_sin_vecino_nunca_se_marca(tabla):
    vecinos = tabla.get("Antuco")
    assert vecinos is None
    # aunque el píxel caiga encima de un Tier A, Antuco no tiene vecinos en su grilla
    vla, vlo = tabla["Quetrupillan"]["Villarrica"]
    propias, cerca = VS.separar([rec([(vla, vlo)])], vecinos)
    assert len(propias) == 1 and cerca == []
    assert VS.linea_resumen([rec([(vla, vlo)])], vecinos) is None


def test_separar_no_toca_el_record_original(tabla):
    vla, vlo = tabla["Quetrupillan"]["Villarrica"]
    r = rec([punto_a(vla, vlo, 1.0)])
    propias, cerca = VS.separar([r], tabla["Quetrupillan"])
    assert propias == [] and cerca[0]["cerca_de_vecino"]["vecino"] == "Villarrica"
    assert "cerca_de_vecino" not in r


# ---------------------------------------------------------------------------------------- revisión del job
def _correr(tmp_path, carpeta, volcan, registros, extra=()):
    d = tmp_path / carpeta
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{volcan}.json").write_text(json.dumps({"records": registros}), encoding="utf-8")
    cob = tmp_path / "cobertura.json"
    cob.write_text(json.dumps({"plataformas": {}, "fallas": [], "incidencias": []}), encoding="utf-8")
    cmd = [sys.executable, str(ROOT / "scripts" / "revisar_sombra.py"), "--json", str(d / f"{volcan}.json"),
           "--log", str(tmp_path / "no_hay.log"), "--cobertura-json", str(cob), "--ini", "2026-10-14",
           "--fin", "2026-10-21", "--desde-utc", "2026-10-21T09:00:00Z", "--sha", "abc", *extra]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={"PYTHONIOENCODING": "utf-8",
                       **{k: v for k, v in __import__("os").environ.items() if k != "GITHUB_STEP_SUMMARY"}})
    return p.returncode, p.stdout


def test_revision_da_aparte_las_pasadas_cerca_del_vecino(tmp_path, tabla):
    vla, vlo = tabla["Quetrupillan"]["Villarrica"]
    regs = [rec([punto_a(vla, vlo, 3.0)]), rec([punto_a(vla, vlo, 5.0)], hora="07:40")]
    rc, out = _correr(tmp_path, "sombra_34", "Quetrupillan", regs)
    assert rc == 0, out
    assert "1 de 2 pasadas de la vía" in out and "propias: 1" in out and "Villarrica: 1, mínimo 3 km" in out


def test_control_la_marca_no_cambia_nada_de_un_volcan_sin_vecino(tmp_path, tabla):
    vla, vlo = tabla["Quetrupillan"]["Villarrica"]
    regs = [rec([(vla, vlo)]), rec([punto_a(vla, vlo, 5.0)], hora="07:40")]
    con = _correr(tmp_path / "a", "sombra_34", "Antuco", regs)
    sin = _correr(tmp_path / "b", "sombra_codigo_mirova", "Antuco", regs)
    assert con == sin and con[0] == 0


def test_control_los_conteos_del_volcan_con_vecino_no_cambian(tmp_path, tabla):
    """La separación agrega una línea y nada más: el resto del resumen y el veredicto son los de siempre."""
    vla, vlo = tabla["Quetrupillan"]["Villarrica"]
    regs = [rec([punto_a(vla, vlo, 3.0)]), rec([punto_a(vla, vlo, 5.0)], hora="07:40")]
    rc_con, con = _correr(tmp_path / "a", "sombra_34", "Quetrupillan", regs)
    rc_sin, sin = _correr(tmp_path / "b", "otra", "Quetrupillan", regs)
    assert rc_con == rc_sin == 0
    assert [ln for ln in con.splitlines() if "Vecinos en la grilla" not in ln] == sin.splitlines()
    assert sum("Vecinos en la grilla" in ln for ln in con.splitlines()) == 1


def test_lista_de_vecinos_ilegible_es_falla(tmp_path):
    malo = tmp_path / "vecinos_malo.yaml"
    malo.write_text("no: [es, la, lista", encoding="utf-8")
    rc, out = _correr(tmp_path, "sombra_34", "Quetrupillan", [rec()], extra=("--vecinos", str(malo)))
    assert rc == 1 and "lista de vecinos ilegible" in out


def test_revisar_sin_vecinos_es_el_de_siempre():
    """La firma nueva no cambia a los que llaman sin `vecinos` (la sombra de los 11, revisar_guardia_modis)."""
    regs = [rec()]
    a = revisar(regs, "", "2026-10-14", "2026-10-21", "2026-10-21T09:00:00Z", {}, sha="abc")
    b = revisar(regs, "", "2026-10-14", "2026-10-21", "2026-10-21T09:00:00Z", {}, sha="abc", vecinos=None)
    assert a == b and "Vecinos" not in a[1]
