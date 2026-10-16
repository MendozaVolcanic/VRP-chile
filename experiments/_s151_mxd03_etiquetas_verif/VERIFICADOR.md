# Verificador con contexto limpio: probe S151 tarea 1.17 (etiquetas MODIS con MxD03, PR #834)

Fecha: 2026-10-16. Leído desde `origin/main` (b9d65830c). Sólo lectura: no se despachó nada ni se editó el repo.
Scripts y salidas de esta verificación: `C:\Users\nmend\AppData\Local\Temp\claude\verif_117\`
(`analisis_pob.py`, `analisis_shift.py`, `geom.py`; corpus y CSV de referencia extraídos de `origin/main` en
`C:\Users\nmend\AppData\Local\Temp\claude\verif_117\data\`, `cons.csv`, `ocr.csv`).

## Veredicto global: SELLABLE CON ARREGLOS (y los arreglos 2 y 3 cambian el diseño, no son cosméticos)

El instrumento (los dos brazos sobre el mismo L1B) está bien construido. Lo que falla es **a quién mide y con qué
vara**: la muestra deja fuera justo las pasadas que deciden la regla de victoria de la réplica, y la banda de 3 km
se apoya en un corrimiento medido hasta 47° de cenit cuando un tercio de la población está a más de eso.

## Punto 1: ¿el brazo M usa MxD03 en todos los lugares donde la posición decide? CUMPLE

- `calculate_vrp` llama `read_modis_l1b(hdf_path)` como global del módulo (`pipeline/process_modis.py:504`), así que
  el `patch.object(pm, "read_modis_l1b", leer)` del probe (`probe_etiquetas.py:95`) sí intercepta. Toda la geometría
  posterior sale de `lat = data["lat"]`, `lon = data["lon"]` (l. 511-512): distancia al centro y al ancla
  (l. 517-523), caja ROI1, ROI de 50 km, anillo de fondo, máscara del p95 (l. 610), `exclude_zones` y
  `active_water_bodies` (l. 999), `anomaly_pixels` (l. 1089, 1399), cúmulo anclado al vent (l. 1116, 1406), vent
  path (l. 1234-1259) y núcleo (l. 1471). No encontré una segunda lectura de geolocalización ni un camino por índice
  que use la posición interpolada.
- `store.append_record` deriva `final_hotspot`, `distance_class` (incluida la degradación summit a far por
  `centroid_dist_km > inner`, `pipeline/store.py:514-519`) y `f5_core_vrp_mw` (l. 602) desde el record, o sea desde
  las posiciones del brazo M. El predicado del tablero recibe `anomaly_pixels` con lat/lon del brazo.
- El ancla (`get_detection_anchor`) es una coordenada de configuración, igual en los dos brazos: correcto.
- Argumentos de `calculate_vrp` y `append_record` coinciden con `scripts/run_pipeline.py:235-254` (y el test los
  compara por AST).
- Residuo menor, no decide: `observation_geometry` (l. 1569) busca el ángulo con la lat/lon del brazo M sobre la
  grilla de ángulos interpolada. Sólo persiste el cenit.
- `_scene_is_day` usa el centro del volcán, no la grilla: igual en los dos brazos.

## Punto 2: ¿la población puede sesgar el resultado? NO CUMPLE

**2a. La banda de 3 km es corta en un tercio de la población.** El modelo que #828 confirmó (el frame *s* recibe la
posición del frame 0,99778·s + 2) predice, con la geometría de MODIS a 705 km (`geom.py`), un corrimiento a lo largo
del barrido de 3,0 km a 45° de cenit, 4,8 km a 54° y 9,6 km a 65° del lado del frame 0 (del otro lado, hasta 4,8 km
a 65°). El modelo reproduce lo medido en #828 (frame 191: predice 3,0, #828 predijo 2,82 y midió 2,58; frame 240:
2,4 contra 2,24 y 2,21). Pero #828 midió sólo hasta 46,8° de cenit. En la población del probe (5.395 records MODIS
del tramo; `sensor_azimuth_deg` está en todos, así que el lado del barrido se puede deducir):

| | A | B | medio | control |
|---|---|---|---|---|
| records con corrimiento predicho que alcanza el límite (margen ≤ corrimiento + 0,5 km) | 293 | 1.656 | **498** | **26** |
| de ellos, publicados hoy | 128 | 2 | **18** | **9** |

1.820 de 5.377 records (34 %) tienen corrimiento predicho mayor que 3 km. La anotación «cota inferior» se va a
encender casi seguro, y entonces el número que el probe entrega es un piso, con 197 publicaciones (32 % de las 622)
en el estrato medio sin medir.

**2b. El evaluador declara CAMBIA POCO con la cota inferior encendida.** Probado con `evaluar_mxd03.evaluar`: 100 %
de los gránulos corridos 5 km da `CAMBIA POCO` y `cota_inferior: True`. El test
`test_la_banda_corta_marca_cota_inferior` verifica la marca pero no el veredicto.

**2c. El control no es control a cenit alto.** A más de 6 km del límite, el README atribuye todo cambio a «otra
detección»; a 55° a 65° del lado del frame 0 el corrimiento es de 5 a 10 km y puede cruzar el límite por
reubicación (26 records, 9 publicados, casi todos PCC). La atribución estaría mal.

**2d. El estrato B no contiene el caso que dice medir.** B tiene 2.585 records: 2.581 `far` sin publicar y sólo 4
`summit` publicados, que son los únicos donde el centroide puede apagar la publicación. Los 83 gránulos B de la
muestra son todos `far` con `pub 0`. Cada gránulo B pesa 25 a 52 records en el estimador, así que un cambio de
detección aislado se infla mucho y el caso real de B (4 records) no se mide.

**2e. La muestra no incluye ninguna alerta protegida de MIROVA.** Ver punto 3.

## Punto 3: ¿la vara sale del dato o de la decisión? NO CUMPLE

`docs/MISSION.md` §«Criterio de victoria de la réplica», regla 1: «En la réplica no se acepta ningún cambio que
pierda una alerta protegida»; regla 4: «Los umbrales de cada prueba salen de los datos de MIROVA, no se eligen». El
2 % y el 5 % son elección del agente (el README lo admite) y la dirección respecto de MIROVA queda fuera del
veredicto. Arreglar la posición es un cambio de producción en la réplica, así que la regla 1 es una compuerta, no un
dato a cruzar después.

Medido sobre `registro_vrp_consolidado.csv` y `registro_vrp_ocr.csv` de `origin/main` (lectura A: `ALERTA_TERMICA*`
con VRP ≥ 1 MW, MODIS, 2026-03-01 a 2026-10-12): **48 pasadas protegidas** (Láscar 40, Nevados de Chillán 6,
Villarrica 2); 45 tienen record nuestro. **Ninguna está en la muestra.** Por estrato: 15 en B (todas `far`), 29 en el
medio sin medir (8 `summit`), 0 en A. O sea que el probe, tal como está, no puede contestar la única pregunta que la
regla de victoria vuelve obligatoria, y las pasadas que la contestan están casi todas en Láscar, el volcán con 2
gránulos A.

Vara propuesta (sale de la decisión, A115): (i) **censo** de las 48 pasadas protegidas en los dos brazos; compuerta:
ninguna publicada por C y apagada por M; (ii) por debajo de 1 MW, el balance neto de M contra C en las dos
direcciones (alertas de MIROVA ganadas menos perdidas, contra publicaciones ganadas menos perdidas en negativos
limpios, regla 3, tramo A119 y regla de mínimas D-9), también en noches (A94); (iii) el 2 % y el 5 % pasan a
informativos o se justifican contra ese balance. Con la tabla de MIROVA el cruce es de pasada y el probe ya guarda
hora y sensor; falta que decida.

## Punto 4: prueba sintética, control negativo, tiempo y autenticación: CUMPLE EN PARTE

- **Sintética**: distingue presente de ausente de punta a punta (pipeline real, `append_record`, predicado con
  node). Limitaciones: el corrimiento es una traslación uniforme hacia el sur, no el defecto real (a lo largo del
  barrido, creciente con el ángulo); el caso AUSENTE es sintético; no ejercita relleno NaN de MxD03 dentro de
  `calculate_vrp`.
- **Control negativo real: no existe.** Falta un brazo C' que pase la lat/lon de `_interp_geo` por el mismo camino
  del parche (`latlon=(d["lat"], d["lon"])`), o M contra M, sobre gránulos reales: debe dar records idénticos. Cuesta
  una corrida más de `calculate_vrp` en uno o dos gránulos por volcán y descarta que el cast a float32, la copia o el
  NaN fabriquen diferencias.
- **Tiempo**: 30 a 50 s por gránulo es creíble (#828: 143 s para 7 pares con bajada, lectura y comparación; acá se
  suman dos `calculate_vrp`); 44 gránulos dan unos 37 min; corte a los 70 min más unos 4 min de instalación y el
  último gránulo quedan bajo 90. Pero **el JSON se escribe sólo al final** (`probe_etiquetas.py:272`): si el job
  muere por timeout o por una búsqueda colgada, se pierde el volcán entero, y el evaluador **no lo marca
  INCOMPLETO** (probado: 1 de 11 volcanes da `CAMBIA POCO`). La subida no falla porque `prueba_sintetica_*.txt`
  existe.
- **Autenticación**: sólo `EARTHDATA_TOKEN`, con candado de vacío en el workflow y en el script; `pipeline.fetch.auth`
  prefiere el token. CUMPLE.

## Arreglos exigidos antes del sello

1. **Evaluador**: (a) `CAMBIA POCO` prohibido si `cota_inferior` está encendida (sale INDETERMINADO o «piso»);
   (b) INCOMPLETO si falta cualquiera de los volcanes pedidos; (c) informar neto (1->0 menos 0->1) aparte del bruto y
   separar «misma detección, otra etiqueta» de «otra detección». Test que fije cada caso.
2. **Población por alcance predicho, no por banda fija**: banda por record = corrimiento predicho por el modelo de
   #828 (cenit, acimut y satélite, ya persistidos) más 1 km de traza y terreno; control sólo donde el margen supera
   esa banda en 2 km o más; muestrear también lo que hoy cae en «medio» y es alcanzable (498 records, 18
   publicados). B se parte: los 4 `summit` publicados se miden todos.
3. **Censo de las 48 pasadas MODIS protegidas** del tramo en los dos brazos, con la compuerta de la regla 1 de
   `docs/MISSION.md` pre-registrada, y el balance de la regla 2 como vara principal. Láscar necesita más presupuesto
   (partir en dos jobs o subir timeout a unos 150 min con corte a 120).
4. **Control negativo real** (brazo C' o M contra M) en al menos un gránulo por volcán, con igualdad exacta exigida.
5. **Escritura incremental** del JSON por gránulo.

## Lo que no verifiqué

- Que MIROVA use MxD03 (o qué geolocalización usa): SP426.5 p. 3 habla de «pixel(s) geolocation» sin nombrar el
  producto. SIN VERIFICAR.
- La regla de lado del barrido (Aqua de noche: frame 0 si acimut > 0; Terra: si acimut < 0) sale de los 7 gránulos
  de #828; los conteos del punto 2 son estimación de alcance, no medición.
- El cruce de las 48 protegidas con nuestros records es por volcán y hora (± 10 min), sin mirar distancia.
