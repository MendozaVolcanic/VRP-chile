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
2. **Ventana de vecinos**: sólo hasta 7x7 (recomendado); un brazo con 8 vecinos sólo si el probe del L1B muestra que
   cambia más de 5 % en Chillán (umbral elegido); si el probe no corrió a tiempo, sólo 7x7.
3. **MODIS**: fuera de este A/B (recomendado) y decidir si se escribe el flag con lo que muestre el probe, o escribirlo
   antes y meterlo.

**Probe del L1B de Chillán** (`probe_l1b/`): escrito y probado, todavía sin correr porque el servicio CMR de NASA está
caído (HTTP 500 desde la mañana del 2026-10-20); se relanza solo al volver. Su resultado, cuando exista, va en
`probe_l1b/README.md`, sección «Resultado».

**Verificador limpio**: PARCIAL, 20 hallazgos, todos incorporados en la versión 2 (`PREREGISTRO.md` §10).

Rutas: `D:\vrp-trabajo\s157-prereg-d25\experiments\_s157_prereg_d25\PREREGISTRO.md` y este archivo,
`D:\vrp-trabajo\s157-prereg-d25\experiments\_s157_prereg_d25\RESUMEN_SELLO.md`.
