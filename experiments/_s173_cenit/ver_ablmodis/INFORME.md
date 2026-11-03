# Verificador con contexto limpio: ablación por pieza de MODIS en Chillán (corrida 41588951267)

## 1. Encabezado

- Fecha y hora del servidor (header `Date` de `gh api repos/MendozaVolcanic/VRP-chile`): **2026-11-03 06:41:56 GMT** (inicio de la sesión 06:28:08 GMT).
- Commit sobre el que medí: **f4ec1061dc2a3becde235e6cc7f7a0d124efba39** = `origin/main` tras `git fetch` = `commit` del JSON del artefacto = `head_sha` de la corrida 41588951267 (`gh api .../actions/runs/41588951267`: `workflow_dispatch`, `success`, creada 2026-11-03T06:17:27Z). El checkout local está en `loop/activo` (`656c27e06`); no lo usé: el código lo saqué con `git show` y `git archive f4ec1061d` a `codigo_origin_main/` y `repo_f4ec1061d/` dentro de esta carpeta.
- Modelo: Claude Fable 5.1 (`claude-fable-5-1`, el que declara mi propio sistema). Esfuerzo: **SIN DATO desde dentro del subagente**; `get_session("self")` devuelve la sesión del orquestador (`claude-opus-5-5`, esfuerzo `medium`), no la mía.
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/ver_ablmodis/` (instrumentos y salidas: `caminos.md`, `releer.py/.out`, `vara_y_records.py/.out`, `recalcular_npz.py/.out/.json`, `analisis_2.py/.out`, `por_sensor.py/.out`, `hallazgos.csv`).
- Disco al cerrar: C: 27 GB libres, D: 4,7 GB. No escribí nada en D:.
- Qué NO miré: `leer.py` ni `leer.out` del coordinador (la tarea lo prohíbe); ningún otro informe de verificador; el frente de VIIRS 750 (la frase «al revés que en VIIRS 750» queda SIN EVIDENCIA desde aquí); el código `.m` de MIROVA; los TIF de MIROVA; el bow tie D28 (no lo medí, sólo lo nombro como SOSPECHA); la geolocalización de 5 km contra el MxD03 fuera del píxel más cercano al cráter; `prueba_local.log` (lo leí, no lo re-corrí). No despaché ningún workflow ni usé credenciales.

## 2. En una pantalla

1. El JSON se reproduce desde `nativos/*.npz` con `piezas.py` de f4ec1061d en **27 de 27** para V0, NAT y G5 (vrp, npix, celdas); el control positivo X2/V0 = 2,000 ± 0,0004 en 26 y 2,0073 en 1 (redondeo de 0,137 MW).
2. **Afirmaciones (2), (4) en su número, (5) y (6): CONFIRMADAS**: K (magnitud publicada `pc.vrp_mw`) mediana 0,678 (<30°, n 10) y 0,137 (≥30°, n 17), Spearman −0,901 con nulo95 [−0,39, +0,33]; NAT 0,960 / 0,460, −0,927, jackknife −0,936..−0,921; G5 0,985 / 0,415, −0,750; NAT_AREA 1,145 / 1,387 y es exactamente NAT × sec³(z).
3. **(4) en su conclusión: CONFIRMADA EN PARTE.** G5 también hunde la razón, y por la propia regla de lectura del README dos brazos que hunden son piezas que interactúan. NAT no usa la geolocalización de 5 km (`piezas.py:269`), así que no comparten causa, pero el arnés no aísla «el remuestreo»: la geolocalización de K corre el píxel del cráter 2,8 km de mediana sobre 30° (máx. 6,5 km; ρ +0,81 con el cenit) y saca el cúmulo de la caja sensible de 5 × 5 en 9 de 27 pasadas.
4. **(3) CONFIRMADA EN PARTE**: en magnitud el fondo de K sólo baja el nivel (sin ceros, FA/MIROVA 0,488 / 0,471, ρ +0,006), pero deja la magnitud en 0,0 (exceso recortado) en **6 de 17 oblicuas y 0 de 10 cercanas al nadir**, con la detección intacta (1 a 9 celdas): el fondo sí hace la caída en PUBLICACIÓN, y esas 6 contienen los 5 ceros de K.
5. **(7) REFUTADA para RN** (cambia celdas y magnitud en 27 de 27, ρ +0,50 fuera del nulo, RN/V0 mediana 1,18 sobre 30°), **EN PARTE para FSH** (mueve la magnitud en 27 de 27, 0,49 a 1,85 de V0, sin patrón de cenit), **CONFIRMADA para SC** (idéntico a V0 en 27 de 27). **(1) CONFIRMADA EN PARTE**: el control `registros_iguales` no puede dar verdadero en este arnés (`store.py:89-94` escribe `regimen.codigo_sha` = `GITHUB_SHA`), así que «igual campo a campo» vale sólo para los 9 campos de `comparar_campos`; la publicación perdida de X2 sí es la regla de cirrus (t_max_k 269,57 K < 273,15 y 11,44 > 10 MW; node da [1, 0]).

## 3. Veredicto por afirmación del coordinador

Denominador de todo: 27 pasadas MODIS de Nevados de Chillán con alerta de MIROVA, 2026-09-29 07:20 a 2026-11-02 07:30, 10 con cenit < 30° y 17 con ≥ 30°; todas nocturnas (dayflag 0 en 27), sun-glint mínimo 42,2°. Razón = magnitud del brazo / VRP de MIROVA en la misma pasada (pareo propio ±120 s, MODIS, `registro_vrp_consolidado.csv` del snapshot de f4ec1061d: 26 filas CONS y 1 sólo OCR, 2026-10-30 07:15, 1,0 MW; las 27 coinciden con `vrp_mirova_mw` del JSON; ninguna ≤ 0,05 MW, así que la regla SN no quita nada; `vara_y_records.out`). Cenit = `sensor_zenith_deg` del record guardado, igual al `z_record` del JSON en 27 de 27 y al del píxel MxD03 más cercano al centro de la grilla dentro de 0,17°.

| # | Afirmación | Veredicto | Mi número (script) |
|---|---|---|---|
| 1a | controles 27 de 27 ok | CONFIRMADA (es «corrió sin excepción»: `estado == ok` en 27, log `FIN: 27 ok de 27; errores 0`) | `releer.out` |
| 1b | K igual campo a campo al record guardado en las 27; `registros_iguales` falso por metadatos como `regimen.codigo_sha` | CONFIRMADA EN PARTE: `control_produccion_dif == []` en 27 (25 K, 2 V), y mi comparación de vrp, npix y pc da 0 diferencias; pero el falso en 27 es **por construcción** (VABLMODIS-03): la igualdad del record entero queda SIN DATO y la atribución es suficiente, no demostrada | `releer.out`, `vara_y_records.out` |
| 1c | V0 igual a V en 27 | CONFIRMADA: vrp_mw, npix y pc.vrp_mw iguales en 27 de 27 | `releer.out` |
| 1d | X2 dobla (1,89 / 2,12) y su única publicación perdida (2026-10-01 08:35, 11,44 MW) es la regla de cirrus | CONFIRMADA: medianas 1,893 / 2,115; X2/V0 2,000 ± 0,0004 en 26, 2,0073 en 1; celdas iguales en 27; única pasada con V publica 1 y X2 publica 0 es esa; node sobre V0 y X2 recalculados da [1, 0]; V0 t_max_k 269,57 K, `isCirrusArtifact` l. 1336-1340 | `releer.out`, `recalcular_npz.out` |
| 2 | K cae: 0,678 / 0,137, Spearman −0,90; V plana 0,947 / 1,054 | CONFIRMADA (K con `pc.vrp_mw`: 0,678 / 0,137, ρ −0,901, nulo95 [−0,39, +0,33], 5 ceros, todos a z > 57° con MIROVA ≤ 3,79 MW; con la suma de escena `vrp_mw` daría 0,699 / 0,203 y −0,870); V 0,947 / 1,054, ρ +0,250 dentro del nulo. Matiz: la mediana oblicua de V es mayor que la cercana en toda muestra jackknife (−0,156..−0,058), y dentro de Terra ρ +0,76 (n 10) | `analisis_2.out`, `por_sensor.out` |
| 3 | FA baja los dos tramos (0,488 / 0,351), ρ −0,38 en el borde del nulo, 6 ceros: el fondo baja el nivel, no hace la caída | CONFIRMADA EN PARTE: 0,488 / 0,351, ρ −0,384, nulo95 [−0,37, +0,46] (semilla 173, p 0,060; semilla 7, 2000 barajados, p 0,050), 6 ceros; **sin ceros ρ +0,006** (n 21) y medianas 0,488 / 0,471: en magnitud no hace la caída. Pero los 6 ceros son publicación perdida con detección intacta, 6 de 17 oblicuas contra 0 de 10 (VABLMODIS-02) | `releer.out`, `analisis_2.out` |
| 4 | NAT reproduce la caída (0,960 / 0,460, ρ −0,93); la pieza es el remuestreo (D17), al revés que en VIIRS 750 | número CONFIRMADO (0,960 / 0,460, ρ −0,927, jackknife −0,936..−0,921, sin ceros −0,913 n 23, dentro de Terra −0,976 y de Aqua −0,909); conclusión CONFIRMADA EN PARTE (VABLMODIS-01); «al revés que en VIIRS 750» SIN EVIDENCIA (no lo medí) | `releer.out`, `analisis_2.out`, `por_sensor.out` |
| 5 | G5 también la reproduce (0,985 / 0,415, ρ −0,75) | CONFIRMADA: 0,985 / 0,415, ρ −0,750, jackknife −0,804..−0,724, sin ceros −0,643 (n 23); mecanismo medido en VABLMODIS-01 | `releer.out`, `analisis_2.out` |
| 6 | NAT_AREA sobrecompensa (1,145 / 1,387): el remuestreo no equivale a multiplicar por el área | CONFIRMADA: 1,145 / 1,387; sobre 30° media sin ceros 1,978 y razón de sumas 2,033; NAT_AREA / NAT = 1/cos³(z) en los 23 no nulos (máx. 1 % de diferencia, `piezas.py:237-239`) | `releer.out` |
| 7 | FSH, SC y RN no mueven nada | SC CONFIRMADA (0 de 27 difieren de V0); FSH CONFIRMADA EN PARTE (vrp difiere en 27 de 27, FSH/V0 mediana 0,975 / 0,938, rango 0,49 a 1,85; medianas contra MIROVA 0,926 / 1,031); RN REFUTADA (VABLMODIS-04) | `releer.out`, `analisis_2.out` |

## 4. Hallazgos (ordenados por gravedad)

### VABLMODIS-01
- TÍTULO: El arnés no aísla el remuestreo: la geolocalización de 5 km de K (G5) hunde la razón oblicua por sí sola, y por la regla de lectura del README las dos piezas interactúan
- ARCHIVO:LÍNEA: `experiments/_s173_cenit_modis/README.md` (TEXTO) «Si dos brazos hunden la razón, las dos piezas interactúan y no se pueden adoptar por separado»; `piezas.py:264-267` (G5 = `preparar_grilla(rad, lat_5km, lon_5km, ...)`), `piezas.py:269` (NAT con `lat_mxd03, lon_mxd03`); SCRIPT:SALIDA `analisis_2.out` §(2) y §(3), `recalcular_npz.json`.
- QUÉ PASA: cuando el satélite mira de lado, la geolocalización que K interpola desde la grilla de 5 km corre el píxel del cráter: 1,51 km de mediana bajo 30° y 2,82 km sobre 30° (mín. 1,36, máx. 6,51 km; ρ(desplazamiento, cenit) +0,805). Sobre la grilla de la vía eso saca el cúmulo de la caja sensible de 5 × 5 celdas (±2 km) en 9 de 27 pasadas (G5 `pc_dist_km` > 2 km, z de 8,9° a 62,9°), donde rigen los umbrales conservadores, y G5 detecta 1 celda donde V0 detecta 8 a 13 (2026-10-01 08:35, 2026-10-28 07:35, 2026-10-30 08:55). G5/V0 mediana 1,051 bajo 30° y 0,349 sobre 30°, ρ(G5/V0, desplazamiento) −0,715. NAT no comparte esa causa (usa el MxD03; mi brazo NAT_G5, el detector nativo con la geolocalización de 5 km, difiere de NAT en 6 de 27: 4 baja, 2 sube, 1 a cero en 2026-10-25), pero el resultado es que dos piezas distintas de K bastan cada una para reproducir la caída, y el diseño de «reemplazar de a una» no puede decir cuál «corrige». El coordinador toma NAT como la pieza; el propio README dice que con dos brazos hundidos no se adopta por separado.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (producción corre la vía entera, con MxD03 y grilla). Decide qué palanca se tira si se desarma la vía: adoptar sólo el remuestreo sobre la geolocalización de K dejaría la caída de G5.
- CÓMO REPRODUCIRLO: `VRP_PROFILE=mirova_equivalent python C:/Users/nmend/vrp-wt/s173_cenit/ver_ablmodis/recalcular_npz.py` y luego `python -I analisis_2.py`; pasadas 2026-10-01 08:35 UTC (desplazamiento 2,44 km, G5 0,364 MW contra V0 5,721) y 2026-10-30 08:55 UTC (4,24 km, G5 1,70 contra V0 20,55).
- CONFIANZA: CONFIRMADO (medido; la interpretación de que las piezas interactúan es la regla del README, no un dato nuevo).
- GRAVEDAD: 4 (decide qué pieza se adopta; no cambia una alerta hoy).

### VABLMODIS-02
- TÍTULO: El fondo de K (FA) apaga la publicación en 6 de 17 pasadas oblicuas con la detección intacta: el fondo sí hace la caída en publicación, aunque no en magnitud
- ARCHIVO:LÍNEA: `piezas.py:67-74` (`t_bg_anillo`: mediana de BT MIR del anillo 5 a 25 km), `piezas.py:77-91` (`vrp_desde` con `recortar=True`: `dl = np.maximum(dl, 0.0)`), `piezas.py:124-127`; SCRIPT:SALIDA `analisis_2.out` §(4) y §(5).
- QUÉ PASA: en las pasadas oblicuas débiles el píxel de 1 km se llena de nieve y la celda alertada queda más fría que la mediana del anillo (en 7 de 27 records de la vía la celda más radiante está bajo 273,15 K; las 6 de FA tienen t_max_k 263,8 a 272,8 K): con el fondo de K el exceso es ≤ 0 y el recorte lo deja en 0,0 MW en las 6 (npix 1, 6, 3, 5, 9, 5: la vía detectó). Son 6 de 17 oblicuas (z 35,1° a 63,1°) y 0 de 10 bajo 30°; cinco coinciden con los 5 ceros de K (2026-09-29 07:20, 10-12 07:20, 10-15 01:05, 10-25 07:20, 10-30 07:15) y la sexta es 2026-10-10 07:40. Sin ceros el fondo sólo baja el nivel (FA/MIROVA 0,488 / 0,471, ρ +0,006; FA/V0 mediana 0,537 / 0,401, ρ −0,318). «El fondo no hace la caída» vale para la magnitud que sobrevive; en publicación el fondo solo reproduce los ceros de K.
- CÓMO SE VE EN EL DASHBOARD: con el fondo de K esas 6 pasadas salen sin alerta (publica 0 en las 6; V las publica las 6).
- CÓMO REPRODUCIRLO: `python -I analisis_2.py` §(4)-(5); pasada 2026-10-25 07:20 UTC (z 57,98°, MIROVA 3,79 MW, V0 2,553 MW en 9 celdas, FA 0,0 MW).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### VABLMODIS-03
- TÍTULO: `control_produccion_igual` (registros_iguales) no puede dar verdadero en este arnés: compara `regimen.codigo_sha`, que el store escribe con el `GITHUB_SHA` de la corrida
- ARCHIVO:LÍNEA: `repo_f4ec1061d/pipeline/store.py:89-94` (`_marca_regimen`: `{"perfil": ..., "codigo_sha": sha_actions, "origen": "actions"}`) y `:549` (`record["regimen"] = _marca_regimen()`); `probe_etiquetas.py:153-159` (`MARCAS_DE_HORA = ("processed_utc", "first_processed_utc")`, compara todo lo demás con `json.dumps`); `ablacion_cenit_modis.py:137`.
- QUÉ PASA: los 27 records guardados llevan 14 `codigo_sha` distintos (`34cea39e` en 11, ninguno `f4ec1061d`), y el record del runner lleva `f4ec1061d`: el comparador entero da falso siempre, con o sin diferencia real, así que es un control que no puede fallar al revés (A116). Lo informativo es `comparar_campos` (`ablacion_cenit_modis.py:78-89`: 7 campos, `pc.vrp_mw` y la lista lat/lon/vrp de píxeles), que da `[]` en 27. La atribución del coordinador a `regimen.codigo_sha` es una causa suficiente, no demostrada: el arnés no persiste qué claves difieren. Comprobé lo que se puede sin el record del runner: no hay commits en `pipeline/` entre `79f41069` y `f4ec1061d` (los 2 controles V), y los records K no llevan `via_codigo_mirova` con el flag apagado (`process_modis.py:1767`), así que esas claves no son la causa.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I releer.py` (bloque CONTROLES) y `python -I vara_y_records.py` (claves por sha).
- CONFIANZA: CONFIRMADO (el porqué estructural); SIN DATO para «es la única diferencia».
- GRAVEDAD: 2.

### VABLMODIS-04
- TÍTULO: RN (vecino más cercano) no es inerte: cambia celdas y magnitud en 27 de 27 y agrega una tendencia positiva con el cenit; FSH tampoco es inerte en magnitud
- ARCHIVO:LÍNEA: `piezas.py:146-164` (`remuestrear_vecino`), `piezas.py:259-263`; SCRIPT:SALIDA `releer.out` (tabla «brazos contra V0» y fila RN), `analisis_2.out` §(7), `por_sensor.out`.
- QUÉ PASA: copiar el píxel grande sin suavizar reparte más radiancia por celda en las oblicuas: RN/V0 mediana 1,041 bajo 30° y 1,178 sobre 30° (rango 0,122 a 1,911); RN/MIROVA medianas 0,962 / 1,104, Spearman +0,500 con nulo95 [−0,37, +0,39] (p 0,000 con 200 barajados; con el barajado dentro de plataforma [−0,13, +0,46], en el borde), jackknife +0,440..+0,590. FSH (sin halo) cambia la magnitud en 27 de 27 (FSH/V0 0,489 a 1,853, medianas 0,975 / 0,938) sin patrón de cenit. SC sí es inerte (idéntico a V0 en 27). «No mueven nada» vale para SC y, en lo que al cenit respecta, para FSH; para RN es falso.
- CÓMO SE VE EN EL DASHBOARD: invisible (RN no está en producción).
- CÓMO REPRODUCIRLO: `python -I releer.py` (fila RN de la tabla de razones) y `python -I analisis_2.py` §(7) (RN/V0 por tramo, mín. 0,122, máx. 1,911).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VABLMODIS-05
- TÍTULO: La regla de cirrus del tablero (t_max_k < 273,15 K y > 10 MW) alcanza a los records de la vía en Chillán oblicuo: 7 de 27 records V0 tienen la celda más radiante bajo 0 °C
- ARCHIVO:LÍNEA: `frontend/index.html` de f4ec1061d l. 1336-1340 (`isCirrusArtifact`: `r.t_max_k < 273.15` y `mirovaEqVrp(...) > 10`) y l. 1425; `mirova_v750_codigo.py:725-734` (t_max_k de la vía = BT de la celda pico de la grilla interpolada); SCRIPT:SALIDA `recalcular_npz.out` (línea PREDICADO), `analisis_2.out` §(8).
- QUÉ PASA: la interpolación lineal a la grilla baja el pico, y un píxel oblicuo de 1 km mezclado con nieve queda bajo 0 °C aunque MIROVA publique 2 a 5 MW: V0 t_max_k 263,8 a 272,8 K en 7 pasadas (todas z ≥ 35°, V0 de 0,14 a 5,72 MW). La regla, calibrada sobre records de K, se dispara en cuanto la magnitud pasa de 10 MW: X2 lo mostró (11,442 MW, publica 0 con node). Hoy ninguna de las 7 supera 10 MW, así que no hay alerta real oculta en estas 27; con una erupción el doble de fuerte vista a 50° la habría.
- CÓMO SE VE EN EL DASHBOARD: una alerta de la vía de más de 10 MW con t_max_k bajo 273,15 K se atenúa como «artefacto cirrus» y no entra al gráfico ni a la publicación.
- CÓMO REPRODUCIRLO: `VRP_PROFILE=mirova_equivalent python recalcular_npz.py 2026-10-01_0835` (imprime el predicado node para V0 y X2).
- CONFIANZA: CONFIRMADO para X2 y para los 7 t_max_k; SOSPECHA para un caso real futuro.
- GRAVEDAD: 3 (puede ocultar una alerta fuerte oblicua; hoy no ocurre en estas 27).

### VABLMODIS-06
- TÍTULO: NAT_AREA es NAT × sec³(z) exacto; la sobrecompensación queda sin mecanismo medido
- ARCHIVO:LÍNEA: `piezas.py:235-239`; SCRIPT:SALIDA `releer.out` (NAT_AREA/NAT por pasada).
- QUÉ PASA: NAT_AREA/NAT coincide con 1/cos³(z) en los 23 no nulos (máx. 1 % de diferencia), así que el brazo es un escalado; sobre 30° da mediana 1,387, media sin ceros 1,978 y razón de sumas 2,033 contra MIROVA. La afirmación (6) se confirma como medición; por qué el remuestreo rinde la mitad del área nominal (bow tie D28 contando dos veces el mismo suelo en el barrido nativo, o la interpolación lineal que no conserva el área) no está medido aquí.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I releer.py`; pasada 2026-10-30 08:55 UTC: sec³ 10,56, NAT 0,445, NAT_AREA 4,745, V 1,428.
- CONFIANZA: CONFIRMADO (el escalado); SOSPECHA (el mecanismo).
- GRAVEDAD: 1.

### VABLMODIS-07
- TÍTULO: «V plana» esconde una mediana oblicua sistemáticamente mayor y una tendencia dentro de Terra
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `analisis_2.out` §(6), `por_sensor.out`.
- QUÉ PASA: V/MIROVA 0,947 bajo 30° y 1,054 sobre 30°; la diferencia de medianas es negativa en todas las muestras jackknife (−0,156..−0,058); dentro de Terra (n 10) ρ +0,758 con medianas 0,768 / 1,189, dentro de Aqua ρ −0,027. Con n 27 el Spearman global (+0,250) queda dentro del nulo; «plana» es correcto como ausencia de tendencia significativa, no como igualdad de tramos.
- CÓMO SE VE EN EL DASHBOARD: invisible (del orden de 10 %).
- CÓMO REPRODUCIRLO: `python -I por_sensor.py`.
- CONFIANZA: CONFIRMADO (los números); SOSPECHA (que sea algo más que n chico).
- GRAVEDAD: 1.

## 5. SEGUIMIENTOS (fuera de mi eje)

- S-1. `pasadas_chillan_modis.json` declara `razon_V_lectura_ab` en 16 pasadas y el README dice que V / MIROVA se controla contra ella; el JSON del artefacto no trae ese control ni el arnés lo calcula (`ablacion_cenit_modis.py` no lee el campo). SIN DATO sobre si V calza con el A/B de MOD-D. Confianza: CONFIRMADO que no está en el artefacto. Archivo: `ablacion_cenit_modis.py:109-178`.
- S-2. El OCR del scraper trae valores distintos de la tabla en 5 pasadas (p. ej. 2026-10-17 02:20: tabla 12,97, OCR 12,0; 2026-10-30 08:55: 14,39 contra 14,0); el arnés usó la tabla (`fuente_M: CONS`) en 26 y el OCR sólo donde la tabla no tiene fila (2026-10-30 07:15). Coherente con S159; lo anoto porque la ventana pisa los dos hitos de A119 (aviso de `calidad_referencia_mirova.avisar`, ambos sobre filas sólo OCR). `vara_y_records.out`.
- S-3. 'publica' None en NAT y NAT_AREA: por `ablacion_cenit_modis.py:159` los brazos nativos no arman record y el predicado del tablero no se evalúa. Para esta comparación no sesga: la distancia mínima del cúmulo al cráter es ≤ 1,89 km en los 23 no nulos (todos «summit»), y los 4 ceros son npix 0 (no detección). Lo que queda SIN DATO es la regla de cirrus sobre NAT (no hay t_max_k nativo): 3 pasadas de NAT superan 10 MW (2026-10-16 08:15, 10-27 08:35, 10-28 01:20).
- S-4. K guarda `pc.vrp_mw = 0.0` con `npix 1` en 2026-10-25 07:20 (record guardado y K del runner): un píxel detectado con magnitud 0 (`vara_y_records.out`). No lo perseguí; confianza CONFIRMADO el dato, SOSPECHA la causa (tope o recorte).

## 6. VERIFICADO LIMPIO

- Reproducción desde los recortes: V0, NAT y G5 recalculados con `piezas.py` de f4ec1061d sobre `nativos/*.npz` calzan con el JSON en 27 de 27 (vrp_mw, npix y celdas de V0). Vara: el JSON del runner. `recalcular_npz.out`.
- Control positivo del lector: X2/V0 = 2,000 ± 0,0004 en 26 y 2,0073 en 1 (0,137 → 0,275 MW, redondeo a 3 decimales); celdas iguales en 27. `releer.out`.
- Pareo por pasada y vara: las 27 `Fecha_Satelite_UTC` tienen fila MODIS de Chillán en el consolidado del snapshot de f4ec1061d al minuto exacto (26) o sólo en el OCR (1); VRP igual al del JSON en 27; ninguna ≤ 0,05 MW. Vara: `registro_vrp_consolidado.csv` y `registro_vrp_ocr.csv` del commit. `vara_y_records.out`.
- Cenit: `z_record` = `sensor_zenith_deg` del record guardado en 27 de 27; contra el MxD03 (píxel más cercano al centro) máx. 0,17°. `vara_y_records.out`, `releer.out`.
- Confusor temporal: ρ(cenit, orden de fecha) +0,009; ρ(razón K, fecha) +0,083; fechas de los dos tramos entremezcladas (ambos cubren del 1 al 31 de octubre). `releer.out`.
- Confusor de plataforma: la caída de K, NAT y G5 se repite dentro de Terra (ρ −0,94, −0,98, −0,77; n 10) y dentro de Aqua (−0,82, −0,91, −0,73; n 17); nulo barajando el cenit dentro de cada plataforma [−0,48, +0,18] para K. `por_sensor.out`.
- Nulo con otra semilla (7) y 2000 barajados: K p < 0,0005, NAT p < 0,0005, G5 p < 0,0005, V p 0,21, FA p 0,050, NAT_AREA p 0,28. `releer.out`.
- Jackknife (sacar una pasada): K −0,896..−0,857 (suma) y diferencia de medianas +0,536..+0,549 (pc); NAT −0,936..−0,921; G5 −0,804..−0,724; FA −0,441..−0,321. Ninguna pasada sola sostiene los Spearman. `releer.out`, `analisis_2.out`.
- Corrida y commit: `gh api .../runs/41588951267` → `head_sha f4ec1061d`, `success`, `workflow_dispatch`; `procedencia.txt` y `commit` del JSON iguales; log `FIN: 27 ok de 27; errores 0`. Workflow: `"on":` entre comillas, sólo `EARTHDATA_TOKEN`, corta si vacío, `upload-artifact@v4`, comentario «NO hace push» (no verifiqué permisos línea a línea más allá del grep).
- `otro_granulo` falso en 27 (el gránulo bajado es el del record).

## 7. SIN DATO

- Igualdad del record K entero contra el guardado (VABLMODIS-03): el arnés no persiste el diff y no puedo correr K en Windows (pyhdf).
- Mi esfuerzo de inferencia real (ver encabezado).
- «Al revés que en VIIRS 750»: no medido aquí.
- `razon_V_lectura_ab` contra V (S-1).
- Regla de cirrus sobre los brazos nativos (S-3).
- Mecanismo de la sobrecompensación de NAT_AREA (VABLMODIS-06).

## 8. FUERA DE ALCANCE

Informe del auditor y de otros verificadores (no leídos); `leer.py`; código `.m` de MIROVA; TIF de MIROVA; bow tie D28; cualquier arreglo (no toqué nada fuera de esta carpeta; nada en `pipeline/`, `data/`, `frontend/`; ni commit ni push).
