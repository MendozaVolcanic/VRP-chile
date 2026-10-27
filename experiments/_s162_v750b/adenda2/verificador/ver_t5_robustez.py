# -*- coding: utf-8 -*-
"""T5: el lector frente a resultados incompletos de la suplementaria y a cajas raras. Sólo comprueba que no se cae y que
lo que no pudo medir lo dice (SIN DATO por nombre). Pregunta 1: si el lector se cayera con datos reales irregulares, esto
lo vería (traceback + código 2). Pregunta 2: el control es la corrida sana (tiene que dar 0 y controles en verde)."""
import copy
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ver_comun import Pob, TMP, lector  # noqa: E402

UNO = [(33, 34, 0.9)]
LEJANA = [(33, 34, 0.9), (33, 50, 5.0), (33, 51, 4.0)]


def base():
    p = Pob()
    for n in range(12):
        p.pasada(f"2026-04-{1 + n:02d} 05:00", "neg_limpio", [])
    for n in range(3):
        p.pasada(f"2026-05-{1 + n:02d} 05:00", "pos", UNO, 0.4, dist_mirova=0.8, pub_prod=True)
    for n in range(3):
        p.pasada(f"2026-07-{1 + n:02d} 05:00", "far_ref", LEJANA, 3.0, dist_mirova=13.1, crater=(33.0, 30.0))
    return p


def caso(nombre, mod):
    d = TMP / "t5" / nombre
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    p = base()
    mod(p)
    p.escribir(d)
    rc, out = lector(d)
    tb = "Traceback" in out
    l1 = [l for l in out.splitlines() if "SIN DATO" in l or "suplementarias SIN DATO" in l][:3]
    print(f"{nombre}: rc={rc} traceback={tb} | {' || '.join(x.strip()[:150] for x in l1)}")
    if tb:
        print("   ", out.strip().splitlines()[-1][:200])


def sin_resultado_supl(p):
    p.res = [r for r in p.res if r["id"] < 100000 or r["id"] == 100000]


def caja_none(p):
    for r in p.res:
        if r["id"] == 100001:
            r["oraculo"]["B0"] = None


def caja_vacia(p):
    for r in p.res:
        if r["id"] == 100001:
            r["oraculo"]["B1"] = {}


def fuera(p):
    for r in p.res:
        if r["id"] == 100002:
            r["estado"] = "volcan_fuera_del_granulo"
            r.pop("oraculo", None)


def error(p):
    for r in p.res:
        if r["id"] == 100002:
            r["estado"] = "error: X"


caso("sana", lambda p: None)
caso("supl_sin_resultado_2de3", sin_resultado_supl)
caso("caja_B0_None", caja_none)
caso("caja_B1_vacia", caja_vacia)
caso("fuera_del_granulo", fuera)
caso("error_en_supl", error)
