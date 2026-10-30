# V375-E: lectura retrospectiva y de las pasadas lejanas con el lector sellado (S168)

**Ningún hallazgo de gravedad 3** (ni en el verificador de la adenda 3 ni en el de la lectura).

- Sello: tag `s168-v375e-cuerpo-sellado` sobre el commit `444d5d888` (rama `claude/adoring-wright-dc0404`, avance
  rápido desde `e6675da85`). Verificador del sello: `experiments/_s168/v375e_adenda3_verificador/INFORME.md`.
- Lectura: commit `7a548be11` (salida cruda), en la rama `claude/s168-v375e-sello`. Lector
  `experiments/_s162_v375/e_adenda2/leer_posicion_v375e.py` sin cambios desde el tag; corrida 2026-10-29 19:57 a 20:56
  UTC, exit 0, sobre el run FAR 40773794395 y los lotes S159, S162 y S162b (§8.9). Salida:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\cranky-payne-f7d913\experiments\_s168\v375e_lectura_lejana\lectura_salida.txt`
  y `lectura.json`.
- Verificador de la lectura (Sonnet 5.5, contexto limpio):
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\cranky-payne-f7d913\experiments\_s168\v375e_lectura_lejana\verificador\INFORME.md`.
  Veredicto: **LECTURA CONFIRMADA CON RESERVAS**. Re-corrió el lector y la salida es idéntica (salida, stdout y json,
  sin contar el fin de línea). Hallazgos: cinco de gravedad 2 (VL168-01 a 05) y tres de gravedad 1.

Todas las cifras de este informe salen de `lectura_salida.txt`, salvo que se diga otra cosa.

## Qué se ve, como geólogo

La pregunta de la regla de posición es qué hacer cuando, en la misma escena, hay un píxel débil junto al cráter y una
fuente más radiante lejos (otro foco, un borde de nube, un salar tibio). **Radiante** ubica el record en la fuente lejana
y el tablero calla. **Cercano** lo ubica en el cráter y el tablero publica.

La lectura muestra el costo y el beneficio de cada uno:

- **Lo que gana cercano**: dos alertas protegidas de NOAA-21, ambas sólo del OCR (Isluga 2026-06-17 05:06 y Láscar
  2026-10-01 05:18), que K publica y que radiante y pico callan. Son las que deciden el veto. Además publica otras dos
  protegidas de Suomi NPP (que por §8.13 no vetan) y cuatro alertas bajo 1 MW: 8 cambios de publicación contra radiante,
  todos a favor de publicar.
- **Lo que paga cercano**: en las 329 pasadas en que MIROVA publicó la fuente como lejana, cercano publica en la cumbre
  en 104, contra 13 de radiante y pico (K publica en 121). En esas escenas cercano se comporta casi como producción, que
  es justo la sobre-publicación que la réplica busca cerrar.

O sea que el veto sellado (ninguna protegida que K publica se puede perder, si otro brazo la publica) eligió cercano por
dos pasadas sueltas, y ese brazo devuelve la mayor parte de las publicaciones en lejanas que radiante evita.

## Veredicto por estrato (texto sellado)

| lectura | resultado |
|---|---|
| controles C1 a C9, equivalencia, cobertura A108 | todos en verde; EQUIVALENTE (máscara 0 distintas, publicación 0 distintas en los tres brazos, VRP 667 de 667); C7 20 de 20; C8 2362 de 2362; 46 negativos limpios SIN DATO, por nombre |
| regla de posición, unión | **ELEGIDO CERCANO** (único que pasa el veto) |
| regla de posición por tramo | T: SE QUEDA RADIANTE; O1: ELEGIDO CERCANO; O2: ELEGIDO CERCANO. La marca A104 mira sólo O1 y O2, que coinciden con la unión: no salta |
| regla de posición con el veto sólo sobre la tabla (informa) | SE QUEDA RADIANTE |
| (a) veto del §5.4 con §8.13 | cercano CUMPLE (0 que vetan); radiante y pico NO CUMPLE (2 cada uno) |
| (b) P2 contra K, silencio, P2-L | CUMPLE en los tres brazos (P2 GANA, SILENCIO ACOTADO BAJO K, P2-L GANA) |
| (c) magnitud M, modo decide, unión | MEJORA en los tres brazos, con d′ MEJORA; MEJORA también en T, O1 y O2, sin marca A104 |
| curva de cenit (informa) | SIN SUSTRATO en K y en los tres brazos (5 noches de nulo, bajo el mínimo de 8), como anunciaba §9.6 |
| P-sinfiltro (informa) | P1 0 perdidas de 80; silencio ACOTADO BAJO K; P2 GANA |
| **paquete §5.4** | **CUMPLE (falta la sombra), con el brazo cercano** |

## Reservas del verificador que hay que decir al reportar (gravedad 2)

- **VL168-01**: la elección de cercano cuelga de esas dos protegidas de NOAA-21 sólo del OCR. Con el veto contado sólo
  sobre la tabla, el resultado es radiante. El texto sellado no dice cómo pesar las lecturas informativas cuando
  contradicen al veto. El verificador hizo una cuenta a mano del error ponderado de posición, que da a radiante como
  mejor; no la reproduce ningún script commiteado, así que aquí no va como número.
- **VL168-02**: T da radiante y la marca A104 no mira T. Sale así del texto («O1 u O2»), pero el texto no dice por qué
  excluye T. La explicación que da el verificador (en T no hay protegidas sólo del OCR que veten, porque antes del
  2026-06-13 el OCR no entra al marco, A119) es suya, no del pre-registro.
- **VL168-03**: la vara 3 (distancia contra la de MIROVA, que según el texto sirve para descartar un brazo) desfavorece a
  cercano en las lejanas (mediana de la diferencia de radios 0,532 km, contra 0,284 de radiante), y no hay regla para
  usarla.
- **VL168-04**: el criterio (b) exige no ser peor que K en las lejanas, no exige no publicar ahí. Cercano cumple con 104
  de 329.
- **VL168-05**: «CUMPLE» no significa «sin protegidas perdidas». Cercano pierde 6 de 80 (3 que K publica, que §8.13 saca
  del veto, y 3 que K tampoco publica), y su cumplimiento de (a) depende de N-3.

## Qué decide Nicolás

1. **Si el paquete sigue a la sombra con cercano, como dice la regla sellada.** Mi recomendación es sí: es la regla
   escrita antes de ver, y elegir otro brazo ahora sería decidir después de ver. Lo que conviene es decir en voz alta el
   costo en las lejanas (104 contra 13) y dejar que la sombra lo mida en la ventana P. La sombra está encendida desde #926
   y sus primeros datos son del 2026-11-03. Si Nicolás prefiere radiante, o leer los dos en la sombra, es una decisión
   suya y queda rotulada como posterior a la lectura.
2. **El lector de la sombra** (§9.8) tiene que escribirse y probarse con mutaciones antes del primer corte de la ventana
   P, y pasar por Nicolás antes de leer. Lleva lo que dejó abierto el verificador de la adenda 3: el arreglo de VA168-01
   (C3 caído corta la impresión), la consecuencia en (d) del sesgo de plataforma y de las dos ganancias (VA168-02), el
   redondeo del cercano (VA168-08), y, si Nicolás quiere, cómo pesar las lejanas (VL168-01, 03 y 04). Todo eso hay que
   escribirlo antes de abrir datos de la ventana P.
3. **No cambiar la vía en `pipeline/` todavía.** Pasar la vía de radiante a cercano es un PR aparte con A45, y toca
   también a VIIRS 750 y MODIS, que comparten `procesar_grilla` (§8.10). Recomiendo esperar a la sombra.

## Lo que no está comprobado

- d y d′ de M, los IC de la curva y las pruebas de signos por par sólo están como los imprime el lector: el json no
  guarda los datos por pasada, así que el verificador no pudo recalcularlos de forma independiente (sí los reprodujo al
  re-correr).
- El nulo completo de 114 mutaciones con la batería de 165 sigue sin re-correr (§9.11, dicho antes del sello).
- El log de Actions del run FAR no se revisó aquí. La cobertura sí se midió en la lectura: 330 de 330 lejanas y 20 de 20
  de control de vida con dato.
