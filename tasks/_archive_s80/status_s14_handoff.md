# Handoff S14 → S15 — VRP Chile

Fecha: 2026-04-21. Leer este archivo **primero** al arrancar S15.
Complementa `tasks/decisions_s14.md` (decisiones y aprendizajes) y
`tasks/status_s13_bibliography_closed.md` (cierre bibliográfico).

---

## Estado al cerrar S14

**Paso 2 (corrección de paridad MIROVA) implementado completo pero
SIN COMMITEAR.** El NRT operacional sigue corriendo con el código de S12;
los cambios S14 quedan en working tree local hasta que Nicolás valide
visualmente o apruebe commit+push.

### Decisión abierta que cerrar al arrancar S15

**"¿Commit y push ahora, o review visual del dashboard primero?"**

Opciones:
- **A) Commit y push directo**: el próximo NRT (cron cada 2h) arranca con
  schema nuevo. Riesgo bajo: los cambios son backward-compatible
  (`inner_radius_km` es opcional en las funciones, records viejos
  siguen leyéndose). Si algo falla, rollback con `git revert` + restaurar
  `volcanoes.yaml.S13backup`.
- **B) Review visual primero**: abrir `frontend/index.html` local contra
  la data existente en `data/mirova_equivalent/*.json`, ver que el
  círculo `inner_radius_km` se dibuja, que el modal "Acerca de" abre, que
  los markers distinguen summit/far donde haya `distance_class`.
  Tarda 5 min, después commit.

Mi recomendación: **B primero** (5 min de seguridad vale la pena), después
commit+push.

---

## Archivos modificados (sin commitear)

### Modified
- `CLAUDE.md` — coeficientes empíricos por sensor + reglas A1–A5 + geometría S14.
- `volcanoes.yaml` — `radius_km=25` + `inner_radius_km` MIROVA-oficial en 11 chilenos.
- `pipeline/process_modis.py` — `+inner_radius_km` arg, `+final_hotspot_*`, `+distance_class`.
- `pipeline/process_viirs.py` — idem.
- `pipeline/process_viirs_mod.py` — idem + `WOOSTER_COEFF 18.9→19.7`.
- `scripts/run_pipeline.py` — pasa `inner_radius_km` a los 3 callers.
- `frontend/index.html` — círculo inner_radius, clasificación summit/far,
  leyenda, botón "Acerca de" + modal con credits, footer persistente MIROVA/Coppola.
- `data/mirova/PlanchonPeteroa_OLD_pre_consolidado.json` — modificación menor
  pre-S14, probablemente sin relación directa, revisar antes de commit.

### New files
- `volcanoes.yaml.S13backup` — **NO commitear** (es backup local de rollback).
- `tasks/decisions_s14.md` — registro de decisiones + aprendizajes S14.
- `tasks/status_s13_bibliography_closed.md` — cierre de fase bibliográfica.
- `tasks/status_s14_handoff.md` — este archivo.
- `experiments/21_*` — calibración k_MIR empírico vs OSF (3 archivos).
- `experiments/22_*` — comparación régimen (3 archivos).
- `experiments/23_*` — diagnósticos paralelos A/B/D (3 archivos).
- `experiments/24_*` — auditoría vent+radius con mapa Leaflet (3 archivos).
- `data/mirova_reference/` — **DB MIROVA v2.5 OSF descargada** (98 MB CSV +
  32 KB schema.docx). Agregar a `.gitignore` si no se quiere commitear
  tamaño, o usar Git LFS. Ver decisión abajo.
- `frontend/llaima_anomalies.png`, `frontend/planchonpeteroa_anomalies.png` —
  screenshots sueltos del dashboard; decidir si se commitean o borran.

### Decisiones pequeñas para commit
- **`data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` (98 MB)**: exceder
  límite recomendado GitHub (50 MB warning, 100 MB hard). Opciones:
  - Git LFS (configurar antes).
  - Agregar a `.gitignore` — cualquiera puede re-bajar con el script OSF.
  - **Recomendado**: `.gitignore` + documentar el path del repo en
    `data/mirova_reference/README.md` con URL de descarga.
- **`volcanoes.yaml.S13backup`**: no commitear, es rollback local.
- **`frontend/*.png` sueltos**: revisar qué son; probablemente borrar.

---

## Pipeline de validación antes de commit

1. **Abrir `frontend/index.html` local** (doble click en Explorer).
2. Navegar a 2–3 volcanes (ej. Lascar, Villarrica, PCC) y confirmar:
   - Círculo rojo discreto alrededor del vent marca el `inner_radius_km`.
   - Markers existentes se renderizan (compatibilidad con records legacy).
   - Botón "ℹ️ Acerca de" arriba a la derecha abre modal con créditos
     MIROVA/Coppola y lista de 7 papers canónicos.
   - Footer al final del dashboard muestra nota persistente de créditos.
3. **Sanity coeficientes** (ya validado en S14, pero re-verificar no rompe):
   ```bash
   python -c "import pipeline.process_modis as m, pipeline.process_viirs as v, pipeline.process_viirs_mod as vm; \
              print(m.WOOSTER_COEFF, v.WOOSTER_COEFF, vm.WOOSTER_COEFF)"
   # Esperado: 18.9 18.0 19.7
   ```
4. **Commit staging limpio** — no incluir `data/mirova_reference/` ni
   `.S13backup`.
5. **Commit message sugerido**:
   ```
   S14: MIROVA-equivalent geometry fix — dual radius + schema unificado

   - volcanoes.yaml: radius_km=25 uniforme + inner_radius_km MIROVA-oficial.
     Valores extraídos de los KML MIROVA: Lastarria/PlanchonPet 3, Copahue 4,
     Lascar/Isluga/NdC/Llaima/Villarrica/Chaiten 5, Tupungatito 7, PCC 20.
   - Schema unificado final_hotspot_lat/lon/dist_km con fallback eruption→vent.
     Fix del bug S12 8ad2f59 donde vent-path quedaba sin coord visible.
   - distance_class={"summit","far"} para clasificación visual al estilo
     MIROVA (rojo=real, gris=posible-lejana).
   - WOOSTER_COEFF VIIRS 750m M-band: 18.9 → 19.7 (validado empíricamente
     contra OSF v2.5, experiments/21_*.py).
   - Dashboard: círculo inner_radius visible, markers distinguen summit/far,
     modal "Acerca de" + footer con créditos a MIROVA/Coppola/papers.
   - CLAUDE.md actualizado con coeficientes por sensor y reglas A1-A5.

   Backward-compatible: records legacy sin distance_class siguen leyéndose.
   El próximo NRT llena los campos nuevos automáticamente.
   ```
6. **Push** al repo.
7. Esperar el próximo cron NRT (2h) y verificar que:
   - GitHub Actions pasó.
   - Algún JSON en `data/mirova_equivalent/` tiene records con
     `distance_class: "summit"` o `"far"`.
   - Dashboard en GitHub Pages renderiza bien.

---

## Siguiente trabajo S15 (orden propuesto)

### 1. Cerrar el commit de S14 (si no se cerró al final de S14)
Ver sección arriba.

### 2. Paso 1b — reproceso Nov 2025
Objetivo: cross-match evento-a-evento entre nuestros detecciones y OSF
v2.5 para medir paridad métrica real (ratio VRP mediana en [0.8, 1.25]).

✅ **EARTHDATA ya configurado** (S14 2026-04-21). `~/.netrc` con username
`nicolasmendoza` verificado con `earthaccess.login(strategy='netrc')` →
`Authenticated: True`. No hay que reconfigurar nada para arrancar.

Crear `scripts/backfill_nov_2025.py` derivado de `run_pipeline.py` con:
- Volcanes: Lascar, Villarrica, Copahue, Chaiten (4 contraste).
- Fechas: 2025-11-01 a 2025-11-30 (30 días).
- Solo VIIRS (MODIS roto en Windows por pyhdf — solo Linux Actions).
- Patrón **fetch-process-delete** granule-por-granule para pico ~100 MB.
- Output: `data/mirova_equivalent_backfill_nov2025/*.json` (no toca
  operacional).

~24 GB tráfico total, ~1 h compute local.

### 3. Auditoría cross-match post-reproceso
Script `experiments/25_crossmatch_nov2025_vs_osf.py`:
- Filtra OSF 2025-11-01 a 2025-11-30 para los 4 volcanes.
- Cross-match con nuestros JSONs por (volcán, sensor, timeUTC ±15 min).
- Métricas: ratio VRP mediano, Spearman correlation, recall, precision.
- Criterio paridad: ratio mediano en [0.8, 1.25] sobre ≥50 pares.

### 4. Decisión S15
- **Si paridad OK** → cerrar como baseline mirova_equivalent y pasar a
  Track B (TIRVolcH, integrated-ROI, experimentos sobre mirova_equivalent
  validado).
- **Si paridad NO OK** → diagnóstico de qué falta (ETI cuadrático, ROI1/ROI2
  dual de Coppola 2016a, o ajustes finos de umbrales).

### 5. Backlog desde S13
- Integrated-ROI Coppola 2015 Eq.1 (Test 1 Villarrica) → en `experimental`.
- TIRVolcH path sobre I5 (Aveni 2024) → en `experimental`.
- VRP→volumen con `c_rad` (Galetto 2025) → Fase 5 post-paridad.

---

## Contexto para sesión fresca

### Contactos
- Diego Coppola (autor MIROVA), dcoppola@unito.it — no contactar todavía
  (ver regla: solo con pipeline validado + pregunta específica).
- Rodrigo De Negri, rdnegri@uchile.cl (OpenVIS, infrasonido).

### Reglas comunicativas (de CLAUDE.md, no olvidar)
- Hablar como geólogo no como programador. Fenómeno físico → pipeline →
  números.
- Nunca adivinar valores físicos o datos instrumentales.
- Citar papers para cualquier cambio metodológico.

### Reglas operacionales S14 (nuevas, ver CLAUDE.md sección "Reglas operacionales S14")
- **A1**: calibración empírica con OSF > derivación teórica de papers.
- **A2**: diagnósticos paralelos locales antes de reprocesos con fetch.
- **A3**: campos distance siempre documentar desde qué punto miden.
- **A4**: MIROVA es simple geometría + umbrales, no máscaras adaptativas.
- **A5**: valores MIROVA oficiales (KML, OSF) son datos, no opiniones.

### Archivos clave para leer al arrancar S15
1. `tasks/status_s14_handoff.md` (este).
2. `CLAUDE.md` secciones "Reglas científicas" y "Reglas operacionales S14".
3. `tasks/decisions_s14.md` (razonamiento detrás de cada decisión).
4. `experiments/21_results.json` (coeficientes empíricos validados).
5. `experiments/24_vent_radius_audit.html` (mapa geométrico).

### Estado NRT operacional
- Cron cada 2h en GitHub Actions (matrix 45 volcanes, max-parallel 8).
- Último NRT conocido al cerrar S14: 2026-04-18 (commit `71f8e5b`).
- Después del commit S14 el cron va a regenerar JSONs con schema nuevo.

---

*Fin handoff S14. Al arrancar S15, abrir este archivo primero.*
