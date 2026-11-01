# -*- coding: utf-8 -*-
"""S160 F4: arma propagacion.csv desde propagacion_grep_salida.txt mas las filas comprobadas a mano (README de main,
pendientes U1 a U13 de AUDIT_S158_R2 que solo existen en loop/activo, A118 en CLAUDE.md)."""
import re, csv
rows = []
sec = None
for l in open('propagacion_grep_salida.txt', encoding='utf-8'):
    if l.startswith('### '):
        sec = l[4:].strip(); continue
    m = re.match(r'  (CON|SIN) marca \| ([^|]+):(\d+) \| (.*)', l)
    if m and sec:
        rows.append([sec, m.group(2).strip().replace(chr(92), '/'), m.group(3),
                     'con marca' if m.group(1) == 'CON' else 'SIN marca',
                     'main d516b9d8c (instantanea) o memoria', m.group(4).strip()[:140]])
R1 = "R1 K en produccion (S153/#850; marcas S153 y S157)"
R15 = "R15 S158 codigo MIROVA V750 (D34) "
manual = [
 (R1, "README.md", "54", "SIN marca", "main d516b9d8c", "and the **integrated-ROI Test 1** for spatially-extended sub-pixel anomalies"),
 (R1, "README.md", "92", "SIN marca", "main d516b9d8c", "test1_integrated.py  Integrated-ROI Test 1 (sub-pixel detection)"),
 (R1, "README.md", "131", "SIN marca", "main d516b9d8c", "integrated-ROI **Test 1** that sums the MIR excess over the 3 km summit ROI and fires"),
 (R1, "README.md", "220", "SIN marca", "main d516b9d8c", "integrated Test 1 can drift ~1 km toward warm low-altitude terrain"),
 (R15 + "U1", "docs/MIROVA_DIVERGENCES.md", "3314", "SIN marca", "loop/activo 60762a939; NO existe en main", "Alcance: solo VIIRS 750. La estructura se puede trasladar a MODIS y VIIRS 375 con cita (F4-H6 de S158 lo refuto)"),
 (R15 + "U1", "docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md", "189;281", "SIN marca", "loop/activo; NO existe en main", "se puede trasladar a MODIS y VIIRS 375"),
 (R15 + "U2", "CLAUDE.md", "123-126", "marca sin limites", "loop/activo; en main la linea no existe", "marca S158 sin los limites del codigo (repositorio compacto, escalon de 50 grados, Etna no ejercita umbrales)"),
 (R15 + "U3", "docs/MIROVA_DIVERGENCES.md", "2385", "SIN marca", "loop/activo (main: 2337)", "D18 encabezado: caja de 5 km igual para todos (el codigo adapta la ROI por volcan, H:120-125)"),
 (R15 + "U4", "docs/MIROVA_DIVERGENCES.md", "2875", "encabezado SIN marca; cuerpo con marca en 2879-2881", "loop/activo (main: 2811 sin marca)", "D27 encabezado K1 = -0,6; el codigo V750 usa -0,5 y rechaza reflejo < 12 grados"),
 (R15 + "U4", "pipeline/diurno.py;experiments/_s151_ab_diurno/PREREGISTRO.md", "128;18", "SIN marca", "loop/activo y main", "K1 diurno -0,6 (A45 para diurno.py; prereg sellado: adenda)"),
 (R15 + "U4", "tests/test_rama_diurna_viirs_s151.py", "114", "con marca (S158 R2)", "loop/activo", "K1 = -0,6 es la Tabla 1 de MODIS"),
 (R15 + "U5", "docs/MIROVA_DIVERGENCES.md", "1303-1309", "con marca (S158 R2)", "loop/activo (main: 1285 sin marca S158)", "D8 RESUELTO con kernel L1129 literal"),
 (R15 + "U8", "docs/MIROVA_DIVERGENCES.md", "1104", "SIN marca", "loop/activo (main: 1086)", "scene=0.010 (Coppola 2016a Table 2): el codigo usa 0,02 fuera de la cumbre y la tabla del paper es la 1"),
 (R15 + "U8", "CLAUDE.md", "152;181", "SIN marca", "loop/activo (main: 138;161)", "kernel 8-vec aritmetico / Kernel 8-vecinos, Drift D1 RESUELTO S17: el codigo usa 3x3 con el central"),
 (R15 + "U8/F2-H3", "CLAUDE.md", "205 (main)", "SIN marca", "main y loop/activo", "A4: no hay mascaras geometricas ni radios adaptativos (H:120-131 del codigo admite exclusion por pixel)"),
 (R15 + "F2-H3", "docs/MISSION.md", "290 (main)", "SIN marca", "main y loop/activo", "exclude_zones: No en papers; MIROVA no usa mascaras geograficas"),
 (R15 + "U9", "experiments/_s157_prereg_d25/RESUMEN_SELLO.md", "3", "SIN marca (sellado: adenda)", "main", "restar la media de los vecinos del crater (lo que hace MIROVA, D25)"),
 (R15 + "U10", "experiments/50_FACTOR_42_HALLAZGO.md", "1;42-50", "SIN marca", "main", "n_hotspots como regiones contiguas (F2-H1 lo refuto)"),
 (R15 + "U11", "documentacion/BIBLIOGRAPHY_SYNTHESIS.md (fuera de git)", "142;248;249", "SIN marca", "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/documentacion/", "VIIRS 750: n=12 nocturno, n=8 diurno (Di Bella 2024) presentado como canonico"),
 (R15 + "U12", "memoria/reference_mirova_daytime_cloud_artifact.md;memoria/feedback_mirova_no_human_supervision.md", "29;37", "SIN marca", "memoria del agente", "MIROVA limpia estos FP por SUPERVISION MANUAL (el codigo rechaza reflejo < 12 grados automaticamente)"),
 (R15 + "U13", "docs/DISENO_D17_REMUESTREO_UTM.md", "282", "desactualizada", "loop/activo; NO existe en main", "pendiente del verificador (V3 ya confirmo la rebaja)"),
 (R15 + "F2-H8", "pipeline/detection_context.py", "974-984", "SIN marca (A45)", "main y loop/activo", "Test 1 K1 es MASCARA DE SATURACION, NO un path de deteccion reportable (el codigo de MIROVA lo publica como alerta)"),
 ("R2 historico reemplazado por K (S158 #883, en main; frontera 2025-02-15)", "memoria/project_s155_estado.md;memoria/feedback_s155_marca_en_los_datos.md", "19;13", "SIN marca", "memoria del agente", "la marca del cambio de detector va en la fecha de observacion 2026-09-18"),
 ("R8 D18 medida en S151 (KC NO CUMPLE; MIROVA mide desde el centro de grilla)", "CLAUDE.md", "1530", "SIN marca", "main d516b9d8c", "A118: D18 nunca se ha medido, y el NO ADOPTAR de S130 probablemente salio de este mismo defecto (S151 la midio: KC NO CUMPLE, veto)"),
]
rows += [list(m) for m in manual]
with open('propagacion.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['rebaja', 'archivo', 'linea', 'marca', 'donde', 'texto_del_hijo'])
    w.writerows(rows)
print(len(rows))
