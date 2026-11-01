"""La marca del cambio de detector va donde cambian los DATOS, no donde se mergeó el código (auditoría post-K S155).

POR QUÉ: K entró a producción el 2026-10-18 09:57 UTC (#850), pero los 30 días anteriores se reprocesaron con K, así
que en las series del tablero el escalón está en la fecha de OBSERVACIÓN 2026-09-18. Con la marca en el 18-oct, un
operador veía a Copahue o Llaima dejar de tener anomalías el 18-sep sin ninguna marca: un cambio del detector leído
como un cambio del volcán, justo lo que la marca existía para evitar (hallazgo de los frentes 2, 3 y 4 de
docs/AUDIT_S155.md, confirmado por sus verificadores y en pantalla con diario.html).

La frontera se mide en los datos: un record es de K si trae regimen.codigo_sha (marca desde S151; ningún record C0 la
trae, porque los C0 marcados quedaron dentro de la ventana reprocesada). Cuando se aplique el reproceso histórico con
K (tarea 1.24) los records anteriores al 18-sep pasarán a traer la marca y esta prueba se pondrá roja: es el aviso de
que hay que mover DATOS_K_DESDE_UTC (o retirar la línea), no un error que haya que silenciar.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MODULO = RAIZ / "frontend" / "cambio_detector.js"
DATOS = RAIZ / "data" / "mirova_equivalent"
# Los once volcanes que cargan las vistas (diario.html y mosaico.html piden <vol>_recent.json de estos).
TIER_A = ["Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
          "Villarrica", "PuyehueCordonCaulle", "Chaiten", "Isluga"]
HAY_NODE = shutil.which("node") is not None


def constantes():
    src = MODULO.read_text(encoding="utf-8")
    m = re.search(r'^\s*const DATOS_K_DESDE_UTC = "(\d{4}-\d{2}-\d{2})T00:00:00Z";', src, re.M)
    p = re.search(r'^\s*const CAMBIO_DETECTOR_UTC = "([^"]+)";', src, re.M)
    assert m, "cambio_detector.js tiene que declarar DATOS_K_DESDE_UTC como fecha de observación a medianoche UTC"
    assert p, "cambio_detector.js tiene que conservar CAMBIO_DETECTOR_UTC (hora del merge de #850)"
    return m.group(1), p.group(1)


def con_marca(r):
    return bool((r.get("regimen") or {}).get("codigo_sha"))


def test_la_frontera_declarada_es_la_de_los_datos():
    desde, _ = constantes()
    problemas = []
    for v in TIER_A:
        recs = json.loads((DATOS / f"{v}.json").read_text(encoding="utf-8")).get("records", [])
        antes = [r for r in recs if r["datetime_utc"][:10] < desde]
        dia = [r for r in recs if r["datetime_utc"][:10] == desde]
        desp = [r for r in recs if r["datetime_utc"][:10] >= desde]
        n_antes = sum(map(con_marca, antes))
        if n_antes:
            problemas.append(f"{v}: {n_antes} records ANTES de {desde} traen marca de K (¿se aplicó el histórico con K?)")
        if not dia or sum(map(con_marca, dia)) < 0.9 * len(dia):
            problemas.append(f"{v}: el {desde} no es el primer día de K ({sum(map(con_marca, dia))} de {len(dia)} con marca)")
        if desp and sum(map(con_marca, desp)) < 0.95 * len(desp):
            problemas.append(f"{v}: desde {desde} sólo {sum(map(con_marca, desp))} de {len(desp)} records traen marca")
    assert not problemas, "mover DATOS_K_DESDE_UTC en frontend/cambio_detector.js:\n" + "\n".join(problemas)


def test_control_la_prueba_ve_una_frontera_corrida():
    """Control positivo: con la frontera un día antes o un día después de la real, la misma cuenta tiene que fallar."""
    desde, _ = constantes()
    recs = json.loads((DATOS / "Copahue.json").read_text(encoding="utf-8")).get("records", [])
    from datetime import date, timedelta
    d = date.fromisoformat(desde)
    for corrida in (d - timedelta(days=1), d + timedelta(days=1)):
        c = corrida.isoformat()
        antes_con = sum(con_marca(r) for r in recs if r["datetime_utc"][:10] < c)
        dia = [r for r in recs if r["datetime_utc"][:10] == c]
        falla = antes_con > 0 or (not dia or sum(map(con_marca, dia)) < 0.9 * len(dia))
        assert falla, f"con la frontera en {c} la prueba no se habría dado cuenta"


@pytest.mark.skipif(not HAY_NODE, reason="el módulo se prueba con node")
def test_la_linea_va_en_la_frontera_de_los_datos_y_el_aviso_dice_las_dos_fechas(tmp_path):
    desde, merge = constantes()
    js = r"""
    const src = require('fs').readFileSync(process.argv[process.argv.length - 1], 'utf8');
    const registrados = [];
    const ventana = { Chart: { register: p => registrados.push(p) } };
    new Function("window", "module", src)(ventana, undefined);
    const p = registrados[0];
    const t = Date.parse(ventana.CambioDetector.DATOS_K_DESDE_UTC);
    const trazos = [];
    const ctx = new Proxy({}, { get: (o, k) => (k in o ? o[k] : (...a) => trazos.push([k, ...a])),
                                set: (o, k, v) => { o[k] = v; return true; } });
    const chart = { ctx, chartArea: { top: 10, bottom: 110, left: 0, right: 200 },
      scales: { x: { type: "time", min: t - 5 * 86400000, max: t + 5 * 86400000,
                     getPixelForValue: v => (v - (t - 5 * 86400000)) / (10 * 86400000) * 200 } } };
    p.afterDatasetsDraw(chart);
    const mov = trazos.filter(x => x[0] === "moveTo")[0];
    process.stdout.write(JSON.stringify([registrados.length, mov, ventana.CambioDetector.textoAviso()]));
    """
    r = subprocess.run(["node", "-e", js, str(MODULO)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    n, mov, aviso = json.loads(r.stdout)
    assert n == 1
    assert mov == ["moveTo", 100, 10], "la línea vertical tiene que caer en DATOS_K_DESDE_UTC"
    d = desde.split("-")
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    legible = f"{int(d[2])} {meses[int(d[1]) - 1]} {d[0]}"
    assert f"fecha de observación desde el {legible}" in aviso, aviso
    assert "18 oct 2026 09:57 UTC" in aviso and "producción" in aviso, aviso
    assert f"crucen el {legible}" in aviso, aviso
