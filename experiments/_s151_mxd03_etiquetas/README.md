# Probe S151, tarea 1.17: etiquetas summit/far de MODIS re-medidas con MxD03 en los 11 volcanes

**Estado: versión 2, escrita y probada con datos sintéticos, NO corrida.** Este README fija la
población, el estimador y el criterio antes de la primera corrida. La muestra y su reparto en jobs
están fijados en `poblacion.json`.

La versión 1 (#834) la revisó un verificador con contexto limpio y la dio por «sellable con arreglos»
(informe fuera del repo: `C:\Users\nmend\AppData\Local\Temp\claude\verif_117\VERIFICADOR.md`). Esta
versión aplica sus cinco arreglos:

1. el evaluador no declara «cambia poco» con la banda corta, sale INCOMPLETO si falta un job pedido, e
   informa el neto aparte del bruto;
2. la banda es por record, según el corrimiento que predice el modelo de #828, y no fija en 3 km;
3. la vara principal es el criterio de victoria de la réplica, con censo de las alertas de MIROVA;
4. se agrega un control negativo real, el brazo C';
5. el JSON se escribe por gránulo.

## Por qué

El probe de #828 (`experiments/_s151_probe_mod03/`) mostró que la posición MODIS que produce
`_interp_geo` (`pipeline/process_modis.py:342`) queda corrida de 1 a 3 km de la geolocalización
oficial MxD03, y que la grilla de 5 km del L1B calza con MxD03 en el offset 2 y no en el 0. Midió 7
gránulos, casi todos de Láscar. De esa posición cuelgan la etiqueta `summit`/`far`, la publicación en
el tablero, D12, el recall MODIS de A81 y A82 y la etiqueta `far` de Chillán. La decisión de cambiar
producción a MxD03 es de Nicolás (A45). Este probe le dice si ese cambio respeta el criterio de
victoria de la réplica y cuánto movería lo que ve el operador.

El fenómeno físico es simple: el satélite mira la misma escena, el mismo píxel caliente y la misma
energía; lo único que cambia es **dónde decimos que está** ese píxel. Si el foco queda a 4 km del
cráter con una geolocalización y a 6 km con la otra, y el radio interno es 5 km, el mismo calor pasa
de «cráter» a «lejano» y deja de publicarse. El corrimiento crece con el ángulo de visión, porque el
píxel se estira hacia el borde del barrido.

## Qué se mide

Por cada gránulo de la muestra, el pipeline de producción corre sobre el **mismo L1B** en tres brazos:

- **C**: tal cual corre hoy (`calculate_vrp` con lat/lon de `_interp_geo`);
- **M**: idéntico, salvo que lat/lon salen de MxD03 (el archivo que el pipeline ya baja y no lee);
- **C'** (sólo en los 2 primeros gránulos de cada job): la lat/lon de `_interp_geo` pasada por el MISMO
  parche que M. Tiene que dar un record **idéntico** al de C. Si no, el parche (copia, conversión a
  float32, NaN) fabrica diferencias y el probe no mide lo que dice.

Las salidas pasan por `store.append_record` (en un directorio temporal, nunca en `data/`) y por el
**predicado del tablero ejecutado con node** desde `frontend/index.html`, con el runner de
`scripts/banco_paridad.py` (A97). Los argumentos de `calculate_vrp` y `append_record` son los de
`scripts/run_pipeline.py`, y un test los compara por AST. Los ángulos siguen saliendo de
`_interp_geo` en todos los brazos, así que lo único distinto es la posición. El cenit sólo se
persiste, porque A_pix es nadir fijo (A66).

Por gránulo se registra:

- etiqueta y publicación en C y en M, y qué cambió;
- si cambió la detección misma (píxeles anómalos o magnitud del cúmulo), para separar «mismo calor,
  otra etiqueta» de «otro calor»;
- el corrimiento `_interp_geo` menos MxD03 en el píxel del cráter;
- si C reproduce lo guardado en el JSON. Esto mide la deriva de código y se informa, pero no decide.

## Población y muestra

Records MODIS de los 11 Tier A entre el **2026-03-01 y el 2026-10-12**: 5.395 gránulos, 622
publicados hoy. MODIS está completo desde marzo (A119), y el 12 de octubre deja margen para que exista
el L1B Standard. El `inner_radius_km` sale de `frontend/index.html`, que coincide con `volcanoes.yaml`.

**La banda de cada record** es el corrimiento que predice el modelo de #828 para su cenit, acimut y
satélite, más 1 km por la traza y el terreno (`seleccionar_mxd03.py::corrimiento_predicho`). El modelo
dice que el frame *s* recibe la posición del frame 0,99778·s + 2, con geometría de MODIS a 705 km.
Con esta implementación da 2,97 km a 44,7° (#828 midió 2,58) y 2,41 km a 40° (midió 2,21), o sea que
sobreestima un poco, que es el lado seguro para una banda. Predice 4,7 km a 54° y 9,3 km a 65° del
lado del frame 0, y 4,7 km a 65° del otro lado.

El lado del barrido sale del acimut. De noche, Aqua tiene el frame 0 del lado de acimut positivo y
Terra del negativo: así salió en 7 de 7 gránulos de #828. Un record sin ángulos recibe la banda máxima.

| estrato | regla (*m* = distancia al límite, *b* = banda del record) | qué puede cambiar |
|---|---|---|
| **A** | hotspot final con *m* ≤ *b* | la etiqueta, y con ella la publicación |
| **B summit** | sólo el cúmulo con *m* ≤ *b*, record `summit` | la publicación (`centroid_dist_km > inner`) |
| **B far** | sólo el cúmulo con *m* ≤ *b*, record `far` | por reubicación, nada |
| **control** | toda distancia con *m* > *b* + 2 km | nada: si cambia, cambió la detección |
| **fuera** | entre *b* y *b* + 2 km | nada según el modelo; se muestrea para comprobarlo |

Así el control queda limpio también a cenit alto, que era el punto 2c del verificador.

**Censo**, medido entero:

- toda pasada con alerta de MIROVA del tramo: 88, de ellas **46 protegidas** (lectura A, alerta del
  scraper de 1 MW o más; Láscar 40, Nevados de Chillán 5, Villarrica 1);
- los **8 B summit**.

La etiqueta de MIROVA sale de `banco_paridad.indexar_referencia` + `etiquetar` (regla de mínimas SN)
sobre la unión histórica de la referencia. Esa unión se bajó del remoto de Mirova-v1, fijado a los
commits `5db11e1b` (consolidado) y `99dd36ad` (OCR), guardados en `poblacion.json`. La protegida sale
de `clase_mirova.alerta_protegida`.

**Muestra uniforme**, determinista con `sha1("s151-tarea-1.17" + clave)`: A 30, B far 6, control 4 y
fuera 3 por volcán.

| volcán | inner | records | A | B summit | B far | control | fuera | publicadas | protegidas | alertas | muestra | jobs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Láscar | 5 | 426 | 3 | 0 | 202 | 85 | 135 | 16 | 40 | 80 | 96 | 48 + 48 |
| Lastarria | 3 | 432 | 35 | 3 | 271 | 14 | 107 | 21 | 0 | 0 | 46 | 46 |
| Isluga | 5 | 410 | 18 | 0 | 184 | 59 | 147 | 12 | 0 | 0 | 31 | 31 |
| Tupungatito | 7 | 482 | 16 | 0 | 157 | 184 | 125 | 24 | 0 | 0 | 29 | 29 |
| Planchón Peteroa | 3 | 494 | 37 | 2 | 327 | 17 | 108 | 28 | 0 | 0 | 45 | 45 |
| Nevados de Chillán | 5 | 499 | 12 | 0 | 263 | 100 | 121 | 21 | 5 | 6 | 31 | 31 |
| Llaima | 5 | 508 | 21 | 0 | 254 | 92 | 141 | 20 | 0 | 0 | 34 | 34 |
| Villarrica | 5 | 516 | 53 | 0 | 205 | 89 | 169 | 42 | 1 | 2 | 45 | 45 |
| Copahue | 4 | 501 | 15 | 0 | 314 | 35 | 136 | 11 | 0 | 0 | 28 | 28 |
| Puyehue Cordón Caulle | 20 | 551 | 201 | 1 | 3 | 251 | 91 | 361 | 0 | 0 | 41 | 41 |
| Chaitén | 5 | 576 | 70 | 2 | 217 | 102 | 183 | 66 | 0 | 0 | 45 | 45 |
| **total** | | **5.395** | **481** | **8** | **2.397** | **1.028** | **1.463** | **622** | **46** | **88** | **471** | **12 jobs** |

18 records no tienen distancias y quedan fuera de los estratos.

### Tope y tiempo

- **Jobs de 48 gránulos como máximo.** Láscar, con 96 por el censo de alertas, se parte en dos jobs. Es
  el presupuesto extra que pide el verificador, sin alargar ningún job.
- **Tiempo por job.** #828 tardó 143 s en bajar, leer y comparar 7 pares, unos 20 s por par. Acá se
  suman dos corridas de `calculate_vrp` por gránulo, más una tercera (C') en 2 gránulos. Estimado:
  **30 a 50 s por gránulo, 15 a 40 min por job**. El script deja de bajar gránulos a los 70 min (los
  marca `sin_tiempo`) y el job tiene `timeout-minutes: 90` (A15). Con `max-parallel: 4`, los 12 jobs
  toman 3 rondas: **1,5 a 2 h de reloj**.
- **Disco del runner.** Cada par pesa 100 a 150 MB y se borra apenas se usa. El pico queda bajo 1 GB,
  contra 14 GB disponibles.
- **JSON por gránulo.** El archivo del job se reescribe después de cada gránulo, con escritura
  atómica. Si el job muere, lo medido queda y el evaluador cuenta lo que falta.

## Estimador

- **Regla 1 (censo, exacto).** De las protegidas medidas: cuántas publica C y cuántas M, y cuántas
  pasan de 1 a 0 (perdidas) y de 0 a 1 (ganadas).
- **Regla 2 (balance bajo 1 MW).** Mide el cambio en la suma de errores de M contra C, Δ:
  *perdidas − ganadas en las alertas no protegidas* (censo, exacto), más *0→1 − 1→0 en los negativos
  limpios*. El segundo término se estima por volcán y estrato: *N* · *k* / *n*, con *N* la cantidad de
  negativos limpios de ese estrato en la población. El intervalo suma las cotas de Wilson de cada
  estrato. Una alerta perdida y una publicación de más pesan igual (regla 2 de `docs/MISSION.md`).
  Δ < 0 quiere decir que M se parece más a MIROVA.
- **Magnitud (informativa).** Bruto (1→0 y 0→1 observados), neto, cambios por tipo («misma detección,
  otra etiqueta» contra «otra detección»), publicaciones movidas estimadas sobre las 622 del tramo, y
  la tabla volcán × satélite × cenit (0 a 20, 20 a 35, 35 a 50 y más de 50 grados) con el corrimiento
  medido y el predicho. También se listan las alertas movidas con su hora, y cuántas noches tocan
  (A94), para cruzarlas después.

## Criterio (fijado antes de correr)

El veredicto principal se decide en este orden:

1. **INVALIDO**: algún C' difiere de su C.
2. **INCOMPLETO**: pasa cualquiera de estas cuatro cosas:
   - falta la salida de un job pedido;
   - un volcán tiene más de 20 % de su muestra sin medir;
   - queda una protegida sin medir;
   - un job no corrió ningún C'.

   En ese caso se repite el job sobre el mismo código (A108).
3. **PIERDE PROTEGIDA**: al menos una protegida pasa de publicada en C a no publicada en M. Es la
   regla 1: el arreglo no es aceptable en la réplica tal como está.
4. **BANDA CORTA**: en más de 10 % de los gránulos medidos, el corrimiento en el cráter supera la banda
   predicha. La población quedó corta, y el balance no se declara.
5. **SIN CAMBIO OBSERVADO**: ningún gránulo cambia ni etiqueta ni publicación. Se informa igual el
   intervalo de Δ, que con muestras chicas es ancho.
6. **MEJORA**: la cota superior de Δ queda bajo 0.
7. **EMPEORA**: la cota inferior de Δ queda sobre 0.
8. **INDETERMINADO**: en cualquier otro caso.

El cero de Δ no es un umbral elegido: es el punto en que M y C cometen los mismos errores contra
MIROVA (A115, regla 4 de `docs/MISSION.md`).

Anotaciones que no cambian el veredicto:

- **control cambia**: si más de 10 % del control cambia de etiqueta, el arreglo no sólo reubica, sino
  que también cambia qué calor se elige (el ROI y el anillo de fondo dependen de la posición).
- **magnitud**: sigue la lectura de la v1 (2 % y 5 % de las publicaciones), sólo informativa. Nunca
  dice «cambia poco» con la banda corta encendida ni con jobs faltantes.

## Prueba del instrumento

`probar_probe_mxd03.py` arma una escena de 81 × 81 píxeles de 1 km, con un foco de 335 K a 6 km al
norte del cráter (inner 5 km), y la pasa por el pipeline real, `append_record` y el predicado con node.
El workflow la corre antes de cada job, y `tests/test_mxd03_etiquetas_s151.py` también.

| caso | geolocalización «interpolada» | qué debe salir | qué sale |
|---|---|---|---|
| PRESENTE | corrida 2 km al sur de la verdadera | corrimiento 2 km, `summit->far`, `1->0`, C' = C | **2,000 km; C summit a 4,67 km, M far a 6,67 km; `summit->far`, `1->0`; C' = C** |
| AUSENTE | igual a la verdadera | todo `igual`, corrimiento 0, C' = C | **todo `igual`, 0,000 km, C' = C** |
| RELLENO | igual, con MxD03 en NaN en una esquina lejos del cráter | todo `igual` | **todo `igual`, C' = C** |

Límite de la prueba: el corrimiento sintético es una traslación uniforme, no el defecto real, que va a
lo largo del barrido y crece con el ángulo. Lo que prueba es que la cadena detecta un corrimiento y
no lo inventa; el tamaño real lo mide el gránulo.

## Cómo correrlo

```
gh workflow run probe-s151-mxd03-etiquetas.yml --ref main -f preregistro_aprobado=si
```

Sólo con el criterio sellado y el PR mergeado: `workflow_dispatch` no corre desde una rama. Para
repetir jobs sueltos, usa `-f jobs='["Lascar-2"]'` y evalúa en local juntando todos los artefactos:
`python evaluar_mxd03.py <carpeta>`.

- **Autenticación:** sólo `EARTHDATA_TOKEN`; el job `plan` y cada job del probe fallan al instante si
  viene vacío (A71).
- **Concurrencia:** grupo propio; `max-parallel: 4` para no cargar LAADS.
- **Salida:** no hace push. Deja un artefacto por job (`s151-mxd03-etq-<job>`, con el JSON por
  gránulo, el log y la prueba sintética) y el resumen con el veredicto (`s151-mxd03-etiquetas-resumen`).
- **Regenerar la muestra:** `python seleccionar_mxd03.py`, en local, con node y `gh`. Sólo antes del
  sello; después, la muestra es la de `poblacion.json`.

## Límites conocidos

- El L1B que se baja es el Standard 6.1, y parte de los records guardados salió del NRT. La diferencia
  es menor que 0,1 K y cae en la columna de deriva (C contra lo guardado).
- El brazo C corre el código de hoy, no el que produjo cada record. El efecto del arreglo se mide C
  contra M, con el mismo código.
- El negativo del balance se estima con 3 a 30 gránulos por estrato. Si casi nada cambia, el
  intervalo de Δ queda ancho; el lado de las alertas, en cambio, es censo y no tiene ese problema.
- Que MIROVA use MxD03 está SIN VERIFICAR: SP426.5 p. 3 habla de «pixel(s) geolocation» sin nombrar el
  producto.
