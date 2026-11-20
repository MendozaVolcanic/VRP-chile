# -*- coding: utf-8 -*-
"""S192 (2026-11-20): auditoría Codex ronda 2, frente 5, hallazgos F5-114 y F5-V201. Rótulos que inducen a error.

POR QUÉ, F5-114 (gravedad 2, fundido con R6). Un foco débil (Llaima, Copahue, Villarrica) aparece en una pasada
nocturna y no en las siguientes, por nubes, mirada oblicua o porque el calor bajó. La tarjeta de mosaico sigue mostrando
ese número, con su color de clase, hasta 48 h, porque `latestVRP` devuelve la última DETECCIÓN publicada, no la última
pasada. La introducción de mosaico decía «el número de cada tarjeta es la última pasada de 48 h» y el title del nivel del
detalle en index decía «La tarjeta muestra la última pasada (48 h)». El verificador de la auditoría midió que el número
sale de la última pasada medida sólo en el 5,5 % de 69.014 tarjetas-hora (2026-03-01 en adelante); en el 45,8 % sale de
una pasada anterior (mediana por volcán de 1,9 a 24,7 h antes, máximo 47,9 h). Se corrige el texto, no el número: la
última detección es lo que el operador necesita ver, y el pie de la tarjeta ya dice «Últ. detección».

POR QUÉ, F5-V201 (gravedad 2). Nuestra réplica mide sólo de noche (MIR nocturno), así que una alerta diurna de MIROVA
nunca puede tener par nuestro. La tarjeta de diario ponía «301 det. nuestras · MIROVA: 353 alertas» en Nevados de
Chillán, que sugiere 52 silencios nuestros, cuando las nocturnas de MIROVA en la ventana eran 277. El total de MIROVA se
deja igual (decisión S151, que vigila tests/test_rebuild_mirova_diurnas_s151.py: computeStats no lee la marca diurna); se
agrega cuántas son de noche, que es lo comparable.

Sólo cambia qué se muestra: ningún record, valor ni detección cambia.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código mal? La prueba de latestVRP tiene control (sin la pasada
posterior, el número sí es de la última pasada); la del desglose, control sin diurnas (no agrega paréntesis) y control de
que el total no cambia. (2) ¿Y si la extracción muriera? `_fuente` lanza si no encuentra la función, y node falla con
mensaje si el código no corre.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
FRONT = RAIZ / "frontend"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


def _fuente(src, nombre):
    """Texto completo de `function nombre(...) {...}`. Copia de la de test_tablero_f5_codex_s192.py."""
    m = re.search(r"(?<![A-Za-z0-9_])(?:async\s+)?function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        raise AssertionError("no encontré " + nombre)
    i = src.index(") {", m.end()) + 2
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[m.start():j + 1]
    raise AssertionError("llave sin cerrar en " + nombre)


def _node(tmp_path, pagina, nombres, cuerpo, previo=""):
    src = (FRONT / pagina).read_text(encoding="utf-8")
    js = previo + "\n" + "\n".join(_fuente(src, n) for n in nombres) + "\n" + cuerpo
    f = tmp_path / "t.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# ── F5-114 ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_mosaico_el_numero_es_la_ultima_deteccion_no_la_ultima_pasada(tmp_path):
    """Instrumento: fija el hecho que el texto debe describir."""
    previo = """
const isSummitDetection = () => true;
const isValidDetection = r => (r.vrp_mw || 0) > 0;
const eqVrpDisplay = r => r.vrp_mw || 0;
const hace = h => new Date(Date.now() - h * 3600000).toISOString().slice(0, 16).replace("T", " ");
"""
    cuerpo = """
const det = { datetime_utc: hace(20), vrp_mw: 3.1, sensor: "VIIRS_NOAA20" };
const tranquila = { datetime_utc: hace(2), vrp_mw: 0, sensor: "VIIRS_NOAA21" };
const a = latestVRP([det, tranquila], 5), b = latestVRP([det], 5);
process.stdout.write(JSON.stringify({ con_pasada_posterior: [a.max, a.ts === det.datetime_utc],
  control: [b.max, b.ts === det.datetime_utc] }));
"""
    out = _node(tmp_path, "mosaico.html", ["parseUtcMs", "latestVRP"], cuerpo, previo)
    # el número es el de hace 20 h aunque hubo una pasada medida hace 2 h: es la última detección
    assert out == {"con_pasada_posterior": [3.1, True], "control": [3.1, True]}, out


def test_los_textos_no_llaman_ultima_pasada_a_la_ultima_deteccion():
    mos = (FRONT / "mosaico.html").read_text(encoding="utf-8")
    idx = (FRONT / "index.html").read_text(encoding="utf-8")
    assert "es la última pasada de 48 h" not in mos
    assert re.search(r"el número de cada tarjeta es la última detección publicada en 48 h", mos), "intro de mosaico"
    detalle = _fuente(idx, "renderDetail")
    assert "La tarjeta muestra la última pasada (48 h)" not in detalle
    assert "La tarjeta muestra la última detección publicada (48 h)" in detalle


# ── F5-V201 ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_diario_desglose_nocturno_de_mirova(tmp_path):
    cuerpo = """
const m = (dia) => ({ dt: "2026-11-10 05:00", vrp: 2, dia });
const chillan = [].concat(Array(277).fill(0).map(() => m(false)), Array(76).fill(0).map(() => m(true)));
process.stdout.write(JSON.stringify({
  chillan: desgloseMirova(chillan),
  sin_diurnas: desgloseMirova([m(false), m(false)]),
  vacio: desgloseMirova([]),
  falla: desgloseMirova(null),
}));
"""
    out = _node(tmp_path, "diario.html", ["desgloseMirova"], cuerpo)
    assert out["chillan"] == {"nocturnas": 277, "diurnas": 76}, out
    assert out["sin_diurnas"] == {"nocturnas": 2, "diurnas": 0}, out
    assert out["vacio"] == {"nocturnas": 0, "diurnas": 0} and out["falla"] is None, out


def test_diario_el_total_de_mirova_no_cambia_y_la_lista_viaja(tmp_path):
    previo = """
const applyS38Filter = x => x;
const enPeriodo = () => true;
const eqVrpDisplay = r => r.vrp_mw || 0;
"""
    cuerpo = """
const mir = [{ dt: "2026-11-10 05:00", vrp: 3, dia: false }, { dt: "2026-11-10 15:00", vrp: 4, dia: true },
             { dt: "2026-11-11 05:00", vrp: 0, dia: false }];
const s = computeStats({ records: [] }, mir, "X");
process.stdout.write(JSON.stringify({ total: s.n_det_mirova, lista: s.mirova_ventana.length,
  desglose: desgloseMirova(s.mirova_ventana), falla: computeStats({ records: [] }, null, "X").mirova_ventana }));
"""
    out = _node(tmp_path, "diario.html", ["parseUtcMs", "computeStats", "desgloseMirova"], cuerpo, previo)
    assert out == {"total": 2, "lista": 2, "desglose": {"nocturnas": 1, "diurnas": 1}, "falla": None}, out


def test_diario_texto_del_desglose(tmp_path):
    cuerpo = """
process.stdout.write(JSON.stringify([textoNocturnas({ nocturnas: 277, diurnas: 76 }),
  textoNocturnas({ nocturnas: 5, diurnas: 0 }), textoNocturnas(null)]));
"""
    out = _node(tmp_path, "diario.html", ["textoNocturnas"], cuerpo)
    assert out[0]["texto"] == " (277 de noche)" and "76" in out[0]["title"] and "277" in out[0]["title"], out
    assert out[1] is None and out[2] is None, out


def test_diario_la_tarjeta_usa_el_desglose():
    src = (FRONT / "diario.html").read_text(encoding="utf-8")
    tarjeta = _fuente(src, "renderCard")
    assert "textoNocturnas(desgloseMirova(stats.mirova_ventana))" in tarjeta
