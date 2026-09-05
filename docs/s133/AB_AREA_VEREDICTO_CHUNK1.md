# S133 · A/B del área, chunk 1: el área corrige el gradiente, pero se pasa de largo

**Ningún brazo pasa los cuatro criterios. El área geolocalizada no sobre-corrige un poco:
invierte el signo del sesgo.** El gradiente cenital que S131 midió existe y el área lo
explica — pero aplicarla completa nos lleva de sub-reportar en el borde del swath a
sobre-reportar.

Resultado sobre el **chunk 1** (2026-04-01 a 2026-05-31, 643 pares por pasada, 8 volcanes,
VIIRS375). Faltan los chunks 2 y 3; esto es un veredicto parcial y se declara como tal.
Números en `experiments/_s133/resultado_ab_area.json` (regla S91).

## El número que decide

Razón de nuestra magnitud contra la de MIROVA, por bin de ángulo cenital del sensor. Un 1,0
sería paridad perfecta; por debajo sub-reportamos, por encima sobre-reportamos.

| brazo | nadir (0-15°) | borde (50°+) | cola de razones > 2 |
|---|---:|---:|---:|
| **control** (área nadir fija, lo actual) | 0,879 | **0,619** | 4,2 % |
| **área geolocalizada** | 0,958 | **1,360** | 20,1 % |
| **área + corona** | 0,958 | **1,303** | 19,5 % |

Léase de izquierda a derecha en la fila del control: en el nadir estamos casi bien y en el
borde nos falta un 38 %. **Ese es el gradiente**, y es real. Ahora léase la fila del área: el
nadir mejora (0,879 → 0,958, dentro de la banda) pero el borde salta a 1,36. La corrección
no llegó tarde ni corta: llegó de más.

Los cuatro criterios, congelados en `docs/s132/AB_AREA_GEOLOCALIZADA.md`:

| | criterio | control | área | área+corona |
|---|---|---|---|---|
| C1 | ambos bins en 0,9-1,1 | ❌ | ❌ | ❌ |
| C2 | ≥ 6 de 8 volcanes en banda | ❌ 3/8 | ❌ 1/8 | ❌ 0/8 |
| C3 | 0 noches de MIROVA perdidas | — | ✅ 0 | ❌ 42 detecciones perdidas |
| C4 | cola de razones > 2 en ≤ 10 % | ✅ 4,2 % | ❌ 20,1 % | ❌ 19,5 % |

## Por qué esto no invalida el diagnóstico de S131, pero sí su remedio

S131 midió que el factor de crecimiento de área **requerido** para aplanar los bins era de
2 a 3× a 60° de cenital, y que el ATBD ofrece hasta 4,38× al borde del swath. La conclusión
fue: entra cómodo, el área alcanza. Y se dijo entonces que era *condición necesaria, no
prueba*.

El reproceso real muestra por qué esa distinción importaba. **Que el área disponible alcance
no significa que el área disponible sea la correcta.** Medida en la geolocalización, el
crecimiento resulta mayor que el requerido, y el resultado se pasa.

## La hipótesis de por qué se pasa, que NO está probada

La función mide el área como el producto de las distancias en el terreno entre centros de
píxeles vecinos. Eso es exacto para una grilla que embaldosa el terreno sin huecos ni
solapes. Pero el barrido de VIIRS **solapa** píxeles adelante y atrás al alejarse del nadir
—es el efecto bow-tie— y la agregación a bordo lo reduce sin eliminarlo. Donde hay solape,
la distancia entre centros es **mayor** que el terreno que el detector realmente integra, y
el área sale inflada justo donde más importa.

Si eso es lo que pasa, la ley correcta está **entre** las dos que probamos: la nadir-fija
sub-corrige, la geolocalizada sobre-corrige. Es una hipótesis con mecanismo y con dirección
predicha, o sea comprobable; no es una explicación cómoda inventada después del resultado.

## Lo que este A/B sí dejó firme

- **El gradiente existe y es grande**: 0,879 en el nadir contra 0,619 en el borde, con 111 y
  210 pares. No es ruido.
- **El área es el mecanismo correcto**: es lo único que se tocó y movió el borde de 0,62 a
  1,36. Ninguna otra explicación tiene esa palanca.
- **La corona empeora todo y además cuesta detecciones**: pierde 42 respecto del control, y
  es el único brazo que falla C3. Ese frente se puede cerrar acá.
- **No se pierde ninguna noche que MIROVA publicara** con el área sola (C3 = 0). El área
  cambia magnitud, no detección — como la auditoría de S131 anticipó contra lo que decía A67.

## Lo que corresponde hacer

**No adoptar ninguno de los tres brazos.** El flag `ENABLE_GEOLOCATED_PIXEL_AREA` queda
apagado y el de la corona también.

Correr los chunks 2 y 3 sigue teniendo sentido para confirmar que el patrón se sostiene en
otra estación del año, pero **no va a cambiar el veredicto**: una razón de 1,36 en el borde
no se arregla con más datos, se arregla con otra ley de área.

El frente que se abre, y que es más prometedor que el que se cierra: medir el **solape** del
barrido y descontarlo del área geolocalizada. Si la hipótesis es correcta, hay una corrección
intermedia que deja los dos bins en banda — que es exactamente lo que el criterio pide y lo
que ninguno de los tres brazos logró.
