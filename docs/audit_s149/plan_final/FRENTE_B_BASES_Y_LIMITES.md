# S149, Frente B: bases de datos y sus límites

Fecha: 2026-09-21. Auditor del frente B. Sólo lectura sobre el repo; scripts y salidas en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s149_audit\frente_B\`.
Eje que estrena: conocimiento medido sobre las bases que no está donde se lee primero.

Bases medidas hoy: snapshot `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`
(38.677 filas, 2026-01-10 19:06 a 2026-09-21 12:50 UTC) y `registro_vrp_ocr.csv` (994 filas,
2026-01-20 a 2026-09-21 06:06); nuestra serie `data/mirova_equivalent/` de los 11 Tier A (60.247
records, 2025-02-15 a 2026-09-21); OSF `VRP_GLOBAL_ARCHIVE_2025.csv` (615.470 filas, última
2025-12-31); copia LOCAL de `../mirova-tif-archive` (sin pull). Noche: en M1 la definición de S139
(UTC antes de 10:42 o desde 22:42); en M3, M4 y M5 el predicado del pipeline
(`auto_audit_weekly.es_pasada_diurna_descartada`). Pareo: mismo volcán, mismo bucket, más o menos 120 s.

## 0. Resumen para quien decide

1. **La tabla `latest.php` no lista los tres satélites VIIRS por igual, y eso no estaba escrito en
   ningún lado.** NOAA-20: 81 a 93 % de nuestras pasadas nocturnas tienen fila todo el año. **NOAA-21:
   0 % hasta el 2026-04-08; la primera fila que parea es del 2026-04-09 05:00 UTC**; sube a 44 a 72 %
   entre abril y julio y recién llega a 90 a 96 % desde agosto. **Suomi NPP: 14 a 37 % todo el año**
   (23 % sobre 3.541 pasadas), sin tendencia. Esto explica el "salto de abril" que S139 dejó como
   SOSPECHA, y explica el hallazgo de hoy de que la tabla casi no lista SNPP (B-01, B-02).
2. **El canal OCR es, en los hechos, el canal de SNPP**: de las ALERTA_OCR de VIIRS 375 nocturnas sin
   fila de tabla, 206 de 287 (antes del 06-13) y 108 de 143 (después) parean con un record nuestro de
   SNPP. La regla A119 (a), "antes del 06-13 decide la tabla sola", equivale entonces a **sacar a SNPP de
   la evaluación**: ni positivo (su alerta vive en el OCR) ni negativo limpio (la tabla no lista la
   pasada). Un tercio de nuestros records VIIRS casi no tiene vara (B-02).
3. **El "86 % en enero, 95 % en febrero" de cobertura de la tabla es casi entero la ausencia de
   Tupungatito contada en el denominador**, que además ya es otro hito. Sin Tupungatito la cobertura es
   95,9 a 99,5 % en enero y 98,2 a 99,6 % en febrero. El hito del 2026-03-01 "tabla, todos" y el "enero no
   se usa" de A119 (b) están apoyados en una cifra deformada al resumirla (B-03).
4. `scripts/calidad_referencia_mirova.py` reproduce bien los hitos que declara (9 de 9 verificados),
   pero **le faltan seis límites documentados o medidos** (B-04) y cubre sólo la referencia: los límites de
   NUESTRA serie (hueco, #535, NRT contra estándar), del OSF y de los TIF no viven en ningún módulo
   consultable.
5. **Instrumentos vigentes que ignoran los límites**: `scripts/libro_de_cuentas.py` y
   `scripts/paper_numbers.py` abren la ventana el 2026-01-01 con CONS unión OCR, sin aviso, cruzando el
   hueco de nuestra serie (B-05); `banco_paridad.indexar_referencia` avisa pero sigue etiquetando
   positivo con el OCR en cualquier ventana (B-06); `frontend/diario.html` y `comparacion.html` dibujan
   sólo las alertas de la tabla, o sea sin 24 a 40 % de las alertas VIIRS 375 de MIROVA (B-07).

## 1. El mapa: qué base sirve, desde cuándo y para qué

| Base | Qué es | Sirve desde | Para qué sirve | Para qué NO sirve |
|---|---|---|---|---|
| Tabla (CONS), MODIS | una fila por gránulo que `latest.php` mostró | tipos actuales desde 2026-01-16; plano 1,96 a 2,12 filas por noche todo el año (M1) | positivos, negativos (RUTINA), magnitud | recall MODIS reciente: el loader trae 2, 2 y 1 alertas MODIS en julio, agosto y septiembre (M5): n no da para una tasa |
| Tabla, VIIRS de NOAA-20 | idem | 2026-01-16; 81 a 93 % de nuestras pasadas todo el año (M4) | es el ÚNICO satélite VIIRS con vara pareja todo 2026 | |
| Tabla, VIIRS de NOAA-21 | idem | **2026-04-09**; pareja con NOAA-20 recién desde **2026-08-01** (90 a 96 %) | desde agosto, todo | cualquier cosa antes del 04-09; tasas por pasada de abril a julio (44 a 86 %, inestable por quincena) |
| Tabla, VIIRS de SNPP | idem | nunca pareja: 14 a 37 % | las filas que lista sirven, pero están sesgadas al borde del barrido: 43 % de listado con cenit de 55 grados o más contra 7 a 12 % bajo 55 (M4c) | negativos limpios de SNPP; recall de SNPP contra la tabla |
| Tabla, Tupungatito | | filas desde 2026-02-14; límite de 7 km desde 2026-02-23 (M1: primera ALERTA entre 5 y 7 km el 02-23 05:00; antes, 5 FALSO_POSITIVO a 5,03 a 5,41 km) | | todo antes del 02-23 |
| OCR | alertas leídas de la imagen, casi todas VIIRS 375 (877 de 994 filas) y en su mayoría de SNPP | existe desde 2026-01-20; una sola versión y un solo método desde 2026-03-01; distancia medida desde 2026-06-13; geometría de observación desde 2026-08-06 | positivo adicional (24 a 40 % de las alertas VIIRS 375 del loader, M5) | negativos (no trae RUTINA); distancia antes del 06-13 (526 de 571 filas en 0 hasta mayo; las notas traen distancia medida con la geometría vieja); VRP de VIIRS 750 y MODIS (truncado a entero, S139 H111, no re-medido hoy) |
| Respaldo 2026-04-08 (`registro_vrp_consolidado_respaldo_20260408.csv`) | copia manual, 11.319 filas | enero a 08-abr | reponer 244 filas que el remoto perdió (17 alertas); lo une `scripts/referencia_mirova_unificada.py:11-14` | no repone lo perdido el 25-ago (ver B-04 punto 3) |
| `latest_consolidado.csv` (raíz) | copia horaria de la tabla | igual que la tabla | frontend | hereda las pérdidas; sin OCR |
| `data/mirova_reference/registro_vrp_ocr.csv` | OCR congelado 2026-03-28, 235 filas | | historia; notas sin mojibake | no lo lee ningún script vigente (grep en `scripts pipeline frontend .github tests`: sólo un comentario en `sync-mirova-csv.yml:16`) |
| Referencias congeladas de los A/B (`experiments/_s14x*/_dl_referencia/`) | descargas del remoto con sha | | reproducir un veredicto | están IGNORADAS por git (20 de 20 revisadas): existen sólo en este disco |
| OSF v2.5 | archivo filtrado y automático (A105) | 2000 a 2025-12-31 | magnitud pareada y esquema (una fila por pasada) sobre 2025; solapa con nuestra serie de 2025-02-15 a 2025-11-15 | NOAA-21 (códigos de satélite sólo 1 a 4, M6); conteos para el NRT (A105); VIIRS 750 y MODIS en 2025: en los 7 volcanes que mi filtro por nombre capturó hay 1.681 filas de 375 m contra 16 de 750 m y 18 de MODIS (M6; mi filtro perdió 4 volcanes con tilde, el total por volcán NO es válido, la proporción sí) |
| GeoTIFF de MIROVA | imagen por pasada | archivo desde 2026-05-09; UTM nativo sólo 8 adquisiciones del 14 y 15 de septiembre (A106, no re-verificado: la copia local termina el 2026-05-20) | ubicar un objeto; celda exacta sólo en la ventana UTM | no trae satélite; en la copia local 1.263 de 2.684 filas comparten md5 con otra (imagen vuelta a servir) y 407 no traen hora de adquisición (M7) |
| KMZ y límites oficiales | `kmz/*.kmz`, `inner_radius_km` | | el límite que aplica el scraper coincide con `volcanoes.yaml` en los 11 (M8) | |
| Nuestra serie | `data/mirova_equivalent/` | 2025-02-15 | | hueco 2025-11-15 a 2026-01-29 en 9 volcanes, 2025-10-09 a 2026-01-29 en PCC, sólo Villarrica continuo (M2a, coincide con CLAUDE.md); cambio de régimen 2026-08-28 (A104, no re-medido); records `nrt`: 0 % hasta junio, 2 a 3 % en julio y agosto, 17,3 % en septiembre (MODIS 31,7 %) (M2c) |

## 2. Hallazgos, por gravedad

### B-01. NOAA-21 no existe en la tabla de MIROVA antes del 2026-04-09 y no queda parejo hasta agosto
- **SCRIPT:SALIDA** `m2_m3_serie_propia_y_satelite.py` (`salida_m2_m3.txt`, tabla M3) y `m4_snpp_noaa21.py` (`salida_m4.txt`, bloque b).
- **QUÉ PASA** MIROVA empezó a listar en `latest.php` las pasadas del tercer satélite VIIRS en abril. De
  nuestras pasadas nocturnas VIIRS 375 de NOAA-21, tienen fila en la tabla 0 de 78, 0 de 434 y 0 de 491 en
  enero, febrero y marzo; 56 % en abril (primera: 2026-04-09 05:00 UTC), 55, 64 y 74 % de mayo a julio,
  92 y 95 % en agosto y septiembre. En VIIRS 750 igual (0, 0, 0, 81, 69, 79, 68, 92, 91 %). Es la causa del
  salto de gránulos por noche que S139 midió y dejó como SOSPECHA "por ejemplo otro satélite"
  (`docs/audit_s139/MAPA_BASES_MIROVA_V1.md:106-108`) y que el hito del 2026-04-01 de
  `scripts/calidad_referencia_mirova.py:24` describe sin causa ni fecha exacta. Y el segundo escalón (2,3 a
  2,6 filas por noche hasta julio, 3,0 a 3,4 desde agosto) es NOAA-21 llegando a paridad, que el módulo no
  tiene como hito.
- **Consecuencia** Una ventana de abril a julio tiene una vara que cambia de quincena en quincena para un
  tercio de las pasadas (44, 68, 62, 49, 57, 72, 86, 62 %). La composición de los negativos limpios VIIRS
  375 por satélite pasa de 80 % NOAA-20 en febrero y marzo a 52, 33 y 14 % en mayo y 42, 43 y 15 % en
  septiembre (M3b). Una comparación mayo contra septiembre no compara la misma mezcla de satélites.
- **CÓMO SE VE EN EL DASHBOARD** Invisible. Se ve en todo A/B o línea base por pasada.
- **CÓMO REPRODUCIRLO** `python experiments/_s149_audit/frente_B/m4_snpp_noaa21.py`
- **CONTROL** NOAA-20 da 85 a 93 % con el mismo pareo; la tabla desplazada 30 min da 0 % en NOAA-20, SNPP y
  MODIS. En NOAA-21 el control desplazado da 22 a 1 %: es fase orbital (la pasada de otro satélite cae cerca
  de los 30 min), no invalida el 0 % sin desplazar.
- **CONFIANZA** CONFIRMADO (tasas y fecha). Que sea una decisión de MIROVA y no de la tabla: SOSPECHA.
- **GRAVEDAD 4** No tuerce una alerta; tuerce toda meta por sensor que se proponga con ventanas anteriores a agosto.

### B-02. La tabla lista sólo 23 % de las pasadas de Suomi NPP, todo el año, sesgadas al borde del barrido; el OCR es el canal de SNPP
- **SCRIPT:SALIDA** `m4_snpp_noaa21.py` bloques a, c y d.
- **QUÉ PASA** No es un desfase del pareo: para las pasadas SNPP sin fila, la fila de tabla más cercana
  está a 8 a 20 min en 49 % y a 20 a 40 min en 22 % (es la pasada de otro satélite), contra 87 % a menos
  de 2 min en NOAA-20. No depende del volcán (21 a 27 % en los 11). Sí depende del cenit: 43 % de listado
  con 55 grados o más (n 1.423), 7 a 12 % bajo 55 (n 2.079); en NOAA-20 el listado es plano (85 a 89 %).
  Cuando la tabla sí lista SNPP, 95 de 828 filas son ALERTA (11,5 %) contra 646 de 3.263 en NOAA-20
  (19,8 %). MIROVA sí procesa SNPP: en el OSF de 2025 SNPP y NOAA-20 aparecen parejos (806 contra 871
  filas nocturnas de 375 m, M6), y sus alertas aparecen en las imágenes (por eso el OCR las captura).
  Hipótesis de causa (SOSPECHA, no probada): la tabla muestra un cupo de filas por volcán y la pasada de
  SNPP queda desplazada por la de NOAA-21 o NOAA-20 vecina, salvo cuando SNPP pasa lejos en el barrido.
- **Consecuencia** (1) 77 % de nuestros records nocturnos SNPP cae en "sin información" en el banco: no
  puede ser negativo limpio. (2) Sus alertas viven en el OCR: 314 de 430 ALERTA_OCR VIIRS 375 sin fila de
  tabla son SNPP. (3) A119 (a) en ventanas anteriores al 06-13 deja a SNPP sin positivos. (4) La muestra
  SNPP que sí entra está sesgada a cenit alto, que es justo el estrato donde S147 encontró el residual
  de sobre-publicación (borde del barrido con fondo frío).
- **CÓMO SE VE EN EL DASHBOARD** En `diario.html` una alerta de MIROVA vista por SNPP no tiene punto MIROVA (ver B-07).
- **CONFIANZA** CONFIRMADO (tasas, cenit, reparto del OCR). Causa: SOSPECHA.
- **GRAVEDAD 4**

### B-03. El "86 % enero, 95 % febrero" de cobertura de la tabla es la ausencia de Tupungatito en el denominador
- **ARCHIVO:LÍNEA** `scripts/calidad_referencia_mirova.py:22`; `CLAUDE.md:1492-1493` y `:1501` ("enero no se usa"); origen `docs/audit_s139/MAPA_BASES_MIROVA_V1.md:92-93`. **SCRIPT** `m1b_cobertura_sin_tupungatito.py`.
- **QUÉ PASA** Con noches calendario desde el 2026-01-10: enero con Tupungatito en el denominador 90,1 /
  87,2 / 90,5 % (MODIS / VIIRS 750 / VIIRS 375), sin él 99,1 / 95,9 / 99,5 %; febrero 94,5 / 95,8 / 95,5 %
  contra 98,2 / 99,6 / 99,3 %. No hay ninguna noche de enero a marzo sin filas, ni noche de enero con
  menos de 8 de 10 volcanes en MODIS. No reproduje el 86,0 exacto de S139 (su denominador no está
  descrito), pero mi tabla M1 por 99,0 x 210 / 242 da 85,9: es el mismo efecto. El módulo cuenta el mismo
  defecto dos veces (hitos 02-14 y 03-01) y la regla lo resume como un problema de "todos".
- **Lo que SÍ es cierto de enero** tipos viejos hasta el 01-15 (primer FALSO_POSITIVO 2026-01-15 17:54;
  17 RUTINA con VRP mayor que 0, la última el 01-14), scraper en desarrollo hasta el 01-19 (heredado de
  S139, no re-medido), y sobre todo que NUESTRA serie no existe hasta el 01-29 salvo Villarrica.
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 2** El error es conservador (descarta datos buenos de 10 volcanes), pero es exactamente la clase "deformado al resumir".

### B-04. Límites documentados o medidos que `calidad_referencia_mirova.py` no tiene
- **ARCHIVO:LÍNEA** `scripts/calidad_referencia_mirova.py:18-28` (HITOS) y `:32-34`.
- Verificados los 9 hitos que declara (M1): todos se reproducen. Faltan:
  1. **2026-04-09** NOAA-21 entra a la tabla y **2026-08-01** llega a paridad (B-01). Nuevo.
  2. **SNPP sub-listado todo el año** (B-02). Nuevo. No es un hito con fecha: es un límite permanente.
  3. **Filas perdidas del remoto antes del 2026-08-29**: 31 alertas (`MAPA_BASES_MIROVA_V1.md:20-25`). La
     unión con el respaldo repone 17 (`referencia_mirova_unificada.py:11-14`). Las otras 14 (perdidas el
     25-ago, de abril a agosto) no vi que ningún módulo las reponga: SIN VERIFICAR (requiere bajar
     `cons_2026-08-22` del remoto). Hoy medí dos de ellas: Láscar MODIS nocturno 2026-03-04 07:15 y
     2026-03-19 01:55 existen sólo como ALERTA_OCR (M1b), lo que contradice el "0 alertas MODIS dependen
     del OCR" de `CLAUDE.md:1494` (son 2 nocturnas y 1 diurna; el loader las cuenta, M5: MODIS 7 % solo-OCR
     en marzo y mayo).
  4. **VRP de 1.000 MW o más aborta el ciclo del scraper** (`MAPA_BASES_MIROVA_V1.md:26-28`): re-medido, 0
     filas con VRP de 1.000 o más en la tabla, máximo 347,13. Es el escenario de la erupción mayor.
  5. **2026-06-15** reclasificación a mano de 49 filas del OCR y 23 automáticas (heredado, no re-medido).
  6. **La ventana de `avisos_de_ventana` ignora `hasta`** (`:34`, sólo `desde < f`): una ventana del
     2026-07-01 al 2026-07-31 recibe el aviso del cambio de versión del 08-06, que no pisa. Inofensivo, pero
     un aviso que suena siempre se deja de leer.
  7. Matiz al hito del 06-13: hay 51 filas OCR anteriores con `Distancia_km` mayor que 0 (la primera del
     2026-02-27), reescritas por la reconciliación; "0 fijo antes del 06-13" no es literal.
- **CONFIANZA** CONFIRMADO salvo lo rotulado. **GRAVEDAD 3**

### B-05. El libro de cuentas y los números del manuscrito abren la ventana el 2026-01-01, sin aviso, sobre el hueco de nuestra serie
- **ARCHIVO:LÍNEA** `scripts/libro_de_cuentas.py:72` y `:160` (`cargar_mirova(("2026-01-01", "2026-12-31"))`); `experiments/_s126_lib.py:68-69` (fuentes: `latest_consolidado.csv` más el OCR del snapshot) y `:139` (noche = hora UTC entre 3 y 9, otra definición); `scripts/paper_numbers.py:322` (`--desde` por defecto 2026-01-01) y `:188` (`load_mirova_alertas`, CONS unión OCR). Ninguno llama a `calidad_referencia_mirova` (grep: sólo `banco_paridad.py:206` y `medir_predicciones.py:96`).
- **QUÉ PASA** Entre el 2026-01-10 y el 01-28 MIROVA publica alertas y nosotros no tenemos ningún record
  en 10 de 11 volcanes. Esas noches entran al denominador del recall como pérdidas. Medido (M5): 13 de
  264 noches-alerta de VIIRS 750 (4,9 %), 43 de 974 de VIIRS 375 (4,4 %), 2 de 83 de MODIS (2,4 %). El
  `recall_v750_dash` del libro (85,06 citado en `CLAUDE.md` A90) tiene entonces un techo de 95,1 % por este
  solo efecto y está subestimado hasta en unos 4 puntos. Además mezcla OCR de enero y febrero (7 versiones)
  como positivo, y dos definiciones de noche distintas de la del banco.
- **CÓMO SE VE EN EL DASHBOARD** Invisible; se ve en el manuscrito y en toda cifra del libro.
- **CÓMO REPRODUCIRLO** `python experiments/_s149_audit/frente_B/m5_loader_y_hueco_enero.py`
- **CONFIANZA** CONFIRMADO (mecanismo y tamaño del denominador). No corrí el libro: el tamaño exacto del sesgo sobre 85,06 es SOSPECHA.
- **GRAVEDAD 3**

### B-06. El aviso de A119 avisa pero no decide: `banco_paridad` sigue etiquetando positivo con el OCR en cualquier ventana, y el loader canónico entrega distancias medidas con la geometría vieja
- **ARCHIVO:LÍNEA** `scripts/banco_paridad.py:209` (sólo imprime) y `:290` (`pos` con cualquier ALERTA, CONS u OCR); `pipeline/mirova_csv_loader.py:91` (desde S139 el regex acepta el mojibake) y `:169`; `scripts/auto_audit_weekly.py:271`.
- **QUÉ PASA** `etiqueta_que_decide` sólo la usa `experiments/_s149_prereg_invierno/medir_predicciones.py:94-98`
  (que sí separa "con la tabla sola"). El banco, el auto-audit semanal y todo script de `experiments/` que
  pase por el banco siguen contando el OCR como positivo antes del 06-13. Y el arreglo del mojibake de S139
  devolvió la distancia a 351 de 351 ALERTA_OCR de marzo al 10 de junio (M5, mediana 2,76 km contra 1,29
  desde el 06-13), distancias que S139 mismo dice que no valen (`MAPA_BASES_MIROVA_V1.md:233`, infladas
  cerca de 2 veces). El loader tampoco filtra por confianza (27 ALERTA_OCR con confianza media o baja).
  Además `experiments/_s149_prereg_invierno/evaluar_ventana.py:53` llama a `armar_tabla.py` con
  `stderr=subprocess.DEVNULL`, que es justo donde sale el aviso.
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 3** El auto-audit semanal usa ventana de 60 días (hoy desde fines de julio), así que hoy no pisa; cualquier re-medición histórica sí.

### B-07. El tablero dibuja sólo las alertas de la tabla: faltan 24 a 40 % de las alertas VIIRS 375 de MIROVA, en su mayoría de SNPP
- **ARCHIVO:LÍNEA** `frontend/diario.html:193-206` y `frontend/comparacion.html:170-180` (`Tipo_Registro !== "ALERTA_TERMICA"` se descarta; el OCR no se carga).
- **QUÉ PASA** Fracción de alertas del loader que viene sólo del OCR, VIIRS 375: 22, 19, 39, 30, 40, 36, 24,
  28 y 24 % de enero a septiembre (M5); VIIRS 750: 5 a 8 % salvo marzo (37 %) y abril (22 %).
- **CÓMO SE VE EN EL DASHBOARD** Una detección nuestra de SNPP en una noche en que MIROVA alertó por esa misma pasada aparece como "sólo nosotros". Conocido en S139 (eje 1 H105, citado en `MAPA_BASES_MIROVA_V1.md:229`); lo nuevo es el tamaño por mes y que es SNPP.
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 3**

### B-08. La base de alertas es chica y muy desigual por volcán y por sensor
- **SCRIPT** `salida_m8_limites.txt`, `salida_m5.txt`. Alertas de la tabla desde el 2026-03-01: Láscar 398, Isluga 236, PCC 187, Tupungatito 152, Lastarria 145, Planchón Peteroa 92, Chaitén 41, Villarrica 29, Nevados de Chillán 17, Copahue 5, **Llaima 1**. MODIS: 97 alertas en todo 2026, 5 desde julio.
- **Consecuencia** Una meta de recall "por sensor" agregada es una meta de Láscar e Isluga; en MODIS después de #535 no hay n para medir nada. **CONFIRMADO. GRAVEDAD 3** (para el diseño de metas del frente C).

### B-09. Las referencias congeladas de los A/B viven sólo en este disco
- 20 de 20 copias `_dl_referencia/*.csv` revisadas están ignoradas por git. Si guardan el sha del remoto se pueden volver a bajar (no verifiqué cada una: SIN VERIFICAR). **GRAVEDAD 2**

### B-10. La copia local de `mirova-tif-archive` termina el 2026-05-20
- `git log -1` del repo hermano: 2026-05-20; `index.csv` 2026-05-09 a 2026-05-20, con `poll.yml` modificado sin commitear. Todo lo que CLAUDE.md afirma de los TIF de septiembre (A106) no se puede verificar en local, y por regla no se le hace pull. **CONFIRMADO. GRAVEDAD 1** (informativo: leer por la API).

## 3. Cifras citadas como vigentes y el tramo sobre el que se calcularon

| Cifra | Dónde | Tramo | Veredicto |
|---|---|---|---|
| `recall_v750_dash` 85,06 | `CLAUDE.md` A90, `libro_de_cuentas.py:148-190` | 2026-01-01 en adelante, CONS unión OCR | cruza el hueco de nuestra serie y el OCR inestable (B-05) |
| 89,1 % de 4.800 contra 93,7 % de 158 (A82, MODIS) | `CLAUDE.md` A82 | 2026-01-29 a 2026-08-28 | MODIS es plano y la ventana parte donde parte nuestra serie: **limpio** en lo que toca a este frente |
| 84,5 contra 62,1 (I-band) y 47,5 contra 22,8 (M-band) | `CLAUDE.md` A82 | misma ventana | mezcla tres vara distintas para VIIRS (sin NOAA-21 hasta abril, parcial hasta julio) y SNPP casi sin negativos: SOSPECHA de sesgo de composición, no medido |
| 62,1 % a 87,1 % (A104) | `CLAUDE.md` A104, `auto_audit_weekly.py:56` | antes y después del 2026-08-28 | el "antes" incluye de abril a julio con NOAA-21 a medio listar; la mezcla de satélites de julio a septiembre cambia poco (M3b: 50/44/7 a 42/43/15), así que el confusor es chico: SOSPECHA |
| 874 de 877 noches (A98) | `docs/audit_s139/EJE_2_banco_todos_los_datos.md:74` | no leí la ventana | SIN VERIFICAR |
| 1.512 y 1.609 pares de magnitud (A10) | `CLAUDE.md` A10 | no leí la ventana | SIN VERIFICAR; la magnitud de la tabla no tiene defecto por tramo conocido, el riesgo sería sólo VRP del OCR truncado |
| D2 cobertura del CSV 79,2 % | `docs/MIROVA_DIVERGENCES.md:44` | S128 | SIN VERIFICAR; con B-01 y B-02 esa cobertura es muy distinta por satélite y conviene re-expresarla así |

## 4. Restricciones que todo análisis del plan final debe respetar

1. **Toda tasa VIIRS se reporta por satélite** (SNPP, NOAA-20, NOAA-21), además de por sensor. Si no se puede, se declara la mezcla de satélites de la ventana.
2. **NOAA-21 no tiene vara antes del 2026-04-09 y no la tiene pareja antes del 2026-08-01.** Para metas por sensor con los tres satélites, la ventana parte el 2026-08-01; si además se exige régimen único (#535), parte el 2026-08-29.
3. **SNPP no tiene negativos limpios representativos en ninguna fecha.** Su recall sólo se puede medir contra el OCR, que sirve con distancia desde el 2026-06-13. No proponer una meta de "callar donde MIROVA calla" para SNPP apoyada en la tabla.
4. **NOAA-20 es el único satélite VIIRS comparable de enero a septiembre.** Cualquier comparación entre estaciones (invierno contra primavera, mayo contra septiembre) se hace primero sólo con NOAA-20.
5. **MODIS**: la tabla es plana y completa desde el 2026-01-16, pero hay 5 alertas desde julio. Metas de recall MODIS sólo sobre marzo a junio, o no hay meta.
6. **Ventana mínima por nuestro lado**: 2026-01-29 (2025-02-15 a 2025-11-15 sólo contra el OSF). Nunca 2026-01-01.
7. **Enero y febrero**: el problema no es la cobertura de la tabla (B-03) sino nuestro hueco, los tipos hasta el 01-15, Tupungatito hasta el 02-23 y el OCR inestable. Desde el 2026-02-23, tabla sola y NOAA-20, MODIS sirve.
8. **OCR**: positivo adicional desde el 2026-03-01; con distancia sólo desde el 2026-06-13; nunca negativo; la distancia parseada de notas anteriores al 06-11 no se usa aunque el loader la entregue.
9. **Por volcán**: reportar siempre n de alertas; Llaima (1), Copahue (5) y Nevados de Chillán (17) no sostienen una tasa.
10. **OSF**: sin NOAA-21, casi sin 750 m ni MODIS en 2025, filtrado (A105). Sirve para magnitud pareada de 375 m de SNPP y NOAA-20 en 2025.
11. **Referencia = remoto del dueño con sha**, unida al respaldo del 08-abr; declarar que 14 alertas perdidas en agosto siguen sin reponer hasta que alguien lo verifique.
12. Todo script que lea los CSV llama a `calidad_referencia_mirova.avisar` y **no manda stderr a DEVNULL**.

## 5. Para otros frentes (sin desarrollar)

- **Frente C**: B-01, B-02 y B-08 cambian cómo se proponen metas por sensor (por satélite; n por volcán). La "variabilidad de MIROVA contra sí misma" entre satélites se puede medir con `m4_snpp_noaa21.py` bloque c (tasa de alerta 11,5 % SNPP contra 19,8 % NOAA-20 en las filas listadas).
- **Frente D**: todo veredicto VIIRS con ventana anterior al 2026-08-01 se decidió con NOAA-21 a medio listar y SNPP sin negativos. El residual de S147 "en el borde del barrido" conviene releerlo sabiendo que la tabla lista SNPP sobre todo en el borde (`salida_m4.txt` bloque c).
- **Frente A**: `CLAUDE.md:1494` "0 alertas MODIS dependen del OCR" es falso por 2 nocturnas; `CLAUDE.md:1492` "86 % en enero" es Tupungatito.
- **Frente G**: `frontend/diario.html:206` sin OCR (B-07); records `nrt` 17,3 % en septiembre contra 0 a 3 % antes (`salida_m2_m3.txt` M2c): o el auto-upgrade a estándar va atrasado o cambió algo; no lo seguí.

## 6. SIN VERIFICAR (dicho en voz alta)

- Las 14 alertas perdidas el 25-ago: si alguna copia las repone. Requiere red.
- La causa del sub-listado de SNPP y si NOAA-21 entró por decisión de MIROVA o de la tabla.
- Si el cambio de régimen #535 (A104) está confundido por composición de satélites: sólo medí la composición, no la tasa de publicación por satélite (requiere node y es del frente C).
- A106 (ventana UTM de los TIF) y todo lo de TIF posterior al 2026-05-20.
- Totales por volcán del OSF (mi filtro por nombre perdió los 4 volcanes con tilde; S139 da 48.360 filas en 10 volcanes y no lo repetí).
- Truncado a entero del VRP del OCR en VIIRS 750 y MODIS (S139 H111).
- Las ventanas exactas de A98 y A10.

## 7. VERIFICADO LIMPIO

| Qué | Resultado | Comando |
|---|---|---|
| Los 9 hitos de `calidad_referencia_mirova.py` contra el snapshot de hoy | se reproducen: primer FALSO_POSITIVO 01-15 17:54 y 17 RUTINA con VRP mayor que 0 hasta el 01-14; Tupungatito desde 02-14 06:06; primera ALERTA entre 5 y 7 km el 02-23; OCR con 4 versiones y 11 métodos en febrero, 1 y 1 desde marzo; razón OCR a tabla 0,26 y 0,29 contra 0,49 a 0,89; gránulos VIIRS por noche 1,59 a 1,77 hasta marzo, 2,3 a 2,6 abril a julio, 3,0 a 3,2 agosto y septiembre; MODIS plano 1,96 a 2,12; mojibake hasta proceso 2026-06-12 12:01; primera versión 30.0 el 2026-08-06 | `python experiments/_s149_audit/frente_B/m1_hitos_referencia.py` (control: borrar 50 % de junio baja la cobertura de 100 a 74 a 82 %) |
| Hueco de nuestra serie | 2025-11-15 a 2026-01-29 en 9 volcanes, 2025-10-09 a 2026-01-29 en PCC, Villarrica continuo; ningún sensor con hueco de más de 10 días en el agregado | `m2_m3_serie_propia_y_satelite.py` M2a y M2b |
| Etiqueta `product_version` contra el nombre del gránulo | 0 contradicciones en 60.247 records (los 593 `nrt` tienen gránulo NRT, ningún estándar lo tiene) | idem M2c |
| Límite de alerta del scraper contra `inner_radius_km` | coherente en los 11 (máxima distancia de ALERTA menor o igual al radio, mínima de FALSO_POSITIVO mayor); control Tupungatito antes del 02-23 da 4,89 y 5,03 | bloque M8 (`salida_m8_limites.txt`) |
| Pareo a más o menos 120 s | no está roto: NOAA-20 85 a 93 %, MODIS 85 a 97 %; desplazado 30 min da 0 % | M3 y su control |
| Snapshot y `latest_consolidado.csv` frescos | sync 2026-09-21 14:06 UTC (`c7110374f`) y snapshot 2026-09-21 15:44 UTC (`1b0ca24f5`) | `git log -1 -- <archivo>` |
| `data/mirova_reference/registro_vrp_ocr.csv` congelado | no lo lee ningún script vigente | `grep -rn "mirova_reference/registro_vrp_ocr" scripts pipeline frontend .github tests` |
| 0 filas con VRP de 1.000 MW o más en la tabla | máximo 347,13 | M1 última línea |
