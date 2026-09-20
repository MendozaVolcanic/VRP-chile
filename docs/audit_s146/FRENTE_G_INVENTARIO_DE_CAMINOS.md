# Frente G (S146): inventario de todo lo que hoy puede cambiar lo que el operador ve

> Auditoría de sólo lectura. No se modificó ningún archivo existente: ni `pipeline/`, ni `frontend/`, ni
> perfiles, ni `data/`, ni `CLAUDE.md`, ni docs. No se corrió pytest, no se descargó nada, git sólo para leer.
> Todo lo que este informe afirma sale de una herramienta ejecutada en esta sesión; los scripts y sus salidas
> están en `experiments/_s146_auditoria/frente_G/`. Este archivo lo arma `armar_informe.py` desde
> `plantilla_informe.md` más `tabla_inventario.md` (generada por `construir_inventario.py`): los valores
> efectivos de los flags y las fechas de git no están transcritos a mano.
> Régimen de todas las huellas medidas: records de los 11 Tier A desde el 2026-09-01 (posterior a #535).

## 0. Lo que pasa físicamente, antes de la tabla

Cada pasada nocturna entrega dos imágenes del volcán: una en infrarrojo medio, que reacciona mucho a un
punto muy caliente aunque sea chico, y una en térmico, que sigue la temperatura media del suelo. Entre esas
dos imágenes y el punto rojo que ve el operador hay una cadena de nueve etapas. El paper de MIROVA describe
una parte corta de esa cadena (leer, recortar, comparar cada píxel con sus vecinos, sumar la energía de los
píxeles alertados). Todo lo demás lo fuimos poniendo nosotros, casi siempre para curar un caso concreto:
un glaciar que inflaba la suma, un salar que robaba la posición, un lago que parecía caliente.

Lo que este inventario muestra es que **varias de esas curas actúan sobre el mismo número una detrás de
otra, y algunas se deshacen entre sí**. La más importante para la brecha de VIIRS 375: el detector propio
"Test 1 integrado" no pregunta si hay un píxel caliente, pregunta si el disco de 3 km alrededor del cráter
tiene dispersión de temperatura. Medido acá con ruido puro, sin ningún cuerpo caliente, su criterio
"3 sigma" se cumple el 100 % de las veces a la resolución de 375 m. Lo único que lo frena es un piso
relativo de 2 %, que se supera con cerca de 1 K de contraste espacial dentro del disco: una cumbre con
roca y nieve lo cumple casi cualquier noche. Y cuando dispara, el ancla honesta lo pone a 0,0 km del
cráter, de modo que la cerca por distancia del dashboard ya no tiene nada que frenar.

## 1. COBERTURA

**Recorridos enteros (lectura línea a línea de la parte ejecutable):** `pipeline/process_viirs.py`
(l. 222 a 2229), `pipeline/store.py`, `pipeline/anchor.py`, `pipeline/single_pixel_mode.py`,
`pipeline/f5_core.py`, `pipeline/geo_utils.py`, `pipeline/clustering.py` (`cluster_hotspots` y
`cluster_pixels_geographic`), `scripts/run_pipeline.py` l. 116 a 360 (todos los callers de los tres
procesadores y de `store.append_record`), `scripts/build_recent_json.py` (cabecera y filtro).

**Recorridos por tramos dirigidos:** `pipeline/process_modis.py` (l. 484 a 663, 995 a 1215 y búsquedas),
`pipeline/test1_integrated.py` (cabecera, l. 129 a 182, 372 a 446), `pipeline/profile.py` (definiciones de
lectura de claves), `frontend/index.html` (l. 780 a 800, 1036 a 1240, 1425 a 1530).

**Sólo por búsqueda:** `pipeline/process_viirs_mod.py`, `pipeline/detection_context.py`, `pipeline/fetch.py`,
`pipeline/scan_geometry.py`, `pipeline/vrp_regimes.py`, `pipeline/path_d_cap.py`, `frontend/diario.html`,
`frontend/mosaico.html`, `.github/workflows/*.yml`, `scripts/auto_audit_weekly.py`,
`scripts/clasificar_referencia.py`, `scripts/banco_paridad.py` (reutilizado para ejecutar el predicado).
Lo que sólo se buscó puede esconder un literal que no vi: **`process_viirs_mod.py` y `detection_context.py`
no tienen cobertura completa**, y ahí la tabla vale como piso.

**No abiertos:** `pipeline/regrid.py`, `exclusion_zones.py`, `test1_spatial_core.py`, `detect_tirvolch.py`,
`mirova_csv_loader.py`, `audit_metrics.py`, `constants.py`, `product_version.py`, `diag_fondo.py`,
`frontend/comparacion.html` (se comprobó por script que no contiene ninguna de las funciones del predicado).
Ningún PDF (lo hace otro frente).

**Atributos de `pipeline.profile`:** 143 con `VRP_PROFILE=mirova_equivalent`
(`volcar_perfil.py`, salida `perfil_efectivo.json`). **Clasificados 143 de 143**: 109 citados
en alguna de las 57 filas de la tabla y 34 como parámetros de un camino apagado o metadatos
(sección 6). Se resolvió de qué sección del YAML lee el código cada uno (`declarado_vs_leido.py`):
**0 claves escritas en una sección distinta de la que se lee**, y **56 atributos toman su valor del
default de `profile.py` porque la clave no está escrita en el YAML operacional**. Entre esos 56 están los
cuatro umbrales del Test 1 integrado (`TEST1_K_SIGMA`, `TEST1_MIR_RELATIVE`, `TEST1_ROI_KM`,
`TEST1_INNER_RING_KM`), los C2 de los Tests 2 y 3 y el flag de los filtros de no aptos.

**Reglas por volcán:** `volcanoes.yaml` completo por script (`reglas_por_volcan.py`): 45 volcanes, 11 con
excepciones; los otros 34 sólo llevan `radius_km: 5` y ninguna otra clave de detección.

**Predicado del dashboard:** extraídas y comparadas por hash las 14 funciones del predicado en las cuatro
vistas (`comparar_frontend.py`); el predicado de `index.html` se ejecutó con node sobre las 2.360 pasadas del
régimen (`huellas_en_records.py`, vía `scripts/banco_paridad.correr_node`, sin portarlo a Python).

**Fechado:** `git log -S` por atributo sobre `pipeline/profile.py` y `git log -G` sobre la línea del YAML
(`fechar_mecanismos.py`, `declarado_vs_leido.py`), más `git log -S` manual para `volcanoes.yaml`,
`store.py` y `frontend/index.html`. El número de PR se da sólo donde aparece en el asunto del commit.

**Conteo por clase de origen (filas):** NUESTRO Y DECLARADO: 34; NUESTRO Y NO DECLARADO: 14; no aplica: 6; ESTA EN EL PAPER (segun doc): 3

## 2. La tabla, ordenada por etapa de la cadena

Leyenda de "origen": ESTA EN EL PAPER vale sólo como "según tal documento del proyecto"; este frente no
abrió ningún PDF. NUESTRO Y DECLARADO nombra la D del catálogo o la regla que lo reconoce. NUESTRO Y NO
DECLARADO significa que ni `docs/MIROVA_DIVERGENCES.md` ni `docs/MISSION.md` lo tienen como divergencia
(búsqueda por nombre del mecanismo y por sus sinónimos; los ceros se confirmaron con una segunda búsqueda
por el nombre con que lo lee el código).

| id | etapa | mecanismo | donde | valor efectivo | sensores | entro | justificacion | estado hoy | evidencia | origen | referencia |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G-01 | 0 adquisicion | Filtro nocturno en tres capas (pre-descarga, por granulo, y red de seguridad al guardar); elevacion solar < 0 | pipeline/fetch.py:731-758; scripts/run_pipeline.py:116-118,180-192; pipeline/store.py:171-182,584-592 | ENABLE_DAYTIME_MODIS=false; NTI_K1_DAY=-0.6; N_SIGMA_MIR_DAY=15.0; DNTI_CONTEXTUAL_C1_DAY=0.02 | los 3 | S1-S12 (fetch); S90 PR #257 (flag diurno MODIS)<br>ENABLE_DAYTIME_MODIS: entra 2026-05-30 56b525f<br>valor por DEFAULT de profile.py (no escrito en el YAML)<br>NTI_K1_DAY: entra 2026-05-30 56b525f<br>valor por DEFAULT de profile.py (no escrito en el YAML) | decision de mision (MIR solo de noche) | VIVO | los tres filtros usan el mismo umbral 0 grados; no hay records diurnos | NUESTRO Y DECLARADO | D27 (la Tabla 1 diurna esta escrita y nunca corre) |
| G-02 | 0 adquisicion | Standard primero, LANCE NRT de respaldo; al guardar, un Standard reemplaza al NRT ya publicado | pipeline/fetch.py:167-225,468-530; pipeline/store.py:604-620 |  | los 3 | S12 | operacional (latencia) | VIVO | product_version=nrt en 125/954 V375, 125/949 V750, 128/457 MODIS (huellas_en_records.json). Lo publicado puede cambiar dias despues | NUESTRO Y NO DECLARADO | sin D; CLAUDE.md lo trata como constraint tecnico |
| G-03 | 0 adquisicion | Cortacircuitos por host (descarga y busqueda CMR): una pasada puede no procesarse | pipeline/fetch.py:372-436,548-730 |  | los 3 | S102 #364; S116 | parche de incidente (A64) | VIVO (infra) | no deja huella en el record: la pasada simplemente falta (A108). SIN DATO sobre cuantas faltan en el regimen | NUESTRO Y NO DECLARADO | A64; sin D |
| G-04 | 0 adquisicion | Interruptores de sensor | scripts/run_pipeline.py:213-218 | SENSOR_MODIS=true; SENSOR_VIIRS_375=true; SENSOR_VIIRS_750=true | los 3 | S9 (6dfcfe7f2)<br>SENSOR_MODIS: entra 2026-04-09 6dfcfe7<br>ultimo cambio YAML 2026-04-09 6dfcfe7<br>SENSOR_VIIRS_375: entra 2026-04-09 6dfcfe7<br>ultimo cambio YAML 2026-04-09 6dfcfe7 | configuracion | VIVO (los tres encendidos) |  | no aplica |  |
| G-05 | 1 lectura | VIIRS I-band: pixeles saturados a NaN (bit 2 de quality_flags) y BT pegada al techo de la LUT (I04 361,77 K; I05 423,33 K) a NaN | pipeline/process_viirs.py:364-401 (literales SAT_BIT_MASK, BT_LUT_MAX) |  | VIIRS375 | S73 F2.8 | parche de un problema (outliers de vrp_tir de miles de MW) | VIVO | sin huella en el record: el pixel desaparece. En un foco fuerte el pixel mas caliente (I04 satura ~367 K) queda fuera del NTI, de la mascara y de la magnitud. SIN DATO de frecuencia | NUESTRO Y NO DECLARADO | D24 declara lo mismo SOLO para MODIS; para VIIRS nadie lo tiene como divergencia |
| G-06 | 1 lectura | VIIRS M-band: mismo guard (M13 634 K; M15 343 K) | pipeline/process_viirs_mod.py:181-294 |  | VIIRS750 | S73 F2.8; S132 | idem | VIVO | idem G-05 | NUESTRO Y NO DECLARADO | idem G-05 |
| G-07 | 1 lectura | MODIS: SI > 32767 a NaN (incluye 65533 saturado) y guard secundario BT > 500 K a NaN | pipeline/process_modis.py:240-246,329,552-557 | ENABLE_BT_SAT_SECONDARY_GUARD=true; BT_SAT_MIR_K_MODIS=500.0 | MODIS | S73 F2.8 (fcd3ba345)<br>ENABLE_BT_SAT_SECONDARY_GUARD: entra 2026-05-23 fcd3ba3<br>ultimo cambio YAML 2026-05-23 fcd3ba3<br>BT_SAT_MIR_K_MODIS: entra 2026-05-23 fcd3ba3<br>ultimo cambio YAML 2026-05-23 fcd3ba3 | parche (PP 695.431 MW) | VIVO | sin huella por record | NUESTRO Y DECLARADO | D24 |
| G-08 | 1 lectura | MODIS: banda 21 primaria, 22 de respaldo; el VRP convierte BT a radiancia siempre con lambda de la banda 21 | pipeline/process_modis.py:544-550,563,1027-1031 | ENABLE_MODIS_B22_PRIMARY=false | MODIS | historico; flag S132 #582<br>ENABLE_MODIS_B22_PRIMARY: entra 2026-09-02 d3b55ac<br>ultimo cambio YAML 2026-09-02 d3b55ac | historico del repo | VIVO (banda 21) |  | NUESTRO Y DECLARADO | D21 |
| G-09 | 1 lectura | MODIS: NTI con banda 31 (11 um) y no 32 | pipeline/process_modis.py:559-565 |  | MODIS | historico | historico | VIVO |  | NUESTRO Y DECLARADO | D20 |
| G-10 | 1 lectura | Area de pixel fija al nadir (sin sec3); sin remuestreo a grilla UTM; area geolocalizada apagada | pipeline/process_viirs.py:735-751; process_modis.py:504-512; process_viirs_mod.py:479-492; scan_geometry.py | ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS=true; ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS=true; ENABLE_GEOLOCATED_PIXEL_AREA=false; ENABLE_UTM_REGRID=false | los 3 | S102 #354 (MODIS), S103 #368 (VIIRS)<br>ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS: entra 2026-05-15 958a7a1<br>ultimo cambio YAML 2026-06-05 3cdb4a7<br>ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS: entra 2026-05-15 958a7a1<br>ultimo cambio YAML 2026-06-07 c48dbb0 | medicion propia (calibracion S14 contra OSF) + A/B | VIVO |  | NUESTRO Y DECLARADO | D17 (remuestreo abierto), A66/A67 con la salvedad S138 |
| G-11 | 1 lectura | Mascara de nube por BT TIR | pipeline/process_viirs.py:823-831; process_modis.py:570,780; V750 no tiene ninguna | CLOUD_MASK_BT_K=0.0 | MODIS, VIIRS375 | S1; apagada S29 en YAML, efectiva en V375 desde #535<br>CLOUD_MASK_BT_K: entra 2026-04-09 6dfcfe7<br>ultimo cambio YAML 2026-05-01 d6e64dc | historico | APAGADA (umbral 0 K) | n_cloud_masked>0 en 0 records de los tres sensores | NUESTRO Y DECLARADO | D14 cerrada |
| G-12 | 2 geometria | ROI = caja de +-radius_km (25 km Tier A, 5 km los otros 34) centrada en lat/lon del volcan, no en el centro de grilla de MIROVA | pipeline/process_viirs.py:779; process_modis.py:534; process_viirs_mod.py:515; volcanoes.yaml radius_km |  | los 3 | S14 (5478bce66), S15 Tema E | replica de la grilla 51x51 de MIROVA | VIVO |  | NUESTRO Y DECLARADO | D17 (get_grid_center nunca se cableo) |
| G-13 | 2 geometria | Fondo regional: anillo circular 5 a 25 km, mediana y desvio; minimo 10 pixeles (literal). Con menos de 10, MODIS devuelve None (no hay record) y VIIRS queda sin deteccion | process_viirs.py:780,945-956; process_modis.py:535,571-580; detection_context.py:1042-1085 | BG_INNER_KM=5.0; BG_OUTER_KM=25.0 | los 3 | S9<br>BG_INNER_KM: entra 2026-04-09 6dfcfe7<br>ultimo cambio YAML 2026-04-09 6dfcfe7<br>BG_OUTER_KM: entra 2026-04-09 6dfcfe7<br>ultimo cambio YAML 2026-04-09 6dfcfe7 | historico | VIVO | t_bg_k presente en 949/954 V375 | NUESTRO Y DECLARADO | D25 (fondo), D8. El minimo de 10 y el 'sin record' de MODIS no estan declarados |
| G-14 | 2 geometria | Ancla de deteccion = crater (vent_lat/lon) y no mirova_center; mirova_center queda solo como dato | pipeline/geo_utils.py:get_detection_anchor; scripts/run_pipeline.py:234,277,324; volcanoes.yaml (11 con mirova_center, 11 con vent) |  | los 3 | S98; mirova_center S15/S80 #220 | parche de regresion (A63) | VIVO |  | NUESTRO Y DECLARADO | seccion S98 del catalogo, D17 |
| G-15 | 2 geometria | ROI1 = circulo de radio inner_radius_km por volcan (3: Lastarria, PP; 4: Copahue; 5: seis volcanes; 7: Tupungatito; 20: PCC); el paper usa caja 5x5 km | detection_context.py:299-325; volcanoes.yaml inner_radius_km | ENABLE_ROI1_BOX_PAPER=false; ROI1_BOX_HALF_KM=2.5 | los 3 | S14 (5478bce66); PCC=20 revertido S62 #85<br>ENABLE_ROI1_BOX_PAPER: entra 2026-08-31 d6d9b8e<br>valor por DEFAULT de profile.py (no escrito en el YAML)<br>ROI1_BOX_HALF_KM: entra 2026-08-31 d6d9b8e<br>valor por DEFAULT de profile.py (no escrito en el YAML) | valores de los KML de MIROVA | VIVO (circulo) |  | NUESTRO Y DECLARADO | D18 |
| G-16 | 3 deteccion | Camino A, test de temperatura de brillo N sigma 5/10 (y piso 5 K, tope de sigma 999 K, umbral local p95 en MODIS y V750) | process_viirs.py:984-998; process_modis.py:583-661; process_viirs_mod.py:586-640 | ENABLE_DUAL_ROI_BT=true; ENABLE_BT_PATH_HOT=false; N_SIGMA_MIR_SUMMIT=5.0; N_SIGMA_MIR_SCENE=10.0; ANOMALY_THRESHOLD_K=5.0; MAX_SIGMA_COMPONENT_K=999.0; N_SIGMA=3.0; N_SIGMA_MIR=3.0; P95_VENT_EXCLUSION_MODIS_KM=5.0; P95_VENT_EXCLUSION_VIIRS750_KM=4.0 | los 3 | S26 (d90f89b31); apagado S40 (1b0c3bdb5)<br>ENABLE_DUAL_ROI_BT: entra 2026-04-28 d90f89b<br>ultimo cambio YAML 2026-05-01 d6e64dc<br>ENABLE_BT_PATH_HOT: entra 2026-05-13 bf1ccfe<br>ultimo cambio YAML 2026-05-13 1b0c3bd | lectura de Tabla 1 | ANULADO por otro flag (la mascara se construye y se pone en cero) | diag_n_bt_path>0 en 0 records de los tres sensores. OJO: su contador sigue decidiendo cosas, ver G-19 | NUESTRO Y DECLARADO | AUDIT_S146 V-08; FASE1 seccion 0 |
| G-17 | 3 deteccion | Camino B, NTI > K1 con compuerta bt > t_bg + 3 K: se calcula y se cuenta, no entra a la mascara | process_viirs.py:1002-1011,1299; process_modis.py:662-668; process_viirs_mod.py:646-654 | NTI_K1_NIGHT=-0.8; NTI_BT_SANITY_K=3.0 | los 3 | S9<br>NTI_K1_NIGHT: entra 2026-04-09 6dfcfe7<br>ultimo cambio YAML 2026-04-09 6dfcfe7<br>NTI_BT_SANITY_K: entra 2026-04-09 6dfcfe7<br>ultimo cambio YAML 2026-04-09 6dfcfe7 | Wright 2002 / Coppola (K1) | DIAGNOSTICO QUE DECIDE (ver G-19) | diag_n_nti_path>0 en 5/954 V375 y 0 en los otros | NUESTRO Y DECLARADO | D23 |
| G-18 | 3 deteccion | Camino D legacy, dNTI contextual dual con compuerta de 3 K y filtros de no aptos: se calcula y se cuenta, no entra a la mascara | process_viirs.py:1055-1083; process_modis.py:683-712; process_viirs_mod.py:690-715; detection_context.py:208-400 | ENABLE_DNTI_CONTEXTUAL_PATH=true; ENABLE_DNTI_DUAL_ROI=true; DNTI_CONTEXTUAL_C1_SUMMIT=0.003; DNTI_CONTEXTUAL_C1_SCENE=0.01; DNTI_CONTEXTUAL_C1=0.003 | los 3 | S15 P3.2/P3.1<br>ENABLE_DNTI_CONTEXTUAL_PATH: entra 2026-04-22 366e618<br>ultimo cambio YAML 2026-04-22 366e618<br>ENABLE_DNTI_DUAL_ROI: entra 2026-04-22 9a88c05<br>ultimo cambio YAML 2026-04-22 9a88c05 | Coppola 2016a (dNTI) | DIAGNOSTICO QUE DECIDE (ver G-19, G-31, G-37) | diag_n_dnti_ctx_path>0 en 507/954 V375, 386/949 V750, 455/457 MODIS | NUESTRO Y NO DECLARADO | el catalogo lo trata como diagnostico inerte (FASE1 seccion 0); su papel de arbitro no esta declarado |
| G-19 | 3 deteccion | Los contadores 'diagnosticos' deciden la FUENTE publicada: only_test1_source exige n_bt=n_nti=n_dnti_ctx=n_eti=0, aunque la mascara real (Tests 2 y 3) tenga pixeles | process_viirs.py:1747-1753; process_modis.py:1275-1290; process_viirs_mod.py:1164-1178 |  | los 3 | S44 | parche (Tupungatito FN) | VIVO | 132 pasadas V375 y 16 V750 con Test 1 disparado, mascara contextual NO vacia y los contadores legacy en cero: el Test 1 gana por 'fuente unica' sin serlo (huellas_en_records.json) | NUESTRO Y NO DECLARADO | 0 menciones de only_test1 en el catalogo y en MISSION |
| G-20 | 3 deteccion | Tests 2 y 3, primer pase: conectiva min(C1, mu + C2 sigma), C1 0,003/0,010, C2 5/10, ETI por regresion cuadratica, dual ROI | process_viirs.py:1242-1300; process_modis.py:842-890; process_viirs_mod.py:825-878; detection_context.py:413-563 | ENABLE_FIRST_PASS_TESTS_2_AND_3=true; ENABLE_DUAL_ROI_FIRST_PASS=true; C2_DNTI_SUMMIT_NIGHT=5.0; C2_DNTI_SCENE_NIGHT=10.0; C2_DETI_SUMMIT_NIGHT=5.0; C2_DETI_SCENE_NIGHT=10.0; ENABLE_TESTS_23_PROSE_BRANCH=false; C1_SUMMIT_OVERRIDE=null; C2_SUMMIT_OVERRIDE=null; VIIRS_C2_OVERRIDE_NIGHT=null | los 3 | S46 #4x (958a7a189), adoptado 3d25ea16e<br>ENABLE_FIRST_PASS_TESTS_2_AND_3: entra 2026-05-15 958a7a1<br>ultimo cambio YAML 2026-05-16 3d25ea1<br>ENABLE_DUAL_ROI_FIRST_PASS: entra 2026-05-15 958a7a1<br>ultimo cambio YAML 2026-05-16 3d25ea1 | paper | VIVO: ES la mascara | diag_n_first_pass_pixels>0 en 346 V375, 59 V750, 455 MODIS | ESTA EN EL PAPER (segun doc) | CLAUDE.md reglas cientificas: Coppola 2016a Tabla 1 y p. 7; conectiva contradictoria segun S136. C2 sale del default de profile.py, no del YAML |
| G-21 | 3 deteccion | Compuerta de temperatura bt > t_bg + 3 K dentro del primer pase (el segundo pase no la tiene) | detection_context.py:546; process_viirs.py:1297 | NTI_BT_SANITY_K=3.0; ENABLE_TESTS_23_NO_BT_GATE_VIIRS375=false | los 3 (flag para quitarla solo en V375) | S9; flag S142<br>NTI_BT_SANITY_K: entra 2026-04-09 6dfcfe7<br>ultimo cambio YAML 2026-04-09 6dfcfe7<br>ENABLE_TESTS_23_NO_BT_GATE_VIIRS375: entra 2026-09-15 2d546f3<br>ultimo cambio YAML 2026-09-15 2d546f3 | historico | VIVO |  | NUESTRO Y DECLARADO | D22 |
| G-22 | 3 deteccion | Filtros de pixeles no aptos para mu y sigma (borde, dNTI/dETI < -0,1) | detection_context.py:59-160; process_viirs.py:1272-1273 | ENABLE_UNSUITABLE_FILTERS_267_273=true | los 3 | S72 (d58f7a46f)<br>ENABLE_UNSUITABLE_FILTERS_267_273: entra 2026-05-21 d58f7a4<br>valor por DEFAULT de profile.py (no escrito en el YAML) | paper | VIVO (por DEFAULT de profile.py; la clave no esta en el YAML) |  | ESTA EN EL PAPER (segun doc) | detection_context.py:42-60 cita 'Coppola 2016a parrafos 267-273' (lineas del .txt, sin pagina): localizador debil |
| G-23 | 3 deteccion | Segundo pase (recaptura de adyacentes), dual ROI, sin condicionar al conjunto activo | process_viirs.py:1306-1357; detection_context.py:822-985 | ENABLE_SECOND_PASS_ADJACENT=true; ENABLE_DUAL_ROI_SECOND_PASS=true; ENABLE_SECOND_PASS_CONDITIONED=false | los 3 | S37/S46 (3d25ea16e)<br>ENABLE_SECOND_PASS_ADJACENT: entra 2026-05-12 970d79e<br>ultimo cambio YAML 2026-05-16 3d25ea1<br>ENABLE_DUAL_ROI_SECOND_PASS: entra 2026-05-15 958a7a1<br>ultimo cambio YAML 2026-05-16 3d25ea1 | paper | VIVO | diag_n_second_pass_recapture>0 en 433 V375, 161 V750, 452 MODIS: recaptura en MAS pasadas que el primer pase en V375 y V750 | NUESTRO Y DECLARADO | D19 (corre sin conjunto activo), D26 |
| G-24 | 3 deteccion | Cercas intra-radio S84/S85 y gate atmosferico / co-validacion / filtros finales por pixel | process_modis.py:712,944; process_viirs.py:1347,1364,1383,1818 | ENABLE_PATH_D_INTRA_RADIO_GATE=false; ENABLE_SECOND_PASS_INTRA_RADIO_GATE=false; PATH_D_ATM_GATE_TBG_MIN_K=null; PATH_D_REQUIRES_COVALIDATION=false; ENABLE_FINAL_PIXEL_FILTER=false; ENABLE_TEST1_PIXEL_FILTER=false | los 3 | S71, S83, S85, S32/S33<br>ENABLE_PATH_D_INTRA_RADIO_GATE: entra 2026-05-26 eb68f8c<br>ultimo cambio YAML 2026-07-01 92fc441<br>ENABLE_SECOND_PASS_INTRA_RADIO_GATE: entra 2026-05-28 958a226<br>ultimo cambio YAML 2026-07-01 92fc441 | parches | APAGADOS |  | NUESTRO Y DECLARADO | A85, D9, S33 |
| G-25 | 3 deteccion | Zonas excluidas (lagos, salar) con lista blanca de lagos crater | pipeline/exclusion_zones.py; process_viirs.py:1393-1398; volcanoes.yaml: Villarrica(2), Lascar(1), Copahue(1), Llaima(1), Tupungatito(1 + lista blanca) | ENABLE_EXCLUDE_ZONES=false | los 3 | S16 (6f879898f), S26; apagado S29<br>ENABLE_EXCLUDE_ZONES: entra 2026-04-29 7cccd8c<br>ultimo cambio YAML 2026-05-01 d6e64dc | parche | ANULADO por flag (las zonas siguen escritas en 5 volcanes) | n_excluded_water>0 en 0 records | NUESTRO Y DECLARADO | MISSION anti-patrones |
| G-26 | 3 deteccion | Test 1 integrado en el ROI: suma de excesos positivos de radiancia MIR en el disco de 3 km contra la mediana del anillo 1 a 3 km; dispara si suma > 3 sigma raiz(N) Y suma > 2 % de L_bg por N | pipeline/test1_integrated.py:317-470; process_viirs.py:1099-1150; process_modis.py:737-760; process_viirs_mod.py:731-760 | ENABLE_TEST1_PATH=true; TEST1_K_SIGMA=3.0; TEST1_MIR_RELATIVE=0.02; TEST1_ROI_KM=3.0; TEST1_INNER_RING_KM=1.0 | los 3 | S25 (dc32ba0f5), adoptado S27/S29<br>ENABLE_TEST1_PATH: entra 2026-04-26 dc32ba0<br>ultimo cambio YAML 2026-05-01 d6e64dc<br>TEST1_K_SIGMA: entra 2026-04-26 dc32ba0<br>valor por DEFAULT de profile.py (no escrito en el YAML) | medicion propia (6/6 Villarrica) con cita bibliografica falsa | VIVO: sostiene 57,8 % de los negativos publicados de V375 (FASE1) | triggered_test1 en 800/954 V375, 200/949 V750, 16/457 MODIS. Los cuatro umbrales salen del DEFAULT de profile.py: no estan escritos en el YAML operacional | NUESTRO Y DECLARADO | D30 (hoy) |
| G-27 | 3 deteccion | El criterio 'absoluto' del Test 1 no es un 3 sigma: la suma de excesos recortados a cero tiene media positiva bajo ruido puro (~0,4 sigma N) y supera 3 sigma raiz(N) siempre que N > ~57. Lo unico que frena es el piso relativo de 2 %, que pasa con ~1 K de dispersion espacial en el disco | pipeline/test1_integrated.py:419-437 |  | los 3; decisivo en VIIRS375 (N~208) | S25 | no se midio el nulo al adoptar | VIVO | nulo_test1_ruido_puro.json: con ruido gaussiano puro el criterio absoluto pasa 100 % en V375, ~40 % en V750, ~16 % en MODIS; dispara 84 % con 1 K y 100 % con 1,5 K en V375. k observado real: mediana 4,86 con 70 pixeles (k_observado_vs_nulo.json) contra 5,75 y 104 del nulo | NUESTRO Y NO DECLARADO | D30 declara que el detector es propio; no declara que su estadistico dispara sin senal |
| G-28 | 3 deteccion | Variantes del Test 1 (integral de NTI, co-validacion NTI, fondo local NTI) | process_viirs.py:1101-1137 (solo V375) | ENABLE_TEST1_NTI_INTEGRAL=false; ENABLE_TEST1_NTI_COVALIDATION=false; ENABLE_TEST1_LOCAL_BG_NTI=false | VIIRS375 | S104/S105<br>ENABLE_TEST1_NTI_INTEGRAL: entra 2026-06-09 d65b86d<br>valor por DEFAULT de profile.py (no escrito en el YAML)<br>ENABLE_TEST1_NTI_COVALIDATION: entra 2026-06-09 2ba97a8<br>valor por DEFAULT de profile.py (no escrito en el YAML) | A/B | APAGADAS |  | NUESTRO Y DECLARADO | A69 (nota S125) |
| G-29 | 3 deteccion | Camino C NTI relativo, camino ETI de escena, vent-path | process_viirs.py:1020,1158,1654; process_modis.py:1223 | ENABLE_NTI_RELATIVE_PATH=false; ENABLE_ETI_QUADRATIC_SCENE=false; ENABLE_VENT_PATH=false; ENABLE_VENT_PATH_MODIS=false; ENABLE_ERUPTION_PATH=true | los 3 | S10-S12, S37<br>ENABLE_NTI_RELATIVE_PATH: entra 2026-04-12 2ee346e<br>ultimo cambio YAML 2026-04-12 2ee346e<br>ENABLE_ETI_QUADRATIC_SCENE: entra 2026-05-12 970d79e<br>valor por DEFAULT de profile.py (no escrito en el YAML) | historicos | APAGADOS (ENABLE_ERUPTION_PATH=True se importa y no se lee en ninguna condicion) | n_nti_rel_path, diag_n_eti_path, vrp_vent_mw > 0 en 0 records | NUESTRO Y DECLARADO | MISSION |
| G-30 | 4 ensamblado | Cumulos 8-conexos; gana el mas cercano al crater dentro del inner (vent_anchored), ignorando cumulos con VRP = 0 | pipeline/clustering.py:75-190 | ENABLE_VENT_ANCHORED_CLUSTERING=true | los 3 | S38 (8a51df89d), S43<br>ENABLE_VENT_ANCHORED_CLUSTERING: entra 2026-05-12 8a51df8<br>ultimo cambio YAML 2026-05-12 f928438 | parche D8 | VIVO |  | NUESTRO Y DECLARADO | seccion D8' del catalogo; A85 |
| G-31 | 4 ensamblado | Prioridad de fuente del Test 1: (1) Test 1 en cumbre y pixel suelto mas caliente lejos; (2) 'fuente unica' (G-19); (3) cumulo rival < 0,01 MW. Si gana, la magnitud y los pixeles publicados se rehacen SOLO con pixeles del Test 1 | pipeline/test1_integrated.py:156-182; process_viirs.py:1735-1767,1912-2030 | ENABLE_TEST1_PRIORITY_WEAK_CLUSTER=true; TEST1_WEAK_CLUSTER_EPS_MW=0.01 | los 3 (rama 3 solo V375) | S26/S30 Regla D, S44, S111 (ea71c62c2)<br>ENABLE_TEST1_PRIORITY_WEAK_CLUSTER: entra 2026-06-16 ea71c62<br>ultimo cambio YAML 2026-06-17 a4ee5b5<br>TEST1_WEAK_CLUSTER_EPS_MW: entra 2026-06-16 ea71c62<br>valor por DEFAULT de profile.py (no escrito en el YAML) | parches | VIVO | final_hotspot_source=test1_roi en 348/954 V375 y 138/949 V750 | NUESTRO Y DECLARADO | MISSION tabla de anti-patrones (Regla D Test 1 'sigue activa'); D30. La rama 2 no esta declarada (G-19) |
| G-32 | 4 ensamblado | Ancla honesta: posicion = cumulo contextual, o el CRATER a 0,0 km cuando gana el Test 1 (modo vent) | pipeline/anchor.py:67-96; process_viirs.py:2063-2098 | ENABLE_HONEST_ANCHOR=true; ENABLE_HONEST_ANCHOR_VIIRS750=true; ENABLE_HONEST_ANCHOR_MODIS=false; ENABLE_HONEST_ANCHOR_MODIS_FIRST_PASS_GATE=true; HONEST_ANCHOR_TEST1_MODE="vent" | VIIRS375 y VIIRS750 (MODIS apagado) | S106 (542fce8d1), S108<br>ENABLE_HONEST_ANCHOR: entra 2026-06-11 86c29ef<br>ultimo cambio YAML 2026-06-12 542fce8<br>ENABLE_HONEST_ANCHOR_VIIRS750: entra 2026-06-12 bd7cba6<br>ultimo cambio YAML 2026-06-13 5e6a598 | A/B | VIVO en VIIRS | un Test 1 disparado queda SIEMPRE summit a 0,0 km: la cerca por distancia del dashboard no lo puede frenar | NUESTRO Y DECLARADO | D11-bis, D19 |
| G-33 | 4 ensamblado | MODIS: cascada legacy (pixel suelto mas caliente decide distance_class) + rescate de cumulo en store (cluster_rescue) con geocerca = radius_km (25 km) | process_modis.py:1275-1320; pipeline/store.py:307,336-394 | ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER=false | MODIS (el rescate no pisa fuentes del ancla honesta) | F47 S77 (71adc9831)<br>ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER: entra 2026-09-02 d3b55ac<br>ultimo cambio YAML 2026-09-02 d3b55ac | parche (F47 H4) | VIVO | distance_class=far en 399/457 MODIS; cluster_rescue en 4, las 4 publicadas | NUESTRO Y NO DECLARADO | D12 y D13 hablan del efecto; el rescate F47 no tiene D propia (1 mencion incidental) |
| G-34 | 4 ensamblado | Guard de coherencia A46: summit pasa a far si el cumulo con energia esta fuera del inner | pipeline/store.py:472-478 |  | los 3 | S113 #444 | parche | VIVO, sustrato minimo | diag_a46_relabel en 1 record MODIS, 0 VIIRS | NUESTRO Y DECLARADO | A81, D13 |
| G-35 | 4 ensamblado | Regla D vent en store: vrp_vent > 0 fuerza summit | pipeline/store.py:437-446 |  | los 3 | S20 | parche | SUSTRATO CERO (vent-path apagado) | vrp_vent_mw>0 en 0 records | NUESTRO Y DECLARADO | MISSION (removido S27) |
| G-36 | 5 magnitud | Wooster por sensor sobre exceso de radiancia; exceso negativo recortado a cero | process_viirs.py:1471-1475; process_modis.py:1058-1060 |  | los 3 | S14, S26 | paper (Wooster) + parche (recorte) | VIVO |  | NUESTRO Y DECLARADO | D25 |
| G-37 | 5 magnitud | Fondo de la MAGNITUD depende del camino y del volcan. Bloque contextual: nucleo 3x3 en Villarrica, PCC, Chaiten, PP y Lastarria (solo MODIS y V375; en V750 el parametro se acepta y no hace nada), anillo 5-25 km en el resto. Bloque Test 1: anillo intermedio 1,5-3 km SOLO en Lascar, NdC y Lastarria (V375), fondo global en esos tres (MODIS, V750), anillo 1-3 km del propio Test 1 en los otros ocho | process_viirs.py:1438-1450,1866-1889; test1_integrated.py:129-153; process_modis.py:1044-1056,1351; process_viirs_mod.py:460-467,1230; volcanoes.yaml local_kernel_bg (5 true, 2 false), lbg_global_compatible (3) | ENABLE_LOCAL_KERNEL_BG=true; ENABLE_TEST1_LBG_GLOBAL=true; ENABLE_TEST1_INTERMEDIATE_BG=true; TEST1_INTERMEDIATE_BG_RING_KM=[1.5, 3.0]; TEST1_INTERMEDIATE_BG_MIN_PIXELS=20 | los 3 | S33/S39 (lbg), S58-S63 (nucleo), S112 #439 (intermedio)<br>ENABLE_LOCAL_KERNEL_BG: entra 2026-05-17 429dfc3<br>ultimo cambio YAML 2026-05-18 4c00ff0<br>ENABLE_TEST1_LBG_GLOBAL: entra 2026-05-05 6156f89<br>ultimo cambio YAML 2026-05-13 36cf583 | A/B por volcan | VIVO | diag_L_bg_local presente en 97 V375 y 151 MODIS, solo en los 5 volcanes opt-in, 0 en V750. El anillo intermedio no deja campo en el record | NUESTRO Y DECLARADO | MISSION l. 90 (conmuta por volcan), D25, seccion D8. El anillo intermedio tiene 0 menciones en el catalogo y que aplique solo a 3 volcanes no esta escrito fuera del codigo |
| G-38 | 5 magnitud | V375, filtro contextual del Test 1 con keep_peak: de los pixeles del Test 1 solo cuentan los que tambien marca el camino D legacy (G-18), mas el mas caliente | process_viirs.py:1839-1850; pipeline/test1_contextual_filter.py | ENABLE_TEST1_CONTEXTUAL_FILTER=true; ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK=true | VIIRS375 | S99/S100 (5da0afdef)<br>ENABLE_TEST1_CONTEXTUAL_FILTER: entra 2026-06-03 73e735f<br>ultimo cambio YAML 2026-06-04 5da0afd<br>ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK: entra 2026-06-03 1d9ec14<br>ultimo cambio YAML 2026-06-04 5da0afd | A/B (Tupungatito 18,9x) | VIVO |  | NUESTRO Y DECLARADO | D10, D19 |
| G-39 | 5 magnitud | MODIS y V750, magnitud 'nucleo focal': solo pixeles del cumulo que tambien marca el camino D legacy, mas el pico. En MODIS en los dos bloques; en V750 SOLO en el bloque del Test 1 | process_modis.py:1155-1160,1405-1410; process_viirs_mod.py:1313-1318; pipeline/vrp_regimes.py:cluster_focal_vrp_mw | ENABLE_FOCAL_CLUSTER_MAGNITUDE=true; ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750=true; FOCAL_CLUSTER_KEEP_PEAK=true | MODIS, VIIRS750 | S109 #418 (7b085e8c5), S112 #442<br>ENABLE_FOCAL_CLUSTER_MAGNITUDE: entra 2026-06-14 fb7e6fc<br>ultimo cambio YAML 2026-06-15 7b085e8<br>ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750: entra 2026-06-18 c8f7179<br>ultimo cambio YAML 2026-06-18 6d6a634 | A/B | VIVO | pc.focal_magnitude en 456/457 MODIS y 157/949 V750 | NUESTRO Y DECLARADO | D11, D19. La asimetria MODIS/V750 no esta declarada |
| G-40 | 5 magnitud | Tope de 5 MW cuando solo disparo lo contextual y t_bg < 270 K (al cumulo y a la suma de escena) | pipeline/path_d_cap.py; process_viirs.py:1407-1414,1479,1551; process_modis.py:999-1006,1068,1162 | PATH_D_ONLY_CAP_MW=5.0; PATH_D_ONLY_CAP_TBG_MAX_K=270.0 | los 3; en los hechos solo MODIS | S71 (dbba73e09)<br>PATH_D_ONLY_CAP_MW: entra 2026-05-20 84c7d31<br>ultimo cambio YAML 2026-05-21 dbba73e<br>PATH_D_ONLY_CAP_TBG_MAX_K: entra 2026-05-20 84c7d31<br>ultimo cambio YAML 2026-05-21 dbba73e | parche D9 | VIVO en MODIS, sustrato cero en VIIRS | pc.d9_capped en 59/457 MODIS (7 publicadas), 0 en V375 y V750. Su condicion usa los contadores anulados n_bt y n_nti: con el camino A apagado, 'solo contextual' es casi siempre verdadero y el tope pasa a depender solo de t_bg | NUESTRO Y DECLARADO | D9 (cerrada S113); el acoplamiento con G-16 no esta declarado |
| G-41 | 5 magnitud | Modo de un pixel: si el cumulo tiene < 5 MW y <= 3 pixeles se publica el MAXIMO por pixel y no la suma | pipeline/single_pixel_mode.py; process_viirs.py:1573-1578,2024-2029; process_modis.py:1185; process_viirs_mod.py:1094 | ENABLE_SINGLE_PIXEL_SUB_MW_MODE=true; SUB_MW_REGIME_THRESHOLD_MW=5.0; SINGLE_PIXEL_MAX_CLUSTER_PIXELS=3 | los 3 | S77 F52-B (6c92c7762)<br>ENABLE_SINGLE_PIXEL_SUB_MW_MODE: entra 2026-05-24 6c92c77<br>ultimo cambio YAML 2026-05-24 6c92c77<br>SUB_MW_REGIME_THRESHOLD_MW: entra 2026-05-24 6c92c77<br>ultimo cambio YAML 2026-05-24 6c92c77 | parche (Tupungatito 30x) | VIVO | single_pixel_mode=True en 837/849 cumulos V375, 185/331 V750, 227/456 MODIS; cambia el numero en 82, 20 y 105 | NUESTRO Y NO DECLARADO | 0 menciones en el catalogo y en MISSION |
| G-42 | 5 magnitud | Corona Eq. 6, fondo por vecinos D25, Eq. 16 lago de lava, nucleo espacial del Test 1, VRP TIR (silenciado), VRPTIR Aveni, suma MIROVA-style | process_viirs.py:627-697,1459,1628,1898,2038; store.py:568 | ENABLE_LOCAL_CLUSTER_MAGNITUDE=false; ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375=false; ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375=false; ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750=false; ENABLE_TEST1_LAVA_LAKE_EQ16=false; ENABLE_TEST1_SPATIAL_CORE=false; ENABLE_VRP_TIR_OUTPUT=false; ENABLE_VRP_TIR_CONSISTENCY_GATE=true; ENABLE_VRPTIR_AVENI=false; ENABLE_SUM_VRP_REPORTING=false | los 3 | S99-S145<br>ENABLE_LOCAL_CLUSTER_MAGNITUDE: entra 2026-06-13 dfb8bab<br>valor por DEFAULT de profile.py (no escrito en el YAML)<br>ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375: entra 2026-08-29 024f9f0<br>valor por DEFAULT de profile.py (no escrito en el YAML) | A/B | APAGADOS | vrp_tir_mw>0, corona_degraded, diag_L_bg_vecinos, vrp_mw_sum_active, vrptir_aveni: 0 records. lava_lake_magmatic=true en Villarrica queda anulado por flag | NUESTRO Y DECLARADO | D25, D10 |
| G-43 | 6 guardado | Tope de 100 pixeles persistidos por record (los de mayor VRP) | process_viirs.py:1487; process_modis.py:1075; pipeline/anomaly_pixels.py |  | los 3 | S26 | anti-bloat del JSON | VIVO | n_anomalous_pixels>100 en 214/457 MODIS y 3/954 V375. Alimenta a G-44 y al nucleo F5 (G-47) | NUESTRO Y DECLARADO | MISSION l. 213 (lo da por infra) |
| G-44 | 6 guardado | Geocerca por pixel: los pixeles persistidos a mas de radius_km (25) del CENTRO del volcan se descartan y vrp_mir_mw se recalcula; si el pixel suelto sigue lejos, vrp_mw a cero | pipeline/store.py:217-269,307-313,351-394 | ENABLE_PIXEL_LEVEL_DISTANCE_FILTER=true | los 3 | S35 H8 #3, adoptado S38<br>ENABLE_PIXEL_LEVEL_DISTANCE_FILTER: entra 2026-05-10 4dd605d<br>ultimo cambio YAML 2026-05-12 f928438 | parche (PCC) | VIVO | discarded_reason=partial_eruption_hotspot_too_far en 432/457 MODIS, 19 V375, 4 V750: deshace las esquinas que la caja de G-12 recupera | NUESTRO Y NO DECLARADO | H8 figura en el roadmap del catalogo como 'implementado', no como divergencia; 0 menciones de geocerca |
| G-45 | 6 guardado | Tope de Villarrica: si el cumulo tiene mas de 12 pixeles, vrp_mw a cero | pipeline/store.py:405-412; volcanoes.yaml Villarrica max_cluster_pixels: 12 |  | los 3, solo Villarrica | S77 F52-A (b76dbba97) | parche (glaciar Pichillancahue 11x) | ANULADO AGUAS ABAJO en 8 de 13 casos | apilamiento_f5_single_pixel.json: 13 records topados en el regimen; 8 se publican igual (los 7 de V750 y 1 de MODIS) porque el dashboard lee pc.vrp_mw y isSummitDetection deja pasar todo record con triggered_test1 | NUESTRO Y NO DECLARADO | 0 menciones en el catalogo y en MISSION |
| G-46 | 6 guardado | Tope de cordura 50.000 MW con discriminacion por BT > 500 K; piso de VRP por sensor | pipeline/store.py:64-153,73-105 | MIN_VRP_MW_MODIS=0.0; MIN_VRP_MW_VIIRS375=0.0; MIN_VRP_MW_VIIRS750=0.0 | los 3 | S19 (1a661c29d); piso S12, quitado S130 #571<br>MIN_VRP_MW_MODIS: entra 2026-04-15 39e6bb0<br>ultimo cambio YAML 2026-08-31 d55bcd5<br>MIN_VRP_MW_VIIRS375: entra 2026-04-15 39e6bb0<br>ultimo cambio YAML 2026-08-31 d55bcd5 | parche de basura / decision | SUSTRATO CERO en el regimen | 0 records con marcas del tope o del piso | NUESTRO Y DECLARADO | catalogo (1 mencion), A130 |
| G-47 | 6 guardado | Nucleo F5': para V375 se persiste (y el dashboard publica) la suma del pixel pico mas los pixeles a <= 0,75 km o con BT >= 295 K, entre los persistidos a <= inner_km del centroide | pipeline/f5_core.py:34-104; pipeline/store.py:551-554; frontend index 1119-1186 |  | VIIRS375 | S96 display (809baa624); S132 #582 al pipeline | medicion propia (F5_CALIBRATION_S95; 0,68 vs 0,58) | VIVO | f5_core_vrp_mw en 846/954. Distinto de pc.vrp_mw en 159: MAYOR en 152 y menor en 7 | NUESTRO Y NO DECLARADO | 0 menciones de F5 en el catalogo y en MISSION; vive en CLAUDE.md A10 y en docs/F5_CALIBRATION_S95.md |
| G-48 | 6 guardado | geo_class (summit / extension / far) con catalogo de features: Lacolito PCC 4 km, Lazufre 5 km | pipeline/store.py:522-538; pipeline/volcanic_features.yaml |  | los 3 | S88 #245 | descriptivo | VIVO, no decide publicacion (solo color naranja en el mapa) | geo_class=extension en 1 record MODIS del regimen | no aplica |  |
| G-49 | 7 dashboard | Cerca: distance_class debe ser summit Y el centroide del cumulo <= inner_km (toggle 'incluir lejanas' apagado por defecto) | frontend/index.html:1043-1064; mosaico.html:245-256; diario.html:239-258 |  | los 3 | S33 (e3bc1f80a), S36 | parche de bug S33 | VIVO | 'valida pero no summit': 400/457 MODIS, 20 V750, 6 V375 | NUESTRO Y DECLARADO | D13 |
| G-50 | 7 dashboard | isValidDetection (cumulo con energia > 0) e isSummitDetection (un record descartado por el pipeline se oculta SALVO que triggered_test1) | frontend/index.html:1466-1488; mosaico.html:393-407; diario.html NO las tiene |  | los 3 | S29, S77 (47f1ad226), S139 | parches | VIVO | publicadas con discarded_reason: 49 V375, 12 V750, 44 MODIS; publicadas con vrp_mw==0: 7 V750 y 1 MODIS (todas Villarrica, G-45) | NUESTRO Y NO DECLARADO | 0 menciones de isValidDetection en el catalogo |
| G-51 | 7 dashboard | Magnitud publicada = F5' en V375 (toggle por vista, encendido por defecto, con respaldo a pc.vrp_mw si F5 <= 0), pc.vrp_mw en MODIS y V750; tope 50.000 | frontend/index.html:1086,1166-1193 |  | los 3 | S96/S100 | medicion propia | VIVO | tres claves de sessionStorage distintas (vrp_f5_core, diario_f5_core, mosaico_f5_core): el estado del toggle no se comparte entre vistas | NUESTRO Y NO DECLARADO | idem G-47 |
| G-52 | 7 dashboard | Supresion de artefactos: cirrus (t_max < 273,15 K y > 10 MW) y campo difuso (>= 100 px, < 1 MW/px, t_max < 278,15 K, >= 50 MW); nunca sobre un record confirmado por MIROVA (cruce +-60 min con el CSV) | frontend/index.html:1207-1238,1425-1455 |  | los 3 | S90 #259, S93 #277 | parche de display (A72 lo marca como candidato a migrar) | SUSTRATO CERO en el regimen | artefacto_termico = 0 de 2.360 pasadas | NUESTRO Y DECLARADO | catalogo (1 mencion c/u), D9 |
| G-53 | 7 dashboard | Niveles de alerta 1 / 10 / 100 / 1000 MW; titular = ultima deteccion valida de 48 h | frontend/index.html:780-791,1490-1512; mosaico.html:237,418 |  | los 3 | S78 | bandas de MIROVA | VIVO | identicas en index y mosaico; diario no tiene niveles | ESTA EN EL PAPER (segun doc) | frontend cita 'bandas MIROVA'; sin localizador de paper en el repo: SOSPECHA |
| G-54 | 7 dashboard | El sitio carga por defecto <volcan>_recent.json (100 dias) | scripts/build_recent_json.py; .github/workflows/pages-deploy.yml:76 |  | los 3 | S120 | rendimiento | VIVO, no filtra por contenido |  | no aplica |  |
| G-55 | 8 despues | Auto-audit semanal (abre issue si recall o magnitud salen de banda; excepcion escrita para Lastarria) | scripts/auto_audit_weekly.py; .github/workflows/audit-weekly.yml |  | los 3 | S119-S124 | control | VIVO; no cambia lo que ve el operador |  | no aplica |  |
| G-56 | 8 despues | Alertas por incidente del NRT (monitor, healthcheck): avisan de la salud del pipeline, no del volcan | .github/workflows/nrt-monitor.yml, nrt-healthcheck.yml |  | los 3 | S85, S123 | control | VIVO; no cambia lo que ve el operador |  | no aplica |  |
| G-57 | 8 despues | Post-proceso de clasificacion 'confirmado por MIROVA / solo nuestro' a data/clasificacion_referencia/ | scripts/clasificar_referencia.py, clasificacion_referencia.py |  | los 3 | S146 (6861a8dca) | eje de referencia | NO CABLEADO: ningun workflow lo corre y ningun HTML lee 'classification' | grep de 'clasificar_referencia' en .github/workflows: solo un comentario en sync-mirova-csv.yml; grep de 'classification' en frontend: 0 | no aplica |  |


### 2.1 La contracara: lo que según el catálogo el paper hace y nosotros no

| qué hace el paper (según el catálogo) | D | flag | valor efectivo | estado |
|---|---|---|---|---|
| Remuestrea el gránulo a una grilla UTM regular antes de detectar | D17 | `ENABLE_UTM_REGRID` | false | no se hace; el área fija al nadir (G-10) es lo único que lo aproxima |
| Trata el bow tie de MODIS | D28 | no existe | | no se hace en ningún paso |
| Banda 22 primaria en MODIS, 21 sólo donde la 22 satura | D21 | `ENABLE_MODIS_B22_PRIMARY` | false | no se hace |
| NTI de MODIS con banda 32 | D20 | no existe | | no se hace |
| Tests 2 y 3 sin condición de temperatura | D22 | `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` (sólo V375; MODIS y V750 no tienen flag) | false | no se hace en el primer pase; el segundo pase nunca tuvo compuerta (ver I-6) |
| Test 1 por píxel (NTI > K1) como camino de detección | D23 | no existe | | se calcula y la máscara del primer pase lo pisa |
| Retira los píxeles del Test 1 del pool de mu y sigma y de los pasos siguientes | GAP A dentro de D11 | `ENABLE_TEST1_K1_BG_EXCLUDE`, `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` | false, false | no se hace |
| Conserva los píxeles saturados | D24 | no existe | | se eliminan (G-07), y en VIIRS también (G-05, G-06, no declarado) |
| Fondo del VRP = media de los vecinos no alertados del píxel | D25 | `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375`, `..._VIIRS750` (MODIS no tiene) | false, false | no se hace |
| Segundo pase con los filtros de no aptos | D26 | no existe | | no se hace |
| Tabla 1 diurna | D27 | `ENABLE_DAYTIME_MODIS` | false | deliberado |
| Refit iterativo a 3 sigma de la regresión de NTIbk | D29 | parámetro `iterative_refit` de `compute_eti_scene_quadratic` (`detection_context.py:699-795`) | SIN DATO: no tracé con qué valor lo llama el primer pase | SOSPECHA, no verificado |
| ROI1 = caja de 5 x 5 km | D18 | `ENABLE_ROI1_BOX_PAPER` | false | no se hace |
| Conectiva de los Tests 2 y 3 según la prosa (`max`) | S136 | `ENABLE_TESTS_23_PROSE_BRANCH` | false | rige `min` |

## 3. Los ES NUESTRO Y NO DECLARADO, por peso

Ordenados por cuánto pueden pesar en la sobre-publicación de VIIRS 375 primero, y en la magnitud después.
Cada uno trae cómo medir su efecto sin tocar el pipeline.

**G-27. El criterio "3 sigma" del Test 1 integrado se cumple sin señal.** Peso: el mayor del inventario.
El fenómeno: el test suma, sobre el disco de 3 km, sólo los excesos positivos de cada píxel respecto de la
mediana del anillo. En un campo de puro ruido la mitad de los píxeles queda sobre la mediana, así que la
suma no tiene media cero: vale cerca de 0,4 sigma por el número de píxeles, mientras el umbral crece sólo
con la raíz de ese número. Con los 208 píxeles que caben en el disco a 375 m el umbral queda superado
siempre. Medido con la función real `compute_test1_mir` y los parámetros efectivos del perfil
(`nulo_test1_ruido_puro.json`, 300 campos por celda): el criterio absoluto pasa 100 % en VIIRS 375,
35 a 55 % en VIIRS 750 y 13 a 19 % en MODIS, **el mismo orden que la sobre-publicación medida por sensor
(86,3 %, 21,4 %, 11,4 %)**. El disparo completo depende entonces del piso relativo de 2 %: 0 % con
0,5 K de dispersión, 84 % con 1,0 K, 100 % con 1,5 K. En los records reales el `test1_k_observed` de las 800
pasadas V375 disparadas tiene mediana 4,86 con 70 píxeles contribuyentes (`k_observado_vs_nulo.json`); el
nulo de ruido puro predice 5,75 y 104 para un disco lleno, o sea que el disparo típico es compatible con
no tener ninguna fuente. Esto no dice que el lago de lava de Villarrica no exista: dice que este estadístico
no lo distingue de una cumbre con textura. D30 declara que el detector es propio; no declara esto.
*Cómo medirlo sobre lo persistido:* no hay campo de dispersión del disco, pero `diag_sigma_bg_k` y
`test1_k_observed` sí están: cruzar `triggered_test1` contra `test1_k_observed / (0,4 raíz(2 n_test1_pixels))`
por etiqueta (negativo limpio, positivo) con el banco de paridad. Si la razón es ~1 en los negativos y
mayor en los positivos, el nulo explica la sobre-publicación. Un umbral corregido por la media del nulo se
puede simular sin reproceso porque `test1_k_observed` y `n_test1_pixels` están persistidos.

**G-19 (con G-18). Un contador "de diagnóstico" decide qué fuente se publica.** `only_test1_source` declara
al Test 1 "fuente única" cuando los contadores de los caminos legacy (BT, NTI, dNTI contextual, ETI) están
en cero. Pero la máscara real hoy son los Tests 2 y 3, que no entran en esa cuenta. Medido
(`huellas_en_records.json`): **132 pasadas VIIRS 375 y 16 VIIRS 750** con Test 1 disparado, píxeles
contextuales reales en la máscara y los contadores legacy en cero; ahí el Test 1 gana la fuente, rehace el
cúmulo y los píxeles publicados sólo con los suyos, y el cúmulo contextual (el camino del paper) se descarta
sin quedar escrito. El verificador de la Fase 1 lo vio como subclase `fuente_unica` (35 negativos limpios);
acá está el mecanismo y el total. El camino D legacy además decide la magnitud: filtra qué píxeles del
Test 1 cuentan en VIIRS 375 (G-38) y cuáles del cúmulo cuentan en MODIS y VIIRS 750 (G-39), con su propia
compuerta de 3 K y un umbral distinto del que arma la máscara.
*Cómo medirlo:* la lista ya es reproducible con `huellas_en_records.py`; para saber cuánto cambia la
publicación hace falta el VRP del cúmulo contextual pisado, que no se persiste (mismo SIN DATO que la Fase 1).
El probe A75 especificado en la Fase 1 lo cubre si captura `ctx_cluster_anchor` antes del pisado.

**G-47 y G-51 con G-41. Dos correcciones de magnitud apiladas en VIIRS 375 que se deshacen.** El modo de un
píxel (pipeline) cambia la suma del cúmulo por su píxel máximo cuando hay menos de 5 MW y hasta 3 píxeles:
está activo en 837 de 849 cúmulos VIIRS 375. Después el núcleo F5' (store y dashboard) vuelve a sumar los
píxeles persistidos a 0,75 km del pico o con BT de 295 K o más, **incluidos píxeles que no son del cúmulo**.
Medido (`apilamiento_f5_single_pixel.json`): F5' difiere de `pc.vrp_mw` en 159 de 830, y en 152 es MAYOR; en
los 82 records donde el modo de un píxel había cambiado el número, la mediana de F5'/pc es 1,74; en 80
records el cúmulo tiene un solo píxel y F5' igual suma otros. Ninguno de los dos mecanismos figura en el
catálogo ni en MISSION. La cifra de paridad 0,68 de CLAUDE.md A10 es el resultado neto de los dos.
*Cómo medirlo:* todo está persistido (`f5_core_vrp_mw`, `pc.vrp_mw`, `pc.single_pixel_mode`,
`anomaly_pixels`): cuatro brazos offline contra MIROVA (suma del cúmulo, máximo, F5' sobre suma, F5' sobre
máximo) con el banco de paridad, por volcán.

**G-45 con G-50. El tope de Villarrica no llega al operador.** El tope pone `vrp_mw` en cero cuando el cúmulo
pasa de 12 píxeles, para no publicar el glaciar Pichillancahue. Pero el dashboard no lee `vrp_mw`: lee
`pc.vrp_mw`, y `isSummitDetection` sólo oculta un record descartado si además `triggered_test1` es falso.
Medido: 13 records topados en el régimen, **8 publicados igual** (los 7 de VIIRS 750, todos con
`triggered_test1`, y 1 de MODIS), con `vrp_mw = 0` y `pc.vrp_mw` entre 0,05 y 4,9 MW. La misma salida de
escape publica 49 records VIIRS 375, 12 VIIRS 750 y 44 MODIS que llevan `discarded_reason`.
*Cómo medirlo:* ya medido; para la historia completa correr `apilamiento_f5_single_pixel.py` sin el corte
de fecha.

**G-44. La geocerca por píxel deshace la caja que recupera las esquinas.** La ROI es una caja de más o menos
25 km (diagonal 35 km) "para recuperar las esquinas donde MIROVA publica" (comentario S15); al guardar, los
píxeles a más de 25 km del centro se descartan y `vrp_mir_mw` se recalcula, y el record queda con
`discarded_reason = partial_eruption_hotspot_too_far`. Pasa en **432 de 457 records MODIS**, 19 VIIRS 375 y
4 VIIRS 750. No cambia `pc.vrp_mw`, pero marca casi todo MODIS como "descartado parcial", que es justo el
campo que `isSummitDetection` mira (G-50).
*Cómo medirlo:* contar `discarded_n_pixels` y cruzar con `Distancia_km` de MIROVA mayor que 25.

**G-05 y G-06. En VIIRS los píxeles saturados desaparecen.** D24 lo declara para MODIS; en VIIRS nadie. La
banda I04 satura cerca de 367 K: en una fase efusiva el píxel del foco queda NaN y no entra ni a la máscara
ni a la magnitud. Hoy no pesa (no hay fase efusiva); pesa el día que importe. SIN DATO de frecuencia: no deja
huella. *Cómo medirlo:* sólo con un probe sobre gránulos (contar `qf & 4` dentro del inner).

**G-33. Rescate de cúmulo F47 en MODIS** con geocerca de 25 km: 4 records del régimen, los 4 publicados.
Sin D propia. *Cómo medirlo:* `final_hotspot_source == cluster_rescue`.

**G-13 (parte). Mínimo de 10 píxeles de fondo como literal**, y en MODIS "sin fondo" significa "sin record"
(`return None`), mientras VIIRS guarda el record sin detección: asimetría que cambia los denominadores de
cualquier tasa por pasada. *Cómo medirlo:* comparar pasadas por noche y sensor contra el catálogo CMR.

**G-02 y G-03. Infraestructura que cambia lo publicado sin dejar rastro en la D:** el reemplazo NRT a
Standard (el 13 % de los records V375 del régimen todavía son NRT) y los cortacircuitos que pueden dejar una
pasada sin procesar (A108). *Cómo medirlo:* `product_version` y el conteo de pasadas por job.

**Configuración invisible (no es un mecanismo, es dónde vive):** 56 atributos rigen desde el default de
`profile.py`. Un lector del YAML operacional no puede saber que el Test 1 integrado usa k = 3, piso 2 %,
disco de 3 km y anillo desde 1 km, ni que los filtros de no aptos están encendidos. Lista completa en
`declarado_vs_leido.json`.

## 4. Apilamientos e interacciones

- **I-1. Ancla honesta contra cerca por distancia (G-32 con G-49).** Cuando gana el Test 1 la posición
  publicada es el cráter exacto. Medido (`interacciones.json`): los 348 records `test1_roi` de VIIRS 375 y
  los 138 de VIIRS 750 tienen `final_hotspot_dist_km = 0` y `distance_class = summit`, el 100 %. En 328 de
  los 348 el centroide del cúmulo que aporta la magnitud está a más de 1 km del cráter. La cerca del
  dashboard, pensada para frenar lo lejano, queda sin efecto sobre el camino que sostiene la mayoría de la
  sobre-publicación. Es la cara de posición de D19 y D11-bis, y está declarada; lo que no está dicho es que
  anula a G-49.
- **I-2. Modo de un píxel más F5'** (sección 3): la segunda deshace a la primera en VIIRS 375.
- **I-3. Tope de Villarrica más `isSummitDetection`** (sección 3): el filtro escribe en un campo que el
  operador no ve.
- **I-4. Caja de 35 km de diagonal más geocerca de 25 km** (G-12 con G-44).
- **I-5. Un camino apagado sigue siendo condición de otros.** Con `ENABLE_BT_PATH_HOT = False` el contador
  `n_bt_path` vale cero siempre; aun así es condición de `only_test1_source` (G-19) y del tope de 5 MW
  (G-40: "sólo contextual" pasó a ser casi siempre verdadero, y el tope depende en los hechos sólo de
  `t_bg < 270 K`). Apagar G-16 cambió el significado de G-19 y G-40 sin tocar su código.
- **I-6. El segundo pase deshace la compuerta del primero.** La compuerta de 3 K (D22) vive sólo en el primer
  pase. Medido: en **230 pasadas VIIRS 375 y 139 VIIRS 750 el primer pase da 0 píxeles y el segundo pase
  "recaptura" alguno**, o sea detecta solo, sin conjunto activo del cual ser adyacente y sin compuerta
  (en MODIS pasa 1 vez). D19 declara que corre sin conjunto activo; la consecuencia (la compuerta D22 es
  permeable en VIIRS) cambia cómo leer cualquier A/B de D22: quitar la compuerta del primer pase puede mover
  poco porque el segundo pase ya opera sin ella.
- **I-7. El fondo con que se detecta no es el fondo con que se mide, y cambia por volcán y por camino**
  (G-37). En VIIRS 375 un mismo volcán puede publicar, en dos pasadas de la misma noche, una magnitud contra
  el núcleo 3 x 3 (si publicó el cúmulo contextual y el volcán es uno de los 5 opt-in), contra el anillo
  1,5 a 3 km (si ganó el Test 1 y es Láscar, NdC o Lastarria) o contra el anillo 1 a 3 km del propio Test 1
  (los otros ocho). En VIIRS 750 el núcleo 3 x 3 no existe aunque el volcán lo tenga pedido
  (`process_viirs_mod.py:460-467` lo declara como TODO desde S72). Lastarria es el único volcán con las dos
  excepciones a la vez.
- **I-8. Tres magnitudes apiladas en MODIS:** fondo por núcleo (5 volcanes), luego núcleo focal (todos),
  luego tope de 5 MW, luego modo de un píxel. El orden importa: el tope deja el cúmulo en 5,0 MW exactos y el
  modo de un píxel exige menos de 5, así que un cúmulo topado nunca pasa al máximo por píxel.

## 5. Divergencias entre las tres copias del frontend

Comparación por hash del cuerpo normalizado (`frontend_funciones.json`):

| función | index | mosaico | diario |
|---|---|---|---|
| `f5CoreMagnitude`, `_havKm` | referencia | idéntica | idéntica |
| `mirovaEqVrp` | referencia | idéntica | **distinta**: sin cúmulo devuelve `vrp_mw` sin el tope de 50.000 y sin el respaldo a `vrp_mir_mw`; aplica la cerca de `distance_class` también a los records sin cúmulo (index no) |
| `mirovaEqVrpCore`, artefactos | referencia | equivalente (sin `includeFar`) | equivalente (toma el nombre del volcán) |
| `isValidDetection` | referencia | equivalente | **no existe** |
| `isSummitDetection` | referencia | idéntica | **no existe** |
| niveles de alerta | 1/10/100/1000 | idénticos | no tiene |
| radio interno | del arreglo de volcanes, respaldo 10 km | del arreglo, sin respaldo | tabla propia `INNER_RADIUS_KM`, respaldo 5 km |

`diario.html` decide "hay detección" sólo con `eqVrpDisplay > 0`. Como no tiene `isSummitDetection`, no aplica
la regla "record descartado sin Test 1 no se muestra": un record con `vrp_mw = 0`, `discarded_reason` y
`triggered_test1` falso que index oculta, diario lo grafica (caso real del régimen: Villarrica MODIS_AQUA 2026-09-01 07:35, topado por G-45, `summit`, `pc.vrp_mw` 5,0, Test 1 falso). Los radios internos están escritos en cuatro
lugares (YAML y tres HTML); hoy coinciden los 11 (comprobado por script). El estado del toggle F5' se guarda
con tres claves distintas de `sessionStorage`, así que dos vistas abiertas pueden mostrar magnitudes distintas
del mismo record. `comparacion.html` no tiene ninguna de estas funciones (deliberado según CLAUDE.md).

## 6. Flags muertos, anulados o con sustrato cero (candidatos a limpiar, no a tocar ahora)

- **Anulado por otro flag:** camino A de temperatura de brillo con todos sus umbrales (G-16);
  `enable_exclude_zones` con zonas todavía escritas en 5 volcanes (G-25); `lava_lake_magmatic` de Villarrica
  (flag Eq. 16 apagado); `local_kernel_bg` en VIIRS 750 (parámetro aceptado, sin implementación).
- **Sustrato cero en el régimen (0 records):** máscara de nube, tope de cordura de 50.000 MW, piso de VRP,
  Regla D vent en store, los dos filtros de artefacto del display (0 de 2.360 pasadas), tope de 5 MW en los
  dos VIIRS, `diag_n_eti_path`, `n_nti_rel_path`, `vrp_tir_mw`.
- **Importado y no leído en ninguna condición:** `ENABLE_ERUPTION_PATH` (aparece sólo en los import de los
  tres procesadores); `VRPTIR_K_TIR_I5` (0 usos fuera de `profile.py`). SOSPECHA hasta confirmarlo con una
  segunda herramienta sobre `scripts/` y `experiments/`.
- **Guard casi sin sustrato:** coherencia A46 (1 record MODIS).
- **Parámetros de caminos apagados** (de `inventario.json`, `atributos_dependientes`):

  - meta (no decide nada): `DATA_SUBDIR` = "mirova_equivalent", `DEFAULT_PROFILE` = "mirova_equivalent", `PROFILES_DIR` = "WindowsPath('C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/pipeline/profiles')", `PROFILE_NAME` = "mirova_equivalent", `VALID_PROFILES` = "{'_s99_test1_ctxpeak', '_s125_viirs_f', 'mirova_equivalent_phase2', '_s133_area_geoloc', '_s126_corona_off', 'mirova_equivalent_no_cap_v1', '_s99_test1_ctx', '_dual_roi_bt_enabled', '_s125_cloudmask_off', '_s129_ab_control', '_s130_d18_circulo', '_s125_mag_control', 'mirova_equivalent_path_d_covalidation_v1', '_s135_ab_c_cond', '_s133_b22_enabled', '_s99_test1_core', '_s135_ab_d_ambos', '_f70_a', '_c2ab_baseline', '_s130_d18_caja', 'mirova_equivalent_unsuitable_only_v1', '_s142_ab_lit_sin_fondo', '_s125_viirs_e', '_c2ab_2pass_off', '_s99_test1_eq16', 'mirova_equivalent_path_d_cap_v1', '_s124_kernelbg_ab', '_s142_ab_control', '_c2ab_both_off', '_no_bt_path', 'mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled', 'mirova_equivalent_villarrica_test1', 'mirova_equivalent_f_s81_b_prime_2nd_pass_gate_disabled', 'mirova_equivalent_test1pix_filter', 'mirova_equivalent_f_s81_a_intra_radio_disabled', 'mirova_equivalent_lbg_global', '_mirova_literal', '_s125_cloudmask_on', '_s133_b22_control', '_s135_ab_b_nokeeppeak', '_s133_area_control', '_s126_corona_ctxoff', '_s135_ab_a_control', '_s142_ab_lit_sp_suelto', '_s142_verif_flags_nuevos', '_d12_honest_anchor_modis', '_s142_ab_lit_keep_peak', '_s125_mag_b', '_s125_mag_c', 'mirova_equivalent', '_s124_villarrica_op_ab', '_s135_ab_e_sp_off', '_s129_ab_bgmag', '_baseline_s44', 'mirova_equivalent_bt_path_on_v1', '_s129_ab_pool', '_c2ab_pathd_off', '_s125_viirs_g', '_d8_vent_anchored', 'mirova_equivalent_test1_retire_only_v1', '_d8_d4_per_vol', 'mirova_equivalent_path_d_atm_gate_v1', 'experimental_ndc_focus', 'mirova_equivalent_f_s81_a_intra_radio_enabled', '_s125_mag_a', 'experimental', 'experimental_lowT', '_s142_ab_literal', '_h_d8_5_full', '_s126_corona_on', '_s133_area_corona', '_f70_b', '_s142_ab_lit_con_compuerta'}", `VOLCANO_OVERRIDES` = {}
  - contracara GAP A / D23 (retiro de los Test 1 K1 del pool y de la mascara): APAGADOS: `ENABLE_TEST1_K1_BG_EXCLUDE` = false, `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` = false
  - parametros de la corona Eq. 6 (G-42, apagada): `LOCAL_CLUSTER_MAG_MIN_CORONA` = 4, `LOCAL_CLUSTER_MAG_MODE` = "footprint", `LOCAL_CLUSTER_MAG_RING_PX` = 1
  - parametros del vent-path (G-29, apagado): `MAX_VENT_SIGMA_CONTRIB_K` = 999.0, `MIN_VENT_PIXELS` = 1, `MODIS_VENT_THRESHOLD_K` = 1.0, `MODIS_VENT_VRP_FLOOR_MW` = 0.0, `N_SIGMA_VENT` = 2.0, `VENT_THRESHOLD_K` = 1.0
  - parametros del camino C (G-29, apagado): `NTI_REL_MIN_FLOOR` = 0.005, `NTI_REL_N_SIGMA` = 3.0
  - parametros del VRP TIR (G-42, salida silenciada): `N_SIGMA_TIR` = 4.0, `TIR_THRESHOLD_K` = 0.5, `VRP_TIR_FLOOR_K` = 3.0, `VRP_TIR_N_SIGMA` = 6.0
  - parametros del nucleo espacial y Eq. 16 del Test 1 (G-42, apagados): `TEST1_CORE_BT_EXT_K` = 295.0, `TEST1_CORE_R_KM` = 0.75, `TEST1_LAVA_LAKE_EPS` = 0.95, `TEST1_LAVA_LAKE_TE_K` = 1000.0
  - parametros del fondo local NTI del Test 1 (G-28, apagado): `TEST1_LOCAL_BG_RING_IN_KM` = 0.5, `TEST1_LOCAL_BG_RING_OUT_KM` = 1.5, `TEST1_MIN_LOCAL_BG_PIXELS` = 8
  - parametros de VRPTIR Aveni (G-42, apagado; VRPTIR_K_TIR_I5 ademas no lo lee nadie): `VRPTIR_K_TIR_I5` = 60.17, `VRPTIR_T_MAX_K` = 600.0, `VRPTIR_T_MIN_K` = 300.0
  - parametro del fondo por vecinos D25 (G-42, apagado): `VRP_BG_NEIGHBOR_MAX_HALF_PX` = 3

## 7. VERIFICADO LIMPIO

- Ninguna clave del YAML operacional está escrita en una sección distinta de la que lee `profile.py`
  (140 atributos resueltos). Las únicas claves del YAML que el código no lee son `profile`, `description` y
  `data_subdir` de cabecera.
- El Test 1 no entra a la máscara ni al fondo con los flags de hoy; coincide con la Fase 1 y su verificador.
- `inner_radius_km` coincide en `volcanoes.yaml` y en las tres vistas para los 11 volcanes.
- `f5CoreMagnitude` es idéntica en las tres vistas y el dashboard usa el valor persistido cuando existe.
- Los tres filtros nocturnos usan el mismo umbral.
- No hay ningún `VOLCANO_OVERRIDES` en el perfil operacional, ni overrides de C1 o C2.
- El post-proceso de clasificación de S146 no está cableado a ningún workflow ni a ninguna vista: no cambia
  lo que el operador ve.

## 8. Límites

- La clase ESTA EN EL PAPER se apoya en documentos del proyecto, no en los PDF.
- "No declarado" significa cero menciones en `docs/MIROVA_DIVERGENCES.md` y `docs/MISSION.md` al momento de
  la búsqueda; otro agente está editando esos dos archivos hoy.
- El nulo del Test 1 es de ruido blanco sin correlación espacial sobre grilla regular; un campo real tiene
  textura correlacionada y un disco con menos píxeles fuera del nadir. Sirve para mostrar que el estadístico
  no tiene media cero, no para fijar una tasa.
- Las huellas son de 20 días de fin de invierno.
- Todo esto es hallazgo del que midió. Falta el verificador con contexto limpio.
