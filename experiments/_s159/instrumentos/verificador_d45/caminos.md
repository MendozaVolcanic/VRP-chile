# Caminos por los que cada afirmacion podria estar mal (escrito ANTES de abrir ningun archivo citado)

Verificador de D-45 (quinta adenda, ADENDA_SIGNOS_P2.md, commit c13cf5808) sobre 7eb91eb5e.
Solo vi hasta ahora: git status/log del worktree, listado de carpetas, espacio en disco.
No he abierto evaluar_d25.py, las pruebas, los scripts del implementador ni sus salidas.

## A1. evaluar_d25.py decide P2 como la adenda §2

1. Unidad y signo: el neto se calcula al reves (K menos D) o con errores sumados en vez de restados; o el "error" de D
   cuenta publicaciones en positivos (no errores) por un operador mal puesto.
2. Bloque noche-volcan: el bloque se arma por pasada, por volcan solo o por noche UTC sin volcan; la "noche" se corta a
   medianoche UTC en vez de la noche local que use banco_paridad; sensores mezclados dentro del bloque.
3. B: los bloques con suma 0 se cuentan en B (la adenda dice que no) o se quitan antes de calcular el neto (cambia el neto).
4. Cola: se usa una cola (direccion unica) o dos colas con |suma| en vez de una cola por direccion; o se decide con el 5 %
   sobre el valor-p a dos colas.
5. Comparacion en enteros: se compara con 0.05 en flotantes (riesgo de empate exacto con B chico: 1/32 = 3,125 %,
   2/64 = 3,125 %; con B = 20, 52429/2^20 = 5,0000 %? hay que enumerar). Un flotante puede dar 0.05000000001 y cambiar el veredicto.
6. Exacto con B <= 20: el umbral esta en 20 pero la rama exacta corre hasta 19 o hasta 21 (off by one); o la enumeracion
   de 2^B repartos esta mal (usa signo original y no sorteado, o no toma valor absoluto por bloque).
7. Sorteos con B >= 21: la semilla 162 no se aplica (se usa el RNG global o una semilla distinta), o los sorteos son 10.000
   pero el +1 (p = (k+1)/(n+1)) no esta, o esta en el numerador y no en el denominador.
8. GANA/PIERDE/BLOQUEA/EMPATE: los nombres estan pero la asignacion esta cruzada (GANA cuando el neto es positivo, que la
   adenda dice que es malo para D); EMPATE con neto 0 no tratado; BLOQUEA (protegidas?) se evalua despues de P2 y lo
   sobrescribe o al reves.
9. SIN SUSTRATO con B <= 4: umbral off by one (B < 4) o aplicado sobre el numero de pasadas en vez de bloques.
10. INDECIDIBLE solo con controles caidos: queda un camino en que un sensor sin datos produce INDECIDIBLE en vez de SIN
    SUSTRATO; o los controles caidos no producen INDECIDIBLE (solo lo imprimen).
11. global_ventana sin cambios: alguna constante nueva (umbral de bloques) se cuela en global_ventana; el diff de la
    funcion no es vacio aunque se afirme.
12. El flag o constante se lee de otro lado: las constantes nuevas estan definidas pero la funcion usa un literal distinto
    (ej. 0.05 escrito aparte de la constante); o la constante existe y nadie la lee.
13. El caller transforma el argumento: decidir_p2_bloques recibe los bloques ya filtrados por otra funcion (ej. quita
    bloques de suma 0 antes y luego la funcion no sabe que B ya cambio), o recibe el neto por sensor calculado con otra
    definicion de "publica" que la de evaluar_fk.py.
14. Por sensor: la decision se toma sobre los tres sensores agregados o solo sobre uno, en vez de por sensor.
15. La vara es otra: la adenda sellada tiene sha256 28eea84c...; si el archivo del worktree no da ese sha, estoy midiendo
    contra otra vara. Comprobar primero.

## A2. Detalle informa §3 y §4; D-34 y D-42 ya no deciden

16. D-34 y D-42 siguen participando del veredicto por un camino residual (ej. una rama "INDECIDIBLE si D-42 cae").
17. Se informan pero con el minimo nuevo (SIN SUSTRATO B <= 4) en vez del propio, o no se imprimen cuando el sensor
    tiene SIN SUSTRATO.
18. Falta algun campo de §3/§4 (B, suma, bloques positivos/negativos, valor-p, metodo exacto/sorteos, semilla).
19. Se informa solo en el JSON y no en el impreso, o al reves.

## A3. Rojas: 31 de 31 fallan por AssertionError contra c13cf5808

20. Las pruebas fallan por ImportError/AttributeError (funcion inexistente en c13cf5808), que no es AssertionError; eso no
    es rojo valido segun la definicion de "atrapada".
21. El XML no es de pytest sobre c13cf5808 sino sobre un arbol intermedio (ver sha en la salida).
22. Son 31 segun el implementador; contar las funciones test_ en el archivo de hoy (puede haber 30 o 32; parametrizadas).
23. Alguna prueba pasa en c13cf5808 (no es roja) y se cuenta como roja.

## A4. Candados: 58 de 58 atrapadas; q01 equivalente

24. "Atrapada" leida del returncode y no del XML (un error de importacion tambien da returncode distinto de 0).
25. La copia sin mutar no da 0 fallas (la prueba de frescura del CSV falla siempre): entonces todas las mutaciones se
    "atrapan" por esa falla ajena. Comprobar que el corredor acota la suite a las pruebas de D25 o que descuenta esa falla.
26. s12a2 re-corrida tras agregar una asercion: la asercion agregada en ac6eab47b vigila exactamente esa mutacion o solo
    la hace fallar por otra excepcion; y las otras 57 no se re-corrieron con la suite nueva (la asercion nueva podria romper
    otra equivalencia).
27. q01 "menos del 5 %" declarada equivalente: con comparacion en enteros, cambiar <= por < es equivalente solo si ningun
    valor exacto k/2^B cae en 5 % exacto; 2^B no es divisible por 20, asi que k/2^B = 1/20 nunca es exacto. Pero con sorteos
    (k+1)/10001 tampoco es exacto 1/20 (10001 no divisible por 20). Equivalencia plausible; comprobar la aritmetica entera.
28. Las 58 mutaciones no cubren alguna rama: el +1 de los sorteos, la semilla, el umbral B <= 4, B <= 20, el signo del neto,
    la exclusion de bloques de suma 0. Listar los operadores y buscar huecos; probar una mutacion propia.
29. mutaciones_parcial.jsonl y mutaciones_salida.json no cuadran entre si (58 en uno, menos en otro).

## A5. Cuatro pruebas de calib_p2 re-apuntadas sin perder lo que vigilaban

30. Al apuntar a resultado_d42 la prueba ya no comprueba el veredicto final; si D-42 volviera a decidir, la prueba no lo
    veria (perdida de vigilancia real).
31. Las pruebas re-apuntadas pasan trivialmente (comparan el campo contra si mismo o contra un valor que siempre existe).

## A6. Placebos: 404 corridas; (a) GANA todas; (b) PIERDE todas; (c) 8/320 GANA, 4/320 PIERDE

32. Placebo (a) y (b): el signo se impone despues de calcular el neto (en el resultado) y no en los errores de entrada; asi
    la prueba no pasa por el camino del evaluador.
33. (c): "sortea el signo por noche" pero el tamano de cada noche se fija del dato real; si se sortea por pasada o por bloque
    distinto al del evaluador, la tasa de falsos no mide la regla.
34. 320 = celdas con sustrato × semillas: comprobar el denominador (cuantas celdas, cuantas semillas, cuantas sin sustrato).
    404 = 42 + 42 + 320? Ver que suma.
35. "GANA 8 de 320 y PIERDE 4 de 320": por D-46 el 5 % se lee sobre todo (c) por cola: 8/320 = 2,5 % y 4/320 = 1,25 %,
    ambas bajo 5 %. Pero si la unidad correcta fuera por celda (40 por celda), 3 de 40 = 7,5 % en V2 V375 GANA excede 5 %.
    D-46 dice que eso se informa y no decide. Comprobar que el resumen lo informa.
36. "Semillas no se ampliaron despues de mirar": comprobar fecha/mtime y contenido de los jsonl vs el script (semillas en
    el codigo); si el script tiene un rango de semillas escrito a mano, no puedo probar que no se amplio salvo por git log.
37. Los placebos corrieron sobre brazos de produccion: comprobar que las rutas de datos no apuntan a s146-ab ni a los
    artefactos del run 39756261926.
38. Con la decision nula (signos al azar) la tasa esperada de GANA+PIERDE en una cola por direccion al 5 % es hasta 10 %
    total; 12/320 = 3,75 %, consistente. Pero los bloques por noche con pocas noches (B entre 5 y 20) tienen tasa exacta
    bajo 5 % por discretitud; verificar que no haya celdas con B <= 4 contadas en 320.

## A7. Mediciones sinteticas: tasa exacta de falsos <= 5 % para B 5..20 (max 4,81 % con B = 18); 7 mismo lado deciden, 6 contra 1 no

39. La tasa exacta se calcula sobre bloques de igual magnitud (todos 1) y no con magnitudes desiguales; con magnitudes
    desiguales la distribucion es otra, pero la cota del 5 % sigue por construccion si la comparacion es correcta.
    Reproducir con mi propia enumeracion de 2^B.
40. "7 del mismo lado deciden": con B = 7 todos del mismo signo, p una cola = 1/128 = 0,78 %; decide. "6 contra 1 no": con
    B = 7, 6 a favor y 1 en contra de magnitud igual: suma = 5; P(suma >= 5) = (1 + 7)/128 = 6,25 % > 5 %: no decide.
    Pero con magnitudes desiguales 6 contra 1 puede decidir (si el contrario es chico). Ver que dice la adenda y que midio el script.
41. B = 5: todos del mismo lado da 1/32 = 3,125 % que decide; con B = 4 1/16 = 6,25 % no decide: coherente con SIN SUSTRATO B <= 4.
    Verificar que el script no cuenta B = 4 como "decide".

## A8. Verdes: probar 31 de 31; suite 2.447 pasan y 1 falla (frescura CSV)

42. "Arbol quieto": comprobar los sha_* antes y despues, y que coinciden con 7eb91eb5e o con el arbol de ese momento
    (A112). Si la suite corrio sobre un arbol anterior al ultimo commit, no es verde de 7eb91eb5e.
43. La falla de frescura del CSV: comprobar que de verdad es del entorno (fecha del CSV en la rama vs hoy) y no de D-45.
44. probar_evaluar_d25.py 31 de 31: coincidencia numerica con las 31 rojas; comprobar que son conjuntos distintos (probar
    puede ser otro script con 31 casos) y que no se confundieron.
45. La suite en el worktree de C: con TMP en C: (A154 OneDrive): g1d/g2c dependen de disco; ver si hay fallos enmascarados.

## A9. Cinco lecturas donde la adenda no fija

46. (1) D-34 y D-42 con su propio minimo: si la adenda dice que "se informan", el minimo propio es lectura razonable; pero
    si la adenda dice que no se informan cuando no hay sustrato, es divergencia.
47. (2) Campos de la prueba de signos siempre calculados: con B = 0 puede dividir por cero o dar p = 1; ver que no reviente.
48. (3) p minimo 1/10.001: eso es (0+1)/(10000+1); coherente con el +1. Pero la adenda puede decir (k+1)/(n+1) o k/n con piso.
49. (4) Dos colas con |suma| >= |neto|: la adenda pide una cola por direccion; si ademas se informa a dos colas, bien; si
    se decide a dos colas, mal.
50. (5) En (c) manda el signo comun de la noche y el tamano se fija antes de la moneda: adenda §6; si la adenda dice
    "por noche" entonces el signo comun es correcto; si dice "por bloque" y el bloque es noche-volcan, hay que ver si la
    noche aqui incluye volcan.

## Transversales

51. La copia local esta atrasada: comprobar que el worktree esta en 7eb91eb5e y limpio (hecho: si) y que las salidas del
    implementador llevan sha de ese commit o de un commit entre c13cf5808 y 7eb91eb5e.
52. Numeros transcritos a mano en el material (58, 404, 320, 8, 4, 3 de 40, 4,81 %, 2.447): cada uno se reproduce desde la
    salida cruda, no desde el README.
53. La ventana temporal de los placebos (que fechas de produccion) no esta en el material: medirla.

---
sha256 del cuerpo anterior (sin esta cola): 755f5a5aeadab9da7b54c574b285696395a75e1230dd37626824c983dbe8ec9b
Hora del servidor (gh api -i repos/MendozaVolcanic/VRP-chile, header Date): Fri, 23 Oct 2026 18:29:26 GMT
