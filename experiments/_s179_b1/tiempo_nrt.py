"""S179: ¿cuánto tarda el NRT por volcán con la vía «código MIROVA» en VIIRS, comparado con producción de hoy?

POR QUÉ: la regla de VIIRS (§5) pide medir el tiempo del NRT antes de encender B1: el paso de producción tiene un techo de
50 min por volcán (nrt.yml). La sombra (`sombra-codigo-mirova.yml`) corre las tres vías con la misma ventana que el NRT
(7 días hacia atrás más hoy, `scripts/ventana_sombra.py`), salvo al comienzo: su ventana parte el 2026-11-03, así que
las corridas de los primeros días procesan menos días y no son comparables. Una primera medición mía las mezcló
(mediana 4,0 min); el verificador lo detectó. Aquí se separa cada corrida con su ventana y su conclusión.

Mide, con la API de GitHub (sólo lectura): por corrida de la sombra, la duración del paso «Run VRP pipeline, perfil
sombra_codigo_mirova» de cada volcán, la conclusión del job y la ventana (días desde 2026-11-03 hasta la fecha de la
corrida, tope 8); y para el NRT de producción, la duración del paso del perfil mirova_equivalent en las corridas de los
mismos días, con su conclusión. Diferencia que no se controla: la sombra no baja MxD03 y producción sí.

Uso: python tiempo_nrt.py --desde 2026-11-03 --out <json>
Pregunta 1 del instrumento: se imprime n de jobs por corrida; un job sin tiempos queda fuera y se cuenta.
"""
import argparse
import io
import json
import statistics
import subprocess
import sys
from datetime import date, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = "MendozaVolcanic/VRP-chile"


def gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True, encoding="utf-8", timeout=120)
    if r.returncode:
        raise RuntimeError(r.stderr)
    return r.stdout


def runs(workflow, desde):
    out = json.loads(gh(["run", "list", "-R", REPO, "--workflow", workflow, "-L", "200", "--json",
                         "databaseId,createdAt,conclusion,event"]))
    return [r for r in out if r["createdAt"][:10] >= desde]


def pasos(run_id, patron):
    txt = gh(["api", f"repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100", "--paginate", "--jq",
              '.jobs[] | . as $j | .steps[] | select(.name|test("' + patron + '")) | '
              '[$j.name, $j.conclusion, .conclusion, .started_at, .completed_at] | @tsv'])
    res, sin = [], 0
    for ln in txt.splitlines():
        job, cj, cs, a, b = (ln.split("\t") + [""] * 5)[:5]
        if not a or not b or a == "null" or b == "null":
            sin += 1
            continue
        m = (datetime.fromisoformat(b.replace("Z", "+00:00")) - datetime.fromisoformat(a.replace("Z", "+00:00"))).total_seconds() / 60
        res.append({"job": job, "job_conclusion": cj, "step_conclusion": cs, "min": round(m, 2)})
    return res, sin


def resumen(v):
    v = sorted(x["min"] for x in v)
    return {"n": len(v), "mediana": round(statistics.median(v), 1) if v else None, "max": v[-1] if v else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2026-11-03")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    salida = {"sombra": [], "nrt_por_dia": {}}
    print("== sombra (las tres vías)")
    for r in sorted(runs("sombra-codigo-mirova.yml", a.desde), key=lambda r: r["createdAt"]):
        dia = date.fromisoformat(r["createdAt"][:10])
        ventana = min((dia - date(2026, 11, 3)).days + 1, 8)
        p, sin = pasos(r["databaseId"], "perfil sombra_codigo_mirova")
        s = resumen(p)
        lento = max(p, key=lambda x: x["min"]) if p else None
        print(f"   {r['createdAt']} run {r['databaseId']} {r['conclusion']:8s} ventana {ventana} días | jobs {s['n']} "
              f"(sin tiempos {sin}) | mediana {s['mediana']} min, máximo {s['max']} min"
              + (f" ({lento['job']}, paso {lento['step_conclusion']})" if lento else ""))
        salida["sombra"].append({"run": r["databaseId"], "creado": r["createdAt"], "conclusion": r["conclusion"],
                                 "ventana_dias": ventana, "pasos": p, "sin_tiempos": sin, **s})
    print("== NRT de producción (perfil mirova_equivalent), por día")
    todos = []
    for r in runs("nrt.yml", a.desde):
        p, _ = pasos(r["databaseId"], "mirova_equivalent")
        for x in p:
            x["dia"] = r["createdAt"][:10]
            x["run"] = r["databaseId"]
        todos += p
    for dia in sorted({x["dia"] for x in todos}):
        v = [x for x in todos if x["dia"] == dia]
        s = resumen(v)
        lento = max(v, key=lambda x: x["min"])
        print(f"   {dia}: jobs {s['n']} | mediana {s['mediana']} min, máximo {s['max']} min ({lento['job']}, "
              f"paso {lento['step_conclusion']})")
        salida["nrt_por_dia"][dia] = {**s, "lento": lento}
    s = resumen(todos)
    print(f"   total: jobs {s['n']} | mediana {s['mediana']} | máximo {s['max']}")
    salida["nrt_total"] = s
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
