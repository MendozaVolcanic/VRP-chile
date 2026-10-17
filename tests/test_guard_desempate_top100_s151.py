# -*- coding: utf-8 -*-
"""S151, tarea 1.22 (D-16 b): el top-100 de píxeles anómalos y el hotspot de escena no pueden
depender de la CPU del runner.

POR QUÉ. En MODIS la temperatura de brillo sale de enteros escalados del L1B, así que toma valores
discretos; con el área de píxel fija de nadir (A66) y el fondo del anillo como un solo número, dos
píxeles con el mismo entero dan un VRP por píxel IDÉNTICO bit a bit. Esos empates son frecuentes
(cientos de píxeles a 244,39 K en Copahue). El corte top-100 se hacía con
`np.argsort(-per_pixel_vrp_mw)[:100]`, cuyo algoritmo por defecto no es estable y que numpy despacha
a una ruta SIMD distinta según la CPU (AVX2, AVX-512 o ninguna). Resultado medido: el mismo commit
en dos runners da otro hotspot de escena en unos pocos records por volcán, y con él otro rescate por
cúmulo y otro `vrp_mw` (Llaima Terra 2026-10-06 01:45, 4,281 contra 3,568 MW). Detalle en el cuerpo
del PR de la tarea 1.22 y en `experiments/_s151_desempate_top100/`.

El arreglo ordena por una clave que depende sólo de la identidad del píxel: VRP descendente y, en
empate, fila y columna ascendentes. Esa clave define una permutación ÚNICA, así que cualquier
implementación correcta de cualquier CPU da la misma.

CONTROL DE INSTRUMENTO (A110, A116). Los tests que comparan dos subprocesos (con y sin las
extensiones SIMD despachables) sólo valen si ese cambio de ruta SIMD puede mover el orden de los
empates en esta máquina. `test_el_instrumento_ve_la_dependencia_de_cpu` lo comprueba sobre
`np.argsort` crudo; si la máquina no tiene extensiones despachables, los tests de CPU se saltan
diciéndolo, en vez de pasar por la razón equivocada.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")


def _extensiones_despachables():
    """Extensiones SIMD que numpy usa en esta CPU por encima de su línea base."""
    try:
        from numpy._core import _multiarray_umath as m  # numpy >= 2
    except ImportError:  # pragma: no cover, numpy 1.x
        from numpy.core import _multiarray_umath as m
    return [f for f in m.__cpu_dispatch__ if m.__cpu_features__.get(f)]


def _correr(codigo, sin_simd):
    env = dict(os.environ)
    env["VRP_PROFILE"] = "mirova_equivalent"
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("NPY_DISABLE_CPU_FEATURES", None)
    if sin_simd:
        env["NPY_DISABLE_CPU_FEATURES"] = " ".join(_extensiones_despachables())
    out = subprocess.run([sys.executable, "-c", codigo], cwd=str(ROOT), env=env,
                         capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert out.returncode == 0, out.stderr[-3000:]
    # la última línea es el JSON; antes puede venir el banner del perfil
    return json.loads(out.stdout.strip().splitlines()[-1])


_ARREGLO_CON_EMPATES = (
    "import numpy as np, json\n"
    "rng = np.random.default_rng(0)\n"
    "v = rng.choice([0.3931, 0.5242, 0.5949, 0.9173, 2.0313], size=418).astype(np.float64)\n"
)


def _requiere_simd():
    if not _extensiones_despachables():
        pytest.skip("esta CPU no tiene extensiones SIMD despachables: no hay dos rutas que comparar")


def test_el_instrumento_ve_la_dependencia_de_cpu():
    """Control positivo: con empates exactos, `np.argsort` por defecto da OTRO orden al apagar las
    extensiones SIMD. Si esto deja de fallar en alguna máquina, los tests de abajo pierden poder
    ahí, y este test lo dice."""
    _requiere_simd()
    codigo = _ARREGLO_CON_EMPATES + "print(json.dumps(np.argsort(-v)[:100].tolist()))"
    con, sin = _correr(codigo, False), _correr(codigo, True)
    if con == sin:
        pytest.skip("en esta CPU las dos rutas SIMD coinciden en este arreglo: instrumento sin poder")
    assert con != sin


def test_orden_canonico_vrp_descendente_y_luego_fila_columna():
    from pipeline.anomaly_pixels import orden_vrp_descendente

    vrps = np.array([1.0, 2.0, 1.0, 2.0, np.nan, 0.5, 2.0])
    rows = np.array([5, 3, 1, 3, 0, 0, 1])
    cols = np.array([0, 9, 7, 2, 0, 0, 4])
    orden = orden_vrp_descendente(vrps, rows, cols)
    pares = [(vrps[i], rows[i], cols[i]) for i in orden]
    # 2.0 en (1,4), (3,2), (3,9); luego 1.0 en (1,7), (5,0); luego 0.5; NaN al final
    assert [(r, c) for _, r, c in pares] == [(1, 4), (3, 2), (3, 9), (1, 7), (5, 0), (0, 0), (0, 0)]
    assert np.isnan(pares[-1][0])


def test_el_orden_no_depende_del_orden_de_entrada():
    """La clave es la identidad del píxel, no su posición en el arreglo: barajar la entrada no
    cambia qué píxeles quedan en el top-100 ni en qué orden."""
    from pipeline.anomaly_pixels import orden_vrp_descendente

    rng = np.random.default_rng(7)
    n = 418
    vrps = rng.choice([0.3931, 0.5242, 0.5949, 0.9173, 2.0313], size=n)
    rows, cols = np.divmod(rng.permutation(61 * 61)[:n], 61)
    ref = [(rows[i], cols[i]) for i in orden_vrp_descendente(vrps, rows, cols)[:100]]
    for semilla in range(20):
        p = np.random.default_rng(semilla).permutation(n)
        got = [(rows[p][i], cols[p][i]) for i in orden_vrp_descendente(vrps[p], rows[p], cols[p])[:100]]
        assert got == ref


def test_build_anomaly_pixels_no_depende_de_la_cpu():
    """`build_anomaly_pixels` (camino del Test 1 de los tres sensores) sobre una grilla con
    empates exactos da la misma lista con y sin extensiones SIMD."""
    _requiere_simd()
    codigo = (
        "import numpy as np, json\n"
        "from pipeline.anomaly_pixels import build_anomaly_pixels\n"
        "rng = np.random.default_rng(3)\n"
        "n = 61\n"
        "vrp = np.where(rng.random((n, n)) < 0.15,"
        " rng.choice([0.3931, 0.5242, 0.9173], size=(n, n)), 0.0)\n"
        "y, x = np.mgrid[0:n, 0:n].astype(float)\n"
        "ap = build_anomaly_pixels(vrp, y, x, np.hypot(y - 30, x - 30), 250.0 + vrp)\n"
        "print(json.dumps([(p['lat'], p['lon']) for p in ap]))\n"
    )
    con, sin = _correr(codigo, False), _correr(codigo, True)
    assert len(con) == 100
    assert con == sin


_ESCENA_MODIS = r'''
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pipeline.process_modis as pm

LAT0, LON0 = -39.42, -71.94
# Malla de 0,5 km (el área por píxel sigue siendo la de nadir, 1 km2, A66): con más píxeles en el
# ROI la fracción de píxeles calientes baja y la desviación del dNTI no tapa a la retícula.
n = 121
d = (np.arange(n) - n // 2) * 0.5
y, x = np.meshgrid(d, d, indexing="ij")
lat = (LAT0 + y / 111.0).astype(np.float32)
lon = (LON0 + x / (111.0 * np.cos(np.radians(LAT0)))).astype(np.float32)
r = np.hypot(y, x)
rng = np.random.default_rng(11)
bt21 = 255.0 + np.clip(r, 0, 12) * 1.2 + rng.normal(0, 0.15, r.shape)
bt31 = bt21 - 1.0 + rng.normal(0, 0.15, r.shape)
# Retícula de píxeles calientes AISLADOS con la misma temperatura exacta (como un mismo entero del
# L1B): cada uno es anómalo contra sus 8 vecinos y todos empatan en VRP por píxel. Son más de 100,
# así que el corte top-100 cae dentro de un empate, y el máximo también es un empate.
hot = np.zeros(r.shape, bool)
hot[::6, ::6] = True
hot &= r <= 20
bt21[hot] = 290.0
bt31[hot] = 258.0

def rad(bt, lam):
    return (pm.C1 / (lam ** 5 * (np.exp(pm.C2 / (lam * bt)) - 1))).astype(np.float32)

data = {"band21": rad(bt21, pm.BAND21_LAMBDA), "band22": rad(bt21, pm.BAND21_LAMBDA),
        "band31": rad(bt31, 11.03), "lat": lat, "lon": lon}
with patch.object(pm, "read_modis_l1b", return_value=data):
    rec = pm.calculate_vrp(
        hdf_path=Path("MOD021KM.A2026200.0300.061.hdf"), geo_path=Path("MOD03.sintetico.hdf"),
        volcano_lat=LAT0, volcano_lon=LON0, radius_km=25.0,
        vent_lat=LAT0, vent_lon=LON0, inner_radius_km=25.0)
ap = rec.get("anomaly_pixels") or []
print(json.dumps({
    "n": rec.get("n_anomalous_pixels"),
    "hotspot": [rec.get("hotspot_lat"), rec.get("hotspot_lon")],
    "pix": [(p["lat"], p["lon"]) for p in ap],
    "vrp_top": [p["vrp_mw"] for p in ap[:2]],
    "vrp_borde": [p["vrp_mw"] for p in ap[-1:]],
}))
'''


def test_modis_top100_y_hotspot_no_dependen_de_la_cpu():
    """Cadena MODIS completa (`calculate_vrp`) sobre una escena sintética con más de 100 píxeles
    empatados: mismo hotspot de escena y mismo top-100, en el mismo orden, con y sin SIMD."""
    _requiere_simd()
    con, sin = _correr(_ESCENA_MODIS, False), _correr(_ESCENA_MODIS, True)
    # Control de la escena: si deja de tener empates en el máximo y en el borde, el test no mide
    # lo que dice medir.
    assert con["n"] > 100, con["n"]
    assert len(con["pix"]) == 100
    assert con["vrp_top"][0] == con["vrp_top"][1], "la escena ya no empata en el máximo"
    assert con["vrp_borde"][0] == con["vrp_top"][0], "la escena ya no empata en el borde del top-100"
    assert con["hotspot"] == sin["hotspot"]
    assert con["pix"] == sin["pix"]


_SITIOS = {
    "pipeline/process_modis.py": "per_pixel_vrp_mw",
    "pipeline/process_viirs.py": "per_pixel_vrp_mw",
    "pipeline/process_viirs_mod.py": "per_pixel_vrp_mw",
}


@pytest.mark.parametrize("archivo", sorted(_SITIOS))
def test_los_procesadores_ordenan_con_el_desempate_explicito(archivo):
    """Guard de las copias en línea (A102): ningún procesador vuelve a ordenar el VRP por píxel con
    un `argsort` sin desempate, y los tres pasan por `orden_vrp_descendente`. Frontera de palabra
    en la búsqueda (A92)."""
    src = (ROOT / archivo).read_text(encoding="utf-8")
    assert not re.search(r"(?<![A-Za-z0-9_])np\.argsort\s*\(\s*-\s*" + _SITIOS[archivo], src)
    assert re.search(r"(?<![A-Za-z0-9_])orden_vrp_descendente\s*\(\s*" + _SITIOS[archivo]
                     + r"\s*,\s*hot_rows\s*,\s*hot_cols\s*\)", src)


def test_build_anomaly_pixels_usa_el_desempate_explicito():
    src = (ROOT / "pipeline" / "anomaly_pixels.py").read_text(encoding="utf-8")
    cuerpo = src.split("def build_anomaly_pixels", 1)[1]
    assert not re.search(r"(?<![A-Za-z0-9_])np\.argsort\s*\(", cuerpo)
    assert re.search(r"(?<![A-Za-z0-9_])orden_vrp_descendente\s*\(", cuerpo)
