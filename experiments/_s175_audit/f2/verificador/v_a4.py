# -*- coding: utf-8 -*-
"""A4: ejecuta enrichWithMirovaConfirmation del index.html de la base con node (extraida, no portada) sobre los
records de los 11 volcanes y data/mirova/<vol>.json, y cruza con los records V375 nocturnos publicados por la vara.

Uso: python v_a4.py <arbol_base> <json_de_v_a1_a3> <tmpdir>
"""
import bisect
import collections
import io
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
A = Path(sys.argv[1]).resolve()
PREV = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
TMP = Path(sys.argv[3])
sys.path.insert(0, str(A))
sys.path.insert(0, str(A / "scripts"))
import banco_paridad as bp  # noqa: E402
import referencia_mirova_unificada as rmu  # noqa: E402

JS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function extraer(nombre) {
  const i = src.indexOf('function ' + nombre + '(');
  if (i < 0) throw new Error('no encontre ' + nombre);
  let j = src.indexOf('{', i), d = 0;
  for (let k = j; k < src.length; k++) { if (src[k] === '{') d++; else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); } }
  throw new Error('no cerro ' + nombre);
}
eval(['parseUtcMs','sensorGroup','ourSensorBucket','mirovaSensorBucket','enrichWithMirovaConfirmation'].map(extraer).join('\n'));
const job = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = {};
for (const [vol, recs, mir] of job) {
  enrichWithMirovaConfirmation(recs, mir);
  out[vol] = recs.map(r => [r.sensor, r.datetime_utc, r._mirova_confirmed ? 1 : 0]);
}
console.log(JSON.stringify(out));
"""


def node(job):
    TMP.mkdir(parents=True, exist_ok=True)
    (TMP / "a4.js").write_text(JS, encoding="utf-8")
    (TMP / "a4_job.json").write_text(json.dumps(job), encoding="utf-8")
    o = subprocess.run(["node", "--max-old-space-size=4096", str(TMP / "a4.js"), str(A / "frontend" / "index.html"),
                        str(TMP / "a4_job.json")], capture_output=True, text=True, timeout=900)
    if o.returncode != 0:
        raise RuntimeError(o.stderr[-2000:])
    return json.loads(o.stdout)


# ---- controles sinteticos (instrumento vivo y capaz de dar 0)
mir_s = [{"datetime_utc": "2026-05-01 05:00", "sensor": "VIIRS375", "VRP_MW": 0.03, "distancia_km": 40.0, "clasificacion": "Muy Bajo"},
         {"datetime_utc": "2026-05-02 05:00", "sensor": "VIIRS375", "VRP_MW": 0.0, "distancia_km": 1.0, "clasificacion": "Bajo"},
         {"datetime_utc": "2026-05-03 05:00", "sensor": "VIIRS375", "VRP_MW": 5.0, "distancia_km": 1.0, "clasificacion": "RUTINA"},
         {"datetime_utc": "2026-05-04 05:00", "sensor": "VIIRS", "VRP_MW": 5.0, "distancia_km": 1.0, "clasificacion": "Bajo"}]
rec_s = [{"sensor": "VIIRS_SNPP", "datetime_utc": "2026-05-01 05:59"},   # 59 min, 0,03 MW a 40 km -> esperado 1
         {"sensor": "VIIRS_SNPP", "datetime_utc": "2026-05-01 06:01"},   # 61 min -> 0
         {"sensor": "VIIRS_SNPP", "datetime_utc": "2026-05-02 05:00"},   # VRP 0 -> 0
         {"sensor": "VIIRS_SNPP", "datetime_utc": "2026-05-03 05:00"},   # RUTINA -> 0
         {"sensor": "VIIRS_SNPP", "datetime_utc": "2026-05-04 05:00"},   # otro bucket (750) -> 0
         {"sensor": "VIIRS_SNPP_750", "datetime_utc": "2026-05-04 05:00"}]  # mismo bucket 750 -> 1
c = node([["sint", rec_s, mir_s], ["vacio", [dict(x) for x in rec_s], []]])
print("control sintetico (esperado 1,0,0,0,0,1):", [x[2] for x in c["sint"]], "| con MIROVA vacio (esperado 0s):", [x[2] for x in c["vacio"]])

# ---- datos reales
job = []
mir_all = {}
for vol in bp.VOLS:
    recs = json.load(open(A / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
    mir = json.load(open(A / "data" / "mirova" / f"{vol}.json", encoding="utf-8")).get("records") or []
    mir_all[vol] = mir
    job.append([vol, [{"sensor": r.get("sensor"), "datetime_utc": r.get("datetime_utc")} for r in recs], mir])
res = node(job)
conf = {}
for vol, lst in res.items():
    for sen, t, k in lst:
        conf[(vol, sen, t)] = k

# referencia unificada cruda (todas las filas y tipos), por (vol, bucket)
filas = rmu.cargar_referencia_unificada(rmu.SNAP_CONS, rmu.SNAP_OCR)
ref = collections.defaultdict(list)
for f in filas:
    ref[(f["volcano"], f["sensor_bucket"])].append(datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S"))
for v in ref.values():
    v.sort()
mirj = collections.defaultdict(list)
for vol, mm in mir_all.items():
    for m in mm:
        if str(m.get("sensor")).upper() == "VIIRS375":
            mirj[vol].append(datetime.strptime(m["datetime_utc"][:16], "%Y-%m-%d %H:%M"))
for v in mirj.values():
    v.sort()


def hay(lista, t, s):
    i = bisect.bisect_left(lista, t - timedelta(seconds=s))
    return i < len(lista) and lista[i] <= t + timedelta(seconds=s)


pubs = [r for r in PREV["v375"] if r["pub"]]
cnt = collections.Counter()
porvol = collections.Counter()
for r in pubs:
    t = datetime.fromisoformat(r["dt"]).replace(tzinfo=None)
    k = conf.get((r["vol"], r["sensor"], t.strftime("%Y-%m-%d %H:%M")))
    if k is None:
        cnt["sin_cruce"] += 1
        continue
    a = hay(ref[(r["vol"], "VIIRS375")], t, 120)
    b = hay(mirj[r["vol"]], t, 120)
    cnt[("conf", k)] += 1
    if k:
        cnt["conf_sin_ref_unificada_120s"] += (not a)
        cnt["conf_sin_data_mirova_120s"] += (not b)
        cnt["conf_sin_ninguna_120s"] += (not a and not b)
        if not a:
            porvol[r["vol"]] += 1
        cnt["conf_lab_" + r["lab"]] += 1
print("V375 nocturnos publicados por la vara:", len(pubs))
print(dict(cnt))
print("confirmados sin fila en la referencia unificada a +-120 s, por volcan:", dict(porvol))
neg = [r for r in PREV["v375"] if r["lab"] == "neg_limpio" and r["pub"]]
print("neg_limpio publicados confirmados:",
      sum(conf.get((r["vol"], r["sensor"], datetime.fromisoformat(r["dt"]).strftime("%Y-%m-%d %H:%M")), 0) for r in neg), "de", len(neg))
allv = [r for r in PREV["v375"]]
print("todos los V375 nocturnos (pub o no) confirmados:",
      sum(conf.get((r["vol"], r["sensor"], datetime.fromisoformat(r["dt"]).strftime("%Y-%m-%d %H:%M")), 0) for r in allv), "de", len(allv))

# ---- desglose: confirmados sin fila en data/mirova a +-120 s pero CON fila en la referencia unificada: que tipo tienen
reft = collections.defaultdict(list)
for f in filas:
    reft[(f["volcano"], f["sensor_bucket"])].append((datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S"), f))
for v in reft.values():
    v.sort(key=lambda x: x[0])
tipos = collections.Counter()
ej = []
for r in pubs:
    t = datetime.fromisoformat(r["dt"]).replace(tzinfo=None)
    if not conf.get((r["vol"], r["sensor"], t.strftime("%Y-%m-%d %H:%M"))):
        continue
    if hay(mirj[r["vol"]], t, 120):
        continue
    fs = [f for (tt, f) in reft[(r["vol"], "VIIRS375")] if abs((tt - t).total_seconds()) <= 120]
    if fs:
        tipos[tuple(sorted({(f["source"], f["tipo"], f.get("origen", "")) for f in fs}))] += 1
        if len(ej) < 5:
            ej.append((r["vol"], r["sensor"], t.isoformat(), [(f["source"], f["tipo"], f["vrp_mw"]) for f in fs]))
print("desglose de los confirmados sin fila en data/mirova pero con fila en la referencia unificada:", sum(tipos.values()))
for k, n in tipos.most_common():
    print("   ", n, k)
print("   ejemplos:", ej)
