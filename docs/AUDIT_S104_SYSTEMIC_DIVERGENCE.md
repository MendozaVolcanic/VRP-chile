# AUDIT S104 — Divergencia sistémica vs MIROVA (multi-volcán, multi-sensor)

**Fecha**: 2026-06-09 · Pedido de Nicolás (A62): "cosas así pueden estar ocurriendo en
todos los volcanes". 4 subagentes paralelos read-only + matriz base propia. Confirma:
SÍ hay divergencias sistémicas, con causas físicas distintas por sensor.

## Matriz base (volcán × sensor, distancia mediana al cráter)
| sensor | dist mediana | % lejos del cráter | veredicto |
|---|---|---|---|
| **VIIRS375** | 0.3–1.6 km | 0–2% | bien anclado (salvo NdC sub-detecta) |
| **VIIRS750** | 0.4–2.6 km (PCC 13 km) | 0–45% | redundante + más disperso que V375 |
| **MODIS** | **16–24 km TODOS** | **87–98%** | campo difuso = artefacto sistémico |

## Eje 1 — MODIS difuso (el "resto" principal que ve Nicolás)
~280 records MODIS/volcán, 87–98% a 16–24 km del cráter, en LOS 11. **Diagnóstico
(Agente 1, 901 records analizados)**:
- Dispara por **Path D (dNTI contextual)** casi exclusivo. Usa NTI (no MIR absoluto) →
  **NO es el sesgo topográfico del Test1 VIIRS** (A69); es otro mecanismo: el kernel
  8-vecinos sobre escena tibia uniforme dispara espurio, y la suma scene-wide infla la
  magnitud (Wooster BT⁸).
- **73% t_max<290K** (no volcánico), **77% t_bg≥270K** (escena tibia, NO cirrus), ~0% real.
- **El cap D9** (`path_d_only_cap_mw=5.0` + `path_d_only_cap_tbg_max_k=270`) **solo atrapa
  el 23% cirrus** — el 77% restante es escena tibia (t_bg≥270) y ESCAPA el cap. 640/901
  (71%) con scene vrp>5 MW sin capear.
- MIROVA reporta MODIS ALERTA solo en Lascar (100). En el resto ~0 → MODIS difuso es
  artefacto que MIROVA no publica.
- **MODIS solo corre en Actions** (pyhdf roto Windows). Fix: (a) display — extender
  discriminante a régimen tibio (path-D only ∧ dispersión alta ∧ sin confirmación
  MIROVA); (c) co-validación VIIRS375 ±ventana; (b) compacidad espacial (A55 riesgo).

## Eje 2 — VIIRS750 redundante y más disperso (Agente 4)
- V750 es **sistemáticamente más disperso que V375 en los 11** (mayor σ_bg por 750m sobre
  terreno heterogéneo → centroides corridos). PCC V750 mediana **13 km** (peor); NdC 45%
  far; Copahue/Lastarria 17–18% far.
- **NO aporta recall** que V375 no tenga (recall750 ≤ recall375 salvo NdC). Los far-V750
  tienen VRP comparable a los near → es mis-localización, no sub-señal.
- **Candidato a peso bajo / display secundario.** (Corrección a la matriz base: MIROVA SÍ
  publica VIIRS750 — Eje 4 abajo.)

## Eje 3 — NdC sub-detección (Agente 4) — el ÚNICO FN sistémico
- NevadosDeChillan: **recall VIIRS375 = 0.00** (0/4 noches ALERTA MIROVA), solo ~50
  detecciones V375 (vs ~430 otros). Faint sub-pixel genuino (señal del cráter no rompe
  umbral). Ya documentado S90. Lever: detección diurna MODIS (S90, flag OFF). Es el caso
  más grave (FN = el riesgo de monitoreo), opuesto a la sobre-detección.

## Eje 4 — Cruce MIROVA por sensor: MIROVA SÍ publica VIIRS750 (Agente 2)
- **CORRECCIÓN a mi matriz base**: el "MIROVA_AL=0 en V750" era un bug de MI script
  (regex no capturó "VIIRS" bare = M-band). **MIROVA publica VIIRS750 bajo etiqueta
  `VIIRS` a secas (217 ALERTA)**; el loader canónico `pipeline/mirova_csv_loader.py:63-83`
  ya lo mapea bien desde S93 (chequea "375" antes que "VIIRS"). El frontend (3 vistas)
  también. Lección A48 (no inventar regex) — el loader del proyecto está SANO.
- MIROVA por sensor en M-band: Lascar 130, PCC 29, Isluga 27, Tupungatito 12 ALERTA V750.

## Eje 5 — PCC: lo confirmado es el CRÁTER, no el lacolito (Agente 3) — corrección
- Sorpresa: el `mirova_center` PCC está a 7.57 km del cráter Puyehue y 4.11 km del
  lacolito. Las ALERTA MIROVA (~7.8 km del grid-center) apuntan al **cráter Puyehue**,
  NO al lacolito. **Lo que MIROVA confirma en PCC es el cráter Puyehue en VIIRS** (0.2–1.2
  MW). El lacolito NO es lo que genera las ALERTA.
- El "resto" de PCC: MODIS difuso (16 km, artefacto), VIIRS375 sub-umbral (0.09 MW, 157/284
  cirrus), VIIRS750 (242/283 cirrus). ~41% del VIIRS no-match es **cirrus** (D9/A23).

## Ranking VIIRS (mejor → peor alineado con MIROVA, Agente 4)
1. Lascar (excelente, 0.25 km, recall 0.92) · 2. Isluga · 3. Lastarria (offset Lazufre
real) · 4. PlanchonPeteroa · 5. Tupungatito (sesgo glaciar) · 6. PCC (V375 ok, V750
disperso) · 7. Chaiten · 8. Villarrica (9.7× cat-b + sesgo N) · 9. Copahue (130× cat-b)
· 10. Llaima (128× cat-b) · 11. **NdC (sub-detección, recall 0)**.

La sobre-detección Copahue/Llaima/Villarrica (9–130×) es **señal cat-b real** (0.06–0.07
MW, ΔT>5K, lava lake / El Agrio / Pichi-Llaima), sub-umbral de **publicación** de MIROVA,
NO artefacto (A54/A68). Lascar/Lastarria/PCC/Tupun bien calibrados (1.1–1.7×).

## NOTA sobre el ground truth — qué es "RUTINA" (corrección de Nicolás, S104)
`RUTINA` NO es un juicio de MIROVA — es un registro del **scraper Mirova-v1**: en cada
escaneo de mirovaweb, si NO había una ALERTA publicada, el scraper guardaba un placeholder
(VRP=0, `Ruta Foto = "No descargada"`); si había ALERTA, la guardaba con su imagen
(`imagenes_satelitales/...`). Implicación para la auditoría: las miles de RUTINA por volcán
(Villarrica 2045 vs 11 ALERTA) son **prueba de cobertura del scraper** — confirman que
cuando nosotros detectamos en una noche sin ALERTA, MIROVA genuinamente no publicó (no es
falta de dato). Esto REFUERZA: la sobre-detección VIIRS375 (cat-b real) y el MODIS difuso
(artefacto) se miden contra cobertura sólida. Lenguaje correcto: "el scraper escaneó esa
noche y MIROVA no publicó ALERTA", NO "MIROVA la clasificó RUTINA".

## Acciones priorizadas (NINGUNA implementada — A45/brainstorming)
**Regla A72 (Nicolás): fix de ALGORITMO sobre display.** Lo que es artefacto (MIROVA no
lo entrega, lo generamos nosotros) se ataca en la DETECCIÓN, no se oculta en el frontend.

| # | Frente | Naturaleza | Fix RAÍZ (algoritmo) | Impacto |
|---|---|---|---|---|
| 1 | **MODIS difuso** | **artefacto** (~0% real) | pipeline: que el path-D no genere el campo difuso — co-validación VIIRS375 cercano / compacidad espacial / t_max absoluto. NO display. | alto — el "resto" universal |
| 2 | **NdC sub-detección** | **FN** (señal real perdida) | pipeline: detección diurna MODIS (S90) o bajar umbral. A45 | alto (FN = lo más grave) |
| 3 | **Cirrus path-D (D9/A23)** | **artefacto** | pipeline: discriminante mejor que t_bg (contaminado por altitud A68) — co-validación BT/NTI | medio |
| 4 | **VIIRS750 disperso** | mis-localización | pipeline: replicar Test1-NTI a V750 (process_viirs_mod.py) / mejorar localización; evaluar si aporta. NO solo "ocultar" | medio |
| 5 | **Test1-NTI nevados** | sesgo topográfico | V2 en A/B (run 27223821692) — algoritmo | en curso |

**El instinto de Nicolás es correcto**: hay divergencia sistémica real. La mayor y más
universal es el **MODIS difuso** (artefacto). Por A72, TODOS estos frentes son de
ALGORITMO (no display) porque son artefactos o sub-detección, no señal cat-b real. El
display-suppression solo aplicaría a la sobre-detección VIIRS375 (cat-b real) — pero ahí
NO se borra ni oculta, es el valor agregado. (Corrección S104: mi encuadre inicial de
"MODIS difuso en display" era erróneo — A72.)
