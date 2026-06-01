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

## §1 — 🚨 PRIORIDAD 0: NRT no avanza (operacional)

**Síntoma (reporte Nicolás)**: dashboard sin datos frescos. **Diagnóstico S95**: NO es
Nevados de Chillán — son los **11 volcanes**, todos clavados en **2026-05-30 06:42 UTC**
(~1.5 días). El cron `nrt.yml` está **VIVO y sano** (runs cada 2h, todos `success`,
último 26726951556). El log del run 26724312017 muestra: el pipeline procesa la fecha
**20260530** (no 05-31), da **VRP=0** en todos los sensores y termina **"No changes to
commit"** → no agrega records nuevos.

**Pendiente confirmar (no pude por entorno roto, NO adivinar)**: el comentario de
`nrt.yml:2` dice *"Procesa SOLO el día actual UTC (hoy)"* pero el log procesó **ayer**
(05-30). Hipótesis a verificar leyendo el comando real `run_pipeline` del yml:
  - (a) **Bug/desfase de fecha**: el workflow calcula la fecha a procesar como
    yesterday o con un offset, y nunca llega a la pasada nocturna del día en curso.
  - (b) **Comportamiento esperado con delay**: NRT procesa "ayer" a propósito (latencia
    LANCE ~3h) y el dato del 05-31 entrará el 06-01. Si es esto, NO es bug — pero
    entonces el dashboard siempre va ~1 día atrás (¿aceptable para OVDAS? preguntar).
  - (c) **Sin actividad térmica real**: VRP=0 en las pasadas del 05-30 es plausible
    (volcanes en reposo), pero eso igual debería commitear un record con VRP=0. Que diga
    "No changes" sugiere que el record 05-30 06:42 YA existía → reprocesa lo mismo.

**Acción S96**: `Read .github/workflows/nrt.yml` completo → ver el comando exacto de
fecha. Confirmar cuál de (a)/(b)/(c). Si (a) bug → fix de fecha (A45, es NRT operacional).
Si (b) → documentar y preguntar a Nicolás si el delay de 1 día es aceptable. Comparar
`date -u` actual vs la fecha que procesa el yml.

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
