# Bloque de arranque S174 (cierre de la sesión S173, 2026-11-05 ~16:50 UTC)

> **Estado fijado con trabajo en curso.** Al escribir esto corría el CI del PR #946 sobre la punta `61910c24d`
> (run 42072413315). Verifica su conclusión con `gh run view 42072413315 --json conclusion` antes de creerle a la
> tabla. No quedaron agentes vivos.
>
> **Desde S173 el `CLAUDE.md` es la versión corta (#949).** La historia íntegra de cada regla está en
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\CLAUDE_HISTORIA.md`. Léela antes de reabrir un
> frente cerrado o de citar un número.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| ROI B4 de VIIRS 750 | MERGEADO a main | #939, `58edb9788` |
| Pre-registro retrospectivo (#940) | MERGEADO a main | #940 |
| Filtros de cirrus y difuso eximen la vía «código MIROVA» en el tablero | MERGEADO a main | #944, `91d1bf901` |
| Paper fuera del repo público | MERGEADO a main | #948, `e6dc323b2`; el manuscrito vive en el repo privado `MendozaVolcanic/vrp-chile-paper` |
| CLAUDE.md corto (160.357 a 30.998 caracteres) | MERGEADO a main y traído a `loop/activo` | #949, `83c6de6bb`; `loop/activo` `23be0c830` |
| Parche VPR939-03 sobre la rama de V750 | MERGEADO a `claude/s162-viirs750-2-918174` | #947, `2f1f36272` |
| Seguimiento de #940 (lector de la retrospectiva) | PR #946 en BORRADOR, tres rondas de verificador | punta `61910c24d`; suite 3.232 pasan 0 fallan; R1 y R2 en `experiments/_s173_aud/ver946/` |
| #945 (lector de la sombra de V750-A separa por ROI y `codigo_sha`) | PR en borrador contra main, sin mergear | `gh pr view 945` |
| mirova-tif-archive | ARREGLADO y verificado en producción | checkout parcial + adelgazamiento de PNG; primera captura real `591a3a8dc` (40 PNG, columna `omitido`) |
| Paper de metodología | Repo privado `MendozaVolcanic/vrp-chile-metodologia` | propuesta + mediciones + VMET-01..31 |
| NRT | Produce | commits «NRT update» del 2026-11-05 hasta 14:17 UTC en main |
| Alertas del auto-audit semanal | ABIERTAS, sin investigar | issues #936 (2026-11-02) y #915 (2026-10-26) |
| Worktrees | 6 en `C:\Users\nmend\vrp-wt\` + 2 en `D:\vrp-trabajo\wt\` (`ver946`, `claude-corto`) | 9 terminados a la papelera tras revisarlos; evidencia de verificadores en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\_archivo_VRP_Chile\evidencia_verificadores_S173_ver940b_ver944.zip` |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Merge del #946 | sí / no | Sí, después de las decisiones 2 a 6 y con CI verde. Tres rondas de verificador limpio; la última dejó sólo gravedad 1, ya arreglada. |
| 2 | Lectura del §7 (sorteo de etiquetas, VPR940b-01) | la vía contra K con etiquetas barajadas, rotulado post hoc / la letra actual declarada SIN PODER | La primera: la letra actual no tiene poder (el instrumento ya lo informa). |
| 3 | Records con `sin_grilla` o `sin_mxd03` (VPR940b-04) | tratarlos como K y listarlos como aviso / excluirlos | Tratarlos como K con aviso (no implementado todavía). |
| 4 | Un Tier A sin F26 en K | rojo / aviso | Rojo (así quedó implementado; confírmalo). |
| 5 | Definición de «separa» en V750 | sin valor por defecto hasta sellar V750-A; candidata `PROVISIONAL_d28_s172` | Decidirla al sellar V750-A, no antes. |
| 6 | Tags de origen y campos de los tres comparadores de C-montaje | lista en el cuerpo del #946 | Fijarlos antes del despacho de D3. |
| 7 | Cerrar PR #912 (público, su contenido ya está en el repo privado) | cerrar / dejar | Cerrar. |
| 8 | Ensayo de los controles de cenit con datos reales de DM antes del despacho | sí / no | Sí: su rama real nunca corrió con datos (R2-02 del verificador). |

## c. Lo aprendido

- **Regla general del workspace (memoria `feedback_s173_temporales_compartidos.md`)**: con agentes en paralelo, cada uno usa
  una carpeta temporal propia con su nombre (preferir `D:/vrp-trabajo/temporales/<sesion>-<tarea>`). Un agente que limpió
  «su» temporal borró el de otro y mató una batería de 40 min (#947).
- **Regla general del workspace (memoria `feedback_s173_costo_por_instrucciones.md`)**: el costo fijo de cada mensaje y
  cada subagente es el tamaño de los `CLAUDE.md` cargados. El de VRP Chile había llegado a 160 mil caracteres por las
  marcas A113 acumuladas; se partió en versión operativa + historia íntegra (#949). Una rebaja nueva va a la historia y
  la línea corta se actualiza al estado vigente, sin copiar la marca entera.
- **Trampa de medición (proyecto)**: pruebas que calculan `relpath` entre el temporal y el repo fallan si están en discos
  distintos (`ValueError: path is on mount 'D:'`). g1d y g2c del guard s146. No son regresiones; correrlas con el
  temporal en el mismo disco del repo.
- **Patrón de defecto confirmado otra vez (S169, «caída como acierto»)**: en el #946 un error interno de los controles de
  cenit salía como SIN SUSTRATO y contaba como OK. Lo encontró el verificador limpio en la segunda ronda, no la suite.
- **Un PR sin checks no es verde** (A39 enmienda): el #949 mostró `mergeStateStatus CLEAN` con 0 checks; el run estaba
  en cola. Esperar el run con conclusión.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: el auto-audit semanal salió fuera de banda el 2026-10-26 y el 2026-11-02 (issues #915 y #936). Causa SIN
  INVESTIGAR. SOSPECHA: puede ser el cambio de vía de MODIS (MOD-D en producción desde #934) o ROI B4, que mueven la
  métrica que el audit compara; no verificado.
- **CONFIRMADO**: en `loop/activo` el guard s146 da 5 fallas: 4 ya existían con el CLAUDE.md viejo y la quinta (G2) cita
  `scripts/vigilancia_guardia_modis.py`, que existe en main y no en `loop/activo` (996 commits atrás). En main pasa.
- **CONFIRMADO**: la rama `claude/s162-viirs750-2-918174` tiene `latest_consolidado.csv` de hace 4 días, y por eso su CI
  falla `test_mirova_csv_freshness_f49`. Es dato viejo de la rama, no código.
- **SOSPECHA**: la rama real de `controles_cenit` del #946 nunca corrió con datos (en sintéticos da SIN SUSTRATO). Si
  dará rojo de más con DM real: SIN VERIFICAR.
- **Pendiente sin estado verificado**: cuatro dudas del CLAUDE.md corto marcadas «estado: ver historia» (D21 con K,
  GAP #A con el Test 1 apagado, nota vigente de A85, keep-peak focal de A100).
- Choque de mutaciones M71/M82 en la rama de V750 que bloquea el sello de V750-A: viene de S172, no se tocó en S173.

## e. Lo que ya está cerrado y no hay que rehacer

- mirova-tif-archive: el job ya no se queda sin disco; el push con checkout parcial y el adelgazamiento funcionan en
  producción (`591a3a8dc`). No reabrir salvo que lleguen correos de falla nuevos.
- El silencio de MIROVA del 2026-11-04 terminó (volvió a publicar ~06:51 UTC del 11-05).
- Los hallazgos de gravedad 2 y 3 de ver940, ver940b, ver944 y ver946 (R1 y R2) están arreglados en sus PR.
- El «11,44 MW» de S173 era el control X2 del verificador, no una alerta (corregido en `experiments/_s173_cenit/README.md`).
- Los temporales de S171 y anteriores se rescataron en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\_archivo_VRP_Chile\temporales_S171_y_anteriores_rescate.zip`
  antes de ir a la papelera.
- `cleanupPeriodDays` quedó en 3650 en `C:\Users\nmend\.claude\settings.json`; los transcripts hasta el 2026-11-05 están
  en `C:\Users\nmend\OneDrive\Escritorio\claude\_respaldo_transcripts_claude\transcripts_2026-11-05.zip`.

## f. Prompt para la próxima sesión

```
Sesión S174 de VRP Chile (coordinadora del programa de réplica por sensor). Carpeta:
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo.

1. Verifica antes de creer: git fetch origin --prune; git status -sb; compara git rev-parse HEAD con
   git ls-remote origin -h refs/heads/loop/activo; date -u. Mira el CI del #946
   (gh run view 42072413315 --json conclusion y gh pr checks 946) y df -h /c /d.
2. Lee en orden: CLAUDE.md (versión corta; la historia está en docs/CLAUDE_HISTORIA.md),
   tasks/BLOQUE_ARRANQUE_S174.md, la bitácora §6 de tasks/LOOP_OBJETIVOS.md (las 6 entradas más nuevas).
3. Trabajo, en este orden:
   a) Investigar las alertas del auto-audit semanal #936 y #915 (systematic-debugging: qué métrica salió de banda,
      desde cuándo, si coincide con #934 MOD-D o #939 ROI B4). Reportar a Nicolás antes de tocar nada.
   b) Presentar a Nicolás las decisiones 1 a 8 del bloque (cada una con la recomendación) y, con su frase, mergear
      #946 con --match-head-commit.
   c) Llevar el #945 a main (revisar su estado, verificador limpio si no lo tiene).
   d) Resolver contra el código las cuatro dudas «estado: ver historia» del CLAUDE.md corto (D21, GAP #A, A85, A100)
      y actualizar las líneas cortas (la historia no se toca).
   e) Destrabar el sello de V750-A (choque M71/M82 en la rama de V750).
   f) Preparar la auditoría de MOD-D del 2026-11-09; recordar la rotación de EARTHDATA_TOKEN del 2026-11-27.
4. Reglas duras: pipeline/ congelado durante la sombra (excepciones: ROI de V750, emergencias del NRT, encendido de
   MODIS decidido, AGREGAR entradas a pipeline/grillas_mirova.yaml para los 34); nada en pipeline/, data/ ni frontend/
   sin tag y sí de Nicolás (A45); merge a main sólo con frase de Nicolás y gh pr merge --match-head-commit; sólo
   EARTHDATA_TOKEN (A71); despachos de a uno desde tags; verificador limpio de otro modelo antes de aceptar un
   resultado; esfuerzo explícito (high) a cada agente y carpeta temporal propia con su nombre en D:; máximo 2 procesos
   pesados locales y parada bajo 3 GB libres en C: o D:; worktrees nuevos en D:; git add por archivo; nunca git stash;
   date -u antes de cada encabezado de bitácora; un PR sin checks no es verde; papelera, nunca borrado definitivo.
5. Si la sesión no alcanza (contexto sobre 50 %): commitea, anota en la bitácora qué quedó corriendo, escribe
   tasks/BLOQUE_ARRANQUE_S175.md con el prompt de la siguiente y lanza la siguiente sesión.
```
