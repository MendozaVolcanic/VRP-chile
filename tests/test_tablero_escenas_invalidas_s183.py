# -*- coding: utf-8 -*-
"""S183 (2026-11-14): una escena que no se pudo medir no es una pasada «sin anomalía».

POR QUÉ. La vía «código MIROVA» declara la escena inválida cuando la mitad o más de la grilla no tiene NTI útil (borde de
la franja o del gránulo, o nubes a 200 K o menos: `pipeline/mirova_v750_codigo.py`, l. 163-167 del .m de MIROVA), y también
la deja vacía por reflejo solar. El código de MIROVA no la mide (NaN); nuestro pipeline la guarda con 0 MW y
`diag_codigo_mirova.motivo_vacio`. El tablero la trataba como una pasada normal: la tabla «Todas las pasadas» decía «sin
anomalía», y la tarjeta la contaba como «última pasada» en la frescura del monitoreo. Así una ausencia de observación
se leía como un volcán tranquilo. La página aparte de los 34 (retirada en #1002) ya las descontaba. El 2026-11-14 eran
37 de 2.945 records en data/sombra_34 y 1.920 de 76.367 en data/mirova_equivalent.

QUÉ FIJA, ejecutando en node las funciones reales de frontend/index.html: (1) `escenaSinDato` reconoce el motivo y no
confunde una pasada normal; (2) `lastEventTime` y `proximaPasadaEsperada` no cuentan esas escenas, con control de que
contarlas sí cambiaría el resultado; (3) `rotuloPasadaSinPublicar` rotula la fila «escena sin datos» y sigue diciendo
«anomalía no publicada» y «sin anomalía» donde corresponde; (4) la tabla usa ese rótulo. No cambia ningún valor
publicado: las escenas tienen 0 MW y sin píxeles.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código mal? Cada prueba trae su control (la escena contada
cambia el resultado). (2) ¿Y si la extracción muriera? `_fuente` lanza si no encuentra la función.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
INDEX = RAIZ / "frontend" / "index.html"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")


def _fuente(src, nombre):
    """Texto completo de `function nombre(...) {...}`. Copia de la de test_tablero_34_y_pixeles_s180.py."""
    m = re.search(r"(?<![A-Za-z0-9_])function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        raise AssertionError("no encontré " + nombre)
    i = src.index(") {", m.end()) + 2
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


def _r(t, motivo=None, **k):
    r = {"datetime_utc": t, "sensor": "VIIRS_NOAA20_750", "vrp_mw": 0, "n_anomalous_pixels": 0}
    if motivo is not False:
        r["diag_codigo_mirova"] = {"motivo_vacio": motivo, "s1": {"motivo": motivo}}
    r.update(k)
    return r


def test_escena_sin_dato_reconoce_el_motivo(tmp_path):
    casos = [_r("2026-11-08 04:30", "escena_invalida"), _r("2026-11-08 04:30", "sunglint"),
             _r("2026-11-08 04:30", "otro_motivo"), _r("2026-11-08 04:30", None), _r("2026-11-08 04:30", False), None]
    out = _node(tmp_path, ["escenaSinDato"], "process.stdout.write(JSON.stringify(DATOS.map(escenaSinDato)));", casos)
    assert out == ["escena sin datos", "reflejo solar", "escena sin medir", None, None, None], out


def test_la_ultima_pasada_no_es_una_escena_que_no_miro(tmp_path):
    regs = [_r("2026-11-08 05:12", None), _r("2026-11-08 09:30", "escena_invalida"), _r("2026-11-07 06:00", False)]
    cuerpo = """
const sin = DATOS.filter(r => !escenaSinDato(r));
process.stdout.write(JSON.stringify({ ultima: lastEventTime(DATOS), todas_invalidas: lastEventTime([DATOS[1]]),
  vacio: lastEventTime([]) }));
"""
    out = _node(tmp_path, ["escenaSinDato", "lastEventTime"], cuerpo, regs)
    assert out == {"ultima": "2026-11-08 05:12", "todas_invalidas": None, "vacio": None}, out


def test_la_proxima_pasada_se_calcula_sin_las_escenas_que_no_miraron(tmp_path):
    """Racimos nocturnos de 3 pasadas a 2 h cada 24 h, durante 12 noches, más una escena inválida a media tarde de cada
    día. Sin descontarlas, el hueco diurno se parte en dos y cambian la mediana y el percentil 90."""
    regs = []
    for dia in range(1, 13):
        for h in (4, 6, 8):
            regs.append(_r("2026-10-%02d %02d:00" % (dia, h), None))
        regs.append(_r("2026-10-%02d 16:00" % dia, "escena_invalida"))
    cuerpo = """
const conRegla = proximaPasadaEsperada(DATOS);
const sinEscenas = proximaPasadaEsperada(DATOS.filter(r => !escenaSinDato(r)));
const comoAntes = proximaPasadaEsperada(DATOS.map(r => Object.assign({}, r, { diag_codigo_mirova: null })));
const k = p => [p.prox, p.medianaH, p.toleranciaH];
process.stdout.write(JSON.stringify({ igual: JSON.stringify(k(conRegla)) === JSON.stringify(k(sinEscenas)),
  control: JSON.stringify(k(comoAntes)) !== JSON.stringify(k(sinEscenas)), mediana: conRegla.medianaH, tol: conRegla.toleranciaH }));
"""
    out = _node(tmp_path, ["parseUtcMs", "escenaSinDato", "proximaPasadaEsperada"], cuerpo, regs)
    assert out["igual"] and out["control"], out
    assert out["mediana"] == 2 and out["tol"] == 20, out


def test_el_rotulo_de_la_fila_sin_valor_publicado(tmp_path):
    casos = [_r("t", "escena_invalida"), _r("t", "sunglint"), _r("t", None, n_anomalous_pixels=3), _r("t", None),
             _r("t", False)]
    cuerpo = """
const isValidDetection = r => false;
process.stdout.write(JSON.stringify(DATOS.map(r => rotuloPasadaSinPublicar(r).texto)));
"""
    out = _node(tmp_path, ["escenaSinDato", "rotuloPasadaSinPublicar"], cuerpo, casos)
    assert out == ["escena sin datos", "reflejo solar", "anomalía no publicada", "sin anomalía", "sin anomalía"], out


def test_la_tabla_y_la_tarjeta_usan_las_funciones():
    src = INDEX.read_text(encoding="utf-8")
    detalle = _fuente(src, "renderDetail")
    assert "const rot = rotuloPasadaSinPublicar(r);" in detalle
    assert "if (i === 3 && rot.title) td.title = rot.title;" in detalle
    # el rótulo viejo inline no quedó duplicado (A102)
    assert '"anomalía no publicada" : "sin anomalía"' not in detalle
    assert "if (escenaSinDato(r)) continue;" in _fuente(src, "lastEventTime")
    assert ".filter(r => !escenaSinDato(r))" in _fuente(src, "proximaPasadaEsperada")
    # verificador S183 escenas, H2: los llamadores de la tarjeta (frescura, semáforo y próxima pasada) siguen usando
    # las funciones con el filtro, no una copia en línea (A102)
    cards = _fuente(src, "buildCards")
    assert "const lastTime = lastEventTime(d.records);" in cards
    assert 'const prox = v.fuente === "sombra_34" ? null : proximaPasadaEsperada(d.records);' in cards
    assert "monitoringFreshness(lastTime," in cards
    # H7: la fila lleva su clase y la clase tiene estilo
    assert 'el("tr", "sin-anomalia" + (rot.sinDato ? " escena-sin-dato" : ""))' in detalle
    assert "tr.escena-sin-dato td" in (RAIZ / "frontend" / "vista_volcan.css").read_text(encoding="utf-8")
    # H6: la noche por defecto del rango no parte en una escena sin datos
    assert "r.datetime_utc > m && !escenaSinDato(r) ? r.datetime_utc : m" in src


@pytest.mark.parametrize("pagina", ["diario.html", "mosaico.html"])
def test_diario_y_mosaico_tampoco_cuentan_la_escena_como_pasada(tmp_path, pagina):
    """Verificador S183 escenas, H1: cada vista tiene su propia frescura (S92: un cambio de display va a las tres)."""
    src = (RAIZ / "frontend" / pagina).read_text(encoding="utf-8")
    js = _fuente(src, "parseUtcMs") + "\n" + _fuente(src, "monitoringFreshness") + """
const viejo = new Date(Date.now() - 50 * 3600000).toISOString().slice(0, 16).replace("T", " ");
const nuevo = new Date(Date.now() - 2 * 3600000).toISOString().slice(0, 16).replace("T", " ");
const a = monitoringFreshness([{ datetime_utc: viejo }, { datetime_utc: nuevo, diag_codigo_mirova: { motivo_vacio: "escena_invalida" } }]);
const b = monitoringFreshness([{ datetime_utc: viejo }, { datetime_utc: nuevo, diag_codigo_mirova: { motivo_vacio: null } }]);
const c = monitoringFreshness([{ datetime_utc: nuevo, diag_codigo_mirova: { motivo_vacio: "escena_invalida" } }]);
process.stdout.write(JSON.stringify({ a: a.cls, b: b.cls, c: c.cls }));
"""
    f = tmp_path / "t.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["b"] == "mon-fresh" and out["a"] != "mon-fresh" and out["c"] == "mon-none", out


def test_el_texto_de_ayuda_no_dice_mas_que_el_registro(tmp_path):
    """H3: el record no guarda si la celda del cráter tenía dato; el texto lo dice. H4: un motivo desconocido no hereda el
    texto de la escena sin datos."""
    casos = [_r("t", "escena_invalida"), _r("t", "motivo_nuevo")]
    cuerpo = """
const isValidDetection = r => false;
process.stdout.write(JSON.stringify(DATOS.map(r => rotuloPasadaSinPublicar(r).title)));
"""
    out = _node(tmp_path, ["escenaSinDato", "rotuloPasadaSinPublicar"], cuerpo, casos)
    assert "el registro no dice si el cráter tenía dato" in out[0] and "no miró" not in out[0], out
    assert "motivo_nuevo" in out[1] and "borde de la franja" not in out[1], out


def _datos(carpeta):
    ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", "origin/main", carpeta], cwd=RAIZ,
                        capture_output=True, text=True)
    nombres = [x for x in ls.stdout.split() if x.endswith(".json") and "_recent" not in x]
    if not ls.returncode and nombres:
        return [json.loads(subprocess.run(["git", "show", "origin/main:" + n], cwd=RAIZ, capture_output=True).stdout)
                for n in nombres]
    arch = [a for a in sorted((RAIZ / carpeta).glob("*.json")) if "_recent" not in a.name]
    if not arch:
        pytest.skip("sin " + carpeta)
    return [json.loads(a.read_text(encoding="utf-8")) for a in arch]


def test_en_los_datos_las_escenas_no_tienen_nada_que_publicar(tmp_path):
    """La premisa de que es sólo un rótulo: toda escena con motivo_vacio tiene 0 MW y ningún píxel, en los 34 y en los 11."""
    recs = [r for d in _datos("data/sombra_34") + _datos("data/mirova_equivalent")
            for r in (d.get("records", []) if isinstance(d, dict) else [])]
    malas = [r for r in recs if (r.get("diag_codigo_mirova") or {}).get("motivo_vacio")
             and ((r.get("vrp_mw") or 0) > 0 or (r.get("n_anomalous_pixels") or 0) > 0)]
    n = sum(1 for r in recs if (r.get("diag_codigo_mirova") or {}).get("motivo_vacio"))
    assert n > 0, "el instrumento no vio ninguna escena: no puede afirmar nada"
    assert not malas, malas[:3]
