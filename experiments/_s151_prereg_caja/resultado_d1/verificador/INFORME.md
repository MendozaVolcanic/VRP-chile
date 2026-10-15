# Verificación del veto D1 de la caja (KC contra K, Láscar 2026-03-14 a 03-27)

**1. Re-corrida.** `evaluar_caja.py` con `--repeticion` da salida idéntica a `eval_d1_rep.txt` (diff vacío fuera de avisos): MODIS VETADO en A y B, VIIRS 375 y 750 CUMPLE, KC NO CUMPLE (veto). Sin repetición, PENDIENTE DE REPETICIÓN. Huella: corona 3 a 1, caja 172 a 172. **CONFIRMADO.**

**2. La pérdida.** Una sola pasada: MYD021KM.A2026086.0710, standard. En K hay un único píxel a 3,20 km del cráter (dN +0,24, dE +3,20). Cae en la corona: fuera de la caja de 2,5 km y dentro del círculo de 5 km. Tiene 0,14 MW y BT 269,9 K sobre un fondo de 268,98 K. El primer pase da 0 píxeles y el píxel entra sólo por la recaptura del segundo pase. En KC esa recaptura da 0. La caja actúa: el umbral estricto en el segundo pase lo apaga. **CONFIRMADO.**

MIROVA ubica la alerta a 1,41 km de su centro de grilla, que está 0,83 km al sur del cráter. Eso la deja a una distancia del cráter de entre 0,58 y 2,24 km. Aun con la celda cuantizada (D15), su |dN| y su |dE| quedan bajo 2,33 km, o sea DENTRO de nuestra caja con cualquier acimut. Nuestro píxel queda al menos a 1,92 km de esa alerta.

**Causa: posición, con evidencia nueva (`pasada.py`).** En las 13 pasadas MODIS de K, el píxel del cráter se corre hacia el lado del sensor y el corrimiento crece con el ángulo:

- Aqua con acimut 100°: +1,1 km E a 17°, +1,4 a 30°, +3,2 a 40° y +3,5 a 45°.
- Terra con acimut -100°: entre -0,9 y -2,2 km (al oeste) a 31-32°.

La única otra pasada que KC pierde (la del 03-14 07:05, Muy Bajo 0,97 MW, 45°) tiene la misma firma. El mecanismo queda SIN VERIFICAR. Los candidatos son la interpolación de 5 a 1 km de `_interp_geo` (zoom con los extremos alineados, `process_modis.py:342`) y el paralaje de una cumbre de 5,6 km. No es D17 (el centro de grilla). La predicción P1 del pre-registro acierta en «posición» y yerra en el código. Además, n = 13 y un solo volcán.

**3. Brazos de intentos distintos.** Los dos brazos de v3 llevan el mismo `codigo_sha` (55a092c). La repetición (0d3cbce) da los 132 records idénticos en los dos brazos, sin contar los campos de fecha y `regimen`, con el mismo gránulo y la misma versión. La clave de la caja está en los 4 logs. Mezclar los intentos no introdujo nada. **CONFIRMADO.**

**4. ¿Es 1,0?** La fila dice `1.0`, `ALERTA_TERMICA`. 56 de las 62 alertas MODIS traen dos decimales, así que es 1,00. Con `v >= 1.0` es protegida en A y B, pero está en el filo: con 0,99 no lo sería. **CONFIRMADO.**

**5. Global.** `_combinar` y §7 dicen que el veto es definitivo y gana sobre D2, V1 y un mecanismo INDECIDIBLE. **CONFIRMADO.**

**6. Qué se puede decir.** De VIIRS sólo se puede decir que en D1 no hubo pérdidas (10 y 10 protegidas); eso no es una tasa. Como la regla sellada cuenta el veto igual, la caja queda descartada para la réplica **con la geolocalización MODIS de hoy**. La causa raíz es el corrimiento del píxel MODIS con el ángulo, no el umbral de la caja. Si eso se corrige, el veto pierde su premisa (A111): conviene anotarlo así en el cierre y no como «la caja apaga alertas».

**Veredicto global: CONFIRMADO** como resultado del pre-registro. La atribución causal es PARCIAL: es posición, pero no D17.

**Defectos propios.** No miré la imagen de MIROVA ni el HDF. Usé el `vent_lat` de `volcanoes.yaml`. No comprobé la convención de submuestreo de MYD021KM ni el signo del paralaje. El patrón sale de 13 pasadas de un solo volcán.
