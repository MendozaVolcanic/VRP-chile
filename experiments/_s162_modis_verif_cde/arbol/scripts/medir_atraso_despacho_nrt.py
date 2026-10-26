# -*- coding: utf-8 -*-
"""Separa DÓNDE se atrasa el NRT: en la creación del evento o en el arranque del run.

POR QUÉ (S141). S139 midió que GitHub despacha los crones de este repo con horas de atraso y funde
las franjas (`docs/audit_s139/NRT_CADENCIA_Y_MEJORAS.md` §1). La pregunta que decide si sirve un
cron externo es otra: si el atraso está en CREAR el evento `schedule` o en que el run, ya creado,
espere un runner. Si está en crear el evento, un disparador externo que llame a `workflow_dispatch`
lo evita, porque ese evento se crea en el momento de la llamada.

QUÉ MIDE, por corrida de nrt.yml: `espera_arranque_s` = primer job iniciado menos creación del run
(común a los dos tipos de evento), y para `schedule` `atraso_creacion_min` = creación del run menos
la franja par anterior del cron "0 */2 * * *". Cuando GitHub funde franjas, este atraso es una cota
inferior del real.

INSTRUMENTO. P1: si el cuello fuera el runner, `espera_arranque_s` sería de minutos; P2: el
`workflow_dispatch` es el control, porque su creación es la llamada misma.

USO: python scripts/medir_atraso_despacho_nrt.py [--n 40] [--out ruta.json]
"""
import argparse
import datetime as dt
import io
import json
import statistics
import subprocess
import sys

REPO = "MendozaVolcanic/VRP-chile"


def gh(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(out.stdout)


def P(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def medir(n):
    runs = gh(f"repos/{REPO}/actions/workflows/nrt.yml/runs?per_page={n}")["workflow_runs"]
    filas = []
    for r in runs:
        if r["event"] not in ("schedule", "workflow_dispatch"):
            continue
        jobs = gh(f"repos/{REPO}/actions/runs/{r['id']}/jobs?per_page=20")["jobs"]
        inicios = [P(j["started_at"]) for j in jobs if j.get("started_at")]
        if not inicios:
            continue
        creado = P(r["created_at"])
        fila = {"run": r["id"], "evento": r["event"], "creado_utc": r["created_at"],
                "espera_arranque_s": round((min(inicios) - creado).total_seconds())}
        if r["event"] == "schedule":
            franja = creado.replace(minute=0, second=0, microsecond=0, hour=creado.hour - creado.hour % 2)
            fila["atraso_creacion_min"] = round((creado - franja).total_seconds() / 60)
        filas.append(fila)
    return filas


def resumen(filas):
    out = {}
    for ev in ("schedule", "workflow_dispatch"):
        sel = [f for f in filas if f["evento"] == ev]
        if not sel:
            continue
        out[ev] = {"n": len(sel), "mediana_espera_arranque_s": statistics.median(f["espera_arranque_s"] for f in sel),
                   "max_espera_arranque_s": max(f["espera_arranque_s"] for f in sel)}
        if ev == "schedule":
            at = [f["atraso_creacion_min"] for f in sel]
            dias = {f["creado_utc"][:10] for f in sel}
            out[ev].update({"mediana_atraso_creacion_min": statistics.median(at), "max_atraso_creacion_min": max(at),
                            "corridas_por_dia": round(len(sel) / max(len(dias), 1), 2), "franjas_declaradas_por_dia": 12})
    return out


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description="Atraso de creación contra espera de arranque del NRT")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    filas = medir(a.n)
    res = {"generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "resumen": resumen(filas), "corridas": filas}
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, ensure_ascii=False)
    print(json.dumps(res["resumen"], indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
