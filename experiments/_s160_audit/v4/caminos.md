# Caminos por los que cada afirmación de F4 podría estar mal (escrito antes de abrir los archivos citados)

Verificador V4, S160. Escrito antes de abrir ningún archivo citado por la lista. No se edita después.

## Comunes a todos
- C0 versión: el auditor leyó una rama distinta de la que dice (main d516b9d8c vs loop/activo vs s159-pruebas). Una
  marca puede estar en una rama y no en otra; "sin marca" puede ser cierto en main y falso en loop/activo, o al revés.
- C1 números de línea: las líneas citadas pueden ser de otra versión del archivo; el pasaje puede existir en otra línea.
- C2 marca en otro lugar: la rebaja pudo bajar al hijo con otra redacción (otro símbolo, otra frase, sin el ID), y el
  grep del auditor no la ve (A89, el cero se lee como ausencia).
- C3 corpus vivo (A90): un número que "no se reproduce" puede no reproducirse porque los datos cambiaron (reproceso,
  tabla que pierde filas), no porque nunca se reprodujo. Distinguir: reconstruir el corpus del commit en que se escribió.
- C4 instrumento distinto: el auditor pudo correr un script distinto del citado, con otra ventana, otro filtro (sensor,
  noche, inner) u otra referencia (tabla sola vs combinado, copia viva vs congelada).
- C5 vara: "documento rector" puede no incluir lo que el auditor dice; un texto histórico conservado deliberadamente
  (texto degradado con marca arriba) no es "sin marca".

## 281 (#883 no bajó a docs rectores)
- #883 puede no haber reemplazado el histórico entero (sólo una ventana o sólo algunos volcanes/sensores); entonces la
  frontera de 2026-09-18 puede seguir existiendo en parte de los datos.
- El reemplazo puede no estar en main (puede estar sólo en loop/activo o en una rama).
- DATOS_K_DESDE_UTC en cambio_detector.js puede haberse movido y los docs pueden referirse a otra frontera (la del
  frontend vs la de los datos); un doc que diga "C0 antes de X" puede estar hablando de la historia del detector, no
  de los datos.
- Puede haber marca en algún doc rector que el auditor no vio (otra frase).
- Los records pueden llevar un campo de versión/detector que muestre mezcla aunque el commit diga "entero".

## 282 (tope D9)
- El script contar_topados_d9.py puede contar otra cosa (d9_capped vs ==5.0) o sobre otro directorio; correrlo en otro
  cwd lee otros datos.
- 1.565/343 eran del corpus del 2026-10-14 con C0; hoy con K pueden ser 16/183 por cambio de detector (A90), no
  porque nunca se reprodujeran. Comprobar corriendo el script sobre los datos del commit de la marca S151.
- "0 de 31 en Chillán" puede depender de qué es "pasada" y de la ventana.

## 283 (D-4 439/992)
- La diferencia 439 vs 478 puede venir de la ventana (la marca puede haber usado otra ventana o la referencia de su
  fecha), de la versión del script (clase_mirova.py cambió), o de tabla vs combinado.
- El auditor puede haber corrido con otro filtro (sólo VIIRS 375, sólo noche, D-9 aplicada o no).

## 284 (D-9 14 pasadas)
- Las 7 restantes pueden estar en otro archivo de salida del mismo directorio (otro script persistido) que el auditor no
  abrió; "sin instrumento" puede ser falso.

## 285 (A118 D18 nunca medido)
- La marca puede existir en CLAUDE.md con otra redacción; S151 puede no haber medido D18 sino otra caja/otro brazo
  (KC no es D18), en cuyo caso "nunca se ha medido" seguiría en pie.

## 286 (S158 sólo en loop/activo)
- Merge posterior a main; conteo "67 commits por delante" depende del ref que se compara (origin/loop/activo vs local).
- Las marcas U1..U13 pueden existir con otra etiqueta.

## 287 ("1 SIN EVIDENCIA" de A113)
- S159 pudo tocarlo en otro directorio que experiments/_s159/; la memoria puede tener marca en otro archivo.

## 288 (memoria del agente)
- Los archivos de memoria pueden tener marca en otra línea o el índice MEMORY.md puede rotular la entrada como
  histórica; el número puede ser correcto en su contexto (p. ej. "86 % enero" con Tupungatito, matiz vs refutación).

## 289 (README)
- README puede tener una nota general de K que cubra los pasajes; "detector vivo" puede ser descripción histórica.

## 290 (D27)
- Ventana de la marca vs ventana del auditor; tabla sola vs combinado; la tabla pierde filas (carrera del scraper),
  lo que es corpus vivo, no error de la marca; o la marca usó otra definición de "de tarde".

## 291 (D33)
- El script copia puede diferir del original; los n de la marca pueden corresponder a otro estrato (sólo un volcán o
  sensor) y no al corpus pre-#883.

## 293 (F2-H3..H9)
- Las resoluciones pueden estar fuera de experiments/_s159 (docs/, otra rama, PR #889); las marcas R2 pueden haber
  llegado a main por otro PR.
sha256: 37f404b4b3d0ab99a5daf3fa12654d166a2206fac75f481114d50b3c1f876a0b  hora servidor: Date: Thu, 22 Oct 2026 04:02:52 GMT
