# Frente C de la auditoría S149: brechas medidas por sensor, y metas

> Auditor del frente C, 2026-09-21. Sólo lectura sobre el repo. Todo número de este informe salió de un
> script mío corrido en esta sesión; los scripts y sus salidas están en
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s149_audit\frente_c\`.
> Lo que no medí va rotulado SOSPECHA o SIN VERIFICAR.

## 0. Resumen para quien decide

Qué pasa físicamente, antes que los números:

1. **VIIRS 375 no pierde nada y grita casi siempre.** Hoy publica en el 100 % de las pasadas en que
   MIROVA alertó (154 de 154) y también en el 87 % de las pasadas que MIROVA listó con VRP 0 en noches
   sin alerta (361 de 416). De cada 100 publicaciones nuestras de VIIRS 375 en pasadas que MIROVA listó,
   sólo 25 coinciden con una alerta suya. La brecha de este sensor es de un solo lado: callar.
2. **VIIRS 750 pierde una de cada tres o cuatro alertas de MIROVA, y no por falta de sensibilidad.** En las
   23 alertas perdidas desde el 13 de junio el píxel del cráter SÍ se detecta, en su lugar (a menos de
   1,4 km), pero su magnitud se calcula como 0,0 MW porque el píxel de la cumbre es más frío que el fondo
   del anillo (20 de 23 casos), y el tablero no publica un cúmulo sin energía. Es la cumbre alta y fría
   contra un entorno más bajo y tibio: el exceso espectral existe, el exceso de radiancia absoluta no.
   Pasa con el Test 1 encendido, o sea que el hallazgo de hoy (72 a 77 % en el control sin Test 1) se
   confirma en producción y no lo causa haber apagado el Test 1.
3. **MODIS en producción no distingue las noches en que MIROVA alerta de las que no.** De 77 alertas MODIS
   de MIROVA desde marzo (76 de Láscar) producción publica 9 (11,7 %), y en negativos limpios publica
   11,5 %: la misma tasa. En las 68 perdidas hay detección y cúmulo con energía dentro del radio interior
   (a 0,5 a 3,2 km del cráter), pero el record queda etiquetado `far` con
   `discarded_reason = partial_eruption_hotspot_too_far` y el tablero lo oculta. No es pérdida sub-píxel:
   MIROVA reporta ahí 0,2 a 3,8 MW. Y no se arregla quitando la etiqueta, porque ese mismo cúmulo con
   energía dentro del radio interior existe en el 90 % de los negativos limpios. El hallazgo de hoy
   (0 de 11 en Láscar en mayo sin Test 1) se confirma en su sustancia: producción publica 2 de esas 11.
4. **MIROVA contra sí misma** da la vara de lo alcanzable: si una pasada VIIRS 375 alerta, otra pasada
   de la misma noche y sensor alerta sólo el 53 % de las veces (78 a 85 % cerca del nadir, 29 a 33 % en el
   borde del barrido), y su magnitud entre pasadas de una misma noche cambia típicamente por un factor
   1,8 a 2,0. Sobre la misma escena, VIIRS 750 de MIROVA confirma apenas el 15 a 19 % de las alertas de
   VIIRS 375, pero cuando 750 alerta, 375 alerta el 95 % de las veces.

## 1. Método, ventanas e instrumento

- **Datos nuestros**: `data/mirova_equivalent/*.json` tal como están en el árbol hoy (producción, perfil
  `mirova_equivalent`). **Referencia**: snapshot del repo
  `data/mirova_reference/mirova_v1_snapshot/` (consolidado llega al 2026-09-21 12:50 UTC, leído con `tail`),
  cargado con `referencia_mirova_unificada.cargar_referencia_unificada`. Sin red.
- **"Publicar"** es el predicado del tablero ejecutado con node desde `frontend/index.html`
  (`scripts/banco_paridad.py:99-150`, `correr_node`), no una copia. El etiquetador es
  `banco_paridad.etiquetar` (`scripts/banco_paridad.py:275-300`).
- **Unidad**: la pasada de MIROVA (filas del mismo volcán y sensor a menos de 120 s). El cruce con el
  etiquetador del banco, que usa como unidad el record nuestro, da los mismos conteos en los tres
  sensores y las tres ventanas (línea "cruce con el banco" de cada salida).
- **Ventanas** (regla A104, medir por tramo; regla A119, el OCR decide sólo desde el 2026-06-13):
  - **HOY**: 2026-09-01 a 2026-09-21. Empieza el 1 de septiembre y no el 29 de agosto porque el
    2026-08-31 20:34 UTC entró #571 (quita el piso de VRP del perfil operacional; `git log` de
    `pipeline/profiles/mirova_equivalent.yaml`), que es otro cambio de régimen dentro de la ventana
    recomendada. Salida: `hoy_0901_0921.txt` y `.json`.
  - **ANTES DE #535**: 2026-06-13 a 2026-08-28. Salida: `pre535_0613_0828.txt`.
  - **MAYO**: 2026-05-01 a 2026-05-31, sólo para el hallazgo de Láscar; ahí decide la tabla sola
    (columna "tabla sola"). Salida: `mayo.txt`.
  - Para MODIS, que casi no tiene alertas en septiembre (1), la atribución usa 2026-03-01 a 2026-09-21
    (MODIS es completo y plano desde marzo, A119).
- **Las dos preguntas del instrumento.** P1: los controles `todo_publica` y `nada_publica` sobre los
  mismos denominadores dan 100 % y 0 % en E1 y E2 en los tres sensores y las tres ventanas; la identidad
  del predicado contra los 7 casos del guard da `True`. P2: toda tasa lleva su n, n = 0 se imprime
  SIN DATO; la repetición de MIROVA entre pasadas se contrasta con un barajado de las etiquetas dentro
  de cada volcán (VIIRS 375: 53 % real contra 35 a 37 % barajado; el barajado no baja a la tasa base de
  21 % porque conserva qué volcanes están activos, y eso es lo correcto: el exceso mide la coherencia de
  la noche, no la del volcán).
- **Límite declarado**: "alertas sin record nuestro" dio 0 en las tres ventanas. El contador puede dar
  distinto de cero (con `recs` vacío daría todas), pero no lo probé con un caso sembrado. SIN VERIFICAR
  como control positivo.

## 2. Estado de hoy por sensor (2026-09-01 a 2026-09-21)

Fuente: `experiments/_s149_audit/frente_c/hoy_0901_0921.txt`. Entre corchetes, intervalo de Wilson al 95 %.

| error | MODIS | VIIRS 750 | VIIRS 375 |
|---|---|---|---|
| E1. Publica donde MIROVA listó VRP 0 (negativo limpio) | 12,5 % (60 de 479) [9,9 a 15,8] | 22,8 % (158 de 692) [19,9 a 26,1] | **86,8 %** (361 de 416) [83,2 a 89,7] |
| E1b. Publica en RUTINA de noche con alerta del sensor | SIN DATO útil (0 de 1) | 23,7 % (9 de 38) | **89,3 %** (100 de 112) |
| E2. Publica donde MIROVA alertó, por pasada | SIN DATO útil (1 de 1) | **66,7 %** (14 de 21) [45,4 a 82,8] | 100 % (154 de 154) [97,6 a 100] |
| E3. Razón nuestra sobre MIROVA, mediana (p25 a p75) | SIN DATO útil (n 1) | **0,45** (0,25 a 0,70), n 14 | 0,82 (0,53 a 1,14), n 154 |
| E3. Factor típico de desvío (exp de la mediana de abs ln) | SIN DATO | 2,58 | 1,49 |
| E3. Fracción de razones entre 0,5 y 2 | SIN DATO | 42,9 % (6 de 14) | 70,1 % (108 de 154) |
| De 100 publicaciones nuestras en pasadas listadas, coinciden con alerta de MIROVA | 1,6 (1 de 61) | 7,7 (14 de 181) | 25,0 (154 de 615) |

La última fila es aritmética sobre las tres primeras (publicaciones en positivos sobre publicaciones en
positivos más negativos limpios más RUTINA de noche con alerta).

### E1 por zona del barrido (negativos limpios)

| zona | MODIS | VIIRS 750 | VIIRS 375 |
|---|---|---|---|
| nadir (cenital bajo 36°) | 17,3 % (34 de 197) | 31,3 % (77 de 246) | 92,5 % (135 de 146) |
| medio (36° a 52°) | 7,0 % (8 de 115) | 19,7 % (28 de 142) | 88,8 % (71 de 80) |
| borde (52° o más) | 10,8 % (18 de 167) | 17,4 % (53 de 304) | 81,6 % (155 de 190) |

En producción (con el Test 1 encendido) la publicación falsa es más alta en el nadir que en el borde en
los tres sensores. Es lo contrario de la estructura que S147 vio al sacar el Test 1 (regla A114): con el
Test 1 encendido la métrica está saturada y esa estructura no se ve.

### E2 por tramo de la magnitud de MIROVA

| tramo de MIROVA | VIIRS 375 hoy | VIIRS 375 antes de #535 | VIIRS 750 hoy | VIIRS 750 antes de #535 | MODIS antes de #535 |
|---|---|---|---|---|---|
| bajo 0,05 MW | 100 % (9 de 9) | 54,8 % (17 de 31) | sin alertas | sin alertas | sin alertas |
| 0,05 a 0,10 | 100 % (40 de 40) | 90,6 % (87 de 96) | sin alertas | 1 de 1 | sin alertas |
| 0,10 a 0,20 | 100 % (44 de 44) | 96,8 % (91 de 94) | 50 % (2 de 4) | 55,6 % (5 de 9) | sin alertas |
| 0,20 a 0,50 | 100 % (44 de 44) | 99,3 % (138 de 139) | 50 % (5 de 10) | 75,8 % (25 de 33) | 12,5 % (1 de 8) |
| 0,50 o más | 100 % (17 de 17) | 96,6 % (57 de 59) | 100 % (7 de 7) | 86,2 % (25 de 29) | 0 % (0 de 5) |
| todas | 100 % (154 de 154) | 93,1 % (390 de 419) | 66,7 % (14 de 21) | 77,8 % (56 de 72) | 7,7 % (1 de 13) |

MIROVA no publica alertas MODIS bajo 0,19 MW ni alertas VIIRS 750 bajo 0,05 MW en estas ventanas: los
tramos bajos sólo existen para VIIRS 375.

### E3 por tramo (VIIRS 375, hoy)

| tramo de MIROVA | n | mediana de la razón | p25 a p75 |
|---|---|---|---|
| bajo 0,05 | 9 | 1,65 | 1,19 a 2,39 |
| 0,05 a 0,10 | 40 | 0,98 | 0,87 a 1,39 |
| 0,10 a 0,20 | 44 | 0,66 | 0,51 a 1,08 |
| 0,20 a 0,50 | 44 | 0,59 | 0,38 a 0,95 |
| 0,50 o más | 17 | 0,77 | 0,58 a 0,91 |

La razón global de 0,82 esconde una pendiente: sobreestimamos lo débil y subestimamos lo que MIROVA pone
entre 0,1 y 0,5 MW. Una meta sobre la mediana global sola no vería esa pendiente.

## 3. Estado de hoy por volcán (2026-09-01 a 2026-09-21)

E1 = publicación en negativos limpios; E2 = publicación en alertas de MIROVA; E3 = mediana de la razón (n).

| volcán | MODIS E1 | V750 E1 | V750 E2 | V375 E1 | V375 E2 | V375 E3 |
|---|---|---|---|---|---|---|
| Láscar | 2,6 % (1/38) | 10,4 % (5/48) | 3 de 5 | 88,0 % (22/25) | 22 de 22 | 0,66 (22) |
| Lastarria | 5,1 % (2/39) | 4,7 % (3/64) | sin alertas | 85,2 % (23/27) | 11 de 11 | 0,94 (11) |
| Isluga | 2,8 % (1/36) | 41,5 % (22/53) | 1 de 2 | 77,8 % (7/9) | 37 de 37 | 0,58 (37) |
| Tupungatito | 9,3 % (4/43) | 19,7 % (13/66) | sin alertas | 93,8 % (15/16) | 26 de 26 | 0,61 (26) |
| Planchón Peteroa | 4,2 % (2/48) | 28,1 % (18/64) | 1 de 1 | 87,5 % (35/40) | 8 de 8 | 1,06 (8) |
| Nevados de Chillán | 2,2 % (1/45) | 11,6 % (8/69) | sin alertas | 92,5 % (49/53) | 4 de 4 | 0,99 (4) |
| Llaima | 0,0 % (0/44) | 21,9 % (16/73) | sin alertas | 79,4 % (50/63) | sin alertas | SIN DATO |
| Villarrica | 18,6 % (8/43) | 20,3 % (13/64) | 1 de 2 | 83,3 % (45/54) | 5 de 5 | 0,84 (5) |
| Copahue | 4,5 % (2/44) | 18,8 % (13/69) | sin alertas | 84,7 % (50/59) | 1 de 1 | 0,77 (1) |
| Puyehue Cordón Caulle | **70,0 % (35/50)** | **61,2 % (30/49)** | 8 de 11 | 96,0 % (24/25) | 32 de 32 | 1,06 (32) |
| Chaitén | 8,2 % (4/49) | 23,3 % (17/73) | sin alertas | 91,1 % (41/45) | 8 de 8 | 1,31 (8) |

Lo que salta: en MODIS, Puyehue Cordón Caulle solo aporta 35 de las 60 publicaciones falsas del sensor;
sin él, MODIS publicaría en 25 de 429 negativos limpios (5,8 %). En VIIRS 375 la publicación falsa es
pareja en los once (77,8 a 96,0 %): no es un problema de un volcán.

## 4. MIROVA contra sí misma

MIROVA no depende de nuestros cambios de régimen, así que doy las dos ventanas como réplica una de la otra.

### 4.1 Repetición entre pasadas de la misma noche y sensor

Para cada pasada con alerta, las OTRAS pasadas de esa noche y sensor que MIROVA listó: fracción que
también alerta.

| | VIIRS 375, jun a ago | VIIRS 375, sep | VIIRS 750, jun a ago | VIIRS 750, sep | MODIS, jun a ago |
|---|---|---|---|---|---|
| tasa base de alerta por pasada | 18,7 % (419/2246) | 21,4 % (154/718) | 3,2 % (72/2263) | 2,8 % (21/755) | 0,7 % (13/1830) |
| repite en otra pasada | **53,4 %** (446/835) | **53,2 %** (198/372) | 14,8 % (20/135) | 18,5 % (10/54) | 18,2 % (2/11) |
| control barajado | 34,7 % | 37,0 % | 8,8 % | 8,6 % | 8,8 % |
| otra pasada en nadir | 84,8 % (201/237) | 78,4 % (87/111) | 64,7 % (11/17) | 60,0 % (6/10) | 2 de 4 |
| otra pasada en medio | 58,8 % (107/182) | 72,8 % (59/81) | 26,5 % (9/34) | 3 de 12 | 0 de 1 |
| otra pasada en borde | **33,2 %** (138/416) | **28,9 %** (52/180) | **0,0 %** (0/83) | 3,1 % (1/32) | 0 de 6 |
| noches con alerta y 2 o más pasadas | 240 | 81 | 62 | 17 | 10 |
| de esas, todas las pasadas alertan | 50 | 13 | 1 | 0 | 1 |

La zona de la otra pasada es la del record nuestro pareado (MIROVA no publica el cenital en la tabla).

Por tramo de la alerta que sirve de ancla (VIIRS 375, jun a ago): bajo 0,05 MW repite 34,9 % (22/63);
0,05 a 0,10, 52,2 %; 0,10 a 0,20, 51,9 %; 0,20 a 0,50, 58,1 %; 0,50 o más, 56,6 %. Las alertas bajo
0,05 MW son las menos reproducibles para la propia MIROVA.

Magnitud entre dos pasadas con alerta de la misma noche: factor mediano **2,0** (p90 5,7; 223 pares) en
jun a ago, y **1,8** (p90 5,1; 99 pares) en septiembre, VIIRS 375.

### 4.2 La misma escena a dos resoluciones (VIIRS 375 y 750 de MIROVA, a menos de 120 s)

| | jun a ago | sep |
|---|---|---|
| si 375 alerta, 750 alerta | 19,3 % (62/321) | 14,6 % (18/123) |
| si 750 alerta, 375 alerta | **95,4 %** (62/65) | **94,7 %** (18/19) |
| si 375 está en 0, 750 alerta | 0,2 % (3/1699) | 0,2 % (1/540) |
| 750 alerta según el tramo de la 375: 0,05 a 0,10 | 1,3 % (1/79) | 0 de 34 |
| 0,10 a 0,20 | 6,5 % (5/77) | 2,9 % (1/35) |
| 0,20 a 0,50 | 28,4 % (29/102) | 25,7 % (9/35) |
| 0,50 o más | 67,5 % (27/40) | 72,7 % (8/11) |
| razón de magnitud 750 sobre 375, mediana (p25 a p75) | 1,06 (0,71 a 1,31), n 62 | 0,92 (0,64 a 1,43), n 18 |
| factor típico de desvío entre las dos | **1,33** | **1,52** |

### 4.3 Entre sensores en la misma noche

Si VIIRS 375 de MIROVA alerta una noche, MODIS de MIROVA alerta esa noche el 4,8 % de las veces
(12/248, jun a ago) y el 0 % (0/81) en septiembre; con la 375 en 0,50 MW o más, 21,7 % (10/46). Bajo
0,20 MW, MODIS nunca (0 de 107). Esto respalda con datos de MIROVA la regla del dueño: MODIS es el
sensor que pierde lo sub-píxel; VIIRS 750 también pierde lo débil (bajo 0,20 MW confirma 1 a 7 %).

## 4 bis. Ya existe una definición de terminado, congelada: el estado de hoy contra ESA tabla

> Agregado tras un aviso del coordinador (dato del frente A). Lo verifiqué leyendo el archivo: no lo heredé.
> **Esta sección manda sobre la 5**: la sección 5 la escribí antes de saber que la tabla existía y queda
> como insumo para revisarla, no como una propuesta desde cero.

**Qué dice y dónde.** `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:75-95`, "Definición
de terminado por sensor (CONGELADA el 2026-09-14, S141, decisión Nicolás)": VIIRS 375 y 750, 0 noches con
alerta perdidas respecto de hoy por estrato; falsas por pasada en negativos limpios de 10 % o menos en
focales y 15 % o menos en nevados; mediana de la razón de magnitud entre 0,8 y 1,25 en cada volcán con
n de 30 o más. MODIS: pasos literales implementados, y en Láscar la tasa en noches con alerta
significativamente mayor que en noches sin alerta; magnitud informativa. Las líneas 88 a 93 dicen que la
consistencia de MIROVA consigo misma **no se corrió** antes de congelar y que es el único motivo de
reapertura. La consume `scripts/auto_audit_weekly.py:148-153` (`FALSAS_BANDA_TERMINADO` y la partición
`REGIMEN`, que importé tal cual).

Fuente de lo que sigue: `contra_tabla_congelada.py` → `tabla_hoy.txt` y `tabla_pre535.txt`.

### Estado contra la tabla

| criterio de la tabla | VIIRS 375 | VIIRS 750 | MODIS |
|---|---|---|---|
| falsas, focales (banda 10 %), hoy | **88,1 %** (111/126) | **28,1 %** (78/278) | 19,4 % (41/211) |
| falsas, nevados (banda 15 %), hoy | **86,2 %** (250/290) | **19,3 %** (80/414) | 7,1 % (19/268) |
| volcanes que cumplen su banda, hoy | 0 de 11 | 2 de 11 (Lastarria, Nevados de Chillán) | 9 de 11 (fallan Villarrica y Puyehue Cordón Caulle) |
| noches con alerta perdidas por el sensor, hoy | 0 de 81 | **3 de 17** | 0 de 1 |
| lo mismo, 2026-06-13 a 2026-08-28 | 10 de 248 | 10 de 63 | **11 de 12** |
| magnitud, volcanes con n de 30 o más, hoy | Isluga 0,58 NO; Puyehue 1,06 SÍ | ninguno llega a n 30 | ninguno |
| lo mismo, jun a ago | Láscar 0,54, Lastarria 0,41, Isluga 0,62 NO; Tupungatito 0,83, Planchón 0,94, Puyehue 0,98 SÍ | ninguno | ninguno |
| MODIS Láscar por noche, con alerta contra sin alerta (jun a ago) | | | 8,3 % (1/12) contra 4,6 % (3/65): no significativo |

La banda de falsas de MODIS no figura en la tabla (su criterio es el contraste en Láscar); la doy porque
`auto_audit_weekly` la mide igual.

### ¿Cumple MIROVA esas bandas contra sí misma? (la condición de reapertura)

- **Magnitud 0,8 a 1,25 por volcán: MIROVA NO la cumple contra sí misma.** Sobre la misma escena, la
  mediana de su VIIRS 750 sobre su VIIRS 375 es 1,10 en Láscar (n 34, dentro), **0,72 en Isluga** (n 11,
  fuera) y **1,31 en Puyehue Cordón Caulle** (n 17, fuera), jun a ago. En el agregado la mediana cae
  dentro (1,04 y 0,88), pero sólo 37,2 % (29 de 78) y 20,0 % (5 de 25) de los pares individuales están
  dentro de la banda. Salvedades: son dos resoluciones distintas, no dos mediciones idénticas, y los n por
  volcán son menores que los 30 que la tabla exige. Con esa salvedad, **la condición de reapertura
  declarada se cumple para la columna de magnitud**: la banda es más estrecha que la coherencia de MIROVA
  por volcán. Lo que sí es alcanzable y está respaldado: mediana agregada por sensor dentro de la banda,
  y sin pendiente por tramo (sección 2, E3 por tramo), que es donde está nuestro defecto real.
- **Falsas 10 y 15 %**: la variabilidad de MIROVA no las refuta ni las respalda, porque un negativo limpio
  vale 0 en MIROVA por construcción. El único cruce independiente que tengo (su 750 alerta cuando su 375
  dice 0) da 0,2 %. El "cerca de 5 % de falsas" que la tabla cita del paper no lo verifiqué: SIN VERIFICAR.
  Lo que sí se puede decir con datos: la banda es **razonable para VIIRS 375** (MIROVA alerta en 19 a
  21 % de las pasadas, así que con 10 a 15 % de falsas más de la mitad de lo publicado coincidiría) y
  **demasiado laxa para VIIRS 750 y MODIS**, cuyos sensores en MIROVA alertan en 3 % y 0,5 % de las
  pasadas: un VIIRS 750 que cumpla el 10 % seguiría publicando tres veces más seguido en negativos que lo
  que MIROVA alerta en total, y a lo más una de cada cinco publicaciones suyas coincidiría.
- **"0 noches perdidas"**: es **demasiado laxa para VIIRS y choca con la definición del dueño de hoy.**
  MIROVA repite su alerta VIIRS 375 en el 53 % de las otras pasadas de la noche, o sea que una noche con
  alerta trae típicamente dos pasadas con alerta; perder una no pierde la noche. Medido: de jun a ago
  VIIRS 375 perdió 29 pasadas con alerta (23 de ellas bajo 0,10 MW) y sólo 10 noches de 248; hoy pierde
  0 y 0. Un brazo que apague las alertas débiles por pasada pasaría el criterio por noche sin que nadie
  lo vea. Como el dueño dijo hoy que en VIIRS no se acepta perder alertas débiles, el criterio tiene que
  medirse **por pasada y por tramo de magnitud de MIROVA**, con la noche como informativo. Para MODIS el
  criterio por noche de la tabla (contraste en Láscar) sí es coherente con su regla, y hoy no se cumple.

### Cómo se reconcilia con las dos definiciones de hoy

1. **Paridad en los dos sentidos** ya está en la tabla (detección y falsas en la misma fila). Lo que falta
   es que las dos columnas usen la misma unidad: hoy una va por noche y la otra por pasada.
2. **VIIRS no pierde alertas débiles**: cambiar "0 noches perdidas" por "0 pasadas con alerta perdidas
   respecto de hoy, por tramo", con la línea base de hoy de la sección 2 (VIIRS 375: 154 de 154). Para
   VIIRS 750 "respecto de hoy" congelaría una pérdida de 22 a 33 % (H2): ahí la referencia debería ser
   MIROVA y no nuestro estado de hoy. El corte de 0,5 MW queda sólo para MODIS.
3. La sección 5 se lee así: sus metas de E2 son la versión por pasada del criterio de detección; sus
   escalas de E1 (tasa base de MIROVA por sensor) son el argumento para revisar la banda de 750 y MODIS;
   su vara de E3 (factor 1,3 a 1,5) es la evidencia de que la banda de magnitud por volcán es más
   estrecha que MIROVA consigo misma.

### Las 111 alertas que S131 cerró como "no fallas"

`docs/s131/agentes/GROUND_TRUTH_ESPACIAL.md:272-287` y la fila H7 de la línea 362 las cierran con "lo que
falta es señal" y "el régimen que el proyecto ya declaró aceptable (FN sub-píxel bajo 0,5 MW)", gravedad
baja. Mi medición de hoy ve la misma clase y contradice el mecanismo:

- **VIIRS 750** (51 de las 111 en S131): desde el 13 de junio son 23, y en las 23 **hay detección en el
  cráter**; se pierden porque la magnitud sale 0 (H2). No falta señal, falta magnitud.
- **VIIRS 375** (60 en S131): de jun a ago son 29. De esas, 17 son `summit` con cúmulo ubicado y magnitud
  0 (13 en Lastarria, 4 en Láscar), y 12 no tienen ningún píxel (`atrib_V375_0613_0828.txt`). Desde el
  1 de septiembre son **0 de 154**: eran recuperables, y se recuperaron. SOSPECHA de que fue #571 (quitar
  el piso de VRP): coincide en fecha, no lo aislé.
- No reconstruí la población exacta de S131 (otra ventana, 1.926 alertas): digo que veo la misma clase,
  no las mismas 111.

## 5. Metas propuestas por sensor (insumo para revisar la tabla congelada, ver 4 bis)

Regla A115: ningún umbral inventado. Cada meta es un número medido arriba, y digo cuál. Donde el dato no
alcanza para fijar un número lo digo y dejo la decisión a Nicolás.

### E2, no perder alertas de MIROVA (por pasada, con el predicado del tablero)

| sensor | meta propuesta | de dónde sale |
|---|---|---|
| VIIRS 375 | **mantener 100 % en todo tramo de 0,05 MW o más**; bajo 0,05 MW se informa aparte | hoy es 100 % (154/154). Regla del dueño: VIIRS captura todo lo que MIROVA publica. Bajo 0,05 MW la propia MIROVA repite la alerta en otra pasada sólo 32 a 35 % de las veces, contra 52 a 70 % en el resto: es el único tramo con respaldo medido para tolerar algo |
| VIIRS 750 | **95 % o más**, en todo tramo de 0,10 MW o más | es la coherencia de MIROVA consigo misma sobre esta señal: cuando su 750 alerta, su 375 alerta 94,7 a 95,4 %. Es alcanzable porque en las 95 alertas de 750 desde junio el píxel ya se detecta en su lugar (72 publicadas más 23 con magnitud 0); hoy 66,7 a 77,8 % |
| MODIS | **SIN META NUMÉRICA todavía** | septiembre tiene 1 alerta MODIS; la población útil es Láscar de marzo a agosto (76). La condición previa a cualquier meta es que el sensor separe: hoy publica 10,5 a 11,7 % en alertas y 11,5 % en negativos. Propuesta de forma, no de número: que la tasa en alertas de 0,50 MW o más supere a la de negativos limpios con intervalos que no se crucen, medido en Láscar |

### E1, callar donde MIROVA calla (negativos limpios, por pasada)

MIROVA vale 0 en un negativo limpio por construcción, así que su variabilidad no da un número para E1. Lo
que sí da es una escala, y propongo usarla:

| sensor | hoy | escala medida | meta propuesta |
|---|---|---|---|
| VIIRS 375 | 86,8 % | tasa base de alerta de MIROVA por pasada: 18,7 a 21,4 % | **no publicar en negativos limpios más seguido de lo que MIROVA alerta en total: 20 % o menos**. Con eso y el recall de hoy, de cada 100 publicaciones coincidirían con MIROVA unas 46 si la RUTINA de noche con alerta sigue como hoy (154 sobre 154 + 83 + 100), y unas 59 si baja en la misma proporción (154 sobre 154 + 83 + 22), contra 25 hoy; es aritmética sobre la tabla de la sección 2, no una medición |
| VIIRS 750 | 22,8 % | tasa base de MIROVA: 2,8 a 3,2 % | **3 % o menos** con el mismo criterio. Hoy publica 7 veces más seguido en negativos que lo que MIROVA alerta en total |
| MODIS | 12,5 % (5,8 % sin Puyehue Cordón Caulle) | tasa base de MIROVA: 0,2 a 0,7 % | mismo criterio daría **1 % o menos**; SIN VERIFICAR que sea alcanzable, porque el detector MODIS deja cúmulo con energía dentro del radio interior en el 87 a 90 % de los negativos |

El criterio "no publicar en negativos más seguido que la tasa base de MIROVA" es una propuesta, no un
resultado: es la única escala por sensor que sale de la base de MIROVA. El número final es decisión de
Nicolás.

**E1b (RUTINA en noche con alerta)** se informa aparte y no entra a la meta de E1. Razón medida: en esas
noches la propia MIROVA alerta en el 53 % de las otras pasadas, y en el 78 a 85 % si la otra pasada es
cercana al nadir; el volcán está caliente y MIROVA calla sobre todo por geometría. Publicar ahí es un
error de paridad por pasada, pero no es una falsa alarma para el operador.

### E3, magnitud pareada

| sensor | hoy | vara medida en MIROVA | meta propuesta |
|---|---|---|---|
| VIIRS 375 | mediana 0,82; factor típico 1,49; 70 % entre 0,5 y 2 | misma escena a dos resoluciones: mediana 0,92 a 1,06; factor típico 1,33 a 1,52 | **mediana entre 0,92 y 1,06 EN CADA TRAMO de 0,05 MW o más** (hoy 0,98 / 0,66 / 0,59 / 0,77) y factor típico de 1,5 o menos (hoy ya cumple). La dispersión ya es la de MIROVA consigo misma; lo que falta es el sesgo, y está en los tramos de 0,10 a 0,50 MW |
| VIIRS 750 | mediana 0,45 a 0,51; factor 2,1 a 2,6 | igual | misma meta. Hoy está lejos en sesgo y en dispersión. SOSPECHA: comparte mecanismo con la pérdida de E2 (fondo del anillo más tibio que la cumbre), no lo medí sobre las publicadas |
| MODIS | n 1 a 2 | sin vara propia (5 pares o menos) | SIN DATO |

Pedir más que un factor 1,3 a 1,5 no tiene respaldo: MIROVA no coincide consigo misma mejor que eso sobre
la misma escena, y entre pasadas de una noche se mueve por un factor 1,8 a 2,0.

## 6. Hallazgos, por gravedad

### H0. El criterio congelado de detección ("0 noches perdidas") no ve la pérdida que el dueño prohibió hoy
- ARCHIVO:LÍNEA: `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md:82-83`;
  SCRIPT:SALIDA: `contra_tabla_congelada.py` → `tabla_pre535.txt` bloque 2.
- QUÉ PASA: una noche activa trae en promedio dos pasadas con alerta de MIROVA (repite 53 %), así que
  apagar una pasada débil no pierde la noche. Medido de jun a ago en VIIRS 375: 29 pasadas perdidas (23
  bajo 0,10 MW) son sólo 10 noches de 248. Un A/B que recorte lo débil pasa el criterio congelado.
  Además la banda de magnitud por volcán es más estrecha que MIROVA consigo misma (Isluga 0,72, Puyehue
  1,31), lo que cumple la condición de reapertura que la propia tabla declara (líneas 88 a 93).
- CÓMO SE VE EN EL DASHBOARD: invisible; es un defecto del criterio con que se aprueban cambios.
- CÓMO REPRODUCIRLO: `python experiments/_s149_audit/frente_c/contra_tabla_congelada.py 2026-06-13 2026-08-28`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 4 (decide qué se adopta en producción). Detalle en la sección 4 bis.

### H1. MODIS en producción publica a la misma tasa con alerta de MIROVA que sin ella
- SCRIPT:SALIDA: `experiments/_s149_audit/frente_c/chequeos.py` → `chequeos.txt` bloque (b);
  `atribuir_perdidas.py MODIS 2026-03-01 2026-09-21` → `atrib_MODIS_0301_0921.txt`.
- QUÉ PASA: Láscar emite 0,2 a 3,8 MW según MIROVA MODIS. Nuestro MODIS detecta 25 a 220 píxeles anómalos
  en esa escena y arma un cúmulo con energía a 0,5 a 3,2 km del cráter en las 76 de 76 alertas, pero 68
  quedan con `distance_class = far` y `discarded_reason = partial_eruption_hotspot_too_far`, y el
  predicado del tablero exige `summit`. Publica 8 de 76 (10,5 %) en alertas y 460 de 4.009 (11,5 %) en
  negativos limpios de los once volcanes (2026-03-01 a 2026-08-28). En Láscar solo: 10,5 % contra 2,0 %
  (4 de 201). Y el cúmulo con energía dentro del radio interior existe en 3.611 de 4.009 negativos
  (90,1 %): quitar la etiqueta no separa nada.
- CÓMO SE VE EN EL DASHBOARD: la serie MODIS de Láscar casi vacía mientras MIROVA muestra alertas MODIS
  de más de 1 MW; y en Puyehue Cordón Caulle MODIS publica en 70 % de las pasadas en que MIROVA dice 0.
- CÓMO REPRODUCIRLO: `python experiments/_s149_audit/frente_c/atribuir_perdidas.py MODIS 2026-03-01 2026-09-21`;
  caso: Láscar 2026-03-07 07:35 UTC, MIROVA 2,70 MW, nuestro cúmulo 2,03 MW a 2,6 km, `far`.
- CONFIANZA: CONFIRMADO (medido). La causa de la etiqueta es el mecanismo ya descrito en A81 y A46; no la
  volví a trazar en el código: SOSPECHA en cuanto a la causa.
- GRAVEDAD: 4 por sensor (el canal MODIS no aporta información a la decisión). Atenuante medido: las 60
  noches de volcán de esas 68 pasadas tienen alguna publicación nuestra por VIIRS 375
  (`noche_cubre.txt`), así que el operador no queda ciego esa noche; pero VIIRS 375 publica 87 % de las
  veces de todos modos, así que esa cobertura no discrimina.

### H2. VIIRS 750 pierde 22 a 33 % de las alertas de MIROVA porque el píxel detectado recibe magnitud 0
- SCRIPT:SALIDA: `atribuir_perdidas.py VIIRS750 2026-06-13 2026-09-21` → `atrib_V750_0613_0921.txt`;
  `chequeos.txt` bloque (a).
- QUÉ PASA: la cumbre es alta y fría; el anillo de fondo baja a terreno más tibio. El píxel de 750 m del
  cráter pasa el test espectral (23 de 23 perdidas son `summit`, cúmulo de 1 o 2 píxeles a 0,05 a 1,33 km),
  pero su temperatura de brillo es menor que `t_bg_k` en 20 de 23 (mediana de la diferencia, 1,8 K bajo el
  fondo; en las 72 publicadas, 2,8 K sobre el fondo y sólo 2 bajo él). La magnitud sale 0,0 MW y
  `isValidDetection` la descarta. MIROVA publica ahí 0,11 a 0,60 MW.
- CÓMO SE VE EN EL DASHBOARD: invisible (la pasada no aparece). MIROVA muestra alerta VIIRS 750.
- CÓMO REPRODUCIRLO: Láscar 2026-09-21 05:42 UTC, `VIIRS_SNPP_750`: `primary_cluster.vrp_mw = 0.0`,
  `centroid_dist_km = 0.049`, píxeles a 262,4 y 260,6 K con `t_bg_k = 264,19`; MIROVA 0,22 MW.
- CONFIANZA: CONFIRMADO el hecho (detecta, magnitud 0, píxel bajo el fondo). SOSPECHA que la causa sea
  únicamente el fondo del anillo: no leí la función que calcula la magnitud.
- GRAVEDAD: 4 por sensor. Noche cubierta por VIIRS 375 en 21 de 21, con la misma salvedad que H1.
- Confirma en producción el hallazgo de hoy del control sin Test 1 (72 a 77 %): producción da 66,7 %
  (sep), 77,8 % (jun a ago), 78,8 % (mayo; 77,6 % con la tabla sola). No lo causa apagar el Test 1: 7 de
  las 23 perdidas tienen `triggered_test1 = True`.

### H3. VIIRS 375 publica en 87 % de los negativos limpios, parejo en los once volcanes y en todo el barrido
- SCRIPT:SALIDA: `hoy_0901_0921.txt`.
- QUÉ PASA: en una pasada donde MIROVA procesó el gránulo y no vio nada, producción publica 361 de 416
  veces; por volcán va de 77,8 a 96,0 %; por zona, 92,5 % nadir y 81,6 % borde. Antes de #535 era 55,7 %
  (782 de 1.405). Conocido desde S139 (A98, A104); lo nuevo es el dato de hoy con un solo instrumento y
  la lectura de precisión: 25 de cada 100 publicaciones coinciden con MIROVA.
- CÓMO SE VE EN EL DASHBOARD: barras VIIRS 375 casi todas las noches en los once volcanes.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 4 (el operador no puede leer un cambio en un canal que casi siempre está encendido).

### H4. La razón de magnitud global esconde una pendiente por tramo
- SCRIPT:SALIDA: `hoy_0901_0921.txt`, bloque "E3 por tramo".
- QUÉ PASA: VIIRS 375 da 1,65 bajo 0,05 MW, 0,98 en 0,05 a 0,10, y 0,59 a 0,66 entre 0,10 y 0,50 MW.
  Una meta sobre la mediana global (0,82) puede cumplirse empeorando un tramo y mejorando otro.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2. Coherente con A99 (faltan vecinos tibios cuando el foco crece),
  que no re-verifiqué.

### H5. La estructura por zona del barrido está invertida entre producción y los brazos sin Test 1
- SCRIPT:SALIDA: tabla E1 por zona de la sección 2.
- QUÉ PASA: en producción el falso es MAYOR en nadir que en borde en los tres sensores, y la propia
  MIROVA alerta 2,5 veces menos en el borde que en el nadir (29 a 33 % contra 78 a 85 %). Paridad en los
  dos sentidos por pasada implica reproducir esa caída de MIROVA en el borde. Es una decisión del dueño,
  no un defecto: ¿se quiere callar en el borde porque MIROVA calla por geometría?
- CONFIANZA: CONFIRMADO el dato. GRAVEDAD: 2 (afecta cómo se define la meta, no una alerta).

### H6. La ventana "desde el 2026-08-29" cruza otro cambio de régimen (#571, 2026-08-31)
- ARCHIVO: `git log -- pipeline/profiles/mirova_equivalent.yaml` (commit `d55bcd5e1`, 2026-08-31 16:34 -0400).
- QUÉ PASA: A104 nombra sólo #535. Una línea base que empiece el 29 de agosto mezcla tres días con piso
  de VRP y el resto sin él. Usé el 1 de septiembre. SIN VERIFICAR cuánto mueve esos tres días.
- GRAVEDAD: 1.

## 7. Lo que cambiaría el plan

1. **La brecha de VIIRS 750 no es de sensibilidad, es de magnitud 0 sobre un píxel ya detectado.** Un plan
   que la ataque bajando umbrales de detección no la toca y sube E1.
2. **MODIS no tiene un problema de "perder sub-píxel": no discrimina.** Las alertas que pierde son de 0,2 a
   3,8 MW. Cualquier A/B en MODIS que mida sólo E1 o sólo E2 va a parecer una mejora moviendo una tasa
   pareja hacia arriba o hacia abajo; hay que exigir separación entre las dos.
3. **Las metas de VIIRS 375 son de un solo lado** (E1 y el sesgo de E3 por tramo); E2 ya está en 100 % y
   la meta es no perderlo.
4. **Todo pre-registro debería fijar E1 y E2 por pasada con el mismo instrumento** (`medir_brechas.py` da
   los tres errores, los controles y el cruce con el banco en una corrida de unos 3 minutos por ventana).

## 8. VERIFICADO LIMPIO

- El predicado con node reproduce los 7 casos del guard: `identidad predicado True` en las tres ventanas
  (primera línea de cada salida).
- Controles `todo_publica` = 100 % y `nada_publica` = 0 % en E1 y E2, tres sensores, tres ventanas.
- Mi unidad (pasada de MIROVA) y la del banco (record nuestro) dan conteos idénticos en positivos,
  negativos limpios y RUTINA de noche con alerta: línea "cruce con el banco" de cada salida.
- Cobertura: 0 alertas de MIROVA sin record nuestro en 2026-05, 2026-06-13 a 2026-08-28 y 2026-09-01 a
  2026-09-21 (con la salvedad de la sección 1).
- A119 respetada: en mayo la columna que decide es "tabla sola" (MODIS 2 de 11 en ambas; VIIRS 750
  77,6 % tabla sola contra 78,8 % con OCR); el aviso del cargador salió por stderr (`mayo.err`).
- La referencia del snapshot está al día: última fila del consolidado 2026-09-21 12:50 UTC.
- MIROVA contra sí misma es estable entre dos ventanas independientes (53,4 y 53,2 %; 95,4 y 94,7 %;
  19,3 y 14,6 %): no es un artefacto de una ventana.

## 9. SIN VERIFICAR

- La causa en el código de la etiqueta `far` de H1 y de la magnitud 0 de H2 (no leí `pipeline/`).
- Que las metas de E1 sean alcanzables sin tocar E2: no hay brazo que lo mida en producción.
- El efecto de los tres días 2026-08-29 a 2026-08-31 (H6).
- La zona del barrido de las pasadas de MIROVA sin record nuestro pareado (usé nuestro cenital).
- La "noche" es la fecha UTC, como en `banco_paridad`; no comprobé si alguna pasada nocturna cae antes
  de las 00 UTC y parte una noche en dos.
- Los resultados de los brazos sin Test 1 y con `max` que cito como "hallazgo de hoy" los leí de
  `experiments/_s149_prereg_invierno/resultados/` y no los recalculé.

## 10. Para otros frentes

- **Frente D**: A94 priorizó la etiqueta `far` en "1 noche de 946" con unidad noche de cualquier sensor
  (`CLAUDE.md`, regla A94). Por sensor y por pasada son 68 de 77 alertas MODIS. La unidad elegida apagó
  el frente; con las metas por sensor que pidió el dueño ese veredicto cambia de tamaño.
- **Frente D**: A82 (rebaja S146) ya decía que en MODIS el cúmulo aparece en 89,1 % de negativos contra
  93,7 % de positivos; mis números (90,1 % y 100 %) lo reproducen en otra ventana.
- **Frente E**: el cálculo de magnitud de VIIRS 750 contra el fondo del anillo (`t_bg_k`,
  `diag_L_bg_local_w_m2_sr_um = None` en los tres records que abrí) frente a lo que dice el paper sobre
  el fondo; `single_pixel_mode: True` en esos cúmulos.
- **Frente G**: Puyehue Cordón Caulle publica MODIS en 70 % y VIIRS 750 en 61 % de los negativos limpios
  de septiembre; es el volcán con `inner_radius_km = 20`.
- **Frente B**: A104 y la ventana recomendada no mencionan #571 (2026-08-31) como corte.
