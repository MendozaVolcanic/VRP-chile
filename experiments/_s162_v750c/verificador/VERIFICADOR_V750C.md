# Verificador V750-C: ablacion del oraculo de MIROVA V750 sobre las grillas de N

## Encabezado

- Hora del servidor (GitHub, cabecera Date) al empezar: Sat, 24 Oct 2026 15:47:00 GMT; al cerrar: 16:03:04 GMT.
- Commit medido: `8cc1cba83bf0fefdf11c90d525ea444597006211` (rama `claude/s162-viirs750-f63ef4`, arbol limpio al empezar; al cerrar solo aparece `?? experiments/_s162_v750c/verificador/`).
- Worktree: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-f63ef4`
- Modelo y esfuerzo declarados: Claude Fable 5.1, esfuerzo medio, contexto limpio (recibi solo titulos y script:salida de V1 a V9; lei `INFORME.md` recien despues de escribir los caminos y de correr `medir.py`).
- sha256 de los insumos del auditor al empezar (antes de leer ninguno):
  - `INFORME.md` `3c566eb20ccaee35d36e457d634ce48dee484e5ce133eb7f68e8fd62ecbf4f18`
  - `ablacion.py` `5e6818c23d558120b5dd08b8d37f02269434ae073257f183672c0e85fedb99a3`
  - `oraculo_ablacion.py` `dad4c212cae96bcfcbef384b5475e662ad4b481017bffbf34165054dc434fc07`
  - `extraer_insumos.sh` `b5c9ae16ec10b8b7688adf33866ac6c07829a9ff7ad25bbb9e0249bbfc53a69e`
  - `ablacion_salida.txt` `5c75dff64c600c04317f147212f65dbfd1f758c41307a9f853f351d3359899c1`
  - `ablacion_por_pasada.csv` (no versionado) `db4e6ef7e485790669048daedc3713ef674b44ab0738d4a474e8793d0f01f77d`
- Insumos extraidos con `extraer_insumos.sh` a `C:\Users\nmend\AppData\Local\Temp\verif_v750c_ins\` desde `origin/s159-pruebas` = `812624cc6baf97872e8c9fc09558e809123d92dd` (tras `git fetch`, asi que no es copia atrasada: camino CT1 cerrado).
- Mis scripts (solo en esta carpeta):
  - `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-f63ef4\experiments\_s162_v750c\verificador\medir.py` `013300f690d367ea4855a49c479c11ad6fadfe5bbf3f63ae8177edfb9f856e9d` -> `medir_salida.txt`
  - `...\verificador\medir2.py` `53d3c4259182090e8f7a5ac0139f39dec25304e440bf271ecf71c7a6d5462acb` -> `medir2_salida.txt`
  - `...\verificador\medir3.py` `e9adcde0cc35333c8c146a8a7caff7eb61dc71fea62043fc504847d2c15f97c5` -> `medir3_salida.txt`
  - Re-run completo de `ablacion.py` del auditor: salida en `C:\Users\nmend\AppData\Local\Temp\verif_v750c_ins\rerun_stdout.txt`; copia de la salida original del auditor en `...\verif_v750c_ins\ablacion_salida_auditor.txt` y `...\ablacion_por_pasada_auditor.csv`.
- Denominadores y ventana de todo lo que sigue, salvo que se diga otra cosa: 510 pasadas nocturnas de VIIRS 750 con oraculo (391 del lote de N y 119 del censo), 2026-03-01 a 2026-10-17 (objetivos de N) y 2026-04-05 a 2026-10-16 (censo); negativos limpios del lote: 195 (ventana 2026-04-02 a 2026-10-17). Las grillas se leyeron en su lugar en `D:\vrp-trabajo\temporales\s159_n\` (C: 42,4 GB y D: 9,7 GB libres al empezar; no se copio nada).

## Caminos por los que cada afirmacion podria estar mal (escritos a las 15:47 GMT, antes de leer scripts ni INFORME)

**V1 (controles 510/510).**
- C1a. «Reproduce al port de R2» puede ser trivial si el modulo importa o copia el port de R2 en vez de reimplementar las piezas: la coincidencia mide identidad de codigo, no fidelidad al `.m`.
- C1b. La comparacion de mascara y VRP puede ser con tolerancia que esconde diferencias reales, o puede comparar solo donde ambos detectan.
- C1c. «Reproduce `geo_linear` del runner 510/510» puede ser que el runner y el brazo O leen la MISMA grilla ya interpolada guardada en el npz; entonces el control prueba que el detector es determinista, no que el remuestreo se reprodujo.
- C1d. 510 puede no ser el universo: cuantas pasadas quedaron fuera y por que.

**V2 (60 cumbres: 1, <=5, 8, 23, 13).**
- C2a. «Detecta en el pixel de K» depende de `celda_k` y de su tolerancia: con 1 celda (3x3) se fabrican coincidencias; sin tolerancia se pierden por redondeo. Correr con 0 y con 1.
- C2b. Los 60 pueden no ser «K en 0,0 MW» con el predicado del dashboard.
- C2c. «MIROVA RUTINA» como negativo limpio depende de la ventana y de la calidad de la referencia (A119).
- C2d. Los brazos «una pieza de K» pueden no implementar la pieza de K, o la pieza puede no estar cableada (A89); si un brazo no cambia nada, su «<=5» es trivial.
- C2e. El brazo «vecino mas cercano (runner)» puede leer otra grilla (otra resolucion, otra extension) y no solo otro interpolador.
- C2f. «Grilla de R2 lineal, 13»: si R2 cambia mas que el desplazamiento, ya hay dos cosas cambiadas.
- C2g. Los brazos pueden compartir cache del brazo O sin que lo diga el nombre.

**V3 (53,6 % y 78 %).**
- C3a. «Exceso nativo» y «exceso de grilla» pueden usar fondos de definicion distinta (anillo de K vs fillmissing2; halo de distinto tamano).
- C3b. El exceso puede ser de BT, de NTI o de radiancia; interpolar radiancia y pasar a BT no conmuta.
- C3c. Mediana con excesos nativos ~0 o negativos: la razon explota o cambia de signo.
- C3d. 78 % en las 48 alertadas: las fuertes tienen vecinos calientes, asi que la interpolacion conserva mas por construccion.

**V4 (conclusion: remuestreo lineal calla).**
- C4a. Confunde interpolador (lineal vs vecino) con remuestreo (nativo vs grilla) con geometria (posicion de la grilla).
- C4b. El vecino mas cercano puede ser mas ruidoso y detectar mas en todo, no solo en las cumbres.
- C4c. Los sustitutos del barrido nativo no son el barrido.
- C4d. Puede ser el fondo o la ZONA de la caja (umbrales conservadores fuera del 7x7) y no el pico.

**V5 (25 negativos vs 4; 114,3 ponderados).**
- C5a. «Publica» puede ser el predicado del oraculo y no el del dashboard (A97).
- C5b. «Ponderados» necesita su peso declarado.
- C5c. Denominador y ventana del lote.

**V6 (0,458 / 0,999 / 0,935 / 0,846 / 1 de 510).**
- C6a. n de pares y volcanes; una mediana agrupada puede esconder un volcan (S126).
- C6b. «Fondo de anillo» puede no ser el anillo de K (radios).
- C6c. Circularidad si el VRP «de MIROVA» se obtuvo con el mismo codigo.
- C6d. «Cambia 1 pasada» puede esconder cambio de magnitud en muchas.

**V7 (regresion recalculada, 165 pasadas, 0 detecciones).**
- C7a. El instrumento puede comparar algo que el segundo pase no puede cambiar por construccion.
- C7b. Puede ser que el `.m` NO recalcule la regresion y el brazo lo invente.

**V8 (caja: 71/78, 78/78).**
- C8a. Que las 78 sean del lote y que «publica» sea el predicado correcto.
- C8b. 78/78 con una caja grande puede ser por incluir pixeles lejanos; ver DONDE cae el pixel que salva.
- C8c. Las 7 perdidas pueden ser de un solo volcan.

**V9 (0 de 17 Tupungatito con vecino).**
- C9a. SIN DATO disfrazado de cero (sin grilla, sunglint, escena invalida).
- C9b. 17 de 60 en un volcan sesga el censo.

**Caminos transversales.** CT1 copia atrasada de `origin/s159-pruebas`; CT2 los npz traen salidas que O pueda leer en vez de recalcular; CT3 el script no corre desde cero; CT4 las piezas «de K» no son las de `pipeline.profile` del perfil `mirova_equivalent`.

## Mediciones propias (las dos preguntas del instrumento en cada una)

**M1. Re-run de `ablacion.py` desde cero** (CT3). Pregunta 1: si el script no corriera o diera otra cosa, el diff lo ve. Pregunta 2: un script muerto no escribe `ablacion_salida.txt`; se comparo contra la copia guardada antes. Resultado: salida IDENTICA linea a linea (`diff` vacio) y CSV con el mismo sha256 `db4e6ef7...`. Los numeros del auditor se reproducen en mi maquina sobre las 510 grillas (`sin grilla en disco: 0`).

**M2. Tolerancia de `celda_k`** (`medir.py`, C2a). Pregunta 1: si la tolerancia de una celda fabricara coincidencias, los conteos con tol 0 y tol 1 difieren. Pregunta 2 (control positivo): en las 48 cumbres donde MIROVA alerto el `.m` detecta en la celda de K en 33 con tol 1; si `celda_k` apuntara a cualquier parte, ese 33 cae a ~0 con tol 0. Resultado: censo 60, todos los brazos y las cuatro variantes del runner dan EXACTAMENTE lo mismo con tol 0, 1 y 2 (O 1/1/1, O_8vec 5/5/5, todoK sin compuerta 8/8/8, geo_nearest 23/23/23, geo_cubic 7, r2_linear 13, r2_nearest 26), y todas las coincidencias estan a distancia 0. Control positivo: pos48 con tol 0: O 30 (33 con tol 1), O_sens 41 (44), geo_nearest 30 (31), r2_linear 19 (19). La tolerancia no fabrica nada en el censo y mueve 1 a 3 de 48 en las alertas. Ninguna pasada del runner esta SIN DATO (las 4 variantes presentes en 60 de 60 y 48 de 48).

**M3. Zona de la caja por defecto donde cae la celda de K** (`medir2.py`, C4d, C9). Pregunta 1: si la zona no importara, los 23 recuperados por vecino mas cercano se repartirian como el censo (19 en zona 1, 38 en zona 2, 3 en zona 0). Pregunta 2: el margen con umbrales de zona 2 nunca puede ser menor que con los propios (aserto en el bucle, paso 60 de 60). Resultado: **los 23 de geo_nearest, los 7 del cubico, los 13 de r2_linear y los 26 de r2_nearest caen TODOS en zona 2** (el 7x7 central sensible); en las 22 cumbres de zona 0 o 1 ningun remuestreo recupera ninguna. Las 22 son Tupungatito 17 (zona 1), PCC 4 (3 en zona 0 y 1 en zona 1) y Lascar 1. Distancia de la celda de K al centro de la grilla de MIROVA: Tupungatito mediana 4,80 km (min 4,37, max 5,41; n = 17; inner 7 km; mitad de la caja sensible 2,625 km), PCC 10,56 km (inner 20), Isluga 0,75, Lascar 1,50, PP 2,02, Lastarria 2,70. Margen del pase 1 en el entorno de K con los umbrales de su zona vs con los de zona 2: zona 1 mediana 0,212 [0,179; 0,250] vs 0,755 [0,714; 0,879], n = 19 (3 pasarian con zona 2); Tupungatito 0,214 vs 0,802 (n = 17); zona 2: 0,702 en ambos (n = 38, 1 pasa).

**M4. V3 con la celda exacta de K en vez del maximo del 3x3, y estratificado por halo** (`medir.py`, C3a). Pregunta 1: si las dos definiciones del exceso no fueran comparables, el estrato por halo k lo mostraria. Resultado: censo 60: max 3x3 mediana 0,536 [0,401; 0,689]; celda exacta 0,545 [0,330; 0,667]; n = 60; en 59 de 60 el F de K tiene 1 solo alertado en la escena (n_hot = 1) y k = 3 en los 60, igual que el halo que usa el brazo de la grilla (`OA.vrp` con 1 celda: k = 3). pos48: 0,780 max 3x3, 0,802 celda exacta, n_hot 1 en 46 de 48, k = 3 en 48. Las dos definiciones usan el mismo fondo (fillmissing2 lineal bajo halo 3x3) en dos geometrias; 0 excesos nativos <= 0 (C3c cerrado).

**M5. Las 7 protegidas que la caja por defecto pierde** (`medir.py`, C8b, C8c). Resultado: **las 7 son de Puyehue-Cordon Caulle** (inner 20 km), ids 141, 364, 220, 69, 231, 257, 334, MIROVA 1,00 a 1,43 MW, y en las 7 el pixel mas radiante que recupera la caja sensible esta a **7,65 a 7,83 km del centro de la grilla**, en zona 1 de la caja por defecto (el lacolito del Cordon Caulle, A20/A68). O 71/78, O_sens 78/78, O_circ 78/78 reproducidos.

**M6. El anillo de los brazos «de K»** (`medir3.py`, C6b, CT4). `oraculo_ablacion.py` l. 177 y 222 usan el anillo `inner_radius_km..25 km` (3 a 20 km segun volcan); K usa 5..25 km fijo (`pipeline.profile`: `BG_INNER_KM = 5.0`, `BG_OUTER_KM = 25.0`; `pipeline/process_viirs_mod.py:539`). Pregunta 1: si cambiar el anillo no hiciera nada, las medianas coinciden en los volcanes con inner = 5 y difieren en PP (3). Resultado sobre las 181 alertas que deciden: O_fanillo con anillo 5..25 publica 89/181, razon 0,458 [0,307; 0,698] n = 89, identico al del auditor; O_comp1 145/181, 0,996, identico. En esta poblacion el unico volcan con inner distinto de 5 que publica es PP (8 alertas, inner 3) y su mediana no se mueve. El error de etiqueta no cambia V6.

**M7. V5 y V6 por volcan desde el CSV** (`medir.py`). Negativos limpios del lote 195: O publica 4 (Lascar 3, Isluga 1), geo_nearest 25 (Isluga 12, Lascar 9, Chaiten 1, PP 1, Chillan 1, Villarrica 1; peso 114,3), r2_linear 15 (84,5), todoK sin compuerta 18 (42,8; PCC 10). Razon O/MIROVA por volcan: Isluga 0,997 (n = 24), Lascar 0,999 (79), Chillan 0,998 (28), PP 0,994 (8), Villarrica 1,042 (5), Chaiten 0,861 (1): plana entre volcanes. O_fanillo por volcan: Isluga 0,329 (4), Lascar 0,421 (61), Chillan 0,684 (22), PP 1,724 (1): el 0,458 es Lascar en 61 de 89.

## Veredicto por afirmacion

### V1. Controles 510/510: CONFIRMADO EN PARTE (gravedad 1)

- CONFIRMADO: identidad contra el port de R2 510/510 y O = `geo_linear` del runner 510/510 se reproducen en mi re-run (M1). La comparacion de identidad es estricta: `np.array_equal` de la mascara y VRP a 1e-9 (`ablacion.py:187-188`); contra el runner, npix y VRP a 1e-6 (l. 191-193), no la mascara.
- LA PARTE QUE NO DICE LO QUE PARECE (C1a, C1c): el modulo `oraculo_ablacion.py` es una reescritura del port de R2 (docstring l. 4), asi que «reproduce al port de R2» prueba que la reescritura no rompio nada, no que el `.m` esté bien traducido; esa fidelidad la sostiene otra cosa que si verifique: `experiments/_s159/o1/comparar_octave_ports_salida.txt` (rama `s159-pruebas`) da 0 discrepancias de deteccion entre Octave y el port de R2 en 791 escenas (1 Etna, 40 chilenas guardadas, 150 variantes, 600 sinteticas), y en VRP `comparar_vrp_salida.txt` da oct/R2 = 1,000 en 13 de 14 escenas y **1,818 en una** (Tupungatito nearest, 1 pixel: la triangulacion de `fillmissing2` no es unica, lo declara el port l. 7-12). Y el control (2) es de determinismo: el npz guarda `gg["linear"]` que es exactamente la entrada del runner (`probe_n.py:370,383`), no se re-remuestreo nada. Las dos cosas estan bien dichas en `ablacion.py:16-18`; el titulo de V1 las resume de mas.
- C1d: 520 resultados, 510 ok, 4 `volcan_fuera_del_granulo`, 6 sin granulo (mi lectura de `resultados_*.json`). El universo de N tiene 398 + 122 = 520 objetivos.

### V2. Censo 60: 1, <=5, 8, 23, 13: CONFIRMADO (gravedad 2 por la lectura que se le da, ver V4)

- Reproducido en M1 y, con tolerancia 0, 1 y 2, en M2: los conteos no dependen de la tolerancia (todas las coincidencias a distancia 0). Camino C2a cerrado.
- C2b: `clase == cumbre_0mw` se arma en `06_censo.py:37` con `lab == neg_limpio and not pub_prod and dc == summit and pc_vrp == 0.0`, o sea el predicado de produccion persistido (`pub_prod`), no otro. Los 60 vienen de 6 volcanes: Isluga 22, Tupungatito 17, Lascar 10, PP 6, PCC 4, Lastarria 1.
- C2c: ventana del censo 2026-04-05 a 2026-10-16, posterior a marzo (A119); la etiqueta RUTINA viene del canal CONS (`mirova[].source = CONS` en el ejemplo leido).
- C2d/CT4, las piezas «de K» contra `pipeline.profile` (`VRP_PROFILE=mirova_equivalent`): 8 vecinos sin el central = `detection_context.py:162-179` (CONFIRMADO); K1 -0,8 = `NTI_K1_NIGHT = -0.8`, piso 0,010 = `DNTI_CONTEXTUAL_C1_SCENE = 0.01` usado para dNTI y dETI (`process_viirs_mod.py:809,893`) (CONFIRMADO); conectiva `max` en los dos (`ENABLE_TESTS_23_PROSE_BRANCH = True`; el `.m` l. 380-382 tambien es `max`) (CONFIRMADO); compuerta `bt > t_bg + 3 K` solo en el primer pase y en el absoluto = `NTI_BT_SANITY_K = 3.0`, `process_viirs_mod.py:674,727` y el segundo pase sin compuerta (`second_pass_adjacent` no recibe `bt_sanity_k`) (CONFIRMADO); regresion del pase 1 reutilizada = `second_pass_adjacent` recibe «eti: 2D array ETI original» (`detection_context.py:873`) (CONFIRMADO); recorte a cero por pixel = `probe_n.py` docstring, tres `np.maximum(x, 0.0)` contados en N (CONFIRMADO por lectura de N, no lo re-medi); fondo de anillo: VER VV-02 (el anillo no es el de K en 4 volcanes; efecto nulo en V6). Todos los brazos actuan en > 0 pasadas (control 3), salvo `O_regp1`, que actua sobre el coeficiente (3b).
- C2e: `geo_nearest` es la MISMA grilla (misma esquina `ul_x, ul_y`, mismas 67 x 67 celdas de 750 m, `probe_n.py:370`) con otro interpolador; `r2_linear` es la grilla corrida 187,5 m en x e y (`ul_x_r2 = ul_x + 187.5`, leido en objetivos) con el mismo interpolador. O sea que 1 -> 23 aisla el interpolador y 1 -> 13 aisla la fase de la grilla. Esto es lo que V4 necesita y lo tiene.

### V3. 53,6 % y 78 %: CONFIRMADO, con una salvedad de lectura (gravedad 1)

- Reproducido (M1) y robusto a la eleccion de celda (M4: 0,545 con la celda exacta, 0,536 con el maximo del 3x3). Las dos definiciones del exceso usan el mismo fondo (fillmissing2 lineal bajo halo 3x3, k = 3 en los 60 y en las 48) en dos geometrias; no hay excesos nativos <= 0. Respuesta a la pregunta clave: **si, miden lo mismo con el mismo fondo**; lo unico que cambia entre numerador y denominador es la geometria (celda interpolada vs pixel nativo).
- Salvedad (C3b, SOSPECHA menor): la radiancia nativa `F_L_hot_pc` sale de `bt_to_spectral_radiance(bt)` de produccion (`probe_n.py:121-128`: L1B -> BT -> radiancia con constantes de produccion) y la de la grilla es `rad["M13"]` de L1B directa; la razon radiancia grilla/nativa de 0,918 incluye ese ida y vuelta. No lo medi; esperable < 1 %, no cambia un 0,54.
- La frase «la señal que sobrevive al remuestreo separa lo que MIROVA alerto de lo que callo» (INFORME l. 93-94) es C3d: las 48 alertadas tienen n_hot = 1 en 46, asi que no es que tengan vecinos calientes en la mascara de K, pero si pueden tener vecinos tibios reales que el promedio lineal conserva; la medicion no separa «señal mas fuerte» de «señal mas extensa». Es una lectura, no un error.

### V4. Lo que calla es el remuestreo lineal: CONFIRMADO EN PARTE (gravedad 3)

- Lo que la evidencia SI distingue (C4a): interpolador (misma grilla, lineal 1 / cubico 7 / vecino 23) y fase de la grilla (lineal corrida media celda 13). No distingue «grilla» de «barrido nativo» (C4c: no hay brazo nativo; el INFORME lo declara y pide el probe). C4b (el vecino solo es mas ruidoso): en las 48 alertadas el vecino NO gana (30-31 contra 33 del lineal con tol 1, M2), y en los negativos del lote publica 25 contra 4 (V5): es mas permisivo en general, pero sus 23 del censo caen exactamente en la celda de K (distancia 0 en los 23), no en cualquier parte. La conclusion se sostiene para lo que mide.
- **La parte que falta (C4d, M3): la atribucion vale solo para las 38 cumbres en la zona sensible (7 x 7 central) de la caja.** Las otras 22 (Tupungatito 17, PCC 4, Lascar 1) caen en zona 0 o 1, donde el `.m` exige 0,02 de contraste y 10 sigma, y ahi NINGUN remuestreo recupera NINGUNA: el margen del pase 1 con los umbrales de su zona es 0,21 (mediana, n = 19) y con los de la zona sensible seria 0,76. En esas 22 lo que calla primero es la geometria de la caja respecto del centro de la grilla de MIROVA (Tupungatito: el pixel de K esta a 4,4 a 5,4 km del centro de la grilla, fuera del 7 x 7 de 2,6 km de semilado; es el mismo desplazamiento centro-crater de A63), y recien despues el remuestreo (con umbrales sensibles solo 3 de 17 pasarian). El INFORME deja Tupungatito «SIN ATRIBUIR»; esta medido que la zona de la caja explica la mayor parte del deficit de margen (0,21 -> 0,80) y que el remuestreo explica el resto. Mi gravedad 3: la respuesta a «que pieza» es DOS piezas, y la segunda es por volcan (depende de donde MIROVA centra su grilla y de que ROI usa para ese volcan, cosa que el `.m` dice que es configurable, l. 120-125, y que el paquete OSF solo muestra para una adquisicion de 2023).

### V5. 25 negativos (114,3) contra 4: CONFIRMADO (gravedad 1)

- Reproducido (M1, M7). «Publica» es el predicado de N (`ablacion.py:106-112`: >= 1 pixel, VRP > 0, pixel mas radiante a <= inner del centro), declarado en el INFORME l. 79-80; no es el del tablero (C5a), pero la comparacion es entre variantes del mismo oraculo con el mismo predicado, asi que la diferencia 4 contra 25 es valida. Peso = N/n del estrato de muestreo (`02_seleccion.py:97,114`); denominador 195 negativos limpios del lote, peso total 5385,5, ventana 2026-04-02 a 2026-10-17. Por volcan los 25 son Isluga 12 y Lascar 9 (M7): la frase «no hay un paquete sin remuestreo que calle lo que MIROVA calla» esta medida en dos volcanes sobre todo.

### V6. La magnitud la da el fondo: CONFIRMADO (gravedad 2)

- 0,999 (n = 145, 127 entre 0,8 y 1,25), 0,458 (n = 89), 0,935 (n = 145), 0,846 (1 px, n = 60) y «recorte cambia 1 de 510» reproducidos (M1). No es circular (C6c): `mirova_vrp` es `max(vrp_mw)` de las filas del scraper de MIROVA pareadas a la pasada (`01_poblacion.py:120`), no un calculo propio. Por volcan la razon del `.m` es plana (0,994 a 1,042 en los 5 volcanes con n >= 5, M7). Anillo de K de verdad (5..25 km) en vez de `inner..25`: 0,458 identico (M6).
- Dos salvedades: (a) el 0,458 es Lascar en 61 de 89 pares y va de 0,33 (Isluga) a 0,68 (Chillan): la direccion es la misma en todos, el numero no es universal; (b) el VRP del port tiene una ambiguedad conocida en cumulos de 1 pixel (oct/R2 = 1,818 en una escena, V1), que el 0,996 de «O 1 px, n = 60» contra MIROVA sugiere que no muerde en esta poblacion, pero no esta medido aparte. C6d: no medi si el recorte cambia magnitudes sin cambiar la pasada; «O_rec 5+ px 1,000 [0,990; 1,013]» contra «O 5+ px 1,000 [0,990; 1,003]» en la salida indica que si mueve el cuartil alto en algo, poco.

### V7. La regresion del segundo pase no decide: CONFIRMADO (gravedad 1)

- El `.m` SI recalcula: el segundo pase llama de nuevo a `contextualDetectionPass` (l. 228-235) y dentro se hace `polyfit` sobre la poblacion sin los alertados del pase 1 (l. 343-346), asi que C7b esta cerrado y `reg_p1 = False` es el `.m`. El brazo `O_regp1` fija el coeficiente del pase 1 (`oraculo_ablacion.py:189-190`), que es lo que K hace (CT4 arriba). Control 3b reproducido: 165 pasadas con excluidos, 165 con coeficiente distinto, maxima diferencia en el contraste ETI 0,000393, bajo el piso de 0,003; `actua_O_regp1 = 0` (ninguna mascara ni VRP cambia). C7a: el instrumento compara la mascara final y el VRP, que el segundo pase si puede cambiar (el control 3 muestra que los otros brazos lo cambian), asi que el cero no es trivial.

### V8. Caja: 71/78 y 78/78: CONFIRMADO EN PARTE (gravedad 3)

- Numeros reproducidos (M1, M5): O 71, O_sens 78, O_circ 78 de 78 protegidas que deciden (lote, no censo).
- La parte que el titulo esconde (C8b, C8c): **las 7 son todas de Puyehue-Cordon Caulle** y en las 7 el pixel que la caja sensible recupera esta a 7,65 a 7,83 km del centro de la grilla de MIROVA, en la zona conservadora de la caja por defecto. No es «la caja» como pieza general: es que el 7 x 7 centrado en el centro de la grilla no cubre el lacolito de PCC, y MIROVA, que si publica esas 7 alertas de 1,0 a 1,4 MW, por fuerza tiene para PCC una ROI que las cubre (el `.m` l. 120-125 dice que las ROI se corren y redimensionan por volcan). Las dos cajas sensibles del brazo (21 x 21 entero, o circulo de 20 km para PCC) son dos lecturas posibles de esa ROI desconocida, y cualquiera de las dos cuesta negativos (8 y 12 crudos del lote contra 4). Asi que V8 es un hallazgo sobre PCC y sobre que la ROI de MIROVA por volcan no esta en el paquete OSF, no sobre un parametro global.
- Ademas, la «caja por defecto» 7 x 7 sensible dentro de 21 x 19 es un SUPUESTO tomado de UNA matriz de ejemplo del paquete (VJ1, 2023-05-19, `_s158_audit_r2/rb/00_box_mat.txt`: BOX==2 7 x 7 central, BOX==1 21 x 19), que ademas contradice el comentario del propio `.m` (l. 111-118: BOX==1 «central volcanic ROI ... conservative», BOX==2 «extended volcanic ROI surrounding the central region ... more sensitive»). Ver VV-01.

### V9. Tupungatito 0 de 17 con vecino mas cercano: CONFIRMADO, y queda ATRIBUIDO en parte (gravedad 2)

- Reproducido con tol 0, 1 y 2 (M2) y no es SIN DATO (C9a): las 17 pasadas tienen resultado de las 4 variantes, `motivo_vacio = None`, `nan_m13 = 0`, y `n_abs/n_p1/n_p2 = 0/0/0` en lineal y en vecino: el oraculo no ve nada en toda la escena de 67 x 67, no solo en el pixel de K. Grillas presentes en disco (M1: sin grilla 0).
- Lo que el INFORME deja «SIN ATRIBUIR» esta en M3: la celda de K esta a 4,37 a 5,41 km del centro de la grilla, en zona 1 (conservadora) en las 17; el margen propio es 0,214 y con umbrales sensibles seria 0,802 (3 de 17 pasarian con la caja circular de 7 km, `O_circ enK 3/17`). O sea: primero la zona de la caja (factor ~4 en el margen), despues el remuestreo (todavia 0,80 < 1 con umbrales sensibles). El vecino mas cercano no se puede probar en zona 2 porque la grilla de vecino no esta guardada.

## Hallazgos propios

### VV-01. La caja «por defecto» del oraculo es la de una matriz de ejemplo y contradice el comentario del `.m`; la ROI por volcan de MIROVA no esta en el paquete

- ARCHIVO:LINEA: `C:\Users\nmend\AppData\Local\Temp\verif_v750c_ins\hotspot.m` l. 105-125 (= `origin/s159-pruebas:experiments/_s159/o1/o2_paquete/MIROVA_VIIRS750_hotspot_detection.m`); `experiments/_s158_audit_r2/granulos/probe_granulos.py:44-53` (rama `s159-pruebas`, «SUPUESTO declarado»); `experiments/_s162_v750c/oraculo_ablacion.py:122-135`.
- QUE PASA: el `.m` recibe BOX como entrada y no la define; su comentario describe BOX==1 como la ROI central conservadora y BOX==2 como la extendida sensible, mientras que la unica matriz de ejemplo del paquete (una adquisicion VJ1 de 2023) trae BOX==2 en el 7 x 7 central y BOX==1 en un bloque de 21 x 19 (no 21 x 21). El port y la ablacion siguen la matriz, con el bloque simetrizado a 21 x 21. Fisicamente: donde esta la zona sensible decide si un pixel tibio de cumbre a 3 a 8 km del centro de la grilla (Tupungatito, PCC) se mira con 0,003 o con 0,02 de contraste. Toda la columna «caja» de V2, V4, V8 y V9 hereda ese supuesto: 22 de las 60 cumbres del censo y las 7 protegidas de PCC estan fuera del 7 x 7.
- COMO SE VE EN EL DASHBOARD: invisible hoy (la ablacion no esta en produccion). Si el paquete se adopta con esta caja, Tupungatito y PCC quedarian con umbrales conservadores en el crater y en el lacolito; con la caja «sensible» 21 x 21, entrarian 4 a 8 negativos mas del lote.
- COMO REPRODUCIRLO: `git show origin/s159-pruebas:experiments/_s158_audit_r2/rb/00_box_mat.txt`; `sed -n 105,125p` del `.m`; `python medir2.py ...` (bloque «distancia de la celda de K al centro de la grilla»).
- CONFIANZA: CONFIRMADO (leido y medido). GRAVEDAD: 3 (tuerce que alertas publica el paquete en dos de los once volcanes; no toca produccion hoy).

### VV-02. Los brazos «fondo de anillo» y «compuerta» no usan el anillo de K sino `inner_radius_km..25 km`; el INFORME lo llama «la mediana de 5 a 25 km, como K»

- ARCHIVO:LINEA: `experiments/_s162_v750c/oraculo_ablacion.py:177` (`anillo = (dk > (inner_km or 0)) & (dk <= 25.0)`) y `:222`; docstring l. 17 y 22; `INFORME.md` l. 121 («la mediana de 5 a 25 km, como K»); K: `pipeline/profile.py:127-128` (`BG_INNER_KM = 5.0`, `BG_OUTER_KM = 25.0` en `mirova_equivalent`), `pipeline/process_viirs_mod.py:539`.
- QUE PASA: para Isluga, Lascar, Chillan, Villarrica y Chaiten (inner 5) es el mismo anillo; para PP y Lastarria (3), Tupungatito (7) y PCC (20) no. Medido (M6): sobre las 181 alertas que deciden, con el anillo de K de verdad el 0,458 y el 0,996 no cambian (el unico volcan con inner distinto de 5 que publica es PP, 8 pares, misma mediana). En el censo no lo medi; ahi PCC con anillo 20..25 (una corona de 5 km en el borde de la escena) es donde mas podria diferir.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: `python medir3.py --insumos ... --grillas ...`.
- CONFIANZA: CONFIRMADO (codigo leido, efecto medido nulo en V6). GRAVEDAD: 1 (error de etiqueta sin consecuencia en los numeros reportados).

### VV-03. El «predicado de N» de publicacion y el control (2) no comparan mascaras: una coincidencia de npix y VRP puede esconder pixeles distintos

- ARCHIVO:LINEA: `experiments/_s162_v750c/ablacion.py:190-194`.
- QUE PASA: el control «O = geo_linear del runner» compara npix y VRP a 1e-6, no la posicion de los pixeles. Como la entrada es identica (mismo npz) y el detector es determinista, el riesgo es nulo aqui, pero el control no lo demuestra: dos mascaras distintas con el mismo npix y el mismo VRP pasarian.
- COMO REPRODUCIRLO: agregar `np.array_equal` contra `pixeles` del runner; no lo hice porque mi M2 ya compara posiciones (celda de K) y da distancia 0 en todas las coincidencias.
- CONFIANZA: CONFIRMADO por lectura. GRAVEDAD: 1.

### VV-04. (fundido con V4 y V9) Dos piezas, no una: la zona de la caja respecto del centro de la grilla de MIROVA explica el silencio de las 22 cumbres fuera del 7 x 7

Ya desarrollado en V4 y V9 (M3). Se lista aqui para que el orquestador lo vea como hallazgo con su propia gravedad: **3**. Es el mismo mecanismo que V8 en PCC: la grilla de MIROVA no esta centrada donde K ancla (Tupungatito 4,8 km, A63), y la caja por defecto no llega.

## SIN DATO

- «K publica 0,510» (INFORME l. 28): viene de N, no lo verifique.
- La razon de magnitud por volcan del brazo de recorte y el efecto del recorte sobre magnitudes sin cambio de pasada (C6d): no medido.
- El ida y vuelta L1B -> BT -> radiancia en `F_L_hot_pc` contra la radiancia L1B de la grilla (C3b): no medido; esperable < 1 %.
- Que hace el vecino mas cercano en Tupungatito con umbrales sensibles: la grilla de vecino no esta guardada en los npz (solo `gg["linear"]`, `probe_n.py:383`), asi que no se puede correr `O_circ` sobre ella. Se necesitaria regenerarla desde el granulo.
- El brazo «sin remuestreo» (barrido nativo): no existe, como declara el INFORME.

## VERIFICADO LIMPIO

- `ablacion.py` corre desde cero sobre los insumos extraidos de `origin/s159-pruebas` (`812624cc6`) y las 510 grillas de `D:\vrp-trabajo\temporales\s159_n\`, y produce exactamente la salida y el CSV del auditor (`diff` vacio; sha256 `db4e6ef7...` del CSV). Comando: `bash experiments/_s162_v750c/extraer_insumos.sh C:/Users/nmend/AppData/Local/Temp/verif_v750c_ins` y `PYTHONIOENCODING=utf-8 python ablacion.py --insumos C:/Users/nmend/AppData/Local/Temp/verif_v750c_ins --grillas D:/vrp-trabajo/temporales/s159_n` desde `experiments/_s162_v750c/`.
- La tolerancia de `celda_k` no fabrica coincidencias: tol 0 = tol 1 = tol 2 en los 60 del censo, todos los brazos y variantes; control positivo en pos48 (30 a 33). Comando: `python verificador/medir.py ...` (bloques censo60 y pos48).
- Las piezas «de K» de la ablacion coinciden con `pipeline.profile` del perfil `mirova_equivalent` hoy (8 vecinos, K1 -0,8, C1 0,010, `max`, compuerta de 3 K solo en el pase 1, regresion del pase 1 reutilizada), salvo el anillo (VV-02, sin efecto en V6). Comando: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.NTI_K1_NIGHT, p.DNTI_CONTEXTUAL_C1_SCENE, p.ENABLE_TESTS_23_PROSE_BRANCH, p.NTI_BT_SANITY_K, p.BG_INNER_KM, p.BG_OUTER_KM)"`.
- `mirova_vrp` de los objetivos es el VRP del scraper de MIROVA, no un calculo propio (`git show origin/s159-pruebas:experiments/_s159/n/01_poblacion.py | sed -n 120p`): el 0,999 no es circular.
- El `.m` recalcula la regresion en el segundo pase (l. 228-235 y 343-346) y el port de R2 da 0 discrepancias de deteccion contra Octave en 791 escenas (`comparar_octave_ports_salida.txt` en `s159-pruebas`).
- Las 17 pasadas de Tupungatito del censo no son SIN DATO: grilla presente, `motivo_vacio = None`, `nan_m13 = 0` en las 4 variantes (`medir.py`, bloque V9).
- El arbol del worktree quedo sin cambios fuera de `experiments/_s162_v750c/verificador/` (`git status --short`); no hubo commit, push, stash ni despacho de Actions.
