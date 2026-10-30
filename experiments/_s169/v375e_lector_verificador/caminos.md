# caminos.md: caminos por los que cada afirmación podría estar mal (escrito antes de abrir cualquier archivo citado)

## B1 (VS168-01: corte que decide y fecha de inicio)
1. `--desde` se compara contra 2026-11-03 pero con otro tipo (str vs date) o se acepta también un valor con hora / zona (2026-11-03T00:00) o una fecha posterior que "parece" igual.
2. La noche de la parada se calcula con un contador que cuenta noches con Suomi NPP, o cuenta noches sin datos, o la cuenta de alertas que deciden se hace sobre otra población que la del texto (§11.8).
3. El lector corta por `--hasta`, pero antes de cortar ya cargó/imprimió datos posteriores (el JSON de salida arrastra campos de noches posteriores).
4. El código de salida 5 se devuelve pero antes ya se imprimió una lectura parcial (stdout, --json, log, archivo temporal) o los contadores revelan composición (p. ej. cuántas alertas por brazo).
5. Una variable de entorno, un argumento oculto (--prueba, --modo, --forzar, --corte), o un parámetro de la función pública `leer(...)` permite fijar otra parada o desactivar el control.
6. Orden de comprobaciones: la lectura se calcula antes de comprobar la parada, y la parada sólo oculta la impresión.
7. "Nunca se sobrescribe": la comprobación de existencia es racy, o usa un nombre distinto por N (lectura_sombra_corte_<N>) pero un corte N' distinto no ve el N previo, de modo que se puede escribir dos cortes distintos (N y N+1) y elegir.
8. El nombre usa N = noches transcurridas, no el índice de la primera noche en que se alcanza la parada; si hay hueco de datos, N puede saltar.
9. Si el control cae (control caído), el lector igual muestra composición de la población.
10. La vara es otra: el texto §11 dice una cosa y el código otra (el texto manda).

## B2 (VS168-02 a 08, desvíos S8 y S0)
1. Cada uno de los 7 hallazgos del verificador anterior tiene texto en §11 pero el código implementa algo distinto, o código sin texto.
2. S8 llevando los CUMPLE de (b), (c), (d) a DECIDE NICOLÁS puede contradecir el §5.4 sellado (tag s168-v375e-cuerpo-sellado) que quizá dice que (b)(c)(d) deciden mecánicamente; cambiar un CUMPLE sellado en DECIDE es modificar una regla sellada.
3. S0 fijando el sha de frontend/index.html: el sha puede ser de un archivo con CRLF/LF distinto (autocrlf), de modo que el control cae en otra máquina; o el sha se compara contra un valor leído de un archivo que el mismo lector escribe.
4. La referencia al sha del predicado del tablero apunta a otra función que la que realmente "publica".

## B3 (coherencia texto y código)
1. Reglas en el código con constantes (umbrales, mínimos de n) que el texto no nombra o nombra con otro valor.
2. Reglas en el texto con números que no están en el código.
3. Códigos de salida del texto distintos de los del código.
4. Casos borde (empate, n=0, división por cero, NaN) que el código decide y el texto no.

## B4 (batería 190/190)
1. Una aserción que "ve en rojo" una regla nueva sólo porque falla por excepción (caída) y no por aserción.
2. La batería usa datos sintéticos con el mismo defecto del código (circular).
3. Las salidas rojo_A..E fueron generadas en otra versión del código que la 983f6f28d.
4. Cuenta 190 incluye aserciones tautológicas.

## B5 (nulo mutar_sombra.py)
1. Mutaciones que no cubren una regla nueva (S1..S8), o cubren el literal pero no el comportamiento.
2. El criterio de atrapada cuenta caída (excepción, SyntaxError, timeout) como atrapada.
3. La mutación equivalente V04 se declara como equivalente DESPUÉS de correr (o sólo en el informe) en vez de antes en el script/texto.
4. Mutaciones que se aplican por reemplazo de texto que ya no calza (0 ocurrencias) y por tanto "no mutan" y salen como no atrapadas, o se cuentan como atrapadas por caída.
5. Mutantes que dejan un archivo del árbol modificado entre corridas (no restauran).

## B6 (perfil sombra_codigo_mirova y cenit del record de K)
1. El perfil no existe con ese nombre en pipeline/profiles/ o su carpeta de salida (data_subdir) difiere de la que el lector lee.
2. El cenit se toma de un campo del record que K no escribe (otro nombre, o sólo en algunos sensores), o se toma de otro lado.
3. El test de tests/test_sombra_codigo_mirova_s167.py no cubre lo que S8 espera.

---
sha256 del contenido anterior a esta nota: 65a93f8161b8cca0ba985805ff6fd68d3a4d9eeca5ae33dd68ea4110b630f562
hora servidor: Fri Oct 30 03:06:32 UTC 2026
