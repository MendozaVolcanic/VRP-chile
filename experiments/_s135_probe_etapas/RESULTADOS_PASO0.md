# Paso 0 del A/B `keep_peak` — la cara cat-b (S135, 2026-09-07 UTC)

> Números del artefacto del run
> [34091969140](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/34091969140)
> (`out_paso0/*.json`, `report.txt`, `criterio_paso0.json`) y de `tabla_paso0.py` →
> `tabla_paso0.json`. Ninguno transcrito a mano (S91). Pasadas elegidas por
> `seleccionar_pasadas_paso0.py` → `pasadas_paso0.json` ANTES de correr; criterio
> pre-registrado en `analisis.evaluar_paso0` ANTES de correr. Read-only, nada en `pipeline/`.

## Resumen para quien sólo lee esto

**Veredicto pre-registrado: INTERMEDIA.** Ninguna de las 9 pasadas cat-b se pierde con
`keep_peak` OFF teniendo el pico en el cráter; 4 se pierden con el pico en el borde del disco.
Ninguna de las 12 tiene nube sospechada (el disco I04 queda a 3-9 K del fondo global, y el I05
lo acompaña).

**Corrección del verificador limpio (gravedad 5), incorporada**: `off_pierde` era una cota
superior que ignoraba el second pass, y el second pass corre ANTES del filtro de `keep_peak` y
no depende de él (`process_viirs.py:1277` vs `:1775-1786`). El propio artefacto lo muestra: en
Lastarria 08-28 el second pass sin conjunto activo devuelve **el mismo píxel** del pico
(fila 1401, col 5624, 2,235 km); en Tupungatito 08-21 devuelve el cráter (0,197 km). Con el
second pass **como está hoy** (D2 sin condicionar), apagar `keep_peak` pierde de verdad **1 de
las 4**: Isluga 08-19, cuyo pico está 3,8 K bajo el fondo y a cota 2,56 km del hotspot de MIROVA,
o sea no es señal. Lastarria 08-27 es el caso discutible: lo que sobrevive por second pass
(1,995 km) está al **S** del cráter y el pico al **N** (2,274 km, cota 0,08 con MIROVA): objetos
distintos, y el que MIROVA publicó es el del N. **Lectura honesta con D2 como está: TENSIÓN
APARENTE salvo Lastarria 08-27.**

**Pero D2 es un drift de fidelidad** (Coppola 2016a l.329-341: second run sólo con conjunto
activo no vacío y sobre los adyacentes). Si D2 se condiciona, esos rescates desaparecen y las
pérdidas vuelven: Lastarria 08-28 y 08-27 (el campo fumarólico a 2,2-2,3 km N/NW, cota 0,64 y
0,08 con MIROVA — A84) y Tupungatito 08-21 (el cráter, que sólo el second pass entrega). **Por
eso D1 y D2 no se pueden decidir por separado**: apagar `keep_peak` es casi gratis con el second
pass permisivo y cuesta el campo de Lastarria con el second pass fiel.

**El régimen nuevo achica el problema antes de tocar nada.** Las 12 pasadas fueron elegidas
porque el record persistido era `test1_roi` con first pass vacío (11/12). Con el código de hoy
(fondo sin máscara de nube, D14) el first pass queda vacío en **4/12** y sólo **1/12** sigue
siendo `test1_roi`; el fondo mediano baja de 264,6 a 260,1 K. En Tupungatito y Láscar el path
contextual encuentra el cráter solo (rango 1 de la máscara, +4,6 a +18,8 K sobre el fondo) y
`keep_peak` ni se invoca. Y en Tupungatito 08-21 el cráter (0,197 km) lo entrega hoy el **second
pass sin conjunto activo** (3 píxeles nuevos, todos ≤ 3 K): D2 y D1 están acoplados.

**H2 sube de n=2 a n=13**: 13/13 `newly_active` con first pass vacío están bajo la compuerta
de 3 K (07-01: 2; Lastarria 08-28: 7; 08-27: 1; Tupungatito 08-21: 3).

## 1. Las 12 pasadas

`fp` = píxeles del first pass; «persistido» = record en `data/` (régimen viejo); «hoy» = el
probe con el código de HEAD. Distancias al `vent_*`; «/ centro» = desde `mirova_center` de
`volcanoes.yaml`, que coincide con el centro del TIF de MIROVA a ±200 m (`docs/AUDIT_S128.md:188-210`;
no es el GVP de S115: coinciden en PCC por casualidad). Presupuesto de error de la cota: semidiagonal
de la celda de 375 m (0,27 km) + residuo por sensor 0,18-0,31 km (`AUDIT_S128.md:191`) ≈ **0,55 km**,
no los 0,4 que decía una versión anterior. cota = |d_pico/centro − d_MIROVA| = cota inferior de la
separación entre los dos puntos (A93). Columna «OFF pierde» = `off_pierde` pre-registrado (cota
superior: ignora el second pass); la lectura corregida está en §2 y §3.

| pasada | clase | fp persist.→hoy | t_bg persist.→hoy | hoy: fuente, d_final | cráter en máscara (rango BT) | pico km vent / centro (ΔBT vs fondo) | (T1 ∩ dNTI) sin pico | MIROVA MW @ km | cota | OFF pierde |
|---|---|---|---|---|---|---|---|---|---|---|
| Lastarria 08-28 06:36 SNPP | cat-b | 0→0 | 263,5→262,4 | `ctx_cluster` 1,111 (second pass, 7 nuevos) | 0 | 2,235 / 2,188 (+0,43) | 0 | 0,06 @ 1,55 | 0,64 | pre-reg. sí; **real no**: el second pass devuelve el mismo píxel (1401,5624). Mismo campo que MIROVA (0,64 ≈ presupuesto 0,55) |
| Lastarria 08-27 05:12 SNPP | cat-b | 0→0 | 263,8→262,9 | `ctx_cluster` 1,995 (second pass, 1 nuevo) | 0 | 2,274 / 2,317 (+0,14) | 0 | 0,05 @ 2,40 | **0,08** | pre-reg. sí; **discutible**: sobrevive por second pass un píxel al S (1,995 km); el pico (N) es el objeto de MIROVA. A46 viva: `final_hotspot` y `pc.centroid` en lados opuestos |
| Lastarria 08-25 06:12 N20 | cat-b | 1→4 | 262,7→260,1 | `ctx_cluster` 1,22 | 0 | 2,254 / 2,215 (+4,37) | **3** | 0,07 @ 1,55 | 0,66 | no (la intersección conserva 3 px) |
| Tupungatito 08-24 05:36 N21 | cat-b | 0→1 | 262,8→259,5 | `ctx_cluster` 0,016 | 5 (**1**) | no aplicó | — | 0,14 @ 4,89 | — | no (contextual en el cráter) |
| Tupungatito 08-22 05:30 N20 | cat-b | 0→2 | 263,7→259,5 | `ctx_cluster` 0,229 | 3 (**1**) | 0,193 / 5,022 (+4,61) | 1 | 0,12 @ 5,21 | **0,19** | no — y el pico ES el cráter y ES el objeto de MIROVA |
| Tupungatito 08-21 06:30 N21 | cat-b | 0→0 | 262,7→257,9 | `ctx_cluster` **0,197** (second pass, 3 nuevos) | 4 (2) | 2,895 / 7,119 (+0,59) | 0 | 0,04 @ 5,21 | **1,91** | pre-reg. sí; **real no**: el second pass entrega el cráter (0,197). El pico NO es el objeto de MIROVA (ella vio el cráter: cráter→centro 4,86 km vs 5,21 publicado) |
| Isluga 08-25 05:12 N21 | cat-b | 0→2 | 265,3→259,7 | `ctx_cluster` 2,243 | 1 (40) | no aplicó | — | 0,57 @ 2,73 | — | no |
| Isluga 08-21 05:24 SNPP | cat-b | 0→1 | 264,6→264,5 | `ctx_cluster` 0,63 | 0 | no aplicó | — | 0,28 @ 0,54 | — | no |
| Isluga 08-19 06:18 N20 | cat-b | 0→0 | 266,7→266,6 | **`test1_roi` 0,0** (único que reproduce) | 0 | 2,975 / 3,245 (**−3,82**) | 0 | 0,04 @ 0,68 | **2,56** | **sí, la única pérdida limpia** (second pass vacío) — y no es señal: −3,8 K bajo el fondo; MIROVA vio el cráter (cráter→centro 0,37 km vs 0,68 publicado) |
| Láscar 08-21 05:42 N20 | control | 0→1 | 268,6→259,4 | `ctx_cluster` 0,061 | 5 (1) | no aplicó | — | 0,24 @ 1,13 | — | no |
| Láscar 08-21 05:24 SNPP | control | 0→3 | 268,9→259,0 | `ctx_cluster` 0,082 | 2 (1) | 0,137 / 0,863 (+9,4) | 2 | 0,37 @ 1,22 | 0,36 | no — pico en el cráter y en la intersección |
| Láscar 08-20 06:00 N20 | control | 0→1 | 265,0→261,0 | `ctx_cluster` 0,141 | 2 (1) | no aplicó | — | 0,14 @ 1,13 | — | no |

Nube sospechada: 0/12 (disco I04 entre −3,0 y −9,0 K del fondo; I05 mediana dentro de ±3,4 K
del I04 en las 12).

## 2. El criterio pre-registrado, aplicado tal cual

| condición | resultado |
|---|---|
| TENSIÓN REAL: ≥ 2 cat-b sin nube con `off_pierde` **y** pico a < 0,5 km del cráter | **0** cumplen |
| TENSIÓN APARENTE: ninguna cat-b se pierde | **no**: 4 se pierden |
| INTERMEDIA: se pierden pasadas con el pico fuera del cráter | **sí, 4/9** → el A/B decide con la distancia de MIROVA como referencia |

El veredicto formal es INTERMEDIA porque así se pre-registró `off_pierde`. Dos cosas que el
criterio no anticipó: (a) el second pass (D2, permisivo) rescata 3 de las 4 «pérdidas» sin
`keep_peak`; (b) la cota A93 muestra que en Tupungatito e Isluga el pico no era el objeto de
MIROVA (ella vio el cráter: cráter→centro 4,86 y 0,37 km contra 5,21 y 0,68 publicados). El
«0 pérdidas con pico en el cráter» se decide sobre **n=2** (sólo Tupungatito 08-22 y Láscar
08-21 tienen el pico en el cráter): es consistente, no concluyente (A90).

## 3. Qué significa para D1 y D2

1. **`keep_peak` OFF no destruye cráteres** en esta muestra: en los 2 casos con el pico en el
   cráter (n=2) hay path contextual o intersección que lo conserva.
2. **Con el second pass como está (D2 permisivo), apagar `keep_peak` es casi gratis**: 3 de las 4
   «pérdidas» las rescata el second pass (una de ellas con el píxel idéntico), la cuarta no es
   señal. El único caso discutible es Lastarria 08-27 (el rescate está al S, el objeto de MIROVA
   al N).
3. **Con el second pass fiel a Coppola (D2 condicionado), apagar `keep_peak` pierde el campo
   fumarólico de Lastarria** (08-27, 08-28; la tercera la salva la intersección) y el cráter de
   Tupungatito 08-21. Es la señal real fuera del cráter que A84 protege. El A/B tiene que medir
   ese FN **por volcán** (A83), no en agregado.
4. **Por eso D1 y D2 son un solo diseño de 4 brazos** (`keep_peak` OFF/ON × second pass
   condicionado/no), sobre el régimen nuevo, con FN sobre cat-b por volcán y con la cota A93
   (desde `mirova_center`, presupuesto 0,55 km) para decidir si lo que se pierde era el objeto
   de MIROVA. Un A/B de `keep_peak` solo mediría un objeto que D2 va a cambiar.
5. **El régimen nuevo ya movió la mayor parte del problema al path contextual**: 11/12 pasadas
   `test1_roi` persistidas son hoy `ctx_cluster`. Antes de cualquier A/B hay que remedir D19
   sobre records del régimen vigente (desde 2026-08-28 23:00) — hoy n≈40 por volcán — o
   reprocesar junio-agosto con el código actual en un `data_subdir` aislado.

## 4. Límites

- Doce pasadas, todas del régimen viejo (el CSV de MIROVA termina el 2026-08-31 y desde el
  28-ago hay 1 candidato): la comparación «persistido vs hoy» es limpia, pero la muestra del
  régimen nuevo no existe todavía.
- La cota A93 usa `mirova_center` de `volcanoes.yaml` como origen (≡ centro del TIF ±200 m,
  `AUDIT_S128.md:188-210`) con presupuesto ~0,55 km. Un primer intento con el `vent` y otro con
  el punto del catálogo dieron cotas falsas (Tupungatito 2,3-5,0 km); una versión anterior de
  este informe usó ±0,4 km y sobre-afirmó «mismo objeto» en Lastarria 08-28. Un radio no es una
  posición, y el presupuesto de error tampoco se adivina.
- `off_pierde` (pre-registrado) ignora el second pass: la lectura real está en §2-§3. Un
  verificador con contexto limpio lo encontró; el autor no.
- Las dos pasadas con Δt = 18 min (Lastarria 08-27, Isluga 08-19) son justo las más cargadas; el
  CSV de MIROVA no trae plataforma, así que «misma pasada» no está probado ahí.
- `out_paso0/` contiene además los 6 JSON de S134 (el workflow sube la carpeta entera, que ya
  los tenía commiteados): no sumar las dos carpetas (H2 = 13/13 cuenta cada pasada una vez).
- El corte de nube (−10 K) queda a 1 K del disco más frío (Láscar 08-21 05:42, −9,0 K): el
  «0/12» es menos holgado de lo que suena.
- «Sin nube» es el criterio del probe (disco I04 a menos de 10 K del fondo, I05 coherente); no
  es una máscara de nube validada.
- H2 (13/13) sigue midiéndose contra el `t_bg` global.

## Verificación cruzada (A93)

Verificador con contexto limpio: reprodujo las 12 filas y las cotas al decimal; refutó
`off_pierde` como medida de pérdida (gravedad 5), el presupuesto ±0,4 de D15 (es ~0,55), la
equivalencia `mirova_center` = GVP de S115, y el docstring de `tabla_paso0.py` sobre Tupungatito;
aportó el control cráter→centro (4,86 / 0,37 km) que sostiene las dos «coincidencias», la A46 viva
en Lastarria 08-27, el n=2, y el margen del corte de nube. Todo incorporado arriba.

## Archivos

`out_paso0/` (12 JSON + `criterio_paso0.json` + `report.txt`), `pasadas_paso0.json`,
`seleccionar_pasadas_paso0.py`, `tabla_paso0.py` → `tabla_paso0.json`. El yml vuelve a
`_archive/` con este PR.
