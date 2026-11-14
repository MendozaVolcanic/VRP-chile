# -*- coding: utf-8 -*-
"""V33B: escribe hallazgos.csv con el modulo csv (una fila por veredicto y por hallazgo propio).
Columnas: id,titulo,archivo_linea,confianza,gravedad,eje,comando_reproduccion,salida_cruda"""
import csv
import pathlib

C = pathlib.Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v33b")
T = r"C:\Users\nmend\vrp-temporales\s175_audit\v33b"
F2 = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f2"
ARBOL = T + r"\arbol_752d348bc"
FILAS = [
    ("V33B-209", "F2-209 verificado: el lector de la sombra V375-E no esta en 752d348bc ni en origin/main cc32ab1fc (si en loop/activo como _leer_sombra.py)",
     "experiments/_s168/v375e_sombra/leer_sombra_v375e.py (blob e720dbc46, tag s172-v375e-lector-resellado)", "CONFIRMADO", 2, "f2",
     "git ls-tree -r origin/main | grep e720dbc46; git merge-base --is-ancestor fc3912cb2 origin/main", str(C / "api_main_head.json")),
    ("V33B-255", "255 verificado: cinco filas de la cola §5 (D-1, D-19, D-23, D-37, D-39) siguen PENDIENTE/EN CURSO en 06de6876a, 395af8034 y 174bb691f",
     "tasks/LOOP_OBJETIVOS.md:526,528,540,543,545 (395af8034)", "CONFIRMADO", 2, "f3",
     "git show 395af8034:tasks/LOOP_OBJETIVOS.md | sed -n 526p;528p;540p;543p;545p; git log origin/main --oneline --grep='#892'", T + r"\255_filas_395af8034.txt"),
    ("V33B-211", "F2-211 verificado: 18 pasadas sin geometria de 1 MW o mas fuera del denominador protegido (14 Chillan), 2 no publicadas",
     "scripts/clase_mirova.py:25-28 (752d348bc)", "CONFIRMADO", 2, "f2",
     f"python {F2}\\sin_geometria.py {ARBOL} 2026-03-01 2026-11-07 <salida>", str(C / "sin_geometria_v33b_salida.txt")),
    ("V33B-213", "F2-213 verificado: Tupungatito 2026-09-28 05:18 (solo OCR, 2,51 MW) con la misma distancia y nota que la fila de las 05:36; C-04 abierto en base y main",
     "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv (filas 2026-09-28 05:18:00 y 05:36:01); docs/COLA_CAMPO.md:15", "CONFIRMADO", 2, "f2",
     "python: leer registro_vrp_ocr.csv del snapshot, Volcan Tupungatito, Fecha_Satelite_UTC 2026-09-28 05:*, columnas Distancia_km, Nota_Validacion, Distancia_aprox_imagen", str(C / "VERIFICACION.md")),
    ("V33B-308", "308 verificado por otro camino: 5 de 11 volcanes sin protegidas nocturnas en 2026-09-01..11-07 (6 de 11 con 60 dias; 3 de 11 desde marzo)",
     "experiments/_s175_audit/v33b/recontar_i10.py", "CONFIRMADO", 2, "f5",
     f"python {C}\\recontar_i10.py {ARBOL}", str(C / "recontar_i10_salida.txt")),
    ("V33B-208", "F2-208 verificado: parada = 30 noches con dato Y 40 alertas; noche 30 = 2026-12-02; con la vara 3 noches/9 alertas, con la tabla raiz 4/26",
     "leer_sombra_v375e.py:90,279-290 (tag s172-v375e-lector-resellado); pipeline/profiles/sombra_codigo_mirova.yaml:7", "CONFIRMADO", 1, "f2",
     f"GIT_DIR=<repo>/.git python experiments/_s168/v375e_sombra/leer_sombra_v375e.py --data-k {ARBOL}\\data\\mirova_equivalent --data-sombra {ARBOL}\\data\\sombra_codigo_mirova --cons <cons> --ocr <ocr> --hasta 2026-11-07 --commit 752d348bc --dir-salida <tmp>", str(C / "lector_v33b_snapshot_stdout.txt")),
    ("V33B-259", "259 verificado: el cierre de D25 en el catalogo cita la delegacion general D-48, no una frase sobre D25",
     "docs/MIROVA_DIVERGENCES.md:2863-2865 (752d348bc); tasks/LOOP_OBJETIVOS.md:3702-3704 (395af8034)", "CONFIRMADO", 1, "f3",
     "git show 752d348bc:docs/MIROVA_DIVERGENCES.md | sed -n 2861,2866p; git show 395af8034:tasks/LOOP_OBJETIVOS.md | sed -n 3700,3706p", str(C / "VERIFICACION.md")),
    ("V33B-260", "260 verificado: la frase «Si, los tres apagados» solo esta en la bitacora como «segun la sesion»; el commit 4164d4547 no la trae",
     "commit 4164d4547; tasks/LOOP_OBJETIVOS.md:2488 (395af8034)", "CONFIRMADO", 1, "f3",
     "git log -1 --format=%B 4164d4547; git grep -i 'tres apagados' origin/main", str(C / "VERIFICACION.md")),
    ("V33B-261", "261 en parte: sin frase en la bitacora, pero #895 lo mergeo la cuenta MendozaVolcanic (2026-10-22 11:29 UTC); la fila D-39 sigue PENDIENTE (se funde con 255)",
     ".github/workflows/sync-mirova-csv.yml:90-102 (752d348bc); tasks/LOOP_OBJETIVOS.md:526,3945 (395af8034)", "CONFIRMADO EN PARTE", 1, "f3",
     "gh api repos/MendozaVolcanic/VRP-chile/pulls/895 --jq '{merged_by: .merged_by.login, merged_at: .merged_at}'", str(C / "api_pr895.json")),
    ("V33B-262", "262 verificado: decision 3 decia «a menos de 4 km del vecino»; #935 implemento max(4 km, inner) por V935-01; sin frase de Nicolas sobre el radio",
     "tasks/LOOP_OBJETIVOS.md:959,933,951-952 (06de6876a); squash 438a010ab; tests/test_vecinos_sombra_34_s173.py", "CONFIRMADO", 1, "f3",
     "git show --format=%B 438a010ab | head -30; git show 06de6876a:tasks/LOOP_OBJETIVOS.md | sed -n 959p", str(C / "VERIFICACION.md")),
    ("V33B-263", "263 verificado: al sellar se agrego la cabecera y cambio una linea del cuerpo («Falta la frase ... (dada, ver la cabecera)»); el archivo sigue BORRADOR en base y main",
     "experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md (3a3b5e495 vs 752d348bc)", "CONFIRMADO", 1, "f3",
     r"python experiments\_s175_audit\f3\sello_regla_modd.py", str(C / "sello_regla_modd_v33b_salida.txt")),
    ("V33B-264", "264 verificado: check pytest failure en c666ab08f; squash c8152580b solo en origin/claude/s162-viirs750-2-918174; la causa (test_csv_max_age_under_48h) no verificada",
     "tasks/LOOP_OBJETIVOS.md:657 (395af8034); commit c8152580b", "CONFIRMADO", 1, "f3",
     "gh api repos/MendozaVolcanic/VRP-chile/commits/c666ab08f/check-runs; git merge-base --is-ancestor c8152580b origin/main", str(C / "api_checks_c666ab08f.json")),
    ("V33B-265", "265 en parte: #945 ya esta en el indice de memoria (corregido tras la auditoria); #950 y #951 siguen sin aparecer en MEMORY.md ni en project_s174_estado.md",
     r"C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\memory\MEMORY.md:28; project_s174_estado.md", "CONFIRMADO EN PARTE", 1, "f3",
     "grep -c -E '#950|#951' <memoria>/MEMORY.md <memoria>/project_s174_estado.md", str(C / "VERIFICACION.md")),
    ("V33B-310", "310 verificado: Lastarria V375 mediana por noche 0,664 (n 15, bajo) contra misma pasada 0,712 (n 13, en banda); invisible por UNDER_BAND_KNOWN",
     "scripts/auto_audit_weekly.py:145,161 (752d348bc); f5_medir_out.json I4", "CONFIRMADO", 1, "f5",
     f"python {T}\\f5_copia\\f5_medir_copia.py (copia de f5/f5_medir.py con OUT cambiado)", T + r"\f5_copia\f5_medir_out.json"),
    ("V33B-210", "F2-210 en parte: las dos protegidas de marzo no tienen record a 120 s (reproducido), pero son filas solo OCR v21 pre-hito 2026-06-11 cuyas horas no estan en la tabla de MIROVA; pasada real SIN DATO",
     "scripts/banco_paridad.py:78; data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv (Lascar 2026-03-11 06:18, Isluga 2026-03-10 04:54)", "CONFIRMADO EN PARTE", 1, "f2",
     f"python {F2}\\f2_banco_v375.py {ARBOL} 2026-03-01 2026-11-07 <prefijo>", str(C / "banco_v33b_0301_1107_salida.txt")),
    ("V33B-01", "Hallazgo propio: las filas OCR de Tupungatito 2026-09-28 05:18 y 05:36 comparten Distancia_aprox_imagen del 2026-10-22 (metodo ambiguo)",
     "registro_vrp_ocr.csv columnas Distancia_aprox_imagen, Distancia_aprox_metodo", "CONFIRMADO", 1, "f2",
     "python: leer registro_vrp_ocr.csv del snapshot, filas Tupungatito 2026-09-28 05:*", str(C / "VERIFICACION.md")),
    ("V33B-02", "Hallazgo propio: alerta_protegida acepta filas solo OCR anteriores al hito 2026-06-11 (A119), asi que el recall de marzo se mide contra OCR mal calibrado",
     "scripts/clase_mirova.py:20-28; docs/audit_s139/MAPA_BASES_MIROVA_V1.md seccion 2 (citado por banco_paridad en stderr)", "SOSPECHA", 2, "f2",
     f"python {F2}\\f2_banco_v375.py {ARBOL} 2026-03-01 2026-11-07 <prefijo> (PROTEGIDAS SIN RECORD, src OCR, fecha marzo)", str(C / "banco_v33b_stderr.txt")),
    ("V33B-03", "Hallazgo propio: el lector de la sombra no corre desde un arbol suelto (exige resolver origin/loop/activo con git y el arbol entero del tag)",
     "leer_sombra_v375e.py:812-816,163 (tag s172-v375e-lector-resellado)", "CONFIRMADO", 1, "f2",
     "python experiments/_s168/v375e_sombra/leer_sombra_v375e.py ... desde git archive sin .git: rc 2", str(C / "VERIFICACION.md")),
]
with open(C / "hallazgos.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    for f in FILAS:
        w.writerow(f)
print("filas:", len(FILAS), "->", C / "hallazgos.csv")
