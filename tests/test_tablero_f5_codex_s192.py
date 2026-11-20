# -*- coding: utf-8 -*-
"""S192 (2026-11-20): auditoría Codex ronda 2, frente 5, hallazgos F5-105 y F5-101. Lo que ve el operador.

POR QUÉ, F5-105 (gravedad 3). `frontend/diario.html` leía la referencia de MIROVA con `loadMirovaRef`, que ante un 404,
un error de red o un JSON roto devolvía `[]`. Un arreglo vacío es lo mismo que «MIROVA no alertó», así que la tarjeta
decía «MIROVA: 0 alertas» sin ninguna señal de falla. Hoy los 11 Tier A tienen alertas de MIROVA en 90 días: una falla
de carga los dejaba a todos en cero, y un cero de MIROVA se lee como volcán tranquilo. Lo mismo con nuestros datos
(`loadVolcanoData` ya devolvía null, pero `computeStats` lo convertía en «0 det. nuestras»). Ahora la falla es null de
punta a punta y la tarjeta dice «no cargó».

POR QUÉ, F5-101 (gravedad 2, fundido con R1). Desde S180 la tarjeta de index.html dice «Sin anomalía» cuando el volcán
tiene pasadas medidas y ninguna anomalía publicada en 48 h; «Sin datos» queda para cuando no hay ninguna pasada medida.
El cambio no se replicó (regla S92): mosaico.html y la barra «Estado actual» de index.html seguían diciendo «Sin datos»
a un volcán vigilado y tranquilo (2.728 de 6.270 tarjetas-instante, 43,5 %, del 2026-10-01 al 11-17, medido por el
verificador de la auditoría). Una escena con `diag_codigo_mirova.motivo_vacio` no es pasada medida (S183): no cuenta.

Sólo cambia qué se muestra: ningún record, valor ni detección cambia.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código mal? Cada prueba trae su control (la carga buena da
arreglo y cero, el volcán sin pasadas sigue «Sin datos», la escena inválida no cuenta). (2) ¿Y si la extracción muriera?
`_fuente` lanza si no encuentra la función, y node falla con mensaje si el código no corre.
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
    """Texto completo de `function nombre(...) {...}` (también `async function`). Copia de la de
    test_tablero_escenas_invalidas_s183.py."""
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


# ── F5-105: diario ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_diario_una_falla_de_carga_de_mirova_no_es_un_arreglo_vacio(tmp_path):
    previo = """
const BASE_PATH = "";
let MODO = "ok";
global.fetch = async (u) => {
  if (MODO === "red") throw new Error("sin red");
  if (MODO === "404") return { ok: false, json: async () => ({}) };
  if (MODO === "roto") return { ok: true, json: async () => { throw new Error("JSON roto"); } };
  if (MODO === "vacio") return { ok: true, json: async () => ({ records: [] }) };
  return { ok: true, json: async () => ({ records: [{ datetime_utc: "2026-11-10 05:00", sensor: "MODIS", VRP_MW: "3.2" }] }) };
};
"""
    cuerpo = """
(async () => {
  const out = {};
  for (const m of ["ok", "vacio", "404", "red", "roto"]) {
    MODO = m;
    const r = await loadMirovaRef({ name: "Lascar", csv: "Lascar" });
    out[m] = r === null ? null : r.length;
  }
  process.stdout.write(JSON.stringify(out));
})();
"""
    out = _node(tmp_path, "diario.html", ["loadMirovaRef"], cuerpo, previo)
    # control: una carga buena da arreglo (con o sin alertas); la falla, null
    assert out == {"ok": 1, "vacio": 0, "404": None, "red": None, "roto": None}, out


def test_diario_computeStats_distingue_falla_de_cero(tmp_path):
    previo = """
const applyS38Filter = x => x;
const enPeriodo = () => true;
const eqVrpDisplay = r => r.vrp_mw || 0;
"""
    cuerpo = """
const json = { records: [{ datetime_utc: "2026-11-10 05:00", vrp_mw: 2 }, { datetime_utc: "2026-11-11 05:00", vrp_mw: 0 }] };
const mir = [{ dt: "2026-11-10 05:00", vrp: 3, dist: 0.5 }];
const k = s => [s.n_det_us, s.n_det_mirova];
process.stdout.write(JSON.stringify({
  ambos: k(computeStats(json, mir, "Lascar")),
  vacios: k(computeStats({ records: [] }, [], "Lascar")),
  falla_mirova: k(computeStats(json, null, "Lascar")),
  falla_nuestra: k(computeStats(null, mir, "Lascar")),
}));
"""
    out = _node(tmp_path, "diario.html", ["parseUtcMs", "computeStats"], cuerpo, previo)
    assert out == {"ambos": [1, 1], "vacios": [0, 0], "falla_mirova": [1, None], "falla_nuestra": [None, 1]}, out


def test_diario_el_texto_del_conteo_dice_no_cargo(tmp_path):
    cuerpo = "process.stdout.write(JSON.stringify([0, 7, null, undefined].map(textoConteo)));"
    out = _node(tmp_path, "diario.html", ["textoConteo"], cuerpo)
    assert out[0] == {"texto": "0", "falla": False} and out[1] == {"texto": "7", "falla": False}, out
    assert out[2]["falla"] and out[3]["falla"] and out[2]["texto"] == "no cargó", out


def test_diario_el_aviso_sin_grafico_no_confunde_falla_con_silencio(tmp_path):
    cuerpo = """
process.stdout.write(JSON.stringify([
  mensajeSinGrafico({ records: [] }, [], "90 días"),
  mensajeSinGrafico({ records: [] }, null, "90 días"),
  mensajeSinGrafico(null, [], "90 días"),
  mensajeSinGrafico(null, null, "90 días"),
]));
"""
    out = _node(tmp_path, "diario.html", ["mensajeSinGrafico"], cuerpo)
    assert out[0] == "Sin detecciones nuestras ni alertas MIROVA en 90 días", out
    bajo = [x.lower() for x in out]
    assert "no cargó" in bajo[1] and "MIROVA" in out[1] and "nuestros datos" not in out[1], out
    assert "Sin detecciones" not in out[1] and "no es un período sin alertas" in bajo[1], out
    assert "no cargó" in bajo[2] and "nuestros datos" in out[2] and "MIROVA" not in out[2], out
    assert "no cargó" in bajo[3] and "MIROVA" in out[3] and "nuestros datos" in out[3], out


def test_diario_la_tarjeta_usa_las_funciones():
    src = (FRONT / "diario.html").read_text(encoding="utf-8")
    tarjeta = _fuente(src, "renderCard")
    assert "textoConteo(stats.n_det_us)" in tarjeta and "textoConteo(stats.n_det_mirova)" in tarjeta
    assert "mensajeSinGrafico(jsonData, mirovaForVolc," in tarjeta
    assert "String(stats.n_det_mirova)" not in tarjeta and "String(stats.n_det_us)" not in tarjeta
    # buildDatasets no revienta con la referencia caída
    assert "buildDatasets(jsonData, mirovaForVolc || []," in tarjeta
    assert "if (!r.ok) return null;" in _fuente(src, "loadMirovaRef")


# ── F5-101: mosaico e index ─────────────────────────────────────────────────────────────────────────────────────────

ND = {"key": "nd", "label": "Sin datos"}
BAJO = {"key": "low", "label": "Bajo"}


@pytest.mark.parametrize("pagina", ["index.html", "mosaico.html"])
def test_rotulo_nivel_sin_anomalia_solo_con_pasada_medida(tmp_path, pagina):
    cuerpo = ("const ND = " + json.dumps(ND) + ", BAJO = " + json.dumps(BAJO) + ";\n"
              "process.stdout.write(JSON.stringify([rotuloNivel(ND, '2026-11-19 05:00'), rotuloNivel(ND, null), "
              "rotuloNivel(BAJO, '2026-11-19 05:00'), rotuloNivel(BAJO, null)]));")
    out = _node(tmp_path, pagina, ["rotuloNivel"], cuerpo)
    assert out == ["Sin anomalía", "Sin datos", "Bajo", "Bajo"], out


def test_mosaico_la_escena_sin_medir_no_es_pasada(tmp_path):
    cuerpo = """
const ok = { datetime_utc: "2026-11-18 05:00" };
const inval = { datetime_utc: "2026-11-19 05:00", diag_codigo_mirova: { motivo_vacio: "escena_invalida" } };
const nulo = { datetime_utc: "2026-11-19 06:00", diag_codigo_mirova: { motivo_vacio: null } };
process.stdout.write(JSON.stringify([lastEventTime([ok, inval]), lastEventTime([inval]), lastEventTime([ok, nulo]),
  lastEventTime([])]));
"""
    out = _node(tmp_path, "mosaico.html", ["lastEventTime"], cuerpo)
    assert out == ["2026-11-18 05:00", None, "2026-11-19 06:00", None], out


def test_mosaico_la_tarjeta_usa_el_rotulo():
    src = (FRONT / "mosaico.html").read_text(encoding="utf-8")
    tarjeta = _fuente(src, "renderMosaico")
    assert "rotuloNivel(level, lastEventTime(records))" in tarjeta
    assert "textContent: level.label" not in tarjeta


def test_index_tarjeta_y_barra_usan_el_rotulo(tmp_path):
    src = (FRONT / "index.html").read_text(encoding="utf-8")
    assert "badge.textContent = rotuloNivel(level, lastTime);" in _fuente(src, "buildCards")
    barra = _fuente(src, "buildAlertSummary")
    assert re.search(r"\bnivelEstado\(", barra), "la barra no usa nivelEstado"
    assert '"Sin anomalía"' in barra and "counts.na" in barra


def test_index_nivel_de_la_barra(tmp_path):
    previo = """
const getLevel = v => (v > 0 ? { key: "low" } : { key: "nd" });
const latestVRP = (recs) => recs.reduce((a, r) => Math.max(a, r.vrp || 0), 0);
"""
    cuerpo = """
const ok = { datetime_utc: "2026-11-18 05:00", vrp: 0 };
const det = { datetime_utc: "2026-11-18 05:00", vrp: 4 };
const inval = { datetime_utc: "2026-11-19 05:00", vrp: 0, diag_codigo_mirova: { motivo_vacio: "escena_invalida" } };
process.stdout.write(JSON.stringify([nivelEstado([ok], false, 5), nivelEstado([], false, 5),
  nivelEstado([inval], false, 5), nivelEstado([det], false, 5)]));
"""
    out = _node(tmp_path, "index.html", ["escenaSinDato", "lastEventTime", "nivelEstado"], cuerpo, previo)
    assert out == ["na", "nd", "nd", "low"], out


def test_index_contar_separa_sin_anomalia_de_sin_datos(tmp_path):
    vol = [{"name": "Lascar"}, {"name": "Llaima"}, {"name": "Isluga"},
           {"name": "Antuco", "fuente": "sombra_34"}, {"name": "Hudson", "fuente": "sombra_34"}]
    niveles = {"Lascar": "na", "Llaima": "nd", "Isluga": "low", "Antuco": "na", "Hudson": "mod"}
    cuerpo = ("const DATOS = " + json.dumps(vol) + ", N = " + json.dumps(niveles) + ";\n"
              "process.stdout.write(JSON.stringify(contarEstadoTablero(DATOS, v => N[v.name])));")
    out = _node(tmp_path, "index.html", ["esPreliminar", "contarEstadoTablero"], cuerpo)
    assert out["principales"] == {"high": 0, "mod": 0, "low": 1, "vlow": 0, "na": 1, "nd": 1}, out
    # un preliminar «sin anomalía» no cuenta como «con anomalía» (control: el de nivel moderado sí)
    assert out["preliminares"] == {"con_anomalia": 1, "total": 2}, out
