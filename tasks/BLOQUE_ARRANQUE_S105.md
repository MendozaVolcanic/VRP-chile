# BLOQUE ARRANQUE S105

**Sesión S104 (2026-06-09)** — investigación de causa raíz del sesgo espacial de las
detecciones VIIRS en volcanes nevados (pedido Nicolás, A62). MUY larga y muy productiva.
8 PRs (#375-379 + probes). Registro: `project_s104_estado` (memoria). Doc central:
`docs/AUDIT_S104_VIIRS_POSITION_OFFSET.md`. Diseño: `docs/superpowers/specs/2026-06-09-test1-nti-covalidation-design.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat ../../[ruta]/memory/project_s104_estado.md
cat docs/superpowers/specs/2026-06-09-test1-nti-covalidation-design.md  # §V2.2 + V2.5
```

## ✅ Cerrado en S104
- **Diagnóstico de causa raíz (CONFIRMADO con ground truth)**: las detecciones VIIRS de
  los nevados (Tupun/Villarrica/Llaima) se sesgan al N por el **gradiente topográfico**
  (cumbre nevada fría vs valle tibio). El Test1 integra **MIR absoluto** → lo capta.
  MIROVA es inmune porque detecta por **NTI** (MIR−TIR cancela topografía). Lastarria NO
  entra (offset N = fumarólico Lazufre real, dato de Nicolás).
- **2 probes ground truth (Actions)**: lava FUERTE (0.55 MW) = NTI 17.4σ en cráter; lava
  DÉBIL (0.11 MW) = NTI 1.8σ en cráter, sin firma per-píxel; topografía = NTI plano.
- **Fix V1 (co-validación per-píxel) REFUTADO por A/B** (run 27186289487): apaga el Test1
  (le pide firma per-píxel que la señal difusa no tiene). Flag OFF, NO adoptado.
- **Núcleo V2 IMPLEMENTADO (PR #379)**: `compute_test1_nti` integra exceso de NTI. TDD
  verde, 687 suite. NO se invoca en el pipeline aún.

## §1 — PRIORIDAD S105: completar el rediseño V2 (Test1-NTI) — A45
1. **Resolver el VRP** (V2.5 del spec): `compute_test1_nti` debe devolver `L_bg_mir`
   (mediana MIR del anillo) + `mask_contributing` para que el caller compute el VRP
   Wooster sobre los píxeles NTI-elegidos. TDD primero.
2. **Caller** (process_viirs.py:818): rama `enable_test1_nti_integral` que llame
   `compute_test1_nti(bt_mir=bt, bt_tir=bt5, ...)` en vez de `compute_test1_mir`.
   ⚠️ A49: NO comerse el return ni el flujo downstream (test1_hot, centroid, L_bg).
3. **A/B 3 brazos** (MIR actual / NTI-integral / off), perfiles aislados, 5 vols
   (3 nevados + Lascar/Lastarria control). Criterios V2.4: 0 FN noches ALERTA + offset
   N→0 + %<3km sube + controles sin cambio + ground truth muestra. ⚠️ k_sigma a CALIBRAR
   (SNR bajo lava débil 1.8σ — quizá varios brazos de k_sigma).
4. A45 completo: tag `pre-s105-test1-nti-integral` + OK Nicolás + reproc + R2/R3/R8.

## §2 — Limpieza (cuando se implemente el caller V2)
- V1 (co-validación per-píxel) quedó en main con flag OFF (`enable_test1_nti_covalidation`,
  `nti_hot_mask` en compute_test1_mir, perfiles `_test1_nti_covalidation_*`). Al
  implementar V2, decidir si quitar V1 (deuda de enfoque refutado) o dejarlo.
- Archivar workflows one-off: `probe-s104-roi.yml`, `probe-s104-nti.yml`,
  `reproc-s104-test1-nti-ab.yml` (A38).

## §3 — Frentes de la AUDITORÍA SISTÉMICA S104 (doc: AUDIT_S104_SYSTEMIC_DIVERGENCE.md)
Auditoría profunda multi-volcán/sensor (4 subagentes). **TODOS son fix de ALGORITMO, no
display (A72: lo que es artefacto se ataca en la detección, no se oculta).** Orden por
impacto, atacar DESPUÉS de cerrar el A/B V2 (un cambio de detección a la vez):
1. **MODIS difuso** (el "resto" universal, artefacto ~0% real): el path-D contextual de
   MODIS dispara sobre escena tibia + suma scene-wide infla magnitud. ~280 recs/volcán a
   16-24km. El cap D9 solo atrapa 23% (cirrus t_bg<270); 77% escena tibia escapa. Fix
   RAÍZ: co-validación VIIRS375 cercano / compacidad espacial / t_max absoluto, para NO
   generar el campo difuso. Distinguir del foco MODIS legítimo (Lascar). MODIS solo en
   Actions (pyhdf). Brainstorming + A45.
2. **NdC sub-detección** (recall VIIRS375 = 0, único FN sistémico): faint sub-pixel. Lever:
   detección diurna MODIS (S90, flag OFF) o bajar umbral. A45. FN = lo más grave.
3. **Cirrus path-D (D9/A23)**: discriminante mejor que t_bg (contaminado por altitud A68).
4. **VIIRS750 disperso/redundante** (más disperso que V375 en los 11, no aporta recall):
   replicar Test1-NTI a process_viirs_mod.py / mejorar localización. NO solo ocultar.
- **Correcciones de la auditoría**: (a) MIROVA SÍ publica VIIRS750 (loader sano S93/A48);
  (b) PCC: lo confirmado es el cráter Puyehue, NO el lacolito; (c) RUTINA = registro del
  scraper Mirova-v1 (cobertura), no juicio de MIROVA — las miles de RUTINA prueban
  cobertura sólida → la comparación vs ALERTA es válida.

## §4 — Pendientes arrastrados
- **🔐 Credenciales Earthdata LOCALES inválidas** (cuenta se bloqueó 10min por reintentos
  S104): el .netrc local necesita actualización (Nicolás; conecta con pendiente S94 rotar
  token). Las de GH Actions OK. NO tocar credenciales yo (A71).
- Display PCC original (lacolito naranja + dedup mapa): re-evaluar bajo A72 — el lacolito
  es señal real (display ok para distinguir), pero el "resto" de PCC es MODIS difuso +
  cirrus (artefacto → frente §3, algoritmo). NO es un simple fix de display.

## Reglas nuevas S104 (persistir en CLAUDE.md — revise-claude-md pendiente)
- **A69** — gradiente topográfico nocturno contamina paths MIR-absolutos; MIROVA inmune
  por NTI. Al auditar/diseñar: ¿el path usa MIR absoluto o NTI?
- **A70** — auditar offset DIRECCIONAL (Δlat,Δlon + rumbos), no solo |distancia| (refuerzo
  A61). Y usar MEDIANA, no media (outliers). La media de offset me engañó en S104.
- **A71** — probes de red con reintentos pueden bloquear Earthdata; verificar credenciales
  antes; correr en Actions si las locales son dudosas.
- **A72** — fix de ALGORITMO sobre display: lo que es artefacto (MIROVA no lo entrega, lo
  generamos nosotros) se ataca en la detección/pipeline, NO se oculta en el frontend. El
  display solo es legítimo para señal cat-b REAL (no borrar del pipeline). Ya en CLAUDE.md.

## Prompt copy-paste S105
```
Sesión S105 — VRP Chile. Sincronizá (raíz en main) y leé tasks/BLOQUE_ARRANQUE_S105.md
+ project_s104_estado + docs/AUDIT_S104_VIIRS_POSITION_OFFSET.md.
S104 diagnosticó el sesgo topográfico de los nevados (Test1 integra MIR absoluto, MIROVA
usa NTI). Fix V1 (co-validación per-píxel) refutado por A/B. Núcleo V2 (compute_test1_nti,
integra NTI) implementado+TDD (#379), no invocado aún.
PRIORIDAD §1: completar V2 — resolver el VRP (V2.5 spec) + caller process_viirs.py + A/B
3 brazos + A45. Recordá A45 (tag+OK+TDD), A49 (no comerse el return), explicá como geólogo.
```
