# Verificador con contexto limpio: resultado de la tarea 1.23 (MxD03 sola)

**Veredicto: CONFIRMADO**, con cuatro matices que tienen que viajar con el resultado. El número se
reproduce exacto, cada lectura mide lo que el README dice, y el control que se cancela por construcción
(Terra contra Aqua) pasa. Lo que cambia es el alcance: la vara VIIRS, en la práctica, es un punto fijo a
0,15 km del ancla, y la ventaja de MxD03 vive sólo donde el píxel más caliente es el cráter.

Material: código del tag `s151-1.23-probe` (commit `eb97779f4`), artefactos en
`C:\Users\nmend\AppData\Local\Temp\claude\p123_all\`. Scripts y salidas en esta carpeta.

## 1. Reproducción

- `evaluar_sola.py` del árbol es idéntico al del tag salvo fin de línea (`diff --strip-trailing-cr` sin
  diferencias; lo mismo `probe_sola.py`, `jobs_123.py`, `vara_viirs.json`, `README.md`).
- Lo corrí con los mismos argumentos (`evaluar_verif.log`, `resumen_verif.json`): el log es idéntico al
  del orquestador y el JSON de salida es igual a `resumen_local.json` (`a == b` da `True`).
- Los 24 medios jobs están, todos con commit `eb97779f4c0e…`. Cada log dice «N de N gránulos medidos»
  salvo **Tupungatitoa, 14 de 15**: el que falta es `MOD021KM.A2026275.0225` («no encontrado o no bajado
  (L1B)»), que está en `_s151_mxd03_cumulo_121/archivo_cmr.json` (línea 9), o sea que no es pedido
  (README l. 294). `sin_tiempo` aparece 0 veces en los 24 logs.
- `conteo_por_brazo`: 470 en los 22 brazos; `motivos_invalido` y `motivos_incompleto` vacíos.
- Anotación: `reproduce_la_121` da 1 diferencia en M, Tupungatito `MOD021KM.A2026223.0120` (M publica en
  la 1.21 con el commit `e472c673b`, no publica acá; C igual). Es un negativo limpio a 36,1° de cenit, no
  entra a la regla 1 ni a ningún rango principal. Causa SIN VERIFICAR (deriva entre commits).

## 2. Cada lectura, ¿mide lo que dice?

**Vara principal.** Compara posiciones 2D, no radios: `math.hypot` de las componentes norte y este
(`evaluar_sola.py:150-151`), con λ y residuo perpendicular. El universo es el que el README anticipa
(l. 252-254): n = 76, 63 noches, 70 Láscar y 6 Chillán, 30 Terra y 46 Aqua, por cenit 33/29/12/2
(`resumen_verif.json`, `vara.principal`). λ = 1,04 [0,93; 1,11]: la vara cae justo donde dice M.

**¿Está atada al ancla?** Sí, en la práctica es el ancla (`controles_vara_salida.txt`):
- |v − ancla| mediana 0,145 km (p90 0,34); la dispersión de v entre noches es 0,17 km norte y 0,14 km este.
- Cambiando v por el ancla (0, 0): dd 0,662 [0,373; 1,000] contra 0,620 [0,349; 0,956] con la vara.
- Barajando v entre noches del mismo volcán (500 veces): dd 0,676 [0,604; 0,726].
- Correlación noche a noche entre v y M: −0,16 (norte) y 0,13 (este).

La vara no aporta información propia de cada noche; aporta que **otro sensor, con otra geolocalización,
ve el calor de Láscar a 0,15 km del ancla**. Eso no es circular: la selección anclada elige cuál cúmulo,
pero su centroide sale de las posiciones VIIRS; un objeto a 1,3 km (donde lo pone `_interp_geo`) seguiría
estando dentro del inner y saldría a 1,3 km. Lo que mide el veredicto, entonces, es «MxD03 pone el píxel
MODIS más caliente más cerca del lugar donde VIIRS ve el calor», que es lo de #828 con un ancla validada.
El README ya lo dijo (l. 264-266).

**Nulo de 20 rumbos en km.** Comparable bajo 35°: `razon_px_nulo_M` 0,999 y 0,971, cruces de borde
M/nulo entre 0,96 y 1,05 en los círculos de 1, 3, 5 y 25 km (`tamano_del_nulo`). Sobre 50° no (1,29,
p90 2,69), que es por lo que el README deja ese tramo descriptivo. El evaluador no marcó ningún nulo con
km distinto del real (INVALIDO vacío). El nulo del estadístico de la vara (pares k, k+4) da |mediana| máx
0,18 km contra 0,62: mide la dispersión por azar con la geometría real, no un sesgo hacia el ancla.

**Test 1 con signo.** Bien implementado contra el README (`evaluar_sola.py:298-342`). Alertas: M sube k
+0,149 contra nulos de −0,159 a +0,178 (2.º de 21, p 0,095): M COMO EL AZAR. Negativos limpios: M baja
k −0,108, el más bajo de 21 (p 0,048): M BAJA. La combinación es MIXTO por la tabla (README l. 361-366).
La dirección es la de una posición mejor, pero en alertas no llega al corte, y la tabla no autoriza la
frase «las pérdidas son el precio de una posición mejor» (README l. 388).

## 3. ¿Podría salir «MXD03 MÁS CERCA» sin que MxD03 fuera mejor?

- **Sesgo constante de la vara**: el control que se cancela por construcción es Terra contra Aqua, que
  corren la grilla en sentidos opuestos. Los dos dan M más cerca: Terra 0,773 [0,288; 1,119], Aqua
  0,609 [0,231; 0,909]. Un sesgo constante sumaría en uno y restaría en el otro. Pasa.
- **La vara hereda la posición MODIS**: no. `construir_vara_viirs.py` usa sólo pasadas VIIRS y el ancla
  (`get_detection_anchor`, l. 109); la correlación noche a noche v contra M es ~0.
- **Selección de la población**: la etiqueta `pos` es de MIROVA y la selección del píxel es la unión
  simétrica de los dos discos (`probe_sola.py:189`). Bajo 35° el píxel está cerca del cráter y la unión
  no lo sesga.
- **Riesgo que queda**: que el ancla (y VIIRS con ella) no sea el objeto que ve MODIS. Lo acota que
  λ ≈ 1 en los dos satélites; no lo elimina (README l. 500-502).

## 4. Las dos varas INDECIDIBLE: matizan, no contradicen

Separé por si el píxel más caliente está en el cráter (máx(|C|, |M|) ≤ 3 km, condición simétrica en C y
M) (`conteo_borde_salida.txt`):

| conjunto | cenit | n | lejos (> 3 km) | dd de los lejanos | dd de los del cráter |
|---|---|---|---|---|---|
| principal | 0 a 35 | 62 | 19 | −0,18 | +1,03 |
| principal | 35 a 90 | 14 | 10 | −2,28 | +0,64 |
| estricta, todos | 0 a 35 | 91 | 46 | −0,09 | +1,00 |
| estricta, todos | 35 a 90 | 72 | 68 | −1,29 | +0,64 |
| amplia, todos | 0 a 35 | 134 | 80 | −0,05 | +1,09 |
| amplia, todos | 35 a 90 | 172 | 167 | −1,11 | +0,89 |

Donde el píxel es el cráter, MxD03 queda más cerca en todos los cortes (sobre 35° con n de 4 a 5). Las
varas amplias son INDECIDIBLE porque agregan gránulos sin alerta cuyo píxel más caliente está a 5 km
(mediana |M − ancla| 5,4 en los no `pos`), donde la vara del cráter no es la posición de ese objeto.
**Sobre 35° el signo se invierte con intervalo fuera de 0** (estricta todos −1,235 [−2,136; −0,114];
amplia todos −1,01 [−1,385; −0,109]), pero sale de píxeles a 4 a 9 km del cráter que caen en el borde
de la selección: la selección por MIR absoluto (A69) junto con la unión de discos puede favorecer por
construcción a la geolocalización que deja ese píxel dentro (mecanismo SIN VERIFICAR). No es evidencia
contra MxD03; es que sobre 35° la vara no dice nada de geolocalización.

## 5. Otros hallazgos

- **Resumen del orquestador mezcla dos conteos**: «gana 9 de 46 ... ganancias como el azar p 0,0952».
  El 9 es el total; el rango que decide es bajo 35° con 8 observadas (nulos 3 a 8). Sobre todos los
  cenits, anotación, sale GANANCIAS ESPECIFICAS (p 0,0476). Las pérdidas: 2 contra nulos 1 a 6 (p alta
  0,905). Cada una de las dos protegidas perdidas se publica en 7 de 20 nulos.
- **El espía refuta la hipótesis del 04-20** (README l. 102-107): el píxel caliente no está en el anillo
  ni en C ni en M (`caliente_en_anillo` False, a 0,34 y 0,08 km). k cae de 4,81 a 2,56 porque σ_bg sube
  de 0,0140 a 0,0234 y ΔL baja de 0,343 a 0,293. En el 04-30 el píxel caliente sí sale del anillo
  (1,35 a 0,23 km) y σ_bg sube 0,0140 a 0,0163. En los dos MxD03 centra el píxel caliente en el cráter y
  el Test 1 baja. Qué píxel infla el anillo: SIN VERIFICAR.

## 6. Qué puede y qué no puede decir para producción (A45)

Puede decir: en Láscar, bajo 35° de cenit, MxD03 pone el píxel caliente donde VIIRS ve el calor
(≈ 0,6 km más cerca que `_interp_geo`), sin sesgo constante de la vara, y las dos protegidas perdidas son
lo que cualquier corrimiento de 0,4 a 1,3 km rompe en ese Test 1 (fila 1 de la tabla del README, l. 388).

No puede decir: que MxD03 sea adoptable (adoptable False; la letra de la regla 1 sigue en PIERDE
PROTEGIDA); que las pérdidas sean el precio de una posición mejor (el Test 1 con signo dio MIXTO); nada del
borde del barrido (vara con 2 gránulos sobre 50°, nulo no comparable sobre 35°); nada fuera de Láscar
(70 de 76; Chillán 6, dd 0,19 con intervalo [−7,4; 2,3]). Adoptarlo exige resolver antes la fragilidad del
Test 1 o una excepción decidida por Nicolás.

## Archivos

- `controles_vara.py`, `controles_vara_salida.txt`: vara con v = ancla, barajada, por satélite y cenit.
- `conteo_borde.py`, `conteo_borde_salida.txt`: separación cráter contra lejanos.
- `evaluar_verif.log`, `resumen_verif.json`: la reproducción.
- `evaluar_sola_tag.py`: copia del evaluador del tag.
