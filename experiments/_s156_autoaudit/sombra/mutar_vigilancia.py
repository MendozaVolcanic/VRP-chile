"""Mutaciones de scripts/vigilancia_sombra.py y de .github/workflows/vigilancia-sombra.yml: cada una debe hacer
FALLAR una prueba POR ASERCIÓN. Una mutación que sólo hace caer el script (KeyError, NameError...) no cuenta: el
criterio lee el resumen `-rf` de pytest (verificador 4 de S156: el criterio anterior no distinguía).
Incluye las del autor y las de los verificadores 2 (M), 3 (N) y 4 (Q), con los textos del código de hoy.
Uso: python mutar_vigilancia.py <raiz_worktree>. Restaura los archivos originales al terminar."""
import re
import subprocess
import sys
from pathlib import Path

raiz = Path(sys.argv[1])
SCRIPT = "scripts/vigilancia_sombra.py"
WF = ".github/workflows/vigilancia-sombra.yml"
originales = {f: (raiz / f).read_text(encoding="utf-8") for f in (SCRIPT, WF)}

MUT = {
    # autor
    "tolerancia_3600": ("TOL_S = cm.VENTANA_S", "TOL_S = 3600"),
    "publica_all": ('return None if not cands else any(r["pub"] for r in cands)',
                    'return None if not cands else all(r["pub"] for r in cands)'),
    "negativos_cualquier_lab": ('if r["b"] == "VIIRS375" and r.get("lab_original") == "neg_limpio"',
                                'if r["b"] == "VIIRS375"'),
    "negativos_cualquier_sensor": ('if r["b"] == "VIIRS375" and r.get("lab_original") == "neg_limpio"',
                                   'if r.get("lab_original") == "neg_limpio"'),
    "negativos_sin_corte": ('and corte_dt is not None and r["dt"] >= corte_dt]', "]"),
    "cotas_en_todos_los_sensores": ("cotas = COTAS_AB[tipo].get(sensor)", 'cotas = COTAS_AB[tipo].get("VIIRS375")'),
    "ventana_ignorada": ('if f.get("tipo") in cm.TIPOS_ALERTA and win[0] <= f["fecha_utc"][:10] <= win[1]:',
                         'if f.get("tipo") in cm.TIPOS_ALERTA:'),
    "diurnas_incluidas": ("        if diurna(b, vol, dt):\n            continue\n", ""),
    "cumplida_solo_por_dias": ('"cumplida": vistas >= PROTEGIDAS_OBJETIVO or bool(vence and hoy >= vence)',
                               '"cumplida": bool(vence and hoy >= vence)'),
    "muy_bajo_incluye_protegidas": ('if p["protegida"] or p["minima"] or p["prod_pub"] is None',
                                    'if p["minima"] or p["prod_pub"] is None'),
    "sin_corte_prospectivo": ('pros = [p for p in pasadas if p["instante_utc"] >= corte]', "pros = list(pasadas)"),
    "corte_al_minuto": ('pros = [p for p in pasadas if p["instante_utc"] >= corte]',
                        'pros = [p for p in pasadas if p["instante_utc"][:16] >= corte[:16]]'),
    "reversion_sin_protegida": ('candidatas = [p for p in calla if p["protegida"] and _clave(p) not in juzgadas]',
                                'candidatas = [p for p in calla if _clave(p) not in juzgadas]'),
    "sin_aviso_perfiles": ("\n              + avisos_perfiles(prod, sombra))", ")"),
    "ciega_no_degrada": ('veredicto = "VIGILANCIA_CIEGA"\n    out.update', "pass\n    out.update"),
    "sombra_detenida_tarde": ("MAX_DIAS_SOMBRA_SIN_DATOS = 3", "MAX_DIAS_SOMBRA_SIN_DATOS = 30"),
    "persistencia_dos": ("def _corridas(fechas, largo=3):", "def _corridas(fechas, largo=2):"),
    "sospecha_apagada": ("sospechosa = (bool(protegidas)", "sospechosa = (False and bool(protegidas)"),
    "duracion_cuenta_retro": ('vistas_pros = sorted((p for p in pros if', 'vistas_pros = sorted((p for p in pasadas if'),
    "minima_mal_marcada": ('"minima": clave in minimas,', '"minima": False,'),
    "persistencia_con_minimas": ('persistencia = _persistencia([p for p in calla if not p["minima"]])',
                                 "persistencia = _persistencia(calla)"),
    "frescura_global": ('        ultima[(r["vol"], r["b"])] = max(ultima[(r["vol"], r["b"])], r["noche"])',
                        '        ultima[(r["vol"], r["b"])] = max(x["noche"] for x in recs)'),
    "adopcion_sin_segundos": ('return f"{m.group(1)} {m.group(2)}{m.group(3) or \':00\'}" if m else None',
                              'return f"{m.group(1)} {m.group(2)}:00" if m else None'),
    "cargar_insumos_sin_original": ('    for r in prod:\n        r["lab_original"] = r["lab"]\n', ""),
    # verificador 2 (M1 a M13)
    "M1_pareo_sin_sensor": ('idx[nombre][(r["vol"], r["b"])].append(r)', 'idx[nombre][r["vol"]].append(r)'),
    "M2_frescura_de_produccion": ("+ avisos_sombra(sombra, hoy) +", "+ avisos_sombra(prod, hoy) +"),
    "M3_muy_bajo_sin_condicion_sombra": ('c[0] += bool(p["sombra_pub"] and not p["prod_pub"])',
                                         'c[0] += bool(not p["prod_pub"])'),
    "M4_persistencia_incluye_retro": ('persistencia = _persistencia([p for p in calla if not p["minima"]])',
                                      'persistencia = _persistencia([p for p in _sombra_si_produccion_no(pasadas) if not p["minima"]])'),
    "M5_umbral_protegida_05": ("protegidas = [f for f in fs if cm.alerta_protegida(f)]",
                               "protegidas = [f for f in fs if cm.alerta_protegida(f, umbral=0.5)]"),
    "M6_sombra_carga_produccion": ("sombra = bp.cargar_nuestros(coords, inner, win, data=SOMBRA)",
                                   "sombra = bp.cargar_nuestros(coords, inner, win)"),
    "M7_negativos_con_sn": ('r.get("lab_original") == "neg_limpio"', 'r.get("lab") == "neg_limpio"'),
    "M8_sospecha_sin_hito": ("                      and minuto[:10] < aa.HITO_OCR_SUOMI_NPP\n", ""),
    "M9_diurna_lat_lon_cambiados": ("aa.es_pasada_diurna_descartada(b, ll[0], ll[1], dt)",
                                    "aa.es_pasada_diurna_descartada(b, ll[1], ll[0], dt)"),
    "M10_lectura_con_sin_geometria": ('if f.get("tipo") in cm.TIPOS_ALERTA and win[0]',
                                      'if (f.get("tipo") in cm.TIPOS_ALERTA or "SIN_GEOMETRIA" in (f.get("tipo") or "")) and win[0]'),
    "M11_historial_se_sobrescribe": ('"sombra_history.jsonl"), "a"', '"sombra_history.jsonl"), "w"'),
    "M12_prod_incluye_no_K": ('prod = [r for r in bp.cargar_nuestros(coords, inner, win) if r.get("sha")]',
                              "prod = list(bp.cargar_nuestros(coords, inner, win))"),
    "M13_reversion_con_produccion_sin_record": (
        'return [p for p in pasadas if p["sombra_pub"] is True and p["prod_pub"] is False]',
        'return [p for p in pasadas if p["sombra_pub"] is True and not p["prod_pub"]]'),
    # verificador 3 (N1 a N28)
    "N1_minimas_umbral_004": ('minimas = cm.aplicar_regla_minimas(filas, "SN").minimas',
                              'minimas = cm.aplicar_regla_minimas(filas, "SN", umbral_mw=0.04).minimas'),
    "N3_instante_sin_segundos": ('"instante_utc": dt.strftime("%Y-%m-%d %H:%M:%S")',
                                 '"instante_utc": dt.strftime("%Y-%m-%d %H:%M:00")'),
    "N5_negativos_desde_medianoche": ("corte_dt = _instante(adopcion) if adopcion else None",
                                      'corte_dt = _instante(adopcion[:10] + " 00:00:00") if adopcion else None'),
    "N6_frescura_borde_mayor_igual": ("if dias > MAX_DIAS_SOMBRA_SIN_DATOS:", "if dias >= MAX_DIAS_SOMBRA_SIN_DATOS:"),
    "N7_frescura_solo_volcanes_vistos": ("    for v in vols:\n        for s in sensores:",
                                         "    for v in sorted({k[0] for k in ultima}):\n        for s in sensores:"),
    "N9_muy_bajo_sin_exigir_record_sombra": (
        'if p["protegida"] or p["minima"] or p["prod_pub"] is None or p["sombra_pub"] is None:',
        'if p["protegida"] or p["minima"] or p["prod_pub"] is None:'),
    "N12_retro_persistencia_con_minimas": ('"persistencia": _persistencia([p for p in calla_retro if not p["minima"]])',
                                           '"persistencia": _persistencia(calla_retro)'),
    "N18_ciega_tapa_reversion": ('if veredicto == "VERDE" and avisos:', "if avisos:"),
    "N19_hoy_ayer": ("hoy = datetime.now(timezone.utc).date().isoformat()",
                     "hoy = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()"),
    "N22_tolerancia_61": ("TOL_S = cm.VENTANA_S", "TOL_S = 61"),
    "N23_sospecha_si_alguna_es_ocr": ('{f.get("source") for f in protegidas} == {"OCR"}',
                                      '"OCR" in {f.get("source") for f in protegidas}'),
    "N24_investigar_ignora_persistencia": ("elif persistencia or negativos", "elif negativos"),
    "N25_retro_incluye_corte": ('retro = [p for p in pasadas if p["instante_utc"] < corte]',
                                'retro = [p for p in pasadas if p["instante_utc"] <= corte]'),
    "N27_corte_sin_adopcion_es_cero": ('corte = adopcion or "9999-99-99 99:99:99"', 'corte = adopcion or "0000"'),
    "N28_wilson_z_164": ("def wilson(k, n, z=1.96):", "def wilson(k, n, z=1.64):"),
    # sobre los arreglos del verificador 3
    "sin_aviso_referencia": ("avisos = (avisos_referencia(filas, hoy) + avisos_sombra", "avisos = (avisos_sombra"),
    "sin_aviso_produccion": (" + avisos_produccion(prod, hoy)", ""),
    "frescura_ignora_sensor": ("            u = ultima.get((v, s))",
                               '            u = max([x for (vv, _), x in ultima.items() if vv == v], default="")'),
    "referencia_umbral_60": ("if dias > aa.MAX_GT_STALE_DAYS:", "if dias > 60:"),
    # decisiones de Nicolás del 2026-10-19
    "muy_bajo_con_minimas": ('if p["protegida"] or p["minima"] or p["prod_pub"] is None',
                             'if p["protegida"] or p["prod_pub"] is None'),
    "cota_muy_bajo_original": ('"muy_bajo": {"VIIRS375": {"V1_SE": (7, 161), "V2_SE": (12, 343)}}',
                               '"muy_bajo": {"VIIRS375": {"V1": (16, 194), "V2": (26, 388)}}'),
    "juzgadas_ignoradas": ("    juzgadas = juzgadas or {}\n", "    juzgadas = {}\n"),
    "evaluar_sin_juzgadas": ("d = disparadores(pasadas, prod, hoy, adopcion, juzgadas=leer_juzgadas())",
                             "d = disparadores(pasadas, prod, hoy, adopcion)"),
    # verificador 4 (Q)
    "Q_plazo_por_dia_de_corrida": ("        return bool(vence) and orden.get(_clave(p), 10 ** 9) <= PROTEGIDAS_OBJETIVO and p[\"instante_utc\"][:10] < vence",
                                   "        return not (vistas_pros and len(vistas_pros) >= PROTEGIDAS_OBJETIVO) and not (vence and hoy >= vence)"),
    "Q_borde_29_excluido": ("orden.get(_clave(p), 10 ** 9) <= PROTEGIDAS_OBJETIVO", "orden.get(_clave(p), 10 ** 9) < PROTEGIDAS_OBJETIVO"),
    "Q_duracion_cuenta_no_protegidas": ('vistas_pros = sorted((p for p in pros if p["protegida"] and p["sombra_pub"] is not None)',
                                        'vistas_pros = sorted((p for p in pros if p["sombra_pub"] is not None)'),
    "Q_fuera_sin_exigir_candidata": ("    elif fuera_de_plazo:\n", "    elif duracion[\"cumplida\"]:\n"),
    "Q_juzgada_sale_de_persistencia": ('persistencia = _persistencia([p for p in calla if not p["minima"]])',
                                       'persistencia = _persistencia([p for p in calla if not p["minima"] and _clave(p) not in juzgadas])'),
    "Q_juzgadas_sin_sensor": ('    return (p["volcano"], p["sensor"], p["fecha_utc"][:16])',
                              '    return (p["volcano"], "MODIS", p["fecha_utc"][:16])'),
    "Q_juzgadas_formato_laxo": ('or not re.fullmatch(r"\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}", p.get("fecha_utc") or "")):',
                                "or False):"),
    # workflow
    "WF_fuera_sin_issue": (WF, "            CANDIDATA_FUERA_DE_PLAZO)\n              abrir ", "            CANDIDATA_FUERA_DE_PLAZO)\n              echo "),
    "WF_fuera_mismo_prefijo": (WF, 'abrir "Sombra de K: candidata fuera de plazo"', 'abrir "Sombra de K: candidata"'),
    "WF_fuera_dice_preautoriza": (WF, "Fuera de plazo NO hay reversion pre-autorizada", "La regla pre-autoriza revertir"),
    "WF_issue_sin_always": (WF, "        if: always()\n", ""),
    "WF_sin_cron_respaldo": (WF, '    - cron: "40 23 * * *"\n', ""),
}
# Control del criterio (A110: un control se valida midiendo su nulo): esta mutación sólo hace caer el script con una
# excepción que no es una aserción. Si el criterio la cuenta como atrapada, el criterio está roto.
CONTROLES = {
    "CONTROL_solo_caida": (SCRIPT, "    adopcion = adopcion or leer_adopcion()\n    juzgadas = juzgadas or {}\n",
                           "    raise KeyError('control')\n"),
}
tests = ["tests/test_vigilancia_sombra_s156.py"]


def por_asercion(junit):
    """¿Alguna prueba falló por aserción? Lee el XML de JUnit: cada <failure> trae el mensaje de la excepción.
    (En modo -q el resumen -rf de pytest no imprime el motivo, así que no sirve para esto.)"""
    import xml.etree.ElementTree as ET
    for f in ET.parse(junit).getroot().iter("failure"):
        if re.match(r"(AssertionError|assert |Failed: DID NOT RAISE)", f.get("message") or ""):
            return True
    return False


atrapadas = 0
control_ok = None
try:
    for nombre, mut in list(CONTROLES.items()) + list(MUT.items()):
        archivo, a, b = mut if len(mut) == 3 else (SCRIPT, *mut)
        orig = originales[archivo]
        if orig.count(a) != 1:
            print(f"{nombre:40s} NO APLICA (cuenta {orig.count(a)})")
            continue
        (raiz / archivo).write_text(orig.replace(a, b), encoding="utf-8", newline="\n")
        junit = raiz / ".mutar_junit.xml"
        r = subprocess.run([sys.executable, "-m", "pytest", *tests, "-q", "--no-header", "-p", "no:cacheprovider",
                            f"--junitxml={junit}"], cwd=raiz, capture_output=True, text=True)
        (raiz / archivo).write_text(orig, encoding="utf-8", newline="\n")
        ult = (r.stdout.strip().splitlines() or [""])[-1]
        ok = r.returncode == 1 and junit.exists() and por_asercion(junit)
        junit.unlink(missing_ok=True)
        if nombre in CONTROLES:
            control_ok = (not ok) and r.returncode == 1
            print(f"{nombre:40s} {'CONTROL OK: cae y NO cuenta' if control_ok else 'CONTROL ROTO'}  | {ult}")
            continue
        atrapadas += ok
        print(f"{nombre:40s} {'ATRAPADA' if ok else 'NO ATRAPADA rc=%d' % r.returncode}  | {ult}")
finally:
    for f, t in originales.items():
        (raiz / f).write_text(t, encoding="utf-8", newline="\n")
print(f"\n{atrapadas} de {len(MUT)} atrapadas por fallo de prueba por aserción; control del criterio: "
      f"{'OK' if control_ok else 'ROTO'}")
