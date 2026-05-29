# S88 — Re-selección offline (refutada como proxy) + decomposición Lascar febrero

**Fecha**: 2026-05-29 (S88). **Script**: `reselect_offline.py` (100% offline, no toca pipeline NRT).
**Datos**: `anomaly_pixels` persistidos en `data/mirova_equivalent/*.json` (11 Tier A) +
loader canónico `load_mirova_alertas` (CONS∪OCR). **Ventana**: igual que S87.

> **NOTA DE CORRECCIÓN (integridad)**: una primera versión de este documento (commit
> inicial PR #238) reportó números ANTICIPADOS, no los del script (decía resel 75.4%
> global, Lascar +4.4pp, 7 recuperables). Eran **incorrectos**. Esta versión corrige con
> el output real del script. La conclusión cambió de signo (ver §1). La lección está en
> la sección final.

## Pregunta

S87 dejó el 74.7% de match 1:1 anomalía dominante como **piso contaminado**: la columna
`vent_anchored` leía el `primary_cluster` PERSISTIDO, que mezcla épocas de estrategia
(pre-S38 `vrp_max` vs post-S38 `vent_anchored`). Dos preguntas, ambas sin reproceso:

1. **¿Puedo estimar el match del pipeline ACTUAL re-aplicando la lógica `vent_anchored`
   a los `anomaly_pixels` persistidos** (en vez de leer el primary stale)?
2. **De los no-match eruptivos de Lascar feb, ¿cuántos tienen el cráter PRESENTE en los
   pixeles persistidos (recuperable en disco) vs AUSENTE (requiere reproceso L1B)?**

## Resultado 1 — la re-selección offline NO es un proxy válido (pregunta 1: NO)

El script reconstruye clusters con `cluster_pixels_geographic` sobre los `anomaly_pixels`
persistidos y re-rankea con `vent_anchored` (espeja `pipeline/clustering.py`). Output real
(tol 2 km):

| Volcán | n | stale% (=S87) | resel% | Δpp |
|---|---:|---:|---:|---:|
| Lastarria | 87 | 98.9 | 83.9 | **−15.0** |
| Villarrica | 11 | 90.9 | 63.6 | **−27.3** |
| Tupungatito | 57 | 77.2 | 59.6 | **−17.6** |
| NevadosDeChillan | 5 | 80.0 | 60.0 | −20.0 |
| Isluga | 74 | 83.8 | 71.6 | −12.2 |
| PlanchonPeteroa | 53 | 94.3 | 84.9 | −9.4 |
| Chaiten | 16 | 93.8 | 87.5 | −6.3 |
| Lascar | 159 | 67.3 | 69.8 | +2.5 |
| PCC | 62 | 25.8 | 38.7 | +12.9 |
| Llaima / Copahue | <4 | = | = | 0 |
| **GLOBAL** | **529** | **74.7** | **69.0** | **−5.7** |

> La columna `stale%` reproduce EXACTAMENTE los números de S87 (Lascar 67.3, Lastarria
> 98.9, PCC 25.8, Tupungatito 77.2…) → el script lee la misma data que S87. El problema
> está en el `resel%`.

**Lectura**: la re-selección offline **baja** el match en 7/9 vols con n≥5, fuerte en los
cráteres compactos bien calibrados (Lastarria −15, Villarrica −27, Tupungatito −18). Es
**peor**, no un piso. Concreto: Lascar 2026-02-03 VIIRS — el primary stale matcheaba
correcto (2.35 km vs MIROVA 1.19), pero la re-selección offline rompió el match eligiendo
un cluster a 6.54 km.

**Causa raíz (reconfirma A18)**: re-clusterizar el **top-100 pixeles ya persistidos** con
`cluster_pixels_geographic(max_dist_km=1.5)` NO reproduce la selección real del pipeline,
que opera sobre el `hot_mask` completo del grid con el VRP per-pixel real y conectividad
de grilla 2D (`cluster_hotspots`). El top-N persistido es una muestra sesgada (los más
calientes de escena), y re-rankearla introduce ruido que mueve el centroide. **La
re-selección offline no sirve para estimar el match del pipeline actual.** Para eso solo
vale el reproceso real desde L1B.

PCC sube (+12.9) por la misma razón inversa: re-clusterizar su campo difuso de 6 focos da
a veces un centroide más cerca del punto MIROVA por azar, no por mejora real. No interpretar.

## Resultado 2 — decomposición Lascar febrero (esta SÍ es válida)

"Cráter presente/ausente" es una propiedad **factual** de los pixeles persistidos (no
depende del método de re-selección), así que esta parte es robusta. De 33 pasadas Lascar-feb
comparables, **10 son no-match** con el primary stale:

| Grupo | n | Significado | Acción |
|---|---:|---|---|
| Recuperables por re-selección offline | **0** | ningún no-match se arregla re-rankeando en disco | — |
| Cráter presente, aún no-match | 2 | 02-11 MODIS (cráter a 3.76 km, borde de tol 2 km) + 02-14 VIIRS (cráter a 1.06 km pero MIROVA reporta a 3.33 km = MIROVA más lejos que nosotros) | reproceso ayuda parcial |
| **Detection-loss (cráter AUSENTE)** | **8** | NINGÚN pixel persistido cae dentro del inner_radius (5 km); el más cercano a 5.9-13.9 km | **REQUIERE reproceso desde L1B** |

### Mecanismo físico de los 8 detection-loss (confirmado pixel-level, `loss_chars.txt`)

Record ganador (mayor VRP de escena, el que entra a la comparación) por noche
detection-loss, distancias desde `mirova_center` (`dmin` = pixel más cercano al cráter):

```
2026-02-08 06:45 MODIS_AQUA  npx=43 dmin=8.3  dmax=33.0 btmax=288K sum_vrp=1059
2026-02-10 08:00 MODIS_AQUA  npx=17 dmin=7.4  dmax=31.7 btmax=286K sum_vrp=177
2026-02-15 07:55 MODIS_AQUA  npx=20 dmin=7.4  dmax=32.4 btmax=286K sum_vrp=122
2026-02-28 01:00 MODIS_TERRA npx=11 dmin=9.5  dmax=28.2 btmax=288K sum_vrp=302
```

Son **MODIS — Terra Y Aqua** (corregido S88: una versión previa del doc decía "todos
TERRA ~01-02:30 GMT"; la auditoría adversarial mostró que los records *ganadores* de
varias noches son AQUA ~06-08 GMT — ver nota de integridad arriba). En todas, durante la
erupción de febrero, los pixeles MODIS se concentran en el Salar a 7-33 km (`dmin` nunca
baja de 5 km en estas noches; ni un pixel dentro del inner_radius de 5 km del cráter). El
pipeline viejo (`bt_path_hot` ON + sin gates intra-radio S84/S85 + `vrp_max`) llenó el
top-100 `anomaly_pixels` con esos pixeles lejanos (off-nadir, elongación sec³ A36),
**y el cráter literalmente no quedó en la lista persistida**. Esto NO se puede arreglar
offline — la información del cráter se perdió al persistir solo el top-N.

> Nota de definición: `sum_vrp` aquí es la suma de TODOS los anomaly_pixels de la escena
> (no el cluster dominante) — por eso 02-08 da 1059 MW. El `scene_vrp` que el script usa
> para elegir el record ganador es el VRP del cluster mayor (`cluster_pixels_geographic`),
> un valor menor. Dos definiciones distintas; ninguna afecta las métricas del JSON.

> Contraste con VIIRS-I 375m las MISMAS noches: casi todas matchean (stale_ok=True), con
> el cráter presente a <2 km. VIIRS-I, con su menor footprint y los gates actuales, sí
> retuvo el cráter. El problema es específico de **MODIS** durante la erupción.

El pipeline ACTUAL no produciría el detection-loss: `bt_path_hot=False` (S40), gates
intra-radio Path D (S84) y second-pass (S85) cortan los pixeles lejanos espurios antes del
top-N, y `vent_anchored` ancla al cráter. Pero **confirmarlo requiere correr el pipeline de
hoy sobre los L1B de febrero** — no es deducible de los datos en disco.

## Conclusión operacional

- **La pregunta 1 se responde NO**: no hay atajo offline para estimar el match del pipeline
  actual. La re-selección sobre el top-N persistido es un proxy sesgado que empeora el
  match (A18 reconfirmado). El 74.7% de S87 sigue siendo el único número que tenemos, y es
  un piso contaminado por la deuda histórica — no se puede "limpiar" sin reproceso.
- **La pregunta 2 se responde con datos**: el gap de Lascar es **deuda de detección real**,
  no solo de selección. 8/10 no-match MODIS-feb perdieron el cráter en el top-N persistido
  (estrategia vieja). Eso **fortalece** el diagnóstico S87 (deuda histórica) con un
  mecanismo más preciso: no es que el primary apunte lejos teniendo el cráter a mano — es
  que el cráter no está en los datos guardados.
- **¿Vale el reproceso (Frente A pleno)?** Es la **única** vía de validación, y ahora con
  más razón (el atajo offline quedó descartado). Acotar a **Lascar feb-2026 MODIS-TERRA**
  (~10-12 noches). MODIS no corre local en Windows (pyhdf roto) → GitHub Actions con
  timeout chunked (regla S15). ROI: flipear ~10 records de Lascar (los 8 detection-loss +
  2 borde) → ~+6pp Lascar, ~+1pp global. Es validación documentable, **no fix** (el NRT ya
  hace lo correcto desde S38-S40). No bloqueante.

## Lección metodológica S88 (la importante)

1. **A18 reconfirmado y reforzado**: NO usar re-selección offline sobre `anomaly_pixels`
   persistidos como proxy del pipeline. El top-N guardado está sesgado a los pixeles más
   calientes de escena; re-clusterizarlo da centroides distintos a la selección real sobre
   el grid completo. Sirve solo para la propiedad factual "cráter presente/ausente", no
   para estimar match/magnitud.
2. **Integridad de proceso (error propio S88)**: escribí doc/commit/PR con números
   anticipados antes de reconciliar contra el output del script. Regla dura: **ningún
   número entra a un doc/commit/PR sin estar copiado del output verificado del script en
   la misma sesión.** Verification-before-completion aplica también a docs, no solo a código.

## Escudo anti-drift respetado

- NO se cambió el criterio de selección (vent_anchored sigue validado por S87, que SÍ usó
  el primary real persistido como ground truth de selección).
- NO se tocó pipeline NRT — análisis 100% offline, A45 no disparada, sin tag defensivo.
- NO huella/G1/exclude_zones/gate-intra-radio nuevos.

## Artefactos

- `reselect_offline.py` — reproducible (el script es correcto; lo que estaba mal era la
  redacción del doc, no el código).
- `reselect_results.json` — métricas per-vol + decomposición Lascar (números reales).
- `lascar_feb_table.txt` — tabla por-noche de los 10 no-match.
- `loss_chars.txt` — caracterización pixel-level de las 8 noches detection-loss (correctas).
- `post_reproc_clean.txt` — output verificado del validador post-reproceso (§8).

---

## 8. FRENTE A EJECUTADO — el reproceso confirma la hipótesis (2026-05-29)

El workflow `reproc-s88-lascar-validation.yml` (GH Actions run 26650931800, **success**)
reprocesó Lascar feb-2026 con la config operacional ACTUAL (perfil
`_s88_reproc_validation`, que `extends: mirova_equivalent` → vent_anchored + bt_path OFF
S40 + gates intra-radio S84/S85). `post_reproc_validate.py` comparó el match 1:1 anomalía
dominante (tol 2 km) entre el operacional persistido (primary stale) y el reproceso.

**Números copiados del output verificado (`post_reproc_clean.txt`):**

| | Match Lascar feb (tol 2 km) |
|---|---:|
| old (operacional stale, estrategia vieja) | 23/35 = **65.7%** |
| new (config actual, reproceso) | 33/35 = **94.3%** |
| **Δ** | **+10 records (+28.6pp)** |

### Los records MODIS que flipean al cráter

Todos los no-match MODIS de febrero pasan de tener el primary en el Salar (17-31 km) a
apuntar al cráter (≤2 km, donde MIROVA reporta):

```
night        mir   old      new    nota
2026-02-09   1.0   23.38 →  1.73   FLIP→OK
2026-02-10   1.0   27.25 →  1.82   FLIP→OK
2026-02-11   1.41  24.21 →  0.34   FLIP→OK
2026-02-12   1.41  29.60 →  1.09   FLIP→OK
2026-02-13   1.41  (none) →  2.02  FLIP→OK   (record nuevo, no existía en operacional)
2026-02-14   1.41  17.73 →  1.42   FLIP→OK
2026-02-15   1.41  31.20 →  1.54   FLIP→OK
2026-02-19   2.0   (none) →  1.50  FLIP→OK   (record nuevo)
2026-02-22   2.0   (none) →  2.04  FLIP→OK   (record nuevo)
2026-02-27   2.0   23.25 →  2.88   (cráter recuperado, queda apenas fuera de tol)
```

Los 2 que NO matchean post-reproceso quedan a ~3 km, es decir el reproceso **sí recuperó
el cráter** (ya no 17-31 km) pero apenas fuera de la tolerancia de 2 km: 02-08 MODIS
(new=3.38) y 02-14 VIIRS (new=0.86 vs MIROVA a 3.33 — acá somos NOSOTROS los que estamos
más cerca del cráter que MIROVA). Divergencia física menor, NO el error catastrófico
previo. **Cero regresiones**: todos los records que ya matcheaban (02-17 MODIS eruptivo,
los ~22 VIIRS) siguen matcheando.

### Conclusión (cierra Frente A)

El reproceso **valida con datos limpios la hipótesis de S87/S88**: el "gap de Lascar" era
**deuda de datos históricos, NO un bug del pipeline actual**. Con la config operacional de
hoy, el pipeline elige el cráter (0.3-2.9 km) en vez del Salar (17-31 km) en los eventos
eruptivos de febrero. Mecanismo confirmado: `bt_path` OFF (S40) impide que los pixeles
saturados off-nadir del Salar (A36 sec³) llenen el top-100, los gates intra-radio
(S84/S85) los cortan, y `vent_anchored` ancla al cráter.

Esto cierra el ciclo abierto en S87: lo que el atajo offline NO pudo demostrar (porque el
cráter ya no estaba en los pixeles persistidos), el reproceso desde L1B lo confirmó. El
NRT viene haciendo lo correcto desde S38-S40; los records de febrero quedaron stale solo
porque el NRT no reprocesa histórico.

> Nota: este reproceso es de VALIDACIÓN en `data/_s88_reproc_validation/` (aislado). NO se
> propaga al operacional `data/mirova_equivalent/` — el dashboard sigue mostrando los
> records históricos stale de febrero. Si se quisiera "limpiar" el dashboard histórico,
> habría que reprocesar a `mirova_equivalent` (decisión aparte; A45 + tag defensivo).
