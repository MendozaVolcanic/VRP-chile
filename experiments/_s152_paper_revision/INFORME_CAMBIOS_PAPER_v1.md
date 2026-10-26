# Informe de cambios propuestos al borrador del paper (S152, 2026-10-16)

Informe de sólo lectura. No se editó nada del repo. El borrador revisado está en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\` (última edición 2026-09-15,
`numbers.json` generado el 2026-09-07 en `83b9df8ff`). Se cotejó contra lo que el proyecto cambió desde el
2026-09-15 (rama `loop/activo` en `d835efd09` y luego `f3520f4d5`, que el loop commiteó mientras trabajaba;
`pipeline/` sin diferencias de lógica de producción: todos los flags nuevos entraron apagados).

Material producido por este informe (fuera del repo):

- `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\repro_0831\` : `scripts/paper_numbers.py --hasta 2026-08-31` (misma ventana de ground truth que el paper).
- `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\repro_0907\` : `--hasta 2026-09-07 --tests` (misma ventana de records que el paper).
- `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\hoy\` : sin `--hasta` (hasta 2026-10-16). **Sólo indicativo: no pegar en el paper** (cruza #535 y los hitos A119).
- `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\scripts\estimar_noches.py` y `estimar_noches_salida.txt` : conteo ad hoc de noches diurnas, mínimas y sólo OCR en la ventana del paper. **No es la función oficial de D-9** (`scripts/clase_mirova.py::aplicar_regla_minimas`); sus números son estimación.

Los números de línea de archivos del repo valen para `f3520f4d5`; `tasks\LOOP_OBJETIVOS.md` crece por arriba de su
§6 en cada vuelta del loop, así que sus líneas de bitácora se corren (buscar por número de vuelta).

Clases: **FALSA**, **REBAJADA** (cierto en parte), **DESACTUALIZADA** (número viejo), **FALTA** (resultado nuevo que debería
estar), **SIN CAMBIO** (revisado). Las citas a papers que el informe señala como centrales requieren verificación
renderizando la página (A95); no las verifiqué contra `.txt`.

---

## 1. Resumen en una pantalla

**Conteos** (una fila de la §2 por afirmación; los ítems de `numbers.json`, `TABLAS.md` y `README.md` van aparte, §3):

| sección | FALSA | REBAJADA | DESACTUALIZADA | FALTA | SIN CAMBIO | SIN LOCALIZAR | total |
|---|---|---|---|---|---|---|---|
| §4 Background (`sec4_background.md`) | 0 | 3 | 1 | 1 | 4 | 0 | 9 |
| §5 Methods (`sec5_methods.md`) | 6 | 9 | 2 | 8 | 2 | 0 | 27 |
| §6 Validation (`sec6_validation.md`) | 7 | 4 | 1 | 3 | 2 | 1 | 18 |
| `numbers.json` / `TABLAS.md` / `README.md` (§3) | 1 | 2 | 6 | 1 | 5 | 0 | 15 |
| **total** | **14** | **18** | **10** | **13** | **13** | **1** | **69** |

**Los 5 cambios más graves** (los que tumbarían el paper ante un revisor):

1. **«La referencia no tiene negativos» y por eso «no se puede reportar precisión» es FALSO.**
   `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\sec6_validation.md:26-29`, `:138-139` y `:153-159`.
   El consolidado de MIROVA trae filas RUTINA: pasadas en que MIROVA miró y no vio nada. El proyecto las usa como
   «negativos limpios» (`docs/audit_s139/MAPA_BASES_MIROVA_V1.md:312`; `docs/MISSION.md:75-77`, criterio de victoria
   punto 3; CLAUDE.md A98). Y con esa vara la réplica en producción publica en el **86,1 %** de los negativos limpios de
   VIIRS 375, 21,4 % en VIIRS 750 y 5,1 % en MODIS sin PCC (control del A/B S147, ventana 2026-09-01 a 2026-09-20,
   `docs/S147_RESULTADO_AB_SIN_TEST1.md:30-38`; ventana en `experiments/_s146_ab_sin_test1/PREREGISTRO.md:243`). El paper
   omite el defecto principal conocido de la réplica (la brecha es de sobre-publicación, no de recall, A98) y además
   la argumenta como imposible de medir. §6.5 entero hay que reescribirlo.
2. **Las alertas diurnas «excluidas» no se excluyen, y perderlas no es «lo correcto».**
   `sec6_validation.md:29-34`. `scripts/paper_numbers.py:188-205` y `pipeline/mirova_csv_loader.py:146-206` no filtran
   por hora: en la ventana del paper hay **19 noches de alerta V375, 5 V750 y 6 MODIS que sólo tienen filas diurnas**
   (12 UTC o más) y están en el denominador del recall (estimación propia, `scripts\estimar_noches_salida.txt`; las 98
   filas diurnas V375 que cita el paper coinciden con mi conteo). Y MIROVA sí procesa VIIRS de día (Campus et al. 2022,
   p. 16 a 17, según `experiments/_s151_alertas_diurnas/README.md:108-128`, página renderizada): bajo la lectura A hay
   **40 pasadas diurnas protegidas contra 232 nocturnas** (`experiments/_s151_alertas_diurnas/README.md:133-153`). La
   definición en `numbers.json` («nocturna 03-09 UTC según el loader») también es falsa.
3. **«Cada producto viaja con su geolocalización» es FALSO para MODIS.**
   `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\sec5_methods.md:6-14`. El pipeline baja
   MOD03/MYD03 y no los lee (`pipeline/process_modis.py:470`, «geo_path is accepted ... but not used»); interpola la
   grilla de 5 km del L1B con `_interp_geo` (`pipeline/process_modis.py:342`), que ignora el offset 2 de esa grilla. Con
   MxD03 como árbitro: 2,58, 2,21 y 1,15 km hacia el sensor en el lado del frame 0 con cenit de 30° o más
   (`experiments/_s151_probe_mod03/README.md:6-20`, PARCIAL verificado), más un término a lo largo de la traza de
   2 − 0,00197·línea km (r = 0,955, `experiments/_s151_mxd03_etiquetas_verif/resultado/VERIFICADOR_RESULTADO.md:108-120`).
   Arrastra a toda posición MODIS del paper (§5.5, §6.2, §6.3).
4. **La lectura de MODIS en §6.3 («no es falla de detección», «sin respuesta por registro a 1 km») es FALSA.**
   `sec6_validation.md:90-99` y `:75-76`. El «cráter válido» aparece en el **89,1 % de 4.800 negativos limpios MODIS
   contra 93,7 % de 158 positivos** (CLAUDE.md A82, l. 1009, AUDIT_S146 V-02): la recall «cráter» de 0,976 no mide
   detección. Y con banda 22 MODIS sí separa en Láscar: **68 de 73 alertas contra 11 de 96 negativos limpios**
   (`docs/S150_RESULTADO_MESES.md:49-58`; marca S150 de D21 en `docs/MIROVA_DIVERGENCES.md:2600-2611`). A82 y A83 están
   rebajadas en el repo y el paper las cita como cierre.
5. **Methods describe una magnitud que no es la que se publica, y dos cierres de divergencia están mal.**
   `sec5_methods.md:102-111` y `:184-202`. Faltan: el fondo es la mediana de un anillo de 5 a 25 km con recorte a cero
   (D25), el modo de un píxel (≤ 3 píxeles y < 5 MW publica el píxel más caliente; 75,5 % de los records con cúmulo,
   `docs/FICHA_SDA_VRP_CHILE.md:25`), el tope de 5 MW con fondo bajo 270 K (1.565 cúmulos topados, 343 sobre 5 MW,
   CLAUDE.md A23 l. 354-360) y el núcleo F5' en V375 (D32, A10). Y §5.7 dice que el A/B de la caja (D18) «no mejoró la
   paridad», cuando ese A/B nunca la midió (marca S148 de D18) y la primera medición real dio **NO CUMPLE (veto)**
   (`docs/MIROVA_DIVERGENCES.md:2303-2310`). §5.3 llama «literal» a una conectiva que el mismo paper permite leer de dos
   maneras (`pipeline/detection_context.py:512-525`).

**Lo que conviene decidir antes de reescribir** (para Nicolás): (a) si la validación se rehace en la ventana limpia
2026-08-29 en adelante (post #535 y con los hitos A119 cumplidos) o se informa por tramo A119; (b) si `paper_numbers.py`
pasa a usar la referencia de la unión histórica (`scripts/referencia_mirova_unificada.py`), la regla SN de D-9 y el
etiquetador de negativos limpios de `scripts/banco_paridad.py`; (c) si §6 adopta las tres métricas del criterio de
victoria (`docs/MISSION.md:47-90`).

---

## 2. Tabla por sección

Rutas del repo: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\` es la raíz de todas las rutas de
esta tabla que empiezan con `docs\`, `pipeline\`, `scripts\`, `experiments\`, `tasks\` o `CLAUDE.md`. Las del paper se dan
completas en cada encabezado de sección. El texto sugerido va en inglés porque el manuscrito está en inglés.

### 2.1 §4 Background: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\sec4_background.md`

| id | línea | afirmación | evidencia nueva | clase | cambio propuesto |
|---|---|---|---|---|---|
| 4-1 | 62-64 | Tests 2 y 3: «dNTI > C1 or dNTI > μ + C2·σ», como única lectura | `pipeline\detection_context.py:512-525`: la fórmula da umbral `min(C1, μ+C2σ)` y la prosa de la misma página describe C1 como cota inferior (`max`); con la fórmula el piso gobierna el 100 % de MODIS y el 99,9 % de VIIRS. Con `max`, V375 en negativos limpios baja de 35,7 % a 2,7 % (abril a agosto, `docs\S150_RESULTADO_MESES.md:45-48`); Coppola 2014 escribe AND (`docs\S150_RESULTADO_MESES.md:20-23`). Decisión D-1 pendiente | REBAJADA | Agregar: «The same page also describes C1 as a minimum threshold, with the scene statistics governing in variable scenes; the two readings (effective threshold min or max of C1 and μ + C2σ) are not equivalent, and Coppola et al. (2014) state the conjunction explicitly.» Verificar p. 187 y Coppola 2014 en imagen (A95) |
| 4-2 | 91-92 | «the product's detectable floor is of the order of 1 MW» | En VIIRS 375 el banner de MIROVA dice NONE hasta 0,04 a 0,05 MW y VERY LOW de 0,05 a 0,91 MW (`docs\S151_CRITERIO_CLASE_MIROVA.md`, §2, tabla del banner); §4.4 ya cita 0,02 a 1,11 MW de Campus 2024 | REBAJADA | «...of the order of 1 MW for MODIS; at 375 m the near-real-time product reports anomalies down to a few hundredths of a MW.» |
| 4-3 | 122-125 | Escala de intensidad Low < 1 MW, Moderate 1-10 ... (Fig. 11) | El pie de la Fig. 11 contradice a la figura (bandas en 10^7 a 10^10 W; banner «VERY HIGH» con 6.797 MW). El sitio de hoy agrega NONE y VERY LOW y corta LOW en 1 MW (`docs\S151_CRITERIO_CLASE_MIROVA.md` §2, página renderizada) | REBAJADA | Citar el pie como tal, notar la contradicción con la figura y describir el banner actual (NONE, VERY LOW < 1 MW, LOW ≥ 1 MW), con fecha de observación |
| 4-4 | 129-138 | Caveats publicados (nubes, falsas alertas diurnas) | MIROVA procesa VIIRS de día con umbrales más altos (Campus 2022 p. 16 a 17, Tabla 4; `experiments\_s151_alertas_diurnas\README.md:108-128`) | FALTA | Una frase: «MIROVA processes daytime VIIRS overpasses with the higher daytime thresholds of Table 1 (Campus et al., 2022).» Así §5.1 puede declarar la restricción nocturna como divergencia propia |
| 4-5 | 24-32 | Fondo = media de los píxeles que rodean; alerta multipíxel = suma | Reforzado: siete textos del grupo, páginas renderizadas (D25 S141, `docs\MIROVA_DIVERGENCES.md:2683-2690`); la suma es el paso (iv) de la cadena NRT (Campus 2022 §3.2, D32 `docs\MIROVA_DIVERGENCES.md:3051-3075`) | SIN CAMBIO | Opcional: anclar también a Campus 2022 p. 7 §3.2 como fuente NRT |
| 4-6 | 98-116 | Grillas y bandas por sensor | Coherente con D17 S141 (MODIS 51×51 de 1 km, M 67×67 de 750 m, I 134×134 de 375 m) | SIN CAMBIO | Ninguno (la agregación a bordo de VIIRS va en §5, ítem 5-13) |
| 4-7 | 88-90 | Umbrales «self-adapting ... independent of local climate and topography» | Es afirmación del paper y está bien atribuida. Pero bajo la lectura de fórmula el piso C1 gobierna casi siempre (`pipeline\detection_context.py:520-522`) | SIN CAMBIO | Dejar en §4; retomar en §8 |
| 4-8 | 142-145 | No hay implementación de referencia publicada | Sin evidencia nueva (sigue SIN LOCALIZAR, nota 6 del editor) | SIN CAMBIO | Ninguno |
| 4-9 | 283-287 (nota 8 del editor) | «Muy Bajo» no aparece en ninguna fuente | El OCR v30 lee el banner `Nivel_Anomalia_MIROVA` desde agosto de 2026: VERY LOW existe en el producto (`docs\S151_CRITERIO_CLASE_MIROVA.md` §2) | DESACTUALIZADA | Reemplazar la nota: la etiqueta sale del banner del sitio, observada desde agosto de 2026 |

### 2.2 §5 Methods: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\sec5_methods.md`

| id | línea | afirmación | evidencia nueva | clase | cambio propuesto |
|---|---|---|---|---|---|
| 5-1 | 6-14 | MODIS se lee «with their MOD03/MYD03 geolocation files»; «every product is paired with its own geolocation granule» | `pipeline\process_modis.py:30-32` (lat/lon gruesas interpoladas), `:342` (`_interp_geo`), `:470` (geo_path no usado). Corrimiento medido contra MxD03: `experiments\_s151_probe_mod03\README.md:6-20`; término a lo largo de la traza: `experiments\_s151_mxd03_etiquetas_verif\resultado\VERIFICADOR_RESULTADO.md:108-120`; arreglo en estudio (tarea 1.21, `tasks\LOOP_OBJETIVOS.md:314-319`) | FALSA | «For MODIS, pixel positions are interpolated from the 5 km tie points of the L1B granule; the MOD03/MYD03 files are retrieved but not used. This interpolation misplaces pixels by 1 to 3 km toward the sensor at zenith angles above 30°, plus up to 2 km along track (Section 5.7).» Y agregar la divergencia a §5.7 |
| 5-2 | 8-9 | Banda 21 primaria, banda 22 donde la 21 satura | Correcto respecto del código, pero el paper usa la 22 y la 21 sólo donde la 22 satura (D21, `docs\MIROVA_DIVERGENCES.md:2596-2611`); con banda 22, Láscar MODIS separa (68/73 contra 11/96) | FALTA | Declarar D21 en §5.7 con el resultado de Láscar y su salvedad (un solo volcán medido) |
| 5-3 | 30-33 | Sólo noche porque «the MIR channel is unusable by day» | MIROVA procesa VIIRS de día (ítem 4-4); D27 pasó de «deliberada» a «pendiente de A/B» y la rama diurna está cableada y apagada (`docs\MIROVA_DIVERGENCES.md:2752-2764`; `docs\FICHA_SDA_VRP_CHILE.md:34`, v1.8) | FALSA | «Detection is restricted to night overpasses. This is a choice of ours, not of MIROVA, which also processes daytime VIIRS data with higher thresholds; sunlight reflected by clouds raises the MIR radiance (Coppola et al., 2014). It is listed as divergence D27.» |
| 5-4 | 39-43 | Cron de 2 h que acota la antigüedad de la serie a 2 h | El cron de GitHub corría 4,25 a 5 veces al día, no 12 (`docs\AUDIT_S150.md:125-127`); desde el 2026-10-16 un cron externo despacha el NRT (`tasks\LOOP_OBJETIVOS.md:368-376`). Además un timeout de LANCE dejó a un job verde sin pasadas (`docs\AUDIT_S150.md:123-124`) | FALSA | Describir la cadencia real (cron de GitHub más despacho externo cada hora de 01 a 12 UTC) y no prometer un límite de 2 h |
| 5-5 | 55-58 | `experimental` «never run by the cron» | `.github\workflows\experimental-diario.yml:21` (`0 14 * * *`), congelado en la detección del 2026-10-09 (#771); su papel cambió (`tasks\LOOP_OBJETIVOS.md:9-11`; `docs\MISSION.md:20-28`) | FALSA | «A separate `experimental` profile, frozen at the operational detection of 2026-10-09, runs daily in its own workflow and writes to its own subdirectory; it is where detections MIROVA does not publish are kept.» |
| 5-6 | 70-71 | C2 = 5/10 «15 by day», C1 = 0,003/0,01 «0,02 by day» | De día no corre nada (D27); los valores diurnos están cableados y apagados (`ENABLE_DAYTIME_VIIRS = False`) | REBAJADA | Quitar los valores diurnos de la frase operativa o decir «coded but not run» |
| 5-7 | 78-80 | «implements Tests 2 and 3 literally» | Ver 4-1. Producción usa `min` (`ENABLE_TESTS_23_PROSE_BRANCH = False`, leído de `pipeline.profile`); la otra lectura reproduce mucho mejor a MIROVA en V375 (`docs\S150_RESULTADO_MESES.md:25-48`) | REBAJADA | «...implements the formula as printed (effective threshold min(C1, μ + C2σ)); the paper's prose supports the stricter reading, which is evaluated in Section 8 (divergence pending decision).» |
| 5-8 | 84-87 | Los no aptos (borde, dNTI < -0,1, activos) se excluyen del pool de μ y σ | Cierto en el primer pase; el segundo pase calcula μ y σ sin esos filtros, y su «efecto nulo» cayó en S145 (D26, `docs\MIROVA_DIVERGENCES.md:2732`) | REBAJADA | Agregar: «...in the first pass; the second pass computes μ and σ without those exclusions (D26).» |
| 5-9 | 94-96 | El Test 1 integrado «catches sub-pixel sources» | Es un detector propio (D30, `docs\MIROVA_DIVERGENCES.md:2827`) y el camino que más publica: apagarlo baja la publicación en negativos limpios de 86,1 a 28,7 % (V375), 21,4 a 5,9 % (V750), 5,1 a 2,5 % (MODIS sin PCC), 2026-09-01 a 09-20 (`docs\S147_RESULTADO_AB_SIN_TEST1.md:30-38`); satura cualquier estratificación (CLAUDE.md A114, l. 1416). El Test 1 por píxel del paper no es camino de detección (D23, `docs\MIROVA_DIVERGENCES.md:2663`) | FALTA | Declarar las dos cosas y su peso medido; remitir a §6 |
| 5-10 | 102-111 | Coeficientes k reconstruidos del OSF v2.5 | Reforzado: el OSF cumple VRP = k·A·(ΣL_hot − ΣL_bk) con error relativo máximo 8,9e-8 (`experiments\_s151_presupuesto_magnitud\README.md:24-26`); `tabla3` se reproduce idéntica | SIN CAMBIO | Ver ítem T-3 (rótulo Di Bella en la Tabla 3) |
| 5-11 | 102-103 | VRP = k·A_pix·(L_MIR − L_bg), sin decir qué es L_bg | L_bg es la mediana de un anillo de 5 a 25 km (kernel local sólo en 5 volcanes) y el exceso se recorta a 0 (D25, `docs\MIROVA_DIVERGENCES.md:2683-2700`; `docs\FICHA_SDA_VRP_CHILE.md:25`) | FALTA | «L_bg is the median of a 5 to 25 km annulus (a local 3 × 3 kernel for five volcanoes), and negative excesses are set to zero; MIROVA uses the mean of the non-alerted neighbours (D25).» |
| 5-12 | 100-128 | La magnitud publicada | Falta lo que realmente se publica: modo de un píxel (≤ 3 píxeles y < 5 MW: el píxel más caliente; 75,5 % de los records con cúmulo al 2026-10-14, `docs\FICHA_SDA_VRP_CHILE.md:25`); tope de 5,0 MW con fondo bajo 270 K (1.565 cúmulos topados, 277 summit, 343 sobre 5 MW, corpus al 2026-10-14, CLAUDE.md A23 l. 354-360); núcleo F5' en V375 en vez de la suma (D32; A10 l. 228-237: sobre 1.512 pares, suma 0,783, núcleo 0,706, `pc.vrp_mw` 0,600) | FALTA | Un párrafo nuevo «What is published», con las tres reglas, sus números con fecha y la remisión a §5.7 |
| 5-13 | 115-121 | Área nadir fija: «fidelity requirement, not a simplification»; MIROVA a «1 km²» | A66/A67 rebajadas S138 («clon literal» demasiado fuerte; D17 abierta, CLAUDE.md l. 793-808); el grupo escribe que el remuestreo corrige el cenit sólo «partially» (D17 S141, `docs\MIROVA_DIVERGENCES.md:2207-2217`); nuestra razón cae de 0,76 en nadir a 0,45 en el borde y el Npix de MIROVA no crece (`experiments\_s151_presupuesto_magnitud\README.md:76-80`, SIN ATRIBUIR); agregación a bordo VIIRS 3:1, 2:1, 1:1 con límites a 36,32° y 52,66° de cenit y escalón robusto de MIROVA sólo a 52,66° (`experiments\_s151_angular_119\INFORME.md:1-40`; verificador en `tasks\LOOP_OBJETIVOS.md:506-516`). Grillas por sensor 1 km, 750 m y 375 m | REBAJADA | «MIROVA resamples onto fixed grids (1 km MODIS, 750 m and 375 m VIIRS); we keep native pixels with the nadir area. This restores the calibration of k but does not reproduce the resampling: our ratio to MIROVA still falls with zenith angle (Section 6.4), an effect not yet attributed.» |
| 5-14 | 125-128 | Un estimador TIR «applies» Stefan-Boltzmann | `ENABLE_VRP_TIR_OUTPUT = False` y `ENABLE_VRPTIR_AVENI = False` (leídos de `pipeline.profile`): el estimador no se publica. Defecto anterior al 15-sep | REBAJADA | «A TIR estimator ... is implemented but not part of the published output.» (SIN VERIFICAR si se calcula en memoria) |
| 5-15 | 144-149 | «detect wide, classify visually», conserva lo real que MIROVA no publica | Objetivo cambiado (decisiones de Nicolás 2026-09-21 y 2026-10-13): la réplica calla donde MIROVA calla y lo demás va al `experimental` (`docs\MISSION.md:20-28`). En MODIS `distance_class` sale del hotspot final, no del cúmulo (`ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`), y depende de si el Test 1 de 3 km dispara y de si un píxel del Salar cae dentro de 25 km (`experiments\_s151_mxd03_etiquetas_verif\resultado\VERIFICADOR_RESULTADO.md:28-55`). MIROVA no elige el cráter por serlo: con foco lejano fuerte informa lejos (15 de 15 con z ≥ 30, `experiments\_s151_seleccion_mirova\README.md:12-19`) | REBAJADA | Reescribir el párrafo con el objetivo vigente, la regla de etiqueta por sensor y la diferencia con la selección de MIROVA (A/B `vrp_max` pendiente, tarea 1.4) |
| 5-16 | 137-140 | Radios internos de los KML de MIROVA | MIROVA mide `Distancia_km` desde el centro de su grilla, no desde el cráter (Tupungatito 34/40, PCC 38/50, Planchón Peteroa 17/17; `docs\MIROVA_DIVERGENCES.md:2312-2318`); nuestro radio se mide desde el ancla en el cráter | FALTA | Una frase con la diferencia de origen y los tres volcanes donde pesa |
| 5-17 | 159 | `[NUM: n_tests_collected]` | `numbers.json` dice 1.225; hoy 1.852 recolectados (`repro_0907\numbers.json`, `pytest --collect-only`, HEAD `f3520f4d5`) | DESACTUALIZADA | Regenerar con el script; no transcribir |
| 5-18 | 157-160 | Mecanismos de reproducibilidad | Desde #785 (2026-10-15) cada record lleva marca de régimen (perfil y sha del código) y desde #769 `first_processed_utc`; los records anteriores no la tienen (tarea 0.6, `tasks\LOOP_OBJETIVOS.md:140-143`) | FALTA | Mencionarlo como cuarto mecanismo y declarar que la ventana validada es anterior a la marca |
| 5-19 | 161-166 | La compuerta de 3 preguntas de MISSION | Hoy además rige el criterio de victoria: ninguna alerta protegida (≥ 1 MW, lectura A) se pierde; bajo 1 MW perder y publicar de más pesan igual; dos direcciones, por sensor y tramo A119 (`docs\MISSION.md:47-90`) | FALTA | Una frase con el criterio, porque es la vara con que se aceptan cambios |
| 5-20 | 172-176 | Ficha SDA v1.5, 16 módulos con cabecera | Ficha v1.8, 2026-10-15 (`docs\FICHA_SDA_VRP_CHILE.md:7`), con correcciones v1.7 de la lógica descrita (l. 25). Conteo de cabeceras: 15 archivos con la línea `Ficha: docs/FICHA_SDA_VRP_CHILE.md`, 18 que mencionan FICHA (grep, SIN VERIFICAR cuál es el criterio) | DESACTUALIZADA | Citar v1.8 y sacar el conteo de un script, no a mano |
| 5-21 | 185-186 | D2 y D3: cobertura incompleta | La calidad de la referencia se describe hoy por tramos (A119, CLAUDE.md l. 1499; `scripts\calidad_referencia_mirova.py:18-56`) | REBAJADA | Remitir a §6.1 reescrita con los tramos A119 |
| 5-22 | 186-188 | D13: la cerca summit suprime «part of the detected magnitude» | En magnitud la cerca apaga el 70,7 % (S145; marca S146 en el título de D13, `docs\MIROVA_DIVERGENCES.md:1721`). El texto evitó el número a propósito | SIN CAMBIO | Opcional: dar el 70,7 % con su fecha y definición |
| 5-23 | 188-189 | D17: «Our per-image grid is not centred on the point MIROVA uses» | Producción no remuestrea (`ENABLE_UTM_REGRID = False`): D17 trata de la grilla F70 apagada; la frase contradice §5.4 («does not resample») | FALSA | «We do not resample onto MIROVA's grid; an implemented regridding (disabled) was centred on the wrong point (D17).» |
| 5-24 | 189-191 | D18: «an A/B reprocessing of the box variant did not improve parity» | El A/B de S130 midió un defecto de cableado, no la caja (marca S148); la primera medición real (D1, 2026-10-15) dio **NO CUMPLE (veto)** por una alerta protegida MODIS de Láscar en la corona, cierre válido sólo con la geolocalización MODIS de hoy (`docs\MIROVA_DIVERGENCES.md:2303-2318`) | FALSA | «A first valid test of the 5 km box failed the acceptance criterion by one protected MODIS alert whose pixel position is itself affected by the MODIS geolocation error; the divergence remains open (D18).» |
| 5-25 | 191-194 | D19 activa: píxel del borde del disco más frío que su fondo | Sigue abierta; S144 midió que ese sitio destaca en la radiancia de MIROVA pero el 86 % del efecto es permanente: sitio tibio estable, no anomalía de la noche; no autoriza apagar `keep_peak` (`docs\MIROVA_DIVERGENCES.md:2440-2449`; A100) | REBAJADA | Agregar la medición S144 en una frase |
| 5-26 | 198-202 | D20: desfase de NTI 0,0001 a 0,0054, «declared rather than corrected» | «Despreciable» rebajado S146 a «chico y no medido» (título de D20, `docs\MIROVA_DIVERGENCES.md:2541`): la estimación es de Planck, no una medición | REBAJADA | «...a Planck-function estimate (not yet measured on our data) puts...» |
| 5-27 | 184-202 | Lista de divergencias de §5.7 | Faltan D21 (5-2), D22 sólo en §5.3, D23, D24 (saturados MODIS eliminados, el paper los conserva, `docs\MIROVA_DIVERGENCES.md:2673`), D25 (5-11), D26 (5-8), D27 (5-3), D30 (5-9), D32 (5-12), el tope D9 (5-12), el corrimiento MODIS (5-1) y el GAP #A (ya pedido en la nota del editor). Saturación: en la erupción de Chillán, 0 píxeles saturados en 385 gránulos (2026-09-28 a 10-16) y en 58 pasadas (10-14 a 10-16), máximo I04 válido 355,96 K sin bit (`tasks\LOOP_OBJETIVOS.md:432-440`, `:518-526`; verificado en `:492-504`); techos latentes M15 343 K (`pipeline\process_viirs_mod.py:182`) y LUT de I04 de NOAA-21 361,00 K bajo el corte 361,27 K (`experiments\_s151_techos_120\INFORME.md`) | FALTA | Tabla de divergencias abiertas en §5.7 o en un apéndice, con estado y remisión; incluir la frase de saturación como límite caracterizado |

### 2.3 §6 Validation: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\sec6_validation.md`

| id | línea | afirmación | evidencia nueva | clase | cambio propuesto |
|---|---|---|---|---|---|
| 6-1 | 5-12 | La referencia es CONS ∪ OCR por el cargador canónico, sobre toda la ventana | (a) El consolidado remoto perdió filas en silencio al menos cinco veces; la referencia correcta es la unión histórica (tarea 0.1, `tasks\LOOP_OBJETIVOS.md:77-97`). Mi reproducción con el snapshot de hoy ya no da lo mismo (PCC V750 38 a 36 noches; agregado V750 246 a 244). (b) Antes del 2026-06-13 el OCR no medía distancia (0 fijo) y su geometría estuvo mal calibrada hasta el 2026-06-11: en esa ventana decide la tabla sola (A119; `scripts\calidad_referencia_mirova.py:18-56`). En la ventana del paper, 85 de las 890 noches de alerta V375 dependen sólo del OCR anterior al 06-13 (estimación propia). (c) Las filas sólo OCR de Suomi NPP pueden traer distancia y clase de otra pasada hasta el 2026-10-09 (mismo archivo, hito Suomi NPP). (d) Regla SN de D-9: unas 60 de las 890 noches V375 tienen todas sus alertas en 0,05 MW o menos y cuentan como «MIROVA no vio nada» (`docs\MISSION.md:79-87`; estimación propia, no la función oficial) | REBAJADA | Reescribir el primer párrafo de §6.1: unión histórica, tramos A119, regla SN, y el OCR informado aparte antes del 06-13 |
| 6-2 | 22-26 | Cobertura 79,2 %; una alerta no capturada «can only depress the apparent recall, never inflate it» | La lógica es falsa: una alerta perdida que nosotros también habríamos perdido sale del denominador y **sube** la recall. El 79,2 % es cobertura por pasada contra el archivo TIF y cota superior (`docs\AUDIT_S128.md:262-276`); la cobertura nocturna de la tabla es 99 a 100 % desde marzo (A119; `scripts\calidad_referencia_mirova.py:23-25`) | FALSA | «Missed alerts bias recall in either direction. Night coverage of the consolidated table is 99 to 100 % from March 2026; per-pass coverage of VIIRS is lower (79.2 % against the image archive, an upper bound).» |
| 6-3 | 26-29 | «the reference carries no negative labels ... no set of confirmed empty nights» | El consolidado trae RUTINA: pasadas en que MIROVA miró y no vio nada. Negativo limpio = RUTINA nocturna sin ALERTA, FP ni ALERTA_OCR esa noche y sensor (`docs\audit_s139\MAPA_BASES_MIROVA_V1.md:312`); es métrica del criterio de victoria (`docs\MISSION.md:75-77`) | FALSA | «MIROVA's consolidated table also lists routine passes in which it detected nothing; a night with only such rows is a clean negative, against which a publication of ours can be scored.» |
| 6-4 | 29-34 | Las 98 filas diurnas V375 «are excluded from the comparison»; perderlas es «the correct behaviour» | No se excluyen: `scripts\paper_numbers.py:188-205` y `pipeline\mirova_csv_loader.py:146-206` no filtran por hora; 19 noches V375, 5 V750 y 6 MODIS son sólo diurnas y están en el denominador (`C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\scripts\estimar_noches_salida.txt`). MIROVA procesa VIIRS de día; bajo la lectura A, 40 pasadas diurnas protegidas contra 232 nocturnas (`experiments\_s151_alertas_diurnas\README.md:133-153`) | FALSA | Excluirlas de verdad en el script (y decirlo) o contarlas como pérdida por diseño: «MIROVA also alerts on daytime VIIRS passes; our night-only chain misses them by construction (D27). They are reported separately.» |
| 6-5 | 36-50 | Las dos cadenas NRT son no supervisadas | Coherente con A105 y Coppola 2026 (ya incorporado en S142) | SIN CAMBIO | Ninguno |
| 6-6 | 56-64 | Recall por noche de alerta; par por pasada a ± 20 min | El criterio de victoria cuenta por pasada (alerta protegida, `docs\S151_CRITERIO_CLASE_MIROVA.md` §3: 439 protegidas, V375 232, V750 149, MODIS 58, sobre la unión de todas las fechas) y separa el estrato bajo 1 MW | FALTA | Agregar la métrica por pasada protegida junto a la noche (A94 sigue valiendo para la noche) |
| 6-7 | 68-76 | Las dos definiciones de validez «separate detection performance from labelling performance» | Cráter válido en 89,1 % de 4.800 negativos limpios MODIS contra 93,7 % de 158 positivos (CLAUDE.md A82, l. 1009); misma condición en el 78 % de los negativos limpios (`docs\AUDIT_S149.md:88-92`). La etiqueta MODIS depende del Test 1 y del Salar (5-15) | FALSA | «The crater definition measures the presence of a cluster near the vent, which in MODIS occurs on most clean negatives as well; it is not a measure of detection.» |
| 6-8 | 82-86 | 26.028 records; 890 / 246 / 82 noches; recall 0,931 / 0,805 | 26.028 se reproduce (el excedente de hoy, 26.154, son pasadas del 2026-09-07 posteriores a la generación, inferido de `ultimo_record`); V750 da hoy 244 noches y 0,803 por la referencia que cambió. Ventana que cruza #535 (A104, CLAUDE.md l. 1305) y los hitos A119 | DESACTUALIZADA | Regenerar con la referencia unificada y por tramo; declarar el régimen del código de los records (5-18) |
| 6-9 | 90-99 | MODIS: «not a detection failure»; «no per-record answer at that resolution» | A82 y A83 rebajadas (CLAUDE.md l. 1009, 1035); banda 22 separa en Láscar, 68/73 contra 11/96 (`docs\S150_RESULTADO_MESES.md:49-58`); con banda 21 y sin Test 1 no ve nada (0/73). Además las posiciones MODIS están corridas (5-1) | FALSA | «In MODIS the dashboard publishes 10 of 82 alert nights. With band 21 as the primary MIR channel (D21) the detector does not separate alerts from clean negatives; with band 22, as in Coppola et al. (2016a), it does at Láscar (68 of 73 against 11 of 96, March to June 2026), not yet measured elsewhere.» |
| 6-10 | 105-111 | Banda de tolerancia 0,5 a 2,0 y conteo en banda | Falta decir qué magnitud se compara (núcleo F5' en V375, `pc.vrp_mw` en el resto; A10 rebajada, la suma es la más cercana: 0,783 contra 0,706 y 0,600, CLAUDE.md l. 228-237); D17 S141 pide reportar también con cenit ≤ 40° (`docs\MIROVA_DIVERGENCES.md:2216-2217`); A99 rebajada: la paridad «0,995 a igual conteo» es producto de factores opuestos (CLAUDE.md l. 1285) | REBAJADA | Definir la magnitud comparada y agregar la columna con cenit ≤ 40° |
| 6-11 | 113-123 | Sesgo de sub-integración: menos píxeles o anillo que se solapa; cúmulo a pocos cientos de metros del cráter | 1.14: en V375 el recorte de lo publicado pesa 47 % [38; 58] del déficit (Lastarria 62 %), y el reparto selección contra fondo depende de la bisagra (fondo 21 a 64 %); la razón cae con el cenit (0,76 a 0,45) sin atribución (`experiments\_s151_presupuesto_magnitud\README.md:10-20`, §3.1, `:76-80`). El fondo es la mediana de un anillo regional más tibio, no un anillo «que se solapa» (D25). El resultado de `docs\AUDIT_S134.md:11-17` es de VIIRS 375 y cinco volcanes | REBAJADA | Reescribir con las tres fuentes (lo que se publica, la selección, el fondo) y el ángulo; acotar la frase de AUDIT_S134 a V375 |
| 6-12 | 127-130 | Dos razones extremas con pocos pares | Sin cambio en los valores | SIN CAMBIO | Ninguno |
| 6-13 | 136-137 | Láscar V375 «30 of 193 dashboard nights», Copahue «210 of 214» | `numbers.json` dice 24/187 y 204/208; con la ventana a 09-07, 27/194 y 211/215; hoy 46/232 y 247/253 (mis tres corridas). Ninguna da 30/193 ni 210/214 | SIN LOCALIZAR | Usar el número del script; si se rehace §6.5 con negativos limpios, esta frase desaparece |
| 6-14 | 138-139 | «Precision requires a reference that labels negatives, and ... this one does not» | Igual que 6-3 | FALSA | Ver 6-3 y 6-16 |
| 6-15 | 143-149 | La población sin alerta es mayormente real o falla del cruce; «only a minority» son artefactos | A54 sin re-medir y armada con OCR anterior al 06-13 (`docs\audit_s150\meta\AUDITOR_F3_VARA_RETROACTIVA.md:249-259`); la causa raíz de la sobre-publicación V375 es el Test 1 integrado (S146; 5-9) | REBAJADA | Quitar la afirmación cuantitativa o re-medirla por tramo A119; nombrar el mecanismo conocido |
| 6-16 | 153-159 | No se reporta precisión; suprimir la población no emparejada quitaría el valor agregado | El criterio de victoria (2026-10-13) mide las dos direcciones; la réplica debe callar donde MIROVA calla y el valor agregado vive en `experimental` (`docs\MISSION.md:20-28`, `:47-90`) | FALSA | §6.5 nuevo: «Publication on clean negatives», por sensor y tramo A119, con el control del A/B S147 como estado de producción (86,1 / 21,4 / 5,1 %, 2026-09-01 a 09-20) y el mecanismo (Test 1 integrado) |
| 6-17 | 82-99 | Régimen de los records validados | La ventana 2026-01-01 a 08-31 es casi entera anterior a #535 (2026-08-28 23:00 UTC), y V375 publica en negativos limpios 62,1 % antes y 87,1 % después de #571 (A104, CLAUDE.md l. 1305); 0 records con marca de régimen antes de #785 | FALTA | Declarar qué código produjo los records; recomendar como ventana principal 2026-08-29 en adelante (post #535, OCR con distancia, tres satélites parejos desde 08-01 según `docs\AUDIT_S149.md`) |
| 6-18 | 1-161 | Resultados de la erupción de Chillán | En la erupción no saturó ningún píxel y el déficit de magnitud no es saturación (MIROVA 22,13 MW contra 10,36 MW nuestro, 2026-10-15 05:00 V375, `tasks\LOOP_OBJETIVOS.md:492-504`) | FALTA | Para §7 (casos), no para §6; anotarlo en el roadmap del borrador |

---

## 3. `numbers.json`, `TABLAS.md` y `README.md`

Archivos: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\numbers.json`,
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\TABLAS.md`,
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\README.md`.

### 3.1 Números de `numbers.json` tocados por este informe

Reproducción con `scripts\paper_numbers.py` (sólo lectura, salida fuera del repo). «Reproduce» quiere decir mismo valor
con el código y los datos de hoy.

| clave | valor en el paper | hoy, misma ventana | clase |
|---|---|---|---|
| `generated_utc`, `git_head`, `ventana` | 2026-09-07 23:33 UTC, `83b9df8ff`, 01-01 a 09-07 | | DESACTUALIZADA |
| `definiciones` (Noche ALERTA) | «nocturna 03-09 UTC según el loader» | el cargador y el script no filtran por hora (`pipeline\mirova_csv_loader.py:146-206`, `scripts\paper_numbers.py:194-205`); docstring en `scripts\paper_numbers.py:30` | FALSA |
| `definiciones` (Sin alerta) | «A54 (95 % son anomalías ... reales ...)» | A54 sin re-medir (F3-8); `scripts\paper_numbers.py:43` | REBAJADA |
| `n_volcanes_configurados`, `n_tier_a` | 45, 11 | 45, 11 | SIN CAMBIO (reproduce) |
| `tabla2` / `n_records_tier_a_ventana` | 26.028 | 26.154 con `--hasta 2026-09-07`; la diferencia está en pasadas del 09-07 que se commitearon después (inferido: `ultimo_record` pasa de 02:30 a 08:05 en los 11; SIN VERIFICAR registro por registro) | SIN CAMBIO (reproduce con salvedad) |
| `tabla3` | k y errores OSF | idéntica | SIN CAMBIO (reproduce) |
| `tabla4`, `agregados` MODIS y V375 | 82 / 10 / 80; 890 / 829 / 829 | idénticos con `--hasta 2026-08-31` | SIN CAMBIO (reproduce) |
| `tabla4`, `agregados` V750 | 246 noches, 198 TP, 0,805 | 244, 196, 0,803 (PCC V750 38 a 36; pares Láscar V750 178 a 177, Isluga V375 310 a 308) | DESACTUALIZADA (no reproduce: la referencia del snapshot cambió; causa probable, filas perdidas del consolidado, tarea 0.1; SOSPECHA, no comprobada fila a fila) |
| `ventana_ground_truth.fin_csv_mirova` | 2026-08-31 | 2026-10-16 | DESACTUALIZADA |
| `n_tests_collected` | 1.225 | 1.852 (`repro_0907`, HEAD `f3520f4d5`) | DESACTUALIZADA |

Valores con toda la ventana hasta hoy (sólo indicativos, `hoy\numbers.json`): 30.669 records; V375 1.052 noches y
recall 0,942; V750 282 y 0,812; MODIS 92, 0,141 dashboard y 0,978 cráter. No sirven para el paper: cruzan #535 y no
aplican A119 ni D-9.

Números del paper que **no** están en `numbers.json` y conviene sacar de un script antes de citarlos: los 98 de filas
diurnas (coincide con mi conteo ad hoc), los 30/193 y 210/214 de §6.5 (SIN LOCALIZAR), y todos los nuevos que este
informe propone (negativos limpios, protegidas, tramos A119, SN).

### 3.2 Otros ítems

| id | archivo:línea | qué | clase | cambio propuesto |
|---|---|---|---|---|
| T-1 | `TABLAS.md:89` | Pie de la Tabla 4: «"no alert" nights are NOT false positives (A54)» | REBAJADA | Distinguir «noche sin alerta» (puede no tener cobertura) de «negativo limpio» (se puede puntuar) |
| T-2 | `TABLAS.md:55-56` | Cabecera: ground truth CONS ∪ OCR del cargador canónico, sin tramos | DESACTUALIZADA | Regenerar con la unión histórica y el aviso A119 en la cabecera |
| T-3 | `TABLAS.md:84` | V750 «matched formula DiBella2024_k1.11e7» | SIN CAMBIO en el número | Rótulo: Di Bella es INGV Catania, no MIROVA (A9); el coeficiente coincide con Campus 2022, citarlo así |
| T-4 | `README.md:6-18` | «Regla única de números»: el script es la fuente | FALTA | Agregar al script: referencia unificada (`scripts\referencia_mirova_unificada.py`), `calidad_referencia_mirova.avisar` (A119 punto d), regla SN, negativos limpios, por pasada protegida, y la marca de régimen |
| T-5 | `README.md:26-27` | sec5 con 1 placeholder | DESACTUALIZADA | Actualizar el estado de las secciones tras esta revisión |

---

## 4. Lo que quedó SIN VERIFICAR

- Las tres estimaciones ad hoc (noches sólo diurnas, noches con todas sus alertas ≤ 0,05 MW, noches sólo OCR antes del
  06-13): usan el snapshot de hoy y una regla simplificada, no `scripts\clase_mirova.py::aplicar_regla_minimas` ni la
  unión histórica. Sirven para dimensionar, no para citar.
- La causa de que V750 no reproduzca (246 a 244): coherente con las pérdidas del consolidado de la tarea 0.1, no
  comprobada fila a fila.
- El origen de los 30/193 y 210/214 de §6.5: SIN LOCALIZAR.
- Si el estimador TIR se calcula en memoria aunque no se publique (5-14).
- El conteo de módulos con cabecera FICHA (15 o 18 según el criterio).
- Las citas a papers que este informe propone agregar o reinterpretar (Coppola 2016a p. 187 sobre la conectiva, Coppola
  2014 sobre el AND, Campus 2022 p. 16 a 17 sobre el día, Fig. 11 de Coppola 2016a): vienen de documentos del repo que
  dicen haber renderizado la página; antes de escribirlas en el paper, verificarlas renderizando la página (A95).
- No corrí la suite ni los evaluadores de los A/B; los números de A/B salen de sus documentos de resultado, todos
  marcados como verificados con contexto limpio en el repo salvo el probe 1.17 (PARCIAL) y el probe MxD03 (PARCIAL).

## 5. Orden sugerido

1. §6.1 y §6.5 (ítems 6-1 a 6-4, 6-14 a 6-17): son los que cambian la tesis del paper; dependen de la decisión de
   ventana y de vara.
2. §5.1, §5.3 y §5.4 (5-1, 5-3, 5-7, 5-9, 5-11 a 5-13): Methods tiene que describir lo que corre.
3. §6.3 MODIS (6-7, 6-9) junto con D21 en §5.7.
4. §5.7 como tabla de divergencias (5-23 a 5-27).
5. `paper_numbers.py` primero (T-4), después regenerar `numbers.json` y `TABLAS.md`, y recién ahí reescribir el texto.
