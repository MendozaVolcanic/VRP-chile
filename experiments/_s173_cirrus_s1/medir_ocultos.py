"""S173 S1: cuantos records oculta hoy el filtro de artefacto termico del tablero, y de que detector son.

POR QUE. Desde el 2026-11-02 MODIS publica con la via «codigo MIROVA» (MOD-D, #934). El filtro S90
(`isCirrusArtifact`: t_max_k < 273,15 K y magnitud > 10 MW) y el S93 (`isDiffuseFieldArtifact`) se
calibraron contra el path D de K sobre cirrus. La via ve el volcan en la grilla de 1 km de MIROVA y en
pasadas oblicuas el t_max de la celda mezcla el foco con nieve: un record frio y potente ya no es
incoherente. Antes de tocar el filtro hay que saber cuantos records oculta y de que detector son (A116).

QUE MIDE. Para cada record de data/mirova_equivalent/*.json (los 45 volcanes):
- el predicado del tablero EJECUTADO con node desde el HTML (A97), para las tres vistas vivas:
  index.html (mirovaEqVrp con innerKm), mosaico.html (igual firma) y diario.html (firma con volcanoName);
- «oculto» = el tablero lo publicaria sin el filtro (summit, valido, magnitud > 0) y el filtro lo marca;
  ademas, aparte, cuantos marca el filtro aunque no se fueran a publicar;
- regimen: via (`via_codigo_mirova is True`, pipeline/mirova_v750_codigo.py:704), K con aviso de la via
  (`via_codigo_mirova` texto: sin_grilla / sin_mxd03 / geo_distinta) o K (sin el campo);
- cenit (`sensor_zenith_deg`) bajo / sobre 30 grados;
- coincidencia con MIROVA para los 11 Tier A: fila ALERTA a +-120 s (pareo unico, clase_mirova.VENTANA_S),
  y el cinturon del tablero (`_mirova_confirmed`: cualquier fila con VRP > 0 a +-60 min en el mismo sensor).

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. ¿Podria dar distinto de cero? Control positivo: un record sintetico de K (sin la marca de la via) con los
   campos del caso X2 de Chillan (t_max 269,57 K, 11,44 MW, summit) tiene que salir oculto en las tres vistas; uno
   con 5,72 MW no. Si el control falla, el script aborta. El mismo record con `via_codigo_mirova: true` se
   informa aparte (`via_cirrus`): 1 con la regla de antes, 0 con la exencion de S173.
2. ¿Y si estuviera muerto? Se informa cuantos records marca el filtro en total; si es 0 en todo el corpus,
   no se lee como «el filtro no hace nada» sin mirar el control.
"""
from __future__ import annotations

import bisect
import collections
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from calidad_referencia_mirova import avisar  # noqa: E402
from clase_mirova import VENTANA_S  # noqa: E402
from referencia_mirova_unificada import bajar_remoto, cargar_referencia_unificada  # noqa: E402

DATA = ROOT / "data" / "mirova_equivalent"
# S173_FRONTEND: carpeta con las tres vistas (por defecto frontend/ del checkout). Para medir la regla de antes se
# apunta a una copia de frontend/ del tag pre-s173-cirrus-s1 (`git show <tag>:frontend/<vista>`).
_FE = Path(os.environ.get("S173_FRONTEND", str(ROOT / "frontend")))
VISTAS = {"index": _FE / "index.html", "mosaico": _FE / "mosaico.html", "diario": _FE / "diario.html"}
OUT = Path(__file__).resolve().parent

_JS = r"""
const fs = require('fs');
const vista = process.argv[2];
const src = fs.readFileSync(process.argv[3], 'utf8');
function extraer(nombre, opcional) {
  const i = src.search(new RegExp('function\\s+' + nombre + '\\s*\\('));
  if (i < 0) { if (opcional) return ''; throw new Error('no encontre function ' + nombre); }
  let j = src.indexOf('{', i), d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  throw new Error('no cerro ' + nombre);
}
function constante(nombre, opcional) {
  const m = src.match(new RegExp('const ' + nombre + '\\s*=\\s*([^;]+);'));
  if (!m) { if (opcional) return ''; throw new Error('no encontre const ' + nombre); }
  return m[0];
}
let USE_F5_CORE = true; let includeFarDistance = false;
// Desde S173 la marca de la via la lee el modulo compartido; si la copia de frontend/ no lo trae, queda indefinido.
let CambioDetector;
try { CambioDetector = require(require('path').join(require('path').dirname(process.argv[3]), 'cambio_detector.js')); } catch (e) {}
const nombres = ['_havKm','mirovaEqVrp','f5CoreMagnitude','mirovaEqVrpCore','isCirrusArtifact',
  'isDiffuseFieldArtifact','isThermalArtifact','isValidDetection','isSummitDetection',
  'esViaCodigoMirova'];
const codigo = [constante('F5_R_CORE_KM', true), constante('F5_BT_EXT_K', true),
  constante('INNER_RADIUS_KM', true)].concat(nombres.map(n => extraer(n, true))).join('\n');
eval(codigo);
const casos = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
const out = casos.map(([r, inner, vol]) => {
  const arg = vista === 'diario' ? vol : inner;
  const c = isCirrusArtifact(r, arg) ? 1 : 0, d = isDiffuseFieldArtifact(r, arg) ? 1 : 0;
  const summit = typeof isSummitDetection === 'function' ? (isSummitDetection(r) ? 1 : 0) : -1;
  const valid = typeof isValidDetection === 'function' ? (isValidDetection(r) ? 1 : 0) : -1;
  const eq = vista === 'diario' ? mirovaEqVrp(r, vol) : mirovaEqVrp(r, inner, false);
  return [c, d, summit, valid, eq];
});
console.log(JSON.stringify(out));
"""

CAMPOS = ["primary_cluster", "distance_class", "vrp_mw", "vrp_mir_mw", "discarded_reason", "triggered_test1",
          "vrp_vent_mw", "t_max_k", "sensor", "f5_core_vrp_mw", "via_codigo_mirova", "_mirova_confirmed"]


def correr_node(vista, casos):
    tmp = tempfile.mkdtemp()
    try:
        runner, datos = os.path.join(tmp, "r.js"), os.path.join(tmp, "c.json")
        Path(runner).write_text(_JS, encoding="utf-8")
        Path(datos).write_text(json.dumps(casos), encoding="utf-8")
        o = subprocess.run(["node", "--max-old-space-size=6144", runner, vista, str(VISTAS[vista]), datos],
                           capture_output=True, text=True, timeout=900)
        if o.returncode != 0:
            raise RuntimeError("node fallo: " + o.stderr[-1500:])
        return json.loads(o.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def inner_por_volcan():
    src = VISTAS["index"].read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r'name:\s*"(\w+)".*?inner_radius_km:\s*([\d.]+)', src):
        out.setdefault(m.group(1), float(m.group(2)))
    return out


def bucket(sensor):
    s = (sensor or "").upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("_750") else "VIIRS375"
    return None


def regimen(r):
    v = r.get("via_codigo_mirova")
    if v is True:
        return "via"
    if isinstance(v, str):
        return "K_aviso_" + v
    return "K"


def control():
    """Control positivo y negativo del instrumento en las tres vistas."""
    base = {"sensor": "MODIS_AQUA", "distance_class": "summit", "t_max_k": 269.57,
            "triggered_test1": False, "vrp_vent_mw": 0.0}
    pos = dict(base, vrp_mw=11.442, primary_cluster={"vrp_mw": 11.442, "centroid_dist_km": 0.708, "n_pixels": 8})
    neg = dict(base, vrp_mw=5.721, primary_cluster={"vrp_mw": 5.721, "centroid_dist_km": 0.708, "n_pixels": 8})
    res = {}
    for v in VISTAS:
        p, n, w = correr_node(v, [[pos, 5.0, "NevadosDeChillan"], [neg, 5.0, "NevadosDeChillan"],
                                  [dict(pos, via_codigo_mirova=True), 5.0, "NevadosDeChillan"]])
        res[v] = {"pos_cirrus": p[0], "neg_cirrus": n[0], "via_cirrus": w[0]}
    return res


def main():
    ctrl = control()
    print("control (pos tiene que dar 1, neg 0):", ctrl)
    if any(c["pos_cirrus"] != 1 or c["neg_cirrus"] != 0 for c in ctrl.values()):
        print("CONTROL FALLA: el instrumento no puede leer el filtro; aborto")
        return 1

    inner = inner_por_volcan()
    recs, casos = [], []
    for f in sorted(DATA.glob("*.json")):
        vol = f.stem
        d = json.loads(f.read_text(encoding="utf-8"))
        for r in d["records"]:
            slim = {k: r.get(k) for k in CAMPOS}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner.get(vol, 5.0), vol])
            z = r.get("sensor_zenith_deg")
            recs.append({"vol": vol, "dt": r.get("datetime_utc", ""), "b": bucket(r.get("sensor")),
                         "sensor": r.get("sensor"), "reg": regimen(r), "z": z,
                         "zc": "sin_z" if z is None else ("z<30" if z < 30 else "z>=30"),
                         "t_max": r.get("t_max_k"), "pc": (r.get("primary_cluster") or {}).get("vrp_mw"),
                         "npx": (r.get("primary_cluster") or {}).get("n_pixels")})
    pred = {v: correr_node(v, casos) for v in VISTAS}

    # Referencia MIROVA (remota, A119 avisado)
    info = bajar_remoto(Path(os.environ.get("S173_DL", str(OUT / "_dl"))))
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    filas = cargar_referencia_unificada(cons, ocr)
    por_vb = collections.defaultdict(list)
    for fl in filas:
        try:
            dt = datetime.strptime(fl["fecha_utc"][:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        por_vb[(fl["volcano"], fl["sensor_bucket"])].append((dt, fl))
    for v in por_vb.values():
        v.sort(key=lambda x: x[0])

    def pareo(vol, b, dt, tol_s):
        lista = por_vb.get((vol, b), [])
        ts = [x[0] for x in lista]
        i = bisect.bisect_left(ts, dt - timedelta(seconds=tol_s))
        out = []
        while i < len(lista) and lista[i][0] <= dt + timedelta(seconds=tol_s):
            out.append(lista[i][1])
            i += 1
        return out

    filas_marcadas = []
    tabla = collections.Counter()
    for k, rec in enumerate(recs):
        ci, di, su, va, eq = pred["index"][k]
        pub_sin_filtro = su == 1 and va == 1 and eq > 0
        for v in VISTAS:
            c, d = pred[v][k][0], pred[v][k][1]
            if c or d:
                tabla[(v, "marca", rec["reg"], rec["b"], rec["zc"], "cirrus" if c else "difuso")] += 1
                if pub_sin_filtro:
                    tabla[(v, "oculta", rec["reg"], rec["b"], rec["zc"], "cirrus" if c else "difuso")] += 1
        if (ci or di) and pub_sin_filtro:
            try:
                dt = datetime.strptime(rec["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except ValueError:
                dt = None
            m2 = pareo(rec["vol"], rec["b"], dt, VENTANA_S) if dt else []
            m60 = pareo(rec["vol"], rec["b"], dt, 3600) if dt else []
            alerta = [x for x in m2 if x["tipo"].startswith("ALERTA")]
            filas_marcadas.append(dict(rec, cirrus=ci, difuso=di, eq=round(eq, 3),
                                       mirova_alerta_2min=[(x["tipo"], x["vrp_mw"], x["dist_km"]) for x in alerta],
                                       mirova_filas_2min=[(x["tipo"], x["vrp_mw"]) for x in m2],
                                       cinturon_60min_vrp=any((x["vrp_mw"] or 0) > 0 for x in m60)))
    fechas = sorted(r["dt"][:10] for r in filas_marcadas if r["dt"])
    if fechas:
        avisar(fechas[0], fechas[-1])
    total_reg = collections.Counter((r["reg"], r["b"]) for r in recs)
    via = [r for r in recs if r["reg"] == "via"]
    print(f"records: {len(recs)} | regimen x sensor: {dict(sorted(total_reg.items()))}")
    print(f"via: {len(via)} records, fechas {min((r['dt'] for r in via), default='-')} a "
          f"{max((r['dt'] for r in via), default='-')}; t_max<273.15: "
          f"{sum(1 for r in via if r['t_max'] is not None and r['t_max'] < 273.15)}; "
          f"magnitud>10 MW: {sum(1 for r in via if (r['pc'] or 0) > 10)}")
    print("\nvista | marca/oculta | regimen | sensor | cenit | filtro | n")
    for k, n in sorted(tabla.items()):
        print(" | ".join(map(str, k)), "|", n)
    print("\nrecords ocultos en index.html (publicarian sin el filtro), uno por linea:")
    for r in sorted(filas_marcadas, key=lambda x: (x["reg"], x["vol"], x["dt"])):
        print(f"  {r['reg']:8s} {r['vol']:20s} {r['dt']} {r['sensor']:16s} z {r['z']} t_max {r['t_max']} "
              f"pc {r['pc']} npx {r['npx']} eq {r['eq']} cirrus {r['cirrus']} difuso {r['difuso']} "
              f"MIROVA_alerta_2min {r['mirova_alerta_2min']} filas_2min {r['mirova_filas_2min']} "
              f"cinturon_60min {r['cinturon_60min_vrp']}")
    (OUT / ("medir_ocultos" + (sys.argv[1] if len(sys.argv) > 1 else "") + ".json")).write_text(json.dumps({
        "control": ctrl, "referencia": {k: v.get("sha") for k, v in info.items()},
        "tabla": [list(k) + [n] for k, n in sorted(tabla.items())],
        "ocultos_index": filas_marcadas,
        "via": via}, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
