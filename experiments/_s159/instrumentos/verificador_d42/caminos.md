# Caminos por los que cada afirmacion podria estar mal (escrito ANTES de abrir ningun archivo citado)

Verificador D-42. Worktree C:\vrp-trabajo\s159-evaluador, commit b57ecfe62 (arbol limpio, `git status --short` vacio).
Hora del servidor al empezar: Thu, 22 Oct 2026 12:46:44 GMT (header `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`).
Lo unico que mire antes de escribir esto: `git diff --stat 5f986a209 b57ecfe62` (nombres de archivos) y `ls` de las carpetas. Ningun contenido.
No leo experiments/_s159/instrumentos/calib_p2/README.md (es el informe del implementador) ni los informes de verificador_d34 / verificador_d29, salvo para saber que mutaciones pidieron V34-03 y V29-01.

## Afirmacion 1: calibracion de P2 sigue la adenda §2

- La adenda dice otra cosa que lo que el titulo resume: leer la adenda ENTERA antes del codigo (la vara puede pedir un bloque distinto a «noche-volcan», o un tope distinto a 5 %, o un numero de sorteos distinto a 1.000, o una semilla distinta a 161).
- El bloque del sorteo no es «noche-volcan entero»: el codigo podria sortear el signo por pasada, por sensor, por noche sin volcan, o por volcan sin noche; o definir «noche» con una frontera UTC distinta a la de PREREGISTRO (la noche local cruza medianoche UTC).
- El bloque se arma con una clave que no es la misma que usa decidir_p2_bloques para contar noches discordantes: entonces el sorteo permuta otra unidad que la que decide.
- La regla de intervalo «la misma de ADENDA_GEMELO §5.3 y §5.4» puede ser una copia en linea que diverge de la funcion que usa P2 sin calibrar (A102): dos copias de la misma logica; mutar una no mueve la otra.
- 1.000 sorteos: la constante podria vivir en un argumento con default distinto, o el bucle correr 999 o 1.001 (off-by-one), o el sorteo 0 ser el observado (incluido en el conteo).
- Semilla 161 = SEMILLA + 4: SEMILLA podria no valer 157 hoy; la semilla podria compartirse con el intervalo (el RNG del intervalo avanzaria el del sorteo y el resultado dependeria del orden de llamada); o la semilla podria derivarse por sensor/volcan y no ser la unica.
- Tope de 5 % por cola por separado: el codigo podria sumar las colas (10 %), o usar `<` en vez de `<=` en la frontera, o contar la fraccion de GANA sobre los sorteos que decidieron en vez de sobre los 1.000, o calibrar solo la cola observada.
- INDECIDIBLE si falla: podria dejar el resultado sin calibrar (el no calibrado se cuela), o no informar el sin calibrar en el JSON.
- BLOQUEA sin calibrar con su fraccion informada: podria calibrarse igual (el bloqueo cambiaria de significado), o la fraccion no quedar en el JSON.
- «todo en el detalle de P2 del JSON»: claves podrian faltar, o quedar en otro nivel del JSON, o quedar solo en el log.
- Quien llama: podria haber dos llamadores (por sensor, combinar, repeticion) y uno sin calibrar.
- El flag o parametro de calibracion podria leerse de un sitio distinto del que creo (A89): argumento CLI, constante, variable de entorno.

## Afirmacion 2: corre solo despues del SIN SUSTRATO y con controles OK; lo que no corre deja None con nota

- El orden en el codigo puede ser el inverso (calibrar antes del SIN SUSTRATO) o la calibracion correr siempre y luego descartarse (gasta el RNG igual, pero ademas podria filtrar algo al JSON).
- «controles OK» puede ser un subconjunto de los controles (gemelo, placebo, D-29) y no todos; o mirar un control que no existe en este evaluador.
- «None con nota»: podria quedar `None` sin nota, o nota sin None (campo con valor viejo), o una cadena vacia; o el JSON podria no serializar None de la forma esperada.
- La prueba que lo verifica podria no cubrir el caso SIN SUSTRATO en un sensor y OK en el otro.

## Afirmacion 3: estrato 203 solo informa, solo VIIRS 750, tabla y totales de la nota

- «solo informa»: una variable compartida podria filtrar al conteo de P1/P1b/P2/M (por ejemplo, si el estrato se calcula sobre la misma lista y la modifica en sitio).
- «solo VIIRS 750»: el filtro de sensor podria usar una subcadena (A92: `VIIRS` contiene a `VIIRS_SNPP` I-band; `_750` como sufijo) o una lista que incluya NOAA-21 o deje fuera a uno.
- La tabla de la nota podria tener columnas/estratos que el codigo no produce, o al reves; los totales podrian no cuadrar con la suma de las filas.
- Podria entrar a `global_ventana` o `combinar` por una via indirecta (una clave del JSON que `combinar` lee generica, por ejemplo recorriendo todas las claves).
- La nota (NOTA_ESTRATO_203.md) podria definir «cumbre» o «0,0 MW» con un predicado distinto al que implementa el codigo (igualdad exacta vs `<= 0`, `pc.vrp_mw` vs `f5_core_vrp_mw`, A10).

## Afirmacion 4: 28 de 28 mutaciones atrapadas por asercion, control verde leido de JUnit

- «atrapada por asercion» vs «atrapada por caida» (S152, regla general): una mutacion que hace explotar el codigo (TypeError, KeyError) se cuenta como atrapada aunque ninguna asercion la mire. Hay que leer el JUnit: `<failure>` (asercion) vs `<error>` (caida).
- El control verde podria estar leido de otro JUnit (de otra corrida o de otro arbol), o el mutador podria restaurar el archivo mal y el control correr sobre una copia mutada.
- El conteo 7 + 5 + 13 + 3 = 28: podria haber mutaciones duplicadas (la misma edicion con dos nombres) o mutaciones que no cambian el codigo (el `replace` no encuentra la cadena y la copia queda igual; entonces el test que falla no esta midiendo la mutacion). Comprobar que cada mutacion cambia el sha del archivo.
- La copia mutada podria no ser la que importan las pruebas (las pruebas importan `experiments/_s157_prereg_d25/evaluar_d25.py` por ruta; si el mutador muta otra copia, las pruebas corren sobre el original).
- El mutador podria correr las pruebas con `-x` o con un subconjunto (`-k`) que cambia entre mutaciones.
- Las mutaciones de V34-03 y V29-01 podrian no ser las que esos verificadores pidieron.

## Afirmacion 5: 24 de 37 nuevas rojas contra 5f986a209, verdes despues, probar 31/31, suite 2.415

- «rojas por asercion» contra 5f986a209: en ese commit las funciones nuevas no existen, asi que lo esperable es `AttributeError`/`ImportError` (caida), no asercion. Leer rojo_calib_p2.xml y contar `<failure>` vs `<error>`.
- Las 13 que no estan rojas: ¿son pruebas que pasan tambien en el arbol viejo? Entonces no miden el cambio (A116). ¿Cuales son y por que?
- La suite 2.415: ¿arbol quieto (A112)? Mirar sha_antes/sha_despues y status_antes/status_despues; ¿cuentan pruebas saltadas (`skipped`) como verdes?
- probar_evaluar_d25 31 de 31: podria ser un script que cuenta sus propios casos; mirar que corre sobre el evaluador de hoy y no sobre `_congelado_v1`.

## Afirmacion 6: falsos y poder con sinteticos

- «falsos por cola de 3,52 % o menos en recorridos exactos»: el enumerador exacto podria recorrer un espacio distinto (signos sin considerar la regla de intervalo; o no incluir los empates; o usar un alfa que no es el del evaluador).
- Por muestreo A, B7, B8 dan 5,4 a 6,6 % en PIERDE: el exceso sobre 5 % puede ser (a) ruido de muestreo (con n repeticiones, el IC del 5 % es ±2·sqrt(0,05·0,95/n)); (b) del generador (el sintetico «nulo» no es simetrico: por ejemplo, el generador mete una asimetria en la cola de PIERDE al redondear, o al empatar); (c) real: la calibracion es anticonservadora porque los bloques no son intercambiables (tamanos distintos de bloque), o porque el tope se aplica a cada cola con los mismos 1.000 sorteos y en ambas colas (prueba de dos colas con 5 % cada una = 10 % total, y en una sola cola la tasa de falsos con un valor-p discreto puede superar 5 % por la discretizacion).
- El estimador de la tasa de falsos podria contar INDECIDIBLE en el denominador o no.
- Poder C 98,8 %, C2 99,8 %, D 68 %, E 33 %: con cuantas repeticiones; el IC. Y el poder podria medirse contra la regla sin calibrar por error.
- «con 4 noches discordantes o menos, P2 nunca decide»: con 4 bloques hay 2^4 = 16 signos; el minimo valor-p a una cola es 1/16 = 6,25 % > 5 %: deberia ser exacto, no empirico. Verificar que 5 bloques (1/32 = 3,1 %) SI puede decidir.

## Afirmacion 7: placebo del 1 %

- Los «brazos desde produccion»: ¿lee data/mirova_equivalent/*.json del worktree (que puede estar atrasado respecto a main) o del remoto?
- El placebo apaga el 1 % de publicaciones «al azar»: si apaga solo en D, entonces D pierde publicaciones respecto a K y lo esperable es PIERDE o INDECIDIBLE, nunca GANA. «GANA en 0 de 20» es trivial en ese diseno (no es control de falsos positivos de GANA, es control de direccion). La pregunta valiosa es cuantas dan PIERDE con 1 %: si P2 da PIERDE con 1 % apagado, es sensible; si da INDECIDIBLE siempre, la calibracion es ciega al 1 %.
- 20 semillas: con 20 repeticiones el IC de 0/20 llega a 14 % (regla de 3 ≈ 3/20). «0 de 20» no excluye una tasa de falsos del 5 %.
- La ventana V1/V2 de los records podria no ser la del A/B real (eso esta bien, pero hay que declararla).
- El placebo podria usar el predicado «publica» de otra via que la del evaluador (reimplementacion en Python en vez del node de A97).

## Afirmacion 8: §2.5 y global_ventana

- Leer el texto de §2.5 entero y la regla vigente de global_ventana en PREREGISTRO/ADENDA_GEMELO; ver el orden de precedencia en el codigo (VETADO > PIERDE > INDECIDIBLE > GANA? o VETADO > INDECIDIBLE > ...).
- Caso concreto: P2 INDECIDIBLE en V375 y PIERDE calibrado en V750 -> ¿NO CUMPLE o INDECIDIBLE? Hay que construirlo con sinteticos y ver que da el codigo.
- Lo que «hoy con un M INDECIDIBLE» hace: si M INDECIDIBLE en un sensor y PIERDE en el otro da NO CUMPLE hoy, entonces «como hoy» admite la lectura del implementador. Verificar en el codigo que hace hoy con M.

## Tareas propias

- Tasa de falsos de A, B7, B8 por otro camino: (i) mas repeticiones con otras semillas; (ii) calculo exacto cuando el numero de bloques lo permite (2^n sorteos enumerados); (iii) separar «generador» de «estimador» corriendo el mismo generador con la regla sin calibrar y con un test exacto de signos de referencia.
- Mutaciones propias: sorteo por pasada en vez de por bloque; una cola sola; tope en la suma de las colas; semilla compartida con el intervalo; calibracion antes del SIN SUSTRATO; off-by-one en 1.000; `<` por `<=` en el tope; fraccion sobre los decididos en vez de sobre los sorteos.

## Riesgos del propio instrumento

- Mis copias para mutar deben vivir en experiments/<carpeta propia>/evaluar_d25.py y el archivo calcula la raiz como AQUI.parents[1]; si el import de las pruebas resuelve por ruta fija, mis mutaciones no las ven: medir con un control (una mutacion que seguro rompe) antes de creer un «atrapada».
- No correr nada con --raiz/--logs/--repeticion/--combinar sobre datos reales; no abrir D:\vrp-trabajo\temporales\s157d25 ni s158*.
- Las pruebas pueden correr con el arbol en movimiento si lanzo pytest en segundo plano mientras edito copias (A112): correr en primer plano o no tocar nada mientras corre.

---
sha256 (antes de esta linea): cbce2b1d673b228d8eaaf7ca20796eb86b019914fc115284184b0111e83627b5
Hora del servidor al cerrar caminos.md: Date: Thu, 22 Oct 2026 12:48:09 GMT
