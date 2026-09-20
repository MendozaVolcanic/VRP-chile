# Verificador con contexto limpio del pre-registro `keep_peak` con dirección (S144, v1)

**Veredicto: la medida NO es viable tal como está escrita.** Hay dos defectos que deciden el resultado
antes de medir. (1) La Parte A no llega a su mínimo de 3 noches: el criterio de latencia deja 2. Por la
tabla de §7, eso hace que la medida completa salga INCONCLUSA, dé lo que dé la Parte B. (2) El disco
de búsqueda centrado en `mirova_center` deja fuera al píxel P en Tupungatito y en Puyehue-Cordón Caulle.
Son 9 de las 22 pasadas de la Parte B fuera de Lastarria, así que la fracción `P` sale empujada hacia
"casi nunca es el objeto". Además, las reglas "azar" y "≤ 1/3" son lo que entrega por defecto un
instrumento que no discrimina, y el placebo, tal como está escrito, no lo detecta.

Documento verificado: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md`
(v1, sin commitear, rama `s144-prereg-keep-peak-direccion`).

Mis scripts están todos fuera del repo, en
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\3a2a7912-9e56-4be4-b449-f2c2c5bbe439\scratchpad\`:
`g_control.py` (control G y funciones comunes), `neg_seed.py` (semillas en alertas y RUTINA),
`partb_n.py` (tamaño factible de la Parte B), `radial.py` (perfil radial del TIF). No toqué nada del
repo salvo este archivo.

**Aviso de contaminación (léelo antes de la v2).** Al medir las propiedades del instrumento sobre todas
las alertas de Lastarria calculé, como subproducto, la distancia al cráter de la semilla en las pasadas
con alerta de dos noches de la Parte A (Lastarria 2026-06-07 05:48 y 2026-07-25 05:48). Las dos dan
1,065 km. **No calculé la clasificación P/F/otro de ninguna noche ni de ninguna pasada.** Queda escrito
para que decidas si esas dos noches siguen siendo "sin mirar".

---

## Hallazgos (ordenados por gravedad)

### 1. La Parte A no puede dar veredicto: el criterio de latencia deja 2 noches, y por §7 la medida entera queda INCONCLUSA

- **Dónde**: pre-registro §4 criterio 3 (l. 56-57), §6 Parte A (l. 118-120), §7 (l. 139-143).
- **Evidencia** (mi consulta al índice `experiments/_s144_conteo_tif/_dl_tif/da4fe36e8920_index.csv`;
  latencia = primera `captured_at_utc` del md5 menos `acquisition_utc`):

  | noche | pasada con alerta | latencia | mediana del raster | ¿usable? |
  |---|---|---|---|---|
  | Isluga 2026-06-16 | 05:24 y 06:00 | sin TIF | | no (ya previsto) |
  | Láscar 2026-06-13 | 05:36:01 | **11,46 h** | 0,0757 | **no (latencia)** |
  | Lastarria 2026-06-07 | 05:48:01 | 2,85 h | 0,0662 | sí |
  | Lastarria 2026-06-14 | 06:06:02 | **13,3 h** | 0,0532 | **no (latencia)** |
  | Lastarria 2026-07-25 | 05:48:01 | 5,7 h | 0,0646 | sí |

- **Qué pasa**: sólo 2 noches cumplen los 5 criterios del TIF usable. La regla de la Parte A exige "al
  menos 3 noches clasificables", así que la Parte A sale INCONCLUSA por construcción, y la tabla de §7
  dice que "cualquier otra combinación" es INCONCLUSO. **La medida no puede terminar en ninguna de las
  dos filas con lectura, pase lo que pase en la Parte B.** Las dos imágenes excluidas tienen medianas
  de noche (0,053 y 0,076, muy por debajo de 0,2).
- **Cómo se ve en el resultado**: un INCONCLUSO que parece salir de los datos, cuando lo fijó el
  criterio antes de medir.
- **Contexto del criterio**: en las 2.187 imágenes nocturnas (03 a 09 UTC) que tengo en disco, 591
  tienen latencia > 8 h y **497 de esas 591 tienen mediana < 0,2**. De las 100 con mediana ≥ 0,2, 94
  ya tienen latencia > 8 h: el corte de mediana, solo, ya atrapa las escenas diurnas. Por mes, la
  fracción con latencia ≤ 8 h es 0,53 en mayo, 0,61 en junio, 0,65 en julio, 0,91 en agosto y 0,86
  en septiembre. **El criterio pega justo en los meses de las 5 noches.**
- **Cómo reproducirlo**: la consulta por noche está en este informe; el conteo mensual y la tabla
  cruzada se generan con el bloque que carga el índice en `g_control.py` más
  `pd.crosstab(n.lat>8, n.med>=0.2)`.
- **CONFIRMADO. Gravedad 5.**

### 2. El disco de búsqueda centrado en `mirova_center` deja fuera a P en Tupungatito y Puyehue-Cordón Caulle: la Parte B queda sesgada hacia "≤ 1/3"

- **Dónde**: pre-registro §4, l. 67-70: "Los 4 km cubren el disco de 3 km del Test 1 más una celda de
  margen, así que la búsqueda incluye al cráter y a nuestro píxel lejano por igual".
- **Evidencia**: el Test 1 se centra en el cráter (`get_detection_anchor`, que prioriza `vent_lat` y
  `vent_lon`: `pipeline/geo_utils.py:53-77`), no en `mirova_center`. La separación entre
  `mirova_center` y el cráter, según `volcanoes.yaml`, es de 7,57 km en Puyehue-Cordón Caulle, 4,86 km
  en Tupungatito y 2,02 km en Planchón-Peteroa (0,83 km en Láscar; ≤ 0,54 km en los demás). Revisé
  todos los records de producción V375 nocturnos con el patrón (1 píxel, P a más de 0,5 km de F,
  desde 2026-05-09). La fracción con P a más de 4 km de `mirova_center` es **1,00 en Puyehue-Cordón
  Caulle, 0,90 en Tupungatito y 0,21 en Planchón-Peteroa**, y 0,00 en los otros 8.
- **Tamaño factible de la Parte B** (`partb_n.py`): 138 pasadas tienen patrón y alerta de MIROVA a
  ±120 s. De ellas, 37 tienen TIF usable (15 en Lastarria y 22 fuera). **En 9 de esas 22 P queda fuera
  del disco R** (con margen de una celda): las 8 de Tupungatito y 1 de Puyehue-Cordón Caulle. En 7 de
  las 8 de Tupungatito, el que sí queda adentro es F (el cráter). En esas pasadas la semilla nunca puede
  ser `P`, y hacerla caer en F es fácil.
- **Qué pasa**: la afirmación de §4 es falsa para 3 de los 11 volcanes. Con 9 de 22 pasadas que no
  pueden dar `P`, la fracción `P` fuera de Lastarria tiene un techo cercano a 13/22 y un piso inflado
  de F y "otro".
- **Cómo se ve en el resultado**: "el píxel lejano casi nunca es el objeto de MIROVA", producido en
  parte por la geometría de la búsqueda.
- **Cómo reproducirlo**: `python partb_n.py` (desde el scratchpad). Para la separación, el bloque
  `hav(mirova_center, vent)` de este informe sobre `volcanoes.yaml`.
- **CONFIRMADO. Gravedad 5.**

### 3. "Azar" y "≤ 1/3" son lo que entrega por defecto un instrumento que no discrimina, y el placebo no lo atrapa

- **Dónde**: §6 Parte A (l. 119-120), Parte B (l. 126-127), placebo §5 (l. 101-104).
- **Qué pasa**: la semilla es un argmax sin umbral de z. Si cae al azar dentro del disco (R ≥ 4 km,
  unos 50 km²), la probabilidad de caer a ≤ 0,75 km de P es del orden del área de ese círculo sobre la
  del disco, **1,77 / 50 ≈ 3,5 %**. Con 3 noches, un instrumento ciego da "azar" (ninguna `P`) con
  probabilidad ≈ 0,965³ ≈ 0,90, y en la Parte B da una fracción `P` muy por debajo de 1/3. **Las dos
  conclusiones de la fila 1 de §7 son el resultado por defecto de un instrumento roto.** Este cálculo
  de área es mío, no está medido sobre imágenes.
- El placebo compara sólo la frecuencia de `P`, y "parecida" no está definido. Si el real da 0 y el
  placebo da 0, hay dos lecturas posibles y ninguna sirve: (a) "parecida", y entonces "azar" nunca
  puede declararse; (b) "no parecida" porque no se definió, y entonces "azar" pasa sin control. Además,
  frente a una fuente **persistente** el placebo acierta sin que el instrumento falle. En Lastarria, la
  misma celda (a 2,363 km del cráter) es la semilla en **14 alertas y en 11 pasadas RUTINA** (z mediano
  6,4 en las RUTINA) (`neg_seed.py`). Otra noche encuentra la misma celda, y el placebo lee eso como
  "no discrimina".
- **Cómo se ve en el resultado**: "la coincidencia de S143 fue de radio" declarada sin que el
  instrumento haya demostrado que puede ver a P cuando P es el objeto.
- **Falta un control positivo de identidad** (ver hallazgo 4). En cada pasada, la semilla debería caer
  en el radio que MIROVA publicó antes de que su posición cuente.
- **Cómo reproducirlo**: aritmética de área de este informe; recurrencia de celdas con
  `python neg_seed.py` y luego `pd.crosstab(l.dr, l.tipo)` sobre `neg_seed.csv`, filtrando Lastarria.
- **CONFIRMADO (la aritmética y la recurrencia); el tamaño exacto del sesgo en imágenes reales no está
  medido. Gravedad 4.**

### 4. La semilla principal ignora el radio que MIROVA publicó, y en Lastarria no es el objeto de MIROVA en 7 de 36 alertas

- **Dónde**: §4, l. 67-72 (la semilla principal es el máximo de ΔL0 en el disco; la variante del
  anillo `|r - Distancia_km| ≤ 0,6` "no decide").
- **Evidencia** (`neg_seed.py`, alertas con TIF usable). Hay alertas en que la semilla cae a un radio
  incompatible con `Distancia_km` para cualquier punto del intervalo que da la separación entre cráter
  y `mirova_center` (margen 0,6 km): **Lastarria 7 de 36, Planchón-Peteroa 5 de 30, Láscar 3 de 47**,
  Chaitén 1 de 15, Isluga 1 de 59, Villarrica 1 de 6, Tupungatito 0 de 45. En Lastarria la
  distancia de la semilla al cráter se agrupa en unas pocas celdas fijas (1,065, 1,305, 1,396 y
  2,363 km), y el `Distancia_km` de MIROVA sigue a esas celdas en la mayoría de los casos (2,40 con
  2,363; 1,55 con 1,396; 1,19 con 1,065; mediana de |semilla - distancia| 0,12 km). Donde no las sigue,
  hay dos focos en competencia y el máximo global elige el otro.
- **Qué pasa**: la pregunta es "¿dónde estaba el objeto que MIROVA publicó?", y el único dato de MIROVA
  sobre ese objeto es su radio. La definición principal lo descarta. En un volcán con dos focos (el
  caso de Lastarria, que aporta 3 de las 4 noches con TIF de la Parte A y 15 de las 37 pasadas de la
  Parte B), la semilla puede ser un objeto que MIROVA no publicó en esa pasada.
- **Cómo se ve en el resultado**: `F` u `otro` asignados a pasadas donde MIROVA publicó justamente algo
  a la distancia de P.
- **Cómo reproducirlo**: `python neg_seed.py` y luego el bloque de "discordantes seguros" de este
  informe sobre `neg_seed.csv`.
- **CONFIRMADO. Gravedad 4.**

### 5. Los records del brazo control de la Parte A vencen el 2026-10-02 y no están fijados por sha

- **Dónde**: §3, l. 43-45 ("bajados con `experiments/_s143_evaluador/bajar_tramos.py`"); la cabecera
  de §3 dice "todas fijadas por sha".
- **Evidencia**: `gh api repos/MendozaVolcanic/VRP-chile/actions/artifacts` muestra los artefactos
  `s143ab-t1-_s142_ab_control-*` (run 35266704955) con `expires_at` desde **2026-10-02T04:02** y los
  `s143ab-t2-_s142_ab_control-*` (run 35340495262) hasta **2026-10-03T01:51**. Hoy es 2026-09-19. La
  única copia local completa que encontré está en el scratchpad de otra sesión
  (`...\0a44fda0-e659-4f4d-80af-9f8577f14092\scratchpad\ab_fus\`), fuera del repo y borrable. Los JSON
  versionados de `experiments/_s143_evaluador/verificador_veredicto/` **no sirven** para la Parte A:
  cada pasada trae una sola posición (`pos`, que en los `test1_roi` es F) más dos distancias, no P y F
  por separado (`recuento.py:49-51`).
- **Qué pasa**: los records de GitHub Actions se fijan por id de run, no por sha, y duran 13 días más.
- **Cómo se ve en el resultado**: si el script llega después del 2 de octubre, la Parte A no se puede
  correr ni reproducir.
- **Cómo reproducirlo**: `gh api "repos/MendozaVolcanic/VRP-chile/actions/artifacts?per_page=100" --jq '[.artifacts[] | select(.name|test("control")) | [.name,.expires_at,.workflow_run.id]]'`.
- **CONFIRMADO. Gravedad 4.**

### 6. Láscar 2026-06-13 no es un píxel lejano, y en las 5 noches la coincidencia fue entre pasadas distintas

- **Dónde**: §1, l. 15-19 ("un cúmulo de un solo píxel a 2 o 3 km del cráter" y las 5 noches); §6
  Parte A, l. 111-116. La premisa viene de H1 del verificador S143 ("centroide a 2,2 a 2,8 km"),
  `experiments/_s143_evaluador/VERIFICADOR_VEREDICTO.md`, fila H1.
- **Evidencia**: leí los records del control en `ab_fus` y reproduje la cota con la lógica de
  `experiments/_s143_evaluador/evaluar.py:281-316`: se toma **cualquier** pasada publicada de la noche
  contra **cualquier** distancia de alerta de esa noche, con la posición `final_hotspot_si_test1`
  (`parametros.json`). Resultado:
  - **Láscar 06-13**: la alerta es a las 05:36 (1,55 km). El único record que pasa la cota es el
    `ctx_cluster` de las **04:42**, con P a **0,32 km** del cráter, F a 0,17 km y **d(P,F) = 0,49 km**.
    El patrón de la Parte A exige P a más de 0,5 km de F, así que **el record que produjo la
    coincidencia queda fuera de los candidatos**. El único candidato con patrón esa noche es el
    `test1_roi` de las 06:24 (P a 2,90 km), que no participó de la cota porque para los `test1_roi` el
    evaluador usa F, el cráter. H5 de S143 ya lo describía como un borde de cota de un píxel cerca del
    cráter (0,472 contra 0,609).
  - En las otras 4 noches la coincidencia viene de un `ctx_cluster` de **otra pasada**: Isluga 06:18
    contra la alerta de 06:00; Lastarria 06-07 06:36 contra la de 05:48; 06-14 05:00 contra la de
    06:06; 07-25 06:36 contra la de 05:48. **En la pasada con alerta, el record del control tenía P = F
    en las 5 noches** (en la de 06-14 06:06, d(P,F) = 0,19).
- **Qué pasa**: "las 5 noches de keep_peak lejano" son 4, y las 4 comparan el objeto de MIROVA en la
  pasada X con nuestro píxel en una pasada Y distinta, de otro satélite, entre 36 y 78 minutos
  después o antes. El diseño lo admite (unidad noche), pero §1 no lo dice. Hay además una prueba más
  directa que el documento no usa: el TIF de MIROVA **en la pasada Y**, donde publicamos P. Ese TIF
  existe en Isluga 06-16 06:18 (la noche que §6 declara SIN DATO) y en Láscar 06:24, Lastarria 06-07
  06:36 y 07-25 06:36 (índice, esta sesión). En esas pasadas MIROVA no dejó fila en CONS ni en OCR
  (`lab: sin` en `pasadas_control_literal.json`).
- **Cómo se ve en el resultado**: la noche de Láscar se clasifica con un record que no fue el que
  "coincidió", y el veredicto "azar" se lee como si hablara del píxel que causó la pérdida.
- **Cómo reproducirlo**: el bloque de lectura de `ab_fus` de este informe (imprime P, F, d(P,F) y las
  distancias a `mirova_center` por record de las 5 noches).
- **CONFIRMADO. Gravedad 3.**

### 7. En los candidatos `ctx_cluster` de Lastarria, P y F están a menos de 1,5 km, y la regla por noche no está definida

- **Dónde**: §4, l. 78-85 (T = 0,75); §6 Parte A (unidad noche, varios records).
- **Evidencia**: en producción (V375 nocturno desde el 2026-05-09, 1 píxel, d(P,F) > 0,5 km) la mediana
  de d(P,F) es 2,77 km y sólo el 6 % queda bajo 1,5 km (n = 2.999). **En `ctx_cluster` de Lastarria el
  52 % queda bajo 1,5 km** (n = 23), y los dos candidatos `ctx_cluster` de la Parte A en Lastarria
  tienen d(P,F) = **0,96** (06-07 06:36) y **1,29** (07-25 06:36). Con T = 0,75 los dos discos se
  traslapan, y una semilla entre ellos cae en `ambos`.
- **Qué pasa**: en las noches que más importan, T es demasiado grande para separar a P de F. Además, una
  noche puede tener varios candidatos con P distintos (Lastarria 06-07 tiene tres: 04:54, 05:30 y
  06:36), y el documento no dice cómo se agrega a "la semilla es P" por noche. La Parte B separa a
  Lastarria por el campo fumarólico, pero la Parte A no, aunque 3 de sus 4 noches con TIF son de
  Lastarria.
- **Cómo se ve en el resultado**: noches no clasificables que el analista resuelve después de ver los
  datos.
- **Cómo reproducirlo**: el bloque de d(P,F) por volcán y fuente de este informe sobre
  `data/mirova_equivalent/*.json`.
- **CONFIRMADO. Gravedad 3.**

### 8. La Parte B mezcla dos regímenes de código que la Parte A excluye por la misma razón

- **Dónde**: §3, l. 45-46.
- **Qué pasa**: la Parte A descarta producción "porque los de junio y julio se generaron con otro
  código". Las Partes B y C usan producción desde mayo, que cruza #535 (2026-08-28 23:00 UTC). La
  regla A104 del `CLAUDE.md` del proyecto pide medir por tramo. En ese cambio, 11 de las 12 pasadas
  `test1_roi` de S135 pasaron a ser `ctx_cluster` (D19, `docs/MIROVA_DIVERGENCES.md` sección D19,
  párrafo "Paso 0").
- **Cómo se ve en el resultado**: una fracción `P` que promedia dos mecanismos distintos de generación
  del patrón.
- **CONFIRMADO (la inconsistencia del texto); el tamaño del efecto no está medido. Gravedad 3.**

### 9. Sesgo por ruido compartido: el TIF de MIROVA y nuestro record salen del mismo granule (SOSPECHA)

- **Qué pasa**: en la Parte B y la Parte C, MIROVA y nosotros procesamos la misma pasada L1B. Si
  nuestro píxel P es el máximo de BT del disco en parte por ruido, ese mismo ruido sube su ΔL0 en el
  TIF de MIROVA. Así, `P` sale más seguido de lo que daría el azar, y z(P) > z(P') aunque no haya
  objeto. El placebo (otra noche) quita ese ruido compartido, así que "real > placebo" puede venir de
  eso y no del objeto. La Parte C mide justamente ese sesgo en negativos limpios, pero el documento la
  deja como "sólo informa" y no la conecta con la lectura de la Parte B.
- **Cómo se ve en el resultado**: "es el objeto" inflado en la misma pasada.
- **SOSPECHA (mecanismo razonado, no medido). Gravedad 3.**

### 10. El control G pasa, pero es casi sólo Láscar y no puede ver un corrimiento de una celda

- **Evidencia** (`python g_control.py Lascar,Villarrica 0.3`): 50 pasadas con TIF; **32 usables: 31 de
  Láscar y 1 de Villarrica**. La semilla cae a ≤ 0,75 km del cráter en el **93,8 %**, con mediana de
  0,179 km, desplazamiento medio de +0,067 km en norte-sur y -0,127 km en este-oeste, y z mediano de
  34. Sin el corte de latencia: n = 49, 93,9 %, mediana 0,128 km. Ninguna de estas pasadas está en
  grilla UTM, así que el informe separado para UTM que pide §5 tiene n = 0. La celda del TIF geográfico
  mide 0,377 × 0,376 km (Láscar).
- **Qué pasa**: G pasa hoy, pero valida un solo cráter del desierto con señal fuerte. No valida los
  nevados, ni las señales débiles (las alertas de Lastarria son de 0,03 a 0,3 MW), ni los bordes del
  disco (§8 del pre-registro ya lo reconoce). Con una tolerancia de 0,75 km (dos celdas) y una mediana
  ≤ 0,5 km, un corrimiento sistemático de **una** celda (0,38 km) pasa G. §5 dice que "se vería" en el
  desplazamiento medio, pero eso se informa y no es compuerta.
- **CONFIRMADO. Gravedad 2.**

### 11. El criterio de latencia no es el de S142 y la cita apunta a otra sección

- **Dónde**: §4 criterio 3, l. 56-57.
- **Evidencia**: S142 midió la latencia como `last_modified_utc - acquisition_utc`
  (`experiments/_s142_ndc/pixeles_mirova.py:202-203`). El pre-registro usa la primera captura del md5.
  Las dos se parecen (sobre 2.274 imágenes nocturnas propias, el 70 % y el 73 % quedan bajo 8 h), pero
  no son la misma definición. El hecho de los "~17 h después" está en `RESULTADOS.md` §2.1, no en §2.6
  (§2.6 punto 3 es la propuesta del filtro de 8 h).
- **CONFIRMADO. Gravedad 2.**

### 12. "El píxel de `keep_peak`" es una inferencia: el record no lo identifica (SOSPECHA)

- **Evidencia**: el record de Lastarria 06-07 06:36 del control (el que produjo la coincidencia) tiene
  `n_anomalous_pixels: 1`, `diag_n_second_pass_recapture: 1` y `triggered_test1: True`, y no trae
  ningún campo que marque el píxel conservado por `keep_peak`. Es posible que P sea el píxel que el
  second pass recapturó al lado del de `keep_peak`, y no el de `keep_peak` mismo. Como estaría a una
  celda, T lo absorbe, pero la etiqueta de §4 ("el píxel de `keep_peak`") es una suposición.
- **SOSPECHA. Gravedad 2.**

### 13. "Mismo satélite" no se puede calcular con el índice ni con los CSV

- **Evidencia**: el índice tiene las columnas `captured_at_utc, volcano, sensor, band, acquisition_utc,
  last_modified_utc, md5, size_bytes, tif_path, kmz_path` (cabecera leída). El CSV consolidado y el OCR
  de MIROVA sólo traen `Sensor` = VIIRS375. El satélite existe sólo de nuestro lado. En la práctica,
  ±120 s ya separa los satélites, que pasan con 36 minutos o más de diferencia, así que es un tema de
  redacción.
- **CONFIRMADO. Gravedad 1.**

---

## VERIFICADO LIMPIO

- **El TIF es radiancia con el gradiente topográfico, pero ΔL0 lo cancela en promedio.** En las pasadas
  RUTINA, la radiancia media por anillo desde el cráter sube de 0,0616 a 0,0923 en Villarrica (n = 144)
  y de 0,0639 a 0,0901 en Llaima (n = 144), entre 0-0,75 km y 5-8 km. Es el gradiente de A69 en el campo
  de MIROVA. La ΔL0 media por anillo queda en torno a 0 más allá de 1,5 km (orden 1e-5). Es algo
  negativa en la cumbre (-6e-4 en Villarrica y Llaima), lo que desfavorece un poco a las semillas en el
  cráter si la señal es débil, o sea que va en contra de F, no a favor de P (`radial.py`). En RUTINA,
  las semillas se reparten por área: el 31 % cae en el anillo de 2 a 3,2 km, contra 39 % esperado por
  área en un disco de 4 km (n = 945, `neg_seed.py`). **No encontré un sesgo sistemático de la semilla
  ΔL0 hacia el borde tibio donde vive P.**
- **La semilla distingue alerta de no-alerta en intensidad**: z mediano en alertas contra RUTINA,
  Lastarria 8,7 contra 4,1; Láscar 21,3 contra 4,2; Tupungatito 9,3 contra 3,4 (`neg_seed.py`).
- **Usar `mirova_center` como origen de `Distancia_km` es correcto.** En Tupungatito, 41 de 45 semillas
  de alerta están a ≤ 0,75 km del cráter mientras MIROVA publica ~4,9 km, que es la separación entre
  cráter y `mirova_center` (4,86 km). El problema del hallazgo 2 es el radio mínimo de 4 km, no el
  centro.
- **Criterio de contenido nocturno** (mediana < 0,2): deja fuera entre 5 y 17 imágenes por volcán de
  entre 174 y 227. Isluga es la que más pierde (17 de 174), así que Atacama queda sano. Ningún volcán
  se acerca a perder la mitad.
- **Ventana UTM**: 24 TIF UTM de 2.221 leídos (21 en EPSG:32719 y 3 en 32718, todos con celda de
  375 m), consistente con las 8 adquisiciones del 14 y 15 de septiembre que declara
  `experiments/_s144_conteo_tif/RESULTADO.md`. El resto es EPSG:4326 de 134 × 134, con celda de
  ~0,377 km. T = 0,75 km son en efecto unas dos celdas.
- **Isluga 2026-06-16** no tiene TIF a las 05:24 ni a las 06:00 (el índice sólo tiene 06:18:01 y
  18:48:01). La afirmación de §6 es correcta.
- **Separación típica P-F**: fuera de los `ctx_cluster` de Lastarria, T = 0,75 km es coherente
  (mediana 2,77 km, 6 % bajo 1,5 km).
- **El brazo control sí tiene los campos que necesita la Parte A**: `primary_cluster.centroid_lat/lon`
  y `final_hotspot_lat/lon` por separado, en los JSON completos de los artefactos (leídos en `ab_fus`).
  Lo que no los tiene es el resumen versionado de `verificador_veredicto/` (ver hallazgo 5).
- **§1: "Apagar `keep_peak` es lo único que baja la sobre-publicación en el A/B de S143"**: coincide con
  H2 de `VERIFICADOR_VEREDICTO.md`.
- **Cota nocturna del evaluador**: `evaluar.py:281-316` compara cualquier pasada publicada contra
  cualquier distancia de alerta de la noche, usando `mirova_center` como centro. El pre-registro la
  describe bien como "radios sin acimut".

**No verificado** (queda abierto para la v2): el tamaño de muestra del control H; el n de la Parte C
después de los filtros de usabilidad; el predicado node (no lo ejecuté); si el remuestreo geográfico de
MIROVA corre la posición en los nevados, fuera de Láscar.

---

## Correcciones recomendadas para una v2 (por gravedad)

1. **(5) Quitar la latencia como criterio de exclusión**, o dejarla sólo como análisis de sensibilidad
   o como estrato. El corte de mediana, solo, ya saca las 100 imágenes con nivel de escena diurna
   (94 de ellas también superan las 8 h). Lo único que la latencia agrega es sacar 497 imágenes con
   mediana de noche, y no hay evidencia de que esas estén mal fechadas. Si se mantiene, reescribir la regla de la Parte A para que con 2
   noches sea descriptiva de forma declarada, y **desacoplar §7** para que la Parte B pueda tener
   lectura propia aunque la A no tenga n.
2. **(5) Centrar el disco de búsqueda para que contenga a P y a F.** Por ejemplo, la unión de un disco
   de 3 km + una celda alrededor del cráter (`get_detection_anchor`) con el disco de `Distancia_km` + 1
   alrededor de `mirova_center`. Excluir y contar por separado las pasadas donde P o F queden fuera.
   Corregir la frase de §4.
3. **(4) Agregar un control positivo de identidad por pasada**: la semilla sólo cuenta si su radio
   desde `mirova_center` es compatible con `Distancia_km` (|r - d| ≤ 0,6 km). Si no, se usa la semilla
   del anillo, que pasa a ser la principal, y el máximo global queda como variante. Informar cuántas
   pasadas fallan la identidad.
4. **(4) Redefinir las reglas de veredicto para que "azar" exija evidencia positiva**: por ejemplo, una
   mayoría de noches o pasadas donde la semilla que cumple la identidad es `F` u `otro` a más de 2T de
   P, con z ≥ un umbral fijado antes (la mediana RUTINA por volcán más un margen, por ejemplo).
   Comparar real contra placebo sobre la distribución completa P/F/otro/ambos, con una regla numérica
   de "parecida". Declarar que en fuentes persistentes (Lastarria) el placebo no separa fuente fija de
   instrumento roto.
5. **(4) Bajar hoy los artefactos del control** con `bajar_tramos.py`, guardar el hash de cada JSON y
   dejarlos donde no se borren, antes del 2026-10-02.
6. **(3) Corregir §1 y §6**: Láscar 06-13 no es un píxel lejano (P a 0,32 km, d(P,F) = 0,49). Decir que
   en las 5 noches la coincidencia fue entre pasadas distintas. Decidir si Láscar sale de la Parte A o
   si se relaja el umbral de 0,5 km para ella (antes de medir). Considerar un brazo adicional con el TIF
   de la **pasada donde publicamos P**, que existe en Isluga 06:18, Láscar 06:24 y Lastarria 06-07 y
   07-25 06:36.
7. **(3) Definir la agregación por noche** cuando hay varios candidatos, y **separar Lastarria también
   en la Parte A**. Para los `ctx_cluster` con d(P,F) < 2T, fijar desde ya que cuentan como `ambos`, o
   bajar T para ellos.
8. **(3) Estratificar las Partes B y C por régimen**, antes y después de #535, o restringirlas al tramo
   posterior, con coherencia con la razón que excluye producción en la Parte A.
9. **(3) Convertir la Parte C en condición de lectura de la Parte B**: si z(P) > z(P') en negativos
   limpios, la fracción `P` de la Parte B se declara inflada por ruido compartido.
10. **(2) Ampliar G** a una pasada focal de nevado (Villarrica tiene 1) o declarar que valida sólo
    Láscar. Poner como compuerta un tope al desplazamiento medio (por ejemplo, < 0,19 km, media celda,
    en cada eje).
11. **(2) Citar la latencia como se define** (primera captura, no `last_modified`) y la sección correcta
    de S142 (§2.1).
12. **(2) Llamar a P "cúmulo primario de un píxel"** y no "el píxel de `keep_peak`", mientras el record
    no lo identifique.
13. **(1) Quitar "mismo satélite"** o decir que se infiere por la hora.
