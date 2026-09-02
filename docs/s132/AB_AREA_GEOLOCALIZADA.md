# S132 · El A/B del área — decisión #5 de AUDIT_S131 §4

**Estado: la pieza que faltaba está construida y probada; el A/B no se corrió.** El flag
`ENABLE_GEOLOCATED_PIXEL_AREA` queda **apagado**. Lo que sigue es lo que hay que correr y
el criterio con el que hay que juzgarlo, escrito antes de correrlo.

## El fenómeno, en una línea

La energía radiante es una **radiancia** —energía por unidad de área— **multiplicada por el
área del píxel**. Un sensor de barrido que apunta de reojo al borde del swath cubre con el
mismo detector un pedazo de terreno mucho más grande que cuando mira hacia abajo. Si usamos
el área del nadir mientras el píxel real es el cuádruple, sub-reportamos la magnitud
exactamente en las pasadas oblicuas.

S131 lo midió: la razón contra MIROVA cae de **0,77 en el nadir a 0,45** en el bin de 50°+
sin corregir, y queda **plana entre 0,79 y 0,87** aplicando la ley de área del ATBD. Es
decir, **el área explica el gradiente cenital completo**. Lo que sobra después es un déficit
uniforme de ~0,82 que ya no es geometría: es el fondo (Eq. 6) y la suma/clúster, los frentes
R1/R2 que S125 dejó abiertos.

## Por qué medir el área en vez de modelarla

VIIRS no crece suave con el ángulo. Hace **agregación de bow-tie a bordo** (Wolfe et al.
2013): junta 3, 2 o 1 muestras del detector según la zona del swath, de modo que el área da
**saltos** en dos fronteras en lugar de seguir una curva. Todo modelo analítico se equivoca
en algún tramo:

| método | factor nadir → borde | comentario |
|---|---|---|
| sec³ de un barredor puro | ~25× | sobre-corrige groseramente (probado y descartado en su momento) |
| factor lineal del repo, tope 2,0 | **1,96×** | su propio docstring reconoce que sub-corrige |
| ATBD 423-ATBD-002 Tabla 2.2-1 (I4) | **4,38×** | 0,371×0,388 km → 0,80×0,789 km, o sea 0,144 → 0,631 km² |

El modelo vigente corrige **menos de la mitad** de lo que hay que corregir. La
geolocalización del granule, en cambio, no es un modelo: es dónde cayó cada píxel. La
distancia en el terreno entre centros vecinos **es** el tamaño del píxel, con los saltos de
agregación ya adentro y sin suponer nada de la órbita ni del sensor.

## Lo construido

`pipeline/scan_geometry.py::pixel_areas_from_geolocation(lat, lon)` — diferencias centradas
en el interior, hacia adelante/atrás en los bordes, producto de los dos pasos. Devuelve NaN
donde la geolocalización viene inválida, a propósito: es preferible un NaN visible a un área
plausible pero falsa, que se propagaría a la magnitud sin que nadie lo note.

Aproximación asumida, dicha explícitamente: el píxel se toma como un paralelogramo de lados
iguales a esas dos distancias. Es exacto para una grilla localmente regular y no modela el
corte real del footprint, que en el borde del swath es un trapecio curvo. Para escalar
energía radiada, ese error es mucho menor que el 4,38× que se está corrigiendo.

**Probado contra una autoridad externa, no contra sí mismo**: alimentada con los pasos del
ATBD, la función devuelve 0,144 km² en el nadir, 0,631 km² en el borde y una razón de 4,38×
(`tests/test_area_geolocalizada_s132.py::test_reproduce_la_razon_del_atbd_viirs`). También
se prueba que captura un salto de agregación sin suavizarlo, que es la razón entera de medir.

## Lo que falta correr, y con qué criterio

Tres brazos, cada uno con su `data_subdir` aislado (A47: nunca en paralelo sobre el mismo
directorio), reproc **real** en GH Actions:

1. **control** — como está hoy (área nadir fija).
2. **área** — `enable_geolocated_pixel_area: true`.
3. **área + corona** — lo anterior más el fondo de la Eq. 6, para atacar el déficit uniforme
   de 0,82 que el área no explica.

Criterio pre-registrado (de AUDIT_S131 §4, punto 5), **por pasada, nunca por noche** — es la
lección A90 del «f requerido 2,93 → 1,72»:

- el bin de 50°+ y el de nadir, ambos entre **0,9 y 1,1**;
- **≥ 6 de 8** volcanes en banda en VIIRS375;
- **0 noches de MIROVA perdidas** (A67: el área multiplica dentro de la integral del Test 1,
  así que puede apagar detecciones, no sólo cambiar magnitudes — hay que mirar FN a nivel
  record, no sólo la mediana);
- pares con razón > 2 en **≤ 10 %**.

**No extender a MODIS por extrapolación.** En VIIRS el bow-tie lo hace el sensor; en MODIS
el remuestreo es trabajo real y el gradiente no está probado — S131 lo midió sobre 50 pares
y un solo volcán.

Tag defensivo antes de tocar nada (A45), y el flip es decisión de Nicolás.
