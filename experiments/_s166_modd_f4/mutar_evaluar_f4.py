# -*- coding: utf-8 -*-
"""Mutaciones de evaluar_f4.py (S166 MOD-D fase 4). Cada mutación cambia UNA regla del pre-registro en una copia del
evaluador fuera del repositorio y corre la batería ENTERA (probar_evaluar_f4.py) contra la copia.

Clasificación (lección S152/S156: una mutación que sólo hace caer el programa no está atrapada):
- ATRAPADA: algún escenario falla por aserción (código 1 de la batería).
- CAE: ningún escenario falla por aserción, pero alguno cae por excepción (código 2).
- VIVA: la batería pasa entera (código 0).
Dos controles: IDENTIDAD (sin mutación) tiene que salir VIVA, y CONTROL_CAIDA (una excepción al entrar a evaluar)
tiene que salir CAE. Si alguno no sale como debe, el medidor está roto y la cifra no vale.
Uso: python mutar_evaluar_f4.py [--paralelo 4] [--solo M01,M02]  (escribe mutar_evaluar_f4_salida.txt)
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import os
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
FUENTE = (AQUI / "evaluar_f4.py").read_text(encoding="utf-8")

MUTACIONES = [
    ("IDENTIDAD", None, None),
    ("CONTROL_CAIDA", "    for f in filas:\n        f[\"_evaluable\"], f[\"_motivo\"] = evaluable(f)\n    armar_tabla(filas, predicado)",
     "    raise RuntimeError(\"caida de control\")\n    armar_tabla(filas, predicado)"),
    ("M01_p1_nunca_veta", 'return {"estado": "VETADO" if any(not x["solo_ocr"] for x in perd) else (',
     'return {"estado": "VETADO" if False else ('),
    ("M02_solo_ocr_como_sin_perdida", '"SOLO OCR" if perd else "SIN PERDIDA")', '"SIN PERDIDA" if perd else "SIN PERDIDA")'),
    ("M03_corte_1mw", "CORTE_MW = 1.0", "CORTE_MW = 1.5"),
    ("M04_error_bajo1_al_reves", 'if f["lab"] == "bajo1":\n        return _pub(f, b) == 0',
     'if f["lab"] == "bajo1":\n        return _pub(f, b) == 1'),
    ("M05_error_negativo_al_reves", 'if f["lab"] == "neg_limpio":\n        return _pub(f, b) == 1',
     'if f["lab"] == "neg_limpio":\n        return _pub(f, b) == 0'),
    ("M06_far_ref_no_cuenta", 'if lejana and f["lab"] == "far_ref":', 'if False and f["lab"] == "far_ref":'),
    ("M07_signo_contribucion", '"c": 1 if eb else -1', '"c": -1 if eb else 1'),
    ("M08_bloque_por_pasada", 'return "%s|%s" % (f["vol"], f.get("noche") or f["dt"][:10])',
     'return "%s|%s" % (f["vol"], f["dt"])'),
    ("M09_m_decide_mejora", 'x["m"]["regla"] == "EMPEORA"', 'x["m"]["regla"] == "MEJORA"'),
    ("M10_tolerancia_vrp_identidad", "TOL_VRP_IDENTIDAD = 1e-3", "TOL_VRP_IDENTIDAD = 1e-2"),
    ("M11_tope_otro_granulo", "MAX_OTRO_GRANULO = 0.01", "MAX_OTRO_GRANULO = 0.02"),
    ("M12_identidad_sin_clase", ' and ident[k]["misma_clase"])', ")"),
    ("M13_identidad_sin_faltan", "ok = bool(con_grilla) and not faltan and", "ok = bool(con_grilla) and"),
    ("M14_via_sin_marca_evaluable", 'if f.get("v_marca") is not True:', "if False:"),
    ("M15_un_solo_motivo_sellado", 'MOTIVOS_SELLADOS = ("volcan_fuera_del_granulo", "escena_invalida")',
     'MOTIVOS_SELLADOS = ("volcan_fuera_del_granulo",)'),
    ("M16_desempate_al_reves", '0 if b == "V-pico" else 1', '1 if b == "V-pico" else 0'),
    ("M17_empate_gana", 'if br[b]["p2l_vs_V"]["estado"] == "GANA"]', 'if br[b]["p2l_vs_V"]["estado"] in ("GANA", "EMPATE")]'),
    ("M18_v_siempre_elegible", 'if "V" in eleg:', "if True:"),
    ("M19_elegible_solo_sin_perdida", 'br[b]["p1"]["estado"] != "VETADO"]', 'br[b]["p1"]["estado"] == "SIN PERDIDA"]'),
    ("M20_p2_lejana_no_decide", 'est = {x["p2"]["estado"], x["p2l_vs_K"]["estado"]}', 'est = {x["p2"]["estado"]}'),
    ("M21_protegida_k_fuera_ignorada", "            or prot_k):", "            or False):"),
    ("M22_placebo_siempre_ok", 'ok = r["dprima_max_abs"] == 0 and all(', "ok = True or all("),
    ("M23_contador_sin_siguen", "ok = not siguen and len(sel) == N_INYECTAR", "ok = len(sel) == N_INYECTAR"),
    ("M24_cobertura_sin_repetidas", "ok = not rep and not faltan", "ok = not faltan"),
    ("M25_sin_pasada_nuestra_ignorada", "and not fallas and not sin\n", "and not fallas\n"),
    ("M26_store_descarto_ignorado", 'if f.get(c) is None and not (f.get("store_descarto") or {}).get(b)]',
     "if f.get(c) is None]"),
    ("M27_tolerancia_posicion", "TOL_DIST_POSICION = 6e-4", "TOL_DIST_POSICION = 1.0"),
    ("M28_k_reproducida_ignorada", 'and not f.get("k_reproducida_en_su_sha")]', "]"),
    ("M29_externo_ausente_ok", 'ctl[k] = externos.get(k) or {"estado": "INDECIDIBLE", "motivo": "control externo ausente"}',
     'ctl[k] = externos.get(k) or {"estado": "OK"}'),
    ("M30_corte_cenit_chillan", "CORTE_CENIT_CHILLAN = 30.0", "CORTE_CENIT_CHILLAN = 60.0"),
    ("M31_chillan_minimo_pares", "    if n < 5:\n        estado = \"SIN SUSTRATO\"", "    if n < 4:\n        estado = \"SIN SUSTRATO\""),
    ("M32_frontera_exclusiva", 'return "summit" if dist <= inner else "far"', 'return "summit" if dist < inner else "far"'),
    ("M33_cercano_es_el_lejano", '"cercano": min(d(f, c) for f, c in celdas)', '"cercano": max(d(f, c) for f, c in celdas)'),
    ("M34_pico_es_el_centroide", '"pico": d(*pico)}', '"pico": d(fr, fc)}'),
    ("M35_neto_sin_ocr_cuenta_todo", 'sum(x["c"] for x in c if not x["solo_ocr"])', 'sum(x["c"] for x in c)'),
    ("M36_record_v_ausente_ignorado", "if f.get(c) is None and not (f.get", "if False and not (f.get"),
    ("M37_sin_sustrato_propone", 'if "SIN SUSTRATO" in est:\n        return "INDECIDIBLE"',
     'if "SIN SUSTRATO" in est:\n        return "PROPONER ADOPCIÓN"'),
    ("M38_pierde_no_veta", 'if "PIERDE" in est:', "if False:"),
    ("M39_bloquea_no_decide", 'if ("BLOQUEA" in est or', "if (False or"),
    ("M40_p1b_no_decide", ' or x["p1b"]["decide"] or', " or"),
    ("M41_variante_no_cambia_clase", '    r["distance_class"] = clase_dc(dd, inner)\n', ""),
    ("M42_p1_mira_al_brazo_contra_si_mismo", 'if f["lab"] == "protegida" and _pub(f, ref) == 1 and _pub(f, b) == 0]',
     'if f["lab"] == "protegida" and _pub(f, b) == 1 and _pub(f, b) == 0]'),
    ("M43_descriptivas_vacias", 'for f in _ev(filas) if _pub(f, b) != _pub(f, "V")]', "for f in _ev(filas) if False]"),
    ("M44_excluida_sin_cotejar_runner", 'if pub != int((f.get("pub_runner") or {}).get("K") or 0):', "if False:"),
    ("M45_lejanas_sin_alertados", '"con_alertados": sum(1 for f in lej if', '"con_alertados": sum(0 for f in lej if'),
    ("M46_excluida_listada_sin_publicar", "        if pub:\n            prot_fuera.append(",
     "        if True:\n            prot_fuera.append("),
]
# Cada texto a mutar tiene que aparecer exactamente una vez en evaluar_f4.py; si no, el medidor dice «NO APLICA» en vez
# de mutar otra cosa.


def correr(nombre, viejo, nuevo, tmp):
    if viejo is None:
        src = FUENTE
    else:
        n = FUENTE.count(viejo)
        if n != 1:
            return nombre, "NO APLICA (%d apariciones)" % n, ""
        src = FUENTE.replace(viejo, nuevo)
    ruta = Path(tmp) / ("ev_%s.py" % nombre)
    ruta.write_text(src, encoding="utf-8")
    env = dict(os.environ, F4_RAIZ=str(RAIZ), PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, str(AQUI / "probar_evaluar_f4.py"), "--modulo", str(ruta)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    clase = {0: "VIVA", 1: "ATRAPADA", 2: "CAE"}.get(p.returncode, "CODIGO_%s" % p.returncode)
    fallan = [ln.split()[2] for ln in p.stdout.splitlines() if ln.startswith("FALLA ASERCION")]
    caen = [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("CAE ")]
    resumen = [ln for ln in p.stdout.splitlines() if ln.startswith("RESUMEN")]
    return nombre, clase, "%s | por aserción: %s | caen: %s" % (resumen[0] if resumen else p.stderr[-300:],
                                                              ",".join(x.split("_")[0] for x in fallan) or "-",
                                                              ",".join(x.split("_")[0] for x in caen) or "-")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--paralelo", type=int, default=4)
    ap.add_argument("--solo", default=None)
    ap.add_argument("--salida", default=str(AQUI / "mutar_evaluar_f4_salida.txt"))
    a = ap.parse_args()
    sel = [m for m in MUTACIONES if not a.solo or m[0] in ("IDENTIDAD", "CONTROL_CAIDA")
           or m[0].split("_")[0] in a.solo.split(",")]
    with tempfile.TemporaryDirectory(prefix="mut_f4_") as tmp, cf.ThreadPoolExecutor(a.paralelo) as ex:
        res = list(ex.map(lambda m: correr(*m, tmp), sel))
    lineas = ["%-40s %-10s %s" % r for r in res]
    ident = dict((r[0], r[1]) for r in res)
    muts = [r for r in res if r[0].startswith("M")]
    atr = sum(1 for r in muts if r[1] == "ATRAPADA")
    lineas.append("")
    lineas.append("CONTROLES: identidad %s (debe ser VIVA), control de caída %s (debe ser CAE)" % (
        ident.get("IDENTIDAD"), ident.get("CONTROL_CAIDA")))
    lineas.append("MUTACIONES: %d de %d atrapadas por aserción; vivas %s; caen %s; no aplican %s" % (
        atr, len(muts), [r[0] for r in muts if r[1] == "VIVA"], [r[0] for r in muts if r[1] == "CAE"],
        [r[0] for r in muts if r[1].startswith("NO APLICA")]))
    txt = "\n".join(lineas)
    print(txt)
    Path(a.salida).write_text(txt + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
