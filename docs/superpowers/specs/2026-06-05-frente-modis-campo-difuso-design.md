# Frente MODIS — campo difuso sobre-estimado (design doc S101)

**Fecha**: 2026-06-05 · **Sesión**: S101 · **Estado**: DISEÑO (no implementado) ·
**Disciplina**: superpowers-brainstorming + A45 (pipeline NRT). Pendiente OK Nicolás.
**Fuente de números**: `experiments/_s99_audit/modis_diffuse/*.py` (S91, ningún número a mano).

---

## 1. Objetivo y misión

Clon MIROVA NRT. El sensor **MODIS** produce records de decenas-cientos de MW
(PCC 342, Tupungatito 133, Chaitén 94) que **MIROVA no publica**. Hay que hacer que
nuestro MODIS sea **tan parco como MIROVA**, sin ocultar detecciones reales (A55).

**MISSION 3 preguntas** (aplicadas): (1) ¿MIROVA lo hace? → MIROVA reporta MODIS muy
parco (ver §2); suprimir el campo difuso ACERCA a MIROVA. (2) ¿Resuelve un drift propio?
→ Sí, el path D contextual + second-pass sobre escena fría es amplificación nuestra.
(3) ¿Evidencia? → §2-§4, todo verificado. **Las 3 dan SÍ.**

---

## 2. Target de fidelidad: qué detecta MIROVA desde MODIS (VERIFICADO)

Fuente: `latest_consolidado.csv` (ALERTA_TERMICA) + OCR, período completo ene–jun 2026.
Script: caracterización en la sesión S101 (consolidado + OCR cruzados).

| Volcán | nº alertas MODIS | VRP (min/med/max) MW | Dist (med/max) km |
|---|--:|---|---|
| **Láscar** | 78 (+30 OCR) | 0.2 / 1.3 / **3.9** (OCR hasta 15) | 1.4 / 2.2 |
| Villarrica | 1 | 1.8 | 2.0 |
| Chaitén | 1 | 0.7 | 3.6 |
| Nevados de Chillán | 1 (+1 OCR) | 1.1 | 1.4 |
| Copahue | 0 (+1 OCR) | 2.0 (OCR) | — |
| Llaima | 0 (+1 OCR) | 1.0 (OCR) | — |
| **TOTAL** | **81 CONS** | | |
| Cero MODIS | **Isluga, Lastarria, PP, PCC, Tupungatito** | — | — |

**Patrón target**: MIROVA-MODIS es SIEMPRE magnitud baja (≤4 MW CONS, ≤15 OCR),
SIEMPRE al cráter (≤3.6 km), clase Muy Bajo/Bajo. Láscar concentra el 96%. **PCC y
Tupungatito = 0 MODIS en 5 meses.** Nuestro pipeline les pone 342 y 133 MW.

---

## 3. El frente es artefacto (VERIFICADO, eje espacial A61 + TIF A24)

### 3.1 TIF de MIROVA (`../mirova-tif-archive`, mayo 2026)
PCC 54, Tupun 48, Láscar 41 TIF MODIS leídos con rasterio. En los 3 volcanes los
píxeles de mayor radiancia caen en el **borde del recuadro (~22–28 km del cráter)**;
**0/12 píxeles top dentro de 3 km del cráter, incluido Láscar**. Regla A24: el TIF es
campo de radiancia (topografía/escena), NO VRP sumable. **Conclusión clave: en MODIS
NO hay foco al cráter que rescatar, ni en Láscar.** La señal térmica real de estos
volcanes vive en VIIRS375. Por eso MIROVA publica MODIS tan parco.

### 3.2 Mecanismo del pipeline (eje código + docs)
`process_modis.py`: el VRP MODIS alto viene de **path D (dNTI contextual, kernel
8-vecinos, `process_modis.py:498-539`)** + **first-pass Tests 2∧3** + **second-pass
recapture** (`:711-749`) sobre **escena tibia** (t_bg ~274 K). 0 de los records >50 MW
dispararon Test1/BT/ETI/NTI; toda la energía es dNTI_ctx + recaptura. El **cap D9**
(5 MW) NO los ataja porque está gateado a `t_bg<270K` (cirrus frío) y estos están a
~274 K. El **gate intra-radio path D** (S83/S84, eb68f8c4) tampoco, porque PCC tiene
`inner_radius_km=20` → el campo difuso a 16 km cabe dentro.

### 3.3 Offsets KMZ confirmados
Tupungatito **4.86 km**, PCC **7.57 km**, PP **2.02 km** (mirova_center vs cráter).
Motiva que cualquier referencia geométrica use el cráter (vent_lat), no mirova_center.

---

## 4. Pruebas hechas y descartes (todo verificado, A62 aplicado a mí mismo)

| Approach probado | Resultado | Por qué se descarta |
|---|---|---|
| **Discriminante térmico** (px caliente cerca cráter) | bt_max ~278–289 K en TODOS, incl. Láscar; 0% >315 K | MODIS 1 km nunca ve píxel caliente puro (foco sub-píxel promediado con km² de roca/nieve). Ciego por temperatura. |
| **Núcleo F5' (display)** | Deshabilitado para MODIS por diseño (`index.html:1048`) | F5' calibrado solo VIIRS375; en MODIS el ancla "píxel máx energía" cae en píxel coarse lejano. |
| **Núcleo-al-cráter** (sumar px ≤2–3 km del cráter) | Colapsa difuso de Tupun/NdC/Copahue/Llaima/Isluga; residuo en PCC/Chaitén/Lastarria/PP | **Borraría actividad de flanco real** (lacolito PCC, fisuras) — A55. El cráter no es el único centro eruptivo. |
| **Compacidad sobre `anomaly_pixels`** | Records MIROVA-confirmados tienen compacidad 0.01 = igual que artefactos | `anomaly_pixels` = top-100 de la ESCENA, no los píxeles del cluster (A46/A07). Métrica contaminada. |
| **Cualquier fix de display** | `primary_cluster` guarda solo agregados (n_pixels, vrp, centroide); NO la lista de píxeles ni dispersión | El frontend no tiene la geometría del cluster → no puede discriminar foco vs difuso. **Descarta display-first.** |

**Hallazgo del acople (#1 ↔ magnitud)**: de 110 records MODIS >20 MW, **88 están
ocultos HOY** por `distance_class="far"` corrupto (cluster cerca del cráter pero
etiqueta del hotspot suelto). Arreglar #1 solo los DESTAPARÍA inflados. → la magnitud
debe resolverse **antes o junto** con #1.

---

## 4bis. Refinación S101 (descartes adicionales — NINGÚN discriminante post-hoc sirve)

Tras "refinar el diseño primero" (decisión Nicolás), se probaron y **descartaron**
los discriminantes post-hoc restantes. Scripts: `reconstruct_cluster_dispersion.py`,
`test_covalidation.py`.

| Discriminante | Resultado | Veredicto |
|---|---|---|
| **Dispersión del cluster** (reconstruido por single-linkage) | Inflados >20MW: radio_p90 **0.0 km**, igual de compactos que los reales | **El cluster artefacto ES compacto** (blob de px tibios de contraste de escena, no esparcido). La dispersión no separa. Además NO validable offline (schema no persiste px del cluster, A46/A07). |
| **Co-validación VIIRS375** (±1d, summit) | Reales 124/124 co-validados; inflados **107/107 también** | VIIRS375 detecta crónicamente (Tupun/PCC casi diario) → "hay VIIRS cerca" es casi siempre cierto → no filtra. |

**Lo único que separa es la magnitud cruda** (MIROVA-MODIS ≤15 MW; inflados >20). Pero
un cap simple no satisface (dejaría PCC en 5 MW donde MIROVA = 0). → el problema NO es
de clasificación post-hoc, es de **raíz**: por qué el pipeline asigna decenas-cientos de
MW a un blob compacto de px apenas tibios (~280 K).

### Causa raíz — DOS palancas (no un discriminante)
1. **Detección**: path D dNTI contextual + second-pass marca blobs compactos de px
   tibios (contraste local de escena). MIROVA genera FP análogos pero los descarta
   (papers sp426_5 L689-696: "típicamente <5 MW, por inspección visual"). Los nuestros
   son >20–342 MW, NO <5 → el problema es la magnitud que les asignamos.
2. **Magnitud — corrección sec³(θ)** (`process_modis.py:341-343`, flag
   `ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS` default **False** = sec³ activo). MIROVA
   resamplea a grid 1 km de área constante y NO usa sec³ (papers, eje A). Para los
   volcanes del SUR (PCC/Tupun) las pasadas MODIS son off-nadir → sec³ infla el área
   3–5× → infla el VRP del campo difuso en la misma proporción (PCC ~70 MW nadir →
   ~342 MW off-nadir). El clon literal sería `enable_nadir_fixed_pixel_area_modis:true`
   (comentario del propio código: "clon literal MIROVA"). **PERO** el WOOSTER_COEFF
   18.9 se calibró empíricamente con sec³ activo (S14, error ≤0.17% vs OSF) → cambiarlo
   exige **re-validar el coeficiente** contra OSF. NO es toggle inocuo (A63: no romper
   calibración S14).

## 5. Conclusión de diseño (REVISADA tras refinación)

No hay discriminante post-hoc (térmico/geométrico/co-validación todos descartados con
datos). El fix ataca las **dos palancas de raíz** en el pipeline (A45 + reproc MODIS
GH/Linux — pyhdf roto local), con cuidado de calibración:

- **Palanca magnitud (sec³)**: medir, con un reproc A/B `nadir_fixed` ON/OFF, cuánto del
  inflado es sec³ off-nadir. Si es la mayor parte, evaluar adoptar nadir-fijo MODIS
  **con re-validación del WOOSTER_COEFF contra OSF** (no solo flip el flag).
- **Palanca detección (path D)**: si tras nadir-fijo aún quedan blobs >5 MV de escena,
  evaluar acotar path D/second-pass (umbral C2 más estricto en ROI2 scene, o gate por
  inner efectivo más chico estilo ROI1 5 km — no el inner=20 de PCC). Riesgo A55/recall.
- **distance_class del cluster (#1)**: sigue siendo el fix de ~1 línea, va junto (§5.1
  abajo) porque destaparía los inflados si va solo.

El fix tiene **dos sub-fixes acoplados** (mismo reproc):

### 5.1 distance_class del cluster (#1) — raíz, ~1 línea
`process_modis.py:1054-1056`: cambiar `final_hotspot_dist_km` →
`primary_cluster.centroid_dist_km` (el cluster ya es vent_anchored al cráter). Elimina
la corrupción "deriva del hotspot suelto". **NO se puede mergear solo** (destaparía los
88 inflados). Va con 5.2. Verificación pixel-level obligatoria (reclasifica summit/far
en los 11 → puede mover recall).

### 5.2 Magnitud = supresión del campo difuso por dispersión del cluster — raíz
En el punto donde se arma `primary_cluster` (`process_modis.py:898-919` normal,
`:1131-1162` Test1; cuidado A49 con el `return` en :1164): medir la **dispersión de
los píxeles del cluster** (p.ej. fracción de energía dentro de R_core del centro de masa
de energía del cluster, o desviación espacial ponderada). Si el cluster es difuso
(dispersión alta, sin concentración) → **suprimir/capar** la magnitud (no publicar como
detección summit). Si es compacto (foco real, cráter o flanco) → conservar.
Persistir un campo diagnóstico (`cluster_dispersion_km` o `compactness_frac`) para que
el display y las auditorías lo usen.

**Decisión abierta a validar con reproc** (no se pudo offline — schema no persiste los
píxeles del cluster): umbral de dispersión y si se suprime (magnitud→0/cap) o se marca.

---

## 6. Criterios de aceptación (vs target §2)

1. PCC, Tupungatito: 0 records MODIS publicados con VRP alto (target MIROVA = 0).
2. Láscar: conserva sus ~78 detecciones MODIS a magnitud ≤4 MW (no romper el real).
3. Singletons (Villarrica/Chaitén/NdC/Copahue/Llaima): conservar el día real, suprimir
   el resto.
4. **0 pérdida de recall vs MIROVA** en los 11 (verif pixel-level, R3 audit independiente).
5. distance_class coherente con el cluster en los 11 (no más "far pero cerca" ni
   "summit a 21 km").
6. Replicar el efecto en las 3 vistas del dashboard (S92 L5).

---

## 7. Riesgos y pre-mortem

- **A55 (anti-patrón gate por path)**: el discriminante es ESPACIAL (dispersión), no
  "gate por path D" — evita el anti-patrón. Aun así clasificar categoría física (S86
  a/b/c/d) de lo que se suprime ANTES de mergear.
- **A19 (no universal)**: la dispersión puede comportarse distinto por volcán
  (glaciar Tupun vs desierto Lascar). Validar per-vol, no extrapolar.
- **Recall (#1)**: derivar distance_class del cluster reclasifica los 11. Riesgo de
  mover recall real. Mitigación: verif pixel-level + reproc A/B enabled/disabled.
- **No revertir (A63)**: cap D9, gate intra-radio path D, vent_anchored clustering,
  fix ancla S98, local_kernel_bg per-vol (Tupun excluido). El fix coexiste, no reemplaza.
- **Reproc**: MODIS no corre local → A/B en GH Actions (~1–2 h por iteración). Diseñar
  el discriminante con cuidado antes de gastar reprocs (A2).
- **Pre-mortem**: si el umbral de dispersión es muy agresivo, borra Láscar real (cat-b);
  si es muy laxo, deja pasar PCC. Mitigación: barrer umbrales en UN reproc multi-valor
  y elegir contra el target §2.

---

## 8. Plan de implementación (cuando Nicolás dé OK — A45)

1. **TDD**: tests sintéticos en `tests/` — cluster compacto (conserva) vs disperso
   (suprime), antes del fix (R1/R7).
2. Tag defensivo `pre-s101-modis-diffuse` + push (A45).
3. Implementar 5.1 + 5.2 con flag de perfil `enable_modis_dispersion_gate`
   (default OFF) + persistir `cluster_dispersion_*`.
4. A/B reproc GH Actions: 2 perfiles enabled/disabled, los 4-5 vols afectados
   (PCC/Tupun/Chaitén/Villarrica + Láscar control), `data_subdir` aislado.
5. Auditar vs target §2 (R3 independiente) + verif pixel-level + R2 vs TIF.
6. Decidir umbral; si pasa criterios §6 → adopción (flip flag) + reproc histórico +
   promover + 3 vistas + R8 público.

**NO implementar sin**: OK explícito de Nicolás + el umbral diseñado. El frente es
nice-to-have operacional (el dashboard hoy oculta los inflados por el `far` corrupto —
frágil pero funcional); no es bloqueante. Calidad > velocidad.

---

## 9. Pendiente de decisión (para revisión de Nicolás)

- **Enfoque del 5.2**: ¿suprimir la magnitud (→0/cap) del cluster difuso, o solo
  marcarlo y dejar que el display lo oculte (usando el campo persistido)?
- **¿Detección o magnitud?**: ¿atacamos solo la magnitud (cap por dispersión, conserva
  el record) o también la detección (que path D/second-pass no detecten el campo difuso
  en escena fría)? Lo segundo es más raíz pero más riesgoso para recall.
- **Umbral de dispersión**: a determinar con reproc multi-valor.
