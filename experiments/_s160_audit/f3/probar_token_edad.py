"""F3 (S160): ¿el vigilante del vencimiento del EARTHDATA_TOKEN (scripts/token_edad.py) ve lo que dice ver?

Sin red y sin token real: se fabrican JWT sintéticos (firma falsa, sólo importa el campo `exp`) y se
llama a estado_token del árbol de main. Nunca se imprime ni se lee un token real.

Pregunta 1: si el token estuviera por vencer, estado_token tiene que decir `renovar` (<= 10 días) o
`vencido`. Pregunta 2 (instrumento): un token sin `exp`, vacío o que no es JWT da `desconocido`, que
es el estado que el healthcheck manda SOLO al resumen del job, sin issue (nrt-healthcheck.yml, paso
«Issue de renovacion del token»: `if ESTADO == "desconocido": ... sys.exit(0)`). Control positivo:
exp dentro de 5 días -> renovar; exp ayer -> vencido; exp en 40 días -> ok.

Uso: python -I probar_token_edad.py <arbol> > salida.txt
"""
import base64
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ARBOL = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ARBOL / "scripts"))
import token_edad  # noqa: E402


def jwt(carga: dict) -> str:
    def b64(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return f"{b64({'alg': 'none'})}.{b64(carga)}.firma"


ahora = datetime(2026, 10, 22, 3, 0, tzinfo=timezone.utc)
casos = [
    ("exp en 40 dias (control ok)", jwt({"exp": int((ahora + timedelta(days=40)).timestamp())})),
    ("exp en 10.0 dias (borde)", jwt({"exp": int((ahora + timedelta(days=10)).timestamp())})),
    ("exp en 5 dias (control renovar)", jwt({"exp": int((ahora + timedelta(days=5)).timestamp())})),
    ("exp ayer (control vencido)", jwt({"exp": int((ahora - timedelta(days=1)).timestamp())})),
    ("secret ausente (cadena vacia)", ""),
    ("secret con espacios", "   "),
    ("JWT sin exp", jwt({"uid": "x"})),
    ("no es JWT (token opaco)", "abcdef0123456789"),
    ("exp como texto", jwt({"exp": "2026-12-07"})),
    ("token real de 60 dias emitido 2026-10-08 18:07 (proxy: updated_at del secret)",
     jwt({"exp": int(datetime(2026, 12, 7, 18, 3, tzinfo=timezone.utc).timestamp())})),
]
print(f"DIAS_AVISO={token_edad.DIAS_AVISO}  ahora={ahora.isoformat()}")
for nombre, t in casos:
    r = token_edad.estado_token(t, ahora)
    issue = "SIN ISSUE (solo resumen)" if r["estado"] == "desconocido" else (
        "issue" if r["estado"] in ("renovar", "vencido") else "sin issue (ok)")
    print(f"{nombre:75s} -> {r['estado']:12s} vence={r['vence_utc']} dias={r['dias_restantes']} | {issue}")
# Fecha en que el aviso se dispararia para el token vigente (proxy): vence - DIAS_AVISO
vence = datetime(2026, 12, 7, 18, 3, tzinfo=timezone.utc)
print(f"token vigente (proxy updated_at 2026-10-08 18:07, vida 60 d): vence {vence.isoformat()}; "
      f"el healthcheck abriria issue desde {(vence - timedelta(days=token_edad.DIAS_AVISO)).date()} "
      f"(corre a las 12:00 UTC, con 2.5 a 6 h de atraso medido en gh_healthcheck_runs.json)")
