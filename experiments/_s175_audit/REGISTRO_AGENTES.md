# Registro de agentes S175

Plan sellado: `docs/PLAN_AUDITORIA_S175.md`, SHA_PLAN = `a325ac8ff8c480fc88fe91d07b1b52046d0c0997`.

## Ola 0 (2026-11-07, hora del servidor Sat, 07 Nov 2026 04:10:15 GMT)

- SHA_BASE = `752d348bc67190e53b610989877e2405d238a1bc` (`origin/main`); SHA_LOOP = `395af8034a3146ffd1d20575f290d7313a71707a`.
- sha256 (contenido de `git show SHA_BASE:<ruta>`, LF):
  - `latest_consolidado.csv`: dee768374b84d49bf39f07c4ade69e71ecf9627528547a5e0a91ca27fbdf45b8
  - `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` (el que leen el audit y el banco): f833bfdef7c3fc5f0b5bb6822ee7225d81dbff6a696ba1c62361b08fe5a9ea4d
  - `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv`: 577a336e76383a672a89ab86f6fe5cd5e69e4dbbde2ff8effdce2074f3d74cc9
- Instantánea: `C:\Users\nmend\vrp-temporales\s175_audit\main\` (29 MB, `git archive` con rutas).
- Insumos: `C:\Users\nmend\vrp-temporales\s175_audit\insumos\` (corridas de 6 workflows, commits de Mirova-v1, nombres de secretos, índices TIF y PNG del archivo, copias de los tres CSV en la base). `rate_limit` 4.936 de 5.000.
- Discos: C: 11 GB libres, D: 4,9 GB.

| agente | modelo | effort pedido | esfuerzo declarado | tokens | duración | resultado |
|---|---|---|---|---|---|---|
| sonda | Fable | high | `reasoning_effort 25` (etiqueta literal en su contexto) | 89.983 | 12 s | **BAJO**: `effort: high` del Agent tool no llega; se para antes de la ola 1 (§5 del plan) |
| F5 | Opus 5.5 (sesión `local_9fb8f14e`, se pidió Fable y la app la abrió en Opus: una sesión sólo puede abrir otras de su familia o más baratas) | high (fijado por la app al abrir la sesión) | lo declara en su informe | | lanzada 2026-11-07 04:16 UTC | prompt `C:\Users\nmend\vrp-temporales\s175_audit\prompts\f5.txt` sha256 37373a88... |
| F2 | Opus 5.5 (sesión `local_ba163e3e`) | high (app) | lo declara en su informe | | lanzada 2026-11-07 04:17 UTC | prompt `...\prompts\f2.txt` sha256 df7b928d... |

Consecuencia para los verificadores: los auditores son Opus, así que los verificadores serán de otro modelo, Sonnet en sesión con esfuerzo high (Fable como subagente corre a 25). Se declara en la síntesis.

## Encargos extra preparados el 2026-11-08 (sin lanzar: uso semanal en 93 %, reinicio 2026-11-08 12:00 UTC)

Pedido de Nicolás: «procede con todo en simultáneo si es posible». Se dejaron listos para lanzar después del reinicio,
cada uno como subagente Fable con `effort: high` (el pedido sí llega, ver limitación 1 de `docs/AUDIT_S175.md`):

| encargo | prompt (en `C:\Users\nmend\vrp-temporales\s175_audit\prompts\`) | sha256 (16) | carpeta | verificador después |
|---|---|---|---|---|
| VX: verificar 302, 108, 111 y 256 | `vx.txt` | be32c28e81cb42a9 | `experiments\_s175_audit\vx\` | ya es verificador (auditores Opus) |
| F5b: posición después del 2026-09-22 con las láminas PNG Latest10NTI | `f5b.txt` | cdc4ffb869a63cff | `experiments\_s175_audit\f5b\` | Opus, sin ver el informe |
| F4t: el token muerto simulado (parte de F4, antes de rotarlo el 2026-11-27) | `f4t.txt` | c62aca6c19b66b99 | `experiments\_s175_audit\f4t\` | Opus, sin ver el informe |
