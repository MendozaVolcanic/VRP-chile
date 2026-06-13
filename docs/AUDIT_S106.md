# AUDIT_S106 — Auditoría integral VRP Chile (workflow multi-agente, ultracode)

> Generado por workflow `audit-integral-vrp-s106` (30 agentes, 9 ejes en paralelo +
> verificación adversarial de cada hallazgo grave). 19 confirmados (0 refutados en la
> refutación), 40 medium/low. Suite verificada post-auditoría: **705 passed, 24 skipped,
> 0 failed** (cierra el gap #1 del completeness critic). Nota: los agentes titularon el
> informe "S107"; la sesión es S106 — inmaterial.

## Resumen por eje

- **mision**: 3 verificados (high/critical), 4 medium/low
- **algoritmo**: 2 verificados (high/critical), 4 medium/low
- **codigo**: 2 verificados (high/critical), 4 medium/low
- **datos**: 1 verificados (high/critical), 7 medium/low
- **groundtruth**: 2 verificados (high/critical), 4 medium/low
- **frontend**: 2 verificados (high/critical), 5 medium/low
- **git_ops**: 2 verificados (high/critical), 4 medium/low
- **tests**: 3 verificados (high/critical), 3 medium/low
- **revision_sesion**: 2 verificados (high/critical), 5 medium/low

---

All facts confirmed. The legacy records cluster in identifiable months (Feb-Mar for Chaiten/Copahue/NdC; dispersed for Isluga and PP), and the reproc-rest run completed `success` but left these truncated — confirming it was never properly merge-promoted or was itself A64-truncated. I have everything needed for the synthesis.

---

# Auditoría integral S107 — VRP Chile (clon MIROVA)

## 1. Veredicto general

**El clon está operacionalmente sano y la entrega central de S106 (ancla espacial honesta) es metodológicamente correcta — pero arrastra una capa de deuda de posición a medio camino, dos pérdidas de recall reales contra señal MIROVA-confirmada, y una red de seguridad de red/tests con agujeros del tamaño exacto de los fallos más recientes.** Las tres cosas que importan:

1. **El ancla honesta funciona y no toca detección ni magnitud** (verificado en código y A/B: 0 diffs pareados de trig_t1) — pero su rollout quedó **incompleto en VIIRS375** (5 volcanes al 74-86%) y **sin replicar en el mapa overview ni en 2 de las 3 vistas**. El dato publicado HOY mezcla dos verdades posicionales en el mismo cráter.
2. **El peor problema de recall NO está en el ancla sino en MODIS Láscar**: 70 de 79 alertas térmicas que MIROVA SÍ publica se pierden del dashboard por el bug de `distance_class` corrupto (Salar de Atacama roba la clasificación), y el reproc F2 planeado en S94 nunca corrió. Es un falso negativo sobre señal confirmada — lo más grave en monitoreo.
3. **Las redes de seguridad tienen agujeros con la forma de los fallos recientes**: el circuit-breaker A64 cubre AUTH y DOWNLOAD pero no la BÚSQUEDA CMR (el fallo NRT del 2026-06-12 fue exactamente eso), los reproc no tienen gate de completitud (de ahí los 5 truncados), y el flag más nuevo y crítico (`enable_honest_anchor`) no está pineado por la tripwire GR2.

---

## 2. Hallazgos confirmados priorizados

### P0 — Crítico, accionar ya
*Ninguno.* Tras la verificación adversarial, ningún hallazgo alcanzó "critical": nada publica magnitudes erróneas activas ni deja ciego al operador. El ancla honesta sólo mueve posición; la magnitud (`pc.vrp_mw`) y la detección están intactas. Esto es buena noticia — el sistema no está roto, tiene deuda.

### P1 — Alto, esta sesión o la próxima

**P1.1 — MODIS Láscar pierde 70/79 alertas MIROVA-confirmadas (deuda Salar S94 nunca reprocesada)**
`pipeline/audit_metrics.py:79` (gate `distance_class!='summit' → 0`) + `Lascar.json`. El cluster está físicamente en el cráter (mediana 1.46 km, coincide con MIROVA 1.41 km) pero el pixel suelto más caliente cae en el Salar de Atacama (16-32 km) → el record queda `distance_class='far'` y se anula. El rescate F47 no dispara porque `hotspot_dist<25 km`. `per_sensor_metrics.json` regenerado hoy sigue dando recall MODIS summit 11%.
**Por qué importa**: Láscar es el único volcán donde MIROVA publica MODIS con regularidad (79/82 alertas Tier A). Perder el 89% es un FN sobre señal confirmada — el peor caso en monitoreo. **No es categoría A54** (real-pero-no-publicada): MIROVA SÍ las publica.
**Recomendación**: ejecutar el reproc histórico F2 de Láscar con el pipeline actual (nadir-fijo MODIS) para que `distance_class` derive del `primary_cluster`, no del hotspot del Salar. Es el espejo MODIS del fix de ancla honesta. Validar antes/después con `per_sensor_metrics.py`.

**P1.2 — Contradicción cross-source S94 vs S95 sobre si el bug `distance_class` cuesta recall**
`docs/AUDIT_S95_gaps_sistemicos.md:26,190,199` ("0 pérdida de recall, ninguno confirmado") vs `docs/AUDIT_S94_per_sensor_metrics.md:41,51-62` ("recall colapsa a 11.8%"). La conclusión "0 pérdida" de S95 está **metodológicamente viciada**: `experiments/_s95_audit/verify_eje5.py:132` cuenta confirmados vía `r.get('_mirova_confirmed')`, flag que sólo existe en runtime del frontend y está **vacío en disco** (0/18616 records) — el "0" estaba garantizado por construcción, no medido contra ground truth.
**Por qué importa**: dos auditorías integrales del proyecto en conflicto directo; la "0 pérdida" pudo desincentivar el fix F2 que S94 pedía. A51 obliga a consolidar.
**Recomendación**: adoptar el número de S94/este cruce como canónico (~70 Láscar MODIS). Corregir el "0 pérdida" en AUDIT_S95 y formalizarlo en MIROVA_DIVERGENCES. El discriminador es estratificar por sensor Y por volcán (sólo Láscar tiene MODIS publicado).

**P1.3 — Isluga (78/114) y Planchón-Peteroa (47/119) tienen su legacy posicional concentrado en noches MIROVA ALERTA_TERMICA**
Cruce contra `latest_consolidado.csv`. La mayoría de los records sin corregir de estos dos volcanes caen justo en las noches de actividad real publicada, con sesgo direccional sistemático (Isluga ~0.95 km al S, PP ~1.00 km, no ruido). Contraste: Chaitén 4/71, NdC 0/68, Copahue 2/82.
**Por qué importa**: es la diferencia entre "cosmético" y "divergencia real de MIROVA en las noches que importan" — el mapa muestra el hotspot corrido ~1 km del cráter justo cuando el operador lo está mirando. (Matiz verificado: para PP el offset es bimodal A22 multi-cráter, no estrictamente A69 topográfico; para Isluga el ancla sólo corrige débilmente 0.95→0.83 km. La urgencia se mantiene pero la atribución mecanística difiere.)
**Recomendación**: priorizar el reproc de relleno V375 de Isluga y PP sobre los otros 3 (ver Sección 3).

**P1.4 — La tabla NRT muestra `pc.vrp_mw` crudo mientras el resto del dashboard usa F5'-núcleo**
`frontend/index.html:2072-2077` `getDisplayVrp()` devuelve el cluster crudo sin F5'-core; chart/tarjetas/alerta usan `mirovaEqVrpDisplay` (F5'-core por default desde S97). 953 records VIIRS375 difieren >10% entre tabla y gráfico — ej. Villarrica 2026-06-13 05:42: tabla 3.91 MW vs tarjeta 0.75 MW (hasta 10.4× en el halo glaciar). El toggle Cluster/Núcleo dice que re-renderiza la tabla pero `getDisplayVrp` ignora `USE_F5_CORE`.
**Por qué importa**: el operador SERNAGEOMIN lee la magnitud en la tabla y ve un número; la tarjeta de la misma pasada muestra otro hasta 9× menor — justo en Villarrica, el volcán que F5' fue creado para curar. Rompe la coherencia del entregable.
**Recomendación**: que `getDisplayVrp` delegue en `mirovaEqVrpDisplay`. **No suprimir** el crudo (A72/A54: es señal cat-b real sobre-estimada por halo glaciar, no artefacto) — unificar o rotularlo explícitamente como "cluster crudo". Sólo afecta `index.html` (diario/mosaico no tienen tabla cruda).

**P1.5 — El mapa overview multi-volcán ignora el ancla honesta**
`frontend/index.html:3047,3082,3085` `updateHotspotLayer` filtra por `hotspot_lat!=null` y plotea el pixel suelto/eruption. 2070 records honest-source (test1_roi sin `hotspot_lat`) quedan EXCLUIDOS del overview, y 1715 se dibujan desplazados (mediana 2.89 km, máx 37.2 km en PCC). Las otras 4 superficies (tabla, tarjeta, scatter, mapa de detalle) SÍ aplican la cascada honesta.
**Por qué importa**: el overview reproduce exactamente el sesgo A69/D11 que S106 vino a corregir, dejando el rollout a medias.
**Mitigante (verificado)**: el layer es opt-in (`showHotspots=false` por default), no siempre-visible — por eso P1 y no más alto.
**Recomendación**: replicar la cascada de `index.html:2411-2419` en el overview y dejar de filtrar por `hotspot_lat!=null`.

**P1.6 — Circuit-breaker A64 no cubre el host de búsqueda CMR**
`pipeline/fetch.py:466-514` (download) tiene el breaker; `search_granules` (`:376-414`, `earthaccess.search_data`) NO. CMR está en el override de timeout mínimo (`:129`, 60 s), que durante una degradación EMPEORA el problema. El fallo NRT del run 27440204415 (2026-06-12 20:09, job Copahue) corrió exactamente 50 min con ~40 reintentos seriales de `Read timed out (cmr.earthdata.nasa.gov)` y murió — 6 volcanes igual.
**Por qué importa**: es el gemelo del incidente A64 que se creía resuelto. Bloquea la actualización NRT del dashboard hasta el siguiente cron de 2h. La red de seguridad tiene el agujero del tamaño del fallo más reciente.
**Mitigante**: `fail-fast:false` aísla volcanes, el cron recupera en 2h, no corrompe datos.
**Recomendación**: extender el breaker a `search_data` (un fallo basta para saltar las plataformas restantes, host común); distinguir ReadTimeout de CMR del transient. Emitir marker `NASA_CMR_UNREACHABLE` y extender `nrt-retry.yml:57-91` (hoy sólo reacciona a `NASA_AUTH_UNREACHABLE`).

### P2 — Deuda / riesgo

- **P2.1 — Magnitud MODIS de clusters eruption usa fondo REGIONAL (anillo 5-25 km) en vez del LOCAL adyacente de Coppola 2016a Eq.6** (`process_modis.py:824`). 134 records `pc.vrp_mw>5`, 0% MIROVA-confirmados = blob de escena tibia. **Es la raíz que GATEA el ancla MODIS** (`enable_honest_anchor_modis:false`). Ya diagnosticado y diseñado HOY (`docs/superpowers/specs/2026-06-13-magnitud-modis-fondo-local-design.md`). *Matiz verificado: NO es uniforme entre sensores (VIIRS375 ya curado por nadir, sólo 2 records; la rama Test1 ya usa fondo local) y NO es la raíz de D11 — esa es de posición, D9 es la cola de magnitud-cirrus.* Implementar Eq.6 flag-OFF + A/B (A45), NO un cap. **OJO** (`vrp_regimes.py:21`): el helper `compute_local_background` es kernel 3×3 **por-hot-pixel**, no "corona del cluster" — el fix debe promediar la corona del cluster contiguo, no reusar el per-pixel.

- **P2.2 — `enable_honest_anchor` (live en producción) no está pineado por la tripwire GR2** (`tests/test_gr2_profile_invariants.py:91-116`). El flag operacional más nuevo + los espejos OFF MODIS/V750 no están en `EXPECTED_OPERATIONAL_FLAGS`; un flip accidental cambiaría posición en producción con CI verde. *Refutado parcialmente: ctxpeak SÍ tiene tripwire en `test_test1_contextual_s99.py:102`; el gap real son sólo los 3 flags honest_anchor.* Añadir las 3 entradas.

- **P2.3 — `dist=0.0` para 2365 records test1_roi es divergencia formal del Distancia_km publicado por MIROVA, sin documentar.** MIROVA reporta Tupungatito a mediana 5.21 km, nunca 0.0 (ni siquiera Villarrica "al cráter" da 0.0 — da 0.84 km fijo). Es un trade-off legítimo (evita el sesgo topográfico) y pasó por A/B pre-registrado, pero **no está como entrada formal en MIROVA_DIVERGENCES** y el tooltip "dist=0.0 = posición=cráter por semántica" **no está en ninguna de las 3 vistas**. Documentar + completar tooltip.

- **P2.4 — Espejo MODIS del ancla honesta gateado sólo por comentario, sin test de guardia.** `enable_honest_anchor_modis:false` con aviso "NO activar sin el fix del destape" en 3 lugares (yaml, process_modis.py, profile.py) pero ningún assert programático. Un flip prematuro saltaría 89 artefactos cat-d de `far`(oculto) a `summit`(publicado). Añadir guardia estilo A63 (`test_detection_anchor.py:100`) que falle si se activa sin el fix de magnitud MODIS.

- **P2.5 — `store.py:324-333` Regla D vent-priority sobrescribe el ancla honesta sin el guard F47.** Patrón A46 textual: dos rutas pisan `final_hotspot_*`, sólo `cluster_rescue` (`:250-251`) recibió el guard. *Verificado: 0 exposure HOY y estructuralmente inalcanzable (vent-path OFF en el único perfil con honest_anchor; ningún perfil combina ambos).* Higiene defensiva — extender el guard antes de promover MODIS/V750.

- **P2.6 — Reproc sin gate de completitud + `merge_promote` con guard documentado pero no implementado.** `merge_promote_honest_anchor.py:15` documenta "GUARD anti-underfetch ... o SKIP" que el código NO implementa (computa `cov_base/cov_repro` pero sólo los imprime). Ningún `reproc-*.yml` tiene assertion. Es la causa raíz sistémica de los 5 truncados. Formalizar el audit de cobertura como step de workflow + implementar el SKIP en el script.

- **P2.7 — Cruce recall/precision es sólo TEMPORAL (±60 min), nunca espacial** (`per_sensor_metrics.py:29,175`). Viola A61 (auditar detección incluye SIEMPRE el eje espacial). El recall "crudo" (MODIS 96%, VIIRS 86-96%) sobre-estima la concordancia: un FP topográfico o un cluster Salar cuenta como TP si cae en la misma pasada. Añadir gate espacial opcional reportado lado a lado.

- **P2.8 — Test1 operacional integra MIR ABSOLUTO** (`process_viirs.py:855`, `test1_integrated.py:316`), vulnerable a A69; MODIS/V750 ni siquiera tienen la rama NTI. *Refutado como accionable: es D11, divergencia ABIERTA documentada; las 3 variantes NTI fueron refutadas por A/B (apagan el Test1 en noches reales). El costo es de posición, no de magnitud.* Mantener como divergencia abierta documentada.

- **P2.9 — `new Date(datetime_utc)` crudo en 4 funciones de conteo de `index.html`** (`:894,1416,1472,3204`) pese a `parseUtcMs` (PR #250). Corre conteos ±3-4h en Chile cerca del borde de ventanas (48h/7d/cutoff tabla). Incumple S92 L5. Migrar las 4 a `parseUtcMs`.

- **P2.10 — Bloque de arranque stale: el último es S99, la sesión es S107.** El "primer comando obligatorio" de CLAUDE.md apunta a un plan de 8 sesiones atrás. Generar `BLOQUE_ARRANQUE_S108.md` o re-apuntar el comando a MEMORY.md.

- **P2.11 — Gates intra-radio S84/S85 siguen ON pese al veredicto anti-patrón A55** (`yaml:164,183`). Decisión Nicolás S105: decidir con datos al cerrar el frente Test1/fondo-local. Ejecutar esa decisión al cerrar el frente actual.

- **P2.12 — `vrp_tir_mw` silenciado a 0 por flag provisional** (`yaml:431`, F46 abierto desde S76). Path TIR core-MIROVA (Aveni 2024) apagado por bug de magnitud no resuelto. Gate correcto, pero elevar F46 a divergencia ABIERTA explícita en MIROVA_DIVERGENCES.

- **P2.13 — La evidencia más fuerte del A/B ("0 diffs pareados de trig_t1") no está en ningún script versionado.** El audit versionado (`audit_honest_anchor.py:40`) cuenta agregado por brazo, no la intersección pareada (sensor, datetime). Las cifras del design §8 (Tupun 540, Villarrica 592...) se calcularon ad-hoc. Viola S91. El patrón de pareo ya existe en `_s98_anchor/audit_spatial.py:69` — escribir `audit_paired_trigt1.py` versionado antes de cerrar D11.

- **P2.14 — Post-nadir, VIIRS375 sub-estima sistemáticamente vs MIROVA** (Láscar 0.38×, Isluga 0.47×). El sesgo se invirtió de sobre-estimar a sub-estimar ~2× en el volcán mejor calibrado. Dentro de banda de paridad (0.5-2.0) salvo Láscar 0.38×. Vigilar; documentar si el global cae <0.5.

### P3 — Housekeeping

- **P3.1** — Tres valores de la constante de Planck C2 conviven (`constants.py:21`=14388.0, `test1_integrated.py:31`=14387.7, `vrptir.py:44`=14387.752). Impacto físico despreciable (~0.03% radiancia, ~1e-5 NTI) pero viola "constantes exactas". Centralizar en `constants.py`.
- **P3.2** — Cruft git: 97 branches remotas (52 `claude/*`), 54 tags `pre-*`, 17 workflows reproc/probe one-off + ~30 carpetas sin trackear en `experiments/_s104_roi_probe/`. Housekeeping en sesión dedicada con OK de Nicolás (A38).
- **P3.3** — `diario.html` tiene firma distinta de `mirovaEqVrp` y le falta el cap 50000 en la rama sin pc (drift S92-L5, hoy dormido). Sincronizar.
- **P3.4** — Nota de cobertura de AUDIT_S105 stale ("test1_contextual: 1 test" → hoy 8). Actualizar.

**Verificaciones de control (positivas, no accionar):**
- Los umbrales núcleo (K1=-0.8, C1=0.003/0.01, C2=5/10, Wooster 18.9/18.0/19.7, λ por sensor) coinciden EXACTAMENTE con Coppola 2016a. El gap vs MIROVA NO viene de los thresholds.
- El loader canónico MIROVA (CONS+OCR, sensor bucketing, alias, dist OCR, dedup) está SANO — el recall NO está contaminado por bug de carga.
- Los 11 JSON parsean OK, sin duplicados, sin VRP negativos/NaN, cobertura Ene29-Jun13 sin gaps >1d.
- La integración del ancla honesta es estructuralmente consistente en los 3 procesadores (sin A49 return-clobber, sin efecto en detección, sin NameError).
- Los filtros display isCirrus/isDiffuse son legítimos (artefacto path-D, nunca ocultan confirmados MIROVA).
- El guard F47/honesto de `store.py:250` funciona en datos reales.

---

## 3. Decisión sobre reprocesar los 5 volcanes truncados

**SÍ, reprocesar — pero DIRIGIDO y por etapas, no los 5 enteros. Hacerlo esta sesión o la próxima.**

**Estado verificado HOY** (no asumido): los 5 siguen truncados — Isluga 74.4%, PP 75.3%, Copahue 83.5%, Chaitén 85.7%, NdC 85.7% honesto. Crítico: **el run reproc-rest 27422803708 completó con `conclusion=success` el 2026-06-12 y aun así estos 5 quedaron sin corregir** — confirma el hallazgo P2.6 (A64 trunca con éxito aparente; el merge_promote no tiene gate de completitud).

**Por qué SÍ**: los records legacy NO son artefactos — son señal cat-b real sub-umbral (`pc.vrp_mw` máx 0.11-0.35 MW, todos summit, lava lake/fumarolas que MIROVA ve). El reproc **sólo mueve el punto en el mapa hacia el cráter**; por construcción del ancla honesta no cambia detección, recall ni magnitud (criterio duro: trig_t1 idéntico o BUG). Riesgo nulo, valor de coherencia alto. Hoy el dashboard sirve dos verdades posicionales para el mismo cráter en estos 5 volcanes.

**Costo real cuantificado** (verificado por clustering temporal):
- **Etapa 1 (prioridad alta, P1.3)**: Isluga + PP. Son los únicos con su legacy mayoritariamente en noches ALERTA. Isluga (114 records, **disperso Feb-Jun** → barrido full-range) + PP (119 records, concentrado Feb+Abr → reproc dirigido de esos chunks).
- **Etapa 2 (prioridad media)**: Chaitén (71, sólo Feb+Mar), NdC (68, sólo Ene+Feb), Copahue (82, Feb+Mar) — su legacy casi no toca noches ALERTA, así que es coherencia visual, no divergencia en noches críticas. Reproc dirigido de 2-3 meses cada uno.

**CUÁNDO y CÓMO** (no antes de cerrar P2.6): 
1. Implementar primero el gate de completitud + el SKIP del `merge_promote` (P2.6), o el reproc volverá a truncar en silencio.
2. Correr local secuencial (A47, NUNCA paralelo sobre el mismo `data_subdir`) o GH Actions con rerun host-por-host fuera del horario flaky de LANCE.
3. `merge_promote_honest_anchor.py` (sólo toca VIIRS375; MODIS/V750 byte-idénticos por flag-OFF).
4. Verificar post-reproc con un test de no-regresión: `final_hotspot_source` no debe contener `'test1'`/`'eruption'` en VIIRS375 de los 11 Tier A. Eso convierte "hay que reprocesar" en aserción de CI.

**Alternativa documentada** (no recomendada sola): dejar que el cron NRT regenere hacia adelante. Pero eso NO toca los records históricos ya publicados (Feb-Abr 2026) — y ahí está la mayoría del legacy en noches ALERTA. El NRT sólo cura la cola de junio.

---

## 4. PUNTOS CIEGOS — lo que estamos pasando por alto

Lo más valioso del informe. Cosas que asumimos correctas sin verificar:

**4.1 — La fidelidad de MAGNITUD se quedó atrás mientras toda la atención fue a la POSICIÓN.** S104-S106 invirtieron sesiones enteras en el sesgo topográfico de posición (ancla honesta, D11). Pero el fondo REGIONAL de magnitud — el anillo 5-25 km usado en la rama eruption de los 3 procesadores (`process_modis.py:824`, `process_viirs.py:1157`, `process_viirs_mod.py:823`) — diverge de la Eq.6 de Coppola ("media de los pixeles que rodean al cluster activo"). Es el mismo principio local-vs-regional que A69, sólo que en el eje de magnitud. Lo asumimos resuelto por los flags per-vol `local_kernel_bg` (S58-62), pero esos son **opt-in para 5 volcanes**; Láscar/Tupungatito/Isluga/NdC siguen con anillo regional. **Punto ciego concreto**: el fix MODIS recién diseñado (2026-06-13) propone reusar `compute_local_background`, que es **kernel por-pixel, no corona del cluster** — implementarlo tal cual sería un fix que "parece Eq.6 pero no lo es" (A48). El frente MODIS no es secundario: es el espejo de magnitud del mismo problema que ya atacamos en posición.

**4.2 — El fondo regional-vs-local NO está resuelto en NINGÚN path que use MIR/radiancia absoluta, sólo enmascarado.** El Test1 operacional (path dominante VIIRS, ~60% de las detecciones publicadas) integra MIR absoluto; MODIS y V750 ni siquiera tienen la rama NTI que cancelaría la topografía. El ancla honesta corrige la posición del record, pero el centroide interno del Test1 sigue capturando el valle tibio de baja altitud. MIROVA es inmune porque detecta por NTI contextual. **Lo damos por cerrado con la ancla, pero la ancla es un parche de presentación sobre una detección que sigue siendo MIR-absoluta.** Esto está documentado como D11 ABIERTO — el punto ciego es tratarlo como "resuelto en S106" cuando sólo se mitigó el síntoma visible.

**4.3 — "conclusion=success" en GitHub Actions NO significa "datos completos".** El run reproc-rest 27422803708 reportó éxito y dejó 5 volcanes truncados. Esto NO es un caso aislado: es un riesgo SISTÉMICO de todo reproc futuro, porque (a) el circuit-breaker A64 degrada con gracia (devuelve lo que pudo bajar), (b) ningún `reproc-*.yml` tiene gate de completitud, y (c) el `merge_promote` documenta un guard anti-underfetch que **no implementó**. Cada decisión basada en "el reproc corrió OK" sin auditar cobertura por-día es un punto ciego. El único motivo por el que S106 lo detectó fue un audit manual de cobertura pre-análisis — un proceso humano, no un gate de código.

**4.4 — El recall que reportamos nunca verificó el EJE ESPACIAL (A61), y A61 es regla vinculante.** Todo el cruce recall/precision es temporal (±60 min). Un cluster mal localizado (Salar de Atacama en Láscar, FP topográfico en nevados, PCC V750 a 13 km) cuenta como TP si cae en la misma pasada de MIROVA. El "recall crudo 96%" puede dar falsa confianza. Es exactamente el fallo que A61 nació para prevenir ("fallé 2 auditorías por saltar el eje espacial") y seguimos midiendo sin él en el script canónico.

**4.5 — Las dos auditorías integrales del proyecto se contradicen y una estaba metodológicamente rota (P1.2).** Más allá del número Láscar: el `verify_eje5.py` de S95 contó "MIROVA-confirmados" con un flag que sólo existe en runtime del frontend y está vacío en disco. El "0 pérdida de recall" no se midió, se garantizó por un bug de método. Esto importa porque **confiamos en docs de auditoría para tomar decisiones de adopción**, y al menos una tenía un número fabricado por construcción. A51 ya marca >3 contradicciones cross-source como gatillo de consolidación.

**4.6 — Las redes de seguridad cubren los fallos PASADOS, no los recientes.** El breaker A64 se construyó para AUTH (S70) y DOWNLOAD (S102) pero el fallo del 2026-06-12 fue de BÚSQUEDA CMR. El `nrt-retry` sólo reacciona a `NASA_AUTH_UNREACHABLE`. Patrón: cada incidente se parchea para su modo exacto y el siguiente entra por el hueco adyacente. La red tiene la forma de los incidentes históricos, no del espacio de fallos.

**4.7 — Asimetría cross-sensor silenciosa**: ~50% de los records de cada volcán (todo MODIS + todo VIIRS750) sigue con ancla legacy porque los espejos están flag-OFF. El mapa de un mismo volcán nevado mezcla posiciones honestas (V375) y legacy (MODIS/V750) sin marca que las distinga. Es estado intencional, pero el punto ciego es presentar la posición como uniforme entre sensores cuando no lo es.

**4.8 — Disciplina de pre-registro erosionándose (soft A66)**: el discriminador A-vs-B pre-registrado del ancla (Lastarria NW) favorecía B (46%, 3.7× sobre azar), pero se adoptó A con un criterio post-hoc ("B empeora offN en nevados"). La conclusión es probablemente correcta, pero la narrativa reescribió el resultado del test pre-registrado. El riesgo es de proceso: el pre-registro es el principal antídoto del proyecto contra el confirmation bias (A62), y cada vez que se racionaliza un resultado contrario se debilita.

---

## 5. Plan de auditoría/revisión recomendado

Lo que esta auditoría (sólo-lectura, sin Chrome/TIF) no pudo cerrar:

1. **Recall espacial (cierra 4.4, P2.7)** — Reescribir el cruce de `per_sensor_metrics.py` con gate espacial: TP sólo si `|dist_nuestro − dist_mirova| < tol` o ambos dentro del inner_radius. Reportar temporal-only y temporal+espacial lado a lado. Reusar el `Distancia_km` del loader (ya disponible). **Herramienta**: Python + el loader canónico existente.

2. **Verificación pixel-level MODIS Láscar (cierra P1.1)** — Antes del reproc F2, confirmar con Chrome MCP sobre mirovaweb + el TIF en `../mirova-tif-archive` (sibling, A62) que el cluster nuestro al cráter coincide con la radiancia local MIROVA en una muestra de las 70 noches perdidas. Esto distingue definitivamente "FN real" de "artefacto Salar coexistente". **Herramienta**: Chrome MCP + TIF archive.

3. **Script pareado de trig_t1 (cierra P2.13, 4.8)** — `audit_paired_trigt1.py` versionado que tome la intersección exacta (sensor, datetime_utc) base-vs-brazo y reporte diffs por granule, reusando el patrón de `_s98_anchor/audit_spatial.py:69`. Re-correr antes de cerrar D11 para que las cifras del design §8 sean reproducibles (S91).

4. **Preview navegador real de las 3 vistas (cierra P1.4, P1.5, P2.9, P3.3)** — Servir `/frontend/` con `BASE_PATH=/` y verificar en navegador: (a) coherencia tabla-vs-tarjeta de magnitud en Villarrica reciente, (b) overview con/sin ancla honesta, (c) conteos de ventana cerca del borde de medianoche UTC. `node --check` NO basta (S92 L5). **Herramienta**: Claude_Preview MCP o servidor local + Chrome MCP.

5. **Audit de cobertura por-día de todo reproc futuro (cierra 4.3, P2.6)** — Formalizar como step de workflow: comparar días esperados del chunk vs días con records, fallar bajo umbral. Implementar el SKIP que `merge_promote_honest_anchor.py:15` ya documenta. **Herramienta**: Python en el yml + assertion.

6. **Consolidación cross-source (cierra P1.2, 4.5, A51)** — Reconciliar S94/S95 sobre el recall MODIS, marcar D11 + el `dist=0.0` test1_roi como divergencias formales en MIROVA_DIVERGENCES, y resolver los gates intra-radio S84/S85 (P2.11). Es el frente de "consolidar antes de features nuevas" que A51 obliga con >3 contradicciones.

**Archivos clave para la próxima sesión** (rutas absolutas):
- `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/pipeline/audit_metrics.py` (gate L79, P1.1)
- `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/pipeline/fetch.py` (breaker L466-514 vs search L376-414, P1.6)
- `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/frontend/index.html` (getDisplayVrp L2072, overview L3047, P1.4/P1.5)
- `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/experiments/_s106_fase2/merge_promote_honest_anchor.py` (guard no implementado L15, P2.6)
- `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/docs/superpowers/specs/2026-06-13-magnitud-modis-fondo-local-design.md` (fix MODIS, P2.1)
- `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/docs/MIROVA_DIVERGENCES.md` (D11 abierto, formalizar dist=0.0 + F46)

---

# Apéndice — Completeness Critic

I have enough to write a sharp completeness critique. The report is genuinely thorough on the position/recall/network axes, but I've confirmed real gaps: it never enumerates its own 9 axes, the test suite (90 files) is touched only via 2 tripwire flags, and several whole subsystems are unmentioned.

---

# COMPLETENESS CRITIC — qué le falta a la auditoría S107

El informe es fuerte en posición (ancla honesta), recall MODIS y red NRT. Pero tiene huecos concretos de cobertura, autorreferencia rota, y dejó sin responder la parte literal del pedido de Nicolás ("revisar TODO el procedimiento").

## Gaps de cobertura (ejes/módulos no tocados)

1. **No enumera sus propios "9 ejes".** El informe se presenta como síntesis de 9 ejes pero nunca lista cuáles fueron, ni cuáles quedaron sin cubrir. Sin ese mapa, "revisar TODO" es inauditable: no se puede saber qué NO se miró. Es el gap meta más grave.

2. **El eje TESTS está casi sin cubrir.** Hay **90 archivos `tests/test_*.py`** y el informe solo toca 2 flags de tripwire (GR2 P2.2, guard A63 P2.4). No verificó: (a) que la suite de 705 efectivamente PASA en el estado actual (el commit de arranque dice "suite 705" pero el informe nunca corrió `pytest`); (b) si los tests nuevos de S104-S106 (`test_honest_anchor.py`, `test_test1_local_bg_nti.py`, `test_test1_nti_*.py`) cubren los caminos refutados o quedaron como zombies; (c) regla A50 — ¿algún "pre-existing fail" sin verificar contra origin/main? Cero verificación de la salud real del CI.

3. **`process_viirs_mod.py` (VIIRS750) tratado solo como espejo.** Se lo nombra en P2.1/P2.5 pero no se audita su `calculate_vrp` propia. El A/B V750 del ancla "está corriendo" — el informe nunca reporta su resultado ni lo bloquea como pendiente de cierre. Queda un brazo experimental vivo sin veredicto.

4. **Módulos enteros del pipeline sin una sola mención**: `exclusion_zones.py`, `clustering.py` / `cluster_hotspots`, `scan_geometry.py` (¡el sec³/área nadir, que es la raíz de S102-S103!), `detect_tirvolch.py`, `single_pixel_mode.py`, `path_d_cap.py` (D9 cap 270→273K, frente abierto S102). El informe habla de magnitud y posición pero no auditó el módulo de geometría de barrido del que dependen ambos.

5. **`volcanoes.yaml` no auditado.** A63 nació de una consolidación que revirtió `mirova_center` de Tupungatito. El informe no verifica que los 11 `mirova_center` / `inner_radius_km` actuales sigan correctos post-S106 — exactamente el tipo de regresión silenciosa que A63 obliga a chequear con `git log -S`.

6. **`fetch.py` NRT/Standard y `product_version`** sin tocar. El informe cubre el circuit-breaker pero no el auto-upgrade NRT→Standard de `store.py`, ni si records `nrt` viejos quedaron sin re-fetchear (impacto VRP declarado <0.1K, pero nunca verificado en los 11 JSON).

## Afirmaciones del propio informe sin verificar

7. **"0 diffs pareados de trig_t1" (la evidencia central del ancla) — el informe ADMITE que no está en script versionado (P2.13) pero igual la usa como prueba en §1, §3 y el veredicto.** Es circular: el hallazgo más load-bearing descansa en cifras ad-hoc que el propio informe marca como no reproducibles (viola S91). Debió degradar la confianza del veredicto, no afirmarlo.

8. **Números de recall (MODIS 96%, VIIRS 86-96%, Láscar 0.38×, 70/79).** El informe ya advierte (P2.7/4.4) que el cruce es solo temporal y por tanto sobre-estima. Pero entonces el "70/79 perdidas" hereda el mismo defecto: es un conteo temporal, no espacial. La cifra estrella de P1.1 está medida con el método que el mismo informe declara viciado. No se puede tener las dos cosas.

9. **"Cobertura Ene29-Jun13 sin gaps >1d" (control positivo).** Afirmado sin mostrar el método. Si el reproc trunca con `success` (4.3), un gap intra-mes podría pasar como "sin gaps" según cómo se midió. Control positivo sin evidencia citada.

## Preguntas del usuario sin responder

10. **"¿Pasamos algo por alto?" en el eje DATOS PUBLICADOS HOY.** El informe verifica posición y magnitud pero no audita si el dashboard live tiene records que NO deberían estar (artefactos cat-d colándose como summit) ni si falta algún volcán/sensor. El cruce es "qué se pierde", nunca "qué sobra y se publica".

11. **Frontend: solo se auditó `index.html`.** `diario.html` y `mosaico.html` reciben una línea cada uno (P3.3, P1.4-nota). La regla S92-L5 ("un cambio se replica en las 3") exige auditar las 3 — el ancla honesta misma podría estar inconsistente entre vistas y nadie lo verificó en `mosaico.html`.

## Recomendación: la verificación más importante que falta

**Correr la suite de tests completa (`pytest`) y reportar pass/fail real, ANTES de cualquier otra cosa.** Es el único eje que valida que el sistema descrito como "operacionalmente sano" efectivamente lo está hoy — y el informe lo omitió por completo sobre 90 archivos de test. Un veredicto "P0: ninguno" sin haber corrido el CI es una aserción sin evidencia (verification-before-completion). Si la suite pasa, refuerza el veredicto; si falla, reordena todo el ranking de prioridades. Cuesta minutos y cierra el agujero más grande del informe.

---

## Verificación post-auditoría (cierra gap del critic)

`python -m pytest tests/` → **705 passed, 24 skipped, 0 failed** (2026-06-13). El veredicto "operacionalmente sano / P0 ninguno" queda respaldado por CI verde, no solo por inspección.