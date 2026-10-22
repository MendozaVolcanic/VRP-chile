# S159, frente «el paquete de MIROVA y el déficit oblicuo»: la razón contra MIROVA por tramo de cenit, VIIRS 750

2026-10-21. Sólo lectura. No se bajó nada: todo sale de los artefactos del frente N ya en disco
(`D:\vrp-trabajo\temporales\s159_n\run_39682867040`, 391 pasadas con resultado ok) y de las tablas de N
(`C:\vrp-trabajo\s159-pruebas\experiments\_s159\n\objetivos_n.json`, `...\n\tabla_por_pasada.csv`). El run del censo
39693661527 no se usa: sólo trae negativos y la razón se mide en alertas. Scripts y salidas en esta carpeta:

- `C:\vrp-trabajo\s159-pruebas\experiments\_s159\oblicuo_paquete\01_razon_por_cenit.py` → `01_razon_por_cenit_salida.txt`
- `C:\vrp-trabajo\s159-pruebas\experiments\_s159\oblicuo_paquete\02_conteo_por_cenit.py` → `02_conteo_por_cenit_salida.txt`
- `C:\vrp-trabajo\s159-pruebas\experiments\_s159\oblicuo_paquete\03_ic_mediana.py` → `03_ic_mediana_salida.txt`

**Población y ventana de todos los números**: alertas de MIROVA que deciden (lab `pos`, `decide`), VIIRS 750 nocturno,
2026-04-01 a 2026-10-21 sin el 18 y 19 de octubre, estado ok: **181** (Chillán 28). Razones crudas (sin pesos, como el
§9 de N); las ponderadas por peso de muestreo van en `01` §4 y no cambian ninguna conclusión. **Cenit**: el del sensor
en el centro de la grilla del volcán, que el probe leyó del gránulo (`geometria_centro.sensor_zenith`); contra el del
record de producción la diferencia mediana es 0,01° (máximo 0,38°) y sólo 1 de 181 pasadas cambia de tramo.

**Brazos**: K = producción (publica según el predicado del tablero); F = fondo y suma del código de MIROVA sobre la
detección nativa de K; O = oráculo, el código entero de MIROVA remuestreado a la grilla de GEO con interpolador lineal
y la caja de cumbre por defecto; S = el mismo oráculo con umbrales de cumbre en todo el recuadro de 21 × 21. **El
oráculo está condicionado a detectar**: «detecta» = al menos un píxel, VRP > 0 y el píxel más radiante a no más de
`inner_radius_km` (supuesto de N, no regla del scraper); detecta 145 de 181.

## Las dos preguntas del instrumento, contestadas antes de leer

1. **Si lo medido estuviera roto, ¿se vería?** Sí. Releyendo los artefactos por mi cuenta reproduzco al milésimo el §9 de
   N (K 0,510 [0,370, 0,733] n 115; F 0,990 [0,703, 1,290] n 163; O 0,999 [0,978, 1,007] n 145; placebo K × 1,2 = 0,612)
   y la detección del oráculo coincide con la columna `O_pub` de N en 181 de 181. Un pareo o una lectura de columnas
   mal hechos no darían esos cuatro números.
2. **Si el instrumento estuviera muerto, ¿se vería distinto?** Sí. Hay un **control positivo**: el déficit oblicuo de
   producción tiene que aparecer, y aparece (K en Chillán sobre 50°: 0,163, n 10; `RESUMEN_SELLO.md` de `_s157_prereg_d25`
   cita 0,16 para V750; la población exacta de #869 no la verifiqué). Y el **control pedido**: el oráculo en el tramo de
   25° o menos tiene que dar cerca de 1, y da **1,000 [IC 95 % 0,994, 1,004] n 71**. Cada celda declara su n; n 0 se
   imprime SIN DATO y n bajo 5 se marca SIN PODER. Las alertas que el oráculo no detecta se cuentan aparte, nunca como
   razón 0.

## La tabla

Razón brazo / MIROVA, mediana [cuartiles] (n = alertas que el brazo publica o detecta). IC 95 % de la mediana por
bootstrap (2.000, semilla 159) en `03_ic_mediana_salida.txt`.

| tramo de cenit | alertas | K (producción) | F (fondo y suma) | oráculo O | O no detecta | recuadro sensible S |
|---|---|---|---|---|---|---|
| ≤ 25° | 93 | 0,634 [0,485, 0,831] n 60 | 1,116 [0,882, 1,381] n 88 | **1,000** [0,967, 1,014] n 71 | 22 | 1,000 n 90 |
| 25 a 40° | 33 | 0,400 [0,310, 0,551] n 20 | 0,792 [0,668, 1,176] n 30 | **1,001** [0,996, 1,007] n 26 | 7 | 1,000 n 32 |
| 40 a 50° | 39 | 0,498 [0,353, 0,575] n 23 | 0,806 [0,607, 1,102] n 31 | **0,997** [0,973, 1,001] n 33 | 6 | 0,995 n 37 |
| > 50° | 16 | **0,178** [0,143, 0,431] n 12 | 0,539 [0,378, 1,542] n 14 | **0,996** [0,984, 1,023] n 15 | 1 | 1,000 n 16 |
| todas | 181 | 0,510 n 115 | 0,990 n 163 | 0,999 n 145 | 36 | 0,999 n 175 |

Chillán aparte (28 alertas):

| tramo | alertas | K | F | O | O no detecta |
|---|---|---|---|---|---|
| ≤ 25° | 5 | 0,910 n 5 | 1,033 n 5 | 1,000 n 5 | 0 |
| 25 a 40° | 5 | 0,678 n 5 | 0,870 n 5 | 1,017 n 5 | 0 |
| 40 a 50° | 6 | 0,377 n 6 | 0,535 n 6 | 0,914 [IC 0,812, 0,995] n 6 | 0 |
| > 50° | 12 | **0,163** [IC 0,098, 0,490] n 10 | 0,470 n 11 | **0,998** [IC 0,988, 1,024] n 12 | 0 |

Sin Chillán, sobre 50° quedan 4 alertas (Isluga 2, Láscar 1, Cordón Caulle 1): K n 2, F n 3, O n 3, todo SIN PODER.
Por volcán y tramo: `01_razon_por_cenit_salida.txt` §5.

## Hallazgos, de mayor a menor gravedad

### OB-1. El código entero de MIROVA en la grilla de GEO cierra el déficit oblicuo de VIIRS 750, también sobre 50°

- **SCRIPT:SALIDA**: `01_razon_por_cenit.py` §1 y §3; `03_ic_mediana.py`.
- **QUÉ PASA**: con el sensor de reojo el píxel nativo cubre más terreno y el foco queda diluido en él; producción
  multiplica ese píxel por el área del nadir y se queda corta. El oráculo, que interpola el gránulo a la grilla fija de
  750 m antes de detectar y sumar, da la misma magnitud que MIROVA en los cuatro tramos: 1,000, 1,001, 0,997 y 0,996,
  sin escalón. En Chillán sobre 50° pasa de 0,163 (K) a 0,998 (O), con los 12 detectados. Ejemplos (`01` §7):
  2026-10-10 06:54 UTC, cenit 67,6°, MIROVA 15,26 MW: K 2,51, F 3,51, O 14,88; 2026-10-16 06:42, 60,6°, MIROVA 14,02:
  K 2,01, F 6,59, O 14,05; 2026-10-10 04:54, 65,5°, MIROVA 2,48: K 0,24, F 0,80, O 2,48.
- **CÓMO SE VE EN EL DASHBOARD**: hoy no se ve el arreglo (remuestreo apagado, `ENABLE_UTM_REGRID = False` según N-2; no
  lo releí). Lo que sí ve el operador es el déficit: ver OB-2.
- **CÓMO REPRODUCIRLO**: `python 01_razon_por_cenit.py` en esta carpeta (lee `D:\vrp-trabajo\temporales\s159_n\run_39682867040`).
- **CONFIANZA**: CONFIRMADO como medición en este lote. Tres límites: (a) sobre 50° hay 16 alertas y 12 son Chillán en
  erupción (2026-09-28 a 10-17), así que el resultado es de Chillán; fuera de Chillán es SIN PODER (n 3); (b) las
  pasadas del 18 y 19 de octubre, de donde salió el probe L1B de #869, no están en el lote; (c) Chillán 40 a 50° da
  0,914 (IC 0,812 a 0,995, n 6), un poco bajo 1 y sin explicar.
- **GRAVEDAD**: 4. Responde la pregunta del frente: en VIIRS 750 el paquete y el déficit oblicuo son la misma palanca;
  el déficit oblicuo tiene arreglo conocido (el paquete entero, no una pieza).

### OB-2. La magnitud de producción cae con el cenit y sobre 50° queda en un sexto de MIROVA en una erupción

- **SCRIPT:SALIDA**: `01_razon_por_cenit.py` §1, §3 y §7; `03_ic_mediana.py`.
- **QUÉ PASA**: K da 0,634 bajo 25°, 0,400 y 0,498 entre 25 y 50°, y **0,178 sobre 50°** (IC 0,121 a 0,425, n 12); en
  Chillán 0,910 → 0,678 → 0,377 → 0,163. Los intervalos de ≤25° y >50° no se solapan.
- **CÓMO SE VE EN EL DASHBOARD**: en la serie de Chillán de fines de septiembre a mediados de octubre, las pasadas
  oblicuas muestran 0,2 a 2,5 MW donde MIROVA dio 2,5 a 15 MW; en dos pasadas de la misma noche con distinto ángulo la
  razón contra MIROVA cambia unas 4 veces (2026-10-05: 05:06 a 53,6° K 1,44 contra MIROVA 3,43, razón 0,42; 06:48 a
  64,3° K 0,26 contra 2,66, razón 0,10), mientras MIROVA da magnitudes parecidas en las dos. Un operador que lea la tendencia puede ver una baja que no existe.
  Dos alertas oblicuas de Chillán (2026-09-28 04:42, 0,23 MW; 2026-10-01 04:42, 0,09 MW) K no las publica.
- **CÓMO REPRODUCIRLO**: igual que OB-1, §7.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 4. Tuerce la lectura de tendencia en una erupción, que es justo cuando el cenit varía entre pasadas.
  No tuerce la detección: las protegidas siguen publicadas (N, 0 de 78 perdidas).

### OB-3. Atribución aproximada: las dos piezas crecen con el cenit, y la del remuestreo deja la firma de conteo

- **SCRIPT:SALIDA**: `01_razon_por_cenit.py` §6; `02_conteo_por_cenit.py`.
- **QUÉ PASA**: cocientes por par, en alertas donde los dos brazos tienen magnitud > 0, mediana por tramo (≤25 / 25-40 /
  40-50 / >50):
  - **fondo y suma** (F/K, misma detección nativa): 1,44 / 1,59 / 1,43 / **3,28** (n 60, 20, 23, 12). Plano hasta 50°;
    sube sobre 50°, donde 10 de 12 pares son Chillán. Coherente con que el fondo de anillo empeora hacia el borde
    (tarea 1.14, F_bg).
  - **detección + grilla + remuestreo** (O/F, mismo fondo y suma): 0,94 / 1,32 / 1,45 / **1,85** (n 69, 24, 27, 14).
    Crece de forma monótona con el cenit.
  - **el paquete entero** (O/K): 1,52 / 2,18 / 2,00 / **5,56** (n 49, 18, 22, 12).
  - **posición de la grilla** (O GEO / O R2, lineal): 1,04 / 0,96 / 0,98 / 0,96; **interpolador** (lineal / vecino más
    cercano): 0,86 / 0,78 / 0,76 / 0,82. Ninguno de los dos sigue al cenit.
  - **firma de conteo** (`02`): celdas alertadas del oráculo por píxel nativo alertado, O_n/F_n: 1,50 / 2,75 / 2,00 /
    2,75 (todas), con el VRP por celda del oráculo contra el VRP por píxel nativo plano en 0,59 / 0,64 / 0,62 / 0,59.
    O sea que el oráculo reparte el foco en más celdas cuanto más oblicuo es el píxel y conserva más energía en total,
    que es lo que se espera si el remuestreo devuelve el área que el área nadir fija le quita (S131, `pipeline/scan_geometry.py:248`
    a `:262`, docstring de `pixel_areas_from_geolocation`).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python 01_razon_por_cenit.py` (§6) y `python 02_conteo_por_cenit.py`.
- **CONFIANZA**: los cocientes, CONFIRMADO. La atribución, **aproximada**: O/F mezcla la detección del código con la
  grilla y el remuestreo, y con estos datos no se separan (falta una detección del código en geometría nativa con área
  medida). Que las celdas extra del oráculo sean reparto del píxel y no sensibilidad de detección: SOSPECHA apoyada en
  que el VRP por celda queda plano. Fuera de Chillán sobre 50° la firma es SIN PODER (n 3).
- **GRAVEDAD**: 3. Dice que ni el fondo solo (F) ni el remuestreo solo bastan sobre 50° en Chillán; hacen falta los
  dos, que es lo que ya había dicho N para el conjunto.

### OB-4. En VIIRS 750 el oráculo sí muestra la firma de conteo que la tarea 1.14 no encontró en VIIRS 375

- **SCRIPT:SALIDA**: `02_conteo_por_cenit_salida.txt`; contra `experiments/_s151_presupuesto_magnitud/README.md` líneas 76
  a 84 y 184 (leídas en esta sesión).
- **QUÉ PASA**: 1.14 dejó la dependencia angular SIN ATRIBUIR porque el Npix de MIROVA (OSF 2025, VIIRS 375) no crece
  hacia el borde. En VIIRS 750 el conteo del oráculo por píxel nativo sí crece (1,5 → 2 a 2,75). No es una contradicción
  demostrada: otro sensor, otro año, y el oráculo no es el Npix de MIROVA (sólo reproduce su magnitud). Pero la marca
  S157 de D17 en `docs/MIROVA_DIVERGENCES.md:2275` («SIN ATRIBUIR, con D25 y D17 compitiendo») descansa en la medición
  de 375 y no distingue sensor.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python 02_conteo_por_cenit.py`.
- **CONFIANZA**: SOSPECHA (de que en 750 la atribución deba cambiar); la medición del conteo, CONFIRMADO.
- **GRAVEDAD**: 2. Si se confirma, la marca de D17 tendría que separar V750 de V375 (A113); lo decide quien orquesta.

### OB-5. F solo no es un arreglo del oblicuo: se queda corto en Chillán y se pasa fuera de Chillán

- **SCRIPT:SALIDA**: `03_ic_mediana_salida.txt`.
- **QUÉ PASA**: sobre 50°, F da 0,470 en Chillán (n 11) y 1,677 fuera de Chillán (n 3, SIN PODER). En 1 píxel F sobre
  el píxel nativo sobrestima los focos débiles (O/F en pares de 1 píxel: 0,525 sobre 50°, 0,753 bajo 25°; Láscar
  2026-04-29 06:18: F 0,275, O 0,158, MIROVA 0,16), y en los focos grandes y oblicuos de Chillán subestima porque no
  reparte.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (F no está en producción).
- **CONFIANZA**: CONFIRMADO en Chillán; fuera de Chillán SIN PODER.
- **GRAVEDAD**: 2 (refuerza N-1 y N-6: adoptar el fondo sin la grilla no resuelve la magnitud oblicua).

### OB-6. Las 36 alertas que el oráculo no detecta no tienen que ver con el cenit: son la caja de Cordón Caulle y Tupungatito

- **SCRIPT:SALIDA**: `01_razon_por_cenit_salida.txt` §1 y §5.
- **QUÉ PASA**: no detectadas por tramo: 22, 7, 6, 1 (proporción 24 %, 21 %, 15 %, 6 %, baja con el cenit, no sube).
  Las 36 son Cordón Caulle (28) y Tupungatito (8), con 0 detectadas en los dos volcanes en todos los tramos; el recuadro
  sensible detecta 175 de 181 y da razón 1,000, 1,000, 0,995 y 1,000. Es la ROI de N-3, no el ángulo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hoy; en la ola 3, un paquete con la caja por defecto perdería esas alertas.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2 (el condicionamiento del oráculo a detectar no sesga la tabla por cenit).

## Qué haría falta para probar lo mismo en VIIRS 375 (otro frente lo porta; no lo repito)

1. El oráculo de 375 con su grilla. Según GEO H1 (citado por N, no lo releí) la grilla de 375 m es la de la esquina R2;
   y los TIF de MIROVA en UTM de 375 m duraron sólo del 2026-09-14 06:36 al 09-15 06:24 (A106), así que la grilla no se
   puede validar por encabezados fuera de esas ocho adquisiciones: hay que validarla por valores, como hizo N en 750.
2. El control de esta misma tabla: oráculo ≤25° cerca de 1 antes de mirar el tramo >50°.
3. Alertas oblicuas fuera de Chillán: en 750 hay 4 sobre 50°. En 375 conviene contar primero cuántas hay por tramo y
   volcán; si fuera de Chillán siguen siendo menos de 5, el resultado será otra vez de Chillán y hay que decirlo.
4. La firma de conteo (`02_conteo_por_cenit.py` adaptado: celdas del oráculo por píxel nativo y VRP por celda), que es
   la medición que 1.14 hizo con el OSF y que el oráculo permite repetir en 2026.
5. El kernel: en 375 el pre-registro D25 separa con y sin kernel por cenit (`RESUMEN_SELLO.md` línea 29); la tabla
   tendría que separarlo igual.

## Lo que quedó sin medir

- Chillán 2026-10-12 05:18 (protegida, 8,44 MW) sigue SIN DATO en N; el 18 y 19 de octubre no están en el lote.
- Separar detección de remuestreo dentro de O/F: no se puede con estos artefactos (sólo hay la grilla remuestreada
  `m13`/`m15` de 67 × 67 en los `grilla_*.npz`, sin la geometría nativa).
- MODIS y el día: fuera de este lote.

## Candidatas para BEYOND_MIROVA_EXTENSIONS §12

| qué | por qué podría ser mejor | evidencia | estado |
|---|---|---|---|
| Magnitud nativa con el área medida en la geolocalización (`pixel_areas_from_geolocation`) en vez de remuestrear | El remuestreo devuelve el área perdida pero reparte el foco por interpolación (O/F en pares de 1 píxel 0,75 a nadir); el área medida corregiría el oblicuo sin suavizar el foco débil | OB-3, OB-5; validar contra SWIR de alta resolución, no contra MIROVA | hipótesis |
| Mostrar el cenit de cada pasada junto a la magnitud en el experimental, o una banda de incertidumbre que crezca con él | En dos pasadas de la misma noche de Chillán la razón contra MIROVA cambia unas 4 veces con el ángulo; el operador debería saber que la oblicua es poco confiable | OB-2 | idea, barata |
| Serie de tendencia que pondere o descarte pasadas sobre 50° cuando hay otra pasada menos oblicua la misma noche | Evita bajas falsas en la tendencia de una erupción | OB-2, 2026-10-05 05:06 contra 06:48 | idea |

## VERIFICADO LIMPIO

- **Reproducción del §9 de N** al milésimo para K, F, O y placebo: `python 01_razon_por_cenit.py`, §0.
- **Detección del oráculo releída = columna `O_pub` de N**: 0 discrepancias en 181 (`01`, línea «control»).
- **El tramo de cenit no depende de qué cenit se use** (centro de grilla contra record): 1 de 181 cambia de tramo,
  diferencia mediana 0,01° (`01`, encabezado). El cenit del record es el del punto reportado o el cráter
  (`pipeline/process_viirs_mod.py:1492` a `:1497`, `observation_geometry`).
- **Población**: 181 alertas que deciden con estado ok, igual que N (`01`, primera línea).
- **La posición de la grilla (GEO contra R2) y el interpolador no explican la dependencia con el cenit**: cocientes sin
  tendencia (`01` §6).
- **Disco**: C: 20 GB y D: 13 GB libres al empezar (`df -h`); no se bajó nada.
- No se tocó el repositorio fuera de esta carpeta, no se hizo git ni se despachó nada.
