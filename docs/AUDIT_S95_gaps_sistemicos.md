# AUDIT S95 — Gaps sistémicos (pedido de Nicolás, cierre S94)

**Sesión S95 (2026-05-31).** Auditoría de errores del mismo patrón que el gap Test1
`anomaly_pixels` descubierto en S94 (fix PR #294, aplicado SOLO en `process_viirs.py`),
y del impacto más amplio de los que ya encontramos. Metodología: 5 subagentes en
paralelo (A26), un eje cada uno, con **cross-check independiente** de las afirmaciones
de alto impacto (A48 — un subagente leyó mal el frontend; ver Eje 5).

**Fuente de verdad reproducible** (integridad §0.5): `experiments/_s95_audit/verify_gaps.py`
→ `verify_gaps.json`. NO toca pipeline (A45). Ningún número de este doc está transcrito
a mano — todos salen del script.

> ⚠️ El entorno de esta sesión entrelaza/corrompe stdout multi-línea. Los números aquí
> provienen de `verify_gaps.json` (escrito a disco, no del stdout).

---

## Resumen ejecutivo (qué accionar)

| Eje | Hallazgo | Veredicto | Acción |
|---|---|---|---|
| **1** | Gap Test1 `anomaly_pixels=[]` también en MODIS + VIIRS750 | **REAL, confirmado** | **Portar `build_anomaly_pixels` (A45+TDD+tag).** Único cambio operacional. |
| 2 | Otros "calculado pero no persistido" (A07) | Real pero menor | `nti` per-pixel = OPCIONAL (no lo pide F5'); `vrp_mir_mw_test1_only` diag barato |
| 3 | Campos `*_dist_km` con ancla engañosa (centro vs eff_vent) | **Real, estructural** | Documentar + regla de cálculo para F5' (recomputar desde lat/lon) |
| 4 | Arrastre del gap Test1 | Real, acotado | Re-correr 4 análisis S94 tras el reproc; métricas por-sensor NO contaminadas |
| **5** | F47-style: `distance_class` gatea antes que el cluster, oculta 1401 records | ⚠️ **"0 pérdida" REFUTADO S106 — ver corrección abajo** | Reproc F2 Láscar MODIS (AUDIT_S106 P1.1) |

**El único cambio operacional al pipeline que sale de esta auditoría es el Eje 1**
(portar el helper a los otros 2 procesadores). El Eje 5 es una incoherencia de esquema
real ~~pero sin pérdida medible (0 records MIROVA-confirmados ocultados)~~; su raíz es el
ancla variable del Eje 3 y se decide aparte con brainstorming. Lo demás es documentación
y método de análisis.

> ## ⚠️ CORRECCIÓN S106 (AUDIT_S106 P1.2) — el "0 pérdida de recall" del Eje 5 era un artefacto de método, NO un hecho
>
> La conclusión "0 pérdida de recall, 0 records MIROVA-confirmados ocultados" estaba
> **metodológicamente viciada**: `experiments/_s95_audit/verify_eje5.py:132` contaba los
> confirmados vía `r.get('_mirova_confirmed')` — un flag que **solo existe en runtime del
> frontend y está vacío en disco** (0/18616 records). El "0" estaba garantizado por
> construcción, no medido contra el ground truth (`latest_consolidado.csv`).
>
> El cruce correcto (AUDIT_S106, estratificado por sensor Y por volcán) da: **MODIS Láscar
> pierde ~70/79 alertas que MIROVA SÍ publica** — el píxel suelto cae en el Salar de
> Atacama (16-32 km) y vuelve `distance_class='far'` aunque el `primary_cluster` está en
> el cráter (mediana 1.46 km, coincide con MIROVA 1.41 km). El rescate F47 no dispara
> porque `hotspot_dist<25 km`. NO es categoría A54 (real-no-publicada): MIROVA las publica.
> Es un FN sobre señal confirmada. **Número canónico: ~70 Láscar MODIS** (no 0).
>
> Acción: reproc histórico F2 de Láscar MODIS con el pipeline actual (nadir-fijo) para que
> `distance_class` derive del `primary_cluster`, no del hotspot del Salar — espejo MODIS
> del fix de ancla honesta S106. Discriminador: estratificar por sensor Y por volcán (solo
> Láscar tiene MODIS publicado con regularidad). Ver AUDIT_S106 §2 P1.1/P1.2.

> **NOTA DE INTEGRIDAD (queda registrado, pedido de Nicolás).** En la primera pasada
> declaré el Eje 5 "REFUTADO" basándome en una lectura del frontend que el stdout
> entrelazado del entorno me entregó **corrupta** (faltaba la línea 904). Al releer
> `mirovaEqVrp` con salida limpia confirmé que el gate de `distance_class` corre
> ANTES que el del cluster → el hallazgo del subagente era correcto. Re-verifiqué con
> `verify_eje5.py` (gate exacto + clasificación). Lección: en este entorno, validar
> contra archivo en disco, no contra stdout multilínea (§0.5).

---

## Eje 1 — Gap Test1 `anomaly_pixels` en MODIS + VIIRS750: **REAL**

### El fenómeno (para Nicolás)
El "path Test1" es el camino que captura la señal **sub-píxel débil** de los volcanes de
campo frío (Tupungatito, Villarrica): integra la radiancia de un ROI alrededor del
cráter cuando ningún píxel solo supera el umbral. Es justo el path que más nos importa
para F5'. En S94 vimos que ese path arma la magnitud (`primary_cluster.vrp_mw`) pero
**tira a la basura la lista de píxeles individuales** que ya tenía calculados
(`anomaly_pixels=[]`), aunque esos píxeles existen en memoria. El fix S94 los rescató,
pero **solo en VIIRS 375 m**. MODIS y VIIRS 750 m tienen su propio path Test1 con el
mismo agujero.

### Evidencia (verify_gaps.py, data/mirova_equivalent operacional)
- `build_anomaly_pixels` importado: **solo en `process_viirs.py`** (verificado: imports
  = MODIS 0 / VIIRS750 0 / VIIRS375 1).
- Records `final_hotspot_source=='test1'` con `pc.vrp_mw>0` y `anomaly_pixels==[]`:
  - **MODIS: 18** · **VIIRS750: 108** · VIIRS375: 912 (históricos pre-fix, esperados —
    se llenan al reprocesar con el fix #294 ya mergeado).
  - Distribución MODIS/VIIRS750 en los 11 Tier A (mayoría en Chaitén, Tupungatito,
    PCC, Isluga, Llaima, NdC, PP). Detalle por volcán en `verify_gaps.json`.

### Ubicación del fix (a confirmar al editar, con A45)
- `process_modis.py`: bloque Test1 cluster ~L1106-1154, grid `t1_vrp_2d` ~L1106-1109.
  Variables en scope para el helper: `t1_vrp_2d, lat, lon, dist, bt_mir`.
- `process_viirs_mod.py`: bloque Test1 cluster ~L1036-1086, grid `t1_vrp_2d` ~L1039.
  Variables: `t1_vrp_2d, lat, lon, dist, bt`.
- Patrón de referencia ya mergeado: `process_viirs.py:1486`
  (`anomaly_pixels = build_anomaly_pixels(t1_vrp_2d, lat, lon, dist, bt)`).

### Por qué es ADITIVO (no toca detección ni magnitud)
Solo serializa píxeles **ya calculados** que alimentan `pc.vrp_mw`. `n_anomalous_pixels`
y la magnitud no cambian. Beneficio doble: (a) desbloquea F5' display-first en MODIS/
VIIRS750, (b) arregla el mapa de píxeles del dashboard para records Test1 de esos
sensores. Igual que el PR #294. **Requiere A45: tag defensivo + OK explícito de Nicolás +
TDD** (test sintético: record pure-Test1 → `anomaly_pixels` no vacío).

### Nota sobre el reproc MODIS (cambia algo del plan §1.5)
En `data/_s94_reproc_modis/` el gap **no se materializa** (0 records vacíos): esos
records Test1 pasaron antes por el eruption-path, que ya había poblado `anomaly_pixels`;
recién después `final_hotspot_source` viró a `test1`. El gap MODIS aparece solo en
records **pure-Test1** (sin eruption-path previo) → los 18 operacionales. Implicación:
**re-reprocesar MODIS NO es urgente por este gap** (el reproc actual ya tiene píxeles en
la práctica); conviene hacerlo igual *después* de portar el fix para cerrar los pocos
pure-Test1, pero no bloquea F5'.

---

## Eje 2 — Otros A07 ("calculado pero no persistido")

- **`nti` per-pixel en `anomaly_pixels`** (los 3 procesadores): el NTI 2D ya se computa
  pero `anomaly_pixels` solo serializa `lat/lon/dist_km/bt_k/vrp_mw`. El subagente lo
  marcó "prioritario para F5'". **Lo bajo a OPCIONAL**: el diseño F5'
  (`2026-05-31-f5-coldfield-magnitude-design.md` §2) concluye que el discriminante
  robusto es **espacial** (densidad/radial/trimming desde el vent), y explícitamente
  **debilita** un gate por NTI/ΔL por píxel (la roca tibia-solar y el píxel del cráter
  tienen intensidad parecida). Las 3 variantes D1/D2/D3 solo necesitan `lat/lon/vrp`,
  que ya están. Persistir NTI es "lindo para análisis futuro", no prerequisito.
- **`vrp_mir_mw_test1_only`** (`process_viirs.py:~1456`, ya rotulado `# diag`, nunca
  retornado): separar magnitud Test1 vs eruption-path ayudaría a auditar Villarrica/
  Tupungatito. 1 línea. Opcional, barato.
- **`n_nti_anomalous` ausente en MODIS** (VIIRS375/750 sí lo persisten): asimetría
  cross-sensor; MODIS computa stats NTI pero no el contador. Cierra comparabilidad de
  audits por-path. Opcional.

**Veredicto**: ningún A07 nuevo es bloqueante. Si se toca el pipeline por el Eje 1
(mismo tag/PR), agregar `nti` per-pixel + `vrp_mir_mw_test1_only` es de bajo costo y
deja el schema más completo — pero **no es necesario para F5'**.

---

## Eje 3 — Campos `*_dist_km` con ancla engañosa: **REAL, estructural**

Confirma y profundiza A48/A3. Hallazgo fundacional: el parámetro `vent_lat/vent_lon`
que reciben los 3 procesadores **NO es el vent morfológico** — el caller
(`run_pipeline.py`) lo llena con `get_effective_vent()` (`geo_utils.py`), cuya prioridad
es **(1) mirova_center → (2) vent field → (3) centroide**. Para Tupungatito y
Planchón-Peteroa "vent" = `mirova_center`, con offset ~3-5 km del cráter (A13/A30). Es
A6 en vivo: la firma dice `vent_lat`, el caller pasa otra cosa.

Consecuencias para el schema:
- `anomaly_pixels[].dist_km` y `hotspot_dist_km` miden desde **volcano_lat/lon (centro
  GVP)**.
- `primary_cluster.centroid_dist_km`, `vent_hotspot_dist_km`, `test1_hotspot_dist_km`
  miden desde **eff_vent (= mirova_center cuando existe)**.
- **`final_hotspot_dist_km` cambia de ancla según `final_hotspot_source`**: `eruption`
  → centro GVP; `test1`/`vent` → eff_vent. **El mismo campo no es comparable consigo
  mismo entre records.** Y `distance_class` se decide sobre ese valor de ancla variable.

**Regla operacional para F5' (la que importa)**: NO comparar `anomaly_pixels.dist_km`
(centro) contra `centroid_dist_km` (eff_vent) — en Tupun/PP difieren ~3-5 km y eso
entra como señal espuria. Recalcular las distancias de píxeles desde **un único ancla
explícito** usando `anomaly_pixels[].lat/lon` (las coords absolutas SÍ son confiables;
el offset solo vive en los `*_dist_km` pre-computados). Es el método que ya usó
`experiments/_s87_bloque2/dominant_anomaly.py`. El bloque S95 §0.5 ya anticipaba esto;
queda confirmado en código.

Acción: documentar (este doc) + aplicar la regla en `f5_variants.py`. Rename de campos =
opcional, no urgente (el docstring de `anomaly_pixels.py:24` ya aclara "dist al centro").

---

## Eje 4 — Arrastre del gap Test1: real y acotado

Consumidores de `anomaly_pixels` y su exposición al gap (verificado en código):

| Consumidor | Qué hace | Impacto gap Test1 |
|---|---|---|
| `f5_variants.py`, `f5_magnitude_candidates.py` | suma/poda VRP por píxel ÷ MIROVA | **FALSO** (Tupun/Villarrica → 0×). **Re-correr tras reproc** |
| `viirs_magnitude_diag.py` | report-foco = max píxel | **FALSO** (`return None` en Test1, sesga) |
| `tupungatito_spatial.py` | píxeles dentro de 2 km del cráter | **FALSO/sesgado** si el top-record es Test1 |
| `scripts/generate_villarrica_pruebas.py`, `compare_tif_mirova_vs_ours.py` | TIF/KMZ + R2 pixel-level | **FALSO** si se corrió en Villarrica/Tupun |
| **`per_sensor_metrics.py`, `spatial_audit.py`** | recall/precisión por sensor (usan `sensor`/`pc`, NO la lista) | **SIN IMPACTO** → **los números headline S94 (VIIRS750 83-87%, etc.) NO están contaminados** |
| `frontend` mapa Leaflet | dibuja píxeles; fallback a hotspot/vent si vacío | degradado, no vacío: records Test1 mostraban 1 marcador (vent) en vez de la nube de píxeles. La magnitud/distancia (de `pc`) estaba bien |
| `pipeline/store.py` | filtro pixel H8 / cluster_pixels | sin impacto (consume lo que su propio path produce) |

**Advertencia crítica (confirma §2 del bloque)**: `data/_s94_reproc_viirs/` está
**PRE-FIX** (records con `anomaly_pixels` vacíos). Correr cualquier análisis F5' sobre
esa carpeta **reproduce el gap** → el re-reproc con el fix #294 es prerequisito de TODO
re-cálculo F5'. Lista a re-generar tras el reproc: `f5_variants.py`,
`f5_magnitude_candidates.py`, `viirs_magnitude_diag.py`, `tupungatito_spatial.py`.

---

## Eje 5 — `distance_class` gatea antes que el cluster: **REAL, 0 pérdida de recall**

El subagente afirmó que `mirovaEqVrp` oculta ~1401 records con cluster dentro del
inner_radius porque `distance_class` gatea primero (estilo bug F47 H4). **Es correcto.**

**Código real** (`frontend/index.html:891-912`, verificado con Read limpio; idéntico en
`diario.html`/`mosaico.html`):
```js
function mirovaEqVrp(r, innerKm = 10, includeFar = false) {
  if (!r.primary_cluster) { ...fallback... }
  if (r.distance_class && r.distance_class !== "summit" && !includeFar) return 0;  // L904: gatea PRIMERO
  const pc = r.primary_cluster;
  if (!includeFar && pc.centroid_dist_km != null && pc.centroid_dist_km > innerKm) return 0;  // L908: además
  return pc.vrp_mw;  // (sanity cap omitido)
}
```
El gate de `distance_class` (L904) corre **antes** del gate de cluster (L908, añadido en
el fix S33). Un record con `distance_class='far'` se pone a 0 aunque el centroide del
cluster esté dentro del inner. **El fix S33 cubrió el caso inverso** (`distance_class=
summit` con cluster far) pero NO este.

**Clasificación de los 1401 ocultos** (`verify_eje5.py`, gate exacto + clasificación):
- Por sensor: **MODIS 1121 · VIIRS750 252 · VIIRS375 28** = 1401.
- **MIROVA-confirmados: 0** → **NINGUNA pérdida de recall contra ground truth.**
- `geo_class=='summit'`: **17** → solo 17 de los 1401 son clasificados summit por el
  clasificador geométrico rico (anclado a features reales en `volcanic_features.yaml`)
  pero ocultados por `distance_class='far'`: esos 17 son la incoherencia F47 genuina
  (cluster summit escondido). Los otros 1384 tienen `geo_class` NO-summit → el
  clasificador rico coincide con `distance_class='far'`. El campo `centroid_dist_km ≤
  inner` los daba "dentro" porque se ancla a `eff_vent` = `mirova_center`, con offset
  ~3-5 km del cráter en Tupun/PP (**el problema del Eje 3 manifestándose acá**).
- 61 se ocultarían **igual** por el filtro físico de artefacto térmico (cirrus/campo
  difuso). 1340 quedan ocultados **solo** por esta incoherencia, ninguno confirmado.
- `distance_class` de los 1401: todos `'far'`. `vrp==5.0` (piso MODIS exacto): 37.

**Veredicto matizado**: hay una **incoherencia de esquema real** (`distance_class`,
píxel single con ancla variable del Eje 3, gatea antes que el cluster) que oculta 1401
records. **PERO no causa pérdida medible de recall**: 0 MIROVA-confirmados. Solo 17 son
geo_class summit (la incoherencia F47 genuina, no confirmados por MIROVA); los otros
1384 son no-summit también por el clasificador rico. Es una **fragilidad/olor de
correctitud**, no una pérdida de detección validada. La raíz compartida con el Eje 3
(ancla) sugiere atacarlos juntos: hacer que `distance_class` se derive del cluster
(coherente con `geo_class`) en vez del píxel single con ancla variable. **NO accionar
reactivamente** (disciplina anti-drift S86/A55) — requiere brainstorming + clasificación
A54 de qué categoría (b/d) son esos records antes de cualquier cambio. Candidato a item
S95+/backlog, no a esta sesión.

---

## Decisiones para Nicolás

1. **Eje 1 (A45)**: ¿autorizás portar `build_anomaly_pixels` a `process_modis.py` y
   `process_viirs_mod.py`? Es aditivo, con tag defensivo + TDD, igual que PR #294.
   (Es el prerequisito de F5' display-first en MODIS/VIIRS750.)
2. **Eje 2**: ¿agrego `nti` per-pixel + `vrp_mir_mw_test1_only` en el mismo PR (schema
   más completo) o lo dejo para después? (No es necesario para F5'.)
3. Ejes 3/4/5: ya documentados, sin cambio de pipeline. La regla del Eje 3 se aplica al
   calibrar F5'.

## Escudo anti-drift
NO gate t_bg ciego (S86). NO ocultar VIIRS750 (MIROVA lo usa). NO tocar detección.
NO co-validación VIIRS (borra reales). Eje 5 = no tocar (no hay bug). Calibrar F5' solo
sobre data reprocesada CON el fix.
