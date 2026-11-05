# Bloque de arranque S175 (escrito durante S174, 2026-11-05 ~22:20 UTC)

> **Estado fijado con trabajo en curso.** Al escribir esto corría la segunda ronda del verificador limpio del #945
> (Sonnet, carpeta `D:\vrp-trabajo\temporales\s174-ver945`, informe esperado `INFORME_R2.md`) y el CI del #945 sobre
> `daf04cfdc` (run 42119741385). Verifica los dos antes de creerle a la tabla. Si S174 alcanzó a actualizar este
> bloque, lo dice abajo con una marca «Actualización».

> **Actualización S174 23:2x UTC: la R2 del verificador del #945 terminó: MERGEABLE CON CAMBIOS (más leve).** 7 de 8
> hallazgos de R1 CERRADOS, VPR945-01 EN PARTE. Nuevos: R2-01 (g2, la duración es el lapso entre extremos y no las
> noches con datos: una pasada suelta a +30 días da CUMPLE), R2-02 (g2, el reloj es global: sin `--sha-desde` una
> noche `sens` da 28,1 de 28 días), R2-03 (g1, sin cota inferior 2026-11-03), R2-04 (g1, 5 de 11 mutaciones nuevas
> sobreviven). Las tres decisiones del autor: coherentes con la letra (PREREGISTRO_V750A.md l. 89 a 95 y 132); la (1)
> abre R2-01 y R2-02. Falta que Nicolás fije el mínimo de noches distintas (R2-01). Siguiente: tercera vuelta corta del
> autor sobre R2-01..04 y R3 del verificador. Informe: `D:\vrp-trabajo\temporales\s174-ver945\INFORME_R2.md`.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Alertas del auto-audit #915 y #936 | INVESTIGADAS, abiertas a propósito | No vienen de #934 ni de #939: las dos juzgaron MODIS con K (0 records de la vía en `79f410697`). Crónicas desde #499 (2026-07-27). Bitácora §6, entrada 17:28 UTC |
| 8 decisiones del bloque S174 | APROBADAS («Sí, a todo», Nicolás) | Bitácora §6; la 3 (`sin_grilla`/`sin_mxd03` como K con aviso) y la 8 (ensayo de cenit con DM real) siguen SIN HACER |
| #946 | MERGEADO a main | squash `f36a8fb98` |
| #912 | CERRADO (rama intacta) | decisión 7 |
| #945 (lector de la sombra V750-A por ROI y sha) | BORRADOR, segunda vuelta del autor en `daf04cfdc`; R2 del verificador en curso | R1: MERGEABLE CON CAMBIOS (VPR945-01 a 08); autor: 67/67 escenarios, 23/23 mutaciones, suite 3.199 pasan |
| #950 (cuatro dudas del CLAUDE.md corto) | ABIERTO contra main, CI verde, espera frase de Nicolás | D21, GAP #A, A85 (obsoleta por #883), A100; sin verificador de otro modelo |
| #951 (M71/M82 de V750-A) | ABIERTO contra `claude/s162-viirs750-2-918174`, espera frase | blanco viejo tras N-3 `a9500912e`; 2/2 atrapadas en 88 escenarios |
| Vigilancia de la guardia MODIS | VERDE sin avisos (2026-11-05 02:46) | nulo 167/0, 1 de 29 protegidas |
| Discos | C: 15 GB, D: ~9 GB libres | `df -h /c /d` a las 20:31 UTC |

## b. Decisiones que espera el dueño

| # | Pregunta | Recomendación |
|---|---|---|
| 1 | Merge de #950 a main | Sí (CI verde, sólo CLAUDE.md, 200 pruebas que lo leen pasan) |
| 2 | Merge de #951 a la rama de V750 | Sí (sólo `experiments/`, medido) |
| 3 | #945: mínimo de noches distintas con datos para que la sombra pueda decir CUMPLE (R2-01), y reloj por volcán y ROI o `--sha-desde` obligatorio (R2-02) | Exigir `--sha-desde` y un mínimo de noches; el número lo fijas tú (el spec del programa cuenta noches con datos, origin/loop/activo l. 475) |
| 4 | #945: un P1 veta antes de cumplir las 4 semanas | Sí (es lo implementado; esperar es la mutación MR22) |
| 5 | #945: la hora del corte de `--sha-desde` es la del commit | Lo que diga la R2 |
| 6 | Lectura real de V750-A: `--roi-brazo B4 --sha-desde 58edb9788...` | Hoy da 0 pasadas: decidir al sellar |
| 7 | Merge de #945 a main | Tras R2 sin gravedad 3 y CI verde |

## c. Lo aprendido en S174

- El parámetro `effort: high` del Agent tool puede no llegar: el verificador informó «esfuerzo del arnés 10» (SOSPECHA,
  ya visto en S172). Pedirle a cada agente que declare su esfuerzo en el encabezado y anotarlo.
- Un medidor de mutaciones con `assert src.count(viejo) == 1` se cae entero cuando un commit reescribe la línea
  mutada: tras cada cambio del analizador, contar los blancos con `ast` (`D:\vrp-trabajo\temporales\s174-dudas\fix_m71.py`).
- sha256 de un archivo extraído con `git show`: LF; el del bloque S162 era CRLF (S169, otra vez).

## d. Pendientes en orden

1. Leer `D:\vrp-trabajo\temporales\s174-ver945\INFORME_R2.md` y el CI del #945; con R2 limpia, presentar decisiones 3 a 5 y mergear #945 con frase.
2. Con frase, mergear #950 (main) y #951 (rama V750); traer el CLAUDE.md de #950 a `loop/activo`.
3. Implementar la decisión 3 del S174 (`sin_grilla`/`sin_mxd03` como K con aviso) y correr el ensayo de cenit con DM real (decisión 8).
4. Corrida completa del medidor de V750-A para el sello (~7 h; un proceso pesado a la vez).
5. 2026-11-09: primer audit semanal con la vía MODIS (recall «sin juzgar» hasta 15 noches) y revisión de la guardia (`data/audit_continuous/guardia_modis_latest.json`, regla `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` §4).
6. 2026-11-27: rotación de `EARTHDATA_TOKEN`.
7. Worktrees de S174 en D: (`wt/ver945`, `wt/s174-dudas`, `wt/s174-v750a-m71`): a la papelera tras mergear, revisando antes que no tengan commits sin subir.

## e. Prompt para la próxima sesión

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
