# META_RULES_S80 — Procedimientos preventivos de pérdida de contexto

> Origen: auditoría S80 detectó que en 10 sesiones (S70–S80) se mergearon 117
> PRs, y que MEMORY.md acumuló >700 líneas perdiendo trazabilidad. El
> usuario perdió contexto en compactaciones automáticas al millón de tokens.
> Este documento define **reglas operativas vinculantes** para evitar
> repetirlo.
>
> Convención: las reglas que empiezan con M (M1, M2, ...) son **meta-reglas**
> sobre el proceso de trabajo. Las que empiezan con A (A1, A2, ...) son
> aprendizajes técnicos y viven en `CLAUDE.md` raíz proyecto.

---

## M1 — Cap de PRs por sesión (alerta + revisión)

**Por qué**: S76-S78 mergeó 65 PRs sin sesión de consolidación entre medio.
La velocidad de cambio rompió la trazabilidad del proyecto.

**Regla**:
- Cap **soft = 12 PRs** por sesión. Pasado ese umbral, Claude debe pausar
  y proponer sesión de consolidación + actualización MEMORY.md.
- Cap **hard = 20 PRs** por sesión. Pasado ese umbral, Claude **debe**
  bloquear merges adicionales hasta que Nicolás revise el batch y se
  cierre la sesión con `SESSION_CLOSE_CHECKLIST` ejecutado.
- Excepción única: cleanup masivo de cosas claramente equivalentes
  (ej. archive workflows). Documentar en el PR.

**Implementación**: al inicio de sesión, contar PRs mergeados desde el
último `BLOQUE_ARRANQUE_S<N>.md`. Si ya estamos cerca del cap soft, no
abrir nuevos PRs sin pasar primero por consolidación.

---

## M2 — Persistencia durante la sesión, no solo al cierre

**Por qué**: S21 introdujo "persistencia in-vivo" como regla meta-meta. Pero
S78-S79 mostró que el closing checklist no se ejecutó completo (gaps
redescubiertos S80). La regla del cierre es red de seguridad, no
persistencia primaria.

**Regla**:
- **Después de cada hallazgo no trivial** (schema gap, source externa,
  hipótesis confirmada/refutada, regresión introducida) → persistir
  inmediatamente en `MEMORY.md` o doc específico antes de continuar.
- **No esperar al cierre**. La sesión puede cortarse abruptamente
  (compactación, timeout, error).
- Si el hallazgo es muy grande, abrir doc nuevo (`docs/F<N>_<tema>_S<N>.md`)
  en el mismo momento y commitear apenas el código relacionado esté listo.

**Implementación**: Claude debe identificar hallazgos como "no trivial"
cuando aparezca cualquiera de estas señales:
- "ahora entiendo por qué..."
- "esto contradice lo que asumía"
- "esto es un bug latente"
- "esto cambia un default operacional"
- "esto requiere paper Coppola/Aveni para respaldo"

---

## M3 — Verificación cross-source antes de etiquetar "pre-existing"

**Por qué**: S79 etiquetó 6 tests fallidos como "pre-existing fails detectados,
issue separado pendiente S80". S80 descubrió que era regresión introducida
por commit `a73775cd` (Task 1 helper insert) que borró el `return t_bg,
std_bg, n_bg` final de `compute_bg_stats`. Una verificación contra
`origin/main` lo habría detectado en 30 segundos.

**Regla**:
- Antes de etiquetar un fail como "pre-existing", correr `git show
  origin/main:<archivo>` y comparar el cuerpo de la función relevante.
- Si la función fue modificada en algún commit del branch actual, es
  candidato a regresión. Verificar diff de ese commit en la función.
- Solo etiquetar como "pre-existing real" cuando el archivo no fue tocado
  en ningún commit del branch O cuando el fail aparece también en
  `origin/main` con HEAD reciente.

**Implementación**: Claude debe ejecutar este check antes de escribir la
palabra "pre-existing" en cualquier doc/comentario/commit message.

---

## M4 — Auditoría flags trimestral

**Por qué**: S80 detectó 12 flags definidos en `pipeline/profile.py` sin
yaml que los pruebe, varios con defaults `True` operacionales pero
invisibles en `mirova_equivalent.yaml` (ej. `enable_unsuitable_filters_267_273`).
Esto es deriva silenciosa de comportamiento.

**Regla**:
- Cada **20 sesiones** (o trimestralmente, lo primero) ejecutar audit:
  ```bash
  # 1. Flags en profile.py
  grep -E "^ENABLE_[A-Z_0-9]+" pipeline/profile.py | sort -u

  # 2. Flags en mirova_equivalent.yaml
  grep -E "^\s+enable_" pipeline/profiles/mirova_equivalent.yaml | sort -u

  # 3. Defaults en profile.py
  grep -E "enable_.*\.get\(.*default" pipeline/profile.py
  ```
- Producir `docs/FLAGS_AUDIT_S<N>.md` con:
  - flags activos por default (yaml o profile.py)
  - flags huérfanos (en código sin yaml)
  - flags fantasma (en yaml sin importar en código)
  - flags ON sin enunciar en mirova_equivalent.yaml (riesgo deriva)
- Mover los huérfanos a `docs/FLAGS_HUERFANOS.md` o eliminarlos del código
  si llevan >5 sesiones sin actividad.

**Próxima auditoría**: S100 o 2026-08-15, lo primero.

---

## M5 — Post-insert verify (no comer código adyacente)

**Por qué**: S79 commit `a73775cd` insertó helper `apply_f66_consistency_gate`
inmediatamente después de `compute_bg_stats` y accidentalmente borró el
`return t_bg, std_bg, n_bg` final. Bug pasó 1 sesión sin detectarse,
trampa para futuras integraciones.

**Regla**:
- Antes de commitear un `Edit`/`Write` que **inserte código entre dos
  estructuras existentes** (funciones, clases, bloques), Claude debe:
  1. Mostrar el diff con `git diff` antes del commit.
  2. Verificar que **la última línea de la función/estructura anterior**
     sigue intacta (`return`, `}` cierre, `pass`, etc.).
  3. Verificar que **la primera línea de la función/estructura siguiente**
     sigue intacta.
- Si insertar entre dos funciones que están separadas solo por líneas
  vacías, agregar separador de comentario (`# ---`) o usar `Edit` con
  `old_string` que incluya 2 líneas de cada lado.

**Implementación**: para inserciones grandes (>20 líneas), usar `Write`
sobre el archivo completo solo si el archivo es <500 líneas; sino usar
`Edit` con contexto generoso (≥5 líneas antes y después).

---

## M6 — Worktrees no-main pueden estar atrasados (siempre `git fetch + pull`)

**Por qué**: S80 detectó que `VRP-Chile-s70/` (worktree canónico nominal)
estaba en branch huérfano `work-s78-bloque-arranque-s79` sin remote,
mostrando 17 workflows reproc-* activos cuando main ya los había archivado
en PR #217. El subagente confundió a Claude.

**Regla**:
- Al entrar a un worktree, verificar SIEMPRE:
  ```bash
  git fetch origin --prune
  git branch --show-current
  git log --oneline HEAD..origin/main  # ¿qué commits faltan?
  ```
- Si la branch local no es `main` y diverge de `origin/main` por más de
  10 commits, **no asumir que el estado del worktree refleja el estado
  del proyecto**. Cambiar a un worktree main-tracking o crear uno nuevo.
- Worktree canónico declarado en `CLAUDE.md` proyecto debe estar en branch
  que sigue `origin/main` (no en branch huérfano).

**Implementación**: actualizar `CLAUDE.md` raíz proyecto memoria con la
ubicación del worktree main-tracking. Cuando empiece sesión:
```bash
git fetch origin --prune
git log --oneline -1 origin/main  # confirmar HEAD remoto
```

---

## M7 — Bloque arranque debe ser self-contained

**Por qué**: BLOQUE_ARRANQUE_S80.md asumió que el lector sabe qué es F66,
qué pasó en S78 con NTI Path B, por qué A47 es vinculante. Cuando hay
pérdida de contexto, esos asumidos rompen.

**Regla**:
- Todo `tasks/BLOQUE_ARRANQUE_S<N>.md` debe linkear al inicio:
  1. `docs/SESSION_INDEX_CONSOLIDATED_S<latest>.md` como primera lectura
  2. Resumen de 3 líneas del estado actual (qué hicimos, qué falta, qué
     no tocar)
- Debe contener glosario inline de acrónimos no obvios (F66, A47, NTI
  Path B, etc.) o linkear al doc canónico que los define.

**Implementación**: usar `docs/SESSION_INDEX_CONSOLIDATED_S80.md` (§0
"Lectura de orientación rápida") como plantilla.

---

## M8 — Auditoría completa cada 20 sesiones

**Por qué**: S80 mostró que la pérdida de contexto se acumula
silenciosamente. Sin auditoría regular, el proyecto entra en estado
"funciona pero no sabemos por qué".

**Regla**:
- Cada **20 sesiones** ejecutar protocolo de auditoría completa, idéntico
  al ejecutado en S80:
  1. Subagente inventario sesiones (cronología + hallazgos)
  2. Subagente drifts/hipótesis/papers
  3. Subagente git activity (PRs/tags/branches/NRT health)
  4. Subagente profile flags vs código
  5. Subagente estado operacional dashboard
- Producir `docs/AUDIT_S<N>.md` con síntesis + contradicciones detectadas
  + plan de cleanup.
- Si la auditoría detecta >3 contradicciones, **pausar features nuevas**
  y consolidar primero.

**Próxima auditoría**: S100.

---

## M9 — Versionado de MEMORY.md (rotación al llegar a 800 líneas)

**Por qué**: MEMORY.md llegó a 762 líneas y solo cargaron las primeras al
contexto inicial. El warning del sistema lo enunció pero Claude lo había
ignorado. La pérdida de memoria estaba indexada en el propio MEMORY.md.

**Regla**:
- Cuando MEMORY.md pase de **800 líneas**, rotar:
  1. Mover detalle de sesiones cerradas (>10 sesiones atrás) a
     `docs/MEMORY_ARCHIVE_S<N1>_S<N2>.md`
  2. Mantener en MEMORY.md solo el índice (1 línea por sesión) + sesiones
     activas (últimas 5) + reglas vinculantes.
  3. Cap MEMORY.md ≤500 líneas estable.

**Implementación**: ejecutable como parte del `SESSION_CLOSE_CHECKLIST`.

---

## M10 — Subagentes paralelos para auditoría/inventario

**Por qué**: la auditoría S80 produjo 5 reportes de calidad en paralelo
porque cada subagente trabajaba sobre scope acotado con resumen ≤800
tokens. Si Claude hubiera hecho todo en su contexto principal, se habría
quedado sin espacio.

**Regla** (extensión A44):
- Para **auditorías read-only** sobre >10 archivos o >3 categorías:
  usar `Agent` con subagent_type `Explore` o `general-purpose`, scope
  bien acotado, pedir resumen ≤800 tokens.
- Para **trabajo paralelo de escritura**: cada subagente en su propio
  worktree (`git worktree add`). NO mezclar branches.
- Resultado del subagente debe ser autocontenido (tablas, paths
  absolutos). Claude principal sintetiza, no relee.

---

## SESSION_CLOSE_CHECKLIST v2 (resumen)

Detalle completo en `docs/SESSION_CLOSE_CHECKLIST.md`. Bloques obligatorios:

- **A. Persistencia hallazgos**: MEMORY.md + topic files actualizados
- **B. Tag defensivo** si hubo cambio en pipeline NRT
- **C. Tests passing** (cero regresiones vs baseline)
- **D. PRs mergeados ≤ cap M1**
- **E. BLOQUE_ARRANQUE_S<N+1>.md generado** con §0 plantilla M7
- **F. Prompt copy-paste-able** para próxima sesión (regla S79)

---

**Aplicación de estas reglas**: vinculantes desde S81 en adelante. Claude
debe invocarlas proactivamente sin que Nicolás las nombre. Si dudás si
aplicar una, aplicala (costo invocar bajo, costo de no invocar = pérdida
de contexto comprobada).

---

## Lecciones durables agregadas S84 (2026-05-28)

- **A56. Bypass parcial de funciones de tercero requiere preservar
  responsabilidades no-target**. Cuando se monkeypatch una función de
  biblioteca externa (earthaccess, requests, etc) para evitar un efecto
  colateral (un GET problemático, un timeout, una validación), hay que
  leer la implementación entera del original e identificar QUÉ MÁS hace
  esa función. Si el bypass se hace simplemente con `return None`, todas
  las otras responsabilidades del original quedan deshabilitadas.

  Caso concreto S77→S84: el bypass F55 a
  `earthaccess.store.Store.set_requests_session` se hizo `return None` para
  skipear el GET a `/profile` que NASA Azure throttle. Pero el original ANTES
  de ese GET inicializaba `self._http_session = self.auth.get_session()`.
  Sin esa inicialización, `download()` posterior fallaba silencioso con
  "session hasn't been set up yet". NRT 100% caído 4 días sin detectar.

  Fix correcto: bypass quirúrgico que preserva el setup:
  ```python
  if not hasattr(self, "_http_session"):
      self._http_session = self.auth.get_session()
  return None
  ```

  Ref: PR #225 + `pipeline/fetch.py:_patched_set_requests_session`.

- **A57. `set +e` + script Python tolerante + workflow exit 0 = "success"
  engañoso**. Cuando un GH Actions step usa `set +e` y el script Python
  no propaga errores con `sys.exit(1)`, el workflow termina exit 0 aunque
  CERO trabajo útil se haya hecho. Hay que validar **contenido**, no solo
  exit code.

  Anti-pattern detectado S84:
  ```yaml
  - name: Reproc
    run: |
      set +e
      python script.py  # falla silencioso, no exit
      git add data/...  # nada que add
      git diff --staged --quiet && { echo "No changes to commit"; exit 0; }
  ```

  Workflow marca success. Pero NO procesó nada. Bug propio de NRT desde
  2026-05-23 hasta detección S84 (~4 días con dashboard stale).

  Mitigación futura: agregar **assertion de contenido** post-script. Ej.:
  ```yaml
  - name: Assert records produced
    run: |
      python -c "
      import json, sys
      d = json.load(open('data/<subdir>/<vol>.json'))
      last_dt = d['records'][-1]['datetime_utc']
      assert last_dt.startswith('2026'), f'records stale: {last_dt}'
      "
  ```

  Pendiente B8 backlog: implementar este pattern en `nrt.yml` y reproc-ab*.

- **A58. NRT necesita health-check de staleness de records, no solo de
  file_updated**. El campo `updated` del JSON refleja el último commit
  del scraper Mirova-v1 (que actualiza `data/mirova/` paralelo) y no
  garantiza que nuestro pipeline haya procesado granules. Para detectar
  fallos silenciosos del pipeline hay que verificar:

  - `max(record.datetime_utc for record in records)` > `now() - 48h`
    para TODOS los Tier A.

  Si algún Tier A tiene `last_record` más antiguo que 48h, **alertar**.

  Implementación sugerida B9 backlog: un workflow cron `nrt-healthcheck.yml`
  que corra 1×/día y abra un issue automático si detecta staleness.

- **A60. Workflows archivados en `_archive/` no requieren fix de TOKEN
  porque no se ejecutan**, pero si alguno se desarchiva (movido de
  `.github/workflows/_archive/` a `.github/workflows/`) DEBE incluir
  `EARTHDATA_TOKEN: ${{ secrets.EARTHDATA_TOKEN }}` además de USERNAME/
  PASSWORD. Patrón: ver `nrt.yml` o `reproc-ab-f-s81-a-intra-radio.yml`.
  Sin TOKEN, NASA Azure throttle endpoint `/profile` rompe earthaccess
  download silenciosamente. Audit S85 P3 confirmó que los 2 workflows
  reproc activos (post fix S84) ya están OK.

- **A59. Reproc 45d × 8 sensores × N vols requiere timeout-minutes ≥ 140**
  (no 50 del NRT). Run 26537938176 (S84, post fix F55) demostró que jobs
  Tier A pesados (Lascar/Lastarria/PCC/Tupungatito) requieren ~125 min
  para 45 días. NRT 1 día cabe en 50 min holgado pero reproc no. Default
  workflows `reproc-ab-*` debe ser **timeout-minutes: 140 step + 150
  job-level**. Doc operacional: ver workflow `reproc-ab-f-s81-a-intra-radio.yml`
  como template.
