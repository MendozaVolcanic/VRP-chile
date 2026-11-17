# Plan: darle al perfil `experimental` una razón de existir (S190)

> **Qué es.** Un plan para que el laboratorio mida algo que MIROVA no hace, sin encender nada en este PR. No toca
> perfiles, workflows ni `pipeline/`. Las decisiones que sólo puede tomar Nicolás están en la tabla del §8.
>
> **Base.** `origin/main` en `13af35186`. Todo número sale de un archivo o script nombrado al lado; los scripts y sus
> salidas están en `experiments/_s190_experimental/`.

## 0. La premisa del encargo, corregida primero

El encargo decía que `experimental` no corre desde S101 y que su último record es del 2026-08-25. Eso es cierto de
**otra carpeta**: `data/experimental/`, la serie vieja de S15 que el propio perfil declara ruido. El perfil de hoy
escribe en `data/experimental_v2/` y **sí corre**:

| hecho | fuente |
|---|---|
| `.github/workflows/experimental-diario.yml` corre el perfil a diario sobre los 11 Tier A desde S150 (decisión de Nicolás del 2026-10-09) | el workflow, cabecera |
| último commit en `data/experimental_v2/`: 2026-11-17 00:15 UTC (`Experimental update Llaima`) | `gh api repos/MendozaVolcanic/VRP-chile/commits?path=data/experimental_v2` |
| 4.842 records desde el 2026-10-02, 3.326 con `vrp_mw > 0` | `rango_experimental_v2.py`, `salida_rango_experimental_v2.txt` |
| corre **congelado en C0** (el detector anterior: Test 1 integrado, conectiva `min`, banda 21, sin la vía en ningún sensor) | `pipeline/profiles/experimental.yaml`, guard `tests/test_experimental_congelado_s150.py` |
| es la **sombra de K** que lee `scripts/vigilancia_sombra.py` (`.github/workflows/vigilancia-sombra.yml`) | cabecera del workflow |
| el tablero lo muestra en la pestaña «Laboratorio» (`frontend/experimental/index.html`, enlazada desde `frontend/index.html:418`) | los dos archivos |

La lectura de «no corre» viene de la auditoría S149 (`docs/audit_s149/plan_final/FRENTE_F_EXPERIMENTAL.md` §0,
puntos 2 y 3), que S150 dejó obsoleta al congelar el perfil y crear el workflow diario. Lo que sigue vigente de esa
auditoría es lo de fondo: **el laboratorio no tiene diferenciación propia**. Hoy no es un laboratorio, es un
testigo: guarda lo que veía producción el 2026-10-09.

Y el testigo dejó de tener a quién vigilar. La sombra existe para disparar la reversión de K si producción calla una
alerta que C0 ve. Desde el 2026-11-11 los tres sensores de producción corren la vía «código MIROVA» y ninguno sigue en
K; el propio `scripts/vigilancia_sombra.py` (comentario S180, líneas 366 a 368) dice que con la lista de sensores en K
vacía la vigilancia «no exige nada». La sombra sigue costando un workflow diario y ya no protege una adopción viva.

## 1. El fenómeno, antes del plan

Un volcán con un foco chico (el lago de lava de Villarrica, el campo fumarólico de Lazufre en Lastarria, el lacolito
de Cordón Caulle) calienta su píxel lo justo para quedar al borde del umbral. MIROVA publica sólo la parte de esa
señal que cruza su línea; el resto es calor real que no aparece. La réplica copia esa línea a propósito, porque su
valor está en que nos crean (memoria `feedback_s143_primero_igualar_a_mirova`). El laboratorio es el lugar donde se
puede bajar la línea, y su costo es el de siempre: cada píxel extra que se mira es una oportunidad de confundir un
valle tibio, un salar o un incendio con el volcán.

Por eso el laboratorio sólo vale si cada cosa que agrega se mide contra algo que **no** sea MIROVA (A115): lo que
MIROVA no publica, contra MIROVA, cuenta siempre como falso positivo.

## 2. ¿Sobre qué base corre? Recomendación: la vía de producción, más una extensión a la vez

**Opción A, la vía de producción más una extensión** (recomendada). El laboratorio hereda `mirova_equivalent` tal
cual (vía «código MIROVA» en los tres sensores) y diverge en una sola dimensión declarada. Así, toda diferencia con
el tablero operacional es atribuible a esa dimensión, que es lo que el diseño S147 exige en su §5 («un cambio de umbral
que además mueva la geometría produce diferencias de geometría disfrazadas de diferencias de umbral»).

**Opción B, el detector anterior (C0, lo que corre hoy).** Tiene un atractivo: ya ve más. Pero lo que ve de más no es
la franja de señal real que buscamos, es mayormente el Test 1 integrado, cuyo valor de reposo crece con el número de
píxeles del disco: S147 midió que el 90,9 % de los records VIIRS 375 superan ese criterio por puro ruido
(`docs/DISENO_SENSIBILIDAD_POR_ZONA_S147.md` §1). El dato de hoy va en la misma dirección: el laboratorio tiene
`vrp_mw > 0` en 3.326 de 4.842 records (69 %), producción en 10.320 de 73.695 (14 %)
(`salida_rango_experimental_v2.txt`; ojo, `vrp_mw > 0` no es el predicado del tablero y las ventanas no son iguales,
así que es una señal de orden de magnitud, no una comparación). Construir encima de C0 mediría el defecto del Test 1,
no el fenómeno; S147 §9 ya lo dejó escrito como tercer riesgo.

**Qué hacer con el C0 congelado.** Dos caminos, y es decisión de Nicolás (D1 del §8):

- **D1-a (recomendado):** dejar `experimental` como está (sombra C0) hasta que Nicolás decida retirarla, y crear un
  perfil **nuevo** para el laboratorio. Una serie no debe mezclar dos configuraciones (`tests/test_profile_data_isolation_s124.py`,
  docstring): reconvertir `experimental` cambiaría la configuración a mitad de `experimental_v2`.
- **D1-b:** retirar la sombra C0 (ya no protege una adopción, §0), apagar `experimental-diario.yml` y
  `vigilancia-sombra.yml`, y reconvertir `experimental` con un `data_subdir` nuevo. Más limpio a la larga, pero
  apaga un vigilante y eso pide su propio PR con guard.

## 3. ¿Con qué cron y cuánto cuesta?

**Fase 1 no necesita cron nuevo** (§5): la primera medición se hace sobre datos que ya existen o con un reproceso
acotado. El cron llega recién si una extensión cumple su criterio pre-registrado.

Costo de referencia, medido:

Ventana: 2026-11-10 04:15 a 2026-11-17 04:15 UTC, suma de la duración de cada job dividida por 7 días. Fuente:
`experiments/_s190_experimental/medir_minutos_actions.py`, salida `salida_minutos_actions.json` (1 run quedó sin jobs
legibles y está listado ahí).

| workflow | minutos-job por día |
|---|---|
| NRT (cron 2 h, 11 Tier A) | 1.852 |
| Reproceso de la historia con la vía (despachos de S180 en adelante) | 1.272 |
| Sombra de los 34 | 438 |
| Tests | 395 |
| **Experimental diario (la sombra C0 de hoy)** | **186** |
| Guardia K de VIIRS | 159 |
| **Sombra código MIROVA (la vía en los 3 sensores, 11 Tier A)** | **147** |
| Guardia K de MODIS | 86 |
| total de todos los workflows | 4.618 |

**Cuánto costaría el laboratorio con cron.** El mejor proxy es la sombra código MIROVA, que corre la vía en los tres
sensores sobre los 11 Tier A una vez al día: unos 150 minutos-job por día. Un laboratorio sobre la vía con un umbral
distinto en la zona A cuesta lo mismo, porque procesa los mismos gránulos. Es un 3 % del total.

**Pico de jobs simultáneos en la semana: 20** (mismo archivo). 20 es el tope de jobs a la vez que GitHub documenta para
cuentas Free; no verifiqué el plan de la cuenta, pero el dato dice que la semana ya tocó ese techo.

**Qué significa el costo en este repo.** El repo es público (`gh api repos/MendozaVolcanic/VRP-chile --jq .visibility`),
así que los minutos de runners estándar no se cobran. El límite que muerde es otro: los jobs simultáneos de la cuenta.
El NRT, las tandas de los 34 y las sombras ya compiten por esos cupos, y un job del laboratorio que ocupa un runner a
la hora del NRT atrasa el dato operacional (fue la razón de S141 para sacar el experimental del job del NRT, cabecera
de `experimental-diario.yml`).

**Si llega a tener cron** (fase 3): un paso más dentro de `experimental-diario.yml` o un workflow propio con el mismo
patrón, a la misma hora (14:00 UTC, cuando ya llegaron las pasadas nocturnas), grupo de concurrencia propio y
`max-parallel: 4`. Ojo con la hora real: en la última semana `experimental-diario` arrancó entre las 18:55 y las 23:09
UTC, no a las 14:00 (`gh run list --workflow experimental-diario.yml -L 8`): el cron de Actions llega horas tarde
(lección S171). Con D1-b el costo neto es negativo (reemplaza a la sombra C0, que cuesta 186 contra unos 150); con
D1-a suma unos 150 minutos-job por día, y Nicolás podría compensarlo revisando si las guardias K (245 minutos-job por día
entre las dos) siguen haciendo falta ahora que ningún sensor de producción corre K.

## 4. ¿Qué `data_subdir` y qué guard impide contaminar la vista operacional?

**Subdir:** uno nuevo y sin historia, propuesto `data/laboratorio_v1/` (D3). Nunca `experimental_v2` (es la sombra C0)
ni `experimental` (legacy de S15).

**Guards que ya existen y lo cubren:**

| guard | qué impide |
|---|---|
| `tests/test_profile_data_isolation_s124.py` | dos perfiles escribiendo en la misma carpeta |
| `tests/test_guard_laboratorio_no_mas_ciego_s147.py` | que el laboratorio tenga un piso de magnitud mayor que producción |
| `tests/test_pages_sin_sombras_s173.py` | que una sombra o guardia (`sombra*.yaml`, `guardia*.yaml`) dispare o entre al deploy de Pages |

**Guards nuevos que pide el plan** (en el PR que cree el perfil, no en éste):

1. **«Difiere sólo en lo declarado»**, con el patrón de `tests/test_experimental_congelado_s150.py` test 1: el perfil
   nuevo resuelto con `VRP_PROFILE` (nunca leyendo el YAML, A89) es igual a `mirova_equivalent` en todo salvo nombre,
   carpeta y la lista explícita de claves de la extensión. Si la réplica cambia, el laboratorio la sigue; si alguien
   mete una segunda diferencia sin declararla, rojo.
2. **El tablero operacional no lee el laboratorio**: `frontend/index.html`, `diario.html` y `mosaico.html` no
   nombran el subdir del laboratorio (búsqueda con frontera de palabra, A92), con un control que sí encuentra
   `mirova_equivalent`.
3. **El commit del NRT no lo agrega**: el paso de commit de `nrt.yml` sólo hace `git add` de
   `data/mirova_equivalent/` (y el laboratorio sólo de su carpeta).
4. **Extender el guard S147** con el parámetro de la extensión cuando sea monótono en «ver más» (su docstring lo deja
   previsto).

## 5. ¿Contra qué referencia, y cómo se consigue hoy?

**SWIR de alta resolución: NHI-v1.** Es la única vara que existe como dato. El repo hermano publica por volcán
`docs/nhi_data/<Volcán>/nhi_timeseries.json` (Sentinel 2 y Landsat 8/9, algoritmo NHI de Marchese), cron diario, vivo
(último commit 2026-11-17 01:07 UTC). Conteo de hoy (`contar_nhi.py`, `salida_contar_nhi.txt`):

- 10 de 11 Tier A; **Lastarria no tiene serie** (404), así que Lazufre sigue sin vara SWIR (lo mismo que vio S149, F-5).
- 1.085 escenas desde febrero, 187 con alerta.
- Desde el 2026-10-02 (inicio de `experimental_v2`): 196 escenas y **19 con alerta**. Es muy poco para medir nada.

Dos advertencias que el criterio tiene que absorber:

- **El nulo ya está medido y es alto.** S131 cruzó NHI con nuestras detecciones sin MIROVA en 5 volcanes: en 4 de 5 la
  tasa de alerta NHI en esas noches fue igual a la tasa basal del volcán (20 a 49 %); sólo Nevados de Chillán subió
  (25 % contra 12 %) (`docs/s131/agentes/OTRO_SENSOR.md`, `experiments/_s131_audit/otro_sensor/`). Un volcán con foco
  crónico «confirma» cualquier cosa por azar. Todo criterio se compara contra ese nulo, no contra cero (A110).
- **NHI es diurno y cada pocos días; nuestras pasadas son nocturnas.** El pareo es escena SWIR contra la noche más
  cercana, con una tolerancia fija que se declara antes de correr.

**Actividad conocida del OVDAS.** No existe como dato en el repo (S149, F-3; no lo volví a buscar fuera de las rutas
que S149 miró). Se consigue de dos formas, las dos con Nicolás (D4): (a) una tabla de episodios que él arme desde los
RAV y los cambios de alerta técnica de los 11 Tier A (volcán, fecha inicio, fecha fin, tipo de fenómeno, fuente), o
(b) un scraper de los reportes públicos de la RNVV (`rnvv.sernageomin.cl`, mencionado en
`docs/BASELINE_LITERATURA_TIER_A_S77.md`), que sería un proyecto aparte con su ficha en el mapa del workspace.

**Persistencia** (diseño S147 §7.3): una fuente real se repite en el mismo lugar noche tras noche y el ruido no. No
necesita referencia externa y sirve como segundo juez.

## 6. ¿Cuál es la primera extensión y con qué criterio pre-registrado?

Repaso de la lista `docs/BEYOND_MIROVA_EXTENSIONS.md` §12 con una sola pregunta: ¿se puede medir contra OVDAS, SWIR o
persistencia?

| id | ¿medible hoy fuera de MIROVA? | por qué |
|---|---|---|
| MEJ-1 trazabilidad | no hace falta | ya es fortaleza actual, no una extensión |
| MEJ-2 fondo determinista | no | cambia la magnitud, y no tenemos verdad de magnitud |
| MEJ-3 fórmula a todo ángulo | no | magnitud; causa desconocida |
| MEJ-4 grilla anclada | no | ya lo hacemos; falta comprobar la coordenada |
| **MEJ-5 señal bajo el umbral de MIROVA** | **sí** | es detección: SWIR y persistencia la pueden confirmar o refutar |
| MEJ-6 día con filtro solar | en parte | su beneficio son alertas que MIROVA sí publicó, o sea paridad más que laboratorio |
| MEJ-7 foco MODIS de Láscar | no como extensión | es un caso, no un cambio de algoritmo |

**Primera extensión: MEJ-5 en la forma del diseño S147**, umbral por zona: más permisivo dentro del `inner_radius_km`
de cada volcán (zona A, el cráter), igual que producción fuera (zona B). Sólo la zona A cambia, así que lo que
aparezca de más está, por construcción, donde el prior volcánico es alto.

**Cambio respecto de S147.** Su parámetro natural era el multiplicador de sigma del criterio contextual del detector de entonces (S147 es
anterior a K). La vía
«código MIROVA» tiene sus propios umbrales (K1, dNTI mínimo); cuál se modula en la zona A se decide al escribir el
`writing-plans` del PR del perfil, leyendo `pipeline/mirova_v750_codigo.py`, y no lo afirmo aquí sin haberlo leído.
Puyehue Cordón Caulle (inner de 20 km, casi dos tercios de la escena, S147 §9) queda fuera de la primera tanda.

**Criterio pre-registrado (borrador; se sella con commit antes de correr, D5):**

1. **Calibración del umbral** (S147 §6): sobre negativos limpios (pasadas que MIROVA listó con VRP 0), el umbral de la
   zona A es el más permisivo cuya tasa de publicación por pasada no supera la tasa objetivo que fije Nicolás (S147
   propone ~30 % en zona A; D5).
2. **Pareo con NHI**: cada escena NHI se parea con la noche más cercana dentro de ±1 día. Se compara la tasa de alerta
   NHI en (i) noches donde **sólo el laboratorio** publica en zona A contra (ii) noches donde **ninguno** publica, por
   volcán, con prueba de permutación dentro del volcán.
3. **Control del instrumento** (A110, A116): el mismo cálculo con las fechas NHI corridas 15 días tiene que dar
   diferencia nula; si da distinta de cero, el instrumento mide estacionalidad y el veredicto no vale.
4. **Persistencia**: la fracción de detecciones extra de la zona A que caen a ≤1 km de otra detección del laboratorio
   en las 3 noches previas, contra la misma fracción con posiciones sorteadas dentro de la zona A.
5. **Veredicto CUMPLE** si (2) da exceso positivo con p < 0,05 en al menos 4 de los 9 volcanes con NHI y sin Puyehue,
   (3) da nulo, y (4) supera al sorteo. **NO CUMPLE** si no. **SIN PODER** si hay menos de 10 escenas NHI pareadas
   con «sólo laboratorio» en un volcán: ese volcán no vota.

**Ventana:** desde 2026-02-15 (la tabla de MIROVA es sana desde marzo, A119; NHI arranca el 2026-02-04) hasta el
último día disponible. La ventana de `experimental_v2` (desde 2026-10-02, 19 alertas NHI) no alcanza.

## 7. Orden de los pasos

| # | paso | sale | quién lo destraba |
|---|---|---|---|
| 0 | este plan | `docs/PLAN_EXPERIMENTAL_S190.md` | Nicolás: tabla del §8 |
| 1 | perfil nuevo detrás de un flag apagado (base vía, zona A sin cambio todavía) + guards 1 a 4 del §4 | PR con tag defensivo (A45, toca `pipeline/` para leer la zona) | Nicolás: A45 |
| 2 | sellar el criterio del §6 con los valores de D5 | commit del pre-registro | Nicolás: D5 |
| 3 | barrido sobre negativos limpios y elección del umbral de zona A | `experiments/_s19x_lab_zona/` | nadie |
| 4 | reproceso del laboratorio en la ventana del §6, por volcán y en Actions (MODIS no corre en Windows) | `data/laboratorio_v1/` | Nicolás: D2 (costo) |
| 5 | medición contra NHI, control y persistencia | veredicto CUMPLE / NO CUMPLE / SIN PODER | nadie |
| 6 | sólo si CUMPLE: cron diario y vista de tres estados en la pestaña Laboratorio (S147 §8), ficha SDA | PR | Nicolás: merge |

## 8. Decisiones para Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| D1 | ¿Qué hacemos con la sombra C0 (`experimental`, `data/experimental_v2/`), que ya no protege ninguna adopción porque ningún sensor sigue en K? | (a) dejarla y crear un perfil nuevo para el laboratorio; (b) retirarla (apagar `experimental-diario.yml` y `vigilancia-sombra.yml`) y reconvertir `experimental` con carpeta nueva; (c) dejar todo como está | **(a)** por ahora: no mezcla configuraciones en una serie y no apaga un vigilante en el mismo paso. Retirar la sombra (b) después, en su propio PR |
| D2 | ¿Base del laboratorio? | (a) la vía de producción más una extensión a la vez; (b) el detector anterior C0 | **(a)**: lo que C0 ve de más es mayormente el Test 1 (90,9 % de VIIRS 375 lo cruza por ruido, S147) |
| D3 | ¿Nombre del perfil y carpeta? | `laboratorio` en `data/laboratorio_v1/`; otro nombre | `laboratorio` / `laboratorio_v1`: no se confunde con la sombra ni con el legacy |
| D4 | ¿Cómo conseguimos la vara OVDAS? | (a) tabla de episodios armada por Nicolás desde RAV y alertas técnicas de los 11 Tier A; (b) scraper de los reportes públicos de la RNVV como proyecto aparte; (c) seguir sólo con NHI y persistencia | **(a)** para empezar (es corta y él la conoce); (b) si se quiere mantener viva |
| D5 | ¿Tasa objetivo en zona A y umbrales del criterio? | ~30 % de las pasadas en negativos limpios (propuesta S147); otra; y p < 0,05 en ≥4 de 9 volcanes | aceptar 30 % y 4 de 9 como punto de partida, sellarlos antes de correr |
| D6 | ¿Puyehue Cordón Caulle en la primera tanda? | fuera; dentro con zona A reducida a un radio propio | **fuera** (inner de 20 km rompe el argumento del área, S147 §9) |
| D7 | ¿Cuánto Actions se le da al reproceso del paso 4? | la ventana entera de una vez; por tandas fuera de horario del NRT y de las tandas de los 34 | **por tandas**, después de que terminen las tandas de los 34 |

### Decisión de Nicolás (2026-11-17, ≈04:41 UTC)

«Sí, las siete», dicho en la sesión S190 y reenviado a esta sesión por S190 (no lo leí de primera mano). Quedan
aceptadas las siete recomendaciones de la tabla: D1 (a), D2 (a), D3 `laboratorio` en `data/laboratorio_v1/`, D4 (a),
D5 30 % y 4 de 9 con p < 0,05 (se sellan con commit antes de correr), D6 Cordón Caulle fuera, D7 por tandas después
de las tandas de los 34. Esto **no** es el sí para A45 del paso 1 ni el «mergea» de este PR: los dos se piden aparte.
La plantilla de la tabla de episodios de D4 está en `docs/PLANTILLA_EPISODIOS_OVDAS_S190.md`.

## 9. Lo que este plan no resuelve

- No leí `pipeline/mirova_v750_codigo.py`: qué umbral de la vía se modula en la zona A queda para el plan del PR del
  perfil (paso 1).
- No medí la tasa de publicación del laboratorio con el predicado del tablero (A97); el 69 % contra 14 % del §2 es
  `vrp_mw > 0` en ventanas distintas.
- No volví a buscar datos OVDAS fuera de lo que S149 revisó.
- Lastarria queda sin vara SWIR; su validación depende de D4 o de la persistencia.
