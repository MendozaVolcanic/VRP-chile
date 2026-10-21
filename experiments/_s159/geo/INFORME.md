# S159, frente GEO: la geometría de MIROVA (partes R, G y S)

2026-10-21. Ola 1 del plan `docs/superpowers/specs/2026-10-21-pruebas-post-auditoria-s158-design.md` (filas G, R y
S del §3). Sólo lectura: no se tocó `pipeline/`, `data/` ni `frontend/`, ni se hizo git. Todo lo de abajo sale de
scripts de esta carpeta (`C:\vrp-trabajo\s159-pruebas\experiments\_s159\geo\`) corridos en esta sesión, con su
salida al lado (`*_salida.txt`). Los TIF se bajaron sueltos por la API de GitHub a `descargas\` (683 archivos,
unos 30 MB), sin clonar `mirova-tif-archive`.

## En una pantalla

1. **La grilla de 750 m de MIROVA no es la de 375 m agrupada de a 2 × 2.** Hay TIF de VIIRS 750 (52 en mi muestra) y de
   MODIS (49) en UTM nativo en la misma ventana del 14 y 15 de septiembre que los de VIIRS 375, cosa que D17 y A106 dan por
   inexistente. En los 11 volcanes la esquina de la grilla de 750 m está **187,5 m al oeste y 187,5 m al sur** de la
   esquina de la de 375 m. La prueba con gránulos de la segunda ronda usó la esquina de 375 m para la grilla de 750 m,
   y ninguna de sus variantes (±375 m en un solo eje) es la grilla real.
2. **Una sola regla arma las tres grillas.** Centros de celda en `X0 - 25000 : paso : X0 + 25000` (y de sur a
   norte), con `(X0, Y0)` el UTM del punto de referencia de MIROVA para el volcán. Con paso 375 da 134 celdas, con
   750 da 67 y con 1000 da 51, y explica el desfase de 62,5 m que S158 no pudo explicar. Se cumple a 1 m en las tres
   grillas de los 11 volcanes. En 8 volcanes `X0` es el `lat`/`lon` del yaml. En Láscar, Planchón-Peteroa y
   Tupungatito es otro punto, de coordenadas redondas (a 233, 1.885 y 2.787 m del yaml).
3. **El escalón de 50° del OSF no tiene que ver con las zonas de agregación del VIIRS.** Salta en el cenit 50,01°
   (barrido 42,69°), dos grados de barrido **antes** del paso de 2:1 a 1:1 (44,680°, cenit 52,6°). En ese límite no
   hay salto (35,5 % contra 35,7 %), y la razón no es constante (mediana 0,51, del 5 al 95 % entre 0,20 y 0,81). La
   sospecha queda refutada.
4. **El radio de cumbre de MIROVA por volcán está dibujado en sus láminas «Dist»** (leyendas «>N km / <N km»), y en
   los 11 coincide con `inner_radius_km` del yaml (3, 4, 5, 7, 20). Que ese radio sea la caja de detección es otra
   cosa: el `.m` usa por defecto una caja sensible de 7 × 7 celdas (±2,6 km). Las láminas «Latest» no dibujan
   ningún recuadro.
5. Queda escrito, sin despachar, el script de la ola 2 que ajusta desfase e interpolador contra un TIF
   (`g2_ajuste_grilla.py`). Su prueba sintética pasa 7 de 8 casos prerregistrados. El que falla está explicado
   abajo y no se maquilló.

## Hallazgos, de mayor a menor gravedad

### H1. La grilla de VIIRS 750 de MIROVA está corrida (−187,5 m, −187,5 m) respecto de la de VIIRS 375, y la prueba con gránulos de R2 no la usó

- **SCRIPT:SALIDA**: `g1_regla_de_origen.py --grillas` → `g1_grillas_salida.txt`; inventario `r1_inventario_tif.py`
  → `r1_inventario_tif.csv`, `r3_resumen_cajas_salida.txt`, `r1d_adquisiciones_utm_salida.txt`. Uso de la grilla en
  R2: `experiments/_s158_audit_r2/granulos/probe_granulos.py:57-58` (`xs = g["ul_x"] + CELDA * (...)` con `ul_x` de
  la grilla de 375 m y `CELDA = 750.0`, l. 40) y `analizar_variantes.py:60` (variantes `(0,0), (±375,0), (0,±375)`).
  Afirmación contraria: `docs/DISENO_D17_REMUESTREO_UTM.md:308` («VIIRS 750 y MODIS: no hay TIF UTM de esos
  sensores (A106)»).
- **QUÉ PASA**: MIROVA arma su imagen de VIIRS 750 sobre celdas de 750 m cuyos bordes no coinciden con los de su
  imagen de 375 m: cada celda de 750 m contiene una celda de 375 m entera y mitades de sus vecinas. En el código,
  la esquina superior izquierda del TIF de 750 m es la del TIF de 375 m menos 187,5 m en x y menos 187,5 m en y, y
  el centro de la grilla de 750 m queda 265 m al suroeste del de la de 375 m. Lo mismo en los 11 volcanes, al
  centímetro. La prueba con gránulos de R2 remuestreó con la esquina de 375 m (la hipótesis 2 × 2 del §4.1 de
  D17), así que sus dos lecturas «grilla e interpolador» (Láscar 2026-09-26 05:48, Chaitén 2026-10-06 05:30) se
  hicieron sobre una grilla que no es la de MIROVA, y sus variantes de media celda tampoco la incluyen (la real está
  corrida en los dos ejes a la vez y en un cuarto de celda de 750).
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy. `ENABLE_UTM_REGRID = False` en producción (leído en esta sesión con
  `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_UTM_REGRID)"`). Pesa en
  la ola 2 (N y la fase 0 de D17): si D17 se implementa con la grilla 2 × 2, las alertas débiles de cumbre que
  dependen de media celda (las dos de arriba) se medirían sobre la grilla equivocada.
- **CÓMO REPRODUCIRLO**: `python -I g1_regla_de_origen.py r1_inventario_tif.csv <volcanoes.yaml> --grillas`.
  Ejemplo crudo, Villarrica, EPSG 32719 (leído de `r1_inventario_tif.csv`): UL VIIRS 375 (222583,934; 5657578,152);
  UL VIIRS 750 (222396,434; 5657390,652); UL MODIS (222271,434; 5658015,652).
- **Instrumento**: (1) si la grilla de 750 fuera 2 × 2, el `dUL` saldría (0, 0); sale (−187,5, −187,5) en los 11
  volcanes, y el de MODIS (−312,5, +437,5) en los 11, que es lo que la regla de H2 da para 51 celdas de 1 km. (2) Si la lectura estuviera muerta no habría filas UTM, y hay 152, con md5 del
  archivo igual al del índice en 152 de 152. **Cruce por valores, no por encabezado** (`g3_cruce_375_750.py` →
  `g3_cruce_375_750_salida.txt`, `g3b_noche_salida.txt`): ajustando el TIF de 375 m sobre el de 750 m de la misma
  adquisición, el desfase extra que mejor reproduce los valores queda en ±130 m alrededor de cero (11 pares
  nocturnos, dx mediana +105 m con cuartiles −97 y +120; dy −75 m) y ningún par cae cerca de (+187,5, +187,5), que es
  lo que daría un encabezado mal puesto sobre datos 2 × 2. Es compatible con el encabezado, pero I4 contra M13 es un
  cruce entre bandas distintas y su dispersión no sirve de vara fina. El «control corrido» de ese script (correr el
  encabezado +187,5 m) sólo comprueba el cableado: por construcción devuelve el mismo ajuste trasladado.
- **CONFIANZA**: CONFIRMADO para el encabezado. SOSPECHA fuerte, no probada, que la grilla del TIF de VIIRS 750 es la
  misma grilla en que corre la detección (el TIF es de 67 × 67, como `ZI_M13` del `.m`).
- **GRAVEDAD**: 4. La implementación de D17 y la lectura de las alertas débiles de cumbre en VIIRS 750 se apoyan en
  la grilla, y la que se venía usando como hipótesis es la equivocada.

### H2. La regla del origen: `X0 - 25000 : paso : X0 + 25000`, con un punto de referencia que en 3 volcanes no es el del yaml

- **SCRIPT:SALIDA**: `g1_regla_de_origen.py` → `g1_regla_de_origen_salida.txt`; `r3_resumen_cajas_salida.txt`.
- **QUÉ PASA**: MIROVA parte de un punto por volcán y arma una grilla de 50 km de lado contando celdas desde 25 km al
  oeste y al sur de ese punto. Como 50 km no es múltiplo exacto de 375 ni de 750 m, la última celda no llega al
  borde y la grilla queda corrida hacia el suroeste: 62,5 m en la de 375 m, 250 m en la de 750 m y nada en la de
  1 km (MODIS, 51 celdas, centrada exacto en el punto). Eso explica el «sexto de celda» que S158 (§3.1 de D17)
  dejó sin explicar, y los tres tamaños de grilla (134, 67, 51) salen de la misma regla. Hipótesis formulada antes de
  mirar los residuos. Residuo contra el yaml: **1,0 m** (0 m este, −1 m norte) en Chaitén, Chillán, Copahue, Isluga,
  Lastarria, Llaima, Cordón Caulle y Villarrica, y lo mismo con la grilla de MODIS (centro a 1 m del yaml, columna
  `d_yaml_m` de `r3`). Las reglas alternativas dejan 89 m (grilla centrada en el punto) o 124 m (filas de norte a
  sur). En los otros tres el punto de MIROVA es de coordenadas redondas y no es el del yaml:

  | volcán | punto de MIROVA deducido | `lat`/`lon` del yaml | distancia | `mirova_center` del yaml al centro del TIF 375 |
  |---|---|---|---|---|
  | Láscar | (-23,37001; -67,73000) | (-23,369; -67,732) | 233 m | 46 m |
  | Planchón-Peteroa | (-35,22301; -70,56800) | (-35,24; -70,568) | 1.885 m | 83 m |
  | Tupungatito | (-33,42501; -69,79700) | (-33,4; -69,8) | 2.787 m | 294 m |

  Y `mirova_center` no es la grilla en ningún volcán: queda de 10 a 494 m del centro de cada TIF, según sensor
  (columna `d_mc_m` de `r3`).
- **CÓMO SE VE EN EL DASHBOARD**: invisible mientras no haya remuestreo. Con D17, cualquier grilla armada desde el
  `lat`/`lon` del yaml estaría corrida 0,2 a 2,8 km en esos tres volcanes, y desde `mirova_center` hasta medio km en
  todos.
- **CÓMO REPRODUCIRLO**: `python -I g1_regla_de_origen.py r1_inventario_tif.csv <volcanoes.yaml>`.
- **Error propio, declarado**: en el docstring de `g1` escribí, antes de medir, que la regla predecía para MODIS
  `UL_1000 - UL_375 = (-312,5; -312,5)`. La componente y estaba mal calculada: la regla da +437,5 m, y es lo que
  se mide. Lo dejé escrito como estaba y lo marco acá.
- **CONFIANZA**: CONFIRMADO (11 volcanes, tres sensores, 152 archivos). Que esos tres puntos redondos sean
  coordenadas GVP: SOSPECHA, no consulté GVP.
- **GRAVEDAD**: 3. Fija la grilla para D17 sin tener que guardar 33 esquinas medidas, y muestra que en tres volcanes
  el yaml no sirve de punto de partida.

### H3. El radio de cumbre de MIROVA está en sus láminas «Dist», igual al `inner_radius_km` del yaml; la caja de detección no está en ninguna parte

- **SCRIPT:SALIDA**: `r2_laminas_dist.py` → `r2_laminas_dist_salida.txt` (25 láminas, la carpeta más reciente de cada
  volcán en `MendozaVolcanic/Mirova-v1`), mosaico `r2_mosaico_leyendas.png` leído a ojo; láminas de Cordón Caulle
  2026-10-10 05:54 (VIIRS 750 y 375 «Latest», VIIRS 750 «Dist») en `descargas\laminas\`.
- **QUÉ PASA**: MIROVA separa sus anomalías por distancia con un umbral propio de cada volcán y lo escribe en la
  leyenda de la lámina «Dist»: Lastarria y Planchón-Peteroa 3 km, Copahue 4, Tupungatito 7, Cordón Caulle 20, y los
  otros seis 5. Los 11 son el `inner_radius_km` del yaml (leído en esta sesión), o sea que el yaml ya trae ese dato.
  En Cordón Caulle la lámina «Dist» de VIIRS 750 muestra un año de alertas rojas («<20km») a 7,5 a 8,5 km. Es
  donde está el foco de 2011: el `vent` del yaml cae 7,6 km al norte del centro de la grilla de MIROVA
  (`experiments/_s158_d17_diseno/grilla_tif_salida.txt`). Lo que no se ve en ningún lado es la caja de detección:
  el `.m` usa por defecto una caja sensible de 7 × 7 celdas (`BOX == 2` en la matriz de ejemplo, filas y columnas 30
  a 36, leído en esta sesión) y deja escrito que «ROI1 and ROI2 can be shifted, reshaped or resized» por volcán
  (`MIROVA_VIIRS750_hotspot_detection.m:120-125`). Una caja de 7 × 7 llega a 2,6 km del centro, no a 5 km ni a 20.
  Las láminas «Latest» no dibujan ningún recuadro.
- **CÓMO SE VE EN EL DASHBOARD**: en Cordón Caulle, si se adopta la caja por defecto del `.m`, las alertas de MIROVA
  a 7,8 km quedan con umbrales de escena y no salen (es lo que R2 vio en 10-10 y 10-16). Si se toma el radio de la
  lámina como caja, se publica con umbrales sensibles en un círculo de 20 km.
- **CÓMO REPRODUCIRLO**: `python -I r2_laminas_dist.py descargas/laminas_dist` y mirar la leyenda de cada PNG.
- **CONFIANZA**: CONFIRMADO que los radios de la leyenda coinciden con el yaml en los 11. SOSPECHA que la caja de
  detección de Cordón Caulle cubre el foco a 7,8 km (es lo que explicaría las alertas, pero ninguna fuente de
  MIROVA lo dice).
- **GRAVEDAD**: 3. Decide con qué umbrales se mira el foco activo de Cordón Caulle, y por analogía el de Tupungatito.

### H4. El escalón de 50° del OSF no es la zona de agregación de la banda M: está en el cenit 50,0 exacto y su razón no es constante

- **SCRIPT:SALIDA**: `s1_escalon_vs_zonas.py` → `s1_escalon_vs_zonas_salida.txt` y figura `s1_escalon_vs_zonas.png`;
  `s1b_cenit_maximo_salida.txt`. Límites de zona renderizados a imagen: VIIRS Geolocation ATBD 2014 (423-ATBD-002),
  p. impresa 27 (p. 49 del PDF), §3.3.1.1, `atbd_geo_p49.png`: paso de 3:1 a 2:1 en ±31,589° de barrido y de 2:1 a
  1:1 en ±44,680°, barrido máximo 56,063°. Altura nominal 828 ± 12 km, p. impresa 9 (p. 31 del PDF),
  `atbd_geo_p31.png`.
- **QUÉ PASA**: el sensor junta muestras de a tres cerca del nadir, de a dos más afuera y deja de juntar en el borde.
  Convertido a cenit sobre una Tierra esférica, el paso al borde cae en 52,6° (52,5 a 52,7 con la altura entre 816 y
  840 km). La conversión la contrasté con el propio OSF: el cenit máximo de MODIS es 65,5° (la fórmula da 65,5 con
  705 km y barrido de 55°) y el de VIIRS 69,99 (la fórmula da 69,6 a 69,9). El ATBD dice «aproximadamente 65°» para
  55° de barrido, donde la fórmula da 67,8: la frase del ATBD es aproximada y los datos del OSF están con la
  fórmula. Sobre los datos de VIIRS 750 del OSF (100.641 filas, 2012 a 2025, global):
  - el localizador de cambio pone el salto en cenit **50,01°** (barrido 42,69°), y en barrido 42,5 a 42,69° no
    cumple el 0 %, mientras que de 42,69 a 43,0° no cumple el 21,8 %;
  - en el límite real de zona no hay salto: 35,5 % (barrido 44,0 a 44,68°) contra 35,7 % (44,68 a 45,4°);
  - 1.574 de las 4.466 filas que están en la zona 2:1 con cenit sobre 50° no cumplen;
  - la razón VRP_OSF / VRP_fórmula de las 8.239 filas que no cumplen tiene mediana 0,508, del 5 al 95 % entre 0,197 y
    0,807, y sólo el 2,0 % está a menos de 1 % de 1/2 (2,1 % de 2/3, 0,9 % de 1/3). Sube despacio con el barrido
    (mediana 0,43 a 42-43° y 0,54 a 54-56,5°), sin salto en 44,68°;
  - no depende del lado del barrido (23,1 % y 25,0 % según el signo de `SatAzi`), y sí mucho del día: 16,3 % de noche
    y 61,9 % de día sobre 50°.
  Un salto limpio en un número redondo de cenit, y no en un límite del sensor, apunta a un umbral de software sobre
  `SatZen` en la cadena de MIROVA (SOSPECHA). F6 de S158 ya había medido que depende de Npix y de la extensión
  (`experiments/_s158_audit/f6/INFORME.md` H1). Esto agrega que la geometría del sensor no lo explica.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Pesa al comparar magnitudes de VIIRS 750 contra el OSF sobre 50°: ahí el
  OSF no es la fórmula del código en una de cada cuatro filas.
- **CÓMO REPRODUCIRLO**: `python -I s1_escalon_vs_zonas.py <VRP_GLOBAL_ARCHIVE_2025.csv> .`
- **Instrumento**: control positivo, un escalón sintético inyectado en barrido 44,680 sobre filas que cumplen, y el
  mismo localizador lo encuentra en 44,68 (cenit 52,61). Control negativo, MODIS 0 de 262.455 filas y VIIRS 375 0 de
  252.374 no cumplen, a todo cenit (VIIRS 375 tiene las mismas zonas de agregación y no muestra nada).
- **CONFIANZA**: CONFIRMADO que la sospecha de la zona de agregación cae. SOSPECHA el umbral de software.
- **GRAVEDAD**: 2.

### H5. La caja de escena es fija en el tiempo, pero los TIF geográficos son otra grilla y un archivo puede haber sido reescrito

- **SCRIPT:SALIDA**: `r3_resumen_cajas_salida.txt`, `r1c_estabilidad_salida.txt`, `r1b_ventana_utm_salida.txt`.
- **QUÉ PASA**: de mayo a septiembre, cada volcán y sensor tiene una sola geometría EPSG:4326 (la mayor diferencia de
  transformada entre archivos es 2e-7 grados, unos 2 cm) y una sola UTM en la ventana. Las cajas geográficas miden
  49,6 a 51,6 km de lado y su centro no es el de la grilla UTM (por ejemplo VIIRS 750 de Chaitén: 267 m del yaml en
  EPSG:4326 contra 354 m en UTM), así que no son la grilla UTM con otra etiqueta: sirven para ubicar, no para contar
  celdas (confirma A106). La ventana UTM por hora de adquisición: VIIRS 375 del 09-14 06:36 al 09-15 06:18, VIIRS
  750 del 09-14 06:36 al 09-15 06:00 y MODIS del 09-14 13:10 al 09-15 13:55 (`r1d`). Hay además 36 archivos UTM sin
  hora de adquisición en el índice. Y en 7 de los 683 archivos el md5 del que está hoy en la ruta no es el del
  índice: la ruta fue reescrita con una imagen posterior (los 7 son VIIRS 375 con nombre 2026-09-15 18:36 o 18:42, en EPSG:4326).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2 (para quien use el archivo de TIF como referencia).

### H6. El script de ajuste para la ola 2 y su prueba sintética

- **SCRIPT:SALIDA**: `g2_ajuste_grilla.py` (no despachado), `g2_prueba_ajuste.py` → `g2_prueba_ajuste_salida.txt`.
- **QUÉ HACE**: proyecta las muestras del gránulo al EPSG del TIF, arma una sola vez los tres interpoladores (vecino,
  lineal sobre Delaunay, cúbico Clough-Tocher), los evalúa en los centros de celda del TIF corridos en ±media celda,
  ajusta una recta entre modelo y TIF (para absorber NRT contra estándar) y mide el error relativo a la desviación
  del TIF, con refinamiento alrededor del mejor. Se niega con un TIF en EPSG:4326 y con un gránulo que no cubre.
- **Prueba** (criterio escrito antes de correr): identifica si el costo es 0,20 o menos y el segundo interpolador
  cuesta 1,5 veces o más; recupera el desfase a 15 m o menos. Resultados: lineal (+100, −60) → (+97,5, −60,0);
  cúbico (−150, +40) → (−150, +37,5); oblicuo con muestras de 790 × 760 m → (+97,5, −60,0); con calibración
  distinta y 1 % de ruido → (+97,5, −60,0); sin desfase → (0, 0); nulo (TIF de otro campo) → costo 0,999, margen
  1,00, **no identifica**, como debe. **Falla el caso vecino** (P2): reconoce bien el interpolador (margen 4,2) y el
  desfase a 2,5 m, pero el costo queda en 0,09, sobre el 0,02 prerregistrado, porque la malla fina de 7,5 m no pasa
  por el desfase real y con vecino más cercano un par de metros cambia muchas celdas. Agregué después un P2b con
  malla de 2,5 m, que pasa. Queda registrado así: P2 falla, P2b pasa, y para la ola 2 conviene la malla de 2,5 m (o
  menos) si el candidato es vecino más cercano.
- **Límites declarados**: el TIF sintético se armó con los mismos interpoladores de scipy que usa el ajuste, así que
  la prueba muestra que el ajuste encuentra lo que existe, no que scipy reproduzca a MATLAB. El `cubic` de MATLAB no
  es idéntico a Clough-Tocher, y `natural` y `v4` de MATLAB no están. El ensayo con datos reales (H1, I4 contra M13)
  dejó una dispersión de ±130 m, así que la vara de la ola 2 tiene que ser el gránulo de la misma banda.
- **CONFIANZA**: CONFIRMADO lo medido. **GRAVEDAD**: 2.

## Qué trae cada TIF

Radiancia espectral, en todos los indicios: valores de 0,02 a 0,46, positivos, float64 o float32 según el archivo.
La temperatura de brillo equivalente de la mediana de cada TIF, si fuera radiancia a 3,74 µm (I4) o 4,05 µm (M13),
da de noche 253 a 289 K (I4) y 247 a 273 K (M13), y en las pasadas de 17 a 20 UTC 241 a 311 K (I4) y 236 a 303 K
(M13): lo esperable para el suelo andino de noche, y con sol, o con nube, de tarde (27 pares,
`g3_cruce_375_750_salida.txt`). No es NTI (que sería negativo, entre −1 y 0) ni temperatura de
brillo (que estaría en los cientos). La banda (I04, M13, B21) sale de la columna `band` del índice del archivo, no de
los metadatos del TIF: SOSPECHA razonable.

## Para la ola 2

- Rehacer la prueba con gránulos de VIIRS 750 con la grilla real: `UL_750 = (X0 - 25375 ; Y0 + 24875)` en el UTM
  de MIROVA del volcán, o directo la esquina del TIF de 750 m en UTM (`r1_inventario_tif.csv`), en vez de la de 375 m.
  Primero en Láscar 2026-09-26 05:48 y Chaitén 2026-10-06 05:30.
- La fase 0 de D17 puede correr `g2_ajuste_grilla.py` sobre los TIF UTM de las tres bandas: en mi muestra hay 51 de VIIRS 375, 52
  de VIIRS 750 y 49 de MODIS en UTM (`r1d`; la muestra tomó todos los archivos de la ventana), no sólo los de VIIRS 375.
- Corregir en D17 §4.1 la frase de la l. 308 y la hipótesis 2 × 2 (eso lo decide el coordinador, A113).

## Lo que no pude medir

- El interpolador de MIROVA: requiere el gránulo L1B de la misma adquisición (ola 2, con `EARTHDATA_TOKEN`).
- Que la grilla del TIF de VIIRS 750 sea la grilla en que corre la detección (SOSPECHA fuerte, ver H1).
- La caja de detección por volcán (`BOX`) en Chile. Ni los TIF ni las láminas la traen.
- La causa del escalón de 50°: sólo que no es la zona de agregación.
- Si los tres puntos redondos de Láscar, Planchón-Peteroa y Tupungatito son GVP (no consulté GVP).
- Por qué algunos TIF son float32 y otros float64 (no lo miré).

## VERIFICADO LIMPIO

- **Las grillas UTM no cambian entre pasadas**: un solo origen por volcán y sensor en los 152 archivos UTM (columnas
  `nc` y `nf` = 1 en `g1_grillas_salida.txt`).
- **Las cajas geográficas no cambian de mayo a septiembre** (2e-7 grados como máximo, `r1c_estabilidad_salida.txt`).
- **Los 152 TIF UTM bajados son los del índice** (md5 152 de 152, `g1_regla_de_origen_salida.txt`).
- **`inner_radius_km` del yaml = radio de las láminas «Dist» de MIROVA en los 11 Tier A** (`r2_mosaico_leyendas.png`
  contra `volcanoes.yaml`); no hay que volver a buscarlo.
- **Todos los Tier A tienen `radius_km` 25** y la escena de MIROVA mide 50,25 km (375/750) o 51 km (MODIS) de lado:
  el radio del yaml corresponde a la mitad de la escena (`r3_resumen_cajas_salida.txt`).
- **La fórmula del VRP del OSF se cumple al 100 % en MODIS y VIIRS 375 a todo cenit, y en VIIRS 750 bajo 50°**
  (`s1_escalon_vs_zonas_salida.txt`), igual que en R2.
- **Las zonas de agregación del VIIRS** son 31,589° y 44,680° de barrido (ATBD renderizado): ya no hay que buscarlas.
- **Producción no remuestrea**: `ENABLE_UTM_REGRID = False` (comando en H1), así que nada de esto mueve hoy lo que
  ve el operador.
