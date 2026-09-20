# -*- coding: utf-8 -*-
"""S145 - D13: reconstruir el denominador del "31 %" de S124.

POR QUE. D13 cita el par 10.773 / 34.763 (31,0 %) y atribuye la medicion a
`experiments/_s124_observabilidad/`. Ese directorio existe pero sus dos scripts miden la
CEGUERA de t_bg, no la cerca, y su unico JSON (01_resumen.json) no contiene ninguno de los
tres numeros. O sea que el par no tiene script ni salida que lo respalde en el repo: para
saber si el 31 % de hoy es el mismo numero hay que reconstruir primero QUE contaba.

Antes de tratar la diferencia entre un numero de hoy y uno de un informe viejo como un
hallazgo, hay que reconstruir el corpus que ese informe pudo ver (A90). Eso es esto: barre
denominadores candidatos sobre los 11 Tier A y busca cual reproduce el par de S124.

Persiste en de_donde_salio_el_31.json. Ningun numero se escribe a mano (regla S91).
USO: python experiments/_s145_d13/de_donde_salio_el_31.py
"""
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / "data" / "mirova_equivalent"
SALIDA = HERE / "de_donde_salio_el_31.json"

VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
# Lo que D13 afirma, para compararlo contra lo reconstruido.
S124 = {"numerador": 10773, "denominador": 34763, "pct": 31.0, "mw": 17678}
# S124 cerro el 2026-08-26 (docs/AUDIT_S125_PROFUNDA.md es de la sesion siguiente). Se barren
# cortes alrededor de esa fecha porque un corpus que crece mueve el denominador solo.
CORTES = ["2026-08-20", "2026-08-22", "2026-08-24", "2026-08-25", "2026-08-26", "2026-08-28",
          "2026-08-31", "2026-09-19"]


def mw_apagados(filas_crudas, corte):
    """Suma de pc.vrp_mw de los records apagados hasta `corte`.

    D13 pone "17.678 MW" en la misma celda que el 31 %, sin denominador. Un MW absoluto
    sobre un corpus que crece no es comparable consigo mismo entre sesiones (A90); esto
    comprueba si ese numero era esa suma, para poder decir QUE media.
    """
    tot, n = 0.0, 0
    for fecha, apagado, pc_vrp in filas_crudas:
        if fecha <= corte and apagado and pc_vrp > 0:
            tot += pc_vrp
            n += 1
    return {"n": n, "suma_pc_vrp_mw": round(tot, 1)}


def candidatos(r):
    """Los denominadores plausibles que alguien pudo usar para "los records de los 11 Tier A"."""
    pc = r.get("primary_cluster") or {}
    return {
        "todos_los_records": True,
        "con_primary_cluster": bool(r.get("primary_cluster")),
        "con_vrp_mw_positivo": (r.get("vrp_mw") or 0) > 0,
        "con_cumulo_con_magnitud": bool(r.get("primary_cluster")) and (pc.get("vrp_mw") or 0) > 0,
    }


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    filas, crudas = [], []
    for vol in VOLS:
        with open(DATA / f"{vol}.json", encoding="utf-8") as fh:
            for r in json.load(fh)["records"]:
                dc = r.get("distance_class")
                apagado = bool(dc) and dc != "summit"
                fecha = (r.get("datetime_utc") or "")[:10]
                filas.append((fecha, apagado, candidatos(r)))
                crudas.append((fecha, apagado, (r.get("primary_cluster") or {}).get("vrp_mw") or 0))

    out = {"afirmacion_de_d13": S124,
           "procedencia": "D13 atribuye la medicion a experiments/_s124_observabilidad/, cuyos "
                          "scripts miden la ceguera de t_bg y cuyo JSON no contiene estos numeros",
           "barrido": []}
    mejor = None
    for corte in CORTES:
        sub = [f for f in filas if f[0] <= corte]
        fila = {"corte": corte}
        for nombre in ("todos_los_records", "con_primary_cluster", "con_vrp_mw_positivo",
                       "con_cumulo_con_magnitud"):
            den = [f for f in sub if f[2][nombre]]
            num = sum(1 for f in den if f[1])
            fila[nombre] = {"denominador": len(den), "numerador": num,
                            "pct": round(100.0 * num / len(den), 2) if den else None}
            d = abs(len(den) - S124["denominador"]) + abs(num - S124["numerador"])
            if mejor is None or d < mejor[0]:
                mejor = (d, corte, nombre, fila[nombre])
        out["barrido"].append(fila)

    out["mejor_ajuste"] = {"distancia_l1_al_par_de_s124": mejor[0], "corte": mejor[1],
                           "denominador_usado": mejor[2], "valores": mejor[3]}
    out["mw_apagados_por_corte"] = {c: mw_apagados(crudas, c) for c in CORTES}
    SALIDA.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"escrito {SALIDA}")
    print("afirmacion de D13: %(numerador)d / %(denominador)d = %(pct)s %%" % S124)
    print("%-12s %28s %28s %28s %28s" % ("corte", "todos", "con_primary_cluster",
                                         "con_vrp_mw>0", "con_cumulo_con_magnitud"))
    for f in out["barrido"]:
        print("%-12s %28s %28s %28s %28s" % (
            f["corte"],
            *["%d/%d = %s %%" % (f[k]["numerador"], f[k]["denominador"], f[k]["pct"])
              for k in ("todos_los_records", "con_primary_cluster", "con_vrp_mw_positivo",
                        "con_cumulo_con_magnitud")]))
    print("\nmejor ajuste:", json.dumps(out["mejor_ajuste"], ensure_ascii=False))
    print("MW apagados (suma de pc.vrp_mw), contra los 17.678 MW de D13:",
          json.dumps(out["mw_apagados_por_corte"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
