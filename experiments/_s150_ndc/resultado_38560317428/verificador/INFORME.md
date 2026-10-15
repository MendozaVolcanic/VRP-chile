# Verificador S151: prueba de Nevados de Chillán (run 38560317428)

**Veredicto: PARCIAL.** Los veredictos impresos están bien calculados y reproducen, pero dos de ellos se pueden leer como algo que no dicen, y la salida omite el costo que decide el criterio de victoria.

## Confirmado

- **Reproduce.** El `.json` sale idéntico y el `.txt` difiere sólo en la línea del perfil, que va por stderr. `probar_medir_ndc.py` da 10 de 10.
- **Las reglas son las del pre-registro**: P1 contra B y contra C0, P2, P3 por pares, P4 con "todas", P5 sólo en las topadas.
- **Recálculo propio** desde los JSON crudos y los CSV (`indep.py`). Coincide decisión por decisión:
  - (a) Las 13 alertas VIIRS 375 y las 11 VIIRS 750 de 1 MW o más las publican los 10 brazos.
  - (b) Hay 3 alertas MODIS de 1 MW o más: 10-01 01:45, **10-01 08:35 (5,18 MW)** y 10-05 07:50. La de las 08:35 la pierden C0, T0, B y G; la publican E, F, J, K, KE y KET.
  - (c) C0 tiene 11 pasadas MODIS topadas, las 11 `far` en C0 y en T0, y 0 publicadas en los dos.
- **Cobertura y cableado.** Las mismas 259 pasadas con la misma versión de producto en los 10 brazos, FLAGS_BRAZO igual a lo declarado y 0 `triggered_test1` en los brazos sin Test 1.

## Riesgo de mala lectura

- **P5_T0 CUMPLE es vacuo.** El tope no toca la etiqueta `far`, así que T0 no podía cambiar ninguna decisión. Además ningún brazo K llega a 5 MW en MODIS (máximo 4,804 MW): `d9_capped` vale 0 en F, J, K, KE y KET, KET es idéntico a KE y P5_KET da SIN DATO. **Quitar el tope en el candidato quedó sin probar.** SIN VERIFICAR: con la etiqueta desde el cúmulo y sin tope, el filtro de cirrus ocultaría unas 6 topadas de E; ahí el tope sí sería compuerta.
- **P4 no prueba la etiqueta.** KE decide igual que K, y K recupera la alerta de las 08:35 sin el flag de etiqueta, igual que F y J. La recuperación es frágil: K la publica con **1,08 MW** contra 5,18 de MIROVA.
- **Nada se adopta**: un volcán, 3 alertas MODIS (casos, no tasas) y magnitud subestimada (razón 0,39 a 0,68).

## Pérdidas bajo 1 MW y suma de errores (`suma.py`, etiquetas del evaluador)

- **En VIIRS 375 se pierden tres, no una**: 10-05 04:48 (0,04 MW) y, en reposo, 09-14 05:42 y 09-18 05:24, que la sección 8 no muestra. Las pierden también B y J, así que la causa es quitar el Test 1, no `max`.
- **En VIIRS 750 la pérdida sí es de `max`**: 09-28 04:42 (0,23 MW), que pierden F, K, KE y KET pero no B ni J.
- **Publicaciones en negativos limpios, todos los sensores**: C0 50 (mediana 0,052 MW), B 12, F/K/KE/KET 1. De las 7 de C0 del 26 y 27, 6 caen sobre RUTINA en 0 y una (09-27 05:36, VIIRS 375) no tiene fila.
- **Suma de errores en Muy Bajo**: C0 52, B 17, J 23, F/K/KE/KET **7**. La lectura B no agrega pasadas.

## Arreglos

1. Que P5 imprima SIN SUSTRATO cuando ninguna topada puede cambiar de etiqueta.
2. Imprimir el costo VIIRS y el recall en reposo.
3. Corregir la mediana con n par: hoy toma el valor superior (MODIS C0 imprime 0,68; la mediana real es 0,63).
4. Agregar un control positivo para P3.

## Defectos propios

- Mi predicado aproxima el del tablero: no lo corrí con node.
- La suma de errores usa las etiquetas del evaluador, no un etiquetador mío.
- No cuento las 76 pasadas `sin_info`; C0 publica 36 de ellas en VIIRS 375.
