# Frente 2.A — Precision gap MIROVA vs VRP Chile (S86)

**Fecha**: 2026-05-28
**Origen**: Bloque arranque S86, Frente 2.A "audit OSF MIROVA" reorientado por Nicolás a usar CSV scraper Mirova-v1 (~4 meses captura en vivo) como ground truth primario en lugar de OSF v2.5 (corte 2019).
**Investigación**: 3 subagentes en paralelo (A perfil MIROVA, B perfil VRP Chile pre-filter, C cruce 1:1).
**Outputs subagentes**: `experiments/_s86_f_precision_gap/{A,B,C}_*.{md,json}` + `script_{A,B,C}.py`.

---

## TL;DR (actualizado post-Subagente D 2026-05-28)

Existe un gate empírico **de una sola feature** que eleva precisión global de 0.254 → 0.335 (sin frontend filter aplicado uniformemente; 0.243 → 0.413 con metodología de Subagente D) **sin perder un solo TP** sobre 117 días, 11 Tier A:

```
pc.mirova_publishable = (sensor_bucket != "VIIRS_M_750")
```

**Hipótesis adicionales investigadas y refutadas con datos** (gran valor durable — eliminan espacio de búsqueda):

- **Gate t_bg_k ≥ 260 K** (Mec 2): cuesta hasta 3 TPs reales (incluído evento eruptivo Lascar 2026-02-17 con cubierta nubosa fría, capturado solo por path D). Trade-off no compensa el +1.3 pp precisión adicional.
- **Gate persistencia temporal ≥2 noches consecutivas** (Mec 3): aporta solo +2 pp precisión sobre G1, cuesta 9% recall y requiere arquitectura dual-flag NRT. Causa: nuestros FPs también persisten (79% consec≥2 vs 91% TPs) porque son **cirrus crónicos, ruido glaciar, halos térmicos zonas no-volcánicas estables** — no "ruido aleatorio". MIROVA filtra estos por otro mecanismo, no por persistencia sola.
- **Gate n_pixels ≥ 3, vrp_mw ≥ 0.2 MW, path ≠ D-solo**: todos destruyen recall sin gain residual (refutado por Subagente C).

Recomendación para S87 (Frente 1.A): implementar **solo G1** como campo derivado `pc.mirova_publishable: bool` en `pipeline/store.py` con tag defensivo + confirmación Nicolás (regla A45), default OFF en operacional, A/B sobre `mirova_equivalent` antes de adopción.

**El gap mayor (0.413 → 0.99) NO se cierra con gates simples — el siguiente frente real es Frente 4 (exclude_zones extendido para los 18 clusters S85 cartografía Fase C) + investigación NTI absoluto/magnitud per-vol. Persistencia, magnitud absoluta y t_bg quedan descartadas como mecanismos dominantes.**

**Lo que NO funciona como gate único** (descartado con datos):
- `pc.n_pixels >= 2` o `>= 3` — destruye 10-25% recall por solo +3-5% precision (cola débil tiene TPs reales de Villarrica lava lake, NdC intermitente).
- `pc.vrp_mw >= 0.2 MW` o `>= 0.5 MW` — destruye 9-20% recall por casi 0 mejora precision.
- `path != D-alone` — destruye 25% recall (path D dNTI también captura TPs físicos reales — es ruidoso, no falso por construcción).

---

## El fenómeno físico (cómo leer este gap)

El pixel del satélite ve un trozo de superficie de tamaño fijo: 1 km² nominal MODIS, 375 m² VIIRS-I, 750 m² VIIRS-M. MIROVA publica ALERTA cuando ese pixel sostiene una anomalía radiativa que el operador puede defender como roca caliente sobre fondo. Esa decisión combina **intensidad** (cuánto se separa del background), **persistencia espacial** (cuántos pixels y dónde respecto del cráter) y **persistencia temporal** (noches consecutivas).

Nuestro pipeline tiene los mismos paths algorítmicos (A=BT clásico, B=NTI absoluto, C=NTI relativo, D=dNTI contextual 8-vec). El gap precisión 0.024 → 0.243 (post-frontend-filter S33) → 0.374 (post-gate propuesto) no viene de la física del ETI Coppola, viene de **mecanismos de supresión que MIROVA aplica y nosotros no**. La investigación distinguió tres mecanismos cuantitativamente y los ordenó por relación valor/riesgo.

---

## Mecanismo 1 — MIROVA no publica VIIRS M-band 750m para Tier A Chile

**Hallazgo**: 0 TPs / 671 FPs en VIIRS_*_750 sobre 117 días, 11 Tier A. **MIROVA literalmente nunca publicó M-band en este ground truth.**

**Lectura geológica**: el pixel M-band de 750×750 m tiene **5.6× más área que el pixel I-band 375×375 m**. Una anomalía sub-pixel del orden de 10⁰–10¹ MW (típica de un lava lake como Villarrica o un cráter intermitente como Nevados de Chillán) se diluye térmicamente sobre el M-band hasta quedar bajo la sensibilidad del algoritmo NTI. MIROVA tomó la decisión operacional de **no perseguir M-band para Chile** porque los volcanes chilenos Tier A producen sistemáticamente señal demasiado débil para esa resolución.

Nuestro pipeline corre VIIRS750 igualmente porque scientifically es procesable y produce un coeficiente Wooster propio (k = 1.97×10⁷ × A_pix km², empírico S14 contra OSF). Pero **lo que detecta es ruido térmico de fondo amplificado** — no es anomalía volcánica.

**Costo operacional del gate** (sensor_bucket != "VIIRS_M_750"): cero TPs perdidos en 117 días. Filtra 671 FPs (44% del total FP).

**Reversibilidad**: si en el futuro un volcán chileno entra en erupción mayor (Calbuco 2015-clase), el flag debería levantarse para ese vol. Por eso el gate va en campo derivado `pc.mirova_publishable` por record, no en filtro de fetch — los records VIIRS750 siguen capturándose y procesándose, solo se marcan no-publishable en el JSON. Si MIROVA empieza a publicar VIIRS750 (cambio en su algoritmo), revisamos.

---

## Mecanismo 2 — Path D dNTI contextual se dispara sobre cirrus alto frío

**Hallazgo (regla A23 confirmada con datos)**: 184 FPs en records con `t_bg_k < 260 K`, **cero TPs en ese régimen** sobre 117 días.

**Lectura geológica**: cuando el satélite mira un cirrus alto uniformemente frío (top de cirrostratus a ~-40°C = 233 K, top de cirrus a ~-50°C = 223 K), el kernel local 8-vecinos del path D ve un campo térmicamente uniforme. La operación `NTI_pixel - mean(NTI_vecinos)` queda dominada por ruido instrumental (NEdT VIIRS ~0.4 K, MODIS ~0.05 K) y produce un dNTI artificial altísimo en pixels aislados que no corresponden a roca caliente — corresponden a **fluctuaciones del campo de radiancia del cirrus**.

Físicamente: ese pixel no es anomalía volcánica, es ruido sobre una capa de hielo a 10 km de altura. MIROVA aparentemente filtra esto con un gate de temperatura de background mínima (no documentado en papers, comportamiento observable).

**Costo del gate** (t_bg_k >= 260 K): cero TPs perdidos. Filtra ~12% adicional de FPs.

**Riesgo conocido**: en eventos invernales con tormenta convectiva sobre el cono volcánico (cubierta nubosa real, no cirrus alto), el background puede caer por debajo de 260 K legítimamente. En esos casos descartaríamos detecciones reales bajo nube. Mitigación: el gate es informativo (no zero-out), el record sigue en el JSON con flag para revisión manual.

---

## Mecanismo 3 — Coherencia espacio-temporal (REFUTADO como gate dominante por Subagente D)

### Hipótesis inicial
MIROVA publica solo cuando una anomalía persiste en ≥N noches consecutivas en el mismo cluster espacial. Físicamente coherente: lava lake, domo, intrusión emiten calor sostenido; cirrus pasajero o ruido instrumental son transitorios.

### Verificación empírica (Subagente D, 117 días)

**Lado MIROVA**: la hipótesis se confirma. 91.4% de las ALERTAs MIROVA forman cadenas ≥2 noches consecutivas, 0.76% son singletons aislados ±7 días. Mediana cadena = 10 noches, p75 = 35 noches. Una ALERTA MIROVA típica es la "punta del iceberg" de un episodio térmico maduro.

**Lado nuestro (refutación)**: la persistencia **NO discrimina TP vs FP** porque nuestros FPs también persisten:

| Métrica | TPs nuestros (n=1650) | FPs nuestros (n=3687) |
|---|---|---|
| % ≥2 noches consecutivas | 91.0% | 79.0% |
| % singleton ±7 días | 1.9% | 6.3% |

La diferencia TP–FP es solo 12 puntos. **Nuestros FPs no son "cirrus pasajero único" — son persistentes pero no volcánicos**: cirrus crónicos sobre el mismo cráter, ruido glaciar reiluminado, halos térmicos de zonas no-volcánicas estables (los 18 clusters cartografiados S85 Fase C).

### Lectura geológica clave (insight durable)

**El gate verdadero de MIROVA NO es persistencia sola, es persistencia EN ZONA VOLCÁNICA**. Las zonas no-volcánicas térmicamente persistentes (Las Máquinas Copahue, lago cráter Trapa-Trapa, ring glaciar Tupungatito, halo lacolítico difuso PCC) son FPs incluso bajo gate de persistencia. MIROVA aparentemente los suprime con una cartografía implícita per-vol de regiones publishable / no-publishable — esto se alinea con el catálogo C.1 de S85 y refuerza el camino de Frente 4 (exclude_zones extendido).

### Gates de persistencia evaluados

| Gate | Recall mantenido | FP filtrado | Precisión post |
|---|---|---|---|
| G1 (baseline sin VIIRS750) | 100% | 36.5% | 0.413 |
| G1 + P1 (n_same_3d ≥ 1) | 96.6% | 40.5% | 0.421 |
| G1 + P2 (≥2 noches consec) | 91.0% | 46.7% | 0.433 |
| G1 + P3 (NOT singleton ±7d) | 98.1% | 39.1% | 0.419 |
| G1 + (P1 OR vrp≥50 MW) | 96.6% | 40.1% | 0.419 |

**Uplift máximo sobre G1 puro**: +2 pp precisión (G1+P2) a costa de 9% recall + complejidad arquitectural NRT (necesita dual-flag `provisional → confirmed` con lookahead). No vale la pena para Frente 1.A.

### Caveats validados por sanity checks

- **Villarrica lava lake**: 34/34 TPs cumplen ≥2 noches consec (100%). 2 clusters espaciales (lava lake + halo). Persistencia preserva señal sub-pixel.
- **Tupungatito (régimen Muy Bajo)**: 95.6% consec ≥2, mediana 42 noches. Persistencia es señal incluso en ΔT débil — refuta versión "régimen-dependencia por volcán" del Mec 3 original. Lo que MIROVA respeta uniformemente NO es régimen, es zona volcánica.
- **PuyehueCordonCaulle**: el más vulnerable a gate persistencia (78% consec≥2, mediana solo 4 noches). Halo lacolítico difuso = clusters menos cohesivos. Candidato a perder TPs reales con P2 estricto.
- **Lascar evento eruptivo feb 15-20**: MIROVA publicó 14 ALERTAs en 5 noches consecutivas. Persistencia preserva el episodio. (Nota: 335 TPs Lascar globales tienen 91.9% consec≥2.)

### Decisión

**Mecanismo 3 NO se incluye en `pc.mirova_publishable` para S87.** Documentado como refutado con datos. Frente 4 (exclude_zones extendido cartografía S85 C.1) toma prioridad para cerrar gap mayor.

---

## Mecanismo 3-bis (anterior versión) — MODIS Chile = Lascar-only

**Hallazgo**: de 64 TP MODIS posibles en 117 días, **8 TPs son Lascar y 56 son FNs en otros vols** (53 de los 56 FN son Lascar mismo — eventos que detectamos pero MIROVA no publicó esa noche, o que MIROVA publicó y nosotros no detectamos por sensibilidad MODIS baja). De los otros 10 Tier A: 0 TPs MODIS en total. PCC tiene 85 FPs MODIS / 0 TPs, Chaitén 17 FPs / 0 TPs, NdC 9 FPs / 0 TPs.

**Lectura geológica**: MODIS 1 km es demasiado grosero para resolver la firma sub-pixel de un lava lake (Villarrica 0.05-0.2 MW), un domo intermitente (NdC, Chaitén) o un lacolito difuso extendido (PCC). MIROVA tomó una decisión operacional: **publica MODIS solo cuando el cráter del volcán produce sistemáticamente ΔT > 20 K**. Eso en Chile = Lascar. El resto cae en VIIRS-375 que tiene 7× más resolución espacial.

**Por qué NO incluimos esto en el gate del Frente 1.A**: el mecanismo es per-volcán, no per-feature universal. Implementarlo como `pc.mirova_publishable = (sensor != MODIS OR volcano == "Lascar")` es un hardcode político que envejece mal. Si Calbuco o Hudson entra en erupción mayor, MIROVA empezará a publicar MODIS para ese vol y nuestro hardcode lo bloqueará silenciosamente.

**Decisión**: dejar Mecanismo 3 para frente futuro (S88+) con investigación de **threshold de actividad sostenida cluster MODIS persistente N noches consecutivas con magnitud > X**. Eso captura el régimen empíricamente sin hardcodear volcanes.

---

## Por qué los gates "obvios" NO funcionaron

Subagentes A y B levantaron tres gates aparentemente fuertes que el cruce 1:1 del Subagente C demolió empíricamente:

### Gate "pc.n_pixels >= 3" (cluster ≥ 3 pixels contiguos)

Subagente B reportó 25% de publishable con n_pixels ≤ 2 → "candidato directo a supresión MIROVA". Pero el cruce 1:1 muestra:
- 89% de TPs tienen n_pixels ≥ 2
- 92% de FPs tienen n_pixels ≥ 2

La diferencia es marginal. Aplicar gate `n_pixels >= 3` cuesta 10.4% recall (TPs perdidos: lava lake Villarrica, domos intermitentes NdC) por +5% precision. **Mal trade-off**.

### Gate "vrp_mw >= 0.05 MW" (piso de magnitud por sensor)

Subagente A reportó pisos limpios por sensor (MODIS 0.30 MW p05, VIIRS375 0.05 MW p05). Pero el cruce muestra que TPs y FPs comparten distribución de magnitud — los FPs path D no son débiles necesariamente, y los TPs incluyen magnitudes desde el piso hacia arriba. El gate `vrp_mw >= 0.2 MW` cuesta 9.2% recall por +0% precision residual.

**Lectura**: el piso de magnitud existe pero no es lo que distingue publishable de no-publishable en MIROVA. Aparentemente MIROVA admite señal débil cuando otros criterios la respaldan (persistencia, contexto vent-anchored).

### Gate "path != D-solo"

Subagente B reportó 82.5% de publishable son path D dNTI solo → "co-validación obligatoria mataría 80% de los FPs". Pero path D también captura una fracción muy alta de los TPs: aplicar `path != D-solo` cuesta 25% recall.

**Lectura**: path D no es falso por construcción. Es ruidoso en condiciones específicas (cirrus alto frío, Mecanismo 2). El gate inteligente es **condicionar path D a contexto térmico válido**, no eliminarlo.

---

## Lo que queda del gap (0.374 → 1.0)

El gate propuesto cubre 46% de los FPs. El 54% residual de FPs es VIIRS375 con `t_bg_k >= 260 K`. Distribución cualitativa por volcán (del Subagente C):

| Vol | FP VIIRS375 residual | Hipótesis física |
|---|---|---|
| Copahue | 109 | Campo geotermal Las Máquinas + lago cráter Trapa-Trapa caliente. Catálogo C.1 S85 lo identificó. |
| PCC | 48 | Lacolito 707 km² con cola térmica difusa (régimen A20 Tier A Muy Bajo). MIROVA puede aplicar coherencia temporal. |
| Chaitén | 91 | Domo en degradación. Halo térmico residual? Verificar persistencia. |
| Llaima | 97 | Glaciar Conguillío. Ring background frío con pixels mixtos. |
| NdC | 57 | Intermitencia real + ruido entre episodios. |
| PP | 60 | Halo regional complejo multi-cráter (Planchón+Peteroa+Azufre). A22 bimodalidad pendiente. |
| Tupungatito | 44 | Ring glaciar warm-relativo (A19 patrón térmico no-universal). |

**Direcciones para S88+**:

1. **Coherencia espacio-temporal** (Mecanismo 3 generalizado): exigir mismo cluster vent-anchored en ≥2 noches consecutivas. Implementación arquitectural compleja (estado entre runs). Captura supresión MIROVA por episodios intermitentes.
2. **exclude_zones extendido** (Frente 4 del bloque S86): incorporar 4 features no-volcánicas catalogadas en C.1 (Las Máquinas Copahue, Río Diguillín NdC, Malargüe PP) + nuevas a cartografiar para Llaima/Chaitén/Tupungatito.
3. **Régimen por volcán adaptativo**: gate de magnitud + n_pixels mínimo calibrado per-vol contra histórico MIROVA (no hardcode, fitted). Aprox 1-2h por volcán.

---

## Hallazgo paralelo no buscado — MODIS Lascar recall 0.125

Mientras buscábamos precisión, el cruce reveló un problema separado: **53 de las 56 FNs MODIS son Lascar**. MIROVA detecta MODIS Lascar que nosotros perdemos. No es supresión nuestra, es **falta de sensibilidad MODIS** — probablemente por gates internos D' demasiado estrictos o por filtro `t_bg_k >= 260 K` que también descartaría TPs Lascar legítimos en noches invernales.

**Importante**: implementar Mecanismo 2 (t_bg_k >= 260 K) sin auditarlo contra Lascar MODIS específicamente puede empeorar el ya pobre recall MODIS Lascar. **Validación obligatoria en S87**: reproc Lascar MODIS 117d con gate vs sin gate, verificar que ninguno de los 8 TPs Lascar MODIS actuales cae bajo el gate.

---

## Anti-pattern evitado

Patrón clásico de overfitting cuando se hace cruce 1:1 sobre un solo periodo: **no diseñar gates que solo distinguen TP de FP en ESTE 117d**. El gate propuesto cumple dos requisitos:

- **Basis físico defendible**: ambos features (sensor M-band + t_bg cirrus) tienen explicación física directa (resolución espacial + ruido instrumental sobre uniformidad atmosférica), no son features estadísticos arbitrarios.
- **Reversibilidad operacional**: ambos son campos derivados informativos. Si MIROVA cambia comportamiento o un vol entra en régimen distinto, el flag se revisa sin pérdida de data raw.

---

## Próximo paso recomendado

**Frente 1.A S87 (simplificado tras Subagente D)**:

1. Tag defensivo `pre-s87-mirova-publishable-g1` sobre `origin/main`.
2. Implementar en `pipeline/store.py` el campo derivado `pc.mirova_publishable: bool`:
   ```python
   pc["mirova_publishable"] = (
       sensor_bucket(record["sensor"]) != "VIIRS_M_750"
       and pc.get("centroid_dist_km", float("inf")) <= inner_radius_km
   )
   ```
   (El segundo término replica lo que `mirovaEqVrp` ya hace en frontend — unifica.)
3. Flag profile `enable_mirova_publishable_field: true` por default (es informativo, no zero-out).
4. Test TDD sintético en `tests/test_store_mirova_publishable.py` con 3 casos canónicos (VIIRS_M_750+intra-radio = no-publishable, VIIRS375+intra-radio = publishable, VIIRS375+extra-radio = R3 fantasma).
5. A/B reproc 117d profile `mirova_publishable_field` vs baseline. Audit precision/recall.
6. PR adopción operacional con tag `pre-s87-publishable-adoption`.

ETA realista S87: 1-2 horas reloj wall.

**Frente 4 S87+ (próxima prioridad real)**:
- Implementar `exclude_zones` extendido per-vol con los 18 clusters cartografiados en `docs/F_S81_C_1_ZONES_CATALOG.md` (S85).
- Investigar el mecanismo MIROVA verdadero remanente: NTI absoluto + magnitud + zona física per-vol.
- ETA realista: 1-2 sesiones.

---

## Reglas activas usadas

- **A11** (universo MIROVA = CONS + OCR) — confirmada masivamente: 72% de ALERTAs OCR no están en CONS.
- **A14** (variantes nombres vol CSV) — Subagentes verificaron empíricamente.
- **A19** (patrón térmico no-universal, ring glaciar Tupungatito) — explicación FP residual Tupungatito.
- **A20-A21** (R2 cluster vs anomalía difusa) — explicación FP residual PCC.
- **A23** (path D dNTI FPs en cirrus alto) — confirmada con N=184 FPs en t_bg<260K vs 0 TPs.
- **A47** (no paralelo sobre `data/mirova_equivalent/`) — respetada por subagentes (solo lectura).
- **A48** (mapeo sensor VIIRS sin sufijo = I375) — subagente C mapeó correctamente.
- **calidad-paso-a-paso** — 3 hipótesis levantadas por A+B fueron refutadas con datos por C antes de implementar.

## Tags defensivos

Ninguno creado en S86 — investigación 100% offline sin tocar `pipeline/`. Tags se crearán en S87 al implementar Frente 1.A.

## Archivos generados S86

- `experiments/_s86_f_precision_gap/A_mirova_published.{md,json}` + `script_A.py`
- `experiments/_s86_f_precision_gap/B_ours_detected.{md,json}` + `script_B.py`
- `experiments/_s86_f_precision_gap/C_crossing.{md,json}` + `script_C.py`
- `docs/F_PRECISION_GAP_INVESTIGATION_S86.md` (este doc)
- `tasks/BLOQUE_ARRANQUE_S87.md` (pendiente generar al cierre S86)
