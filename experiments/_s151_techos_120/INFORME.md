# Tarea 1.20: cuánto pesan los dos techos latentes (sólo lectura)

Código leído en `origin/main` 3591d9d0 (sin diferencias en `pipeline/` con `loop/activo`). Scripts y salidas en `C:\Users\nmend\AppData\Local\Temp\claude\techos_120\scripts\`. Páginas renderizadas a imagen en `C:\Users\nmend\AppData\Local\Temp\claude\techos_120\paginas\` (A95).

## Hallazgo 1: techo de M15 en 343 K (`pipeline/process_viirs_mod.py:182`, aplicado en 286)

**Qué pasa con el píxel.** `aplicar_techo_saturacion_mband` pone NaN sólo en **M15** cuando su BT es 342,5 K o más; M13 queda intacto. Consecuencias: el NTI del píxel queda NaN (l. 551-558), así que el píxel **no puede pasar los Tests 2 y 3** (primer pase, l. 851) **ni el segundo pase** (`detection_context.py:919`, el dNTI hereda el NaN). El Test 1 lee sólo M13 (l. 756) y puede rescatarlo, pero **sólo dentro de 3 km del cráter** (`TEST1_ROI_KM = 3.0`, leído de `pipeline.profile`). El VRP se calcula con M13, pero sólo sobre píxeles detectados: fuera de esos 3 km el píxel más caliente queda como **agujero** en el cúmulo y su radiancia no se suma. `t_max_k` no se entera (sale de M13). Es la versión M15 de **D24** (MODIS borra DN 65533; Coppola 2016a, p. 3 de `sp426.5.pdf`, columna izquierda, conserva los saturados).

**Cuándo puede ocurrir** (`ventana_fisica_m15.py`, modelo de dos componentes): de noche M15 llega a 342,5 K con un VRP por píxel de al menos **32 a 37 MW** (píxel uniforme a 342,5 K, cota absoluta), **160 a 230 MW** con lava a 500 K y **690 a 2.030 MW** con lava a 800 a 1.150 K; M13 sigue midiendo (414 a 556 K, bajo 634). Sólo una erupción efusiva grande lo activa.

**Huella en el corpus** (`huella_corpus.py`, `cota_vrp_y_m15_implicito.py`; 26.185 records V750, 2025-02-15 a 2026-10-16). El JSON **no guarda M15** (A89), así que uso una cota: de noche M15 no supera a M13 en más de ~15 K. **26.181 records** tienen `t_max_k` bajo 327,5 K, donde M15 no pudo llegar al corte. Los **4** restantes son Nevados de Chillán, 26 y 27 de febrero de 2025, con píxeles a 14 a 19 km al oeste del cráter (origen no verificado); en los cuatro el píxel más caliente **fue detectado** por los Tests 2 y 3 sin Test 1, lo que exige M15 finito, y su M15 implícito por el NTI es **292 a 301 K**. El máximo VRP por píxel del corpus V750 es **67,5 MW**. Run 38863912173 (154 gránulos V750): **0** borrados por techo y **0** con bit en M15 (`techos_y_bits_run38863912173.py`). **Borra señal hoy: no, 0 records y 0 píxeles.** **Control positivo: no existe** ni en el corpus ni en el run.

**Matiz a «válido hasta 374 K»** (`rango_lut_vs_tmax.py`): el tope de la LUT (Tabla C.3, p. 42 del User Guide L1B) equivale a **1,5 veces** la señal de Tmax (381,4 contra 381,7 K en centro de banda), y el ATBD Radiométrico Rev C (p. 81) dice que el detector satura por diseño a **~1,2 veces** (~359 K en centro de banda), antes del tope. Sobre ese punto el bit 4 ya borra. Lo que el techo borra sin otra razón es **de 342,5 K al punto de saturación real**, que no está medido. La Tmax 343 K de Campus 2022 (Tabla 1, p. 6) es especificación (Tabla 2, p. 6 del ATBD), no saturación. MIROVA: Campus 2022 (p. 7, §3.2) dice que la detección «is the same used for MODIS» y no habla de M15 saturado: lo que hace MIROVA con M15 caliente queda **SIN VERIFICAR**.

**Propuesta (no implementada, A45).** Reemplazar el 343 fijo por el tope de la LUT **del propio gránulo** menos 0,5 K, con el bit 4 como defensa principal, y anotar el caso como extensión de D24 a M15. Antes, el probe P2.

## Hallazgo 2: la LUT de I04 de NOAA-21 queda bajo el corte de producción

**Confirmado** en los 46 gránulos NOAA-21 del run: tope de LUT **361,00 K**, contra el corte `361,77 − 0,5 = 361,27 K` (`process_viirs.py:373, 400-402`); NOAA-20 361,70 y Suomi NPP 361,78. En NOAA-21 la defensa secundaria nunca dispara.

**Defensa que queda: el bit 4, y funciona en ese satélite**: **263 píxeles en 23 de 46 gránulos** NOAA-21 (13 de noche en 8). Por la Tabla C.1 (p. 41) un DN de 4095 o más fija el bit y lleva la radiancia al tope; como el detector satura (~1,2 veces Tmax) antes del tope de la LUT (1,5 veces), un píxel en el tope sin bit 4 sólo puede venir de un `Out_of_Range` (valor 2) sin saturación, que el diseño no espera salvo deriva de ganancia. **Huella**: un píxel así quedaría con `t_max_k` de 361,0 K; en **26.386 records V375** no hay ninguno de 360,5 K o más en ninguna plataforma (máximo NOAA-21 354,24 K; `huella_corpus.py`). Indicio, no medición: el 2025-02-27 05:18 NOAA-21 da I04 máximo 353,6 K con M13 de 361,2 K en la misma pasada; I04 a 375 m debía estar más caliente, así que sus píxeles más calientes faltan, y con el corte a 361,27 sólo el bit pudo borrarlos. **Borra señal hoy: no** (el defecto dejaría pasar basura, no borra), **peso bajo**.

**Propuesta.** El mismo cambio del hallazgo 1 (tope de la LUT del gránulo) lo cierra en los tres satélites; alternativa, enmascarar también el valor 2 por arriba. Probe P1 antes.

## Probes propuestos (GitHub Actions, sin implementar)

- **P1**: en los 23 gránulos VJ202IMG con bit (lista en `techos_y_bits_run38863912173.py`, p. ej. `VJ202IMG.A2026281.0630.021`), tabla cruzada de I04 en el tope de la LUT contra los valores 4 y 2 del flag. Cierra el hallazgo 2 si todo píxel en el tope trae el 4.
- **P2**: gránulos VNP02MOD/VJ102MOD de erupciones efusivas grandes (candidatos, sin saber si llegan: Holuhraun 2014, Kilauea fisura 8 2018, Sundhnúkur 2023-2024): máximo de M15, píxeles de 342,5 K o más sin bit 4 y su M13. Es el control positivo que falta.
