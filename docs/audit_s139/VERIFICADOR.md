# S139: informe del verificador con contexto limpio

Fecha del servidor al cerrar: 2026-09-13 20:09 UTC (`gh api -i`, header `Date`). HEAD local `b16bb8fab`.
Sólo lectura. Archivos escritos: este informe y `experiments/_s139_audit/verificador/` (4 scripts propios,
sus salidas `v1_salida.txt` a `v4_salida.txt`, y `rerun_*.txt` con la salida de re-correr los scripts de los
seis ejes). `git status --short` al final: sólo `docs/audit_s139/` y `experiments/_s139_audit/` sin trackear;
ningún archivo trackeado quedó modificado, no hubo que restaurar nada.

## 0. Resumen para quien decide

1. **El número dominante de la brecha tiene un dueño que ningún eje nombró.** Los ejes 2, 4 y 6 miden que
   VIIRS 375 publica en 4 de cada 5 noches sin alerta. Medido por pasada contra el granule exacto que
   MIROVA listó con VRP 0 (el negativo más limpio que existe), publicamos en 2.062 de 3.245 (63,5 %), y
   **1.356 de esas 2.062 publicaciones (66 %) son el objeto D19**: un cúmulo de un píxel del Test 1,
   publicado por el ancla como `test1_roi`, con BT del píxel **1,56 K bajo el fondo** (mediana) y 0,050 MW.
   En pasadas con ALERTA ese objeto es sólo 171 de 960. S135 ya reprocesó el brazo que lo apaga
   (`keep_peak` OFF, brazo B): quitó el 100 % del artefacto sin perder ninguna noche confirmada en 6
   volcanes, y falló su criterio de paridad por 0,016. Ninguno de los tres planes pone esa palanca primero.
2. **Cada sensor sobre-publica un objeto distinto**: VIIRS 375 el píxel D19 de 0,05 MW; VIIRS 750 cúmulos de
   0,30 MW sin D19 (3 %); MODIS campos de 2 MW con p90 exactamente 5,000 MW, el tope del path D. Un plan
   con las mismas palancas para los tres sensores ataca el mecanismo equivocado en dos de ellos.
3. **RUTINA sí sirve como negativo de paridad por pasada**, aunque no sea "cielo despejado sin calor". La
   sobre-publicación no sale de nubes ni del borde del barrido: es mayor a nadir (72 %) que a cenital
   de 60 o más (52 %). La tesis del eje 1 ("un banco con RUTINA mediría la nubosidad") no se sostiene;
   la parte factual (RUTINA = "MIROVA procesó y dio 0") sí.
4. **Los tres números de línea base se reconcilian**: 82 % (eje 2) es por sensor; 90 % (ejes 2 y 4) es
   cualquier sensor, y la diferencia entre 1.384 y 1.557 negativos son las noches con FALSO_POSITIVO; el
   47,7 % y la "precisión 26,3 %" del eje 6 mezclan los tres sensores y no son defendibles.
5. **La paridad de magnitud VIIRS 375 por pasada es 0,55 a 0,61**; el 0,689 del libro de cuentas es máximo
   por noche a ambos lados, que infla ~0,1 a 0,2. No es diferencia de año ni de referencia.
6. **"B22 ya se corrió y dio NO ADOPTAR" es cierto y engañoso**: el criterio que falló era de invariancia
   (razón ON/OFF en 0,95 a 1,05), no de paridad; la paridad nunca se midió (n = 2).

## 1. Método del verificador y controles

| script | qué mide | P1 (¿vería el defecto?) | P2 (¿instrumento muerto?) / control |
|---|---|---|---|
| `v1_negativo_por_pasada.py` | publicación por pasada contra la fila CONS del mismo granule (±120 s); por clase, volcán, cenital; magnitud; composición | publicar todo daría 1 en negativos; nada, 0 en positivos | predicado portado **validado 7.377/7.377 noches-sensor** contra el node del eje 2; reloj +3 h da **0 pareos** en los 3 sensores; SIN_FILA aparte |
| `v2_ratio_0551_vs_0689.py` | ratio nuestro/MIROVA cambiando un factor a la vez | la variante que replica el libro debe dar 0,689 y la del eje 6 0,551 | replica: 0,693 (n 858; el corpus creció) y 0,551 (n 1.507) |
| `v3_keep_peak_y_desfase.py` | fracción del objeto D19 en lo publicado; proxy sin él; desfase de reloj CONS | si D19 no importara, igual fracción en neg y pos | 0 records sin `final_hotspot_source` (el marcador existe en todos) |
| `v4_d19_fisica.py` | BT del píxel D19 menos `t_bg_k` | calor real daría BT − fondo > 0 casi siempre | 0 records SIN DATO de píxeles o fondo |

Ventana de v1, v3, v4: 2026-01-10 a 2026-09-07 (fin del OCR), pasadas nocturnas, 11 Tier A. v2: 2026 completo y
2025-02-15 a 2025-11-30. **Advertencia A18 sobre v3**: el "proxy sin D19" filtra records ya seleccionados; no
predice un reproceso con `keep_peak` OFF. La evidencia de efecto es el reproceso de S135, no el proxy.

Re-corrí los 9 scripts de los ejes 2, 3, 4 y 6 y `medir_ocr.py` del eje 1 (`rerun_index.txt`: todos exit 0).
Los de imagen del eje 1 se re-corrieron contra `latest_consolidado.csv`.

## 2. Veredicto por afirmación

### A1. Eje 1 H101: RUTINA no es un negativo confiable
- **Parte factual, CONFIRMADA**: RUTINA es `vrp <= 0` (`scraper.py:153-154`, leído por el eje 1 en el remoto; no
  lo releí) y el lado tabla de la muestra se reproduce: `imagen_vs_tabla_ampliado.py latest_consolidado.csv`
  da control 8/8 ausentes, 22 ausentes, 48 NaN presentes todos RUTINA.
- **La evidencia es más débil de lo que parece**: de 80 adquisiciones transcritas en el script ampliado, 70
  son NaN y **sólo 38 son nocturnas** (UTC ≤ 11, conteo por regex sobre el script). Los ejemplos de nube y
  borde que cita (Isluga 18:48 y 19:24) son **pasadas diurnas**, que ningún banco nocturno usa. Las imágenes
  no se guardaron: la clasificación "nube / borde / despejado" no es reproducible.
- **La conclusión general NO se sostiene** (medido en v1): (a) en pasadas pareadas RUTINA en noches sin ninguna
  alerta ni FP, VIIRS 375 publica 63,5 %, así que la sobre-publicación no depende de los huecos de cobertura
  de la noche; (b) por cenital del sensor publica 501/693 (72 %) bajo 30 grados y 590/1.131 (52 %) sobre 60,
  lo contrario de lo que haría el borde del barrido; (c) una pasada nublada que MIROVA da 0 tampoco nos deja
  ver el cráter, así que la nube agrega negativos fáciles y **subestima** nuestra tasa, no la infla.
- Veredicto: RUTINA por pasada es un negativo **de paridad** válido (es literalmente la salida de MIROVA para
  ese granule); no es verdad de "no hay calor". GRAVEDAD de la sobre-lectura: 3 (llevaría a descartar el único negativo que hay).

### A2. Mirova-v1 local "102.948 commits atrás"
CONFIRMADO. Se obtuvo como `rev-list --count origin/main` (ref local, 152.808) menos `HEAD` (49.860).
`gh api repos/MendozaVolcanic/Mirova-v1/compare/<HEAD local>...main` da hoy `ahead_by 102953` (5 commits más
desde que el eje 1 midió). HEAD local: 2026-03-28.

### A3. Consolidado omite gránulos; 539 alertas sólo OCR; sync no trae OCR; 97 positivos V375
- 539 = 846 ALERTA_TERMICA_OCR menos 307 con llave exacta en CONS: CONFIRMADO (`rerun_eje1_medir_ocr.txt`:67-68).
- El dashboard no usa OCR: CONFIRMADO. `.github/workflows/sync-mirova-csv.yml:51` baja sólo
  `registro_vrp_consolidado.csv`; `:108-110` reconstruye con `--source latest_consolidado.csv`.
- 97 noches positivas V375: CONFIRMADO (`rerun_eje2_banco_noches.py.txt`: `cons` 745/757 contra `cons_ocr` 840/854).
  Que sean alertas genuinas y no artefactos del OCR: SOSPECHA (A76).
- Tasa de omisión: el eje 1 da 27/120 con muestra de 2 días. Por pasada (v3) **46 % de nuestras pasadas
  VIIRS 375 nocturnas no tienen fila CONS a ±2 min** (5.596/10.398 pareadas). Parte puede ser nuestra
  (granules adyacentes que cubren el mismo volcán en una pasada: tenemos ~3,9 pasadas V375 por volcán-noche
  y MIROVA lista ~2): SOSPECHA, no separado.

### A4. Eje 1 H106: `rebuild_mirova_from_consolidado.py:76` descarta alertas grandes
CONFIRMADO en código (`VALID_CLASSES = {"Muy Bajo", "Bajo"}`, rechazo en `:86-89`). Matiz que el eje 1 no dice:
el comentario `:64-75` declara el conjunto **cerrado a propósito** ("do NOT speculatively add Moderado/Alto").
Es una decisión deliberada de S8, no un olvido, y justo por eso no se va a arreglar sola. Latente hoy (0 filas
afectadas según el eje 1, no re-medido). GRAVEDAD 3.

### A5. Reconciliación de las tres líneas base
| fuente | unidad | negativo | predicado | resultado |
|---|---|---|---|---|
| eje 2 | noche UTC por **sensor** | sólo RUTINA en ese sensor, sin FP ni ALERTA; exige cobertura; CONS+OCR | dashboard ejecutado con node | V375 1.145/1.393 (82,2 %), V750 1.205/2.188 (55,1 %), MODIS 428/2.347 (18,2 %), recall MODIS 10/75 |
| eje 2 | noche de volcán, cualquier sensor | idem | idem | recall 874/877, negativos 1.252/1.384 (90,5 %) |
| eje 2, `sin_alerta` | noche de volcán | RUTINA **o FP**, sin ALERTA | idem | 1.409/1.568 (89,9 %) |
| eje 4 | noche local (UTC − 12 h), cualquier sensor | RUTINA del volcán y sin ALERTA en ningún sensor (FP incluido) | port sin `isValidDetection` ni `isThermalArtifact` | 886/891; 1.400/1.557 (89,9 %) |
| eje 6 | noche UTC por volcán **y sensor, sumada sobre los 3 sensores** | RUTINA sin ALERTA en ese sensor | cráter del auto-audit | 2.986/6.259 (47,7 %); por sensor 81,9 / 55,0 / 18,3 % |

Re-corridos, todos reproducen exacto. La diferencia 1.384 contra 1.557 son las noches con FALSO_POSITIVO
(`sin_alerta` del eje 2 da 89,9 %, igual que el eje 4). El 47,7 % del eje 6 es un promedio de tres tasas
ponderado por cuántas noches tiene cada sensor (MODIS aporta 2.409 unidades al 18 %); la "precisión 26,3 %"
suma las mismas unidades mezcladas. **Defendibles**: las tasas por sensor del eje 2 (predicado real,
cobertura, OCR) y, como cota sin el problema de pasadas omitidas, las de v1 por pasada: V375 63,5 %,
V750 20,4 % (693/3.392), MODIS 10,2 % (305/2.977). Cualquier sensor: 90 %, con la definición declarada.

### A6. Eje 2 H206 y H207
- H206: CONFIRMADO en sentido, no en cifra. Re-corrido, el AUC agrupado con etiquetas barajadas dentro de
  cada volcán da en V375 0,635 a 0,699 (`pc_dist` 0,699, `f5` 0,659, `pc_vrp` 0,644), no 0,66 a 0,70; el
  script usa `random.Random(7)` pero el resultado cambió entre corridas (SOSPECHA: orden de iteración de un
  conjunto). La media por volcán barajada queda en 0,47 a 0,52. La trampa de Simpson es real.
- H207: CONFIRMADO exacto (`pc_vrp` sólo summit media 0,829; `pc_dist` 0,831; rangos por volcán idénticos).

### A7. B22 en S133 y segundo pase condicionado en S135
- S133 corrió **dos** A/B distintos: B22 (run 33872821788, Láscar n = 61, Villarrica n = 70, agosto 2026) y
  área (run 33912398561). La memoria "S133 fue el A/B del área" y el eje 3 "S133 corrió B22" son ambas ciertas
  (`tasks/BLOQUE_ARRANQUE_S134.md:73-74`).
- B22 NO ADOPTAR: CONFIRMADO (`docs/s133/AB_B22_VEREDICTO.md:16-19`): C1 fondo −1,221/−1,181 K, C2 0 pasadas
  perdidas, C3 razón ON/OFF 0,107/0,256. **Matiz decisivo**: C3 exigía invariancia (0,95 a 1,05), no
  paridad con MIROVA; el mismo documento (`:44-48`) dice que la caída "apunta a adoptar" y que no se adoptó
  porque el criterio se congeló antes. Leer "B22 empeora" sería falso.
- S135 −46,6 %: CONFIRMADO (`experiments/_s135_ab_d1d2/RESULTADO_FINAL.md:18-20,29-33`): brazos C (sólo 2º pase
  condicionado) y E (apagado) producen 47 % más registros del artefacto; D (ambos) pierde 12 noches; **B
  (`keep_peak` OFF) quita 100 % del artefacto con 0 noches perdidas y paridad 0,692 contra 0,708 del control**.
  Sólo VIIRS 375, 6 volcanes, 2026-06-01 a 2026-08-31, 260 noches.

### A8. Eje 3: 34,8 % de noches RUTINA con ALERTA; RUTINA por pasada 71 a 77 %
- 34,8 % (927/2.661): CONFIRMADO por re-corrida (conteos por volcán idénticos). Pero es un hombre de paja
  para los bancos reales: el eje 2 exige sólo RUTINA **en ese sensor** y el eje 4 y S138 excluyen ALERTA de
  cualquier sensor. GRAVEDAD rebajada de 4 a 2.
- "RUTINA es registro por pasada": CONFIRMADO (control +3 h da 0). **La cifra 71 a 77 % está inflada por la
  tolerancia de 20 min** (v3): a ±2 min parean 53,8 % V375, 56,5 % V750 y 94,0 % MODIS; un 16 % adicional
  sólo parea entre 10 y 20 min, es decir con otra pasada. La cobertura real por pasada es peor de lo que dice el eje 3.

### A9. Eje 4 H402, H403, H405
CONFIRMADO por re-corrida: cúmulo en inner en 80/80 noches MODIS positivas y 1.512/1.556 negativas (97,2 %);
primer pase MODIS en 685/685, 422/422, 201/201, 1.134/1.134; AUC magnitud 0,378 focal y 0,510 nevado.
`diag_n_first_pass_summit` sólo en `pipeline/process_modis.py:1531` (grep). v1 lo refuerza por pasada: MODIS
publica en 10/87 pasadas ALERTA (11,5 %) y 305/2.977 negativas (10,2 %): no discrimina.
Nota de vocabulario: el eje 4 llama "D19" al segundo pase condicionado; el catálogo (`MIROVA_DIVERGENCES.md:2058`)
y el eje 5 llaman D19 sobre todo a `keep_peak`. Son dos palancas.

### A10. Eje 5 H501 y H502 (flags)
CONFIRMADO. Leído con `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p"`: no hay flag de
compuerta ni de fondo uniforme (lista de nombres con GATE/BT_/KERNEL/UNIFORM impresa). `ENABLE_LOCAL_KERNEL_BG
True` pero gateado por `local_kernel_bg_compatible` desde `volcanoes.yaml` (`scripts/run_pipeline.py:244,288,334`;
`process_modis.py:1041`; `process_viirs.py:1398`); en `process_viirs_mod.py` el parámetro sólo aparece en la
firma (`:419`). La compuerta `NTI_BT_SANITY_K` vive en 5 sitios MODIS (`665,693,701,821,869`), 6 VIIRS 375
(`976,998,1038,1046,1178,1240`) y 6 VIIRS 750 (`624,643,677,685,780,832`). El "sin compuerta" de S137 sólo
envolvió `first_pass_tests_2_and_3` (`experiments/_s136/conformidad_apendice.py:220-224,268`). Respuesta a lo
que el eje 5 dejó abierto: `compute_local_background` usa **media** de vecinos (`pipeline/vrp_regimes.py:104`,
`np.mean(neighbors)`), que coincide con la ecuación 6 del paper. H511 CONFIRMADO: `bt_mir` puede venir de B22
(`process_modis.py:548`) y se reconvierte con `BAND21_LAMBDA` (`:1022,1025`). H510 CONFIRMADO: `keep_peak`
sólo en `process_viirs.py:178,1788`.

### A11. Eje 5 H503, H505, H507
- H503: CONFIRMADO. `MIN_POR_DIA = 2.4` (`tests/test_guard_timeout_vs_ventana_s129.py:43`), guard creado
  2026-08-31 (`a70a59309`); el run 33872836355 (2026-09-04) terminó 19 `failure` a 151 min y 5 `success`.
  61 días x 2,4 = 146 ≤ 150: el guard lo dejaba pasar.
- H505: fecha del secret CONFIRMADA (`EARTHDATA_TOKEN 2026-08-04T07:19:42Z`); vida de 60 días leída en
  `docs/EARTHDATA_TOKEN_SETUP.md:12,42`; vencimiento ~2026-10-03 es derivado (SOSPECHA contra el panel NASA).
- H507: CONFIRMADO con una corrección: los artefactos de S129 vencen **2026-09-14** (mín. de los runs 33370202265
  y 33412422099), no el 15. S133 B22 2026-09-18, S133 área 2026-09-19, S135 2026-09-22.
- H504 (NRT 5 a 7 por día): CONFIRMADO, 4 a 7 runs por día entre 2026-09-03 y 2026-09-13.

### A12. Eje 6 H603 y el 0,551 contra 0,689
- Recall 98,0 % (n 1.530), 45,9 % (n 37), 16,1 % (n 224); ratio 0,551 (n 1.499); 269 de 332 clase 0 publicadas
  en cráter: CONFIRMADO por re-corrida. Dos salvedades: el predicado es el del auto-audit, no el del dashboard;
  y qué significa `class 0` no está verificado. "Nada vivo lo lee": grep en `scripts pipeline tests .github` da 0.
- Descomposición (v2, VIIRS 375):

| variante | ratio mediano | n |
|---|---|---|
| 2026, máximo por noche a ambos lados, cualquier `pc.vrp_mw > 0` (libro) | 0,693 | 858 |
| 2026, idem con predicado cráter | 0,690 | 858 |
| 2026, por pasada contra CONS ALERTA ±2 min | 0,613 | 991 |
| 2025 OSF, por pasada (eje 6) | 0,551 | 1.507 |
| 2025 OSF, máximo por noche (método del libro) | 0,745 | 972 |

  **El factor que manda es la unidad**: el máximo por noche sube la razón 0,08 en 2026 y 0,19 en 2025. Año y
  referencia mueven poco (por pasada 0,55 contra 0,61). El predicado no mueve nada. La mediana de medianas por
  volcán da 0,87 (2026) y 0,84 (2025): la mezcla de volcanes también cambia el número. Número defendible:
  **0,55 a 0,61 por pasada**, declarando unidad y año.

### A13. Coppola y papers
- H606: SOSPECHA confirmada como ausencia de registro (mi grep en `docs tasks` sólo encuentra propuestas y
  "contactar a Coppola DESPUÉS", `docs/PAPER_VRP_CHILE_DRAFT_S72.md:26`).
- H607: CONFIRMADO al estado S128: `docs/s128/lectura_papers.json:1394-1397` Fernandina 2025 `SIN_TOCAR`;
  `:821-823` Massimetti 2020 `MENCIONADO`.

## 3. Contradicciones entre ejes, resueltas

| # | contradicción | resolución con dato |
|---|---|---|
| X1 | 82 % / 90,5 % / 89,9 % / 47,7 % | A5: unidad por sensor contra cualquier sensor, noches FP, suma entre sensores |
| X2 | eje 1 "27/120 omitidas" contra eje 3 "71 a 77 % con fila" | tolerancia: a ±2 min sólo 54 a 57 % de nuestras pasadas VIIRS tienen fila (v3) |
| X3 | eje 1 "RUTINA no sirve" contra ejes 2, 4, 6 que la usan | por pasada limpia la sobre-publicación V375 sigue en 63,5 % y crece a nadir (v1); RUTINA vale para paridad |
| X4 | 0,551 contra 0,689 | A12: unidad |
| X5 | eje 4 "D19 es no-op en MODIS" contra eje 5 "D19 sólo en V375" | hablan de palancas distintas (segundo pase contra `keep_peak`); ambas ciertas |
| X6 | eje 3 "B22 NO ADOPTAR" contra eje 4 "banda 22 literal, puede" | ambos ciertos; el NO ADOPTAR era por invariancia, no por paridad (A7) |
| X7 | planes: eje 4 B y C, eje 3 factorial, eje 5 B22 + D25 + 2º pase | ninguno prioriza `keep_peak` OFF, que es la palanca con reproceso hecho sobre el objeto dominante V375 (H-S139-01) |
| X8 | eje 2 H206 0,66 a 0,70 contra re-corrida 0,64 a 0,70 | no determinismo del barajado; la conclusión no cambia |
| X9 | eje 5 artefactos S129 el 15 | vencen el 14 |

## 4. Lista fundida de hallazgos (lo peor primero)

### H-S139-01. La sobre-publicación de VIIRS 375 es, en dos tercios, el píxel frío de `keep_peak` (D19)
- SCRIPT:SALIDA `v3_salida.txt`, `v4_salida.txt`, `v1_salida.txt`. Fuentes fundidas: eje 2 H201, eje 4 H401, eje 6 H602.
- QUÉ PASA. En un cono nevado de noche, el píxel más tibio del disco del Test 1 es el borde de menor cota, no el
  cráter (A69). `keep_peak` conserva ese único píxel y el ancla lo publica como `test1_roi`. En pasadas
  negativas limpias es 1.356 de 2.062 publicaciones (66 %), contra 171 de 960 en pasadas ALERTA (18 %); el píxel
  está bajo el fondo en 65,7 % de los casos de noches sin alerta (mediana −1,56 K, n 2.817) y el cúmulo mide 0,050 MW.
  No es calor volcánico: es topografía. Magnitud publicada en negativos limpios: mediana 0,046 MW; 782 de 2.062
  bajo el p5 de las ALERTAS nocturnas de MIROVA (0,04 MW).
- DASHBOARD. Punto rojo summit casi todas las noches en Llaima, Copahue, Villarrica, Chaitén: el operador ve
  "algo en el cráter" donde no hay calor.
- Proxy offline sin ese objeto (cota, A18): negativos V375 por noche 82,2 % a 43,1 %; positivos 98,4 % a 87,2 %
  (95 noches, 46 de Tupungatito y 23 de Lastarria, la tensión S134 H1). El reproceso real de S135 brazo B no
  perdió ninguna en esos volcanes.
- REPRODUCIR `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/verificador/v3_keep_peak_y_desfase.py`.
- CONFIANZA CONFIRMADO (composición y física); SOSPECHA el tamaño del efecto fuera de los 6 volcanes y 3 meses de S135.
- GRAVEDAD 5 para el plan; 4 para la alerta.

### H-S139-02. Tres sensores, tres objetos distintos en los negativos
- SCRIPT:SALIDA `v1_salida.txt`. VIIRS 750 publica 20,4 % por pasada negativa, mediana 0,303 MW, 30 % de 1 píxel,
  D19 en 20 de 693. MODIS 10,2 %, mediana 2,011 MW, **p90 5,000 MW = `PATH_D_ONLY_CAP_MW`**, y no discrimina
  (11,5 % en pasadas ALERTA). Fuentes: eje 2 H202, eje 4 H402 y H408.
- CONFIANZA CONFIRMADO. GRAVEDAD 4. Consecuencia: B22 + fondo uniforme no tocan el objeto dominante de V375,
  y en MODIS el objeto publicado en negativos es el campo difuso con tope.

### H-S139-03. MODIS: el predicado del dashboard mide la etiqueta `far`, no la detección; el poder es de Láscar
Eje 2 H202, eje 4 H402, H404, H405; A9. CONFIRMADO. GRAVEDAD 4.

### H-S139-04. Las palancas D22 y D25 no existen como flag; D25 no existe en VIIRS 750; la compuerta está en 17 sitios
Eje 5 H501, H502; eje 4 H406; A10. CONFIRMADO. GRAVEDAD 4 (un brazo mal delimitado mide otra combinación).

### H-S139-05. La referencia: RUTINA es "MIROVA dio 0 en este granule"; la noche es la unidad contaminada, no la pasada
Eje 1 H101, H102; eje 3 H302, H303; A1, A3, A8. CONFIRMADO lo factual; REFUTADO que invalide RUTINA como negativo de
paridad. Cobertura real por pasada ±2 min: V375 53,8 %, V750 56,5 %, MODIS 94,0 %. GRAVEDAD 4.

### H-S139-06. No hay definición de terminado ni regla de desempate fidelidad contra paridad
Eje 6 H601, eje 3 P6. Grep del eje 6 re-corrido: 3 coincidencias, ninguna de la misión. S135 brazo B es el caso
exacto: el más limpio falla la paridad por 0,016. CONFIRMADO. GRAVEDAD 4.

### H-S139-07. Paridad de magnitud VIIRS 375: 0,55 a 0,61 por pasada; 0,69 es máximo por noche
A12. CONFIRMADO. GRAVEDAD 3 (el libro de cuentas y el auto-audit usan distintas unidades y ninguna lo declara en el dashboard).

### H-S139-08. El dashboard compara sin OCR; el JSON de MIROVA descarta clases de 10 MW o más
Eje 1 H105, H106; eje 2 H203; A3, A4. CONFIRMADO. GRAVEDAD 3.

### H-S139-09. El veredicto B22 de S133 es de invariancia, no de paridad
A7. CONFIRMADO. GRAVEDAD 3 (evita cerrar B22 por error, A95).

### H-S139-10. El segundo pase condicionado solo empeora el artefacto 46,6 %; ambos juntos pierden 12 noches
Eje 3 H304; A7. CONFIRMADO. GRAVEDAD 3.

### H-S139-11. AUC agrupado engaña; por volcán sí hay señal en V375
Eje 2 H206, H207; A6. CONFIRMADO. GRAVEDAD 3.

### H-S139-12. Operación: guard de reloj bajo, token ~2026-10-03, artefactos vencen desde mañana, NRT 4 a 7 por día
Eje 5 H503, H504, H505, H507; A11. CONFIRMADO (vencimiento del token derivado). GRAVEDAD 3.
Los artefactos de S129 vencen el 2026-09-14: si se quieren, hay que bajarlos hoy.

### H-S139-13. Verdad externa sin usar: archivo OSF 2025 y TIF remotos vivos
Eje 6 H603, H605. Confirmado: grep 0 lectores de OSF; `mirova-tif-archive` remoto con commit 2026-09-13 14:42 UTC
y checkout local 2026-05-20. GRAVEDAD 3.

### H-S139-14. `f5_core_vrp_mw` supera a `pc.vrp_mw` en 23 % de los records V375
Eje 2 H208. Re-medido: 17.667 records, 4.145 sobre 1 %, 964 lo duplican. CONFIRMADO. GRAVEDAD 2.

### H-S139-15. B22 reconvierte radiancia con la longitud de onda de B21
Eje 5 H511; A10. CONFIRMADO el código, SOSPECHA el tamaño. GRAVEDAD 2.

### H-S139-16. Evidencia de imagen del eje 1: mitad diurna y no archivada
A1. 38 de 70 NaN transcritos son nocturnos; imágenes no guardadas. CONFIRMADO. GRAVEDAD 2.

### H-S139-17. El predicado cambia de un eje a otro y cambió hoy
Eje 3 H301, H309; eje 4 H410. S138 eje 5 §4.4 usa `final_hotspot_dist_km` (`docs/audit_s138/EJE_5_bateria_apendice_instrumento.md:319-322`);
eje 4 M1 omite `isValidDetection` e `isThermalArtifact`; eje 6 usa el del auto-audit. Efecto medido chico
(tasas por sensor coinciden a menos de 1 punto). CONFIRMADO. GRAVEDAD 2.

### H-S139-18. Coppola sin consultar; Fernandina 2025 y Massimetti 2020 sin leer a fondo
A13. SOSPECHA (ausencia de registro) y CONFIRMADO (estado S128). GRAVEDAD 2.

### H-S139-19. El auto-audit semanal lleva 7 semanas FUERA_DE_BANDA sin poder cambiar una decisión
Eje 6 H608. `history.jsonl`: VERDE hasta 2026-07-20, FUERA_DE_BANDA del 2026-07-27 al 2026-09-07. CONFIRMADO. GRAVEDAD 2.

No verificados por mí (quedan con la confianza de su autor): eje 1 H107 a H114, eje 5 H506, H508, H509, H512,
eje 6 H604, H609, H610, eje 3 H305 a H312 salvo lo citado.

## 5. Qué sostiene un plan y qué no

**Sostienen un plan (CONFIRMADO):**
1. En VIIRS 375 el objeto dominante de la sobre-publicación es D19 `keep_peak`, físicamente un píxel bajo el fondo; su
   palanca tiene flag (`ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK`), está en el paper como infidelidad (no literal) y tiene
   reproceso hecho con 0 noches perdidas en 6 volcanes.
2. Cada sensor necesita su propio diagnóstico: V375 D19; V750 otro objeto de ~0,3 MW; MODIS etiqueta `far` en
   positivos y campo con tope de 5 MW en negativos.
3. RUTINA por pasada es un negativo de paridad utilizable; la noche necesita cobertura por pasada a ±2 min, no 20.
4. D22 y D25 exigen código nuevo con A45 antes de cualquier A/B; D25 no existe en V750; `compute_local_background`
   ya usa media.
5. MODIS no se puede calibrar por paridad propia (80 positivos, 74 de Láscar, 3 después de junio).
6. Magnitud V375 por pasada 0,55 a 0,61; siempre declarar unidad.
7. Operación: token, artefactos que vencen desde el 14 de septiembre, guard de reloj a 5,1 min por día.

**No sostienen un plan:**
- "RUTINA no es negativo, el banco mediría la nubosidad" (A1).
- 47,7 % y "precisión 26,3 %" (A5).
- 0,689 como paridad de magnitud sin declarar unidad (A12).
- "B22 ya se probó y no sirve" (A7).
- "71 a 77 % de las pasadas tienen fila MIROVA" (A8).
- "34,8 % de los negativos son positivos" como defecto de los bancos actuales (A8).
- Cualquier cifra del proxy de v3 como efecto esperado de apagar `keep_peak` (A18).

## 6. Preguntas que sólo Nicolás puede decidir

1. **`keep_peak` OFF**: S135 brazo B elimina el artefacto sin perder noches y aleja la paridad de magnitud 0,016
   (0,692 contra 0,708). ¿Se acepta esa pérdida marginal para quitar el punto rojo diario de 5 volcanes nevados?
   ¿O se extiende primero a los 11 Tier A y a más meses?
2. **Desempate** fidelidad al paper contra paridad con lo que MIROVA publica, y una definición de terminado por sensor.
3. ¿Se acepta RUTINA por granule como negativo de paridad aunque MIROVA no distinga nube de cielo despejado?
4. MODIS: ¿criterio sólo de fidelidad literal, dado que no hay positivos fuera de Láscar?
5. ¿El dashboard debe incluir el canal OCR? ¿Y abrir `VALID_CLASSES` a Moderado y Alto antes de una fase efusiva?
6. ¿Escribir a Diego Coppola con las 11 preguntas del eje 6 antes de gastar 650 a 1.100 h de runner?
7. ¿Renovar el token Earthdata y bajar hoy los artefactos de S129 (vencen el 2026-09-14) antes de fijar el plan?
8. Unidad de magnitud oficial: ¿por pasada o máximo por noche?

## 7. VERIFICADO LIMPIO

| qué | comando | resultado |
|---|---|---|
| Los 9 scripts de los ejes 2, 3, 4, 6 y `medir_ocr.py` corren y reproducen sus números | `experiments/_s139_audit/verificador/rerun_index.txt` | exit 0 todos; eje 2, 3, 4 y 6 idénticos salvo el AUC barajado |
| Predicado del dashboard en Python igual al ejecutado con node | `v1_negativo_por_pasada.py`, primera línea | 7.377/7.377 |
| Pareo de pasadas no es azar | `v1`, reloj +3 h | 0/5.334, 0/10.398, 0/10.314 |
| `final_hotspot_source` persistido en todos los records de la ventana | `v3`, primera línea | 0 sin campo |
| Flags de producción del plan | `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."` | B22 False, 2º pase condicionado False, keep_peak True, kernel local True, `NTI_BT_SANITY_K` 3.0, UTM False, tope path D 5.0, etiqueta MODIS por cúmulo False, prosa False, Test 1 NTI False |
| Fondo local 3x3 usa media | `sed -n 38,110p pipeline/vrp_regimes.py` | `np.mean(neighbors)` |
| `keep_peak` sólo en VIIRS 375 | `grep -rn ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK pipeline/*.py` | `process_viirs.py:178,1788` |
| `diag_n_first_pass_summit` sólo MODIS | `grep -rn diag_n_first_pass_summit pipeline/` | `process_modis.py:1531` |
| Mirova-v1 local atrasado | `gh api .../compare/<HEAD>...main` | 102.953 |
| A/B B22 y área de S133, A/B de 5 brazos S135 existen con esos veredictos | lectura de `docs/s133/AB_B22_VEREDICTO.md`, `tasks/BLOQUE_ARRANQUE_S134.md:73-74`, `experiments/_s135_ab_d1d2/RESULTADO_FINAL.md` | sanos, no volver a buscarlos |
| El dashboard no consume OCR | `grep -n "consolidado\|rebuild" .github/workflows/sync-mirova-csv.yml` | sólo consolidado |
| Guard de reloj y fallas S133 | `grep MIN_POR_DIA tests/test_guard_timeout_vs_ventana_s129.py`; jobs del run 33872836355 | 2,4; 19 failure a 151 min |
| Árbol de trabajo limpio | `git status --short` | sólo carpetas S139 sin trackear |
