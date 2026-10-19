#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificador F3 (S155): simula el auto-audit semanal de HOY y lo separa por regimen (C0 / K).

Pregunta 1 (si lo medido estuviera roto, lo veria?): corre el MISMO scripts/auto_audit_weekly.main()
del cron, sin portar nada, con la referencia bajada hoy del remoto. Si el script estuviera roto, la
salida mixta no reproduciria la estructura de latest.json (control: corrida con la referencia vieja
del repo debe dar numeros del mismo orden que latest.json del 2026-10-14).
Pregunta 2 (instrumento muerto?): cada corrida imprime n por bucket; un n = 0 se informa como SIN DATO.
Control positivo de la separacion por regimen: la corrida K-sola debe tener 0 records antes del
2026-09-18 y la C0-sola 0 records con regimen; se imprime.

Regimen de un record: K si trae `regimen.codigo_sha` (todos los sha observados descienden de 34cea39e,
comprobado con git merge-base en esta sesion); C0 si no trae `regimen`.

Nada de esto escribe en el repo: OUTDIR, ROOT y DATA se redirigen a este directorio.
"""
import csv
import glob
import io
import json
import os
import sys
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import auto_audit_weekly as aw  # noqa: E402
import banco_paridad as bp  # noqa: E402
import referencia_mirova_unificada as rmu  # noqa: E402

FRESCA = AQUI / "ref_fresca"
CONS_F = str(FRESCA / "registro_vrp_consolidado.csv")
OCR_F = str(FRESCA / "registro_vrp_ocr.csv")
HIST_COMB = AQUI / "historico_combinado.csv"
K_SHA = "34cea39e4b64f0862e4bad949016a57ea181f8c4"


def armar_historico():
    """union_historica commiteada (al 14-oct) + snapshot del repo (14-oct): aproxima la union que el cron regenera."""
    filas, campos = [], []
    for p in [REPO / "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv",
              REPO / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv"]:
        with open(p, encoding="utf-8", errors="replace") as fh:
            r = csv.DictReader(fh)
            for c in r.fieldnames:
                if c not in campos:
                    campos.append(c)
            filas.extend(r)
    with open(HIST_COMB, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    return len(filas)


def es_k(rec, cache={}):
    sha = (rec.get("regimen") or {}).get("codigo_sha")
    if not sha:
        return False
    if sha not in cache:
        cache[sha] = subprocess.run(["git", "merge-base", "--is-ancestor", K_SHA, sha], cwd=REPO).returncode == 0
    return cache[sha]


def armar_raiz(nombre, quedarse):
    raiz = AQUI / ("raiz_" + nombre)
    dd = raiz / "data" / "mirova_equivalent"
    dd.mkdir(parents=True, exist_ok=True)
    stats = {"n": 0, "antes_0918": 0, "con_regimen": 0}
    for vol in aw.VOLS:
        d = json.load(open(REPO / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))
        recs = [r for r in d["records"] if (r.get("datetime_utc") or "") >= "2026-08-01" and quedarse(r)]
        for r in recs:
            stats["n"] += 1
            stats["antes_0918"] += r["datetime_utc"][:10] < "2026-09-18"
            stats["con_regimen"] += bool(r.get("regimen"))
        d2 = dict(d)
        d2["records"] = recs
        json.dump(d2, open(dd / f"{vol}.json", "w", encoding="utf-8"))
    return raiz, stats


def correr(nombre, raiz=None, cons=CONS_F, ocr=OCR_F, hist=str(HIST_COMB)):
    out = AQUI / ("out_" + nombre)
    out.mkdir(exist_ok=True)
    for f in out.glob("*"):
        f.unlink()
    aw.OUTDIR = str(out)
    aw.CONS, aw.OCR = cons, ocr
    aw.alertas_mirova.__defaults__ = (cons, ocr, hist)
    rmu.cargar_referencia_unificada.__defaults__ = (Path(cons), Path(ocr), rmu.RESPALDO_20260408, Path(hist) if hist else None)
    aw.ROOT = str(raiz) if raiz else str(REPO)
    bp.DATA = (Path(raiz) if raiz else REPO) / "data" / "mirova_equivalent"
    print(f"\n===== CORRIDA {nombre} (ROOT={aw.ROOT}, cons={Path(cons).parent.name}) =====", flush=True)
    buf = io.StringIO()
    vieja = sys.stdout
    sys.stdout = buf
    try:
        aw.main()
    finally:
        sys.stdout = vieja
    print(buf.getvalue())
    return json.load(open(out / "latest.json", encoding="utf-8"))


def main():
    print("historico combinado filas:", armar_historico())
    res = {}
    res["mixta_ref_fresca"] = correr("mixta_ref_fresca")
    res["mixta_ref_repo"] = correr("mixta_ref_repo",
                                   cons=str(REPO / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv"),
                                   ocr=str(REPO / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"),
                                   hist=str(REPO / "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv"))
    rc0, s0 = armar_raiz("C0", lambda r: not es_k(r))
    rk, sk = armar_raiz("K", es_k)
    print("raiz C0:", s0, " raiz K:", sk)
    res["C0"] = correr("C0", raiz=rc0)
    res["K"] = correr("K", raiz=rk)
    resumen = {}
    for k, d in res.items():
        resumen[k] = {"window": d["window"], "ventana_falsas": d["ventana_falsas"], "verdict": d["verdict"],
                      "flags": d["flags"], "recall": d["recall"],
                      "magnitud": d["magnitud_ratio_by_vol"],
                      "falsas_por_sensor": (d["falsas_publicaciones"].get("por_sensor")
                                            if "por_sensor" in d["falsas_publicaciones"] else d["falsas_publicaciones"]),
                      "cobertura_avisos": d["cobertura"]["avisos"]}
    json.dump({"stats_raices": {"C0": s0, "K": sk}, "corridas": resumen},
              open(AQUI / "simular_cron_resumen.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(resumen, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
