# Bloque de arranque S167 (cierre de la coordinadora S166, 2026-10-28 ~12:55 UTC)

> El estado se fijó **con trabajo en curso**:
> - W6 del A/B diurno (run 40681454167): 4 jobs en verde, 3 corriendo, 15 en cola a las 12:50 UTC.
> - MOD-D fase 4 (sesión `local_6c14ddd3`) corre sus mutaciones finales sobre `ff03538dd` (unos 40 min).
> - Loop VIIRS 750 2 (`local_94f4be0d`) tiene el medidor de V750-A vivo y los arreglos VP-01 a VP-03 sin commitear.
>
> Verifica las tres cosas antes de creer esta tabla. La bitácora viva es `tasks/LOOP_OBJETIVOS.md` §6 (vueltas 1 a 22
> de S166), en la rama `loop/activo`. Las sesiones hijas pueden caer con «401 OAuth access token has expired» tras
> muchas horas; sus procesos de fondo siguen vivos, pero sólo vuelven cuando Nicolás les escribe en la app.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| #920, #921 y #922 no cambian records | **COMPROBADO en los tres sensores** | NRT: 12 records MODIS reescritos con el código nuevo, mismos campos, 0 con la vía (`experiments/_s166/nrt_campos_s166.py`). Bit a bit run 40683093630: VERDE en VIIRS 375 y 750, 44 records por lado, con control ROJO y detecciones reales (`experiments/_s166/bitabit_40683093630/`) |
| #923 (probe del bit a bit) | **mergeado** `34de58c29` | frase de Nicolás «Apruebo los dos», `--match-head-commit 79d93cace` |
| #924 (audit: referencia sospechosa aparte, pérdida aceptada de PCC V750 10-10) | **mergeado** `ba61c330f` | mismo; suite 2738 passed, CI verde. El punto 2 («mismo objeto») salió del PR |
| A/B diurno sobre K (D-10) | W1 a W5 **parejas**; **W6 corriendo** (40681454167) | W4: 2.266 por brazo; W5: 2.386 por brazo; 0 faltan y 0 sobran (vueltas 6 y 17) |
| V750-B | sellado; **adenda 2 SELLADA** en `739edff39`, anexada en `609fa1c88`, tag `s162-v750b-adenda2-sellada` | batería 40 de 40 y mutaciones 33 de 33 en árbol propio de S166 (vuelta 2) |
| V750-A (tres brazos de posición) | borrador en `58d62bd8f`; verificador LISTO CON CAMBIOS (VP-01 a VP-03), **arreglos sin commitear** | mensaje de Loop VIIRS 750 2, 12:10 UTC |
| V375-E adenda 2 (brazos de posición, 330 lejanas) | **SELLADA** en `67838f2a5`, tag `s166-v375e-adenda2-sellada`; N-3 aplicado; vara nueva del paso 1 aceptada | batería 140 de 140 corrida por S166 en árbol LF de D: (vuelta 22) |
| Corrida de lejanas de V375-E | **sin despachar**; espera que termine W6 (cupo de 20 jobs) | §8.8 de `PREREGISTRO_E.md` en el tag |
| MOD-D fase 4 (pre-registro) | rama `claude/s166-modd-f4`, último `ff03538dd` (arreglos VF4-01 a 12, batería 53); mutaciones finales corriendo | mensaje de la sesión, 12:20 UTC |
| Censo A113 de citas tras #919 a #922 | hecho; 1 cita corrida remapeada (`MIROVA_DIVERGENCES.md` l. 1487, 1876 a 1908) | `experiments/_s166/CENSO_CITAS_A113.md`; quedan 59 citas viejas de antes |
| #915 | **abierto**; con #924 sus dos alertas de Tupungatito y la de PCC ya no levantan flag | se ve en el audit del lunes 2026-11-02 |
| Disco | C: 18 GB, D: 7,0 GB (12:50 UTC) | `df -h`; se liberaron unos 13 GB archivando sesiones terminadas |

## b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Sello del pre-registro de MOD-D fase 4 cuando llegue con sus mutaciones | sellar / pedir cambios | **Sellar** si las mutaciones salen atrapadas por aserción y un verificador corto revisa los arreglos VF4 |
| 2 | Sello de V750-A con los tres brazos, tras VP-01 a VP-03 | sellar / esperar el medidor completo | **Esperar el medidor completo sobre los 74 escenarios** antes de sellar: las 18 mutaciones nuevas sólo se probaron contra los 13 escenarios nuevos |
| 3 | «Mismo objeto» en la magnitud por noche del audit (§b 2 de S166) | criterio medido / dejarlo | **Dejarlo hasta tener un criterio medido contra la referencia** (separación en noches donde los dos son cumbre). El corte por `inner_radius_km` no corrige PCC y la exclusión por Suomi NPP escondía una bandera real de Chillán |
| 4 | Cerrar #915 | cerrar ya / tras el audit del 2026-11-02 | **Tras el audit del lunes**: comprobar en el issue real que las protegidas aparte salen bien armadas (SIN VERIFICAR en Actions) |
| 5 | Remapear las 59 citas viejas (51 de `MIROVA_DIVERGENCES.md`, 6 de `MISSION.md`, 2 de `SINTOMAS.md`) | sesión propia / dejar | **Sesión propia**, por contenido (A101), con la lista «no tocar» del censo |
| 6 | Encender vías o flags (V750, MODIS, V375, MxD03, «sin dato») | no / con reproceso | **No**, hasta los A/B de fase 4 |
| 7 | Congreso, licencia, política de IA de la revista, correo a Coppola | de Nicolás | sin urgencia |

## c. Lo aprendido

Proyecto (por enrutar a `CLAUDE.md` o `docs/META_RULES_S80.md` en la próxima revisión):
- **Un criterio de «mismo objeto» por radio de cumbre no sirve en volcanes de radio grande.** PCC tiene
  `inner_radius_km` 20: dos objetos a 10,7 km quedan «iguales». Y excluir las noches de Suomi NPP OCR por su distancia
  escondía una bandera real de Chillán en erupción, donde el VRP sí era de su pasada. Un corte en km sin medir contra la
  referencia es A115.
- **Un bit a bit verde vale si hay sustrato y si el comparador puede dar rojo.** Antes de creerle, contar detecciones
  reales en los dos lados (Villarrica no tuvo ninguna ese día) y correr el control (`--control` da ROJO).
- **Las protegidas sólo OCR de Suomi NPP anteriores al 2026-10-09 se tratan igual en el audit y en los pre-registros**:
  se informan aparte y no deciden (decisión de Nicolás, S166).

Regla general del workspace:
- **`git archive` en Windows sale en CRLF** si `core.autocrlf=true`; los sha256 no calzan y los analizadores sellados
  se niegan a correr. Usar `git -c core.autocrlf=false archive`. Refuerza `feedback_s163_md5_y_autocrlf`.
- **La papelera de Windows no libera disco.** Para liberar espacio: archivar sesiones terminadas (la app limpia su
  worktree) o `git worktree remove` sobre un worktree limpio cuyo trabajo está en el remoto. Revisar antes
  `git status --porcelain --ignored`.
- **Una sesión de la app cae con «401 OAuth access token has expired» después de muchas horas.** Sus procesos de fondo
  siguen; un SendMessage no la despierta; vuelve cuando el usuario le escribe en la app.
- **El clasificador acepta el merge cuando la aprobación nombra el merge** («Apruebo los dos» respondiendo a la pregunta
  que traía los dos sha), y lo niega con una aprobación genérica («continúa con todo lo que recomiendes»). Siempre con
  `--match-head-commit`.
- **Crear una rama desde `main` sin cambiar de rama**: `GIT_INDEX_FILE=<tmp> git read-tree origin/main`, `git
  update-index --add --cacheinfo`, `git write-tree`, `git commit-tree`, `git push origin <sha>:refs/heads/<rama>`.
- **Una batería que corre desde un checkout no corre desde un árbol extraído sin todas sus dependencias**: hubo que
  extraer `experiments/` y `tests/` enteros (385 MB) y apuntar `GIT_DIR` al repo.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: #920 a #922 no cambian records (NRT MODIS más bit a bit de un día en los tres sensores).
- **CONFIRMADO**: con la regla de posición de hoy, V375 calla 4 protegidas (Isluga 06-17, 09-28 y 10-03; Láscar 10-01).
  Con N-3, Isluga 09-28 y 10-03 (Suomi NPP OCR) ya no vetan; Isluga 06-17 y Láscar 10-01 (NOAA-21) sí.
- **SIN VERIFICAR**: que el issue del audit arme bien la lista aparte en GitHub Actions (sólo se probó la línea de Python).
- **SOSPECHA**: la caída de C: del 2026-10-27 al 28 (de 23 a 4,6 GB) no se explica entera por VRP; la carpeta temporal de
  Windows pesa 8,3 GB, sin dueño identificado.
- **SIN VERIFICAR**: el nulo de V375-E en LF da 82 de 84 (L42 depende del CRLF del checkout), según el autor.

## e. Lo que ya está cerrado y no hay que rehacer

- Comprobación de #920 a #922 (NRT y bit a bit). No se repite.
- Merges de #923 y #924.
- Sellos de la adenda 2 de V750-B y de la adenda 2 de V375-E.
- W1 a W5 del A/B diurno, con cobertura pareja.
- §b 1 y §b 3 del bloque S166 (Suomi NPP OCR aparte; pérdida aceptada de PCC V750 10-10), en `main` con #924.
- Censo A113 tras #919 a #922; la única cita corrida ya está remapeada.
- Archivadas las sesiones mxd03 (#920), V375-E vía (#921) y MOD-D fase 3 (#919).

## f. Prompt para la próxima sesión

```text
Retoma VRP Chile como sesión coordinadora S167 (relevo de S166, cierre del 2026-10-28 ~12:55 UTC). Empieza con la
skill retomar. Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (loop/activo, en el commit del cierre o más nuevo); hora del servidor con gh api -i repos/MendozaVolcanic/VRP-chile |
   grep -i date (A86); df -h /c /d (parada bajo 3 GB).
2. Lee CLAUDE.md del proyecto, tasks/BLOQUE_ARRANQUE_S167.md y tasks/LOOP_OBJETIVOS.md §6 (vueltas 1 a 22 de S166).
3. Mira las sesiones vivas con mcp__ccd_session_mgmt__list_sessions y ListAgents, y avísales que la coordinadora ahora
   eres tú: Loop VIIRS 750 2 (local_94f4be0d-2b32-4570-b711-3a6f14cc8a0a), MOD-D fase 4
   (local_6c14ddd3-bf05-4eeb-8582-9ec601b25c20) y V375-E fase 4 (local_b1177c51-d68f-4bd8-83b0-f256e70c85fb, ya
   entregó). Si alguna cayó con «401 OAuth access token has expired», pídele a Nicolás que le escriba en la app.

Trabajo, en orden:
- W6 del A/B diurno (run 40681454167): cuando termine, lee experiments/_s151_ab_diurno/salidas/40681454167/cobertura.txt
  en la rama s151-ab-diurno/40681454167. Después, la lectura con dias_excluidos_nasa.py y evaluar_con_exclusion.py
  (--opcion-e e-ii), desde un git -c core.autocrlf=false archive del commit sellado, con verificador limpio de otro
  modelo. El veredicto va a Nicolás.
- Corrida de pasadas lejanas de V375-E, después de W6: desde el tag s166-v375e-adenda2-sellada, copia
  experiments/_s162_v375/e_adenda2/probe-s166-v375e-far.yml a .github/workflows/ en la rama s166-v375e-far-disparo
  (no se mergea) y empuja (§8.8 de PREREGISTRO_E.md). Cuenta en el log que procesó tantas pasadas como pidió (A108).
- MOD-D fase 4: recibe el sha final con mutaciones, pasa un verificador corto sobre los arreglos VF4 y llévaselo a
  Nicolás para el sello (§b 1).
- V750-A: recibe los arreglos VP-01 a VP-03 y el medidor completo; el sello espera al medidor sobre los 74 escenarios
  (§b 2).
- 2026-11-02: audit semanal; comprueba que #915 o su sucesor arme la lista aparte de #924 y propón cerrarlo (§b 4).
- 2026-11-03: objetivos de V750-B (--hasta 2026-11-02, sha256, tag) y despacho con los tres cambios de la adenda 2
  (§7 y §8 de ADENDA2_V750B.md); la consulta C-06 del cese de Suomi NPP contra CMR.
- Pídele a Nicolás las decisiones del §b, con la recomendación.
- Corre como loop propio con la skill loop en modo dinámico; anota cada vuelta con date -u y commitea en loop/activo.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y el sí explícito de Nicolás (A45); un merge a main sólo con
una frase de Nicolás que nombre el merge y gh pr merge --match-head-commit <sha> (una aprobación genérica no basta);
sólo EARTHDATA_TOKEN (A71); despachos uno a la vez dentro del cupo de 20 jobs (NRT usa 11), desde tags; verificador
limpio de otro modelo antes de aceptar un resultado; git -c core.autocrlf=false archive para árboles de verificación;
git add por archivo; nunca git stash; un fetch por comando o refspec explícito; la papelera no libera disco; Claude no
borra de forma permanente; texto con barras invertidas con Edit, no con heredoc; español de Chile sin voseo ni guiones
largos; rutas absolutas. Si la sesión no alcanza: commitea, anota en la bitácora qué quedó corriendo y cierra con
/cierre.
```
