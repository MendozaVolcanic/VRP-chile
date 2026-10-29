# Costo de la sombra prospectiva de las vías «código MIROVA» (S167, 2026-10-29)

Medido antes de crear el perfil, como pide el programa por sensor (§12.5 punto 4: «medir ahora el costo en el tiempo
del NRT»). Lo no medido va como ESTIMADO o SOSPECHA.

## 1. Qué hace hoy el NRT (medido)

`medir_costo_nrt.py`, salida en `medir_costo_nrt_salida.txt`, filas en `tiempos_jobs.csv`:

| flujo | corridas | jobs | ventana (inicio de jobs, UTC) | paso del pipeline: mediana / p90 / máx | job: mediana / máx |
|---|---|---|---|---|---|
| NRT (`nrt.yml`) | 38 | 418 | 2026-10-27 06:10 a 2026-10-29 12:43 | 17,7 / 24,5 / 29,8 min | 19,3 / 32,1 min |
| `experimental-diario.yml` | 8 | 88 | 2026-10-21 18:19 a 2026-10-28 20:11 | 18,4 / 25,2 / 32,6 min | 20,0 / 34,8 min |

- Timeout del paso del NRT: 50 min; del job: 80 min.
- Cada job procesa 8 días (hoy y 7 atrás, `default_date_window`).
- Reparto de un job, Copahue de las 12:43 UTC del 2026-10-29 (`fases.py` sobre su log): 15,7 min buscando y
  bajando, 10,8 min procesando, 83 gránulos nocturnos (32 de VIIRS 375, 32 de VIIRS 750, 19 de MODIS). Es un solo job:
  el reparto de los demás no está medido.
- El NRT hoy corre **cada hora** (despachos a las :10 más el schedule de las horas pares), en el grupo `push-main`, y
  las corridas duran de 37 a 87 min de reloj (dos tandas de 8 jobs).

## 2. Qué cuesta la vía (medido en local, CPU)

`bench_via.py`, salida en `bench_via_salida.txt`. Grillas reales de VIIRS 375 (`tests/datos_s165_v375`) para el
detector y el fondo; para el remuestreo, un gránulo sintético de la forma real de cada sensor centrado en Villarrica.

| sensor | haversine del gránulo entero | remuestreo a la grilla de MIROVA | detector + fondo + record |
|---|---|---|---|
| VIIRS 375 (6464 × 6400) | 5,2 s | 11,5 s (incluye otra haversine entera) | 1,1 a 2,1 s con alertados; 0,03 s sin |
| VIIRS 750 (3232 × 3200) | 1,1 s | 2,4 s | no medido aparte (grilla de 67 × 67, menor que la de 375) |
| MODIS (2030 × 1354) | 0,3 s | 1,0 s | no medido aparte |

Por job de 83 gránulos como el de Copahue: unos 32 × 18 s + 32 × 4 s + 19 × 1,5 s ≈ **12 min de vía**, más la
lectura de los archivos, contra **10,8 min de proceso de K**. SOSPECHA: el runner puede ser más lento que este
computador; no está medido.

**Hallazgo**: la vía importa `pyproj` (`remuestrear_grilla`) y el NRT no lo instala. Con las vías encendidas en el NRT
tal como está, cada gránulo daría `ERROR processing` y no habría ningún record. El workflow de la sombra lo instala.

## 3. Dos formas de correr la sombra (ESTIMADO)

| forma | paso de la sombra | efecto en producción |
|---|---|---|
| Paso más dentro del job del NRT, compartiendo búsqueda y gránulos (`VRP_CONSERVAR_GRANULOS`, patrón de `reproc_brazos.py`) | unos 15 min por job, cada hora | cada job del NRT pasa de ~19 a ~34 min de mediana (peor caso ~45 a 50); cada corrida, unos 30 min más de reloj, con el NRT ya despachado cada hora: corridas pendientes del grupo `push-main` desplazadas y dato operacional más tarde |
| **Workflow aparte, una vez al día** (molde de `experimental-diario.yml`, grupo propio) | lo que tarda experimental-diario más ~4 min de vía sobre K: mediana ~22 min, peor job 37 a 45 min | ninguno: grupo de concurrencia propio, 4 jobs a la vez, push con reintento |

Nicolás eligió el workflow aparte (2026-10-29, en el chat de esta sesión). Paso con timeout de 60 min (A15: 1,3 × 45),
job de 80.

## 4. Antes de encender

El costo en el runner no está medido. El workflow tiene un modo `medir=true` (despacho a mano, ventana pasada, no
commitea) para medirlo sobre uno o dos volcanes antes del sí de encendido; si el peor job pasa de 45 min, se sube el
timeout o se parte la matriz antes de ponerle schedule.
