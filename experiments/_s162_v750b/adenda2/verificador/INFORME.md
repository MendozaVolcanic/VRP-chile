# Verificador con contexto limpio: adenda 2 de V750-B (posición del record y pasadas lejanas de MIROVA)

- Hora del servidor al abrir: Tue, 27 Oct 2026 22:44:47 GMT (header Date de `gh api -i repos/MendozaVolcanic/VRP-chile`);
  al cerrar: 23:04:30 GMT.
- Lista de caminos escrita ANTES de abrir el código: `LISTA_CAMINOS_previa.md`, sha256
  `0231d1ae749199f211cc8b977bf813a558cd57017c19c82a665ae7945ffa4d5f` (verificado sin cambios al cerrar).
- Commit medido: `83405c557` (HEAD al empezar; HEAD al cerrar `245fe46e5`, que sólo cambió `tasks/LOOP_VIIRS750.md`:
  los archivos de la adenda son los mismos). Contexto sellado medido en `origin/main` `bd711db63` (población y banco) y
  en el tag `s162-v750b-sellado` (analizador).
- Modelo: Sonnet 5.5 (claude-sonnet-5-5), contexto limpio: leí la adenda y su código como objeto, no vi el informe de ningún otro verificador de esta adenda.
- Entorno: Windows 11, Python 3.12, node del PATH. No corrí nada en Linux ni en GitHub Actions.
- Qué NO miré (ver SIN DATO): el probe contra NASA (no hay token ni red a LAADS), resultados reales de un run, el
  workflow en vivo, `mutar_adenda2.py` del autor (crea copias temporales dentro de `adenda2/`, fuera de mi carpeta; usé
  mi propio arnés), `adenda1/` salvo lo que la adenda 2 reutiliza, y la rama de disparo `s162-v750b-disparo`.
- Límites cumplidos: sólo escribí dentro de `experiments/_s162_v750b/adenda2/verificador/` y en
  `C:\vrp-trabajo\temporales\v750b_ver2\`; sin commit, push ni workflows; `git status` fuera de mi carpeta limpio. C: 23 GB
  y D: 7,5 GB libres (arriba de 3 GB). Una salvedad: la batería del autor (que me pidieron correr) crea y borra en el
  acto `experiments/_s162_v750b/_p7_analizar_otro.py` (P7); comprobé que no quedó residuo.

## En una pantalla

**Veredicto: LISTO CON CAMBIOS.** La lectura sellada de V750-B no se contamina y los tres brazos miden lo que dicen.
Pero hay un paso del procedimiento que pierde datos en silencio y varias cosas que conviene arreglar o declarar antes
del sello.

Lo que se sostiene (evidencia mía, no del autor):
1. La lista del run es exactamente la sellada seguida de las 20 suplementarias (`run[:5841] == sellada`,
   `run[5841:] == supl`), ids sin choque, y el orden dentro de cada gránulo se conserva, así que los 5.841 objetivos sellados
   se procesan igual que sin la adenda (19 de las 20 caen en gránulos que ya se bajan; 1 gránulo nuevo).
2. La cadena sellada (analizador y compañero de la adenda 1) itera sólo sobre `obj`: los resultados de más no entran a
   ninguna métrica; lo único que cambia es la línea informativa «con resultado N».
3. El lector, en su fila «radiante», da EXACTAMENTE las filas B0 a B5 del analizador sellado (canales decide y tabla)
   con cráter centrado y con cráter corrido del centro (T1, T1b). Ese es el cimiento de la comparación y está sano.
4. Reproduje el ensayo: 5.841 contra 5.841 IGUALES, 20 `far_ref` con gránulo, 0 sin gránulo, archivo suplementario
   byte a byte igual (`ef76b26b...`), aun con otro sha del consolidado.

Lo que hay que mirar (todos en detalle abajo), de más a menos grave:
- **VAD2-01 (gravedad 3)**: `separar_resultados_v750b.py` pisa en silencio resultados cuando dos carpetas de artefactos
  se llaman igual, y el pre-registro manda juntar el run con su relanzamiento. Además es un paso innecesario para
  proteger la lectura sellada (punto 2).
- **VAD2-02 (2)**: el lector cuenta pasadas con K distinto de producción que el analizador sellado saca de todos los
  brazos (§7), así que su fila «radiante» no reproduce B0/B1 cuando hay alguna.
- **VAD2-03 (2)**: si el control del generador falla, deja en la carpeta los archivos de la corrida anterior (la lista
  del run incluida), contra lo que dice el texto.
- **VAD2-04 (2)**: la batería y el nulo del autor son angostos. De 30 mutaciones mías sólo 6 se atrapan (14 de 20 en el
  lector sobreviven, 3 de 3 en el separador y 7 de 7 en el generador: 24 en total, 22 sin contar 2 equivalentes). Una de ellas,
  el ancla en el cráter, importa y el código de hoy está bien (T1b).
- **VAD2-05 (2)**: la vara 3 mezcla filas OCR de antes del 2026-06-13 (A119) en «alertas con distancia»: 19 de 273.
- **VAD2-06 (2)**: el despacho no define cómo se relanza con `SOLO` (con la lista sellada por defecto, los ids
  suplementarios se descartan sin error y el job sale verde).
- **VAD2-07 (2, SOSPECHA)**: «far_ref: publica 0» no distingue «no había alertados» de «había y no publica».
- Seis hallazgos menores (gravedad 1): VAD2-08 a VAD2-13.

## Hallazgos

### VAD2-01. El separador pisa resultados cuando dos carpetas de artefactos tienen el mismo nombre (y no hace falta)
- ARCHIVO:LÍNEA: `adenda2/separar_resultados_v750b.py:36` (`q = dest / parte / Path(d).name / rel`); SCRIPT:SALIDA
  `verificador/ver_t4_separar_colision.py`, `verificador/ver_t4_salida.txt`.
- QUÉ PASA: el separador escribe `dest/<parte>/<nombre de la carpeta>/<ruta relativa>`. Si la corrida original y su
  relanzamiento con `SOLO` están en dos carpetas de igual nombre (ambas `artefactos`, por ejemplo) con la misma ruta
  relativa `s162-v750b-chunk-3/resultados_03.json`, la segunda pisa a la primera y los resultados «ok» de la original
  desaparecen. El mensaje final cuenta las filas escritas («sellado 4») y no las que sobreviven. El pre-registro (§9,
  «Run a medias») manda justamente relanzar y juntar. Por la otra cara: el analizador y el compañero iteran sólo sobre
  `obj` (`analizar_v750b.py:203-209`, `adenda1/cobertura_cajas_v750b.py:64-73`), así que dejar los resultados sin separar sólo
  cambia la línea informativa «con resultado N» (lo comprueba el testigo P8 del propio autor). El paso lossy protege una línea.
- CÓMO SE VE EN EL DASHBOARD: invisible. En la lectura sellada aparecería como pasadas SIN DATO que sí se procesaron;
  con más del 2 % o una protegida, la cobertura cierra y la lectura se frena; bajo el 2 % se lee con menos pasadas.
- CÓMO REPRODUCIRLO: `python experiments/_s162_v750b/adenda2/verificador/ver_t4_separar_colision.py`. Con
  `uno/artefactos` y `dos/artefactos` quedan los ids `[2]`; con `uno/arte_a` y `dos/arte_b` (control) quedan `[0, 1, 2, 1002]`.
- CONFIANZA: CONFIRMADO el mecanismo; SOSPECHA que en el run los nombres choquen (depende de cómo se bajen).
- GRAVEDAD: 3.
- Sugerencia (no la aplico): anteponer un índice a `Path(d).name`, contar lo escrito después de escribir, o quitar
  el paso y dejar el testigo P8 como documentación.

### VAD2-02. El lector no aplica la exclusión de «K distinto de producción» del analizador sellado
- ARCHIVO:LÍNEA: `adenda2/leer_posicion_v750b.py:162-164` (`oks`) contra `analizar_v750b.py:291-298` (`k_dist` y
  `oks = [i for i in oks if i not in set(k_dist)]`); SCRIPT:SALIDA `verificador/ver_t1_consistencia_radiante_vs_sellado.py`,
  `verificador/ver_t1_salida.txt`.
- QUÉ PASA: el sellado (§7) saca de todos los brazos las pasadas donde el K del probe no reproduce a producción (tolera
  hasta 1 %). El lector arma su propio `oks` sin esa exclusión. Con 159 pasadas y una con K distinto, la fila B0 del
  sellado da `n_baja = 3` y la «radiante» del lector `n_baja = 4`; sin pasadas K-distinto las seis cajas son iguales
  (control: 6 de 6 IGUAL). Las diferencias entre brazos del lector no se distorsionan (misma población para los tres),
  pero la fila «radiante» no calza con el B0/B1 del veredicto, y la adenda no lo dice.
- CÓMO SE VE EN EL DASHBOARD: invisible (diagnóstico).
- CÓMO REPRODUCIRLO: `python experiments/_s162_v750b/adenda2/verificador/ver_t1_consistencia_radiante_vs_sellado.py`
  (caso B: «DISTINTO» en B0 a B5, columna `n_baja`).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### VAD2-03. Si el control del generador falla, quedan los archivos de la corrida anterior
- ARCHIVO:LÍNEA: `adenda2/objetivos_supl_v750b.py:95-99` y 83 (`poblacion_supl.json` se escribe antes del control);
  SCRIPT:SALIDA `C:\vrp-trabajo\temporales\v750b_ver2\gen2.log` y el listado de `gen2`.
- QUÉ PASA: el docstring y el §3 dicen «si no, sale 1 y no escribe la lista del run». Es cierto de lo que escribe, pero no
  borra lo que ya estaba. Con `--dest` apuntando a una carpeta que tiene un `objetivos_run_v750b.json` de antes (la
  carpeta por defecto es `adenda2/`, donde el §7 manda commitear), un segundo intento con control caído (por ejemplo
  `--hasta` distinto: «5803 contra 5841, DISTINTAS», rc 1) deja el `objetivos_run_v750b.json` y el
  `objetivos_supl_v750b.json` viejos junto a un `poblacion_supl.json` nuevo. Quien commitea «los archivos de la carpeta»
  despacharía una lista que no pasó el control de esa corrida.
- CÓMO SE VE: invisible hasta que el lector (C3) vea listas que no calzan, o nunca si calzan por azar.
- CÓMO REPRODUCIRLO: comandos en `verificador/NOTAS_REPRODUCCION.md` (bloque VAD2-03); logs en `verificador/logs/`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### VAD2-04. La batería y el nulo del autor son angostos: 24 de mis 30 mutaciones sobreviven
- ARCHIVO:LÍNEA: `adenda2/probar_adenda2.py` (toda), `adenda2/mutar_adenda2.py:25-48`; SCRIPT:SALIDA
  `verificador/ver_mutar.py`, `verificador/ver_mutar_salida.txt`.
- QUÉ PASA: el autor declara 13 de 13 atrapadas por aserción y su arnés es honesto (su identidad pasa y su control cae).
  Con 30 mutaciones mías (una línea cada una, mismo criterio de «atrapada = sale 1 con FALLAS»): lector, de 20, 6 atrapadas
  (M1 km por celda, M2 centro corrido, M15, M16, M19, M20) y 12 que la batería no ve (M3 ancla siempre el centro,
  M4 predicado lee otra columna, M5 sin filtro de `dayflag`, M6 sólo el canal decide, M7 P2 contra cercano, M8 «cambian»
  cuenta suplementarias, M9 y M10 (C3 sin ids o sin disjuntos), M11 pico = el más lejano, M13, M14, M18), más M12
  (equivalente: cruzar fila y columna con centro en la diagonal) y M17 (desempate, sólo importa con empates exactos).
  Separador: 0 de 3 (S2 manda la suplementaria a ninguna parte, S3 pierde el id 100000, S4 pisa una carpeta
  no vacía). Generador (`main`): 0 de 7 (G3 el control siempre IGUALES, G4 ids desde 0, G5 sin días excluidos, G6 orden
  invertido, G7 `en_sc` verdadero, G8 selecciona también `pos`, G9 la distancia sale de cualquier fila); el autor sólo
  prueba `poblacion_con_far_ref`. Identidad PASA y control CAÍDA, así que el arnés vale.
  Importa porque M3 no es cosmético: el ancla en el cráter es lo que hace que `radiante` calce con el sellado en Cordón
  Caulle y Tupungatito. El código de hoy está bien (T1b: 12 de 12 IGUAL con cráter corrido, canales decide y tabla; la
  copia M3 da 12 de 12 DISTINTO), pero la batería no lo protegería de un cambio futuro. Lo mismo
  vale para M11 (T7 comprueba que hoy pico elige el de mayor M13: COINCIDE).
- CÓMO SE VE: invisible hoy; mañana, un diagnóstico de posición silenciosamente torcido para V750-A.
- CÓMO REPRODUCIRLO: `python experiments/_s162_v750b/adenda2/verificador/ver_mutar.py` (unos 7 min). T1b con la copia
  M3: `python ver_t1b_ancla_craterdesplazado.py <ruta absoluta de _m/m05_leer_posicion_v750b.py>`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.
- Sugerencia: agregar a la batería una comparación «radiante = B0..B5 del sellado» (mi T1/T1b, ya escrita) con un cráter
  corrido, una escena con el pico más débil lejos y el más radiante cerca, y una prueba de `main` del generador con
  stubs.

### VAD2-05. La vara 3 «alertas con distancia» incluye filas OCR de antes del 2026-06-13 (A119)
- ARCHIVO:LÍNEA: `adenda2/leer_posicion_v750b.py:271-273`
  (`str(f.get("tipo", "")).startswith("ALERTA")`, sin filtrar `source` ni fecha); SCRIPT:SALIDA
  `verificador/ver_t6_vara3_ocr.py`, `verificador/ver_t6_salida.txt`.
- QUÉ PASA: A119 dice que el OCR tuvo la geometría mal calibrada hasta el 2026-06-11 y sin distancia medida hasta el
  2026-06-13, y que antes de esa fecha lo que decide es la tabla sola. La vara 3 toma la primera fila ALERTA con
  distancia, de la fuente que sea. En la población sellada de hoy (273 pasadas `pos` con distancia): 254 salen de la tabla,
  14 son OCR de antes del 2026-06-13 y 5 OCR de después (conteo propio sobre `objetivos_v750b.json` del ensayo). En la
  escena de T6, dos alertas solo-OCR con 20 km bajan «fracción a 1 km o menos» de 1,00 a 0,60 sin tocar la mediana. En
  `far_ref` no pasa: las 20 traen fila CONS y `dist_ref` es la de la tabla en las 20.
- CÓMO SE VE: V750-A leería un porcentaje de calce de distancia castigado por una referencia que sabemos defectuosa.
- CÓMO REPRODUCIRLO: `python experiments/_s162_v750b/adenda2/verificador/ver_t6_vara3_ocr.py`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### VAD2-06. El despacho no define el relanzamiento: con la lista sellada por defecto los ids suplementarios se descartan sin error
- ARCHIVO:LÍNEA: `probe_v750b.py:256-259` (filtro de `--solo` sobre la lista leída) y `probe-s162-v750b.yml:22`
  (`OBJETIVOS` por defecto = sellada); `ADENDA2_V750B.md` §7.
- QUÉ PASA: §7 dice que el único cambio es `OBJETIVOS` en la copia del workflow de la rama de disparo. El
  pre-registro §9 manda relanzar faltantes con `SOLO` «sobre el mismo tag». Si el relanzamiento usa el yml del tag (lista
  sellada) con ids ≥ 100000 en `SOLO`, el probe filtra a vacío, imprime «0 granulos, 0 pasadas», sale 0 y el job queda
  verde sin haber procesado nada (lectura del código; no corrí el probe por falta de token). Es el patrón A108 (un
  run verde no prueba cobertura). Además: la lista del run y los scripts viven en `adenda2/`, que no existe en el tag
  `s162-v750b-sellado`; el texto no dice cómo llegan a la rama de disparo.
- CÓMO SE VE: invisible; las suplementarias quedarían SIN DATO (se nombran en el lector) y alguien creería que «el
  relanzamiento ya corrió».
- CONFIANZA: SOSPECHA (lectura de código, sin ejecución). GRAVEDAD: 2.

### VAD2-07. «far_ref: publica 0» no distingue «no había alertados» de «había y no publica»
- ARCHIVO:LÍNEA: `adenda2/leer_posicion_v750b.py:251-258`.
- QUÉ PASA: la sección de pasadas lejanas cuenta cuántas publica cada brazo y lista sólo las que publican; no imprime
  cuántas de las `far_ref` observadas tienen al menos un alertado en esa caja. Si en el run real la mayoría de las 20
  no tiene ningún alertado, los tres brazos darán 0 y se leerá como «ningún brazo publica de más» cuando la escena
  nunca ocurrió (pregunta 2 del instrumento: el cero no distingue «no hay» de «no medí»). Hay un control parcial: las
  líneas de distancia (vara 3) imprimen `n` = pasadas con alertado y referencia. Sin dato real no puedo medir cuántas serán.
- CONFIANZA: SOSPECHA. GRAVEDAD: 2.

### VAD2-08. El control del generador compara sólo (volcán, hora, gránulo)
- ARCHIVO:LÍNEA: `adenda2/objetivos_supl_v750b.py:57-58` y 90-93. SCRIPT:SALIDA `C:\vrp-trabajo\temporales\v750b_ver2\g_sellada_lab_cambiada.log`.
- QUÉ PASA: una lista sellada con una pasada `neg_limpio` cambiada a `pos` protegida (misma clave) da «5841 contra 5841,
  IGUALES» y escribe todo. La docstring dice que así «se ve que las dos listas salieron de los mismos records y de la misma
  referencia»; sólo se ve que tienen las mismas claves. El efecto en la suplementaria es nulo (un cambio pos/neg moviendo la
  clave sí cae), pero la frase sobrepromete. Positivo: con una pasada de menos o con `--hasta` distinto el control sí cae
  (rc 1: «5841 contra 5840» y «5803 contra 5841»).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### VAD2-09. `--dest` igual a la carpeta sellada borraría `poblacion_completa.json` sellada
- ARCHIVO:LÍNEA: `adenda2/objetivos_supl_v750b.py:78, 81-84` (`P.AQUI = dest`; `crudo.unlink()`).
- QUÉ PASA: el script hace que 01_poblacion escriba `poblacion_completa.json` en `dest`, lo copia a
  `poblacion_supl.json` y borra el original. Con el `dest` por defecto (`adenda2/`) no toca nada sellado; con
  `--dest experiments/_s162_v750b` pisaría y borraría el `poblacion_completa.json` que el §7 manda commitear. Lectura
  de código; no lo ejecuté sobre el árbol real. CONFIANZA: CONFIRMADO por lectura. GRAVEDAD: 1.

### VAD2-10. Con las suplementarias, 301 de 1.319 gránulos sellados cambian de trozo
- SCRIPT:SALIDA cálculo propio sobre la lista del ensayo (ver `NOTAS_REPRODUCCION.md`, bloque «trozos»).
- QUÉ PASA: el reparto es `n % 32` sobre los gránulos ordenados; un gránulo nuevo (el de Isluga 100017) desplaza a los
  siguientes. Los resultados por pasada no dependen del trozo, y el reparto sigue equilibrado (41 a 42 gránulos, 135 a 218
  pasadas por trozo). Sólo afecta a quien compare logs o artefactos por trozo con un run sin la adenda. CONFIANZA:
  CONFIRMADO. GRAVEDAD: 1.

### VAD2-11. El texto dice que el SIN DATO de la suplementaria «se lista por nombre»; el sin gránulo sólo se cuenta, y las listas se cortan en 20
- ARCHIVO:LÍNEA: `adenda2/leer_posicion_v750b.py:155-156` (cuenta `len(dsg.get('pasadas'))`), 168-170 (lista los
  `sin` del run), 249 y 258 (`[:20]`); `ADENDA2_V750B.md` §4 («se lista por nombre y no frena nada»).
- QUÉ PASA: los fallos del run sí salen por nombre; las pasadas sin gránulo sólo por conteo (el nombre está en el JSON);
  las listas «por nombre» de cambios y de `far_ref` se truncan a 20 sin avisar. Hoy son 0 sin gránulo y 20 `far_ref`,
  así que no muerde. CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### VAD2-12. «Centro de la grilla (desde donde mide MIROVA)» es la celda (33, 33), no el punto de referencia
- ARCHIVO:LÍNEA: `adenda2/leer_posicion_v750b.py:277` (`A.C`); `ADENDA2_V750B.md` §4 vara 3. FUENTE: S165,
  `experiments/_s165_regla_posicion/v750_salida.txt`, líneas de procedencia («X0, Y0 ... fila 32,67 y columna 33,33 ...
  a 0,35 km o menos»), leído en `origin/loop/activo` `72928820b`.
- QUÉ PASA: hay hasta 0,35 km entre el centro de celda que usa el lector y el punto de referencia de MIROVA, y la
  `Distancia_km` de MIROVA está cuantizada a 0,75 km (D15). El umbral «a 1 km o menos» absorbe ambas cosas, pero la
  frase «desde donde mide MIROVA» es más precisa de lo que se sabe. CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### VAD2-13. Dos afirmaciones de contexto sin respaldo localizable
- ARCHIVO:LÍNEA: `ADENDA2_V750B.md` §2 («19 en VIIRS 750, `experiments/_s165_regla_posicion/INFORME.md`») y §5.
- QUÉ PASA: (a) el INFORME de S165 que leí (`origin/loop/activo` `72928820b`) da para VIIRS 750 «resto: 0 pasadas», no 19;
  la cifra no aparece ahí (la lista del generador da 20 sobre otra ventana). (b) La adenda declara qué no cubre (las
  FALSO_POSITIVO con ALERTA en la misma pasada) pero no menciona que 8 pasadas V750 `sin_geometria` (MIROVA vio calor sin
  saber dónde, V31.1) quedan fuera por construcción (conteo del propio generador: `sin_geometria: 8`). CONFIANZA: (a)
  SOSPECHA, (b) CONFIRMADO. GRAVEDAD: 1.

## SEGUIMIENTOS (no son defectos de la adenda)
- El lector imprime números aunque la compuerta del veredicto sellado esté cerrada o la cobertura sea insuficiente; es
  diagnóstico, pero conviene que quien lo lea sepa primero el estado de la compuerta (el orden de §8 ya lo implica).
- `01_poblacion.py` (en `origin/main`) escribe `"data_records": "origin/main 533398f8f"` fijo en el meta de
  `poblacion_completa.json` y de `poblacion_supl.json`, aunque los records sean de otro commit. Lo heredan los archivos
  que el §7 manda commitear.
- «Lo correcto es no publicar» en `far_ref` es una premisa de la réplica de MIROVA (A115). En el perfil `experimental` la
  lectura sería la contraria (A54: un alertado junto al cráter es una señal real no publicada). Conviene que V750-A lo
  diga si usa la vara 2.
- Hipótesis de S165 sobre cómo ubica MIROVA el punto (el más radiante dentro de su límite y, si no hay, FP) sigue SIN
  VERIFICAR; la vara 3 de esta adenda no la zanja con 20 pasadas, y los tres brazos nunca tendrán «posición» de MIROVA
  (A93).
- La batería del autor crea y borra `experiments/_s162_v750b/_p7_analizar_otro.py` dentro de una carpeta sellada
  mientras corre; si se mata el proceso a mitad queda residuo.

## VERIFICADO LIMPIO (cada ítem con la vara contra la que lo comprobé)
1. **Batería 18 de 18 reproducida**: `python experiments/_s162_v750b/adenda2/probar_adenda2.py --evaluador <evaluar_d25.py
   sha 2e557697...>` → «TODOS LOS ESCENARIOS COMO SE ESPERA (18)». Vara: su `probar_adenda2_salida.txt`; diff idéntico salvo
   la ruta temporal (`verificador/bateria_autor_corrida_verificador.txt`).
2. **Ensayo del generador reproducido sobre el árbol `bd711db63`** (`C:\vrp-trabajo\temporales\v750b_supl_ensayo`,
   `--hasta 2026-10-26`): control «5841 contra 5841, IGUALES», 20 `far_ref` con gránulo, 0 sin gránulo; `objetivos_supl`
   byte a byte igual al del ensayo (sha `ef76b26b...f0fe`) aunque el consolidado remoto pasó de `e68617b5` a `416d540e`
   (la población no cambió). Vara: §6 de la adenda.
3. **Cifras del §6**: Lastarria 5, Tupungatito 4, Chillán 3, Láscar 2, Planchón-Peteroa 2, Isluga 2, Llaima 1, Villarrica 1;
   distancias 6,41 a 29,56 km; 6 antes del 2026-06-13; 20 filas FALSO_POSITIVO de la tabla y 1 con OCR además; `pub_prod`
   = 0 en las 20; 20/5.841 = 0,34 %. Vara: `objetivos_supl_v750b.json` del ensayo, conteos míos.
4. **Lista del run**: `run[:5841] == sellada`, `run[5841:] == suplementaria`, 5.861 ids únicos, orden interno de cada
   gránulo sellado conservado (el `objs[0]` que fija `PG.LATLON` es el mismo). Vara: lectura de `probe_v750b.py:260-266`
   y cálculo propio. 19 de 20 suplementarias comparten gránulo con pasadas selladas, 1 gránulo nuevo: el costo de bajada
   es ~0.
5. **Brazo K sin estado entre pasadas**: `guardar_como_store` usa una carpeta temporal nueva por llamada
   (`experiments/_s159/n/probe_n.py:202-225`), así que agregar pasadas al run no puede cambiar el K de las otras.
6. **Lector = analizador sellado en «radiante»**: T1 (cráter centrado, sin K-distinto) 6 de 6 cajas IGUAL; T1b (cráter
   corrido a (33; 28,5), escena que cambia de clase según el ancla, canales decide y tabla) 12 de 12 IGUAL, con
   control positivo (la copia M3 da 12 de 12 DISTINTO) y con P1 de B1 = 1 como se esperaba.
7. **Identidad del analizador**: sha256 con LF del archivo del worktree = el del tag `s162-v750b-sellado` =
   `83b7159bd0666871b2e88a48c23feba4900ae28c24abd76b6cb3abf7b2593392`; el worktree tiene 533 CRLF y el lector normaliza.
   `evaluar_d25.py` sha `2e5576973ef1...`. Vara: `git show s162-v750b-sellado:...` y `sha256sum`.
8. **Extracción con `ast`**: el texto literal de `prot_tabla`, `etiqueta`, `ventana`, `metricas` y `p2` ejecutado en el
   lector reproduce las métricas del analizador sellado (punto 6) y `p2` recibe `ref` correcto.
9. **Brazos «cercano» y «pico»**: T7, escena de 9 píxeles con el más radiante en el extremo cercano: radiante calla,
   cercano y pico publican; con el más radiante en el extremo lejano, pico calla. COINCIDE.
10. **Robustez**: T5, seis variantes (suplementarias sin resultado, caja `None`, caja `{}`, volcán fuera del gránulo,
    error): sin traceback, rc 0, SIN DATO por nombre cuando corresponde. **Escala**: T8, 5.841 + 20 pasadas con cúmulos de 0
    a 40 píxeles: 11 s, controles en verde.
11. **Cadena sellada ciega a lo ajeno**: `analizar_v750b.py:203-209` y `adenda1/cobertura_cajas_v750b.py:64-73` iteran `obj`; los
    resultados con ids que no están en la lista sellada sólo suben la cuenta de «con resultado».
12. **Control del generador sí cae donde debe**: con una pasada de menos y con `--hasta` distinto sale 1 y no escribe
    `objetivos_run` ni `sin_granulo_supl` (la salvedad es VAD2-03).
13. **Formato**: el conteo de guiones largos y de guiones medios da 0 en los ocho archivos de la adenda (grep por esos dos caracteres); sin voseo.
14. **Sin edición ajena**: `git status --short` sólo muestra `?? .../adenda2/verificador/`.

## SIN DATO
- Comportamiento real del probe con ids ≥ 100000 y con las 20 pasadas (no hay token ni red a LAADS; no corrí el probe).
  Lo único que leí fue el código: formatea `grilla_{id:05d}.npz` (acepta 6 dígitos) y agrupa por gránulo.
- Cuántas de las 20 `far_ref` tendrán algún alertado en las cajas (VAD2-07): sólo se sabe con el run.
- Re-ejecución de `mutar_adenda2.py` del autor (crea copias dentro de `adenda2/`); su resultado «13 de 13» queda como lo
  informa; mis seis mutaciones atrapadas coinciden en el sentido con las suyas, no es una re-ejecución.
- Linux y el runner de GitHub: todo lo mío corrió en Windows.
- La rama de disparo `s162-v750b-disparo` y cómo llegan a ella la lista del run y los scripts (VAD2-06).
- La cifra «19 en VIIRS 750» de S165 (VAD2-13).

## Archivos de este verificador (rutas absolutas)
Carpeta: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-2-918174\experiments\_s162_v750b\adenda2\verificador\`
(`LISTA_CAMINOS_previa.md`, `ver_comun.py`, `ver_t1*`, `ver_t4*`, `ver_t5*`, `ver_t6*`, `ver_t7*`, `ver_t8*`, `ver_mutar.py`,
`ver_mutar_salida.txt`, `_m/` con las copias mutadas, `NOTAS_REPRODUCCION.md`). Temporales: `C:\vrp-trabajo\temporales\v750b_ver2\`.
