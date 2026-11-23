# Latencia del NRT contra MIROVA, medición «después» (S196, E2a del camino de independencia)

Repite la medición «antes» de S150 (`experiments/_s150_latencia/`) con `first_processed_utc`, por sensor, por volcán y
por franja, para contestar la pregunta del operador del OVDAS de turno: **¿cuánto después del paso del satélite veo la
alerta?**

## Qué mide y de dónde sale cada hora

Para cada pasada de los 11 Tier A (`latencia.py`, docstring con el detalle):

| Tramo | Hora final | Fuente |
|---|---|---|
| NASA | producción del gránulo NRT | nombre del archivo (`.AAAADDDhhmmss.`); sólo records con gránulo NRT |
| repo | el runner del NRT escribió el record | `first_processed_utc` del record |
| commit | primer commit del JSON del volcán que contiene ese `first_processed_utc` | `git show` de cada commit (verificado, no supuesto) |
| tablero | término del primer despliegue exitoso de Pages creado después del commit | `pages_runs.json` (API de GitHub) |
| MIROVA | primera vez que el scraper Mirova-v1 vio la pasada en mirovaweb.it | `Fecha_Proceso_UTC` del consolidado, commit `90f64fcce` de Mirova-v1 |

Todas desde la adquisición (`datetime_utc` del record; `Fecha_Satelite_UTC` en MIROVA). Pareo con MIROVA como S150:
mismo volcán, misma familia de sensor, adquisición a 3 min o menos.

**Ventana declarada.** Noche: 2026-11-09 a 2026-11-22 (14 días UTC completos). MODIS de día: desde el merge de #1090
(2026-11-22 06:58:25 UTC, cuando el NRT empezó a procesar el día) hasta la corrida (2026-11-23 10:53 UTC): un solo día
de pasadas, 21. Los 158 records MODIS diurnos anteriores a #1090 entraron por relleno y quedan fuera; ningún record de la
ventana tiene `first_processed_utc` a más de 48 h, ninguno falta, todos son de origen `actions`, y los 1.232 tienen commit
y despliegue.

Correr: `python experiments/_s196_latencia/latencia.py --desde 2026-11-09 --hasta 2026-11-22 --hasta-dia-modis 2026-11-23
--bajar-pages --bajar-mirova --out <carpeta>` (el consolidado bajado no se guarda en el repo por tamaño; su sha está en
`resumen.json`). Salidas aquí: `resumen.json`, `pasadas.csv` (una fila por pasada), `pages_runs.json`.

## Resultado (horas desde el paso del satélite; mediana, y p10 a p90)

| Sensor y franja | Pasadas | NASA produce el gránulo | En el repo | En el tablero | Pareadas con MIROVA | VRP Chile (pareadas) | MIROVA por el scraper | VRP Chile menos MIROVA | VRP Chile llega primero |
|---|---|---|---|---|---|---|---|---|---|
| MODIS noche | 334 | 1,78 (0,70 a 1,92; n=66) | 2,08 | 2,31 (1,17 a 2,99) | 325 | 2,31 | 2,36 (1,19 a 3,19) | -0,05 (-1,25 a 1,02) | 170 de 325 |
| VIIRS 375 noche | 432 | 2,32 (1,84 a 2,47; n=113) | 2,62 | 2,86 (2,22 a 3,57) | 376 | 2,83 | 2,79 (2,45 a 3,15) | 0,00 (-0,58 a 0,73) | 183 de 376 |
| VIIRS 750 noche | 445 | 2,32 (1,84 a 2,47; n=119) | 2,62 | 2,84 (2,22 a 3,57) | 386 | 2,80 | 2,80 (2,49 a 3,10) | 0,00 (-0,57 a 0,53) | 200 de 386 |
| MODIS día | 21 | 1,09 (n=21) | 2,01 | 2,23 (1,28 a 4,81) | 21 | 2,23 | 1,69 (1,53 a 3,10) | 0,70 (-0,65 a 1,71) | 8 de 21 |

Por volcán (mediana del tablero contra MIROVA, `resumen.json` → `por_volcan`): de noche ningún volcán se separa más de
0,32 h (Isluga MODIS, 2,84 contra 2,52); de día la muestra es de 1 o 2 pasadas por volcán.

## Lectura para el operador del OVDAS

- **Hoy el turno ve la alerta de noche unas 2,3 h después del paso de MODIS y unas 2,8 h después del de VIIRS, lo mismo
  que por MIROVA a través del scraper.** La mediana de la diferencia por pasada es -0,05 h en MODIS y 0,00 h en VIIRS, y
  VRP Chile llega primero en cerca de la mitad de las pasadas (170 de 325, 183 de 376, 200 de 386).
- **La mayor parte de la espera es de NASA, no nuestra.** El gránulo NRT sale 1,8 h (MODIS) y 2,3 h (VIIRS) después del
  paso; desde ahí, esperar la corrida del NRT, bajarlo, procesarlo y publicarlo nos toma 0,62 h en mediana por pasada
  (0,44 a 0,46 hasta el repo; el resto es el commit y Pages), medido en las pasadas que aún tienen el nombre del gránulo
  NRT (66 MODIS, 113 VIIRS 375, 119 VIIRS 750). Lo que queda por ganar de nuestro lado es del orden de media hora.
- **Contra S150 la brecha se cerró.** Antes: VRP Chile 5,05 h, MIROVA 2,77 h, VRP Chile primero en 319 de 1.660
  (pasadas nocturnas del 2026-09-14 al 2026-10-02, misma definición del tablero y del pareo). No se atribuye aquí a qué
  cambio se debe (disparador externo del NRT y otros): SIN ATRIBUIR.
- **De día, MODIS todavía llega más tarde que MIROVA** (2,23 contra 1,69 h, VRP Chile primero en 8 de 21; del gránulo NRT
  al tablero, 1,13 h por pasada contra 0,62 de noche), pero es un solo día de datos: SIN CONCLUIR hasta juntar al menos
  dos semanas.
- **Criterio de E2a del camino** («la mediana de VRP Chile no supera la de MIROVA en una ventana de al menos dos semanas,
  por sensor»): de noche se cumple en MODIS (2,31 contra 2,36) y en VIIRS 750 (2,80 contra 2,80); en VIIRS 375 la
  mediana pareada de VRP Chile supera a la de MIROVA por 0,04 h (unos 2 min; 2,83 contra 2,79), aunque la mediana de la
  diferencia por pasada es 0,00. Por la letra, VIIRS 375 no lo cumple por dos minutos; el umbral sigue siendo SOSPECHA
  hasta que lo fije el OVDAS (paso 1 del §5).

## Salvedades

- La hora de MIROVA es la del scraper: cota superior de la latencia de mirovaweb.it (incluye el atraso del propio
  scraper). Es exactamente la latencia con que el OVDAS ve hoy a MIROVA, que es la comparación que importa para dejarlo;
  mirovaweb.it misma puede publicar antes (SIN MEDIR).
- La hora del tablero es el término del despliegue de Pages. Pages sirve los JSON con `Cache-Control: max-age=600`
  (cabecera leída el 2026-11-23), así que un navegador puede ver el dato hasta 10 min más tarde; no está sumado.
- VIIRS 375 y 750 salen de la misma corrida del NRT, por eso sus tramos nuestros son casi iguales.
- La hora de producción NASA sólo está en los records cuyo gránulo sigue siendo NRT (66 de 334 en MODIS, 113 y 119 en
  VIIRS); el resto ya pasó a estándar y su nombre de archivo es el del estándar.
