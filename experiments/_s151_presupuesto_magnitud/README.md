# Tarea 1.14 (estudio A): presupuesto de la magnitud, pasada por pasada

> Escrito el 2026-10-14 por el loop (tarea 1.14 de `tasks/LOOP_OBJETIVOS.md`) y corregido el mismo día con los
> siete arreglos del verificador con contexto limpio de #814 (veredicto PARCIAL; §7). Sin correr el pipeline:
> sólo records en disco, salidas de A/B ya corridos (ramas `s146-ab/<run>`, extraídas con `git archive <ref>
> <ruta>` a un temporal fuera del repo, y el zip de S143) y la referencia de MIROVA. No toca `pipeline/` ni los
> perfiles. No despacha nada. Definiciones y tolerancias en [`PREREGISTRO.md`](PREREGISTRO.md), escrito antes
> de correr (mismo commit: git no prueba el orden). Todas las tablas salen de `e_resumen.py`
> (`e_resumen_salida.md`), que lee las salidas JSON de los scripts.

## En una línea

**En VIIRS 375 el déficit de magnitud no se puede repartir con precisión entre «contamos menos píxeles» y
«restamos más fondo»: el reparto depende de la bisagra que se elija, y con las dos razonables el fondo va de
21 a 64 % del déficit.** Lo que sí está medido con nuestros datos: el recorte del tablero pesa poco en Láscar,
Isluga y Tupungatito y mucho en Lastarria. Entre las palancas ya construidas, la que más mueve la magnitud hacia
MIROVA es el fondo por vecinos (D25): factor 1,28 [1,21; 1,35] en los mismos records, cerca del 60 % del déficit
de su brazo de comparación, más en las pasadas oblicuas. Quitar keep_peak (1,05) y quitar la compuerta D22 (1,03)
también van en la dirección correcta, mucho menos; la conectiva `max` y quitar el Test 1 la bajan. La
dependencia con el ángulo de la pasada **no** se puede atribuir al remuestreo de MIROVA (D17).

## 1. El fenómeno

Un foco volcánico chico (fumarola, lago de lava, domo) ocupa una fracción de un píxel. MIROVA calcula la
potencia de una pasada como k·A·Σ(L_píxel − L_fondo) sobre **todos** los píxeles que alertó (Campus et al. 2022,
§3.2; D32), con el fondo de cada uno igual a la media de sus vecinos no alertados (Campus 2024; D25). Nosotros
usamos la misma fórmula con el mismo k y la misma A (S139; acá el OSF cumple VRP = k·A·(ΣL_hot − ΣL_bk) con
error relativo máximo 8,9e-8). La diferencia puede venir de:

- **Qué sumamos (selección)**: cuántos píxeles entran (alertamos menos) y qué tan calientes son (los nuestros
  son los más calientes del foco).
- **Cuánto restamos (fondo)**: la mediana de un anillo de 5 a 25 km, o el fondo del Test 1 en las pasadas
  donde dispara; MIROVA, la media de los vecinos. En un cono nevado con valles tibios el anillo es más tibio
  que los vecinos del cráter, y cada kelvin de fondo de más se come parte de un exceso de pocos kelvin.
- **Qué publicamos (recorte)**: el tablero muestra el núcleo F5' (VIIRS 375) o el cúmulo con el modo de un
  píxel (VIIRS 750 y MODIS), no la suma de nuestros alertados.

## 2. Qué es medición y qué es identidad

Por pasada, con D lo publicado, S_in la suma de nuestros alertados dentro del inner y V_M el VRP de MIROVA:

    R = D / V_M = F_rec · F_n · F_hot · F_bg

- **F_rec = D / S_in es lo único medido sólo con nuestros datos.**
- F_n, F_hot y F_bg necesitan el Npix y las radiancias de MIROVA, que sólo trae el **OSF v2.5 de 2025** (parte
  A). El fondo nuestro que entra (Lbg) es el **implícito**, definido para que la suma de nuestros píxeles cierre:
  el producto reproduce R **por construcción** (error 2,3e-14). Eso no es un control de la física, es aritmética.
- El reparto entre F_hot y F_bg exige una **bisagra**: medir el fondo a nuestro nivel caliente o al de MIROVA. Las
  dos son igual de legítimas y dan repartos muy distintos (Tabla A2). Se informan las dos y el promedio de las
  dos órdenes, que es el valor de Shapley. **Los intervalos cubren sólo el muestreo (bootstrap por noche), no la
  elección de la bisagra.**
- En 2026 la referencia NRT trae sólo el VRP, y la razón se separa en **F_rec · G** (parte B).
- **No está verificado que el OSF de 2025 valga como vara del NRT** (A105: el OSF es un producto filtrado con
  clase automática): no hay solape entre el OSF y la referencia NRT del scraper con qué comprobarlo.

## 3. Resultados

### 3.1 VIIRS 375, 2025 contra el OSF (parte A; tablas completas en `e_resumen_salida.md`)

R 0,69 [0,66; 0,71] en 1.474 pasadas. Reparto del déficit en escala logarítmica, sobre las pasadas donde existen
las dos bisagras:

| estrato | pasadas | recorte | selección / fondo, bisagra nuestra | bisagra MIROVA | Shapley |
|---|---|---|---|---|---|
| VIIRS 375, todos | 1.438 | 47 % [38; 58] | 32 % / 21 % | -12 % / 64 % | 10 % / 43 % |
| sin kernel local (Láscar, Isluga, Copahue) | 741 | 2 % | 63 % / 35 % | 34 % / 64 % | 48 % / 49 % |
| Láscar | 383 | 1 % | 71 % / 28 % | 46 % / 53 % | 59 % / 40 % |
| Isluga | 333 | 3 % | 59 % / 38 % | 25 % / 72 % | 42 % / 55 % |
| Lastarria | 230 | 62 % [45; 87] | -4 % / 42 % | -51 % / 89 % | -28 % / 66 % |

**Lectura.** En Láscar e Isluga el recorte no pesa: el déficit es selección más fondo, y según la bisagra el
fondo es entre un cuarto y tres cuartos de él (Shapley: mitad y mitad). En Lastarria pesan el recorte y el fondo.
En los volcanes con kernel local (Cordón Caulle con inner de 20 km, Chaitén, Planchón-Peteroa, Villarrica) R está
cerca de 1 o sobre 1 y las fracciones no significan nada. Tupungatito no tiene pares clase 1 del OSF en 2025.

### 3.2 El ángulo de la pasada no es la firma del remuestreo (arreglo c)

El déficit crece con el ángulo cenital (VIIRS 375 sin kernel: R 0,76 a nadir, 0,45 en el borde). Si eso fuera el
remuestreo de MIROVA (D17), su Npix crecería hacia el borde, porque un píxel oblicuo más grande se repartiría en
más celdas. **No crece**: medianas de 3, 5, 5 y 4 en las cuatro bandas (Tabla A3), y en Isluga 3, 3, 4 y 5 sin
saltos que sigan al área. Lo que sí cambia con el ángulo es el fondo: F_bg cae de 0,85 a nadir a 0,73 en el
borde (sin kernel), y en Láscar de 0,93 a 0,70. O sea que parte de la dependencia angular es fondo, no conteo, y
el «37 % por ángulo» de la versión anterior (calculado dentro de la selección) no se puede leer como el tamaño
de D17. Queda **SIN ATRIBUIR**: la dependencia existe, su mecanismo no está identificado.

### 3.3 VIIRS 375, 2026 contra la referencia NRT (parte B)

| tramo de calendario | estrato | pasadas / noches | R | F_rec | G |
|---|---|---|---|---|---|
| abr a ago | todos | 916 / 543 | 0,61 [0,58; 0,65] | 0,88 [0,86; 0,91] | 0,69 [0,65; 0,74] |
| | Láscar | 200 / 110 | 0,47 [0,43; 0,51] | 1,00 | 0,47 [0,43; 0,51] |
| | Isluga | 192 / 108 | 0,54 [0,49; 0,58] | 0,98 | 0,55 [0,50; 0,60] |
| | Lastarria | 119 / 79 | 0,35 [0,28; 0,43] | 0,86 [0,81; 0,90] | 0,41 [0,32; 0,51] |
| | Tupungatito | 104 / 68 | 0,61 [0,55; 0,67] | 1,00 | 0,61 [0,55; 0,67] |
| 29 ago a 14 oct | todos | 259 / 144 | 0,66 [0,59; 0,72] | 0,89 [0,85; 0,93] | 0,74 [0,65; 0,83] |
| | Láscar | 41 / 22 | 0,60 [0,53; 0,70] | 0,97 | 0,62 [0,53; 0,73] |
| | Isluga | 73 / 37 | 0,53 [0,46; 0,61] | 0,98 | 0,54 [0,47; 0,62] |
| | Tupungatito | 25 / 16 | 0,41 [0,26; 0,60] | 1,00 | 0,41 [0,26; 0,60] |
| | Nevados de Chillán | 34 / 14 | 0,57 [0,48; 0,70] | 0,91 | 0,63 [0,51; 0,80] |

El F_rec es medición pura y confirma lo de 2025: en Láscar, Isluga y Tupungatito publicamos lo que alertamos, y
todo el déficit está en G (selección y fondo juntos, sin forma de separarlos sin el Npix de MIROVA).

**Régimen de código contra ventana de calendario (arreglo b).** El tramo «abr a ago» de producción es de
**código anterior a #535**: ninguno de sus 17.450 records tiene hora de proceso. El tramo «29 ago a 14 oct» se
procesó del 2026-09-03 al 2026-10-14 (4.879 de 5.460 con hora). En cambio **todos los brazos de A/B de la
parte C se procesaron entre el 2026-09-17 y el 2026-09-22, con código posterior a #535**, aunque cubran ventanas
de marzo a septiembre. La versión anterior decía que los brazos eran «de antes de #535»: era falso. Consecuencia:
la parte B y la parte C **no son comparables en los mismos meses**; un mismo junio es código viejo en B y código
nuevo en C.

### 3.4 Las palancas ya construidas, medidas en las mismas pasadas (parte C)

| palanca (brazo A → brazo B) | ventana de calendario | pasadas | B / A | déficit de A que cierra |
|---|---|---|---|---|
| **fondo por vecinos D25** (literal sin D25 → literal) | jun a ago | 468 | **1,28 [1,21; 1,35]** | 60 % [51; 70] |
| literal entero (control → D22 + D25 + sin keep_peak) | jun a ago | 478 | 1,23 [1,18; 1,28] | 55 % [46; 65] |
| quitar keep_peak | jun a ago | 478 | 1,05 [1,02; 1,07] | 22 % [12; 33] |
| quitar la compuerta D22 | jun a ago | 423 | 1,03 [1,02; 1,05] | 17 % [9; 27] |
| conectiva `max` (sobre la base sin Test 1) | may a sep | 824 | 0,93 [0,91; 0,94] | -18 % [-24; -14] |
| quitar el Test 1 integrado | 1 a 20 sep | 124 | 0,88 [0,81; 0,94] | -38 % [-66; -19] |
| **nulo**: gemelo del control | mar, Láscar | 88 | **1,00 exacto** | 0 % |

Por volcán, D25: Isluga 1,72, Tupungatito 2,37, Láscar 1,20, Lastarria 0,91 (empeora), y 0,99 a 1,00 en los
volcanes con kernel local. **El 1,28 se midió dentro del brazo `literal`** (sin compuerta, sin keep_peak, segundo
pase condicionado): ningún brazo corrido es «producción más D25».

**D25 por banda de ángulo** (Tabla C2): 1,18 [1,12; 1,24] a nadir, 1,22, 1,36 y 1,41 [1,27; 1,60] en el borde;
con efecto fijo por volcán, 1,00 / 1,08 [1,00; 1,17] / 1,17 [1,05; 1,33] / 1,20 [1,07; 1,33]. **D25 sí actúa sobre
la dependencia angular**, coherente con que el fondo empeore hacia el borde (§3.2). La versión anterior decía lo
contrario.

### 3.5 VIIRS 750 y MODIS

- **VIIRS 750**: el recorte pesa (F_rec 0,71 en los dos tramos de 2026: el cúmulo con el modo de un píxel y la
  magnitud focal contra la suma de los alertados del inner, tarea 1.8). En 2025 (sólo Láscar, 17 pasadas) el
  recorte es 39 %; selección y fondo, 44 / 17 % con nuestra bisagra y 23 / 38 % con la de MIROVA. La conectiva
  `max` y el Test 1 no cambian ninguna pasada de VIIRS 750.
- **MODIS**: en 2026 publicamos 6 pasadas con alerta antes de #535 y ninguna después (45 y 7 no publicadas, la
  etiqueta `far` de A82): no hay magnitud que descomponer. En 2025 (Láscar, 35 pasadas) el fondo explicaba más
  que todo el déficit con cualquier bisagra (F_bg 0,47 [0,42; 0,53] con la nuestra) y la selección suma **más**
  que MIROVA. Con la banda 22, MODIS publica 37 pasadas con alerta en Láscar, con R 0,42 [0,34; 0,52].

## 4. Controles

| control | resultado | consecuencia |
|---|---|---|
| C6 auto-audit reproducido | 11 de 11 volcanes dentro de ±0,05 | los datos se cargan igual que en el auto-audit. No prueba que el auto-audit mida un objeto limpio: junta VIIRS 375 con VIIRS 750 y su ventana cruza #535 |
| C3 réplica del núcleo F5' | 100 % (1.499, 4.778 y 1.978 records) | en VIIRS 375 F_rec es recorte puro |
| C2 cúmulo de un píxel | **2025: 100 % de 869**. 2026: VIIRS 375 89 a 94 % antes de #535 y 97 a 100 % después; VIIRS 750 97 a 98 %; **MODIS 79 a 87 %** | la falla de MODIS es **sólo de 2026**: ahí su `pc.vrp_mw` no siempre sale de los píxeles guardados (magnitud focal) y su F_rec queda SIN DATO como recorte puro. El F_rec de MODIS 2025 sí es recorte |
| C4 fondo implícito contra anillo (2025) | 93,4 % de 2.008 píxeles; VIIRS 375 con Test 1: 90,8 % de 1.450 | **en 2025 el Test 1 dispara en 1.462 de 1.474 pares VIIRS 375**, y aun así el fondo implícito es sobre todo el del anillo |
| C1 píxel = k·A·(L(bt) − fondo del anillo), 2026 | sin Test 1: MODIS 99,6 %, VIIRS 375 100 %, VIIRS 750 93 %; con Test 1: 25 %, 59 % y 12 % | en 2026 las pasadas con Test 1 usan otro fondo por píxel. Es de 2026; no se aplica a la parte A |
| C5 pareo corrido 6 h | 0 de 1.552 (A); 3 de 1.287 y 0 de 360 (B) | el pareo no empareja azar |
| C7 identidad | 2,3e-14 (código); 8,9e-8 (consistencia del OSF) | es aritmética, no física (§2) |
| nulo de la parte C | gemelo: B/A = 1,00 exacto en 88 pasadas; la banda 22 deja VIIRS en 1,00 exacto | el instrumento de brazos no inventa efectos |
| T2 campo del TIF comparable (parte D) | **falla**: 18,5 % de 27 pasadas con el anillo del TIF a ±3 % del nuestro | el fondo medido en el GeoTIFF de MIROVA queda SIN DATO |

## 5. Recomendación para el siguiente A/B

**Medir D25 en VIIRS 375 como brazo propio, sobre producción (C0) y también sobre la base F** (sin Test 1),
con el flag que ya existe y está apagado (`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375`). Por qué:

1. Es la palanca construida que más mueve la magnitud hacia MIROVA (1,28, y más en las pasadas oblicuas), y es
   fidelidad literal (siete textos del grupo MIROVA, D25). Quitar keep_peak y quitar D22 también ayudan, pero
   poco (1,05 y 1,03).
2. Nunca se midió aislado: el 1,28 es dentro de `literal`.
3. **Sobre producción la sobre-publicación está saturada**: con el Test 1 encendido, producción publica en 734 de
   832 negativos limpios de VIIRS 375 (`experiments/_s151_prereg_fk_11/PREREGISTRO.md`, V1). Ahí el costo de D25
   en sobre-publicación (+0,052 en S143, medido sin keep_peak) no se vería (A114). Por eso **los negativos limpios
   se miden sobre F**, donde la métrica no está saturada.
4. Coordinarlo con el probe de D25 en VIIRS 750 (D-5, #793) y con el resultado del A/B de F y K (D-7, #798): si se
   adopta F, la base cambia (sin Test 1 la magnitud baja a 0,88 de producción y `max` a 0,93), y D25 es lo que
   podría devolverla.

Lo que el A/B tiene que mirar además: Lastarria, que empeora con D25; los volcanes con kernel local, donde no
cambia nada; y el efecto por banda de ángulo.

**Para la decisión D-1 (conectiva `max`)**: cuesta 7 % de magnitud en VIIRS 375 (824 pasadas, cinco meses), y más
en el borde del barrido (0,85 en la banda de 50° o más).

## 6. Lo que no se pudo resolver

- **El reparto selección contra fondo** no está identificado: depende de la bisagra (§2, §3.1).
- **El mecanismo de la dependencia angular**: no es el conteo remuestreado de MIROVA (su Npix no crece), y el
  fondo explica una parte; el resto queda sin atribuir.
- **La validez del OSF 2025 como vara del NRT** (A105): sin solape con qué comprobarla.
- **El conteo de MIROVA en 2026**: no hay OSF de 2026; el GeoTIFF no trae la máscara de alertados (A24) y su
  campo no pasó el control T2. El archivo local de TIF llega sólo al 2026-05-20 (checkout atrasado, sin pull).
- **D25 sobre producción y sobre F**: no hay brazo corrido; el 1,28 es del contexto `literal`.
- **MODIS en el régimen actual**: sin pasadas con alerta publicadas no hay razón que descomponer (A82).
- **Tupungatito en 2025**: sin pares del OSF.

## 7. Enmiendas posteriores a ver datos (declaradas)

1. **C7**: el pre-registro pedía error < 1e-9 contra D / V_M; dio 8,9e-8 porque el producto reproduce
   D / (k·A·Npix·(L_hot − L_bk)), no D / V_M. Se separaron las dos cosas.
2. **C1**: el pre-registro excluía sólo `test1_roi`. El agregado pasaba (96,2 %) porque MODIS aporta casi todos
   los píxeles; el desglose por sensor y por Test 1 es el que se informa.
3. Agregados tras la primera corrida: F_sel = F_n · F_hot, la fracción del ángulo con intervalo y la marca
   «R casi 1». La parte D (TIF) se escribió después de A, B y C, con sus controles en el docstring de
   `d_tif_fondo.py` antes de correrla.
4. **Verificador con contexto limpio de #814** (PARCIAL; confirmó la reconstrucción y los factores de las
   palancas). Arreglos aplicados en el mismo PR: (a) reparto como rango con las dos bisagras y Shapley, y aviso de
   que la descomposición es una identidad y de que el IC sólo cubre el muestreo; (b) régimen de código separado
   de la ventana de calendario, con la hora de proceso de cada brazo y de cada tramo; (c) retirada la atribución
   del ángulo a D17 y la frase «D25 no toca la parte del ángulo», con el efecto de D25 por banda con intervalo;
   (d) «la única palanca» pasó a «la que más mueve»; (e) recomendación de medir D25 sobre C0 y sobre F, con
   negativos limpios en F; (f) la falla de C2 en MODIS acotada a 2026; (g) la validez del OSF como vara del NRT,
   declarada sin verificar. Lo que cayó de la versión anterior: «tres tercios», «el ángulo es D17» y «D25 no toca
   el ángulo». Lo que sigue en pie: F_rec, los factores de las palancas y la recomendación de medir D25, ahora
   con otro diseño.

## 8. Reproducir

```bash
cd experiments/_s151_presupuesto_magnitud
python a_osf_exacto.py --osf "<ruta>/VRP_GLOBAL_ARCHIVE_2025.csv"
python b_regimen_actual.py --dest <temporal>        # baja la referencia de Mirova-v1 por la API (sha en la salida)
git archive origin/s146-ab/<run> experiments/_s146_ab_sin_test1/salidas/<run> | tar -x -C <temporal>/ab   # runs en c_palancas_ab.py
python c_palancas_ab.py --ab <temporal>/ab --s143 <temporal>/s143 --dest <temporal>
python d_tif_fondo.py --tif-dir <ruta local de mirova-tif-archive>
python e_resumen.py
```

La referencia de MIROVA se baja en cada corrida y su sha queda en las salidas (la corrida final de B y C usó el
consolidado `e54c1018af65a6062e2d6c08a4bd5a9d371012fb` y el OCR `03cab0e74aa2bb672c2b113f8f380af50e0a36e0`; con
los consolidados de corridas anteriores los factores de C no cambiaron). Records de `data/mirova_equivalent/` en
la base de la rama (`b316b9295`). Los CSV de pares quedan fuera de git por `.gitignore` y se regeneran.
