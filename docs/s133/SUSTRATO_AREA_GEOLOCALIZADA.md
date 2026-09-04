# S133 · El A/B del área no se puede correr todavía: el brazo «área» es el control

**Hallazgo: `ENABLE_GEOLOCATED_PIXEL_AREA` no tiene ningún consumidor en producción.**
El flag se define y se lee en `pipeline/profile.py:576`, y ahí termina. Ninguna función
del pipeline lo consulta, y `pixel_areas_from_geolocation` (`pipeline/scan_geometry.py:248`)
no tiene una sola llamada fuera de sus tests. Si el A/B de 3 brazos de
[`AB_AREA_GEOLOCALIZADA.md`](../s132/AB_AREA_GEOLOCALIZADA.md) se lanzara hoy, el brazo
«área» produciría exactamente lo mismo que el control, y el reproceso se gastaría en medir
la diferencia entre un archivo y su copia.

Fuente de todos los números: `experiments/_s133/sustrato_area_geolocalizada.json`
(regla S91). El sustrato de código se responde por AST, no por `grep` de texto, porque el
nombre en el punto de uso no tiene por qué ser el de la definición (A89).

## Por qué no se vio antes

S132 dejó la pieza «construida y probada», y lo estaba: la función existe, reproduce la
razón 4,38× del ATBD y tiene siete tests. Lo que no existe es el cable entre la pieza y el
procesador. La prueba verde de la función y la prueba verde de que el flag arranca apagado
conviven perfectamente con que nadie llame a ninguna de las dos.

Es la misma forma del A/B de fondos de S130, donde la pregunta previa a «¿mejora algo?»
resultó ser «¿llega a ejecutarse?». Y es la forma de A89 por el lado incómodo: el cero de
una búsqueda se lee como ausencia, pero acá el cero **era** ausencia y no lo verificó nadie
porque la pieza tenía tests.

## Sustrato de dato: sobra, y es el bin más poblado

Sobre los records persistidos que llevan `sensor_zenith_deg`:

| sensor | n | cenital mediano | fracción ≥ 50° | n en bin 50°+ |
|---|---|---|---|---|
| VIIRS375 | 11.600 | 48,7° | 48,2 % | 5.595 |
| VIIRS750 | 11.514 | 48,6° | 48,0 % | 5.531 |
| MODIS | 5.911 | 44,2° | 40,1 % | 2.372 |

El bin de 50°+ es el más poblado de los cinco en los tres sensores. Coincide con lo que
S131 midió sobre pares contra MIROVA (1.147 de 2.773), con **otro denominador**: aquellos
eran pares volcán×noche contra MIROVA, estos son records persistidos (A90).

**Advertencia de denominador.** De los 60.962 records del corpus, 31.937 **no** tienen el
cenital persistido, así que la tabla corre sobre los 29.025 que sí. Los que faltan no están
repartidos al azar: son el backfill histórico de 2025 (cobertura ~10 % por mes hasta
2026-01) y la ventana corta de abril-2026 de los 34 volcanes fuera del cron. Desde 2026-02
la cobertura es del 100 %. Como el A/B reprocesa y genera records nuevos, el hueco no lo
afecta; pero los porcentajes de arriba describen 2026 en los Tier A, no el corpus entero.
La serie mensual completa está en el JSON.

## Dónde va el cable

Dos sitios, uno por banda, y en los dos la geolocalización ya está en una variable local
inmediatamente antes de la llamada:

| archivo | línea de la llamada | lat/lon disponibles en |
|---|---|---|
| `pipeline/process_viirs.py` | 710 (`viirs_pixel_areas`) | 705-706 |
| `pipeline/process_viirs_mod.py` | 453 (`viirs_pixel_areas`) | 451 |

**Una mina que hay que esquivar al cablear.** El tercer modo no puede pasar por la rama
de factor lineal de `viirs_pixel_areas`: esa rama topa la corrección en 2,0× porque su
docstring leyó como multiplicador de área el «approximately 2» que el ATBD da **por eje**
(S131 §5). Un tope de 2,0× estrangularía justamente el 4,38× que se quiere medir. Hoy la
rama está muerta (`nadir_fixed=True`), y debe seguir estándolo: el modo geolocalizado tiene
que ser una tercera opción explícita, no un parámetro que caiga dentro del modelo lineal.

## Lo que corresponde hacer, en orden

1. **Cablear** el flag en los dos sitios, con test que falle antes y pase después. Toca
   `pipeline/process_viirs*.py` → tag defensivo y confirmación explícita de Nicolás (A45).
2. Recién entonces **correr el A/B de 3 brazos** con el criterio ya pre-registrado en el
   doc de S132, que no se toca.
3. El flip sigue siendo decisión de Nicolás.

El criterio pre-registrado de S132 no se modifica por este hallazgo: sigue siendo válido,
sólo que hasta ahora no había nada que juzgar.

## Una corrección al criterio, que no lo cambia

El cuarto punto del criterio pide «0 noches de MIROVA perdidas» razonando por A67 que el
área multiplica dentro de la integral del Test 1. La auditoría de S131 ya había dejado
anotado que **eso no tiene respaldo en el código de hoy**: `test1_integrated.py` integra
`Σ max(0, L − L_bg)` sin área. O sea, la predicción es que el área mueva sólo magnitud.
El criterio se conserva igual —medir FN a nivel record es barato y protege contra algún
gate en MW que quede aguas abajo—, pero su resultado esperado es 0 por construcción, y si
diera distinto de 0 lo que hay que revisar primero es por dónde entró el área a la
detección, no la magnitud.
