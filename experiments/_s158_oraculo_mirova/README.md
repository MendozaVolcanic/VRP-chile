# Oráculo: el código de MIROVA para VIIRS 750, en Python (S158)

**Qué es.** Un port línea a línea de `MIROVA_VIIRS750_hotspot_detection.m` y `MIROVA_VIIRS750_VRP.m` (OSF zm62w,
2026-07-24, MIT, Diego Coppola; copia en `../_s158_d17_diseno/osf_codigo_mirova/`). No es producción: es un
instrumento para correr el detector de MIROVA sobre una matriz y comparar con el nuestro.

**Por qué se le puede creer.** La matriz de ejemplo que MIROVA publicó es la pasada real de Etna del 2023-05-19
00:54 (NOAA-20). El archivo OSF v2.5 la trae con el mismo cenit y azimut, y con lo que dio el sistema en producción:

| | MIROVA (OSF v2.5) | oráculo |
|---|---|---|
| píxeles alertados | 5 | 5 (los mismos) |
| suma de L_hot | 1,96534218 | 1,96534218 |
| suma de L_bk | 1,072886152 | 1,073661545 (0,07 %) |
| VRP | 9.889.528 W | 9.880.936 W (0,09 %) |

La detección coincide exacta; el fondo, con 0,07 % de diferencia. ⚠️ **Corregido por el frente F6 de la auditoría S158**
(`experiments/_s158_audit/f6/INFORME.md`, hallazgo 2): la primera versión decía que esto «prueba que el código publicado
es el que corrió en producción». Dice más de lo que mide. En Etna los 5 píxeles entran por la caja de cumbre y ninguno
por el Test 1 ni por la región de fuera, así que la pasada prueba la detección de cumbre, el fondo y la fórmula del VRP,
no los umbrales. Y sobre 50° de cenit el VRP publicado de VIIRS 750 no es el del código en el 24 % de las filas del OSF
(hallazgo 1 de F6): el código publicado no es toda la cadena.

**Lo que este control no cubre** (`mutar_oraculo_salida.txt`): en Etna el foco supera todos los umbrales por mucho, así
que cambiar los 8 vecinos por los 9, `max` por `min`, K1 a -0,8, el mínimo de dNTI a 0,010 o recortar a cero no cambia
el resultado. Sí lo cambian apagar el segundo pase (-10,8 %), sacar la dilatación del fondo (+0,8 %) y usar como fondo
la media de los 8 vecinos no alertados, que es el brazo D de D25 (+2,65 % contra MIROVA). Para cubrir lo demás hace
falta una pasada débil con resultado publicado.

**Supuesto declarado.** `fillmissing2(A, 'linear')` se replica con `griddata` lineal; en una grilla regular la
triangulación tiene empates y el orden de los ejes cambia el resultado (0,7 % con fila y columna, 0,07 % con columna y
fila, que es la convención de MATLAB). Ajustado contra un solo caso.

**Una trampa que cayó acá mismo.** La primera versión del control de mutaciones reescribía el archivo y lo recargaba
con `importlib.reload`: Python reusó el bytecode viejo y siete mutaciones dieron «igual», una de ellas falsa. Ahora cada
mutación corre en un intérprete nuevo y sin bytecode.

Pruebas: `tests/test_oraculo_mirova_v750_s158.py` (6). Uso:

```
python -I -B experiments/_s158_oraculo_mirova/mutar_oraculo.py . <carpeta temporal>
```
