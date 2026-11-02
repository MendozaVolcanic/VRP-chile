# -*- coding: utf-8 -*-
"""V1: qué hacen los instrumentos de A (auto_audit_weekly, cambio_detector.js, es_k de test_guard_serie_k_pura,
vigilancia_sombra de A) con records sintéticos de MODIS: K antes, vía en medio, K después (= tras un revert de B).
Read-only: importa los módulos del worktree y usa funciones puras. Pregunta 1: si estuviera roto, ¿lo veo? Sí: el
detector asignado y la fecha de la marca son la salida. Pregunta 2: control positivo incluido (record sin marca -> C0)."""
import sys, os, json, subprocess
sys.path.insert(0, "scripts"); sys.path.insert(0, "tests")
import auto_audit_weekly as aa
import test_guard_serie_k_pura_s158 as gk

def rec(dt, via=None, sha="abc"):
    r = {"datetime_utc": dt, "sensor": "MODIS_AQUA", "regimen": ({"codigo_sha": sha} if sha else None)}
    if via is not None: r["via_codigo_mirova"] = via
    return r

k_antes  = rec("2026-11-01 05:00")
via_rec  = rec("2026-11-03 05:00", via=True)
caida_k  = rec("2026-11-04 05:00", via="sin_mxd03")
k_post   = rec("2026-11-06 05:00")            # tras el revert: K otra vez, sin la clave
c0_ctrl  = rec("2025-01-01 05:00", sha=None)  # control positivo: sin marca -> C0
recs = {"Lascar": [k_antes, via_rec, caida_k, k_post, c0_ctrl]}
front = aa.frontera_via_modis(recs)
print("169 frontera_via_modis =", front)
for nombre, r in [("k_antes", k_antes), ("via", via_rec), ("caida_k", caida_k), ("k_post_revert", k_post), ("c0_ctrl", c0_ctrl)]:
    print(f"169 {nombre:14s} detector_de_record={aa.detector_de_record(r, '2025-02-15'):9s} "
          f"detector_de_noche={aa.detector_de_noche(r['datetime_utc'], '2025-02-15', 'MODIS', front)}")
print("167 es_k(via_rec) =", gk.es_k(via_rec), "; es_k(k_post) =", gk.es_k(k_post), "; es_k(c0_ctrl) =", gk.es_k(c0_ctrl))
# 161: el filtro de producción «sólo K» de vigilancia_sombra en A es r.get('sha') del banco (banco_paridad.py:289 lee regimen.codigo_sha)
print("161 sha que leería el banco para via_rec =", (via_rec.get("regimen") or {}).get("codigo_sha"))
# cambio_detector.js primeraViaModis con los mismos records (node)
js = r"""
const fs=require('fs'); const src=fs.readFileSync(process.argv[2],'utf8');
function extraer(n){const i=src.indexOf('function '+n+'('); let j=src.indexOf('{',i), d=0; for(let k=j;k<src.length;k++){if(src[k]==='{')d++; else if(src[k]==='}'){d--; if(d===0) return src.slice(i,k+1);}}}
eval(extraer('isoDeRecord')); eval(extraer('primeraViaModis'));
const recs=JSON.parse(process.argv[3]);
console.log('169 cambio_detector primeraViaModis(K antes, via, caida, K despues)=', primeraViaModis(recs));
console.log('169 control: solo K =', primeraViaModis(recs.filter(r=>r.via_codigo_mirova===undefined)));
"""
open(os.path.join(os.environ["V"], "cd.js"), "w", encoding="utf-8").write(js)
o = subprocess.run(["node", os.path.join(os.environ["V"], "cd.js"), os.path.abspath("frontend/cambio_detector.js"), json.dumps(recs["Lascar"])], capture_output=True, text=True)
print(o.stdout.strip(), o.stderr.strip()[-300:])
