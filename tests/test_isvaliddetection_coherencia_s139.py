# -*- coding: utf-8 -*-
"""S139 (decision S138-H): `isValidDetection` no puede declarar deteccion un record cuya magnitud
publicada es cero.

POR QUE. El dashboard tiene dos predicados del mismo concepto. `mirovaEqVrp` publica la magnitud
del cumulo del crater (`primary_cluster.vrp_mw`); `isValidDetection` decidia "hay deteccion" con
`vrp_mw > 0` **o** `triggered_test1`. Un record con el cumulo en 0,0 MW y el Test 1 disparado
contaba como deteccion en el contador del crater, en las pastillas de sensor y en la corroboracion
con MIROVA, mientras el grafico lo mostraba en cero para la misma pasada (familia A46, hallazgo P5
del verificador S138). Medido S139 con el predicado literal: 2.219 records summit en esa situacion;
en noches de volcan, 161 noches quedaban "detectadas" solo por pasadas sin energia y MIROVA publico
alerta en 1 de ellas.

QUE VIGILA. (1) Sobre todos los records reales, en index.html y mosaico.html: si hay
`primary_cluster`, valida implica `primary_cluster.vrp_mw > 0`. (2) Controles: el caso del
verificador (Tupungatito 2026-08-21 05:30 VIIRS_SNPP_750, cumulo en 0,0 MW) es invalido; un cumulo
con energia es valido; un record legacy sin cumulo con Test 1 sigue siendo valido (no se toca la
rama pre-S27). (3) Las dos vistas dan exactamente lo mismo (regla S92 L5).

Se ejecuta la funcion tal como esta publicada, extraida del HTML con node, no una reescritura.
"""
import glob
import json
import os
import shutil
import subprocess
import tempfile

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VISTAS = ["index.html", "mosaico.html"]

_JS_RUNNER = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function extraer(nombre) {
  const i = src.indexOf('function ' + nombre + '(');
  if (i < 0) throw new Error('no encontre function ' + nombre);
  let j = src.indexOf('{', i), d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  throw new Error('no cerro ' + nombre);
}
eval(extraer('isValidDetection'));
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
console.log(JSON.stringify(casos.map(r => isValidDetection(r))));
"""


def _correr(vista, casos):
    tmp = tempfile.mkdtemp()
    try:
        runner = os.path.join(tmp, "runner.js")
        datos = os.path.join(tmp, "casos.json")
        with open(runner, "w", encoding="utf-8") as fp:
            fp.write(_JS_RUNNER)
        with open(datos, "w", encoding="utf-8") as fp:
            json.dump(casos, fp)
        out = subprocess.run(["node", runner, os.path.join(ROOT, "frontend", vista), datos],
                             capture_output=True, text=True, timeout=300)
        assert out.returncode == 0, f"node fallo en {vista}: {out.stderr[-800:]}"
        return json.loads(out.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _records_reales():
    casos, claves = [], []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "mirova_equivalent", "*.json"))):
        nombre = os.path.splitext(os.path.basename(f))[0]
        with open(f, encoding="utf-8") as fp:
            d = json.load(fp)
        for r in d.get("records", d):
            pc = r.get("primary_cluster")
            casos.append({"vrp_mw": r.get("vrp_mw"), "triggered_test1": r.get("triggered_test1"),
                          "primary_cluster": ({"vrp_mw": pc.get("vrp_mw")} if pc else None)})
            claves.append((nombre, r.get("datetime_utc"), r.get("sensor")))
    return casos, claves


node = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


@node
@pytest.mark.parametrize("vista", VISTAS)
def test_valida_implica_cumulo_con_energia_en_records_reales(vista):
    casos, claves = _records_reales()
    assert len(casos) > 10000, f"muy pocos records para que la prueba signifique algo: {len(casos)}"
    # Control de instrumento: el defecto tiene que existir en los datos, si no el test no mide nada.
    expuestos = [i for i, c in enumerate(casos)
                 if c["primary_cluster"] and (c["primary_cluster"]["vrp_mw"] or 0) <= 0
                 and c["triggered_test1"] is True]
    assert len(expuestos) > 100, f"sin sustrato: solo {len(expuestos)} records con cumulo en 0 y Test 1"
    res = _correr(vista, casos)
    malos = [claves[i] for i, (c, v) in enumerate(zip(casos, res))
             if v and c["primary_cluster"] and (c["primary_cluster"]["vrp_mw"] or 0) <= 0]
    assert not malos, (f"{vista}: {len(malos)} records declarados deteccion con el cumulo en 0 MW; "
                       f"p.ej. {malos[:3]}")


@node
@pytest.mark.parametrize("vista", VISTAS)
def test_controles(vista):
    cumulo_cero_test1 = {"vrp_mw": 0.0, "triggered_test1": True, "primary_cluster": {"vrp_mw": 0.0}}
    con_energia = {"vrp_mw": 0.3, "triggered_test1": False, "primary_cluster": {"vrp_mw": 0.3}}
    legacy_test1 = {"vrp_mw": 0.0, "triggered_test1": True, "primary_cluster": None}
    legacy_vrp = {"vrp_mw": 1.2, "triggered_test1": False}
    nada = {"vrp_mw": 0.0, "triggered_test1": False, "primary_cluster": None}
    assert _correr(vista, [cumulo_cero_test1, con_energia, legacy_test1, legacy_vrp, nada]) == \
        [False, True, True, True, False]


def test_el_caso_de_referencia_sigue_en_los_datos():
    """Ancla real del control sintetico: Chaiten 2025-03-16 05:24 VIIRS_SNPP_750, summit, cumulo de
    2 pixeles en 0,0 MW y Test 1 disparado. OJO: el caso que citaba el verificador S138 para P5
    (Tupungatito 2026-08-21 05:30 V750) tiene `triggered_test1 = False` y `vrp_mw = 0`, asi que el
    dashboard ya no lo contaba: es un ejemplo de D25 (crater en 0 MW), no de P5. Verificado S139."""
    with open(os.path.join(ROOT, "data", "mirova_equivalent", "Chaiten.json"), encoding="utf-8") as fp:
        recs = json.load(fp)["records"]
    r = [x for x in recs if x["datetime_utc"] == "2025-03-16 05:24" and x["sensor"] == "VIIRS_SNPP_750"]
    assert r, "no esta el record Chaiten 2025-03-16 05:24 VIIRS_SNPP_750"
    assert r[0]["distance_class"] == "summit"
    assert (r[0]["primary_cluster"]["vrp_mw"] or 0) == 0 and r[0].get("triggered_test1") is True


@node
def test_las_dos_vistas_coinciden():
    casos, _ = _records_reales()
    assert _correr("index.html", casos) == _correr("mosaico.html", casos)
