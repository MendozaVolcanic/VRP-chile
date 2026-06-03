# S99 — Mecanismo del ~19× de Tupungatito (auditoría ESPACIAL, A61)

**Objetivo**: confirmar con datos qué *path* marca los píxeles de más y **dónde caen
espacialmente**, para fundamentar el brainstorm del fix.

**Read-only.** Datos: `data/mirova_equivalent/Tupungatito.json` (1291 records, post-fix-ancla
S98 → todo anclado al cráter). Cráter (vent) = (-33.389044, -69.826374), `inner_radius_km=7`,
Núcleo F5' = 0.75 km. Scripts: `audit_tupun.py`, `tif_analysis.py`. Números canónicos en
`canonical_numbers.json` / `tif_analysis.json` (verificados doc==JSON por `verify.py`).

---

## Reconciliación de métricas (necesaria antes de leer los números)

- El "58 px → 100 px" del handoff S98 es **`primary_cluster.n_pixels`**, NO `n_anomalous_pixels`.
  `n_anomalous_pixels` es un campo *scene-wide* que en VIIRS375 casi siempre vale 0–7 (ruido).
- Los 514 records VIIRS375 (sin sufijo `_750`) son el sensor operacional (caballo de batalla).
- **460/514 tienen lista `anomaly_pixels` poblada**, con un **cap de 100 elementos** (los clusters
  reales pueden ser >100, ej. `pc.n_pixels=101`). Esa lista ES la huella espacial del cluster.

---

## 1. ¿Qué path marca los píxeles de más? — Limitación + hallazgo

**Limitación de schema**: `anomaly_pixels` persiste solo `lat/lon/dist_km/bt_k/vrp_mw` —
**NO hay path por píxel**. Los contadores de path viven a nivel record (`diag_n_dnti_ctx_path`,
`diag_n_bt_path`, `diag_n_nti_path`, `diag_n_eti_path`).

**Hallazgo clave que redirige la pregunta**: los **258/258** records VIIRS375 con cluster
grande (`pc.n_pixels≥20`) tienen **`triggered_test1=True`** y **`diag_n_first_pass_pixels=0`**.
Es decir, los píxeles del cluster grande **no vienen del first-pass por paths A/B/C/D** — vienen
del **Test1 integrado-ROI** (Coppola 2015), que recaptura píxeles por contraste ΔL dentro de la
ROI sin pasar por el conteo de paths. Por eso los `diag_n_*_path` de los records grandes son
todos ~0 (mediana dNTI-ctx=2, resto=0): **no es que el path D marque de más; es que Test1
levanta un disco de píxeles fríos de glaciar por contraste con un fondo aún más frío.**

Conclusión §1: el path responsable **no es dNTI-contextual first-pass** sino el **Test1
integrado-ROI**. El "path D" del handoff era una hipótesis razonable pero los datos la matizan:
en VIIRS375 grande domina Test1.

**Evolución estacional del cluster (VIIRS375, mediana mensual)** — el cluster explota en abril:

| Mes | n records | `pc.n_pixels` med | `pc.vrp_mw` med |
|---|---|---|---|
| 2026-01 | 12 | 3 | 0.15 |
| 2026-02 | 118 | 2 | 0.17 |
| 2026-03 | 124 | 2 | 0.20 |
| **2026-04** | 122 | **23** | 0.48 |
| **2026-05** | 133 | **45** | **1.82** |
| 2026-06 | 5 | 3 | 0.10 |

(MIROVA reporta ~0.2 MW estable → 1.82/0.2 ≈ ~9× mediano en mayo; picos individuales ~19×.)

## 2. ESPACIAL (A61): ¿anillo/halo o foco compacto?

Marzo (record chico, 1 px) vs Abril/Mayo (record grande, 100 px):

| Régimen | n anomaly_pixels | dist→cráter (km) | en Núcleo 0.75 km | pc.vrp_mw | t_bg_k |
|---|---|---|---|---|---|
| **Marzo (chico)** ej. 03-01 06:06 | 1 | 0.09 | 1/1 | 0.079 | 270.3 |
| **Abril (grande)** 04-15 05:42 | 100 | min 0.23 / **med 2.15** / max 2.99 | **8/100** | 5.0 | 264.8 |
| **Abril (grande)** 04-20 05:48 | 100 | min 0.16 / **med 2.07** / max 2.97 | **11/100** | 2.20 | 263.8 |

**Agregado Abril+Mayo (n=183 records con ≥20 anomaly_pixels)**: en promedio **solo 7.3 %** de
los píxeles del cluster caen dentro del Núcleo 0.75 km; la **mediana de la mediana de distancias**
es **2.14 km**. El 100 % cae dentro del inner de 7 km, pero distribuido como un **disco/halo de
~0.1 a 3.0 km alrededor del cráter** — NO un foco compacto. BT de esos píxeles 250–274 K (frío),
es decir mosaico nieve/roca de glaciar, no lava. El centroide del cluster sí queda cerca del
cráter (centroid_dist mediana 1.1–1.2 km en todos los meses) **porque el halo es aproximadamente
simétrico** — el centroide engaña; la masa de píxeles está en el anillo, no en el centro.

→ Marzo = **foco compacto en el cráter** (consistente con MIROVA ~0.2 MW). Abril/Mayo = **halo
nival difuso** que infla la SUMA de VRP.

## 3. ¿Ayudaría un gate por t_bg_k?

Records grandes (`pc.n_pixels≥20`, n=258): `t_bg_k` **min 261.1 / mediana 266.1 / max 273.6 K**.
**235/258 (91 %) están por debajo de 270 K**; 23 entre 270–274 K; **0 por encima de 290 K**.

- El gate cirrus existente (display, `t_max<273 ∧ VRP>10 ∧ no-confirmado`) **NO** los agarra:
  estos no son cirrus (no son incoherentes; son señal real de glaciar) y muchos tienen VRP<10.
- Un gate "duro" por `t_bg<270` **dispararía sobre 91 % de los records grandes** — pero también
  sobre los chicos de invierno de Marzo (270.3–270.9 K, ¡que son los CORRECTOS!). El t_bg de
  fondo es frío en TODO el invierno, esté el cluster inflado o no. **t_bg solo no discrimina**
  halo-inflado de foco-correcto. El discriminante es **espacial** (dispersión del cluster), no
  térmico-de-fondo. (Coincide con A54/S86: el gate por t_bg fue refutado.)

## 4. ¿Qué ve el TIF MIROVA? (A24 reconfirmado empíricamente)

6 TIFs VIIRS375 recientes (Mayo 19–20) de `../mirova-tif-archive/data/tif/Tupungatito/`
(rasterio 1.5.0 OK):

- **~17,900 píxeles positivos** por TIF, sumando **>1000 "MW"** (hasta 4374). El **pico** del
  campo está a **13–35 km del cráter** (¡fuera del volcán!).
- Esto confirma **A24**: el TIF "Last" es el **campo de radiancia de toda la grilla 51×51 km**
  (topografía/escena), **NO** el cluster seleccionado. La suma del TIF **no** es el VRP de MIROVA.
- ~1095 píxeles positivos caen dentro de 7 km del cráter, 14 dentro de 0.75 km — es el campo de
  fondo del summit, no un foco. **El TIF no sirve como ground-truth per-píxel del cluster.**
- El VRP que MIROVA reporta (~0.2 MW) sale de su **selección de cluster específica**, invisible
  en el TIF. MIROVA ve **1 foco compacto** (su número estable ~0.2 MW); nosotros sumamos un
  **disco de ~100 px** → de ahí el factor.

## 5. Sub-pregunta para el fix: ¿el Núcleo 0.75 km es físicamente correcto?

En los records grandes Abril/Mayo, **solo ~7–11 de cada 100 px del cluster caen dentro de
0.75 km del cráter**; el resto (~90 %) es halo lejano (1–3 km). Recortar al Núcleo 0.75 km
**elimina exactamente el halo nival y conserva el puñado de píxeles peri-cratéricos** — es decir,
**el recorte del Núcleo es físicamente correcto** para este modo de falla: aísla el foco real
(donde MIROVA reporta) y descarta el anillo de contraste nieve/roca. Marzo (foco de 1 px a
0.1 km) sobrevive intacto al recorte. Esto valida la dirección F5'-Núcleo como mitigación.

---

### Síntesis del mecanismo (geológico → pipeline)

A 5682 m el cráter de Tupungatito está rodeado de glaciar. En verano (ene–mar) el fondo es nieve
homogénea y el único contraste térmico real es el cráter → cluster de 1–3 px, VRP ~0.2 MW = MIROVA.
Desde **abril** entra el invierno austral: el reborde del glaciar se vuelve un **mosaico nieve/roca
expuesta**, y cada parche de roca relativamente "tibio" (250–274 K) contrasta con la nieve aún más
fría. El **Test1 integrado-ROI** lee ese contraste como anomalía y recaptura un **disco de ~100 px**
en un anillo de 0.1–3 km. Como el VRP del cluster es la **SUMA** de esos píxeles, la magnitud sube
de ~0.2 a 2–5 MW (mediana mayo 1.82 MW vs ~0.2 de MIROVA → ~9–19×). MIROVA no se infla porque
selecciona un foco compacto, no la suma del campo.

**El discriminante NO es el path ni el t_bg de fondo; es la DISPERSIÓN ESPACIAL del cluster.**
El Núcleo 0.75 km recorta correctamente el halo. Fix candidato S99 = brainstorm sobre recorte
espacial del cluster (no gate térmico, no co-validación por path).
