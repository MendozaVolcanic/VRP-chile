# D13 remedida: cuánta magnitud apaga hoy la cerca `distance_class != summit`

**Sesión S145 · 2026-09-20 · read-only (no se tocó `pipeline/` ni `frontend/`)**

Scripts y salidas: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s145_d13\`
(`remedir_la_cerca.py` → `remedir_la_cerca.json`, `remedir_la_cerca_regimen_previo.json` y
`remedir_la_cerca_con_dia_parcial.json`; `de_donde_salio_el_31.py` →
`de_donde_salio_el_31.json`). Ningún número de este informe está escrito a mano: todos
salen de esos cuatro JSON.

---

## 1. Qué se cubrió y qué no

**Cubierto.**

| eje | alcance |
|---|---|
| lectura de D13 | entrada completa (`docs/MIROVA_DIVERGENCES.md`, l. 1468 y siguientes), incluido el bloque "Clasificación cumplida, S126" |
| procedencia del 31 % | barrido de 4 denominadores candidatos × 8 cortes de fecha sobre los 11 Tier A |
| la cerca en el frontend | los 4 archivos de `frontend/` revisados uno por uno |
| remedición | 2.273 pasadas nocturnas de los 11 Tier A, 2026-09-01 a 2026-09-19, los 3 sensores |
| ventana de contraste | 9.962 pasadas, 2026-06-01 a 2026-08-25 (régimen anterior al #535 y al #571) |
| cruce con MIROVA | referencia unificada CONS ∪ OCR bajada del remoto del dueño, 1.842 filas nocturnas en la ventana actual y 7.270 en la de contraste |
| controles de instrumento | identidad del predicado contra el guard S139, y atribución (toda la diferencia de MW viene de la cerca) |

**No cubierto, y por qué.**

- **Los 34 volcanes fuera del Tier A.** No tienen serie continua (`volcanoes.yaml`: 11 con
  serie desde 2025-02, 34 con una ventana corta de abril-2026), así que una tasa sobre
  ellos no es comparable con nada.
- **Las pasadas diurnas.** Se descartan con el mismo criterio del pipeline
  (`auto_audit_weekly.es_pasada_diurna_descartada`), igual que en el banco de paridad.
- **La ventana que cruza el cambio de régimen.** Deliberado: el #535 (2026-08-28 23:00 UTC)
  apagó la máscara de nube y el #571 (2026-08-31 20:34 UTC) quitó el piso VRP. Las dos
  fechas se verificaron con `git log`. Una ventana que los cruce mezcla dos regímenes (A104).
- **El día parcial 2026-09-20.** Se excluyó tras comprobar que metía 9 noches falsas en la
  cuenta de "noches que se estrenarían": las 9 eran del día en curso, todavía sin las otras
  pasadas de esa noche. La corrida con el día incluido quedó en
  `remedir_la_cerca_con_dia_parcial.json` para que se vea la diferencia: mismas fracciones
  (83,4 % de MODIS apagado en vez de 82,5 %), pero 9 noches fantasma.
- **El escenario de levantar la cerca en el pipeline.** Esto mide el display, no propone
  ningún cambio: D13 está cerrada como documental desde S126 y aquí no se reabre.

**Control de instrumento (las dos preguntas).** El predicado de publicación es el del
dashboard ejecutado con `node` sobre `frontend/index.html` (sha `24fba8a1`), nunca
reconstruido a mano (A97). El control de identidad contra los 5 casos del guard S139 da
`([0,1,1,1,0],[1,0])`, que es el valor esperado, en las dos corridas. El control de
atribución exige que **ninguna** pasada que atraviesa la cascada cambie de magnitud al mover
el toggle: da 0 records y 0,0 MW de diferencia fuera de la cerca, en las dos ventanas. Sin
eso, los MW de abajo estarían midiendo otra cosa.

---

## 2. Qué afirma D13, exactamente

El título dice: *"La cerca `distance_class != summit` del frontend apaga el 31 % de la
magnitud"*. La tabla de abajo, en cambio, rotula la celda del 31 % como **records apagados**:

| condición del helper | records apagados | magnitud |
|---|---|---|
| `distance_class != "summit"` | 10.773 / 34.763 (31,0 %) | 17.678 MW |
| `pc.centroid_dist_km > inner_radius` | 0 (0,0 %), no-op | |

O sea que el 31 % nunca fue una fracción de magnitud: es una fracción de **conteo**, y los
17.678 MW van sin denominador al lado. El título pegó las dos cosas.

**La procedencia no cierra.** D13 atribuye la medición a
`experiments\_s124_observabilidad\`. Ese directorio existe, pero sus dos scripts miden la
ceguera de `t_bg` y su único JSON no contiene ninguno de los tres números. El par no tiene
script ni salida que lo respalde en el repo.

**Reconstruido, sí cierra** (`de_donde_salio_el_31.json`). Con corte 2026-08-25 y
denominador "records con `primary_cluster.vrp_mw > 0`":

| | D13 | reconstruido hoy |
|---|---|---|
| numerador | 10.773 | 10.770 |
| denominador | 34.763 | 34.739 |
| porcentaje | 31,0 % | 31,0 % |
| MW | 17.678 | 17.683,7 |

Los cuatro coinciden dentro del ruido de reprocesos. Ninguno de los otros tres
denominadores candidatos se acerca: sobre **todos** los records da 18,94 %, sobre los que
tienen `primary_cluster` da 27,81 %, sobre los que tienen `vrp_mw > 0` da 30,78 %. Así que
el 31 % de S124 es **la fracción de records no-summit entre los que tienen cúmulo con
magnitud, sobre toda la historia**, y los 17.678 MW son la **suma acumulada** de
`pc.vrp_mw` de esos records.

---

## 3. Dónde está la cerca

En las 3 vistas live, con el mismo par de condiciones dentro de `mirovaEqVrp`:

| archivo | condición 1 | condición 2 |
|---|---|---|
| `frontend\index.html` | l. 1056 | l. 1060 |
| `frontend\diario.html` | l. 241 | l. 250 |
| `frontend\mosaico.html` | l. 251 | l. 253 |

`frontend\comparacion.html` tiene su propio `continue` equivalente en la l. 205 y **cero**
usos de `mirovaEqVrp`: es el preview deliberadamente distinto, no se toca.

La magnitud que el operador ve en el gráfico es
`isThermalArtifact(r, inner) ? 0 : mirovaEqVrpDisplay(r, inner, includeFarDistance)`
(`frontend\index.html` l. 2258), con `USE_F5_CORE = true` por defecto. En VIIRS 375 eso pasa
por `f5_core_vrp_mw` y no por `pc.vrp_mw` (A10/A46): acá no hubo que elegir campo, porque
quien lo resuelve es el código del dashboard.

---

## 4. La remedición

### 4.1 En conteo, el 31 % sigue en pie

| ventana | no-summit / cúmulos con magnitud | % |
|---|---|---|
| S124, reconstruida (toda la historia al 2026-08-25) | 10.770 / 34.739 | **31,0** |
| acumulada a hoy (al 2026-09-19) | 11.321 / 36.646 | **30,9** |
| régimen previo (2026-06-01 a 2026-08-25) | 1.929 / 5.541 | **34,8** |
| **régimen actual (2026-09-01 a 2026-09-19)** | **411 / 1.462** | **28,1** |

El número acumulado casi no se movió, pero eso no prueba nada: un acumulado sobre un corpus
que creció de 34.739 a 36.646 está dominado por la historia vieja y no puede detectar un
cambio de régimen de tres semanas (A90). El que informa es el de la última fila: **28,1 %**,
contra 34,8 % en el régimen anterior. Bajó, pero sigue siendo del mismo orden.

### 4.2 En magnitud, el 31 % nunca fue el número, y hoy es más del doble

Ventana **2026-09-01 a 2026-09-19**, 11 Tier A, 2.273 pasadas nocturnas:

| | MW |
|---|---|
| lo que el gráfico dibuja hoy | 233,29 |
| lo que dibujaría sin la cerca | 797,35 |
| **lo que la cerca apaga** | **564,06 = 70,7 %** |

En la ventana de contraste (2026-06-01 a 2026-08-25) la cifra es **75,0 %**. O sea que la
fracción de magnitud apagada es estable alrededor de tres cuartos y **siempre lo fue**: el
31 % del título nunca describió la magnitud.

Los filtros de artefacto no cambian esto. Llaman a `mirovaEqVrp` con `includeFar` clavado en
`false` (l. 1215 y 1233), así que sobre un record que la cerca apaga ven 0 y no disparan.
Preguntándole a la misma función del dashboard por el mismo record con la etiqueta puesta en
`summit`, el resultado es que taparía **0 de los 411**: la cerca es lo único que retiene
esos 564 MW.

### 4.3 El reparto es de MODIS, no es plano

Esto corrige de frente lo que D13 dice ("el reparto por volcán es notablemente plano"):

| sensor | pasadas | % no-summit | MW hoy | MW sin la cerca | apaga |
|---|---|---|---|---|---|
| MODIS | 442 | **87,1 %** | 115,58 | 661,67 | **82,5 %** |
| VIIRS 375 | 918 | 0,65 % | 62,41 | 64,44 | 3,2 % |
| VIIRS 750 | 913 | 2,19 % | 55,30 | 71,24 | 22,4 % |

El reparto por volcán parecía plano porque se miraba agrupado (el error que persigue la nota
de S126 sobre estratificar): al abrirlo por sensor, casi 9 de cada 10 pasadas MODIS quedan
etiquetadas `far` mientras VIIRS 375 no llega al 1 %. Es exactamente la asimetría A81/A46
far→summit: el `final_hotspot` de MODIS, que se elige por máximo de MIR absoluto en la
escena, se va a un salar o a un valle tibio y arrastra la etiqueta, mientras el cúmulo sigue
en el cráter. A 1 km de píxel el gradiente topográfico compite con el foco (A69/A80), y eso
no pasa a 375 m. Los mismos porcentajes por sensor en el régimen anterior: MODIS 85,3 %,
VIIRS 375 1,7 %, VIIRS 750 10,5 %.

Por volcán, la magnitud apagada va de 12,7 % (Puyehue Cordón Caulle, cuyo `inner_radius` de
20 km deja casi todo dentro) a 92,5 % (Lastarria). El detalle completo, por volcán y por
volcán × sensor, está en `remedir_la_cerca.json`.

---

## 5. De lo que la cerca apaga, ¿cuánto confirmó MIROVA?

Los 411 records apagados, cruzados contra la referencia unificada (pareo de ±120 s):

| etiqueta | records | MW |
|---|---|---|
| **`pos`** (MIROVA alertó en esa pasada) | **0** | **0** |
| `neg_limpio` (MIROVA miró esa pasada y no vio nada) | 387 | 539,4 |
| `far_ref` (MIROVA marcó falso positivo: calor fuera del límite) | 5 | 6,0 |
| `sin_info` (sin fila pareable) | 19 | 18,7 |

Y en **noches de volcán**, que es la unidad en que el operador vive una alerta (A94): de las
209 noches de la ventana, las 209 publican algo hoy. La cerca **no tapa ninguna noche con
alerta de MIROVA**, y levantarla **no estrenaría ninguna noche nueva** sin confirmación.

**El poder del cruce, dicho de frente.** En septiembre MODIS tiene **1 sola pasada `pos`**
entre 442. Con ese denominador, "0 alertas tapadas en MODIS" no es una medición fuerte: es
que MIROVA casi no publicó por MODIS en estas tres semanas. La ventana de contraste sí tiene
músculo, y ahí el resultado es mucho más filoso:

> De las **16** pasadas MODIS del régimen anterior donde MIROVA alertó y nosotros detectamos,
> la cerca apagó **15**. Las 15 son de **Láscar**, con el cúmulo entre **0,64 y 2,86 km del
> cráter** (o sea, crateriano) y la etiqueta en `far`. **Las 15 noches ya estaban cubiertas
> por otra pasada publicada.**

Eso es lo que la cerca esconde cuando esconde algo real: no detecciones lejanas de verdad,
sino cúmulos crateranos mal etiquetados por el `final_hotspot` (A81). Y es redundante en
noches: 15 de 15 ya tenían la noche cubierta. Por eso el efecto sobre el recall del operador
es nulo, aunque el mecanismo esté vivo y sea grande en records y en MW.

---

## 6. Respuesta directa a la pregunta

1. **¿El 31 % sigue siendo el número correcto?** En **conteo**, sí, con un matiz: sobre el
   denominador de S124 (records con cúmulo con magnitud) hoy da **28,1 %** en el régimen
   actual y 30,9 % acumulado. No cambió de orden.
2. **¿Estaba medido sobre otra cosa?** Sí, y ahí está el error real: el 31 % es una fracción
   de **records**, y el título de D13 la presenta como fracción de **magnitud**. La fracción
   de magnitud es **70,7 %** hoy y era 75,0 % antes del cambio de régimen. El título subestima
   por más del doble lo que la cerca hace con el número que el operador lee.
3. **¿Cambió con el régimen?** Poco y en la dirección esperable: el #571, al quitar el piso
   VRP, agregó pasadas de magnitud chica, y eso bajó las dos fracciones (34,8 → 28,1 en
   conteo, 75,0 → 70,7 en magnitud). El mecanismo no se movió: sigue siendo MODIS, sigue
   siendo el `final_hotspot` que se va del cráter, y sigue sin que lo toquen los filtros de
   artefacto.
4. **¿Cuánto de lo apagado es señal que MIROVA confirmó?** En el régimen actual, **cero de
   411 records y cero MW**, con la advertencia de poder del punto 5. En el régimen anterior,
   15 records y 24,6 MW sobre 1.929 (**0,8 %**), todos Láscar MODIS con el cúmulo al cráter,
   y **ninguna noche perdida** porque las 15 ya estaban cubiertas.
5. **Lo que no cambia.** La segunda condición de la cerca (`pc.centroid_dist_km > inner`)
   sigue siendo un **no-op exacto**: 0 records en las dos ventanas. Eso sí se confirma tal
   como D13 lo escribió.

**Qué corregir en el catálogo** (sugerido, no aplicado acá): el **título** de D13, que dice
magnitud y mide records; la atribución del script, que apunta a un directorio donde la
medición no está; y la frase "el reparto por volcán es notablemente plano", que se sostenía
sobre un agrupado y no sobre el corte por sensor. La conclusión de fondo de S126 (la cerca
es ortogonal al artefacto y no es una palanca) **no** queda tocada por nada de esto: lo que
la cerca apaga sigue sin ser señal que MIROVA confirme.
