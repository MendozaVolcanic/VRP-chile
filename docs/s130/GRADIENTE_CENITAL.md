# S130 · El sub-reporte crece con el ángulo cenital — y MIROVA es plano

Verificación del segundo frente de fidelidad (el remuestreo), con el control de
instrumento que faltaba. **El diagnóstico se confirma en VIIRS y no está probado en
MODIS.**

## Por qué se volvió a medir

El bloque de arranque heredaba de S129 que *«VIIRS375 va de 0,796 cerca del nadir a
0,570 entre 35° y 50°, IC sin solape»*. Regla de esta etapa: no heredar afirmaciones
sin trazarlas. Se remidió con la definición explícita, y el número cambió — pero la
conclusión se robusteció, porque además apareció el control que faltaba.

## Lo medido

`experiments/_s130_cenital/medir_gradiente_cenital.py`. Un par por (volcán, fecha,
bucket), máximo de cada lado, `pc.vrp_mw` nuestro (**A10**, nunca `record.vrp_mw`),
loader canónico CONS ∪ OCR (**A11**), sólo pasadas nocturnas, ventana 2026, once
Tier A. El ángulo es `|sensor_zenith_deg|`.

**Ratio nuestro/MIROVA por bin:**

| bin | MODIS | VIIRS750 | VIIRS375 |
|---|---|---|---|
| 0–15° | 0,778 (n 21) | 0,781 (n 94) | 0,740 (n 385) |
| 15–25° | 0,828 (n 21) | 0,631 (n 66) | 0,584 (n 334) |
| 25–35° | 0,862 (n 17) | 0,373 (n 62) | 0,466 (n 317) |
| 35–50° | 1,253 (n 18) | 0,396 (n 101) | 0,389 (n 587) |
| 50°+ | 0,400 (n 18) | 0,326 (n 93) | **0,253 (n 1144)** |

En VIIRS el descenso es monótono y grande: **2,9×** entre extremos en 375 m y
**2,4×** en 750 m. Y el bin más oblicuo es el **más poblado** en VIIRS375 (1.144 de
2.767 pares), así que la mayor parte de nuestras comparaciones vive en el régimen
más sesgado.

## El control de instrumento — lo que decide la lectura

Un ratio que cae con el ángulo admite dos lecturas opuestas: que **nosotros
perdemos** señal en oblicuo, o que **MIROVA la infla**. Separarlas exige mirar
numerador y denominador por separado.

**VIIRS375** (MW medianos):

| bin | n | nuestro | MIROVA |
|---|---|---|---|
| 0–15° | 385 | 0,159 | 0,230 |
| 15–25° | 334 | 0,140 | 0,270 |
| 25–35° | 317 | 0,096 | 0,230 |
| 35–50° | 587 | 0,081 | 0,240 |
| 50°+ | 1144 | **0,059** | **0,250** |

**MIROVA es plano** (0,23–0,27 en los cinco bins) y **el nuestro cae 2,7×**. En
VIIRS750 el patrón se repite: nuestro 0,966 → 0,264, MIROVA en ~1,0 hasta el último
bin.

La conclusión es nuestra, no de ellos.

## La explicación física

Un píxel VIIRS a 50° de nadir cubre mucho más terreno que uno a nadir. **Coppola
2014 §2.2** describe que MIROVA **remuestrea** a una malla de área constante: la
energía del píxel elongado se reparte en celdas de área nominal, así que su magnitud
**no depende del ángulo**. Nosotros integramos sobre el píxel tal como viene del
sensor.

Eso es exactamente lo que la tabla muestra: su serie plana, la nuestra cayendo.

## Lo que NO está probado: MODIS

Los valores de MODIS —0,778 · 0,828 · 0,862 · **1,253** · 0,400— **no son
monótonos**, y cada bin tiene entre 17 y 21 pares. Con ese n y ese ruido no se puede
afirmar ni negar el gradiente en MODIS.

No es un detalle menor: la corrección del remuestreo se justifica hoy **para VIIRS**,
y extenderla a MODIS sería extrapolar. El n bajo tiene causa conocida — la cobertura
de ground truth MIROVA-MODIS es chica (82 noches-ALERTA en toda la ventana).

## Qué implicaría corregirlo

El brazo fiel **no es sólo regridear**. Coppola 2012 §3.2 pone el **bow-tie** como
paso (i): en los bordes del swath VIIRS, píxeles consecutivos se solapan, y
remuestrear sin de-solapar primero **duplicaría píxeles calientes** e inflaría la
magnitud en la dirección contraria al error que se quiere corregir.

Es decir: **bow-tie + regrid**, en ese orden, o nada. Es un trabajo de fondo sobre el
núcleo del pipeline, no un flag — y por eso esta sesión lo deja **medido y
diagnosticado**, no implementado a medias.

## Relación con D17 y con el gap de magnitud

S128 concluyó que **D17 y el gap de magnitud son el mismo problema**. Esta medición
lo sostiene con el control que a esa conclusión le faltaba: el sub-reporte global
(D5 = 0,73) **no es parejo** — es 0,74 cerca del nadir y 0,25 en oblicuo. Una
mediana global sobre todos los ángulos promedia dos regímenes y esconde que el
mecanismo es geométrico.

Es el mismo error de denominador que **A90** describe, ahora sobre el eje angular en
vez del temporal.
