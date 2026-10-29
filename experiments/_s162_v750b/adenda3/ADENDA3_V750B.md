# Adenda 3 de V750-B: la regla N-3 (borrador para el sello, 2026-10-29)

Estado: **BORRADOR, escrito antes de ver datos y antes del despacho del 2026-11-03.** Aprobada en su contenido por
Nicolás el 2026-10-29 («Sí a todo», vía la coordinadora S167, programa
`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §12.5 punto 5). Se marca SELLADA, con el tag
`s167-v750b-adenda3-sellada`, sólo después de un verificador corto con contexto limpio. No toca nada de lo sellado:
el pre-registro, el analizador `analizar_v750b.py` (sha256 LF `83b7159b...`), las adendas 1 y 2, el probe y el
workflow quedan igual.

## 1. Por qué, como geólogo

Una alerta de MIROVA que existe sólo por el OCR sale de leer la imagen por volcán que MIROVA publica, no de su tabla.
En Suomi NPP ese canal llegó a traer la imagen de otra pasada (la cabecera «Last Update» lo delata; Mirova-v1#20), y
antes del 2026-10-09 no hay forma de saber si una alerta protegida leída así es de la pasada que comparamos. Si V750-B
descarta una ROI porque «pierde» una protegida que quizás no estaba ahí, puede quedarse con una ROI peor por un error
de la referencia, no del detector. Nicolás decidió tratar esas alertas igual en todas partes: se informan aparte y no
deciden (S166 para el auto-audit, #924; V375-E §8.13, sellado el 2026-10-28; V750-A §6 ter).

## 2. La regla

Una pasada es **N-3** si es protegida (`protegida`), **no** tiene alerta de la tabla (`alerta_tabla` falso, o sea que
la protegida existe sólo por el OCR), es de Suomi NPP (`sensor == "VIIRS_SNPP_750"`) y su `hora_utc` es anterior al
2026-10-09.

- **No veta.** Una N-3 que un brazo no publica no suma al P1 que veta (§5), así que no lo saca de los elegibles del
  §6.1. Como en la ventana T decide la tabla sola, una pasada sin alerta de la tabla nunca fue etiqueta ahí: la regla
  sólo actúa en la ventana O (desde el 2026-06-13), con el canal que decide y con el canal «todo».
- **Se informa aparte.** El lector lista cada N-3 observada por volcán y hora, con qué brazos la publican y cuáles
  no; cada línea de métricas imprime el P1 que veta al lado del que las cuenta todas («P1 0 (que veta; todas 1, N-3
  aparte 1)»), y debajo de los elegibles imprime los que daría la regla sin la adenda, contando también las N-3. Una
  pérdida de esta clase se ve, pero no decide.
- **No cambia nada más**: la protegida con alerta de la tabla (aunque esa alerta sea menor de 1 MW y la protegida
  venga del OCR), la de otra plataforma o la del 2026-10-09 en adelante siguen vetando. E, P2, la regla §6.2 y §6.3,
  el orden de cercanía al `.m`, los controles del §7 (incluido el control positivo de Cordón Caulle) y la cobertura
  (una protegida SIN DATO sigue frenando la lectura, sea o no N-3) quedan como están sellados. La adenda 2 (posición,
  diagnóstico) tampoco cambia: no decide, y su P1 sigue contando todas.

## 3. Cómo se aplica sin tocar lo sellado

`adenda3/leer_n3_v750b.py` exige el sha256 del analizador sellado, le aplica cinco reemplazos de texto exactos (cada
uno tiene que aparecer una sola vez; si no, se niega con salida 2) y lo ejecuta entero con el `__file__` del
sellado: mismas rutas, mismo oráculo, mismo predicado del tablero con node, misma prueba de signos. Los reemplazos:
(1) el conteo del P1 separa las N-3; (2) la línea de métricas muestra los dos P1; (3) la lista aparte y los elegibles
sin la adenda; (4) la línea del veredicto lleva «[con la adenda 3, regla N-3]»; (5) un encabezado.

**Lectura del 2026-11-03 en adelante**: el mismo procedimiento sellado (adenda 2 §3: separar resultados, leer la
lista sellada), con un solo cambio: **el veredicto de V750-B es el de `leer_n3_v750b.py`**, con los mismos
argumentos con que se correría `analizar_v750b.py`. El analizador sellado se corre igual al lado y su salida se
guarda: es la regla sin N-3, que sólo informa. El despacho, el probe, los objetivos y el workflow no cambian.
Al generar los objetivos (R4), antes de leer cualquier resultado, se cuentan las N-3 de la lista sellada (son
etiquetas de la referencia, no resultados) y se informan con la lista.

## 4. Pruebas

- `adenda3/probar_adenda3.py` (`probar_adenda3_salida.txt`): **9 de 9** como se espera. Escenas sintéticas armadas con
  el constructor de la batería sellada (`bateria_regla_v750b.py`, extraído con ast), corridas por el lector entero:
  N0 la base sin N-3 (B0 y B5 siguen fuera por Cordón Caulle); N1 B2 pierde una N-3 del 2026-09-20 y sigue elegible,
  con su línea en la lista aparte y los dos P1; N2 la misma el 2026-10-09 veta (borde); N3 la misma de NOAA-20 veta;
  N4 la misma con alerta de la tabla de 0,6 MW veta; N5 la N-3 decide la ROI (B0 la pierde en Láscar, donde B4 es la
  caja B0: con la adenda B4, sin ella B2); N6 una sólo del OCR en T no es etiqueta ni se lista; N7 dos N-3 y una de la
  tabla perdidas: veta la de la tabla (P1 1, todas 3, aparte 2); N8 un analizador que no es el sellado se rechaza.
- Rojo antes (`probar_adenda3_rojo_salida.txt`): la misma batería contra el analizador sellado, sin la adenda: 9 de 9
  fallan por aserción; en N1 B2 queda fuera de los elegibles y en N5 el sellado elige B2.
- Nulo (`mutar_adenda3_salida.txt`): **12 de 12 mutaciones de una línea atrapadas por aserción** (hito con «<=»,
  cualquier plataforma, aunque haya alerta de la tabla, hito corrido, sensor de la banda I, la N-3 vuelve a vetar,
  sin el total de P1, la lista sin pedir etiqueta, elegibles informativos con el P1 que veta, acepta cualquier
  analizador, veredicto sin la marca, lista sin imprimir); la identidad PASA y el control que se cae sale CAÍDA.
  Sin atrapar, declaradas por equivalentes: quitar «protegida» de la condición (sólo se consulta sobre etiquetas
  protegidas) y listar con el canal que decide en vez de «todo» (sin alerta de la tabla sólo hay etiqueta en O, donde
  coinciden).
- Comandos (rutas absolutas en la máquina de Nicolás; temporales en D:):
  `python adenda3/probar_adenda3.py --evaluador <evaluar_d25.py del tag s161-d25-lectura> --dest <carpeta>`,
  la misma con `--lector analizar_v750b.py` para el rojo, y `python adenda3/mutar_adenda3.py --evaluador <...> --dest
  <carpeta>`.

## 5. Límites declarados

- La regla usa los campos que la población ya trae (`protegida`, `alerta_tabla`, `sensor`, `hora_utc`); si la lista
  del 2026-11-03 trae `alerta_tabla` mal calculado, la regla hereda ese error. Lo vigila la cuenta de N-3 que se
  informa al generar los objetivos.
- La regla no distingue si la alerta del OCR resultó ser de la misma pasada: es una regla por clase, igual que en el
  auto-audit y en V375-E. Una N-3 que sí era real y que un brazo pierde queda listada por nombre, no escondida.
