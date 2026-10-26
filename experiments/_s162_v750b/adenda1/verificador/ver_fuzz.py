# -*- coding: utf-8 -*-
"""Verificador de la adenda 1: diferencial aleatorio entre el analizador sellado, el compañero y un oráculo propio.

Poblaciones aleatorias con todos los estados que el probe puede dejar (ok, error_K, grilla_incompleta, fuera del gránulo,
sin_granulo, error genérico, sin resultado, diurna, sin cráter, sin cobertura, dayflag ausente), archivo de sin gránulo
válido / ausente / ajeno, y (modo B) cajas faltantes o vacías. Compara:
  A) sin cajas faltantes: SIN DATO, sin gránulo, protegidas SIN DATO y veredicto de cobertura del compañero == analizador.
  B) con cajas faltantes: el total y el veredicto del compañero == un oráculo escrito aparte de la regla del §4.
Uso: python ver_fuzz.py --evaluador <evaluar_d25.py> --dest <carpeta> [--n 30] [--semilla 1]
"""
import argparse
import hashlib
import importlib.util
import json
import random
import re
import subprocess
import sys
from pathlib import Path

ADE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("probar_adenda1", ADE / "probar_adenda1.py")
PA = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PA)

ESTADOS = ["ok"] * 10 + ["error_K", "grilla_incompleta", "volcan_fuera_del_granulo", "sin_granulo", "error: X: y",
                         "sin_resultado"]


def poblacion(rng, con_faltas):
    global p_malo
    p = PA.Pob()
    n = rng.choice([50, 100, 150, 200])
    p_malo = rng.choice([0.0, 0.004, 0.008, 0.012, 0.016, 0.02, 0.03])
    prot_en_malo = rng.random() < 0.3
    for k in range(n):
        lab = rng.choice(["pos", "neg_limpio", "neg_limpio", "neg_limpio"])
        vr = rng.choice([0.4, 1.0, 1.5, 3.0]) if lab == "pos" else None
        est = rng.choice(ESTADOS) if rng.random() < p_malo else "ok"
        if not prot_en_malo and est != "ok" and lab == "pos" and vr >= 1.0:
            vr = 0.4
        kw = dict(lab=lab, vrp_mirova=vr, dayflag=0 if rng.random() > p_malo else 1,
                  cob=PA.COB if rng.random() < 0.97 else PA.COB_SIN_CRATER,
                  volcan=rng.choice(["Lascar", "PuyehueCordonCaulle"]))
        hora = f"2026-0{rng.randint(4, 9)}-{rng.randint(10, 28)} {rng.randint(0, 9):02d}:{rng.randint(0, 5)}0"
        if est == "sin_resultado":
            i = p.pasada(hora, **kw)
            p.res[i] = None   # se quita después
            continue
        if est in ("sin_granulo", "error: X: y"):
            i = p.pasada(hora, estado="ok", **kw)
            p.res[i] = {"id": i, "volcan": kw["volcan"], "hora_utc": hora, "estado": est}
            continue
        if con_faltas and est == "ok" and rng.random() < p_malo * 2:
            fl = rng.sample(PA.CAJAS, rng.randint(1, 3))
            if rng.random() < 0.5:
                kw["sin_caja"] = tuple(fl)
            else:
                kw["caja_vacia"] = tuple(fl)
        p.pasada(hora, estado=est, **kw)
    p.res = [r for r in p.res if r is not None]
    # algunas con cobertura ausente o dayflag ausente
    for r in p.res:
        if r.get("estado") == "ok":
            u = rng.random()
            if u < p_malo / 2:
                r.pop("cobertura", None)
            elif u < p_malo:
                r.pop("dayflag", None)
    return p


def oraculo(p, sin_g, sg_ok):
    """Regla del §4 escrita aparte: cuenta de SIN DATO y veredicto de cobertura (sin usar partida() del analizador)."""
    res = {r["id"]: r for r in p.res}
    sin = falta = fuera = scr = 0
    prot = []
    for o in p.objs:
        r = res.get(o["id"])
        st = (r or {}).get("estado")
        if st == "volcan_fuera_del_granulo":
            fuera += 1
            continue
        malo = False
        if st != "ok":
            malo = True
        else:
            c = r.get("cobertura")
            if c is None:
                malo = True
            else:
                n7 = c.get("nan_7_crater", c.get("nan_7"))
                if n7 is None:
                    malo = True
                elif n7 > 0 or c.get("nan_crater", c.get("nan_centro")):
                    scr += 1
                    continue
                else:
                    if r.get("dayflag") != 0:
                        malo = True
                    else:
                        orc = r.get("oraculo") or {}
                        if any(not isinstance(orc.get(b), dict) for b in PA.CAJAS):
                            falta += 1
                            if o["protegida"]:
                                prot.append(o["id"])
                            continue
        if malo:
            sin += 1
            if o["protegida"]:
                prot.append(o["id"])
    prot += [x for x in sin_g if x["protegida"]]
    den = max(1, len(p.objs) + len(sin_g) - fuera - scr)
    total = sin + falta + len(sin_g)
    ok = sg_ok and total <= 0.02 * den and not prot
    return total, sin, falta, ("SUFICIENTE" if ok else "INSUFICIENTE")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--sin-analizador", action="store_true", help="sólo compañero contra oráculo propio (rápido)")
    ap.add_argument("--companero", default=str(ADE / "cobertura_cajas_v750b.py"))
    a = ap.parse_args()
    rng = random.Random(a.semilla)
    malas, corridas = [], 0
    dist = {}
    for k in range(a.n):
        modo = "A" if k % 2 == 0 else "B"
        p = poblacion(rng, con_faltas=(modo == "B"))
        sg_modo = rng.choice(["valido"] * 8 + ["ajeno", "ausente"])
        sin_g = []
        if rng.random() < 0.25:
            sin_g = [{"volcan": "Lascar", "hora_utc": f"2027-01-{j + 1:02d} 05:00", "protegida": rng.random() < 0.15}
                     for j in range(rng.randint(1, 3))]
        d = a.dest / f"f{k:03d}"
        d.mkdir(parents=True, exist_ok=True)
        p.escribir(d, sin_granulo=sin_g, sha_ajeno=(sg_modo == "ajeno"))
        if sg_modo == "ausente":
            (d / "sin_granulo.json").unlink()
        sg_ok = sg_modo == "valido"
        sg_efectivo = sin_g if sg_ok else []
        rc, c, out = PA.companero(a.companero, d)
        if c is None:
            malas.append((k, modo, "compañero ilegible", out[-300:]))
            continue
        o_total, o_sin, o_falta, o_cob = oraculo(p, sg_efectivo, sg_ok)
        corridas += 1
        kk = (modo, o_cob, "falta>0" if o_falta else "falta=0", "sin_g" if sg_efectivo else "-", "prot" if any(o["protegida"] for o in p.objs) else "-")
        dist[kk] = dist.get(kk, 0) + 1
        if (c["total"], c["sellado"], c["falta"], c["cob"]) != (o_total, o_sin, o_falta, o_cob):
            malas.append((k, modo, "compañero != oráculo", c, (o_total, o_sin, o_falta, o_cob)))
        if rc != (0 if o_cob == "SUFICIENTE" else 3):
            malas.append((k, modo, "código de salida", rc, o_cob))
        if modo == "A" and not a.sin_analizador:
            an, outa = PA.analizador(d, a.evaluador)
            if an is None:
                malas.append((k, modo, "analizador ilegible", outa[-300:]))
                continue
            obs, no_obs, sd, sg, cob = an
            pa = re.search(r"protegidas SIN DATO \(falla de cobertura, no de brazo\): (.*)", outa).group(1).strip()
            pc = re.search(r"protegidas SIN DATO: (.*)", out).group(1).strip()
            if not (sd == c["sellado"] and sg == c["sin_g"] and cob == c["cob"] and pa == pc and c["falta"] == 0):
                malas.append((k, modo, "compañero != analizador", an, c, pa, pc))
            # el hueco: observadas + no obs + SIN DATO + sin gránulo debe ser len(objetivos) cuando no falta caja
            if obs + no_obs + sd != len(p.objs):
                malas.append((k, modo, "el analizador pierde pasadas sin faltas de caja", obs, no_obs, sd, len(p.objs)))
    print(f"poblaciones {a.n}, comparadas {corridas}, discrepancias {len(malas)}")
    for kk, v in sorted(dist.items()):
        print("  clase", kk, v)
    for m in malas:
        print("DISCREPANCIA", m)
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
