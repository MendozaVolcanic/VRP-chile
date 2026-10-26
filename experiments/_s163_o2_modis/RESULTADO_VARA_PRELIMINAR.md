# O2 MODIS: vara PRELIMINAR del fondo con la regla de `fillmissing2` de MATLAB (2026-10-26)

**PRELIMINAR y SIN VERIFICADOR LIMPIO todavía.** La prueba de oro es correr `correr_o2_modis.m` en MATLAB (paquete de
esta carpeta), que espera a que Nicolás vuelva a entrar a MathWorks.

## El fenómeno

En una alerta MODIS de pocos píxeles el VRP es la radiancia MIR de esos píxeles menos el fondo que habría sin el foco.
El código de MIROVA estima ese fondo tapando las alertas y un halo de 3 × 3 celdas, y rellenando el hueco por
interpolación lineal sobre una triangulación de las celdas que quedan. En una grilla regular, cuatro centros vecinos
están sobre un mismo círculo y la triangulación no es única: cada programa elige una diagonal distinta, y con ella
cambia el valor que se le asigna al centro del hueco. Con un solo píxel alertado, ese centro es todo el fondo de la
alerta. Nuestro port elige como lo hace scipy; MATLAB lo hace con otra regla, que la rama `s163-o2-alternativa`
identificó (perturbación simbólica de Delaunay, marco x = fila, y = columna; confirmada en 166 de 166 escenas de
VIIRS 750 contra MATLAB).

## Qué se midió

`vara_preliminar_fillmissing2.py` → `vara_preliminar_fillmissing2_salida.txt` y `.json`. Las 404 escenas del paquete
(116 pasadas MODIS, lotes S159 y MOD-C), con la misma construcción del hueco que el port y sólo la función de relleno
cambiada.

Controles: con el relleno del port, la misma construcción reproduce el VRP del port en 404 de 404 escenas (máximo
2e-16): la diferencia que sigue es sólo la regla de relleno. 0 aristas ilegales en la triangulación. Nulo: el marco
cambiado (x = columna) discrepa de la regla en 196 de 404, así que en MODIS la regla discrimina. Ninguna escena tiene
celdas de alerta fuera de la envolvente convexa (el borde, poco probado, no entra aquí).

## Qué dice

| píxeles | escenas | port/regla, mediana | difieren más de 1 % | más de 10 % | iguales a 1e-9 |
|---|---|---|---|---|---|
| 1 | 168 | 1,000 (p5 0,80; p95 1,42) | 132 | 79 | 29 |
| 2 | 132 | 1,000 | 2 | 0 | 129 |
| 3 | 77 | 1,000 | 1 | 0 | 76 |
| 4 | 27 | 1,028 (p95 1,22) | 15 | 12 | 7 |

En la variante `fisica` (el PM que decide en MOD-D): 36 escenas de 1 píxel con razón entre 0,75 y 3,78 (19 difieren
más de 10 %); 7 de 4 píxeles con mediana 1,12. Casos extremos: Llaima 2026-07-24 01:05 (la publicación que el
diagnóstico de MOD-C atribuyó a un artefacto de gradiente) baja de 0,43 a 0,11 MW con la regla; Láscar 2026-05-11
07:55 (la candidata a experimental) baja de 0,30 a 0,21 MW.

## Lo que implica para MOD-D (para decidir, no decidido)

La detección no cambia (la regla sólo toca el fondo). Lo que cambia es la magnitud del PM en alertas de 1 y 4 píxeles,
y con ella la prueba M y la curva de cenit del censo. El censo de MOD-D guarda la grilla 51 × 51 de cada pasada, así
que el PM con la regla de MATLAB se puede calcular después, fuera de línea, sin otro despacho. Recomendación: una adenda
informativa de MOD-D, fechada antes de leer el censo, que informe M también con la regla de MATLAB (sin cambiar la
regla sellada, que es la del port). Va a la coordinadora.
