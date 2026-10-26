# Distancia de Dist.png en vez de la del OCR: cuántas alertas cambian de lado

2026-10-16, sólo lectura (no se tocó VRP Chile ni Mirova-v1). Todo vive en
`C:\Users\nmend\AppData\Local\Temp\claude\cambian_lado\`; cada número cita su script y su salida.
Referencia: la unificada (`scripts\referencia_mirova_unificada.py::cargar_referencia_unificada`, con unión histórica y
respaldo) sobre el remoto de Mirova-v1 bajado el 2026-10-16 04:14 UTC (consolidado `756526e1`, OCR `99dd36ad`,
`_dl\procedencia.json`). El aviso A119 sale al inicio de `medir_salida_C.txt`. Lecturas por serie de tiempo:
`C:\Users\nmend\AppData\Local\Temp\claude\verifdist\v2\ocr_vs_serie.csv`, variante C (imagen más reciente de 1 a 25 d).
Regla: una fila cambia de lado sólo si todo el intervalo de la serie queda al otro lado del límite más/menos 0,6 km.

## 1. Lo que cambia (`medir.py`, salida `medir_salida_C.txt`; variante A en `medir_salida_A.txt`)

396 filas OCR del 2026-06-13 al 2026-10-08 (374 ALERTA, 22 FALSO_POSITIVO); el tipo calza con la distancia OCR en
todas las que la tienen. 369 son VIIRS 375 con imagen; las 19 de VIIRS 750 y la de MODIS no tienen ninguna.
**48 filas cambian.** Por pasada, con la lectura A:

| | protegidas (VRP de 1 MW o más) | alertas de cualquier VRP |
|---|---|---|
| cráter pasa a lejana | **19** (9 nocturnas) | 41 (29 nocturnas) |
| lejana pasa a cráter | 1 (nocturna) | 2 |

Protegidas, todas VIIRS 375: **Isluga 7** (4 nocturnas), **Lastarria 6** (todas diurnas, 17 a 18 UTC), **Tupungatito 4**
(nocturnas), **Láscar 2** (1 nocturna) pierden; Láscar 2026-08-21 06:30 gana. De cualquier VRP: Lastarria 14, Isluga 10,
Láscar 8 (y 2 ganan), Tupungatito 6, Planchón Peteroa 2, Chillán 1 (diurna). Ninguna en Puyehue-Cordón Caulle, Villarrica,
Llaima, Copahue ni Chaitén. Ninguna tiene 0,05 MW o menos (la regla SN no las toca). Con la variante A: 18 y 1.
De las 61 protegidas con fila OCR en la ventana, 43 dependen sólo del OCR: 19 lejos, 8 cráter confirmado, 6 sin marcador,
10 sin lectura (9 de VIIRS 750).

## 2. Control: en las pasadas que también están en la tabla, ¿quién acierta el lado?

197 filas OCR tienen la misma pasada en la tabla (±180 s). **El OCR acierta el lado en las 197** (173 de 173 sin las 24 que
son copia exacta de la tabla). **La serie decide 153 y acierta 146 (95,4 %)**: 5 veces dice lejana una pasada de cráter y 2
veces dice cráter una lejana (Láscar 08-21 06:30 y 10-02 06:00, tabla 27,67 y 25,99 km, serie la celda del cráter 1,22).
En distancia la serie sí es mejor: su intervalo contiene la de la tabla en 164 de 177 (92,7 %), el OCR queda a 0,6 km en
147 de 177 (83,1 %). Pero ese sesgo del OCR (PCC, Tupungatito) no cruza el límite.

**Control que falla** (`medir6.py`): cuando la columna trae un marcador a la cifra del OCR y otro lejano, la serie dice
lejana en **5 de 9** pasadas cuya verdad es cráter, y en 27 de 32 de las alertas sólo OCR. El patrón no distingue.
Clasificación de los 20 cambios de protegidas (`medir4.py`, `medir5.py`):
- **10 firmes**, todas diurnas (Lastarria 6, Isluga 3, Láscar 1): no hay marcador a la cifra del OCR; el control diurno
  del verificador dio 0 errores en 244.
- **1 probable**: Tupungatito 09-14 06:18 (2,22 MW), sin marcador a la cifra OCR, pero la marca de 13,11 km la reclama
  también la pasada de las 05:00.
- **8 indecidibles** con el patrón que falla el control: Isluga 4, Tupungatito 3, Láscar 1, todas nocturnas.
- **La ganancia de Láscar 08-21 es un error de la serie**: la tabla trae esa pasada como FALSO_POSITIVO a 27,67 km.
El satélite no ayuda (`medir2.py`): 25 de 31 cambios nocturnos son Suomi NPP, contra 90 de 118 de las sólo OCR que no
cambian; dos protegidas nocturnas (Isluga 06-17 y Láscar 10-01) son NOAA-21.

## 3. Veredictos ya publicados (`medir3.py` → `medir3_salida.txt`, `medir2.py` → `medir2_salida_C.txt`)

- **Meses de S150** (abril a agosto, B contra F): 16 pasadas cambian de etiqueta. Control: sin cambio reproduce 860/134
  y 400/90 (y 904/138 con SN). VIIRS 375: suma B 860 a 859, F 134 a 130 (SN: 903 y 134). Protegidas perdidas: aplicando
  la serie también donde hay tabla, B 1 a 2 y F 3 a 4 (es la ganancia falsa de Láscar, que nadie publica); aplicada sólo
  sin tabla, B 1 y F 3 iguales. **F gana igual.** VIIRS 750: 400/90, sin cambio.
- **Chillán** (09-14 a 10-07): 0 de sus pasadas cambian. **VIIRS 750** (1.10): sin lectura, sin cambio. **Caja** (1.7):
  el veto es una protegida MODIS, sin cambio.
- **F/K V1** (08-29 a 10-08, todavía sin evaluar): 15 pasadas nocturnas cambian y **7 protegidas pierden** (Isluga 3,
  Tupungatito 3, Láscar 1), 6 con el patrón ambiguo. Es el único resultado que esto puede mover.

## 4. Al margen y límites

- 5 alertas OCR de la ventana no tienen distancia (0 = "no medida", fail-open); 2 son protegidas y cuentan hoy sin
  distancia: Chaitén VIIRS 375 2026-09-11 18:12 (1,89 MW) e Isluga VIIRS 750 2026-09-04 18:30 (22 MW), ambas diurnas.
- Sólo VIIRS 375. No releí las PNG: uso las lecturas del verificador. El calado incluye la propia pasada de la tabla en el
  control (circularidad que el verificador midió sin efecto). El control del patrón ambiguo tiene 9 casos.
