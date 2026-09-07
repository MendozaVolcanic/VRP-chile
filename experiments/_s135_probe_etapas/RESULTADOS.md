# Probe A75 por etapa — resultados (S135, 2026-09-07 UTC)

> Números del artefacto `s135-probe-etapas` del run
> [34071793829](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/34071793829)
> (`out/*.json`, `out/report.txt`, `out/criterio.json`), leídos con `leer_artefacto.py`.
> Ninguno transcrito a mano (regla S91). Diseño y criterio pre-registrado:
> `experiments/_s134_audit/f3/probe_etapas_ci.md`. Ejecuta la decisión **D1(b)** de
> `docs/AUDIT_S134.md` §D. Read-only: nada en `pipeline/`, ningún flag.

## Resumen para quien sólo lee esto

**H1 queda REFUTADA por el criterio estricto, en la rama que el diseño previó**: en la
pasada insignia de D19 (Villarrica 2026-07-01) **el cráter no está en el footprint del
Test 1** antes del recorte. `keep_peak` no descarta el cráter: elige el píxel menos malo de
un footprint que nunca lo contuvo. El problema es anterior: el Test 1 dispara sobre un disco
frío sin señal alguna en el cráter — gradiente topográfico (A69) **o tope de nube**: el disco
está 27 K bajo el fondo global y un lapso ambiental sobre ~1.300 m de desnivel explica ~8-9 K,
no 27; el probe no capturó I05 y no puede distinguirlos (verificador limpio, gravedad 4). En las tres noches de
Villarrica el píxel del cráter, cuando está en la máscara, ocupa el rango 24 de 36 o 33 de
49 por temperatura, y siempre está **por debajo del fondo global**.

**Hallazgo no previsto, y el más importante**: 2 de las 3 pasadas de Villarrica **no
reproducen** el record persistido con el código de hoy sobre el mismo granule estándar.
La causa está identificada con archivo:línea y fecha: hasta el 28 de agosto a las 23:00 UTC
`process_viirs.py` tenía escrito a mano `CLOUD_BT_THRESHOLD = 260 K` y el fondo global
5-25 km de VIIRS excluía los píxeles más fríos; desde #535 lee `cloud_mask_bt_k: 0.0`
(D14, cerrada y correcta). En noches de invierno sobre nevados eso baja el fondo global
3-10 K y cambia qué path dispara. **Los conteos de D19 (245/289 `test1_roi` desde
2026-06-01) mezclan los dos regímenes**: 396 records del viejo contra 40 del nuevo en
Villarrica. El mecanismo D19 sigue vivo en el régimen nuevo (la pasada del 31-ago
reproduce exacta), pero su tamaño hay que volver a medirlo sobre el régimen vigente.

**H2 CONFIRMADA pero con n=2**: los únicos `newly_active` del second pass con first pass
vacío (07-01) están 2/2 bajo la compuerta de 3 K. Y en el régimen nuevo esa recaptura
**fija la posición publicada** (07-01: `ctx_cluster` a 3,789 km, summit por ser < 5 km):
D2 gana peso, no lo pierde.

**Control Láscar 3/3**: el cráter es el píxel más caliente de la máscara en las tres
noches (rango 1; +9,4 a +26,5 K sobre el fondo global), el path contextual gana y
`keep_peak` ni se invoca. El control no ejercita `keep_peak`; el criterio lo preveía («si
aplica»).

## 1. Las seis pasadas, una por una

Distancias al `vent_*` de `volcanoes.yaml` (= ancla de detección en los dos volcanes;
verificado en el run). «vs fondo» = BT del píxel menos `t_bg_k` global del record del probe.

| pasada | régimen | record hoy | Test 1: n máscara / disco | cráter <0,5 km en máscara (rango BT) | px más cercano al vent | `keep_peak` | (T1 ∩ dNTI) sin pico | second pass |
|---|---|---|---|---|---|---|---|---|
| Villarrica 07-01 05:00 N20 | viejo (persistido `test1_roi` 0,0 km, t_bg 270,1) | **`ctx_cluster` 3,789 km**, t_bg **266,81**, fp 0 | 49 / 112 | **0** | 0,177 km · 239,49 K (**−27,3 K**) · fuera | 2,678 km W · 263,86 K (**−2,95 K**) · argmax del disco | 0 px (dNTI 0) → sale 1 px | active 0 → **2 nuevos, 2/2 ≤ 3 K** |
| Villarrica 08-14 04:42 N20 | viejo (persistido `test1_roi` 0,0 km, t_bg 262,78) | **`ctx_cluster` 2,076 km**, t_bg **252,42**, fp **5** | 36 / 74 | 2 (rango 24) · 249,66 y 250,68 K (−2,8 / −1,7 K) | 0,188 km · en máscara | no aplicó | — | active 5 → 2 nuevos, 2/2 ≤ 3 K |
| Villarrica 08-31 05:06 N21 | nuevo (persistido `test1_roi` 0,0 km, t_bg 262,29) | **reproduce exacto**: `test1_roi` 0,0 km, t_bg 262,29, pc 2 px | 49 / 97 | 1 (rango 33) · 261,02 K (−1,3 K) | 0,041 km · 260,34 K (−1,95 K) · **fuera** | 2,966 km E · 268,54 K (**+6,25 K**) · argmax del disco | **2 px (dNTI 5)** → sale 2 px | active 0 → 0 nuevos |
| Láscar 06-17 05:42 SNPP | viejo | `ctx_cluster` 0,094 km, pc 3 px 0,501 MW, fp 2 | 96 / 192 | 6 (**rango 1**) · 288,85 K (+26,5 K) | 0,097 km · en máscara | no aplicó | — | active 2 → 2 nuevos, 0/2 ≤ 3 K |
| Láscar 07-09 05:48 N20 | viejo | `ctx_cluster` 0,061 km, pc 3 px 0,265 MW, fp 3 | 93 / 187 | 5 (**rango 1**) · 279,81 K (+17,5 K) | 0,131 km · en máscara | no aplicó | — | active 3 → 1 nuevo, 1/1 ≤ 3 K |
| Láscar 07-10 05:30 N20 | viejo | `ctx_cluster` 0,144 km, pc 3 px 0,139 MW, fp 2 | 83 / 171 | 4 (**rango 1**) · 273,49 K (+10,6 K) | 0,191 km · en máscara | no aplicó | — | active 2 → 1 nuevo, 1/1 ≤ 3 K |

`fp` = `diag_n_first_pass_pixels`. En las tres de Láscar el record del probe coincide con
el persistido en fuente y distancia (`ctx_cluster`, 0,06-0,14 km).

### Perfil BT mediana contra distancia al cráter (anillos de 0,25 km, dentro del disco de 3 km)

Distingue «borde del disco = cota baja en todas direcciones» de «valle de un lado» (A70).
Δ = mediana del último anillo con datos menos la del primero, por octante.

| pasada | perfil (km → K) | Δ borde−centro por octante (K) | lectura |
|---|---|---|---|
| Villarrica 07-01 | 239,5 · 238,0 · 239,8 · 238,9 · 239,9 · 240,2 · 245,1 · 242,5 · 245,8 · 243,8 · 249,5 · 247,0 | N +10,4 · NE +12,1 · E +6,3 · SE +8,2 · S +5,6 · SW +6,5 · W +10,0 · NW +3,8 | **gradiente radial en los 8 octantes**: es el cono entero, no un valle. Pero 239 K en la cumbre son 27 K bajo el fondo global, más de lo que da la cota: **nube sobre la cumbre no descartada** (sin I05 en el probe) |
| Villarrica 08-14 | 250,2 · — · 247,8 · 243,7 · 245,5 · 248,2 · 248,2 · 246,4 · 246,9 · 251,8 · 249,0 · 250,1 | N −3,7 · NE −4,1 · E −1,1 · SE +0,4 · S +12,6 · SW +12,7 · W −1,8 | asimétrico: sube sólo al S/SW (12,6-12,7 K). Un lado, no el cono entero |
| Villarrica 08-31 | 260,3 · 261,0 · 260,3 · 261,4 · 260,5 · 260,1 · 260,4 · 256,9 · 260,4 · 261,8 · 260,4 · 260,5 | N −1,5 · NE +3,0 · **E +6,3** · SE +1,0 · S −0,6 · SW −2,1 · W −2,6 · NW +1,7 | **plano** (~260 K en todo el disco). El pico es un píxel discreto a 2,97 km E, +8 K sobre su entorno, contextualmente anómalo (dNTI): no es el gradiente |
| Láscar 06-17 | 288,8 · 266,5 · 260,3 · 258,9 · 260,4 · 259,2 · 259,1 · 258,9 · 258,8 · 259,3 · 259,8 · 260,2 | N −7,0 · NE −2,7 · E −3,1 · SE −31,1 · S −2,1 · SW +3,6 · W −6,0 · NW −4,2 | cráter caliente y aislado; el disco es plano a 259-260 K |
| Láscar 07-09 | 279,8 · 264,2 · 260,1 · 258,4 · … · 261,0 | N −2,8 · NE −13,2 · E −3,6 · SE −18,8 · S +4,9 · SW +6,5 · W −2,3 · NW −3,3 | ídem |
| Láscar 07-10 | 272,2 · 265,4 · 259,0 · 259,4 · … · 260,7 | N −6,2 · NE −6,1 · E −14,9 · SE +2,4 · S +4,3 · SW +4,7 · W −9,0 · NW +1,5 | ídem |

**Tres noches de Villarrica, tres fenómenos distintos.** D19 describía uno solo («el borde
del disco, 3 K bajo el fondo»). Ese es el 07-01. El 08-14 es un flanco S tibio (y hoy dispara
el first pass, no el Test 1). El 08-31 es un objeto discreto a 3 km E del cráter que sobrevive
al filtro contextual por mérito propio: **`keep_peak` es inerte esa noche** (la intersección ya
tenía sus 2 píxeles; agregar el pico no cambió nada). Qué es ese objeto a 3 km E (roca
expuesta, infraestructura, otra cosa) es pregunta para Nicolás: el probe no lo puede decir.

## 2. El criterio pre-registrado, aplicado tal cual

| enunciado | condición | resultado |
|---|---|---|
| H1 confirmada | las 3 de Villarrica con ≥1 px de máscara a <0,5 km **y** pico a >2 km; las 3 de Láscar con pico <0,5 km si aplica | nevado **1/3** (sólo 08-31); control 3/3 («no aplica» en las tres) |
| H1 refutada | en Villarrica el cráter no está en `mask_contributing` | **SÍ, 07-01** (0 px a <0,5 km; el más cercano, a 0,177 km, está 27 K bajo el fondo) |
| H2 confirmada | ≥90 % de `newly_active` con first pass vacío tienen bt − t_bg ≤ 3 K | **2/2 = 100 %**, una sola pasada (07-01). n insuficiente para un umbral del 90 %: se reporta, no se cierra |

Veredicto formal: **H1 REFUTADA · H2 CONFIRMADA con n=2**. El `criterio.json` del artefacto
lo dice con las mismas palabras. El criterio es asimétrico por diseño (refuta con una pasada,
confirma sólo con 3/3): la refutación descansa en **1 de 6 pasadas**, la del 07-01, que además
puede ser una noche nublada. Se reporta así porque así se pre-registró (A91); lo que se sigue de
ella está en §4, no es un veredicto sobre `keep_peak` en general.

Qué significa la refutación, en el sentido exacto del diseño: *«el Test 1 ni siquiera ve el
cráter y el problema está antes, en el ROI/fondo del Test 1»*. Apagar `keep_peak` no
recupera un cráter que no está en la máscara. Lo que apagarlo hace en estas noches:

| noche | `keep_peak` ON (hoy) | `keep_peak` OFF (Test 1 ∩ dNTI, sin pico) |
|---|---|---|
| 07-01 | pc = 1 px del borde W (0,13 MW); posición final del second pass a 3,789 km | **0 px del Test 1**: no se publica el nivel base falso. Quedan los 2 px del second pass sin activos (H2/D2) |
| 08-14 | `keep_peak` no corre (first pass 5 px) | igual |
| 08-31 | 2 px a 2,58/2,97 km E (dNTI) | **igual**: los 2 px ya estaban en la intersección |

## 3. El hallazgo no previsto: dos regímenes de fondo en la ventana de D19

`docs/MIROVA_DIVERGENCES.md` D14 y `docs/S126_CLOUDMASK_YA_ESTA_VIVA.md` documentan el
cambio y su razón (MIROVA NRT no filtra nubes; el destino es correcto). Lo que S134 no
tuvo en cuenta es que su ventana (records desde 2026-06-01) lo cruza. Medido con
`regimen_fondo.py` → `regimen_fondo.json` sobre `data/mirova_equivalent/*.json`, VIIRS 375 m,
corte en el merge de **#535** (2026-08-28 23:00 UTC, cuando cambió el código; #537 del 29-ago fue
sólo documentación). No hay records entre las 23:00 y las 00:00 de esa noche, así que el corte a
medianoche da lo mismo:

| volcán | régimen | n | t_bg mediana | first pass > 0 | first pass = 0 con recaptura | fuentes (`test1_roi` / `ctx_cluster` / ninguna / `test1`) |
|---|---|---|---|---|---|---|
| Villarrica | viejo 06-01→08-28 23:00 | 396 | 268,5 K | 19 (4,8 %) | 22/377 | 229 / 32 / 135 |
| | nuevo 08-28 23:00→09-06 | 40 | **262,3 K** | 7 (17,5 %) | 7/33 | 22 / 12 / 6 / 0 |
| Llaima | viejo | 394 | 268,6 K | 16 (4,1 %) | 33/378 | 206 / 40 / 141 / 7 |
| | nuevo | 40 | **260,9 K** | 12 (30 %) | 5/28 | 21 / 15 / 4 / 0 |
| Láscar | viejo | 325 | 264,3 K | 136 (42 %) | 18/189 | 132 / 133 / 60 / 0 |
| | nuevo | 35 | 263,4 K | 21 (60 %) | 8/14 | 6 / 26 / 3 / 0 |

Lectura: en los nevados el fondo global baja 6-8 K (entra la nieve fría al anillo 5-25 km)
y el first pass dispara 4-7 veces más seguido; en Láscar (desierto seco, casi nada bajo
260 K) no se mueve. La proporción `test1_roi` de Villarrica es parecida en los dos
regímenes (58 % contra 55 %), pero **una misma pasada puede cambiar de path** (08-14). El
grupo nuevo tiene 40 records: las proporciones son indicativas, no robustas (A90).

Consecuencia para D19: los 245/289 de S134 son un conteo del régimen viejo. El mecanismo
existe en el nuevo (08-31 reproduce; 07-01 sigue eligiendo el borde), pero **el tamaño del
anillo de S133/S134 en producción hoy es un número que no está medido**.

## 4. Qué cambia para D1(c) — diseño del A/B, todavía no se corre

Lo que el probe cambia del A/B recomendado en AUDIT_S134 §D:

1. **La pregunta ya no es «¿`keep_peak` descarta el cráter?»** (no: el cráter no está en la
   máscara, o está en el rango 24-33 y bajo el fondo). Es **«¿apagar `keep_peak` elimina el
   nivel base falso sin perder las noches en que el pico sí es el cráter?»** — y esas noches
   están en **Lastarria (60 %), Tupungatito (34 %), Isluga (30 %)** de corroboración MIROVA
   (S134 F3), no en Villarrica. El probe no las miró: eran 6 pasadas, 3 y 3, por diseño.
2. **Paso 0 antes del A/B**: correr este mismo probe sobre 3 pasadas `test1_roi` con alerta
   MIROVA de Lastarria y 3 de Tupungatito (la cara cat-b de la tensión A83/A84). Si en esas
   noches el pico está a <0,5 km del cráter y es el rango 1 de la máscara, `keep_peak` OFF
   las pierde y el A/B tiene que medir ese FN; si el pico también es el borde, la tensión
   era aparente. Costo: el yml ya existe, 5 minutos de CI, sin tocar `pipeline/`. Dos exigencias que este
   probe no cumplió: **noches despejadas** (capturar también I05 y exigir que la mediana del
   disco no esté a más de ~10 K del fondo global, para no repetir el 07-01), y un **control que
   ejercite `keep_peak`**: en las 3 de Láscar el first pass disparó y `keep_peak` ni corrió
   (`final_hotspot_source` tiene que ser `test1` para que corra), así que el control fue
   vacuo por construcción; hay que elegir pasadas focales con first pass vacío.
3. **El A/B tiene que correr sobre el régimen nuevo** (desde 2026-08-29) o re-procesar la
   ventana entera con el código de hoy; comparar brazos contra los records persistidos de
   junio-agosto mezclaría dos fondos distintos.
4. **D2 sube de prioridad**: en el régimen nuevo, con `keep_peak` OFF, lo que queda en una
   noche 07-01 son los 2 píxeles del second pass sin conjunto activo, y ya hoy son los que
   fijan la posición publicada (3,789 km). Un A/B de `keep_peak` sin condicionar el second
   pass mediría un objeto que D2 va a cambiar.
5. Criterio pre-registrado sugerido (A91, unidades del objeto): brazo OFF vs ON sobre los
   11 Tier A, estratificado nevado/focal; **FN** = pasadas con alerta MIROVA V375 (CONS∪OCR,
   ±90 min) que ON publica summit y OFF no; **nivel base falso** = records summit con
   `pc.n_pixels == 1`, `bt_k < t_bg_k` y sin alerta MIROVA. Adoptar sólo si FN cat-b = 0 en
   Lastarria/Tupungatito/Isluga **y** el nivel base falso cae ≥ 80 % en los nevados.

## 5. Límites de lo medido

- Seis pasadas, elegidas en S134 por ser las insignia de cada clase: no son muestra.
- «vs fondo» usa `t_bg_k` global del record del probe (régimen nuevo); el Test 1 mide
  contra el anillo local 1-3 km (Villarrica: 244,8 / 248,2 / 260,4 K en las tres noches).
- H2 con n=2, y medida contra el `t_bg` global, no contra el fondo que el second pass usa
  internamente (el diseño decía «bt − t_bg» sin especificar cuál). La compuerta faltante está
  probada por lectura de código (S134 verificador);
  el probe sólo agrega que, en la única noche con first pass vacío que recapturó, los dos
  píxeles estaban bajo los 3 K.
- El probe corre `calculate_vrp` sin `store.append_record`: el `vrp_mw` del dashboard (que
  pone `store`) no está en el JSON del probe; sí está `primary_cluster.vrp_mw`.
- El objeto a 2,97 km E de Villarrica (08-31) queda sin identificar.
- El probe no capturó I05: no distingue nieve fría de tope de nube en el disco del 07-01.
- Verificación cruzada con contexto limpio (A93): reprodujo 6/6 pasadas de §1, §2 y §3 al
  número; refutó la leyenda del corte de §3 y una fila incompleta de Llaima; aportó la nube del
  07-01 (gravedad 4), la falta de script de §3 (3, corregida con `regimen_fondo.py`), el fondo de
  H2 (2) y el control vacuo (1). Todo incorporado arriba.

## Archivos

`out/*.json` (6 pasadas + `criterio.json` + `report.txt`), `analisis.py` (puro, con tests),
`probe_etapas.py` (runner), `leer_artefacto.py` (re-evalúa el criterio desde `out/`),
`regimen_fondo.py` → `regimen_fondo.json` (§3). El yml
vuelve a `.github/workflows/_archive/probe-s135-etapas.yml` con este PR (regla S80).
