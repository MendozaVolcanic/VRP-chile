# Verificación PR #826 (corrimiento MODIS, tarea 1.15)

**Veredicto global: PARCIAL.** El defecto de código es real y su tamaño cuadra, pero tres afirmaciones están sobredichas.

1. **Convención: CONFIRMADO en el eje del barrido.** Data Dictionary C7, p. 66 (renderizada): offset 2 e increment 5 sobre `Max_EV_frames`. El offset a lo largo de la traza no está en el documento: SIN VERIFICAR. El sesgo asimétrico sale del barrido; la traza sólo dispersa (±2 líneas).
2. **Código: CONFIRMADO.** Una rampa pasada por `_interp_geo` real da 0,99778·s + 2,000. Del lado del frame 0: 1,00 km a 17°, 3,01 a 45°, 4,97 a 55°. Del otro lado: −0,09, 1,10 y 2,21.
3. **Medición: PARCIAL.** Reproduje 0,90 [0,80; 1,01] desde el CSV (igual con bootstrap por noche). `lado` concuerda con el acimut en las 91 pasadas. Defectos:
   - (a) El «coeficiente negativo» es del M3, donde el paralaje absorbe un tan z libre. El modelo invertido solo da +0,15 con rms 1,164 contra 0,937. Con desplazamiento fijo por volcán y satélite da +0,68 (rms 0,935 contra 0,914), y en Terra la asimetría libre no se distingue (1,41 contra 1,20). Lo que discrimina es el contraste este/oeste entre Aqua y Terra.
   - (b) Con un tan z simétrico libre, la interpolación sube a 1,20 [1,04; 1,34] y queda un residuo que se aleja del sensor, −0,77 [−1,06; −0,47]. El 0,90 depende del modelo.
   - (c) La fila M4 del README dice «+0,14 hacia el sensor», pero la columna es −h·tan z: ese +0,14 significa que se ALEJA.
   - (d) En producción con alerta, MODIS da −0,38 [−1,42; +0,70]: todo descansa en un brazo y casi un solo volcán.
   - Que el frame 0 quede a la derecha se infiere de los datos (SIN VERIFICAR en la documentación).
4. **Paralaje: CONFIRMADO para el término dominante.** La cumbre se aleja del sensor (sin corrección: 4,4 km a 40°, ausentes). El residuo de (b) tiene el signo del paralaje residual, así que no se puede descartar algo de paralaje.
5. **VIIRS: CONFIRMADO con matiz.** VIIRS usa VNP03IMG por píxel (`process_viirs.py:444`). Reproduje −0,058 [−0,102; −0,006] en 1.138 pasadas, pero en producción el Test 1 enmascara igual que en MODIS. El control comparable es el brazo K: +0,011 [−0,053; +0,070] en 345 pasadas.
6. **MIROVA: PARCIAL.** El CRS se lee del archivo y se deduplica por md5. La hora sale de `index.csv`: el TIF no la trae (revisé uno). Aqua tiene n = 15 y 11, Terra sólo 3 y 4, y el sesgo de Aqua al este sigue sin explicar.
7. **Consecuencias.** MxD03 se baja (`fetch.py:189-194,791-792`), se exige y se pasa (`run_pipeline.py:223-236`) y se ignora (`process_modis.py:470`): CONFIRMADO. Lo de la caja es PARCIAL: el 0,85 y el 0,69 aplican el modelo con coeficiente 1, ignoran la componente a lo largo de la traza y son píxeles débiles (0,7 y 0,9 K). La premisa del veto queda en duda, no refutada.
8. **Suite** sobre árbol quieto: 1765 passed, 6 skipped, 2 xfailed, `git status` limpio.

**Arreglos:**
- Corregir la fila M4.
- Sustituir el argumento del «coeficiente negativo» por la comparación de rms y el ajuste por satélite.
- Informar el modelo de 1,20 más el residuo.
- Declarar el nulo de producción.
- Usar VIIRS del brazo K como control.
- Rebajar el veto a «en duda».
- Correr el probe contra MxD03 antes de tocar `pipeline/` (A45).

**Defectos de esta verificación:** no bajé los runs (reajusté desde el CSV), no abrí ningún MOD021KM real y no rehice el análisis de los TIF.
