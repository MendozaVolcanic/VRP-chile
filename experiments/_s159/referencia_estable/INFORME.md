# Estabilidad de la referencia de MIROVA (S159, 2026-10-21)

Auditoría de sólo lectura. No se modificó nada del repositorio; todo vive en
`C:\vrp-trabajo\s159-pruebas\experiments\_s159\referencia_estable\`.

## Qué se midió y con qué

La referencia llega por dos canales que `.github/workflows/sync-mirova-csv.yml` copia a NUESTRO repo:

| canal | ruta en el repo | cadencia real de la copia |
|---|---|---|
| tabla (`latest.php`, consolidado) | `latest_consolidado.csv` | horaria desde 2026-05-24 (antes, congelada a mano desde S73); commitea sólo si cambió |
| OCR de las imágenes | `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` | semanal (auto-audit) hasta 2026-09-14; horaria desde 2026-09-20 |

`historia_referencia.py` recorre las versiones commiteadas en `origin/main` (sha `d516b9d8c`) con
`git cat-file --batch`, sin red, y compara cada una con la anterior. `analizar.py` saca los números.
Dos corridas:

- **Ventana de 60 días** (base 2026-08-21 23:36, hasta 2026-10-21 23:40): 354 versiones de la tabla y
  47 del OCR. `historia.json` → `resumen_60d.txt`.
- **Historia completa** (desde la primera copia horaria, 2026-05-23, hasta 2026-10-21 23:40): 1.238
  versiones de la tabla y 56 del OCR. `historia_completa.json` → `resumen_completa.txt`. (La pedí con
  `--hasta 2026-08-22` y el flag no se aplicaba por un error mío en el script, ya arreglado; la corrida
  quedó como superconjunto y se usa así.)

Definiciones:
- **Clave de fila**: volcán normalizado + sensor normalizado + `Fecha_Satelite_UTC` al minuto (la de
  `scripts/referencia_mirova_unificada.py::clave` sin el canal, porque el canal es el archivo).
- **Contenido** (lo que cuenta como reescritura): `Tipo_Registro`, `VRP_MW`, distancia (tabla:
  `Distancia_km`; OCR: `Distancia_km` si es mayor que 0, si no la de `Nota_Validacion`, como
  `leer_pasadas`) y `Clasificacion Mirova`.
- **Metadatos** (no cuentan): `Ultima_Actualizacion*`, `Fecha_Proceso*`, `Editado`, `Ruta Foto`, `timestamp`.
- **Estratos**: alerta de 1 MW o más (protegida), alerta bajo 1 MW, alerta sin geometría (V31.1),
  FALSO_POSITIVO, RUTINA.
- **Edad** de un evento: hora del commit de nuestra copia menos la hora de la pasada.

### Las dos preguntas del instrumento

1. *Si lo medido estuviera roto, ¿lo vería?* Sí, para altas, bajas y cambios de contenido entre dos
   versiones consecutivas de nuestra copia. **No** ve lo que pasa entre dos copias: Mirova-v1 commitea
   cada 5 min y en la ventana de 60 días la brecha entre versiones nuestras es mediana 3,9 h, p90 6,6 h,
   máximo 22,3 h (2026-10-17). El sync tuvo 200 corridas del 2026-09-12 a hoy (192 verdes, 8
   canceladas, 0 fallas; `gh run list --workflow sync-mirova-csv.yml --limit 200`), bastante menos que
   las ~940 horas del tramo. En el OCR, antes del 2026-09-20 la copia es semanal: un cambio del OCR
   anterior a esa fecha sólo se ubica «entre dos copias».
2. *Si el instrumento estuviera muerto, ¿se vería distinto?* Sí: el conteo de la ventana cierra
   (33.814 filas base + 10.544 altas − 1.948 bajas = 42.410 en la última versión) y la historia completa
   **encontró cambios reales de contenido** (H1), así que el «0 cambios» de los últimos 60 días no viene
   de un instrumento ciego.

**Nulo**: la última versión de la tabla contra sí misma da 0 altas, 0 bajas, 0 cambios, 0 metadatos.
**Control positivo sintético**: sobre esa versión (42.410 filas), sumar 7,5 MW a una fila, cambiar el
tipo de otra y borrar una tercera da `alta 0 / baja 1 / cambio 2`, campos `tipo` y `vrp` (esperado
0 / 1 / 2). **Controles positivos reales**: la versión `82b1401db` (2026-10-21 23:40) entra como la última,
con la pasada MODIS de las 20:05 UTC de hoy; y las 163 filas perdidas el 2026-08-19 17:41 que volvieron a
las 19:52 aparecen como 163 bajas seguidas de 163 «reaparece» (H4).

**Límite del OCR**: el workflow rechaza una versión del OCR con menos líneas que la anterior (paso
«Download fresh OCR CSV»), así que una baja neta del OCR no puede entrar a nuestra copia. El guard no
disparó en ninguna de las 200 corridas desde el 2026-09-12.

## Hallazgos, lo peor primero

### H1. El OCR reescribió 39 alertas viejas a FALSO_POSITIVO, 30 de ellas protegidas, sin tocar sus fechas

- SCRIPT:SALIDA `analizar.py historia_completa.json` → `resumen_completa.txt`, bloque OCR:
  `cambios por campo {'tipo': 39, 'dist': 39}`, `alerta_>=1MW -> falso_positivo: 30`,
  `alerta_<1MW -> falso_positivo: 9`.
- QUÉ PASA. El scraper volvió a medir la distancia de alertas OCR ya publicadas y las reclasificó: la
  distancia pasó de 0 a 2,1 km (en el cráter) a **9,7 a 33,4 km** (fuera del radio) y el tipo, de
  `ALERTA_TERMICA_OCR` a `FALSO_POSITIVO_OCR`. El VRP no cambió en ninguna (0 de 39) y
  **`Ultima_Actualizacion` tampoco**: la fila reescrita conserva las fechas de su primera escritura.
  Fueron dos tandas: 34 filas entre nuestras copias del 2026-05-29 y del 2026-07-01, y 5 entre las del
  2026-08-03 y del 2026-08-10. Las pasadas van del 2026-02-27 al 2026-08-01 (edad en nuestra copia: 9 a
  125 días). Por volcán: Láscar 17, Lastarria 13, y 2 o menos en Isluga, Planchón Peteroa, Tupungatito,
  Llaima y Copahue; 37 VIIRS 375 y 2 MODIS. Ejemplos protegidos: Lastarria VIIRS 375 2026-05-12 18:00,
  3,83 MW, de 0,76 a 10,88 km; Planchón Peteroa VIIRS 375 2026-05-11 19:42, 9,27 MW, de 0,67 a 23,19 km;
  Tupungatito VIIRS 375 2026-07-08 17:36, 1.357,39 MW, de 0 a 24,86 km.
- Contradice un hecho escrito: `docs/audit_s139/MAPA_BASES_MIROVA_V1.md:142` y `:340` («no hubo
  reprocesos retroactivos del OCR») y el hito de `scripts/calidad_referencia_mirova.py:26`. Ese
  instrumento era una matriz mes de pasada × mes de **proceso**; como el reproceso no toca las fechas de
  proceso, la matriz no podía verlo (la pregunta 1 del instrumento, respondida en contra). Corresponde
  marcarlo según A113.
- CÓMO SE VE EN EL DASHBOARD. Un punto de MIROVA en el cráter que pasa a «lejano»: una alerta de MIROVA
  que deja de contar como tal. No revisé los JSON del tablero de esas fechas (SOSPECHA en esa parte).
- CÓMO REPRODUCIRLO. `git show dfa5e46c4:data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv | grep "2026-05-12 18:00" | grep Lastarria`
  y el mismo `grep` sobre la versión anterior del archivo (`git log -2 --format=%h dfa5e46c4 -- <ruta>`).
- CONFIANZA. CONFIRMADO (medido). La causa (recalibración de la geometría del OCR, el tramo «mal
  calibrado hasta 2026-06-11» de A119) es SOSPECHA.
- GRAVEDAD 4. Un A/B leído antes del 1 de julio contaba 30 alertas protegidas más que uno leído después,
  con los mismos datos nuestros, y en la fila no queda rastro: sólo una copia vieja lo muestra.

### H2. La tabla pierde filas viejas en tandas y no las devuelve

- SCRIPT:SALIDA `resumen_60d.txt`, bloque CONS.
- QUÉ PASA. En la ventana de 60 días el remoto perdió **1.948 filas de pasadas ya ocurridas** en
  **6 tandas**, cada una en una sola versión: 2026-08-25 19:55 (202), 08-26 19:18 (186), 10-06 02:57
  (207), 10-16 21:25 (529), 10-17 22:17 (194) y 10-18 18:04 (630). Por estrato: **14 alertas
  protegidas**, 77 alertas bajo 1 MW, 46 FALSO_POSITIVO y 1.811 RUTINA. Por sensor: 695 MODIS, 619
  VIIRS 375, 634 VIIRS 750. Pierden los 11 volcanes (de 139 en Villarrica a 236 en Chaitén) y todos los
  meses desde enero en proporción parecida: se ve como un muestreo al azar del archivo entero.
  **Ninguna reapareció** en la tabla hasta la última versión. Ninguna baja tiene una alta vecina (mismo
  volcán y sensor, ±15 min) en la misma versión: no son renombres de clave. La fila perdida más joven
  tenía 19,2 h.
- Las 14 protegidas: Láscar 10 (MODIS 2026-02-09, 02-14, 03-19, 04-05, 04-18; VIIRS 375 03-21, 05-02,
  05-12, 06-01; VIIRS 750 01-15), Puyehue-Cordón Caulle 3 (VIIRS 375 01-13; VIIRS 750 01-23, 06-05) y
  Villarrica 1 (VIIRS 375 2026-08-21 05:48, 1,82 MW). Siete tienen copia en el OCR y siete sólo
  existían en la tabla.
- CÓMO SE VE EN EL DASHBOARD. El tablero lee `data/mirova/<Volcán>.json`, que el workflow rehace desde
  la tabla y el OCR cada vez que la tabla cambia. Si la fila perdida tiene copia en el OCR, el JSON la
  conserva con `source: ocr` y la distancia del OCR (Villarrica VIIRS 375 2026-08-21 05:48 pasó de 0,84
  a 0,95 km). Si no la tiene, **la alerta de MIROVA desaparece del gráfico sin aviso**: Láscar MODIS
  2026-02-09 07:20, 1,64 MW, está en `data/mirova/Lascar.json` en `5c55c0749`, falta en `0c8848ff9` y
  sigue faltando en `origin/main`. (Comprobado para esa; las otras seis sin copia OCR, SOSPECHA por el
  mismo mecanismo.)
- CÓMO REPRODUCIRLO. `python -I historia_referencia.py --desde 2026-08-22` y
  `python -I analizar.py historia.json`. Puntual (la versión anterior del archivo es `5c55c0749`, no
  `0c8848ff9~1`): `git show 5c55c0749:latest_consolidado.csv | grep "2026-08-21 05:48" | grep Villarrica`
  trae la fila VIIRS 375 de 1,82 MW; en `0c8848ff9` ya no está.
- CONFIANZA. CONFIRMADO. La causa (escritura concurrente en Mirova-v1, issue MendozaVolcanic/Mirova-v1#19)
  es SOSPECHA: no abrí ese repo.
- GRAVEDAD 4.

### H3. La unión histórica tapa las pérdidas, pero con días de atraso y no todas

- SCRIPT:SALIDA `resumen_60d.txt` (`bajas en union_historica de hoy 1946 de 1948`) y el cruce con las tres
  versiones commiteadas de `data/mirova_reference/union_historica/consolidado_filas_perdidas.csv`.
- QUÉ PASA. `cargar_referencia_unificada` (`scripts/referencia_mirova_unificada.py:163-180`) suma por
  defecto las filas que la tabla perdió. Esa unión la regenera el auto-audit semanal: existe desde el
  2026-10-14 (794 filas) y se regeneró el 2026-10-19 16:29 (2.145; entraron 1.351, no salió ninguna).
  Hoy recupera 1.946 de las 1.948 bajas y las 14 protegidas. Pero:
  1. entre la tanda y la regeneración la fila no está en ninguna parte: las 7 protegidas perdidas del
     16 al 18 de octubre faltaron entre 0,9 y 2,8 días; las 7 de agosto y del 6 de octubre faltaron hasta
     el 14 de octubre;
  2. no recupera 2 RUTINA MODIS (Láscar y Tupungatito, pasada 2026-10-16 01:45) que llegaron a las 07:08 y
     se perdieron a las 21:25 del mismo día: la unión toma una versión por día;
  3. no ve las reescrituras de H1: sólo guarda filas que desaparecen, no filas que cambian;
  4. también mueve la vara: un banco con la unión del 14-oct y otro con la del 19-oct miden contra 1.351
     filas distintas con el mismo remoto.
- CÓMO SE VE EN EL DASHBOARD. Invisible: la unión no entra a `data/mirova/*.json` (el paso «Rebuild» pasa
  sólo `--source latest_consolidado.csv --ocr ...registro_vrp_ocr.csv`).
- CONFIANZA. CONFIRMADO. GRAVEDAD 3.

### H4. Una versión corrupta de la tabla: 822 duplicados y 163 filas menos durante dos horas

- SCRIPT:SALIDA `resumen_completa.txt` y el desglose de la versión `81dd25ce3`.
- QUÉ PASA. La versión del 2026-08-19 17:41 traía 822 claves repetidas (filas idénticas, por ejemplo
  Nevados de Chillán MODIS 2026-08-17 21:30 dos veces) y le faltaban 163 filas (152 RUTINA, 6 alertas
  bajo 1 MW, 5 FALSO_POSITIVO). La de las 19:52 devolvió las 163 y quitó los duplicados. Fuera de esa
  versión, los únicos duplicados son 3 pasadas de Planchón Peteroa del 2026-01-16 escritas como `Peteroa`
  y como `PlanchonPeteroa` (A14), con contenido idéntico, presentes hasta el 2026-08-19 y ausentes desde
  entonces. Ningún duplicado tuvo contenido contradictorio.
- CÓMO SE VE EN EL DASHBOARD. Dos horas con 6 alertas de MIROVA de menos; después vuelven.
- CONFIANZA. CONFIRMADO. GRAVEDAD 2 (`leer_pasadas` resuelve los duplicados, no las 163 faltantes).

### H5. Asentamiento: la tabla llega en menos de ~27 h; el OCR en menos de 20 h, salvo el relleno de V31.1

- SCRIPT:SALIDA líneas `alta ...` de los dos resúmenes y los cortes por commit.
- **Tabla, ventana de 60 días** (10.544 altas): ninguna llegó con más de 21,8 h. Mediana 4,5 h en MODIS,
  6,1 h en VIIRS 375, 5,9 h en VIIRS 750; protegidas (n = 89) mediana 8,1 h, p90 12,6 h, máximo 19,9 h.
- **Tabla, historia completa**: las 3.646 altas «tardías» del 2026-05-24 son la primera copia horaria
  sobre un archivo congelado desde S73 (atraso nuestro, no de MIROVA) y no cuentan. Fuera de esa, sólo 17
  filas llegaron con más de 24 h, todas RUTINA o FALSO_POSITIVO: 11 el 2026-06-15 (ausentes en la copia
  anterior con 11,7 h de edad, presentes a las 24,4 h) y 6 el 2026-07-22 (las 4 de VIIRS 750 de la pasada
  2026-07-21 19:12 estaban ausentes a las 25,1 h y presentes a las 27,1 h). Ninguna alerta llegó tarde.
- **OCR desde 2026-09-21** (copia horaria, 132 altas): alertas de 1 MW o más, máximo 19,9 h; bajo 1 MW,
  15,9 h; FALSO_POSITIVO, 10,3 h. Las únicas de más de 24 h son **12 alertas sin geometría**: 9 del relleno
  de V31.1 del 2026-10-15 18:16 (la más vieja, Nevados de Chillán 2026-10-10 06:30, 131,8 h, 32,0 MW en
  VIIRS 750) y 3 que coinciden con la brecha de 22 h de nuestra copia el 17-oct. Por diseño no son alerta
  de la lectura A; sí mueven la lectura B y su estrato.
- Antes del 2026-09-20 la latencia del OCR en nuestra copia (hasta 879,9 h) es atraso de nuestra copia
  semanal. La de origen (`Fecha_Proceso_UTC` menos la pasada, filas del último OCR desde agosto): VIIRS 375
  mediana 3,6 h y máximo 19,3 h (n = 284), VIIRS 750 máximo 19,3 h (n = 23), MODIS 7,9 h (n = 5).
- CONFIANZA. CONFIRMADO. GRAVEDAD 2: la llegada se asienta en un día; lo que no se asienta es la pérdida
  (H2) ni la reescritura (H1), que golpean a cualquier edad (de 19 h a 125 días).

### H6. El banco de paridad registra el hash, pero baja el remoto del momento

- ARCHIVO:LÍNEA `scripts/banco_paridad.py:493-503` y `scripts/referencia_mirova_unificada.py:191-200`.
- QUÉ PASA. Sin `--snapshot`, `banco_paridad.main` baja el último commit del remoto y anota su sha, más
  el `git hash-object` de la unión y del respaldo. Queda trazable, pero dos corridas del mismo A/B en días
  distintos usan varas distintas por defecto y no hay forma de pedir «el remoto de tal sha».
- CONFIANZA. CONFIRMADO (leído). GRAVEDAD 2.

## Recomendación para congelar la referencia en un A/B (no implementada)

1. **Congelar por hash de contenido**: el pre-registro guarda el `git hash-object` de la tabla, del OCR y
   de la unión usados, y una copia de los tres en el directorio del experimento; el evaluador se niega a
   correr si un hash no coincide. Es lo único que protege contra H1, porque la fila reescrita no deja
   marca en sus fechas.
2. **Tomar la vara de NUESTRA historia**: `git show <sha de origin/main>:latest_consolidado.csv` es
   reproducible sin red. Para la tabla, armar la vara como unión de todas nuestras versiones hasta el
   corte (clave volcán + sensor + minuto, gana la versión más nueva que tuvo la fila). Recupera las 1.948
   bajas de la ventana, incluidas las 2 que la unión diaria pierde, y no depende del auto-audit. Excluir
   la versión `81dd25ce3` (H4).
3. **Ventana de asentamiento: 48 h** desde la hora de la pasada, para los dos canales. Lo medido llega en
   27,1 h como máximo (tabla) y 19,9 h (OCR con geometría); 48 h deja margen para la brecha de 22 h de
   nuestra copia. Si las alertas sin geometría entran alguna vez al criterio, para ellas hacen falta
   7 días (máximo medido 131,8 h).
4. **Contra la pérdida y la reescritura no hay ventana**: pasan a cualquier edad. Al releer un A/B viejo,
   informar primero el delta de la vara (filas que entraron, salieron o **cambiaron de tipo** entre el hash
   congelado y el de hoy, por estrato) y recién después comparar veredictos. Este instrumento
   (`historia_referencia.py` + `analizar.py`) ya lo da.
5. Marcar según A113 la afirmación «sin reproceso retroactivo del OCR» en
   `docs/audit_s139/MAPA_BASES_MIROVA_V1.md:142,340`, `scripts/calidad_referencia_mirova.py:26` y A119.

## VERIFICADO LIMPIO

- **Contenido de filas de la tabla**: 0 cambios de tipo, VRP, distancia o clase en las 1.238 versiones
  desde el 2026-05-23 (`python -I analizar.py historia_completa.json`: el bloque CONS no tiene línea
  «cambios»). La tabla sólo crece y pierde; nunca reescribe una fila.
- **OCR en los últimos 60 días**: 0 cambios de contenido y 0 bajas en 47 versiones (`resumen_60d.txt`).
- **Variantes de nombre**: sólo las 3 de Peteroa del 2026-01-16, idénticas en contenido; 0 desde el
  2026-08-19 (`resumen_completa.txt`, `variantes`).
- **Duplicados con contenido contradictorio**: 0 (desglose de `81dd25ce3` y de la primera versión con
  duplicados, `359b922bd`).
- **Llegada tardía de alertas a la tabla**: 0 de 1.128 alertas con más de 24 h, fuera de la primera copia
  del 2026-05-24.
- **Guard del OCR**: 0 corridas en rojo del sync desde el 2026-09-12 (`gh run list`): el OCR remoto no
  se encogió en ese tramo.
- **Unión histórica**: sólo crece (0 filas salen entre sus tres versiones).
- **Instrumento**: nulo 0/0/0/0 y control positivo 0/1/2 (línea `autotest` de los dos resúmenes).

## Archivos

- `C:\vrp-trabajo\s159-pruebas\experiments\_s159\referencia_estable\historia_referencia.py` (recorre la historia)
- `C:\vrp-trabajo\s159-pruebas\experiments\_s159\referencia_estable\analizar.py` (resume)
- `C:\vrp-trabajo\s159-pruebas\experiments\_s159\referencia_estable\historia.json` y `resumen_60d.txt`
- `C:\vrp-trabajo\s159-pruebas\experiments\_s159\referencia_estable\historia_completa.json`, `resumen_completa.txt` y `completa.log`
