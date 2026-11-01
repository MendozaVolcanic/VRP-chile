# F1 (S158): traducción literal, nuestro VIIRS 750 contra el código de MIROVA

Auditor F1, 2026-10-21. Rama `s158-d17-diseno`, worktree `D:\vrp-trabajo\temporales\s158_d17`. No se tocó nada fuera de
`experiments/_s158_audit/f1/`. Python con `-B`, perfil `mirova_equivalent` leído de `pipeline.profile`.

Vara: `experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m` (H) y
`MIROVA_VIIRS750_VRP.m` (V), leídos enteros en esta sesión; el oráculo `experiments/_s158_oraculo_mirova/mirova_v750.py`
se leyó entero y reprodujo su control en esta sesión (5 píxeles, 9.880.936 W). Nuestro lado:
`pipeline/process_viirs_mod.py` (pvm), `pipeline/detection_context.py` (dc), `pipeline/store.py`, `frontend/index.html`
(predicado ejecutado con node, A97).

## Instrumentos de esta sesión (todos en esta carpeta, con su salida al lado)

| script | qué mide | salida |
|---|---|---|
| `nuestro_k_en_grilla.py` | nuestra cadena K (funciones de `pipeline/` en el orden de `calculate_vrp`) sobre una matriz 67 x 67 | módulo |
| `etna_k_contra_mirova.py` | pasada de Etna del ejemplo OSF por MIROVA y por K; barrido de un foco débil | `etna_k_contra_mirova_salida.txt` |
| `etna_barrido_fino.py` | umbral de detección y publicación, foco dentro y fuera de la caja 7 x 7 | `etna_barrido_fino_salida.txt` |
| `etna_compuerta.py` | si el primer pase vacío es la compuerta `bt > t_bg + 3 K` | `etna_compuerta_salida.txt` |
| `predicado_tablero.js` | el predicado del tablero (texto de `index.html`) evaluado con node sobre los 28.581 records V750 | `pub_v750.json` |
| `sustrato_corpus.py` | sustrato de cada diferencia en los records V750 de los 11 Tier A | `sustrato_corpus_salida.txt` |
| `alertas_mirova_perdidas.py` | cada ALERTA_TERMICA V750 de la tabla de MIROVA, clasificada por lo que hicimos | `alertas_mirova_perdidas_salida.txt` |
| `cruce_referencia.py` | razón publicado / MIROVA y detalle de las cumbres en cero | `cruce_referencia_salida.txt`, `..._desde_0613_salida.txt` |
| `primer_pase_vacio.py` | detecciones que vienen sólo del segundo pase | `primer_pase_vacio_salida.txt` |
| `chequeos_varios.py` | NTI absoluto, filtros de artefacto, alertas diurnas, ida y vuelta LUT | `chequeos_varios_salida.txt` |

Ventanas: «K» = records con `datetime_utc` desde 2026-09-18 (fecha en que los datos cambian de detector) hasta el
2026-10-21 06:48, 1.553 records V750, 67 publicados. «Desde 2026-06-13» = tramo en que la geometría del OCR ya estaba
calibrada (A119); en las dos se usa SÓLO la tabla (`latest_consolidado.csv`, `Sensor == "VIIRS"`, `Tipo_Registro`), sin
OCR. `scripts/calidad_referencia_mirova.py` avisó sólo hitos del OCR (2026-10-09 y 2026-10-10), que no se usa.

Control del instrumento principal (Etna): el oráculo da 5 píxeles y 9,881 MW, igual a su README; nuestra cadena, sobre la
misma matriz, da los mismos 5 píxeles (fila, columna 35,32 35,33 35,34 36,32 36,33). Con f = 0 las dos dan 0 (control
negativo). El join del predicado da 67 publicados y 1.486 no publicados en K (ninguno de los dos lados muerto).

---

## Hallazgos, de lo más grave a lo menos

### H1. El fondo del VRP es la mediana del anillo de 5 a 25 km: en una cumbre fría la magnitud cae a menos de la mitad y las alertas débiles desaparecen del tablero

- **ARCHIVO:LÍNEA**: `pipeline/process_viirs_mod.py:560-567` (t_bg = mediana de M13 en el anillo), `:1041`
  (`L_bg_rad` escalar), `:1056` (`np.maximum(L_hot - L_bg_rad, 0.0)`); `pipeline/clustering.py` (vent_anchored prefiere
  cúmulos con vrp > 0); `frontend/index.html:1595` (`isValidDetection` exige `pc.vrp_mw > 0`). MIROVA: `V:63-85` (huecos
  dilatados 3, 5 o 7 celdas, `fillmissing2` lineal, sin recorte).
- **QUÉ PASA**: de noche la cumbre de un volcán alto es más fría que las laderas bajas que forman el anillo de 5 a 25 km.
  MIROVA estima el fondo bajo el foco interpolando desde los alrededores inmediatos (frío, como la cumbre); nosotros
  usamos un solo número para toda la escena, la mediana del anillo, que queda varios grados más tibia. El exceso de
  radiancia del foco se achica, y si el píxel detectado es más frío que esa mediana el exceso sale negativo, se recorta a
  0 MW, el cúmulo vale 0 y el tablero no lo publica aunque el detector lo vio.
  - Misma pasada de Etna, mismos 5 píxeles: MIROVA 9,881 MW, nosotros 2,748 MW (sin recorte 2,600). Fondo de MIROVA bajo
    los píxeles: BT 269,9 a 270,9 K; nuestro t_bg: 280,55 K (`etna_barrido_fino_salida.txt`).
  - Foco de Etna escalado (barrido a): MIROVA publica 2,881 MW con 5 píxeles en f = 0,3, 0,995 MW en f = 0,15 y 0,022 MW en
    f = 0,05; nosotros detectamos 1 a 4 píxeles en todo ese rango y publicamos **0** en todos.
  - Corpus, ventana K: de 51 ALERTA_TERMICA V750 de MIROVA, 7 (13,7 %) son «cumbre_en_cero»: detectamos un píxel dentro
    del inner y vale 0 MW por el fondo (Isluga 2, Láscar 4, Chillán 1; MIROVA 0,16 a 0,36 MW, todas a 0,75 km). Desde
    2026-06-13: 26 de 136 (19,1 %). Ninguna es ≥ 1 MW. En K hay además 30 records con píxel detectado en la cumbre y
    todos en 0 MW, ninguno publicado; 15 de ellos son pasadas RUTINA de MIROVA (en esas ocultarlos coincide con MIROVA).
  - Magnitud neta en pasadas que los dos publican: publicado / MIROVA mediana **0,411** (K, n = 40; Chillán 0,416 con
    n = 32) y **0,416** desde 2026-06-13 (n = 103; Láscar 0,424 con 38, PCC 0,368 con 19). El pareo se hace desde
    nuestros records y puede repetir una fila de MIROVA: la mediana es indicativa, no exacta.
- **CÓMO SE VE EN EL DASHBOARD**: en la erupción de Chillán las barras de VIIRS 750 quedan en ~40 % de lo que publica
  MIROVA (10 a 20 MW donde MIROVA da 25 a 50); en Láscar e Isluga las alertas débiles de MIROVA (Muy Bajo) no aparecen.
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/f1/etna_barrido_fino.py`; corpus:
  `python -B experiments/_s158_audit/f1/alertas_mirova_perdidas.py 2026-09-18`. Caso: Láscar 2026-09-21 05:42
  VIIRS_SNPP_750, t_bg 264,19 K, píxel en el inner a 262,37 K, MIROVA ALERTA_TERMICA 0,22 MW.
- **CONFIANZA**: CONFIRMADO el mecanismo (leído y medido sobre la pasada de Etna) y el sustrato (corpus). Que en Chile la
  causa de la razón 0,41 sea toda el fondo es SOSPECHA: en Etna explica el 100 % (mismos píxeles, mismo coeficiente),
  en Chile no hay gránulo para separarlo de D17.
- **GRAVEDAD**: 4. Tuerce la lectura de nivel de una erupción en curso (magnitud a 0,4) y apaga alertas débiles en la
  cumbre. Las perdidas son bajo 1 MW, donde una pérdida pesa igual que una publicación de más (criterio de victoria).
- Nota para D25: el brazo D del A/B (media de vecinos no alertados) toma justo el halo que MIROVA aparta con la dilatación
  (ya dicho en `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §4.3; el oráculo lo midió en +2,65 % sobre Etna). Lo que este
  informe agrega es el tamaño del problema que D25 quiere resolver: ×0,28 en Etna y ×0,41 en Chile.

### H2. Rechazamos todo VIIRS 750 diurno; MIROVA lo procesa y en la ventana K hay 3 alertas protegidas de Chillán perdidas por eso

- **ARCHIVO:LÍNEA**: `pipeline/store.py:203-224` (`_reject_daytime`, rechaza VIIRS de día salvo `ENABLE_DAYTIME_VIIRS`),
  perfil efectivo `ENABLE_DAYTIME_VIIRS = False` (leído de `pipeline.profile`). MIROVA: `H:173-199` (rama `dayflag ≠ 0`
  con K1 -0,5, 15σ y mínimos 0,02) y `H:83-89` (rechazo por sun-glint < 12°).
- **QUÉ PASA**: de día MIROVA sigue detectando con umbrales más altos; nosotros no generamos record. En una erupción, el
  foco es lo bastante fuerte para pasar los umbrales diurnos.
- **Sustrato**: las 3 ALERTA_TERMICA V750 de la ventana K sin record nuestro son de Chillán, de día (2026-10-01 18:42,
  3,71 MW; 2026-10-10 18:18, 3,33 MW; 2026-10-18 19:06, 2,49 MW; las tres a 0,75 km), y no tenemos ningún record V750 a
  ±90 min. Las tres son ≥ 1 MW, o sea alertas protegidas. Desde 2026-03-01 la tabla trae 4 ALERTA_TERMICA V750 diurnas
  de 279 (`chequeos_varios_salida.txt`, c).
- **CÓMO SE VE EN EL DASHBOARD**: la serie de MIROVA muestra puntos de tarde (con el ícono de sol) que nuestra serie no
  tiene; el operador ve a MIROVA ver algo que nosotros no.
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/f1/alertas_mirova_perdidas.py 2026-09-18` (clase
  `sin_record`) y la consulta de ±90 min que se corrió en esta sesión sobre `NevadosDeChillan.json`.
- **CONFIANZA**: CONFIRMADO (código leído, flag leído, tres pasadas contadas).
- **GRAVEDAD**: 4. Son pérdidas de alertas ≥ 1 MW, que el criterio de victoria no admite. Ya existe el flag (D-10); lo nuevo
  es que el código de MIROVA confirma la rama diurna y que la rama nuestra apagada lleva K1 -0,6 donde el código usa
  -0,5 (`pvm:481`, `_umbrales_de_la_pasada`), y no tiene el rechazo por sun-glint.

### H3. La región sensible: nosotros, un círculo de 3 a 20 km centrado en el cráter; MIROVA, una caja de 7 x 7 celdas centrada en su grilla

- **ARCHIVO:LÍNEA**: `pipeline/detection_context.py:299-325` (`roi1_summit_mask`: `dist_km <= inner_km`), `pvm:534`
  (`ENABLE_ROI1_BOX_PAPER = False`), `pvm:521` (distancia al cráter). MIROVA: `H:136-138`, `H:389-399`; matriz de
  ejemplo: la clase 2 ocupa filas y columnas 30 a 36 de 67 (49 celdas), la clase 1 filas 22 a 42 y columnas 24 a 42
  (verificado cargando el `.mat` en esta sesión).
- **QUÉ PASA**: un píxel tibio a 3 o 4 km del centro, en la ladera, está dentro de nuestro círculo de 5 km (umbral
  sensible: 5σ y 0,003) pero fuera de la caja de MIROVA (10σ y 0,02 en NTI). Lo publicamos donde MIROVA calla. Además la
  caja de MIROVA está centrada en su centro de grilla y la nuestra en el cráter: en PCC están a 7,58 km, en Tupungatito
  a 4,86 km, en Planchón Peteroa a 2,02 km.
  - Etna, foco corrido 5 celdas al NE (fuera de la caja, dentro de 5 km): MIROVA no detecta nada con f ≤ 0,3; nosotros
    detectamos hasta f = 0,05 y publicamos 0,449 MW en f = 0,3 (barrido b).
  - Corpus K, publicados: 15 de 67 (22,4 %) tienen todos sus píxeles del inner fuera de la caja; los 15 son de PCC (28 de
    28 píxeles). En los otros diez volcanes, 0 píxeles publicados fuera de la caja.
- **CÓMO SE VE EN EL DASHBOARD**: puntos rojos «summit» en PCC con umbral de cumbre a 7 km del centro de la grilla de
  MIROVA.
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/f1/etna_barrido_fino.py` (bloque b);
  `python -B experiments/_s158_audit/f1/sustrato_corpus.py` (bloque 2).
- **CONFIANZA**: CONFIRMADO el mecanismo y el sustrato contra la caja del ejemplo. SOSPECHA para PCC en particular: el
  código dice que las ROI «can be shifted, reshaped or resized» por volcán (`H:120-125`) y en la ventana K MIROVA alertó en
  PCC a 7,65 y 7,83 km, así que su caja de PCC puede no ser la del ejemplo.
- **GRAVEDAD**: 3. Sube la publicación donde MIROVA no publica (A98), concentrado en PCC; en los demás volcanes el
  sustrato publicado es cero.

### H4. Fuera de la cumbre el mínimo de MIROVA en NTI es 0,02 (0,0225 en nuestras unidades) y decide en 3 de cada 4 pasadas; el nuestro (0,01) decide en 6 %

- **ARCHIVO:LÍNEA**: `pvm:486` (`DNTI_CONTEXTUAL_C1_SCENE = 0.01`), `dc:525-535`; `dc:162-189` (media de 8 vecinos).
  MIROVA: `H:183-187`, `H:281-312` (media de 3 x 3 con el central).
- **QUÉ PASA**: el contraste de MIROVA es 8/9 del nuestro para el mismo píxel (la media incluye al propio píxel), así que
  sus mínimos fijos valen 9/8 en nuestras unidades: NTI fuera 0,0225, ETI fuera 0,01125, cumbre 0,003375. Con los μ y σ
  de nuestro primer pase:

  | ventana | n | μ+10σ(dNTI) < 0,0225 (manda el mínimo de MIROVA) | < 0,01 (manda el nuestro) | umbral de MIROVA ≥ 1,5 × el nuestro | cumbre ETI: manda 0,003375 |
  |---|---|---|---|---|---|
  | corpus 2025-02-15 a 2026-10-21 | 28.580 | 83,4 % | 4,8 % | 37,0 % | 30,0 % |
  | K | 1.552 | 75,6 % | 6,2 % | 37,6 % | 21,7 % |
  | publicados K | 67 | 53,7 % | 1,5 % | 20,9 % | 20,9 % |

- **CÓMO SE VE EN EL DASHBOARD**: invisible en los diez volcanes de inner ≤ 7 km (fuera del inner no se publica). Sube
  la publicación en PCC (inner 20 km, ver H3) y en lo que el laboratorio y los recuentos de «lejanas» muestran.
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/f1/sustrato_corpus.py`, bloque 1.
- **CONFIANZA**: CONFIRMADO como sustrato (qué umbral manda). El efecto por píxel no se puede medir: el dNTI de cada
  píxel no se persiste. La equivalencia 9/8 vale exacta sólo con los 8 vecinos válidos, y nuestro σ sale de otro pool
  (barrido nativo, D17).
- **GRAVEDAD**: 2. Sobre-publicación fuera de la cumbre, que el tablero en su mayor parte no muestra.

### H5. El primer pase con compuerta de BT queda vacío en las cumbres frías y el segundo pase, sin compuerta y sin condición, hace la detección: 19 de 67 publicados vienen sólo de él

- **ARCHIVO:LÍNEA**: `dc:546` (compuerta `bt > t_bg + 3` en el primer pase), `dc:958` (el segundo pase no la tiene),
  `dc:906` y perfil `ENABLE_SECOND_PASS_CONDITIONED = False`; el segundo pase reusa el ETI del primero (`pvm:916`) y su
  pool de μ y σ no aplica el piso de -0,1 (`dc:923`). MIROVA: sin compuerta (`H:389-399`), segundo pase con regresión y
  estadísticos recalculados (`H:228-235`) y piso de -0,1 en NTI en los dos pases (`H:298`).
- **QUÉ PASA**: en una cumbre más fría que la mediana del anillo (el mismo fenómeno de H1), la compuerta rechaza el foco
  en el primer pase. El segundo pase, que el paper describe como refinamiento de los bordes de lo ya detectado, corre
  aunque no haya nada detectado y sin compuerta, y encuentra el foco como una detección nueva. El resultado se parece al
  de MIROVA por accidente.
  - Etna: con compuerta, primer pase 1 píxel (f = 1) y 0 (f = 0,3 y 0,1); sin compuerta, 4 y 1, igual que el primer pase
    de MIROVA (4 en f = 1). En f = 0,3 la vía con compuerta termina con 4 píxeles y MIROVA con 5
    (`etna_compuerta_salida.txt`).
  - Corpus K: 53 de 118 pasadas con detección (45 %) tienen el primer pase vacío; 19 de los 67 publicados (28 %) salen
    sólo del segundo pase (`primer_pase_vacio_salida.txt`).
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy. Es un riesgo: si se adopta el segundo pase condicionado
  (`docs/PREREGISTRO_AB_D1_D2_S135.md`) sin quitar la compuerta, se apagan esos 19 publicados de 67 (cota: el segundo pase
  condicionado también cambia los nuevos adyacentes).
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/f1/etna_compuerta.py`;
  `python -B experiments/_s158_audit/f1/primer_pase_vacio.py`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3. No tuerce una decisión hoy, pero dos palancas (D22 y la condición del segundo pase) están acopladas sin
  que el catálogo lo diga, y mover una sola apaga alertas.

### H6. Lo publicado es un cúmulo con modo de un píxel; MIROVA suma todos los alertados de la escena

- **ARCHIVO:LÍNEA**: `pvm:1092-1130`, `pipeline/single_pixel_mode.py` (cúmulos de ≤ 3 píxeles y < 5 MW publican el
  máximo, no la suma), `frontend/index.html:1162-1183` (`mirovaEqVrp` publica `pc.vrp_mw` sólo si el cúmulo está dentro
  del inner). MIROVA: `V:83-85` y `H:241-248` (suma de todos los alertados, de las tres regiones).
- **QUÉ PASA**: un foco que ocupa dos o tres píxeles se informa por el más caliente; MIROVA suma los tres.
  - Publicados K: modo de un píxel activo en 52 de 67, con más de 1 píxel en 18 de ellos. Razón publicado / suma de todos
    los píxeles guardados (top 100 y descartados): mediana 1,000, p5 0,388, < 0,9 en 20,9 % (n = 67; ningún record con
    los 100 píxeles llenos, así que la suma es completa).
- **CÓMO SE VE EN EL DASHBOARD**: magnitud más baja en uno de cada cinco publicados, encima de H1.
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/f1/sustrato_corpus.py`, bloque 4.
- **CONFIANZA**: CONFIRMADO (D32 y D8' ya lo nombran; esto es el sustrato en K).
- **GRAVEDAD**: 2.

### H7. Pasadas en que MIROVA alerta y nosotros no detectamos nada, sin causa atribuible desde los records

- **SCRIPT:SALIDA**: `alertas_mirova_perdidas_salida.txt`, clase `sin_deteccion`: 5 de 51 en K (PCC 3, Chillán 2) y 16 de
  136 desde 2026-06-13. Una ≥ 1 MW: PCC 2026-10-10 05:54 VIIRS_NOAA21_750, MIROVA 1,19 MW a 7,83 km, nuestro μ+5σ del
  dNTI 0,0142 (umbral de cumbre casi 5 veces el mínimo 0,003).
- **QUÉ PASA**: en esas pasadas nuestro σ del contraste es alto (μ+5σ entre 0,008 y 0,014) y el foco no lo supera.
  Candidatos: el pool de μ y σ sobre el barrido nativo con duplicados de bow tie (D17), las absolutas que no salen del
  pool, el piso de -0,1 aplicado a los dos índices, la desviación con N. Sin el gránulo no se separan.
- **CÓMO SE VE EN EL DASHBOARD**: MIROVA con alerta, nosotros sin barra.
- **CONFIANZA**: CONFIRMADO el conteo; la causa es SOSPECHA.
- **GRAVEDAD**: 3 (una alerta protegida en la ventana K).

### H8. Diferencias de entrada sin sustrato medible desde los records

- `pvm:244-253, 278-286`: leemos BT del LUT de la L1B y la volvemos a radiancia con Planck monocromática a 4,05 y
  10,763 µm y constantes CODATA (`pvm:352-355`); MIROVA recibe radiancia (`H:19-23`) y usa sus propias constantes
  (`H:410-412`). Con una respuesta espectral de M13 supuesta rectangular, la ida y vuelta sesga la radiancia en -0,55 % a
  240 K, -0,25 % a 300 K y +0,02 % a 600 K (`chequeos_varios_salida.txt`, d). En el exceso de un foco de 0,2 MW eso es del
  orden de 10⁻³ MW. SOSPECHA (no se tiene el LUT real), GRAVEDAD 1.
- `pvm:252, 285`: el bit de saturación de calidad y los techos de 634 K (M13) y 343 K (M15) pasan el píxel a NaN; el
  código compacto de MIROVA no trae control de calidad («Quality screening ... remain the responsibility of the user»,
  README). Un píxel saturado en MIROVA entra al detector con su radiancia tope; acá se vuelve un hueco. El máximo de
  `t_max_k` en el corpus V750 es 364,9 K, pero ese instrumento es ciego: un píxel anulado no llega a `t_max_k`. SOSPECHA,
  GRAVEDAD 1 en Chile hoy, más alta en una erupción efusiva grande.
- `H:150-154`: MIROVA anula BT de M15 ≤ 200 K. Nosotros no. No se persiste la BT de M15; el mínimo de t_bg (M13) en el
  corpus es 207,6 K y 44 de 28.581 records tienen t_bg < 220 K. SIN DATO para M15. GRAVEDAD 1.
- `H:163-167`: MIROVA rechaza la escena con la mitad o más de NaN; nosotros sólo exigimos 10 píxeles en el anillo
  (`pvm:566`). Proxy (cobertura del ROI contra el p95 de su clase de cenit): 64 de 1.553 pasadas K bajo el 50 %, ninguna
  publicada. Sin efecto en el tablero en K. GRAVEDAD 1.

### H9. Un record sin detección vale 0,0 MW; MIROVA lo declara NaN y advierte que no es emisión cero

- **ARCHIVO:LÍNEA**: `V:19-22, 45, 50-52` (VRP NaN sin alertas: «No detected alert does not demonstrate zero emission»);
  `pvm:1027` (`vrp_mw = 0.0` por defecto), `frontend/index.html:1162-1183` (devuelve 0), `toDailyMax` (`index.html:1021`)
  toma el 0 como valor.
- **QUÉ PASA**: una pasada nublada y una pasada limpia sin anomalía quedan iguales en el JSON. En el gráfico de barras un
  0 no se dibuja, así que el operador no lo ve distinto; un consumidor que promedie la serie sí.
- **CONFIANZA**: CONFIRMADO lo leído; el efecto sobre consumidores no se midió. **GRAVEDAD**: 1.

---

## VERIFICADO LIMPIO

| qué | vara | cómo se confirmó |
|---|---|---|
| Coeficiente y área del VRP iguales | `V:88-91` (1,97e7 × 0,5625 = 11.081.250) | `pvm:66` y `pvm:55`: 19,7 × 562.500 = 11.081.250; control de `sustrato_corpus.py` bloque 3: el VRP recalculado desde `bt_k` y `t_bg_k` reproduce el guardado (error mediano 2,8e-4, n = 128) |
| Conectiva `max` en los Tests 2 y 3, los dos pases | `H:306-312`, `H:376-382` | `dc:525` y `dc:943` con `ENABLE_TESTS_23_PROSE_BRANCH = True` (leído de `pipeline.profile`) |
| Umbrales de cumbre de noche (5σ, 0,003 en NTI y ETI) y fuera (10σ, 0,01 en ETI) | `H:180-187` | `pipeline.profile` imprimió C2 5/10 y C1 0,003/0,01 |
| Regresión cuadrática NTI esperado contra NTI | `H:343-350` | `dc:765` `np.polyfit(x, y, 2)` (el refit iterativo es D29, ya catalogado) |
| Detección sobre una pasada fuerte | oráculo de Etna | mismos 5 píxeles por las dos cadenas (`etna_k_contra_mirova_salida.txt`) |
| Umbral de detección de un foco débil en la cumbre, dentro de la caja | oráculo, barrido a | las dos detectan desde f = 0,05 y ninguna en f = 0,045 (`etna_barrido_fino_salida.txt`); la diferencia está en la magnitud (H1), no en la detección |
| Test 1 absoluto (K1 -0,8 y no alerta directa) no hace perder publicaciones en K | `H:206, 245` | las 8 pasadas K con `nti_max > -0,7` (todas Chillán) están publicadas (`chequeos_varios_salida.txt`, a) |
| Filtros de artefacto del tablero no ocultan ningún V750 | `index.html:1336-1367` | 0 records V750 con `isThermalArtifact` y `mirovaEqVrp > 0` en 28.581 (con `_mirova_confirmed` sin setear, cota que oculta más) |
| Tope D9 sin efecto en lo publicado de K | | 0 de 67 publicados con `d9_capped` |
| Tope de tamaño de cúmulo (Villarrica, `max_cluster_pixels: 12`) | | 0 records con `cluster_too_large_for_volcano` en todo `Villarrica.json`, todos los sensores. OJO: si ocurriera, `store.py:447-454` pone `vrp_mw = 0` pero deja `primary_cluster.vrp_mw`, que es lo que lee el tablero (ver Fuera de alcance) |
| Escena incompleta no llega al tablero en K | `H:163-167` | proxy: 0 de 64 pasadas con cobertura bajo 50 % están publicadas |

## Fuera de alcance

- `pipeline/store.py:447-454`: el tope `max_cluster_pixels` anula `record.vrp_mw` pero no `primary_cluster.vrp_mw`; el
  tablero publica el segundo (`index.html:1181`) y `isValidDetection` también lo lee (`index.html:1602`). Hoy sin
  sustrato (0 records). Familia A46.
- El predicado `isValidDetection` es verdadero y lo publicado es 0 en 369 records V750 del corpus (cúmulo con energía
  fuera del inner): los contadores que usan `isValidDetection` cuentan detecciones que el gráfico no muestra. No se siguió.
- `alertas_mirova_perdidas.py` mira sólo VIIRS 750. El mismo fondo escalar con recorte existe en MODIS y VIIRS 375
  (`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §3, fila 12, y comentario de `pvm:1043-1045`), sin código de MIROVA contra
  qué medirlo: TRASLADADO, no CONFIRMADO.

## Lo que no pude medir

- El efecto por píxel de los umbrales (H4, H7): el dNTI y el dETI de cada píxel no se persisten, y no encontré gránulos L1B
  locales: la búsqueda de `VJ102MOD*` y `VNP02MOD*` que lancé se cortó antes de recorrer `D:\vrp-trabajo` y el repo de
  OneDrive, así que es SIN DATO, no «no hay». Sin el gránulo no se puede correr el oráculo sobre una pasada chilena.
- La causa de la razón 0,41 en Chile separada entre fondo (H1) y remuestreo (D17): pide el gránulo y el remuestreo.
- La caja de MIROVA para cada volcán chileno: el código dice que se ajusta por volcán y sólo trae la de Etna.
- El LUT real de M13 y M15 (H8): la cifra usa una respuesta espectral rectangular supuesta.
- BT de M15 de los píxeles (filtro de 200 K y techo de 343 K): no se persiste.
- Si MIROVA publica en su tabla una alerta cuyo VRP sale negativo (alerta no vacía, ΔL < 0): el código devuelve el
  número, la cadena NRT que lo publica no está en OSF.
