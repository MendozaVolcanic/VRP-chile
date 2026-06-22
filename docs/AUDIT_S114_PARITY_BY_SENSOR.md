# AUDIT S114 — Re-auditoría de paridad por sensor + frente MODIS far→summit

**Fecha**: 2026-06-19. **Ground-truth**: CONS+OCR frescos descargados hoy (A17),
`experiments/_s114_audit/mirova_fresh/{cons,ocr}.csv` (CONS hasta 2026-06-19 13:55).
**Ventana**: 2026-05-01 .. 2026-06-30. **Scripts (fuente de verdad, A-S91)**:
`experiments/_s114_audit/parity_by_sensor_s114.py`, `discriminante_far2summit.py`.

> Regla de evaluación: gate del dashboard = lo que ve el operador = `mirovaEqVrp`
> (`distance_class=="summit"` AND `pc.centroid_dist_km<=inner` AND `0<pc.vrp_mw<=50000`),
> verbatim de `frontend/index.html:950`. pc.vrp_mw NO record.vrp_mw (A10).

## 1. Resultado agregado por sensor (rollup 11 Tier A)

| Sensor | n ALERTA | recall CRÁTER (pipeline) | recall DASHBOARD (operador) | brecha (far→summit oculto) |
|---|---|---|---|---|
| **MODIS** | 19 | **89.5%** (17/19) | **15.8%** (3/19) | **14 noches** |
| **VIIRS750** | 70 | 85.7% (60/70) | 85.7% (60/70) | 0 |
| **VIIRS375** | 216 | 99.1% (214/216) | 99.1% (214/216) | 0 |

- **CRÁTER** = el pipeline encontró el cluster crateriano genuino (pc.vrp>0, centroid≤inner).
- **DASHBOARD** = además `distance_class=="summit"` (lo que se muestra).
- La diferencia CRÁTER−DASHBOARD **es** el bug A46 far→summit.

**Lectura geológica**: en MODIS el pipeline SÍ encuentra el cráter (90%) pero el dashboard
lo oculta (16%). La caída NO es falta de detección — es 100% el bug de etiquetado A46.
VIIRS375/750 no tienen brecha (sus pérdidas son FN reales sub-umbral, no coherencia).

## 2. Anatomía del frente far→summit (864 records, casi todos MODIS)

Records con cluster crateriano real (centroid≤inner, pc.vrp>0) pero `distance_class=="far"`:
**864 totales** (862 MODIS + 2 VIIRS750), repartidos en los 11 vols. Pero al cruzar con el
estado MIROVA-MODIS de cada noche:

| | far→summit en noche ALERTA (legítimo) | far→summit en noche RUTINA (candidato A69) |
|---|---|---|
| n | **28** (Láscar 23, Villarrica 3, Chaitén 2) | **834** (los otros 8 vols: 0 ALERTA) |

Solo 28 records (≈14 noches) son recuperación de recall legítima. Los 834 restantes son
candidatos a artefacto A69 (campo difuso topográfico; MIROVA-MODIS no emitió ALERTA).

## 3. ¿Hay discriminante físico real-vs-A69? — NO (5 candidatos refutados)

`discriminante_far2summit.py` (campos persistidos verificados, A48; NO `nti_max` top-level
que es None en MODIS — usar `diag_nti_max`):

| Discriminante | ALERTA (legítimo, n=28) | RUTINA (A69, n=834) | ¿Separa? |
|---|---|---|---|
| `diag_nti_max` | med −0.91 | med −0.91 | **No** — idéntico (MODIS 1km siempre integra fondo → NTI plano) |
| ΔT = t_max−t_bg | med 16.6 K | med 11.7 K | Solapa fuerte (ALERTA min 6.9; RUTINA max 42.9) — no gate limpio |
| `diag_n_first_pass_summit` | (gate S111) | — | Refutado en A/B S111 + artefacto de versión (campo nuevo #433) |
| **co-validación VIIRS375** | 100% | **90%** | **No** — VIIRS375 ve foco sub-píxel casi cada noche (recall 99%) |
| dispersión final_hotspot | spread 13 km | (mezclado) | **No** — disperso en los 11 vols (13-24 km), no objeto externo único |

**Conclusión geofísica**: MODIS 1 km no resuelve el foco del cráter. El "cluster crateriano
MODIS" es mayormente gradiente topográfico (A69) que se enciende casi igual en noches ALERTA
y RUTINA. MIROVA-MODIS emite ALERTA solo cuando hay un foco fuerte (19 noches/2 meses en 11
vols). **No existe discriminante físico persistido** que separe los 28 legítimos de los 834
A69 → el guard far→summit general es **trap A48/A55** (igual que S113 evitó re-derivar 2527).

## 4. Caso Láscar / Salar de Atacama (el menos malo, pero tampoco quirúrgico)

El `final_hotspot` de Láscar cae al SW (lon −67.88..−67.97) = **Salar de Atacama**, con
t_max ~280-288 K (costra salina cálida por inercia térmica nocturna) pero `diag_nti_max ~−0.91`
(plano = calor de fondo, NO anomalía NTI). Mecanismo A69: el final_hotspot se elige por **MIR
absoluto** scene-wide, no por NTI → MIROVA es inmune (detecta por NTI contextual).

Ya existe `exclude_zones: Salar de Atacama` (volcanoes.yaml:130, S16) **pero** centrado en
(−23.5, −68.2) r=25 km → no cubre el borde ESTE del Salar (lon −67.88) donde caen los píxeles
que roban el hotspot.

**Concentración (verificada offline)**: de las **23 records far→summit Láscar en noche ALERTA
(15 noches únicas), 23/23 tienen el FH en la zona Salar (lon<−67.84); 0 en otro lado.** En las
15 noches ALERTA, TODAS están robadas por el Salar. (RUTINA: 46/49 también Salar, 3 otro.)
Láscar tiene foco crateriano crónico REAL (volcán muy activo, fumarólico permanente, desierto
de altura — NO nevado, NO A69 topográfico). El ladrón concentrado contrasta con los nevados
(FH disperso = A69 difuso).

**⚠️ Extender el exclude_zone Salar NO es el camino (corrección S114, sanity check Nicolás).**
`exclude_zones` está en la lista de parches que MISSION.md prohíbe expandir ("remediación de
drift, no causa raíz"). **MIROVA no excluye el Salar — simplemente no lo detecta** (NTI plano
~−0.91 = no incandescencia; su inmunidad es intrínseca al método NTI, no una máscara).
La causa raíz de nuestro bug es que el `final_hotspot` (del que sale summit/far) se elige por
**MIR absoluto** scene-wide → salta al Salar. Es el drift A69/D11 (MIR absoluto vs NTI). Un
exclude_zone taparía el síntoma con el mismo tipo de parche que MISSION veta, y no escala a los
nevados (ladrón difuso, sin objeto excluible).

El fix MISSION-compliant sería que la etiqueta summit/far derive de la **detección genuina por
NTI** (como MIROVA), no del píxel más caliente en MIR absoluto. **Pero el NTI absoluto MODIS
está clavado ~−0.91 para todo** (cráter, Salar y difuso por igual — §3) → ni elegir por NTI
separa en MODIS. Habría que ir al dNTI contextual / señal first-pass = **el frente D11/A69
grande**, ya veredictado "sin discriminante suficiente" en S111.

## 5. Veredicto del frente (parte MODIS)

El frente "MODIS far→summit (A46 inverso)" del bloque S114 **se descompone en dos sub-frentes
de naturaleza distinta**:

**(a) Nevados (~800 records, NdC/Tupun/Villarrica/Copahue/Lastarria/PP/Llaima/Isluga/PCC) —
TRAP A48, NO accionable como guard.** Es la cara display del problema D11/A69 (final_hotspot
disperso por MIR absoluto; campo difuso topográfico). S111 ya lo investigó con A/B riguroso
(`enable_honest_anchor_modis`, run 27662625697) → **veredicto NO ADOPTAR** (gate
`first_pass_summit` necesario pero no suficiente). La re-auditoría S114 lo confirma con data
fresca + 5 discriminantes refutados. Un guard far→summit general aquí inundaría el dashboard
con difuso A69. **No tocar** — pertenece al frente D11/A69 de detección (root fix, abierto).

**(b) Láscar (15 noches ALERTA + ~46 RUTINA) — el ladrón es identificable (Salar) PERO el fix
no es un exclude_zone (anti-patrón MISSION, §4).** El caso es real (foco crateriano crónico) y
limpio de diagnosticar, pero la raíz es la misma que (a): el `final_hotspot` por MIR absoluto.
El único fix MISSION-compliant es alinear el etiquetado con la detección NTI, que en MODIS 1 km
no separa (NTI clavado) → cae dentro del frente D11/A69 grande. **No accionable con un parche.**

Operacionalmente **NO hay pérdida de alerta** en ningún caso: VIIRS375 cubre las noches al 99%
(A62: cobertura por-noche sana; lo que falla es la completitud por-sensor de la serie MODIS).

→ **Veredicto S114**: el frente far→summit MODIS es, en sus dos mitades, la cara display del
problema D11/A69 (MIR absoluto vs NTI). No hay fix de parche MISSION-compliant; el camino real
es el frente D11 de detección (diseño grande, ya con historia S104-S111). El recall MODIS bajo
en el dashboard es esperado dada la física (MODIS 1 km no resuelve focos sub-píxel) y está
cubierto por VIIRS375. **Cerrar el frente como confirmación de D11; no introducir exclude_zone.**

## 6. VIIRS750 y VIIRS375 (deepdive subagentes A26)

Detalle en `VIIRS750_DEEPDIVE.md` / `VIIRS375_DEEPDIVE.md` (+ `.json`). Ambos: **sanos, sin
brecha far→summit, nada accionable**.

**VIIRS750** — recall 85.7% (CONS) / 85.9% (CONS+OCR). Las 10 FN: 2 sub-umbral (a), 0
recuperable (b), 8 marginal MIROVA <0.3 MW (c). En **9/10** detectamos el cráter (record
summit, centroid dentro de inner) pero `pc.vrp=0` porque `nti_max` está en el piso (~−0.91 a
−0.94): foco **sub-píxel para 750 m** — vimos el cráter, no lo cuantificamos (techo físico
M-band, A54). Los 2 far→summit Tupungatito (06-09) = artefacto A69 ring glaciar (`nti_max`
−0.925 plano, t_bg ~251 K, ΔT inflado por contraste cráter/glaciar A19); MIROVA RUTINA esa
noche → el gate S100 los dejó en `far` con razón. **No recuperar.**

**VIIRS375** — recall 99.1% (CONS) / 99.5% nocturno-puro / 98.8% (CONS+OCR nocturno). Las 2
"FN": (1) NdC 06-12 = **falsa FN**, la ALERTA es diurna 14:18 local (A76, perderla es correcto
night-only); (2) Lastarria 06-14 = FN real sub-umbral A54 (MIROVA 0.03 MW; tenemos el record
summit anclado pero pc.vrp=0). OCR no cambia el panorama (45 artefactos diurnos A76 detectados;
2 PCC difusas sub-umbral perdidas). Sobre-detección RUTINA 84.3% = recall real sub-umbral
conocido (A54/A68), no bug. **Sensor sano.**

## 6b. Barrido sistemático de discriminantes D11 (brainstorming S114, "probar todo y descartar")

Script: `experiments/_s114_audit/discriminant_sweep.py`. Métrica AUC (Mann-Whitney) entre
POS = far→summit Láscar (foco real, n=72) y NEG = far→summit nevados RUTINA (A69, n=785).

| Discriminante | AUC | Veredicto |
|---|---|---|
| `first_pass_summit` (gate S111) | 0.415 | ❌ no separa (nevados tienen *más*) |
| `diag_nti_max` / paths dNTI,ETI,NTI,BT | ~0.50 | ❌ inútil (NTI MODIS clavado ~−0.91) |
| ΔT, σ_bg, nti_std | 0.64–0.74 | ❌ débil, solapa |
| co-val VIIRS375 *presencia* | (90% ambos, S106) | ❌ no separa |
| contexto temporal Method-2 (persistencia) | Láscar 100% / nevados 96-100% noches | ❌ ambos persistentes |
| pc magnitud / n_pixels | 0.40–0.56 | ❌ |
| **co-val VIIRS375 *magnitud*** | **0.882** | ⚠️ separa pero cross-sensor + corte imperfecto |
| régimen per-vol (Láscar≠nevado) | (por construcción) | ⚠️ MISSION S99 "no conmuta por régimen" |

Gate VIIRS-magnitud (mejor candidato) trade-off: thr=0.15 → 100% Láscar-ALERTA / deja pasar
23% nevados-A69; thr=0.30 → 83% Láscar / deja pasar 3% nevados. No hay corte limpio.

**Conclusión del barrido**: NINGÚN discriminante per-record MISSION-puro separa foco real
(Láscar) de A69 difuso (nevados) en MODIS 1 km. Los dos que separan violan MISSION (cross-
sensor / per-régimen). El far→summit MODIS es la cara display de D11/A69 **irreducible en MODIS
1 km** dentro del marco clon-literal.

**Origen del cluster difuso nevado (descarta revertir gate S85 como fix)**: de los far→summit
nevados con campo presente (n=184), solo **23% son cluster solo-por-recaptura-S85**
(`first_pass_summit==0 & recapture>0`); el **77% vienen del first-pass genuino**
(`first_pass_summit>0`) = el Test 2/3 dNTI disparando sobre el difuso (el "leak C1", A74).
Revertir S85 (anti-patrón A55) tocaría solo el 23% y además afecta a Láscar (21% también
solo-recaptura). La infidelidad raíz vs MIROVA está en la **detección first-pass dNTI** que
genera cluster sobre el difuso suave — frente D11 de detección, ya refutado 3× (V1/V2/fondo-local).

## 6c. Frente B (D2 — N·σ Tabla 1 Coppola 2016a) — REFUTADO (workflow adversarial S114)

Workflow `d2-nsigma-viability` (4 agentes: papers verbatim + recompute σ + escéptico + veredicto;
~17 transformaciones single + ~45 pares). Artefactos: `experiments/_s114_audit/frenteB_result.json`,
`sigma_ratio_sweep_result.json`. **Veredicto: B no es viable.**

**Tabla 1 verbatim (Coppola 2016a SP426.5, `documentacion/sp426_5.txt:336-356`)**: MODIS noche
**5σ ROI1 (summit 5×5km) / 10σ ROI2 (scene 50×50km)**, día 15σ; C1=0.003/0.01/0.02. El σ es
**global per-imagen** (media+std de todos los píxeles suitable), NO contextual local (los 8 vecinos
solo computan el dNTI; el gate compara contra m+C2·σ global). Nuestro `diag_nti_std` = std del NTI
del **anillo de fondo** (`process_modis.py:461`).

**El N·σ canónico (= lo que B propone replicar) NO separa**: AUC 0.72, Láscar med 3.5σ vs nevados
3.1σ. **A 5σ literal, Láscar-ALERTA queda 0/23** → subir el umbral apaga el foco real, no corta el
difuso. Candidatas con AUC>0.80 que NO sobreviven la prueba física:

| Candidato | AUC | Por qué se refuta |
|---|---|---|
| (b) NTImax/sd_dnti | 0.87 | cociente mixto sin base de paper (A35); colas se cruzan al revés (PP 11.9, Llaima 9.5 > Láscar max 7.4) |
| (d) N·σ BT clásico | 0.81 | BT absoluto (A69-vulnerable); colas solapan |
| **roi95_nsigma** (hallazgo nuevo S114) | 0.87 | **KILLER cat-b verificado**: focos reales en nevado (Villarrica lava-lake 1.01-2.14, Chaitén domo 1.9-2.0) caen en la banda del difuso (0.44-2.62); umbral p90=1.88 mata 2/5 (40%) de cat-b real. Captura geometría de escena Láscar, no física universal |
| co-val VIIRS375 | 0.88 | cross-sensor — MISSION lo prohíbe |

**Razón física (de fondo)**: a 1 km, el píxel MODIS mezcla la lava sub-píxel con nieve/hielo/roca
fría → exceso suave, distribuido, de bajo contraste. El difuso topográfico A69 produce **el mismo
tipo de objeto físico**. El σ no los distingue porque no hay diferencia de forma que capture — solo
cambia el origen (volcánico vs orográfico), invisible en el dato persistido. La única señal que
separa (VIIRS375) lo hace porque 375 m **resuelve** el foco sub-píxel que 1 km no puede (A77:
instrumento correcto). Lo que MIROVA tiene y quizás no replicamos del todo es **arquitectura**
(dual-ROI con C2 distinto, segundo pase refinador, NTI_bk por regresión cuadrática), NO un σ más
alto — y el veredicto estima que ni eso resuelve el solapamiento físico, solo lo atenúa (requeriría
verificar nuestro código + A/B que no destruya cat-b; frente grande, beneficio incierto).

**Conclusión D11-MODIS**: el far→summit MODIS es **irreducible por gate/umbral/discriminante post-hoc
per-record** dentro del clon literal. Concuerda con S104/S105/S106/S108 (A69). El recall MODIS está
cubierto por VIIRS375 (A77, mejor sensor sub-píxel). No hay pérdida de alerta.

## 6d. Auditoría de fidelidad de la detección MODIS vs Coppola 2016a (workflow S114)

Workflow `modis-detection-fidelity-audit` (7 agentes: 5 componentes + síntesis + crítica
adversarial, verificada `file:line`). **Veredicto: la detección MODIS es FIEL a Coppola 2016a.**

> Nota A48: los componentes 1 y 2 reportaron un "gap crítico" (path dNTI solo C1, sin μ+C2·σ).
> La síntesis+crítica lo **refutaron leyendo el código**: `process_modis.py:718` sobrescribe
> `hot_mask_2d = fp_hot` con first-pass ON → el path operacional es `first_pass_tests_2_and_3`,
> que SÍ aplica la rama OR completa `min(C1, μ+C2·σ)` dual-ROI. El "C1-only" era un contador
> diagnóstico (`diag_n_dnti_ctx_path`), no el hot_mask. Subagentes confusos, corregidos con file:line.

| Componente Coppola 2016a | Nuestro código | Fidelidad |
|---|---|---|
| Tests 2∧3 (`dNTI>C1 OR dNTI>μ+C2σ`, AND dNTI×dETI) | `first_pass_tests_2_and_3` (detection_context.py:449-468) | **full** |
| μ/σ global "all suitable pixels within the image" | `build_unsuitable_mask` pool global per-ROI | **full** |
| Unsuitable §267-273 (edge + dNTI/dETI<−0.1) | `ENABLE_UNSUITABLE_FILTERS_267_273`=True (default) | **full** |
| Dual-ROI C1/C2 Tabla 1 (0.003/5 summit, 0.010/10 scene) | profile + detection_context.py:449-455 | **full** |
| Second Run (excluye activos, recomputa μ/σ, §323-325) | `second_pass_adjacent` (:773/786) | **full** |
| ETI regresión cuadrática (Eq.4-5) | `compute_eti_scene_quadratic` | **full** |
| Kernel 8-vecinos media aritmética | `_nanmean_8neighbors_fast` (D1 resuelto S17) | **full** |
| **§298-300 (retiro Test 1 K1 del pool μ/σ)** | `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK`=False (default) | **partial = GAP #A** |

**GAP #A — único gap de fidelidad literal real**: no aplicamos el retiro de los píxeles Test 1 K1
del pool μ/σ (§298-300, flag OFF). PERO: (1) **no ataca el difuso** — al contrario, retirar
outliers positivos del pool BAJA σ → umbral `μ+C2·σ` más permisivo; (2) **irrelevante para el
difuso nevado** (NTI≈−0.91, lejos de K1=−0.8, casi nada que retirar); (3) merece su propio A/B
como **fidelidad literal independiente**, NO como solución al difuso. (El §323-325, retiro de
activos Tests 2/3, SÍ se cumple vía second-pass — la síntesis lo había omitido, la crítica lo corrigió.)

**Veredicto: el difuso pasa GENUINAMENTE, no por bug.** A 1 km el gradiente cumbre-fría/valle-tibio
produce outliers espaciales reales en dNTI **y** dETI (un píxel 272 K rodeado de 281 K es, a escala
local 8-vec ≈3 km, una discontinuidad positiva real) que cruzan C1=0.003 — la definición del paper
aplicada a topografía nival a 1 km. El ETI cancela el gradiente de gran escala (50 km), pero el dNTI
contextual opera a escala local donde la discontinuidad persiste. La BT (único campo donde difuso y
foco difieren) **no entra al gate** dNTI/dETI. → La separación debe venir de un **eje ortogonal**
(ancla `first_pass_summit` D11 [NO ADOPTAR S111], co-val cross-sensor [MISSION prohíbe], cap físico),
no de tocar C1/C2/μ/σ (alto riesgo de matar cat-b — el KILLER ya verificado). Consistente con S104
(V1 refutado) y S106 (fondo-local refutado en todo el barrido).

## 7. Síntesis ejecutiva

1. **VIIRS (ambas bandas) sano** — recall limitado solo por física de resolución / sub-umbral
   real (A54), no por bugs. Nada accionable.
2. **MODIS dashboard 16% = bug de etiquetado A46, no falta de detección** (pipeline-cráter 90%).
3. El frente far→summit MODIS (ambas mitades, nevados y Láscar) es la **cara display de
   D11/A69** (final_hotspot por MIR absoluto vs NTI). **No hay fix de parche MISSION-compliant**
   — un exclude_zone está vetado por MISSION y MIROVA no excluye zonas (es inmune por NTI).
4. **El frente B (N·σ Tabla 1) está REFUTADO** (§6c): el N·σ canónico no separa foco de difuso
   (solapan a ~3σ); a 5σ literal se apaga el foco real de Láscar. Ningún discriminante post-hoc
   per-record MISSION-puro separa.
5. **La detección MODIS es FIEL a Coppola 2016a** (§6d, auditoría file:line + adversarial): la
   arquitectura dual-ROI 5σ/10σ + Tests 2∧3 OR + second-run + ETI cuadrático YA está implementada
   y activada, y es fiel. **El difuso pasa GENUINAMENTE, no por bug** — es la física de 1 km
   (outlier espacial real sobre topografía nival). Único gap de fidelidad literal: **GAP #A**
   (§298-300 retiro Test 1 K1 del pool μ/σ, flag OFF) — irrelevante para el difuso (lo afloja),
   merece su propio A/B como fidelidad independiente.
6. **D11-MODIS far→summit es IRREDUCIBLE** dentro del clon literal: agotadas TODAS las vías —
   detección (gate post-hoc, N·σ Tabla 1, arquitectura completa, todas fieles/refutadas) Y los
   tres ejes ortogonales: ancla `first_pass_summit` (NO ADOPTAR S111), cross-sensor VIIRS375
   (MISSION prohíbe), **cap físico de magnitud (REFUTADO S114: AUC 0.45 vrp / 0.62 npx; el difuso
   med 0.66 MW está ENTRE Láscar 0.42 y cat-b 0.82 → cualquier cap mata cat-b o pasa difuso;
   KILLER: Chaitén/Villarrica reales caen en la banda del difuso)**, y **contexto temporal Method-2
   (REFUTADO S114: el difuso es tan variable en el tiempo como el foco, CV 0.84-1.22 ambos → la
   línea base temporal no separa)**. **Cerrar el frente.**

   **Razón geológica de fondo (cierre definitivo)**: a 1 km, un foco volcánico sub-píxel débil y el
   gradiente topográfico difuso producen la **misma firma en TODOS los ejes medibles** — espectral
   (NTI/dNTI/ETI), de magnitud (VRP/n_pixels), espacial (compacidad/dispersión) y temporal
   (variabilidad). La única diferencia (origen volcánico vs orográfico) no deja huella en el dato.
   El único instrumento que los separa es VIIRS375 (resuelve el foco sub-píxel) — A77.
7. **Cero pérdida de alerta operacional** — VIIRS375 cubre (A77: instrumento correcto para
   sub-píxel). Es completitud por-sensor de la serie MODIS, no FN.
