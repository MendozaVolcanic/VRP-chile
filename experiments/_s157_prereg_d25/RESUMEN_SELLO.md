# D25 sobre K, para sellar: una pantalla

**Qué se quiere saber.** Si restar como fondo la media de los vecinos del cráter (lo que hace MIROVA, D25) en vez de
la mediana del anillo de 5 a 25 km acerca nuestra magnitud a la de MIROVA sin publicar donde MIROVA calla. Caso:
Chillán en erupción, donde con el sensor oblicuo (cenit de 50° o más) nuestra razón mediana contra MIROVA es 0,45 en
VIIRS 375 y 0,16 en VIIRS 750 (PR #869).

**Lo nuevo que ya está medido (en disco, sin correr nada).** Con la detección vieja, D25 en VIIRS 750 encendía 268 de
268 negativos limpios con el cráter en cero. Con K esa población es de **17 y 21 pasadas en VIIRS 750 y de 0 y 2 en
VIIRS 375** (ventanas V1 y V2), del mismo orden que lo que D25 podría recuperar (11 y 23 alertas en VIIRS 750). El
riesgo de sobre-publicación de D25 sobre K es chico y medible (`sustrato_k_salida.txt`), y en noches es cero en VIIRS
750: todo cae en noches que K ya publica por otra pasada (verificador, `verificador/v3_salida.txt`). Ojo: en VIIRS 375
cinco volcanes ya restan sus vecinos (kernel local) y ahí D25 casi no cambia nada; se miden aparte.

**Brazos.** K (la réplica de hoy), K' (K otra vez, para medir el ruido del runner) y D (K más D25 en VIIRS 375 y 750).
MODIS fuera: D25 no existe en `process_modis` y escribirlo es tocar el pipeline (A45).

**Ventanas.** V1, 2026-08-29 a 2026-10-18 (tabla y OCR, Chillán en erupción, con gemelo). V2, 2026-04-01 a 2026-06-12
(tabla sola, poder del veto, en dos mitades). Sólo VIIRS en todas las pruebas.

**Cómo se decide** (lectura A, regla SN, por sensor, por tramo de cenit ≤ 40° y > 40°, por ventana):
- **Veto**: ninguna protegida (1 MW o más) que K publica puede dejar de publicarse. Las que crucen de 1 MW hacia abajo
  se listan y decides tú.
- **Suma bajo 1 MW**: alertas débiles perdidas más publicaciones donde MIROVA calló; D no puede quedar peor que K más
  el ruido del gemelo.
- **Magnitud**: en las alertas que los dos publican, D tiene que quedar más cerca del VRP de MIROVA que K (escala
  logarítmica, pasarse cuenta igual que quedarse corto), con intervalo al 95 % por bloques de noche y una regla
  calibrada contra los mismos datos (falsas mejoras en 5 % o menos). Decide en **VIIRS 750 en todo el cenit** y en
  **VIIRS 375 sin kernel con cenit ≤ 40°**; en VIIRS 375 sin kernel con cenit > 40° **sólo puede bloquear** (un
  empeoramiento por pasarse impide adoptar, una mejora no cuenta), porque ahí en Chillán D25 no puede cerrar pero en los
  focos débiles sí puede pasarse.
- **Informa sin decidir**: si el cúmulo cambia de lugar (y si toca una protegida, auditoría espacial antes de adoptar),
  el tope de 5 MW que esconde el alza en escenas frías, y las publicaciones que apagan los filtros del tablero.

**Resultado por veredicto.** CUMPLE (veto limpio, suma sin perder, magnitud mejora en algún estrato y no empeora en
ninguno, en las dos ventanas): se abre el ciclo de adopción, con tu «sí» al final. Magnitud neutra en todo: decides tú (D25 es fidelidad
literal). Veto o suma perdida: no se adopta.

**Costo.** ~22 a 31 h de grupo de runners en serie (3 despachos), desde un tag, no antes de que terminen los
reprocesos de Chillán.

**Antes de despachar** (candado): el evaluador `evaluar_d25.py` con sus pruebas que fallan por la razón correcta y un
verificador limpio, como en la adenda K del diurno.

**Lo que tienes que decidir** (detalle en `PREREGISTRO.md` §8):
1. **VIIRS 375 oblicuo**: que sólo pueda bloquear (recomendado), que decida en las dos direcciones, o que sólo informe.
2. **Ventana de vecinos**: resuelta por la regla del pre-registro con el probe (8 vecinos y 7x7 dan idéntico): sólo 7x7.
3. **MODIS**: fuera de este A/B (recomendado) y decidir aparte si se escribe el flag (el probe dice que en Chillán sí
   movería la magnitud), o escribirlo antes y meterlo.

**Probe del L1B de Chillán** (10 gránulos del 18-oct, controles en verde, `probe_l1b/README.md`): D25 sube VIIRS 375
×1,08 a 1,09 en todo el cenit (a las 06:48 la razón pasa de 0,35 a 0,38) y VIIRS 750 ×1,13 a 1,14, y ×2,16 en la pasada
de las 06:48 (0,12 a 0,27). Los vecinos del cráter son nieve 6 a 12 K más fría que el anillo, y aunque MIROVA los
sumara todos no cerrarían nada (0,06 a 0,70 MW contra 2 a 17 que faltan): en Chillán el resto del déficit oblicuo no es
fondo ni selección, queda para D17 o saturación. La ventana 1 contra 3 da lo mismo (decisión 2 resuelta: sólo 7x7). En
MODIS, el análogo de D25 sube Chillán ×1,32 y ×2,45 (razón 0,49 a 0,64 y 0,24 a 0,59), y el kernel 3x3 que ya existe da
lo mismo.

**Verificador limpio**: PARCIAL, 20 hallazgos, todos incorporados en la versión 2 (`PREREGISTRO.md` §10).

Rutas: `D:\vrp-trabajo\s157-prereg-d25\experiments\_s157_prereg_d25\PREREGISTRO.md` y este archivo,
`D:\vrp-trabajo\s157-prereg-d25\experiments\_s157_prereg_d25\RESUMEN_SELLO.md`.
