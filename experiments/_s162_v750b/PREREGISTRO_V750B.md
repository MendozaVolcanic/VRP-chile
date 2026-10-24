# Pre-registro V750-B (S162): la región sensible (ROI) del código de MIROVA, por volcán, en VIIRS 750

Estado: **v3, en tercera vuelta corta sobre el delta v2 a v3** (con conforme sin cambios en la regla queda sellada, D-48), corregido tras dos verificadores limpios: el primero (Fable 5.1,
`verificador/VERIFICADOR_PREREGISTRO_V750B.md`, «listo para sello con cambios») y la segunda vuelta (Sonnet,
`verificador_v2/VERIFICADOR_V2_PREREGISTRO_V750B.md`, «conforme con cambios»); qué cambió en cada vuelta, en §12. No se despacha
nada hasta (1) el sello, (2) que la sesión del instrumento entregue la cobertura contra la referencia (fase 0, programa
§8.1, #904) y (3) que la coordinadora (S162, sesión «Retomar») lo meta en el despacho combinado de la fase 1. Autor:
sesión hija VIIRS 750 (loop `tasks/LOOP_VIIRS750.md`), 2026-10-24. Programa:
`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §2 y §3.

**Decisiones resueltas por la coordinadora (S162) bajo D-48** (Nicolás, 2026-10-24: «sobre las decisiones mías haz lo
que tú recomiendes»), informadas a Nicolás para que pueda revertirlas: (1) en T decide sólo la tabla, en O tabla más
OCR; (2) sin ganador nunca se elige un brazo que PIERDE o BLOQUEA; (3) la distancia del record se mide desde el cráter,
como producción; (4) brazo B5 con la lectura del comentario del `.m` (corona sensible, centro conservador). DN-2 pasa a
ser **paso obligatorio de la lectura**: si gana B2 o B4, antes de proponer la adopción se documenta que es fidelidad al
`.m` (la ROI por volcán que declaran sus l. 105-125) y no un gate nuestro (A85). El sello queda dado cuando la segunda
vuelta del verificador (otro modelo) dé conforme.

## 1. La pregunta, como geólogo

El código de MIROVA mira cada volcán en una grilla de 67 × 67 celdas de 750 m centrada en su propio punto (el centro
del TIF). Dentro de esa grilla hay una zona sensible (5 sigma, piso 0,003) y el resto con umbrales conservadores (10
sigma, piso 0,02). El `.m` publicado no trae la matriz de zonas de cada volcán: trae una sola matriz de ejemplo (una
pasada de 2023, con la zona sensible en el 7 × 7 central) y un comentario (l. 105-125) que dice que las zonas «can be
shifted, reshaped or resized» por volcán. El comentario además describe las zonas al revés que la matriz de ejemplo:
una ROI central conservadora rodeada de una corona extendida sensible. Eso importa en dos volcanes:

- **Cordón Caulle**: el calor está en el campo del lacolito, a 4,6 a 10,5 km del centro según MIROVA; el cráter de
  `volcanoes.yaml` está a 7,6 km. Con la zona sensible de 7 × 7 el código pierde 6 protegidas que MIROVA sí publicó
  (censo S159, `origin/s159-pruebas:experiments/_s159/oraculo_censo/INFORME.md`, C-1).
- **Tupungatito**: el cráter está a 4,9 km al NW del centro; en V750-C las 17 cumbres tibias que K ve y el código calla
  caen ahí, en la zona conservadora (`experiments/_s162_v750c/verificador/VERIFICADOR_V750C.md`, V4 y V9).
- (Planchón-Peteroa: cráter a 2,0 km al S del centro.)

La pregunta es qué zona sensible reproduce a MIROVA **en las dos direcciones**: publicar sus alertas (sobre todo las
de 1 MW o más) y callar en las noches en que no vio nada. Ningún brazo es «la ROI de MIROVA», que no conocemos: son
lecturas candidatas, y gana la que mejor reproduce lo que MIROVA publicó y calló. El resultado fija la ROI del paquete
V750-A.

Lo que ya se sabe (se usa como control, no se re-mide como hallazgo): en el censo S159 la caja del ejemplo pierde 6
protegidas y publica 5 negativos limpios de 5.353; la sensible de 21 × 21 no pierde ninguna, gana 1 y publica 15 (ΔE
−90 contra K).

## 2. Brazos

Todos son el código de MIROVA (port de R2, `experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py` en `origin/main`,
validado contra Octave en 791 de 791 escenas, S159 O1) sobre la grilla GEO con interpolación lineal (esquina
`X0 ± 25.000 m`, paso 750, S159 GEO), sin compuerta, sin recorte, con su fondo y su suma. Sólo cambia la matriz de
zonas (en el `.m` la zona 0 y la 1 comparten los umbrales conservadores, l. 389-395; lo único que decide es dónde está
la zona 2, la sensible):

| brazo | zona sensible (BOX == 2) | zona conservadora |
|---|---|---|
| **B0** caja del ejemplo | 7 × 7 en el centro de la grilla | el resto |
| **B1** sensible | 21 × 21 en el centro | el resto |
| **B2** caja en el cráter | 7 × 7 centrada en la celda del cráter de `volcanoes.yaml` (`vent_lat`, `vent_lon`) | el resto |
| **B3** círculo | círculo de radio `inner_radius_km` del tablero (`banco_paridad.inner_desde_html`) en el centro | el resto |
| **B4** sensible en dos volcanes | B1 en Cordón Caulle y Tupungatito; B0 en los otros nueve | |
| **B5** lectura del comentario | corona: el 21 × 21 menos el 7 × 7 central (que queda conservador) | el 7 × 7 central y el resto |
| **K** | producción (`calculate_vrp` de `pipeline/process_viirs_mod.py` sobre el mismo gránulo) | |

Brazos de diagnóstico que **no deciden V750-B** (confirman V750-C, mismo gránulo y misma corrida):

| brazo | qué |
|---|---|
| **N0** nativo, caja del ejemplo | el código sobre la ventana NATIVA del gránulo (67 × 67 píxeles del barrido alrededor del píxel más cercano al centro), con las zonas definidas **en km** desde el centro de la grilla (semilados 2,625 y 7,875 km) para que midan lo mismo que en la grilla a cualquier ángulo de barrido |
| **N1** nativo, sensible | ídem con la sensible de 7,875 km de semilado |

N0 y N1 corren sólo en el subconjunto **S_C** (marcado en `objetivos_v750b.json` con `en_sc`): las cumbres de K en 0,0
MW (negativas y con alerta), las alertas que deciden y 300 negativos limpios sin cúmulo de K sorteados con semilla 162.
Se informan por tramo de 10° de cenit.

**Insumos que el run guarda**: la grilla GEO lineal (`m13`, `m15`, float32) de todas las pasadas y la ventana nativa
(`lat`, `lon`, `m13`, `m15`, float32, más la esquina fila y columna) de las de S_C. Tamaño estimado (SOSPECHA, del
tamaño de las grillas de N): ~170 MB y ~30 MB comprimidos.

## 3. Población y ventanas (programa §2, A119, A104)

- VIIRS 750 nocturno (`dayflag = 0`), los 11 volcanes Tier A, pasadas con record de producción y fila de la referencia
  de MIROVA a ±120 s. Lista: `objetivos_v750b.py` (corre `experiments/_s159/n/01_poblacion.py` de `origin/main` sin
  cambiar su lógica, con la ventana extendida), regenerada y commiteada antes del despacho con su sha256.
- **T** (decide la tabla sola): 2026-04-01 a 2026-06-12. **O** (decide tabla más OCR; la tabla sola al lado):
  2026-06-13 a 2026-11-02 12:59 UTC. Fuera en todos los brazos: el **12-oct** (opción «excluido» del programa: no se
  arma el rescate de LAADS), el 13 y del 17 al 20 de octubre (D-29). Las pasadas sin gránulo en el record salen de la
  lista y se listan como SIN DATO declarado. Toda la ventana es anterior al cese de Suomi NPP.
- Cortes informados por tramo: #535 (no separa brazos), adopción de K (2026-10-18 09:57 UTC).

## 4. Etiquetas, cobertura y record

- Alerta, protegida (lectura A, ≥ 1 MW), regla SN (D-9) y negativo limpio: las de `01_poblacion.py`
  (`banco_paridad`, `scripts/clase_mirova.py`). **Canal que decide** (programa §2): en T, sólo las filas de la tabla
  (`source == "CONS"`; una alerta sólo del OCR no entra y una protegida sólo por el OCR no es protegida); en O, tabla
  más OCR. Si la sesión del instrumento ya mergeó el arreglo de FALSO_POSITIVO, se informa con y sin.
- **Cobertura antes del veredicto**: (a) «no observada», fuera del denominador y contada aparte: volcán fuera del
  gránulo, o celdas sin dato en el 7 × 7 alrededor del **cráter** (no del centro de la grilla); (b) **SIN DATO**, con
  nombre: pasada que no bajó, sin gránulo, grilla incompleta o error del brazo K. Si hay más de 2 % de SIN DATO o una
  protegida SIN DATO, no se lee el veredicto: se relanzan sólo esas pasadas (`SOLO`) y se vuelve a leer; si siguen
  faltando, se declaran y la coordinadora decide con Nicolás si se lee igual.
- **Record de cada brazo del oráculo**: el cúmulo 8-conexo del píxel alertado más radiante (corrige C-4 del censo); su
  VRP es el del `.m` sobre la unión de los alertados; su distancia se mide desde la posición del **cráter** de
  `volcanoes.yaml` en la grilla, igual que producción, que mide desde `get_detection_anchor`. Se informa al lado
  cuántas publicaciones cambiarían midiendo desde el centro de la grilla. Predicado «publica»: el del tablero,
  ejecutado con node (A97).
- **Record de K**: el que produce el probe; si K no arma record (ROI vacía), cuenta como «K no publica».

## 5. Métricas (programa §2)

Por brazo, contra MIROVA, en T, en O y en T ∪ O, con el canal que decide y, al lado, con la tabla sola y con todo:

- **P1** protegidas perdidas (veto): protegida que el brazo no publica.
- **P1b** cruces de 1 MW en las dos direcciones (informativo).
- **P2** E = alertas bajo 1 MW sin publicar + negativos limpios publicados; la diferencia contra B1 se decide con la
  **prueba de signos por bloque noche-volcán** (D-45: `prueba_signos_p2` y `regla_signos_p2` extraídas con `ast` de
  `experiments/_s157_prereg_d25/evaluar_d25.py` del tag `s161-d25-lectura`, sha256
  `2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747`, que el analizador comprueba: exacta hasta 20
  bloques; GANA o PIERDE con p ≤ 0,05; BLOQUEA si el neto va en contra sin llegar; SIN SUSTRATO con 4 bloques o menos).
- Descriptivas: razón VRP brazo/MIROVA en alertas publicadas; Cordón Caulle, Tupungatito y Planchón-Peteroa aparte;
  por tramo de 10° de cenit.
- **Sin placebo de ganancia**: el placebo K × 1,2 del programa §2 es del comparador de magnitud M (D-44), y V750-B no
  decide por M (las razones son descriptivas). M y su placebo van en V750-A.

## 6. Regla de decisión (escrita antes de ver los datos)

1. **Elegible**: P1 = 0 en T ∪ O con el canal que decide (la condición «y P1 = 0 en O con la tabla sola» que tenía la
   v2 es redundante: toda protegida de la tabla en O ya es protegida con el canal que decide; se deja en el código y
   no veta nada aparte). Un brazo que pierde una protegida no entra al paquete, aunque gane en P2.
2. **Gana**: un elegible distinto de B1 que en P2 contra B1, sobre T ∪ O con el canal que decide, da GANA, y que con
   la tabla sola (T ∪ O) **no es peor** que B1. «No es peor» = GANA o EMPATE, o SIN SUSTRATO con el neto en 0 o a
   favor (con 4 bloques o menos la prueba no puede rechazar, y un neto en contra no se premia). Si ganan dos o más,
   el de menor E (T ∪ O, canal que decide). Multiplicidad: se contrastan hasta cinco brazos contra B1, cada uno al
   5 % de una cola; no se corrige (los brazos están muy correlacionados y todos los candidatos ya cumplen P1 = 0), y
   se declara: la probabilidad de que algún brazo gane sólo por azar es mayor que 5 %.
3. **Si ninguno gana**: se elige entre B1 y los elegibles que **no son peores** que B1 ni con el canal que decide ni
   con la tabla sola (definición del punto 2: nunca uno que PIERDE o BLOQUEA, ni uno SIN SUSTRATO con el neto en
   contra), por cercanía al `.m`, en este orden: B4 (cambia sólo dos volcanes respecto del ejemplo), B2
   (conserva la caja de 7 × 7 y sólo la mueve), B5 (la lectura del comentario del `.m`), B1, B3 (B3 usa nuestra
   configuración, no la de MIROVA). Razón: a igual desempeño manda la fidelidad al código (decisión de Nicolás del
   2026-10-21). Si B1 tampoco es elegible y nadie más lo es: NINGÚN BRAZO ELEGIBLE, y V750-A no se arma con esta ROI.
4. P1b no decide.
5. **Paso obligatorio de la lectura (D-48)**: B2 y B4 son ajustes por volcán. MISSION excluye gates por volcán cuando
   son nuestros (A85), pero aquí el ajuste es de MIROVA (el comentario del `.m` lo declara). Si el elegido es B2 o B4,
   antes de proponer su adopción se documenta que es fidelidad al `.m` y no un parche nuestro.

## 7. Controles (todos dentro de la compuerta: si uno cae, no se imprime veredicto)

| control | qué tiene que dar | si no |
|---|---|---|
| nulo del contador | toda perturbación de un record publicado (VRP a 0, `far`) deja de publicar y todo cúmulo inyectado publica | el predicado no mide |
| K = producción | publica igual y `pc.vrp_mw` a 0,001 MW; las distintas salen de todos los brazos y se listan; si son más del 1 % o hay una protegida, se detiene | el run no mide producción |
| B0 y B1 = censo S159 | mismo número de píxeles, mismas posiciones y VRP a 1e-6 que el censo en las pasadas comunes (artefactos del censo en `D:\vrp-trabajo\temporales\s159_oraculo\censo_39713438252`, objetivos en `origin/s159-pruebas`); obligatorio | el oráculo cambió |
| control positivo | B0 pierde al menos 1 protegida de Cordón Caulle **y B1 publica 3 o más de ésas** (en el ensayo: 7 y 7) | el instrumento no ve la ROI, o el oráculo está muerto |
| control negativo | B4 contra B1 sólo en Cordón Caulle y Tupungatito, donde son idénticos por construcción: SIN SUSTRATO con 0 bloques | el evaluador cuenta diferencias que no existen |
| cobertura | §4: SIN DATO bajo 2 % y ninguna protegida | se relanza antes de leer |
| N0 y N1 | se informa, por grupo y tramo de cenit, cuántas pasadas de S_C detectan en el píxel de K y con algún píxel, al lado de B0 y B1 (diagnóstico de V750-C; no compara máscaras índice a índice porque las geometrías no coinciden, y no cierra la compuerta) | |

## 8. Predicciones (para poder fallar)

- B0: pierde 6 o más protegidas (todas de Cordón Caulle); no elegible. (Verificador v3, VB3-04: esto no es una
  predicción que pueda fallar con veredicto, porque el control positivo de §7 exige que B0 pierda alguna; si no la
  pierde, no hay veredicto.)
- B1: 0 protegidas perdidas; negativos limpios del orden de 15 en 5.353 (censo) más lo que agregue la ventana extendida.
- B2: como MIROVA ubica el calor de Cordón Caulle a 4,6 a 10,5 km del centro y el cráter del yaml está a 7,6 km,
  predigo que pierde alguna protegida de Cordón Caulle (no elegible).
- B3: 0 perdidas; más negativos que B1.
- B4: 0 perdidas; menos negativos que B1.
- B5: como deja conservador el 7 × 7 central, predigo que pierde alertas de cumbre débiles en volcanes con el calor en
  el centro (Láscar, Villarrica) y queda detrás de B1 en P2.
- N0 (V750-C): si lo que calla las cumbres dentro de la zona sensible es el promedio del remuestreo, N0 detecta en la
  celda de K en más de la mitad de las cumbres negativas que caen dentro del 7 × 7 central y publica más negativos
  limpios que B0 en S_C; en Tupungatito no lo predigo (VB-10 del verificador: depende del ángulo de barrido, se lee por
  tramo de cenit). Si N0 no supera al vecino más cercano de la grilla (23 de 38 en el censo), el remuestreo no es la
  pieza y lo que calla es la interpolación misma.

## 9. Costo, escala y despacho

- Un run de sólo lectura, combinable con V375-B, V375-C y MOD-C (programa §7, fase 1). Referencia: el censo S159 tardó
  1 h 31 min con 32 trozos para 5.746 pasadas; el generador corrido por la segunda vuelta del verificador con los datos
  del 2026-10-24 da 5.770 pasadas en 1.301 gránulos y 0 sin gránulo; al 2026-11-02 serán unas 6.000. Más N0 y N1 en
  S_C. Estimado unas 2 h con 32 trozos; timeout 120 min por trozo.
- Workflow `probe-s162-v750b.yml`: autentica sólo con `EARTHDATA_TOKEN` y falla al instante si viene vacío (A71);
  `"on":` entre comillas (A43); `pipefail` con `tee` (S141); el probe sale 2 si falta una pasada (no baja, sin
  gránulo, grilla incompleta o error de K); el artefacto falla si la carpeta queda vacía (`if-no-files-found: error`).
- Lo despacha la coordinadora desde un tag que fija el código (S152), en una rama auxiliar que no se mergea, con
  `experiments/_s162_v750b/objetivos_v750b.json` commiteado y su sha256 anotado.
- Artefactos en C: (`C:\vrp-trabajo\temporales\s162_v750b\`); parada si C: baja de 3 GB.
- Lectura: `python analizar_v750b.py --art <artefactos> --objetivos objetivos_v750b.json --evaluador
  <evaluar_d25.py del tag> --censo-art D:\vrp-trabajo\temporales\s159_oraculo\censo_39713438252 --censo-objetivos
  <objetivos.json del censo S159>`.
- Run a medias: si el run termina con trozos en rojo, se relanzan sólo las pasadas faltantes con `SOLO` sobre el mismo
  tag; los resultados se juntan (un resultado «ok» reemplaza a uno fallido) y se lee una sola vez.
- **Leer con faltantes** (§4): si después del relanzamiento siguen faltando pasadas o el control del censo no se puede
  correr, y la coordinadora con Nicolás deciden leer igual, se usa `--leer-con-faltantes "<motivo y decisión>"`: cada
  línea de veredicto sale marcada con el motivo y el código de salida es 5. No se edita el analizador después del
  sello. La bandera `--censo-omitido-solo-pruebas` es sólo para baterías sintéticas: cubre sólo el censo, marca el
  veredicto «SIN CENSO, NO VALE PARA EL RUN» y sale con código 4.
- Pasadas sin gránulo: el generador las escribe en `sin_granulo_v750b.json`, atado por sha256 a
  `objetivos_v750b.json` (se commitean juntos); el analizador **exige** el archivo y que corresponda a esa lista (si
  falta o es de otra lista, la cobertura queda SIN DATO y no hay veredicto), y cuenta sus pasadas como SIN DATO; una
  protegida entre ellas frena la lectura. Comando de lectura: agregar `--sin-granulo
  experiments/_s162_v750b/sin_granulo_v750b.json`.
- `--solo-controles` sale 0 sólo con la compuerta abierta; cerrada, 3. Con el censo pedido y fallado, la bandera de
  pruebas no lo reemplaza. El 2 % de cobertura se cuenta sobre las pasadas que cuentan (sin «fuera» ni «sin_crater»).
- El artefacto siempre lleva el log del trozo, así que `if-no-files-found: error` no avisa de un trozo muerto; lo
  avisa el paso del probe en rojo (`pipefail`) y, en la lectura, las pasadas «sin resultado», que cuentan como SIN DATO.

## 10. Lo que este pre-registro NO decide

- No adopta nada ni toca `pipeline/`: la ROI elegida entra al pre-registro de V750-A, con su propio sello, tag y el sí
  de Nicolás (A45).
- No decide el filtro de publicación del paquete (P-sinfiltro es de V750-A).
- No mide el diurno (V750-E), ni VIIRS 375, ni MODIS.

## 11. Estado de lo preparado

- `probe_v750b.py` (brazos B0, B1, B2, B3, B5 y N0, N1; guarda insumos), `objetivos_v750b.py`, `analizar_v750b.py`
  (regla del §6 y controles del §7), `probe-s162-v750b.yml`.
- Prueba sin red del probe en verde (`python probe_v750b.py --sin-red`); prueba local sobre las 510 grillas de N
  (`prueba_local_510_salida.txt`): B0 y B1 iguales a N en 510 de 510, B2 y B3 cambian máscaras en Cordón Caulle y
  Tupungatito; ensayo del analizador sólo con controles (`ensayo_analizador_salida.txt`).
- **Batería sellada de la regla**: `bateria_regla_v750b.py` (comprueba sola el resultado esperado de 18 escenarios:
  los 8 del primer verificador, V1, V3 y V6 de la segunda vuelta, y S1, S2, E5b, E3b, KD, SG y SGx agregados tras la
  tercera; sale 1 si alguno no coincide) → `bateria_regla_v750b_salida.txt`. Encontró un defecto de la propia v3
  (la bandera de pruebas abría también la cobertura), corregido. Su nulo se mide con `verificador_v3/mutar_v3.py`
  (11 mutaciones de una línea del analizador): la tercera vuelta midió 5 de 11 atrapadas con 11 escenarios (VB3-03;
  el texto anterior de este punto decía que la v3 «suma los escenarios que las mataban», y eso valía para 3 de 11);
  los 7 escenarios nuevos están hechos para las 6 que sobrevivían, y la medición sobre la batería de 18 se anota en
  la bitácora y en §12.
- Centro de las zonas: las de la grilla se centran en la celda (33, 33) y las del brazo nativo en el centro del TIF,
  que cae en los índices (32,75; 33,25): un cuarto de celda (unos 0,19 km) por eje. Sólo afecta la comparación del
  brazo nativo con la grilla y se declara.

## 12. Qué cambió de la v1 a la v2 (verificador limpio, Fable 5.1)

- VB-01: la regla de §6.3 ya no puede elegir un brazo que PIERDE o BLOQUEA contra B1.
- VB-02: un record de K vacío ya no tumba el analizador; cuenta como «K no publica» y lo vigila el control K = producción.
- VB-03 y VB-08: «canal que decide» definido (T con la tabla sola, O con tabla más OCR) y la regla dice qué ventana y
  canal deciden cada paso.
- VB-04, VB-05 y VB-16: grilla incompleta, error de K y pasada sin gránulo son SIN DATO con nombre y hacen salir 2 al
  probe; la cobertura de la cumbre se mide en el cráter; criterio de relanzamiento escrito.
- VB-06: los controles positivo, negativo y contra el censo entran a la compuerta; el del censo es obligatorio.
- VB-07: la distancia del record se mide desde el cráter, como producción.
- VB-09: brazo B5 con la lectura del comentario del `.m`.
- VB-10: las zonas del brazo nativo se definen en km y se informan por cenit; predicción de Tupungatito retirada.
- VB-11: el 12-oct queda excluido en todos los brazos.
- VB-12: K distinto de producción en una pasada ya no detiene todo; sale de los brazos y se lista, con tope de 1 %.
- VB-13: citas al censo S159 con su rama (`origin/s159-pruebas`).
- VB-14: artefacto vacío falla; retención de 30 días.
- VB-15: se declara por qué no hay placebo.
- Además: sha256 del evaluador del tag fijado y comprobado; criterio para un run a medias.

De la v2 a la v3 (segunda vuelta, Sonnet; decisiones de diseño bajo D-48 por la coordinadora):

- VB2-01: el desempate tampoco puede elegir un brazo peor que B1 con la tabla sola.
- VB2-02: SIN SUSTRATO sólo cuenta como «no peor» con el neto en 0 o a favor (lectura conservadora), **confirmada por
  la coordinadora bajo D-48** (2026-10-24).
- VB2-03 y VB2-04: la bandera de pruebas marca el veredicto y sale con código 4; camino escrito para leer con
  faltantes (`--leer-con-faltantes`, código 5), sin editar el analizador después del sello.
- VB2-05 y VB2-06: batería que comprueba sola sus 11 escenarios; control positivo que exige que B1 publique lo que
  B0 pierde (detecta un oráculo muerto); control negativo con filo (B4 contra B1 donde son idénticos).
- VB2-07: pasadas sin gránulo en un archivo que el analizador lee; protegidas no observadas por nombre.
- VB2-08: multiplicidad declarada. VB2-09: el control del censo compara la posición de los píxeles. VB2-10:
  redundancia declarada. VB2-11: lo que `if-no-files-found` no cubre, declarado. VB2-12: el texto del control de N0
  y N1 dice lo que el código hace. VB2-13: lista completa de K distinta. VB2-14: cuarto de celda declarado.
  VB2-15: tamaños actualizados.
