# -*- coding: utf-8 -*-
"""Auditoría externa con Codex, ronda 4, frente E+F (S200): el índice de miniaturas se relee en una página abierta.

POR QUÉ. R4FEF-107 (gravedad 2) tenía dos mitades. La de la falla la cerró #1126: un índice ilegible ya no queda en
caché. La otra mitad seguía: un índice LEÍDO BIEN quedaba en caché toda la sesión. El tablero se usa abierto por horas
en el turno; el sondeo de index.html (5 min) vuelve a dibujar el panel del volcán cuando el NRT trae pasadas nuevas, pero
`cargarIndice` devolvía el índice de la primera lectura, así que la tabla mostraba la pasada nueva y el panel «Últimas 10
pasadas» no, hasta recargar la página. Ahora una lectura (buena o 404) vale `VIGENCIA_MS`, la misma cadencia del sondeo
y de frontend/cobertura.js, y después se relee. Detalle: D:\\codex-vrp\\_salida\\ronda4\\fef_r4_verificacion\\VEREDICTO.md
(R4FEF-107) y el mensaje final del agente de #1126.

QUÉ FIJA, ejecutando con node el archivo real frontend/miniaturas.js con un fetch sintético y un reloj controlado:
(1) dentro de VIGENCIA_MS la segunda consulta no vuelve a pedir el archivo (no se recarga en cada redibujo);
(2) vencida la vigencia se relee y devuelve el índice nuevo (la pasada nueva aparece);
(3) un 404 (volcán sin miniaturas, los 34) también se relee al vencer: si el volcán empieza a tener miniaturas, aparecen.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código de antes? Sí: con miniaturas.js de origin/main
`9bd65c37f` (último cambio del archivo en `a94dbfc31`, #1126) (2) y (3) dan una sola petición y el índice viejo, y VIGENCIA_MS no existe (comprobado al escribirla).
(2) ¿Y si la carga muriera? El harness exige returncode 0 y cada caso exige su número exacto de peticiones; si el módulo
no carga, no hay salida JSON y la prueba cae.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MINI = RAIZ / "frontend" / "miniaturas.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="el panel se prueba con node")

HARNESS = r"""
'use strict';
const fs = require('fs'), vm = require('vm');
const IN = JSON.parse(fs.readFileSync(0, 'utf8'));
let ahora = Date.parse('2026-11-25T12:00:00Z');
class RelojDate extends Date {
  constructor(...a) { if (a.length) super(...a); else super(ahora); }
  static now() { return ahora; }
}
const pedidos = [];
let respuesta = null;   // {status, cuerpo}
const sb = {
  Date: RelojDate, console, Promise, JSON, Math, Object, Array, String, Number, Boolean, Set, Map, encodeURIComponent,
  window: { dispatchEvent: () => true }, CustomEvent: function (n) { this.type = n; },
  fetch: async (url) => {
    pedidos.push(url);
    const r = respuesta;
    return { ok: r.status >= 200 && r.status < 300, status: r.status, json: async () => JSON.parse(r.cuerpo) };
  },
};
vm.createContext(sb);
vm.runInContext(fs.readFileSync(IN.mini, 'utf8') + '\n;globalThis.Miniaturas = Miniaturas;', sb, { filename: 'miniaturas.js' });
const M = sb.Miniaturas;
const indice = (n) => JSON.stringify({ n_ultimas: 10, familias: { VIIRS375: Array.from({ length: n }, (_, i) => ({ datetime_utc: '2026-11-25T0' + i + ':00:00Z' })) } });
const largo = (idx) => idx && idx.familias ? idx.familias.VIIRS375.length : null;
(async () => {
  const out = { vigencia_ms: M.VIGENCIA_MS === undefined ? null : M.VIGENCIA_MS };
  const V = (typeof M.VIGENCIA_MS === 'number') ? M.VIGENCIA_MS : 5 * 60 * 1000;
  // caso 1 y 2: índice bueno
  respuesta = { status: 200, cuerpo: indice(3) };
  const a = await M.cargarIndice('Lascar');
  ahora += 60 * 1000;
  respuesta = { status: 200, cuerpo: indice(4) };
  const b = await M.cargarIndice('Lascar');
  out.dentro = { pedidos: pedidos.filter(u => u.includes('Lascar')).length, largo: largo(b), primero: largo(a) };
  ahora += V + 1000;
  const c = await M.cargarIndice('Lascar');
  out.vencido = { pedidos: pedidos.filter(u => u.includes('Lascar')).length, largo: largo(c) };
  // caso 3: 404 que después aparece
  respuesta = { status: 404, cuerpo: '' };
  const d = await M.cargarIndice('Antuco');
  ahora += V + 1000;
  respuesta = { status: 200, cuerpo: indice(2) };
  const e = await M.cargarIndice('Antuco');
  out.sin_miniaturas = { pedidos: pedidos.filter(u => u.includes('Antuco')).length, antes: largo(d), despues: largo(e) };
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(3); });
"""


@pytest.fixture(scope="module")
def salida():
    r = subprocess.run(["node", "-e", HARNESS], input=json.dumps({"mini": str(MINI)}), capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_vigencia_igual_al_sondeo_de_index(salida):
    assert salida["vigencia_ms"] == 5 * 60 * 1000


def test_dentro_de_la_vigencia_no_se_vuelve_a_pedir(salida):
    assert salida["dentro"] == {"pedidos": 1, "largo": 3, "primero": 3}


def test_vencida_la_vigencia_se_relee_y_aparece_la_pasada_nueva(salida):
    assert salida["vencido"] == {"pedidos": 2, "largo": 4}


def test_un_404_tambien_se_relee(salida):
    assert salida["sin_miniaturas"] == {"pedidos": 2, "antes": None, "despues": 2}
