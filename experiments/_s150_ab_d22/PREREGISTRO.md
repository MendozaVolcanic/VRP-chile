# Pre-registro S150: la conectiva max sin la compuerta D22 (abril a agosto de 2026)

> **SIN APROBAR TODAVÍA EN SU FORMA FINAL**: Nicolás aprobó el 2026-10-09 hacer esta prueba ("sí a todo",
> orden: primero este A/B, después la sonda de tres campos). Falta el verificador con contexto limpio; el
> despacho va después de él. Escrito y commiteado antes de correr.

## 1. El fenómeno y la pregunta

La meta del dueño: la réplica publica todo lo que MIROVA publica y calla donde calla. La conectiva `max` (brazo F)
bajó la publicación en negativos limpios de VIIRS 375 de 35,7 % a 2,7 % (abril a agosto) pero pierde alertas
débiles de MIROVA: 36 con etiqueta confiable (`docs/S150_ALERTAS_DEBILES_MAX.md`). De esas, **14 en VIIRS 375**
son un píxel apenas más caliente que su fondo (-1,1 a +3,0 K) que la compuerta D22 (`bt > t_bg + 3 K` antes de
los Tests 2 y 3; el paper no la tiene, Coppola 2016a p. 7) bloquea en el primer pase; con `min` las rescataba el
segundo pase sin condicionar, con `max` el segundo pase también las rechaza.

**Pregunta**: si se quita D22 encima de `max`, ¿vuelven esas alertas sin que vuelvan los falsos? Si MIROVA no
tiene la compuerta, debería ser así: los falsos los sigue filtrando la estadística de la escena.

Quitar D22 ya se probó en S143 (NO ADOPTAR), pero con el Test 1 encendido y `min`, que saturan la métrica (A114).

## 2. Brazos y despacho

| brazo | perfil | qué es |
|---|---|---|
| F (control) | `_s147_ab_sin_test1_max` | sin Test 1, conectiva `max` |
| F2 | `_s150_max_sin_d22` | F sin la compuerta D22 en VIIRS 375 |

Perfiles verificados: `diff_perfiles_d22_salida.txt` (F2 difiere de F sólo en
`ENABLE_TESTS_23_NO_BT_GATE_VIIRS375`). El flag llega al primer pase (`_eti_gate_bt`) y al segundo
(`apply_bt_gate`) de `pipeline/process_viirs.py`; el workflow escribe ese flag en la línea `FLAGS_BRAZO` del log.

Cinco despachos, uno por mes (abril, mayo, junio, julio, agosto 01 a 27), los 11 Tier A, brazos F y F2,
`control=_s147_ab_sin_test1_max`, desde `main`. Mismo workflow (`reproc-s146-ab-sin-test1.yml`) y mismas
referencias congeladas por mes que el A/B de meses (`experiments/_s149_prereg_invierno/_congelado/<mes>/`).
El código del detector es el mismo que el de esos runs: lo único que cambió en `pipeline/` desde entonces es
`first_processed_utc` en `store.py` (descriptivo).

## 3. Controles, antes de mirar nada

1. **Cobertura pareja** F contra F2 por mes (`evaluar_ventana.py`).
2. **Determinismo gratis**: F de este run contra F del run de meses de S149/S150 (mismo código del detector),
   misma decisión de publicar en 98 de cada 100 pasadas o más, por sensor. Si falla, nada decide.
3. **Cableado**: la línea `FLAGS_BRAZO` del log de cada job trae `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` = false
   en F y true en F2.
4. **La lista de pérdidas está fija de antemano**: `experiments/_s150_debiles/filas.json` (1.143 alertas que B
   publica; `perdida: true` en 46). El camino D22 y la etiqueta confiable salen de
   `experiments/_s150_debiles/clases_rechazo.py`, no se re-derivan después de ver el resultado.

## 4. Predicciones (VIIRS 375; VIIRS 750 se informa, D22 no lo toca)

| # | qué | regla | si falla |
|---|---|---|---|
| **P1** | F2 recupera las pérdidas del camino D22 | publica **al menos 7 de las 14** pérdidas de VIIRS 375 con etiqueta confiable y camino "solo 2.o pase, BT < t_bg + 3 K" | la compuerta no es la causa de esas pérdidas |
| **P2** | F2 no reabre los falsos | publicación en negativos limpios de F2 **≤ F + 3 puntos** en cada mes **y ≤ 18 %** (umbral de S147) | NO ADOPTAR |
| **P3** | lo que queda sigue sin cargarse al borde | razón borde/nadir de la tasa falsa de F2 ≤ 1,3 (con al menos 10 negativos por zona) | se informa |
| **P4** | F2 no pierde lo que F publica | F2 conserva **≥ 98 %** de las positivas que F publica, y ninguna de 1 MW o más | NO ADOPTAR |
| P5 | informativa | cuántas de las 22 pérdidas de VIIRS 375 del camino "primer pase" (18 con etiqueta confiable) cambian con F2 (no deberían: D22 no las bloqueaba) | |
| P6 | informativa | qué publica F2 de nuevo en negativos limpios: zona, magnitud, volcán | |

**Veredicto por mes y agregado**: MERECE SEGUIR si P1, P2 y P4 se cumplen en el agregado y P2 y P4 en cada mes;
NO ADOPTAR si P2 o P4 fallan; INDECIDIBLE si fallan los controles. Si los meses discrepan, se dice, no se promedia.

## 5. Instrumento

`evaluar_ventana.py` (control F, brazo F2) por mes y `medir_predicciones.py` para P2 a P4;
`recuperacion_d22.py` (en esta carpeta) para P1 y P5 contra la lista fija. Probado antes de despachar: con F
contra sí mismo en los cinco meses, las 14 pérdidas del camino D22 y las 22 del primer pase aparecen en las
tablas y F2 "recupera" 0: el instrumento ve las pasadas y no inventa recuperaciones (`recuperacion_d22_prueba_salida.txt`).

## 6. Costo

Cinco runs de 22 jobs (11 volcanes × 2 brazos), de a uno por el grupo de concurrencia; 4 a 6 h cada run. La
prueba de Nevados de Chillán (despacho desde el 2026-10-13) comparte el grupo: tiene prioridad.
