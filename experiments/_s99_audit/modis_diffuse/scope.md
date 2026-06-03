# S99 — Scope: campo MODIS sobre-estimado (records "cientos de MW" que MIROVA no reporta)

**Fecha**: 2026-06-03 · **Autor**: subagente audit (read-only) · **Fuente de números**: `audit.py` → `audit_result.json` (ningún número a mano).
**Alcance**: caracterizar y scopear, NO implementar. Disciplina systematic-debugging.

## Resumen ejecutivo (<500 palabras)

Hay un frente MODIS **separado** del de VIIRS375/Test1. Son records con `pc.vrp_mw` de decenas a cientos de MW que MIROVA **no** publica desde MODIS. Total en los 11 Tier A: **15 records >50 MW** y **105 >20 MW**.

**Corrección a la premisa del prompt**: estos NO vienen del *eruption-path por umbral BT*. El `final_hotspot_source="eruption"` es solo la etiqueta del modo-cluster; los píxeles vienen de **path D (dNTI contextual)** + fuerte **second-pass recapture**. En todos los >50 MW: `diag_n_bt_path=0`, `diag_n_eti_path=0`, `diag_n_nti_path=0`; toda la energía es `diag_n_dnti_ctx_path` (13–82 px) + recaptura (72–127 px). **0 de los 105 >20 MW disparó Test1.** Es la **misma familia A23/D9** (path D sobre fondo frío) que el cirrus, pero en **régimen de escena tibia**, no la suma BT que el prompt suponía.

### Tabla por volcán (records MODIS, ventana actual del JSON operacional)

| Volcán | MODIS >50 | MODIS >20 | máx pc.vrp (MW) | path dominante | MIROVA MODIS reporta? (CONS ALERTA / OCR) |
|---|--:|--:|--:|---|---|
| PuyehueCordonCaulle | **6** | 19 | **342.2** | dnti_ctx (19/19) | **0** / 0 |
| Tupungatito | **5** | 15 | **133.5** | dnti_ctx (13) | **0** / 0 |
| Chaiten | **4** | 25 | 93.9 | dnti_ctx (19) | 1 (VRP 1MW) / 0 |
| NevadosDeChillan | 0 | 10 | 49.1 | dnti_ctx (7) | 1 (VRP 1MW) / 1 (1MW) |
| Villarrica | 0 | 17 | 32.4 | dnti_ctx (11) | 1 (1MW) / 0 |
| Llaima | 0 | 6 | 38.8 | dnti_ctx (4) | 0 / 0 |
| Lascar | 0 | 5 | 43.6 | dnti_ctx (4) | **78 (1–3 MW)** / 23 (1–3 MW) |
| Copahue | 0 | 2 | 38.6 | dnti_ctx (2) | 0 / 0 |
| PlanchonPeteroa | 0 | 3 | 43.6 | dnti_ctx (1) | 0 / 0 |
| Isluga | 0 | 2 | 22.7 | dnti_ctx (2) | 0 / 0 |
| Lastarria | 0 | 1 | 22.0 | dnti_ctx (1) | 0 / 0 |

**Ground truth MIROVA (latest_consolidado.csv `Tipo_Registro=ALERTA_TERMICA` + OCR)**: MIROVA desde MODIS **solo** reporta Láscar (78 ALERTA, 1–3 MW) y singletons de 1 MW en Chaitén/NdC/Villarrica. En los peores (PCC, Tupungatito) MIROVA-MODIS = **0**. Donde sí reporta (Láscar) lo hace a **1–3 MW**, dos-tres órdenes de magnitud bajo nuestros 50–342 MW. Confirma: estos picos MODIS no tienen correlato MIROVA.

### Clasificación (S86 a/b/c/d)

La **magnitud** es **cat (d) artefacto**, aunque pueda haber un núcleo cat (b) sin resolver debajo. Evidencia (PCC top 342 MW, 2026-04-26): 95 píxeles del cluster repartidos **2.4–25 km** del cráter (mediana **16.3 km**), solo **5 px ≤5 km**; BT píxeles 270–281 K (apenas sobre el fondo ~274 K). Es un **campo de escena tibio** (valle/bosque otoñal sobre ROI frío) que path D lee como anomalía local y la suma da cientos de MW. MODIS 1 km **no resuelve** el lacolito/lava-lake sub-píxel que MIROVA sí ve con VIIRS375 → el número MODIS no representa potencia radiante de un foco real. Mismo veredicto que S91/S93 warm-scene PCC (reclasificado b→d *para la magnitud*).

### Por qué el filtro display NO los atrapa

`isDiffuseFieldArtifact` (index.html:1092) exige **`t_max<278.15K` (5°C) ∧ `n_pixels≥100` ∧ `vrp≥50` ∧ `vrp/px<1.0`**. Estos records **fallan las 3 compuertas a la vez**: t_max **283.8–290.0 K** (10–17°C, escena tibia, no fría); npix **5–86** (compacto, no campo de cientos); vrp/px **2.61–16.69** (energía concentrada, no diluida). El filtro (y el `isCirrusArtifact`, t_max<0°C) fue diseñado para el **régimen frío** (cirrus/nieve, cientos de px tibios apenas). Estos son un **tercer régimen**: escena tibia + cluster compacto + alta energía/px. Gap = ninguna compuerta cold-scene los cubre.

### Opciones de fix (rankeadas, NO implementar)

1. **(a) Display — extender el discriminante a régimen tibio** *(menor riesgo, recomendado primero)*. Añadir rama "campo tibio sobre-estimado": p.ej. dominado por path D (`diag_n_dnti_ctx_path` alta, `n_bt=n_eti=n_nti=0`) ∧ dispersión espacial alta (mediana `dist_km` de píxeles ≫ inner) ∧ sin confirmación MIROVA. **Pro**: display-only, no toca pipeline NRT (A45), reversible, replicable en 3 vistas (S92 L5). **Contra/riesgo**: umbral mal puesto puede ocultar un foco real débil — el discriminante DEBE ser espacial (dispersión), NO solo magnitud (A61); validar 0 reales atrapadas vs MIROVA antes de mergear. No requiere Linux.
2. **(c) Co-validación SOLO-MODIS** *(raíz parcial, riesgo medio)*. Exigir respaldo VIIRS375 ±ventana para publicar magnitud MODIS (alineado con plan S93 F3, "co-validación solo MODIS es segura"). **Pro**: ataca la causa (MODIS no resuelve el foco; VIIRS375 sí). **Contra**: cambio de pipeline → A45 (tag + OK Nicolás + TDD); puede borrar el escaso MODIS real (Láscar 1–3 MW) si la ventana no matchea; **requiere reproc**.
3. **(b) Pipeline — recorte de compacidad al path D/cluster en MODIS** *(raíz, mayor riesgo)*. Penalizar/excluir píxeles path-D dispersos del cluster (compacidad espacial). **Pro**: corrige la magnitud en origen. **Contra**: toca `process_modis.py`/clustering (A45 + brainstorming obligatorio); alto riesgo de romper semántica VRP en los 11 vols (A55 anti-patrón "gate por path"); **MODIS NO corre local en Windows (pyhdf roto)** → todo A/B exige reproc GH Actions Linux.

**Recomendación de orden**: (a) display ya, mientras se diseña (c) co-validación-solo-MODIS con A45 + reproc GH. (b) pipeline solo si (a)+(c) no bastan.
