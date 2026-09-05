# S134 · F4 — VERIFICACIÓN con contexto limpio

Verificador independiente. Releí los PDF, reimplementé f(θ) desde cero sin importar la del
auditor, volví a correr los dos scripts y agregué sensibilidades. **Read-only**: no toqué
`pipeline/`, `data/`, perfiles ni git. Lo mío vive en `experiments/_s134_audit/f4/verif_f4.py`
y `verif_f4b.py`; los números salen de `verif_resultados.json` y `verif_resultados_b.json`.

Los números que cito son de MI corrida, no transcritos del informe.

---

## Hallazgo 1 · La derivación de f(θ) = min(1, 32/(k·r))

**CONFIRMADO · gravedad 2**

Las cinco citas son verbatim y están donde el auditor dice:

| id | verificación mía |
|---|---|
| G1 | `pdftotext … VIIRS_Geolocation_ATBD_2014.pdf` línea 542/544: I-band `0.371 x 0.388` en nadir, `0.80 x 0.789` en fin de barrido |
| G2+G3 | línea 3891, verbatim: la extensión del barrido crece *"from 11.87 kilometers at nadir to 25.60 kilometers at a scan angle of 56.063 degrees"* … *"maximum overlap over 50 percent at 56.063 degrees. This overlap is unaffected by the VIIRS pixel aggregation strategy which applies only in the cross-track direction"* |
| G4 | línea 800: fronteras 3:1→2:1 en 31.589°, 2:1→1:1 en 44.680° |
| G5 | `JPSS_ATBD_VIIRS_Imagery_RevE.pdf` línea 459, verbatim: *"deleting 4 of the 32 detectors … for the middle (Aggregate 2) part of the scan and 8 of the 32 detectors for the edge (No aggregation) part"* |

**Corroboración que el auditor no usó** y que refuerza G2: la misma línea 3891 dice que el FOV
recoge *"sixteen moderate resolution band pixels"* por barrido, y la Tabla 2.2-1 da M-band
along-track 0,742 km en nadir y 1,60 km en el borde → 16 × 0,742 = 11,87 y 16 × 1,60 = 25,60.
La razón 2,1567 aparece por dos caminos independientes dentro del ATBD.

**Aritmética**: reimplementé f sin mirar su código. `2_max_dif_f_auditor_vs_mia = 0.0` sobre los
643 pares. f(nadir) = 1,000 y f(cenital 70°) = **0,61823**; la tabla de siete filas del informe
se reproduce entera. H calibrada 801,638 km, r(EOS) = 2,1566976 contra el objetivo 2,1566976.

**Los supuestos que esconde, y qué pasaría si cada uno fuera falso** (`1_tension_S4_19grados`,
`1_modelo_alternativo_r_lineal_en_theta`, `C_sensibilidad_S4`):

1. *Solape sólo along-track.* Lo autoriza G3 explícitamente. Si fuera falso, faltaría descontar
   también en el eje de barrido → f sería aún menor y el borde caería por debajo de 1,0.
2. *El solape empieza en θ > 0 (tensión S4, la que el auditor declara).* La cuantifiqué: mi
   modelo pone **1 fila entera de solape ya en θ = 13,31°** (cenital 15,0°) y **2,10 filas en
   θ = 19°**, justo donde el ATBD §2.2.2 (línea 690) dice que el solape *empieza* — y agrega que
   *"the scan gap at nadir is nominally zero"*. O sea que la tensión es real y vale ~2,1 filas.
   Absorbiéndola (f' = (32 + 2,10)/(k·r)): borde **1,007 → 1,073**, nadir 0,940 → 0,958, cola
   13,8 % → 16,5 %. **El veredicto no cambia** (C1 sigue pasando, C4 sigue fallando), pero se come
   casi todo el margen del borde.
3. *r(θ) = razón de distancia oblicua.* Es el supuesto con más grados de libertad y el informe no
   lo somete a sensibilidad. Un modelo alternativo igual de defendible (r lineal en θ entre 0,371
   y 0,80 km) da f(cenital 20°) = **0,733** en vez de 0,947 — reprobaría el propio control
   negativo. Los dos bins juzgados casi no lo notan (nadir está clavado por el `min(1,·)`, el
   borde por la razón del ATBD), pero **los bins del medio sí**: ahí es donde la ley intermedia
   se rompe (ver hallazgo propio P2).
4. *Altura orbital.* Irrelevante, como dice el informe: 1,007 vs 1,010 con H = 829 km.

**Nota menor P7**: el ATBD se contradice consigo mismo — §2.2.2 (línea 690) dice 11,9 → **25,9**
km y §3.4.2.1 (línea 3891) dice 11,87 → **25,60**. Con 25,9 la razón sería 2,176 y f(EOS) 0,613.
Despreciable, pero el informe presenta el 25,60 como si el documento fuera unívoco.

---

## Hallazgo 2 · La tabla de las tres leyes

**CONFIRMADO · gravedad 1** (la medición; el veredicto que se apoya en ella es otra cosa, ver P1/P2)

`python experiments/_s134_audit/f4/f4_solape_ley_intermedia.py` reproduce **exacto**: control
0,879 / 0,619 / cola 4,2 %; geoloc 0,958 / 1,360 / 20,1 %; geoloc×f 0,940 / 1,007 / 13,8 %;
corona 0,619→1,303; n = 111 y 210; 643 pares; ventana 2026-04-01 → 2026-05-31. El control
positivo contra los siete números de S133 da `pasa = true` y el negativo mueve el nadir 1,88 %.

Lo que revisé de la mecánica, con el número:

- **Buckets de sensor** (trampa A48): `VIIRS_NOAA20 / SNPP / NOAA21` sin sufijo → `v375`, con
  `_750` → `v750`; la ground truth mapea `VIIRS375 → v375`. Correcto.
- **Campo de magnitud**: usa `f5_core_vrp_mw` para VIIRS375, que es lo que manda el matiz S132 de
  A10. Y verifiqué el fallback: **643/643 pares usan `f5_core_vrp_mw`; el fallback a
  `primary_cluster.vrp_mw` aporta 0,0 % tanto dentro como fuera de la cola** (`4_fallback_A46`).
  El informe lo declara como si cubriera parte del conjunto pareado; en los pares no cubre nada.
  Esto además **elimina** el fallback como explicación alternativa de la cola.
- **Pareo por pasada (±20 min)**: acá sí hay algo. **309 de los 643 pares comparten clave
  (volcán, valor MIROVA, día), con reúso máximo 3**: una misma ALERTA puede parearse con más de
  un granule nuestro. Reconstruí un pareo **1-a-1 codicioso** (cada ALERTA se consume una sola
  vez, la más cercana en tiempo): quedan 517 pares y da nadir **0,940**, borde **1,067**, cola
  **14,7 %**. **El veredicto es robusto al esquema de pareo.**
- **Cortes de cenital**: `_bin_de` sobre `sensor_zenith_deg`; el bin 50+ va de 50,0° a 70,4°
  (mediana 59,1°) y NO está clavado en el valor de EOS: su f mediana es **0,777**, no 0,618, con
  196/210 registros en la zona k = 24. O sea que el 1,007 del borde sí depende del modelo de r
  (supuesto 3), aunque menos que los bins del medio.
- **Ground truth**: el script lee `latest_consolidado.csv` (el archivo **vivo**, 35.875 filas),
  no el snapshot congelado (35.036) que dice el encargo. Lo medí: **con el snapshot dan los mismos
  643 pares y las mismas cinco medianas** (`B_gt_vivo_vs_snapshot`). Impacto hoy = cero; riesgo
  A90 de reproducibilidad = real (ver P5).

---

## Hallazgo 3 · El veredicto (C1 pasa, C4 no pasa → no adoptar)

**PARCIALMENTE REFUTADO — el poste se movió por omisión · gravedad 3**

C1 y C4 están aplicados exactamente como el script los congela, y no encontré ningún ajuste
posterior. **Pero el criterio pre-registrado de S133 tiene CUATRO patas, no dos**:
`docs/s133/AB_AREA_VEREDICTO_CHUNK1.md:28-35` las lista, y su propio encabezado dice *"Ningún
brazo pasa **los cuatro** criterios"*:

| | criterio | control (S133) | mi corrida |
|---|---|---|---|
| C1 | ambos bins en 0,9-1,1 | ❌ | intermedia ✅ |
| **C2** | **≥ 6 de 8 volcanes en banda** | **❌ 3/8** | **intermedia ❌ 1/8** |
| C3 | 0 noches de MIROVA perdidas | — | no computable off-line (A18) |
| C4 | cola > 2 en ≤ 10 % | ✅ 4,2 % | intermedia ❌ 13,8 % |

Mi implementación de C2 **reproduce los dos valores que S133 publicó** (control 3/8, área 1/8),
así que el instrumento está calibrado. La ley intermedia da **1/8** evaluable en banda (Lastarria
1,069; Villarrica 1,050 pero n = 13 < 15): **igual de mal que geoloc y peor que el control (3/8)**.

El informe dice *"el mismo de S132/S133"* y muestra una tabla de dos filas. C2 es **computable
con los mismos pares** —de hecho sus medianas por volcán ya están en `cola_composicion.json`— y
no se evaluó. C3 sí es legítimamente incomputable off-line, pero tampoco se nombra como ausente.

La **conclusión final ("no adoptar") queda intacta y de hecho reforzada**: falla 2 de 3 criterios
computables, no 1 de 2. Lo que queda mal calibrado es la *distancia* a la adopción que el lector
se lleva.

---

## Hallazgo 4 · H1, la cola es el régimen sub-MW

**PLAUSIBLE en su núcleo, SOBRE-AFIRMADO en su título · gravedad 3**

Los números se reproducen exactos: 89 pares en cola; **17,1 % en los 514 pares con MIROVA
< 0,5 MW, 0,8 % en los 118 de 0,5-2 MW, 0 % en los 11 de 2-10 MW**; Chaitén 33,3 % (n = 27) y PCC
28,3 % (n = 99). Que la cola viva casi entera en el régimen sub-MW es **CONFIRMADO**.

Lo que **no** se sostiene es el título *"no es el gradiente cenital"*. Dos mediciones mías:

1. **La cola responde a la ley de área, dentro del mismo estrato.** En los mismos 514 pares
   sub-MW: control **5,3 %** → geoloc **24,5 %** → intermedia **17,1 %** (`4_cola_por_tramo_*`).
   Si la cola fuera una propiedad de la ground truth, no se cuadruplicaría al cambiar el área.
2. **Dentro del estrato sub-MW, la cola se duplica en el borde del barrido**
   (`D_cola_bin_x_tramo`): 50+ **28,0 %** (51/182), 0-15 **14,3 %**, 25-35 16,7 %, 35-50 8,5 %.
   Y en los pares ≥ 0,5 MW la cola es 0 % en **todos** los bins. O sea que el eje cenital está
   dentro de la cola, no fuera.

Lo que pasa de verdad es más fino y más interesante: **f corrige la mediana del borde pero casi no
toca su dispersión**. IQR relativo del bin 50+: control 1,462 → intermedia 1,400
(`D_dispersion_por_bin*`). La mediana se movió 0,619 → 1,007; el ancho, nada.

**Explicación alternativa que el auditor no consideró y que sí encontré**: MIROVA publica con
**dos decimales**. Los 643 valores pareados tienen 2 decimales exactos, el mínimo es **0,02**, la
mediana **0,21**, y bajo 0,5 MW hay sólo **46 valores distintos** repartidos en 514 pares (los más
frecuentes: 0,09 ×30, 0,07 ×29, 0,06 ×23). En 0,02-0,03 MW la sola cuantización del denominador
vale ±17-25 %. No fabrica una razón de 3 por sí sola, pero es un amplificador real del cociente
que no aparece en el informe. (No es un "piso" que trunque: el mínimo 0,02 no se acumula.)

**Consecuencia práctica**: la recomendación 7.3 del informe —*revisar C4 porque "está midiendo el
régimen sub-MW y no la ley de área"*— se apoya en la mitad de la afirmación que mis datos
contradicen. C4 mide las dos cosas a la vez. Si se toca C4, que sea con ese matiz sobre la mesa.

---

## Hallazgo 5 · H2 (pozo en 35-50°) y H4 (el área no se persiste)

**H2 CONFIRMADO · gravedad 2.** Los cinco bins salen 0,940 · 0,986 · 0,896 · **0,786** · 1,007, no
monótonos, y se mantienen con el pareo 1-a-1 (0,940 · 0,986 · 0,891 · 0,785 · 1,067). La
atribución al borrado bow-tie es consistente con los conteos: el bin 35-50 está 147/155 en la zona
k = 28 y el 50+ 196/210 en k = 24. Pero el informe le da la lectura benigna ("el criterio sólo
juzga los extremos, no cambia el veredicto"); la lectura completa es P2, abajo.

**H4 CONFIRMADO · gravedad 1.** Los 452 registros de
`~/ab_area/s133area-_s133_area_geoloc-Lascar/Lascar.json` tienen 67 claves distintas y **ninguna**
de área de píxel (`6_H4_claves`: sólo `anomaly_pixels`, `n_anomalous_pixels`, `n_test1_pixels`,
`n_vent_pixels`, `diag_n_first_pass_pixels`, `discarded_*`). El productor es
`pipeline/scan_geometry.py:317` (`resolve_viirs_pixel_areas`; el informe cita `:319`, que es la
tercera línea de la misma firma).

---

# Mis hallazgos propios

### P1 · Se evaluaron 2 de los 4 criterios pre-registrados, y el omitido falla peor
**gravedad 3.** Ya desarrollado en el hallazgo 3. C2 = 1/8 para la ley intermedia contra 3/8 del
control. Comando: `python experiments/_s134_audit/f4/verif_f4.py` → `3_C2_*`.

### P2 · C1 juzga 2 de los 5 bins, y son justo los 2 donde la ley nueva gana
**gravedad 3.** Con las medianas por bin de la propia corrida:

| bin | geoloc solo | geoloc × f | ¿f mejora? |
|---|---:|---:|---|
| 0-15 | 0,958 ✅ | 0,940 ✅ | apenas peor |
| 15-25 | 1,043 ✅ | 0,986 ✅ | mejor |
| 25-35 | 1,033 ✅ | **0,896** ❌ | **la saca de banda** |
| 35-50 | 0,925 ✅ | **0,786** ❌ | **la saca de banda** |
| 50+ | **1,360** ❌ | 1,007 ✅ | la mete en banda |

**Bins en banda: geoloc 4/5, ley intermedia 3/5.** La afirmación del informe —*"la ley intermedia
es claramente mejor que las dos anteriores en el centro de la distribución"*— es **falsa para el
centro**: en 25-35 y 35-50, geoloc sin f está en banda y con f no. La ley intermedia gana en el
borde y pierde en el medio; C1, al mirar sólo los extremos, no puede ver el intercambio.
Esto reordena la lectura de H2: el pozo de 0,786 no es un detalle que el criterio no juzga, es
la cara visible de que f **sobre-descuenta en la zona intermedia** — coherente con que ahí es
donde el modelo de r tiene todos sus grados de libertad (supuesto 3 del hallazgo 1).

### P3 · La cola sí responde a la ley de área y al bin cenital
**gravedad 3.** Desarrollado en el hallazgo 4 (5,3 → 24,5 → 17,1 % dentro del estrato sub-MW;
28,0 % en 50+ contra 14,3 % en 0-15).

### P4 · La cuantización a 2 decimales de MIROVA amplifica el cociente en el régimen sub-MW
**gravedad 2.** 46 valores distintos bajo 0,5 MW para 514 pares; mínimo 0,02.

### P5 · El instrumento lee la ground truth VIVA, no el snapshot
**gravedad 1.** `f4_solape_ley_intermedia.py:146` apunta a `latest_consolidado.csv`, que el cron
de sincronización reescribe cada hora. Hoy da idéntico al snapshot (mismo 643, mismas medianas),
así que **no invalida nada**; pero los siete números del control positivo quedan anclados a un
archivo que cambia solo, que es exactamente el modo de falla silenciosa de A90. Para que el
control positivo siga siendo un control, debería apuntar al snapshot congelado.

### P6 · El fallback A46 no participa: el informe lo declara como si cubriera parte
**gravedad 1.** 0,0 % de los 643 pares. Es una sobre-declaración inocua, pero le quita al lector
una preocupación que no existe y le deja la impresión de que sí.

### P7 · El propio ATBD da dos pares de números para la franja
**gravedad 1.** 11,9/25,9 (§2.2.2) contra 11,87/25,60 (§3.4.2.1).

---

## NO VERIFICADO (lo digo sin vergüenza)

1. **Que f aplicado por píxel dentro del pipeline dé lo mismo que el factor por record** (S1 del
   informe). Requiere granules. El informe ya lo declara.
2. **Sospecha propia, de lectura de código, sin número**: `pixel_areas_from_geolocation`
   (`pipeline/scan_geometry.py:248-311`) mide el paso along-track por **diferencia centrada en el
   índice de fila del arreglo**. En la frontera entre dos barridos, la fila 31 del barrido *n* y la
   fila 0 del barrido *n+1* son **contiguas en el arreglo pero solapadas en el terreno**: ahí la
   diferencia centrada no mide el tamaño del píxel, mide el salto del bow-tie. Dos de cada 32 filas
   del brazo `geoloc` podrían llevar un área sistemáticamente equivocada, y no en la dirección que f
   corrige. Tampoco sé si los píxeles borrados por bow-tie llegan como *fill* y arrastran NaN a sus
   vecinos (`resolve_viirs_pixel_areas` los devuelve al área modelada, en silencio). Todo esto
   necesita un granule; con los JSON no se puede, precisamente por H4.
3. **C3** (noches de MIROVA perdidas) para la ley intermedia. Es incomputable con filtrado
   off-line: haría falta reproceso real (A18).

---

## VERIFICADO LIMPIO

| qué | cómo lo confirmé |
|---|---|
| Los 7 números del control positivo y los 3 de la ley intermedia | corrida propia de `f4_solape_ley_intermedia.py`, exactos a 3 decimales |
| f(θ) del auditor contra una reimplementación independiente | `2_max_dif_f_auditor_vs_mia = 0.0` sobre 643 pares |
| Las 5 citas del ATBD (G1-G5) | `pdftotext` + `grep`, verbatim, líneas 542/544/690/800/3891 y 459 |
| Coherencia interna del ATBD por un segundo camino | 16 píxeles M × 0,742 km = 11,87; × 1,60 km = 25,60 (línea 3891 + Tabla 2.2-1) |
| Buckets de sensor VIIRS (trampa A48) | `A_bucket_de_cada_sensor`: sin sufijo → v375, `_750` → v750 |
| Campo de magnitud correcto para VIIRS375 (matiz S132 de A10) | `f5_core_vrp_mw` en 643/643 pares |
| Robustez al esquema de pareo | pareo 1-a-1: 517 pares, 0,940 / 1,067, cola 14,7 % — mismo veredicto |
| Robustez a la fuente de ground truth | snapshot congelado da los mismos 643 pares y las mismas 5 medianas |
| Robustez a la tensión S4 (los "19 grados") | absorbiendo 2,10 filas: 0,958 / 1,073, cola 16,5 % — mismo veredicto |
| Robustez a la altura orbital | 1,007 vs 1,010 |
| Que el mecanismo del doble conteo sea posible en NUESTRO código | `cluster_hotspots` usa `ndi_label` sobre el arreglo 2-D (`pipeline/clustering.py:98`), y las filas de dos barridos consecutivos SON vecinas en el arreglo → un foco del borde puede entrar dos veces al mismo cúmulo. El mecanismo es coherente con el código, no sólo con el ATBD |
| Que nada de esto toque producción hoy | `VRP_PROFILE=mirova_equivalent` → `ENABLE_GEOLOCATED_PIXEL_AREA = False`, `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS = True` |
| Que el auditor no modificó el repositorio | `git status --porcelain`: sólo `docs/INDEX.md` modificado y `experiments/_s134_audit/`, `docs/AUDIT_S134.md`, `tests/test_guard_regla_c_s134.py` sin seguimiento |
