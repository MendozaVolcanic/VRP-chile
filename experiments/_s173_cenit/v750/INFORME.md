# Auditoría S173: qué pieza corrige la caída de la razón con el cenit, VIIRS 750, Nevados de Chillán

## 1. Encabezado

- Hora del servidor: inicio Tue, 03 Nov 2026 00:42:10 UTC (`date -u`); cierre de mediciones Tue, 03 Nov 2026
  00:52:19 GMT (header `Date` de la API de GitHub).
- Commits medidos:
  - vara de MIROVA, predicado del tablero y records K de hoy: `origin/main` 5de08ebf62d1ea092c485c0a030f323f2cbdcf2a,
    copia por `git archive` en `C:/Users/nmend/vrp-wt/s173_cenit/v750/repo/` (`repo/COMMIT.txt`). sha256:
    `registro_vrp_consolidado.csv` 3d1fa40d…, `registro_vrp_ocr.csv` d793ba34…, `NevadosDeChillan.json` c3aa3e0f….
  - ablación de V750-C y auditoría S172: `origin/loop/activo` ddd83c5b901e46451dfc0e422656162ad29a29cc, copias en
    `C:/Users/nmend/vrp-wt/s173_cenit/v750/src/s162/` y `src/s172/` (`oraculo_ablacion.py` de loop/activo es idéntico
    al de `origin/claude/adoring-wright-dc0404`: `diff -q` sin salida).
  - insumos del frente N (objetivos, resultados del runner, port de R2): `origin/s159-pruebas`
    812624cc6baf97872e8c9fc09558e809123d92dd, extraídos con `extraer_insumos.sh` en
    `C:/Users/nmend/vrp-wt/s173_cenit/v750/insumos/`.
  - grillas: leídas en `D:/vrp-trabajo/temporales/s159_n/` (518 `grilla_*.npz`), sin copiar ni modificar.
- Modelo: Claude Opus 5.5 (claude-opus-5-5). Esfuerzo: el que fijó quien orquesta (la configuración de mi sesión
  indica esfuerzo bajo; no lo puedo verificar de otra forma).
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/v750/`
- No usé worktree: trabajé con `git show` / `git archive` dentro de CARPETA (la copia `repo/`, 31 MB, queda porque los
  scripts la necesitan para reproducirse; se puede borrar sin perder nada del repositorio).
- Qué NO miré: el código de `pipeline/` más allá del fondo del VRP de VIIRS 750 (`process_viirs_mod.py` l. 1064 a
  1092); los gránulos nativos (no están: las grillas no traen la ventana nativa, `ablacion.py` l. 12 a 14); el área real
  del píxel oblicuo de VIIRS (no la calculé, no tengo el dato a mano y no lo adivino); MODIS y VIIRS 375; otros
  volcanes; el día; ningún paper; no corrí ningún A/B nuevo en el runner.

## 2. En una pantalla

1. En las 28 pasadas de Chillán con grilla y alerta de MIROVA (12 noches, 2026-09-28 a 2026-10-17; 7 bajo 30°, 21 a
   30° o más) K repite la caída de S172: 0,910 bajo 30° y 0,285 sobre 30° (con ceros), Spearman −0,864 fuera del barajado.
2. En la grilla, la ÚNICA pieza de K que reproduce la caída es el fondo de anillo (mediana 5 a 25 km): con él la razón
   va de 0,791 a 0,373 (Spearman −0,486, fuera, 12 de 12 réplicas sin una noche); con todas las demás piezas de K y el
   fondo del código la razón queda plana (1,017 / 1,000, Spearman +0,061). El brazo O es plano (1,000 / 0,996).
3. Pero ningún brazo aplana la caída partiendo de K: en el gránulo nativo, con el fondo y la suma del código (brazo F
   de N, sin remuestreo) el nadir sube a 1,033 y lo oblicuo queda en 0,522 (Spearman −0,662, fuera, 12 de 12). Cerca
   de la mitad de la caída (en escala logarítmica) sigue viva sin el fondo de K: es lo que separa el gránulo nativo de
   la grilla (remuestreo y área del píxel, D17; SOSPECHA de mecanismo).
4. Respuesta: las dos palancas actúan, y ninguna alcanza sola. El fondo (D25 del catálogo) explica la caída DENTRO de
   la grilla; el remuestreo explica lo que queda en el gránulo nativo. n chico (7 pasadas bajo 30°).

Informe: `C:/Users/nmend/vrp-wt/s173_cenit/v750/INFORME.md`

## 3. El fenómeno, primero

Cuando el satélite mira el domo de lado, el píxel nativo de VIIRS es más grande en el suelo que en el nadir. El calor
del domo, que no cambia en una hora, queda repartido en un píxel más ancho: cada píxel brilla menos sobre su fondo,
pero el píxel cubre más superficie. MIROVA pasa la imagen a una grilla fija de celdas de 750 m: el píxel oblicuo, ancho,
cae sobre varias celdas, y al sumar todas las celdas alertadas la potencia total se recupera. Nosotros dejamos el píxel
nativo y lo multiplicamos por el área del nadir: si el píxel es más ancho, esa área se queda corta.

Sobre ese exceso diluido actúa además el fondo. MIROVA estima el fondo de cada alertado interpolando los vecinos de
alrededor (apartando un halo). K toma la mediana de un anillo de 5 a 25 km, que en Chillán es terreno más bajo y más
tibio que la cumbre (A69). Cerca del nadir el exceso del domo es grande y ese error de fondo pesa poco; de lado, el
exceso por celda es chico y el mismo error se come una fracción mayor. En 6 de 21 pasadas oblicuas el fondo de anillo
supera a la radiancia de las propias celdas alertadas y el VRP sale negativo.

Lo medido abajo separa las dos cosas: en la grilla (donde el área ya está bien repartida) sólo el fondo produce la
caída; en el gránulo nativo (donde el área no se corrige) la caída sigue aunque se ponga el fondo de MIROVA.

## 4. Mediciones (cada una con sus dos preguntas)

Todos los scripts y salidas están en CARPETA. Ventana de datos de todos los números: pasadas nocturnas de Chillán de
las grillas de N, 2026-04-15 04:54 a 2026-10-17 06:18 (47 pasadas); las 28 con alerta de MIROVA van de 2026-09-28
04:42 a 2026-10-17 06:18, 12 noches. Denominador de cada tabla: indicado en ella.

### s01, ablación restringida a Chillán (`s01_ablacion_chillan.py`, salida `s01_salida.txt`, `s01_por_pasada.csv`)

Reúsa sin tocarlos `BRAZOS`, `piezas`, `cargar`, `buscar_grilla` y `publica` de `ablacion.py` (S162).

- P1 (si lo medido estuviera roto): identidad contra el port de R2, 47 de 47 ok; brazo O = `geo_linear` del runner,
  47 de 47 ok; control positivo, +10 % de radiancia M13 en los alertados de O cambia el VRP en 29 de 29 pasadas con
  alerta de O.
- P2 (instrumento muerto): cada brazo cambia al menos una pasada contra O salvo `O_regp1` (0 de 47; lo mismo que en
  S162 sobre 510: la regresión del pase 2 apenas cambia `c_eti`, `ablacion_salida.txt` l. 5). O_regp1 no mide nada
  en Chillán y no lo cuento como verificación. Cambios por brazo: O_8vec 4, O_umbK 4, O_comp 21, O_comp1 5,
  O_sens 7, O_circ 2, O_rec 1, O_fanillo 29, O_sinhalo 29, O_todoK 31, O_todoK_sincomp 9.
- Inventario: 53 objetivos de Chillán; 47 con resultado `ok`, oráculo y noche, todos con grilla. Fuera: 2 diurnas,
  4 sin gránulo (2 `pos_prot`/`pos_nopub` y 2 `reintento_1012`). El redisparo `redisparo_39690106947_resultados_00.json`
  no lo lee `ablacion.cargar` (ver SEGUIMIENTOS), pero sus 4 filas de Chillán también son `sin_granulo`: no cambia
  nada aquí.
- Cenit: `sensor_zenith_deg` del record K del runner, presente en 47 de 47; contra `geometria_centro.sensor_zenith`
  del gránulo, |dif| máx 0,86°, mediana 0.

### s02, pareo con MIROVA y razón por cenit (`s02_razon_por_cenit.py`, salidas `s02_salida.txt`, `s02_resumen.json`, `s02_por_pasada.csv`, `s02_stderr.txt`)

Vara: unión CONS+OCR de `repo/data/mirova_reference/mirova_v1_snapshot/`, D-9 SN, pareo ±120 s con
`banco_paridad.parear`; VRP de la fila CONS si es ALERTA, si no el OCR (misma regla que `s02_pareo_por_pasada.py` de
S172). Los avisos A119 salieron por stderr (`s02_stderr.txt`): 7 tramos. El único de la tabla (NOAA-21, 2026-04-09) es
anterior a las alertas; los otros seis son del OCR, que aporta 3 de las 28 alertas, y s04 (a) repite todo con CONS sola.

- P1: control positivo, K nativo en las mismas pasadas cae con el cenit (abajo); control de escala, O ×2 da mediana
  1,996 contra 0,998. Las 28 alertas pareadas son exactamente las 28 `pos` de N (0 alertas con etiqueta distinta, 0 VRP
  de MIROVA distinto del guardado por N). K de main (predicado del tablero en node) = K del runner en las 26 que
  publican (`s03_salida.txt`, |dif| > 0,006 MW: 0).
- P2: referencia corrida +1 día: 0 pares de 47.
- Fuente de las alertas: 25 CONS, 3 OCR. Plataformas: NOAA-20 13, NOAA-21 10, Suomi NPP 5.

### s03, brazos nativos de N y brazos de grilla propios (`s03_nativos_y_extra.py`, salidas `s03_salida.txt`, `s03_por_pasada.csv`)

Razón «con ceros»: denominador fijo de 28; un brazo que no da VRP > 0 cuenta 0. Así no se pierden las pasadas
oblicuas con VRP negativo (CV750-04).

- Brazos de N (gránulo nativo, `probe_n.py` l. 4 a 20 de `origin/s159-pruebas`): K = producción; K2 = K otra vez;
  C = K sin la compuerta del primer pase; F = K con el fondo y la suma del código de MIROVA, sin recorte, sin modo de un
  píxel, área y coeficiente de K; FC = F y C.
- Brazos propios en la grilla: `X_fanillo_rec` (sólo fondo de anillo + recorte, que es lo que hace K:
  `process_viirs_mod.py` l. 1072 y 1087); `X_todoK_fcodigo` (todas las piezas de K de O_todoK menos el fondo);
  `X_todoK_sinrec` (O_todoK sin recorte).
- P1: K2 = K en 28 de 28 (nulo del runner); F record contra `F_pc_central`: igual en 26 de 27, la otra es el tope de
  5 MW (SEGUIMIENTOS). P2: barajado del cenit, 200 veces, semilla 173.

### s04, robustez (`s04_robustez.py`, salida `s04_salida.txt`)

- (a) sólo CONS (A119), n 25: el signo y la significancia de cada brazo no cambian.
- (b) dejando una noche fuera (12 réplicas): K, F y X_fanillo_rec quedan fuera del barajado en 12 de 12; O y
  X_todoK_fcodigo en 0 de 12.

### Tabla central (razón con ceros, n 28; `s03_salida.txt`)

| brazo | qué cambia contra MIROVA | med < 30° (n 7) | med ≥ 30° (n 21) | ≥30 / <30 | Spearman (barajado 2,5 a 97,5 %) |
|---|---|---|---|---|---|
| K nativo (tablero) | producción | 0,910 | 0,285 | 0,313 | −0,864 ([−0,405; +0,408]) FUERA |
| N F (nativo, fondo y suma del código) | todo K salvo fondo, recorte y modo 1 px | 1,033 | 0,522 | 0,505 | −0,662 ([−0,342; +0,344]) FUERA |
| N F escena (todos los alertados) | idem, sin selección del cúmulo | 1,033 | 0,598 | 0,579 | −0,533 ([−0,357; +0,381]) FUERA |
| O (grilla, código entero) | nada | 1,000 | 0,996 | 0,996 | +0,053 ([−0,340; +0,378]) dentro |
| O_fanillo | fondo de anillo | 0,743 | 0,319 | 0,429 | −0,523 ([−0,448; +0,356]) FUERA |
| X_fanillo_rec (= O_todoK) | fondo de anillo + recorte | 0,791 | 0,373 | 0,471 | −0,486 ([−0,456; +0,361]) FUERA |
| X_todoK_fcodigo | todas las piezas de K salvo el fondo | 1,017 | 1,000 | 0,983 | +0,061 ([−0,382; +0,314]) dentro |
| O_todoK_sincomp | 8 vecinos, regresión, umbrales, caja | 1,017 | 1,002 | 0,984 | +0,291 ([−0,326; +0,356]) dentro |
| O_sinhalo | fondo interpolado sin halo | 1,007 | 0,965 | 0,959 | −0,147 dentro |
| O_rec | recorte a cero | 1,000 | 0,996 | 0,996 | +0,062 dentro |
| O_comp | compuerta en los DOS pases | 0,946 | 0,716 | 0,757 | −0,450 ([−0,402; +0,367]) FUERA |
| O_comp1 | compuerta sólo en el pase 1 (como K) | 1,000 | 0,993 | 0,993 | −0,069 dentro (sin ceros, `s02_salida.txt`) |
| O_8vec / O_umbK / O_sens / O_circ | una pieza cada uno | 1,000 a 1,017 | 1,000 | ~1 | +0,03 a +0,23 dentro (`s02_salida.txt`) |
| geo_nearest / geo_cubic | otro interpolador | 1,307 / 1,163 | 1,216 / 1,122 | 0,930 / 0,965 | −0,029 / −0,230 dentro |
| r2_linear / r2_nearest | grilla vieja de R2 | 1,011 / 0,982 | 1,005 / 0,965 | 0,995 / 0,983 | +0,081 / −0,006 dentro |

Los cuartiles y rangos de cada fila están en `s03_salida.txt` y `s02_salida.txt`. Con n 7 bajo 30° las medianas de ese
tramo son frágiles: el Spearman con barajado y las 12 réplicas de s04 son lo que sostiene cada veredicto.

## 5. Hallazgos

### CV750-01
- TÍTULO: Dentro de la grilla, sólo el fondo de anillo de K reproduce la caída de la razón con el cenit; las demás piezas de K dejan la razón plana
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_nativos_y_extra.py` : `s03_salida.txt` (filas O_fanillo, X_fanillo_rec, X_todoK_fcodigo, O_todoK_sincomp); `s04_salida.txt` (b); fondo de K en `repo/pipeline/process_viirs_mod.py` l. 1072 y 1087, anillo 5 a 25 km en `repo/pipeline/profiles/mirova_equivalent.yaml` l. 156 a 158
- QUÉ PASA: el anillo de 5 a 25 km alrededor de la cumbre nevada es más tibio que el entorno inmediato de las celdas alertadas, y de lado el exceso por celda es chico, así que ese fondo regional se come una fracción creciente con el cenit. En la grilla, fondo de anillo + recorte da 0,791 bajo 30° y 0,373 sobre 30° (Spearman −0,486, fuera en 12 de 12 réplicas), mientras todas las demás piezas de K juntas con el fondo del código dan 1,017 y 1,000 (+0,061, dentro en 12 de 12).
- CÓMO SE VE EN EL DASHBOARD: invisible como tal; contribuye a que una pasada oblicua de Chillán muestre un VRP varias veces menor que la pasada cercana al nadir de la misma noche.
- CÓMO REPRODUCIRLO: `cd C:/Users/nmend/vrp-wt/s173_cenit/v750 && python -B s01_ablacion_chillan.py && python -B s02_razon_por_cenit.py && python -B s03_nativos_y_extra.py && python -B s04_robustez.py`; pasada ejemplo NevadosDeChillan VIIRS_NOAA20_750 2026-10-16 06:42 UTC (z 60,6°: O 1,002, X_fanillo_rec 0,475)
- CONFIANZA: CONFIRMADO (medido; la equivalencia de O_fanillo con el fondo de K es aproximada: K toma Planck de la mediana de BT y excluye lo que excluya `compute_bg_stats`, el brazo toma la mediana de radiancia en la grilla; ver SIN DATO)
- GRAVEDAD 1-5: 4 (decide que el fondo es condición necesaria de cualquier arreglo de la caída oblicua)

### CV750-02
- TÍTULO: En el gránulo nativo, poner el fondo y la suma de MIROVA (brazo F de N) sube el nadir pero no aplana la caída
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_nativos_y_extra.py` : `s03_salida.txt` (filas N F pc, N F escena centr, N K pc); `s04_salida.txt`; definición del brazo en `src/probe_n.py` l. 10 a 15
- QUÉ PASA: con el fondo de MIROVA en la geometría nativa la razón queda 1,033 bajo 30° y 0,522 sobre 30° (Spearman −0,662, fuera en 12 de 12 y con CONS sola), contra 0,910 y 0,285 de K; sumando todos los alertados de la escena, 1,033 y 0,598. El fondo arregla el nivel del nadir y cerca de la mitad (logarítmica: ln 0,313 = −1,16 contra ln 0,505 = −0,68) de la caída; el resto vive en lo que el gránulo nativo no tiene y la grilla sí. Ningún brazo medible aplana la caída partiendo de K.
- CÓMO SE VE EN EL DASHBOARD: arreglar sólo el fondo (V750 con el fondo del código pero sin remuestreo) seguiría mostrando Chillán oblicuo a la mitad de MIROVA.
- CÓMO REPRODUCIRLO: igual que CV750-01; pasada ejemplo VIIRS_NOAA20_750 2026-10-10 06:54 UTC (z 67,6°: K 0,164, F 0,230, O 0,975)
- CONFIANZA: CONFIRMADO (la medición); que el resto sea el área o el remuestreo (D17) es SOSPECHA: F también difiere de O en el detector nativo de K (qué píxeles alerta), y no hay brazo que separe ambas cosas
- GRAVEDAD 1-5: 4 (sin esto se elegiría una sola palanca y la caída oblicua seguiría)

### CV750-03
- TÍTULO: La grilla alerta más celdas por píxel nativo cuando el satélite mira de lado, pero con este n no es significativo
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_salida.txt`, sección CONTEO
- QUÉ PASA: un píxel nativo oblicuo, más ancho, cae sobre más celdas de 750 m. Celdas alertadas de O por píxel alertado nativo de K: mediana 1,333 bajo 30° (n 7) y 3,000 sobre 30° (n 20), Spearman +0,238, dentro del barajado ([−0,360; +0,384]). Los píxeles nativos alertados no crecen (2 y 2), las celdas sí (3 y 5). Es la firma esperada del área nadir fija, pero no está probada.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B s03_nativos_y_extra.py`, sección CONTEO
- CONFIANZA: SOSPECHA (dirección medida, sin significancia; además el conteo de O no es sólo área, depende del detector)
- GRAVEDAD 1-5: 2

### CV750-04
- TÍTULO: Medir la razón sólo donde el brazo da VRP positivo esconde la caída del fondo de anillo (sesgo de superviviente)
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s02_salida.txt` (O_fanillo, MAGNITUD: Spearman −0,352, dentro, n 22) contra `s03_salida.txt` (O_fanillo con ceros: −0,523, fuera, n 28); `s02_salida.txt` sección DESCOMPOSICIÓN (Lbk/Lhot O_fanillo 0,559 bajo 30° y 0,888 sobre 30°, máximo 1,186)
- QUÉ PASA: en 6 pasadas, todas a 31° o más, el fondo de anillo es más radiante que las propias celdas alertadas y el VRP sale negativo; el criterio «VRP > 0» de `ablacion.py` (l. 300, razón sólo sobre los que publican) las descarta y deja sólo las oblicuas que se salvaron. Leer la ablación de S162 por cenit con ese criterio subestima justo el efecto que se busca.
- CÓMO SE VE EN EL DASHBOARD: con recorte (K) esas pasadas son 0,0 MW: una alerta de MIROVA sin magnitud nuestra (VIIRS_SNPP_750 2026-10-10 04:54, z 65,5°: X_fanillo_rec 0,017).
- CÓMO REPRODUCIRLO: `python -B s02_razon_por_cenit.py` y `python -B s03_nativos_y_extra.py`; pasadas VIIRS_NOAA21_750 2026-09-29 06:00 (z 31,1°, O_fanillo −0,857) y VIIRS_SNPP_750 2026-10-10 04:54 (z 65,5°, −0,975)
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2 (un instrumento mal leído mandaría a la palanca equivocada)

### CV750-05
- TÍTULO: O_comp cae con el cenit pero no es la compuerta de K; la de K es O_comp1, que es plana
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `src/s162/oraculo_ablacion.py` l. 17 a 19 (TEXTO: «'p1' sólo en el primer pase y en el absoluto, como K, cuyo segundo pase recaptura sin compuerta»); `s03_salida.txt` (O_comp 0,946 / 0,716, −0,450 fuera, 11 de 12 réplicas en `s04_salida.txt`); `s02_salida.txt` (O_comp1 1,000 / 0,993, −0,069 dentro)
- QUÉ PASA: exigir que la celda esté 3 K sobre la mediana del anillo apaga más celdas diluidas de lado; pero K no aplica esa compuerta en el segundo pase. El brazo que la aplica en los dos pases no representa a K.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B s02_razon_por_cenit.py`; `python -B s04_robustez.py`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1 (riesgo de lectura, no defecto del pipeline)

## 6. SEGUIMIENTOS

- La tarea dice «geometría del borde del barrido (D25)»; en el catálogo D25 es el fondo (TEXTO,
  `src/MIROVA_DIVERGENCES_main.md` l. 2861: «El fondo del VRP es la mediana de un anillo regional de 5 a 25 km»).
  En este informe D25 = fondo y la geometría del píxel oblicuo va con D17. Confianza CONFIRMADO. Gravedad 2 (la
  pregunta «D17 o D25» cambia de sentido según la etiqueta).
- `ablacion.py` l. 74 (`(ins / "n").rglob("resultados_*.json")`) no lee `redisparo_39690106947_resultados_00.json`.
  En Chillán sus 4 filas son `sin_granulo` y no cambia nada; en otros volcanes no lo miré. SOSPECHA, gravedad 1.
- Tope de 5 MW en el record del brazo F: VIIRS_NOAA21_750 2026-10-01 05:24 UTC, F pc 5,0 contra `F_pc_central` 6,214
  (MIROVA 9,0). La razón de F bajo 30° de esa pasada sale 0,556 en vez de 0,690. No cambia el veredicto (la pasada está
  en el tramo bajo 30°, donde F ya da 1,033). Confianza CONFIRMADO (la diferencia); que sea el tope D9 es SOSPECHA
  (5,0 exacto). Gravedad 1.
- Tensión con la tarea 1.14 (`docs/SINTOMAS.md` §1, «el Npix de MIROVA no crece hacia el borde»): en Chillán el port
  da 3 celdas bajo 30° y 5 sobre 30° (no significativo, CV750-03). No es una refutación. SOSPECHA, gravedad 1.

## 7. VERIFICADO LIMPIO

- El port de MIROVA reproduce a MIROVA en Chillán a todo cenit: O 1,000 / 0,996 (n 7 / 21), Spearman +0,053 dentro;
  0 de 12 réplicas fuera; con CONS sola +0,148 dentro. Vara: la referencia del scraper por pasada (`s02`, `s04`). Esto
  es lo que permite leer la ablación: si O no fuera plano, ningún brazo diría nada.
- El remuestreo en sí no es sensible al interpolador ni a la grilla de R2 en cuanto a la pendiente: geo_nearest,
  geo_cubic, r2_linear y r2_nearest dentro del barajado (cambian el nivel, de 0,97 a 1,31, no la pendiente).
  Vara: MIROVA por pasada. Comando: `python -B s03_nativos_y_extra.py`.
- Pareo: 28 de 28 alertas pareadas coinciden con las `pos` de N, VRP idéntico; +1 día da 0 pares. Comando:
  `python -B s02_razon_por_cenit.py`.
- K del runner de N = K publicado hoy en main (node, `mirovaEqVrpDisplay`) en las 26 que publican; K2 = K en 28 de 28.
  Vara: el record de `repo/data/mirova_equivalent/NevadosDeChillan.json` y el predicado del tablero.
- El halo del fondo de MIROVA no es la palanca: O_sinhalo 1,007 / 0,965, −0,147 dentro.

## 8. SIN DATO

- Un brazo «gránulo nativo con fondo de MIROVA y área real del píxel» o «grilla con detector nativo de K»: no existe en
  los insumos (las grillas no traen la ventana nativa; N no guardó el área del píxel). Es lo que separaría, dentro de lo
  que queda en CV750-02, el área/remuestreo (D17) del detector nativo de K.
- Equivalencia exacta de O_fanillo con el fondo de K: K usa Planck de la mediana de BT del anillo nativo con las
  exclusiones de `compute_bg_stats` (`repo/pipeline/detection_context.py` desde l. 1051, sólo leí la firma y el
  docstring); el brazo usa la mediana de radiancia M13 de la grilla con exclusión de la máscara.
- Pasadas bajo 30°: sólo 7 (6 en el subconjunto común de s02). Con ese n no se puede afinar la pendiente por tramos
  más finos.
- Ventana antes del 2026-09-28: las grillas de Chillán de abril a septiembre son todas negativas (19 sin alerta de
  MIROVA); no aportan razón.

## 9. FUERA DE ALCANCE

- MODIS y VIIRS 375 (otros agentes). Otros volcanes. Cualquier arreglo o A/B en `pipeline/` (A45). Corregir
  `ablacion.py` o las citas del catálogo.
