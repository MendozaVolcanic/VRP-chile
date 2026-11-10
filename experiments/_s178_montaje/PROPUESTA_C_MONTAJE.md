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
