# Informe del implementador: los dos PR del encendido de la vía «código MIROVA» en MODIS (S172)

Fecha: 2026-11-01 (hora del servidor, 2026-11-02 UTC al cerrar). Diseño implementado:
`docs/superpowers/specs/2026-11-01-encendido-modd-design.md` (`d24fda8f3`). Regla:
`experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` (rama `loop/activo`, sin sellar). Worktree
`D:/vrp-trabajo/worktrees/s172-modd-encendido`. No se abrió PR, no se mergeó nada, no se despachó ningún workflow ni se
creó ningún tag. Las dos ramas están empujadas a `origin`.

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
