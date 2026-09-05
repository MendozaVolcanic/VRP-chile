# S134 · F1 — Posición del cúmulo → magnitud publicada → paridad con MIROVA, por pasada

**Veredicto del criterio pre-registrado: NO CUMPLE. La posición del cúmulo NO explica el déficit
de paridad.** La razón ours/MIROVA es ~0,70 en VIIRS 375 m tanto cuando nuestro cúmulo está en el
cráter (≤0,5 km: 0,744) como cuando está a 1,5-3 km (0,659). Y el hallazgo que reordena la lectura
de S133: **en las pasadas que MIROVA confirma, nuestro cúmulo YA está en el cráter** (Villarrica
0,15 km, Tupungatito 0,23, PCC 0,22, Chaitén 0,28, PP 0,38). El anillo de 2,3-2,8 km vive casi
entero en las 2.152 pasadas que publicamos y MIROVA no.

Script: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s134-f1/experiments/_s134_audit/f1/f1_posicion_magnitud_paridad.py`
Salidas: `resultados.json` (ancla `vent_*`), `resultados_ancla_catalogo.json` (línea base roja),
`salida_vent.txt`, `salida_ancla_catalogo.txt` (stdout completo de cada corrida), mismo directorio.
Data leída sólo lectura desde la raíz canónica (`data/mirova_equivalent/<Vol>.json`, snapshot MIROVA
CONS∪OCR del 2026-08-31). Sin ningún cambio a `pipeline/` ni a otro archivo del repo.

## Ventana y denominadores (A90)

| qué | valor |
|---|---|
| records nuestros, 11 Tier A, `datetime_utc ≥ 2026-04-01` | 18.373 (último 2026-09-05 08:30); duplicados por `(sensor, granule)`: **0** |
| ALERTAS MIROVA CONS∪OCR, 11 Tier A, ≥ 2026-04-01, `vrp_mw > 0` | 1.371 (CONS 980 · OCR 391; última 2026-08-31 06:00) |
| pares por pasada (±20 min, mismo volcán y bucket, `mag_pub > 0`) | **1.161** (V375 992 · V750 164 · MODIS 5) |
| MIROVA con pasada nuestra sin publicar (FN) | 124 |
| MIROVA sin pasada nuestra (cobertura) | 86 |
| nuestros publicados sin ALERTA MIROVA | 3.889 (V375 2.152 · V750 1.340 · MODIS 397) |

Para los pares sólo cuentan records hasta la última alerta del snapshot (2026-08-31). Las
distribuciones de posición usan hasta el último record en disco. `|dt|` mediana y p95 de los pares:
0,0 min (los segundos del timestamp MIROVA son la única diferencia). Con ±60 min los tres conjuntos
no se mueven (1.161 / 86 / 124): el pareo no depende de la tolerancia.

Regla de magnitud replicada de `frontend/index.html:1039-1059` (`mirovaEqVrp`: `distance_class ==
"summit"` y `pc.centroid_dist_km ≤ inner`, cap 50.000) y `:1162-1182` (`mirovaEqVrpCore`: I-band
usa `f5_core_vrp_mw` si es número > 0, si no cae a `pc.vrp_mw`; MODIS y M-band publican `pc.vrp_mw`).
`USE_F5_CORE` arranca `true` (`:1082`). En los 992 pares I-band el campo `f5_core_vrp_mw` está
presente y > 0: **0 caen al fallback** (sobre todo el corpus, 2.212 de 7.318 records I-band no lo
tienen, pero ninguno de ellos es un par).

## Controles del instrumento

| control | esperado | medido | pasa |
|---|---|---|---|
| Línea base roja (ancla catálogo → vent) | Villarrica cambia | d_crater mediana V375 publicados **3,03 → 2,80 km**; Láscar 0,77 → 0,20; PCC 7,72 → 0,62; Tupungatito 3,21 → 2,22. Copahue/NdC/Llaima/Lastarria/Isluga no cambian porque su `vent_*` **es igual** al catálogo (d = 0,00 km, medido del YAML) | sí — la ancla se usa |
| Positivo Láscar V375 desde 2026-06-01 | mediana ≈0,2 km, ~79 % ≤500 m, n=208 (S133) | **0,22 km · 79,8 % · n=208** | sí, exacto |
| Pareo Láscar V375 desde 2026-06-01 | ≥50 % con par | 110 de 118 alertas con pasada a ±20 min (**93,2 %**); 104 publicadas | sí |
| `pc.centroid_dist_km` del pipeline vs mi haversine desde `vent_*` | 0 | mediana \|Δ\| = **0,000 km en los 11** (con catálogo: Villarrica 0,64, PCC 6,93, Tupungatito 2,50) | sí — el pipeline mide desde el vent |
| Negativo (`far` pareados) | ruido | V375/V750: **n=0** (el gate del operador no publica `far`); MODIS `far` con `pc.vrp_mw`: n=43, mediana 0,90, IQR 0,47-2,77 | ruido ancho, coherente |
| Los 11 tienen `vent_lat/lon` | sí | sí (0 faltantes) | sí |

Pregunta 1 del instrumento: si la posición no explicara nada, las medianas por bin saldrían iguales
y Spearman ≈0 — es lo que salió (ρ = −0,105 con d_crater; −0,059 con d_pico). Si lo explicara todo,
el bin ≤0,5 km daría ~1 y el bin lejano se alejaría en todos los volcanes — no pasó en ninguno.
Pregunta 2: el instrumento distingue vivo de muerto — la línea base roja mueve exactamente los
volcanes cuyo vent difiere del catálogo y deja quietos los otros seis.

## Criterio pre-registrado — tabla de los 9 volcanes con anillo (VIIRS 375 m)

Regla (escrita antes de correr): mediana(d_crater ≤ 0,5 km) en [0,7; 1,4] **y** mediana(> 1,5 km)
fuera, con n ≥ 5 en ambos bins, en ≥ 6 de 9.

| volcán | pares | cerca ≤0,5 km: n · mediana · IC95 | lejos >1,5 km: n · mediana · IC95 | cumple |
|---|---|---|---|---|
| Lastarria | 142 | 0 · — | 75 · 0,465 · [0,414-0,588] | no evaluable |
| Llaima | 3 | 0 · — | 3 · 0,431 | no evaluable |
| Villarrica | 21 | **21 · 0,897 · [0,821-0,970]** | 0 · — | no evaluable |
| Copahue | 4 | 0 · — | 4 · 0,962 | no evaluable |
| Chaitén | 35 | 28 · 1,438 · [1,263-1,724] | 5 · 0,737 | **False** (cerca fuera de banda, lejos dentro: al revés) |
| Nevados de Chillán | 6 | 2 · 1,126 | 1 · 1,097 | no evaluable |
| Planchón-Peteroa | 98 | 75 · 0,954 · [0,780-1,128] | 4 · 1,449 | no evaluable |
| Puyehue-C. Caulle | 159 | 138 · 1,018 · [0,898-1,089] | 6 · 1,313 | **False** (ambos en/cerca de banda) |
| Tupungatito | 115 | 90 · 0,701 · [0,648-0,748] | 23 · 0,833 · [0,573-1,455] | **False** (cerca en el borde, lejos dentro) |

**Evaluables 3 de 9 · cumplen 0 · NO CUMPLE.** El criterio ni siquiera se puede evaluar en 6
volcanes porque los pares no se reparten entre bins: en cada volcán caen casi todos en uno solo. Eso
ya es el resultado: MIROVA confirma un régimen de posición por volcán, no una mezcla.

Láscar (control, fuera del criterio): 205 de 207 pares a ≤0,5 km y razón **0,529** [0,495-0,577].
Isluga: 184 de 202 en 0,5-1,5 km, razón 0,611. El contraejemplo de S133 se mantiene y se agrava:
el volcán con el cúmulo mejor puesto es el que peor paridad tiene.

## Paridad por sensor × bin d_crater (razón ours/MIROVA, magnitud del operador)

| sensor / bin | n | mediana | IC95 | >1,4 | <0,7 | en banda |
|---|---|---|---|---|---|---|
| **V375 todos** | 992 | **0,705** | [0,675-0,735] | 107 | 490 | 395 |
| ≤0,5 km | 559 | 0,744 | [0,711-0,779] | 68 | 249 | 242 |
| 0,5-1,5 | 294 | 0,621 | [0,588-0,671] | 20 | 169 | 105 |
| 1,5-3 | 132 | 0,659 | [0,560-0,776] | 17 | 70 | 45 |
| >3 | 7 | 1,125 | — | 2 | 2 | 3 |
| **V750 todos** | 164 | **0,572** | [0,534-0,672] | — | — | — |
| ≤0,5 km | 125 | 0,554 | [0,517-0,629] | 3 | 80 | 42 |
| 0,5-1,5 | 29 | 0,658 | [0,310-0,921] | 6 | 16 | 7 |
| 1,5-3 | 9 | 2,263 | — (8 son Isluga) | 7 | 0 | 2 |
| **MODIS summit (operador)** | 5 | 0,919 | — | 1 | 1 | 3 |

Spearman razón~d_crater V375: ρ = −0,105 (p = 9e-4, n=992): significativo por el n, pero de signo
contrario a la hipótesis (más lejos, apenas más bajo) y de tamaño irrelevante. Con d_pico: ρ = −0,059
(p = 0,06). El mismo cruce por volcán está en `resultados.json → paridad_por_volcan_sensor_bin`.

### Por volcán (todos los bins juntos)

| volcán | V375 n · mediana · IC95 | >1,4 / <0,7 | V750 n · mediana |
|---|---|---|---|
| Láscar | 207 · **0,529** · [0,495-0,577] | 1 / 160 | 106 · 0,540 |
| Isluga | 202 · 0,611 · [0,579-0,658] | 5 / 125 | 24 · 1,204 |
| Lastarria | 142 · **0,506** · [0,448-0,606] | 16 / 90 | 0 |
| Llaima | 3 · 0,431 | 0 / 2 | 0 |
| Villarrica | 21 · 0,897 · [0,821-0,970] | 1 / 3 | 4 · 0,994 |
| Copahue | 4 · 0,962 | 1 / 1 | 1 · 1,333 |
| Chaitén | 35 · **1,353** · [1,203-1,614] | 16 / 4 | 1 · 1,150 |
| Nevados de Chillán | 6 · 1,198 | 1 / 0 | 0 |
| Planchón-Peteroa | 98 · 0,976 · [0,808-1,096] | 16 / 22 | 2 · 6,783 |
| Puyehue-C. Caulle | 159 · 1,031 · [0,918-1,125] | 38 / 27 | 24 · 0,655 |
| Tupungatito | 115 · 0,702 · [0,652-0,763] | 12 / 56 | 2 · 0,072 |

El déficit se concentra en los tres volcanes de foco fuerte y aislado sobre roca seca (Láscar,
Lastarria, Isluga: 0,51-0,61, IC que excluyen 0,7). Los nevados con pares suficientes (PP, PCC,
Villarrica) están **en banda**. Chaitén sobre-estima 1,35.

## ¿De qué SÍ depende la razón? (covariables, V375, n=992)

| covariable | bins → n · mediana |
|---|---|
| **nº de `anomaly_pixels` nuestros** | 1 px: 532 · **0,670** · 2-3 px: 297 · 0,658 · 4-9 px: 116 · 0,895 · ≥10 px: 47 · **1,162** |
| VRP MIROVA (MW) | <0,3: 637 · 0,793 (104 >1,4 / 258 <0,7) · 0,3-1: 287 · **0,596** · 1-3: 67 · 0,607 |
| cenital (°) | <20: 270 · 0,809 · 20-40: 292 · 0,690 · ≥40: 430 · **0,605** |
| `single_pixel_mode` | True: 973 · 0,698 · False: 19 · 0,889 |

V750 repite el patrón: 1 px 0,536 (n=81) → ≥10 px **1,584** (n=29); cenital <20° 0,783 → ≥40° 0,511.

**En 532 de 992 pares I-band el record tiene exactamente UN píxel anómalo.** El `single_pixel_mode`
(`pipeline/profile.py:735-743`: ON, umbral 5 MW, ≤3 px) es un no-op sobre un cúmulo de 1 píxel
(`max` de uno = suma), así que no es la causa del déficit; y `f5_core_vrp_mw/pc.vrp_mw` tiene
mediana 1,003 (p75 1,336) — el núcleo agrega vecinos sólo en una minoría.

## d_crater vs d_pico (records publicados desde 2026-04-01)

En I-band `d_pico ≈ d_crater` en los 11 (mediana de la diferencia < 0,05 km; PCC 0,62 vs 1,43 es la
excepción, lacolito extenso). La fracción «centroide > 1,5 km pero pico ≤ 0,5 km» es **0,000 en los
11 × V375**: cuando el cúmulo está en el flanco, el píxel más caliente también está en el flanco. El
anillo es del calor que detectamos, no del centroide. En M-band y MODIS sí divergen (Villarrica V750
1,34 vs 2,75; PCC MODIS 2,30 vs 13,73) porque esos cúmulos son multi-píxel y el pico cae en el borde.
Tabla completa: `resultados.json → posicion_d_crater_vs_d_pico_desde`.

## Posición del cúmulo: pares (MIROVA confirma) vs nuestros sin MIROVA (V375, desde 2026-04-01)

| volcán | pares: n · d mediana · ≤0,5 km | sin MIROVA: n · d mediana · ≤0,5 km | offset mediano sin MIROVA (N, E) km |
|---|---|---|---|
| Láscar | 207 · **0,17** · 99 % | 99 · 0,27 · 68 % | +0,04, −0,06 |
| Isluga | 202 · 0,86 · **0 %** | 203 · 2,59 · 0,5 % | −0,69, −0,45 |
| Lastarria | 142 · 2,14 · 0 % | 70 · 2,36 · 0 % | +1,52, −1,43 (NW 54/70) |
| Llaima | 3 · 2,28 · 0 % | 234 · 2,84 · 0 % | +0,55, +0,82 |
| Villarrica | 21 · **0,15** · 100 % | 262 · **2,80** · 1 % | +0,03, −0,24 (4 cuadrantes parejos) |
| Copahue | 4 · 3,00 · 0 % | 249 · 2,82 · 0 % | −2,07, +0,10 |
| Chaitén | 35 · **0,28** · 80 % | 307 · 2,60 · 15 % | +0,20, −0,39 |
| Nevados de Chillán | 6 · 0,59 · 33 % | 97 · 2,74 · 2 % | +0,50, +0,43 |
| Planchón-Peteroa | 98 · **0,38** · 77 % | 186 · 2,72 · 12 % | +0,03, +0,93 |
| Puyehue-C. Caulle | 159 · **0,22** · 87 % | 285 · 2,42 · 28 % | +0,13, +0,05 |
| Tupungatito | 115 · **0,23** · 78 % | 160 · 2,62 · 25 % | +1,06, −0,15 |

Lectura física: cuando hay una fuente puntual fuerte (la que MIROVA también ve), el cúmulo cae en el
cráter — en los nevados también. El anillo aparece en las pasadas sin fuente fuerte, con los cuatro
cuadrantes poblados casi por igual en Villarrica/Copahue/Llaima (no es un flanco: es todo el
contorno). Las dos excepciones con foco fijo desplazado son Lastarria (NW, 1,5 N / 1,4 W, ya
conocido: Lazufre, A84) e **Isluga (SW, 0,7 S / 0,5 W, IQR N −0,92/−0,52 y E −0,66/−0,26 sobre los
513 publicados, y 0 % de los pares a ≤0,5 km)**.

## Estrato MODIS doble

| MODIS | n pares | mediana | IC95 | clases | FN restantes |
|---|---|---|---|---|---|
| sólo `summit` (lo que ve el operador) | 5 | 0,919 | — | summit 5 | 43 |
| `summit ∪ far` con `pc.vrp_mw` | 48 | 0,910 | [0,580-1,404] | far 43 · summit 5 | **0** |

Los 43 FN MODIS son todos Láscar, todos `far` con `pc.vrp_mw > 0`, y el cúmulo `far` está a
mediana **1,56 km** del cráter (2 % ≤0,5 km, 53 % >1,5 km; offset mediano −0,31 N / −0,63 E, los
cuatro cuadrantes). Con la magnitud del cúmulo la paridad MODIS queda en 0,91 pero con IQR 0,48-2,26:
ruidosa.

## Los tres conjuntos del pareo, por sensor

| sensor | alertas MIROVA | pares | FN (pasada nuestra sin publicar) | sin pasada nuestra | nuestros sin MIROVA |
|---|---|---|---|---|---|
| V375 | 1.113 | 992 | 44 (28 `summit` con `mag_pub`=0 · 16 sin cúmulo) | 77 | 2.152 |
| V750 | 205 | 164 | 37 (todos `summit`) | 4 | 1.340 |
| MODIS | 53 | 5 | 43 (todos `far`, A46) | 5 | 397 |

- FN con OTRO granule nuestro publicado a ±20 min: **5 de 124** (el pareo castiga de más en 5 casos).
- VRP MIROVA mediano de los 124 FN: 0,265 MW (p75 0,52). Los 16 FN sin cúmulo alguno tienen MIROVA
  0,01-0,23 MW en 14 casos; los otros dos son 0,60 y 2,15 MW.
- Los 86 «sin pasada»: 59 son Láscar (26) y Lastarria (33), **todos OCR**, todos entre 17:24 y 18:24
  UTC (13-14 h local), sin ningún record nuestro a menos de 10 h; VRP mediano 2,87 MW. Son pasadas
  **diurnas**: el pipeline es nocturno por diseño y A76 las marca sospechosas de reflexión solar.
  No son FN.

## Nuestra distancia vs `Distancia_km` de MIROVA en el mismo par (indicativo — D15)

Comparación desde el catálogo (la ancla más parecida a la de MIROVA, que mide desde su centro de
grilla, cuantizada). V375 n=810: nosotros 1,01 km, MIROVA 1,55; diferencia mediana −0,33 km, IQR
[−0,85; +0,05]. Los valores MIROVA son discretos (Láscar 1,13/1,19/1,50/1,55; Tupungatito
4,80/4,89/5,21/5,41 mientras nosotros desde el vent damos 0,23 — la referencia de MIROVA en
Tupungatito está ~5 km del cráter, coherente con A63). La razón **no** depende del desacuerdo de
posición con MIROVA: |Δ| <0,5 km → 0,730 (n=433); 0,5-1,5 → 0,658 (262); 1,5-3 → 0,740 (108).

---

## HALLAZGOS (ordenados por gravedad)

### H1 · La hipótesis «la posición explica la paridad» queda REFUTADA; el déficit ~0,70 es uniforme en posición
- SCRIPT:SALIDA — `f1_posicion_magnitud_paridad.py --ancla vent` → `resultados.json → criterio`,
  `paridad_por_sensor_bin_d_crater`.
- QUÉ PASA — Físicamente: en las pasadas que MIROVA publica, nuestro cúmulo está donde está el
  calor (cráter), y aun así integramos ~30 % menos energía en I-band y ~45 % menos en M-band. No es
  que midamos otro objeto; es que del mismo objeto sacamos menos. Criterio: 0 de 9 cumplen (3
  evaluables); bins ≤0,5 / 0,5-1,5 / 1,5-3 km dan 0,744 / 0,621 / 0,659; ρ = −0,105.
- CÓMO SE VE EN EL DASHBOARD — magnitudes ~0,7× MIROVA en Láscar/Lastarria/Isluga (0,51-0,61) de
  forma sostenida; un umbral operacional expresado en MW se cruza más tarde que en MIROVA.
- CÓMO REPRODUCIRLO — `python f1_posicion_magnitud_paridad.py --ancla vent`; ventana 2026-04-01 →
  2026-08-31, 992 pares V375.
- CONFIANZA — CONFIRMADO. GRAVEDAD — 3.

### H2 · El anillo de S133 vive en lo que MIROVA NO publica; el eje espacial separa confirmado de no confirmado
- SCRIPT:SALIDA — `resultados.json → posicion_pares_vs_nuestros_sin_mirova`.
- QUÉ PASA — En 8 de los 9 volcanes con anillo, los pares están a 0,15-0,59 km del cráter (77-100 %
  a ≤0,5 km en Villarrica/PCC/Chaitén/Tupungatito/PP) y los «nuestros sin MIROVA» a 2,4-2,8 km con
  0-28 % al cráter, repartidos en los cuatro cuadrantes. Es la firma del A69 (MIR absoluto sigue la
  frontera nieve-roca de todo el contorno cuando no hay fuente fuerte). Corrige la lectura de S133:
  «el cúmulo que publicamos está a 2,3-2,8 km» es verdad del corpus, pero **no** de las pasadas con
  señal confirmada. NO propongo gate por distancia (A55/A85); lo que esto habilita es medir el corpus
  «sin MIROVA» como objeto propio (¿cat-b real o artefacto?) — pregunta de otro frente.
- CÓMO SE VE EN EL DASHBOARD — en 5 meses el operador ve 2.152 detecciones I-band «summit» (rojas)
  que MIROVA no reporta, la mayoría en el flanco a 2-3 km; 2,2 por cada par confirmado.
- CÓMO REPRODUCIRLO — misma corrida; sección «POSICIÓN del cúmulo V375» de `salida_vent.txt`.
- CONFIANZA — CONFIRMADO (la clasificación real/artefacto de esos 2.152 NO está medida acá).
  GRAVEDAD — 3.

### H3 · El déficit escala con el número de píxeles que retenemos: 1 píxel → 0,67; ≥10 → 1,16
- SCRIPT:SALIDA — `resultados.json → razon_vs_covariables`.
- QUÉ PASA — 532 de 992 pares I-band tienen exactamente UN `anomaly_pixel`; ahí la razón es 0,670.
  Con 4-9 píxeles sube a 0,895 y con ≥10 a 1,162 (V750: 0,536 → 1,584). Láscar, el contraejemplo de
  S133, encaja: cúmulo en el cráter (99 %), 1 píxel, razón 0,53. Mecanismo candidato: MIROVA integra
  más píxeles del mismo cúmulo que los que nuestro test contextual deja pasar alrededor del pico
  (S129: «MIROVA suma»). El `single_pixel_mode` no es causa (no-op sobre 1 píxel); `f5_core` tampoco
  (razón núcleo/cúmulo mediana 1,003).
- CÓMO SE VE EN EL DASHBOARD — el sub-reporte es peor justo en los focos fuertes y aislados (Láscar,
  Lastarria, Isluga), no en los nevados.
- CÓMO REPRODUCIRLO — sección «RAZÓN vs covariables» de `salida_vent.txt`.
- CONFIANZA — la correlación CONFIRMADA; el mecanismo (MIROVA retiene más píxeles) SOSPECHA — el CSV
  no trae n de píxeles VIIRS y no lo verifiqué contra el TIF. GRAVEDAD — 3.

### H4 · El gradiente cenital de la razón persiste tras nadir-fijo: 0,81 (<20°) → 0,69 → 0,61 (≥40°)
- SCRIPT:SALIDA — `resultados.json → razon_vs_covariables → zenith_deg` (V375 n 270/292/430; V750
  0,783 → 0,509).
- QUÉ PASA — a mayor ángulo el píxel real es más grande y el foco sub-píxel se diluye más; MIROVA lo
  compensa por área geolocalizada, nosotros por área nadir fija. Reproduce lo que S131 midió y S133
  decidió NO adoptar (el área invierte el sesgo). Lo registro como vigente en esta ventana.
- CÓMO SE VE EN EL DASHBOARD — la misma fuente aparece hasta un 25 % más baja según la geometría de
  la pasada; oscila noche a noche sin que el volcán cambie.
- CÓMO REPRODUCIRLO — misma corrida.
- CONFIANZA — CONFIRMADO (medido). GRAVEDAD — 2.

### H5 · MODIS: 43 de las 48 pasadas que MIROVA confirma quedan invisibles por la etiqueta `far`
- SCRIPT:SALIDA — `resultados.json → estrato_doble_summit_vs_summit_U_far → MODIS`,
  `modis_far_pareado_posicion`.
- QUÉ PASA — todas Láscar; `pc.vrp_mw > 0` pero `distance_class = "far"`, con el cúmulo a mediana
  1,56 km del cráter (no en el cráter: 2 % ≤0,5 km). Es la cara conocida A46/A82 cuantificada sobre
  esta ventana. Con el cúmulo incluido la paridad MODIS es 0,91 (IQR 0,48-2,26).
- CÓMO SE VE EN EL DASHBOARD — Láscar MODIS sin barra en 43 pasadas donde MIROVA publicó; recall
  MODIS del operador 5/53 en la ventana.
- CÓMO REPRODUCIRLO — sección «ESTRATO DOBLE» de `salida_vent.txt`.
- CONFIANZA — CONFIRMADO. GRAVEDAD — 2 (VIIRS cubre las mismas noches; anti-A8: no reabrir el
  far→summit por vía espectral).

### H6 · Isluga: foco fijo a 0,86 km al SW del `vent_*` en el 100 % de los pares
- ARCHIVO — `volcanoes.yaml` (Isluga `lat/lon = vent_lat/lon = −19.15 / −68.83`, d = 0,00 km entre
  ambos, medido hoy); `resultados.json → posicion_pares_vs_nuestros_sin_mirova → Isluga`.
- QUÉ PASA — 202 pares, 0 % a ≤0,5 km, mediana 0,86 km; offset SW apretado (cuadrante SW 355 de 513
  publicados; IQR N −0,92/−0,52, E −0,66/−0,26). MIROVA también lo pone a 0,53-0,84 km de su celda.
  Un foco térmico persistente a ~0,8 km de la coordenada declarada, con dispersión de un solo píxel,
  se parece más a «la coordenada del cráter activo no es la del catálogo» que a un anillo. El inner
  (5 km) lo cubre, así que la clasificación no cambia; pero toda distancia publicada de Isluga lleva
  ~0,8 km de sesgo y S133 lo contó como «pegado al cráter» (0,96 km, 0 %).
- CÓMO SE VE EN EL DASHBOARD — distancia al cráter ~0,9 km constante en un volcán con foco puntual.
- CÓMO REPRODUCIRLO — misma corrida; `pos_resumen` de Isluga V375.
- CONFIANZA — el patrón CONFIRMADO; la interpretación (coordenada del vent) SOSPECHA — hay que
  cotejar contra la posición del cráter activo (imagen/DEM), no lo hice. GRAVEDAD — 2.

### H7 · Los 59 «MIROVA sin pasada nuestra» de Láscar y Lastarria son ALERTAS OCR diurnas
- SCRIPT:SALIDA — `resultados.json → fn_detalle → sin_pasada_por_bucket_vol`; chequeo ad hoc en
  sesión: 0 de 59 con record I-band a ≤3 h, 59 de 59 a ≤12 h (el más cercano a 10-11 h).
- QUÉ PASA — todas entre 17:24 y 18:24 UTC (13-14 h local), VRP mediano 2,87 MW, sólo canal OCR.
  El pipeline es nocturno (MIR solo nocturno, regla científica) y A76 documenta que MIROVA publica
  artefactos solares diurnos en el producto per-volcán. Correcto no tenerlas. Riesgo: cualquier
  métrica de recall sobre CONS∪OCR **sin filtro día/noche** las cuenta como FN (59 de 86 huecos).
- CÓMO SE VE EN EL DASHBOARD — invisible (no hay record).
- CÓMO REPRODUCIRLO — filtrar `mirova_sin_pasada_nuestra` por vol y hora UTC.
- CONFIANZA — el dato CONFIRMADO; que el auto-audit las cuente como FN SOSPECHA (no leí
  `pipeline/audit_metrics.py` en esta sesión). GRAVEDAD — 1.

### H8 · M-band multi-píxel sobre-estima: `single_pixel_mode=False` → 1,59 (n=26); Isluga 1,5-3 km → 2,26 (n=8)
- SCRIPT:SALIDA — `resultados.json → razon_vs_covariables → VIIRS750`, `paridad_por_sensor_bin_d_crater → VIIRS750 → 1.5-3`.
- QUÉ PASA — cuando el cúmulo M-band supera 3 píxeles o 5 MW y se publica la suma, la razón salta a
  1,6-2,3 mientras el resto de M-band está en 0,55: dos regímenes de magnitud en un mismo sensor.
- CÓMO SE VE EN EL DASHBOARD — saltos ×3 entre pasadas consecutivas de Isluga V750 sin cambio físico.
- CONFIANZA — CONFIRMADO el número; n chico, sin IC. GRAVEDAD — 1.

### H9 · Dos FN V375 sin cúmulo alguno con MIROVA 0,60 y 2,15 MW
- SCRIPT:SALIDA — `resultados.json → mirova_con_pasada_sin_publicar_FN` (filtrar `distance_class`
  null, `n_pixels` null, `triggered_test1` false).
- QUÉ PASA — 16 FN sin `primary_cluster`; 14 con MIROVA ≤0,23 MW (sub-umbral aceptable), 2 no.
  Volcanes de los 16: PCC 6, Tupungatito 3, NdC 2, Isluga 2, Lastarria/Láscar/PP 1.
- CONFIANZA — CONFIRMADO el conteo; no investigué los 2 records. GRAVEDAD — 1.

---

## VERIFICADO LIMPIO

- **Ancla.** Los 11 Tier A tienen `vent_lat/vent_lon`; en 6 coincide con el catálogo (Copahue, NdC,
  Llaima, Lastarria, Isluga: 0,00 km) y en 5 difiere (Villarrica 0,85, Láscar 0,68, Chaitén 0,59,
  PP 0,50, Tupungatito 2,73, PCC 7,58 km). `pc.centroid_dist_km` del pipeline coincide con haversine
  desde `vent_*` en los 11 (mediana |Δ| 0,000 km). Comando: el chequeo `chk` del script.
- **Convención de sensores A48**, verificada con `Counter(r['sensor'])` sobre 18.373 records:
  `MODIS_TERRA/AQUA`, `VIIRS_{SNPP,NOAA20,NOAA21}` (I-band), `VIIRS_*_750` (M-band). El CSV MIROVA
  trae `Sensor ∈ {MODIS, VIIRS, VIIRS375}` y `normalize_sensor` (`pipeline/mirova_csv_loader.py`)
  manda `VIIRS`→V750, `VIIRS375`→V375.
- **Sin duplicados** `(sensor, granule)` en la ventana (0 de 18.373).
- **Pareo robusto**: ±20 y ±60 min dan los mismos tres conjuntos; |dt| = 0 min en todos los pares;
  sólo 5 de 124 FN tienen granule vecino publicado.
- **Regla del operador** replicada de `frontend/index.html:1039-1059, 1082, 1162-1182`; 0 fallbacks
  a `pc.vrp_mw` en los 992 pares I-band; el filtro `isThermalArtifact` (`:1232`) no marca ningún par.
- **Control positivo Láscar** reproduce S133 exacto (0,22 km · 79,8 % · n=208 desde 2026-06-01).
- **La tabla de S133** (`docs/s133/ANILLO_TIER_A.md`) se reproduce con el mismo filtro; lo que cambia
  es su lectura (H2), no sus números.
- **`single_pixel_mode`** ON, umbral 5 MW, ≤3 px (`pipeline/profile.py:735-743`,
  `mirova_equivalent.yaml:489-491`, confirmado con `VRP_PROFILE=mirova_equivalent python -c ...`).
  No es causa del déficit (H3).
- **MIROVA `Distancia_km` cuantizada (D15)** reconfirmada por pasada; Tupungatito MIROVA 4,8-5,4 km
  vs nuestro 0,23 desde el vent = la referencia de MIROVA está lejos del cráter (A63), no nosotros.
- **No medido acá, para que nadie lo tome por verificado**: clasificación real/artefacto de los
  3.889 «nuestros sin MIROVA»; n de píxeles de MIROVA por pasada (H3 mecanismo); posición del cráter
  activo de Isluga (H6); qué hace `audit_metrics.py` con las OCR diurnas (H7).
