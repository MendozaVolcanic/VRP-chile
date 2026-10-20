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
asignado cuando el conteo L1A llega a 4095; para las bandas I y M la nota 1 de la p. 41 fija el DN en 4095, y lo de
la radiancia fijada al «Reported Range» es de la DNB, Tabla C.2; corregido tras el verificador) y el probe guarda los
atributos `flag_masks` y `flag_meanings` del propio archivo para verificarlo contra el producto (no se llegó a hacer:
ver Resultado).

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

## Resultado (run 39512756808, 2026-10-20 23:06 UTC, `454e66931`): el probe NO midió lo que quería medir

Tercer y último despacho (el coordinador pidió no volver a despachar). Salida: `analizar_saturacion_salida.txt`
(`analizar_saturacion.py resultado`), artefactos en `resultado/`.

- **Qué bajó.** 2 de 40 pasadas: el control C de MODIS Terra (2026-10-06 01:45, cenit 2,5°) y una oblicua del grupo
  B, VIIRS 750 de Suomi NPP del 2026-09-29 06:36 (cenit 55,8°; publicamos 0,329 MW, MIROVA 2,03).
- **Por qué no bajó el resto.** (1) Descargas de VJ202 (NOAA-21) rechazadas con HTTP 401 por
  `data.laadsdaac.earthdatacloud.nasa.gov`, las primeras dos del job V375, que abortó por el corte de las dos primeras
  fallas; la de Suomi NPP sí bajó. No se tocó ninguna credencial (A71). (2) **Defecto propio**: el job V750_MODIS se
  cayó al escribir el JSON de la pasada de Suomi NPP porque `flag_meanings` llega como arreglo de bytes. Arreglado
  después del run (`_a_texto`, `_a_json`), sin volver a correr. (3) El grupo A (2026-10-18) nunca llegó a intentarse
  en este run (iba al final); en los dos runs anteriores CMR no lo indexaba y LAADS no lo entregó.
- **Lo medido.** Control C de MODIS: 0 códigos SI > 32767 en B21, B22 y B31 en los 89 píxeles de la ventana, 0
  perdidos, C-P1 en verde (C-0 cumple, trivialmente: noche fría). Oblicua V750 del 29-sep (sólo en el log, C-IDX no
  quedó registrado, así que el agregado no la cuenta): **0 bits 4, 0 bits 2, 0 en el tope de la LUT y 0 perdidos por
  el lector en M13 y en M15** sobre 156 píxeles de la ventana, cota 0,0 MW contra una falta de 1,70 MW. Coincide con
  PS-1, pero es una pasada. (PS-1 decía «techo de reporte ~634 K»: ese es el techo de Campus 2022 que usa el pipeline; el de la Tabla C.3 es 683 K, línea 1 de la salida del análisis.)
- **Hallazgo lateral, sin verificar.** En esa misma ventana, **44 de 156 píxeles traen M15 en sentinela** (DN
  65532 a 65535) y M13 sano. Un sentinela no es saturación, pero el lector lo pone en NaN y el NTI de ese píxel no
  existe. Si el código es 65533 (Bowtie_Deleted), el terreno lo ve el barrido vecino y no se pierde nada; si es otro,
  sí. El contador no los contaba como perdidos (la BT cruda ya es NaN). Desde este commit el probe separa los
  sentinelas por código (`sentinela_codigos`). Que M15 tenga sentinelas y M13 ninguno en la misma ventana es raro y
  merece mirarse antes de creerlo.
- **C-POS** no se alcanzó (iba después de las oblicuas). El contador sólo quedó validado por C-SIN (en verde en los
  dos runners) y por el control nadir de MODIS.

**Verificador con contexto limpio** (en primer plano, mismo día). Confirma el bit (Tabla C.1, p. 40, renderizada;
la máscara se aplica a la banda correcta, como `process_viirs_mod.py`), los números de la pasada del 29-sep y el
veredicto, y observa:
- La cota 0 de esa pasada sale de **0 perdidos**, no de medir energía. Hay evidencia independiente más fuerte: el
  `t_max_k` persistido de esa pasada es **273,28 K** (`pasadas.json`), el máximo de M13 en todo el ROI, así que la
  saturación de M13 o M15 era físicamente imposible ahí sin necesidad del probe.
- Lo que el contador deja fuera: los sentinelas (BT cruda ya NaN), los píxeles del cúmulo que entran recortados en el
  tope (se cuentan aparte, sin cota), y en MODIS «perdido» es un modelo del probe, no la salida de `read_modis_l1b`,
  e incluye cualquier código SI > 32767. La cota supone que un píxel perdido se habría alertado.
- Los 44 sentinelas de M15 con M13 sano son **incoherentes con el bowtie**, que borra todas las bandas M: queda SIN
  EVIDENCIA qué son. El probe ahora cuenta las máscaras 256 (Bowtie_Deleted) y 2048 (Dead_Detector).
- Nombres: en este probe «bit2_oor» es la máscara 2 y «bit4_sat» la máscara 4; el pipeline llama «bit-2» a la
  máscara 4 (posición del bit). Mismo bit, dos nombres.
- El caso que motivó el probe (2026-10-18 06:48, falta de ~20 MW) **no se midió**. Pista del verificador, sin
  verificar: en esa pasada VIIRS 375 ve ~310 K; un foco así llenando parte de un píxel M debería subir M13 sobre los
  273 K que marca, lo que apunta a geometría (D17) más que a saturación.
Aplicado: corrección de la cita, máscaras 256 y 2048, fondo de MODIS en la longitud de onda de la banda de la que sale
la radiancia (B22 o B21), B22 en el veredicto de MODIS (recortada en 32767 cuenta; inválida no, porque con K entra la
B21), y C-SIN extendido a `crudo_viirs` (HDF5 sintético) y `contar_modis`, con mutaciones de las máscaras 4 y 256
atrapadas por aserción. C-POS sigue sin correr: el contador de MODIS no ha mostrado en datos reales que puede dar
distinto de cero.

**Veredicto.** Con una pasada oblicua medida no se puede decir si la saturación explica el déficit oblicuo de Chillán.
Lo único medido apunta a que no (0 saturados, cota 0 contra 1,70 MW de falta), igual que la predicción PS-1 por física
del sensor (M13 de doble ganancia, techo de reporte de 683 K según la Tabla C.3), pero es el caso, no la muestra.

## Reproducir

```bash
python experiments/_s157_saturacion/seleccionar_pasadas.py   # arma pasadas.json, sin red
python experiments/_s157_saturacion/prueba_saturacion.py     # C-SIN, sin red
python experiments/_s157_saturacion/analizar_saturacion.py resultado   # lee los JSON del artefacto
```
