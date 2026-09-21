# Pre-registro: la conectiva `max` fuera de septiembre, y el brazo MODIS con banda 22 (S149)

> **VERSION 2, NO APROBADA. No se ha despachado nada.** La versión 1 pasó por un verificador con
> contexto limpio que la dejó "apta con cambios" (`docs/audit_s149/VERIFICADOR_PREREGISTRO_INVIERNO.md`,
> diez hallazgos, uno de gravedad 5). Esta versión los incorpora; la sección 9 dice qué cambió y por
> qué. Falta el "sí" explícito de Nicolás: el candado `preregistro_aprobado` es suyo.
> Es una adenda de `experiments/_s147_ab_conectiva/PREREGISTRO.md`: hereda su fenómeno, su hipótesis
> y su sección 6 (no autoriza nada en producción).

## 1. Por qué hacen falta otras ventanas

El A/B de septiembre confirmó que `max` apaga selectivamente el borde del barrido con fondo frío en
VIIRS 375 (`docs/S148_RESULTADO_AB_CONECTIVA.md`). Veinte días de septiembre son una sola condición
de terreno. Dos preguntas quedan abiertas: si el efecto se repite con la escena en pleno invierno
(nieve extendida, fondo frío en casi todo el barrido, que es justo la condición donde `max` recorta
más), y si se repite donde hay más señal débil que perder.

**Lo que estas ventanas NO pueden responder, dicho de entrada.** La versión 1 se justificaba con
Villarrica y Nevados de Chillán, los dos volcanes de foco más débil. Medido el sustrato, esa
justificación no se sostiene: la tabla de tiempo casi real de MIROVA trae muy pocas alertas de esos
dos volcanes en cualquier mes del año (Villarrica, entre 1 y 9 pasadas por mes; Chillán, entre 0 y
4, todas bajo 0,5 MW). Ninguna ventana tiene poder para decidir sobre ellos por separado. Se
informan pasada por pasada y no deciden.

## 2. El sustrato, medido ANTES de elegir las ventanas

`sustrato_referencia.py` (versión 2) cuenta **pasadas nocturnas únicas** con alerta de MIROVA, por
mes, desde que hay serie continua nuestra (`sustrato_referencia_salida.txt`). La versión 1 contaba
doble cada pasada que tiene fila de la tabla y fila de OCR, y sólo miraba de junio a agosto.

| mes | V375 | V750 | MODIS | Villarrica V375 (n, bajo 0,5 MW) | Láscar MODIS (n, con 0,5 MW o más) |
|---|---|---|---|---|---|
| marzo | 187 | 52 | 27 | 3, 3 | **27, 25** |
| mayo | **296** | 52 | 11 | **9, 8** | 11, 6 |
| junio | 238 | 50 | 13 | 3, 2 | 13, 6 |
| agosto 01 a 27 | 126 | 26 | 1 | 5, 0 | 1, 0 |

(La tabla completa, de febrero a agosto, está en la salida.) Tres consecuencias:

- **Mayo es el mes con más sustrato VIIRS del año** y el único con un Villarrica débil de cierto
  tamaño (9 pasadas, 8 bajo 0,5 MW, del 11 al 31 de mayo).
- **Agosto es la escena de invierno**, con menos sustrato (126) y un Villarrica que en esa ventana
  está fuerte (5 pasadas del 18 al 24, mediana 1,82 MW): sirve para la nieve, no para el foco débil.
- **El sustrato MODIS es marzo, no junio**: 27 pasadas de Láscar, 25 con 0,5 MW o más, contra 13 y 6
  en junio.

## 3. Ventanas y brazos

| # | ventana | volcanes | brazos | pregunta |
|---|---|---|---|---|
| **V1** | 2026-05-01 a 2026-05-31 | los 11 Tier A | B, F | la conectiva en VIIRS donde hay más señal que perder |
| **V2** | 2026-08-01 a 2026-08-27 | los 11 Tier A | B, F | la conectiva con escena de invierno |
| **M** | 2026-03-01 a 2026-03-31 | sólo Láscar | B, J, K | la conectiva en MODIS, junto con la banda 22 |
| control | cada ventana | sólo Láscar | gemelo de B | determinismo del reproceso (sección 6) |

B es `_s146_ab_sin_test1` (control), F `_s147_ab_sin_test1_max`, J `_s149_ab_sin_test1_b22`,
K `_s149_ab_sin_test1_b22_max`, y el gemelo `_s149_ab_sin_test1_gemelo`. Resueltos como los resuelve
el código (`diff_perfiles_s149_salida.txt`, A89): el gemelo difiere de B sólo en nombre y directorio;
J de B sólo en `ENABLE_MODIS_B22_PRIMARY`; K de J sólo en `ENABLE_TESTS_23_PROSE_BRANCH`. El
verificador trazó que los dos flags llegan a todos sus consumidores (A118): la banda se decide en un
solo punto (`merge_mir_bands`) y radiancia, temperatura de brillo y NTI heredan la elegida; la
conectiva viaja en las cuatro llamadas de cada procesador.

V2 termina el 27 para no cruzar el 2026-08-28 23:00 UTC (A104). Todos los brazos se reprocesan con el
código de hoy; la referencia de MIROVA no depende de nuestro código.

**Por qué tres brazos en MODIS.** En MODIS `max` sola apaga el detector, porque la banda 21 tiene
unas diez veces más ruido que la 22 y ese ruido infla la desviación de la escena que `max` usa como
umbral. La pregunta con sentido es J contra K. B contra J es D21 por sí sola y se informa aparte.

**Referencia congelada por ventana** en `_congelado/<ventana>/` con su manifiesto
(`congelar_referencia.py`): la de S146 está recortada a septiembre. Comprobado que la congelada
reproduce el sustrato del snapshot vivo (296, 126 y 27).

**Requisito de despacho**: los perfiles J, K y gemelo tienen que estar en `main` (el workflow corre
desde `main`), y el paso que confirma el brazo imprime ahora también `conectiva_prosa`, `caja_roi1` y
`modis_b22`, que antes no salían en el registro del job.

## 4. Con qué se mide

El evaluador de S146 no puede dar veredicto en estas ventanas: sus parámetros, sus pisos de recall en
conteo absoluto y su lista de pérdidas esperadas son de septiembre, y sin producción comparable
siempre imprime INDECIDIBLE. No se fuerza. Se mide con dos scripts de esta carpeta:

- `armar_tabla.py`: tabla por pasada con los dos brazos, para cualquier ventana y referencia, usando
  el predicado de node y el etiquetador del evaluador. **Validado**: sobre septiembre reproduce la
  tabla del verificador de S148 con 0 diferencias de etiqueta o de publicación en 2.386 pasadas.
- `medir_predicciones.py`: P1, P2, P4, P5, P6 y la selectividad. **Probado sobre septiembre**
  (`medir_predicciones_septiembre_salida.txt`): devuelve 29,8 a 2,7 % en negativos limpios, recall
  137 a 135, razón borde sobre nadir 2,17 a 0,25 y selectividad cumplida, o sea lo ya publicado.
  (La razón del control da 2,17 y no el 2,15 de S148 porque los cortes de zona de este script son
  36 y 52 grados sobre el ángulo del brazo de control; el del brazo F no cambia.)

Receta de la unión de septiembre, que no estaba escrita en ningún lado: brazos B y F del run
35548121381, con Chaitén, Tupungatito y Villarrica del brazo B reemplazados por los del run
35558196104. Se extrae con `git archive <rama> <ruta>`, siempre con ruta (17 MB, no 900).

## 5. Predicciones para V1 y V2 (VIIRS 375), cada ventana por separado

Los umbrales de P1, P2 y P4 son los del pre-registro de S147; no se afinan con lo visto en septiembre.

| # | predicción | regla exacta | si falla |
|---|---|---|---|
| **P1** | baja la publicación en negativos limpios | F en **18 % o menos**. **Sólo decide si B supera 18 %** en esa ventana; si no, INDECIDIBLE (B nunca se ha medido fuera de septiembre) | el efecto no generaliza |
| **P2** | selectividad por zona | razón entre la tasa falsa del borde y la del nadir de F en **1,3 o menos**. Exige 10 negativos limpios o más en cada zona; si el nadir de F publica 0, la razón se calcula contra una publicación | el recorte no es selectivo del borde |
| **P4** | recall por pasada | F conserva al menos `ceil(n_B × 118 / 141)` de las `n_B` positivas que publica B, y **ninguna** pérdida con 0,5 MW o más de MIROVA. Se informa además con la tabla de MIROVA sola, sin OCR, porque la versión del OCR cambia dentro de las ventanas (29.x del 12 al 14 de junio, 30.0 el 6 de agosto) | NO ADOPTAR |
| **P5** | pasadas que MIROVA lista con VRP 0 en noche con alerta | F recorta ese estrato **más que un apagado parejo**: razón F sobre B menor que la fracción de todo lo publicado por B que F conserva. Exige 20 publicadas por B o más | el recorte en ese estrato no es selectivo |
| **C8b** | selectividad a una cola | `evaluar.selectividad_supervivencia` (PR #739): observado mayor que el percentil 97,5 del nulo | lo apagado no distingue positivas de negativos |
| P6 | Villarrica y Chillán | **informativa**: cada positiva, una por una, con su magnitud y qué hace cada brazo | no decide: sin poder |

**Por qué P5 no tiene un número fijo.** La versión 1 pedía "la mitad o menos". Medido sobre
septiembre, un apagado sin ninguna selectividad ya deja esa razón en 0,47, o sea que el azar la
cumplía. En septiembre F da 0,37 contra 0,47. Y la supervivencia de lo que publica el control ordena
los tres estratos como uno esperaría físicamente: **negativos limpios 9 %, RUTINA en noche con alerta
37 %, positivas 99 %**. El estrato del medio se comporta como una mezcla, coherente con que cerca de
un tercio de esas pasadas cae sobre el foco (`docs/S149_COSTO_OCULTO_MAX.md` §4). P5 sólo arbitra
NOAA-20 y NOAA-21: la tabla de MIROVA casi no lista Suomi NPP.

**Qué etiqueta decide (A119, agregado tras la observación de Nicolás, ANTES de evaluar ninguna
ventana).** La referencia no tiene la misma calidad todo el año (`docs/audit_s139/MAPA_BASES_MIROVA_V1.md`
§2; `calidad_referencia_por_mes_salida.txt`). El OCR estuvo mal calibrado hasta el 2026-06-11 y no midió
distancia hasta el 2026-06-13, y en mayo un tercio de las alertas de VIIRS 375 viene sólo del OCR. Por
eso, **en toda ventana que empiece antes del 2026-06-13 (mayo y marzo) P4 y C8b DECIDEN con las
positivas de la tabla sola**, y la versión con OCR se informa aparte. Los negativos limpios y el estrato
de P5 salen siempre de la tabla, así que P1, P2 y P5 no cambian. MODIS no depende del OCR en ningún mes.
`medir_predicciones.py` ya imprime las dos versiones de P4.

**P3 no se usa**: en invierno casi todo el fondo es frío y la celda deja de ser un contraste.

**Regla de decisión por ventana**: MERECE SEGUIR si P1, P2, P4 y C8b se cumplen; NO ADOPTAR si P4
falla; INDECIDIBLE si falla la cobertura, el determinismo, o P1 o P2 caen en su cláusula de sustrato.
P5 y P6 se informan en el titular. Si V1 y V2 discrepan, se dice así y no se promedia.

## 6. Controles

- **Cobertura pareja y simétrica**, contada antes de mirar nada (A108), con la entrada `control` del
  workflow. Si falla: repetir el job corto, no interpretar.
- **Determinismo** (reemplaza al control positivo contra producción, que acá no existe: la producción
  de esos meses es de otro régimen): el gemelo de B sobre Láscar tiene que coincidir con B en la
  decisión de publicar en **98 de cada 100 pasadas o más**. Con gránulos de hace meses ya no hay
  promoción de tiempo casi real a estándar, así que se espera 100.
- **Identidad del predicado del tablero**, pineada, como en S147.
- **No se cita C8** (un apagador al azar lo cumple). La selectividad es C8b, cuyo nulo está medido:
  el apagador al azar lo cumple 3 de 200 veces en VIIRS 375.

## 7. Marzo, Láscar, MODIS

No hay línea base de J ni de K, así que prometer números sería inventarlos. Se pre-registra la
dirección y un umbral duro:

- K no pierde ninguna pasada MODIS positiva de Láscar que J publique y que MIROVA dé con 0,5 MW o más.
- K no publica más que J en negativos limpios de MODIS.
- Si J publica menos de 15 de las 27 positivas, el brazo es INDECIDIBLE por falta de sustrato.
- Se informa sin decidir: B contra J (es D21), magnitud pareada, y los tres sensores de Láscar.

Límite conocido: MODIS no corre en Windows (pyhdf), así que este brazo sólo se puede reprocesar en
GitHub Actions y no se puede ensayar en local antes.

## 8. Costo

El verificador midió que en septiembre cada job tardó 45 a 55 minutos por 20 días; la versión 1
sobreestimaba. V1 y V2: 22 jobs cada una más el gemelo, del orden de 75 a 90 minutos por job. M: 3
jobs más el gemelo. Se despacha **de a una ventana**, V1 primero. El cron del NRT ya entrega la mitad
de sus corridas desde el 2026-08-27 por un problema de GitHub conocido desde S133 (medido hoy: hueco
mediano de 4,8 h desde el 14 de septiembre, antes de cualquier A/B), así que la sospecha de S148 de
que los A/B lo hacían saltar no se sostiene; igual se mira mientras corre.

## 9. Qué cambió respecto de la versión 1, y por qué

| hallazgo del verificador | cambio |
|---|---|
| H5, gravedad 5: el evaluador no puede evaluar estas ventanas | sección 4: dos scripts propios, validados sobre septiembre; referencia congelada por ventana; control de determinismo |
| H1, gravedad 4: el sustrato contaba doble | conteo por pasada única; sección 2 reescrita |
| H2, gravedad 4: agosto trae un Villarrica fuerte | se dice; se agrega mayo como ventana principal |
| H6, gravedad 4: P6 no podía fallar en Chillán y era redundante en Villarrica | P6 pasa a informativa, y la sección 1 dice que no hay poder |
| H3, gravedad 3: junio no es el único sustrato MODIS | la ventana MODIS pasa a marzo |
| H4, gravedad 3: perfiles fuera de `main`, flags sin imprimir | requisito de despacho; tres flags agregados al registro del job |
| H7, gravedad 3: P1 se cumplía sola si B ya estaba bajo 18 % | cláusula de sustrato en P1 |
| H8 y H9, gravedad 2: redondeo de P4, P2 indefinida | fórmula `ceil` escrita; muestra mínima y piso en P2 |
| H10, gravedad 2: cambia la versión del OCR | P4 se informa también sin OCR |
| propio: P5 la cumplía el azar | umbral atado a su nulo |

## 10. Decisiones de Nicolás antes de correr

1. ¿Apruebas las tres ventanas (mayo, agosto, marzo sólo Láscar) en ese orden?
2. ¿Apruebas la regla de decisión de la sección 5, con P5 y P6 informativas?
3. El "sí" del candado, que se pone una vez por ventana.
