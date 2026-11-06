# -*- coding: utf-8 -*-
"""S162 V750-A: nulo de las pruebas `probar_evaluar_v750a.py` (al estilo de `_s162_v750b/mutar_bateria.py`).

POR QUÉ. Unas pruebas en verde no prueban nada si con la regla rota también salen en verde (A110). Se rompe a mano UNA
línea del analizador por vez y se corren las pruebas enteras contra esa copia: la mutación cuenta como ATRAPADA sólo si
las pruebas salen 1 por ASERCIÓN («== PRUEBAS: FALLAS») y ningún escenario se cayó con una excepción; si alguno se cayó,
es CAÍDA (S156: una mutación que sólo hace caer el programa no se cuenta como atrapada). Controles: IDENTIDAD (la copia
sin mutar tiene que salir 0, «TODOS LOS ESCENARIOS COMO SE ESPERA») y CAIDA (una mutación que sólo lanza una excepción
tiene que salir CAÍDA).

La copia mutada vive en esta misma carpeta con otro nombre (`_mut_<id>_evaluar_v750a.py`), así resuelve las mismas
rutas que el original, y se borra al terminar. Las corridas van en paralelo (cada una con su carpeta de destino).
M29 a M52 se agregaron tras el verificador limpio (VA-01 a VA-07): cada una rompe una regla que sus
roturas V01 a V41 mostraron sin vigilar. MR1 a MR7 (S173, VPR939-03, LECTURA LR1; ids MR porque la rama `claude/s162-viirs750-2-918174` ya usa M53 a M95) rompen el régimen de la sombra: el
filtro por ROI, la compuerta sin brazo, la marca SIN DATO, el corte por sha y el corte de cenit en 30°. MR9 a MR24 (S174,
VPR945, LECTURA LR2; la rama de V750-A ya usa MR8) rompen la segunda vuelta: la duración de 4 semanas y su reloj, el
volcán fuera del mapa de ROI, las 0 observadas, el sha resuelto de --sha-desde, y las seis roturas que el verificador
dejó vivas (MY2, MY3, MY4, MY10, MY12, MY15, MY16 de su mutar_propio.py). MR25 a MR42 (S174, VPR945-R2, LECTURA LR3)
rompen la tercera vuelta: las 14 noches, los bordes de 28,0 días y de 14 noches, --sha-desde obligatorio, la compuerta de
otra ROI posterior al corte, la ventana desde el 2026-11-03 y desde la hora del commit (la del committer), el piso de 7
caracteres, la salida 5 del PROVISORIO con faltantes y el corte de las pasadas sin gránulo (MZ1, MZ4, MZ5, MZ6 y MZ7 del
verificador quedan en MR27, MR36, MR37, MR29 y MR39). MR2, MR4, MR9, MR10 y MR19 cambiaron de blanco porque el código
que rompían cambió (MR10 rompe ahora la ventana desde la hora del corte, que reemplazó al reloj desde el corte).
Uso: python mutar_evaluar_v750a.py --dest <tmp> --evaluador <evaluar_d25.py del tag> [--hilos 4]
Salida: 0 si los controles salen como deben y todas las mutaciones quedan ATRAPADAS; 1 si no.
"""
import argparse
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ORIGINAL = AQUI / "evaluar_v750a.py"
PRUEBAS = AQUI / "probar_evaluar_v750a.py"
ESCENARIOS_SOLO = ""   # S173: --escenarios

MUTACIONES = {
    "M1": ("§6.2: una protegida perdida (P1) ya no entra a los motivos",
           "motivos.append(f\"P1 {m['P1']}\")", "pass"),
    "M2": ("§6.2 (L1): P1 cuenta también las protegidas que K tampoco publica",
           'if e == "prot" and not pb and pub(i, "K"):', 'if e == "prot" and not pb:'),
    "M3": ("§6.2 (L3): P2 SIN SUSTRATO pasa",
           'if reg not in ("GANA", "EMPATE"):', 'if reg not in ("GANA", "EMPATE", "SIN SUSTRATO"):'),
    "M4": ("§6.2: P2 BLOQUEA pasa",
           'if reg not in ("GANA", "EMPATE"):', 'if reg not in ("GANA", "EMPATE", "BLOQUEA"):'),
    "M5": ("§6.2: la razón de M sin la banda 0,9 a 1,1",
           "if rz is None or not (BANDA_RAZON[0] <= rz <= BANDA_RAZON[1]):", "if rz is None:"),
    "M6": ("§5: M sin el comparador d′ (D-28)",
           'return EM.decidir_estrato(P_, "decide", "simetrica", True, comparador=comparador)',
           'return EM.decidir_estrato(P_, "decide", "simetrica", True, comparador=False)'),
    "M7": ("§6.2: M NEUTRO pasa",
           'if rm != "MEJORA":', 'if rm not in ("MEJORA", "NEUTRO"):'),
    "M8": ("§6 (L10): «informar por canal» sin mirar que la falla sea de la ventana O",
           'elif all(v == "O" and x.startswith("P2") for v, _c, x in fallas):',
           'elif all(x.startswith("P2") for v, _c, x in fallas):'),
    "M9": ("§4.1: tolerancia de VRP de 1e-1 MW en vez de 1e-6",
           "TOL_VRP_EQUIV = 1e-6", "TOL_VRP_EQUIV = 1e-1"),
    "M10": ("§4.1: la banda de triangulación se ignora",
            '(banda if res[i].get("banda_triangulacion") else dist).append(i)', "dist.append(i)"),
    "M11": ("§6.1 (L2): la prueba local no exige «mutaciones: TODAS COMO SE ESPERA»",
            "ok = verde and todas and n_atr >= MIN_MUT_LOCAL and caida", "ok = verde and n_atr >= MIN_MUT_LOCAL and caida"),
    "M12": ("§6.1: sólo el runner decide (la prueba local deja de bloquear)",
            "if dist or not local_ok:", "if dist:"),
    "M13": ("§7 (L6): el control positivo de la ROI siempre pasa",
            'ctrl["positivo de la ROI"] = len(roi) >= 1', 'ctrl["positivo de la ROI"] = True'),
    "M14": ("§7 (L8): el nulo K contra K acepta P2 PIERDE",
            'ctrl["nulo K contra K gemelo"] = g_reg in ("EMPATE", "SIN SUSTRATO") and',
            'ctrl["nulo K contra K gemelo"] = g_reg in ("EMPATE", "SIN SUSTRATO", "PIERDE") and'),
    "M15": ("§7: K = producción siempre pasa",
            "k_ok = not k_dist ", "k_ok = True "),
    "M16": ("cobertura: el archivo de pasadas sin gránulo se acepta sin comprobar que sea de esta lista",
            "cob_ok = sg_ok and len(sin) + len(sin_g)", "cob_ok = len(sin) + len(sin_g)"),
    "M17": ("compuerta: con controles caídos igual se lee el veredicto",
            "if a.solo_controles or not todo_ok:", "if a.solo_controles:"),
    "M18": ("la marca «LEÍDO CON FALTANTES» no se escribe en la línea del veredicto",
            'pr(ver + (" " + aviso if aviso else ""))', "pr(ver)"),
    "M19": ("§6.3 (L3): en la sombra BLOQUEA también falla",
            'if reg == "PIERDE":', 'if reg in ("PIERDE", "BLOQUEA"):'),
    "M20": ("§6.3: una protegida perdida en la sombra ya no entra a los motivos",
            "motivos.append(f\"{canal}: P1 {m['P1']}\")", "pass"),
    "M21": ("S-1 (L12): «decidida por la escena» pasa a ser «cambió la celda decisiva»",
            "return alerta_celda(dA, dA) != alerta_celda(dA, dB) or alerta_celda(dB, dB) != alerta_celda(dB, dA)",
            "return alerta_celda(dA, dA) != alerta_celda(dB, dB)"),
    "M22": ("S-1 (L12): el umbral de la celda es siempre u1, sin mirar la zona",
            'return dg[f"pasada{pase}"][f"u_{x}{2 if zona == 2 else 1}"]', 'return dg[f"pasada{pase}"][f"u_{x}1"]'),
    "M23": ("S-1 (a): el cambio de sd se mide del brazo B contra sí mismo",
            'dB[f"pasada{p}"][f"sd_{x}"] - dA[f"pasada{p}"][f"sd_{x}"]',
            'dB[f"pasada{p}"][f"sd_{x}"] - dB[f"pasada{p}"][f"sd_{x}"]'),
    "M24": ("etiquetas: con la tabla sola también cuentan las alertas sólo del OCR",
            'if canal == "tabla" and not o.get("alerta_tabla"):', "if False:"),
    "M25": ("P2: las alertas bajo 1 MW sin publicar dejan de ser error",
            'err = lambda x: int((e == "baja" and not pub(i, x)) or (e == "neg" and pub(i, x)))',
            'err = lambda x: int(e == "neg" and pub(i, x))'),
    "M26": ("§4.1 (L13): la máscara no se compara, sólo el VRP",
            "if mp != mo or abs(", "if abs("),
    "M27": ("S-1: la protegida decidida por la escena no llega a la línea del veredicto",
            "s1_prot.add(nombre(i))", "pass"),
    "M28": ("P-sinfiltro (L11, informa): la distancia no se neutraliza",
            'r["distance_class"] = "summit"', "pass"),
    "M29": ("§7 (L18): K = producción sólo mira las protegidas",
            "k_ok = not k_dist ", 'k_ok = not [i for i in k_dist if obj[i].get("protegida")] '),
    "M30": ("§7: el VRP de K contra producción con tolerancia de 1000 MW",
            'abs((vrp(i, "K") or 0) - (obj[i].get("pc_vrp") or 0)) > 0.001',
            'abs((vrp(i, "K") or 0) - (obj[i].get("pc_vrp") or 0)) > 1000'),
    "M31": ("§6.2: piso de la banda de M en 0,5", "BANDA_RAZON = (0.9, 1.1)", "BANDA_RAZON = (0.5, 1.1)"),
    "M32": ("§6.2: techo de la banda de M en 1,25", "BANDA_RAZON = (0.9, 1.1)", "BANDA_RAZON = (0.9, 1.25)"),
    "M33": ("cobertura: las pasadas sin gránulo del generador no cuentan",
            "len(sin) + len(sin_g) <= AB.MAX_SIN_DATO", "len(sin) <= AB.MAX_SIN_DATO"),
    "M34": ("cobertura: una protegida SIN DATO ya no frena sola",
            "<= AB.MAX_SIN_DATO * den_cob and not prot_sin", "<= AB.MAX_SIN_DATO * den_cob"),
    "M35": ("cobertura: la pasada diurna deja de ser SIN DATO",
            'elif part[i] == "observada" and r.get("dayflag") != 0:', "elif False:"),
    "M36": ("§6.1 (L2): sin mínimo de mutaciones atrapadas en la prueba local",
            "ok = verde and todas and n_atr >= MIN_MUT_LOCAL and caida", "ok = verde and todas and caida"),
    "M37": ("§6.1 (L2): sin exigir el control caído de la prueba local",
            "ok = verde and todas and n_atr >= MIN_MUT_LOCAL and caida", "ok = verde and todas and n_atr >= MIN_MUT_LOCAL"),
    "M38": ("§6.1 (L2): la línea VERDE sin los casos del §4.1",
            "verde = (any(c[0] >= MIN_CASOS_LOCAL[0] and c[1] >= MIN_CASOS_LOCAL[1] for c in casos)",
            "verde = (bool(casos)"),
    "M39": ("--solo-controles se ignora", "if a.solo_controles or not todo_ok:", "if not todo_ok:"),
    "M40": ("P2: el bloque pierde el volcán (sólo la noche)",
            'sumas[(o["hora_utc"][:10], o["volcan"])] += c', 'sumas[o["hora_utc"][:10]] += c'),
    "M41": ("M sin el piso de sustrato (5 pares, 3 noches)",
            'if len(P_) < EM.N_MIN_PARES or len({p["bloque"] for p in P_}) < EM.N_MIN_NOCHES:', "if not P_:"),
    "M42": ("etiquetas: se ignora el flag `decide`",
            'if o["lab"] != "pos" or not o.get("decide"):', 'if o["lab"] != "pos":'),
    "M43": ("§7 (L8): el nulo K contra K acepta M MEJORA o EMPEORA",
            'and g_m in ("NEUTRO", "SIN SUSTRATO")', 'and g_m in ("NEUTRO", "SIN SUSTRATO", "MEJORA", "EMPEORA")'),
    "M44": ("§6.3: en la sombra P1 se mide sólo con la tabla (la versión anterior de esta mutación sólo hacía caer el "
            "programa: regs['todo'] quedaba sin definir)",
            'm, nadie = metricas("P", "TODO", canal)', 'm, nadie = metricas("P", "TODO", "tabla")'),
    "M45": ("§6.2: la razón de M se exige sólo en la ventana O",
            "if rz is None or not (BANDA_RAZON[0] <= rz <= BANDA_RAZON[1]):",
            'if v == "O" and (rz is None or not (BANDA_RAZON[0] <= rz <= BANDA_RAZON[1])):'),
    "M46": ("S-1 (L12): el umbral de la celda es siempre el del pase 1",
            'return dg[f"pasada{pase}"][f"u_{x}{2 if zona == 2 else 1}"]',
            'return dg["pasada1"][f"u_{x}{2 if zona == 2 else 1}"]'),
    "M47": ("S-1 (L12): la celda alerta con el NTI solo",
            'return all(cd[f"c_{x}"] > _u(dg_umbral, cd["pase"], cd["zona"], x) for x in ("nti", "eti"))',
            'return all(cd[f"c_{x}"] > _u(dg_umbral, cd["pase"], cd["zona"], x) for x in ("nti",))'),
    "M48": ("S-1: sin el par (P-def, O)",
            'PARES_S1 = (("P", "Pdef"), ("P", "O"), ("Pdef", "O"))', 'PARES_S1 = (("P", "Pdef"), ("P", "O"))'),
    "M49": ("§6.1 (L12): la marca «decidida por la escena» nunca sale en la equivalencia",
            "if decidida_por_escena(dP, dO) else \"\")", "if False else \"\")"),
    "M50": ("§7 (L7): el control de publicación del placebo siempre pasa",
            'ctrl["placebo (publicación)"] = not pl_dist', 'ctrl["placebo (publicación)"] = True'),
    "M51": ("§6.3 (L19): la sombra sin protegidas no lo dice",
            '+ ("; SIN PROTEGIDAS: P1 no pudo vetar" if not n_prot else "")', '+ ""'),
    "M52": ("§6.2 (L4): la razón de M no exige que K publique",
            'and (pub(i, "K") and vrp(i, "K") > 0 or not exigir_k)', "and (True or not exigir_k)"),
    "MR1": ("sombra (LR1): el filtro por ROI no saca ninguna pasada (lo de antes de S173)",
            'if roi != esperada.get(obj[i]["volcan"]):', "if False:"),
    "MR2": ("sombra (LR1): sin --roi-brazo no se cierra la compuerta y se lee como B0",
            '            return salir(3)\n        if not a.sha_desde:\n',
            '            a.roi_brazo = "B0"\n        if not a.sha_desde:\n'),
    "MR3": ("sombra (LR1): una pasada sin régimen no es SIN DATO y entra a la lectura",
            "            motivo_sin[i] = sin_regimen[i]", "            pass"),
    "MR4": ("sombra (LR1): --sha-desde no corta nada",
            "            elif corte:", "            elif False:"),
    "MR5": ("sombra (LR1): un sha que git no conoce entra a la lectura",
            '                    sin_regimen[i] = "sha_desconocido"', "                    pass"),
    "MR6": ("sombra (§12.8 punto 2): el corte de cenit en 40° y no en 30°",
            '(("bajo 30°", lambda z: z < 30), ("sobre 30°", lambda z: z >= 30))',
            '(("bajo 30°", lambda z: z < 40), ("sobre 30°", lambda z: z >= 40))'),
    "MR7": ("sombra (§12.8 punto 2): el borde de 30° va abajo",
            '(("bajo 30°", lambda z: z < 30), ("sobre 30°", lambda z: z >= 30))',
            '(("bajo 30°", lambda z: z <= 30), ("sobre 30°", lambda z: z > 30))'),
    # S174, VPR945 (segunda vuelta del PR #945)
    "MR9": ("sombra (§4.3, LR2): la duración de 4 semanas no se exige",
            "dias_ok = dias >= DIAS_MIN_SOMBRA", "dias_ok = True"),
    "MR10": ("sombra (LR2, LR3): con --sha-desde la ventana (y el reloj) no parte de la hora del commit del corte",
             "ventana_desde = max(INICIO_SOMBRA, fecha_corte)", "ventana_desde = INICIO_SOMBRA"),
    "MR11": ("sombra (LR2): el reloj cuenta también las pasadas no observadas y las SIN DATO",
             'horas = sorted(obj[i]["hora_utc"] for i in oks0) or', 'horas = sorted(obj[i]["hora_utc"] for i in obj) or'),
    "MR12": ("sombra (VPR945-02): un volcán fuera del mapa de ROI vuelve a salir como «otra ROI»",
             '            if obj[i]["volcan"] not in esperada:', "            if False:"),
    "MR13": ("VPR945-03: con 0 observadas no hay mensaje propio (dice SUFICIENTE y cae el nulo)",
             "    if not oks0:\n", "    if False:\n"),
    "MR14": ("VPR945-04: --sha-desde acepta una referencia móvil (HEAD) mientras git la resuelva",
             "return sha if o.returncode == 0 and len(x) >= 7 and sha.startswith(x) else \"\"",
             "return sha if o.returncode == 0 else \"\""),
    "MR15": ("VPR945-04: la salida lleva lo tecleado en --sha-desde y no el sha resuelto",
             '(f", desde {corte} (commit del', '(f", desde {a.sha_desde} (commit del'),
    "MR16": ("VPR945-06 (MY2): sólo se exige la ROI; un record sin sha entra a la lectura",
             "if not roi or not sha:", "if not roi:"),
    "MR17": ("VPR945-06 (MY3): sólo se exige el sha; un record sin ROI no es SIN DATO",
             "if not roi or not sha:", "if not sha:"),
    "MR18": ("VPR945-05 (MY10): la lista de protegidas que salen de la lectura sale siempre «ninguna»",
             'for i, m in fuera_regimen.items() if obj[i].get("protegida")] or "ninguna")',
             'for i, m in fuera_regimen.items() if False] or "ninguna")'),
    "MR19": ("VPR945-07 (MY4): un --sha-desde que no resuelve no cierra con su mensaje y se usa lo tecleado "
             "(R2: con el corte obligatorio, saltarse la compuerta sin más hacía caer el programa)",
             "        if not corte:\n",
             "        if not corte:\n            corte = a.sha_desde\n        if False:\n"),
    "MR20": ("VPR945-07 (MY12): el conteo «dentro» incluye las SIN DATO del régimen",
             "dentro = sum(1 for i in reg if i not in fuera_regimen and i not in sin_regimen and i not in sin_mapa)",
             "dentro = sum(1 for i in reg if i not in fuera_regimen and i not in sin_mapa)"),
    "MR21": ("VPR945-07 (MY15): el cenit decide: una protegida sobre 30° que P pierde cierra la compuerta",
             '        sin_z = [i for i in oks0 if obj[i].get("z") is None]\n',
             '        sin_z = [i for i in oks0 if obj[i].get("z") is None]\n'
             '        if any(etiqueta(obj[i], "decide") == "prot" and pub(i, "K") and not pub(i, "P") and '
             'obj[i].get("z", 0) >= 30 for i in oks0):\n            ctrl["cenit"] = False\n'),
    "MR22": ("sombra (LR2): antes de las 4 semanas un P1 tampoco veta (espera la duración)",
             "if motivos and (dur_ok or p1_veta):", "if motivos and dur_ok:"),
    "MR23": ("sombra (LR2): antes de las 4 semanas un P2 PIERDE ya es NO CUMPLE",
             "if motivos and (dur_ok or p1_veta):", "if motivos:"),
    "MR24": ("VPR945-07 (MY16): el régimen se lee también en las pasadas no observadas",
             '            if AB.partida(r) != "observada":\n                continue\n', "            pass\n"),
    # S174, VPR945-R2 (tercera vuelta del PR #945, LECTURA LR3)
    "MR25": ("R2-01: las 14 noches distintas no se exigen", "noches_ok = noches >= NOCHES_MIN_SOMBRA",
             "noches_ok = True"),
    "MR26": ("R2-04: con 14 noches justas no alcanza (el borde va arriba)", "noches_ok = noches >= NOCHES_MIN_SOMBRA",
             "noches_ok = noches > NOCHES_MIN_SOMBRA"),
    "MR27": ("R2-04 (MZ1): con 28,0 días justos no alcanza (el borde va arriba)", "dias_ok = dias >= DIAS_MIN_SOMBRA",
             "dias_ok = dias > DIAS_MIN_SOMBRA"),
    "MR28": ("R2-01: se cuentan pasadas y no noches", "noches = len({h[:10] for h in horas}) if oks0 else 0",
             "noches = len(horas) if oks0 else 0"),
    "MR29": ("R2-01 (MZ6): la noche es el mes", "noches = len({h[:10] for h in horas}) if oks0 else 0",
             "noches = len({h[:7] for h in horas}) if oks0 else 0"),
    "MR30": ("R2-02: sin --sha-desde no se cierra con su mensaje", "        if not a.sha_desde:\n",
             "        if False:\n"),
    "MR31": ("R2-02: una pasada de otra ROI con código posterior al corte no cierra la compuerta",
             "        if roi_cambia:\n", "        if False:\n"),
    "MR32": ("R2-02: una pasada de otra ROI con sha desconocido no cierra la compuerta",
             "es_ancestro(corte, reg[i][1]) is not False", "es_ancestro(corte, reg[i][1]) is True"),
    "MR33": ("R2-02: la compuerta de otra ROI mira también las pasadas de antes de la ventana",
             'and obj[i]["hora_utc"] >= ventana_desde and es_ancestro', "and es_ancestro"),
    "MR34": ("R2-03: sin cota inferior del 2026-11-03", "ventana_desde = max(INICIO_SOMBRA, fecha_corte)",
             "ventana_desde = fecha_corte"),
    "MR35": ("R2-03: la ventana no saca ninguna pasada",
             '            if i not in fuera_regimen and obj[i]["hora_utc"] < ventana_desde:', "            if False:"),
    "MR36": ("R2-04 (MZ4): la hora del corte es la del autor, no la del committer", '"--format=%ct"', '"--format=%at"'),
    "MR37": ("R2-04 (MZ5): --sha-desde acepta 4 caracteres", "len(x) >= 7", "len(x) >= 4"),
    "MR38": ("R2-04: --sha-desde exige 8 caracteres", "len(x) >= 7", "len(x) >= 8"),
    "MR39": ("R2-04 (MZ7): un PROVISORIO leído con faltantes sale 4 y no 5", "rc_final = rc_final or 4", "rc_final = 4"),
    "MR40": ("R2-03: las pasadas sin gránulo no se cortan con la ventana",
             '        sin_g = [x for x in sin_g if not x.get("hora_utc") or x["hora_utc"] >= ventana_desde]',
             "        pass"),
    "MR41": ("R2-01: CUMPLE con los días o con las noches (basta una)", "dur_ok = dias_ok and noches_ok",
             "dur_ok = dias_ok or noches_ok"),
    "MR42": ("R2-04: los días se redondean (27,99 se lee 28,0)", 'dias_txt = f"{math.floor(dias * 10) / 10:.1f}"',
             'dias_txt = f"{dias:.1f}"'),
    "CAIDA": ("CONTROL: el analizador sólo se cae (excepción al cargar los objetivos)",
              'obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8"))}',
              'raise RuntimeError("mutación de control: el programa se cae")'),
}


def correr(dest, evaluador, nombre, viejo=None, nuevo=None):
    copia = AQUI / f"_mut_{nombre}_evaluar_v750a.py"
    src = ORIGINAL.read_text(encoding="utf-8")
    if viejo is not None:
        assert src.count(viejo) == 1, (nombre, "la línea a mutar aparece", src.count(viejo), "veces")
        src = src.replace(viejo, nuevo)
    copia.write_text(src, encoding="utf-8")
    sal = dest / f"pruebas_{nombre}"
    if sal.exists():
        shutil.rmtree(sal)
    try:
        o = subprocess.run([sys.executable, str(PRUEBAS), "--dest", str(sal), "--analizador", str(copia),
                            "--evaluador", str(evaluador)] + (["--solo", ESCENARIOS_SOLO] if ESCENARIOS_SOLO else []),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=7200, cwd=str(AQUI))
    finally:
        copia.unlink()
    txt = o.stdout + o.stderr
    linea = next((x for x in txt.splitlines() if x.startswith("== PRUEBAS")), "(sin línea de pruebas)")
    atrapan = [x.split(" | ")[0] for x in txt.splitlines() if " | FALLA" in x]
    if o.returncode == 0 and "TODOS LOS ESCENARIOS COMO SE ESPERA" in linea:
        estado = "PASA"
    elif o.returncode == 1 and "FALLAS" in linea:
        estado = "ATRAPADA"
    else:
        estado = "CAÍDA"
    return nombre, estado, o.returncode, linea, atrapan


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--evaluador", required=True, type=Path)
    ap.add_argument("--hilos", type=int, default=4)
    ap.add_argument("--solo", default="", help="ids de mutaciones a correr (IDENTIDAD y CAIDA van siempre)")
    ap.add_argument("--escenarios", default="",
                    help="S173: escenarios de las pruebas a correr (--solo de probar_evaluar_v750a.py); sólo para "
                         "mutaciones de un camino que el resto no recorre (la sombra), y se dice en la salida")
    a = ap.parse_args()
    sel = {x for x in a.solo.split(",") if x}
    a.dest.mkdir(parents=True, exist_ok=True)
    mut = {k: v for k, v in MUTACIONES.items() if not sel or k in sel or k == "CAIDA"}
    trabajos = [("IDENTIDAD", None, None)] + [(k, v[1], v[2]) for k, v in mut.items()]
    global ESCENARIOS_SOLO
    ESCENARIOS_SOLO = a.escenarios
    with ThreadPoolExecutor(a.hilos) as ex:
        res = {r[0]: r for r in ex.map(lambda t: correr(a.dest, a.evaluador, *t), trabajos)}
    L = []

    def pr(s):
        print(s, flush=True)
        L.append(s)

    ident = res["IDENTIDAD"]
    if sel:
        pr(f"(corrida parcial: --solo {a.solo})")
    if a.escenarios:
        pr(f"(escenarios parciales: --escenarios {a.escenarios})")
    pr(f"IDENTIDAD | {ident[1]} (tiene que ser PASA) | rc {ident[2]} | {ident[3][:200]}")
    malos = 0 if ident[1] == "PASA" else 1
    for nom, (que, _v, _n) in mut.items():
        _, est, rc, linea, atrapan = res[nom]
        esperado = "CAÍDA" if nom == "CAIDA" else "ATRAPADA"
        malos += est != esperado
        pr(f"{nom} | {est} (tiene que ser {esperado}) | rc {rc} | {que} | {linea[:120]} | escenarios que fallan "
           f"{atrapan}")
    n_mut = len(mut) - 1
    atr = sum(1 for k in mut if k != "CAIDA" and res[k][1] == "ATRAPADA")
    ctrl = ident[1] == "PASA" and res["CAIDA"][1] == "CAÍDA"
    pr(f"== RESUMEN: {atr} de {n_mut} mutaciones atrapadas por aserción; controles "
       f"{'como deben' if ctrl else 'FALLAN'}; {'TODO COMO SE ESPERA' if malos == 0 else f'{malos} FUERA DE LO ESPERADO'}")
    (a.dest / "mutar_evaluar_v750a_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 0 if malos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
