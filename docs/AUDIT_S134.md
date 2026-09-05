# AUDIT S134 — el anillo, y por qué nos alejamos de MIROVA

> **Estado: CERRADA (2026-09-05).** Plan: `docs/superpowers/plans/2026-09-05-auditoria-s134-anillo-y-paridad.md`.
> Método: `GUIA_MAESTRA_AUDITORIAS.md` (workspace) + `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md`.
> Scripts, hallazgos y verificaciones por frente: `experiments/_s134_audit/f{1..5}/`
> (`F*_HALLAZGOS.md` del auditor, `VERIFICACION.md` del verificador con contexto limpio, `REGLA_C.md`).
> Guards de la regla B: `tests/test_guard_regla_c_s134.py`, `tests/test_guard_anillo_s134.py`,
> `tests/test_guard_keep_peak_s134.py`.

## Resumen ejecutivo (para quien sólo lee esto)

**La hipótesis que motivó la sesión queda refutada por tres vías independientes.** El anillo de
2,3-2,8 km de S133 no explica el déficit de magnitud contra MIROVA: en las pasadas que MIROVA
confirma, nuestro cúmulo ya está en el cráter (Villarrica 0,15 km, PCC 0,22, Tupungatito 0,23,
Chaitén 0,28, PP 0,38) y aun así integramos ~30 % menos en VIIRS 375 m; la razón ours/MIROVA es
plana en distancia al cráter (0,74 · 0,62 · 0,66 por bin; ρ = −0,105; 0 de 9 volcanes cumplen el
criterio pre-registrado). El anillo **vive en los records débiles que MIROVA no publica** (85 % de
ellos con menos de 0,1 MW) y **está en los 11 volcanes, incluido Láscar** — la tabla de S133 se
reproduce exacta, su interpretación no.

**El mecanismo tiene nombre y archivo:línea (F3, confirmado con gravedad 5 por el verificador).**
En un cono nevado el píxel más caliente en el infrarrojo medio de un disco de 3 km alrededor de la
cumbre es el borde del disco (cota más baja), no el cráter (A69). El Test 1 marca ~la mitad del disco,
el filtro contextual lo intersecta con una máscara dNTI que en esas noches está vacía, y `keep_peak`
(`process_viirs.py:1777-1786`, adopción S100) conserva sólo el `argmax(BT)`: un píxel del borde,
2,95 K **más frío que el fondo global** en el 70 % de los casos, que se publica como *summit* «a 0,0
km» (`anchor.py:89`) con una magnitud de 0,03-0,17 MW medida contra un anillo que solapa el ROI
(fondo autorreferente, S126; corona Eq. 6 apagada). Ocurre en los 11 Tier A, entre 56 y 266 records
cada uno en tres meses. La posición en el cráter está declarada como convención en el frontend; **la
magnitud no la cubre ninguna convención**. Es una TENSIÓN con A83/A84 (el mismo mecanismo devuelve
pasadas MIROVA-confirmadas en Lastarria 60 %, Tupungatito 34 %, Isluga 30 %): no se propone fix; se
propone el probe A75 en CI (S135) y la decisión es de Nicolás (§D).

**El área geolocalizada con descuento del solape del barrido deja los dos bins de cenital en banda
(0,94 / 1,01) pero NO ADOPTAR** (F4): la cola > 2 queda en 13,8 % (criterio ≤ 10 %), y el criterio
C2 que S133 había congelado y el auditor no evaluó da 1 de 8 volcanes en banda contra 3 de 8 del
control. La derivación f(θ) sale del ATBD verbatim sin parámetro ajustado y acierta dirección y
tamaño (1,360 → 1,007), lo que la deja como candidata a A/B por píxel en S135, no como adopción.

**Regla C**: 7 pendientes siguen abiertos, 5 cerrados (con guard), 0 sin verificar. **Verificación
cruzada**: 4 verificadores confirmaron los hallazgos centrales, refutaron 5 números o enunciados
(el «0,21 km» de F2 como separación 2D, tres conteos de alertas, la ventana horaria de F1 H7, la
cifra 4,9 % de F3) y aportaron 14 hallazgos propios, el mayor de ellos la pata de magnitud de
`keep_peak`. **Nada en `pipeline/` fue tocado; ningún flag cambió.**

**Eje nuevo declarado (regla A):** posición del cúmulo → magnitud publicada → paridad con
MIROVA, por sensor y régimen, con la misma pasada y la misma ancla en los dos sistemas.

**Pregunta que motiva la sesión.** S133 midió que en 9 de 11 Tier A el centroide del cúmulo
VIIRS 375 m que publicamos está a 2,3-2,8 km del cráter (`docs/s133/ANILLO_TIER_A.md`). Si
nosotros integramos calor del flanco y MIROVA integra el cráter, las dos magnitudes son de dos
objetos distintos y ninguna corrección de área o de banda cierra la brecha.

## Cómo se corrió (decisiones de infraestructura, 2026-09-05)

- **Disco al 100 %** (4,3 GB libres; un worktree completo pesa 3,2 GB). Se aplicó la salida que
  prevé A44: cinco worktrees **sparse-checkout** de 29 MB (`../VRP-Chile-s134-f{1..5}/`,
  branches `s134-f{1..5}`), sin `data/` ni `documentacion/`; los auditores leen esos
  directorios desde la raíz canónica por ruta absoluta, sólo lectura. Detalle en
  `experiments/_s134_audit/README.md`.
- **Sin granules y sin credenciales**: no hay granules VIIRS en disco y el `_netrc` local es de
  abril (A71: probar credenciales con reintentos bloqueó la cuenta en S104). F3 y F4 cambiaron
  de método: F3 traza estática + atribución sobre los píxeles persistidos (`anomaly_pixels`) y
  deja el probe A75 real diseñado para CI en S135; F4 deriva el solape del ATBD verbatim y lo
  aplica a los pares del A/B ya bajados (`~/ab_area`, 24/24; `~/ab_b22`, 4/4).
- **Orden**: F5 corrió primero; F1, F2, F3 se lanzaron sin esperar su cierre porque no consumen
  nada de F5 salvo el conteo de duplicados, que F1 hace por construcción. F4 se lanzó junto con
  ellos por la misma razón (usa pares ya bajados, no el resultado de F1).
- **Incidente de cuota**: los cuatro auditores del primer intento murieron por límite de sesión
  (HTTP 429, reinicio 13:40 Santiago) y se relanzaron a las 17:47 UTC retomando lo que dejaron.
- Suite al arrancar: **1183 passed · 3 skipped** (26 s), igual que al cierre de S133.

## 0. Regla C — los pendientes heredados (F5, Sonnet; verificado por quien orquesta)

Detalle, comandos y salidas: `experiments/_s134_audit/f5/REGLA_C.md`.

**Los tres números: confirmados abiertos 7 · ya cerrados 5 · sin poder verificar 0.**

| # | pendiente | veredicto | evidencia |
|---|---|---|---|
| P1 | gazetteer de rasgos volcánicos | **CERRADO** (S88/S89) | vive en `pipeline/volcanic_features.yaml`, no en `volcanoes.yaml` (A89: el nombre del pendiente no era el del archivo); commits `c4dcdef0b`, `8fe378e42` |
| P2 | D13 denominador de la cerca `distance_class` | **ABIERTO (documental, sin acción)** | el denominador SÍ se midió en S124 (31,0 %, 10.773/34.763) y S126 lo clasificó como decisión de no tocar; el encabezado del catálogo sigue diciendo «ABIERTA» |
| P3 | `mirova_center` por volcán×sensor | **ABIERTO** | sigue uno por volcán, extraído de un solo KMZ |
| P4 | corpus duplicado por granule | **CERRADO / medido limpio** | 0 duplicados por `(sensor, granule)` y por `(sensor, datetime_utc)` en los 11 Tier A (n≈58.335, historia completa) y en los 24 JSON de `~/ab_area` (n=12.186); instrumento con control positivo (1 duplicado inyectado, detectado). Script `f5/p4_duplicados.py` |
| P5 | `nti_max` persistido en MODIS | **CERRADO** (`59846e897`) | se persiste como `diag_nti_max` (`process_modis.py:1188` → `:1509`); 226/226 records MODIS de Villarrica desde 2026-06-01 lo tienen |
| P6 | guard del timeout de `nrt.yml` vs duración observada | **ABIERTO** | 4 tests mencionan `nrt.yml`, ninguno compara timeout con duración; `nrt.yml:69` job 80 min (comentario manual S131), pasos 50 min (`:179`, `:206`) |
| P7 | scraper OLI/MSI `NPixHot` | **ABIERTO** | 0 código; sólo comentarios en perfiles |
| P8 | instrumento del «≤ 0,17 % contra OSF» | **ABIERTO** | `tests/test_coefficients.py` sólo fija la constante (`== 18.9`); el 0,17 % se cita, no se recalcula |
| P9 | marcador «extensión» para PCC | **CERRADO como mecanismo, NO-OP medido** | `geo_class == "extension"` existe (`frontend/index.html:2828`, naranja) y PCC tiene entrada en `volcanic_features.yaml`, pero **0 de 5.340** records de PCC lo activan. La decisión volcanológica sigue siendo de Nicolás (§5) |
| P10 | `diag_d9_capped` persistido | **CERRADO** | `primary_cluster["d9_capped"]`, activo en `mirova_equivalent.yaml:463-464`; 269/5.340 records de PCC |
| P11 | chunks 2 y 3 del A/B del área | **ABIERTO como dato; CERRADO POR DECISIÓN** | ⚠️ F5 lo declaró «cerrado, corrió completo»; la verificación cruzada lo refutó: «chunk» es ventana temporal (`reproc-s133-area-ab.yml:108-119`, inputs `start/end`, `overwrite` «true en el PRIMER chunk») y los 24 JSON del run `33912398561` cubren exactamente 2026-04-01 → 05-31. Los chunks 2/3 no corrieron y **no se corren**: el veredicto NO ADOPTAR no cambia con más datos (`docs/s133/AB_AREA_VEREDICTO_CHUNK1.md`) |
| P12 | B22 con ventana ancha | **ABIERTO** | 1 solo run (`33872821788`), 2 volcanes, n=2 pares; decisión de Nicolás (§5) |

**Lección de instrumento registrada**: F5 leyó «24/24 verdes» como «universo completo» sin mirar
la ventana de los datos (A90: conteo sin ventana). La corrección salió de la verificación cruzada,
no del auditor — es la razón de que el que verifica no sea el que encontró.

Guards propuestos para los cerrados (regla B): ver `f5/REGLA_C.md` §Guards. Se escriben al
cierre (§3) para los que entren como CONFIRMADO.

## 1. F1 · Posición → magnitud → paridad por pasada (Fable) — verificado §5.1

Informe y script: `experiments/_s134_audit/f1/F1_HALLAZGOS.md`, `f1_posicion_magnitud_paridad.py`
(salidas `resultados.json`, `resultados_ancla_catalogo.json`). Ventana 2026-04-01 → 2026-08-31
(última alerta del snapshot); 18.373 records nuestros, 1.371 ALERTAS MIROVA, **1.161 pares por
pasada** (V375 992 · V750 164 · MODIS 5), 124 FN, 86 sin pasada nuestra, 3.889 nuestros sin MIROVA.

**Criterio pre-registrado: NO CUMPLE — la posición del cúmulo no explica la paridad.** La razón
ours/MIROVA en VIIRS 375 m es plana en distancia al cráter: 0,744 (≤0,5 km, n=559) · 0,621
(0,5-1,5; n=294) · 0,659 (1,5-3; n=132); Spearman ρ = −0,105. De los 9 volcanes con anillo, 3 son
evaluables y 0 cumplen; en los otros 6 los pares caen casi todos en un solo bin.

**El fenómeno que reordena la lectura de S133.** En las pasadas que MIROVA confirma, nuestro cúmulo
**ya está en el cráter** (Villarrica 0,15 km · PCC 0,22 · Tupungatito 0,23 · Chaitén 0,28 · PP 0,38;
77-100 % a ≤0,5 km). El anillo de 2,3-2,8 km vive casi entero en las 2.152 pasadas I-band «summit»
que publicamos y MIROVA no, repartido en los cuatro cuadrantes (Villarrica, Copahue, Llaima: todo el
contorno, no un flanco). Es la firma de A69: cuando no hay fuente puntual fuerte, el MIR absoluto
sigue la frontera nieve-roca. Los números de `ANILLO_TIER_A.md` se reproducen exactos (Láscar
0,22 km · 79,8 % · n=208); su interpretación —«integramos otro objeto que MIROVA»— no. Del mismo
objeto sacamos menos.

**De qué SÍ depende la razón** (V375, n=992): del número de píxeles que retenemos (1 píxel: 532
pares, 0,670 · ≥10 píxeles: 47, 1,162; V750 0,536 → 1,584) y del cenital (0,809 <20° → 0,605
≥40°). El déficit se concentra en los focos fuertes y aislados sobre roca seca: Láscar 0,529
[0,495-0,577], Lastarria 0,506, Isluga 0,611; los nevados con pares suficientes (PP 0,976, PCC
1,031, Villarrica 0,897) están en banda; Chaitén sobre-estima 1,353. Láscar deja de ser un
contraejemplo: cúmulo en el cráter (99 %), un píxel, razón 0,53.

| hallazgo | confianza del auditor | gravedad |
|---|---|---|
| H1 hipótesis refutada; déficit ~0,70 uniforme en posición | CONFIRMADO | 3 |
| H2 el anillo vive en lo que MIROVA no publica; el eje espacial separa confirmado de no confirmado (A83) | CONFIRMADO (la clase real/artefacto de esos 2.152 NO está medida) | 3 |
| H3 el déficit escala con los píxeles retenidos; mecanismo «MIROVA suma más píxeles del mismo cúmulo» | correlación CONFIRMADA · mecanismo SOSPECHA | 3 |
| H4 gradiente cenital persiste tras nadir-fijo (0,81 → 0,61) | CONFIRMADO | 2 |
| H5 MODIS: 43 de 48 pasadas confirmadas quedan `far` con `pc.vrp_mw>0`, cúmulo a 1,56 km; con `summit ∪ far` paridad 0,91 y 0 FN | CONFIRMADO (A46/A82 cuantificado) | 2 |
| H6 Isluga: foco fijo 0,86 km al SW del `vent_*` en el 100 % de los pares; huele a coordenada de cráter, no a anillo | patrón CONFIRMADO · interpretación SOSPECHA | 2 |
| H7 los 59 «MIROVA sin pasada nuestra» de Láscar/Lastarria son ALERTAS OCR diurnas (17-18 UTC): correctas por night-only (A76); un recall CONS∪OCR sin filtro día/noche las cobra como FN | dato CONFIRMADO | 1 |
| H8 M-band multi-píxel sobre-estima (1,59; Isluga 2,26) | CONFIRMADO, n chico | 1 |
| H9 dos FN V375 sin cúmulo con MIROVA 0,60 y 2,15 MW | conteo CONFIRMADO | 1 |

Controles: línea base roja mueve exactamente los 5 volcanes con vent ≠ catálogo (Villarrica 3,03 →
2,80 km) y deja quietos los 6 con vent = catálogo; pareo Láscar 93 %; ±20 y ±60 min dan los mismos
tres conjuntos; 0 duplicados; 0 fallbacks de `f5_core` en los pares; `pc.centroid_dist_km` del
pipeline = haversine desde `vent_*` en los 11.

## 2. F2 · Dónde pone MIROVA su cúmulo, misma pasada (Opus) — verificado §5.2

Informe y scripts: `experiments/_s134_audit/f2/F2_HALLAZGOS.md`, `00_`…`09_*.py`, `f2_*.py`
(salidas `resultados.json` 223 filas, `control_instrumento.json`, `control_condicionamiento.json`,
`cola_validacion.json`). Ventana 2026-06-01 → 2026-09-05, ALERTAS MIROVA VIIRS375 con TIF a ≤120 s
y record nuestro de la misma pasada: **n = 223** en 10 de 11 Tier A (Llaima: 0 alertas). 271 TIF
(39 MB) bajados por URL raw del `index.csv`, en `experiments/_s134_audit/tif/` (gitignored).

**Control de instrumento: PASA, acotado.** En Láscar el máximo del GeoTIFF **restringido al inner
(5 km)** cae a < 1 km del cráter en 5 de 5 (0,128-0,273 km); sin restringir, 0 de 5 (23 km, el salar):
reproduce a S131 en su propio terreno. Control negativo de clase: en pasadas RUTINA el máximo está a
4,78 km y 9 % a < 1 km, contra 82 % en ALERTA (PP: 8 % vs 80 %) — el TIF ve la anomalía, no la
topografía. **S131 no queda refutado, queda acotado**: donde el inner es grande o el terreno nevado
(PCC 16,5 km, Tupungatito 6,7, Villarrica 4,71) el máximo vuelve a ser el artefacto A69. Por eso el
veredicto no se apoya en el TIF sino en el auto-reporte de MIROVA. Georreferencia verificada: EPSG:4326,
celda 0,375 km, extensión 50,3 km (confirma `half_km = 25,5`).

**Respuesta al frente (tal como quedó tras la verificación cruzada, §5.2): no se puede afirmar que
MIROVA ponga su cúmulo en otro lugar que nosotros, y el «se corre» de S133 era el ancla.** MIROVA mide
su `Distancia_km` desde el centro de SU grilla, que está a 7,57 km del cráter en PCC y 4,86 en
Tupungatito; comparar su número con el nuestro desde el vent es comparar dos reglas con cero
distinto (S115, A13, D15). Re-anclando nuestro centroide a ese centro, los dos radios coinciden a
0,21 km mediano (n=220) — **pero el CSV de MIROVA trae un radio sin acimut**, así que la diferencia
de radios es una cota inferior de la separación, no la separación (cota superior: PCC 15,6 km,
Tupungatito 10,2). Donde el TIF sí arbitra la posición 2D (inner chico, terreno seco) la separación
verdadera es **Láscar 0,24 km y PP 0,14 km**. El auditor retractó un resultado intermedio propio
(«MIROVA más lejos en el 77 %») que era el offset del ancla, y esa retractación sí se sostiene.

**El anillo de S133 es un efecto del denominador (A90).** La réplica de la tabla de S133 da error 0,00 km
en los 11; condicionando en pasadas con ALERTA los nevados pasan de 2,27-2,79 km a **0,18-0,36 km**
(desplazamiento mediano −1,63 km, n=10 volcanes), y los tres que S133 dio por genuinos no se mueven
(Láscar −0,07, Isluga −0,11, Lastarria −0,08). Converge con F1 §1 por otra vía (TIF + CSV vs sólo CSV).

| hallazgo | confianza | gravedad |
|---|---|---|
| H1 el anillo es del denominador: vive en las pasadas sin alerta MIROVA | CONFIRMADO (verificador: **más fuerte** recomputado sin exigir TIF, n mayor) | 3 |
| H2 MIROVA y nosotros: mismo lugar (0,21 km); el «se corre» era el ancla | **REFUTADO como estaba enunciado** (radio sin acimut); sobrevive el mecanismo del ancla y la separación 2D en Láscar/PP | 4 → 2 |
| H3 `index.csv` del archivo TIF: dos relojes discrepan > 60 s en el 14,2 %, `acquisition_utc` vacío 17,6 %; a ±20 min el 27 % de los pares serían del otro satélite | CONFIRMADO exacto | 2 |
| H4 `anomaly_pixels` (mediana 1) ≠ `n_anomalous_pixels` (mediana 2) | desajuste CONFIRMADO · causa «recorte» **REFUTADA**: en 4.465 records el 35,6 % tiene `len > n` (incluso `n=0` con 1 píxel). Son dos máscaras: `n_anomalous_pixels` sale de los Tests 2/3 (`process_viirs.py:1368`) y el camino del Test 1 sobrescribe `anomaly_pixels` con `build_anomaly_pixels(t1_vrp_2d)` filtrando `vrp>0` (`:1889`). Coincide con F3 §4 | 2 |
| H5 Llaima 0 ALERTAS V375 en 3 meses vs 277 records nuestros | Llaima CONFIRMADO; **los otros tres conteos REFUTADOS**: Villarrica 15 (no 3), NdC 8 (no 1), Copahue 3 (no 1), Isluga 133 (no 51) — el informe presentó pares TIF+record como si fueran ALERTAS | 3 |

## 3. F3 · El mecanismo que corre el cúmulo al flanco (Fable) — verificado §5.3

Informe y scripts: `experiments/_s134_audit/f3/F3_HALLAZGOS.md`, `atribucion_pixeles.py`,
`anillo_por_source.py`, `tabla_6_pasadas.py`, `cruce_mirova_por_clase.py`, `probe_etapas_ci.md`
(diseño del probe A75 para CI, S135). Ventana: records VIIRS375 `summit` desde 2026-06-01. Sin
granules (A71): traza estática + atribución sobre los píxeles persistidos.

**El fenómeno.** En un cono nevado la temperatura MIR nocturna sigue la altitud: el píxel más caliente
de un disco de 3 km centrado en la cumbre es el borde del disco (cota más baja), no el cráter (A69).

**El mecanismo, con archivo:línea.** El Test 1 integra el exceso sobre la **mediana** del anillo 1-3 km
(`test1_integrated.py:376,412,420`), así que por construcción marca ~la mitad del disco (mediana 67
píxeles). El filtro contextual (`process_viirs.py:1775-1786`, flags efectivos
`ENABLE_TEST1_CONTEXTUAL_FILTER=True` y `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK=True`, adopción S100 #340)
lo intersecta con `dNTI_ctx`, que en estas noches está vacío (174/245 en Villarrica), y `keep_peak`
conserva sólo `argmax(BT)`: **un píxel, el más caliente en MIR del disco**, que es el borde. Ese píxel
es el `primary_cluster`, su ΔL la magnitud, y el ancla honesta (`anchor.py:89`) lo rotula
`test1_roi` **en el vent a 0,0 km**. La suposición del docstring D10 «pico = cráter» es falsa en
los nevados de señal débil.

**La firma en los datos (Villarrica, n=289 summit publicados):** 245 son `test1_roi`, 243 con exactamente
1 píxel, mediana 2,80 km, 200 de 247 píxeles en la corona 2,5-3,0 km, rumbo repartido en los 8 octantes
(es el borde del disco, no un valle), y **BT menor que `t_bg_k` en 172/245**. MIROVA publicó esas
pasadas en el 4,9 % según el auditor — **el verificador obtuvo 11,5 %** (27/235, ±90 min, CONS∪OCR); la
dirección aguanta, la cifra no (Llaima 1,8 %, Copahue 2,3 %, Chaitén 2,7 %, PCC 3,4 %, NdC 7,8 % son del auditor). Control
positivo: los `ctx_cluster` con primer pase de Láscar → 0,17 km, 82,8 % con alerta MIROVA (n=128).

**Corrección a S133:** el anillo está en los **11**, incluido Láscar (sus 60 `test1_roi` caen a 2,48 km);
la diferencia Láscar 0,22 vs Villarrica 2,79 es la **mezcla de fuentes** (Láscar 149 contextuales en el
cráter contra 60 Test 1; Villarrica 44 contra 245), no que el mecanismo respete a Láscar.

Candidatas del brief: (a) selección de otro cúmulo — no, llega un solo píxel a `cluster_hotspots`;
(b) cúmulo grande con cola — no, `pc.n_pixels==1`; (c) recaptura del second pass — sí, secundaria (H2);
(d) centroide no ponderado — cierto (`clustering.py:102-103`) pero irrelevante (≤0,1 km).

| hallazgo | confianza | gravedad |
|---|---|---|
| H1 `keep_peak` publica como «summit a 0,0 km» un píxel del borde del ROI más frío que el fondo, en los 11 Tier A, casi todas las noches. **TENSIÓN con A83/A84, no fix**: el mismo mecanismo devuelve pasadas MIROVA-confirmadas en Lastarria (60 %), Tupungatito (34 %), Isluga (30 %) | CONFIRMADO | 4 |
| H2 `second_pass_adjacent` (`detection_context.py:876`) corre con máscara activa vacía y sin la compuerta `bt > t_bg + 3 K` del first pass (`:517-522`): segunda detección más permisiva, no recaptura. 424 records en los 11 (verificador: 438; Chaitén 89 exacto), 404 fallan esa compuerta; el «175 más fríos que el fondo» **no reproduce** (0 con `t_max_i04_k`; falta medirlo con el `bt_k` del píxel); 3,2-3,9 km; MIROVA 0 % en Villarrica/Llaima/Copahue | CONFIRMADO | 3 |
| H3 un record, dos objetos: con `ENABLE_TEST1_PRIORITY_WEAK_CLUSTER` el `primary_cluster` es el pico del Test 1 (`:1926`) y la posición es el snapshot contextual (`:1521`, `anchor.py:82`): `pc ≠ final` en 19/44 Villarrica, 23/52 Llaima, 14/22 Tupungatito. S133 midió el objeto que no se dibuja (familia A46/A81) | CONFIRMADO | 3 |
| H4 `anomaly_pixels[].dist_km`, `hotspot_dist_km`, `diag_t_max_dist_km` miden desde el catálogo (`process_viirs.py:723`): 0,85 km de sesgo en Villarrica | CONFIRMADO | 2 |
| H5 centroide geométrico, no ponderado | CONFIRMADO, cosmético | 1 |
| H6 comentario `mirova_equivalent.yaml:375` «[2,4] km» vs efectivo (1.5, 3.0) | **REFUTADO como defecto** por el verificador: la l. 379 del mismo bloque declara «Ring [1.5,3]»; es redacción | 1 |

**Cómo se ve en el dashboard:** punto rojo *summit* sobre el cráter, «0,0 km», 0,03-0,17 MW «Muy Bajo»
casi todas las noches — **en los 11 Tier A, no en 6** (verificador: 56-266 records `test1_roi` por volcán en 3
meses); el píxel real a 2,8 km sólo bajo «Todos los pixels». Fabrica un nivel base falso que hace
indistinguible un inicio real de 0,1 MW en el cráter.

**Lo que sólo el probe en CI puede medir:** el footprint del Test 1 (67 px) no se persiste; sin él no se
sabe si el cráter estaba dentro de `mask_contributing` antes de que `keep_peak` lo descartara.

## 4. F4 · El solape del barrido (Opus) — verificado §5.4

Informe y scripts: `experiments/_s134_audit/f4/F4_HALLAZGOS.md`, `f4_solape_ley_intermedia.py`,
`f4_cola_composicion.py` (salidas `resultados.json`, `cola_composicion.json`). Sustrato: los 24 JSON
del A/B de S133 (`~/ab_area`, 8 volcanes × 3 brazos, 2026-04-01 → 05-31, **643 pares** V375).

**El fenómeno.** La franja de un barrido VIIRS mide 11,87 km a lo largo del vuelo en el nadir y
25,60 km en el borde, pero el satélite avanza siempre 11,87 km entre barridos: hacia el borde cada
barrido vuelve a mirar terreno que el anterior ya miró (*bow-tie*, «maximum overlap over 50 percent
at 56.063 degrees»). Un foco cerca del borde aparece en píxeles de dos barridos y el área
geolocalizada completa lo cuenta dos veces. El instrumento ya borra a bordo 4 y 8 de las 32 filas en
las zonas media y externa, así que el solape residual es menor que el geométrico.

**f(θ) = min(1, 32/(k·r))** derivada sólo de cuatro números del ATBD verbatim (Geolocation ATBD 2014
Tabla 2.2-1 p.13 y §3.4.2.1 p.95; Imagery ATBD RevE §3.2.4 p.22-23), sin parámetro ajustado: 1,000 en
el nadir, 0,618 en el borde, con dos saltos hacia arriba en las fronteras de zona (curva serrucho).

| ley | nadir 0-15° (n=111) | borde ≥50° (n=210) | cola > 2 |
|---|---:|---:|---:|
| control (área nadir fija, lo actual) | 0,879 [0,836-0,953] | 0,619 [0,540-0,762] | 4,2 % |
| geoloc (brazo S133) | 0,958 [0,881-1,025] | 1,360 [1,170-1,508] | 20,1 % |
| **geoloc × f(θ)** | **0,940** [0,878-1,019] | **1,007** [0,891-1,187] | 13,8 % |

**Veredicto contra el criterio pre-registrado (el de S132, congelado antes de correr): C1 bins en
0,90-1,10 PASA; C4 cola ≤ 10 % NO PASA → NO ADOPTAR.** Controles: el positivo reproduce los 7 números
de S133 exactos a 3 decimales; el negativo mueve el nadir 1,88 % (< 3 %); la altura orbital no importa
(1,007 vs 1,010).

| hallazgo | confianza | gravedad |
|---|---|---|
| H1 la cola > 2 no es el gradiente cenital: 17,1 % en los 514 pares con MIROVA < 0,5 MW, 0,8 % en 0,5-2 MW, 0 % en 2-10 MW; Chaitén 33 % y PCC 28 %. C4 mide el régimen sub-MW, no la ley de área | CONFIRMADO | 2 |
| H2 pozo 0,786 en 35-50° por los saltos del borrado bow-tie | CONFIRMADO | 2 |
| H3 el mecanismo acertó dirección y tamaño sin parámetros libres (1,360 → 1,007) | número CONFIRMADO · causalidad SOSPECHA (exige A/B por píxel con reproceso real, A18) | 3 |
| H4 el área por píxel del brazo geoloc no se persiste (A7/A46) | CONFIRMADO | 1 |

Declarado no verificable sin granules: f aplicada por píxel dentro del pipeline vs factor por
record; la tensión del «~19°» del ATBD §2.2.2 con una f que descuenta desde θ > 0.

## 5. Verificación cruzada (contexto limpio, Opus; el que verifica no es el que encontró)

Cada verificador recibió sólo títulos, rutas y scripts; releyó, volvió a correr y enumeró los caminos
por los que cada afirmación podría estar mal. Informes: `experiments/_s134_audit/f{1..4}/VERIFICACION.md`
(scripts `verif_*.py`). Lo que el verificador no confirma baja a SOSPECHA/PLAUSIBLE.

### 5.1 F1 (verificador reprodujo el script sin tocarlo: los 8 controles y la cabecera, al decimal)

| hallazgo | veredicto del verificador | gravedad final | lo que agregó |
|---|---|---|---|
| H1 criterio NO CUMPLE | **CONFIRMADO** | 3 | control anti-Simpson: ρ dentro de cada volcán con signos mezclados (Láscar −0,34, Tupungatito +0,18, PCC +0,09); el agregado no esconde un efecto |
| H2 el anillo vive en lo no publicado | **CONFIRMADO** descriptivo · **PLAUSIBLE** causal | 3 | estratificado por magnitud: en ≥0,3 MW pares y no-pares son idénticos (0,16 vs 0,16 km) y el 85 % del «sin MIROVA» es <0,1 MW — confirmación de MIROVA y señal débil son casi el mismo eje. Pero dentro del mismo volcán y la misma magnitud el hueco persiste (Villarrica 0,16 vs 2,80, n=261): no es sólo selección. **Léase «el anillo vive en los records débiles»** |
| H3 déficit vs nº de píxeles | **PLAUSIBLE con reserva fuerte** | 3 | la covariable es `anomaly_pixels` de la ESCENA; `pc.n_pixels` queda en 1-2 en los cuatro bins, así que no mide «píxeles retenidos». MIROVA también sube con n_px (ρ +0,36); nosotros más rápido (ρ +0,56). La corroboración M-band es OTRO mecanismo (H8: ahí MIROVA baja). El mecanismo «MIROVA suma más píxeles del cúmulo» queda sin sostén en el dato; F3 §3 H1 ofrece el mecanismo real (un solo píxel por `keep_peak`) |
| H4 gradiente cenital | **CONFIRMADO con matiz** | 2 | nítido en Láscar (0,71→0,42), Isluga, Tupungatito; ausente o invertido en PCC, PP, Chaitén. El agregado lo exagera por composición |
| H5 MODIS 43 `far` | **CONFIRMADO exacto** | 2 | — |
| H6 Isluga | patrón CONFIRMADO · interpretación **PLAUSIBLE FUERTE** | **3** (sube) | **Isluga es el único Tier A con `vent_*` a 2 decimales** (−19,15 / −68,83): ±0,55 km sólo por cuantización, el orden del offset. Su `mirova_center` (5 decimales) está 0,37 km al SW, la misma dirección; nuestro centroide queda a 0,48 km de esa referencia y a 0,83 del vent. Falta el cráter real (imagen/DEM) |
| H7 OCR diurnas | sustancia CONFIRMADA · **un número REFUTADO** | 1 | el rango real es 17:18-19:00 UTC, no «17:24-18:24»: 14 de 59 caen fuera de la ventana declarada; el record nuestro más cercano está a 6,4 h, no >10 h. La conclusión (diurnas, correcto perderlas) no cambia; los números transcritos no los respaldaba su propia salida (A90) |
| H8 M-band multi-píxel | **CONFIRMADO** | **2** (sube) | es el mecanismo que explica el tramo M-band que H3 se atribuía |
| H9 dos FN sin cúmulo | **CONFIRMADO exacto** | 1 | — |

Hallazgos propios del verificador: **P1** el script mide 607 alertas ambiguas (44 %, ≥2 granules a
±20 min) y el informe no lo dice mientras certifica «pareo robusto»; impacto acotado (el elegido es
siempre |dt|=0; 136 de 2.152 «sin MIROVA» son hermanos no elegidos, 6,3 %). **P2** la covariable de H3.
**P3** la coordenada de Isluga. **P4** la ventana horaria de H7. Fue a buscar una divergencia en la
réplica de la regla del operador (`distance_class` falsy, fallback sin `primary_cluster`) y **no
existe sobre esta data** (0 y 0 records).

### 5.2 F2 (verificador reprodujo los 4 scripts principales cifra por cifra; 0 TIF nuevos)

| hallazgo | veredicto | gravedad final | lo que agregó |
|---|---|---|---|
| control de instrumento acotado | **PLAUSIBLE** | 2 | restringir al inner es legítimo como enunciado condicional: el control ALERTA-vs-RUTINA (82 % vs 9 %) no se fabrica eligiendo el disco. Pero hay un salto de objeto: el máximo del TIF NO es el cúmulo que MIROVA declara — como estimador de su `Distancia_km` da error mediano 0,88 km y le gana al nulo trivial en sólo 61 % de 223 pasadas (11,15 km en PCC). S131 acotado, no refutado |
| H2 «separación 0,21 km» | **REFUTADO como está enunciado** | 4 → 2 | el CSV de MIROVA no tiene lat/lon: es un radio sin acimut; `08_reanclar.py` compara dos radios desde el mismo centro. Cota superior real de la separación: PCC 15,62 km, Tupungatito 10,15. Sobrevive la retractación del 77 % y la separación 2D donde el TIF arbitra: Láscar 0,24 km, PP 0,14. S131 §4 ya había hecho el re-ancla sobre 1.815 pasadas (A50: la respuesta estaba en el repo) |
| H1 anillo = denominador | **CONFIRMADO y más fuerte** | 3 | `06_` exigía TIF y tiraba el 61 % de las alertas; recomputado sin TIF: Villarrica 0,13 km (n=11), Tupungatito 0,21 (n=50), PP 0,40 (n=43), desplazamiento −1,43 km; Copahue se invierte (2,90, n=3). **El sesgo de selección cambia la lectura**: estratificando los records sin alerta por magnitud propia, en Láscar y PCC la intensidad ya explica el anillo, pero en Villarrica, Copahue y Llaima **el decil alto sigue a 2,8 km** — no hay variable interna que reproduzca el corte (A83). Redacción propuesta: *el anillo vive en la población no confirmada y no es marcable con nuestros datos* |
| H5 conteos de alertas | Llaima CONFIRMADO · **otros tres REFUTADOS** | 3 | Villarrica 15, NdC 8, Copahue 3, Isluga 133 |
| H3 dos relojes | **CONFIRMADO** | 2 | 17,6 % y 14,2 % exactos |
| H4 `anomaly_pixels` | desajuste CONFIRMADO · causa REFUTADA | 2 | dos máscaras, no recorte (ver §2) |

Hallazgos propios del verificador: **P0** los 271 TIF estaban sólo en el worktree, no en el árbol
canónico (copiados a `experiments/_s134_audit/tif/` de la raíz al cierre; gitignored). **P1** la fila
F2-6 de la cola de campo arrastra el «86 % de Isluga» del bloque retractado; re-anclado es 18 %, y el
volcán donde MIROVA queda sistemáticamente más cerca es **PP (95 %)**. **P2** el semiancho 36,08 km del
informe se midió desde el cráter, no desde el raster; el raster real es 51,11 × 51,29 km (semiancho
25,55): confirma `half_km=25,5`, pero las cifras de celda/extensión del informe no reproducen.

### 5.3 F3 (verificador releyó la rama con archivo:línea y reprodujo los conteos con scripts propios)

| hallazgo | veredicto | gravedad final | lo que agregó |
|---|---|---|---|
| H1 `keep_peak` publica el borde del disco como summit a 0,0 km | **CONFIRMADO** | **5** (sube de 4) | los 5 flags efectivos ON (`ENABLE_TEST1_CONTEXTUAL_FILTER`, `..._KEEP_PEAK`, `ENABLE_TEST1_PRIORITY_WEAK_CLUSTER`, `ENABLE_HONEST_ANCHOR`, modo `vent`); `TEST1_ROI_KM = 3.0`; el argmax sobre la máscara ES el argmax del disco (`mask_contributing = excess_roi > 0`). Reproduce 245/289, 100 % de 1 píxel, 2,80 km, 198/245 en [2,5-3,0], `final_hotspot_dist_km = 0,0` en 245/245. «Más frío que el fondo» es válido con el par correcto (`bt_k` del cúmulo vs `t_bg_k`): 172/245, mediana **−2,95 K**. Enumeró 5 lecturas alternativas; 4 caen (81 % apilado en la corona contra ~30 % por área; 100 % de 1 píxel prueba intersección vacía; el anillo sigue al path, no al cerro: `ctx_cluster` 12/44 en la corona). **La única que sobrevive es «posición = semántica deliberada de integral-de-ROI»** (`frontend/index.html:2779-2784` lo declara) **y no cubre la magnitud**: `pc.vrp_mw` mide ese píxel del flanco contra el anillo [1,3] km que solapa el ROI (fondo autorreferente S126), con la corona Eq. 6 (`sp426_5.txt:355-358`) apagada: `ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375 = False`. Publicamos 0,011-0,618 MW (mediana 0,046) como exceso de roca desnuda del flanco sobre su propio anillo de nieve |
| corrección al brief: anillo en los 11 | **CONFIRMADO** | — | `test1_roi` al vent: Villarrica 2,80 · Copahue 2,80 · Llaima 2,84 · Isluga 2,76 · NdC 2,69 · **Láscar 2,63** · Chaitén 2,60 · PP 2,59 · Lastarria 2,46 · PCC 2,45 · Tupungatito 2,26; Láscar 138 `test1_roi` / 152 `ctx_cluster`, Villarrica 245 / 44; `ctx_cluster` de Láscar 0,18 km (n=152) |
| H2 second pass sin compuerta BT | **CONFIRMADO y peor** | 3 | la compuerta falta en `detection_context.py:877-879`; el call site del path ETI sí la reaplica (`process_viirs.py:1171-1172`), el principal (`:1277`) no; los dos filtros que lo taparían (`ENABLE_FINAL_PIXEL_FILTER`, gate intra-radio) están False. **No es el diseño de Coppola**: `sp426_5.txt:329-341` condiciona el second run a un conjunto activo no vacío Y a los píxeles adyacentes; el nuestro corre con máscara vacía en **2.295/3.164** records summit V375 y sin restricción de vecindad. 438 records `first_pass==0 & recapture>0` (auditor 424); «175 más fríos» no reproduce |
| H3 dos objetos en un record | **CONFIRMADO exacto** | 3 | el dashboard dibuja `final_hotspot` (`index.html:2787-2790`), no `pc.centroid` (sólo recorta F5' en `:1140`) |
| H4 distancias desde el catálogo | **CONFIRMADO, medido** | 2 | `anomaly_pixels[].dist_km` error 0,0027 km contra catálogo vs 0,694 contra vent; `hotspot_dist_km` ídem; la detección (dual-ROI) usa `vent_dist_per_pixel` (`:729`): **cuatro orígenes en un record** |
| H6 comentario YAML | **REFUTADO como defecto** | 1 | la l. 379 documenta su propio override |
| punto 7 dashboard | **CONFIRMADO** | 4 | son **11 volcanes**, no 6 |

Hallazgos propios del verificador: **P1 (3)** el popup muestra `bt_k: r.t_max_k ?? r.t_max_i04_k`
(`index.html:2789`), el máximo del ROI de 25 km — un TERCER píxel: punto en el cráter (0,0 km),
temperatura de un píxel que puede estar a 25 km (+9,76 K sobre el fondo) y magnitud de uno a 2,8 km
que está 2,95 K bajo el fondo. **P2 (3)** el second run sin conjunto activo ni adyacencia (arriba).
**P3 (método)** el control cruzado Láscar 82,8 % vs Villarrica 4,9 % está confundido por cuánto
publica MIROVA de cada volcán (118 vs 15 alertas); el control válido es dentro del volcán y aguanta en
10/11 (`ctx_cluster` corrobora más que `test1_roi`: Láscar 97,1 vs 47,8 %; PCC 55,6 vs 16,1; PP 73,1
vs 32,0; Villarrica 32,4 vs 11,5; única inversión Tupungatito, n=9). **P4** dos cifras no reproducen
(4,9 % → 11,5 %; «175 más fríos» → 0). **P5 (4)** la pata de magnitud no estaba enunciada y es lo
único que la defensa «semántica deliberada» no cubre.

### 5.5 Balance de la verificación cruzada

| | F1 | F2 | F3 | F4 |
|---|---|---|---|---|
| hallazgos del auditor | 9 | 5 | 6 | 4 (+veredicto) |
| confirmados | 7 | 3 | 5 | 4 |
| rebajados a plausible | 1 (H3) | 1 (instrumento) | 0 | 1 (H1) |
| refutados (enunciado o número) | 1 número (H7) | 1 (H2 «0,21 km») + 3 conteos | 1 (H6) + 2 cifras | veredicto parcial (C2 omitido) |
| propios del verificador | 4 | 3 | 5 | 7 |

Patrón de los errores refutados, para el registro de método: **cuatro de los cinco son de
instrumento, no de dato** — un radio comparado como si fuera una posición (F2 H2), pares TIF+record
contados como alertas (F2 H5), una ventana horaria transcrita que la propia salida no respalda (F1
H7, A90), un porcentaje de corroboración calculado sobre un pareo distinto (F3 4,9 %). El quinto (C2
omitido en F4) es una lista de criterios pre-registrados de la que se evaluaron dos de cuatro. Ninguno
cambió un veredicto; todos habrían quedado escritos como hechos sin el verificador.

### 5.4 F4 (verificador reimplementó f(θ) sin importar el código: diferencia 0,0 en los 643 pares)

| hallazgo | veredicto | gravedad final | lo que agregó |
|---|---|---|---|
| derivación de f(θ) | **CONFIRMADO** | 2 | las 5 citas del ATBD son verbatim (`pdftotext`); corroboró la franja por un segundo camino (16 píxeles M × 0,742 = 11,87 km). Cuantificó la tensión S4: el modelo pone 2,10 filas de solape en θ=19°; absorbiéndolas el borde va a 1,073 y la cola a 16,5 % — mismo veredicto. El supuesto frágil es r(θ): un modelo alternativo defendible da f(20°)=0,733 y reprobaría el control negativo |
| tabla de las tres leyes | **CONFIRMADO** | 1 | reproduce exacto. 309 pares reusan la misma ALERTA (máx 3): con pareo 1-a-1 quedan 517 pares, 0,940/1,067, cola 14,7 % — el veredicto aguanta. La ground truth se lee del CSV vivo, no del snapshot; ambos dan idéntico |
| veredicto NO ADOPTAR | **PARCIALMENTE REFUTADO en la forma, REFORZADO en el fondo** | 3 | S133 congeló **cuatro** criterios (`AB_AREA_VEREDICTO_CHUNK1.md:28-35`) y el auditor evaluó dos. **C2 (volcanes en banda) es computable y da 1/8 para la ley intermedia contra 3/8 del control**. «No adoptar» sale más firme |
| H1 la cola es del régimen sub-MW | **PLAUSIBLE, sobre-afirmado** | 3 | los repartos reproducen, pero la cola **sí responde a la ley** dentro del estrato sub-MW (control 5,3 % → geoloc 24,5 % → intermedia 17,1 %) y **se duplica en el borde** (≥50°: 28,0 % vs 14,3 % nadir). Alternativa que faltaba: MIROVA publica a 2 decimales (mínimo 0,02; sólo 46 valores distintos bajo 0,5 MW en 514 pares) → ±17-25 % de cuantización del denominador. Debilita la recomendación de revisar C4 |
| H2 pozo 0,786 en 35-50° | **CONFIRMADO** | 2 | aguanta el pareo estricto |
| H4 área por píxel no persistida | **CONFIRMADO** | 1 | 67 claves, ninguna de área |

Hallazgos propios del verificador: **P1** C2 omitido. **P2 «mejor en el centro» es falso**: C1 juzga 2
de 5 bins y son los 2 donde f gana; por bins en banda, geoloc tiene 4/5 y la intermedia 3/5 — f saca
de banda a 25-35° y 35-50°. **P3** la cola sí tiene eje cenital. **P4** cuantización de MIROVA. **P7** el
ATBD se contradice (25,9 vs 25,60 km). NO VERIFICADO (necesitan granules): f por píxel; C3; y una
sospecha de lectura de código — la diferencia centrada de `pixel_areas_from_geolocation` cruza la
frontera de barrido en 2 de cada 32 filas y ahí mide el salto del bow-tie, no el píxel.

## 6. Cierre por guard (regla B)

| qué cierra | test | tipo |
|---|---|---|
| §0 P1 gazetteer existe con PCC y Lastarria | `tests/test_guard_regla_c_s134.py::test_p1_*` | invariante |
| §0 P4 sin duplicados por `(sensor, granule)` en los 11 Tier A | `::test_p4_*` (parametrizado × 11) | invariante |
| §0 P5 `diag_nti_max` persistido en MODIS | `::test_p5_*` | invariante |
| §0 P10 cap de path D activo en el perfil efectivo y persistido en PCC | `::test_p10_*` | invariante |
| §1/§2 control positivo permanente: Láscar V375 con el cúmulo a < 0,5 km en la mayoría de las pasadas publicadas | `tests/test_guard_anillo_s134.py::test_control_positivo_lascar_cumulo_en_el_crater` | invariante |
| §1 A13: los scripts de posición de `experiments/_s134_audit/` anclan en `vent_*`, no en el catálogo | `::test_scripts_de_posicion_s134_anclan_en_vent` | invariante |
| §3 H1 `keep_peak`: la firma (records `test1_roi` de 1 píxel a > 2 km con `bt_k < t_bg_k` publicados como summit a 0,0 km) | `tests/test_guard_keep_peak_s134.py::test_keep_peak_no_publica_pixeles_bajo_el_fondo_como_summit` | **xfail estricto**: describe el comportamiento correcto y hoy falla; el día que un cambio lo cure, el XPASS rompe la suite y obliga a actualizar este doc y `MIROVA_DIVERGENCES.md` |
| §3 H2 second pass sin primer pase | `::test_second_pass_no_publica_sin_primer_pase` | **xfail estricto**, misma lógica |
| §0 P9 marcador «extensión» | no medible como invariante: es un no-op medido (0/5.340) y la decisión es de Nicolás | — |
| §0 P11 chunks 2/3 | hecho histórico cerrado por decisión, no invariante | — |
| §2 H3 relojes del `index.csv` del archivo TIF | no medible desde este repo (el archivo es otro repo); queda como nota de método en §Seguimientos | — |
| §4 F4 ley intermedia | no se adopta nada; el instrumento es `f4_solape_ley_intermedia.py` con control positivo propio (reproduce S133 a 3 decimales) | — |

## M. Pruebas de campo para Nicolás

Dashboard: `https://mendozavolcanic.github.io/VRP-chile/?volcano=<Volcan>` (parámetro verificado en
`frontend/index.html:869`). mirovaweb: `https://www.mirovaweb.it/NRT/volcanoMap.php?volcano=<Volcan>&sensor=VIIRS375`
sirve la vista **actual**, no una pasada histórica; para la pasada concreta el sustituto es el TIF
descargado en `experiments/_s134_audit/tif/` (nombre `YYYYMMDD_HHMMSS_VIIRS375.tif`). Todas las
pasadas de abajo son nocturnas (solar_zenith > 143°).

| ID | pasada UTC | volcán | qué mirar | qué decide |
|---|---|---|---|---|
| F3-1 | 2026-07-01 05:00 (NOAA-20) | Villarrica | en el dashboard, con «Todos los pixels»: el punto rojo *summit* en el cráter a «0,0 km» y el píxel real a 2,68 km, BT 263,9 K contra fondo 270,1 K, 0,130 MW | si ese píxel del flanco, más frío que el fondo, debe seguir publicándose como anomalía crateriana «Muy Bajo» (decisión D1) |
| F3-2 | 2026-08-14 04:42 (NOAA-20) | Villarrica | ídem: píxel a 2,86 km, 266,3 K vs 262,8 K, 0,142 MW | ídem |
| F3-3 | 2026-08-31 05:06 (NOAA-21) | Villarrica | 2 píxeles a 2,58 y 2,97 km, publicados a 0,0 km, 0,165 MW | ídem |
| F3-4 | 2026-06-17 05:42 (SNPP) | Láscar | control positivo: 4 píxeles, pico a 0,10 km, 288,9 K vs 265,7 K, 0,550 MW | que el mecanismo sí pone el cúmulo en el cráter cuando hay foco |
| F3-5 | 2026-07-09 05:48 (NOAA-20) | Láscar | ídem, pico 0,13 km, 279,8 K, 0,359 MW | ídem |
| F3-6 | 2026-07-10 05:30 (NOAA-20) | Láscar | ídem, pico 0,26 km, 273,5 K, 0,249 MW | ídem |
| F2-1 | 2026-08-21 06:36 (NOAA-21) | Puyehue-C. Caulle | nuestro cúmulo a 0,08 km del cráter; MIROVA declara 8,19 km **desde su centro de grilla, que está a 7,57 km del cráter** | que el «8 km» es el ancla, no un desacuerdo |
| F2-2 | 2026-08-21 06:30 (NOAA-21) | Tupungatito | nuestro 2,89 km; MIROVA 5,21 km; offset del ancla 4,86 km | ídem |
| F2-3 | 2026-08-20 06:00 (NOAA-20) | Láscar | máximo del TIF a 0,128 km y nuestro cúmulo a 0,14 km, los dos en el cráter | los tres puntos coinciden con foco fuerte |
| F2-4 | 2026-08-09 05:54 (SNPP) | Planchón-Peteroa | nuestro 0,47 km; TIF 0,60 km; MIROVA 2,02 km con ancla a 2,02 km | multi-cráter (A22): ¿el cúmulo cae en Peteroa? |
| F2-5 | 2026-07-20 05:48 (NOAA-20) | Villarrica | nuestro 0,15 km del cráter, máximo del TIF a 4,71 km | una de las pocas pasadas confirmadas; el caso donde el TIF falla como árbitro |
| F2-6 | 2026-08-20 06:00 (NOAA-20) | Isluga | nuestro 0,86 km al SW del `vent_*`; MIROVA 0,53 km desde su centro, que está 0,37 km al SW | si la coordenada del cráter activo de Isluga es la declarada (2 decimales) o hay que refinarla (decisión D4). Nota del verificador: el «86 % MIROVA más cerca» del informe F2 era del bloque retractado; re-anclado es 18 % |
| F1-1 | serie completa | Isluga | en el mapa, la nube de detecciones V375 respecto del cráter marcado: ¿está 0,8 km al SW de forma sistemática? | decisión D4 |
| F1-2 | serie completa | Llaima | el dashboard muestra serie térmica continua (277 records summit en 3 meses) y MIROVA no publicó ninguna alerta V375 en la ventana | si el operador debe ver esa ausencia de corroboración (decisión D5) |

## D. Tabla de decisiones del dueño (opciones y recomendación; no se tomaron)

| # | decisión | opciones | recomendación |
|---|---|---|---|
| D1 | **`keep_peak` y la magnitud del píxel único** (F3 H1, gravedad 5). El mecanismo publica en los 11 Tier A un píxel del borde del disco, más frío que el fondo global, como summit a 0,0 km con 0,03-0,17 MW | (a) no tocar y documentar la convención también para la magnitud; (b) correr el probe A75 en CI (`experiments/_s134_audit/f3/probe_etapas_ci.md`) para medir cuántos píxeles del cráter había antes del recorte y diseñar el A/B; (c) A/B directo `keep_peak` OFF vs ON con FN estratificado sobre cat-b real (Lastarria, Tupungatito, Isluga son los que el mecanismo corrobora) | **(b) primero, luego (c)**. No (a): la magnitud no está cubierta por ninguna convención y fabrica un nivel base falso. Cualquier cambio pasa por MISSION.md (3 preguntas), A45 (tag + confirmación) y A83 (estratificar por régimen) |
| D2 | **second pass sin conjunto activo** (F3 H2 + P2). Corre con máscara vacía en 2.295/3.164 records y sin adyacencia, contra `sp426_5.txt:329-341` | (a) condicionar el second pass a `n_first_pass > 0` y a la vecindad 8 del conjunto activo (fidelidad literal al paper); (b) sólo reponer la compuerta BT; (c) dejar | **(a)**, con A/B: es un drift de fidelidad respecto de Coppola 2016a, no un gate nuevo (pasa la puerta 1 de MISSION). Medir FN sobre cat-b antes de flip |
| D3 | **flip de `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`** (heredada de S132/S133). F1 H5: 43 de 48 pasadas MODIS confirmadas quedan `far` con cúmulo a 1,56 km; con `summit ∪ far` paridad 0,91 (IQR 0,48-2,26) y 0 FN | (a) no encender; (b) re-correr el A/B con C2' en unidades de `inner_radius` (`docs/s133/C2_NORMALIZADO_INNER_RADIUS.md`); (c) encender | **(b)**. F1 y F3 dicen que el cúmulo MODIS está a 1,5 km, no en el cráter, así que el flip no es «corregir una etiqueta» sino «aceptar un cúmulo a 1,5 km»: hay que medirlo con el criterio en las unidades correctas (A91) |
| D4 | **coordenada del cráter de Isluga** (F1 H6, plausible fuerte). Único Tier A con `vent_*` a 2 decimales (±0,55 km); el foco está 0,86 km al SW en el 100 % de los pares; el `mirova_center` está 0,37 km al SW | (a) refinar `vent_lat/lon` con imagen/DEM (Nicolás conoce el volcán); (b) dejar | **(a)**: barato, toca sólo `volcanoes.yaml`, y corrige toda distancia publicada de un Tier A. Verificar antes con la prueba F1-1 |
| D5 | **mostrar la corroboración de MIROVA por volcán en el dashboard** (F2 H5, F1 H2). Llaima 0 alertas V375 en 3 meses contra 277 records; Villarrica 15, Copahue 3, NdC 8 | (a) un indicador por volcán «alertas MIROVA V375 en 90 d / records nuestros»; (b) nada | **(a)**, es display de señal real (A72: no esconde un artefacto, separa confirmado de no confirmado). Sin tocar pipeline |
| D6 | **ley de área intermedia** (F4). No adoptar hoy; f(θ) acierta dirección y tamaño sin parámetros | (a) A/B en S135 aplicando f **por píxel** en `resolve_viirs_pixel_areas` con los 4 criterios de S133 y C4 revisado a la luz de la cuantización de MIROVA a 2 decimales; (b) archivar | **(a)**, después de D1/D2: si el píxel publicado cambia, la paridad por cenital cambia con él |
| D7 | **marcador «extensión» para PCC** (P9, heredada). El mecanismo existe y es un no-op medido (0/5.340) | (a) ajustar `volcanic_features.yaml` para que dispare; (b) quitarlo; (c) dejar | pregunta volcanológica de Nicolás; sin recomendación técnica |
| D8 | **re-correr B22 con ventana ancha** (P12, heredada) | (a) sí, Isluga 66 / Láscar 62; (b) archivar hasta D1 | **(b)**: F1/F3 muestran que la magnitud publicada en régimen débil es la de un píxel del flanco; medir B22 sobre eso es medir el objeto equivocado |

## Seguimientos (no se arreglan en S134)

- **`frontend/index.html:2789`** popup con `bt_k: r.t_max_k ?? r.t_max_i04_k` (máximo del ROI de 25 km): tres píxeles distintos en un globo (F3 verificador P1, gravedad 3).
- **Campos de distancia desde el catálogo** (`anomaly_pixels[].dist_km`, `hotspot_dist_km`, `diag_t_max_dist_km`, `process_viirs.py:723/945/1429/1437`) conviviendo con `vent_*` en el mismo record (F3 H4, A3). Candidato a unificar al vent con guard.
- **Área por píxel del brazo geoloc no persistida** (F4 H4, A7/A46).
- **`experiments/_s133_villarrica_focus/anillo_tier_a.py`** mide `pc.centroid`, que para los records `ctx_cluster` con `_test1_wins` no es lo que se dibuja (F3 H3). Si se reusa, medir `final_hotspot` o ambos.
- **Informe F1 H7**: la ventana horaria correcta es 17:18-19:00 UTC y el record más cercano está a 6,4 h; corregir si se cita. **Informe F2**: los conteos de alertas por volcán son de pares TIF+record, no de alertas (Villarrica 15, NdC 8, Copahue 3, Isluga 133 son los correctos); la fila F2-6 de la cola arrastraba el «86 %» retractado.
- **`index.csv` de `mirova-tif-archive`**: dos relojes discrepan > 60 s en el 14,2 % y `acquisition_utc` va vacío en 17,6 %; a ±20 min el 27 % de los pares serían del otro satélite. Nota de método para quien use el archivo: exigir coincidencia de relojes y ≤120 s (F2 H3). Es otro repo.
- **`pixel_areas_from_geolocation`** (`scan_geometry.py`): la diferencia centrada cruza la frontera de barrido en 2 de cada 32 filas y ahí mide el salto del bow-tie, no el píxel (sospecha del verificador F4; necesita granules).
- **ATBD Geolocation 2014** se contradice consigo mismo (25,9 vs 25,60 km de franja al borde); sin efecto en el veredicto.
- **Recall CONS∪OCR sin filtro día/noche** cobra como FN 59 alertas OCR diurnas de Láscar/Lastarria (F1 H7): revisar `pipeline/audit_metrics.py` (no leído en S134).
- **F5 auditor (Sonnet) leyó «24/24 verdes» como universo completo** sin mirar la ventana (P11). Patrón A90, ya corregido en §0.
- **Disco al 100 %**: la suite dio `MemoryError` en dos tests que cargan JSON grandes hasta que se recortó su huella; el pagefile no puede crecer. Los worktrees sparse se eliminan al cierre.
