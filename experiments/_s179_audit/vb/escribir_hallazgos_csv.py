# -*- coding: utf-8 -*-
"""Escribe hallazgos.csv del verificador VB con el módulo csv (campos con comas entre comillas).
Rutas armadas con os.path.join sobre cadenas crudas: una barra invertida suelta ante t, r o b se vuelve un carácter
de control (le pasó a la primera versión de este script: 3 filas con tabulador)."""
import csv
import os

V = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vb"
T = r"D:\vrp-trabajo\temporales\s179-audit\vb"
INS = r"D:\vrp-trabajo\temporales\s179-audit\insumos"
DATOS_B = r"D:\vrp-trabajo\temporales\s179-audit\b\datos"


def v(nombre):
    return os.path.join(V, nombre)


def t(nombre):
    return os.path.join(T, nombre)


F = [
    ("451", "Plazo de 29 protegidas se agota en 11 a 13 días, casi sólo Chillán (más 2 o 3 de Cordón Caulle): CONFIRMADO EN PARTE",
     "scripts/vigilancia_guardia_modis.py:228-237,327 (438a60a1e)", "CONFIRMADO EN PARTE", 3, "B",
     'python "' + v("sim_ventana_16d78.py") + '"', v("sim_ventana_16d78_salida.txt")),
    ("454+DEC-15", "Cinco condiciones de la regla §5 sin hacer; paso de nrt.yml para VIIRS movido a después del merge sin frase de Nicolás: CONFIRMADO",
     ".github/workflows/nrt.yml:373-384; scripts/revisar_errores_modis_nrt.py:12-13 (438a60a1e); tasks/LOOP_OBJETIVOS.md:645 (0472cd95e)",
     "CONFIRMADO", 3, "B", "sed -n 373,384p .github/workflows/nrt.yml; sed -n 640,646p tasks/LOOP_OBJETIVOS.md", v("INFORME_VB.md")),
    ("456", "Salto de magnitud vía/K el día del encendido: mediana por volcán 0,44 a 4,09 (no 1,3 a 3,2); el tablero sólo dibuja una línea: CONFIRMADO EN PARTE",
     "frontend/cambio_detector.js:284-293 (438a60a1e); docs/superpowers/specs/2026-11-08-encendido-v375e-design.md:60 (0472cd95e)",
     "CONFIRMADO EN PARTE", 3, "B", 'python "' + v("magnitud_via_k.py") + '" ' + DATOS_B + " 2026-11-03 2026-11-09",
     v("magnitud_via_k_438a60a1e_salida.txt")),
    ("452", "Cota (i) de VIIRS 375 bajo lo observado: 3,7 a 4,9 veces según denominador y ventana, sobre 3 casos (p 0,02 a 0,05): CONFIRMADO EN PARTE",
     "scripts/vigilancia_guardia_viirs.py:73 (438a60a1e); regla l. 92", "CONFIRMADO EN PARTE", 2, "B",
     'python "' + v("tasa_por_pasada_452.py") + '"', v("tasa_por_pasada_452_salida.txt")),
    ("453+DEC-6", "Falsa alarma de las cotas con incertidumbre de la tasa: 9 a 40 % según el modelo (Jeffreys 12 a 28 %); cota (ii) de VIIRS 750 de 1 caso: CONFIRMADO EN PARTE (la regla l. 98 ya lo declara)",
     "experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md:88-98 (438a60a1e)", "CONFIRMADO EN PARTE", 2, "B",
     'python "' + v("cotas_sensibilidad.py") + '"', v("cotas_sensibilidad_salida.txt")),
    ("455", "Protegidas probadas con la vía: 6 volcanes sin ninguna en VIIRS 375 y 7 en VIIRS 750; también Cordón Caulle y Planchón-Peteroa aportan: CONFIRMADO EN PARTE",
     "experiments/_s178_lectura/lectura.json (ff8a39972) sensores.*.lectura_b, osf.por_sensor", "CONFIRMADO EN PARTE", 2, "B",
     'python "' + v("protegidas_por_volcan.py") + '"', v("protegidas_por_volcan_salida.txt")),
    ("457", "Revert de B1 con B2 adentro choca en 11 archivos (no 9); perfiles limpios; resolución no ensayada: CONFIRMADO EN PARTE",
     "cuerpo de #974 y #983; simulación git merge-tree con objetos privados", "CONFIRMADO EN PARTE", 2, "B",
     "git merge-tree --write-tree --name-only --merge-base=f0eb9bbe e68819484 1028c78f8 (GIT_OBJECT_DIRECTORY privado)",
     t("mt_paso2_revert_B1_tras_B2.txt")),
    ("460", "La vía no escribe record en 11 de 223 pasadas V375 (4,9 %); una Muy Bajo ahí no entra a ninguna cota; 0 casos con alerta en 8 noches: CONFIRMADO",
     "pipeline/process_viirs.py:773-774,781-782; scripts/vigilancia_guardia_modis.py:252-254,280-294,318 (438a60a1e)", "CONFIRMADO", 2, "B",
     'python "' + v("re_detalle_sombra.py") + '"', v("re_detalle_sombra_salida.txt")),
    ("463", "Lector de V375-E fuera de main, ningún workflow lo corre, su brazo K es data/mirova_equivalent (lo pierde con B1): CONFIRMADO",
     "regla l. 29,44; docs/AUDIT_S175.md:216,272 (37670d910); leer_sombra_v375e.py l. 25,76,93 (tag s172-v375e-lector-resellado)",
     "CONFIRMADO", 2, "B", "git cat-file -e 438a60a1e:experiments/_s168/v375e_sombra/leer_sombra_v375e.py", t("leer_sombra_v375e_tag.py")),
    ("DEC-19", "Veredicto fila 4 de VIIRS 750 sin frase de Nicolás; D5 quita uno de sus dos motivos: CONFIRMADO",
     "experiments/_s178_lectura/lectura.json (ff8a39972); tasks/BLOQUE_ARRANQUE_S179.md:19,39 (0472cd95e)", "CONFIRMADO", 2, "B",
     "git show ff8a39972:experiments/_s178_lectura/lectura.json", t("lectura_ff8a39972.json")),
    ("VB-01", "Datos de la guardia K de VIIRS anteriores al 11-11 salen de una sola ejecución manual con conclusión failure; la primera programada falló en 11 de 11; primera programada verde 2026-11-11 00:12 UTC",
     "insumos runs_guardia-k-viirs.json; git log origin/main -- data/guardia_k_viirs; regla l. 132",
     "CONFIRMADO (causa de la falla: SOSPECHA)", 2, "B", "gh run view 42742205624 --repo MendozaVolcanic/VRP-chile --json jobs",
     t("run_42742205624.json")),
    ("461", "Guardia y respaldo de la vigilancia corren pasada la medianoche UTC (4,6 y 6,8 h; 3,4 y 5,5 h); la regla l. 68 ata el plazo a quien lee el aviso: CONFIRMADO EN PARTE",
     "regla l. 68; .github/workflows/guardia-k-viirs.yml:7,16-19 (438a60a1e)", "CONFIRMADO EN PARTE", 1, "B",
     "leer " + os.path.join(INS, "runs_guardia-k-viirs.json"), os.path.join(INS, "runs_guardia-k-viirs.json")),
    ("458", "#974, #983 y #975 chocan con main sólo en la ficha; CI anterior a #982 y #984; tres numeraciones de la ficha: CONFIRMADO",
     "docs/FICHA_SDA_VRP_CHILE.md (438a60a1e, bbbe2068d, e68819484); tasks/LOOP_OBJETIVOS.md:576,582", "CONFIRMADO", 1, "B",
     "git merge-tree --write-tree --name-only 438a60a1e bbbe2068d (objetos privados)", t("mt_bbbe2068d_sobre_438a60a1e.txt")),
    ("DEC-14", "Quita los 3: se quitaron 5 avisos (incluidos los de VIIRS aún no visibles); el cuerpo de #984 lo dijo y Nicolás mergeó: CONFIRMADO EN PARTE",
     "frontend/cambio_detector.js:284-293 (438a60a1e); tasks/LOOP_OBJETIVOS.md:576,593 (0472cd95e); cuerpo de #984", "CONFIRMADO EN PARTE", 1, "B",
     "gh pr view 984 --repo MendozaVolcanic/VRP-chile --json body", t("pr_984.json")),
]
with open(v("hallazgos.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "titulo", "archivo_linea", "confianza", "gravedad", "eje", "comando_reproduccion", "salida_cruda"])
    w.writerows(F)
print("filas", len(F))
