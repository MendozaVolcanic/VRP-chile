# Verificador del candado de la adenda K, tercera vuelta

Commit verificado: `1c1c2b1f76fcadf95c0284f78365a513bce4dcb3` (worktree `D:\vrp-trabajo\worktrees\s155-verif-candado`,
detached). Vara: `experiments/_s151_ab_diurno/ADENDA_K.md` (sellada v2: opción A de §3.1, opción i de §3.2, candado
de §4) y, por su remisión, `PREREGISTRO.md`. No modifiqué código, pruebas ni documentos del repo: sólo escribí en esta
carpeta. Las copias mutadas `experiments/_vk3_*` se borraron solas (`ls -d experiments/_vk*`: «No such file or
directory» al final) y los temporales de `D:\vrp-trabajo\temporales\v3_*` los borré yo. `git status --short` al
terminar: sólo `?? experiments/_s151_ab_diurno/verificador_candado_k_v3/`.

## Veredicto corto

Desde el punto de vista de las pruebas, **listo para despachar si el evaluador no se toca entre el tag y la
evaluación**. Las pruebas nuevas atrapan lo que dicen atrapar y por la razón correcta: las 42 mutaciones del autor
caen por una prueba con nombre (41 con el filtro `1,3,k`, la restante con la batería completa), ninguna por caída. El
código de hoy decide con la regla sellada, y la regla nueva de N-5 y la exigencia de 40 caracteres no rompen una
corrida con la forma real del A/B. Quedan tres huecos de gravedad 2 (la rama K del veredicto fuera de W2, el Test 1
en pasada diurna, `x_obs` por techo) que son regresiones futuras que pasarían en verde, no defectos de hoy.

## Corridas (salida cruda al lado)

| qué | comando | archivo | resultado |
|---|---|---|---|
| batería completa, árbol quieto | `PYTHONDONTWRITEBYTECODE=1 python experiments/_s151_ab_diurno/probar_evaluar_diurno.py` (TMP en D:) | `arnes_completo_salida.txt` | «AUTOPRUEBA: 125 de 125 comprobaciones OK», rc 0, 05:05:17 a 05:18:59 UTC. Nada se escribió en el árbol mientras corría salvo esta carpeta, que el arnés no lee (`grep -n "glob(\|iterdir" probar_evaluar_diurno.py evaluar_diurno.py`: sólo lee `<raiz>/<brazo>/*.json`) |
| 42 mutaciones del autor + 30 nuevas + control, filtro `1,3,k` | `SOLO=1,3,k HILOS=6 python m6_mutaciones_v3.py` | `m6_salida.txt` | 05:19 a 06:19 UTC; control «ninguna»: 76 de 77, sólo falla el artefacto conocido `cobertura_workflow` |
| 9 mutaciones con la batería completa | `SOLO="" HILOS=8 python m6_mutaciones_v3.py ninguna veredicto_w2_antes_de_g3 w2_simetrica_adopta g2_ignorado_en_k g3_ignorado_en_k repetir_ignorado_en_k h2a_solo_nocturnos h2a_cero_solo_diurno xobs_techo_crudo` | `m6_completa_salida.txt` | control «ninguna» 125 de 125 (segunda batería completa limpia, en copia) |
| forma de las raíces reales de C0 | `python m5_raices_reales.py C:/Users/nmend/AppData/Local/Temp/claude/diurno_eval` | `m5_raices_reales_salida.txt` | 10 raíces, 0 brazos sin records, 0 volcanes vacíos |
| raíces reales disfrazadas de K | `python m7_raices_k_disfrazadas.py` | `m7_salida.txt`, `m7_punta_a_punta_*.txt` | ver pregunta 2 |
| `x_obs` con techo, piso y redondeo | `python -c` (texto en el archivo) | `m8_xobs_redondeo_salida.txt` | ceil distinto en 2.964 pares (x, n), n < 400 |

Método de mutación (`m6_mutaciones_v3.py`): importa el diccionario `MUT` del script del autor
(`candado_k_s155/m1_mutaciones_v2.py`, leído antes: copia los `.py` y `.json` de primer nivel, aplica UN reemplazo
que tiene que aparecer exactamente una vez, corre el arnés de la copia, borra la copia) y le agrega 30 propias con el
mismo mecanismo, prefijo `_vk3_`. Comprobé antes de correr que los 72 textos aparecen exactamente una vez en
`evaluar_diurno.py`. ATRAPADA (caída) se informa aparte y no cuenta.

Las dos preguntas del instrumento. (1) Cada mutación es la regla rota de una forma concreta, así que si las pruebas no
la ven, sale NO ATRAPADA. (2) El instrumento vivo se ve en el control «ninguna» (sólo el artefacto conocido) y en el
control positivo: las 41 que la segunda vuelta vio atrapadas siguen atrapadas, y en `m7` el escenario (e), un solo
record con sha de 12 caracteres entre 27.314, sale roto.

## Pregunta 1: ¿las pruebas nuevas atrapan lo que dicen, por la razón correcta?

**Las 42 del autor.** Con `1,3,k`: 41 ATRAPADAS por prueba, 0 por caída, 1 NO ATRAPADA (`veredicto_w2_antes_de_g3`,
apaga G3 entero). Con la batería completa esa también cae, por siete casos de G3 con nombre (`m6_completa_salida.txt`:
«118 de 125 OK | fallan ['borde_fuera_del_corte', ...]»). Las que cerraban N-1 a N-5 caen por la prueba que las
nombra:
- `g1_regla_inversa` por `regla_decide` (los dos casos discriminan de verdad: x = 8, cola 0,0507 FALLA y p95 CUMPLE;
  x = 7, cola 0,0490 CUMPLE y p95 FALLA, `arnes_completo_salida.txt`). Ojo con el segundo: el p95 muestreado FALLA
  porque D queda exactamente en el p95 (+0,2619 contra +0,2619). Depende del muestreo con la semilla del evaluador;
  si otra versión de numpy moviera el p95, la prueba «el caso discrimina» se pondría roja (falso rojo, no falso
  verde). Versiones de esta corrida: numpy 2.4.4, scipy 1.17.1, Python 3.12.10.
- `h2a_solo_primera_raiz`, `h2a_solo_lascar`, `h2a_solo_diurno` por `h2a_matriz`.
- `xobs_floor` por `regla_decide` («15 publicadas de 22 positivos: x_obs = 14 (esperado 15)»).
- `sha_opcional`: en el `m1_salida.txt` del autor salió ATRAPADA (caída) con un `TypeError` de `fullmatch(None)`; en mi
  corrida, sobre el código del commit (`a.sha_codigo or ""`, `evaluar_diurno.py:947`), cae por prueba
  (`punta_a_punta_k`). El autor ya lo había repetido aparte (`m1_sha_opcional_salida.txt`).
- `k_sin_flag_b22` ahora cae por prueba (`base_k`), no por `KeyError`.

**Las 30 nuevas.** 14 ATRAPADAS por prueba, 1 por caída (`sha40_apagado_c0`: con `--base c0` el evaluador se niega
siempre y el arnés muere; es imposible de no ver), 15 NO ATRAPADAS. Las ocho más serias las repetí con la batería
completa: siguen NO ATRAPADAS, 125 de 125.

| mutación | qué hace | batería | gravedad |
|---|---|---|---|
| `w2_simetrica_adopta` | con base k, «G1 pasa sólo con W2» deja de dar DEPENDE DEL OCR y sigue a ADOPTAR | completa | 2 (V3-1) |
| `g2_ignorado_en_k` | con base k, ADOPTAR aunque G2 falle | completa | 2 (V3-1) |
| `g2_uno_basta_en_k` | con base k, basta G2 en un sensor | 1,3,k | 2 (V3-1) |
| `g3_ignorado_en_k` | con base k, se salta G3 | completa | 2 (V3-1) |
| `repetir_ignorado_en_k` | con base k, se salta PENDIENTE DE REPETICION | completa | 2 (V3-1) |
| `h2a_solo_nocturnos` | H2a cuenta el Test 1 sólo en records con hora UTC < 12 | completa | 2 (V3-2) |
| `xobs_techo_crudo` | `x_obs = ceil(m1 * npos)` | completa | 2 (V3-3) |
| `xobs_techo` | ídem sólo con base k | 1,3,k | 2 (V3-3) |
| `h2a_cero_solo_diurno` / `h2a_cero_solo_control` | la regla de 0 records mira un solo brazo | completa / 1,3,k | 1 (V3-4) |
| `h2a_conteo_sin_acumular`, `h2a_conteo_ultima_raiz`, `linea_h2a_sin_conteo` | la línea «H2a: N ... M» informa un número falso | 1,3,k | 1 (V3-5) |
| `rotulo_siempre_adenda` | con base c0 la línea final dice «§6 con la adenda K» | 1,3,k | 1 |
| `sha40_desde_13` | acepta un sha de 13 a 40 caracteres | 1,3,k | 1 (falla cerrado: H2a marca todos los records) |
| `h2a_salta_C` | H2a se salta los volcanes que empiezan con C (Chaitén, Copahue) | 1,3,k | 1 |

Atrapadas por prueba: `h2a_cero_apagado`, `h2a_cero_por_brazo_total`, `sha40_desde_7`, `sha40_match_prefijo`,
`rotulo_siempre_original`, `w2_k_decide_aunque_falle_sin_w2`, `controles_ignorados_en_k`, `alfa_g1_0045`,
`alfa_global_006`, `cola_exacta_fn_gt`, `h2a_sin_triggered`, `cableado_log_sin_flags_k`, `h2b_base_por_defecto_k`.

## Pregunta 2: ¿el cambio puede romper una corrida real?

No, con la forma real de las raíces y siguiendo el procedimiento de la adenda §4.
- Las diez raíces de C0 (`m5_raices_reales_salida.txt`) traen sólo records de su media ventana (por ejemplo W2a de
  2026-06-13 02:15 a 2026-06-21 21:25), entre 699 y 2.149 records por raíz y brazo, ningún volcán con el JSON vacío,
  todos con `regimen`. O sea, la regla «una raíz donde un brazo trae 0 records» no se dispara con datos reales. El sha
  de los records es de 40 caracteres en minúscula (muestra de 1.493 records de W2a, W5a y W6b: los tres shas tienen
  largo 40), así que la exigencia de 40 caracteres coincide con lo que escribe `pipeline/store.py:93` (`GITHUB_SHA`).
  Control positivo de que el script lee: los records C0 traen el Test 1 (por ejemplo W2a control 457).
- Hecho notable de paso: W5a trae dos shas en los dos brazos (`7b825ba04271` 968 y `eb97779f4c0e` 231 en el control),
  o sea un job repetido desde otro commit y unido. Es exactamente lo que H2a existe para atrapar, y pasó en la corrida
  real sobre C0.
- Raíces reales disfrazadas de K (`m7_salida.txt`; sólo se tocaron nombres de brazo, flags del log, `triggered_test1`,
  `test1_roi` y `regimen`): (a) diez raíces limpias: «conteo {'control': 9762, 'diurno': 17552} | problemas 0»;
  (c) más una repetición con los dos brazos: 0 problemas; (d) sin `Copahue.json` en el control de W5a: H2a no lo ve (lo
  ve la cobertura, no es su trabajo); (e) control positivo, un record con sha de 12: «1 records con codigo_sha distinto
  del tag». Punta a punta con `--brazos K --base k --sha-codigo <40>`: rc 0, «regla G1: cola exacta», «H2a: 9762 records
  del control y 17552 del diurno leídos», «OK», «== VEREDICTO (§6 con la adenda K)» (el veredicto mismo no significa
  nada: son datos de C0). Con sha de 12 o en mayúsculas el evaluador se niega con su motivo (rc 1).
- Lo único que la regla N-5 rompe es un camino que el pre-registro todavía describe (V3-6, gravedad 1).

## Hallazgos

### V3-1. La rama K del veredicto sólo está probada en la regla W2, en H2a y en los controles
- Dónde: `evaluar_diurno.py:919` (repetir), `:924` (G3), `:934` (pasa sólo con W2), `:936` (G2). Pruebas de la ruta
  K: `chequear_regla_w2` (sólo `G1_W2W6` FALLA) y `chequear_punta_a_punta_k` (k1 ADOPTAR con G2 que cumple, k2 G1
  falla, k3 y k4 controles, k5 rechazos).
- Qué pasa: la adenda dice que G2, G3 y el resto del §6 rigen sin cambio sobre K. El código de hoy lo cumple, porque
  esas ramas no dependen de la base (leído). Pero ninguna prueba las ejerce con `--base k`: una regresión que las
  condicione a la base pasa los 125 casos. La peor: con K, «G1 pasa sólo con W2» o «G2 falla» terminando en ADOPTAR.
- Cómo se ve: invisible para el operador; el A/B diría ADOPTAR donde la regla sellada dice DEPENDE DEL OCR o DECIDE
  NICOLAS CON M4. Atenuante: ADOPTAR no enciende nada en producción (adenda §5).
- Reproducir: `SOLO="" python m6_mutaciones_v3.py w2_simetrica_adopta g2_ignorado_en_k g3_ignorado_en_k repetir_ignorado_en_k`.
- Confianza CONFIRMADO. Gravedad 2. Arreglo que sugeriría (no lo hice): en `chequear_regla_w2`, los mismos `res`
  sintéticos con `G1_W2W6` CUMPLE y `G1_W3W6` FALLA, con G2 que falla, con G3 que falla y con `repetir` no vacío, bajo
  `_con_base("k", ...)`.

### V3-2. Ninguna prueba pone un Test 1 en una pasada diurna
- Dónde: `probar_evaluar_diurno.py:472` y `:593` (records de H2a a las «2026-07-01 05:00» UTC) y `:679` (k3 marca
  `por["diurno"]["Lascar"][0]`, que la segunda vuelta midió nocturno).
- Qué pasa: de día es donde el Test 1 decidía en C0 (adenda §1: 2.000 de 2.077 publicaciones diurnas de VIIRS 375 en
  negativos limpios). Una H2a que mire sólo records nocturnos pasa la batería entera.
- Cómo se ve: invisible; un brazo con el Test 1 encendido de día pasaría H2a (el cableado por log sí lo vería si el
  log existe, pero H2a está justo para cuando no hay log de esa corrida).
- Reproducir: `SOLO="" python m6_mutaciones_v3.py h2a_solo_nocturnos` (125 de 125).
- Confianza CONFIRMADO. Gravedad 2.

### V3-3. `x_obs` por techo no lo ve nadie, y va en la dirección peligrosa
- Dónde: `evaluar_diurno.py:622` (hoy `round`, correcto). La prueba de N-4 cubre el piso (15/22).
- Qué pasa: `ceil(x/n*n)` difiere de x en 2.964 pares (x, n) con n < 400, por ejemplo 7 de 25
  (`m8_xobs_redondeo_salida.txt`). Sube `x_obs` en uno, achica la cola y hace cumplir G1 más fácil: anticonservador,
  al revés que N-4.
- Reproducir: `SOLO="" python m6_mutaciones_v3.py xobs_techo_crudo` (125 de 125).
- Confianza CONFIRMADO. Gravedad 2. Arreglo sugerido: un caso con 7 publicadas de 25 positivos.

### V3-4. La regla de 0 records se prueba sólo con los dos brazos vacíos a la vez
- Dónde: `evaluar_diurno.py:133`; pruebas en `chequear_h2a_matriz` (sin directorios y JSON vacíos, siempre los dos).
- Qué pasa: si la regla mirara un solo brazo, nada lo ve. Atenuante: una media ventana sin brazo diurno deja más del
  10 % de la tabla sin procesar y el evaluador manda a repetir (`:840`, `MAX_NO_PROCESADAS_POS`); sin control, G3 ve
  noches dispares. O sea, hay defensa en profundidad.
- Confianza CONFIRMADO. Gravedad 1.

### V3-5. La línea de conteo de H2a se prueba por presencia, no por verdad
- Dónde: `evaluar_diurno.py:126` y `:136`; prueba `probar_evaluar_diurno.py` (k1 sólo pide N > 0 y M > 0).
- Qué pasa: acumular mal (sólo el último volcán, sólo la última raíz) o imprimir un número fijo pasa. `DESPACHO_K.md`
  le pide al operador mirar esa línea antes del veredicto.
- Confianza CONFIRMADO. Gravedad 1.

### V3-6. El camino del pre-registro «la repetición como otra --raiz» queda roto por N-5 si la repetición trae un solo brazo
- Dónde: `PREREGISTRO.md:423` («Una repetición por cobertura (§5.4) se agrega como otra `--raiz` DESPUÉS de la
  original») contra `evaluar_diurno.py:133`.
- Qué pasa: medido en `m7_salida.txt` (b): una raíz extra con sólo el brazo diurno de Llaima da «_s154_ab_diurno_k_control
  en ...: 0 records», y punta a punta «INDECIDIBLE (... (H2a))». Falla cerrado, con el motivo escrito. La adenda §4
  manda unir con `unir_ventana.py`, y así (escenario c) no pasa nada. Sugiero dejar escrito en `DESPACHO_K.md` que
  las repeticiones se unen, no se agregan como raíz.
- Confianza CONFIRMADO. Gravedad 1.

### V3-7. Detalles del procedimiento (gravedad 1 o menos)
- `DESPACHO_K.md` no escribe el `gh workflow run` completo. El workflow tiene por defecto los brazos de C0
  (`.github/workflows/reproc-s151-ab-diurno.yml`, entradas `brazos` y `control`). Olvidar `-f brazos=` corre C0 y el
  evaluador con brazos K sale con 0 records (N-5, falla cerrado); olvidar `-f control=` hace fallar la aserción
  «el flag diurno no es el que declara el brazo» del propio job. Ninguno termina en un veredicto falso.
- SOSPECHA: que `GITHUB_SHA` de un `workflow_dispatch` sobre un tag anotado sea el sha del commit (lo que el evaluador
  compara). No lo verifiqué; si no lo fuera, H2a marcaría todo y la primera media ventana lo mostraría (falla cerrado).
- H-4, segunda mitad, sigue abierta: con `--brazos ""` se salta todo el bloque de `evaluar_diurno.py:942`, incluida la
  exigencia de 40 caracteres (leído; no lo volví a correr).
- `DESPACHO_K.md` pide que las 42 mutaciones caigan por prueba: se cumple contando la batería completa para
  `veredicto_w2_antes_de_g3`; con el filtro `1,3,k` son 41.

## VERIFICADO LIMPIO

- Batería completa sobre el commit, árbol quieto: 125 de 125 (`arnes_completo_salida.txt`), y otra vez 125 de 125 en
  copia (`m6_completa_salida.txt`, «ninguna»).
- Las 42 mutaciones del autor: todas atrapadas por prueba (41 con `1,3,k`, 1 con la completa), ninguna por caída
  (`m6_salida.txt`, `m6_completa_salida.txt`).
- La regla que decide coincide con la que se rotula, en las dos direcciones, sobre casos que de verdad discriminan
  (`regla_decide`, `arnes_completo_salida.txt`), y `g1_regla_inversa`, `g1_siempre_cola`, `alfa_g1_le`,
  `alfa_g1_0055`, `alfa_g1_0045`, `cola_exacta_fn_gt` caen.
- H2a con varias raíces, volcanes y brazos (`h2a_matriz`): `h2a_solo_*`, `h2a_ignora_ultima_raiz`,
  `h2a_cero_apagado`, `h2a_cero_por_brazo_total` caen.
- 40 caracteres: sha de 12 y en mayúsculas rechazados con su motivo sobre raíces reales (`m7_punta_a_punta_sha_de_12.txt`,
  `..._en_mayusculas.txt`); el sha de 40 de los records reales pasa.
- Rótulo final con base k: «== VEREDICTO (§6 con la adenda K)» (`m7_punta_a_punta_sha_completo.txt`;
  `rotulo_siempre_original` cae).
- `_con_base` restaura `BRAZOS`, `DECLARADO` y `REGLA` en `finally` (leído) y `chequear_base_k` ahora restaura `REGLA`
  (N-3 cerrado: la prueba «base c0» exige `regla == "p95 muestreado"` y `g1_siempre_cola` cae).
- `_repartir` comprueba con `assert` que la repartición es factible; los dos casos de `regla_decide` comprueban en
  ejecución que discriminan, así que un cambio de la semilla o del muestreo da rojo, no verde.
- Raíces reales: ninguna raíz ni brazo vacío, sólo records de su media ventana, sha de 40 en minúscula
  (`m5_raices_reales_salida.txt`).
