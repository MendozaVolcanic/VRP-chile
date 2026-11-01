# S157: dónde se va el tiempo de un job de reproceso (medición antes de cambiar nada)

Script: `experiments/_s157_busqueda_ventana/medir_tiempos.py`. Salidas: `medicion_salida.md` (cuatro jobs, detalle por
categoría) y `medicion_muestra.md` (una fila por job, 27 jobs de reproceso y 9 del NRT). Logs de los cuatro jobs del
detalle en `logs/`; los de la muestra se bajaron con `gh api repos/MendozaVolcanic/VRP-chile/actions/jobs/<id>/logs` y
la lista de ids está en `muestra_jobs.tsv` y `muestra_nrt.tsv`.

## 1. Los 51 min sin atribuir son la búsqueda de la geolocalización

Por cada día y cada plataforma, `fetch.fetch_for_volcano` hace DOS búsquedas a CMR: la del L1B, que tiene marcadores
(`SEARCH_START` / `SEARCH_DONE`), y la del producto de geolocalización (`MOD03`, `VNP03IMG`, ...), que no tiene
ninguno. Entre `SEARCH_DONE` y el marcador siguiente sólo corren el filtro nocturno (python sobre a lo más 5 gránulos)
y esa búsqueda.

El control lo confirma: en los 78 intervalos tras `SEARCH_DONE` en que NO hubo búsqueda de geolocalización (el L1B vino
vacío o el filtro nocturno dejó cero) el intervalo vale 0,0 s. Donde sí la hubo, vale lo mismo que la búsqueda del
L1B (mediana 8,0 s contra 7,2 s en el job de Chillán; 0,4 contra 0,4 s en los otros tres).

Job de Chillán (117669982883, 151,3 min): búsqueda L1B 41,4 min, búsqueda geo 44,9 min, búsquedas fallidas 9,0 min:
**95,4 min esperando a CMR (63 %)**. Procesamiento 39,0 min, descarga 14,6 min. Las líneas que imprime el procesamiento
salen sin flush y aparecen con la hora del marcador siguiente; por eso el procesamiento de un día no se puede partir
más fino que «del último marcador del día al primero del día siguiente».

## 2. Pero ese job es atípico: CMR tiene dos estados (y un tercero)

| estado de CMR | jobs | mediana por búsqueda | fracción del job esperando a CMR |
|---|---|---|---|
| rápido | 20 de 27 jobs de reproceso (18 a 20-oct) | 0,3 a 0,5 s | 5 a 17 % (mediana ~10 %) |
| lento | 2 de 27 (Chillán 19-oct 17:45 y 20-oct 03:22) y los 3 NRT de las 14:42 del 20-oct | 4,2 a 7,3 s | 45 a 63 % |
| caído | 5 de 27 (20-oct 08:11 a 08:31) y 6 de 9 NRT (08:11 y 12:11 del 20-oct) | sin respuesta | el job dura 0,2 a 10 min, sale **verde** y no trae ningún dato |

Con CMR rápido, la búsqueda por ventana ahorra 3 a 13 min por trozo de 37 días (lo que hoy cuestan sus ~590
búsquedas). Con CMR lento, ahorra la mayor parte de 30 a 95 min. En un trozo típico el tiempo se va en **procesar**
(55 a 70 %, ~75 s por día) y **descargar** (20 a 30 %), y eso no lo toca la búsqueda por ventana.

## 3. La pérdida silenciosa es mayor que la que se conocía

En los 5 jobs de reproceso con CMR caído, cada búsqueda devolvió `{"errors":["An Internal Error has occurred."]}` (HTTP
500). earthaccess lo levanta como `RuntimeError`, no como `Timeout`, así que NO pasa por el cortacircuito de S116: cae en
el `except Exception` de `fetch_for_volcano`, se imprime un `WARN: Failed to fetch` y la plataforma queda vacía.
Resultado: 152 fallas por job (19 días por 8 plataformas), job verde, cero records. Lo mismo en el NRT: 60 a 64 fallas
por job, verde. Es la misma pérdida de A108 por otro camino, y es el camino dominante en esta muestra.

## 4. Qué se puede esperar de cada parte del cambio

1. **Buscar una vez por ventana**: de ~590 búsquedas por trozo de 37 días a ~16 a 30 (16 productos, más los intentos
   de versión y de NRT que hagan falta). Ahorro: chico con CMR rápido, grande con CMR lento. Además baja en ~20 veces el
   número de veces que el job queda expuesto a una falla de CMR.
2. **Brazos en el mismo job**: cada brazo extra deja de buscar y de bajar (20 a 30 % del tiempo de su job); el
   procesamiento sigue siendo uno por brazo. Para un A/B de 3 brazos, del orden de 20 a 25 % menos minutos de runner con
   CMR rápido, más con CMR lento. A cambio el job es más largo, y para quedar bajo 170 min por paso hay que partir la
   ventana en trozos más cortos.
3. **Marcar el día que no se pudo buscar**: independiente del ahorro, y el hallazgo 3 lo vuelve lo más importante.

Veredicto de la medición: la búsqueda por ventana ahorra lo esperado (y más) en el estado lento de CMR, que es el del
log que motivó el cambio y el del NRT de la tarde del 20-oct; en el estado rápido ahorra poco (~10 % del job). No es
motivo para detenerse: el ahorro depende del estado de CMR, la reducción de exposición a fallas no, y la marca de
cobertura es necesaria en cualquier caso.
