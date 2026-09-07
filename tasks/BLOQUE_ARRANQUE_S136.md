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

OBJETIVO S136 (si Nicolás no decide otra cosa): (1) medir D19 sobre el régimen vigente
(records V375 summit desde 2026-08-28 23:00; reusar experiments/_s134_audit/f3/verif_h1.py con
esa ventana; reportar con denominador — hoy n≈40 por volcán, así que puede convenir esperar o
reprocesar junio-agosto con el código actual en CI, chunked, sin tocar data/ operacional);
(2) paso 0 del A/B D1(c): el mismo probe (yml en _archive/probe-s135-etapas.yml; agregar captura
de I05 y exigir noches despejadas: mediana del disco a menos de ~10 K del fondo global) sobre
3 test1_roi MIROVA-confirmadas de Lastarria y 3 de Tupungatito (la cara cat-b de A83/A84) y un
control focal con first pass VACÍO; (3) con eso, escribir el pre-registro del A/B keep_peak
OFF/ON (criterio propuesto en RESULTADOS.md §4.5) y presentárselo a Nicolás junto con D2, que
sube de prioridad: en el régimen nuevo el second pass sin conjunto activo fija la posición
publicada (07-01: 3,789 km, summit).

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
| análisis puro con 13 tests (A89, escena sintética D19, criterio, yml) | `analisis.py`, `tests/test_probe_etapas_s135.py` |
| resultados + verificación con contexto limpio (4 correcciones incorporadas) | `RESULTADOS.md` |
| §3 dos regímenes de fondo, con script | `regimen_fondo.py` → `regimen_fondo.json` |
| adenda S135 a D19 | `docs/MIROVA_DIVERGENCES.md` |
| yml archivado | `.github/workflows/_archive/probe-s135-etapas.yml` |

## Decisiones que siguen esperando a Nicolás (AUDIT_S134 §D)

D1 (ahora con el probe: A/B sólo sobre el régimen nuevo y tras el paso 0 cat-b) · D2 (sube de
prioridad) · D3 · D4 · D5 · D6 · D7 · D8. Y una nueva: **qué es el objeto a 2,97 km E del cráter
de Villarrica** (08-31, +8 K sobre un disco plano, dNTI-positivo).
