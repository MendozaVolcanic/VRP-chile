# Bloque de arranque S169 (cierre de la coordinadora S168, 2026-10-29 23:21 UTC)

> **El estado se fijó con trabajo en curso**, y algo puede aterrizar encima de este commit:
> - V375-E (sesión `local_438070ff`, rama `claude/s168-v375e-sello`): la lectura lejana terminó (`7a548be11`, salida
>   cruda) y su verificador corre en local desde las 20:59 UTC (PID 15924, `leer_posicion_v375e.py` con salida a
>   `D:/vrp-trabajo/temporales/s168_ver_lectura/`). Instrucción dada: dejar el veredicto con `INFORME.md` en su rama.
> - MOD-D fase 4 (sesión `local_5b198297`, rama `claude/s168-modd-f4-sello`): sellado; arma el candado del §11 con un
>   solo proceso pesado, que se abre cuando termine el PID 15924; después las mutaciones reformadas (~9 h en serie,
>   según la sesión). Sin merge ni despacho. Instrucción dada: entregar por su rama con `INFORME.md`.
> - V750-A (sesión `local_94f4be0d`, otra familia): medidor `mutar_evaluar_v750a.py` (PID 1324, 2 hilos), ~55 h desde
>   el 2026-10-29 13:46 UTC.
>
> Ninguna de esas sesiones tiene coordinadora viva que la escuche: S169 las encuentra con `git ls-remote` y les escribe
> con `SendMessage` (ids arriba). Bitácora viva: `tasks/LOOP_OBJETIVOS.md` §6, vueltas 1 a 8 de S168, rama `loop/activo`.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| Sombra del código MIROVA | **ENCENDIDA**: #926 mergeado (squash `c42ee0eb7`, frase «Sí, mergea #926», `--match-head-commit f48fcbe7c`, CI `pytest` verde); cron diario 15:00 UTC, workflow `active` | tag `pre-s168-encender-sombra` (`ba3788279`); `gh api .../workflows/sombra-codigo-mirova.yml` |
| Despacho `medir=true` de la sombra | leído: 77 de 77 records de la vía, 0 errores; MODIS 1 de 17 con calor (Aqua 26-oct, 0,184 MW, la misma pasada que la alerta de MIROVA de 0,29 MW según el verificador), VIIRS 750 0 de 32 (MIROVA 0), VIIRS 375 28 con el log ciego; job 907 s (8 días) | run 40945613044; `experiments/_s168/sombra_run_40945613044/` (`INFORME.md`, `VERIFICADOR.md`: CONFIRMADO CON RESERVAS) |
| MOD-D fase 4 | **SELLADO**: tag `s168-modd-f4-sellado` en `3768e9431`; VS-02 aceptado por Nicolás («Sí, acéptala») | `ls-remote`; `experiments/_s168/modd_f4_verificador/INFORME.md` en la rama de MOD-D |
| Candado del §11 de MOD-D | en curso, sin tag | sesión `local_5b198297` |
| V375-E | cuerpo y adenda 3 sellados (`s168-v375e-cuerpo-sellado`, `444d5d888`); **lectura lejana hecha, sin verificar**: posición ELEGIDO CERCANO, M MEJORA en los tres brazos, §5.3 SIN SUSTRATO, §5.4 retrospectiva cercano CUMPLE (falta la sombra), PAQUETE CUMPLE (falta la sombra) | `7a548be11`, `experiments/_s168/v375e_lectura_lejana/lectura_salida.txt` (exit=0, 19:57 a 20:56 UTC) |
| V750-A / V750-B | medidor corriendo; V750-B se despacha el 2026-11-03 con la adenda 3 sellada | PID 1324; bloque S168 |
| `main` | `443da8649`: desde `c42ee0eb7` sólo datos (nada en `pipeline/`, `frontend/`, `.github/`) | `git diff --stat c42ee0eb7 origin/main -- pipeline/ frontend/ .github/` vacío |
| Disco y memoria | C: 21 GB, D: 5,7 GB; archivo de paginación en `C:\pagefile.sys`, 4,0 de 25,6 GB en uso | `df -h`; `Win32_PageFileUsage` |
| #915, #813, #912, #913 | abiertos | `gh issue list` |

## b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Veredicto de V375-E (lectura lejana) | adoptar el brazo cercano a la sombra / esperar | **Esperar el verificador** de la sesión V375-E; si confirma, el paso que falta es §5.4 (d) con la sombra desde el 2026-11-03, no una adopción hoy |
| 2 | Cerrar #915 | tras el audit del 2026-11-02 | **Tras el audit**, comprobando que arme la lista aparte de #924 |
| 3 | Merge del workflow del candado de MOD-D (el humo de ~25 pasadas sólo se despacha desde `main`) | sí / no | **Sí cuando el candado tenga tag y verificador limpio**; workflow aparte, sólo `workflow_dispatch` |
| 4 | Remapeo de las 59 citas viejas | sesión propia / dejar | **Sesión propia** (sin cambios desde S166) |
| 5 | Congreso, licencia, política de IA, correo a Coppola | de Nicolás | sin urgencia |

## c. Lo aprendido

Proyecto (enrutar a `docs/META_RULES_S80.md` o `CLAUDE.md` en la próxima revisión):
- **Un costo se mide en el modo en que va a correr.** Estimé el job diario de la sombra a partir de un despacho de 8
  días suponiendo que el modo programado corría 1 día; `ventana_sombra.py` usa 8 (lookback 7). El verificador lo
  marcó gravedad 3. Leer la ventana del modo programado antes de escalar un costo.
- **Un log puede estar ciego para un camino nuevo.** La línea de VIIRS 375 de `run_pipeline.py` imprime campos que el
  record de la vía no llena (`vrp_mir_mw`, `t_max_i04_k`): sale `None` haya o no detección. Y `medir=true` no guarda
  los records. Una corrida de medición que no deja records sólo prueba la plomería.

Regla general del workspace:
- **En el loop, la coordinadora no pregunta cada paso** (Nicolás, S168): prepara, prueba y verifica sola; le lleva sólo
  las compuertas (merge, encender, A45, reglas selladas) con el trabajo hecho. Memoria `feedback_s168_loop_no_preguntar`.
- **Un PR se puede armar sin checkout**: índice temporal (`GIT_INDEX_FILE`), `read-tree`, `hash-object -w`,
  `update-index --cacheinfo`, `write-tree`, `commit-tree`, `push <sha>:refs/heads/<rama>`. No toca el árbol de trabajo
  ni cambia de rama.
- **En un `python - <<'EOF'` con f-string, una ruta de Windows se rompe** (`\v`, `\t` se vuelven caracteres de
  control). Escribir rutas con `/` o en cadenas crudas.
- **`Get-Item C:\pagefile.sys` puede no ver el archivo de paginación**; `Get-CimInstance Win32_PageFileUsage` sí.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: la vía corre en gránulos reales de los tres sensores (77 de 77, run 40945613044).
- **CONFIRMADO** (verificador de la sombra): 4 gránulos de VIIRS 375 no dejan record y nada lo avisa; 3 no contienen el
  volcán según CMR, el cuarto SIN VERIFICAR.
- **SOSPECHA**: que los ceros de MODIS y VIIRS 750 de la sombra sean «miró y no vio»; el motivo está en el JSON, que el
  modo diario sí guardará desde el 2026-11-03.
- **SIN VERIFICAR**: la lectura lejana de V375-E (su verificador corre).
- **SIN VERIFICAR**: el tiempo de las mutaciones reformadas de MOD-D (~9 h, según la sesión).

## e. Lo que ya está cerrado y no hay que rehacer

- Lectura y verificador del despacho `medir=true` de la sombra; el encendido (#926).
- El sello de MOD-D fase 4 y la aceptación de VS-02.
- La corrida lejana de V375-E y su lectura cruda con el lector sellado (sólo falta el verificador).

## f. Prompt para la próxima sesión

```text
Retoma VRP Chile como sesión coordinadora S169 (relevo de S168, cierre del 2026-10-29 23:21 UTC). Empieza con la
skill retomar. Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (loop/activo); hora con date -u (A86); df -h /c /d (parada bajo 3 GB en D:); Get-CimInstance Win32_PageFileUsage.
2. Lee CLAUDE.md del proyecto, tasks/BLOQUE_ARRANQUE_S169.md, tasks/LOOP_OBJETIVOS.md §6 (vueltas de S168) y el §12 de
   docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md (rama loop/activo).
3. git ls-remote origin 'refs/heads/claude/s168-*' 'refs/tags/s168-*' 'refs/tags/s169-*' y lee el INFORME.md que hayan
   dejado V375-E (claude/s168-v375e-sello) y MOD-D (claude/s168-modd-f4-sello). Comprueba con Get-CimInstance
   Win32_Process qué Python siguen vivos (máximo 2 pesados). Escríbeles con SendMessage que ahora reportan a S169:
   V375-E local_438070ff-f989-4fa6-8da9-dc3d9f78a1f4, MOD-D local_5b198297-ad3f-4aca-850a-c5dd3d856b80,
   V750 local_94f4be0d-2b32-4570-b711-3a6f14cc8a0a.

Trabajo, en orden:
- V375-E: con el veredicto del verificador de la lectura lejana, si no trae gravedad 3, llévale a Nicolás el resultado
  con recomendación (lo que falta es §5.4 (d) con la sombra desde el 2026-11-03).
- MOD-D: cuando el candado del §11 tenga tag, verificador limpio de otro modelo; si pasa, pídele a Nicolás la frase
  para mergear el workflow del humo (sólo workflow_dispatch) y despacha el humo desde tag.
- 2026-11-02: audit semanal; comprueba #915 y la lista aparte de #924; propón cerrarlo.
- 2026-11-03: V750-B (objetivos --hasta 2026-11-02, N-3 contada al generar, sha256, despacho desde tag con las adendas
  2 y 3; lectura con adenda3/leer_n3_v750b.py); consulta C-06 del cese de Suomi NPP en CMR. Ese día a las 15:00 UTC
  corre la primera sombra con datos: comprueba que commitee data/sombra_codigo_mirova/ y que revisar_sombra.py deje
  los 11 jobs verdes.
- #813 sigue abierto hasta que la ROI por volcán esté decidida (V750-B y C13).
- Corre como loop propio con la skill loop en modo dinámico; avanza y prueba sin preguntar cada paso, y lleva a
  Nicolás sólo las compuertas (merge, encender, A45, reglas selladas) con el trabajo hecho. Anota cada vuelta con
  date -u y commitea en loop/activo.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y el sí explícito de Nicolás (A45); merge a main sólo con
una frase de Nicolás que nombre el merge y gh pr merge --match-head-commit <sha>; sólo EARTHDATA_TOKEN (A71); despachos
uno a la vez dentro del cupo de 20 jobs, desde tags; verificador limpio de otro modelo antes de aceptar un resultado;
git -c core.autocrlf=false archive para árboles de verificación; git add por archivo; nunca git stash; máximo 2
procesos pesados locales y temporales en D:; rutas de Windows con / en scripts; la hora de la bitácora es la del
servidor; Claude no borra de forma permanente; español de Chile sin voseo ni guiones largos; rutas absolutas. Si la
sesión no alcanza: commitea, anota en la bitácora qué quedó corriendo y cierra con /cierre.
```
