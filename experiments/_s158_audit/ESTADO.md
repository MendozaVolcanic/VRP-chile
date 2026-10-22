# Estado de la auditoría S158 (para retomar si la sesión se corta)

> Escrito el 2026-10-21 antes de lanzar los auditores, a pedido de Nicolás («quizas puedes guardar el estado antes»).
> Rama `s158-d17-diseno`, PR #885 (borrador). Worktree `D:\vrp-trabajo\temporales\s158_d17`.

## Hecho y subido

- Código de MIROVA V750 bajado y verificado por hash: `experiments/_s158_d17_diseno/osf_codigo_mirova/`.
- Comparación de 13 puntos y dónde nos equivocamos de juicio: `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`.
- Diseño de D17, grilla UTM de MIROVA, curva angular: `docs/DISENO_D17_REMUESTREO_UTM.md`.
- Plan de auditoría: `docs/PLAN_AUDITORIA_S158.md` (frentes F1 a F6, verificadores V1 a V3, bloque común §4,
  alcance de cada frente §5).
- **Fase 0 cumplida**: oráculo en `experiments/_s158_oraculo_mirova/` (reproduce la pasada de Etna de MIROVA: mismos 5
  píxeles, VRP a 0,09 %), pruebas en `tests/test_oraculo_mirova_v750_s158.py`.
- Vigilante de OSF: `scripts/vigilar_osf_mirova.py` y `.github/workflows/vigilar-osf-mirova.yml`.

## Decisión de Nicolás

«Oráculo aquí y luego los 9» (2026-10-21): seis auditores en paralelo y tres verificadores, como subagentes de esta
sesión (no sesiones aparte: el disco no alcanza para worktrees nuevos), cada uno escribiendo en su carpeta
`experiments/_s158_audit/f1/` a `f6/` y `v1/` a `v3/`.

## Cómo retomar

1. `git log --oneline -10` y `git status` en el worktree, no suponer el estado.
2. Mirar qué carpetas `experiments/_s158_audit/f*/INFORME.md` existen y si cierran con «Lo que no pude medir»: un
   informe sin esa sección quedó cortado.
3. Relanzar sólo los frentes incompletos con el prompt del plan: el bloque canónico de
   `docs/_prompts/PREAMBULO-AUDITOR.md` entero, el bloque común del §4 de `docs/PLAN_AUDITORIA_S158.md`, el alcance del
   §5, y la línea «Retoma: lee tu INFORME.md parcial y sigue desde donde quedó, no lo rehagas».
4. Con los seis informes, lanzar V1 (F1 y F6), V2 (F2 y F5) y V3 (F3 y F4) con sólo la lista de hallazgos de gravedad
   3 o más (título, ubicación, gravedad).
5. Síntesis en `docs/AUDIT_S158.md` con la tabla de decisiones de Nicolás; marcas A113 en el mismo PR.

## Lanzamiento

| frente | estado |
|---|---|
| F1 a F6 | lanzados el 2026-10-21 como subagentes en segundo plano (F2 y F4 en Fable, el resto en Opus, esfuerzo alto); prompt = bloque canónico + §4 + §5 del plan, con carpeta y presupuesto de dos horas |
| F1 a F6 | **terminados**; informes en f1/ a f6/ (commit 56ec42c6b) |
| V1 a V3 | **terminados** (commit 928ec40bf); lanzados el 2026-10-21 (Opus, esfuerzo alto): V1 = F1 y F6 (7 hallazgos), V2 = F2 y F5 (4), V3 = F3 y F4 (6); sólo título, ubicación y gravedad |
| síntesis | **hecha**: docs/AUDIT_S158.md |
| segunda ronda | aprobada por Nicolás; **C: ya tiene 31 GB libres** (2026-10-21); la lanza Nicolás en una sesión nueva con el prompt del brief |
| segunda ronda | **hecha** el 2026-10-21 en la rama `claude/s158-audit-r2-0eeee2`: `docs/AUDIT_S158_R2.md`, material en `experiments/_s158_audit_r2/`, veredictos propios commiteados antes de leer la primera ronda (`26c9d078a`) |
| sesión S158 de diseño y auditoría | **cerrada** el 2026-10-21: todo commiteado y subido (PR #885); temporales borrados; datos de Vulcano re-bajables con `experiments/_s158_d17_diseno/bajar_jepv6.py` |

## Pendiente, con dueño

- Segunda ronda (brief en `BRIEF_SEGUNDA_RONDA.md`): segundo oráculo, replicación, meta-auditor, prueba con gránulos chilenos, marcas A113 de la tabla de F2, guía de revisión visual.
- Adenda D25 con el fondo del código: su sesión falló por disco; conviene relanzarla **después** de que la segunda ronda confirme el hallazgo del fondo (decisión 1 de `docs/AUDIT_S158.md` §4).
- Decisiones de Nicolás: tabla del §4 de `docs/AUDIT_S158.md`.
- PR #886 y #887 (sesiones hermanas, borradores abiertos): llegaron por su cuenta a que el fondo del anillo deja cumbres en 0 MW; los revisa la sesión que los lanzó.
