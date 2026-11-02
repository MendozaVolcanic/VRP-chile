# Informe del implementador: los dos PR del encendido de la vía «código MIROVA» en MODIS (S172)

Fecha: 2026-11-01 (hora del servidor, 2026-11-02 UTC al cerrar). Diseño implementado:
`docs/superpowers/specs/2026-11-01-encendido-modd-design.md` (`d24fda8f3`). Regla:
`experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` (rama `loop/activo`, sin sellar; ⚠️ **S173 (A113)**: desde el PR B (#934) la regla vive en main, en esta misma ruta (ronda 4)). Worktree
`D:/vrp-trabajo/worktrees/s172-modd-encendido`. No se abrió PR, no se mergeó nada, no se despachó ningún workflow ni se
creó ningún tag. Las dos ramas están empujadas a `origin`.

## Ronda 3 (2026-11-02, S173): arreglos pedidos por la segunda pasada de auditoría

Informes: `experiments/_s173_aud/f1/INFORME.md`, `f2/INFORME.md` y sus verificadores `v1/INFORME.md` y `v2/INFORME.md`
(rama `loop/activo`). Worktrees nuevos: `D:/vrp-trabajo/worktrees/s173-moddA` (rama de A) y
`D:/vrp-trabajo/worktrees/s173-moddB` (rama nueva de B). La rama vieja `claude/s172-modd-flip` (`c9525f994`) no se
tocó. Cada arreglo, con su prueba vista primero en rojo y un commit por arreglo. Las rondas 1 y 2 de abajo se
conservan tal cual; donde la ronda 3 las corrige, lo dice aquí.

**PR A, commits nuevos** (sobre `0a0dae344`; avance rápido, sin reescribir historia):

| sha | arreglo | rojo visto antes | verde después |
|---|---|---|---|
| `e6e2a2511` | (1, hallazgo 205, bloqueante) `"VIA_MODIS"` en `REGIMENES` de `scripts/auto_audit_weekly.py`. Barrí con `grep` todo lo que enumera regímenes (A118): `REGIMENES` sólo lo usa `estratificar_magnitud` (el `REGIMENES` de `scripts/evaluador_comun.py` es otro, sin la vía); `DETECTORES` ya tenía `VIA_MODIS`; `TRAMOS_CENIT` no depende del detector. Tres pruebas en `tests/test_auto_audit_via_modis_s172.py`: todo régimen que devuelve `regimen_de_pasada` está en `REGIMENES`; magnitud por régimen con la vía publicando; y la gemela de punta a punta de `main()` con la vía publicando en noches con alerta (la de la ronda 1 tenía la vía en vrp 0 y no pisaba ese camino) | 3 de 11 (`ValueError: tuple.index(x): x not in tuple`, l. 849) | 11 de 11; con el de cenit, 24 |
| `18c887103` | (2, hallazgo 206) `sensores_sin_juzgar` avisa también cuando MODIS queda bajo `MIN_N_RECALL` desde el cambio de detector a la vía (clave `detector: VIA_MODIS`, `motivo: cambio_de_detector`, `juzga_desde` = frontera de la vía); va a `latest.json`, a la consola y a los dos cuerpos de issue de `.github/workflows/audit-weekly.yml` («por un cese de plataforma o un cambio de detector»). No degrada el veredicto, igual que el cese | 3 de 14 | 14 de 14; los 14 archivos del audit, 123 |
| `dcf658393`, `fb1a66d39`, `132b7550e` | (3, hallazgos 161, 162 y V1-04) cherry-pick `-x` de `a256a75cc`, `087b08ced` y `ffe46a68e` del PR B (vigilancia de la sombra de K sin los records de la vía, `esAnclaHonesta` del tablero y la enmienda de `test_no_modifica_la_vigilancia_de_k`). Aplicaron limpio | sus pruebas de B copiadas sobre A sin el código: 7 de 7 fallan | ver la tabla de pruebas |
| `71d355888` | (3) `experimental`, `experimental_ndc_focus` y `_s146_ab_control` declaran `enable_modis_codigo_mirova: false` en `thresholds:`. Inerte en A (los tres ya leían `False`); está aquí para que un revert de B no la arrastre. Los comentarios dicen ahora que el encendido es del PR B. Prueba nueva `tests/test_perfiles_derivados_via_modis_apagada_s173.py` (YAML y `pipeline.profile`) | 3 de 6 (el YAML no declaraba la clave) | 6 de 6 |

El flag de producción sigue apagado en A: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p;
print(p.ENABLE_MODIS_CODIGO_MIROVA)"` da `False` en `71d355888`. En `pipeline/` sólo cambian esos tres perfiles.

**PR B nuevo**: rama `claude/s173-modd-flip`, nacida de la punta nueva de A. Lleva sólo lo que A no tiene: los
commits `f75285693` (con la versión de A de los tres perfiles derivados; queda sólo el flag de producción y las
pruebas del encendido), `61a310340`, `efbbf4d80`, `7f60c02ee`, `d9bdaa6a6` y `c9525f994`, más (4, hallazgo 201) el
guard `tests/test_guard_modis_codigo_mirova_encendido_s172.py` con `sombra_34` en `VIVOS` sólo si su YAML existe
(rojo visto con los archivos de #932 copiados al árbol: 2 fallas, la del 201 y la prueba nueva; verde 7 de 7 con y
sin ellos). El arreglo 4 va en B y no en A porque el guard vive en B: fija producción encendida y en A daría rojo. El
árbol de B nuevo difiere del de B viejo sólo en lo que agregó A en esta ronda (`git diff --stat c9525f994` sobre B
nuevo: 7 archivos, en `pipeline/` sólo comentarios de los tres perfiles) y en el guard.

**Órdenes de merge y reversión** (`git merge-tree --write-tree`, sin crear refs; base `origin/main` `47cdc446f`;
script y salida en el scratchpad de la sesión, `merges.sh` y `merges_salida.txt`):

| estrategia | orden | merges | árbol final | revert de B | árbol del revert contra el mismo orden sin B |
|---|---|---|---|---|---|
| merge commit | A, B, #932 | limpios | `6753a9a13` | limpio (`376033661`) | idéntico |
| merge commit | A, #932, B | limpios | `6753a9a13` | limpio (`376033661`) | idéntico |
| squash | A, B, #932 | limpios | `6753a9a13` | limpio (`376033661`) | idéntico |
| squash | A, #932, B | limpios | `6753a9a13` | limpio (`376033661`) | idéntico |

Los cuatro órdenes dan el mismo árbol. Corrige el punto 6 de la ronda 2 y el hallazgo 203: con `ffe46a68e` ya en A, B
no modifica `tests/test_vigilancia_guardia_modis_s172.py` y el squash de B sobre el squash de A deja de chocar.
Control positivo del instrumento: el A y el B viejos (`0a0dae344`, `c9525f994`) squasheados así siguen chocando en ese
archivo (rc 1). El revert sobre el `main` del día del revert sigue SIN VERIFICAR (208: choca si otro PR toca una línea
vecina del flag).

Las puntas y los árboles de esta sección son los de los commits de código; este informe y el cuerpo del PR B
entran después como commits de documentos (B se rebasa sobre la punta final de A, que no está empujada antes) y
el cuerpo del PR B repite los órdenes de merge sobre las puntas finales.

**Pruebas** (rutas explícitas, no la suite: la lista de 50 archivos es la de los tocados, los vigilados por las
auditorías, los que usan los arneses y los de #932; corre los que existen en cada árbol):

| árbol | archivos | resultado |
|---|---|---|
| A (`71d355888`) | 48 | 813 pasan, 0 fallan |
| B nuevo, punta de código (`db1447fce`) | 49 | 821 pasan, 0 fallan |
| A+B+#932 (árbol `6753a9a13`, con el `main` de hoy) | 50 | 922 pasan, 0 fallan (la falla del 201 ya no aparece; flag de producción `True` leído de `pipeline.profile`) |

**Quedan para Nicolás** (no arreglados en esta ronda, por pedido): 207 (tres maneras de fechar el encendido: tablero
y audit por primera observación de la vía, hasta ~8 a 9 días antes del merge por el upgrade NRT a estándar; vigilancia
por primera escritura; la regla cita `CAMBIO_DETECTOR_MODIS_UTC`, que no existe), 208 (el revert de B choca si otro PR
toca las líneas vecinas del flag en `mirova_equivalent.yaml`, los tres flags de MxD03), 209 y V2-02 (una excepción de
la vía distinta de la falta de pyproj deja MODIS mudo con el NRT en verde; nrt.yml no tiene un paso «salió MODIS» como
la guardia; lo ve la vigilancia de la guardia a los 3 días por volcán). Siguen además 202 (#932 deja rojas 16 de 32
pruebas de la ROI de V750-B), 204 (nadie vigila que la guardia y su vigilancia corran), 210 y 211, fuera de esta ronda.

## Ronda 2 (2026-11-02): arreglos pedidos desde la mini auditoría

Síntesis de la mini auditoría: `D:/vrp-trabajo/temporales/s172_miniaud/SINTESIS.md` (veredicto «LISTO CON CAMBIOS»).
El worktree se recreó desde `origin/claude/s172-modd-encendido` (estaba limpio y subido cuando se quitó por espacio).
La ronda 1 de este informe, más abajo, se conserva tal cual; donde la ronda 2 la corrige, lo dice aquí.

**PR A, commits nuevos** (sobre `c83882fcf`):

| sha | qué |
|---|---|
| `03f3edec5` | (1, bloqueante G5) pyproj en los 22 workflows que corren un perfil con alguna vía encendida (con el perfil del PR B): `nrt.yml`, `backfill-tier-a.yml`, `reproc-chunked.yml` y los probe/reproc de despacho manual. Paso «Comprobar pyproj» (`python -c "import pyproj"`) en esos tres operacionales, después de instalar y antes de `run_pipeline.py`, con la misma condición que la instalación. Prueba `tests/test_guard_pyproj_vias_s172.py`: lee las vías de cada perfil desde `pipeline.profile` y recorre `.github/workflows/` (sin comentarios). Rojo visto: en el PR A sin arreglo, falla la del paso de comprobación; con los perfiles del PR B y los workflows sin arreglo, 22 workflows sin pyproj (`verificacion/rojo_pyproj_pr_b.txt`). |
| `94048cc61` | (2) vigilancia de la guardia: MA172-202 (protegida posterior al encendido que la guardia publica y producción no tiene record, pasadas `ESPERA_SIN_RECORD_H` = 24 h, propuesta que fija Nicolás: INVESTIGAR y línea en el issue; no es reversión pre-autorizada, la regla dice «calla»), MA172-204 (frescura de la referencia también en las filas de MODIS), MA172-206 (encendido = menor `processed_utc` de la vía, no `first_processed_utc`, que hereda K), MA172-208 (nulo con 0 pares = aviso, vigilancia ciega). Rojo visto: 17 de 30 en `tests/test_vigilancia_guardia_modis_s172.py` antes del cambio. |
| (último de la rama) | esta sección y `verificacion/pruebas_pr_a_ronda2.txt` |

**PR B** rebasado sobre `94048cc61`; además de sus tres commits de la ronda 1 (con sha nuevo por el rebase), trae:
(3) `scripts/vigilancia_sombra.py` deja de contar como K los records MODIS de la vía (por clave con
`aa.claves_via_modis`, porque el banco de paridad no copia la marca) y, con records de la vía, deja de exigir la
frescura de K en MODIS (si no, la vigilancia de K quedaría ciega para siempre tres días después del encendido); rojo 4
de 4 en `tests/test_vigilancia_sombra_via_modis_s172.py`; salida sobre `data/` de hoy idéntica antes y después
(`verificacion/vigilancia_sombra_antes_despues.txt`). (4) El tablero reconoce `codigo_mirova` como ancla honesta: la
lista de fuentes vive en `esAnclaHonesta` de `frontend/index.html` (definida en la línea que estaba en blanco, sin
correr las citas) y las siete copias la llaman; diario y mosaico no tienen esa lista; rojo 3 de 3 en
`tests/test_tablero_ancla_codigo_mirova_s172.py`; verificado con node y en el navegador (index carga sin errores y el
marcador de un record de la vía es el cúmulo, 0,567 km). (5) `tests/test_guard_adopcion_k_s153.py` espera la vía en la
diferencia del laboratorio (rojo visto en la punta de B: 1 fallo). Más: el cuerpo del PR declara el ancla pre-K y los
arneses (MA172-107) y el recuento de 33 pruebas (MA172-108); y la prueba «no modifica la vigilancia de K» del PR A
vigila sólo el workflow, porque el PR B cambia `vigilancia_sombra.py` a propósito.

**Pruebas de la ronda 2** (sólo archivos tocados y vecinos, con `--basetemp` en D:): PR A, 627 pasan y 5 omitidas
(`verificacion/pruebas_pr_a_ronda2.txt`); PR B, 1444 pasan, 20 omitidas, 0 fallan
(`verificacion/pruebas_pr_b_ronda2.txt`; con el temporal en D: `test_guard_libro_de_pruebas_s146` también pasa). Antes
de cada corrida pesada esperé el cupo de procesos.

**(6) Revert del PR B, simulado en el worktree y sin push** (ramas desechables borradas):
- sobre la punta de B rebasado: `git diff A B | git apply -R --check` limpio, y `git revert` de `A..B` deja el árbol
  idéntico a A;
- sobre `origin/main` `0f08e889c` con A y B mergeados con merge commit: el revert del merge de B deja exactamente main+A;
- con squash: A squasheado sobre main, B rebasado sobre ese squash y squasheado, y el revert del squash de B deja
  exactamente main+A. Squashear B **sin** rebasarlo sobre el squash de A choca (add/add en
  `tests/test_vigilancia_guardia_modis_s172.py`): con squash merge, B se rebasa sobre main después de mergear A.

**Pendientes que quedan escritos** (fuera de esta ronda):
- `scripts/run_pipeline.py` l. 279 y 280 atrapa toda excepción por gránulo y sigue: un error de la vía no cae a K ni
  deja el job rojo. No lo toqué (pipeline/ y el corredor congelados); el paso «Comprobar pyproj» cubre el caso medido,
  pero no cualquier otra excepción de la vía (VMA172-202).
- MA172-203 (paso `if: failure()` en la guardia que abra el issue), MA172-205 (la marca del tablero tras una reversión),
  MA172-206 en el tablero y el audit (la marca y `frontera_via_modis` usan la primera observación de la vía, que con el
  upgrade NRT a estándar cae días antes del merge), MA172-104 y 110 (`_s154_reproc_k_historico` y `experimental_lowT`
  heredan la vía), MA172-105 y 106 (README, SINTOMAS, aviso de `index.html`, cabecera de `mirova_v750_codigo.py` y
  comentario de `profile.py`), MA172-207 y 209 (texto de la regla), MA172-304 (audit tras una reversión) y VMA172-203
  (el stale-gate del NRT no ve una caída sólo de MODIS).
- `backfill-tier-a.yml` y `reproc-chunked.yml` siguen pasando `EARTHDATA_USERNAME`/`EARTHDATA_PASSWORD` además del
  token (A71); no es de esta ronda.

## Por qué, en una línea

Con K, MODIS pierde más de un tercio de las noches en que MIROVA alerta; la vía ganó el A/B de MOD-D; Nicolás decidió
encenderla ya con K de guardia y reversión el mismo día si la vía calla una protegida que K publica. El PR A deja todo
el andamiaje de esa guardia funcionando con el flag apagado; el PR B es sólo el encendido, para que su `git revert` sea
limpio.

## Ramas y commits

**PR A, `claude/s172-modd-encendido`** (nace del tag `pre-s171-adopcion-modd`, `d3cd0b2ae`):

| sha | pieza |
|---|---|
| `d24fda8f3` | diseño (de la coordinadora) |
| `c7c817f5e` | (a) perfil `pipeline/profiles/guardia_k_modis.yaml` |
| `40bd0bc36` | (b) `.github/workflows/guardia-k-modis.yml` y `scripts/revisar_guardia_modis.py` |
| `a34b361c4` | (c) `scripts/vigilancia_guardia_modis.py`, `.github/workflows/vigilancia-guardia-modis.yml`, `sombra_pasadas_juzgadas_modis.json` |
| `fa1a48595` | (d) detector `VIA_MODIS` en `scripts/auto_audit_weekly.py` |
| `ae252ee39` | (e) marca de MODIS en `frontend/cambio_detector.js` y las tres vistas |
| `da67fa417` | (e) arreglo menor de la prueba (sin guiones largos literales) |
| (último de la rama) | este informe y `verificacion/pruebas_pr_a.txt` |

**PR B, `claude/s172-modd-flip`** (nace de `da67fa417`, la punta del PR A antes de este informe; el commit del informe
vive sólo en el PR A, para no hacer circular el sha):

| sha | pieza |
|---|---|
| `479a30c18` | (a, b) el flag, los perfiles vivos, el ancla pre-K, el guard y las pruebas que fijaban K |
| `47279fe78` | (c) ficha v1.18, marcas A113, comentarios de `process_modis.py` |
| `b42823194` | (d) `PR_B_CUERPO.md` y salida de las pruebas |

## Qué hace cada pieza

- **Perfil de la guardia** (`guardia_k_modis.yaml`): `extends: mirova_equivalent`, vía de MODIS apagada, sólo MODIS,
  `data_subdir: guardia_k_modis`, los tres flags de K declarados. Leído desde `pipeline.profile` difiere de producción
  sólo en carpeta, nombre, sensores VIIRS y (con el PR B) la vía.
- **Workflow de la guardia** (`guardia-k-modis.yml`): calcado de la sombra. Cron **17:40 UTC**: el NRT corre a la hora
  en punto (cron externo y `nrt.yml`), su reintento a las :30 de horas impares, sync a las :12, watchdog a las :20,
  pages a las :50, experimental a las 14:00 y la sombra a las 15:00 con hasta 100 min (16:40); 17:40 queda después y en
  un minuto libre (la prueba lo calcula). `workflow_dispatch` con volcán, medir, start y end. Sólo `EARTHDATA_TOKEN` con
  corte si viene vacío (A71), `"on":` entre comillas, grupo propio `guardia-k-modis`, push con 5 reintentos, aserción
  del perfil desde `pipeline.profile` antes de correr, revisión después del commit, log tachado antes de subirse. Sin
  fecha mínima: corre desde el merge del PR A (es el nulo de la guardia).
- **Revisión de la corrida** (`scripts/revisar_guardia_modis.py`, importa piezas de `revisar_sombra.py` sin
  modificarlo): rojo si la corrida no escribió MODIS, si hay records con la marca de la vía (la guardia dejó de ser K),
  VIIRS u otro perfil, o un día sin MODIS sin prueba de que no hubo pasada.
- **Vigilancia** (`scripts/vigilancia_guardia_modis.py`, importa `vigilancia_sombra.py` sin modificarlo; workflow por
  `workflow_run` de la guardia más cron de respaldo 22:45 UTC; issues «Guardia K de MODIS: ...»): reversión candidata
  (protegida A que la guardia publica y producción calla, desde el encendido, dentro de 29 protegidas o 120 días);
  candidata fuera de plazo; investigar si Muy Bajo perdidas > 2 o sobre-publicación en negativos limpios > 3 en el
  plazo, si el nulo previo al encendido se rompe, o si una protegida anterior al encendido ya tiene record de la vía;
  pasadas que la guardia registra y producción no, por semana ISO, sin disparar; vigilancia ciega por frescura por
  volcán, referencia, guardia con marca de la vía, perfiles cruzados o flag encendido sin records de la vía. El
  encendido sale de los datos: primer `first_processed_utc` de un record MODIS con `via_codigo_mirova: true`.
- **Audit semanal**: detector `VIA_MODIS` (records MODIS con `via_codigo_mirova: true`), frontera desde los datos,
  en MODIS decide la vía; K se informa entero. Las bandas no se recalibran. El banco de paridad no se toca (lo leen
  instrumentos sellados): la vía se cruza por clave.
- **Marca del tablero**: segunda marca en `frontend/cambio_detector.js` (línea naranja «MODIS: vía MIROVA» y aviso),
  desde la primera pasada MODIS de la vía que tiene una de K antes; sólo en gráficos con serie MODIS visible o en la
  serie sin rótulo de mosaico. Las vistas llaman `CambioDetector.notarRecords(...)` una vez, en una línea existente.
- **PR B**: `enable_modis_codigo_mirova: true` en `mirova_equivalent.yaml`; `experimental`, `experimental_ndc_focus` y
  el ancla `_s146_ab_control` lo declaran `false`; guard
  `tests/test_guard_modis_codigo_mirova_encendido_s172.py`; ficha v1.18; marcas A113; cuerpo del PR en
  `experiments/_s171_modd_adopcion/PR_B_CUERPO.md`.

Lectura del flag (PR B), con `VRP_PROFILE=<perfil> python -c "import pipeline.profile as p;
print(p.ENABLE_MODIS_CODIGO_MIROVA)"`: `mirova_equivalent` True, `sombra_codigo_mirova` True, `guardia_k_modis` False,
`experimental` False, `experimental_ndc_focus` False (antes del arreglo los dos laboratorios daban True).

## Pruebas corridas (sólo archivos tocados y vecinos; no la suite completa)

- PR A, sobre su punta `da67fa417` en un checkout limpio: 561 pasan, 5 omitidas, 0 fallan
  (`experiments/_s171_modd_adopcion/verificacion/pruebas_pr_a.txt`; la lista de archivos está en el comando del
  informe de la sesión: las pruebas nuevas, todas las `test_auto_audit_*`, las de la marca de K y del cese, la
  vigilancia de K, la sombra, los guards de workflows y de perfiles, y las del predicado de las tres vistas).
- PR B, sobre `479a30c18` más los documentos (árbol quieto): 1339 pasan, 20 omitidas, 2 fallan
  (`verificacion/pruebas_pr_b.txt`). Los dos fallos son `test_guard_libro_de_pruebas_s146.py::test_g1d_...` y
  `::test_g2c_...`, por `os.path.relpath` entre C: (temporales) y D: (worktree): fallan igual en el PR A
  (`verificacion/libro_de_pruebas_en_pr_a.txt`), no los causa el encendido. La lista: todo archivo de `tests/` que
  nombra `process_modis` o `run_pipeline` (71), los que nombran el flag o los perfiles, y los guards de documentos.
- Comparación del audit antes y después del detector `VIA_MODIS` sobre `data/` real: `latest.json` idéntico salvo
  `generated_utc`, historial y salida idénticos (`verificacion/audit_antes_despues.txt`).
- Corrida real de la vigilancia sobre `data/` de hoy: VIGILANCIA_CIEGA (no hay guardia todavía, aviso por cada
  volcán). Con la guardia apuntada a producción, nulo 0 distintas de 338 pasadas pareadas y el aviso de perfil cruzado
  dispara (control del instrumento). No se commiteó esa salida (era una prueba de instrumento).
- Navegador (servidor local del worktree, puerto 8172, ya detenido): index, diario y mosaico cargan sin errores de JS y
  sin marca de MODIS con los datos de hoy; con un record de la vía inyectado en Chillán aparece el aviso naranja y la
  línea cae en la fecha en el gráfico principal.

Rojos vistos antes de cada verde: anotados en el mensaje de cada commit (perfil inexistente; workflow y script
inexistentes; módulo inexistente; 7 de 8 en el audit, con el recall MODIS mezclado en 55,6 %; 8 de 9 en la marca; 2 de
6 en el guard del PR B con los laboratorios en True).

No corrí: la suite completa (pedido explícito: hay otros procesos pesados), ni ningún workflow en GitHub.

## Desvíos del diseño y decisiones que tomé al ver el código

1. **El encendido rompía pruebas que el encargo no listaba.** Con el flag en el perfil fallaron 28: 26 que corren
   `process_modis` con el perfil de producción y pasan por la vía (o agregan la marca `"sin_grilla"` al record: el
   golden de S142, los arneses de MxD03 y de cráter sin dato, el núcleo de `process_modis`, las sondas 121 y 117),
   `test_experimental_congelado_s150` (su lista de diferencias declaradas) y una mía (un comentario del perfil que
   nombraba la guardia). Las 28 pasaban en el PR A (comprobado en un checkout limpio de `da67fa417`). Esas pruebas
   miden K de MODIS, que sigue vivo como guardia, así que las dejé midiendo K explícitamente (arneses con la vía apagada
   por defecto salvo que un brazo la pida, fixture en `test_process_modis_core.py`) en vez de regenerar goldens con la
   vía. Van en el PR B, porque sin el encendido no hacen falta.
2. **El ancla de las pruebas pre-K heredaba la vía.** `_s146_ab_control` (tests/produccion_pre_k.py) es un brazo viejo
   de A/B, pero es el ancla viva de las pruebas escritas sobre la producción de antes de K. Le declaré la vía apagada y
   `produccion_pre_k` la parchea en los procesadores (`FLAGS_POSTERIORES`). Es la única excepción a «los brazos viejos no
   se tocan».
3. **Brazos viejos que siguen heredando la vía** (perfiles que extienden `mirova_equivalent`, sin la clave, con
   workflow de despacho manual o sin workflow): todos los `_*.yaml` de `pipeline/profiles/` salvo `_s146_ab_control`
   (`_s146_ab_sin_test1` es el control del guard). Si alguien re-despacha uno de esos A/B después del PR B, en MODIS
   medirá la vía. Lo dejo escrito; no los toqué. `mirova_equivalent_villarrica_test1` no extiende producción.
4. **Fecha del encendido en la vigilancia**: tomé el primer `first_processed_utc` de un record MODIS de la vía (cuándo
   escribió la vía por primera vez), que llega después del merge. Las pasadas entre el merge y esa primera corrida
   quedarían del lado retrospectivo; por eso una protegida anterior al encendido cuyo record de producción ya es de la
   vía pide investigar (no es reversión pre-autorizada). Es la implementación más cercana a «desde el encendido» sin
   una constante.
5. **(iii) borde 171-01 sin disparo**: la regla no da cota; se informa por semana (A115).
6. **Nulo de la guardia como disparador de investigación**: el diseño lo llama el nulo medido; lo hice disparar
   INVESTIGAR si antes del encendido guardia y producción publican distinto en una pasada pareada (se puede juzgar en el
   archivo de juzgadas). Si las versiones NRT y estándar de un gránulo difieren entre las dos corridas, esto puede dar
   falsas alarmas: SIN VERIFICAR hasta que corra la guardia.
7. **Marca del tablero**: se exige una pasada de K antes de la primera de la vía en los mismos records (para no correr
   la marca al inicio del JSON liviano pasados 100 días). El audit usa el mínimo sobre los JSON completos; coinciden
   mientras haya K antes, que en los completos siempre hay.
8. **Comentarios de `pipeline/process_modis.py`** (cabecera FICHA y el del bloque de la vía) decían «APAGADA (hoy)»:
   los actualicé en el PR B. Sólo comentarios: AST idéntico, mismas 1792 líneas (las citas archivo:línea no se corren).
9. **Guiones largos**: todo lo que agregué tiene 0. Archivos que ya los tenían antes (`scripts/auto_audit_weekly.py`,
   `CLAUDE.md`, `docs/*.md`, las vistas) los conservan: cambiarlos sería reescribir historia o cambiar la salida del
   audit que comparé.
10. **Archivo bajo `pruebas/`**: `.gitignore` ignora `Pruebas/`; la carpeta de evidencia se llama `verificacion/`.

## Lo que quedó fuera o SIN VERIFICAR

- Ningún workflow nuevo corrió en GitHub (no se despacha nada): la guardia, su revisión y su vigilancia están probadas
  sólo localmente. El primer día dirá si el job cabe y si el nulo es cero.
- El revert del PR B sale limpio sobre su propia punta (`git apply -R --check`), y ningún commit de `origin/main`
  posterior a `d3cd0b2ae` toca sus archivos (al 2026-11-02). Sobre el `main` del día del revert: SIN VERIFICAR.
- `nrt-monitor.yml` vigila las fallas de la sombra; no lo extendí a la guardia (la vigilancia ciega cubre una guardia
  sin datos frescos, pero no un job que falla de punta a punta sin que la vigilancia corra). Recomendado como paso
  aparte.
- La nota en #915 de que el issue semanal saltará con la vía, y el aviso a consumidores (texto en `PR_B_CUERPO.md`),
  los hace la coordinadora o Nicolás.
- La ficha va a v1.18 sobre `main` (v1.17); si otra rama sube la ficha antes, habrá que renumerar.
- D33 aplicado a la vía, y cómo se comporta el far→summit (D11) y la pérdida de Láscar (D12) con la vía: no medidos.
