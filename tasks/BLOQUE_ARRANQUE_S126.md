# Bloque de arranque S126

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S125. Esa sesión encontró y aisló la causa del
sub-reporte de magnitud, y dejó un candidato de adopción a medio verificar.

Leé en este orden:
  1. docs/S125_DIAGNOSTICO_SUBREPORTE_VIIRS.md   (dónde vive el sub-reporte)
  2. docs/S125_AB_MAGNITUD_RESULTADO.md          (el A/B de 4 ramas, NO ADOPTAR)
  3. tasks/BLOQUE_ARRANQUE_S126.md               (las tareas, en orden)

EL HALLAZGO. El sub-reporte no estaba en la cadena de magnitud: está en un solo
sensor. Ratio nuestro/MIROVA sobre 1049 pares nocturnos — MODIS 1,08 (calibrado),
VIIRS 750 m 0,83, VIIRS 375 m 0,69. Y el A/B mostró que UNA pieza lo explica
entero: apagando `enable_test1_contextual_filter` la magnitud de VIIRS 375 pasa
de 0,600 a 1,043, con los IC casi sin solaparse. El anillo intermedio [1,5-3] km
no mueve nada, pese a que el fondo de VIIRS 375 está +2,49 K más caliente que el
de VIIRS 750 en el 100% de 21.511 pares (hallazgo real, consecuencia nula).

⚠️ NO ADOPTAR TODAVÍA. Falta medir el costo — ver TAREA 1.

═══════════════════════════════════════════════════════════════════════════
TAREA 1 — el costo de apagar el filtro contextual (read-only, sin CI)
═══════════════════════════════════════════════════════════════════════════

El filtro se adoptó para CORTAR EL HALO NIVAL: los píxeles tibios sobre nieve
alrededor del cráter, que no son anómalos contra sus vecinos. Apagarlo sube la
magnitud a paridad, pero la pregunta abierta es cuánto ruido destapa.

Señal de alarma ya visible: el p75 del brazo E es 2,684 contra 0,878 del control.
La mediana mejoró pero la cola alta se disparó — puede ser el halo volviendo.

Medir sobre los datos que YA están en disco (`data/_s125_viirs_e/` vs
`data/_s125_mag_control/`):

  · Detecciones nuevas en E que el control no tenía: ¿cuántas, y caen sobre el
    cráter o sobre el halo nevado? (usar la distancia del centroide al vent).
  · Estratificar por RÉGIMEN, no sólo por sensor: Villarrica y Chillán son
    nevados y ahí el halo importa; Láscar y Lastarria son desierto de altura y
    el filtro no debería estar haciendo nada. Si el daño se concentra en los
    nevados, es el halo; si es parejo, es otra cosa.
  · Falsos positivos contra MIROVA: noches donde E detecta y MIROVA no publicó.
  · n_pixels por cluster antes y después: el filtro deja 87% de clusters en 1
    píxel; ver a cuánto sube y si los píxeles agregados son contiguos al cráter.

Recién con eso se decide. Si el costo en FP es bajo y concentrado fuera de los
nevados, es adopción. Si destapa el halo, hay que buscar una variante que
conserve la energía sin recuperar el ruido.

═══════════════════════════════════════════════════════════════════════════
DESPUÉS, en este orden
═══════════════════════════════════════════════════════════════════════════

  2. Leer el brazo G (`data/_s125_viirs_g/`) y confirmar que no hay interacción
     entre las dos piezas. Correr `experiments/_s125_magnitud/03_veredicto_viirs.py`
     — ya lo toma automáticamente si el directorio existe. Si G ≈ E, cerrado.

  3. A/B de la máscara de nube. Perfiles YA creados y verificados:
     `_s125_cloudmask_on` (260 K, control = como está hoy) y `_s125_cloudmask_off`
     (0.0, lo que el perfil ya declara). Decide las 15 noches ciegas de Chillán.
     Lo que hay que medir está escrito en la cabecera de los propios perfiles:
     apagarla recupera noches ciegas PERO puede meter topes de nube fríos en el
     anillo, bajando t_bg e inflando la magnitud.

  4. El piso VRP — recién ahora, porque si la magnitud de VIIRS sube, varios de
     los 761 records suprimidos suben solos por encima del piso sin tocarlo.
     Lo que ya está probado (ver §"piso VRP" abajo).

═══════════════════════════════════════════════════════════════════════════
REGLAS DE ESTA ETAPA (siguen vigentes de S125)
═══════════════════════════════════════════════════════════════════════════

  · Todo probado con script reproducible que persista los números (S91).
  · Estratificar por SENSOR siempre: mezclar MODIS con VIIRS fabricó la falsa
    "bimodalidad" de Láscar (los outliers de 19× eran todos MODIS).
  · Descartar las alertas DIURNAS de MIROVA: son artefacto de reflexión solar
    (A76) y el pipeline es night-only. Contarlas como FN es contar como fallo
    algo que hacemos bien.
  · El CONTROL de un A/B nunca puede ser `mirova_equivalent` a secas: esa data
    es un acumulado reprocesado en momentos y versiones distintas. Usar un clon
    reprocesado en la misma ventana.
  · Verificar los flags leyendo `pipeline.profile`, nunca el YAML — y el NIVEL:
    los `enable_*` de magnitud/paths van bajo `paths:`, los umbrales bajo
    `thresholds:`, y `enable_single_pixel_sub_mw_mode` en la RAÍZ.
  · Antes de leer un reproceso sobre datos existentes:
        python experiments/_s124_ndc_focus/05_verificar_reproceso.py <json>
  · Comparar siempre sobre la INTERSECCIÓN de pasadas (datetime_utc + sensor).
```

---

## Estado al cerrar S125

**Suite**: 911 tests verdes. **NRT**: sano (último run verde 28-ago 18:13 UTC,
datos commiteados 19:50).

**Tags defensivos**: `pre-s125-magnitud-ab`, `pre-s125-cloudmask`.

**PR abierto**: #535 (diagnóstico + fix de máscara + brazos). CLEAN, esperando CI.

**Datos de A/B en disco**: `_s125_mag_{control,a,b,c}` · `_s125_viirs_{e,f}`
(G en curso al cierre).

### Lo que quedó PROBADO

| hallazgo | cómo se probó |
|---|---|
| El sub-reporte vive en VIIRS 375, no en la cadena de magnitud | ratio por sensor sobre 1049 pares nocturnos: MODIS 1,08 · V750 0,83 · V375 0,69 |
| **El filtro contextual lo explica entero** | A/B: control 0,600 → E 1,043; IC casi sin solaparse; controles internos (V750, MODIS) idénticos |
| El anillo intermedio no mueve nada | brazo F ≡ control, exacto |
| El fondo de V375 está +2,49 K más caliente | 21.511 pares de la MISMA pasada, 100 % de los casos |
| El sesgo cambia de signo con el régimen | 1,70 bajo 0,05 MW vs 0,61-0,66 sobre 0,2 MW |
| El área integrada se derrumba con la resolución | 87 % de clusters V375 de 1 píxel (0,14 km²) vs 4 px / 4,0 km² MODIS |
| Chillán: 3/3 alertas de MIROVA reproducidas | `plot_simple.py`; y el umbral bajo NO aporta noches (23 vs 23) |
| Las 15 noches ciegas las causa la máscara de nube | descarta 13.200-17.300 px vs ~1.100 normal; no queda ni el t_max |

### Lo REFUTADO (no reabrir sin evidencia nueva)

- **La máscara de nube NO causa el fondo caliente**: sin máscara la brecha es
  +2,77 K, con máscara +2,32 K. Si fuera la causa, desaparecería.
- **Láscar no es bimodal**: eran dos sensores mezclados. Los outliers de 19×
  son todos MODIS; las 40 noches que sub-reportan son VIIRS de 1 píxel.
- **El "colapso de 50×" en magnitudes altas no existe**: 8 de 9 casos eran
  alertas DIURNAS de MIROVA (artefacto solar), incluido Láscar 760 MW.
- **La corona (Eq. 6) no aporta** — pero ojo: está cableada SÓLO en MODIS, así
  que el brazo A no probó lo que se diseñó para probar. No dice "no sirve",
  dice "no llega adonde se mide".

### El piso VRP — probado, pendiente de decisión

- **Los papers NO lo justifican**: Coppola 2016a tiene una clase de alerta
  explícita **"Low < 1 MW"** (`sp426_5.txt:684`). El criterio de MIROVA es de
  CONTRASTE contra el fondo, no de energía; el VRP es una salida, nunca una
  compuerta. Nuestro piso invierte esa relación.
- **Límite instrumental real**: la banda I4 tiene NEdT 2,5 K contra 0,107 K de
  M13 (~25× más ruidosa). Pero ese ruido es lo que el test N·σ ya mide por
  imagen; el piso lo cuenta una segunda vez y peor, ciego al fondo de esa noche.
- **Está mal aplicado**: `store.py:466` lo aplica a `record.vrp_mw` (VRP de
  escena) y NO a `primary_cluster.vrp_mw`, que es lo que se grafica y lo que
  muestra el dashboard. Por eso hay records de 0,009-0,019 MW pese al piso.
- **El de MODIS es código muerto**: suprime **0 de 12.152**.
- **La justificación del YAML está falsada**: dice "mínimo observado" con n=1 y
  n=2; con n=1000 el mínimo real de MIROVA en V375 es 0,010 y en V750 0,090 —
  ambos pisos quedaron POR ENCIMA del mínimo que MIROVA publica.
- MIROVA publica con **resolución de 0,01 MW** (todos los valores son múltiplos
  exactos), así que su "mínimo" de 0,010 es redondeo, no umbral. Su distribución
  decae suave (521 · 284 · 196 · 194 · 67 · 9 · 1), no se corta.

### Bugs de infraestructura documentados, sin arreglar

- **El job `merge` puede cancelarse en silencio**: comparte el grupo
  `push-main`, así que dos reprocesos que terminan juntos pierden uno. El run
  figura `cancelled` y parece que no corrió, cuando el cómputo está hecho.
  Pasó con el brazo A; se recuperó de los artifacts sin re-computar (receta:
  `gh run download <id>` + `merge_chunk_stores.py --ventanas`). **Fix pendiente:
  que reintente en vez de cancelarse.**
- **Canal OCR partido**: `build_c2ab_windows.py:55` consume una copia congelada
  el 2026-03-28 (235 filas) mientras el snapshot llega al 08-24 (887).
- **`modis_vent_threshold_k` duplicado** en dos niveles del YAML en los 39
  perfiles: gana el de `thresholds:` y el de `paths:` nunca corrió.
- **`audit_metrics.mirova_eq_vrp()`** muerta (sólo `tests/`) y ya divergida de
  las 3 copias del frontend — un audit que la use mide otra cosa que el dashboard.

### Correcciones documentales aplicadas en S125

`CLAUDE.md`: A69 obsoleta en su cierre · A23/A17/A7/A42 obsoletas · rebaja de
A82 propagada · **A86-A88 incorporadas** (vivían sólo en la memoria del agente).
`MISSION.md`: la Regla D Test1-priority y la cloud mask figuraban "removidas
S27" y siguen activas · `MAX_SIGMA_COMPONENT_K` neutralizado por valor, no por
código. `MIROVA_DIVERGENCES.md`: D5 rebajada (declaraba sobre-reporte cuando hoy
es sub-reporte, signo opuesto) · D12 congelada con nota anti-A8 · D14 corregida.

Detalle completo: `docs/AUDIT_S125_PROFUNDA.md`.
