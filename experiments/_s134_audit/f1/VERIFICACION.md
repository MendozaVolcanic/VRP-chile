# S134 · F1 — VERIFICACIÓN (contexto limpio, read-only)

Verificador independiente. No recibí el razonamiento del auditor, sólo el informe, el script y las
salidas. Todo lo de abajo está anclado a un tool result de esta sesión.

**Reproducción del instrumento.** Corrí el script del auditor sin tocarlo
(`python experiments/_s134_audit/f1/f1_posicion_magnitud_paridad.py --ancla vent --out <scratchpad>`)
y salieron **exactamente** los mismos números de cabecera: 18.373 records, 0 duplicados, 1.371
ALERTAS (CONS 980 · OCR 391), **1.161 pares · 86 sin pasada · 124 FN · 3.889 nuestros sin MIROVA**,
|dt| mediana 0,0 min. Los 8 controles del auditor reproducen al decimal: Láscar 0,22 km · 79,8 % ·
n=208; pareo Láscar 93,2 %; `centroid_dist_km` del pipeline vs mi haversine = 0,000 km en los 11;
0 fallbacks f5 en los 992 pares. Script propio: `verif_f1.py` (mismo directorio).

Nada del repositorio fue modificado; sólo agregué `verif_f1.py`.

---

## Veredicto por hallazgo

| # | veredicto | mi gravedad | (gravedad del auditor) |
|---|---|---|---|
| H1 criterio NO CUMPLE | **CONFIRMADO** | 3 | 3 |
| H2 el anillo vive en lo no publicado | **CONFIRMADO** descriptivo · **PLAUSIBLE** la lectura causal | 3 | 3 |
| H3 el déficit escala con nº de píxeles | **PLAUSIBLE** con reserva fuerte (el covariable no es el cúmulo) | 3 | 3 |
| H4 gradiente cenital | **CONFIRMADO** con matiz (no es universal) | 2 | 2 |
| H5 MODIS 43 `far` | **CONFIRMADO** exacto | 2 | 2 |
| H6 Isluga | patrón **CONFIRMADO**; interpretación sube de sospecha a **PLAUSIBLE fuerte** | 3 | 2 |
| H7 59 OCR diurnas | sustancia **CONFIRMADA**; un número **REFUTADO** (la ventana horaria) | 1 | 1 |
| H8 M-band multi-píxel sobre-estima | **CONFIRMADO** | 2 | 1 |
| H9 dos FN sin cúmulo | **CONFIRMADO** exacto | 1 | 1 |

---

### H1 · CONFIRMADO · gravedad 3

Reproduje bin a bin: 0,744 · 0,621 · 0,659 (n 559/294/132), ρ = −0,105 (p 8,8e-4, n=992), criterio
3 evaluables de 9, **0 cumplen**.

**Caminos por los que podría estar mal, y qué encontré:**

1. *Simpson: ¿un efecto real dentro de cada volcán se cancela al agrupar?* Es el riesgo mayor,
   porque cada volcán vive casi entero en un solo bin. Lo medí (V6): ρ dentro de volcán con n≥20
   da **signos mezclados** — Láscar −0,337, Chaitén −0,329, Lastarria −0,154, Isluga −0,030,
   PP +0,082, PCC +0,090, Tupungatito +0,178. No hay un efecto consistente escondido. El de Láscar
   (p=7e-7) ocurre en un rango de 0,02-0,73 km: es estructura fina intra-cráter, no el eje de la
   hipótesis.
2. *¿El criterio estaba armado para fallar?* No. La banda [0,7;1,4] es la de paridad del proyecto
   y el n≥5 es razonable. Al contrario: es **generoso** con la hipótesis, porque basta que el bin
   lejano quede fuera de banda para cumplir.
3. *¿La magnitud usada es la del operador?* Sí, y lo verifiqué contra el código, no contra el
   informe (ver «verificado limpio» abajo).
4. *«0 de 9 cumplen» sobrevende.* Son 6 no evaluables + 3 que fallan. El informe lo dice en su
   tabla, pero el titular de la primera línea no. Cosmético.

El veredicto de refutación queda en pie por los cuatro caminos.

### H2 · CONFIRMADO como descripción · PLAUSIBLE como explicación · gravedad 3

Los números reproducen (pares 0,15-0,59 km; sin MIROVA 2,4-2,8 km; cuatro cuadrantes).
La pregunta del encargo —¿sesgo de selección?— la respondí estratificando por **magnitud publicada**
(V3), que es lo que separa las dos lecturas:

| mag_pub | pares: n · d mediana · ≤0,5 km | sin MIROVA: n · d mediana · ≤0,5 km |
|---|---|---|
| <0,1 MW | 377 · 0,97 · 31 % | **1.828** · 2,74 · 7 % |
| 0,1-0,3 | 424 · 0,35 · 62 % | 282 · 0,93 · 34 % |
| 0,3-1 | 159 · **0,16** · 94 % | 34 · **0,16** · 82 % |
| 1-3 | 32 · 0,13 · 97 % | 8 · 0,09 · 100 % |

**Lecturas posibles, enumeradas:**

1. **Sesgo de selección puro** (MIROVA publica sólo lo fuerte, y lo fuerte está en el cráter). La
   tabla lo apoya en parte: en los bins ≥0,3 MW los dos conjuntos son **indistinguibles** (0,16 vs
   0,16), y el **85 %** del conjunto «sin MIROVA» (1.828 de 2.152) vive en <0,1 MW. Es decir:
   «MIROVA no lo publica» y «es débil» no son ejes separables en esta data — son casi el mismo eje.
2. **Dice algo del pipeline** (el anillo es el A69: MIR absoluto siguiendo la frontera nieve-roca
   cuando no hay foco fuerte). Sobrevive al control: dentro del mismo corte de magnitud <0,3 MW y
   dentro del mismo volcán el hueco **persiste** — Villarrica pares 0,16 vs sin MIROVA 2,80 (n=261);
   Tupungatito 0,23 vs 2,62; PCC 0,29 vs 2,49; Chaitén 0,28 vs 2,61. La magnitud sola no lo explica.
3. **Artefacto del pareo**: 136 de los 2.152 V375 «sin MIROVA» (**6,3 %**) sí están a ±20 min de una
   alerta, y quedaron fuera sólo porque otro granule fue el elegido. Infla el conjunto, no lo crea.
4. **Umbral de reporte de MIROVA** en vez de posición: MIROVA reporta desde ~0,1 MW; nuestro piso es
   más bajo. Indistinguible de (1) con esta data.

Conclusión: la **descripción** es correcta y reproducible; la **frase** «el anillo vive en lo que
MIROVA no publica» debería leerse «el anillo vive en los records débiles», porque la confirmación de
MIROVA es un proxy de magnitud, no un eje independiente. El auditor ya se abstuvo de proponer un gate
y marcó explícitamente que la clasificación real/artefacto no está medida — eso es correcto y lo
respaldo. Bajo la gravedad de la *conclusión causal*, no del hallazgo.

Comando: `python experiments/_s134_audit/f1/verif_f1.py` → bloque `V3`.

### H3 · PLAUSIBLE con reserva fuerte · gravedad 3

La correlación reproduce exacta (V375: 0,670 · 0,658 · 0,895 · **1,162**; V750: 0,536 → 1,584). Pero
tres cosas que el informe no dice cambian su lectura (V4):

1. **El covariable no es el cúmulo.** `n_anomaly_pixels` es el conteo de la ESCENA. El cúmulo
   (`pc.n_pixels`) se queda en **1-2 píxeles en los cuatro bins** de V375 (1,0 · 2,0 · 2,0 · 2,0). El
   título del hallazgo («el número de píxeles **retenidos**») y su mecanismo candidato («MIROVA
   integra más píxeles del mismo cúmulo») describen el cúmulo, que es justamente lo que no varía.
   Lo que varía es cuánta anomalía hay en la escena — un proxy del tamaño de la fuente.
2. **MIROVA sube también.** ρ(n_px, MIROVA) = **+0,364** en V375. Nuestra magnitud sube más rápido
   (ρ=+0,561; mediana 0,09 → 0,405 = ×4,5 contra 0,14 → 0,36 = ×2,6 de MIROVA), así que **algo**
   queda tras descontar el tamaño — pero no todo, y la razón es muy sensible al denominador
   (ρ(MIROVA, razón) = **−0,411**), que es la alternativa que el encargo pedía considerar.
3. **La corroboración M-band es de otro mecanismo.** En V750 ρ(n_px, MIROVA) = **−0,113** y el bin
   ≥10 px tiene MIROVA 0,27, *más bajo* que el bin de 1 px (0,63), con `pc.n_pixels` = 11. O sea: ahí
   la razón sube porque **nosotros** sumamos de más — que es el H8 del propio informe, no «MIROVA
   retiene más». Citar V750 como «repite el patrón» junta dos mecanismos opuestos.

El hallazgo señala algo real (escalamos distinto que MIROVA con el tamaño de la fuente), pero el
mecanismo propuesto no está sostenido por el covariable medido. El auditor ya marcó el mecanismo
como SOSPECHA; agrego que el covariable tampoco mide lo que su nombre sugiere.

### H4 · CONFIRMADO con matiz · gravedad 2

0,809 → 0,690 → 0,605 reproduce. Camino de error revisado: **composición por volcán** (el bin ≥40°
tiene más Láscar/Isluga, que son los de peor razón). Estratifiqué dentro de volcán (V5): el gradiente
es nítido en **Láscar** (0,711→0,421), **Isluga** (0,745→0,457) y **Tupungatito** (0,807→0,665), y
está **ausente o invertido** en PCC (1,026→1,108), PP (0,976→1,166) y Chaitén (1,353→1,440);
Lastarria no es monótono. O sea: el efecto existe, pero el número agregado lo exagera por
composición, y no es universal. El informe lo presenta como si lo fuera.

### H5 · CONFIRMADO exacto · gravedad 2

5 summit / 48 summit∪far (43 `far` + 5 summit), los 43 **todos de Láscar**, d mediana **1,56 km**,
razón 0,900 (far) y **0,910 IQR [0,48; 2,26]** para el conjunto, **FN restantes = 0**. Idéntico.

### H6 · patrón CONFIRMADO · interpretación PLAUSIBLE FUERTE (sube de sospecha) · gravedad 3

202 pares, **0,0 %** a ≤0,5 km, d mediana 0,86; sobre los 513 publicados el cuadrante SW se lleva
355. Todo reproduce. Y encontré en el repo la evidencia que el auditor dijo no haber cotejado:

- **Isluga es el único de los 11 Tier A cuyo `vent_lat/vent_lon` tiene 2 decimales** (−19,15 /
  −68,83). Los demás: 5-7 decimales los que fueron refinados (Láscar, Villarrica, Chaitén, PP, PCC,
  Tupungatito), 3 decimales los que quedaron en el catálogo (Copahue, NdC, Llaima, Lastarria).
  Dos decimales a esa latitud son **±0,55 km en latitud y ±0,52 km en longitud** de sola
  cuantización: el orden exacto del offset observado.
- El propio `mirova_center` de Isluga (**−19,15212 / −68,83269**, 5 decimales) está a **0,37 km al
  SW** del `vent_*` — la **misma dirección** del sesgo.
- Nuestro centroide típico (−19,1560 / −68,8347) está a **0,48 km del `mirova_center`** y a
  **0,83 km del `vent_*`**: nuestro cúmulo está casi el doble de cerca de la referencia de MIROVA que
  de la coordenada declarada.

Con esto, «la coordenada declarada del cráter de Isluga es un valor de catálogo redondeado» pasa de
corazonada a lectura respaldada por el propio YAML. Lo que sigue **NO VERIFICADO**: dónde está el
cráter activo real (requiere imagen/DEM, no lo hice) y si el foco es el cráter o una fumarola SW.
Subo la gravedad a 3 porque toca toda distancia publicada de un Tier A y es barato de comprobar.

Comando: `verif_f1.py` bloque `V9` + el chequeo de decimales del YAML.

### H7 · sustancia CONFIRMADA · un número REFUTADO · gravedad 1

Correctos: **59** (V375: Láscar 26 + Lastarria 33 — el «60» que da un conteo ingenuo incluye 1
alerta MODIS de Láscar), **100 % OCR**, VRP mediano **2,87 MW**, y el pipeline es nocturno (nuestros
records V375 caen en las horas UTC 04-07). La conclusión —no son FN— está bien.

**REFUTADO**: «todos entre **17:24 y 18:24** UTC». Contra el propio `resultados.json` del auditor, el
rango es **17:18 a 19:00** y **14 de los 59 (24 %) caen fuera** de la ventana declarada
(17:18 ×2, 18:30 ×2, 18:36, 18:42, 18:48 ×2, 18:54 ×4, 19:00 ×2). También «sin ningún record nuestro
a menos de 10 h»: el record nuestro más cercano de cualquier sensor está a **6,4 h** (mediana 7,8 h).
Ninguna de las dos correcciones toca la conclusión —19:00 UTC siguen siendo las 15:00 locales, pleno
día— pero son números transcritos que su propia salida no respalda (A90 / no-transcribir-números).

### H8 · CONFIRMADO · gravedad 2 (el auditor puso 1)

Reproduce. Le subo la gravedad porque, como muestro en H3.3, **este** es el mecanismo que explica el
tramo M-band que H3 se atribuye: es un régimen doble de magnitud dentro de un mismo sensor, no ruido
de n chico.

### H9 · CONFIRMADO exacto · gravedad 1

16 FN sin `primary_cluster`; 14 con MIROVA ≤0,23 MW y dos de 0,60 y 2,15; volcanes PCC 6, Tupungatito
3, NdC 2, Isluga 2, Lastarria/Láscar/PP 1. Idéntico.

---

## Hallazgos propios

### P1 · El script mide 607 alertas ambiguas y el informe no lo dice · gravedad 2

`meta.n_ambiguas = 607`: **607 de las 1.371 alertas (44 %)** tienen ≥2 granules nuestros distintos
dentro de ±20 min. El número lo calcula e imprime el propio script, está en `resultados.json` y en
`salida_vent.txt`, y **no aparece en `F1_HALLAZGOS.md`** (`grep -n "607\|ambigu"` → 0 líneas en la
sección relevante). Peor: la sección «VERIFICADO LIMPIO» certifica «**Pareo robusto**» sin
mencionarlo. El impacto real es acotado y lo cuantifiqué —el elegido siempre es el de |dt|=0, y sólo
**136 de los 2.152** V375 «sin MIROVA» (6,3 %) son hermanos no elegidos— pero un número del
instrumento que se mide, no se reporta y además se cubre con un certificado de limpieza es
exactamente el patrón que la línea base roja existe para evitar.

### P2 · El covariable de H3 no es lo que su interpretación afirma · gravedad 3

Ver H3.1. `pc.n_pixels` = 1-2 en los cuatro bins de V375. Es un hallazgo propio porque cambia el
mecanismo candidato, no sólo la confianza.

### P3 · La coordenada de Isluga está redondeada a 2 decimales y es la única así · gravedad 3

Ver H6. Evidencia del repo que el informe declaró no haber buscado.

### P4 · La ventana horaria de H7 no la respalda su propia salida · gravedad 1

Ver H7.

---

## VERIFICADO LIMPIO (lo que fui a buscar como error y no lo era)

- **Réplica de la regla del operador.** Fui a `frontend/index.html` directo. `mirovaEqVrp` (l. 1039)
  usa `if (r.distance_class && r.distance_class !== "summit")` —condición **falsy**, más laxa que el
  `== "summit"` estricto del script— y para records sin `primary_cluster` cae a `r.vrp_mw ??
  r.vrp_mir_mw`, camino que el script no replica. Parecía una divergencia segura. **No lo es**: en
  los 18.373 records hay **0** con `primary_cluster` y `distance_class` falsy, y **0** sin
  `primary_cluster` con `vrp_mw`/`vrp_mir_mw` > 0 (los 6.267 `None` son todos sin cúmulo y con
  magnitud 0). Las dos implementaciones coinciden sobre esta data.
- **`f5CoreMagnitude`** (l. 1115) devuelve el campo persistido `f5_core_vrp_mw` cuando es número, y
  `mirovaEqVrpCore` cae a `base` si es ≤0 — idéntico al script. 0 fallbacks en los 992 pares.
- **Convención A48**: `Counter(sensor)` da MODIS_TERRA/AQUA, VIIRS_{SNPP,NOAA20,NOAA21} y sus `_750`;
  el bucket del script es correcto.
- **Dedupe**: 0 duplicados `(sensor, granule)` en la ventana.
- **La ancla**: `centroid_dist_km` del pipeline coincide con haversine desde `vent_*` (0,000 km en
  los 11). La línea base roja mueve los 5 volcanes con `vent ≠ catálogo` y deja quietos los 6 que
  coinciden — comprobado leyendo el YAML, no el informe.
- **H5, H9, controles del auditor**: reproducen al decimal.

## NO VERIFICADO

- Clasificación real vs artefacto de los 3.889 «nuestros sin MIROVA» (el auditor tampoco la midió y
  lo declara).
- Nº de píxeles que MIROVA integra por pasada — el CSV no lo trae; el mecanismo de H3 sigue sin
  contraste directo.
- Posición del cráter activo de Isluga contra imagen/DEM/GVP (sin acceso externo en esta sesión).
- Qué hace `pipeline/audit_metrics.py` con las OCR diurnas (riesgo señalado en H7; no lo leí).
