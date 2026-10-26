# Pre-registro V750-A (S162): el paquete del código de MIROVA contra K en VIIRS 750

Estado: **BORRADOR para el sello de Nicolás.** Depende de V750-B (la ROI) y de V750-C (que el remuestreo es pieza
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
- **M** magnitud: razón brazo/MIROVA en las alertas que publican los dos, con el comparador de ganancia pareja
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

## 6. Regla de adopción (escrita antes de ver los datos)

P se propone a Nicolás para producción (A45) si y sólo si:

1. **Equivalencia** (§4.1): 0 pasadas distintas fuera de la banda de triangulación, en local y en el runner; 5 de 5
   mutaciones atrapadas por aserción.
2. **Censo** (§4.2), en T y en O, con la tabla sola **y** con tabla más OCR:
   - P1 = 0 (ninguna protegida que K publica y P no; ninguna protegida de MIROVA que P no publique, fuera de las que K
     tampoco publica, que se listan);
   - P2 de P contra K: GANA o EMPATE (no PIERDE ni BLOQUEA);
   - M: mediana de la razón de P entre 0,9 y 1,1 en las protegidas, y el comparador separa a P de K×1,2.
3. **Sombra** (§4.3): P1 = 0; si hay sustrato, P2 no PIERDE.
4. Los controles de §7 en verde.

Si 1 falla, se arregla la vía y se repite §4.1 (no se mira el censo). Si 2 falla sólo en P2 por la ventana O y no por
la T, se informa por canal antes de decidir (el OCR es la parte menos creíble de la referencia). Si P no se adopta,
V750-D (Kgeo) pasa a tener su propio A/B (programa §3).

## 7. Controles (antes de leer el veredicto)

| control | qué tiene que dar |
|---|---|
| K = producción | publica igual y `pc.vrp_mw` a 0,001 MW en todas las pasadas ok |
| P = O | §4.1 en el runner |
| control positivo de la ROI | P-def pierde al menos una protegida de Cordón Caulle |
| placebo | K×1,2: P1 y P2 iguales a K por construcción en la publicación (el predicado no mira la magnitud salvo VRP > 0); M lo tiene que separar de K |
| nulo | K contra K (gemelo en otro proceso del mismo runner) da P2 EMPATE o SIN SUSTRATO y M sin separación |
| cobertura | §8.1 del programa: lista vacía o explicada |

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

## 11. Pendiente antes del sello

- Resultado de V750-B (la ROI) y del brazo nativo N0/N1 (confirma V750-C).
- Analizador `evaluar_v750a.py` con la regla de §6, probado sin red (nulo, placebo y control positivo sobre las 510
  grillas de N), y su verificador limpio.
- ~~Prueba de equivalencia local de §4.1 escrita antes de la implementación (TDD), roja sobre el `main` de hoy.~~
  Hecha (`equivalencia_v750a.py`); falta su verificador limpio, junto con el del pre-registro.
