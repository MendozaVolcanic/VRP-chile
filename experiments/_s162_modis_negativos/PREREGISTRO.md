# Pre-registro S162 MODIS: lote de negativos `neg_resto` para resolver o refutar el «GANA» del port de MIROVA

> Escrito el 2026-10-24, **antes** de despachar el lote y sin ningún resultado suyo. Lo despacha la sesión
> coordinadora dentro del despacho combinado de la fase 1 (con los brazos de VIIRS 750 y VIIRS 375 que preparan otras
> sesiones). Lo que cambie después del commit de este archivo va en una adenda fechada al final, nunca reescribiendo
> esto. Es MEDICIÓN de sólo lectura: no decide adopción ni toca `pipeline/`, `data/` ni `frontend/`. Decisión de
> Nicolás que lo autoriza: D-36 / D-48 (2026-10-24), lote de 300 a 400 negativos del estrato por sensor.

Todo número de este documento sale de un script de esta carpeta con su salida al lado (`NN_*_salida.txt`).

## 1. Pregunta

En S159 el código operacional de MIROVA (escrito para VIIRS 750, OSF, MIT) portado a MODIS (banda 22 primaria,
geolocalización MxD03, grilla 51 × 51 de 1 km) reprodujo a MIROVA en una muestra de 150 pasadas y le «ganó» a
producción (K): ΔE −44,0, IC [−58,8; −29,5] (`experiments/_s159/portes/INFORME.md` P-1). El verificador con contexto
limpio lo dejó **NO RESUELTO** (`experiments/_s159/portes/verificador/INFORME.md` V-1): en el estrato `neg_resto`
(MIROVA miró y no vio nada, y K tampoco publica; 5.093 pasadas) el port calló en todas las sorteadas, cada una pesaba
unas 134 noches, y con cero eventos el bootstrap re-sortea ceros y no ve nada. Wilson deja el silencio del port hasta
9,4 % contra 0,76 % de K.

**Pregunta**: ¿en qué fracción de las noches en que MIROVA miró y no vio nada, y producción tampoco publicó, publica el
port? ¿Alcanza esa fracción para borrar la ventaja de −44 que el port tiene en los otros estratos?

Físicamente: una noche de `neg_resto` es una escena sin anomalía que ni MIROVA ni producción marcaron. Si el port
publica ahí, está viendo como anomalía algo que MIROVA en el mismo gránulo no vio (fondo topográfico, borde de nube,
ruido de detector). Cada una de esas publicaciones le cuesta al operador una alerta falsa, y en el criterio de MISSION
pesa lo mismo que una alerta débil perdida.

## 2. Población (`01_seleccion.py` → `01_seleccion_salida.txt`)

- **La misma población congelada de S159**, sin reconstruirla: `experiments/_s159/portes/poblacion_completa.json`
  (blob `cb48ddd4`, igual en el commit del lote `0e18e1053` y en `origin/s159-pruebas`). Razón (A90): la población viva
  cambia sola con cada commit NRT; el estrato que se quiere acotar es el de S159, y sus pesos son los de esa población.
- **Pasadas**: MODIS (Terra y Aqua) nocturnas de los 11 Tier A, del 2026-03-01 al 2026-10-21 (A119: en MODIS la tabla
  está completa y es plana desde marzo), sin el 17 al 20 de octubre (las mismas exclusiones de S159). Records de
  `data/mirova_equivalent` de `origin/main 533398f8f` (lo publicado, detector K).
- **Etiqueta de MIROVA**: `scripts/banco_paridad.py::etiquetar`, pareo a ±120 s, regla D-9 en modo SN (en MODIS no
  actúa: `clase_mirova.SENSORES_MINIMA` es sólo VIIRS 375). Negativo limpio = MIROVA miró (hay fila suya a ±120 s) y
  ninguna fila es alerta. Referencia: consolidado `fe2d0a57`, OCR `4ddd5481`.
- **Tabla decide, OCR aparte (A119)**: medido en `01_seleccion_salida.txt`, en MODIS no hay **ninguna** alerta sólo del
  OCR en la población (0), y las 5.093 pasadas de `neg_resto` tienen fila sólo de la tabla (`('CONS',): 5093`), sin
  ninguna fila del OCR. O sea que en este estrato la etiqueta con la tabla sola y la conjunta coinciden.
- **Estrato `neg_resto`**: negativo limpio que decide y en el que el record publicado no pasa el predicado del tablero
  (`pub_prod` = 0). Reproduce **5.093** exacto (`01_seleccion_salida.txt`; S159 `02_seleccion_salida.txt` da lo
  mismo). Clases MODIS completas: `pos_prot` 50, `pos_bajo` 42, `neg_pub` 39, `neg_resto` 5.093.
- **Ya sorteadas en S159**: 38 (no 37): 37 con resultado y 1 «volcán fuera del gránulo» (Cordón Caulle 2026-08-31
  02:50); de las 37, una es escena inválida (Villarrica 2026-03-11 01:30, más de la mitad de la grilla sin dato). Con la
  regla de este pre-registro (§6), S159 tuvo **0 de 36 evaluables**. Las 38 salen del marco.
- **Marco del sorteo**: 5.055 pasadas (`01_seleccion_salida.txt`).
- **Cortes de régimen (A104)** que cruza la ventana: #535 (2026-08-28 23:00 UTC) y el reproceso de K (2026-09-18).
  Afectan sólo a la ETIQUETA de K (el port no depende del pipeline): se informan por tramo y los cubre el control de K
  re-corrido (§6). Los records del estrato los escribieron 6 commits distintos (`01_seleccion_salida.txt`, sha de los
  records), que es justo por qué hace falta ese control.

## 3. Muestra

- **n = 400** del marco, asignación **proporcional** por estrato volcán × cenit (≤ 40°, > 40°; 22 estratos),
  redondeo por mayor resto, semilla **162**. Pesos entre 12,33 y 13,57: la muestra es casi autoponderada y la tasa se
  estima con x / n crudo (S159 usó asignación igual, con pesos dispares; aquí no conviene, porque con pocos eventos el
  peso de cada uno manda). 10 pasadas partidas entran y se informan aparte. Plataforma: Aqua 208, Terra 192. Tramos:
  315 antes de #535, 85 después. Ids 1000 a 1399, para no chocar con los 0 a 309 de S159.
- **Más 13 pasadas de control de instrumento** (peso 0, fuera de todo denominador; §6): 8 protegidas sorteadas y 2
  `neg_resto` de S159, más (adenda del verificador, VCD-10) las 3 protegidas de S159 con cenit sobre 50°, todas de
  Chillán (2026-10-01 08:35, 10-12 07:20 y 10-15 01:05), re-corridas con el mismo id. Total del archivo
  `objetivos_neg_resto_modis.json`: 413 (blob `2d57443d`; el sorteo principal no cambió).
- **Por qué 400 y no 300** (`03_regla_decision_salida.txt`, tabla de planificación, que usa la regla de §5 con las
  filas reales de S159):

| n evaluables | x = 0 | x = 1 a 6 o 7 | x ≥ 7 u 8 |
|---|---|---|---|
| 300 | INDECIDIBLE (IC [−56,1; +0,9]) | INDECIDIBLE | REFUTA desde x = 7 |
| 350 | CONFIRMA (IC [−56,4; −4,8]) | INDECIDIBLE (x 1 a 7) | REFUTA desde x = 8 |
| 380 | CONFIRMA (IC [−56,4; −7,7]) | INDECIDIBLE (x 1 a 7) | REFUTA desde x = 8 |
| 400 | CONFIRMA (IC [−56,5; −9,4]) | INDECIDIBLE (x 1 a 7) | REFUTA desde x = 8 |

  Con 300 el lote **no puede confirmar nada**, ni con cero eventos. Con 400 confirma sólo con cero eventos y deja
  margen para perder hasta unas 20 pasadas no evaluables (a 380 sigue confirmando con 0). La cota de Wilson con 0
  eventos baja de 0,0941 (n 37) a 0,0095 (n 400), unas 48 pasadas del marco, del orden de las 39 de K en todos los
  negativos.

## 4. Brazos

- **PORT, variante `fisica`** (la principal, la única que decide): `experiments/_s159/portes/mirova_port.py` con la
  caja del mismo tamaño en metros que la de VIIRS 750 (ROI2 5 × 5, ROI1 15 × 15 celdas de 1 km), banda 22 primaria con
  21 donde 22 satura, MxD03, remuestreo lineal. Sin un solo cambio respecto de S159 (blobs comprobados en el runner,
  §8).
- Las variantes `pixel`, `sensible`, `fisica_b21` y `fisica_geo5km` las corre el probe igual (no se pueden apagar sin
  modificarlo); son descriptivas y no entran al veredicto.
- **K re-corrido: SÍ.** Razón: el estrato se define por «K no publica» sobre un record escrito por 6 commits distintos
  y a ambos lados de dos cortes de régimen; si el K de hoy publicara en alguna de esas pasadas, la etiqueta del estrato
  estaría mal para esa pasada, y sin re-correrlo no se vería. Costo medido: 1,69 s de 9,1 s por pasada (18,5 %),
  0,19 h de runner en el lote (`04_costo_salida.txt`).

## 5. Métricas y regla de decisión (`03_regla_decision.py`, `07_leer_lote.py`)

- **x** = pasadas evaluables del lote en que el port publica, con el predicado del tablero (`isSummitDetection &&
  isValidDetection && !isThermalArtifact && mirovaEqVrpDisplay > 0`) ejecutado con node sobre el record sintético del
  port, con el mismo código de S159 (`04_analizar.py`: `dist_centroide`, `record_port`, `slim`;
  `banco_paridad.correr_node`). **n** = pasadas evaluables del lote (§6).
- **ΔE total** = ΔE_otros + 0 (las 36 evaluables de S159 en `neg_resto`, conocidas, ninguna encendida) + 5.055 · p.
  - ΔE_otros: la parte de pos_bajo y neg_pub de S159, con las filas congeladas por `02_filas_lote_s159.py`
    (`filas_lote_s159_modis_fisica.json`; reproduce las 8 cuentas de `04_analizar_salida.txt` de S159 y ΔE −44,0).
    Bootstrap estratificado por clase, 20.000 réplicas, semilla 162: IC [−59,50; −29,50].
  - p: Beta(x + ½, n − x + ½) (Jeffreys), una réplica por réplica del bootstrap. Con cero eventos tiene varianza, que
    era el defecto de V-1. Es una convención declarada, no derivada (Brown, Cai y DasGupta 2001, Statistical Science
    16:101, recomiendan Jeffreys y Wilson para p chico).
  - Conservador a propósito: la tasa de las evaluables se aplica a las 5.055 del marco aunque algunas no sean
    evaluables (en esas el port no puede publicar).
- **Veredicto**, con el IC 95 % percentil de ΔE total:
  - **CONFIRMA el GANA** si el IC queda entero bajo 0.
  - **REFUTA** (el port enciende de más; el «GANA» cae) si el IC queda entero sobre 0.
  - **INDECIDIBLE** si contiene 0; se informa además el signo del punto (ΔE = −44,0 + 5.055 · x / n).
  - Con n = 400: CONFIRMA si x = 0; INDECIDIBLE si x = 1 a 7; REFUTA si x ≥ 8.
  - R1 (protegidas perdidas) no cambia: el lote no tiene positivos; queda el 0 de 48 de S159.
- **Controles de la regla** (pasan, `03_regla_decision_salida.txt`): con los datos de S159 (0 de 36) da INDECIDIBLE,
  lo mismo que dijo V-1; con 40 de 400 da REFUTA; con 0 de 400 da CONFIRMA. Ensayo en seco del lector sobre el lote de
  S159 (`07_ensayo_en_seco_s159_salida.txt`): 38 objetivos, 36 evaluables, K re-corrido 36 de 36, x = 0, INDECIDIBLE.
- **Se informa al lado, sin decidir**: R3 (publicación ponderada del port en los 5.132 negativos limpios contra 0,0076
  de K); la «cota conservadora» (suma de la cota superior de ΔE_otros y 5.055 · Wilson superior), que **nunca**
  confirma, ni con 0 de 400 (+18,6): se declara para que nadie la lea como veredicto; x contra K re-corrido en vez del
  publicado; la tasa ponderada; y x / n por volcán, cenit, plataforma, tramo #535 y partidas.

## 6. Controles, que se miran ANTES de leer x (si fallan, la lectura no se hace)

1. **Cobertura (A108)**: estado por pasada contra las 413 pedidas. **No evaluables**, fuera de n y contados aparte:
   estado distinto de `ok` (sin gránulo, volcán fuera del gránulo, error), escena inválida del `.m`
   (`motivo_vacio = escena_invalida`) o grilla con más de la mitad sin dato (`port_estado = grilla_incompleta`). Si
   quedan menos de 350 evaluables, la tabla de §3 dice qué puede resolver el lote (con 300 ya no confirma).
2. **K re-corrido = publicado**: publica igual y `pc.vrp_mw` a 0,001 MW. Toda diferencia se lista; si pasa del 5 %,
   la lectura se informa también contra K re-corrido.
3. **Control de instrumento contra S159** (A116: en un estrato donde se espera 0, hay que mostrar que el instrumento
   puede dar distinto de 0): las 13 pasadas de control dan el mismo `npix` y VRP del port `fisica` que en S159 (a 1e-6
   MW), y las 11 protegidas publican. Si no, la cadena cambió y el lote no se lee.
4. **Prueba sin red del envoltorio en el runner** (job `prueba`, que el lote necesita para arrancar): identidad del
   port con y sin envoltorio, índices y ángulos del recorte y 8 de 8 mutaciones atrapadas por aserción.
5. **Recorte nativo guardado** en todas las evaluables (se informa; no bloquea la lectura de x, sí la tarea MOD-E).

## 7. Costo medido (`04_costo.py` → `04_costo_salida.txt`)

Del lote S159 (resultados por pasada y API de GitHub, `jobs_39712862945.json`): 9,1 s por pasada MODIS (mediana 9,2;
p95 11,0; K incluido), 104 s fijos por job (checkout de 61 s, dependencias 30 s, prueba sin red del probe). Los 6 jobs
MODIS de S159 sumaron 0,551 h. Proyección para 410 pasadas en 8 trozos (413 con los 3 controles agregados: **1,28 h**, medido por el verificador): **1,27 h de runner**, unos 9,5 min por job
(11,1 con el p95 por pasada). El job `prueba` es nuevo: SIN DATO en el runner; en este computador la prueba tarda 61 a
82 s, así que el job debería rondar 3 min (estimado). Guardar un recorte sintético de 136 × 136 tomó 0,04 s
(`05_prueba_envoltorio_salida.txt`).

## 8. Recorte nativo para MOD-E (ablación del bow tie, D28): `envoltorio_nativo.py`

- Corre `probe_portes.py` **sin modificarlo**: envuelve `_ventana` (anota las rebanadas del recorte sólo mientras
  corre `leer_modis`), `pipeline.process_modis.read_modis_l1b` (se queda con el dict del L1B de esa lectura y devuelve
  el mismo objeto, así que K no cambia), `leer_modis` (guarda el recorte sin tocar lo que devuelve) y `procesar` (anota
  `nativo` en el resultado).
- **Por pasada**, `nativo_<id>.npz`: `lat_mxd03`, `lon_mxd03` (float64, la que usa el port), `lat_5km`, `lon_5km`
  (float32, la de producción), `b21`, `b22`, `b31` (radiancias float32 de `read_modis_l1b`, antes de
  `merge_mir_bands`), `linea` y `frame` (int16, índice en el gránulo de cada píxel; barrido = linea // 10, detector =
  linea % 10), `sensor_zenith`, `sensor_azimuth`, `rebanadas`, `forma_granulo`. 48 bytes por píxel sin comprimir
  (medido).
- **Tamaño** (`06_tamano_recortes_salida.txt`, ESTIMADO con un modelo geométrico del barrido; no hay gránulo real en
  Windows): mediana 0,67 MB por pasada y máximo 1,06 MB sin comprimir; **total ≤ 289 MB** más 18 MB de grillas, unos
  **307 MB** de artefacto (cota; con la compresión del sintético, unos 126 MB, optimista). D: tiene 9,7 GB libres hoy:
  cabe holgado. Si D: baja de 3 GB, se para y se avisa.
- **Prueba** (`05_prueba_envoltorio.py` → `_salida.txt`): gránulo sintético de 300 × 280, volcán en (170, 100), foco
  que el port detecta (npix 1, VRP 4,61 MW). Pasa: mismo resultado del port en las 5 variantes y misma grilla con y sin
  envoltorio; las 7 capas guardadas son el píxel (linea, frame) del gránulo; `read_modis_l1b` transparente fuera de
  `leer_modis`. Mutaciones atrapadas por aserción: 6 de 6 en la v1, 8 de 8 desde la adenda 1 (línea corrida en 1, frames al revés, B21 guardada como B22,
  lat de 5 km guardada como la del MxD03, recorte alterado, B31 de la fila siguiente). El sintético **no simula el bow
  tie**: prueba que los índices identifican el píxel, no que haya duplicados.

## 9. Para la coordinadora: qué meter en el despacho combinado

1. Commitear esta carpeta tal cual (el workflow comprueba el blob `2d57443d` de `objetivos_neg_resto_modis.json`).
2. Recomendado: fijar el commit base con un tag antes de despachar, porque hoy sólo lo alcanza la rama
   `s159-portes-disparo`: `git tag s162-base-portes 0e18e1053bb1cdc3fe1a4ef8d0c1aa72bbe60e64 && git push origin
   s162-base-portes`. Su `pipeline/` es idéntico al de `origin/s159-pruebas` y difiere de `origin/main` sólo en
   `pipeline/fetch.py` y `scripts/run_pipeline.py` (`git diff --stat 0e18e1053 origin/main -- pipeline/
   scripts/run_pipeline.py volcanoes.yaml`).
3. Los dos jobs (`prueba` y `probe`, matriz de 8 trozos con `--sensor MODIS --nchunks 8`) de
   `probe-s162-negmodis.yml` son autocontenidos: cada uno hace checkout del commit base, trae esta carpeta del commit de
   disparo con sparse-checkout y comprueba los blobs. Se pueden copiar a `.github/workflows/` tal cual (disparo por push
   a `s162-negmodis-disparo`) o pegarlos como dos jobs más del workflow combinado. Comando por trozo:
   `python experiments/_s162_modis_negativos/envoltorio_nativo.py --objetivos
   experiments/_s162_modis_negativos/objetivos_neg_resto_modis.json --out out --sensor MODIS --chunk <0..7> --nchunks 8`.
   Un trozo con alguna pasada no evaluable sale con código 2 (job rojo) y sube el artefacto igual.
4. Bajar los artefactos a `D:\vrp-trabajo\temporales\s162_negmodis\run_<id>\` y leer:
   `python -I experiments\_s162_modis_negativos\07_leer_lote.py --raiz <árbol del commit base con 04_analizar.py> --art
   D:\vrp-trabajo\temporales\s162_negmodis\run_<id> --s159 D:\vrp-trabajo\temporales\s159_portes\run_39712862945
   --salida experiments\_s162_modis_negativos\07_leer_lote_salida.txt`. El árbol base para leer necesita además
   `experiments/_s159/portes/04_analizar.py`, que está en `origin/s159-pruebas` y no en `0e18e1053`.

## 10. Lo que este pre-registro no hace y lo que queda abierto

- No adopta nada ni propone cambiar producción. No mide día ni otros sensores.
- **ΔE_otros hereda la convención de S159**: bootstrapea `pos_bajo`, que es censo; esa varianza es la de S159, no una
  nueva. Si se quisiera tratar el censo como fijo, el IC se angostaría (no se hace: sería mover la regla).
- Con n = 400 el lote sólo **confirma con cero eventos**; con 1 a 7 queda INDECIDIBLE. Resolver esa franja pediría
  otro lote (decisión de Nicolás), no releer este con otra regla.
- El tamaño de los recortes es una estimación con modelo (SIN DATO de gránulo real); el job `prueba` no tiene costo
  medido.
- SOSPECHA no verificada: ningún control mira si la geolocalización MxD03 de un gránulo viene corrida; el control de
  instrumento contra S159 sólo garantiza que la cadena es la misma.

## Adenda 1 (2026-10-24, antes de despachar): verificador con contexto limpio

Verificador Fable alto (`experiments/_s162_modis_verif_cde/INFORME.md`): MOD-C se sostiene. Los siete scripts
reproducen sus salidas byte a byte, la regla es monótona y sus fronteras no se mueven con 10 semillas ni con N = 5.093,
y el workflow es válido, de sólo lectura y por token. Tres grietas, arregladas antes del despacho:
- **VCD-08**: la prueba del envoltorio era ciega a `sensor_zenith` y `sensor_azimuth` (el sintético los tenía
  constantes). Ahora varían con la línea y el frame, la prueba los compara píxel a píxel y suma dos mutaciones
  (intercambio y cenit corrido): **8 de 8 atrapadas por aserción** (`05_prueba_envoltorio_salida.txt`).
- **VCD-10**: los 8 controles protegidos eran todos de Láscar bajo 41°. Se agregan, sin sorteo, las 3 protegidas de
  S159 con cenit sobre 50° (Chillán). El archivo de objetivos pasa de 410 a 413 (blob `2d57443d`, ya en el workflow); el
  sorteo principal no cambia (diff de `01_seleccion_salida.txt`: sólo la línea de controles).
- **VCD-14**: `07_leer_lote.py` trata `motivo_vacio = sunglint` como no evaluable (de noche no debería ocurrir; si
  ocurre, no es «el port calla»).
Nada de esto toca la pregunta, la muestra, la regla de decisión ni el costo.

## Adenda 2 (2026-10-24, antes de despachar): ronda 2 del verificador

`experiments/_s162_modis_verif_cde/ronda2/INFORME.md`: **se puede despachar tal como está**; los tres arreglos de la
adenda 1 hacen lo que dicen. VCD-15 (gravedad 1): el texto todavía decía 10 controles, 6 de 6 mutaciones y 1,27 h para
413; corregido arriba. El nombre del paso del workflow («6 mutaciones») queda como está: es cosmético, y cambiarlo
separaría este archivo del commit de disparo `ffc1abc1b` que ya armó la coordinadora.
