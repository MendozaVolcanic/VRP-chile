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
distribute a reprocessed Chilean archive for the period we cover.

<!-- src: docs/paper/sec5_methods.md §5.1 ; CLAUDE.md ("Refs MIROVA son NRT ... Comparar contra NRT es operacionalmente correcto") -->

Three limits of this reference must be stated before any number is read. First, coverage is
partial: an internal audit measured the scraped ground truth at 79.2 % of the MIROVA passes
for the period examined, with the shortfall concentrated in VIIRS rather than MODIS, so an
alert MIROVA published but we did not capture is invisible to us and can only depress the
apparent recall, never inflate it. Second, the reference carries no negative labels. MIROVA
publishes detections; it does not publish an assertion that a given overpass contained
nothing. There is no set of confirmed empty nights against which a detection of ours could be
scored as wrong. Third, the reference contains alerts from daytime overpasses, which our
night-only chain cannot reproduce by design: near solar noon a cloud top reflects sunlight in
the mid-infrared while staying cold in the thermal band, and the index rises with nothing hot
beneath it. Ninety-eight such rows are present in the VIIRS 375 m reference. They are excluded
from the comparison rather than counted as misses, because missing them is the correct
behaviour.

One asymmetry that is often assumed here does **not** apply. The visual supervision described
in the MIROVA literature — cloud-affected data discarded a posteriori, residual false alerts
removed by hand — belongs to the curated archive prepared for publication, not to the
near-real-time product we compare against. The NRT chain monitors hundreds of volcanoes
worldwide, free of charge, every one to two hours; there is no capacity to review each
detection by hand, nor the local knowledge of each volcano that doing so would require. Both
sides of our comparison are therefore unsupervised, and any difference in recall is
algorithmic: something one system's rules capture and the other's do not. We state this
explicitly because the opposite assumption would set an artificial ceiling on how faithful an
open implementation can aspire to be, and would excuse differences that are in fact
investigable.

<!-- src: docs/MIROVA_DIVERGENCES.md:42-52 (D2, cobertura 79,2 % medida en AUDIT_S128 §4) ; docs/MIROVA_DIVERGENCES.md:72-95 (D3) ; regla durable del proyecto desde S21 (memoria: MIROVA NRT sin supervisión humana) ; A76 (artefacto solar diurno) ; conteo de 98 filas diurnas: experiments/_s135_probe_etapas/d19_regimen_vigente.py -->

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
underlying question — whether a 1 km pixel can separate a weak sub-pixel crater source from a
diffuse topographic gradient — was examined across several independent axes and found to have
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
VIIRS 375 m series sit at or slightly below unity — Puyehue-Cordón Caulle 1.029 over 258
pairs, Villarrica 0.945 over 38, Planchón-Peteroa 0.895 over 171 — while the deficit
concentrates in Láscar 0.530 (316 pairs), Isluga 0.580 (310) and Lastarria 0.569 (218). A
ratio below one means we integrate less energy than MIROVA does over the same overpass:
either our cluster covers fewer pixels than the region MIROVA sums, or our local background
is estimated over an annulus that overlaps the region being measured, which suppresses the
excess. An internal audit tested and rejected the hypothesis that the deficit is caused by
our cluster sitting off-crater — on MIROVA-confirmed passes the cluster centroid is within a
few hundred metres of the vent, and the ratio is flat with distance to the crater. Chaitén at
1.312 over 62 pairs is the one well-sampled series above unity.

<!-- src: docs/paper/numbers.json → tabla4 ; docs/AUDIT_S134.md:11-20 -->

Two ratios sit far outside the band and both rest on very few pairs: Planchón-Peteroa on
VIIRS 750 m at 6.783 from 2 pairs, and Tupungatito on VIIRS 750 m at 0.090 from 3 pairs. We
report them for completeness and draw no inference from them; the corresponding 375 m series
for the same volcanoes, with 171 and 209 pairs, are 0.895 and 0.645.

<!-- src: docs/paper/numbers.json → tabla4 (PlanchonPeteroa|VIIRS750, Tupungatito|VIIRS750, ...|VIIRS375) -->

## 6.5 Why we report no precision against MIROVA

Many of our nights carry a valid detection with no corresponding MIROVA alert — at Láscar on
VIIRS 375 m, 30 of 193 dashboard nights; at Copahue, 210 of 214. It would be arithmetically
easy and scientifically wrong to call those false positives. Precision requires a reference
that labels negatives, and as stated in §6.1 this one does not.

<!-- src: docs/paper/numbers.json → tabla4 (Lascar|VIIRS375, Copahue|VIIRS375) ; docs/paper/numbers.json → definiciones ("Sin alerta ... NO se rotulan «falsos positivos»") -->

An internal audit classified that population and found it dominated by two categories that
are not detector errors. The first is thermal anomalies that are physically real but that
MIROVA does not publish: chronic fumarolic fields offset from the summit, sub-threshold lava
lakes, and the diffuse anomaly of an extended laccolith. The second is failures of the
cross-match itself — name variants, unparsed distances in the OCR channel, and coverage that
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

- Las figuras previstas en el esqueleto (6, 7 y 8) no las produje. La Figura 8 —histograma
  de razones por record contra la banda— es la que más directamente respalda §6.4.
- La ventana de la Tabla 4 arranca el 2026-01-01, pero la serie de la mayoría de los Tier A
  parte el 2026-01-29 (Tabla 2). Conviene decidir si el manuscrito declara la ventana
  nominal o la efectiva por volcán.
