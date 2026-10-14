# Estudio C (tarea 1.13 del loop): alertas diurnas de MIROVA que la réplica no mira

Fecha: 2026-10-14. Referencia: `scripts/referencia_mirova_unificada.cargar_referencia_unificada()` (44.469 filas,
2026-01-10 19:06 a 2026-10-14 13:05 UTC). Regla día/noche: la del pipeline (`pipeline.store._solar_elevation` +
`_reject_daytime`, perfil `mirova_equivalent`, `ENABLE_DAYTIME_MODIS = False`). Alerta protegida: lectura A
(`scripts/clase_mirova.alerta_protegida`). Todo número sale de un `*_salida.txt` de esta carpeta.

## 1. El fenómeno

De día el canal de infrarrojo medio (3,7 a 4 µm) suma a la emisión térmica la luz solar reflejada. Una nube,
un salar o una ladera clara pueden levantar unos pocos píxeles sin que haya nada caliente debajo, y el suelo
del desierto se calienta al sol. Por eso la réplica descarta toda pasada con el Sol sobre el horizonte. MIROVA,
en cambio, procesa el día con umbrales más altos y publica lo que pasa esos umbrales.

## 2. La población (`poblacion.py`)

Controles: la regla del pipeline acierta 6 de 6 casos sintéticos; el conteo de D27 (37 alertas de tabla entre
13 y 21 UTC, 19 de 1 MW o más) se reproduce exacto sobre `latest_consolidado.csv` del commit `1f73c2006`; la
versión de hoy da 38 y 20 por una fila nueva (Nevados de Chillán MODIS 2026-10-14 13:05, 6,98 MW). La regla de
elevación y el corte horario 13 a 21 UTC coinciden en las 2.658 filas de alerta (ninguna a menos de 3 grados
del horizonte).

- **135 filas de alerta diurnas** (de 2.658); **97 protegidas**, que son **94 pasadas** (CONS y OCR juntas).
- D27 contaba sólo la tabla (19). Con el OCR son cinco veces más: de las 97 filas protegidas, 78 son del OCR.
  Sólo 19 de las 94 pasadas protegidas diurnas tienen la alerta en la tabla.
- Sensor: VIIRS 375 domina (85 filas protegidas); MODIS 6, VIIRS 750 6.
- Volcán (filas protegidas): Láscar 39, Lastarria 31, Nevados de Chillán 10, Isluga 7, Villarrica 5,
  Tupungatito 2, Chaitén, Planchón-Peteroa y Puyehue-Cordón Caulle 1 cada uno.
- Hora: 17 a 19 UTC (13 a 15 h de Chile) casi todas; elevación solar de 30 a 60 grados en 89 de 97.
- Magnitud: 90 de 97 entre 1 y 10 MW; 6 entre 10 y 100; una de 760,6 MW (Láscar, 2026-06-15, el caso de A76).
- Frente a lo que hoy cuentan los evaluadores: **346 pasadas protegidas nocturnas contra 94 diurnas**
  (las diurnas son el 21 % del total de protegidas bajo la lectura A).

Contexto que pesa: la tabla de MIROVA lista **22.410 filas diurnas** (6.192 MODIS, 7.928 VIIRS 375 y 8.290
VIIRS 750 en CONS), casi todas RUTINA. En VIIRS 375 la tabla alerta en 29 de 7.928 pasadas diurnas (0,4 %)
contra 1.236 de 7.183 nocturnas (17 %).

## 3. ¿Calor o Sol?

Cuatro instrumentos, cada uno con un control que podía fallar.

**a) Continuidad con las noches vecinas** (`real_o_reflejo.py`). Un foco real no depende de la hora. Para
cada pasada protegida se mira la alerta nocturna mayor del mismo volcán y sensor a ±72 h. Umbral sin
inventar (A115): T = 3,16, el percentil 95 de esa misma razón entre alertas nocturnas protegidas y sus
vecinas nocturnas. Resultado:

| | consistente | desproporcionada (> T) | aislada | sospecha |
|---|---|---|---|---|
| nocturnas (N1, no pueden ser reflejo) | 325 | 18 | 3 | 6,1 % |
| diurnas | 54 | 39 | 1 | **42,6 %** |

Control positivo: las 8 diurnas de Nevados de Chillán en erupción (desde el 2026-09-28) salen consistentes.
Control negativo: la de 760,6 MW sale desproporcionada. Con ventana de ±36 h: 34,0 % contra 8,4 %. La razón
diurna mediana es 2,21 (nocturna 0,84). Lastarria es el caso extremo: VRP diurno mediano 2,87 MW contra
0,09 MW de noche.

**b) Dónde caen las detecciones de MIROVA de día** (`distancia_dia_noche.py`, sólo tabla, porque la
distancia del OCR puede venir de otra pasada). Fracción de filas con VRP > 0 a 3 km o menos, contra el azar
(1,1 % para puntos uniformes en la grilla de 51 × 51 km). Control nocturno: Láscar, Villarrica, Chaitén,
Isluga y Nevados de Chillán dan 44 a 89 veces el azar de noche (pasa). De día, todos los sensores juntos:
VIIRS 375 4,6 veces el azar (contra 48,3 de noche), mediana 16,9 km. **Lastarria: 0 de 176 detecciones
diurnas cerca del cráter** (mediana 10,7 km; de noche 73 %). De día sólo Láscar (12,9), Villarrica (14,0) y
Nevados de Chillán (11,5) se amontonan en el cráter, y aun así muy por debajo de la noche.

**c) La pasada vecina en la tabla** (`pasada_vecina_tabla.py`). De noche, la pasada de la tabla más cercana
(±60 min) repite la alerta protegida en 56 %; de día en 4,8 %. **Este instrumento no sirve para separar
reflejo**: falla su control positivo, porque en Nevados de Chillán en erupción la vecina diurna tampoco
repite (1 alerta y 9 RUTINA). Lo que mide es que MIROVA de día detecta de forma errática con sus umbrales
altos. Lo único que deja es una firma de Lastarria: su vecina diurna es FALSO_POSITIVO (calor fuera del radio)
en 25 de 35 casos, contra 18 de 288 de noche.

**d) La imagen** (`tif_diurno.py`; sólo lectura local, sin pull). Contraste del cráter en el GeoTIFF I04 de
MIROVA contra 30 puntos al azar del mismo ráster (control que se cancela: mediana -0,018 en 646 rásters).
Control positivo: Láscar de noche con alerta da mediana 4,63 y 65 % sobre 3, contra -0,47 en RUTINA. De día
el cráter no se destaca: Láscar 9 % sobre 3, Lastarria 0 %, Isluga 3 %. Límite: los TIF diurnos locales son
casi todos del 9 al 19 de mayo, y ninguna alerta OCR diurna tiene su propia imagen (el TIF más cercano está
18 min después y es otra pasada; en 6 de 8 esa pasada figura en la tabla como FALSO_POSITIVO y en 2 como
RUTINA).

**Clasificación combinada** (`peso_criterio.py`): de las 94 pasadas protegidas diurnas,
- **39 real probable** (magnitud consistente y volcán con detección diurna amontonada en el cráter, corte de
  10 veces el azar): Láscar 28, Nevados de Chillán 8, Villarrica 3;
- **40 reflejo o Sol probable** (desproporcionada o aislada): Lastarria 19, Láscar 10, Isluga 5,
  Tupungatito 2, y uno en Chaitén, Planchón-Peteroa, Villarrica y Nevados de Chillán;
- **15 indeterminadas** (consistentes en magnitud, pero de día MIROVA nunca detecta en ese cráter): Lastarria 12,
  Isluga 2, Puyehue-Cordón Caulle 1.

El 39 es frágil: con un corte de 20 veces el azar ningún volcán califica y las 39 pasan a indeterminadas
(con 5 veces no cambia nada). El rango honesto de reales es 0 a 54, con 39 como lectura central; el de reflejo,
40 a 55.

## 4. Qué dicen los papers (páginas renderizadas a 200 dpi, `renderizar_paginas.py`)

- **Coppola et al. 2016a** (`sp426.5.pdf`), PDF p. 7, Tabla 1: parámetros distintos de noche y de día
  (K1 = -0,6, C1 = 0,02, C2 = 15 de día); la columna derecha dice que se separan porque «solar effects
  amplify the variability» del NTI y el ETI. PDF p. 16 a 17, sección «False alerts»: las falsas alertas
  ocurren principalmente en imágenes diurnas, en bordes de agua y nubes dispersas, y «typically radiate less
  than 5 MW». 75 de nuestras 94 diurnas protegidas están bajo 5 MW.
- **Campus et al. 2022** (*Sensors* 22:1713), p. 16, §5, segundo párrafo: el MIROVA VIIRS se evaluó con
  todas las imágenes diurnas y nocturnas de 2021. p. 17, Tabla 4 y párrafo «Nighttime vs daytime data»: la
  frecuencia de alertas VIIRS baja de 51 % de noche a 20 % de día por los umbrales diurnos más altos,
  fijados contra el calentamiento y la reflexión solar. **MIROVA sí procesa VIIRS de día.**
- **Coppola et al. 2026** (*Scientific Data*), PDF p. 7 a 8, «Data aggregation» y Tabla 1: el conjunto
  curado aplica un umbral mínimo de VRP **diurno de 5,0 × 10⁷ W (50 MW) en los tres sensores**, contra
  10⁴ a 5 × 10⁶ W de noche. Ese conjunto no es el NRT (A105), pero dice que el propio grupo descarta toda
  detección diurna bajo 50 MW. De nuestras 94, sólo la de 760,6 MW la pasa, y es el artefacto de A76.
- **Tesis de Massimetti**: en las páginas que ubica la capa de texto, el día aparece sólo para SWIR de
  Sentinel 2 y Landsat 8 (PDF idx 38, p. 31; idx 138). Sobre si MIROVA procesa VIIRS de día: SIN LOCALIZAR.
- **Coppola 2025** (capítulo Springer), p. 336, Tabla 2: umbral NTI -0,8 de noche y -0,6 de día, citado de
  Wright et al. 2002, para MODIS. No dice nada propio de VIIRS.

## 5. Cuánto pesan en el criterio

| sensor | tramo A119 | protegidas nocturnas (cuentan hoy) | diurnas | real | reflejo | indet. | diurnas en la tabla |
|---|---|---|---|---|---|---|---|
| MODIS | ene-feb | 9 | 0 | 0 | 0 | 0 | 0 |
| MODIS | mar-12jun | 39 | 3 | 0 | 3 | 0 | 2 |
| MODIS | 13jun-oct | 7 | 1 | 1 | 0 | 0 | 0 |
| VIIRS 375 | ene-feb | 12 | 4 | 4 | 0 | 0 | 4 |
| VIIRS 375 | mar-12jun | 98 | 54 | 22 | 20 | 12 | 5 |
| VIIRS 375 | 13jun-oct | 38 | 26 | 10 | 13 | 3 | 6 |
| VIIRS 750 | ene-feb | 19 | 0 | 0 | 0 | 0 | 0 |
| VIIRS 750 | mar-12jun | 95 | 0 | 0 | 0 | 0 | 0 |
| VIIRS 750 | 13jun-oct | 29 | 6 | 2 | 4 | 0 | 2 |
| **total** | | **346** | **94** | **39** | **40** | **15** | **19** |

Sin enero y febrero (A119): 306 nocturnas contra 90 diurnas, 35 reales. En marzo a 12 de junio, que es donde
sólo la tabla decide, apenas 7 pasadas diurnas protegidas están en la tabla.

En la unidad del operador (A94) la pérdida es mucho menor: de las 39 reales, **35 tienen una alerta nocturna
protegida de MIROVA del mismo volcán a 24 h o menos**, o sea el evento la réplica sí lo puede ver de noche.
Lo que se pierde es la pasada, no el episodio. Las 8 de Nevados de Chillán en erupción caen en ese caso.

## 6. Recomendación

1. **No abrir el día en la réplica para cerrar esta brecha.** Lo que se ganaría son 35 a 39 pasadas reales en
   volcanes cuyo episodio ya se ve de noche, al costo de unas 40 a 55 publicaciones que son Sol o reflejo,
   justo la clase que Coppola 2016a describe y que el conjunto curado de Coppola 2026 descarta entero. Además
   el pipeline no tiene día para VIIRS, que trae 91 de las 97 filas protegidas diurnas: sería un detector nuevo con los
   umbrales de la Tabla 1 diurna, y eso pide su propio A/B.
2. **Decisión para Nicolás**: declarar en el criterio de victoria que las alertas diurnas quedan fuera de
   «ninguna protegida se puede perder», con este conteo como respaldo, o contarlas como pérdida conocida
   aparte. Hoy no las cuenta nadie y no está escrito.
3. **Propagar (A113), sin tocar el pipeline en este PR**: el docstring de `pipeline/store.py:_reject_daytime`
   dice que VIIRS no tiene fuente MIROVA diurna; es falso (Campus 2022 p. 16 a 17, y 7.928 pasadas VIIRS 375
   diurnas en la tabla). D27 dice que MIROVA publica detecciones diurnas «de MODIS»; son sobre todo de VIIRS 375.

## 7. Lo que no se resolvió

- Ninguna alerta OCR diurna tiene su propia imagen: el clasificador de real o reflejo es indirecto (magnitud
  y geografía de las detecciones), no un examen píxel a píxel. Bajar las imágenes por la API de Mirova-v1
  (`imagenes_satelitales/`) cerraría eso, y no se hizo por la regla de no traer datos.
- La clase «real probable» depende de un corte por volcán que con 20 veces el azar deja cero reales.
- Láscar: la magnitud dice real en 28 casos, pero la imagen diurna de mayo casi nunca muestra el cráter
  (9 %). No se sabe si el VRP OCR diurno de Láscar es el cráter o la suma de calor de toda la escena.
- Qué haría la réplica con estas pasadas si procesara el día: no medido (no se despachó nada).
