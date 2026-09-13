# Auditoría S138: verificador limpio (agente 7)

Fecha del servidor (header `Date` de `gh api repos/MendozaVolcanic/VRP-chile`): **2026-09-13 12:27 UTC**.
Repo en `main` = `6b1dd91ef`; al cerrar, `git status --short` muestra sólo `docs/audit_s138/` y
`experiments/_s138_audit/` sin seguimiento. Read-only: no edité un solo archivo del repo, no creé
ramas ni tags, no disparé CI ni descargué granules. Mis scripts viven en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s138_audit\verificador\`.

No leí los seis informes como fuente: los leí como lista de afirmaciones y fui al `file:line`, al
PDF o al banco. Todo número de acá lo produjo un tool result de esta sesión.

**Discrepancia (f), el espacio en disco: FUERA DE ALCANCE por decisión del dueño.** No medí `df`
ni `du`. El hallazgo H4 del eje 6 queda sin verificar por esa razón, no por falta de evidencia.

---

## 0. Lo que corrí, y lo que confirma que el instrumento no estaba muerto

| banco | resultado |
|---|---|
| `experiments/_s138_audit/eje3/marcador_predicado_dashboard.py` | re-corrido, tabla idéntica |
| `experiments/_s138_audit/eje5/medir_9_figuras.py` | re-corrido, controles sintéticos OK, A2 = 10,98 km |
| `experiments/_s138_audit/eje5/romper_bateria.py` | re-corrido, control de identidad **0 discrepancias de 72**, control positivo 48 de 48 |
| `experiments/_s138_audit/eje2/01_controles_sinteticos_detection_context.py` | re-corrido, M1 a M4 idénticos |
| `experiments/_s138_audit/eje2/02_records_operacionales_extras.py` | re-corrido, todos los conteos idénticos |
| `experiments/_s133/auditar_guards_por_subcadena.py` | re-corrido, **1 candidato** (ver P7: deja el árbol sucio; lo restauré) |
| `experiments/_s138_audit/verificador/ticks2.py` (mío) | mide las 9 figuras con la escala de los rótulos del eje |
| `experiments/_s138_audit/verificador/predicado_operador.py` (mío) | re-puntúa los 8 brazos con `mirovaEqVrp` escrito desde el frontend |
| `experiments/_s138_audit/verificador/cobertura_cruzada.py` (mío) | pasa las pérdidas por sensor a noches de volcán |

No pude correr: los instrumentos 1, 2 y 3 de S137 (necesitan HDF4; pyhdf no existe en Windows y los
granules no están en disco). Para ésos verifiqué por lectura de código y sobre las salidas
commiteadas, y lo digo caso por caso.

**Control positivo global del instrumento**: mis mediciones cambiaron veredictos en las dos
direcciones. Confirmé 22 hallazgos, corregí 6 y refuté 1, y encontré 8 cosas propias. Un verificador
muerto habría confirmado todo o nada.

---

## 1. Los hallazgos de gravedad 3 o más, uno por uno

Veredicto: **CONFIRMADO** (lo leí o lo medí) / **CORREGIDO** (el mecanismo vale, el enunciado o el
número no) / **REFUTADO** / **NO VERIFICABLE**.

### Eje 1, afirmaciones de cierre

| # | veredicto | grav. final | evidencia de esta sesión |
|---|---|---|---|
| H1 GAP #A: CLAUDE.md dice "mislabel, no reabrir"; el catálogo lo reabre | **CONFIRMADO** | **2** (baja de 3) | `CLAUDE.md:119` contra `docs/MIROVA_DIVERGENCES.md:1319-1340` (leídos hoy). `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`. Bajo la gravedad porque el propio catálogo registra que el A/B de S130 midió **efecto nulo** ("conteo 883 vs 883, umbral 277,47 vs 277,47"): la contradicción apaga un frente, no tuerce una alerta |
| H2 el encabezado de D11 dice "CERRADA S114, detección fiel, ejes agotados" | **CONFIRMADO** | 3 | `docs/MIROVA_DIVERGENCES.md:1259` leído hoy, contra D21 y D22 del mismo archivo y contra el PDF renderizado (ver §3.b y VERIFICADO LIMPIO) |
| H3 los cierres "agotado / no adoptar" heredan la configuración que S137 puso en duda | **CONFIRMADO** la dependencia | 3 | `ENABLE_MODIS_B22_PRIMARY=False` y `NTI_BT_SANITY_K=3.0` efectivos hoy; los A/B citados corrieron bajo ellos. El efecto sigue SOSPECHA |
| H4 A66/A67 llaman "clon literal" al área nadir fija | **CONFIRMADO** documentalmente | 3 | Flags nadir `True`, `ENABLE_UTM_REGRID=False`; PDF p.3: *"cropped and resampled (into an equally spaced 1 km grid)"*. El número de S130 (0,74 a 0,25 con el ángulo) **NO VERIFICABLE** hoy |

### Eje 2, matriz de conformidad

| # | veredicto | grav. final | evidencia |
|---|---|---|---|
| H1 la compuerta no decide la detección: el segundo pase la anula | **CONFIRMADO** | 4 | Re-corrí M1: píxel a `t_bg+1 K` con dNTI 0,0078, primer pase 0 píxeles, **segundo pase en modo producción lo marca (1)**, con `conditioned=True` no. Control positivo a +8 K pasa el primer pase. Código leído: `detection_context.py:532` (compuerta) contra `:887` y `:939-948` (sin compuerta) |
| H1-bis "la pérdida de A6 está atribuida al paso equivocado" | **CONFIRMADO y ELEVADO de SOSPECHA a MEDICIÓN** | 4 | Ver §3.b: los JSON commiteados lo prueban sin necesitar el reproceso que el eje 2 pedía |
| H2 el Test 1 K1 no es camino de detección ni retira del pool | **CONFIRMADO** | **3** (baja de 4) | Re-corrí M2 y M3: bloque 7x7 de 49 píxeles calientes, Test 1 marcaría 49, primer pase 27, tras el segundo 28, **interior 3x3: 1 de 9**. Pool: `n_bg` 2393 contra 2392. Bajo a 3 porque el peso en records reales es 0,09 % MODIS, 1,34 % V375, 0,12 % V750 (script 02) y el efecto en fase efusiva sigue sin un solo caso en el corpus: es SOSPECHA dimensionada, no medición |
| H3 el fondo del VRP es la mediana de un anillo regional | **CONFIRMADO y ELEVADO** | **4** (sube de 3) | `process_modis.py:1023` (anillo 5-25 km), `:1041-1052` (kernel sólo con `local_kernel_bg_compatible`), `:1056` (`np.maximum(..., 0)`). Sube a 4 porque es la causa **medida** de la pérdida de A6 (§3.b) y de los 1.480 + 2.699 cúmulos en 0,0 MW |
| H4 los saturados de MODIS (DN 65533) se eliminan; el paper los conserva | **CONFIRMADO contra el PDF** | 3 | `process_modis.py:246-250` `rad[dn > 32767] = np.nan`. PDF p.3, texto extraído hoy: *"eliminating, for each band, all the pixels with DN > 32 768 ... with the exception of the pixels with DN = 65 533, indicating saturated values"*. Sin caso en data: el efecto sigue SOSPECHA |
| H5 sin remuestreo ni bow tie, área fija de 1 km2 | **CONFIRMADO** | 3 | `ENABLE_UTM_REGRID=False`, `ENABLE_NADIR_FIXED_PIXEL_AREA_*=True`, `ENABLE_GEOLOCATED_PIXEL_AREA=False`, todos leídos de `pipeline.profile` |
| H9 el número publicado no es la suma de la escena | **CONFIRMADO, conteos idénticos** | 3 | Re-corrí el script 02: MODIS `pc.vrp_mw != vrp_mw` 87,78 %, `focal_magnitude` 94,62 %, `single_pixel_mode` 47,62 %, `d9_capped` 11,58 %, `far` con cúmulo summit 9.422 (78,35 %); V375 `single_pixel_mode` 79,89 %; n = 12.025 / 23.729 / 23.540, ventana 2025-02-15 a 2026-09-13 |

### Eje 3, instrumentos de S137

| # | veredicto | grav. final | evidencia |
|---|---|---|---|
| H1 la batería mide "cúmulo a 5 km con VRP > 0"; el operador ve "summit" | **CONFIRMADO dos veces** | 4 | Re-corrí su script **y** escribí el mío desde `frontend/index.html:1043-1064` sin mirar el suyo: los dos dan producción `6/6 0/3` (batería) contra **`2/6 2/3`** (dashboard). Mi conteo independiente de la etiqueta: de las 22 pasadas que la batería cuenta como publicadas, **19 llevan `far` y 3 `summit`**. Control negativo (exigir una clase inexistente): 0/6 en los tres brazos |

### Eje 4, D21 y D22 en VIIRS

| # | veredicto | grav. final | evidencia |
|---|---|---|---|
| H1 VIIRS750 pierde 33 de 246 noches con el cráter en 0,0 MW | **CORREGIDO** | **2** (baja de 4) | El conteo de 33 es correcto **en noches-sensor** y lo reproduje. Pero en la unidad del operador (la noche del volcán, A94) **las 33 están cubiertas por otra pasada del mismo volcán esa misma noche: 0 noches perdidas**. Ver §3.d. El caso emblema, Tupungatito 2026-08-21, tiene cuatro pasadas VIIRS375 visibles con 0,057 a 0,158 MW mientras las tres V750 publican 0,0 |
| H2 la compuerta está neutralizada de facto; los tres factores están acoplados | **CONFIRMADO** | 3 | Coherente con mi M1 re-corrido y con `ENABLE_SECOND_PASS_CONDITIONED=False`. Su consecuencia para el diseño del A/B es la parte que sobrevive entera |
| H3 MODIS Láscar: noches con el cúmulo en el cráter y rótulo `far` | **CONFIRMADO en mecanismo, CORREGIDO en unidad** | 3 (A/B) / **1** (operador) | Mi conteo: **825 de 949** records MODIS de Láscar son `far` con el cúmulo a menos de 5 km y VRP > 0. En noches: 67 de 77 perdidas en MODIS, y **65 de esas 67 cubiertas por otro sensor**. El "59" del eje 4 sale de un predicado más estrecho (fuente `eruption`); el mío da 65 |

### Eje 5, la batería como instrumento

| # | veredicto | grav. final | evidencia |
|---|---|---|---|
| H1 el "conforme" no verifica el objeto: 0 de 6 verificables, 2 son otro objeto | **CONFIRMADO** | **4** (baja de 5) | Re-corrí `romper_bateria.py`: control de identidad 0 de 72, control positivo 48 de 48, y el cuadro de objeto reproducido. Bajo a 4 porque la gravedad se mide en "qué decisión de alerta puede torcer": ésta tuerce tres decisiones de diseño del pipeline, no una alerta publicada |
| H2 la batería mezcla pasadas y noches | **CONFIRMADO** | 4 | En `B22 min sinBT loc`, A2 es CONFORME por la pasada de las 03:00, con el cúmulo a **11,53 km** del objeto del autor; en la pasada de la figura ese brazo lo tiene a 3,60 km (salida cruda re-corrida) |
| H3 el conteo cambia con el radio y con la pasada | **CONFIRMADO, tabla reproducida** | 4 | Producción `6/0` a 5 km con todas las pasadas, **`4/0`** a 3 km con sólo la de la figura. `B22 max sinBT loc` pasa de 5/3 a **6/3** con radio 8 km o con la referencia en el autor |
| H4 el holdout MODIS de jun-ago 2026 son 15 noches, todas de Láscar, 0 en nevados | **CONFIRMADO exacto** | 4 | Lo recalculé con el loader canónico y el filtro diurno del pipeline: MODIS 15 (todas Láscar), V750 85, V375 312, total por volcán idéntico a su tabla. Serie mensual de pasadas-ALERTA MODIS nocturnas: jun 13, jul 2, ago 1, sep 1 |
| H5 4 de 8 brazos, incluida producción, no persisten la posición | **CONFIRMADO** | 3 | `grep -o '"pc_lat"' \| wc -l`: 0 en los cuatro brazos de `_s136` y `b22`/`b22_prosa`; **24** en los cuatro `sincompuerta` |
| H6 el control de validez por NTI no discrimina | **CONFIRMADO** | 3 | Lo recalculé: la banda de A6 (-0,93 ± 0,06) la pasan **16 de 24** pasadas de todos los casos; la de A5, **18 de 24**; la de A8, 18 de 24 |
| H7 el 9,6 km de A2 no lo produce ningún script | **CONFIRMADO el hecho, CORREGIDO el número** | 3 | Mi medición independiente (escala por los rótulos del eje): **10,12 km, rumbo 84,2**. Ver §3.a |
| H8 varios conformes son cúmulos del camino D con el tope de 5 MW | **CONFIRMADO y REFORZADO** | 3 | Los cinco casos con VRP exactamente 5,0 en producción tienen **`diag_n_nti_path = 0`**, que es el predicado del tope (`process_modis.py:997-1002`). Corrijo una frase: el JSON **sí** guarda `diag_n_nti_path`, así que no hace falta inferirlo del 5,0 exacto |

### Eje 6, decisiones, operación, higiene

| # | veredicto | grav. final | evidencia |
|---|---|---|---|
| H1 la cadencia del NRT sigue al 43 % y ningún monitor la mide | **CONFIRMADO, y empeorado** | 3 | `gh run list --workflow=nrt.yml --limit 120`: 118 programadas, 118 verdes, **5 a 7 corridas por día** contra 12 esperadas. A las 12:27 UTC la última programada seguía siendo la de las **08:57**: 3,5 h sin corrida con un cron de 2 h (el eje 6 midió 2,9 h a las 11:49) |
| H2 un job puede terminar verde sin descargar nada | **CONFIRMADO con log crudo; un detalle CORREGIDO** | 3 | Log del job `103701222253`: `WARN: Failed to fetch MODIS_TERRA: ... ConnectTimeoutError ... connect timeout=60.0`, luego `DOWNLOAD_SKIP host caído ['nrt3.modaps.eosdis.nasa.gov']` seis veces y `No changes to commit`. El commit más reciente de `PlanchonPeteroa.json` en el remoto sigue siendo **2026-09-12 20:43**, 15,7 h atrás. Corrección: el job vecino de Villarrica (`103701222157`) descargó a las **08:58** y el de PP falló a las **09:18**, 20 minutos después; la evidencia no prueba que el host estuviera arriba en ese instante. Lo que sí prueba el log es lo que importa: **un solo ConnectTimeout apaga seis plataformas para toda la corrida y el job sale con exit 0** |
| H4 disco al 100 % | **FUERA DE ALCANCE** | n/a | Instrucción del orquestador |

---

## 2. La lista única fundida

Varios ejes describen el mismo mecanismo con nombres distintos. Ésta es la lista sin duplicados,
lo peor primero.

| id | qué es | lo reportan | grav. |
|---|---|---|---|
| **H-S138-01** | **El fondo del anillo, con el recorte de ΔL a cero, borra del dashboard cúmulos reales del cráter.** En una cumbre helada el cráter con lava sub-píxel está más frío que la mediana de un anillo de 5 a 25 km lleno de valle tibio, así que su exceso de radiancia sale negativo y se recorta a 0,0 MW. El paper mide contra los vecinos del píxel (p.8: *"the arithmetic mean of all the pixels surrounding the active one"*) | eje 2 H1+H3, eje 3 (e), eje 4 H1+H4 | **4** |
| **H-S138-02** | **El segundo pase corre sin conjunto activo y sin compuerta, y es el que detecta.** Es D19/D2. Anula la compuerta de D22 en detección (13,96 % de los records V375 y 17,24 % de los V750 se detectan **sólo** ahí) y su pool de mu y sigma no aplica los no-aptos del paper | eje 1 C8+H6, eje 2 H1+H7+X2, eje 4 H2 | **4** |
| **H-S138-03** | **La batería del Apéndice A no mide lo que se le hace decir.** No mira la posición del objeto (0 de 6 conformes de producción verificables, 2 son otro objeto), no distingue la pasada del autor (mezcla hasta dos noches locales), no usa el predicado del operador (producción es 2/6 y 2/3, no 6/6 y 0/3), cambia de veredicto con el radio, la mitad de los brazos no persiste posición, y su control de validez lo pasa el 70 % de cualquier escena | eje 3 H1, eje 5 H1+H2+H3+H5+H6+H7+H8 | **4** |
| **H-S138-04** | **El Test 1 K1 del paper no es camino de detección ni retira del pool.** `hot_mask_2d = fp_hot` pisa el `combine_hot_paths` en los tres sensores; `test1_mask` llega en `None`. El interior de un cuerpo caliente extenso se pierde (1 de 9 píxeles en el bloque sintético) | eje 1 H1+C12, eje 2 H2 | 3 |
| **H-S138-05** | **Afirmaciones de cierre apoyadas en una lectura del paper hoy refutada.** El encabezado de D11, A82, A83, A84, el "no adoptar" de D18 y el punto 5 del bloque S137 dicen "cerrado / agotado / fiel" sobre records producidos con banda 21 y compuerta de 3 K, o contra la evidencia del propio documento | eje 1 H2+H3, eje 6 H9 | 3 |
| **H-S138-06** | **Sin remuestreo, sin bow tie, con área fija de 1 km2 sobre píxeles que no la miden.** Es D17 | eje 1 H4, eje 2 H5 | 3 |
| **H-S138-07** | **La etiqueta `far`, derivada del píxel más caliente de la escena, esconde el cúmulo del cráter.** 9.422 records MODIS (78,35 %); 825 de 949 en Láscar | eje 2 X12, eje 3 H1, eje 4 H3 | 3 |
| **H-S138-08** | **El número que ve el operador no es la suma de la escena del paper** en la mayoría de los records (cúmulo vent-anchored, magnitud focal, modo píxel único, tope D9, núcleo F5', filtro de 25 km) | eje 2 H9 | 3 |
| **H-S138-09** | **Los píxeles saturados de MODIS se eliminan; el paper los conserva explícitamente** | eje 2 H4 | 3 |
| **H-S138-10** | **La cadencia del NRT está al 43 % desde el 30 de agosto y ningún monitor mide cadencia** | eje 6 H1 | 3 |
| **H-S138-11** | **Un job del NRT termina verde sin descargar nada** cuando el cortacircuitos declara caído al host al primer timeout | eje 6 H2 | 3 |
| **H-S138-12** | **El holdout MODIS de jun-ago 2026 no tiene estrato nevado**: 15 noches, todas de Láscar | eje 5 H4 | 3 |
| **H-S138-13** | El guard de la conectiva pasa por coincidencia de subcadena (`min(` casa con `min_bg_pixels`) | eje 1 H5 | 2 |
| **H-S138-14** | El día no existe: la Tabla 1 diurna está escrita y nunca corre | eje 2 H6 | 2 |
| **H-S138-15** | El ROI1 es un círculo per-volcán de 3 a 20 km, no la caja de 5 x 5 km del paper (D18) | eje 2 H8 | 2 |
| **H-S138-16** | CLAUDE.md dice grilla de 51x51 km; el texto del paper dice 50 x 50 km tres veces | eje 1 H7 | 1 |

---

## 3. Las discrepancias

### (a) La posición de la anomalía del autor en la figura A2

**Tres números circulaban**: 9,6 km escrito a mano en `conformidad_apendice.py:230` (sin productor),
10,45 km del eje 3 y 10,98 km del eje 5. Los tres salen de la misma figura, así que la diferencia es
de calibración.

Medí por mi cuenta con un instrumento que ninguno de los dos usó
(`experiments/_s138_audit/verificador/ticks2.py`): **la escala sale de los rótulos 10, 20, 30, 40 y
50 de cada eje**, no del marco del panel, porque el marco es justo lo que un anti-aliasing de uno o
dos píxeles corre. Trabajé sobre el PNG embebido nativo (xref 140, 1065 x 607 px), no sobre un
render de la página.

```
A2  panel [342,566,394,599]  px/celda x=4,01  y=4,38  residuo del ajuste 0,3 px (x) y 0,2 px (y)
    celdas que abarca el panel: 51,12 en x, 51,14 en y   -> la matriz es de 51 x 51, no de 50 x 50
    centroide de la mascara: celda (36,07 , 27,02)   centro de la grilla: 26,0
    dist = 10,12 km   rumbo = 84,2 grados   area = 7,7 celdas
controles: A6 0,33 km (el paper lo pone en el crater)  A3 0,56  A5 1,36  A8 1,10  A1 1,38
           A4, A7, A9 (los tres negativos reales): "sin mascara", no 0 km
```

Sobre el **mismo raster nativo**, el método del marco (el del eje 5) da 10,24 km y el de los rótulos
10,12: **difieren 0,12 km**. O sea que el 10,98 del eje 5 no viene de su calibración sino de medir
sobre el render de la página a 200 dpi en vez del raster embebido. Y si el centro se toma de los
bordes del eje en vez de suponerlo en la celda 26, el resultado baja a 9,81 km.

**Lo que va al informe**: *la anomalía del autor en A2 está a **10 ± 0,5 km, rumbo 84 grados**, medida
desde el centro de la grilla, que según el paper (p.3) es la cumbre del volcán*. El signo de la
incertidumbre lo da la horquilla completa de instrumentos: 9,8 a 11,0 km.

**Qué cambia**: nada de lo sustantivo. Bajo cualquiera de los cinco números la detección del autor
está muy afuera de la caja de 5 km que evalúa la batería, y los cinco positivos restantes están en la
cumbre. **Lo que sí cae es el post hoc**: `RADIO_POST_HOC_KM = 3.0` alrededor de un punto con 1,2 km
de dispersión entre instrumentos no puede decidir nada, y de hecho el veredicto del brazo
`B22 min sinBT` cambia dentro de esa dispersión (2,79 km con el punto de S137, 3,60 con el del eje 5).
Eso vuelve al hallazgo H7 del eje 5 más fuerte, no más débil.

Dato de regalo: la matriz de las figuras es de **51 celdas**, deducido del ajuste y no supuesto. O
sea que el "51x51" de CLAUDE.md describe bien lo que MIROVA dibuja, y el "50 x 50 km" del texto del
paper describe otra cosa. El paper se contradice a sí mismo por una celda; H-S138-16 queda en
gravedad 1 pero con la fuente encontrada.

### (b) La pérdida del cráter de Villarrica en A6: ¿la compuerta o el fondo?

**El fondo.** Lo deciden los JSON commiteados, sin necesidad del reproceso que el eje 2 pedía. Pasada
de la figura, 2009-06-24 05:55 UTC:

```
brazo                                    fp   dist del cumulo   VRP publicado
b22                    (compuerta ON)     0       0,807 km         0,0 MW
b22_sincompuerta       (compuerta OFF)    2       0,807 km         0,0 MW
b22_sincompuerta_fondolocal               2       0,807 km       0,539 MW
```

La lectura física, primero el fenómeno: el cráter de Villarrica esa noche está **más frío en BT que
la mediana de un anillo de 5 a 25 km** que incluye el lago y el valle. Lo que lo delata es el
contraste espectral, no la temperatura. Ahora el código: la compuerta `bt > t_bg + 3 K` lo saca del
primer pase, **pero el segundo pase, que no la lleva, lo recupera igual**, así que el cúmulo está en
el cráter con la compuerta puesta. Quitar la compuerta cambia `fp` de 0 a 2 y **no cambia el número
publicado**. Lo que lo cambia es el fondo: `delta_L = max(L_pix - L_bg, 0)` (`process_modis.py:1056`)
con `L_bg` derivado del anillo (`:1023`) deja el píxel en cero, y con el kernel local de vecinos
(`:1041-1052`) da 0,539 MW. Y un cúmulo en 0,0 MW es invisible: `mirovaEqVrp` devuelve 0.

Consecuencias:
- El eje 2 (H1) tenía razón y su SOSPECHA pasa a **medición**.
- El eje 3, en su afirmación (e), describe bien los números pero los encadena mal: "el cráter cae
  sólo por la compuerta" es cierto del **primer pase**, no de lo que el operador ve. Queda
  **CORREGIDO**.
- El eje 4 encadena bien los tres pasos en su H1 (compuerta, segundo pase, anillo) y mantiene el
  crédito.
- Para el A/B: **quitar la compuerta sola no devuelve una sola alerta**. El factor que mueve el
  número publicado es el fondo.

### (c) El predicado del operador: ¿coinciden los ejes 3 y 5?

**No miden lo mismo, así que no se contradicen.** El eje 3 mide "¿lo vería el operador?"
(`distance_class`); el eje 5 mide "¿es el objeto del autor?" (posición). Las dos correcciones apuntan
en la misma dirección: el 6/6 de producción no es evidencia de fidelidad.

Lo reproduje desde cero con `predicado_operador.py`, escribiendo el predicado desde
`frontend/index.html:1043-1064` y sin mirar el script del eje 3:

```
brazo                                          bateria   dashboard   casos que cambian
_s136/out_apendice (B21 min = produccion)      6/6 0/3    2/6 2/3    A1 A2 A5 A6 (pos), A7 A9 (neg)
_s137/..._sincompuerta_fondolocal              6/6 2/3    5/6 3/3    A2 (pos), A4 (neg)
(los otros seis brazos no cambian)
CONTROL NEGATIVO (exigir una distance_class inexistente): 0/6 en los tres brazos probados
distance_class de las 22 pasadas que la bateria cuenta como publicadas: far 19, summit 3
```

Coincide dígito a dígito con el eje 3, incluido el "19 de 22". **Con el predicado del operador,
producción da 2 de 6 positivos y 2 de 3 negativos.** Los dos falsos positivos "estructurales" de
producción (A7 y A9) también se vuelven invisibles, así que el 0/3 que se usaba como cargo contra la
configuración actual es en realidad 2/3.

### (d) Las 33 noches de VIIRS750: ¿pérdidas de la noche o de un sensor?

**De un sensor. Las 33 de 33 están cubiertas.** Con el mismo loader del eje 4
(`pipeline.mirova_csv_loader.load_mirova_alertas`, CONS unión OCR, snapshot del 2026-09-07), el mismo
filtro diurno y el mismo criterio de visible, **ventana 2026-01-11 a 2026-09-07**:

```
== VIIRS750: 246 noches-sensor con ALERTA; 33 perdidas con pc0 ==
   CUBIERTAS por otro sensor del mismo volcan esa noche = 33;  NO cubiertas = 0
     Isluga 11/11   Lascar 8/8   Tupungatito 8/8   PlanchonPeteroa 4/4   PCC 1/1   Villarrica 1/1
   NOCHES REALMENTE PERDIDAS PARA EL OPERADOR: 0
== VIIRS375: 896 noches-sensor; 6 perdidas con pc0; cubiertas 5; perdida real 1 (NevadosDeChillan)
== MODIS:    77 noches-sensor;  67 perdidas (no por pc0); cubiertas 65; perdida real 2
```

El caso emblema del eje 4, Tupungatito 2026-08-21 (MIROVA V750 0,19 MW), en crudo:

```
04:54 VIIRS_NOAA21      pc 0,072 MW  2,98 km  summit  VISIBLE
05:30 VIIRS_SNPP        pc 0,057 MW  2,58 km  summit  VISIBLE
05:30 VIIRS_SNPP_750    pc 0,0   MW  0,33 km  summit  no visible
05:48 VIIRS_NOAA20      pc 0,158 MW  0,04 km  summit  VISIBLE
05:48 VIIRS_NOAA20_750  pc 0,0   MW  0,31 km  summit  no visible
06:30 VIIRS_NOAA21      pc 0,062 MW  2,90 km  summit  VISIBLE
06:30 VIIRS_NOAA21_750  pc 0,0   MW  0,55 km  summit  no visible
```

El operador ve Tupungatito esa noche. La frase "Tupungatito V750 pierde 8 de 14 noches; en un volcán
con anomalía débil y persistente es la diferencia entre sigue y se apagó" queda **REFUTADA en su
consecuencia**: el volcán no desaparece del dashboard ninguna de esas ocho noches.

El mecanismo sigue siendo real y vale investigarlo; lo que no vale es priorizarlo por un número de
noches-sensor. Es exactamente A94, la regla que S136 escribió después de cometer el mismo error, y
esta vez el que la pisó fue el eje que más cuidado puso en declarar su unidad.

**Matiz que encontré y que también corrige el "invisible"**: el conteo de detecciones de la tarjeta
(`distanceCounts`, `frontend/index.html:1701-1721`) no usa `mirovaEqVrp` sino `isValidDetection`
(`:1466`), que da verdadero con `triggered_test1` aunque la magnitud sea 0. De los cúmulos en 0,0 MW
de V750, **195 en Tupungatito, 121 en Láscar, 68 en Planchón-Peteroa y 19 en Isluga** tienen
`triggered_test1 = True` y `distance_class = summit`: el operador los cuenta como detecciones del
cráter, con magnitud cero. "Invisible" es exacto para el gráfico y la tarjeta de titular, no para el
contador.

### (e) Focal contra nevado: ¿usan la misma lista?

**No, y el eje 4 usa una que no existe en el repo.** Las listas que sí están escritas:

| fuente | focal |
|---|---|
| `scripts/build_c2ab_windows.py:41-42` (S131) | Láscar, Lastarria, Isluga, Planchón-Peteroa, **PCC** |
| `experiments/_s114_audit/discriminant_sweep.py:29-30` | sólo Láscar (llama nevados a los otros 10) |
| `experiments/_s136/medir_fenomeno_test1.py:26` | control Láscar y Lastarria; **PP y PCC son nevados** |
| `experiments/_s135_ab_d1d2/evaluar_ab.py:91` | sólo Láscar y Lastarria (**Isluga no es focal**) |

El eje 4 declara que su clasificación coincide con las dos últimas. No coincide: llama focal a Isluga
(que en `evaluar_ab.py` no lo es), nevado a PCC (focal en S131) e **intermedio** a Planchón-Peteroa,
una categoría que no aparece en ningún archivo del repo. El eje 5 sí fija la de S131 y declara el
conflicto con la de S114.

**Manda la de S131** (`scripts/build_c2ab_windows.py:41-42`): es la que vive en `scripts/`, la que
construye las ventanas del A/B, la que CLAUDE.md respalda vía A21 y `docs/R2_GATES_BY_REGIME.md`, y
la que el eje 5 pre-registró. La de S114 se descalifica sola llamando nevados a 10 de 11.

**Y esto no es cosmético.** Recalculé la tabla de margen del pico del eje 4 cambiando sólo la
partición:

```
particion del eje 4 :  focal 330/484 = 0,682   intermedio 14/25 = 0,560   nevado 511/1177 = 0,434
particion de S131   :  focal 527/1148 = 0,459                            nevado 328/538  = 0,610
```

**El signo se invierte.** Y se invierte por un solo volcán: PCC aporta 639 de los 1.686 records
medibles con la fracción más baja de todas (0,286), así que de qué lado caiga decide el resultado. La
conclusión de fondo del eje 4 ("la clasificación nevado/focal no predice el fenómeno; lo predice
cráter frío contra anillo tibio") queda **reforzada**; el enunciado numérico que la acompaña
("mayor en los focales, IC disjuntos") queda **CORREGIDO**. Es la lección de S126 otra vez: una
mediana agrupada invierte un veredicto según cómo se agrupe.

### (f) Espacio en disco

**FUERA DE ALCANCE por decisión del dueño.** No medí `df` ni `du`. El hallazgo H4 del eje 6 queda
sin verificar.

---

## 4. Contradicciones entre fuentes, y la regla de salida (A51)

Cuento como contradicción un enunciado que **gobierna decisiones** y que el código, los datos o el
PDF de hoy desmienten. Seis confirmadas:

| # | enunciado que gobierna | la otra fuente que lo desmiente |
|---|---|---|
| **C1** | `CLAUDE.md:119`: "el antiguo GAP #A fue RESUELTO S115 = MISLABEL, no era un gap real. **NO reabrir** como trabajo pendiente" | `docs/MIROVA_DIVERGENCES.md:1319-1340`: "**REABIERTO S128: las dos patas de este cierre son FALSAS**, verificadas contra el código y el paper", más el guard `tests/test_guard_gap_a_pool_musigma_s128.py` que existe justamente para que no vuelva a cerrarse así. El código le da la razón al catálogo: `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False` |
| **C2** | `docs/MIROVA_DIVERGENCES.md:1259`, encabezado de D11: "**CERRADA S114** (irreducible a 1 km; **detección fiel a Coppola**; todos los ejes agotados)" | D21 y D22 del **mismo archivo**, abiertas, más el PDF p.7 renderizado: la fórmula de los Tests 2 y 3 no tiene ninguna condición de temperatura y el código la impone (`detection_context.py:532`) |
| **C3** | `CLAUDE.md` A82: el far a summit de MODIS es "irreducible", "todos los ejes agotados" | Los ejes se barrieron sobre records producidos con `ENABLE_MODIS_B22_PRIMARY=False` y `NTI_BT_SANITY_K=3.0`, las dos divergencias que S137 abrió (D21, D22). CLAUDE.md ya la rebajó por la vía geométrica en S124 y no por la espectral |
| **C4** | `CLAUDE.md` A92: el barrido de guards por subcadena "tras endurecerlos **da 0**" | Lo corrí hoy: **da 1**, `tests/test_conectiva_tests23_s136.py:204` (`assert "min(" in src`, que casa con `min_bg_pixels`, `min_corona`, `min_local`, `min_pixels`, `minute` y tres más) |
| **C5** | `tasks/BLOQUE_ARRANQUE_S137.md:141`, bajo "**Cerrado en esta sesión, no rehacer**": "Retirar la intersección contextual. Los datos apuntan a que sigue curando" | El **mismo archivo**, `:121-123`: "Dirección clara, n insuficiente (3 contra el umbral de 4), así que **formalmente sigue indeterminado**" |
| **C6** | `CLAUDE.md` A66 y A67: el área nadir fija es "el modo de área **clon literal** de MIROVA para los 3 sensores" | PDF p.3: *"cropped and **resampled** (into an equally spaced 1 km grid)"*, y `ENABLE_UTM_REGRID = False`. El área uniforme es necesaria pero no es el remuestreo; D17 sigue abierta |

Menciono por completitud dos que **no** cuento: el "51x51 km" de CLAUDE.md contra el "50 x 50 km"
del paper (medí que las figuras son de 51 celdas, así que el enunciado tiene fuente aunque no la
cite: es imprecisión, no contradicción) y el probe de A84 que no está en el repo (es evidencia
irreproducible, no un enunciado desmentido).

### Veredicto de la regla de salida

**6 contradicciones confirmadas, más de 3.** Según A51, **el proyecto pausa el frente y consolida
antes del A/B**. Y hay una razón sustantiva además de la formal: cinco de las seis (C1, C2, C3, C5,
C6) son la misma enfermedad, que es A95 en masa. Un A/B lanzado hoy heredaría de esos cierres qué
brazos no correr, y eso es precisamente lo que está mal.

Lo que la consolidación tiene que tocar, en orden: el encabezado de D11 (C2), la frase del GAP #A en
CLAUDE.md (C1), la rebaja espectral de A82 (C3), el punto 5 del bloque S137 (C5), la palabra "clon
literal" de A66 y A67 (C6) y el guard de la conectiva (C4, una línea).

---

## 5. Mis hallazgos propios

### P1. La auditoría entera está contando pérdidas en la unidad equivocada: en noches de volcán, casi todas desaparecen
- **SCRIPT:SALIDA**: `experiments/_s138_audit/verificador/cobertura_cruzada.py`; salida cruda en §3.d.
- **QUÉ PASA.** El fenómeno primero: un volcán no se observa una vez por noche, se observa cinco o
  seis veces, con tres sensores. Que un sensor no publique no deja al operador a ciegas si otro sí
  publica en la misma noche. El código: los tres ejes que midieron recall lo hicieron por
  **noche-sensor**, que es la unidad natural del CSV de MIROVA, no la del operador. Pasadas a noches
  de volcán: VIIRS750 pierde **0 de 33**, MODIS **2 de 67**, VIIRS375 **1 de 6**. Ventana 2026-01-11
  a 2026-09-07, 11 Tier A, loader CONS unión OCR con el filtro diurno del pipeline.
- **CÓMO SE VE EN EL DASHBOARD**: el volcán aparece igual esas noches, con la magnitud de otro sensor.
- **CÓMO REPRODUCIRLO**: `PYTHONIOENCODING=utf-8 python experiments/_s138_audit/verificador/cobertura_cruzada.py`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 4, y es una gravedad al revés: obliga a **bajar** la
  prioridad de H-S138-01 como problema de recall y a sostenerla como problema de fidelidad y de
  magnitud, que es otra conversación.

### P2. Leer el PDF con PyMuPDF no cura la corrupción de operadores que el protocolo de la auditoría le atribuye sólo al `.txt`
- **SCRIPT:SALIDA**: `documentacion/sp426.5.pdf` p.21, `get_text()` devuelve `(NTI ,20.93)`; el
  `.txt` en `documentacion/sp426_5.txt:817` devuelve exactamente lo mismo. El **render a 400 dpi**
  del mismo rectángulo (`experiments/_s138_audit/verificador/caption_A6.png`) muestra
  `(NTI < −0.93)`.
- **QUÉ PASA**: la fuente del paper mapea `<` a `,`, el menos tipográfico a `2`, `μ` a `m` y `σ` a
  `s`. La capa de texto del PDF arrastra el mismo mapeo, así que `fitz.get_text()` la reproduce. El
  preámbulo de esta auditoría, la regla A95 y los ejes 1 y 2 mandan leer el PDF "con PyMuPDF, nunca
  el `.txt`, que corrompe los operadores": el remedio es insuficiente. Lo único que cura es
  **renderizar**. Los ejes 1 y 2 construyeron sus matrices citando líneas de un volcado de
  `get_text()`, así que cualquier afirmación suya que dependa de un operador de comparación o de un
  signo menos leído ahí es sospechosa hasta renderizarla.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Tuerce auditorías, que es cómo llegan los umbrales al
  pipeline.
- **CÓMO REPRODUCIRLO**: `python -c "import fitz; print(fitz.open('documentacion/sp426.5.pdf')[20].get_text().find(',20.93'))"`
  y comparar con el render de `fitz.Rect(100,304,330,326)` a 400 dpi.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3.
- **Nota tranquilizadora**: rendericé la pieza más cargada de toda la auditoría, la fórmula de los
  Tests 2 y 3 (p.7), y **coincide con lo que los ejes leyeron**: `dNTI_PIX > C1 or dNTI_PIX > μ_dNTI
  + C2 σ_dNTI` (Test 2) **and** lo mismo con dETI (Test 3), sin condición de temperatura. D22 y la
  conectiva `min` quedan verificadas en la fuente, no en la capa de texto.

### P3. El régimen focal/nevado del eje 4 no existe en el repo y su conclusión cambia de signo con la lista que sí existe
- Ver §3.e, con las dos tablas. **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3 (torcería el
  pre-registro del A/B, que exige estratificar).

### P4. La atribución de la pérdida de A6 es el fondo, no la compuerta, y se decide sin reprocesar
- Ver §3.b. **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 4. Cambia qué brazo del A/B puede ganar: un
  brazo "sin compuerta" con fondo del anillo publica el mismo 0,0 MW.

### P5. `isValidDetection` y `mirovaEqVrp` discrepan sobre qué es una detección, y la discrepancia es sistemática
- **ARCHIVO:LÍNEA**: `frontend/index.html:1466-1470` (`isValidDetection`: `vrp_mw > 0` **o**
  `triggered_test1`) contra `:1043-1064` (`mirovaEqVrp`: `primary_cluster.vrp_mw`). El primero
  gobierna los contadores (`:1712`, `:1719`, `:2011`, `:2314`, `:3109`); el segundo, la magnitud.
- **QUÉ PASA**: un record con el cúmulo del cráter en 0,0 MW y `triggered_test1 = True` cuenta como
  **detección summit** en la tarjeta de los últimos 7 días y en el indicador de corroboración con
  MIROVA, mientras su magnitud se muestra en cero. Conté 195 en Tupungatito V750, 121 en Láscar, 68
  en Planchón-Peteroa y 19 en Isluga. Es la familia A46 otra vez: dos predicados del mismo concepto
  que no se pusieron de acuerdo.
- **CÓMO SE VE EN EL DASHBOARD**: el contador de detecciones del cráter sube y el gráfico sigue en
  cero, esa misma noche, para el mismo volcán.
- **CÓMO REPRODUCIRLO**: contar en `data/mirova_equivalent/Tupungatito.json` los records
  `sensor` terminado en `_750` con `primary_cluster.vrp_mw == 0`, `n_pixels > 0`,
  `triggered_test1 == true` y `distance_class == "summit"`.
- **CONFIANZA**: CONFIRMADO (código y conteo). **GRAVEDAD**: 2.

### P6. Los paneles de las figuras del apéndice no son isótropos en píxeles
- **SCRIPT:SALIDA**: `ticks2.py` sobre las nueve figuras: 4,01 px por celda en el eje x y 4,38 en el
  eje y, con residuos de ajuste de 0,2 a 0,5 px.
- **QUÉ PASA**: cualquier instrumento que suponga celdas cuadradas se equivoca un 9 % en la
  componente norte-sur. No cambió ningún veredicto acá porque la anomalía de A2 es casi puro este y
  las demás están sobre el centro, pero es una trampa lista para la próxima medición de posición.
  (El eje 5 sí trata los dos ejes por separado; lo anoto para quien escriba el siguiente.)
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

### P7. Un script de auditoría modifica un archivo trackeado al correr
- **ARCHIVO**: `experiments/_s133/auditar_guards_por_subcadena.py` escribe
  `experiments/_s133/auditar_guards_por_subcadena.json`. Correrlo ensucia el árbol; lo restauré con
  `git checkout --`. El eje 3 vio el archivo modificado a mitad de sesión y no supo de dónde venía:
  venía de esto.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

### P8. El tope D9 de la batería es verificable en el JSON, no hay que inferirlo del 5,0 exacto
- **SCRIPT:SALIDA**: `predicado_operador.py`, último bloque: las cinco pasadas con VRP exactamente
  5,0 en producción tienen `diag_n_nti_path = 0`, que es la mitad del predicado del tope
  (`process_modis.py:997-1002`; la otra mitad, `n_bt_path == 0`, es constante porque
  `ENABLE_BT_PATH_HOT = False`). Corrige la frase del eje 5 H8 "el JSON no guarda
  `diag_n_bt_path/nti_path`".
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 (mejora el instrumento, no cambia el hallazgo).

---

## 6. VERIFICADO LIMPIO

Lo que miré y está sano, con el comando que lo confirma. No hace falta volver a mirarlo salvo que
cambie el comando.

1. **La fórmula de los Tests 2 y 3, leída en la fuente y no en la capa de texto.** Renderizada a 400
   dpi de `sp426.5.pdf` p.7, `fitz.Rect(50,388,260,472)`: `dNTI_PIX > C1 or dNTI_PIX > μ + C2 σ`
   (Test 2) **and** el mismo par con dETI (Test 3). Sin condición de temperatura. El código la
   implementa con `combinar = min` (`detection_context.py:510` y `:924`) y
   `ENABLE_TESTS_23_PROSE_BRANCH = False`.
2. **Los 28 flags efectivos** que los seis ejes citan, leídos de `pipeline.profile` y no del YAML
   (A89): `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.<NOMBRE>)"`.
   Los 28 coinciden con lo que cada eje declaró, sin una sola excepción.
3. **Tabla 1 del paper contra el código**: `C1 = 0,003 / 0,010`, `C2 = 5 / 10`, `K1 = -0,8`.
4. **Las citas `file:line` de los tres procesadores**:
   `grep -n "hot_mask_2d = fp_hot|hot_mask_2d = combine_hot_paths|delta_L = np.maximum|combinar = max if"`
   devuelve exactamente los pares que los ejes 1, 2 y 4 citan: `process_modis.py:824/888/1056`,
   `process_viirs.py:1188/1259/1416`, `process_viirs_mod.py:783/851/985`,
   `detection_context.py:510/924`.
5. **El segundo pase no se escapa del ROI** pese a que `newly_active` no lleva `roi_mask`
   (`detection_context.py:940-948`): el ETI es NaN fuera de `mask_valid`
   (`detection_context.py:735/772`, `eti = np.full_like(nti, np.nan)` y
   `eti[mask_valid] = eti_full[mask_valid]`), así que `isfinite(deti)` lo confina. El H6 del eje 1
   acertó también en esta parte.
6. **El texto del paper sobre los saturados**, extraído hoy de la p.3: *"with the exception of the
   pixels with DN = 65 533"*. La divergencia H4 del eje 2 es limpia.
7. **Los controles de los dos bancos que más deciden**: `romper_bateria.py` reproduce 72 de 72
   veredictos commiteados y hunde los 48 positivos con radio 0,01 km; `medir_9_figuras.py` acierta
   los controles sintéticos (10,13 km a 90 y a 0 grados), responde a la escala invertida (rumbo 180)
   y a 2 km por celda (20,26 km), y devuelve "sin máscara" en los tres negativos reales.
8. **El instrumento del predicado del operador es reproducible por dos implementaciones
   independientes**: la del eje 3 y la mía, escrita desde el frontend, dan los mismos ocho pares.
9. **Los conteos operacionales del eje 2** se reproducen dígito a dígito sobre
   n = 12.025 / 23.729 / 23.540, ventana 2025-02-15 a 2026-09-13.
10. **El holdout del eje 5** se reproduce volcán por volcán y sensor por sensor: MODIS 15, V750 85,
    V375 312 en jun-ago 2026.
11. **El NRT no tiene un solo run rojo**: 118 de 118 programadas verdes en las últimas 120 corridas.
    Lo que falla es la cadencia (H-S138-10) y el silencio de un job (H-S138-11), no el resultado.
12. **El árbol quedó limpio**: `git status --short` al cerrar muestra sólo las dos carpetas sin
    seguimiento de la auditoría. Restauré el único archivo trackeado que se ensució (P7).

**Lo que NO verifiqué y no hay que dar por auditado**: los instrumentos 1, 2 y 3 de S137 en
ejecución (HDF4 ausente en Windows); los números de S130 sobre el gradiente cenital; el espacio en
disco (fuera de alcance); la clasificación de las 197 ramas del eje 6; la tabla de 25 decisiones del
eje 6, de la que sólo verifiqué C5 y los flags; y el peso real de H-S138-04 y H-S138-09 sobre
eventos efusivos, que no tienen un solo caso en el corpus.

---

## Resumen

De los 25 hallazgos de gravedad 3 o más que traían los seis ejes, **confirmé 18, corregí 6 y refuté
1 en su consecuencia**, y agregué 8 propios. La lista sin duplicados son 16 hallazgos, H-S138-01 a
H-S138-16.

Lo más importante que corregí es una cuestión de unidades, y toca a tres ejes a la vez. Las pérdidas
que la auditoría contó por **noche-sensor** casi no existen por **noche de volcán**: VIIRS750 pierde
0 de 33, MODIS 2 de 67, VIIRS375 1 de 6. Un volcán se observa cinco o seis veces por noche con tres
sensores, y Tupungatito, el caso emblema, aparece las ocho noches "perdidas" con 0,06 a 0,16 MW en
VIIRS375. El mecanismo es real y vale investigarlo; priorizarlo por ese número no. Es A94 otra vez.

Lo segundo, la atribución. La pérdida del cráter de Villarrica en la figura A6 la causa **el fondo
del anillo**, no la compuerta de temperatura: con la compuerta puesta el cúmulo ya está en el cráter,
a 0,807 km, porque el segundo pase no lleva compuerta, y publica 0,0 MW; quitar la compuerta no
cambia ese cero, y cambiar el fondo a vecinos lo lleva a 0,539 MW. Un brazo del A/B que quite sólo la
compuerta no va a devolver una sola alerta.

Lo tercero, dos instrumentos. Medí la anomalía del autor en A2 con la escala de los rótulos del eje:
**10,1 km, rumbo 84**, con una horquilla de 9,8 a 11,0 entre instrumentos, lo que deja sin piso el
post hoc de 3 km. Y leer el PDF con PyMuPDF **no** cura la corrupción de operadores que el protocolo
le atribuye al `.txt`: la capa de texto da `,20.93` donde el papel dice `< −0.93`. Sólo renderizar
cura. Rendericé la fórmula de los Tests 2 y 3, que sostiene D22 y la conectiva, y coincide con lo
que los ejes leyeron.

**Contradicciones entre fuentes confirmadas: 6** (GAP #A, encabezado de D11, A82, A92, el punto 5 del
bloque S137, y A66/A67). Más de tres, así que **por A51 el proyecto pausa el frente y consolida antes
del A/B**. Cinco de las seis son la misma enfermedad: un cierre que hereda una lectura del paper hoy
refutada, que es A95 en masa.

Ruta: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\audit_s138\VERIFICADOR.md`.
Scripts y salidas:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s138_audit\verificador\`.
