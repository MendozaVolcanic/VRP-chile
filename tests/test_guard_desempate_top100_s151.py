# -*- coding: utf-8 -*-
"""S151, tarea 1.22 (D-16 b): el orden de los empates que decide el top-100 de píxeles anómalos
y el hotspot de escena tiene que ser determinista, no depender de la CPU del runner. (La
aritmética sí sigue dependiendo de la CPU en el último dígito, por ejemplo `diag_mu_deti`: este
arreglo no la toca.)

POR QUÉ. En MODIS la temperatura de brillo sale de enteros escalados del L1B, así que toma valores
discretos; con el área de píxel fija de nadir (A66) y el fondo del anillo como un solo número, dos
píxeles con el mismo entero dan un VRP por píxel IDÉNTICO bit a bit. Esos empates son frecuentes
(cientos de píxeles a 244,39 K en Copahue). El corte top-100 se hacía con
`np.argsort(-per_pixel_vrp_mw)[:100]`, cuyo algoritmo por defecto no es estable y que numpy despacha
a una ruta SIMD distinta según la CPU (AVX2, AVX-512 o ninguna). Resultado medido: el mismo commit
en dos runners da otro top-100 y, en unos pocos records, otro hotspot de escena, y con él otro
rescate por cúmulo y otro `vrp_mw` (consistente con Llaima Terra 2026-10-06 01:45, 4,281 contra
3,568 MW; la lista que probaría el empate en ese record no se guarda). Detalle en el cuerpo
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


_ESCENA_MODIS = r"""
import json, os
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pipeline.process_modis as pm

if os.environ.get("ORDEN_VIEJO") == "1":
    # Control: la expresion de antes del arreglo, para medir si la escena discrimina.
    pm.orden_vrp_descendente = lambda v, r, c: np.argsort(-np.asarray(v))

LAT0, LON0 = -39.42, -71.94
# Malla de 0,5 km (el area por pixel sigue siendo la de nadir, 1 km2, A66): con mas pixeles en el
# ROI la fraccion de pixeles calientes baja y la desviacion del dNTI no tapa a la reticula.
n = 121
d = (np.arange(n) - n // 2) * 0.5
y, x = np.meshgrid(d, d, indexing="ij")
lat = (LAT0 + y / 111.0).astype(np.float32)
lon = (LON0 + x / (111.0 * np.cos(np.radians(LAT0)))).astype(np.float32)
r = np.hypot(y, x)


def rad(bt, lam):
    return (pm.C1 / (lam ** 5 * (np.exp(pm.C2 / (lam * bt)) - 1))).astype(np.float32)


salida = []
for semilla in range(6):
    rng = np.random.default_rng(11)
    bt21 = 255.0 + np.clip(r, 0, 12) * 1.2 + rng.normal(0, 0.15, r.shape)
    bt31 = bt21 - 1.0 + rng.normal(0, 0.15, r.shape)
    # Reticula de pixeles calientes AISLADOS con la misma temperatura exacta (como un mismo entero
    # del L1B): cada uno es anomalo contra sus 8 vecinos y todos empatan en VRP por pixel. Son mas de
    # 100, asi que el corte top-100 cae dentro de un empate. Ademas, 4 de ellos (elegidos con la
    # semilla) estan mas calientes y empatan entre si en el maximo: es el empate que decide el
    # hotspot. Con un maximo empatado entre MUCHOS (toda la reticula) el argsort por defecto deja
    # casi siempre el mismo primero en las dos rutas SIMD, y el hotspot no discriminaba.
    hot = np.zeros(r.shape, bool)
    hot[::6, ::6] = True
    hot &= r <= 20
    bt21[hot] = 290.0
    bt31[hot] = 258.0
    filas, cols = np.nonzero(hot)
    k = np.random.default_rng(semilla).choice(filas.size, 4, replace=False)
    bt21[filas[k], cols[k]] = 300.0
    bt31[filas[k], cols[k]] = 260.0
    data = {"band21": rad(bt21, pm.BAND21_LAMBDA), "band22": rad(bt21, pm.BAND21_LAMBDA),
            "band31": rad(bt31, 11.03), "lat": lat, "lon": lon}
    with patch.object(pm, "read_modis_l1b", return_value=data):
        rec = pm.calculate_vrp(
            hdf_path=Path("MOD021KM.A2026200.0300.061.hdf"), geo_path=Path("MOD03.sintetico.hdf"),
            volcano_lat=LAT0, volcano_lon=LON0, radius_km=25.0,
            vent_lat=LAT0, vent_lon=LON0, inner_radius_km=25.0)
    ap = rec.get("anomaly_pixels") or []
    salida.append({
        "n": rec.get("n_anomalous_pixels"),
        "hotspot": [rec.get("hotspot_lat"), rec.get("hotspot_lon")],
        "pix": [(p["lat"], p["lon"]) for p in ap],
        "vrp": [p["vrp_mw"] for p in ap],
    })
print(json.dumps(salida))
"""


def _correr_escena(sin_simd, orden_viejo):
    os.environ["ORDEN_VIEJO"] = "1" if orden_viejo else "0"
    try:
        return _correr(_ESCENA_MODIS, sin_simd)
    finally:
        os.environ.pop("ORDEN_VIEJO", None)


def _control_de_escena(res):
    """Si la escena deja de tener empates en el maximo y en el borde, el test no mide lo que dice."""
    for e in res:
        assert e["n"] > 100, e["n"]
        assert len(e["pix"]) == 100
        assert e["vrp"][0] == e["vrp"][1] == e["vrp"][3] > e["vrp"][4], "ya no hay 4 empatados en el maximo"
        assert e["vrp"][-1] == e["vrp"][4], "ya no hay empate en el borde del top-100"


def test_control_con_el_orden_viejo_la_escena_discrimina_hotspot_y_top100():
    """Control positivo (A110): con la expresion de antes del arreglo, apagar las extensiones SIMD
    cambia el top-100 y, en alguna de las 6 escenas, el hotspot de escena. Si el hotspot no cambia
    en ninguna, la asercion del hotspot del test de abajo no tiene poder en esta CPU y se dice."""
    _requiere_simd()
    con, sin = _correr_escena(False, True), _correr_escena(True, True)
    _control_de_escena(con)
    assert any(a["pix"] != b["pix"] for a, b in zip(con, sin)), "el orden viejo no cambio el top-100"
    if not any(a["hotspot"] != b["hotspot"] for a, b in zip(con, sin)):
        pytest.skip("en esta CPU el orden viejo no cambia el hotspot en ninguna escena: sin poder")


def test_modis_top100_y_hotspot_no_dependen_de_la_cpu():
    """Cadena MODIS completa (`calculate_vrp`) sobre 6 escenas sinteticas con empates en el maximo
    y en el borde: mismo hotspot de escena y mismo top-100, en el mismo orden, con y sin SIMD."""
    _requiere_simd()
    con, sin = _correr_escena(False, False), _correr_escena(True, False)
    _control_de_escena(con)
    assert [e["hotspot"] for e in con] == [e["hotspot"] for e in sin]
    assert [e["pix"] for e in con] == [e["pix"] for e in sin]


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


_REGRID = r"""
import hashlib, json, os
import numpy as np
import pipeline.regrid as rg

if os.environ.get("ORDEN_VIEJO") == "1":
    # Control: argsort sin `kind`, como antes del arreglo.
    class _NP:
        def __getattr__(self, nombre):
            return getattr(np, nombre)

        @staticmethod
        def argsort(a, **_):
            return np.argsort(a)

    rg.np = _NP()

LAT0, LON0 = -39.42, -71.94
m = 80
d = (np.arange(m) - m // 2) * 0.5
y, x = np.meshgrid(d, d, indexing="ij")
lat = LAT0 + y / 111.0
lon = LON0 + x / (111.0 * np.cos(np.radians(LAT0)))
# Cada posicion aparece DOS veces (filas duplicadas, como el solape del bow tie): la distancia al
# centro de la celda empata exacto y el valor distingue cual muestra gano la celda.
lat2, lon2 = np.repeat(lat, 2, axis=0), np.repeat(lon, 2, axis=0)
valor = np.repeat(np.arange(m, dtype=float)[:, None], m, axis=1)
valor = np.stack([valor, valor + 0.5], axis=1).reshape(2 * m, m)
out = rg.regrid_to_utm(lat2, lon2, {"b": valor}, LAT0, LON0, cell_km=1.0, half_km=15.0)
g = out["b"]
print(json.dumps({"md5": hashlib.md5(np.nan_to_num(g, nan=-1).tobytes()).hexdigest(),
                  "frac_segunda": float(np.nanmean((g % 1) == 0.5))}))
"""


def _correr_regrid(sin_simd, orden_viejo):
    os.environ["ORDEN_VIEJO"] = "1" if orden_viejo else "0"
    try:
        return _correr(_REGRID, sin_simd)
    finally:
        os.environ.pop("ORDEN_VIEJO", None)


def test_regrid_desempate_determinista_entre_muestras_duplicadas():
    """`pipeline/regrid.py` (A102, hoy inerte: ENABLE_UTM_REGRID apagado). Entre dos muestras
    a la misma distancia del centro de su celda gana siempre la de mayor indice del swath (orden
    estable, escritura de peor a mejor), con y sin SIMD."""
    nuevo = _correr_regrid(False, False)
    assert nuevo["frac_segunda"] == 1.0, nuevo
    if _extensiones_despachables():
        assert _correr_regrid(True, False) == nuevo


def test_control_regrid_con_el_orden_viejo_depende_de_la_cpu():
    _requiere_simd()
    con, sin = _correr_regrid(False, True), _correr_regrid(True, True)
    if con == sin:
        pytest.skip("en esta CPU el orden viejo del regrid coincide en las dos rutas: sin poder")
    assert con != sin


def test_regrid_usa_orden_estable():
    src = (ROOT / "pipeline" / "regrid.py").read_text(encoding="utf-8")
    assert re.search(r"(?<![A-Za-z0-9_])np\.argsort\s*\(\s*-d2\[validas\]\s*,\s*kind\s*=\s*\"stable\"\s*\)", src)
