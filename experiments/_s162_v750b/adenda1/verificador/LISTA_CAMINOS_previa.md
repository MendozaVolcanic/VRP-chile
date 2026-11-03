# Lista de caminos previa (escrita antes de abrir la carpeta adenda1)

Hora del servidor (gh api -i): Mon, 26 Oct 2026 01:54:02 GMT
Commit medido: e7c56af0b2d5019e350e14bd23b98c940b33a1bf

Afirmación: el analizador sellado deja caer en silencio una pasada ok/nocturna/cráter cubierto con una caja del oráculo faltante; la adenda 1 (compañero) lo resuelve sin cambiar reglas.

Caminos por los que podría estar mal:

1. El hueco no existe tal cual: l. 205-209 del analizador no deja caer lo que se dice (p. ej. otra condición lo cuenta antes).
2. El compañero no reproduce exactamente la cuenta del analizador en algún estado (nocturno vs diurno, cráter cubierto vs no, estado distinto de "ok", cajas vacías, orden, empates, redondeo del 2 %, el freno por protegida).
3. El caso SÍ ocurre con el probe sellado (probe_v750b.py escribe cajas incompletas en alguna condición), o el probe tiene otra forma de no escribir una caja.
4. Hay otra forma de que una pasada desaparezca del denominador que la adenda no cubre (estado distinto de ok, diurna, cráter no cubierto, sin oráculo, volcán sin caja, pasada duplicada, clave distinta).
5. El compañero cuenta mal SIN DATO: doble conteo, cuenta pasadas que el analizador ya cuenta, o pasadas no protegidas con el freno equivocado.
6. La prueba pasa por la razón equivocada: rojo sin compañero por una excepción (ImportError, ruta) y no por aserción; verde con compañero por un escenario que no ejercita el hueco; fixtures que no se parecen a la salida real del probe.
7. La prueba usa una copia del analizador distinta de la sellada (hash) o el evaluador d25 de otra versión.
8. El medidor de mutaciones: mutaciones atrapadas por caída/excepción y no por aserción; falta de control de caída; mutaciones que no son realmente distintas (equivalentes); "7 de 7" cuenta mal; mutaciones con identidad no verificada.
9. La adenda cambia en realidad una regla (umbral del 2 %, definición de cobertura, SUFICIENTE, freno por protegida) o el texto de adenda en el pre-registro dice algo distinto de lo que hace el código.
10. El pre-registro sellado fue modificado de forma que invalide el sello (sha, marca inicial) o el analizador sellado fue tocado.
11. El comando de lectura descrito en la adenda no corre (rutas, argumentos, orden de corrida, dependencia de evaluar_d25.py, encoding en Windows).
12. El compañero lee otras entradas que el analizador (otro archivo, otro filtro de ventana temporal, otra definición de protegida >=1 MW), de modo que las dos cuentas divergen en datos reales.
13. Efectos laterales: el compañero escribe en carpetas que no debe, o depende del estado de git/hora.
14. La salida *_salida.txt commiteada no corresponde a lo que produce el script hoy.
