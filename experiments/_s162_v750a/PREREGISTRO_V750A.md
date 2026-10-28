# Pre-registro V750-A (S162): el paquete del código de MIROVA contra K en VIIRS 750

Estado: **BORRADOR para el sello de Nicolás.** El sello espera la lectura de V750-B (la ROI elegida se incorpora antes
de sellar, §11) y depende también de V750-C (que el remuestreo es pieza
obligatoria). Nada se implementa en `pipeline/` ni se despacha antes del sello, del verificador limpio de este
documento, del tag defensivo y del sí de Nicolás (A45). Autor: sesión hija VIIRS 750 (`tasks/LOOP_VIIRS750.md`),
2026-10-24. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §3 (V750-A), §7 (fases 3 y 4)
y §9 (decisiones 2, 3, 5, 11 y 12).

## 1. Qué se propone y por qué, como geólogo

Hasta hoy la réplica reconstruyó MIROVA leyendo papers y la armó pieza a pieza sobre nuestro detector K. MIROVA
publicó el código de VIIRS 750, y tres mediciones dicen que sus piezas no se pueden trasplantar sueltas:

- El código entero, corrido en la grilla de MIROVA, da la magnitud de MIROVA al centésimo: razón 0,999 [0,978; 1,007]
  en 145 alertas (S159 N-2), contra 0,510 de K.
- El fondo del código sobre la detección de K enciende cumbres tibias que MIROVA calla (S159 N-1: +60 negativos), y
  V750-C (verificado) mostró por qué, con dos piezas: dentro de la caja sensible, MIROVA no las ve porque interpola
  el gránulo a su grilla fija con un promedio lineal que reparte el calor de un píxel aislado (el brazo nativo del run
  de V750-B dirá si es el remuestreo en sí o sólo el interpolador); fuera de la caja (Tupungatito), porque su ROI las
  mira con umbrales conservadores.
- En el censo de noches sin actividad, el código con la caja sensible publica 15 de 5.353 contra 54 de K, sin perder
  protegidas (ΔE −90, S159 censo).

O sea que para callar donde MIROVA calla y medir lo que mide hay que ver el volcán como lo ve MIROVA: interpolado a su
grilla, con su detector, su fondo y su suma. La propuesta es una **vía de proceso alternativa para VIIRS 750**, detrás
de un flag, que corre el código de MIROVA completo, y compararla con K.

## 2. Qué es «P», el paquete

P = para cada pasada nocturna de VIIRS 750 y cada volcán Tier A:

1. **Remuestreo** del gránulo (M13 y M15, radiancia) a la grilla de MIROVA: UTM del volcán, 67 × 67 celdas de 750 m,
   esquina de la regla GEO (centros `X0 ± 25.000 m`, paso 750; `experiments/_s159/geo/INFORME.md:16-20`), con
   interpolación lineal sobre los píxeles a menos de 45 km (como `probe_n.grillar`). La grilla por volcán (EPSG,
   esquina) se fija en configuración y se vigila con un test (A63: nadie la regenera sin revisar).
2. **Detección**: `MIROVA_VIIRS750_hotspot_detection.m` literal (port validado contra Octave, 791 de 791 escenas),
   con la BOX que elija V750-B.
3. **Magnitud**: `MIROVA_VIIRS750_VRP.m` literal (fondo `fillmissing2` lineal bajo halo de 3, 5 o 7 celdas, suma de
   todos los alertados, sin recorte, coeficiente 1,97e7 × 0,5625).
4. **Record**: mismo esquema que hoy (el tablero no cambia). `pc.vrp_mw` = el VRP del paso 3 (unión de los alertados,
   como publica MIROVA, D32); posición, `distance_class` y centroide = el cúmulo 8-conexo, en la grilla, del píxel
   alertado más radiante (corrige C-4 del censo). Sin modo de un píxel y sin tope D9 (N-5: el tope recorta una
   erupción real de Chillán).
5. **Publicación**: el predicado del tablero de hoy, sin cambios (decisión §9.5 del programa: mantener el filtro de
   cumbre y medir P-sinfiltro).

## 3. Brazos

| brazo | qué es | para qué |
|---|---|---|
| **K** | producción | control |
| **P** | el paquete de §2 con la ROI de V750-B | candidato |
| **P-def** | P con la caja por defecto del `.m` | control positivo de la ROI (tiene que perder protegidas de Cordón Caulle) |
| **P-sinfiltro** | P publicando todo lo que detecta, sin el predicado de distancia | decisión §9.5: ¿MIROVA filtra por distancia? |
| **Kgeo** | K con agrupación geográfica (`cluster_pixels_geographic`, sin llamador hoy) y huellas deduplicadas | diagnóstico de CM162; sólo decide V750-D si P no se adopta |
| **K×1,2** | K con su VRP multiplicado por 1,2 | placebo de ganancia (programa §2): la métrica M tiene que distinguir P de un K escalado |
| **O** | el oráculo (port de R2) sobre la misma grilla | identidad: P tiene que ser O |
| **P-cercano** | P con el record ubicado en el alertado más cercano al cráter | brazo de posición (§6 bis) |
| **P-pico** | P con el record ubicado en el alertado de mayor M13 | brazo de posición (§6 bis) |

**Brazos de posición (decisión de Nicolás del 2026-10-27, programa §7, rama `loop/activo` `72928820b`).** Sus palabras:
«Sí: no fijes la regla todavía; mídela como brazo (radiante, cercano y pico) en los A/B de cada sensor contra lo que
publica MIROVA». P, P-cercano y P-pico comparten **la misma detección y el mismo VRP** (la unión de los alertados del
`.m`); sólo cambia el punto desde donde se mide la distancia del record al cráter, y con ella la clase `summit` o `far`
que decide si el tablero publica. **P** (radiante) es lo que hace hoy la vía: el centroide del cúmulo 8-conexo del
alertado más radiante. Físicamente, la regla decide sólo en una escena: un píxel débil junto al cráter y una fuente más
radiante lejos (otro foco, borde de nube, incendio). Con radiante el record queda lejano y el tablero calla; con cercano
queda en la cumbre y el tablero publica la suma, que viene sobre todo de la fuente lejana; con pico manda el píxel más
radiante solo, sin promediar su cúmulo. Medido por S165 (`experiments/_s165_regla_posicion/INFORME.md`, en
`loop/activo`): en VIIRS 750 «cercano» cambia 1 a 2 de 5.640 pasadas, siempre publicando de más; la distancia de MIROVA
calza mejor con el píxel pico que con el centroide. La población de §4.2 suma las pasadas `far_ref` (MIROVA publicó una
fuente lejana: fila FALSO_POSITIVO de la tabla y ninguna ALERTA), que V750-B corre si Nicolás sella su adenda 2
(`experiments/_s162_v750b/adenda2/ADENDA2_V750B.md`); sin ellas, el §6 bis se lee igual y se declara que la vara de
las pasadas lejanas quedó SIN DATO.

## 4. Las tres pruebas, en orden (fases 3 y 4 del programa)

### 4.1 Equivalencia (PD3): la vía del pipeline reproduce al oráculo pasada por pasada

- Sin red, en local y en CI: sobre las 510 grillas de N, el ejemplo de Etna del OSF y los 10 recortes nativos de R2
  (más las ventanas nativas que guarde el run de V750-B), la función del pipeline da **la misma máscara** (índice por
  índice) y el mismo VRP (diferencia relativa ≤ 1e-9) que `mirova_v750_r2`. Lo mismo para el remuestreo contra
  `probe_n.grillar` sobre las ventanas nativas.
- En el runner (dentro del run de §4.2): P contra O en cada pasada, del gránulo al record. Tolerancia: máscara idéntica
  y VRP a 1e-6 MW en todas, salvo las pasadas cuyo VRP cae en la banda de triangulación (20 semillas de jitter 1e-6,
  como N), que se listan aparte. **Una sola pasada distinta fuera de la banda bloquea la adopción** hasta explicarla.
- Mutaciones con control (S156): seis mutaciones (K1 y mínimos de K, media de 8 vecinos sin el central, fondo sin
  halo, recorte a cero, fondo de anillo, remuestreo por vecino más cercano) tienen que hacer fallar la prueba **por
  aserción**; una mutación de control que sólo hace caer el programa tiene que salir como caída, no como atrapada.
  Escrita y probada antes de la implementación: `equivalencia_v750a.py` → `equivalencia_v750a_salida.txt` (línea base
  ROJA porque el módulo no existe; identidad del oráculo contra sí mismo en 1.020 casos de E1 y 10 recortes de E3; 6
  de 6 mutaciones atrapadas por aserción y la de control caída). El remuestreo de referencia reproduce, en los 10
  recortes, la grilla lineal que guardó el runner de R2: la regla GEO queda probada también sin red.

### 4.2 Censo retrospectivo (decide la adopción)

- Población: la de V750-B (VIIRS 750 nocturno, 2026-04-01 a 2026-11-02 12:59 UTC, sin el 13 ni el 17 a 20 de octubre,
  12-oct sólo con los gránulos rescatados). Ventanas T (tabla sola) y O (tabla más OCR, tabla sola al lado). Un run de
  sólo lectura con los siete brazos, despachado por la coordinadora desde un tag. Si el run de V750-B guardó las
  grillas GEO de todas las pasadas, P, P-def, P-sinfiltro y O se calculan **en local** sobre ellas y el run sólo hace
  falta para K, Kgeo y la identidad P = O desde el gránulo.
- Cobertura contra la referencia (§8.1) antes del veredicto; «no observado» fuera del denominador.

### 4.3 Sombra prospectiva (confirma; no decide sola)

- Desde el 2026-11-03 (sin Suomi NPP: otro régimen, programa §2 ventana P), P corre en el NRT en un perfil sombra con
  su propio `data_subdir` (nunca en `mirova_equivalent`), al menos 4 semanas. Se mide con las mismas métricas contra
  MIROVA. Si en 4 semanas hay 4 bloques noche-volcán o menos, P2 es SIN SUSTRATO y la sombra sólo puede vetar (P1).

## 5. Métricas (programa §2)

- **P1** protegidas perdidas (lectura A, regla SN, ±120 s): veto.
- **P1b** cruces de 1 MW en las dos direcciones.
- **P2** E = alertas bajo 1 MW sin publicar + negativos limpios publicados; P contra K por la prueba de signos por
  bloque noche-volcán (D-45, `regla_signos_p2` de `experiments/_s157_prereg_d25/evaluar_d25.py`, tag
  `s161-d25-lectura`).
- **M** magnitud: razón brazo/MIROVA en las alertas que publican los dos (el brazo y MIROVA; L4, ver §10b), con el
  comparador de ganancia pareja (que se arma sobre las alertas que publican K y el brazo)
  (D-28, D-30, D-32: `evaluar_d25.py` del mismo tag) y el placebo K×1,2: M sólo dice «P mide mejor» si separa a P de
  K **y** de K×1,2.
- Todo por tramo de 10° de cenit, por volcán y por canal. Curva de razón por cenit comparada contra la de MIROVA
  (más oblicua sobre menos oblicua de la misma noche: MIROVA 0,503, oráculo 0,517, K 0,239), no contra 1.
- **Diagnóstico de acoplamiento por la sigma de escena** (obligatorio, no decide; seguimiento cruzado de MODIS,
  verificador de la ablación del bow tie D28, `experiments/_s162_modis_bowtie/real/verificador/`, commit `f49e57dd7`,
  hallazgo S-1). Físicamente: el umbral contextual del código de MIROVA no es local al cráter. Usa la media y la
  desviación del contraste NTI y ETI de **toda** la grilla de 51 km (`mu + s · sd`, con piso), así que un cambio que
  sólo toca píxeles lejos del cráter (el borde de la escena, el bow tie, el remuestreo de una franja oblicua) mueve el
  umbral de la cumbre y puede encender o apagar una publicación del cráter sin que el cráter haya cambiado. En MODIS
  eso pasó con márgenes de NTI de 1e-6 a 8e-4. Para cada par de brazos que comparten la detección del `.m` pero
  difieren en la grilla o en el remuestreo (P, P-def, O; y en la vía del pipeline contra el oráculo), el analizador
  informa por pasada: (a) cuánto cambia `sd` del contraste NTI y ETI en el primer y el segundo pase entre los dos
  brazos; (b) el margen de la celda decisiva del cráter contra su umbral (`c / u` en NTI y en ETI); (c) las pasadas
  cuya publicación cambia entre brazos y cuyo margen cae dentro del cambio de umbral que produce (a). Esas pasadas se
  listan por nombre, se cuentan por volcán y por tramo de cenit, y cualquier cambio de publicación de una protegida que
  caiga en ese grupo se informa como «decidido por la escena, no por el cráter» al lado del veredicto. Lo mismo vale
  para la prueba de equivalencia de §4.1: una diferencia de máscara P contra O que sólo se explique por la sigma de
  escena se informa así, y bloquea igual (la vía tiene que reproducir también la escena).

## 6 bis. Regla de posición (escrita antes de ver los datos; se aplica antes del §6)

Los tres brazos de posición se comparan contra lo que publica MIROVA. La vara es la de §5 más las pasadas lejanas:

- **E_lejana**: pasadas `far_ref` en que el brazo publica (MIROVA vio el calor y lo ubicó lejos del cráter; publicarlo
  como cumbre es publicar de más). Entra a la prueba de signos sumada a E, en el mismo bloque noche-volcán: **P2'** es
  la prueba de signos de D-45 sobre E + E_lejana.
- **Elegible**: P1 = 0 en T y en O, con la tabla sola y con tabla más OCR (la misma condición de P1 del §6.2).
- **Gana**: un elegible distinto de P (radiante) que en P2' contra P, sobre T ∪ O con el canal que decide, da GANA, y
  que con la tabla sola no es peor que P (GANA o EMPATE, o SIN SUSTRATO con el neto en 0 o a favor). Si ganan los dos,
  el de menor E + E_lejana; a igual valor, P-pico (la distancia de MIROVA calza mejor con el pico, S165).
- **Si ninguno gana**: P (radiante), si es elegible. Razón: es lo que hace hoy la vía y lo que midió el censo, y a igual
  desempeño no se cambia sin evidencia.
- **Si P no es elegible**: el elegible que no es peor que P en P2' ni con el canal que decide ni con la tabla sola; si
  son los dos, el de menor E + E_lejana y a igual valor P-pico. Si ninguno: NINGUNA POSICIÓN ELEGIBLE, y P no se adopta.
- El §6 se evalúa después sobre P con la posición elegida (en adelante, «P» es ese brazo).
- **Multiplicidad**: dos contrastes contra P, cada uno al 5 % de una cola, sin corregir; se declara que la probabilidad
  de que alguno gane sólo por azar es mayor que 5 %.
- **Descriptivas, no deciden**: las pasadas que cambian de publicación contra P, por nombre y etiqueta; en las
  pasadas lejanas, cuántas tienen algún alertado (un cero de E_lejana sin alertados no dice nada); y la distancia de
  cada brazo desde la celda central de la grilla contra la `Distancia_km` de MIROVA (OCR sólo desde el 2026-06-13,
  A119; diferencia de radios, A93).

## 6 ter. Regla N-3 (agregada el 2026-10-28, antes de ver los datos; programa §12.0, §12.1 y §12.5)

Nicolás decidió (S166) que las alertas sólo del OCR de Suomi NPP anteriores al 2026-10-09 se informan aparte y no
deciden: en el auto-audit (#924) y en V375-E (§8.13 de su pre-registro, sellado el 2026-10-28). Aquí se aplica lo mismo:

- **Qué pasadas**: protegida (`protegida`), sin alerta de la tabla (`alerta_tabla` falso, o sea que la protegida
  existe sólo por el OCR), de Suomi NPP (`sensor == "VIIRS_SNPP_750"`) y con `hora_utc` anterior al 2026-10-09.
- **Qué cambia**: no vetan. No cuentan en el P1 de la elegibilidad del §6 bis ni en el P1 del §6.2 (ninguna de sus
  dos ramas: la protegida que K publica y P no, ni la protegida de MIROVA que P no publica). Con la tabla sola nunca
  contaban, porque no tienen alerta de la tabla; la regla sólo toca el canal de tabla más OCR.
- **Qué no cambia**: la magnitud M (§6.2) y E. Una protegida no entra a E, y la regla habla sólo del veto, igual que
  en V375-E. La sombra (§4.3) empieza el 2026-11-03, después del hito y del cese de Suomi NPP (2026-11-02), así que no
  tiene pasadas de esta clase.
- **Cómo se informa**: el analizador las lista aparte por nombre (volcán, hora, cuál brazo las publica) y, por cada
  brazo, imprime el P1 que veta sin ellas al lado del P1 que las cuenta todas. Una pérdida de esta clase se ve, pero no
  bloquea.
- **Implementación**: después del medidor completo que corre sobre el analizador sin N-3 (no se edita el analizador
  mientras corre, A112), con escenarios rojos antes del cambio y mutaciones que deshagan la regla, atrapadas por
  aserción.

## 6. Regla de adopción (escrita antes de ver los datos)

P (con la posición elegida en el §6 bis) se propone a Nicolás para producción (A45) si y sólo si:

1. **Equivalencia** (§4.1): 0 pasadas distintas fuera de la banda de triangulación, en local y en el runner; **6 de 6**
   mutaciones atrapadas por aserción (las seis del §4.1) y la de control como caída. (L2, resuelta por D-48: este punto
   decía «5 de 5», un resto de cuando la prueba tenía cinco.)
2. **Censo** (§4.2), en T y en O, con la tabla sola **y** con tabla más OCR:
   - P1 = 0 (ninguna protegida que K publica y P no; ninguna protegida de MIROVA que P no publique, fuera de las que K
     tampoco publica, que se listan);
   - P2 de P contra K: GANA o EMPATE (no PIERDE ni BLOQUEA);
   - M: mediana de la razón P/MIROVA entre 0,9 y 1,1 (bordes incluidos) en **todas las protegidas que P publica**, con
     VRP de P y de MIROVA mayores que 0, publique K o no; y el comparador separa a P de K×1,2. (L4, resuelta por D-48:
     la calibración que se exige es la de P. Si P publica al doble de MIROVA justo en las protegidas que K no ve, eso
     es un defecto de P, y una razón restringida a las que también publica K lo escondería. La razón sobre las que
     publican K y P, que es el conjunto del comparador, se imprime al lado y no decide.)
3. **Sombra** (§4.3): P1 = 0; si hay sustrato, P2 no PIERDE.
4. Los controles de §7 en verde.

Si 1 falla, se arregla la vía y se repite §4.1 (no se mira el censo). Si 2 falla sólo en P2 por la ventana O y no por
la T, se informa por canal antes de decidir (el OCR es la parte menos creíble de la referencia). Si P no se adopta,
V750-D (Kgeo) pasa a tener su propio A/B (programa §3).

## 7. Controles (antes de leer el veredicto)

| control | qué tiene que dar |
|---|---|
| K = producción | publica igual y `pc.vrp_mw` a 0,001 MW; se toleran hasta 1 % de pasadas ok distintas y ninguna protegida (de la tabla o del OCR); con menos de 100 pasadas ok el 1 % es cero, así que una sola cierra (VB-A07). Esas pasadas salen de P1, P2, M y de los controles que comparan contra K, y se listan por nombre; la equivalencia P = O (§6.1) y el S-1 se siguen midiendo sobre TODAS las observadas, porque no dependen de K (VB-A02) (L18, resuelta por D-48: la tolerancia de V750-B, mismo probe y misma población; con cero, una diferencia de máquina entre runners como la de S152 cerraría la compuerta sin defecto del paquete) |
| P = O | §4.1 en el runner |
| control positivo de la ROI | P-def pierde al menos una protegida de Cordón Caulle |
| placebo | K×1,2: en la publicación, igual a K salvo donde los filtros de artefacto del tablero miran la magnitud; M lo tiene que separar de K (ver la nota de abajo) |
| nulo | K contra K (gemelo en otro proceso del mismo runner) da P2 EMPATE o SIN SUSTRATO y M sin separación |
| cobertura | §8.1 del programa: lista vacía o explicada |

**Nota del placebo (L7, resuelta por D-48).** La frase que estaba en la tabla, «el predicado no mira la magnitud salvo
VRP > 0», es falsa para el tablero de hoy: `isCirrusArtifact` (`frontend/index.html:1336-1340`: `t_max_k` bajo 273,15 K
y VRP de cumbre sobre 10 MW) e `isDiffuseFieldArtifact` (`:1355-1363`: `t_max_k` bajo 278,15 K, 100 píxeles o más, VRP
de 50 MW o más y menos de 1 MW por píxel) miran la magnitud, así que un K de 9,0 MW con `t_max` 270 K publica y el mismo
por 1,2 no (verificador del analizador, VA-02). Físicamente son los filtros del tablero contra el cirro frío y el campo
difuso sobre fondo gélido. Hay un tercer sitio, que la versión anterior de esta nota omitía (segunda vuelta del
verificador, VB-A01): `mirovaEqVrp` devuelve 0 sobre 50.000 MW (`frontend/index.html:1182`), el tope de cordura del
tablero, sin mirar `t_max`. El control queda como compuerta, con esta forma: una diferencia de publicación K contra
K×1,2 en una pasada cuyo record de K tiene `t_max_k` bajo 278,15 K (los dos filtros exigen ese `t_max`) o cuyo VRP de K
queda bajo el tope y el de K×1,2 sobre él, se lista por nombre y no cierra; cualquier otra diferencia cierra. La
versión anterior decía que con el predicado de hoy la otra clase no se puede producir: era falso, el tope la producía.
Con las tres explicaciones, esa mitad del control sólo atraparía un sitio nuevo del tablero que mire la magnitud (se
declara en `LECTURAS_EVALUAR_V750A.md`, A116).

## 8. Predicciones (para poder fallar)

Con la ROI B1 (O-sens), del censo S159 sobre 2026-04-01 a 10-21: P publica 15 negativos limpios contra 54 de K, pierde
0 protegidas y gana 1, gana 59 alertas bajo 1 MW y pierde 8; ΔE ≈ −90. Razón en protegidas ≈ 1,00. P-def pierde 6
protegidas de Cordón Caulle. P-sinfiltro: hasta 43 negativos (censo C-3), así que **predigo que P-sinfiltro empata o
pierde contra P** en P2. Kgeo: cambia 7 a 13 de ~290 publicaciones de K, todas hacia arriba (verificador de CM162).

## 9. Implementación (PR en borrador, después del sello; A45)

- Tag defensivo `pre-s16x-v750-codigo-mirova` y el sí de Nicolás antes del primer edit en `pipeline/`.
- Módulo nuevo `pipeline/mirova_v750_codigo.py`: el port con el aviso MIT de Coppola, cabecera FICHA y comentario «POR
  QUÉ» por bloque (CPLT N°372); remuestreo a la grilla GEO; record con el esquema de hoy.
- Flag `enable_v750_codigo_mirova` (por defecto `false`), leído desde `pipeline.profile` en la sección donde el código
  lo lee (S124, A89), con test que lo compruebe.
- La grilla por volcán (EPSG y esquina) en `volcanoes.yaml` con test de regresión (A63).
- **Laboratorio** (A117): si `mirova_equivalent` pasa a P, `experimental` sigue con K (ve más, no menos); el guard
  `tests/test_guard_laboratorio_no_mas_ciego_s147.py` se adapta en el mismo PR para comparar por dirección.
- `docs/FICHA_SDA_VRP_CHILE.md` y `docs/MIROVA_DIVERGENCES.md` (D17, D22, D25, D34) actualizados en el mismo PR (A113).
- CI con conclusión antes de dar el PR por listo (A39 enmienda S142).

## 10. Lo que este pre-registro NO decide

- La ROI (V750-B), el diurno (V750-E), VIIRS 375 y MODIS.
- No cambia la vara: lectura A, regla SN y corte de 1 MW quedan como están.
- La adopción misma: la decide Nicolás con los resultados en la mano (A45).

## 10b. Lecturas resueltas bajo D-48 (2026-10-25)

Nicolás (2026-10-24, D-48): «sobre las decisiones mías haz lo que tú recomiendes». La sesión VIIRS 750 2 resolvió con
su recomendación las cuatro lecturas que el analizador dejó para el sello (`LECTURAS_EVALUAR_V750A.md`); quedan
informadas a Nicolás y son revocables antes del sello:

| lectura | decisión | por qué |
|---|---|---|
| L2 | §6.1 exige 6 de 6 mutaciones (no 5 de 5), las seis del §4.1 por nombre (VB-A06) | son las seis del §4.1; el «5» era un resto |
| L4 | razón de M sobre todas las protegidas que P publica | revierte la lectura que tomó el analizador tras VA-03: la vara es la calibración de P; la otra se imprime al lado |
| L7 | placebo de publicación: las diferencias con `t_max` de K bajo 278,15 K, o que cruzan el tope de 50.000 MW del tablero, se listan y no cierran | la premisa de §7 era falsa (VA-02); los dos filtros de artefacto y el tope son los sitios del tablero que miran la magnitud (el tope lo agregó VB-A01) |
| L18 | K = producción con la tolerancia de V750-B (1 %, ninguna protegida de la tabla o del OCR; con menos de 100 pasadas, ninguna); las distintas salen de P1, P2, M y los controles contra K, no de §6.1 ni del S-1 | revierte la de cero que tomó el analizador tras VA-01: mismo probe y misma población que V750-B, y los runners tienen diferencias de máquina (S152); la equivalencia no depende de K (VB-A02) |

Cada una cambia el analizador y su prueba en el mismo commit; los escenarios E28, E30, E31, E50, E51 y E52 de
`probar_evaluar_v750a.py` las fijan y salen rojos contra el analizador anterior (E28, E30, E31, E51; E50 y E52 vigilan
el tope y la protegida). La segunda vuelta del verificador (Fable 5.1, `verificador_v2/INFORME.md`): listo con
cambios de texto, ninguna de las cuatro abre un veredicto de adopción falso; sus hallazgos VB-A01 a VB-A07 se
corrigieron con E53 a E60 y las mutaciones M57 a M62.

## 11. Pendiente antes del sello

- **Brazos de posición (§3 y §6 bis, agregados el 2026-10-27)**: ~~el analizador (P-cercano y P-pico desde los mismos
  píxeles del paquete, E_lejana, P2' y la regla del §6 bis), sus escenarios y sus mutaciones~~ hechos el 2026-10-28:
  escenarios E61 a E73 en `probar_evaluar_v750a.py`, rojos por aserción contra el analizador anterior
  (`probar_evaluar_v750a_rojo_posicion_salida.txt`, 13 de 13) y la batería entera verde con ellos
  (`probar_evaluar_v750a_salida.txt`, 74 de 74); mutaciones M63 a M80, 18 de 18 atrapadas por aserción sobre la batería
  restringida a E61 a E73, con identidad y control de caída como deben (`mutar_evaluar_v750a_posicion_salida.txt`);
  lecturas nuevas L20 a L27 en `LECTURAS_EVALUAR_V750A.md`. Falta: la corrida completa del medidor sobre la batería
  entera (unas 7 h, con disco y CPU libres; confirma también que M63 a M80 no se caen en los escenarios viejos) y un
  verificador limpio de este agregado.
- **El sello depende de la lectura de V750-B** (programa §12.1 paso 4 y §12.5 punto 2): la ROI que elija V750-B se
  incorpora a P antes del sello, con sus escenarios y su medidor; sin esa lectura no se sella.
- **Regla N-3 (§6 ter)**: escrita el 2026-10-28; falta su implementación en el analizador, escenarios y mutaciones,
  cuando termine el medidor completo que corre sobre la versión sin N-3 (desde el 2026-10-28 13:50 UTC).
- Resultado de V750-B (la ROI) y del brazo nativo N0/N1 (confirma V750-C).
- Analizador `evaluar_v750a.py` con la regla de §6, probado sin red (nulo, placebo y control positivo sobre las 510
  grillas de N), y su verificador limpio.
- ~~Prueba de equivalencia local de §4.1 escrita antes de la implementación (TDD), roja sobre el `main` de hoy.~~
  Hecha (`equivalencia_v750a.py`); falta su verificador limpio, junto con el del pre-registro.
