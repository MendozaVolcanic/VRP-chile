# Frente D (S146): los cierres que se apoyan en una cifra

> Auditoría de sólo lectura, 2026-09-20. No se tocó `pipeline/`, `frontend/`, perfiles, `data/`, `CLAUDE.md` ni el catálogo. No se usó git para escribir.
> Scripts y salidas crudas: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_auditoria\frente_D\` (`dNN_*.py` y su `.json`).
> Ningún número de este informe está escrito a mano: cada uno sale de un script de esa carpeta y la salida cruda va pegada en la sección 3.
> Ojo con el prefijo: D-01, D-02... son hallazgos de este frente. Las divergencias del catálogo se escriben siempre "divergencia D13", "divergencia D9", etc.

## El fenómeno, antes que los números

Un cierre con cifra apaga un frente con la autoridad de una medición. Lo que encontré no son errores de cálculo: los números se reproducen casi todos. Lo que falla es el NOMBRE que se le puso al conjunto contado. Cuatro formas se repiten:

1. **La etiqueta no es la que el texto dice.** "Real contra artefacto" se midió como "MIROVA publicó contra no publicó" (D-03). "Falsos negativos recuperados" se contó en una ventana donde no existe ninguna referencia de MIROVA (D-04).
2. **Falta la tasa base.** "El pipeline encuentra el cráter el 90 % de las noches con alerta" no dice nada si también pone un cúmulo en el cráter el 98 % de las noches sin alerta (D-02). "Sólo 1,5 % corroborado" no dice nada si lo que sí se publica del mismo sensor da 0,6 % (D-05).
3. **La ventana cruza un cambio de régimen o un hueco del corpus.** La divergencia D9 se cerró con la máscara de nube de 260 K todavía activa (D-01); el libro de cuentas mide 2026 entero (D-06); 45 "falsos negativos" son un hueco de enero sin datos (D-07, D-08).
4. **El denominador de comparación es el equivocado.** Un corrimiento de NTI se declaró despreciable contra un margen de 0,14 cuando el umbral que manda es 0,003 (D-09).

## 1. Cobertura (primero)

Fuente: `d00_cierres_con_cifra.py` (re-ancla los 89 cierres del censo por texto y busca cifras) y `d13_cobertura.py` (el mapa de cierre a categoría es juicio mío, declarado en el script; los conteos salen del script).

```
n_censo 89 | n_no_reanclados 0 | n_movidos 4 | n_cifra_en_linea 19 | n_cifra_en_entorno 74 | n_prioritarios_con_cifra 19
control_regex_vacia 0 | control_positivo_D13 True
total 89
 24  NO_TOCADO_HISTORICO(corpus reprocesado)
 24  REMEDIDO
 15  SIN_CIFRA(fuera del frente D)
 10  CIFRA_ES_PARAMETRO_FISICO_O_CITA(frente C)
  9  NO_TOCADO_por_alcance(salidas de A/B o probes que no estan en disco; tiempo)
  4  YA_AUDITADO_S145
  3  TRAZADO_A_FUENTE
```

| categoría | n | qué significa |
|---|---|---|
| cierres del censo con cifra en su entorno (5 líneas a cada lado) | 74 de 89 | el universo del frente; es un piso (una cifra escrita en palabras no aparece) |
| re-medidos sobre los datos de hoy y sobre la ventana reconstruida | 24 | agrupan 8 familias de números: divergencia D9 (S113), A82 con la divergencia D11, A83, divergencia D13 (S126), divergencia D18, divergencia D20, tabla de parches de MISSION, y el control de la divergencia D13 |
| sólo trazados a su fuente | 3 | A85 (214 noches), divergencia D12 (76 noches), A/B de la divergencia D18. Sus brazos de A/B no están en disco, no se pueden re-medir |
| ya auditados en S145, no recontados | 4 | divergencias D23, D24, D26, D29 (`docs\audit_s145\DIVERGENCIAS_MENORES_VERIFICADAS.md`) |
| la cifra es un parámetro físico o una cita de paper | 10 | "1 km", "260 K", sigma de Stefan Boltzmann: son del frente C |
| no tocados, históricos | 24 | 19 de `docs\HYPOTHESIS_LOG.md` (S18 a S68) y 5 del catálogo (divergencias D8, D8', D-PCC). El corpus se reprocesó varias veces desde entonces (ancla S98, nadir fijo S102 y S103, gates S118, piso S130): sus números no se pueden reconstruir desde `data\` de hoy. SIN DATO, no OK |
| no tocados, por alcance | 9 | cifras de runs de CI o de probes de sesión cuyo resultado no quedó en disco (catálogo l. 289, 435, 656, 1405; `CLAUDE.md` l. 324, 996, 1001, 1114, 1512 del censo). SIN DATO |

**Ampliación fuera del censo** (el censo busca por palabras clave y no los trae, pero son cierres por cifra): A94 y su fuente `experiments\_s136\ETIQUETA_IMPACTO_NETO.md`; A81; A98; A104; `scripts\libro_de_cuentas.py` (4 de sus 13 ids re-medidos; el script NO se ejecutó porque escribe `docs\LIBRO_DE_CUENTAS.json` y corre `pytest --co`); la frase "11 Tier A con serie continua desde 2025-02" de `CLAUDE.md`.

**Control positivo del método** (`d01_control_D13.py`): la divergencia D13. Reproduce exacto el informe S145, incluida la magnitud, con un predicado de publicación reconstruido en Python (no `node`, A97), que queda así calibrado:

```
records_historia_al_2026-08-25 (10770, 34739, 31.0)
records_regimen_actual_0901_0919 (411, 1462, 28.11)
mw_regimen_actual_0901_0919(n,dibuja,sin_cerca,pct_apagado) (2273, 233.29, 797.35, 70.7)
mw_regimen_previo_0601_0825 (9958, 1143.4, 4579.68, 75.0)
```

**Límites declarados.** (a) La referencia MIROVA es la copia local (`latest_consolidado.csv` y `data\mirova_reference\mirova_v1_snapshot\`), no el remoto del dueño. (b) Los records anteriores a un reproceso ya no existen: donde el número de hoy difiere del de entonces lo marco NO REPRODUCIBLE, no refutado, salvo que la definición misma esté mal. (c) "Sin alerta" en mis scripts es "sin fila ALERTA en CONS u OCR", que NO es el "negativo limpio" del banco de paridad. (d) El régimen actual tiene 19 días: sus n son chicos y van impresos. (e) Ningún verificador con contexto limpio revisó todavía estos hallazgos.

## 2. Tabla de veredictos

Gravedad 1 a 5 = cuánto trabajo futuro apaga la cifra si está mal nombrada. Confianza = en MI veredicto.

| id | cierre (archivo:línea de hoy) | la cifra | qué dice contar | qué cuenta en realidad | ventana | veredicto | conf. | grav. |
|---|---|---|---|---|---|---|---|---|
| D-01 | divergencia D9, `docs\MIROVA_DIVERGENCES.md:515-537`; `CLAUDE.md:1547`; `docs\MISSION.md:103` | 199 far con 0 fuga; 207 de 214 = 96,7 % | records fríos de path-D visibles "MIROVA-confirmados ese sensor+noche" | hoy, con ese pareo: 26 de 216 = 12,0 %. El "0 fuga" es circular (la población se define por ser `far`). Medido con la máscara de 260 K activa en V375 | 2026-05-01 a 06-18, régimen previo a #535 | NO REPRODUCIBLE, y NOMBRA OTRA COSA en ventana | media | **4** |
| D-02 | A82, `CLAUDE.md:963`; divergencia D11 `docs\MIROVA_DIVERGENCES.md:1259`; `docs\MISSION.md:106` | "el pipeline encuentra el cráter 90 %" (17 de 19); S130: 97,6 % | detección del cráter en noches MODIS con alerta | presencia de un cúmulo con magnitud dentro del inner, que en MODIS ocurre también en el 98,2 % de las noches SIN alerta | S114: 2026-05-01 a 06-30, n = 19 noches-sensor | NOMBRA OTRA COSA (sin tasa base) | alta | **4** |
| D-03 | A83, `CLAUDE.md:983` (tipo "agotado") | 4.560 records, 37,1 % confirmados, AUC 0,859 | separar "cat-b REAL" de "ARTEFACTO topográfico" | separar "MIROVA publicó esa noche-sensor" de "no publicó". Los 2.870 "artefacto" incluyen los desérticos focales y todo lo real que MIROVA no publica, que es justo la definición de cat-b en A54 | feb a jun 2026 | NOMBRA OTRA COSA (etiqueta) | alta | **4** |
| D-04 | divergencia D12, nota S125 `docs\MIROVA_DIVERGENCES.md:1403`; `docs\AUDIT_S121_D12_AB.md:19,44` | "cura 76 noches de Láscar", "76 noches de FN recuperadas (reales)" | falsos negativos frente a MIROVA recuperados | noches con cúmulo dentro del inner. La ventana del A/B no tiene NINGUNA alerta de MIROVA (la referencia empieza el 2026-01-11) y el script no carga referencia. Hoy hay cúmulo en 90 de 90 noches | 2025-02-15 a 05-15 | NOMBRA OTRA COSA | alta | **3** |
| D-05 | divergencia D13, cierre S126, `docs\MIROVA_DIVERGENCES.md:1540-1546` | "artefacto (37 %)", "corroboraría casi nada (1,5 %)", "sobre todo" | calidad de lo que la cerca esconde | 1,5 % es pareo por MISMO sensor y el 95,2 % de lo apagado es MODIS, donde MIROVA casi no alerta: los MODIS que SÍ se publican dan 0,6 %. Por noche con cualquier sensor: 33,2 % contra 42,9 %. Y 37 % no es "sobre todo" | 2026-05-01 a 08-28 | NOMBRA OTRA COSA (sin nulo, unidad) | alta | **3** |
| D-06 | `scripts\libro_de_cuentas.py:236-240, 275-283` | D5 0,73; V375 0,69; recall V750 85,06 | "el número recalculado hoy" | una mediana sobre 2026 entero, 91,7 % de cuyos pares (1.053 de 1.148, `d16`) son del régimen previo a #535: no puede ver el régimen de hoy (V375 0,848 con `pc.vrp_mw`, 0,906 con `f5_core_vrp_mw`, n = 72). En V375 mide `pc.vrp_mw`, que no es lo publicado | 2026-01-01 a 12-31 | NOMBRA OTRA COSA (ventana, A104) | alta | **3** |
| D-07 | A94 en `CLAUDE.md` y `experiments\_s136\ETIQUETA_IMPACTO_NETO.md` | 946 noches; 94,8 a 95,2 %; "45 noches sin nada = el falso negativo real, es detección" | noches con alerta y fallos de detección | 946 son FECHAS UTC con alguna alerta: 25 sólo tienen alerta diurna, y las 45 "sin nada" son todas de enero 2026 (11 al 28), cuando el corpus no tiene ningún record de ese volcán. Hueco de corpus, no detección. La conclusión de A94 (4 ocultas, 3 de NdC) SÍ se reproduce | toda la serie, referencia al 2026-09-07 | NOMBRA OTRA COSA (denominador); conclusión de A94 en pie | alta | **3** |
| D-08 | `CLAUDE.md` sección Arquitectura; A81 (tabla mensual en `docs\s130\A81_DISCREPANCIA_RESUELTA.md`) | "11 Tier A con serie continua desde 2025-02"; tasa "plana 15 a 17 %, sin un solo quiebre" | serie continua | hay un hueco del 2025-11-16 al 2026-01-28 en 10 de 11 volcanes (PCC desde el 2025-10-10). Las filas 2025-12 y 2026-01 de la tasa mensual son de Villarrica solo | 2025-02 a hoy | NOMBRA OTRA COSA (menor: la tasa plana se sostiene) | alta | 2 |
| D-09 | divergencia D20, `docs\MIROVA_DIVERGENCES.md:2194-2222` (4 entradas "despreciable") | corrimiento de NTI 0,0001 a 0,0054 "contra un margen de ~0,14"; "en el dNTI se cancela" | efecto sobre la detección | se comparó contra el margen al K1 (ruta NTI absoluta, legado). El umbral que gobierna es el piso C1 = 0,003 del dNTI: el residuo diferencial entre un píxel y vecinos 3 a 10 K más fríos es 12 a 74 % de C1 | cálculo de Planck | NOMBRA OTRA COSA (denominador de comparación) | media (cuerpo negro, orden de magnitud) | 2 |
| D-10 | `docs\MISSION.md:142` | máscara de 260 K "ciega ~23 % de las pasadas" | pasadas de V375 cegadas | no encontré script ni JSON que dé 23 % (`experiments\_s124_observabilidad\01_resumen.json` trae otras cifras) | sin declarar | NO REPRODUCIBLE | media | 1 |
| L-01 | divergencia D18, `docs\MIROVA_DIVERGENCES.md:2060-2064` | 9.203 far a summit; mediana 22 km; p10 11,8; ni uno dentro | lo mismo | lo mismo: 9.203 al 2026-08-31; 22,16; 11,86; 0 dentro del inner | toda la serie al 08-31 | NOMBRA LO QUE CUENTA | alta | |
| L-02 | A81 en `CLAUDE.md` | 9.196; 15 a 17 % mensual; 78,5 % de MODIS | lo mismo | hoy 9.541; 14,8 a 17,2 %; 78,3 % | toda la serie | NOMBRA LO QUE CUENTA (con la nota D-08) | alta | |
| L-03 | A82, `CLAUDE.md:963` | recall del dashboard 99 / 86 / 16 % | noches-sensor con alerta | 99,3 / 90,6 / 14,3 en su ventana; 99,0 / 89,8 / 10,0 en todo el régimen previo | 2026-05-01 a 06-30 | NOMBRA LO QUE CUENTA (el n de MODIS, 14 a 19, no se declara en `CLAUDE.md`) | alta | |
| L-04 | A85, `docs\MIROVA_DIVERGENCES.md:1441` | 0 robos en 214 noches focales | lo mismo | 55+46+44+30+39 = 214, 0 robos; además 76 noches de nevados, 0 robos | run 28312968093 | NOMBRA LO QUE CUENTA (trazado) | media | |
| L-05 | A/B de la divergencia D18, `docs\MIROVA_DIVERGENCES.md:2067` | 0 noches perdidas; no reduce detecciones | lo mismo | `n_detecciones` círculo contra caja: igual en 5 de 6, PCC 749 a 743 | 2026-05-29 a 08-24 (régimen previo) | NOMBRA LO QUE CUENTA (trazado); ventana previa a #535 | media | |
| L-06 | A98 en `CLAUDE.md` | 874 de 877 noches | noches de volcán con alerta nocturna y corpus | 921 fechas con alerta nocturna menos 44 del hueco de enero = 877; publicadas 874 | 2026-01-10 a 09-07 | NOMBRA LO QUE CUENTA | alta | |
| L-07 | `docs\MISSION.md:142`, libro `piso_invisibles` | 582 a 0 | records invisibles por el piso | hoy 0 | toda la serie | NOMBRA LO QUE CUENTA | alta | |
| L-08 | A104 en `CLAUDE.md` | 62,1 % y 87,1 % | publicación en negativos limpios de V375 | es por PASADA (87,1 % de 295); por noche es 100 % de 93. `CLAUDE.md` no dice la unidad | tramos antes y después de #571 | NOMBRA LO QUE CUENTA (trazado; unidad omitida) | media | |
| S-01 | divergencia D2, `docs\MIROVA_DIVERGENCES.md:44` | cobertura 79,2 % "cota superior" | pasadas del archivo TIF presentes en el CSV | SOSPECHA, no medido: A106 dice que MIROVA vuelve a servir imágenes viejas con hora nueva (md5 repetido), lo que inflaría el denominador y haría que 79,2 % NO sea cota superior. No abrí el archivo TIF (17 GB, regla S143) | S128 | SIN DATO | | 2 |

Conteo por veredicto sobre las 19 filas: NOMBRA OTRA COSA 8 (D-02 a D-09), NO REPRODUCIBLE 2 (D-01, que además cruza régimen, y D-10), NOMBRA LO QUE CUENTA 8 (L-01 a L-08), SIN DATO 1 (S-01).

## 3. Los que caen, por gravedad, con salida cruda

### D-01 (gravedad 4). Divergencia D9 "efectivamente resuelta en sus dos caras": el 96,7 % no se reproduce y la ventana es de otro régimen

**Fenómeno.** Una escena con fondo muy frío (menos de 262 K) puede ser cirrus alto o puede ser simplemente un volcán de 5.600 m. S113 cerró la divergencia D9 diciendo que casi todo lo frío visible era lo segundo, porque MIROVA lo confirmaba "ese sensor+noche" en 207 de 214 casos, y que por eso un filtro por temperatura de fondo mataría detecciones reales. La definición vive sólo en la memoria del agente (`reference_s113_cirrus_d9_scope.md`): no hay script en el repo.

**Lo medido** (`d10`, `d10b`; definición mía declarada: `t_bg_k < 262`, path-D dominante, `pc.vrp_mw > 0`). La población se reproduce (216 far y 216 summit contra 199 y 214), la confirmación no:

```
"ctx>resto|frio<262": n 216 | mismo_sensor_misma_fecha [26, 12.0] | cualquier_sensor_misma_fecha [88, 40.7]
                              mismo_sensor_pm1dia [53, 24.5]      | cualquier_sensor_pm1dia [159, 73.6]
"ctx>resto|NO frio (nulo)": n 1296 | [681, 52.5] | [832, 64.2] | [851, 65.7] | [1010, 77.9]
```

Con cualquier definición de "confirmado", lo frío se confirma MENOS que lo no frío. Ni la variante más generosa llega a 96,7 %. Por volcán, la confirmación se concentra en Láscar (29 de 29), Lastarria (32 de 33) y PCC (56 de 60); Llaima 0 de 8, Villarrica 2 de 13, Chaitén 3 de 13. Atenuante honesto: los records de mayo y junio se reprocesaron después de S113, así que no puedo afirmar que S113 calculó mal; afirmo que hoy el número no está en ningún lado y no se reproduce.

El "199 con 0 fuga al dashboard" es circular: la población se define como `far` y la cerca apaga lo `far`.

**La ventana.** S113 midió con la máscara de 260 K activa en VIIRS 375, que borraba justo las escenas frías. Summit fríos de path-D por sensor:

```
S113(05-01..06-18)            summit n 216: v750 162, v375 16,  modis 38 | confirmados 26 (12.0 %)
previo_invierno(07-01..08-28) summit n 416: v750 286, v375 34,  modis 96 | confirmados 19 (4.6 %)
actual(09-01..09-19)          summit n 300: v375 217, v750 70,  modis 13 | confirmados 75 (25.0 %), no confirmados 225, max 5.0 MW
```

VIIRS 375 pasó de 34 en 59 días a 217 en 19 días. "No quedan acciones abiertas en D9" se escribió sobre un régimen que ya no existe. El tope de 5 MW sí sigue actuando (máximo 5,0 en los tres tramos).

### D-02 (gravedad 4). "En MODIS el pipeline SÍ encuentra el cráter (90 %)": la tasa base es 98 %

**Fenómeno.** El argumento que cierra la cara MODIS de la divergencia D11, y que sostiene la lectura de la divergencia D12 y de A81 ("no es falta de detección, es 100 % el bug de etiquetado"), es que en las noches con alerta MODIS de MIROVA nuestro cúmulo está en el cráter. Pero en MODIS hay un cúmulo con magnitud dentro del inner casi TODAS las noches, con o sin volcán encendido (`d12`; tuplas = con cúmulo, total, %):

```
previo(01-29..08-28)  modis con_alerta [50, 50, 100.0]   sin_alerta [2234, 2276, 98.2]
                      v750  con_alerta [193, 226, 85.4]  sin_alerta [1158, 2106, 55.0]
                      v375  con_alerta [805, 819, 98.3]  sin_alerta [1215, 1513, 80.3]
actual(09-01..09-19)  modis [1, 1, 100.0] / [200, 208, 96.2] | v750 [13, 14, 92.9] / [96, 195, 49.2] | v375 [72, 72, 100.0] / [137, 137, 100.0]
```

100 % contra 98,2 % no es "encontrar el cráter": es un detector que en MODIS no discrimina. El número del cierre cuenta presencia de cúmulo, no detección. Coincide con lo que S137 encontró por otra vía (la banda 21 fabrica el primer paso de MODIS, divergencias D21 y D22) y con `d04`: el 78,3 % de TODOS los records MODIS son far a summit. El recall del dashboard por sensor (99 / 86 / 16) sí se reproduce (L-03). Nota: "sin alerta" acá no es negativo limpio (límite c).

### D-03 (gravedad 4). A83 "agotado": la etiqueta del AUC es "MIROVA publicó", no "real contra artefacto"

`experiments\_s116_followup\c2_discriminator.json` lo declara: `tp_label: ALERTA_TERMICA (vol,noche,sensor-bucket) +/-1 dia`, `n_tp_mirova_alerta 1690`, `n_ntp 2870`, y llama `artifact_rejection` al rechazo de los 2.870. Entre esos "artefactos" están 1.517 records de volcanes focales desérticos (donde el propio estudio dice que no hay artefacto topográfico) y todo lo real que MIROVA no publica, que según A54 es el 46 % de los no publicados y es la definición misma de cat-b. La regla usa "cat-b real" para lo confirmado por MIROVA, al revés que A54.

Re-medido hoy con esa misma etiqueta (`d08`), con nulo barajando etiquetas DENTRO de cada volcán:

```
S116_pudo_ver(02-01..06-27),solo_recapture  todos: n_pos 1430 n_neg 1972 auc 0.762 nulo 0.57
                                            v375: auc 0.655 nulo 0.589 | v750: auc 0.711 nulo 0.647 | modis: n_pos 5, SIN DATO
previo(01-29..08-28)   todos 0.684 (nulo 0.538) | v375 0.625 (nulo 0.606) | v750 0.594 (nulo 0.555)
actual(09-01..09-19)   todos 0.667 (nulo 0.521) | v375 0.635 (nulo 0.614) | v750 0.5   (nulo 0.558)
```

El 0,859 no se reproduce hoy (0,762 en la ventana reconstruida; el corpus se reprocesó). Y por sensor casi todo el AUC es "de qué volcán es el record" (el nulo ya da 0,59 a 0,65). Esto REFUERZA la parte de A83 que dice que no hay escalar por record; lo que cae es el nombre: A83 no midió real contra artefacto, y no puede apagar esa búsqueda. Tampoco midió lo que hoy importa (A98): un predictor de "MIROVA publicaría".

### D-04 (gravedad 3). Divergencia D12: las "76 noches de FN recuperadas" no tienen contra qué ser FN

`d15`:

```
"n_alertas": 2010, "gt_fecha_min": "2026-01-11", "gt_lascar_min": "2026-01-11",
"alertas_en_ventana_AB_2025-02-15_05-15": 0,
"lascar_modis_noches_en_ventana": 90, "con_cumulo_dentro_del_inner": 90
```

El A/B de S121 corrió sobre 2025-02-15 a 05-15. La referencia de MIROVA empieza el 2026-01-11: en esa ventana hay 0 alertas. `experiments\_s121_d12_ab\analyze.py` no carga ninguna referencia (l. 75: "noches curadas (far a summit con cluster menor o igual al inner)"). "Reales" y "FN recuperadas" son adjetivos sin medición. Con la tasa base de D-02 (hoy 90 de 90 noches tienen cúmulo), 76 es lo esperable sin volcán. El veredicto NO ADOPTAR no depende de esto y sigue en pie; lo que cae es que exista una "cura real y valiosa" medida.

### D-05 (gravedad 3). Divergencia D13, cierre S126: el 1,5 % mide la rareza de las alertas MODIS de MIROVA

`d07` reproduce la población (2.704 de 8.044 contra 2.694 de 8.033; anillo 37,6 % contra 36,9 %) y muestra que el 95,2 % de lo apagado es MODIS (97,6 % en MW). `d07b`:

```
apagado|modis   n 2573 mismo_sensor 27 (1.0 %)    noche_cualquier_sensor 862 (33.5 %)
apagado|todos   n 2704 mismo_sensor 41 (1.5 %)    noche_cualquier_sensor 899 (33.2 %)
publicado|modis n 339  mismo_sensor 2  (0.6 %)    noche_cualquier_sensor 131 (38.6 %)
publicado|todos n 5340 mismo_sensor 1755 (32.9 %) noche_cualquier_sensor 2290 (42.9 %)
```

Los MODIS que el dashboard SÍ muestra se corroboran menos (0,6 %) que los que esconde (1,0 %). En la unidad del operador (noche, cualquier sensor) lo escondido coincide con una noche de alerta el 33,2 % de las veces y lo publicado el 42,9 %. "Corroboraría casi nada" no se sostiene; "destaparía sobre todo artefacto (37 %)" tampoco: 37,6 % en el anillo, 15,6 % a menos de 1 km, 15,8 % fuera del inner. Y el 37 % no tiene nulo: MODIS tiene píxeles de 1 km y un cúmulo a 1,5 a 3 km del cráter es geometría esperable (SOSPECHA, no medido). "D13 deja de ser una palanca" queda sin el número que lo sostenía.

### D-06 (gravedad 3). El libro de cuentas no puede ver el régimen de hoy

`d05` replica sus funciones (control: 0,741 / 0,70 / 85,49, dentro de su banda) y las parte (tuplas = n de pares, mediana):

```
libro(2026 entero)     global [1148, 0.741] v375_pc [887, 0.7]   v375_f5core [887, 0.824] v750 [210, 0.814] modis [51, 1.073] recall_v750 [218, 255, 85.49]
previo(01-01..08-28)   global [1053, 0.73]  v375_pc [808, 0.689] v375_f5core [808, 0.811] v750 [195, 0.828] recall_v750 [203, 239, 84.94]
actual(09-01..09-19)   global [86, 0.825]   v375_pc [72, 0.848]  v375_f5core [72, 0.906]  v750 [13, 0.649]  recall_v750 [13, 14, 92.86]
```

(1) La ventana es el año entero y cruza #535 y #571: dirá OK por inercia durante meses. (2) `ratio_v375` usa `pc.vrp_mw`, que en V375 no es lo que el operador ve (`f5_core_vrp_mw`). (3) Consecuencia para A99 ("magnitud ~0,7"): ese 0,7 es del régimen previo; hoy es 0,85 a 0,91 con n = 72 (chico, sin intervalo: SOSPECHA de cambio, no medición cerrada). (4) Además el script escribe un archivo y corre `pytest --co`, así que un auditor de sólo lectura no puede ejecutarlo.

### D-07 (gravedad 3). Las 45 "noches sin nada" de S136 son un hueco de enero

`d02` reproduce exacto 946 / 897 / 4 / 45. `d02b`:

```
n = 45 | por mes: [('2026-01', 45)] | 'otros Tier A con record esa fecha': [(1, 45)]
fechas_solo_alerta_diurna 25 | sin_nada_sin_ningun_record 45 | NOCT_total 921 | NOCT_publica 874 | NOCT_oculta 3
```

Las 45 son del 11 al 28 de enero de 2026, fechas en que sólo Villarrica tiene records. El documento las presenta como "el falso negativo real... es detección" (Puyehue 14, Láscar 10, Lastarria 10). El recall del gate no es 94,8 %: sacando el hueco y las fechas sólo diurnas es 874 de 877 (el número de A98). La conclusión de A94 sobrevive: 4 ocultas (NdC 3, Tupungatito 1).

### D-08 (gravedad 2). "Serie continua desde 2025-02": no lo es

`d03` (días con al menos un record por mes):

```
2025-10     31 en diez volcanes, PCC 9
2025-11     15 en nueve volcanes, Villarrica 30, PCC 0
2025-12      0 en diez volcanes, Villarrica 31
2026-01      3 en diez volcanes, Villarrica 31
```

Todo número "sobre toda la serie" tiene 74 días sin 10 volcanes (111 días en PCC), fechas exactas en `d16`. La tasa mensual de A81 en 2025-12 y 2026-01 es de Villarrica solo (dentro de MODIS sube a 93,7 % en diciembre, `d04`). La conclusión de A81 (tasa plana) se sostiene en los otros 18 meses.

### D-09 (gravedad 2). Divergencia D20: despreciable contra el umbral equivocado

`d09` reproduce el cálculo de S128 (8e-05 a 250 K, 0,00539 a 290 K) y agrega lo que sobrevive en el dNTI:

```
T=270,dT=3: -0.00036 | T=280,dT=3: -0.00054 | T=290,dT=3: -0.00074 | T=280,dT=10: -0.00158 | T=290,dT=10: -0.00222
C1_summit 0.003 | peor_caso_como_fraccion_de_C1_summit 0.74
```

El corrimiento no es uniforme: crece con la temperatura, así que entre un píxel y vecinos más fríos queda un residuo de 12 % (3 K a 270 K) a 74 % (10 K a 290 K) del piso C1 de cumbre. Dirección: con banda 31 un píxel de terreno más tibio que sus vecinos recibe un dNTI algo MENOR que con banda 32. Es un modelo de cuerpo negro homogéneo: sirve para decir que "despreciable" se juzgó contra 0,14 en vez de 0,003, no para dar el valor.

### D-10 (gravedad 1). "Ciega ~23 % de las pasadas"

Sin fuente localizable. La máscara ya se retiró (#535), así que no apaga nada.

## 4. Verificado limpio

- **Control de la divergencia D13**: 10.770 / 34.739 = 31,0 %; 233,29 y 797,35 MW; 70,7 % y 75,0 %. Idéntico a S145.
- **Divergencia D18** (L-01, L-05): 9.203, 22,16 km, 11,86 km, 0 dentro del inner; el A/B contó detecciones y no cambian.
- **A81** (L-02), **A82 recall por sensor** (L-03), **A85** (L-04), **A98** (L-06), **piso VRP** (L-07), **A104** (L-08).
- **A94, la conclusión**: 4 noches enteramente ocultas, 3 de NdC y 1 de Tupungatito, reproducido exacto.
- **Libro de cuentas, control**: mis réplicas caen dentro de sus bandas (0,741 / 0,70 / 85,49), o sea que el libro calcula lo que dice; lo que falla es la ventana (D-06).
- **Divergencias D23, D24, D26, D29**: ya auditadas en S145, no recontadas.

## 5. Correcciones sugeridas (redactadas, NO aplicadas)

1. Divergencia D9: cambiar "EFECTIVAMENTE RESUELTA... no quedan acciones abiertas" por "cerrada bajo el régimen con máscara de 260 K; sin re-medir desde #535", y retirar "207 (96,7 %)" o marcarlo sin script.
2. A82, divergencias D11 y D12: toda frase "el pipeline encuentra el cráter N %" lleva al lado la tasa en noches sin alerta.
3. A83: reemplazar "cat-b real contra artefacto" por "publicado por MIROVA contra no publicado".
4. `docs\AUDIT_S121_D12_AB.md` y nota S125: "76 noches con cúmulo dentro del inner (sin referencia MIROVA en la ventana)".
5. Divergencia D13, cierre S126: retirar "corroboraría casi nada (1,5 %)" o darlo con su nulo.
6. `scripts\libro_de_cuentas.py`: ventanas por régimen, `f5_core_vrp_mw` en V375, y una opción de no escribir.
7. `CLAUDE.md`: "serie desde 2025-02 con un hueco del 2025-11-16 al 2026-01-28 en 10 de 11"; en A94, "946 fechas UTC" y quitar las "45 noches" como frente de detección.
