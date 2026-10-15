# -*- coding: utf-8 -*-
"""Tarea 1.6 del loop. Duracion de los jobs de reproc-s146-ab-sin-test1.yml en runs pasados, para estimar
cuanto tarda el A/B de este pre-registro. Lee la API de GitHub con `gh` (solo lectura, sin credenciales
propias). Agrupa por volcan y por perfil a partir del nombre del job, que trae la matriz
"reproc (Volcan, perfil)".

  python duracion_runs.py RUN_ID [RUN_ID ...]
  python duracion_runs.py --estimar > duracion_runs_salida.txt
"""
import collections, io, json, statistics, subprocess, sys
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def jobs(run_id):
    r = subprocess.run(["gh", "api", "--paginate", "repos/MendozaVolcanic/VRP-chile/actions/runs/%s/jobs?per_page=100" % run_id,
                        "--jq", ".jobs[] | [.name, .conclusion, .started_at, .completed_at] | @json"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip()]


def t(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


# Runs de referencia para la estimacion (ventana en dias; las ventanas salen de cobertura.txt de cada rama
# s146-ab/<run> y de despachar_cola.sh de S149: mayo 31, junio 30, julio 31, agosto 1 a 27; NdC 24).
MESES = {"35599902448": 31, "35675490175": 30, "35728617326": 31, "35759688167": 27}  # brazos B y F, 11 volcanes
NDC = ("38560317428", 24)                                                               # 10 brazos, un volcan
CON_TEST1 = ("_s146_ab_control", "_s150_sin_tope_d9", "_s150_etiqueta_cumulo")
PARALELO = 6  # max-parallel del workflow


def estimar():
    """Minutos por dia de ventana y por job, separando los brazos con el Test 1 (mas lentos) de los sin el."""
    sin, con, cola = [], [], []
    for run_id, dias in MESES.items():
        ds = [((t(f) - t(i)).total_seconds() / 60) for n, c, i, f in jobs(run_id) if n.startswith("reproc") and c == "success"]
        sin += [d / dias for d in ds]; m = statistics.median(ds); cola += [d / m for d in ds]
    for n, c, i, f in jobs(NDC[0]):
        if n.startswith("reproc") and c == "success":
            d = (t(f) - t(i)).total_seconds() / 60 / NDC[1]
            (con if any(p in n for p in CON_TEST1) else sin).append(d)
    r_sin, r_con, peor = statistics.median(sin), statistics.median(con), max(cola)
    print("min por dia y job: sin Test 1 mediana %.2f (n %d) | con Test 1 mediana %.2f (n %d) | job mas lento / mediana del run: %.2f"
          % (r_sin, len(sin), r_con, len(con), peor))
    plan = {"V1 (2026-08-29 a 10-08, C0 F K G)": (41, 2, 2), "V2a (2026-03-01 a 04-20, C0 K)": (51, 1, 1),
            "V2b (2026-04-21 a 06-12, C0 K)": (53, 1, 1)}
    total = 0
    for nombre, (dias, n_con, n_sin) in plan.items():
        jc, js = r_con * dias, r_sin * dias
        pared = 11 * (n_con * jc + n_sin * js) / PARALELO / 60; total += pared
        print("%-36s job con Test 1 ~%.0f min (peor ~%.0f), sin Test 1 ~%.0f min | %d jobs | pared ~%.1f h" % (
            nombre, jc, jc * peor, js, 11 * (n_con + n_sin), pared))
    print("total en serie (el grupo de concurrencia corre uno a la vez): ~%.1f h" % total)


def main():
    if sys.argv[1:] == ["--estimar"]:
        return estimar()
    for run_id in sys.argv[1:]:
        js = [j for j in jobs(run_id) if j[0].startswith("reproc")]
        if not js:
            print("run", run_id, "sin jobs reproc"); continue
        dur = {}
        for nombre, concl, ini, fin in js:
            if ini and fin:
                dur[nombre] = ((t(fin) - t(ini)).total_seconds() / 60, concl)
        ini_run = min(t(j[2]) for j in js if j[2]); fin_run = max(t(j[3]) for j in js if j[3])
        mins = [d for d, c in dur.values() if c == "success"]
        print("run %s: %d jobs reproc (%d success) | de %s a %s, %.1f h de pared" % (
            run_id, len(js), len(mins), ini_run, fin_run, (fin_run - ini_run).total_seconds() / 3600))
        if mins:
            print("   minutos por job exitoso: mediana %.0f, minimo %.0f, maximo %.0f, suma %.0f" % (
                statistics.median(mins), min(mins), max(mins), sum(mins)))
        por_vol = collections.defaultdict(list)
        for nombre, (d, c) in dur.items():
            vol = nombre.split("(")[-1].split(",")[0].strip()
            if c == "success":
                por_vol[vol].append(d)
        for v in sorted(por_vol):
            print("   %-20s %s" % (v, " ".join("%.0f" % x for x in sorted(por_vol[v]))))
        malos = sorted((n, c) for n, (d, c) in dur.items() if c != "success")
        if malos:
            print("   jobs no exitosos:", malos)


if __name__ == "__main__":
    main()
