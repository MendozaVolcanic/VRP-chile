"""frontend/periodo.js (S153, selector de noche o rango del tablero): se prueba el módulo tal como se publica, con
node, no una reescritura en Python.

POR QUÉ: la lógica de fechas del tablero ya falló una vez por zona horaria (PR #250: un string sin 'Z' se leía como
hora local y corría el corte 3 a 4 h en Chile). Este módulo concentra toda la lógica de período de las tres vistas, así
que sus bordes (00:00 y 23:59 UTC, la noche chilena, la URL) se fijan con casos que pueden fallar.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MODULO = RAIZ / "frontend" / "periodo.js"
HAY_NODE = shutil.which("node") is not None

ARNES = r"""
const P = require(process.argv[process.argv.length - 1])   // con node -e, el argumento es el último;
const casos = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const out = casos.map(([fn, args]) => {
  try { return { ok: true, v: P[fn](...args) }; } catch (e) { return { ok: false, err: String(e) }; }
});
process.stdout.write(JSON.stringify(out));
"""

AHORA = 1760745600000  # 2025-10-18 00:00:00 UTC


def correr(casos):
    r = subprocess.run(["node", "-e", ARNES, str(MODULO)], input=json.dumps(casos), capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    salida = json.loads(r.stdout)
    for c, s in zip(casos, salida):
        assert s["ok"], (c, s.get("err"))
    return [s["v"] for s in salida]


pytestmark = pytest.mark.skipif(not HAY_NODE, reason="el módulo se prueba con node")


def test_el_modulo_existe():
    assert MODULO.exists()


def test_url_sin_parametros_da_el_periodo_por_defecto():
    (p,) = correr([["desdeURL", ["?volcano=Villarrica", 30]]])
    assert p == {"dias": 30}


def test_url_con_dias_y_con_rango():
    a, b, c, d, e = correr([
        ["desdeURL", ["?dias=7", 30]],
        ["desdeURL", ["?desde=2026-09-01&hasta=2026-09-15", 30]],
        ["desdeURL", ["?desde=2026-10-01", 30]],                    # una sola noche
        ["desdeURL", ["?desde=2026-09-15&hasta=2026-09-01", 30]],   # al revés: se ordena
        ["desdeURL", ["?desde=2026-13-45&dias=x", 30]],             # basura: por defecto
    ])
    assert a == {"dias": 7}
    assert b == {"desde": "2026-09-01", "hasta": "2026-09-15"}
    assert c == {"desde": "2026-10-01", "hasta": "2026-10-01"}
    assert d == {"desde": "2026-09-01", "hasta": "2026-09-15"}
    assert e == {"dias": 30}


def test_escribir_url_conserva_el_volcan_y_quita_lo_que_sobra():
    a, b, c = correr([
        ["aURL", [{"desde": "2026-10-01", "hasta": "2026-10-01"}, "?volcano=Lascar&dias=7", 30]],
        ["aURL", [{"dias": 30}, "?volcano=Lascar&desde=2026-10-01&hasta=2026-10-02", 30]],
        ["aURL", [{"dias": 7}, "", 30]],
    ])
    assert a == "?volcano=Lascar&desde=2026-10-01&hasta=2026-10-01"
    assert b == "?volcano=Lascar"
    assert c == "?dias=7"


def test_filtro_en_los_bordes_de_la_fecha_utc():
    recs = [{"datetime_utc": t} for t in
            ("2026-09-30 23:59", "2026-10-01 00:00", "2026-10-01 05:36", "2026-10-01 23:59", "2026-10-02 00:00")]
    (f,) = correr([["filtrar", [recs, {"desde": "2026-10-01", "hasta": "2026-10-01"}, AHORA]]])
    assert [r["datetime_utc"] for r in f] == ["2026-10-01 00:00", "2026-10-01 05:36", "2026-10-01 23:59"]


def test_filtro_movil_y_todo():
    recs = [{"datetime_utc": "2025-10-10 05:00"}, {"datetime_utc": "2025-10-17 05:00"}, {"datetime_utc": "2024-01-01 05:00"}]
    a, b = correr([["filtrar", [recs, {"dias": 7}, AHORA]], ["filtrar", [recs, {"dias": 0}, AHORA]]])
    assert [r["datetime_utc"] for r in a] == ["2025-10-17 05:00"]
    assert len(b) == 3


def test_historia_completa_solo_si_el_periodo_sale_de_los_90_dias():
    v = correr([
        ["necesitaHistoria", [{"dias": 30}, AHORA]],
        ["necesitaHistoria", [{"dias": 0}, AHORA]],
        ["necesitaHistoria", [{"dias": 180}, AHORA]],
        ["necesitaHistoria", [{"desde": "2025-10-01", "hasta": "2025-10-02"}, AHORA]],
        ["necesitaHistoria", [{"desde": "2025-06-01", "hasta": "2025-10-02"}, AHORA]],
    ])
    assert v == [False, True, True, False, True]


def test_rotulos_de_la_noche_chilena():
    a, b, c, d = correr([
        ["rotulo", [{"desde": "2026-10-16", "hasta": "2026-10-16"}]],
        ["rotulo", [{"desde": "2026-10-01", "hasta": "2026-10-01"}]],   # cruza el cambio de mes
        ["rotulo", [{"desde": "2026-09-01", "hasta": "2026-09-15"}]],
        ["rotulo", [{"dias": 30}]],
    ])
    assert a == "16 oct 2026 UTC (noche del 15 al 16 de oct en Chile)"
    assert b == "1 oct 2026 UTC (noche del 30 de sep al 1 de oct en Chile)"
    assert c == "1 sep a 15 sep 2026 UTC"
    assert d == "últimos 30 días"


def test_rotulo_corto_para_el_nivel():
    v = correr([
        ["rotuloCorto", [{"dias": 30}]], ["rotuloCorto", [{"dias": 1}]], ["rotuloCorto", [{"dias": 0}]],
        ["rotuloCorto", [{"desde": "2026-10-16", "hasta": "2026-10-16"}]],
        ["rotuloCorto", [{"desde": "2026-09-01", "hasta": "2026-09-15"}]],
    ])
    assert v == ["30 d", "24 h", "todo", "16 oct", "1 sep a 15 sep"]


def test_desplazar_una_noche_y_cruzar_meses():
    a, b, c = correr([
        ["desplazar", [{"desde": "2026-10-01", "hasta": "2026-10-01"}, -1]],
        ["desplazar", [{"desde": "2026-09-01", "hasta": "2026-09-15"}, 1]],
        ["desplazar", [{"dias": 30}, 1]],   # una ventana móvil no se desplaza
    ])
    assert a == {"desde": "2026-09-30", "hasta": "2026-09-30"}
    assert b == {"desde": "2026-09-02", "hasta": "2026-09-16"}
    assert c == {"dias": 30}


def test_fecha_utc_de_un_punto_del_grafico():
    v = correr([["fechaDeX", ["2026-10-01"]], ["fechaDeX", [1759276800000]], ["fechaDeX", ["x"]]])
    assert v == ["2026-10-01", "2025-10-01", None]


def test_es_por_defecto():
    v = correr([["esPorDefecto", [{"dias": 30}, 30]], ["esPorDefecto", [{"dias": 7}, 30]],
                ["esPorDefecto", [{"desde": "2026-10-01", "hasta": "2026-10-01"}, 30]]])
    assert v == [True, False, False]
