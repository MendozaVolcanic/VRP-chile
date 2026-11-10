#!/usr/bin/env python
"""S175 decision 7 (F2-204, V2-04): cuantas marcas «MIROVA confirmo» cambian al pasar de ±60 min sin D-9 a la
misma pasada (±120 s) con D-9, y si algun record cambia de filtro de artefacto (la marca exime de los filtros de
cirro y campo difuso, asi que ahi si se tocaria lo publicado).

POR QUE ASI. Las dos marcas salen de la funcion REAL del tablero (`enrichWithMirovaConfirmation` extraida del
HTML y ejecutada con node, A97), no de un port: la de antes del `index.html` de un commit (por defecto
origin/main) y la de despues del `index.html` del arbol. «Publicado» es el predicado del tablero que ya corre
`banco_paridad.cargar_nuestros` (node, sin la marca, que no entra al predicado).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Si lo medido estuviera roto, lo veria: el control `antes_vs_antes`
corre la funcion vieja dos veces y tiene que dar 0 cambios; y la nueva marca tiene que ser un subconjunto de la
vieja (la ventana se achica y D-9 solo quita), asi que `nuevas_sin_vieja` tiene que dar 0. (2) Instrumento
muerto: si la extraccion fallara node cae con error; `artefacto_sin_exencion` cuenta cuantos records serian
artefacto con la marca forzada a false (si da 0, la exencion no tiene que eximir y el 0 de `cambia_filtro` no
dice nada del caso con artefactos; la funcion misma la vigila tests/test_filtro_cirrus_no_oculta_via_s173.py); y la cuenta de la vieja sobre V375 publicados se compara
con la de F2 (2.225 de 2.632 en 2026-03-01..2026-11-07 con el arbol 752d348bc; el corpus crece, A90, asi que
se espera parecida, no igual).

Uso: python medir.py [--antes REF] [--ini 2026-03-01] [--fin AAAA-MM-DD] > salida
"""
import argparse, collections, json, os, subprocess, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402

_JS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function extraer(nombre) {
  const i = src.indexOf('function ' + nombre + '(');
  if (i < 0) throw new Error('no encontre function ' + nombre);
  let j = src.indexOf('{', i), d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  throw new Error('no cerro ' + nombre);
}
const CambioDetector = require(require('path').join(require('path').dirname(process.argv[3]), 'cambio_detector.js'));
const consts = (src.match(/^const (INNER_RADIUS_KM|MIROVA_\w+)\s*=[^;]+;/gm) || []).join('\n');
let includeFarDistance = false;
eval(consts + '\n' + ['parseUtcMs', 'sensorGroup', 'ourSensorBucket', 'mirovaSensorBucket',
  'enrichWithMirovaConfirmation', 'mirovaEqVrp', 'isCirrusArtifact', 'isDiffuseFieldArtifact'].map(extraer).join('\n'));
const job = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
const out = {};
for (const [vol, rutaRec, rutaMir, inner] of job) {
  const recs = JSON.parse(fs.readFileSync(rutaRec, 'utf8')).records || [];
  const mir = JSON.parse(fs.readFileSync(rutaMir, 'utf8')).records || [];
  enrichWithMirovaConfirmation(recs, mir);
  out[vol] = recs.map(r => [r.datetime_utc, r.sensor, r._mirova_confirmed ? 1 : 0,
                            isCirrusArtifact(r, inner) ? 1 : 0, isDiffuseFieldArtifact(r, inner) ? 1 : 0,
                            // control: el filtro sin la exencion (marca forzada a false), para saber si la exencion
                            // tiene algo que eximir
                            ((x) => (isCirrusArtifact(x, inner) || isDiffuseFieldArtifact(x, inner)) ? 1 : 0)(
                              Object.assign({}, r, { _mirova_confirmed: false }))]);
}
process.stdout.write(JSON.stringify(out));
"""


def correr(html, tmp):
    inner = bp.inner_desde_html()
    job = [[v, str(ROOT / "data" / "mirova_equivalent" / f"{v}.json"), str(ROOT / "data" / "mirova" / f"{v}.json"),
            inner[v]] for v in bp.VOLS]
    (tmp / "job.json").write_text(json.dumps(job), encoding="utf-8")
    (tmp / "r.js").write_text(_JS, encoding="utf-8")
    p = subprocess.run(["node", "--max-old-space-size=4096", str(tmp / "r.js"), str(html),
                        str(ROOT / "frontend" / "x"), str(tmp / "job.json")], capture_output=True, text=True,
                       encoding="utf-8", timeout=900)
    if p.returncode != 0:
        raise SystemExit("node fallo con %s: %s" % (html, p.stderr[-1500:]))
    return json.loads(p.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--antes", default="origin/main")
    ap.add_argument("--ini", default="2026-03-01")
    ap.add_argument("--fin", default="2099-12-31")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="s175_confirmo_") as t:
        tmp = Path(t)
        viejo = tmp / "index_antes.html"
        viejo.write_bytes(subprocess.run(["git", "-C", str(ROOT), "show", f"{a.antes}:frontend/index.html"],
                                         capture_output=True, check=True).stdout)
        sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", a.antes], capture_output=True, text=True).stdout.strip()
        A, A2, D = correr(viejo, tmp), correr(viejo, tmp), correr(ROOT / "frontend" / "index.html", tmp)
    print(f"antes = frontend/index.html de {a.antes} ({sha}); despues = arbol de trabajo")
    print(f"control antes_vs_antes (tiene que dar 0): {sum(x != y for v in A for x, y in zip(A[v], A2[v]))}")

    # 1) Todos los records, toda la historia: marca y filtros de artefacto
    c = collections.Counter()
    for v in bp.VOLS:
        assert len(A[v]) == len(D[v]) and all(x[:2] == y[:2] for x, y in zip(A[v], D[v]))
        for x, y in zip(A[v], D[v]):
            c["records"] += 1
            c["conf_antes"] += x[2]; c["conf_despues"] += y[2]
            c["nuevas_sin_vieja (tiene que dar 0)"] += int(y[2] and not x[2])
            c["artefacto_antes"] += int(x[3] or x[4]); c["artefacto_despues"] += int(y[3] or y[4])
            c["cambia_filtro_artefacto"] += int((x[3], x[4]) != (y[3], y[4]))
            c["artefacto_sin_exencion (control)"] += y[5]
    print("\n1) todos los records de los 11 Tier A, toda la historia, todos los sensores")
    print(json.dumps(dict(c), ensure_ascii=False))

    # 2) Publicados (predicado del tablero), por sensor, en la ventana
    idx = {}
    dup = 0
    for v in bp.VOLS:
        for x, y in zip(A[v], D[v]):
            k = (v, x[0], x[1])
            if k in idx and idx[k] != (x[2], y[2]):
                dup += 1
            idx[k] = (x[2], y[2])
    recs = bp.cargar_nuestros(bp._coords_por_volcan(), bp.inner_desde_html(), (a.ini, a.fin))
    por = collections.defaultdict(collections.Counter)
    for r in recs:
        if not r["pub"]:
            continue
        k = (r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), r["sensor"])
        if k not in idx:
            por[r["b"]]["sin_par (tiene que dar 0)"] += 1
            continue
        old, new = idx[k]
        s = por[r["b"]]
        s["publicados"] += 1; s["conf_antes"] += old; s["conf_despues"] += new
        s["pierden_marca"] += int(old and not new); s["ganan_marca"] += int(new and not old)
    print(f"\n2) publicados (predicado del tablero), ventana {a.ini}..{a.fin}; claves repetidas con marca distinta: {dup}")
    tot = collections.Counter()
    for b in ("MODIS", "VIIRS375", "VIIRS750"):
        print(b, json.dumps(dict(por[b]), ensure_ascii=False)); tot.update(por[b])
    print("TOTAL", json.dumps(dict(tot), ensure_ascii=False))


if __name__ == "__main__":
    main()
