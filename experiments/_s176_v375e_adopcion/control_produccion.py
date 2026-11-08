# -*- coding: utf-8 -*-
"""S176: el PR A no cambia lo publicado. Comparación bit a bit con y sin el PR sobre los datos reales de data/.

POR QUÉ, COMO GEÓLOGO. Lo que el operador ve son los records de data/mirova_equivalent/ y los informes que los juzgan. Si este
PR moviera algo con los flags apagados, una alerta podría cambiar sin que nadie lo decidiera. La prueba directa sería reprocesar
un volcán-día con y sin el PR, pero exige bajar gránulos de NASA (A71: nada de llamadas reales aquí) y no hay gránulos L1B reales
en disco: queda SIN DATO, y se declara. En su lugar:
  1. El código que escribe records es byte a byte el mismo: `pipeline/` (salvo el perfil nuevo), run_pipeline y volcanoes.yaml.
  2. Todo perfil existente resuelve exactamente las mismas constantes en pipeline.profile con y sin el PR (A89).
  3. Lo que el PR sí toca (audit semanal, vigilancia de K, vigilancia de la guardia de MODIS y marca del tablero) da exactamente lo
     mismo, sin contar la hora de generación, corrido sobre los mismos records reales con el código de main y con el de la rama.
Control positivo (A110): la comparación de 3 se repite con un record real de VIIRS marcado como vía, y tiene que dar distinto.

Uso: python -I experiments/_s176_v375e_adopcion/control_produccion.py <base> <carpeta temporal>
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
RUNNER = r'''
import json, os, sys
from pathlib import Path
arbol, salida, modo = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
sys.path[:0] = [str(arbol), str(arbol / "scripts")]
os.chdir(arbol)
salida.mkdir(parents=True, exist_ok=True)
def sin_hora(d):
    if isinstance(d, dict):
        return {k: sin_hora(v) for k, v in d.items() if k not in ("generated_utc", "processed_utc")}
    return [sin_hora(x) for x in d] if isinstance(d, list) else d
if modo == "perfiles":
    import importlib, pipeline.profile as p
    out = {}
    for f in sorted((arbol / "pipeline" / "profiles").glob("*.yaml")):
        os.environ["VRP_PROFILE"] = f.stem
        importlib.reload(p)
        out[f.stem] = {k: repr(sorted(v) if isinstance(v, (set, frozenset)) else v) for k, v in vars(p).items() if k.isupper()}
    (salida / "perfiles.json").write_text(json.dumps(out, sort_keys=True), encoding="utf-8")
else:
    hoy = sys.argv[4]
    import auto_audit_weekly as aa
    if modo == "marcar":                 # control positivo: un record real de VIIRS pasa a ser de la vía
        import copy
        orig = aa.cargar_records
        def falso():
            r, i = orig()
            r = copy.deepcopy(r)
            for recs in r.values():
                for x in recs:
                    if str(x.get("sensor")).startswith("VIIRS") and str(x.get("datetime_utc")) >= "2026-11-05":
                        x["via_codigo_mirova"] = True
            return r, i
        aa.cargar_records = falso
    aa.OUTDIR = str(salida)
    aa.main()
    (salida / "audit.json").write_text(json.dumps(sin_hora(json.load(open(salida / "latest.json", encoding="utf-8"))), sort_keys=True), encoding="utf-8")
    import vigilancia_sombra as vs
    (salida / "vig_k.json").write_text(json.dumps(sin_hora(vs.evaluar(hoy)), sort_keys=True, default=str), encoding="utf-8")
    import vigilancia_guardia_modis as vg
    (salida / "vig_modis.json").write_text(json.dumps(sin_hora(vg.evaluar(hoy)), sort_keys=True, default=str), encoding="utf-8")
'''
MARCA = r'''
const M = require(process.argv[1]);
const fs = require('fs'), path = require('path');
const d = process.argv[2], res = {};
for (const f of fs.readdirSync(d).filter(x => x.endsWith('.json'))) {
  const recs = JSON.parse(fs.readFileSync(path.join(d, f), 'utf8')).records;
  res[f] = M.primeraViaModis(recs);
}
const avisos = [];
const doc = { body: { insertBefore(){} , firstChild: null}, getElementById: id => null, querySelector: () => null,
  createElement: () => ({ style: {}, setAttribute(){}, appendChild(){}, }), createTextNode: t => { avisos.push(t); return {}; } };
for (const f of fs.readdirSync(d).filter(x => x.endsWith('.json')))
  M.notarRecords(JSON.parse(fs.readFileSync(path.join(d, f), 'utf8')).records, doc);
console.log(JSON.stringify({ res, desde: M.viaModisDesde(), avisos: avisos.filter(a => a.startsWith('Desde')) }));
'''


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def correr(arbol, salida, modo, hoy=""):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONHASHSEED="0")
    r = subprocess.run([sys.executable, "-c", RUNNER, str(arbol), str(salida), modo] + ([hoy] if hoy else []),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if r.returncode != 0:
        print(f"FALLA {arbol} {modo}:\n" + r.stderr[-2500:])
        sys.exit(1)


def main(base, temp):
    temp = Path(temp)
    base = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", base], capture_output=True, text=True).stdout.strip()
    arbol_base = temp / "arbol_base"
    if not arbol_base.exists():
        arbol_base.mkdir(parents=True)
        a = subprocess.run(["git", "-C", str(RAIZ), "archive", base, "scripts", "pipeline", "frontend", "volcanoes.yaml",
                            "experiments/_s171_modd_adopcion",
                            "experiments/_s151_prereg_fk_11"], capture_output=True)
        assert a.returncode == 0
        subprocess.run(["tar", "-x", "-C", str(arbol_base)], input=a.stdout, check=True)
        subprocess.run(["cmd", "/c", "mklink", "/J", str(arbol_base / "data"), str(RAIZ / "data")], check=True,
                       capture_output=True)
    print("== 1. código que escribe records, byte a byte (git)")
    r = subprocess.run(["git", "-C", str(RAIZ), "diff", "--name-status", base, "HEAD", "--", "pipeline", "scripts/run_pipeline.py",
                        "volcanoes.yaml", ".github/workflows/nrt.yml"], capture_output=True, text=True).stdout.strip()
    print("  diff en pipeline/, run_pipeline, volcanoes.yaml y nrt.yml:", r or "(nada)")
    assert r in ("A\tpipeline/profiles/guardia_k_viirs.yaml",), r
    print("== 2. constantes de todos los perfiles existentes en pipeline.profile")
    correr(arbol_base, temp / "s_base", "perfiles")
    correr(RAIZ, temp / "s_rama", "perfiles")
    pb, pr = (json.loads((temp / d / "perfiles.json").read_text(encoding="utf-8")) for d in ("s_base", "s_rama"))
    nuevos = sorted(set(pr) - set(pb))
    # El catálogo trae el perfil nuevo y la ruta es la de cada árbol: son las dos únicas constantes que deben diferir.
    fuera = {"VALID_PROFILES", "PROFILES_DIR"}
    distintos = sorted(n for n in pb if {k: v for k, v in pb[n].items() if k not in fuera}
                       != {k: v for k, v in pr.get(n, {}).items() if k not in fuera})
    print(f"  perfiles en main: {len(pb)}; nuevos en la rama: {nuevos}; distintos: {distintos}")
    assert nuevos == ["guardia_k_viirs"] and not distintos
    print("== 3. audit, vigilancias y marca, sobre los mismos records reales")
    hoy = subprocess.run(["date", "-u", "+%Y-%m-%d"], capture_output=True, text=True).stdout.strip()
    correr(arbol_base, temp / "s_base", "normal", hoy)
    correr(RAIZ, temp / "s_rama", "normal", hoy)
    for f in ("audit.json", "vig_k.json", "vig_modis.json"):
        a, b = sha(temp / "s_base" / f), sha(temp / "s_rama" / f)
        print(f"  {f}: {'IDENTICO' if a == b else 'DISTINTO'} sha256 {a[:16]}")
        assert a == b, f
    salidas = [subprocess.run(["node", "-e", MARCA, "--", str(a / "frontend" / "cambio_detector.js"), str(RAIZ / "data" / "mirova_equivalent")],
                              capture_output=True, text=True, encoding="utf-8") for a in (arbol_base, RAIZ)]
    assert all(x.returncode == 0 for x in salidas), [x.stderr[-400:] for x in salidas]
    m = [x.stdout for x in salidas]
    print("  marca del tablero (primera vía de MODIS por volcán, fecha y avisos):", "IDENTICO" if m[0] == m[1] else "DISTINTO")
    print("   ", m[1][:220])
    assert m[0] == m[1] and m[1].strip()
    print("== control positivo: con records reales de VIIRS marcados como vía, la rama tiene que dar distinto")
    correr(RAIZ, temp / "s_marca", "marcar", hoy)
    a, b = sha(temp / "s_rama" / "audit.json"), sha(temp / "s_marca" / "audit.json")
    print("  audit.json:", "DISTINTO" if a != b else "IDENTICO", "(tiene que ser DISTINTO)")
    assert a != b
    salida = json.loads((temp / "s_marca" / "audit.json").read_text(encoding="utf-8"))
    print("  por_detector:", sorted(salida["por_detector"]), "| vigente_por_sensor:", salida["detector"].get("vigente_por_sensor"))
    assert {"VIA_V375", "VIA_V750"} <= set(salida["por_detector"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
