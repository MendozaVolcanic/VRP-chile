# Pre-veredicto A/B MODIS fondo-local (S108) — clasificación A54 de inflados

**Fuente**: `classify_modis_inflated.py` sobre data base (flip OFF). Run A/B: 27480234385.

## Qué SON los 121 inflados MODIS (pc.vrp_mw > 5)
Corregido sesgo A48/A68 (usar `pc.centroid_dist_km` del cluster, NO `final_hotspot_dist_km`
= píxel suelto del Salar, patrón D12):

| Vol | n | pc.vrp med | dist_CLUSTER | dist_pixel | ΔT med | cat-d | cat-b(MIROVA) | ambig | max pc.vrp |
|---|---|---|---|---|---|---|---|---|---|
| Chaiten | 38 | 7.1 | 1.14 km | 15.3 km | 10.0 K | 17 | 6 | 15 | 18.6 |
| Villarrica | 28 | 7.1 | 2.36 km | 19.8 km | 10.4 K | 22 | 1 | 5 | 21.0 |
| PCC | 27 | 7.1 | 2.50 km | 18.8 km | 12.2 K | 13 | 0 | 14 | **60.2** (cirrus D9) |
| Tupungatito | 18 | 8.1 | 2.79 km | 21.1 km | 14.4 K | 0 | **11** | 7 | 13.6 |
| Llaima | 9 | 7.4 | 1.58 km | 13.5 km | 10.5 K | 5 | 0 | 4 | 10.9 |
| Lascar | 1 | 5.7 | 0.18 km | 27.7 km | 14.9 K | 0 | 1 | 0 | 5.7 |
| **TOTAL** | **121** | | | | | **57** | **19** | **45** | |

## Hallazgos
1. **Los clusters están AL CRÁTER** (dist_cluster 0.2–2.8 km), no difusos lejanos. El
   "lejos" (13–27 km) es el píxel suelto (Salar/halo) = D12. `pc.vrp` es la magnitud
   del cluster al cráter, inflada por el campo difuso MODIS 1km sumado (A68 ~5000× en
   warm-scene extremo).
2. **ΔT bajo (10–14 K)** uniforme = régimen sub-pixel/Muy Bajo (A12). Señal débil real
   o ruido; la magnitud de 7 MW es del método de suma, no del foco.
3. **84% sin MIROVA** → magnitud inflada de señal sub-umbral → V-B debe curar (acercar
   a ~MIROVA/0). **16% cat-b con MIROVA** (Tupungatito 11 = clave) → señal real.
4. PCC max 60.2 MW = artefacto cirrus D9/A23 (frente aparte; el cap D9 o V-B lo tocan).

## Criterio EXTRA para el veredicto (A54/A68) — más allá de C1/C2/C3
- **C2 (curar ≥85%) NO basta**: hay que verificar que para los **19 cat-b** (sobre todo
  **Tupungatito**), la magnitud curada por V-B **se acerca a la magnitud MIROVA** de esa
  noche, NO cae a ~0. Si V-B destruye cat-b real → NO adoptar (destruye valor, A54).
- Cuando el A/B complete: cruzar `pc.vrp` curado (V-B) vs `VRP MIROVA` (CSV) para los
  cat-b. Bueno = converge a MIROVA. Malo = → 0 con MIROVA > 0.
- Recordar A19: Tupungatito refutó el kernel-bg per-pixel (ring glaciar). V-B es corona
  del cluster (mecanismo distinto) — pero Tupungatito es el caso a vigilar.

## HALLAZGO DECISIVO (cierra el riesgo A54): MIROVA casi no publica MODIS aquí
Cruce por SENSOR (latest_consolidado.csv, ALERTA 2026, columna VRP_MW):

| Vol | ALERTA MODIS | ALERTA VIIRS | VRP_MW MODIS MIROVA |
|---|---|---|---|
| **Lascar (CONTROL)** | **81** | 269 | med 1.19, max 3.94 |
| Chaiten | 1 | 26 | 0.74 |
| Villarrica | 1 | 10 | 1.83 |
| Llaima | 0 | 1 | — |
| Tupungatito | 0 | 107 | — |
| PCC | 0 | 0 | — |

**MIROVA solo publica MODIS para Lascar** (foco real, ΔT alto, el control). Para
Tupun/PCC/Llaima publica 0 MODIS; Chaiten/Villarrica solo 1. → Los 121 inflados MODIS
de los 5 vols no-Lascar NO tienen contraparte MODIS-MIROVA: son **sobre-detección de
método** (campo difuso 1km sumado sobre señal sub-pixel que solo VIIRS375 ve; MIROVA
sí ve VIIRS pero no MODIS = no hay foco MODIS resoluble).

**Riesgo A54 (V-B destruye señal MODIS real) DESCARTADO**: no hay foco MODIS-MIROVA en
esos vols. V-B curar los inflados a <5/~0 ACERCA a la realidad MODIS-MIROVA. El único
foco MODIS real es **Lascar** → protegido por **C3** (ratio ON/base ∈ [0.85,1.15]).
La "cat-b" de la heurística previa era FALSA (contaba MIROVA-VIIRS, no MODIS).

**Veredicto simplificado**: si V-B pasa C1 (detección intacta) + C2 (curar ≥85%) + C3
(Lascar preservado, el único foco MODIS real), es ADOPTABLE sin riesgo de destruir señal
real. Verificación extra opcional: que la magnitud V-B de Lascar (control) siga ≈ MIROVA
MODIS (1.19 med) — no solo el ratio interno.

## Probe destape del FLIP ancla MODIS (probe_modis_destape.py, offline A18)
El flip `enable_honest_anchor_modis` (§1, gateado por §2) destaparía **~2476 records
far→summit** (offline sobre-estima, ref V750: 93→32 real). Desglose:
- **cura del recall = 792** (flips con pc.vrp≤5 Y MIROVA publicó) → suben el recall
  summit-gated MODIS (hoy 10.8%, AUDIT_S108_ESTADO). Lascar 196, Tupun 141, Lastarria
  159, Isluga 130, PP 104 — el grueso de la cura D12.
- **landmine = 84** (flips con pc.vrp>5) → los inflados que §2 V-B debe curar ANTES del
  flip. Coincide con los 121 clasificados (orden de magnitud).
- **resto ~1600** (pc.vrp≤5 SIN MIROVA) = señal débil MODIS al cráter sin confirmación
  MIROVA → cat-b real (A54) o ruido. **ESTO agranda el alcance del flip más allá del
  framing del design (134 inflados)**: el flip es de ALTO impacto (cientos-miles de
  records summit nuevos). Requiere análisis del ~1600 (cat-b vs ruido) + A45 + OK Nicolás
  ANTES de activar. NO es solo "curar Láscar".

**Implicación**: §2 (magnitud, A/B en curso) se decide primero por C1/C2/C3. El flip §1
(ancla MODIS) es un paso SEPARADO de alto impacto — su veredicto necesita evaluar el
destape completo (~2476), no solo los 84 inflados. Reproc real con el flag ON dará el
conteo exacto.

## Cross-sensor del destape (classify_destape_modis.py): 93% es señal REAL
De los ~2476 flips far→summit del flip §1, cuántos están confirmados cross-sensor (esa
noche NUESTRO VIIRS vio summit con pc.vrp>0, o MIROVA publicó):
- **REAL (cross-confirmado) = 2318 (93%)** — el flip recupera señal real (VIIRS la ve;
  MIROVA la publica en VIIRS) = cat-b/TP. **Refuerza el flip §1**: cura el gap MODIS
  summit-gated (10.8%) recuperando mayormente señal real, NO inflando ruido.
- candidato-ruido = 156 (6%), **concentrado en NevadosDeChillan (128 de 196 destape =
  65%)**. NdC es el OUTLIER a investigar antes del flip §1 (¿Cerro Blanco difuso captado
  por el inner? ¿ruido MODIS?). Los otros 10 vols: 0–10 ruido c/u (~93–100% confirmado).
- landmine pc.vrp>5 = 84 (§2 V-B cura).

**Veredicto §1 (flip ancla MODIS)**: recupera 93% señal real cross-confirmada → SÓLIDO.
Condiciones para activar: (a) §2 cura los 84 inflados (A/B en curso), (b) investigar el
destape NdC (128 candidato-ruido), (c) reproc real con flag ON (A18 offline sobre-estima),
(d) OK explícito Nicolás (A45, alto impacto dashboard). Caveat confirmación: el cruce es
TEMPORAL (misma noche VIIRS summit), no espacial pareado — suficiente como señal, no prueba.

### NdC: caso especial del flip §1 (MIROVA 0 en 2026, no calibrable)
Investigación del outlier: **NdC tiene 0 alertas MIROVA en 2026** (ni VIIRS ni MODIS). Sus
196 destape (67 con VIIRS-nuestro, 129 sin) son sobre-detección sin ground truth MIROVA.
Los 129 candidato-ruido: clusters AL CRÁTER (dist 2.87 km; lat/lon med -36.865/-71.380 =
cráter Nuevo/Arrau, NO Cerro Blanco), **ΔT muy bajo (8.4 K)**, **pc.vrp muy bajo (0.42 MW
med, max 5.77)**. VIIRS 375m (más sensible que MODIS 1km) NO los ve → muy probablemente
**ruido térmico al cráter** (gradiente/sub-pixel), no foco real.
**Decisión del flip §1 para NdC, pendiente**: (a) §2 V-B podría bajar la magnitud (0.42 MW)
bajo el umbral de display → mitiga el destape; (b) sin MIROVA no hay paridad que romper
(ni a favor ni en contra); (c) requiere ground truth NdC (TIF/Chrome A61/A62) o criterio
de Nicolás (geólogo). **NO bloquea el flip en los otros 10** (93–100% señal real). El flip
es global (un flag); si NdC resulta ruido, el gate de magnitud/§2 es la mitigación correcta
(NO un gate per-vol, anti-MISSION).
