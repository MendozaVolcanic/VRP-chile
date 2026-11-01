# Verificador con contexto limpio, frente 4 (S155): cierres que el detector K pudo volver falsos

Worktree `D:\vrp-trabajo\worktrees\s155-audit-f4`, detached en `cb90031a` (origin/main, 2026-10-19 10:27 UTC).
No leí `experiments/_s155_audit/frente_4/`. Nada del repositorio fue modificado (`git status`: sólo
`?? experiments/_s155_audit/`). Flags leídos desde `pipeline.profile`; publicación = predicado del tablero
ejecutado con node (`banco_paridad.correr_node` sobre `frontend/index.html`, control de identidad
`([0,1,1,1,0],[1,0])` verificado en `base.py`). Referencia MIROVA: snapshot del repo (sync 2026-10-18 23:10 UTC).

## Instrumento

`base.py REF DESDE HASTA` arma una fila por record de los 11 Tier A con el predicado del tablero, las etiquetas
de MIROVA del banco (reglas `original` y `SN`) y el régimen (`K` si `processed_utc >= 2026-10-18T09:57:30Z`).
Dos tablas:
- `main_jul_oct.jsonl`: worktree, 2026-07-01 a 2026-10-19, 12.864 records.
- `tag_c0_ventana.jsonl`: tag `pre-s154-reproc-k-datos` (las MISMAS pasadas escritas con C0 antes del
  reproceso), 2026-09-18 a 2026-10-18, 3.576 records.

**La comparación que decide es la pareada** (mismas pasadas, mismo mes, mismo estado del volcán, sólo cambia
el detector). Las comparaciones C0 de agosto-septiembre contra K de septiembre-octubre mezclan estación y
detector, y en magnitud eso solo mueve la mediana de VIIRS 375 en 0,15 (ver F4-07).

Las dos preguntas del instrumento van en la cabecera de cada script. Controles positivos usados: el par
C0/K de las mismas pasadas cambia en los tres sensores (a1); `todo_publica`/`nada_publica` dan 1 y 0 (a3);
λ21=λ21 da cociente 1 (a11); las fracciones de a4 no son 0 ni 1 en todos los estratos.

## Veredictos

| ID | Veredicto | Grav. | Evidencia (salida cruda en este directorio) |
|---|---|---|---|
| F4-01 | CONFIRMADO (con matiz menor) | 4 | `a1_escalon.out`, `a1b_chillan_mirova.out` |
| F4-02 | CONFIRMADO (corrijo un detalle) | 2 | `a2_c0_residuales.out` |
| F4-03 | PARCIAL: números sí, «se invirtió» no | 2 | `a3_brecha.out`, `a3b_perdidas.out` |
| F4-04 | PARCIAL: vale para el Test 2 en cumbre, no para todos | 2 | `a4_umbral.out` |
| F4-05 | CONFIRMADO en la premisa; matices | 3 | profiles del tag (abajo), `a5_cumulo_cero.out` |
| F4-06 | CONFIRMADO «no idéntico»; «más ciego en MODIS» débil | 2 | `a6_perfiles.out`, `a6b_lab_modis.out` |
| F4-07 | PARCIAL: V375 baja menos de lo dicho, V750 REFUTADO, D5 ya marcada | 2 | `a7_magnitud.out` |
| F4-08 | CONFIRMADO en dirección, n chico | 2 | `a8_modis_d9.out` |
| F4-09 | CONFIRMADO | 2 | `a9_test1_inerte.out`, código |
| F4-10 | PARCIAL | 1 | código, `a10_segundo_pase.out` |
| F4-11 | PARCIAL: mecanismo sí, «sale bajo» sin referencia | 1 | `a11_lambda.out`, código |
| F4-12 | PARCIAL | 1 | grep de documentos |
| F4-13 | CONFIRMADO | 1 | `a13_d13.out` |

### F4-01: la marca del cambio de detector está 30 días corrida respecto del escalón de la serie
- ARCHIVO: `frontend/cambio_detector.js:15` (`CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z"`), plugin que dibuja
  la línea en el eje x de tiempo (`:71-96`), aviso «Las comparaciones que crucen esa fecha mezclan dos
  detectores» (`:40-41`); `docs/FICHA_SDA_VRP_CHILE.md:7` («rige desde el merge del PR»). Eje x del diario =
  `datetime_utc` (`frontend/diario.html:584, 653`).
- QUÉ PASA: el operador ve la serie por fecha de OBSERVACIÓN. Las pasadas observadas desde el 2026-09-18 se
  reescribieron con K, así que el escalón está el 18-sep; la línea y el aviso lo ponen el 18-oct. Fracción de
  pasadas VIIRS 375 publicadas por día (11 Tier A): 09-17 42/49 = 0,86, 09-18 8/50 = 0,16, y 0,06 a 0,36 en
  adelante. El par de las mismas pasadas lo atribuye al detector: de 1.282 pasadas V375 que C0 publicaba, K
  publica 276 (1.006 dejan de publicar). Chillán V375: 3 a 5 publicadas por noche del 08 al 17-sep; con K, 1,
  0, 0, 0, 1, 0, 0, 0, 0, 0 del 18 al 27-sep y 3 el 28 (no «ninguna», ése es el matiz). El tag C0 de esas
  mismas noches da 3 a 5 por noche. MIROVA esas noches: RUTINA salvo alertas el 09-14 y el 09-28 (CONS 351
  RUTINA, 6 ALERTA, 6 FP; OCR 5 alertas).
- DASHBOARD: en el diario de 90 días el escalón cae el 18-sep sin marca, y la marca cae en el borde derecho
  diciendo que lo de antes es otro detector. Con Chillán en erupción es exactamente la lectura «la erupción
  declinó» que el comentario del propio archivo dice querer evitar.
- REPRODUCIR: `python base.py WORKTREE 2026-07-01 2026-10-19 main_jul_oct.jsonl`,
  `python base.py pre-s154-reproc-k-datos 2026-09-18 2026-10-18 tag_c0_ventana.jsonl`, `python a1_escalon.py`.
- Lo de #852: el perfil `_s154_reproc_k_historico` es idéntico a la réplica salvo nombre y directorio (a6), y su
  cabecera dice que la ventana 2025-02-15 a 2026-09-17 se pasará a la serie con
  `scripts/reemplazar_ventana_reproceso.py`. Si eso se aplica, la frontera vuelve a moverse (o desaparece).
  CONFIRMADO como intención escrita, no como hecho.

### F4-02: 26 records C0 dentro de la ventana declarada K
- Los 26 son MODIS Terra de cuatro pasadas (09-28 01:25/01:30, 10-02 00:50/02:25, 10-10 01:05/01:10), con
  `processed_utc` anterior al corte; 0 records K antes del 18-sep y 0 C0 después del 18-oct.
- Dos se publican como cumbre, los dos de PCC: 2026-09-28 01:25 (0,852 MW, a 0,6 km) y 2026-10-10 01:05
  (0,378 MW, a 2,2 km). **Corrección**: los DOS tienen fila RUTINA con VRP 0 de MIROVA (CONS), no sólo el del
  10-10; ambos son negativos limpios.
- Gravedad 2 (no 3): dos pasadas MODIS de un mes, bajo 1 MW, en el volcán con más publicación de más (V4-04).

### F4-03: A98 no se invirtió; se atenuó y perdió su premisa
- Pareado, mismas pasadas 18-sep a 17-oct, regla SN, todos los sensores, por noche de volcán: C0 recall 82/82,
  publicación en negativos 0,963 (n 190); K recall 0,963 (79/82), negativos 0,142. Por pasada: C0 0,932 / 0,419;
  K 0,880 / 0,018. Ventana 18-sep a 18-oct: K 81/85 por noche (reproduce el número del auditor), 4 perdidas:
  Chaitén 10-11 (V375, MIROVA 0,16 MW), Isluga 09-19 (V375, 0,06 MW, nuestro cúmulo a 7,9 km queda `far`),
  Villarrica 09-25 (MODIS Aqua 08:05, 0,9 MW a 0,0 km, sin cúmulo nuestro), PCC 10-18. Ninguna protegida.
- Por qué «se invirtió» no se sostiene: en noches, K publica de más en 27 noches negativas (0,142 de 190) y
  pierde 3 a 4 noches positivas. La sobre-publicación sigue siendo la brecha mayor por noche, ahora unas 7
  veces menor. Por pasada se acerca: V750 pierde 12 de 41 alertas y publica de más en 10 de 804 negativos;
  MODIS 4 de 10 contra 8 de 581.
- Lo que sí cae de A98: el «874 de 877 noches detectadas» (recall saturado) ya no vale con K. Necesita marca.

### F4-04: qué término gobierna el umbral
- `pipeline/detection_context.py:525` (`combinar = max if use_prose_branch else min`), `:943` igual en el
  segundo pase; `ENABLE_TESTS_23_PROSE_BRANCH = True`.
- Fracción de records K (18-sep a 19-oct) con `μ+C2·σ > C1`, que bajo `max` significa que gobierna el
  estadístico: dNTI cumbre 1,000 / 1,000 / 0,983 (V375 / V750 / MODIS); dETI cumbre 0,977 / 0,906 / 0,873;
  dNTI escena 0,875 / 0,937 / 0,894; **dETI escena 0,553 / 0,296 / 0,539**. «98 a 100 %» vale sólo para el
  Test 2 en el ROI de cumbre.
- A103 (el piso C1 = 0,003 es el umbral efectivo, en la ruta contextual falla el dETI) se refería a cumbre: ahí,
  con `max`, el estadístico gobierna el dETI en 97,7 % de V375, así que A103 cae para V375. CONFIRMADO en ese
  alcance. Lo de D26 y el GAP #A («dejan de tener efecto nulo») es consecuencia lógica, no medida: SOSPECHA.
- Medido con los `diag_mu/sd` del primer pase persistidos; C1/C2 desde `pipeline.profile`.

### F4-05: el NO ADOPTAR de D22/D25 se midió bajo C0
- Leído con `pipeline.profile` sobre `git archive pre-s143-ab-d22-d25 pipeline`: `mirova_equivalent`
  TEST1_PATH True, PROSE False, B22 False; `_s142_ab_literal` y `_s142_ab_lit_con_compuerta` TEST1_PATH True,
  PROSE False (los 5 brazos `extends: mirova_equivalent`). Y era sólo VIIRS 375: D25 en V750 y MODIS nunca se
  midió en ese A/B.
- Matiz: el pre-registro `experiments/_s150_ab_d22/PREREGISTRO.md` no está «sin correr» a secas: lleva dos marcas,
  SUSPENDIDO (S150, por su verificador) y «NO se rehace» (S151, #788), con la pregunta trasladada a la sonda de
  tres campos. Lo que sigue vigente: el veredicto de S143 es de C0 y nadie lo marcó.
- Láscar 2026-10-08 08:00 MODIS Aqua: cúmulo cumbre 0,0 MW (1 píxel, del segundo pase), MIROVA ALERTA 0,29 MW a
  1,0 km. CONFIRMADO el hecho. La atribución a D25 (exceso contra la mediana del anillo recortado a cero) es
  consistente con un cúmulo detectado de 0,0 MW, pero no la medí píxel a píxel: SOSPECHA. Y no es caso único,
  ver V4-03.

### F4-06: el laboratorio corre C0
- `a6_perfiles.out`: `experimental` difiere de la réplica en `ENABLE_TEST1_PATH` (True), `PROSE_BRANCH` (False),
  `MODIS_B22_PRIMARY` (False), además de nombre y directorio; `experimental_ndc_focus` igual más dos sensores
  apagados. A117 («idéntico salvo el directorio») es FALSO hoy.
- «Más ciego en MODIS»: mismas pasadas 18-sep a 19-oct, el laboratorio publica 61 MODIS contra 18 de la réplica,
  41 contra 6 en negativos limpios, y en alertas de MIROVA 3 de 6 contra 4 de 6. Hay 4 pasadas MODIS que la
  réplica publica y el laboratorio no. O sea: ya no es superconjunto de la réplica en MODIS (4 records), pero
  llamarlo «más ciego» exagera; en total ve mucho más, la mayor parte en negativos.
- El guard `tests/test_guard_laboratorio_no_mas_ciego_s147.py` sólo compara los tres pisos de magnitud
  (`:75-107`), así que no puede ver un cambio de detector. Ése es el defecto de fondo.

### F4-07: magnitud contra MIROVA
- Pareado (mismas pasadas con alerta, que ambos publican): V375 0,637 a 0,545 (n 134); **V750 0,418 a 0,418
  (n 29)**; MODIS 0,58 a 0,635 (n 3). No pareado (C0 29-ago a 17-sep contra K): V375 0,793 a 0,542.
- La caída de V375 es real pero la mitad de lo dicho: la ventana sola mueve la mediana C0 de 0,79 a 0,64. En V750
  el «0,60 a 0,42» es selección y ventana, no detector: en las mismas pasadas la razón no cambia. REFUTADO para V750.
- «D5 resuelta de MISSION»: `docs/MISSION.md:198-201` ya dice «D5 tampoco está resuelta» (marca S146). REFUTADO
  ese punto. S103 (0,78× / 0,80×), A66/A67/A99 siguen siendo números C0 sin marca: PARCIAL.

### F4-08: A82/D9 bajo K
- Cúmulo con magnitud dentro del inner, MODIS, pareado: C0 0,151 en negativos (n 558) contra 0,300 en positivos
  (n 10); K 0,011 contra 0,600. Dirección confirmada; con n = 10 positivos no alcanza para declarar que MODIS
  «separa». (Ojo: el 89,1 / 93,7 de A82 es de otra ventana C0; aquí C0 ya da 15 / 30.)
- D9, mismas pasadas: 129 topados en C0 (21 publicados), 1 en K: PCC 2026-10-03 01:25 MODIS Terra, 5,0 MW,
  cumbre, publicado, en negativo limpio (RUTINA). CONFIRMADO.

### F4-09: cinco flags del Test 1 sin efecto con K
- Código: el Test 1 entra sólo con `ENABLE_TEST1_PATH` (`process_viirs.py:1126`, `process_modis.py:741`,
  `process_viirs_mod.py:754`); ctxpeak y keep_peak exigen `final_hotspot_source == "test1"`
  (`process_viirs.py:1876-1880`); la prioridad de cúmulo débil exige `test1_centroid_lat` (`:1800-1804`); el fondo
  intermedio y el L_bg global sólo alimentan `effective_L_bg`, que se usa en ramas `source == "test1"`
  (`:1904-1963`, `process_modis.py:1365-1377`).
- Medido: 3.661 records K, 0 con `triggered_test1`, 0 con `n_test1_pixels > 0`, 0 con fuente `test1` (C0: 51 de
  9.203). CONFIRMADO. D10 sin marca de K en sus primeras líneas; A100 en `CLAUDE.md:1313` sin marca. El cierre
  de keep_peak de S144 no lo revisé: SIN VERIFICAR. Nota: `FOCAL_CLUSTER_KEEP_PEAK` (otro flag, en
  `cluster_hotspots` de MODIS y V750) sí sigue activo.

### F4-10: la marca S153 de D19 y el segundo pase
- `docs/MIROVA_DIVERGENCES.md` (D19, marca S153): «el second pass sin conjunto activo (D2) no lo toca K». Código:
  `process_viirs.py:1235` y `:1375` pasan `use_prose_branch` a `second_pass_adjacent`, que usa `max`
  (`detection_context.py:943`). K sí cambia el umbral del segundo pase; lo que no cambia es que corra sin
  conjunto activo (`ENABLE_SECOND_PASS_CONDITIONED = False`). La frase es ambigua, no falsa en lo que dice de D2.
  Pero D2 pesa más con K: ver V4-02.

### F4-11: λ de la banda 21 con BT de la banda 22
- `process_modis.py:550-554` (B22 primaria), `:1036-1062` (L_bg y radiancia del píxel con `BAND21_LAMBDA`).
  ΔL(λ21)/ΔL(λ22) = 0,93 a 0,96 en pares típicos; sobre 23 records K MODIS con píxeles, mediana 0,944
  (0,929 a 0,951). Mecanismo CONFIRMADO. «Sale 5 a 6 % bajo» necesita decir contra qué: `WOOSTER_COEFF` se
  calibró empíricamente con la cadena de banda 21 (S14), así que contra MIROVA el sesgo no está medido (SIN
  EVIDENCIA). Mismo λ21 en el NTI sintético del ETI y del primer pase (`:773`, `:857`); la regresión cuadrática
  probablemente lo absorbe: SOSPECHA, gravedad 1.

### F4-12: D4 y D23
- `docs/MISSION.md` ya tiene marca S153 en «Si encontrás que el literal puro pierde recall» (~l. 327); el catálogo
  (`MIROVA_DIVERGENCES.md:107` y la tabla de `:701`, «Cerrado S27») no. D23 (`:2676`) trata del K1 por píxel, que
  K no cambia; una marca no es obligatoria, aunque con el Test 1 integrado apagado ya ningún camino captura los
  interiores de colada con dNTI cercano a 0 (SOSPECHA de mayor peso). PARCIAL.

### F4-13: D13
- Pareado, records con cúmulo de magnitud > 0: la cerca `dc != summit` apaga 615/2.344 (0,262) en C0 y 137/481
  (0,285) en K. En magnitud 0,570 contra 0,132. Composición: en C0 es MODIS (582 de 615), en K es VIIRS 375 (115
  de 137; en C0 V375 eran 6). CONFIRMADO.

## Hallazgos propios

**V4-01 (2). La marca no distingue «fecha de adopción» de «fecha desde la que la serie es K», y nada en el dato
lo dice.** Los records sí lo saben (`processed_utc`, y `regimen.codigo_sha` en los nuevos; los 26 C0 de F4-02
tienen `regimen: null`), pero el frontend no lo usa. Un arreglo que tome la fecha del dato y no la del merge
sobreviviría a #852. Es el mismo defecto de F4-01 visto como diseño.

**V4-02 (3). Con K, el segundo pase sin conjunto activo (D2) sostiene una parte grande de lo que se publica, y la
evidencia de la decisión D2 pendiente es de C0.** Publicaciones con primer pase vacío y sólo recaptura, mismas
pasadas: V375 26/1.245 en C0 contra 46/264 (17 %) en K; V750 31/383 contra 19/61 (31 %). En K, 14 de esas 46 de
V375 y 7 de las 19 de V750 son pasadas con alerta de MIROVA (9 y 4 en negativos). Encender
`ENABLE_SECOND_PASS_CONDITIONED` con K apagaría esas 21 pasadas con alerta. El A/B de S135 que estudió D2 corrió
con C0. `a10_segundo_pase.out`.

**V4-03 (2). Cúmulos de cumbre con 0,0 MW (detectados, invisibles) en V750 y MODIS, con alerta de MIROVA.** Mismas
pasadas: V750 28 de 109 cúmulos en K (119 de 532 en C0); con alerta de MIROVA 7 en K contra 6 en C0. Lista K:
Láscar 09-20, 09-21, 09-22, 10-08 (V750) y 10-08 (MODIS); Isluga 09-20, 10-12 (V750) y 10-06 (V375); Chillán
10-01 (V750). Es el mecanismo de D25 fuera del sensor donde se midió. `a5_cumulo_cero.out`.

**V4-04 (2). Con K, la publicación de más que queda se concentra en Cordón Caulle.** Negativos limpios, 18-sep a
19-oct: PCC aporta 20 de 46 publicaciones (MODIS 6/59, V375 9/68, V750 5/73) y las 6 de 1 MW o más (V750 1,0 a
1,7 MW; MODIS 1,45 y el 5,0 topado de F4-08). No sé si es artefacto o el lacolito difuso real (A20, A68): no lo
clasifiqué. `a14_neg_por_volcan.out`.

**V4-05 (1, denominador). La noche del 2026-10-13 no tiene ningún record VIIRS** en los 11 volcanes, ni en el tag
ni en main (MODIS sí, 24). MIROVA tampoco tiene filas VIIRS nocturnas esa noche (sólo 17 a 19 UTC). Parece un
hueco de datos aguas arriba, no del pipeline; cualquier serie diaria lo muestra como cero.

## VERIFICADO LIMPIO

- Flags de K en producción: `ENABLE_TEST1_PATH False`, `ENABLE_TESTS_23_PROSE_BRANCH True`,
  `ENABLE_MODIS_B22_PRIMARY True` (`VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."`).
- Perfil del histórico `_s154_reproc_k_historico` idéntico a la réplica salvo nombre y directorio
  (`python a6_perfiles.py _s154_reproc_k_historico`).
- Reproceso de la ventana: 0 records K con fecha anterior al 18-sep, 0 C0 posteriores al 18-oct; los únicos C0
  dentro son los 26 MODIS Terra (`a2_c0_residuales.out`).
- Test 1 inerte con K: 0 de 3.661 (`a9_test1_inerte.out`).
- Las 4 noches perdidas con K están todas bajo 1 MW de MIROVA: ninguna alerta protegida perdida en la ventana
  (`a3b_perdidas.out`).
- El tag `pre-s154-reproc-k-datos` existe (`d024b990`) y sirve de gemelo C0 de la ventana: es la base pareada que
  conviene usar en cualquier medición futura de este frente.
- Predicado del tablero: control de identidad del banco verde en cada corrida de `base.py`.
