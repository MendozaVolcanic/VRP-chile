# 6. Validation against MIROVA

## 6.1 The reference universe and what it can support

We validate VRP Chile against the alerts MIROVA itself publishes in near-real time for
Chilean volcanoes. A companion scraper collects those alerts from two channels of the public
MIROVA web product: the consolidated table of latest detections, and an OCR pass over the
per-volcano images, which carry values that the consolidated table does not expose. A single
canonical loader merges and deduplicates both channels, and every figure reported below is
computed on that union.

<!-- src: docs/paper/numbers.json → definiciones ("CONS ∪ OCR (loader canónico A11)") ; CLAUDE.md:A11 -->

Both sides of the comparison are near-real-time products. Our records are built from LANCE
NRT granules when the Standard granule is not yet archived, and the MIROVA alerts we collect
are the ones its NRT chain published at the time. Comparing NRT against NRT is therefore the
operationally meaningful test, and it is also the only one available: MIROVA does not
distribute a reprocessed Chilean archive covering 2026, the period of this comparison.

<!-- src: docs/paper/sec5_methods.md §5.1 ; CLAUDE.md ("Refs MIROVA son NRT ... Comparar contra NRT es operacionalmente correcto") ; [6.1] Coppola et al. 2023, feart-11-1240107.pdf, p. 3 impresa (visor 3), col. izq., 3.er párrafo (archivo histórico descargable) -->

Three limits of this reference must be stated before any number is read. First, coverage is
partial: an internal audit measured the scraped ground truth at 79.2 % of the MIROVA passes
for the period examined, with the shortfall concentrated in VIIRS rather than MODIS, so an
alert MIROVA published but we did not capture is invisible to us and can only depress the
apparent recall, never inflate it. Second, the reference carries no negative labels. MIROVA
publishes detections; it does not publish an assertion that a given overpass contained
nothing. There is no set of confirmed empty nights against which a detection of ours could be
scored as wrong. Third, the reference contains alerts from daytime overpasses, which our
night-only chain cannot reproduce by design: by day, sunlight reflected by clouds and other
reflective surfaces raises the MIR radiance and hence the NTI without any hot source
(Coppola et al., 2014, p. 3410). Ninety-eight such rows are present in the VIIRS 375 m reference. They are excluded
from the comparison rather than counted as misses, because missing them is the correct
behaviour.

One asymmetry that is often assumed here does **not** apply. The visual supervision described
in the MIROVA literature was applied to the first curated archive (Coppola et al., 2023, p. 4);
the current global archive (v2.5) retains threshold-filtered detections with an automated
classification, and no additional quality control or manual screening was applied when it was
aggregated (Coppola et al., 2026, p. 7). The automatically posted time series are provided
'as they are' (Coppola et al., 2016a, p. 197).
<!-- S142 (A105): la supervisión visual de Coppola 2023 p. 4 es de la base v.1. [nuevo] Coppola et al. 2026, Scientific Data (Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf), p. 7 (visor 7, artículo en prensa), subsección "Data aggregation", 3.er párrafo: "No additional quality control or manual screening was applied during this aggregation step"; verificado en página renderizada en S142. Agregar la referencia a la bibliografía. --> The NRT chain monitors hundreds of volcanoes worldwide, with products posted within
1-4 h of each overpass (Coppola et al., 2016a, p. 196) and freely accessible on the web
(Coppola et al., 2020, p. 11); there is no capacity to review each
detection by hand, nor the local knowledge of each volcano that doing so would require. Both
sides of our comparison are therefore unsupervised, and any difference in recall is
algorithmic: something one system's rules capture and the other's do not. We state this
explicitly because the opposite assumption would set an artificial ceiling on how faithful an
open implementation can aspire to be, and would excuse differences that are in fact
investigable.

<!-- src: docs/MIROVA_DIVERGENCES.md:42-52 (D2, cobertura 79,2 % medida en AUDIT_S128 §4) ; docs/MIROVA_DIVERGENCES.md:72-95 (D3) ; regla durable del proyecto desde S21 (memoria: MIROVA NRT sin supervisión humana) ; A76 (artefacto solar diurno) ; conteo de 98 filas diurnas: experiments/_s135_probe_etapas/d19_regimen_vigente.py ; [6.2] Coppola et al. 2014, coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf, p. 3410 impresa (visor 10), §2.4.2 Daytime algorithm, 1.er párrafo ; [6.3] Coppola et al. 2023, feart-11-1240107.pdf, p. 4 impresa (visor 4), §2.5 ; [6.3] Coppola et al. 2016a, sp426.5.pdf, p. 197 impresa (visor 17), col. izq., §Metereological and volcanic clouds ; [6.3] Coppola et al. 2016a, sp426.5.pdf, p. 196 impresa (visor 16), col. der. ("completely autonomous") ; [6.3] Campus et al. 2022, campus2022_sensors_22_1713.pdf, p. 8 impresa (visor 8), §3.4 ; [6.3] Laiolo et al. 2026, s00445-025-01932-y.pdf, p. 4 impresa (visor 4) ; [6.3] Coppola 2025, 978-3-031-86841-2.pdf, p. 346 impresa (visor 350), §4.1, y p. 347 impresa (visor 351) ; [6.4] Campus et al. 2022, campus2022_sensors_22_1713.pdf, p. 7 impresa (visor 7) ; [6.4] Coppola et al. 2020, Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf, p. 3 impresa (visor 3) ("216 units") ; [6.4] Coppola et al. 2023, feart-11-1240107.pdf, p. 3 impresa (visor 3) (">200") ; [6.5] Coppola et al. 2016a, sp426.5.pdf, p. 196 impresa (visor 16), col. izq. ; [6.6] Coppola et al. 2020, Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf, p. 11 impresa (visor 11), col. izq., último párrafo ; [6.6] Coppola et al. 2023, feart-11-1240107.pdf, p. 3 impresa (visor 3) ("freely downloaded") ; [6.7] Coppola et al. 2023, feart-11-1240107.pdf, p. 4 impresa (visor 4), col. der., 1.er párrafo ; [6.7] Coppola 2025, 978-3-031-86841-2.pdf, p. 347 impresa (visor 351), col. izq. ; [6.8] conocimiento local de cada volcán: SIN LOCALIZAR (ver Notas para el editor) -->

## 6.2 What counts as a match

Recall is computed at the level of the alert night. A MIROVA alert night is a triple of
volcano, sensor family and UTC date for which at least one alert row exists in the merged
ground truth; sensor families are MODIS, VIIRS 750 m and VIIRS 375 m, kept separate because
each has its own detection limit. An alert night is recovered when at least one of our
records for the same volcano, the same sensor family and the same UTC date qualifies as
valid. Magnitude parity is computed at the finer level of the individual overpass: a record
and an alert row of the same sensor family are paired when their acquisition times differ by
no more than 20 minutes and both report a positive radiative power; where several candidates
exist, the closest in time is used.

<!-- src: docs/paper/numbers.json → definiciones ("Noche ALERTA", "Par por pasada") -->

We use two definitions of a valid record, and the distance between them is itself a result.
A *crater-valid* record has a primary cluster with positive radiative power below an
implausibility ceiling of 50,000 MW and a cluster centroid inside the volcano's inner radius.
A *dashboard-valid* record is a crater-valid record that is additionally labelled `summit`.
The two can disagree because the label is derived from the resolved single hotspot of the
scene while the published magnitude comes from the vent-anchored cluster: when a fire, a salt
flat or a warm valley floor holds the hottest pixel of a wide scene, the record is labelled
`far` even though its crater cluster is real. Reporting both figures separates detection
performance from labelling performance instead of averaging them into one number.

<!-- src: docs/paper/numbers.json → definiciones ("Record CRÁTER", "Record DASHBOARD") ; CLAUDE.md:A46, A81 -->

## 6.3 Recall by sensor

Over the window 2026-01-01 to 2026-09-07 the eleven Tier A volcanoes accumulated 26,028
records. Against them the merged ground truth holds 890 VIIRS 375 m alert nights, 246 VIIRS
750 m alert nights and 82 MODIS alert nights. Recall on the dashboard definition is 0.931
for VIIRS 375 m (829 of 890) and 0.805 for VIIRS 750 m (198 of 246); for these two sensor
families the crater and dashboard definitions coincide exactly, so labelling costs nothing.

<!-- src: docs/paper/numbers.json → ventana, n_records_tier_a_ventana, agregados -->

MODIS is the informative case. Its dashboard recall is 0.122 (10 of 82 alert nights) while
its crater recall is 0.976 (80 of 82). The gap is not a detection failure: on 80 of 82 nights
the pipeline places a valid cluster inside the crater radius. It is a labelling failure of
the kind described above, and it is severe at 1 km resolution because the MODIS scene is
large enough to contain a hotter non-volcanic pixel far from the vent on most nights. Láscar
shows the effect in isolation: 77 alert nights, crater recall 0.974, dashboard recall 0.117.
We report the discrepancy rather than resolving it by redefining the label, because the
underlying question (whether a 1 km pixel can separate a weak sub-pixel crater source from a
diffuse topographic gradient) was examined across several independent axes and found to have
no per-record answer at that resolution.

<!-- src: docs/paper/numbers.json → agregados, tabla4 (Lascar|MODIS) ; CLAUDE.md:A82, A83 -->

## 6.4 Magnitude parity

For each volcano and sensor family we report the median of the ratio between our radiative
power and MIROVA's over paired overpasses, with its interquartile range and the number of
pairs (Table 4). We adopt the operational tolerance band of 0.5 to 2.0 used throughout the
project. On VIIRS 375 m, 10 of the 11 volcanoes with at least one pair fall in band; on
VIIRS 750 m, 6 of 8; on MODIS only one volcano yields pairs at all, and it is in band.

<!-- src: docs/paper/numbers.json → agregados ; docs/paper/TABLAS.md Table 4 -->

The residual bias is one of under-integration, not of over-reporting. The best-sampled
VIIRS 375 m series sit at or slightly below unity (Puyehue-Cordón Caulle 1.029 over 258
pairs, Villarrica 0.945 over 38, Planchón-Peteroa 0.895 over 171), while the deficit
concentrates in Láscar 0.530 (316 pairs), Isluga 0.580 (310) and Lastarria 0.569 (218). A
ratio below one means we integrate less energy than MIROVA does over the same overpass:
either our cluster covers fewer pixels than the region MIROVA sums, or our local background
is estimated over an annulus that overlaps the region being measured, which suppresses the
excess. An internal audit tested and rejected the hypothesis that the deficit is caused by
our cluster sitting off-crater: on MIROVA-confirmed passes the cluster centroid is within a
few hundred metres of the vent, and the ratio is flat with distance to the crater. Chaitén at
1.312 over 62 pairs is the one well-sampled series above unity.

<!-- src: docs/paper/numbers.json → tabla4 ; docs/AUDIT_S134.md:11-20 -->

Two ratios sit far outside the band and both rest on very few pairs: Planchón-Peteroa on
VIIRS 750 m at 6.783 from 2 pairs, and Tupungatito on VIIRS 750 m at 0.090 from 3 pairs. We
report them for completeness and draw no inference from them; the corresponding 375 m series
for the same volcanoes, with 171 and 209 pairs, are 0.895 and 0.645.

<!-- src: docs/paper/numbers.json → tabla4 (PlanchonPeteroa|VIIRS750, Tupungatito|VIIRS750, ...|VIIRS375) -->

## 6.5 Why we report no precision against MIROVA

Many of our nights carry a valid detection with no corresponding MIROVA alert: at Láscar on
VIIRS 375 m, 30 of 193 dashboard nights; at Copahue, 210 of 214. It would be arithmetically
easy and scientifically wrong to call those false positives. Precision requires a reference
that labels negatives, and as stated in §6.1 this one does not.

<!-- src: docs/paper/numbers.json → tabla4 (Lascar|VIIRS375, Copahue|VIIRS375) ; docs/paper/numbers.json → definiciones ("Sin alerta ... NO se rotulan «falsos positivos»") -->

An internal audit classified that population and found it dominated by two categories that
are not detector errors. The first is thermal anomalies that are physically real but that
MIROVA does not publish: chronic fumarolic fields offset from the summit, sub-threshold lava
lakes, and the diffuse anomaly of an extended laccolith. The second is failures of the
cross-match itself: name variants, unparsed distances in the OCR channel, and coverage that
begins later for some targets than for others. Only a minority were artefacts of our own
detector, principally cold-cirrus responses and a ring background over glaciated terrain.

<!-- src: CLAUDE.md:A54 (AUDIT_S86, categorías a/b/c/d) ; [NUM: fracciones a/b/c/d de las noches sin alerta, AUDIT_S86, remedidas sobre la ventana de este manuscrito] -->

We therefore report recall and magnitude parity, and we do not report precision against
MIROVA, because on this reference precision would be a badly defined quantity. Suppressing
the unmatched population to improve a precision figure would also remove the detections that
constitute the added value of an independent implementation. The declared cost of this choice
is that the paper offers no upper bound on our own false-alarm rate; establishing one
requires a reference with negative labels, which for Chilean volcanoes means field or
ground-based corroboration rather than another satellite product.

<!-- src: CLAUDE.md:A54 ; docs/paper/sec5_methods.md §5.7 -->

---

## Localizadores: archivos PDF y convención de página

Todos los archivos están en `documentacion\`. "p. impresa" es el folio del artículo y "visor" la
página del PDF. Los localizadores de cada comentario `src` fueron verificados mirando la página
renderizada (`docs/audit_s141/lectura/VERIFICADOR_MANUSCRITO.md`); el número entre corchetes es la
fila de ese informe. Las fuentes de código, datos y auditorías del repo quedan como estaban. La
etiqueta "MIROVA database v1" de Coppola et al. 2023 viene del localizador: **sin segunda
verificación**.

| ref | paper (autor, año, revista) | archivo PDF | convención de página |
|---|---|---|---|
| Coppola et al., 2016a | Coppola et al. 2016a, *Geol. Soc. London Spec. Publ.* 426 | `sp426.5.pdf` | p. impresa = visor + 180. **Deducida, no leída**: el PDF no imprime folios; el rango 181-205 sale de la lista de referencias de Campus et al. 2024 (p. 6) |
| Coppola, 2025 | Coppola 2025, capítulo 11 de *Modern Volcano Monitoring* (Springer) | `978-3-031-86841-2.pdf` (libro completo) | p. impresa = visor − 4 (p. 346 = visor 350; p. 347 = visor 351). **`978-3-031-86841-2_9.pdf` NO es este capítulo** (es el de R. Campion sobre gases) |
| Coppola et al., 2014 | Coppola et al. 2014, *Int. J. Remote Sens.* 35(9) | `coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf` | p. impresa = visor + 3400 (visor 10 = p. 3410) |
| Coppola et al., 2020 | Coppola et al. 2020, *Front. Earth Sci.* 7:362 | `Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf` | p. impresa = visor |
| Coppola et al., 2023 | Coppola et al. 2023, *Front. Earth Sci.* (MIROVA database v1) | `feart-11-1240107.pdf` | p. impresa = visor |
| Campus et al., 2022 | Campus et al. 2022, *Sensors* 22:1713 | `campus2022_sensors_22_1713.pdf` | p. impresa = visor |
| Laiolo et al., 2026 | Laiolo et al. 2026, *Bull. Volcanol.* 88:11 | `s00445-025-01932-y.pdf` | p. impresa = visor |

---

## Notas para el editor

**Placeholders dejados (1):** un `[NUM:]` en §6.5, para las fracciones de la clasificación
de la población «noche nuestra sin alerta de MIROVA». Los porcentajes que circulan en el
proyecto (≈49 % fallas del cruce, ≈46 % anomalías reales, ≈5 % artefactos) vienen de
`AUDIT_S86`, que se midió en mayo sobre un corpus mucho más chico que el de hoy. Por la
regla A90 no los transcribí: son conteos absolutos sobre un corpus vivo. Si Nicolás quiere
la cifra en el paper, hay que agregar la clave a `scripts/paper_numbers.py` y remedirla
sobre la misma ventana que la Tabla 4. Mientras tanto el texto afirma sólo el orden de
magnitud cualitativo («dominada por dos categorías», «una minoría»), que sí se sostiene.

**Lo que corregí del esqueleto S72:**

1. El esqueleto proponía **precision y F1** como métricas centrales. No se pueden calcular
   contra este ground truth y las saqué; §6.5 explica por qué. Es el cambio de alcance más
   grande respecto del borrador.
2. Los números de S119 (VIIRS375 98,4 % / VIIRS750 84,5 % / MODIS-cráter 100 %; «9/11 en
   banda») están obsoletos y no coinciden con la Tabla 4 vigente. Usé sólo `numbers.json`.
3. El esqueleto ofrecía como ground truth el **OSF v2.5** además del NRT. Lo dejé fuera de
   §6: el OSF ya aparece en §5.4 como fuente de calibración de los coeficientes, y usarlo
   también como validación sería circular. Si el editor prefiere una validación histórica
   contra OSF, es una sección aparte, no ésta.

**Lo que no pude verificar:**

- El «79,2 % de cobertura» sale del encabezado actualizado de D2, que cita `AUDIT_S128` §4.
  No abrí ese audit ni recalculé la cobertura sobre la ventana de este manuscrito.
- La afirmación de que la brecha de magnitud no se explica por el cúmulo fuera del cráter
  sale del resumen ejecutivo de `AUDIT_S134`; no corrí el script.
- No cité D19 en el cuerpo. Es una divergencia abierta de gravedad alta que afecta
  justamente a records débiles publicados como *summit*, y §5.7 ya la declara. Decisión de
  alcance para Nicolás: si D19 se cierra antes del envío, §6.4 puede cambiar; si sigue
  abierta, conviene que §8 (Discussion) la retome explícitamente al hablar del sesgo de
  sub-integración, porque los dos fenómenos viven en la misma población de records débiles.

**Decisiones de alcance pendientes:**

- Las figuras previstas en el esqueleto (6, 7 y 8) no las produje. La Figura 8 (histograma
  de razones por record contra la banda) es la que más directamente respalda §6.4.
- La ventana de la Tabla 4 arranca el 2026-01-01, pero la serie de la mayoría de los Tier A
  parte el 2026-01-29 (Tabla 2). Conviene decidir si el manuscrito declara la ventana
  nominal o la efectiva por volcán.

**Localizadores de literatura (S141):**

- **Fila 6.8 (SIN LOCALIZAR): localizador pendiente de verificar en imagen.** «Nor the local
  knowledge of each volcano that doing so would require» no tiene fuente en los PDF revisados.
  Coppola et al. 2020, p. 11, habla del conocimiento de los observadores, no del operador de
  MIROVA. Queda como argumento propio, o hay que buscarle fuente.
- **Frases reemplazadas por los textos del verificador.** §6.1: el archivo no reprocesado se
  acota a 2026 (MIROVA sí publica archivos históricos, Coppola et al. 2023, p. 3). §6.1, tercer
  límite: el mecanismo diurno se ancla a Coppola et al. 2014, p. 3410, que describe la reflexión
  solar sobre nubes y otras superficies; «near solar noon» y «cold in the thermal band» no están en
  la literatura y se quitaron. Asimetría de supervisión: se ancla a Coppola et al. 2023, p. 4, y
  2016a, p. 197. «Every one to two hours» no aparece en ninguna fuente y pasa a «within 1-4 h of
  each overpass» (2016a, p. 196). «Free of charge» pasa a «freely accessible on the web» (Coppola
  et al. 2020, p. 11), que habla del acceso al sitio, no de un servicio gratuito.
- **Matices del localizador para la asimetría de supervisión que el texto no recoge.** Laiolo et
  al. 2026, p. 4, publica un dataset sin inspección visual, y Campus et al. 2022, p. 8, dice que en
  crisis los datos deben ser evaluados por un usuario final. Decidir si se mencionan.
- **La nota `src` del cierre de §6.1 sigue citando la memoria del agente** («regla durable del
  proyecto desde S21»). No es citable en un paper; la afirmación ya tiene respaldo en literatura
  (Coppola et al. 2016a, p. 197; 2023, p. 4) y la cita a la memoria puede salir.
- **§6 no tiene tabla de referencias.** Coppola et al. 2014, 2016a, 2020 y 2023 se citan ahora en
  el cuerpo; sus filas están en la tabla de §4 (con los metadatos pendientes de 2020 y 2023).
