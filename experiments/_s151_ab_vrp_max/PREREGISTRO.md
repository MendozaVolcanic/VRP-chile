# Pre-registro S151, tarea 1.4: la anomalía mayor (`vrp_max`) contra el cúmulo del cráter (`vent_anchored`)

> Estado: **borrador v2, SIN DESPACHAR.** v1 escrita el 2026-10-14 por el loop (tarea 1.4 de
> `tasks/LOOP_OBJETIVOS.md` §4); v2 el mismo día con los arreglos del verificador con contexto limpio de #794
> (§9). Falta: sello de Nicolás (`sellar.py`) y, para el brazo A2, un cambio de código con ciclo A45 que hoy no
> existe (§1.3). Todo número de este documento sale de un script de esta carpeta con su salida guardada:
> `sustrato.py` → `sustrato_salida.txt` y `.json`; `diff_perfiles.py` → `diff_perfiles_salida.txt`;
> `probar_evaluar.py` → `probar_evaluar_salida.txt`. Las reglas de §4 y §5 las implementa `evaluar.py`, con
> los parámetros congelados en `parametros.json`.

## 1. El fenómeno, el mecanismo y lo que el código hace hoy

### 1.1 El fenómeno

De noche, en el recuadro de un volcán puede haber más de una fuente de calor: el cráter y, por ejemplo, un
incendio, un salar que devuelve de noche el calor del día o un campo geotermal. Nuestro recuadro es una **caja
de 50 × 50 km centrada en el catálogo** (`roi_mask_bbox`: `process_viirs.py:780`, `process_modis.py:538`,
`process_viirs_mod.py:516`), que llega a unos 35 km en las esquinas. MIROVA informa una sola fuente por pasada.
Nicolás decidió el 2026-10-09 (`docs/AUDIT_S150.md` §8) que la réplica elija como MIROVA: **la anomalía de mayor
energía de la escena**. Nuestra réplica elige otra cosa: el cúmulo pegado al cráter (`vent_anchored`, S38).

Las dos reglas divergen de **dos maneras** (la v1 decía que sin calor lejano daban lo mismo, y era falso):
- **(a) lejano más fuerte que el cráter.** `vrp_max` elige el lejano y el tablero, que calla todo lo que queda
  fuera del `inner_radius`, deja la pasada en silencio. Cambia la **publicación**.
- **(b) varios cúmulos cerca del cráter**, incluidos los del Test 1 dentro del disco de 3 km: `vent_anchored`
  toma el más cercano y `vrp_max` el más energético. Cambia la **magnitud** publicada, no la publicación. Ejemplo
  verificado a mano: Chaitén, Suomi NPP, 2026-09-16 05:42, cúmulo publicado 0,399 MW a 0,84 km; el más energético
  del disco, 1,026 MW a 1,44 km (sustrato, reconstrucción desde los píxeles guardados).

Lo que se sabe del lado de MIROVA, y lo que no:
- Su tabla trae **359 filas lejanas nocturnas** (FALSO_POSITIVO del consolidado, hora UTC bajo 12, del
  2026-03-01 al 2026-10-09), no 858: las otras 499 son de la tarde (`docs/audit_s150/meta/VERIFICADOR_DATOS.md`
  D2, `AUDITOR_F2_NUMEROS.md` H1). `sustrato.py` §1 las reproduce: **359** (V375 332, V750 17, MODIS 10).
- La etiqueta FALSO_POSITIVO y la clase NULO **las escribe el scraper** (`Mirova-v1/scraper.py` l. 144 a 154),
  por distancia contra su `limite_km`; MIROVA sólo publica la fila. No dicen que MIROVA las descarte.
- Que la tabla traiga una fila por pasada no prueba que esa fila sea la mayor: es compatible con otras reglas
  (SOSPECHA de F2, no medida). Este A/B tampoco lo prueba (§6).
- **75 de las 359 están a más de 25 km** de la referencia de MIROVA y ninguna a más de 35,4 km. Caben en
  nuestra caja sólo si caen hacia una esquina; la distancia de MIROVA no trae acimut, así que no se sabe cuáles.

### 1.2 El mecanismo, consumidor por consumidor (A118)

El flag existe: `ENABLE_VENT_ANCHORED_CLUSTERING` (`pipeline/profile.py:440`, leído de la sección `paths:`; en
producción vale True, leído de `pipeline.profile`, A89). Con False, los tres procesadores le pasan
`strategy="vrp_max"` a `pipeline/clustering.py::cluster_hotspots`, que ordena los cúmulos por energía. Pero la
selección no es el último paso, y el flag **no llega a todos los que deciden qué ve el operador**:

| consumidor | dónde (2026-10-14) | ¿llega el flag? |
|---|---|---|
| selección del cúmulo contextual | `process_viirs.py:1518`, `process_viirs_mod.py:1066`, `process_modis.py:1111` | **sí** |
| selección del cúmulo del Test 1 | `process_viirs.py:1980`, `process_viirs_mod.py:1298`, `process_modis.py:1401` | **sí**, dentro del disco de 3 km: cambia el más cercano por el más energético (divergencia (b), magnitud) |
| fuente final, Regla D primera rama (`pipeline/test1_integrated.py:175`; en V750 y MODIS la regla está escrita en línea) | `process_viirs.py:1770`, `process_viirs_mod.py:1180`, `process_modis.py:1294` | **no**: si el Test 1 tocó el cráter y el píxel más energético de la escena está lejos, la fuente vuelve al Test 1, justo el caso (a) |
| fuente final, Regla D tercera rama, rival débil (`pipeline/test1_integrated.py:198`; sólo V375, encendida en producción) | `process_viirs.py:1770` | **sí**: lee `primary_cluster.vrp_mw`, que con `vrp_max` es el del cúmulo más energético, así que el rival deja de ser débil más seguido y el Test 1 gana menos |
| magnitud publicada (cúmulo del Test 1 recalculado) | `process_viirs.py:1919`, `process_viirs_mod.py:1244`, `process_modis.py:1367` | **no** en los casos de la primera rama: el `primary_cluster` vuelve a ser el del cráter |
| posición y etiqueta (ancla honesta, `pipeline/anchor.py:67`, rama `not (ctx_far and test1_summit_hit)`) | `process_viirs.py:2091`, `process_viirs_mod.py:1379`, `process_modis.py:1484` | parcial: el cúmulo contextual es el de `vrp_max`, pero si el Test 1 tocó el cráter la posición vuelve al cráter |
| guard de coherencia de la etiqueta | `pipeline/store.py:480` | sí (deriva del cúmulo) |
| filtro por píxel y rescate | `pipeline/store.py:320` (`_filter_pixels_by_distance`) y `:343` | el filtro mueve los píxeles a más de `radius_km` (25 km) **del catálogo** a `discarded_anomaly_pixels` y recalcula `hotspot_dist_km` DESPUÉS de que la Regla D decidió con el de antes; el rescate no aplica |
| tablero | `frontend/index.html:1063` y `:1067` (`mirovaEqVrp`) | sí, y convierte un cúmulo lejano en **silencio** (lejos del `inner_radius` vale 0) |
| distancias | `pc.centroid_dist_km` se mide desde el cráter (ancla de detección); `hotspot_dist_km` y `anomaly_pixels[].dist_km` desde el catálogo (`process_viirs.py:754`) | la Regla D decide con la distancia **del catálogo** (PCC: el cráter está a 7,3 km del catálogo) |

Consecuencia medida en el sustrato (§7): de las 245 pasadas del universo de 359 que hoy publicamos, **152
están en la Regla D** (el flag no las vuelve lejanas) y sólo 3 se vuelven lejanas con el flag solo. En la
ventana T3 el flag sí cambia, cercano por cercano, la elección en 24 pasadas V375 de Regla D y en 216 fuera de
ella (§7).

### 1.3 Prerrequisito del brazo A2 (cambio de código, NO implementado; ciclo A45)

La regla completa de MIROVA necesita que la Regla D y el ancla honesta cedan ante la anomalía mayor. Cambio
propuesto, para un PR aparte con tag `pre-s151-anomalia-mayor` y el sí de Nicolás:
1. Flag nuevo `enable_anomalia_mayor_total` en `paths:` (por defecto false), leído en `pipeline/profile.py`.
2. En los tres procesadores (A102: son tres copias), con el flag encendido y `vent_anchored` apagado: calcular
   la energía del cúmulo del Test 1 ANTES de decidir la fuente (hoy se calcula después, en el bloque que
   empieza en `process_viirs.py:1919`) y darle la fuente al Test 1 sólo si su energía es mayor o igual que la
   del cúmulo contextual ganador. Lo mismo para la rama del cúmulo rival débil (sólo V375).
3. En `resolve_honest_anchor`, con el flag encendido, no devolver `test1_roi` cuando ganó el cúmulo lejano.
4. La Regla D mide con `hotspot_dist_km` del catálogo; con el flag encendido deja de decidir, pero el PR debe
   decir si se mide desde el cráter (AUDITOR_F1).
5. Tests primero (TDD), uno por procesador, y un guard que pruebe que el flag llega a selección, fuente,
   magnitud, posición y etiqueta (A118), con frontera de palabra (A92).
6. Sólo el perfil de experimento `_s151_ab_vrp_max_total` lo enciende; `mirova_equivalent.yaml` no se toca.

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
  **no deciden** (`comun.etiquetar`) y `evaluar.py` las informa aparte (`protegidas_que_no_deciden_calladas`).
  En la ventana hay 5 protegidas así (Isluga y Tupungatito);
- contiene la erupción de Nevados de Chillán, que es donde están las alertas protegidas: deciden y se publican
  hoy **25** (V375 12, V750 10, MODIS 3; `sustrato_salida.txt` §7).

Por qué no los siete meses: el efecto esperado de A1 sobre la publicación es de unas 5 pasadas (§7) y el costo
crece con la ventana. **Puerta:** si T3 da GANA EL CRITERIO, se repite en T2 (2026-06-13 a 2026-08-28) con el
mismo evaluador antes de cualquier recomendación; si da otra cosa, no se extiende.

**Referencia:** se congela el día del despacho desde el remoto del dueño, como en la prueba de Chillán:
`python experiments/_s150_ndc/congelar_desde_remoto.py vrp_max 2026-08-29 2026-10-08` (escribe
`experiments/_s150_ndc/_congelado_vrp_max/` con manifiesto y sha). El evaluador le suma la unión histórica del
repo (`cargar_referencia_unificada`, tarea 0.1). Antes de evaluar, comprobar que la congelada no perdió filas de
la ventana contra el snapshot del repo (D1 de VERIFICADOR_DATOS: el consolidado remoto perdió 207 filas).

**Despacho propuesto** (requiere: este PR mergeado, porque el workflow corre desde `main`; sello; y para A2 el
PR de §1.3). Dos corridas de media ventana (el A/B de S146 con 20 días es la forma probada; 41 días en un job
arriesga el tope de 300 minutos por paso):

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

**Evaluación de las dos corridas (fusión):** cada corrida deja en su rama `s146-ab/<run_id>` la carpeta
`experiments/_s146_ab_sin_test1/salidas/<run_id>/` con `<perfil>/<volcán>.json` y `logs/<perfil>_<volcán>.log`.
```
python experiments/_s151_ab_vrp_max/evaluar.py --corrida <salidas/run1> --corrida <salidas/run2> \
  --cons experiments/_s150_ndc/_congelado_vrp_max/registro_vrp_consolidado.csv \
  --ocr experiments/_s150_ndc/_congelado_vrp_max/registro_vrp_ocr.csv --brazo A1=_s151_ab_vrp_max [--brazo A2=_s151_ab_vrp_max_total]
```
El evaluador concatena los records de cada perfil de las dos corridas en memoria; una pasada repetida entre
corridas es falla de K1. Un relanzamiento parcial (A108) se pasa como una corrida más sólo si su volcán no está
en la original; si está, se reemplazan el JSON y el log de ese volcán en la carpeta original.

**Recomendación del loop:** despachar una sola vez con A0, A1 y A2 después del PR de §1.3. A1 solo es barato
de preparar (ya está), pero el sustrato dice que su efecto sobre la publicación es casi nulo; su valor es
confirmar la lectura de §1.2 (P1, P2) y medir la divergencia (b), no decidir la regla.

## 4. Controles, antes de mirar ningún veredicto (`evaluar.py`, K1 a K4)

0. **Cobertura pareja por corrida** con `experiments/_s146_ab_sin_test1/contar_pasadas.py --control <A0>
   --brazo <A1> [--brazo <A2>]` y `experiments/_s143_evaluador/bajar_tramos.py --estricto` (A108). Si un brazo
   tiene menos pasadas, se repite ese job antes de evaluar.
1. **K1** el brazo y el control tienen exactamente las mismas pasadas (volcán, sensor, minuto), sin repetidas
   entre corridas. Si no: INDECIDIBLE POR INSTRUMENTO.
2. **K2 determinismo:** en las pasadas donde el control tiene un solo cúmulo y no disparó el Test 1, el brazo
   tiene que ser idéntico (cúmulo, etiqueta, publicación). Una diferencia: INDECIDIBLE POR INSTRUMENTO (algo
   distinto del flag cambió).
3. **K3 cableado, por corrida y volcán:** cada (corrida, volcán) con records de un perfil tiene que traer su log,
   cuya primera línea `FLAGS_BRAZO` dice `ENABLE_VENT_ANCHORED_CLUSTERING` True en A0 y False en A1 y A2. Si
   falta un log, la clave o el valor no calza: INDECIDIBLE POR INSTRUMENTO. (La v1 exigía 11 logs por perfil y
   con dos corridas, 22, habría dado INDECIDIBLE siempre.)
4. **K4 el mecanismo actúa (A116):** al menos una pasada cuyo cúmulo pasa de cerca del cráter (o de no tener
   cúmulo) a lejos. Si es cero: INDECIDIBLE: EL MECANISMO NO ACTUÓ, nunca INERTE.

`probar_evaluar.py` prueba que cada salida puede ocurrir (doce casos, salida guardada, todos dan lo esperado): el
control contra sí mismo da INDECIDIBLE: EL MECANISMO NO ACTUÓ; una pasada de menos o una corrida repetida dan
K1 en rojo; una pasada de un cúmulo cambiada da K2 en rojo; dos corridas en carpetas temporales con la forma de
`salidas/<run_id>` dan K3 en verde con los logs correctos y en rojo con un flag equivocado o un log ausente; y
salen INERTE, GANA EL CRITERIO, GANA SOLO POR ACCIDENTE, NO ADOPTAR por veto y NO ADOPTAR por suma.

## 5. Reglas y predicciones (`evaluar.py`, mismo nombre en el código)

Todo se mide **por sensor**, en las dos direcciones (lo que se pierde y lo que se gana), sobre las pasadas que
**deciden** (A119). "Publica" y "magnitud" son el predicado del tablero ejecutado con node (A97).

- **R1 veto, lectura A:** una positiva con alerta protegida (alerta del scraper con VRP de 1 MW o más,
  `scripts/clase_mirova.py`) que el control publica y el brazo no. Una sola: NO ADOPTAR. Las protegidas que no
  deciden y el brazo calla se listan aparte y no vetan.
- **R1 veto, lectura B** (D-4 pendiente, issue #782): R1 A más las pasadas `far_ref` protegidas (MIROVA vio
  1 MW o más lejos) donde el control tenía **el mismo objeto** y el brazo lo pierde. "Mismo objeto" = cúmulo
  publicado fuera del `inner_radius` y con radio a 2 km o menos del de MIROVA (diferencia de radios, cota A93;
  radio nuestro desde el cráter). No se usa el predicado del tablero para B porque el tablero calla todo lo
  lejano: B con el tablero castigaría al brazo justo cuando elige el objeto de MIROVA.
- **R2 suma de errores (Muy Bajo):** E = positivas bajo 1 MW sin publicar + negativos limpios publicados.
  ΔE = E(brazo) menos E(control), por sensor. Si algún ΔE es positivo: NO ADOPTAR. Si todos son cero: INERTE
  sólo si además no cambia ninguna publicación (0 silenciadas y 0 nuevas); si cambian publicaciones que el
  criterio no cuenta (`far_ref`, `sin_info`, positivas que no deciden), NEUTRO EN EL CRITERIO. Si baja: GANA EL
  CRITERIO, salvo que la baja salga entera de **ganancias por accidente** (negativo limpio que el brazo calla
  porque eligió un cúmulo lejano: MIROVA no vio nada en esa pasada, ni lejos, así que callar el cráter detrás de
  otro objeto que MIROVA tampoco vio son dos errores que se cancelan, A100): entonces GANA SOLO POR ACCIDENTE, que
  no cuenta como evidencia a favor.
- **R3 magnitud:** positivas publicadas en los dos brazos con magnitud distinta: cuántas quedan más cerca de
  MIROVA (en log) y cuántas más lejos; mediana de la razón por brazo. Se informa; no veta. Aparte, por sensor:
  cuántas pasadas cambian el cúmulo publicado **cercano por cercano** (divergencia (b)) y cuántas de ellas son de
  Regla D.
- **R4 objeto lejano:** `far_ref` donde el cúmulo publicado es el mismo objeto que MIROVA (definición de R1 B),
  control contra brazo. Es lo único que mide la fidelidad que la regla promete comprar; se informa.
- **Orden del veredicto:** instrumento (K1 a K3), mecanismo (K4), veto, suma de errores.

Predicciones (números de `sustrato_salida.txt` §7, sobre los records de producción de T3; con margen porque el
control se reprocesa con el código de hoy):

| id | brazo | predicción | qué significa si falla |
|---|---|---|---|
| P1 | A1 | silencia a lo más 35 pasadas en V375 y 3 en V750 (sustrato: seguro 4, seguro más estimado 5; techo 179 y 2) | el flag llega a más de lo que dice §1.2, o el sustrato no vio la escena entera: el "techo" NO es una cota exacta, porque el tope de 100 píxeles se aplica antes del filtro de `store.py` y lo que quedó fuera no se guardó |
| P2 | A1 | ninguna pasada de Regla D (Test 1 en el cráter y píxel más energético de la escena, antes del filtro de `store.py`, fuera del `inner_radius`) pasa de cerca a lejos o cambia de publicación. Los cambios cercano por cercano en esas pasadas (sustrato: 24 en V375) NO cuentan | la lectura A118 de §1.2 es falsa |
| P3 | A1 | cero vetos en V375 y V750, y \|ΔE\| de 5 o menos en esos sensores | el sustrato subestimó el efecto; MODIS sin predicción (C1 falla en MODIS, sólo hay cotas: techo 93) |
| P4 | A2 | silencia al menos 50 pasadas en V375 (sustrato: 283 publicadas con Regla D) y R4 sube a 25 o más (producción 5 de 70; con lejano dominante 54 de 70) | el cambio de código no llegó, o nuestros cúmulos lejanos no son los objetos de MIROVA |
| P5 | A2 | pierde la alerta protegida de Láscar, NOAA-21, 2026-10-01 05:18 (MIROVA 1,2 MW en el cráter; nuestro cúmulo del cráter 0,138 MW; nuestro píxel más energético a 19,7 km) y por lo tanto VETO bajo A | si no la pierde, nuestro cúmulo lejano pesa menos que el del cráter aunque su píxel máximo pese más |

## 6. Lo que este A/B no puede decir

- **Si MIROVA de verdad elige la mayor.** Una fila por pasada es compatible con otras reglas, y la distancia de
  MIROVA no trae acimut: R4 descarta objetos distintos, no prueba que sean el mismo (A93, A107). Lo que sí da
  el sustrato: en las `far_ref` que publicamos, nuestro píxel o cúmulo más energético está lejos en 157 de 247
  (64 %), contra 7,6 % en los negativos limpios (razón 8,3; nulo barajado mediana 2,93, p95 3,38), y en 134 de
  esas 157 el radio calza a 2 km. **Pero 154 de las 157 son de Regla D**: C2 respalda sobre todo la premisa del
  brazo A2 (que nuestro objeto lejano es el de MIROVA), no la de A1. Y en las positivas, donde MIROVA informó el
  cráter, nuestro más energético está lejos en 192 de 1.677 (11 %): eso es lo que A2 arriesga.
- **Los 75 objetos de MIROVA a más de 25 km**: alcanzables sólo si caen hacia una esquina de la caja; sin acimut
  no se sabe cuántos. En T3 hay 13 records cuyo cúmulo publicado ya está entre 25 y 36 km del cráter.
- **El valor de mostrar lo lejano.** El tablero calla todo cúmulo fuera del `inner_radius`, así que, bajo la
  lectura A, la regla de la anomalía mayor sólo puede bajar la suma de errores callando al cráter. Si la réplica
  debería mostrar las detecciones lejanas como lo hace la tabla de MIROVA es una decisión de display de Nicolás,
  fuera de este A/B.
- **Otros tramos.** Una ventana de 41 días dominada por la erupción de Chillán; la puerta de §3 lo cubre sólo si
  T3 gana.
- **MODIS y VIIRS 750 en el sustrato:** la reconstrucción de cúmulos desde los píxeles guardados no reproduce
  el `primary_cluster` (C1: 0,40 y 0,72 contra 0,95 en V375), así que para esos sensores sólo hay cotas, y la
  divergencia (b) sólo se estima en V375.
- **Las positivas sólo OCR** antes del 2026-06-13 y las de Suomi NPP antes del 2026-10-09: no deciden.
- **La magnitud del objeto lejano** contra la de MIROVA: R3 sólo mira las positivas del cráter.

## 7. Sustrato (`sustrato.py`, datos en disco al 2026-10-14; ver la salida para cada cifra)

La escena se arma con `anomaly_pixels` más `discarded_anomaly_pixels` (los que `store.py` sacó por estar a más
de 25 km del catálogo; en T3, 972 records los tienen), y la Regla D se evalúa con el píxel más energético de esa
escena completa, que es el que vio el procesador.

Las 359 lejanas nocturnas, contra nuestra pasada pareada a ±2 min: sin record nuestro 0; no publicamos 114
(28 con cúmulo lejano, 86 sin cúmulo con energía); publicamos 245: **Regla D 152**, sin píxel lejano 52, no
observable 33 (el record sólo guarda los píxeles del Test 1, o llegó al tope de 100), lejano más débil 5,
seguro 2, estimado 1.

Clases para el brazo A1 (pasada que hoy publica): **seguro**, el píxel lejano más energético pesa más que la
suma del cráter; **estimado**, agrupando los píxeles el cúmulo mayor queda lejos (sólo V375, único sensor que
pasa C1); **posible**, la suma lejana pesa más que el píxel máximo del cráter; **Regla D**, el flag no la vuelve
lejana; **no observable**. Y, cruzado, **cercano por cercano** (divergencia (b)).

Controles del sustrato: **C1** reproducción del `primary_cluster` con la regla reconstruida: V375 0,953 (pasa
el 0,90), V750 0,724 y MODIS 0,400 (fallan: sólo cotas). La v1 lo juzgaba en total y fallaba; se cambió a por
sensor después de ver la salida, y queda dicho. **C2** enriquecimiento (§6): pasa contra su nulo medido; la v1
usaba sólo la clase "seguro" y "pasaba" con 1 de 247 contra 4 de 4.288, sin poder, y se cambió después de ver la
salida. **C3** sintético (incluye píxeles de esquina y el cambio cercano por cercano) y **C4** identidad del
predicado: pasan.

En la ventana T3: A1 podría silenciar 4 (seguro), 5 (más estimado), techo 274 (V375 179, MODIS 93, V750 2);
sólo A2 alcanza 320 (V375 283, MODIS 22, V750 15). **Cercano por cercano en V375** (reconstrucción): de las 283
publicadas de Regla D, 39 tienen 2 o más cúmulos y en 24 cambia la elección; de las 1.453 fuera de la Regla D,
377 tienen 2 o más y en 216 cambia. El verificador de #794 midió por su lado 42, 24 y 217; la diferencia de 3 y
1 viene de agrupar por cercanía y no por la grilla. En todo marzo a octubre, el techo de A1 en el criterio es de
0 vetos seguros y casi todo "posible" en MODIS, y la Regla D protege 17 positivas protegidas (7 que deciden).

## 8. Decisiones que este pre-registro deja para Nicolás

1. El cambio de código de §1.3 (A45): sin él, el A/B mide el flag y no la regla que decidiste.
2. D-4 (issue #782): lectura A o B; el evaluador da las dos.
3. Si una baja de la suma de errores que viene sólo de callar el cráter detrás de un cúmulo lejano que MIROVA
   no vio cuenta como ganancia (el evaluador la marca GANA SOLO POR ACCIDENTE).
4. Si la réplica debería mostrar las detecciones lejanas, como la tabla de MIROVA (display, fuera de este A/B).

## 9. Qué cambió de la v1 a la v2 (verificador con contexto limpio de #794: SELLABLE CON ARREGLOS)

1. **P2 fallaba por construcción**: el flag también elige entre cúmulos del Test 1 dentro del disco de 3 km.
   P2 se redefinió (cerca contra lejos o publicación) y el cambio cercano por cercano se informa aparte. La
   frase "sin calor lejano dan lo mismo" era falsa y salió.
2. **"Disco de 25 km" era falso**: el recuadro es una caja de 50 × 50 km. El sustrato ahora suma los píxeles
   que `store.py` sacó de la lista, evalúa la Regla D con el píxel de antes del filtro, y deja de llamar cota a
   su techo.
3. **K3** exigía 11 logs por perfil y con dos corridas habría dado siempre INDECIDIBLE: ahora es por corrida y
   volcán, y el evaluador recibe varias corridas (`--corrida`) y las fusiona, con prueba.
4. `probar_evaluar.py` pasó de 5 a 12 casos: INERTE, GANA EL CRITERIO, NO ADOPTAR por suma y K3 con logs.
5. Tabla §1.2: la tercera rama de la Regla D (rival débil) sí consume el flag en V375; el ancla también se llama
   en `process_viirs_mod.py:1379` y `process_modis.py:1484`.
6. Las protegidas que no deciden se listan aparte en `evaluar.py`; INERTE exige 0 silenciadas y 0 nuevas (si
   no, NEUTRO EN EL CRITERIO); la docstring de `sustrato.py` describe C2 v2 y su alcance.
