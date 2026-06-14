# Design — Magnitud MODIS: núcleo focal/contextual (S109 §1)

**Fecha**: 2026-06-14 · **Sesión**: S109 · **Autor**: Claude (delegación autónoma Nicolás)
**Estado**: diseño aprobado (dirección) → implementación flag-OFF + A/B.
**Tags A45**: `pre-s109-modis-focal-magnitude` (antes del primer edit a `pipeline/`).

## 0. Resumen ejecutivo

La magnitud del cluster MODIS al cráter está inflada (~7 MW) en 5 volcanes nevados
(Chaitén, Villarrica, Llaima, Tupungatito, PCC) porque **suma el campo difuso topográfico**
(~10 K sobre el fondo frío), que MIROVA ignora por diseño. El fix S107/S108 (fondo-local de
corona) fue **refutado con datos**. Este diseño ataca otra palanca, papers-fiel: **restringir
la suma de la magnitud del cluster a los píxeles genuinamente focales/contextuales**
(anómalos vs sus 8 vecinos ∪ {pico}), generalizando a MODIS el filtro contextual **ya probado
en VIIRS** (ctxpeak, S100, que curó Tupun/Villarrica/Llaima). Solo magnitud — detección y
posición intactas. Flag-OFF + A/B 3 brazos.

## 1. Fenómeno físico (por qué pasa)

En estos volcanes la cumbre nevada irradia poco de noche, pero el entorno del cráter + el valle
tibio de baja altitud quedan ~10 K sobre el fondo frío del anillo lejano (5-25 km). Eso es
**gradiente topográfico nocturno** (= A69 / D11, la misma raíz que el sesgo de posición que
trabajamos S104-S106), **no lava**. La señal volcánica real de estos cráteres es **sub-píxel**:
MIROVA la ve por **VIIRS 375 m** (más fino), no por MODIS 1 km.

## 2. Causa raíz en el pipeline (verificado S109)

- La magnitud del cluster es la **suma del VRP per-pixel** sobre el cluster contiguo
  (`process_modis.py:910-946` eruption; `:1146-1201` test1; `clustering.py:113`;
  `vrp_regimes.py:186-194`).
- **Los inflados son path eruption (105/121), no test1 (10/121)** — `breakdown_inflated_source.py`.
  → Portar ctxpeak tal cual (solo toca test1) curaría ~10/121. Hay que **generalizar al cluster**.
- Los píxeles difusos entran por **dNTI contextual (semilla) + second-pass recapture** (14-185 px)
  — NO por NTI absoluto ni BT (medianas `diag_n_*_path`: bt=0, nti_abs=0, dnti_ctx=1-70, 2ndpass=14-185).
- **La magnitud ES el campo difuso sumado** (`_s109_diffuse_probe`): el píxel más caliente del
  cluster aporta solo **16-20%** de `pc.vrp_mw`; el 80-84% son ~8-13 píxeles de ~0.5 MW. BT pico
  283-287 K, ΔT 10-14 K. Ningún píxel sobresale = firma del campo topográfico. **Control Láscar**
  (único MODIS-foco real, 82 ALERTA MIROVA-MODIS): píxel máximo = 55% (foco discreto).

## 3. Papers (qué hace MIROVA, verbatim)

- `VRP = A_pix · k · Σ_Npix (L_hot,i − L_bk)`, **Npix = solo píxeles ALERTADOS** (superan
  umbral NTI/dNTI/ETI). Coppola 2016a SP426.5 Eq.7-8; Coppola 2023 Eq.1-2; Coppola 2024 Eq.17.
- Coppola 2023:464-466 VERBATIM: *"VRP ... is **fundamentally insensitive to the diffuse heat
  dispersed from the crater area at a few degrees above the background** (zones of diffuse
  degassing)"*. El umbral (Tabla 1: K1=−0.8 noche, C2=5σ) excluye el difuso por diseño.
- **Un algoritmo por sensor, uniforme entre volcanes** (Coppola 2024:1135-1145). MIROVA reporta
  **cada sensor por separado, nunca combina** → cap cross-sensor (candidato b) = divergencia.
- Cruce ground truth: MIROVA publica **0-1 ALERTA MODIS** en estos 5 vols vs **82 en Láscar**.

## 4. Decisión de Nicolás (estado final deseado)

> *"En el resto de los volcanes está silenciado por algún tema de algoritmo donde las señales
> son más débiles; si nos pasa lo mismo está bien. Quizás sí muestra algo cuando hay incendios,
> pensá en eso."*

- **Silenciado-por-algoritmo** (NO un gate por-volcán): si el algoritmo fiel deja la magnitud
  MODIS en ~0 donde MIROVA también la silencia, está bien.
- **Los incendios SÍ deben mostrarse.** MODIS es excelente sensor de fuego; Chaitén/Villarrica/
  Llaima están en zona boscosa. Un incendio es **focal y fuerte** (un píxel domina, ΔT alto) →
  opuesto al campo difuso. El fix correcto **distingue foco de difuso**, no silencia el volcán.

## 5. Enfoque elegido: A — núcleo focal/contextual del cluster

Restringir la magnitud del cluster a `(píxeles del cluster ∩ contextualmente anómalos) ∪ {pico}`.
El difuso uniforme (no anómalo vs sus 8 vecinos) se cae; el foco discreto (incendio / lava /
Láscar / cráter contextualmente anómalo) se conserva. **El `keep-peak` garantiza que un foco
sub-píxel real nunca caiga a cero** (anti-FN del cráter embebido).

### Enfoques descartados (contra MISSION)
- **B — gate ΔT/focalidad binario**: PASS papers pero umbral afinado a mano (drift). Fallback.
- **C — cap cross-sensor VIIRS**: FAIL MISSION (combina sensores). VIIRS queda como diagnóstico.
- **fondo-local de corona (S107)**: REFUTADO con datos (corona más fría → infla). Ataca el
  fondo (L_bk); este diseño ataca la **selección de píxeles** — palanca ortogonal a la refutada.

## 6. Mecanismo exacto

### Helper puro nuevo en `pipeline/vrp_regimes.py`
```
def cluster_focal_vrp_mw(cluster_pixel_indices, vrp_per_pixel_2d, dnti_ctx_mask,
                         keep_peak=True):
    """Suma el VRP del cluster SOLO sobre píxeles contextualmente anómalos ∪ {pico}.
    Devuelve (vrp_mw, n_focal, degraded). degraded=True si no había ningún píxel
    contextual y se cayó al solo-pico (transparencia, no fallback silencioso)."""
```
- `focal = [rc for rc in cluster_pixel_indices if dnti_ctx_mask[rc]]`
- si `keep_peak`: agregar el píxel de máximo `vrp_per_pixel_2d` del cluster.
- si `focal` vacío (sin contextual y keep_peak=False) → degenera al solo-pico, `degraded=True`.
- `vrp_mw = Σ vrp_per_pixel_2d[focal]`.

### Integración en `process_modis.py` (POST-selección, espejo estructural del S107 §2)
- **Detección, clustering y posición se computan sin cambios** sobre el `hot_mask_2d` completo
  (C1/posición intactas). El cluster primario `_c` se selecciona igual (vent-anchored/vrp_max).
- Cuando `ENABLE_FOCAL_CLUSTER_MAGNITUDE` ON, **antes** del cap D9, recomputar **solo** `_vrp_c`:
  ```
  _vrp_c, _n_focal, _focal_degraded = cluster_focal_vrp_mw(
      _c["pixel_indices"], vrp_per_pixel_2d, dnti_ctx_hot,
      keep_peak=FOCAL_CLUSTER_KEEP_PEAK)
  ```
  Se aplica en los **dos** sitios (eruption `:919-946` y test1 `:1175-1201`) → MODIS uniforme.
- `primary_cluster` conserva `n_pixels`/`centroid_*` del cluster completo (posición intacta);
  solo cambia `vrp_mw`. Diag nuevo: `focal_magnitude` (n_focal, degraded) para auditar.
- Reusa `dnti_ctx_hot` ya computado (`:528/550`, default zeros). NO toca `compute_local_background`
  ni `effective_L_bg` (guard A48: no es fondo-local).

### Flags (`pipeline/profile.py`, default OFF)
- `ENABLE_FOCAL_CLUSTER_MAGNITUDE: bool = False`
- `FOCAL_CLUSTER_KEEP_PEAK: bool = True`

## 7. MISSION — 3 preguntas

1. **¿Está en papers core?** SÍ. El criterio contextual (anómalo vs 8 vecinos) = Coppola 2016a
   Tests 2/3 (dNTI). Sumar solo píxeles alertados = Coppola 2023 Eq.1 + "fundamentally insensitive
   to diffuse heat". Verbo activo: el sistema aplica el umbral contextual automáticamente. → PASS.
2. Cierra divergencia: cara-magnitud de **D11/A69** (MIR/campo absoluto sesga; MIROVA inmune por
   contextual). Alinea con MIROVA. → PASS.
3. Uniforme por sensor (no per-vol, no per-régimen). → consistente con el hecho canónico S99.

**No es un parche per-vol** (anti-A55): es un criterio uniforme que, donde no hay foco resoluble,
da ~0 (como MIROVA), y donde hay foco (incendio/lava/Láscar), lo conserva.

## 8. Plan A/B (3 brazos, criterios A66 PRE-REGISTRADOS)

Perfiles aislados (`data_subdir` propio, A47), reproc GH Actions (MODIS necesita Linux/pyhdf):
- **base**: `ENABLE_FOCAL_CLUSTER_MAGNITUDE=False` (inflado actual).
- **ctx_keeppeak**: ON, `keep_peak=True` (forma recomendada, anti-FN).
- **ctx_pure**: ON, `keep_peak=False` (canario — mide cuánto aporta el pico; si → 0 en estos vols
  confirma "campo topográfico puro sin foco contextual"; en Láscar/foco debe preservar).

Vols: Chaitén, Villarrica, Llaima, Tupungatito, PCC (inflados) + **Láscar (control)**. Ventana =
la del A/B S107 (mismos records inflados).

### Criterios de aceptación (pre-registrados)
- **C1 — detección 0-diffs** en granules COMUNES (no contar cobertura NASA distinta por corrida,
  lección S108). El fix es post-selección → 0 cambios en `triggered_test1`/`n_anomalous`/posición.
- **C2 — inflados curados**: `pc.vrp_mw > 5 → ≤ ~MIROVA` (objetivo: mediana ON/base ≪ 1; acercar a
  la magnitud MODIS-MIROVA = ~0 donde MIROVA no publica). Medir % de los 121 que bajan.
- **C3 — Láscar control preservado**: ratio ON/base ∈ [0.85, 1.15] (foco MODIS real intacto).
- **C4 — foco/incendio sobrevive**: identificar ≥1 noche con foco discreto (Láscar, o un record
  con píxel-pico ≥40% del cluster) y verificar que ON conserva su magnitud (no la mata). Valida
  la restricción de Nicolás (los incendios se muestran).

Veredicto: adoptar el brazo que pase C1+C3+C4 y maximice C2 sin violar C4. Si ctx_pure mata foco
(viola C4) y ctx_keeppeak no (C4 OK), adoptar keep_peak. A18: reproc REAL, no preview offline.

## 9. Riesgos y caveats (A62)

- **Eficacia parcial**: en el path eruption ~la mitad de los píxeles del cluster pueden ser dNTI
  (Chaitén dnti_ctx≈6, cluster≈11) → el filtro podría bajar 7→~3 MW, no →0. El A/B lo mide; si
  insuficiente, el fallback es el brazo `ctx_pure` o un núcleo espacial (B). NO prometer →0 a priori.
- **Lección S106 (fondo-local-NTI)**: a escala local la señal real débil es tan suave como la
  topografía → un criterio contextual podría matar foco real. **Diferencia clave que lo hace
  viable acá**: (a) tocamos MAGNITUD, no detección; (b) la señal real de estos vols la lleva
  VIIRS (que ya reportamos); (c) `keep-peak` + **C3 Láscar** + **C4 incendio** son los controles
  duros. Si C3/C4 fallan → NO adoptar (mismo rigor que la refutación del fondo-local).
- **PCC cirrus (D9/A23)**: el max inflado PCC (60 MW) es path-D cirrus, frente aparte (cap D9).
  El núcleo-focal lo reduce parcialmente pero la causa raíz cirrus queda abierta (D9).
- **Acoplamiento §1 (flip ancla MODIS)**: este fix de magnitud desbloquea el flip (S107 verdict).
  El flip es alto impacto (~2476 destape) + caso especial NdC (MIROVA 0) → su propio A45 + OK Nicolás.

## 10. Archivos tocados

- `pipeline/vrp_regimes.py` — helper `cluster_focal_vrp_mw` (puro).
- `pipeline/process_modis.py` — import + 2 integraciones post-selección (eruption + test1), flag-gated.
- `pipeline/profile.py` — 2 flags default OFF.
- `tests/test_focal_cluster_magnitude.py` — TDD (difuso→pico, foco→conserva, degraded, detección-no-cambia).
- `pipeline/profiles/_modis_focalmag_{base,ctx,ctxpure}.yaml` — A/B (data_subdir aislado).
- `.github/workflows/reproc-s109-modis-focalmag-ab.yml` — reproc (clon de reproc-s107).
- `experiments/_s109_modis_mag/audit_focalmag_ab.py` — audit pre-escrito (C1-C4, granules comunes).
