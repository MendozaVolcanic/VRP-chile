# Auditoría VS34: sombra aislada de los 34 volcanes (rama claude/s172-sombra-34)

## 1. Encabezado

- Hora del servidor (date -u de esta máquina): lunes 2026-11-02 02:14 UTC al cerrar; la sesión partió a las 01:45 UTC.
- Commit medido: 30d9f9418 (rama claude/s172-sombra-34), contra la base pre-s172-sombra-34 (main 14fb62030). Worktree leído sin editar: D:/vrp-trabajo/worktrees/s172-sombra34. Las mutaciones se hicieron en una copia (git archive) en CARPETA/copia.
- Modelo: Sonnet 5.5, esfuerzo bajo.
- CARPETA: D:/vrp-trabajo/temporales/ver_s172_sombra34/ (scripts con su salida al lado; hallazgos.csv; caminos.md, sha256 1162f97f842be44db7d012466a56c8062614261616f7794542b02150a72f9523, escrito a las 01:49:50 UTC, después de una primera pasada de lectura: no recibí hallazgos ajenos, así que no fue una verificación ciega).
- Qué NO miré: ningún gránulo real (la vía nunca corrió en un volcán de los 34); la suite completa; el relector (rama claude/s172-v375e-relector); el contenido de scripts/revisar_sombra.py más allá de las primeras 120 líneas; cuánto tarda cada job o cuánto carga LAADS con 34 jobs (SIN DATO); si MIROVA excluye vecinos en Chile (SIN DATO); la API de GitHub (0 llamadas); el estado real de los crons en Actions.

## 2. En una pantalla

Veredicto global: **LISTA CON CAMBIOS**. Grillas, perfil y workflow están bien hechos y no tocan producción ni la sombra de los 11 (V-1 y V-2 limpios; el único archivo que el lector sellado marca es la grilla, como el autor declara).
Lo que importa para un geólogo (V-4, CONFIRMADO con el código): en 4 volcanes nuevos el calor de un vecino activo de los 11 (Villarrica en Quetrupillán, Chaitén en Michinmahuida, Puyehue-Cordón Caulle en Antillanca, Copahue en Callaqui) entra en la magnitud, el conteo de píxeles y la posición del volcán nuevo, sin etiqueta que lo distinga; con datos de los 11 el vecino está activo en 0 a 34 % de las pasadas según sensor (estimación).
Los 52 tests nuevos son verdes y 24 de 34 mutaciones propias caen, pero 10 pasan en verde, entre ellas "la vigilancia ya no abre issue en CIEGA", que es justo lo que la vigilancia debe garantizar.
Antes del merge: decidir cómo se lee a los 12 volcanes con vecino (idealmente sin tocar pipeline/), cerrar el test de la vigilancia y revisar el efecto en Pages. Orden de merge: después del relector.

## 3. Hallazgos (peor primero)

### VS34-01
- TÍTULO: El calor de un volcán vecino activo se cuenta como anomalía del volcán nuevo (4 casos con vecino de los 11, 12 volcanes con algún vecino)
- ARCHIVO:LÍNEA: pipeline/mirova_v750_codigo.py:397 a 466 (detectar_mirova: Test 1 absoluto en toda celda no NaN, umbrales de BOX 0 en el resto), :584 a 606 (vrp_mirova suma todos los alertados), :687 a 744 (procesar_grilla: cúmulo del píxel más radiante, distance_class None sin inner); SCRIPT:SALIDA v4_vecinos_geometria.py:v4_vecinos_geometria_salida.txt, v4_vecinos_sintetico.py:v4_vecinos_sintetico_salida.txt, v4_vecinos_datos.py:v4_vecinos_datos_salida.txt
- QUÉ PASA: Un lago de lava o un domo caliente a 17 a 25 km del volcán nuevo cae dentro de su grilla de 51 x 51 km, en la zona BOX 0 (fuera de la caja sensible), y la vía no lo excluye: el Test 1 (NTI mayor a -0,7) alerta en cualquier celda y la contextual usa el piso estricto. La magnitud es la suma de TODOS los alertados, así que el record del volcán tranquilo lleva la magnitud del vecino; y como el cúmulo elegido es el del píxel más radiante, el centroide y final_hotspot caen en el vecino, con distance_class null (los 34 no tienen inner_radius_km). Si hay calor propio débil y del vecino fuerte, quedan mezclados en un solo vrp_mw. El código de MIROVA dice que sus ROI pueden adaptarse para excluir volcanes vecinos (docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md l. 95 a 96, TEXTO, paráfrasis mía); si lo aplica en Chile es SIN DATO. La grilla no tiene campo para excluir celdas.
- Medido (gránulo sintético sin red, foco de 320 K SOLO en las coordenadas del vecino, nada en el cráter del objetivo; fondo 270 K): Quetrupillán con foco en Villarrica da vrp_mw 29,35 (V750), 13,65 (V375), 18,93 (MODIS), n_anom 4, 15 y 2, cúmulo a 19,4 a 19,5 km; Michinmahuida con Chaitén 13,48 / 6,74 / 10,86 a 17,3 a 17,6 km; Antillanca con Puyehue-Cordón Caulle 24,43 / 13,31 / 18,97 a 19,9 a 20,2 km; Callaqui con Copahue 17,56 / 10,17 / 19,12 a 24,4 a 24,8 km. Control negativo (sin foco): vrp 0 y n_anom 0 en los 7 pares; control positivo (foco en el cráter propio): vrp 9,5 a 18,9 MW y cúmulo a 0,0 km. Con foco de 300 K los valores bajan (11,8 / 3,5 / 6,7 para Quetrupillán); el mecanismo es el mismo.
- Frecuencia con datos de los 11 (ESTIMACIÓN: detector K sobre píxeles de barrido, no la vía; pasadas nocturnas del 2026-08-01 al 2026-10-31, denominador por sensor en la salida): pasadas con VRP mayor a 0 en el vecino, VIIRS 375 / VIIRS 750 / MODIS: Villarrica 7,7 / 1,7 / 1,4 %; Chaitén 12,0 / 0,2 / 0 %; Puyehue-Cordón Caulle 33,6 / 10,6 / 8,3 %; Copahue 8,5 / 1,5 / 0 %; medianas de 0,10 a 0,83 MW. NTI absoluto mayor a -0,7: 0 % en los cuatro. Es del orden de lo que se espera de un volcán nuevo tranquilo, así que la contaminación puede ser del tamaño de la señal propia.
- Geometría: 12 de los 34 (no 11) tienen otro volcán del yaml dentro de la celda de la grilla; ver VS34-07. Los vecinos de los 11 caen siempre en BOX 0 (a 17,5 a 24,5 km); Descabezado Grande y Cerro Azul-Quizapú (8,2 km) y Lonquimay-Tolhuaca (9,6 km) caen en BOX 1 en V750.
- CÓMO SE VE EN EL DASHBOARD: invisible (la sombra no se publica). Pero los datos de la sombra son los que decidirán si los 34 se publican: Quetrupillán, Michinmahuida, Antillanca-Casablanca y Callaqui aparecerían como los volcanes nuevos más activos por calor que no es suyo.
- CÓMO REPRODUCIRLO: python -I D:/vrp-trabajo/temporales/ver_s172_sombra34/v4_vecinos_sintetico.py (Quetrupillán, familia VIIRS750, foco en Villarrica -39.42/-71.93, noche sintética); datos: python -I .../v4_vecinos_datos.py.
- CONFIANZA: CONFIRMADO el mecanismo (código y salida sintética); la frecuencia real es ESTIMACIÓN; lo que hace MIROVA, SIN DATO.
- GRAVEDAD: 4 (sesga la decisión de publicar 4 volcanes; no toca alertas de los 11).

### VS34-02
- TÍTULO: Pruebas que no pueden fallar: 10 de 34 mutaciones propias pasan en verde, incluida "la vigilancia ya no abre issue"
- ARCHIVO:LÍNEA: tests/test_sombra_34_s172.py:279 a 286 (test_workflow_de_vigilancia_abre_issue: sólo busca subcadenas), :223 a 245 (workflow); SCRIPT:SALIDA v5_mutaciones.py:v5_mutaciones_salida_total.txt
- QUÉ PASA: El test de la vigilancia comprueba que el texto "CIEGA)" y "gh issue create" estén en el YAML, no lo que hace el case. Cambiar `OK|ESPERA)` (vigilancia-sombra-34.yml l. 77) por `OK|ESPERA|CIEGA)` deja el texto "CIEGA)" presente, el case ya no abre issue nunca, y los 52 tests siguen verdes (mismo patrón de A92). Tampoco caen: `--dir` apuntando a data/sombra_codigo_mirova (la vigilancia miraría la sombra de los 11 y daría verde con la de los 34 muerta), un cron imposible (31 de febrero), el checkout de otra rama, `if: always()` perdido en la revisión de records y en el tachado del log, permissions contents write a read (el push fallaría), timeout del paso de 75 a 5 min, roi_v750 de un volcán nuevo cambiado de def a sens, y que vigilar_sombra_34.py salga con 0 aun en CIEGA (este último no afecta al workflow, que lee el JSON).
- CÓMO SE VE EN EL DASHBOARD: invisible; un cambio futuro a la vigilancia o al workflow pasaría el CI sin avisar y la sombra quedaría ciega sin issue.
- CÓMO REPRODUCIRLO: en una copia, cambiar `OK|ESPERA) echo` por `OK|ESPERA|CIEGA) echo` en .github/workflows/vigilancia-sombra-34.yml y correr python -m pytest tests/test_sombra_34_s172.py -q: "52 passed". Detalle: v5_mutaciones.py (nombres VW1 a VW4, W8 a W12, G4, V5).
- CONFIANZA: CONFIRMADO (lo medí). Lo que SÍ cae: 24 de 34 (grillas movidas o borradas, zona UTM, cron en horas del NRT, usuario y clave, volcán fuera de la matriz, git add de otra carpeta, grupo push-main, token vacío, otro perfil, perfil con test1, vías apagadas, overrides, truthy en la vía, ventana de 480 h, perfil ignorado, matriz vacía, any en vez de all, permissions de issues, issue que nunca crea).
- GRAVEDAD: 3 (la vigilancia ciega es el aviso de que la sombra murió).

### VS34-03
- TÍTULO: pages-deploy copia todo data/ al sitio público; data/sombra_34 suma al menos 0,7 MB por día y dispara un deploy por cada push
- ARCHIVO:LÍNEA: .github/workflows/pages-deploy.yml:69 (`cp -r data _site/data`; disparador `paths: "data/**"`; `concurrency: group pages, cancel-in-progress: true`); SCRIPT:SALIDA v2_tamano_registro.py:v2_tamano_registro_salida.txt, v2_pages_data_gzip_salida.txt
- QUÉ PASA: Todo lo que se commitea bajo data/ sale en el sitio de GitHub Pages que sirve el tablero. data/ ya pesa 808,2 MB en main 14fb62030 (suma de git ls-tree) y 82,8 MB comprimido (gzip -6 de git archive). Un record de la vía sin alertados pesa 1.862 bytes con indent=2 (con un foco 4.073, con un cúmulo grande 9.118); a 11,3 records por día y volcán (proxy: Villarrica K, ago a oct 2026) los 34 aportan al menos 0,72 MB por día, unos 262 MB por año. Los 34 pushes diarios disparan además 34 corridas de pages-deploy con cancel-in-progress, que se cancelan entre sí durante la hora y media que dura la sombra.
- El límite: la página de límites de GitHub Pages (leída con WebFetch esta sesión, respuesta de un modelo pequeño, no la página renderizada) dice que los sitios publicados no pueden pasar de 1 GB. Si ese 1 GB se mide sobre el sitio sin comprimir, quedan unos 192 MB de margen y la sombra de los 34 sola los agotaría en unos 267 días en la cota baja (menos si hay alertas); si se mide sobre el artefacto comprimido hay mucho margen. No lo pude distinguir: SIN DATO.
- CÓMO SE VE EN EL DASHBOARD: si el deploy falla por tamaño, el tablero deja de actualizarse (visible como deploy rojo, no como error en pantalla). Hoy no hay problema.
- CÓMO REPRODUCIRLO: python -I v2_tamano_registro.py; git archive 14fb62030 data | gzip -6 | wc -c.
- CONFIANZA: CONFIRMADO que data/ se copia entero y los números de tamaño; SOSPECHA el efecto sobre el límite.
- GRAVEDAD: 2.

### VS34-04
- TÍTULO: La vigilancia de la sombra de los 34 no la vigila nadie y comparte con la sombra la misma dependencia del cron de GitHub
- ARCHIVO:LÍNEA: .github/workflows/vigilancia-sombra-34.yml (schedule "27 23 * * *"), .github/workflows/nrt-monitor.yml:139 a 190 (la regla de ausencia existe sólo para sombra-codigo-mirova.yml)
- QUÉ PASA: Para la sombra de los 11 hay dos capas: la vigilancia de datos frescos y una regla de ausencia en nrt-monitor (sin corrida verde en 26 h abre issue). Para los 34 sólo hay la primera. Los crons de GitHub de este repo llegan con horas de atraso (lo dice el informe de capacidad S172 para la experimental y la sombra de los 11), y si GitHub no entrega el evento schedule, la sombra y su vigilancia caen juntas sin que un tercero lo note. El diseño interno es bueno (SIN_VEREDICTO abre issue, matriz vacía es CIEGA, ESPERA sólo hasta 48 h después de max(2026-11-03, alta)).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: grep -n "sombra" .github/workflows/nrt-monitor.yml (sólo sombra-codigo-mirova.yml); no hay referencia a sombra-34 ni a vigilancia-sombra-34 fuera de sus propios archivos y tests.
- CONFIANZA: CONFIRMADO que falta la capa; SOSPECHA que el modo de falla ocurra.
- GRAVEDAD: 2.

### VS34-05
- TÍTULO: Los 34 no tienen ancla de cráter: la caja sensible y las distancias se miden desde el punto GVP del yaml
- ARCHIVO:LÍNEA: volcanoes.yaml (los 11 tienen vent_lat y vent_lon, los 34 ninguno; mirova_center tampoco); pipeline/mirova_v750_codigo.py:253 a 294 (caja_roi 'def' centrada en n // 2) y :788 a 828; pipeline/geo_utils.py:53 a 78 (get_detection_anchor); SCRIPT:SALIDA v1_grillas_salida.txt
- QUÉ PASA: En V750 y MODIS la zona sensible (7 x 7 celdas, 5,25 km, y 5 x 5, 5 km) queda en el centro de la grilla = el lat/lon del yaml con tres decimales (~110 m), no en el cráter; en los 11 el cráter lo verificó Nicolás en terreno. En edificios grandes (caldera del Hudson, campo de Laguna del Maule, complejos como Descabezado Grande) el foco activo puede quedar fuera de la caja sensible y tratarse con el piso estricto, y centroid_dist_km se mide desde un punto que puede no ser el cráter. En 3 de los 11 el punto de MIROVA está a 0,23, 1,9 y 2,8 km del yaml (cabecera de grillas_mirova.yaml), y esa corrección no se puede hacer para los 34.
- CÓMO SE VE EN EL DASHBOARD: invisible; afecta la comparabilidad "es como en los 11" en que se apoya la decisión.
- CÓMO REPRODUCIRLO: en el worktree, python -I -c "import yaml;v=yaml.safe_load(open('volcanoes.yaml',encoding='utf-8'))['volcanoes'];print([x['name'] for x in v if x.get('vent_lat') is not None])" (da sólo los 11).
- CONFIANZA: CONFIRMADO que no hay ancla; SOSPECHA que cambie qué detecta.
- GRAVEDAD: 2.

### VS34-06
- TÍTULO: Una prueba vieja ajustada usa "tiene inner_radius_km" como sustituto de "es Tier A" y se romperá cuando se decida el inner de los 34
- ARCHIVO:LÍNEA: tests/test_mirova_v375_codigo_s165.py:117 a 130; SCRIPT:SALIDA v5_viejas_mutaciones.py:v5_viejas_mutaciones_salida.txt (O5)
- QUÉ PASA: El ajuste filtra los volcanes con grilla por `inner_radius_km is not None` para quedarse con 11. Dar un inner a un volcán de los 34 (decisión D5 pendiente) lleva la cuenta a 12 y la prueba cae con "assert 12 == 11", un mensaje que no apunta a la causa. Las dos pruebas viejas sí pueden fallar por lo que cambiaron (sin grilla de Láscar cae la de la sombra de los 11; una grilla inventada para cualquier nombre cae por el control "VolcanSinGrilla"); la de la caja 375 compara dos implementaciones sobre la misma grilla, así que no fija posiciones (mover Láscar 300 m no la hace caer; eso lo cubre test_grilla_reproduce_las_esquinas_de_miroVA). Además test_volcan_por_coordenadas_reconoce_los_11_con_grilla (tests/test_mirova_v750_cableado_s162.py:91) ahora recorre 45 y su nombre quedó viejo. La mutación O4 de ese archivo de salida es un no-op mío (cadena igual) y no cuenta.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: en la copia, añadir `inner_radius_km: 5` a Hudson en volcanoes.yaml y correr pytest tests/test_mirova_v375_codigo_s165.py -k caja_de_375.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VS34-07
- TÍTULO: El informe de la rama cuenta 11 de 34 con vecino en la grilla; por geometría de celdas son 12 (Osorno con Calbuco, en la fila de borde)
- ARCHIVO:LÍNEA: experiments/_s172_sombra34/vecinos_en_la_grilla.py (corte |dx| y |dy| menor o igual a 25.000 m); SCRIPT:SALIDA v4_vecinos_geometria.py:v4_vecinos_geometria_salida.txt
- QUÉ PASA: Con el cuadrado real de celdas, Calbuco cae a 27,5 km de Osorno dentro de la grilla de V750 y MODIS, en la fila o columna de borde, que detectar_mirova pone en NaN (box[:, [0, -1]] y box[[0, -1], :]). Calbuco queda sin alertar, pero sus vecinas interiores pueden recibir su calor interpolado. Efecto pequeño; el conteo del informe es una cota inferior.
- CÓMO SE VE EN EL DASHBOARD: invisible. CÓMO REPRODUCIRLO: python -I v4_vecinos_geometria.py (líneas "Osorno | VIIRS750 | Calbuco | 27.5 | NaN(borde)"). CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### VS34-08
- TÍTULO: Mergear antes del relector hace que el lector sellado de V375-E marque cambio de régimen por la grilla (conocido); el relector debe comparar sólo las 11
- ARCHIVO:LÍNEA: experiments/_s168/v375e_sombra/leer_sombra_v375e.py en el tag s170-v375e-lector (RUTAS_REGIMEN l. 95, cambio_significativo, grillas_sin_roi); SCRIPT:SALIDA v2_lector_regimen.py:v2_lector_regimen_salida.txt
- QUÉ PASA: Con las funciones del lector sellado extraídas por ast, entre la base y la punta de la rama sólo cuentan como cambio de régimen pipeline/grillas_mirova.yaml (True: sin las claves de ROI la grilla difiere porque hay 34 claves nuevas) y pipeline/profiles/sombra_34.yaml (False: el lector sólo mira dos perfiles). Es lo que el autor declara. El relector tiene que comparar por volcán (las 11 intactas), no el archivo entero, o marcará régimen en cualquier adición futura. Control positivo: entre dos commits de main que tocaron process_viirs.py, el mismo script marca 30 archivos de pipeline/ y volcanoes.yaml como cambio.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 3 si se mergea en el orden equivocado, 1 en el orden indicado. CÓMO SE VE: el lector devolvería régimen cambiado (invisible para el operador). CÓMO REPRODUCIRLO: python -I v2_lector_regimen.py.

## 4. SEGUIMIENTOS (fuera de mi eje o sin medir)

- La vigilancia exige un record de la vía por volcán en 48 h: para los del extremo norte (Taapacá, Parinacota, Guallatiri, a -18 grados) con menos pasadas utilizables podría dar CIEGA de más; el autor lo dice en su INFORME (SIN VERIFICAR). scripts/vigilar_sombra_34.py:vigilar. SOSPECHA.
- Cuando la vía no puede correr (MODIS sin MxD03) el procesador sigue K con radius_km 5 del yaml: cuánto pasa y qué fondo le queda a K con ese radio no se midió. scripts/run_pipeline.py:252 a 275, pipeline/store.py:349. SOSPECHA.
- nrt.yml mantiene un cron de GitHub "0 */2" que llega con horas de atraso: la frase "no se cruza con el NRT" de sombra-34.yml depende de los despachos externos de las 01 a 12 UTC; un NRT atrasado podría cruzarse, y en el peor caso 8 + 8 + 4 + 4 = 24 jobs piden más que el tope de 20 (hace cola, no falla). SOSPECHA.
- git archive en esta máquina (autocrlf true) saca los archivos en CRLF mientras los blobs son LF; el test de los 3.805 bytes ya normaliza, pero cualquier guard que compare bytes sin normalizar vería otra cosa localmente. No lo medí en esas pruebas.

## 5. VERIFICADO LIMPIO

- V-1, las 11 grillas no cambian: v1_grillas.py:v1_grillas_salida.txt. Vara: bytes de git show pre-s172-sombra-34 contra git show 30d9f9418, con CRLF normalizado: los primeros 3.805 bytes son idénticos (sha256 da755f3e...); la comparación por clave de las 11 también; control mutado (X0 de Chaitén) rompe el prefijo; 0 claves duplicadas (con un loader propio que las detecta, porque yaml.safe_load se queda con la última sin avisar); 45 claves igual a los 45 nombres de volcanoes.yaml; nrt.yml = las 11 con grilla vieja.
- V-1, las 34 siguen la regla de las 11: reimplementé la proyección con pyproj sin importar el generador del autor: epsg por longitud, X0 e Y0 a menos de 0,06 m del UTM del lat/lon del yaml, centro_lat y centro_lon = yaml a 5 decimales, roi def: 0 desviaciones en 34. Ninguna longitud queda en la zona equivocada (13 en 32718, 21 en 32719; Mocho-Choshuenco, -72,027, en 32718). Distancia mínima entre dos volcanes: 0,084 grados, así que volcan_por_coordenadas (tolerancia 1e-6) no confunde nombres. Límite: la regla es la de la mayoría; en 3 de los 11 MIROVA usa otro punto (VS34-05).
- V-2, producción y sombra de los 11: la rama no cambia ningún .py de pipeline/, ni run_pipeline, ni volcanoes.yaml, ni sombra-codigo-mirova.yml (git diff --stat: 15 archivos, sólo yaml de grillas, perfil nuevo, dos workflows nuevos, un script nuevo, tests y experimento). Perfiles resueltos desde pipeline.profile (v3_perfil.py): sombra_34 difiere de sombra_codigo_mirova sólo en DATA_SUBDIR y PROFILE_NAME, y de mirova_equivalent (producción) sólo en esas dos más los tres ENABLE_*_CODIGO_MIROVA; 153 constantes comparadas; el control (producción contra sombra de los 11) da exactamente esas diferencias. Los consumidores de la grilla (process_modis.py:640, process_viirs.py:769, process_viirs_mod.py:506) sólo actúan con los flags de la vía encendidos, que en producción están en False. El store no aplica a records de la vía el filtro por distancia, la geocerca ni el tope de píxeles (pipeline/store.py:357 a 363, 401, 455), así que el radius_km de 5 km de los 34 no recorta los records de la vía.
- V-3, perfil y workflow: `extends` de un solo nivel correcto (pipeline/profile.py:51 a 67); `"on":` entre comillas; cron 7 13 fuera de las 01 a 12 UTC; un solo secreto (EARTHDATA_TOKEN) con falla inmediata antes del pipeline; grupo sombra-34 con cancel-in-progress false; push con 5 reintentos pull --rebase; git add sólo de data/sombra_34/<volcán>.json; la aserción de perfil del paso corre y falla con el perfil equivocado; matriz de 34 igual a volcanoes.yaml menos nrt.yml (test y lectura); el diff contra sombra-codigo-mirova.yml es sólo nombres, matriz, cron, paralelismo y comentarios. El productor escribe regimen.perfil (pipeline/store.py:93, 94 y 549) y la vía escribe via_codigo_mirova True (mirova_v750_codigo.py:704), que es lo que la vigilancia lee.
- V-5, pruebas: 52 de 52 verdes en una copia (v5_base_verde_salida.txt: 52 passed in 31,29 s). 194 pruebas pasan sobre cinco archivos de las vías, las dos pruebas viejas ajustadas y dos guardas (v5_viejas_y_guardas_salida.txt: 194 passed in 90,79 s). Mutaciones: ver VS34-02 y VS34-06.
- Orden de merge: el único archivo de la rama que el lector sellado marca es la grilla (VS34-08).

## 6. SIN DATO

- Que la vía corra en un gránulo real de un volcán nuevo, y cuántas pasadas MODIS tienen MxD03 en los 34 (el autor tampoco).
- Cuánto calor del vecino entra con textura real: mi gránulo sintético es limpio (ruido 0,3 K) y el efecto de la interpolación (V750-C) no está modelado; las frecuencias de VS34-01 vienen del detector K, no de la vía.
- Si MIROVA enmascara vecinos en sus grillas chilenas (su código dice que se puede).
- Duración real por job, carga sobre LAADS con 34 jobs más por día, tope de jobs simultáneos de la cuenta.
- Si el 1 GB de Pages se mide comprimido o sin comprimir (VS34-03).

## 7. FUERA DE ALCANCE

El relector (claude/s172-v375e-relector), el plan de decisión (compuerta de paridad con MIROVA), nrt.yml, la suite completa, cualquier despacho de workflow o commit.
