# Verificador con contexto limpio del candado de la adenda K, segunda vuelta

Commit verificado: `5b07733376031a0292af5f487c9e6620976e6efc` (`commit.txt`), mismo contenido que `main` en
`cf272543c` (PR #858): `git diff --stat 5b0773337 origin/main -- experiments/_s151_ab_diurno/` sale vacío. Regla
contra la que se mide: `experiments/_s151_ab_diurno/ADENDA_K.md` (sellada v2, opción A de §3.1, opción i de §3.2,
candado de §4). No modifiqué código ni pruebas. Todo lo que cito salió de una corrida de esta sesión y vive en esta
carpeta. La sesión se cortó una vez por un reinicio del PC; reconstruí el estado desde los archivos y repetí sólo la
corrida que había quedado incompleta (`m1_completa_salida.txt`). Las copias mutadas `experiments/_vk2_*` no quedaron
(`ls -d experiments/_vk2_*`: «No such file or directory», comprobado después del reinicio y al final).

## Veredicto corto

La corrección del commit `5b0773337` cierra lo que encontró el primer verificador: las cuatro mutaciones de H-1 y las
de H-2 y H-3 ahora caen por una prueba, no por una caída. El evaluador, sobre los datos reales de C0, sigue dando lo
mismo que antes con las dos bases. Quedan dos huecos de prueba que importan para el despacho real: **ninguna prueba
distingue la regla que decide de la que sólo se rotula** (N-1, gravedad 3), y **H2a se prueba con una sola raíz, un
solo volcán y el brazo diurno**, mientras el A/B real corre con diez raíces y once volcanes (N-2, gravedad 3). Ninguno
cambia el resultado de un despacho hecho hoy con el código de hoy: son regresiones futuras que pasarían en verde.

## Comandos y salidas

| qué | comando | salida |
|---|---|---|
| batería completa, árbol quieto | `python experiments/_s151_ab_diurno/probar_evaluar_diurno.py` | `arnes_completo_salida.txt`: «AUTOPRUEBA: 107 de 107 comprobaciones OK», rc=0, 01:27:11 a 01:39:49 UTC |
| 42 mutaciones con `PROBAR_SOLO=1,3,k` | `HILOS=5 python m1_mutaciones_v2.py` | `m1_salida.txt` (control «ninguna»: sólo falla el artefacto conocido `cobertura_workflow`) |
| 5 mutaciones con la batería completa | `SOLO="" HILOS=5 python m1_mutaciones_v2.py g1_regla_inversa h2a_solo_primera_raiz h2a_solo_lascar h2a_solo_diurno veredicto_w2_antes_de_g3` | `m1_completa_salida.txt` |
| estado de `ED.REGLA` entre las comprobaciones rápidas | `python m2_fuga_regla.py` | `m2_fuga_regla_salida.txt` |
| bordes del CLI sobre W6a real | ver encabezados `###` del archivo | `m3_bordes_cli_salida.txt` |
| ¿cuándo discrepan la cola exacta y el p95 muestreado? | `python m4_reglas_discrepan.py` | `m4_reglas_discrepan_salida.txt` |
| evaluador real, 10 raíces de C0, base por defecto | `python -I evaluar_diurno.py --raiz <W2a> ... --raiz <W6b> --repetidas W2,W3,W5,W6` | `real_c0_salida.txt` |
| ídem con `--brazos <C0> --base k --sha-codigo eb97779f...` | | `real_basek_salida.txt` |

Método de las mutaciones (`m1_mutaciones_v2.py`): por cada una se copian los `.py` y `.json` de primer nivel de
`_s151_ab_diurno` a `experiments/_vk2_<nombre>/` (mismo nivel, para que el evaluador ubique el repo por la profundidad
de su carpeta), se aplica UN reemplazo de texto que tiene que aparecer exactamente una vez (comprobado para las 42) y
se corre el `probar_evaluar_diurno.py` de la copia. ATRAPADA (prueba) = alguna comprobación distinta de
`cobertura_workflow` falla; ATRAPADA (caída) = el arnés no llega a la línea AUTOPRUEBA; NO ATRAPADA = sólo falla el
artefacto. A diferencia del script del primer verificador, éste corre también los casos de punta a punta k1 a k5 y el
caso 21. La batería larga con `PROBAR_SOLO=1,3,k` incluye los casos 1, 3, 11, 12, 13, 14 y 21.

## Resultado de las mutaciones

**Las 15 del primer verificador**: 13 ATRAPADAS por prueba, 2 NO ATRAPADAS (`h2a_solo_primera_raiz`,
`h2a_solo_lascar`, ver N-2). Las ocho que el primer verificador reportó no atrapadas y que H-1 a H-3 cubrían
(`conservadora_en_g1`, `xobs_menos_1`, `k_sin_w2`, `control_siempre_ok`, `w2_sin_mirar_g1b`,
`h2a_apagado_en_evaluar`, `sha_opcional`, `h2a_solo_control`) caen todas por una prueba con nombre, no por caída.

**Las 27 nuevas**: con `PROBAR_SOLO=1,3,k`, 16 ATRAPADAS por prueba, 1 por caída (`k_sin_flag_b22`), 10 NO ATRAPADAS; una de esas 10 (`veredicto_w2_antes_de_g3`) cae con la batería completa.

Total de esta vuelta, 42: **30 por prueba, 1 por caída, 11 NO ATRAPADAS** (con 1,3,k eran 29, 1 y 12). Las 11, con la batería que las corrió:

| mutación | qué hace | batería | gravedad |
|---|---|---|---|
| `g1_regla_inversa` | con base k decide con el p95 muestreado y con c0 con la cola exacta; el rótulo `regla` sigue diciendo «cola exacta» | **completa**, 107 de 107 | 3 (N-1) |
| `h2a_solo_primera_raiz` | H2a mira sólo la primera `--raiz` | **completa**, 107 de 107 | 3 (N-2) |
| `h2a_solo_lascar` | H2a mira sólo `Lascar.json` | **completa**, 107 de 107 | 3 (N-2) |
| `h2a_solo_diurno` | H2a mira sólo el brazo diurno | **completa**, 107 de 107 | 2 (N-2) |
| `g1_siempre_cola` | la cola exacta decide también con c0 | 1,3,k | 1 (N-3) |
| `xobs_floor` | `int(m1*npos)` en vez de `round` | 1,3,k | 2 (N-4) |
| `alfa_g1_le` | `<=` en vez de `<` en G1 | 1,3,k | 1 |
| `alfa_g1_0055` | alfa 0,055 en G1 | 1,3,k | 1 |
| `control_sin_b` | el control del nulo ignora su parte (b), el brazo perfecto | 1,3,k | 1 |
| `w2_con_sin_sustrato` | la regla W2 decide también si W3 a W6 da SIN SUSTRATO | 1,3,k | 1 |
| `h2a_sha_prefijo7` | H2a compara sólo 7 caracteres del sha | 1,3,k | 1 |

`veredicto_w2_antes_de_g3` (mal nombrada: apaga el chequeo de G3 en `veredicto`) salió NO ATRAPADA con 1,3,k y
**ATRAPADA con la batería completa** (7 casos de G3 fallan). No cuenta como hueco: es del pre-registro original y sus
casos están fuera del filtro. `k_sin_flag_b22` cae por un `KeyError` dentro de la propia prueba
(`probar_evaluar_diurno.py:294`): se ve, el arnés sale con traza, pero no es una prueba que la nombre.

## Estado de H-1 a H-5

- **H-1 (sin punta a punta con `--base k`): CERRADO.** `chequear_punta_a_punta_k` (`probar_evaluar_diurno.py:491`)
  corre `evaluar()` con `--brazos K --base k --sha-codigo` sobre el universo real (k1 a k5), y
  `chequear_regla_w2` (`:427`) arma la regla con `configurar_brazos` (`:439`). Las cuatro mutaciones de H-1 caen por prueba
  (`m1_salida.txt`: `k_sin_w2` por `regla_w2`, `w2_sin_mirar_g1b` por `regla_w2` y `punta_a_punta_k`,
  `h2a_apagado_en_evaluar` y `sha_opcional` por `punta_a_punta_k`). Lo que la punta a punta no cubre está en N-2.
- **H-2 (d y e de §3.1): CERRADO**, con margen estrecho en (e). (d): «colas del muestreo (200000) dentro de 4 errores
  estándar de las exactas en todos los x (peor 0.47)». (e): «con el nulo exacto corrido en +1 el control FALLA: 0.007
  contra 0.023 exacto (± 0.014)» (`arnes_completo_salida.txt:1810`); la diferencia, 0,016, supera la tolerancia por
  0,002. Aun así `control_tol_x5` (tolerancia ×5) cae, porque lo atrapa otra pieza; la tolerancia en sí no está
  defendida más allá de ×1. `control_siempre_ok`, `control_xcrit_ultimo`, `control_colas_gt`, `control_solo_b`,
  `control_exacto_apagado` y `cola_en_c0` caen por prueba.
- **H-3 (empate sólo en una dirección): CERRADO para x_obs y la cola**, ABIERTO para la regla. La prueba nueva fija
  `x_obs` y el valor exacto de la cola (`probar_evaluar_diurno.py:392-393`), así que `conservadora_en_g1` y `xobs_menos_1` caen. Pero el empate
  sigue en el borde del soporte (x = 3 = máximo) y **ahí las dos reglas dan lo mismo**: «empate del arnés
  [(4,2,2),(6,1,2)] x=3: cola exacta FALLA | p95 muestreado FALLA» (`m4_reglas_discrepan_salida.txt`). Es la raíz de N-1.
- **H-4 (`--base c0` con brazos K; `--brazos ""`): CERRADO en su primera mitad, ABIERTO en la segunda (gravedad 1).**
  `--base c0` con brazos K se niega (`evaluar_diurno.py:99-102`; prueba k5; mutación `h2b_c0_con_brazos_k` cae), también
  con tabulador (`m3_bordes_cli_salida.txt`, caso D). Con `--brazos "" --base k --sha-codigo ...` el bloque de
  `evaluar_diurno.py:935` se salta entero: no hay `[brazos]`, decide el «p95 muestreado» con la regla W2 vieja y sólo
  corre H2a (caso A: «decide: p95 muestreado», «INDECIDIBLE (records ... (H2a))»). Sobre raíces K los directorios C0 no
  existen y el resultado sería INCOMPLETO o PENDIENTE (razonado de `cargar_brazo`; no lo corrí sobre raíces K: SOSPECHA),
  así que falla fuerte, no en silencio.
- **H-5 (detalles): sin cambios, siguen abiertos, gravedad 1.** El procedimiento `git rev-parse <tag>^{commit}` no está
  escrito en ningún lado (`grep -rn "rev-parse\|\^{commit}"` en `ADENDA_K.md`, `PREREGISTRO.md` y el workflow:
  nada). Un sha abreviado sí sale ROTO sobre records reales (`m3_bordes_cli_salida.txt`, caso E2: «79 records con
  codigo_sha distinto del tag»). La línea final sigue diciendo «VEREDICTO (§6, regla original)» con base k
  (`evaluar_diurno.py:1104`).

## Hallazgos nuevos

### N-1. Ninguna prueba distingue la regla que decide de la regla que se rotula
- Dónde: `evaluar_diurno.py:621` (`cumple = (p_cola < ALFA_G2) if REGLA["cola_exacta"] else (d > p95 + EPS_D)`) y
  `:625` (el rótulo `regla` sale de `REGLA`, no de la cuenta). Pruebas: `probar_evaluar_diurno.py:385-393` (empate) y k1
  (que mira `res["G1_W2W6"]["regla"] == "cola exacta"`).
- Qué pasa: si se intercambian las dos ramas, con `--base k` G1 decide con el p95 muestreado y el rótulo sigue
  diciendo «cola exacta». Los dos casos que deberían verlo no pueden: el empate del arnés está en el borde del soporte,
  donde las dos reglas coinciden, y k1 y k2 están lejos del umbral (P = 1,6e-63 y P > 0,05).
- Cómo se ve: `g1_regla_inversa` NO ATRAPADA con la batería completa, 107 de 107 (`m1_completa_salida.txt`). Y no es un
  caso de laboratorio: en 800 casos sintéticos puestos en el borde del valor crítico, **8 dan veredicto distinto**
  según la regla, en las dos direcciones, por ejemplo «estratos [(102, 6, 30), (66, 10, 4), (95, 5, 26), (43, 8, 4)]
  x=8 | cola exacta FALLA (P=0.0507) | p95 muestreado CUMPLE» (`m4_reglas_discrepan_salida.txt`). Es exactamente la
  situación que motivó la opción A (W3 a W6 sobre C0, D en un salto del nulo).
- Consecuencia si regresa: el A/B sobre K decidiría con la regla que Nicolás no selló, cerca del umbral, con la salida
  diciendo lo contrario. Con el código de hoy no pasa: sobre C0 la línea dice «decide: cola exacta» y la cola es
  0,5223 y 0,1058, igual que el primer verificador (`real_basek_salida.txt`).
- Reproducir: `SOLO="" python m1_mutaciones_v2.py g1_regla_inversa`; `python m4_reglas_discrepan.py`. Arreglo que
  sugeriría (no lo hice): un caso de prueba de los que lista `m4`, con veredicto esperado distinto en c0 y en k.
- Confianza alta. Gravedad **3**.

### N-2. H2a se prueba con una raíz, un volcán y un brazo
- Dónde: `evaluar_diurno.py:120-125`; pruebas `probar_evaluar_diurno.py:451-488` (`chequear_h2a_h2b`, una raíz, sólo
  `Lascar.json`, los dos brazos iguales) y `:522-523` (k3 toca sólo `por["diurno"]["Lascar"][0]`; k4 cambia el sha de
  todos los records).
- Qué pasa: el A/B real corre con diez raíces (W2a a W6b) y once volcanes. Una H2a que mire sólo la primera raíz, sólo
  Láscar o sólo el brazo diurno pasa toda la batería. El caso que H2a existe para atrapar es justo un job repetido desde
  otra referencia y unido en una raíz que no es la primera, o un Test 1 en otro volcán.
- Cómo se ve: `h2a_solo_primera_raiz`, `h2a_solo_lascar` y `h2a_solo_diurno` NO ATRAPADAS con la batería completa,
  107 de 107 (`m1_completa_salida.txt`). Además, k3 marca como Test 1 el primer record de Láscar, que es **nocturno**: el
  caso sale INDECIDIBLE también por G3, así que con H2a apagada el veredicto sigue siendo INDECIDIBLE y sólo la
  exigencia de «H2a» en el texto lo distingue (`m1_salida.txt`, `h2a_apagado_en_evaluar`: «INDECIDIBLE (G3: FALLA ...»).
- Atenuante: el código de hoy sí recorre todas las raíces, los dos brazos y todos los `*.json`; sobre las 10 raíces de
  C0 ve el Test 1 y los otros commits en varios volcanes (`real_basek_salida.txt`: «_s151_ab_diurno_control/Chaiten: 47
  records con el Test 1; ... 114 records con codigo_sha distinto del tag»).
- Reproducir: `SOLO="" python m1_mutaciones_v2.py h2a_solo_primera_raiz h2a_solo_lascar h2a_solo_diurno`.
- Confianza alta. Gravedad **3** (raíz y volcán), **2** (brazo).

### N-3. Las comprobaciones rápidas dejan `ED.REGLA` en base k, y la prueba «con base c0» corre con la regla k
- Dónde: `probar_evaluar_diurno.py:291` (`chequear_base_k` llama `configurar_brazos(..., "k")`) y su `finally` (`:313`),
  que restaura `BRAZOS` y `DECLARADO` pero no `REGLA`; la comprobación de `:424`.
- Cómo se ve: «tras chequear_base_k REGLA = {'cola_exacta': True, 'w2_decide_nicolas': True}» y «g1 en el punto de la
  comprobación «base c0»: regla = cola exacta» (`m2_fuga_regla_salida.txt`). La prueba dice que comprueba c0 y comprueba
  k; sólo pide que existan las claves, así que pasa igual. `g1_siempre_cola` (la cola decide también con c0) NO ATRAPADA.
  La batería larga no se contamina: cada `evaluar()` vuelve a llamar `configurar_brazos` (las 107 pasan).
- Consecuencia: sólo la reproducibilidad de la corrida sobre C0; sobre C0 las dos reglas dan NO ADOPTAR.
- Reproducir: `python m2_fuga_regla.py`. Confianza alta. Gravedad **1**.

### N-4. `x_obs` por truncamiento no lo vería nadie
- Dónde: `evaluar_diurno.py:615`. Hoy usa `round` y está bien. Si alguien lo cambiara por `int(m1 * npos)`, el número
  cambia en 3.258 de los pares (x, n) con n < 400 (por ejemplo 15 de 22), porque `x/n*n` no da el entero exacto
  (cuenta propia, `python -c` en esta sesión). Es conservador (baja x_obs). `xobs_floor` NO ATRAPADA con 1,3,k.
- Confianza alta. Gravedad **2**.

### N-5. H2a da OK sobre cero records
- Dónde: `evaluar_diurno.py:120-131`: si los directorios de los brazos no existen en una raíz, `glob` no devuelve nada y
  no se informa ningún problema.
- Cómo se ve: brazos K sobre la raíz W6a de C0 (donde no hay directorios K): «records de los dos brazos sin Test 1 y
  con codigo_sha eb97779f4c0e (adenda K §4 H2a): OK» (`m3_bordes_cli_salida.txt`, caso C). El veredicto sale igual
  INDECIDIBLE (controles del nulo sin sustrato), y una raíz sin brazos deja pasadas sin procesar que la cobertura
  manda a repetir, así que no termina en un veredicto falso. Pero la línea de H2a no dice cuántos records leyó, y un
  OK sobre nada se ve igual que un OK sobre todo.
- Confianza alta. Gravedad **1**.

## VERIFICADO LIMPIO

- **Batería completa en árbol quieto**: 107 de 107, rc 0, 12 min 38 s. Mientras corría sólo escribí en esta carpeta
  (que el arnés no lee) y corrí `m2_fuga_regla.py` con `PYTHONDONTWRITEBYTECODE=1`, que importa el arnés sin escribir.
- **Los casos de punta a punta k1 a k5** (`arnes_completo_salida.txt:1828-1834`): ADOPTAR con cola exacta y P =
  1,6e-63; H2a OK sobre records limpios; NO ADOPTAR con un brazo que publica sólo en negativos; INDECIDIBLE por H2a con
  un Test 1 y con otro commit; se niega sin `--sha-codigo` y con `--base c0` sobre brazos K.
- **Regla W2** (`evaluar_diurno.py:921-925`): base c0 «NO ADOPTAR»; base k, cumple sin W2 y falla con W2, «DECIDE
  NICOLAS CON M4»; base k, falla con y sin W2, «NO ADOPTAR» (`arnes_completo_salida.txt:1813-1815`). `w2_en_c0` cae.
- **Cálculo de la cola**: fuerza bruta en 60 casos (0 malos), `cola_exacta(x)` incluye el propio x, colas del muestreo
  contra exactas. `gt_en_g1`, `xobs_mas_1`, `g1_estratos_juntos`, `alfa_g1_010`, `estratos_con_tabla` caen.
- **Datos reales de C0 con el commit de hoy**: base por defecto, «regla G1: p95 muestreado», «NO ADOPTAR (G1 falla en
  W2 a W6: FALLA)», controles del nulo OK 0,013 contra 0,012 (`real_c0_salida.txt`); base k, «regla G1: cola exacta»,
  cola 0,5223 y 0,1058, control exacto 0,013 contra 0,012 (± 0,010) OK, INDECIDIBLE por cableado de los dos brazos y por
  H2a (`real_basek_salida.txt`). Coincide con lo que reportó el primer verificador.
- **H2b**: brazos K sin `--base` se niegan; `--base c0` con brazos K se niega, también con tabulador.
- **H2a sin sha**: devuelve un problema en vez de caerse (`h2a_sin_sha_ok` cae); `sin regimen` sale como roto
  (`h2a_sin_regimen_ok` cae); `h2a_ignora_ultima_raiz` y `h2a_no_bloquea` caen.

## Las dos preguntas del instrumento

- *Si la regla estuviera mal, ¿las pruebas lo verían?* Para el cálculo de la cola, para la regla W2, para el control del
  nulo y para el cableado de `--base k`, sí: 30 mutaciones caen por una prueba con nombre. Para **cuál de las dos reglas
  decide** cerca del umbral, no (N-1). Para **H2a sobre más de una raíz, un volcán o el brazo control**, no (N-2).
- *Si el evaluador estuviera muerto, ¿la salida se vería distinta?* Sí en lo que decide: la cola cambia entre ventanas
  y coincide con una cuenta independiente, y la línea `[brazos]` nombra la regla. No en una línea: H2a da «OK» igual
  sobre cero records que sobre todos (N-5).

## ¿Listo para despachar?

Sí, en el sentido de que con el código de hoy el A/B decide con la regla sellada: lo comprobé de punta a punta sobre
datos reales y sintéticos. Lo que falta es del lado de las pruebas y protege contra regresiones: un caso donde la cola
exacta y el p95 muestreado discrepan (N-1, de los que lista `m4`) y H2a probada con dos raíces, dos volcanes y un
Test 1 en el brazo control (N-2). Son unas 30 líneas de arnés. Recomiendo cerrarlas antes del despacho si va a entrar
código nuevo al evaluador entre ventanas; si el despacho sale del tag fijo `s154-diurno-k-codigo` y el evaluador no se
toca, el riesgo es bajo. Y dejar escrito en el procedimiento `git rev-parse s154-diurno-k-codigo^{commit}` (H-5).
