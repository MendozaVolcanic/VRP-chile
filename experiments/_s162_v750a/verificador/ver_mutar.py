# -*- coding: utf-8 -*-
"""Verificador V750-A: nulo de las pruebas del autor con mutaciones MIAS (una linea cada una).
Corre los escenarios de probar_evaluar_v750a.py contra una copia mutada del analizador. Parada temprana en la primera
FALLA o CAIDA salvo --completo (las no atrapadas siempre corren completas)."""
import argparse
import importlib.util
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PADRE = AQUI.parent
sys.path.insert(0, str(PADRE))
spec = importlib.util.spec_from_file_location("probar", PADRE / "probar_evaluar_v750a.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)

ORIG = (PADRE / "evaluar_v750a.py").read_text(encoding="utf-8")

Q = '"'
MUT = {
    "V01": ("K=prod: se quita 'and not k_dist_prot'",
            "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0)) and not k_dist_prot",
            "k_ok = len(k_dist) <= AB.MAX_K_DISTINTO * max(1, len(oks0))"),
    "V02": ("K=prod: la mitad pc_vrp (0,001 MW) deja de contar",
            '- (obj[i].get("pc_vrp") or 0)) > 0.001})', '- (obj[i].get("pc_vrp") or 0)) > 1000})'),
    "V03": ("K=prod: las distintas no salen de los brazos",
            "oks = [i for i in oks0 if i not in set(k_dist)]", "oks = list(oks0)"),
    "V04": ("M: banda de razon con piso 0,5 en vez de 0,9", "BANDA_RAZON = (0.9, 1.1)", "BANDA_RAZON = (0.5, 1.1)"),
    "V05": ("M: banda de razon con techo 1,25 en vez de 1,1", "BANDA_RAZON = (0.9, 1.1)", "BANDA_RAZON = (0.9, 1.25)"),
    "V06": ("cobertura: las pasadas sin granulo del generador no cuentan",
            "len(sin) + len(sin_g) <= AB.MAX_SIN_DATO * den_cob", "len(sin) <= AB.MAX_SIN_DATO * den_cob"),
    "V07": ("cobertura: una protegida SIN DATO ya no frena sola",
            "<= AB.MAX_SIN_DATO * den_cob and not prot_sin", "<= AB.MAX_SIN_DATO * den_cob"),
    "V08": ("cobertura: el denominador no saca fuera/sin_crater",
            'den_cob = max(1, len(obj) + len(sin_g) - no_obs["fuera"] - no_obs["sin_crater"])',
            "den_cob = max(1, len(obj) + len(sin_g))"),
    "V09": ("cobertura: la pasada diurna deja de ser SIN DATO",
            'elif part[i] == "observada" and r.get("dayflag") != 0:', "elif False:"),
    "V10": ("M: los pares sólo con protegidas",
            'if etiqueta(o, canal) not in ("prot", "baja") or not en_ventana(o, v):',
            'if etiqueta(o, canal) != "prot" or not en_ventana(o, v):'),
    "V11": ("§4.1: tolerancia de VRP 5e-3 en vez de 1e-6", "TOL_VRP_EQUIV = 1e-6", "TOL_VRP_EQUIV = 5e-3"),
    "V12": ("S-1: se quita el par (Pdef, O)",
            'PARES_S1 = (("P", "Pdef"), ("P", "O"), ("Pdef", "O"))', 'PARES_S1 = (("P", "Pdef"), ("P", "O"))'),
    "V13": ("S-1: el umbral siempre del pase 1",
            'return dg[f"pasada{pase}"][f"u_{x}{2 if zona == 2 else 1}"]',
            'return dg["pasada1"][f"u_{x}{2 if zona == 2 else 1}"]'),
    "V14": ("S-1: la celda alerta sólo con NTI",
            'all(cd[f"c_{x}"] > _u(dg_umbral, cd["pase"], cd["zona"], x) for x in ("nti", "eti"))',
            'all(cd[f"c_{x}"] > _u(dg_umbral, cd["pase"], cd["zona"], x) for x in ("nti",))'),
    "V15": ("§6.1 local: no exige el minimo de mutaciones atrapadas",
            "ok = verde and todas and n_atr >= MIN_MUT_LOCAL and caida", "ok = verde and todas and caida"),
    "V16": ("§6.1 local: no exige el control caido",
            "ok = verde and todas and n_atr >= MIN_MUT_LOCAL and caida",
            "ok = verde and todas and n_atr >= MIN_MUT_LOCAL"),
    "V17": ("§6.1 local: no exige VERDE ni la ausencia de ROJA",
            'verde = any(x.startswith("VERDE:") for x in lin) and not any(x.startswith("ROJA") for x in lin)',
            "verde = True"),
    "V18": ("--solo-controles ignorado", "if a.solo_controles or not todo_ok:", "if not todo_ok:"),
    "V19": ("P2: el bloque pierde el volcan (sólo la noche)",
            'sumas[(o["hora_utc"][:10], o["volcan"])] += c', 'sumas[(o["hora_utc"][:10],)] += c'),
    "V20": ("etiqueta 'decide': T y O invertidas",
            'canal = "tabla" if o["hora_utc"] < AB.FRONTERA_OCR else "todo"',
            'canal = "todo" if o["hora_utc"] < AB.FRONTERA_OCR else "tabla"'),
    "V21": ("M: sin piso de sustrato (5 pares, 3 noches)",
            'if len(P_) < EM.N_MIN_PARES or len({p["bloque"] for p in P_}) < EM.N_MIN_NOCHES:', "if False:"),
    "V22": ("control nulo del contador siempre OK", "nulo_ok = bool(nidx) and c_nulo == 0", "nulo_ok = True"),
    "V23": ("control placebo M siempre OK",
            'ctrl["placebo (M con comparador)"] = all(r != "MEJORA" for r in pl_m.values())',
            'ctrl["placebo (M con comparador)"] = True'),
    "V24": ("control placebo publicacion siempre OK",
            'ctrl["placebo (publicación)"] = not pl_dist', 'ctrl["placebo (publicación)"] = True'),
    "V25": ("P1b abajo: el corte de 1 MW pasa a 100 MW",
            'if e == "prot" and pb and vb < 1.0:', 'if e == "prot" and pb and vb < 100.0:'),
    "V26": ("etiqueta: el flag 'decide' del objetivo se ignora",
            'if o["lab"] != "pos" or not o.get("decide"):', 'if o["lab"] != "pos":'),
    "V27": ("§6.1: la etiqueta 'decidida por la escena' nunca sale", "if decidida_por_escena(dP, dO)", "if False"),
    "V28": ("M: la razon se mide sobre TODAS las alertas, no sólo protegidas",
            'if etiqueta(obj[i], canal) == "prot" and en_ventana(obj[i], v) and pub(i, b)',
            'if etiqueta(obj[i], canal) in ("prot", "baja") and en_ventana(obj[i], v) and pub(i, b)'),
    "V29": ("P2: el bloque usa mes en vez de noche",
            'sumas[(o["hora_utc"][:10], o["volcan"])] += c', 'sumas[(o["hora_utc"][:7], o["volcan"])] += c'),
    "V30": ("nulo K-gemelo acepta M MEJORA/EMPEORA",
            'g_m in ("NEUTRO", "SIN SUSTRATO")', 'g_m in ("NEUTRO", "SIN SUSTRATO", "MEJORA", "EMPEORA")'),
    "V32": ("sombra: P2 PIERDE sólo cuenta en el canal tabla", 'if reg == "PIERDE":',
            'if reg == "PIERDE" and canal == "tabla":'),
    "V33": ("sombra: P1 sólo en canal tabla", 'if m["P1"]:\n                motivos.append(f"{canal}: P1',
            'if m["P1"] and canal == "tabla":\n                motivos.append(f"{canal}: P1'),
    "V34": ("censo: P1 sólo en canal tabla", 'if m["P1"]:\n                    motivos.append(f"P1',
            'if m["P1"] and canal == "tabla":\n                    motivos.append(f"P1'),
    "V35": ("censo: P2 sólo en la ventana T", 'if reg not in ("GANA", "EMPATE"):',
            'if reg not in ("GANA", "EMPATE") and v == "T":'),
    "V36": ("censo: M comparador sólo en canal tabla", 'if rm != "MEJORA":', 'if rm != "MEJORA" and canal == "tabla":'),
    "V37": ("censo: razon M sólo en ventana O", "if rz is None or not (BANDA_RAZON[0] <= rz <= BANDA_RAZON[1]):",
            "if v == 'O' and (rz is None or not (BANDA_RAZON[0] <= rz <= BANDA_RAZON[1])):"),
    "V38": ("M: la razon de las protegidas exige tambien que K publique (lectura de §5 'que publican los dos')",
            'if etiqueta(obj[i], canal) == "prot" and en_ventana(obj[i], v) and pub(i, b)',
            'if etiqueta(obj[i], canal) == "prot" and en_ventana(obj[i], v) and pub(i, b) and pub(i, "K")'),
    "V41": ("S-1: las pasadas con diagnostico invalido se tratan como validas (sin SIN DATO)",
            "if diag_valido(dA) and diag_valido(dB):", "if dA and dB:"),
    "V42": ("equivalencia local: el archivo ausente no cierra",
            'if not ruta or not Path(ruta).exists():\n        return False, "salida de la prueba local AUSENTE (SIN DATO)"',
            'if not ruta or not Path(ruta).exists():\n        return True, "salida de la prueba local AUSENTE (SIN DATO)"'),
    "V39": ("equivalencia: la VRP nunca se compara",
            'or abs((p.get("vrp_mw") or 0.0) - (o_.get("vrp_mw") or 0.0)) > TOL_VRP_EQUIV', "or False"),
    "V40": ("equivalencia: la banda eximiria siempre que el campo exista",
            '(banda if res[i].get("banda_triangulacion") else dist).append(i)',
            '(banda if res[i].get("banda_triangulacion") is not None else dist).append(i)'),
}


def correr(nombre, dest, ev, completo):
    que, viejo, nuevo = MUT[nombre]
    n = ORIG.count(viejo)
    if n != 1:
        return nombre, "ERROR", f"la linea aparece {n} veces", []
    copia = PADRE / f"_ver_{nombre}_evaluar_v750a.py"
    copia.write_text(ORIG.replace(viejo, nuevo), encoding="utf-8")
    sal = dest / f"pruebas_{nombre}"
    sal.mkdir(parents=True, exist_ok=True)
    fallas, caidas, oks = [], [], []
    try:
        for esc in P.ESCENARIOS:
            est, det = P.correr(esc, P.ESCENARIOS[esc], copia, ev, sal)
            if est == "OK":
                oks.append(esc)
            elif est == "FALLA":
                fallas.append((esc, det[0][:110] if det else ""))
            else:
                caidas.append((esc, det[0] if det else ""))
            if not completo and (fallas or caidas):
                break
    finally:
        copia.unlink(missing_ok=True)
    if caidas:
        estado = "CAIDA"
    elif fallas:
        estado = "ATRAPADA" + (" (parada temprana)" if not completo else "")
    else:
        estado = "PASA (NO ATRAPADA)"
    return nombre, estado, que, (fallas[:4] + caidas[:2])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, required=True)
    ap.add_argument("--evaluador", required=True, type=Path)
    ap.add_argument("--hilos", type=int, default=5)
    ap.add_argument("--solo", default="")
    ap.add_argument("--completo", action="store_true")
    a = ap.parse_args()
    sel = [x for x in a.solo.split(",") if x] or list(MUT)
    a.dest.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.hilos) as ex:
        futs = [ex.submit(correr, n, a.dest, a.evaluador, a.completo) for n in sel]
        for f in futs:
            nombre, est, que, det = f.result()
            print(f"{nombre} | {est} | {que} | {det}", flush=True)


if __name__ == "__main__":
    main()
