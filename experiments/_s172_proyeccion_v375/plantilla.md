# Proyeccion de la fecha de parada de la sombra V375-E

Ruta: D:/vrp-trabajo/temporales/s172_proyeccion_v375/INFORME.md (solo lectura sobre el repo; no se reproceso nada, no se corrio el lector).

## Respuesta corta

| Escenario | Noche de parada | Que lo define |
|---|---|---|
| Optimista | **2026-12-02** | las 30 noches desde el 2026-11-03 tienen dato; las 40 alertas se juntan mucho antes |
| Central | **2026-12-02** (borde 2026-12-03) | con la tasa de huecos observada (1 noche de 56; 1 de 152 desde junio) la mediana cae en el 2 dic |
| Pesimista | **2026-12-09** (p95 si se pierde el 10 % de las noches de la via; 2026-12-15 si fuera el 20 %) | huecos de dato en la sombra, no falta de alertas |

La parada la manda el **conteo de noches**, no el de alertas. Con el ritmo de septiembre y octubre las 40 alertas se juntan en una mediana de 10 noches (13 sin Chillan), hacia el 13 al 16 de noviembre; las 30 noches con dato no se cumplen hasta el 2 de diciembre. La lectura que decide solo se puede hacer cuando la referencia de MIROVA llegue a 2 dias despues de la noche de parada (control S9, `REZAGO_DIAS = 2`): **no antes del 4 de diciembre** en el caso central.

## Como cuenta el lector sellado (leido, no supuesto)

Fuente: `git show s170-v375e-lector:experiments/_s168/v375e_sombra/leer_sombra_v375e.py` (copia en lector.py de esta carpeta).
- `PARADA_NOCHES, PARADA_ALERTAS = 30, 40`; `DESDE_P = "2026-11-03"`; `SENSOR_SNPP = "VIIRS_SNPP"` (las pasadas de Suomi NPP se descartan antes de clasificar).
- `noche_parada(pob, con_dato)`: recorre las noches en orden; una noche cuenta si tiene al menos una pasada de la poblacion `pob` que ademas tenga record de la via (`con_dato`: clave (volcan, sensor, hora) presente en los records de `data/sombra_codigo_mirova` con `via_codigo_mirova == True`). Suma por noche las pasadas de clase `pos_prot` o `pos_bajo`. Para en la **primera noche** con noches >= 30 y alertas >= 40 acumuladas.
- `pob` sale de `banco_paridad` (VIIRS 375, 11 Tier A, records de K): `pos` (la referencia trae una ALERTA a +-120 s) se parte en `pos_prot` si alguna alerta es protegida (`clase_mirova.alerta_protegida`) y `pos_bajo` si no. Referencia indexada con `regla_minimas="SN"` (D-9: las de 0,05 MW o menos no cuentan como alerta). Una noche sin ninguna pasada etiquetada `pos`, `neg_limpio` o `far_ref` no entra a `pob`, aunque K tenga records.
- La noche es la fecha UTC de la pasada.

## Como medi (reproducible)

- Records de K: `origin/main` 14fb62030a186fda02ce2ba172866cf01408eeb9 (2026-11-01 23:34 UTC), `data/mirova_equivalent/*.json` de los 11 Tier A, VIIRS 375 de NOAA-20 y NOAA-21. Las pasadas de Suomi NPP se excluyeron (889 entre 2026-09-05 y 2026-11-01).
- Referencia: Mirova-v1 remoto fijado a sha: consolidado `be83ae16494459d56c09391fa96177a7f620ce28` (46.247 filas, hasta 2026-11-01 22:05 UTC) y OCR `c5731c4541735fba6c7fd0128a07e67c6a234ddc` (1.214 filas, hasta 2026-11-01 06:36 UTC); sin capas locales (`respaldo_path=None`, `historico_path=None`), como hace el lector.
- Etiquetado con las funciones de origin/main (`banco_paridad.indexar_referencia`, `cargar_nuestros`, `etiquetar`) y clase con `poblacion` importada del lector sellado; predicado del tablero con node.
- Ventana: **56 noches, 2026-09-05 a 2026-10-30** (8 semanas de 7 noches). Quedan fuera el 31 oct y el 1 nov porque la referencia aun no los completa. En la corrida 2026-09-05 a 2026-11-01 la poblacion fue de 1.306 pasadas (688 NOAA-20, 618 NOAA-21); dentro de las 56 noches son 1.263 (656 y 607).
- Scripts y salidas en la carpeta: medir.py, analizar.py, simular.py, pob_*.json, series.json, serie_diaria.csv, sim.json.
- Cautela A119: entre septiembre y octubre la ventana pisa los hitos del 2026-10-09 y 10-10 de la referencia (arreglo del OCR de Suomi NPP y V31.1). Las alertas que vienen de la tabla CONS son 234 de las 244 (96 %), asi que el resultado no depende del OCR.

## 1. Alertas que deciden por noche (NOAA-20 + NOAA-21, VIIRS 375, 11 Tier A)

Numerador: pasadas `pos_prot` + `pos_bajo`. Denominador: 56 noches UTC (2026-09-05 a 2026-10-30). Total 244, de las cuales **42 protegidas y 202 bajas**; 132 son de NOAA-20 y 112 de NOAA-21.

### Con Chillan

{TABLA_TODAS}

Por noche (56): media 4,36; mediana 4; p10 2; p90 7; minimo 0; maximo 11. Ventanas de 30 noches consecutivas dentro de las 56 (27 ventanas): suma minima 111, mediana 118, maxima 139. Noches hasta juntar 40 alertas, desde cada noche de inicio que lo logra dentro de lo observado (50 de 56 inicios): minimo 6, mediana 10, maximo 14.

### Sin Nevados de Chillan

{TABLA_SINCH}

Por noche (56): media 3,50; mediana 3; p10 1; p90 6,5; maximo 10. Ventanas de 30 noches (27): suma minima 81, mediana 87, maxima 110. Noches hasta 40 alertas (45 de 56 inicios): minimo 6, mediana 13, maximo 17.

Chillan aporta **48 de las 244** alertas (19,7 %): 5 de las 105 de septiembre (del 5 al 30) y 43 de las 139 de octubre (del 1 al 30). Por volcan, alertas que deciden en la ventana: Isluga 53, Nevados de Chillan 48, Puyehue-Cordon Caulle 44, Lascar 28, Tupungatito 26, Planchon-Peteroa 18, Chaiten 15, Lastarria 8, Villarrica 4, Llaima 0, Copahue 0.

Las alertas solo mandarian si el ritmo medio cayera bajo 40/30 = 1,33 por noche durante las 30 noches. La semana mas baja observada es 2,71 con Chillan y 2,43 sin Chillan (factor 1,8 por encima del umbral). Sin Chillan y con el resto a la mitad la mediana de parada sigue siendo el 2 dic; se corre (al 6 o 7 dic) recien con el ritmo sin Chillan multiplicado por 0,35, es decir 1,2 por noche, que es mas bajo que cualquier semana observada.

## 2. Noches con dato

Numerador: noches UTC con al menos una pasada en `pob`. Denominador: noches de la ventana.
- **55 de 56** noches (2026-09-05 a 2026-10-30). Falta el 2026-10-13: K tiene 11 records de NOAA-20 esa noche y ninguno con etiqueta que cuente (los 11 son `sin_info`); NOAA-21 no tiene record ese dia.
- Mismo criterio en 2026-06-01 a 2026-10-30: **151 de 152** noches (junio 30 de 30, julio 31 de 31, agosto 31 de 31, septiembre 30 de 30, octubre 29 de 30), la misma noche faltante.
- Pasadas de poblacion por noche (NOAA-20 + NOAA-21), 56 noches: mediana 23, minimo 0 (el 13 oct), maximo 30.
- Las caidas del NRT se curan con la ventana de 8 dias hacia atras: el token de Earthdata vencio el 2026-10-03 07:18 UTC y el NRT estuvo caido hasta el 2026-10-08 (REGISTRO_CREDENCIALES.md), y las 7 noches del 3 al 9 oct tienen dato hoy.

**SIN DATO:** la cobertura de la sombra misma. `data/sombra_codigo_mirova/` no existe en origin/main (la ventana arranca el 3 nov; el workflow `sombra-codigo-mirova.yml` corre una vez al dia a las 15:00 UTC). Uso la poblacion de K como proxy de las noches con dato de la via. El unico respaldo es la corrida de medicion run 40945613044 (77 records de la via de 77 posibles, Lascar, 8 dias, segun el comentario del workflow; no lo verifique).

## 3. Proyeccion

Modelo: la noche 1 es el 2026-11-03. Cada noche tiene dato con probabilidad 1 - g; las alertas por noche se remuestrean por bloques semanales de las 8 semanas medidas (7 noches consecutivas, para conservar la autocorrelacion y los saltos como las semanas 2 y 8); 20.000 simulaciones por celda; parada en la primera noche con 30 noches con dato y 40 alertas. Fecha de la noche de parada, con alertas al ritmo observado:

{TABLA_SIM}

A ritmo observado, con y sin Chillan salen fechas identicas porque las alertas nunca ligan; difieren solo si el ritmo cae bajo 1,33 por noche (sim.json trae tambien los escenarios con alertas a 0,5 y 0,35 del ritmo).

- **Optimista: 2 dic.** Treinta noches seguidas con dato.
- **Central: 2 dic**, con riesgo de un dia (3 dic) si falta una noche. La mediana es 2 dic en todos los g hasta 1,8 %.
- **Pesimista: 9 dic**, p95 si se pierde el 10 % de las noches de la via (3 noches esperadas; 15 veces la tasa observada en K desde junio). Con 20 % de noches perdidas el p95 es 15 dic. El 10 % es un juicio mio, no una medicion: la via corre una vez al dia en GitHub Actions y no hay historia propia.

## 4. Supuestos que mueven la fecha

1. **Cobertura de la sombra (el que mas mueve).** Cada noche sin pasada con record de la via corre la parada un dia. Es lo unico SIN DATO. Sugerencia: desde el 4 nov contar noches con record de la via contra las de K y mirar si la brecha pasa de 1 de 56.
2. **Token de Earthdata.** Vence el 2026-12-07 18:03 UTC (REGISTRO_CREDENCIALES.md; rotar antes del 2026-11-27). Si no se rota, el caso pesimista (5 a 9 dic) cruza el vencimiento. La caida de oct 3 a 8 no dejo huecos gracias al backfill de 8 dias, pero eso no cubre una caida de mas de 8 dias ni una justo antes de la lectura.
3. **Las alertas no mandan.** Hace falta caer bajo 1,33 por noche durante 30 noches; lo observado es 2,4 en la semana mas baja sin Chillan. Solo lo mueve un cambio de regimen grande, por ejemplo que Isluga y Puyehue-Cordon Caulle (97 de las 196 sin Chillan) dejen de alertar a la vez que Chillan se calma.
4. **Chillan.** No cambia la fecha de parada; cambia cuando se juntan las 40 (mediana de 13 noches sin Chillan en vez de 10).
5. **Un solo satelite.** Si cayera NOAA-20 o NOAA-21, las alertas de la ventana bajan a 112 o 132 de 244 (sin Chillan, a la proporcion correspondiente: unas 90 a 106 en 56 noches, 1,6 a 1,9 por noche), todavia sobre 1,33; las noches con dato no se pierden, porque cada nave cubre casi todos los volcanes. Es una aproximacion mia, no medida pasada a pasada.
6. **Estacion.** Noviembre y diciembre acortan la noche en latitudes altas; hoy ya hay 23 pasadas de poblacion por noche (casi cada volcan por sensor), asi que no creo que cambie, pero para noviembre y diciembre SIN DATO.
7. **Referencia.** El rezago S9 (2 dias) y el ritmo de actualizacion de Mirova-v1 mueven la fecha de **lectura**, no la de parada.
8. **Lo que no hace este informe.** No corre el lector (una sola lectura por ventana, §11.8) ni sus controles S0 a S10.

## Limites

- Las alertas se cuentan sobre la poblacion de K; el lector las cuenta sobre `pob` filtrada por `con_dato`. Si la via no tuviera record en una pasada con alerta, esa alerta no suma. Efecto no medible hoy (SIN DATO); como las alertas sobran unas 3 veces, no mueve la fecha.
- Las 8 semanas incluyen la erupcion de Chillan; fuera de ella solo hay la variante sin Chillan.
