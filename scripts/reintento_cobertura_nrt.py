# ════════════════════════════════════════════════════════════════════
# FICHA SDA · reintento_cobertura_nrt.py  ·  SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Que una corrida del NRT que quedo verde pero no pudo buscar o bajar alguna pasada (CMR de
#                 NASA caido, corte de red) se reintente sola, sin ponerse roja ni mandar correos.
# Lógica        : El NRT resume por volcan la cobertura que escribe run_pipeline.py (sólo conteos, fechas y
#                 etapas) y la sube como artefacto. nrt-retry.yml baja esos artefactos de la ultima corrida y
#                 este script decide: reintentar si la corrida es verde, tuvo fallas de busqueda o descarga, no
#                 es ella misma un reintento y no se llego al tope de reintentos en 24 h.
# Modelo/método : Reglas deterministicas (orquestacion). Sin aprendizaje automatico.
# Datos entrada : JSON de cobertura de run_pipeline.py; lista de corridas de nrt.yml (API de GitHub).
#                 SIN datos personales (el login del actor sólo se compara con el del bot).
# Variables     : n de fallas por volcan, conclusion y actor de la corrida, reintentos en 24 h.
# Limitaciones  : No mira el detector ni los records: sólo decide si relanzar el NRT. Sin dato (sin
#                 artefactos, sin actor, sin la lista de corridas) no reintenta. Las corridas rojas siguen por
#                 el camino NASA_DOWN de nrt-retry.yml, que este script no toca.
# Refs/datos    : Auditoria de Codex, ronda 2, F6-104 (D:\codex-vrp\_salida\ronda2\PENDIENTES_F6_PARA_NICOLAS.md).
#                 Entrenamiento: No aplica (sin ML). Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""S198 (F6-104, opción (b) aprobada por Nicolás el 2026-11-24): reintento de las corridas verdes del NRT con fallas de
búsqueda o descarga.

POR QUÉ. El NRT no corre en modo estricto (una falla de NASA no debe teñir de rojo cada corrida ni llenar el correo, A58
de julio), así que con CMR caído la corrida sale verde con un `::warning`. `nrt-retry.yml` sólo miraba corridas rojas y
nunca reintentaba ésas. Este script le da el dato estructurado para hacerlo, sin leer texto libre del log.

Dos subcomandos, sólo biblioteca estándar (nrt-retry corre sin instalar nada):

    resumir --entrada cobertura_nrt/X.json --volcan X --salida cobertura_resumen/X.json
    decidir --runs runs.json --id <run> --dir <artefactos> --salida $GITHUB_OUTPUT

Prueba: tests/test_reintento_cobertura_nrt_s198.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Quien despacha con el GITHUB_TOKEN (nrt-retry.yml). Una corrida con este actor ya es un reintento y no se reintenta
# por cobertura: así no hay cadena. El cron externo (cron-job.org) despacha con un token personal, no con éste.
ACTOR_REINTENTO = "github-actions[bot]"
# POR QUÉ 4: nrt-retry corre 12 veces al día. Una falla determinista (un gránulo roto en LAADS que falla igual en cada
# intento) haría reintentar en cada una durante los 8 días de la ventana, duplicando la carga sobre NASA. Con 4 en
# 24 h una caída pasajera de unas horas se reintenta entera y la determinista cuesta como mucho 4 corridas al día.
MAX_REINTENTOS_24H = 4


def resumir(cobertura: dict, volcan: str) -> dict:
    """Lo que necesita nrt-retry, sin los mensajes de error (texto libre que podría llevar una URL o un secreto).
    Sólo cuentan las fallas de búsqueda o descarga; las incidencias (día en curso parcial, búsqueda vacía) no."""
    fallas = list(cobertura.get("fallas") or [])
    etapas = Counter(str(f.get("etapa") or "?") for f in fallas)
    fechas = sorted({str(f["fecha"]) for f in fallas if f.get("fecha")})
    return {"volcan": volcan, "n_fallas": len(fallas), "etapas": dict(sorted(etapas.items())), "fechas": fechas}


def _fecha(iso: str | None) -> datetime | None:
    try:
        return datetime.strptime(str(iso)[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _actor(run: dict) -> str | None:
    return ((run.get("triggering_actor") or {}).get("login")) or None


def decidir_verde(run: dict | None, corridas: list | None, resumenes: list, ahora: datetime | None = None
                  ) -> tuple[bool, str]:
    """¿Se reintenta la corrida `run`? Sólo el camino verde; la roja la decide nrt-retry por NASA_DOWN."""
    ahora = ahora or datetime.now(timezone.utc)
    if not run:
        return False, "sin dato: no se encontró la corrida en la lista de la API"
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        return False, f"la corrida no es verde (status={run.get('status')}, conclusion={run.get('conclusion')})"
    actor = _actor(run)
    if not actor:
        return False, "sin dato: la corrida no trae actor; no se sabe si ya es un reintento"
    if actor == ACTOR_REINTENTO:
        return False, "la corrida ya es un reintento (la despachó nrt-retry); no se encadena"
    if not resumenes:
        return False, "sin dato: la corrida no dejó resúmenes de cobertura (anterior a S198 o artefacto perdido)"
    con_fallas = [r for r in resumenes if int(r.get("n_fallas") or 0) > 0]
    if not con_fallas:
        return False, f"cobertura sin búsquedas ni descargas fallidas en {len(resumenes)} volcanes"
    if corridas is None:
        return False, "sin dato: no se pudo leer la lista de corridas para el tope de 24 h"
    desde = ahora - timedelta(hours=24)
    previos = [c for c in corridas if _actor(c) == ACTOR_REINTENTO and (_fecha(c.get("created_at")) or ahora) > desde]
    if len(previos) >= MAX_REINTENTOS_24H:
        return False, f"tope cumplido: {len(previos)} reintentos en 24 h (máximo {MAX_REINTENTOS_24H})"
    detalle = ", ".join(f"{r.get('volcan')} ({r.get('n_fallas')}: {', '.join(r.get('fechas') or [])})"
                        for r in sorted(con_fallas, key=lambda r: str(r.get("volcan"))))
    return True, f"búsquedas o descargas fallidas en {len(con_fallas)} volcanes: {detalle}"


def _leer_json(ruta: Path):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _leer_resumenes(carpeta: Path) -> list:
    out = []
    if carpeta.is_dir():
        for p in sorted(carpeta.rglob("*.json")):
            d = _leer_json(p)
            if isinstance(d, dict) and "n_fallas" in d:
                out.append(d)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resumir")
    r.add_argument("--entrada", required=True)
    r.add_argument("--volcan", required=True)
    r.add_argument("--salida", required=True)
    d = sub.add_parser("decidir")
    d.add_argument("--runs", required=True, help="respuesta de GET .../actions/workflows/nrt.yml/runs")
    d.add_argument("--id", required=True)
    d.add_argument("--dir", required=True, help="carpeta con los artefactos cobertura-* bajados")
    d.add_argument("--salida", required=True, help="archivo $GITHUB_OUTPUT")
    d.add_argument("--ahora", default=None, help="AAAA-MM-DDTHH:MM:SSZ (pruebas)")
    a = ap.parse_args(argv)

    if a.cmd == "resumir":
        cob = _leer_json(Path(a.entrada))
        if not isinstance(cob, dict):
            print(f"Sin cobertura en {a.entrada}: no se sube resumen.")
            return 0
        res = resumir(cob, a.volcan)
        Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
        Path(a.salida).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        print(f"Resumen de cobertura de {a.volcan}: {res['n_fallas']} búsquedas o descargas fallidas.")
        return 0

    lista = _leer_json(Path(a.runs))
    corridas = lista.get("workflow_runs") if isinstance(lista, dict) else None
    run = next((c for c in (corridas or []) if str(c.get("id")) == str(a.id)), None)
    resumenes = _leer_resumenes(Path(a.dir))
    ok, motivo = decidir_verde(run, corridas, resumenes, ahora=_fecha(a.ahora))
    motivo = motivo.replace("\n", " ")
    print(f"Corrida {a.id}: {'reintentar' if ok else 'no reintentar'} ({motivo})")
    with open(a.salida, "a", encoding="utf-8") as fh:
        fh.write(f"should_retry={'true' if ok else 'false'}\n")
        fh.write(f"motivo=cobertura: {motivo}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
