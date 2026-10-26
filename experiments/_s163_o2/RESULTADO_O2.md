# O2: el código de MIROVA corrido en MATLAB (S163, 2026-10-26)

## Qué se hizo

El paquete O2 de S159 (`C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete\`, rama `s160-auditoria`) se corrió en
MATLAB Online (basic, cuenta de Nicolás) el 2026-10-26 ~02:15 UTC.

- Versión: MATLAB 26.2.0.3386108 (R2026b); `fillmissing2` y `colfilt` de las carpetas de MATLAB (no hay shim en la ruta).
- Los cuatro archivos se bajaron dentro de MATLAB con `websave` desde esta misma rama (commit `61267289e`), porque la
  subida por el navegador no aceptó archivos. md5 calculados dentro de MATLAB, iguales a los del paquete original:
  `entradas_o2.mat` fb849b6a96a9d348e75cf502e21a326c, `MIROVA_VIIRS750_VRP.m` b0ceebb2b7864cd27c145dc8d41968cc,
  `MIROVA_VIIRS750_hotspot_detection.m` ddffea3672a08e5aa17c702f72d72170, `correr_o2.m` e6761d861b61009b32991afd3f350986.
- Resultado: `resultado_o2.mat` (md5 1f7fdc4bed0f8cb6223204bbce42ba43, 1.899.622 bytes) y `salida_matlab.txt`
  (diario de MATLAB, md5 0dea1210337f9cd47210b615bebdaf67); md5 iguales en MATLAB Drive y tras la descarga.
- Lectura: `leer_o2.py` de `s160-auditoria` (`46664ad9d`) → `leer_o2_salida.txt`.

## Qué dice

1. **MATLAB reproduce a MIROVA en Etna, exacto**: Tot_Lmir_bk 1,072886152 y VRP 9.889.528,4 W, iguales al OSF v2.5. El
   resultado sirve como vara.
2. **Detección**: 0 listas de alertas distintas entre MATLAB y Octave en las 311 escenas (166 con alerta). La detección de
   los ports, ya validada contra Octave, queda validada contra MATLAB.
3. **VRP: ningún modelo de `fillmissing2` es el de MATLAB.** Contra MATLAB, diferencia mayor a 1 % en 32 de 166 escenas
   (shim de Octave), 26 (segundo port) y 45 (primer port); máximo 0,82. Iguales a 1e-9: 101, 101 y 86. En alertas de un
   píxel hay casos donde MATLAB no calza con ninguno (Villarrica 2026-09-19 05:48, variante nearest: MATLAB 0,4212 MW, los
   tres modelos 0,7438), otros donde calza con uno solo (Tupungatito 2026-03-01 05:36: MATLAB = segundo port 0,3943; Puyehue
   2026-10-10 05:54: MATLAB = primer port 0,9450).

Consecuencia: para la métrica de magnitud en alertas de un píxel, la vara no puede ser un port; tiene que ser la salida de
MATLAB (estas 166 escenas) o un port nuevo validado contra ella. Con 2 o más píxeles los ports quedan cerca. SIN VERIFICADOR
LIMPIO todavía.
