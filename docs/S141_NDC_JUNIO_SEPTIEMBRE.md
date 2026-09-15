# Nevados de Chillán, junio a septiembre de 2026: actualización S141 del análisis S124

Actualiza `docs/S124_NDC_FOCO_JUNIO_AGOSTO.md` (se conserva como historia) con lo aprendido entre S125 y
S141. Figuras y números: `experiments/_s141_ndc/` (`ndc_s141.py` escribe `ndc_s141.json`;
`regimen_535.py` escribe `regimen_535.json`; `mirova_pagina_20260915.json` guarda lo leído en la página de
MIROVA). Ningún número de este documento está escrito a mano fuera de esas salidas (regla S91).

## 1. Lo que hace el volcán

El cráter Nicanor mantiene un foco caliente muy débil, de centésimas de MW, que a 375 m ocupa uno o dos
píxeles y compite con una cumbre nevada que de noche queda más fría que los valles. MIROVA lo publicó
como alerta en el cráter cinco noches entre junio y septiembre (16 de junio; 18 y 20 de agosto; 14 y 15 de
septiembre), siempre entre 0,05 y 0,09 MW. Aparte, publicó tres alertas lejos del cráter (15 de julio,
26 de agosto y 5 de septiembre, esta última de 0,14 MW a 1,9 km) y dos diurnas que son el artefacto
solar A76 (12 de junio 0,32 MW y 25 de agosto 0,60 MW). El silencio de julio que mostraba S124 sigue ahí.

Cuando MIROVA alerta en el cráter, medimos lo mismo: la mediana de nuestro VRP sobre el suyo, pasada contra
pasada, es 1,13 en las 6 pasadas comparables (1,12 en las 5 con el sensor a 40° o menos). El caso de hoy lo
muestra bien: el 14 de septiembre a las 05:42 UTC, con el satélite casi en la vertical, MIROVA publicó
0,09 MW y nosotros 0,094 MW a 230 m del cráter.

## 2. Lo que cambió desde S124 en la forma de mirar

| S124 | S141 | por qué |
|---|---|---|
| alertas del consolidado | referencia unificada (consolidado + OCR + respaldo), con las pasadas en que MIROVA miró sin ver nada | la brecha es de sobre-publicación, no de recall (S139) |
| filtro reconstruido a mano | predicado del dashboard ejecutado con node | lo que ve el operador (S138) |
| magnitud del cúmulo | núcleo F5 | es lo que muestra el dashboard en VIIRS 375 m (S132) |
| perfil experimental del foco | no se usa | dejó de actualizarse el 27 de agosto |
| barras "no se pudo medir el fondo" | pasadas sin ningún píxel de fondo, con el corte del PR #535 marcado | la máscara de nube de 260 K se comía la nieve (D14) |
| sin geometría | sensor a más de 40° marcado aparte | el propio grupo MIROVA no confía en esa magnitud (D17, nota S141) |

Dos controles del instrumento pasan: el predicado da los casos conocidos del guard, y la carga de Nevados de
Chillán publica exactamente lo mismo que el banco de paridad completo (1.169 pasadas, 0 discrepancias).
Las alertas que llegan duplicadas por consolidado y OCR se cuentan una vez por pasada.

## 3. El hallazgo que cambia la lectura: desde el 28 de agosto publicamos casi siempre

En las pasadas VIIRS 375 m donde MIROVA miró y no vio nada, nuestro dashboard publica una anomalía en
~9 de cada 10 desde fines de agosto. Antes era ~6 de cada 10. **No es Nevados de Chillán: pasa en los 11
volcanes a la vez**, y el escalón coincide con el PR #535, que apagó en producción la máscara de nube
(`regimen_535.json`, 11 Tier A, pasadas del 10 de agosto al 15 de septiembre):

| tramo | negativos limpios | tasa de publicación | no publicadas que estaban ciegas |
|---|---|---|---|
| antes de #535 (hasta 28-ago 23:00 UTC) | 412 | 0,61 | 75 de 160 |
| entre #535 y #571 (máscara apagada, piso VRP aún puesto) | 64 | 0,84 | 0 de 10 |
| después de #571 (sin piso VRP) | 297 | 0,87 | 1 de 38 |

**El fenómeno.** A la altura de estos volcanes, en invierno, la nieve irradia a la misma temperatura que
una nube baja. La máscara de 260 K descartaba esos píxeles como nube y, en muchas pasadas, dejaba el primer
pase sin un solo píxel de fondo: la pasada quedaba ciega y no podía publicar nada. Esa ceguera escondía la
sobre-publicación. Al apagar la máscara (lo que MIROVA hace, Laiolo 2026 p. 4), las pasadas recuperaron
fondo y publicaron como el resto. Quitar el piso VRP tres días después movió poco: sólo 5 de las 297
publicaciones posteriores habrían quedado ocultas por él.

**Por qué importa.** La línea base de la Fase 1 (63,5 % en S139) y el auto-audit semanal (62,9 % con ventana
de 60 días) mezclan los dos regímenes y subestiman el actual. El objetivo de terminado (10 % en focales,
15 % en nevados) hay que medirlo contra ~0,87, no contra 0,63. **Caveat**: el tramo entre los dos merges
tiene sólo 64 pasadas en tres días; el escalón es claro en la serie semanal (panel D de la figura), pero no
se descarta del todo un aporte estacional.

## 4. La página de MIROVA y su GeoTIFF (15 de septiembre)

Consultada a pedido de Nicolás, con el navegador de la app (la extensión de Chrome no estaba conectada), y
sólo leyendo el raster que la página ya tenía cargado.

- **Qué ofrece.** La página de detalle muestra las 10 últimas imágenes VIIRS 375 m con VRP y ángulos cenital
  y azimutal, y tres gráficos (VRP logarítmico, lineal y distancia máxima) servidos como imágenes PNG, sin
  datos por pasada. El mapa deja elegir volcán, sensor, fondo y paleta, leer valores por píxel y descargar el
  GeoTIFF o el KMZ de la última pasada.
- **El GeoTIFF está en la grilla nativa de MIROVA**: UTM 19S (EPSG:32719), 134 × 134 celdas de 375 m. Esto
  corrige lo que S124 dejó anotado (que los TIF venían reproyectados a latitud y longitud). El cráter Nicanor
  cae en la celda fila 68, columna 66; el centro de la grilla es la 67, 67.
- **La alerta de hoy (0,05 MW, 06:18 UTC) son dos celdas contiguas del cráter**, (67, 66) y (68, 66), que
  sobresalen igual sobre su entorno. Por brillo crudo el cráter no destaca: el máximo del campo está en el
  borde norte de la grilla (gradiente del terreno, A69) y, restando la mediana de 9 × 9 celdas, el cráter
  queda en el puesto 626 de 15.876. MIROVA lo alerta por su índice contextual, no por ser lo más brillante.
- **Reconstrucción de la magnitud, no concluyente.** Con el fondo de cada celda como la media de sus vecinas
  no alertadas (la definición del grupo), una celda da 0,030 MW, dos 0,065 y tres 0,078, contra 0,05
  publicados. Una sola pasada no alcanza para saber cuántos píxeles sumó MIROVA.
- **Sobre-publicación, en concreto.** El 14 de septiembre a las 06:18 (sensor a 38°) y 06:36 (a 60°) MIROVA
  no alertó; nosotros publicamos 0,043 y 0,072 MW en la celda del cráter o a una celda.
- **El archivo propio ya guarda estos TIF.** `MendozaVolcanic/mirova-tif-archive` sondea MIROVA cada pocos
  minutos y tiene los dos TIF de estas alertas. Es la base para contar, pasada por pasada, cuántos píxeles
  suma MIROVA: lo que le faltó al probe de la Fase 1.

## 5. Qué sigue

1. Re-medir la línea base de sobre-publicación de la Fase 1 sólo con el régimen posterior al 28 de agosto.
2. Contar los píxeles de MIROVA con los TIF archivados (script reproducible, no consultas en la página),
   empezando por las alertas de este volcán, y usarlo en el probe v2.
3. Revisar si los TIF archivados de mayo también están en UTM, para cerrar la corrección de S124.
