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
roturas V01 a V41 mostraron sin vigilar. M53 a M56 (y M15, M29, M50, M52 reescritas) son de la resolución de L2, L4, L7
y L18 por D-48 (relevo VIIRS 750, 2026-10-25). La antigua M50 («el placebo de publicación siempre pasa») ya no se puede
atrapar: con el predicado de hoy toda diferencia K contra K×1,2 tiene t_max frío y se explica (A116, LECTURAS).
M63 a M80 son de los brazos de posición (§3 y §6 bis, decisión de Nicolás del 2026-10-27). M81 a M85, del verificador limpio de
esos brazos (verificador_posicion/INFORME.md: MV2, MV3, MV9, MV10 y el arreglo de VP-01).
MR1 a MR7 (S173, VPR939-03, LECTURA LR1; ids MR porque la rama `claude/s162-viirs750-2-918174` ya usa M53 a M95) rompen el régimen de la sombra: el
filtro por ROI, la compuerta sin brazo, la marca SIN DATO, el corte por sha y el corte de cenit en 30°. MR9 a MR24 (S174,
VPR945, LECTURA LR2; la rama de V750-A ya usa MR8) rompen la segunda vuelta: la duración de 4 semanas y su reloj, el
volcán fuera del mapa de ROI, las 0 observadas, el sha resuelto de --sha-desde, y las seis roturas que el verificador
dejó vivas (MY2, MY3, MY4, MY10, MY12, MY15, MY16 de su mutar_propio.py). MR25 a MR42 (S174, VPR945-R2, LECTURA LR3)
rompen la tercera vuelta: las 14 noches, los bordes de 28,0 días y de 14 noches, --sha-desde obligatorio, la compuerta de
otra ROI posterior al corte, la ventana desde el 2026-11-03 y desde la hora del commit (la del committer), el piso de 7
caracteres, la salida 5 del PROVISORIO con faltantes y el corte de las pasadas sin gránulo (MZ1, MZ4, MZ5, MZ6 y MZ7 del
verificador quedan en MR27, MR36, MR37, MR29 y MR39). MR2, MR4, MR9, MR10 y MR19 cambiaron de blanco porque el código
que rompían cambió (MR10 rompe ahora la ventana desde la hora del corte, que reemplazó al reloj desde el corte).
MR43 a MR50 (S174, VPR945-R3, LECTURA LR3) rompen la cuarta vuelta: las noches por volcán de ROI cambiada (también con 0
pasadas), el reparto de 7 y 7 por mitad del lapso en el conjunto y por volcán, el borde de la mitad, el minuto exacto del
corte en la ventana y en la compuerta (MV1 y MV2 del verificador quedan en MR48 y MR49) y la línea por volcán con los 0.
MR25, MR26, MR28 y MR29 cambiaron de blanco: la regla de las noches pasó a reparto_noches.
MR51 a MR63 (S174, VPR945-R4, quinta vuelta: ventana fija, LECTURA LR3) rompen la ventana fija: el borde de la semana,
el umbral de 5 noches por semana (abajo y arriba), el fin sin incluir, las cotas del fin y de «ahora», la compuerta de
otra ROI sólo dentro de lo que se lee, la exigencia por semana en los volcanes sin cambio, la cota superior de las
pasadas sin gránulo, las noches por volcán sobre las pasadas leídas y los días de calendario hasta min(ahora, fin).
Con la ventana fija cambiaron de blanco MR9 y MR27 («ahora» llega al fin), MR11, MR25, MR26, MR28, MR29, MR40, MR41,
MR44, MR45, MR46 y MR50; MR47 (la noche de la mitad del lapso) se retiró con el reparto por mitades. La regla de las 14
noches no tiene mutación propia: con 5 por semana el total es 20 o más y una rotura de esa sola condición sobrevive por
construcción (dicho en voz alta, A116).
MR28 y MR29 cambiaron de blanco en la sexta vuelta (la noche se cuenta en semana_de).
MR64 a MR71 (S174, VPR945-R5, sexta vuelta; decisión de Nicolás del 2026-11-06, LECTURA LR3) rompen: las 14 noches de
cada volcán sin cambio de ROI (abajo, arriba y sin la regla), la noche contada una sola vez en la semana de su primera
pasada (contada en todas, o en la de la última), la conversión de una zona distinta de UTC en --ahora, el reloj UTC
cuando no se da --ahora (MX11 del verificador) y la pasada en el minuto exacto de «ahora» (MX13). La regla de 14 de los
volcanes cambiados sigue sin mutación propia (R5-05: redundante con 5 por semana, A116). Con la noche contada una sola
vez, la mutación MX9 del verificador (total = suma de las semanas) pasa a ser equivalente.
MR72 a MR75 (S174, VPR945-R6, retoques tras el merge de #945, sin cambio de regla) rompen: la regla de 14 noches de los
volcanes sin cambio cuando se lee con B0 (apagada si ningún volcán cambia, o con la lista vacía; MY7 y MY8 del
verificador, que sobrevivían a todo), la captura del OverflowError de --ahora (R6-01) y la conversión a la zona local en
vez de a UTC (MY10; R6-03: ER45 corre con TZ en UTC+12, así que cae también con TZ=UTC en el proceso padre).
MR76 a MR79 (S174, VPR953, seguimiento del verificador de #953, sin cambio de regla) rompen la regla de 14 noches de los
volcanes sin cambio en un volcán que no es el primero (X12 a X14 del verificador: sólo el primero, sin el último, sin el
segundo; ER56) y la lista de la línea CUMPLE recortada a dos volcanes (X15; ER55 exige ahora los once).
VPR953-01: una mutación atrapada SÓLO porque un escenario con la bandera «no se cae» (no_traceback) vio un Traceback se
rotula aparte, «sólo por la bandera "no se cae"», en su línea y en el RESUMEN (MR74 es la única hoy): la bandera es la
aserción natural de ese defecto, pero no es una aserción sobre la salida del lector.
MR8 (S173, sólo en la rama de V750-A hasta S175) rompe la lista de protegidas que salen por otra ROI.
Reconciliación S175: M91 («N-3 llega a la sombra») cambió de blanco. El de antes (metricas con n3=True en §6.3) es
equivalente desde la ventana fija: la sombra no lee nada anterior al 2026-11-03 y la clase N-3 es anterior al
2026-10-09, así que es_n3 nunca es cierta ahí (§6 ter lo anticipa; tests/test_bateria_lector_v750a_s174.py fija
FRONTERA_N3 < INICIO_SOMBRA). El blanco de hoy es el único camino por el que esa clase puede entrar: la ventana.
M52 queda la de la rama (L4 por D-48 cambió el sentido de exigir_k); la de main rompía la lectura anterior.
--escenarios (S162, brazos de posición) restringe la batería a los escenarios nombrados, en IDENTIDAD, CAIDA y cada
mutación. Sirve para medir rápido las mutaciones de una pieza nueva contra los escenarios que la fijan (la batería entera
tarda unos 40 min por corrida con un hilo); una mutación ATRAPADA así cae por aserción EN ESOS escenarios, pero no
descarta que se caiga en otro, así que no reemplaza la corrida sin --escenarios, que es la que cuenta para el §6.
Uso: python mutar_evaluar_v750a.py --dest <tmp> --evaluador <evaluar_d25.py del tag> [--hilos 4] [--solo M1,M2]
     [--escenarios E61,E62]
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
# VPR953-01: el texto con que probar_evaluar_v750a.py marca la falla de un escenario con no_traceback=True
BANDERA = "y el escenario afirma que no se cae"

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
            "ok = verde and todas and n_atr >= MIN_MUT_LOCAL and len(nombradas) == len(MUT_LOCAL) and caida", "ok = verde and n_atr >= MIN_MUT_LOCAL and len(nombradas) == len(MUT_LOCAL) and caida"),
    "M12": ("§6.1: sólo el runner decide (la prueba local deja de bloquear)",
            "if dist or not local_ok:", "if dist:"),
    "M13": ("§7 (L6): el control positivo de la ROI siempre pasa",
            'ctrl["positivo de la ROI"] = len(roi) >= 1', 'ctrl["positivo de la ROI"] = True'),
    "M14": ("§7 (L8): el nulo K contra K acepta P2 PIERDE",
            'ctrl["nulo K contra K gemelo"] = g_reg in ("EMPATE", "SIN SUSTRATO") and',
            'ctrl["nulo K contra K gemelo"] = g_reg in ("EMPATE", "SIN SUSTRATO", "PIERDE") and'),
    "M15": ("§7: K = producción siempre pasa",
            "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO", "k_ok = True or len(k_dist) <= AB.MAX_K_DISTINTO"),
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
    "M29": ("§7 (L18): K = producción sólo mira las protegidas (sin el tope del 1 %)",
            "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0)) and not k_dist_prot", "k_ok = not k_dist_prot"),
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
            "ok = verde and todas and n_atr >= MIN_MUT_LOCAL and len(nombradas) == len(MUT_LOCAL) and caida", "ok = verde and todas and caida"),
    "M37": ("§6.1 (L2): sin exigir el control caído de la prueba local",
            "ok = verde and todas and n_atr >= MIN_MUT_LOCAL and len(nombradas) == len(MUT_LOCAL) and caida", "ok = verde and todas and n_atr >= MIN_MUT_LOCAL and len(nombradas) == len(MUT_LOCAL)"),
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
    "M50": ("§7 (L7): ninguna diferencia del placebo se explica por los filtros (todas cierran)",
            '.get("t_max_k") or 1e9) < TMAX_FILTROS_ARTEFACTO\n', '.get("t_max_k") or 1e9) < 0\n'),
    "M51": ("§6.3 (L19): la sombra sin protegidas no lo dice",
            '+ ("; SIN PROTEGIDAS: P1 no pudo vetar" if not n_prot else "")', '+ ""'),
    "M52": ("§6.2 (L4 por D-48): la razón de M exige que K publique",
            "def razon_prot(b, v, canal, exigir_k=False):", "def razon_prot(b, v, canal, exigir_k=True):"),
    "M53": ("§7 (L18): una protegida con K distinto ya no cierra si cabe en el 1 %",
            "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0)) and not k_dist_prot", "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0))"),
    "M54": ("§7 (L18): las pasadas con K distinto no salen de los brazos",
            "oks = [i for i in oks0 if i not in set(k_dist)]", "oks = list(oks0)"),
    "M55": ("§7 (L18): tolerancia de K = producción en 5 % en vez de 1 %",
            "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max", "k_ok = len(k_dist) <= 0.05 * max"),
    "M56": ("§6.1 (L2 por D-48): mínimo de 5 mutaciones atrapadas en vez de 6",
            "MIN_MUT_LOCAL = 6 ", "MIN_MUT_LOCAL = 5 "),
    # tras la segunda vuelta del verificador (verificador_v2/INFORME.md, VB-A01 a VB-A06; sus roturas R1 a R6)
    "M57": ("§6.2 (VB-A03): los bordes de la banda de M quedan fuera",
            "BANDA_RAZON[0] <= rz <= BANDA_RAZON[1]", "BANDA_RAZON[0] < rz < BANDA_RAZON[1]"),
    "M58": ("§7 (VB-A04): K = producción apagado en la sombra",
            "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO", "k_ok = (not censo) or len(k_dist) <= AB.MAX_K_DISTINTO"),
    "M59": ("§7 (VB-A05): «ninguna protegida» mira sólo la tabla",
            'k_dist_prot = [nombre(i) for i in k_dist if obj[i].get("protegida")]',
            "k_dist_prot = [nombre(i) for i in k_dist if prot_tabla(obj[i])]"),
    "M60": ("§6.1 (VB-A02): la equivalencia saca las pasadas con K distinto",
            '        for i in oks0:\n            p, o_ = res[i]["paquete"]["P"], res[i]["paquete"]["O"]',
            '        for i in oks:\n            p, o_ = res[i]["paquete"]["P"], res[i]["paquete"]["O"]'),
    "M61": ("§7 (VB-A01): el tope de 50.000 MW del tablero no explica la diferencia del placebo",
            'or vrp(i, "K") <= TOPE_TABLERO_MW < vrp(i, "K") * GANANCIA_PLACEBO]', "or False]"),
    "M62": ("§6.1 (VB-A06): las seis mutaciones de la prueba local no se exigen por nombre",
            "and len(nombradas) == len(MUT_LOCAL) and caida", "and caida"),
    # brazos de posición (§3 y §6 bis, decisión de Nicolás del 2026-10-27): cada una rompe una pieza de la regla
    "M63": ("§6 bis: P-cercano toma el alertado más LEJANO del cráter",
            "p = min(px, key=lambda p: (np.hypot(p[0] - ancla[0], p[1] - ancla[1]), p[0], p[1]))",
            "p = max(px, key=lambda p: (np.hypot(p[0] - ancla[0], p[1] - ancla[1]), p[0], p[1]))"),
    "M64": ("§6 bis: P-pico toma el alertado más DÉBIL",
            "p = max(px, key=lambda p: p[4])", "p = min(px, key=lambda p: p[4])"),
    "M65": ("§6 bis: el ancla de los brazos de posición es el centro de la grilla, no pos_crater",
            "ancla = anc(i)\n", "ancla = (AB.C, AB.C)\n"),
    "M66": ("§6 bis: E_lejana no suma a P2'",
            "if lejana and etiqueta_lejana(o, canal):", "if False:"),
    "M67": ("§6 bis: P2' con el canal que decide se mide contra K, no contra P",
            'p2d = {b: p2(b, "P", "TODO", "decide", lejana=True) for b in POS[1:]}',
            'p2d = {b: p2(b, "K", "TODO", "decide", lejana=True) for b in POS[1:]}'),
    "M68": ("§6 bis: gana sin exigir que con la tabla sola no sea peor",
            'and p2d[b][0] == "GANA" and no_peor(*p2t[b][:2])]', 'and p2d[b][0] == "GANA"]'),
    "M69": ("§6 bis: desempate invertido (gana el de MAYOR E + E_lejana)",
            'return min(cands, key=lambda b: (sum(e_tot[b]), b != "Ppico"))',
            'return max(cands, key=lambda b: (sum(e_tot[b]), b != "Ppico"))'),
    "M70": ("§6 bis: a igual E + E_lejana gana P-cercano, no P-pico",
            'b != "Ppico"))', 'b != "Pcercano"))'),
    "M71": ("§6 bis: elegible sin mirar la ventana O",
            "for v in VENTANAS for canal in CANALES)\n", 'for v in ("T",) for canal in CANALES)\n'),
    "M72": ("§6 bis: el §6 se evalúa siempre sobre P (radiante), no sobre el brazo elegido",
            'PE = eleccion or "P"', 'PE = "P"'),
    "M73": ("§6 bis: las pasadas far_ref cuentan como negativos en E (y en P1, P2 y M)",
            'if o["lab"] == "neg_limpio":', 'if o["lab"] in ("neg_limpio", "far_ref"):'),
    "M74": ("§6 bis: con el canal que decide basta no ser peor (EMPATE o SIN SUSTRATO ganan)",
            'p2d[b][0] == "GANA"', "no_peor(*p2d[b][:2])"),
    "M75": ("§6 bis: SIN SUSTRATO cuenta como «no peor» con cualquier neto",
            '(reg == "SIN SUSTRATO" and neto <= 0)', '(reg == "SIN SUSTRATO")'),
    "M76": ("§6 bis: si P no es elegible, se toma un elegible sin exigir que no sea peor que P",
            "np_ = [b for b in POS[1:] if eleg[b] and no_peor(*p2d[b][:2]) and no_peor(*p2t[b][:2])]",
            "np_ = [b for b in POS[1:] if eleg[b]]"),
    "M77": ("§6 bis: NINGUNA POSICIÓN ELEGIBLE no entra a los motivos del §6",
            'fallas.append(("TODO", "decide", "§6 bis: NINGUNA POSICIÓN ELEGIBLE"))', "pass"),
    "M78": ("§6 bis: sin pasadas far_ref no se dice que la vara lejana quedó SIN DATO",
            '("" if far else ": SIN DATO', '("" if True else ": SIN DATO'),
    "M79": ("§6 bis: «con algún alertado» cuenta todas las far_ref",
            'con_alert = sum(bool((res[i]["paquete"]["P"] or {}).get("npix")) for i in far)', "con_alert = len(far)"),
    "M80": ("§6 bis (A119): la distancia del OCR se usa también antes del 2026-06-13",
            'and (f.get("source") == "CONS" or o["hora_utc"] >= AB.FRONTERA_OCR)', "and True"),
    # tras el verificador limpio de los brazos de posición (verificador_posicion/INFORME.md): sus MV2, MV3, MV9 y MV10,
    # las dos piezas que el autor había dejado sin cubrir, y la del arreglo de VP-01
    "M81": ("§6 bis (L20, MV2): E_lejana con la tabla sola cuenta también los FALSO_POSITIVO del OCR",
            'startswith("FALSO_POSITIVO") and f.get("source") == "CONS"', 'startswith("FALSO_POSITIVO") and True'),
    "M82": ("§6 bis (MV3): elegible mira sólo la tabla, no tabla más OCR",
            "for v in VENTANAS for canal in CANALES)\n",
            'for v in VENTANAS for canal in ("tabla",))\n'),
    "M83": ("§6 bis (L20, MV9): para las far_ref el canal que decide es siempre la tabla sola",
            'canal = "tabla" if o["hora_utc"] < AB.FRONTERA_OCR else "todo"\n    if canal == "tabla":',
            'canal = "tabla"\n    if canal == "tabla":'),
    "M84": ("§6 bis (MV10): la condición «con la tabla sola» se mide con el canal que decide",
            'p2t = {b: p2(b, "P", "TODO", "tabla", lejana=True) for b in POS[1:]}',
            'p2t = {b: p2(b, "P", "TODO", "decide", lejana=True) for b in POS[1:]}'),
    "M85": ("§6 bis (VP-01): una lista descriptiva cortada a 20 no lo dice",
            '+ (f" (y {len(lst) - n} más, cortada a {n})" if len(lst) > n else "")', '+ ""'),
    # §6 ter (N-3, S170): mutaciones que deshacen la regla; las atrapan E26, E77 a E80
    "M86": ("§6 ter: las N-3 vuelven a contar en el P1 que veta",
            'm["P1_n3" if n3 and es_n3(o) else "P1"] += 1', 'm["P1"] += 1'),
    "M87": ("§6 ter: la clase N-3 no mira el sensor (entra NOAA-20)",
            ' and o.get("sensor") == SENSOR_N3', ''),
    "M88": ("§6 ter: la clase N-3 no mira la alerta de la tabla",
            'bool(o.get("protegida")) and not o.get("alerta_tabla") and', 'bool(o.get("protegida")) and'),
    "M89": ("§6 ter: la frontera del 2026-10-09 incluye el mismo día",
            'and o["hora_utc"] < FRONTERA_N3)', 'and o["hora_utc"][:10] <= FRONTERA_N3)'),
    "M90": ("§6 ter: la clase N-3 sin frontera de fecha",
            '\n            and o["hora_utc"] < FRONTERA_N3)', ')'),
    # S175: el blanco cambió (el de antes, n3=True en §6.3, es equivalente con la ventana fija; ver el encabezado)
    "M91": ("§6 ter: la clase N-3 llega a la sombra (§6.3; la ventana no la saca)",
            'if i not in fuera_regimen and obj[i]["hora_utc"] < ventana_desde:',
            'if i not in fuera_regimen and obj[i]["hora_utc"] < ventana_desde and not es_n3(obj[i]):'),
    "M92": ("§6 ter: la elegibilidad del §6 bis cuenta las N-3",
            'eleg = {b: all(metricas(b, v, canal, n3=True)[0]["P1"] == 0',
            'eleg = {b: all(metricas(b, v, canal)[0]["P1"] == 0'),
    "M93": ("§6 ter: el P1 del §6.2 cuenta las N-3",
            'm, nadie = metricas(PE, v, canal, n3=True)', 'm, nadie = metricas(PE, v, canal)'),
    "M94": ("§6 ter: el §6.2 no imprime el P1 que cuenta las N-3",
            "contando las N-3 {m['P1'] + m['P1_n3']}", "contando las N-3 {m['P1']}"),
    "M95": ("§6 ter: la lista aparte de las N-3 sale vacía",
            'n3_l = [i for i in oks if es_n3(obj[i]) and etiqueta(obj[i], "todo") == "prot"]', 'n3_l = []'),
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
    "MR8": ("sombra (LR1): la lista de protegidas que salen por otra ROI sale vacía (sólo en esta rama)",
            '[f"{nombre(i)} ({m})" for i, m in fuera_regimen.items() if obj[i].get("protegida")] or "ninguna"',
            '"ninguna"'),
    "MR9": ("sombra (§4.3, LR2; R4): CUMPLE no espera a que «ahora» llegue al fin de la ventana fija",
            "ahora_ok = t_ahora >= t_fin", "ahora_ok = True"),
    "MR10": ("sombra (LR2, LR3): con --sha-desde la ventana (y el reloj) no parte de la hora del commit del corte",
             "ventana_desde = max(INICIO_SOMBRA, fecha_corte)", "ventana_desde = INICIO_SOMBRA"),
    "MR11": ("sombra (LR2; R4): las noches del conjunto cuentan también las pasadas no observadas y las SIN DATO",
             'noches_sem, noches = semanas_noches([obj[i]["hora_utc"] for i in oks0], t_ini)',
             'noches_sem, noches = semanas_noches([obj[i]["hora_utc"] for i in obj], t_ini)'),
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
    "MR25": ("R2-01 (R4): las noches del conjunto no se exigen (ni por semana ni las 14)",
             "noches_ok = not faltan_noches(noches_sem, noches)", "noches_ok = True"),
    "MR26": ("R4: con 5 noches justas en una semana no alcanza (el borde va arriba)",
             "return min(ns) < NOCHES_MIN_SEMANA or n < NOCHES_MIN_SOMBRA",
             "return min(ns) <= NOCHES_MIN_SEMANA or n < NOCHES_MIN_SOMBRA"),
    "MR27": ("R2-04 (MZ1; R4): con «ahora» justo en el fin de la ventana no alcanza (el borde va arriba)",
             "ahora_ok = t_ahora >= t_fin", "ahora_ok = t_ahora > t_fin"),
    "MR28": ("R2-01: se cuentan pasadas y no noches (R5: blanco nuevo, la noche se cuenta una vez)",
             "semana_de.setdefault(h[:10], k)", "semana_de.setdefault(h, k)"),
    "MR29": ("R2-01 (MZ6): la noche es el mes (cada mes cuenta como una noche, la del día 1; R5: blanco nuevo)",
             "semana_de.setdefault(h[:10], k)", 'semana_de.setdefault(h[:8] + "01", k)'),
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
    "MR35": ("R2-03: la ventana no saca las pasadas anteriores a su inicio",
             '            if i not in fuera_regimen and obj[i]["hora_utc"] < ventana_desde:', "            if False:"),
    "MR36": ("R2-04 (MZ4): la hora del corte es la del autor, no la del committer", '"--format=%ct"', '"--format=%at"'),
    "MR37": ("R2-04 (MZ5): --sha-desde acepta 4 caracteres", "len(x) >= 7", "len(x) >= 4"),
    "MR38": ("R2-04: --sha-desde exige 8 caracteres", "len(x) >= 7", "len(x) >= 8"),
    "MR39": ("R2-04 (MZ7): un PROVISORIO leído con faltantes sale 4 y no 5", "rc_final = rc_final or 4", "rc_final = 4"),
    "MR40": ("R2-03: las pasadas sin gránulo no se cortan con la ventana",
             '        sin_g = [x for x in sin_g if not x.get("hora_utc") or (x["hora_utc"] >= ventana_desde\n'
             '                                                               and en_lectura(x["hora_utc"]))]',
             "        pass"),
    "MR41": ("R2-01 (R4): CUMPLE con el fin de la ventana o con las noches (basta una)",
             "dur_ok = ahora_ok and noches_ok and not vol_falta", "dur_ok = (ahora_ok or noches_ok) and not vol_falta"),
    "MR42": ("R2-04: los días se redondean (27,99 se lee 28,0)", 'dias_txt = f"{math.floor(dias * 10) / 10:.1f}"',
             'dias_txt = f"{dias:.1f}"'),
    # S174, VPR945-R3 (cuarta vuelta del PR #945, LECTURA LR3)
    "MR43": ("R3-01: ningún volcán cuenta como de ROI cambiada (las noches por volcán no se exigen)",
             'cambia = sorted(v for v, t in esperada.items() if t != RV.roi_por_volcan("B0").get(v))', "cambia = []"),
    "MR44": ("R3-01: un volcán de ROI cambiada sin pasadas leídas pasa transparente (0 noches no frena)",
             "vol_falta = [v for v in sorted(exigidos) if faltan_noches(*por_v[v])]",
             "vol_falta = [v for v in sorted(exigidos) if por_v[v][1] and faltan_noches(*por_v[v])]"),
    "MR45": ("R4-02: sin semanas en el conjunto, basta con 14 noches (lo de la tercera vuelta)",
             "noches_ok = not faltan_noches(noches_sem, noches)", "noches_ok = noches >= NOCHES_MIN_SOMBRA"),
    "MR46": ("R4-01: en un volcán de ROI cambiada basta con 14 noches, sin semanas",
             "vol_falta = [v for v in sorted(exigidos) if faltan_noches(*por_v[v])]",
             "vol_falta = [v for v in sorted(exigidos) if por_v[v][1] < NOCHES_MIN_SOMBRA]"),
    "MR48": ("R3-04 (MV1 del verificador): una pasada en el minuto exacto del commit del corte queda fuera",
             'if i not in fuera_regimen and obj[i]["hora_utc"] < ventana_desde:',
             'if i not in fuera_regimen and obj[i]["hora_utc"] <= ventana_desde:'),
    "MR49": ("R3-04 (MV2 del verificador): la compuerta de otra ROI ignora la pasada del minuto exacto del corte",
             'and obj[i]["hora_utc"] >= ventana_desde and es_ancestro', 'and obj[i]["hora_utc"] > ventana_desde and es_ancestro'),
    "MR50": ("R3-01: la línea de noches por volcán esconde los volcanes con 0 noches",
             "for v, (ns, n) in sorted(por_v.items())))", "for v, (ns, n) in sorted(por_v.items()) if n))"),
    # S174, VPR945-R4 (quinta vuelta del PR #945: ventana fija, LECTURA LR3)
    "MR51": ("R4: una pasada en el minuto exacto de inicio + 7 días va a la semana anterior (borde de semana)",
             "k = (hora_dt(h) - t_ini) // SEMANA", "k = math.ceil((hora_dt(h) - t_ini) / SEMANA) - 1"),
    "MR52": ("R4: el umbral por semana baja a 4 noches", "NOCHES_MIN_SEMANA = 5", "NOCHES_MIN_SEMANA = 4"),
    "MR53": ("R4: el umbral por semana sube a 6 noches", "NOCHES_MIN_SEMANA = 5", "NOCHES_MIN_SEMANA = 6"),
    "MR54": ("R4: el fin de la ventana se incluye (una pasada en el minuto del fin entra)",
             "return t < t_fin and t <= t_ahora", "return t <= t_fin and t <= t_ahora"),
    "MR55": ("R4: la ventana no tiene fin (sólo la corta «ahora»)",
             "return t < t_fin and t <= t_ahora", "return t <= t_ahora"),
    "MR56": ("R4-03: una pasada con fecha posterior a «ahora» entra a la lectura",
             "return t < t_fin and t <= t_ahora", "return t < t_fin"),
    "MR57": ("R4: la compuerta de otra ROI mira también las pasadas posteriores al fin de la ventana",
             '\n                             and en_lectura(obj[i]["hora_utc"])})', "})"),
    "MR58": ("R4 (decisión de la coordinadora): la exigencia por semana alcanza también a los volcanes sin cambio de ROI",
             "SEMANA_EXIGE_SIN_CAMBIO = False", "SEMANA_EXIGE_SIN_CAMBIO = True"),
    "MR59": ("R4: las pasadas sin gránulo posteriores al fin de la ventana cuentan en la cobertura",
             'and en_lectura(x["hora_utc"]))]', "and True)]"),
    "MR60": ("R4-04 (MW10 del verificador): las noches de un volcán cambiado cuentan sus pasadas no observadas y SIN DATO",
             'por_v = {v: semanas_noches([obj[i]["hora_utc"] for i in oks0 if obj[i]["volcan"] == v], t_ini)',
             'por_v = {v: semanas_noches([obj[i]["hora_utc"] for i in obj if obj[i]["volcan"] == v], t_ini)'),
    "MR61": ("R4: los días se cuentan hasta el fin aunque «ahora» sea anterior",
             "dias = max(0.0, (t_lim - t_ini).total_seconds() / 86400)",
             "dias = max(0.0, (t_fin - t_ini).total_seconds() / 86400)"),
    "MR62": ("R4-01: los volcanes de ROI cambiada no se exigen (sólo el conjunto)",
             "exigidos = [v for v in esperada if v in cambia or SEMANA_EXIGE_SIN_CAMBIO]", "exigidos = []"),
    "MR63": ("R4: el límite de la lectura que se imprime (y los días) es el fin aunque «ahora» sea anterior",
             "t_lim = min(t_fin, t_ahora)", "t_lim = t_fin"),
    # S174, VPR945-R5 (sexta vuelta del PR #945; decisión de Nicolás del 2026-11-06, LECTURA LR3)
    "MR64": ("R5-03: los volcanes sin cambio de ROI piden 13 noches en vez de 14",
             "NOCHES_MIN_SIN_CAMBIO = 14", "NOCHES_MIN_SIN_CAMBIO = 13"),
    "MR65": ("R5-03: los volcanes sin cambio de ROI piden 15 noches en vez de 14",
             "NOCHES_MIN_SIN_CAMBIO = 14", "NOCHES_MIN_SIN_CAMBIO = 15"),
    "MR66": ("R5-03: los volcanes sin cambio de ROI no piden noches (CUMPLE con 2 de 11 volcanes)",
             "vol_pocas = [v for v in sin_cambio if por_v[v][1] < NOCHES_MIN_SIN_CAMBIO]", "vol_pocas = []"),
    "MR67": ("R5-02: una noche con pasadas a los dos lados de un borde cuenta en las dos semanas",
             "semana_de.setdefault(h[:10], k)", "semana_de.setdefault((h[:10], k), k)"),
    "MR68": ("R5-01: una zona distinta de UTC en --ahora se ignora en vez de convertirse",
             "t = t.astimezone(datetime.timezone.utc).replace(tzinfo=None)", "t = t.replace(tzinfo=None)"),
    "MR69": ("R5-04 (MX11): sin --ahora se lee el reloj local en vez del UTC",
             "datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None, microsecond=0)",
             "datetime.datetime.now().replace(microsecond=0)"),
    "MR70": ("R5-04 (MX13): una pasada en el minuto exacto de «ahora» queda fuera",
             "return t < t_fin and t <= t_ahora", "return t < t_fin and t < t_ahora"),
    "MR71": ("R5-02: la noche va a la semana de su última pasada en vez de la primera",
             "for h in sorted(horas, key=hora_dt):", "for h in sorted(horas, key=hora_dt, reverse=True):"),
    # S174, VPR945-R6 (sexta ronda del verificador limpio, retoques tras el merge de #945)
    "MR72": ("R6-02 (MY7 del verificador): la regla de las 14 noches de los sin cambio se apaga si ningún volcán cambia "
             "de ROI (lectura con B0)",
             "dur_ok = ahora_ok and noches_ok and not vol_falta and not vol_pocas",
             "dur_ok = ahora_ok and noches_ok and not vol_falta and not (vol_pocas and cambia)"),
    "MR73": ("R6-02 (MY8 del verificador): con B0 la lista de volcanes sin cambio queda vacía",
             "sin_cambio = [v for v in sorted(esperada) if v not in exigidos]",
             "sin_cambio = [v for v in sorted(esperada) if v not in exigidos] if cambia else []"),
    "MR74": ("R6-01: el OverflowError de pasar --ahora a UTC no se captura (salida 1 con traceback)",
             "except (ValueError, OverflowError):", "except ValueError:"),
    "MR75": ("R6-03 (MY10 del verificador): la zona de --ahora se convierte a la zona local de la máquina, no a UTC",
             "t = t.astimezone(datetime.timezone.utc).replace(tzinfo=None)", "t = t.astimezone().replace(tzinfo=None)"),
    # S174, VPR953 (verificador de #953; X12 a X15 de su mutar_propio.py)
    "MR76": ("VPR953-02 (X12): sólo el primero de los volcanes sin cambio de ROI pide 14 noches",
             "vol_pocas = [v for v in sin_cambio if por_v[v][1] < NOCHES_MIN_SIN_CAMBIO]",
             "vol_pocas = [v for v in sin_cambio[:1] if por_v[v][1] < NOCHES_MIN_SIN_CAMBIO]"),
    "MR77": ("VPR953-02 (X13): el último de los volcanes sin cambio de ROI no pide 14 noches",
             "vol_pocas = [v for v in sin_cambio if por_v[v][1] < NOCHES_MIN_SIN_CAMBIO]",
             "vol_pocas = [v for v in sin_cambio[:-1] if por_v[v][1] < NOCHES_MIN_SIN_CAMBIO]"),
    "MR78": ("VPR953-02 (X14): el segundo de los volcanes sin cambio de ROI no pide 14 noches",
             "vol_pocas = [v for v in sin_cambio if por_v[v][1] < NOCHES_MIN_SIN_CAMBIO]",
             "vol_pocas = [v for j, v in enumerate(sin_cambio) if j != 1 and por_v[v][1] < NOCHES_MIN_SIN_CAMBIO]"),
    "MR79": ("VPR953-03 (X15): la línea CUMPLE nombra sólo a dos de los volcanes sin cambio de ROI",
             '", ".join(f"{v} {por_v[v][1]}" for v in sin_cambio)',
             '", ".join(f"{v} {por_v[v][1]}" for v in sin_cambio[:2])'),
    "CAIDA": ("CONTROL: el analizador sólo se cae (excepción al cargar los objetivos)",
              'obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8"))}',
              'raise RuntimeError("mutación de control: el programa se cae")'),
}


def correr(dest, evaluador, nombre, viejo=None, nuevo=None, escenarios=""):
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
                            "--evaluador", str(evaluador)] + (["--solo", escenarios] if escenarios else []), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=259200, cwd=str(AQUI))  # 3 días: el plazo es de reloj y corre suspendido
    except subprocess.TimeoutExpired:
        # S162 (relevo): con CPU compartida una mutación pasó las 2 h y la excepción tumbó TODO el medidor, sin un
        # solo resultado. Un tiempo agotado es SIN DATO de esa mutación (no cuenta como atrapada) y se sigue.
        print(f"   {nombre}: SIN DATO (tiempo agotado)", flush=True)
        return nombre, "SIN DATO (tiempo)", None, "(tiempo agotado)", [], False
    finally:
        copia.unlink()
    txt = o.stdout + o.stderr
    # S162 (relevo): M82 cayó sin línea de pruebas y sin traza; la salida entera de cada corrida queda en disco
    (dest / f"salida_{nombre}.txt").write_text(txt, encoding="utf-8")
    linea = next((x for x in txt.splitlines() if x.startswith("== PRUEBAS")), "(sin línea de pruebas)")
    fallan = [x for x in txt.splitlines() if " | FALLA" in x]
    atrapan = [x.split(" | ")[0] for x in fallan]
    # VPR953-01: ¿todas las fallas son la bandera «no se cae» (un Traceback en un escenario con no_traceback)?
    solo_bandera = bool(fallan) and all(BANDERA in x for x in fallan)
    if o.returncode == 0 and "TODOS LOS ESCENARIOS COMO SE ESPERA" in linea:
        estado = "PASA"
    elif o.returncode == 1 and "FALLAS" in linea:
        estado = "ATRAPADA"
    else:
        estado = "CAÍDA"
    print(f"   {nombre}: {estado} | {linea[:100]}", flush=True)   # en vivo: si algo cae después, esto queda
    return nombre, estado, o.returncode, linea, atrapan, solo_bandera


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--evaluador", required=True, type=Path)
    ap.add_argument("--hilos", type=int, default=4)
    ap.add_argument("--solo", default="", help="ids de mutaciones a correr (IDENTIDAD y CAIDA van siempre)")
    ap.add_argument("--escenarios", default="",
                    help="escenarios de las pruebas a correr (--solo de probar_evaluar_v750a.py); restringe la batería y "
                         "no reemplaza la corrida entera, y se dice en la salida")
    a = ap.parse_args()
    sel = {x for x in a.solo.split(",") if x}
    a.dest.mkdir(parents=True, exist_ok=True)
    mut = {k: v for k, v in MUTACIONES.items() if not sel or k in sel or k == "CAIDA"}
    trabajos = [("IDENTIDAD", None, None)] + [(k, v[1], v[2]) for k, v in mut.items()]
    with ThreadPoolExecutor(a.hilos) as ex:
        res = {r[0]: r for r in ex.map(lambda t: correr(a.dest, a.evaluador, *t, escenarios=a.escenarios), trabajos)}
    L = []

    def pr(s):
        print(s, flush=True)
        L.append(s)

    ident = res["IDENTIDAD"]
    if sel:
        pr(f"(corrida parcial: --solo {a.solo})")
    if a.escenarios:
        pr(f"(batería restringida a --escenarios {a.escenarios}: «atrapada» es por aserción en esos escenarios; no "
           "reemplaza la corrida con la batería entera)")
    pr(f"IDENTIDAD | {ident[1]} (tiene que ser PASA) | rc {ident[2]} | {ident[3][:200]}")
    malos = 0 if ident[1] == "PASA" else 1
    for nom, (que, _v, _n) in mut.items():
        _, est, rc, linea, atrapan, bandera = res[nom]
        esperado = "CAÍDA" if nom == "CAIDA" else "ATRAPADA"
        malos += est != esperado
        marca = ' sólo por la bandera "no se cae"' if est == "ATRAPADA" and bandera else ""
        pr(f"{nom} | {est}{marca} (tiene que ser {esperado}) | rc {rc} | {que} | {linea[:120]} | escenarios que fallan "
           f"{atrapan}")
    n_mut = len(mut) - 1
    atr = sum(1 for k in mut if k != "CAIDA" and res[k][1] == "ATRAPADA")
    atr_b = sum(1 for k in mut if k != "CAIDA" and res[k][1] == "ATRAPADA" and res[k][5])
    ctrl = ident[1] == "PASA" and res["CAIDA"][1] == "CAÍDA"
    pr(f"== RESUMEN: {atr} de {n_mut} mutaciones atrapadas ({atr - atr_b} por aserción sobre la salida, {atr_b} sólo "
       f"por la bandera \"no se cae\"); controles "
       f"{'como deben' if ctrl else 'FALLAN'}; {'TODO COMO SE ESPERA' if malos == 0 else f'{malos} FUERA DE LO ESPERADO'}")
    (a.dest / "mutar_evaluar_v750a_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 0 if malos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
