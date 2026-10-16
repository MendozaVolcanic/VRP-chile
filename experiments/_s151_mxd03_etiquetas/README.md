# Probe S151, tarea 1.17: etiquetas summit/far de MODIS re-medidas con MxD03 en los 11 volcanes

**Estado: escrito, probado con datos sintéticos, NO corrido.** Este README fija la población, el
estimador y el criterio antes de la primera corrida. La muestra está fijada en `poblacion.json`.

## Por qué

El probe de #828 (`experiments/_s151_probe_mod03/`) mostró que la posición MODIS que produce
`_interp_geo` (`pipeline/process_modis.py:342`) queda corrida de 1 a 3 km de la geolocalización
oficial MxD03, y que la grilla de 5 km del L1B calza con MxD03 en el offset 2 y no en el 0. Midió 7
gránulos, casi todos de Láscar. De esa posición cuelgan la etiqueta `summit`/`far`, la publicación en
el tablero, D12, el recall MODIS de A81 y A82 y la etiqueta `far` de Chillán. La decisión de cambiar
producción a MxD03 es de Nicolás (A45); este probe le dice cuánto movería lo que el operador ve.

El fenómeno físico es simple: el satélite mira la misma escena, el mismo píxel caliente y la misma
energía; lo único que cambia es **dónde decimos que está** ese píxel. Si el foco queda a 4 km del
cráter con una geolocalización y a 6 km con la otra, y el radio interno del volcán es 5 km, el mismo
calor pasa de «cráter» a «lejano» y deja de publicarse.

## Qué se mide

Para cada gránulo de la muestra, el probe corre el pipeline de producción **dos veces sobre el mismo
L1B**:

- **brazo C**: tal cual corre hoy (`calculate_vrp` con lat/lon de `_interp_geo`);
- **brazo M**: idéntico, salvo que lat/lon salen de MxD03 (el archivo que el pipeline ya baja y no lee).

Las dos salidas pasan por `store.append_record` (escribiendo en un directorio temporal, nunca en
`data/`) y por el **predicado del tablero ejecutado con node** desde `frontend/index.html`
(`isSummitDetection && isValidDetection && !isThermalArtifact && mirovaEqVrpDisplay > 0`), con el
mismo runner de `scripts/banco_paridad.py` (A97: no se reconstruye a mano). Los argumentos de
`calculate_vrp` y `append_record` son los de `scripts/run_pipeline.py`; un test los compara por AST.
Los ángulos (cenit, acimut) siguen saliendo de `_interp_geo` en los dos brazos, para que lo único
distinto sea la posición (el cenit sólo se persiste: A_pix es nadir fijo, A66).

Por gránulo se registra:

- la etiqueta en C y en M, y si cambia (`summit->far`, `far->summit`, o aparece o desaparece);
- la publicación en C y en M, y si cambia (`1->0`, `0->1`);
- si cambió la detección misma (número de píxeles anómalos o magnitud del cúmulo), para separar
  «mismo calor, otra etiqueta» de «otro calor»;
- el corrimiento `_interp_geo` menos MxD03 en el píxel del cráter (norte, este y total), que extiende
  la tabla de #828 a los 11 volcanes, por satélite y cenit;
- si el brazo C reproduce la etiqueta y la publicación guardadas en el JSON (deriva de código desde
  que se produjo el record; se informa, no entra al veredicto).

## Población y muestra

Records MODIS de los 11 Tier A entre el **2026-03-01 y el 2026-10-12** (A119: MODIS completo desde
marzo; el 12 de octubre deja margen para que exista el L1B Standard), un record por gránulo.
`inner_radius_km` de `frontend/index.html`, que coincide con `volcanoes.yaml` en los 11.

| estrato | regla | qué puede cambiar |
|---|---|---|
| **A** | hotspot final a 3 km o menos del límite (`|d − inner| ≤ 3`) | la etiqueta, y con ella la publicación |
| **B** | sólo el centroide del cúmulo a 3 km o menos del límite | la publicación de un `summit` (por `centroid_dist_km > inner`) |
| **control** | todas las distancias a más de 6 km del límite | nada por reubicación: si cambia, cambió la detección |
| medio | el resto (3 a 6 km del límite) | no se muestrea; se cuenta |

Los 3 km son el corrimiento máximo que midió #828. La población A y B es la que el encargo define
(«`final_hotspot` o `primary_cluster` a 3 km o menos del límite»), separada en dos porque sólo A puede
cambiar la etiqueta: en B el hotspot final está lejos (típicamente el Salar en Láscar, D12) y el que
está cerca del límite es el cúmulo.

Conteo de la población (de `seleccionar_mxd03.py`, que lo escribe en `poblacion.json`):

| volcán | inner | A | B | control | medio | publicadas en el tramo | muestra A / B / control |
|---|---|---|---|---|---|---|---|
| Láscar | 5 | 2 | 202 | 17 | 204 | 16 | 2 / 8 / 6 |
| Lastarria | 3 | 43 | 365 | 18 | 4 | 21 | 30 / 8 / 6 |
| Isluga | 5 | 13 | 206 | 16 | 173 | 12 | 13 / 8 / 6 |
| Tupungatito | 7 | 12 | 96 | 76 | 298 | 24 | 12 / 8 / 6 |
| Planchón Peteroa | 3 | 47 | 417 | 18 | 9 | 28 | 30 / 8 / 6 |
| Nevados de Chillán | 5 | 11 | 266 | 42 | 177 | 21 | 11 / 8 / 6 |
| Llaima | 5 | 13 | 269 | 33 | 193 | 20 | 13 / 8 / 6 |
| Villarrica | 5 | 46 | 190 | 11 | 269 | 42 | 30 / 8 / 6 |
| Copahue | 4 | 14 | 377 | 26 | 83 | 11 | 14 / 8 / 6 |
| Puyehue Cordón Caulle | 20 | 173 | 3 | 229 | 142 | 361 | 30 / 3 / 6 |
| Chaitén | 5 | 64 | 194 | 9 | 307 | 66 | 30 / 8 / 6 |
| **total** | | **438** | **2.585** | **495** | **1.859** | **622** | **215 / 83 / 66 = 364** |

### Tope y por qué

- **A: 30 por volcán.** Es el estrato que decide la etiqueta: 6 volcanes entran enteros y en los otros
  cinco 30 gránulos dan una tasa con intervalo de Wilson de unos ±15 puntos. Más gránulos no caben
  en el job (abajo).
- **B: 8 por volcán.** Casi todo B es `far` con el hotspot a más de 10 km del límite: por reubicación
  no puede publicarse. Ocho gránulos sirven para confirmar que la tasa es cero o cercana; si no lo
  es, el estimador lo pesa por la población entera (25 a 50 records por gránulo).
- **control: 6 por volcán.** Basta para ver si el brazo M cambia cosas lejos del límite.
- Muestreo uniforme y determinista dentro de cada estrato: orden por `sha1("s151-tarea-1.17" + clave)`.
- **Tiempo por job.** #828 tardó 143 s en bajar, leer y comparar 7 pares (unos 20 s por par); acá se
  suman dos corridas de `calculate_vrp` por gránulo. Estimado: **30 a 50 s por gránulo, 25 a 40 min
  por job** con el tope de 44. El script deja de bajar gránulos a los 70 min (los marca
  `sin_tiempo`) y el job tiene `timeout-minutes: 90` (A15). Con `max-parallel: 4`, los 11 volcanes
  toman 3 rondas: **1,5 a 2 h de reloj**.
- **Disco del runner.** Cada par pesa unos 100 a 150 MB y se borra apenas se usa; el pico queda bajo
  1 GB contra los 14 GB del runner.

## Estimador

Por volcán y estrato *s* (A, B), con población *N_s*, *n_s* gránulos medidos y *k_s* cambios:
cambios estimados = *N_s · k_s / n_s*. Se suman A y B de los 11 volcanes para las publicaciones (*E_pub*)
y para las etiquetas (*E_lab*). *E_pub* se divide por las **622 publicaciones MODIS del tramo**
(predicado del tablero sobre los records guardados). Se informa también el intervalo que da sumar las
cotas de Wilson de cada estrato, las tasas por volcán, y la tabla volcán × satélite × cenit (0 a 20,
20 a 35, 35 a 50, más de 50 grados) con cambios y corrimiento mediano y máximo.

El estrato medio y el control no se extrapolan: el medio no se muestrea y el control es un testigo.

## Criterio (fijado antes de correr)

- **INCOMPLETO** si en algún volcán queda sin medir más de 20 % de su muestra (error de NASA o
  falta de tiempo). Se repite el job corto de ese volcán sobre el mismo código (A108).
- **CAMBIA MUCHO** si se cumple cualquiera de estas dos:
  1. *E_pub* llega a 5 % de las publicaciones del tramo **y** se observaron al menos 3 publicaciones
     movidas (un gránulo de B pesa 25 a 50 records y un caso aislado no decide);
  2. en algún volcán con 10 o más gránulos A medidos, la cota inferior de Wilson de la tasa de cambio
     de etiqueta llega a 20 %.
- **CAMBIA POCO** si *E_pub* queda bajo 2 % de las publicaciones **y** en todo volcán con 10 o más
  gránulos A medidos la cota inferior de Wilson de la tasa de cambio de etiqueta queda bajo 10 %.
- **INTERMEDIO** en cualquier otro caso.

Dos anotaciones que acompañan al veredicto sin cambiarlo:

- **cota inferior**: si más de 10 % de los gránulos se corre más de 3 km en el cráter, la banda de 3
  km se quedó corta y el estrato medio también puede cambiar: las cifras son un piso.
- **control cambia**: si más de 10 % del control cambia de etiqueta, el arreglo no sólo reubica:
  también cambia qué calor se elige (por el ROI o el anillo de fondo, que dependen de la posición).

Sobre los umbrales (A115): «cuánto es mucho» para un arreglo de infraestructura no lo contesta la base
de MIROVA, así que el 2 % y el 5 % son una elección mía, medida contra lo que el operador ve (las
publicaciones), y Nicolás puede cambiarlos antes de sellar. Lo que sí contesta MIROVA es la
**dirección**: si cada publicación movida va hacia lo que MIROVA alertó o en contra. Eso no entra al
veredicto; el resultado guarda la hora y el sensor de cada gránulo para cruzarlo después con la tabla
de MIROVA (`scripts/banco_paridad.py`, A119), y también para contarlo en noches (A94).

## Prueba del instrumento

`probar_probe_mxd03.py` arma una escena de 81 × 81 píxeles de 1 km con un foco de 335 K a 6 km al norte del
cráter (inner 5 km) y la pasa por el pipeline real, `append_record` y el predicado con node, en los
dos brazos. El workflow la corre antes del probe, y `tests/test_mxd03_etiquetas_s151.py` también.

| caso | geolocalización «interpolada» | qué debe salir | qué sale |
|---|---|---|---|
| PRESENTE | corrida 2 km al sur de la verdadera | corrimiento 2 km, `summit->far`, `1->0` | **corrimiento 2,000 km; C summit a 4,67 km, M far a 6,67 km; `summit->far`, `1->0`** |
| AUSENTE | igual a la verdadera | todo `igual`, corrimiento 0 | **todo `igual`, corrimiento 0,000 km** |

## Cómo correrlo

```
gh workflow run probe-s151-mxd03-etiquetas.yml --ref main -f preregistro_aprobado=si
```

Sólo con el criterio sellado y el PR mergeado: `workflow_dispatch` no corre desde una rama. Para
repetir volcanes sueltos: `-f volcanes='["Lascar"]'`.

- **Autenticación:** sólo `EARTHDATA_TOKEN`; el job falla al instante si viene vacío (A71).
- **Concurrencia:** grupo propio; `max-parallel: 4` para no cargar LAADS.
- **Salida:** no hace push. Un artefacto por volcán (`s151-mxd03-etq-<volcán>`: JSON por gránulo,
  log y prueba sintética) y el resumen con el veredicto (`s151-mxd03-etiquetas-resumen`).
- **Regenerar la muestra:** `python seleccionar_mxd03.py` (local, con node). Sólo antes del sello: después,
  la muestra es la de `poblacion.json`.

## Límites conocidos

- El L1B que se baja es el Standard 6.1; parte de los records guardados se produjo con el NRT. La
  diferencia de temperatura es menor que 0,1 K y entra en la columna de deriva (C contra guardado).
- El brazo C corre el código de hoy, no el que produjo cada record. El efecto del arreglo se mide C
  contra M (mismo código); C contra guardado se informa aparte.
- El estrato medio (1.859 records) no se mide. Si la anotación «cota inferior» sale encendida, el
  siguiente paso es muestrearlo.
