# S163 H3: ¿el tablero muestra hoy records del detector anterior a K?

**Veredicto: REFUTADO para el tablero de hoy.** En `origin/main` (`0b233221f`, 2026-10-26 02:27 UTC) y en lo que
GitHub Pages sirve hoy no queda ningún record del detector anterior a K entre los que el tablero publica: 0 de 9.538
publicados, 0 de 72.438 records en total, en los 11 Tier A y los tres sensores. El caso de ejemplo (Láscar 2026-08-22
05:06, Suomi NPP 375 m) hoy es un record de K, `far`, cúmulo de 0,511 MW a 8,23 km, y el tablero **no lo publica**.
H3 fue cierto hasta el despliegue de #883 (2026-10-21 11:48 UTC). La subagente 4 de S162 lo vio porque su rama nació de
un `main` del 2026-10-18, anterior al reemplazo (A25, A52). **Recomendación: no reprocesar nada.**

## 1. Qué pasa físicamente y por qué importaba

Hasta el 2026-10-18 la réplica corría el detector anterior (C0), que suma la radiancia de todo el ROI de cumbre en el
Test 1 integrado. Con ese camino encendido, una noche tibia en el cráter de Láscar alcanzaba para publicar una
detección `summit` débil (0,034 MW a 0,73 km) aunque el calor de esa pasada estuviera en realidad a 9 a 29 km. K apaga
ese camino (D30), y la misma pasada queda `far`, con la energía donde está. Si el tablero hubiera mezclado los dos
detectores según la fecha, el operador habría visto un cambio de comportamiento del volcán donde sólo cambió el código
(A104). Por eso valía la pena medirlo.

## 2. Qué se midió y cómo

Cada record se clasifica por dos varas independientes:

- **(a) Marca de régimen** que escribe `pipeline/store.py:_marca_regimen` (l. 89 a 94; se escribe en l. 541): perfil y
  `codigo_sha` del run. Es K si el sha desciende del merge de K (#850, `34cea39e4`, 2026-10-18 09:57:30 UTC) y el
  perfil, **leído en ese sha**, trae los tres flags de K (`enable_test1_path: false`,
  `enable_tests_23_prose_branch: true`, `enable_modis_b22_primary: true`, siguiendo el `extends`). Un record sin marca
  es NO-K (la marca existe desde S151 y ningún record C0 de producción la trae).
- **(b) Huella física del Test 1 integrado**, que K apaga: `triggered_test1` verdadero o `final_hotspot_source` igual a
  `test1` o `test1_roi`.

«El tablero publica» es el predicado del tablero ejecutado con node sobre `frontend/index.html` del mismo commit
(`banco_paridad._JS`: `isSummitDetection` y `isValidDetection` y no `isThermalArtifact` y `mirovaEqVrpDisplay` > 0),
nunca reconstruido a mano (A97). El control de identidad del predicado (5 casos de S139 y 2 de publicación) da lo
esperado en las tres corridas.

Scripts (sólo lectura; leen con `git show`, no tocan el checkout):

| script | salida | qué mide |
|---|---|---|
| `censo_h3.py [commit]` | `censo_main_salida.txt` | censo de `origin/main` |
| `censo_h3.py pre-s158-reemplazo-k` | `censo_control_pre883_salida.txt` | control positivo: el corpus anterior a #883 |
| `pages_h3.py` | `pages_salida.txt` | lo que GitHub Pages sirve hoy (JSON completo y `_recent`) |
| `noches_h3.py` | `noches_salida.txt` | tamaño de H3 en noches, antes contra después de #883 |

## 3. Resultados

### 3.1 Censo de `origin/main` (entregable 1)

Denominador: **72.438 records** de los 11 Tier A, observaciones del 2025-02-15 01:40 al 2026-10-26 01:40 UTC.

| vara | resultado |
|---|---|
| régimen por la marca | K: 72.438; NO-K o SIN DATO: **0** |
| huella del Test 1 integrado | **0** records |
| publicados por el tablero | 9.538, de ellos NO-K: **0**; con huella: **0** |
| observaciones anteriores al 2026-09-18 | 68.072 records, 0 NO-K; 9.093 publicados, 0 NO-K |

La tabla por volcán, sensor y mes que pedía la tarea queda vacía: no hay una sola celda distinta de cero. La tabla
por mes de observación (21 meses, de 1.607 a 3.696 records por mes) está en `censo_main_salida.txt`; en todos los meses
la columna NO-K vale 0. El 68.072 coincide exacto con el que S160 midió sobre `d516b9d8c`
(`experiments/_s160_audit/v4/v_281_regimen_por_mes_salida.txt`, citado en la marca S160 de `docs/MISSION.md`).

### 3.2 Control positivo: el instrumento sí ve la mezcla cuando existe (pregunta 1, A116)

Sobre el tag `pre-s158-reemplazo-k` (`bacc630c4`, corpus anterior a #883): 63.696 records (2025-02-15 a 2026-10-21
08:10 UTC), **59.800 sin marca** y 3.896 K; 24.363 con huella del Test 1; el tablero publicaba 25.574, de ellos
**25.188 NO-K** y 22.167 con huella. El caso de S162 sale ahí exactamente como lo describió la subagente: NO-K, huella
del Test 1, **publicado**. O sea que el cero de hoy no es ceguera del instrumento.

### 3.3 Lo que sirve GitHub Pages hoy

Bajado de `https://mendozavolcanic.github.io/VRP-chile/` el `index.html` desplegado y los 22 JSON (11 completos y 11
`_recent`, que es con lo que arranca el tablero, S120):

| archivo | records | ventana | NO-K | huella | publicados | publicados NO-K |
|---|---|---|---|---|---|---|
| `<vol>.json` | 72.435 | 2025-02-15 01:40 a 2026-10-25 07:25 | 0 | 0 | 9.538 | 0 |
| `<vol>_recent.json` | 11.638 | 2026-07-18 02:05 a 2026-10-25 07:25 | 0 | 0 | 1.019 | 0 |

Los 3 records de diferencia con `main` son pasadas NRT de la última noche que el sitio todavía no tenía al bajarlo
(caché o despliegue en curso); no cambian ningún conteo de publicados. Los 90 residuos C0 que #883 apartó en
`data/_c0_residuales/` se copian al sitio con todo `data/`, pero ninguna vista los pide (único uso en
`frontend/`: un comentario en `cambio_detector.js:22`).

### 3.4 De dónde vino la mezcla (entregable 2)

| fecha (UTC) | qué pasó | evidencia |
|---|---|---|
| 2026-10-18 09:57 | merge de K (#850) | `34cea39e4` |
| 2026-10-18 ~11:00 | backfill con K de los 30 días previos (observaciones desde el 2026-09-18) | `369244ced data(backfill): Lascar 2026-09-18..2026-10-18 (S120)`; S155 ancló la marca del tablero ahí |
| 2026-10-18 22:09 | se corta la rama de S162 (`merge-base` `2ca366cdc`) | `git merge-base origin/s162-v375-protegidas-snpp origin/main` |
| 2026-10-21 11:48 | #883 reemplaza con K todo el histórico de los 11 Tier A desde el 2025-02-15; Pages lo despliega con éxito | `8471add46`; run de `pages-deploy.yml` sobre `8471add46`, `success` |
| 2026-10-24 | la subagente 4 de S162 lee `data/` de su rama y ve el C0 | `INFORME.md` de S162, H3 |

En `2ca366cdc`, en `014a1ab61` (punta de la rama de S162) y en `8471add46^`, el record de Láscar 2026-08-22 05:06 Suomi
NPP es `triggered_test1 True`, `test1_roi`, `summit`, 0,034 MW a 0,732 km, sin marca. En `8471add46` pasa a
`_s154_reproc_k_historico` en `3695f6758`, `far`, 0,511 MW a 8,23 km. La frontera que S162 tomó del mensaje del
backfill (2026-09-18) era real entre el 2026-10-18 y el 2026-10-21; desde #883 ya no hay frontera en los datos
(`DATOS_K_DESDE_UTC = "2025-02-15T00:00:00Z"`, `frontend/cambio_detector.js:32`).

Todos los `codigo_sha` distintos del corpus de hoy (53 combinaciones de perfil y sha, `_s154_reproc_k_historico` y
`mirova_equivalent`) descienden de `34cea39e4` y traen los tres flags de K en su perfil; ninguno falta en el repo local.

### 3.5 Efecto en lo que ve el operador (entregable 3)

**Hoy: 0 noches.** No hay records C0 publicados, así que no hay ninguna noche que cambie si se reescribiera con K.

Tamaño que tuvo H3 mientras fue cierto (del 2026-10-18 al 2026-10-21 11:48 UTC, y antes de K en todo el histórico),
medido como el cambio que produjo #883 en las noches publicadas (observaciones del 2025-02-15 al 2026-09-17; noche =
fecha UTC de la pasada menos 12 h; publica si el tablero publica al menos un record de esa noche, en cualquier sensor):

Antes = tag `pre-s158-reemplazo-k` (`bacc630c4`); después = `origin/main` al correr el script (`c69ea98d2`, dos
commits NRT después del censo; no tocan observaciones anteriores al 2026-09-18).

| | noches |
|---|---|
| con algún record antes / después / en ambos | 5.603 / 6.380 / 5.603 (la diferencia es el hueco de nov 2025 a ene 2026 que #883 llenó) |
| publicadas, sobre las 5.603 en ambos: antes / después | **5.343 / 2.627** |
| publica → no publica | **2.730** |
| no publica → publica | 14 |

| volcán | publica → no | no → publica | publicadas antes | después |
|---|---|---|---|---|
| PuyehueCordonCaulle | 121 | 0 | 468 | 347 |
| Villarrica | 491 | 1 | 572 | 82 |
| Lascar | 36 | 2 | 477 | 443 |
| Copahue | 467 | 0 | 498 | 31 |
| NevadosDeChillan | 373 | 3 | 387 | 17 |
| Llaima | 486 | 0 | 498 | 12 |
| Chaiten | 329 | 0 | 484 | 155 |
| PlanchonPeteroa | 192 | 0 | 488 | 296 |
| Lastarria | 42 | 7 | 477 | 442 |
| Isluga | 65 | 0 | 505 | 440 |
| Tupungatito | 128 | 1 | 489 | 362 |

Por familia de sensor (noche y sensor): MODIS 869 publica → no y 210 al revés; VIIRS 375 2.515 y 39; VIIRS 750 2.530
y 0. Lectura: con el detector anterior el tablero publicaba en 95 % de las noches con datos (5.343 de 5.603), casi
(siempre `summit`, que el predicado exige). Las mayores caídas son Copahue, Llaima, Villarrica y Chillán; Láscar,
Lastarria e Isluga casi no cambian. Es consistente con la sobre-publicación que motivó K (A98, D30), pero acá no se
cruzó con MIROVA: cuántas de esas 2.730 noches eran alertas de MIROVA no está medido (SIN DATO). Esto es lo que H3 habría significado si siguiera vigente; desde el 2026-10-21 está en 0.

## 4. Recomendación (entregable 5)

**No reprocesar nada.** El tramo que H3 señalaba ya se reprocesó con K en #883 y está desplegado. Lo que sí conviene:

1. **Bajar H3 en el informe de S162** con una marca A113 que apunte acá: «REFUTADO para el tablero desde #883
   (2026-10-21); la rama se cortó del `main` del 2026-10-18». Lo hace quien tenga esa rama; esta sesión no la toca.
2. **Regla para las hijas del loop** (A52 aplicado a datos): antes de medir `data/`, leerlo de `origin/main` con
   `git show origin/main:data/...` o hacer `git merge origin/main` en la rama; un informe que mida datos debe citar el
   commit del corpus. `censo_h3.py` ya recibe el commit como argumento.
3. La vigilancia existe: `tests/test_cambio_detector_frontera_s155.py` mide la frontera en los datos, y la marca S160
   de `docs/MISSION.md` ya registra el 68.072. No hace falta un guard nuevo.

## 5. Límites y SIN DATO

- Sólo los 11 Tier A. Los 34 volcanes fuera del cron (ventana corta de abril de 2026) no se miraron, porque no están en
  el tablero principal como serie viva; SIN DATO sobre su régimen.
- La marca dice con qué código y perfil se escribió el record, no reproduce el cálculo. Que «K en ese sha» sea el
  mismo detector en los 53 shas se apoya en los tres flags; otros cambios de código posteriores a #850 (por ejemplo los
  de S154 a S161) no se auditaron acá, y no son lo que H3 pregunta.
- La noche se define con un corte fijo de 12 h UTC; no se usó el selector de noche o día del tablero (S153).
- La comparación con Pages se hizo una vez, a las ~02:35 UTC del 2026-10-26.

## 6. Verificación independiente (entregable 4)

VERIFICADOR_PLACEHOLDER
