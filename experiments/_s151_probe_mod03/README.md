# Probe S151: geolocalización MODIS de `_interp_geo` contra MxD03 (tarea 1.15)

**Estado: escrito, probado con datos sintéticos, NO corrido.** Este README fija el criterio antes de la
primera corrida.

## Resultado (run 38733452917, 2026-10-15; verificador limpio PARCIAL, `resultado/`)

**Veredicto del criterio pre-registrado: PARCIAL.** La condición 2 se cumple (en el lado del frame 0 con cenit de 30° o
más, nuestra posición se aparta de MxD03 2,58, 2,21 y 1,15 km hacia el sensor) y no hay ninguna de REFUTA, pero la
condición 1 falla en dos gránulos (residuos +0,36 y -0,45 km contra la tolerancia de 0,3).

- **El defecto existe y la grilla lo dice sola:** la geolocalización de 5 km del L1B coincide con MxD03 en el offset 2,
  en los dos ejes y en los 7 gránulos (0,0000 km), contra 2,6 km en el frame 0 y 2,27 km en la línea 0. El offset 2 a lo
  largo de la traza, que el PR #826 dejó SIN VERIFICAR, queda confirmado.
- **Por qué el modelo no calza exacto** (compatible, no medido): `_interp_geo` trae el terreno sólo en los nodos de 5 km;
  el relieve de 300 a 450 m a escala de 1 km por tan θ da 0,2 a 0,45 km con el signo observado; el de 43° es el único
  donde la interpolación cruza entre barridos (bow tie), lo que explica su traza.
- **Control independiente:** en los 3 gránulos donde el píxel más brillante de banda 22 cae en el cráter, MxD03 lo
  ubica a 0,13, 0,18 y 0,35 km del vent y `_interp_geo` a 1,29, 1,02 y 1,10 km.
- **Consecuencia:** leer MxD03 queda justificado, calce o no el modelo; corregir sólo el offset del zoom dejaría 0,2 a
  1 km por terreno y bow tie. La caja (D18) mantiene el veto con su premisa «en duda» y se vuelve a medir después del
  arreglo. SIN VERIFICAR: otros volcanes y la posición MxD03 del píxel del veto.

## Por qué

El estudio del PR #826 (`experiments/_s151_corrimiento_modis/`) encontró que, en MODIS, el píxel del
cráter de Láscar sale corrido hacia el sensor. Atribuyó el corrimiento a `_interp_geo`
(`pipeline/process_modis.py:342`).

- **El mecanismo.** `_interp_geo` estira la grilla de 5 km de MxD021KM con un `zoom` que alinea los
  extremos, cuando el primer punto grueso es el frame 2 (MODIS L1B Data Dictionary C7, p. 66).
- **El verificador con contexto limpio** confirmó el defecto de código: el frame *s* recibe la posición del
  frame 0,99778·s + 2,000.
- **Su efecto sobre el cráter** está medido en un solo brazo de A/B y casi un solo volcán, y su tamaño
  depende del modelo de ajuste.

MxD03 trae la posición de cada píxel de 1 km, corregida por terreno. El pipeline ya la baja y no la lee.
Comparar las dos geolocalizaciones en el mismo gránulo decide la pregunta sin depender de que haya un foco
térmico.

## Qué hace

Baja 7 pares MxD021KM + MxD03 de Láscar (los 14 archivos están en CMR, consultado el 2026-10-15) y compara
las dos geolocalizaciones píxel a píxel:

| gránulo | satélite | lado de la traza | cenit | nota |
|---|---|---|---|---|
| A2026073.0705 | Aqua | lado del frame 0 | 44,6° | pasada del veto de la caja |
| A2026086.0710 | Aqua | lado del frame 0 | 39,9° | pasada del veto de la caja |
| A2026074.0745 | Aqua | otro lado | 30,5° | |
| A2026113.0800 | Aqua | otro lado | 43,2° | |
| A2026078.0155 | Terra | lado del frame 0 | 31,2° | |
| A2026075.0135 | Terra | otro lado | 10,4° | |
| A2026077.0115 | Terra | otro lado | 46,8° | |

En cada gránulo, el probe toma el píxel MxD03 más cercano a `vent_lat/vent_lon`, mide la diferencia
`_interp_geo` menos MxD03 y la descompone:

- **A lo largo del barrido.** Se compara con lo que predice la regla 0,99778·s + 2: la posición MxD03 del
  frame fraccionario contra la del frame *s*.
- **A lo largo de la traza.** Se compara con la regla análoga para las líneas.
- **Hacia el sensor.** Con el acimut del sensor que trae MxD03.

Además informa tres cosas:

- la mediana del residuo en una ventana de 15 km;
- con qué offset (0 a 4) los puntos gruesos de L1B coinciden con MxD03 en cada eje;
- si el frame 0 queda a la derecha de la traza, y dónde cae el píxel más brillante en banda 22 con cada
  geolocalización.

## Criterio (fijado antes de correr)

- **CONFIRMA** si se cumplen las dos condiciones:
  1. En los 7 gránulos, la diferencia a lo largo del barrido en el píxel del cráter coincide con la
     predicha dentro de 0,3 km.
  2. En los gránulos del lado del frame 0 con cenit de 30° o más, esa diferencia es de 1,0 km o más hacia
     el sensor.
- **REFUTA** si se da cualquiera de estas dos:
  1. La diferencia total en el píxel del cráter queda bajo 0,3 km en los 7 gránulos.
  2. Su signo contradice al predicho en algún gránulo donde la predicción pasa de 1 km.
- **PARCIAL** en cualquier otro caso. **INCOMPLETO** si falta un gránulo; el script sale entonces con
  código 2.

Hay cosas que se informan pero no entran al veredicto, y que el PR #826 deja SIN VERIFICAR: el offset a lo
largo de la traza, el lado del frame 0 y el píxel brillante.

## Prueba del instrumento

`probar_probe.py` arma un barrido sintético con geometría de espejo a 705 km y corre el núcleo `comparar`
con la `_interp_geo` real. Hay que mostrar que el instrumento puede dar cada resultado (A116):

| caso | grilla gruesa | qué debe salir | qué sale |
|---|---|---|---|
| 1 | tomada con la convención documentada | CONFIRMA | **CONFIRMA**: a 45° del lado del frame 0 mide +3,00 km contra +3,01 predichos; detecta el frame 0 a la derecha y el offset 2 en los dos ejes |
| 2 | tomada donde el zoom la pone, o sea sin defecto | REFUTA | **REFUTA**: diferencias bajo 0,01 km |

El workflow corre esta prueba antes del probe.

## Cómo correrlo

```
gh workflow run probe-s151-mod03.yml --ref main -f preregistro_aprobado=si
```

Sólo con el criterio sellado. El workflow tiene que estar en `main`: `workflow_dispatch` no corre desde
una rama.

- **Autenticación:** sólo con `EARTHDATA_TOKEN`, y falla al instante si viene vacío (A71).
- **Concurrencia:** grupo propio.
- **Salida:** no hace push. El resultado queda en el artefacto `s151-probe-mod03` (`probe_mod03.json`,
  `probe.log` y `prueba_sintetica.txt`).
