# Caja de 5 × 5 km (D18): resultado de la ventana D1 (2026-10-15)

**Veredicto del pre-registro: KC NO CUMPLE (veto)**, en las lecturas A y B y con las cinco reglas de D-9.
Verificado por un verificador con contexto limpio (`verificador/INFORME.md`): CONFIRMADO como resultado del
pre-registro; la atribución causal, PARCIAL. El veto es definitivo según §7 del pre-registro: manda sobre D2,
V1 y cualquier mecanismo INDECIDIBLE.

## Qué pasó, primero en el volcán

Láscar, 2026-03-27 07:10 UTC, MODIS Aqua. MIROVA publica una alerta de 1,0 MW (protegida, en el filo del corte de
1 MW). Nuestro brazo K (sin Test 1, banda 22, conectiva `max`) la publica con un único píxel débil (0,14 MW, BT
269,9 K sobre un fondo de 268,98 K) que entra sólo por la recaptura del segundo pase. Ese píxel cae a **3,20 km al
este** del cráter: dentro del círculo de cumbre de 5 km, fuera de la caja de 2,5 km. Con la caja, la recaptura usa
el umbral estricto y el píxel se apaga. MIROVA ubica su alerta a 1,41 km de su centro de grilla, o sea dentro de su
propia caja con cualquier acimut, a 1,92 km o más de nuestro píxel. VIIRS 375 y 750: ninguna pérdida (10 protegidas
en cada sensor; no es una tasa).

## La causa es la posición del píxel MODIS, pero no D17 (hallazgo del verificador, SIN VERIFICAR el mecanismo)

En las 13 pasadas MODIS de K en esta ventana, el píxel del cráter aparece **corrido hacia el lado del sensor, y el
corrimiento crece con el ángulo de visión**: Aqua, acimut 100°: +1,1 km al este a 17°, +3,2 a 40°, +3,5 a 45°;
Terra, acimut -100°: -0,9 a -2,2 km (al oeste) a 31° y 32°. La otra pasada que KC pierde (03-14 07:05, Muy Bajo
0,97 MW, 45°) tiene la misma firma. Candidatos: la interpolación de la geolocación de 5 km a 1 km
(`_interp_geo`, `pipeline/process_modis.py:342`) o el paralaje de una cumbre de 5,6 km sobre el elipsoide. No es
D17, que trata del centro de grilla. El pre-registro acertó en «posición» y se equivocó de causa.

**Cómo leer el cierre:** la caja queda descartada para la réplica **con la geolocalización MODIS de hoy**. Si ese
corrimiento se corrige, el veto pierde su premisa y la caja se vuelve a medir (A111, A95).

## Corridas y archivos

- Primera corrida: run 38679191229. Dos cortes de NASA en el brazo caja (`SEARCH_CMR_TIMEOUT`, `502 Bad Gateway`)
  y un tercer intento con cobertura 132 contra 132. La recolección quedó roja por dos defectos del workflow, no de
  los datos: no puede volver a publicar la rama en un reintento, y en una ventana de un volcán cuenta como
  faltantes los otros diez.
- Repetición: run 38698329137, 132 records idénticos en los dos brazos salvo fechas y `regimen`.
- `evaluar_D1_sin_repeticion.txt`: PENDIENTE DE REPETICIÓN. `evaluar_D1_con_repeticion.txt` y `.json`: el veto.
- `verificador/`: informe y scripts (`pasada.py`, `geo.py`, `sesgo_modis.py`).

Límites: n = 13 pasadas en un solo volcán; ni la imagen de MIROVA ni el HDF revisados; `vent_lat` de
`volcanoes.yaml`.
