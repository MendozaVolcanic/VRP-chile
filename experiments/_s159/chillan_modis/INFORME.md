# S159, frente Chillán MODIS: por qué el primer pase no ve las dos alertas protegidas a 58° de cenit

Worktree `C:\vrp-trabajo\s159-m`, rama `s159-chillan` (cortada de `origin/s159-pruebas`, `db3e9cbb4`). Sólo lectura:
nada en `pipeline/`, `data/` ni `frontend/`; lo que se cambió para medir se cambió en memoria dentro del probe (A75).
Fecha 2026-10-21. Criterio sellado en `PREREGISTRO.md` antes del primer despacho, con una adenda declarada antes del
tercero (se dice abajo qué es preregistrado y qué es exploratorio).

Runs (rama auxiliar `s159-chillan-disparo`, no mergear):
- `39692284700`: cayó en los 7 gránulos con `IndexError` (mi envoltorio leía argumentos posicionales y
  `calculate_vrp` llama por nombre). No produjo datos; se corrigió enlazando a la firma (`inspect.signature`).
- `39692725826`: medición preregistrada. Datos en `resultado/run39692725826/`.
- `39693552091`: mismo probe más los brazos de la adenda (SC, MIN, MINSC hasta el record). Datos en
  `resultado/run39693552091/`. El brazo P de los dos runs es idéntico (0 diferencias en 12 campos × 7 gránulos,
  `resultado/resumen_salida.txt` l. 1).

## Las dos preguntas del instrumento (valen para todo lo que sigue)

1. **¿Vería un primer pase roto?** Sí. El probe llama a la función de producción y, aparte, replica sus cuentas paso a
   paso (`replica.py`) para exponer dNTI, dETI, umbral y compuerta de cada píxel. La réplica tiene que dar la MISMA
   máscara que la original: dio idéntica en 7 de 7 gránulos, en el primer y en el segundo pase
   (`resultado/run39693552091/analizar_salida.txt`, líneas «CONTROL instrumento»). Prueba sintética previa:
   `probar_replica.py`, 32 combinaciones idénticas y control de compuerta (BT fría: con compuerta no, sin compuerta sí).
2. **¿Se vería distinto con el instrumento muerto?** Sí. El record que arma el probe con `store.append_record`
   reproduce el publicado en `data/mirova_equivalent/NevadosDeChillan.json` en 6 de 7 gránulos (diagnósticos del primer
   y segundo pase iguales, `t_bg`, μ y σ del dNTI con diferencia relativa 0,0). El séptimo (E2) no reproduce y queda
   SIN DATO (H5). **Control positivo**: C1, C2 y C3 (protegidas publicadas, cenit 50,5°, 54,0° y 3,2°) pasan las
   cuatro etapas con el mismo instrumento, y el predicado del tablero ejecutado con node da publicado en los tres y no
   publicado en T1 y T2, como hoy (`resultado/run39693552091/publicacion_salida.txt`; identidad del predicado
   `([0, 1, 1, 1, 0], [1, 0])`, la esperada).

Denominadores y ventana: 7 gránulos MODIS de Nevados de Chillán, 2026-09-29 a 2026-10-17. El estrato de alertas sale de
`estrato.py` (referencia unificada, filas MODIS de Chillán del 2026-09-01 al 2026-10-21, pareo a ±5 min con nuestros
106 records MODIS de esa ventana): 211 filas de MIROVA, 22 de alerta, 16 pasadas protegidas (lectura A); de esas 16,
11 publicadas, 2 no publicadas con record (T1 y T2) y 3 sin record (diurnas). Pareo a ±5 min: ninguna fila de alerta
pareó con más de un record (`n_cand` vale 1 o 0 en las 22, `estrato_tabla.json`).

## Hallazgos, de mayor a menor gravedad

### H1. T1 y T2 caen por el Test 2 bajo la conectiva `max`, y aunque se detectaran la magnitud saldría 0 MW: la cumbre está más fría que el anillo
- **SCRIPT:SALIDA**: `resultado/run39693552091/analizar_salida.txt` (bloques T1 y T2), `resultado/resumen_salida.txt`,
  `resultado/vecindad_salida.txt`, `resultado/run39693552091/publicacion_salida.txt`. Código:
  `pipeline/detection_context.py:525` (`combinar = max if use_prose_branch else min`), `:546` (compuerta),
  `pipeline/process_modis.py:1083`, `:1113` y `:1118` (fondo escalar del anillo y recorte `ΔL ≥ 0`).
- **QUÉ PASA (el fenómeno)**: de noche, la cumbre de Chillán (nieve, 3.200 m) está mucho más fría que el terreno de 5 a
  25 km que forma el anillo de fondo: la TIR (banda 31) del píxel del cráter queda 9,7 K (T1) y 12,4 K (T2) bajo la
  mediana del anillo. A 58° de cenit el píxel MODIS es grande (en T1 los dos vecinos de la misma línea están a 3,47 km
  del cráter, `vecindad_salida.txt`), y la lava ocupa una fracción mínima: el mejor píxel dentro de los 5 km tiene un exceso
  de MIR sobre TIR de 6,5 K (T1) y 9,1 K (T2), contra 10,5 a 29,8 K en los gránulos donde publicamos. O sea, hay calor
  volcánico en el píxel, pero no alcanza a levantarlo sobre un fondo que es más tibio que la cumbre por altitud.
- **QUÉ PASA (el código)**, etapa por etapa, sobre el mejor píxel dentro del inner (T1 a 3,47 km, T2 a 2,39 km; los
  dos en la zona de cumbre, así que rige el umbral de cumbre, no el de escena):
  1. **Saturación: no.** 0 DN > 32767 en las bandas 21 y 22 de los 21 (T1) y 18 (T2) píxeles a 4 km o menos; BT 22
     máxima 276,1 y 270,0 K, lejos de saturar.
  2. **Test 2 (dNTI): falla.** dNTI 0,0147 contra umbral 0,0194 (T1) y 0,0136 contra 0,0183 (T2). El umbral lo pone la
     rama estadística μ + 5σ (σ del dNTI 0,0039 y 0,0037; C1 = 0,003 no gobierna en ninguno de los 7 gránulos). En
     unidades de esa σ el píxel está a 3,78σ y 3,72σ, cuando hace falta 5; los controles dan 14,5σ a 36σ (E2, publicado por el segundo pase, 9,4σ).
     Le faltan 0,0047 de dNTI, equivalentes a +1,5 K (T1) y +1,4 K (T2) de BT MIR con la TIR fija.
  3. **Test 3 (dETI): pasa** (0,0125 contra 0,0096; 0,0138 contra 0,0101).
  4. **Compuerta de 3 K (D22): falla.** BT MIR − t_bg = −3,70 K y −4,37 K; pide más de +3 (faltan 6,7 y 7,4 K).
  5. **Magnitud: saldría 0.** Con la conectiva `min` en los dos pases (brazo MIN) el segundo pase sí detecta: 1 píxel a
     3,40 km (T1) y 2 a 0,92 km de centroide (T2), clase `summit`, pero `pc.vrp_mw` = 0,0 y el tablero no publica: la
     BT MIR del píxel está bajo `t_bg`, así que `ΔL` contra el fondo del anillo es negativo y se recorta a 0. Para
     tener magnitud mayor que cero el píxel tendría que subir 3,7 K (T1) y 4,4 K (T2), más de lo que pide el Test 2.
- **Contrafactuales preregistrados** (dentro del inner, run 39692725826): producción 0; F1 sin compuerta 0; F2 `min`
  sólo en el primer pase 0; F4 σ de los controles (mediana 0,00355) 0; B21 primaria 0; **F3 (`min` y sin compuerta)
  2 en T1 y 3 en T2**. Con la regla sellada, **ningún candidato único es la causa**: el preregistro no tenía regla para
  dos factores que sólo actúan juntos, y se informa así.
- **Lectura de la adenda (exploratoria)**: la compuerta no es la barrera que decide la DETECCIÓN en producción, porque
  el segundo pase, con `enable_second_pass_conditioned: false` (`pipeline/profiles/mirova_equivalent.yaml:440`), corre
  aunque el primero venga vacío y no aplica compuerta (H2): con `min` en los dos pases detecta aun con la compuerta
  puesta (brazo MIN), y sin compuerta pero con `max` no detecta (brazo SC). La barrera de detección es el Test 2 con la
  rama μ + 5σ; la de PUBLICACIÓN es el fondo de anillo con recorte. Las dos vienen del mismo fenómeno: comparar la
  cumbre fría contra un fondo tibio.
- **Lo que la compuerta mide en realidad** (`resumen_salida.txt`, dos últimas líneas): el mejor píxel de T1 (269,23 K)
  queda a −3,70 K de su propio `t_bg` (272,94) pero a +3,93 K del `t_bg` de C1 (265,30), que sí pasaría. En C1 la
  compuerta pasó porque esa noche el anillo estaba 7,6 K más frío, no porque el volcán estuviera más caliente.
- **CÓMO SE VE EN EL DASHBOARD**: el 2026-10-12 y el 2026-10-15 no hay barra MODIS en Chillán cuando MIROVA alertó 2,18
  y 1,72 MW; la noche sí se publicó en otra pasada (#864). Invisible para el operador que sólo mira la noche; visible
  como hueco en la serie MODIS.
- **CÓMO REPRODUCIRLO**: `python experiments/_s159/chillan_modis/analizar.py
  experiments/_s159/chillan_modis/resultado/run39693552091/probe_chillan.jsonl` (y `resumen.py`, `vecindad.py`,
  `publicacion.py` sobre el mismo jsonl). Pasadas: MYD021KM.A2026285.0720 (2026-10-12 07:20 UTC) y
  MOD021KM.A2026288.0105 (2026-10-15 01:05 UTC). Para rehacer el probe: push a `s159-chillan-disparo`.
- **CONFIANZA**: CONFIRMADO (medido y reproducido; la réplica es idéntica a producción).
- **GRAVEDAD**: 3. Dos protegidas perdidas en MODIS durante una erupción; la noche quedó cubierta por otra pasada. El
  mecanismo no es de Chillán: cualquier cumbre nevada vista de lado, con alerta débil, cae igual (SOSPECHA de alcance,
  no medido fuera de estos 7 gránulos).
- **Decisión para Nicolás (no es una propuesta de arreglo)**: las palancas que moverían estas dos pasadas son la
  conectiva (`max` entró a producción en S153 con el detector K, según la regla de adopción citada en el `CLAUDE.md`
  del proyecto; no la volví a medir) y
  el fondo de la magnitud (D25 no existe en `process_modis`, D-26; R2-6 de `docs/AUDIT_S158_R2.md` ya midió 37 records
  MODIS en 0 MW por este recorte). Cualquiera de las dos sola no basta en T1 y T2.

### H2. El segundo pase sin condicionar deshace la compuerta de 3 K del primero
- **ARCHIVO:LÍNEA**: `pipeline/detection_context.py:906` (sólo se salta con `conditioned=True`), `:943` y siguientes
  (sin compuerta de BT); `pipeline/process_modis.py:995`; perfil `mirova_equivalent.yaml:440`.
- **QUÉ PASA**: un píxel que pasa los Tests 2 y 3 pero no tiene 3 K sobre el fondo se cae en el primer pase y vuelve en
  el segundo, que re-evalúa toda la escena con los mismos umbrales y sin compuerta. El docstring de S135 ya lo dice
  («correrlo igual lo convierte en una segunda detección más permisiva»). Medido: E2 (2026-10-17 08:50, cenit 62,8°)
  se publica sólo por el segundo pase (primer pase 0, segundo pase 2, mejor píxel a 0,15 K de la compuerta), y en T1
  y T2 el brazo MIN detecta con el primer pase vacío.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; cambia qué píxeles entran, no cómo se dibujan.
- **CÓMO REPRODUCIRLO**: bloque E2 de `resultado/run39693552091/analizar_salida.txt` y brazo MIN en
  `publicacion_salida.txt`.
- **CONFIANZA**: CONFIRMADO en el código y en T1/T2 (brazo MIN); en E2 el número viene de un gránulo NRT que no
  reproduce el record (H5), así que E2 ilustra, no prueba.
- **GRAVEDAD**: 2. Cualquier A/B de D22 que mida sólo el primer pase mide un efecto que el segundo pase deshace (A118).

### H3. E1 (0,13 MW a 58,4°): la señal no está en el píxel a esta resolución
- **SCRIPT:SALIDA**: bloque E1 de `analizar_salida.txt`; `resumen_salida.txt`.
- **QUÉ PASA**: el mejor píxel dentro del inner no tiene exceso de MIR sobre TIR (−0,02 K) y su dNTI está a 2,1σ; ningún
  contrafactual detecta, ni F3 (dETI 0,00075 bajo el piso C1 de 0,003). Es la conclusión «señal bajo el piso» del
  preregistro.
- **CÓMO SE VE EN EL DASHBOARD**: sin barra MODIS el 2026-09-29 07:20; alerta no protegida.
- **CÓMO REPRODUCIRLO**: MYD021KM.A2026272.0720, mismo comando que H1.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

### H4. Tres protegidas diurnas sin record (estrato aparte)
- **SCRIPT:SALIDA**: `estrato_salida.txt`: 2026-10-14 13:05 (6,98 MW), 2026-10-16 12:45 (13,63 MW), 2026-10-17 20:50
  (11,94 MW) UTC, sin record nuestro a ±5 min. El pipeline MODIS es sólo nocturno (`ENABLE_DAYTIME_MODIS` apagado).
- **QUÉ PASA**: no es un defecto del primer pase; es la decisión de no procesar el día, ya anotada como MEJ-6 en
  `docs/BEYOND_MIROVA_EXTENSIONS.md` §12 y en D-10.
- **CÓMO SE VE EN EL DASHBOARD**: sin barra MODIS diurna, como en todos los volcanes.
- **CONFIANZA**: CONFIRMADO el conteo; que el criterio de victoria cuente o no las diurnas: SOSPECHA, no lo leí en
  `docs/MISSION.md`. **GRAVEDAD**: 2.

### H5. E2 no reproduce el record publicado: SIN DATO para ese gránulo
- **SCRIPT:SALIDA**: bloque E2 de `analizar_salida.txt` (`mu_dnti` relativo 0,057, `pc.vrp_mw` 0,535 contra 0,538).
- **QUÉ PASA**: el probe bajó la versión `6.1NRT` (`MYD021KM.A2026290.0850.061.2026290101145.NRT.hdf`) porque la búsqueda
  de la estándar no devolvió nada, y el record publicado es de la estándar (`.061.2026292010016`) y además lo escribió
  otro `codigo_sha` (`cf272543`, contra `34cea39e` de los otros). No separé cuál de las dos cosas explica la diferencia.
- **CONFIANZA**: CONFIRMADO que no reproduce; la causa, SOSPECHA. **GRAVEDAD**: 1 (instrumento).

## Contexto físico (sin uso causal)

TIR del cráter menos mediana del anillo: −7,9 (C3, nadir), −2,1 (C1), −5,1 (C2), −8,1 (E2), −12,4 (T2), −9,7 (T1),
−12,1 K (E1). La cumbre siempre está más fría que el anillo; en T1, T2 y E1 lo está más. En T1 la fila siguiente del
cráter (0,3 km) da 254 K en MIR y 252 K en TIR, 12 y 11 K bajo el píxel del cráter: nube o nieve en la cumbre, SOSPECHA. La banda 21
no ayuda: a estas temperaturas está cuantizada (en T1, 23 cuentas separan 250,5 de 266,4 K) y difiere de la 22 hasta
4,3 K entre vecinos. La hipótesis D17 (MIROVA remuestrea a 1 km y su VRP con área fija suma varias celdas del mismo
píxel grande) sería una explicación de por qué MIROVA da 2 MW donde nuestro píxel no tiene exceso sobre el anillo:
SOSPECHA, no medida aquí.

## VERIFICADO LIMPIO

- **Saturación en los 7 gránulos**: 0 DN > 32767 en las bandas 21 y 22 a 4 km o menos del cráter y 0 BT MIR no finitas
  (`grep "saturacion" resultado/run39693552091/analizar_salida.txt`). Con esto el probe de saturación de #880 queda
  contestado para MODIS en estas pasadas: no satura.
- **Banda primaria**: B21 primaria da 0 píxeles dentro del inner en T1, T2 y E1 (`grep "B21" .../analizar_salida.txt`).
- **σ del fondo**: la σ del dNTI de T1 y T2 (0,0039, 0,0037) está dentro del rango de los controles (0,0021 a 0,0039),
  y con la σ de los controles (F4) sigue en 0. La σ del anillo de BT (`diag_sigma_bg_k` 9,7 y 6,3 K) no entra al primer
  pase: `first_pass_tests_2_and_3` sólo usa `t_bg`, en la compuerta (`pipeline/detection_context.py:546`).
- **Máscara de nube**: `cloud_mask_bt_k: 0.0` (`pipeline/profiles/mirova_equivalent.yaml:53`), usada en
  `pipeline/process_modis.py:621`: no descarta píxeles. La compuerta atmosférica del camino D está apagada
  (`PATH_D_ATM_GATE_TBG_MIN_K = None`, leído de `pipeline.profile`), así que el primer pase sí corrió (`n_bg` 761 y 792).
- **Umbral de escena contra cumbre**: todos los candidatos están en la zona de cumbre (`inner_radius_km: 5`,
  `volcanoes.yaml:255`); el umbral de escena no interviene.
- **Geolocalización**: no la volví a medir; el frente M (`experiments/_s159/m/INFORME.md` H4) ya mostró que con MxD03
  tampoco detecta.
- **Réplica e instrumento**: réplica idéntica 7 de 7 (primer y segundo pase), record reproducido 6 de 7, nulo de
  ejecución entre runs 0 diferencias, controles positivos C1 a C3 pasan, predicado del tablero con identidad correcta.
- Comandos: `python experiments/_s159/chillan_modis/probar_replica.py` (local, sin HDF);
  `python experiments/_s159/chillan_modis/analizar.py <jsonl>`; `python experiments/_s159/chillan_modis/resumen.py
  <jsonl run 39692725826> <jsonl run 39693552091>`; `python experiments/_s159/chillan_modis/publicacion.py <jsonl>`;
  `python experiments/_s159/chillan_modis/estrato.py`.

## Candidatas para BEYOND_MIROVA_EXTENSIONS §12

| id propuesto | qué | por qué podría ser mejor | evidencia | estado |
|---|---|---|---|---|
| MEJ-a | **Fondo local para la cumbre en pasadas oblicuas** | En una cumbre nevada vista a 58°, el anillo de 5 a 25 km es más tibio que la cumbre y anula la magnitud de un píxel con exceso real de MIR sobre TIR (6,5 a 9,1 K). Un fondo de vecinos o de la misma altitud seguiría a la cumbre fría. Es la cara MODIS de D25 | este informe H1; R2-6 de `docs/AUDIT_S158_R2.md` | idea; medir contra OVDAS o SWIR, no contra MIROVA |
| MEJ-b | **Usar el exceso MIR menos TIR como indicio en el perfil experimental** | En estos 7 gránulos separa T1 y T2 (6,5 y 9,1 K) de E1 (−0,02 K) y no depende del fondo del anillo; podría marcar «calor débil en pasada oblicua» sin pasar por la compuerta ni por la magnitud | este informe, `resultado/resumen_salida.txt` | idea; sin tasa base en negativos limpios |
| MEJ-c | **Marca de pasada oblicua sobre cumbre fría** | Complementa MEJ-9 del frente M: separar «el sensor no podía ver» de «no había nada» cuando el cenit pasa de ~55° y la TIR del cráter queda más de 8 K bajo el anillo | este informe H1 y contexto físico; `experiments/_s159/m/INFORME.md` MEJ-9 | idea |
