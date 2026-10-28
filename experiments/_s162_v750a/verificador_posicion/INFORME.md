# Verificador limpio de los brazos de posición de V750-A (P-cercano, P-pico, E_lejana, P2', regla del §6 bis)

- **Hora del servidor** (header Date de `gh api -i repos/MendozaVolcanic/VRP-chile`): Wed, 28 Oct 2026 02:05:37 GMT. Cierre del
  informe: Wed, 28 Oct 2026 02:41 UTC (`date -u` del equipo, tras la batería completa).
- **Commit medido**: `8b9156476` (HEAD de la rama hoy es `d4bcc7f78`, que sólo agrega una línea a `tasks/LOOP_VIIRS750.md`; los
  cinco archivos del objeto están idénticos a `8b9156476`, comprobado con `git diff --quiet 8b9156476 -- <archivos>`).
  Objeto: `git diff 699e2d04f 8b9156476 -- experiments/_s162_v750a/` (evaluar_v750a.py, probar_evaluar_v750a.py,
  mutar_evaluar_v750a.py, LECTURAS_EVALUAR_V750A.md L20 a L27, PREREGISTRO_V750A.md §11).
- **Vara**: PREREGISTRO_V750A.md §3 y §6 bis, escritos en `699e2d04f` antes de la implementación. `git diff` confirma que el
  agregado NO tocó ni el §3 ni el §6 bis (sólo el §11), así que la vara está intacta. Referencia de método: `experiments/_s162_v750b/adenda2/leer_posicion_v750b.py`.
- **Evaluador del tag**: `evaluar_d25.py`, sha256 `2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747` (coincide con el
  pedido).
- **Lista previa de caminos** (escrita antes de abrir el código nuevo, hora 02:05:37 GMT):
  `LISTA_CAMINOS_previa.md`, sha256 `e3ca5f6e53cb1e0502cea7ced5ea184024bf43c6a965866e8dbaa7b7c30020ef` (el de antes de abrir el código; después se
  reemplazaron tres guiones largos por dos puntos y un paréntesis, regla de Nicolás, sin cambiar el contenido: sha256 actual `7e35fa7f2da68b2e42292b67e0bbb6c173ead234b5b891e3c0c29f4c7422224a`).
- **Modelo**: Claude Sonnet 5.5, contexto limpio (no vio el informe de ningún verificador anterior de este agregado).
- **Qué NO miré**: la corrida completa del medidor `mutar_evaluar_v750a.py` (8 a 14 h, prohibida por el encargo); datos reales
  (ningún `resultados_*.json` ni `objetivos_run` real: todo es sintético); el probe/runner que produce los artefactos de las
  far_ref para V750-A; el JavaScript del predicado del tablero (se ejecuta con node pero no lo audité); el código sin cambios
  del analizador (S-1, equivalencia §6.1, comparador de M, `cargar_m`); el generador de la adenda 2 de V750-B y su sello; el
  pre-registro fuera de §3, §6 bis y §11; si la lista suplementaria real trae las far_ref con los campos que `etiqueta_lejana`
  espera (sólo lo leí en el generador y en `banco_paridad.etiquetar`: las filas traen `tipo`, `source`, `dist_km`).

## En una pantalla

**Veredicto: LISTO CON CAMBIOS.** No encontré ningún defecto que haga que un brazo mida otra cosa que la escrita en el §3, que
E_lejana sea otra cosa que el §6 bis, ni que la regla elija mal en alguna rama; el agregado reproduce el contrato con la vara.
Lo que pido cambiar es menor y no toca la regla:

1. **VP-01** (gravedad 2): dos de las listas descriptivas que el §6 bis pide «por nombre» se cortan a 20 sin decirlo.
2. **VP-02** (gravedad 2): la lectura L25 pone entre comillas, como texto del pre-registro, una frase que el pre-registro no tiene.
3. **VP-03** (gravedad 2): el placebo de M que cierra la compuerta se mide sobre P (radiante), no sobre el brazo que decide.
4. Las dos piezas que el autor declaró sin mutación (E_lejana con tabla sola excluye los FALSO_POSITIVO del OCR; «elegible» mira
   también tabla más OCR) **están correctas en el código** y las cubrí con escenarios y mutaciones propios (W3, W4; MV2, MV3, MV9,
   MV10: 4 de 4 atrapadas por aserción). Recomiendo incorporar W3 y W4 a la batería del autor (SEGUIMIENTO S-01).

Evidencia que sostiene el veredicto: los 13 escenarios nuevos del autor (E61 a E73) pasan; mis 6 escenarios propios (W1 a W6)
pasan; mis 11 mutaciones de una línea sobre el analizador quedan 11 de 11 atrapadas por aserción, con IDENTIDAD 6 de 6 y CAIDA
como caída; la salida completa del analizador anterior y del nuevo sobre la misma población difiere sólo en el rótulo
«(posición ...)» y el sufijo del veredicto, con y sin far_ref; la batería entera que corrí yo, con el analizador del commit, dio `== PRUEBAS: TODOS LOS ESCENARIOS COMO SE ESPERA (74)` (74 de 74, 0 líneas que no sean OK salvo la de cierre; `probar_bateria_completa_salida.txt`, 02:20 a 02:40 UTC, OMP_NUM_THREADS=1 como el autor), o sea que los 61 escenarios viejos siguen verdes con el agregado.

Ruta del informe: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-2-918174\experiments\_s162_v750a\verificador_posicion\INFORME.md`

## Hallazgos (todos, cobertura primero, peor primero)

### VP-01. Listas descriptivas del §6 bis cortadas a 20 sin avisar
- **ARCHIVO:LÍNEA**: `experiments/_s162_v750a/evaluar_v750a.py:721` (`lst[:20]`, «cambian de publicación contra P») y `:728`
  (`[...][:20]`, «pasadas lejanas ... lista»).
- **QUÉ PASA**: el §6 bis pide «las pasadas que cambian de publicación contra P, por nombre y etiqueta». El analizador imprime el
  conteo completo pero la lista queda en 20 entradas, y no dice que se cortó. El analizador gemelo de V750-B tiene la regla
  VAD2-11 («una lista impresa que se corta lo dice»; `leer_posicion_v750b.py`, función `corta`).
- **CÓMO SE VE**: el operador o Nicolás leen «P-cercano: 24 [...]» y ven 20 nombres; las 4 pasadas faltantes no aparecen en
  ningún lado. Es una descriptiva que no decide, pero es justo la lista con la que se revisa a mano cuándo cambió una publicación.
  Con los números de S165 (1 a 2 de 5.640 pasadas) rara vez pasará de 20 en las alertas; con las far_ref puede.
- **CÓMO REPRODUCIR**: `python experiments/_s162_v750a/verificador_posicion/mis_escenarios.py --dest <dir> --evaluador <evaluar_d25.py> --solo W5`;
  en `<dir>/W5/stdout.txt` la línea «cambian de publicación contra P (radiante), P-cercano: 24» trae 20 entradas. El conteo
  quedó en `vp_W5_cortada.txt` (`declaradas: 24 | entradas listadas: 20 | menciona "cortada": False`).
- **CONFIANZA**: CONFIRMADO (lo medí: 24 declaradas, 20 listadas, sin nota).
- **GRAVEDAD**: 2.

### VP-02. L25 cita como texto del pre-registro una frase que no está en él
- **ARCHIVO:LÍNEA**: `experiments/_s162_v750a/LECTURAS_EVALUAR_V750A.md:36` (fila L25, columna «texto del pre-registro»).
- **QUÉ PASA**: la columna cita entre comillas «los controles y salidas existentes no cambian». `grep -n "controles y salidas
  existentes" PREREGISTRO_V750A.md` no encuentra nada (sólo aparece en L25), y `git show 699e2d04f -- PREREGISTRO_V750A.md` tampoco
  lo trae. Lo que el pre-registro dice (§2 punto 4) es «el tablero no cambia». La lectura toma una decisión real (los controles
  de §7 siguen sobre P radiante, ver VP-03) y la presenta como si viniera de un compromiso previo.
- **CÓMO SE VE**: invisible en el tablero; en la auditoría, una lectura que parece apoyada en el texto sellado y no lo está.
- **CÓMO REPRODUCIR**: `grep -n "controles y salidas existentes" experiments/_s162_v750a/PREREGISTRO_V750A.md experiments/_s162_v750a/LECTURAS_EVALUAR_V750A.md`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2 (no cambia ningún número; sí la honestidad de la trazabilidad, que es lo que A95 y A113 cuidan).

### VP-03. El placebo de M que cierra la compuerta no mide al brazo que decide
- **ARCHIVO:LÍNEA**: `evaluar_v750a.py:514-515` (`m_pares("P", v, canal)` dentro de `pl_m`) frente a `:769-771` (el §6.2 usa `m_pares(PE, ...)`).
- **QUÉ PASA**: el control «placebo K×1,2 (M con comparador)» es compuerta de §7 y se calcula con los pares de P (radiante). Cuando
  la regla elige P-cercano o P-pico, M del veredicto se calcula sobre otros pares (los que publican K y el brazo elegido), y el
  placebo con comparador no se corre sobre ellos; sólo se imprime, informativo y SIN comparador, el placebo de los pares de PE.
  L25 lo declara («miden el instrumento y no la regla de posición»), pero el instrumento de M se aplica a una muestra distinta de
  la que el placebo comprobó.
- **CÓMO SE VE**: físicamente, si el brazo elegido suma al conjunto de pares una protegida que sólo él publica, el comparador
  podría tener un comportamiento propio con ella sin que ningún control lo haya visto. Un riesgo teórico; en la mayoría de los
  casos los pares son los mismos (los tres brazos comparten VRP y casi toda la publicación).
- **CÓMO REPRODUCIR**: leer las dos líneas; no produje un escenario donde difieran (no probado, por eso va como defecto de diseño).
- **CONFIANZA**: SOSPECHA de impacto; CONFIRMADO el hecho de que el control usa P.
- **GRAVEDAD**: 2.

## SEGUIMIENTOS

- **S-01** Incorporar W3 y W4 (`mis_escenarios.py`) a `probar_evaluar_v750a.py` y MV2, MV3, MV9, MV10 a `mutar_evaluar_v750a.py`:
  son las dos piezas que el autor dijo sin cubrir. Sin ellos, quien rompa `etiqueta_lejana` (canal tabla) o el recorrido de
  `CANALES` en `eleg` no hace caer nada.
- **S-02** Tras la corrida completa del medidor (8 a 14 h), confirmar que M63 a M80 no se caen en los escenarios viejos y que mis
  cuatro mutaciones nuevas quedan atrapadas en la batería entera. Mi comprobación de «atrapada» es por aserción sobre W1 a W6,
  no sobre los 74.
- **S-03** El pareo de `dist_ref` del generador y la regla de `punto_pos`/descriptivas usan criterios distintos de fila
  (L27 lo declara); cuando exista la lista real de far_ref, comparar cuántas far_ref pierden su distancia por esa diferencia.
- **S-04** `etiqueta_lejana(..., "tabla")` deja fuera una far_ref cuya tabla tiene RUTINA y el OCR el FALSO_POSITIVO: no es
  lejana para la tabla sola ni es negativo limpio (el banco la etiqueta far_ref). Es una exclusión consistente con L20, no un
  defecto; sólo conviene saber que existe ese estrato.
- **S-05** Los arreglos de VP-01 a VP-03 son del autor; no toqué nada fuera de esta carpeta.

## VERIFICADO LIMPIO (cada ítem con su vara y su comando)

Convención: «escenario» = población sintética + analizador ENTERO con node; «atrapada» = el escenario cae por aserción (línea
que falta o sobra), no por excepción. Control positivo en cada caso: la mutación correspondiente cambia la línea fijada. Control
de instrumento muerto: CAIDA da CAÍDA, no FALLA.

| # | Qué verifiqué | Vara | Evidencia |
|---|---|---|---|
| L-1 | Los tres brazos comparten detección y VRP; sólo cambia el punto de la distancia | §3 | `rec_pos` (l. 347-359) parte de `rec_paq(i,"P")` y sólo reemplaza `distance_class` y `centroid_dist_km`; `vrp()` (l. 410) da el VRP de P para POS. W1, W2, W4 |
| L-2 | P-cercano mide desde el cráter (`pos_crater`), no desde el centro de la grilla | §3, programa | W1 (Lastarria) y E70 del autor; MV7 (`* 0.75` a `* 1.0`) atrapada por W1 |
| L-3 | Borde del radio interior: `<=` igual que `record_cumulo` (4 celdas = 3,0 km exactos en Lastarria) | sellado V750-B `record_cumulo` | W1 pasa con el cercano a 4 celdas publicando y a 5 celdas callando; MV1 (`<=` a `<`) atrapada |
| L-4 | P-pico = el de mayor M13 (el mismo que siembra el cúmulo); P-cercano = el más cercano con desempate (distancia, fila, columna) | `leer_posicion_v750b.py::punto` | lectura lado a lado de `punto_pos` y `punto`: idénticos en regla y desempate; M63, M64 del autor |
| L-5 | El anillo (centroide en el cráter, todos los píxeles a 6 km) separa radiante de cercano/pico | §3 | W2: P publica 6 far_ref, cercano y pico 0 («P (radiante) publica 6 | P-cercano publica 0 | P-pico publica 0») |
| L-6 | E_lejana cuenta far_ref donde el brazo publica; entra a P2' en el mismo bloque noche-volcán con signo correcto | §6 bis | W2 (E_lejana 6/0/0, P2' GANA neto -6 en 6 bloques); MV6 (signo de `c`) y MV11 (`pub` negado) atrapadas por W2 |
| L-7 | E_lejana con la tabla sola excluye FALSO_POSITIVO_OCR | L20, A11 | W4: tabla sola «SIN SUSTRATO (neto 0, bloques 0)» y decide «GANA (neto -8, bloques 16)»; MV2 (CONS a True) y MV10 (tabla a decide) atrapadas |
| L-8 | El canal que decide es tabla en T y tabla más OCR en O también para las far_ref | L20 | MV9 (decide siempre tabla) atrapada por W4 |
| L-9 | «Elegible» exige P1 = 0 también con tabla más OCR | §6 bis | W3: protegida sólo del OCR que K y P publican y cercano/pico pierden: «P-cercano no», elegido P (radiante) aunque cercano gana P2'; MV3 (CANALES a tabla) atrapada |
| L-10 | «No peor»: SIN SUSTRATO con neto 0 sí, con neto positivo no | §6 bis, L22 | W4 (neto 0 sí) y E69 (neto +1 no); MV4 (`<= 0` a `< 0`) atrapada por W4 |
| L-11 | El desempate suma E + E_lejana (no sólo E) | §6 bis | W5: cercano E 0 + E_lejana 6, pico E 4 + 0, elegido P-pico; MV5 (sólo E) atrapada |
| L-12 | Si ninguno gana y P es elegible, P; NINGUNA POSICIÓN ELEGIBLE entra a los motivos del NO CUMPLE | §6 bis, L23, L24 | E63, E65 del autor (reproducidos 13 de 13) y M76, M77 del autor |
| L-13 | Las far_ref no contaminan P1, P2, M, E ni el control positivo | L25, §6 bis | `diff_contaminacion.py`: salida completa de `699e2d04f` y `8b9156476` sobre la misma población, con y sin 3 far_ref; sólo difieren el rótulo «(posición ...)» del §6.2, el sufijo `[posición del record: ...]` y las líneas nuevas de §6 bis, Pcercano/Ppico informativas y P-sinfiltro (declarado) |
| L-14 | Las far_ref sí cambian los conteos de cobertura y de K = producción | L25 | diff entre `base` y `base+3 far_ref` en el analizador nuevo: cambian sólo los conteos (objetivos 49 a 52, K = producción y placebo «de 49 a 52», equivalencia «de 49 a 52», pasadas con diagnóstico del S-1 y filas del S-1 por pasada 145 a 154) y las líneas de §6 bis; ninguna línea de P1, P2, M ni E |
| L-15 | Sin far_ref: «SIN DATO» y la regla se lee igual; con far_ref sin alertados: «un cero de E_lejana no dice nada» | §6 bis | base de `diff_contaminacion` y E71, E72 del autor |
| L-16 | Distancia descriptiva de far_ref: la fila de la tabla, o del OCR desde 2026-06-13 | L27, A119 | W6: 3 de la tabla (abril) + 2 sólo OCR en abril (fuera) + 2 sólo OCR en septiembre = n=5; MV8 atrapada |
| L-17 | Los escenarios del autor caen por aserción sin la implementación | línea base roja | `probar_evaluar_v750a_rojo_posicion_salida.txt`: 13 de 13 FALLA con «falta una línea», ninguna CAÍDA |
| L-18 | E61 a E73 verdes y los 61 viejos intactos con el código del commit | autor 74/74 | corrí la batería entera: 74 de 74 OK (`probar_bateria_completa_salida.txt`); y aparte `--solo E61..E73`: 13 de 13 |
| L-19 | Mutaciones del autor: ninguna equivalente, todas por aserción | autor 18/18 | lectura de `mutar_evaluar_v750a_posicion_salida.txt`: 18 con «FALLAS n de 13» y escenarios nombrados; CAIDA = «CAÍDAS 13 (fallas por aserción 0)»; IDENTIDAD PASA |
| L-20 | Sin guiones largos ni medios en el objeto | regla de Nicolás | grep del guion largo y del guion medio en los 8 archivos del diff: 0 en cada uno |
| L-21 | La cifra del §11 del pre-registro (13 de 13, 74 de 74, 18 de 18) coincide con los archivos de salida guardados | §11 | las tres salidas guardadas dicen eso |
| L-22 | El analizador del tag es el pedido | encargo | `sha256sum evaluar_d25.py` = `2e5576...6747` |

## Mis instrumentos (todos en esta carpeta)

- `LISTA_CAMINOS_previa.md`: la lista de caminos escrita antes de abrir el código.
- `mis_escenarios.py` (W1 a W6) y `mis_escenarios_salida.txt`: 6 de 6 OK con el analizador real.
- `mutar_propias.py` y `mutar_propias_salida.txt`: IDENTIDAD 6 de 6; MV1 a MV11 atrapadas 11 de 11 por aserción; CAIDA como caída.
- `diff_contaminacion.py` y `diff_contaminacion_salida.txt`.
- `probar_bateria_completa_salida.txt`: batería entera (74) con el analizador del commit.

## Dos preguntas del instrumento, resumidas

1. Si lo que mido estuviera roto, ¿mi medición lo vería? Sí para lo que cubren W1 a W6 (cada pieza tiene su mutación atrapada);
   NO para lo que no cubren: la ramificación «P no elegible con candidato que pierde sólo en tabla» (el autor tiene M76), ni el
   comportamiento con datos reales.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Sí: CAIDA da CAÍDA; la IDENTIDAD pasa; y los cuatro escenarios
   decisivos (W1, W3, W4, W5) fallan por línea faltante al romper la pieza que fijan.
