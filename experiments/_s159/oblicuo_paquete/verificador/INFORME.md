# S159, verificador del frente «el paquete de MIROVA y el déficit oblicuo»

2026-10-21. Contexto limpio, sólo lectura de los artefactos del frente N ya en disco
(`D:\vrp-trabajo\temporales\s159_n\run_39682867040`) y de las tablas de N
(`C:\vrp-trabajo\s159-pruebas\experiments\_s159\n\objetivos_n.json`, `...\n\tabla_por_pasada.csv`). No se bajó nada,
no hubo git ni despachos. Scripts y salidas en esta carpeta:

- `C:\vrp-trabajo\s159-pruebas\experiments\_s159\oblicuo_paquete\verificador\v1_romper.py` → `v1_romper_salida.txt`
- `C:\vrp-trabajo\s159-pruebas\experiments\_s159\oblicuo_paquete\verificador\v2_controles.py` → `v2_controles_salida.txt`
- `C:\vrp-trabajo\s159-pruebas\experiments\_s159\oblicuo_paquete\verificador\v3_atribucion.py` → `v3_atribucion_salida.txt`

**Denominador y ventana de todos los números**: las 181 alertas de MIROVA que deciden (lab `pos`, `decide`), VIIRS 750
nocturno, 2026-04-01 a 2026-10-21 sin el 18 y 19 de octubre, estado ok; sobre 50° de cenit hay 16 (Chillán 12, Isluga
2, Láscar 1, Cordón Caulle 1).

**Las dos preguntas del instrumento.** (1) Si la coincidencia del oráculo fuera «en cualquier caso», el barajado
(oráculo de una pasada contra el MIROVA de otra) daría también cerca de 1 y estrecho: no da (abajo). (2) Instrumento
muerto: cada celda declara su n; K del artefacto crudo contra la columna `K_pc` de N, 0 discrepancias en 181;
`03_ic_mediana.py` re-corrido da exactamente la salida del informe (diferencia sólo de fin de línea; el archivo
original se restituyó). Control positivo: K tiene que caer con el cenit y cae (0,178 sobre 50°).

## Respuesta a la pregunta clave: ¿el 0,996 es tautológico?

**No es tautológico en el sentido peligroso, pero tampoco es evidencia del fenómeno físico. Mide réplica, no física.**

1. **No hay circularidad de datos.** El oráculo lee sólo radiancias del gránulo (`probe_n.py:85-99`, `oraculo()` recibe
   `m13g, m15g` y llama `ORA.detectar` y `ORA.vrp`); el VRP de MIROVA no entra. Las 16 alertas sobre 50° tienen el
   VRP de la **tabla** (CONS, 12 sólo tabla y 4 tabla más OCR, y en las 4 se eligió el valor de la tabla: 3,43 contra
   3,0 del OCR, `v2` (a)). El OCR redondea a entero, así que una coincidencia al 1 % no puede venir del OCR.
2. **La coincidencia es de cada pasada, no del volcán.** Oráculo pareado sobre 50°: 0,996 [0,986, 1,012], 12 de 15
   entre 0,9 y 1,1. Barajado dentro del mismo volcán: 0,883 [0,171, 4,134], 244 de 2.800. Otra pasada de la misma
   noche (A109): 0,995 [0,512, 1,790], 9 de 78, contra 38 de 45 pareado (`v1` §4). K barajado se dispersa igual que K
   pareado, como debe.
3. **El grado de libertad elegido sobre los mismos datos no lo explica.** El interpolador lineal se eligió en N-2
   sobre las 181; pero gana también sólo con ≤50° (lineal 0,999, 102 de 130 en [0,9, 1,1]; vecino 1,227, 18 de 123;
   cúbico 1,214, 21 de 124), así que el tramo sobre 50° queda fuera de muestra respecto de esa elección (`v3` (b)).
   La esquina de la grilla viene de encabezados de TIF (GEO H1), no del VRP.
4. **Por qué igual no prueba el fenómeno.** El oráculo es el código de MIROVA sobre la misma observación que MIROVA
   procesó: coincidir es lo que hace un port correcto. Dice que nuestra brecha contra MIROVA es de código, no que el
   número de MIROVA sea el calor real. El control que separa las dos lecturas no es contra MIROVA sino **dentro de la
   misma noche, entre pasadas de distinto ángulo**: si el paquete «cerrara el oblicuo» en sentido físico, MIROVA y el
   oráculo darían lo mismo a 65° que a 10° esa noche. Ver VO-1.

## Veredictos

### VO-1. MIROVA misma sufre el déficit oblicuo; el paquete cierra la brecha contra MIROVA, no la dilución física (hallazgo propio)

- **SCRIPT:SALIDA**: `v2_controles.py` (c); `v1_romper.py` §5.
- **QUÉ PASA**: en la misma noche y volcán, la pasada más oblicua (diferencia de cenit ≥ 15°) contra la menos oblicua:
  MIROVA **0,503** por noche [0,411, 0,787], **13 de 15 noches bajo 1**; el oráculo 0,517 (n 26 pares); K 0,239.
  Nulo con los MISMOS pares ordenados por hora: MIROVA 1,054, 7 de 15 bajo 1. Sobre 50° contra ≤30°: MIROVA 0,387 por
  noche, 5 de 5 bajo 1 (8 de 9 pares son Chillán). Ejemplo: Chillán 2026-10-16, 05:42 a 2,0° MIROVA 15,63; 06:42 a
  60,6° MIROVA 14,02 y 05:00 a 58,0° MIROVA 8,36. 2026-10-05: 05:48 a 12,4° MIROVA 7,86; 05:06 a 53,6° 3,43; 06:48 a
  64,3° 2,66.
- **Consecuencia para las afirmaciones**: «el paquete entero cierra el oblicuo» vale contra MIROVA, que es la vara de
  `mirova_equivalent`; no vale como corrección física. La frase de OB-2 «MIROVA da magnitudes parecidas en las dos»
  compara dos pasadas oblicuas (53,6° y 64,3°); la pasada casi a nadir de esa noche dio el doble. Y «un operador puede
  ver una baja que no existe»: MIROVA también la muestra, a la mitad; K la muestra del doble (K/MIROVA de la oblicua
  sobre K/MIROVA de la menos oblicua: 0,373, n 23).
- **CÓMO SE VE EN EL DASHBOARD**: la línea de MIROVA de Chillán también baja en las pasadas oblicuas; la nuestra baja más.
- **CONFIANZA**: CONFIRMADO como medición (n 15 noches, 11 de Chillán en erupción, con variabilidad intranoche real
  grande: nulo [0,787, 2,229]). Que la causa sea la dilución del píxel y no otra cosa: SOSPECHA.
- **GRAVEDAD**: 3. No cambia la decisión de réplica; sí cambia lo que se puede prometer en el experimental
  (BEYOND §12): ahí el oblicuo sigue abierto aun con el paquete.

### Afirmación 1 (razón por tramo, cierre del oblicuo): PARCIAL

- Números CONFIRMADOS al milésimo (K 0,178 n 12, F 0,539 n 14, O 0,996 n 15; ≤25° O 1,000, IC 0,994 a 1,004, n 71).
- Los tres brazos tienen denominadores distintos (selección). En el mismo subconjunto sobre 50° (n 12): K 0,178, F
  0,491, O 0,994; sin condicionar (no publica = 0, n 16): K 0,153, F 0,491, O 0,994 (`v1` §2). La conclusión aguanta.
- Dominio: sobre 50° es Chillán (12 de 16); fuera de Chillán n 3, SIN PODER, y una de esas 3 (Isluga 2026-06-22 05:12)
  da O 0,08. Esa no es falla del port: su banda de triangulación de `fillmissing2` va de 0,018 a 0,223 contra MIROVA
  0,22 (ver Afirmación 1 bis).
- La parte «cierra el oblicuo» es PARCIAL por VO-1.

### Afirmación 1 bis (O1, VRP ambiguo por la triangulación): no altera la tabla, pero sí casos sueltos

- 22 alertas tienen banda máx/mín > 1,82, todas de **1 píxel y ≤ 0,47 MW** (Isluga 13); sobre 50° sólo dos (Chillán
  0,09 MW e Isluga 0,22). En Chillán sobre 50° la banda mediana es 1,043 (`v1` §3, `v2` (b)). MIROVA cae dentro de la
  banda del oráculo (±0,005) en 96 de 145. CONFIRMADO. Gravedad 2: cualquier razón de una alerta débil de 1 píxel
  tiene un error de hasta 12 veces que la mediana esconde.

### Afirmación 2 (atribución y firma de conteo): PARCIAL

- F/K: plano hasta 50° (1,44 a 1,59) y 3,28 sobre 50°, con 10 de 12 pares de Chillán; sin Chillán sobre 50° n 2.
  El salto es del tramo de Chillán, no se puede separar de la erupción. CONFIRMADO el número; la tendencia con el
  cenit, SIN PODER fuera de Chillán.
- O/F «crece de forma monótona»: sin Chillán 0,941 / 1,322 / 1,233 / 0,575 (n 64, 19, 21, 3): sube de ≤25 a 25-40 y
  después no; sobre 50° va al revés (SIN PODER) (`v3` (a)). Monótono sólo con Chillán dentro.
- Firma de conteo O_n/F_n: correlación de Spearman con la **magnitud de MIROVA +0,80** y con el **cenit +0,36** (n 134);
  sin Chillán, cenit +0,18 y magnitud +0,82 (`v1` §8). La firma sigue sobre todo al tamaño del foco (un foco grande
  deja más celdas sobre el umbral), y Chillán mezcla foco grande con oblicuo. «1,5 a ~2,75» no es una serie con el
  cenit: es 1,50 / 2,75 / 2,00 / 2,75. Dentro de Chillán el cenit pesa algo (+0,44 contra +0,30, n 27). El VRP por
  celda plano en ~0,6: CONFIRMADO el número; la lectura «reparto del píxel oblicuo», SOSPECHA confundida con magnitud.

### Afirmación 3 (las 36 no detectadas son la caja, no el ángulo): CONFIRMADA, con un matiz

- Las 36 son las 36 alertas de Cordón Caulle (28) y Tupungatito (8) de la población; su cenit (22/7/6/1) es
  exactamente el de esos dos volcanes, así que el ángulo no selecciona. En las 36 el oráculo no tiene **ningún píxel**
  (no es el filtro de `inner`); el recuadro sensible detecta 30, con el píxel pico en la caja de valor 2 (`v1` §6).
- Matiz: 6 (Cordón Caulle 4, Tupungatito 2) no las detecta ni el recuadro sensible; ahí «es la caja» no alcanza.
  SOSPECHA: otra causa.

### Afirmación 4 (ejemplo Chillán 2026-10-10 06:54): CONFIRMADA

- Desde el artefacto crudo: cenit 67,57°, K 2,508, F 3,508, O 14,878 (13 celdas), banda del oráculo [14,878, 15,250],
  MIROVA 15,26 de la tabla (CONS, `dist_km` 2,37). La banda alta coincide con MIROVA al 0,07 %.

## VERIFICADO LIMPIO

- El oráculo no recibe el VRP de MIROVA: `probe_n.py:85-99` (sólo `m13g`, `m15g`, la caja, `dayflag`, `sunglint`).
- K de la tabla de N = record crudo del artefacto: 0 de 181 discrepancias (`v1`).
- VRP de MIROVA sobre 50° = tabla en 16 de 16 (`v1` §1, `v2` (a)); sólo OCR en 5 de 181, ninguna sobre 50°.
- Cenit centro de grilla = record (ya en el informe; reconfirmado en el ejemplo, 67,57 en los dos).
- `03_ic_mediana.py` re-corrido = salida del informe.
- Interpolador lineal elegido fuera de muestra para >50° (`v3` (b)).
