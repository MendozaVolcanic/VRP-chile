# -*- coding: utf-8 -*-
"""Marcador de sólo display «también hay calor en la cumbre» (S194): cuántas pasadas lo llevarían.

POR QUÉ: con la regla de posición «radiante» (D8'), una pasada con un alertado débil sobre el cráter y un cúmulo más
radiante a varios km queda `far`, y el tablero la muestra como anomalía lejana: el operador no ve que también hubo calor
en la cumbre. Cambiar la regla se midió y se rechazó (experiments/_s193_radiante_variante/INFORME.md). El marcador no
mueve nada: sólo avisa. Antes de dibujarlo se mide en cuántas pasadas saldría, si recupera la vista de las 12
protegidas sólo OCR (Codex F12-V301) y si informa (que no salga en casi todas las lejanas).

Predicado del marcador (el mismo que implementa frontend/cumbre.js; con --modulo se exige que den igual record por
record): record de la vía «código MIROVA», que el tablero NO pone en la cumbre (isSummitDetection falso, ejecutado con
node desde frontend/index.html) y con al menos un alertado de `anomaly_pixels` a `dist_km` <= inner_radius_km del
volcán. `dist_km` se mide desde el mismo cráter que `distance_class` (mirova_v750_codigo.py, armado del record).

Pasadas: las mismas que el informe S193 (banco_paridad.cargar_nuestros, nocturnas, sin escenas sin medir, 11 Tier A,
noches del 2026-03-01 al 2026-11-18). «Publicada como lejana» = lo que el tablero publica con «Incluir lejanas»:
no cumbre, isValidDetection, no artefacto térmico y mirovaEqVrpDisplay(r, inner, true) > 0.

Sólo lectura del repo. Uso:
  python -B experiments/_s194_marcador_cumbre/medir_marcador.py [--data <carpeta de JSON>] [--modulo]
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts", ROOT / "experiments" / "_s193_radiante_variante"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import banco_paridad as bp  # noqa: E402
import comparacion_via_k as cvk  # noqa: E402
from medir_variante import CODEX_12, INICIO, FIN_PRINCIPAL, familia  # noqa: E402

RES_S193 = ROOT / "experiments" / "_s193_radiante_variante" / "resultado.json"

_OUT_VIEJO = """const out = casos.map(([r, inner]) => {
  const summit = isSummitDetection(r), valid = isValidDetection(r);
  const art = isThermalArtifact(r, inner), disp = mirovaEqVrpDisplay(r, inner, false);
  return [summit ? 1 : 0, valid ? 1 : 0, art ? 1 : 0, disp,
          (summit && valid && !art && disp > 0) ? 1 : 0];
});"""
_OUT_NUEVO = """const out = casos.map(([r, inner]) => {
  const summit = isSummitDetection(r), valid = isValidDetection(r);
  const art = isThermalArtifact(r, inner), disp = mirovaEqVrpDisplay(r, inner, false);
  const dispFar = mirovaEqVrpDisplay(r, inner, true);
  return [summit ? 1 : 0, valid ? 1 : 0, art ? 1 : 0, disp,
          (summit && valid && !art && disp > 0) ? 1 : 0,
          (!summit && valid && !art && dispFar > 0) ? 1 : 0, dispFar];
});"""


def instalar_runner():
    """Mismo runner de banco_paridad (predicado del tablero con node) con dos salidas más: si la pasada se publica como
    lejana con «Incluir lejanas» y su magnitud. El predicado de publicación por defecto no cambia (control C3)."""
    if _OUT_VIEJO not in bp._JS:
        raise SystemExit("banco_paridad._JS cambió: revisar el reemplazo del runner")
    bp._JS = bp._JS.replace(_OUT_VIEJO, _OUT_NUEVO)


def calor_en_cumbre(r, inner):
    """Predicado del marcador en Python (paridad con frontend/cumbre.js). Devuelve (n, dmin) o None. No mira la clase:
    el llamador exige además que el tablero no ponga la pasada en la cumbre."""
    if r.get("via_codigo_mirova") is not True:
        return None
    ds = [float(p["dist_km"]) for p in (r.get("anomaly_pixels") or [])
          if p.get("dist_km") is not None and float(p["dist_km"]) <= inner]
    return (len(ds), min(ds)) if ds else None


def cargar_pasadas(data, coords, inner):
    """Pasadas como en S193 (evaluar) más las salidas nuevas del runner, guardadas al vuelo."""
    capt = []
    orig = bp.correr_node

    def correr(casos):
        res = orig(casos)
        capt.append(res)
        return res
    bp.correr_node = correr
    try:
        sin_medir = cvk.escenas_sin_medir(data)
        pas = bp.cargar_nuestros(coords, inner, (INICIO, FIN_PRINCIPAL), data=data)
    finally:
        bp.correr_node = orig
    pred = capt[0]
    assert len(pred) == len(pas)
    for p, q in zip(pas, pred):
        p["summit"], p["valid"], p["art"], p["pub_far"], p["disp_far"] = q[0], q[1], q[2], q[5], q[6]
    return cvk.quitar_escenas_sin_medir(pas, sin_medir)


def records_por_clave(data):
    out = {}
    for vol in bp.VOLS:
        d = json.loads((Path(data) / f"{vol}.json").read_text(encoding="utf-8"))
        for r in d["records"]:
            out[(vol, r.get("sensor"), r.get("datetime_utc"))] = r
    return out


def clave(p):
    return (p["vol"], p["sensor"], p["dt"].strftime("%Y-%m-%d %H:%M"))


_JS_MODULO = r"""
const fs = require('fs');
const C = require(process.argv[2]);
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
console.log(JSON.stringify(casos.map(([r, inner]) => { const m = C.calorEnCumbre(r, inner); return m ? [m.n, m.dMinKm] : null; })));
"""


def correr_modulo(casos):
    """frontend/cumbre.js ejecutado con node sobre los records completos (con anomaly_pixels)."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "m.js").write_text(_JS_MODULO, encoding="utf-8")
    (tmp / "c.json").write_text(json.dumps(casos), encoding="utf-8")
    o = subprocess.run(["node", "--max-old-space-size=4096", str(tmp / "m.js"), str(ROOT / "frontend" / "cumbre.js"),
                        str(tmp / "c.json")], capture_output=True, text=True, timeout=600)
    if o.returncode != 0:
        raise RuntimeError(o.stderr[-1500:])
    return json.loads(o.stdout)


def control_sintetico(inner):
    """Un record lejano con un alertado a 0,7 km del cráter de Láscar da marca; el mismo sin ese píxel, no; uno de la
    cumbre, no (el tablero ya lo pone en la cumbre)."""
    lejos = [{"lat": 0, "lon": 0, "dist_km": 15.2, "bt_k": 330.0}, {"lat": 0, "lon": 0, "dist_km": 15.6, "bt_k": 320.0}]
    cerca = {"lat": 0, "lon": 0, "dist_km": 0.7, "bt_k": 300.0}
    base = {"sensor": "VIIRS_NOAA20", "via_codigo_mirova": True, "vrp_mw": 2.0, "n_anomalous_pixels": 3,
            "distance_class": "far", "triggered_test1": False, "discarded_reason": None, "vrp_vent_mw": 0.0,
            "primary_cluster": {"vrp_mw": 2.0, "n_pixels": 2, "centroid_dist_km": 15.4}}
    con = dict(base, anomaly_pixels=[cerca] + lejos)
    sin = dict(base, anomaly_pixels=lejos, n_anomalous_pixels=2)
    cumbre = dict(con, distance_class="summit")
    il = inner["Lascar"]
    res = {"con": calor_en_cumbre(con, il), "sin": calor_en_cumbre(sin, il),
           "no_via": calor_en_cumbre(dict(con, via_codigo_mirova=False), il)}
    pub = bp.correr_node([[{k: x.get(k) for k in bp.CAMPOS_JS}, il] for x in (con, sin, cumbre)])
    res["summit_tablero"] = [q[0] for q in pub]
    res["ok"] = (res["con"] == (1, 0.7) and res["sin"] is None and res["no_via"] is None
                 and res["summit_tablero"] == [0, 0, 1])
    return res, [[con, il], [sin, il], [cumbre, il]]


def med(xs):
    return round(statistics.median(xs), 3) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data" / "mirova_equivalent"))
    ap.add_argument("--modulo", action="store_true", help="exigir paridad con frontend/cumbre.js")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    data = Path(a.data)
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    instalar_runner()
    pas = cargar_pasadas(data, coords, inner)
    pas = [p for p in pas if p["noche"] <= FIN_PRINCIPAL]
    recs = records_por_clave(data)
    s193 = json.loads(RES_S193.read_text(encoding="utf-8"))
    far_ref_114 = {(f["vol"], f["sensor"], f["dt"]) for f in s193["principal"]["tabla"]["detalle_cambios"]["far_ref"]}
    cambian_218 = {(f["vol"], f["sensor"], f["dt"]) for lst in s193["principal"]["tabla"]["detalle_cambios"].values()
                   for f in lst}
    c12 = {(f["vol"], f["sensor"], f["dt"]) for f in s193["principal"]["combinado"]["detalle_cambios"]["pos_protegida"]}
    assert {(v, d) for v, _, d in c12} == CODEX_12

    out = {"meta": {"data": str(data), "ventana": [INICIO, FIN_PRINCIPAL], "inner": inner}}
    sint, casos_sint = control_sintetico(inner)
    out["control_sintetico"] = sint
    print("Control sintético (con píxel a 0,7 km marca; sin él no; no vía no; cumbre la pone el tablero):", sint)
    print("Pasadas (control: 28.840 en el informe S193):", len(pas))
    print("Claves únicas:", len({clave(p) for p in pas}))

    est = collections.defaultdict(collections.Counter)
    marcadas, dmins, ns = [], [], []
    for p in pas:
        r = recs[clave(p)]
        m = calor_en_cumbre(r, inner[p["vol"]])
        marca = bool(m) and not p["summit"]
        p["marca"], p["m"] = marca, m
        fam = familia(p["sensor"])
        for e in ("total", "b=" + fam, "vol=" + p["vol"], f"vol_b={p['vol']}|{fam}"):
            c = est[e]
            c["pasadas"] += 1
            con_alert = bool(r.get("n_anomalous_pixels"))
            c["con_alertados"] += con_alert
            if p["summit"]:
                c["cumbre"] += 1
                c["cumbre_publicadas"] += p["pub"]
                c["cumbre_no_publicadas"] += not p["pub"]
            elif con_alert:
                c["lejanas"] += 1
                c["lejanas_publicables"] += p["pub_far"]
                c["lejanas_con_marca"] += marca
                c["lejanas_publicables_con_marca"] += marca and p["pub_far"]
                c["lejanas_no_publicables_con_marca"] += marca and not p["pub_far"]
        if marca:
            marcadas.append(p)
            dmins.append(m[1])
            ns.append(m[0])
    for c in est.values():
        if c["lejanas_publicables"]:
            c["pct_lejanas_publicables_con_marca"] = round(100 * c["lejanas_publicables_con_marca"]
                                                          / c["lejanas_publicables"], 1)
    out["estratos"] = {k: dict(v) for k, v in sorted(est.items())}
    out["marca_px_en_cumbre"] = {"mediana_n": med(ns), "max_n": max(ns) if ns else None,
                                 "n_1": sum(1 for n in ns if n == 1),
                                 "dmin_mediana_km": med(dmins), "dmin_min": min(dmins) if dmins else None,
                                 "dmin_max": max(dmins) if dmins else None}
    clave_pas = {clave(p): p for p in pas}
    # las 12 protegidas sólo OCR
    doce = []
    for k in sorted(c12):
        p = clave_pas.get(k)
        doce.append({"clave": k, "en_pasadas": p is not None, "marca": bool(p and p["marca"]),
                     "pub_defecto": p and p["pub"], "pub_far": p and p["pub_far"],
                     "n_cumbre": p and p["m"] and p["m"][0], "dmin": p and p["m"] and p["m"][1],
                     "lejana_km": p and p["pc_dist"]})
    out["codex_12"] = {"con_marca": sum(d["marca"] for d in doce), "de": len(doce), "detalle": doce}
    # las 114 far_ref y las 218 que cambiaban con la variante
    f114 = [clave_pas.get(k) for k in far_ref_114]
    out["far_ref_114"] = {"en_pasadas": sum(p is not None for p in f114),
                          "con_marca": sum(bool(p and p["marca"]) for p in f114)}
    set_marca = {clave(p) for p in marcadas}
    out["cruce_variante_218"] = {"cambian_s193": len(cambian_218), "cambian_con_marca": len(cambian_218 & set_marca),
                                 "marca_sin_cambio_s193": len(set_marca - cambian_218)}
    extra = [clave_pas[k] for k in sorted(set_marca - cambian_218)]
    out["marca_fuera_de_las_218"] = collections.Counter(
        ("publicable_lejana" if p["pub_far"] else "no_publicable") + ("|art" if p["art"] else "")
        + ("|invalida" if not p["valid"] else "") for p in extra)
    # no publicadas con alertado en la cumbre (sólo dato)
    nopub = collections.Counter()
    for p in pas:
        r = recs[clave(p)]
        m = calor_en_cumbre(r, inner[p["vol"]])
        if not m:
            continue
        if p["summit"] and not p["pub"]:
            nopub["cumbre_no_publicada"] += 1
        if not p["summit"] and not p["pub_far"]:
            nopub["lejana_no_publicable"] += 1
    out["no_publicadas_con_alertado_en_cumbre"] = dict(nopub)
    # paridad con el módulo del tablero
    if a.modulo:
        # El módulo exige además distance_class "far"; aquí la marca exige que node diga «no cumbre». Deben coincidir.
        casos = [[recs[clave(p)], inner[p["vol"]]] for p in pas]
        js = correr_modulo(casos + casos_sint)
        jsp, jss = js[:len(casos)], js[len(casos):]
        py = [p["m"] if p["marca"] else None for p in pas]
        dif = [i for i, (x, y) in enumerate(zip(jsp, py)) if (x is None) != (y is None)
               or (x is not None and (x[0] != y[0] or abs(x[1] - y[1]) > 1e-9))]
        sint_ok = jss[0] == [1, 0.7] and jss[1] is None and jss[2] is None
        out["paridad_modulo"] = {"casos": len(casos), "distintos": len(dif), "con_marca_js": sum(x is not None for x in jsp),
                                 "sintetico_js": jss, "sintetico_ok": sint_ok}
        print("Paridad con frontend/cumbre.js:", out["paridad_modulo"])

    print("Control: claves de las 12 en las pasadas:", sum(d["en_pasadas"] for d in doce), "de 12")
    print("== total:", out["estratos"]["total"])
    for e in ("b=MODIS", "b=VIIRS375", "b=VIIRS750"):
        print(f"  {e:12s}", out["estratos"].get(e))
    print("-- por volcán y sensor (lejanas publicables con marca / lejanas publicables):")
    for e, c in out["estratos"].items():
        if e.startswith("vol_b=") and c.get("lejanas_con_marca"):
            print(f"  {e[6:]:32s} {c.get('lejanas_publicables_con_marca', 0):4d} / {c.get('lejanas_publicables', 0):4d}"
                  f"  (no publicables con marca {c.get('lejanas_no_publicables_con_marca', 0)})")
    print("Píxeles en la cumbre de las marcadas:", out["marca_px_en_cumbre"])
    print("Las 12 protegidas sólo OCR con marca:", out["codex_12"]["con_marca"], "de", out["codex_12"]["de"])
    for d in doce:
        print("   ", d)
    print("Las 114 far_ref de S193:", out["far_ref_114"])
    print("Cruce con las 218 que la variante movía:", out["cruce_variante_218"], dict(out["marca_fuera_de_las_218"]))
    print("No publicadas con alertado en la cumbre (dato):", out["no_publicadas_con_alertado_en_cumbre"])
    sal = Path(a.salida) if a.salida else Path(__file__).with_name("resultado.json")
    sal.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("->", sal)


if __name__ == "__main__":
    main()
