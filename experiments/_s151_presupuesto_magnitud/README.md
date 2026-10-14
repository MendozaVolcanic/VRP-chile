# Tarea 1.14 (estudio A): presupuesto de la magnitud, pasada por pasada

> Escrito el 2026-10-14 por el loop (tarea 1.14 de `tasks/LOOP_OBJETIVOS.md`). Sin correr el pipeline: sólo
> records en disco, salidas de A/B ya corridos (ramas `s146-ab/<run>`, extraídas con `git archive <ref> <ruta>`
> a un temporal fuera del repo, y el zip de S143) y la referencia de MIROVA. No toca `pipeline/` ni los perfiles.
> No despacha nada. Definiciones y tolerancias en [`PREREGISTRO.md`](PREREGISTRO.md), escrito antes de correr
> (mismo commit: git no prueba el orden). Todas las tablas salen de `e_resumen.py` (`e_resumen_salida.md`).

## En una línea

**En VIIRS 375 el déficit de magnitud se reparte en tres partes de tamaño parecido, y la única palanca ya
construida que lo mueve en la dirección correcta es el fondo por vecinos (D25): en los mismos records cierra el
60 % del déficit (factor 1,28 [1,21; 1,35]), sobre todo en Isluga y Tupungatito.** La conectiva `max` y quitar
el Test 1 lo empeoran. La parte que depende del ángulo de la pasada (la firma del remuestreo de MIROVA, D17) es
el otro tercio y no tiene palanca construida. En MODIS la magnitud no se puede medir hoy (casi no publicamos
en pasadas con alerta), y en 2025 la explicaba casi entera el fondo.

## 1. El fenómeno

Un foco volcánico chico (fumarola, lago de lava, domo) ocupa una fracción de un píxel. MIROVA calcula la
potencia de una pasada como k·A·Σ(L_píxel − L_fondo) sobre **todos** los píxeles que alertó (Campus et al. 2022,
§3.2; D32), con el fondo de cada uno igual a la media de sus vecinos no alertados (Campus 2024; D25), y sobre su
imagen remuestreada a una grilla de celdas de área fija. Nosotros usamos la misma fórmula con el mismo k y la
misma A (S139, verificado de nuevo acá: el OSF cumple VRP = k·A·(ΣL_hot − ΣL_bk) con error relativo máximo
8,9e-8). Entonces la diferencia sólo puede venir de tres cosas:

- **Qué sumamos (selección)**: cuántos píxeles entran y qué tan calientes son. En una pasada oblicua el píxel
  real de VIIRS crece; MIROVA lo reparte en más celdas de su grilla y las suma todas; nosotros contamos un
  píxel con área de nadir. Eso hace que el déficit crezca con el ángulo cenital.
- **Cuánto restamos (fondo)**: restamos la mediana de un anillo de 5 a 25 km (o un fondo local del Test 1 en
  las pasadas donde dispara); MIROVA, la media de los vecinos del píxel. En un cono nevado con valles tibios el
  anillo es más tibio que los vecinos del cráter, y cada kelvin de fondo de más se come parte de un exceso que
  es de pocos kelvin.
- **Qué publicamos (recorte)**: el tablero no muestra la suma de nuestros alertados sino el núcleo F5' (VIIRS
  375) o el cúmulo con el modo de un píxel (VIIRS 750 y MODIS).

## 2. La identidad que se descompone

Por pasada, con D lo publicado, S_in la suma de nuestros alertados dentro del inner, V_M el VRP de MIROVA:

    R = D / V_M = F_rec · F_sel · F_bg        F_sel = F_n · F_hot

F_rec = D / S_in; F_n = píxeles nuestros con energía / Npix de MIROVA; F_hot y F_bg separan el exceso por píxel
en nivel caliente y fondo, usando como bisagra el fondo de MIROVA. Es exacta (control C7: 2,3e-14) pero
necesita Npix y la radiancia de fondo de MIROVA, que sólo trae el **OSF v2.5 de 2025** (parte A). En 2026 la
referencia NRT trae sólo el VRP, y la razón se separa en **F_rec · G** (parte B), donde G junta conteo, nivel y
fondo. Dentro de F_sel (o de G) se aísla la parte que depende del ángulo cenital: el efecto de cada banda de
ángulo contra la de nadir (0 a 20°), con efecto fijo por volcán. Las fracciones del déficit son en escala
logarítmica: media de ln F sobre media de ln R. Intervalos al 95 % por bootstrap de **noches** (2.000 réplicas;
1.000 para el ángulo), porque las pasadas de una misma noche no son independientes. Con R casi 1 la fracción no
significa nada y se marca así.

## 3. Resultados

### 3.1 VIIRS 375, el sensor que publica (tablas completas en `e_resumen_salida.md`)

**2025, descomposición exacta contra el OSF** (1.474 pasadas, 948 noches):

| estrato | R | F_rec | F_sel | de F_sel, ángulo | F_bg | reparto rec / sel / fondo | dentro de sel, ángulo |
|---|---|---|---|---|---|---|---|
| VIIRS 375, todos | 0,69 [0,66; 0,71] | 0,85 [0,82; 0,87] | 0,90 [0,86; 0,93] | 0,87 [0,84; 0,90] | 0,90 [0,88; 0,93] | 43 % / 29 % / 28 % | 37 % [27; 48] |
| sin kernel local (Láscar, Isluga, Copahue) | 0,56 [0,54; 0,58] | 0,99 [0,98; 0,99] | 0,70 [0,68; 0,72] | 0,79 [0,76; 0,82] | 0,81 [0,79; 0,83] | 2 % / 62 % / 36 % | 41 % [35; 47] |
| Láscar | 0,57 [0,54; 0,59] | 1,00 | 0,68 [0,66; 0,70] | 0,79 [0,75; 0,82] | 0,84 [0,82; 0,86] | 1 % / 69 % / 30 % | 42 % [35; 49] |
| Isluga | 0,54 [0,51; 0,58] | 0,98 | 0,70 [0,66; 0,74] | 0,78 [0,72; 0,82] | 0,79 [0,77; 0,81] | 3 % / 59 % / 38 % | 42 % [33; 51] |
| Lastarria | 0,61 [0,55; 0,68] | 0,80 [0,77; 0,83] | 1,01 [0,94; 1,09] | 0,96 [0,85; 1,09] | 0,75 [0,68; 0,82] | 45 % / -3 % / 58 % | 8 % [-19; 33] |

Tupungatito no tiene pasadas clase 1 del OSF pareadas en 2025 (S139 ya lo había visto).

**2026 contra la referencia NRT** (R = F_rec · G):

| tramo | estrato | pasadas / noches | R | F_rec | G | de G, ángulo | fracción del déficit por ángulo |
|---|---|---|---|---|---|---|---|
| abr a ago (antes de #535) | todos | 916 / 543 | 0,61 [0,58; 0,65] | 0,88 [0,86; 0,91] | 0,69 [0,65; 0,74] | 0,83 [0,77; 0,89] | 38 % [25; 52] |
| | Láscar | 200 / 110 | 0,47 [0,43; 0,51] | 1,00 | 0,47 [0,43; 0,51] | 0,71 [0,64; 0,79] | 45 % [33; 56] |
| | Isluga | 192 / 108 | 0,54 [0,49; 0,58] | 0,98 | 0,55 [0,50; 0,60] | 0,77 [0,69; 0,85] | 42 % [27; 55] |
| | Lastarria | 119 / 79 | 0,35 [0,28; 0,43] | 0,86 [0,81; 0,90] | 0,41 [0,32; 0,51] | 0,75 [0,54; 1,07] | 27 % [-7; 56] |
| | Tupungatito | 104 / 68 | 0,61 [0,55; 0,67] | 1,00 | 0,61 [0,55; 0,67] | 0,86 [0,75; 0,98] | 31 % [4; 57] |
| 29 ago a 14 oct (después) | todos | 259 / 144 | 0,66 [0,59; 0,72] | 0,89 [0,85; 0,93] | 0,74 [0,65; 0,83] | 0,85 [0,73; 0,96] | 38 % [12; 68] |
| | Láscar | 41 / 22 | 0,60 [0,53; 0,70] | 0,97 | 0,62 [0,53; 0,73] | 0,94 [0,79; 1,14] | 12 % [-31; 39] |
| | Isluga | 73 / 37 | 0,53 [0,46; 0,61] | 0,98 | 0,54 [0,47; 0,62] | 0,76 [0,62; 0,90] | 43 % [20; 67] |
| | Tupungatito | 25 / 16 | 0,41 [0,26; 0,60] | 1,00 | 0,41 [0,26; 0,60] | 0,55 [0,33; 0,97] | 67 % [4; 120] |
| | Nevados de Chillán | 34 / 14 | 0,57 [0,48; 0,70] | 0,91 | 0,63 [0,51; 0,80] | 0,74 [0,54; 0,98] | 53 % [4; 101] |

**Lo que dicen juntas.** En los volcanes con déficit grande (Láscar, Isluga, Tupungatito) el recorte del tablero
no pesa (F_rec 0,97 a 1,00): publicamos lo que alertamos. El déficit está entero en G, y G se parte en una
parte que depende del ángulo (0,71 a 0,86 en el tramo largo) y una de nadir. En 2025, donde se puede separar,
la parte de nadir es fondo (0,79 a 0,84) más un resto chico de selección (0,86 a 0,90 a nadir, que se lee en
`F_sel por banda z` de `a_osf_exacto_salida.txt`). Lastarria es otro caso: ahí pesan el recorte y el fondo, no
el ángulo. Los volcanes con kernel local (Puyehue-Cordón Caulle, Chaitén, Planchón-Peteroa, Villarrica) están
cerca de 1 o sobre 1, y Cordón Caulle compensa un recorte grande (F_rec 0,56) con una suma que duplica a MIROVA
(inner de 20 km): sumar todos los alertados no lo arreglaría, lo empeoraría.

### 3.2 Las palancas ya construidas, medidas en las mismas pasadas (parte C)

| palanca (brazo A → brazo B) | ventana | pasadas | B / A | déficit de A que cierra | por volcán |
|---|---|---|---|---|---|
| **fondo por vecinos D25** (literal sin D25 → literal) | jun a ago | 468 | **1,28 [1,21; 1,35]** | **60 % [51; 70]** | Isluga 1,72, Tupungatito 2,37, Láscar 1,20, Lastarria 0,91, volcanes con kernel 0,99 a 1,00 |
| literal entero (control → D22+D25+sin keep_peak) | jun a ago | 478 | 1,23 [1,18; 1,28] | 55 % [46; 65] | |
| quitar keep_peak | jun a ago | 478 | 1,05 [1,02; 1,07] | 22 % [12; 33] | |
| quitar la compuerta D22 | jun a ago | 423 | 1,03 [1,02; 1,05] | 17 % [9; 27] | |
| conectiva `max` (sobre la base sin Test 1) | may a sep, 5 meses | 824 | **0,93 [0,91; 0,94]** | **-18 % [-24; -14]** | Láscar, Isluga y Tupungatito casi 1; Lastarria 0,88 a 0,93; Cordón Caulle 0,74 a 0,86 según el mes |
| quitar el Test 1 integrado | 1 a 20 sep | 124 | 0,88 [0,81; 0,94] | -38 % [-66; -19] | Tupungatito 0,63, Láscar 0,80 |
| banda 22 con `max` en MODIS (efecto sobre VIIRS 375, sólo Láscar) | mar y jun | 92 | 0,98 [0,96; 0,99] | -4 % | |
| **nulo**: gemelo del control | mar, Láscar | 88 | **1,00 exacto** | 0 % | |

El fondo D25 mueve **G** (factor por G 1,28; por recorte 1,00), y en Isluga y Tupungatito sube también el número
de píxeles con energía (mediana 1 a 2): con un fondo más frío, píxeles que hoy quedan recortados a 0 MW
empiezan a aportar. Por eso su efecto en Isluga (1,72) es mayor que lo que la parte A atribuye al fondo solo
(F_bg de Isluga en 2025: 0,79): mueve fondo y conteo a la vez. Los brazos de A/B son todos de antes de #535 salvo el de
quitar el Test 1, y el de D25 viene del contexto `literal` (sin compuerta, sin keep_peak, segundo pase
condicionado), no de producción.

### 3.3 VIIRS 750 y MODIS

- **VIIRS 750**: el recorte sí pesa (F_rec 0,71 en los dos tramos de 2026: el cúmulo publicado
  con el modo de un píxel y la magnitud focal contra la suma de los alertados del inner, tarea 1.8). En 2025
  (sólo Láscar, 17 pasadas) el reparto fue recorte 39 %, selección 44 %, fondo 17 %. La conectiva `max` y el
  Test 1 no cambian ninguna pasada de VIIRS 750 (B/A 1,00 en 118 y 13 pasadas). En la erupción de Chillán
  (post #535, 21 pasadas) R 0,47 con F_rec 0,78 y G 0,61; n chico.
- **MODIS**: en 2026 casi no hay qué medir: con alerta de MIROVA publicamos 6 pasadas antes de #535 y ninguna
  después (45 y 7 no publicadas, la etiqueta `far` de A82). En 2025 (Láscar, 35 pasadas) el fondo explicaba
  el déficit entero (F_bg 0,47 [0,42; 0,53], 4,2 K de fondo de más), con una selección que **suma más** que
  MIROVA (F_sel 1,86) y un recorte de 0,53 que no es interpretable (control C2 falla en MODIS, ver §4). Con la
  banda 22 MODIS publica 37 pasadas con alerta en Láscar, con R 0,42 [0,34; 0,52].

## 4. Controles (cada uno podía fallar)

| control | resultado | consecuencia |
|---|---|---|
| C3 réplica del núcleo F5' | 100 % en las tres poblaciones (1.499, 4.778, 1.978) | lo publicado en VIIRS 375 sale exactamente de los píxeles: F_rec es recorte puro |
| C2 cúmulo de un píxel reconstruido | 2025: 100 % (869). 2026: VIIRS 375 89 a 94 % antes de #535 (falla en records con Test 1) y 97 a 100 % después; VIIRS 750 97 a 98 %; **MODIS 79 a 87 %** | **F_rec de MODIS queda SIN DATO como recorte puro**: su `pc.vrp_mw` no siempre sale de los píxeles guardados (magnitud focal). En VIIRS 750 queda justo bajo el 98 % pre-registrado y se informa marcado. En VIIRS 375 no afecta: lo publicado es el núcleo F5', que C3 reconstruye entero |
| C1 píxel = k·A·(L(bt) − fondo del anillo) | agregado 96,2 % (pasa), pero **sólo en records sin Test 1**: MODIS 99,6 %, VIIRS 375 100 %, VIIRS 750 93 %; con Test 1: 59 %, 12 % y 25 % | hallazgo: en las pasadas donde dispara el Test 1 el VRP por píxel usa **otro fondo** (el anillo intermedio o el global del Test 1), no el del anillo de 5 a 25 km. La descomposición no lo supone (usa el fondo implícito exacto), pero «nuestro fondo» es una mezcla |
| C4 fondo implícito contra anillo (2025) | 93,4 % de 2.008 píxeles | pasa |
| C5 pareo corrido 6 h | 0 de 1.552 (A); 3 de 1.287 y 0 de 360 (B) | el pareo no empareja azar |
| C6 auto-audit reproducido | 11 de 11 volcanes dentro de ±0,05 (Láscar 0,442, Isluga 0,516, Lastarria 0,559, Tupungatito 0,647 exactos) | estamos midiendo los mismos objetos que el auto-audit |
| C7 identidad | 2,3e-14 (código); 8,9e-8 (consistencia del OSF) | ver enmienda 1 |
| nulo de la parte C | gemelo del control: B/A = 1,00 exacto en 88 pasadas; la banda 22 de MODIS deja VIIRS en 1,00 exacto | el instrumento de brazos no inventa efectos |
| T2 campo del TIF comparable (parte D) | **falla**: sólo 18,5 % de 27 pasadas con el anillo del TIF a ±3 % del nuestro (mediana 1,049) | **el fondo medido en el GeoTIFF de MIROVA queda SIN DATO** |

## 5. Lo que recomiendo para el siguiente A/B

**El fondo por vecinos (D25) en VIIRS 375, aislado sobre la base de producción**, con el flag que ya existe y
está apagado (`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375`). Por qué éste y no otro:

1. Es la única palanca construida que mueve la magnitud hacia MIROVA: cierra 60 % [51; 70] del déficit en los
   mismos records, y en Isluga y Tupungatito casi entero (77 y 89 %). Las otras dos que existen (conectiva
   `max`, quitar el Test 1) la bajan.
2. Es fidelidad literal (siete textos del grupo MIROVA, D25), no un parche: pasa la pregunta 1 de MISSION.
3. Nunca se midió solo sobre producción: S143 lo midió dentro de `literal`, y antes de #535.

Lo que el A/B tiene que mirar además de la magnitud: (a) **la sobre-publicación**, porque en S143 D25 la subía
(+0,052 en negativos limpios, H_S143_D22_D25) y la brecha dominante del proyecto sigue siendo ésa (A98); (b)
**Lastarria**, que empeora con D25 (0,91), y los volcanes con kernel local, donde no cambia nada; (c) el estrato
de ángulo, porque D25 no toca la parte que depende del ángulo y no hay que leer su efecto como si cerrara todo.

**Lo que no recomiendo todavía**: el remuestreo (D17, estudio B propuesto). Es el otro tercio del déficit (37 %
en 2025, 38 % en 2026 en VIIRS 375; 41 a 45 % en Láscar e Isluga), pero no está construido y su tamaño medido
acá es una cota: la dependencia con el ángulo también puede venir de que el foco se diluye en un píxel más
grande, cosa que el remuestreo no arregla. Va después de D25, con este presupuesto como línea base.

**Para la decisión D-1 (conectiva `max`)**: su costo en magnitud es 7 % [6; 9] en VIIRS 375 (824 pasadas, cinco
meses), concentrado en Lastarria y Cordón Caulle. No cambia el veredicto de sobre-publicación, pero es un costo
que la decisión debe conocer.

## 6. Lo que no se pudo resolver

- **El conteo de MIROVA en 2026.** No hay OSF de 2026; el GeoTIFF no trae la máscara de alertados (A24), y su
  campo no pasó el control de comparabilidad (T2). La separación conteo contra fondo en 2026 sale sólo de los
  brazos de A/B, no de MIROVA.
- **El archivo local de TIF llega al 2026-05-20**, no al 2026-09-22: el checkout de `mirova-tif-archive` está
  atrasado y la regla prohíbe pull. La parte D usó 11 días (52 pasadas con alerta, 27 atribuidas), todas antes
  de #535.
- **Ningún brazo de D25 después de #535**: el factor 1,28 es de junio a agosto.
- **MODIS en el régimen actual**: sin pasadas con alerta publicadas no hay razón que descomponer; el problema
  ahí es la etiqueta (A82), no la magnitud.
- **Tupungatito en 2025**: sin pares del OSF; su reparto sólo viene de 2026 y de los brazos.
- **La parte de nadir de G en 2026** (fondo más selección a nadir) no se separa sin Npix; se infiere de 2025.

## 7. Enmiendas posteriores a ver datos (declaradas)

1. **C7**: el pre-registro pedía error < 1e-9 entre el producto de los factores y D / V_M. Dio 8,9e-8 porque
   el producto reproduce D / (k·A·Npix·(L_hot − L_bk)), no D / V_M: la diferencia es la consistencia del propio
   OSF. Se separaron las dos cosas; la identidad de código da 2,3e-14.
2. **C1**: el pre-registro excluía sólo `final_hotspot_source == test1_roi`. El agregado pasa (96,2 %) porque
   MODIS aporta casi todos los píxeles; el desglose por sensor y por Test 1 se agregó después de ver el
   resultado, y es el que se informa.
3. Se agregaron después de la primera corrida: el factor de selección F_sel = F_n · F_hot (F_n solo exagera
   porque MIROVA suma vecinos tibios de poco exceso), la fracción del ángulo con intervalo y la marca «R casi 1».
4. La parte D (TIF) se escribió después de A, B y C; sus controles están en el docstring de `d_tif_fondo.py`,
   escritos antes de correrla.

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

Referencia de MIROVA usada en B y C: consolidado `7c6af1c0c1c8afd58d7bfc70e37aba2ff862c015`, OCR
`03cab0e74aa2bb672c2b113f8f380af50e0a36e0`. Records de `data/mirova_equivalent/` en la base de la rama
(`b316b9295`). Los CSV de pares (`*_pares.csv`) quedan fuera de git por `.gitignore` y se regeneran.
