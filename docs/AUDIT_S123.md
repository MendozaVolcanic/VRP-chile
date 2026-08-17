# AUDIT_S123 — Auditoría integral (6 ejes) + sprint de cierre

> **Fecha**: 2026-08-17 · **Método**: 6 subagentes read-only en paralelo (misión/fidelidad,
> operacional NRT, docs/memoria, frontend, desempeño por modo, repo/tests/seguridad) +
> verificación propia de los hallazgos accionables.
> **Regla A51**: auditoría integral cada ~20 sesiones. La anterior fue `AUDIT_S122` (02-ago).

---

## 0. Advertencia de método (leer antes que nada)

Esta auditoría empezó el 09-ago y se cerró el 17-ago. **Durante el tramo intermedio yo
seguí razonando con la fecha del 09-ago**, tratando timestamps de hace 8 días como si
fueran de hoy. Lo detecté recién al chocar con un issue "del futuro" (#504, 10-ago) y
resolverlo pidiendo la hora del **servidor** (`gh api -i` → header `Date`).

Consecuencia concreta: el informe intermedio decía "NRT verde hace 5 días" cuando eran
13, y dio por fresco un healthcheck que ya tenía una semana.

**Regla que sale de acá (A86)**: en sesiones largas o retomadas, la fecha del razonamiento
se ancla al **servidor** (`gh api -i`, header `Date`), no a la memoria de la sesión ni al
último timestamp leído. Antes de afirmar "hoy", "hace N días" o "reciente", pedir la hora.
Un timestamp leído hace 20 mensajes no es "ahora".

---

## 1. Estado por eje

### 1.1 Misión y fidelidad — sano, con una contradicción de fondo

**Cerrado y consolidado** (no reabrir, anti-A8): D1, D4, D5, D6, D7, D8; **D9** (S113, sus
dos caras); **D11 cara far→summit** (S114, irreducible A82); **gates intra-radio S84/S85**
(flip OFF S118, verificado S119); **GAP #A** (mislabel S115). Irreducibles A83/A84/A85.

**Abierto con próximo paso**: **D12** (FN MODIS). El Paso 0 de C2 peak-of-kernel se
ejecutó (S122, read-only, con refutación adversarial) y el veredicto es **no viable**: el
pico del blob path-D solapa con el de los nevados (Láscar [2.23, 4.52] MW vs nevados
[1.42, 4.26]). Costo del FN: 71 noches, mediana 1.06 MW, con **98% de cobertura por
VIIRS375** (A77: a 1 km MODIS es el instrumento equivocado para focos sub-píxel).
`AUDIT_S122.md:143` deja el cierre formal **pendiente de Nicolás**.

**Abierto sin plan**: D2 y D3, congeladas desde S27. D2 quedó mitigada de facto por el
loader CONS∪OCR de S86, pero el doc nunca se actualizó. **NEW-8** está medido (0 FPs
residuales, no accionable) y es formalmente abierto pero sin síntoma.

**La contradicción de fondo (no resuelta, decisión de Nicolás)**: tres flags de fondo
local — `enable_local_kernel_bg` (5 volcanes), `enable_test1_lbg_global`,
`enable_test1_intermediate_bg` — **conmutan método por volcán** vía `volcanoes.yaml`,
contra `MISSION.md:74-79`, que es el mismo criterio con que se rechazó Eq.16 en S99 y el
A/B per-régimen en S118. Cada flag se adoptó con A/B y evidencia; el **agregado** es lo
que la misión prohíbe, y nunca se puso sobre la mesa como decisión explícita.

### 1.2 Operacional NRT — sano; una regresión propia detectada y reparada

NRT verde desde el 04-ago (13 días corridos, run #1279 al cierre). Sin pipelines zombie en
la muestra. `sync-mirova-csv`, `nrt-retry` y `pages-deploy` verdes.

**Regresión introducida por esta misma sesión y corregida**: el `concurrency: push-main`
del PR #502 dejó a `audit-weekly` encolado tras el lock que `nrt.yml` ocupa ~50 min de
cada 2 h; llegó otro run del grupo y GitHub descartó el pendiente → `cancelled`. Perder el
turno es inocuo para un cron horario y **caro para uno semanal**: se perdió la auditoría de
paridad de la semana. Reparado sacándolo del grupo (commit `a7be3d81`) — su push **ya era
robusto por sí solo** (bucle de 4 intentos con `pull --rebase`), así que el grupo no le
aportaba protección, solo le quitaba la corrida.

**Lección A85 aplicada a infraestructura**: puse una cerca donde ya había protección. De
los 6 workflows del grupo, 3 (`nrt`, `sync-mirova-csv`, `audit-weekly`) ya tenían retry
con rebase. Frente pendiente: dar retry a los 3 que no lo tienen (`nrt-retry`, `backfill`,
`reproc`) y evaluar si el grupo compartido deja de hacer falta.

### 1.3 Alertas — rediseñadas y verificadas en producción

Antes: en la caída de 13 días los 3 canales emitieron ~180 avisos para **un** incidente
(~9 correos/día del gate A57 + 4 comentarios/día de `nrt-monitor` + 1 del healthcheck), y
**ninguno avisaba la recuperación** (#498 y #336 quedaron abiertos con el sistema sano;
#336 llevaba desde el 04-jun con 58 comentarios).

Ahora (PR #503): A57 **avisa sin fallar** el run; el healthcheck escala por antigüedad
(48 h → 72 h → 7 d → 14 d → 30 d) **editando** el cuerpo (no notifica) y comentando solo al
cruzar escalón; ambos canales **cierran** su issue al recuperarse.

**Verificado en producción, no solo en diseño**: #498 y #336 se cerraron solos en vivo, y
en los 8 días siguientes hubo **8 healthchecks verdes y cero issues nuevos** con el sistema
sano. La misma caída de 13 días habría generado ~4 avisos en lugar de ~180.

Además se eliminó una **auto-perpetuación**: al fallar A57 se saltaba el commit (el step no
tenía `if: always()`), así que un volcán stale que recibiera un granule de más de 72 h veía
su dato descartado y no salía nunca del estado stale — el gate sostenía la condición que
denunciaba.

### 1.4 Credencial NASA — cerrado el P0(3) de AUDIT_S122

El 20-jul expiró el token y el pipeline aplicó política de red a un problema de
credencial: reintentar, degradar, seguir → 13 días de cron verde sin datos.

Causa exacta: `earthaccess` ≥0.17 envuelve el rechazo HTTP en
`RuntimeError(response.text)`, que **no** está en `_CMR_SEARCH_ERRORS` (correcto: no debe
tripear el breaker de red) y por eso subía intacto al catch-all de `fetch_for_volcano`. El
401 real sobrevive en `__cause__.response`.

Fix (PR #507, TDD, 823 tests verdes): `EarthdataCredentialError` — 401 siempre aborta; 403
y status ausente **solo** si el cuerpo habla de la credencial, porque NASA usa 403 también
para EULA no aceptada y throttling, y abortar por eso mataría el NRT entero por un sensor.

### 1.5 Frontend — funciona; un panel estaba roto en silencio

Sitio y datos verificados en vivo: las 3 vistas cargan `_recent.json` (ninguna quedó
apuntando al JSON completo), `latest_consolidado.csv` se auto-sincroniza, la vista Beyond
MIROVA existe y responde.

**Roto y reparado (PR #508)**: el panel "2b Eq.16" pedía `data/_s99_test1_eq16/Villarrica.json`,
borrado por la poda S121 → 404 durante ~2 meses. Nadie lo notó porque degradaba de forma
engañosa: el panel afirma un resultado medido y debajo mostraba "aún sin data, corré el
workflow", como si el experimento nunca se hubiera ejecutado.

**Causa raíz** (vale como regla): el directorio era un A/B descartable **hasta que S120
publicó una vista que lo consume**. Esa reclasificación tácita de experimento a dependencia
de producción no actualizó ni el inventario de poda ni el `.gitignore`. Restaurado desde el
tag `pre-s121-data-prune` y sacado del `.gitignore` con la razón escrita.

**Deuda de display pendiente** (decisión ya tomada, sin implementar): PCC "extensión
naranja, no summit" (A68) y la migración de las supresiones de artefactos a fix de
algoritmo (A72).

**Riesgo estructural**: los helpers están triplicados en las 3 vistas y su equivalencia es
manual, sin test de paridad (regla S92 L5 sin red).

### 1.6 Desempeño por modo

**Operacional** (última medición, ventana 60 d al 17-ago): ratio **3/3 sensores en banda**
(MODIS 0.75, VIIRS750 0.81, VIIRS375 0.68); recall al cráter VIIRS375 92-95%, VIIRS750
77-83%, MODIS ~100%. La precisión formal es <0.50 en los 3 pero por A54 la mayoría de esos
"FP" es señal física real sub-umbral que MIROVA no publica — no leerla como error.

**El eslabón débil medido es VIIRS750** (Tupungatito 46% recall + 7.47× magnitud, PP 43%,
Isluga 66%) y **no tiene frente asignado**: D12 atacaba MODIS y se agotó.

**Experimental**: M1 zonas 2ª (8 volcanes) sin avance, bloqueado en Nicolás (30-45 min
frente al mapa, desbloquea M4). M2 AVTOD con **premisa refutada** — AVTOD no publica VRP en
watts (mide °C sobre fondo con ASTER) y la serie por fecha está en una Table S1 que no
tenemos: cerrar como estaba scopeado y re-scopear a la vía categórica. Backfill P4
pendiente. Paper Volcanica: hay esqueleto con números S119, no manuscrito.

### 1.7 Repo, tests y seguridad

- **Suite completa: 823 passed, 0 failed** (con el checkout al día).
- **No hay CI de pytest en PRs**: la validación depende de disciplina (A39). Riesgo medio.
- **Repo remoto 4.25 GiB**, creciendo ~30 MB/día. El bloat es la **historia**, no el árbol
  (`data/` ~645 MB casi plano): cada corrida NRT commitea JSONs 12 veces al día y git
  guarda toda versión. El `filter-repo` autorizado en S121 quedó **diseñado sin ejecutar**,
  y la arquitectura sostenible (repo satélite de datos) sigue sin decisión.
- **PAT de GitHub en `~/.claude/settings.json` en texto plano**: sigue ahí, pendiente de
  rotar. Es el hallazgo #1 de seguridad y lleva meses. Fuera de eso, limpio: sin
  credenciales en versionados, sin `.env`/`.netrc` trackeados.

---

## 2. Hallazgo del triage de paridad (issues #499/#500/#504/#505)

**Tres semanas seguidas de "auto-audit FUERA DE BANDA" sin triage.** Resultado:

**El recall bajo era contaminación del hueco de datos.** El auto-audit cuenta las noches
ciegas en el **denominador** del recall — MIROVA publicó y nosotros no — cuando en realidad
no miramos. La magnitud, en cambio, se calcula solo sobre noches en que sí detectamos, así
que el hueco no puede moverla: esa asimetría es la que separa ruido de señal. Medido: el
recall cae con la caída y se recupera con el backfill (VIIRS375 97.8 → 79.4 → **95.3**).
Cerrados #499, #500 y #504.

**Deuda que deja**: el auto-audit **no tiene guarda de cobertura** — una caída del NRT le
hace abrir issues de recall automáticamente. Debería excluir del denominador las noches sin
granules.

**Lo que el hueco NO explica → [#506](https://github.com/MendozaVolcanic/VRP-chile/issues/506)**:
Villarrica pasó de 0 píxeles del path BT y 0.060 MW medianos (abr-may) a **482 píxeles y
2.107 MW** (ago) — 35× la magnitud, con el escalón en junio, coincidente con el anillo
[1.5, 3] adoptado en #439/#440 (17-jun). No es estacional: el invierno 2025 con el mismo
ΔT daba 0 píxeles BT. Mecanismo probable: al muestrear el fondo más cerca del cráter el
anillo sube por el cono nevado, baja el fondo de referencia, y el path de **MIR absoluto**
toma el flanco tibio-por-altitud como anomalía — **A69 reintroducido**.

**No se tocó el pipeline** por tres razones: A79 (el anillo se adoptó para recuperar un
trigger real de NdC; un revert plano probablemente lo pierde), A54/A72 (falta clasificar
cuánto de esos 305 píxeles es artefacto y cuánto halo real del lago) y A45 (tag +
confirmación de Nicolás).

**Nota de método**: el auto-audit de hoy ya **no** marca a Villarrica, porque la magnitud
solo se evalúa donde MIROVA también publicó y ese `n` es chico. **El flag desapareció; el
fenómeno no.** Un flag que se apaga no es prueba de que el problema se fue.

---

## 3. Qué queda — clasificado

**Decisiones de Nicolás** (no las puedo tomar yo):
1. Cierre formal de **D12** como irreducible (recomendado: cerrar).
2. **Contradicción per-volcán vs MISSION**: documentar como excepción, converger a método
   uniforme, o redefinir el borde de la misión.
3. **Arquitectura de datos**: ejecutar `filter-repo` (destructivo, ya autorizado) y/o mover
   la data NRT a repo satélite. Lo segundo es la cura; lo primero sin lo segundo se
   revierte en meses.
4. **Rotar el PAT** (5 minutos suyos; yo no debo tocar credenciales — A71).
5. **M1**: 30-45 min de su ojo de geólogo frente al mapa.

**Frentes técnicos abiertos, por valor**:
1. **#506 Villarrica** — probe read-only del anillo [1.5,3] vs [2,4] midiendo por separado
   magnitud y trigger, en Villarrica **y** en el caso NdC que motivó el cambio.
2. **VIIRS750** — el eslabón débil medido, sin frente asignado.
3. **Guarda de cobertura en el auto-audit** — evita repetir 3 semanas de falsos issues.
4. **Retry de push** para `nrt-retry`/`backfill`/`reproc`; después, evaluar si `push-main`
   sigue haciendo falta.
5. **CI de pytest en PRs** — hoy la única red es la disciplina.
6. **Test de paridad de los helpers** triplicados del frontend.

---

## 4. Reglas nuevas

- **A86 — anclar la fecha al servidor en sesiones largas.** Ver §0. Antes de afirmar "hoy",
  "hace N días" o "reciente", pedir la hora al servidor (`gh api -i`, header `Date`). Un
  timestamp leído hace 20 mensajes no es "ahora"; una sesión puede abarcar días.
- **A87 — un flag que se apaga no prueba que el problema se fue.** Las métricas con ventana
  rodante y `n` chico pueden dejar de marcar un fenómeno que sigue vivo (caso Villarrica).
  Antes de cerrar por "ya no aparece", verificar el **mecanismo** en los records.
- **A88 — si un directorio de datos pasa a alimentar el frontend, deja de ser descartable
  en el mismo PR que publica la vista.** Sale del `.gitignore` y entra al inventario de
  poda con la razón escrita. La reclasificación tácita de experimento a dependencia de
  producción es lo que rompió el panel Eq.16 durante 2 meses.
- **A85 vale para infraestructura, no solo para gates físicos.** Antes de agregar una cerca
  (concurrency, gate, guard), medir si el daño que evitaría existe y si el componente ya se
  protege solo. `audit-weekly` ya tenía retry; la cerca solo le costó su corrida semanal.
