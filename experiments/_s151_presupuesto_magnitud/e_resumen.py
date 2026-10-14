# -*- coding: utf-8 -*-
"""Tarea 1.14: arma las tablas del README desde las salidas JSON de las partes A, B y C (ningun numero a mano).

Uso: python e_resumen.py   ->  e_resumen_salida.md
"""
from __future__ import annotations

import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def f3(x):
    return "s/d" if x is None else f"{x:.2f}".replace(".", ",")


def ic(t):
    if not t:
        return "s/d"
    return f"{f3(t[0])} [{f3(t[1])}; {f3(t[2])}]"


CERCA_DE_1 = (0.87, 1.15)   # con R casi 1 la media de ln R es casi 0 y una fraccion del deficit no significa nada


def pct(t, r=None):
    if not t:
        return "s/d"
    if r is not None and CERCA_DE_1[0] <= r <= CERCA_DE_1[1]:
        return "n/a (R casi 1)"
    return f"{round(100 * t[0])} % [{round(100 * t[1])}; {round(100 * t[2])}]"


def main():
    A = json.load(open(AQUI / "a_osf_exacto_salida.json", encoding="utf-8"))
    B = json.load(open(AQUI / "b_regimen_actual_salida.json", encoding="utf-8"))
    Cc = json.load(open(AQUI / "c_palancas_ab_salida.json", encoding="utf-8"))
    L = ["## Tabla A. OSF 2025, descomposicion exacta (media geometrica [IC 95 % por noche])", "",
         "| estrato | pasadas / noches | R | F_rec (recorte) | F_sel (conteo x nivel) | de F_sel, por angulo | F_bg (fondo) | reparto log rec / sel / bg | dentro de sel, angulo |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k in ("VIIRS375", "VIIRS375|sin_kernel", "VIIRS375|con_kernel", "VIIRS375|Lascar", "VIIRS375|Isluga",
              "VIIRS375|Lastarria", "VIIRS375|PlanchonPeteroa", "VIIRS375|PuyehueCordonCaulle", "VIIRS375|Chaiten",
              "VIIRS375|Copahue", "VIIRS750|Lascar", "MODIS|Lascar"):
        r = A["reparto"].get(k)
        if not r:
            continue
        ang = r.get("angulo_en_sel") or {}
        L.append(f"| {k} | {r['n_pasadas']} / {r['n_noches']} | {ic(r['R_gm'])} | {ic(r['ln_rec'])} | {ic(r['ln_sel'])} | "
                 f"{ic(ang.get('factor_medio'))} | {ic(r['ln_bg'])} | {pct(r['frac_ln_rec'], r['R_gm'][0])} / "
                 f"{pct(r['frac_ln_sel'], r['R_gm'][0])} / {pct(r['frac_ln_bg'], r['R_gm'][0])} | "
                 f"{pct(ang.get('frac'), r['R_gm'][0])} |")
    L += ["", "## Tabla B. 2026 contra la referencia NRT: R = F_rec x G (media geometrica [IC 95 % por noche])", "",
          "| tramo | estrato | pasadas / noches | R | F_rec | G | parte de G que depende del angulo (factor medio) | fraccion del deficit por angulo | S_all / V_M |",
          "|---|---|---|---|---|---|---|---|---|"]
    for tramo in ("pre_535", "post_535"):
        for k, r in B["tramos"][tramo]["reparto"].items():
            ang = r.get("angulo_en_G") or {}
            L.append(f"| {tramo} | {k} | {r['n_pasadas']} / {r['n_noches']} | {ic(r['R_gm'])} | {ic(r['ln_rec'])} | {ic(r['ln_G'])} | "
                     f"{ic(ang.get('factor_medio'))} | {pct(ang.get('frac'), r['R_gm'][0])} | {f3(r['S_all_sobre_V_M_gm'])} |")
    L += ["", "## Tabla C. Palancas ya implementadas: magnitud del brazo B contra el A en las mismas pasadas positivas", "",
          "| palanca (A -> B) | ventana | sensor o volcan | pasadas / noches | R_A | R_B | B / A | deficit de A que cierra | cambio por recorte / por G |",
          "|---|---|---|---|---|---|---|---|---|"]
    for it in Cc["comparaciones"]:
        filas = list(it["por_sensor"].items()) + list(it["por_volcan"].items())
        for k, r in filas:
            if not r or (k == "VIIRS750" and r["frac_pasadas_identicas"] == 1.0 and it["palanca"] != "nulo_gemelo"):
                continue
            if "|" in k and it["palanca"] not in ("fondo_vecinos_D25", "quitar_test1") and not k.endswith(("Lascar", "Isluga", "Tupungatito", "Lastarria")):
                continue
            L.append(f"| {it['palanca']} | {it['ventana']} | {k} | {r['n_pasadas']} / {r['n_noches']} | {ic(r['R_gm_A'])} | {ic(r['R_gm_B'])} | "
                     f"{ic(r['factor_B_sobre_A'])} | {pct(r['frac_deficit_cerrado'], r['R_gm_A'][0])} | {f3(r['factor_por_recorte'])} / {f3(r['factor_por_G'])} |")
    L += ["", "Agrupado por palanca:", ""]
    for k, r in Cc["agrupado"].items():
        L.append(f"- {k}: {r['n_pasadas']} pasadas, B/A {ic(r['factor_B_sobre_A'])}, cierra {pct(r['frac_deficit_cerrado'])}, "
                 f"R_A {ic(r['R_gm_A'])}, R_B {ic(r['R_gm_B'])}")
    for k, r in Cc.get("agrupado_solo_B", {}).items():
        L.append(f"- {k} (solo B publica): {r['n']} pasadas, R {ic(r['R_gm'])}")
    D = json.load(open(AQUI / "d_tif_fondo_salida.json", encoding="utf-8"))
    L += ["", "## Controles", "",
          f"- Parte A: {json.dumps(A['controles'], ensure_ascii=False)}",
          f"- Parte B, C6 (auto-audit reproducido): pasa = {B['control_C6_auto_audit']['pasa']}, fuera de tolerancia "
          f"{B['control_C6_auto_audit']['fuera_de_tolerancia']}; referencia {json.dumps(B['referencia'])}"]
    for tramo, tr in B["tramos"].items():
        L.append(f"- Parte B {tramo}: {json.dumps(tr['controles'], ensure_ascii=False)}")
    L += [f"- Parte C referencia: {json.dumps(Cc['referencia'])}; nulo gemelo B/A: "
          f"{[Cc['agrupado'][k]['factor_B_sobre_A'] for k in Cc['agrupado'] if k.startswith('nulo_gemelo')]}",
          f"- Parte D: ventana TIF local {D['ventana_tif_local']}, T1 {D['control_T1_atribucion']}, T2 {D['control_T2_campo_comun']}"]
    (AQUI / "e_resumen_salida.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
