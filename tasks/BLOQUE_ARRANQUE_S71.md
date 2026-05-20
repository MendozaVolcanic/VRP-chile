# BLOQUE DE ARRANQUE S71 — VRP Chile

> Continuación tras cierre S70 (S70-0 + S70-1 + S70-2). PRs **#103 + #106 + #107 ya mergeados a `main`** (2026-05-20).
> Hallazgo crítico abierto: **D9 — bug path D dNTI ctx en cirrus alto**.

---

## 1. Pre-condición antes de arrancar S71

**Estado main al cierre S70**: commits S70-0 + S70-1 + S70-2 integrados. Verificar:

```bash
git fetch origin && git log origin/main --oneline -5
# Debe mostrar merges 103/106/107
```

Validar **NRT cron post-fix** (PR #103 incorporó probe atmosférico + workflow retry):

```bash
gh run list --workflow nrt.yml --limit 10 --json conclusion,createdAt | python -c "import json,sys; d=json.load(sys.stdin); s=sum(1 for r in d if r['conclusion']=='success'); print(f'Success: {s}/{len(d)} ({100*s/len(d):.0f}%)')"
```

Si NRT success rate ≥80% → fix validado, seguir T1. Si <80% → **T0 prioritario: diagnóstico nuevo** antes de T1 (el probe atmosférico no resolvió, hipótesis distinta a NASA timeout).

Cerrar **issue #1** cuando ≥80% confirmado:

```bash
gh issue close 1 --comment "Fix S70-0 validado post-merge. Success rate: X/10."
```

---

## 2. Priorización (en orden, ejecutar sin saltarse)

### T1 — Fix path D dNTI ctx en cirrus (D9) — **PRIORIDAD ALTA**

**Decisión metodológica de Nicolás (S70-2)**:
> "Debemos seguir la información que esté en los papers o probar diferentes alternativas hasta llegar a la réplica de MIROVA."

#### Fase 1: lectura de papers (papers-first)

Leer en orden:
1. **Coppola 2016a §SP 426.5** — introducción del dNTI contextual. Buscar: ¿menciona comportamiento en cirrus, t_bg cold, o gate atmosférico?
2. **Campus 2024** — métodos MIROVA actualizados. ¿Hay update sobre dNTI ctx?
3. **Coppola 2024 cap Springer** — método actual MIROVA NRT. ¿Cómo MIROVA real evita FPs en cirrus?
4. **Aveni 2024 RSE TIRVolcH** — Tier A Muy Bajo, posible discusión de fondo frío.

Si los papers MIROVA dan **respuesta explícita** sobre cómo manejar cirrus en path D → implementar literal lo que dicen. Listo.

Si los papers **no resuelven** → fase 2.

#### Fase 2: A/B test alternativas (solo si fase 1 no resuelve)

Probar 3 alternativas con profile flag aislado (NO tocar `mirova_equivalent.yaml` operacional):

- **Alternativa A** — gate atmosférico: `enable_dnti_contextual_path: true` pero skip cuando `t_bg_k < 260K` (o threshold a calibrar).
- **Alternativa B** — co-validación obligatoria: path D solo cuenta si BT path O NTI path también dispararon (path D no cuenta solo).
- **Alternativa C** — cap de magnitud: si path D fue único trigger Y `t_bg_k < 270K`, cap `pc.vrp_mw` a límite razonable (ej. 2 MW Tier A Muy Bajo).

Profiles a crear:
- `pipeline/profiles/mirova_equivalent_path_d_atm_gate_v1.yaml` (Alt A)
- `pipeline/profiles/mirova_equivalent_path_d_covalidation_v1.yaml` (Alt B)
- `pipeline/profiles/mirova_equivalent_path_d_cap_v1.yaml` (Alt C)

Cada profile con `data_subdir` aislado para no contaminar operacional.

Workflows A/B (clonar de uno existente — el #103 reorganizó archivados):
- `reproc-ab-path-d-atm-gate.yml`
- `reproc-ab-path-d-covalidation.yml`
- `reproc-ab-path-d-cap.yml`

Cada uno corre los 11 vols Tier A 90 días + audit contra MIROVA NRT (consolidado + OCR).

**Criterio de winner**:
- Mediana ratio per-vol ∈ [0.5-2.0]
- Recall MIROVA ≥0.70
- Precision ≥0.50
- Ningún record con `pc.vrp_mw >5 MW` sin co-validación BT/NTI o con `t_bg_k <260K`

Adoptar el winner en `mirova_equivalent.yaml` operacional. Documentar D9 como RESUELTO + entry HYPOTHESIS_LOG.

**Costo estimado**: 3-5h (fase 1 lectura ~1h, fase 2 si necesaria ~2-4h)

---

### T2 — Cluster selection residual (PP Modo B + Tupungatito 43%) — **PRIORIDAD MEDIA**

S70-2 T1 (PP multi-caso) identificó distribución bimodal: pipeline a veces aísla cráter (Modo A ratio ~1×), a veces se va al halo regional del complejo (Modo B ratio 10×). Mismo mecanismo subyacente que Tupungatito 43% residual (S66+).

**Decisión metodológica**: misma que T1 — papers MIROVA primero (¿discuten cluster selection en complejos multi-cráter o lacolitos extendidos?), después A/B si no resuelven.

Por ahora dejar como pendiente arquitectural — requiere investigación dedicada.

---

### T3 — MODIS final_hotspot fix — **PRIORIDAD BAJA**

Identificado S62 paralelo. `final_hotspot.lat/lon` asigna al pixel más caliente individual de la escena MODIS, no al cluster summit. Diferente de D9 (D9 es path D, T3 es selección de hotspot post-cluster). Abordar después de D9 resuelto.

---

### T4 — Frontend bugs 6-11 — **PRIORIDAD BAJA**

Plan ya escrito en `tasks/frontend_bugs_s67_remaining.md`. Implementación es polish UX, no afecta correctness del pipeline. Sesión dedicada cuando bandwidth.

---

### T5 — Goldens regenerar (16 tests skipped) — **DESPUÉS DE T1**

Bloqueado por T1: regenerar goldens contra pipeline con bug path D conocido los atraparía como "golden". Esperar fix path D adoptado.

---

## 3. Estado de hallazgos S70 (referencia rápida)

| Doc | Contenido | Estado |
|---|---|---|
| `docs/MIROVA_DIVERGENCES.md` D6 | TIF no es VRP per-pixel sumable | Cerrada |
| `docs/MIROVA_DIVERGENCES.md` D7 | Bandas gates R2 por régimen del vol | Cerrada |
| `docs/MIROVA_DIVERGENCES.md` D9 | **Bug path D cirrus** | **Abierta — fix T1 S71** |
| `docs/HYPOTHESIS_LOG.md` H_S70_TIF_VRP_SUMABILITY | TIF dual verdict | Confirmada |
| `docs/HYPOTHESIS_LOG.md` H_S70_R2_RETROACTIVO_4VOLS | 5/5 Tier A R2 evaluados | Confirmada |
| `docs/HYPOTHESIS_LOG.md` H_S70_PATH_D_CIRRUS_FP | Bug path D | Confirmada — fix pendiente |
| `docs/R2_GATES_BY_REGIME.md` | Bandas gates por régimen | Activo |

---

## 4. Calidad sobre tokens (S71+)

**Regla operativa final S70-2** (Nicolás): "olvida la restricción de tokens, tenemos que gastar lo que corresponda para que podamos hacer un buen trabajo".

**Gastar los tokens que sean necesarios para hacer buen trabajo**. NO optimizar costo si compromete calidad. Las herramientas se usan cuando aportan valor:

- **Subagentes**: usar libremente para investigaciones independientes, paralelización (dispatching-parallel-agents), auditorías cross-eje. El costo de un fix mal hecho > costo de una sesión cara.
- **Skills**: invocar todas las que apliquen (superpowers-brainstorming, systematic-debugging, writing-plans, verification-before-completion, TDD). Regla meta CLAUDE.md global ("si dudás, invocala igual") se mantiene.
- **Brainstorming + design docs** antes de adopciones metodológicas: paso ineludible. Toma 30 min y muchos tokens pero evita refactors 10× peores después.
- **Auditoría integral** cuando se solicita: 5-7 agentes en paralelo cubriendo misión + código + docs + git + ground truth. No recortar a 2 por economía.
- **Verificación pixel-level + audit independiente** antes de "listo": obligatorios en adopciones (regla S33). NO saltarlos.
- **Persistencia in-vivo**: documentar hallazgos INMEDIATAMENTE en docs cuando aparecen.

**Costos que SÍ vale evitar** (no comprometen calidad):
- Re-leer archivo ya leído en la sesión sin cambio.
- Loops de polling con `sleep` cuando se puede usar `run_in_background` + notificación.
- Tool outputs gigantes pegados al contexto (snapshots, listados): delegar a subagente con resumen o escribir a JSON.
- Decisiones obvias preguntadas innecesariamente al usuario.

Ver A26 en `CLAUDE.md` proyecto.

---

## 5. Quick start S71

```bash
# 1. Sync con main
cd C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70
git fetch origin --prune
git checkout main && git pull
git checkout -b s71-path-d-fix

# 2. Validar NRT cron post-#103 merge (pre-condición sección 1)
gh run list --workflow nrt.yml --limit 10

# 3. Arrancar T1 Fase 1 — papers
# Despachar subagente Explore con scope:
# "Leer Coppola 2016a §SP 426.5 + Campus 2024 + Coppola 2024 cap Springer + Aveni 2024 RSE
#  buscando dNTI contextual + cirrus / t_bg cold / gate atmosférico.
#  Reporte <800 tokens con verdict: hay método explícito SÍ/NO + cita textual."
# Si SÍ → implementar literal. Si NO → fase 2 A/B con 3 alternativas (gate atm, co-validación, cap).
```
