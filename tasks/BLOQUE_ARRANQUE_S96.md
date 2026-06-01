# BLOQUE ARRANQUE S96

**Sesión previa S95 (2026-05-31).** Muy productiva pese a un entorno de tools
inestable (stdout entrelazado/vacío durante gran parte de la sesión → 4 errores de
"número antes del dato", todos detectados y corregidos contra archivos en disco).
3 PRs mergeados (#297, #298, #299). main al día.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S96.md
cat docs/AUDIT_S95_gaps_sistemicos.md        # auditoría 5 ejes
cat docs/F5_CALIBRATION_S95.md               # calibración F5' D2-safe v2
```
Memoria: [[reference_s95_gaps_sistemicos]] (índice completo S95).

## §0.5 — Integridad (REFORZADA S95)
El entorno entrelaza/vacía stdout. **Regla operativa S95**: número/conclusión NUNCA
antes de leer el dato; escribir salida SIEMPRE a archivo único y leer con `cat`/`Read`;
un tool call por mensaje (empaquetar varios causó cancelaciones en cadena). 4 deslices
esta sesión, todos corregidos — pero costó tiempo. A45 para tocar pipeline (tag+OK+TDD+
reproc). A47 reproc no paralelo sobre mismo data_subdir. VRP_TMP_DIR=C:/vrp_tmp.

## §1 — 🚨 PRIORIDAD 0: NRT procesa solo "ayer" — DECISIÓN: agregar el día en curso

**Síntoma (reporte Nicolás)**: dashboard sin datos frescos (NdC, pero en realidad TODOS).
**Diagnóstico S95 (CONFIRMADO leyendo `nrt.yml`)**: NO es bug ni fallo — los **11 vols**
están clavados en **2026-05-30 06:42 UTC** porque el cron procesa **"ayer"** por diseño
(`nrt.yml:27`: `--date` vacío = yesterday). El cron está **vivo y sano** (runs cada 2h
todos `success`). El run del 31-may procesó el 30-may (ya cargado) → VRP=0 → "No changes
to commit". La pasada nocturna del 31-may NO se procesa hasta el 01-jun. El dashboard va
sistemáticamente **~1 día atrás**. Además hay healthcheck A57 (nrt.yml:261-298) que falla
el run si el último record tiene >72h (hoy ~36h, todavía no salta).

**DECISIÓN DE NICOLÁS (S95 cierre)**: NO es aceptable el retraso de 1 día. Para monitoreo
volcánico se necesita el dato **lo antes posible tras cada pasada**. → **El NRT debe
procesar también el día en curso (hoy), no solo ayer.**

**Fenómeno físico que justifica procesar hoy+ayer**: las pasadas que más importan son las
**nocturnas** (MIR sin contaminación solar diurna), que en Chile (UTC−4) caen en la
**madrugada UTC** del día en curso (~03:00–07:00 UTC). LANCE publica ~3h post-overpass.
Por tanto, cuando el cron corre durante el día UTC, la pasada nocturna de HOY ya está
disponible. Procesar solo "ayer" la pierde por ~24h. Debe procesar **hoy** (para lo
nuevo) **y ayer** (red de seguridad: pasadas tardías + upgrade NRT→Standard que store.py
hace, delta BT <0.1K despreciable).

**Acción S96 (A45 — NRT operacional, tag+OK Nicolás+verificación)**:
1. `Read .github/workflows/nrt.yml` (ya leído S95: el `--date` sale de
   `github.event.inputs.date`, vacío en cron → run_pipeline default = yesterday).
   Verificar en `scripts/run_pipeline.py` cómo resuelve la fecha default (confirmar que
   "vacío = yesterday" y si acepta procesar un rango hoy+ayer).
2. Diseño del fix: que el cron procese **hoy y ayer** en cada corrida. Opciones:
   (i) loop de 2 fechas en el step (`--date today` y `--date yesterday`), o
   (ii) `--start yesterday --end today` si run_pipeline soporta rango con esas fechas.
   Preferir el cambio mínimo. Cuidar idempotencia (store.py dedup por datetime+sensor →
   reprocesar no duplica) y el timeout 50 min/step (2 días × sensores debe caber; medir).
3. **A45 completo**: tag defensivo `pre-s96-nrt-current-day` antes de editar nrt.yml;
   correr un `workflow_dispatch` manual de prueba con 1 volcán y `--date today` para
   validar que descarga la pasada del día y commitea ANTES de tocar el cron; OK explícito
   de Nicolás; recién entonces mergear.
4. Considerar subir la **cadencia** del cron si hace falta capturar la pasada apenas
   publica LANCE (hoy `0 */2 * * *` = cada 2h; podría bastar, medir latencia real
   pasada→aparece-en-dashboard tras el fix).
5. Verificar de paso que el secret `EARTHDATA_TOKEN` del repo no esté por expirar (si las
   descargas empezaran a fallar sería otra causa de stale; hoy NO es el problema — el run
   descarga y procesa OK, solo mira la fecha equivocada).

**Criterio de aceptación**: tras el fix, el último record de cada Tier A debe tener
fecha = pasada nocturna del día en curso (no ayer), visible en el dashboard el mismo día.

## §2 — F5' (lo central de S95, CALIBRADO — falta implementar)

Calibración completa en `docs/F5_CALIBRATION_S95.md`. Veredicto: **D2-safe v2 (ancla =
píxel de máxima energía) con R_core=0.75 km**. Sobre data reprocesada (data/_s94_reproc):
- Campo frío curado: Tupungatito 15.85→2.52×, Villarrica 9.83→2.07×, mediana 5.64→1.74×.
- Láscar (cráter caliente) conservado 0.84×.
- **0 eventos MIROVA-confirmados a magnitud 0** (criterio seguridad cumplido tras 2
  intentos; el ancla correcta es el píxel de mayor VRP, no el más cercano al vent).
- Scripts: `experiments/_s95_audit/f5_d2safe.py` (variante final) + `f5_d2_sweep.py`.

**Pendiente S96 — implementar F5' display-first** (decisión Nicolás S94, reversible):
1. Replicar D2-safe v2 como `mirovaEqVrpCore(r)` en las **3 vistas** frontend
   (index.html, diario.html, mosaico.html — S92 L5), recomputando la magnitud desde
   `anomaly_pixels` (ahora poblados en los 3 sensores tras #297). Regla Eje3/A48:
   recomputar distancias desde lat/lon, NO usar `dist_km` (ancla variable).
2. Validar en **preview real navegador** (no node --check) las 3 vistas.
3. Solo si convence visualmente + R2 pixel-level vs TIF MIROVA → bajar a
   `process_viirs.py` (segundo umbral para la suma de magnitud, detección intacta) con
   A45 completo. Detección NUNCA se toca.

## §3 — Pendientes menores
- **Re-disparar VIIRS reproc** para 5 vols que no completaron el matrix S95: Copahue,
  NevadosDeChillan, Llaima, Chaiten, Isluga (editar matrix de
  `.github/workflows/reproc-s94-f2-viirs.yml` a esos 5; NO son campo-frío, no urgente,
  no afecta F5'). Probable: 0 pasadas VIIRS nocturnas válidas en la ventana.
- **🔐 ROTAR token Earthdata** `C:/Users/nmend/edl_token.txt`: quedó expuesto en el chat
  de S94, Nicolás confirmó que NO lo rotó → sigue comprometido. El cron NRT usa el
  secret `EARTHDATA_TOKEN` del repo (separado); verificar también que ese no expiró
  (podría relacionarse con §1 si las descargas fallan).

## §4 — Estado consolidado S95
- **PR #297** — fix Test1 anomaly_pixels portado a MODIS + VIIRS750 (gap A07 sistémico;
  18 MODIS + 108 VIIRS750 afectados). Aditivo, TDD, tag pre-s95-test1-anomaly-pixels-modis-v750.
- **PR #298 + #299** — calibración F5' (D2-safe v2; #299 rectifica error de números de #298).
- **Auditoría 5 ejes** (`docs/AUDIT_S95_gaps_sistemicos.md`): Eje1 accionado; Eje3 ancla
  engañosa de distancias → regla F5'; Eje5 incoherencia `distance_class` real pero 0
  pérdida recall → backlog (no reactivo, A55).
- **Reproc MODIS+VIIRS completo** en `data/_s94_reproc` (11 vols), deuda histórica
  limpiada (PCC 1362→287 MW, Chaitén 534→94, etc.).
- main: ver `git log -1` (último commit del cierre).
