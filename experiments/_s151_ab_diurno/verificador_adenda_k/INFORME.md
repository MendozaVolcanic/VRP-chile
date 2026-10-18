# Verificador con contexto limpio: adenda K del A/B diurno (tarea 1.32, D-10, issue #813)

Fecha: 2026-10-18 (hora del servidor de GitHub al cierre: 22:53 UTC). Worktree `s153-adopcion`, rama
`loop/diurno-k-adenda` en 4d8bcc625, sin checkout ni commits. Sólo se escribió en esta carpeta.

## Veredicto: NO LISTA PARA EL SELLO TAL COMO ESTÁ (faltan dos cosas que se resuelven antes de ver datos)

Las cuatro preguntas de la §6: (1) LIMPIO, (2) HALLAZGO, (3) LIMPIO, (4) HALLAZGO en la prueba, no en la regla.
Además, un hallazgo propio de gravedad 4 sobre cómo la adenda resume el contrafactual (V1).

## Comandos y salidas (todo corrido en esta sesión; salida cruda en esta carpeta)

| qué | comando | salida |
|---|---|---|
| pruebas de perfiles | `python -m pytest tests/test_perfiles_diurno_k_s154.py tests/test_guard_perfiles_congelados_s153.py -q` | `pytest_perfiles_salida.txt`: 9 passed |
| constantes en proceso limpio por perfil | `python -I verificador_adenda_k/p1_constantes_proceso_limpio.py` | `p1_salida.txt` |
| arnés, subconjunto | `PROBAR_SOLO=1,3 python -I experiments/_s151_ab_diurno/probar_evaluar_diurno.py` | `arnes_solo_1_3_salida.txt` (30 de 31, ver V5) |
| arnés, batería completa | `python -I experiments/_s151_ab_diurno/probar_evaluar_diurno.py` (dos veces) | `arnes_completo_salida.txt` (abortó por PermissionError en el temporal de Windows) y `arnes_completo_salida_2.txt`: **79 de 79 OK**, rc 0 |
| caminos del cableado | `python -I verificador_adenda_k/p2_caminos_cableado.py` | `p2_salida.txt` |
| fuentes de los records de producción bajo K | `python -I verificador_adenda_k/p2b_fuentes_bajo_k.py data/mirova_equivalent` | `p2b_salida.txt` |
| nulo exacto propio, fuerza bruta, muestreo | `python -I verificador_adenda_k/p4_cuantil_exacto.py <repo principal>/experiments/_s151_ab_diurno/salidas/W2_W6_s154/resultado.json` | `p4_salida.txt` |
| costo de las corridas citadas | `gh api repos/MendozaVolcanic/VRP-chile/actions/runs/<run>/jobs` y `python -I verificador_adenda_k/p5_costos.py` | `p5_salida.txt` |

## Pregunta 1: ¿diferencias entre los perfiles K y producción que la prueba no vea? LIMPIO

- En un proceso limpio por perfil (`p1_salida.txt`, 147 constantes): producción contra control K difieren sólo en
  `DATA_SUBDIR` y `PROFILE_NAME`; control K contra diurno K, además en `ENABLE_DAYTIME_VIIRS`. (`VALID_PROFILES`
  aparece distinto sólo porque es un `set` y su `repr` cambia con la semilla de hash de cada proceso; lista los
  mismos archivos.) El instrumento ve K: control K contra control C0 difiere exactamente en `ENABLE_TEST1_PATH`,
  `ENABLE_TESTS_23_PROSE_BRANCH` y `ENABLE_MODIS_B22_PRIMARY`.
- Nada fuera de `pipeline.profile` decide distinto entre producción y los brazos: el código sólo consume constantes
  en mayúscula (ninguna lectura de `_cfg` ni del YAML fuera de `profile.py`); `volcanoes.yaml` lo leen igual todos
  los perfiles y los overrides por volcán van en `VOLCANO_OVERRIDES`, que la prueba compara; las únicas ramas por
  nombre de perfil son `regimen.perfil` en store (G3 lo excluye) y el filtro a los 11 Tier A de
  `run_pipeline.py:464`, que no corre con `--volcano` (el workflow siempre lo pasa, l. 163). La invocación del NRT
  (`nrt.yml:188`) y la del A/B usan los mismos argumentos salvo fechas y `--overwrite`. Las variables de entorno que
  lee el pipeline (`fetch.py`) tocan cobertura, no detección.
- Residuo, no hallazgo: la prueba garantiza «idéntico a producción» en el commit donde corre. El tag fijo de la §4
  lo congela; si `main` cambia `mirova_equivalent` después del tag, la réplica y el control dejan de coincidir, y eso
  es lo correcto para un A/B (mide un solo pipeline).

## Pregunta 2: ¿algún camino por el que un brazo C0 pase el cableado con `--base k`? HALLAZGO (H2a y H2b)

Lo que está bien (`p2_salida.txt`): con `--base k` salen ROTO un brazo con la conectiva `min`, uno con banda 21, uno
con los tres flags de C0, un log de workflow viejo sin las claves de K (`fl.get(c)` da None y `None is not False`) y
un JSON sin log. Los tres flags de K están en la lista `FLAGS_BRAZO` que escribe el workflow
(`.github/workflows/reproc-s151-ab-diurno.yml:157`: `ENABLE_TEST1_PATH`, `ENABLE_TESTS_23_PROSE_BRANCH`,
`ENABLE_MODIS_B22_PRIMARY`). La batería completa pasa 79 de 79, con la comprobación `base_k` incluida.

### H2a. El cableado mira el log, nunca los records; y la unión de la §4 separa records de logs

- Dónde: `experiments/_s151_ab_diurno/evaluar_diurno.py:339-367` (`cableado` sólo lee la línea FLAGS_BRAZO del log de
  la raíz) y `experiments/_s153_fk_v2/unir_ventana.py:16-20` (`brazos()` junta sólo `*.json`; los logs no pasan a la
  raíz unida).
- Qué pasa: la §4 manda repetir un job corto y unir con `unir_ventana.py`. La raíz unida no trae `logs/`, así que (a)
  el evaluador la da por ROTA («sin línea FLAGS_BRAZO»), o (b) quien evalúa apunta `--logs` al primer intento y el log
  ya no es el del job que escribió los records repetidos: es el patrón H5 de la corrida C0, y con eso los flags y el
  commit del job repetido no los mira nadie. Ningún paso compara `regimen.codigo_sha` de los records contra el tag.
- Cómo se ve: caso g de `p2_salida.txt`: log con K y records con `final_hotspot_source = test1_roi`,
  `triggered_test1 = True` y otro `codigo_sha` dan cableado OK.
- Hay un invariante barato a nivel de record: en producción, de los 3.548 records procesados desde el
  2026-10-18 09:57:30 UTC, **0** tienen `triggered_test1` verdadero y **0** `test1_roi` (`p2b_salida.txt`). Exigir en
  los dos brazos «ningún record con `triggered_test1` ni fuente `test1`/`test1_roi`» y «todos los `codigo_sha` iguales
  al del tag» cierra el camino sin depender de qué log quedó en la raíz. SOSPECHA: que el invariante también valga de
  día (sólo lo medí en producción, que es nocturna).
- Confianza alta. **Gravedad 3** (un job repetido desde otra referencia mezclaría dos pipelines sin aviso, A108).

### H2b. `--base` vale `c0` por defecto

- Dónde: `evaluar_diurno.py:1006` (`default="c0"`).
- Qué pasa: con `--brazos` de K y sin `--base k`, la exigencia de K se apaga y un brazo con los tres flags de C0 pasa
  (casos h e i de `p2_salida.txt`). La línea `[brazos] ... base c0` lo imprime, pero nada lo bloquea. La adenda
  escribe el comando con `--base k`; el riesgo es olvidarlo al re-correr.
- Cómo cerrarlo: que los nombres `_s154_*` impliquen `k`, o que `--brazos` distinto del default exija `--base`.
- Confianza alta. **Gravedad 2**.

## Pregunta 3: ¿valen las ventanas anteriores a #850 para un A/B sobre K? LIMPIO

Los dos brazos reprocesan esas fechas desde cero con el mismo código (directorio vacío, `--overwrite`, ningún módulo
lee `data/mirova_equivalent/`: el único `DATA_DIR` sale de `DATA_SUBDIR`, `store.py:62`). Lo que cambió el
2026-10-18 es nuestro detector, no el dato satelital ni la referencia de MIROVA, que además está congelada y se
controla contra `sustrato.json`. Las mezclas de régimen de A104 y de la tarea 1.23 bis son de records guardados, no
de un reproceso con un solo tag. Los tramos de calidad de la referencia (A119) siguen como los fijó el pre-registro.

## Pregunta 4: ¿la opción A está bien planteada y alcanza la prueba? REGLA BIEN; PRUEBA INSUFICIENTE (H4)

- La regla es el valor p exacto de una cola de una prueba de permutación estratificada, con el empate contado del
  lado del nulo (≥). Es consistente con el pre-registro: en las dos ventanas da lo mismo que «D mayor que el cuantil
  95 exacto» (`p4_salida.txt`, W2 a W6 y W3 a W6, FALLA en las dos formas).
- Implementación propia, independiente de la del verificador anterior (hipergeométrica con `math.comb` y `Fraction`,
  sin scipy): 200 casos al azar contra fuerza bruta, **0 distintos**. Sobre las clases de la corrida C0 reproduce
  exacto los números de la adenda: W2 a W6 P(≥D) 0,5223, cuantil +0,2760; W3 a W6 P(≥D) 0,1058, P(>D) 0,0253,
  cuantil +0,2303.
- Lo que la adenda no dice y Nicolás debería saber al sellar: con un nulo tan discreto la regla A es **conservadora**.
  La probabilidad real de cumplir por azar es 0,0120 en W2 a W6 y 0,0253 en W3 a W6, no 0,05 (`p4_salida.txt`). En
  W3 a W6 sobre C0, para cumplir hacía falta un positivo publicado más (18 de 20). No es un error; es el costo de
  no inventar un desempate.

### H4. La prueba propuesta no alcanza para confiar en el cálculo exacto

- Dónde: `ADENDA_K.md`, §3, opción A.
- (a) «El muestreo tiene que coincidir con el exacto lejos de los saltos» no está definido, y comparar cuantiles es
  justo lo que salta: con 20 semillas el p95 muestreado de W2 a W6 toma +0,2446 o +0,2760. Lo que sí converge es la
  cola: P(≥D) muestreada 0,5137 a 0,5320 contra 0,5223 exacta (3 errores estándar = 0,0150). Compara colas con
  tolerancia binomial, no cuantiles.
- (b) «Dar el valor del verificador en W2 a W6» compara contra otra implementación del mismo método, y depende de
  `resultado.json`, que no está en esta rama ni en `origin/main` (ver V2). Falta la comprobación independiente:
  fuerza bruta en estratos chicos (el script de esta carpeta la hace en segundos), un caso con D justo sobre un
  átomo (tiene que contar el átomo) y la mutación `>` en vez de `≥`, que tiene que fallar.
- (c) `controles_del_nulo` (`evaluar_diurno.py:587-623`) compara contra el p95 muestreado. Si G1 pasa al valor p
  exacto y el control sigue en el p95, el control valida un instrumento distinto del que decide (A110; el propio
  comentario de `d_de`, l. 535, pide que el control pase por el código que decide). La adenda no lo menciona.
- (d) Recomendación de forma: hacer la comparación en el entero X (publicados entre positivos), como el verificador
  anterior, no en D flotante. Hoy el D del evaluador y el átomo del nulo coinciden bit a bit (`p4_salida.txt`), pero
  el empate de W3 a W6 mostró que el caso que decide es justamente el de igualdad.
- Confianza alta. **Gravedad 3**.

## Hallazgos propios

### V1. La §1 cita el contrafactual por la ventana que lo favorece y calla la que decide primero

- Dónde: `ADENDA_K.md`, §1, tercer punto y párrafo siguiente.
- Qué pasa: dice que el contrafactual sin Test 1 «deja G1 W3 a W6 cumpliendo (P = 0,001)». El mismo contrafactual da
  G1 **W2 a W6 FALLA** (D +0,132 contra cuantil exacto +0,195, P(≥D) 0,194; `salidas/W2_W6_s154/verificador/v2_salida.txt`
  §4 y H4 del INFORME anterior). Por el §6 del pre-registro y por `veredicto()` (`evaluar_diurno.py:825-826`), si G1
  falla en W2 a W6 el resultado es **NO ADOPTAR**, sin mirar W3 a W6.
- Por qué pesa: los 12 positivos de W2 son sólo OCR, 9 con magnitud desproporcionada (pre-registro §3), y **0 de
  ellos** salen por cúmulo contextual (`v2_salida.txt` §6). K quitó el Test 1, así que lo esperable es que el brazo
  diurno sobre K no recupere ninguno, y que W2 hunda G1 en W2 a W6 justo cuando W3 a W6 discrimina. La regla del
  pre-registro se escribió contra el riesgo contrario (que W2 inflara G1: «si pasa sólo con W2, depende del OCR»); el
  caso simétrico («pasa sólo sin W2») no tiene salida propia y cae en NO ADOPTAR por una ventana que el propio
  pre-registro trata como dudosa. Es una decisión de criterio que se puede tomar **ahora, antes de ver datos**; después
  ya no. Si se deja como está, que la adenda lo diga; si se cambia, va al sello y se declara como cambio de §6.
- Confianza alta en los hechos; el efecto sobre K es SOSPECHA (no medido). **Gravedad 4**.

### V2. La evidencia que cita la adenda no está en su rama

- `salidas/W2_W6_s154/evaluar_salida.txt`, `.../verificador/INFORME.md` y `resultado.json` están en `loop/activo`
  (`git ls-files` en el checkout principal), pero no en `loop/diurno-k-adenda` (HEAD) ni en `origin/main`
  (`git ls-tree -r origin/main experiments/_s151_ab_diurno/salidas` vacío). Al mergear la adenda a `main`, sus citas
  apuntan a archivos que no existen ahí; también los docstrings de los perfiles K y de su prueba. **Gravedad 2**.

### V3. Costo y reloj de la §4

- Horas de runner por media ventana: **10,2 a 15,1** (no «unas 15»); diez medias ventanas, unas 100 a 150 h. La
  mediana por job: control 15,4 a 24,1 min, diurno 40,2 a 58,7 (máximo 66,8), coincide con la adenda.
- Reloj: cada una de las tres corridas citadas duró **7,7, 11,5 y 8,5 h** (de `created_at` a `updated_at`), y el grupo
  `s151-ab-diurno` corre de a una. Diez medias ventanas son del orden de **3 a 5 días**, no 2 a 3.
- El NRT corre con `max-parallel: 8` (`nrt.yml:80`), no 11: con el histórico (8, run 39125546355, hoy 73 de 177 jobs
  terminados, 8 corriendo) quedan 4 de 20, así que «sin margen» no es exacto. Esperar igual es prudente.
- **Gravedad 1** (planificación, no método).

### V4. Ambigüedad menor en la §1

«987 de ellas vienen sólo de `test1_roi` (VIIRS 750: 389 de 731)»: el 389 es `test1_roi`, no `triggered_test1`
(que en VIIRS 750 es 493 de 731, `v2_salida.txt` §2). Se lee bien en contexto. **Gravedad 1**.

### V5. El arnés con `PROBAR_SOLO` da un rojo falso y dos verdes vacíos

- Dónde: `probar_evaluar_diurno.py:537-546`. El bloque de cobertura del caso 14 lee los directorios de los casos 7, 19
  y 8, que con `PROBAR_SOLO=1,3` no se escribieron: el 8 sale `[FALLA]` y el 7 y el 19 salen OK porque «falta todo»
  devuelve el 1 esperado (`arnes_solo_1_3_salida.txt`, l. 205-207). Con la batería completa todo da OK. El aviso
  «NO es la batería completa» ya está; conviene que el bloque se salte si sus casos no corrieron. **Gravedad 1**.

## VERIFICADO LIMPIO

- Las cifras de la §1 y la §3: 2.000 de 2.077, 987 `test1_roi`, 389 de 731, 11 de 22 (las 8 de W2 incluidas),
  P = 0,001 (0,00097), 1.142 contra 20 y 357 contra 6; p95 +0,2446 muestreado y +0,2760 exacto; empate de W3 a W6
  (+0,2303, 0,106 y 0,025). Salen de `salidas/W2_W6_s154/verificador/v2_salida.txt` y `evaluar_salida.txt`, y las del
  nulo las reproduje con una implementación propia.
- Perfiles: los dos escriben en su propio directorio, extienden `mirova_equivalent`, declaran los tres flags de K y
  pasan el guard de perfiles congelados (9 passed).
- Workflow: `FLAGS_BRAZO` trae los tres flags de K; el paso «El brazo LEE lo que declara» ya no fija el nombre del
  brazo diurno y, por lectura del código (l. 138, no ejecutado), falla si el input `control` no coincide con los brazos (un control equivocado hace que los dos
  brazos exijan `ENABLE_DAYTIME_VIIRS` verdadero y el control lo tiene falso).
- Los arreglos #854 y #855 no cambian el criterio: el aviso de saturación sólo imprime y anota (`evaluar_diurno.py:959-970`)
  y el orden de estratos sólo fija el reparto del generador.
- La adenda no tiene guiones largos ni medios (`grep -c` da 0) ni contradice al pre-registro sin decirlo, salvo la
  omisión de V1, que no lo contradice pero deja fuera el caso que decide.

## Qué falta para el sello

1. Resolver V1 en el texto: declarar qué pasa si G1 cumple sin W2 y falla con W2 (mantener NO ADOPTAR a sabiendas, o
   darle salida propia), y citar el contrafactual en las dos ventanas.
2. Si se elige la opción A: ampliar su prueba con H4 a, b, c (colas en vez de cuantiles, fuerza bruta, empate,
   mutación, controles del nulo con la regla exacta).
3. Cerrar H2a con el invariante a nivel de record y el `codigo_sha` del tag, o decir en la §4 cómo se evalúa una raíz
   unida (de qué logs y con qué control del commit).
4. Menores: H2b, V2, V3.
