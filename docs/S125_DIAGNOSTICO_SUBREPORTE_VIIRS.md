# Por qué VIIRS sub-reporta y MODIS no — diagnóstico S125

> Todos los números salen de scripts sobre los JSON operacionales; ninguno está
> transcrito a mano (regla S91). El A/B de magnitud que precede a este documento
> está en `docs/S125_AB_MAGNITUD_RESULTADO.md`.

## El hecho

Ratio nuestro/MIROVA sobre **1049 pares nocturnos** (se descartaron 171 alertas
diurnas de MIROVA: son artefactos de reflexión solar, regla A76, y nuestro
pipeline es night-only — perderlas es correcto):

| sensor | n | ratio mediana |
|---|---|---|
| MODIS (1 km) | 50 | **1,08** |
| VIIRS 750 m | 195 | 0,83 |
| VIIRS 375 m | 804 | **0,69** |

Y el sesgo **cambia de signo con el régimen**, no es un factor constante:

| MIROVA reporta | n | ratio |
|---|---|---|
| < 0,05 MW | 32 | **1,70** (sobre-reportamos) |
| 0,05 – 0,1 | 122 | 1,19 |
| 0,1 – 0,2 | 179 | 0,81 |
| 0,2 – 0,5 | 355 | **0,66** |
| 0,5 – 1 | 161 | **0,61** |
| 1 – 5 | 199 | **0,66** |

O sea: en el rango que importa para monitoreo (≥0,2 MW) falta un tercio, y en la
cola muy débil sobra.

## Causa 1 — el área integrada se derrumba con la resolución

| sensor | píxeles por cluster (mediana) | área integrada | clusters de 1 solo píxel |
|---|---|---|---|
| MODIS | 4 | 4,00 km² | 23 % |
| VIIRS 750 m | 2 | 1,13 km² | 41 % |
| VIIRS 375 m | **1** | **0,14 km²** | **87 %** |

**28 veces menos área integrada** de MODIS a VIIRS 375. Y el 87 % de los clusters
de VIIRS 375 son de un solo píxel — al revés de lo que uno esperaría: a mejor
resolución, una anomalía debería repartirse en MÁS píxeles, no en menos.

Físicamente el VRP per-píxel es invariante a la resolución (el área entra
multiplicando y el contraste dividiendo). Lo que NO es invariante es **cuántos
píxeles se suman**: si el foco y su halo se reparten en varios píxeles de 375 m y
el pipeline se queda con uno, se pierde la fracción restante. En MODIS el mismo
foco cabe en un píxel y no se pierde nada.

## Causa 2 — el fondo de VIIRS 375 está sistemáticamente más caliente

Comparando las dos bandas de VIIRS **en la misma pasada** (mismo satélite, misma
hora, mismo terreno) sobre 21.511 pares:

| | |
|---|---|
| t_bg(375 m) − t_bg(750 m) | **+2,49 K** (mediana), p25 +1,54 / p75 +4,57 |
| pasadas donde 375 m tiene el fondo más caliente | **100 %** |

Con un contraste típico de ~10 K, inflar el fondo 2,5 K se come un cuarto de la
señal — el orden del sub-reporte.

### La máscara de nube NO es la causa (hipótesis refutada)

| | diferencia de fondo |
|---|---|
| la máscara descartó > 500 px | +2,32 K |
| la máscara **no** descartó nada | **+2,77 K** |

Si fuera la máscara, la brecha desaparecería cuando no enmascara. Pasa lo
contrario. La máscara sigue siendo un problema real (produce las 15 noches
ciegas de Chillán, ver D14) pero **no sesga el fondo**.

### La causa real: un anillo de fondo distinto, exclusivo de VIIRS 375

`ENABLE_TEST1_INTERMEDIATE_BG = True` con
`TEST1_INTERMEDIATE_BG_RING_KM = (1.5, 3.0)`.

`process_viirs.py:1656-1678` estima el fondo del Test 1 en un anillo de **1,5 a
3 km** del cráter y le da **precedencia** sobre el anillo global. MODIS
(`process_modis.py:1263`) y VIIRS 750 (`process_viirs_mod.py:1140`) usan el
global de **5 a 25 km**.

Un anillo a 1,5–3 km cae **sobre el edificio volcánico**, dentro de la aureola
térmica del cráter. Eso es exactamente lo que la Eq. 6 de Coppola busca evitar:
el fondo debe representar terreno no afectado. Fondo caliente → ΔL chico → VRP
bajo. Signo correcto y magnitud coherente con los +2,5 K medidos.

**Nota**: este anillo se adoptó en S112 (#439/#440) y ya había sido señalado como
sospechoso en S123 (frente #506, Villarrica con magnitud 35× desde junio).

## Lo que esto dice del A/B que acabamos de correr

**Ninguno de los cuatro brazos tocó estos dos mecanismos.** El A/B probó:

- `cluster_focal_vrp_mw` — que **no se aplica a VIIRS 375** (sólo MODIS y V750).
- `apply_single_pixel_mode` — que sí, pero es el menor de los recortes.
- `cluster_corona_background` — cableada **sólo en MODIS**.

El recorte dominante de VIIRS 375 es un **tercero**:
`ENABLE_TEST1_CONTEXTUAL_FILTER = True` (`process_viirs.py:1628-1639`), que
reduce los píxeles del Test 1 a los contextualmente anómalos más el pico. Es el
análogo del focal pero para VIIRS, y **quedó activo en los cuatro brazos**.

Por eso el A/B movió sólo +0,10: apagó los recortes que VIIRS casi no usa, y dejó
intactos los dos que lo gobiernan.

## Qué probar ahora (el A/B que corresponde)

Tres piezas exclusivas de VIIRS 375, aislables por flag:

| brazo | qué apaga |
|---|---|
| **E** | `enable_test1_contextual_filter` — el recorte de píxeles |
| **F** | `enable_test1_intermediate_bg` — vuelve al anillo global 5-25 km |
| **G** | ambas |

Criterio pre-registrado igual que el anterior, pero **estratificado por sensor**
(mezclar MODIS con VIIRS en una mediana única fabricó la falsa bimodalidad de
Láscar), y con el control interno: MODIS y VIIRS 750 **no deben cambiar**, porque
ninguna de las dos piezas los toca. Si cambian, el A/B está mal montado.

Predicción: F debería explicar la mayor parte, porque el fondo entra en todos los
píxeles y su sesgo (+2,5 K sobre ~10 K de contraste) es del orden del déficit.

## Lo que NO hay que concluir

- No "VIIRS está roto": los coeficientes, el área nadir, la longitud de onda y el
  anillo global son correctos y están verificados. El problema son dos decisiones
  de método aplicadas sólo a un sensor.
- No adoptar nada de esto sin A/B: las dos piezas se adoptaron en su momento con
  una razón (cortar el halo nival, evitar contaminación del fondo local), y
  apagarlas puede destapar lo que vinieron a resolver.
