# -*- coding: utf-8 -*-
"""S159 frente N, paso 5: detalle de lo que el veredicto pre-registrado no muestra (post hoc, informativo).

(a) Los negativos limpios que F enciende y las alertas que F no recupera, pasada por pasada, con el oráculo al lado.
(b) El oráculo contado como si fuera un brazo, con la misma regla de MISSION y los mismos pesos. NO estaba
    pre-registrado como brazo (el pre-registro lo declara referencia); se informa marcado como post hoc.
(c) Las protegidas que el oráculo con la caja por defecto no detecta.
(d) La magnitud del oráculo con un píxel: qué fracción cae a menos de 5 % de MIROVA (pregunta de O1/O2).

Pregunta 1 del instrumento: si el oráculo detectara al azar, su razón con MIROVA no se concentraría en 1; se imprime
la dispersión. Pregunta 2: las pasadas sin oráculo (grilla incompleta, estado distinto de ok) se cuentan aparte.
Uso: python 05_detalle.py --art <carpeta(s) del run>
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402


def alerta(o, inner):
    if not o or not o.get("npix") or (o.get("vrp_mw") or 0) <= 0:
        return False
    return max(o["pixeles"], key=lambda p: p[4])[3] <= inner


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--tabla", default=str(AQUI / "tabla_por_pasada.csv"))
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.loads((AQUI / "objetivos_n.json").read_text(encoding="utf-8"))}
    res = {}
    for d in a.art:
        for f in sorted(Path(d).rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:
                    res[r["id"]] = r
    T = {int(r["id"]): r for r in csv.DictReader(open(a.tabla, encoding="utf-8"))}
    inner = B.inner_desde_html()
    L = []
    pr = lambda *x: (print(*x), L.append(" ".join(str(y) for y in x)))
    b = lambda v: v == "True"
    ok = [i for i in T if T[i]["K_pub"] in ("True", "False") and obj[i]["peso"] > 0]

    pr("== (a) negativos limpios que F publica y K no (muestra, con peso)")
    for i in ok:
        if obj[i]["lab"] == "neg_limpio" and b(T[i]["F_pub"]) and not b(T[i]["K_pub"]):
            br = res[i]["brazos"]
            pc = br["F"]["record"]["primary_cluster"]
            pr(f"   {i} {obj[i]['volcan']} {obj[i]['hora_utc']} z {obj[i]['z']} peso {obj[i]['peso']:.1f} | K pc "
               f"{T[i]['K_pc']} | F pc {pc['vrp_mw']} n {pc['n_pixels']} a {pc['centroid_dist_km']} km banda "
               f"{T[i]['F_banda']} | primer pase {T[i]['F_n_primer_pase']} | O {T[i]['O_geo_linear_npix']} px | "
               f"MIROVA {[(m['tipo'], m['vrp_mw']) for m in obj[i]['mirova']]}")
    pr("== (a) alertas que deciden y F no publica")
    for i in ok:
        if obj[i]["lab"] == "pos" and obj[i]["decide"] and not b(T[i]["F_pub"]):
            pr(f"   {i} {obj[i]['volcan']} {obj[i]['hora_utc']} MIROVA {obj[i]['mirova_vrp']} prot "
               f"{obj[i]['protegida']} | K pc {T[i]['K_pc']} dc {T[i]['K_dc']} | F pc {T[i]['F_pc']} | O "
               f"{T[i]['O_geo_linear_npix']} px {T[i]['O_geo_linear_vrp']} | O anillo "
               f"{T[i]['O_geo_linear_anillo_sensible_npix']} px")

    pr("== (b) el oraculo contado como brazo (POST HOC, no pre-registrado como brazo), pesos de §2")
    for v in ("geo_linear", "geo_linear_anillo_sensible", "r2_linear"):
        c = dict.fromkeys(("prot_perd", "prot_gan", "prot_n", "mb_gan", "mb_perd", "mb_n", "mb_fnK", "mb_fnX",
                           "neg_on", "neg_off", "neg_n", "negK", "negX"), 0.0)
        sin = 0
        for i in ok:
            o = obj[i]
            orc = (res[i].get("oraculo") or {}).get(v)
            if orc is None:
                sin += 1
                continue
            w = o["peso"]
            pk, px = b(T[i]["K_pub"]), alerta(orc, inner[o["volcan"]])
            if o["lab"] == "pos" and o["decide"]:
                if o["protegida"]:
                    c["prot_perd"] += w * (pk and not px); c["prot_gan"] += w * (px and not pk); c["prot_n"] += w
                else:
                    c["mb_gan"] += w * (px and not pk); c["mb_perd"] += w * (pk and not px); c["mb_n"] += w
                    c["mb_fnK"] += w * (not pk); c["mb_fnX"] += w * (not px)
            elif o["lab"] == "neg_limpio":
                c["neg_on"] += w * (px and not pk); c["neg_off"] += w * (pk and not px); c["neg_n"] += w
                c["negK"] += w * pk; c["negX"] += w * px
        dE = (c["mb_fnX"] + c["negX"]) - (c["mb_fnK"] + c["negK"])
        pr(f"   {v}: sin oraculo {sin} | prot perdidas {c['prot_perd']:.0f} ganadas {c['prot_gan']:.0f} de "
           f"{c['prot_n']:.0f} | bajo 1 MW ganadas {c['mb_gan']:.1f} perdidas {c['mb_perd']:.1f} de {c['mb_n']:.1f} | "
           f"neg encendidos {c['neg_on']:.1f} apagados {c['neg_off']:.1f} de {c['neg_n']:.1f} (K {c['negK']:.1f}, "
           f"O {c['negX']:.1f}) | dE {dE:.1f}")

    pr("== (c) protegidas que el oraculo geo_linear no detecta como alerta")
    for i in ok:
        o = obj[i]
        if o["lab"] == "pos" and o["decide"] and o["protegida"]:
            orc = (res[i].get("oraculo") or {}).get("geo_linear")
            if not alerta(orc, inner[o["volcan"]]):
                an = (res[i].get("oraculo") or {}).get("geo_linear_anillo_sensible") or {}
                pr(f"   {i} {o['volcan']} {o['hora_utc']} MIROVA {o['mirova_vrp']} a "
                   f"{[m['dist_km'] for m in o['mirova'] if m['tipo'].startswith('ALERTA')]} km | O {orc and orc.get('npix')} px"
                   f" {orc and orc.get('vrp_mw')} | anillo {an.get('npix')} px {an.get('vrp_mw')}")

    pr("== (d) oraculo geo_linear: |razon - 1| por numero de pixeles, en alertas que detecta")
    for et, cond in (("1 px", lambda n: n == 1), ("2-4 px", lambda n: 2 <= n <= 4), ("5+ px", lambda n: n >= 5)):
        rz = []
        for i in ok:
            o = obj[i]
            orc = (res[i].get("oraculo") or {}).get("geo_linear")
            if o["lab"] == "pos" and o["decide"] and alerta(orc, inner[o["volcan"]]) and cond(orc["npix"]):
                rz.append(orc["vrp_mw"] / o["mirova_vrp"])
        n = len(rz)
        if n:
            pr(f"   {et}: n {n}, a menos de 2 % {sum(abs(x - 1) <= 0.02 for x in rz)}, de 5 % "
               f"{sum(abs(x - 1) <= 0.05 for x in rz)}, de 25 % {sum(abs(x - 1) <= 0.25 for x in rz)}; min "
               f"{min(rz):.3f} max {max(rz):.3f}")
    # banda de triangulación del oráculo: ¿el central (sin perturbar) es el que coincide?
    cen, ban = 0, 0
    for i in ok:
        o = obj[i]
        orc = (res[i].get("oraculo") or {}).get("geo_linear")
        if o["lab"] == "pos" and o["decide"] and alerta(orc, inner[o["volcan"]]) and orc["npix"] == 1 and orc.get("vrp_banda"):
            lo, hi = orc["vrp_banda"]
            if hi - lo > 0.05 * orc["vrp_mw"]:
                ban += 1
                cen += abs(orc["vrp_mw"] / o["mirova_vrp"] - 1) <= 0.05
    pr(f"   1 px con banda de triangulacion mayor que 5 %: {ban}; de ellos el central (sin perturbar) a menos de 5 % "
       f"de MIROVA: {cen}")
    (AQUI / "05_detalle_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
