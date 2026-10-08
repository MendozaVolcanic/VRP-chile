# Auditor D, S150: los instrumentos con que el proyecto decide

> Frente D de `docs/PLAN_AUDITORIA_S150.md`. Auditado el 2026-10-08 sobre `main` (327621e2c) y las ramas
> `s146-ab/*`. Sólo lectura sobre el repo; mis sondas están en `experiments/_s150_audit/D/`, cada una con
> su salida cruda al lado (`dN_*.txt`) y con las dos preguntas del instrumento en el encabezado. Los datos
> de los runs (35599902448, 35675490175, 35728617326, 35759688167, 35766187578) los extraje con
> `git archive origin/s146-ab/<run> experiments/_s146_ab_sin_test1/salidas/<run>` a un temporal fuera del
> repo, y armé las tablas de mayo a agosto con `armar_tabla.py` sin tocarlo.
>
> Instrumentos revisados: `armar_tabla.py`, `medir_predicciones.py`, `evaluar_ventana.py`,
> `recall_por_magnitud.py`, `congelar_referencia.py`, `agregado.py`, `determinismo_lascar.py`,
> `modis_lascar_brazos.py`, `magnitud_por_satelite.py`, `calidad_referencia_por_mes.py`,
> `sustrato_referencia.py` (todos en `experiments/_s149_prereg_invierno/`),
> `experiments/_s146_ab_sin_test1/evaluar.py`, `scripts/banco_paridad.py`,
> `scripts/referencia_mirova_unificada.py`, `scripts/calidad_referencia_mirova.py`,
> `scripts/libro_de_cuentas.py` (con `experiments/_s126_lib.py`), `scripts/auto_audit_weekly.py` y
> `.github/workflows/audit-weekly.yml`.

## Resumen

Los instrumentos del A/B de S149 y S150 (`armar_tabla`, `medir_predicciones`, `banco_paridad`) están
**sanos en lo mecánico**: el pareo, la zona horaria, los nombres y la etiqueta se sostienen, y la tabla de
agosto se reproduce exacta. Los dos defectos graves están en la **auditoría automática semanal**, que es la
única alarma de paridad que corre sola: juzga el recall con una vara que no ve la etiqueta `far` (justo el
defecto de la erupción de Chillán) y su guarda de cobertura no distingue un apagón de una falla de
detección, y cuando sí lo distingue se calla. En los instrumentos del A/B, el hallazgo de fondo es que las
predicciones automáticas que quedaron decidiendo en VIIRS (P1, P2, P5 y C8b) **las cumple un brazo tonto que
sólo apaga el borde del barrido**; el brazo F real las cumple por más que eso, así que los veredictos de S150
no cambian, pero el instrumento es más débil de lo que dice.

## Hallazgos (ordenados por gravedad)

### D-01. La auditoría semanal juzga el recall con una vara que no ve lo que el tablero oculta. Gravedad 4

- **SCRIPT:SALIDA**: `scripts/auto_audit_weekly.py`, bloques "2. Nuestros records" (criterio `crater`:
  `0 < pc.vrp_mw <= CAP` y `centroid_dist_km <= INNER`, sin mirar `distance_class`) y "4. Flags contra
  bandas" (el flag usa `recall_crater_pct`; `recall_dash_pct` se calcula y no decide nada).
  Sonda: `experiments/_s150_audit/D/d4_auditoria_semanal_vs_tablero.py`, salida
  `d4_auditoria_semanal_vs_tablero.txt`.
- **QUÉ PASA**. Físicamente: en una noche activa el cúmulo nuestro está en el cráter, pero el píxel más
  caliente de la escena está lejos (otro foco, un salar tibio), y la etiqueta `far`, que se deriva de ese
  píxel, esconde la pasada del tablero (A46/A81). En el código: la auditoría semanal cuenta esa noche como
  detectada, porque su vara "cráter" ignora la etiqueta. El predicado además está reescrito en Python, no
  es el del tablero ejecutado con node (A97). Y MODIS sólo es flaggeable con 15 noches de alerta o más
  (`MIN_N_RECALL`): en la ventana del 2026-10-05 hubo 7, así que MODIS no puede levantar aviso.
- **Medido** (ventana 2026-08-06 a 2026-10-05, la del `latest.json` del 2026-10-05; 11 Tier A; unidad:
  noche de volcán y sensor con ALERTA nocturna de MIROVA):

  | sensor | noches con alerta | "cráter" (decide el flag) | "dash" (no decide) | tablero real (node) |
  |---|---|---|---|---|
  | MODIS | 7 | 85,7 % | 28,6 % | 28,6 % |
  | VIIRS 750 | 50 | 82,0 % | 82,0 % | 82,0 % |
  | VIIRS 375 | 194 | 92,8 % | 92,8 % | 92,8 % |

  Las cuatro noches MODIS que la vara "cráter" da por vistas y el tablero esconde, todas con el cúmulo a
  0,7 a 2,5 km del cráter y etiqueta `far`: Láscar 2026-08-21 y 2026-09-25, **Nevados de Chillán
  2026-09-29** (MIROVA 0,13 MW; nuestro cúmulo 4,94 MW a 1,2 km) y Villarrica 2026-09-25.
- **CÓMO SE VE EN EL DASHBOARD**: el operador no ve esas pasadas MODIS; el informe semanal dice que MODIS
  tiene 85,7 % de recall y no levanta aviso. La única alarma automática de paridad no puede ver el defecto
  que el plan S150 encontró a mano durante la erupción.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_audit/D/d4_auditoria_semanal_vs_tablero.py 2026-08-06
  2026-10-05`. Control positivo: reproduce exactamente las seis cifras de `latest.json`.
- **CONFIANZA**: CONFIRMADO.
- **Matiz**: la pasada grave del plan (Chillán 2026-10-01 08:35, MIROVA 5,18 MW, nuestro cúmulo 2,29 MW a
  0,88 km, `far`) **no aparece** ni en la vara "dash", porque la unidad es la noche y la pasada de las
  01:45 de esa noche sí se publica (leído en `data/mirova_equivalent/NevadosDeChillan.json`). La unidad
  noche es defendible (A94), pero la deja ciega a una pasada oculta cuando otra de la misma noche se ve.

### D-02. La guarda de cobertura de la auditoría semanal culpa a la detección por un apagón, y cuando por fin lo reconoce se calla. Gravedad 4

- **SCRIPT:SALIDA**: `scripts/auto_audit_weekly.py`, bloque "S124: cobertura de la ventana"
  (`dias_nuestros = {d for (_v, _s, d) in ours.keys()}`, donde `ours` sólo recibe claves de noches con
  **detección en el cráter**, y umbral `MIN_COVERAGE_PCT = 80` sobre 61 días);
  `.github/workflows/audit-weekly.yml`, paso "Open issue if out of band" (sólo abre issue si el veredicto
  es `FUERA_DE_BANDA`). Sonda: `experiments/_s150_audit/D/d5_cobertura_semanal.py`, salida
  `d5_cobertura_semanal.txt`.
- **QUÉ PASA**. Cuando el NRT se cae, las noches en que no miramos entran al denominador del recall como
  fallas de detección. S124 puso una guarda para eso, pero (a) mide "días con alguna detección en el
  cráter de algún volcán", no días con datos, y (b) exige bajar de 80 % de 61 días: un apagón de menos de
  unos 12 días no la dispara. Y si la dispara, el veredicto pasa a `DEGRADADO`, que **no abre issue**.
- **Medido** en la corrida del 2026-10-05 (apagón desde el 2026-10-03): la guarda dio 95,1 %, el veredicto
  fue `FUERA_DE_BANDA` por "recall VIIRS375 92.8 % < banda 93.4 %" y abrió el issue #757. De las 14
  noches de alerta V375 no detectadas, **11 no tienen ningún record nuestro** (días 3 a 5 de octubre, entre
  ellas tres noches de Nevados de Chillán); sin ellas el recall es 98,4 %, dentro de banda. Control
  positivo: un apagón simulado de los últimos 10 días deja la guarda en 83,6 %, todavía sobre 80 %.
- **CÓMO SE VE EN EL DASHBOARD**: invisible en el tablero. En GitHub, el issue semanal del apagón dice
  "paridad fuera de banda" y manda a revisar la detección; un apagón de dos semanas o más produciría
  `DEGRADADO` y **ningún issue**.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_audit/D/d5_cobertura_semanal.py 2026-08-06 2026-10-05`.
- **CONFIANZA**: CONFIRMADO (código, `latest.json`, issue #757 listado con `gh issue list`).
- Se cruza con el frente A (operación); acá se evalúa como instrumento.

### D-03. Las predicciones automáticas que deciden en VIIRS las cumple un brazo que sólo apaga el borde del barrido. Gravedad 3

- **SCRIPT:SALIDA**: `experiments/_s149_prereg_invierno/medir_predicciones.py` (C8b, l. 74-94: el nulo
  baraja pos/neg sólo dentro de cada volcán; P2 y P5); lo mismo en
  `experiments/_s146_ab_sin_test1/evaluar.py::selectividad_supervivencia` (nulo por volcán y sensor).
  Sondas: `d7_controles_medir_predicciones.py` y `d8_c8b_confusor_cenit.py`, con sus `.txt`.
- **QUÉ PASA**. Físicamente: al borde del barrido el píxel VIIRS crece y se diluye, y MIROVA alerta menos
  ahí; los negativos limpios se concentran en el borde (agosto: 126 de 197) y las positivas en el nadir
  (66 de 120). La etiqueta y la geometría están correlacionadas. En el código: el nulo de C8b no controla
  el cenit, así que cualquier brazo que corte el borde parece "selectivo por etiqueta".
- **Medido** con brazos sintéticos sobre la tabla real de agosto (V375): el brazo `borde_solo`, que apaga
  todo lo publicado con cenit de 52° o más **sin mirar ninguna etiqueta**, cumple P1 (12,5 %), P2 (0,00),
  P5 (0,25 contra parejo 0,50) y C8b (+0,45 contra nulo +0,22, y con la tabla sola también); sólo lo frena
  P4 (5 pérdidas de 0,5 MW o más). Con un nulo estratificado por volcán **y** zona de cenit, `borde_solo`
  falla en los cuatro meses y el **brazo F real sigue cumpliendo** (mayo +0,88 contra 0,60; junio +0,91
  contra 0,65; julio +0,93 contra 0,63; agosto +0,81 contra 0,60). Controles: identidad falla con los dos
  nulos; el oráculo (publica sólo positivas) cumple con los dos; el apagador al azar falla P2, P4, P5 y C8b.
- **Consecuencia para el plan**: los veredictos de S150 sobre F no cambian. Pero tras la enmienda del recall
  (el recall de VIIRS lo decide Nicolás mirando la tabla), las predicciones que quedan decidiendo solas no
  distinguen una mejora de detección de un recorte geométrico; el peso de la prueba queda entero en la
  tabla por tramo y en las pérdidas del borde (H2 del verificador). Conviene estratificar el nulo de C8b por
  zona.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; tuerce una decisión de adopción, no una pasada.
- **CÓMO REPRODUCIRLO**: armar `tabla_agosto.json` con `armar_tabla.py` (control y brazo del run
  35759688167, referencia `_congelado/agosto`) y correr `python experiments/_s150_audit/D/d7_controles_medir_predicciones.py
  tabla_agosto.json` y `d8_c8b_confusor_cenit.py tabla_mayo.json ... tabla_agosto.json`.
- **CONFIANZA**: CONFIRMADO.

### D-04. El libro de cuentas mide el "recall del DASHBOARD" con una copia vieja del predicado y un filtro nocturno por hora que tira la mitad de las alertas MODIS. Gravedad 2

- **SCRIPT:SALIDA**: `scripts/libro_de_cuentas.py::r_recall_v750_dash` y `r_piso_invisibles` (reescriben
  `isValidDetection` con la regla anterior a #642 de S139: `vrp_mw > 0 o triggered_test1`, sin exigir
  energía al cúmulo, y omiten el control de inner y de artefacto de `mirovaEqVrp`);
  `experiments/_s126_lib.py::cargar_mirova` (noche = hora UTC entre 3 y 9). Sonda: `d6_libro_predicado.py`,
  salida `d6_libro_predicado.txt`.
- **QUÉ PASA**. El libro dice medir "el predicado que el dashboard usa DE VERDAD", pero su copia en Python
  quedó atrás: en 2026 hay **1.224 records** que el libro cuenta como publicados y el tablero no (404 de
  VIIRS 750, 811 de VIIRS 375, 9 de MODIS), y ninguno al revés. El recall VIIRS 750 que registra es 83,52 %
  y con el tablero real es **79,78 %** (267 noches). Aparte, el filtro horario de `_s126_lib` tira **59 de
  132** alertas MODIS nocturnas (las de Terra, antes de las 03 UTC), que entran a `D5_ratio_global` por un
  solo lado: nuestro máximo de la noche las incluye y el de MIROVA no.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. El libro sigue en "OK" porque la banda (78 a 92) es más ancha
  que la deriva.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_audit/D/d6_libro_predicado.py`. Control positivo: la
  sonda llama a la función real del libro y da 83,52.
- **CONFIANZA**: CONFIRMADO.

### D-05. La referencia "congelada" de S149 no está en git, el manifiesto no dice de qué commit salió y nada verifica su sha. Gravedad 2

- **SCRIPT:SALIDA**: `.gitignore:40` (`*.csv`) ignora `experiments/_s149_prereg_invierno/_congelado/*/registro_vrp_*.csv`;
  `git ls-files` de esa carpeta da sólo los seis `MANIFIESTO.json`. Sonda: `d2_reconstruir_congelado.py`,
  salida `d2_reconstruir_congelado.txt`.
- **QUÉ PASA**. Los veredictos de S149 y S150 se apoyan en doce CSV que existen sólo en este disco. Medido:
  **sí se pueden reconstruir desde git**, con la lógica literal de `congelar_referencia.py`: el consolidado
  sale del commit **3872fedd4** (2026-09-14) y el OCR del **d21fe1c0d** (2026-09-20), y con eso los doce
  sha256 coinciden con los manifiestos. Pero el manifiesto no nombra esos commits (el docstring dice que
  guarda "fecha del snapshot" y no la guarda), así que hoy la reconstrucción exige búsqueda.
  `evaluar_ventana.py` no verifica el sha antes de usar los CSV. Y si alguien los fuerza a git, con
  `core.autocrlf=true` salen en CRLF al hacer checkout en Windows y el sha no coincide aunque las filas
  sean las mismas: ya pasa con los CSV congelados de S146, que están en git (consolidado: disco
  `21e44043e2fa`, CRLF; blob `f112027dcbe6`, LF).
- **Lo que no cambia**: entre 3872fedd4 y HEAD las filas viejas del consolidado sólo cambiaron
  `Ultima_Actualizacion` (33 filas), nunca el tipo ni el VRP.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_audit/D/d2_reconstruir_congelado.py`. Control positivo:
  recortar otra vez el CSV del disco reproduce su propio sha en los doce archivos.
- **CONFIANZA**: CONFIRMADO.

### D-06. La cadena de S149 no registra qué predicado del tablero usó. Gravedad 2

- **ARCHIVO:LÍNEA**: `scripts/banco_paridad.py:68` (`HTML = ROOT / "frontend" / "index.html"`, el del
  árbol de trabajo al momento de correr); `armar_tabla.py` escribe `ventana`, `n_ref` y `pasadas`, sin el
  sha de `index.html`; `medir_predicciones.py` tampoco lo imprime. `banco_paridad.main` sí lo guarda, pero
  la cadena del A/B no pasa por ahí.
- **QUÉ PASA**. El predicado se lee del archivo vivo cada vez. Hoy no produjo daño: `index.html` no cambia
  desde el 2026-09-13 (#642, `git log -- frontend/index.html`), antes de todas las evaluaciones de S149 y
  S150. Pero si el frente B o el arreglo de `far` tocan el tablero, reevaluar un mes viejo da otro número
  sin que nada lo diga.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO (leído).

### D-07. La magnitud de VIIRS 375 de la auditoría semanal no es la que ve el operador. Gravedad 2

- **SCRIPT:SALIDA**: `scripts/auto_audit_weekly.py` usa `pc.vrp_mw` para los tres sensores; el tablero
  publica en VIIRS 375 el núcleo F5 (A10, matiz S132). Sonda: `d9_magnitud_semanal_v375.py`, salida
  `d9_magnitud_semanal_v375.txt`.
- **Medido** (VIIRS 375, misma ventana): Lastarria 0,53 con `pc.vrp_mw` contra **0,87** con el núcleo del
  tablero; Láscar 0,45 contra 0,62; PCC 0,96 contra 1,12; Chaitén 1,17 contra 1,36. Láscar y Lastarria
  están en la lista de excepciones que no abren issue por debajo de la banda, justamente por un déficit
  que en parte es de la vara.
- **SOSPECHA anexa**: en varios volcanes el núcleo F5 sale **mayor** que `pc.vrp_mw` en la mediana por
  noche, cosa que no esperaba de un recorte; puede ser que el máximo de la noche venga de records distintos
  en cada vara. No lo seguí (es del frente C).
- **CONFIANZA**: CONFIRMADO en la diferencia; SOSPECHA en la causa.

### D-08. La "noche" es la fecha UTC y parte en dos las pasadas MODIS de las 21 UTC de invierno. Gravedad 1

- **ARCHIVO:LÍNEA**: `scripts/banco_paridad.py:215` (`noche = f["fecha_utc"][:10]`) y `cargar_nuestros`.
- **Medido**: de 20.989 filas nocturnas de la referencia en 2026, 47 son MODIS a las 21 UTC (mayo a agosto,
  todas RUTINA). Quedan agrupadas con la noche local anterior, no con la que empiezan. Efecto: pocas
  decenas de negativos MODIS mal asignados al año; ninguna alerta.
- **CONFIANZA**: CONFIRMADO.

### D-09. `modis_lascar_brazos.py` no comprueba cobertura y compara K y J sobre tablas distintas. Gravedad 1

- **ARCHIVO:LÍNEA**: `experiments/_s149_prereg_invierno/modis_lascar_brazos.py:49` filtra `len(v) == 2` sin
  contar lo que descarta; B y J salen de una tabla y K de otra, con B de otro despacho. En S150 los
  denominadores coincidieron (73 y 96 para los tres), así que hoy no hubo daño; un corte de NASA en un solo
  brazo cambiaría los denominadores en silencio (A108).
- **CONFIANZA**: CONFIRMADO (leído); sin efecto medido en S150.

### D-10. `evaluar_ventana.py` tira el stderr de `armar_tabla` y no se detiene si el determinismo falla. Gravedad 1

- **ARCHIVO:LÍNEA**: `experiments/_s149_prereg_invierno/evaluar_ventana.py:60` y `:86`
  (`stderr=subprocess.DEVNULL`); `:89-90` imprime "FALLA: INDECIDIBLE" y sigue con las predicciones.
- **QUÉ PASA**. El aviso A119 se pierde por ese camino, pero `medir_predicciones.py:98-99` lo vuelve a
  imprimir por stdout, y así aparece en los `resultados/*.txt` (comprobado en `mayo_VIIRS375.txt`). Lo que
  sí se pierde es el traceback si node falla (el `check=True` corta, pero sin decir por qué).
- **CONFIANZA**: CONFIRMADO.

### Confirmados del verificador S150 (leídos, no re-medidos)

- **H8**: `armar_tabla.py` llama a `ev.cargar_referencia_unificada(cons, ocr)` con el respaldo por defecto
  (`RESPALDO_20260408`), que no figura en el manifiesto. El respaldo está en git (fijo desde 068773fa8).
- **H7**: en `banco_paridad.etiquetar`, el negativo limpio exige `not ns["alerta"]`, con `ns` armado con
  alertas de CONS **y** OCR; la versión "tabla sola" de `medir_predicciones.py:46-50` sólo saca positivas.

## VERIFICADO LIMPIO

| qué | cómo | resultado |
|---|---|---|
| Pareo pasada nuestra con fila de MIROVA a ±120 s | `d1_pareo.py <B agosto> _congelado/agosto 2026-08-01 2026-08-27` | 168 de 170 alertas V375, 27 de 27 V750 y la única MODIS caen a ±120 s; ninguna entre 2 y 15 min; las 2 restantes no tienen pasada nuestra. Control: desplazando +5 min, 5 de 198 |
| Satélites mezclados (la referencia no trae satélite) | mismo script | 0 pasadas nuestras de satélites distintos a ±120 s en el mismo volcán y sensor |
| Zona horaria | epoch `timestamp` del CSV contra `Fecha_Satelite_UTC` en 11 filas de CONS, OCR, respaldo y congelados | coinciden al segundo: `Fecha_Satelite_UTC` es UTC. `Fecha_Proceso_GitHub` y `Fecha_Captura_Chile` no los usa ningún instrumento (grep en `scripts/`, `pipeline/mirova_csv_loader.py`, `_s149`, `_s146`, `_s126_lib`) |
| Contradicciones tabla contra OCR en la misma pasada | `d3_contradicciones_referencia.py 2026-03-01 2026-10-07` | 0: el OCR sólo agrega pasadas que la tabla no lista o coincide con ella. Control: una fila sintética OCR ALERTA sobre una RUTINA aparece y sale `pos` |
| Nombres de volcanes (A14) | `normalize_volcano_name` sobre los 12 nombres de los tres CSV (incluido `Peteroa` del respaldo); `_s126_lib.ALIAS` contra `latest_consolidado.csv` | todos normalizan |
| `inner_radius_km` | `index.html` (lo que usa node), `volcanoes.yaml` y `INNER` de la auditoría semanal | iguales en los 11 |
| Campos que pasa el banco al predicado | uso de campos en `mirovaEqVrp*`, `f5CoreMagnitude`, `isValidDetection`, `isSummitDetection`, `isThermalArtifact` contra `bp.CAMPOS_JS` | completos (`_mirova_confirmed` queda en falso a propósito, docstring del banco) |
| `USE_F5_CORE` del runner node | `index.html:1086` | el defecto del tablero es `true`, igual que el runner |
| Reproducibilidad de la tabla de agosto | `armar_tabla.py` + `medir_predicciones.py` sobre el run 35759688167 | idéntico a `resultados/agosto_VIIRS375.txt` en P1, P2, P4 y P5 |
| Deriva de la referencia en filas viejas | consolidado 3872fedd4 contra 1b0ca24f5 y contra HEAD | sólo cambia `Ultima_Actualizacion` (33 filas) |
| Etiqueta de la tabla para alertas fuertes | tipo por clasificación y VRP en los CSV | la tabla sólo usa "Bajo" y "Muy Bajo", pero lista alertas de hasta 7,86 MW; no es ciega a las fuertes |

## SIN VERIFICAR

- Que el job de GitHub haya aplicado los flags declarados de cada brazo (lo dejó abierto el verificador; los
  logs no los imprimen).
- La causa de que el núcleo F5 salga mayor que `pc.vrp_mw` en la mediana por noche (D-07).
- El nulo estratificado por zona para P5 (sólo lo hice para C8b).
