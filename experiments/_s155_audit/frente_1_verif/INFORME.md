# Verificador con contexto limpio, frente 1 (S155): el detector K contra la documentación y el código

Worktree `D:\vrp-trabajo\worktrees\s155-audit-f1`, detached en `cb90031a` (origin/main, 2026-10-19 10:27 UTC).
No leí `experiments/_s155_audit/frente_1/`. No modifiqué nada fuera de esta carpeta. Flags leídos desde
`pipeline.profile` (salida en `v_flags.txt`).

Las dos preguntas del instrumento van en el docstring de cada script. Salidas crudas al lado:

| script | salida | qué mide |
|---|---|---|
| `v_flags.py` | `v_flags.txt` | flags resueltos de `mirova_equivalent` y `experimental` |
| `v_regimen_por_fecha.py` | `v_regimen_por_fecha.txt` | records con Test 1 por tramo de fecha, hoy |
| `v_regimen_control.py` | `v_regimen_control.txt` | lo mismo sobre los JSON en `34cea39e` (control positivo) y en HEAD |
| `v_escalon_ndc.py` | `v_escalon_ndc.txt` | dónde cae el escalón de la serie (aproximación, no el predicado del tablero) |
| `v_fuente_hotspot_k.py` | `v_fuente_hotspot_k.txt` | `final_hotspot_source` bajo C0 y bajo K |
| `v_eruption_marcador.py` | `v_eruption_marcador.txt` | si el marcador de los records `eruption` se aleja del cúmulo |
| `v_lambda_b21_con_b22.py` | `v_lambda_b21_con_b22.txt` | efecto de usar la longitud de onda de la banda 21 con datos de la 22 |
| `v_covalid.txt` | (comando en el texto) | flag de co-validación del camino D |
| `revert_simulado.txt` | `git merge-tree --write-tree --merge-base=34cea39e HEAD 34cea39e^` | revert simulado sin tocar el árbol |

## Veredicto sobre la lista del auditor

| ID | mi veredicto | mi gravedad | nota corta |
|---|---|---|---|
| F1-01 | PARCIAL | 3 | conflicto CONFIRMADO; «el aviso seguiría diciendo K» REFUTADO; el problema real es otro (V1-01) |
| F1-02 | PARCIAL | 2 | el título sí fecha las métricas (S119, 2026-07-01); falta decir que son de C0 |
| F1-03 | PARCIAL | 2 | D21 y D30 CONFIRMADO, con la marca en la línea siguiente; D26 «ABIERTA» es correcto |
| F1-04 | CONFIRMADO | 2 | números reproducidos del log; MISSION tiene marca general arriba, D11 y A82 no |
| F1-05 | CONFIRMADO | 2 | |
| F1-06 | CONFIRMADO | 2 | además Tupungatito 09-14 contradice la frase de la ficha |
| F1-07 | CONFIRMADO | 2 | el propio YAML se contradice (l. 26-30 contra l. 63-77) |
| F1-08 | PARCIAL | 1 | sin marca, pero parte del mecanismo A69 sigue (compuerta D22, etiqueta MODIS): SOSPECHA |
| F1-09 | PARCIAL | 2 | vent-path y BT tienen otra justificación propia; D4 «resuelta» sí cae |
| F1-10 | CONFIRMADO | 1 | |
| F1-11 | CONFIRMADO | 2 | `test1_integrated.py` se contradice en su propia cabecera |
| F1-12 | CONFIRMADO | 2 | |
| F1-13 | CONFIRMADO | 1 | además D-4 figura como pendiente |
| F1-14 | CONFIRMADO | 1 | |
| F1-15 | CONFIRMADO en el texto, invisible en el mapa | 1 | 52 `eruption` bajo K (24 summit); marcador = cúmulo en 24 de 24 |

### F1-01. Reversión por `git revert`
- `revert_simulado.txt`: `CONFLICT (modify/delete): frontend/cambio_detector.js` y `tests/test_cambio_detector_s153.py`
  (modificados por #851, `a7a466771`). El perfil y el resto revierten limpio. CONFIRMADO.
- «Si se resuelve conservando HEAD, el aviso seguiría diciendo K»: REFUTADO. En el árbol simulado `8bf51b81`
  las tres vistas quedan con 0 inclusiones de `cambio_detector.js` (el revert quita la línea `<script>` que #850
  agregó); el archivo queda huérfano y no se dibuja nada.
- «Ningún texto nombra el commit»: cierto para el hash, pero FICHA, MISSION:17 y D21/D26/D30 nombran «el PR de
  adopción» y el tag `pre-s153-adopcion-k`. Ningún documento da el número #850 (sólo un comentario en
  `frontend/index.html:1624`).
- Lo grave no es esto, ver V1-01: el revert no toca los datos escritos con K.

### F1-02. Modal «Acerca de»
`frontend/index.html:542-552`: título «Métricas de desempeño (S119, auditoría integral post-flip C2, 2026-07-01)»
y «Algoritmo operacional: Coppola 2016a literal (Tests 2∧3 ...)». Las métricas están fechadas en el título, así
que no son del todo «sin marca»; lo que falta es decir que se midieron con el Test 1 integrado encendido y antes de
#535, y que el detector cambió. El «Algoritmo operacional» nunca nombró el Test 1, ni bajo C0. PARCIAL, 2.

### F1-03. Encabezados de D21, D26, D30
`docs/MIROVA_DIVERGENCES.md:2601` (D21 «ABIERTA»), `:2849` (D30 «ABIERTA»): CONFIRMADO, y `CLAUDE.md:1822` y
`docs/MISSION.md:208` mandan leer «los encabezados». Pero la marca S153 está en la **línea inmediatamente
siguiente** en los tres (cumple A113 b) y termina con «El encabezado y el texto que siguen se conservan por
historia». Sólo engaña a quien hace `grep '^## D'`; ningún script parsea esos encabezados (busqué `ABIERTA` en
`scripts/ tests/ pipeline/ .github/`: un solo uso, ajeno). D26: su encabezado dice «ABIERTA, efecto nulo bajo la
conectiva `min`», que es un enunciado condicional ya marcado como caído en el mismo encabezado; su marca S153 dice
«D26 queda abierta y sin medir bajo `max`», así que «ABIERTA» es correcto. PARCIAL, baja a 2.

### F1-04. D11 sigue cerrada
- `docs/MIROVA_DIVERGENCES.md:1492`: «CERRADA S114, CONDICIONADA S138 ... valen sólo bajo banda 21 primaria y
  compuerta de 3 K ... No se reabre ... hasta consolidar D21/D22». La única nota S153 dentro de D11 (l. ~1557) es
  sobre la conectiva, no sobre la condición. CONFIRMADO.
- Los números del auditor salen del log de la evidencia: `experiments/_s153_fk_v2/v2.log:232-240`, «MODIS fuera de
  Lascar ... todos C0 242 de 2173 | K 18 de 2173» (V2, 2026-03-01 a 2026-06-12, negativos limpios). Leídos, no
  recalculados.
- A82 (`CLAUDE.md:1020`) dice «Sólo Láscar; en los otros diez volcanes no está medido»: ese mismo log lo midió.
  CONFIRMADO.
- `docs/MISSION.md:215-217`: lo cubre a medias la marca general de `MISSION.md:8-17` («Toda frase ... con la banda 21
  describe el estado previo a S153»), que el auditor no menciona. No dice que D11 se reabre.
- Gravedad 2: no tuerce una alerta hoy (producción ya corre K); apaga trabajo futuro.

### F1-05. Cabecera de `pipeline/profiles/mirova_equivalent.yaml`
l. 1-21: «clon literal MIROVA con Test 1 integrated-ROI activo», «Test 1 integrated-ROI ON en MODIS B21». Las marcas
S153 están junto a cada flag (l. 263-271, 573-578), no en la cabecera. CONFIRMADO, 2.

### F1-06. Ficha SDA
- Costo de VIIRS 750 ausente: CONFIRMADO. `v1.log:155-157` recall 32 → 28 de 42; `v2.log:227-228` 95 → 91 de 117.
  La ficha (l. 25 y fila v1.9) sólo da el costo de VIIRS 375.
- «ninguna protegida queda sobre otro objeto»: CONFIRMADO que excede la fuente. `experiments/_s153_fk_v2/a61/INFORME.md:140`
  dice «No encontré ...» y l. 148 «Que el objeto publicado por K sea el de MIROVA: SIN VERIFICAR en las 14». Y la
  fila de Tupungatito V375 09-14 06:18 (l. 136) dice «ninguno de los dos es el objeto de MIROVA»: hay una protegida
  (dudosa) donde K publica otro objeto que el de MIROVA.

### F1-07. «El laboratorio es idéntico al operacional»
- `pipeline/profiles/experimental.yaml:26-30` y el docstring de `tests/test_guard_laboratorio_no_mas_ciego_s147.py`
  («Hoy es IGUAL al operacional») son falsos hoy: `v_flags.txt` muestra que difieren en
  `ENABLE_MODIS_B22_PRIMARY`, `ENABLE_TEST1_PATH` y `ENABLE_TESTS_23_PROSE_BRANCH`. El mismo YAML lo dice en l. 63-77
  (bloque S150 del congelamiento): el archivo se contradice.
- «Ve menos en MODIS»: `v2.log:223-224`, protegidas A MODIS C0 6 de 39 contra K 39 de 39. CONFIRMADO, y no es
  monótono: en VIIRS 375 y en negativos el laboratorio publica más. El guard sigue verde porque sólo compara pisos.

### F1-08. A69 y D11 describen el Test 1 como activo
A69 (`CLAUDE.md:851-882`) no tiene marca S153 y cierra con «La causa raíz que A69 describe sigue viva en los 3
sensores» (l. 879-880). El cuerpo de D11 (l. 1501-1507) habla del Test 1 en presente. CONFIRMADO el texto. Pero
«sigue viva» puede seguir siendo parcialmente cierto bajo K por otra puerta: la compuerta `bt > t_bg + 3 K` (D22)
sigue encendida (`ENABLE_TESTS_23_NO_BT_GATE_VIIRS375 = False`) y la etiqueta MODIS sale del `final_hotspot`
(`enable_modis_distance_class_from_cluster: false`). SOSPECHA, no medí cuánto. Gravedad 1.

### F1-09. Cierres justificados con «el Test 1 cubre lo sub-píxel»
- Vent-path: `mirova_equivalent.yaml:190-193` («Test 1 integrated-ROI cumple rol equivalente para sub-pixel»), pero
  la razón primera es «vent-path NO existe en papers MIROVA», que no cae.
- BT path: `mirova_equivalent.yaml:414-421`, razón primera «paper Coppola 2016a NO menciona bt_path puro»; tampoco cae.
- D4: `docs/MISSION.md:203` «Resueltas: ... D4 recall sub-pixel (S27)» sin marca propia (sólo la general de arriba);
  H_S27_1 sí tiene marca S153 (`MIROVA_DIVERGENCES.md:802`). Y K pierde justo lo sub-píxel: `v1.log:91` 16 de 194
  alertas Muy Bajo de VIIRS 375 (0 con C0), `v2.log:148` 26 de 388. D4 está reabierta de hecho. PARCIAL, 2.

### F1-10. «bug fix» y banda 21 en docstrings
`pipeline/detection_context.py:935-939`: «Bug fix S46 Task 5: antes usábamos `max` (AND lógico), ahora `min` (OR
lógico paper-correct)», y producción corre `max`. El primer pase (l. 512-525) sí explica las dos lecturas.
`pipeline/process_modis.py:25-26`: «Band 21 ... primary MIR hotspot channel; Band 22 used where Band 21 is
saturated» (además la física está al revés: la que satura es la 22). `:772`: «B21 primary, B22 fallback».
CONFIRMADO, 1.

### F1-11. Cabeceras FICHA
`pipeline/process_modis.py:5-6` «Tests contextuales y de ROI integrado de Coppola 2016a», sin decir que el Test 1
está apagado; l. 14 «sobre-deteccion difusa irreducible a 1 km». `pipeline/test1_integrated.py:4` «Uno de los 3
criterios MIROVA», l. 7 «Regla determinista (Coppola 2015 Eq.1)», mientras l. 12 dice «DETECTOR PROPIO del
proyecto, no del paper (D30)» y el docstring (l. 34) dice que D30 está «abierta y sin decision». La cabecera se
contradice sola y no dice que está apagado. CONFIRMADO, 2 (son el elemento público de la Res. 372).

### F1-12. Bloques de arranque
En main: `ls tasks/BLOQUE_ARRANQUE_S*.md | sort -V | tail -1` da S150. En `origin/loop/activo`: S152 a S155.
`CLAUDE.md` no menciona la rama. CONFIRMADO, 2.

### F1-13. `docs/INDEX.md`
Último commit 2026-10-14; ninguna fila de S153/S154; l. 109 «A/B de B22: NO ADOPTAR» y l. 26 «ninguno cumple» sin
marca. Además l. 131 da D-4 como «decisión pendiente, issue #782», decidida el 2026-10-14 según el glosario de
`CLAUDE.md`. CONFIRMADO, 1.

### F1-14. D10 y D24
D10 (`MIROVA_DIVERGENCES.md:1434`, «ADOPTADO S100»): el ctxpeak sólo actúa con `final_hotspot_source == "test1"`
(`pipeline/process_viirs.py:1876`), y bajo K no hay ningún record con esa fuente (`v_fuente_hotspot_k.txt`: 0 de
3.687 desde el 2026-09-18). D24 (l. 2691): «el NaN de B21 cae a B22», bajo K es al revés
(`process_modis.py:337-338`). CONFIRMADO, 1.

### F1-15. «con K todos los records son ctx_cluster»
`frontend/index.html:1624`. `v_fuente_hotspot_k.txt`: desde 2026-09-18, 531 `ctx_cluster` y 52 `eruption` (todos
MODIS; 24 con etiqueta summit, 23 con magnitud). Desde el merge (110 records) 0 `eruption`. Efecto en el mapa:
`v_eruption_marcador.txt`, en los 24 summit la distancia de `anomaly_pixels[0]` es igual a `final_hotspot_dist_km`
(0 de 24 a más de 2 km): invisible. El aviso del tablero nombra sólo el Test 1 (`frontend/cambio_detector.js:41`).
CONFIRMADO, 1. Nota: 12 de esos 24 son de Nevados de Chillán y 9 de PCC.

## Hallazgos propios

### V1-01. El tablero marca el cambio de detector el 18-oct, pero la serie cambió el 18-sep
- ARCHIVO:LÍNEA: `frontend/cambio_detector.js:16` (`CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z"`) y `:41`
  («Desde el ... la réplica usa el detector K»); backfill `5783192c1` y hermanos (`data(backfill): <volcán>
  2026-09-18..2026-10-18 (S120)`, 2026-10-18 ~11:04 UTC).
- SCRIPT:SALIDA: `v_regimen_control.txt`: tramo 2026-09-18 a 2026-10-18 09:57, 11 Tier A, Test 1 en 1.586 de 3.576
  records (44,4 %) en `34cea39e`, y en 0 de 3.577 hoy; `processed_utc` 2026-10-18 en 3.529. Control positivo: el
  tramo 2026-08-01 a 09-18 sigue con 39,2 % (`v_regimen_por_fecha.txt`), así que el campo no está muerto.
- QUÉ PASA: el volcán no cambió el 18-sep, cambió el instrumento. Los 30 días previos al merge se reescribieron con K,
  y la línea vertical y el aviso dicen que el cambio fue un mes después. En la tendencia de 90 días el escalón queda
  sin marca. Aproximación (no es el predicado del tablero, `v_escalon_ndc.txt`): records summit con magnitud,
  Villarrica 152 de 353 (18-ago a 18-sep) contra 4 de 352 (18-sep a 18-oct); Láscar 112 de 296 contra 46 de 282;
  Chillán 114 de 353 contra 105 de 325 (en `34cea39e`: 193 de 324). Ningún record dice con qué detector se escribió;
  el bloque S155 además dice que quedaron pasadas Terra sin reprocesar en esa ventana (26 records con
  `processed_utc` anterior). Y el histórico por trozos con K (#852) moverá la frontera más atrás todavía.
- DASHBOARD: el operador ve Villarrica «apagarse» el 18-sep sin aviso, y el aviso le dice que antes del 18-oct todo
  es comparable. Es exactamente el error que `cambio_detector.js:6-7` dice querer evitar («la erupción declina»).
- Además: la reversión (F1-01) no revierte esos datos; tras un `git revert` el tablero mostraría datos K sin ninguna
  marca. Ni la ficha ni MISSION mencionan el reproceso.
- REPRODUCIR: `python experiments/_s155_audit/frente_1_verif/v_regimen_control.py 34cea39e` y `... HEAD`.
- CONFIANZA: CONFIRMADO (datos); la lectura del operador es SOSPECHA razonada (no abrí el tablero).
- GRAVEDAD: 4.

### V1-02. Con la banda 22 primaria, la magnitud MODIS sigue convirtiendo con la longitud de onda de la banda 21
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:1036` y `:1040` (`L_bg_global` y `hotpix_rad` con `BAND21_LAMBDA` sobre
  `bt_mir`, que con K es la temperatura de la banda 22, `:554`); también `:1062`, `:1367-1392`, `:1528`. El paper
  (`MIROVA_DIVERGENCES.md:2623`, cita verbatim de sp426.5 p. 3) dice que la banda corregida está «centred at
  3.959 um», la de la 22.
- SCRIPT:SALIDA: `v_lambda_b21_con_b22.txt`: el ΔL con 3,929 µm queda 3 a 6 % bajo el de 3,959 µm (razón 0,938 a
  0,970 entre T_bg 250 a 280 K y T 255 a 400 K); control 3,929 contra 3,929 da 1,0000. En detección no importa: el
  NTI_app de los Tests 2 y 3 (`:773`, `:857`) también usa 3,929, pero el residuo tras el ajuste cuadrático es
  6,9e-5 contra un C1 de 0,003.
- QUÉ PASA: la radiancia que se resta es la de un cuerpo negro a la temperatura medida por la 22, evaluada en el
  centro de la 21. Bajo C0 era coherente; bajo K subestima la magnitud MODIS unos 5 %. Analítico, no medido sobre
  records (la magnitud MODIS con B22 fuera de Láscar está declarada sin medir en D21).
- DASHBOARD: magnitud MODIS ~5 % baja; podría cruzar 1 MW hacia abajo sólo en alertas al borde.
- CONFIANZA: CONFIRMADO el código; efecto en records SOSPECHA. GRAVEDAD: 1.

### V1-03. La cabecera FICHA del módulo que hoy decide la detección describe la conectiva vieja
- `pipeline/detection_context.py:5` «(NTI_pixel - media(NTI 8-vecinos)) > C1 marca un pixel anomalo», l. 10
  «Variables: C1 ...»: con K el umbral es `max(C1, μ + C2·σ)` (l. 525, 943) y el sigma global puede gobernar; no
  nombra ni C2 ni el dETI. l. 11: «mitigado por co-validacion y cap de magnitud», pero
  `PATH_D_REQUIRES_COVALIDATION = False` en producción (`v_covalid.txt`); sólo el tope de 5 MW actúa.
- Invisible en el tablero; es transparencia pública (Res. 372). CONFIRMADO. GRAVEDAD: 2.

### V1-04. La vigilancia de la sombra que dispara la reversión no tiene código
- La ficha v1.9 (l. 25) y `REGLA_ADOPCION.md:137-145` dicen que cada semana se cuentan producción y sombra contra
  MIROVA con el mismo evaluador, y que una protegida que la sombra ve y la réplica calla se revierte el mismo día.
  Ningún `.py` de main ni de `origin/loop/activo` lee `data/experimental_v2/` salvo un test de aislamiento y un
  script de frescura de S149 (`git grep -l experimental_v2`). `scripts/auto_audit_weekly.py:340-345` guarda la
  serie de negativos de producción, sin alarma y sin la sombra.
- El único disparador de reversión de un SDA en producción depende de que alguien corra el conteo a mano.
- CONFIANZA: CONFIRMADO que no hay código; SOSPECHA que no se haga a mano en el loop. GRAVEDAD: 2.

## VERIFICADO LIMPIO
- Producción corre K: `VRP_PROFILE=mirova_equivalent python experiments/_s155_audit/frente_1_verif/v_flags.py` da
  `ENABLE_TEST1_PATH=False`, `ENABLE_TESTS_23_PROSE_BRANCH=True`, `ENABLE_MODIS_B22_PRIMARY=True`; y en los records:
  0 de 110 con Test 1 desde el merge (`v_regimen_por_fecha.txt`).
- El laboratorio está congelado en C0 y difiere de producción sólo en esos tres flags (diff de `v_flags.txt`).
- El revert simulado del perfil y del resto de #850 sale limpio; sólo choca en el aviso y su test.
- Las marcas S153 existen al inicio de D21, D26, D30, H_S27_1, `MISSION.md:8-17`, el punto NTI de `CLAUDE.md:112` y
  junto a cada flag del YAML.
- Citas: `CLAUDE.md` A10 «l. 1595» es `isValidDetection` (`sed -n 1595p frontend/index.html`);
  `mirova_equivalent.yaml:270` «profile.py:726» es la asignación del flag.
- El marcador de los records `eruption` coincide con su `final_hotspot` (0 de 24 a más de 2 km).
- El error de longitud de onda no toca la detección (residuo 6,9e-5 contra C1 0,003).
- Números de la evidencia que el auditor cita (V750 4 de 42 y 4 de 117; MODIS 6 contra 39; 242 contra 18 de 2.173):
  presentes tal cual en `v1.log` y `v2.log`; no los recalculé desde los records.
