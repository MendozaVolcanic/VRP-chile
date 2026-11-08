# -*- coding: utf-8 -*-
"""F4T (S175), instrumento 4: el canal de aviso. Corre scripts/token_edad.py de la base con tokens sintéticos y después
ejecuta, tal cual están escritos en nrt-healthcheck.yml (base 752d348bc), los bloques Python de los pasos
«Issue de renovacion del token (por transicion)», «Detect stale Tier A» y «Notificar por escalón», con un shim de
`gh` en el PATH que anota cada llamada y devuelve respuestas enlatadas (ninguna llamada real a GitHub).

Línea base roja (2) del plan: en la base, un token «desconocido» (secret ausente o no JWT) no abre issue (hallazgo 124
de F0). Si este instrumento no lo reencuentra, está ciego.

Las dos preguntas:
1. Si el canal estuviera roto (no abre issue cuando debe), ¿se ve? Sí: el shim anota si hubo `gh issue create`.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Sí: control positivo = estado `vencido` sin issue abierto
   tiene que producir `gh issue create`; y el shim con `F4T_LABEL_EXISTE=1` tiene que hacer fallar `gh label create`
   como lo hizo GitHub el 2026-10-04 (run 37215535362).

Además calcula, sin red, en qué corrida de las 12:00 UTC el token vigente (vence 2026-12-07 18:03 UTC, insumo) pasa a
`renovar` con DIAS_AVISO = 10 de scripts/token_edad.py.
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\f4t\repo_base")
BASE_WF = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\f4t\base_wf")
TMP = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\f4t\tmp_04")
TMP.mkdir(parents=True, exist_ok=True)
BASH = r"C:\Program Files\Git\bin\bash.exe"
AHORA = datetime(2026, 11, 7, 4, 10, 45, tzinfo=timezone.utc)  # hora del servidor del insumo


def jwt(exp: datetime) -> str:
    def b64(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return b64({"alg": "RS256"}) + "." + b64({"exp": int(exp.timestamp()), "uid": "f4t"}) + ".firma-falsa"


sys.path.insert(0, str(REPO / "scripts"))
import token_edad  # noqa: E402  (de la base; sin red)

print(f"token_edad.DIAS_AVISO = {token_edad.DIAS_AVISO}")
print("\n## A. scripts/token_edad.py (estado_token) con tokens sintéticos, ahora =", AHORA.isoformat())
TOKENS = {
    "vacío (secret ausente)": "",
    "no JWT ('hola')": "hola",
    "JWT con exp en 2026-12-07 18:03 UTC (el vigente, según el insumo)": jwt(datetime(2026, 12, 7, 18, 3, tzinfo=timezone.utc)),
    "JWT que vence en 5 días": jwt(AHORA + timedelta(days=5)),
    "JWT vencido ayer": jwt(AHORA - timedelta(days=1)),
    "JWT con payload sin exp": "a." + base64.urlsafe_b64encode(b'{"uid":"x"}').decode().rstrip("=") + ".b",
}
ESTADOS = {}
for nombre, tok in TOKENS.items():
    res = token_edad.estado_token(tok, AHORA)
    ESTADOS[nombre] = res
    print(f"- {nombre}: {res}")

print("\n## B. Calendario del aviso para el token vigente (cron del healthcheck: 12:00 UTC diario)")
vence = datetime(2026, 12, 7, 18, 3, tzinfo=timezone.utc)
primera = None
d = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
while d < vence + timedelta(days=2):
    est = token_edad.estado_token(jwt(vence), d)["estado"]
    if est == "renovar" and primera is None:
        primera = d
    if est in ("renovar", "vencido") and d.day in (27, 28, 7, 8):
        print(f"- corrida {d:%Y-%m-%d %H:%M} UTC -> {est} (dias_restantes={token_edad.estado_token(jwt(vence), d)['dias_restantes']})")
    d += timedelta(days=1)
print(f"- primera corrida que da `renovar`: {primera:%Y-%m-%d %H:%M} UTC; vencimiento {vence:%Y-%m-%d %H:%M} UTC; "
      f"margen {(vence - primera).total_seconds() / 86400:.2f} días")

# ---------------------------------------------------------------- bloques del YAML
y = yaml.safe_load((BASE_WF / "nrt-healthcheck.yml").read_text(encoding="utf-8"))
PASOS = {p.get("name"): p for p in y["jobs"]["healthcheck"]["steps"]}


def heredoc(nombre: str) -> str:
    run = PASOS[nombre]["run"]
    m = re.search(r"python - <<'PYEOF'\n(.*?)\n\s*PYEOF", run, re.S)
    if not m:
        raise SystemExit(f"sin heredoc en {nombre}")
    cuerpo = m.group(1)
    # quitar la indentación común del heredoc
    lineas = cuerpo.splitlines()
    ind = min(len(l) - len(l.lstrip()) for l in lineas if l.strip())
    return "\n".join(l[ind:] for l in lineas)


def shim_gh(label_existe: bool, issue_abierto: dict | None) -> Path:
    d = TMP / "shim"
    d.mkdir(exist_ok=True)
    llamadas = TMP / "gh_llamadas.txt"
    if llamadas.exists():
        llamadas.unlink()
    abierto = json.dumps(issue_abierto) if issue_abierto else ""
    (d / "gh").write_text(
        "#!/bin/bash\n"
        f"echo \"gh $*\" >> '{llamadas.as_posix()}'\n"
        "case \"$1 $2\" in\n"
        f"  'issue list') printf '%s' '{abierto}'; exit 0;;\n"
        + ("  'label create') echo 'label with name \"'$3'\" already exists; use `--force` to update its color and description' >&2; exit 1;;\n"
           if label_existe else "  'label create') echo 'creada'; exit 0;;\n")
        + "  'issue create') echo 'https://github.com/x/y/issues/999'; exit 0;;\n"
        "  *) exit 0;;\n"
        "esac\n", encoding="utf-8", newline="\n")
    os.chmod(d / "gh", 0o755)
    return d


def correr_bloque(nombre_paso: str, env_extra: dict, label_existe: bool, issue_abierto: dict | None, cwd: Path | None = None) -> dict:
    codigo = heredoc(nombre_paso)
    shim = shim_gh(label_existe, issue_abierto)
    # En Windows, subprocess.run(["gh", ...]) no resuelve un script de bash llamado `gh`: este preámbulo (lo único que
    # se agrega al bloque del YAML) desvía esa llamada al shim por bash. El resto del bloque corre tal cual está escrito.
    preambulo = (
        "import subprocess as _sp\n"
        "_orig_run = _sp.run\n"
        "def _run(args, *a, **k):\n"
        "    if args and args[0] == 'gh':\n"
        f"        args = [{BASH!r}, {str(shim / 'gh')!r}] + list(args[1:])\n"
        "    return _orig_run(args, *a, **k)\n"
        "_sp.run = _run\n"
    )
    py = TMP / "bloque.py"
    py.write_text(preambulo + codigo, encoding="utf-8")
    env = {"PATH": shim.as_posix() + ":/usr/bin:/bin:" + Path(sys.executable).parent.as_posix().replace("C:", "/c"),
           "GH_REPO": "MendozaVolcanic/VRP-chile", "GH_TOKEN": "no-se-usa",
           "GITHUB_OUTPUT": (TMP / "gh_output.txt").as_posix(), "GITHUB_STEP_SUMMARY": (TMP / "summary.md").as_posix(),
           "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    env.update(env_extra)
    (TMP / "gh_output.txt").write_text("", encoding="utf-8")
    (TMP / "summary.md").write_text("", encoding="utf-8")
    r = subprocess.run([BASH, "-c", f"python '{py.as_posix()}'"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, cwd=cwd or TMP, timeout=120)
    llamadas = (TMP / "gh_llamadas.txt").read_text(encoding="utf-8").splitlines() if (TMP / "gh_llamadas.txt").exists() else []
    return {"exit": r.returncode, "salida": (r.stdout + r.stderr).strip().splitlines(), "gh": llamadas,
            "output": (TMP / "gh_output.txt").read_text(encoding="utf-8")}


def resumen_gh(llamadas):
    return [" ".join(l.split()[:3]) for l in llamadas]


print("\n## C. Paso «Issue de renovacion del token (por transicion)» con shim de gh")
CASOS = [
    ("LÍNEA BASE ROJA (2): desconocido (secret ausente o no JWT), sin issue abierto", {"ESTADO": "desconocido", "VENCE": "", "DIAS": ""}, False, None),
    ("desconocido con la etiqueta ya existente (da igual: no llama a gh)", {"ESTADO": "desconocido", "VENCE": "", "DIAS": ""}, True, None),
    ("CONTROL+: vencido, sin issue abierto, etiqueta NO existe", {"ESTADO": "vencido", "VENCE": "2026-12-07T18:03+00:00", "DIAS": "-0.8"}, False, None),
    ("vencido, sin issue abierto, etiqueta YA existe (hoy existe: API labels)", {"ESTADO": "vencido", "VENCE": "2026-12-07T18:03+00:00", "DIAS": "-0.8"}, True, None),
    ("renovar, sin issue abierto, etiqueta YA existe (lo que pasará el 2026-11-28 12:00 UTC si nadie rotó)", {"ESTADO": "renovar", "VENCE": "2026-12-07T18:03+00:00", "DIAS": "9.3"}, True, None),
    ("vencido, issue abierto en renovar (transición: comenta)", {"ESTADO": "vencido", "VENCE": "2026-12-07T18:03+00:00", "DIAS": "-0.8"}, True, {"number": 999, "body": "<!-- s140-token: renovar -->\n\nx"}),
    ("ok, issue abierto (rotado: cierra)", {"ESTADO": "ok", "VENCE": "2027-01-20T00:00+00:00", "DIAS": "44.0"}, True, {"number": 999, "body": "<!-- s140-token: vencido -->\n\nx"}),
]
for titulo, envx, lab, abierto in CASOS:
    r = correr_bloque("Issue de renovacion del token (por transicion)", envx, lab, abierto)
    print(f"- {titulo}\n    exit={r['exit']} | gh: {resumen_gh(r['gh'])}\n    salida: {' / '.join(s[:110] for s in r['salida'][:3])}")

print("\n## D. Paso «Detect stale Tier A» + «Notificar por escalón» con datos sintéticos de 50 h (lo que deja un token muerto a las 50 h)")
datos = TMP / "repo_falso" / "data" / "mirova_equivalent"
datos.mkdir(parents=True, exist_ok=True)
TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "Chaiten", "Villarrica",
          "NevadosDeChillan", "Llaima", "Copahue"]
for h, etiqueta in ((50, "50 h sin dato"), (20, "control: 20 h, fresco")):
    ultimo = (datetime.now(timezone.utc) - timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for v in TIER_A:
        (datos / f"{v}.json").write_text(json.dumps({"records": [{"datetime_utc": ultimo}]}), encoding="utf-8")
    r1 = correr_bloque("Detect stale Tier A", {}, False, None, cwd=TMP / "repo_falso")
    out = dict(l.split("=", 1) for l in r1["output"].splitlines() if "=" in l)
    r2 = correr_bloque("Notificar por escalón (o cerrar si se recuperó)",
                       {"STALE_COUNT": out.get("stale_count", "0"), "MISSING_COUNT": out.get("missing_count", "0"),
                        "MAX_AGE_H": out.get("max_age_h", "0")}, True, None, cwd=TMP / "repo_falso")
    print(f"- {etiqueta}: detect exit={r1['exit']} stale_count={out.get('stale_count')} max_age_h={out.get('max_age_h')} | "
          f"notificar exit={r2['exit']} gh: {resumen_gh(r2['gh'])}\n    salida: {' / '.join(s[:100] for s in r2['salida'][:3])}")

print("\nSalidas intermedias en", TMP)
