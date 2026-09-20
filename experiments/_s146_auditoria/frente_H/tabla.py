# -*- coding: utf-8 -*-
# Frente H S146. Fuente unica de la tabla: escribe hipotesis.json y tabla_generada.md.
# Solo crea archivos dentro de experiments/_s146_auditoria/frente_H/. No lee ni toca data/ ni pipeline/.
#
# Codigos de configuracion vigente entonces y hoy divergente:
#  M260   mascara de nube BT<260 K cableada a mano en process_viirs.py (solo VIIRS 375),
#         del 2026-04-05 (a6e9a6ee4) al 2026-08-28 23:00 UTC (#535, 1888c1e3e). MODIS leia el perfil (0 desde S29).
#  PRE46  mascara de pixeles calientes armada con los caminos legacy (BT, NTI, dNTI); el primer pase
#         Tests 2 y 3 mas segundo pase entra al operacional el 2026-05-16 (3d25ea16e).
#  G3K    compuerta bt > t_bg + 3 K dentro de los Tests 2 y 3 (D22), desde PRE46 en adelante.
#  B21    banda 21 primaria en MODIS (D21). Solo afecta MODIS.
#  SEC3   area de pixel con sec3 del cenit; nadir fijo MODIS 2026-06-05 (#354), VIIRS 2026-06-07/08 (#368, #373).
#  T1     Test 1 integrado en el ROI activo (detector propio, D30), operacional desde 2026-05-01 (d6e64dc0b).
#  ANILLO fondo por mediana de anillo de 5 a 25 km (D25); kernel local solo en 5 volcanes desde S61 a S63.
#  PISO   pisos VRP por sensor, retirados 2026-08-31 (#571).
#  C2G    cercas intra-radio S83/S85 activas (2026-05-26 a 2026-07-01, #474).
#  ANCLA_TUP ancla de Tupungatito en el centro de caja del KMZ y no en el crater (corregida S65 2026-05-20, revertida S80, recorregida S98).
#
# Profundidad: A = abri el instrumento (script, workflow o perfil) en esta sesion;
#              B = lei el documento que declara el veredicto (lineas citadas);
#              C = solo la entrada de HYPOTHESIS_LOG.md (leido entero) o la regla A de CLAUDE.md.
# Veredicto H: SIGUE = sigue valiendo; CONFIG = vale solo bajo su configuracion;
#              PERDIDO = instrumento perdido; NUNCA = nunca se midio (se descarto por argumento);
#              OBSOLETA = el mecanismo que media ya no existe en el codigo (caso de CONFIG sin nada que repetir).
import json, io, os

R = []
def row(id, que, ses, inst, ventana, codigo535, cobertura, config, metrica, prereg, orig, ver, porque, prof, fuente, apaga=0):
    R.append(dict(id=id, que=que, sesion_fecha=ses, instrumento=inst, ventana_datos=ventana,
                  codigo_respecto_535=codigo535, cobertura=cobertura, config_divergente=config,
                  metrica_unidad=metrica, criterio_preregistrado=prereg, veredicto_original=orig,
                  veredicto_H=ver, por_que=porque, profundidad=prof, fuente=fuente, trabajo_que_apaga=apaga))

# ------------------------------------------------------------------ DESCARTADO / REFUTADO / NO ADOPTAR
row("H-01", "Test 1 con fondo LOCAL sobre NTI: medir el exceso de la cumbre contra sus vecinos inmediatos y en el indice MIR/TIR, para que el valle tibio bajo un cono nevado no cuente como calor (A69)",
    "S105/S106, 2026-06-10", "experiments/_s104_roi_probe/audit_local_sweep.py y audit_sensor_strat.py (existen); workflow _archive/reproc-s105-test1-nti-local-sweep.yml; perfiles _archive/_test1_nti_local{,_ks20,_ks25}.yaml; flag ENABLE_TEST1_LOCAL_BG_NTI sigue en el codigo, apagado",
    "2026-01-29 a 2026-06-08", "ANTES", "VIIRS 375; Tupungatito, Villarrica, Llaima, Lascar, Lastarria (5 de 11). Generalizado a 'el sesgo no es separable a escala local' para todos",
    "M260, G3K, T1, ANILLO, C2G; SEC3 hasta el 7 de junio",
    "corrimiento al norte en metros (mediana), conteo de RECORDS con Test 1 disparado, y 'recall' por noche definido como 'existe algun record VIIRS 375 ese dia' (audit_local_sweep.py:70-71), sin exigir deteccion ni publicacion. Sin negativos limpios, sin predicado del dashboard, sin nulo",
    "SI (design 2026-06-10 par. 12, antes de correr)",
    "REFUTADO en todo el barrido k=2,0/2,5/3,0: 'el Test 1 se apaga en noches ALERTA' (Tupungatito 59/75, Villarrica 3/11 a k=2,0)",
    "CONFIG", "El criterio protegia la redundancia del mismo detector que hoy sostiene 57,8 % de la sobre-publicacion de VIIRS 375 (FASE1_SUSTRATO:79). A k=2,0 el brazo bajo los disparos del Test 1 a la mitad (Tupungatito 465 a 220, Villarrica 462 a 177, Llaima 428 a 209), curo el corrimiento (1047/748/1097 m a 182/170/206 m) y el propio informe dice que 'el recall global se sostiene porque otros paths rescatan esas noches'. Nunca se midio publicacion por noche ni negativos limpios. Repetir: mismo perfil, codigo de hoy, banco de paridad S145",
    "A", "docs/superpowers/specs/2026-06-10-test1-local-bg-nti-design.md:209-245 y :254-270; audit_local_sweep.py:62-76", 5)

row("H-02", "Co-validacion por pixel en NTI del Test 1: exigir que cada pixel del disco tenga firma propia en el indice",
    "S104, 2026-06-09", "experiments/_s104_roi_probe/audit_ab_test1_nti.py (existe); run 27186289487; perfiles _archive/_test1_nti_covalidation_{enabled,disabled}.yaml",
    "2026-01-29 a 2026-06-08 (segun el yml)", "ANTES", "VIIRS 375, 5 volcanes", "M260, G3K, T1, ANILLO, C2G",
    "si el Test 1 sigue disparando; posicion", "design 2026-06-09", "REFUTADO: 'apaga el Test 1' (la senal difusa no tiene firma por pixel)",
    "CONFIG", "Mismo defecto de criterio que H-01: 'apaga el Test 1' se conto como dano sin medir si la noche se sigue publicando por el camino contextual ni cuanto baja la publicacion en negativos. Hoy FASE1 mide que sin Test 1 siguen seguras 71 de 75 noches",
    "B", "docs/MIROVA_DIVERGENCES.md:1429-1430", 3)

row("H-03", "Test 1 que integra NTI (y no radiancia MIR absoluta) con fondo de anillo",
    "S104/S105, 2026-06-09", "experiments/_s104_roi_probe/audit_ab_test1_nti_v2.py (existe); run 27223821692; perfil _archive/_test1_nti_integral.yaml; flag ENABLE_TEST1_NTI_INTEGRAL apagado, rama solo en process_viirs.py",
    "2026-01-29 a 2026-06-08", "ANTES", "VIIRS 375, 5 volcanes", "M260, G3K, ANILLO, C2G",
    "metros de corrimiento al norte; controles de recall y magnitud 'sin cambio'", "SI", "REFUTADO por insuficiente: corrige 50 m de 1000 a 1500 m; 'inocuo'",
    "CONFIG", "Se juzgo solo por POSICION. Nunca se midio su efecto sobre la publicacion en negativos limpios, que es la pregunta de hoy. Un brazo 'inocuo' en recall y magnitud que cambia de MIR absoluto a NTI es candidato barato a re-medir",
    "B", "docs/MIROVA_DIVERGENCES.md:1431-1434; CLAUDE.md A69 nota S125", 3)

row("H-04", "Quitar la compuerta de 3 K (D22) y el fondo de anillo (D25) en VIIRS 375, brazo literal con 5 ablaciones",
    "S143, 2026-09-17/19", "experiments/_s143_evaluador/ (existe), workflow reproc-s143-ab-d22d25.yml, perfiles _s142_ab_*.yaml",
    "2026-06-01 a 2026-08-31", "DESPUES (datos de invierno reprocesados con codigo posterior a #535)", "VIIRS 375, 9 volcanes. No dice nada de V750 ni MODIS (declarado)",
    "B21 no aplica; T1 activo en todos los brazos",
    "pasadas en negativo limpio, noches para recall, razon de magnitud; con verificador y linea base", "SI, v2 con verificador antes de correr",
    "NO ADOPTAR: ningun brazo cumple los tres",
    "SIGUE", "Es el A/B mejor instrumentado del proyecto y corrio en el regimen actual. Lo que si queda cojo es el criterio 1 (cota escalar sin acimut, A107): las 5 perdidas del literal son 4 y son coincidencias de radio. La atribucion (todo el descenso viene de apagar keep_peak; D22 y D25 empujan en contra) sigue valiendo y no hay que repetirla",
    "C", "docs/HYPOTHESIS_LOG.md:1525-1538", 1)

row("H-05", "Apagar keep_peak y/o condicionar el segundo pase (D19), 5 brazos",
    "S135, 2026-09-07", "experiments/_s135_ab_d1d2/evaluar_ab.py y RESULTADO_FINAL.md (existen); workflow reproc-s135-ab-d1d2.yml; perfiles _s135_ab_*.yaml",
    "2026-06-01 a 2026-08-31", "DESPUES", "VIIRS 375, 6 volcanes (Isluga, Lascar, Lastarria, PCC, Planchon-Peteroa, Tupungatito). Sin nevados del sur",
    "G3K, T1, ANILLO",
    "noches confirmadas perdidas (260), % de artefacto quitado, paridad AGREGADA (mediana unica de los 6 volcanes)", "SI",
    "NO ADOPTAR: el brazo B (sin keep_peak) pierde 0 noches y quita 100 % del artefacto, pero falla el criterio 3 por 0,692 contra 0,708",
    "CONFIG", "El criterio 3 es una paridad agregada que hoy se sabe defectuosa por dos lados: A100 (keep_peak daba paridad por accidente, con el pixel equivocado a ~3 km) y V-12 (el agregado compensa entre volcanes de 0,66 a 1,39). El brazo B fue rechazado por 0,016 de una metrica que premiaba el artefacto. No hay que re-correrlo: hay que re-evaluar sus salidas con criterio por volcan y negativos limpios",
    "B", "experiments/_s135_ab_d1d2/RESULTADO_FINAL.md:9-25; CLAUDE.md A100; docs/AUDIT_S146.md:75", 4)

row("H-06", "Medir con direccion (GeoTIFF UTM de MIROVA) si el cumulo lejano que publica keep_peak es el objeto de MIROVA",
    "S144, 2026-09-19", "experiments/_s144_keep_peak_direccion/verificadores/ (existe)", "estratos ajenos a la muestra", "DESPUES", "VIIRS 375; el fenomeno es de Lastarria (12 de 15 pasadas)", "",
    "contraste de campo con nulos medidos", "SI, siete versiones", "CERRADO sin correr la medida (habria dado INCONCLUSO 90 % de las veces)",
    "NUNCA", "La medida pre-registrada no se corrio. Lo que si se midio (nulos y controles) sigue valiendo como leccion de instrumento (A109, A110). El cierre no habilita ni prohibe apagar keep_peak",
    "C", "docs/HYPOTHESIS_LOG.md:1540-1567", 2)

row("H-07", "Probe de vecinos tibios v1 y v2: en que etapa se pierden los vecinos del foco que MIROVA suma",
    "S141/S142, 2026-09-15", "experiments/_s141_fase1_probe{,_v2}/ (existen), runs 34929024703 y 34967596160", "pasadas OSF 2025 reprocesadas con codigo de hoy", "DESPUES", "VIIRS 375; estrato nevado sin muestra",
    "G3K, ANILLO", "fraccion de vecinos por test limitante, por volcan, con controles C1 a C4", "SI", "v1 INDETERMINADO; v2 HETEROGENEO en focal, INDETERMINADO en nevado",
    "SIGUE", "Bien instrumentado y en el regimen actual. No justifica A/B. El hallazgo post hoc (dETI 52 de 52 en la ruta contextual, compuerta BT 18 de 18 en la del Test 1, piso C1 en los 70) queda como pista declarada, no como veredicto",
    "C", "docs/HYPOTHESIS_LOG.md:1499-1523", 1)

row("H-08", "Area de pixel geolocalizada (en vez de nadir fijo) para corregir el gradiente cenital de la magnitud",
    "S133, 2026-09-05", "experiments/_s133/analizar_ab_area.py, resultado_ab_area.json (existen); workflow reproc-s133-area-ab.yml", "chunk 1: 2026-04-01 a 2026-05-31 (el yml llega a 08-31)", "DESPUES", "VIIRS 375, 8 volcanes, 643 pares por pasada",
    "G3K, T1, ANILLO", "razon de magnitud por bin de cenit, sobre pares donde MIROVA publico", "SI", "NO ADOPTAR: invierte el signo del sesgo (veredicto declarado PARCIAL, solo chunk 1)",
    "CONFIG", "El documento del veredicto se declara parcial y no encontre en docs/ el veredicto de los chunks 2 y 3 (SIN DATO: no abri resultado_ab_area.json). Ademas el area sola no es el remuestreo (A66 rebajada): el brazo fiel, bow tie mas remuestreo centrado en get_grid_center, nunca se corrio",
    "B", "docs/s133/AB_AREA_VEREDICTO_CHUNK1.md:1-10; docs/MIROVA_DIVERGENCES.md:2072, 2122", 3)

row("H-09", "Banda 22 como primaria en MODIS (D21)",
    "S133, 2026-09-05", "experiments/_s133/analizar_ab_b22.py, resultado_ab_b22.json (existen); workflow reproc-s133-b22-ab.yml", "2026-08-01 a 2026-08-31", "DESPUES", "MODIS; solo Lascar (n=61) y Villarrica (n=70), pareado por granulo",
    "G3K, ANILLO, conectiva min", "invariancia: razon ON/OFF dentro de 0,95 a 1,05 y cambio del fondo", "SI",
    "NO ADOPTAR (fallaron los dos criterios, el fondo cambio -1,2 K)",
    "CONFIG", "El criterio era de INVARIANCIA, no de paridad: 'la paridad nunca se midio (n = 2)' (audit_s139/VERIFICADOR.md:30-32). Un mes, dos volcanes, con la compuerta puesta, y S137 mostro que banda y compuerta interactuan. Hoy la bateria del Apendice A da 9 de 9 al brazo con banda 22. No es una refutacion de D21",
    "B", "docs/s133/AB_B22_VEREDICTO.md:1-12; docs/audit_s139/VERIFICADOR.md:30-32", 4)

row("H-10", "ROI1 como caja de 5 km igual para todos (paper) en vez de circulo de 3 a 20 km por volcan (D18)",
    "S130, 2026-08-31/09-01", "experiments/_s130_d18/ (existe); run 33456630043; perfiles _s130_d18_{caja,circulo}.yaml", "2026-05-29 a 2026-08-24", "DESPUES (flag mergeado el 2026-08-31, d6d9b8e05; perfil con cloud_mask_bt_k 0.0)", "6 volcanes, tres sensores segun el perfil",
    "G3K, B21, T1, ANILLO", "detecciones perdidas y paridad sobre records comunes (5.551); control de instrumento: 366 records cambian", "SI (PREREGISTRO_AB_D18.md)", "NO ADOPTAR por ausencia de beneficio",
    "CONFIG", "Correccion a A-13 del frente A: este A/B NO corrio en el regimen viejo. El regimen lo fija el codigo que procesa, no la fecha del granulo (experiments/_s136/RESULTADO_PROBE.md:14-19), y el codigo es posterior a #535. Lo que si le falta es la unidad: nunca se midio publicacion en negativos limpios, y la caja manda pixeles a umbrales mas estrictos, que es la direccion que hoy interesa (la caja de PCC pasa de 20 km a 5). Re-evaluar las salidas ya generadas, sin re-correr",
    "A", "docs/s130/VEREDICTO_AB_D18.md:1-14; git d6d9b8e05; pipeline/profiles/_s130_d18_caja.yaml:76", 3)

row("H-11", "Fondos autorreferentes (GAP A: sacar los pixeles del Test 1 por pixel del pool de mu y sigma; fondo de magnitud)",
    "S129/S130, 2026-08-31", "experiments/_s129_ab_fondos/, _s130_ab_sustrato/ (existen); workflow reproc-s129-ab-fondos.yml", "2026-03-01 a 2026-05-28", "DESPUES", "5 volcanes", "G3K, B21, conectiva min",
    "cuatro firmas pre-registradas", "SI", "SIN VEREDICTO: los brazos no difieren, el mecanismo casi no tiene sustrato",
    "SIGUE", "La falta de sustrato se volvio a ver hoy por otra via: diag_n_nti_path > 0 en 5 de 954 pasadas V375 y 0 en el resto (FASE1_SUSTRATO:18). Ojo: vale para volcanes sin fase efusiva; con lava expuesta el sustrato aparece",
    "B", "docs/s130/AB_FONDOS_SIN_SUSTRATO.md:1-14", 1)

row("H-12", "Corona Eq.6 (fondo por la corona de pixeles que rodea al cumulo), 2x2 con el filtro contextual",
    "S126/S127, 2026-08-29/30", "experiments/_s126_corona/01_veredicto.py (existe); perfiles _s126_corona_{on,off,ctxoff}.yaml", "2026-06-25 a 2026-08-24", "DESPUES (perfiles con cloud 0.0, corridos el 29 y 30 de agosto)", "VIIRS 375, 5 volcanes (Villarrica, Planchon-Peteroa, Lascar, PCC, NdC)",
    "G3K, T1, PISO aun activo", "un par por NOCHE con el maximo de ambos lados; criterio 5 = cero detecciones perdidas", "SI (S126_CORONA_PREREGISTRO.md)",
    "NO ADOPTAR: Villarrica sube 0,045 en vez de bajar; 8 detecciones perdidas de 2.179 (0,37 %)",
    "CONFIG", "Dos defectos hoy conocidos: (1) la paridad por maximo nocturno infla 0,1 a 0,2 contra la de pasada (audit_s139/VERIFICADOR.md:28-29); (2) el criterio 5 conto como perdida 8 detecciones de 0,021 a 0,042 MW sin preguntar si eran noches que MIROVA confirma: en el regimen de hoy perder publicaciones de centesimas de MW en negativos limpios es el objetivo, no el dano. Es la misma familia que D25, que S145 implemento apagado",
    "B", "docs/S127_CORONA_RESULTADO.md:26-79", 3)

row("H-13", "Brazos de magnitud A, B, C (apagar dos reducciones y encender la corona) para el sub-reporte VIIRS",
    "S125, 2026-08-28", "experiments/_s125_magnitud/02_veredicto_ab.py (existe); perfiles _s125_mag_*.yaml", "2026-06-25 a 2026-08-24", "ANTES (datos commiteados 2026-08-28 15:06 UTC, ocho horas antes de #535)", "VIIRS 375, 4 volcanes, 15 a 57 noches",
    "M260, G3K, T1, PISO", "volcanes en banda, IC bootstrap, FN nuevos; por noche", "SI", "NO ADOPTAR todavia: 2 de 4 criterios; la direccion era correcta en 4 de 4",
    "CONFIG", "Corrio con la mascara de 260 K, que en invierno dejaba sin fondo pasadas enteras de Villarrica y Lascar (69 y 29 noches ciegas, S126_CLOUDMASK_RESULTADO:19-24). Muestra insuficiente declarada por el propio informe",
    "B", "docs/S125_AB_MAGNITUD_RESULTADO.md:10-42; git 69c1e4c9e", 2)

row("H-14", "Remuestreo a grilla UTM (F70), 4 brazos",
    "S124, 2026-08-27/28", "experiments/_s124_f70/ (existe); perfiles _f70_{a,b}.yaml", "2026-06-25 a 2026-08-24", "ANTES", "VIIRS 375, 11 volcanes; n = 1 y 2 en dos de ellos (V-04)",
    "M260, G3K, T1, grilla mal centrada (D17), sin bow tie", "mediana de 61 dias, pareado por pasada", "SI (en el perfil _f70_b.yaml)", "NO ADOPTAR; D16 'CERRADA, no reabrir'",
    "CONFIG", "Ya rebajado por V-04: lo refutado fue el regrid F70, no la grilla de MIROVA. Agrego: corrio ademas con la mascara de 260 K. El propio veredicto reconoce que ningun script commiteado produce uno de sus numeros (S124_F70_VEREDICTO.md:97-99)",
    "B", "docs/S124_F70_VEREDICTO.md:1-5, 52-110; docs/AUDIT_S146.md:70", 4)

row("H-15", "Ancla honesta en MODIS (D12): dejar de etiquetar far el foco de Lascar cuando un pixel del Salar roba el hotspot",
    "S121, 2026-07-17", "experiments/_s121_d12_ab/ (existe el directorio; el frente B y V-09 dan los artefactos por perdidos); workflow reproc-s121-d12-modis-ab.yml", "2025-02-15 a 2026-07-17", "ANTES (no afecta: MODIS leia el perfil)", "MODIS, 4 volcanes",
    "B21, G3K, ANILLO", "noches 'curadas' = cumulo dentro del inner, sin cargar ninguna referencia (V-09); destape de records path D sobre 5 MW", "SI", "NO ADOPTAR (destapa 131 records de artefacto)",
    "PERDIDO", "V-09: el 76 exacto es NO VERIFICABLE y 'curada' no era 'MIROVA confirmo'. Con tasa base de 89,1 % de cumulo dentro del inner (V-02) la metrica no distingue actividad",
    "B", "docs/AUDIT_S121_D12_AB.md:1-50; docs/AUDIT_S146.md:73", 3)

row("H-16", "Cercas intra-radio por camino (S83/S85): 'protegen al crater del robo de cumulo'",
    "S118, 2026-06-28/07-01", "experiments/_s118_c2ab/ (existe); run 28312968093; perfiles _c2ab_*.yaml", "ventanas dirigidas (el yml solo trae su fecha de alta)", "ANTES", "11 Tier A, 4 brazos",
    "M260 (en VIIRS 375), G3K, T1", "robo de cumulo en noches focales confirmadas (214); cola inflada en RECORDS", "SI (A66)", "REFUTADA la hipotesis; cercas a OFF (#474)",
    "CONFIG", "Para la pregunta que se hizo (robo) sigue valiendo, con el matiz B-03 (incluye noches donde el robo es imposible). Para la pregunta de hoy NUNCA se midio: cuanto subio la publicacion en negativos limpios al apagar las cercas. El costo se conto en records inflados sobre 1,5x, no en pasadas publicadas donde MIROVA callo",
    "B", "docs/AUDIT_S118_C2_GATES_AB.md:3-65; docs/HYPOTHESIS_LOG.md:9-27", 2)

row("H-17", "Cuantificar el Muy Bajo de NdC con otro fondo para el Test 1 (anillos 1,5-3, 2-4, 3-5 km, NTI local, Eq.16, nucleo espacial)",
    "S112, 2026-06-17", "experiments/_s112_test1_lowmag/audit_t1lm_ab.py (existe); run 27705248529; perfiles _archive/_t1lm_*.yaml", "2026-05-01 a 2026-06-17", "ANTES", "VIIRS 375; NdC, Lascar, Lastarria; 3 ALERTAS de NdC",
    "M260, G3K, T1", "error log de magnitud en 3 alertas e 'inflacion RUTINA' por pasada (24 en control contra 52 a 54 en los anillos)", "SI, endurecido por revision adversarial",
    "NO ADOPTAR por criterio... y ADOPTADO el mismo dia por decision (ver seccion 4, H-A07)",
    "CONFIG", "Unico A/B anterior a S139 que midio inflacion en noches RUTINA, y dio que el anillo intermedio la DUPLICA. Se adopto igual. Ver H-A07",
    "A", "docs/S112_TEST1_LOWMAG_AB_RESULTS.md:3-48", 4)

row("H-18", "Fondo local para la MAGNITUD en MODIS (huella o anillo alrededor del cumulo)",
    "S107/S108, 2026-06-13/14", "experiments/_s107_modis_localmag/ (existe); run 27480234385; perfiles _archive/_modis_localmag_*.yaml", "2026-01-29 a 2026-06-13", "no aplica (MODIS)", "MODIS, 6 volcanes",
    "B21, G3K, ANILLO", "RECORDS inflados (pc.vrp > 5 MW) que bajan a 5 o menos: 4 % y 20 % contra 85 % pre-registrado", "SI (A66)", "REFUTADO: mas records suben que se curan",
    "CONFIG", "Es la misma familia fisica que D25 (fondo por vecinos), que S138 identifico como 'la palanca real' y S145 implemento apagado en V750. La refutacion de S108 se midio con banda 21 (que S137 mostro que fabrica el primer pase MODIS) y con una metrica de records sobre 5 MW, sin referencia (MIROVA casi no publica MODIS fuera de Lascar). No refuta D25 y nadie lo ha dicho por escrito",
    "B", "docs/AUDIT_S108_AB_MODIS_VEREDICTO.md:1-41", 3)

row("H-19", "Ancla del cumulo en el pico de NTI (brazo B) en vez del crater; y no re-anclar ctx_cluster (A84)",
    "S106, 2026-06-11; S117", "A/B S106: workflows _archive/reproc-s106-*.yml y experiments/_s106_fase2/ (existen). Probe S117: scratchpad/probe_ctx_cluster_s117.py NO EXISTE (B-09)", "2026-01-29 a 2026-06-11", "ANTES", "VIIRS 375 y 750, 5 a 6 volcanes",
    "M260, G3K, T1", "metros de corrimiento al norte", "SI", "brazo B descartado (Llaima 2263 m, peor); A84 'no reabrir'",
    "PERDIDO", "La pata S106 tiene instrumento; la pata S117 (indistinguibles en n_pixels y VRP) lo perdio. El frente A dice que A84 se reproduce igual. Es de posicion, no de publicacion: baja prioridad",
    "C", "CLAUDE.md A84; docs/audit_s146/FRENTE_B_CIERRES_CON_SCRIPT.md:66, 227", 1)

row("H-20", "'ctxpeak es un parche redundante del sec3': A/B de 3 brazos (base, nadir+ctx, nadir sin ctx)",
    "S102, 2026-06-06", "workflow _archive/reproc-s102-viirs-noctx-ab.yml; experiments/_s99_audit/analyze_viirs_3way.py (existe)", "2026-04-01 a 2026-06-06", "ANTES", "VIIRS, 11 volcanes", "M260, G3K, T1",
    "razon de magnitud sobre records donde MIROVA publico", "SI", "REFUTADA: nadir sin ctx es 2,43x peor",
    "CONFIG", "El propio proyecto lo dejo escrito en S136: 'ambas son previas a #535, que bajo el fondo global 6 a 8 K en nevados... hoy no tiene respaldo' (MISSION_GATE_S136:80-81). Y la metrica premiaba a keep_peak por accidente (A100)",
    "B", "CLAUDE.md A66; docs/MISSION_GATE_S136_TEST1_CONTEXTUAL.md:78-84", 3)

row("H-21", "Alternativas a ctxpeak para la magnitud del Test 1: filtro por pixel (41 FN), contextual puro (31 FN por crater embebido), nucleo espacial, Eq.16",
    "S99, 2026-06-03", "experiments/_s99_audit/ab_test1_audit.py (existe); runs 26864573601 y 26885140366; perfiles _s99_test1_*.yaml", "2026-04-01 a 2026-05-31 (S100)", "ANTES", "3 volcanes (Tupungatito entre ellos), VIIRS 375",
    "M260, G3K, SEC3", "FN de magnitud en records (pc.vrp = 0 donde MIROVA detecto); razon mediana", "parcial", "descartadas; 'ctxpeak es el UNICO'",
    "CONFIG", "El brazo B de S135 es contextual puro y dio 0 perdidas en 260 noches con Tupungatito adentro (28 noches), en el regimen actual. Los '31 FN' de S99 eran records con magnitud cero, no noches sin publicar",
    "B", "docs/MIROVA_DIVERGENCES.md:1365; docs/S99_TEST1_AB_RESULTS.md:19-54; docs/MISSION_GATE_S136_TEST1_CONTEXTUAL.md:80", 3)

row("H-22", "Camino contextual en cirrus alto (D9): compuerta atmosferica por t_bg (A) y co-validacion con BT o NTI (B)",
    "S71, 2026-05-21", "workflows _archive/reproc-ab-path-d-{atm-gate,covalidation,cap}.yml; perfiles mirova_equivalent_path_d_*_v1.yaml; experiments/127, 130, 131 (existen)", "2026-02-20 a 2026-05-20", "ANTES", "11 Tier A, tres sensores",
    "M260, G3K, SEC3, PRE46 ya no (el primer pase habia entrado 5 dias antes)", "conteo de RECORDS con vrp > 5 MW solo path D y t_bg < 260 K; 'recall 7/7' por volcan", "NO consta", "A y B rechazadas; C (tope de 5 MW) adoptada",
    "CONFIG", "Reabierta hoy por V-01. Agrego una SOSPECHA de instrumento: desde el 2026-05-15 el comentario del codigo dice que los caminos legacy 'se calcularon arriba (diag) pero no contribuyen cuando ON' (process_viirs.py:1235-1237, blame 958a7a189), y la evidencia de S70 ('100 % disparan SOLO por path D') se leyo de diag_n_dnti_ctx_path el 2026-05-20. Si el contador ya era solo diagnostico, la atribucion al path D de S70/S71 no mide lo que dice. No lo verifique corriendo nada",
    "A", "docs/MIROVA_DIVERGENCES.md:282-296, 579-648; pipeline/process_viirs.py:1235-1237", 4)

row("H-23", "Barrido Coppola literal de 22 variantes: C2 = 3, 4, 8; C1 = 0,01; sin dual-ROI; Di Bella n = 12; drifts 1 a 7",
    "S46, 2026-05-15/16", "experiments/87_audit_s46_round1.py y 87_results.md (existen); workflow _archive/reproc-s46-coppola-literal-ab.yml", "2026-04-16 a 2026-05-16", "ANTES", "11 Tier A, tres sensores",
    "M260, SEC3, ANCLA_TUP, PISO", "TP/FN/FP en RECORDS; FP definido SOLO como 'detectamos cuando el scraper marca FALSO_POSITIVO' (87_audit_s46_round1.py:153, 202)", "SI (reglas de decision en el design)",
    "se adopto drift234; el resto 'sin diferencia'",
    "CONFIG", "El FP vale 39 en 18 de las 22 variantes: el instrumento era ciego a la sobre-publicacion, porque una pasada RUTINA donde publicamos no contaba como nada. Todo lo que ese barrido dice sobre C1, C2, dual-ROI o n = 12 respecto de precision es SIN DATO. Subir C2 o C1 en el ROI de cumbre nunca se midio contra negativos limpios",
    "A", "experiments/87_results.md:8-31; experiments/87_audit_s46_round1.py:145-215", 5)

row("H-24", "Kernel de fondo local en Tupungatito ('refuta el kernel en glaciar', A19)",
    "S62, 2026-05-19", "workflow _archive/reproc-ab-lastarria-tupungatito.yml; run 26072884472", "2026-03-01 a 2026-05-19", "ANTES", "VIIRS 375, Tupungatito",
    "M260, SEC3, ANCLA_TUP", "razon mediana sobre records con alerta; recall 70 a 87", "NO", "NO ADOPTAR: 10,37x a 18,46x",
    "CONFIG", "Se midio UN DIA ANTES de descubrir que el ancla de Tupungatito apuntaba al centro de caja del KMZ y que el cumulo elegido era el flanco SE, falso (H_S64, HYPOTHESIS_LOG:259-279; corregido S65, 2026-05-20). El 18,46x es del glaciar del flanco, no del crater. A19 generaliza desde ahi a 'ring glaciar empeora con kernel'. Ademas area con sec3 y mascara de 260 K",
    "C", "docs/HYPOTHESIS_LOG.md:283-307 y 259-279; CLAUDE.md A19", 3)

row("H-25", "Bajar el radio interno de PCC de 20 a 7 km",
    "S62, 2026-05-19", "run 26072886354", "marzo a mayo 2026", "ANTES", "PCC", "M260, SEC3",
    "razon mediana", "NO", "revertido (3,64x, peor)",
    "SIGUE", "Vale como leccion de metodo (A18). Como parametro por volcan la puerta de la mision lo rechaza igual (backlog_s115.md:5-14)",
    "C", "docs/HYPOTHESIS_LOG.md:311-330", 0)

row("H-26", "Fondo por percentil bajo del anillo (p01 a p25) para igualar la magnitud de MIROVA",
    "S56, 2026-05-17", "experiments/101_background_variants_offline.py (existe)", "5 casos de Villarrica", "ANTES", "Villarrica, VIIRS 375, n = 5",
    "SEC3, M260", "razon por caso, con el percentil APROXIMADO como mediana menos k sigma", "NO", "confirmada offline, descartada como 'probable hack' a favor del kernel local",
    "NUNCA", "Se midio con un proxy gaussiano sobre 5 casos de un volcan, y se descarto por argumento de fidelidad. No hay que retomarla: el canon dice media de vecinos, no percentil de anillo (D25)",
    "C", "docs/HYPOTHESIS_LOG.md:1163-1211", 0)

row("H-27", "Cuatro estrategias de agregacion (pixel maximo, Eq.16, umbral estricto, radio de 1 km)",
    "S55, 2026-05-17", "experiments/100_aggregation_strategies_offline.py (existe)", "5 casos de Villarrica", "ANTES", "Villarrica, n = 5", "SEC3, M260, ANILLO con recorte a cero",
    "razon por caso", "NO", "NEGATIVA: todas dan 0 en 4 de 5",
    "CONFIG", "Operaban sobre anomaly_pixels ya recortados a cero por el fondo de anillo (el propio log lo dice). Lo refutado es 'agregar distinto arregla la magnitud con ESTE fondo'. Con fondo de vecinos (D25) nunca se probaron",
    "C", "docs/HYPOTHESIS_LOG.md:1215-1247", 1)

row("H-28", "Sumar todos los pixeles alertados de la escena, como escribe Coppola 2019 p. 3, en vez de publicar un solo cumulo; barrido de radio uniforme",
    "S129, 2026-08-30", "experiments/_s129_suma/01_suma_vs_cluster.py y 02_radio_de_suma.py (existen)", "records de 2026 (SIN DATO si separa tramos: no abri el script)", "mezcla probable", "VIIRS 375, 9 volcanes con n de 5 o mas noches",
    "G3K, T1, ANILLO con recorte, keep_peak", "volcanes en banda 0,7 a 1,4; un par por noche", "SI", "NEGATIVO: el mejor radio uniforme (10 km) gana un volcan; 'pasa a brazo del A/B'",
    "NUNCA", "Se midio offline sobre los pixeles persistidos (tope de 100, con nuestro fondo y nuestro recorte). El brazo de reproceso que el propio documento pide nunca se corrio. No es una refutacion de la suma de escena",
    "B", "docs/s129/RADIO_DE_SUMA.md:17-80", 2)

row("H-29", "Filtros de no aptos del segundo pase, retiro de los Test 1 K1, BT path encendido, sin tope",
    "S72 a S73, mayo 2026", "workflows _archive/reproc-ab-{unsuitable-filters,unsuitable-only,test1-retire-only,bt-path-on-v1,no-cap-v1}.yml; perfiles mirova_equivalent_*_v1.yaml (existen)", "2026-02-20 a 2026-05-20", "ANTES", "11 Tier A",
    "M260, SEC3, G3K", "SIN DATO (no abri los audits)", "SIN DATO", "filtros de no aptos adoptados (S72); retiro K1 apagado; BT path apagado",
    "CONFIG", "Cobertura declarada, no verificada: solo confirme que los workflows y perfiles existen y su ventana. V-05 ya establecio que el filtro corre desde S72",
    "A (solo existencia y ventana)", "experiments/_s146_auditoria/frente_H/workflows_ab.json", 1)

row("H-30", "Filtro por pixel a 5 sigma sobre el Test 1 (Phase 1), sobre la mascara final (Phase 2) y fondo global (D4)",
    "S33, 2026-05-05", "experiments/76_audit_independent.py, pipeline/audit_metrics.py (existen); runs 25339969705, 25401379853, 25414145698", "90 dias hasta abril 2026", "ANTES", "11 Tier A",
    "PRE46, M260, SEC3, ANCLA_TUP", "recall global en RECORDS y razon mediana", "NO (se corrigio la metrica despues de ver el resultado, por un bug real)", "REFUTADOS: -18,6 y -63 puntos de recall",
    "OBSOLETA", "La mascara sobre la que actuaban (caminos legacy) ya no es la de produccion. El recall se media como OR con triggered_test1. D4 fondo global 'refutado' aca se adopto por volcan ocho dias despues (S39, 36cf58316)",
    "B", "docs/MIROVA_DIVERGENCES.md:733-768", 1)

row("H-31", "N sigma uniforme 3 contra 5 (Coppola) y 12 (Di Bella) en el umbral de temperatura de brillo",
    "S19, 2026-04-25", "docs/DRIFTS_S17.md (existe); 6 reprocesos locales", "30 dias, abril 2026", "ANTES", "3 volcanes (Tupungatito, Chaiten, Lascar)",
    "PRE46, M260, SEC3", "F1 en records", "SI (elegir el de mayor F1)", "REFUTADA: 3 sigma gana; 5 y 12 dan resultados identicos al bit por el tope de 7 K",
    "OBSOLETA", "Dos de los tres brazos eran el mismo brazo (instrumento sin poder), y el camino de temperatura de brillo esta apagado desde S40 (2026-05-13) con sustrato cero hoy (FASE1_SUSTRATO:15-21). No apaga nada vigente",
    "C", "docs/HYPOTHESIS_LOG.md:754-773", 0)

row("H-32", "Aveni 2025 Ec. 9 (VRP por TIR) para el lago de lava de Villarrica; y k de Di Bella para VIIRS 375",
    "S24, 2026-04-26", "experiments/52_aveni_tir_poc.py (existe)", "6 refs de Villarrica; 37 pares de Tupungatito", "ANTES", "Villarrica, Tupungatito",
    "PRE46", "razon por caso", "SI", "REFUTADAS",
    "SIGUE", "Son de formula, no de deteccion ni de regimen: el k de 18,0 quedo respaldado por Coppola 2026 Tabla 1 (AUDIT_S146:158) y la Ec. 9 no es del canal NRT (H14, H16)",
    "C", "docs/HYPOTHESIS_LOG.md:864-882, 1436-1451", 0)

row("H-33", "Sigma del fondo calculado solo en el ROI de cumbre (D6) para que el glaciar no infle el umbral",
    "S21, 2026-04-25", "experiments/41_DIAGNOSIS_FINAL_S21.md (existe)", "3 granulos", "ANTES", "Tupungatito, n = 3 granulos",
    "PRE46, camino de venteo (retirado S27)", "razon de sigmas (0,81 contra menos de 0,5 esperado)", "SI", "REFUTADA",
    "OBSOLETA", "El camino que usaba ese umbral (venteo con tope de 3 K) se retiro en S27. Tres granulos de un volcan",
    "C", "docs/HYPOTHESIS_LOG.md:681-699", 0)

row("H-34", "H1, H2, H3, H5, H7, H8 (S17): sigma del venteo, caja de busqueda chica, descarga sin timeout, regresion de codigo, zona horaria del scraper, referencia erronea",
    "S16/S17, abril 2026", "commits y py-spy citados en el log", "abril 2026", "ANTES", "infraestructura", "camino de venteo retirado",
    "varias", "en parte", "REFUTADAS (la causa real era NOAA-21, H10)",
    "SIGUE", "Son de infraestructura y de adquisicion; ningun cambio de regimen las toca. H10 (NOAA-21) esta verificado limpio por el frente A",
    "C", "docs/HYPOTHESIS_LOG.md:532-643", 0)

row("H-35", "Discriminante fisico por record entre foco debil real y artefacto (barrido de candidatos, AUC 0,859)",
    "S116, 2026-06-27", "JSON sin script (B-08)", "4.560 records summit", "ANTES", "tres sensores agregados",
    "M260, B21, G3K", "AUC contra la etiqueta 'MIROVA publico'", "NO", "A83: agotado",
    "PERDIDO", "V-03: etiqueta defectuosa, paradoja de Simpson (0,554 dentro de volcan y sensor). La puerta de la mision prohibe igual un discriminante por record contra la etiqueta de MIROVA: no retomar",
    "C", "docs/AUDIT_S146.md:72", 1)

row("H-36", "far a summit en MODIS: 8 discriminantes, N sigma de la Tabla 1, tope de magnitud (AUC 0,45), contexto temporal Method-2, ancla de primer pase",
    "S111 a S114, junio 2026", "experiments/_s111_d11/, _s114_audit/ (existen)", "abril a junio 2026", "no aplica (MODIS)", "MODIS",
    "B21, G3K, ANILLO, conectiva min", "AUC y recall en records contra la etiqueta de MIROVA", "en parte", "A82: fisicamente irreducible, no reabrir",
    "CONFIG", "Ya rebajada tres veces (S124, S138, S146 V-02). No agrego medicion. Lo que habria que repetir es la tasa base por volcan con banda 22 y sin compuerta, no los discriminantes",
    "C", "CLAUDE.md A82; docs/AUDIT_S146.md:69", 3)

row("H-37", "Filtro por intensidad o distancia 'de Laiolo 2026' como clon literal",
    "S136, 2026-09-08", "experiments/_s136/FILTRO_INTENSIDAD_DESCARTADO.md, piso_mirova.py (existen)", "canal NRT", "DESPUES", "11 Tier A", "",
    "lectura del PDF mas minimo publicado por MIROVA", "no aplica", "DESCARTADO por dos vias",
    "SIGUE", "La lectura documental la repitio el verificador de S141 (P-01). Un piso de intensidad cortaria alertas reales de 0,02 a 0,06 MW (NdC)",
    "B", "experiments/_s136/FILTRO_INTENSIDAD_DESCARTADO.md:1-30; docs/MIROVA_DIVERGENCES.md:1853-1860", 0)

row("H-38", "Test 1 sin la interseccion contextual (tercer estado del eje: interseccion actual, contextual puro, sin interseccion)",
    "S136, 2026-09-08", "experiments/_s136/probe_3brazos.py, RESULTADO_PROBE.md (existen); run 34274884640", "20 pasadas", "DESPUES", "VIIRS 375; 3 pasadas de nevado con sustrato",
    "G3K, ANILLO", "razon de magnitud por pasada", "SI", "INDETERMINADO por falta de sustrato (3 pasadas utiles de nevado)",
    "NUNCA", "El brazo 'nunca se corrio en este regimen' como reproceso (MISSION_GATE_S136:87-89). El probe dice que donde el filtro actua la magnitud casi se duplica (1,17 a 2,23 con n = 3): indicio, no veredicto",
    "B", "experiments/_s136/SUSTRATO_RESUELVE_EL_DESENLACE.md:14-25", 2)

row("H-39", "Hipotesis abiertas de S27 que nunca se probaron: dNTI con C1 negativo, camino solo TIR (TIRVolcH), composicion de caminos en cascada contra OR",
    "S27, 2026-04-30", "ninguno", "no aplica", "no aplica", "no aplica", "",
    "no aplica", "no aplica", "quedaron como 'hipotesis abiertas S28+' en MISSION",
    "NUNCA", "Siguen listadas en docs/MISSION.md:231-236 sin medicion. La de composicion (cascada contra OR) es justo lo que FASE1 midio hoy por otra via: el Test 1 no entra a la mascara, compite por la fuente del cumulo",
    "B", "docs/MISSION.md:229-236", 1)

row("H-40", "Local p95 del ROI como umbral adicional (D7): agregarlo a VIIRS 375 o quitarlo de MODIS y V750",
    "S23, 2026-04-26", "tests/test_local_roi_paridad.py", "no aplica", "no aplica", "tres sensores", "",
    "no aplica", "no aplica", "diferida 'requiere A/B contra OSF'",
    "OBSOLETA", "El umbral sigue en process_modis.py:614-617 pero cuelga del camino de temperatura de brillo, que esta apagado. Nunca se midio y ya no hace falta",
    "A", "docs/HYPOTHESIS_LOG.md:831-841; pipeline/process_modis.py:614-617", 0)

row("H-41", "Compuerta de coherencia de 'campo difuso' en el pipeline (backlog S93) y supresion de cirrus en display (S90)",
    "S90/S93, 2026-05-30", "tasks/backlog_s93_pipeline_diffuse_field_gate.md", "no aplica", "no aplica", "MODIS sobre todo", "",
    "no aplica", "no aplica", "anotada como opcional, nunca corrida",
    "NUNCA", "La puerta de la mision la trata como parche (A72: artefacto se arregla en la deteccion, no se esconde). Se lista por cobertura; no se propone",
    "B", "tasks/backlog_s93_pipeline_diffuse_field_gate.md:1-49", 0)

row("H-42", "Conectiva de los Tests 2 y 3: min (formula) contra max (prosa)",
    "S136 a S146", "experiments/_s136/VEREDICTO_CONECTIVA.md, experiments/_s146_bateria/ (existen); workflow probe-s146-bateria-apendice.yml", "9 escenas MODIS del Apendice A (2000 a 2015)", "DESPUES", "MODIS, escenas del paper (no son volcanes chilenos salvo Villarrica A6)",
    "se prueba con y sin B21 y G3K", "conformes de 9", "vara de A2 re-escrita en S146", "S136: min no reproduce; S146: el mejor brazo usa max y da 9 de 9",
    "SIGUE", "Es fidelidad al Apendice A y corre con el codigo de hoy. No dice nada de la sobre-publicacion en VIIRS (AUDIT_S146:118-120). Tres brazos INDECIDIBLES por no guardar posicion",
    "B", "docs/AUDIT_S146.md:96-120", 1)

row("H-43", "A/B de distance_class en MODIS (decision 4 de AUDIT_S131)",
    "S132, 2026-09-03", "experiments/_s132/ab_distance_class_modis.json (citado)", "SIN DATO", "DESPUES", "MODIS", "B21, G3K",
    "cuatro criterios, fallo C2", "SI", "NO ADOPTAR",
    "CONFIG", "Solo lei el encabezado. A94 y V-02 ya dicen que el frente de la etiqueta rinde una noche de 946 y que la tasa base lo vuelve indiscriminante",
    "B (encabezado)", "docs/s132/AB_DISTANCE_CLASS_MODIS.md:1-8", 0)

# ------------------------------------------------------------------ ADOPTADO CON A/B
row("H-A01", "ADOPCION. Test 1 integrado en el ROI: sumar el exceso MIR de todo el disco de 3 km para ver focos sub-pixel (detector propio, D30)",
    "S27 a S29, 2026-04-30/05-01", "runs 25148058512 y reintentos; perfil _mirova_literal.yaml (existe)", "2026-01-29 a 2026-04-29", "ANTES", "11 Tier A; VIIRS 375 en S27, V750 en S28, MODIS en S29",
    "PRE46 (el camino contextual contra el que 'subio el recall' ya no existe), M260, SEC3, ANCLA_TUP",
    "recall en RECORDS de alerta (507), contando como acierto 'pc.vrp > 0 O triggered_test1' (DIVERGENCES:884-885); FP contados solo como detecciones far (3.840 contra 3.500). Sin negativos limpios", "NO consta",
    "ADOPTADO: recall 50 a 80 %",
    "CONFIG", "La justificacion (+30 puntos de recall) se midio contra una deteccion contextual que dos semanas despues fue reemplazada por el primer pase Tests 2 y 3 mas segundo pase (S46). Hoy, en el regimen actual, sin Test 1 siguen seguras 71 de 75 noches VIIRS 375 y 0 se pierden seguro, mientras sostiene solo 186 de 322 negativos publicados (FASE1:79-88). El aporte de recall que justifico la adopcion nunca se re-midio despues de S46. Y el acierto se contaba con el disparo del propio Test 1, o sea circular",
    "B", "docs/MIROVA_DIVERGENCES.md:848-935; git d6e64dc0b, 3d25ea16e", 5)

row("H-A02", "ADOPCION. Primer pase Tests 2 y 3 mas segundo pase (drift234)",
    "S46, 2026-05-16", "experiments/87_results.md", "2026-04-16 a 2026-05-16", "ANTES", "11 Tier A", "M260, SEC3",
    "F1 en records; +3 TP (los 3 de MODIS), FP constante en 39", "SI", "ADOPTADO por +0,7 de F1 y 'alineacion con el paper'",
    "CONFIG", "La ganancia medida son 3 records MODIS. El efecto sobre la publicacion en negativos no se pudo ver con ese instrumento (H-23). La adopcion es defendible por fidelidad, no por la medicion",
    "A", "experiments/87_results.md:8-60", 2)

row("H-A03", "ADOPCION. Kernel de fondo local por volcan (Villarrica, Planchon-Peteroa, Lastarria, Chaiten, PCC)",
    "S58 a S63, mayo 2026", "workflows _archive/reproc-ab-local-kernel-bg*.yml, reproc-ab-pcc-kernel.yml, reproc-ab-chaiten.yml; experiments/104, 105 (existen)", "2026-04-16 a 2026-05-15 (Villarrica); 2026-03-01 a 2026-05-19 (resto)", "ANTES", "VIIRS 375 sobre todo; extendido a MODIS por TDD sin A/B propio (HYPOTHESIS_LOG:1035-1040)",
    "M260, SEC3", "razon mediana sobre records donde MIROVA alerto (Villarrica n = 2 casos comparables, luego 5); N de records summit baja 65 %", "parcial",
    "ADOPTADO por volcan",
    "CONFIG", "Tres defectos: es una conmutacion por volcan que la mision prohibe (MISSION:93-99 lo declara deuda); Villarrica se decidio con n = 2; y el -65 % de records summit en Villarrica nunca se leyo como lo que hoy importa (menos publicacion en negativos). D25 propone lo mismo uniforme. El R2 retroactivo de S70 lo valido con un caso por volcan",
    "C", "docs/HYPOTHESIS_LOG.md:965-1018, 283-307, 50-80", 3)

row("H-A04", "ADOPCION. ctxpeak (D10): intersectar el Test 1 con la mascara contextual y rescatar siempre el pixel mas caliente (keep_peak)",
    "S100, 2026-06-04", "experiments/_s99_audit/ab_test1_fair.py (existe); run 26921561612", "2026-04-01 a 2026-05-31", "ANTES", "VIIRS 375; 272 pares, 256 en 6 volcanes; Llaima 0 pares, Villarrica 2, Copahue 1, NdC 3",
    "M260, SEC3, G3K", "pares record a record donde MIROVA publico; recall y razon. Sin negativos", "NO consta para el criterio 'justo' (se escribio tras detectar un confusor de cobertura)",
    "ADOPTADO: 0 FN nuevos, Tupungatito 18,4x a 1,24x",
    "CONFIG", "A100 y D19 ya mostraron que keep_peak publica como summit a 0,0 km un pixel del borde del disco, mas frio que el fondo, y que la paridad salia por accidente. En S143 todo el descenso de publicacion en negativos (0,917 a 0,547) viene de apagarlo. La adopcion nunca miro negativos y los nevados del sur tenian 0 a 3 pares",
    "A", "docs/S100_TEST1_FULL_AB.md:16-50; docs/HYPOTHESIS_LOG.md:1535", 5)

row("H-A05", "ADOPCION. Area de pixel a nadir fijo, MODIS (S102) y VIIRS (S103)",
    "S101 a S103, 2026-06-05/08", "experiments/_s99_audit/audit_nadir_promote_r3.py, analyze_viirs_nadir_ab.py (existen); workflows _archive/reproc-s10{1,2,3}-*.yml", "2026-01-29 a 2026-06-07", "ANTES", "11 Tier A; MODIS con n = 1 fuera de Lascar (S102_NADIR_PROMOTE_RESULTS:19-24, 42)",
    "M260 (VIIRS 375), G3K, T1", "razon mediana global por sensor sobre records con referencia; FN a nivel record", "SI (target en design 2026-06-06)",
    "ADOPTADO: VIIRS 375 2,27x a 0,78x",
    "SIGUE", "El cambio es de formula y esta respaldado por la calibracion S14 y por Coppola 2026 Tabla 1. Lo que NO vale es leer 0,78 como 'paridad sana': S130 midio que la razon cae de 0,740 cerca del nadir a 0,253 mas alla de 50 grados aun con nadir fijo. A67 ya anoto el efecto colateral: menos detecciones (Villarrica 636 a 602), que nunca se conto en negativos",
    "B", "docs/S102_NADIR_PROMOTE_RESULTS.md:8-42; CLAUDE.md A66, A67", 1)

row("H-A06", "ADOPCION. Ancla espacial honesta (VIIRS 375 S106, V750 S108) y magnitud de nucleo focal (MODIS S109, V750 S112)",
    "S106 a S112, junio 2026", "experiments/_s106_fase2/, _s109_modis_mag/audit_focalmag_ab.py, _s112_v750focal/ (existen)", "2026-01-29 a 2026-06-17", "ANTES", "5 a 6 volcanes por A/B, resto promovido por reproceso",
    "M260, B21, G3K", "S109: 0 diferencias de deteccion en granulos comunes (1.791), control Lascar 1,000, foco preservado; C2 de cura 71 % contra 85 % pre-registrado", "SI (A66)",
    "ADOPTADOS; S109 con C2 por debajo de lo pre-registrado, reinterpretado como 'metrica de maximizar'",
    "CONFIG", "En MODIS no hay referencia fuera de Lascar, asi que 'curar' fue bajar records de mas de 5 MW, no acercarse a MIROVA. El plan definitivo dice que MODIS publica igual con alerta (11,5 %) que sin ella (10,2 %). No lo re-medi",
    "B", "docs/AUDIT_S109_MODIS_FOCAL_VEREDICTO.md:4-41; docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:30-36", 2)

row("H-A07", "ADOPCION. Anillo intermedio de fondo para el Test 1 mas prioridad al cumulo debil (S112), por volcan (Lascar, NdC, Lastarria)",
    "S112, 2026-06-17", "experiments/_s112_test1_lowmag/audit_t1lm_ab.py (existe); run 27705248529", "2026-05-01 a 2026-06-17", "ANTES", "VIIRS 375; 3 alertas de NdC",
    "M260, G3K", "el A/B midio inflacion en pasadas RUTINA: 24 (control) contra 54 (anillo 1,5 a 3 km)", "SI, y el veredicto pre-registrado fue NO ADOPTAR",
    "ADOPTADO contra su propio criterio, por evidencia externa (Sentinel-2 vio 6 pixeles calientes en NdC el 16 de junio) y decision de Nicolas 'recall sobre precision'",
    "CONFIG", "Es la unica adopcion cuyo A/B midio la sobre-publicacion y la vio duplicarse, y aun asi entro a mirova_equivalent, gateada por volcan. Bajo la regla S143 (primero igualar, lo demas al experimental) es candidata directa a mudarse. ENABLE_TEST1_INTERMEDIATE_BG y ENABLE_TEST1_PRIORITY_WEAK_CLUSTER siguen en True (leido de pipeline.profile hoy)",
    "A", "docs/S112_TEST1_LOWMAG_AB_RESULTS.md:3-48", 4)

row("H-A08", "ADOPCION de hecho. Mascara de nube apagada (#535 la apago creyendo que era un no-op; S126 decidio no revertir)",
    "S125/S126, 2026-08-28/29", "experiments/_s126_cloudmask/02_veredicto.py (existe); runs 33257081431 y 33257082834", "SIN DATO exacto (tres volcanes, invierno 2026)", "es el cambio mismo", "VIIRS 375; NdC, Villarrica, Lascar",
    "G3K, T1, PISO", "noches ciegas recuperadas (176 de 181); paridad con n = 8 y 35", "el script se escribio antes de terminar los reprocesos",
    "SOSTENER el apagado",
    "CONFIG", "Fiel al paper (Laiolo 2026 p. 4, verificado S128), asi que la decision es correcta por la mision. Pero el costo se midio mal para la pregunta de hoy: 'solo 21 de 286 detecciones nuevas caen en noches que MIROVA confirma' (S126_CLOUDMASK_RESULTADO:63), o sea 265 publicaciones nuevas donde MIROVA no alerto, leidas como 'cara negativa chica'. Es el origen medido del salto 62,1 a 87,1 %",
    "B", "docs/S126_CLOUDMASK_RESULTADO.md:11-76", 3)

row("H-A09", "ADOPCION. Retiro de los pisos VRP (S130) y apagado de las cercas intra-radio (S118)",
    "S118 y S130", "experiments/_s126_piso/, _s130_piso_vrp/, _s118_c2ab/ (existen)", "2026-05-01 a 2026-08-28 (piso)", "el piso, DESPUES", "11 Tier A",
    "", "piso: que suprime sobre lo visible; cercas: robo de cumulo", "SI", "ADOPTADOS",
    "SIGUE", "Los dos van hacia el literal. Ninguno conto cuanto sube la publicacion en negativos limpios, pero ambos quitan cosas que MIROVA no tiene. Cobertura declarada: no abri los scripts del piso",
    "B", "docs/S126_PISO_VRP_ES_UN_NO_OP.md:1-14; docs/AUDIT_S118_C2_GATES_AB.md", 0)

row("H-A10", "ADOPCIONES sin A/B propio leido: agrupamiento anclado al crater y filtro de distancia por pixel (S38), fondo global del Test 1 por volcan (S39), BT path apagado (S40), modo de pixel unico sub-MW (F52-B), compuerta de consistencia TIR (F46), guarda de saturacion (S73), tope de 5 MW (S71)",
    "S38 a S77, mayo 2026", "workflows _archive/reproc-ab-d8-*.yml, reproc-ab-lbg-global.yml, reproc-ab-h8.yml, reproc-no-bt-path-15d.yml; experiments/84 a 89 (existen)", "ventanas de 15 a 30 dias entre 2026-04-12 y 2026-05-11", "ANTES", "11 Tier A",
    "M260, SEC3, ANCLA_TUP", "SIN DATO (no abri los audits)", "SIN DATO", "ADOPTADOS",
    "CONFIG", "Cobertura declarada, no verificada. Todas anteriores a nadir fijo y a #535, con ventanas de dos a cuatro semanas. El tope de 5 MW si lo verifico V-01 como funcionando",
    "A (solo existencia y ventana)", "experiments/_s146_auditoria/frente_H/workflows_ab.json; git log -S sobre mirova_equivalent.yaml", 1)

json.dump(R, io.open(os.path.join(os.path.dirname(__file__), "hipotesis.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

with io.open(os.path.join(os.path.dirname(__file__), "tabla_generada.md"), "w", encoding="utf-8") as f:
    f.write("| ID | qué se probó (fenómeno) | sesión y fecha | instrumento | ventana de los datos | código respecto de #535 | sensores y volcanes | config. de entonces hoy divergente | métrica y unidad | criterio antes de ver | veredicto original | veredicto H | prof. |\n")
    f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in R:
        c = lambda k: str(r[k]).replace("|", "/").replace("\n", " ")
        f.write("| " + " | ".join([c("id"), c("que"), c("sesion_fecha"), c("instrumento"), c("ventana_datos"), c("codigo_respecto_535"),
                                   c("cobertura"), c("config_divergente"), c("metrica_unidad"), c("criterio_preregistrado"),
                                   c("veredicto_original"), "**" + c("veredicto_H") + "**", c("profundidad")]) + " |\n")
    f.write("\n### Por qué, fila por fila (con fuente)\n\n")
    for r in R:
        f.write("- **%s** (%s). %s *Fuente: %s.*\n" % (r["id"], r["veredicto_H"], r["por_que"], r["fuente"]))

from collections import Counter
print(len(R), Counter(r["veredicto_H"] for r in R))
