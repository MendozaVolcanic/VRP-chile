# Verificador del probe S151 MxD03 (run 38733452917)

Script y salida: `C:/Users/nmend/AppData/Local/Temp/claude/verifmod03/recalcular.py` y `salida_recalculo.txt`.

**1. PARCIAL bien aplicado: CONFIRMADO.** La condición 1 falla: los residuos del barrido son −0,24, −0,02, +0,05, **+0,36**, **−0,45**, −0,14 y +0,08 km. La condición 2 se cumple (2,58, 2,21 y 1,15 km hacia el sensor). Ninguna condición de REFUTA se da.

**2. Compara lo correcto: CONFIRMADO.** El probe lee lat y lon de MxD03 a 1 km, con la misma forma que la banda 22, y le aplica la `_interp_geo` real. Toma como cráter el píxel que MxD03 pone más cerca del vent y proyecta la diferencia sobre vectores locales de barrido y de traza. El signo, sacado de `SensorAzimuth`, coincide con el «este» de #825. Además, `offsets_grilla_km` da **0,0000 en offset 2, en los dos ejes y en los 7 gránulos**: la grilla de L1B es MxD03 submuestreada.

**3. Por qué el modelo sobrestima: PARCIAL.** El mecanismo es compatible, pero no está medido. `_interp_geo` sí trae terreno en los nodos de 5 km; lo que le falta es el de 1 km.
- **Relieve.** En los 6 gránulos con cenit ≥ 30° el residuo hacia el sensor es negativo, y ese signo es el que da el relieve. El orden de magnitud también calza: 300 a 450 m de relieve (`alturas_dem.json`) por tan θ dan 0,2 a 0,45 km. El paralaje absoluto de 5,6 km se cancela, porque los dos lados lo traen.
- **Bow tie, en el de 43°.** Es el único donde la interpolación cruza entre barridos (líneas 37 y 42). Eso explica su traza: +0,77 observado contra −0,26 predicho.

**4. Grande donde importa: CONFIRMADO.** En el cráter, la diferencia total es 2,62, 2,27 y 1,17 km en el lado del frame 0 con cenit ≥ 30°, y de 0,86 a 1,72 en los demás gránulos (incluido el de 10°, por la traza). Hay un control independiente: en los 3 gránulos donde el píxel más brillante en banda 22 cae en el cráter, MxD03 lo pone a 0,13, 0,18 y 0,35 km del vent, y `_interp_geo` a 1,29, 1,02 y 1,10 km. Eso basta para leer MxD03, calce o no el modelo.

**5. Traza: CONFIRMADO el offset 2.** Desfase de 0,0 km en la línea 2, contra 2,27 en la línea 0. `pred_traza` calza dentro de 0,2 km en 6 de 7 gránulos.

**6. `pixel_brillante_b22_*`.** Es el máximo de banda 22 a menos de 8 km, ubicado con cada geolocalización. En las pasadas del veto cae a 4 a 7 km del vent: no es el píxel del veto (3,20 km al este). **No dice nada de la caja.**

**Veredicto global: PARCIAL.** El defecto existe y pasa de 1 km. El modelo no calza por terreno y bow tie, no por otra causa. SIN VERIFICAR: otros volcanes, y la posición MxD03 del píxel del veto.

**Recomendación.**
- Leer MxD03 en producción, con tag y el sí de Nicolás (A45). Corregir sólo el offset del zoom deja entre 0,2 y 1 km de error.
- Mantener el veto de la caja con su premisa marcada en duda, y volver a medir la caja después del arreglo. Si se le resta el corrimiento de 2,2 km, el píxel del 03-27 quedaría a unos 1 km (estimado).
