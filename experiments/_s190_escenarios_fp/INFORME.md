# Escenarios de falso positivo: firma, cuánto pesan y la defensa más liviana (S190)

Pedido de la coordinadora S190 (2026-11-17), a raíz de la alerta de MacaCay del 2026-11-15 05:36 UTC (VIIRS 750 de
NOAA-20, 1 píxel, 4,1 MW, con el VIIRS 375 del mismo satélite en 0). El caso MacaCay y el escenario del píxel VIIRS
750 aislado los audita otra tarea (`D:\vrp-trabajo\temporales\s190_fp\`); acá sólo aparecen como contexto.

**Criterio.** La réplica (`mirova_equivalent`) publica lo que MIROVA publica, calla donde calla y da la misma
magnitud. Perder una alerta que MIROVA publica (FN) es lo más grave del glosario, así que cada defensa llega con su
costo en alertas protegidas (lectura A: alerta de MIROVA con 1 MW o más), contado por pasada y por noche. Tres niveles:
NADA (MIROVA también la publica; la réplica debe publicarla), MARCA (se publica con etiqueta de baja confianza, no se
calla nada) y FILTRO (sólo en el perfil `laboratorio`, medido contra OVDAS o SWIR, nunca en la réplica).

**Nada de esto cambia producción ni el tablero.** Las MARCAS y FILTROS son propuestas.

## Instrumento

- Script: `experiments/_s190_escenarios_fp/escenarios_fp.py`; salida completa: `experiments/_s190_escenarios_fp/salida.txt`.
  Corrido sobre un checkout de origin/main (`0d5f5ac6f`, 2026-11-17).
- «Publicada» es copia literal de `mirovaEqVrp` de `frontend/index.html`: VRP mayor que 0, `distance_class == summit` y
  centroide del cúmulo a `inner_radius_km` o menos (los 34 sin MIROVA, con 5 km, como hace el tablero).
- Conjunto 11 (Tier A): `data/mirova_equivalent/`, 73.700 records, **8.546 pasadas publicadas en 3.006 noches-volcán**,
  del 2025-02-15 al 2026-11-17, todas nocturnas.
- Conjunto 34: `data/historia_34/` (10 volcanes del norte, tandas 1 y 2) más `data/sombra_34/` (los 34, desde el
  2026-11-03), 61.062 records, **365 pasadas que el predicado publicaría, en 354 noches**. Hoy el tablero sólo muestra la
  sombra (10 de esas 365); la historia espera su publicación. Los `data/mirova_equivalent/<uno de los 34>.json` son
  fósiles de abril de 2026 con el detector anterior y el tablero no los lee: quedaron fuera.
- Referencia MIROVA: `cargar_referencia_unificada` + `clase_mirova.resumir_pasadas`, pareo por volcán y sensor a
  ±120 s (más 60 s porque nuestra hora viene truncada al minuto). Ventanas sanas (A119): canal «union» (tabla + OCR)
  desde 2026-06-11; canal «tabla» sola desde 2026-03-01. MIROVA no publica los 34: para ellos la columna MIROVA es
  **SIN DATO** y el costo en protegidas no se puede medir.
- «MIROVA publicó» = la pasada de MIROVA tiene fila con VRP (alerta, FALSO_POSITIVO del scraper, mínima o sin
  geometría); `FALSO_POSITIVO` es etiqueta del scraper por quedar fuera de su radio, no de MIROVA (A11). «Rutina» =
  MIROVA miró y no vio nada. «Sin fila» = MIROVA no tiene esa pasada.
- Costo: (i) protegidas A pareadas a una pasada nuestra de la firma; (ii) **noches protegidas perdidas**: noches con
  alerta protegida de MIROVA en que todas nuestras publicadas caen en la firma (filtrarla nos dejaría sin nada esa
  noche). Denominador: 74 noches protegidas en «union» (73 con alguna publicada nuestra) y 135 en «tabla» (135 con
  alguna publicada nuestra).
- Umbrales: declarados al inicio del script; son de trabajo, no calibrados. Lo que decide es la columna de costo y la
  de MIROVA, que no dependen de afinar el umbral sino de qué pasadas toca.

## Resumen

| # | Escenario | Firma usada | Publicadas 11 (noches) | Publicadas 34 | MIROVA publicó / pareadas en ventana union | Protegidas A pareadas (union/tabla) | Noches protegidas perdidas (union/tabla) | Defensa |
|---|---|---|---|---|---|---|---|---|
| 1a | Incendio o quema, verano | centroide ≥ 2 km, al sur de 36°, dic a mar | 37 (31) | 0 | sin pasadas en ventana union; tabla: 1 de 5 | 0/0 | 0/0 | NADA (la firma atrapa fuentes fijas volcánicas, ver texto) |
| 1b | Calor lejos del cordón | centroide ≥ 10 km (sólo posible en PCC, inner 20 km) | 17 (17) | 0 | 2 de 3 | 0/0 | 0/0 | **MARCA** «lejos del cráter»; FILTRO en laboratorio |
| 2 | Borde de nube, fondo frío | sólo contraste (`n_abs = 0`) y `t_bg` 8 K bajo la mediana del volcán, sensor y mes | 182 (132) | 37 | 34 de 56 | 7/8 | 0/1 | NADA |
| 2b | Fondo heterogéneo | sólo contraste y `sd_nti` ≥ 2 × la mediana | 290 (179) | 4 | 85 de 96 | **70/71** | 0/1 | NADA (es la señal misma) |
| 3 | Gradiente de nieve o glaciar (A69) | sólo contraste, < 1 MW, `t_bg` < 255 K, píxel < 8 K sobre el fondo | 197 (164) | 17 | 20 de 60 (25 rutina) | 0/0 | 0/0 | **MARCA**; FILTRO en laboratorio |
| 4 | Lago cratérico o campo geotermal | Copahue o PCC con < 1 MW | 1.197 (379) | 0 | 161 de 215 | 2/4 | 0/1 | NADA |
| 4b | Fuente fija fuera del cráter | celda de ~1 km a ≥ 1,5 km, ≥ 5 noches | 481 (386) | 0 | 50 de 71 | 5/5 | 0/0 | NADA |
| 5a | Borde de barrido | cenit ≥ 55° y 1 píxel | 385 (375) | 30 | 32 de 70 (31 rutina) | 0/0 | 0/0 | **MARCA**; FILTRO en laboratorio |
| 5b | Volcán vecino | punto publicado más cerca del centro de otro volcán | 7 (7) | 0 | 2 de 2 | 0/0 | 0/0 | **MARCA** «más cerca de X» |
| 6 | Ruido de detector, SAA | 1 píxel, sin otra publicada del volcán a ±48 h ni otro sensor esa noche | 65 (65) | 162 | 9 de 32 (21 rutina) | 0/0 | **1**/0 | **MARCA**; no filtrar |
| 7 | Fuente industrial (norte) | fuente fija fuera del cráter al norte de 28° | 424 (345), todas volcánicas | 0 | 40 de 60 | 0/0 | 0/0 | NADA (ninguna industrial dentro del radio publicado) |
| 8 | Reflejo solar, suelo caliente de día | `dayflag = 1` | 0 | 0 | sin objeto | 0/0 | 0/0 | SIN OBJETO hasta abrir el día (#813, sesión s190-diurno) |
| 9 | Escena incompleta (gránulo partido) | `celdas_sin_dato > 0` o `L_bk = 0` | 251 (197) | 14 | 14 de 49 (**31 sin fila**) | 3/5 | 0/1 | **MARCA**; filtro según la tarea s190_fp |

Combinado (salida, bloque «combinaciones»):

| Propuesta | Firmas | Pasadas 11 (noches) | Pasadas 34 | Protegidas A pareadas (union/tabla) | Noches protegidas perdidas si se filtrara |
|---|---|---|---|---|---|
| MARCA en el tablero | 1b, 3, 5a, 5b, 6, 9 | 833 (702) | 182 | 3/5 | union: Tupungatito 2026-08-01 y 2026-09-28; tabla: Isluga 2026-06-10 |
| FILTRO en `laboratorio` | 1b, 3, 5a, 5b | 560 (507) | 39 | 0/0 | ninguna |

La MARCA no calla nada, así que su costo real es cero; la fila dice lo que costaría si alguien la convirtiera en filtro,
y por eso 6 y 9 quedan sólo como marca. El FILTRO del laboratorio, con las cuatro firmas juntas, no toca ninguna
alerta protegida de MIROVA en las dos ventanas.

**Lectura de conjunto.** Ningún escenario justifica un filtro en la réplica: donde la firma es grande (2, 2b, 4, 4b) es
calor real que MIROVA también publica, y filtrarla cuesta alertas protegidas. Donde la firma se separa de MIROVA (3, 5a,
6, 9: MIROVA dice «rutina» o no tiene la pasada en un tercio a dos tercios de los casos) el costo en protegidas es
cero o una noche, y la herramienta adecuada para la réplica no es un filtro sino encontrar por qué divergimos
(paridad), con una marca mientras tanto.

## Escenario por escenario

### 1. Incendios forestales y quemas agrícolas

**Fenómeno.** Un incendio es calor real, a menudo más intenso que un domo, pero en el bosque o el campo, no en el
cráter. Dura de horas a días, se mueve y lo ven todos los sensores. En el sur la temporada es de diciembre a marzo.

**Lo que muestran los datos.** La firma ingenua (centroide a 2 km o más, al sur de 36°, de diciembre a marzo) junta 37
pasadas en el conjunto 11, pero casi todas son dos fuentes fijas: una celda de Copahue a 2,0 km del centro de
`volcanoes.yaml` (20 noches, 0,07 a 0,16 MW, sólo VIIRS 375) y otra de Cordón Caulle a 2,9 km (14 noches). Una fuente
que se repite en la misma celda durante semanas no es un incendio. El control estacional lo confirma: la tasa de
publicadas lejos del cráter por pasada nocturna válida en el sur es baja en pleno verano (enero 3 de 2.057, febrero 5
de 2.762, diciembre 1 de 2.041) y máxima en marzo y abril (28 de 4.065 y 23 de 3.962); no hay exceso de temporada de
incendios. Los 34 del sur sólo tienen datos desde el 2026-11-03 (sombra): para ellos es SIN DATO hasta que corra su
historia.

Lo que sí parece calor no volcánico son las **17 pasadas de Puyehue-Cordón Caulle con centroide a 10 km o más** (11 a
20 km; el inner de PCC es 20 km porque así lo trae el KML de MIROVA): posiciones distintas cada vez, una sola noche
cada una, en todas las estaciones, 0,2 a 3,6 MW, de 1 a 9 píxeles. Las 7 de ellas que caen más cerca del centro de
Carrán-Los Venados que del de PCC están en la fila 5b. En ventana, MIROVA publicó 2 de 3 (las dos con la etiqueta
FALSO_POSITIVO del scraper, o sea fuera de su radio pero publicadas por MIROVA) y la tercera no tiene fila. Con la tabla
sola desde marzo: 2 de 5 publicadas, 3 sin fila.

**FIRMS.** No se pudo cruzar: la API de archivo de FIRMS pide `MAP_KEY` (registro), y crear credenciales no es algo
que haga esta sesión (`docs/s131/agentes/OTRO_SENSOR.md` ya lo había dejado igual). Hay dos caminos para Nicolás:
registrar el `MAP_KEY` gratuito (y anotarlo en `REGISTRO_CREDENCIALES.md`), o usar los CSV públicos de los últimos 7
días, que no piden clave y alcanzan para la vigilancia NRT pero no para la historia. **SIN DATO.**

**Defensa.** 1a: NADA (lo que atrapa es volcánico). 1b: MARCA «lejos del cráter (≥ 10 km), posible fuente no
volcánica» en el tablero; FILTRO en laboratorio, idealmente con FIRMS cuando haya clave. Costo medido: 0 protegidas y 0
noches.

### 2. Bordes de nube y nube fina

**Fenómeno.** Una nube enfría el infrarrojo térmico. Si el píxel central queda despejado y sus vecinos nublados, el
fondo de la ventana 3 × 3 baja y el contraste (dNTI, dETI) del píxel central sube sin que haya más calor. La firma
esperada: alerta sólo por contraste (no por el umbral absoluto de NTI) con un fondo más frío que lo habitual.

**Lo que muestran los datos.** 182 pasadas del conjunto 11 (2,1 %) y 37 del 34 cumplen la firma. MIROVA publicó 34 de
las 56 que caen en su ventana. Las publicadas no están más cargadas de fondo frío que el conjunto de detecciones: 2,2 %
de las publicadas contra 4,5 % de todas las detecciones nocturnas del conjunto 11 (11,4 % contra 14,4 % en el 34), y lo
mismo con umbrales de 5 y 12 K. Límite del control: `t_bg_k` sólo se guarda cuando la pasada detectó algo (61.451
records sin detección no lo traen), así que la base son las detecciones, no las escenas despejadas sin detección. Un
control contra escenas sin detección queda SIN DATO.

La variante de fondo heterogéneo (2b) atrapa sobre todo Láscar y Chillán, donde la heterogeneidad la pone el propio
foco caliente: filtrarla perdería 70 protegidas pareadas (66 de Chillán).

**Defensa.** NADA, en la réplica y en el laboratorio, hasta tener una máscara de nube independiente del propio
detector. Filtrar costaría 7 a 8 protegidas por pasada (2) o 70 a 71 (2b) y una noche (Isluga 2026-06-10, tabla).

### 3. Gradiente topográfico en nevados y glaciares (A69)

**Fenómeno.** De noche la nieve y el hielo se enfrían más que la roca desnuda. Un píxel de roca rodeado de nieve tiene
más contraste térmico que sus vecinos sin que haya calor volcánico. La firma: alerta sólo por contraste, débil (bajo 1
MW), con fondo muy frío y el píxel apenas unos grados sobre él.

**Lo que muestran los datos.** 197 pasadas (2,3 %); 121 son de Tupungatito, el caso del anillo glaciar (A19), donde
además la vía usa la caja `sens` en VIIRS 750 (D36). En ventana, MIROVA publicó 20 de 60, dijo rutina en 25 y no tiene
fila en 15: es una divergencia de paridad, no un falso positivo que MIROVA comparta.

**Defensa.** MARCA «contraste débil sobre fondo de nieve». FILTRO en laboratorio. En la réplica, la defensa correcta
es la paridad: averiguar por qué publicamos lo que MIROVA llama rutina (punto de partida, D36 en Tupungatito). Costo
medido del filtro: 0 protegidas y 0 noches.

### 4. Lagos cratéricos tibios y campos geotermales

**Fenómeno.** Calor real, pero no magmático en el sentido de lava: el lago ácido y las fumarolas de Copahue, los campos
geotermales y fumarolas del Cordón Caulle. Es débil, persistente y en el mismo lugar.

**Lo que muestran los datos.** Copahue y PCC bajo 1 MW: 1.197 pasadas (14,0 % del conjunto 11), y MIROVA publicó 161
de 215 en ventana. La variante «fuente fija fuera del cráter» (4b) junta 481 pasadas en celdas que se repiten: la del
flanco NNO de Lastarria a 2,4 km (315 noches, sólo VIIRS 375, MIROVA alerta 35 de 55), la de Copahue a 2,0 km, la de
Cordón Caulle a 2,9 km, una de Isluga a 1,9 km y una de Chillán a 1,9 km (VRP mediano 1,53 MW, MIROVA alerta 9 de 10).
Todas son fuentes volcánicas o hidrotermales conocidas que MIROVA también publica.

Observación lateral: la celda persistente de Copahue está a 2,0 km al este del centro de `volcanoes.yaml`. Si esa
celda es el cráter activo, la coordenada del volcán no apunta al cráter; no lo verifiqué y queda para la tarea de
coordenadas (s190-coordenadas), que no tiene a Copahue en su lista.

**Defensa.** NADA. Filtrar costaría 2 a 5 protegidas y una noche (PCC 2026-05-25, tabla). Que el foco sea geotermal y
no lava es información para el operador de OVDAS, que ya la tiene; no es un error del detector.

### 5. Geometría: borde de barrido y volcán vecino

**Fenómeno.** Lejos del nadir el píxel crece varias veces respecto del nadir, el efecto bow-tie repite
líneas y la geolocalización empeora. Un foco pequeño queda diluido en un solo píxel grande y su posición puede caer en
el volcán de al lado.

**Lo que muestran los datos.** 5a (cenit ≥ 55° y 1 píxel): 385 pasadas del 11 y 30 del 34. En ventana MIROVA publicó 32
de 70 y dijo rutina en 31: otra divergencia de paridad. El `.m` de detección de VIIRS 750 de MIROVA (OSF
zm62w) no corta por cenit: el único descarte geométrico es el sun-glint bajo 12°; para MODIS y VIIRS 375 no tenemos su
código, SIN DATO. 5b: 7 pasadas, todas de PCC, cuyo punto queda más cerca
del centro de Carrán-Los Venados (son parte de las 17 de 1b); MIROVA publicó las 2 que caen en ventana. Ningún píxel se
publicó a la vez para dos volcanes en la misma pasada. En los 34, 0 casos de 5b; Macá y Cay comparten una sola entrada
(MacaCay) y no se pueden separar con este instrumento. Descabezado Grande con Cerro Azul y Mocho-Choshuenco no dieron
casos, pero sólo tienen la sombra desde el 2026-11-03: la prueba es corta.

**Defensa.** MARCA «píxel único en borde de barrido» y «más cerca de <vecino>». FILTRO en laboratorio para 5a. Costo
medido: 0 protegidas y 0 noches.

### 6. Ruido de detector y Anomalía del Atlántico Sur (SAA)

**Fenómeno.** Protones atrapados en la SAA, que a la altura de VIIRS y MODIS cubre buena parte de Sudamérica austral,
golpean el detector y dejan un píxel o una línea con radiancia alta en el infrarrojo medio. Se ve como un píxel solo,
que ningún otro satélite ni sensor repite.

**Evidencia publicada.** Para VIIRS hay: la documentación del producto de fuego de 375 m dice que la SAA puede producir
temperaturas de brillo espurias en I4 y falsas alarmas; NASA documenta barridos espurios de M13 con radiancia alta en el
L1B, y el equipo de fuego de VIIRS veía decenas de anomalías nocturnas por noche sobre el Atlántico antes de filtrarlas.
Para MODIS bandas 21 y 22 no encontré fuente que lo documente: **SIN DATO**.

**Lo que muestran los datos.** 1 píxel, sin otra publicada del volcán a ±48 h ni otro sensor esa noche: 65 pasadas del
11 (0,8 %), 62 de ellas VIIRS 375; MIROVA publicó 9 de 32 en ventana y dijo rutina en 21. En el 34 son 162 de 365
(44 %), sobre todo Irruputuncu (57) y Guallatiri (44) en VIIRS 375, y 103 de las 162 caen a 1,5 km o menos del centro:
ambos volcanes tienen fumarolas activas en la cumbre, así que lo más probable es calor fumarólico débil en el límite de
detección, no ruido; sin referencia MIROVA no se puede decidir. Con los records no se separa un impacto de partícula de
calor real débil: haría falta mirar el L1B (un impacto ocupa un detector o un barrido, no un foco).

**Defensa.** MARCA «píxel único sin confirmar». No filtrar: con la firma se perdería una noche protegida (Tupungatito
2026-09-28, union) y, combinada con las otras marcas, dos (también Tupungatito 2026-08-01).

### 7. Fuentes industriales en el norte

**Fenómeno.** Fundiciones, antorchas y relaves calientes son calor real y constante en un punto fijo.

**Lo que muestran los datos.** Al norte de 28° las únicas fuentes fijas fuera del cráter dentro del radio publicado son
el campo de Lastarria (fumarolas, MIROVA alerta 35 de 55) y una celda de Isluga; 0 candidatas industriales en el 11 y
en los 10 del norte con historia. Con inner de 3 a 5 km, una mina tendría que estar casi en la cumbre para publicarse.
No medí las detecciones lejanas (fuera del inner), que no se publican.

**Defensa.** NADA.

### 8. Reflejo solar, salares y suelo caliente de día

0 pasadas diurnas publicadas: la vía publica sólo de noche. SIN OBJETO hasta que se abra el día (#813); lo mide la
sesión s190-diurno.

### 9. Escena incompleta (agregado)

**Fenómeno.** Cuando el gránulo corta la ROI o hay celdas sin dato, el fondo se calcula con menos vecinos (o queda en
cero, `L_bk = 0`) y el contraste de una celda tibia se infla. Es el mecanismo que la tarea s190_fp está mirando en
MacaCay (`L_bk = 0`, 2.096 celdas sin dato).

**Lo que muestran los datos.** 251 pasadas del 11 y 14 del 34. Lo más llamativo es la referencia: de las 49 en ventana,
**31 no tienen fila en MIROVA**, contra 14 que MIROVA publicó y 4 rutina. Sugiere que MIROVA no procesa o no publica
escenas incompletas que nosotros sí; es SOSPECHA y la mide s190_fp.

**Defensa.** MARCA «escena incompleta». El filtro lo decide s190_fp: con esta firma costaría 3 a 5 protegidas y una
noche (Isluga 2026-06-10, tabla).

## Qué queda abierto

1. Paridad en 3, 5a, 6 y 9: publicamos pasadas que MIROVA llama rutina o no tiene. Es lo que más acercaría la réplica, y
   se resuelve en `pipeline/`, no con un filtro.
2. FIRMS para 1b: necesita `MAP_KEY` (decisión de Nicolás) o los CSV públicos de 7 días.
3. Historia de los 24 del sur fuera de las tandas 1 y 2: sin ella, incendios en los 34 es SIN DATO.
4. Coordenada de Copahue (lateral, para s190-coordenadas).

Fuentes de la sección 6: [ATBD de fuego VIIRS I-band (NOAA STAR)](https://www.star.nesdis.noaa.gov/aerosoltraining/documents/VIIRS_AF_Iband_ATBD_v1.0_20200506.pdf),
[nota de NASA LandWeb sobre barridos M13](https://landweb.modaps.eosdis.nasa.gov/displayissue?id=657),
[NASA Earth Observatory, «A Fire in the Middle of the Atlantic Ocean?»](https://earthobservatory.nasa.gov/images/144141/a-fire-in-the-middle-of-the-atlantic-ocean),
[VIIRS I-Band 375 m Active Fire Data (Earthdata)](https://www.earthdata.nasa.gov/data/instruments/viirs/near-real-time-data/viirs-i-band-375-m-active-fire-data).
