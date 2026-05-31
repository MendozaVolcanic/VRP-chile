# AUDIT S94 — Métricas POR SENSOR (loader corregido) + diagnóstico VIIRS750

**Sesión S94 (2026-05-30).** Re-análisis pedido en `tasks/BLOQUE_ARRANQUE_S94.md` §2,
tras el fix del bug del loader VIIRS750 (PR #280). Reemplaza la tabla §6 de
`AUDIT_S93_artefactos_sobreestimacion.md` (invalidada por §7 de ese doc).

**Fuente de verdad reproducible**: `experiments/_s94_audit/per_sensor_metrics.py`
→ `per_sensor_metrics.json`. Verificación programática doc==fuente:
`experiments/_s94_audit/verify_doc.py` (regla integridad §0.5). NO toca pipeline (A45).

---

## 0. El fenómeno, primero

MIROVA publica **cada satélite como una serie independiente** (MODIS 1 km, VIIRS
I-band 375 m, VIIRS M-band 750 m). Cada sensor "ve" cosas distintas según su
resolución: el de 375 m resuelve un foco volcánico chico; el de 1 km lo promedia
con su entorno frío y solo lo ve cuando es grande. Por eso una métrica global
mezclada (un solo recall/precisión) es engañosa: junta un sensor casi ciego a lo
débil (MODIS) con la fuente real del recall (VIIRS 375 m). Hay que medir por sensor.

El bug §7 (la etiqueta CSV `VIIRS` a secas = M-band 750 m se bucketizaba como
375 m) había producido el falso "MIROVA no usa VIIRS750, recall 0". Con el loader
corregido, **MIROVA sí publica VIIRS750** y nosotros lo matcheamos bien.

---

## 1. Tabla corregida — VISTA A: CRUDO

Detección nuestra con `primary_cluster.vrp_mw>0`, **cualquier distancia**, match
temporal ±60 min contra alertas MIROVA (CONS∪OCR, VRP>0) del **mismo bucket de
sensor**, restringido a la ventana de cobertura por volcán. Responde "¿vimos
**algo** esa noche con ese sensor?".

| Sensor | N_ours | N_mir(cov) | TP | match_mir | Precisión | Recall | Ratio_med |
|---|---|---|---|---|---|---|---|
| MODIS | 2796 | 76 | 74 | 74 | **2.6%** | **97.4%** | 2.51× |
| VIIRS375 | 4107 | 679 | 1478 | 648 | **36.0%** | **95.4%** | 2.00× |
| VIIRS750 | 2838 | 165 | 278 | 143 | **9.8%** | **86.7%** | 1.53× |

**VIIRS750 recall 86.7%, NO 0.** Confirmado el diagnóstico §2.

## 2. Tabla corregida — VISTA B: SUMMIT-GATED (lo que muestra el dashboard)

Réplica de `frontend mirovaEqVrp` + `isThermalArtifact`: la detección cuenta solo
si está dentro del `inner_radius` (`distance_class=summit`) y NO es artefacto
térmico (cirrus / campo difuso). Es el número operacional que ve Nicolás.

| Sensor | N_ours | N_mir(cov) | TP | match_mir | Precisión | Recall | Ratio_med |
|---|---|---|---|---|---|---|---|
| MODIS | 217 | 76 | 9 | 9 | 4.2% | **11.8%** | 1.73× |
| VIIRS375 | 3910 | 679 | 1456 | 648 | 37.2% | **95.4%** | 2.04× |
| VIIRS750 | 1383 | 165 | 242 | 137 | 17.5% | **83.0%** | 1.51× |

**Dos lecturas clave del salto crudo→summit:**
- **VIIRS375 no cambia** (recall 95%, el caballo de batalla). Intacto, como debe ser.
- **MODIS colapsa a recall 11.8%**: de los 74 records MODIS que matchean a MIROVA
  en tiempo, solo 9 están en el cráter; el resto son `far`. **Todos los 74 TP MODIS
  son Láscar Feb-2026** y casi todos `distance_class=far` con VRP 0.3–5.9 MW → son
  los records de **deuda histórica S88** (el pipeline viejo elegía el clúster del
  Salar de Atacama off-nadir, A36, en vez del cráter caliente). No es error del
  pipeline actual; es data vieja → la limpia un **reproc** (F2).

---

## 3. Diagnóstico VIIRS750 "recall 0" (systematic-debugging) — RESUELTO

**Causa raíz del síntoma**: bug de bucketing del loader/frontend (PR #280 + S93 F1
`mirovaSensorBucket`). Con 0 alertas MIROVA en el cajón VIIRS750, el recall era
0/0 → "0.00". **No perdíamos VIIRS750 reales.** Verificado en navegador: Láscar
ventana "Todo" muestra ahora **VIIRS750 Recall 0.83** (TP=82 FN=17), ya no 0.

**¿Perdemos reales o son artefactos?** Ambas cosas coexisten, separadas por volcán:
- **Recall agregado 83–87%** lo domina Láscar (114 alertas VIIRS750, 96% matcheadas)
  + PCC (88%). Donde MIROVA publica VIIRS750, lo agarramos.
- **22 FN reales** (potencial pérdida): todos muy débiles (VRP 0.17–0.99 MW,
  mediana 0.25), casi todos cerca del cráter. Isluga (8) y Tupungatito (5) dominan
  → el clásico gap de recall sub-píxel en señal débil, no un bug.
- **Precisión baja (9.8% crudo / 17.5% summit)**: producimos 2838 detecciones
  VIIRS750, de las cuales 1408 son `far` y 1152 `summit` → el mismo mecanismo de
  campo frío que MODIS (path D Wooster sobre nieve/glaciar), más suave.

**Por qué Nicolás vio "0.00"**: probablemente en Tupungatito, ventana 30 días.
Tupungatito tiene ~11 alertas VIIRS750 en 5 meses, todas débiles; en una ventana de
30 días hay 1–3 y es fácil que 0 matcheen → recall 0.00 **real** (señal débil +
muestra chica), agravado antes por el bug que lo daba 0 globalmente. Por volcán:
Láscar 96 %, PCC 88 %, Isluga 60 %, Tupungatito 55 %, PP 33 %, NdC 0 % (1 alerta).

---

## 4. El confound que bloquea evaluar F3 offline

El split contextual-only (¿la detección disparó por foco térmico "duro" BT/NTI, o
solo por el path D contextual sobre fondo frío?) **no es interpretable sobre la data
actual** por dos razones:

1. **`enable_bt_path_hot: false`** (adoptado S40): el path BT está apagado en el
   perfil operacional. `diag_n_bt_path` ≈ 0 siempre por configuración, no por
   ausencia de lava. En 2803 records MODIS, solo **4** tienen foco duro
   (BT o NTI). El predicado de co-validación `n_bt==0 ∧ n_nti==0` se reduce de hecho
   a `n_nti==0`.
2. **Cluster histórico equivocado**: los 74 TP MODIS son el clúster-Salar (far),
   no el cráter. Si el cráter de Láscar Feb estaba a 119 MW (S86), sus píxeles
   tienen NTI alto — pero el pipeline viejo no los seleccionó, así que el record
   persistido marca `diag_n_nti_path=0`.

| Sensor | TP | TP_ctx | FP | FP_ctx |
|---|---|---|---|---|
| MODIS | 74 | 74 (100%) | 2722 | 2718 (100%) |
| VIIRS375 | 1478 | 1377 (93%) | 2629 | 2532 (96%) |
| VIIRS750 | 278 | 278 (100%) | 2560 | 2531 (99%) |

Leído literal, "co-validación mataría el 100 % de los TP MODIS" — pero eso es
artefacto del bt_path-OFF + clúster-Salar, **no** una predicción válida del
comportamiento post-reproc. **Conclusión metodológica (refuerza A18/S88): la
seguridad de F3 SOLO se puede medir tras el reproc F2 con el pipeline vigente.**

---

## 5. Plan F2–F5 replanteado (con los números correctos)

### Cambios respecto al diseño S93 (`2026-05-30-clon-mirova-por-sensor-design.md`)

- **§3.2 "VIIRS750 — no reportar" → REFUTADO.** MIROVA publica VIIRS750 (158 CONS /
  179 CONS∪OCR), recall 83–87 %. Ocultarlo destruiría recall real (categoría b,
  A54). VIIRS750 pasa a tratarse **como un sensor de pleno derecho**: conservar
  detección, atacar la precisión (artefactos de campo frío) igual que MODIS.
- **§3.1 MODIS co-validación → sigue candidata, pero el orden es vinculante:**
  el dashboard YA oculta los artefactos MODIS (summit-gate + filtro térmico → solo
  2 FP MODIS visibles en Láscar). El problema operacional de MODIS no es la
  precisión mostrada (ya limpia), sino el **recall al cráter (11.8 %)** = deuda
  histórica. **F2 (reproc) primero**; recién con data reprocesada se puede medir
  si F3 es seguro (§4).

### Orden recomendado

| Fase | Qué | Toca | Por qué / gate |
|---|---|---|---|
| **F2** | Reproc histórico local con el pipeline ACTUAL (cap D9 + vent_anchored + gates) | `data/` | Limpia deuda Salar de Láscar (recall MODIS/cráter) y picos 337/190 MW (A18). NO toca código. A47 secuencial. |
| **F3** | Co-validación path D **solo MODIS** (flag por-sensor) | `process_modis.py` | **Evaluar SOLO sobre data reprocesada (§4).** A45: tag+OK Nicolás+TDD+reproc+R2. Confirmar 0 pérdida de evento-noche. |
| **F4** | VIIRS750: atacar precisión de campo frío (no ocultar) | display y/o pipeline | Reformulado: NO es "no procesar". Opción display (cap/marcado) primero. |
| **F5** | VIIRS375 reportar-foco (magnitud, ratio 2.0×→~1.5×) | `process_viirs.py` | Opcional. A45 completo. |

### Criterios de aceptación (actualizados)
- Recall por evento-noche VIIRS375 **no baja** (reproc real, no offline).
- Recall VIIRS750 **se conserva** (≥80 % agregado; MIROVA lo publica).
- MODIS: recall-al-cráter sube tras F2 (deuda Láscar); precisión mostrada ya alta.
- Ratio mediano por sensor en tolerancia (VIIRS375/750 ≤2×; MODIS solo en eventos reales).

---

## 6. Auditoría ESPACIAL — ¿caen las detecciones en la laguna cratérica?

Pregunta de Nicolás (Tupungatito). La auditoría §1–§3 es **temporal** (¿vimos algo
esa noche?); ésta es **espacial** (¿el punto cae en el cráter?). Fuentes
reproducibles: `experiments/_s94_audit/tupungatito_spatial.py` (+`.json`) y
`spatial_audit.py` (+`.json`, los 11 vols).

### El fenómeno
El cráter de Tupungatito es una **laguna chica** cuya emisión térmica es **sub-píxel**
(~0.3 MW, lo que MIROVA ve con VIIRS 375 m). El fondo es **glaciar a −32 °C**. Dos
sensores cuentan historias distintas:
- **VIIRS 375 m** resuelve el foco: **336 de 373 detecciones (90 %) tienen el centroide
  del cluster a <2 km del cráter**. Coincide con MIROVA (que reporta su foco a ~0.5 km
  del cráter, una vez corregido su offset de medición). **Este sensor funciona.**
- **MODIS 1 km** NO resuelve el foco. Sobre el glaciar helado, el path D contextual
  enciende afloramientos de roca apenas sobre cero (−0.3 °C, "tibios" relativos al
  hielo) y Wooster lee el contraste hielo↔roca como fondo↔lava.

### La evidencia que responde la observación de Nicolás
El **record de mayor VRP** de Tupungatito (2026-05-14, **190.9 MW, MODIS_AQUA**) tiene
**0 de 77 píxeles anómalos dentro de 2 km del cráter** — están todos a **7–27 km** sobre
el glaciar/altiplano. La magnitud NO sale de la laguna; sale del campo frío disperso.
Y el sesgo es sistemático: el VRP mediano del **glaciar (>7 km) es 5.05 MW**, MAYOR que
el del **cráter (0–2 km), 2.62 MW** — el artefacto brilla más que el foco real.

| Geometría Tupungatito | valor |
|---|---|
| cráter ↔ mirova_center | 4.86 km (offset A13/A30) |
| VIIRS375 con centroide <2 km del cráter | 336 / 373 (90 %) |
| VRP mediano cráter (0–2 km) | 2.62 MW |
| VRP mediano glaciar (>7 km) | 5.05 MW |
| Record top: 190.9 MW MODIS, píxeles <2 km del cráter | 0 / 77 |

### Cross-volcán (los 11, `spatial_audit.py`)
El patrón es **por sensor, universal**: **VIIRS375 siempre centrado** (mediana ~1 km en
10/11; única excepción PCC 4.94 km = lacolito extendido genuino, cat. b A20/A24). **MODIS
y VIIRS750 dispersos** (medianas 3–18 km) por baja resolución + elongación off-nadir sec³θ
(A36). La firma de "campo difuso disperso" (n_px≥100 ∧ vrp/px<1) es **rara** incluso en
glaciares (Tupungatito 4/442 summit) — la dispersión viene del **sensor de baja
resolución ubicando mal el centroide**, no de un campo difuso extendido (salvo PCC).

### Qué significa operacionalmente
- **La señal canónica (VIIRS375) reproduce el foco de MIROVA.** El clon, en el sensor que
  importa, está bien.
- **La dispersión "fuera del cráter" es enteramente MODIS + VIIRS750.** El dashboard ya
  oculta lo `far` (gate summit → VRP=0 en "solo cráter") + el filtro de campo difuso, pero
  el MAPA los dibuja en gris e históricamente inflaban el chart.
- **Tupungatito es exactamente el caso para F3** (co-validación MODIS): sin foco térmico
  duro sobre el glaciar, MODIS no debería reportar. Pero F3 solo se valida tras F2 (§4) y
  con cuidado (A19: el ring glaciar de Tupungatito refuta kernel-bg; co-validación es otro
  mecanismo, hay que medirlo, no extrapolarlo).

## 7. Escudo anti-drift (vigente)
NO gate t_bg ciego (S86). NO ocultar VIIRS750 (refutado §5). NO tocar detección
VIIRS375 (recall). NO co-validación global (mata 93 % recall, S93). NO tocar
pipeline sin tag+OK (A45). La co-validación distingue por COHERENCIA (foco duro
presente), no por fondo frío — y solo es medible tras F2.
