# -*- coding: utf-8 -*-
"""Marca «cráter no medido» (S194, Codex C1-102 y C1-V202): cuántos records la traen y qué les muestra hoy el tablero.

POR QUÉ: la vía «código MIROVA» anota en diag_codigo_mirova si al cráter le faltó dato antes de interpolar (#1060,
ficha v1.47) y, desde #1077 (ficha v1.61), separa el relleno bow-tie de VIIRS del hueco real de MIR y TIR. El tablero no
lee esas claves: un foco aislado que cae en el hueco sale «sin anomalía», y uno con vecinos tibios publica una fracción
sin aviso. Antes de dibujar la marca se cuenta cuántos records la llevan, de qué tipo, y qué muestra hoy el tablero en
ellos, con el predicado real (funciones de frontend/index.html ejecutadas con node, como scripts/banco_paridad.py).

Tipos (por record; un record puede caer en varios):
  hueco_mir       px_mir_hueco_crater > 0 (MIR perdida que NO es bow-tie). Lo que marca el tablero.
  sin_posicion    crater_sin_posicion True. Lo marca el tablero.
  saturado        px_saturados_crater > 0 (VIIRS). Lo marca el tablero, con otro texto (potencia mínima).
  bowtie          px_bowtie_crater > 0. No se marca (el barrido vecino midió ese suelo).
  hueco_tir       px_tir_hueco_crater > 0. No se marca (otro efecto, sin texto verificado).
  ambiguo         px_mir_invalido_crater > 0 en un record sin las claves separadas (procesado antes de #1077). No se marca.

«Qué muestra hoy» (con «Solo cráter», el valor por defecto): «publicada» si eqVrp > 0 (la fila lleva potencia);
si no, el rótulo de rotuloPasadaSinPublicar («sin anomalía», «anomalía no publicada», «escena sin datos», ...).

Con --modulo exige que frontend/crater_no_medido.js dé el mismo resultado que el predicado en Python record por record.
Sólo lectura del repo. Uso:
  python -B experiments/_s194_mir_perdido/medir_mir_perdido.py [--data <carpeta de JSON>] [--modulo]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import banco_paridad as bp  # noqa: E402

HTML = ROOT / "frontend" / "index.html"
MODULO = ROOT / "frontend" / "crater_no_medido.js"
CLAVES = ("crater_sin_posicion", "px_mir_invalido_crater", "px_saturados_crater", "px_bowtie_crater",
          "px_mir_hueco_crater", "px_tir_hueco_crater")

_LISTA_VIEJA = """['_havKm','mirovaEqVrp','f5CoreMagnitude','mirovaEqVrpCore','mirovaEqVrpDisplay',
   'isCirrusArtifact','isDiffuseFieldArtifact','isThermalArtifact','isValidDetection',
   'isSummitDetection']"""
_LISTA_NUEVA = """['_havKm','mirovaEqVrp','f5CoreMagnitude','mirovaEqVrpCore','mirovaEqVrpDisplay',
   'isCirrusArtifact','isDiffuseFieldArtifact','isThermalArtifact','isValidDetection',
   'isSummitDetection','escenaSinDato','rotuloPasadaSinPublicar']"""
_OUT_VIEJO = """const out = casos.map(([r, inner]) => {
  const summit = isSummitDetection(r), valid = isValidDetection(r);
  const art = isThermalArtifact(r, inner), disp = mirovaEqVrpDisplay(r, inner, false);
  return [summit ? 1 : 0, valid ? 1 : 0, art ? 1 : 0, disp,
          (summit && valid && !art && disp > 0) ? 1 : 0];
});"""
# Lo mismo que la tabla «Últimas pasadas» de renderDetail con «Solo cráter»: eqVrp = isThermalArtifact ? 0 :
# mirovaEqVrpDisplay(r, inner, false); si no es > 0, el rótulo de rotuloPasadaSinPublicar. Y el valor con «Incluir
# lejanas», para saber si la pasada publica algo lejos.
_OUT_NUEVO = """const out = casos.map(([r, inner]) => {
  const art = isThermalArtifact(r, inner);
  const eq = art ? 0 : mirovaEqVrpDisplay(r, inner, false);
  const eqFar = art ? 0 : mirovaEqVrpDisplay(r, inner, true);
  return [eq, eqFar, eq > 0 ? 'publicada' : rotuloPasadaSinPublicar(r).texto];
});"""


def runner_js():
    js = bp._JS
    if _LISTA_VIEJA not in js or _OUT_VIEJO not in js:
        raise SystemExit("banco_paridad._JS cambió: revisar el reemplazo del runner")
    return js.replace(_LISTA_VIEJA, _LISTA_NUEVA).replace(_OUT_VIEJO, _OUT_NUEVO)


def correr_tablero(casos):
    tmp = Path(tempfile.mkdtemp())
    (tmp / "r.js").write_text(runner_js(), encoding="utf-8")
    (tmp / "c.json").write_text(json.dumps(casos), encoding="utf-8")
    o = subprocess.run(["node", "--max-old-space-size=4096", str(tmp / "r.js"), str(HTML), str(tmp / "c.json")],
                       capture_output=True, text=True, encoding="utf-8", timeout=600)
    if o.returncode != 0:
        raise RuntimeError(o.stderr[-1500:])
    return json.loads(o.stdout)


_JS_MODULO = r"""
const fs = require('fs');
const C = require(process.argv[2]);
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
console.log(JSON.stringify(casos.map(r => { const m = C.craterNoMedido(r); return m ? [m.nMir, m.nSat, m.sinPosicion] : null; })));
"""


def correr_modulo(recs):
    tmp = Path(tempfile.mkdtemp())
    (tmp / "m.js").write_text(_JS_MODULO, encoding="utf-8")
    (tmp / "c.json").write_text(json.dumps(recs), encoding="utf-8")
    o = subprocess.run(["node", "--max-old-space-size=4096", str(tmp / "m.js"), str(MODULO), str(tmp / "c.json")],
                       capture_output=True, text=True, encoding="utf-8", timeout=600)
    if o.returncode != 0:
        raise RuntimeError(o.stderr[-1500:])
    return json.loads(o.stdout)


def inner_todos():
    """inner_radius_km de todos los volcanes de VOLCANOES (bp.inner_desde_html se limita a los 11)."""
    src = HTML.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r'name:\s*"(\w+)".*?inner_radius_km:\s*([\d.]+)', src):
        out.setdefault(m.group(1), float(m.group(2)))
    return out


def _pos(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0


def tipos(d):
    """Tipos de marca del diag (ver docstring)."""
    t = []
    if _pos(d.get("px_mir_hueco_crater")):
        t.append("hueco_mir")
    if d.get("crater_sin_posicion") is True:
        t.append("sin_posicion")
    if _pos(d.get("px_saturados_crater")):
        t.append("saturado")
    if _pos(d.get("px_bowtie_crater")):
        t.append("bowtie")
    if _pos(d.get("px_tir_hueco_crater")):
        t.append("hueco_tir")
    if "px_mir_hueco_crater" not in d and _pos(d.get("px_mir_invalido_crater")):
        t.append("ambiguo")
    return t


def marca_py(r):
    """Predicado del tablero en Python (paridad con frontend/crater_no_medido.js::craterNoMedido)."""
    d = r.get("diag_codigo_mirova")
    if not isinstance(d, dict):
        return None
    n_mir = round(d["px_mir_hueco_crater"]) if _pos(d.get("px_mir_hueco_crater")) else 0
    n_sat = round(d["px_saturados_crater"]) if _pos(d.get("px_saturados_crater")) else 0
    sin_pos = d.get("crater_sin_posicion") is True
    return [n_mir, n_sat, sin_pos] if (n_mir or n_sat or sin_pos) else None


def familia(sensor):
    s = sensor or ""
    return "MODIS" if s.startswith("MODIS") else "VIIRS750" if s.endswith("_750") else "VIIRS375" if s.startswith("VIIRS") else "otro"


def control_sintetico():
    """El mismo record con y sin cada marca; bow-tie y ambiguo no marcan."""
    base = {"sensor": "VIIRS_NOAA20_750", "datetime_utc": "2026-11-22 05:06", "via_codigo_mirova": True, "vrp_mw": 0.0,
            "n_anomalous_pixels": 0, "anomaly_pixels": []}
    d0 = {"crater_sin_posicion": False, "px_mir_invalido_crater": 0, "px_saturados_crater": 0, "px_bowtie_crater": 0,
          "px_mir_hueco_crater": 0, "px_tir_hueco_crater": 0}
    casos = {"control": d0, "hueco": dict(d0, px_mir_invalido_crater=2, px_mir_hueco_crater=2),
             "bowtie": dict(d0, px_mir_invalido_crater=3, px_bowtie_crater=3),
             "ambiguo": {k: v for k, v in dict(d0, px_mir_invalido_crater=3).items()
                         if k not in ("px_bowtie_crater", "px_mir_hueco_crater", "px_tir_hueco_crater")},
             "tir": dict(d0, px_mir_invalido_crater=1, px_tir_hueco_crater=1),
             "sat": dict(d0, px_saturados_crater=1), "sinpos": dict(d0, crater_sin_posicion=True)}
    recs = {k: dict(base, diag_codigo_mirova=v) for k, v in casos.items()}
    py = {k: marca_py(r) for k, r in recs.items()}
    esperado = {"control": None, "hueco": [2, 0, False], "bowtie": None, "ambiguo": None, "tir": None,
                "sat": [0, 1, False], "sinpos": [0, 0, True]}
    return {"py": py, "ok": py == esperado}, recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data" / "mirova_equivalent"))
    ap.add_argument("--modulo", action="store_true", help="exigir paridad con frontend/crater_no_medido.js")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    data = Path(a.data)
    inner = inner_todos()
    tier_a = set(bp.VOLS)

    tot = collections.Counter()
    proc_rango = collections.defaultdict(list)
    est = collections.defaultdict(collections.Counter)
    con_claves = []   # (vol, r)
    todos = []        # para la paridad
    for f in sorted(data.glob("*.json")):
        vol = f.stem
        d = json.loads(f.read_text(encoding="utf-8"))
        for r in d.get("records", []):
            tot["records"] += 1
            tot["tier_a" if vol in tier_a else "no_tier_a"] += 1
            tot["via"] += r.get("via_codigo_mirova") is True
            dg = r.get("diag_codigo_mirova")
            todos.append(r)
            if not isinstance(dg, dict) or "px_mir_invalido_crater" not in dg:
                continue
            gen = "separadas" if "px_mir_hueco_crater" in dg else "sin_separar"
            tot["con_claves_" + gen] += 1
            proc_rango[gen].append((r.get("processed_utc") or "", r.get("datetime_utc") or ""))
            con_claves.append((vol, r, gen))
            for t in tipos(dg) or ["ninguna"]:
                est[familia(r.get("sensor")) + "|" + gen][t] += 1
                est["total|" + gen][t] += 1

    print("Records:", dict(tot))
    for g, xs in sorted(proc_rango.items()):
        print(f"  claves {g}: processed_utc {min(x[0] for x in xs)} a {max(x[0] for x in xs)};"
              f" datetime_utc {min(x[1] for x in xs)} a {max(x[1] for x in xs)}")
    print("Por sensor y generación de claves (tipo: records):")
    for k in sorted(est):
        print(f"  {k:24s} {dict(est[k])}")

    # bow-tie contra hueco en los records con las claves separadas: ¿todo el inválido es bow-tie?
    sep = [r for _, r, g in con_claves if g == "separadas"]
    inv_pos = [r for r in sep if _pos(r["diag_codigo_mirova"].get("px_mir_invalido_crater"))]
    inv_eq_bt = [r for r in inv_pos if r["diag_codigo_mirova"].get("px_mir_invalido_crater")
                 == r["diag_codigo_mirova"].get("px_bowtie_crater")]
    print(f"Claves separadas: {len(inv_pos)} records con px_mir_invalido_crater > 0; en {len(inv_eq_bt)} el inválido"
          f" es todo bow-tie (px_mir_invalido_crater == px_bowtie_crater)")

    # Qué muestra hoy el tablero en los records con claves
    casos = [[{**{k: r.get(k) for k in bp.CAMPOS_JS}, "n_anomalous_pixels": r.get("n_anomalous_pixels"),
               "diag_codigo_mirova": r.get("diag_codigo_mirova")}, inner.get(vol)] for vol, r, _ in con_claves]
    tab = correr_tablero(casos)
    vista = collections.defaultdict(collections.Counter)
    filas = []
    for (vol, r, gen), (eq, eq_far, rot) in zip(con_claves, tab):
        ts = tipos(r["diag_codigo_mirova"])
        marca = marca_py(r)
        for t in ts or ["ninguna"]:
            vista[t][rot] += 1
        if marca:
            vista["MARCA_TABLERO"][rot] += 1
        if marca or "ambiguo" in ts:
            filas.append({"vol": vol, "sensor": r.get("sensor"), "dt": r.get("datetime_utc"), "gen": gen, "tipos": ts,
                          "marca": marca, "tablero": rot, "eq_mw": eq, "eq_far_mw": eq_far,
                          "motivo_vacio": r["diag_codigo_mirova"].get("motivo_vacio")})
    print("Qué muestra hoy el tablero («Solo cráter»), por tipo:")
    for t in sorted(vista):
        print(f"  {t:14s} {dict(vista[t])}")
    print("Records que el tablero marcaría (criterio de frontend/crater_no_medido.js):")
    for x in filas:
        if x["marca"]:
            print("  ", x)
    n_amb = sum(1 for x in filas if "ambiguo" in x["tipos"])
    print(f"Ambiguos (sin separar, no se marcan): {n_amb}")

    sint, recs_sint = control_sintetico()
    print("Control sintético (hueco, saturado y sin posición marcan; control, bow-tie, ambiguo y TIR no):", sint)

    out = {"meta": {"data": str(data)}, "totales": dict(tot),
           "rango_claves": {g: {"processed_min": min(x[0] for x in xs), "processed_max": max(x[0] for x in xs),
                                "dt_min": min(x[1] for x in xs), "dt_max": max(x[1] for x in xs)}
                            for g, xs in proc_rango.items()},
           "estratos": {k: dict(v) for k, v in sorted(est.items())},
           "separadas_invalido_pos": len(inv_pos), "separadas_invalido_todo_bowtie": len(inv_eq_bt),
           "tablero_por_tipo": {k: dict(v) for k, v in sorted(vista.items())},
           "marcadas": [x for x in filas if x["marca"]], "ambiguos": n_amb, "control_sintetico": sint}

    if a.modulo:
        lista_sint = list(recs_sint.values())
        js = correr_modulo(todos + lista_sint)
        jsp, jss = js[:len(todos)], js[len(todos):]
        py = [marca_py(r) for r in todos]
        dif = [i for i, (x, y) in enumerate(zip(jsp, py)) if x != y]
        sint_ok = jss == [marca_py(r) for r in lista_sint]
        out["paridad_modulo"] = {"records": len(todos), "distintos": len(dif), "con_marca_js": sum(x is not None for x in jsp),
                                 "sintetico_ok": sint_ok}
        print("Paridad con frontend/crater_no_medido.js:", out["paridad_modulo"])

    sal = Path(a.salida) if a.salida else Path(__file__).with_name("resultado.json")
    sal.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("->", sal)


if __name__ == "__main__":
    main()
