# Control de instrumento del evaluador sobre los artefactos de S135

> Generado por `experiments/_s143_evaluador/control_s135.py` el 2026-09-17T19:50:50+00:00. Artefactos locales de los runs __run34173711390, __run34208191011 (no versionados, fuera del repo), fusionados en un directorio temporal: 18 archivos, 0 conflictos, 0 faltantes. Ventana 2026-06-01 a 2026-08-31, seis volcanes, brazos A, B y D. Ningún número de este documento está escrito a mano: todos salen de `control_s135.json`.

## Por qué este control

Un evaluador escrito antes de ver datos puede estar equivocado sin que nada avise. S135 corrió
el mismo sensor en la misma ventana y dejó dos números publicados contra los cuales medirse:
**260 noches confirmadas** y **12 noches** que el brazo D pierde.

## Las doce noches de S135

El evaluador nuevo las reproduce **una a una** como pérdida del brazo D sin filtro de cota en el
brazo: 12 noches, y el conjunto coincide exactamente con el publicado (sí).

| volcán | fecha | control publica con cota | brazo D publica con cota | brazo D publica |
|---|---|---|---|---|
| Isluga | 2026-07-01 | sí | no | no |
| Isluga | 2026-07-16 | sí | no | no |
| Isluga | 2026-08-19 | sí | no | no |
| Lastarria | 2026-07-02 | sí | no | no |
| Lastarria | 2026-08-28 | sí | no | no |
| PlanchonPeteroa | 2026-06-22 | sí | no | no |
| PlanchonPeteroa | 2026-06-26 | sí | no | no |
| PlanchonPeteroa | 2026-07-24 | sí | no | no |
| PlanchonPeteroa | 2026-08-09 | sí | no | no |
| PlanchonPeteroa | 2026-08-24 | sí | no | no |
| Tupungatito | 2026-07-07 | sí | no | no |
| Tupungatito | 2026-08-01 | sí | no | no |

## Con la cota también en el brazo, el brazo D pierde más

Exigirle al brazo lo mismo que al control (hallazgo 2 del verificador) lleva las pérdidas de D de 12 a **28**, y las de B de 0 a **14**.
Las que aparecen sólo con la cota son noches en que el brazo publica, pero un objeto que está lejos
de lo que MIROVA informó esa noche: con el criterio viejo el brazo se quedaba con la noche por
publicar otra cosa. El caso a caso, con la cota del mejor objeto publicado por cada uno:

| brazo | volcán | fecha | cota del brazo (km) | cota del control (km) | distancia de MIROVA (km) |
|---|---|---|---|---|---|
| _s135_ab_b_nokeeppeak | Isluga | 2026-06-16 | 1.771 | 0.46 | [2.3, 4.14, 4.19] |
| _s135_ab_b_nokeeppeak | Lascar | 2026-06-02 | 0.703 | 0.473 | [1.5, 3.33] |
| _s135_ab_b_nokeeppeak | Lascar | 2026-06-09 | 0.557 | 0.494 | [1.55] |
| _s135_ab_b_nokeeppeak | Lascar | 2026-06-13 | 0.609 | 0.472 | [1.55, 1.62] |
| _s135_ab_b_nokeeppeak | Lastarria | 2026-06-01 | 1.325 | 0.038 | [2.4, 2.76] |
| _s135_ab_b_nokeeppeak | Lastarria | 2026-06-07 | 0.967 | 0.005 | [2.19] |
| _s135_ab_b_nokeeppeak | Lastarria | 2026-06-13 | 1.022 | 0.153 | [2.17, 2.19, 2.4] |
| _s135_ab_b_nokeeppeak | Lastarria | 2026-06-14 | 1.175 | 0.035 | [2.4] |
| _s135_ab_b_nokeeppeak | Lastarria | 2026-06-28 | 0.635 | 0.533 | [2.7] |
| _s135_ab_b_nokeeppeak | Lastarria | 2026-07-25 | 1.608 | 0.45 | [2.7] |
| _s135_ab_b_nokeeppeak | PlanchonPeteroa | 2026-06-15 | 0.766 | 0.18 | [1.35] |
| _s135_ab_b_nokeeppeak | PlanchonPeteroa | 2026-06-23 | 0.708 | 0.375 | [1.22] |
| _s135_ab_b_nokeeppeak | PlanchonPeteroa | 2026-07-24 | 0.761 | 0.159 | [1.35] |
| _s135_ab_b_nokeeppeak | PlanchonPeteroa | 2026-08-24 | 0.819 | 0.227 | [1.22] |
| _s135_ab_d_ambos | Isluga | 2026-06-16 | 1.771 | 0.46 | [2.3, 4.14, 4.19] |
| _s135_ab_d_ambos | Lascar | 2026-06-02 | 0.703 | 0.473 | [1.5, 3.33] |
| _s135_ab_d_ambos | Lascar | 2026-06-09 | 0.557 | 0.494 | [1.55] |
| _s135_ab_d_ambos | Lascar | 2026-06-13 | 0.609 | 0.472 | [1.55, 1.62] |
| _s135_ab_d_ambos | Lascar | 2026-06-25 | 0.594 | 0.474 | [1.5, 1.62, 1.88] |
| _s135_ab_d_ambos | Lastarria | 2026-06-01 | 1.325 | 0.038 | [2.4, 2.76] |
| _s135_ab_d_ambos | Lastarria | 2026-06-07 | 0.986 | 0.005 | [2.19] |
| _s135_ab_d_ambos | Lastarria | 2026-06-13 | 1.022 | 0.153 | [2.17, 2.19, 2.4] |
| _s135_ab_d_ambos | Lastarria | 2026-06-14 | 1.287 | 0.035 | [2.4] |
| _s135_ab_d_ambos | Lastarria | 2026-06-28 | 0.635 | 0.533 | [2.7] |
| _s135_ab_d_ambos | Lastarria | 2026-07-06 | 1.029 | 0.05 | [2.19] |
| _s135_ab_d_ambos | Lastarria | 2026-07-25 | 1.608 | 0.45 | [2.7] |
| _s135_ab_d_ambos | Lastarria | 2026-08-02 | 1.194 | 0.255 | [2.4] |
| _s135_ab_d_ambos | PlanchonPeteroa | 2026-06-15 | 0.766 | 0.18 | [1.35] |
| _s135_ab_d_ambos | PlanchonPeteroa | 2026-06-23 | 0.708 | 0.375 | [1.22] |
| _s135_ab_d_ambos | Tupungatito | 2026-06-03 | 1.18 | 0.267 | [5.41] |

De esas 30 noches, **7** tienen el objeto del brazo a menos de 0,70 km de la
cota, o sea al borde del presupuesto de 0,55 km: son las más sensibles a la elección del umbral y a
la distancia que informó MIROVA, que viene cuantizada a su celda de grilla (D15).

## El universo: 257 hoy contra las 260 publicadas

El evaluador nuevo cuenta **257** noches confirmadas; S135 publicó **260**. La
diferencia no es del instrumento nuevo, y se atribuye con dos controles cruzados sobre los mismos
artefactos fusionados:

1. el evaluador **viejo** (`evaluar_ab.py`, otra implementación, predicado reconstruido a mano y
   referencia del snapshot) corrido **hoy** da **257**, volcán por volcán igual que
   el nuevo (sí);
2. el mismo evaluador viejo con el **regex del loader OCR anterior al PR #652** (S140, el que corría
   en S135) vuelve a dar **260**.

| volcán | nuevo | viejo hoy | viejo con loader previo a #652 | S135 publicado |
|---|---|---|---|---|
| Isluga | 71 | 71 | 71 | 71 |
| Lascar | 52 | 52 | 52 | 52 |
| Lastarria | 48 | 48 | 48 | 48 |
| PuyehueCordonCaulle | 31 | 31 | 33 | 33 |
| PlanchonPeteroa | 28 | 28 | 28 | 28 |
| Tupungatito | 27 | 27 | 28 | 28 |

El PR #652 le devolvió la distancia a 557 alertas OCR cuyas notas venían en codificación doble. Sin
esa distancia la cota de mismo objeto no se podía calcular y la noche se aceptaba por defecto; con
ella, esas noches muestran que lo publicado está lejos de lo que informó MIROVA. Es el caso de libro
de A90: el número de un informe viejo no es comparable con el de hoy sin reconstruir el corpus y el
código que ese informe pudo ver.

## Los dos predicados

Sobre las 2157 pasadas nocturnas de VIIRS 375 del control, el predicado del
dashboard ejecutado con node y el `publica_en_crater` reconstruido a mano de S135 discrepan en
**1**. El evaluador usa el de node (A97); el viejo se deja
acá sólo como control cruzado.

## Los otros dos criterios, contra los números publicados

En negativos limpios el control publica en 0,938 de 535 pasadas, el régimen que el verificador declaró esperable para el
control reprocesado de S135 (93,8 %, hallazgo 16); el brazo D baja a 0,430.

En magnitud, la mediana del control sobre pares decisivos es 0,730 (n = 425) y la del brazo D 0,720; S135 publicó 0.708 (n = 606) y 0.713 (n = 479).
La diferencia esperada: S135 pareaba a 20 minutos y podía usar varias filas de MIROVA por pasada,
acá el pareo es de 2 minutos (`banco_paridad.TOL_S`) con una sola fila por pasada, CONS antes que OCR,
y las medianas se toman sobre las pasadas que publican los dos brazos, no sobre el conjunto de cada uno.

## Una advertencia sobre un contador que NO es comparable

`coincidencias_de_fecha_descartadas` cuenta distinto en cada evaluador: el viejo anota la noche si
**algún** objeto publicado queda fuera de la cota (aunque otro de la misma noche la pase), y el nuevo
sólo si **ninguno** la pasa. Por eso el viejo muestra números mucho mayores sin que eso signifique
que descarta más noches. La cifra comparable es la de noches confirmadas.

## Qué queda probado y qué no

- CONFIRMADO: el evaluador reproduce las doce noches de S135 y coincide volcán por volcán con la otra
  implementación sobre los mismos datos.
- CONFIRMADO: la diferencia con el 260 publicado es el loader OCR de #652, no el instrumento.
- Lo que este control NO prueba: que los criterios 2 y 3 estén bien calibrados para los brazos de
  S143 (son otros perfiles) ni que la cota acepte sólo objetos verdaderamente iguales, que es una cota
  inferior por construcción (A93).
