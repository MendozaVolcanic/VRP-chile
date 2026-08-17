# Bloque de arranque S124

> Escrito al cierre de S123 (2026-08-17). Leer **antes** de empezar trabajo.
> Ancla de estado: [`docs/AUDIT_S123.md`](../docs/AUDIT_S123.md).

## Primer comando

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
gh api -i repos/MendozaVolcanic/VRP-chile 2>/dev/null | grep -i "^date:"   # A86: anclar "hoy" al servidor
ls docs/AUDIT_S*.md | sort -V | tail -1
```

**A86 (nueva)**: no razones con la fecha de memoria. En S123 estuve 8 días tratando
timestamps viejos como si fueran de hoy y reporté "5 días" donde eran 13. Pedí la hora al
servidor y se resolvió en un comando.

**Nota de red**: `git pull` en esta máquina puede tardar >10 min (repo 4.25 GiB). Si
timeoutea, lanzalo en background y trabajá contra el remote con `gh api` mientras tanto.

## Estado en una línea

NRT **sano** (verde desde 04-ago, sin hueco: el backfill 21-jul→02-ago está commiteado).
Alertas rediseñadas y verificadas en producción. P0 de credencial NASA **cerrado**. Panel
Eq.16 **reparado**. Queda un frente físico nuevo (#506 Villarrica) y 5 decisiones de Nicolás.

## Lo que pasó en S123

| PR / commit | Qué |
|---|---|
| #502 | `concurrency: push-main` en los 6 workflows que pushean + Node 20 → 24 (17 refs, 0 residual) |
| #503 | Alertas **por incidente, no por corrida**: escalones 48h/72h/7d/14d/30d + cierre automático |
| `a7be3d81` | **Reparación de regresión propia**: `audit-weekly` fuera del grupo `push-main` |
| #507 | `EarthdataCredentialError` — credencial muerta aborta, host caído sigue degradando |
| #508 | Panel Eq.16: restaurado el JSON desde el tag + fuera del `.gitignore` + fallback honesto |
| — | Triage de 4 issues de paridad: #499/#500/#504 cerrados, #505 vigente, **#506 abierto** |

## Empezar por acá (en orden de valor)

### 1. #506 Villarrica — el único frente físico nuevo

Villarrica pasó de 0 píxeles del path BT y 0.060 MW (abr-may) a **482 píxeles y 2.107 MW**
(ago). Escalón fechado en junio, coincidente con el anillo [1.5, 3] de #439/#440. Mecanismo
probable: A69 reintroducido (el anillo sube por el cono nevado → baja el fondo → el path de
MIR absoluto toma el flanco tibio-por-altitud como anomalía).

**Siguiente paso, read-only y barato**: probe A/B del anillo [1.5,3] vs [2,4] sobre
Villarrica **y** sobre el caso NdC 16-jun que motivó el cambio, midiendo **por separado**
el efecto en magnitud y en trigger (A79: un revert plano probablemente pierde el trigger
de NdC). No tocar `process_viirs.py` sin tag + visto bueno (A45).

Antes de proponer supresión: clasificar cuánto de esos 305 píxeles es artefacto y cuánto
halo real del lago (A54/A72). Si es real, suprimirlo destruye valor.

### 2. VIIRS750 — el eslabón débil medido, sin frente asignado

Recall 77-83% global, pero Tupungatito 46% + magnitud 7.47×, PP 43%, Isluga 66%. D12
atacaba MODIS y se agotó; nadie abrió este. Empezar por diagnóstico, no por fix.

### 3. Guarda de cobertura en el auto-audit

Hoy una caída del NRT le hace abrir issues de recall automáticamente (pasó 3 semanas
seguidas). Debería contar las noches sin granules en la ventana y excluirlas del
denominador, o degradar a WARN. Barato y evita repetir el ruido.

### 4. Retry de push en los 3 que no lo tienen

`nrt-retry`, `backfill` y `reproc` siguen en `push-main` porque **no** tienen bucle de
reintento. Dárselo (patrón de `audit-weekly`: 4 intentos con `pull --rebase -X theirs`) y
después evaluar si el grupo compartido sigue haciendo falta. Lección A85 aplicada a infra:
la cerca solo sirve donde el componente no se protege solo.

## Decisiones de Nicolás (bloquean trabajo)

1. **D12** — cierre formal como irreducible. C2 peak-of-kernel refutado en S122 (el pico
   del blob solapa con nevados); FN cubiertos 98% por VIIRS375. **Recomendado: cerrar.**
2. **Contradicción per-volcán vs MISSION** — `enable_local_kernel_bg` (5 vols),
   `enable_test1_lbg_global`, `enable_test1_intermediate_bg` conmutan método por volcán,
   contra `MISSION.md:74-79`. Salidas: excepción documentada / método uniforme / redefinir
   el borde. Lo indefendible es la contradicción tácita.
3. **Arquitectura de datos** — `filter-repo` (autorizado S121, sin ejecutar) y/o repo
   satélite. Lo segundo es la cura: el bloat es la historia (~30 MB/día), no el árbol.
4. **Rotar el PAT** de `~/.claude/settings.json` (5 min suyos; A71: no tocar credenciales).
5. **M1 zonas 2ª** — 30-45 min frente al mapa, desbloquea M4.

## No reabrir (anti-A8)

D9 (S113) · D11 far→summit MODIS (S114, A82) · gates intra-radio S84/S85 (S118, A85) ·
GAP #A (S115, mislabel) · re-ancla `ctx_cluster` (S117, A84) · discriminante físico
universal cat-b vs artefacto (S116, A83) · C2 peak-of-kernel (S122).

## Reglas nuevas de S123

- **A86** — anclar "hoy" al servidor en sesiones largas.
- **A87** — un flag que se apaga no prueba que el problema se fue: verificar el mecanismo
  en los records antes de cerrar por "ya no aparece".
- **A88** — si un directorio de datos pasa a alimentar el frontend, sale del `.gitignore` y
  entra al inventario de poda **en el mismo PR** que publica la vista.
