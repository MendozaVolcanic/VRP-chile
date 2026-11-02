# -*- coding: utf-8 -*-
"""hallazgos.csv con el modulo csv (un campo con comas sin comillas corre las columnas sin dar error)."""
import csv
from pathlib import Path

C = Path(__file__).parent
F = [
    ("VPR2-01", "Inventario (b) del §3.1 incompleto: Lastarria MODIS 2026-02-24 07:05 (negativo publicado por K) y siete pasadas de 2025 miradas por nombre", "PREREGISTRO_copia.md:129-137,397; origin/main:experiments/_s159/m/INFORME.md:49-51,78; experiments/_s162_vuelta2/CUMULOS_POR_MATRIZ.md:15,64,66", "CONFIRMADO", 3, "fuera de muestra", "git grep -n 'Lastarria.\\{0,40\\}2026-02-24 07:05' origin/main -- experiments; python contar_f26.py <export> 2026-02-01 2026-02-28 F26M", "contar_f26_F26M_bloques_modis.txt; febrero_pasadas_nombradas.txt; pasadas_2025_nombradas.txt"),
    ("VPR2-02", "SIN SUSTRATO de P2 cumple en V375-E §9.7 pero cae en la fila 5 (SIN PODER): dos lectores, dos veredictos; en 750 no esta mapeado", "PREREGISTRO_copia.md:418,275; s170-v375e-lector:experiments/_s162_v375/PREREGISTRO_E.md §9.7 fila (b); aa5583646:experiments/_s162_v750a/PREREGISTRO_V750A.md:232-233", "CONFIRMADO", 2, "reglas computables", "git show s170-v375e-lector:experiments/_s162_v375/PREREGISTRO_E.md | sed -n '/^### 9\\.7/,+40p' | grep -n 'SIN SUSTRATO'", "cita_v375e_s53.txt"),
    ("VPR2-03", "'Veta' significa fila 2 en F26 y fila 4 en R25; C-cobertura lo usa sin tramo", "PREREGISTRO_copia.md:355,356,415,417", "CONFIRMADO", 2, "reglas computables", "leer las cuatro lineas", "PREREGISTRO_copia.md"),
    ("VPR2-04", "Placebo 'M no da MEJORA': K x 1,2 da MEJORA por d con K/MIROVA < 0,83 si no se exige d' (D-28); en 750 'MEJORA' no existe", "PREREGISTRO_copia.md:361; evaluar_d25_blob_1dbabf65.py:245-253; origin/main:experiments/_s157_prereg_d25/ADENDA_PLACEBO.md:15,55; aa5583646:PREREGISTRO_V750A.md:234-236", "CONFIRMADO", 2, "controles", "python -c \"import math; print(abs(math.log10(0.78))-abs(math.log10(0.65)))\"", "evaluar_d25_blob_1dbabf65.py"),
    ("VPR2-05", "Protegidas MODIS del OSF son 161, no 162: la de Villarrica 2025-03-26 13:55 es diurna con la noche del proyecto; 'una de 1 MW o mas' son tres; sin Lascar 6 (50 %)", "PREREGISTRO_copia.md:225,226,238-240,384", "CONFIRMADO", 2, "poder", "python contar_osf.py <export> <OSF csv> vent", "contar_osf_vent_salida.txt; contar_osf_centro_salida.txt"),
    ("VPR2-06", "C-K y nulo del runner admiten excepciones 'nombradas' sin tope: control que no puede fallar", "PREREGISTRO_copia.md:357,362", "CONFIRMADO", 2, "controles", "leer las dos lineas", "PREREGISTRO_copia.md"),
    ("VPR2-07", "Texto de V750-A a aplicar 'como anexo no verificado' sin commit ni lineas", "PREREGISTRO_copia.md:276,124; aa5583646:experiments/_s162_v750a/PREREGISTRO_V750A.md:174-243", "CONFIRMADO", 2, "reglas computables", "git show aa5583646:experiments/_s162_v750a/PREREGISTRO_V750A.md | grep -n '^## 6'", "cita_v750a_secciones.txt; cita_v750a_s6.txt"),
    ("VPR2-08", "R-2, R-3, R-6, R-8, R-11 y R-12 no se contestan con 'si' sin ambiguedad", "PREREGISTRO_copia.md:552,553,556,558,561,562", "CONFIRMADO", 2, "decisiones R", "leer la tabla del §12", "PREREGISTRO_copia.md"),
    ("VPR2-09", "C-montaje decide con 'cada diferencia se explica', sin criterio computable", "PREREGISTRO_copia.md:358", "CONFIRMADO", 2, "controles", "leer la linea", "PREREGISTRO_copia.md"),
    ("VPR2-10", "'Marzo lo toca solo MOD-D' omite la V2 de K; D25 ausente del inventario (no toca F26 ni 2025)", "PREREGISTRO_copia.md:127; origin/main:experiments/_s151_prereg_fk_11/PREREGISTRO.md:99-102; docs/PREREGISTRO_AB_D22_D25_S143.md:89,91", "CONFIRMADO", 1, "fuera de muestra", "git show origin/main:experiments/_s153_fk_v2/v2.log | sed -n 15p", "cita_k_prereg_l85_105.txt; cita_fk_v2_marzo.txt"),
    ("VPR2-11", "Composicion por satelite del §3.3 (800/132/163; 855/200) no se reproduce con SN y Tupungatito desde 02-23 (790/111/162; 844/198)", "PREREGISTRO_copia.md:178-180", "CONFIRMADO EN PARTE", 1, "poder", "python contar_f26.py <export> 2026-02-01 2026-03-31 F26", "contar_f26_F26_salida.txt"),
    ("VPR2-12", "Citas SIN LOCALIZAR: '27 pasadas contra 48 bloques; V375-E l. 66 a 68' y 'port de V750 0,994 a 0,998'", "PREREGISTRO_copia.md:357,64-65; s170-v375e-lector:PREREGISTRO_E.md:66-68; origin/loop/activo:experiments/_s172_chillan/verificador/INFORME.md:28", "CONFIRMADO", 1, "citas", "git show s170-v375e-lector:experiments/_s162_v375/PREREGISTRO_E.md | grep -n -E '27 pasadas|48 bloques'", "cita_v375e_ventana.txt"),
    ("VPR2-13", "§5.3 omite NULO SESGADO y el nulo de 8 noches; fila 4 hace decidir a la curva donde V375-E §9.7 dice que en retrospectiva solo informa (desviacion no declarada en §5.6)", "PREREGISTRO_copia.md:308-310,417; s170-v375e-lector:PREREGISTRO_E.md §5.3 y §9.7", "CONFIRMADO", 1, "reglas computables", "git show s170-v375e-lector:experiments/_s162_v375/PREREGISTRO_E.md | sed -n '/^### 5\\.3/,+12p'", "cita_v375e_s53.txt"),
    ("VPR2-14", "Regla del tres supone independencia entre noches consecutivas de Lascar; cifras del §7 aun no recalculadas por el autor con sha", "PREREGISTRO_copia.md:376-386,403-404", "CONFIRMADO", 1, "poder", "contar_f26.py y contar_osf.py", "contar_f26_F26_salida.txt; contar_f26_F26M_salida.txt; contar_osf_vent_salida.txt"),
]
with open(C / "hallazgos.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    for f in F:
        w.writerow(f)
print("hallazgos.csv:", len(F), "filas")
