# CM162: los cúmulos se arman en la matriz del barrido, no en el terreno (mecanismo y tamaño)

- Hora del servidor: inicio Sat, 24 Oct 2026 14:03:15 GMT; cierre de mediciones 14:25:54 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`, header Date).
- Commit medido: `origin/main` = `e850152b5a0a5a57a496e9f08f33d461ab43a050` (2026-10-24 12:46 UTC). El código se leyó con `git show origin/main:<ruta>` y se extrajo con `git archive origin/main pipeline volcanoes.yaml` a `src_main/` de esta carpeta, porque el árbol de trabajo (`loop/activo`) difiere de `origin/main` en 11 archivos de `pipeline/` (`git diff origin/main --stat -- pipeline/`), entre ellos `profile.py` y `mirova_equivalent.yaml`. Los flags se evaluaron desde `src_main` con `VRP_PROFILE=mirova_equivalent`.
- Records: control K del A/B de D25, idéntico a producción salvo MODIS apagado, en las tres ventanas (`d25/V1`, `V2a`, `V2b`, `_s157_ab_d25_k_control`, sha256 en `m00`); y `data/mirova_equivalent/<Volcán>.json` de `origin/main` para MODIS y para la historia entera (copias en `data_main/`). El record de Chillán V750 2026-10-14 06:18 es idéntico en `origin/main` y en K (verificado campo a campo, salida del inventario).
- Referencia de MIROVA: V1 contra la congelada del pre-registro (`ref_v1/`, sha256 del CSV consolidado en disco `b6a2c277…3286`, MANIFIESTO con LF `5ae612a6…`); V2 y la historia contra el snapshot de `origin/main` (`ref_main/`, consolidado `4057e2f0…05be`, OCR `fd7a7098…1888`, más `union_historica/consolidado_filas_perdidas.csv`). Protegida = lectura A de `scripts/clase_mirova.py` (fila `ALERTA_TERMICA` o `ALERTA_TERMICA_OCR` con geometría y 1 MW o más, mismo volcán y banda, a 120 s del minuto del record).
- Modelo y esfuerzo: Claude Fable 5.1 (claude-fable-5-1); el nivel de esfuerzo lo fija la sesión que me lanzó y no es visible desde adentro. Todas las cifras salen de los scripts de esta carpeta (`m00` a `m04`, cada uno con su `_salida.txt`).
- Qué NO miré: ningún gránulo L1B (los índices fila y columna de cada píxel no están en los records, así que el paso exacto de la matriz queda en SOSPECHA); el brazo D del A/B; los 34 volcanes fuera de Tier A; el código MATLAB de MIROVA (usé la nota de memoria y el catálogo, no lo releí); la nubosidad; MODIS en las ventanas K (no corre ahí).

## En una pantalla

1. El cúmulo que se publica es una componente conexa de la MATRIZ del gránulo (`clustering.py:96`, `ndi_label` con vecindad 3×3 sobre índices), y la matriz no es un mapa: lejos del nadir dos barridos consecutivos se solapan en el terreno y VIIRS borra filas a bordo, así que dos píxeles vecinos en el suelo pueden no ser vecinos en la matriz. Medido sobre los records: en VIIRS 375 el cúmulo publicado tiene un píxel alertado a menos de un paso de grilla (calibrado por cenit) que NO es su miembro en 4 de 98 pasadas multi-cúmulo bajo 10° de cenit y en 44 de 98 entre 50 y 60° (ventanas K); el paso de grilla medido a nadir es 0,371 km, y hay pares entre cúmulos a 0,18 a 0,29 km, que no caben en un mismo barrido.
2. Dónde duele: en VIIRS 750, que publica `pc.vrp_mw`. La selección `vent_anchored` elige por distancia del CENTROIDE al cráter (`clustering.py:149-153`) y el modo de un píxel publica el máximo del fragmento elegido (`single_pixel_mode.py:181-182`), así que puede publicar un pedazo del foco sin el píxel más caliente. Al volver a pegar los fragmentos a menos de un paso, cambian 8 de 338 publicaciones V750 de las ventanas K (2,4 %), todas hacia arriba, 7 de las 8 entre 30 y 60° de cenit; 4 de 82 protegidas cambian y 1 cruza 1 MW (Láscar 2026-05-05 06:06, 0,932 a 1,001, MIROVA 1,62). Control positivo: Chillán 2026-10-14 06:18 pasa de 1,173 a 1,890 (MIROVA 2,0). En la historia entera: 61 de 2.070 publicaciones V750 cambian, 11 cruzan 1 MW, 6 de 153 protegidas cambian.
3. VIIRS 375 queda inmune en el NÚMERO publicado: `f5_core` ancla en el píxel de mayor VRP a menos de `inner_km` del centroide y suma su entorno sin mirar la membresía, así que en 0 de 157 pasadas fragmentadas (K) y 0 de 875 (historia) cambia la cifra. Lo que sí cambia en V375 es cosmético pero persistido: `n_pixels`, centroide y `n_hotspots_clustered` (cuenta fragmentos como hotspots). MODIS: 3 fragmentadas de 570 publicadas y 1 cambio, con poca potencia sobre 45° (11 cúmulos de 2+ píxeles).
4. La misma vecindad de matriz también cuenta DOBLE: cuando los dos barridos que vieron el mismo terreno quedan 8-conexos, el cúmulo suma dos veces la misma huella. Láscar V750 a 22 a 24,5° de cenit lo hace de forma recurrente (13 de 16 casos de la historia; 2025-07-07 05:24 trae dos píxeles a 0,18 km con 1,553 y 1,553 MW); el modo de un píxel lo esconde salvo cuando suma (Chillán V750 2026-10-01 06:00: 4,2 de los 11,1 MW publicados son un duplicado; MIROVA 10,0). Es el F5-09 de AUDIT_S155 con mecanismo.
5. No está en el catálogo con otro nombre: D17 y D28 piden el remuestreo y el bow tie de MODIS, D32 la suma de todos los alertados, y AUDIT_S155 (F5-01, F5-09, V5-02) describió los síntomas en Chillán; ninguno dice que el agrupamiento mismo es por índice de matriz. La dirección del desplazamiento no distingue el mecanismo (prueba de orientación sin señal), el paso exacto (filas borradas, solape sin borrar o paralaje del DEM) exige el L1B, y la decisión de arreglo pasa por un A/B que mida publicaciones y protegidas por tramo de cenit, con negativos limpios (PCC 2026-06-11 06:18 cruzaría 1 MW donde MIROVA vio nada) y con deduplicación de huellas.

## Fenómeno, mecanismo, números

**El fenómeno.** Un radiómetro de barrido mira el suelo línea a línea mientras el satélite avanza. Al nadir las líneas de dos barridos sucesivos se tocan; hacia el borde del barrido cada línea se ensancha y los barridos se montan unos sobre otros (bow tie). VIIRS lo resuelve a bordo: agrega muestras a lo largo del barrido en tres zonas (cambia de 3×1 a 2×1 a 31,59° de ángulo de barrido y a 1×1 a 44,68°) y borra detectores en las zonas externas (4 de 32 en la zona media y 8 de 32 en el borde para la banda I; ATBD Imagery RevE p. 21 y 23, citado verbatim en `docs/s128/PAPERS_A5_GEOMETRIA.md` l. 63-79). El L1B conserva las filas borradas como relleno `65533 = Bowtie_Deleted` (`documentacion/VIIRS_L1B_UserGuide_Aug2021.md` l. 704-730 y 2026). Resultado: en la matriz del gránulo hay filas vacías entre barridos, y los píxeles que sobreviven a cada lado del hueco pueden estar sobre el mismo terreno o a medio píxel uno de otro.

**El mecanismo en el código.** `cluster_hotspots` (`src_main/pipeline/clustering.py:31-163`, igual en `origin/main`) etiqueta componentes conexas de `hot_mask_2d` con `scipy.ndimage.label` y una estructura 3×3 de unos (l. 87-96): la vecindad es de índices fila y columna; las coordenadas `lat`/`lon` sólo entran después, para el centroide y su distancia al cráter (l. 102-104). Las filas `Bowtie_Deleted` llegan como NaN (`process_viirs.py:83` y `391-392`), nunca son alertadas, y cortan la conectividad. Luego `vent_anchored` ordena por (dentro del inner, distancia del centroide, menos VRP) (l. 149-153), y `apply_single_pixel_mode` publica el máximo del fragmento elegido cuando pesa menos de 5 MW y tiene 3 píxeles o menos (`single_pixel_mode.py:161-183`; flags `ENABLE_SINGLE_PIXEL_SUB_MW_MODE=True`, 5,0 MW, 3 píxeles, evaluados desde `origin/main`). En V375 el tablero publica `f5_core_vrp_mw` (`f5_core.py:61-104`), que ancla en el píxel de mayor VRP a menos de `inner_km` del centroide y suma lo que queda a 0,75 km o sobre 295 K: no mira la membresía, por eso es inmune. Existe `cluster_pixels_geographic` (`clustering.py:166-247`, unión por haversine) y no tiene ningún llamador en `pipeline/` (sólo los `import` de `process_viirs.py:53`, `process_viirs_mod.py:47`, `process_modis.py:54`). `ENABLE_UTM_REGRID = False`: el remuestreo que haría MIROVA antes de agrupar (nota `reference_codigo_mirova_osf.md`: opera sobre `ZI_M13` remuestreado) no corre (D17).

**Cómo se midió sin L1B.** La membresía del cúmulo no se persiste; se infiere como el subconjunto de `anomaly_pixels` cuya media de lat/lon reproduce el centroide (misma técnica del verificador), y se valida reproduciendo `pc.vrp_mw`: 0 fallas en los 11.661 records con membresía (`m01_salida.txt`, no hay fila `ctrl_FALLA`; MODIS se valida como subconjunto por la magnitud focal). El paso de grilla se calibra desde los propios datos: distancia mínima entre miembros 8-conexos por sensor y tramo de 5° de cenit (`m03_salida.txt`, tabla de calibración): V375 da 0,371 km en el percentil 10 a 0 a 5° (el tamaño nominal de la banda I) y sube a 0,53 km en el percentil 25 a 45 a 50°; V750 da 0,742 km a 0 a 5°. Un par de píxeles alertados a menos de 0,9 × percentil 25 del tramo no puede ser de un mismo barrido. Con ese umbral se mide (a) «fragmentado»: el cúmulo publicado tiene un alertado a menos de un paso que no es miembro; (b) el contrafactual de pegarle esos fragmentos (iterativo) y recalcular con la MISMA regla de magnitud (modo de un píxel, y f5 en V375); (c) «doble»: dos miembros a menos de 0,5 × mediana del tramo.

**Los números (ventanas K, control = producción; `m03_salida.txt`).** Tramos de cenit 0-10 / 10-20 / 20-30 / 30-40 / 40-50 / 50-60 / 60-70:

| | V375 publicadas > 0 | V375 multi-cúmulo | V375 fragmentadas | V375 con el pico fuera del cúmulo | V750 publicadas > 0 | V750 fragmentadas | V750 cambia la publicación |
|---|---|---|---|---|---|---|---|
| 0-10 | 225 | 98 | 4 | 1 | 51 | 0 | 0 |
| 10-20 | 240 | 97 | 4 | 1 | 64 | 0 | 0 |
| 20-30 | 256 | 104 | 17 | 8 | 48 | 0 | 0 |
| 30-40 | 260 | 107 | 24 | 12 | 52 | 1 | 1 |
| 40-50 | 309 | 113 | 36 | 12 | 60 | 6 | 3 |
| 50-60 | 302 | 98 | 44 | 17 | 47 | 6 | 4 |
| 60-70 | 180 | 54 | 28 | 14 | 16 | 0 | 0 |
| total | 1.773 | 671 | 157 | 65 | 338 | 13 | 8 |

V375: 0 cambios en la cifra publicada (f5) en las 157. V750: los 8 cambios suben (0,113 a 0,132; 0,329 a 0,347; 1,173 a 1,890; 0,753 a 0,941; 0,572 a 0,676; 0,932 a 1,001; 0,484 a 0,570; 0,447 a 1,755). Protegidas V750 (26 + 41 + 15 = 82): cambian 4 (Chillán 2026-09-29 06:36 y 2026-10-14 06:18, Láscar 2026-04-23 06:12 y 2026-05-05 06:06), cruza 1 MW una (Láscar 05-05). Sin protección pero con cruce: PCC 2026-06-11 06:18, 0,447 a 1,755 con MIROVA en 0,0 esa pasada. Historia entera de `origin/main` (detectores mezclados, `m03_salida.txt`, bloque `main`): V750 147 fragmentadas de 2.070 publicadas, 61 cambian (todas suben), 11 cruzan 1 MW, 6 de 153 protegidas cambian y 1 cruza; 30 de los 61 cambios son de Láscar y 14 de Chillán. V375: 875 fragmentadas de 8.994, 357 con el pico fuera, 0 cambios de cifra. MODIS: 3 fragmentadas de 570, 1 cambio, 0 protegidas tocadas.

## Hallazgos

### CM162-01: en VIIRS 750 se publica un fragmento del foco armado por índice de matriz; en pasadas oblicuas puede dejar fuera al píxel más caliente

- ARCHIVO:LÍNEA: `pipeline/clustering.py:87-96` (vecindad 3×3 sobre índices), `:149-153` (orden por distancia del centroide), `pipeline/process_viirs_mod.py:1098-1130` (llamada y modo de un píxel), `pipeline/single_pixel_mode.py:181-182`. SCRIPT:SALIDA: `m03_umbral_por_cenit.py` → `m03_salida.txt` y `m03_fragmentados.csv`.
- QUÉ PASA: cerca del borde del barrido, el foco del cráter se ve en dos barridos que se montan; las filas borradas a bordo (o el solape) dejan esos píxeles a 2 o más filas de distancia en la matriz y el etiquetado los parte en dos cúmulos. El que gana es el de centroide más cercano al cráter, no el más caliente, y con 3 píxeles o menos se publica el máximo de ese fragmento. Tamaño: 8 de 338 publicaciones V750 de las ventanas K (2,4 %; 7 entre 30 y 60°), 4 de 82 protegidas, 1 cruce de 1 MW; en la historia 61 de 2.070 y 11 cruces.
- CÓMO SE VE EN EL DASHBOARD: una magnitud V750 más baja que la del píxel que está al lado; en Chillán 2026-10-14 06:18 el operador ve 1,17 MW (Muy Bajo) con un píxel de 1,89 MW (Bajo) a 0,67 km, y MIROVA publicó 2,0. Siempre a la baja: el defecto nunca sube una publicación.
- CÓMO REPRODUCIRLO: `cd <CARPETA> && python m03_umbral_por_cenit.py`; la línea `CONTROL POSITIVO` imprime Chillán V750 NOAA-21 2026-10-14 06:18 UTC con `pub 1.173 -> nuevo 1.89`.
- CONFIANZA: CONFIRMADO el hecho (geometría de los records más el código); el paso exacto de la matriz, SOSPECHA (CM162-04).
- GRAVEDAD: 3. Tuerce el nivel (Muy Bajo contra Bajo) en V750 de pasadas oblicuas y decide el cruce de 1 MW en 1 protegida de 82; en la historia, 11 cruces.

### CM162-02: en VIIRS 375 el mismo defecto existe y crece con el cenit, pero el número publicado no lo ve; lo que queda torcido es la posición, el tamaño y el conteo de hotspots

- SCRIPT:SALIDA: `m03_salida.txt` (bloques `K_*`/`V375`: `fragmentado` 54 + 49 + 54, `pico_fuera` 19 + 29 + 17, `cambia` 0) y `m01_salida.txt` (`cf_cambia` 0 en V1 y V2a, `cf15_cambia` 1 en V2b).
- QUÉ PASA: la banda I se fragmenta más que la M (157 de 671 multi-cúmulo en K; de 4 de 98 bajo 10° a 44 de 98 entre 50 y 60°), y en 65 el píxel más caliente del entorno queda fuera del cúmulo. Como `f5_core` ancla en el pico a menos de `inner_km` del centroide sin mirar la membresía (`f5_core.py:83-104`), la cifra publicada no cambia en ninguna. Sí quedan torcidos y persistidos `primary_cluster.n_pixels`, el centroide (y de ahí `centroid_dist_km` y `geo_class`) y `n_hotspots_clustered`, que cuenta fragmentos de un mismo foco como hotspots distintos.
- CÓMO SE VE EN EL DASHBOARD: invisible en la magnitud. Visible, si alguien lo mira, como «2 a 4 hotspots» donde hay uno.
- CÓMO REPRODUCIRLO: `python m03_umbral_por_cenit.py`; el bloque «V375 fragmentadas con cambio de publicacion (f5)» sale vacío. Caso: Chillán V375 2026-10-15 05:00 UTC (cenit 62,4°, dos píxeles a 0,026 km en cúmulos distintos, `m01c_salida.txt` del verificador).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. No cambia una alerta hoy; cualquier métrica que use `n_hotspots_clustered`, el centroide o `n_pixels` de V375 en pasadas oblicuas hereda el defecto.

### CM162-03: la vecindad de matriz también suma dos veces la misma huella cuando los dos barridos quedan 8-conexos

- SCRIPT:SALIDA: `m04_dobles.py` → `m04_salida.txt`.
- QUÉ PASA: cuando el solape entre barridos NO deja filas de por medio, el mismo trozo de suelo entra dos veces al cúmulo. Pares de miembros a menos de medio paso: V750 16 de 484 cúmulos de 2+ píxeles en la historia, 13 de ellos Láscar a 22 a 24,5° de cenit (2025-07-07 05:24: dos píxeles a 0,18 km con 1,553 y 1,553 MW); V375 21 de 2.669. El modo de un píxel lo esconde (publica el máximo), pero cuando el cúmulo suma, la publicación lleva el duplicado: Chillán V750 2026-10-01 06:00, 11,084 MW publicados con un duplicado de 4,175 (MIROVA 10,0); V375 14 de los 21 en modo suma (Chillán 2026-10-16 06:42, 0,614 de 6,591). La suma de escena `vrp_mw` lo lleva siempre.
- CÓMO SE VE EN EL DASHBOARD: magnitud inflada en régimen de suma (sobre 5 MW o más de 3 píxeles) en el borde del barrido; AUDIT_S155 F5-09 lo había visto en Chillán V375 sobre 50° sin mecanismo.
- CÓMO REPRODUCIRLO: `python m04_dobles.py`; Láscar V750 2025-07-07 05:24 UTC y Chillán V750 2026-10-01 06:00 UTC.
- CONFIANZA: CONFIRMADO el par de píxeles a menos de medio paso con la misma energía; que sea el mismo terreno, SOSPECHA fuerte (sin L1B).
- GRAVEDAD: 2.

### CM162-04: el paso exacto de la matriz (filas borradas, solape sin borrar o paralaje del DEM) no se puede fijar desde los records

- SCRIPT:SALIDA: `m01_salida.txt` (`cerca_ang>=60` 14 de 44, 15 de 39, 13 de 51 contra `intra_ang>=60` 65 de 156, 75 de 151, 97 de 175) y `m01b_salida.txt`.
- QUÉ PASA: la prueba de orientación (desplazamiento del par respecto del azimut del sensor persistido en el record) no separa los pares entre cúmulos de los pares dentro del cúmulo: la fracción perpendicular al barrido es parecida en ambos. Y hay pares a menos del paso de nadir con cenit bajo: Lascar 2026-10-02 05:36 (23,8°, 0,290 km), PCC 2026-08-31 05:42 (15,5°, 0,180 km), PCC 2026-10-10 05:54 (23,6°, 0,220 km), más pares DENTRO del cúmulo a 0,19 a 0,26 km a 11 a 15° (Chillán 2026-10-01 06:00, PP 2026-10-05 05:48). Un paso de 0,371 km a nadir no admite dos píxeles distintos a 0,18 km en un mismo barrido, así que son de barridos distintos o la geolocalización corregida por el DEM comprime el espaciado en la ladera que mira al sensor. Cuál de los dos, y cuántas filas median, exige los índices del gránulo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python m01b_casos_bajos.py`.
- CONFIANZA: SOSPECHA (el mecanismo fino); CONFIRMADO que no es un mismo barrido.
- GRAVEDAD: 1 para la decisión (el tamaño ya está medido sin esto); 3 para el diseño del arreglo, porque el remuestreo (D17) y la deduplicación por huella (V5-02) responden a mecanismos distintos.

### CM162-05: el instrumento de calibración tiene dos tramos débiles

- SCRIPT:SALIDA: `m03_salida.txt`, tabla de calibración.
- QUÉ PASA: V750 15 a 20° calibra con n = 10 y percentil 25 de 0,316 km (duplicados en la muestra): el umbral de ese tramo (0,285) es demasiado bajo y subcuenta fragmentados ahí (ventanas K: 0 fragmentadas en 10 a 20°, puede ser real o ser esto). MODIS sobre 45° hereda el tramo 40 a 45° (n = 9), y sólo hay 11 cúmulos MODIS de 2+ píxeles sobre 45°: el «3 fragmentadas de 570» de MODIS es poca potencia, no ausencia.
- CÓMO SE VE EN EL DASHBOARD: no aplica.
- CONFIANZA: CONFIRMADO (es una propiedad de mi medición).
- GRAVEDAD: 1.

### CM162-06: `cluster_pixels_geographic` es código muerto y `n_hotspots_clustered` cuenta fragmentos

- ARCHIVO:LÍNEA: `pipeline/clustering.py:166-247`; `grep -rn "cluster_pixels_geographic(" pipeline/` sobre `src_main` da 0 llamadas fuera de la definición. `n_hotspots_clustered = len(_clusters)` en `process_viirs.py:1561`, `process_viirs_mod.py:1104`, `process_modis.py:1173`.
- QUÉ PASA: la alternativa geográfica existe desde S27 para post-procesar JSON y nunca se cableó; y el campo que el proyecto equipara con el `n_hotspots` de MIROVA (D1) cuenta componentes de matriz, que en pasadas oblicuas son fragmentos de un mismo foco (CM162-02).
- CÓMO SE VE EN EL DASHBOARD: invisible (el tablero no muestra `n_hotspots_clustered`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## Qué pregunta tendría que contestar un A/B

No propongo el arreglo como hecho. Hay tres formas de armar cúmulos «en el terreno» y responden a mecanismos distintos: (1) remuestrear a la grilla UTM antes de detectar (D17, flag `enable_utm_regrid`, es lo que hace MIROVA y además deduplica); (2) agrupar por distancia geográfica (`cluster_pixels_geographic`, que no deduplica: CM162-03 empeoraría si suma); (3) deduplicar por huella y luego agrupar. La pregunta del A/B, por sensor y por tramo de cenit de 10°, con el control = producción: cuántas publicaciones V750 y MODIS cambian y hacia dónde; cuántas protegidas (lectura A) cambian de lado de 1 MW en cada sentido; cuántos negativos limpios cruzan 1 MW (PCC 2026-06-11 06:18 es el caso que avisa del costo); y en V375 que la cifra f5 no se mueva (es el nulo que ya está medido: 0 de 1.032). Como brazo aparte, la suma de todos los alertados (D32), porque las protegidas que suben con el fragmento pegado siguen debajo de MIROVA (Chillán 09-29: 0,347 contra 2,03).

## SEGUIMIENTOS

1. Sonda L1B de lectura, sin tocar el pipeline: para `VJ102MOD.A2026287.0618` (Chillán V750 2026-10-14 06:18) y para los tres casos de cenit bajo de CM162-04, imprimir fila, columna, scan y las filas `Bowtie_Deleted` entre los píxeles alertados. Cierra CM162-04 y decide entre remuestreo y deduplicación.
2. Repetir `m03` con la referencia congelada de V2 cuando exista (acá V2 se pareó contra el snapshot vivo).
3. Si se registra en el catálogo, enlazarlo a D17, D28 y D32 y a AUDIT_S155 F5-01, F5-09 y V5-02, y marcar en D1 que `n_hotspots_clustered` cuenta fragmentos.
4. Mirar MODIS sobre 45° con más datos antes de decir que está limpio.

## VERIFICADO LIMPIO

- Inferencia de membresía: reproduce `pc.vrp_mw` en 643/643 (V1 V375), 154/154 (V1 V750), 548 y 144 (V2a), 629 y 167 (V2b), 9.268 y 2.659 (historia); MODIS como subconjunto, 0 fallas. Vara: `grep -c FALLA m01_salida.txt` da 0.
- Ancla de la selección: `vent_lat/vent_lon` de `volcanoes.yaml` reproduce `primary_cluster.centroid_dist_km` en todos los records (0 `ancla_FALLA`). Vara: la misma.
- `f5_core_vrp_mw` no depende de la membresía del cúmulo: 0 cambios en 1.032 pasadas V375 fragmentadas. Vara: bloque «V375 fragmentadas con cambio de publicacion (f5)» vacío en `m03_salida.txt`.
- El record de Chillán V750 2026-10-14 06:18 de `origin/main` es igual al del control K (pc, píxeles, cenit 51,48, azimut -84,61). Vara: salida del inventario de esta sesión (bloque `K:`/`main:`).
- Flags leídos desde `origin/main` (no del árbol de trabajo): `ENABLE_UTM_REGRID False`, `ENABLE_VENT_ANCHORED_CLUSTERING True`, `ENABLE_SINGLE_PIXEL_SUB_MW_MODE True` (5,0 MW, 3 px), `ENABLE_FOCAL_CLUSTER_MAGNITUDE True` con `keep_peak` (MODIS), `ENABLE_LOCAL_CLUSTER_MAGNITUDE* False`, `ENABLE_TEST1_PATH False`. Vara: `cd src_main && VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_UTM_REGRID)"`.
- `Bowtie_Deleted` (65533) se enmascara a NaN en los dos caminos de lectura de VIIRS I. Vara: `git show origin/main:pipeline/process_viirs.py | sed -n '83p;391,392p;409,410p'`.
- Paso de grilla medido a nadir: V375 0,371 km (p10 a 0 a 5°, n = 258), V750 0,742 km (n = 51), MODIS 0,976 km (n = 26), coherentes con el tamaño nominal: la geolocalización persistida es sana a esa escala. Vara: tabla de `m03_salida.txt`.
- Referencias: hashes en el encabezado; la congelada de V1 coincide con su MANIFIESTO con fin de línea LF (verificado por el verificador de la vuelta 1, no repetido acá).

## SIN DATO

- Índices fila y columna, número de barrido y filas borradas entre los píxeles de cada par: no están en los records; sin el L1B no se decide entre filas borradas, solape sin borrar y paralaje del DEM.
- Records con cúmulo pero sin `anomaly_pixels` o con cúmulo mayor que los píxeles guardados: V375 35 + 29 + 36 (K) y 460 (historia); V750 9 + 8 + 10 y 71; MODIS 13. Quedan fuera de todos los conteos.
- MODIS sobre 45° (11 cúmulos de 2+ píxeles en toda la historia).
- Si los pares a menos de medio paso son el mismo terreno (CM162-03) o dos huellas distintas comprimidas por la ladera.
- Protegidas de V2 contra la referencia que el A/B congeló para V2 (no estaba en disco; se usó el snapshot vivo).
- El brazo D del A/B (no se midió; el verificador de la vuelta 1 ya mostró que el cruce P1b de V750 depende de CM162-01).
