# S159, frente «pareo MODIS en el borde del gránulo»

Fecha 2026-10-21. Datos: `origin/main` en `533398f8f` (records de `data/mirova_equivalent/` y referencia de
`data/mirova_reference/`: snapshot con consolidado hasta 2026-10-19 08:30 y OCR hasta 2026-10-20 17:30, más
respaldo y unión histórica, vía `referencia_mirova_unificada.cargar_referencia_unificada`). Para #864, el
commit del run que lo abrió, `2e1bc0e31` (2026-10-19 16:29 UTC). Todo corrió sobre espejos extraídos con
`git archive` en `D:\vrp-trabajo\temporales\s159_pareo\` (borrados al terminar); nada en `scripts/` se editó.
Las variantes de pareo son parches en memoria (`variantes.py`).

Scripts y salidas, todos en `C:\vrp-trabajo\s159-pruebas\experiments\_s159\pareo_modis\`:

| script | qué mide | salida |
|---|---|---|
| `medir_pareo.py` | tasa base: records nuestros por categoría de pareo; filas de MIROVA sin par; pares de gránulos consecutivos | `medir_pareo_salida.txt`, `.json` |
| `borde_por_anillo.py` | que los pares de gránulos son el volcán partido (anillo de fondo repartido) | `borde_por_anillo_salida.txt` |
| `granulo_que_elige_mirova.py` | qué gránulo lista MIROVA cuando el volcán cae en dos | `granulo_que_elige_mirova_salida.txt` |
| `banco_variantes.py` | `banco_paridad` con pareo hoy / ancho / por órbita, pasada a pasada | `banco_variantes_0110.*`, `banco_variantes_0301.*` |
| `partidas_por_detector.py` | publicación en negativos de pasadas partidas contra enteras | `partidas_por_detector_salida.txt` |
| `fraccion_en_cambios.py` | para cada pasada que cambia de etiqueta, qué parte del ROI tenía el gránulo de MIROVA | `fraccion_en_cambios_salida.txt` |
| `audit_864_variantes.py` + `comparar_latest.py` | `auto_audit_weekly.main()` de #864 con fecha congelada, tres pareos | `audit_864_*.txt`, `cmp_*.txt` |
| (en línea) | conciliación con el verificador, horas UTC, protegidas de Chillán | `chequeos_menores_salida.txt` |

Variantes de pareo: **hoy** (±120 s, lo que está en `scripts/`); **ancha** (±390 s en todo pareo por pasada,
cubre el gránulo vecino de MODIS, 5 min, y de VIIRS, 6 min); **órbita** (la unidad es la pasada física: los
records del mismo volcán y plataforma en gránulos consecutivos se juntan en una cadena que publica si
cualquiera de sus records publica, y se etiqueta con las filas de MIROVA de cualquiera de sus horas o, si no
hay, del gránulo vecino de sus extremos). Ninguna cadena tiene más de dos gránulos (`audit_864_orbita.txt`:
6.756 de uno y 192 de dos; `banco_variantes_0110.txt`: 31.573 y 773).

## Resumen en una línea

El desfase existe y es geometría de borde, pero **la regla de hoy acierta en casi todos los casos y ensanchar
la tolerancia empeora el instrumento**: el gránulo vecino que MIROVA lista casi nunca contiene el cráter
cuando nosotros sí lo tenemos. En #864 no cambia ningún flag, ningún recall, ninguna razón de magnitud ni
ninguna alerta protegida.

## Hallazgos (lo peor primero)

### 1. MIROVA lista siempre el gránulo del SUR, contenga o no el cráter, y sólo alerta cuando el cráter está en él

- SCRIPT:SALIDA `granulo_que_elige_mirova.py` → `granulo_que_elige_mirova_salida.txt`
- QUÉ PASA. De noche Aqua, Suomi NPP, NOAA-20 y NOAA-21 bajan de norte a sur y Terra sube. Cuando el ROI de
  25 km cae en el límite entre dos gránulos de la misma órbita y MIROVA lista uno solo, lista el del sur en
  **526 de 537** casos (MODIS 127 de 130, con Terra al revés en el tiempo que Aqua; VIIRS 375 218 de 223;
  VIIRS 750 181 de 184). Con nuestra fracción del anillo de fondo como indicador de dónde está el cráter, en
  las filas RUTINA esa fracción en el gránulo de MIROVA se reparte entre 0 y 1 (mediana 0,55 MODIS, 0,46 en
  VIIRS; bajo 0,5 en 55 de 129, 114 de 201 y 103 de 184), mientras que en las **24 de 24 alertas** es 0,5 o
  más (V375 mediana 0,83). Lectura: MIROVA mira un solo gránulo por pasada y no ve el cráter cuando éste cayó
  en el del norte; su RUTINA ahí es «no miré», no «no vi». Denominador: cadenas de dos records nuestros de los
  11 Tier A, toda la historia, con exactamente un gránulo listado por MIROVA a ±120 s (las cadenas sin ninguna fila de MIROVA en
  ninguno de sus dos gránulos quedan fuera: en MODIS 146 de 150 son anteriores a la referencia; en VIIRS 437 de
  559 y 358 de 464, y el resto son pasadas VIIRS que MIROVA no lista).
- CÓMO SE VE EN EL DASHBOARD: invisible en el tablero. Se ve en las evaluaciones: esas pasadas entran como
  negativos limpios (con el record nuestro del gránulo sur, que tampoco tiene el cráter y casi nunca publica),
  y la publicación del gránulo norte, que sí ve el cráter, queda fuera de toda métrica.
- CÓMO REPRODUCIRLO: `python granulo_que_elige_mirova.py <espejo de origin/main>`. Caso: Isluga VIIRS 375
  2026-02-04 05:48 / 05:54, anillo 12.774 / 0 píxeles, MIROVA RUTINA a las 05:54, nosotros publicamos a las
  05:48 (0,189 MW a 0,79 km).
- CONFIANZA: CONFIRMADO el conteo y la asimetría; SOSPECHA alta la lectura «MIROVA no mosaica» (la prueba es
  indirecta: si mosaicara, sus alertas no tendrían por qué caer todas con fracción ≥ 0,5; con p ≈ 0,45 de
  caer bajo 0,5, 22 de 22 en V375 es improbable por azar). Falta confirmarlo con un GeoTIFF de MIROVA de una
  pasada partida.
- GRAVEDAD 2: el volumen es chico (las fracciones bajo 0,5 son 55, 114 y 103 en toda la historia, del orden
  del 1 a 3 % de los negativos limpios), pero ensucia justo los negativos que el proyecto usa para medir la
  sobre-publicación, y esconde pasadas en que MIROVA está ciega.

### 2. Las «121 de 5.815» no son pasadas perdidas: 130 de 148 son la otra mitad de una pasada ya pareada y las 18 restantes parean con un gránulo que no tiene el ROI

- SCRIPT:SALIDA `medir_pareo.py` → `medir_pareo_salida.txt`; `fraccion_en_cambios_salida.txt`;
  `chequeos_menores_salida.txt`
- QUÉ PASA. Ventana con referencia (2026-01-10 a 2026-10-21, desde la primera fila de MIROVA de cada volcán):
  **6.646 records MODIS nocturnos**; parean a ±120 s **6.349**; sólo con el gránulo vecino (±5 min)
  **148**; sin fila a ±10 min 149. En la ventana del verificador (2026-02-15 a 2026-10-17) el denominador
  coincide exacto (**5.815**) y hoy salen **128** en vez de 121 (su script leía otra copia de la referencia,
  sin respaldo ni unión histórica; la diferencia de 7 no la atribuí fila a fila). De las 148:
  - **130** tienen además un record nuestro en el gránulo que MIROVA lista: la pasada física SÍ está pareada,
    por el otro record. Clase de MIROVA: 129 RUTINA y 1 alerta bajo 1 MW (Villarrica 2026-09-25 08:00/08:05,
    0,9 MW). Ninguna protegida.
  - **18** son pasadas en que sólo tenemos un gránulo y MIROVA listó el vecino. Las 18 son RUTINA. En las 18
    nuestro gránulo trae entero el anillo de fondo (0,93 a 1,02 de la mediana de pasadas enteras del mismo
    volcán, plataforma y cenit a ±3°), o sea que el gránulo de MIROVA tiene a lo más un borde del ROI y no el
    cráter. Chillán 2026-01-19 02:40 (el control positivo) da 0,944: MIROVA 02:35 tiene ~6 % del ROI,
    coherente con el cráter en la línea 23 que midió el verificador. Por volcán: Chillán 5, Cordón Caulle 3,
    Chaitén 2, Láscar 2, Villarrica 2, Copahue, Llaima, Planchón Peteroa y Tupungatito 1. Por mes: 1 a 4,
    sin concentración.
  - Del lado de MIROVA, 21 filas MODIS nocturnas sin record a ±120 s pero con record a ±5 min: las 18 de
    arriba y 3 en que MIROVA listó los dos gránulos y nosotros uno (Lastarria 01-17 01:20, Planchón Peteroa
    06-01 08:15, Villarrica 08-08 07:10). Ninguna es alerta.
  Comprobé que es borde y no otra cosa: en los 283 pares de gránulos consecutivos MODIS de nuestro corpus el
  anillo de los dos miembros suma 0,913 del anillo entero (mediana; p10 0,878, p90 0,952) y el miembro menor
  tiene 0,208; un gránulo duplicado daría ~2 y una hora mal guardada ~1 en cada miembro. Control: las pasadas
  enteras dan 1,000 (p10 0,966). En las 148, la hora del record es la del nombre del gránulo (148 de 148), todas
  nocturnas, entre 00:50 y 08:50 UTC (ninguna cruza la medianoche, así que no cambia la noche de nadie).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python medir_pareo.py --raiz <espejo>`; Chillán MODIS Terra 2026-01-19 02:40,
  `MOD021KM.A2026019.0240.061.2026019131323.hdf`.
- CONFIANZA: CONFIRMADO los conteos; la fracción del ROI es un indicador indirecto de la línea del cráter
  (el record no guarda la posición dentro del gránulo, hallazgo 5).
- GRAVEDAD 1: el pareo de hoy no pierde ninguna pasada informativa. **Corrige la lectura del verificador de M**:
  contar Chillán 01-19 como noveno caso con referencia (la RUTINA de las 02:35) no vale, porque ese gránulo de
  MIROVA no tiene el cráter.

### 3. Ensanchar la tolerancia a ±5 min (o ±6) empeora el banco: cuenta dos veces la misma pasada y agrega negativos sin información

- SCRIPT:SALIDA `banco_variantes.py` → `banco_variantes_0110.txt` (ventana 2026-01-10 a 2026-10-21) y
  `banco_variantes_0301.txt` (2026-03-01 a 2026-10-21, la de `banco_paridad` por defecto), regla D-9
  original (la de `banco_paridad` por defecto).
- QUÉ PASA. Por pasada, ventana 01-10:

  | sensor | métrica | hoy | ancha | órbita |
  |---|---|---|---|---|
  | MODIS | recall en positivos | 0,8482 (n 112) | 0,8407 (n 113) | 0,8482 (n 112) |
  | MODIS | publica en negativos limpios | 0,0078 (n 6.156) | 0,0083 (n 6.302) | 0,0084 (n 6.171) |
  | VIIRS 375 | recall en positivos | 0,9279 (n 1.719) | 0,9167 (n 1.741) | 0,9279 (n 1.719) |
  | VIIRS 375 | publica en negativos limpios | 0,0268 (n 4.260) | 0,0277 (n 4.408) | 0,0284 (n 4.261) |
  | VIIRS 750 | recall en positivos | 0,7671 (n 365) | 0,765 (n 366) | 0,7671 (n 365) |
  | VIIRS 750 | publica en negativos limpios | 0,0088 (n 6.819) | 0,0091 (n 6.998) | 0,0094 (n 6.829) |

  Por noche de volcán no cambia nada en ninguna variante (sólo V750 n_neg 2.746 a 2.747). Con la ancha, los
  positivos nuevos son la mitad del borde de pasadas ya pareadas (V375: 22 nuevos, publica 1), y por eso el
  recall por pasada **baja** sin que se haya perdido ninguna alerta: es doble conteo. Las ~150 a 180 pasadas
  nuevas por sensor en negativos son las del hallazgo 2 y las mitades del hallazgo 1. Con órbita no entra ni
  sale ningún positivo; los cambios son 18 MODIS, 10 V750 y 1 V375 de un solo record que pasan de
  `sin_info` a negativo (MIROVA con un borde del ROI) y 2 MODIS, 7 V375 y 4 V750 partidas que pasan de no
  publicar a publicar. **En las 13 partidas, el gránulo de MIROVA tenía menos de la mitad de nuestro anillo
  (0,0 a 0,48) y el record que publica es el otro** (`fraccion_en_cambios_salida.txt`): no son
  sobre-publicación contra MIROVA, son pasadas en que MIROVA no miró el cráter.
- CÓMO SE VE EN EL DASHBOARD: invisible (es la vara, no el tablero).
- CÓMO REPRODUCIRLO: `python banco_variantes.py --raiz <espejo> --inicio 2026-01-10 --fin 2026-10-21 --out x.json`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 2 si alguien implementa el ±5 min que sugiere el frente: movería la tasa de falsas y el recall por
  pasada en la dirección equivocada, de a décimas de punto.

### 4. Las publicaciones del gránulo norte en pasadas partidas no entran a ninguna métrica, y son tres veces más frecuentes que en pasadas enteras

- SCRIPT:SALIDA `partidas_por_detector.py` → `partidas_por_detector_salida.txt` (variante órbita, ventana
  2026-01-10 a 2026-10-21; todos los records son K, frontera de datos 2025-02-15 en `cambio_detector.js` de hoy)
- QUÉ PASA. En negativos limpios de VIIRS 375, una pasada partida publica en **13 de 147 (8,8 %)** contra
  **108 de 4.114 (2,6 %)** de las enteras (Fisher p = 0,0002; cenit mediano 50 contra 52°, no es el cenit).
  VIIRS 750 4 de 169 contra 60 de 6.660 (p = 0,07); MODIS 2 de 131 contra 50 de 6.040 (p = 0,30). En las 19
  que publican, publica siempre el miembro con el anillo mayor, el que tiene el cráter: la hipótesis «el
  pedazo chico de anillo da un fondo ruidoso» queda **refutada**. Lo que queda es el hallazgo 1: en 13 de
  las 19 MIROVA miraba el gránulo sin cráter (las 6 restantes publican en el gránulo de MIROVA y el banco de
  hoy ya las cuenta). Casos que pesan: Chillán MODIS Aqua 2026-10-13 07:55, 2,076 MW a
  1,6 km, publicado, con MIROVA RUTINA a las 08:00 en un gránulo con 0,23 de nuestro anillo; Láscar MODIS
  2026-05-05 01:30, 0,739 MW, MIROVA 01:25 con 0,33.
- CÓMO SE VE EN EL DASHBOARD: el operador ve la detección (es un record más). Lo que no ve nadie es que las
  auditorías contra MIROVA la tratan como inexistente: ni falsa ni confirmada.
- CÓMO REPRODUCIRLO: `python partidas_por_detector.py <espejo>`; Chillán `MYD021KM.A2026286.0755.061.2026287110859.hdf`
  (2,076 MW, `summit`) y su vecino `MYD021KM.A2026286.0800.061.2026287111225.hdf` (sin cúmulo).
- CONFIANZA: CONFIRMADO el exceso y quién publica; SOSPECHA que sea calor real (no lo validé contra OVDAS ni
  SWIR; Chillán está en erupción en octubre y 2 MW a 1,6 km es coherente, pero no lo probé).
- GRAVEDAD 2: muy pocas pasadas, pero entre ellas hay una de 2 MW en Chillán en erupción que la comparación
  con MIROVA no puede ver.

### 5. El record no guarda dónde cayó el cráter dentro del gránulo

- ARCHIVO:LÍNEA `pipeline/process_modis.py:1581` persiste `diag_n_bg_anillo` (lo usé de indicador); ningún
  campo del record MODIS trae la línea ni la muestra del cráter (claves listadas para Chillán 2026-01-19 en esta
  sesión). `pipeline/fetch.py:752-753` busca gránulos con una caja de `radius_km/111` grados, así que el
  gránulo vecino que sólo roza el ROI a veces no se baja o no da record.
- QUÉ PASA. Para saber si una fila de MIROVA habla del cráter hay que saber en qué gránulo está el cráter. Hoy
  sólo se puede aproximar con la fracción del anillo; con la línea del cráter sería exacto.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO que el campo no está; SOSPECHA que la caja de búsqueda explique las 18 pasadas de un
  solo gránulo (podría ser también el corte de `min_bg_pixels=10`, `process_modis.py:628-631`).
- GRAVEDAD 1 (es un vacío de esquema, A7: la posición ya se calcula para el ROI y sólo falta guardarla).

## Efecto en #864 (auto-audit del 2026-10-19)

Control de reproducción: la variante «hoy» sobre `2e1bc0e31` con la fecha congelada a 2026-10-19T16:29:28Z
reproduce el `latest.json` commiteado **hoja por hoja (0 distintas de 1.203)** y los 10 flags del issue
(`cmp_commit_vs_hoy.txt`, `audit_864_hoy.txt`).

| bloque de #864 | ancha | órbita |
|---|---|---|
| 10 flags y veredicto FUERA_DE_BANDA | iguales | iguales |
| recall cráter y publicación por sensor (MODIS 66,7 % n 12; V750 73,3 % n 30; V375 96,8 % n 93) | iguales | iguales |
| razones de magnitud por volcán, por volcán y sensor, por píxeles, por cenit, por régimen, y `n_misma_pasada` | iguales | iguales |
| 5 alertas protegidas sin publicar (Tupungatito ×2, Cordón Caulle, Chillán MODIS 10-12 07:20 y 10-15 01:05) | iguales | iguales |
| falsas K MODIS | 7/658 → 8/682 | 7/658 → 8/659 |
| falsas K VIIRS 375 | 20/656 → 22/677 | 20/656 → 22/656 (3,0 → 3,4 %) |
| falsas K VIIRS 750 | 949 → 976 negativos, 1,1 → 1,0 % | 949 → 951 negativos |

Por qué recall y magnitud no pueden cambiar: `auto_audit_weekly.nuestros_por_noche` y
`noches_mirova_con_instante` agrupan por (volcán, sensor, fecha UTC), no por pasada, y ninguna pasada de borde
cruza la medianoche. Las dos protegidas MODIS de Chillán tienen un solo record a ±15 min, el de su misma hora
(`chequeos_menores_salida.txt`), y el verificador de M ya había ubicado su cráter en las líneas 981 y 187: no
son borde. Que el instrumento sí puede cambiar las protegidas lo muestra el control sintético (alerta a +5 min
de un record que publica: `sin_record` con 120 s, `publicada` con 390 s; `banco_variantes_0110.txt`, última
línea). En la tabla de falsas de órbita, el +1 de MODIS y el +2 de V375 son, por fecha, candidatos de la lista
de `fraccion_en_cambios_salida.txt` (Chillán 10-13 07:55; Lastarria 09-22 y Cordón Caulle 10-12 en V375),
todos con el gránulo de MIROVA sin el cráter: identidad SOSPECHA, no la pareé caso a caso sobre el corpus de
`2e1bc0e31`.

## VIIRS

Mismo fenómeno, con gránulos de 6 min: 224 records V375 y 196 V750 sólo parean con el vecino; 223 y 185 son la
otra mitad de una pasada ya pareada; 1 y 11 son de un solo gránulo (todas RUTINA, nuestro gránulo con el ROI
entero, 0,97 a 1,09). Las 22 alertas V375 que aparecen son mitades de pasadas ya pareadas. MIROVA elige el sur
todavía más sistemáticamente que en MODIS (hallazgo 1). No hay pérdida de alertas.

## Regla mejor que una tolerancia más ancha (descrita, no implementada)

1. Unidad = pasada física: records del mismo volcán y la misma plataforma en gránulos consecutivos
   (diferencia exacta de 5 min en MODIS, 6 en VIIRS). Publica si publica cualquiera de sus records.
2. Una fila de MIROVA informa sobre el cráter sólo si su gránulo contiene el cráter. Con los datos de hoy: en
   una pasada partida, si el miembro de MIROVA tiene la mitad o más del anillo; en una pasada de un solo
   record, si la fila de MIROVA es de ese mismo gránulo. Si no, la pasada va a un estrato «MIROVA sin cráter»
   (como `far_ref`): ni positivo ni negativo, y sus publicaciones se informan aparte.
3. Costo: tocar `banco_paridad.etiquetar` y `parear`, `auto_audit_weekly.alertas_protegidas` y
   `_misma_pasada`, y los más de 70 scripts que importan el etiquetador (que hoy reproducen resultados
   publicados: tendría que entrar como modo explícito, como D-9). Efecto medido: del orden de 100 a 300
   negativos menos en toda la historia por sensor, tasas que se mueven en centésimas de punto, ningún positivo.
   Con la línea del cráter persistida (hallazgo 5) la regla 2 sería exacta en vez de aproximada (cambio en
   `pipeline/`, regla A45).

Mi recomendación al orquestador: **no** cambiar `TOL_S` ni `VENTANA_S`. Si se quiere limpiar, la regla 2
como modo opcional del etiquetador; no es urgente para ninguna decisión de alerta.

## VERIFICADO LIMPIO

- El auto-audit reproduce #864 exacto con los datos y el código del run: `python audit_864_variantes.py --raiz
  <espejo de 2e1bc0e31> --variante hoy --out <dir>` y `python comparar_latest.py <latest commiteado>
  <dir>/latest.json` dan 0 hojas distintas de 1.203.
- Recall y magnitud del auto-audit son por noche, no por pasada: las variantes ancha y órbita no mueven ninguna
  de esas hojas (`cmp_hoy_vs_ancha.txt`, `cmp_hoy_vs_orbita.txt`: todas las diferencias están bajo
  `falsas_publicaciones`).
- Ninguna alerta protegida de MIROVA en toda la ventana con referencia queda sin par por el borde: las 148 MODIS
  son 147 RUTINA y 1 alerta de 0,9 MW ya pareada por el otro gránulo (`medir_pareo_salida.txt`).
- MIROVA guarda las horas MODIS en múltiplos exactos de 5 min con segundos 00 (12.007 de 12.007 filas MODIS del
  consolidado), igual que nuestro `datetime_utc` (hora de inicio del gránulo, 148 de 148 casos de borde): no hay
  desfase de convención horaria.
- No hay gránulos duplicados ni horas mal guardadas en los pares: la suma del anillo de los dos miembros da 0,91
  a 1,00 del anillo entero, no 2 (`borde_por_anillo_salida.txt`).
- Control negativo de `medir_pareo.py`: 0 records MODIS con fila de MIROVA a ±150 min (la otra plataforma está a
  más de 3 h). En VIIRS ese control no sirve (50 y 42 casos: otros satélites de la constelación a ~50 min) y no
  lo cuento.
- Las cadenas de gránulos nunca pasan de dos (`banco_variantes_0110.txt`: 773 de dos, ninguna de tres).
- La regla D-9 (`clase_mirova.VENTANA_S`) compara filas de MIROVA entre sí; MIROVA lista los dos gránulos de una
  órbita sólo 12 veces en 12.780 pasadas MODIS (`medir_pareo_salida.txt`), así que el borde no la afecta.

## Candidatas para BEYOND_MIROVA_EXTENSIONS §12

1. **Pasadas partidas en que MIROVA mira el gránulo sin cráter.** Procesamos los dos gránulos de la órbita;
   MIROVA lista sólo el del sur (526 de 537) y no alerta cuando el cráter quedó en el del norte (0 de 24
   alertas con el cráter fuera de su gránulo). Ejemplos ya publicados por nosotros: Chillán MODIS 2026-10-13
   07:55 (2,08 MW a 1,6 km, MIROVA RUTINA 08:00) y Láscar MODIS 2026-05-05 01:30 (0,74 MW). Validación que
   corresponde: OVDAS o SWIR de alta resolución, no MIROVA.
2. **Pasadas en que tenemos el gránulo con el ROI entero y MIROVA el vecino** (18 MODIS, 12 VIIRS en la
   ventana con referencia): ahí nuestro dato es el único que mira el cráter. Chillán 2026-01-19 02:40 (0,85 MW,
   `summit`) y Cordón Caulle 2026-06-26 07:40 (0,50 MW) publican.
3. **Guardar la línea y la muestra del cráter en el gránulo** (hallazgo 5): permitiría decir, pasada a pasada,
   si la fila de MIROVA podía ver el cráter.
