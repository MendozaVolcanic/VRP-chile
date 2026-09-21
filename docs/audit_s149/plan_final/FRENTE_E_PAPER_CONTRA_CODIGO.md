# FRENTE E (S149): el paper contra el código, pieza por pieza

Auditor del frente E, 2026-09-21. Sólo lectura sobre el repo. Scripts, salidas e imágenes en
`experiments/_s149_audit/frente_e/`. Árbol en `main` (`1dba6c5f9` al empezar).

**Eje que estrena**: qué piezas propias son HIJAS del Test 1 integrado (desaparecen solas al apagarlo)
y cuáles siguen vivas en la configuración más literal que ya se corrió (brazo F, mayo 2026); y dónde
quedó escrito, sin marca, el veredicto que fundó esa acumulación.

**Cómo se leyó cada cosa** (para que el verificador sepa qué pesa cada afirmación):

- Perfil: resuelto desde `pipeline.profile` con `VRP_PROFILE=mirova_equivalent`, 144 atributos
  (`resolver_perfil.py` → `perfil_mirova_equivalent.json`). Nunca el YAML (A89).
- Paper: `documentacion/sp426.5.pdf`, páginas idx 2 a 8 (impresas 3 a 9) **renderizadas a imagen**
  (`render.py`, PNG `sp426_idx2..8.png`) y leídas como imagen (A95). Las citas de Coppola 2016a de este
  informe salen de esas imágenes. Campus 2022, Campus 2024, Coppola 2026 y el capítulo de Coppola **no
  los rendericé en esta sesión**: todo lo que diga de ellos va rotulado HEREDADO (de
  `docs/MIROVA_DIVERGENCES.md` D25/D32, que declaran haberlos renderizado en S140, S141 y S147).
- Código: `pipeline/detection_context.py` (l. 60 a 143, 208 a 563, 699 a 1085), `pipeline/process_viirs.py`
  (l. 728 a 837 y 925 a 1908), trozos de `process_modis.py`, `anchor.py`, `frontend/index.html`
  (l. 1000 a 1260 y 1455 a 1488). `process_viirs_mod.py` sólo por `grep`: lo que diga de M-band más
  allá de los flags es HEREDADO de `docs/audit_s138/EJE_2_matriz_conformidad_pdf.md`.
- Medición: run 35599902448 (mayo 2026, 2026-05-01 a 2026-05-31, 11 Tier A, brazos B y F), extraído
  con `git archive` con ruta al scratchpad (28 MB, borrado al terminar).

**Aviso de cobertura**: existe una matriz de conformidad previa, muy buena, hecha desde el PDF en S138
(`docs/audit_s138/EJE_2_matriz_conformidad_pdf.md`, 24 pasos, 18 mecanismos extra). No la repito: la
re-verifiqué contra el código de hoy en los puntos que deciden y le agrego lo que no tenía (la
dependencia respecto del Test 1, la medición sin Test 1, el origen del veredicto de S27). Sus números
de línea están corridos (A101); los de este informe son de hoy.

---

## 0. La respuesta corta a la pregunta de Nicolás

Sí, hay enredo, y tiene una forma precisa. De los 28 flags encendidos del perfil, **8 ejecutan el algoritmo del paper** (los Tests 2 y 3 con su
Tabla 1 nocturna, el segundo pase, los filtros de no aptos, el área fija). Alrededor hay tres capas propias:

1. **El Test 1 integrado y su séquito** (9 flags encendidos y 15 constantes que sólo existen para él o
   para reparar sus efectos): prioridad de fuente, filtro contextual, `keep_peak`, tres fondos alternativos,
   `lbg_global_compatible` por volcán, el modo del ancla honesta. Apagado el Test 1, **toda esa capa
   queda inerte sin tocar nada más** (medido: 0 records con `triggered_test1` o `source=test1` en los
   dos brazos de mayo).
2. **La capa de magnitud y publicación** (cúmulo anclado al cráter, modo píxel único, magnitud focal,
   tope de 5 MW, núcleo F5, cerca `far`, filtros de artefacto del tablero, filtro de 25 km y
   `max_cluster_pixels` en `store.py`). Esta capa **sigue entera** sin el Test 1 y es donde el número
   publicado deja de ser la suma del paper (Ec. 8).
3. **Tres desvíos dentro del propio núcleo literal** que siguen aun en el brazo F: la compuerta de 3 K
   (D22), el segundo pase sin condicionar (D19) y el fondo por mediana de anillo con recorte a cero
   (D25). S138 midió que los dos primeros se compensan entre sí.

Y el hallazgo de conocimiento perdido: **el veredicto "el literal puro pierde recall, no reabrir" que
justificó toda la capa 1 se midió en S27 con un perfil que no tenía los Tests 2 y 3 del paper** (se
escribieron 16 días después). Ese perfil sigue en el repo con el nombre `_mirova_literal`, y hoy es
MENOS literal que producción. Ver hallazgo E-01.

---

## 1. INVENTARIO 1: lo que hacemos y el paper no dice

Columnas: **Hija del T1** = la pieza sólo actúa si el Test 1 integrado disparó o ganó la fuente
(leído en el código; S = sí, N = no). **Viva en F** = deja marca en los records del brazo F de mayo
(`piezas_vivas_sin_test1_salida.txt`; "n/m" = no deja marca persistida, no medible así).

### 1.a Detección

| # | Pieza (flag = valor efectivo) | Qué hace físicamente | ¿En los papers? | Problema que vino a resolver | Hija del T1 | ¿El problema sigue sin T1? |
|---|---|---|---|---|---|---|
| X1 | **Test 1 integrado en el ROI** `ENABLE_TEST1_PATH=True`, `TEST1_ROI_KM=3.0`, `TEST1_INNER_RING_KM=1.0`, `TEST1_K_SIGMA=3.0`, `TEST1_MIR_RELATIVE=0.02` | Suma el exceso de radiancia MIR de un disco de 3 km y dispara si supera 3 sigmas propagadas (`process_viirs.py:1100-1151`) | **No.** El Test 1 del paper es por píxel: «NTI_PIX > K1 (Test 1)» (SP426.5 p. 6, imagen `sp426_idx5.png`). La única suma del paper es la magnitud (Ec. 8, p. 9). D30 ya lo registra | Recall sub-píxel en S27 (Villarrica, Lastarria, PP) | es el padre | Ver E-01: el problema se midió contra un "literal" sin Tests 2 y 3. Con el primer pase de hoy y sin T1, VIIRS 375 conserva 288 de 296 alertas en mayo y 137 de 143 en septiembre (`docs/S149_RESULTADO_CONECTIVA_MAYO.md` §7, HEREDADO) |
| X2 | **Compuerta de temperatura** `NTI_BT_SANITY_K=3.0` dentro de los Tests 2 y 3 | Exige que el píxel esté 3 K sobre la mediana del anillo (`detection_context.py:546`) | **No.** La fórmula de los Tests 2 y 3 (p. 7, `sp426_idx6.png`) sólo tiene dNTI y dETI contra C1 o mu + C2 sigma. D22 | Nació para el camino NTI absoluto (D22, commit `59846e897`) y se heredó | N | n/m. Sigue viva en B y F. S138: el segundo pase sin condicionar la anula |
| X3 | **Segundo pase sin condicionar** `ENABLE_SECOND_PASS_CONDITIONED=False` | Reaplica los Tests 2 y 3 a toda la caja aunque el primer pase esté vacío y sin restringirse a los vecinos de lo activo (`detection_context.py:906-907, 964-965`) | **Distinto.** Paper p. 7: «applied only if one or more pixels have been detected by the previous tests, and focuses on refining the hotspot detection for the pixels adjacent to those already flagged» | Ninguno declarado: es el comportamiento histórico de S46 | N | **Viva en F**: 81 de 580 cúmulos con magnitud de VIIRS 375 (14 %) y 46 de 115 de VIIRS 750 (40 %) existen SÓLO por el segundo pase |
| X4 | **Conectiva `min`** `ENABLE_TESTS_23_PROSE_BRANCH=False` | Umbral efectivo = el menor entre C1 y mu + C2 sigma (`detection_context.py:525`) | **Ambiguo en el propio paper.** Fórmula p. 7: «dNTI_PIX > C1 or dNTI_PIX > mu + C2 sigma». Prosa, mismo párrafo: «the parameter C1 implies that a minimum threshold needs to be exceeded» y «when highly variable scenes are analysed, the detection (...) is achieved using statistical analysis of the whole scene». Y p. 9: «a value of C2 ≥ 10 will efficiently avoid false detections but will cause the omission of more than 25% of the small alerts»: bajo `min`, C2 sólo puede actuar en las escenas donde mu + C2 sigma queda BAJO C1 (muy homogéneas) y nunca puede subir el umbral por sobre C1; que el autor describa a C2 como el control principal entre omisiones y falsas apunta a `max`, pero no lo prueba (lectura mía, SOSPECHA; la pregunta a Coppola sigue siendo la que decide) | n/a (es lectura, no parche) | N | Es LA palanca medida en S148 y S149 |
| X5 | **ROI1 = círculo de 3 a 20 km por volcán** `ENABLE_ROI1_BOX_PAPER=False` | Área que recibe el umbral laxo (`roi1_summit_mask`, `detection_context.py:299-325`) | **Distinto.** «inner region (ROI1) consists of a box (5 × 5 km) centred on the volcano's summit» (p. 3, `sp426_idx2.png`). D18 | Valores de los KML de MIROVA usados como clasificación visual (S14) y reutilizados como ROI1 | N | n/m. Desde #738 la caja llega al segundo pase; nunca medida |
| X6 | **Banda 21 primaria en MODIS** `ENABLE_MODIS_B22_PRIMARY=False` | MIR de baja ganancia (ruidosa) como primaria (`process_modis.py:550-567`) | **Distinto.** «by using the L21 or L22 radiance, depending on band 22 saturation (or not)» (p. 3). D21 | Histórico del repo | N | **Viva y decisiva**: en el brazo B el primer pase de MODIS marca píxeles en 730 de 733 pasadas de mayo (99,6 %), y con `max` en 3 de 733. Un detector que dispara en el 99,6 % de las escenas no está detectando |
| X7 | NTI de MODIS con banda 31 (`process_modis.py:80, 261`) | TIR de 11,03 µm en vez de 12,02 | **Distinto.** «L_TIR is the radiance of the TIR channel (L32)» (p. 4, `sp426_idx3.png`). D20 | Histórico | N | n/m |
| X8 | Saturados MODIS a NaN (`process_modis.py:558-561`), `ENABLE_BT_SAT_SECONDARY_GUARD=True` | Borra el píxel más caliente de un paroxismo | **Distinto.** «with the exception of the pixels with DN = 65 533» (p. 3). D24 | Basura de PP 2026-03-18 (F28) | N | n/m, sin casos |
| X9 | Refit iterativo a 3 sigma de la regresión (`detection_context.py:770-788`) | Ajusta NTIbk tres veces descartando residuos | **No** (p. 5: un ajuste). D29 | Proteger el ajuste de los píxeles calientes | N | n/m, siempre activo, sin flag |
| X10 | Sólo noche `ENABLE_DAYTIME_MODIS=False` | Descarta pasadas diurnas | **Distinto** (Tabla 1 tiene columnas de día). D27, deliberado | Contaminación solar | N | deliberada |
| X11 | Camino dNTI contextual heredado `ENABLE_DNTI_CONTEXTUAL_PATH=True` (+ `ENABLE_DNTI_DUAL_ROI`) | Máscara `dNTI > C1` sola, sin Test 3 (`detection_context.py:276-282`). **No entra a la detección**: `hot_mask_2d = fp_hot` la pisa (`process_viirs.py:1303`) | No es un test del paper | Era el detector antes de S46 | N | Sigue viva como INSUMO: alimenta la magnitud focal (X14) y el filtro contextual del T1 (X18). Es un segundo detector corriendo en la sombra |
| X12 | `ENABLE_DUAL_ROI_BT=True`, `N_SIGMA_MIR_SUMMIT/SCENE=5/10` | Test de temperatura con los números de C2 | **No** (D31) | S26 | N | **Inerte**: `ENABLE_BT_PATH_HOT=False` lo pone en ceros (`process_viirs.py:998-999`). Un flag en `True` que no hace nada |

### 1.b Séquito del Test 1 (todas Hijas del T1; con `ENABLE_TEST1_PATH=False` quedan inertes)

| # | Pieza | Qué hace | Por qué existe | Evidencia de que cuelga del T1 |
|---|---|---|---|---|
| X13 | `ENABLE_TEST1_PRIORITY_WEAK_CLUSTER=True`, `TEST1_WEAK_CLUSTER_EPS_MW=0.01` + Regla D | El T1 le gana la fuente al cúmulo contextual si éste es débil o lejano | El T1 y el cúmulo daban posiciones distintas (A46) | `process_viirs.py:1770-1774`: exige `test1_centroid_lat is not None` |
| X18 | `ENABLE_TEST1_CONTEXTUAL_FILTER=True` + **`ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK=True`** (ctxpeak, D10, D19) | Recorta el disco del T1 a lo contextualmente anómalo y conserva siempre el píxel más caliente | El T1 sumaba el halo nival entero: 8 a 30 veces MIROVA | `process_viirs.py:1846`: `final_hotspot_source == "test1"` |
| X19 | `ENABLE_TEST1_INTERMEDIATE_BG=True` (anillo 1,5 a 3 km), `ENABLE_TEST1_LBG_GLOBAL=True` + `lbg_global_compatible` por volcán (Láscar, NdC, Lastarria) | Tres fondos alternativos para la magnitud del T1 | La magnitud del T1 salía 0 o 4,4 veces MIROVA según el fondo | `process_viirs.py:1874-1896`, sólo se usa en el recompute del T1 |
| X20 | `HONEST_ANCHOR_TEST1_MODE="vent"`, `ENABLE_HONEST_ANCHOR=True`, `_VIIRS750=True` | Publica a 0,0 km los records donde manda el T1 | El centroide del disco del T1 lo arrastra el gradiente topográfico (A69) | `anchor.py:82-89`: sin T1 la cascada devuelve siempre el centroide del cúmulo contextual |
| X21 | `ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750=True` | Magnitud focal en M-band | ídem | HEREDADO de S138 («sólo camino Test 1»); consistente con mayo: 0 marcas `focal_magnitude` en V750 en B y F |
| X22 | 8 flags apagados del T1: `_NTI_INTEGRAL`, `_NTI_COVALIDATION`, `_LOCAL_BG_NTI`, `_SPATIAL_CORE`, `_PIXEL_FILTER`, `_LAVA_LAKE_EQ16`, `_NULL_CORRECTED`, `_K1_*` (estos dos últimos son del Test 1 del PAPER, ver inventario 2) | Intentos sucesivos de curar al T1 | S99 a S147 | apagados |
| X23 | `isValidDetection`: respaldo `triggered_test1 === true` para records sin cúmulo (`frontend/index.html:1476`) | Cuenta como detección un T1 sin cúmulo | legacy | explícito |

### 1.c Magnitud, selección del cúmulo y publicación (NO son hijas del T1: siguen todas)

| # | Pieza | Qué hace físicamente | ¿En los papers? | Problema que resolvía | Viva en F (mayo) |
|---|---|---|---|---|---|
| X14 | `ENABLE_FOCAL_CLUSTER_MAGNITUDE=True` + `FOCAL_CLUSTER_KEEP_PEAK=True` (MODIS, `process_modis.py:1165-1169`) | Suma sólo los píxeles del cúmulo que además pasan el dNTI heredado (X11), más el pico | No | Campo difuso topográfico de MODIS (A69, D11) | B: 732 de 732 cúmulos MODIS. F: 3 de 3 |
| X15 | `ENABLE_SINGLE_PIXEL_SUB_MW_MODE=True`, 5 MW, hasta 3 píxeles | Publica el **máximo** de los píxeles del cúmulo, no la suma | **Contrario.** «the total radiative power is calculated as being the sum of the single RP_PIX» (Ec. 8, p. 9, `sp426_idx8.png`). D32 (HEREDADO: Campus 2022 y 2024 y Coppola 2026 dicen suma de todos los alertados) | Inflado bajo 5 MW (F52, S77), cuando el T1 y el anillo ya inflaban | F: 570 de 580 en V375, 110 de 115 en V750. **Donde cambia el número** (cúmulo summit de 2 o 3 píxeles): 139 de 450 en V375 (31 %), 17 de 90 en V750 (`single_pixel_efecto_salida.txt`) |
| X16 | `ENABLE_VENT_ANCHORED_CLUSTERING=True` | El cúmulo primario es el más cercano al cráter, no el de más energía | No. El paper no elige cúmulo: suma todo | Salares y lagos lejanos ganaban el primario (D8') | F: `pc.vrp` distinto de la suma de escena en 339 de 580 (V375), 112 de 115 (V750) |
| X17 | Tope `PATH_D_ONLY_CAP_MW=5.0` con `t_bg<270 K` | Censura la magnitud a 5,0 MW si no disparó ni BT ni K1 | No | Cirrus sobre fondo frío, 80 a 510 MW (D9) | B: 68 MODIS, 1 V750. F: 0. **Bajo `max` el problema que resolvía desaparece** (SOSPECHA razonable: n de un mes) |
| X24 | Fondo = **mediana** del anillo de 5 a 25 km (`detection_context.py:1083`), `ENABLE_LOCAL_KERNEL_BG=True` sólo en 5 volcanes (`volcanoes.yaml`: PCC, Villarrica, Chaitén, PP, Lastarria; no existe en M-band) | Contra qué se mide el exceso | **Distinto.** «L_4bk is estimated from the arithmetic mean of all the pixels surrounding the active one (or around the active cluster)» (p. 8, `sp426_idx7.png`). D25 | kernel-bg: lagos y halos (S58 a S62); por volcán porque Tupungatito empeoraba (A19) | n/m |
| X25 | Recorte `delta_L = max(., 0)` (`process_viirs.py:1478`, `process_modis.py:1070`) | Un píxel alertado más frío que el anillo vale 0,0 MW | No (el paper no lo necesita: su fondo es local) | -26 MW en S26 | n/m. Con `isValidDetection` (vrp > 0) convierte una detección en no publicada |
| X26 | Núcleo F5 `f5_core_vrp_mw` (`pipeline/f5_core.py`, `frontend/index.html:1119-1186`), por defecto en el tablero para I-band | Recorta la magnitud a 0,75 km del píxel pico (o BT ≥ 295 K) | No | Halo glaciar del camino contextual y del T1 (S95 a S97) | F: distinto de `pc.vrp` en 200 de 541 |
| X27 | `mirovaEqVrp`: cerca `distance_class != summit` → 0 y `pc.centroid_dist_km > innerKm` → 0 (`frontend/index.html:1056-1060`) | No publica nada fuera del `inner_radius_km` | No. La propia cabecera del código dice que MIROVA publica lejanas (l. 1039-1042). D13 | Salar a 24 km con 19.389 MW (S33) | F: 130 de 580 cúmulos V375 con magnitud no son `summit` |
| X28 | `isCirrusArtifact`, `isDiffuseFieldArtifact` (`frontend/index.html:1207-1238`) | Ocultan del gráfico VRP > 10 MW con t_max bajo 0 °C, o campo de 100+ píxeles | No | Camino contextual sobre cirrus (D9) | n/m. Mismo problema que X17: candidato a quedar sin sustrato bajo `max` (SIN MEDIR) |
| X29 | `store.py`: filtro a 25 km en círculo (`ENABLE_PIXEL_LEVEL_DISTANCE_FILTER=True`), rescate, `max_cluster_pixels=12` (Villarrica), tope 50 GW | Recorta o anula records después del procesador | No | varios | B MODIS: `partial_eruption_hotspot_too_far` en 712 de 732; `cluster_too_large` 11. F V375: 41 + 38 |
| X30 | Ancla de detección por volcán (`get_detection_anchor`: el cráter gana al centro de grilla; `run_pipeline.py:234, 277, 324`) | Centro del ROI1 y de las distancias | Distinto en la letra (el paper centra TODO en la cumbre GVP, p. 3), defendible | Tupungatito a 5 km del lago (S97, S98) | n/m. La caja de 50 km se centra en `lat/lon` y el ROI1 en el cráter: dos centros (D17) |
| X31 | Área nadir fija sin remuestreo `ENABLE_NADIR_FIXED_PIXEL_AREA_*=True`, `ENABLE_UTM_REGRID=False` | A_pix constante sobre píxeles que no miden eso | A medias: el área sí («1 km² for the resampled MODIS pixels», p. 9); el remuestreo y el bow tie no (p. 3). D17, D28 | sec³ inflaba 1 a 5 veces | n/m |
| X32 | `ENABLE_VRP_TIR_CONSISTENCY_GATE=True` | Compuerta del VRP TIR | n/a | F46 | **Inerte**: `ENABLE_VRP_TIR_OUTPUT=False` |

**Conteo** (script en línea sobre `perfil_mirova_equivalent.json`; denominador: 144 atributos, de los
cuales 63 son flags `ENABLE_*` y **28 están en `True`**). De esos 28: **8 son el algoritmo del paper**
(`FIRST_PASS_TESTS_2_AND_3`, `DUAL_ROI_FIRST_PASS`, `DUAL_ROI_SECOND_PASS`, `SECOND_PASS_ADJACENT`,
`UNSUITABLE_FILTERS_267_273`, `ERUPTION_PATH` como contenedor, y los dos `NADIR_FIXED` a medias);
**9 son el Test 1 integrado y su séquito** (`TEST1_PATH`, `TEST1_CONTEXTUAL_FILTER`, `_KEEP_PEAK`,
`TEST1_INTERMEDIATE_BG`, `TEST1_LBG_GLOBAL`, `TEST1_PRIORITY_WEAK_CLUSTER`, `HONEST_ANCHOR`,
`HONEST_ANCHOR_VIIRS750`, `FOCAL_CLUSTER_MAGNITUDE_VIIRS750`); **3 están en `True` y son inertes**
(`DUAL_ROI_BT`, `VRP_TIR_CONSISTENCY_GATE`, `HONEST_ANCHOR_MODIS_FIRST_PASS_GATE`, este último porque
`ENABLE_HONEST_ANCHOR_MODIS=False`); **2 son el detector en la sombra** (X11); y **6 son la capa de
magnitud y publicación** (`FOCAL_CLUSTER_MAGNITUDE`, `LOCAL_KERNEL_BG`, `SINGLE_PIXEL_SUB_MW_MODE`,
`VENT_ANCHORED_CLUSTERING`, `PIXEL_LEVEL_DISTANCE_FILTER`, `BT_SAT_SECONDARY_GUARD`). Además hay 14
constantes `TEST1_*` y `HONEST_ANCHOR_TEST1_MODE` que sólo existen para el Test 1 integrado. La
asignación a cada grupo es mía, por lectura del código; los totales (144, 63, 28, 14) son del script.

---

## 2. INVENTARIO 2: lo que el paper dice y no hacemos

Pasos de Coppola et al. 2016a en el orden del paper. Estado contra el código de HOY. «Literal» sólo
si corre en el perfil operacional con los valores del paper (no si existe detrás de un flag apagado).

| Paso del paper (página impresa) | Estado | Dónde (hoy) | D# | Flag que lo haría literal |
|---|---|---|---|---|
| DN inválidos fuera, saturados 65533 **conservados** (p. 3) | hecho distinto | `process_modis.py:558-561` | D24 | no hay |
| Quitar bow tie antes de remuestrear (p. 3) | **no hecho** en MODIS; VIIRS lo trae borrado de origen (HEREDADO S138) | `process_modis.py:509` sólo con regrid | D28 | `ENABLE_UTM_REGRID` (no es lo mismo) |
| L21ok = banda 22, y 21 donde la 22 satura (p. 3) | hecho distinto (21 primaria) | `process_modis.py:550` | D21 | `ENABLE_MODIS_B22_PRIMARY` |
| Recorte y **remuestreo** a grilla de 1 km, 50 × 50 km, centro GVP (p. 3) | caja de 50 km: hecho (`roi_mask_bbox`, `process_viirs.py:780`). Remuestreo: **no hecho**. Centro: dos centros | | D17 | `ENABLE_UTM_REGRID` (S124: centrado en el punto equivocado) |
| ROI1 caja 5 × 5 km, ROI2 el resto (p. 3 y 4) | hecho distinto | `detection_context.py:299-325` | D18 | `ENABLE_ROI1_BOX_PAPER` (cableado completo desde #738) |
| NTI con L32 (p. 4) | hecho distinto en MODIS (B31); VIIRS no tiene equivalente literal | `process_modis.py:80` | D20 | no hay |
| NTIapp, regresión cuadrática por imagen, ETI (p. 5) | hecho literal, con un refit que el paper no tiene | `detection_context.py:699-794` | D29 | no hay (parámetro `iterative_refit` sin flag) |
| dNTI y dETI: media aritmética de 8 vecinos, sin mirar nubes (p. 5) | **hecho literal** | `detection_context.py:483-486`, `CLOUD_MASK_BT_K=0.0` | | |
| No aptos: **borde de la matriz remuestreada** y dNTI o dETI < -0,1 (p. 5) | pisos -0,1: hecho literal en el primer pase. **Borde: declarado hecho, inerte** (E-03). Segundo pase: no hecho | `detection_context.py:64-78, 123-129` y `:923` | D26 (pool), borde sin D# | no hay |
| Test 1: NTI > K1 **activa** el píxel y lo **retira** de lo que sigue (p. 6) | **no hecho en ninguna de sus dos caras**: K1 se calcula (`process_viirs.py:1004-1010`, con compuerta de 3 K que el paper no tiene), entra a `combine_hot_paths` y `hot_mask_2d = fp_hot` lo pisa (`:1303`); no se retira del pool (`:1272-1274`) | | D23, GAP #A | `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` hace SÓLO la cara de retirar. **No existe flag que haga activo al píxel K1 con el primer pase encendido** |
| Tests 2 y 3 a la vez, Tabla 1 nocturna (p. 7) | valores: **hecho literal** (0,003 / 0,01 / 5 / 10 / -0,8, sin overrides). Conectiva: ambigua, hoy `min`. Más la compuerta de 3 K | `detection_context.py:525-552` | D22 | `ENABLE_TESTS_23_PROSE_BRANCH`; `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` (sólo I-band: **no existe para MODIS ni M-band**) |
| mu y sigma sobre todos los aptos de la imagen (p. 7) | hecho literal en el primer pase | `detection_context.py:492-510` | | |
| Activos de los Tests 2 y 3 eliminados del análisis posterior (p. 7) | hecho literal | `detection_context.py:910-923` | | |
| Segundo pase: sólo si hubo detección, sólo adyacentes (p. 7) | hecho distinto | `detection_context.py:906, 964` | D19 | `ENABLE_SECOND_PASS_CONDITIONED` |
| Tabla 1 diurna (p. 7) | no hecho, deliberado | | D27 | `ENABLE_DAYTIME_MODIS` |
| Fondo = media de los píxeles que rodean al activo o al cúmulo (Ec. 6, p. 8) | hecho distinto | `detection_context.py:1083`; `process_viirs.py:1445-1478` | D25 | `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375` y `_VIIRS750`; **no existe para MODIS** (ahí está `ENABLE_LOCAL_CLUSTER_MAGNITUDE`, corona) |
| RP_PIX = 18,9 × A_PIX × ΔL (Ec. 7, p. 8) | hecho literal en MODIS (`process_modis.py:87`); VIIRS con coeficientes empíricos S14 | | | |
| RP = **suma de todos los píxeles alertados** (Ec. 8, p. 9) | **hecho distinto en lo publicado**: X15, X16, X14, X17, X26, X27, X29 | | D32, D1, D13 | `ENABLE_SUM_VRP_REPORTING` (lo consume sólo `store.py`; no verifiqué qué publica) |
| Descarte visual a posteriori de nubes (p. 8) | n/a en NRT | | | |
| Mismos parámetros, grilla y ROI para todo volcán (p. 9: «by using the same spatial grid and ROIs») | hecho distinto: `inner_radius_km`, `local_kernel_bg`, `lbg_global_compatible`, `max_cluster_pixels` por volcán | `volcanoes.yaml`, `run_pipeline.py:243-252` | D18 parcial | |

Campus 2022, Campus 2024, capítulo de Coppola y Coppola 2026: **no leídos por mí**. Lo que el catálogo
declara verificado en página renderizada y que afecta este inventario (HEREDADO): fondo por píxel
como media de vecinos NO alertados y fondo total como suma de esos fondos (D25); suma de todos los
alertados como paso (iv) de la cadena NRT (D32). Ninguno agrega un paso de detección que no esté arriba.

---

## 3. Hallazgos, por gravedad

### E-01. El veredicto que fundó el Test 1 integrado («el literal puro pierde recall, no reabrir») se midió con un perfil sin los Tests 2 y 3 del paper, y sigue escrito sin marca donde se lee primero
- ARCHIVO:LÍNEA: `pipeline/profiles/_mirova_literal.yaml` (resuelto: `diff_perfiles.txt`);
  `docs/MISSION.md:173` y `:225-232`; memoria `project_s27_mirova_literal_negativo.md:104`
  («Decisiones consolidadas (no reabrir): el operacional con parches NO se va a clonar literal puro»)
  y `milestone_s27_h_s27_1_confirmada.md`; índice `MEMORY.md` («S27 Test1 cierra D4 (recall 50→80 %)»).
- QUÉ PASA. El fenómeno que S27 quería capturar es real: una fuente menor que el píxel que no levanta
  ningún píxel por sí sola. Pero el "literal" contra el que se midió que el paper no alcanzaba tenía,
  resuelto hoy desde `pipeline.profile`: `ENABLE_FIRST_PASS_TESTS_2_AND_3=False`,
  `ENABLE_SECOND_PASS_ADJACENT=False`, `ENABLE_BT_PATH_HOT=True` (el test de temperatura 5σ/10σ que D31
  muestra que no está en el paper). No podía ser de otro modo: `first_pass_tests_2_and_3` entró al
  repo el **2026-05-15** (`git log -S"def first_pass_tests_2_and_3"`: `958a7a189`, S46) y el A/B
  literal es del **2026-04-29** (`db602040b`). O sea: «5σ/10σ + dNTI no basta» se concluyó sin el
  Test 3 (dETI), sin la rama estadística y sin segundo pase. Y el remedio que se adoptó (T1 integrado,
  «100 % de recall» en Lastarria 60 de 60 y PP 28 de 28) es el detector que S147 mostró que dispara
  con ruido puro en 38 o más de 40 escenas: un recall sin negativos de un detector saturado (A98, A114).
  La rebaja llegó a D30 y a `MISSION.md:106`, pero **no** a `MISSION.md:173` («sub-pixel debe ir por
  Test 1 (Coppola 2016a SP426.5)»), ni a `:225-232` (que manda leer la memoria de S27), ni a los dos
  archivos de memoria, que siguen diciendo «no reabrir» y «cualquier cambio futuro debe mantener o
  mejorar este estado». Es A113 y es exactamente la clase de cosa del eje de esta auditoría.
- CÓMO SE VE EN EL DASHBOARD: es el origen del 86 % de publicación donde MIROVA no vio nada en VIIRS 375.
- CÓMO REPRODUCIRLO: `python experiments/_s149_audit/frente_e/diff_perfiles.py _mirova_literal`;
  `git log --format="%h %ad %s" --date=short -S"def first_pass_tests_2_and_3" -- pipeline/detection_context.py`.
- CONFIANZA: CONFIRMADO (perfil resuelto, fechas de git, textos leídos). SOSPECHA sólo en un punto: no
  reconstruí el YAML exacto del día del A/B; el de hoy tiene `enable_test1_path: true` porque se editó
  el 2026-04-30 (`5bf3660b9`), lo que sólo refuerza que el A/B del 29 no tenía ni T1 ni Tests 2 y 3.
- GRAVEDAD: **4**. No tuerce una alerta hoy; tuerce el plan: es el cierre que durante 120 sesiones
  hizo impensable la configuración que en septiembre y mayo da 2 a 3 % en vez de 86 %.

### E-02. Aun en el brazo más literal corrido (F), tres de cada diez magnitudes publicables de VIIRS 375 son el MÁXIMO de un cúmulo de 2 o 3 píxeles, no la suma que manda la Ec. 8
- SCRIPT:SALIDA: `single_pixel_efecto.py` → brazo F, mayo 2026, denominador cúmulos `summit` con
  `pc.vrp_mw > 0`: V375 139 de 450 (31 %) con `single_pixel_mode` y más de un píxel; V750 17 de 90;
  brazo B: 237 de 723 y 38 de 204; MODIS B 18 de 62. Código: `pipeline/single_pixel_mode.py`
  (`vrp_mw = max(per_pixel_vrp)`), llamado en `process_viirs.py:1580-1585`.
- QUÉ PASA. Un foco que cae en el límite entre dos píxeles reparte su radiancia; el paper la suma, el
  modo píxel único se queda con la mitad mayor. Se adoptó en S77 para frenar un inflado que venía del
  T1 y del fondo de anillo. Coincide en signo y en sitio con lo que A99 describe (la razón ~0,7 es
  «de selección: vecinos tibios que MIROVA suma»). SOSPECHA, no medido acá: cuánto del 0,7 explica.
  Atenuante leído: en I-band el tablero publica `f5_core_vrp_mw`, que vuelve a sumar lo que está a
  0,75 km del pico, así que el efecto pleno cae en **VIIRS 750 y MODIS** y en todo audit que use `pc.vrp_mw`.
- CÓMO SE VE EN EL DASHBOARD: magnitud sistemáticamente menor que la de MIROVA en focos de 2 o 3 píxeles.
- CONFIANZA: CONFIRMADO el conteo; SOSPECHA el vínculo con el 0,7.
- GRAVEDAD: 3.

### E-03. El filtro «píxeles del borde de la matriz» figura como hecho y no hace nada: marca el borde del gránulo entero, no el de la caja de 50 km
- ARCHIVO:LÍNEA: `pipeline/detection_context.py:64-78` y `:123`
  (`_edge_unsuitable_mask(roi_mask.shape)`); `pipeline/process_viirs.py:739-780` (no hay recorte:
  `lat`, `lon` y `roi_mask` tienen la forma del gránulo).
- QUÉ PASA. El paper saca del pool el marco de la matriz de 50 × 50 porque ahí la media de 8 vecinos
  está mal definida. Acá no hay matriz recortada: el "borde" es la fila y la columna 0 del gránulo,
  que casi nunca tocan la caja. En cambio el borde REAL de nuestra caja sí tiene el problema: el ETI
  es NaN fuera de `roi_mask` (`detection_context.py:793`), así que el dETI de los píxeles del marco se
  calcula con 3 a 5 vecinos (`_nanmean_8neighbors_fast` ignora NaN) y esos píxeles entran al pool y
  pueden alertar. S138 lo anotó en una celda de su matriz («el borde es el del granule entero») sin
  hallazgo ni D#; `ENABLE_UNSUITABLE_FILTERS_267_273=True` y la lista de VERIFICADO LIMPIO de S138
  (punto 6) lo dan por activo.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (ROI2, umbral estricto, y lo lejano no se publica). Bajo
  `max` importa más: el marco aporta colas al sigma que ahora decide.
- CÓMO REPRODUCIRLO: leer las dos líneas; sintético: `roi_mask` interior en una matriz mayor y contar
  `_edge_unsuitable_mask(shape) & roi_mask` = 0. **No lo corrí**: CONFIRMADO por lectura, efecto SIN MEDIR.
- GRAVEDAD: 2.

### E-04. `ENABLE_TEST1_NULL_CORRECTED` existe en el perfil y ningún procesador lo lee: un brazo de A/B con ese flag sería idéntico al control
- ARCHIVO:LÍNEA: `pipeline/profile.py:301`; `pipeline/test1_integrated.py:220, 307, 361, 467`
  (parámetro `null_corrected`); `grep -rn null_corrected pipeline/process_*.py scripts/*.py` → 0
  (`consumidores.py`: «SIN CONSUMIDOR POR NOMBRE», con frontera de palabra, repetido con `grep -i`).
- QUÉ PASA. El estadístico corregido del T1 está implementado y probado a nivel de función, pero el
  flag no llega a ninguna llamada de `compute_test1_mir` / `compute_test1_nti`. El bloque de arranque
  lo lista como «implementado y apagado» y como arrastre «brazo del Test 1 con el estadístico corregido
  para el experimental». Es A118 antes de ocurrir.
- CÓMO SE VE EN EL DASHBOARD: invisible. CONFIANZA: CONFIRMADO. GRAVEDAD: 3 (cuesta una corrida de 4 h y un veredicto falso de «sin efecto»).

### E-05. No existe la palanca para hacer literal el Test 1 del PAPER (K1) con el primer pase encendido, ni la de quitar la compuerta de 3 K en MODIS y M-band
- ARCHIVO:LÍNEA: `process_viirs.py:1229-1237` y `:1303`; `consumidores.py`:
  `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` sólo en `process_viirs.py`.
- QUÉ PASA. El interior de una colada de varios píxeles no es anómalo respecto de sus vecinos; el paper
  lo activa por NTI > -0,8. Acá ese píxel sólo cuenta si además pasa los Tests 2 y 3.
  `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` hace la mitad (retirar del pool) y, por su nombre y por
  `combine_hot_paths`, la otra mitad al revés. Una «configuración literal» armada sólo con flags
  existentes queda sin K1 y, en MODIS y VIIRS 750, con compuerta.
- CÓMO SE VE EN EL DASHBOARD: magnitud sub-estimada en fase efusiva (D23, gravedad 4 allí; efecto real SOSPECHA).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 3 para el plan.

### E-06. El perfil llamado `_mirova_literal` es menos literal que producción y es el nombre que cualquiera buscaría
- SCRIPT:SALIDA: `diff_perfiles.txt`: 29 diferencias contra producción, entre ellas primer y segundo
  pase apagados, BT path encendido, pisos de VRP 0,02 / 0,15 / 0,27, área sec³.
- QUÉ PASA: fósil de S27 con nombre de destino. Un comentario del procesador todavía lo cita como
  referencia viva (`process_viirs.py:1398-1399`).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2 (trampa para el próximo A/B).

### E-07. Un segundo detector corre en la sombra y decide la magnitud de MODIS
- ARCHIVO:LÍNEA: `process_viirs.py:1056-1084` (se calcula), `:1303` (no detecta),
  `process_modis.py:1165-1169` (decide qué píxeles suman).
- QUÉ PASA: la máscara `dNTI > C1` sola (sin Test 3, con compuerta, conectiva propia) ya no detecta,
  pero recorta la magnitud de 732 de 732 cúmulos MODIS del brazo B. Cambiar la conectiva del primer
  pase a `max` no cambia esta máscara: los dos quedan con criterios distintos. No medí el efecto.
- CONFIANZA: CONFIRMADO el cableado; efecto SIN MEDIR. GRAVEDAD: 2.

### E-08. Tres flags en `True` que no hacen nada, y un docstring que contradice al código
- `ENABLE_DUAL_ROI_BT=True` (pisado por `ENABLE_BT_PATH_HOT=False`, `process_viirs.py:998`);
  `ENABLE_VRP_TIR_CONSISTENCY_GATE=True` (salida apagada); `P95_VENT_EXCLUSION_*` (sólo alimenta el
  BT path). `scan_geometry.py:175-177` dice que «el ROI exterior sigue siendo el círculo» y
  `process_viirs.py:780` usa la caja. Ruido para quien lea el perfil buscando qué está encendido.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

---

## 4. Propuesta: la configuración «literal mínima»

### 4.a Qué sería (con los flags que existen hoy)

| sobre `mirova_equivalent` | flag | estado de la evidencia |
|---|---|---|
| apagar el Test 1 integrado (arrastra X13, X18 a X23) | `enable_test1_path: false` | medido S147, S148, S149 |
| conectiva de la prosa | `enable_tests_23_prose_branch: true` | medido sept. y mayo: 29,8 → 2,7 % y 30,1 → 2,3 % en V375 |
| banda 22 primaria en MODIS | `enable_modis_b22_primary: true` | **obligatoria junto con `max`**: con banda 21 y `max` MODIS se apaga (3 de 733 pasadas con primer pase en mayo); con banda 21 y `min` dispara en 730 de 733. Brazos J y K en cola, sin evaluar |
| caja de 5 × 5 km | `enable_roi1_box_paper: true` | nunca medida de verdad (A118); cableado completo desde #738 |
| segundo pase condicionado | `enable_second_pass_conditioned: true` | **no separable de la compuerta** (S138): ver orden |
| sin compuerta de 3 K | `enable_tests_23_no_bt_gate_viirs375: true` | sólo I-band; falta el flag en MODIS y M-band (E-05) |
| fondo por vecinos | `enable_vrp_bg_neighbor_mean_viirs375/750: true` | S143: empuja la sobre-publicación EN CONTRA (+0,05) bajo `min` y con T1; sin medir bajo `max` |
| suma en vez de máximo | `enable_single_pixel_sub_mw_mode: false` | sin medir sin T1 |

Lo que **ningún flag** da hoy: K1 como activo (E-05), remuestreo con bow tie (D17, D28), borde real de
la caja (E-03), suma de todos los alertados sin cerca de distancia (D32, D13), banda 32 (D20).

### 4.b Perfiles que se le parecen y qué pasó

| perfil | diferencia efectiva con producción (`diff_perfiles.txt`) | resultado |
|---|---|---|
| `_mirova_literal` (S27) | 29 diferencias; NO es literal (E-06) | «NO APROBADO», recall -27,6 puntos: mide otra cosa (E-01) |
| `_s142_ab_literal` (S143) | sin compuerta, fondo por vecinos, segundo pase condicionado, `keep_peak` off; **con T1 encendido y `min`**; sólo V375 | NO ADOPTAR: sobre-publicación 0,917 → 0,547 y magnitud 0,77 → 0,94, pierde 5 noches. El verificador: todo el descenso venía de apagar `keep_peak`; D22 y D25 empujaban en contra (`docs/audit_s143/BITACORA_S143.md:105-114`). Se corrió bajo la saturación del T1 (A114) |
| `_s146_ab_sin_test1` (B) | sólo `ENABLE_TEST1_PATH=False` | V375 86,1 → 28,7 %; NO ADOPTAR por C2, C4 y C7 (C7 después bajado a informativo, según `docs/PLAN_AUDITORIA_S149.md:16`) |
| `_s147_ab_sin_test1_max` (F) | B + `max` | sept. 29,8 → 2,7 %, mayo 30,1 → 2,3 %, recall 135 de 143 y 276 de 296; costo bajo 0,10 MW. **Es lo más cercano a la literal mínima que existe** |
| `_s147_ab_sin_test1_caja_max` (H) | F + caja | corrido antes de #738: no midió la caja |
| `_s149_ab_sin_test1_b22_max` (K) | F + banda 22 | en cola, Láscar marzo a junio |

Nadie ha corrido todavía F + segundo pase condicionado, ni F + suma, ni F + fondo por vecinos.

### 4.c Orden para llegar sin mover dos cosas a la vez

Control de cada paso = el brazo aprobado del paso anterior (A114: el control debe ser el régimen donde
la palanca PUEDE actuar, no producción). Cada paso con su pre-registro, su nulo y paridad en los dos
sentidos, por tramo de magnitud.

0. **Sin cómputo**: propagar E-01 (marcar `MISSION.md:173`, `:225-232` y las dos memorias de S27),
   renombrar o archivar `_mirova_literal` (E-06), cablear o retirar `ENABLE_TEST1_NULL_CORRECTED`
   (E-04). Decisión del orquestador; yo no toqué nada.
1. **Sin T1** (B). Ya medido. Es el piso de todo lo demás.
2. **+ `max`** (F). Medido en dos ventanas; faltan determinismo y el resto de la cola.
3. **+ banda 22 en MODIS** (K contra J). En cola. Sin esto MODIS no tiene detector bajo `max`.
4. **+ caja 5 × 5** (H contra F, repetido post #738).
5. **+ segundo pase condicionado Y sin compuerta, juntos**: es la única excepción honesta a «una cosa
   a la vez», porque S138 midió que se compensan (condicionar solo reactiva la compuerta con toda su
   fuerza; quitar la compuerta sola no cambia lo publicado). Requiere antes el flag de la compuerta en
   MODIS y M-band (E-05). Se puede partir en 5a (ambos, sólo V375) con los flags de hoy.
6. **Magnitud, con la detección ya congelada**: suma en vez de máximo (X15), después fondo por
   vecinos (D25), después decidir si F5 y la magnitud focal siguen teniendo problema que resolver.
   Medir contra la magnitud pareada de MIROVA, por volcán (A99 rebajada).
7. **Poda**: tope de 5 MW, filtros de cirrus y campo difuso del tablero, `max_cluster_pixels`: medir si
   les queda sustrato bajo el paso 5 (en mayo, brazo F, el tope actuó 0 veces). Si no, se retiran.
8. **Lo que pide código nuevo**: K1 activo (D23), borde de la caja (E-03), remuestreo (D17).

Lo que el experimental hereda: todo lo que la réplica apague (conectiva `min`, T1 con el estadístico
corregido) es justo su materia prima. Es del frente F; sólo lo anoto.

---

## 5. Para otros frentes

- **Frente D**: `docs/audit_s143/BITACORA_S143.md:105-114` (NO ADOPTAR del brazo literal, corrido con el
  T1 encendido: candidato a A114). `project_s27_mirova_literal_negativo.md:104` («no reabrir»).
- **Frente A**: `MEMORY.md` índice, línea «S27 Test1 cierra D4 (recall 50→80 %)» sin marca; D30 dice
  que ese número quedó SIN EVIDENCIA en S147.
- **Frente C**: MODIS brazo B, mayo: primer pase con píxeles en 730 de 733 pasadas y sólo 62 cúmulos
  `summit` con magnitud (`piezas_vivas_sin_test1_salida.txt`). Contexto de las «0 de 11» de Láscar.
- **Frente G**: `frontend/index.html:1476` respaldo `triggered_test1`; l. 1086 `USE_F5_CORE` por
  defecto; los filtros de artefacto l. 1207-1238 exceptúan `_mirova_confirmed`.
- **Frente F**: `diff_perfiles.txt`: `experimental` difiere de producción sólo en `DATA_SUBDIR` y `PROFILE_NAME`.

---

## 6. VERIFICADO LIMPIO

1. **Tabla 1 nocturna exacta y sin overrides**: `0.003 / 0.01 / 5 / 10 / -0.8`; `C1_SUMMIT_OVERRIDE`,
   `C2_SUMMIT_OVERRIDE`, `VIIRS_C2_OVERRIDE_NIGHT` en `None`. `VRP_PROFILE=mirova_equivalent PYTHONPATH=. python experiments/_s149_audit/frente_e/resolver_perfil.py`. Coincide con la Tabla 1 leída en imagen (`sp426_idx6.png`).
2. **La fórmula de los Tests 2 y 3 dice «or» en su propia línea y «and» entre tests**; la Ec. 6 dice
   media de los píxeles que rodean; la Ec. 8 es una suma; el ROI1 es una caja de 5 × 5 km; L_TIR es
   L32; el Test 1 es por píxel. Todo leído en imagen renderizada, no en la capa de texto.
   (Curiosidad: la Ec. 5 impresa repite «NTI_bk =» donde debería decir ETI; errata del paper, p. 5.)
3. **El primer pase reemplaza, no suma**: `hot_mask_2d = fp_hot` en los tres procesadores
   (`process_viirs.py:1303`, `process_modis.py:897`, `process_viirs_mod.py:882`). Ningún camino
   heredado (BT, K1, dNTI solo, NTI relativo, ETI S37) entra a la máscara de detección en producción.
4. **Apagar el T1 lo apaga de verdad**: 0 records con `triggered_test1` o `final_hotspot_source=test1`
   en 3.682 pasadas por brazo (mayo, B y F). Control positivo del instrumento: los records con píxeles
   de primer pase bajan de B a F (V375 662 → 499, V750 148 → 70, MODIS 730 → 3).
5. **El segundo pase queda acotado a la caja**: el ETI es NaN fuera de `roi_mask`
   (`detection_context.py:753, 793`) y `newly_active` exige dETI finito (`:958-959`).
6. **ROI2 es la caja de 50 × 50 km** en los 11 Tier A (`radius_km=25`, `roi_mask_bbox`,
   `process_viirs.py:780`), no el círculo.
7. **Sin máscara de nube**: `CLOUD_MASK_BT_K=0.0`; `process_viirs.py:824-832` queda todo en `True`.
8. **dNTI y dETI con media aritmética de 8 vecinos** (`detection_context.py:483-486`, centro excluido).
9. **Pisos de VRP en 0,0** en producción (y 0,02 / 0,15 / 0,27 sólo en el fósil `_mirova_literal`).
10. **Los flags de los brazos llegan al módulo**: `_s149_ab_sin_test1_b22_max` declara
    `enable_modis_b22_primary` en la raíz del YAML y resuelve `ENABLE_MODIS_B22_PRIMARY=True`
    (`diff_perfiles.txt`); los brazos B, F, H y `_s142_ab_literal` resuelven exactamente lo que su
    descripción dice, sin diferencias de más.
11. **El ancla honesta sin T1 es sólo el centroide del cúmulo contextual** (`anchor.py:82-84`).

**Lo que NO verifiqué**: `process_viirs_mod.py` línea a línea; `store.py` (sólo por `grep` y por las
marcas `discarded_reason`); Campus 2022, Campus 2024, el capítulo y Coppola 2026 (no abiertos); qué
publica `ENABLE_SUM_VRP_REPORTING`; el efecto numérico de E-02, E-03 y E-07; el YAML de
`_mirova_literal` tal como estaba el 2026-04-29; ninguna ventana que no sea mayo de 2026; y no corrí
pytest ni reprocesé ningún gránulo.
