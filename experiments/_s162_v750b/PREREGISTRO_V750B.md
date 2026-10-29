# Pre-registro V750-B (S162): la región sensible (ROI) del código de MIROVA, por volcán, en VIIRS 750

> ⚠️ **Adenda 3 (2026-10-29, SELLADA por Nicolás el 2026-10-29 sobre `fe4802a2a`; ver al final)**: regla N-3. Una
> protegida sin alerta de la tabla, de Suomi NPP (`VIIRS_SNPP_750`) y anterior al 2026-10-09 no veta en el §6.1; se
> lista aparte con el P1 que veta al lado del que las cuenta todas. **El veredicto del 2026-11-03 es el de
> `adenda3/leer_n3_v750b.py`** (la compuerta de la adenda 1 va primero, igual que en `adenda1/leer_v750b.py`, que se
> corre al lado y sólo informa). Al generar los objetivos se cuentan las N-3 de la lista sellada. Nada más cambia.

> ⚠️ **Adenda 2 (2026-10-27, SELLADA por Nicolás el 2026-10-28 sobre `739edff39`; ver al final)**: suma al mismo run
> las pasadas en que MIROVA publicó una fuente lejana (lista suplementaria aparte, ids desde 100000, la lista sellada
> intacta) y un lector de diagnóstico de la posición del record (radiante, cercano y pico) que no decide V750-B. El
> despacho del 2026-11-03 cambia en tres cosas (§3 y §7 de la adenda): la rama de disparo lleva los archivos de
> `adenda2/`, el workflow lee `adenda2/objetivos_run_v750b.json` y todo relanzamiento con `SOLO` lee esa misma lista.
> La lectura sellada corre sobre la parte sellada de los resultados (§8 de la adenda). Ninguna regla de la ROI cambia.

> ⚠️ **Adenda 1 (2026-10-25, informativa, agregada después del sello; ver al final)**: el analizador sellado deja caer
> sin contar la pasada «ok» a la que le falta una caja del oráculo. La lectura del 2026-11-03 se hace con
> `adenda1/leer_v750b.py`, que corre antes el compañero `adenda1/cobertura_cajas_v750b.py` y no deja pasar al
> analizador si cierra. Ninguna regla cambia y el analizador no se edita.

Estado: **SELLADO bajo D-48** (2026-10-24; condición de la coordinadora cumplida: la batería atrapa por aserción 13 de 13
mutaciones del analizador, con la copia sin mutar y la mutación que sólo se cae como controles, `mutar_bateria_salida.txt`),
corregido tras dos verificadores limpios: el primero (Fable 5.1,
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
   el de menor E (T ∪ O, canal que decide), y a igual E el primero en el orden de cercanía al `.m` del punto 3
   (VB3-01, aprobado por la coordinadora bajo D-48). Multiplicidad: se contrastan hasta cinco brazos contra B1, cada uno al
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

De la v3 a la versión sellada (tercera vuelta, Fable, sólo sobre el delta; coordinadora bajo D-48):

- VB3-01 (regla): a igual E entre ganadores, el orden de cercanía al `.m` del §6.3; escenario S3.
- VB3-02: el archivo de pasadas sin gránulo es obligatorio y está atado por sha256 a la lista de objetivos.
- VB3-03: la batería pasó de 11 a 19 escenarios (S1, S2, S3, E5b, E3b, KD, SG, SGx); `mutar_bateria.py` mide su nulo:
  13 de 13 mutaciones atrapadas por aserción (las 11 de la tercera vuelta con el texto puesto al día y 2 propias),
  identidad PASA y la mutación que sólo se cae sale CAÍDA.
- VB3-04 a VB3-07: declarado (B0 y el control positivo) o arreglado (código de `--solo-controles`, bandera de pruebas
  con censo fallado, denominador del 2 %).

## Adenda 1 (2026-10-25, informativa; propuesta por la sesión VIIRS 750 2, la confirma la coordinadora bajo D-48)

**Qué pasa.** `analizar_v750b.py` (l. 208-209) cuenta una pasada como observada sólo si trae las cinco cajas del oráculo
(B0, B1, B2, B3, B5), pero la que es «ok», nocturna y con el cráter cubierto y no las trae no entra en la lista de SIN
DATO (l. 206) ni en la de no observadas (l. 207): sale del numerador y del denominador a la vez, sin nombre. Si es una
protegida, la cobertura sigue diciendo SUFICIENTE y la protegida queda fuera de P1 sin que nadie la haya mirado.
Encontrado por el subagente que escribió el analizador de V750-A; demostrado en el escenario D1 de
`adenda1/probar_adenda1.py` (25 objetivos, el analizador sellado da 24 observadas, 0 SIN DATO y cobertura SUFICIENTE con
la protegida sin caja).

**Cuánto puede pesar.** Con el probe sellado, nada esperado: `probe_v750b.py` (l. 166-169) calcula las cinco cajas
juntas en el mismo bloque y cualquier excepción marca la pasada entera como `error`, que sí es SIN DATO. El caso sólo
aparece si un relanzamiento con `SOLO` corre otro código, o si un artefacto llega dañado pero legible. Por eso es una
adenda y no un arreglo: el riesgo es que el analizador calle, no que mida mal.

**Por qué no cambia ninguna regla.** El §4 ya dice que una pasada con error de un brazo es SIN DATO, que con más del 2 %
de SIN DATO o una protegida SIN DATO no se lee el veredicto, y que se relanzan sólo las faltantes. Una pasada sin una
caja del oráculo es un brazo que no corrió. La adenda aplica esa regla a un caso que el código no cubría; las métricas,
la regla del §6 y los controles del §7 quedan como están, y el analizador no se edita (§9).

**Cómo se lee el 2026-11-03** (versión 2, tras el verificador de la adenda, VAD-01 a VAD-05). En lugar del comando
del §9 se usa el lector, que corre el compañero y sólo entonces el analizador sellado, con los mismos argumentos que
el §9 y rutas absolutas (`<repo>` es la raíz del árbol de lectura; el compañero no se puede saltar):

    python <repo>/experiments/_s162_v750b/adenda1/leer_v750b.py --art <artefactos> --objetivos <repo>/experiments/_s162_v750b/objetivos_v750b.json --sin-granulo <repo>/experiments/_s162_v750b/sin_granulo_v750b.json --evaluador <evaluar_d25.py del tag> --censo-art D:\vrp-trabajo\temporales\s159_oraculo\censo_39713438252 --censo-objetivos <objetivos.json del censo S159>

- Compañero SUFICIENTE: el lector corre el analizador y sale con su código.
- Compañero INSUFICIENTE por pasadas sin caja (la llave falta; el analizador las dejaría caer): no se lee. Se relanzan
  con `SOLO` las pasadas que lista como «falta caja» y se vuelve a leer; si siguen faltando, la coordinadora decide con
  Nicolás si se lee igual con `--leer-con-faltantes "<motivo>"` (§9): el lector marca cada línea de la salida con
  «[LEÍDO CON FALTANTES DE LA ADENDA: motivo]» y sale 5.
- **Caja ilegible** (la llave está pero vale `null`, o le falta `npix`, `vrp_mw` o `pixeles`; VAD-03 y VAD-04): el
  analizador la cuenta como observada y después se cae (`null`) o la lee como «no publica» sin aviso (`{}`). Esa pasada
  cierra la cobertura siempre, haya el porcentaje que haya, y **no se puede leer ni con `--leer-con-faltantes`**: se
  relanza.
- Sin cajas faltantes ni ilegibles el compañero da el mismo SIN DATO y el mismo veredicto de cobertura que el
  analizador sellado (escenarios A4, A6 y A11 a A17, cada uno comprobado contra el analizador). Una pasada que el
  compañero cuenta como «falta caja» queda fuera de las métricas igual que en el analizador; una con caja ilegible, en
  cambio, quedaría DENTRO si se leyera, y por eso no se lee. (La versión 1 de este punto decía que toda pasada «falta
  caja» quedaba fuera; era falso para la caja `null`, VAD-03.)

**Pruebas.** `adenda1/probar_adenda1.py`: roja por aserción sin el compañero (`probar_adenda1_rojo_salida.txt`), verde
con él (`probar_adenda1_salida.txt`). Nulo: `adenda1/mutar_adenda1.py` (`mutar_adenda1_salida.txt`), siete mutaciones
de una línea del compañero, la copia sin mutar y una mutación que sólo se cae. La primera corrida del nulo dejó pasar
dos (la protegida que no frena cuando está bajo el 2 %, y la diurna contada dos veces); se agregaron los escenarios A7
y A8 y se volvió a medir. Verificador limpio (Sonnet 5.5, `adenda1/verificador/INFORME.md`): LISTO CON CAMBIOS, sin
hallazgos de gravedad 4 o 5; el defecto del analizador y el caso «no debería ocurrir con el probe sellado» quedan
confirmados. Cambios hechos por sus hallazgos: VAD-01 (lector con la compuerta), VAD-02 (comando con rutas absolutas),
VAD-03 y VAD-04 (cajas ilegibles cierran siempre), VAD-05 (escenarios A11 a A17 por las siete roturas suyas que la
batería dejaba pasar, más A9, A10 y L1 a L4, y esas roturas sumadas al nulo). VAD-06: la salida roja demuestra sólo que
sin compañero no hay lectura; el peso de la prueba está en el nulo. VAD-07 (que «sin cambiar ninguna regla» es una
lectura conservadora del §4 b, que no nombra la caja) se acepta tal cual. VAD-08 (una protegida «fuera» o «sin
cráter» no frena) es el diseño sellado y queda fuera de esta adenda.

## Adenda 2 (2026-10-27; SELLADA por Nicolás el 2026-10-28 sobre `739edff39`)

Sello: Nicolás, en el chat de la coordinadora S166, primero «Sello la adenda 2 de V750-B (rama
claude/s162-viirs750-2-918174, commit 4dbd88dce). Pide antes una pasada corta del verificador sobre los 13 cambios.»,
y, tras esa pasada (SELLABLE CON CAMBIOS MENORES, arreglos en `739edff39`), «Lo que tú recomiendes» ante la pregunta de
traspasar el sello a `739edff39`; la recomendación era sí. S166 comprobó en un árbol propio (core.autocrlf=false):
batería 40 de 40, nulo 33 de 33, y `analizar_v750b.py`, `objetivos_v750b.py` y `probe_v750b.py` idénticos al tag
`s162-v750b-sellado`. El texto que sigue es el de `adenda2/ADENDA2_V750B.md` en `739edff39`, con los títulos bajados un
nivel; su línea «PROPUESTA, SIN SELLAR» del encabezado es la de antes del sello y no se copia. Los scripts sellados son los
de `adenda2/` en ese commit.

### 1. Qué pidió Nicolás y por qué toca a V750-B

Nicolás, 2026-10-27 (programa §7, rama `loop/activo`, `72928820b`): «Sí: no fijes la regla todavía; mídela como brazo
(radiante, cercano y pico) en los A/B de cada sensor contra lo que publica MIROVA». El programa agrega que la vara
incluye las pasadas en que MIROVA publicó una fuente lejana (`FALSO_POSITIVO` de la tabla), y que si un pre-registro
está sellado los brazos entran por adenda, antes de ver los datos.

En VIIRS 750 los tres brazos de posición pertenecen a V750-A (el A/B de fase 4), que sigue en borrador y los recibe en
su texto. V750-B no decide nada sobre la posición. Pero es la única corrida que baja los gránulos antes de V750-A, y
guarda lo necesario para medir los tres brazos: por cada pasada y cada caja, todos los alertados con su fila, columna
y radiancia M13, y la grilla entera. Si V750-B corre sin las pasadas lejanas, V750-A tendría que volver a bajarlas
de NASA.

### 2. El fenómeno, como geólogo

La regla de posición sólo importa en una escena: un píxel débil junto al cráter y una fuente más radiante lejos (otro
foco del complejo, un borde de nube, un incendio). El analizador sellado ubica el record en el centroide del cúmulo
del alertado más radiante (**radiante**). Si ese cúmulo cae fuera del radio interior, el record queda lejano y el
tablero calla. Con **cercano**, el mismo record queda en la cumbre y el tablero publica la suma de todos los alertados,
que en esa escena viene sobre todo de la fuente lejana. Con **pico**, manda el píxel más radiante solo, sin promediar
su cúmulo: en un cúmulo que cruza el borde del radio interior, el centroide puede quedar adentro y el pico afuera.

Las pasadas en que MIROVA publicó una fuente lejana son justo esa escena vista desde MIROVA: vio calor y lo ubicó lejos
del cráter. Ahí lo correcto es no publicar como cumbre, y es donde «cercano» puede publicar de más. La medición de S165
no las pudo mirar en VIIRS (el programa §7, `72928820b`, dice «19 en VIIRS 750»; el informe de S165 no trae esa cifra,
VAD2-13, y el generador de esta adenda da 20 sobre su propia ventana, §6).

### 3. Qué agrega (nada de lo sellado cambia)

1. **Lista suplementaria** (`adenda2/objetivos_supl_v750b.py`). Corre la misma población (`01_poblacion.py` de main,
   la misma lógica) cambiando sólo el filtro de etiquetas de la l. 106 para dejar pasar también `far_ref` (fila
   FALSO_POSITIVO y ninguna ALERTA a ±120 s, etiqueta de `banco_paridad`). Aplica los mismos cortes del generador
   sellado (días excluidos, cese de Suomi NPP, sin gránulo afuera y declarado). Escribe aparte
   `objetivos_supl_v750b.json` (ids desde 100000), `sin_granulo_supl_v750b.json` (atado por sha256),
   `objetivos_run_v750b.json` (la sellada, sin tocar, seguida de la suplementaria) y `poblacion_supl.json`.
   **Control**: las `pos` y `neg_limpio` de esa corrida, con los mismos cortes, tienen que ser exactamente las de la
   lista sellada del mismo día, campo por campo (volcán, hora, gránulo, etiqueta, protegida, alerta de la tabla y si
   decide; VAD2-08). Si no, sale 1 sin escribir ninguna lista y deja la población como
   `poblacion_supl_CONTROL_FALLIDO.json`. Se niega a escribir en la carpeta sellada o encima de salidas de otra corrida
   (sale 2; no borra nada; VAD2-03 y VAD2-09).
2. **El run lee `objetivos_run_v750b.json`.** En la rama de disparo, además de lo que ya manda el §9 sellado, van los
   cuatro archivos de `adenda2/` del punto 1 (el tag `s162-v750b-sellado` no tiene esa carpeta: se commitean en la
   rama de disparo junto a la lista sellada) y la copia del workflow con
   `OBJETIVOS: "experiments/_s162_v750b/adenda2/objetivos_run_v750b.json"`. El probe y su lógica no cambian; las
   pasadas suplementarias corren en los mismos 32 trozos. Según el verificador, 19 de las 20 del ensayo caen en
   gránulos que ya se bajan, y 301 de 1.319 gránulos sellados cambian de trozo (cosmético, VAD2-10).
3. **Relanzamiento** (VAD2-06). Un relanzamiento de faltantes con `SOLO` tiene que leer la **misma** lista del run: si
   lee la sellada, el probe descarta sin error los ids desde 100000, imprime «0 granulos, 0 pasadas» y el trozo sale
   verde sin haber hecho nada (A108; lectura del código, no ejecutado). Antes de dar por bueno un relanzamiento se
   cuenta, en su log, que procesó tantas pasadas como ids pidió `SOLO`.
4. **Separación antes de la lectura sellada** (`adenda2/separar_resultados_v750b.py`). Escribe `sellado/` (ids menores
   que 100000) y `supl/`, cada carpeta de artefactos con su índice delante, para que la corrida y su relanzamiento no
   se pisen aunque se llamen igual (VAD2-01, que con la primera versión perdía resultados); cuenta releyendo lo escrito
   y sale 1 si las partes no suman lo leído. El verificador mostró que sin separar sólo cambia la línea informativa
   «con resultado N» del analizador; se separa igual para que la lectura sellada vea **exactamente** lo que habría visto
   sin la suplementaria (byte a byte, escenario P8, con su testigo).
5. **Diagnóstico de posición** (`adenda2/leer_posicion_v750b.py`). No decide V750-B: es insumo de V750-A.

### 4. El diagnóstico

- **Brazos**, sobre la misma detección de cada caja (B0 a B5; sólo cambia el punto desde donde se mide la distancia,
  y con ella la clase `summit` o `far`; el VRP, que es el de la unión de los alertados, y el tamaño del cúmulo quedan
  como los arma el analizador sellado):
  - **radiante**: `record_cumulo` del analizador sellado, sin tocar;
  - **cercano**: el alertado más cercano al cráter (`pos_crater`, como mide producción);
  - **pico**: el alertado de mayor M13, el mismo que siembra el cúmulo, con el mismo desempate.
- **Población**: la del analizador sellado, con su misma exclusión de las pasadas en que el K del probe no reproduce a
  producción (§7; VAD2-02). Así la fila «radiante» de cada caja es la del veredicto sellado: el verificador lo comprobó
  contra el analizador, con el cráter en el centro y corrido del centro.
- **Publica**: el predicado del tablero ejecutado con node (A97).
- **Vara 1, alertas y negativos limpios** (la población sellada): P1 y E del §5 con el canal que decide y con la tabla
  sola, en T y O juntas, y la prueba de signos de P2 contra radiante de la misma caja. Las funciones (`etiqueta`,
  `metricas`, `p2`) se extraen con ast del `main()` del analizador sellado y se ejecutan sin copiar a mano; el
  analizador se identifica por sha256 con fin de línea LF (`83b7159b...`, el del tag). Además, las pasadas que cambian
  de publicación contra radiante, por nombre.
- **Vara 2, pasadas lejanas de MIROVA**: cuántas tienen algún alertado en cada caja (VAD2-07: sin eso, un cero de
  «publica» no distingue «la escena no ocurrió» de «el brazo no publica de más») y cuántas publica cada brazo (lo
  correcto es cero), por nombre.
- **Vara 3, distancia**: la distancia de cada brazo desde la celda central de la grilla (33, 33; el punto de
  referencia de MIROVA queda a hasta 0,35 km de ella, VAD2-12) contra la `Distancia_km` de MIROVA, en alertas y en
  pasadas lejanas: mediana de la diferencia y fracción a 1 km o menos. Del OCR sólo entran las filas desde el
  2026-06-13 (A119; VAD2-05). Es diferencia de radios, no de posiciones (A93): sirve para descartar un brazo, no para
  afirmar que ve el mismo objeto que MIROVA. S165 encontró que la distancia de MIROVA calza mejor con el píxel pico que
  con el centroide; esto lo mide en VIIRS 750 con el código de MIROVA.
- **Controles** (si uno cae, sale 3 y dice DIAGNÓSTICO NO LEGIBLE): C1, en las cajas con un solo alertado los tres
  brazos coinciden, con al menos un caso; C2, nulo del predicado (un record radiante publicado, pasado a lejano, deja
  de publicar); C3, las listas (ids sellados bajo 100000, suplementarios desde 100000, sin choque, todas `far_ref`,
  archivo sin gránulo atado por sha256); C4, el analizador es el sellado (si no lo es, ni se carga).
- **SIN DATO** de la suplementaria: las procesadas que fallaron se listan por nombre; las sin gránulo, también. No frena
  nada (es diagnóstico).
- Orden de lectura: primero la sellada (§8). Si su compuerta queda cerrada, el diagnóstico se informa igual pero con
  esa marca, porque mide sobre la misma población.

### 5. Lo que esta adenda NO hace

- No toca la ROI, las métricas, la regla del §6 ni los controles del §7 de V750-B, ni su analizador.
- No elige regla de posición. Eso lo decide V750-A, con su propia regla escrita antes del sello.
- No cubre los `FALSO_POSITIVO` que en la misma pasada conviven con una ALERTA (esa pasada es `pos` y ya está en la
  población sellada), ni las 8 pasadas `sin_geometria` del ensayo (MIROVA vio calor sin saber dónde, V31.1), que
  quedan fuera de las dos listas por construcción (VAD2-13).
- «Lo correcto es no publicar» en las pasadas lejanas es una premisa de la réplica (A115): vale para
  `mirova_equivalent`, no para el perfil `experimental`.

### 6. Ensayo (2026-10-27, sobre main `bd711db63`, ventana hasta 2026-10-26)

`objetivos_v750b.py` da 5.841 objetivos (0 sin gránulo). `objetivos_supl_v750b.py` con la misma ventana: control
IGUALES (5.841 contra 5.841), **20 pasadas `far_ref` con gránulo, 0 sin gránulo**: Lastarria 5, Tupungatito 4,
Nevados de Chillán 3, Láscar 2, Planchón-Peteroa 2, Isluga 2, Llaima 1, Villarrica 1; distancias de MIROVA de 6,4 a
29,6 km; 6 antes del 2026-06-13. Las 20 traen una fila `FALSO_POSITIVO` de la tabla (una trae además una del OCR), y su
distancia sale de la de la tabla en las 20, así que no depende del OCR mal calibrado de antes de junio (A119).
Producción no publica ninguna de las 20. Costo: 20 pasadas más sobre unas 6.000 (0,3 %). El verificador reprodujo el
ensayo (5.841 IGUALES, 20, 0 sin gránulo, archivo suplementario idéntico byte a byte) con la versión anterior del
generador; la versión corregida ordena las suplementarias también por hora, así que su sha256 ya no es el del ensayo.
Los archivos del ensayo no son los definitivos y no se commitean.

### 7. Despacho del 2026-11-03 (sólo si Nicolás selló esta adenda)

Sobre el main de ese día, en este orden (la carpeta `adenda2/` no debe tener salidas de antes):

    python experiments/_s162_v750b/objetivos_v750b.py --data data/mirova_equivalent --ref-dest <carpeta> --hasta 2026-11-02
    python experiments/_s162_v750b/adenda2/objetivos_supl_v750b.py --data data/mirova_equivalent --ref-dest <carpeta> --hasta 2026-11-02 --sellado experiments/_s162_v750b/objetivos_v750b.json

Se commitean `objetivos_v750b.json`, `sin_granulo_v750b.json` y `poblacion_completa.json` (sellados) y
`adenda2/objetivos_supl_v750b.json`, `adenda2/sin_granulo_supl_v750b.json`, `adenda2/objetivos_run_v750b.json` y
`adenda2/poblacion_supl.json`, con los tres sha256 que imprime el segundo comando. La coordinadora despacha desde el tag,
en la rama de disparo con esos archivos, con `OBJETIVOS` apuntando a `objetivos_run_v750b.json` (§3, puntos 2 y 3).

### 8. Lectura

    python <repo>/experiments/_s162_v750b/adenda2/separar_resultados_v750b.py --art <artefactos> [<relanzamiento>] --dest <carpeta nueva>
    python <repo>/experiments/_s162_v750b/adenda1/leer_v750b.py --art <carpeta nueva>/sellado <resto de argumentos de la adenda 1>
    python <repo>/experiments/_s162_v750b/adenda2/leer_posicion_v750b.py --art <artefactos> [<relanzamiento>] --objetivos <repo>/experiments/_s162_v750b/objetivos_v750b.json --objetivos-supl <repo>/experiments/_s162_v750b/adenda2/objetivos_supl_v750b.json --sin-granulo-supl <repo>/experiments/_s162_v750b/adenda2/sin_granulo_supl_v750b.json --evaluador <evaluar_d25.py del tag s161-d25-lectura>

El veredicto de V750-B es el del segundo comando y sólo ése. El tercero informa.

### 9. Pruebas

- `adenda2/probar_adenda2.py` (`probar_adenda2_salida.txt`): **40 de 40** como se espera, con escenas sintéticas en el
  formato del probe: LEJANA (alertado débil junto al cráter y cúmulo brillante a 13 km), BORDE (cúmulo que cruza el
  radio interior con el pico afuera), UNO (un solo alertado), PICOCERCA (el más radiante junto al cráter y un cúmulo
  más débil lejos) y una pasada con el cráter 7,5 km al W del centro. Comprueba P1 y E por brazo en los dos canales,
  los cambios contra radiante con su etiqueta (exactos, sin las suplementarias), P2, la pasada lejana (sólo cercano
  publica; una con alertado y otra sin ninguno), la distancia desde el centro con el cráter corrido, la exclusión de K
  distinto en publicación y en magnitud (K en 0 MW con producción en 0,5 MW) y de la diurna, la alerta sólo del OCR
  (cuenta en el canal que decide y no en la tabla sola; antes del 13-jun no entra a la vara 3), los controles C1 (con y
  sin casos), C3 (tres roturas) y C4, el SIN DATO por lista, la separación (P8 y su testigo, carpetas del mismo nombre,
  carpeta ocupada), las funciones del generador (filtro, cortes, control, selección, numeración y orden de la lista del
  run) y `generar()` entero con dependencias sintéticas (P18: control bien, control caído, segundo intento fallido en
  la misma carpeta, salidas previas y carpeta sellada, esta última con una carpeta de mentira para que una guarda rota
  nunca escriba en la real).
- Nulo: `adenda2/mutar_adenda2.py` (`mutar_adenda2_salida.txt`): **33 de 33 mutaciones de una línea atrapadas por
  aserción** (21 del lector, 2 del separador, 10 del generador), la copia sin mutar PASA y la mutación que sólo hace
  caer al lector sale CAÍDA. Incluye las 14 del verificador que la primera versión de la batería dejaba pasar (VAD2-04)
  y las 6 del verificador corto (N1, su E4, y G10 a G13 sobre `generar()`). En G12 y G13 el `generar()` mutado lanza
  `FileExistsError` en vez de devolver 2: la batería lo registra como salida equivocada y la aserción del escenario lo
  ve. Quedan sin atrapar, declaradas: el predicado leyendo la columna del VRP de display en vez de la de publicación
  (en todas las escenas probadas las dos coinciden: un record lejano da display 0), el desempate del pico y el cruce de
  filas y columnas del centroide (equivalentes en las escenas, sólo importan con empates o en la diagonal), la primera
  de las dos defensas del separador contra una carpeta ocupada (la segunda la ataja) y el chequeo de suma del
  separador (E9 del verificador corto: hoy inalcanzable, porque cada fila va a una de las dos partes).
- Límite declarado: apagar C2 no lo atrapa ninguna escena (con datos sanos el control ya da verde); se prueba por las
  mutaciones que rompen lo que vigila (L5 lo hace caer).
- **Ensayo del segundo comando del §7 sobre datos reales** (pedido por el verificador corto, N3), 2026-10-28 00:14
  UTC, con el `generar()` reescrito, sobre el árbol de main `bd711db63` y la ventana hasta el 2026-10-26: salida 0,
  control IGUALES (5.841 contra 5.841, campo por campo), 20 pasadas lejanas, 0 sin gránulo; sha256 suplementaria
  `c4d75157...`, lista del run `527788b7...` (5.841 + 20), iguales a los de la versión anterior del generador sobre los
  mismos datos. Un segundo intento sobre la misma carpeta se niega (salida 2).

### 10. Estado y verificador

- Batería: 40 de 40. Nulo: 33 de 33 atrapadas por aserción; identidad PASA; control CAÍDA.
- Verificador limpio (Sonnet 5.5, `adenda2/verificador/INFORME.md`, sobre `83405c557`): **LISTO CON CAMBIOS**, ningún
  hallazgo de gravedad 4 o 5; la lectura sellada no se contamina y los tres brazos miden lo que dicen. Sus 13 cambios
  quedaron en `4dbd88dce`: VAD2-01 (separador), VAD2-02 (exclusión de K distinto), VAD2-03 y VAD2-09 (el generador no
  escribe encima ni en la carpeta sellada), VAD2-04 (escenarios y 14 mutaciones suyas al nulo), VAD2-05 (OCR de antes
  del 13-jun fuera de la vara 3), VAD2-06 (relanzamiento, §3.3), VAD2-07 (pasadas lejanas con alertado), VAD2-08
  (control campo por campo), VAD2-10 (declarado), VAD2-11 (sin gránulo por nombre), VAD2-12 (celda central) y VAD2-13
  (cifra 19 y `sin_geometria`). Seguimiento suyo que no es de la adenda: `01_poblacion.py` escribe en el meta un
  commit fijo (`533398f8f`) aunque los records sean de otro.
- **Sello**: Nicolás selló la adenda sobre `4dbd88dce` (2026-10-28, vía la coordinadora S166), condicionado a una pasada
  corta del verificador sobre los 13 cambios. Esa pasada (Sonnet con contexto limpio, lanzada por S166,
  `S166_VERIFICADOR_CORTO_ADENDA2_V750B.md` en las notas compartidas) dio **SELLABLE CON CAMBIOS MENORES**: lo sellado
  sigue intacto y batería y nulo se reproducen en un árbol aparte. Arreglos de esta versión, todos dentro de
  `adenda2/`: N1 (el lector excluye también por magnitud, |VRP de K − pc_vrp| > 0,001 MW, como el sellado l. 292-293),
  N2 (la población de un intento fallido cuenta como salida previa), el resto de VAD2-11 (toda lista cortada avisa
  que lo está) y N3 (`generar()` separado de sus dependencias y probado entero, cuatro mutaciones nuevas sobre él, y el
  ensayo del §9 sobre datos reales). El sello pasa a este commit cuando Nicolás lo confirme.

## Adenda 3 (2026-10-29; SELLADA por Nicolás el 2026-10-29 sobre `fe4802a2a`)

Sello: Nicolás, en el chat de la coordinadora S167, el 2026-10-29: «Sí a todo» ante el programa
`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §12.5 punto 5 (una adenda 3 corta de V750-B que
aplique la regla N-3, escrita antes de ver datos, con verificador), condicionado al verificador corto. Primera pasada
(Sonnet con contexto limpio, sobre `5b924379d`): SELLABLE CON CAMBIOS MENORES, con VA3-01 como condición; arreglos en
`fe4802a2a`. Segunda pasada sobre `fe4802a2a`: **SELLABLE** (VA3-01 a VA3-04 cerrados; batería 12 de 12, rojo 12 de 12,
rojo contra `5b924379d` falla N9, N10 y N11, nulo 14 de 14, identidad PASA, control CAÍDA). Informes en `loop/activo`:
`experiments/_s167/v750b_adenda3_verificador/INFORME.md` e `INFORME_R2.md`. La mutación equivalente de VA3-03 queda
declarada como gravedad 1. El texto que sigue es el de `adenda3/ADENDA3_V750B.md` en `fe4802a2a`, con los títulos
bajados un nivel; su párrafo «BORRADOR» del encabezado es el de antes del sello y no se copia. Los scripts sellados son
los de `adenda3/` en ese commit.

### 1. Por qué, como geólogo

Una alerta de MIROVA que existe sólo por el OCR sale de leer la imagen por volcán que MIROVA publica, no de su tabla.
En Suomi NPP ese canal llegó a traer la imagen de otra pasada (la cabecera «Last Update» lo delata; Mirova-v1#20), y
antes del 2026-10-09 no hay forma de saber si una alerta protegida leída así es de la pasada que comparamos. Si V750-B
descarta una ROI porque «pierde» una protegida que quizás no estaba ahí, puede quedarse con una ROI peor por un error
de la referencia, no del detector. Nicolás decidió tratar esas alertas igual en todas partes: se informan aparte y no
deciden (S166 para el auto-audit, #924; V375-E §8.13, sellado el 2026-10-28; V750-A §6 ter).

### 2. La regla

Una pasada es **N-3** si es protegida (`protegida`), **no** tiene alerta de la tabla (`alerta_tabla` falso, o sea que
la protegida existe sólo por el OCR), es de Suomi NPP (`sensor == "VIIRS_SNPP_750"`) y su `hora_utc` es anterior al
2026-10-09.

- **No veta.** Una N-3 que un brazo no publica no suma al P1 que veta (§5), así que no lo saca de los elegibles del
  §6.1. Como en la ventana T decide la tabla sola, una pasada sin alerta de la tabla nunca fue etiqueta ahí: la regla
  sólo actúa en la ventana O (desde el 2026-06-13), con el canal que decide y con el canal «todo».
- **Se informa aparte.** El lector lista cada N-3 observada por volcán y hora, con qué brazos la publican y cuáles
  no; cada línea de métricas imprime el P1 que veta al lado del que las cuenta todas («P1 0 (que veta; todas 1, N-3
  aparte 1)»), y debajo de los elegibles imprime los que daría la regla sin la adenda, contando también las N-3. Una
  pérdida de esta clase se ve, pero no decide.
- **No cambia nada más**: la protegida con alerta de la tabla (aunque esa alerta sea menor de 1 MW y la protegida
  venga del OCR), la de otra plataforma o la del 2026-10-09 en adelante siguen vetando. E, P2, la regla §6.2 y §6.3,
  el orden de cercanía al `.m`, los controles del §7 (incluido el control positivo de Cordón Caulle) y la cobertura
  (una protegida SIN DATO sigue frenando la lectura, sea o no N-3) quedan como están sellados. La adenda 2 (posición,
  diagnóstico) tampoco cambia: no decide, y su P1 sigue contando todas.

### 3. Cómo se aplica sin tocar lo sellado

`adenda3/leer_n3_v750b.py` exige el sha256 del analizador sellado, le aplica cinco reemplazos de texto exactos (cada
uno tiene que aparecer una sola vez; si no, se niega con salida 2) y lo ejecuta entero con el `__file__` del
sellado: mismas rutas, mismo oráculo, mismo predicado del tablero con node, misma prueba de signos. Los reemplazos:
(1) el conteo del P1 separa las N-3; (2) la línea de métricas muestra los dos P1; (3) la lista aparte y los elegibles
sin la adenda; (4) la línea del veredicto lleva «[con la adenda 3, regla N-3]»; (5) un encabezado.

**La compuerta de la adenda 1 va primero (VA3-01).** La lectura sellada es `adenda1/leer_v750b.py` (adenda 2 §8): corre
el compañero `cobertura_cajas_v750b.py` y, si la cobertura con las cajas no cierra, no deja pasar al analizador (salida
3; con `--leer-con-faltantes` marca el veredicto y sigue). `leer_n3_v750b.py` carga ese lector sellado tal cual (exige
su sha256 y el del compañero, los del tag `s162-v750b-adenda2-sellada`) y le cambia una sola cosa: el analizador que
llama es el sellado con la adenda 3. La compuerta, sus salidas y su marca son las selladas, sin copiarlas.

**Lectura del 2026-11-03 en adelante**: el mismo procedimiento sellado (adenda 2 §3 y §8: separar resultados, leer la
lista sellada con `adenda1/leer_v750b.py`), con un solo cambio: **el veredicto de V750-B es el de
`leer_n3_v750b.py`**, con los mismos argumentos con que se correría `adenda1/leer_v750b.py`. El lector sellado se
corre igual al lado y su salida se guarda: es la regla sin N-3, que sólo informa. Antes de que Nicolás confirme la
ROI (§6.5), se miran juntas la lista aparte de N-3 y la ROI de la lectura sin N-3 (VA3-05): si la N-3 cambió la ROI,
la ROI elegida puede perder una protegida que sí era real, y eso se dice. El despacho, el probe, los objetivos y el
workflow no cambian.
Al generar los objetivos (R4), antes de leer cualquier resultado, se cuentan las N-3 de la lista sellada (son
etiquetas de la referencia, no resultados) y se informan con la lista.

### 4. Pruebas

Cifras de la versión tras el verificador corto (VA3-01 a VA3-04); el detalle de cada corrida, en sus salidas.

- `adenda3/probar_adenda3.py` (`probar_adenda3_salida.txt`): **12 de 12** como se espera (las 9 de abajo más N9 a
  N11, que siguen el párrafo). Escenas sintéticas armadas con
  el constructor de la batería sellada (`bateria_regla_v750b.py`, extraído con ast), corridas por el lector entero:
  N0 la base sin N-3 (B0 y B5 siguen fuera por Cordón Caulle); N1 B2 pierde una N-3 del 2026-09-20 y sigue elegible,
  con su línea en la lista aparte y los dos P1; N2 la misma el 2026-10-09 veta (borde); N3 la misma de NOAA-20 veta;
  N4 la misma con alerta de la tabla de 0,6 MW veta; N5 la N-3 decide la ROI (B0 la pierde en Láscar, donde B4 es la
  caja B0: con la adenda B4, sin ella B2); N6 una sólo del OCR en T no es etiqueta ni se lista; N7 dos N-3 y una de la
  tabla perdidas: veta la de la tabla (P1 1, todas 3, aparte 2); N8 un analizador que no es el sellado se rechaza
  (la copia ajena vive en la carpeta temporal, no en la sellada: VA3-04); N9 la N-3 de N1 sin la caja B5: la
  compuerta de la adenda 1 cierra, salida 3 y sin veredicto (VA3-01); N10 la misma con `--leer-con-faltantes`: se lee,
  con la marca de la adenda 1 en el veredicto; N11 `--salida=ruta` sola escribe en esa ruta (VA3-02).
- Rojo contra el analizador sellado, sin la adenda (`probar_adenda3_rojo_salida.txt`): fallan por **comportamiento**
  N1 (B2 fuera de los elegibles), N5 (B4 fuera, el sellado elige B2), N7 (P1 3) y N9 (el analizador solo lee sin
  compuerta); las demás fallan sólo porque falta el texto de la adenda (VA3-03), y eso no prueba nada sobre la regla.
- Rojo contra el lector anterior (`5b924379d`, sin la compuerta; `probar_adenda3_rojo_va3_salida.txt`): N9, N10 y N11
  fallan por aserción; las otras nueve pasan, porque ese lector ya aplicaba bien la regla.
- Nulo (`mutar_adenda3_salida.txt`): mutaciones de una línea del lector, cada una atrapada por aserción (hito con
  «<=», cualquier plataforma, aunque haya alerta de la tabla, hito corrido, sensor de la banda I, la N-3 vuelve a
  vetar, sin el total de P1, la lista sin pedir etiqueta, elegibles informativos con el P1 que veta, acepta cualquier
  analizador, veredicto sin la marca, lista sin imprimir, se salta la compuerta de la adenda 1, `--salida` reconocida
  sólo escrita aparte); la identidad PASA y el control que se cae sale CAÍDA. Sin atrapar, declaradas por
  equivalentes: quitar «protegida» de la condición (sólo se consulta sobre etiquetas protegidas), listar con el canal
  que decide en vez de «todo» (sin alerta de la tabla sólo hay etiqueta en O, donde coinciden) y, en los elegibles
  informativos, el P1 que veta en vez del total con la tabla sola (en ese canal una protegida exige alerta de la
  tabla y nunca es N-3; VA3-03). Sin cubrir por una escena: los sha256 del lector y del compañero de la adenda 1.
- Verificador corto con contexto limpio (Sonnet, lanzado por S167, `experiments/_s167/v750b_adenda3_verificador/
  INFORME.md` en `loop/activo`), sobre `5b924379d`: SELLABLE CON CAMBIOS MENORES, con VA3-01 (gravedad 3) como
  condición del sello. Arreglados en esta versión: VA3-01 (compuerta de la adenda 1), VA3-02 (`--salida=ruta`),
  VA3-03 (rojo de comportamiento separado del de texto, tercer equivalente declarado), VA3-04 (N8 fuera de la carpeta
  sellada); VA3-05 (N5 es la regla actuando) queda dicho en el §3.
- Comandos (rutas absolutas en la máquina de Nicolás; temporales en D:):
  `python adenda3/probar_adenda3.py --evaluador <evaluar_d25.py del tag s161-d25-lectura> --dest <carpeta>`,
  la misma con `--lector analizar_v750b.py` para el rojo, y `python adenda3/mutar_adenda3.py --evaluador <...> --dest
  <carpeta>`.

### 5. Límites declarados

- La regla usa los campos que la población ya trae (`protegida`, `alerta_tabla`, `sensor`, `hora_utc`); si la lista
  del 2026-11-03 trae `alerta_tabla` mal calculado, la regla hereda ese error. Lo vigila la cuenta de N-3 que se
  informa al generar los objetivos.
- La regla no distingue si la alerta del OCR resultó ser de la misma pasada: es una regla por clase, igual que en el
  auto-audit y en V375-E. Una N-3 que sí era real y que un brazo pierde queda listada por nombre, no escondida.
