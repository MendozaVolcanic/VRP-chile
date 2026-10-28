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
M63 a M80 son de los brazos de posición (§3 y §6 bis, decisión de Nicolás del 2026-10-27).
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
            "for v in VENTANAS for canal in CANALES) for b in POS}", 'for v in ("T",) for canal in CANALES) for b in POS}'),
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
                           errors="replace", timeout=14400, cwd=str(AQUI))
    except subprocess.TimeoutExpired:
        # S162 (relevo): con CPU compartida una mutación pasó las 2 h y la excepción tumbó TODO el medidor, sin un
        # solo resultado. Un tiempo agotado es SIN DATO de esa mutación (no cuenta como atrapada) y se sigue.
        print(f"   {nombre}: SIN DATO (tiempo agotado)", flush=True)
        return nombre, "SIN DATO (tiempo)", None, "(tiempo agotado)", []
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
    print(f"   {nombre}: {estado} | {linea[:100]}", flush=True)   # en vivo: si algo cae después, esto queda
    return nombre, estado, o.returncode, linea, atrapan


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--evaluador", required=True, type=Path)
    ap.add_argument("--hilos", type=int, default=4)
    ap.add_argument("--solo", default="", help="ids de mutaciones a correr (IDENTIDAD y CAIDA van siempre)")
    ap.add_argument("--escenarios", default="", help="restringe la batería a estos escenarios (no reemplaza la corrida entera)")
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
