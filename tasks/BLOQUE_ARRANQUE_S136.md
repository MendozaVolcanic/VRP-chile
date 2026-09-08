# Bloque de arranque S136

## Prompt para pegar al inicio de la sesión (escrito para Claude Fable 5.1)

```
Continuamos VRP Chile desde S135. Ayer corrimos el probe A75 por etapa en CI (decisión D1(b) de
AUDIT_S134 §D): experiments/_s135_probe_etapas/RESULTADOS.md, verificado con contexto limpio.

QUÉ SALIÓ. El criterio pre-registrado dio H1 REFUTADA por la rama prevista: en Villarrica
2026-07-01 el cráter no está en el footprint del Test 1 antes de keep_peak (0 px a <0,5 km; el
disco entero a 239 K, 27 K bajo el fondo global — gradiente A69 o tope de nube, el probe no
capturó I05). keep_peak no descarta el cráter; elige el borde de un footprint que nunca lo tuvo.
Tres noches, tres fenómenos (07-01 cono frío; 08-14 flanco S; 08-31 objeto discreto a 2,97 km E,
dNTI-positivo, donde keep_peak es inerte). Control Láscar 3/3 pero vacuo: keep_peak sólo corre
si final_hotspot_source == "test1" y en Láscar siempre gana el contextual.

LO NO PREVISTO, y lo más importante: 2 de 3 pasadas de Villarrica NO reproducen el record
persistido con el código de hoy sobre el mismo granule. Causa: hasta #535 (2026-08-28 23:00 UTC)
process_viirs.py fijaba CLOUD_BT_THRESHOLD = 260 K a mano; hoy lee cloud_mask_bt_k: 0.0 (D14,
cerrada, correcta). En nevados el fondo global baja 6-8 K (Villarrica 268,5 → 262,3 K; Llaima
268,6 → 260,9; Láscar no se mueve) y el first pass dispara 4-7× más. Los conteos de D19
(245/289 test1_roi) son del régimen viejo: 396 records contra 40 del nuevo. El mecanismo sigue
(08-31 reproduce exacto) pero su tamaño en producción hoy NO está medido.

PASO 0 YA CORRIÓ (S135, experiments/_s135_probe_etapas/RESULTADOS_PASO0.md, verificado): 12 pasadas
(9 cat-b Lastarria/Tupungatito/Isluga + 3 control Láscar con first pass vacío), con I05, sin nube.
Veredicto pre-registrado INTERMEDIA (0 pérdidas con el pico en el cráter, n=2; 4/9 con el pico en el
borde). El verificador limpio corrigió (gravedad 5) que off_pierde ignoraba el second pass, que corre
antes del filtro y no depende de keep_peak: con D2 permisivo (hoy) el second pass rescata 3 de las 4
(Lastarria 08-28 con el píxel idéntico, Tupungatito 08-21 con el cráter) y la cuarta (Isluga 08-19)
no es señal (−3,8 K; cota A93 2,56 km del hotspot de MIROVA). Con D2 condicionado como manda Coppola,
keep_peak OFF pierde el campo fumarólico de Lastarria (cota 0,08/0,64, presupuesto 0,55 km) y el
cráter de Tupungatito 08-21. Conclusión: D1 y D2 son UN diseño de 4 brazos (keep_peak OFF/ON ×
second pass condicionado/no), régimen nuevo, FN cat-b por volcán, cota A93 desde mirova_center.
11/12 test1_roi persistidos son hoy ctx_cluster (régimen D14). H2 = 13/13 ≤ 3 K.

PAPER (S135): docs/paper/ tiene §4 y §5 en prosa (PR #601), README del flujo, y
scripts/paper_numbers.py --tests → numbers.json/TABLAS.md (Tablas 2-4; PR #600). D20 registrado
(banda 31 vs 32, despreciable). Siguiente paso acordado: §6 Validation con la Tabla 4 y las
divergencias abiertas de frente; después §3/§7/§8. Las 11+6 notas al editor de sec4/sec5 esperan
revisión de Nicolás (la más importante: Coppola 2014 citado de segunda mano; grilla 50 vs 51 km).

OBJETIVO S136 (si Nicolás no decide otra cosa): (1) medir D19 sobre el régimen vigente
(records V375 summit desde 2026-08-28 23:00; reusar experiments/_s134_audit/f3/verif_h1.py con
esa ventana; reportar con denominador — hoy n≈40 por volcán, así que puede convenir esperar o
reprocesar junio-agosto con el código actual en CI, chunked, sin tocar data/ operacional);
(2) escribir el pre-registro del A/B de 4 brazos (keep_peak OFF/ON × second pass condicionado a
conjunto activo no vacío + vecindad 8, Coppola 2016a l.329-341) con FN medido sobre cat-b por
volcán y presentárselo a Nicolás; (3) si lo aprueba, montar los 4 perfiles con data_subdir
aislado (patrón S24/S25) sobre la ventana del régimen nuevo.

HILO PARALELO — el paper. Nicolás preguntó en S135 en qué quedó. Estado: un solo borrador,
docs/PAPER_VRP_CHILE_DRAFT_S72.md (475 líneas, esqueleto anotado, sin prosa salvo el abstract,
que está marcado [UPDATE S119]); sin tocar desde S120 (2026-07-02, PR #479). Decisiones ya
tomadas (§0): venue Volcanica (diamond OA, sin APC), scope clon + beyond-MIROVA, Coppola después,
MIT, Claude en agradecimientos. Faltan: prosa de §3-§11, tablas de validación regeneradas por
script (S91), 12+ figuras, ~30-40 refs con DOI (hoy 20 sin DOI, sin .bib), coautores, disclosure
IA con SERNAGEOMIN. Riesgo: el abstract cita números de S119 y desde entonces cambiaron
nadir-fijo, D14, D17/D18, S130 (piso), S132 (F5'), D19. Propuesta de S135 para seguirlo: ver
el mensaje de cierre de S135 (cuatro pasos: congelar los números en un script único, redactar
§4-§5 desde MIROVA_DIVERGENCES + FICHA_SDA, §6 validación con la banda de paridad vigente, y
recién entonces §3/§7/§8). Preguntar a Nicolás qué paso quiere primero.

LÍMITES: nada en pipeline/ sin tag + confirmación (A45); ningún flag sin A/B real y criterio
pre-registrado (A18/A91); granules sólo en CI (A71); los 2 xfail de test_guard_keep_peak_s134.py
son el tripwire de D19. Español de Chile sin voseo; fenómeno → mecanismo → números; todo número
con denominador y ventana (A90); un radio no es una posición (A93).

LEER, en orden: 1. este bloque · 2. experiments/_s135_probe_etapas/RESULTADOS.md ·
3. docs/MIROVA_DIVERGENCES.md D19 (adenda S135, al final) · 4. docs/AUDIT_S134.md §D ·
5. docs/PAPER_VRP_CHILE_DRAFT_S72.md §0 y §C (sólo si se retoma el paper).

ESTADO AL ARRANCAR: suite 1211 passed · 4 skipped · 2 xfailed. Nada corriendo en CI. Yml del
probe archivado. Tres flags de S132 siguen OFF. Ninguna decisión de §D tomada por Nicolás.
```

## Lo que S135 dejó hecho

| item | dónde |
|---|---|
| probe A75 por etapa VIIRS375, read-only, corrido en CI (run 34071793829, 6/6) | `experiments/_s135_probe_etapas/` · PR #598 |
| paso 0 (12 pasadas cat-b/control, I05, criterio pre-registrado) corrido (run 34091969140) | `RESULTADOS_PASO0.md` · PR #600/#602 |
| paper: §4 + §5 en prosa, README, `scripts/paper_numbers.py`, D20 | `docs/paper/` · PR #600/#601 |
| análisis puro con 13 tests (A89, escena sintética D19, criterio, yml) | `analisis.py`, `tests/test_probe_etapas_s135.py` |
| resultados + verificación con contexto limpio (4 correcciones incorporadas) | `RESULTADOS.md` |
| §3 dos regímenes de fondo, con script | `regimen_fondo.py` → `regimen_fondo.json` |
| adenda S135 a D19 | `docs/MIROVA_DIVERGENCES.md` |
| yml archivado | `.github/workflows/_archive/probe-s135-etapas.yml` |
| D19 medido en el régimen vigente: **la caída no está demostrada** (39,0 % cae dentro de la variación mensual; el artefacto se mudó de rama) | `D19_HOY.md` · `d19_regimen_vigente.py` |
| pre-registro del A/B de 4 brazos, con criterio y umbrales | `docs/PREREGISTRO_AB_D1_D2_S135.md` |
| paper: §6 Validation en prosa + recorte de la ventana de ground truth | `docs/paper/sec6_validation.md` |

## Seguimiento nuevo (S135, no arreglado a propósito)

**El ground truth que leen los análisis está siete días atrás del que refresca el pipeline.**
`data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` (35.037 filas, hasta
2026-08-31) es el que consumen el cargador canónico, `scripts/paper_numbers.py` y todas las
mediciones; `latest_consolidado.csv` en la raíz (36.160 filas, hasta 2026-09-07) es el que
`sync-mirova-csv.yml` actualiza cada hora y el que consume el frontend. El workflow corre verde:
no está roto, escribe en otro archivo (familia A17, canal partido). No se tocó en S135 porque
cambiar la fuente del ground truth en medio de una medición comparativa la invalidaría. Al
arreglarlo, ojo con la asimetría: `latest_consolidado.csv` es sólo el canal consolidado; el OCR
fresco sigue en el snapshot. Mitigación ya aplicada: `paper_numbers.py` y
`d19_regimen_vigente.py` recortan toda comparación a la última fecha presente en el CSV y lo
declaran en la salida (antes, seis días de septiembre contaban como «detectamos y MIROVA no»).

## Decisiones que siguen esperando a Nicolás (AUDIT_S134 §D)

**D1 y D2: DECIDIDO Y EN EJECUCIÓN (2026-09-07).** Nicolás autorizó tocar el pipeline, fijó
**cero pérdidas** sobre lo que MIROVA entrega (más exigente que el 10 % propuesto) e instruyó
«ser lo más fiel posible y entender por qué sucede y arreglar cuando diferimos»: una pérdida
NO descarta el brazo, abre una investigación por pasada. Corre sobre los 6 volcanes que
deciden. El segundo pase condicionado está implementado detrás de
`ENABLE_SECOND_PASS_CONDITIONED` (OFF en producción, 17 tests, PR #605) y el A/B de 5 brazos
está lanzado (`reproc-s135-ab-d1d2.yml`, chunk 1 = 06-01→07-15 con overwrite=true; **falta el
chunk 2 = 07-16→08-31 con overwrite=false**). Evaluador pre-escrito:
`experiments/_s135_ab_d1d2/evaluar_ab.py --dir <artefactos>`. Texto viejo, por historia:
**esperaba tres respuestas suyas**
(`docs/PREREGISTRO_AB_D1_D2_S135.md` §«Lo que necesito de vos»): (a) ¿autoriza tocar
`pipeline/detection_context.py` para el brazo del segundo pase condicionado (A45)?; (b) ¿acepta
el umbral de rechazo del criterio 1 (perder >10 % de noches MIROVA-confirmadas en Lastarria,
Tupungatito o Isluga descarta el brazo)?; (c) ¿los 11 Tier A o los 5 que deciden? Sin (a) sólo
corren los brazos A y B. · D3 · D4 · D5 · D6 · D7 · D8. Y una nueva: **qué es el objeto a 2,97 km E del cráter
de Villarrica** (08-31, +8 K sobre un disco plano, dNTI-positivo).
