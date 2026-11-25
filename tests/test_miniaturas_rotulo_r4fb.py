# -*- coding: utf-8 -*-
"""Auditoría Codex ronda 4, frente B (S199): el pie de cada tarjeta de «Últimas 10 pasadas» dice la verdad.

POR QUÉ. La imagen de la tarjeta pinta en rojo todos los alertados de la pasada, y la potencia que se publica es la del
tablero (eqVrp), que con «Solo cráter» vale 0 para una detección lejana. El pie leía ese 0 como «Sin anomalía» al lado de
los píxeles rojos (R4FB-106: 6 de 120 tarjetas reales al 2026-11-24, VIIRS 375 de Isluga, Láscar, Lastarria y
Planchón-Peteroa); tres motivos de escena no medida (fondo_no_estimado, crater_no_evaluado, sin_radiancia_valida) también
salían «Sin anomalía» (R4FB-104); la tarjeta no llevaba las marcas de cráter no medido ni de fondo no estimado que el
resto del tablero ya muestra (R4FB-105); y si el JSON del volcán no cargaba, el panel caía a la potencia del índice
(suma de todos los alertados, lejanas incluidas) y mostraba esas 6 lejanas como «VRP = 0,10 a 1,58 MW» (R4FB-V202).
Detalle: D:\\codex-vrp\\_salida\\ronda4\\fb_r4\\INFORME.md y D:\\codex-vrp\\_salida\\ronda4\\fb_r4_verificacion\\VEREDICTO.md.

QUÉ FIJA, ejecutando con node los archivos reales frontend/crater_no_medido.js y frontend/miniaturas.js en un DOM mínimo,
con las opciones de Miniaturas.montar extraídas del texto real de frontend/index.html (recordDe, vrpDe, radioKm):
(1) las 6 entradas reales de R4FB-106 dicen «Anomalía lejana, X km» y no «Sin anomalía»; control: con «Incluir lejanas»
    muestran su potencia, y una pasada sin alertados sigue diciendo «Sin anomalía».
(2) los cinco motivos de escena no medida dicen «No medida: <motivo>»; control: sin motivo, «Sin anomalía».
(3) las marcas de crater_no_medido.js llegan al pie; control: un record limpio no lleva marca.
(4) con el store vacío las 6 lejanas dicen «Sin dato del tablero» y ninguna muestra potencia.
(5) una lejana con alertados también en la cumbre lleva la marca de cumbre.js (caso real: Láscar 2026-11-24 05:06,
    que en la imagen tiene un rojo sobre el cráter); control: una lejana sin alertados en la cumbre no la lleva.
La eqVrp del tablero se sustituye por una mínima (lejana con «Solo cráter» = 0): su lógica real la fijan otras pruebas
(test_tope_publicacion_s190.py, test_isvaliddetection_coherencia_s139.py); aquí se prueba qué hace el panel con su 0.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código de antes? Sí: con miniaturas.js e index.html de origin/main
anterior a este cambio, (1), (2) y (3) dan «Sin anomalía» y (4) da «VRP = ...» (comprobado al escribirla). (2) ¿Y si la
carga muriera? _node exige returncode 0, cada caso exige el número de tarjetas esperado y las opciones se extraen del
texto real: si la línea de montar cambia de forma, la prueba cae.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
FRONT = RAIZ / "frontend"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="el panel se prueba con node")

# Las 6 entradas reales de R4FB-106 (data/miniaturas/<volcán>/indice.json de main al 2026-11-24; claves en
# D:\codex-vrp\_salida\ronda4\_insumos\claves_fb.csv). Se copian aquí porque el índice rota cada pasada.
LEJANAS = [
    ("Isluga", "VIIRS_NOAA20", "2026-11-21 05:18", 29.211, 4, 1.358, 5, "29 km"),
    ("Lascar", "VIIRS_NOAA21", "2026-11-24 05:06", 12.27, 5, 1.1, 5, "12 km"),
    ("Lastarria", "VIIRS_NOAA20", "2026-11-22 05:00", 15.026, 3, 1.579, 3, "15 km"),
    ("Lastarria", "VIIRS_NOAA21", "2026-11-22 05:48", 23.212, 3, 0.505, 3, "23 km"),
    ("PlanchonPeteroa", "VIIRS_NOAA20", "2026-11-21 05:24", 21.247, 3, 0.649, 3, "21 km"),
    ("PlanchonPeteroa", "VIIRS_NOAA21", "2026-11-21 06:06", 23.838, 1, 0.103, 3, "24 km"),
]

D0 = {"motivo_vacio": None, "crater_sin_posicion": False, "px_mir_invalido_crater": 0, "px_saturados_crater": 0,
      "px_bowtie_crater": 0, "px_mir_hueco_crater": 0, "px_tir_hueco_crater": 0, "alertados_sin_fondo": 0}


def _montar_opts():
    """El objeto de opciones de Miniaturas.montar tal como está en index.html (brace matching sobre el texto real)."""
    src = (FRONT / "index.html").read_text(encoding="utf-8")
    m = re.search(r"Miniaturas\.montar\(dp, v\.name, ", src)
    assert m, "no encontré la llamada a Miniaturas.montar en index.html"
    i = m.end()
    assert src[i] == "{"
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[i:j + 1]
    raise AssertionError("objeto de opciones sin cerrar")


HARNESS = r"""
'use strict';
const fs = require('fs'), vm = require('vm');
const IN = JSON.parse(fs.readFileSync(0, 'utf8'));
class El {
  constructor(tag) { this.tag = tag; this.children = []; this.parent = null; this.className = ''; this._text = null;
    this.title = ''; this.dataset = {}; this.attrs = {}; this.style = {}; }
  set textContent(t) { this.children = []; this._text = String(t); }
  get textContent() { return this._text != null && !this.children.length ? this._text
    : this.children.map(c => c.textContent).join(' '); }
  appendChild(c) { c.parent = this; this.children.push(c); return c; }
  removeChild(c) { this.children = this.children.filter(x => x !== c); return c; }
  get firstChild() { return this.children[0] || null; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  addEventListener() {}
  remove() { if (this.parent) this.parent.removeChild(this); }
  getContext() { return null; }
}
function buscar(el, cls, out = []) {
  if ((' ' + el.className + ' ').includes(' ' + cls + ' ')) out.push(el);
  for (const c of el.children) buscar(c, cls, out);
  return out;
}
const tick = () => new Promise(r => setImmediate(r));
async function panel(caso) {
  const document = { createElement: t => new El(t), getElementById: () => null, head: new El('head'), documentElement: {} };
  const sb = { document, console, Date, String, Math, Number, JSON, Object, Array, encodeURIComponent, setTimeout, Promise,
    Image: class { set src(v) { this._src = v; } }, getComputedStyle: () => ({ getPropertyValue: () => '' }),
    fetch: async () => ({ ok: true, json: async () => ({ n_ultimas: 10, familias: { [caso.familia]: caso.entradas } }) }) };
  vm.createContext(sb);
  vm.runInContext(fs.readFileSync(IN.cnm, 'utf8'), sb, { filename: 'crater_no_medido.js' });
  vm.runInContext(fs.readFileSync(IN.cumbre, 'utf8'), sb, { filename: 'cumbre.js' });
  vm.runInContext(fs.readFileSync(IN.mini, 'utf8') + '\n;globalThis.Miniaturas = Miniaturas;', sb, { filename: 'miniaturas.js' });
  // Variables que la llamada de index.html toma de renderDetail.
  sb.d = { records: caso.records };
  sb.includeFar = !!caso.includeFar;
  sb.innerKm = caso.innerKm || 5;
  sb.detailSensor = caso.familia;
  sb.fmtLocalCL = s => s;
  sb.getLevel = v => ({ key: v > 0 ? 'low' : 'none' });
  sb.eqVrp = r => (r.distance_class === 'far' && !sb.includeFar) ? 0
    : (r.primary_cluster ? (r.primary_cluster.vrp_mw || 0) : (r.vrp_mw || 0));
  const opts = vm.runInContext('(' + IN.opts + ')', sb);
  const host = new El('div');
  const p = sb.Miniaturas.montar(host, 'X', opts);
  await tick(); await tick();
  return buscar(p, 'mini-tarjeta').map(t => ({
    estado: t.dataset.estado,
    vrp: (buscar(t, 'mini-vrp')[0] || {}).textContent,
    title: (buscar(t, 'mini-vrp')[0] || {}).title,
    marcas: buscar(t, 'mini-marca').map(x => x.textContent),
    colores: buscar(t, 'mini-marca').map(x => x.style.color || null),
    clases: t.className }));
}
(async () => {
  const out = {};
  for (const [k, caso] of Object.entries(IN.casos)) out[k] = await panel(caso);
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""


def _correr(casos):
    datos = {"cnm": str(FRONT / "crater_no_medido.js"), "cumbre": str(FRONT / "cumbre.js"),
             "mini": str(FRONT / "miniaturas.js"),
             "opts": _montar_opts(), "casos": casos}
    r = subprocess.run(["node", "-e", HARNESS], input=json.dumps(datos), capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _entrada(dt, sensor, **kw):
    e = {"datetime_utc": dt, "sensor": sensor, "granule": "g", "product_version": "nrt", "vrp_mw": 0.0,
         "n_anomalous_pixels": 0, "distance_class": None, "final_hotspot_dist_km": None, "motivo_vacio": None,
         "archivo": None, "sin_imagen": "sin_granulo_en_esta_corrida", "alertadas": [], "dayflag": 0}
    e.update(kw)
    return e


def _record(e, vrp=0.0, diag=None, **kw):
    r = {"datetime_utc": e["datetime_utc"], "sensor": e["sensor"], "distance_class": e["distance_class"],
         "final_hotspot_dist_km": e["final_hotspot_dist_km"], "n_anomalous_pixels": e["n_anomalous_pixels"],
         "vrp_mw": vrp, "via_codigo_mirova": True, "primary_cluster": {"vrp_mw": vrp} if vrp else None,
         "diag_codigo_mirova": dict(D0, **(diag or {}))}
    r.update(kw)
    return r


def _lejanas():
    entradas, records = [], []
    for volcan, sensor, dt, dist, n_alert, vrp, inner, _ in LEJANAS:
        e = _entrada(dt, sensor, distance_class="far", final_hotspot_dist_km=dist, n_anomalous_pixels=n_alert,
                     vrp_mw=vrp, alertadas=[[30 + i, 30] for i in range(n_alert)], archivo=f"VIIRS375/{volcan}.png",
                     sin_imagen=None)
        entradas.append(e)
        records.append(_record(e, vrp=vrp))
    return entradas, records


def test_r4fb_106_las_6_lejanas_reales_no_dicen_sin_anomalia():
    entradas, records = _lejanas()
    control = _entrada("2026-11-20 05:00", "VIIRS_NOAA20")
    out = _correr({
        "solo_crater": {"familia": "VIIRS375", "entradas": entradas + [control], "records": records + [_record(control)]},
        "incluir": {"familia": "VIIRS375", "entradas": entradas, "records": records, "includeFar": True},
    })
    sc = out["solo_crater"]
    assert len(sc) == 7
    for t, (volcan, sensor, dt, dist, n_alert, vrp, inner, txt) in zip(sc, LEJANAS):
        assert t["estado"] == "lejana", (volcan, dt, t)
        assert t["vrp"] == "Anomalía lejana, " + txt, (volcan, dt, t)
        assert "Sin anomalía" not in t["vrp"] and "VRP" not in t["vrp"]
        assert "mini-lejana" in t["clases"] and "mini-con" not in t["clases"]
        assert "Incluir lejanas" in t["title"]
    # control: pasada sin alertados en el cráter
    assert sc[6]["estado"] == "nada" and sc[6]["vrp"] == "Sin anomalía"
    # control: con «Incluir lejanas» la misma tarjeta publica su potencia
    for t, fila in zip(out["incluir"], LEJANAS):
        assert t["estado"] == "con" and t["vrp"].startswith("VRP = "), t


@pytest.mark.parametrize("motivo,texto", [
    ("fondo_no_estimado", "No medida: fondo no estimado"),
    ("crater_no_evaluado", "No medida: cráter no evaluable"),
    ("sin_radiancia_valida", "No medida: sin radiancia válida"),
    ("escena_invalida", "No medida: escena inválida"),
    ("sunglint", "No medida: reflejo solar"),
    ("angulo_ausente", "No medida: sin ángulo"),   # S199 (F8-107, F3-102, R3F3-102)
])
def test_r4fb_104_las_escenas_no_medidas_dicen_no_medida(motivo, texto):
    e = _entrada("2026-11-20 05:00", "MODIS_TERRA", motivo_vacio=motivo)
    c = _entrada("2026-11-20 03:00", "MODIS_TERRA")
    out = _correr({"x": {"familia": "MODIS", "entradas": [e, c],
                         "records": [_record(e, diag={"motivo_vacio": motivo}), _record(c)]}})["x"]
    assert len(out) == 2
    assert out[0]["estado"] == "no_medida" and out[0]["vrp"] == texto, out[0]
    assert "no es «sin anomalía»" in out[0]["title"]
    assert out[1]["vrp"] == "Sin anomalía"   # control: sin motivo


def test_r4fb_105_la_tarjeta_lleva_las_marcas_de_crater_y_fondo():
    hueco = _entrada("2026-11-20 06:00", "VIIRS_NOAA21")
    sat = _entrada("2026-11-20 05:00", "VIIRS_NOAA20", n_anomalous_pixels=4)
    sinfondo = _entrada("2026-11-20 04:00", "VIIRS_NOAA21", n_anomalous_pixels=5)
    limpio = _entrada("2026-11-20 03:00", "VIIRS_NOAA20", n_anomalous_pixels=3)
    out = _correr({"x": {"familia": "VIIRS375", "entradas": [hueco, sat, sinfondo, limpio], "records": [
        _record(hueco, diag={"px_mir_hueco_crater": 2}),
        _record(sat, vrp=25.8, diag={"px_saturados_crater": 3}, distance_class="summit"),
        _record(sinfondo, vrp=4.2, diag={"alertados_sin_fondo": 2}, distance_class="summit"),
        _record(limpio, vrp=1.5, distance_class="summit"),
    ]}})["x"]
    assert len(out) == 4
    # cráter con la MIR perdida y 0 MW: no es «Sin anomalía»
    assert out[0]["estado"] == "cnm" and out[0]["vrp"] == "Cráter no medido", out[0]
    assert "No se pudo medir el cráter" in out[0]["title"]
    # potencia con MIR saturada: VRP y la marca de que puede ser mayor
    assert out[1]["vrp"] == "VRP = 25.8 MW"
    assert any("MIR saturada en 3 píxeles" in m for m in out[1]["marcas"]), out[1]
    # potencia con alertados sin fondo
    assert out[2]["vrp"] == "VRP = 4.20 MW"
    assert any("fondo no estimado en 2 de 5 alertados" in m for m in out[2]["marcas"]), out[2]
    # control: record limpio, sin marca
    assert out[3]["vrp"] == "VRP = 1.50 MW" and out[3]["marcas"] == []


def test_lejana_con_calor_en_la_cumbre_lleva_la_marca_de_cumbre_js():
    """Láscar 2026-11-24 05:06 (NOAA21): la pasada es lejana por la regla radiante, pero la imagen muestra también un
    alertado sobre el cráter. «Anomalía lejana» sola escondería ese calor; la tarjeta lleva la marca de cumbre.js."""
    lej = _entrada("2026-11-24 05:06", "VIIRS_NOAA21", distance_class="far", final_hotspot_dist_km=12.27,
                   n_anomalous_pixels=2, alertadas=[[33, 33], [40, 36]])
    sin = _entrada("2026-11-24 04:00", "VIIRS_NOAA20", distance_class="far", final_hotspot_dist_km=8.5,
                   n_anomalous_pixels=1, alertadas=[[40, 36]])
    out = _correr({"x": {"familia": "VIIRS375", "innerKm": 5, "entradas": [lej, sin], "records": [
        _record(lej, vrp=1.1, anomaly_pixels=[{"dist_km": 0.4, "bt_k": 300.0}, {"dist_km": 12.27, "bt_k": 310.0}]),
        _record(sin, vrp=0.3, anomaly_pixels=[{"dist_km": 8.5, "bt_k": 305.0}]),
    ]}})["x"]
    assert out[0]["vrp"] == "Anomalía lejana, 12 km"
    assert out[0]["marcas"] == ["◉ también hay calor en la cumbre (1 píxel a 0,4 km)"], out[0]
    assert out[0]["colores"] == ["#ff8a65"]
    # control: lejana sin alertados en el radio de la cumbre, sin marca; bajo 10 km la distancia lleva un decimal
    assert out[1]["vrp"] == "Anomalía lejana, 8,5 km" and out[1]["marcas"] == []


def test_r4fb_v202_sin_store_no_se_inventa_potencia():
    entradas, records = _lejanas()
    out = _correr({"vacio": {"familia": "VIIRS375", "entradas": entradas, "records": []},
                   "control": {"familia": "VIIRS375", "entradas": entradas, "records": records}})
    assert len(out["vacio"]) == 6
    for t in out["vacio"]:
        assert t["estado"] == "sin_dato" and t["vrp"] == "Sin dato del tablero", t
        assert "MW" not in t["vrp"]
    assert all(t["estado"] == "lejana" for t in out["control"])


def test_index_no_cae_a_la_potencia_del_indice_sin_record():
    """La llamada de index.html pasa recordDe y su vrpDe no usa e.vrp_mw (suma de todos los alertados)."""
    opts = _montar_opts()
    assert "recordDe" in opts and "radioKm" in opts
    assert "e.vrp_mw" not in opts
