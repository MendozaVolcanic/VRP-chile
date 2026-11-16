#!/usr/bin/env python
"""F2 S175: el banco fija _mirova_confirmed = false; el navegador lo calcula. ¿Cuanto cambia lo publicado?

POR QUE. En frontend/index.html, isCirrusArtifact e isDiffuseFieldArtifact devuelven false si el record trae
_mirova_confirmed, y esa marca la pone enrichWithMirovaConfirmation: cualquier fila de data/mirova/<volcan>.json con
VRP > 0 y clase distinta de NULO/RUTINA, mismo bucket, a +-60 min, sin mirar distancia ni la regla D-9. El banco
(banco_paridad.correr_node) la deja en false a proposito (la etiqueta no puede entrar al predicado). Si en algun record
la marca cambia la publicacion, el tablero que ve el operador y la vara del banco no son el mismo predicado.

Corre con node las funciones EXTRAIDAS de index.html del arbol (no portadas): el predicado de banco_paridad mas
enrichWithMirovaConfirmation, parseUtcMs, sensorGroup, ourSensorBucket y mirovaSensorBucket, sobre todos los records de
los 11 Tier A en la ventana (de dia y de noche, todos los sensores) y data/mirova/<volcan>.json del arbol.
Tres versiones: (a) confirmado false (banco); (b) confirmado como el navegador; (c) como el navegador pero sin las
filas VIIRS375 de 0,05 MW o menos (D-9). Controles: (P1) cuantos records quedan confirmados y cuantos son artefacto en
(a): si no hubiera artefactos, la medicion no podria ver nada y se dice; (P2) n por sensor impreso.
Uso: python confirmado_navegador.py <arbol> <inicio> <fin> <salida.txt>
"""
import collections, json, os, subprocess, sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve(); INI, FIN, OUT = sys.argv[2], sys.argv[3], Path(sys.argv[4])
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402

JS = bp._JS.split("const casos = JSON.parse")[0].replace(
    "'isSummitDetection'].map(extraer)",
    "'isSummitDetection','parseUtcMs','sensorGroup','ourSensorBucket','mirovaSensorBucket',"
    "'enrichWithMirovaConfirmation'].map(extraer)") + r"""
const entrada = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = {};
for (const [vol, inner, recs, mir] of entrada) {
  const pred = () => recs.map(r => { const s = isSummitDetection(r), v = isValidDetection(r), a = isThermalArtifact(r, inner),
                                       d = mirovaEqVrpDisplay(r, inner, false); return [(s && v && !a && d > 0) ? 1 : 0, a ? 1 : 0]; });
  recs.forEach(r => { r._mirova_confirmed = false; });
  const a = pred();
  enrichWithMirovaConfirmation(recs, mir);
  const conf = recs.map(r => r._mirova_confirmed ? 1 : 0);
  const b = pred();
  const mir2 = mir.filter(m => !(mirovaSensorBucket(m.sensor || m.Sensor) === 'VIIRS375' && parseFloat(m.VRP_MW ?? m.vrp_mw ?? 0) <= 0.05 + 1e-9));
  enrichWithMirovaConfirmation(recs, mir2);
  const conf2 = recs.map(r => r._mirova_confirmed ? 1 : 0);
  const c = pred();
  out[vol] = recs.map((r, i) => [a[i][0], b[i][0], c[i][0], conf[i], conf2[i], a[i][1]]);
}
console.log(JSON.stringify(out));
"""
assert "enrichWithMirovaConfirmation" in JS
inner = bp.inner_desde_html()
entrada, meta = [], {}
for vol in bp.VOLS:
    d = json.load(open(ARBOL / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))
    mir = json.load(open(ARBOL / "data" / "mirova" / f"{vol}.json", encoding="utf-8"))["records"]
    recs = []
    for r in d["records"]:
        if not (INI <= (r.get("datetime_utc") or "")[:10] <= FIN) or bp.bucket(r.get("sensor")) is None:
            continue
        slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        slim["datetime_utc"] = r["datetime_utc"]
        if r.get("f5_core_vrp_mw") is None:
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (r.get("anomaly_pixels") or [])]
        recs.append(slim)
    meta[vol] = [(x["sensor"], x["datetime_utc"]) for x in recs]
    entrada.append([vol, inner[vol], recs, mir])
tmp = Path(tempfile.mkdtemp(dir=r"C:\Users\nmend\vrp-temporales\s175_audit\f2"))
(tmp / "r.js").write_text(JS, encoding="utf-8"); (tmp / "c.json").write_text(json.dumps(entrada), encoding="utf-8")
o = subprocess.run(["node", "--max-old-space-size=4096", str(tmp / "r.js"), str(bp.HTML), str(tmp / "c.json")],
                   capture_output=True, text=True, timeout=900)
if o.returncode != 0:
    sys.exit("node fallo: " + o.stderr[-2000:])
res = json.loads(o.stdout)
c = collections.Counter(); difs = []
for vol in bp.VOLS:
    for (sen, dt), (pa, pb, pc_, cf, cf2, art) in zip(meta[vol], res[vol]):
        b = bp.bucket(sen)
        c[(b, "n")] += 1; c[(b, "pub_banco")] += pa; c[(b, "pub_navegador")] += pb; c[(b, "pub_nav_sin_minimas")] += pc_
        c[(b, "confirmado")] += cf; c[(b, "confirmado_sin_minimas")] += cf2; c[(b, "artefacto_banco")] += art
        if pa != pb or pb != pc_:
            difs.append(f"{vol} {dt} {sen} banco {pa} navegador {pb} nav_sin_minimas {pc_} confirmado {cf}/{cf2} artefacto {art}")
L = [f"arbol {ARBOL.name} ventana {INI}..{FIN} sha index.html blob {subprocess.run(['git','hash-object',str(bp.HTML)],capture_output=True,text=True).stdout.strip()}"]
for b in bp.BUCKETS:
    L.append(f"{b}: " + ", ".join(f"{k} {c[(b, k)]}" for k in ("n", "pub_banco", "pub_navegador", "pub_nav_sin_minimas",
                                                              "confirmado", "confirmado_sin_minimas", "artefacto_banco")))
L.append(f"records con publicacion distinta: {len(difs)}"); L += difs
OUT.write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L[:60]))
