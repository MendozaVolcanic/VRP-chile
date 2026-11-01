# Verificador con contexto limpio del candado de la adenda K (PR #858, rama `loop/diurno-k-candado`)

Commit verificado: `0819f871956797209dd4741e13843ade3da55393` (HEAD del worktree `s153-adopcion`, árbol sin cambios
salvo `experiments/_s154_reproc_k/`, ajeno). Regla contra la que se mide: `experiments/_s151_ab_diurno/ADENDA_K.md`
(sellada v2, opción A de §3.1 y opción i de §3.2, candado de §4). No modifiqué código: sólo escribí en esta carpeta.

## Veredicto por pieza

| pieza | veredicto | por qué, en una línea |
|---|---|---|
| (1) G1 con la cola exacta P(nulo ≥ D) < 0,05 | **CONFIRMADO** en el cálculo; las pruebas del arnés no cubren todo lo que la adenda pide | x_obs, cola y p95 exacto iguales a una convolución propia con `Fraction` (diferencia 6e-16); faltan las pruebas (d) y la mitad de (e) de §3.1 |
| (2) «cumple sin W2, falla con W2» → DECIDE NICOLAS CON M4 | **CONFIRMADO** en el código; **PARCIAL** en las pruebas | `veredicto()` hace exactamente eso sólo con la regla W2 encendida; el arnés no comprueba que `--base k` la encienda (mutación `k_sin_w2` no atrapada) |
| (3) H2a, records sin Test 1 y con el `codigo_sha` del tag | **CONFIRMADO** en el código y sobre datos reales; **PARCIAL** en las pruebas | sobre las 10 raíces reales de C0 ve el Test 1 (220 archivos) y los otros commits (171 archivos, 0 en W6); el arnés no corre `evaluar()` con `--base k`, así que no vería que el chequeo se apague |
| (4) H2b, `--base` explícito si los brazos no son los de C0 | **CONFIRMADO** | brazos K sin `--base` se niega por CLI, con espacios y con tabulador; queda un camino documentado abajo (H-4, gravedad 2) |

**¿Listo para despachar?** El cálculo y la lógica están bien: si se despacha hoy, el A/B decide con la regla sellada.
Lo que falta es del lado de las pruebas: la adenda dice «Se implementa ANTES de despachar con estas pruebas en el arnés:
(a) ... (e)», y (d) no existe y (e) sólo está a medias (H-2). Además el cableado de la regla dentro de `evaluar()` con
`--base k` no tiene ninguna prueba de punta a punta (H-1). Recomiendo cerrar H-1 y H-2 (unas 30 líneas de arnés) antes
del despacho; ninguno cambia el resultado de la corrida, cambian si una regresión futura se vería.

## Comandos y salidas (todas de esta sesión)

| qué | comando | salida |
|---|---|---|
| arnés completo | `python experiments/_s151_ab_diurno/probar_evaluar_diurno.py` (árbol quieto mientras corrió, A112) | `arnes_salida.txt` |
| evaluador sobre las 10 raíces reales, base por defecto | `python -I experiments/_s151_ab_diurno/evaluar_diurno.py --raiz <W2a> ... --raiz <W6b> --repetidas W2,W3,W5,W6 --out reeval_c0_resultado.json` | `reeval_c0_salida.txt`, `reeval_c0_resultado.json` |
| ídem con `--base k --sha-codigo eb97779f...` (punta a punta, brazos C0) | mismo comando + `--brazos _s151_ab_diurno_control,_s151_ab_diurno_on --base k --sha-codigo eb97779f4c0e1a40df20182a60921c1778bced1a` | `reeval_basek_salida.txt` |
| cola exacta del verificador anterior sobre mi resultado | `python -I verificador_adenda_k/p4_cuantil_exacto.py verificador_candado_k/reeval_c0_resultado.json` | `p4_sobre_reeval_salida.txt` |
| regla exacta contra `Fraction`, control del nulo roto, `veredicto()` | `python -I v1_regla_sobre_clases_reales.py reeval_c0_resultado.json` | `v1_salida.txt` |
| mutaciones contra las pruebas nuevas del arnés | `python -I v2_mutaciones_candado.py` | `v2_salida.txt` |
| H2a sobre raíces reales y bordes de H2a/H2b | `python -I v3_h2a_h2b_bordes.py <diurno_eval>` | `v3_salida.txt` |

## Hallazgos

### H-1. El arnés nunca corre `evaluar()` con `--base k`: tres piezas del candado se pueden apagar sin que nada falle
- Dónde: `probar_evaluar_diurno.py` (la batería larga llama `correr(d, extra)` con `extra` en `[]` o
  `["--repetidas", "W3"]`; ningún caso pasa `--brazos`, `--base` ni `--sha-codigo`); el cableado está en
  `evaluar_diurno.py:93` (`REGLA.update(...)`), `:930` (exige `--sha-codigo`) y `:975` (corre H2a).
- Qué pasa: `chequear_regla_w2` enciende la regla W2 tocando `ED.REGLA` a mano (`probar_evaluar_diurno.py:400`), y
  `chequear_h2a_h2b` llama `cableado_records` directo. Nadie comprueba que `--base k` encienda la regla W2, que exija
  `--sha-codigo`, ni que `evaluar()` llame a H2a.
- Cómo se ve (`v2_salida.txt`): las mutaciones `k_sin_w2` (la base k deja la regla W2 apagada), `h2a_apagado_en_evaluar`
  (`if False:` en la línea 975), `sha_opcional` y `w2_sin_mirar_g1b` (DECIDE aunque G1 falle también sin W2) salen
  **NO ATRAPADA** con 23 de 23 comprobaciones OK. Con `k_sin_w2` el A/B real decidiría NO ADOPTAR donde la regla sellada
  dice DECIDE NICOLAS, y la única pista sería el texto `W2: pre-registro original` de la línea `[brazos]`.
- El código de hoy está bien: lo comprobé punta a punta en `reeval_basek_salida.txt` (línea 1: `regla G1: cola exacta |
  W2: decide Nicolás si cumple sin W2`; línea 11: H2a ROTO; veredicto INDECIDIBLE por cableado y H2a, como debe ser con
  brazos C0), y `v1_salida.txt` recorre los 16 casos de `veredicto()`.
- Reproducir: `python -I v2_mutaciones_candado.py`.
- Confianza alta. Gravedad **3** (no cambia la corrida de hoy; una regresión futura del candado pasaría en verde).

### H-2. Faltan pruebas que la adenda pide para la opción A: (d) colas contra el muestreo, y (e) el control con el nulo exacto roto
- Dónde: `probar_evaluar_diurno.py:337-390` (`chequear_cola_exacta`) y `:666` (caso 21); `evaluar_diurno.py:668-691`.
- Qué pasa: (d) no hay ninguna comprobación que compare la cola exacta con la del muestreo. (e) el control con la regla
  exacta sólo se prueba en la dirección «da OK con un brazo que no discrimina»; el caso 21, que exige FALLA con el nulo
  roto, rompe `nulo_barajado`, que la rama exacta ni usa, y corre con la regla c0.
- Cómo se ve: la mutación `control_siempre_ok` (`ok = True` en la línea 688) sale NO ATRAPADA (`v2_salida.txt`). Y sobre
  las clases reales (`v1_salida.txt`), el control con la regla exacta **da OK con una pmf rota**: «pmf corrida +1» en W2 a
  W6 da 0,002 contra 0,012 ± 0,010 → OK (en W3 a W6 sí falla). La binomial por estrato también da OK, pero ahí la rotura
  es casi equivalente con estos tamaños (no la cuento). Las roturas anticonservadoras (corrida −1, sin estratos) sí fallan
  en las dos ventanas.
- Atenuante medido: la prueba contra fuerza bruta del arnés atrapa cualquier rotura de `distribucion_x_exacta` (60
  casos, 0 malos), y la corrida +1 es conservadora. El control no es la última línea de defensa de la pmf, pero la adenda
  lo pide validado y su tolerancia (3 errores estándar con 1.000 permutaciones y una cola de 0,012) no ve un salto de un
  paso en W2 a W6.
- Reproducir: `python -I v1_regla_sobre_clases_reales.py reeval_c0_resultado.json`.
- Confianza alta. Gravedad **2**.

### H-3. La prueba del empate sólo ve errores en una dirección, y su empate es el borde del soporte
- Dónde: `probar_evaluar_diurno.py:358-380`; `evaluar_diurno.py:607-609`.
- Qué pasa: el caso elegido es `[(4,2,2),(6,1,2)]` con x = 3, el máximo posible, donde P(X > x) = 0 (salida del arnés:
  «P(X>=x) = 0.0556; con «>» cumpliría (0.0000)»). La prueba exige FALLA y no comprueba `x_obs`. Por eso atrapa los
  errores que hacen cumplir de más (`gt_en_g1`, `xobs_mas_1`: ATRAPADA) y no los que hacen cumplir de menos
  (`conservadora_en_g1`, `xobs_menos_1`: NO ATRAPADA, `v2_salida.txt`). El empate realista es interior, como W3 a W6 sobre
  C0 (P(≥) 0,1058, P(>) 0,0253).
- Confianza alta. Gravedad **2** (un error conservador apagaría ADOPTAR en silencio, sin dar nunca un falso ADOPTAR).

### H-4. H2b acepta brazos K con `--base c0` explícito, y `--brazos ""` salta todo el bloque
- Dónde: `evaluar_diurno.py:96-103` y `:927`.
- Qué pasa: `resolver_base(K, "c0")` devuelve `c0` (`v3_salida.txt`): con los brazos K y `--base c0` el evaluador decide
  con el p95 muestreado, sin regla W2, sin H2a, y sin exigir los flags de K en los logs. Cumple la letra de H2b
  («`--base` explícito»), pero no hay nada que ate los nombres K a la base k. Además, si `a.brazos` es falso (`--brazos ""`
  o un `Namespace` armado a mano), el bloque entero se salta y quedan los brazos C0 con la regla c0; con raíces K eso
  termina en INCOMPLETO o en un error, no en un veredicto (razonado del código y de `v3_salida.txt` para el `Namespace`;
  el caso `--brazos ""` no lo corrí: SOSPECHA).
- Confianza media. Gravedad **2**.

### H-5. Detalles menores
- `--sha-codigo` se compara como texto exacto contra los 40 caracteres de `GITHUB_SHA`. Si el tag `s154-diurno-k-codigo`
  es anotado, `git rev-parse <tag>` da el sha del objeto tag, no del commit (lo comprobé en un repositorio de prueba:
  `42b9125e...` contra `10f4868f...`), y un sha abreviado da todo roto (`v3_salida.txt`: 2 problemas). Falla fuerte, no
  en silencio; conviene escribir en el procedimiento `git rev-parse <tag>^{commit}`. Gravedad 1.
- H2a sobre una raíz unida mira sólo el record que quedó: `unir_intentos.comparar` excluye `regimen` (`PROCESO`,
  `unir_intentos.py:166`), así que un record de otro commit idéntico al del tag puede quedar oculto. Su contenido es el
  mismo, salvo campos de proceso; no cambia ninguna métrica. Gravedad 1.
- H2a ignora un JSON en un subdirectorio del brazo y se cae con un JSON lista (`AttributeError`); `cargar_brazo` tampoco
  lee subdirectorios, así que no hay records que el evaluador use y H2a no vea. `triggered_test1` distinto de `True`
  (1, «true») no se cuenta, pero en las 27.314 lecturas reales siempre es `bool`. Gravedad 1.
- La línea final dice `VEREDICTO (§6, regla original)` también con `--base k` (`evaluar_diurno.py:1096`): «original» se
  refiere a la regla de alertas mínimas, no al pre-registro sin adenda, pero se puede leer mal. Gravedad 1.
- §3.2 pide informar «aparte las alertas de W2 que se pierden»; M4 informa por ventana las recuperadas de W2, no lista
  las perdidas (se deducen de los positivos de W2). Gravedad 1, SOSPECHA de que alguien la quiera como línea propia.

## VERIFICADO LIMPIO

- **x_obs y la población de D** (`evaluar_diurno.py:586-609`): `d_de` y `estratos_de` usan el mismo conjunto de
  positivos (ventana, procesada, `pos`). `x_obs` del evaluador = cuenta propia de publicadas entre positivos: 25 en W2 a
  W6 y 17 en W3 a W6 (`v1_salida.txt`). El redondeo no tiene margen de error: `m1` es una fracción de enteros. Sobre los
  datos reales no hay pasadas a la vez `pos` y `neg` (0 de 5.018), que es lo único que podría separar el N del nulo del
  de D.
- **Parámetros de scipy** (`:551`): `stats.hypergeom(n_s, k_s, p_s)` es (M = población, n = publicadas, N = positivos),
  el orden correcto; además la pmf es simétrica en n y N, y `np.arange(p_s + 1)` cubre todo el soporte. pmf del evaluador
  contra convolución con `Fraction`: diferencia máxima 1,7e-16 en los 22 estratos reales.
- **La cola incluye el propio x** (`:609`, `pmf[x_obs:]`): cola 0,5222763730 y 0,1057679874, iguales a `Fraction`
  (diferencia 6e-16). La regla «>» daría 0,3139 y 0,0253; W3 a W6 sobre C0 es justamente un caso en que «>» cumpliría y
  «≥» falla.
- **p95 exacto** (`:611-612`): +0,276025 y +0,230262, iguales al cuantil propio y a los +0,2760 y +0,2303 del
  verificador anterior (`p4_sobre_reeval_salida.txt`, que además reproduce su 0,5223 / 0,1058 y la cola muestreada
  dentro de 3 errores estándar con 20 semillas).
- **El umbral**: `ALFA_G2 = 0.05` (`:132`), con «<» estricto, como dice la adenda.
- **Regla W2** (`:913-918`, `v1_salida.txt`): sólo con la regla encendida, y sólo cuando G1 falla con W2 y cumple sin
  W2; los otros 14 casos dan lo mismo que la regla original. Con `--base c0` la decisión sigue siendo el p95 muestreado
  y el veredicto sobre C0 no cambia: NO ADOPTAR, igual que la corrida verificada (`reeval_c0_salida.txt`, línea 509).
- **`codigo_sha` desde un tag**: `store.py:89-94` escribe `GITHUB_SHA`, el workflow hace `actions/checkout@v4` sin
  `ref` (el código corrido es ese commit), y en los records reales de W6a y W6b, despachados desde `s151-diurno-codigo`,
  el sha es `eb97779f...` = `git rev-parse s151-diurno-codigo^{commit}`; W5a, unida con una repetición desde ese tag,
  trae los dos shas (2.507 y 831 records). Una repetición desde el mismo tag lo conserva.
- **H2a lee todo**: las 10 raíces, los dos brazos y todos los `*.json` del directorio de cada brazo (más que
  `cargar_brazo`, que sólo lee los 11 volcanes). Sobre C0 ve 220 archivos con Test 1 y 171 con otro sha, 0 en W6a/W6b
  (`v3_salida.txt`).
- **H2b**: brazos K sin `--base` se niegan por CLI, también con espacios o tabulador (`evaluar()` quita espacios antes);
  `--base k` sin `--sha-codigo` se niega.
- **Arnés completo**: ver la última sección.

## Las dos preguntas del instrumento

- *Si la regla estuviera mal implementada, ¿las pruebas lo verían?* Para el cálculo, sí: fuerza bruta y el empate atrapan
  roturas de la pmf y el cambio de «≥» por «>». Para el cableado con `--base k`, no (H-1); para errores conservadores en
  `g1`, no (H-3); para un control del nulo siempre OK, no (H-2).
- *Si el evaluador estuviera muerto, ¿la salida se vería distinta?* Sí: la línea de la cola cambia entre ventanas
  (0,5223 contra 0,1058) y coincide con una cuenta independiente; con `--base k` la línea `[brazos]` y la de H2a nombran
  la regla, y sobre brazos C0 H2a sale ROTO con conteos que coinciden con los records.

## Arnés completo

`arnes_salida.txt`: **«AUTOPRUEBA: 95 de 95 comprobaciones OK»**, rc 0, 11 min 54 s. Mientras corrió no edité ningún
archivo que el arnés lee (sólo escribí en esta carpeta, que el arnés no toca). El verde no contradice H-1 a H-3: esas
mutaciones dejan las 95 en verde porque ninguna comprobación las mira.
