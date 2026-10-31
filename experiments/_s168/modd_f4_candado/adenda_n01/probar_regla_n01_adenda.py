# -*- coding: utf-8 -*-
"""BORRADOR (S170): prueba de la regla candidata de la adenda a N-01 (regla_n01_adenda.py).
Parte A, sintética: la regla acepta una escena inválida en que el censo llegó al mismo motivo con la misma grilla, y
NO la acepta si el censo llegó a OTRO motivo, si la grilla es OTRA, si la máscara o el VRP difieren, si el motivo es
«volcán fuera del gránulo», o si falta el campo del censo. Cada caso se compara además con la regla sellada.
Parte B, real (opcional): aplica las dos reglas a una tanda ya corrida, con el motivo del port del censo.
Uso: python probar_regla_n01_adenda.py [<carpeta del censo> <carpeta de la tanda> <identidad.json>]
"""
import ast
import glob
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
sys.path.insert(0, str(AQUI))
sys.stdout.reconfigure(encoding="utf-8")
import regla_n01_adenda as R  # noqa: E402

BASE = {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True, "grilla_igual_float32": True,
        "motivo_censo": "escena_invalida"}
CASOS = [  # (nombre, cambios a la identidad, motivo del runner, ¿la candidata la explica?)
    ("mismo motivo y misma grilla", {}, "escena_invalida", True),
    ("el censo llegó a OTRO motivo (ninguno)", {"motivo_censo": None}, "escena_invalida", False),
    ("el censo llegó a OTRO motivo (fuera del gránulo)", {"motivo_censo": "volcan_fuera_del_granulo"},
     "escena_invalida", False),
    ("OTRA grilla (no igual a float32)", {"grilla_igual_float32": False}, "escena_invalida", False),
    ("misma grilla declarada pero otra máscara", {"misma_mascara": False}, "escena_invalida", False),
    ("misma grilla declarada pero otro VRP", {"dvrp": 0.01}, "escena_invalida", False),
    ("sin el campo motivo_censo", {"motivo_censo": "__falta__"}, "escena_invalida", False),
    ("volcán fuera del gránulo con el censo de acuerdo", {"motivo_censo": "volcan_fuera_del_granulo"},
     "volcan_fuera_del_granulo", False),
]


def parte_a():
    malas = 0
    for nombre, cambios, motivo, espera in CASOS:
        x = dict(BASE, **cambios)
        if x.get("motivo_censo") == "__falta__":
            x.pop("motivo_censo")
        clave = ("Volcan", "2026-03-01 01:00")
        filas = [{"vol": clave[0], "dt": clave[1], "grilla_censo": "g.npz", "_motivo": motivo}]
        vieja, nueva = R.selladas_sin_explicar({clave: x}, filas)
        explica = not nueva
        ok = explica == espera and vieja == [clave]
        malas += not ok
        print("%s  %-52s candidata %s (espera %s) | sellada: sin explicar %d" % (
            "OK   " if ok else "FALLA", nombre, "explica" if explica else "NO explica",
            "explica" if espera else "NO explica", len(vieja)))
    # otro gránulo: las dos reglas la explican (como hoy) y la candidata no cambia eso
    clave = ("Volcan", "2026-03-02 01:00")
    vieja, nueva = R.selladas_sin_explicar({clave: dict(BASE, mismo_granulo=False)},
                                           [{"vol": clave[0], "dt": clave[1], "grilla_censo": "g.npz",
                                             "_motivo": "volcan_fuera_del_granulo"}])
    ok = vieja == [] and nueva == []
    malas += not ok
    print("%s  %-52s sellada y candidata la explican como otro gránulo" % ("OK   " if ok else "FALLA",
                                                                         "otro gránulo declarado"))
    print("parte A: %d de %d" % (len(CASOS) + 1 - malas, len(CASOS) + 1))
    return malas


def parte_b(censo, tanda, ruta_ident):
    pob = {(p["vol"], p["dt"]): p for p in
           json.load(open(RAIZ / "experiments/_s166_modd_f4/poblacion_f4.json", encoding="utf-8"))["pasadas"]}
    mc = {}
    for a in glob.glob(censo + "/run_*/*/ab_parte*.jsonl"):
        for ln in open(a, encoding="utf-8"):
            r = json.loads(ln)
            if r.get("tipo") == "record":
                port = r.get("port")
                port = ast.literal_eval(port) if isinstance(port, str) else (port or {})
                mc[(r["vol"], r["dt"])] = (port.get("fisica") or {}).get("motivo_vacio")
    ident = {(x["vol"], x["dt"]): dict(x, motivo_censo=mc.get((x["vol"], x["dt"])))
             for x in json.load(open(ruta_ident, encoding="utf-8"))["pasadas"]}
    rec = [json.loads(ln) for a in glob.glob(tanda + "/*-parte-*/f4_parte*.jsonl") for ln in open(a, encoding="utf-8")]
    filas = [dict(pob[(r["vol"], r["dt"])], vol=r["vol"], dt=r["dt"], _motivo=r["motivo"])
             for r in rec if r.get("tipo") == "record"]
    vieja, nueva = R.selladas_sin_explicar(ident, filas)
    print("parte B (%s): selladas sin explicar con la regla sellada %d; con la candidata %d %s" % (
        Path(tanda).name, len(vieja), len(nueva), nueva[:10]))


if __name__ == "__main__":
    m = parte_a()
    if len(sys.argv) == 4:
        parte_b(*sys.argv[1:])
    sys.exit(1 if m else 0)
