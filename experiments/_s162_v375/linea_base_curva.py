# -*- coding: utf-8 -*-
"""S162 V375-E, línea base: la curva de cenit de PRODUCCIÓN (K) contra la de MIROVA en VIIRS 375, sobre la población
congelada de S159 (experiments/_s159/portes/poblacion_completa.json: records de origin/main 533398f8f con K, pareo
±120 s, regla SN). No es un resultado del paquete: es el brazo de control de V375-E medido de antemano, y sirve para
probar curva_cenit.py sobre datos reales.

Lo que el tablero publica en VIIRS 375 es la magnitud del núcleo (`f5_core_vrp_mw`, con `pc.vrp_mw` cuando falta, A10
matiz S132). Ventana: 2026-04-01 a 2026-10-21 sin el 12, 13 y 17 a 20 de octubre; también por tramo T / O.
Uso: python -I linea_base_curva.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import curva_cenit as CC  # noqa: E402

EXCLUIDOS = ("2026-10-12", "2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")


def main():
    pob = json.loads((RAIZ / "experiments/_s159/portes/poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"]
    pas = []
    for o in pob:
        if o["b"] != "VIIRS375" or o["lab"] != "pos" or not o["decide"] or o["hora_utc"][:10] in EXCLUIDOS:
            continue
        vk = o.get("f5_core") if o.get("f5_core") is not None else o.get("pc_vrp")
        pas.append({"vol": o["volcan"], "hora": o["hora_utc"], "z": o["z"], "mir": o["mirova_vrp"],
                    "K": bool(o["pub_prod"]), "VK": vk, "plat": o.get("sensor")})
    print("pasadas con alerta de MIROVA que deciden:", len(pas))
    sp = CC.sesgo_plataforma(pas, "VK", "K")
    print("sesgo de plataforma de K contra MIROVA (factor mediano, IC, n):",
          {k: (round(v["factor"], 3), [round(10 ** x, 3) for x in v["ic"]], v["n"]) for k, v in sp["por_plataforma"].items()},
          "-> SESGADO" if sp["sesgado"] else "-> sin sesgo de plataforma")
    for nom, cond in (("condicionada (las dos pasadas publicadas)", True), ("sin condicionar (no publica = 0)", False)):
        for tr, f in (("todo", lambda p: True), ("T", lambda p: p["hora"][:10] < "2026-06-13"),
                      ("O", lambda p: p["hora"][:10] >= "2026-06-13")):
            pares = CC.pares_por_noche([p for p in pas if f(p)], "VK", "K", condicionar=cond)
            r = CC.resumen(pares, nulo=CC.pares_nulo([p for p in pas if f(p)], "VK", "K", condicionar=cond))
            t = r["todas"]
            fm = lambda x: f"{x[0]:.3f} [{x[1][0]:.3f}; {x[1][1]:.3f}] n {x[2]}"  # noqa: E731
            print(f"\n{nom}, {tr}: noches {t['n_noches']}; MIROVA oblicua/menos {fm(t['r_mir'])} (nulo por hora "
                  f"{fm(t['r_mir_hora'])}, no sirve en 375; bajo 1: {t['bajo_1_mir']}); K {fm(t['r_x'])}; razón doble K/MIROVA "
                  f"{fm(t['d'])} -> {CC.veredicto(r)}")
            print(f"   curva de MIROVA separada del nulo: {CC.curva_mirova_separada(r)}")
            nu = r["nulo"]
            print(f"   nulo de cenit parecido (< 5°, ordenado como la lectura): noches {nu['n_noches']}; MIROVA {fm(nu['r_mir'])}; "
                  f"K {fm(nu['r_x'])}; d {fm(nu['d'])}")
            for k, v in r.items():
                if k in ("misma plataforma", "plataformas distintas"):
                    print(f"   {k}: noches {v['n_noches']}; d {fm(v['d'])}")
                elif k not in ("todas", "nulo"):
                    print(f"   {k}: noches {v['n_noches']}; MIROVA {fm(v['r_mir'])}; K {fm(v['r_x'])}; d {fm(v['d'])}")
            if tr == "todo" and cond:
                # controles del instrumento (PREREGISTRO_E.md §4): ganancia pareja no mueve d; ganancia que crece con
                # el cenit (1 + 0,01 por grado sobre 20°) tiene que subirlo
                for nom_c, g in (("ganancia pareja x1,2", lambda z: 1.2),
                                 ("ganancia con el cenit", lambda z: 1 + 0.01 * max(z - 20, 0))):
                    pc = [{**p, "VK": (p["VK"] or 0) * g(p["z"] or 0)} for p in pas if f(p)]
                    rc = CC.resumen(CC.pares_por_noche(pc, "VK", "K", condicionar=cond))
                    print(f"   control {nom_c}: d {fm(rc['todas']['d'])}")
                vols = {}
                for p in pares:
                    vols.setdefault(p["vol"], []).append(round(p["d"], 2))
                print("   d por volcán:", vols)


if __name__ == "__main__":
    main()
