# S193 mapas: capa de agua y marca «pico sobre agua» en el tablero (2026-11-21)

Pedido de Nicolás (2026-11-21): «nosotros igual tenemos gente revisando las anomalías, sería bueno mejorar los mapas».
Sigue a la medición de la sesión de lagos (`experiments/_s193_lagos/INFORME.md`, PR #1075): el píxel más caliente cae
sobre agua en 124 de 14.391 pasadas de la vía, 35 en Laguna del Maule y 21 en Carrán-Los Venados.

Sólo display: no cambia ninguna detección, ningún valor publicado ni el nivel de alerta.

## Qué se midió antes de mostrar la marca

La capa del tablero (`frontend/agua/<Volcan>.geojson`, de `scripts/generar_capa_agua.py`) es la máscara JRC a 30 m
poligonizada, simplificada (tolerancia 0,0004°) y sin charcos de menos de 0,015 km², para que pese poco (1,97 MB los
43 volcanes, el mayor 180 KB). Hay que saber si esa simplificación cambia la clase de algún píxel frente a la máscara
que usó el informe de lagos.

| archivo | qué mide | resultado |
|---|---|---|
| `comparar_fraccion.py` → `comparar_fraccion.txt` | la capa con shapely, píxel por píxel contra `pixeles.csv` del informe de lagos | 41.988 de 41.989 píxeles en la misma clase; 1 marca de más (Sollipulli) |
| `comparar_js.js` → `comparar_js.txt` | lo mismo con el código que corre en el navegador (`frontend/agua.js`) | idéntico a shapely; 0,009 ms por píxel |

Con tolerancias mayores (0,0008°) la capa baja a 0,9 MB y la clase no cambia, pero la fracción se aparta hasta 0,33 en
algunos píxeles y el contorno se corre unos 90 m en el mapa; se eligió 0,0004°.

`pixeles.csv` no está en el repo (`experiments/_s193_lagos/`, se regenera con su `medir_agua.py`); la copia usada está en
`D:\vrp-trabajo\temporales\s193\lagos\pixeles.csv`.

## Verificación en el navegador (servidor local del worktree)

- Laguna del Maule: tarjeta, tabla, popup y nota de «Píxeles medidos» marcan las dos pasadas del 2026-11-20 (05:42
  NOAA-20 y 01:30 MODIS) con 100 % de la celda en agua; el contraste del pico contra el fondo es 8,2 K.
- Carrán-Los Venados: la pasada VIIRS 750 del 2026-11-12 05:36 (2,18 MW) cae sobre una laguna pequeña a 1,8 km del
  punto, 85 % de la celda; 1 de sus 2 píxeles sobre agua.
- Control, Láscar: 5 de 2.837 pasadas con el pico sobre agua, las 5 en clase lejana (18 a 23 km), igual que el informe
  de lagos; ninguna en la cumbre, ninguna marca en tabla ni tarjeta.
- Vista diaria y mosaico: cargan las capas de los 11 sin errores; ninguna marca (sus detecciones sobre agua son lejanas
  y estas vistas cuentan la cumbre). Control positivo con un record de Laguna del Maule: «💧 2 con el pico sobre agua».

## Qué no se hizo (contexto del operador, punto 3 del encargo)

El operador de MIROVA mira el mapa NTI (Coppola 2016a). El record de la vía no guarda el NTI ni el dNTI por píxel
(sólo `bt_k`, posición y la celda decisiva del cráter en `diag_codigo_mirova`), así que el tablero muestra el contraste
del pico contra el fondo (`bt_k − t_bg_k`, K), cuántos píxeles de la pasada caen sobre agua y la huella de cada uno.
El informe de lagos midió que ese contraste se solapa entre agua (mediana 10,0 K) y tierra (12,3 K): sirve de contexto,
no separa. Guardar el NTI por píxel tocaría `pipeline/` (A45).
