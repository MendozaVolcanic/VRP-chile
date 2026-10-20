# Tarea 1.33 (a): por qué nuestra magnitud de Nevados de Chillán queda bajo la de MIROVA con K

> Escrito el 2026-10-20 (S157, sesión lateral del loop) y corregido el mismo día con el verificador con
> contexto limpio (veredicto PARCIAL, §7; informe en `verificador/INFORME_VERIFICADOR.md`). Sólo lectura: no
> toca `pipeline/`, los perfiles ni `tasks/LOOP_OBJETIVOS.md`, y no despacha nada. Todos los números salen de
> `a_pasadas_salida.txt` y `b_mancha_mirova_salida.txt` (regla S91). **No adopta nada**: es el insumo para que
> Nicolás decida qué pre-registrar primero.

## En una línea

**En VIIRS 375 el fondo no puede cerrar el déficit de las pasadas oblicuas de Chillán: ni restando un fondo
cero llegamos a MIROVA. En VIIRS 750 y MODIS sí podría, y ahí además pesa el recorte del tablero. Qué es el
resto (área del píxel, otro efecto del ángulo o píxeles que MIROVA suma y nosotros no) no se puede separar sin
el L1B ni el Npix de MIROVA. Recomendación: pre-registrar primero D25, pero con el criterio de Chillán
corregido, y D17 después con el contraste por zona de agregación.**

## 1. El fenómeno

Chillán tiene hoy un foco muy caliente y chico: en las pasadas en que MIROVA da 9 MW o más, el píxel más
caliente de VIIRS 375 está entre 328 y 347 K, sobre un anillo de 271 a 275 K. Ese calor ocupa una fracción de
un píxel. Cuando el satélite mira de lado (cenital de 50 a 68°), el píxel en el terreno es dos a cuatro veces
más grande que a nadir: el mismo foco queda repartido en más superficie y cada píxel brilla menos (a las 06:48
del 18-oct, el píxel de 750 m más caliente marca 288 K, contra 317 K a las 06:00, casi a nadir). Si la potencia
se calcula con el área nominal del píxel, se subestima en la proporción en que el píxel creció. Coppola 2014
§2.2 describe que MIROVA remuestrea a celdas de área fija («one hot-spot pixel, whose area is 2 km² in the
original image, becomes two pixels with equal areas of 1 km²», citado en `docs/s131/REMUESTREO_LEY_DE_AREA.md`);
que eso conserve la energía es inferencia nuestra, y el grupo escribe que el remuestreo corrige el cenit sólo
en parte (D17, nota S141). Nosotros usamos el área nominal sin remuestrear.

El fondo es otra historia. La cumbre nevada está más fría que los valles del anillo de 5 a 25 km, así que
nuestra mediana del anillo resta un fondo algo más tibio que el de los vecinos del cráter (D25). Pero frente a
un foco de 330 K a 3,74 µm el fondo pesa poco: su radiancia es una fracción chica de la del píxel caliente.
Sólo en los píxeles con poco exceso (VIIRS 750 y MODIS de lado, 280 a 290 K) el fondo se come una parte
importante, y ahí cualquier error de unos kelvin cambia mucho la magnitud.

Y queda una tercera posibilidad que este estudio no puede medir: que MIROVA sume vecinos tibios que nosotros no
alertamos (selección, A99 y A103).

## 2. Qué se midió, pasada por pasada

`a_pasadas.py` toma las alertas nocturnas de MIROVA en Chillán (referencia unificada remota de Mirova-v1,
pareo de ±2 min de `banco_paridad`), se queda con las pasadas con K (record con `codigo_sha`) que el tablero
publica (predicado de `frontend/index.html` ejecutado con node, A97) y separa la razón R = D / M (publicado
sobre MIROVA) en:

- **F_rec = D / S_in**, recorte del tablero: lo publicado sobre la suma de nuestros alertados dentro del inner
  de 5 km (todos nuestros alertados caen dentro). Medición pura.
- **F_cero**: lo que aporta el recorte a cero del exceso negativo (S26). Siempre 1 o más: sube la magnitud.
- **G = S_in / M**, lo que queda para selección, fondo y área. Sin el Npix de MIROVA no se reparte entre los
  tres; se acota sin L1B:
  - **fondo**: G con los vecinos 5 y 10 K más fríos que el anillo (sensibilidad, no medición de D25) y G con
    fondo cero, que es el techo de D25 tal como está programado (el flag sólo cambia el fondo de nuestros
    píxeles; no dice nada de la selección);
  - **área**: f_area, cuánto más grande es el píxel real que el nominal (modelo geométrico anclado al ATBD,
    brazo B de `experiments/_s131_audit/magnitud/02_correccion_area_por_angulo.py`), y G·f_area.
- **saturación**: I4 se descarta desde 361,27 K y no deja rastro en el record; se compara con VIIRS 750 de la
  misma pasada.

Controles: el VRP de los 263 píxeles (223 de las pasadas con alerta y 40 de las sin geometría) se reproduce
con la fórmula del procesador; D coincide con `f5_core_vrp_mw` en las 44 pasadas de VIIRS 375 y con
`primary_cluster.vrp_mw` en las 43 de VIIRS 750 y MODIS (verificador). Universo: 95 pasadas con alerta, las 95
con K, 87 publicadas (las 8 no publicadas están en la salida). Aparte, 11 alertas «sin geometría» publicadas
(MIROVA vio calor en esa pasada pero el OCR no sabe dónde): no sirven para detección, sí para magnitud, y van
como estrato separado.

### 2.1 El caso que pidió Nicolás: NOAA-21, 2026-10-18 06:48, cenital 67,6°

| | MIROVA | publicado | R | F_rec | G | G con vecinos 10 K más fríos | G con fondo 0 | f_area | G con área real |
|---|---|---|---|---|---|---|---|---|---|
| VIIRS 750 | 22,85 | 2,84 | 0,12 | 0,42 | 0,30 | 0,55 | 0,96 | 3,72 | 1,11 |
| VIIRS 375 | 25,79 | 8,93 | 0,35 | 0,95 | 0,36 | 0,41 | 0,47 | 3,73 | 1,36 |

Y las de la misma mañana casi a nadir:

| | cenital | MIROVA | publicado | R | F_rec | G | G fondo 0 | G con área real |
|---|---|---|---|---|---|---|---|---|
| VIIRS 750, 05:42 | 20,5 | 20,87 | 14,03 | 0,67 | 1,00 | 0,67 | 0,92 | 0,80 |
| VIIRS 750, 06:00 | 22,3 | 18,98 | 13,60 | 0,72 | 1,00 | 0,72 | 0,98 | 0,89 |
| VIIRS 375, 06:00 | 22,3 | 9,94 | 7,20 | 0,72 | 1,00 | 0,72 | 0,89 | 0,90 |

**VIIRS 750 a las 06:48.** Alertamos 6 píxeles que suman 6,84 MW, pero el tablero publica sólo el cúmulo en
modo de un píxel (2,84 MW): el recorte se lleva más de la mitad (F_rec 0,42). Lo que queda (0,30) no lo cierra
el fondo (fondo cero da 0,96; vecinos 10 K más fríos, 0,55). Un píxel alertado está a 268,9 K, bajo la mediana
del anillo (272,0 K): el entorno inmediato del cráter está más frío que el anillo, la dirección de D25 es
correcta. **VIIRS 375 a las 06:48**: el recorte no pesa (0,95) y el fondo casi no mueve nada (fondo cero, 0,47).
El área real lo pasa de largo (1,36), como S133 en el borde del barrido (`docs/s133/AB_AREA_VEREDICTO_CHUNK1.md`).

**Ojo con anclar en esta pasada (verificador):** de las 06:00 a las 06:48 quien cambia es MIROVA, no nosotros.
MIROVA multiplica su VIIRS 375 por 2,6 (9,94 a 25,79) y nuestra suma sube ×1,3 (7,20 a 9,37); en 750 MIROVA sube
×1,2 y nosotros bajamos a la mitad. Bajo la hipótesis del área, nuestro 375 y nuestro 750 implicarían cambios de
potencia incompatibles entre sí. Una pasada no basta para anclar un pre-registro.

### 2.2 Estratificado por cenital (medianas por pasada, 87 pasadas)

| sensor | cenital | n | R | F_rec | G | alza con vecinos -10 K | G con fondo 0 | f_area | G con área real |
|---|---|---|---|---|---|---|---|---|---|
| VIIRS 375 | < 30° | 12 | 0,73 | 1,00 | 0,73 | ×1,09 | 0,98 | 1,11 | 0,80 |
| VIIRS 375 | 30 a 50° | 13 | 0,58 | 1,00 | 0,58 | ×1,06 | 0,64 | 1,75 | 0,94 |
| VIIRS 375 | ≥ 50° | 19 | 0,45 | 1,00 | 0,45 | ×1,28 | 0,68 | 2,34 | 0,95 |
| VIIRS 750 | < 30° | 9 | 0,84 | 1,00 | 0,91 | ×1,19 | 1,22 | 1,20 | 0,97 |
| VIIRS 750 | 30 a 50° | 12 | 0,41 | 1,00 | 0,45 | ×1,35 | 0,96 | 1,71 | 0,79 |
| VIIRS 750 | ≥ 50° | 11 | 0,16 | 0,57 | 0,32 | ×2,00 | 1,18 | 2,35 | 0,59 |
| MODIS | < 30° | 5 | 0,75 | 1,00 | 0,75 | ×1,38 | 1,48 | 1,19 | 0,78 |
| MODIS | 30 a 50° | 3 | 0,20 | 0,71 | 0,34 | ×1,71 | 1,27 | 1,90 | 0,64 |
| MODIS | ≥ 50° | 3 | 0,20 | 0,70 | 0,20 | ×2,56 | 1,12 | 4,17 | 0,85 |

Con el corte que pide D17 (nota S141), cenit ≤ 40 contra > 40: VIIRS 375 R 0,68 contra 0,52 (G con área real
0,85 contra 0,95, sobre-corrige); VIIRS 750 R 0,79 contra 0,35 (G con área real 0,97 contra 0,66, sub-corrige);
MODIS 0,64 contra 0,20 (n = 7 y 4). La tabla completa, pasada por pasada, está en `a_pasadas_salida.txt`.

## 3. Qué componente crece con el ángulo

- **VIIRS 375: sólo G, y el fondo no puede ser.** El recorte es plano (1,00 en las tres bandas). Con fondo cero,
  G llega a 0,64 y 0,68 en las bandas oblicuas, y en 25 de 32 pasadas oblicuas ni el fondo cero cierra la
  brecha. Lo que hace caer G con el ángulo es área, otro efecto del ángulo o selección: este estudio no los
  separa. El área **reduce** la caída pero no la aplana: si lo que sobra a nadir (0,73 a 0,80) fuera parejo, G
  con área real tendría que quedar en ~0,80 en las tres bandas y queda en 0,80 / 0,94 / 0,95, la misma
  sobre-corrección que S133 vio con más pasadas. Y f_area está correlacionado 0,91 con la secante del cenital,
  así que las bandas no distinguen área de cualquier otra cosa que crezca con el ángulo (verificador H2 y H3).
- **VIIRS 750: el recorte del tablero aparece en el borde** (F_rec 0,57; el cúmulo en modo de un píxel, tarea
  1.8) **y la sensibilidad al fondo crece mucho** (×1,19 a ×2,00). Esa sensibilidad es función casi pura del
  exceso de temperatura del píxel sobre el fondo (verificador H8: correlación -0,95), y ese exceso cae con el
  ángulo en VIIRS 750 pero no en 375, aunque el área crece igual en los dos. Que el exceso caiga por dilución
  geométrica, y no por otro efecto del ángulo (camino atmosférico, oclusión del borde del cráter), no está
  medido.
- **MODIS: igual dirección que VIIRS 750**, con 11 pasadas en total.
- **El único contraste que separa área de ángulo es la zona de agregación a bordo** (al pasar de 2:1 a 1:1, cerca
  de 52,6° de cenital, el píxel se achica aunque el ángulo siga subiendo). Entre 40 y 62°: en VIIRS 375 la zona
  2:1 da G 0,55 y la 1:1 da 0,60 (n = 11 y 9), lo que el área predice; en VIIRS 750 da 0,48 y 0,34 (n = 9 y 5),
  al revés de lo que el área predice. Con estos n no decide nada.
- **Saturación: la falta de energía en VIIRS 375 es común a MIROVA y a nosotros.** En las cinco pasadas casi a
  nadir con mucha más energía en 750 que en 375, las dos razones coinciden (3,09 nuestra y 2,93 de MIROVA; 2,18 y
  1,81; 2,16 y 2,05; 1,89 y 1,91; 1,88 y 1,74). La correlación de 0,79 en las 30 pasadas está inflada porque las
  dos razones caen con el cenital (sólo por eso se esperaría ~0,47; verificador H7). Que la falta sea saturación
  de I4 es lo esperable, no está verificado sin L1B.
- **Recorte a cero: sube, no baja.** Está en 25 de 87 pasadas y su factor es 1,00 a 1,73 (en 2 de ellas el
  exceso total sin recorte es negativo y el factor no se define).
- **Las alertas sin geometría** (11, estrato aparte) traen un contraejemplo fuerte para el área: 10-oct 06:30, a
  50,5° y en zona 2:1, G 0,97 en VIIRS 375 (G con área real 2,16) y 0,81 en 750 (1,80).

## 4. Las miniaturas de MIROVA no discriminan

`b_mancha_mirova.py` cuenta los px blanco puro alrededor del cráter en las miniaturas «Latest10NTI» que MIROVA
publicó de Chillán el 17 y 18 de octubre (archivo `mirova-tif-archive`, data/png). La mancha crece con el
ángulo (VIIRS 375: 2 a 3 px entre 20 y 28°, 19 px a 67,6°; VIIRS 750: 12 a 24 px y 46 px), con pendiente
contra log(f_area) de 2,00 y 0,85 en las pasadas de 9 MW o más (n = 5 cada una).

**Pero no prueba el remuestreo del VRP (verificador H4, REFUTADO como discriminante).** La lámina es un mapa en
coordenadas de terreno: cualquier mapa así agranda la mancha de un píxel oblicuo, sume MIROVA el VRP sobre
celdas o sobre píxeles nativos con área nominal. Además el blanco sigue más a la potencia que al área
(correlación 0,94 contra 0,89 en VIIRS 375), y la pasada débil del 17-oct 04:42 casi no deja blanco. El mapeo
miniatura a pasada sí está verificado. Queda como dato, no como argumento.

## 5. Recomendación: D25 primero, con el criterio de Chillán corregido

1. **Lo que se sostiene (verificado):** en Chillán, D25 tal como está programado no puede cerrar el déficit de
   VIIRS 375 oblicuo, porque su techo (fondo cero) es 0,64 a 0,68. En VIIRS 750 y MODIS sí puede acercarse
   (techo 0,96 a 1,48) y su alza crece con el ángulo.
2. **Lo que no se sostiene:** que el resto sea área (D17). La primera versión de este README lo concluía por
   descarte, y el descarte no excluye la selección; el área sobre-corrige respecto del nadir; las bandas no la
   separan del ángulo; el contraste por zona sale mixto; las miniaturas no discriminan. Y la tarea 1.14 ya midió
   que D25 también tiene dependencia angular (1,18 a nadir, 1,41 en el borde, §3.4), en reproceso real.
3. **Por eso, pre-registrar primero D25** (tarea 1.29, como ya estaba planificado): es la única de las dos
   palancas medida como brazo de reproceso (1,28 en `literal`), el flag existe y está apagado
   (`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375` y `_VIIRS750`), y este estudio deja su predicción escrita y falsable
   para Chillán. **Pero el criterio de magnitud de Chillán no puede ponerse en VIIRS 375 oblicuo**, donde D25
   no puede pasar por construcción: el criterio va en VIIRS 750 y MODIS, y en VIIRS 375 sólo con cenit ≤ 40°,
   reportando además la tabla por banda de cenit (con el corte de 40° de D17).
4. **D17 después**, como A/B con dos brazos (remuestreo F70 centrado con `geo_utils.get_grid_center()`, hoy sin
   cablear, y área por píxel) y con el contraste por zona de agregación pre-registrado, porque es lo único que
   separa área de ángulo. Ninguno de los dos brazos está respaldado hoy (S133 se pasó; 1.14 no vio crecer el
   Npix de MIROVA).
5. **El recorte del tablero en VIIRS 750** (F_rec 0,57 en el borde) es una tercera palanca, independiente,
   abierta en la tarea 1.8.
6. **Lo más barato que falta para separar selección de fondo** es leer el L1B de 3 o 4 pasadas de Chillán (la
   de las 06:48 y las de las 05:42 y 06:00 del 18-oct): da el fondo real de los vecinos (D25 medido, no
   sensibilidad) y cuántos píxeles tibios alrededor del foco quedan fuera por dETI o por el piso C1 (selección).
   Necesita un probe en Actions con `EARTHDATA_TOKEN`, que esta sesión no despacha.

## 6. Lo que no se pudo resolver

- **El reparto selección contra fondo contra área** dentro de G: sin el Npix de MIROVA ni el L1B no se separa.
- **El fondo real de los vecinos**: sin L1B. Las credenciales locales son el par usuario y clave vencido que ya
  bloqueó la cuenta (A71), y el NRT corre con un token de la misma cuenta en plena erupción: no se intentó.
- **La contradicción con 1.14 sobre el Npix** (no crece con el ángulo en el OSF de 2025).
- **MODIS**: 11 pasadas en total.
- Menores (verificador H11): 10 pasadas usan el VRP del OCR, y 3 de VIIRS 750 traen enteros (hasta ±7 %); la
  pasada del 2026-09-28 05:18 en VIIRS 375 (MIROVA 0,05 MW) entra como positiva con la regla `original`, y bajo
  la regla SN de D-9 sería «MIROVA no vio nada».

## 7. Verificador con contexto limpio

Opus, sólo con rutas y scripts, re-corrió los dos scripts (mismas 95 / 95 / 87 pasadas, 223 de 223 píxeles,
misma tabla; sólo cambió el commit del consolidado) y escribió sus propias comprobaciones (`verificador/v1` a
`v5`; los scripts apuntan al worktree de D: de esta sesión). Veredicto **PARCIAL**: confirma la tabla, la
reproducción por píxel, el hallazgo lateral de MODIS y el techo del fondo en VIIRS 375; deja parcial la lectura
del área, la del testigo de saturación y la recomendación, y refuta las miniaturas como discriminante. Este
README ya incorpora sus hallazgos H1 a H10: la cabecera y §5 cambiaron de «D17 primero» a «D25 primero con el
criterio corregido», y se agregaron el corte de 40°, el contraste por zona y el estrato sin geometría.

## 8. Hallazgo lateral (no es de esta tarea)

Con K, MODIS toma la temperatura de la banda 22 (D21), pero el VRP vuelve a radiancia con la longitud de onda
de la banda 21 (`pipeline/process_modis.py:1036` y `:1040`). Así es como se reproducen los píxeles MODIS (con la
longitud de onda de la banda 22 sólo pasan 3 de 23); con la de la banda 22 la magnitud MODIS sería 1,052 a 1,059
veces mayor en las 11 pasadas (campo `f_lambda_modis`). Es chico frente al déficit, pero es una inconsistencia
que nació con D21, y no se ha medido si el k = 18,9 calibrado sobre la banda 21 vale para la 22.

## 9. Reproducir

```bash
python -I experiments/_s157_magnitud_chillan/a_pasadas.py --dest <temporal>      # baja la referencia de Mirova-v1
python -I experiments/_s157_magnitud_chillan/b_mancha_mirova.py --png <temporal>  # baja 4 láminas por la API
```

Referencia de la corrida final: consolidado `87771312303346e075801e624bc08b7839cc5f16`, OCR
`7bf81852cd5d9103e03ed957ba998c0c90d73586`; records de `data/mirova_equivalent/NevadosDeChillan.json` en
`57d18ad78` (sha del archivo en la salida). Con los consolidados `7968fa1b`, `25114fe7` y `81941e2c` (este último
en la corrida del verificador) dio las mismas 87 pasadas y la misma tabla.
