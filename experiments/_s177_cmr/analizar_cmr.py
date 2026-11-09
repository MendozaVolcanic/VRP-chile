"""S177: lee el censo de censo_cmr.py y contesta si la carga propia aporta a los cortes de CMR.

POR QUE ASI: una coincidencia de horas no prueba causa. Si el reproceso provoca los cortes, deberian (1) no aparecer
cuando el reproceso no corre, a la misma hora del dia, y (2) aparecer siempre que corre, con la misma carga. Por eso
se cruza cada hora con los trabajos activos y se compara contra el control natural: los dias previos sin reproceso.

Salida: tabla por hora en <out>/horas.csv y resumen en <out>/resumen.json (y por pantalla).
Uso: python experiments/_s177_cmr/analizar_cmr.py --out C:/Users/nmend/vrp-temporales/s177_cmr
"""
import argparse
import collections
import csv
import datetime as dt
import io
import json
import pathlib
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

FALLAS = {"SEARCH_CMR_TIMEOUT", "SEARCH_VENTANA_ERR"}
# Consulta real a CMR: una por SEARCH_VENTANA (ventana resuelta) y cada falla. SEARCH_START solo marca el inicio por
# plataforma y dia, que con ventana se sirve de memoria: se reporta aparte y no entra al denominador de consultas.
CONSULTAS = FALLAS | {"SEARCH_VENTANA"}


def t(s):
    return dt.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)


def hora(x):
    return x.replace(minute=0, second=0, microsecond=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    jobs = [json.loads(x) for x in open(out / "jobs.jsonl", encoding="utf-8")]
    evs = [json.loads(x) for x in open(out / "eventos.jsonl", encoding="utf-8")]

    # Trabajos reales de reproceso, sin el job de plan; un rerun lista de nuevo los reutilizados (misma hora de inicio).
    vistos = set()
    reproc = []
    for j in jobs:
        # Un trabajo en cola trae started_at sin haber corrido: contarlo infla reproc_medio (verificador S177).
        if j["wf"] != "reproc-retro-paquete.yml" or not j["started"] or j["name"].startswith("plan") or j["status"] == "queued":
            continue
        k = (j["name"], j["started"])
        if k in vistos:
            continue
        vistos.add(k)
        reproc.append(j)
    ahora = dt.datetime.now(dt.timezone.utc)

    h = collections.defaultdict(lambda: collections.Counter())
    tipos_err = collections.Counter()
    for e in evs:
        b = hora(t(e["ts"]))
        h[b]["ev:" + e["ev"]] += 1
        h[b]["wf:" + e["wf"] + ":" + e["ev"]] += 1
        if e["ev"] in FALLAS:
            w = e["txt"].split("err=")[-1][:60] if "err=" in e["txt"] else e["txt"][:60]
            tipos_err[w] += 1
    ini, fin = min(h), max(h)
    filas = []
    b = ini
    while b <= fin:
        sig = b + dt.timedelta(hours=1)
        minutos = 0.0
        for j in reproc:
            s, c = t(j["started"]), t(j["completed"]) if j["completed"] else ahora
            minutos += max(0.0, (min(c, sig) - max(s, b)).total_seconds() / 60)
        c = h[b]
        consultas = sum(c["ev:" + x] for x in CONSULTAS)
        fallas = sum(c["ev:" + x] for x in FALLAS)
        filas.append({"hora": b.strftime("%Y-%m-%d %H"), "reproc_medio": round(minutos / 60, 2), "consultas": consultas,
                      "fallas": fallas, "cmr_timeout": c["ev:SEARCH_CMR_TIMEOUT"], "ventana_err": c["ev:SEARCH_VENTANA_ERR"],
                      "skip": c["ev:SEARCH_SKIP"], "start": c["ev:SEARCH_START"],
                      "timeout_nrt": c["wf:nrt.yml:SEARCH_CMR_TIMEOUT"],
                      "timeout_sombra34": c["wf:sombra-34.yml:SEARCH_CMR_TIMEOUT"],
                      "timeout_sombra11": c["wf:sombra-codigo-mirova.yml:SEARCH_CMR_TIMEOUT"],
                      "timeout_guardia": c["wf:guardia-k-modis.yml:SEARCH_CMR_TIMEOUT"],
                      "timeout_reproc": c["wf:reproc-retro-paquete.yml:SEARCH_CMR_TIMEOUT"]})
        b = sig
    with open(out / "horas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)

    def grupo(pred):
        g = [x for x in filas if pred(x)]
        n, c, fa = len(g), sum(x["consultas"] for x in g), sum(x["fallas"] for x in g)
        t_nrt = sum(x["timeout_nrt"] for x in g)
        return {"horas": n, "consultas": c, "fallas": fa, "fallas_por_100": round(100 * fa / c, 2) if c else None,
                "horas_con_falla": sum(1 for x in g if x["fallas"]), "timeout_nrt": t_nrt}

    res = {
        "ventana": [filas[0]["hora"], filas[-1]["hora"]],
        "n_trabajos_reproc": len(reproc),
        "tipos_de_error": tipos_err.most_common(12),
        "con_reproceso_ge_3": grupo(lambda x: x["reproc_medio"] >= 3),
        "sin_reproceso": grupo(lambda x: x["reproc_medio"] == 0),
        "sin_reproceso_18a01utc": grupo(lambda x: x["reproc_medio"] == 0 and (int(x["hora"][-2:]) >= 18 or int(x["hora"][-2:]) <= 1)),
        "con_reproceso_18a01utc": grupo(lambda x: x["reproc_medio"] >= 3 and (int(x["hora"][-2:]) >= 18 or int(x["hora"][-2:]) <= 1)),
        "con_reproceso_02a17utc": grupo(lambda x: x["reproc_medio"] >= 3 and 2 <= int(x["hora"][-2:]) <= 17),
    }
    (out / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print("\nhoras con falla:")
    for x in filas:
        if x["fallas"]:
            print(x["hora"], "reproc", x["reproc_medio"], "consultas", x["consultas"], "fallas", x["fallas"],
                  "| nrt", x["timeout_nrt"], "s34", x["timeout_sombra34"], "s11", x["timeout_sombra11"],
                  "guardia", x["timeout_guardia"], "reproc", x["timeout_reproc"], "venterr", x["ventana_err"])


if __name__ == "__main__":
    main()
