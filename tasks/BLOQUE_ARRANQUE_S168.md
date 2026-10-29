# Bloque de arranque S168 (cierre de la coordinadora S167, 2026-10-29 ~15:45 UTC)

> **El estado se fijó con trabajo en curso**, y algo puede aterrizar encima de este commit:
> - MOD-D fase 4 (sesión `local_6c14ddd3`): `mutar_evaluar_f4.py --paralelo 2` desde las 12:59 UTC, con los arreglos de
>   E53 y M82 sin commitear en su worktree (`focused-pascal-db1501`). Rama remota todavía en `ff03538dd`.
> - V375-E fase 4 (`local_b1177c51`): `mutar_adenda2.py` desde las 14:09 UTC; cierre del cuerpo del pre-registro sin
>   commitear en `adoring-wright-dc0404` (rama remota en `67838f2a5`).
> - V750-A (Loop VIIRS 750 2, `local_94f4be0d`): medidor completo M3 a M85 sobre 77 escenarios en D:, 2 hilos, ~55 h
>   de equipo despierto (identidad PASA, M1 a M3 atrapadas).
> - Perfil de sombra (`local_b4c997d6`, arrancada 15:42 UTC): mide el costo en el NRT y deja un PR con tag, sin encender.
>
> **Aterrizó después del cierre (17:15 UTC, `date -u`):** V375-E empujó la **adenda 3** (§9 de `PREREGISTRO_E.md`) en
> `e6675da85` (rama `claude/adoring-wright-dc0404`, verificado con `ls-remote`), SIN SELLAR. Según su informe (no
> verificado por la coordinadora): responde VC167-01 a 09 en §9.1 a §9.11; el lector corre la M con
> `evaluador_comun.decidir_estrato` sobre la unión con A104 por tramo; la curva de cenit sale SIN SUSTRATO por
> construcción; batería 165 de 165; mutaciones 113 de 114 atrapadas (L20 equivalente), con las 111 primeras no
> re-corridas con la batería nueva (§9.11 lo dice). Run FAR sin abrir. **Próximo paso de S168:** verificador corto
> sobre `e6675da85`, y sellar sólo si no trae gravedad 3.
>
> Verifica todo antes de creerle a esta tabla. La bitácora viva es `tasks/LOOP_OBJETIVOS.md` §6, vueltas 1 a 23 de S167,
> en la rama `loop/activo`. El estado de cada sensor y el camino a la adopción están en el §12 de
> `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` (en `loop/activo`, no en `main`).

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| Programa por sensor | **ACTUALIZADO** con marcas A113 en §1 a §11 y §12 nuevo (estado y camino a PD4); verificador limpio LISTO CON CAMBIOS, todos aplicados | `ec13d3c34`; `experiments/_s167/verificador_programa/INFORME.md`; `experiments/_s167/digest_sensores.md` |
| Siete decisiones del §12.5 | **APROBADAS** por Nicolás («Sí a todo», 2026-10-29 ~13:40 UTC), con sus condiciones | `bfe691ba7`; programa §12.5 |
| A/B diurno W6 | terminado, cobertura PAREJA (1.593 nocturnas por brazo) | run 40681454167; rama `s151-ab-diurno/40681454167` (`e70c3146a`) |
| Lectura diurna W2 a W6 (adenda 1, e-ii) | **V375 ADOPTAR (b), V750 ADOPTAR (b), global DECIDE NICOLÁS**; verificador CONFIRMADO CON RESERVAS (VD167-01: 13 publicaciones en pasadas no listadas; VD167-02: V375 en el filo, neto 0) | `experiments/_s167/diurno_w2_w6/` (lector y verificador) |
| Las 13 diurnas no listadas | clasificadas: 6 calor volcánico (Villarrica, Chillán), **6 artefacto, todas V375** (4 PCC a 12,7 a 18,2 km, Lastarria, Tupungatito), 1 sin dato. Con eso V375 pasa a caso e (DECIDE CON M4) | `experiments/_s167/diurnas_13/` |
| #813 (día en VIIRS) | **queda ABIERTO**; se retoma con la ROI por volcán decidida (V750-B y C13) | vuelta 23, `49b869c2c` |
| Corrida lejana de V375-E | 350 de 350 pasadas (14 trozos, «sin procesar: 0 de 25»); **sin leer** | run 40773794395; artefactos en `D:\vrp-trabajo\temporales\s167_v375e_far\run_40773794395\` |
| Cuerpo de V375-E (§1 a §7) | **NO sellado todavía**: verificador corto SELLABLE CON CAMBIOS MENORES pero con VC167-04 (gravedad 3: el lector no implementa §4, §5.2, §5.3 ni P-def, P-sinfiltro, PLACEBO) y VC167-01 a 05; la hija los está cerrando | `experiments/_s167/v375e_cuerpo_verificador/INFORME.md` |
| Adenda 3 de V750-B (N-3) | **SELLADA** en `3da2c42f8`, tag `s167-v750b-adenda3-sellada`; dos pasadas del verificador (VA3-01 cerrado) | `experiments/_s167/v750b_adenda3_verificador/INFORME.md` e `INFORME_R2.md` |
| V750-A | N-3 escrita en el borrador (§6 ter, `44ed62768`), sello atado a V750-B; plazos del medidor alargados (`5323d1f3e`) | rama `claude/s162-viirs750-2-918174` (`9a57fea4f`) |
| MOD-D fase 4 | primera corrida final **NO VALE** (control de caída ATRAPADA, M82 CAE); arreglados, segunda corrida en marcha | vuelta 7 y 11 de S167 |
| Disco | C: 27 GB, D: 6,0 GB (15:42 UTC). Dos caídas de C: (37 MB y 1,99 GB): **causa, el archivo de paginación** (40,5 GB, bajó a 25 GB con el reinicio) | vueltas 10, 12 y 14 |
| `main` | `cc66fa57f`: sólo datos del NRT y sync de MIROVA desde `ba61c330f`; nada en `pipeline/` ni `frontend/` | `git diff --stat ba61c330f origin/main -- pipeline/ frontend/` vacío |
| #915 | abierto; se mira en el audit del lunes 2026-11-02 | issue |

## b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Sello de MOD-D fase 4 | ya aprobado con condición | **Aplicarlo** cuando llegue la corrida limpia (mutaciones atrapadas por aserción, control de caída CAÍDA, §13 al día) y pase un verificador corto de los arreglos VF4, E53 y M82 |
| 2 | Sello del cuerpo de V375-E | ya aprobado con condición | **Aplicarlo** sólo cuando la hija cierre VC167-01 a 05 por texto y pase otro verificador corto; recién ahí leer la corrida lejana |
| 3 | Perfil de sombra: encenderlo | sí / no | **Decidir con el PR en la mano** (costo medido en el NRT); nada antes |
| 4 | Cerrar #915 | tras el audit del 2026-11-02 | **Tras el audit**, comprobando que arme la lista aparte de #924 |
| 5 | Tope del archivo de paginación o `powercfg -h off` | de Nicolás (configuración del sistema) | **Fijar un tope** al archivo de paginación: el paralelismo local llegó a comerse 13 GB de C: en media hora |
| 6 | Remapeo de las 59 citas viejas | sesión propia / dejar | **Sesión propia** (pendiente de S166, sin cambios) |
| 7 | Congreso, licencia, política de IA, correo a Coppola | de Nicolás | sin urgencia |

## c. Lo aprendido

Proyecto (enrutar a `CLAUDE.md` o `docs/META_RULES_S80.md` en la próxima revisión):
- **Leer antes de sellar es sellar después de ver.** `leer_posicion_v375e.py` corre controles, posición y el §5 de una
  vez; con el cuerpo sin sellar, la corrida lejana se bajó pero no se leyó. Y un verificador «SELLABLE CON CAMBIOS
  MENORES» puede traer un hallazgo de gravedad 3 (VC167-04, VA3-01): el veredicto no reemplaza leer la gravedad.
- **Un lector nuevo que envuelve a uno sellado tiene que reusar sus compuertas, no reescribirlas** (VA3-01: el lector de
  la adenda 3 se saltaba la compuerta de cobertura de cajas; el arreglo fue cargar el lector sellado y cambiar sólo un
  paso).
- **El balance en el filo cambia con un solo caso fuera de la cuenta**: VIIRS 375 diurno estaba en neto 0 y 13
  publicaciones en pasadas no listadas por MIROVA no entraban a ninguna cuenta (A118 otra vez).

Regla general del workspace:
- **El paralelismo local se paga en disco C:, no sólo en CPU.** Con 31,6 GB de RAM, seis procesos de mutación más un
  medidor y navegadores hicieron crecer el archivo de paginación administrado por Windows unos 13 GB en media hora (C:
  a 1,99 GB); bajó a 25 GB con el reinicio. Máximo 2 procesos pesados en paralelo en este equipo.
- **Un plazo de reloj en un medidor local se come las suspensiones del equipo** y convierte en CAE lo que es tiempo
  dormido; usar plazos holgados o tiempo de CPU.
- **El scratchpad en C:\...\Temp no sirve para insumos de una corrida de días**: la limpieza tras un reinicio borró un
  archivo y el medidor de V750-A cayó en todas las mutaciones. Insumos en D: con su sha.
- **La hora de la bitácora la da el servidor, nunca una estimación** (A86): cinco encabezados «aprox.» de S167 se
  adelantaron hasta 35 min y hubo que corregirlos a la hora del commit.
- **`git worktree remove` lo niega el clasificador** («Irreversible Local Destruction») aunque el worktree esté limpio y
  su commit en `main`; pedir el sí de Nicolás o dejarlo.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: el archivo de paginación causó la caída de C: (40,5 GB antes del reinicio, 25 GB después; C: de 2,3 a
  25 GB sin borrar nada).
- **CONFIRMADO**: la lectura diurna se reproduce idéntica desde dos árboles independientes (salvo la hora de CMR).
- **CONFIRMADO**: la corrida lejana procesó 350 de 350 pasadas (log de los 14 trozos).
- **SOSPECHA**: las clasificaciones de Villarrica y Chillán como calor real se apoyan en coherencia con lo nocturno y con
  MIROVA, sin SWIR. Tupungatito 08-30 tiene una alerta de MIROVA de 0,69 MW esa tarde a distancia compatible: sin
  acimut no se puede decir si es el mismo objeto.
- **SOSPECHA**: los tres `headless_shell` (Playwright) que escribían ~3 MB/s a las 05:3x UTC eran de otra sesión; no se
  identificó cuál.
- **SIN VERIFICAR**: la batería 77 de 77 de V750-A y las cifras de las mutaciones nuevas de MOD-D (según los autores).
- **SIN VERIFICAR** (heredado de S166): que el issue del audit arme bien la lista aparte de #924 en Actions.

## e. Lo que ya está cerrado y no hay que rehacer

- Actualización del programa por sensor y su verificador (`ec13d3c34`); las siete decisiones del §12.5.
- W6 y la lectura diurna W2 a W6 con dos verificadores; la clasificación de las 13 diurnas.
- La corrida lejana de V375-E (no se vuelve a despachar; sólo falta leerla tras el sello del cuerpo).
- Adenda 3 de V750-B sellada con tag.
- Diagnóstico del disco (archivo de paginación).

## f. Prompt para la próxima sesión

```text
Retoma VRP Chile como sesión coordinadora S168 (relevo de S167, cierre del 2026-10-29 ~15:45 UTC). Empieza con la
skill retomar. Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (loop/activo, en el commit del cierre o más nuevo); hora del servidor con gh api -i repos/MendozaVolcanic/VRP-chile |
   grep -i date (A86); df -h /c /d (parada bajo 3 GB). Revisa también el archivo de paginación (ls -la /c/pagefile.sys).
2. Lee CLAUDE.md del proyecto, tasks/BLOQUE_ARRANQUE_S168.md, tasks/LOOP_OBJETIVOS.md §6 (vueltas 1 a 23 de S167) y el
   §12 de docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md.
3. Mira las sesiones vivas con mcp__ccd_session_mgmt__list_sessions y avísales que la coordinadora ahora eres tú:
   MOD-D fase 4 (local_6c14ddd3-bf05-4eeb-8582-9ec601b25c20), V375-E fase 4 (local_b1177c51-d68f-4bd8-83b0-f256e70c85fb),
   Loop VIIRS 750 2 (local_94f4be0d-2b32-4570-b711-3a6f14cc8a0a) y Perfil de sombra
   (local_b4c997d6-0e41-4048-af53-aaed4a2bee3b). Comprueba con Get-CimInstance Win32_Process qué Python siguen vivos.

Trabajo, en orden:
- MOD-D fase 4: recibe el sha de la corrida limpia (control de caída CAÍDA, M82 atrapada, §13 al día), pasa un
  verificador corto limpio de otro modelo sobre los arreglos VF4, E53 y M82, y aplica el sello aprobado (tag). Después,
  candado del §11 y despacho en tandas desde tag.
- V375-E: recibe el cierre del cuerpo (VC167-01 a 05), pasa otro verificador corto, sella con tag y recién ahí lee la
  corrida lejana (run 40773794395, artefactos en D:\vrp-trabajo\temporales\s167_v375e_far\run_40773794395\) con
  leer_posicion_v375e.py (§8.9), con verificador limpio. El veredicto va a Nicolás.
- 2026-11-02: audit semanal; comprueba #915 y la lista aparte de #924; propón cerrarlo.
- 2026-11-03: V750-B (objetivos --hasta 2026-11-02, N-3 contada al generar, sha256, despacho desde tag con los cambios de
  las adendas 2 y 3; lectura con adenda3/leer_n3_v750b.py); consulta C-06 del cese de Suomi NPP en CMR.
- Perfil de sombra: recibe el PR con el costo medido; el encendido pide otro sí de Nicolás con frase que nombre el merge.
- V750-A: el sello espera el medidor completo, la implementación de N-3 con su propio rojo y mutaciones, y V750-B.
- #813 sigue abierto hasta que la ROI por volcán esté decidida (V750-B y C13).
- Corre como loop propio con la skill loop en modo dinámico; anota cada vuelta con date -u y commitea en loop/activo.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y el sí explícito de Nicolás (A45); merge a main sólo con
una frase de Nicolás que nombre el merge y gh pr merge --match-head-commit <sha>; sólo EARTHDATA_TOKEN (A71); despachos
uno a la vez dentro del cupo de 20 jobs, desde tags; verificador limpio de otro modelo antes de aceptar un resultado;
git -c core.autocrlf=false archive para árboles de verificación; git add por archivo; nunca git stash; máximo 2
procesos pesados locales y temporales en D:; la hora de la bitácora es la del servidor; Claude no borra de forma
permanente (y el clasificador niega git worktree remove); español de Chile sin voseo ni guiones largos; rutas
absolutas. Si la sesión no alcanza: commitea, anota en la bitácora qué quedó corriendo y cierra con /cierre.
```
