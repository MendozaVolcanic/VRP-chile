# Bloque de arranque S166 (cierre de la coordinadora S165, 2026-10-27 ~23:25 UTC)

> El estado se fijó **con trabajo en curso**: W4 del A/B diurno (run 40545948109) seguía corriendo, con 16 de 22 jobs
> en verde y 6 en cola. Además, Loop VIIRS 750 2 podía estar escribiendo la adenda 2 de V750-B en su rama. Verifica las
> dos cosas antes de creer esta tabla. La bitácora viva es `tasks/LOOP_OBJETIVOS.md` §6 (vueltas 1 a 14 de S165), en la
> rama `loop/activo`.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| Vías «código MIROVA» por sensor (fase 3) | **en `main`, las tres APAGADAS**: VIIRS 750 (#907, S164), MODIS (#919, `d94f25191`), VIIRS 375 (#921, `bd711db63`) | merges por orden de Nicolás; arnés S142 idéntico byte a byte antes de cada merge (bitácora vueltas 4, 8, 11) |
| MxD03 en MODIS (MOD-B) | **en `main`, tres flags APAGADOS** (#920, `ab3ff9fe3`) más V165-03, la pasada «sin dato» como incidencia (#922, `7a17af8c4`) | probe de equivalencia run 40584157486: 18 de 18 iguales al brazo X de MOD-B con el flag encendido y 18 de 18 iguales a K apagado (vuelta 12) |
| Integración `loop/activo` a `main` | **hecha** (#918, `cc16b3a7f`, merge commit); `main` vuelve a `loop/activo` en cada vuelta | `git rev-list origin/main..origin/loop/activo` era 0 tras #918 |
| A/B diurno sobre K (D-10) | W1, W2 y W3 **terminadas con cobertura pareja**; **W4 en curso** (run 40545948109, 2026-08-13 a 08-31); faltan W5 y W6 | W2: 2.154 pasadas por brazo, 0 faltan; W3: 1.429, 0 faltan (vueltas 1 y 7) |
| Regla de posición (radiante contra cercano) | **medida y verificada**. Nicolás decidió medirla como brazo (radiante, cercano y pico) en los A/B de cada sensor | `experiments/_s165_regla_posicion/INFORME.md` y `verificador/INFORME.md`; `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §7 |
| #915 (auto-audit fuera de banda) | **clasificado entero**, issue abierto | Chillán MODIS: vuelta 1 (MOD-D recupera 2 de 3); resto: `experiments/_s165_issue915/INFORME.md` |
| D-39 (scraper Mirova-v1 perdía filas) | **cerrado** por Nicolás (Mirova-v1#26, `7f4ea069b`); el consolidado ganó 2.648 filas el 2026-10-27 a las 12:41 UTC (A90) | sync de VRP Chile verde, run 40505762684 (vuelta 4) |
| Medidor de V750-A | **completo**: 62 de 62 mutaciones atrapadas por aserción | `origin/claude/s162-viirs750-2-918174` `ac0987fc4` (vuelta 3) |
| V750-A y V750-B con los tres brazos de posición | **en curso** en Loop VIIRS 750 2: brazos en el borrador de V750-A (sin sellar) y adenda 2 de V750-B (sellado), con lista suplementaria de pasadas lejanas | mensaje de S165 a esa sesión, 2026-10-27 ~22:30 UTC |
| NRT | verde en todas las corridas del 2026-10-27; **todavía ninguna con #920, #921 y #922 en el código** (la próxima es a las 01:10 UTC) | `gh run list --workflow nrt.yml` |
| Disco | C: 23 GB, D: 7,5 GB (23:22 UTC) | `df -h` |

## b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | ¿El auto-audit sigue marcando alertas que vienen sólo del OCR de Suomi NPP anteriores al 2026-10-09? | seguir / excluirlas e informarlas aparte | **Excluirlas e informarlas aparte**: en #915 las dos de Tupungatito eran problema de la referencia (la distancia venía de otra pasada), no FN |
| 2 | ¿La magnitud por noche del audit exige que nuestro máximo y el de MIROVA sean el mismo objeto? | no / sí | **Sí**: sin eso, en PCC y Tupungatito se mezclan objetos distintos y la razón sale baja de más (0,517 y 0,618 sin esas noches) |
| 3 | ¿Registrar como pérdida aceptada la de PCC VIIRS 750 del 2026-10-10 (lacolito, ya cerrada sin cambiar K en #865 y #881)? | sí / no | **Sí**, para que no reaparezca en cada audit |
| 4 | Sellar la adenda 2 de V750-B (lista suplementaria de pasadas en que MIROVA publicó una fuente lejana, ids desde 100000, los 5.781 sellados intactos) | sellar antes del 2026-11-03 / despachar V750-B tal como está | **Sellarla** cuando llegue con su verificador; si no alcanza, despachar lo sellado y medir las lejanas aparte |
| 5 | Encender alguna vía o flag (V750, MODIS, V375, MxD03, «sin dato», distancia desde el cráter) | no por ahora / con reproceso verificado | **No por ahora**: primero los A/B de fase 4 con los tres brazos de posición; «sin dato» deja fuera 223 de 5.465 pasadas, una de ellas alerta bajo 1 MW (Villarrica 2026-09-25 08:05); la distancia desde el cráter publica de más en PCC |
| 6 | Mazos del congreso, política de IA de la revista (PDF en jvolcanica.org con anti-robot; «internal use only» del 2026-08-12 es SIN VERIFICAR) y licencia del repo | de Nicolás | sin urgencia de este lado |
| 7 | Correo a Coppola | en espera | seguir esperando |

## c. Lo aprendido

Proyecto (se enruta a `CLAUDE.md` o `docs/META_RULES_S80.md` en la próxima revisión; por ahora vive aquí y en la memoria):
- **Comprobar la identidad de un PR con un instrumento propio, no con el del autor.** Antes de cada merge de una vía
  apagada, se corrió el arnés S142 entero con `git archive` del tag (o de `main`) y de la rama, y se comparó con `cmp`.
  Cuesta unos 2 minutos y da evidencia independiente del golden que trae el PR. Fue así en #919, #920, #921 y #922.
- **Varios PR desde el mismo tag chocan en los documentos compartidos** (versión de la FICHA SDA, citas de `CLAUDE.md`,
  guard G8, `profile.py`). Hay que fijar el orden de merge, y el segundo hace merge de `main`, vuelve a correr la suite
  y se re-verifica. La cita de A100 se remapeó tres veces en un día (1172, 1259, 1350, 1356): cada PR que toca
  `process_modis.py` la mueve (A101).
- **La regla de posición de la vía no es la de MIROVA, y tampoco está probada la contraria.** La distancia de la tabla
  de MIROVA calza mejor con el píxel pico que con el centroide del cúmulo. Antes de fijar una regla de posición, medir
  los tres candidatos contra lo que publica MIROVA, incluidas las pasadas en que publicó una fuente lejana.

Regla general del workspace:
- **Dos `git fetch` en el mismo comando pisan `FETCH_HEAD`.** Un diff contra `FETCH_HEAD` después del segundo fetch
  compara contra la rama equivocada, sin error. Usar refspecs explícitos a `refs/remotes/...` o un fetch por comando.
- **El clasificador de modo automático niega mergear sin revisión humana**, aunque la aprobación venga reenviada por otra
  sesión. Lo que funciona es la frase del dueño en este mismo chat, con el sha («Apruebo el merge de #N ... en el sha X.
  Mergéalo tú.»), y `gh pr merge --match-head-commit <sha>` para que no entre otra cosa.
- **No inventar ids de sesión en un brief.** Se usó uno sin verificar y hubo que retirar la propuesta. Nombrar a la
  coordinadora por su título y decir que la busquen con ListAgents.
- **Antes de atribuir una caída de disco, mirar quién escribe.** C: bajó 15 GB en una hora por un proceso ajeno
  (`run_ciclo.py`) y no por VRP.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: con la regla de hoy, la vía de VIIRS 375 calla 4 alertas protegidas de MIROVA que el port publica
  (Isluga 06-17, 09-28 y 10-03; Láscar 10-01). Con «cercano», MODIS publicaría de más en Láscar 2026-03-30 (11,7 MW como
  cumbre; MIROVA lo ubica a 26,87 km).
- **CONFIRMADO**: en VIIRS los conteos de la regla de posición son cota inferior, porque la muestra excluye las pasadas en
  que MIROVA publicó una fuente lejana (338 en VIIRS 375 y 19 en VIIRS 750, sin grillas).
- **CONFIRMADO**: el déficit de magnitud de Chillán en MODIS cae con el cenit (0,75 bajo 30° contra 0,20 sobre 30°,
  ρ −0,83). **SOSPECHA**: el mecanismo, que lo están midiendo MOD-D y MxD03.
- **SOSPECHA**: la tercera pérdida MODIS de Chillán (2026-10-25 07:20) es el mismo patrón que las dos que recupera MOD-D;
  cae fuera de la ventana del censo (SIN DATO).
- **SIN VERIFICAR**: que el NRT con #920, #921 y #922 en el código produzca los mismos records (el arnés sintético dice
  que sí; falta la corrida real de las 01:10 UTC del 2026-10-28 y el bit a bit de un día de NRT en VIIRS 375).
- Seguimientos del verificador de #922: V16503-04 (14 citas viejas en `docs/MIROVA_DIVERGENCES.md`) y V16503-05
  (`scripts/backfill_nov_2025.py` sin informe de cobertura).

## e. Lo que ya está cerrado y no hay que rehacer

- Fase 3 de las tres vías y MxD03 con V165-03: mergeadas, verificadas e identidad comprobada aparte. No se rehacen.
- La medición de la regla de posición en los tres sensores: hecha y verificada. Lo que falta son los brazos dentro de los
  A/B, no otra medición.
- #915: clasificado entero; sólo quedan las decisiones 1 a 3 del §b.
- D-39: cerrado. No recordárselo a Nicolás.
- Medidor de V750-A: 62 de 62.
- Integración de `loop/activo` a `main` (#918).
- W1, W2 y W3 del A/B diurno: cobertura pareja; no se repiten.

## f. Prompt para la próxima sesión

```text
Retoma VRP Chile como sesión coordinadora S166 (relevo de S165, cierre del 2026-10-27 ~23:25 UTC). Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (loop/activo, en el commit del cierre o más nuevo); hora del servidor con gh api -i repos/MendozaVolcanic/VRP-chile |
   grep -i date (A86); df -h /c /d (parada bajo 3 GB).
2. Lee CLAUDE.md del proyecto, tasks/BLOQUE_ARRANQUE_S166.md, tasks/LOOP_OBJETIVOS.md §6 (vueltas 1 a 14 de S165) y
   docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md §7 (regla de posición como brazo).
3. Mira las sesiones vivas con mcp__ccd_session_mgmt__list_sessions y ListAgents, y avísale a Loop VIIRS 750 2
   (local_94f4be0d-2b32-4570-b711-3a6f14cc8a0a) que la coordinadora ahora eres tú. Las sesiones mxd03 (local_f2be5b7f),
   V375-E (local_0a1b597c) y modd-fase3 (local_1860a1d4) ya entregaron: se pueden archivar si Nicolás está de acuerdo.

Trabajo, en orden:
- Primer NRT con #920, #921 y #922 en el código (01:10 UTC del 2026-10-28 o el siguiente): verde, ningún record con
  via_codigo_mirova, y los campos de los records iguales a los de antes en los 11 Tier A (A116).
- A/B diurno: cuando termine W4 (run 40545948109), lee su cobertura.txt y despacha la siguiente, una a la vez:
  V='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]'
  gh workflow run reproc-s151-ab-diurno.yml --ref s163-diurno-k-codigo -f preregistro_aprobado=si -f start=<inicio> -f end=<fin>
    -f vols="$V" -f brazos='["_s154_ab_diurno_k_control","_s154_ab_diurno_k_on"]' -f control=_s154_ab_diurno_k_control
  W5 2026-09-01 a 09-20; W6 10-01 a 10-14. Al terminar W6, la lectura con dias_excluidos_nasa.py y
  evaluar_con_exclusion.py (--opcion-e e-ii) desde un git archive del commit sellado, con verificador limpio; el
  veredicto va a Nicolás.
- V750: recibir de Loop VIIRS 750 2 la adenda 2 de V750-B con su verificador y llevársela a Nicolás para el sello
  (§b 4). El 2026-11-03: objetivos de V750-B (--hasta 2026-11-02, sha256, tag) y despacho; la lista suplementaria va
  sólo si Nicolás selló la adenda 2. Ese mismo día, la consulta C-06 del cese de Suomi NPP contra CMR.
- Bit a bit de un día de NRT en VIIRS 375: llevar experiments/_s162_v750a/probe-s162-bitabit-nrt.yml a
  .github/workflows/ (PR chico) y comparar el tag pre-s165-via-375 contra main con
  experiments/_s165_v375_via/comparar_bitabit_nrt_v375.py.
- Revisión de propagación (A113) tras los cuatro PR de pipeline/ del 2026-10-27: FICHA SDA, tabla de flags, citas
  file:line de CLAUDE.md y de docs/MIROVA_DIVERGENCES.md (V16503-04, 14 citas).
- Pedirle a Nicolás las decisiones del §b, con la recomendación.
- Correr como loop propio con la skill loop en modo dinámico sobre tasks/LOOP_OBJETIVOS.md; anotar cada vuelta con la hora
  de date -u y commitear en loop/activo.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y el sí explícito de Nicolás (A45); un merge a main sólo
con la frase de Nicolás en este chat y gh pr merge --match-head-commit <sha>; antes de proponer un merge de una vía
apagada, correr el arnés S142 con git archive de main y de la rama y compararlo con cmp; sólo EARTHDATA_TOKEN (A71);
despachos uno a la vez dentro del cupo de 20 jobs (NRT usa 11), desde tags; verificador limpio de otro modelo antes de
aceptar un resultado; git add por archivo; nunca git stash; un fetch por comando o refspec explícito (FETCH_HEAD se
pisa); las ramas de las hijas tienen que estar en el remoto; disco justo (parada bajo 3 GB); Claude no borra de forma
permanente (papelera de Windows); texto con barras invertidas con Edit, no con heredoc; español de Chile sin voseo ni
guiones largos; rutas absolutas. Si la sesión no alcanza: commitea, anota en la bitácora qué quedó corriendo y cierra
con /cierre.
```
