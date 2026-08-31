# S129 · El método MIR no ve lo difuso — y el canon lo dice

> Salió de leer Mannini et al. 2019 (GRL), el último paper canon-adyacente que quedaba
> sin tocar. Informe: `docs/s129/PAPERS_MANNINI2019_FUMAROLAS.md`.

## Lo que dice el canon sobre su propio método

Campus/Laiolo et al. 2024 —*Thermal unrest at La Fossa (Vulcano Island)*, Bull. Volcanol.
86:25, que es **el mismo paper que `pipeline/process_viirs.py:74` cita para nuestro
`WOOSTER_COEFF = 18.0`**— escribe en la página 4:

> *«for temperatures between 600 and 1500 K, the MIR method estimates the radiant power
> with an error of ~30% … **Hydrothermal systems are commonly characterised by
> temperatures below this range.** However, Coppola et al. (2022) proved that even in a
> fumarolic field such as that of Vulcano, featuring at least a component exceeding or
> approximating 600 K …, the method works as a proxy of the flux radiated **exclusively
> by this hottest component**»*

O sea: el método MIR **no mide el calor de un campo fumarólico**. Mide la esquirla más
caliente que haya adentro, y sólo funciona si esa esquirla existe y llega a ~600 K.

## Cuánto es la esquirla

Mannini et al. 2019 lo cuantifica en Vulcano combinando medición en terreno con ASTER a
90 m: **el 93 ± 2 % del calor sale de la zona difusa** —unos 64.000 m² a +4 K sobre el
fondo, 9 MW— y sólo el **7 %** de las bocas discretas (~100 m², 0,65 MW).

**El método MIR ve ese 7 %.**

## Lo que reencuadra

**Nuestra «paridad» en Lastarria no es paridad con el volcán.** Lastarria es el campo
fumarólico Lazufre. Nosotros medimos ~0,5-0,8 del VRP de MIROVA, y los dos estamos
midiendo la misma fracción chica del calor real. Que coincidamos con ellos no significa
que el número represente al volcán — significa que compartimos la misma limitación
física. Vale la pena decirlo así en el dashboard, porque un operador razonablemente lee
«VRP bajo» como «poca energía».

**Y toca la decisión del piso VRP, que está abierta.** El agente estimó, con Planck y
las áreas de Mannini, que el campo entero de Vulcano —14º del mundo en densidad de
flujo— entraría a nuestro pipeline como **~0,07 MW en VIIRS375** y **~0,10 MW en
MODIS**: exactamente el rango 0,04-0,06 que venimos llamando «artefacto topográfico».

⚠️ **Ese número es un cálculo propio, no una medición de ningún paper.** Es un modelo
de mezcla de radiancia sobre áreas publicadas, y hereda esa incertidumbre. Pero el orden
de magnitud alcanza para el punto: **un piso de 0,1 MW borraría un campo fumarólico
real**. Refuerza la recomendación de S126 —quitar el piso— y ahora por física, no sólo
por nuestros datos.

Concuerda además con Coppola 2014, que evaluó un corte de 2 MW, midió que bajaba el
acierto de ~79 % a menos de 59 %, y lo rechazó: *«we preferred to keep some false alerts
than missing several real hot-spots»*.

## Un precedente para el frente del fondo

Mannini define el fondo como el **vecino no anómalo más frío** (Lee & Tag 1990). Nuestro
kernel promedia los 8 vecinos **incluidos los anómalos**. Es un tercer testimonio
independiente contra el fondo autorreferente que S126 identificó, y viene de fuera del
canon MIROVA, que es lo que le da valor.

## Dos advertencias del propio informe

- Mannini **no opina** sobre el método MIR: no menciona MIR, Wooster, MODIS/VIIRS, VRP
  ni sub-píxel una sola vez. Quien lo dice es Campus 2024. No atribuirle a Mannini una
  conclusión que es de otro paper.
- El PDF **no trae ecuaciones** (están en un *Supporting Information* que no tenemos), y
  su cifra de densidad difusa «0,55-1,57 kW/m²» no cuadra con los otros números del
  mismo paper. **No usarla.**

## Pendiente de trazabilidad

`pipeline/process_viirs.py:70` atribuye el `k = 18,0` a *«Laiolo et al. 2024»*. La
higiene del corpus de S128 determinó que el autor correcto es **Campus et al. 2024** y
corrigió `BIBLIOGRAPHY_SYNTHESIS.md`, pero **el comentario del código sigue con la
atribución vieja**. Es un comentario, no comportamiento — y `process_viirs.py` está bajo
A45, así que queda anotado y no tocado.
