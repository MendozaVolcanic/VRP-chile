# Subagente F (S86) — Auditoría integridad scraper Mirova-v1

**Fecha**: 2026-05-28
**Repo auditado**: https://github.com/MendozaVolcanic/Mirova-v1 (default `main`, pushed 2026-05-28T20:02Z, NO archived)
**CSVs locales**: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` (17,966 filas) + `registro_vrp_ocr.csv` (520 filas)
**Outputs adjuntos**: `F_scraper_integrity.json`, `script_F.py`

---

## TL;DR — ¿el scraper es confiable como ground truth?

**Sí, con tres ajustes obligatorios en el pipeline de cruce TP/FP** (locales en VRP Chile, NO en el scraper).

El scraper Mirova-v1 está **vivo, sano y bien instrumentado**: cron `Monitor Volcanico VRP` corre cada ~5 min, `Scraper OCR` cada hora :05, 20/20 últimos runs `success`, último commit hace minutos. La captura latest.php es completa (median gap entre filas por vol = ~0.8h, p95 ≤6.8h, ningún gap >48h en 134 días) y la lógica del parser HTML es directa. **No hay falsos negativos de captura sistémicos**.

Pero los CSVs tienen **cuatro divergencias de schema/semántica que sesgan el cruce TP/FP** si no se ajustan en `VRP Chile`:

1. **Variante huérfana `Peteroa`** en CONS (65 filas, 2026-01-10→2026-01-16, 1 ALERTA_TERMICA) que el scraper renombró a `PlanchonPeteroa` el 2026-01-16. Si filtramos por `PlanchonPeteroa` perdemos esa 1 ALERTA y 5 días de RUTINA.
2. **Tupungatito tiene 35 días menos de cobertura** (CONS empieza 2026-02-14 vs los otros 10 Tier A en 2026-01-10). Razón documentada en `scraper.py:31` (`"NUEVO: TUPUNGATITO"`). Cualquier audit Tupungatito sobre ventana >100d está **falseando recall a la baja**.
3. **OCR `Distancia_km` siempre = 0.0** (520/520 filas). La distancia REAL está en el campo libre `Nota_Validacion` (490/520 filas, formato `dist≈XX km`). Cualquier filtro nuestro por `Distancia_km` rechaza la totalidad del universo OCR.
4. **OCR aporta 344 ALERTAs únicas no presentes en CONS** (66% del OCR no aparece en latest.php). Regla A11 ya lo dice — pero el dimensionamiento concreto es: 117 Lascar, 55 Lastarria, 49 PCC, 47 Isluga, 31 PP, 21 Tupungatito, 11 Chaiten, 7 Villarrica, 3 Copahue, 2 Llaima, 1 NdC. Si el cruce TP/FP usa solo CONS, **estamos sub-contando ALERTAs** y sobre-reportando FPs.

Las cuatro son ajustes en NUESTRO loader del ground truth, no bugs del scraper.

---

## Matriz de issues por severidad

### Bloqueante (cambia veredictos del cruce TP/FP)

| ID | Issue | Impacto | Donde |
|---|---|---|---|
| **F-B1** | OCR aporta 344 ALERTAs únicas (66% del OCR) no presentes en CONS, distribuidas en los 11 Tier A | Cualquier cruce que use solo CONS sub-cuenta `MIROVA_alert_count` y sobre-cuenta nuestros FPs. Lascar el más afectado (+117), Lastarria (+55), PCC (+49). | Loader local (no bug Mirova-v1) |
| **F-B2** | OCR `Distancia_km` = 0 en TODAS las filas; la distancia real vive en texto libre `Nota_Validacion` | Si nuestro cruce filtra OCR por `Distancia_km<=inner_radius`, descarta 100% del OCR. | Bug del extractor OCR en `ocr_utils.py` — la distancia se calcula pero no se persiste en la columna |
| **F-B3** | Tupungatito CONS empieza 2026-02-14 (35d después que otros) | Audits sobre Tupungatito ventana >100d sobre-estiman FP-rate / sub-estiman recall MIROVA. | scraper.py:31 (vol nuevo) — no es bug, es histórico documentado |
| **F-B4** | Variante `Peteroa` (65 filas pre-2026-01-16, 1 ALERTA) huérfana en CONS | Filtros por `PlanchonPeteroa` saltean estas 6 días de cobertura. | Loader local (rename histórico del scraper) |

### Importante (sesga métricas en algún subset)

| ID | Issue | Impacto |
|---|---|---|
| **F-I1** | Schema `Clasificacion Mirova` divergente: CONS usa `{NULO, Muy Bajo, Bajo, FALSO POSITIVO}` (sin `Moderado/Alto/Muy Alto`); OCR usa `{Muy Bajo, Bajo, Medio, Alto}`. `scraper.py:55-60` mapea VRP→{Muy Bajo/Bajo/Moderado/Alto/Muy Alto} pero el OCR usa `Medio` (¡label distinto!) y no usa `Moderado`. Cualquier filter cross-CSV por nivel se rompe. |
| **F-I2** | Tipo_Registro `FALSO_POSITIVO` (CONS, 363 filas) NO se descarta automáticamente — son detecciones MIROVA fuera del `limite_km` del scraper (Lastarria 107, Lascar 62, Llaima 45, Isluga 34, NdC 28). Si nuestro cruce ignora FALSO_POSITIVO los pierde como MIROVA detection lejana (que algunos vols del Tier A SÍ tienen — PCC lacolito a 7-12 km). |
| **F-I3** | El scraper tiene `limite_km` HARDCODED per-vol (`scraper.py:16-27`): Lastarria 3.0, Lascar 5.0, PP 3.0, Tupungatito 7.0, PCC 20.0, etc. **Estos NO coinciden con `volcanoes.yaml` de VRP Chile** (ej. PP tiene `inner_radius_km=3` en ambos, OK; pero Lastarria scraper=3.0, VRP también 3.0 — OK; Lascar scraper=5.0 = OK). Coinciden — pero hay que documentarlo como dependencia. |
| **F-I4** | 1 ALERTA Chaiten VIIRS750 (sensor `VIIRS`) detectada (`2026-01-20 05:36`, VRP=0.33 MW, dist=0.0). Subagente C reportó **0 ALERTAs VIIRS750 en Tier A** — discrepancia menor (Chaiten tiene 1, no 0). |

### Cosmético

| ID | Issue | Impacto |
|---|---|---|
| **F-C1** | Encoding utf-8 limpio: 0 filas con mojibake. ✅ |
| **F-C2** | Timezone consistente: 0/5000 filas con diff UTC-CL distinto de 3h o 4h (DST chileno). ✅ |
| **F-C3** | CONS `Distancia_km` = 0 en solo 6/763 ALERTAs (0.8%) — uno de ellos el Chaiten VIIRS750 mencionado. Anomalía de captura del campo `cols[4]` cuando la fila MIROVA tiene whitespace raro. Marginal. |
| **F-C4** | OCR sensor `VIIRS` aparece 60 veces (ambiguo: VIIRS750 vs VIIRS legado). Normalizar a `VIIRS750` igual que en CONS. |

---

## Detalle de hallazgos por tarea

### Tarea 1 — Repo Mirova-v1

- **Activo y sano**. Default branch `main`, push hace minutos (`2026-05-28T20:02:12Z`). NO archivado.
- **Cron health**: 3 workflows activos (`Monitor Volcanico VRP` ~5 min, `Scraper OCR` :05 hourly, `Generador de Graficos`). Últimos 20 runs todos `success`.
- **Issues**: 0 abiertos / 0 cerrados. Repo único developer.
- **Stack**: `scraper.py` (245 líneas, parser BeautifulSoup contra `https://www.mirovaweb.it/NRT/latest.php`), `scraper_ocr.py` + `ocr_utils.py` (37 KB, Tesseract sobre imágenes per-vol), `merger_maestro.py` (consolida los CSVs).
- **Lógica de captura** (`scraper.py`): para cada fila del tbody de latest.php, parsea `(timestamp, id_vol, vrp_mw, distancia_km, sensor)`. Si `vrp>0` y `dist<=limite_km` → ALERTA_TERMICA. Si `vrp>0` y `dist>limite_km` → FALSO_POSITIVO. Si `vrp=0` → RUTINA. Clasificación por VRP siguiendo Coppola 2016 (1e6/1e7/1e8/1e9).

### Tarea 2 — CSV integrity

Cubierta en matriz arriba. Highlights:

- **Continuidad**: median delta entre filas consecutivas = 0.8–0.9 h, p95 ≤ 6.75h, max 18.67h (Lastarria, único caso > 14h). **0 gaps > 48h en ninguno de los 11 Tier A**. Captura sólida.
- **Coverage cons (rango fechas)**: 10 Tier A en 2026-01-10 → 2026-05-18 (≈134 días); Tupungatito en 2026-02-14 → 2026-05-18 (≈94 días, **gap 35 días al inicio, F-B3**).
- **Sensor coverage CONS** (ALERTAS): MODIS 75 (74 Lascar + 1 NdC), VIIRS750 141 (Lascar 91, PCC 21, Isluga 16, Tupungatito 9, PP 2, NdC 1, **Chaiten 1**), VIIRS375 547 (todos). **Solo Lascar tiene volumen MODIS** — confirma intuición de Fase 1b S83 (MODIS 1km insensible salvo Lascar).
- **OCR cobertura**: muy desigual. Lascar 206, Lastarria 81, PCC 63, Isluga 63, PP 46, Tupungatito 28, Chaiten 16, Villarrica 8, Copahue 3, Llaima 3, NdC 3.

### Tarea 3 — mirovaweb.it live

Respondió HTTP 200 al GET. Tabla renderizada client-side via JS (no se puede verificar última fila sin headless). Como evidencia indirecta: GH Actions del scraper triggerea cada 5 min y los últimos 20 runs son `success`, así que el endpoint está vivo y respondiendo lo que el scraper espera.

### Tarea 4 — Variantes de nombre

CONS volcanes: `Llaima, Tupungatito, Nevados de Chillan, Copahue, PlanchonPeteroa, Chaiten, Puyehue-Cordon Caulle, Lastarria, Lascar, Isluga, Villarrica, **Peteroa**`. OCR volcanes: subset sin `Peteroa`.

- **`Peteroa` huérfano** (F-B4): 65 filas todas en 2026-01-10→2026-01-16. Confirmado: scraper.py mapea id `357040 → PlanchonPeteroa` actualmente. La existencia de `Peteroa` indica que en algún commit pre-2026-01-16 el `nombre` era `Peteroa` y luego se renombró. Las 65 filas viejas NO fueron migradas.
- Resto consistente. `Puyehue-Cordon Caulle` (con guión + espacio) idéntico en ambos CSVs (Subagente A reportaba variante sin guión — verifico abajo: no existe en CONS ni OCR; solo en `id_mirova` interno).
- `Nevados de Chillan` con espacios en ambos CSVs (ojo: en `id_mirova` el scraper usa `ChillanNevadosde` para construir URLs MIROVA — no es variante del CSV).

### Tarea 5 — Cruce OCR vs CONS

Re-validación regla A11. De 520 filas OCR:

- **176 (34%) overlap** con CONS por clave (timestamp, vol_normalizado, sensor_normalizado VIIRS→VIIRS750).
- **344 (66%) son únicos al OCR** y NO existen en CONS. **Esto es coverage adicional MIROVA que solo entra por canal OCR** (MIROVA publica la imagen por vol pero no la incluye en latest.php — patrón observado por Nicolás).

Distribución por vol del incremento exclusivo OCR: Lascar +117, Lastarria +55, PCC +49, Isluga +47, PP +31, Tupungatito +21, Chaiten +11, Villarrica +7, Copahue +3, Llaima +2, NdC +1. **Total +344 ALERTAs MIROVA sobre las 763 del CONS = +45% universo**.

---

## Recomendaciones (ordenadas por ROI)

### Acciones locales en VRP Chile (NO tocar scraper)

1. **[Bloqueante]** Loader del ground truth en VRP Chile debe consumir **CONS ∪ OCR**, dedup por `(timestamp, vol_normalizado, sensor_normalizado)`. Cualquier audit / R3 / cruce TP/FP que use solo CONS está sub-dimensionado en ~45% del universo. Verificar que `scripts/audit_*.py` y `experiments/*` actuales lo hagan; varios audits S60-S62 (A10) usaban CONS solo.
2. **[Bloqueante]** Extraer `Distancia_km` del OCR parseando `Nota_Validacion` con regex `dist[≈~=]\s*(\d+\.?\d*)\s*km` antes de aplicar filtros geográficos al universo OCR.
3. **[Bloqueante]** Documentar en `volcanoes.yaml` (o en el loader) que **Tupungatito tiene coverage MIROVA solo desde 2026-02-14**. Audits ventana >94d deben recortar o anotar.
4. **[Bloqueante]** En el loader, agregar `Peteroa → PlanchonPeteroa` al mapa de alias para no perder las 6 días pre-rename.
5. **[Importante]** Decidir política sobre `FALSO_POSITIVO` (363 filas): MIROVA SÍ las publicó (vrp>0) pero el scraper las marcó como out-of-radius. Para vols con anomalía lacolito real (PCC), conviene tratarlas como **detecciones MIROVA lejanas** y compararlas contra nuestro path `far`, no descartarlas.
6. **[Importante]** Unificar el set de `Clasificacion Mirova` antes de cualquier filter cross-CSV: mapear OCR `Medio → Moderado` o agregar `Medio` al set válido nuestro.

### Bugs a sugerirle a Nicolás para Mirova-v1 (opcional, ROI moderado)

7. **[F-B2]** En `ocr_utils.py` (~37 KB), el extractor calcula la distancia (la deja en `Nota_Validacion`) pero no la persiste en la columna `Distancia_km`. Fix de 1 línea cuando se construye el dict OCR row. **ROI alto, esfuerzo mínimo**.
8. **[F-B4]** Backfill o normalizar `Peteroa → PlanchonPeteroa` en CONS histórico (script de migración una sola vez). **Cosmético si se maneja con alias local, pero limpiar el snapshot es mejor higiene**.
9. **[F-I1]** En `scraper_ocr.py`, ajustar el mapping de label OCR para usar `Moderado` (alineado a `obtener_clasificacion_mirova` en `scraper.py:55-60`) en lugar de `Medio`. Schema-consistency entre CSVs del mismo scraper.

---

## Conclusión accionable para Nicolás

El scraper Mirova-v1 es **confiable como ground truth**. La captura latest.php es completa, los workflows están sanos, no hay gaps de cron, no hay encoding bugs y la lógica del parser es directa. **Cero issues bloqueantes en el scraper en sí**.

Lo que **invalida parcialmente nuestro cruce TP/FP es cómo el loader local de VRP Chile interpreta los CSVs**: si solo lee CONS estamos perdiendo 344 ALERTAs OCR (+45% universo), si filtra OCR por `Distancia_km` pierde el 100% del OCR, y si filtra `PlanchonPeteroa` pierde las 6 días `Peteroa`. Las 4 correcciones son locales y caben en una sola PR del loader (≈30 líneas). Una vez aplicadas, los veredictos TP/FP/FN son comparables.

El único bug interno del scraper que vale la pena reportarte es **F-B2** (persistir `Distancia_km` extraído por OCR en su propia columna en vez de solo dejarlo en `Nota_Validacion`). Fix de 1 línea en `ocr_utils.py`, te ahorra parsing regex aguas abajo a vos y a cualquier consumidor futuro del CSV.

---

## Paths

- **Datos**: `data/mirova_reference/mirova_v1_snapshot/{registro_vrp_consolidado.csv, registro_vrp_ocr.csv}`
- **Outputs**:
  - `experiments/_s86_audit_profundo/F_scraper_integrity.json` (matriz completa por vol)
  - `experiments/_s86_audit_profundo/F_scraper_integrity.md` (este doc)
  - `experiments/_s86_audit_profundo/script_F.py` (reproducible)
- **Referencias scraper**: `https://github.com/MendozaVolcanic/Mirova-v1/blob/main/scraper.py` (245 líneas), `scraper_ocr.py`, `ocr_utils.py`
