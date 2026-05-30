# Design — Supresión display de artefactos cirrus físicamente incoherentes

**Fecha**: 2026-05-30 (S90). **Estado**: diseño + criterio validado empíricamente,
aprobado por Nicolás ("hagamos lo que recomiendes, que quede registro"). **Solo
frontend** (display) — NO toca pipeline/detección (A45 no aplica). Para revertir:
quitar el bloque de filtro en `frontend/index.html` (un solo lugar).

## 1. Problema

El dashboard muestra como detección summit valores de cientos a 1362 MW que MIROVA
no publicó y que son físicamente imposibles: artefactos del path D (dNTI contextual)
sobre cirrus alto frío (A23/D9, drift abierto). Auditoría S90: de 5538 records
mostrados (mirovaEqVrp>0), solo 1707 confirmados por MIROVA (CONS+OCR); 145 superan
20 MW y solo 14 están confirmados. Los picos PCC 1362/892 MW tienen el píxel más
caliente bajo cero (cima de nube, no lava).

## 2. Criterio (validado empíricamente, NO elegido a dedo)

Script: `experiments/_s90_display_artifact/test_criterion.py`. Métrica de seguridad:
de los records que el criterio ocultaría, ¿cuántos son detecciones MIROVA reales
(CONS+OCR, ±60min, mismo bucket)? DEBE ser 0.

| Criterio | oculta | MIROVA-conf atrapadas |
|---|---|---|
| t_max<273 K solo | 463 | **77** ❌ |
| **t_max<273 K & VRP>10 MW** | 26 | **0** ✓ |
| t_max<273 K & VRP>20 MW | 18 | 0 ✓ |
| t_max<268 K & VRP>10 MW | 10 | 0 (pierde 1362) |

**Criterio adoptado**: ocultar del gráfico si
**`t_max_k < 273.15 K` (0°C) Y `mirovaEqVrp(r) > 10 MW` Y `NOT _mirova_confirmed`**.

Razón física: una escena cuyo píxel MÁS caliente está bajo cero no tiene fuente
térmica; si aun así reporta >10 MW, ese VRP viene del kernel contextual sobre cirrus
uniforme (artefacto), no de calor real. El piso de 10 MW separa los artefactos
inflados de las detecciones faint reales (que tienen VRP bajo aunque su píxel sea
frío sobre nieve — las 77 confirmadas). Empíricamente, 0 detecciones MIROVA reales
caen en el criterio.

**Por qué NO usa `t_bg` (crítico, MISSION)**: usar `t_bg<260` sería replicar el gate
refutado S86 (mata la erupción real de Láscar bajo nube fría, que tiene t_bg frío
PERO t_max caliente). El criterio usa `t_max` (píxel más caliente), que distingue
"nube sin fuente" (t_max frío) de "lava bajo nube" (t_max caliente). Láscar-bajo-nube
tiene t_max>273 → NO se toca. NO es categoría (b): una feature volcánica real
(lacolito, lava lake) emite → su píxel está sobre cero.

## 3. Comportamiento (decisión Nicolás: ocultar del gráfico, conservar en tabla)

Patrón S18 ("ocultar far por defecto, no borrar — preservar evidencia"):
- **Gráfico VRP** (y VRE acumulada, scatter distancia): los records que matchean el
  criterio NO se grafican (no inflan la escala ni aparecen como picos).
- **Tabla de detecciones**: SE MANTIENEN, atenuados + etiqueta "artefacto cirrus"
  (preserva evidencia/trazabilidad).
- **Mapa**: el marker se atenúa/etiqueta como artefacto (NO se borra).
- **Métricas** (precision/recall): los artefactos no deberían contar como detecciones
  nuestras válidas → excluirlos del conteo de "shown" (mejora la precisión reportada
  hacia el valor real). [Verificar en implementación que no rompe computeMetrics.]

## 4. Implementación (frontend, TDD via preview)

- Helper JS `isCirrusArtifact(r, eqVrp)`: `eqVrp > 10 && r.t_max_k != null &&
  r.t_max_k < 273.15 && !r._mirova_confirmed`. Vive junto a `mirovaEqVrp`.
- Aplicar en: `toDailyMax`/buildDatasets (chart), distance scatter, VRE, overview
  map color, alert summary, latestDetection (card). En la tabla: NO excluir, marcar.
- Verificación: preview en navegador no-UTC (lección S89). Confirmar que el pico
  PCC 1362/892 desaparece del gráfico pero sigue en la tabla marcado; que Láscar y
  las detecciones reales NO se tocan.

## 5. Pre-mortem

- **t_max_k semántica por sensor**: MODIS=MIR B21/22; VIIRS puede ser I04/I05.
  Verificar que `t_max_k` represente el píxel caliente en la banda de detección.
  El criterio es conservador (VRP>10 + no-confirmado) → bajo riesgo aun si t_max_k
  varía de banda.
- **Robustez futura**: el "0 confirmadas atrapadas" se midió sobre data actual.
  Re-correr `test_criterion.py` si cambia el dataset MIROVA. Registro queda para
  ajustar umbral si aparece un caso real con t_max<273 & VRP>10 (entonces subir el
  piso de VRP, NO bajar a t_bg).
- **No es categoría (b)**: confirmado — el criterio exige t_max bajo cero, donde no
  hay feature volcánica real (que emite sobre cero).

## 5b. Resultado verificado (preview, S90)

`isCirrusArtifact` flaggea **26 records** (idéntico al test): PCC 15, Chaitén 3,
Copahue/Villarrica 2, Isluga/Lastarria/NdC/Tupungatito 1. Verificado en preview:
- PCC 1362 MW (t_max 272.8) y 892 MW (t_max 265.9) → `artifact=true` → removidos del
  gráfico. Chart max PCC: **1362 → 644.8 MW**.
- Record MIROVA-confirmado de control (t_max 290) → `artifact=false` (intacto).
- `latestDetection`, chart `eqVrp`, y `computeMetrics` `eqVrp` cablean el filtro.

**CAVEAT — valores altos WARM-scene quedan (fuera de scope)**: tras el filtro persisten
picos PCC de 645/338/222 MW con **t_max ≥ 273 K** (288/275/285) — tienen píxel caliente,
NO son cirrus. Causa probable: off-nadir MODIS área inflada (A36) o contextual sobre
terreno cálido, o señal real no-publicada (categoría b). Este criterio NO los toca a
propósito (no son físicamente incoherentes). Quedan como **investigación aparte** — NO
extender el criterio bajando t_max ni metiendo t_bg (gate refutado S86). El caso 338
(t_bg 243 cirrus, t_max 275) es borderline cirrus pero su píxel supera 0°C → conservador
lo deja; subir el umbral arriesgaría detecciones reales (validación lo mostró a 273).

## 5c. Implementado en v2 (S92)
- **Tabla**: los artefactos cirrus ahora se **atenúan** (`tr.row-cirrus-artifact td
  { opacity: 0.5 }`) y llevan el badge **"artefacto cirrus"** (con tooltip
  explicativo) en la celda de sensor; el VRP se pinta en `--muted` (no con color de
  alerta). Se conserva el record (trazabilidad). `buildNRTTable` evalúa
  `isCirrusArtifact(r, v.inner_radius_km ?? 10)` por record (innerKm per-volcán,
  crítico para PCC inner=20). Display-only, NO toca pipeline ni `mirovaEqVrp`.
- **Verificado en preview** (navegador del entorno): 26 artefactos en data (idéntico
  al criterio S90: PCC 15, Chaitén 3, Copahue/Villarrica 2, Isluga/Lastarria/NdC/
  Tupungatito 1). Render confirmado forzando un caso de prueba: filas artefacto
  opacity 0.5 + badge + VRP muted; filas normales opacity 1 + color de nivel; sin
  errores de consola. Nota: hoy 0 artefactos caen en la ventana de 7 días de la
  tabla → en producción solo se marcan cuando aparezca uno reciente.

## 6. Fuera de alcance

- NO toca pipeline/detección (los records se siguen generando/guardando).
- NO usa t_bg (gate refutado S86).
- NO cambia mirovaEqVrp ni clustering ni vent_anchored.
