# -*- coding: utf-8 -*-
"""Mutaciones de evaluar_f4.py (S166 MOD-D fase 4). Cada mutación cambia UNA regla del pre-registro en una copia del
evaluador fuera del repositorio y corre la batería ENTERA (probar_evaluar_f4.py) contra la copia.

Clasificación (lección S152/S156: una mutación que sólo hace caer el programa no está atrapada):
- ATRAPADA: algún escenario falla por aserción (código 1 de la batería) y ninguno cae.
- ATRAPADA_CON_CAIDAS: alguno falla por aserción y otro cae por excepción (VS-01 del tercer verificador): no cuenta como
  atrapada, porque la aserción puede ser un escenario que convierte la caída en falla.
- CAE: ningún escenario falla por aserción, pero alguno cae por excepción (código 2).
- VIVA: la batería pasa entera (código 0).
- ROTA: la copia no carga (error de sintaxis) o sale con código 1 sin ninguna aserción fallida (VF4-08): no cuenta.
Cuatro controles: IDENTIDAD (sin mutación) tiene que salir VIVA, CONTROL_CAIDA (un RuntimeError al entrar a evaluar)
y CONTROL_CAIDA_VALUEERROR (lo mismo con ValueError, la excepción que E53 sabe convertir; VS-01) tienen que salir CAE,
y CONTROL_ROTA (un error de sintaxis) tiene que salir ROTA. Si alguno no sale como debe, el medidor está roto y la cifra no vale.
Uso: python mutar_evaluar_f4.py [--paralelo 4] [--solo M01,M02] [--salida ruta]  (escribe mutar_evaluar_f4_salida.txt)
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
    ("CONTROL_ROTA", "PLACEBO = 1.2", "PLACEBO = = 1.2"),
    ("CONTROL_CAIDA", "    for f in filas:\n        f[\"_evaluable\"], f[\"_motivo\"] = evaluable(f)\n    armar_tabla(filas, predicado)",
     "    raise RuntimeError(\"caida de control\")\n    armar_tabla(filas, predicado)"),
    ("CONTROL_CAIDA_VALUEERROR",
     "    for f in filas:\n        f[\"_evaluable\"], f[\"_motivo\"] = evaluable(f)\n    armar_tabla(filas, predicado)",
     "    raise ValueError(\"caida de control\")\n    armar_tabla(filas, predicado)"),
    ("M01_p1_nunca_veta", 'return {"estado": "VETADO" if any(not x["solo_ocr"] for x in perd) else (',
     'return {"estado": "VETADO" if False else ('),
    ("M02_solo_ocr_como_sin_perdida", '"SOLO OCR" if perd else "SIN PERDIDA")', '"SIN PERDIDA" if perd else "SIN PERDIDA")'),
    ("M03_corte_1mw", "CORTE_MW = 1.0", "CORTE_MW = 1.5"),
    ("M04_error_bajo1_al_reves", 'if lab == "bajo1":\n        return _pub(f, b) == 0', 'if lab == "bajo1":\n        return _pub(f, b) == 1'),
    ("M05_error_negativo_al_reves", 'if lab == "neg_limpio":\n        return _pub(f, b) == 1', 'if lab == "neg_limpio":\n        return _pub(f, b) == 0'),
    ("M06_far_ref_no_cuenta", 'if lejana and lab == "far_ref":', 'if False and lab == "far_ref":'),
    ("M07_signo_contribucion", '"c": 1 if eb else -1', '"c": -1 if eb else 1'),
    ("M08_bloque_por_pasada", 'return "%s|%s" % (f["vol"], f.get("noche") or f["dt"][:10])',
     'return "%s|%s" % (f["vol"], f["dt"])'),
    ("M09_m_decide_mejora", 'x["m"]["regla"] == "EMPEORA"', 'x["m"]["regla"] == "MEJORA"'),
    ("M10_tolerancia_vrp_identidad", "TOL_VRP_IDENTIDAD = 1e-3", "TOL_VRP_IDENTIDAD = 1e-2"),
    ("M11_tope_otro_granulo", "MAX_OTRO_GRANULO = 0.01", "MAX_OTRO_GRANULO = 0.02"),
    # M12: el texto cambió con la adenda a N-01 (la línea sigue con el caso simétrico); la mutación es la misma
    ("M12_identidad_sin_clase", '<= TOL_VRP_IDENTIDAD and ident[k]["misma_clase"]', "<= TOL_VRP_IDENTIDAD"),
    ("M13_identidad_sin_faltan", "and bool(con_grilla) and not faltan and", "and bool(con_grilla) and"),
    ("M14_via_sin_marca_evaluable", 'if f.get("v_marca") is not True:', "if False:"),
    ("M15_un_solo_motivo_sellado", 'MOTIVOS_SELLADOS = ("volcan_fuera_del_granulo", "escena_invalida")',
     'MOTIVOS_SELLADOS = ("volcan_fuera_del_granulo",)'),
    ("M16_desempate_al_reves", '0 if b == "V-pico" else 1', '1 if b == "V-pico" else 0'),
    ("M17_empate_gana", 'if br[b]["p2l_vs_V"]["estado"] == "GANA"]', 'if br[b]["p2l_vs_V"]["estado"] in ("GANA", "EMPATE")]'),
    ("M18_v_siempre_elegible", 'if "V" in eleg:', "if True:"),
    ("M19_elegible_solo_sin_perdida", 'if br[b]["p1"]["estado"] != "VETADO"\n', 'if br[b]["p1"]["estado"] == "SIN PERDIDA"\n'),
    ("M20_p2_lejana_no_decide", 'est = {x["p2"]["estado"], x["p2l_vs_K"]["estado"]}', 'est = {x["p2"]["estado"]}'),
    ("M21_protegida_k_fuera_ignorada", 'or prot_k or res.get("protegidas_que_otra_posicion_publica")', 'or False or res.get("protegidas_que_otra_posicion_publica")'),
    ("M22_placebo_siempre_ok", 'ok = r["dprima_max_abs"] == 0 and all(', "ok = True or all("),
    ("M23_contador_sin_siguen", "ok = not siguen and len(sel) == N_INYECTAR", "ok = len(sel) == N_INYECTAR"),
    ("M24_cobertura_sin_repetidas", "ok = not rep and not faltan", "ok = not faltan"),
    ("M25_sin_pasada_nuestra_ignorada", "and not fallas and not sin and not sin_medir", "and not fallas and not sin_medir"),
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
    ("M35_union_decide", 'return f.get("lab_union", f["lab"]) if union else f["lab"]', 'return f.get("lab_union", f["lab"])'),
    ("M36_record_v_ausente_ignorado", "if f.get(c) is None and not (f.get", "if False and not (f.get"),
    ("M37_sin_sustrato_propone", 'if "SIN SUSTRATO" in est:\n        return "INDECIDIBLE"',
     'if "SIN SUSTRATO" in est:\n        return "PROPONER ADOPCIÓN"'),
    ("M38_pierde_no_veta", 'if "PIERDE" in est:', "if False:"),
    ("M39_bloquea_no_decide", 'if ("BLOQUEA" in est or', "if (False or"),
    ("M40_p1b_no_decide", ' or x["p1b"]["decide"] or', " or"),
    ("M41_variante_no_cambia_clase", '    r["distance_class"] = clase_dc(dd, inner)\n', ""),
    ("M42_p1_mira_al_brazo_contra_si_mismo", 'if _lab(f, True) == "protegida" and _pub(f, ref) == 1 and _pub(f, b) == 0]', 'if _lab(f, True) == "protegida" and _pub(f, b) == 1 and _pub(f, b) == 0]'),
    ("M43_descriptivas_vacias", 'for f in _ev(filas) if _pub(f, b) != _pub(f, "V")]', "for f in _ev(filas) if False]"),
    ("M44_excluida_sin_cotejar_runner", 'elif pub != int(f["pub_runner"]["K"]):', "elif False:"),
    ("M45_lejanas_sin_alertados", '"con_alertados": sum(1 for f in lej if', '"con_alertados": sum(0 for f in lej if'),
    ("M46_excluida_listada_sin_publicar", "        if pub:\n            prot_fuera.append(",
     "        if True:\n            prot_fuera.append("),
    ("M47_posicion_puede_perder_protegida_de_V", ' and (b == "V" or br[b]["p1_vs_V"]["estado"] != "VETADO")]', "]"),
    ("M48_otra_posicion_recupera_ignorada", '            or prot_k or res.get("protegidas_que_otra_posicion_publica")):',
     "            or prot_k):"),
    ("M49_identidad_sin_total_de_grillas", "ok = n_pob == n_grillas_censo and bool(con_grilla)", "ok = bool(con_grilla)"),
    ("M50_k_sin_campo_ok", "ok = not sin_campo and not sin_pub and", "ok = not sin_pub and"),
    ("M51_lista_ausente_ok", "and not sin and not sin_medir", "and not sin"),
    ("M52_sin_protocolo_e", 'if rojo_solo_en_e(res["controles"]["cobertura"]):', "if False:"),
    ("M53_protocolo_no_saca_e", '_evaluar([f for f in filas if not _es_e(f["dt"])]', "_evaluar([f for f in filas]"),
    ("M54_protocolo_con_cualquier_e", "return bool(dts) and all(_es_e(d) for d in dts)", "return bool(dts) and any(_es_e(d) for d in dts)"),
    ("M55_contador_cuarenta", "N_INYECTAR, SEMILLA_INYECTAR = 50, 166", "N_INYECTAR, SEMILLA_INYECTAR = 40, 166"),
    ("M56_chillan_banda_alta", "0.8 <= med <= 1.25 and 20 * num <= den", "0.8 <= med <= 2.0 and 20 * num <= den"),
    ("M57_chillan_banda_baja", "0.8 <= med <= 1.25 and 20 * num <= den", "0.5 <= med <= 1.25 and 20 * num <= den"),
    ("M58_chillan_p", "0.8 <= med <= 1.25 and 20 * num <= den", "0.8 <= med <= 1.25 and 2 * num <= den"),
    ("M59_no_peor_tolera_neto", 'p["neto"] <= 0)', 'p["neto"] <= 5)'),
    ("M60_p1b_k_estricto", '_mag(f, "K") >= CORTE_MW > _mag(f, b)', '_mag(f, "K") > CORTE_MW > _mag(f, b)'),
    ("M61_estado_arnes_ignorado", 'if f.get("estado") != "ok":\n        return False, "falla_arnes_"',
     'if False:\n        return False, "falla_arnes_"'),
    ("M62_motivo_desconocido_ok", '    if mot:\n        return False, "falla_" + str(mot)', '    if False:\n        return False, "falla_" + str(mot)'),
    ("M63_chillan_siempre_V", 'res["chillan"] = chillan(filas, bc)', 'res["chillan"] = chillan(filas, "V")'),
    ("M64_posicion_sin_clase", ' and \\\n            clase_dc(d, f["inner"]) == v.get("distance_class")', ""),
    ("M65_posicion_sin_vrp", 'if w.get("distance_class") == v.get("distance_class"):', "if False:"),
    ("M66_cobertura_sin_sobrantes", "and not sobran and", "and"),
    ("M67_main_sin_lista_ok", 'pob.get("sin_pasada_nuestra"), predicado', "(), predicado"),
    # segunda vuelta del verificador: X01 a X14 (vivas con la batería de 53) y las reglas nuevas N-01, N-02, N-03, N-05
    ("M68_frontera_e_un_dia_despues", 'INICIO_E = "2026-10-17"', 'INICIO_E = "2026-10-18"'),
    ("M69_frontera_e_estricta", "return str(dt)[:10] >= INICIO_E", "return str(dt)[:10] > INICIO_E"),
    ("M70_chillan_sin_magnitud_positiva", ' and _mag(f, "K") > 0 and _mag(f, b) > 0:\n            mm', ":\n            mm"),
    ("M71_elegible_solo_sin_perdida", '(b == "V" or br[b]["p1_vs_V"]["estado"] != "VETADO")',
     '(b == "V" or br[b]["p1_vs_V"]["estado"] == "SIN PERDIDA")'),
    ("M72_identidad_total_minimo", "ok = n_pob == n_grillas_censo", "ok = n_pob >= n_grillas_censo"),
    ("M73_tope_otro_granulo_exclusivo", "frac_otro <= MAX_OTRO_GRANULO", "frac_otro < MAX_OTRO_GRANULO"),
    ("M74_otra_posicion_solo_tabla", 'for x in p1(filas, bc, o)["perdidas"]})',
     'for x in p1(filas, bc, o)["perdidas"] if not x["solo_ocr"]})'),
    ("M75_protegida_sellada_solo_tabla", 'not f["_evaluable"] and _lab(f, True) == "protegida"',
     'not f["_evaluable"] and _lab(f, False) == "protegida"'),
    ("M76_identidad_ignora_selladas", "not selladas_sin_explicar and frac_otro", "frac_otro"),
    ("M77_selladas_no_cuentan_en_el_tope", "for k in con_grilla + selladas if k in ident", "for k in con_grilla if k in ident"),
    ("M78_k_difiere_none_ok", 'not isinstance(f.get("k_difiere_de_guardado"), bool)', '"k_difiere_de_guardado" not in f'),
    ("M79_sin_publicacion_de_k_ok", "ok = not sin_campo and not sin_pub and not sin_explicar",
     "ok = not sin_campo and not sin_explicar"),
    ("M80_e_via_no_corrio_propone", 'if res["e_via_no_corrio"] and res["veredicto"] == "PROPONER ADOPCIÓN":', "if False:"),
    ("M81_e_via_cualquier_falla", 'if str(x["motivo"]).startswith("falla_via_")]', "]"),
    # M82: la fila sin publicación de K del runner se acepta en silencio (con «if False» caía en el elif por KeyError
    # y salía CAE, que no es la mutación que se quiere medir)
    ("M82_excluida_sin_publicacion_ok",
     'fallas.append({"vol": f["vol"], "dt": f["dt"], "motivo": "sin_publicacion_de_K_del_runner"})', "pass"),
    # M83 a M86: las mutaciones A1, A3, A6 y A8 del tercer verificador (VS-03 a VS-06), con su escenario nuevo
    ("M83_n_grillas_censo_5322", "N_GRILLAS_CENSO = 5321 ", "N_GRILLAS_CENSO = 5322 "),
    ("M84_posicion_sin_n", '"OK" if n and not malas else "INDECIDIBLE", "n_con_alertados"',
     '"OK" if not malas else "INDECIDIBLE", "n_con_alertados"'),
    ("M85_contador_sin_no_pasan", "ok = not siguen and len(sel) == N_INYECTAR and not no_pasan and",
     "ok = not siguen and len(sel) == N_INYECTAR and"),
    ("M86_chillan_empates_como_pares", "(empates if db == dk else pares).append(par)", "pares.append(par)"),
    # M87 a M94: la adenda a N-01 (S170, borrador), una condición por mutación, con E65 a E67
    ("M87_adenda_sin_motivo_censo", 'return (x.get("motivo_censo") == "escena_invalida" and x.get("mismo_granulo") is True',
     'return (x.get("mismo_granulo") is True'),
    ("M88_adenda_sin_grilla_igual", 'and x.get("grilla_igual_float32") is True and x.get("misma_mascara") is True',
     'and x.get("misma_mascara") is True'),
    ("M89_adenda_sin_mascara", 'and x.get("grilla_igual_float32") is True and x.get("misma_mascara") is True',
     'and x.get("grilla_igual_float32") is True'),
    ("M90_adenda_sin_clase", 'and x.get("misma_clase") is True and x.get("dvrp") is not None',
     'and x.get("dvrp") is not None'),
    ("M91_adenda_sin_vrp", 'x.get("dvrp") is not None and abs(x["dvrp"]) <= TOL_VRP_IDENTIDAD)',
     'x.get("dvrp") is not None)'),
    ("M92_adenda_tambien_fuera", 'if k in ident and motivo_de[k] == "escena_invalida"', 'if k in ident'),
    ("M93_adenda_sin_simetrico", '                 and ident[k].get("motivo_censo") != "escena_invalida")]', ')]'),
    ("M94_adenda_nunca_acuerdo", '                                   and k not in por_acuerdo)', ')'),
]
CONTROLES = (("IDENTIDAD", "VIVA"), ("CONTROL_CAIDA", "CAE"), ("CONTROL_CAIDA_VALUEERROR", "CAE"),
             ("CONTROL_ROTA", "ROTA"))
# Cada texto a mutar tiene que aparecer exactamente una vez en evaluar_f4.py; si no, el medidor dice «NO APLICA» en vez
# de mutar otra cosa.


def clasificar(codigo, fallan, caen):
    """VS-01: ATRAPADA sólo si hay aserciones y ninguna caída; con las dos, ATRAPADA_CON_CAIDAS, que no cuenta."""
    if codigo == 1:
        return ("ATRAPADA_CON_CAIDAS" if caen else "ATRAPADA") if fallan else "ROTA"
    return {0: "VIVA", 2: "CAE", 3: "ROTA"}.get(codigo, "CODIGO_%s" % codigo)


def controles_malos(clases):
    """N-02: los controles que no salen como deben (uno ausente no se cuenta: --solo siempre los corre)."""
    return [c for c, debe in CONTROLES if clases.get(c) != debe]


def resumir(res):
    """Las líneas de salida y el código de salida: 1 y «NO VALE» si algún control no sale como debe (VS-03: probado en
    probar_mutar_f4.py)."""
    lineas = ["%-40s %-10s %s" % r for r in res]
    ident = dict((r[0], r[1]) for r in res)
    muts = [r for r in res if r[0][:1] == "M" and r[0][1:3].isdigit()]
    atr = sum(1 for r in muts if r[1] == "ATRAPADA")
    lineas.append("")
    lineas.append("CONTROLES: " + ", ".join("%s %s (debe ser %s)" % (c, ident.get(c), debe) for c, debe in CONTROLES))
    lineas.append("MUTACIONES: %d de %d atrapadas por aserción; vivas %s; caen %s; atrapadas con caídas %s; rotas %s; "
                  "no aplican %s" % (
                      atr, len(muts), [r[0] for r in muts if r[1] == "VIVA"], [r[0] for r in muts if r[1] == "CAE"],
                      [r[0] for r in muts if r[1] == "ATRAPADA_CON_CAIDAS"], [r[0] for r in muts if r[1] == "ROTA"],
                      [r[0] for r in muts if r[1].startswith("NO APLICA")]))
    # N-02 (segunda vuelta): si un control no sale como debe, la cifra no vale (con la identidad ATRAPADA, una mutación
    # puede parecer atrapada por un escenario que falla igual sin mutar); se dice en la salida y el código es 1
    malos = controles_malos(ident)
    if malos:
        lineas.append("NO VALE: controles que no salen como deben: %s" % malos)
    return "\n".join(lineas), 1 if malos else 0


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
    fallan = [ln.split()[2] for ln in p.stdout.splitlines() if ln.startswith("FALLA ASERCION")]
    # VF4-08: ATRAPADA exige al menos un escenario que falla POR ASERCIÓN; un código 1 sin ninguno (un error de sintaxis
    # al importar) o un 3 (la copia no carga) es ROTA: la mutación está mal escrita y no cuenta
    caen = [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("CAE ")]
    clase = clasificar(p.returncode, fallan, caen)
    resumen = [ln for ln in p.stdout.splitlines() if ln.startswith("RESUMEN")]
    if os.environ.get("MUT_PROGRESO"):  # corridas largas: una línea por mutación, para no perderlo todo si se corta
        with open(os.environ["MUT_PROGRESO"], "a", encoding="utf-8") as fh:
            fh.write("%s %s %s\n" % (nombre, clase, resumen[0] if resumen else "-"))
    return nombre, clase,"%s | por aserción: %s | caen: %s" % (resumen[0] if resumen else p.stderr[-300:],
                                                              ",".join(x.split("_")[0] for x in fallan) or "-",
                                                              ",".join(x.split("_")[0] for x in caen) or "-")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--paralelo", type=int, default=4)
    ap.add_argument("--solo", default=None)
    ap.add_argument("--salida", default=str(AQUI / "mutar_evaluar_f4_salida.txt"))
    a = ap.parse_args()
    sel = [m for m in MUTACIONES if not a.solo or m[0] in dict(CONTROLES)
           or m[0].split("_")[0] in a.solo.split(",")]
    with tempfile.TemporaryDirectory(prefix="mut_f4_") as tmp, cf.ThreadPoolExecutor(a.paralelo) as ex:
        res = list(ex.map(lambda m: correr(*m, tmp), sel))
    txt, codigo = resumir(res)
    print(txt)
    Path(a.salida).write_text(txt + "\n", encoding="utf-8")
    sys.exit(codigo)


if __name__ == "__main__":
    main()
