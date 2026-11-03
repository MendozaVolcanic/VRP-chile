# Auditoría S173: la magnitud de K contra MIROVA por cenit, VIIRS 750, Puyehue-Cordón Caulle

## 1. Encabezado

- Hora del servidor: inicio Tue, 03 Nov 2026 02:30:18 GMT (header `Date` de la API de GitHub); cierre de mediciones
  Tue Nov 3 02:43:01 UTC 2026 (`date -u`, `s00_salida.txt` corrido al final).
- Commits medidos (`s00_salida.txt`):
  - vara de MIROVA, records K de hoy, predicado del tablero, perfil y código de producción: `origin/main`
    f20495d374dc868a3dd789d1e16f662fd24c6210, copia por `git archive` en `C:/Users/nmend/vrp-wt/s173_cenit/pcc750/repo/`.
    sha256: `registro_vrp_consolidado.csv` 3d1fa40d…, `registro_vrp_ocr.csv` d793ba34…, `PuyehueCordonCaulle.json`
    c5598df6…, `data/audit_continuous/latest.json` c8a0b892….
  - ablación V750-C (`ablacion.py`, `oraculo_ablacion.py`) y `probe_n.py`: `origin/loop/activo`
    b9da9adb07bb10a4d6e3dd83f283e63482a2f968, copias en `src/` (idénticas a las que usó `v750/` para Chillán: `diff -q`
    sin salida).
  - insumos del frente N (objetivos, resultados del runner, port de R2): `origin/s159-pruebas`
    812624cc6baf97872e8c9fc09558e809123d92dd, extraídos con el mismo procedimiento de `extraer_insumos.sh` en
    `insumos/` (`diff -r` contra los de `v750/`: iguales).
  - grillas: leídas en `D:/vrp-trabajo/temporales/s159_n/` (las 72 de PCC), sin copiar ni modificar.
- Modelo: Claude Opus 5.5 (claude-opus-5-5). Esfuerzo: el que fijó quien orquesta; mi sesión no expone el valor y no
  lo puedo verificar (la configuración de esta sesión sugiere esfuerzo bajo).
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/pcc750/`. Sin worktree, sin escribir fuera de CARPETA, sin commits, sin
  workflows. Llamadas a la API de GitHub: 1.
- Qué NO miré: el detector nativo de K por dentro (por qué no encuentra el lacolito en 7 de 29 alertas: sólo lo cuento);
  `neighbor_mean_radiance_background` (el fondo alternativo D25 con flag apagado, sólo leí su envoltorio); el área real
  del píxel oblicuo; un modelo de elevación (la causa topográfica del fondo queda SOSPECHA); el día; VIIRS 375 y MODIS
  de PCC; otros volcanes; ningún paper; ningún A/B nuevo en el runner.

## 2. En una pantalla

1. Por pasada, K publica en PCC VIIRS 750 bajo MIROVA a todo cenit y peor de lado: ventana 2026-04-01 a 11-02 (53
   alertas, 42 noches), con ceros 0,571 bajo 30° y 0,117 sobre 30°, Spearman −0,508 FUERA del barajado; sólo
   publicadas 0,696 y 0,336. Es déficit de NIVEL y de PENDIENTE. En la ventana del auto-audit (22 alertas) la pendiente
   no es significativa (−0,236, dentro).
2. El nivel es el mismo mecanismo que Chillán, más fuerte: el fondo de anillo de K (mediana 5 a 25 km) es 3,6 K más
   tibio que el fondo local de MIROVA bajo el lacolito, y el lacolito sólo sobresale 4,7 K de ese fondo local: el anillo
   se come casi todo el exceso ya en el nadir. En la grilla, poner ese fondo en el código de MIROVA baja la razón de 1,00
   a 0,18 (bajo 30°); todas las demás piezas de K juntas la dejan en 1,00. En el gránulo nativo, K da 0,425 y K con el
   fondo de MIROVA (F) 1,128.
3. La pendiente es de ceros: los fracasos de K (no detecta, o detecta con 0,0 MW) pasan de 6 de 18 bajo 30° a 8 de 11
   sobre 30°. Los 0,0 MW son el anillo con recorte; las 7 no detecciones no las reproduce ninguna pieza de K en la
   grilla (SOSPECHA: remuestreo o detector nativo). La pérdida aceptada del 2026-10-10 05:54 es una de ellas.
4. No es la posición (el cúmulo de K cae en la misma celda que el de MIROVA) ni la suma de alertados (K tiene 1 píxel).
   Y en PCC la base de la ablación del ejemplo (caja 7 × 7) no alerta en ninguna de las 72 pasadas: hubo que usar las
   cajas B1 y B3 de V750-B, que tampoco son planas contra MIROVA (−0,47).

Informe: `C:/Users/nmend/vrp-wt/s173_cenit/pcc750/INFORME.md`

## 3. El fenómeno, primero

El lacolito de Cordón Caulle es una anomalía débil y extensa, a unos 7,6 km del punto del volcán (el centro de la
grilla de MIROVA, que es la cumbre del Puyehue), sobre la meseta alta del cordón. A 750 m no hay un foco: hay uno o dos
píxeles que quedan 4 a 5 K de temperatura de brillo M13 sobre su entorno inmediato (`s04_salida.txt`, dBT
caliente-código 4,718 K bajo 30°, 3,943 sobre 30°).

MIROVA estima el fondo de cada píxel alertado interpolando por debajo de él, después de apartar un halo: o sea, con el
terreno que lo rodea en la meseta. K toma un solo número para toda la escena, la mediana de la temperatura de brillo
en un anillo de 5 a 25 km alrededor del punto del volcán. Ese anillo es casi todo terreno que no es la meseta del
lacolito, y es más tibio: su mediana queda 3,6 K sobre el fondo local de MIROVA cerca del nadir y 5,5 K de lado. La
banda de 5 a 10 km, donde está el lacolito, es 0,9 K más fría que la mediana del anillo, y la de 20 a 25 km 0,4 K más
tibia; el mismo perfil aparece en las 43 pasadas sin alerta, así que es el terreno y no la propia anomalía difusa la que
entibia el anillo (`s05_salida.txt`; la causa de altura es SOSPECHA, sin modelo de elevación).

Resultado: el píxel caliente supera al anillo por apenas 0,7 K en el nadir y queda 1,6 K por DEBAJO de él de lado.
Cuando queda por debajo, el exceso es negativo y el recorte a cero lo deja en 0,0 MW: una alerta de MIROVA sin magnitud
nuestra, que el tablero no publica. De lado el píxel nativo es más grande, el exceso del lacolito se diluye (de 4,7 a
3,9 K) mientras el anillo no cambia, y la fracción de pasadas que quedan en cero sube.

En Chillán el mismo anillo pesaba poco en el nadir porque el exceso del domo es grande (0,910 de razón de K bajo 30°);
en PCC el exceso es del mismo tamaño que el error del anillo, y el déficit aparece a todo cenit.

## 4. Mediciones (cada una con sus dos preguntas)

Scripts y salidas en CARPETA. Los números de este informe salen de esas salidas.

### s00, configuración (`s00_config.py`, `s00_salida.txt`)

Commits, sha256 de insumos y valores del perfil leídos de `pipeline.profile` (no del YAML, A89): `BG_INNER_KM 5.0`,
`BG_OUTER_KM 25.0`, `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 False`, `ENABLE_V750_CODIGO_MIROVA False`,
`ENABLE_UTM_REGRID False`, `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS True`. El anillo de K se mide desde el punto del
volcán: `repo/pipeline/process_viirs_mod.py` l. 548 (`dist = haversine_km(volcano_lat, volcano_lon, lat, lon)`) y
l. 570 (`bg_mask  = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)`), TEXTO. Fondo y recorte del VRP: l. 1072 y 1087.

### s01, razón K / MIROVA por pasada con los records de hoy (`s01_razon_k_por_pasada.py`, `s01_salida.txt`, `s01_por_alerta_*.csv`, `s01_resumen.json`, `s01_stderr.txt`)

Unidad: la pasada con alerta de MIROVA VIIRS 750 (CONS y OCR de la misma pasada fundidos, VRP de la CONS si hay),
pareada a ±120 s con nuestro record. Vara: unión CONS+OCR, D-9 SN, avisos A119 en `s01_stderr.txt`. Magnitud nuestra:
`disp` del predicado del tablero ejecutado en node. Cenit: `sensor_zenith_deg` del record (presente en todos).

- P1: control x2 dobla la mediana (1,392 contra 0,696); `disp` = `pc.vrp_mw` del JSON en todos los publicados (0
  distintos); cenit del record contra `Zenith_Sat_deg` del OCR, |dif| 0,27° (n 1: el control es débil, sólo una fila
  OCR de PCC VIIRS 750 trae cenit). Identidad del predicado de node: `([0, 1, 1, 1, 0], [1, 0])`.
- P2: con la referencia corrida +1 día quedan 2 de 16 (ventana del auto-audit) y 3 de 39 (amplia) records publicados
  pareados con una alerta. No es cero: las pasadas de PCC caen casi a la misma hora noche tras noche y MIROVA alerta
  casi todas las noches. El pareo por minuto es bueno pero no perfecto; no cambia ningún veredicto (el error es de
  pocas pasadas y no tiene relación con el cenit).
- Ventana del auto-audit (2026-09-03 a 11-02): 22 alertas, 16 noches, 0 sin record; 14 bajo 30° y 8 sobre 30°.
- Ventana amplia (2026-04-01 a 11-02): 53 alertas, 42 noches, 0 sin record; 33 y 20.

| ventana | serie | bajo 30° | sobre 30° | Spearman (barajado 2,5 a 97,5 %) |
|---|---|---|---|---|
| auto-audit | tablero, con ceros | 0,390 (n 14) | 0,154 (n 8) | −0,236 ([−0,386; +0,456]) dentro |
| auto-audit | tablero, sólo publicadas | 0,677 (n 10) | 0,255 (n 6) | −0,162 dentro |
| auto-audit | por noche, como el auto-audit | 0,511 (n 13) | | (reproduce el 0,512 del auto-audit) |
| amplia | tablero, con ceros | 0,571 (n 33) | 0,117 (n 20) | −0,508 ([−0,215; +0,260]) FUERA |
| amplia | tablero, sólo publicadas | 0,696 (n 27) | 0,336 (n 12) | −0,414 ([−0,286; +0,338]) FUERA |
| amplia | sólo CONS (A119) | 0,576 (n 31) | 0,117 (n 20) | −0,511 FUERA |
| amplia | desde el 2026-06-13 | 0,368 (n 21) | 0,097 (n 15) | −0,407 FUERA |
| amplia | escena (todos los alertados), con ceros | 0,571 | 0,117 | −0,414 FUERA |

La escena da lo mismo que el cúmulo: K casi siempre tiene un solo píxel alertado (pc 1 píxel en la mediana de los dos
tramos). La distancia del cúmulo de K al punto del volcán (7,631 / 7,724 km) coincide con la de MIROVA (7,830 / 7,830).

### s02, ablación en la grilla, con tres cajas (`s02_ablacion_pcc.py`, `s02_salida.txt`, `s02_por_pasada.csv`)

Reúsa `cargar`, `buscar_grilla`, `publica` y `celda_k` de `ablacion.py` y `detectar`/`vrp` de `oraculo_ablacion.py`
sin tocarlos. Dos cambios de instrumento, los dos por PCC:

1. Base. Con la caja del ejemplo (O, 7 × 7 sensible al centro) el código de MIROVA no alerta en NINGUNA de las 72
   pasadas (control positivo sin sustrato: 0 pasadas con alertado). Se agregan dos bases: S = 21 × 21 sensible (B1 de
   V750-B) y C = círculo de 20 km sensible (B3). Sobre cada base, una pieza de K cada vez.
2. Anillo. `oraculo_ablacion.py` arma el anillo del fondo y el de la compuerta desde `inner_km` hasta 25 km
   (l. 177 y 222); en PCC eso es 20 a 25 km. K usa 5 a 25 (s00). Los brazos `_525` pasan `inner_km = 5` al oráculo y
   fijan el círculo de la caja en 20 km con un reemplazo local de `OA.caja` (sólo en este proceso); los `_2025` son los
   del original.

- P1: identidad O = port de R2 72 de 72; O = `geo_linear` del runner 72 de 72; control positivo (+10 % de M13 en los
  alertados) cambia el VRP en 27 de 27 pasadas con alertado de S y 30 de 30 de C; los brazos `_525` difieren de sus
  gemelos `_2025` en 27 (S), 30 (C) y 25 (todo K) pasadas.
- P2: brazos que no cambian nada contra su base (no miden su pieza en PCC): `_regp1`, `_umbK` y `_rec` en S y C (0
  pasadas); toda la familia O (base muda). Cambian: `_8vec` 6/8, `_comp1_525` 2/3, `_comp_525` 24/26, `_fan*` y
  `_sinhalo` 27/30, `todoK525` 36, `todoK525_fcodigo` 9.
- Cenit del record K del runner contra el del centro de la geometría: |dif| máx 1,27°, mediana 0,275°.

### s03, razón de cada brazo contra MIROVA por cenit (`s03_razon_brazos_por_cenit.py`, `s03_salida.txt`, `s03_resumen.json`, `s03_por_pasada.csv`)

Denominador fijo: las 29 pasadas de la grilla con alerta de MIROVA (2026-04-07 05:42 a 2026-10-16 05:42, 26 noches;
18 bajo 30° y 11 sobre 30°; 27 CONS, 2 OCR). Razón «con ceros»: un brazo que no da VRP > 0 cuenta 0.

- P1: 29 de 29 alertas coinciden con las `pos` de N (0 con etiqueta distinta, 0 con VRP distinto); K2 = K en 29 de 29;
  K del tablero de hoy = K del runner en las 15 que publica (|dif| > 0,006 MW: 0) y K del runner no da VRP > 0 donde el
  tablero no publica (0 casos); F record = `F_pc_central` en 22 de 22; C ×2 dobla la mediana (2,002 contra 1,001).
- P2: referencia +1 día, 0 pares de 72; barajado 200, semilla 173.

| brazo | qué es | bajo 30° (n 18) | sobre 30° (n 11) | Spearman (barajado) |
|---|---|---|---|---|
| K (tablero = runner) | producción | 0,425 | 0,000 | −0,647 ([−0,391; +0,361]) FUERA |
| N F pc | K con fondo y suma del código, sin recorte, nativo | 1,128 | 0,990 | −0,390 ([−0,364; +0,376]) FUERA |
| N FC pc | F sin la compuerta | 1,158 | 0,990 | −0,364 dentro |
| O | código de MIROVA, caja 7 × 7 | 0,000 | 0,000 | sin sustrato |
| S | código, 21 × 21 sensible (B1) | 0,997 | 0,684 | −0,430 ([−0,340; +0,373]) FUERA |
| C | código, círculo 20 km (B3) | 1,001 | 0,808 | −0,468 ([−0,394; +0,342]) FUERA |
| C_fan525 | C con el fondo de anillo de K | 0,171 | 0,000 | −0,401 FUERA |
| C_fan525_rec | y el recorte | 0,176 | 0,000 | −0,415 FUERA |
| C_fan2025 | anillo del original (20-25 km) | 0,060 | 0,000 | −0,381 FUERA |
| C_sinhalo | fondo del código sin halo | 0,773 | 0,433 | −0,472 FUERA |
| C_8vec / C_comp1_525 | una pieza de detección de K | 1,003 / 0,996 | 0,892 / 0,808 | −0,449 dentro / −0,412 FUERA |
| todoK525 | todas las piezas de K en la grilla | 0,176 | 0,000 | −0,415 FUERA |
| todoK525_fcodigo | todas menos el fondo de anillo | 0,996 | 0,808 | −0,412 FUERA |
| todoK525_fcodigo_sincomp | y sin compuerta | 1,003 | 0,892 | −0,449 dentro |

Posición (s03, DESCOMPOSICIÓN): el cúmulo de K está a 0,000 km de la celda alertada de C más cercana en la mediana de
los dos tramos (rango 0 a 0,75 km bajo 30°, 0 sobre 30°, n 14 y 6); a 0,375 / 0,000 km de la celda más radiante de C.
La celda de K está a 7,649 a 7,830 km del centro, igual que el pico de C y que la `Distancia_km` de MIROVA (7,65 y
7,83, cuantizada a celdas, D15).

### s04, de qué está hecho el déficit, el fondo en K de temperatura y robustez (`s04_mecanismo_y_robustez.py`, `s04_salida.txt`)

- Qué le pasa a K en cada alerta (runner, nativo): bajo 30° (n 18) 3 no detecta, 3 detecta con 0,0 MW, 12 con VRP;
  sobre 30° (n 11) 4, 4 y 3. Spearman del cenit contra «fracaso» (no detecta o 0 MW) +0,619 (barajado [−0,367;
  +0,412]) FUERA; contra «no detecta» sólo +0,376 dentro. Control: K2 da la misma clase en 29 de 29.
- En las 7 «detecta con 0,0 MW», F (fondo del código) da 0,554 a 0,706 MW. En las 7 «no detecta», C da VRP en 5
  (las otras 2 no las ve nadie: 2026-09-28 05:36 y 2026-08-22 06:18, esta con `Distancia_km` 2,25 de MIROVA, otro
  objeto) y `todoK525_fcodigo` las detecta todas esas 5 (s03 DETALLE).
- Fondo: Planck(t_bg del record K) / mediana del anillo 5-25 de la grilla 1,053 [0,957; 1,058], n 29 (el brazo de
  grilla representa el fondo de K a ±5 %). BT del anillo menos BT del fondo del código: +3,604 K bajo 30°, +5,532 sobre
  30° (dentro). BT caliente menos código: +4,718 y +3,943 (Spearman −0,466 FUERA). BT caliente menos anillo: +0,678 y
  −1,589 (−0,480 FUERA).
- Sin ceros: K 0,652 (n 12) y 0,375 (n 3), Spearman −0,349 dentro; F 1,381 (15) y 1,310 (7), dentro; C 1,003 (16) y
  0,892 (9), −0,505 FUERA; `todoK525` 0,398 (11) y 0,211 (4).
- Robustez: sólo CONS, todos los signos y veredictos iguales (`todoK525_fcodigo` queda FUERA por 0,01: −0,351 contra [−0,341; +0,420]).
  Dejando una noche fuera (26 réplicas): K FUERA 26/26; C 26/26; S 25/26; `C_fan525_rec` 24/26; F 13/26 (su pendiente
  es frágil). Mediana bajo 30° estable: K 0,364 a 0,485; F 1,126 a 1,131; C 1,000 a 1,002; `C_fan525_rec` 0,149 a 0,204.
  Corte en 40° en vez de 30°: mismos Spearman.

### s05, perfil radial de BT en la grilla (`s05_perfil_radial.py`, `s05_salida.txt`)

- P1: control de la inversa de Planck de producción (250, 270, 290 K vuelven exactos); el mismo perfil sobre 43
  negativos limpios como control de «terreno contra anomalía».
- BT por banda menos la mediana del anillo 5-25, alertas (n 29): 0-5 km −4,8 K; 5-10 km −0,9 / −0,6; 10-15 km −0,2;
  15-20 km 0,0; 20-25 km +0,4 / +0,6. Negativos (n 43): −4,6 / −1,5; −0,6 / −0,2; −0,2 / −0,1; −0,1 / 0,0;
  +0,5 / +0,2. Misma forma con y sin alerta.

## 5. Hallazgos (orden de gravedad)

### CPCC750-01
- TÍTULO: En PCC el fondo de anillo de K con recorte explica el déficit de NIVEL a todo cenit: el anillo es tan radiante como el lacolito
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `repo/pipeline/process_viirs_mod.py` l. 548, 570, 1072, 1087; `s03_razon_brazos_por_cenit.py` : `s03_salida.txt` (filas C, C_fan525_rec, todoK525, todoK525_fcodigo, N K pc, N F pc); `s04_salida.txt` §(2)
- QUÉ PASA: el lacolito sobresale 4,7 K de su entorno en la meseta, y la mediana del anillo de 5 a 25 km, casi todo terreno más tibio fuera de la meseta, queda 3,6 K sobre ese entorno: el exceso sobre el anillo es de 0,7 K en el nadir y negativo de lado. En la grilla, el código de MIROVA con el fondo de anillo de K pasa de 1,001 a 0,176 bajo 30° (con ceros); todas las demás piezas de K juntas lo dejan en 0,996. En el gránulo nativo, K 0,425 contra F (fondo del código) 1,128.
- CÓMO SE VE EN EL DASHBOARD: el VRP de Cordón Caulle en VIIRS 750 aparece como la mitad del de MIROVA cuando se publica, y la mitad de las alertas de MIROVA (14 de 29 en el lote) no tienen magnitud nuestra; el auto-audit lo marca con 0,512.
- CÓMO REPRODUCIRLO: `cd C:/Users/nmend/vrp-wt/s173_cenit/pcc750 && python -B s02_ablacion_pcc.py && python -B s03_razon_brazos_por_cenit.py && python -B s04_mecanismo_y_robustez.py`; pasada ejemplo PuyehueCordonCaulle VIIRS_NOAA21_750 2026-07-06 05:54 UTC (z 21,9°: K 0,11, C 1,00, C_fan525_rec 0,03)
- CONFIANZA: CONFIRMADO (medido en la grilla y en el nativo; la equivalencia del brazo de grilla con el fondo de K, ±5 %, también medida)
- GRAVEDAD 1-5: 4 (es la palanca de la magnitud en PCC; con el fondo de anillo ninguna otra pieza puede igualar a MIROVA)

### CPCC750-02
- TÍTULO: La PENDIENTE de K con el cenit en PCC es de ceros: los fracasos (no detecta o 0,0 MW) pasan de 6 de 18 a 8 de 11
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s04_mecanismo_y_robustez.py` : `s04_salida.txt` §(1) y §(3); `s01_salida.txt` (ventana amplia)
- QUÉ PASA: de lado el exceso diluido del lacolito queda bajo el anillo más seguido y el recorte lo deja en 0,0 MW (3 de 18 a 4 de 11), y el detector nativo pierde más pasadas (3 de 18 a 4 de 11). Con ceros la razón de K cae de 0,425 a 0,000 (Spearman −0,647, FUERA en 26 de 26 réplicas); sin ceros cae de 0,652 a 0,375 pero no es significativo (n 3 sobre 30°). Fracaso contra cenit: +0,619 FUERA.
- CÓMO SE VE EN EL DASHBOARD: las pasadas oblicuas de PCC con alerta de MIROVA casi nunca muestran barra nuestra en VIIRS 750 (3 de 11 en el lote; 12 de 20 publicadas en la ventana amplia, con 0,336 de razón).
- CÓMO REPRODUCIRLO: `python -B s04_mecanismo_y_robustez.py`; pasadas VIIRS_NOAA21_750 2026-07-03 05:12 UTC (z 40,5°, K detecta 0,0 MW, F 0,681 MW, MIROVA 0,52) y VIIRS_NOAA21_750 2026-10-14 06:24 UTC (z 51,0°, K no detecta, C 0,306, MIROVA 0,31)
- CONFIANZA: CONFIRMADO (los conteos); el reparto entre fondo y detector por cenit tiene n 3 a 4 por celda
- GRAVEDAD 1-5: 4

### CPCC750-03
- TÍTULO: Las no detecciones de K en alertas de MIROVA (7 de 29, incluida la pérdida aceptada del 2026-10-10) no las reproduce ninguna pieza de K en la grilla
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s04_salida.txt` §(1) «en las 'a'»; `s03_salida.txt` DETALLE (columnas NKpc «-», C, tKfcod)
- QUÉ PASA: en 5 de las 7 pasadas en que el detector nativo de K no encuentra nada, el código de MIROVA en la grilla sí ve el lacolito, y también la grilla con TODAS las piezas de detección de K (8 vecinos, umbrales, compuerta sobre el anillo 5-25, círculo, regresión): `todoK525_fcodigo` da 0,83 a 1,00 de razón. Lo que hace callar a K no está entre las piezas de la grilla: queda lo que separa el gránulo nativo de la grilla (remuestreo, D17) o una parte del detector nativo que el oráculo no tiene (selección del cúmulo anclado, filtro final).
- CÓMO SE VE EN EL DASHBOARD: una noche en que MIROVA alerta y nosotros no tenemos ni un píxel en VIIRS 750; en PCC esas noches se cubren con VIIRS 375 (la pérdida aceptada lo dice así).
- CÓMO REPRODUCIRLO: `python -B s04_mecanismo_y_robustez.py`; VIIRS_NOAA21_750 2026-10-10 05:54 UTC (z 23,6°, MIROVA 1,19 MW, K sin anomalía, C 1,193 MW, todoK525 1,005 MW)
- CONFIANZA: CONFIRMADO (que la grilla con las piezas de K sí detecta); SOSPECHA (el mecanismo)
- GRAVEDAD 1-5: 3

### CPCC750-04
- TÍTULO: La base de la ablación con la caja del ejemplo no alerta nada en PCC; la ablación de S162 y los brazos de remuestreo del runner no miden PCC, y producción tiene `roi_v750: def` para PCC
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s02_salida.txt` (control (4): 0 pasadas con alertado de O; «pasadas con al menos un alertado por base: O 0, S 27, C 30»); `s03_salida.txt` (fila O); `repo/pipeline/grillas_mirova.yaml` l. 38; `repo/pipeline/mirova_v750_codigo.py` l. 821
- QUÉ PASA: el lacolito está a 7,6 km del centro, fuera de la zona sensible de 7 × 7 celdas (±2,6 km), y el código de MIROVA con esa caja no alerta en ninguna de las 72 pasadas (29 con alerta de MIROVA). La caja que usa la vía «código MIROVA» de VIIRS 750 para PCC hoy es `def` («PuyehueCordonCaulle: {…, roi_v750: def}», TEXTO); el archivo dice que la decide V750-B, cuyo prerregistro predice exactamente esto (`origin/loop/activo:experiments/_s162_v750b/PREREGISTRO_V750B.md` l. 30 a 32, TEXTO: «Con la zona sensible de 7 × 7 el código pierde 6 protegidas que MIROVA sí publicó»). La vía está apagada (`ENABLE_V750_CODIGO_MIROVA False`, s00).
- CÓMO SE VE EN EL DASHBOARD: hoy invisible. Si la vía de VIIRS 750 se encendiera con `def`, PCC quedaría sin ninguna publicación de VIIRS 750 en este lote (0 de 29 alertas).
- CÓMO REPRODUCIRLO: `python -B s02_ablacion_pcc.py`; cualquier pasada de PCC, p. ej. VIIRS_NOAA21_750 2026-05-25 05:42 UTC (O 0 alertados, S y C 1 alertado con razón 0,92)
- CONFIANZA: CONFIRMADO (medido en el lote de N); conocido por V750-B
- GRAVEDAD 1-5: 3 (condición de cualquier adopción de la vía en PCC; ya está en el camino de V750-B)

### CPCC750-05
- TÍTULO: En la ablación de S162 el anillo del fondo y de la compuerta va de inner a 25 km, no de 5 a 25 como K: en PCC mide otro anillo
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `src/s162/oraculo_ablacion.py` l. 177 y 222 (TEXTO: «anillo = (dk > (inner_km or 0)) & (dk <= 25.0)»); `repo/pipeline/process_viirs_mod.py` l. 570; `s02_salida.txt` (3b)
- QUÉ PASA: en Chillán (inner 5) coincide con K; en PCC (inner 20) el brazo `O_fanillo` y la compuerta de `O_comp`/`O_todoK` usan 20 a 25 km. Medido: el anillo 5-25 da otra máscara o VRP que el 20-25 en 27 a 30 pasadas; con el de 20-25 la razón de C cae a 0,060 bajo 30° en vez de 0,176. La dirección del veredicto no cambia en PCC, pero el número sí, y en Lastarria (3), Planchón-Peteroa (3), Copahue (4) y Tupungatito (7) el anillo del oráculo tampoco es el de K.
- CÓMO SE VE EN EL DASHBOARD: invisible (es del instrumento).
- CÓMO REPRODUCIRLO: `python -B s02_ablacion_pcc.py && python -B s03_razon_brazos_por_cenit.py` (filas C_fan525 contra C_fan2025)
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2 (lectura equivocada de la ablación fuera de Chillán)

### CPCC750-06
- TÍTULO: El port de MIROVA en la grilla no es plano contra MIROVA en PCC con ninguna de las cajas que alertan
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_salida.txt` (filas S y C); `s04_salida.txt` §(3) y §(4b)
- QUÉ PASA: C reproduce a MIROVA cerca del nadir (1,001 con ceros, 1,003 sin ceros) pero queda bajo de lado (0,808 y 0,892), Spearman −0,468 FUERA en 26 de 26 réplicas; S igual (0,997 / 0,684). En Chillán el brazo O era plano (antecedente). Aquí no se puede afirmar que MIROVA sea plano contra un port: una parte de la pendiente puede ser de cómo el port ve PCC (ROI real de MIROVA para PCC desconocida; celdas alertadas 2 en el nadir y 1 de lado).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B s03_razon_brazos_por_cenit.py`; VIIRS_NOAA21_750 2026-05-16 05:12 UTC (z 40,5°: C 0,60)
- CONFIANZA: CONFIRMADO (la pendiente del port); SOSPECHA (la causa)
- GRAVEDAD 1-5: 2 (límite de lo que la ablación puede atribuir en la pendiente)

### CPCC750-07
- TÍTULO: Con el fondo de MIROVA en el gránulo nativo (F) no queda el déficit de remuestreo que quedaba en Chillán; F queda sobre MIROVA
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_salida.txt` (N F pc), `s04_salida.txt` §(3) y §(4b)
- QUÉ PASA: F da 1,128 bajo 30° y 0,990 sobre 30° con ceros (Spearman −0,390, FUERA por poco y sólo en 13 de 26 réplicas), y 1,381 / 1,310 sin ceros (dentro). En Chillán F oblicuo quedaba en 0,522 (antecedente, CV750-02 de `v750/`). En PCC la magnitud nativa con el fondo correcto no se pierde de lado: lo que se pierde son detecciones (CPCC750-03). Por qué F supera a MIROVA en 1,3 veces sin ceros no lo sé.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy; si se adoptara sólo el fondo del código sobre el detector nativo, PCC quedaría unas 1,3 veces sobre MIROVA donde detecta.
- CÓMO REPRODUCIRLO: `python -B s03_razon_brazos_por_cenit.py`; VIIRS_NOAA21_750 2026-04-13 05:30 UTC (z 16,9°: F 2,32, C 0,89, K 0,73)
- CONFIANZA: CONFIRMADO (los números); SOSPECHA (la causa del exceso)
- GRAVEDAD 1-5: 2

### CPCC750-08
- TÍTULO: En la ventana del auto-audit la pendiente con el cenit de PCC V750 no se ve; hace falta la ventana larga
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s01_salida.txt` (ventanas auditoria y amplia); `repo/data/audit_continuous/latest.json` (`window` 2026-09-03 a 2026-11-02; `PuyehueCordonCaulle|VIIRS750` por cenit: z30-50 n 2, z50-60 n 1, z>=60 n 1)
- QUÉ PASA: con 22 alertas (8 sobre 30°) el Spearman de la razón con ceros es −0,236, dentro del barajado; con 53 alertas (abril a noviembre) es −0,508 FUERA. El 0,512 del auto-audit (por noche) es sobre todo nivel y ceros.
- CÓMO SE VE EN EL DASHBOARD: invisible; afecta cómo se lee el aviso del auto-audit.
- CÓMO REPRODUCIRLO: `python -B s01_razon_k_por_pasada.py`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1

### CPCC750-09
- TÍTULO: En un campo difuso el halo del fondo de MIROVA pesa: sin halo el código pierde la mitad de lado
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_salida.txt` (C_sinhalo 0,773 / 0,433, contra C 1,001 / 0,808); `s04_salida.txt` §(3) (C_sinhalo sin ceros 0,838 / 0,443)
- QUÉ PASA: los vecinos inmediatos del píxel alertado del lacolito llevan parte de la misma anomalía difusa; interpolar el fondo sin apartar el halo lo entibia. En Chillán el halo no era palanca (O_sinhalo 1,007 / 0,965, antecedente). El fondo alternativo D25 con flag apagado (`vrp_bg_neighbor_mean_v750`, `repo/pipeline/process_viirs_mod.py` l. 417, «media de la radiancia de los vecinos NO alertados», l. 1073 TEXTO) se parece más a «sin halo» que a «con halo»: SOSPECHA de que en PCC no alcanzaría (no leí `neighbor_mean_radiance_background`).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy.
- CÓMO REPRODUCIRLO: `python -B s03_razon_brazos_por_cenit.py`
- CONFIANZA: CONFIRMADO (el brazo); SOSPECHA (la extrapolación a D25)
- GRAVEDAD 1-5: 2

## 6. La pérdida aceptada (PCC V750 2026-10-10 05:54 UTC, #865, #881), aparte

MIROVA 1,19 MW, CONS, cenit 23,6°. K no tiene ningún píxel anómalo (record de main: `pc_n` None, `n_anomalous` 0;
runner igual). En la grilla, el código de MIROVA con caja C la ve con 1,193 MW (razón 1,00) y con todas las piezas de K,
fondo de anillo incluido, 1,005 MW (0,84). Es una pérdida de DETECCIÓN del gránulo nativo, no de magnitud ni de fondo
(CPCC750-03). Fuentes: `s01_salida.txt` (DETALLE amplia), `s04_salida.txt` §(1).

## 7. SEGUIMIENTOS

- `oraculo_ablacion.py` l. 177 y 222: el anillo debería ser 5-25 km para representar a K en todo volcán (CPCC750-05).
  Releer las conclusiones de V750-C de S162 en Lastarria, Planchón-Peteroa, Copahue, Tupungatito y PCC. CONFIRMADO,
  gravedad 2.
- `pipeline/grillas_mirova.yaml` l. 38, PCC `roi_v750: def`: si V750-B no la cambia, la vía de VIIRS 750 calla PCC
  (CPCC750-04). CONFIRMADO en el lote, gravedad 3.
- El fondo alternativo D25 de V750 (`vrp_bg_neighbor_mean_v750`, flag apagado) en un campo difuso: medir en PCC antes de
  proponerlo como arreglo (CPCC750-09). SOSPECHA, gravedad 2.
- Nulo del pareo por minuto: con la referencia corrida +1 día quedan 2 de 16 y 3 de 39 pares en PCC (s01), porque las
  pasadas caen a la misma hora cada noche. Un evaluador que use ese nulo como «debe dar 0» falla en PCC. CONFIRMADO,
  gravedad 1.
- Record K del 2026-04-30 06:06 (VIIRS_NOAA20_750, z 30,9°): el cúmulo está a 24,85 km del centro de la grilla y lleva
  `distance_class` summit con 0,0 MW (`s04_salida.txt` §(1)). No lo seguí. SOSPECHA de cúmulo mal elegido, gravedad 1.

## 8. VERIFICADO LIMPIO

- El pareo: 29 de 29 alertas de la grilla coinciden con las `pos` de N con el mismo VRP; 0 pares con +1 día en la
  grilla; 0 alertas sin record en s01. Vara: la referencia del scraper por pasada. Comando: `python -B s03_razon_brazos_por_cenit.py`.
- K del runner = K del tablero de hoy en las 15 publicadas, K2 = K en 29 de 29; `disp` = `pc.vrp_mw` del JSON. Vara: el
  record de `repo/data/mirova_equivalent/PuyehueCordonCaulle.json` y el predicado de node.
- El brazo de grilla «anillo 5-25» representa el fondo de K: Planck(t_bg del record) / mediana del anillo 1,053
  [0,957; 1,058]. Vara: el `t_bg_k` del record K del runner. Comando: `python -B s04_mecanismo_y_robustez.py`.
- La posición no es la palanca: el cúmulo de K cae en la misma celda que una alertada de C (mediana 0 km en los dos
  tramos) y a la misma distancia del centro que el pico de C y que MIROVA. Vara: posiciones de celda en la grilla, no
  radios (A93). Comando: `python -B s03_razon_brazos_por_cenit.py`.
- La suma de todos los alertados no es la palanca: escena = cúmulo en K (s01, con ceros 0,571 / 0,117 las dos), y F
  escena = F cúmulo (s03).
- El anillo no se entibia por la propia anomalía: el perfil radial tiene la misma forma con y sin alerta (s05).
- Ventana de los datos y A119: las conclusiones no cambian con CONS sola ni desde el 2026-06-13 (s01, s04).

## 9. SIN DATO

- La causa de las no detecciones nativas (CPCC750-03): no hay un brazo «grilla con detector nativo de K» ni «nativo con
  área real» en los insumos.
- La ROI real de MIROVA para PCC: sin ella no se puede decir si la pendiente del port (CPCC750-06) es de MIROVA o del port.
- Los brazos de remuestreo del runner (`geo_nearest`, `geo_cubic`, `r2_linear`, `r2_nearest`) usan la caja del ejemplo y
  en PCC no alertan: no miden la sensibilidad al interpolador aquí.
- Altura del terreno del anillo contra la meseta: sin modelo de elevación, la explicación topográfica de s05 es SOSPECHA.
- n por tramo: 18 y 11 en la grilla; K publica sólo 3 sobre 30°. La pendiente sin ceros de K no se puede afirmar.

## 10. FUERA DE ALCANCE

VIIRS 375 y MODIS de PCC; otros volcanes; cualquier arreglo o A/B en `pipeline/` (A45); corregir `oraculo_ablacion.py`,
`grillas_mirova.yaml` o el auto-audit.
