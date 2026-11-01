# -*- coding: utf-8 -*-
"""Bateria de mutaciones con control (A110) para el merge que conserva la base.

POR QUE: que las pruebas pasen no dice que vigilen algo. Cada mutacion rompe a
proposito una pieza del arreglo (en el script o en el paso del workflow) y se
mira si alguna prueba la atrapa POR ASERCION sobre el resultado. Una prueba que
falla porque el codigo se cae (excepcion de Python, o el paso de bash sale con
error, etiqueta PASO_CAYO) no cuenta como atrapada: es una caida, y se informa
aparte (regla de S156, mutacion que cae no es atrapada).

Controles:
  - sin mutacion: todo pasa (si no, la bateria no mide nada);
  - caida deliberada (error de sintaxis): tiene que clasificarse como CAIDA;
  - las mutaciones equivalentes conocidas se declaran antes de correr.

Trabaja sobre una COPIA (no toca el worktree), asi que no edita archivos que
otra corrida este leyendo (A112).

Uso: python experiments/_s157_merge_conserva/mutaciones.py
Escribe resultado_mutaciones.json al lado.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
SCRIPT = "scripts/merge_chunk_stores.py"
YML = ".github/workflows/reproc-chunked.yml"
PRUEBAS = ["tests/test_merge_chunk_stores.py",
           "tests/test_reproc_chunked_merge_conserva_s157.py"]

# (id, archivo, texto original, texto mutado, que rompe, esperado)
MUTACIONES = [
    ("CTRL_caida", SCRIPT, "def _key(record: dict) -> tuple:",
     "def _key(record: dict) -> tuple:\n    return (", "error de sintaxis (control de caida)", "CAIDA"),
    ("S1_base_ignorada", SCRIPT, "    if base is not None:\n        volcano = base",
     "    if False:\n        volcano = base", "no carga la base", "ATRAPADA"),
    ("S2_resucita_dentro", SCRIPT, "            if _en_alguna((rec.get",
     "            if False and _en_alguna((rec.get", "conserva tambien lo de dentro de la ventana", "ATRAPADA"),
    ("S3_bordes_exclusivos", SCRIPT, "return any(v[0] <= fecha <= v[1]",
     "return any(v[0] < fecha < v[1]", "bordes de ventana abiertos", "ATRAPADA"),
    ("S4_fin_exclusivo", SCRIPT, "return any(v[0] <= fecha <= v[1]",
     "return any(v[0] <= fecha < v[1]", "dia final de la ventana abierto", "ATRAPADA"),
    ("S5_compara_hora", SCRIPT, 'if _en_alguna((rec.get("datetime_utc") or "")[:10], ventanas)',
     'if _en_alguna((rec.get("datetime_utc") or "")[:19], ventanas)', "compara fecha y hora contra la ventana", "ATRAPADA"),
    ("S6_updated_base", SCRIPT, '        updated = base.get("updated", "") or ""',
     '        updated = ""', "ignora el updated de la base", "ATRAPADA"),
    ("S7_claves_base", SCRIPT, "        out = dict(base)", "        out = {}",
     "no hereda las claves de la base", "EQUIVALENTE (la base del store solo tiene volcano, updated, records)"),
    ("S8_sin_control_volcan", SCRIPT, 'and store["volcano"] != volcano):',
     'and False):', "acepta base de otro volcan", "ATRAPADA"),
    ("S9_sin_orden", SCRIPT, 'records = sorted(merged.values(), key=lambda r: r.get("datetime_utc") or "")',
     "records = list(merged.values())", "no ordena por fecha", "ATRAPADA"),
    ("S10_base_sin_ventanas_main", SCRIPT, "        if vent_raw is None:\n            print(\"ERROR: --base exige",
     "        if False:\n            print(\"ERROR: --base exige",
     "quita el rechazo de --base sin --ventanas en main()",
     "EQUIVALENTE (merge_stores tambien lo rechaza, defensa doble)"),
    ("Y1_sin_base", YML, '--base "$BASE" \\\n', "\\\n", "el workflow no pasa --base", "ATRAPADA"),
    ("Y2_base_del_despacho", YML,
     "git fetch -q --depth=1 origin main && git checkout -q -f -B reproc-merge FETCH_HEAD ||",
     "true ||", "une contra el checkout del despacho", "CAIDA o ATRAPADA (git rechaza el push)"),
    ("Y3_push_forzado", YML, "git push origin HEAD:main && exit 0",
     "git push -f origin HEAD:main && exit 0", "push forzado pisa lo que main gano", "ATRAPADA"),
    ("Y4_ventana_invertida", YML, 'VENT="$VENT ${W%%_*}:${W##*_}"',
     'VENT="$VENT ${W##*_}:${W%%_*}"', "ventana mal leida del nombre del artefacto", "ATRAPADA"),
    ("Y6_sin_set_e_off", YML, "          set +e\n", "",
     "deja el `bash -e` de GitHub activo", "CAIDA (el paso sale con error, PASO_CAYO)"),
    ("Y5_ignora_fallo_merge", YML, 'unir || { echo "ERROR: fallo el merge"; exit 1; }',
     "unir || true", "sigue aunque el merge falle", "ATRAPADA"),
]


def _copia(dst: Path, desde: Path = RAIZ):
    for rel in [SCRIPT, YML, *PRUEBAS]:
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(desde / rel, dst / rel)
    (dst / "scripts" / "__init__.py").touch()


def _correr(dst: Path) -> dict:
    xml = dst / "r.xml"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                    "--rootdir", str(dst), f"--junitxml={xml}", *PRUEBAS],
                   cwd=dst, env=env, capture_output=True, text=True, timeout=900)
    if not xml.exists():
        return {"total": 0, "afirma": [], "cae": ["sin junit (coleccion caida)"]}
    afirma, cae, total = [], [], 0
    for tc in ET.parse(xml).getroot().iter("testcase"):
        total += 1
        for f in list(tc.findall("failure")) + list(tc.findall("error")):
            # SOLO el mensaje de la excepcion: el texto completo trae el codigo
            # fuente del helper `_correr`, donde la etiqueta PASO_CAYO aparece
            # siempre (primera corrida: rotulaba como caida lo que era asercion)
            msg = f.get("message") or ""
            nombre = tc.get("name")
            es_asercion = f.tag == "failure" and "AssertionError" in msg.split("\n")[0] \
                or (f.tag == "failure" and msg.lstrip().startswith("assert"))
            if es_asercion and "PASO_CAYO" not in msg:
                afirma.append(nombre)
            else:
                cae.append(nombre)
    return {"total": total, "afirma": afirma, "cae": cae}


def main() -> int:
    base_tmp = Path(os.environ.get("TMP", tempfile.gettempdir()))
    resultados = []
    with tempfile.TemporaryDirectory(dir=base_tmp) as d:
        # foto UNICA del estado a medir: si alguien edita el worktree mientras
        # corre, las mutaciones siguen midiendo lo mismo (A112)
        foto = Path(d) / "foto"
        _copia(foto)
        dst = Path(d) / "trabajo"
        _copia(dst, foto)
        r0 = _correr(dst)
        print(flush=True)
        print(f"CONTROL sin mutacion: {r0['total']} pruebas, "
              f"{len(r0['afirma'])} fallan por asercion, {len(r0['cae'])} caen")
        if r0["afirma"] or r0["cae"] or not r0["total"]:
            print("ABORTO: el control sin mutacion no esta limpio")
            return 1
        for mid, rel, orig, mut, que, esperado in MUTACIONES:
            _copia(dst, foto)
            p = dst / rel
            txt = p.read_text(encoding="utf-8")
            n = txt.count(orig)
            if n != 1:
                print(f"{mid}: el texto original aparece {n} veces, no se aplica")
                resultados.append({"id": mid, "estado": f"NO APLICADA ({n})"})
                continue
            p.write_text(txt.replace(orig, mut), encoding="utf-8", newline="")
            r = _correr(dst)
            if r["afirma"]:
                estado = "ATRAPADA"
            elif r["cae"]:
                estado = "CAIDA"
            else:
                estado = "SOBREVIVE"
            print(f"{mid:28s} {estado:9s} esperado {esperado}; "
                  f"asercion={r['afirma']} caida={r['cae']}", flush=True)
            resultados.append({"id": mid, "archivo": rel, "rompe": que, "estado": estado,
                               "esperado": esperado, "atrapan": r["afirma"], "caen": r["cae"]})
    (AQUI / "resultado_mutaciones.json").write_text(
        json.dumps({"control_sin_mutacion": r0, "mutaciones": resultados},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
