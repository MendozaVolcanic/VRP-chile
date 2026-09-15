# S139: el archivo OSF v2.5, es el mismo producto que MIROVA publica en NRT, o esta reprocesado

Auditoria de solo lectura. Scripts y salidas en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\osf_vs_nrt\`
(`01_match_nombres.py` a `03_cobertura_2025_y_satelite.py`, cada uno con su `*_salida.txt`). No se
modifico ningun archivo del repositorio fuera de esta carpeta y este informe.

## 0. Respuesta corta

> ⚠️ **Corrección S142 (A105).** La revisión manual de Coppola 2023 §2.5 es de la base **v.1**. El OSF
> **v2.5 no tuvo revisión manual**: "No additional quality control or manual screening was applied
> during this aggregation step" (Coppola et al. 2026, Scientific Data, p. 7, leído en página renderizada
> en S141). La clase es automática (DBSCAN más reglas por distancia, p. 10 a 12) y el archivo aplica
> umbrales VRP por sensor al construirse (Tabla 1, p. 8). La consecuencia práctica de este informe se
> mantiene (el OSF es un producto **filtrado**, no un espejo del NRT, y sus conteos no valen para el
> NRT), pero la causa es el filtrado por umbrales y clase automática, no la supervisión humana. Lo de
> abajo se conserva como se escribió.

**Esta reprocesado y supervisado a mano; no es un espejo del feed NRT.** No hay forma de comprobarlo
por comparacion pasada-por-pasada (el archivo termina el 2025-12-31 y las dos fuentes NRT locales
empiezan despues, sin un solo dia de solape), pero la documentacion oficial de MIROVA lo dice de forma
explicita: el archivo global es un producto **con revision manual** que quita incendios y falsas
alarmas antes de publicarse. Sirve para propiedades del algoritmo (formula, fondo, geometria). No
sirve para medir recall o precision de un clon NRT.

## 1. Solape temporal: NINGUNO, en ninguna de las dos fuentes locales

| fuente | ventana con datos | fuente de la fecha |
|---|---|---|
| OSF v2.5 (`VRP_GLOBAL_ARCHIVE_2025.csv`) | 2000-01-01 a 2025-12-31 | `timeUTC` min/max del CSV |
| Scraper Mirova-v1 (`registro_vrp_consolidado.csv` + `registro_vrp_ocr.csv`) | desde 2026-01-10 | primera fila del primer commit que creo el archivo (`35109b78`, 2026-01-11); repo GitHub creado 2026-01-09T15:54:58Z |
| `mirova-tif-archive` (headers "VRP: x MW @ y km" de imagenes NRT descargadas) | 2026-05-08 a 2026-05-20 (local, `up to date` con origin) | `index.csv`, 2.684 filas, `captured_at_utc`/`last_modified_utc` |

Brecha OSF-scraper: **10 dias** (2025-12-31 a 2026-01-10). Brecha OSF-TIF-archive: **~4 meses y 9
dias**. Ningun dia de 2025 tiene contraparte NRT local. Verificado con `git log --reverse` en ambos
repos hermanos (no son checkouts atrasados: los dos estan al dia contra `origin/main`).

## 2. Pareo TIF vs OSF por pasada: SIN DATO, no imposible de medir sino imposible de intentar

El plan pedia parear encabezados "VRP: x MW @ y km" de `mirova-tif-archive` contra filas del OSF
2025 (mismo volcan, misma hora UTC). El indice local (`index.csv`, 2.684 filas) cubre solo
**2026-05-08 21:43 UTC a 2026-05-20 12:51 UTC**, y el repo remoto arranco en ese mismo momento
(`gh api repos/MendozaVolcanic/mirova-tif-archive` -> `created_at: 2026-05-09T04:44:43Z`; el commit
inicial es `"init: scaffold mirova-tif-archive"` fechado 2026-05-09). No existe ni un solo TIF o KMZ
de 2025 en este repositorio: **n=0, fraccion identica = SIN DATO**. La pregunta "el VRP y la distancia
por pasada, son iguales o distintos" no se puede responder con los datos disponibles hoy; solo se
podra responder retroactivamente cuando el archivo tif-archive acumule 2026 completo y MIROVA publique
un OSF que cubra 2026 (probablemente a fines de 2026 o en 2027, ver seccion 4).

## 3. Que dice la documentacion oficial del OSF: revision manual explicita

### 3.1 `schema_v25.md` (extraido del docx `MIROVA_Database_Schema_v2.5.docx`, "Last updated: February 2026")

- "**class: INT**: Automated binary classification label (1 = volcanic detection; 0 = non-volcanic
  detection)."
- "The class field represents an automated classification and should be treated as a screening
  indicator rather than a definitive label."
- "While substantial quality control procedures are applied, the dataset may contain classification
  inaccuracies, missing values, incomplete records, or artefacts..."

Esto ya dice que hay control de calidad, pero no aclara si es automatico o manual, ni si implica
remover filas (no solo reetiquetarlas).

### 3.2 Coppola et al. 2023 (Frontiers, `documentacion/coppola2023_frontiers.md`), seccion 2.5
"Supervision of the dataset" (parrafo completo, cita literal menor a 15 palabras por fragmento):

> "the entire dataset has been supervised to remove obvious *non-volcanic* thermal features. This
> step was done manually by checking the time series and removing data points related to fires or
> false alerts, based on visual inspection of the images or based on fact-checking within volcanic
> activity reports, or news available on the web. However, some errors (alerts of non-volcanic
> origin) can be still present in the database..."

Esto es la fuente primaria mas fuerte del hallazgo: **la supervision es manual y remueve filas**
(no solo las reetiqueta con `class=0`). El resultado es que el OSF contiene MENOS registros que el
feed NRT crudo que le dio origen, porque las filas removidas ya no existen en el CSV que descargamos.
Un mismo parrafo tambien anticipa el limite: "algunos errores pueden seguir presentes" (no es depuracion
perfecta), y no dice en que paso del pipeline ocurre la limpieza (antes o despues de calcular VRP).

Coppola et al. 2019 (`coppola2019_frontiers.md`, sobre MIROVA v1 web) describe el sistema en linea como
un "sort of quality control service of the data" pensado para ayudar a la interpretacion humana en
tiempo casi real, distinto del proceso de curado retrospectivo del archivo v.1 completo (2023 §2.5).
Es decir: **hay dos capas de supervision distintas** documentadas en dos papers distintos: (a) el
apoyo visual que ofrece la web en NRT para que un humano interprete cada imagen, y (b) la limpieza
retrospectiva del archivo completo antes de publicarlo en OSF. La (b) es la que aqui importa.

## 4. Senales internas en el CSV para los 11 Tier A de Chile

Dato: `VRP_GLOBAL_ARCHIVE_2025.csv`, matcheado por `Volc_LAT/Volc_LON` (tolerancia 0,15 grados) y
verificado por `Volc_Name`. VRP esta en **vatios** (no MW; ver ordenes de magnitud, columna `VRP`).

### 4.1 El archivo mezcla generaciones de sensores, no un solo algoritmo en 25 anios

Codigo `Satellite` por anio (suma de los 10 Tier A con historia larga, Tupungatito no aparecio en el
matching por coordenadas):

| periodo | codigos presentes | interpretacion |
|---|---|---|
| 2000-2011 | 1, 2 | solo MODIS (Terra/Aqua) |
| 2012 en adelante | + 3 | se agrega VIIRS Suomi-NPP (lanzado oct-2011) |
| 2018 en adelante | + 4 | se agrega VIIRS NOAA-20 (lanzado nov-2017) |

Esto es un cambio de FLOTA de sensores, esperable y documentado por las fechas reales de lanzamiento,
no evidencia por si solo de reprocesado. Pero implica que "el OSF" no es un producto homogeneo: 2025
corre con 4 sensores simultaneos, 2005 con 1. Comparar Chile contra el OSF completo sin filtrar por
sensor/anio mezclaria regimenes distintos.

### 4.2 El piso de VRP positivo cae de golpe justo cuando se agrega VIIRS (~2012)

Ejemplos (minimo VRP>0 por anio, en vatios):

- Chaiten: 2008-2011 minimo 163.000-326.000 W -> 2012 en adelante 12.000-50.000 W.
- Copahue: previo a 2012 (pocas filas, todas `class=0`) minimo 180.000-2.000.000 W -> 2012 en
  adelante 10.000-30.000 W.
- Lastarria: 2003-2010 (7 filas sueltas, todas `class=0`) minimo 280.000-9.000.000 W -> 2012 en
  adelante 16.000-30.000 W.
- Isluga y Puyehue-Cordon Caulle: sin filas con coordenada matching antes de 2011-2012.

Coincide con la resolucion mas fina de VIIRS (375 m/750 m vs 1 km MODIS), que detecta focos mas chicos
con menos energia. Consistente con la seccion 4.1: es un cambio de capacidad instrumental, no
necesariamente evidencia de "otro algoritmo silencioso". Pero confirma, otra vez, que el archivo no es
uniforme en el tiempo.

### 4.3 `class` es persistentemente 0 en Llaima desde 2012, con VRP no despreciable

Llaima: 2012-2025 el campo `class` es `0` en el 100% de las filas salvo 3 de 16 en 2012 (`{'0':13,
'1':3}`), con VRP mediano de cientos de miles de vatios por anio, comparable en orden de magnitud a
Copahue o Isluga (que si tienen `class=1` mayoritario). El clasificador automatico de MIROVA trata la
anomalia persistente de Llaima como "no volcanica" (fumarolica/termal de fondo) de forma sistematica
desde hace 13 anios, mientras que localmente (`docs/project_llaima_thermal.md` referenciado en
`MEMORY.md`) VRP Chile la trata como senal termica real de interes. Esto no prueba reprocesado, pero
es una divergencia de criterio (automatico vs. lo que el operador chileno considera relevante) que hay
que tener presente si se usa `class` como filtro "ground truth" para Chile.

### 4.4 Cobertura 2025 desigual y con corte a mitad de anio en al menos 2 volcanes

Filas de 2025 por volcan y distribucion mensual (`03_salida.txt`):

| volcan | n 2025 | ultima fecha | patron |
|---|---|---|---|
| Laascar | 815 | 2025-12-31 | denso todo el anio (35-87/mes) |
| Isluga | 521 | 2025-12-31 | denso todo el anio (24-52/mes) |
| Puyehue-Cordon Caulle | 436 | 2025-12-31 | denso todo el anio (21-60/mes) |
| Lastarria | 456 | 2025-12-31 | denso todo el anio (28-45/mes) |
| Planchon-Peteroa | 295 | 2025-12-15 | denso, cae en dic (6 filas) |
| Copahue | 117 | 2025-12-17 | irregular, pico nov (35) |
| Chaiten | 109 | 2025-12-29 | irregular, bajo todo el anio |
| **Nevados de Chillan** | 109 | 2025-12-16 | **71 de 109 caen en febrero solo**; jun-dic con 1-6/mes |
| Llaima | 34 | 2025-12-13 | disperso, bajo todo el anio |
| **Villarrica** | **42** | 2025-12-29 | **30 de 42 caen en ene-abr; mayo-dic con 0-3/mes**, vs. 511 filas en 2024 |

Villarrica y Nevados de Chillan muestran una caida abrupta de densidad a mitad de 2025 que no se ve en
Lascar, Isluga, PCC o Lastarria (que mantienen densidad pareja los 12 meses). Dos lecturas posibles,
NO se puede elegir entre ellas con este CSV solo: (a) baja real de actividad termica visible en MIR
(plausible, MIROVA solo ve el lago de lava de Villarrica cuando esta expuesto), o (b) el archivo OSF
2025 para esos dos volcanes esta incompleto/con revision pendiente al momento del corte del snapshot
(consistente con la revision manual de la seccion 3.2, que toma tiempo y se hace por lotes, no en
NRT). No hay dato local para descartar (b): seria necesario un OSF mas nuevo o el propio scraper NRT
de Mirova-v1 sobre esos meses para contrastar densidad de pasadas reales vs. densidad publicada.

## 5. Conclusion operativa

**Para que SI sirve el OSF** (propiedades del algoritmo/sensor, no dependen de si una fila fue
retenida o removida en la revision manual):
- Validar la formula VRP = k*A*(Tot_Lmir_hot - Tot_Lmir_bk) y sus constantes (ya hecho en
  `docs/audit_s139/MAGNITUD_DESCOMPOSICION_OSF.md`, cumplimiento >99% con error <0,1%).
- `Tot_Lmir_bk` y `Npix` por pasada: son subproductos del calculo interno del algoritmo para las filas
  que SI quedaron en el archivo; no dependen de que la fila haya sobrevivido la revision manual de
  fuego/falsa alarma (esa revision decide "incluir o no la fila", no "recalcular Npix distinto").
  Utiles para calibrar area de pixel, geometria (SatZen/SatAzi) y comportamiento del fondo.
- Contexto de largo plazo por volcan (regimen termico, ordenes de magnitud tipicos) siempre que se
  filtre por sensor/anio (seccion 4.1-4.2) para no mezclar la era MODIS-solo con la era
  multi-sensor.

**Para que NO sirve el OSF:**
- Medir recall o precision del clon NRT (`mirova_equivalent`) contra "lo que MIROVA hubiera dicho en
  vivo": no hay overlap temporal con ninguna fuente NRT local (seccion 1), y aunque lo hubiera, el
  archivo esta supervisado a mano para remover fuegos y falsas alarmas (seccion 3.2; falso para la v2.5,
  ver la corrección S142 en §0: el filtro es por umbrales y clase automática): un FP real
  del feed NRT (el que VRP Chile busca reproducir) puede simplemente no estar en el OSF porque
  alguien ya lo borro despues del hecho. Comparar contra el OSF subestimaria sistematicamente los
  falsos positivos "esperables" de un clon fiel al NRT.
- Ground truth de recall/FN reciente: la cobertura 2025 esta incompleta para al menos 2 de los 11
  Tier A (Villarrica, Nevados de Chillan; seccion 4.4), asi que ni dentro del propio 2025 conviene
  tratar el archivo como completo para los meses mas recientes.
- Contraste pasada-por-pasada de VRP/distancia individual: sin dato posible hoy (seccion 2); el
  archivo hermano de TIFs recien empieza a acumular la ventana que en 2026-2027 permitiria hacerlo.

## 6. Que falto y por que

- No se pudo confirmar version anterior del OSF (v2.0 a v2.4) ni un changelog formal: no hay copia
  local de versiones previas del CSV/SQL, y no se busco online (fuera del alcance de lectura local
  pedido). El propio `schema_v25.md` no incluye historial de versiones.
- No se leyo el `.docx` original (`MIROVA_Database_Schema_v2.5.docx`) mas alla de la version ya
  extraida a markdown en `experiments/_s139_audit/eje6/schema_v25.md`; se asumio que esa extraccion
  es fiel (no se re-extrajo con markitdown en esta sesion).
