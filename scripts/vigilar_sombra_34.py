"""S172: aviso de vigilancia ciega de la sombra de los 34 (.github/workflows/sombra-34.yml).

POR QUÉ. Un vigilante ciego no da error, da VERDE (S156). Si la sombra de los 34 deja de correr (el cron no dispara,
alguien desactiva el workflow, el token vence, un volcán sale de la matriz) o corre sin escribir nada, nadie lo nota:
la revisión por job (scripts/revisar_sombra.py) sólo actúa cuando el job corre. Este script lo corre otro workflow
(.github/workflows/vigilancia-sombra-34.yml) con su propio cron y, si algún volcán no tiene datos frescos, el
workflow abre un issue.

QUÉ ES «FRESCO»: el JSON data/sombra_34/<Volcán>.json tiene al menos un record de la vía (`via_codigo_mirova` es True)
escrito por el perfil sombra_34 (`regimen.perfil`) con `processed_utc` dentro de las últimas --horas (48 por defecto:
una corrida diaria que llega con horas de atraso no dispara; dos días sin datos sí). La lista de volcanes sale de la
matriz del workflow de la sombra, no de una copia. Un volcán que sale de la matriz deja de vigilarse; por eso
tests/test_sombra_34_s172.py amarra la matriz a volcanoes.yaml menos nrt.yml.

CUÁNDO EMPIEZA: no antes de --horas después de max(2026-11-03, --alta). --alta es la fecha en que el workflow de la
sombra llegó a main (el workflow de vigilancia la pide a la API de GitHub); sin ella, se usa sólo el 2026-11-03.
Antes de eso imprime ESPERA y no hay issue.

Salida: imprime el veredicto (ESPERA, OK o CIEGA) y el detalle; con --salida, el mismo veredicto en JSON. Sale 0 en
ESPERA y OK, 1 en CIEGA. Un insumo ilegible no termina en traceback: cuenta como ciego para ese volcán.

Uso: python scripts/vigilar_sombra_34.py [--dir data/sombra_34] [--workflow .github/workflows/sombra-34.yml]
       [--ahora AAAA-MM-DDTHH:MM:SSZ] [--alta AAAA-MM-DDTHH:MM:SSZ] [--horas 48] [--salida veredicto.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

FECHA_MINIMA = datetime(2026, 11, 3, tzinfo=timezone.utc)   # la de scripts/ventana_sombra.py
PERFIL = "sombra_34"


def _utc(texto):
    if not texto:
        return None
    try:
        t = datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def volcanes_de_la_matriz(ruta_workflow):
    y = yaml.safe_load(Path(ruta_workflow).read_text(encoding="utf-8"))
    return list(y["jobs"]["process"]["strategy"]["matrix"]["volcano"])


def ultimo_dato(ruta_json):
    """(processed_utc más reciente de un record de la vía del perfil, motivo si no hay)."""
    p = Path(ruta_json)
    if not p.exists():
        return None, "sin archivo"
    try:
        datos = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, f"archivo ilegible ({type(e).__name__})"
    regs = datos.get("records") if isinstance(datos, dict) else None
    if not isinstance(regs, list):
        return None, "sin lista `records`"
    mejor = None
    for r in regs:
        if not isinstance(r, dict) or r.get("via_codigo_mirova") is not True:
            continue
        reg = r.get("regimen")
        if not isinstance(reg, dict) or reg.get("perfil") != PERFIL:
            continue
        t = _utc(r.get("processed_utc"))
        if t is not None and (mejor is None or t > mejor):
            mejor = t
    return mejor, (None if mejor else "ningún record de la vía del perfil sombra_34")


def vigilar(dir_datos, volcanes, ahora, horas=48, alta=None):
    inicio = max(FECHA_MINIMA, alta or FECHA_MINIMA) + timedelta(hours=horas)
    out = {"ahora": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"), "horas": horas,
           "vigila_desde": inicio.strftime("%Y-%m-%dT%H:%M:%SZ"), "n_volcanes": len(volcanes), "ciegos": []}
    if not volcanes:
        out["veredicto"] = "CIEGA"
        out["ciegos"].append({"volcano": None, "motivo": "la matriz del workflow de la sombra no trae volcanes"})
        return out
    if ahora < inicio:
        out["veredicto"] = "ESPERA"
        return out
    corte = ahora - timedelta(hours=horas)
    for v in volcanes:
        t, motivo = ultimo_dato(Path(dir_datos) / f"{v}.json")
        if t is None:
            out["ciegos"].append({"volcano": v, "motivo": motivo, "ultimo": None})
        elif t < corte:
            out["ciegos"].append({"volcano": v, "motivo": f"último record de la vía hace más de {horas} h",
                                  "ultimo": t.strftime("%Y-%m-%dT%H:%M:%SZ")})
    out["veredicto"] = "CIEGA" if out["ciegos"] else "OK"
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/sombra_34")
    ap.add_argument("--workflow", default=".github/workflows/sombra-34.yml")
    # VIGILAR_SOMBRA_34_AHORA: sólo para que la prueba ejecute el paso real del workflow con un reloj fijo (VS34-02)
    ap.add_argument("--ahora", default=os.environ.get("VIGILAR_SOMBRA_34_AHORA") or None)
    ap.add_argument("--alta", default=None)
    ap.add_argument("--horas", type=float, default=48)
    ap.add_argument("--salida", default=None)
    a = ap.parse_args(argv)
    ahora = _utc(a.ahora) if a.ahora else datetime.now(timezone.utc)
    if ahora is None:
        print("ERROR: --ahora ilegible", file=sys.stderr)
        return 2
    try:
        volcanes = volcanes_de_la_matriz(a.workflow)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as e:
        print(f"CIEGA: no se pudo leer la matriz de {a.workflow} ({type(e).__name__})")
        volcanes = []
    d = vigilar(a.dir, volcanes, ahora, a.horas, _utc(a.alta))
    print(f"{d['veredicto']}: {len(volcanes)} volcanes, vigila desde {d['vigila_desde']}, ventana {a.horas:g} h")
    for c in d["ciegos"]:
        print(f"  - {c['volcano']}: {c['motivo']}" + (f" (último {c['ultimo']})" if c.get("ultimo") else ""))
    if a.salida:
        Path(a.salida).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if d["veredicto"] == "CIEGA" else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # el detalle lleva tildes; en Windows la consola no es UTF-8
    sys.exit(main())
