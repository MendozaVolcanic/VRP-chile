# Design — Detección diurna MODIS (clon literal MIROVA)

**Fecha**: 2026-05-30 (S90). **Estado**: diseño aprobado (dirección), pendiente
escritura de plan (`writing-plans`) + implementación con A45 (tag + OK explícito).
**Autor**: sesión Claude S90, brainstorming con Nicolás.

## 1. Problema (fenómeno → mecanismo)

La auditoría S90 de recall vs MIROVA (ver `experiments/_s90_audit/RESULTS.md`)
mostró que las **anomalías térmicas MÁS grandes** que perdemos en Nevados de
Chillán y Villarrica son **pasadas diurnas MODIS**:
- NdC 2026-03-17 13:15 UTC (solar ~08:30 local), MODIS, VRP MIROVA 1.06 MW.
- NdC 2026-04-20 19:00 UTC (solar ~14:15), VIIRS, 0.99 MW.
- Villarrica 2026-05-29 19:55 UTC (solar ~15:06), MODIS, **1.83 MW**.

De las tres no tenemos NINGÚN record: el pipeline **excluye todo lo diurno**
(`store.py:422-431`, rechaza si `_solar_elevation > 0`). Es la regla histórica
"MIR solo nocturno" (la luz solar reflejada contamina la banda MIR ~3.9 µm).

MIROVA, en cambio, **sí procesa MODIS de día** — con parámetros más estrictos,
no con corrección solar. Excluir todo el diurno es por lo tanto una **divergencia
de MIROVA** que estamos pagando en recall sobre los eventos diurnos reales.

## 2. MISSION — las 3 preguntas (vinculantes)

**Pregunta 1 — ¿Está documentado en papers MIROVA core? → SÍ.**
Coppola 2016a SP426.5 Tabla 1 (`documentacion/sp426_5.txt:317-343`) define
parámetros DÍA separados de NOCHE para MODIS, confirmado verbatim por Coppola
2024 cap.11 Tabla 2 (`coppola2024_chapter.txt:1033-1037`):

| Parámetro | Noche | **Día** |
|---|---|---|
| K1 (NTI fijo, Test 1) | −0.8 | **−0.6** |
| C1 (dNTI/dETI mínimo contextual) | 0.003 (R1) / 0.01 (R2) | **0.02** (ambos) |
| C2 (N·σ contextual) | 5σ (R1 summit) / 10σ (R2 scene) | **15σ** (ambos) |

MIROVA NO corrige el sol ni cambia de banda: sube el umbral N·σ a 15 y endurece
K1 a −0.6 para absorber la variabilidad solar del MIR. Mismas bandas B21/22 MIR
+ B31/32 TIR. **→ Implementable: replica metodología documentada y cierra la
divergencia "MIR solo nocturno".**

**Pregunta 2 — ¿Cierra divergencia documentada?** También SÍ: relacionada con D4
(recall sub-pixel/summit) en `MIROVA_DIVERGENCES.md` — recuperamos detecciones
diurnas reales que MIROVA publica y nosotros descartábamos por completo.

**Alcance VIIRS — exclusión deliberada.** Ningún paper MIROVA-core (Coppola,
Campus 2024, Massimetti) publica parámetros VIIRS diurnos; los describen como
**solo nocturno** ("night-time VIIRS images", `campus2024_extracted.txt:148,197`).
El único set VIIRS diurno (n=8) viene de **Di Bella 2024 — NO MIROVA** (regla A9).
Por lo tanto **VIIRS se mantiene nocturno** (como ya está). VIIRS diurno sería
divergencia → solo en perfil `experimental`, citando Di Bella, NUNCA en operacional.

## 3. Alcance (YAGNI)

**SOLO MODIS diurno (Terra + Aqua).** VIIRS sin cambios (sigue nocturno). El
gate `store.py` debe permitir MODIS diurno pero **seguir rechazando VIIRS diurno**.
No se toca: clustering, VRP/Wooster, vent_anchored, geo_class, frontend.

## 4. Parámetros día (verbatim Coppola 2016a Tabla 1)

Nuevas claves de perfil (el perfil ya tiene `nti_k1_night: -0.8`, anticipando el
par day):
- `nti_k1_day: -0.6`
- `dnti_contextual_c1_day: 0.02` (aplica a summit y scene de día)
- `n_sigma_mir_day: 15.0` (aplica a summit y scene de día)

Selección día/noche **a nivel de escena** (una pasada MODIS sobre un volcán chico
es día o noche entera; per-pixel/terminador es over-engineering, descartado).
Reusar `_solar_elevation(lat, lon, dt_utc)` (ya existe en `store.py`): `elev > 0`
→ usar set día; si no → set noche (actual).

## 5. Componentes que toca

1. **`pipeline/store.py:422-431`** — el gate `_solar_elevation>0`: cuando el flag
   de perfil está ON, permitir records MODIS diurnos; seguir rechazando VIIRS
   diurnos (chequear `sensor.startswith("MODIS")`). Flag OFF = comportamiento
   actual intacto.
2. **`pipeline/process_modis.py`** — seleccionar el set de thresholds (K1, C1, N·σ)
   según día/noche de la escena. Hoy usa siempre noche. Inyectar la elección
   día/noche en los paths Test1/dual-ROI BT/dNTI.
3. **Perfiles A/B nuevos** — `_daytime_modis_enabled.yaml` / `_disabled.yaml` con
   `data_subdir` aislado (patrón S24/S25). El flag nuevo: `enable_daytime_modis`
   (default **False** — opt-in, NO toca operacional).

## 6. Enfoque (A — aprobado)

Path diurno **gateado por flag**, validado por A/B ANTES de adoptar en operacional.
Rechazados: B (quitar gate directo, viola A45/anti-drift), C (per-pixel, YAGNI).

## 7. Validación (regla S33 — obligatoria antes de adopción operacional)

1. **A/B reproc** (GH Actions o local) sobre los 11 Tier A, `enabled` vs `disabled`,
   ventana que cubra los eventos diurnos conocidos (NdC mar/abr, Villarrica may).
2. **Métricas**: recall/precisión/F1/ratio vs MIROVA (computeMetrics) en cada perfil.
   Esperado: ↑recall (capturar las diurnas reales) sin ↑FP grosero.
3. **R2 pixel-level** sobre ≥1 evento diurno con TIF MIROVA disponible (NdC tiene
   47 TIFs MODIS, ahora indexados — PR #254): confirmar que el píxel diurno que
   detectamos coincide con el de MIROVA.
4. **R3 audit independiente**: cruce con CSV MIROVA confirmando que las nuevas
   detecciones diurnas matchean alertas MIROVA reales (no son FP solares).
5. **Cuestionar el resultado** (R6): si recall sube >30%, verificar que no sea
   métrica auto-confirmatoria. Las nuevas TP deben corresponder a ALERTAS MIROVA
   diurnas, no a ruido.

**Criterio de adopción**: recall diurno-MODIS sube en ≥1 volcán SIN que la
precisión global caiga por debajo del piso del proyecto (≥0.50 donde ya se medía),
y ≥1 evento validado pixel-level contra TIF MIROVA. Si la precisión se desploma
(FP solares dominan) → NO adoptar, documentar y mantener exclusión diurna.

## 8. Pre-mortem (qué podría salir mal)

- **FP solares**: el 15σ podría no bastar para algunas escenas diurnas muy
  reflectivas (nieve, desierto Atacama). Mitigación: el A/B lo mide; si los FP
  diurnos son groseros, el criterio de adopción lo bloquea.
- **σ_bg diurno inflado**: el background diurno es más ruidoso → N·σ podría
  comportarse distinto que de noche. El 15σ de MIROVA ya lo contempla; verificar
  empíricamente en el A/B (no asumir).
- **`_solar_elevation` aproximada**: la fórmula es aproximada (~±2°). Cerca del
  terminador (elev ~0) podría clasificar mal. Bajo impacto (pocas pasadas en el
  terminador); documentar, no sobre-ingenierizar.
- **Doble-conteo MODIS día+noche mismo volcán**: si un volcán tiene pasada diurna
  Y nocturna el mismo día, ahora cuenta ambas. Es correcto (MIROVA también).
- **Regresión nocturna**: el flag OFF debe dejar TODO igual. Test obligatorio:
  con flag OFF, 0 cambios en los records nocturnos existentes.

## 9. Plan de tests (TDD, antes del código)

- Test: con `enable_daytime_modis=False`, un record MODIS diurno sintético sigue
  siendo rechazado por el gate (no regresión).
- Test: con flag ON, un record MODIS diurno con señal > umbral día (15σ, K1=−0.6)
  se acepta y guarda; uno bajo umbral se rechaza.
- Test: con flag ON, un record VIIRS diurno SIGUE rechazado (literal MIROVA).
- Test: selección día/noche — escena con `elev>0` usa K1=−0.6/C2=15; con `elev<0`
  usa K1=−0.8/C2=5-10.
- Test: parámetros verbatim (K1=−0.6, C1=0.02, C2=15) cargados del perfil.

## 10. A45 / anti-drift

- La implementación toca `store.py` + `process_modis.py` (NRT operacional) →
  **tag defensivo `pre-s9X-daytime-modis` + OK explícito de Nicolás ANTES del
  primer edit** (A45/A45-refuerzo S75).
- El flag default **False**: el operacional `mirova_equivalent.yaml` NO cambia
  hasta validación A/B + R2 + R3 aprobadas (regla S33).
- NO es un "gate intra-radio" ni un parche de los anti-patrones — es replicación
  de parámetros documentados Coppola 2016a. Pasa las 3 preguntas MISSION por la
  puerta 1 (verde), no por la gris.

## 11. Fuera de alcance (explícito)

- VIIRS diurno (sería divergencia → `experimental` + Di Bella).
- Corrección solar / banda nueva (MIROVA no lo hace).
- Cambios a clustering, VRP, vent_anchored, geo_class, frontend.
- Day/night per-pixel.
