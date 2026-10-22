# S159, frente Chillán MODIS: preregistro

Sellado antes del primer despacho del probe (rama `s159-chillan`). Sólo lectura: nada en `pipeline/`, `data/` ni
`frontend/`. Lo que se cambia para medir se cambia en memoria, dentro del probe, con envoltorios (A75).

## Pregunta

Por qué el primer pase de producción (`first_pass_tests_2_and_3`, Tests 2 y 3 de Coppola 2016a con la conectiva
`max`, dual ROI y compuerta de 3 K) no marca ningún píxel en dos pasadas MODIS de Nevados de Chillán en que MIROVA
publicó alerta protegida (lectura A, 1 MW o más):

| id | gránulo | MIROVA | cenit en el record |
|---|---|---|---|
| T1 | MYD021KM.A2026285.0720 | 2026-10-12 07:20, 2,18 MW a 2,24 km | 58,19° |
| T2 | MOD021KM.A2026288.0105 | 2026-10-15 01:05, 1,72 MW a 2,24 km | 57,58° |

Estratos agregados (salen de `estrato.py`, pareo a ±5 min contra la referencia unificada, septiembre y octubre de 2026):

| id | gránulo | por qué entra |
|---|---|---|
| E1 | MYD021KM.A2026272.0720 | alerta MIROVA no protegida (0,13 MW), no publicada, cenit 58,4°, primer pase 0 |
| E2 | MYD021KM.A2026290.0850 | protegida (7,09 MW) publicada con primer pase 0 y 2 píxeles del segundo pase, cenit 62,8° |
| C1 | MYD021KM.A2026274.0835 | control positivo oblicuo: protegida publicada, cenit 50,5°, primer pase 2 |
| C2 | MOD021KM.A2026290.0220 | control positivo oblicuo: protegida publicada, cenit 54,0°, primer pase 1 |
| C3 | MOD021KM.A2026289.0140 | control positivo nadir: protegida publicada, cenit 3,2°, primer pase 2 |

Las tres protegidas sin record nuestro (2026-10-14 13:05, 2026-10-16 12:45, 2026-10-17 20:50 UTC) son pasadas diurnas;
el pipeline MODIS es sólo nocturno (`ENABLE_DAYTIME_MODIS` apagado). Se informan como estrato aparte y no se sondean.

## Qué se mide

Por gránulo, con la función de producción `process_modis.calculate_vrp` y los argumentos de
`scripts/run_pipeline.py:235-245`, envolviendo `first_pass_tests_2_and_3` y `second_pass_adjacent` (se llama a la
original; el envoltorio sólo copia entradas y salidas) y `read_modis_l1b` (para guardar las radiancias):

1. Para cada píxel a 4 km o menos del ancla (`get_detection_anchor`), y su vecindad de 3 × 3 alrededor del más
   cercano: DN crudo de las bandas 21, 22 y 31, BT 21, 22, MIR mezclada y 31, NTI, NTI_app, ETI, media de 8 vecinos,
   dNTI, dETI, umbral de cada test en su zona (cumbre o escena), qué rama gobierna el umbral (C1 o μ + C2·σ), si pasa
   Test 2, Test 3 y la compuerta `bt > t_bg + 3 K`, y las mismas cantidades del segundo pase.
2. Lo que habría hecho falta: el ΔNTI que le falta al mejor píxel dentro del inner (5 km) para pasar los dos tests
   (el ETI sube lo mismo que el NTI si la TIR no cambia, porque NTI_bk depende sólo de NTI_app, que sale de la TIR),
   la radiancia MIR y la BT MIR equivalentes con la TIR fija, y la BT que pide la compuerta.
3. Contrafactuales, todos dentro del envoltorio o con un global del módulo cambiado en memoria:
   F1 sin compuerta de 3 K (`apply_bt_gate=False`), F2 conectiva `min`, F3 las dos, F4 la σ del dNTI y del dETI del
   gránulo reemplazada por la mediana de los tres controles, y B21 (`ENABLE_MODIS_B22_PRIMARY = False`, corrida
   completa de `calculate_vrp`). Se cuenta cuántos píxeles del primer pase caen dentro del inner en cada uno.
4. Contexto físico, sin uso causal: BT 31 del píxel del cráter contra la mediana del anillo de 5 a 25 km (una nube
   enfría la TIR del cráter); factor de área del píxel con `modis_pixel_areas(nadir_fixed=False)` en el cráter.

## Qué cuenta como «la causa es X» (decidido antes de ver los datos)

La etapa en que cae una pasada es la PRIMERA que falla, en este orden, para el mejor píxel dentro del inner (el de
mayor `min(dNTI − umbral_dNTI, dETI − umbral_dETI)`): (a) valor finito en el ROI, (b) Test 2, (c) Test 3,
(d) compuerta de 3 K. Además, por candidato:

- **Saturación**: es causa si algún píxel a 4 km o menos trae DN > 32767 en la banda 22 y queda NaN en la BT MIR, o
  si la banda 21 que lo reemplaza da un valor que pasaría. Se descarta si hay 0 DN > 32767 en 21 y 22 a 4 km o menos
  y todos los valores son finitos.
- **Compuerta de 3 K (D22)**: es causa si F1 da 1 o más píxeles dentro del inner y producción da 0.
- **Conectiva `max`**: es causa si F2 da 1 o más píxeles dentro del inner y producción da 0.
- **Fondo (σ del dNTI o dETI)**: es causa si F4 da 1 o más píxeles dentro del inner y producción da 0. La σ del
  anillo de BT (`diag_sigma_bg_k`) no entra al primer pase (sólo `t_bg`, en la compuerta); eso se confirma leyendo
  el código y se informa.
- **Banda primaria**: es causa si B21 da 1 o más píxeles dentro del inner.
- **Señal bajo el piso**: si ningún contrafactual (F1 a F4, B21) da un píxel dentro del inner, y en particular si F3
  (umbral = C1 = 0,003 y sin compuerta) da 0, el mejor píxel tiene un contraste de NTI menor que el piso del paper: la
  señal no está en el píxel del gránulo a esta resolución. Es la conclusión, no un candidato descartado por defecto.
- **Nube o máscara**: `CLOUD_MASK_BT_K` vale 0,0 en producción, así que la máscara no descarta píxeles; se confirma
  leyendo el perfil. La nube física sólo se informa como contexto (punto 4), nunca como causa con este instrumento.
- Si dos candidatos son causa a la vez, se informan los dos con su número; no se elige.

## Controles

- **Instrumento**: mi réplica de la máscara del primer pase tiene que ser idéntica a la que devuelve la función
  original en los 7 gránulos, y el record que arma el probe con `store.append_record` tiene que reproducir el
  publicado en `data/mirova_equivalent/NevadosDeChillan.json` (`diag_n_first_pass_pixels`, `diag_n_first_pass_summit`,
  `diag_n_second_pass_recapture` iguales; `t_bg_k`, `diag_mu_dnti`, `diag_sd_dnti` dentro de 1e-3 relativo). Un
  gránulo que no reproduce queda SIN DATO, no entra al veredicto.
- **Positivo**: en C1, C2 y C3 el mejor píxel dentro del inner tiene que pasar las cuatro etapas. Si un control no
  pasa, el instrumento está roto y no hay veredicto.
- Un gránulo que no baja queda SIN DATO (el script sale con código 2).

## Adenda posterior al primer resultado (run 39692725826), declarada antes del segundo despacho

El criterio de arriba no cambia y se aplica tal cual al run 39692725826. Ese run mostró que en T1 y T2 ningún
contrafactual de un solo factor (F1, F2, F4, B21) enciende un píxel dentro del inner y que F3 (conectiva `min` y sin
compuerta, juntas) sí enciende 2 y 3. El preregistro no tenía una regla para dos factores que sólo actúan juntos: se
informa así, sin elegir uno. Además el mejor píxel tiene BT MIR por DEBAJO de `t_bg`, y la magnitud del cúmulo
resta el fondo del anillo con recorte `dL >= 0` (`pipeline/process_modis.py`, bloque «S26: clip ΔL ≥ 0»), así que
detectarlo podría no bastar para publicarlo. Para medirlo, sin criterio nuevo de causa, se agregan tres brazos que
llegan hasta el record y el predicado del tablero (node): SC (primer pase sin compuerta), MIN (conectiva `min` en los
dos pases) y MINSC (las dos). Son exploratorios: describen qué haría falta para publicar, no deciden la causa.
