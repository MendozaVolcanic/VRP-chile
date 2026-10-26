# Informe de cambios propuestos al borrador del paper, versión 2 (S152, 2026-10-16)

Versión 2 de `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\INFORME_CAMBIOS_PAPER.md`, con las 14 correcciones del
verificador con contexto limpio (`C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\VERIFICADOR_INFORME_PAPER.md`:
33 ítems revisados, 19 CONFIRMADO, 14 CORREGIR, 0 REFUTADO). Apliqué las 14; hay un desacuerdo de detalle sobre una
cifra que el verificador propuso (§5 de este informe). Sólo lectura: no se editó nada del repo.

El borrador está en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\` (última edición
2026-09-15; `numbers.json` generado el 2026-09-07 en `83b9df8ff`). Lo cotejé contra lo que cambió desde el 2026-09-15
(rama `loop/activo`, HEAD `f3520f4d5`). En `pipeline/` no hay cambios en la lógica de producción: todos los flags nuevos
entraron apagados.

Material de este informe (fuera del repo):

- `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\repro_0831\`: `scripts/paper_numbers.py --hasta 2026-08-31`, la misma ventana de ground truth del paper.
- `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\repro_0907\`: `--hasta 2026-09-07 --tests`, la misma ventana de records.
- `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\hoy\`: sin `--hasta`, o sea hasta el 2026-10-16. **Sólo indicativo.**
- `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\scripts\estimar_noches.py` y su salida: estimación ad hoc. **No es la función oficial de D-9.**
- Del verificador: `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\verif\` (`dia_recuperadas.py` y los CSV de `83b9df8ff`).

Los números de línea valen para `f3520f4d5`. Las líneas de la bitácora de `tasks\LOOP_OBJETIVOS.md` se corren con cada
vuelta del loop: hay que buscarlas por número de vuelta.

Clases: **FALSA**, **REBAJADA** (cierto en parte), **DESACTUALIZADA** (era cierto al escribirse, o el número cambió),
**FALTA** (un resultado nuevo que debería estar), **SIN CAMBIO** (revisado).

Columna «verif.» de las tablas: **C** = confirmado por el verificador; **K** = corregido por él y aplicado acá;
**SR** = no lo revisó uno a uno, queda **SIN VERIFICAR** por un tercero.

Todas las citas a PDF de este informe (Coppola 2016a p. 187 y Fig. 11, Coppola 2014, Campus 2022 p. 16 y 17, Coppola
2026) salen de documentos del repo que dicen haber renderizado la página. Ni yo ni el verificador renderizamos ninguna:
quedan **SIN VERIFICAR en imagen** (A95) hasta que alguien lo haga antes de escribirlas en el paper.

---

## 1. Resumen en una pantalla

**Conteos** (69 filas, una por afirmación; la §3 cubre `numbers.json`, `TABLAS.md` y `README.md`):

| sección | FALSA | REBAJADA | DESACTUALIZADA | FALTA | SIN CAMBIO | total |
|---|---|---|---|---|---|---|
| §4 Background | 0 | 3 | 0 | 1 | 5 | 9 |
| §5 Methods | 4 | 10 | 3 | 8 | 2 | 27 |
| §6 Validation | 5 | 4 | 4 | 3 | 2 | 18 |
| §3: `numbers.json`, `TABLAS.md`, `README.md` | 1 | 2 | 6 | 1 | 5 | 15 |
| **total** | **10** | **19** | **13** | **13** | **14** | **69** |

Qué cambió respecto de la v1 (14 FALSA, 18, 10, 13, 13, 1 SIN LOCALIZAR):

- 5-5 bajó de FALSA a DESACTUALIZADA y 5-24 de FALSA a REBAJADA.
- 6-3, 6-14 y 6-16 eran la misma premisa falsa contada tres veces. Ahora es una sola fila (6-3). Lo que queda de 6-16,
  «suprimir quitaría el valor agregado», es DESACTUALIZADA: dejó de valer cuando cambió el objetivo.
- 6-13 dejó de ser SIN LOCALIZAR: queda localizada y DESACTUALIZADA.
- 4-9 pasó a SIN CAMBIO.
- Se agregó 6-11b (Isluga, `sec6_validation.md:116`).

Las 10 FALSA son **10 errores independientes**. Dos están emparentados: 6-4 y la definición «nocturna» de
`numbers.json` vienen de la misma ausencia de filtro horario en el script, pero cada una está escrita en un lugar
distinto.

**Los 5 más graves** (reordenados con las correcciones). La unidad (pasada o noche) y la ventana van en cada uno.

1. **«La referencia no tiene negativos», y por eso «no se puede reportar precisión», es FALSO.**
   `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\sec6_validation.md:26-29`, `:138-139`
   y `:153-159`.
   - El consolidado trae filas RUTINA: 32.751 en la ventana del 2026-01-01 al 08-31, con mediana de VRP 0,0 (conteo del
     verificador). Con ellas se define el negativo limpio (`docs\audit_s139\MAPA_BASES_MIROVA_V1.md:312`).
   - **En el régimen de los records que valida el paper** (anterior a #535, del 2026-03-01 al 08-28), producción
     publica en negativos limpios así (`experiments\_s142_linea_base\RESULTADOS.md`, filas `contexto_marzo_a_535`):

     | sensor | por pasada | por noche de volcán |
     |---|---|---|
     | VIIRS 375 | 60,7 % de 2.675 | 79,8 % de 1.104 |
     | VIIRS 750 | 22,3 % de 4.367 | 55,9 % de 1.772 |
     | MODIS | 11,5 % de 4.009 | 18,6 % de 1.910 |

   - Después de #571 VIIRS 375 sube a 86,5 % de 325 por pasada y 100 % de 102 por noche (del 09-01 al 09-17, misma
     tabla). El 86,1 / 21,4 / 5,1 % de la v1 es el control del A/B S147, del 09-01 al 09-20 y por pasada
     (`docs\S147_RESULTADO_AB_SIN_TEST1.md:30-38`). **Si §6 se queda en enero a agosto, no puede citar el 86,1 %.**
   - El paper omite el defecto principal de la réplica (A98: la brecha es de sobre-publicación, no de recall) y lo
     presenta como imposible de medir.
2. **«Cada producto viaja con su geolocalización» es FALSO para MODIS.**
   `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\sec5_methods.md:6-14`.
   - Ya lo era al escribirse. El pipeline baja MOD03/MYD03 (`pipeline\fetch.py:189-194`) y no los lee
     (`pipeline\process_modis.py:470-471`). Interpola la grilla de 5 km del L1B (`:34-35`, `_interp_geo` en `:342`).
   - Con MxD03 como árbitro, en 7 gránulos de Láscar (veredicto PARCIAL), nuestra posición se corre 1,15 a 2,58 km
     hacia el sensor **del lado del frame 0 del barrido**, con cenit de 30° o más
     (`experiments\_s151_probe_mod03\README.md:6-20`).
   - A eso se suma un término a lo largo de la traza de 2 − 0,00197·línea km (r = 0,955, n = 157 con cenit bajo 30°;
     `experiments\_s151_mxd03_etiquetas_verif\resultado\VERIFICADOR_RESULTADO.md:108-120`).
3. **La lectura de MODIS en §6.2 y §6.3 es FALSA** (`sec6_validation.md:68-76` y `:90-99`).
   - Por noche, que es la unidad del paper: el 98,2 % de las noches de negativo limpio tiene cúmulo en el cráter
     (`docs\audit_s146\VERIFICADOR_CONTEXTO_LIMPIO.md:215-217`). Es más que el 0,976 del paper para las noches con
     alerta, así que la «recall cráter» no mide detección.
   - Por pasada da lo mismo: 89,1 % de 4.800 negativos contra 93,7 % de 158 positivos, del 2026-01-29 al 08-28.
   - Con banda 22 **y sin el Test 1 integrado**, por pasada y sólo en Láscar, MODIS separa: 68 de 73 alertas contra 11
     de 96 negativos limpios. Producción, en la misma población, publica 8 de 73 contra 1 de 96
     (`docs\S150_RESULTADO_MESES.md:49-64`).
4. **Methods no describe la magnitud que se publica, y dos afirmaciones de fidelidad están mal**
   (`sec5_methods.md:100-128` y `:184-202`).
   - Faltan cuatro reglas de lo publicado:
     - el fondo es la mediana de un anillo de 5 a 25 km, con recorte a cero (D25);
     - en el modo de un píxel (3 píxeles o menos y bajo 5 MW) se publica el píxel más caliente, lo que vale para el
       75,5 % de los records con cúmulo (`docs\FICHA_SDA_VRP_CHILE.md:25`);
     - hay un tope de 5 MW con fondo bajo 270 K (1.565 cúmulos topados, CLAUDE.md A23);
     - en V375 se publica el núcleo F5' (D32).
   - §5.3 llama «literal» a una conectiva que el paper permite leer de dos maneras
     (`pipeline\detection_context.py:512-525`).
   - §5.7 cierra D18 con un A/B que no midió la caja (REBAJADA, ver 5-24).
5. **Las alertas diurnas «excluidas» no se excluyen** (`sec6_validation.md:29-34`). Es FALSO como enunciado y chico
   como número.
   - `scripts\paper_numbers.py:194-205` y `pipeline\mirova_csv_loader.py:146-206` no filtran por hora, y nunca lo
     hicieron. Hay 19 noches V375, 5 V750 y 6 MODIS sólo diurnas en el denominador.
   - Pero 14 de las 19 V375 ya cuentan como recuperadas (por un record nocturno del mismo día UTC), y también 3 de 5 en
     V750 y 1 de 6 en MODIS. Excluirlas mueve la recall de 0,931 a 0,936 (V375), de 0,803 a 0,808 (V750, con la
     referencia de hoy) y de 0,122 a 0,118 (MODIS); script `verif\dia_recuperadas.py` del verificador.
   - Que «perderlas es lo correcto» no lo decide la física: lo decide el criterio de fidelidad del 2026-10-13. Las 40
     pasadas diurnas protegidas contra 232 nocturnas son de otra ventana (del 2026-01-10 al 10-14, con A119, los tres
     sensores; `experiments\_s151_alertas_diurnas\README.md:133-153`). De esas 40, 19 tienen magnitud desproporcionada
     (probable reflejo) y 21 no tienen evidencia ni de reflejo ni de calor.

**Antes de reescribir, Nicolás tiene que decidir tres cosas:**

- (a) Si la validación se queda en el régimen anterior a #535 (y entonces cita sus tasas propias) o se rehace desde el
  2026-08-29, por tramo A119.
- (b) Si `paper_numbers.py` pasa a usar la unión histórica (`scripts\referencia_mirova_unificada.py`), la regla SN y el
  etiquetador de negativos limpios de `scripts\banco_paridad.py`.
- (c) Si §6 adopta las tres métricas del criterio de victoria (`docs\MISSION.md:47-90`).

---

## 2. Tabla por sección

Las rutas que empiezan con `docs\`, `pipeline\`, `scripts\`, `experiments\`, `tasks\`, `.github\` o `CLAUDE.md` cuelgan
de `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`. El texto sugerido va en inglés, como el
manuscrito.

### 2.1 §4 Background: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\sec4_background.md`

| id | línea | afirmación | evidencia | clase | verif. | cambio propuesto |
|---|---|---|---|---|---|---|
| 4-1 | 62-64 | Tests 2 y 3: «dNTI > C1 or dNTI > μ + C2·σ», como única lectura | `pipeline\detection_context.py:512-525`: la fórmula da el umbral `min(C1, μ+C2σ)`, y la prosa de la misma página describe C1 como cota inferior (`max`). Con la fórmula, el piso gobierna el 100 % de MODIS y el 99,9 % de VIIRS. Con `max`, en VIIRS 375 la publicación en negativos limpios baja de 35,7 % a 2,7 %, comparando brazos **sin Test 1** (B contra F, de abril a agosto, `docs\S150_RESULTADO_MESES.md:45-48`), no producción contra `max`; el recall de esos meses sigue pendiente de Nicolás (l. 34-41). Coppola 2014 escribe AND (l. 20-23) | REBAJADA | K | «The same page also describes C1 as a minimum threshold, with the scene statistics governing in variable scenes; the two readings (effective threshold min or max of C1 and μ + C2σ) are not equivalent, and Coppola et al. (2014) state the conjunction explicitly.» Verificar p. 187 y Coppola 2014 en imagen |
| 4-2 | 91-92 | «the product's detectable floor is of the order of 1 MW» | En VIIRS 375 el banner de MIROVA dice NONE de 0,02 a 0,05 MW y VERY LOW de 0,05 a 0,91 MW (`docs\S151_CRITERIO_CLASE_MIROVA.md` §2) | REBAJADA | SR | «...of the order of 1 MW for MODIS; at 375 m the near-real-time product reports anomalies down to a few hundredths of a MW.» |
| 4-3 | 122-125 | Escala de intensidad de la Fig. 11 | El pie contradice a la figura (S151, `docs\S151_CRITERIO_CLASE_MIROVA.md` §2, página renderizada según ese documento); el banner de hoy corta en 1 MW | REBAJADA | SR | Citar el pie, notar la contradicción y describir el banner actual con su fecha de observación |
| 4-4 | 129-138 | Caveats publicados | MIROVA procesa VIIRS de día con umbrales más altos (Campus 2022 p. 16 y 17, según `experiments\_s151_alertas_diurnas\README.md:120-124`) | FALTA | C | «MIROVA processes daytime VIIRS overpasses with the higher daytime thresholds of Table 1 (Campus et al., 2022).» |
| 4-5 | 24-32 | Fondo = media de los vecinos; alerta multipíxel = suma | Reforzado por D25 S141 y D32 | SIN CAMBIO | C | Opcional: citar Campus 2022 p. 7 §3.2 como fuente NRT |
| 4-6 | 98-116 | Grillas y bandas | Coherente con D17 S141 (`docs\MIROVA_DIVERGENCES.md:2207-2213`) | SIN CAMBIO | C | Ninguno |
| 4-7 | 88-90 | Umbrales «self-adapting» | Bien atribuido al paper | SIN CAMBIO | SR | Retomar en §8 (piso C1, `detection_context.py:520-522`) |
| 4-8 | 142-145 | No hay implementación de referencia | Sin evidencia nueva | SIN CAMBIO | SR | Ninguno |
| 4-9 | 283-287 (nota 8) | «Muy Bajo» es etiqueta del sitio, no del paper | Sigue siendo cierta | SIN CAMBIO | K | Sólo agregar la fecha de observación (banner leído por el OCR v30 desde agosto de 2026) |

### 2.2 §5 Methods: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\sec5_methods.md`

| id | línea | afirmación | evidencia | clase | verif. | cambio propuesto |
|---|---|---|---|---|---|---|
| 5-1 | 6-14 | MODIS se lee «with their MOD03/MYD03 geolocation files» | `pipeline\process_modis.py:34-35`, `:342`, `:470-471` (desde `c3e8aca603`, 2026-04-04); `pipeline\fetch.py:189-194`. Corrimiento: ver grave 2 | FALSA | C | «For MODIS, pixel positions are interpolated from the 5 km tie points of the L1B granule; MOD03/MYD03 are retrieved but not used. On the frame-0 side of the scan, at zenith angles of 30° or more, this places pixels 1 to 2.6 km toward the sensor in the cases measured at Láscar, plus an along-track term of up to about 2 km (Section 5.7).» |
| 5-2 | 8-9 | Banda 21 primaria | El paper usa la 22 (D21, `docs\MIROVA_DIVERGENCES.md:2596-2611`) | FALTA | SR | Declarar D21 en §5.7 con el resultado de Láscar y su salvedad |
| 5-3 | 30-33 | Sólo noche porque «MIR is unusable by day»; «cold at 11 µm» | MIROVA procesa VIIRS de día (4-4); D27 (`docs\MIROVA_DIVERGENCES.md:2752-2764`). Ya estaba en la nota H2 del editor (`sec5_methods.md:297-301`); «cold at 11 µm» es la frase que §6 dice haber quitado por no estar en la literatura (`sec6_validation.md:238-239`) | FALSA | C | «Detection is restricted to night overpasses. This is our choice, not MIROVA's, which also processes daytime VIIRS data with higher thresholds (divergence D27).» Quitar «cold at 11 µm» |
| 5-4 | 39-43 | Cron de 2 h que acota la antigüedad de la serie | Unas 5 corridas al día ya en S139 (`docs\audit_s139\NRT_CADENCIA_Y_MEJORAS.md:1`); 34 corridas del 09-25 al 10-02 (`docs\audit_s150\VERIFICADOR_AUDITORIA.md:319-321`); cron externo desde el 2026-10-16 | FALSA | C | Describir la cadencia real y no prometer 2 h |
| 5-5 | 55-58 | `experimental` «never run by the cron» | Era cierto el 2026-09-14 (salió del cron NRT en #667, `2bcc9916a`, 15:28; edición del borrador `0d483e53c`, 16:55). Dejó de serlo el 2026-10-09 con `.github\workflows\experimental-diario.yml` (#775, `600cb6f09`) | DESACTUALIZADA | K | «A separate `experimental` profile, frozen at the operational detection of 2026-10-09, runs daily in its own workflow and subdirectory.» |
| 5-6 | 70-71 | C1 y C2 «by day» | De día no corre nada (D27, `ENABLE_DAYTIME_VIIRS = False`) | REBAJADA | SR | «coded but not run» |
| 5-7 | 78-80 | «implements Tests 2 and 3 literally» | Ver 4-1 (el 35,7 a 2,7 % es sin Test 1, en los dos brazos). `ENABLE_TESTS_23_PROSE_BRANCH = False` | REBAJADA | K | «...implements the formula as printed (effective threshold min(C1, μ + C2σ)); the paper's prose supports the stricter reading, still under evaluation.» |
| 5-8 | 84-87 | Los no aptos salen del pool de μ y σ | El segundo pase no los saca (D26, `docs\MIROVA_DIVERGENCES.md:2732`) | REBAJADA | SR | «...in the first pass; the second pass does not apply these exclusions (D26).» |
| 5-9 | 94-96 | Test 1 integrado para fuentes subpíxel | Es un detector propio (D30) y el camino que más publica: el control S147, por pasada del 09-01 al 09-20, publica 86,1 % en V375 y apagarlo lo baja a 28,7 % (`docs\S147_RESULTADO_AB_SIN_TEST1.md:30-38`). El Test 1 por píxel del paper no es un camino de detección (D23) | FALTA | SR | Declararlo con su peso, dando ventana y unidad |
| 5-10 | 102-111 | k reconstruidos del OSF | `tabla3` idéntica; identidad del OSF con error 8,9e-8 (`experiments\_s151_presupuesto_magnitud\README.md:24-26`) | SIN CAMBIO | SR | Ver T-3 |
| 5-11 | 102-103 | L_bg sin definir | Mediana de un anillo de 5 a 25 km, kernel local en 5 volcanes, recorte a 0 (D25, `docs\MIROVA_DIVERGENCES.md:2683-2700`) | FALTA | C | «L_bg is the median of a 5 to 25 km annulus (a local 3 × 3 kernel for five volcanoes), and negative excesses are set to zero; MIROVA uses the mean of the non-alerted neighbours (D25).» |
| 5-12 | 100-128 | La magnitud publicada | Modo de un píxel (75,5 % de los records con cúmulo, `docs\FICHA_SDA_VRP_CHILE.md:25`); tope de 5 MW con fondo bajo 270 K (1.565 topados, 277 summit, 343 sobre 5 MW, corpus al 2026-10-14, CLAUDE.md A23); núcleo F5' en V375 (D32; A10: 0,783 la suma, 0,706 el núcleo y 0,600 `pc.vrp_mw`, sobre 1.512 pares) | FALTA | C | Párrafo «What is published» con las tres reglas y sus números fechados |
| 5-13 | 115-121 | Área nadir como «fidelity requirement» | A66 y A67 rebajadas; remuestreo «partially» (D17 S141); razón de 0,76 en nadir a 0,45 en el borde (`experiments\_s151_presupuesto_magnitud\README.md:76-80`); escalón robusto de MIROVA sólo a 52,66° (`experiments\_s151_angular_119\INFORME.md`) | REBAJADA | SR | «This restores the calibration of k but does not reproduce the resampling; our ratio to MIROVA still falls with zenith angle, an effect not yet attributed.» |
| 5-14 | 125-128 | Estimador TIR «applies» | `ENABLE_VRP_TIR_OUTPUT = False` | REBAJADA | SR | «implemented but not part of the published output» (sin verificar si se calcula en memoria) |
| 5-15 | 144-149 | «detect wide, classify visually» | Objetivo cambiado (`docs\MISSION.md:20-28`); etiqueta MODIS desde el hotspot final (`VERIFICADOR_RESULTADO.md` de la 1.17, Punto 1); MIROVA informa el foco lejano fuerte (`experiments\_s151_seleccion_mirova\README.md:12-19`) | REBAJADA | SR | Reescribir con el objetivo vigente y la regla de etiqueta por sensor |
| 5-16 | 137-140 | Radios internos de los KML | MIROVA mide desde el centro de su grilla en Tupungatito, PCC y Planchón Peteroa (`docs\MIROVA_DIVERGENCES.md:2312-2318`) | FALTA | SR | Una frase con la diferencia de origen |
| 5-17 | 159 | `[NUM: n_tests_collected]` | 1.225 en `numbers.json`; 1.852 hoy (`repro_0907`) | DESACTUALIZADA | SR | Regenerar con el script |
| 5-18 | 157-160 | Reproducibilidad | Marca de régimen por record desde #785 (2026-10-15) y `first_processed_utc` desde #769 | FALTA | SR | Mencionarlo, y declarar que la ventana validada es anterior |
| 5-19 | 161-166 | La compuerta de MISSION | Criterio de victoria (`docs\MISSION.md:47-90`) | FALTA | SR | Una frase con el criterio |
| 5-20 | 172-176 | Ficha v1.5, 16 módulos | Ficha v1.8, 2026-10-15 (`docs\FICHA_SDA_VRP_CHILE.md:7`); 15 o 18 módulos según el criterio | DESACTUALIZADA | SR | Citar la v1.8 y contar con un script |
| 5-21 | 185-186 | D2 y D3 | Tramos A119 (`scripts\calidad_referencia_mirova.py:18-56`) | REBAJADA | SR | Remitir a §6.1 |
| 5-22 | 186-188 | D13 | Sin número fijado | SIN CAMBIO | C | Opcional: dar el 70,7 % |
| 5-23 | 188-189 | D17: «our per-image grid is not centred» | `ENABLE_UTM_REGRID = False`; D17 trata de la grilla F70 apagada (`docs\MIROVA_DIVERGENCES.md:2205`); contradice `sec5_methods.md:116` | FALSA | C | «We do not resample onto MIROVA's grid; an implemented regridding (disabled) was centred on the wrong point (D17).» |
| 5-24 | 189-191 | D18: «an A/B ... did not improve parity» | Literalmente un A/B corrió y no mejoró la paridad, pero no medía la caja (marca S148). La primera medición válida también falló: veto por una protegida MODIS de Láscar (`docs\MIROVA_DIVERGENCES.md:2303-2310`). Que la posición de ese píxel esté afectada por el corrimiento MODIS está SIN VERIFICAR (`experiments\_s151_probe_mod03\README.md:20`) | REBAJADA | K | «An early A/B did not test the box (a wiring defect); the first valid test failed the acceptance criterion by one protected MODIS alert whose pixel position may be affected by the MODIS geolocation error. The divergence remains documented (D18).» |
| 5-25 | 191-194 | D19 | Medición S144: sitio tibio estable, 86 % permanente | REBAJADA | SR | Una frase |
| 5-26 | 198-202 | D20 «declared rather than corrected» | «Despreciable» pasó a «chico y no medido» (`docs\MIROVA_DIVERGENCES.md:2541`) | REBAJADA | SR | «a Planck-function estimate (not measured on our data)» |
| 5-27 | 184-202 | Lista de §5.7 | Faltan D21, D23, D24, D25, D26, D27, D30, D32, el tope D9, el corrimiento MODIS y el GAP #A. Saturación en Chillán: 0 píxeles en 385 gránulos y en 58 pasadas, I04 máximo 355,96 K; techos latentes de M15 y NOAA-21 (`experiments\_s151_techos_120\INFORME.md`) | FALTA | SR | Tabla de divergencias abiertas, con estado y remisión |

### 2.3 §6 Validation: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\sec6_validation.md`

| id | línea | afirmación | evidencia | clase | verif. | cambio propuesto |
|---|---|---|---|---|---|---|
| 6-1 | 5-12 | Referencia CONS ∪ OCR con el cargador canónico en toda la ventana | (a) Unión histórica (tarea 0.1): dos alertas V750 de PCC están **borradas** del consolidado actual (ver 6-8). (b) Antes del 2026-06-13 decide la tabla sola (A119): en la ventana, 85 de las 890 noches V375 dependen sólo del OCR anterior al 06-13 (estimación propia). (c) Filas OCR de Suomi NPP con la imagen de otra pasada hasta el 10-09. (d) Regla SN: unas 60 de las 890 noches V375 tienen todas sus alertas en 0,05 MW o menos (estimación, no la función oficial) | REBAJADA | SR | Reescribir con la unión histórica, los tramos A119, la regla SN y el OCR anterior al 06-13 informado aparte |
| 6-2 | 22-26 | 79,2 %; «can only depress the apparent recall» | La lógica es falsa (`docs\AUDIT_S128.md:262-276`). Que el 79,2 % sea «cota superior» es SOSPECHA: MIROVA vuelve a servir imágenes viejas con hora nueva (A106), lo que inflaría el denominador (`docs\audit_s146\FRENTE_D_CIERRES_CON_NUMERO.md:81`) | FALSA | C | «Missed alerts bias recall in either direction. Night coverage of the consolidated table is 99 to 100 % from March 2026; per-pass coverage of VIIRS against the image archive was 79.2 %.» |
| 6-3 | 26-29, 138-139, 153-157 | No hay negativos; la precisión no se puede calcular; no hay cota de la falsa alarma sin etiquetas negativas | Una sola premisa falsa (antes 6-3, 6-14 y la primera mitad de 6-16): 32.751 filas RUTINA en la ventana; tasas por régimen en el grave 1 (`experiments\_s142_linea_base\RESULTADOS.md`) | FALSA | C | «MIROVA's consolidated table also lists routine passes in which it detected nothing; a night with only such rows is a clean negative. In the period validated here, the published series appears on X % of clean-negative passes and Y % of clean-negative nights (by sensor and A119 interval).» Los números, del script |
| 6-4 | 29-34 | 98 filas diurnas V375 «excluded»; perderlas es «correct» | Ver grave 5: no se excluyen; el efecto en la recall es de 0,004 a 0,005 | FALSA | K | Excluirlas en el script y decirlo, o contarlas aparte como pérdida por diseño (D27) |
| 6-5 | 36-50 | Dos cadenas no supervisadas | A105 y Coppola 2026 ya incorporados | SIN CAMBIO | C | Ninguno |
| 6-6 | 56-64 | Recall por noche | El criterio cuenta alertas protegidas por pasada (439 en la unión de todas las fechas: V375 232, V750 149, MODIS 58; `docs\S151_CRITERIO_CLASE_MIROVA.md` §3). Ese 232 no es el 232 de nocturnas del grave 5 | FALTA | SR | Agregar la métrica por pasada protegida |
| 6-7 | 68-76 | Las dos definiciones «separate detection from labelling» | Ver grave 3 (por noche 98,2 % en negativos contra 0,976 con alerta) | FALSA | K | «The crater definition measures the presence of a cluster near the vent, which in MODIS occurs on nearly all clean-negative nights as well; it is not a measure of detection.» |
| 6-8 | 82-86 | 26.028 records; 890 / 246 / 82 noches; recall | 26.028 **se reproduce exacto** cortando cada volcán en el `ultimo_record` del paper (verificador). V750 da 244: faltan PCC V750 2026-02-26 05:24 (0,75 MW) y 2026-08-18 05:48 (0,64 MW), `ALERTA_TERMICA` **borradas** del consolidado actual, no reclasificadas (CSV de `83b9df8ff` contra los de hoy). Además la ventana cruza #535 (A104) | DESACTUALIZADA | K | Regenerar con la unión histórica y por tramo |
| 6-9 | 90-99 | MODIS: «not a detection failure»; «no per-record answer» | Ver grave 3 | FALSA | K | «With band 21 as the primary MIR channel (D21) the published series hardly separates alerts from clean negatives. With band 22 and without the integrated Test 1, as tested at Láscar from March to June 2026, it published 68 of 73 alert passes against 11 of 96 clean-negative passes (production: 8 of 73 and 1 of 96). This was measured at a single volcano.» |
| 6-10 | 105-111 | Banda de tolerancia | Falta decir qué magnitud se compara (A10, D32); reportar también con cenit ≤ 40° (D17 S141); A99 rebajada | REBAJADA | SR | Definir la magnitud comparada y agregar la columna con cenit ≤ 40° |
| 6-11 | 113-123 | Sub-integración por menos píxeles o por un anillo que se solapa | 1.14: el recorte pesa 47 % del déficit V375, el fondo 21 a 64 % según la bisagra, y el efecto depende del ángulo (`experiments\_s151_presupuesto_magnitud\README.md:10-20`, §3.1); el fondo es un anillo regional (D25); AUDIT_S134 vale sólo para V375 (`docs\AUDIT_S134.md:11-17`) | REBAJADA | SR | Reescribir con lo publicado, la selección, el fondo y el ángulo |
| 6-11b | 116 | «Isluga 0.580 (310)» | Hoy da 0,582 sobre 308 (`repro_0831`), por la misma pérdida de filas. Láscar V750 (178 a 177) no está en el texto | DESACTUALIZADA | K | Regenerar |
| 6-12 | 127-130 | Dos razones extremas | Idénticas en `repro_0831` | SIN CAMBIO | C | Ninguno |
| 6-13 | 136-137 | «30 of 193», «210 of 214» | Localizado: sale del `numbers.json` de `c421005c8` y `5a2bf24f2` (2026-09-07), anterior al recorte de la ventana de ground truth de `994c9f842` (#604), que lo bajó a 24/187 y 204/208. Los 6 de más eran noches posteriores al fin del CSV contadas como «sin alerta» | DESACTUALIZADA | K | Regenerar; si §6.5 se rehace con negativos limpios, la frase desaparece |
| 6-15 | 143-149 | La mayoría es real; los artefactos son minoría | A54 sin re-medir y con OCR anterior al 06-13 (`docs\audit_s150\meta\AUDITOR_F3_VARA_RETROACTIVA.md:249-259`) | REBAJADA | SR | Re-medir por tramo o quitar la cuantificación |
| 6-16 | 155-157 | «Suppressing ... would remove the added value» | No es falso como razonamiento: el objetivo cambió el 2026-10-13 (`docs\MISSION.md:20-28`, `:47-90`). La réplica calla donde MIROVA calla y el valor agregado va en `experimental` | DESACTUALIZADA | K | Reemplazar por el objetivo vigente |
| 6-17 | 82-99 | Régimen de los records | Ventana anterior a #535; V375 en negativos limpios: 60,7 % por pasada y 79,8 % por noche del 03-01 al 08-28, contra 86,5 % y 100 % del 09-01 al 09-17 (`experiments\_s142_linea_base\RESULTADOS.md`); 0 records con marca de régimen antes de #785 | FALTA | SR | Declarar el régimen y elegir ventana (decisión (a)) |
| 6-18 | 1-161 | Erupción de Chillán | 0 saturados; MIROVA 22,13 MW contra 10,36 MW nuestros el 2026-10-15 05:00 (V375) | FALTA | SR | Para §7, no para §6 |

---

## 3. `numbers.json`, `TABLAS.md` y `README.md`

Archivos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\paper\`.

### 3.1 Números de `numbers.json`

| clave | en el paper | hoy, misma ventana | clase | verif. |
|---|---|---|---|---|
| `generated_utc`, `git_head`, `ventana` | 2026-09-07 23:33 UTC, `83b9df8ff` | | DESACTUALIZADA | SR |
| `definiciones`, Noche ALERTA | «nocturna 03-09 UTC según el loader» | sin filtro horario (`scripts\paper_numbers.py:30` y `:194-205`) | FALSA | C |
| `definiciones`, Sin alerta | «A54 (95 % ...)» | A54 sin re-medir (`scripts\paper_numbers.py:43`) | REBAJADA | SR |
| `n_volcanes_configurados`, `n_tier_a` | 45, 11 | 45, 11 | SIN CAMBIO | SR |
| `tabla2`, `n_records_tier_a_ventana` | 26.028 | exacto, cortando en el `ultimo_record` del paper | SIN CAMBIO | C |
| `tabla3` | | idéntica | SIN CAMBIO | SR |
| `tabla4`, `agregados` MODIS y V375 | 82/10/80; 890/829/829 | idénticos | SIN CAMBIO | C |
| `tabla4`, `agregados` V750 | 246, 198, 0,805 | 244, 196, 0,803: dos alertas de PCC borradas del consolidado (6-8); además Isluga V375 310 a 308 y Láscar V750 178 a 177 | DESACTUALIZADA | K |
| `ventana_ground_truth.fin_csv_mirova` | 2026-08-31 | 2026-10-16 | DESACTUALIZADA | SR |
| `n_tests_collected` | 1.225 | 1.852 | DESACTUALIZADA | SR |

### 3.2 Otros ítems

| id | archivo:línea | qué | clase | verif. | cambio propuesto |
|---|---|---|---|---|---|
| T-1 | `TABLAS.md:37` | Pie de la Tabla 4: «"no alert" nights are NOT false positives (A54)» | REBAJADA | K | Distinguir una noche sin alerta de un negativo limpio |
| T-2 | `TABLAS.md:4` | Cabecera sin tramos A119 | DESACTUALIZADA | K | Regenerar con la unión histórica y el aviso A119 |
| T-3 | `TABLAS.md:32` | V750 «DiBella2024_k1.11e7» | SIN CAMBIO en el número | K | Rótulo: Di Bella es INGV Catania (A9); citar Campus 2022 |
| T-4 | `README.md:6-18` | Regla de números | FALTA | SR | Agregar al script la unión histórica, `calidad_referencia_mirova.avisar`, la regla SN, los negativos limpios, las protegidas y el régimen |
| T-5 | `README.md:26-27` | Estado de las secciones | DESACTUALIZADA | SR | Actualizar |

---

## 4. Lo que queda SIN VERIFICAR

- Las filas marcadas SR: 5-13, 5-15, 5-16, 5-18 a 5-21, 5-25 a 5-27 y 6-15 a 6-18. Además, del resto, todas las que
  llevan SR en la columna «verif.». No las revisó un tercero.
- Las citas a PDF que este informe propone (Coppola 2016a p. 187 y Fig. 11, Coppola 2014, Campus 2022 p. 16 y 17).
  Nadie las renderizó en esta revisión.
- Las estimaciones propias (85 noches sólo OCR anteriores al 06-13, unas 60 noches mínimas).
- Si el estimador TIR se calcula en memoria aunque no se publique.
- El conteo de módulos con cabecera FICHA.

## 5. Desacuerdos con el verificador

1. **El «100 % por noche» del régimen anterior a #535 (grave 1).** El verificador escribe que el proyecto tiene, para
   el tramo anterior, 62,1 % por pasada y 100 % por noche, y cita `docs\audit_s146\FRENTE_D_CIERRES_CON_NUMERO.md:80`.
   Esa línea dice «es por PASADA (87,1 % de 295); por noche es 100 % de 93». Es decir, ata el 100 % al 87,1 %, que es
   el tramo **posterior** a #571.
   La tabla fuente lo confirma (`experiments\_s142_linea_base\RESULTADOS.md`):
   - fila `VIIRS375 | despues_571`: 86,5 % de 325 por pasada y **100,0 % de 102** por noche;
   - fila `antes_535_misma_longitud`: 62,6 % de 358 y **80,7 % de 114**;
   - fila `contexto_marzo_a_535`: 60,7 % de 2.675 y **79,8 % de 1.104**.

   Apliqué su corrección de fondo (el 86,1 % no vale para la ventana del paper), pero con las cifras del tramo anterior
   que da la tabla: 79,8 % por noche, no 100 %.
2. **El 62,1 %.** El verificador lo toma de A104. La salida persistida hoy da 62,6 % de 358 para la misma ventana
   corta (él mismo lo anota, desde `FRENTE_B_CIERRES_CON_SCRIPT.md:72`). Para la ventana del paper uso la fila de marzo
   al 08-28 (60,7 %), que es la que cubre esos records.
