# F2 · VERIFICACIÓN independiente (contexto limpio)

Verificador: sesión propia, sin el razonamiento del auditor. Todo re-corrido. Ningún archivo
del repositorio modificado; ningún comando git que cambie estado; **cero TIF nuevos
descargados** (los 271 estaban en el worktree `VRP-Chile-s134-f2`, no en el árbol canónico —
ver Hallazgos propios P0). Scripts míos: `verif_01_esquema.py`, `verif_02_condicionamiento.py`,
`verif_03_separacion.py`, `verif_04_georref.py`.

---

## Resumen

| # | hallazgo | veredicto | gravedad mía |
|---|---|---|---|
| 1 | control del instrumento PASA acotado | **PLAUSIBLE** (acotado más de lo que dice) | 2 |
| 2 | separación mediana 0,21 km re-anclando | **REFUTADO como está enunciado** / mecanismo CONFIRMADO | 4 |
| 3 | el anillo es efecto del denominador | **CONFIRMADO y más fuerte** / lectura incompleta | 3 |
| 4 | Llaima 0 ALERTAS V375; Villarrica 3, Copahue 1, NdC 1 | **CONFIRMADO Llaima / REFUTADOS los otros tres** | 3 |
| 5 | dos relojes en `index.csv` | **CONFIRMADO** al decimal | 2 |
| 6 | `anomaly_pixels` ≠ `n_anomalous_pixels` | **CONFIRMADO el desajuste / REFUTADA la causa** | 2 |

---

## 1. Control del instrumento — PLAUSIBLE (gravedad 2)

Reproduce exacto: 5/5 a <1 km dentro del inner, 0/5 sin restringir; RUTINA 9 % vs ALERTA 82 %
(Láscar), 8 % vs 80 % (PP). Comandos: `python 03_control_instrumento.py`,
`python 07_pareado_y_negativo.py`.

**Caminos por los que podría estar mal, enumerados:**

1. *Mover el poste* (restringir al inner hasta que pase). **Parcialmente sí, parcialmente no.**
   El control ALERTA-vs-RUTINA lo rescata: dentro del **mismo** disco de 5 km, las pasadas con
   alerta concentran el máximo en el cráter y las de rutina no. Eso no se puede fabricar
   eligiendo el espacio de búsqueda. Como enunciado condicional —«dentro del inner, el máximo
   del TIF marca la anomalía»— es legítimo.
2. *Salto de objeto*: «el máximo del TIF» **no es** «el cúmulo que MIROVA declara». Es el paso
   que el informe no controla. Lo medí: como estimador de la `Distancia_km` que MIROVA publica,
   el máximo del TIF tiene error mediano **0,88 km** y le gana al nulo trivial —«el cúmulo está
   en el centro de la grilla»— en apenas **61 %** de 223 pasadas: 0,57 km de error en Láscar,
   pero **11,15 km en PCC** y **5,40 en Tupungatito**. El instrumento ve *la anomalía*; que vea
   *dónde MIROVA la puso* está sostenido sólo en Láscar y PP.
3. *n = 5, y las 5 más recientes*. El control negativo de clase amplía a n=45/23 y n=20/25, así
   que el veredicto no depende de esas 5.
4. *¿S131 refutado?* **No.** Queda **acotado**, y el informe lo dice bien. Mi medición del
   punto 2 (61 % contra el nulo) está del lado de S131.

**Además, el hallazgo 1 es decorativo para el hallazgo 2**: la §3 del informe no usa el TIF, usa
el auto-reporte de MIROVA. Pasar el control no compra nada para la conclusión central.

---

## 2. «Separación mediana 0,21 km» — REFUTADO como está enunciado (gravedad 4)

Reproduce numéricamente exacto (`python 08_reanclar.py`: GLOBAL 1,19 / 1,55 / +0,21).
**El número es correcto; lo que no es correcto es llamarlo «separación».**

El CSV de MIROVA **no tiene columna de latitud ni de longitud** — verificado: las 13 columnas
son `timestamp, Fecha_Satelite_UTC, …, Distancia_km, …`. La posición de MIROVA es un **escalar**:
un radio sin acimut. `08_reanclar` compara |nuestro|@mc contra |MIROVA|@mc, dos **radios desde el
mismo centro**. La diferencia de dos radios no es la distancia entre los dos puntos. Cota real
medida por volcán:

| volcán | n | \|r1−r2\| (lo que se reporta) | cota superior r1+r2 |
|---|---|---|---|
| PuyehueCordonCaulle | 32 | 0,29 | **15,62** |
| Tupungatito | 22 | 0,16 | **10,15** |
| Lastarria | 36 | 0,25 | 4,26 |
| PlanchonPeteroa | 20 | 0,16 | 4,14 |
| Láscar | 45 | 0,52 | 2,41 |

La separación real está **en algún punto entre esas dos columnas, y el dato no la determina**.
La frase «las dos posiciones son indistinguibles a la resolución del propio ground truth» no
está sostenida — y no lo está justamente en PCC y Tupungatito, que son los dos casos donde la
conclusión hace todo su trabajo («los 8 km eran el ancla»).

**Lo que sí sobrevive**, y no es poco: el mecanismo. El 77 % de `07_(a)` es artefacto del ancla,
la retractación es correcta, y donde el TIF sí arbitra medí la **separación 2D verdadera** entre
nuestro centroide y el máximo del TIF: Láscar p50 **0,24 km** (62 % bajo la celda, n=16), PP p50
**0,14 km** (82 %, n=11). En foco fuerte la conclusión es correcta y ahora está medida como
distancia entre puntos. En PCC, Tupungatito y los nevados sigue **sin medir**.
Comando: `python verif_03_separacion.py`.

**Nota A50/A89**: S131 §4 ya había establecido el re-ancla en `mirova_center` sobre **1.815**
pasadas (error 0,48 km vs 1,02 km; ρ 0,487 vs −0,073). La trampa en que el auditor cayó y de la
que salió ya estaba documentada en el repo, en `docs/s131/agentes/GROUND_TRUTH_ESPACIAL.md` §4.

---

## 3. El anillo como efecto del denominador — CONFIRMADO y más fuerte (gravedad 3)

Reproduce exacto, incluida la réplica de S133 a **0,00 km** (`python 06_control_condicionamiento.py`).

**Camino enumerado: ¿n=10 alcanza?** El n=10 son *volcanes*; los n por volcán son los que
importan, y varios son indefendibles (Copahue 1, NdC 1, Villarrica 3). Recomputé **sin exigir
TIF** — `06_` lee `resultados.json`, que exige TIF **y** record a ≤120 s y por eso tira el 61 %
de las ALERTAS, aunque el hallazgo 3 **no necesita el TIF para nada**:

| volcán | todos | con ALERTA (mío, n) | `06_` reportaba (n) |
|---|---|---|---|
| Villarrica | 2,79 | **0,13** (n=11) | 0,19 (n=3) |
| Chaitén | 2,49 | **0,23** (n=17) | 0,18 (n=9) |
| Tupungatito | 2,27 | **0,21** (n=50) | 0,25 (n=22) |
| PlanchonPeteroa | 2,45 | **0,40** (n=43) | 0,36 (n=20) |
| NevadosDeChillan | 2,61 | 0,50 (n=4) | 0,33 (n=1) |
| Copahue | 2,80 | **2,90** (n=3) ← *se invierte* | 1,56 (n=1) |

Desplazamiento mediano **−1,43 km** con 2-3× más datos. **El efecto es real y está mejor
sostenido de lo que el informe lo sostiene.** Único cambio de signo: Copahue, cuyo −1,24 era una
mediana de un solo par. Comando: `python verif_02_condicionamiento.py`.

**Camino enumerado: ¿sesgo de selección?** Sí, y **cambia la lectura, no la conclusión**.
Estratifiqué los records **sin** alerta por nuestra propia magnitud (decil bajo vs decil alto):

| volcán | sin alerta, decil BAJO | sin alerta, decil ALTO | con ALERTA |
|---|---|---|---|
| Láscar | 2,64 | **0,15** | 0,17 |
| PCC | 2,86 | **0,21** | 0,23 |
| Tupungatito | 2,13 | 0,57 | 0,21 |
| Villarrica | 2,77 | **2,79** | 0,13 |
| Copahue | 2,53 | **2,87** | 2,90 |
| Llaima | 2,78 | **2,80** | s/d |

En Láscar, PCC y Tupungatito la intensidad **propia** ya explica el anillo: la ALERTA es un
proxy. Pero en Villarrica, Copahue, Llaima y Chaitén el decil alto sin alerta **sigue a
2,3-2,9 km**, o sea **no tenemos ninguna variable interna que reproduzca el corte**. Es A83 otra
vez: sin MIROVA no podemos separar las dos poblaciones. Por eso la frase «el anillo es un efecto
del denominador, no de la detección» es media verdad operacional: para el operador el anillo
sigue ahí, y **no es marcable con nuestros propios datos**. Sugiero re-redactar como «el anillo
vive en la población que MIROVA no confirma, y no tenemos con qué distinguirla».

---

## 4. Los conteos de ALERTAS — CONFIRMADO Llaima, REFUTADOS los otros tres (gravedad 3)

`python verif_01_esquema.py` §C2. Alias descartado con la técnica T2: `sorted(set(Volcan))` da
**exactamente 11 nombres** en CONS y en OCR; 3.355 filas con grafía única `Llaima`.

ALERTAS **VIIRS375 desde 2026-06-01** según el loader: **Llaima 0** (correcto), pero
**Villarrica 15** (no 3), **NevadosDeChillan 8** (no 1), **Copahue 3** (no 1), Chaitén 18 (no 9),
PP 44 (no 20), Tupungatito 54 (no 22), PCC 88 (no 32), Lastarria 86 (no 36), Isluga 133 (no 51),
Láscar 118 (no 45). Los números del informe son **conteos de pares TIF+record**, no de ALERTAS,
y la §6 los presenta como ALERTAS («Villarrica 3 ALERTAS contra 289 records»). La conclusión de
fondo —Llaima sin ground truth espacial contemporáneo, y el operador sin forma de saberlo—
**queda en pie**; la de Villarrica/Copahue/NdC («n = 0-3») **no**: hay 15, 3 y 8.

---

## 5. Los dos relojes — CONFIRMADO (gravedad 2)

Reproduce al decimal: 18.885 filas, `acquisition_utc` vacío en **3.324 (17,6 %)**, discrepancia
>60 s en **2.210 de 15.561 (14,2 %)**. Cobertura 2026-05-08 … 2026-09-05.
`python verif_01_esquema.py` §C3. Sin caminos de falla abiertos. Nota al margen: el archivo sí se
reactivó después de S131 (que lo daba parado desde 2026-05-20); agosto está flaco —2.267 escenas
contra 5.984 de junio— y **esa** es la fuente real de la atrición del §3.

---

## 6. `anomaly_pixels` — desajuste CONFIRMADO, causa REFUTADA (gravedad 2)

Medido sobre **4.465** records V375 (no las 223): `len < n` **7,6 %**, `== n` 56,8 %,
**`len > n` 35,6 %**. Hay records con `n_anomalous_pixels = 0` y `anomaly_pixels` con un
elemento (Láscar 2026-06-05 04:42). **Un array más largo que su contador no es un recorte.**
El máximo observado es 98 < 100, así que el cap tampoco actúa.

Leído el código: `n_anomalous = len(hot_rows)` (`pipeline/process_viirs.py:1368`) cuenta la
máscara de los tests 2/3, mientras el path Test 1 **sobrescribe** `anomaly_pixels` con
`build_anomaly_pixels(t1_vrp_2d, …)` (`:1889`), que filtra `vrp_2d > 0` — otra máscara, y con el
`max(ΔL, 0)` de por medio. Son **dos campos con semántica distinta**, no un array truncado.
`len(anomaly_pixels) == primary_cluster.n_pixels` en 78,4 %, consistente con eso. El informe
acierta el síntoma y erra la causa; el aviso operativo —«no reconstruyas la geometría del cúmulo
desde `anomaly_pixels`»— **es correcto igual, y por una razón peor**.

---

## Hallazgos propios

- **P0 · Los 271 TIF no están donde el informe dice** (gravedad 2).
  `experiments/_s134_audit/tif/` del árbol canónico está **vacío**; los archivos viven en el
  worktree `VRP-Chile-s134-f2`, y `f2_lib.py` codifica esa ruta absoluta en `WT`/`TIFDIR`. Quien
  reproduzca desde el repo canónico va a **bajar 271 TIF sin enterarse**. Comando:
  `ls experiments/_s134_audit/tif | wc -l` → 0.
- **P1 · La cola de validación arrastra un número retractado** (gravedad 3). F2-6 dice que Isluga
  es «el único volcán donde MIROVA está sistemáticamente más cerca (86 % de 51 pasadas)». Ese
  86 % sale del bloque `07_(a)`, que el propio informe **retracta** por contaminación del ancla.
  Re-anclado (`08_`), Isluga da **18 %**, y el volcán con MIROVA sistemáticamente más cerca es
  **PlanchonPeteroa, 95 %**. La cola manda a Nicolás a mirar el volcán equivocado.
- **P2 · El control de georreferencia mide desde el cráter, no desde el centro del raster**
  (gravedad 1). El `semiancho = 36,08 km` de `03_` es `nanmax(dist al vent)`, o sea la distancia
  del vent a la esquina más lejana; compararlo con 25,5·√2 = 36,06 sólo cuadra porque el vent
  está cerca del centro. Medido sobre el propio raster: **51,11 × 51,29 km**, semiancho
  **25,55 km**, semidiagonal 36,21 — que **sí** confirma `half_km = 25,5` y coincide con S131
  (25,29-25,65). La conclusión es correcta; la magnitud que la respalda es otra. Y las cifras
  «celda 0,375 × 0,374 km, extensión 50,3 × 50,1 km» del informe **no reproducen** (medí
  51,11 × 51,29). Comando: `python verif_04_georref.py`.

---

## VERIFICADO LIMPIO

| qué | cómo | resultado |
|---|---|---|
| Los 4 scripts principales (`03_`, `06_`, `07_`, `08_`) | re-corridos completos | reproducen **cifra por cifra**, sin excepción |
| Réplica de la tabla de S133 | `06_` | error mediano 0,00 km sobre 11 volcanes |
| Alias del CSV (técnica T2) | `sorted(set(Volcan))` en CONS y OCR | 11 nombres exactos, ningún alias oculto |
| Estadística de los dos relojes | recomputada de cero desde `index.csv` | 17,6 % y 14,2 % exactos |
| `pipeline/mirova_csv_loader.py` worktree vs canónico | `diff -q` | idénticos — el loader no está parcheado |
| Que ningún script escribiera en el repo | `git status --short` antes y después | sólo `experiments/_s134_audit/` sin seguimiento |
| Que no se bajara ningún TIF | conteo antes/después de correr `07_` | 271 → 271 |
| `half_km = 25,5` | medido sobre el raster (P2) | confirmado, 25,55 km |
| Nocturnidad, `radius_km`/`inner_radius_km`, emparejamiento a 0-1 s | aceptados del informe tras reproducir `02_`/`03_` | sin objeción |

**Lo que NO verifiqué**: la separación 2D real en PCC, Tupungatito y los nevados (no es medible
con este dato); MODIS y VIIRS750; magnitud; el impacto del hallazgo 6 sobre el frontend.
