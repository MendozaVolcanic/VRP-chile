# F48 — Refs MIROVA Llaima / Copahue (S77 M2)

## TL;DR

`data/mirova/Llaima.json` y `data/mirova/Copahue.json` estaban vacíos (`records: []`).
La causa NO es scraper roto ni filtro mal: **MIROVA realmente no emite alertas
térmicas para estos 2 volcanes en la ventana scrapeada** (~1730 muestras por
volcán sobre ~6 meses, 99.94% clasificadas `NULO`). Después del rebuild contra el
snapshot histórico (`mirova_v1_snapshot/registro_vrp_consolidado.csv`, 17,966
filas) ambos quedan con **1 sola detección** cada uno (`Muy Bajo`, VIIRS375).

Esto es **dato científico real, no gap operacional**: durante el período cubierto
Llaima y Copahue están térmicamente quietos según MIROVA. El dashboard ya puede
graficar la línea ref (aunque trivial), y futuros eventos térmicos se acumularán
automáticamente vía cron del scraper Mirova-v1.

## Auditoría de causa raíz

Script: `experiments/142_m2_llaima_copahue/audit.py`.

### Conteo por clasificación (latest_consolidado.csv, 15,176 filas)

| Volcán | NULO | Muy Bajo | Bajo | FALSO POSITIVO | Total |
|---|---:|---:|---:|---:|---:|
| Llaima | **1,463** | 0 | 0 | 0 | 1,463 |
| Copahue | 1,475 | 1 | 0 | 2 | 1,478 |
| Lascar | 1,047 | 84 | 163 | 0 | 1,294 |
| Lastarria | 1,211 | 74 | 3 | 1 | 1,289 |
| Chaiten | 1,554 | 15 | 0 | 1 | 1,570 |
| Villarrica | 1,466 | 4 | 2 | 0 | 1,472 |
| Isluga | 1,149 | 71 | 2 | 0 | 1,222 |
| Tupungatito | 909 | 70 | 0 | 0 | 979 |
| Puyehue-Cordon Caulle | 1,433 | 81 | 8 | 0 | 1,522 |
| Nevados de Chillan | 1,453 | 3 | 1 | 8 | 1,465 |
| PlanchonPeteroa | 1,322 | 35 | 0 | 0 | 1,357 |

Solo `Muy Bajo` y `Bajo` son detecciones térmicas reales según MIROVA (lección
L7.10 en `rebuild_mirova_from_consolidado.py`). `NULO` significa MIROVA evaluó
la captura y rechazó: no hay anomalía térmica significativa.

### Sobre el snapshot histórico (17,966 filas)

| Volcán | NULO | Muy Bajo | Bajo | FALSO POSITIVO |
|---|---:|---:|---:|---:|
| Llaima | 1,729 | 1 | 0 | 0 |
| Copahue | 1,736 | 1 | 0 | 2 |

Sumando la única `Muy Bajo` por volcán que sí existe en historia más larga,
quedan los `data/mirova/<Volcano>.json` con 1 record cada uno.

### Detecciones recuperadas

- **Llaima 2026-05-15 06:24 UTC** — VIIRS375, VRP=0.08 MW, distancia=1.88 km del
  vent, clasificación `Muy Bajo`.
- **Copahue 2026-04-22 05:12 UTC** — VIIRS375, VRP=0.21 MW, distancia=3.69 km del
  vent, clasificación `Muy Bajo`.

Magnitudes consistentes con el rango bajo (~0.05-0.5 MW) que MIROVA típicamente
clasifica `Muy Bajo` (señal sub-pixel, candidato a ruido pero respaldado por
otros sensores en la ventana).

## Físicamente, por qué Llaima/Copahue tienen tan pocos alertas

Ambos están actualmente en quietud térmica:

- **Llaima**: último ciclo eruptivo significativo ~2008-2009 (Coppola 2016b
  catalog). Desde ~2010 sin emisión persistente de lava o gases calientes a
  niveles VRP MIROVA-detectable. Cráter cubierto de nieve/hielo gran parte del
  año. La señal térmica residual del sistema fumarólico está debajo del piso
  VIIRS 375m sub-pixel (~0.05 MW).
- **Copahue**: actividad de degassing pasivo + lago cratérico ácido (40-60°C)
  desde 2014 — calor sensible bajo el umbral MIR/TIR MIROVA. Episodios
  estrombolianos cortos (2015, 2020) sí dispararon refs pero fuera del scrape
  de Mirova-v1.

Esto contrasta con Tier A térmicamente activos hoy:
- Lascar (lago de lava intermitente, 247 refs MIROVA confirmadas)
- Lastarria (campo fumarólico hot 77 refs)
- Puyehue-Cordón Caulle (~89 refs, residual post-2011)

## Decisión operacional

1. **Recuperación aplicada** (1 ref cada volcán): los JSONs ahora tienen 1
   record cada uno; el dashboard puede levantar la línea ref aunque sea trivial.
2. **No tratar como bug** — el bajo conteo refleja la física, no un problema de
   pipeline. Auditorías recall/precision contra estos 2 volcanes en S77+ no
   tienen señal estadística suficiente y deben reportarse como N/A.
3. **Re-correr el rebuild contra `latest_consolidado.csv`** mensualmente cuando
   Mirova-v1 publique snapshot fresco. Si MIROVA detecta nueva actividad en
   Llaima/Copahue automáticamente cae a `Muy Bajo`/`Bajo` y aparece acá.

## Fix script secundario

`scripts/rebuild_mirova_from_consolidado.py` apuntaba a un CSV hardcoded ya
borrado (`14042026 registro_vrp_consolidado.csv`). Ahora:
- Default source = `latest_consolidado.csv` (repo root, cron-refreshed).
- Flag `--source PATH` para apuntar a snapshot histórico u otro CSV.

Sin este fix, el script directamente fallaba con `FileNotFoundError`.

## Próximos pasos

- [ ] Spot-check `NevadosDeChillan` y `PuyehueCordonCaulle` JSONs (en CSV están
  como `Nevados de Chillan` y `Puyehue-Cordon Caulle` — name mapping) — probable
  caso similar de stale rebuild. **Fuera del scope de F48** pero anotar.
- [ ] Considerar agregar metadata `n_nulo_observations` en cada JSON para
  comunicar al dashboard que MIROVA observó pero rechazó (vs no observó), útil
  para distinguir "volcán quieto" de "volcán no monitoreado".
- [ ] Si futuro reproceso operacional sobre Llaima/Copahue muestra recall trivial
  (0 ó 1 sobre 1 ref), reportar explícitamente N/A en métricas — no manchar
  agregados globales.
