# Verificador con contexto limpio: tarea 1.20 (techos latentes de M15 e I04)

Medición verificada: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s151_techos_120\INFORME.md` (rama `loop/activo`) y su material en `C:\Users\nmend\AppData\Local\Temp\claude\techos_120\`.
Código leído en `origin/main` d9b104826 (2026-10-16 09:24 UTC); `git diff origin/main HEAD -- pipeline/` vacío. Flags leídos de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent` (A89), no del YAML.
Mis scripts y salidas: `C:\Users\nmend\AppData\Local\Temp\claude\verif_120\scripts\` (`chillan_4.py`, `cotas.py`, `i05_cota_m15.py`, con sus `.txt`). Sólo lectura: no toqué el repo.

## Veredicto global: PARCIAL

La conclusión central del hallazgo 1 (el techo de M15 no borra nada hoy) se sostiene, y la refuerzo con un instrumento independiente. Pero hay tres cosas que el informe dice mal o se queda corto: el Test 1 rescata bastante menos de lo que se afirma; el hallazgo 2 subestima el bit de saturación de I04, que es justamente la versión D24 del problema y está cerca de actuar **hoy** en la erupción de Chillán; y el «indicio» de 2025-02-27 casi con seguridad no es una erupción.

---

## 1. Lectura del código (A6): PARCIAL

**Confirmado, trazando llamadores:**
- `aplicar_techo_saturacion_mband` (`pipeline/process_viirs_mod.py:185-194`) pone NaN en M15 a 342,5 K o más (l. 286); M13 no se toca salvo su propio techo de 633,5 K.
- NTI NaN por `valid_both` (l. 551-558). Eso apaga para el píxel el camino B (`nti_path_hot`, l. 669-676), el D (`dual_roi_contextual_dnti_hot_mask`), el primer pase (`first_pass_tests_2_and_3`, `detection_context.py:479`, `mask_valid_eti` exige NTI finito) y el segundo pase (`detection_context.py:919`, el dNTI hereda el NaN). El kernel de 8 vecinos es `nan`-consciente (`_nanmean_8neighbors_fast`, l. 182-190), así que el hueco **no** se propaga a los vecinos: no los apaga, sólo les quita el vecino caliente del promedio.
- `compute_test1_mir` (`pipeline/test1_integrated.py:348`) lee sólo `bt` = M13, ROI de 3 km (`TEST1_ROI_KM = 3.0`).
- `t_max_k` sale de `roi_bt_full` = M13 en la caja ROI (l. 1134-1135): no se entera del techo de M15.
- El VRP se calcula con M13 sobre `hot_mask_2d` (l. 1035-1047): un píxel no detectado no suma.

**Corrección: el Test 1 no «rescata» el píxel dentro de 3 km en general.** Con `ENABLE_FIRST_PASS_TESTS_2_AND_3 = True`, `hot_mask_2d` se **reemplaza** por `fp_hot` (l. 908) y el Test 1 no entra al cúmulo. Sólo aporta magnitud si la fuente *legacy* termina en `"test1"` (l. 1262 y 1290), y eso pasa sólo en dos casos (l. 1196-1215): (a) el Test 1 es la única fuente (`n_nti_path`, `n_dnti_ctx_path`, `n_eti_path` y `n_bt_path` en cero), o (b) su centroide cae dentro de `inner_radius_km` **y** el píxel de mayor VRP del cúmulo contextual cae fuera. En el escenario realista del techo, que es un foco intenso con halo, los vecinos del píxel saturado pasan los Tests 2 y 3 cerca del cráter, el `hotspot` queda dentro del inner, y el Test 1 **no** reemplaza: el píxel más caliente queda como agujero **también dentro de los 3 km**. El rescate funciona sólo cuando el píxel saturado está solo (cúmulo de 1 píxel). La etiqueta `ctx_cluster` de los records es del ancla honesta (l. 1398-1413) y cambia sólo la posición, no la magnitud. Los records de Chillán de octubre de 2026 muestran el caso: `triggered_test1 = True` con fuente `ctx_cluster` y 2 a 9 píxeles (por ejemplo, 2026-10-10 06:30 SNPP_750: 5 píxeles, el más caliente aporta 16,2 de 25,9 MW). Si ese píxel perdiera M15, se perderían esos 16,2 MW sin rescate.
Cuando el rescate sí ocurre, la magnitud pasa por `cluster_focal_vrp_mw` con `FOCAL_CLUSTER_KEEP_PEAK = True`, que conserva el pico. Ese detalle está bien.

## 2. La «cota física»: CONFIRMADA en su conclusión, con dos matices

**¿Puede M15 pasar 342,5 K con un VRP bajo la cota de 32 a 37 MW?** Sí. La cota supone emisividad 1 en las dos bandas y fondo de 250 a 290 K. Con emisividad a 4 µm menor que a 11 µm (silicatos, ε13 de 0,7 a 0,9) o con fondo tibio, el mínimo baja a **16 a 30 MW** (`cotas.txt`). O sea que «cota absoluta» es una cota de cuerpo negro, no absoluta. **Pero el «26.181 no pudieron alcanzarlo» no depende de esa cota**: se apoya en `t_max_k` bajo 327,5 K con un margen de 15 K entre M15 y M13. Ese margen cubre el peor caso de emisividad que calculé (8,9 K con ε13 = 0,7). De noche ninguna superficie natural llega a 342 K, y en un píxel mezcla con lava M13 queda muy por encima de M15.

**Instrumento independiente (nuevo).** La gemela V375 de cada pasada trae `t_max_i05_k`: I05 (11,45 µm, 375 m) ve el mismo objeto con menos mezcla que M15 (750 m). Sobre 23.721 records V750 con gemela, **ninguna gemela tiene I05 de 320 K o más**. El máximo de todo el corpus V375 es **319,51 K** (Chillán 2025-02-27 05:18 NOAA-21), y las gemelas de los 4 candidatos dan de 298,6 a 319,5 K (`i05_cota_m15.txt`). Eso confirma, por otro camino, que M15 quedó lejos del corte.

**Matiz sobre el «M15 implícito» de 292 a 301 K.** Usa `nti_max`, que es un máximo sobre la ROI y por eso es mayor o igual que el NTI del píxel de `t_max`. El M15 que sale de ahí es una **cota inferior**, no el valor: el I05 de 318 a 320 K sugiere que el M15 real de esas dos pasadas estaba más cerca de 300 a 320 K. La conclusión no cambia, porque la sostiene el argumento de detección (los 4 picos están en `anomaly_pixels` con fuente distinta de `test1`, lo que exige NTI finito; verificado en `chillan_4.txt`) y ahora también el I05.

**A90.** El corpus ya tiene 26.222 records V750 (eran 26.185 cuando corrió el informe). Hay un record de 326,89 K del 2026-10-15 06:00 NOAA-21, en la erupción en curso y a 0,6 K de la cota de 327,5 K del informe. Con el I05 de su gemela (≤ 320 K) igual queda lejos del corte de M15.

## 3. El cero de hoy (A116): PARCIAL

- Instrumento del corpus: **puede** dar distinto de cero. Dio 4 candidatos, que se despejaron después.
- Contador del probe (`saturacion.py:70-81`): tiene control positivo **sintético** (`tests/test_saturacion_chillan_s151.py`, con saturados sembrados, uno en el techo sin bit), pero el verificador de 1.18 ya advirtió que ese control sólo prueba coherencia interna. Para el techo de M15 no existe caso real: confirmado.
- **Para I04 el cero está por romperse, y el informe no lo ve.** Los máximos de I04 del corpus se amontonan en **353,26 a 354,24 K** en NOAA-21 (cuatro noches distintas: 22, 23, 27 y 28 de febrero de 2025) y en 353,56 K en NOAA-20. Mientras tanto, el M13 de las mismas pasadas varía entre 317 y 361 K. Un máximo que no sigue la intensidad del foco es la firma de un techo: el I04 que sobrevive llega a ~354 K, y lo que pasa de ahí desaparece. Es coherente con el diseño (saturación a ~1,2 veces la señal de Tmax, ATBD Rev C p. 81, página renderizada y verificada), **corregido por el error de centro de banda**: el cálculo monocromático del informe sobrestima en ~6 K el BT del tope (I04: 367,7 K calculado contra 361,78 K de la LUT real; M15: 381,4 contra 374,6 K). Así, los «~359 K» del informe equivalen a ~353 a 354 K en la escala de la LUT, justo donde están amontonados los valores.
- **En la erupción en curso**: Suomi NPP dio **355,96 K en el cráter de Chillán** (2026-10-16 06:18, a 0,49 km) y 347,12 K el día anterior. Suomi NPP parece saturar algo más arriba que NOAA-21, pero el cráter ya está en el borde. Si la actividad sube, el bit borra el píxel del cráter en V375: el agujero D24 aparece en el producto que el operador más mira. Ese es el control positivo real que falta, y está ocurriendo ahora.
- Consecuencia para el **hallazgo 2**: «la defensa secundaria nunca dispara en NOAA-21, pesa poco» es correcto. Pero tratar el bit como «defensa que queda» invierte el problema: el bit es el que borra señal, y lo hace desde ~354 K, no desde 359 K ni desde 361 K. El «Borra señal hoy: no» es cierto para el techo y probablemente falso para el bit en febrero de 2025 (ver punto 4).
- Por la misma corrección de centro de banda, en M15 la ventana que el techo borra «sin otra razón» va de 342,5 K a **~352 K** (LUT), no a ~359 K: es más angosta de lo que dice el informe.

## 4. El indicio de 2025-02-27: PARCIAL

**Lo que se sostiene, y sale reforzado:** la pasada NOAA-21 de 05:18 es la misma en los dos records (gránulo `VJ202IMG.A2025058.0518.021`). Da I04 de 353,64 K a 14,14 km y M13 de 361,19 K a 14,8 km: el mismo objeto. A 375 m y a longitud de onda más corta, el I04 de un foco sub-píxel debería superar al M13; que quede 7,5 K abajo indica que faltan los píxeles más calientes. Suomi NPP 05:42 repite el patrón (352,04 contra 364,86 K) y NOAA-20 06:06, con un foco más débil, no (348,66 contra 333,33 K). A eso se suma el amontonamiento en ~354 K del punto 3.

**Lo que no está demostrado:**
- «Sólo el bit pudo borrarlos». Descarta el techo (correcto en NOAA-21, porque el tope de la LUT de 361,00 K queda bajo el corte), pero no descarta los DN centinela (`FLAG_DNS`), el relleno de la LUT (`bt < 0`) ni un «doblado» (*folding*) de I4 saturado que entregue un valor bajo en vez de borrar. Sin el gránulo no se distinguen; el P1 lo cierra.
- «En esa erupción» (texto del encargo; el informe dice, bien, «origen no verificado»). El objeto está **a 12 a 19 km al oeste del cráter** (lon -71,50 a -71,58), en el valle bajo, y **se mueve entre noches** (15 km el 26, 14 y 19 km el 27, 12 km el 28). MODIS Aqua ve 239 píxeles y 186 MW el 26. Hay actividad desde el 15 de febrero. Es la geometría de un **incendio forestal**, no de una fuente volcánica. Busqué en la web un incendio en Pinto o Coihueco para esas fechas y **no lo encontré** (las búsquedas sólo devolvieron incendios de marzo de 2025 y de 2026): queda como inferencia por geometría, **SIN VERIFICAR**. Hay que dejar de llamarlo erupción. Igual sirve como control positivo de saturación, porque al detector le da lo mismo de dónde viene el calor.

## 5. La propuesta (tope de la LUT del gránulo menos 0,5 K, con el bit como defensa principal): PARCIAL, choca con D24

- **Con A37 no choca.** Usa el esquema propio de VIIRS (bit 2 más radiancia recortada), no el centinela de MODIS.
- **Con D24 sí choca, en dirección.** D24 (`docs/MIROVA_DIVERGENCES.md`, l. 2673) registra que el paper **conserva** los saturados marcados (`sp426.5.pdf` p. 3). La propuesta mantiene el borrado por bit, que según el punto 3 actúa desde ~352 K en M15 y ~354 K en I04. Sólo cambia 342,5 K por ~352 K: el agujero D24 en M15 sigue ahí, una ventana más arriba. Y la parte del «tope de la LUT menos 0,5» queda casi redundante, porque el bit dispara antes de llegar al tope.
- **Alternativa más fiel y de bajo riesgo en M15:** conservar el valor recortado y marcarlo. En V750, M15 sólo entra al NTI y al ETI (no hay VRP TIR; `grep vrp_tir` en `process_viirs_mod.py` da 0). Un M15 recortado por abajo sube el NTI: el píxel se detecta igual y no aparece la basura que motivó F28 (que era el VRP TIR de I05 a 423 K, comentario en `process_viirs.py:368-371`). En I04 conservar el recortado afecta la magnitud MIR (la subestima, como MIROVA con los saturados), y eso hay que pensarlo aparte.
- **Fidelidad a MIROVA:** lo que hace MIROVA con VIIRS saturado sigue SIN VERIFICAR, como dice el informe. Cualquier cambio tiene que pasar por las 3 preguntas de MISSION y por A45 (toca `process_viirs*.py`). La extensión de D24 a VIIRS (M15 **e I04**) debería registrarse; hoy D24 habla sólo de MODIS.

## Prioridad que sugiere esta verificación

El riesgo vivo no es el techo de M15. Es el **bit de I04 en el cráter de Chillán** durante la erupción en curso: Suomi NPP ya da 355,96 K y el techo efectivo observado está en ~354 K. Antes del P2 (erupciones lejanas), conviene correr el P1 sobre las pasadas de octubre de 2026 de Chillán y sobre `VJ202IMG.A2025058.0518`, contando píxeles con bit **dentro de la caja de 25 km**.
