# Probe de saturación del sensor en Nevados de Chillán (S157)

> Escrito el 2026-10-20 **antes de correr**. Sólo lectura: no toca `pipeline/` ni los perfiles, no escribe en `data/`.
> Workflow `.github/workflows/probe-s157-saturacion-chillan.yml`, 2 jobs, grupo de concurrencia propio, autenticación
> sólo por `EARTHDATA_TOKEN` (A71). El resultado, cuando exista, va en `resultado/` con el número de run.

## Por qué

Con el sensor oblicuo nuestra magnitud de Chillán en erupción queda muy bajo la de MIROVA (VIIRS 750, 2026-10-18
06:48, cenit 67,6°: 2,84 contra 22,85 MW). El probe de #871 (`../_s157_prereg_d25/probe_l1b/`) midió que el fondo
(D25) sube esa pasada ×2,16 y que los vecinos no alertados suman a lo más 0,06 a 0,70 MW: lo que queda apunta a D17
(área, remuestreo) o a **saturación**. #869 notó además que VIIRS 375 trae menos energía que VIIRS 750 en la misma
pasada, también en MIROVA, y lo dejó como «saturación probable, sin verificar».

La saturación importa por cómo la trata el pipeline. Un píxel saturado no entra con un valor tope: **se borra**.
En VIIRS, `read_viirs_l1b` y `read_viirs_mod_l1b` ponen NaN donde el bit 4 (Saturation) de los quality flags está
encendido, donde la BT llega al tope de la LUT y, en las bandas M, sobre el techo de Campus 2022 (M13 634 K, M15
343 K). En MODIS, `calibrate` descarta todo SI > 32767, que incluye 65533 («Detector is saturated»). Y basta que
sature la banda **térmica** (I05, M15, B31) para que el NTI quede en NaN y el píxel no se alerte nunca, aunque su
MIR esté sana. Si eso le pasa al píxel más caliente del cráter, la energía que falta es justo la del foco.

El bit está verificado contra el UserGuide (`documentacion/VIIRS_L1B_UserGuide_Aug2021`, Tabla C.1: «4 = Saturation»,
asignado cuando el conteo L1A llega a 4095; la radiancia se fija al «Reported Range» de la Tabla C.3) y el probe guarda
los atributos `flag_masks` y `flag_meanings` del propio archivo para verificarlo contra el producto.

## Qué corre

Ver el docstring de `probe_saturacion.py`. Las pasadas salen de `seleccionar_pasadas.py` (`pasadas.json`), sin elegir
a mano, con la referencia congelada del pre-registro (`../_s157_prereg_d25/_congelado_v1`, ventana 2026-08-29 a
2026-10-18):

- **A.** Los 10 gránulos del 2026-10-18 de #871.
- **B.** Pasadas nocturnas de Chillán con cenit de 50° o más y alerta de MIROVA pareada de **1 MW o más** (las
  protegidas del criterio de `docs/MISSION.md`): 11 de VIIRS 375, 10 de VIIRS 750, 5 de MODIS (37 con cualquier VRP;
  las 11 bajo 1 MW quedan fuera porque ahí el déficit es de décimas de MW).
- **C.** Control casi a nadir (cenit menor que 15°), la noche más fría de la ventana sin alerta de MIROVA: VIIRS 375 y
  750 del 2026-09-30 05:42 y MODIS Terra del 2026-10-06 01:45.
- **POS.** Control positivo: MODIS Aqua de Planchón Peteroa del 2026-03-18 08:05, el gránulo de F28 con 113 píxeles
  SI = 65533.

## Controles (fijados antes)

- **C-SIN.** `prueba_saturacion.py`: el contador sobre una escena sintética con bits y topes puestos a mano encuentra
  todos y sólo esos, y la cota es k·A·(L − L_anillo). Corrido local antes de despachar: OK; con el bit mal puesto
  (`BIT_SAT = 2`) falla por aserción.
- **C-0.** Grupo C: 0 píxeles perdidos y 0 con bit 4 en la ventana.
- **C-POS.** > 0 códigos 65533 a ≤ 25 km de Planchón Peteroa. Si da 0, el contador de MODIS está ciego.
- **C-P1** (de #871): el control reproduce el record persistido. **C-IDX**: los índices del cúmulo capturado caen sobre
  los píxeles anómalos del record. Si alguno falla, la pasada se informa y no se interpreta.

## Regla de lectura (escrita antes)

Por pasada, con `falta` = VRP de MIROVA menos lo que publicamos (núcleo F5' en VIIRS 375, cúmulo en VIIRS 750 y MODIS):

- **descartada**: 0 píxeles perdidos en la ventana y ningún píxel del cúmulo con bit 4 o en el tope de la LUT. La
  saturación aporta exactamente 0 al déficit de esa pasada.
- **cierra**: la cota inferior de energía de los perdidos es mayor o igual que `falta`.
- **indeterminada**: hay perdidos o recortados pero la cota no alcanza. La verdadera energía puede ser mayor (la MIR
  saturada sólo da un piso), así que no decide.

## Predicciones (escritas antes)

- **PS-1, VIIRS 750.** M13 es de doble ganancia y su techo de reporte es ~634 K; las BT del cúmulo están entre 270 y
  320 K. Predigo **0 perdidos y 0 bits 4 en M13** en todas las pasadas, oblicuas o no: en VIIRS 750 la saturación
  queda descartada y el déficit oblicuo (06:48: falta ~20 MW) es de D17 u otro efecto del ángulo. La única vía abierta
  sería M15 sobre 342,5 K, que no espero con M13 bajo 320 K.
- **PS-2, VIIRS 375.** I04 satura cerca de 368 K (Reported Range 4,659 W m⁻² sr⁻¹ µm⁻¹, Tabla C.3) y el `t_max_k` del
  record llega a 335 K. Como un píxel borrado no aparece en `t_max_k`, no lo puedo descartar de antemano. Si hay
  saturación en Chillán, espero que sea **más frecuente cerca del nadir** (píxel más chico, foco más resuelto) que en
  el borde, lo contrario de lo que haría falta para explicar el déficit oblicuo.
- **PS-3, MODIS.** B22 satura en ~331 K pero con K entra la B21 donde la 22 satura, así que el píxel sólo se pierde si
  saturan las dos o la B31. Predigo 0 perdidos.

## Lo que este probe NO decide

No mide D17: si la saturación queda descartada, D17 sigue siendo el candidato, no un hecho. Diez gránulos de una
mañana más 26 pasadas de un volcán son el caso, no la muestra.

## Intentos

- **Run 39511561148** (2026-10-20 22:55 UTC, `fc7834727`): los dos jobs abortaron en la primera y la segunda pasada
  con «sin gránulo» en la búsqueda, sin bajar nada (salida 3, el corte de las dos primeras fallas). No era defecto del
  probe: a esa hora CMR devolvía 0 gránulos VIIRS del 2026-10-18 y 0 del 19 (241 por día del 15 y 16; 5 de MYD021KM el
  18), mientras el listado del archivo de LAADS sí los tenía con el nombre exacto del record. Se agregó un respaldo que
  baja L1B y GEO del archivo de LAADS cuando CMR no los indexa (`bajar_laads`), y se reintentó el mismo workflow, como
  hizo #871 tras el HTTP 500 de CMR.
- **Run 39512351523** (2026-10-20 23:00 UTC, `dcf8cf380`): CMR seguía sin el 18 y el 19 (verificado a las 23:05: 0
  VJ202IMG, 0 VNP02MOD). El respaldo encontró los archivos en el listado de LAADS, pero la descarga con la sesión
  devolvió 10.833 bytes que no eran el archivo, en las dos primeras pasadas de cada job, y abortó. Tercer intento
  (el último): el orden pasa a C, B, POS y A, para que las pasadas que CMR sí indexa (C y B, del 2026-09-28 al
  2026-10-16) no dependan de la caída del 18; el respaldo de LAADS usa `earthaccess.download` con la URL y guarda el
  comienzo de la respuesta si vuelve a fallar.

## Reproducir

```bash
python experiments/_s157_saturacion/seleccionar_pasadas.py   # arma pasadas.json, sin red
python experiments/_s157_saturacion/prueba_saturacion.py     # C-SIN, sin red
python experiments/_s157_saturacion/analizar_saturacion.py resultado   # lee los JSON del artefacto
```
