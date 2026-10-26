# Verificador 5 de S156: vigilancia de la sombra, diff 66171d296..f9a5b7e17

Worktree de sólo lectura `D:\vrp-trabajo\worktrees\s156-sombra-verif` (detached en f9a5b7e17, `git status` limpio al
terminar). Mutaciones en una copia extraída con `git archive` en
`D:\vrp-trabajo\temporales\s156_sombra\verificador5\copia\`. Python 3.12.10, pytest 9.0.3 (el CI usa 3.11: SIN
VERIFICAR en 3.11, aunque el cambio no usa nada propio de 3.12).

## Veredicto por afirmación

| Afirmación | Veredicto | Script y salida |
|---|---|---|
| F1. Plazo pasada por pasada: dentro si es una de las primeras 29 protegidas vistas por la sombra (la 29.ª incluida, orden por instante) y anterior al vencimiento | **PARCIAL** | `e1_bordes_plazo_y_juzgadas.py` → `e1_salida.txt`. Lo que funciona: la 29.ª entra, la 30.ª no (P8, P9); empates de instante se rompen por nombre de volcán, determinista (P1: Llaima dentro, Villarrica fuera, mismo granulo); protegida sin record de producción cuenta como vista, sin record de sombra no (P5); las juzgadas ocupan lugar en el orden (P9). Dos matices: (a) **el vencimiento es la FECHA, no el instante**: con adopción 2026-10-18 09:57:30, una candidata del 2027-02-15 05:00 o 09:57:29 sale FUERA aunque sea anterior a adopción + 120 días (P4); el plazo real termina 2027-02-15 00:00 UTC, casi 10 h antes. (b) **la clase de una pasada SÍ puede cambiar entre corridas** cuando aparece una protegida vista con instante anterior o desaparece una: P2 (fila tardía: REVERSION → FUERA; el consolidado pierde dos filas: vuelve a REVERSION) y P3 (la sombra llega tarde a una pasada anterior: REVERSION → FUERA). |
| F1 (b), ¿pasa en los datos? | **PARCIAL / SIN VERIFICAR a escala diaria** | `e2_filas_tardias_referencia.py` → `e2_salida.txt`. Contra los snapshots semanales versionados (2026-09-21 a 2026-10-14) la referencia del 2026-10-19 **pierde** 1 a 5 alertas por snapshot (0 protegidas) y **no agrega** filas tardías con instante anterior al máximo de cada snapshot. Los tres snapshots más viejos tienen una fila suelta del 2026-09-19 y no sirven para esto. Un desfase de un día (OCR o sombra que llega a la corrida siguiente) no se ve con snapshots semanales: SIN VERIFICAR. El efecto sólo importa en el borde de la 29.ª. |
| F2. Una juzgada sale sólo de la reversión y sigue en persistencia, conteos, retrospectivo y duración | **CONFIRMADO en el código; PARCIAL en coherencia con la marca (d)** | P6, P7, P9 de `e1_salida.txt`; F4. La juzgada no dispara reversión ni FUERA (P7), cuenta en la duración y en el orden (P9) y queda en el retrospectivo (F4). Pero (d) dice «no vuelven a disparar», y **tres juzgadas en noches seguidas dan INVESTIGAR por persistencia todos los días, para siempre** (P6: 2026-10-25, 2026-12-31, 2027-06-01 y 2028-01-01). Antes de este cambio la juzgada salía de la persistencia; el cambio lo reintrodujo. La nota en REGLA_ADOPCION.md se presenta como «nota de implementación, no decisión nueva», pero cambia el alcance de (d) en ese caso. |
| F2. Formato estricto del archivo de juzgadas | **CONFIRMADO, con un hueco menor** | Las 5 entradas malas de la prueba caen; mis mutaciones que quitan cada validación quedan atrapadas (`v5_todo.json`). Una fecha con forma válida pero imposible (`2026-13-45 99:99`) pasa la expresión regular y no calza con nada, en silencio. |
| F3. 72 de 72 atrapadas por aserción, control que cae y no cuenta | **CONFIRMADO** | Reproducido con `mutar_vigilancia.py` sobre la copia (`mutar_autor_abs.txt`: 72 de 72, control OK). Sin bytecode (`PYTHONDONTWRITEBYTECODE=1`, borrando el .pyc antes de cada mutación) el resultado es idéntico (`v5_todo_nobc.txt` igual a `v5_todo.txt`): la suite corre en 0,3 s, así que descarté un .pyc viejo. Ninguna mutación del autor mezcla fallas por aserción con caídas (`v5_todo.json`, revisión de mensajes); ninguna depende sólo de `DID NOT RAISE` salvo `Q_juzgadas_formato_laxo`, donde es legítimo. |
| F3. ¿El criterio puede dar un falso «atrapada»? | **Nulo medido con 7 controles** | `mutar_v5.py` → `v5_todo.txt`. Seis controles que sólo hacen caer el script (KeyError en `disparadores`, ValueError en `leer_juzgadas`, que una prueba con `pytest.raises(ValueError)` absorbe, TypeError en `pasadas_de_alerta`, NameError en `dentro_de_plazo`, ValueError en `wilson`, SyntaxError): **ninguno cuenta**. El séptimo, un `raise AssertionError` dentro del script, **sí cuenta**: el criterio clasifica por tipo de excepción. Hoy es teórico: 0 `assert` en el script y sus cinco módulos auxiliares. Detalle: con una ruta RELATIVA el script del autor escribe el JUnit en un lugar que no lee y da «0 de 72» (`mutar_autor_normal.txt`); falla del lado seguro. |
| F3. Mutaciones nuevas (26 sobre el código que cambió) | **4 sobreviven** | `v5_todo.txt`: de 23 que aplican, 18 atrapadas por aserción, 1 por caída (`V5_leer_juzgadas_ausente_vacio_falla`: archivo ausente lanza FileNotFoundError; el criterio no la cuenta, con razón) y 4 sobreviven: `V5_fuera_gana_a_reversion` (si en una corrida hay a la vez una candidata dentro y otra fuera de plazo, el veredicto pasaría a FUERA y se abriría el issue sin pre-autorización: la prioridad no tiene prueba), `V5_fuera_incluye_juzgadas` (una juzgada fuera de plazo dispararía FUERA todos los días: la exclusión no tiene prueba), `V5_vence_inclusivo` (`<` cambiado a `<=` en el vencimiento: el borde no tiene prueba) y `V5_workflow_fuera_sin_detalle` (el issue de fuera de plazo sin la línea de la pasada). Las 4 dan 58 de 58 pruebas en verde. Tres no aplicaron por texto duplicado; las cubren `Q_duracion_cuenta_no_protegidas` y P9. |
| F4. Corrida real con la referencia del 2026-10-19 | **CONFIRMADO** | `correr_sombra.py` → `f4_out/sombra_latest.json`, `f4_stdout.txt`, `f4_comparacion.txt`: VERDE, 0 de 29 desde la adopción, vence 2027-02-15, 61 protegidas vistas en el retrospectivo, PCC VIIRS 750 2026-10-10 05:54 como juzgada y en el retrospectivo; **idéntico** a `sombra_latest_2026-10-19_final.json` salvo `generated_utc`. El bloque del workflow que arma el detalle imprime bien una candidata fuera de plazo (`e3_snippet_workflow.py` → `e3_salida.txt`). |

## Hallazgos propios, por gravedad

1. **MEDIA. La persistencia es pegajosa sin salida, y ahora también por juzgadas.** Una racha de tres noches en
   cualquier volcán desde la adopción da INVESTIGAR todas las corridas, sin plazo y sin forma de marcarla como vista
   (P6, también sin juzgadas). El archivo de juzgadas no la apaga, a diferencia de la reversión. El workflow comenta
   cada día el issue abierto, o abre uno nuevo si se cerró. Se resuelve con una decisión (¿la persistencia tiene plazo?
   ¿una racha juzgada se anota?), no con código a ciegas.
2. **MEDIA (pruebas). La prioridad REVERSIÓN sobre FUERA DE PLAZO y la exclusión de juzgadas en FUERA no están
   probadas** (dos mutantes sobreviven). El código de hoy está bien (P7, P8); una regresión no se notaría.
3. **BAJA. El vencimiento se corta a medianoche UTC del día 120**, no en el instante adopción + 120 días, mientras
   que la adopción se mide al segundo. Es conservador (acorta la pre-autorización ~10 h) pero contradice la frase
   «anterior al vencimiento (adopción + 120 días)». Sin prueba del borde.
4. **BAJA. La clase de una pasada en el borde de la 29.ª puede cambiar entre corridas** por filas que la referencia
   pierde (medido: 1 a 5 alertas por semana, ninguna protegida todavía) o por la sombra que llega tarde. Un issue de
   «candidata a reversión» podría quedar acompañado al día siguiente de uno de «fuera de plazo» por la misma pasada.
   Mitigación posible: congelar el orden en el archivo de historial.
5. **BAJA.** `sombra_history.jsonl` guarda `n_reversion` pero no el número de candidatas fuera de plazo.
6. **BAJA.** Fechas imposibles con forma válida pasan el formato estricto de juzgadas.

## ¿Impide mergear?

No. La corrida real es correcta y no hay reversión indebida ni ceguera hoy (faltan 120 días para el vencimiento y la
sombra no ha visto ninguna protegida posterior a la adopción). Antes de que haga falta conviene: agregar las dos
pruebas del hallazgo 2 y la del borde del vencimiento, y llevarle a Nicolás el hallazgo 1, porque la nota en la regla
cambia el alcance de su marca (d) en el caso de la persistencia.
