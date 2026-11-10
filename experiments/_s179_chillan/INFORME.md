# S179: Nevados de Chillán, 2026-10-01 a 11-09, tres sensores: producción, la vía «código MIROVA» y MIROVA

Fecha: 2026-11-10 (~18:45 UTC). Medición exploratoria del coordinador, **sin verificador**. Pedido de Nicolás: comparar
nuestros datos de Chillán en octubre y noviembre en los tres sensores; hay una colada que avanza hacia el SE y hoy llega
a casi 1 km.

Base: producción de `origin/main` en `b68779c65` (`salida/base_main.txt`). La vía: trozos de Chillán de la
retrospectiva D2 (run 42507820590, 10-01 a 10-16) y de la historia P4 (run 42749607584, 10-17 a 11-09), perfil
`_s172_retro_paquete`. Referencia: snapshot del repo, regla D-9 SN, pareo ±120 s. «Publica» y la magnitud mostrada
salen del predicado del tablero ejecutado con node, igual en los dos brazos. Instrumentos: `comparar_chillan.py` y
`geometria_vista.py`; salidas en `salida/`.

## 1. ¿Publicamos lo que MIROVA alerta, y con qué magnitud?

Ninguna alerta de MIROVA quedó sin pasada nuestra a ±120 s en ningún sensor.

| sensor | alertas de MIROVA (de 1 MW o más) | producción publica | la vía publica | magnitud nuestra / MIROVA, mediana [p25; p75] | negativos limpios publicados |
|---|---|---|---|---|---|
| MODIS | 37 (37) | 33 (K hasta el 11-02) | **37** | producción 0,75 [0,24; 0,98]; **vía 1,00 [0,85; 1,19]** | 0 de 34 y 0 de 33 |
| VIIRS 375 | 77 (65) | 77 | 77 | K 0,56 [0,34; 0,75]; **vía 0,99 [0,90; 1,00]** | K 1 de 14; vía 0 de 14 |
| VIIRS 750 | 69 (63) | 67 | **69** | K 0,47 [0,27; 0,72]; **vía 1,00 [0,97; 1,04]** | K 1 de 31; vía 0 de 31 |

Lectura: en la erupción de Chillán la vía no pierde ninguna alerta en ningún sensor y su magnitud calza con la de
MIROVA. K subestima la potencia a la mitad en VIIRS y perdió 4 alertas de MODIS de 1 MW o más (12, 15, 25 y 30 de
octubre). Es la ventana que la retrospectiva no cubría para decidir (decidió con febrero y marzo).

Ojo con la vara: que la vía calce con MIROVA es lo esperado si el código está bien portado; no dice que la potencia sea
la verdadera, sólo que es la de MIROVA.

## 2. ¿Vemos la colada hacia el SE?

**El foco.** El píxel más caliente de VIIRS 375 cae, en mediana, a 0,37 km (vía) y 0,55 km (producción) al SO (rumbo
222° a 226°) del punto del yaml (lat −36,863, lon −71,377): lat −36,8653 lon −71,3800 (vía) y lat −36,8667 lon −71,3811
(producción). El yaml no marca el cráter activo; el repo no trae la coordenada del cráter Nicanor, así que el foco es
una estimación nuestra, a contrastar con la posición conocida del domo.

**La zona caliente crece.** Píxeles alertados por pasada en VIIRS 375 con la vía: 6 en la primera semana de octubre,
10 en la segunda, 12 a fines de octubre, 13 en noviembre (K: 3 a 5). MIROVA también ve el foco alejarse del centro: su
Distancia_km de VIIRS 375 sube de 0,84 km (1 a 15 de octubre) a 1,13 km (16 a 31) y a 1,27 km (noviembre); en VIIRS 750
de 1,06 a 1,68 km. La nuestra (vía) sube de 0,59 a 0,72 y a 0,81 km.

**Hacia dónde.** Mirar de lado mueve los píxeles: con el satélite al este y cenit de 35° o más, el centroide se corre
0,65 a 0,92 km al oeste; con el satélite al oeste, 0,16 a 0,20 km al este. Ese corrimiento cambia de signo con el lado,
así que es de la geometría de observación (relieve alto visto en oblicuo), no del volcán. Con sólo las pasadas casi
verticales (cenit menor que 35°):

| quincena | n (vía) | píxel más lejano del foco (vía) | rumbos de ese píxel |
|---|---|---|---|
| 1 a 15 de octubre | 11 | 0,53 km | 4 de 11 a 135° (SE); el resto disperso |
| 16 a 31 de octubre | 16 | 0,83 km | 13 de 16 entre 208° y 245° (SO) |
| 1 a 9 de noviembre | 7 | 1,05 km | 7 de 7 entre 200° y 226° (SSO a SO) |

Producción (geolocalización nativa del gránulo, no la grilla) da lo mismo en noviembre: 7 de 7 entre 209° y 242°.

**Lectura (⚠️ resuelta en §3: la colada va al SO, Nicolás 2026-11-10; se conserva el texto original).** Nuestros datos muestran una zona caliente que crece desde el foco hasta ~1 km a comienzos de noviembre,
pero hacia el SSO y SO, no hacia el SE. A comienzos de octubre sí hubo píxeles al SE. Esto no coincide con lo que
Nicolás ve en terreno, y no sé todavía por qué. Caminos posibles, ninguno comprobado:
1. el foco (nuestro «cráter») no es el punto de salida de la colada, y lo que crece al SO es otra cosa (el domo, la
   zona de fumarolas, un depósito caliente);
2. un error de geolocalización compartido: producción y vía usan la misma geolocalización del gránulo, así que su
   coincidencia no es una prueba independiente;
3. un frente de colada estrecho o ya enfriándose que en 375 m pesa menos que el resto de la zona caliente.

La prueba que lo resuelve es una imagen SWIR de alta resolución (Sentinel-2 o Landsat, 20 a 30 m) de una fecha de
noviembre, comparada con nuestros píxeles de la misma noche, o la posición del frente de colada que tenga OVDAS.

## 3. Contraste con el punto de Nicolás (2026-11-10, ~20:25 UTC)

Nicolás corrigió: la colada va al **SO**, no al SE, y dio el punto lat −36,867309, lon −71,379167. Se lee como la boca
de la colada (el cráter activo); si fuera el frente, la lectura de abajo cambia. Instrumento:
`contraste_punto_nicolas.py`, salida `salida/contraste_punto_nicolas_salida.txt`. Control: el punto del yaml cae a
0,517 km, rumbo 22°, del punto de Nicolás (comprobado a mano: 0,479 km al N y 0,193 km al E).

- **El foco calza con el punto.** El píxel más caliente de VIIRS 375 queda, en mediana, a 0,16 km (vía) y 0,20 km
  (producción) del punto en las pasadas casi verticales: dentro de un píxel de 375 m. El 0,16 de la vía es fijo
  porque la vía trabaja sobre la grilla, que cuantiza la posición (D15).
- **La zona caliente crece al SO.** Píxel más lejano desde el punto, sólo cenit < 35°:

| quincena | vía: n, alcance mediano, rumbo mediano | producción: n, alcance mediano, rumbo mediano |
|---|---|---|
| 1 a 15 de octubre | 11, 0,50 km, 287° (disperso) | 13, 0,36 km, 241° |
| 16 a 31 de octubre | 17, 0,85 km, 239° | 17, 0,65 km, 242° |
| 1 a 9 de noviembre | 7, 0,97 km, 239° (208° a 239°) | 7, 0,79 km, 238° (224° a 252°) |

Lectura: con el punto de Nicolás como boca, nuestros dos brazos ven la colada avanzar al SO (rumbo ~240°) y llegar a
~1 km a comienzos de noviembre (la vía), lo que coincide con lo observado en terreno. El «no sé por qué» de §2 era el
dato de terreno, no el instrumento. La vía ve más lejos que producción (0,97 contra 0,79 km): alerta más píxeles
tibios del borde, como MIROVA. Exploratorio, sin verificador; un píxel de 375 m no resuelve el frente con precisión
mejor que ~0,2 a 0,4 km.
