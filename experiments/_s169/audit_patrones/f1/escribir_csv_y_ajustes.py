# Auditoría S169 f1: ajusta dos citas del INFORME.md y escribe hallazgos.csv con el módulo csv (un campo con comas sin
# comillas correría las columnas sin dar error). Solo escribe en esta carpeta.
import csv
from pathlib import Path

D = Path(__file__).resolve().parent
p = D / "INFORME.md"
s = p.read_text(encoding="utf-8")
s = s.replace("`experiments/_s162_v750a/equivalencia_v750a.py:195-199`", "`experiments/_s162_v750a/equivalencia_v750a.py:196-200`")
s = s.replace('- `analizar_v750b.py:23`/`adenda3`: la lista "aparte" de N-3 sale de `oks`, es decir sin las pasadas con K distinto de producción (`analizar_v750b.py:298`); una N-3 con K distinto no se lista. Gravedad 1, SOSPECHA.',
              '- Adenda 3, reemplazo 3 de `adenda3/leer_n3_v750b.py:82-92`: la lista aparte de N-3 sale de `oks`, es decir sin las pasadas con K distinto de producción (`analizar_v750b.py:298`); una N-3 con K distinto no se lista. Gravedad 1, SOSPECHA.')
s = s.replace("- Aviso de 'estado del equipo': C: libre 18 GB y D: libre 19 GB al empezar (sobre el umbral de 3 GB), no los toqué.",
              "- Estado del equipo: C: con 18 GB libres y D: con 19 GB libres al empezar (sobre el umbral de 3 GB); no hubo parada.")
p.write_text(s, encoding="utf-8")

F = [
 ("P1-01", "El lector del 2026-11-03 corre desde un worktree atrasado y evalua 'publica' con el tablero de ese worktree, no con el de main del dia", "experiments/_s162_v750b/r4/INFORME.md:70-71; analizar_v750b.py:36-42", "CONFIRMADO estructura; SOSPECHA efecto", 3, "P-C/P-E", "git -C <repo> rev-list --count claude/s162-viirs750-2-918174..origin/main (1446); diff de frontend/index.html rama vs main", "diff_clase_mirova_rama_vs_main.txt"),
 ("P1-02", "--leer-con-faltantes abre la compuerta aunque el control del censo haya corrido y FALLADO", "experiments/_s162_v750b/analizar_v750b.py:414 (texto PREREGISTRO_V750B.md:212-214)", "CONFIRMADO (leido, no ejecutado)", 3, "P-G", "analizar_v750b.py ... --leer-con-faltantes x con una escena donde el censo da DISTINTO", "(lectura de codigo; sin salida)"),
 ("P1-03", "La poblacion del generador depende de VRP_PROFILE del shell; R4 §3 no lo fija ni lo imprime", "scripts/banco_paridad.py:60; scripts/auto_audit_weekly.py:249-254; pipeline/diurno.py; pipeline/profiles/_s154_ab_diurno_k_on.yaml:15", "CONFIRMADO cadena; SOSPECHA efecto", 3, "P-E", "VRP_PROFILE=_s154_ab_diurno_k_on python experiments/_s162_v750b/objetivos_v750b.py --data <main> --ref-dest <c> --hasta 2026-10-29 (SIN DATO: no ejecutado)", "(sin salida: SIN DATO)"),
 ("P1-04", "El generador no avisa si --data es viejo o incompleto", "experiments/_s162_v750b/objetivos_v750b.py:89-127; r4/INFORME.md:25-26", "CONFIRMADO", 3, "P-E/P-F", "max(datetime_utc) por volcan de data/mirova_equivalent contra 2026-11-02 12:59 (comprobacion que falta)", "(lectura de codigo; sin salida)"),
 ("P1-05", "El veredicto no registra la identidad de sus insumos, se puede releer con otros argumentos y la salida se pisa", "analizar_v750b.py:185,198-200,203-204; adenda3/leer_n3_v750b.py:149-152; PREREGISTRO_V750B.md:211", "CONFIRMADO", 3, "P-B/P-F", "grep -n sha256 analizar_v750b.py; correr dos veces con el mismo --salida", "(lectura de codigo; sin salida)"),
 ("P1-06", "Regla N-3 corta por fecha 2026-10-09 pero el arreglo del OCR de Suomi NPP fue el 2026-10-09 14:01 UTC", "adenda3/leer_n3_v750b.py:61-64; ADENDA3_V750B.md §1-2; r4/ensayo_20261029/gen1_salida.txt", "SOSPECHA", 2, "P-G", "contar en la lista real protegida sin alerta_tabla, VIIRS_SNPP_750, hora_utc que empieza con 2026-10-09", "(sin salida: requiere la lista del dia)"),
 ("P1-07", "El pre-registro promete informar por tramo #535 y adopcion de K; el analizador solo estratifica por cenit", "PREREGISTRO_V750B.md:106; analizar_v750b.py:485-495", "CONFIRMADO", 2, "P-G", "grep -n '535|2026-10-18|adopci' experiments/_s162_v750b/analizar_v750b.py (vacio)", "(lectura de codigo; sin salida)"),
 ("P1-08", "Con y sin FALSO_POSITIVO prometido en el pre-registro; el arreglo (#903) esta en main y nada informa con y sin", "PREREGISTRO_V750B.md:112-113; scripts/clase_mirova.py (main 443da8649); experiments/_s159/n/01_poblacion.py:111", "CONFIRMADO condicion; SOSPECHA efecto", 2, "P-G", "git log origin/main --oneline --grep='#903'; grep -n FALSO_POSITIVO analizar_v750b.py (vacio)", "(lectura de codigo; sin salida)"),
 ("P1-09", "El analizador hashea el evaluador sobre bytes crudos (sin normalizar CRLF) y R4 no da receta de la copia", "analizar_v750b.py:67-68; r4/INFORME.md:70", "CONFIRMADO codigo; SOSPECHA uso", 2, "P-A", "python -I verificar_shas_selladas.py; sha256sum D:/vrp-trabajo/temporales/evaluar_d25_s161.py", "verificar_shas_selladas_salida.txt"),
 ("P1-10", "Protegida fuera del granulo o sin crater sale de P1 sin frenar la lectura; el probe sale 0", "probe_v750b.py:149-151,277-278; analizar_v750b.py:152-160,228-233", "SOSPECHA", 2, "P-F", "leer la linea 'protegidas no observadas' de la salida real antes del veredicto", "(sin salida: requiere el run)"),
 ("P1-11", "V750-A: la parte local del §6.1 se lee de un archivo de texto sin atarlo al modulo ni al commit", "experiments/_s162_v750a/evaluar_v750a.py:240-258", "CONFIRMADO", 2, "P-C/P-B", "PYTHONIOENCODING=utf-8 python -I forjar_equivalencia_local.py", "forjar_equivalencia_local_salida.txt"),
 ("P1-12", "V750-A: el medidor de mutaciones nunca corrio completo contra la bateria actual (77 escenarios, M1 a M85)", "mutar_evaluar_v750a.py:38-234; PREREGISTRO_V750A.md:284-286", "CONFIRMADO", 2, "P-F", "grep -l 'M81|M85' experiments/_s162_v750a/*.txt (vacio)", "mutar_evaluar_v750a_posicion_salida.txt"),
 ("P1-13", "Rama de la ROI: la prueba no cubre main(); 5 de 10 mutaciones propias no atrapadas; '4 mutaciones atrapadas' sin instrumento en la rama", "scripts/roi_v750b_a_grillas.py:64-76; tests/test_roi_v750b_variantes_s169.py", "CONFIRMADO", 2, "P-D", "PYTHONIOENCODING=utf-8 python -I mutar_roi_propio.py", "mutar_roi_propio_salida.txt"),
 ("P1-14", "Los dos generadores bajan la referencia viva de Mirova-v1 por separado; el control puede caer o mezclar referencias", "adenda2/objetivos_supl_v750b.py:115-120,152-161; objetivos_v750b.py:95-99", "SOSPECHA", 2, "P-B/P-E", "comparar 'referencia remota' de gen1_salida.txt y gen2_salida.txt", "(sin salida)"),
 ("P1-15", "poblacion_completa.json lleva data_records escrito a mano (533398f8f) que no corresponde al --data", "experiments/_s159/n/01_poblacion.py:144-146 (main 443da8649)", "CONFIRMADO", 1, "P-F", "git show 443da8649:experiments/_s159/n/01_poblacion.py | sed -n 144,146p", "(lectura de codigo; sin salida)"),
 ("P1-16", "En Windows poblacion_completa.json y poblacion_supl.json salen con CRLF y su sha256 no es el del texto (latente)", "01_poblacion.py:143-147; adenda2/objetivos_supl_v750b.py:162; r4/armar_rama_disparo.sh:36-38", "CONFIRMADO", 1, "P-A", "PYTHONIOENCODING=utf-8 python -I crlf_generadores.py", "crlf_generadores_salida.txt"),
 ("P1-17", "Aplicar la ROI dos veces deja el comentario del YAML diciendo otro brazo", "scripts/roi_v750b_a_grillas.py:56-60", "CONFIRMADO", 1, "P-F", "PYTHONIOENCODING=utf-8 python -I roi_doble_aplicacion.py", "roi_doble_aplicacion_salida.txt"),
 ("P1-18", "equivalencia_v750a.py llama no existe todavia a cualquier ImportError, incluido uno interno del candidato", "experiments/_s162_v750a/equivalencia_v750a.py:196-200", "CONFIRMADO", 1, "P-F", "lectura de codigo", "(lectura de codigo; sin salida)"),
 ("P1-19", "mutar_bateria.py (V750-B) cuenta ATRAPADA sin exigir el codigo de salida 1", "experiments/_s162_v750b/mutar_bateria.py:90-95", "SOSPECHA", 1, "P-D", "lectura de codigo", "(lectura de codigo; sin salida)"),
]
with open(D / "hallazgos.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    for r in F:
        r = list(r)
        if not r[7].startswith("("):
            r[7] = str(D / r[7])
        w.writerow(r)
rows = list(csv.reader(open(D / "hallazgos.csv", encoding="utf-8")))
print(len(rows) - 1, "filas; columnas por fila:", {len(r) for r in rows})
