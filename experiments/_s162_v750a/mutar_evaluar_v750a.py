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
roturas V01 a V41 mostraron sin vigilar.
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
    "M44": ("§6.3: la sombra mira sólo la tabla",
            'for canal in CANALES:\n            m, nadie = metricas("P", "TODO", canal)',
            'for canal in ("tabla",):\n            m, nadie = metricas("P", "TODO", canal)'),
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
                            "--evaluador", str(evaluador)], capture_output=True, text=True, encoding="utf-8",
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
    a = ap.parse_args()
    a.dest.mkdir(parents=True, exist_ok=True)
    trabajos = [("IDENTIDAD", None, None)] + [(k, v[1], v[2]) for k, v in MUTACIONES.items()]
    with ThreadPoolExecutor(a.hilos) as ex:
        res = {r[0]: r for r in ex.map(lambda t: correr(a.dest, a.evaluador, *t), trabajos)}
    L = []

    def pr(s):
        print(s, flush=True)
        L.append(s)

    ident = res["IDENTIDAD"]
    pr(f"IDENTIDAD | {ident[1]} (tiene que ser PASA) | rc {ident[2]} | {ident[3][:200]}")
    malos = 0 if ident[1] == "PASA" else 1
    for nom, (que, _v, _n) in MUTACIONES.items():
        _, est, rc, linea, atrapan = res[nom]
        esperado = "CAÍDA" if nom == "CAIDA" else "ATRAPADA"
        malos += est != esperado
        pr(f"{nom} | {est} (tiene que ser {esperado}) | rc {rc} | {que} | {linea[:120]} | escenarios que fallan "
           f"{atrapan}")
    n_mut = len(MUTACIONES) - 1
    atr = sum(1 for k in MUTACIONES if k != "CAIDA" and res[k][1] == "ATRAPADA")
    ctrl = ident[1] == "PASA" and res["CAIDA"][1] == "CAÍDA"
    pr(f"== RESUMEN: {atr} de {n_mut} mutaciones atrapadas por aserción; controles "
       f"{'como deben' if ctrl else 'FALLAN'}; {'TODO COMO SE ESPERA' if malos == 0 else f'{malos} FUERA DE LO ESPERADO'}")
    (a.dest / "mutar_evaluar_v750a_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 0 if malos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
