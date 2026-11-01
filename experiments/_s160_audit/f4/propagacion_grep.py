# -*- coding: utf-8 -*-
"""S160 F4: para cada rebaja del periodo S146..S157, busca sus hijos (frase, numero o ID) en la instantanea de
d516b9d8c y en la memoria del agente, y dice si el pasaje lleva marca (⚠️ o el ID de la sesion de la rebaja en la
mismo pasaje envolvente, desde el inicio de la regla o encabezado, tope 80 lineas). Pregunta 1 del instrumento: si la propagacion estuviera rota del todo, cada hijo
saldria SIN MARCA; pregunta 2: el control positivo es A83 (rebajada S146, tiene que salir CON MARCA) y el control
negativo es una frase inventada (0 hits).
Uso: python -I propagacion_grep.py <raiz_instantanea> <carpeta_memoria>
"""
import re, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(sys.argv[1]); MEM = Path(sys.argv[2])
ARCHIVOS = [ROOT / "CLAUDE.md"] + sorted(ROOT.glob("docs/*.md")) + sorted(ROOT.glob("docs/*/*.md")) \
    + sorted(ROOT.glob("pipeline/profiles/*.yaml")) + sorted(ROOT.glob("pipeline/*.py")) + sorted(ROOT.glob("scripts/*.py")) \
    + sorted(ROOT.glob("tests/*.py")) + sorted(ROOT.glob("frontend/*.html")) + sorted(ROOT.glob("frontend/*.js")) \
    + sorted(MEM.glob("*.md"))
REBAJAS = [
 ("R1 K en produccion (S153/#850; marcas S153 y S157)", ["S153", "S157"], [
    r"ENABLE_TEST1_PATH\s*=\s*True", r"enable_test1_path:\s*true", r"Test 1 integrado[^.\n]{0,60}(producci[oó]n|en el ROI)", r"min\(C1", r"ENABLE_MODIS_B22_PRIMARY\s*=\s*False", r"banda 21 (como )?primaria", r"recall (de )?50 ?(a|→|->) ?80", r"50→80"]),
 ("R2 historico reemplazado por K (S158 #883, en main; frontera 2025-02-15)", ["S158", "#883"], [
    r"desde la observaci[oó]n del 2026-09-18", r"se mover[aá] m[aá]s atr[aá]s", r"C0 antes del 2026-09-18", r"30 d[ií]as previos", r"0 de 3\.6[68][17]", r"frontera de K en la fecha"]),
 ("R3 tope D9 / A23 (S146 V-01, S151 P5)", ["S146", "S151"], [
    r"207 de 214", r"207 \(96", r"matar[ií]a 207", r"0 fuga", r"0 records sobre 5 MW", r"1\.565", r"343 c[uú]mulos", r"no quedan acciones abiertas"]),
 ("R4 A119 corregida (S151 D5/D6)", ["S151"], [
    r"86 ?% (en|de )?enero", r"cobertura nocturna 86", r"0 alertas MODIS dependen", r"MODIS est[aá] completo"]),
 ("R5 A10 / D32 (S147)", ["S147", "D32"], [
    r"pc\.vrp_mw[^.\n]{0,80}lo que MIROVA reporta", r"cluster summit\s*=\s*lo que MIROVA", r"solo cluster summit"]),
 ("R6 criterio de victoria, D-4 y D-9 (S151)", ["S151", "D-4", "D-9"], [
    r"priorizamos recall sobre precision", r"recall sobre precisi", r"lectura B[^.\n]{0,40}pendiente", r"decisi[oó]n pendiente D-4"]),
 ("R7 D8' anomalia mayor (S150/S151)", ["S150", "S151"], [
    r"D8'[^\n]{0,40}RESUELTO", r"no es `vrp_mw desc`", r"m[aá]s cercano al cr[aá]ter"]),
 ("R8 D18 medida en S151 (KC NO CUMPLE; MIROVA mide desde el centro de grilla)", ["S151"], [
    r"D18 nunca se ha medido", r"nunca se ha medido con la caja", r"igual para todos", r"mide desde el centro de su grilla"]),
 ("R9 D4 recall 50 a 80 SIN EVIDENCIA (S147)", ["S147"], [
    r"recall (de )?50 ?(a|→|->) ?80", r"50→80", r"cierra D4"]),
 ("R10 serie continua FALSO (S146 V-15)", ["S146"], [r"serie continua"]),
 ("R11 A87 ejemplo SIN VERIFICAR (S146)", ["S146"], [r"482 p[ií]xeles"]),
 ("R12 A76 cita corrupta (S146 C-05)", ["S146"], [r"5 ?% tolerados", r"aleatorios en espacio"]),
 ("R13 Gaua no esta en SP426.5 (S146 V-07)", ["S146"], [r"Gaua"]),
 ("R14 D13 31 % son records, 70,7 % magnitud (S146)", ["S146"], [r"31 ?% de la magnitud", r"apaga el 31"]),
 ("CONTROL+ A83 AUC 0,859 (rebajada S146)", ["S146"], [r"AUC 0[.,]859"]),
 ("CONTROL- frase inventada", ["S999"], [r"zanahoria lunar"]),
]
def leer(p):
    try: return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception: return []
for titulo, tokens, pats in REBAJAS:
    print(f"\n### {titulo}")
    n_hits = n_marca = 0
    for p in ARCHIVOS:
        lineas = leer(p)
        for i, l in enumerate(lineas):
            if any(re.search(pt, l) for pt in pats):
                # pasaje envolvente: desde el hit hacia atras hasta el inicio de la regla o del encabezado (A113 b: la
                # marca va al inicio del pasaje), tope 80 lineas. El control positivo A83 obligo a ensanchar la ventana
                # de 3 lineas: su marca esta 6 lineas antes del numero.
                j = i
                while j > 0 and j > i - 80 and not re.match(r"^(#{1,4} |- \*\*A\d+\.|\| )", lineas[j]):
                    j -= 1
                ctx = " ".join(lineas[j:i+1])
                marca = ("⚠️" in ctx) or any(t in ctx for t in tokens)
                n_hits += 1; n_marca += marca
                rel = p.relative_to(ROOT) if ROOT in p.parents else ("memoria/" + p.name)
                print(f"  {'CON' if marca else 'SIN'} marca | {rel}:{i+1} | {l.strip()[:150]}")
    print(f"  -> hits {n_hits}, con marca {n_marca}, sin marca {n_hits - n_marca}")
