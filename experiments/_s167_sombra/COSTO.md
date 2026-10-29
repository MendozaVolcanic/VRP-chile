# Costo de la sombra prospectiva de las vías «código MIROVA» (S167, 2026-10-29)

Medido antes de crear el perfil, como pide el programa por sensor (§12.5 punto 4: «medir ahora el costo en el tiempo
del NRT»). Lo no medido va como ESTIMADO o SOSPECHA.

## 1. Qué hace hoy el NRT (medido)

`medir_costo_nrt.py`, salida en `medir_costo_nrt_salida.txt`, filas en `tiempos_jobs.csv` (agregado con `git add -f`: `*.csv` está en `.gitignore`):

| flujo | corridas | jobs | ventana (inicio de jobs, UTC) | paso del pipeline: mediana / p90 / máx | job: mediana / máx |
|---|---|---|---|---|---|
| NRT (`nrt.yml`) | 38 | 418 | 2026-10-27 06:10 a 2026-10-29 12:43 | 17,7 / 24,5 / 29,8 min | 19,3 / 32,1 min |
| `experimental-diario.yml` | 8 | 88 | 2026-10-21 18:19 a 2026-10-28 20:11 | 18,4 / 25,2 / 32,6 min | 20,0 / 34,8 min |

- Timeout del paso del NRT: 50 min; del job: 80 min.
- Cada job procesa 8 días (hoy y 7 atrás, `default_date_window`).
- Reparto de un job, Copahue de la corrida 40871093208 (jobs desde las 12:43 UTC del 2026-10-29; `fases.py` sobre su
  log, salida en `fases_salida_copahue_40871093208.txt`): 15,7 min buscando y bajando, 10,8 min procesando, 83
  gránulos nocturnos (32 de VIIRS 375, 32 de VIIRS 750, 19 de MODIS). Es un solo job: el reparto de los demás no está
  medido.
- Cadencia (`corridas_nrt_20261029.txt`, las 30 corridas más recientes al 2026-10-29 17:19 UTC): además del schedule,
  hay despachos a las :10 de cada hora durante parte del día (12 el 2026-10-29, de las 01:10 a las 12:10 UTC), todos en
  el grupo `push-main`; las 28 corridas verdes duraron de 31 a 91 min de reloj (dos tandas de 8 jobs).
- El peor job histórico que cita `nrt.yml` es de 56 min (Villarrica, 2026-09-02): la muestra de arriba es de dos días
  y no lo contiene.

## 2. Qué cuesta la vía (medido en local, CPU)

`bench_via.py`, salida en `bench_via_salida.txt`. Grillas reales de VIIRS 375 (`tests/datos_s165_v375`) para el
detector y el fondo; para el remuestreo, un gránulo sintético de la forma real de cada sensor centrado en Villarrica.

| sensor | haversine del gránulo entero | remuestreo a la grilla de MIROVA | detector + fondo + record |
|---|---|---|---|
| VIIRS 375 (6464 × 6400) | 5,2 s | 11,5 s (incluye otra haversine entera) | 1,1 a 2,1 s con alertados; 0,03 s sin |
| VIIRS 750 (3232 × 3200) | 1,1 s | 2,4 s | no medido aparte (grilla de 67 × 67, menor que la de 375) |
| MODIS (2030 × 1354) | 0,3 s | 1,0 s | no medido aparte |

Por job de 83 gránulos como el de Copahue (ESTIMADO, multiplicación a mano de las cifras de arriba): unos 32 × 18 s + 32 × 4 s + 19 × 1,5 s ≈ **12 min de vía**, más la
lectura de los archivos, contra **10,8 min de proceso de K**. SOSPECHA: el runner puede ser más lento que este
computador; no está medido.

**Hallazgo**: la vía importa `pyproj` (`remuestrear_grilla`) y el NRT no lo instala (no está en la lista de paquetes instalados del log del job de Copahue de la corrida 40871093208). Con las vías encendidas en el NRT
tal como está, cada gránulo daría `ERROR processing` y no habría ningún record. El workflow de la sombra lo instala.

## 3. Dos formas de correr la sombra (ESTIMADO)

| forma | paso de la sombra | efecto en producción |
|---|---|---|
| Paso más dentro del job del NRT, compartiendo búsqueda y gránulos (`VRP_CONSERVAR_GRANULOS`, patrón de `reproc_brazos.py`) | unos 15 min por job, cada hora | cada job del NRT pasa de ~19 a ~34 min de mediana (peor caso ~45 a 50); cada corrida, unos 30 min más de reloj, con el NRT ya despachado cada hora: corridas pendientes del grupo `push-main` desplazadas y dato operacional más tarde |
| **Workflow aparte, una vez al día** (molde de `experimental-diario.yml`, grupo propio) | experimental-diario (K, mediana 18,4, máximo 32,6) menos el proceso de K (10,8) más la vía (~12) y la lectura de los archivos: ESTIMADO mediana ~20 a 22 min, peor job 37 a 45 min si el runner es hasta 1,5 veces más lento | ninguno: grupo de concurrencia propio, 4 jobs a la vez, push con reintento |

Nicolás eligió el workflow aparte (2026-10-29, en el chat de esta sesión). Como el costo en el runner no está medido,
el timeout no se ancla a la estimación sino al peor job observado del NRT (56 min): paso de 75 min (A15: 1,3 × 56 = 73)
y job de 100 (hallazgo 2 del verificador).

Un job puede quedar verde sin medir nada: `run_pipeline.py` atrapa toda excepción por gránulo y sale 0. Por eso el
workflow termina con `scripts/revisar_sombra.py`, que deja el job rojo si hubo `ERROR processing`, si algún record de
la ventana no es de la vía (`via_codigo_mirova` distinto de true: cayó a K) o si no hay ningún record de la vía
(hallazgo 1 del verificador).

## 4. Antes de encender

El costo en el runner no está medido. El workflow tiene un modo `medir=true` (despacho a mano, ventana pasada, no
commitea) para medirlo sobre uno o dos volcanes antes del sí de encendido; si el peor job pasa de 45 min, se sube el
timeout o se parte la matriz antes de ponerle schedule.

Lo que sólo ese despacho puede comprobar: el camino completo de MODIS (pyhdf no corre en Windows) y el de VIIRS 750
sobre gránulos reales. La prueba de punta a punta de `tests/test_sombra_codigo_mirova_s167.py` ejercita VIIRS 375; de
los otros dos sólo comprueba que el volcán tenga grilla (hallazgo 4 del verificador).

Efecto lateral al encender (hallazgo 6): cada commit de la sombra toca `data/**` y dispara `pages-deploy.yml`, que
copia `data/` entera al sitio público. Son hasta 11 despliegues más al día y la carpeta queda publicada aunque el
tablero no la lea, igual que hoy `data/experimental_v2/`.
