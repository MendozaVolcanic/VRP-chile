# -*- coding: utf-8 -*-
"""S132 — F5' núcleo en el pipeline (decisión #3 de AUDIT_S131 §4).

EL PROBLEMA. Lo que el operador lee en el dashboard para VIIRS375 no es `pc.vrp_mw`: es
`f5CoreMagnitude`, un algoritmo que hoy vive SÓLO en JavaScript, se recalcula en cada
carga de página y no queda escrito en ningún JSON. Medido en S131 sobre 1.609 pares por
pasada: el número mostrado da 0,68 contra MIROVA y `pc.vrp_mw` da 0,58, y coinciden entre
sí en el 5,7 % de los records. O sea, la cifra que se audita no es la cifra que se publica.

POR QUÉ IMPORTA PARA OVDAS. Un número que sólo existe mientras el navegador lo está
mirando no es trazable: no se puede reproducir a posteriori, no entra a las auditorías de
paridad y no aparece en la ficha del sistema. Es la regla A72 al revés — el display se
convirtió en algoritmo.

QUÉ ES F5' FÍSICAMENTE. MIROVA reporta la energía del CÚMULO del cráter, no la suma de
todo lo caliente de la escena. F5' reproduce eso: ancla en el píxel de máxima energía
dentro del cúmulo validado y suma los píxeles de su vecindad inmediata (0,75 km) más los
que están francamente tibios (BT ≥ 295 K, la cola térmica real del cuerpo caliente),
descartando el halo glaciar disperso. Calibrado sólo sobre VIIRS375
(docs/F5_CALIBRATION_S95.md); en MODIS y VIIRS750 el píxel grueso hace que el ancla salte
a fuentes lejanas, por eso ahí no se aplica.

ESTE MÓDULO NO CAMBIA NINGÚN NÚMERO: porta el mismo algoritmo a Python para poder
persistirlo. La prueba de que el port es fiel no son estos casos de juguete sino
`test_paridad_con_el_javascript`, que corre las DOS implementaciones sobre los records
reales del repo y exige coincidencia.
"""
import numpy as np
import pytest

from pipeline.f5_core import F5_BT_EXT_K, F5_R_CORE_KM, f5_core_vrp_mw


def _rec(pixels, pc_lat=-39.42, pc_lon=-71.93):
    return {"anomaly_pixels": pixels,
            "primary_cluster": {"centroid_lat": pc_lat, "centroid_lon": pc_lon}}


def test_sin_pixeles_no_recomputa():
    assert f5_core_vrp_mw(_rec([]), 5.0) is None
    assert f5_core_vrp_mw({"primary_cluster": {}}, 5.0) is None


def test_sin_centroide_de_cluster_no_recomputa():
    """Sin cúmulo validado no hay dónde anclar: se cae a pc.vrp_mw (return None)."""
    r = {"anomaly_pixels": [{"lat": -39.42, "lon": -71.93, "vrp_mw": 1.0}],
         "primary_cluster": {"centroid_lat": None, "centroid_lon": None}}
    assert f5_core_vrp_mw(r, 5.0) is None


def test_ningun_pixel_dentro_del_inner_no_recomputa():
    """Asimetría A46: anomaly_pixels puede no cubrir el cúmulo. Ahí NO se recomputa."""
    r = _rec([{"lat": -39.9, "lon": -72.5, "vrp_mw": 8.4}])  # ~60 km del centroide
    assert f5_core_vrp_mw(r, 5.0) is None


def test_suma_el_nucleo_y_descarta_el_halo_frio_lejano():
    r = _rec([
        {"lat": -39.420, "lon": -71.930, "vrp_mw": 2.0, "bt_k": 300.0},   # pico
        {"lat": -39.424, "lon": -71.930, "vrp_mw": 0.5, "bt_k": 280.0},   # ~0,44 km: entra
        {"lat": -39.460, "lon": -71.930, "vrp_mw": 0.3, "bt_k": 270.0},   # ~4,4 km, frío: fuera
    ])
    assert f5_core_vrp_mw(r, 5.0) == pytest.approx(2.5)


def test_el_pixel_tibio_lejano_entra_por_bt():
    """La cola térmica real del cuerpo caliente se conserva aunque esté lejos del pico."""
    r = _rec([
        {"lat": -39.420, "lon": -71.930, "vrp_mw": 2.0, "bt_k": 300.0},
        {"lat": -39.460, "lon": -71.930, "vrp_mw": 0.3, "bt_k": F5_BT_EXT_K},
    ])
    assert f5_core_vrp_mw(r, 5.0) == pytest.approx(2.3)


def test_el_pixel_pico_siempre_sobrevive():
    """Guard D2-safe: el núcleo nunca puede quedar en 0 si había señal."""
    r = _rec([{"lat": -39.420, "lon": -71.930, "vrp_mw": 1.5, "bt_k": 250.0}])
    assert f5_core_vrp_mw(r, 5.0) == pytest.approx(1.5)


def test_las_constantes_son_las_del_frontend():
    assert (F5_R_CORE_KM, F5_BT_EXT_K) == (0.75, 295.0)


# ---------------------------------------------------------------------------
# Control de instrumento: el port se prueba contra el original, no contra sí mismo.
# ---------------------------------------------------------------------------
import glob
import json
import os
import shutil
import subprocess
import tempfile

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

_JS_RUNNER = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');

// Se extraen del frontend las DOS funciones tal como están publicadas, sin reescribirlas:
// si alguien edita el JS y el port deja de coincidir, este test lo tiene que ver.
function extraer(nombre) {
  const i = src.indexOf('function ' + nombre + '(');
  if (i < 0) throw new Error('no encontré function ' + nombre);
  let j = src.indexOf('{', i), d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  throw new Error('no cerró ' + nombre);
}
const F5_R_CORE_KM = 0.75, F5_BT_EXT_K = 295.0;
eval(extraer('_havKm'));
eval(extraer('f5CoreMagnitude'));

const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
console.log(JSON.stringify(casos.map(c => f5CoreMagnitude(c.record, c.inner_km))));
"""


def _casos_reales(limite=4000):
    """Records VIIRS I-band de verdad, con su inner_radius_km real por volcán."""
    with open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8") as fp:
        vols = yaml.safe_load(fp)
    vols = vols.get("volcanoes", vols)
    inner = {}
    for v in (vols if isinstance(vols, list) else vols.values()):
        if isinstance(v, dict) and v.get("name"):
            inner[v["name"]] = float(v.get("inner_radius_km") or 10.0)

    casos = []
    from pipeline.f5_core import es_viirs_iband
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "mirova_equivalent", "*.json"))):
        nombre = os.path.splitext(os.path.basename(f))[0]
        ik = inner.get(nombre, 10.0)
        with open(f, encoding="utf-8") as fp:
            d = json.load(fp)
        for r in d.get("records", d):
            if es_viirs_iband(r.get("sensor")) and r.get("anomaly_pixels"):
                casos.append({"record": {"anomaly_pixels": r["anomaly_pixels"],
                                         "primary_cluster": r.get("primary_cluster")},
                              "inner_km": ik})
                if len(casos) >= limite:
                    return casos
    return casos


@pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")
def test_paridad_con_el_javascript():
    """El port Python devuelve EXACTAMENTE lo mismo que el JS publicado, sobre records reales.

    Es la única prueba que puede afirmar que persistir `f5_core_vrp_mw` no cambia la cifra
    que el operador viene viendo. Los casos de juguete de arriba prueban las ramas; esta
    prueba el algoritmo entero contra su original.
    """
    casos = _casos_reales()
    assert len(casos) > 200, f"muy pocos casos reales para que la prueba signifique algo: {len(casos)}"

    tmp = tempfile.mkdtemp()
    try:
        runner = os.path.join(tmp, "runner.js")
        datos = os.path.join(tmp, "casos.json")
        with open(runner, "w", encoding="utf-8") as fp:
            fp.write(_JS_RUNNER)
        with open(datos, "w", encoding="utf-8") as fp:
            json.dump(casos, fp)
        out = subprocess.run(
            ["node", runner, os.path.join(ROOT, "frontend", "index.html"), datos],
            capture_output=True, text=True, timeout=300)
        assert out.returncode == 0, f"el runner de node falló: {out.stderr[-800:]}"
        js = json.loads(out.stdout)

        py = [f5_core_vrp_mw(c["record"], c["inner_km"]) for c in casos]
        assert len(js) == len(py)

        discrepancias = []
        for i, (a, b) in enumerate(zip(js, py)):
            if (a is None) != (b is None):
                discrepancias.append((i, a, b))
            elif a is not None and abs(a - b) > 1e-9:
                discrepancias.append((i, a, b))
        assert not discrepancias, (
            f"{len(discrepancias)} de {len(casos)} records difieren entre el JS y el port; "
            f"primeras: {discrepancias[:5]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Persistencia: que el número publicado exista en el JSON.
# ---------------------------------------------------------------------------
def _record_viirs_iband():
    return {
        "datetime_utc": "2026-05-12 03:30",
        "sensor": "VIIRS_NOAA20",
        "vrp_mw": 3.0,
        "hotspot_dist_km": 0.4,
        "primary_cluster": {"n_pixels": 3, "vrp_mw": 3.0,
                            "centroid_lat": -39.420, "centroid_lon": -71.930,
                            "centroid_dist_km": 0.4},
        "anomaly_pixels": [
            {"lat": -39.420, "lon": -71.930, "dist_km": 0.4, "vrp_mw": 2.0, "bt_k": 300.0},
            {"lat": -39.424, "lon": -71.930, "dist_km": 0.5, "vrp_mw": 0.5, "bt_k": 280.0},
            {"lat": -39.470, "lon": -71.930, "dist_km": 5.0, "vrp_mw": 0.5, "bt_k": 265.0},
        ],
        "product_version": "standard",
    }


def test_store_persiste_f5_core_para_viirs_iband(tmp_path, monkeypatch):
    """El número que el dashboard publica queda escrito en el JSON, no sólo en el navegador."""
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = _record_viirs_iband()
    store.append_record("TestVolcano", r, inner_radius_km=5.0)
    # Núcleo = píxel pico (2,0) + vecino a 0,44 km (0,5); el de 5,5 km y 265 K queda fuera.
    assert r["f5_core_vrp_mw"] == pytest.approx(2.5)


def test_store_no_persiste_f5_core_en_modis(tmp_path, monkeypatch):
    """F5' se calibró sólo sobre I-band: en MODIS el píxel de 1 km hace saltar el ancla."""
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = _record_viirs_iband()
    r["sensor"] = "MODIS_TERRA"
    store.append_record("TestVolcano", r, inner_radius_km=5.0)
    assert r.get("f5_core_vrp_mw") is None


def test_store_no_persiste_f5_core_en_viirs_750(tmp_path, monkeypatch):
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = _record_viirs_iband()
    r["sensor"] = "VIIRS_NOAA20_750"
    store.append_record("TestVolcano", r, inner_radius_km=5.0)
    assert r.get("f5_core_vrp_mw") is None


def test_store_sin_inner_radius_no_computa(tmp_path, monkeypatch):
    """Legacy intacto: sin inner_radius_km el campo no aparece (mismo criterio que geo_class)."""
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = _record_viirs_iband()
    store.append_record("TestVolcano", r)
    assert r.get("f5_core_vrp_mw") is None
