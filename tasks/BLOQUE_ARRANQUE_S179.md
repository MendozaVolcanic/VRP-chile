# Bloque de arranque S179 (cierre de S178, 2026-11-10 17:25 UTC)

> **Estado fijado con trabajo en curso.** Corre el reintento de 2 trozos de P4 (run 42749607584, `gh run rerun
> --failed` a las 17:22 UTC: Copahue 2026-10-17 a 11-05 y 11-06 a 11-09, salida 3 en el primer intento). Ningún
> agente ni proceso local quedó corriendo. Lo que llegue después de este commit está en el run, no en git.
>
> El bloque anterior (S178) sigue en `tasks/BLOQUE_ARRANQUE_S178.md`, sin tocar: es la línea de base de lo que se creía
> al abrir S178. La bitácora con cada paso de S178 y su evidencia está en `tasks/LOOP_OBJETIVOS.md` §6 (entradas
> «2026-11-10 ... (S178)»).

Objetivo de Nicolás (vigente): publicar VIIRS con la vía «código MIROVA». Desde S178: retrospectiva leída, regla de
reversión de VIIRS sellada, y el encendido sólo espera las 3 noches verdes de la guardia K y su frase.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Retrospectiva D2 a D4 (P1) | **LEÍDA con candado**, verificador limpio: VÁLIDA CON RESERVAS (ninguna cambia un veredicto) | tag `s178-retro-lectura`, rama `claude/s178-retro-lectura`, `experiments/_s178_lectura/lectura.json` (commit `ff8a39972`) |
| Veredictos por sensor (§8.1) | MODIS fila 4 DECIDE NICOLÁS (regla PROPONER ADOPCIÓN, sin poder sin las pasadas §3.1 b); **VIIRS 375 fila 6 NO SE CONTRADICE**; VIIRS 750 fila 4 DECIDE NICOLÁS (sólo por V750-A en borrador; la regla da sin pérdida, P2 GANA, M MEJORA). Ninguna protegida perdida en ningún sensor | `lectura_salida.txt` en la misma rama |
| C-K | verde, 0 excepciones; control 6 de 6 | `experiments/_s178_ck/` (loop/activo, `2bfc9164b`) |
| C-montaje | OK: 949 pasadas, 0 diferencias (V375 contra la banda de triangulación, decisión *post hoc* de Nicolás) | `experiments/_s178_montaje/PROPUESTA_C_MONTAJE.md`, `montaje_dm_salida.json` (loop/activo) |
| Regla de reversión de VIIRS | **SELLADA** («Sello la regla», 10:12:44 UTC) y en main (#982, `a9bd0313b`). `COTAS`: VIIRS 375 14/17 (C-rad), VIIRS 750 12/2 | `experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md`, `scripts/vigilancia_guardia_viirs.py`, tag `s178-regla-reversion-viirs-sellada` |
| Mergeados hoy a main | #976 y #984 (los tres avisos de texto fuera; comprobado en el sitio publicado), #977 (revisores con noche cerrada), #978 (P5 sólo K), #979 (lector: caja B4, C-montaje, tags de origen, OSF local), #982 (regla sellada) | main `438a60a1e` |
| Guardia K de VIIRS (P3) | cuenta noches desde el 11-10 con el revisor corregido; **0 de 3** al cierre (primera corrida 19:35 UTC del 11-10) | `guardia-k-viirs.yml` |
| B1 (#974) y B2 sobre B1 (#983) | listos en borrador, CI verde. **#983 contiene B1 y B2**: mergearlo antes de #974 enciende los dos | #983 `e68819484` |
| Vara MATLAB V750 (P5) | VERDE sobre main `e7cfbaf54` (311 de 311) | #980 (borrador) |
| Plan de reemplazo de la historia (P6) | escrito; verificador: **CON ERRORES** (3 huecos, anotados en el plan) | #981 `62ccb8830` |
| Cotas VIIRS 375 (P10) | hechas y verificadas; C-rad elegida | `experiments/_s178_cotas_v375/` (en main con #982) |
| Anexo de #955 (P9) | escrito, verificado y corregido; listo para la frase | #955 `9da50f1b5` |
| P4 (historia con la vía) | 163 de 165 trozos verdes; 2 de Copahue relanzados | run 42749607584, tag `s178-retro-historia` |
| #962 (sombra sin corrida verde) | diagnosticada: 1 falso rojo (arreglado por #977) y 2 timeouts reales de NASA ya reparados; se cierra sola con la primera corrida verde | bitácora S178 |
| main en loop/activo | **NO integrado** (284 commits de main faltan en loop/activo) | `git rev-list --count HEAD..origin/main` |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Encender VIIRS 375 (merge de #974) | ahora / tras 3 noches verdes de la guardia | **Tras las 3 noches** (11-10, 11-11 y 11-12). Antes renumerar la ficha de #974 a v1.23 (main ya está en v1.22). |
| 2 | Encender VIIRS 750 (merge de #983, B2 sobre B1) | después de #974 / esperar más evidencia | **Después de #974**, con la ficha en v1.24. Su evidencia es más débil (14 casos, 12 de Chillán); la vara MATLAB está verde (#980). |
| 3 | Auditoría con Fable 5.2 de las decisiones y planes S172 a S178 | sí al abrir S179 / más adelante | **Sí, primer punto de S179** (ver sección g). Escribir antes la guía de prompting de Fable 5.2. |
| 4 | Merge de #955 (auditoría S175 con anexo) | sí / no | **Sí**: anexo verificado, ningún veredicto cambia. Comprobar su CI con main al día. |
| 5 | Merge de #980 (salida de la vara MATLAB) | sí / no | **Sí**: sólo agrega la salida fechada. |
| 6 | Plan de reemplazo (#981): pasadas K sin par en la vía | apartarlas a una carpeta fuera del tablero / dejarlas | **Apartarlas**: un solo K anterior a la vía mantiene el aviso y mezcla detectores; quedan guardadas sin borrar. |
| 7 | Tupungatito antes del 2026-02-23 (787 MODIS, 1.574 V375, 1.563 V750, todos K, sin reproceso con la vía) | reprocesar con la vía (fuera del planificador sellado) / apartar / dejar K con aviso | **Reprocesar con la vía** en un despacho propio fuera de la retrospectiva (no decide nada, sólo completa la serie). |
| 8 | Codex local (heredada) | sólo tras rotar el PAT | Sin cambio. |

## c. Lo aprendido

Reglas generales del workspace (van a la memoria como feedback):
- **Un control común rojo por construcción bloquea todo aunque el resto esté listo.** C-montaje tenía 5 PENDIENTES
  escritos a propósito y dejaba los tres sensores INDECIDIBLES. Antes de despachar una prueba sellada, correr el lector en
  modo control (sin veredictos) para ver qué controles pueden ponerse verdes con los datos que habrá.
- **Una tolerancia declarada por instrumento tiene que existir para cada instrumento.** La banda de triangulación se
  declaró para VIIRS 750 y no para VIIRS 375, que también la tenía: 12 diferencias de fondo numérico dejaron todo rojo y
  hubo que decidir *post hoc*. Al declarar comparadores, revisar qué incertidumbre propia guardó cada A/B.
- **Una regla sellada no puede hacer git show de un archivo fuera de git.** El OSF (98 MB, ignorado) no entraba al
  manifiesto; se resolvió verificando su sha256 en bruto contra el declarado. Al sellar, nombrar referencias que estén
  en git o con hash en bruto declarado.
- **El clasificador de permisos sólo deja mergear con la frase explícita de merge.** «Avanza con todo» y «Sello la
  regla» fueron bloqueados; «Mergea #982» pasó. Pedir siempre «mergea #N».
- **Sumar por pasada cuando la exposición cambia entre ventanas.** En F26-V la tabla de MIROVA no trae NOAA-21: sumar por
  día abarataba la cota (verificador de P10).
- **Un despliegue que copia `data/` entera tiene techo.** GitHub Pages: 1 GB; cualquier carpeta nueva en `data/` va al
  sitio público (verificador de #981).

Propias del proyecto: el «hallazgo 101» (píxel de cumbre con BT bajo `t_bg`, cúmulo 0 MW) sigue SIN ATRIBUIR; la ficha
SDA se renumera en cadena según el orden real de merge.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: el plan #981 no se puede aplicar tal cual (falta la regla «no pisar records de la vía ni agregar los de
  P4 desde el 11-02»; P5 caerá al quitar los K de MODIS; Pages pasaría de 1 GB).
- **CONFIRMADO**: #983 enciende B1 y B2 juntos si entra antes que #974.
- **CONFIRMADO**: main no está integrado en loop/activo (284 commits).
- **SOSPECHA**: los 2 trozos rojos de P4 en Copahue (salida 3 con `--estricto-cobertura`) son un corte transitorio; los
  logs muestran pasadas MODIS «sin record» por borde, que en otros volcanes no dieron rojo. Mirar el reintento.
- **SOSPECHA**: las pasadas VIIRS sin par en la vía son descarte de borde (VIIRS no lo registra en el log).
- **SOSPECHA**: la guardia K de VIIRS saldrá verde esta noche con #977; no hay corrida todavía.
- **CONFIRMADO** (fragilidad, no bug): un timeout de NASA pone en rojo una corrida de la sombra aunque el día siguiente
  la repare (#962).

## e. Lo que ya está cerrado y no hay que rehacer

- La lectura de la retrospectiva: no se re-corre (reproducida idéntica por el verificador). Su candado, C-K, C-montaje
  y la caja B4 están cerrados.
- Las cotas de VIIRS 375 y 750 y la regla de reversión de VIIRS: selladas y en main.
- Los tres avisos de texto del tablero: fuera, comprobado en el sitio publicado.
- El falso rojo del revisor de la guardia y de la sombra: arreglado (#977), incluido el hueco de ventana vacía.
- La vara MATLAB de V750 sobre main: verde (#980).
- El anexo de #955: verificado y corregido.
- D2, D3 y D4: no se relanzan.

## g. Plan de S179 (en este orden)

1. **Auditoría con Fable 5.2** (decisión b3). Antes: escribir `GUIA_PROMPTING_prompting-claude-fable-5-2.md` en el
   workspace desde la página oficial (skill `investigacion`) y ajustar el hook que hoy recuerda la de 5.1. Diseño:
   `GUIA_MAESTRA_AUDITORIAS.md` (cobertura primero, preámbulo anti-fabricación, verificador con contexto limpio).
   Revisores Fable 5.2 en esfuerzo `high`, uno por frente: (a) MODIS (adopción S172, retrospectiva DECIDE NICOLÁS,
   reemplazo); (b) VIIRS 375 y 750 (B1, B2, D5, regla sellada, cotas C-rad); (c) instrumento y retrospectiva (candado,
   C-montaje con las dos decisiones *post hoc*, caja B4, OSF local); (d) planes pendientes (#981, 34 volcanes, Compuerta
   B) contra `docs/MISSION.md`. Cada encargo: «terminar todo el trabajo», sin subagentes salvo necesidad, separar lo
   prohibido (pipeline, data, frontend, merges, NASA) de lo permitido (leer, correr scripts, recontar), informe para un
   lector sin contexto. Verificador cruzado de otro modelo sobre los hallazgos. Costo: del orden de un millón de tokens;
   mirar `get_usage` y decirlo antes de lanzar.
2. **Guardia K de VIIRS**: leer cada corrida (cron 19:35 UTC); 3 noches verdes habilitan b1.
3. **P4**: leer el reintento de Copahue; si cae dos veces, sus pasadas quedan SIN DATO en la primera línea del resultado.
4. **Corregir #981** con los 3 hallazgos del verificador, y preparar el script (`--familia`, `--apartar-sin-par`, regla
   de no pisar la vía) con TDD.
5. **Integrar main en loop/activo** (merge, sin rebase).
6. Encendido (b1, b2) cuando corresponda, con «mergea #974» y luego «mergea #983».

## f. Prompt para la próxima sesión

```
Sesión S179 de VRP Chile (coordinadora del programa de réplica por sensor). Carpeta:
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo. Única dueña del loop.
Objetivo de Nicolás: publicar VIIRS con la vía «código MIROVA». La retrospectiva ya está leída (S178) y la regla de
reversión de VIIRS sellada; el encendido espera 3 noches verdes de la guardia K y su frase.

1. Verifica antes de creer: date -u; git fetch origin --prune; git status -sb; git rev-parse HEAD contra
   git ls-remote origin -h refs/heads/loop/activo (debe ser el commit del cierre de S178 o posterior);
   gh run view 42749607584 (reintento de Copahue en P4); gh run list --workflow guardia-k-viirs.yml --limit 3
   (¿corrió el 11-10 a las 19:35 UTC y salió verde?); gh issue list --state open; gh pr list --state open;
   df -h /c /d; get_usage. Lista las sesiones vinculadas.
2. Lee: CLAUDE.md; tasks/BLOQUE_ARRANQUE_S179.md entero (la sección g es el plan); las entradas S178 de la
   bitácora §6 de tasks/LOOP_OBJETIVOS.md; C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md.
3. Pide a Nicolás las decisiones de la sección b con su recomendación (b3 primero).
4. Trabajo según la sección g: auditoría con Fable 5.2 (guía de prompting de 5.2 primero), guardia, P4, #981,
   integrar main en loop/activo, encendido cuando toque.

Reglas duras: los merges a main, el encendido y toda A45 nueva son sólo de Nicolás, con la frase «mergea #N» en tu
conversación (el clasificador bloquea frases indirectas); gh pr merge --match-head-commit. #983 contiene B1 y B2:
nunca antes que #974. Nada en pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45). Sólo EARTHDATA_TOKEN
(A71); ninguna llamada a NASA desde verificadores; verificador limpio de otro modelo antes de aceptar un resultado;
effort high explícito y carpeta temporal propia; máximo 5 agentes y 2 procesos pesados locales; tope de 500 MB por
agente, sin git init, git add del árbol ni copias del árbol; parada bajo 3 GB libres en C: o D:; git add por archivo;
nunca git stash; no incluyas archivos de experiments/_s176_codex/; date -u antes de cada encabezado de bitácora; un
PR sin checks no es verde; export MSYS_NO_PATHCONV=1 en git show; español de Chile con tú y sin guiones largos ni
medios; rutas absolutas completas para Nicolás.

Si la sesión no alcanza: deja la auditoría con sus encargos escritos y commiteados, la guardia leída y anotada en
la bitácora, y cierra con /cierre al 50 % del contexto.
```
