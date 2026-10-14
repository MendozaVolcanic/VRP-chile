# Pre-registro S151, tarea 1.4: la anomalía mayor (`vrp_max`) contra el cúmulo del cráter (`vent_anchored`)

> Estado: **borrador v1, SIN DESPACHAR.** Escrito el 2026-10-14 por el loop (tarea 1.4 de
> `tasks/LOOP_OBJETIVOS.md` §4, rama `loop/activo`). Falta: verificador con contexto limpio, sello de Nicolás
> (`sellar.py`), y para el brazo A2 un cambio de código con ciclo A45 que hoy no existe (§1.3).
> Todo número de este documento sale de un script de esta carpeta con su salida guardada:
> `sustrato.py` → `sustrato_salida.txt` y `.json`; `diff_perfiles.py` → `diff_perfiles_salida.txt`;
> `probar_evaluar.py` → `probar_evaluar_salida.txt`. Las reglas de §4 y §5 las implementa `evaluar.py`, con
> los parámetros congelados en `parametros.json`.

## 1. El fenómeno, el mecanismo y lo que el código hace hoy

### 1.1 El fenómeno

De noche, en el recuadro de 25 km alrededor de un volcán puede haber más de una fuente de calor: el cráter y,
por ejemplo, un incendio, un salar que devuelve de noche el calor del día o un campo geotermal. MIROVA informa
una sola fuente por pasada. Nicolás decidió el 2026-10-09 (`docs/AUDIT_S150.md` §8) que la réplica elija como
MIROVA: **la anomalía de mayor energía de la escena**. Nuestra réplica elige otra cosa: el cúmulo pegado al
cráter (`vent_anchored`, S38). Las dos reglas dan lo mismo cuando no hay calor lejano, o cuando el lejano es más
débil que el del cráter; divergen sólo en las pasadas con un cúmulo lejano **más fuerte** que el del cráter.

Lo que se sabe del lado de MIROVA, y lo que no:
- Su tabla trae **359 filas lejanas nocturnas** (FALSO_POSITIVO del consolidado, hora UTC bajo 12, del
  2026-03-01 al 2026-10-09), no 858: las otras 499 son de la tarde (`docs/audit_s150/meta/VERIFICADOR_DATOS.md`
  D2, `AUDITOR_F2_NUMEROS.md` H1). `sustrato.py` §1 las reproduce: **359** (V375 332, V750 17, MODIS 10).
- La etiqueta FALSO_POSITIVO y la clase NULO **las escribe el scraper** (`Mirova-v1/scraper.py` l. 144 a 154),
  por distancia contra su `limite_km`; MIROVA sólo publica la fila. No dicen que MIROVA las descarte.
- Que la tabla traiga una fila por pasada no prueba que esa fila sea la mayor: es compatible con otras reglas
  (SOSPECHA de F2, no medida). Este A/B tampoco lo prueba (§6).
- **75 de las 359 están a más de 25 km** de la referencia de MIROVA. Nuestro recuadro es un disco de 25 km y el
  de MIROVA un cuadrado de 51 km (D17): ningún brazo puede elegir esos objetos.

### 1.2 El mecanismo, consumidor por consumidor (A118)

El flag existe: `ENABLE_VENT_ANCHORED_CLUSTERING` (`pipeline/profile.py:440`, leído de la sección `paths:`; en
producción vale True, leído de `pipeline.profile`, A89). Con False, los tres procesadores le pasan
`strategy="vrp_max"` a `pipeline/clustering.py::cluster_hotspots`, que ordena los cúmulos por energía. Pero la
selección no es el último paso, y el flag **no llega a todos los que deciden qué ve el operador**:

| consumidor | dónde (2026-10-14) | ¿llega el flag? |
|---|---|---|
| selección del cúmulo contextual | `process_viirs.py:1518`, `process_viirs_mod.py:1066`, `process_modis.py:1111` | **sí** |
| selección del cúmulo del Test 1 | `process_viirs.py:1980`, `process_viirs_mod.py:1298`, `process_modis.py:1401` | sí, pero sólo ve el disco de 3 km del cráter: no hay lejano que elegir |
| fuente final (Regla D, primera rama de `resolve_test1_source_priority`, `pipeline/test1_integrated.py:175`) | `process_viirs.py:1770`, `process_viirs_mod.py:1180`, `process_modis.py:1294` | **no**: si el Test 1 tocó el cráter y el píxel más energético de la escena está lejos, la fuente vuelve al Test 1, justo el caso de la anomalía mayor |
| magnitud publicada (cúmulo del Test 1 recalculado) | `process_viirs.py:1919`, `process_viirs_mod.py:1244`, `process_modis.py:1367` | **no** en esos casos: el `primary_cluster` vuelve a ser el del cráter |
| posición y etiqueta (ancla honesta) | `pipeline/anchor.py:67` (rama `not (ctx_far and test1_summit_hit)`), llamada en `process_viirs.py:2091` | parcial: el cúmulo contextual es el de `vrp_max`, pero si el Test 1 tocó el cráter la posición vuelve al cráter |
| guard de coherencia de la etiqueta | `pipeline/store.py:480` | sí (deriva del cúmulo) |
| rescate del cúmulo | `pipeline/store.py:343` | no aplica (sólo actúa sobre píxeles a más de `radius_km` = 25 km) |
| tablero | `frontend/index.html:1063` y `:1067` (`mirovaEqVrp`) | sí, y convierte un cúmulo lejano en **silencio** (lejos del `inner_radius` vale 0) |
| distancias | `pc.centroid_dist_km` se mide desde el cráter (ancla de detección); `hotspot_dist_km` y `anomaly_pixels[].dist_km` desde el catálogo (`process_viirs.py:754`) | la Regla D decide con `hotspot_dist_km`, **del catálogo** (PCC: el cráter está a 7,3 km del catálogo) |

Consecuencia medida en el sustrato (§7): de las 245 pasadas del universo de 359 que hoy publicamos, **152
están protegidas por la Regla D** (el flag no las toca) y sólo 2 son alcanzables por el flag solo.

### 1.3 Prerrequisito del brazo A2 (cambio de código, NO implementado; ciclo A45)

La regla completa de MIROVA necesita que la Regla D y el ancla honesta cedan ante la anomalía mayor. Cambio
propuesto, para un PR aparte con tag `pre-s151-anomalia-mayor` y el sí de Nicolás:
1. Flag nuevo `enable_anomalia_mayor_total` en `paths:` (por defecto false), leído en `pipeline/profile.py`.
2. En los tres procesadores (A102: son tres copias), con el flag encendido y `vent_anchored` apagado: calcular
   la energía del cúmulo del Test 1 ANTES de decidir la fuente (hoy se calcula después, en el bloque que empieza en `process_viirs.py:1919`)
   y darle la fuente al Test 1 sólo si su energía es mayor o igual que la del cúmulo contextual
   ganador. Lo mismo para la rama del cúmulo rival débil.
3. En `resolve_honest_anchor`, con el flag encendido, no devolver `test1_roi` cuando ganó el cúmulo lejano.
4. Tests primero (TDD), uno por procesador, y un guard que pruebe que el flag llega a selección, fuente,
   magnitud, posición y etiqueta (A118), con frontera de palabra (A92).
5. Sólo el perfil de experimento `_s151_ab_vrp_max_total` lo enciende; `mirova_equivalent.yaml` no se toca.

## 2. Brazos (perfiles verificados leyendo `pipeline.profile`: `diff_perfiles_salida.txt`)

| brazo | perfil | diferencia contra `mirova_equivalent` | estado |
|---|---|---|---|
| A0 control | `_s146_ab_control` | ninguna (verificado) | existe |
| A1 flag solo | `_s151_ab_vrp_max` (este PR) | `ENABLE_VENT_ANCHORED_CLUSTERING` True a False, y nada más (verificado) | existe |
| A2 regla completa | `_s151_ab_vrp_max_total` | A1 más `enable_anomalia_mayor_total: true` | **no existe**: espera §1.3 |

Cada brazo escribe en su `data_subdir` (A47). Este PR agrega `ENABLE_VENT_ANCHORED_CLUSTERING` a la línea
`FLAGS_BRAZO` de `.github/workflows/reproc-s146-ab-sin-test1.yml`; sin eso K3 no se puede verificar.

## 3. Ventana, referencia y despacho

**Ventana: 2026-08-29 a 2026-10-08 (tramo T3), elegida con A119 y A104:**
- después de #535 (2026-08-28 23:00 UTC): un solo régimen de máscara de nube (A104);
- después del 2026-06-13: la positiva del OCR decide (geometría calibrada y distancia medida);
- después del 2026-04-01 y del 2026-04-09: la tasa por pasada de VIIRS es comparable y NOAA-21 está en la tabla;
- antes del 2026-10-09: las positivas **sólo OCR de Suomi NPP** pueden traer distancia y clase de otra pasada;
  **no deciden** (`comun.etiquetar`) y se informan aparte. En la ventana hay 5 protegidas así (Isluga y
  Tupungatito), las 5 con Regla D;
- contiene la erupción de Nevados de Chillán, que es donde están las alertas protegidas: deciden y se publican
  hoy **25** (V375 12, V750 10, MODIS 3; `sustrato_salida.txt` §7).

Por qué no los siete meses: el efecto esperado de A1 es de unas 5 pasadas (§7) y el costo crece con la
ventana. **Puerta:** si T3 da GANA EL CRITERIO, se repite en T2 (2026-06-13 a 2026-08-28) con el mismo
evaluador antes de cualquier recomendación; si da NO ADOPTAR o INERTE, no se extiende.

**Referencia:** se congela el día del despacho desde el remoto del dueño, como en la prueba de Chillán:
`python experiments/_s150_ndc/congelar_desde_remoto.py vrp_max 2026-08-29 2026-10-08` (escribe
`experiments/_s150_ndc/_congelado_vrp_max/` con manifiesto y sha). El evaluador le suma la unión histórica del
repo (`cargar_referencia_unificada`, tarea 0.1). Antes de evaluar, comprobar que la congelada no perdió filas de
la ventana contra el snapshot del repo (D1 de VERIFICADOR_DATOS: el consolidado remoto perdió 207 filas).

**Despacho propuesto** (requiere: este PR mergeado, porque el workflow corre desde `main`; verificador limpio;
sello; y para A2 el PR de §1.3). Dos corridas de media ventana (el A/B de S146 con 20 días es la forma
probada; 41 días en un job arriesga el tope de 300 minutos por paso):

```
gh workflow run reproc-s146-ab-sin-test1.yml --ref main -f preregistro_aprobado=si \
  -f start=2026-08-29 -f end=2026-09-18 \
  -f vols='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]' \
  -f brazos='["_s146_ab_control","_s151_ab_vrp_max","_s151_ab_vrp_max_total"]' -f control=_s146_ab_control
```
y la segunda con `start=2026-09-19 end=2026-10-08`. Sin A2, `brazos` lleva sólo los dos primeros.
- El workflow está en el grupo de concurrencia `s146-ab-sin-test1` y GitHub guarda **una sola corrida
  pendiente por grupo**: con la prueba de Chillán corriendo (run 38560317428), la primera media ventana queda
  en cola; la segunda se despacha **sólo cuando la primera ya esté corriendo**, o desplaza a la pendiente.
- Tope del loop: 2 A/B a la vez.
- Duración: no la estimo con un número; la referencia es el A/B de S146, misma forma.

**Recomendación del loop:** despachar una sola vez con A0, A1 y A2 después del PR de §1.3. A1 solo es barato
de preparar (ya está), pero el sustrato dice que su efecto es casi nulo; su valor es confirmar la lectura de
§1.2 (P1, P2), no decidir la regla.

## 4. Controles, antes de mirar ningún veredicto (`evaluar.py`, K1 a K4)

0. **Cobertura pareja por corrida** con `experiments/_s146_ab_sin_test1/contar_pasadas.py --control <A0>
   --brazo <A1> [--brazo <A2>]` y `experiments/_s143_evaluador/bajar_tramos.py --estricto` (A108). Si un brazo
   tiene menos pasadas, se repite ese job antes de evaluar.
1. **K1** el brazo y el control tienen exactamente las mismas pasadas (volcán, sensor, minuto). Si no:
   INDECIDIBLE POR INSTRUMENTO.
2. **K2 determinismo:** en las pasadas donde el control tiene un solo cúmulo y no disparó el Test 1, el brazo
   tiene que ser idéntico (cúmulo, etiqueta, publicación). Una diferencia: INDECIDIBLE POR INSTRUMENTO (algo
   distinto del flag cambió).
3. **K3 cableado:** la primera línea `FLAGS_BRAZO` del log de cada job (los 11 volcanes) dice
   `ENABLE_VENT_ANCHORED_CLUSTERING` True en A0 y False en A1 y A2. Si falta la clave o el valor no calza:
   INDECIDIBLE POR INSTRUMENTO.
4. **K4 el mecanismo actúa (A116):** al menos una pasada cuyo cúmulo pasa de cerca del cráter (o de no tener
   cúmulo) a lejos. Si es cero: INDECIDIBLE: EL MECANISMO NO ACTUÓ, nunca INERTE.

`probar_evaluar.py` prueba que cada control puede encenderse (salida guardada, los cinco dan lo esperado): el
control contra sí mismo da K4 = 0 e INDECIDIBLE; un brazo al que le falta una pasada da K1 en rojo; uno que
cambia una pasada de un cúmulo da K2 en rojo; uno que silencia la candidata de P5 da veto.

## 5. Reglas y predicciones (`evaluar.py`, mismo nombre en el código)

Todo se mide **por sensor**, en las dos direcciones (lo que se pierde y lo que se gana), sobre las pasadas que
**deciden** (A119). "Publica" y "magnitud" son el predicado del tablero ejecutado con node (A97).

- **R1 veto, lectura A:** una positiva con alerta protegida (alerta del scraper con VRP de 1 MW o más,
  `scripts/clase_mirova.py`) que el control publica y el brazo no. Una sola: NO ADOPTAR.
- **R1 veto, lectura B** (D-4 pendiente, issue #782): R1 A más las pasadas `far_ref` protegidas (MIROVA vio
  1 MW o más lejos) donde el control tenía **el mismo objeto** y el brazo lo pierde. "Mismo objeto" = cúmulo
  publicado fuera del `inner_radius` y con radio a 2 km o menos del de MIROVA (diferencia de radios, cota A93;
  radio nuestro desde el cráter). No se usa el predicado del tablero para B porque el tablero calla todo lo
  lejano: B con el tablero castigaría al brazo justo cuando elige el objeto de MIROVA.
- **R2 suma de errores (Muy Bajo):** E = positivas bajo 1 MW sin publicar + negativos limpios publicados.
  ΔE = E(brazo) menos E(control), por sensor. Si algún ΔE es positivo: NO ADOPTAR. Todos cero: INERTE. Si baja:
  GANA EL CRITERIO, salvo que la baja salga entera de **ganancias por accidente** (negativo limpio que el brazo
  calla porque eligió un cúmulo lejano: MIROVA no vio nada en esa pasada, ni lejos, así que callar el cráter
  detrás de otro objeto que MIROVA tampoco vio son dos errores que se cancelan, A100): entonces GANA SOLO POR
  ACCIDENTE, que no cuenta como evidencia a favor.
- **R3 magnitud:** positivas publicadas en los dos brazos con magnitud distinta: cuántas quedan más cerca de
  MIROVA (en log) y cuántas más lejos; mediana de la razón por brazo. Se informa; no veta.
- **R4 objeto lejano:** `far_ref` donde el cúmulo publicado es el mismo objeto que MIROVA (definición de R1 B),
  control contra brazo. Es lo único que mide la fidelidad que la regla promete comprar; se informa.
- **Orden del veredicto:** instrumento (K1 a K3), mecanismo (K4), veto, suma de errores.

Predicciones (números de `sustrato_salida.txt` §7, sobre los records de producción de T3; con margen porque el
control se reprocesa con el código de hoy):

| id | brazo | predicción | qué significa si falla |
|---|---|---|---|
| P1 | A1 | silencia a lo más 35 pasadas en V375 y 3 en V750 (sustrato: seguro 4, seguro más estimado 5; techo 176 y 1) | el flag llega a más de lo que dice §1.2: la Regla D no es el único bloqueo |
| P2 | A1 | cero cambios en pasadas donde el control disparó el Test 1 y tiene el píxel más energético fuera del `inner_radius` | la lectura A118 de §1.2 es falsa |
| P3 | A1 | cero vetos en V375 y V750, y \|ΔE\| de 5 o menos en esos sensores (INERTE en la práctica) | el sustrato subestimó el efecto; MODIS sin predicción (C1 falla en MODIS, sólo hay cotas: techo 93) |
| P4 | A2 | silencia al menos 50 pasadas en V375 (sustrato: 283 publicadas con Regla D) y R4 sube a 25 o más (producción 5 de 70; con lejano dominante 54 de 70) | el cambio de código no llegó, o nuestros cúmulos lejanos no son los objetos de MIROVA |
| P5 | A2 | pierde la alerta protegida de Láscar, NOAA-21, 2026-10-01 05:18 (MIROVA 1,2 MW en el cráter; nuestro cúmulo del cráter 0,138 MW; nuestro píxel más energético a 19,7 km) y por lo tanto VETO bajo A | si no la pierde, nuestro cúmulo lejano pesa menos que el del cráter aunque su píxel máximo pese más |

## 6. Lo que este A/B no puede decir

- **Si MIROVA de verdad elige la mayor.** Una fila por pasada es compatible con otras reglas, y la distancia de
  MIROVA no trae acimut: R4 descarta objetos distintos, no prueba que sean el mismo (A93, A107). Lo que sí da
  el sustrato: en las `far_ref` que publicamos, nuestro píxel o cúmulo más energético está lejos en 156 de 247
  (63 %), contra 7,6 % en los negativos limpios (razón 8,3; nulo barajado 2,95, p95 3,40), y en 134 de esas 156
  el radio calza a 2 km. Y en las positivas, donde MIROVA informó el cráter, nuestro más energético está lejos
  en 191 de 1.677 (11 %): eso es lo que A2 arriesga.
- **Los 75 objetos de MIROVA a más de 25 km**: fuera de nuestro disco en todos los brazos.
- **El valor de mostrar lo lejano.** El tablero calla todo cúmulo fuera del `inner_radius`, así que, bajo la
  lectura A, la regla de la anomalía mayor sólo puede bajar la suma de errores callando al cráter. Si la réplica
  debería mostrar las detecciones lejanas como lo hace la tabla de MIROVA es una decisión de display de Nicolás,
  fuera de este A/B.
- **Otros tramos.** Una ventana de 41 días dominada por la erupción de Chillán; la puerta de §3 lo cubre sólo si
  T3 gana.
- **MODIS y VIIRS 750 en el sustrato:** la reconstrucción de cúmulos desde los píxeles guardados no reproduce
  el `primary_cluster` (C1: 0,26 y 0,72 contra 0,95 en V375), así que para esos sensores sólo hay cotas.
- **Las positivas sólo OCR** antes del 2026-06-13 y las de Suomi NPP antes del 2026-10-09: no deciden.
- **La magnitud del objeto lejano** contra la de MIROVA: R3 sólo mira las positivas del cráter.

## 7. Sustrato (`sustrato.py`, datos en disco al 2026-10-14; ver la salida para cada cifra)

Las 359 lejanas nocturnas, contra nuestra pasada pareada a ±2 min: sin record nuestro 0; no publicamos 114
(28 con cúmulo lejano, 86 sin cúmulo con energía); publicamos 245: **Regla D 152**, sin píxel lejano 53, no
observable 35 (el record sólo guarda los píxeles del Test 1), lejano más débil 3, seguro 1, estimado 1.

Clases para el brazo A1 (pasada que hoy publica): **seguro**, el píxel lejano más energético pesa más que la
suma del cráter; **estimado**, agrupando los píxeles guardados el cúmulo mayor queda lejos (sólo V375, único
sensor que pasa C1); **posible**, la suma lejana pesa más que el píxel máximo del cráter (techo); **Regla D**,
el flag no llega; **no observable**.

Controles del sustrato: **C1** reproducción del `primary_cluster` con la regla reconstruida: V375 0,952 (pasa
el 0,90), V750 0,721 y MODIS 0,260 (fallan: sólo cotas). La versión 1 lo juzgaba en total y fallaba con 0,667;
se cambió a por sensor después de ver la salida, y queda dicho. **C2** enriquecimiento (arriba, §6): pasa
contra su nulo medido; la versión 1 usaba sólo la clase "seguro" y "pasaba" con 1 de 247 contra 4 de 4.288, sin
poder, y se cambió después de ver la salida. **C3** sintético y **C4** identidad del predicado: pasan.

En la ventana T3: A1 podría silenciar 4 (seguro), 5 (más estimado), techo 270 (V375 176, MODIS 93, V750 1);
sólo A2 alcanza 320 (V375 283, MODIS 22, V750 15). En todo marzo a octubre, el techo de A1 en el criterio es
de 0 vetos seguros y casi todo "posible" en MODIS, y la Regla D protege 17 positivas protegidas (7 que deciden).

## 8. Decisiones que este pre-registro deja para Nicolás

1. El cambio de código de §1.3 (A45): sin él, el A/B mide el flag y no la regla que decidiste.
2. D-4 (issue #782): lectura A o B; el evaluador da las dos.
3. Si una baja de la suma de errores que viene sólo de callar el cráter detrás de un cúmulo lejano que MIROVA
   no vio cuenta como ganancia (el evaluador la marca GANA SOLO POR ACCIDENTE).
4. Si la réplica debería mostrar las detecciones lejanas, como la tabla de MIROVA (display, fuera de este A/B).
