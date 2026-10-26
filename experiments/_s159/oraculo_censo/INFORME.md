# Censo del oráculo de MIROVA en los negativos limpios de VIIRS 750 (S159, analizado por la sesión nocturna S160)

- Hora del servidor al analizar: 2026-10-22 ~04:25 UTC. Run del censo **39713438252** (rama auxiliar
  `s159-oraculo-disparo`, 32 jobs: 28 verdes, 4 en rojo por pasadas sin procesar declaradas, 20 en total) y run del
  rescate del 12-oct **39715348772** (20 pasadas, las 20 ok). Artefactos en `D:\vrp-trabajo\temporales\s159_oraculo\`.
- Pre-registro: `PREREGISTRO.md` (commiteado antes del disparo, con la adenda §8 antes del run aparte). Analizador:
  `02_analizar.py`, sin cambios de lógica después del disparo (`1259ccc66` sólo agrega una línea de salida y recorta una
  lista, hecho por el agente antes de que terminara el run). Salidas: `02_analizar_salida.txt` (principal, sin el
  rescate) y `02_analizar_salida_con_rescate.txt` (con el estrato del 12-oct reemplazando a sus SIN DATO), más las
  tablas `tabla_por_pasada*.csv`, `negativos_publicados*.csv` y `resumen*.json`.
- Quién: el agente de S159 diseñó, pre-registró y despachó; murió antes de que terminara el run. El análisis lo corrió
  la sesión nocturna (Opus 5.5) con el analizador pre-registrado, sin tocarlo. **Sin verificador todavía.**
- Ventana de todos los números: VIIRS 750 nocturno, 2026-04-01 a 2026-10-21 sin el 18 ni el 19 de octubre; pareo a
  120 s; regla D-9 SN; lectura A de protegidas; predicado «publica» del tablero ejecutado con node (A97).

## En una pantalla

1. **Los cuatro controles pasan, antes de mirar el resultado**: K = producción en 5.620 de 5.620 pasadas ok (publica y
   `pc.vrp_mw` a 0,001 MW); oráculo = frente N en 1.006 de 1.006 comparaciones; las 1.006 perturbaciones del nulo
   cambian la publicación; el oráculo detecta las alertas de MIROVA con razón 1,000 (O-def, 193 de 253) y 0,999 (O-sens,
   241 de 253).
2. **El efecto del oráculo en negativos ya no tiene la cota abierta del frente N** («hasta ~139 más»): sobre los 5.353
   negativos limpios ok, **O-def publica 5 y O-sens 15**, contra **54 de K**.
3. **O-def: PIERDE PROTEGIDAS** (6, todas de Cordón Caulle, 1,00 a 1,43 MW), aunque ΔE sea −60 (rango −62 a −43).
4. **O-sens: GANA EN EL CENSO**: 0 protegidas perdidas y 1 ganada; ΔE **−90** (rango −92 a −73). Con el estrato
   rescatado del 12-oct: 0 SIN DATO, ΔE −92, mismo veredicto.
5. Las etiquetas son descriptivas (pre-registro §4): **no deciden ninguna adopción**, eso es la ola 3 con su propio
   pre-registro y sello de Nicolás.

## Resultado por caja (principal, sin el rescate)

| | negativos publicados (de 5.353 ok) | encendidos / apagados | protegidas perdidas / ganadas | bajo 1 MW sin publicar (K / O) | ΔE (rango por SIN DATO) | etiqueta |
|---|---|---|---|---|---|---|
| K | 54 (1,01 %) | | | 65 | | |
| O-def | 5 (0,09 %) | 1 / 50 | 6 / 0 | 65 / 54 | −60 (−62 a −43) | PIERDE PROTEGIDAS |
| O-sens | 15 (0,28 %) | 7 / 46 | 0 / 1 | 65 / 14 | −90 (−92 a −73) | GANA EN EL CENSO |

- Sensibilidad declarada (distancia desde `volcanoes.yaml` en vez del centro del TIF): O-def ΔE −59, O-sens 16
  negativos y ΔE −88; mismas etiquetas.
- Por volcán, los 15 negativos de O-sens: Tupungatito 5, Isluga 3, Láscar 3, Cordón Caulle 3, Llaima 1. Los 54 de K:
  Cordón Caulle 25, Isluga 10, Láscar 9, Tupungatito 4, Chaitén 3, y 1 en Llaima, Chillán y Villarrica. O-sens publica
  en Tupungatito 5 negativos donde K publica 4 (el único volcán donde el oráculo publica más), con píxeles a 4,8 a
  6,7 km del centro y temperaturas de 226 a 263 K.
- Por cenit: O-sens 11 de 1.891 con cenit ≤ 40° y 4 de 3.568 sobre 40°; K 41 y 13.
- Bajo 1 MW: O-sens pierde 8 que K publica (Cordón Caulle 4, Isluga 2, Láscar 1, Tupungatito 1) y gana 59.
- Las 14 alertas sólo OCR anteriores al 13-jun (no deciden, A119): K publica 14, O-def 13, O-sens 14.
- Pasadas fuera del gránulo (el píxel más cercano al centro a más de 5 km): 106, todas negativos limpios; no son SIN
  DATO y ninguna caja publica en ellas.

## Estrato rescatado del 12-oct (adenda §8)

Las 20 pasadas de los cuatro gránulos reprocesados por NASA (VJ202MOD 05:12 y 05:18, VNP02MOD 05:48 y 05:54) corren
todas: 17 negativos limpios y 3 alertas (la protegida de Chillán 05:18, Isluga 05:48 y Chillán 05:54). Ninguna caja
publica en esos negativos; O-sens detecta la protegida de Chillán. El pre-registro decía que el control 1 no aplica
ahí (producción procesó el archivo original); igual da 0 diferencias en las 5.640 pasadas ok, o sea que K sobre el
archivo nuevo publica lo mismo que producción sobre el viejo en esas 20.

## Qué NO dice

- No es un A/B de adopción ni toca producción. Es un censo de sólo lectura de un oráculo validado contra Octave.
- Sólo VIIRS 750. No dice nada de VIIRS 375 ni de MODIS (ver `experiments/_s159/portes/`).
- La etiqueta positiva que decide después del 13-jun incluye alertas del OCR. El analizador no da la lectura con la
  tabla de `latest.php` sola, que Nicolás considera la más creíble; queda como seguimiento (se puede sacar de
  `tabla_por_pasada*.csv` si trae el canal de cada alerta, SIN VERIFICAR que lo traiga).
- Las 6 protegidas que pierde O-def son las mismas de Cordón Caulle que ya había visto el frente N: la caja por
  defecto las deja fuera y la sensible no. Que sea porque el campo difuso del lacolito (A68) cae fuera de la cumbre de
  7 × 7 es SOSPECHA: este análisis no lo midió.

---

## Secciones agregadas por el agente del frente (S159, 2026-10-22)

Nota de proceso: el agente del frente no murió; el run tardó 1 h 31 min (02:48:59 a 04:19:34 UTC) y siguió esperando
con un único `gh run view` cada 5 a 10 min. Lo de arriba lo escribió la sesión nocturna con el analizador pre-registrado;
lo revisé contra mi propia corrida de `02_analizar.py` sobre los mismos artefactos, que da **el mismo texto** (comparado
ordenando líneas y sin finales de línea: 0 diferencias), así que no reemplacé las salidas commiteadas. Lo que sigue son
las piezas que el encargo pedía y que faltaban: hallazgos en formato, pasadas partidas, comparación con F, por qué no se
publica lo que el oráculo detecta, candidatas para §12 y VERIFICADO LIMPIO. No toqué `verificador/` (lo está escribiendo
otra sesión). Scripts nuevos, todos post hoc y descriptivos: `03_detalle.py`, `04_por_que_no_publica.py`,
`05_pixeles_fuera_del_recuadro.py`, con sus `_salida.txt`. Resultados crudos de los dos runs en
`resultados_crudos.tar.gz` (0,7 MB; los mismos JSON de `D:\vrp-trabajo\temporales\s159_oraculo\`).

Ventana de todo número: VIIRS 750 nocturno, 2026-04-01 a 2026-10-21 sin el 18 ni el 19 de octubre, población del frente
N (5.746 pasadas, 5.476 negativos limpios, 256 alertas que deciden). Denominador de negativos: 5.353 ok (5.476 menos 106
fuera del gránulo y 17 SIN DATO); con el rescate, 5.370.

### Hallazgos, de mayor a menor gravedad

#### C-1. El código de MIROVA con la caja por defecto pierde 6 protegidas y 33 alertas débiles que producción publica, casi todas de Cordón Caulle

- SCRIPT:SALIDA: `02_analizar.py` → `02_analizar_salida.txt`, bloque `== O-def` (líneas «protegidas» y «bajo 1 MW perdidas»).
- QUÉ PASA: en Cordón Caulle la anomalía no está en el cráter sino repartida en el campo del lacolito, a 4,6 a 10,5 km
  del centro según MIROVA. La caja por defecto pone los umbrales sensibles sólo en la cumbre de 7 × 7 celdas (±2,6 km)
  y el resto con umbrales de escena, que esos píxeles débiles no pasan. En el censo: 6 protegidas perdidas (1,00 a
  1,43 MW, las mismas que vio N) y 33 de las alertas bajo 1 MW que K publica (27 de Cordón Caulle).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy. Si el paquete de la ola 3 usara la caja por defecto, el operador dejaría
  de ver alertas de Cordón Caulle de 1 MW o más que MIROVA sí publica (regla 1 de MISSION).
- CÓMO REPRODUCIRLO: `python 02_analizar.py --art D:\vrp-trabajo\temporales\s159_oraculo\censo_39713438252`; por ejemplo
  Cordón Caulle 2026-06-07 05:54 (MIROVA 1,2 MW).
- CONFIANZA: CONFIRMADO (censo: 78 de 79 protegidas medidas; 79 de 79 con el rescate). Que la causa sea el lacolito
  fuera de la cumbre de 7 × 7: SOSPECHA apoyada en las distancias de MIROVA (N-3), no medida aquí píxel por píxel.
- GRAVEDAD: 4 (con esta caja el paquete no se puede adoptar).

#### C-2. Contado entero, el oráculo con el recuadro sensible publica 15 negativos limpios de 5.353, no «hasta 139»: la cota abierta de N queda cerrada

- SCRIPT:SALIDA: `02_analizar_salida.txt`, bloque `== O-sens`; `resumen.json`.
- QUÉ PASA: de las noches en que MIROVA miró y no vio nada, producción (K) publica 54 (1,01 %) y el código entero de
  MIROVA con el recuadro sensible publica 15 (0,28 %): 7 que K no publica, y 46 de las de K apagadas. Con las alertas:
  0 protegidas perdidas, 1 ganada, 59 alertas bajo 1 MW ganadas y 8 perdidas; ΔE = (14 + 15) − (65 + 54) = **−90**
  (rango por SIN DATO −92 a −73; con el rescate, −92). La predicción del verificador de N era ≈ 12 con cota hasta ~139;
  salieron 15: 12 ya estaban en las pasadas que N midió y **3 vienen de los 5.303 negativos sin ningún píxel de
  producción** (Tupungatito 2026-04-16 05:24 y 2026-06-10 04:54, Cordón Caulle 2026-10-09 06:54), que N no podía ver
  por muestreo. Contra F (fondo del código sobre nuestra detección, censo de N): F enciende 60 y queda en ΔE +12; el
  paquete entero queda en −90. Por cenit: O-sens 11 de 1.891 (≤ 40°) y 4 de 3.568 (> 40°); K 41 y 13.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy. Con el paquete, el operador vería en seis meses 39 puntos de cumbre menos en
  noches sin actividad (de 54 a 15) y 51 alertas débiles más en neto (59 ganadas, 8 perdidas).
- CÓMO REPRODUCIRLO: igual que C-1; la lista de los 15 está al final del bloque `== O-sens`.
- CONFIANZA: CONFIRMADO (censo; controles 1 a 4 en verde). Condicionado a C-3 y C-4.
- GRAVEDAD: 4 (es el número que pedía el pre-registro de adopción de la ola 3).

#### C-3. El «gana» de O-sens descansa en el radio interior del tablero: el código detecta 43 negativos y 28 no se publican sólo por estar `far`

- SCRIPT:SALIDA: `03_detalle.py` → `03_detalle_salida.txt`; `04_por_que_no_publica.py` → `04_por_que_no_publica_salida.txt`.
- QUÉ PASA: el código de MIROVA con el recuadro sensible marca píxeles en 43 de los 5.353 negativos. El predicado del
  tablero publica 15; los otros 28 tienen VRP positivo y no son cirrus: no se publican sólo porque el centroide cae más
  lejos que el `inner_radius_km` del tablero, medido desde el centro del TIF (Lastarria 6, Chillán 5, Copahue 4,
  Llaima 3, Villarrica 3 y otros; lista en `04_por_que_no_publica_salida.txt`). Además el código detecta también
  **fuera** del recuadro de 21 × 21: la celda con `box == 0` entra como región de escena (`m0`) y sólo se excluye el
  borde de la matriz (`experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py:140-145`); por eso hay una detección de
  Lastarria 2026-08-25 05:48 con centroide a 22,8 km. Si el paquete publicara todo lo que el código detecta, sin
  filtro de distancia (no sabemos qué filtro usa MIROVA para publicar), los negativos serían hasta 43 (0,80 %) y ΔE
  quedaría en −62 o menos (las alertas `far` que se ganarían lo bajarían más; no medido).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy; decide si el paquete necesita el filtro `summit` del tablero.
- CÓMO REPRODUCIRLO: `python 04_por_que_no_publica.py --art D:/vrp-trabajo/temporales/s159_oraculo/censo_39713438252`.
- CONFIANZA: CONFIRMADO (medido y leído). Que MIROVA publique sin filtro de distancia: SOSPECHA, sin dato.
- GRAVEDAD: 3.

#### C-4. El record sintético junta todos los alertados en un centroide: un píxel lejano hace perder una alerta de Láscar

- SCRIPT:SALIDA: `05_pixeles_fuera_del_recuadro.py` → `05_pixeles_fuera_del_recuadro_salida.txt`.
- QUÉ PASA: el record del pre-registro (función `record_oraculo` de N) promedia la posición de todos los alertados. En
  Láscar 2026-08-26 05:48 (alerta de MIROVA 0,37 MW, K publica 0,172) el código marca la cumbre y además un píxel fuera
  del recuadro; el centroide se corre más allá del radio interior y el tablero no la publica, con las dos cajas. Sin los
  píxeles de fuera del recuadro se publica. Es 1 de las 8 alertas bajo 1 MW que O-sens «pierde» y 1 de las 33 de O-def:
  efecto de cómo se armó el record, no del código de MIROVA. Mezclas en todo el censo: 1 pasada por caja; ningún
  negativo cambia. Aproximación declarada: el VRP del recorte se reparte por radiancia, sin recalcular el fondo (no
  cambia el signo, que es lo que lee el predicado).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python 05_pixeles_fuera_del_recuadro.py --art D:/vrp-trabajo/temporales/s159_oraculo/censo_39713438252`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2 (mueve ΔE en 1; para la ola 3, el record del paquete debe salir de un cúmulo, no
  del centroide de todos los alertados).

#### C-5. 106 de los 5.476 «negativos limpios» son pasadas que no miran el volcán (1,9 %), y 44 más no ven la cumbre

- SCRIPT:SALIDA: `02_analizar_salida.txt`, líneas «fuera del granulo» y «por partida» de cada caja.
- QUÉ PASA: el recuadro de 25 km de producción toca el borde del gránulo y el record existe, pero el píxel del gránulo
  más cercano al volcán está a más de 5 km (hasta 23 km): MIROVA tampoco miró el cráter y su fila RUTINA no dice «no
  había nada». Es N-8 generalizado: N vio 2 de 143 (1,4 %), el censo da 106 de 5.476. Además 44 pasadas tienen celdas
  sin dato en la cumbre de 7 × 7 («sin cráter») y 174 están partidas pero con la cumbre entera. **Ni K ni el oráculo
  publican en ninguna de esas 324**; sacarlas sólo achica el denominador (K 54 de 5.309, O-sens 15 de 5.309). Coincide
  con `experiments/_s159/negativo_crater/INFORME.md` (la regla sólo saca denominador), medido aquí por otra vía (la
  cobertura del gránulo en la grilla, no `diag_n_bg_anillo`).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: igual que C-1.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

#### C-6. En los gránulos reprocesados del 12-oct, K reproduce a producción también sobre el archivo nuevo, y el código mide la protegida de Chillán en 0,80 de MIROVA

- SCRIPT:SALIDA: run 39715348772, `probe_rescate.log` del artefacto, y `02_analizar_salida_con_rescate.txt`.
- QUÉ PASA: las 20 pasadas de los cuatro gránulos que NASA reprocesó el 19-oct bajaron de la nube de LAADS
  (`data.laadsdaac.earthdatacloud.nasa.gov/prod-lads/...`, la misma ruta que CMR da a producción; `/archive/allData/`
  redirige al login de URS y devuelve una página de 10 KB, lo que hizo fallar los intentos 39713687687 y 39714551225).
  K publica igual y con el mismo `pc.vrp_mw` que producción en las 20 (el control no aplicaba, y aun así pasa).
  Chillán 05:18, protegida: MIROVA 8,44 MW, oráculo 6 px 6,753 (0,80), K 3,46. Isluga 05:48: 0,244 contra 0,24.
  Chillán 05:54: 0,417 contra 0,40. Las dos cajas publican las tres.
- CÓMO REPRODUCIRLO: push de `probe-s159-oraculo-rescate.yml` a una rama auxiliar con `EARTHDATA_TOKEN`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1 (cierra los SIN DATO; la protegida queda medida).

### Cuántas pasadas quedaron SIN DATO y por qué

20 en el censo, todas de los gránulos reprocesados del 2026-10-12 (VJ202MOD 05:12 y 05:18, VNP02MOD 05:48 y 05:54): CMR
da la entrada vieja y la búsqueda por ventana no encuentra otra (`sin_granulo_*|sin_granulo_por_ventana`). Las 20 se
recuperaron en el run aparte (C-6): con el rescate, 0 SIN DATO. Los 4 jobs en rojo del censo son los que tenían esas
pasadas (el probe sale 2 si falta una; `volcan_fuera_del_granulo` no cuenta como falta).

### Lo que no cubre

- MIROVA no publica con el predicado del tablero: «publica» aquí es nuestra regla aplicada al record del código. Cómo
  decide MIROVA publicar (distancia, umbral de VRP) sigue sin conocerse (C-3).
- El recuadro sensible es una aproximación de la ROI de MIROVA en Cordón Caulle y Tupungatito (N-3); la caja real por
  volcán no se conoce.
- Sólo VIIRS 750 nocturno. El canal de la alerta (tabla u OCR) no se separó (lo anota la sección de arriba).

## Candidatas para BEYOND_MIROVA_EXTENSIONS §12

| qué | por qué podría ser mejor | evidencia | estado |
|---|---|---|---|
| Separar «no miré» de «no vi» en el record (cobertura del gránulo sobre la cumbre) | 106 pasadas (1,9 %) no miran el volcán y 44 no ven la cumbre; MIROVA las lista como RUTINA. Un SDA que lo declare es más honesto con el operador | C-5; medido con la grilla del gránulo, sin parámetros nuevos | idea, barata |
| Mostrar en el experimental lo que el código de MIROVA detecta fuera del radio interior | 28 negativos con detección `far` (Lastarria 6, Chillán 5, Copahue 4 y otros); si son fumarolas o campos tibios reales son categoría b (A54) | C-3; validar contra OVDAS y SWIR, no contra MIROVA | hipótesis |
| Los píxeles de un píxel que nuestro segundo pase ve y el código no (de N) | el censo confirma que el código no los publica (O-def 1 de los 60 de N, O-sens 4) | N, apéndice; este censo | hipótesis (ya anotada por N) |

## VERIFICADO LIMPIO

- **K = producción en todo el censo**: 5.620 de 5.620 pasadas ok (5.640 con el rescate), misma publicación con el
  predicado del tablero y mismo `pc.vrp_mw` a 0,001 MW. `python 02_analizar.py --art <censo>`, línea «control 1».
- **El oráculo es determinista entre corridas**: 1.006 comparaciones (503 pasadas × 2 cajas) iguales a N en número de
  píxeles y VRP a 1e-6 MW. Línea «control 2». Vale como control de regresión, no de verdad.
- **El contador ve lo que dice ver**: 956 perturbaciones de records que publican (VRP a 0 y `far`) dejan de publicar y 50
  cúmulos inyectados en negativos pasan a publicar; 0 excepciones. Línea «control 3».
- **El oráculo reproduce la magnitud de MIROVA en el censo entero**: O-def 193 de 253 alertas, razón 1,000 [0,984,
  1,008]; O-sens 241 de 253, 0,999 [0,973, 1,010]. Línea «control 4».
- **Ninguna publicación del oráculo en negativos es ambigua por la triangulación** (banda de 20 semillas que no toca
  0): `03_detalle_salida.txt`, última línea.
- **Cobertura**: 5.746 de 5.746 objetivos con resultado; 0 pasadas perdidas sin explicar (106 fuera, 20 SIN DATO
  declaradas y rescatadas).
- **Nada en `pipeline/`, `data/` ni `frontend/`**: los dos workflows son de sólo lectura y viven en ramas auxiliares
  (`s159-oraculo-disparo`, `s159-oraculo-rescate`) que no se mergean.
