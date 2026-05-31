# AUDIT S93 — Artefactos de campo frío y sobre-estimación de VRP vs MIROVA

**Sesión S93 (2026-05-30).** Disparado por Nicolás: picos engañosos en el dashboard
(PCC 337 MW, Tupungatito 190/82 MW), ratio mediano 20× en Tupungatito, precisión 0.24,
detecciones dispersas fuera del cráter. Pregunta: ¿por qué los generamos si MIROVA no?
Investigación con superpowers-systematic-debugging + 3 subagentes. Datos reproducibles:
`experiments/_s93_audit/{magnitude_coverage,ratio_vs_mirova}.json`.

## 1. Mecanismo raíz (físico)

El VRP de Wooster (MIR) calcula la potencia como proporcional a **ΔL = L(píxel) − L(fondo)**.
El método asume que el fondo es la superficie normal y el píxel anómalo es lava/foco caliente.

Cuando el fondo es **nieve/hielo/cirrus gélido** (t_bg −10 a −32 °C) y el "píxel anómalo"
es **terreno normal apenas sobre cero** (t_max +1 a +5 °C, NO lava), pasan dos cosas:
1. El **path D (dNTI contextual 8-vecinos, c1=0.003 summit)** marca el píxel porque destaca
   de sus vecinos nevados (umbral muy bajo) — `process_modis.py:505+`, `detection_context.py`.
2. El **VRP de Wooster lo cuantifica con ΔL espurio**: interpreta el contraste nieve↔terreno
   (~20–32 K) como si fuera fondo↔lava. La suma de cientos de píxeles débiles
   (`clustering.py:113`) da decenas-cientos de MW.

Resultado: 20–200× sobre lo que MIROVA reporta (0.03–0.3 MW). Confirmado: PCC 05-05
337 MW (t_bg −30 °C, t_max +1.8 °C, 670 px, **todo path D**, n_bt=0 n_nti=0).

**Por qué MIROVA no lo tiene tan grave**: usa principalmente **VIIRS 375 m** (resuelve el
foco real vs el campo difuso que MODIS 1 km integra), reporta el foco y no la suma del campo,
y filtra estos casos. Es divergencia de método/resolución (A20/A24), no solo de umbral.

## 2. El pipeline YA mitiga esto (cap D9) — pero parcialmente

Existe `apply_d9_scene_cap` (`path_d_cap.py`) + predicado `_path_d_cap_active`
(`process_modis.py:794`, simétrico en VIIRS): **capea pc.vrp_mw a 5 MW** cuando
`n_bt_path==0 AND n_nti_path==0 AND t_bg<270 K`. Marca `primary_cluster.d9_capped=true`.

**Verificado**: el cap funciona en MODIS y VIIRS desde **~2026-05-23**. PCC y Tupungatito
post-05-23 capean correctamente a 5.00. **La distinción contextual-only es la salvaguarda**
que el gate t_bg ciego de S86 no tenía: una erupción real (Lascar 02-17) dispara BT/NTI duros
(n_bt>0 por lava caliente) → NUNCA se capea. **Por eso NO se pierden TPs reales** — responde
la duda de Nicolás. El gate refutado en S86 era `t_bg<260` *ciego* (sin contextual-only).

## 3. Cuatro problemas que el cap D9 NO resuelve

| # | Problema | Evidencia | Naturaleza |
|---|---|---|---|
| **P1** | **Deuda histórica**: records pre-05-23 sin capear | PCC 179, Tupungatito 69, etc. con vrp inflado. Ratio pre-05-23: PCC 2.6×, Lastarria 4.9×, Tupun 10× | Datos viejos. **Reproc local** (A18, no toca código) |
| **P2** | **Cap a 5 MW es demasiado alto** para señal débil | Tupungatito post-cap todo en 5.00, MIROVA ~0.3 → ratio residual 16×. "Empeoró a 17×" = artefacto del cap uniforme | Calibración del cap. Brainstorming + A45 |
| **P3** | **Gap t_bg 270–273 K** (fondo "templado frío") no cubierto | PCC 644 MW (t_bg 272.1, t_max +14.9 °C, 40 px). **ZONA GRIS**: t_max alto = puede ser foco real | Cuidado: bajar el umbral puede tocar reales |
| **P4** | **Dispersión espacial** (far) | Tupun 43% far, NdC 67%, Copahue 55% | Display: `includeFar=false` ya da 0; el mapa los dibuja en gris |

## 4. Respuestas a las observaciones de Nicolás

- **Tupungatito no cae en la laguna cratérica**: 43% de las detecciones son `distance_class=far`
  (fuera del inner_radius 7 km) — path D marca el campo glaciar disperso, no el cráter. El
  frontend con "solo cráter" les da VRP=0, pero el MAPA los dibuja (gris "far"). Dentro del
  radio, el campo difuso esparce puntos sobre el glaciar en vez de concentrar en el foco.
- **Dato alto en tabla** (VIIRS_NOAA21 05-26 3.96 MW): mismo mecanismo glaciar, magnitud
  menor, **bajo el cap de 5** → no capeado. Para Tupungatito (MIROVA ~0.3) es ~13×.
- **Ratio 20×**: combina P1 (deuda) + P2 (cap grueso) + método suma-MODIS vs foco-VIIRS375 (A24).
- **"No replicamos MIROVA"**: parcialmente cierto en MAGNITUD para volcanes glaciar/lacolito de
  señal débil. En DETECCIÓN (recall) sí (Lascar 1.08×, Isluga 1.33× bien calibrados).

## 5. Plan de arreglo propuesto (decisión de Nicolás, A45)

1. **Reproc histórico local** (mayor impacto, NO toca código): regenera los JSON con el cap D9
   actual → la deuda (337/190 MW) baja a 5 MW. Patrón A15/A18 (local, no GH Actions).
2. **Revisar el cap** (P2/P3): ¿bajar de 5 MW? ¿usar single-pixel mode (reportar foco, no suma)
   para señal débil? ¿ampliar predicado al warm-scene (t_max apenas sobre cero, criterio display
   S93) y franja t_bg 270–273 con cuidado de la zona gris P3? → brainstorming + tag + TDD + R2.
3. **Display far** (P4): verificar que el mapa respete "solo cráter" por defecto.

**Escudo**: NO gate t_bg ciego (S86). El cap por COHERENCIA (contextual-only) es seguro y
ya probado. La zona gris P3 (foco t_max alto sobre fondo 271–273) requiere R2 pixel-level
antes de tocar.

## 6. ADDENDUM — análisis POR SENSOR (insight de Nicolás, el decisivo)

Nicolás: "MODIS solo ve pocas cosas y solo cuando son grandes; MIROVA reporta cada satélite
por separado." Re-análisis separando sensores (`experiments/_s93_audit/covalidation_impact.py`
+ conteos CSV) — esto reorienta TODO:

**Detecciones nuestras vs MIROVA, por sensor (11 Tier A, ~5 meses):**
| Sensor | TP (nuestro∩MIROVA) | FP | Precisión | Ratio | Alertas MIROVA en CSV |
|---|---|---|---|---|---|
| **MODIS** | 74 | 2722 | **2.6%** | 2.5× | **80** (77 = Lascar) |
| **VIIRS 375m** | 1550 | 2557 | 38% | 1.9× | **787** |
| **VIIRS 750m** | 0 | 2838 | **0%** | — | **0** |

**Conclusiones (con datos):**
1. **MIROVA NO usa VIIRS 750m** para estos volcanes (0 alertas). Nuestras 2838 detecciones
   VIIRS750 son un sensor que el clon **no debería reportar**. (No es ruido a calibrar — es
   un sensor fuera del alcance MIROVA.)
2. **MODIS solo ve lo grande**: MIROVA publica 80 alertas MODIS, 77 son Lascar (erupción real).
   Para volcanes en reposo, MIROVA MODIS ≈ 0. Nuestro MODIS reporta 2796 (97% artefacto).
3. **VIIRS 375m es la fuente real** (787 MIROVA, 1550 TP nuestros), ratio 1.9× (tolerable).
4. **Co-validación SOLO MODIS es segura**: los 74 TP MODIS están **100% cubiertos por una
   detección VIIRS375 nuestra el mismo día** (0 casos donde MODIS sea único) → apagar el MODIS
   contextual-only NO baja recall por evento. Verificado.
5. **Reportar el foco (max per-pixel) vs suma** acerca magnitud: Tupungatito 10.6×→2.4×,
   PCC 2.4×→1.4× (cota offline, A18).

**Display**: el chart ya separa por sensor; las MÉTRICAS (recall/precisión/ratio) se muestran
MEZCLADAS (un número global) → engañoso (mezcla MODIS 2.6% con VIIRS375 38%). MIROVA reporta
por sensor. VIIRS750 se grafica en las 3 vistas pese a que MIROVA no lo usa.

→ Diseño en `docs/superpowers/specs/2026-05-30-clon-mirova-por-sensor-design.md`.

## 7. ⚠️ CORRECCIÓN (fin de S93) — BUG del loader invalida la división VIIRS

**Nicolás detectó el error**: "MIROVA publica todos los sensores, no es que no use
VIIRS750 — detecta menos, igual que VIIRS375." Tenía razón. El loader
`mirova_csv_loader.normalize_sensor` mapeaba mal la etiqueta CSV **`VIIRS`** (a secas,
= M-band 750m) → la bucketizaba como **VIIRS375** (orden de `if` equivocado, regla A48:
heurística S86 no verificada contra el frontend). El CSV tiene 7185 filas `VIIRS`.

**Conteo CORRECTO de alertas MIROVA Tier A (CONS, VRP>0):**
| Sensor | Correcto | Lo que decía la tabla §6 (buggeado) |
|---|---|---|
| MODIS | 79 | 80 ✓ |
| VIIRS 375m | 627 | 787 ✗ |
| **VIIRS 750m** | **158** | **0 ✗✗** |

**Qué se INVALIDA de §6** (pendiente re-análisis sesión nueva): toda la división
VIIRS375 vs VIIRS750 (TP/FP/precisión/ratio por esos dos buckets). La conclusión #1
("MIROVA no usa VIIRS750") es **FALSA**.

**Qué SIGUE válido**: el diagnóstico raíz físico (Wooster sobre fondo gélido); la
conclusión **MODIS** (79 alertas, 77 Lascar → "solo ve lo grande"; el bug era del VIIRS,
no del MODIS); co-validación-solo-MODIS sigue como candidata (re-verificar recall por
sensor con datos correctos).

**Reparado en S93** (fix loader + revert F1): `normalize_sensor` corregido + test
`test_normalize_sensor_viirs_sin_sufijo_es_750` (TDD, suite 613 passed); F1 revierte la
exclusión de VIIRS750 (ahora se muestra como 3.er sensor en las métricas y el chart).
**Pendiente sesión nueva**: re-correr todo el análisis por-sensor con el bucketing
correcto y replantear F2–F5 con esos números. NO usar los números VIIRS de §6.
