# -*- coding: utf-8 -*-
"""S180 (2026-11-12): los 34 volcanes sin MIROVA en la página principal, el orden de las tarjetas, la capa «Píxeles
medidos» y la salida de los botones que ya no cambiaban nada.

POR QUÉ. Nicolás pidió que los 45 volcanes funcionaran como los 11 de MIROVA en la página principal, poder ordenar las
tarjetas, ver en el mapa los píxeles que el satélite midió (no sólo un punto por anomalía) y sacar los botones
desactualizados. Es un SDA en producción (Resolución CPLT N°372): mostrar los 34 no puede cambiar lo que se publica de
los 11, ni hacer pasar por anomalía de cumbre un foco a 20 km.

QUÉ FIJA, ejecutando en node las funciones reales de frontend/index.html:
1. `derivarClaseSombra` sólo completa `distance_class` vacío, con el criterio de mirovaEqVrp (centroide del cúmulo a
   5 km o menos), y sobre los datos reales de data/sombra_34 no cambia ningún valor de mirovaEqVrp (con o sin lejanas).
2. `ordenarVolcanes` ordena norte a sur, sur a norte, los 11 de MIROVA primero y por VRP, sin perder volcanes.
3. `pixelesMedidos` arma un cuadro por píxel con su lado por sensor, descarta píxeles sin posición y avisa del tope.
4. Los botones «Escala», «Píxeles» y «Magnitud» ya no están en ninguna vista y USE_F5_CORE queda fijo en las tres.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría si algo cambiara? Cada prueba de node tiene un control: un orden
roto, un lado de píxel cambiado o una clase sobrescrita dan otro resultado y la aserción lo nombra. (2) ¿Y si la
extracción muriera? `_fuente` lanza si no encuentra la función, y node falla con mensaje si el código no corre.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
INDEX = RAIZ / "frontend" / "index.html"
VISTAS = ["index.html", "diario.html", "mosaico.html"]

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


def _fuente(src, nombre):
    """Texto completo de `function nombre(...) {...}` o de `const nombre = ...;` de una línea."""
    m = re.search(r"(?<![A-Za-z0-9_])function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        m2 = re.search(r"^const " + re.escape(nombre) + r" = [^\n]*;", src, re.M)
        if not m2:
            raise AssertionError("no encontré " + nombre)
        return m2.group(0)
    i = src.index("{", m.end())
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[m.start():j + 1]
    raise AssertionError("llave sin cerrar en " + nombre)


def _node(tmp_path, nombres, cuerpo, datos):
    src = INDEX.read_text(encoding="utf-8")
    js = "\n".join(_fuente(src, n) for n in nombres) + "\nconst DATOS = " + json.dumps(datos) + ";\n" + cuerpo
    f = tmp_path / "t.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _sombra_real():
    """Records de data/sombra_34 en origin/main (el dato que lee la página). Skip si no hay remoto."""
    ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", "origin/main", "data/sombra_34/"], cwd=RAIZ,
                        capture_output=True, text=True)
    nombres = [x for x in ls.stdout.split() if x.endswith(".json")]
    if ls.returncode or not nombres:
        pytest.skip("sin data/sombra_34 en origin/main en este checkout")
    recs = []
    for n in nombres:
        raw = subprocess.run(["git", "show", "origin/main:" + n], cwd=RAIZ, capture_output=True).stdout
        recs += json.loads(raw).get("records", [])
    return recs


def test_clase_derivada_no_cambia_ningun_valor_publicado(tmp_path):
    recs = _sombra_real()
    assert len(recs) > 500 and all(r.get("distance_class") is None for r in recs), "la premisa: la sombra no trae clase"
    cuerpo = """
const RADIO_CUMBRE_SOMBRA_KM = 5;
const antes = DATOS.map(r => [mirovaEqVrp(r, 5, false), mirovaEqVrp(r, 5, true)]);
const copia = JSON.parse(JSON.stringify(DATOS));
derivarClaseSombra(copia);
const despues = copia.map(r => [mirovaEqVrp(r, 5, false), mirovaEqVrp(r, 5, true)]);
let distintos = 0; for (let i = 0; i < antes.length; i++) if (antes[i][0] !== despues[i][0] || antes[i][1] !== despues[i][1]) distintos++;
const conClase = copia.filter(r => r.distance_class);
const cumbre = conClase.filter(r => r.distance_class === "summit");
const cumbreBien = cumbre.every(r => (r.primary_cluster && r.primary_cluster.centroid_dist_km != null ? r.primary_cluster.centroid_dist_km : r.final_hotspot_dist_km) <= 5);
// control: una clase que ya venía no se toca
const fijo = [{ distance_class: "far", primary_cluster: { centroid_dist_km: 1, vrp_mw: 3 } }];
derivarClaseSombra(fijo);
const publicados = antes.filter(a => a[0] > 0).length;
process.stdout.write(JSON.stringify({ distintos, n: antes.length, conClase: conClase.length, cumbre: cumbre.length, cumbreBien, fijo: fijo[0].distance_class, publicados }));
"""
    out = _node(tmp_path, ["mirovaEqVrp", "derivarClaseSombra"], cuerpo, recs)
    assert out["distintos"] == 0, out
    assert out["conClase"] > 0 and out["cumbreBien"] and out["fijo"] == "far", out
    # cada detección publicada con «solo cráter» quedó rotulada cumbre (y viceversa no se exige: puede haber cumbre sin cúmulo)
    assert out["cumbre"] >= out["publicados"], out


def test_orden_de_las_tarjetas(tmp_path):
    vs = [{"name": "A", "lat": -20.0, "hasMirova": False}, {"name": "B", "lat": -40.0, "hasMirova": True},
          {"name": "C", "lat": -30.0, "hasMirova": True}, {"name": "D", "lat": -18.0, "hasMirova": False}]
    cuerpo = """
const vrp = { A: 0.5, B: 0, C: 12, D: 0 };
const o = k => ordenarVolcanes(DATOS, k, v => vrp[v.name]).map(v => v.name).join("");
process.stdout.write(JSON.stringify({ ns: o("ns"), sn: o("sn"), mirova: o("mirova"), vrp: o("vrp"), raro: o("xx"), intacta: DATOS.map(v => v.name).join("") }));
"""
    out = _node(tmp_path, ["ordenarVolcanes"], cuerpo, vs)
    assert out == {"ns": "DACB", "sn": "BCAD", "mirova": "CBDA", "vrp": "CADB", "raro": "DACB", "intacta": "ABCD"}, out


def test_pixeles_medidos(tmp_path):
    pix = [{"lat": -36.86, "lon": -71.38, "bt_k": 330, "dist_km": 0.5}, {"lat": None, "lon": -71.3},
           {"lat": -36.87, "lon": -71.37, "bt_k": 290, "dist_km": 1.1}]
    casos = [
        {"sensor": "VIIRS_NOAA20", "anomaly_pixels": pix, "primary_cluster": {"n_pixels": 2}},
        {"sensor": "VIIRS_NOAA21_750", "anomaly_pixels": pix[:1]},
        {"sensor": "MODIS_AQUA", "anomaly_pixels": [{"lat": -36.9, "lon": -71.4}] * 3005},
        {"sensor": "VIIRS_SNPP"},
    ]
    cuerpo = """
const TOPE_PIXELES_MEDIDOS = 3000;
process.stdout.write(JSON.stringify(DATOS.map(r => { const p = pixelesMedidos(r); return [p.n, p.pixeles.length, p.ladoKm, p.recortado, p.nCumulo]; })));
"""
    out = _node(tmp_path, ["sensorFootprintKm", "pixelesMedidos"], cuerpo, casos)
    assert out == [[2, 2, 0.375, False, 2], [1, 1, 0.75, False, None], [3005, 3000, 1.0, True, None],
                   [0, 0, 0.375, False, None]], out


def test_los_34_marcados_y_los_11_intactos(tmp_path):
    cuerpo = """
const VOLCANOES = VOLCANOES_ALL.map(v => v.hasMirova ? v : Object.assign({}, v, { fuente: "sombra_34", inner_radius_km: 5, radius_km: 25 }));
const once = VOLCANOES.filter(v => v.hasMirova), resto = VOLCANOES.filter(v => !v.hasMirova);
process.stdout.write(JSON.stringify({
  n: VOLCANOES.length, once: once.length, mismos: once.every(v => VOLCANOES_ALL.includes(v) && !v.fuente),
  resto: resto.length, marcados: resto.every(v => v.fuente === "sombra_34" && v.inner_radius_km === 5),
}));
"""
    src = INDEX.read_text(encoding="utf-8")
    m = re.search(r"const VOLCANOES_ALL = \[.*?\n\];", src, re.S)
    assert m, "no encontré VOLCANOES_ALL"
    assert "const VOLCANOES = VOLCANOES_ALL.map(v => v.hasMirova ? v : Object.assign({}, v, { fuente: \"sombra_34\", inner_radius_km: 5, radius_km: 25 }));" in src
    f = tmp_path / "v.js"
    f.write_text(m.group(0) + "\n" + cuerpo, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == {"n": 45, "once": 11, "mismos": True, "resto": 34, "marcados": True}


@pytest.mark.parametrize("vista", VISTAS)
def test_botones_que_ya_no_cambiaban_nada_salieron(vista):
    src = (RAIZ / "frontend" / vista).read_text(encoding="utf-8")
    for b in ('id="btn-mag', 'id="btn-all-pixels"', 'id="btn-primary-pixel"', 'id="btn-linear"', 'id="btn-log"'):
        assert b not in src, (vista, b)
    assert re.search(r"^const USE_F5_CORE = true;", src, re.M), vista
    # ninguna reasignación (antes las hacían los manejadores de los botones; main tenía 2 en index)
    assert not re.search(r"^\s*USE_F5_CORE\s*=[^=]", src, re.M), vista
    # el núcleo no recorta la vía: si eso cayera, fijar el modo dejaría de ser neutro para los datos nuevos
    assert "CambioDetector.esViaCodigoMirova(r)) return null" in src, vista


def test_el_mapa_dibuja_los_pixeles_medidos():
    src = INDEX.read_text(encoding="utf-8")
    assert 'capasCtl.addOverlay(medidosLayer, "Píxeles medidos (una pasada)");' in src
    assert "medir(hotspots.length ? hotspots[hotspots.length - 1] : null);" in src
    assert "const bbMed = window._mapRefs.medir ? window._mapRefs.medir(r) : null;" in src
