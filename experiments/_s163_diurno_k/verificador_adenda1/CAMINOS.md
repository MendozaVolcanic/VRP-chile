# Caminos por los que la Adenda 1 o su script podrían decidir mal (escritos ANTES de abrir el script)

Lo único del script que había visto al escribir esto: nada. Lo único de la adenda: el texto de PREREGISTRO.md §11.

## A. La regla excluye días que no debía (saca datos reales de un A/B)
- A1. CMR devuelve 0 por una consulta mal armada (short_name o versión equivocados, p. ej. VJ202IMG/VJ102IMG con otra
  versión que la que usa el pipeline; página truncada; caja distinta) y no por falta real de NASA. Si además el control
  no tiene esa plataforma (p. ej. NOAA-21 no se procesa), se excluirían días enteros.
- A2. Un error de red o HTTP de CMR (timeout, 5xx, JSON vacío) se lee como 0 gránulos.
- A3. El día se define distinto en CMR (UTC 00:00 a 24:00), en el script, en los records (campo de fecha/hora) y en el
  evaluador sellado (`excluir_dias`): desfase de un día, zona horaria, pasada que cruza medianoche UTC.
- A4. «Alguna plataforma»: basta que falte UNA plataforma (p. ej. NOAA-21 en M) para sacar el día entero de los dos
  brazos, incluidas plataformas sanas, MODIS y las alertas protegidas de ese día. Puede cambiar el veredicto en
  cualquier dirección; hay que contar cuántas protegidas y negativos salen en W1 y si el script lo informa.
- A5. (b') cuenta records «de P» con el campo `sensor`: mapeo sensor -> producto CMR incompleto o equivocado
  (VIIRS_SNPP = banda I 375 m = VNP02IMG; VIIRS_SNPP_750 = M = VNP02MOD; NOAA20/NOAA21; nombres con sufijos NRT, v2.1, etc.).
  Un valor de `sensor` no mapeado se ignora en silencio y haría cumplir (b') de más.
- A6. (b') se cuenta sobre el control completo o sólo sobre un volcán/job; si una matriz de volcanos tiene un job caído,
  o si hay records sólo cuando hay detección (no por cada gránulo), «sin record» no equivale a «sin dato».
- A7. (b') incluye o excluye records diurnos del control (el control no debería tenerlos) o records de otras fechas.
- A8. NRT: el pipeline cae a `_NRT` (LANCE) cuando el estándar no existe aún; la consulta de (a) sólo mira el estándar.
  Si el estándar da 0 y el NRT tiene datos pero el control igual no tiene records por un fallo propio, se excluye un
  fallo del pipeline como si fuera NASA (oculta un defecto del instrumento).
- A9. La lista depende de la hora de la consulta (CMR cambia: reprocesos, rezago de indexado). Dos corridas dan listas
  distintas; la regla no fija cuándo se consulta ni congela la respuesta.
- A10. Hard-code: una lista de días escrita a mano (decisión caso a caso) en vez de derivada.

## B. La regla deja DENTRO un hueco de NASA
- B1. Hueco parcial dentro del día (gránulos de la mañana sí, los del mediodía no): (a) exige 0 en todo el día, así que
  no lo ve; I4 fallaría y el resultado sería INVÁLIDO (aceptable) o, si I4c tolera 6 y 21 pasadas sin record (V10), pasa.
- B2. Hueco que NASA tiene pero sobre la caja de 11 volcanes se ve y sobre el volcán concreto no (gránulo en la caja sin
  cubrir el volcán): (a) no se cumple, el día queda dentro.
- B3. Plataforma con hueco pero el control sí tiene un record de P ese día (p. ej. de otra hora): (b') no se cumple.
- B4. La cuenta de (a) por producto: sólo cuenta cuando el producto IMG y MOD de la misma plataforma coinciden; si se
  mezclan, un día con IMG pero sin MOD.

## C. La adenda no cumple alguna de las siete condiciones
- C1. (1) fecha: ¿commit 867cb1ec es anterior a cualquier dato de W2? Run 40379112237: createdAt, estado, rama
  s151-ab-diurno/40379112237 en el remoto. ¿W3 a W6?
- C2. (2) criterio mecánico: (a) y (b') tal como las pide la coordinadora; el script implementa exactamente eso.
- C3. (3) «si I4 vuelve a fallar tras excluir, INVÁLIDO»: el evaluador sellado lo hace con la lista; la adenda lo escribe.
- C4. (4) el evaluador sellado no cambia: `git diff 68687d2d4 867cb1ec -- evaluar_diurno_k.py` vacío; además la lista llega
  por un mecanismo que el evaluador ya tiene (`excluir_dias`) y en el formato que lee.
- C5. (5) la adenda dice (b) -> (b') después de ver W1, con el motivo.
- C6. (6) la salida informa las dos versiones.
- C7. (7) regla fija desde el commit para W2 a W6; si el script o el texto dejan una puerta (parámetros, flags, lista a mano).

## D. Cifras y reproducibilidad de la adenda
- D1. Las cifras de W1 (3/37, 4/40, 2 nocturnas, 0/31, 0/33, 4/5 y 4/16, 1/34 y 2/37) contra las salidas y contra una
  re-corrida de W1 desde la rama de datos y la referencia congelada.
- D2. «En W2 a W6 el catálogo CMR tiene gránulos todos los días» contra una consulta nueva y contra las fechas reales de W2 a W6.
- D3. Pruebas (18) pasan; que fallen por la razón correcta; mutaciones 9 de 9 y control de caída.
- D4. «0 de 31 / 0 de 33 con la lista» no oculta, tras excluir, que se hayan ido protegidas.

---
Sellado: sha256 del bloque anterior (archivo hasta la línea previa a este pie) = 4a83599ffeca7baf6a44f6ef1242c6656f5bebe6d25b1e11e02f0083ea67ace2
Hora del servidor (gh api -i, cabecera Date): Mon, 26 Oct 2026 18:50:30 GMT. Commit: 867cb1ec80308338412af1c0c59b28541c271872.
