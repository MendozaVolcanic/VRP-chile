# S161: qué se sabe y qué falta en la alerta #864

> Escrito el 2026-10-23, sesión lateral de sólo lectura. No toqué `pipeline/`, `data/`, perfiles ni ramas. No hice
> commit, push ni comentarios. Leí el cuerpo y los comentarios de #864, #886 y #887, los informes de esas ramas con
> `git show origin/<rama>:<ruta>`, y volví a correr el auto-audit sobre una copia de `origin/main` de hoy
> (`3bbd18d2c`). Cada afirmación dice de dónde sale; SOSPECHA donde no lo medí.

Insumos de esta sesión, fuera del repo:
- copia de `main` de hoy: `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\987e79d7-bb76-47e0-b758-01c9a2321725\scratchpad\main_hoy\`
- salida del auto-audit de hoy: `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\987e79d7-bb76-47e0-b758-01c9a2321725\scratchpad\audit_hoy.log`
- muestreo de records: `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\987e79d7-bb76-47e0-b758-01c9a2321725\scratchpad\muestra.py`

## 0. Tres correcciones al encargo, antes de lo demás

1. **Chillán MODIS sí tiene frente, y está en `main`.** S159 lo midió con probe L1B y verificador limpio:
   `experiments/_s159/chillan_modis/INFORME.md` y `verificador/INFORME.md` (commit `9cab55005`, ancestro de
   `origin/main`, comprobado con `git merge-base --is-ancestor`). El traspaso `tasks/BLOQUE_ARRANQUE_S161.md` l. 133 ya
   lo apunta. Lo que no tiene es una decisión pedida ni un A/B: ver §3.
2. **El A/B de D25 sí toca parte de los otros dos puntos.** Su pre-registro (`experiments/_s157_prereg_d25/PREREGISTRO.md`
   en `main`, l. 154 y 196 a 212) mide VIIRS 375 sin kernel (Tupungatito no tiene `local_kernel_bg` en `volcanoes.yaml`,
   leído hoy) y VIIRS 750 en los 11 Tier A, incluida la recuperación de cúmulos del cráter en 0,0 MW. Lo que D25 no
   resuelve en esos dos puntos se dice abajo.
3. **El auto-audit ya no da los números de #864.** `data/audit_continuous/latest.json` en `main` es del 2026-10-19 y
   tenía la frontera de K en 2026-09-18. Corrido hoy, la frontera es 2025-02-15 (histórico en K) y la ventana
   2026-08-24 a 2026-10-23 es entera K, así que los `n` cambian:

| punto de #864 | 2026-10-19 (#864) | hoy, 2026-10-23 (`audit_hoy.log`) |
|---|---|---|
| recall VIIRS 750 | 73,3 % (n = 30) | **72,9 % (n = 48)**, sigue fuera (banda 79,5) |
| Tupungatito VIIRS 375 | 0,266x (n = 8) | **0,448x (n = 19)**; bajo 30° 0,544 (15), 30 a 50° 0,326 (4) |
| Chillán MODIS | 0,485x (n = 7) | **0,485x (n = 7)**; bajo 30° 0,707 (4), 30 a 50° 0,171 (2), 50 a 60° 0,203 (1) |
| Chillán VIIRS 375 / 750 | 0,65 / 0,687 | iguales (0,65, n 16; 0,687, n 13) |
| **nuevo**: PCC VIIRS 750 | no aparecía | **0,517x (n = 10)**, flag nuevo |
| 5 protegidas sin publicar | las 5 | las mismas 5 |

El próximo auto-audit semanal (lunes) abrirá un issue con esta lista, no con la de #864 (SOSPECHA: deducido de que
corre el mismo script sobre la misma data; no lo comprobé contra el cron).

## 1. Tupungatito VIIRS 375 (#886, rama `s158-tupungatito`, borrador, sin tocar desde 2026-10-21 12:38 UTC)

**Qué concluye** (`experiments/_s158_tupungatito/README.md`):
- Las dos protegidas de #864 (2026-09-28 05:18, 2,51 MW; 2026-09-29 04:54, 1,86 MW) no son del cráter: la serie de
  MIROVA las dibuja a 22,6 y 9,6 km, fuera de su círculo de 7 km; la distancia de ~5 km de la fila sólo OCR es de otra
  pasada. Nuestro record de la misma pasada ve el mismo objeto lejano y lo marca `far`. No hay ninguna protegida
  nocturna de cráter perdida en toda la serie K.
- El déficit de magnitud es real (0,49 por noche, n 101; 0,36 por pasada, n 141, con referencia de la tabla) y es
  sobre todo el **fondo**: el anillo de 5 a 25 km es valle tibio y el foco está ~5 K sobre él; en 6 pasadas el píxel
  queda bajo el anillo y publicamos 0,0 MW. C0 restaba el anillo de 1 a 3 km (13 K más frío) por su Test 1, y por eso
  daba más. El ángulo agrega una parte compatible con D17, dependiente del modelo de área. La selección pesa poco.

**Verificado por verificador limpio** (`verificador/INFORME_VERIFICADOR.md`): CONFIRMADAS la lejanía de las protegidas
(por una vía independiente, la dirección en la miniatura), el 0,266 reproducido con la función del auto-audit y los
números del lado del barrido. PARCIALES: el fondo como pieza principal (la prueba de coherencia 1.130 de 1.130 era casi
vacía, 1.126 records de un píxel; el mecanismo queda respaldado por código, SOSPECHA para records de otras fechas) y la
comparación con C0 (mezclaba noches; en las mismas 14 noches C0 0,825 contra K 0,553). Sin verificar: el reparto
fondo/área en el borde, las 10 pasadas del este de un píxel, el origen del 5,68 km del OCR (§6 del README).

**¿Siguen valiendo con los datos de hoy?** Sí en lo que muestreé:
- Records de hoy de las dos protegidas (`muestra.py` sobre la copia de `main`): 2026-09-28 05:18 `far`, cúmulo a
  21,574 km, 0,15 MW, 2 píxeles; 2026-09-29 04:54 `far`, 9,403 km, 1,112 MW, 1 píxel. Iguales a la tabla del §2 del
  README (21,57 y 9,40 km).
- Filas de la referencia en el snapshot de `main`: siguen con `Distancia_km` 5,27 y 5,68, `ALERTA_TERMICA_OCR`, y
  `Distancia_aprox` «ambiguo» (5,27 a 22,57 y 5,41 a 9,59), como dice el README.
- El auto-audit de hoy las sigue contando como protegidas sin publicar, y su único filtro de distancia
  (`scripts/auto_audit_weekly.py:526`) es sobre **nuestro** cúmulo, no sobre la distancia de la alerta. La sugerencia 2
  del §8 de #886 no está implementada.
- El 0,448 de hoy (n 19) coincide en valor con el «sin las 2 lejanas» de #886 (0,448, n 7), pero es otra ventana y por
  la regla del código incluye las dos lejanas en el denominador (SOSPECHA: deducido de l. 526 y del §3 de #886; no
  recalculé la mediana sin ellas).

**Qué falta para cerrar el punto de #864:**
- **Protegidas (decisión de Nicolás, barata):** que el auto-audit mire la distancia de la alerta de MIROVA antes de
  contarla como protegida o meterla al denominador de magnitud (pareo con la tabla, o `Distancia_aprox_*` cuando dé
  «único»). Es cambiar un criterio de la vara, no el detector. Con eso las dos protegidas de Tupungatito salen de la
  lista con evidencia ya verificada.
- **Magnitud:** lo decide la lectura del A/B de D25 (pre-registro, predicciones 1 y 2). #886 dejó una predicción
  falsable más fina (cenit bajo 30°: de 0,45 hacia 1 si los vecinos quedan ~7 K bajo el anillo; las 6 pasadas en 0,0
  MW dejan de serlo), pero está en la rama de #886, no en el pre-registro sellado; leerla junto al veredicto. Si D25 no
  cierra, la palanca siguiente es D17 (área), que #886 no separa.
- **El PR:** mergear #886 como evidencia (sólo agrega `experiments/`) o cerrarlo con puntero; hoy no está en `main`.

## 2. Recall VIIRS 750 (#887, rama `s158-v750-recall`, borrador, sin tocar desde 2026-10-21 12:46 UTC)

**Qué concluye** (`experiments/_s158_v750/README.md`, ventana 2026-03-01 a 2026-10-21, lectura A, regla SN, predicado
del tablero con node): 324 alertas con record, 249 publicadas, **75 perdidas** (recall 0,7685).
- **55 de 75 (M3)** son el patrón de D25: se alerta un píxel en el cráter (54 sólo por la recaptura del segundo pase),
  su BT queda bajo el fondo del anillo, la magnitud se recorta a 0,0 MW y el tablero lo oculta. El fondo es el de
  siempre; lo que cambia es que el píxel está más frío.
- **20 de 75 (M1)** no alertan ningún píxel; 11 con cenit de 35° o más, 9 debajo. Sin causa separada.
- El lector de M15 no causa ninguna (probe L1B, run 39597022719, 125 de 127 pasadas, C-P1 en 125 de 125). El «M13
  sano» de #880 era leer sentinelas de 16 bits en una banda de 32.
- Para el operador casi no hay pérdida: 74 de 75 caen en noches que el volcán publica por otra vía. Sólo 1 protegida
  (PCC 2026-10-10, #865, cerrado).
- Lateral latente: `FLAG_DNS` de `process_viirs_mod.py` es de 16 bits; sin LUT de M13 dejaría pasar códigos como
  radiancia. Sin efecto hoy.

**Verificado por verificador limpio** (en primer plano, según el README): reprodujo byte a byte las salidas de
`listar_perdidas.py`, `analizar_probe.py` y `prueba_probe_m15.py`, y rebajó cuatro frases (cenit de M1, «BT bajo el
fondo» es tautológico, contraste con negativos sin condicionar, igualdad exacta de M13 y M15 en la escena); las cuatro
están corregidas. No leí un informe de verificador aparte en la rama: lo que digo del verificador sale del README.

**¿Siguen valiendo con los datos de hoy?** Sí en lo que muestreé. `muestra.py` tomó, sin elegir a mano, todas las
pérdidas de PCC (14) y Tupungatito (11) y las tres primeras de Isluga de `perdidas_v750.json`, y comparó clase,
`pc.vrp_mw`, número de píxeles y `t_bg_k` con el record de hoy en `main`: **28 de 28 iguales**. No recalculé el recall
de la ventana de #887; el auto-audit de hoy da 72,9 % con n 48 en su propia ventana, del mismo orden.

**Ojo con un número que se podría leer como contradicción:** #887 dice que condicionado a que haya algún píxel
alertado, M3 aparece en 18 % de las positivas y en **37 %** de los negativos limpios. O sea, despegar del cero todos
los M3 publicaría proporcionalmente más donde MIROVA calla. El pre-registro de D25 lo contempla como P2 y no predice
el signo en VIIRS 750 (predicción 5). Sus conteos (11 y 23 alertas recuperables, 17 y 21 negativos encendibles, l. 130
a 145) son de las ventanas V1 y V2 del A/B, no de la de #887; no son comparables directamente con los 55.

**Qué falta para cerrar el punto de #864:**
- **M3 (55 de 75):** lo decide la lectura del A/B de D25 en VIIRS 750, con P2 como freno (si recupera alertas pero
  enciende más negativos, no sirve).
- **M1 (20 de 75):** nadie la tiene. #887 descartó el lector de M15; quedan señal bajo el umbral, D17 o geometría
  oblicua, sin medir. Es la parte de VIIRS 750 que ni D25 ni ningún frente abierto contesta.
- **Decisión de Nicolás que habilita cerrar sin arreglar:** con 74 de 75 noches cubiertas por otra vía (A94), el recall
  por pasada de VIIRS 750 puede quedarse fuera de banda sin que el operador pierda noches. Si se acepta así, la banda
  79,5 % por pasada de VIIRS 750 en el auto-audit deja de ser la vara correcta y conviene medirla por noche o con la
  misma pasada en banda I. Es un cambio de criterio, no de detector.
- **El PR:** mergear #887 como evidencia o cerrarlo con puntero; hoy no está en `main`. El `FLAG_DNS` queda como
  seguimiento (tocaría `pipeline/`, ciclo A45).

## 3. Chillán MODIS (sin PR propio; frente S159 en `main`)

**Qué hay** (`experiments/_s159/chillan_modis/INFORME.md`, probe L1B sobre 7 gránulos, runs 39692725826 y 39693552091):
las dos protegidas de #864 (T1 2026-10-12 07:20, T2 2026-10-15 01:05, cenit ~58°) caen en el **Test 2 bajo la
conectiva `max`** (dNTI a 3,78σ y 3,72σ cuando hace falta 5), y aunque se detectaran (con `min` en los dos pases sí se
detectan) **la magnitud saldría 0 MW**: la cumbre está más fría que el anillo y el exceso se recorta a cero. No hay
saturación, la banda 21 no ayuda, la σ está dentro del rango de los controles.

**Verificado por verificador limpio** (`verificador/INFORME.md`): CONFIRMADAS el Test 2, la magnitud 0, los controles y
el estrato (por los CSV remotos). PARCIALES: la compuerta de 3 K (la aritmética sí; que la cumbre nevada sea la causa
física, SOSPECHA, porque la geolocalización de estas pasadas está comprimida, 0,40 km entre filas en T1, y no se
descartó nube) y «sólo `min` y sin compuerta juntos» (con el flag real, `min` sola detecta).

**¿Sigue valiendo hoy?** Los records de T1 y T2 en `main` siguen con 0 píxeles, sin cúmulo, y el píxel más caliente de
la escena a 24,17 y 29,12 km del cráter (`muestra.py`). La magnitud 0,485x (n 7) es idéntica a la de #864 y su caída
está en las pasadas oblicuas (0,17 y 0,20 sobre 30°; 0,707 bajo 30°, en el borde de la banda). Por ejemplo la pasada
de 2026-10-15 07:35 (cenit 44°) publica 3,12 MW contra 15,27 de MIROVA (tabla), 0,20.

**Qué no cubre nadie:**
- D25 no existe en `process_modis` y MODIS quedó fuera del A/B (D-26; #864 comentario del 2026-10-21). La λ de la banda
  22 (#872, flag apagado) mueve +5,75 %, no cierra un 0,2.
- El déficit de magnitud en las pasadas oblicuas **publicadas** de MODIS no está descompuesto aparte (#869 lo tocó con
  un techo de fondo cero de 0,96 a 1,48; S159 trató sólo las no publicadas). SOSPECHA: el mismo par fondo de anillo y
  geometría (D17, `_interp_geo`) explica ambas, no medido.

**Qué falta para convertirlo en decisión de Nicolás:** S159 ya la planteó y nadie la registró en
`tasks/LOOP_OBJETIVOS.md` §5 (busqué «Chillán» junto a «MODIS» y no hay decisión abierta). Las dos palancas son la
conectiva (`max` entró con K en S153) y un fondo de magnitud MODIS que siga a la cumbre (la cara MODIS de D25); ninguna
sola basta en T1 y T2. Cualquiera de las dos toca `pipeline/` y pide A45 y un A/B propio. Antes de eso, lo barato que
falta: medir la geolocalización con MxD03 en las pasadas oblicuas (el frente M ya vio que el cráter se mueve 5,75 km en
T1), porque decide si «el píxel del cráter» es el correcto.

## 4. Fuera de los tres, para no perderlo

- **PCC VIIRS 750 0,517x (n 10)** es un flag nuevo de hoy, no de #864. Por cenit: bajo 30° 0,76 (6), sobre 30° 0,07
  a 0,29 (4). #887 tiene 14 pérdidas de PCC en VIIRS 750 (7 M3 y 7 M1, en su ventana; contadas en `muestra.py`). PCC tiene `local_kernel_bg: true`
  en `volcanoes.yaml`. Sin causa medida; SOSPECHA de que sea el mismo patrón oblicuo de Chillán VIIRS 750 (#869).
- Isluga (0,493, n 44), Láscar VIIRS 375 (0,552) y VIIRS 750 (0,338) y Lastarria (0,644) están bajo 0,7 hoy pero no
  levantan flag porque están en `UNDER_BAND_KNOWN` (`scripts/auto_audit_weekly.py`, comentario S141: sacarlos al cerrar
  la Fase 1).
- Chillán VIIRS 375 y 750: a la espera de D25, como acordó Nicolás el 2026-10-21 (comentario de #864).

## 5. Resumen para decidir

| punto | causa medida | verificador | lo decide | falta |
|---|---|---|---|---|
| Tupungatito, 2 protegidas | alertas lejanas mal rotuladas por el OCR | CONFIRMADO | Nicolás: criterio de distancia en el auto-audit | implementarlo; mergear o cerrar #886 |
| Tupungatito, magnitud | fondo del anillo (parte D17) | PARCIAL | lectura del A/B de D25 | leer la predicción de #886 junto al veredicto |
| VIIRS 750, M3 (55/75) | patrón D25 | reproducido | lectura del A/B de D25 (con P2) | nada antes del veredicto |
| VIIRS 750, M1 (20/75) | sin medir | n/a | nadie | un frente propio, o aceptar que la noche está cubierta |
| VIIRS 750, la vara | 74/75 noches cubiertas | reproducido | Nicolás: ¿recall por pasada o por noche? | decisión |
| Chillán MODIS, 2 protegidas | Test 2 con `max` y fondo de anillo | CONFIRMADO / PARCIAL | Nicolás: registrar la decisión de S159 | MxD03 en oblicuas; A/B propio con A45 |
| Chillán MODIS, magnitud 0,485 | sin descomponer aparte | n/a | nadie | SOSPECHA: mismo mecanismo |
| PCC VIIRS 750 0,517 (nuevo) | sin medir | n/a | nadie | se verá el lunes en el issue nuevo |

## Reproducir

```bash
git -C "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile" archive origin/main scripts pipeline data/mirova_equivalent data/mirova_reference volcanoes.yaml frontend | tar -x -C <dir>
cd <dir> && mkdir -p data/audit_continuous && VRP_PROFILE=mirova_equivalent python scripts/auto_audit_weekly.py
python -I muestra.py <dir con perdidas.json> <dir>
```

`perdidas.json` es `git show origin/s158-v750-recall:experiments/_s158_v750/perdidas_v750.json`. El auto-audit escribe
su `latest.json` dentro de `<dir>`, no en el repo.
