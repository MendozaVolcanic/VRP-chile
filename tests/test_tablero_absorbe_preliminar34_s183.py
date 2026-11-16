# -*- coding: utf-8 -*-
"""S183 (2026-11-13): el tablero principal absorbe lo único que hacía frontend/preliminar_34.html y él no.

POR QUÉ. Desde #992 los 34 volcanes sin MIROVA están en la página principal y la página aparte sobraba, salvo por dos
cosas que el tablero no hacía (Nicolás aprobó pasarlas y sacar la pestaña):
1. Un píxel alertado a 5 km o menos del volcán cuando el centroide del cúmulo está lejos. El valor publicado sigue el
   centroide, como MIROVA, así que esa pasada se lee «fuera» o «anomalía no publicada», y justo es actividad en el
   cráter. Caso real: Carrán-Los Venados, 2026-11-12 05:36 UTC, VIIRS_NOAA21, 0,65 MW, píxel a 1,8 km, centroide a
   20,6 km. Es sólo un rótulo: no cambia mirovaEqVrp ni ningún valor publicado (usar el píxel para el valor lo decide
   Nicolás aparte).
2. El mismo foco visto desde dos volcanes vecinos (grillas de unos 50 km que se traslapan): sin la marca, el operador
   lee dos anomalías donde hay una.
Más dos filtros del selector de orden, «sólo los 34» y «sólo los 11».

QUÉ FIJA, ejecutando en node las funciones reales de frontend/index.html: el rótulo (sintético y el caso real de
Carrán), que no toca el record ni el valor, el foco compartido (sintético y los datos de hoy), los filtros sin perder
ni duplicar tarjetas, que la página los usa y que la página aparte ya no existe.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría si el código estuviera mal? Cada caso tiene su control negativo
(píxel lejos, centroide ya en cumbre, otra hora, otro sensor, a 9 km, un volcán de los 11). (2) ¿Y si la extracción
muriera? `_fuente` lanza si no encuentra la función y node falla con mensaje si el código no corre.
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

FUNCIONES = ["distanciaKmSombra", "pixelEnCumbreSombra", "textoPixelEnCumbre", "ultimoPixelEnCumbre",
             "focosCompartidosSombra", "parseUtcMs"]


def _constante(src, nombre):
    """Valor numérico de `const nombre = N;` tal como está en index.html (verificador S183, H2: antes la prueba
    inyectaba sus propias constantes y un cambio del radio en la página pasaba sin ruido)."""
    m = re.search(r"^const " + re.escape(nombre) + r" = ([0-9.]+);", src, re.M)
    if not m:
        raise AssertionError("no encontré la constante " + nombre)
    return float(m.group(1))


_SRC = INDEX.read_text(encoding="utf-8")
CONSTANTES = "".join("const %s = %s;\n" % (n, _constante(_SRC, n)) for n in ("RADIO_CUMBRE_SOMBRA_KM", "KM_MISMO_FOCO_SOMBRA"))


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


def _node(tmp_path, cuerpo, datos, nombres=FUNCIONES, previo=CONSTANTES):
    src = INDEX.read_text(encoding="utf-8")
    js = previo + "\n".join(_fuente(src, n) for n in nombres) + "\nconst DATOS = " + json.dumps(datos) + ";\n" + cuerpo
    f = tmp_path / "t.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


SOMBRA = {"name": "X", "display": "Equis", "lat": -30.0, "lon": -70.0, "fuente": "sombra_34", "hasMirova": False}


def _rec(**k):
    base = {"datetime_utc": "2026-11-12 05:36", "sensor": "VIIRS_NOAA21", "vrp_mw": 0.65,
            "primary_cluster": {"centroid_dist_km": 20.6, "vrp_mw": 0.65},
            "anomaly_pixels": [{"lat": -30.01, "lon": -70.0}, {"lat": -30.185, "lon": -70.0}]}
    base.update(k)
    return base


def test_pixel_en_cumbre_con_centroide_lejos_y_sus_controles(tmp_path):
    casos = [
        [_rec(), SOMBRA],                                                                     # sí: píxel a 1,1 km
        [_rec(anomaly_pixels=[{"lat": -30.185, "lon": -70.0}]), SOMBRA],                       # píxel lejos
        [_rec(primary_cluster={"centroid_dist_km": 3.0, "vrp_mw": 0.65}), SOMBRA],             # ya es de cumbre
        [_rec(vrp_mw=0), SOMBRA],                                                              # sin detección
        [_rec(), dict(SOMBRA, fuente=None, hasMirova=True)],                                  # uno de los 11
        [_rec(anomaly_pixels=[{"lat": None, "lon": -70.0}, {"lat": -30.03, "lon": -70.0}]), SOMBRA],  # sin posición
        [_rec(primary_cluster=None, final_hotspot_dist_km=20.6), SOMBRA],                      # sin cúmulo
        [_rec(anomaly_pixels=[{"lat": -30.0405, "lon": -70.0}]), SOMBRA],                      # 4,5 km: dentro
        [_rec(anomaly_pixels=[{"lat": -30.0504, "lon": -70.0}]), SOMBRA],                      # 5,6 km: fuera
        # el `dist_km` del píxel no manda: se mide desde las coordenadas del volcán (A3)
        [_rec(anomaly_pixels=[{"lat": -30.01, "lon": -70.0, "dist_km": 30.0}]), SOMBRA],
        [_rec(anomaly_pixels=[{"lat": -30.185, "lon": -70.0, "dist_km": 0.5}]), SOMBRA],
    ]
    cuerpo = """
const out = DATOS.map(([r, v]) => { const m = pixelEnCumbreSombra(r, v); return m ? [Math.round(m.pixel_km * 100) / 100, m.centroide_km, textoPixelEnCumbre(m)] : null; });
process.stdout.write(JSON.stringify(out));
"""
    out = _node(tmp_path, cuerpo, casos)
    assert out[0] == [1.11, 20.6, "píxel a 1,1 km de la cumbre"], out
    assert out[1] is None and out[2] is None and out[3] is None and out[4] is None, out
    assert out[5][0] == 3.34, out
    assert out[6][1] == 20.6, out
    assert out[7][2] == "píxel a 4,5 km de la cumbre" and out[8] is None, out
    assert out[9][0] == 1.11 and out[10] is None, out


def test_los_umbrales_de_la_pagina():
    """5 km es la cumbre D5 (la de los KML de MIROVA más usada); 1 km, unos dos píxeles de 375 m. Si cambian, que sea
    a propósito y cambiando esta prueba."""
    assert _constante(_SRC, "RADIO_CUMBRE_SOMBRA_KM") == 5
    assert _constante(_SRC, "KM_MISMO_FOCO_SOMBRA") == 1


def test_el_rotulo_no_toca_el_record(tmp_path):
    """Es sólo un rótulo: ni el record ni el valor publicado cambian al calcularlo."""
    cuerpo = """
const r = DATOS; const antes = JSON.stringify(r);
const v0 = mirovaEqVrp(r, 5, false);
pixelEnCumbreSombra(r, { lat: -30, lon: -70, fuente: "sombra_34" });
ultimoPixelEnCumbre([r], { lat: -30, lon: -70, fuente: "sombra_34" }, 0);
process.stdout.write(JSON.stringify({ igual: JSON.stringify(r) === antes, v0, v1: mirovaEqVrp(r, 5, false) }));
"""
    out = _node(tmp_path, cuerpo, _rec(), nombres=FUNCIONES + ["mirovaEqVrp"])
    assert out == {"igual": True, "v0": 0, "v1": 0}, out


def test_ultimo_pixel_en_cumbre_respeta_la_ventana(tmp_path):
    regs = [_rec(datetime_utc="2026-11-12 05:36"), _rec(datetime_utc="2026-11-12 07:10", vrp_mw=0),
            _rec(datetime_utc="2026-11-08 05:00"), _rec(datetime_utc="2026-11-12 03:00")]
    cuerpo = """
const v = %s;
const a = ultimoPixelEnCumbre(DATOS, v, Date.UTC(2026, 10, 11, 12, 0));
const b = ultimoPixelEnCumbre(DATOS, v, Date.UTC(2026, 10, 12, 6, 0));
process.stdout.write(JSON.stringify({ a: a && a.r.datetime_utc, b }));
""" % json.dumps(SOMBRA)
    assert _node(tmp_path, cuerpo, regs) == {"a": "2026-11-12 05:36", "b": None}


def _det(volcan, lat, **k):
    r = {"datetime_utc": "2026-11-07 05:24", "sensor": "VIIRS_NOAA21", "vrp_mw": 1.0,
         "final_hotspot_lat": lat, "final_hotspot_lon": -69.09}
    r.update(k)
    return volcan, r


def test_foco_compartido_sintetico(tmp_path):
    vs = [{"name": n, "display": n + " d", "fuente": "sombra_34"} for n in ("G", "P", "Lejos", "Tarde", "Otro", "Cero")]
    vs.append({"name": "T11", "display": "Tier A", "hasMirova": True})
    datos = {}
    for n, r in [_det("G", -18.42), _det("P", -18.421), _det("Lejos", -18.50), _det("Tarde", -18.42, datetime_utc="2026-11-07 06:24"),
                 _det("Otro", -18.42, sensor="VIIRS_NOAA20"), _det("Cero", -18.42, vrp_mw=0), _det("T11", -18.42)]:
        datos.setdefault(n, {"records": []})["records"].append(r)
    cuerpo = """
const m = focosCompartidosSombra(DATOS.vs, DATOS.datos);
process.stdout.write(JSON.stringify(Object.fromEntries([...m.entries()])));
"""
    out = _node(tmp_path, cuerpo, {"vs": vs, "datos": datos})
    assert out == {"G|2026-11-07 05:24|VIIRS_NOAA21": ["P d"], "P|2026-11-07 05:24|VIIRS_NOAA21": ["G d"]}, out


def _sombra_real():
    """{volcán: records} de data/sombra_34 en origin/main (lo que lee la página). Sin esa ref (un checkout de CI de
    un PR no siempre la trae, verificador S183 H3), cae a data/sombra_34 del árbol, que es la misma carpeta."""
    ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", "origin/main", "data/sombra_34/"], cwd=RAIZ,
                        capture_output=True, text=True)
    nombres = [x for x in ls.stdout.split() if x.endswith(".json")]
    if not ls.returncode and nombres:
        return {Path(n).stem: json.loads(subprocess.run(["git", "show", "origin/main:" + n], cwd=RAIZ,
                                                          capture_output=True).stdout).get("records", []) for n in nombres}
    arch = sorted((RAIZ / "data" / "sombra_34").glob("*.json"))
    if not arch:
        pytest.skip("sin data/sombra_34 ni en origin/main ni en el árbol")
    return {a.stem: json.loads(a.read_text(encoding="utf-8")).get("records", []) for a in arch}


def _volcanes_de_la_pagina(tmp_path):
    """Los 45 tal como los arma index.html (VOLCANOES_ALL y VOLCANOES), evaluados en node."""
    m = re.search(r"const VOLCANOES_ALL = \[.*?\n\];", _SRC, re.S)
    assert m, "no encontré VOLCANOES_ALL"
    linea = re.search(r"^const VOLCANOES = VOLCANOES_ALL\.map[^\n]*", _SRC, re.M).group(0)
    return _node(tmp_path, "process.stdout.write(JSON.stringify(VOLCANOES));", None, nombres=[],
                 previo=m.group(0) + "\n" + linea + "\n")


def test_los_34_de_la_pagina_estan_donde_los_pone_el_pipeline(tmp_path):
    """El rótulo mide desde las coordenadas del volcán de la página y el centroide con que se compara lo midió el
    pipeline desde volcanoes.yaml: tienen que ser el mismo punto. Laguna del Maule estaba a 8,2 km (verificador S183,
    H1). Reemplaza la prueba de la lista de los 34 que tenía la página aparte."""
    import yaml
    todos = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    pagina = _volcanes_de_la_pagina(tmp_path)
    sombra = [v for v in pagina if v.get("fuente") == "sombra_34"]
    assert {v["name"] for v in sombra} == {n for n, v in todos.items() if v["radius_km"] != 25}
    lejos = [(v["name"], v["lat"], v["lon"]) for v in sombra
             if abs(v["lat"] - todos[v["name"]]["lat"]) > 1e-6 or abs(v["lon"] - todos[v["name"]]["lon"]) > 1e-6]
    assert not lejos, lejos


def test_datos_reales_carran_y_focos_compartidos(tmp_path):
    datos = _sombra_real()
    vs = [v for v in _volcanes_de_la_pagina(tmp_path) if v.get("fuente") == "sombra_34"]
    assert len(vs) == 34
    cuerpo = """
const { vs, datos } = DATOS;
const carran = vs.find(v => v.name === "CarranLosVenados");
const rotulos = datos.CarranLosVenados.filter(r => r.datetime_utc.startsWith("2026-11-12 05:36"))
  .map(r => { const m = pixelEnCumbreSombra(r, carran); return [r.sensor, m ? textoPixelEnCumbre(m) : null, m ? m.centroide_km : null]; });
const m = focosCompartidosSombra(vs, Object.fromEntries(Object.entries(datos).map(([k, recs]) => [k, { records: recs }])));
let n = 0; for (const v of vs) for (const r of datos[v.name] || []) if (r.vrp_mw > 0 && Number.isFinite(r.final_hotspot_lat)) n++;
process.stdout.write(JSON.stringify({ rotulos, compartidas: m.size, n }));
"""
    out = _node(tmp_path, cuerpo, {"vs": vs, "datos": datos})
    rot = {s: (t, c) for s, t, c in out["rotulos"]}
    assert rot["VIIRS_NOAA21"] == ("píxel a 1,8 km de la cumbre", 20.601), out["rotulos"]
    assert rot["VIIRS_NOAA21_750"] == (None, None), "su centroide ya está a 1,8 km: el rótulo no agrega nada"
    # 10 de 49 el 2026-11-13; el corpus crece (A90): se exige que haya y que sea una parte, no el número exacto
    assert 10 <= out["compartidas"] < out["n"] and out["n"] >= 49, out


def test_filtros_solo_34_y_solo_11(tmp_path):
    vs = [{"name": "A", "lat": -20.0, "hasMirova": False}, {"name": "B", "lat": -40.0, "hasMirova": True},
          {"name": "C", "lat": -30.0, "hasMirova": True}, {"name": "D", "lat": -18.0, "hasMirova": False}]
    cuerpo = """
const o = k => ordenarVolcanes(DATOS, k, v => 0).map(v => v.name).join("");
process.stdout.write(JSON.stringify({ s34: o("solo34"), s11: o("solo11"), todos: o("ns"), intacta: DATOS.map(v => v.name).join("") }));
"""
    out = _node(tmp_path, cuerpo, vs, nombres=["ordenarVolcanes"], previo="")
    assert out == {"s34": "DA", "s11": "CB", "todos": "DACB", "intacta": "ABCD"}, out
    assert sorted(out["s34"] + out["s11"]) == sorted(out["todos"])


def test_la_pagina_usa_las_funciones_y_ofrece_los_filtros():
    src = INDEX.read_text(encoding="utf-8")
    assert re.search(r'const ORDENES_TARJETAS = \[[^\]]*"solo34"[^\]]*"solo11"', src)
    assert '<option value="solo34">' in src and '<option value="solo11">' in src
    # Cadenas exactas (verificador S183, H2): con subcadenas sueltas, quitar el rótulo de una fila o de la tarjeta, o
    # la ventana de 48 h, pasaba sin ruido. La lógica se prueba en node; aquí, que la página la cablea.
    cards = _fuente(src, "buildCards")
    assert "ultimoPixelEnCumbre(d.records.filter(r => isSensorVisible(r)), v, Date.now() - 48 * 3600000)" in cards
    assert "if (pcEl) card.appendChild(pcEl);" in cards
    detalle = _fuente(src, "renderDetail")
    assert 'const compartidos34 = v.fuente === "sombra_34" ? focosCompartidosSombra(VOLCANOES, allData) : null;' in detalle
    assert "const marca34 = marcaSombra34(r, v, compartidos34);" in detalle
    assert "if (i === 2 && marca34) td.appendChild(marca34);" in detalle            # fila sin anomalía publicada (Carrán)
    assert "if (marca34) td.appendChild(marca34); }" in detalle                     # fila con detección publicada
    assert "pixelEnCumbreSombra(" in _fuente(src, "marcaSombra34")
    # un filtro no se recuerda en el navegador: al volver se ven los 45 (verificador S183, H4)
    assert 'const ORDEN_ES_FILTRO = o => o === "solo34" || o === "solo11";' in src
    assert "ORDENES_TARJETAS.includes(o) && !ORDEN_ES_FILTRO(o) ? o : \"ns\"" in src
    assert "if (!ORDEN_ES_FILTRO(ordenTarjetas)) { try { localStorage.setItem(" in src


def test_la_marca_de_la_fila_lleva_los_dos_rotulos(tmp_path):
    """marcaSombra34 arma lo que se ve en la celda «Zona»; con un `el` falso se lee su texto sin navegador."""
    v = dict(SOMBRA)
    cuerpo = """
const el = (tag, cls) => ({ cls, textContent: "", title: "", hijos: [], appendChild(c) { this.hijos.push(c); } });
const v = %s;
const comp = new Map([["X|2026-11-12 05:36|VIIRS_NOAA21", ["Vecino"]]]);
const texto = m => m ? m.hijos.map(h => h.cls + ":" + h.textContent) : null;
process.stdout.write(JSON.stringify({
  ambos: texto(marcaSombra34(DATOS, v, comp)),
  solo_cumbre: texto(marcaSombra34(DATOS, v, new Map())),
  solo_vecino: texto(marcaSombra34(Object.assign({}, DATOS, { anomaly_pixels: [] }), v, comp)),
  nada: texto(marcaSombra34(Object.assign({}, DATOS, { anomaly_pixels: [] }), v, null)),
  tier_a: texto(marcaSombra34(DATOS, Object.assign({}, v, { fuente: undefined }), comp)),
}));
""" % json.dumps(v)
    out = _node(tmp_path, cuerpo, _rec(), nombres=FUNCIONES + ["marcaSombra34"])
    assert out == {
        "ambos": ["marca-34-cumbre:píxel a 1,1 km de la cumbre", "marca-34-compartido:también visto desde Vecino"],
        "solo_cumbre": ["marca-34-cumbre:píxel a 1,1 km de la cumbre"],
        "solo_vecino": ["marca-34-compartido:también visto desde Vecino"],
        "nada": None, "tier_a": None}, out


def test_la_pagina_aparte_ya_no_existe_ni_se_enlaza():
    """S183: la retiró el tablero (Nicolás aprobó). Si vuelve, que sea a propósito y cambiando esta prueba."""
    assert not (RAIZ / "frontend" / "preliminar_34.html").exists()
    assert not (RAIZ / "frontend" / "preliminar_34.js").exists()
    for pagina in ("index.html", "diario.html", "mosaico.html"):
        assert 'href="preliminar_34.html"' not in (RAIZ / "frontend" / pagina).read_text(encoding="utf-8"), pagina
