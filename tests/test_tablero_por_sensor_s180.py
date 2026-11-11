# -*- coding: utf-8 -*-
"""S180: el tablero por sensor (tarjeta mínima y página del volcán con pestañas MODIS, VIIRS 375, VIIRS 750 y
Combinado) cambia cómo se muestra, nunca qué se publica.

POR QUÉ. Nicolás pidió el 2026-11-11 que el tablero se pareciera al visualizador de MIROVA: una serie por sensor,
sin separar satélites, y una tarjeta con lo que decide. Es un cambio de presentación sobre un SDA en producción
(Resolución CPLT N°372): si al reorganizar la página se tocara un predicado de publicación, el operador vería otro
volcán sin que nada lo avise. Estas pruebas fijan que eso no pasó y que lo que se movió no se perdió.

QUÉ MIDE, y qué no:
- SÍ: que el cuerpo de cada predicado de publicación de las tres vistas es el mismo que en el tag
  `pre-s180-visualizador` (punta de main antes del rediseño), sin contar comentarios ni espacios. Si un cambio
  futuro toca un predicado A PROPÓSITO, se mueve el tag de referencia de esta prueba con su razón escrita.
- SÍ: que unir satélites no cambia ningún máximo diario (propiedad de toDailyMax, probada con node sobre el código
  real) y que las series se llaman como las busca cambio_detector.js.
- SÍ: que las líneas que salieron de la tarjeta siguen en la página del volcán, y que el enlace a MIROVA usa el GVP
  de volcanoes.yaml.
- NO: cómo se ve. Eso se verificó en navegador real (capturas en el PR).

Las dos preguntas del instrumento: (1) si un predicado cambiara, ¿fallaría? Sí, `test_control_un_cambio_se_nota`
mete un cambio y exige que la comparación lo vea. (2) ¿Y si la extracción estuviera muerta? Cada cuerpo extraído
tiene que existir y no estar vacío, y se exigen los predicados centrales en las tres vistas.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
TAG = "pre-s180-visualizador"
VISTAS = ["index.html", "diario.html", "mosaico.html"]
# Lo que decide qué se publica y cuánto vale (lista del encargo de S180 y sus auxiliares). latestDetection (index) y
# latestVRP (mosaico) sí cambiaron, sólo para devolver además el sensor: se vigilan aparte, por sus guardas.
PREDICADOS = ["mirovaEqVrp", "mirovaEqVrpCore", "mirovaEqVrpDisplay", "eqVrpDisplay", "f5CoreMagnitude",
              "isValidDetection", "isSummitDetection", "isThermalArtifact", "isCirrusArtifact",
              "isDiffuseFieldArtifact", "toDailyMax", "esAnclaHonesta", "esValorCensurado", "pixelesDelMarcador"]


def _fuente_tag(vista):
    r = subprocess.run(["git", "show", f"{TAG}:frontend/{vista}"], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8")
    if r.returncode != 0:
        pytest.skip(f"sin el tag {TAG} en este checkout")
    return r.stdout


def _cuerpo(src, nombre):
    """Cuerpo de `function nombre(...) {...}` (frontera de palabra, A92), sin comentarios `//` ni espacios de más."""
    m = re.search(r"(?<![A-Za-z0-9_])function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        return None
    i = src.index("{", m.end())
    prof = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            prof += 1
        elif src[j] == "}":
            prof -= 1
            if prof == 0:
                cuerpo = re.sub(r"//[^\n]*", "", src[i + 1:j])
                return re.sub(r"\s+", " ", cuerpo).strip()
    return None


@pytest.mark.parametrize("vista", VISTAS)
def test_los_predicados_de_publicacion_no_cambiaron(vista):
    antes, ahora = _fuente_tag(vista), (RAIZ / "frontend" / vista).read_text(encoding="utf-8")
    vistos = set()
    for nombre in PREDICADOS:
        c0 = _cuerpo(antes, nombre)
        if c0 is None:
            continue
        c1 = _cuerpo(ahora, nombre)
        assert c1, f"{vista}: {nombre} desapareció"
        assert c0 == c1, f"{vista}: cambió el cuerpo de {nombre}"
        vistos.add(nombre)
    assert "isValidDetection" in vistos and "isThermalArtifact" in vistos, (vista, vistos)


def test_control_un_cambio_se_nota():
    src = (RAIZ / "frontend" / "index.html").read_text(encoding="utf-8")
    c = _cuerpo(src, "isValidDetection")
    assert c
    mutado = src.replace("function isValidDetection(", "function isValidDetection(r0, ", 1)
    mutado = re.sub(r"(function isValidDetection\([^{]*\{)", r"\1 if (r0) return false;", mutado, count=1)
    assert _cuerpo(mutado, "isValidDetection") != c


def _guardas(src, nombre):
    """Las líneas que deciden qué record entra (los `continue` y el valor), sin comentarios."""
    c = _cuerpo(src, nombre) or ""
    return [g.strip() for g in re.findall(r"if \([^;]*?\) continue;|const v = [^;]*;", c)]


@pytest.mark.parametrize("vista,nombre", [("index.html", "latestDetection"), ("mosaico.html", "latestVRP")])
def test_la_ultima_deteccion_se_elige_igual(vista, nombre):
    g0 = _guardas(_fuente_tag(vista), nombre)
    g1 = _guardas((RAIZ / "frontend" / vista).read_text(encoding="utf-8"), nombre)
    assert len(g0) >= 4 and g0 == g1, (g0, g1)


EQVRP = "isThermalArtifact(rec, innerKm) ? 0 : mirovaEqVrpDisplay(rec, innerKm, includeFarDistance)"


def test_eqvrp_de_la_pagina_y_del_minigrafico_son_el_mismo():
    """El minigráfico de la tarjeta usa una copia de la expresión de eqVrp de renderDetail (A102: vigilada aquí)."""
    src = (RAIZ / "frontend" / "index.html").read_text(encoding="utf-8")
    assert src.count("const eqVrp = (rec) => " + EQVRP + ";") == 2, "renderDetail y datosMiniGrafico"
    assert EQVRP in _fuente_tag("index.html")
    assert "toDailyMax(" in (_cuerpo(src, "datosMiniGrafico") or "")


def test_series_una_por_sensor_con_el_nombre_que_busca_cambio_detector():
    cuerpo = _cuerpo((RAIZ / "frontend" / "index.html").read_text(encoding="utf-8"), "buildDatasets")
    etiquetas = re.findall(r'label:"([^"]+)"', cuerpo)
    propias = [e for e in etiquetas if not e.startswith("MIROVA")]
    assert propias == ["MODIS", "VIIRS 750m", "VIIRS 375m"], propias
    assert re.match(r"^MODIS", propias[0])
    assert re.match(r"^VIIRS\b.*750", propias[1]) and re.match(r"^VIIRS\b.*375", propias[2])
    assert not any(re.search(r"Terra|Aqua|SNPP|NOAA", e) for e in etiquetas), etiquetas
    js = (RAIZ / "frontend" / "cambio_detector.js").read_text(encoding="utf-8")
    assert "serie: /^MODIS/" in js and r"serie: /^VIIRS\b.*375/" in js and r"serie: /^VIIRS\b.*750/" in js


@pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")
def test_unir_satelites_no_cambia_ningun_maximo_diario(tmp_path):
    """Con el toDailyMax real de index.html: el máximo diario de la unión es el máximo de los máximos por satélite."""
    src = (RAIZ / "frontend" / "index.html").read_text(encoding="utf-8")
    m = re.search(r"function toDailyMax\(", src)
    i = src.index("{", m.end())
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            break
    fn = src[m.start():j + 1]
    recs = []
    import random
    rnd = random.Random(180)
    for _ in range(400):
        d = f"2026-10-{rnd.randint(1, 28):02d} {rnd.randint(0, 23):02d}:{rnd.randint(0, 59):02d}"
        recs.append({"datetime_utc": d, "sensor": rnd.choice(["VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"]),
                     "v": rnd.choice([0, 0, rnd.random() * 50])})
    js = fn + """
const recs = %s; const g = r => r.v;
const union = new Map(toDailyMax(recs, g).map(p => [p.x, p.y]));
const porSat = new Map();
for (const s of ["VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"])
  for (const p of toDailyMax(recs.filter(r => r.sensor === s), g)) porSat.set(p.x, Math.max(porSat.get(p.x) ?? -1, p.y));
let malos = 0; for (const [x, y] of union) if (porSat.get(x) !== y) malos++;
process.stdout.write(JSON.stringify([union.size, porSat.size, malos]));
""" % json.dumps(recs)
    f = tmp_path / "t.js"
    f.write_text(js, encoding="utf-8")
    n_union, n_sat, malos = json.loads(subprocess.run(["node", str(f)], capture_output=True, text=True,
                                                      check=True).stdout)
    assert n_union == n_sat > 20 and malos == 0


def test_lo_que_salio_de_la_tarjeta_sigue_en_la_pagina_del_volcan():
    src = (RAIZ / "frontend" / "index.html").read_text(encoding="utf-8")
    tarjeta, plegado = _cuerpo(src, "buildCards"), _cuerpo(src, "filasUltimaLectura")
    for cls in ("vc-thermal", "vc-anom", "vc-mirova", "vc-corr", "vc-distance"):
        assert f'"{cls}' not in tarjeta, f"{cls} sigue en la tarjeta"
        assert f'"{cls}' in plegado, f"{cls} se perdió: no está en filasUltimaLectura"
    assert "filasUltimaLectura(v, d)" in _cuerpo(src, "renderDetail")
    for f in ("datosMiniGrafico(", "monitoringFreshness(", "latestDetection("):
        assert f in tarjeta, f


def test_la_url_dice_el_volcan_abierto():
    src = (RAIZ / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "escribirVolcanEnURL();" in _cuerpo(src, "renderDetail")
    assert 'q.set("volcano", currentVolcano.name)' in _cuerpo(src, "escribirVolcanEnURL")


def test_enlace_a_mirova_con_el_gvp_de_volcanoes_yaml():
    src = (RAIZ / "frontend" / "index.html").read_text(encoding="utf-8")
    bloque = re.search(r"const MIROVA_VOLCANO_ID = \{(.*?)\};", src, re.S).group(1)
    ids = {k: int(v) for k, v in re.findall(r"(\w+): (\d+)", bloque)}
    data = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    vs = data["volcanoes"] if isinstance(data, dict) else data
    tier_a = {v["name"]: v["gvp_id"] for v in vs if v.get("mirova_monitored")}
    assert len(tier_a) == 11 and ids == tier_a
    # páginas comprobadas en mirovaweb.it el 2026-11-11: MOD, VIR (750), VIR375 y MIR (combinada)
    codigos = re.findall(r'mirova: "(\w+)"', src)
    assert codigos == ["MOD", "VIR375", "VIR", "MIR"], codigos
    assert '"https://www.mirovaweb.it/NRT/volcanoDetails_" + t.mirova + ".php?volcano_id=" + id' in src
