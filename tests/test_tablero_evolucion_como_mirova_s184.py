# -*- coding: utf-8 -*-
"""S184 (2026-11-14): la evolución «como MIROVA» de la página del volcán (frontend/index.html, armarEvolucion).

POR QUÉ. Los gráficos por volcán de MIROVA muestran a la vez el último mes y el último año (2 meses y 2 años en el
combinado), un palito por pasada en su hora real y el color por distancia (rojo a 5 km o menos, negro más lejos): así se
ve cuándo la actividad pasó al cráter (Nevados de Chillán, desde septiembre de 2026). El tablero agregó ese bloque. Es
SÓLO display: el alto de cada palito tiene que ser el valor que publica eqVrp de renderDetail, y el color tiene que
seguir la regla de publicación de mirovaEqVrp (centroide del cúmulo contra inner_radius_km). Si eso se rompe, el
operador ve en color algo que no se publica, o un valor distinto del que cuentan las estadísticas.

QUÉ FIJA, ejecutando en node las funciones reales de index.html (y cambio_detector.js, que decide la vía):
- Paridad record por record con la expresión de eqVrp copiada de la página, sobre datos reales de tres volcanes
  (Chillán, Láscar y Puyehue-Cordón Caulle, cuyo cráter es de 20 km), con «Solo cráter» y con «Incluir lejanas».
- Los casos sintéticos de cada regla (cráter, fuera, clase far, artefacto, cero, fecha mala) con su control.
- Unir historia y ventana reciente, ventanas, ejes, clases de la escala (sacadas de LEVELS, sin umbrales nuevos),
  una marca de MIROVA por pasada (no el máximo diario) y los datasets (rótulos que busca cambio_detector.js).
- Que la página baja la historia sólo del volcán abierto, y que el gráfico de distancia del período usa la misma
  distancia (A102).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría si el código estuviera mal? Cada caso tiene un control que cambia
una sola cosa y exige el resultado opuesto; la paridad exige además que haya pasadas de las dos clases (si todo fuera
«cráter» la prueba no vería un color mal puesto). Mutaciones atrapadas: ver el PR de S184. (2) ¿Y si la extracción
muriera? `_fuente` y `_const` lanzan si no encuentran el nombre, node falla con mensaje si el código no corre, y la
paridad exige un mínimo de records reales.
"""
import json
import re
import shutil
from datetime import datetime, timezone
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
INDEX = RAIZ / "frontend" / "index.html"
CAMBIO = RAIZ / "frontend" / "cambio_detector.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")

FUNCIONES = ["parseUtcMs", "_havKm", "f5CoreMagnitude", "mirovaEqVrp", "mirovaEqVrpCore", "mirovaEqVrpDisplay",
             "isCirrusArtifact", "isDiffuseFieldArtifact", "isThermalArtifact", "esAnclaHonesta", "sensorGroup",
             "getLevel", "rotuloVentanaEvol", "ventanasEvol", "distanciaDePasada", "pasadasEvol", "todasPasadasEvol",
             "escenaSinDato", "isValidDetection", "esOblicuaEvol", "textoCenitEvol", "clasesGraficoEvol",
             "ultimaPasadaEvol", "vrpPublicadoEvol", "ultimaConCalorEvol", "mwEvol", "haceEvol", "textoUltimaPasadaEvol", "marcasEvol", "tMinRecords",
             "unirHistoriaEvol", "enVentanaEvol", "puntosMirovaEvol", "clasesEscalaEvol", "ejeLogEvol",
             "ejeDistEvol", "ejeXEvol", "rotuloFueraEvol", "inicioDatosEvol", "datosEvol", "datasetsEvol",
             "fechaUtcEvol", "inicioMirovaEvol", "historiaEvol", "armarEvolucion", "mirovaEsDia", "mirovaPointStyle", "mirovaPointFill",
             "mirovaPointRadius", "mirovaSufijoSinGeo", "mirovaLineasDia", "mirovaIconoSol", "mirovaDiaDataset"]
CONSTANTES = ["USE_F5_CORE", "F5_R_CORE_KM", "F5_BT_EXT_K", "LEVELS", "EVOL_DIAS", "EVOL_GRIS", "EVOL_LOG_MIN_MW",
              "EVOL_LOG_MAX_MW", "EVOL_SERIES", "MIROVA_SIN_GEO_TXT", "MIROVA_DIA_TXT", "MIROVA_DIA_RAYOS", "_iconosSol",
              "_historiaEvol", "_evolOcultas", "EVOL_MODOS", "palitosEvolPlugin", "lineasEvolPlugin", "EVOL_CENIT_OBLICUO",
              "NOTA_CENIT_EVOL", "EVOL_EXTREMO_MW", "EVOL_COLOR_LINEA", "EVOL_LIMITE_DETECCION_MW", "EVOL_COLOR_MARCA",
              "ETIQUETA_SENSOR", "EVOL_MISMA_PASADA_MS", "EVOL_PRIORIDAD_ESTADO", "EVOL_FILA_MARCA"]
T_20261001_0500Z = int(datetime(2026, 10, 1, 5, tzinfo=timezone.utc).timestamp() * 1000)
# La expresión de eqVrp de renderDetail, tal como está en la página (test_tablero_por_sensor_s180 vigila que sea una).
EQVRP = "isThermalArtifact(rec, innerKm) ? 0 : mirovaEqVrpDisplay(rec, innerKm, includeFarDistance)"


def _fuente(src, nombre):
    """Texto completo de `function nombre(...) {...}`."""
    m = re.search(r"(?<![A-Za-z0-9_])function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        raise AssertionError("no encontré la función " + nombre)
    i = src.index(") {", m.end()) + 2
    prof = 0
    for j in range(i, len(src)):
        prof += {"{": 1, "}": -1}.get(src[j], 0)
        if prof == 0:
            return src[m.start():j + 1]
    raise AssertionError("llave sin cerrar en " + nombre)


def _const(src, nombre):
    """`const nombre = ...;` completo (también los arreglos y objetos de varias líneas)."""
    m = re.search(r"^const " + re.escape(nombre) + r" = ", src, re.M)
    if not m:
        raise AssertionError("no encontré la constante " + nombre)
    prof, cita = 0, None
    for j in range(m.end(), len(src)):
        c = src[j]
        if cita:                                   # dentro de un texto: sólo importa dónde se cierra
            if c == cita and src[j - 1] != "\\":
                cita = None
            continue
        if c in "\"'`":
            cita = c
        elif c in "[{(":
            prof += 1
        elif c in "]})":
            prof -= 1
        elif c == ";" and prof == 0:
            return src[m.start():j + 1]
    raise AssertionError("constante sin cerrar: " + nombre)


def _js(src=None):
    src = src if src is not None else INDEX.read_text(encoding="utf-8")
    cab = "const CambioDetector = require(%s);\n" % json.dumps(str(CAMBIO))
    return cab + "\n".join(_const(src, c) for c in CONSTANTES) + "\n" + "\n".join(_fuente(src, f) for f in FUNCIONES)


def _node(tmp_path, cuerpo, datos=None, src=None):
    js = _js(src) + "\nconst DATOS = " + json.dumps(datos) + ";\n" + cuerpo
    f = tmp_path / "t.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout)


def _pc(dist, vrp=2.0, **k):
    return dict({"vrp_mw": vrp, "centroid_dist_km": dist, "n_pixels": 3}, **k)


def _rec(dt="2026-10-01 05:00", sensor="VIIRS_NOAA21_750", dist=2.0, vrp=2.0, **k):
    r = {"datetime_utc": dt, "sensor": sensor, "primary_cluster": _pc(dist, vrp), "vrp_mw": vrp,
         "distance_class": "summit" if dist <= 5 else "far", "t_max_k": 320.0,
         "final_hotspot_source": "codigo_mirova", "final_hotspot_dist_km": dist}
    r.update(k)
    return r


# ── Paridad con eqVrp sobre datos reales ─────────────────────────────────────────────────────────────────────────────

VOLCANES = [("NevadosDeChillan", 5), ("Lascar", 5), ("PuyehueCordonCaulle", 20)]
PARIDAD = """
const res = {};
for (const [nombre, innerKm, records] of DATOS) {
  for (const includeFarDistance of [false, true]) {
    const eqVrp = (rec) => %s;
    const pub = records.map(r => [r.datetime_utc, r.sensor, eqVrp(r)]).filter(x => x[2] > 0)
      .map(x => x.join("|")).sort();
    const pts = pasadasEvol(records, innerKm);
    const evol = pts.filter(p => p.enCrater || includeFarDistance).map(p => [p.dt, p.sensor, p.y].join("|")).sort();
    res[nombre + "|" + includeFarDistance] = { iguales: JSON.stringify(pub) === JSON.stringify(evol), n: pub.length,
      nEvol: evol.length, crater: pts.filter(p => p.enCrater).length, fuera: pts.filter(p => !p.enCrater).length,
      registros: records.length };
  }
}
console.log(JSON.stringify(res));
""" % EQVRP


def _datos_reales():
    datos = []
    for nombre, inner in VOLCANES:
        f = RAIZ / "data" / "mirova_equivalent" / (nombre + ".json")
        if not f.exists():
            pytest.skip("sin " + str(f))
        datos.append([nombre, inner, json.loads(f.read_text(encoding="utf-8"))["records"]])
    return datos


def test_paridad_record_por_record_con_eqvrp_en_datos_reales(tmp_path):
    """Lo que la evolución dibuja en color (o en gris con «Incluir lejanas») es exactamente lo que publica eqVrp."""
    src = INDEX.read_text(encoding="utf-8")
    assert src.count("const eqVrp = (rec) => " + EQVRP + ";") >= 1, "la expresión de eqVrp cambió: actualizar EQVRP"
    res = _node(tmp_path, PARIDAD, _datos_reales())
    for clave, r in res.items():
        assert r["registros"] >= 1000, (clave, r)          # la extracción de datos no está vacía
        assert r["iguales"], (clave, r)
        assert r["n"] >= 50, (clave, r)
    # control: en Chillán hay pasadas de las dos clases (si no, un color mal puesto no se vería)
    ch = res["NevadosDeChillan|false"]
    assert ch["crater"] >= 50 and ch["fuera"] >= 50, ch
    # con «Incluir lejanas» se publica todo lo dibujable; con «Solo cráter», sólo lo del cráter
    assert res["NevadosDeChillan|true"]["n"] == ch["crater"] + ch["fuera"], res
    assert ch["n"] == ch["crater"], ch


def test_control_paridad_falla_si_el_color_no_sigue_la_regla(tmp_path):
    """La misma comparación sobre una copia donde `enCrater` mira la distancia del ancla en vez de la regla de
    publicación: tiene que dejar de coincidir. Si no, la prueba de paridad no vería un color mal puesto."""
    src = INDEX.read_text(encoding="utf-8")
    viejo = "const enCrater = mirovaEqVrpDisplay(r, innerKm, false) > 0;"
    assert src.count(viejo) == 1
    mutado = src.replace(viejo, "const enCrater = (distanciaDePasada(r) ?? 0) <= innerKm + 0.5;")
    res = _node(tmp_path, PARIDAD, _datos_reales()[:1], src=mutado)
    assert not res["NevadosDeChillan|false"]["iguales"], res


# ── Casos sintéticos ────────────────────────────────────────────────────────────────────────────────────────────────

def test_pasadas_reglas_y_controles(tmp_path):
    casos = {
        "crater": [_rec(dist=3.0)],
        "fuera": [_rec(dist=8.0)],
        "clase_far_cerca": [_rec(dist=3.0, distance_class="far")],     # la clase far manda, como en mirovaEqVrp
        "cero": [_rec(vrp=0.0)],
        "fecha_mala": [_rec(dt="sin fecha")],
        # cirrus: t_max bajo 0 °C y más de 10 MW, sin vía ni confirmación: artefacto, no se dibuja
        "cirrus": [_rec(vrp=30.0, t_max_k=250.0, sensor="VIIRS_NOAA21_750")],
        "cirrus_control": [_rec(vrp=30.0, t_max_k=300.0, sensor="VIIRS_NOAA21_750")],
        "orden": [_rec(dt="2026-10-02 05:00"), _rec(dt="2026-10-01 05:00")],
        # el alto es el del cúmulo (mirovaEqVrp), no la suma de la escena (A10): en la vía coinciden, aquí no
        "escena": [_rec(vrp=2.0, vrp_mw=50.0)],
        # VIIRS 375 bajo K: el núcleo F5' persistido es lo que se publica (mirovaEqVrpDisplay)
        "nucleo_k": [_rec(sensor="VIIRS_NOAA21", vrp=4.0, f5_core_vrp_mw=1.5)],
        "nucleo_via": [_rec(sensor="VIIRS_NOAA21", vrp=4.0, f5_core_vrp_mw=1.5, via_codigo_mirova=True)],
    }
    cuerpo = """
const out = {};
for (const [k, recs] of Object.entries(DATOS)) out[k] = pasadasEvol(recs, 5);
console.log(JSON.stringify(out));
"""
    o = _node(tmp_path, cuerpo, casos)
    assert len(o["crater"]) == 1 and o["crater"][0]["enCrater"] is True and o["crater"][0]["y"] == 2.0
    assert o["crater"][0]["grupo"] == "VIIRS750" and o["crater"][0]["dist"] == 3.0
    assert len(o["fuera"]) == 1 and o["fuera"][0]["enCrater"] is False and o["fuera"][0]["y"] == 2.0
    assert len(o["clase_far_cerca"]) == 1 and o["clase_far_cerca"][0]["enCrater"] is False
    assert o["cero"] == [] and o["fecha_mala"] == []
    assert o["cirrus"] == [] and len(o["cirrus_control"]) == 1
    assert [p["dt"] for p in o["orden"]] == ["2026-10-01 05:00", "2026-10-02 05:00"]
    assert o["escena"][0]["y"] == 2.0, o["escena"]
    assert o["nucleo_k"][0]["y"] == 1.5 and o["nucleo_via"][0]["y"] == 4.0, (o["nucleo_k"], o["nucleo_via"])


def test_distancia_de_pasada(tmp_path):
    casos = [
        _rec(dist=3.0, hotspot_dist_km=9.0),                                              # ancla honesta: 3
        _rec(dist=3.0, hotspot_dist_km=9.0, final_hotspot_source="vent"),                # no honesta: hotspot 9
        {"datetime_utc": "x", "anomaly_pixels": [{"dist_km": 4.5}]},                     # sólo píxeles
        {"datetime_utc": "x"},                                                           # nada
    ]
    o = _node(tmp_path, "console.log(JSON.stringify(DATOS.map(distanciaDePasada)));", casos)
    assert o == [3.0, 9.0, 4.5, None], o


def test_unir_historia_y_ventanas(tmp_path):
    hist = [{"t": 1}, {"t": 5}, {"t": 9}, {"t": 10}]
    rec = [{"t": 10, "nuevo": True}, {"t": 12, "nuevo": True}]
    cuerpo = """
const [hist, rec] = DATOS;
console.log(JSON.stringify({
  union: unirHistoriaEvol(hist, rec, 10),
  sinHist: unirHistoriaEvol(null, rec, 10),
  sinRec: unirHistoriaEvol(hist, [], Infinity),
  t0: tMinRecords([{datetime_utc: "2026-10-02 05:00"}, {datetime_utc: "2026-10-01 05:00"}]),
  t0vacio: tMinRecords([]) === Infinity,
  vent: enVentanaEvol([{t: 0}, {t: 86400000}, {t: 2 * 86400000}], 3 * 86400000, 2).map(p => p.t),
  ventX: enVentanaEvol([{x: 0}, {x: 2 * 86400000}], 3 * 86400000, 2).map(p => p.x),
  sens: ventanasEvol("VIIRS375"), comb: ventanasEvol("COMB"), modis: ventanasEvol("MODIS"),
  otro: rotuloVentanaEvol(90),
}));
"""
    o = _node(tmp_path, cuerpo, [hist, rec])
    assert o["union"] == [{"t": 1}, {"t": 5}, {"t": 9}, {"t": 10, "nuevo": True}, {"t": 12, "nuevo": True}], o["union"]
    assert o["sinHist"] == rec and o["sinRec"] == hist
    assert o["t0"] == T_20261001_0500Z
    assert o["t0vacio"] is True
    assert o["vent"] == [86400000, 2 * 86400000] and o["ventX"] == [2 * 86400000]
    assert o["sens"] == [{"dias": 30, "rotulo": "Último mes"}, {"dias": 365, "rotulo": "Último año"}]
    assert o["modis"] == o["sens"]
    assert o["comb"] == [{"dias": 60, "rotulo": "Últimos 2 meses"}, {"dias": 730, "rotulo": "Últimos 2 años"}]
    assert o["otro"] == "Últimos 90 días"


def test_tmin_es_utc(tmp_path):
    o = _node(tmp_path, 'console.log(JSON.stringify(tMinRecords([{datetime_utc: "2026-10-01 05:00"}])));')
    assert o == T_20261001_0500Z  # UTC, no hora local


def test_clases_de_la_escala_salen_de_levels(tmp_path):
    cuerpo = """
const c = clasesEscalaEvol(LEVELS);
const mid = k => k.hasta === Infinity ? k.desde * 2 : (k.desde > 0 ? Math.sqrt(k.desde * k.hasta) : k.hasta / 2);
console.log(JSON.stringify({ c: c.map(k => [k.desde, k.hasta === Infinity ? "inf" : k.hasta, k.rotulo]),
  coincide: c.every(k => getLevel(mid(k)).label === k.rotulo),
  topes: LEVELS.slice(1).map(l => l.max === Infinity ? "inf" : l.max) }));
"""
    o = _node(tmp_path, cuerpo)
    assert [k[0] for k in o["c"]] == [0, 1, 10, 100, 1000], o
    assert [k[2] for k in o["c"]] == ["Muy Bajo", "Bajo", "Moderado", "Alto", "Muy Alto"], o
    assert o["coincide"] is True
    # nada inventado: los techos de las bandas son exactamente los de LEVELS
    assert [k[1] for k in o["c"]] == o["topes"]


def test_ejes(tmp_path):
    cuerpo = """
console.log(JSON.stringify({ vacio: ejeLogEvol([]), debil: ejeLogEvol([0.003, 5]), normal: ejeLogEvol([0.5, 80]),
  cero: ejeLogEvol([0, -1]), d25: ejeDistEvol(25), dsin: ejeDistEvol(null) }));
"""
    o = _node(tmp_path, cuerpo)
    assert o["vacio"] == {"min": 0.01, "max": 100000}
    x = _node(tmp_path, "console.log(JSON.stringify([ejeXEvol(1000 * 86400000, 30), inicioDatosEvol(NaN, 0, 1), "
              "inicioDatosEvol(10 * 86400000, 40 * 86400000, 365), inicioDatosEvol(10 * 86400000, 40 * 86400000, 30), "
              "inicioDatosEvol(10.5 * 86400000, 40 * 86400000, 30)]));")
    assert x[0] == {"min": 970 * 86400000, "max": 1000 * 86400000 + 0.6 * 86400000}
    # la ventana de 365 días empieza mucho antes que los datos: se avisa; la de 30 días está cubierta (día de tolerancia)
    assert x[1] is None and x[2] == 10 * 86400000 and x[3] is None and x[4] is None
    assert o["debil"] == {"min": 0.001, "max": 100000}       # lo débil de VIIRS 375 no queda bajo el eje
    assert o["normal"] == {"min": 0.01, "max": 100000}
    assert o["cero"] == {"min": 0.01, "max": 100000}
    # distancia: eje fijo, como MIROVA (lo que pasa de 25 km se recorta en datasetsEvol, con triángulo)
    assert o["d25"] == {"min": 0, "max": 25} and o["dsin"] == {"min": 0, "max": 25}


def test_mirova_una_marca_por_pasada(tmp_path):
    recs = [
        {"datetime_utc": "2026-10-01 05:00", "sensor": "VIIRS375", "VRP_MW": "3.5"},
        {"datetime_utc": "2026-10-01 06:40", "sensor": "VIIRS375", "VRP_MW": "1.2", "source": "ocr"},  # mismo día
        {"datetime_utc": "2026-10-01 07:00", "sensor": "VIIRS", "VRP_MW": "2", "sin_geometria": True},
        {"datetime_utc": "2026-10-01 08:00", "sensor": "VIIRS375", "VRP_MW": "0"},        # cero: no se dibuja
        {"datetime_utc": "2026-10-01 09:00", "sensor": "OTRO", "VRP_MW": "9"},            # sensor sin serie
    ]
    cuerpo = """
const info = s => s === "VIIRS375" ? { color: "#e91e63", label: "VIIRS 375m" } : s === "VIIRS" ? { color: "#00bcd4", label: "VIIRS 750m" } : null;
console.log(JSON.stringify({ noche: puntosMirovaEvol(DATOS, info, false), dia: puntosMirovaEvol(DATOS.slice(0, 1), info, true) }));
"""
    o = _node(tmp_path, cuerpo, recs)
    n = o["noche"]
    assert [p["y"] for p in n] == [3.5, 1.2, 2.0], n          # dos pasadas del mismo día: dos marcas
    assert [p["ocr"] for p in n] == [False, True, False] and [p["sinGeo"] for p in n] == [False, False, True]
    assert n[0]["x"] == T_20261001_0500Z and n[0]["dt"] == "2026-10-01 05:00" and n[2]["sensor"] == "VIIRS 750m"
    assert all(p["dia"] is False for p in n) and o["dia"][0]["dia"] is True


def test_datasets(tmp_path):
    pts = [
        {"t": 1, "grupo": "VIIRS375", "y": 2.0, "enCrater": True, "dist": 1.0, "sensor": "VIIRS_NOAA21"},
        {"t": 2, "grupo": "MODIS", "y": 5.0, "enCrater": True, "dist": None, "sensor": "MODIS_AQUA"},
        {"t": 3, "grupo": "VIIRS750", "y": 1.0, "enCrater": False, "dist": 12.0, "sensor": "VIIRS_NOAA20_750"},
        {"t": 4, "grupo": "VIIRS750", "y": 0.5, "enCrater": False, "dist": 32.0, "sensor": "VIIRS_NOAA20_750"},
    ]
    cuerpo = """
const m = [{ label: "MIROVA VIIRS 375m (ref.)", data: [] }];
const f = ds => ds.map(d => ({ label: d.label, n: d.data.length, palitos: !!d.palitos, color: d.borderColor,
  ys: d.data.map(x => x.y === undefined ? null : x.y) }));
const dd = datasetsEvol(DATOS, m, "dist", false, 25);
const recorte = dd[1].data.map(x => [x.y, x.recortada, dd[1].pointStyle({ raw: x })]);
_evolOcultas.add("VIIRS 375m");
const oculta = datasetsEvol(DATOS, m, "log", false).map(d => [d.label, !!d.hidden]);
console.log(JSON.stringify({ log: f(datasetsEvol(DATOS, m, "log", false)), lejanas: f(datasetsEvol(DATOS, m, "lin", true)),
  dist: f(dd), gris: EVOL_GRIS, recorte, oculta }));
"""
    o = _node(tmp_path, cuerpo, pts)
    log = o["log"]
    assert [d["label"] for d in log] == ["MODIS", "VIIRS 375m", "Fuera del cráter: no publicada", "MIROVA VIIRS 375m (ref.)"]
    assert re.match(r"^MODIS", log[0]["label"]) and re.match(r"^VIIRS\b.*375", log[1]["label"])  # cambio_detector.js
    assert log[0]["ys"] == [5.0] and log[1]["ys"] == [2.0] and log[2]["ys"] == [1.0, 0.5]
    assert log[0]["palitos"] and log[2]["palitos"] and log[2]["color"] == o["gris"]
    assert log[1]["color"] == "#e91e63"
    assert o["lejanas"][2]["label"] == "Fuera del cráter (contada con «Incluir lejanas»)"
    d = o["dist"]
    # distancia: sin MIROVA, sin palitos, y la pasada sin distancia no se dibuja
    assert [x["label"] for x in d] == ["VIIRS 375m", "Fuera del cráter: no publicada"], d
    assert d[0]["ys"] == [1.0] and d[1]["ys"] == [12.0, 25.0] and not any(x["palitos"] for x in d)
    # 32 km queda en el techo de 25 con triángulo; 12 km, en su lugar con círculo
    # fuera: cuadrado (S184 tanda 2); más lejos que el eje: triángulo
    assert o["recorte"] == [[12.0, False, "rect"], [25.0, True, "triangle"]], o["recorte"]
    # una serie apagada en la leyenda sigue apagada al rearmar los datasets
    assert dict(o["oculta"])["VIIRS 375m"] is True and dict(o["oculta"])["MODIS"] is False


# ── Cableado en la página ───────────────────────────────────────────────────────────────────────────────────────────

def test_la_pagina_baja_solo_la_historia_del_volcan_abierto():
    src = INDEX.read_text(encoding="utf-8")
    h = _fuente(src, "historiaEvol")
    assert 'fetchJSON(BASE_PATH + "data/mirova_equivalent/" + v.name + ".json")' in h
    assert "VOLCANOES" not in h and "VOLCANOES" not in _fuente(src, "armarEvolucion")
    assert "_historiaEvol[v.name]" in h                       # una vez por volcán y sesión
    assert "_fullHistoryLoaded" in h and "sombra_34" in h     # no repite lo que ya está en allData
    assert "enrichWithMirovaConfirmation(" in h               # mismo enriquecimiento que loadVolcano
    rd = _fuente(src, "renderDetail")
    assert "armarEvolucion(evolHost, v, d, innerKm, sinLineasDeVia);" in rd
    # A102: el gráfico de distancia del período usa la misma distancia
    assert "distanciaDePasada(r)" in _fuente(src, "buildDistanceData")


def test_la_linea_1600_sigue_en_su_lugar():
    assert INDEX.read_text(encoding="utf-8").splitlines()[1599].startswith("function isValidDetection")


def test_textos_sin_guiones_largos():
    src = INDEX.read_text(encoding="utf-8")
    for nombre in ["armarEvolucion", "rotuloFueraEvol", "rotuloVentanaEvol", "datasetsEvol", "lineasEvolPlugin"]:
        if nombre == "lineasEvolPlugin":
            i = src.index("const lineasEvolPlugin")
            cuerpo = src[i:src.index("\n};", i)]
        else:
            cuerpo = _fuente(src, nombre)
        assert "\u2014" not in cuerpo and "\u2013" not in cuerpo, nombre


def test_control_extraccion_muerta():
    with pytest.raises(AssertionError):
        _fuente("function otra() { return 1; }", "pasadasEvol")
    with pytest.raises(AssertionError):
        _const("const OTRA = 1;", "EVOL_DIAS")


# ── datosEvol y armarEvolucion ejecutados (verificador S184, H2: antes sólo se probaban las funciones puras) ─────────

def _datos_d():
    """allData sintético de un volcán: una pasada por sensor en el cráter, una fuera, y MIROVA noche y día."""
    return {
        "records": [
            _rec(dt="2026-11-10 05:00", sensor="MODIS_AQUA", dist=1.0, vrp=8.0),
            _rec(dt="2026-11-10 06:00", sensor="VIIRS_NOAA21", dist=1.0, vrp=3.0, via_codigo_mirova=True),
            _rec(dt="2026-11-11 06:00", sensor="VIIRS_NOAA20_750", dist=1.0, vrp=4.0),
            _rec(dt="2026-11-12 06:00", sensor="VIIRS_NOAA20_750", dist=32.0, vrp=6.0),
        ],
        "mirovaRecords": [
            {"datetime_utc": "2026-11-10 06:01", "sensor": "VIIRS375", "VRP_MW": "2.5"},
            {"datetime_utc": "2026-11-10 05:01", "sensor": "MODIS", "VRP_MW": "7"},
            {"datetime_utc": "2026-11-10 15:00", "sensor": "VIIRS375", "VRP_MW": "9", "dia": True},
        ],
        "mirovaDiaOcr": [{"datetime_utc": "2026-11-11 15:00", "sensor": "VIIRS", "VRP_MW": "4", "source": "ocr"}],
    }


def test_datos_evol_filtros(tmp_path):
    cuerpo = """
const d = DATOS;
const visibles = { MODIS: true, VIIRS375: true, VIIRS750: true, MIROVA: true };
const r = o => { const x = datosEvol(Object.assign({ d, histTodas: null, innerKm: 5, sensorKey: "COMB", visible: visibles, hasMirova: true }, o));
  return { todos: x.todos.map(p => p.grupo + (p.enCrater ? "" : "*")), noche: x.mirovaNoche.map(p => p.sensor), dia: x.mirovaDia.map(p => p.sensor) }; };
const hist = [{ t: 0, grupo: "MODIS", enCrater: true, y: 1 }, { t: Date.parse("2026-11-10T05:00:00Z"), grupo: "MODIS", enCrater: true, y: 1, viejo: true }];
const u = datosEvol({ d, histTodas: hist, innerKm: 5, sensorKey: "COMB", visible: visibles, hasMirova: true }).todos;
console.log(JSON.stringify({
  comb: r({}), v375: r({ sensorKey: "VIIRS375" }),
  apagado: r({ visible: Object.assign({}, visibles, { VIIRS750: false }) }),
  sinMirova: r({ visible: Object.assign({}, visibles, { MIROVA: false }) }), sombra: r({ hasMirova: false }),
  union: u.map(p => [p.t === 0, !!p.viejo, p.grupo]) }));
"""
    o = _node(tmp_path, cuerpo, _datos_d())
    assert o["comb"]["todos"] == ["MODIS", "VIIRS375", "VIIRS750", "VIIRS750*"], o["comb"]
    assert o["comb"]["noche"] == ["MODIS", "VIIRS 375m"] and o["comb"]["dia"] == ["VIIRS 375m", "VIIRS 750m"], o["comb"]
    assert o["v375"] == {"todos": ["VIIRS375"], "noche": ["VIIRS 375m"], "dia": ["VIIRS 375m"]}, o["v375"]
    assert o["apagado"]["todos"] == ["MODIS", "VIIRS375"] and o["apagado"]["dia"] == ["VIIRS 375m"], o["apagado"]
    assert o["sinMirova"]["noche"] == [] and o["sinMirova"]["dia"] == [] and len(o["sinMirova"]["todos"]) == 4
    assert o["sombra"]["noche"] == [] and o["sombra"]["dia"] == []
    # de la historia sólo entra lo anterior al primer record reciente; lo reciente entra entero (4 pasadas)
    assert o["union"][0] == [True, False, "MODIS"] and not any(x[1] for x in o["union"]) and len(o["union"]) == 5, o["union"]


ARNES = """
const AHORA = Date.parse("2026-11-14T12:00:00Z");
Date.now = () => AHORA;
let charts = {}, allData = {}, includeFarDistance = false, detailSensor = "COMB", evolModo = "log", evolCenitAbierto = false;
let _fullHistoryLoaded = false; const BASE_PATH = "";
const sensorVisible = { MODIS: true, VIIRS375: true, VIIRS750: true, MIROVA: true };
const sessionStorage = { setItem() {} };
function enrichWithMirovaConfirmation() {}
const PEDIDOS = []; let FETCH = () => Promise.resolve(null);
async function fetchJSON(url) { PEDIDOS.push(url); return FETCH(url); }
function mk(tag) { return { tag, children: [], className: "", textContent: "", isConnected: true, oyentes: {},
  appendChild(c) { this.children.push(c); return c; }, append(...cs) { this.children.push(...cs); },
  removeChild(c) { this.children.splice(this.children.indexOf(c), 1); }, get firstChild() { return this.children[0] || null; },
  addEventListener(e, f) { this.oyentes[e] = f; }, getContext() { return { canvas: this }; } }; }
function el(tag, cls) { const e = mk(tag); if (cls) e.className = cls; return e; }
const VIVOS = new Set(); let CREADOS = 0;
class Chart { constructor(ctx, cfg) { this.data = cfg.data; this.options = cfg.options; VIVOS.add(this); CREADOS++; }
  destroy() { VIVOS.delete(this); } isDatasetVisible(i) { return !this.data.datasets[i].hidden; }
  setDatasetVisibility(i, v) { this.data.datasets[i].hidden = !v; } update() {} }
const titulos = host => { const out = []; const rec = n => { if (n.tag === "h5") out.push(n.textContent); (n.children || []).forEach(rec); }; rec(host); return out; };
const etiquetas = k => charts[k].data.datasets.map(d => d.label);
const V11 = { name: "X", hasMirova: true, radius_km: 25 };
const V34 = { name: "S", hasMirova: false, fuente: "sombra_34", radius_km: 25 };
let currentVolcano = V11;
const espera = () => new Promise(r => setTimeout(r, 0));
function _r(dt, vrp, dist) { return { datetime_utc: dt, sensor: "MODIS_AQUA", primary_cluster: { vrp_mw: vrp, centroid_dist_km: dist, n_pixels: 3 },
  vrp_mw: vrp, distance_class: dist <= 5 ? "summit" : "far", t_max_k: 320, final_hotspot_source: "codigo_mirova", final_hotspot_dist_km: dist }; }
"""


def _arnes(tmp_path, cuerpo, datos=None):
    envuelto = "\n(async () => {\n" + cuerpo + "\n})().catch(e => { console.error(e.stack); process.exit(1); });"
    return _node(tmp_path, ARNES + envuelto, datos)


def test_armar_evolucion_ejecutado(tmp_path):
    cuerpo = """
const d = DATOS; const host = mk("div"); const out = {};
// historia: un volcán de los 11 baja SU archivo completo, una vez
FETCH = () => Promise.resolve({ records: [_r("2025-03-01 05:00", 2.0, 1.0)].concat(d.records) });
armarEvolucion(host, V11, d, 5, {});
out.pedidos1 = PEDIDOS.slice(); out.cargando = titulos(host);
await espera(); await espera();
out.vivos = VIVOS.size; out.creados = CREADOS; out.lista = titulos(host);
out.ejeX = [charts["evol-0"].options.scales.x.min, charts["evol-1"].options.scales.x.min];
out.leyenda = [charts["evol-0"].options.plugins.legend.display !== false, charts["evol-1"].options.plugins.legend.display !== false];
armarEvolucion(host, V11, d, 5, {}); out.pedidos2 = PEDIDOS.length; out.vivos2 = VIVOS.size;
// leyenda: apagar una serie la apaga en los dos paneles y sigue apagada al rearmar
charts["evol-0"].options.plugins.legend.onClick({}, { text: "MODIS", datasetIndex: charts["evol-0"].data.datasets.findIndex(x => x.label === "MODIS") }, { chart: charts["evol-0"] });
out.apagadaEnAmbos = ["evol-0", "evol-1"].map(k => charts[k].data.datasets.find(x => x.label === "MODIS").hidden);
armarEvolucion(host, V11, d, 5, {});
out.apagadaTrasRearmar = charts["evol-1"].data.datasets.find(x => x.label === "MODIS").hidden;
charts["evol-0"].options.plugins.legend.onClick({}, { text: "MODIS", datasetIndex: charts["evol-0"].data.datasets.findIndex(x => x.label === "MODIS") }, { chart: charts["evol-0"] });
// sensores y MIROVA apagados en la leyenda de arriba
sensorVisible.VIIRS750 = false; sensorVisible.MIROVA = false; armarEvolucion(host, V11, d, 5, {});
out.sinV750 = etiquetas("evol-1"); sensorVisible.VIIRS750 = true; sensorVisible.MIROVA = true;
// «Incluir lejanas»: rótulo del gris y tooltip con la mayúscula de «Incluir lejanas» intacta
includeFarDistance = true; armarEvolucion(host, V11, d, 5, {});
const gris = charts["evol-1"].data.datasets.find(x => x.fueraCrater);
out.grisLejanas = gris.label;
out.tooltip = charts["evol-1"].options.plugins.tooltip.callbacks.label({ raw: gris.data[0], dataset: gris, parsed: { y: gris.data[0].y } });
includeFarDistance = false;
// distancia: eje fijo 0 a 25 y lo de 32 km en el techo
evolModo = "dist"; armarEvolucion(host, V11, d, 5, {});
out.dist = [charts["evol-1"].options.scales.y.min, charts["evol-1"].options.scales.y.max,
            charts["evol-1"].data.datasets.find(x => x.fueraCrater).data.map(p => [p.y, !!p.recortada])];
evolModo = "log";
out.vivosFin = VIVOS.size;
console.log(JSON.stringify(out));
"""
    o = _arnes(tmp_path, cuerpo, _datos_d())
    assert o["pedidos1"] == ["data/mirova_equivalent/X.json"], o["pedidos1"]
    assert o["cargando"][1].endswith("(bajando la historia del volcán…)"), o["cargando"]
    assert o["vivos"] == 2 and o["creados"] == 4, o            # se redibujó al llegar la historia, sin fugas
    assert "bajando" not in o["lista"][1] and "datos desde el 2025-03-01" in o["lista"][1], o["lista"]
    assert "datos desde" not in o["lista"][0], o["lista"]      # los 2 meses están cubiertos por los datos
    ahora = int(datetime(2026, 11, 14, 12, tzinfo=timezone.utc).timestamp() * 1000)
    assert o["ejeX"] == [ahora - 60 * 86400000, ahora - 730 * 86400000], o["ejeX"]
    assert o["leyenda"] == [True, True]
    assert o["pedidos2"] == 1 and o["vivos2"] == 2             # una sola descarga por volcán y sesión
    assert o["apagadaEnAmbos"] == [True, True] and o["apagadaTrasRearmar"] is True
    assert "VIIRS 750m" not in o["sinV750"] and not any("MIROVA" in x for x in o["sinV750"]), o["sinV750"]
    assert o["grisLejanas"] == "Fuera del cráter (contada con «Incluir lejanas»)"
    assert o["tooltip"][1].endswith("fuera del cráter (contada con «Incluir lejanas»)"), o["tooltip"]
    assert o["dist"][0] == 0 and o["dist"][1] == 25 and o["dist"][2] == [[25, True]], o["dist"]
    assert o["vivosFin"] == 2


def test_armar_evolucion_fallo_sombra_y_otro_volcan(tmp_path):
    cuerpo = """
const d = DATOS; const out = {};
// JSON cortado: fetchJSON rechaza; el panel no queda «bajando» para siempre
FETCH = () => Promise.reject(new SyntaxError("JSON cortado"));
const h1 = mk("div"); armarEvolucion(h1, V11, d, 5, {}); await espera(); await espera();
out.fallo = titulos(h1)[1]; out.estado = _historiaEvol.X.estado;
// la sombra de los 34 no baja nada; su año dice desde cuándo hay datos
const n0 = PEDIDOS.length; currentVolcano = V34; const h2 = mk("div"); armarEvolucion(h2, V34, d, 5, {});
out.sombraPedidos = PEDIDOS.length - n0; out.sombra = titulos(h2);
// la historia llega cuando el operador ya abrió otro volcán: no se redibuja el bloque viejo
FETCH = () => Promise.resolve({ records: d.records });
const VY = Object.assign({}, V11, { name: "Y" }); currentVolcano = VY;
const h3 = mk("div"); armarEvolucion(h3, VY, d, 5, {}); const c0 = CREADOS;
currentVolcano = V11; await espera(); await espera();
out.redibujoAjeno = CREADOS - c0;
console.log(JSON.stringify(out));
"""
    o = _arnes(tmp_path, cuerpo, _datos_d())
    assert o["estado"] == "fallo" and "no se pudo bajar la historia" in o["fallo"], o
    assert o["sombraPedidos"] == 0
    assert "datos desde el 2026-11-10" in o["sombra"][1] and "datos desde" in o["sombra"][0], o["sombra"]
    assert o["redibujoAjeno"] == 0, o


# ── S184 tanda 2: cenit, última pasada, clases con Extremo, límite de detección, marcas de todas las pasadas ───────────

def test_todas_las_pasadas_y_sus_estados(tmp_path):
    casos = [
        _rec(dt="2026-11-01 05:00", dist=2.0, sensor_zenith_deg=12.0, sensor_azimuth_deg=-80.0),            # cráter
        _rec(dt="2026-11-01 06:00", dist=9.0, sensor_zenith_deg=51.0),                                     # fuera
        dict(_rec(dt="2026-11-01 07:00", vrp=30.0, t_max_k=250.0), n_anomalous_pixels=40),                 # artefacto cirrus
        {"datetime_utc": "2026-11-01 08:00", "sensor": "VIIRS_NOAA21", "n_anomalous_pixels": 0,
         "diag_codigo_mirova": {"motivo_vacio": "escena_invalida"}},
        {"datetime_utc": "2026-11-01 09:00", "sensor": "VIIRS_NOAA21", "n_anomalous_pixels": 0,
         "diag_codigo_mirova": {"motivo_vacio": "sunglint"}},
        {"datetime_utc": "2026-11-01 10:00", "sensor": "MODIS_AQUA", "n_anomalous_pixels": 0, "sensor_zenith_deg": 30},
        {"datetime_utc": "sin fecha", "sensor": "MODIS_AQUA"},
    ]
    cuerpo = """
const t = todasPasadasEvol(DATOS, 5);
console.log(JSON.stringify({ e: t.map(p => p.estado), zen: t.map(p => p.zen), azi: t[0].azi,
  igual: JSON.stringify(pasadasEvol(DATOS, 5)) === JSON.stringify(t.filter(p => p.y > 0)),
  marcas: marcasEvol(t).map(m => m.estado) }));
"""
    o = _node(tmp_path, cuerpo, casos)
    assert o["e"] == ["crater", "fuera", "no_publicada", "sin_datos", "reflejo", "nada"], o["e"]
    assert o["zen"] == [12.0, 51.0, None, None, None, 30] and o["azi"] == -80.0
    assert o["igual"] is True
    # las marcas son sólo las pasadas sin palito
    assert o["marcas"] == ["no_publicada", "sin_datos", "reflejo", "nada"], o["marcas"]


def test_cenit_oblicuo_y_texto(tmp_path):
    o = _node(tmp_path, "console.log(JSON.stringify([esOblicuaEvol(40), esOblicuaEvol(40.5), esOblicuaEvol(null), "
              "textoCenitEvol(51.4, -85.2), textoCenitEvol(12, null), textoCenitEvol(undefined, 3), EVOL_CENIT_OBLICUO]));")
    assert o == [False, True, False, "cenit 51°, azimut -85°", "cenit 12°", None, 40], o


def test_ultima_pasada(tmp_path):
    cuerpo = """
const P = (t, estado, y, zen) => ({ t, dt: "D" + t, estado, y, zen, grupo: "VIIRS375", sensor: "VIIRS_NOAA21" });
const H = 3600000, A = 100 * H;
const base = [P(1 * H, "crater", 3, 20), P(2 * H, "fuera", 2, 50), P(3 * H, "sin_datos"), P(4 * H, "reflejo")];
const u1 = ultimaPasadaEvol(base, false), u2 = ultimaPasadaEvol(base, true);
const u3 = ultimaPasadaEvol([P(1 * H, "crater", 3, 20), P(2 * H, "nada", undefined, 61)], false);
console.log(JSON.stringify({
  u1: [u1.p.t / H, u1.vrp], u2: [u2.p.t / H, u2.vrp], u3: [u3.p.estado, u3.vrp],
  vacia: ultimaPasadaEvol([P(1 * H, "sin_datos")], false),
  t1: textoUltimaPasadaEvol(u1, A, false), t2: textoUltimaPasadaEvol(u2, A, true),
  t3: textoUltimaPasadaEvol(u3, A, false), t4: textoUltimaPasadaEvol(null, A, false),
  t5: textoUltimaPasadaEvol(ultimaPasadaEvol([P(99 * H, "crater", 25, 10)], false), A, false),
  hace: [haceEvol(A - 5 * 60000, A), haceEvol(A - 6 * H, A), haceEvol(A - 72 * H, A), haceEvol(A + 1000, A), haceEvol(A - 30 * H, A)] }));
"""
    o = _node(tmp_path, cuerpo)
    # las escenas sin datos y de reflejo no son «última pasada» (como la tarjeta, S183)
    assert o["u1"] == [2, 0] and o["u2"] == [2, 2] and o["vacia"] is None, o
    assert o["u3"] == ["nada", 0]
    assert o["t1"]["clave"] == "nd" and "anomalía fuera del cráter, no publicada" in o["t1"]["texto"], o["t1"]
    assert "cenit 50°" in o["t1"]["texto"] and "(oblicua)" in o["t1"]["texto"] and "hace 4 días" in o["t1"]["texto"]
    assert o["t2"]["clave"] == "low" and "Bajo, 2,00 MW" in o["t2"]["texto"], o["t2"]
    assert o["t3"]["clave"] == "nd" and "sin anomalía" in o["t3"]["texto"] and "cenit 61° (oblicua)" in o["t3"]["texto"]
    assert o["t4"]["clave"] == "nd" and "sin pasadas medidas" in o["t4"]["texto"]
    assert o["t5"]["clave"] == "mod" and "VIIRS 375" in o["t5"]["texto"] and "(oblicua)" not in o["t5"]["texto"]
    assert o["hace"] == ["hace 5 min", "hace 6 h", "hace 3 días", "hace 0 min", "hace 30 h"], o["hace"]


def test_clases_del_grafico_con_extremo(tmp_path):
    cuerpo = """
const c = clasesGraficoEvol(LEVELS);
console.log(JSON.stringify({ c: c.map(k => [k.desde, k.hasta === Infinity ? "inf" : k.hasta, k.rotulo, k.color]),
  nivel: getLevel(20000).label, base: clasesEscalaEvol(LEVELS).length }));
"""
    o = _node(tmp_path, cuerpo)
    c = o["c"]
    assert [k[0] for k in c] == [0, 1, 10, 100, 1000, 10000], c
    assert c[4][1] == 10000 and c[5] == [10000, "inf", "Extremo (MIROVA)", "#e040fb"], c
    assert [k[3] for k in c[1:]] == ["#2ecc40", "#ffdc00", "#ff851b", "#ff4136", "#e040fb"] and c[0][3] is None
    # sólo el gráfico: getLevel y la escala del tablero no cambian
    assert o["nivel"] == "Muy Alto" and o["base"] == 5


def test_datasets_forma_relleno_y_estrella(tmp_path):
    pts = [
        {"t": 1, "grupo": "VIIRS375", "y": 2.0, "enCrater": True, "dist": 1.0, "zen": 20, "sensor": "VIIRS_NOAA21"},
        {"t": 2, "grupo": "VIIRS375", "y": 3.0, "enCrater": True, "dist": 1.0, "zen": 55, "sensor": "VIIRS_NOAA21"},
        {"t": 3, "grupo": "VIIRS750", "y": 1.0, "enCrater": False, "dist": 12.0, "zen": 10, "sensor": "VIIRS_NOAA20_750"},
    ]
    cuerpo = """
const f = ds => ds.map(d => ({ label: d.label, n: d.data.length,
  forma: d.data.map(x => typeof d.pointStyle === "function" ? d.pointStyle({ raw: x }) : d.pointStyle),
  relleno: d.data.map(x => typeof d.pointBackgroundColor === "function" ? d.pointBackgroundColor({ raw: x }) : d.pointBackgroundColor) }));
console.log(JSON.stringify({
  con: f(datasetsEvol(DATOS, [], "log", false, null, DATOS[1])),
  sinAnomalia: f(datasetsEvol(DATOS, [], "log", false, null, { t: 9, y: undefined })),
  // la última pasada no vio nada pero cae a la misma hora que una pasada con anomalía de otro satélite: sin estrella
  mismaHora: f(datasetsEvol(DATOS, [], "log", false, null, { t: 1, y: undefined })),
  fueraVentana: f(datasetsEvol(DATOS, [], "log", false, null, { t: 99, y: 5, dist: 1 })),
  dist: f(datasetsEvol(DATOS, [], "dist", false, 25, DATOS[2])) }));
"""
    o = _node(tmp_path, cuerpo, pts)
    con = {d["label"]: d for d in o["con"]}
    assert con["VIIRS 375m"]["forma"] == ["circle", "circle"]
    assert con["VIIRS 375m"]["relleno"] == ["#e91e63", "rgba(0,0,0,0)"]          # la de 55° va hueca
    assert con["Fuera del cráter: no publicada"]["forma"] == ["rect"]
    assert con["★ Última pasada"]["n"] == 1 and con["★ Última pasada"]["forma"] == ["star"]
    assert not any(d["label"].startswith("★") for d in o["sinAnomalia"] + o["fueraVentana"] + o["mismaHora"])
    assert any(d["label"].startswith("★") for d in o["dist"])


def test_armar_evolucion_tanda2(tmp_path):
    cuerpo = """
const d = DATOS; const out = {}; currentVolcano = V34;
const tiene = (host, cls) => { let x = null; const rec = n => { if ((n.className || "").split(" ").includes(cls)) x = x || n; (n.children || []).forEach(rec); }; rec(host); return x; };
const h = mk("div"); armarEvolucion(h, V34, d, 5, {});
out.caja = tiene(h, "evol-ultima"); out.caja = [out.caja.className, out.caja.textContent];
out.cenit = !!tiene(h, "evol-cenit");
const o0 = charts["evol-0"].options.plugins.lineasEvol;
out.comb = [o0.limiteMw, o0.clases.length, o0.marcas.length];
detailSensor = "VIIRS375"; armarEvolucion(h, V34, d, 5, {});
out.v375 = charts["evol-0"].options.plugins.lineasEvol.limiteMw;
evolModo = "dist"; armarEvolucion(h, V34, d, 5, {});
out.dist = [charts["evol-0"].options.plugins.lineasEvol.limiteMw, charts["evol-0"].options.plugins.lineasEvol.clases];
evolModo = "log"; detailSensor = "COMB";
const ds = charts["evol-1"].data.datasets; const v = ds.find(x => x.label === "VIIRS 375m");
out.tooltip = charts["evol-1"].options.plugins.tooltip.callbacks.label({ raw: v.data[0], dataset: v, parsed: { y: v.data[0].y } });
console.log(JSON.stringify(out));
"""
    datos = _datos_d()
    datos["records"].append({"datetime_utc": "2026-11-12 08:00", "sensor": "MODIS_AQUA", "n_anomalous_pixels": 0,
                             "sensor_zenith_deg": 58.0})
    datos["records"].append({"datetime_utc": "2026-11-12 09:00", "sensor": "VIIRS_NOAA21", "n_anomalous_pixels": 0,
                             "diag_codigo_mirova": {"motivo_vacio": "escena_invalida"}})
    datos["records"][1]["sensor_zenith_deg"] = 47.0
    datos["records"][1]["sensor_azimuth_deg"] = 101.0
    o = _arnes(tmp_path, cuerpo, datos)
    # la última pasada medida es la MODIS de las 08:00 (sin anomalía, oblicua); la escena sin datos de las 09:00 no cuenta
    assert o["caja"][0] == "evol-ultima evol-ultima-nd", o["caja"]
    assert "2026-11-12 08:00 UTC" in o["caja"][1] and "sin anomalía" in o["caja"][1] and "cenit 58° (oblicua)" in o["caja"][1]
    assert o["cenit"] is True
    # combinado: sin línea de límite (cada sensor tiene la suya); clases con Extremo; marcas de las dos pasadas sin palito
    assert o["comb"] == [None, 6, 2], o["comb"]
    assert o["v375"] == 0.01 and o["dist"] == [None, None]
    assert o["tooltip"][-1] == "  cenit 47°, azimut 101° · mirada oblicua: una fuente chica puede no verse o verse menor", o["tooltip"]


def test_tabla_de_pasadas_con_cenit():
    src = INDEX.read_text(encoding="utf-8")
    rd = _fuente(src, "renderDetail")
    assert '{label: "Cenit", title:' in rd
    assert rd.count("celdaCenit(tdZ, r); row.appendChild(tdZ);") == 2      # filas con y sin anomalía
    assert "td.colSpan = 9;" in rd and "td.colSpan = 8;" not in rd


def test_nota_del_cenit_dice_lo_medido():
    src = INDEX.read_text(encoding="utf-8")
    nota = _const(src, "NOTA_CENIT_EVOL")
    for frase in ["68 %", "17 %", "0,81 a 0,14 MW", "0,73 a 0,14 MW", "no separan", "Chillán"]:
        assert frase in nota, frase
    assert "\u2014" not in nota and "\u2013" not in nota
    assert (RAIZ / "experiments" / "_s184_cenit" / "INFORME.md").exists()


# ── Revisión S185 de #1011 (2026-11-15) ──────────────────────────────────────────────────────────────────────────────

def test_s185_historia_cargando_reintento_y_mirova_desde(tmp_path):
    cuerpo = """
const d = DATOS; const out = {};
allData = { X: { mirovaRecords: [{ datetime_utc: "2026-11-01 00:00" }] }, Z: { mirovaRecords: [{ datetime_utc: "2026-11-05 00:00" }] } };
let resolver; FETCH = () => new Promise(r => { resolver = r; });
const h = mk("div"); armarEvolucion(h, V11, d, 5, {});
out.cargando = titulos(h);                       // mientras baja: sin «datos desde» (no se sabe dónde empiezan)
resolver(null); await espera(); await espera();
out.fallo = [_historiaEvol.X.estado, titulos(h)[1]];
const n0 = PEDIDOS.length; armarEvolucion(h, V11, d, 5, {}); out.sinReintento = PEDIDOS.length - n0;   // antes del minuto
_historiaEvol.X.reintentarMs = 0; FETCH = () => Promise.resolve({ records: d.records });
armarEvolucion(h, V11, d, 5, {}); out.reintento = PEDIDOS.length - n0;
await espera(); await espera(); out.lista = [_historiaEvol.X.estado, titulos(h)];
console.log(JSON.stringify(out));
"""
    o = _arnes(tmp_path, cuerpo, _datos_d())
    assert not any("datos desde" in t for t in o["cargando"]), o["cargando"]
    assert "MIROVA desde el 2026-11-01" in o["cargando"][1], o["cargando"]
    assert o["fallo"][0] == "fallo" and "datos desde" not in o["fallo"][1] and "no se pudo" in o["fallo"][1], o["fallo"]
    assert o["sinReintento"] == 0 and o["reintento"] == 1, o
    assert o["lista"][0] == "lista" and "datos desde el 2026-11-10" in o["lista"][1][1], o["lista"]


def test_s185_serie_gris_con_clave_estable(tmp_path):
    cuerpo = """
const d = DATOS; const out = {}; currentVolcano = V34;
const h = mk("div"); armarEvolucion(h, V34, d, 5, {});
const gris = k => charts[k].data.datasets.find(x => x.fueraCrater);
const i = charts["evol-1"].data.datasets.indexOf(gris("evol-1"));
charts["evol-1"].options.plugins.legend.onClick({}, { text: gris("evol-1").label, datasetIndex: i }, { chart: charts["evol-1"] });
out.antes = ["evol-0", "evol-1"].map(k => gris(k).hidden);
includeFarDistance = true; armarEvolucion(h, V34, d, 5, {});
out.despues = [gris("evol-1").label, gris("evol-1").hidden];
includeFarDistance = false;
console.log(JSON.stringify(out));
"""
    o = _arnes(tmp_path, cuerpo, _datos_d())
    assert o["antes"] == [True, True], o
    assert o["despues"] == ["Fuera del cráter (contada con «Incluir lejanas»)", True], o


def test_s185_una_sola_cadena_de_distancia():
    src = INDEX.read_text(encoding="utf-8")
    assert "const dist = distanciaDePasada(r) ?? r.vent_hotspot_dist_km;" in _fuente(src, "renderDetail")
    assert "const honestDist = (r) => distanciaDePasada(r);" in src
    # fuera de distanciaDePasada no queda ninguna copia de la cadena
    sin_funcion = src.replace(_fuente(src, "distanciaDePasada"), "")
    assert "?? r.hotspot_dist_km ?? r.final_hotspot_dist_km" not in sin_funcion
    assert not re.search(r"\?\?\s*r\.hotspot_dist_km\s*\n\s*\?\?\s*r\.final_hotspot_dist_km", sin_funcion)


# ── Verificador de la tanda 2 (2026-11-15): empates de hora, última con calor, límites, dibujo de rayas y límite ──────

def test_ultima_pasada_empates_y_ultima_con_calor(tmp_path):
    cuerpo = """
const P = (t, estado, y, grupo, dt) => ({ t, dt: dt || ("D" + t), estado, y, grupo, sensor: grupo, zen: 30 });
const M = 60000, H = 60 * M, A = 100 * H;
// misma hora: la de 375 vio 1,857 MW en el cráter y la de 750 nada; el archivo trae primero la 375
const empate = [P(10 * H, "crater", 1.857, "VIIRS375"), P(10 * H, "nada", undefined, "VIIRS750")];
// dos gránulos de la misma pasada a 6 min: el primero con calor, el segundo sin
const granulos = [P(10 * H, "crater", 3, "VIIRS375"), P(10 * H + 6 * M, "nada", undefined, "VIIRS375")];
// a 50 min ya es otra pasada: manda la última aunque no vea nada
const otra = [P(10 * H, "crater", 3, "VIIRS375"), P(10 * H + 50 * M, "nada", undefined, "MODIS")];
const fuera = [P(10 * H, "fuera", 9, "VIIRS750"), P(10 * H, "crater", 0.5, "VIIRS375")];
const u = (l, f) => { const x = ultimaPasadaEvol(l, f); return [x.p.grupo, x.p.estado, x.vrp]; };
const conCalor = ultimaConCalorEvol(otra, false);
console.log(JSON.stringify({ empate: u(empate, false), empateInv: u(empate.slice().reverse(), false), granulos: u(granulos, false),
  otra: u(otra, false), fueraSolo: u(fuera, false), fueraLejanas: u(fuera, true),
  conCalor: [conCalor.p.grupo, conCalor.vrp], sinCalor: ultimaConCalorEvol([P(1, "nada")], false),
  texto: textoUltimaPasadaEvol(ultimaPasadaEvol(otra, false), A, false, conCalor).texto,
  textoConCalorIgual: textoUltimaPasadaEvol(ultimaPasadaEvol(granulos, false), A, false, ultimaConCalorEvol(granulos, false)).texto,
  extremo: textoUltimaPasadaEvol({ p: P(1, "crater", 12000, "MODIS"), vrp: 12000 }, A, false).texto }));
"""
    o = _node(tmp_path, cuerpo)
    assert o["empate"] == ["VIIRS375", "crater", 1.857] and o["empateInv"] == ["VIIRS375", "crater", 1.857], o
    assert o["granulos"] == ["VIIRS375", "crater", 3] and o["otra"] == ["MODIS", "nada", 0], o
    # con «Solo cráter» manda el cráter (0,5 publicado); con «Incluir lejanas», el de fuera (9 MW)
    assert o["fueraSolo"] == ["VIIRS375", "crater", 0.5] and o["fueraLejanas"] == ["VIIRS750", "fuera", 9], o
    assert o["conCalor"] == ["VIIRS375", 3] and o["sinCalor"] is None
    assert "sin anomalía" in o["texto"] and ". Última con calor publicado: D36000000 UTC" in o["texto"] and "Bajo, 3,00 MW" in o["texto"], o["texto"]
    assert "Última con calor" not in o["textoConCalorIgual"], o["textoConCalorIgual"]
    assert "Muy Alto (Extremo en la escala de MIROVA), 12000,00 MW" in o["extremo"], o["extremo"]


def test_limites_por_sensor_en_la_pagina(tmp_path):
    cuerpo = """
const d = DATOS; const out = {}; currentVolcano = V34; const h = mk("div");
for (const s of ["MODIS", "VIIRS750", "VIIRS375", "COMB"]) { detailSensor = s; armarEvolucion(h, V34, d, 5, {});
  out[s] = charts["evol-0"].options.plugins.lineasEvol.limiteMw ?? null; }
detailSensor = "COMB"; console.log(JSON.stringify(out));
"""
    o = _arnes(tmp_path, cuerpo, _datos_d())
    assert o == {"MODIS": 1, "VIIRS750": 0.1, "VIIRS375": 0.01, "COMB": None}, o


def test_dibujo_de_rayas_y_limite(tmp_path):
    cuerpo = """
const llamadas = [];
const ctx = { save() {}, restore() {}, setLineDash() {}, beginPath() {}, moveTo() {}, lineTo() {}, stroke() {},
  fillRect(x, y, w, h) { llamadas.push(["rect", this.fillStyle, Math.round(x), y, h]); },
  fillText(t, x, y) { llamadas.push(["text", t]); } };
const esc = (min, max, px0, px1) => ({ min, max, type: "linear", getPixelForValue: v => px0 + (v - min) / (max - min) * (px1 - px0) });
const chart = { ctx, chartArea: { left: 0, right: 100, top: 10, bottom: 110 }, scales: { x: esc(0, 100, 0, 100), y: esc(0, 10, 110, 10) } };
lineasEvolPlugin.beforeDatasetsDraw(chart, {}, { marcas: [{ t: 10, estado: "sin_datos" }, { t: 20, estado: "reflejo" },
  { t: 30, estado: "nada" }, { t: 40, estado: "no_publicada" }, { t: 500, estado: "nada" }], limiteMw: 0.5 });
console.log(JSON.stringify(llamadas));
"""
    o = _node(tmp_path, cuerpo)
    rects = [c for c in o if c[0] == "rect"]
    # fila de arriba (y = top) lo que no se pudo medir; fila de abajo (y = top + 6) lo medido sin palito; la de t=500 cae fuera
    assert rects == [["rect", "#ffffff", 9, 10, 5], ["rect", "#ffc400", 19, 10, 5],
                     ["rect", "rgba(150,160,175,0.6)", 29, 16, 5], ["rect", "#5dade2", 39, 16, 5]], rects
    assert ["text", "límite de detección ~0,5 MW (MIROVA)"] in o, o


def test_nota_del_cenit_sin_generalizar():
    src = INDEX.read_text(encoding="utf-8")
    nota = "".join(re.findall(r'"([^"]*)"', _const(src, "NOTA_CENIT_EVOL")))   # el texto unido, sin los cortes de línea
    for frase in ["gradual", "56 %", "en Isluga se mantiene", "no baja ni la fracción ni el VRP", "área del píxel en el nadir",
                  "no está medido aparte"]:
        assert frase in nota, frase
    assert "Isluga, Lastarria y Planchón-Peteroa caen igual" not in nota
    assert "VRP puede salir más bajo" not in src and "VRP tiende a salir más bajo" not in src
