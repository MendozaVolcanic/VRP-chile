# Verificador con contexto limpio: deriva de los 8 records MODIS (tarea 1.23 bis)

Sólo lectura sobre `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile` (rama `loop/activo`,
HEAD `46d9ac96d`, que no es el `656ff67bf` del informe: el corpus creció, los conteos se rehicieron sobre
este HEAD). Scripts y salidas en `C:\Users\nmend\AppData\Local\Temp\claude\verif_deriva\`. Informe
verificado: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s153_deriva_123bis\INFORME.md`.

## Veredicto: CONFIRMADO en lo central, con dos correcciones y tres puntos SIN VERIFICAR

La tesis (los 8 records y otros 3.231 MODIS de enero a junio de 2026 quedaron escritos con los gates
intra-radio encendidos y nunca se reescribieron) resiste los tres intentos de refutación que hice, dos de
ellos independientes de la datación por historia git y de la sonda de hoy. Correcciones: la fecha de
última escritura de 3 de los 8 está mal (sin consecuencia), y la mezcla de detectores tiene **dos**
fronteras, no una.

## 1. Fechas de los flags, leídas como las lee el código

Evalué `pipeline.profile` (`VRP_PROFILE=mirova_equivalent`, `python -I`) sobre `pipeline/profile.py` +
`pipeline/profiles/` extraídos con `git archive <sha> <rutas>` en cada commit. Las claves se leen de la
sección `paths:` (`pipeline/profile.py:131`, `:154`, `:170`), no de la raíz (A89 descartada).

| commit | fecha | camino D | segundo pase |
|---|---|---|---|
| `eb68f8c4c` (#224) | 2026-05-26 17:52 UTC | False | no existe |
| `752aed06c` (#226) | 2026-05-28 04:44 UTC | **True** | no existe |
| `958a226e3` (#227) | 2026-05-28 05:57 UTC | True | False |
| `60de1bb27` (#229) | 2026-05-28 16:39 UTC | True | **True** |
| `a271cd552`, `3c37c6e79` | 06-01, 06-06 | True | True |
| `92fc4412c~1` | 2026-07-01 20:30 UTC | True | True |
| `92fc4412c` (#474) | 2026-07-01 20:46 UTC | **False** | **False** |
| HEAD | 2026-10-18 | False | False |

`git log -G` sobre las dos claves no da otro cambio. Los perfiles con que se generaron las dos
promociones también tienen los dos gates en True: `_s94_reproc_modis` (hereda `mirova_equivalent`, la
fuente MODIS de `a271cd552` según su mensaje) y `_s102_nadir_promote` (el de `3c37c6e79`). El diff de #474
dentro de `pipeline/` es sólo el YAML.

Barrí además **todas** las constantes de `pipeline.profile` en el último commit antes del gate, en
`a271cd552`, `3c37c6e79`, antes y después del flip y en HEAD (`dump_profile.py`). Las únicas que están
encendidas dentro de la ventana y apagadas tanto antes como después son los dos gates. Todo lo demás
cambió en un solo sentido y sigue igual hoy. Ese es el descarte de confusores por flag.

## 2. Datación de los 8 records

La bisección del investigador compara 5 campos y supone que el valor final no aparece, desaparece y
vuelve. La rehice como barrido lineal sobre **todos** los commits no NRT que tocaron cada JSON desde el
2026-05-25 y una muestra de 1 cada ~40 NRT, con firma rica (10 campos de detección + hash de
`anomaly_pixels`) (`escan8.py`, `escan8.log`). Resultado:

- Ninguno de los 8 cambia en ningún commit posterior al 2026-06-06 (pasan intactos S106, S110, S120,
  S122 geometría, #571, #588, #594, `ab76888cf`). Ninguno se reescribió después del flip: CONFIRMADO.
- **Corrección**: Chaitén 04-28, Isluga 05-09 e Isluga 05-19 se escribieron por última vez en
  `3c37c6e79` (2026-06-06, nadir fijo MODIS), no en `a271cd552`. En `3c37c6e79` cambiaron
  `diag_n_dnti_ctx_path` y `anomaly_pixels` pero no los 5 campos de la bisección. Sigue siendo ventana
  con gates encendidos, así que la conclusión no cambia; pero la advertencia de la corrida mínima
  («cuatro de los 8 son anteriores a nadir fijo») vale sólo para **Llaima 03-11**.

## 3. ¿Las pruebas miden lo que dicen? Tres controles

Reproduje las salidas: 247 de 250 contra 217 de 218, y 49 de 56 en la aritmética. El riesgo es que
«escrito en la ventana» coincide con «observado de enero a junio de 2026», así que cualquier cosa propia
de ese periodo (colección del L1B, estación, #535) daría el mismo cuadro. Tres controles:

**(a) Firma estructural del gate, sin historia git ni sonda** (`corpus_v.py`). Con el gate del segundo
pase encendido, ningún píxel fuera del `inner_radius_km` puede venir del segundo pase, así que los
píxeles listados fuera del inner (distancia al vent de `volcanoes.yaml`) no pueden superar al primer
pase. Sin PCC:

| clase (HEAD) | records | listados fuera del inner > primer pase |
|---|---|---|
| ventana del gate | 2.869 | **1** |
| posterior al flip | 8.742 | 5.319 |

Si los 3.231 se hubieran escrito sin gate, más de la mitad violaría la cota.

**(b) Experimento natural en el flip** (muestra de 470). El código de `pipeline/` a los dos lados del
2026-07-01 20:46 difiere sólo en los dos flags. Escritos por el NRT del 06-07 al flip: 37 de 38 salen hoy
con más píxeles (el que no, Copahue 06-24, tiene 1 píxel y 0 recapturados). Escritos del flip al 07-31: 30
de 30 idénticos. Misma estación, mismo código salvo los flags.

**(c) #535 descartado** para estos conteos: escritos después del flip y antes del 2026-08-28 23:00, 135 de
135 idénticos hoy; después, 82 de 83 (el distinto es el Láscar `nrt`).

La aritmética 49 de 56 es un control propio: el código de mayo y el de hoy coinciden, sólo la ventana
difiere. Vale sólo para los 56 con primer pase previo comparable; en los 195 con versión previa al gate,
142 no coinciden porque esa versión es de código pre S97.

## 4. Conteo del corpus y VIIRS

Rehecho con snapshots `--first-parent` (dan los mismos commits) y con firma rica: **3.231** MODIS con
píxeles en la ventana, idéntico con las dos firmas. Todos `standard`, sin `processed_utc`, observados del
2026-01 al 2026-06 (67, 585, 656, 626, 655, 642), 10 volcanes, Villarrica 0. Por mes de observación, sin
Villarrica, enero a junio de 2026 es ventana en el 99,6 % (23 posteriores en junio).

**Corrección**: el 2025 lo escribió el backfill S120 **después** del flip. Toda serie MODIS que cruce el
**2025-11/2026-01** también mezcla los dos detectores, no sólo la que cruza el 2026-07-01.

VIIRS: conteo reproducido (2.563 + 1.953). La firma estructural casi nunca se viola en VIIRS ni sin gate
(V375 13 de 6.276, V750 126 de 3.721 posteriores). Por eso la prueba tiene poco poder ahí. Esas cifras son
un piso de cuántos records cambiarían: si la deriva VIIRS existe es chica, pero no está medida. SIN VERIFICAR.

## 5. Publicaciones que cambiarían (muestra, predicado del tablero)

`pub_muestra.py`: publicación de cada record guardado recalculada hoy con `banco_paridad.correr_node`
(coincide con `pub_guardada` en los 470), contra la publicación del brazo C de la sonda 1.17, que la
calculó con el mismo predicado. En los 250 escritos con gate: **8 cambian `distance_class` y 5 cambian
publicación**. Se encienden 3 (Isluga 05-09, 05-18, 05-19) y se apagan 2 (Chaitén 03-06, 04-28). Los 8 son
negativos limpios y ninguno es protegido. Neto en la muestra: una publicación falsa más. En los 218
posteriores al flip: 0 cambios. La muestra está estratificada (los cambios caen en los estratos A y
B_summit), así que extrapolarlo a los 3.231 queda SIN VERIFICAR.

## SIN VERIFICAR

- La corrida con los gates encendidos que reproduzca lo guardado: diseñada, no corrida. MODIS no corre
  en Windows (pyhdf).
- Que los píxeles de diferencia caigan todos fuera del inner: la sonda no guarda listas de píxeles.
- Cuál de los dos gates explica qué parte de la diferencia.
- La deriva VIIRS, y las publicaciones en el corpus completo.
