# Pre-registro V750-B (S162): la región sensible (ROI) del código de MIROVA, por volcán, en VIIRS 750

Estado: **BORRADOR para el sello de Nicolás.** No se despacha nada hasta (1) el sello, (2) que la sesión del
instrumento entregue la cobertura contra la referencia (fase 0, programa §8.1) y (3) que la coordinadora (S162,
sesión «Retomar») lo meta en el despacho combinado de la fase 1. Autor: sesión hija VIIRS 750 (loop
`tasks/LOOP_VIIRS750.md`), 2026-10-24. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §3.

## 1. La pregunta, como geólogo

El código de MIROVA mira cada volcán en una grilla de 67 × 67 celdas de 750 m centrada en su propio punto (el centro
del TIF). Dentro de esa grilla hay una zona «de cumbre» donde los umbrales son sensibles (5 sigma, piso 0,003) y un
anillo donde son de escena (10 sigma, piso 0,02). El `.m` publicado trae una caja de cumbre de 7 × 7 celdas (±2,6 km)
y dice en sus comentarios que la región se ajusta por volcán. Eso importa en dos volcanes:

- **Cordón Caulle**: el calor no está en el centro de la grilla sino en el campo del lacolito, a 4,6 a 10,5 km según
  MIROVA; nuestro cráter de `volcanoes.yaml` está a 7,6 km del centro. Con la caja de 7 × 7 el código pierde 6
  protegidas que MIROVA sí publicó (censo S159, `experiments/_s159/oraculo_censo/INFORME.md` C-1).
- **Tupungatito**: el cráter está a 4,9 km al NW del centro; la caja de 7 × 7 no lo cubre.
- (Planchón-Peteroa: cráter a 2,0 km del centro, dentro de la caja pero en el borde.)

La pregunta es qué zona sensible reproduce a MIROVA **en las dos direcciones**: publicar sus alertas (sobre todo las
de 1 MW o más) y callar en las noches en que no vio nada. El resultado fija la ROI del paquete V750-A.

El verificador de V750-C agregó dos cosas que este pre-registro hereda: (1) en Tupungatito las 17 cumbres tibias que K
ve y el `.m` calla caen a 4,4 a 5,4 km del centro de la grilla, en la zona conservadora, y es la ROI la que las calla
antes que la interpolación; (2) la «caja por defecto» (B0) es un supuesto de **una** matriz de ejemplo de 2023 (BOX ==
2 de 7 × 7 central, BOX == 1 de 21 × 19, que aquí se simetriza a 21 × 21), y el comentario del `.m` (l. 105-125) dice
que la ROI se mueve, cambia de forma o de tamaño por volcán. O sea que ningún brazo es «la ROI de MIROVA»: son lecturas
candidatas, y la que gane se elige por cómo reproduce lo que MIROVA publicó y calló.

Lo que ya se sabe (no se re-mide como hallazgo, se usa como control): en el censo, la caja por defecto pierde 6
protegidas y publica 5 negativos limpios de 5.353; el recuadro sensible de 21 × 21 no pierde ninguna, gana 1 y publica
15 (ΔE −90 contra K). En la muestra de V750-C (`experiments/_s162_v750c/INFORME.md` V750C-4) el círculo
`inner_radius_km` sensible y el 21 × 21 sensible detectan las 78 protegidas; el círculo publica 12 negativos del lote
contra 8.

## 2. Brazos

Todos son el código de MIROVA (port de R2, `experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py`, validado contra
Octave en 791 de 791 escenas, S159 O1) sobre la grilla GEO con interpolación lineal (esquina `X0 ± 25.000 m`, paso
750, S159 GEO), sin compuerta, sin recorte, con su fondo y su suma. Sólo cambia la matriz BOX:

| brazo | zona sensible (BOX = 2) | anillo de escena (BOX = 1) |
|---|---|---|
| **B0** O-def | 7 × 7 en el centro de la grilla (el `.m`) | 21 × 21 en el centro |
| **B1** O-sens | 21 × 21 en el centro | (ninguno) |
| **B2** O-cráter | 7 × 7 centrada en la celda del cráter de `volcanoes.yaml` (`vent_lat`, `vent_lon`) | 21 × 21 en el centro |
| **B3** O-círculo | círculo de radio `inner_radius_km` (lista del tablero, `banco_paridad.inner_desde_html`) en el centro | el resto del 21 × 21 |
| **B4** O-sens-PT | B1 en Cordón Caulle y Tupungatito; B0 en los otros nueve | |
| **K** | producción (`calculate_vrp` de `pipeline/process_viirs_mod.py` sobre el mismo gránulo) | |

Además, dos brazos de diagnóstico que **no deciden V750-B** (son la confirmación de V750-C, mismo gránulo y misma
corrida):

| brazo | qué |
|---|---|
| **N0** O-nativo-def | el código sobre la ventana NATIVA del gránulo (filas y columnas del barrido, 67 × 67 píxeles alrededor del píxel más cercano al centro), caja 7 × 7 y 21 × 21 en píxeles nativos |
| **N1** O-nativo-sens | ídem con 21 × 21 sensible |

N0 y N1 corren sólo en el subconjunto **S_C**: las 66 cumbres negativas y las 48 cumbres con alerta de V750-C, las
alertas que deciden de la ventana y 300 negativos limpios sin ningún píxel de K, sorteados con semilla 162 entre los de
la ventana (lista fija en `objetivos_sc.json`, que se commitea antes del despacho).

Sin brazo con la matriz de ejemplo tal cual (anillo de 21 × 19 en vez de 21 × 21): en el `.m` la zona 0 y la zona 1
usan los mismos umbrales conservadores (`MIROVA_VIIRS750_hotspot_detection.m` l. 389-395), así que el tamaño del anillo
no puede cambiar ninguna máscara (medido: 0 de 510 grillas de N). Lo único que decide es dónde está la zona sensible.

**Insumos que el run guarda** (para no volver a bajar gránulos en la ablación local siguiente): la grilla GEO lineal
(`m13`, `m15`, float32) de todas las pasadas, y la ventana nativa (`lat`, `lon`, `M13`, `M15`, fila y columna del
barrido, float32, hasta 45 km) de las pasadas de S_C. Tamaño estimado: ~170 MB y ~30 MB comprimidos.

## 3. Población y ventanas (programa §2, A119, A104)

- VIIRS 750 nocturno (`dayflag = 0`), los 11 volcanes Tier A, pasadas con record de producción y con fila de la
  referencia de MIROVA a ±120 s.
- **T** (decide con la tabla sola): 2026-04-01 a 2026-06-12. **O** (tabla más OCR, la tabla sola al lado):
  2026-06-13 a 2026-11-02 12:59 UTC, sin el 13 ni el 17 a 20 de octubre (D-29). El 12-oct sólo con los cuatro gránulos
  rescatados de LAADS (patrón `experiments/_s159/oraculo_censo/probe_rescate.py`); si alguno no baja, el 12-oct se
  excluye en todos los brazos. Toda la ventana es anterior al cese de Suomi NPP (2026-11-02 13:00 UTC).
- Cortes informados por tramo: #535 (no separa brazos), adopción de K (2026-10-18 09:57 UTC).
- Lista de objetivos: `01_objetivos.py` de `experiments/_s159/oraculo_censo/` con la ventana extendida, regenerada y
  commiteada antes del despacho con su sha256.

## 4. Etiquetas y record

- Alerta, protegida (lectura A, ≥ 1 MW), regla SN (D-9) y negativo limpio: `scripts/clase_mirova.py`, con el arreglo
  de FALSO_POSITIVO de la sesión del instrumento si ya está mergeado (si no, se informa con y sin).
- **Cobertura antes del veredicto** (§8.1): toda pasada de la referencia sin record a ±120 s y todo día con pasadas de
  MIROVA y cero records se lista; una protegida sin record en todos los brazos que producción sí tiene es falla de
  cobertura, no del brazo. Las pasadas «no observadas» (volcán fuera del gránulo, cumbre sin dato) salen del
  denominador (censo C-5) y se cuentan aparte.
- Record de cada brazo del oráculo: **el cúmulo 8-conexo del píxel alertado más radiante** (corrige C-4 del censo), con
  su VRP calculado por el `.m` sobre la unión de los alertados (el VRP que MIROVA publica). Predicado «publica»: el del
  tablero, ejecutado con node (A97, `banco_paridad`). Secundario, para continuidad con el censo: el record de
  `record_oraculo` de N (centroide de todos los alertados).

## 5. Métricas (programa §2)

Por brazo, contra MIROVA, en T y en O por separado y en T ∪ O (con la tabla sola al lado en O):

- **P1** protegidas perdidas (veto): alerta de MIROVA ≥ 1 MW que el brazo no publica.
- **P1b** cruces de 1 MW en las dos direcciones: el brazo publica bajo 1 MW donde MIROVA dio ≥ 1, y ≥ 1 MW donde MIROVA
  dio bajo 1 o nada.
- **P2** suma de errores bajo 1 MW, E = alertas bajo 1 MW sin publicar + negativos limpios publicados; la diferencia
  contra B1 se decide con la **prueba de signos por bloque noche-volcán** (D-45: `prueba_signos_p2` y
  `regla_signos_p2` de `experiments/_s157_prereg_d25/evaluar_d25.py` en el tag `s161-d25-lectura`; exacta hasta 20
  bloques; GANA o PIERDE con p ≤ 0,05; BLOQUEA si el neto va en contra sin llegar; SIN SUSTRATO con 4 bloques o menos).
- Descriptivas: razón VRP brazo/MIROVA (mediana, cuartiles) en alertas y en protegidas; todo por volcán (con Cordón
  Caulle, Tupungatito y Planchón-Peteroa aparte), por tramo de 10° de cenit y por canal (tabla, OCR).

## 6. Regla de decisión (escrita antes de ver los datos)

1. **Elegible**: P1 = 0 en T y en O, con la tabla sola **y** con tabla más OCR. Un brazo que pierde una protegida no
   entra al paquete, aunque gane en P2.
2. Entre los elegibles, cada uno contra B1 por P2 (regla D-45). Se elige el que GANA contra B1; si dos ganan, el de menor
   E en T ∪ O.
3. Si ninguno gana contra B1 (empates o BLOQUEA), se elige por **cercanía al `.m`**, en este orden: B4 (cambia sólo dos
   volcanes respecto del `.m`), B2 (conserva la caja de 7 × 7, sólo la mueve), B1, B3 (B3 usa nuestra configuración,
   no la de MIROVA). Razón: a igual desempeño manda la fidelidad al código (decisión de Nicolás del 2026-10-21).
4. P1b no decide pero se informa; un cruce hacia abajo en una protegida ya es pérdida en P1.
5. **Decisión para Nicolás, no del pre-registro**: B4 y B2 son ajustes por volcán. MISSION excluye gates por volcán
   cuando son nuestros (A85), pero aquí el ajuste por volcán es de MIROVA (el `.m` lo declara). Si el elegido es B4 o
   B2, Nicolás confirma que eso es fidelidad y no un parche nuestro antes de pasarlo a V750-A.

## 7. Controles, leídos antes del veredicto

| control | qué tiene que dar | si no |
|---|---|---|
| K = producción | publica igual y `pc.vrp_mw` a 0,001 MW en todas las pasadas ok | el run no mide producción: se detiene la lectura |
| B0 y B1 = censo | mismo número de píxeles y VRP a 1e-6 que el censo S159 en las pasadas comunes | el oráculo cambió: se detiene |
| control positivo | B0 pierde al menos 1 protegida de Cordón Caulle (el censo vio 6) | el instrumento no ve la ROI |
| control negativo | B1 contra sí mismo (dos corridas del evaluador) da E idéntico y P2 SIN SUSTRATO o EMPATE | el evaluador no es determinista |
| cobertura | lista de §4 vacía, o cada caso explicado | SIN DATO declarado, nunca contado como acierto |
| N0/N1 actúan | N0 distinto de B0 en al menos una máscara de S_C | el brazo nativo no corre |

## 8. Predicciones (para poder fallar)

- B0: pierde 6 o más protegidas (todas de Cordón Caulle); no elegible.
- B1: 0 protegidas perdidas; negativos limpios publicados del orden de 15 en 5.353 (censo) más lo que agregue la
  ventana extendida.
- B2: recupera las de Cordón Caulle sólo si el lacolito cae en la caja de 7 × 7 alrededor del cráter del yaml; como
  MIROVA las ubica a 4,6 a 10,5 km del centro, predigo que **pierde** alguna (no elegible). Tupungatito: la recupera.
- B3: 0 perdidas; más negativos que B1 (V750-C: 12 contra 8 en la muestra).
- B4: 0 perdidas; menos negativos que B1 (sólo dos volcanes con la sensible).
- N0 (V750-C; predicción revisada antes de cualquier dato, tras el verificador de V750-C): si lo que calla las cumbres
  dentro de la caja es el promedio del remuestreo, N0 detecta en la celda de K en más de la mitad de las cumbres
  negativas que caen dentro del 7 × 7 (predigo 25 o más de unas 43) y en casi ninguna de Tupungatito (zona
  conservadora); N1 recupera además parte de Tupungatito. Si N0 no supera al vecino más cercano de la grilla (23 de
  38 en el censo), el remuestreo no es la pieza y lo que calla es la interpolación misma. Publica más negativos limpios
  que B0 en S_C.

## 9. Costo, escala y despacho

- Un run de sólo lectura, combinable con V375-B, V375-C y MOD-C (programa §7, fase 1). Referencia: el censo S159
  tardó 1 h 31 min con 32 trozos para 5.746 pasadas; con la ventana extendida a 11-02 serán unas 6.900 (SOSPECHA,
  se cuenta al regenerar los objetivos), más N0/N1 en ~600. Estimado 2 h con 32 trozos, timeout 90 min por trozo.
- Autentica sólo con `EARTHDATA_TOKEN` y falla al instante si viene vacío (A71); `"on":` entre comillas (A43);
  `pipefail` con `tee` (S141); sale 2 si falta una pasada.
- Lo despacha la coordinadora, desde un tag que fija el código (S152), en una rama auxiliar que no se mergea.
- Artefactos en C: (pedido de la coordinadora: D: está en ~9,7 GB), en `C:\vrp-trabajo\temporales\s162_v750b\`;
  parada si C: baja de 3 GB.

## 10. Lo que este pre-registro NO decide

- No adopta nada ni toca `pipeline/`: la ROI elegida entra al pre-registro de V750-A, que tiene su propio sello, tag y
  sí de Nicolás (A45).
- No decide el filtro de publicación del paquete (P-sinfiltro es de V750-A).
- No mide el diurno (V750-E) ni VIIRS 375 ni MODIS.

## 11. Pendiente antes del sello (lo hace esta sesión)

- `probe_v750b.py` (reusa `probe_n.py` y `probe_censo.py` de S159; agrega B2, B3, B4, N0, N1 y el guardado de
  insumos), `01_objetivos.py` extendido, `objetivos_sc.json`, `02_analizar.py` con la regla de §6, y su prueba sin red
  sobre las 510 grillas de N (B0 y B1 tienen que reproducir los números de N; B2, B3 y B4 tienen que dar distinto en
  Cordón Caulle o Tupungatito).
- Verificador limpio del pre-registro y del analizador antes del sello.
