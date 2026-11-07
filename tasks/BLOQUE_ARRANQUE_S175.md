# Bloque de arranque S175 (cierre de S174, 2026-11-07 20:05 UTC)

> **Actualización 2026-11-07 20:47 UTC: la auditoría S175 terminó los cinco frentes.** F1 (vía MODIS) corrió antes del lunes y tiene su verificador V1; la síntesis cerrada está en `docs/AUDIT_S175.md` del PR #955 (borrador, `9ab30cfb1`). Sólo falta el anexo del audit semanal del lunes 2026-11-09. Donde abajo dice «F1 el 2026-11-09», léelo así: F1 ya está; el lunes sólo se agrega el anexo y se cierra #955. F1 dejó dos hallazgos de gravedad 4 (leer su veredicto en la síntesis antes de actuar).

> **Sin trabajo en vuelo al fijar este estado.** Ningún agente de S174 sigue corriendo; la sesión de auditoría
> S175 (`local_f899f426`) está en reposo con su PR #955 en borrador. El NRT y la sombra siguen commiteando a main
> (último NRT verde 2026-11-07 18:28 UTC; último dato `5d04126f3` 18:58 UTC). El bloque anterior (escrito el
> 2026-11-05) queda abajo como histórico, sin borrar.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| #945 lector de la sombra V750-A separado por ROI y sha, ventana fija de 28 días, 14 noches por volcán | MERGEADO 2026-11-07 03:30 UTC | squash `235ba7918`; 6 vueltas de autor; verificador R6 MERGEABLE (`D:\vrp-trabajo\temporales\s174-ver945\INFORME_R6.md`) |
| #953 retoques R6 (OverflowError de `--ahora`, B0 con 14 noches, ER45 con TZ) | MERGEADO 2026-11-07 10:32 UTC | squash `34eb44d9b`; `C:\Users\nmend\vrp-temporales\s174-ver953\INFORME.md` |
| #952 controles de cenit de la retrospectiva D3 sin falsos verdes | MERGEADO 2026-11-07 15:55 UTC | squash `36a191d45`; R2 MERGEABLE (`C:\Users\nmend\vrp-temporales\s174-ver952\INFORME_R2.md`) |
| #954 el CI corre la batería del lector de V750-A (job `bateria-v750a`, huella de batería y medidor) | MERGEADO 2026-11-07 17:40 UTC | squash `35b08984d`; R2 MERGEABLE CON CAMBIOS menores (`C:\Users\nmend\vrp-temporales\s174-ver954\INFORME_R2.md`) |
| Auditoría integral S175 (F0, F2, F3, F5) | SÍNTESIS PARCIAL en PR #955 (borrador, rama `claude/relaxed-almeida-d17378`, `f2987aa5b`) | 35 hallazgos confirmados, 0 refutados; sólo el 251 queda en gravedad 3 (`SINTOMAS.md` describe MODIS de producción como K). F1 (vía MODIS) corre tras el audit del lunes 2026-11-09 |
| Lectura real de V750-A | PROVISORIO (rc 4), 1,4 de 28 días, una noche por volcán | autor R6 sobre `ba77c1f6d`, B4 y `--sha-desde 58edb9788` |
| `loop/activo` contra main | ATRASADA: no tiene #945, #952, #953 ni #954 | `git cherry -v loop/activo origin/main`; último merge de main a la rama `dd7467218` (2026-11-06) |
| Disco | C: 16 GB libres, D: 4,9 GB | `df -h` 2026-11-07 20:00 UTC, tras vaciar la papelera (la auditoría movió 11 carpetas, 10,99 GB) |
| Plan semanal | 89 % (Fable 44 %), reinicio 2026-11-08 12:00 UTC | `get_usage` 20:00 UTC |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Protección de rama de main (VPR954-03): hoy un PR en rojo se puede mergear | (a) dejar como está; (b) checks obligatorios `pytest` y `bateria-v750a` sin exigir revisión | (b): la regla «frase de Nicolás y CI verde» se aplica a mano; la protección la hace cumplir sola |
| 2 | VPR952-04: si todas las etiquetas llegan `sin_info`, el control de cenit dice SIN SUSTRATO y no se distingue de un sensor callado | (a) aceptarlo; (b) ROJO en un control de etiquetas o en `c_cobertura` | (b), PR chico; el defecto es de la etiqueta, no del cenit |
| 3 | Pre-registro de la retrospectiva l. 409: el texto dice que con un control de cenit en rojo «la curva no se lee»; el lector manda el sensor entero a la fila 1 (desde VPR946-01) | (a) bajar el lector al texto; (b) mantener el lector y dejar escrita la divergencia | (b): la lectura estricta sólo puede impedir una adopción, no provocarla |
| 4 | Fila 4 del veredicto D3 por la curva de cenit en el tramo DM | ningún sensor tiene sustrato en DM ni en F26 (ensayo de cenit de S174) | Aceptar que la fila 4 por la curva no se activa ahí y escribirlo en el veredicto |
| 5 | Decisión 3 de S174 (`sin_grilla`/`sin_mxd03` tratados como K con aviso) ya aprobada, pero toca `pipeline/` | hacerla en S175 con tag defensivo | Sí, con tag y tu confirmación A45 antes del primer edit |
| 6 | Triage de los 35 hallazgos de #955 | arreglar todo / por categoría / sólo g3 | Primero el 251 (documento), después los g2 agrupados, cuando F1 cierre |

## c. Lo aprendido

- **El esfuerzo sí llegaba (REGLA GENERAL).** Los transcriptos de los agentes muestran `output_config.effort: high` en
  cada pedido (10 de 10 en disco, Opus y Sonnet); el 10 a 15 que declaran no es el nivel. Rebaja la sospecha de S172
  y S174. Destino: memoria `feedback_s175_esfuerzo_en_transcripto.md` (la escribió la auditoría) y rebaja en
  `feedback_s174_medidor_blanco_viejo.md`.
- **Identidad del pareo (proyecto).** El recall del audit semanal es por noche y círculo con un port del predicado;
  nadie comparaba la posición de los positivos con MIROVA. Ante cualquier métrica de paridad, preguntar pasada, foco,
  predicado, magnitud, etiqueta y tiempo. Destino: memoria `feedback_s174_identidad_del_pareo.md`; frente F5 de S175.
- **Un instrumento fuera de `tests/` no tiene CI (REGLA GENERAL).** El lector de V750-A decidía una adopción y ningún
  workflow lo corría (VPR953-04). Todo analizador que decide algo necesita un envoltorio en `tests/`. Destino:
  `docs/META_RULES_S80.md` como regla nueva (pendiente, ver §d).
- **Parches sobre parches.** #945 necesitó seis vueltas: cada ronda del verificador encontró un borde nuevo de la
  misma regla (reloj, ventana, cobertura por volcán). Escribir el contrato del lector (ventana, mínimos, qué es una
  noche) antes del código. Destino: bitácora 2026-11-06 08:41 UTC.
- **Heredocs en esta máquina (REGLA GENERAL, cuarta vez).** `\v` y `\t` dentro de un heredoc se vuelven caracteres
  de control; escribir con Write o armar la barra con `chr(92)` y comprobar que no quedan chr(9) ni chr(11).
- **Disco.** Cada clon de verificador pesa 1,5 a 12 GB: reusar un clon entre rondas. La papelera no libera nada hasta
  vaciarla y el clasificador de permisos puede bloquear el envío; lo vacía Nicolás.
- **Un push a `loop/activo` no dispara el CI**: la suite sobre esa rama se corre a mano.

## d. Problemas abiertos e hipótesis

| Ítem | Etiqueta |
|---|---|
| `loop/activo` no tiene #945, #952, #953 ni #954 | CONFIRMADO (`git cherry`) |
| La suite completa no ha corrido sobre `loop/activo` desde el merge de main del 2026-11-06 | CONFIRMADO |
| El guard del libro de pruebas (G1/G1b) falla en local porque el generador recorre `.claude/worktrees` | CONFIRMADO (S174); arreglo: excluir `.claude/` en `scripts/libro_de_pruebas.py` |
| Medidor completo de V750-A (M1 a M52, MR1 a MR79 sobre 105 escenarios) sin correr tras crecer la sombra y agregar ER56/ER57 | SOSPECHA de que alguna mutación cambie de estado |
| La huella de #954 ata al diff, no al contenido (quien copia la huella nueva sin correr el medidor pasa) | CONFIRMADO (verificador R2, N10); anotado en el PR |
| `_cenit_finito` acepta `"20"` y `True` como cenit (VPR952-R2-02) | SOSPECHA |
| Comentario «158 s» viejo en `tests/test_bateria_lector_v750a_s174.py:49` (el CI mide 211 s) | CONFIRMADO |
| Citas a rutas privadas (`s174-cenit\INFORME.md`, `s174-ver952\...`) en el repo público | CONFIRMADO (autor #952) |
| VIIRS 375 sobre-publica 11 % en volcanes focales (41 de 373 negativos limpios), sobre la banda del 10 % | CONFIRMADO (audit 2026-11-02) |
| MODIS perdió 4 protegidas en Nevados de Chillán (12, 15, 25 y 30 de oct), juzgado con K | CONFIRMADO; el audit del 2026-11-09 es el primero con la vía |
| El VRP truncado de MIROVA en MODIS mueve la lista de protegidas en el umbral de 1 MW | SOSPECHA (F5 I8 de S175; leer su resultado en #955) |

## e. Lo que ya está cerrado y no hay que rehacer

- #945, #952, #953 y #954 en main, cada uno con verificador limpio de otro modelo y frase de Nicolás.
- El «esfuerzo bajo» de los agentes: refutado con los transcriptos. No relanzar nada por esa causa.
- Alertas #915 y #936: investigadas en S174 (juzgaron MODIS con K); abiertas a propósito hasta el audit con la vía.
- #950 y #951 mergeados el 2026-11-06. CLAUDE.md corto en `loop/activo`.
- Limpieza de disco: los clones y worktrees de #945, #952, #953 y #954 ya no existen; los informes de cada
  verificador siguen en `C:\Users\nmend\vrp-temporales\s174-*` y `D:\vrp-trabajo\temporales\s174-*`.

## f. Prompt para la próxima sesión

```
Sesión S175 de VRP Chile (coordinadora del programa de réplica por sensor). Carpeta:
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo.

1. Verifica antes de creer: date -u; git fetch origin --prune; git status -sb; HEAD contra
   git ls-remote origin -h refs/heads/loop/activo; df -h /c /d; get_usage del plan.
   gh pr view 955 --json state,isDraft,headRefOid; gh pr checks 955. Último run de audit-weekly.yml
   y de vigilancia de la guardia MODIS (data/audit_continuous/latest.json y guardia_modis_latest.json en origin/main).
2. Lee: CLAUDE.md; este bloque (tasks/BLOQUE_ARRANQUE_S175.md, la parte de arriba); las 8 entradas más nuevas de la
   bitácora §6 de tasks/LOOP_OBJETIVOS.md; la síntesis docs/AUDIT_S175.md del PR #955.
3. Trabajo en orden:
   a. Traer main a loop/activo (merge; resolver con la versión de main lo sellado) y correr la suite completa
      a mano con el árbol quieto (un push a loop/activo no dispara el CI).
   b. Lunes 2026-11-09: leer el audit semanal (primero con la vía MODIS), revisar la guardia, y avisar a la sesión
      de auditoría para lanzar F1 y su verificador; cerrar #955 con F1 incluido.
   c. Presentar a Nicolás las decisiones de §b con su recomendación; arreglar el hallazgo 251 (SINTOMAS.md).
   d. Medidor completo de V750-A para el sello (unas 7 h, un proceso pesado, en un clon reusado).
   e. Seguimientos chicos en un PR: comentario 158 s, VPR952-R2-01 a 03, citas a rutas privadas, libro sin .claude/.
   f. Antes del 2026-11-27: rotar EARTHDATA_TOKEN (fecha en REGISTRO_CREDENCIALES.md).
4. Reglas duras: pipeline/ congelado durante la sombra (excepciones: ROI de V750, emergencias del NRT, MODIS decidido,
   agregar entradas a grillas_mirova.yaml); nada en pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45);
   merge a main sólo con frase de Nicolás y gh pr merge --match-head-commit; sólo EARTHDATA_TOKEN (A71); despachos de
   a uno desde tags; verificador limpio de otro modelo antes de aceptar un resultado; effort high explícito y carpeta
   temporal propia con su nombre; máximo 2 procesos pesados locales y parada bajo 3 GB libres en C: o D:; git add por
   archivo; nunca git stash; date -u antes de cada encabezado de bitácora; un PR sin checks no es verde; papelera, nunca
   borrado definitivo; heredocs sin \v ni \t (Write o chr(92)).
5. Si la sesión no alcanza (contexto sobre 50 % o cambio de día): commitea, anota en la bitácora, escribe el bloque S176
   con /cierre.
```

---

# Histórico: bloque anterior (escrito durante S174, 2026-11-05 ~22:20 UTC)

> **Estado fijado con trabajo en curso.** Al escribir esto corría la segunda ronda del verificador limpio del #945
> (Sonnet, carpeta `D:\vrp-trabajo\temporales\s174-ver945`, informe esperado `INFORME_R2.md`) y el CI del #945 sobre
> `daf04cfdc` (run 42119741385). Verifica los dos antes de creerle a la tabla. Si S174 alcanzó a actualizar este
> bloque, lo dice abajo con una marca «Actualización».

> **Actualización S174 23:2x UTC: la R2 del verificador del #945 terminó: MERGEABLE CON CAMBIOS (más leve).** 7 de 8
> hallazgos de R1 CERRADOS, VPR945-01 EN PARTE. Nuevos: R2-01 (g2, la duración es el lapso entre extremos y no las
> noches con datos: una pasada suelta a +30 días da CUMPLE), R2-02 (g2, el reloj es global: sin `--sha-desde` una
> noche `sens` da 28,1 de 28 días), R2-03 (g1, sin cota inferior 2026-11-03), R2-04 (g1, 5 de 11 mutaciones nuevas
> sobreviven). Las tres decisiones del autor: coherentes con la letra (PREREGISTRO_V750A.md l. 89 a 95 y 132); la (1)
> abre R2-01 y R2-02. Nicolás fijó el mínimo (2026-11-06 00:48 UTC, frase «14 noches»): 14 noches distintas con datos
> además de las 4 semanas; `--sha-desde` obligatorio en sombra (recomendación de la coordinadora). Tercera vuelta del
> autor LANZADA (informe en `D:\vrp-trabajo\temporales\s174-autor945-r3\INFORME_AUTOR_R3.md`); R3 del verificador HECHA 2026-11-06 05:08 UTC sobre `932a3e9fd`: MERGEABLE CON CAMBIOS (menor), R3-01 g2 (noches por volcán con ROI cambiada) y R3-02 a R3-05 g1; informe `D:\vrp-trabajo\temporales\s174-ver945\INFORME_R3.md`. C: quedó en 2,85 GB libres. Después: R4 sobre `b13ec336e` (R4-01 g2, el mismo defecto de anclar el reloj a las pasadas); Nicolás eligió ventana fija; quinta vuelta del autor lanzada 2026-11-06 (`D:\vrp-trabajo\temporales\s174-autor945-r5\INFORME_AUTOR_R5.md`), falta R5 del verificador (Sonnet, reutilizar `clon3`, sin suite local). Confirmar con Nicolás los defaults: 5 noches por semana, sólo conjunto y volcanes cambiados. Informe: `D:\vrp-trabajo\temporales\s174-ver945\INFORME_R2.md`.

## a-prev. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Alertas del auto-audit #915 y #936 | INVESTIGADAS, abiertas a propósito | No vienen de #934 ni de #939: las dos juzgaron MODIS con K (0 records de la vía en `79f410697`). Crónicas desde #499 (2026-07-27). Bitácora §6, entrada 17:28 UTC |
| 8 decisiones del bloque S174 | APROBADAS («Sí, a todo», Nicolás) | Bitácora §6; la 3 (`sin_grilla`/`sin_mxd03` como K con aviso) y la 8 (ensayo de cenit con DM real) siguen SIN HACER |
| #946 | MERGEADO a main | squash `f36a8fb98` |
| #912 | CERRADO (rama intacta) | decisión 7 |
| #945 (lector de la sombra V750-A por ROI y sha) | BORRADOR, segunda vuelta del autor en `daf04cfdc`; R2 del verificador en curso | R1: MERGEABLE CON CAMBIOS (VPR945-01 a 08); autor: 67/67 escenarios, 23/23 mutaciones, suite 3.199 pasan |
| #950 (cuatro dudas del CLAUDE.md corto) | MERGEADO 2026-11-06 (`77e54e8e0`), CLAUDE.md ya en `loop/activo` (`9b70ca5f8`) | D21, GAP #A, A85 (obsoleta por #883), A100; sin verificador de otro modelo |
| #951 (M71/M82 de V750-A) | MERGEADO 2026-11-06 (`c8152580b`); su única falla de CI es la frescura del CSV de esa rama | blanco viejo tras N-3 `a9500912e`; 2/2 atrapadas en 88 escenarios |
| Vigilancia de la guardia MODIS | VERDE sin avisos (2026-11-05 02:46) | nulo 167/0, 1 de 29 protegidas |
| Discos | C: 15 GB, D: ~9 GB libres | `df -h /c /d` a las 20:31 UTC |

## b-prev. Decisiones que espera el dueño

| # | Pregunta | Recomendación |
|---|---|---|
| 1 | Merge de #950 a main | Sí (CI verde, sólo CLAUDE.md, 200 pruebas que lo leen pasan) |
| 2 | Merge de #951 a la rama de V750 | Sí (sólo `experiments/`, medido) |
| 3 | #945: mínimo de noches distintas con datos para que la sombra pueda decir CUMPLE (R2-01), y reloj por volcán y ROI o `--sha-desde` obligatorio (R2-02) | RESUELTO 2026-11-06: 14 noches (frase de Nicolás) y `--sha-desde` obligatorio |
| 4 | #945: un P1 veta antes de cumplir las 4 semanas | Sí (es lo implementado; esperar es la mutación MR22) |
| 5 | #945: la hora del corte de `--sha-desde` es la del commit | Lo que diga la R2 |
| 6 | Lectura real de V750-A: `--roi-brazo B4 --sha-desde 58edb9788...` | Hoy da 0 pasadas: decidir al sellar |
| 7 | Merge de #945 a main | Tras R2 sin gravedad 3 y CI verde |

## c-prev. Lo aprendido en S174

- El parámetro `effort: high` del Agent tool puede no llegar: el verificador informó «esfuerzo del arnés 10» (SOSPECHA,
  ya visto en S172). Pedirle a cada agente que declare su esfuerzo en el encabezado y anotarlo.
- Un medidor de mutaciones con `assert src.count(viejo) == 1` se cae entero cuando un commit reescribe la línea
  mutada: tras cada cambio del analizador, contar los blancos con `ast` (`D:\vrp-trabajo\temporales\s174-dudas\fix_m71.py`).
- sha256 de un archivo extraído con `git show`: LF; el del bloque S162 era CRLF (S169, otra vez).

## d-prev. Pendientes en orden

1. Leer `D:\vrp-trabajo\temporales\s174-ver945\INFORME_R2.md` y el CI del #945; con R2 limpia, presentar decisiones 3 a 5 y mergear #945 con frase.
2. HECHO 2026-11-06: #950 y #951 mergeados, CLAUDE.md en `loop/activo`. Main traído a `loop/activo` el 2026-11-06 (`dd7467218`); las 2 fallas que quedan del libro son sólo locales (worktrees en `.claude/`).
3. Implementar la decisión 3 del S174 (`sin_grilla`/`sin_mxd03` como K con aviso) y correr el ensayo de cenit con DM real (decisión 8).
4. Corrida completa del medidor de V750-A para el sello (~7 h; un proceso pesado a la vez).
5. 2026-11-09: primer audit semanal con la vía MODIS (recall «sin juzgar» hasta 15 noches) y revisión de la guardia (`data/audit_continuous/guardia_modis_latest.json`, regla `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` §4).
6. 2026-11-27: rotación de `EARTHDATA_TOKEN`.
7. Worktrees de S174 en D: (`wt/ver945`, `wt/s174-dudas`, `wt/s174-v750a-m71`): a la papelera tras mergear, revisando antes que no tengan commits sin subir.

## e-prev. Prompt para la próxima sesión

```
Sesión S175 de VRP Chile (coordinadora del programa de réplica por sensor). Carpeta:
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo.

1. Verifica antes de creer: git fetch origin --prune; git status -sb; HEAD contra
   git ls-remote origin -h refs/heads/loop/activo; date -u; df -h /c /d. Estado de #945, #950 y #951
   (gh pr view N --json state,isDraft,mergeStateStatus,headRefOid y gh pr checks N).
2. Lee: CLAUDE.md, tasks/BLOQUE_ARRANQUE_S175.md, las 6 entradas más nuevas de la bitácora §6 de
   tasks/LOOP_OBJETIVOS.md y D:\vrp-trabajo\temporales\s174-ver945\INFORME_R2.md.
3. Trabajo en el orden de §d del bloque. Presenta a Nicolás las decisiones de §b con su recomendación antes de mergear.
4. Reglas duras: las del bloque S174 §f punto 4 (pipeline/ congelado durante la sombra; A45; merge sólo con frase y
   --match-head-commit; sólo EARTHDATA_TOKEN; despachos de a uno desde tags; verificador limpio de otro modelo; esfuerzo
   high explícito y carpeta temporal propia en D:; máximo 2 procesos pesados; parada bajo 3 GB; git add por archivo;
   nunca git stash; date -u antes de cada encabezado; un PR sin checks no es verde; papelera, nunca borrado).
5. Si la sesión no alcanza (contexto sobre 50 %): commitea, anota en la bitácora, escribe el bloque S176 y lanza la siguiente.
```
