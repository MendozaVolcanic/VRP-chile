# Verificador con contexto limpio: la conectiva `max` en mayo de 2026 (S149)

> Afirmación revisada: `docs/S149_RESULTADO_CONECTIVA_MAYO.md` (commit `e1b9d6ac4`, rama `s149-resultado-mayo`).
> Datos: rama remota `s146-ab/35599902448`, extraída con ruta (28 MB) a una carpeta temporal fuera del repo.
> Scripts y salidas propias: `experiments/_s149_verificador_mayo/`. No se tocó `pipeline/`, no se corrió
> pytest, no se hizo commit ni push.
> **Reuso declarado**: para "publica" usé el predicado del evaluador (`banco_paridad.correr_node`, que
> ejecuta `frontend/index.html` con node) y el filtro diurno `es_pasada_diurna_descartada`. Todo lo demás
> (lectura de los JSON de los brazos, lectura de los dos CSV congelados, pareo a 120 s, etiquetas, conteos)
> está reimplementado en `v1_reimplementacion.py`, y se informa con y sin el filtro diurno.

## Veredicto

**SE SOSTIENE, CON SALVEDADES.** Todos los números de VIIRS 375 del documento se reproducen de forma
independiente, los brazos leyeron los flags que dicen, y la regla "decide la tabla sola" no esconde
ninguna pérdida de la tabla. Las salvedades son de proceso y de redacción, no de resultado; y la
sección 3 del documento interpreta mal las dos pérdidas del OCR (la evidencia apunta a una fuente
caliente lejana, no a un dígito mal leído), lo que en realidad **refuerza** la regla A119.

## 1. Caminos por los que podía estar mal (enumerados antes de medir)

1. La enmienda A119 podría ser posterior al resultado.
2. Sacar las positivas del OCR podría cambiar también los negativos o el denominador a favor de F.
3. `vrp_ref` podría tomar la fila equivocada cuando hay dos alertas pareadas y esconder una pérdida grande.
4. `alerta_solo_ocr` podría estar mal calculado.
5. Los brazos podrían no haber leído el flag de la conectiva.
6. Cobertura despareja entre brazos.
7. El predicado de publicar podría depender de algo que cambió entre brazos.
8. El script que mide pudo cambiarse después de ver los datos.
9. Los negativos limpios de mayo podrían no ser comparables con los de septiembre (composición).
10. Las pérdidas podrían ser chicas por pasada y grandes por noche (A94).
11. Las dos pérdidas del OCR podrían ser señal real del cráter.

## 2. Qué se reprodujo (salida: `experiments/_s149_verificador_mayo/v1_salida.txt` y `v3_salida.txt`)

| número del documento | reimplementación | coincide |
|---|---|---|
| 1.478 pasadas V375 en ambos brazos | 1.478 y 1.478, 1.478 comunes | sí |
| negativos limpios n 349, 30,1 a 2,3 % | n 349, B 105 (30,1 %), F 8 (2,3 %) | sí |
| P2: nadir 13/3 de 85, medio 23/1 de 70, borde 69/4 de 194; razón 2,33 a 0,58 | idéntico | sí |
| P4 con OCR: 296 positivas, B 288, F conserva 276, 2 pérdidas de 0,5 MW o más | idéntico | sí |
| P4 tabla sola: 198, B 195, F conserva 187, 0 pérdidas de 0,5 MW o más | idéntico | sí |
| las 8 pérdidas de la tabla, entre 0,02 y 0,12 MW (Tupungatito 3, Cordón Caulle 2, Chaitén 2, Isluga 1) | idéntico, fila por fila | sí |
| P5: razón 0,36 contra 0,62 de apagado parejo | 77 a 28 (0,36); parejo 449 de 723 = 0,62 | sí (mi n da 161 y no 159 porque armé "noche con alerta" sin el filtro diurno; no mueve la razón) |
| tabla de Lastarria: 35 alertas, mediana 0,07, máximo 0,20 | 35, 0,07, 0,20 | sí |
| tabla de Isluga: 30 alertas, mediana 0,26, máximo 0,74 | 30, 0,26, 0,74 | sí |
| V750 y MODIS | leídos de `resultados/mayo_VIIRS750.txt` y `mayo_MODIS.txt`, coinciden con el documento | sí (no reimplementados: SIN VERIFICAR de forma independiente) |

C8b no se reimplementó (SIN VERIFICAR de forma independiente); los valores del documento (+0,883 contra
+0,517) coinciden con `resultados/mayo_VIIRS375.txt` (+0,8828 y +0,5165).
"De las 11 pasadas MODIS con alerta de Láscar": la salida dice 11 positivas MODIS en total; que las 11
sean de Láscar sale del sustrato del pre-registro y queda SIN VERIFICAR acá.

## 3. Hallazgos, por gravedad (1 a 5)

### H1 (gravedad 3). Cuando se commiteó la enmienda A119 ya había datos de los dos volcanes de las pérdidas grandes

- Enmienda: PR #744, único commit 2026-09-21 13:48:56 UTC, mergeado 13:52:17 UTC (`gh pr view 744`).
- Run 35599902448: despachado 12:30:12 UTC; la rama con las salidas se escribió 17:32:06 UTC
  (`git log origin/s146-ab/35599902448`), así que **la evaluación sí es posterior a la enmienda**.
- Pero a las 13:49 ya habían terminado 6 jobs, entre ellos **los dos brazos de Lastarria (13:22 y 13:34) y
  los dos de Isluga**, y el workflow sube un artefacto por job
  (`.github/workflows/reproc-s146-ab-sin-test1.yml:148-154`). O sea que los datos de justo esos dos
  volcanes eran descargables antes de escribir la regla.
- No encontré ninguna señal de que se hayan bajado (SIN VERIFICAR, y un negativo así no se puede probar).
  La regla tiene motivación independiente y anterior (`calidad_referencia_por_mes_salida.txt`, mismo PR),
  y H5 de este informe la respalda con evidencia física. Conclusión: la frase "antes de que existiera el
  resultado" es cierta para la evaluación y **no es estrictamente cierta para los datos**. Conviene
  decirlo así en el documento, y para las ventanas que siguen escribir las enmiendas con el run sin despachar.

### H2 (gravedad 2). El veredicto de la tabla sola se agregó al script después de tener los datos

`medir_predicciones.py` se modificó en el mismo commit del resultado (`e1b9d6ac4`, 14:39 hora local): antes
imprimía sólo los tres conteos de la tabla sola; el piso, el conteo de pérdidas graves y la palabra CUMPLE
se agregaron después. El pre-registro decía que el script "ya imprime las dos versiones de P4", que era
cierto a medias. El cambio es mecánico (misma fórmula `ceil(n_B × 118 / 141)`, mismo umbral de 0,5 MW) y mi
reimplementación da lo mismo, así que no cambia nada; queda anotado por disciplina.

### H3 (gravedad 2). "Los negativos limpios salen siempre de la tabla" no es exacto

El etiquetador (`scripts/banco_paridad.py:275-302`) exige una fila RUTINA de la tabla, pero **excluye la noche
si hay cualquier alerta del sensor, incluidas las del OCR**. Con la tabla sola de punta a punta (el OCR no
existe) los negativos limpios pasan de 349 a 383 y P1 queda en **31,3 a 3,7 %** (B 120, F 14) en vez de
30,1 a 2,3 %. Sigue cumpliendo con holgura (umbral 18 %). Las 98 positivas que vienen sólo del OCR no se
vuelven negativos: quedan las 98 como `sin_info` (59 son Suomi NPP, 35 NOAA-21). Excluirlas no favorece a
F: entre ellas F conserva **89 de 93 (96 %)**, la misma tasa que en la tabla (187 de 195, 96 %).

### H4 (gravedad 1). `vrp_ref` y `alerta_solo_ocr` están bien

`anotar_vrp_mirova` toma la fila de la tabla antes que la del OCR (`evaluar.py:113-119`). Hay 42 positivas
con dos alertas pareadas. Recalculé las pérdidas graves con el **máximo** de cualquier alerta pareada: salen
las mismas dos y ninguna de la tabla. La única pérdida con doble fila (Tupungatito 05-24 06:36) trae 0,05 MW
en las dos fuentes. `alerta_solo_ocr` coincide con mi cálculo (98).

### H5 (gravedad 3, a favor del resultado pero corrige el documento). Las dos pérdidas del OCR son una fuente caliente a unos 19 km, no un dígito mal leído

Salida: `v2_noches_ocr_salida.txt` y los CSV congelados.

- **Lastarria 2026-05-02 05:06**: nuestro gránulo trae un píxel de **304 K sobre un fondo de 263 K**. El
  control lo tiene en la suma de escena (`vrp_mw` 1,139) y publica un cúmulo de 0,033 MW a 1,0 km; F deja
  como cúmulo primario ese píxel lejano: **1,107 MW a 19,5 km**, `far`. El VIIRS 750 de la misma pasada no ve
  nada en ningún brazo. En la tabla, esa misma noche MIROVA da 0,20 MW (06:12) y 0,10 MW (06:42) en el
  cráter, RUTINA con 0 a las 05:24, y en pasadas vecinas lista **FALSO_POSITIVO de 0,19 y 1,06 MW a 16 a 18 km**
  (2026-05-03 05:06 y 05:54).
- **Isluga 2026-05-29 04:54**: píxel de 289 K sobre 265 K; F lo deja en **0,49 MW a 18,6 km**. La tabla de
  esa noche da 0,49 MW (05:12) y 0,15 MW (06:00) a 0,53 km, y a las 06:36 un **FALSO_POSITIVO de 0,45 MW a
  15,66 km**.

Lectura: los 2,36 y 0,86 MW del OCR son del orden de lo que nuestro propio detector mide en ese objeto
lejano, y la tabla de MIROVA clasifica ese objeto como falso positivo cuando lo lista. El OCR de esa época
no medía distancia (`Distancia_km` 0 fijo, nota "Estrella en Y=..."), así que lo rotuló alerta. Es
exactamente el defecto que A119 describe. Dos correcciones al documento: (a) la hipótesis "dígito mal
leído" de Lastarria no se sostiene: la clasificación del OCR dice "Medio", coherente con más de 1 MW, y
nuestro gránulo tiene 1,1 MW reales a 19,5 km; (b) la de Isluga no es "plausible como señal del cráter":
es el mismo patrón. Límite: no vi las imágenes de MIROVA ni sé qué es la fuente (SIN VERIFICAR); la
atribución se apoya en magnitud, distancia y las filas FALSO_POSITIVO vecinas, no en posición con acimut (A93, A107).

Efecto colateral que el documento no menciona: en estas dos pasadas F no sólo apaga, **mueve el cúmulo
primario del cráter a 19 km**. No se publica (queda `far`), pero es el mismo fenómeno de "competencia por el
ancla" que frenó el A/B sin Test 1 en S147. Vale medirlo en el agregado antes de cualquier adopción.

### H6 (gravedad 2). Por noche, F pierde 2 de 138 noches con alerta de la tabla

En la unidad del operador (A94): de 138 noches (volcán, noche) en que el control publica alguna pasada
positiva de la tabla en V375, F se queda sin ninguna en **Chaitén 2026-05-19** (0,07 y 0,05 MW) e **Isluga
2026-05-25** (0,04 MW). Las dos bajo 0,1 MW. No miré si V750 o MODIS cubren esas noches (SIN VERIFICAR). El
documento sólo informa por pasada.

### H7 (gravedad 1). Flags, cobertura y predicado

- Los 22 jobs imprimen su línea `brazo`: 11 con `conectiva_prosa False` y 11 con `True`, y todo lo demás
  igual (`test1_path False`, `prioridad_debil True`, `caja_roi1 False`, `modis_b22 False`). Salida:
  `v4_flags_por_job_salida.txt`. Ojo: esa línea está en el registro de GitHub del job, no en los `.log` de la
  carpeta `logs` extraída.
- Cobertura: 3.682 y 3.682, sin faltantes (`cobertura.txt` del run).
- El predicado es el mismo para los dos brazos (mismo `index.html`, misma llamada). F publica y B no en una
  sola pasada de 1.478.

### H8 (gravedad 2). Comparabilidad de los negativos con septiembre y detalle de Villarrica

- Los 349 negativos limpios de mayo están muy concentrados: Chaitén 54, Copahue 62, Llaima 61, Chillán 54,
  Villarrica 51, Cordón Caulle 27; **Láscar, Lastarria e Isluga aportan 4 cada uno** (porque casi todas sus
  noches tienen alerta). El 30,1 % es un promedio de tasas muy distintas (Cordón Caulle 24 de 27, Copahue 8
  de 62). No comparé contra la composición de septiembre (SIN VERIFICAR); si se cita "mayo repite
  septiembre", conviene mostrar la tabla por volcán de ambas. Las 8 publicaciones falsas que le quedan a F:
  Chaitén 3, Cordón Caulle 3, Isluga 1, Villarrica 1.
- Villarrica: "conserva las 9" es cierto, pero con la etiqueta que decide sólo **4** de esas 9 son de la tabla
  (máximo 0,55 MW); las otras 5 son del OCR.

## 4. Números que difieren

Ninguno del documento. Los que agrego: P1 con tabla sola de punta a punta 31,3 a 3,7 % (H3); OCR solo, F
conserva 89 de 93 (H3); por noche, 2 de 138 perdidas (H6); P5 con n 161 en mi armado contra 159.

## 5. Qué le pediría al documento antes de darlo por cerrado

1. Reemplazar la lectura de la sección 3 por la de H5 y anotar el movimiento del cúmulo a 19 km.
2. Decir que la enmienda es anterior a la evaluación pero no a los primeros artefactos (H1).
3. Agregar la pérdida por noche (H6) y P1 con tabla sola de punta a punta (H3).
4. Sigue pendiente el determinismo (gemelo de Láscar, run 35599941522), que no revisé.
