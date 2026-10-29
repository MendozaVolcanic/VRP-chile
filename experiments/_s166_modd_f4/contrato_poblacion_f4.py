# -*- coding: utf-8 -*-
"""S168: ¿poblacion_f4.json calza con el contrato que lee evaluar_f4.py (sellado, sin modificarlo)?

POR QUÉ. El evaluador mezcla la población en las filas del runner por (vol, dt) dentro de main() y saca de ella tres
cosas que deciden controles: las pasadas esperadas (cobertura), el conjunto de la identidad (`grilla_censo`, que tiene
que sumar 5.321) y `sin_pasada_nuestra`. Este script arma filas mínimas de runner (una por pasada, como si la vía
hubiera corrido en todas), las mezcla con la población EXACTAMENTE como evaluar_f4.main y corre los controles del
evaluador que leen la población, con un predicado sintético que nunca publica (el contrato no depende del tablero).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Si la población estuviera mal armada, ¿se vería? Sí: cobertura con faltantes o
sobrantes, identidad con otro total que 5.321, o `tramo` distinto de C/E darían distinto de lo esperado. (2) Si el
chequeo no pudiera fallar, ¿se vería? Sí: se repite quitando una pasada del runner (cobertura tiene que dar 1 faltante)
y quitando `sin_pasada_nuestra` (cobertura tiene que quedar en rojo por no medida).
Uso: python contrato_poblacion_f4.py  (escribe contrato_poblacion_f4_salida.txt)
"""
from __future__ import annotations

import collections
import importlib.util
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("evaluar_f4_sellado", AQUI / "evaluar_f4.py")
EV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(EV)
L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


def nunca(casos):
    return [(0, 0.0)] * len(casos)


def filas_runner(pob, quitar=()):
    por = {(p["vol"], p["dt"]): p for p in pob["pasadas"]}
    filas = [{"tipo": "record", "vol": v, "dt": d, "estado": "ok", "motivo": None, "v_marca": True}
             for (v, d) in por if (v, d) not in quitar]
    for f in filas:                       # como evaluar_f4.main
        f.update({k: v for k, v in por.get((f["vol"], f["dt"]), {}).items() if k not in f})
    for f in filas:
        f["_evaluable"], f["_motivo"] = EV.evaluable(f)
    return filas, list(por)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pob = json.load(open(AQUI / "poblacion_f4.json", encoding="utf-8"))
    pr("poblacion_f4.json: checkout", pob["checkout"], "| generado", pob["generado_utc"], "| head_e",
       pob["head_e"]["estado"], "| días de E excluidos", pob["dias_e_excluidos"])
    claves = [(p["vol"], p["dt"]) for p in pob["pasadas"]]
    pr("pasadas:", len(claves), "| únicas:", len(set(claves)), "| por tramo:",
       dict(collections.Counter(p["tramo"] for p in pob["pasadas"])))
    pr("etiquetas lab:", dict(sorted(collections.Counter(p["lab"] for p in pob["pasadas"]).items())),
       "| fuera de ETIQUETAS del evaluador:", sorted({p["lab"] for p in pob["pasadas"]} - set(EV.ETIQUETAS)))
    pr("sin_pasada_nuestra presente:", "sin_pasada_nuestra" in pob, "| n:", len(pob.get("sin_pasada_nuestra") or []))
    frontera = [(p["vol"], p["dt"], p["tramo"]) for p in pob["pasadas"] if (p["tramo"] == "E") != EV._es_e(p["dt"])]
    pr("tramo C/E contra la frontera del evaluador (INICIO_E", EV.INICIO_E + "): pasadas que no calzan", len(frontera))
    faltan_campos = collections.Counter(k for p in pob["pasadas"] for k in ("vol", "dt", "noche", "tramo", "lab",
                                                                            "vrp_mirova", "grilla_censo", "l1b",
                                                                            "geo", "url_l1b", "url_geo")
                                        if k not in p or (k in ("l1b", "geo", "url_l1b", "url_geo") and not p[k]))
    pr("campos ausentes o vacíos:", dict(faltan_campos))
    prot_sin_vrp = [(p["vol"], p["dt"]) for p in pob["pasadas"] if p["lab"] in ("protegida", "bajo1")
                    and not (p.get("vrp_mirova") or 0) > 0]
    pr("alertas (protegida o bajo1) sin vrp_mirova > 0:", prot_sin_vrp)

    filas, esperadas = filas_runner(pob)
    cid = EV.control_identidad({}, filas)
    pr("control_identidad del evaluador (sin archivo de identidad): estado", cid["estado"], "| grillas en población",
       cid["n_grillas_en_poblacion"], "de", cid["n_grillas_esperadas"], "| con grilla evaluables", cid["n_con_grilla"],
       "| faltan", cid["n_faltan"])
    cob = EV.control_cobertura(filas, esperadas, pob.get("sin_pasada_nuestra"), nunca)
    pr("control_cobertura del evaluador: estado", cob["estado"], "| faltan", cob["n_faltan"], "| sobran",
       len(cob["sobran"]), "| repetidas", len(cob["repetidas"]), "| fallas", cob["n_fallas"], "| sin pasada nuestra",
       len(cob["sin_pasada_nuestra"]), "| evaluables", cob["n_evaluables"])
    ok = cid["n_grillas_en_poblacion"] == EV.N_GRILLAS_CENSO and cid["n_faltan"] == cid["n_con_grilla"] and \
        cob["estado"] == "OK" and not frontera and not prot_sin_vrp and len(claves) == len(set(claves))

    # control del chequeo: tiene que poder fallar
    f1, e1 = filas_runner(pob, quitar={claves[0]})
    c1 = EV.control_cobertura(f1, e1, pob.get("sin_pasada_nuestra"), nunca)
    c2 = EV.control_cobertura(filas, esperadas, None, nunca)
    pr("control del chequeo: sin una pasada del runner ->", c1["estado"], "faltan", c1["n_faltan"],
       "| sin sin_pasada_nuestra ->", c2["estado"], "no medida", c2["sin_pasada_nuestra_no_medida"])
    ok_ctl = c1["estado"] == "INDECIDIBLE" and c1["n_faltan"] == 1 and c2["estado"] == "INDECIDIBLE"
    pr("CONTRATO:", "CALZA" if ok and ok_ctl else "NO CALZA")
    (AQUI / "contrato_poblacion_f4_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    sys.exit(0 if ok and ok_ctl else 1)


if __name__ == "__main__":
    main()
