# -*- coding: utf-8 -*-
"""S157, tarea 1.29, candado. Mutaciones de evaluar_d25.py: cada regla del pre-registro rota a propósito tiene que hacer
fallar a probar_evaluar_d25.py POR UNA ASERCIÓN CON NOMBRE (la línea RESUMEN con el caso que falla). Una mutación que
hace caer el script (traceback, sin RESUMEN) NO cuenta como atrapada (memoria S156: control de caída). Una que deja
20 de 20 en verde queda NO ATRAPADA y se informa como tal.

Cada mutación corre en una copia de la carpeta (experiments/_s157_mut_<n>/, borrada al terminar) con su propio TMP.
Uso: python mutar_evaluador_d25.py <TMP> [paralelos] [nombres separados por coma]   -> mutaciones_salida.txt
"""
import concurrent.futures as cf
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TMP = Path(sys.argv[1]).resolve()
PAR = int(sys.argv[2]) if len(sys.argv) > 2 else 3
COPIAR = ("evaluar_d25.py", "probar_evaluar_d25.py", "sustrato_k.py", "_congelado_v1")

# (nombre, texto original, texto mutado, caso que debería atraparla)
MUTACIONES = [
    ("corte_50", 'CORTE_CENIT = 40.0', 'CORTE_CENIT = 50.0', "corte"),
    ("sin_bloqueo", '("VIIRS375|sin_kernel|z>40", "bloquea")', '("VIIRS375|sin_kernel|z>40", "decide")', "bloq_mejora"),
    ("kernel_decide", '("VIIRS375|kernel|z<=40", "informa")', '("VIIRS375|kernel|z<=40", "decide")', "kernel"),
    ("ignora_empeora", 'empeora = any(v == "EMPEORA" for v in m.values())', 'empeora = False', "empeora750"),
    ("pierde_tras_indec", '    if "PIERDE" in p2:                 # verificador H2', '    if False:                 # verificador H2', "p2_m_indec"),
    ("sin_volcanes", 'r == "MEJORA" and vols_neg < MIN_VOLCANES_MEJORA', 'False', "un_volcan"),
    ("sin_repeticion", '            if rp is not None and len(rp) == 2:', '            if False:', "rep_si / rep_no"),
    ("orden_mejora", '"SIN EFECTO", "MEJORA", "CUMPLE")', '"MEJORA", "SIN EFECTO", "CUMPLE")', "orden"),
    ("simetrica_signo_par", '        falsos[regla_m(rng.choice((-1.0, 1.0), size=len(uniq))[idx] * a, W)[0]] += 1',
     '        falsos[regla_m(rng.choice((-1.0, 1.0), size=len(a)) * a, W)[0]] += 1', "calib_simetrica"),
    ("snpp_decide", 'if excluir and es_snpp(k, c, prot):\n                snpp.append(k); continue',
     'if False:\n                snpp.append(k); continue', "snpp"),
    ("sin_p1b", '(c["disp"] or 0) >= 1 > (b["disp"] or 0)', 'False', "p1b"),
    ("sin_huella", 'if con_pc and huella < len(con_pc):', 'if False:', "huella"),
    ("sin_modis", 'if n_modis[n]:', 'if False:', "modis"),
    ("sin_flags", 'if fl.get(c) != val:', 'if False:', "flag"),
    ("sin_determinismo", 'ok = bool(amb) and igual / len(amb) >= UMBRAL_DETERMINISMO', 'ok = True', "determ"),
    ("p2_sordo", '"PIERDE" if sd > sk + ruido', '"PIERDE" if sd > sk + ruido + 1000', "p2"),
    ("combinar_any", 'elif all(r["mejora"] for r in rs):', 'elif any(r["mejora"] for r in rs):', "combinar"),
    ("sin_ruidosas", 'if g is not None and len(g) == 2 and g["control"]["pub"] != g["brazo"]["pub"]:', 'if False:', "veto_gemelo"),
    ("sin_pendientes", 'elif "G" not in brazos:', 'elif False:', "v2_veto"),
    ("mejora_lo", '"MEJORA" if hi < 0', '"MEJORA" if lo < 0', "nulo"),
    ("bloquea_cuenta_mejora", 'elif modo == "bloquea" and r == "MEJORA":', 'elif False:', "bloq_mejora"),
    ("calib_por_par", 'f_mej, f_emp, poder = calibrar_simetrico(d, W, bl)',
     'f_mej, f_emp, poder = calibrar_simetrico(d, W, list(range(len(d))))', "(ninguno: la unidad prueba la función, no su uso)"),
    ("boot_por_pasada", 'W = pesos_bloque([p["bloque"] for p in P])', 'W = pesos_pasada(len(P))', "(ninguno esperado)"),
]


def una(i, nombre, a, b, esperado):
    dst = AQUI.parent / ("_s157_mut_%02d" % i)
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir()
    for f in COPIAR:
        (shutil.copytree if (AQUI / f).is_dir() else shutil.copy2)(AQUI / f, dst / f)
    src = (dst / "evaluar_d25.py").read_text(encoding="utf-8")
    if src.count(a) != 1:
        shutil.rmtree(dst)
        return nombre, "NO APLICA (el texto original aparece %d veces)" % src.count(a), esperado, ""
    (dst / "evaluar_d25.py").write_text(src.replace(a, b), encoding="utf-8")
    p = subprocess.run([sys.executable, str(dst / "probar_evaluar_d25.py"), str(TMP / nombre)],
                       capture_output=True, text=True, encoding="utf-8")
    shutil.rmtree(dst, ignore_errors=True)
    # Cada corrida de probar deja varios cientos de MB (copia unida de K y brazos por caso): se borra al terminar.
    # Sin esto, 23 mutaciones llenaron el disco D: el 2026-10-20 (18 caídas por "No space left on device").
    shutil.rmtree(TMP / nombre, ignore_errors=True)
    out = p.stdout + p.stderr
    m = re.search(r"RESUMEN: (\d+) de (\d+) casos OK(?: \| FALLAN: (\[.*\]))?", out)
    if not m:
        return nombre, "CAÍDA (sin RESUMEN: no cuenta como atrapada)", esperado, out[-400:]
    if m.group(3):
        return nombre, "ATRAPADA por %s" % m.group(3), esperado, ""
    return nombre, "NO ATRAPADA (%s de %s OK)" % (m.group(1), m.group(2)), esperado, ""


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(PAR) as ex:
        solo = sys.argv[3].split(",") if len(sys.argv) > 3 else None   # para repetir mutaciones sueltas
        futs = [ex.submit(una, i, *m) for i, m in enumerate(MUTACIONES) if solo is None or m[0] in solo]
        res = [f.result() for f in futs]
    n_atr = sum(r[1].startswith("ATRAPADA") for r in res)
    n_caida = sum(r[1].startswith("CAÍDA") for r in res)
    for nombre, estado, esperado, cola in res:
        print("%-22s %-60s esperado: %s" % (nombre, estado, esperado))
        if cola:
            print("      cola: %s" % cola.replace("\n", " | ")[-300:])
    print("\nATRAPADAS por aserción: %d de %d | caídas (no cuentan): %d | no atrapadas: %d" % (
        n_atr, len(res), n_caida, len(res) - n_atr - n_caida))


if __name__ == "__main__":
    main()
