# S178: C-montaje no se puede correr tal como quedó sellado (propuesta para que decida Nicolás)

Fecha: 2026-11-10 (UTC). Escrito ANTES de mirar la vía de D2 en ninguna ventana (sólo se contó el campo `roi` de los
records de VIIRS 750 de D2, que es parte del montaje). Rama loop/activo.

## Qué pasa, como geólogo

La prueba retrospectiva pregunta si la vía «código MIROVA» sigue viendo el cráter como MIROVA fuera de los meses en que
se eligieron sus reglas. Antes de creerle, C-montaje comprueba algo más básico: que la vía que corrió en D2 sea la
misma que se midió en los tres A/B (MOD-D fase 4 en MODIS, V375-E en VIIRS 375 y V750-B en VIIRS 750), comparando en
la quincena DM (2026-10-01 a 10-16), que corrió en los dos lados. Si no son la misma, lo que se lea en febrero, marzo y
2025 sería de otra vía.

El pre-registro sellado (§6, fila C-montaje) nombra qué comparar en cada A/B, pero no dice en qué campo del record está
ni con qué tolerancia, y el lector lo dejó como PENDIENTE a propósito («no se inventa»). Al buscarlo (S178):

| A/B | qué nombra el §6 | qué guardó el A/B en DM | qué trae el record de D2 |
|---|---|---|---|
| MOD-D fase 4, brazo V | máscara, VRP a 0,001 MW, clase | records de la vía (`v_slim`, con `via_codigo_mirova`), 354 líneas DM; la máscara en el npz de la grilla (`mascara`) | VRP, clase, y de la máscara sólo conteos (`diag_codigo_mirova.n_abs`, `n_p1`, `n_p2`), no las celdas |
| V375-E, lectura lejana | la lectura lejana | ningún record del pipeline: el port sobre las grillas npz (`port.C13`: `vrp_mw`, `pixeles`, `vrp_banda`) en 27 pasadas DM del lote FAR y tres lotes más | VRP y número de píxeles del cúmulo |
| V750-B con B4 | banda de triangulación de V750-A §4.1 | el oráculo (`oraculo.B0` y `oraculo.B1`, `vrp_banda` [mín, máx]); B4 es B1 en Cordón Caulle y Tupungatito y B0 en los otros nueve; 460 pasadas DM | VRP y `roi` |

Ubicación de los datos (todos en disco local; el primer artefacto de Actions vence el 2026-11-21):
MOD-D `D:/vrp-trabajo/temporales/s170_t1`, `s170_t2`, `s170_t3`; V375-E `D:/vrp-trabajo/temporales/s167_v375e_far/run_40773794395`
y los lotes de `s159_portes` y `C:/vrp-trabajo/temporales/s162_v375`; V750-B `D:/vrp-trabajo/temporales/v750b_r4_20261103`.

Tags de despacho encontrados (ningún documento los declara «de origen»; salen del mensaje del tag y del `head_sha` del
run): MOD-D `s170-modd-f4-candado` (d65fd231d); V375-E `s166-v375e-adenda2-sellada` (67838f2a5; el run salió de
a57b0dca7, que desciende de él); V750-B `s169-v750b-objetivos-20261103` (94f67fd6c) y su relanzamiento
`s169-v750b-relanzamiento-20261103` (dd8fc62b0).

Mientras C-montaje esté rojo, el lector deja los tres sensores en INDECIDIBLE (es un control común). C-K ya está verde
(3.138 pasadas, 0 diferencias, commit 2bfc9164b) y la caja B4 quedó arreglada en el lector (PR aparte).

## Lo que hay que decidir

Llenar los huecos es fijar una regla que el sello dejó abierta. Va antes de mirar nada y la decides tú.

**Opción A (recomendada): fijar las tres comparaciones así, antes de correr, y construirlas con TDD.**
1. MODIS contra MOD-D: presencia de la pasada, `primary_cluster.vrp_mw` a 0,001 MW, `distance_class`, y de la máscara
   el número de celdas alertadas (npz `mascara` contra `n_p1`/`n_p2` del record), porque el record no guarda las celdas.
2. VIIRS 375 contra V375-E: presencia, VRP del cúmulo contra `port.C13.vrp_mw` a 0,001 MW y píxeles contra
   `port.C13.pixeles`, en las pasadas DM de los cuatro lotes.
3. VIIRS 750 contra V750-B: presencia y VRP de la vía dentro de la banda `vrp_banda` del brazo que B4 usa en ese
   volcán (B1 en Cordón Caulle y Tupungatito, B0 en los otros nueve), que es la banda de V750-A §4.1.
4. Tags de origen: los de arriba, escritos en `TAGS_MONTAJE_ESPERADOS` del lector.
5. Toda diferencia se explica sólo como dice el §6: un hunk del `git diff` re-corrido con el código del tag de origen,
   u otro gránulo. Re-correr MODIS exige el runner (pyhdf no corre en Windows).

Costo: un adaptador por formato y tres comparadores con sus pruebas (una sesión de trabajo), más un despacho corto en
Actions si aparecen diferencias de MODIS. Riesgo: si la máscara por conteo deja pasar una diferencia real de celdas,
se ve en el VRP, que sí se compara a 0,001 MW.

**Opción B: dar C-montaje por no aplicable.** No la recomiendo: el sello dice que una diferencia sin explicar deja todo
INDECIDIBLE, y saltarlo es leer la prueba sin saber si mide la vía que se va a encender.

**Opción C: correr sólo MODIS (el único A/B con records del pipeline) y dejar VIIRS INDECIDIBLE.** No sirve para lo que
buscas (encender VIIRS).

## Decisión de Nicolás y declaración (antes de correr; nada de D2 mirado salvo el campo `roi`)

Nicolás, 2026-11-10, en la conversación de S178: «Sí, opción A». Lo que sigue fija la opción A en detalle. Un único
cambio respecto del texto de arriba, en la dirección más estricta: la máscara se compara **celda por celda**, no por
conteo, porque al mirar los formatos resultó que el record de la vía sí guarda las celdas (`anomaly_pixels`; en VIIRS
con `fila` y `col`, `pipeline/mirova_v750_codigo.py` l. 726 a 731) y los tres A/B también (MOD-D: `v_slim.anomaly_pixels`
con lat y lon; V375-E: `port.C13.pixeles` y V750-B: `oraculo.<B>.pixeles`, ambos con fila y columna en sus dos primeras
posiciones).

**Qué pasadas se comparan.** Sólo las de DM (2026-10-01 a 10-16 UTC) que el A/B midió, en los 11 Tier A. Clave:
volcán, plataforma (del sensor del record; en V375-E y V750-B, del prefijo del gránulo o de los archivos: VNP Suomi NPP,
VJ1 NOAA-20, VJ2 NOAA-21) y hora al minuto. Las pasadas de D2 que el A/B no midió no se comparan (el A/B no las tiene).

**Qué es una diferencia, por A/B** (`primary_cluster.vrp_mw` del record de D2, redondeado a 0,001 MW por el pipeline;
por eso ninguna tolerancia más fina tiene sentido):
1. MODIS contra MOD-D fase 4, brazo V (`v_slim` de las líneas DM de `f4_parte*.jsonl` en `s170_t1` a `s170_t3`):
   falta la pasada en D2; o el conjunto de celdas alertadas (lat y lon a 5 decimales) difiere; o |VRP D2 − VRP V| > 0,001
   MW; o `distance_class` difiere.
2. VIIRS 375 contra V375-E (`port.C13` de las pasadas DM del lote FAR y de los lotes S159, S162 y S162b): falta la
   pasada; o el conjunto (fila, col) de `anomaly_pixels` difiere de las dos primeras posiciones de `pixeles`; o
   |VRP D2 − `vrp_mw`| > 0,001 MW (vacío cuenta como 0).
3. VIIRS 750 contra V750-B con B4 (`oraculo.B1` en Cordón Caulle y Tupungatito, `oraculo.B0` en los otros nueve, de
   `art_41615021658` y `art_41693265163`): falta la pasada; o el conjunto (fila, col) difiere; o el VRP de D2 está a más
   de 0,001 MW de la banda `vrp_banda` (de `vrp_mw` si la banda no viene; vacío cuenta como 0).

**Tags de origen** (`TAGS_MONTAJE_ESPERADOS`): MOD-D fase 4 `s170-modd-f4-candado`; V375-E
`s166-v375e-adenda2-sellada`; V750-B `s169-v750b-objetivos-20261103` (las pasadas del relanzamiento,
`s169-v750b-relanzamiento-20261103`, se marcan con su tag y su diff también se lista).

**Explicación de una diferencia** (§6, sin cambio): `otro_granulo` si el gránulo de D2 no es el del A/B (comparado
por nombre de archivo sin versión de proceso), o `hunk` con el hunk escrito tras re-correr esa pasada con el código del
tag de origen. Nada más cuenta. En V375-E y V750-B lo medido fue el port y el oráculo, no el pipeline: una diferencia
ahí significa que la vía del pipeline no reproduce lo que se midió (V750-A §4.1 exige máscara idéntica), y si no la
explica otro gránulo queda sin explicar y C-montaje sigue rojo. No se ensancha ninguna tolerancia al ver datos.

## Resultado (2026-11-10 08:11 UTC) y la decisión que queda

Corrida con el código del PR #979 (commit 6a07f8ea2), D2 en DM (12 trozos), los tres A/B en disco. Salida:
`montaje_dm_salida.json`.

- **MODIS contra MOD-D fase 4: 343 pasadas, 0 diferencias** (mismas celdas, VRP a 0,001 MW, misma clase).
- **VIIRS 750 contra V750-B con B4: 440 pasadas, 0 diferencias.**
- **VIIRS 375 contra V375-E: 166 pasadas, 12 diferencias**, todas de VRP: mismas celdas, mismas temperaturas de
  brillo, mismo gránulo (el mismo archivo, versión incluida). Diferencia entre 0,3 % y 3 %, con signo variable.

Como geólogo: la vía y el port ven exactamente los mismos píxeles calientes; lo único que cambia es el fondo que se le
resta bajo el halo, que se interpola con una triangulación numéricamente inestable. El propio port de V375-E midió esa
inestabilidad (`vrp_banda`, 20 semillas de jitter), y **las 12 caen dentro de su banda** (`banda_v375.py`,
`banda_v375_salida.txt`; 9 con holgura, 3 en el borde dentro de los 0,0005 MW del redondeo del record).

Con la declaración tal cual, ninguna de las 12 se explica (no es otro gránulo y re-correr con el código del tag de
origen da el valor del port), así que **C-montaje queda PENDIENTE y, por el §6, los tres sensores INDECIDIBLES**.

**DECIDE NICOLÁS** (rotulado *post hoc*: se ve después de correr):
- **Opción 1 (recomendada):** en VIIRS 375 comparar también contra la banda de triangulación del port, como ya se
  hace en VIIRS 750 (es el criterio de V750-A §4.1 y la banda la calculó el A/B en octubre, no ahora). C-montaje pasa
  y se lee D2 a D4. El costo es aceptar un criterio fijado después de ver estas 12 pasadas.
- **Opción 2:** mantener la declaración: C-montaje rojo y la retrospectiva entera INDECIDIBLE hasta un instrumento
  nuevo (por ejemplo, que la vía guarde su propia banda), lo que obliga a re-correr D2.
