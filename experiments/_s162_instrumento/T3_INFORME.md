# T3 (fase 0 del programa por sensor): placebo de ganancia, comparador d′ y placebos de D-44 en el evaluador común

Sesión hija «Instrumento» de S162, 2026-10-24. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md`
§8.3. Módulo: `scripts/evaluador_comun.py` (bloque T3). Pruebas: `tests/test_evaluador_comun_t3_s162.py`. Apilado sobre
el PR de T1+T2+T5 (usa su tabla por pasada).

## El fenómeno que obliga a tener estas piezas

Nuestra magnitud queda bajo la de MIROVA (razón 0,5 a 0,65 según sensor). Entonces cualquier brazo que sólo
multiplique la magnitud por un factor parejo, sin saber nada del volcán ni del píxel, se «acerca» a MIROVA en
promedio, y la regla simétrica de M le da MEJORA (R2-8 de AUDIT_S158_R2). El comparador d′ (D-28) pregunta otra
cosa: si el brazo queda más cerca de MIROVA que una ganancia pareja del mismo tamaño, es decir, si sube los pares que
tiene que subir. En P2 (cuántos errores de publicación), las pasadas de una noche comparten volcán y atmósfera; el
nulo es por bloque noche-volcán (D-45), y los placebos de D-44 comprueban que la prueba puede fallar en las dos
direcciones y que no da falsos de más.

Hasta hoy todo esto vivía sólo en `evaluar_d25.py` (rama `s159-evaluador-d25`, tag `s161-d25-lectura`): sólo VIIRS y
sólo el A/B de D25. MODIS no tenía evaluador.

## Qué agrega

- M: `decidir_estrato(P, modo)` con la calibración simétrica (D-27), el mínimo de dos volcanes (H4), el comparador
  d′ (D-28) con la calibración de d′ (D-30 respuesta 2, D-32: 1.000 repeticiones, semilla 160); `placebo_ganancia`
  (K×1,2 y K×0,8, con y sin comparador, informa); `pares_m` arma los pares desde la tabla común con un estrato que
  define el que llama (por sensor, cenit, kernel: el estrato es del pre-registro, no del módulo).
- P2: `clase_p2` (alerta bajo 1 MW; negativo limpio = RUTINA de la tabla en un volcán, sensor y día sin alerta ni
  FALSO_POSITIVO), `contribuciones_p2` (sólo pasadas observadas por los dos lados, T2), `decidir_p2` con la prueba de
  signos por bloque (D-45: exacta con 20 bloques o menos, si no 10.000 sorteos con semilla 162; SIN SUSTRATO con 4).
- Placebos de D-44 a nivel de tabla (`placebo_p2`): (a) apagar negativos limpios publicados, debe GANAR; (b) apagar
  alertas bajo 1 MW publicadas, debe PERDER; (c) simétrico por bloque noche-volcán (corrige V42-21, el de S160
  sorteaba por pasada): en cada bloque con pasadas de los dos lados se voltean m = mín(n₊, n₋) del lado que sale por
  moneda justa, así el aporte del bloque es ±m con probabilidad 1/2 exacta.
- Constantes y semillas: las selladas en D25. Un A/B nuevo que quiera otras las declara en su pre-registro.

## Equivalencia con el evaluador sellado (`t3_equivalencia.py`)

`evaluar_d25.py` del tag `s161-d25-lectura` (blob `1dbabf657`, idéntico al del worktree `C:\vrp-trabajo\s159-evaluador`,
importado sólo para leer con `python -B`): **250 casos, 0 diferencias** (`t3_equivalencia_salida.txt`), campo por
campo en `decidir_estrato` (decide, bloquea, informa; efectos nulos, a favor, en contra, placebo ×1,2 y ×0,8, sin
sustrato) y en la prueba de signos (exacta y por sorteos). **Control negativo** (`--control-negativo`: semilla de d′ y
mínimo de volcanes perturbados en el port): **17 diferencias** (`t3_equivalencia_control_negativo_salida.txt`), así que
el cero de arriba no es ceguera del instrumento.

## Pruebas, placebos y mutaciones

- 21 pruebas. Lo central: el placebo ×1,2 da MEJORA **sin** comparador y no **con** comparador, y su d′ es 0 exacto;
  un brazo que corrige cada par hacia MIROVA da MEJORA con comparador; una MEJORA de un solo volcán queda NEUTRO; el
  placebo (a) GANA, el (b) PIERDE y el (c) da pocos falsos y voltea lo mismo de cada lado en un bloque asimétrico.
- Placebo (c), primera versión: volteaba el bloque entero del lado que salía; como los bloques del lado +1 traían más
  pasadas que los del −1, el neto salía sesgado (11 PIERDE de 40 en la tabla sintética). Rehecho con m = mín(n₊, n₋):
  7 GANA y 8 PIERDE de 200 (3,5 % y 4 % por cola, bajo el 5 %).
- Mutaciones (`mutaciones_t3.json` → `mutaciones_t3_salida.txt`): primera corrida 16 de 21; F1 caía por construcción
  (la prueba leía una clave que no existe sin comparador), F4 era casi equivalente (con signos al azar `s·d` y `s·|d|`
  tienen la misma distribución; sólo cambia el poder) y F5, F11 y F16 pedían casos nuevos. Con cuatro pruebas más y
  una aserción sobre el poder: **21 de 21 atrapadas por aserción**, con control de caída.

## Límites

- `placebo_p2` voltea `pub` en la tabla; no pasa por el predicado del tablero (S160 lo hacía sobre records y corría el
  evaluador entero). Para P2 da lo mismo, porque P2 sólo mira `pub`; para M no se usa.
- No se corrió sobre producción real (los placebos de D-44 sobre V1 y V2 de S160 siguen siendo la referencia). Eso
  queda para el primer A/B que use este evaluador, como corrida de instrumento antes de leer brazos.
- No reemplaza al evaluador sellado de D25: es para A/B nuevos.
