# VRP Chile

Sistema VRP independiente para volcanes chilenos (equivalente MIROVA, propio).
Repo: https://github.com/MendozaVolcanic/VRP-chile

> **Versión operativa corta (S173, 2026-11-05).** La historia completa de cada regla (todas las marcas
> «⚠️ rebajada / refutada / obsoleta» con su evidencia y el texto original que A113 manda conservar) está en
> [`docs/CLAUDE_HISTORIA.md`](docs/CLAUDE_HISTORIA.md)
> (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\CLAUDE_HISTORIA.md`), copia íntegra
> del CLAUDE.md al commit `80aafc49e`. **Consúltala antes de reabrir un frente cerrado o de citar un número.**
> Cada regla de abajo dice lo que hoy es verdad y termina con su puntero «(historia: Ann)», que remite a ese archivo. Una rebaja nueva
> se escribe acá (estado vigente) y, si conserva texto viejo, en la historia (A113).

> ⚖️ **SDA en producción (Resolución CPLT N°372).** Al crear o editar código de detección o clasificación,
> aplicar la cabecera FICHA y el comentario «POR QUÉ» por bloque, y mantener
> [`docs/FICHA_SDA_VRP_CHILE.md`](docs/FICHA_SDA_VRP_CHILE.md) al día. Estándar:
> [`../../GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md`](../../GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md).

## Worktree canónico y primer comando (LEER PRIMERO)

Canónico: la raíz `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/`, en `main`. Los worktrees
`VRP-Chile-s70/`, `-s80-consolidation/`, `-s79-f66/` no son canónicos (A52).

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
ls tasks/BLOQUE_ARRANQUE_S*.md | sort -V | tail -1   # último bloque de arranque
ls docs/AUDIT_S*.md | sort -V | tail -1              # última auditoría integral
cat docs/MIROVA_DIVERGENCES.md                       # catálogo vivo
```

⚠️ S157: en `main` el último bloque de arranque es S150; desde S151 viven en `loop/activo`
(`git ls-tree --name-only origin/loop/activo tasks/`).

## Misión vinculante (LEER ANTES DE TOCAR PIPELINE)

> ⚠️ **S172 (A113): MODIS de producción ya no es K.** Desde el merge del PR B (#934) MODIS corre la vía «código
> MIROVA» (`enable_modis_codigo_mirova: true`, `pipeline/mirova_v750_codigo.py`); VIIRS 375 y 750 siguen con K.
> Decisión de Nicolás del 2026-10-31. K de MODIS queda de guardia (`pipeline/profiles/guardia_k_modis.yaml`,
> `scripts/vigilancia_guardia_modis.py`), reversión pre-autorizada por `git revert` del PR B. Lo que describa el
> MODIS de producción como K (D21, D12, cara MODIS de D11) es previo a S172. Ver `docs/MISSION.md`, ficha v1.18.
>
> ⚠️ **S177 B1 (A113; PROPUESTA: rige sólo desde el merge del PR B1): VIIRS 375 de producción deja de ser K.** Corre la
> vía «código MIROVA» (`enable_v375_codigo_mirova: true`); K de VIIRS queda de guardia
> (`pipeline/profiles/guardia_k_viirs.yaml`), reversión por `git revert -m 1` del merge de B1 (regla
> `experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md`). Lo que abajo diga «VIIRS 375 y 750 = K» o que
> el tablero publica `f5_core_vrp_mw` en VIIRS 375 vale para VIIRS 375 sólo hasta ese merge. Ver `docs/MISSION.md`,
> ficha v1.23.

**Objetivo: clon literal MIROVA NRT.** Antes de tocar `pipeline/`, leer [docs/MISSION.md](docs/MISSION.md) y
aplicar las 3 preguntas; si las 3 dan NO, no implementar y anotarlo en `tasks/backlog_*.md`. Parches viejos
(`MAX_SIGMA_COMPONENT_K=7K`, vent-path, `exclude_zones`, Reglas D, cloud mask, pisos VRP) no vuelven sin ese paso.

## Documentación bibliográfica (leer ANTES de buscar online)

PDFs y síntesis en `documentacion/` (no en el Vault). Source of truth: `documentacion/BIBLIOGRAPHY_SYNTHESIS.md`
(⚠️ S158 R2: su fila de VIIRS 750, Di Bella 2024, no es MIROVA). Claves: `sp426.5.pdf`/`sp426_5.txt` (Coppola
2016a), `THESIS_MASSIMETTI.pdf`, `coppola2024_chapter.txt`, `campus2024_extracted.txt`. Workflow S36: buscar
local (`find documentacion/ -iname "*<topic>*"`), síntesis, PDF, y sólo entonces online. El Vault
(`C:\Users\nmend\OneDrive\Escritorio\claude\Vault\`) tiene notas, no PDFs (A35).

## Reglas científicas (no negociables)

- **VRP MIR (Wooster)**, validados S14 contra MIROVA v2.5 OSF (error ≤0.17 %, 48.360 filas): MODIS
  `WOOSTER_COEFF=18.9`, VIIRS 750 M13 `19.7`, VIIRS 375 I4 `18.0`; A_pix nadir fijo en los 3. NO usar Di Bella
  2024 k=2,48×10⁷ para VIIRS 375.
- **VRP TIR (I05)**: Stefan-Boltzmann puro (Ec. 5 de Aveni 2024). El cierre de D3 está rebajado (S146): la
  Ec. 16 de Springer es el modelo de dos componentes y el «no adoptada» de la Ec. 9 es SOSPECHA.
- **Código operacional de MIROVA VIIRS 750** (OSF zm62w, 2026-07-24, D34,
  `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`): difiere de producción en 10 de 13 puntos (K1 -0,7, dNTI mínimo
  0,02 fuera de la cumbre, media 3 × 3 con el central, fondo interpolado bajo halo).
- **Detector de producción**: MODIS = vía «código MIROVA» (S172). VIIRS 375 y 750 = **K** (S153, #850,
  `34cea39e`): sin Test 1 integrado (`enable_test1_path: false`, D30), conectiva `max` en Tests 2 y 3 (piso C1
  **y** `μ+C2·σ`), banda 22 primaria en MODIS (D21; la guardia K y también la vía). Regla
  `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` (#848), evidencia `experiments/_s153_fk_v2/README.md`. El
  histórico de los 11 Tier A desde 2025-02-15 está reprocesado con K (#883). `experimental` sigue con el detector
  anterior (A117). Tag `pre-s153-adopcion-k`; el `git revert` ya no es limpio (S157).
- **Detector anterior** (N·σ 5/10 noche y 15 día, C1 0,003/0,010 y 0,02 día, rama `min`, banda 21): fiel al
  paper, no al código de MIROVA (S160). El test de BT con N·σ no está en la Tabla 1 y está apagado desde S40
  (D31). El Test 1 integrado era detector propio (su cita «Coppola 2015» es Heap et al.).
- **Divergencias de S128 a S138**: D21 (banda primaria; S174: en MODIS de producción la vía usa siempre la banda 22 primaria y la 21 donde la 22
  satura, `pipeline/mirova_v750_codigo.py::leer_radiancia_modis`; la guardia K también, `enable_modis_b22_primary: true`),
  D22 (compuerta `bt > t_bg + 3 K`, encendida según S157), GAP #A (reabierto S128, guard
  `tests/test_guard_gap_a_pool_musigma_s128.py`; S174: `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` sigue en `False` en los
  tres procesadores; MODIS de producción no pasa por ese código cuando corre la vía; efecto en VIIRS bajo K SIN MEDIR). «No quedan gaps de fidelidad
  literal» es FALSO (S137).
- **Kernel dNTI**: `np.mean` de 8 vecinos (D1, S17); en VIIRS 750 MIROVA usa 3 × 3 con el central (S158 R2).
- MIR sólo nocturno. Bandas: MODIS 21/22 + 31; VIIRS I04/I05; M13/M15. Constantes exactas del paper y cita en
  todo cambio metodológico. Si dudas de un método, dilo; nunca adivines. (historia: Reglas científicas)

## Reglas geométricas S14 (MIROVA-equivalent)

- `radius_km = 25 km` en los 11 Tier A (grilla MIROVA UTM 51×51 km); los 34 restantes en 5 km
  (`volcanoes.yaml`: `{25: 11, 5: 34}`, S131).
- `inner_radius_km` por volcán (KML MIROVA):

  | Volcán | inner | Volcán | inner |
  |---|---|---|---|
  | Lastarria | 3 | Lascar, Isluga, NdC, Llaima, Villarrica, Chaiten | 5 |
  | Planchón-Peteroa | 3 | Tupungatito | 7 |
  | Copahue | 4 | PuyehueCordonCaulle | **20** |

- Esquema dual «detectar amplio + clasificar visual»: dentro de `inner_radius_km` → `distance_class="summit"`;
  fuera → `"far"`. No se filtran, se clasifican.
- Campo unificado `final_hotspot_lat/lon/dist_km` (fallback eruption→vent). Dashboard y auditorías usan sólo
  este campo.

## Reglas operacionales A1 a A119 (estado vigente)

Nota S157/S160: las reglas que explican un resultado por el Test 1 integrado (A12, A19, A66, A67, A69, A100,
A114) se escribieron con ese camino encendido; desde #850 no corre (D30) y desde #883 todo el histórico es K.
La lección de método de cada una se conserva; el mecanismo ya no actúa en producción. detalle:
docs/CLAUDE_HISTORIA.md, inicio de «Reglas operacionales S14».

- **A1.** Calibración empírica > derivación teórica: con data pública del mismo grupo (OSF, Zenodo), calcular el coeficiente antes de creerle al paper. (historia: A1)
- **A2.** Agotar diagnósticos sobre data en disco antes de reprocesos caros. (historia: A2)
- **A3.** Todo campo de distancia documenta desde qué punto mide; usar `final_hotspot_dist_km`. (historia: A3)
- **A4.** Un solo juego de umbrales por sensor; la variación por volcán es geometría. ⚠️ S158 R2: en VIIRS 750 MIROVA sí admite píxeles excluidos y ROI desplazables; si excluye algo en Chile es SIN DATO. (historia: A4)
- **A5.** Valores MIROVA oficiales (KML, OSF) son datos: usarlos tal cual; divergir sólo con experimentos en `experimental`. (historia: A5)
- **A6.** Trazar callers al concluir comportamiento. El ejemplo drifteó (S127): la función hoy es `get_detection_anchor()` (`get_effective_vent` es alias sin llamador, D17); la lección vale entera. (historia: A6)
- **A7.** El ejemplo es OBSOLETO (S125; hoy `diag_sigma_bg_k`, `diag_eff_threshold_k`, `diag_nti_std`). Lección: «no calculado» ≠ «calculado pero no persistido». (historia: A7)
- **A8.** Verificar data fresca (reprocesar un día con código actual) antes de asumir el problema de un handoff. (historia: A8)
- **A9.** MIROVA = Torino + Firenze + Sapienza (Coppola, Laiolo, Massimetti, Campus, Aveni, Cigolini). NO MIROVA: INGV Catania (Di Bella, Del Negro...) ni CNR-IMAA Potenza (NHI). Lista: `~memory/reference_papers_mirova_canonical.md`. (historia: A9)
- **A10.** Rebajada en su premisa (S147, D32): `pc.vrp_mw` NO es «lo que MIROVA reporta» (MIROVA suma todos los píxeles alertados). Sigue en pie: `record.vrp_mw` no es el campo correcto; el dashboard publica `f5_core_vrp_mw` en VIIRS 375 (S132) y `pc.vrp_mw` en MODIS y VIIRS 750 (cita vigilada por el guard G8). (historia: A10)
- **A11.** Universo MIROVA = CONS + OCR; OCR es complemento; `FALSO_POSITIVO_OCR` es etiqueta del scraper, no de MIROVA. (historia: A11)
- **A12.** El ejemplo es FALSO (S128/S131): ΔT reales Láscar 16,9 K, Isluga 8,3 K. ⚠️ S158 R2: «Coppola 2024 L1129» no respalda el kernel-bg. Lección vigente: el patrón térmico decide, validar por A/B (A19). (historia: A12)
- **A13.** FALSA (S124): Villarrica no tiene distancia fija 0,84; el campo está cuantizado a la celda de grilla (D15). (historia: A13)
- **A14.** Buscar todas las variantes de nombre del CSV (`PlanchonPeteroa`, `Puyehue-Cordon Caulle`, `Nevados de Chillan`). (historia: A14)
- **A15.** `timeout >= duración_esperada × 1.3`. (historia: A15)
- **A16.** Pre-escribir scripts de audit mientras corren workflows. (historia: A16)
- **A17.** OBSOLETA desde S77: `sync-mirova-csv.yml` automatiza el CSV. Ojo (S125): `data/mirova_reference/registro_vrp_ocr.csv` está congelado; el vivo es `.../mirova_v1_snapshot/registro_vrp_ocr.csv`. (historia: A17)
- **A18.** Un preview offline no predice la selección de cúmulo: validar con reproc real. (historia: A18)
- **A19.** El patrón térmico no es universal (Tupungatito, anillo glaciar, empeora con kernel-bg): decidir por volcán con A/B. (historia: A19)
- **A20.** R2 con centroide no aplica a anomalías difusas (PCC); validar por magnitud agregada + geometría (D7). (historia: A20)
- **A21.** Las bandas de los gates R2 dependen del régimen (`docs/R2_GATES_BY_REGIME.md`). (historia: A21)
- **A22.** PP es bimodal en selección de cúmulo: multi-caso (3 a 5 ALERTAs) y reportar la moda. (historia: A22)
- **A23.** D9 reabierta en parte (S146): sigue viva sólo la co-validación del path D sobre fondo frío; gate por `t_bg` descartado; el tope de 5 MW recorta sin medir que lo recortado sea artefacto, el código MIROVA V750 no lo tiene (S158) y bajo K casi no actúa (S160). (historia: A23)
- **A24.** El TIF de MIROVA no es VRP por píxel sumable (D6). (historia: A24)
- **A25.** `git fetch origin --prune` al inicio; `git log main` local no refleja `origin/main`. (historia: A25)
- **A26.** Calidad sobre tokens (Nicolás S70-2): subagentes, skills y verificación sin recortar; evitar re-lecturas, polling y salidas gigantes. (historia: A26)
- **A35.** Valores numéricos de notas Vault `ai_generated` se cotejan contra el PDF (UserGuide > Coppola 2025 > papers históricos > Vault). (historia: A35)
- **A36.** OBSOLETA desde S102/S103: el pipeline ya no aplica sec³ (nadir fijo); seguirla mete un factor espurio. (historia: A36)
- **A37.** MODIS marca saturación con `SI=65533`, VIIRS con el bit 2 del quality flag: leer el UserGuide de cada sensor. (historia: A37)
- **A38.** Antes de borrados masivos (>10 archivos o >50 MB): inventario, tag `pre-<scope>-cleanup` + push, confirmación. (historia: A38)
- **A39.** Claude mergea PRs con `mergeStateStatus=CLEAN`, checks verdes y 0 regresiones (alta criticidad: confirmar); fallback `gh api --method PUT .../pulls/<N>/merge`. Enmienda S142: «0 checks» recién abierto es SIN DATO (`gh pr checks <N> --watch`); tras editar un documento, `grep -rl <archivo> tests/` y suite completa. (historia: A39)
- **A40.** Búsqueda bibliográfica dirigida: manual `investigacion` (OpenAlex) > orquestadores con WebSearch. (historia: A40)
- **A41.** `Claude_in_Chrome` sirve para Perplexity Pro navegando a `perplexity.ai/search/new?q=<...>&sources=scholar`. (historia: A41)
- **A42.** OBSOLETA desde S74: la causa del HTTP 422 era el «Norway Problem» (A43): quotear `"on":`. (historia: A42)
- **A44.** Un worktree dedicado por subagente paralelo que toque git. (historia: A44)
- **A45.** Tag defensivo + push y confirmación explícita de Nicolás antes de tocar `pipeline/process_*.py`, `store.py` o `mirova_equivalent.yaml`. (historia: A45)
- **A46.** Dos representaciones del punto caliente (`hotspot_*` vs `primary_cluster.*`) son vector de bugs: auditar los gates downstream (F47 H4). (historia: A46)
- **A47.** Reproc local nunca paralelo sobre el mismo `data_subdir`; JSON corrupto: `git checkout origin/main -- <archivo>`. (historia: A47)
- **A48.** Validar la convención antes de aceptar heurísticas de un subagente (`VIIRS_SNPP/NOAA20/NOAA21` = 375 m; `VIIRS_*_750` = M-band). (historia: A48)
- **A49.** Al insertar código entre dos estructuras, revisar con `git diff` que el `return` anterior sigue intacto. (historia: A49)
- **A50.** Antes de llamar «pre-existente» a una falla, comparar con `git show origin/main:<archivo>`. (historia: A50)
- **A51.** Auditoría completa cada 20 sesiones (`docs/AUDIT_S<N>.md`); con >3 contradicciones, consolidar antes de features. (historia: A51)
- **A52.** Worktrees no-main pueden estar atrasados: `git fetch origin --prune && git log --oneline HEAD..origin/main`. (historia: A52)
- **A53.** Cap de 12 PRs por sesión (soft) y 20 (hard); persistencia in-vivo de todo hallazgo. (historia: A53)
- **A54.** El gap de precisión vs MIROVA es mayormente metodológico (S86: 95,4 % de los «FP» son anomalías reales): clasificar la categoría (a/b/c/d) antes de un «fix de precisión». Matizada por A69 en nevados. (historia: A54)
- **A55.** Un gate «intra-radio por path» exige verificar que el frontend no lo hace ya y qué categoría física filtra. (historia: A55)
- **A56-A60.** Reglas preventivas NRT (S82) en `docs/META_RULES_S80.md`. (historia: A56-A60)
- **A61.** Auditar detección incluye el eje espacial: lat/lon contra el cráter y el TIF de MIROVA, no sólo distancias. (historia: A61)
- **A62.** La insistencia del experto es señal: asumir error y refutarlo con datos (Chrome MCP, `../mirova-tif-archive`). (historia: A62)
- **A63.** Consolidar config no debe revertir fixes deliberados: revisar `git log -S` y dejar un test de regresión. (historia: A63)
- **A64.** Blindar la red NASA en auth y descarga: circuit-breaker por host (#364); ConnectTimeout no se reintenta, ReadTimeout sí. (historia: A64)
- **A65.** Hangs de CI: instrumentar con markers `print(..., flush=True)` por etapa antes de adivinar el fix. (historia: A65)
- **A66.** Nadir fijo adoptado en MODIS (#354), pero no es «clon literal» (S138): el paper remuestrea a 1 km (`ENABLE_UTM_REGRID = False`, D17 abierta). Lección vigente: A/B de 3 brazos con criterio pre-registrado. (historia: A66)
- **A67.** Nadir fijo VIIRS adoptado (#368, #373), misma salvedad D17. Cambiar área o escala cambia también la detección: verificar FN por record. (historia: A67)
- **A68.** Ante «sobre-detección», separar display de over-detección real; el proxy `t_bg<270K` está contaminado por altitud. (historia: A68)
- **A69.** Los paths de MIR absoluto son vulnerables al gradiente topográfico de los nevados; el NTI lo atenúa pero no lo cancela (S128), el ETI sí. El Test 1 integrado que culpaba está apagado desde #850; parte del mecanismo puede seguir por D22 (SOSPECHA). `compute_test1_nti` está flag-OFF (S125). Pregunta siempre: ¿MIR absoluto o NTI? (historia: A69)
- **A70.** Auditar el offset direccional con mediana (Δlat, Δlon, rumbos), por sensor y por path. (historia: A70)
- **A71.** Probes con reintentos pueden bloquear la cuenta Earthdata; nunca manipular credenciales de Nicolás. (historia: A71)
- **A72.** Fix de algoritmo sobre fix de display: artefacto → no generarlo; señal real sub-umbral (cat-b) → display legítimo. (historia: A72)
- **A73.** Gatear decisiones binarias sobre el first-pass dentro del inner, no sobre agregados contaminados. (historia: A73)
- **A74.** Verificar el índice absoluto antes de concluir «normalización rota». (historia: A74)
- **A75.** Probe de atribución por etapa con monkeypatch read-only. (historia: A75)
- **A76.** MIROVA publica artefactos solares diurnos en su producto por volcán: OCR VIIRS 375 alto en pasada diurna cerca del mediodía es sospechoso. La cita «Coppola 2023 §2.5, ~5 %» está CORRUPTA (S146). ⚠️ S158: VIIRS 750 sí tiene gate automático (sun-glint bajo 12°). (historia: A76)
- **A77.** «Erupciona pero VRP no lo ve»: revisar MIROVA OLI/MSI (SWIR alta resolución, NHI); el foco puede ser sub-píxel. (historia: A77)
- **A78.** Explosiva ≠ efusiva: escanear `nti_max` multi-sensor antes de concluir FN. (historia: A78)
- **A79.** Al adoptar un parámetro, verificar el evento específico que lo motivó, no sólo la métrica agregada. (historia: A79)
- **A80.** `nti_max` plano (~-0,9) sirve de sanity check, pero NO discrimina real de artefacto (S116, AUC 0,251). (historia: A80)
- **A81.** El bug A46 es bidireccional: medir ambas caras contra MIROVA y preferir el fix unidireccional. El 2.527 es del corpus de junio (A90); el «NO destapar» NdC hereda la rebaja de A82. (historia: A81)
- **A82.** El «irreducible / agotado» NO vale: rebajado en S124 (eje geométrico, D17), S138 (sólo bajo banda 21 y D22), S146 (sin tasa base), S151 (banda 22 en Láscar) y S157 (K en MODIS fuera de Láscar); MODIS cambió de vía en S172. Qué hacer con D11 lo decide Nicolás. (historia: A82)
- **A83.** Rebajada (S146): el AUC 0,859 no tiene script y su etiqueta es «MIROVA publicó» (re-medido 0,762; 0,554 dentro de volcán y sensor). No apaga la búsqueda de un discriminante real vs artefacto. (historia: A83)
- **A84.** Lo medido sigue (ctx_cluster de Llaima y Lastarria indistinguibles; A/B de S106 descartado); el «irreducible» heredado de A82 no. (historia: A84)
- **A85.** Lección vigente: medir el daño antes de agregar una cerca geométrica. El «0 robos en 214» está observado (B-03); bajo la regla de la anomalía mayor (Nicolás, 2026-10-09) un cúmulo lejano más fuerte no es robo. La nota S153 (MODIS ene-jun 2026 escrito con los gates intra-radio) quedó OBSOLETA con #883: los 4.286 records MODIS de ene-jun 2026 de los 11 Tier A tienen `processed_utc` de 2026-10 (main `f36a8fb98`, S174). (historia: A85)
- **A86.** Anclar «hoy» a la hora del servidor (`gh api -i <repo>` → header `Date`). (historia: A86)
- **A87.** El ejemplo quedó SIN VERIFICAR (S146), no usarlo como evidencia (D31). Lección vigente: un flag que se apaga no prueba que el problema se fue; verificar el mecanismo en los records. (historia: A87)
- **A88.** Data que pasa a alimentar el frontend deja de ser descartable en el mismo PR. (historia: A88)
- **A89.** «No aparece» casi nunca significa que no esté: trazar cómo lo lee el código; flags desde `pipeline.profile`, nunca del YAML. (historia: A89)
- **A90.** Un conteo absoluto sobre un corpus vivo no se compara entre sesiones: registrar proporción y ventana (el corpus crece también hacia atrás). (historia: A90)
- **A92.** Un guard por subcadena da falso verde: exigir frontera de palabra y barrer con `experiments/_s133/auditar_guards_por_subcadena.py`. (historia: A92)
- **A93.** Un radio no es una posición; «verdes» no es una ventana; un pareo no es el conjunto que dice contar. (historia: A93)
- **A94.** Un caso de referencia justifica investigar, no priorizar; medir en la unidad del operador (la noche). (historia: A94)
- **A95.** Un cierre hereda las premisas de su lectura: comprobarla en el PDF renderizado a imagen (`get_pixmap(dpi=200)`), no en la capa de texto. (historia: A95)
- **A96.** Nunca `git stash pop` sin mirar `git stash list`; `git cherry` da falsos «sin integrar» con squash: verificar por contenido. (historia: A96)
- **A97.** Atribuir un mecanismo simulando la etapa siguiente con el predicado literal del dashboard. (historia: A97)
- **A98.** La brecha de paridad es sobre-publicación, no recall (874 de 877 noches); toda métrica lleva negativos limpios. (historia: A98)
- **A99.** Rebajada (S146): el 0,995 es producto de dos factores opuestos y compensa entre volcanes (0,66 a 1,39); ya no apaga la búsqueda en k, área, banda o Planck. (historia: A99)
- **A100.** Con K el `keep_peak` del Test 1 no actúa (0 records con fuente `test1`/`test1_roi` desde #883); el «nunca apagarlo solo» valía para el detector anterior. El keep-peak focal (`FOCAL_CLUSTER_KEEP_PEAK`) es otro mecanismo y hoy no actúa en producción (S174, main `f36a8fb98`): en VIIRS 750 y en la segunda llamada de MODIS sólo corre con fuente `test1` (0 de 73.620 records de los 11 Tier A); la primera de MODIS (`pipeline/process_modis.py:1356`) es del camino K, que la vía salta (74 de 74 records MODIS desde el 2026-11-02 18 UTC con `via_codigo_mirova: true`). Sigue vivo en la guardia K y en los records que caen a K (`sin_grilla`, `sin_mxd03`). (historia: A100)
- **A101.** Las citas `file:line` se remapean por contenido (`scripts/remapear_citas.py`), salvo las históricas deliberadas (A6, A49). (historia: A101)
- **A102.** Al corregir una función, buscar también las copias en línea de su lógica. (historia: A102)
- **A103.** La pérdida de vecinos tibios está en la detección, no en el ensamblado (dETI 52 de 52; BT 18 de 18). (historia: A103)
- **A104.** Una métrica con ventana que cruza #535 (2026-08-28 23:00 UTC) mezcla dos regímenes: medir por tramo. (historia: A104)
- **A105.** El OSF v2.5 NO está supervisado a mano (Coppola et al. 2026, Sci. Data p. 7): sus conteos no valen para el NRT. (historia: A105)
- **A106.** Corregida (S144): GeoTIFF VIIRS 375 de MIROVA en UTM nativo sólo del 2026-09-14 06:36 al 2026-09-15 06:24, después EPSG:4326; leer la hora de adquisición y desconfiar de md5 repetidos. (historia: A106)
- **A107.** Una cota de distancia escalar sirve para descartar, no para identificar el objeto. (historia: A107)
- **A108.** Un run 100 % verde no prueba cobertura pareja: contar pasadas por brazo (`bajar_tramos.py --estricto`). (historia: A108)
- **A109.** Medir contra un producto del mismo gránulo infla por selección: usar otra pasada de la misma noche (45 a 120 min). (historia: A109)
- **A110.** Un control se valida midiendo su nulo sobre datos sin nada que detectar; preferir controles que se cancelan por construcción. (historia: A110)
- **A111.** Un cierre sin respaldo citable es una creencia: correr el script, pedir numerador, denominador y ventana; sin respaldo ≠ refutado. (historia: A111)
- **A112.** Una línea base se corre sobre un árbol quieto; si hubo edición durante la corrida, se descarta. (historia: A112)
- **A113.** Una rebaja se propaga a los hijos en el mismo PR (`grep` de número, frase e ID), con marca al inicio y el texto viejo conservado. (historia: A113)
- **A114.** Una palanca que satura la métrica esconde las demás: estratificar antes de medir. (historia: A114)
- **A115.** Un umbral se le pregunta a la referencia: `mirova_equivalent` contra MIROVA; `experimental` contra OVDAS y SWIR. (historia: A115)
- **A116.** Medir cuántos casos mueve un cambio antes de llamarlo arreglo, y que el instrumento puede dar ≠ 0 antes de creerle a un cero. (historia: A116)
- **A117.** Un perfil derivado se vigila por dirección (`tests/test_guard_laboratorio_no_mas_ciego_s147.py`). ⚠️ S157: el laboratorio NO es idéntico al operacional: quedó con el detector anterior y en MODIS ve menos (6 de 39 protegidas contra 39 de 39); el guard sólo compara pisos. (historia: A117)
- **A118.** Un flag de umbral o geometría llega a todos sus consumidores (caja ROI1 al segundo pase, arreglado S149); un evaluador sólo ve los estratos que etiqueta. ⚠️ S160: la caja, medida en S151 sobre K, NO CUMPLE (veto). (historia: A118)
- **A119.** Antes de usar los CSV de MIROVA, mirar desde cuándo sirve cada canal (tabla sana desde marzo; OCR mal calibrado hasta 2026-06-11; VIIRS por pasada desde abril; enero no se usa; hitos en `scripts/calidad_referencia_mirova.py`). ⚠️ S151: el «86 % en enero» era Tupungatito en el denominador; «0 alertas MODIS dependen del OCR» es falso, son 5 hoy. (historia: A119)

## Explicar como geólogo, no como programador

1. Primero el fenómeno físico (qué pasa en el volcán, el píxel, la atmósfera, el fondo), en lenguaje natural.
2. Después el mecanismo del pipeline y si tiene sentido frente al fenómeno.
3. Al final, sólo los números y fórmulas necesarios.
4. El «por qué» antes del «cómo»; nombrar el trade-off FP vs FN y su costo.
5. Tablas y métricas agregadas sí; derivaciones largas viven en papers y comentarios de código.
6. Nunca adivinar un valor físico o instrumental: ir a mirarlo.

## Arquitectura

- `pipeline/`: fetch.py, process_modis.py, process_viirs.py, process_viirs_mod.py, store.py, scan_geometry.py.
- `frontend/`: `index.html`, `diario.html`, `mosaico.html` live, cada una con su copia de helpers
  (`mirovaEqVrp`): un cambio de display se replica en las 3 (S92). `comparacion.html` es PREVIEW sin
  `mirovaEqVrp` a propósito. Verificar en navegador real. GitHub Pages despliega en push a `frontend/**`.
- `volcanoes.yaml`: 45 volcanes; 11 Tier A con serie continua (sin hueco nov-ene tras #883); 34 fuera del cron.
- `nrt.yml`: cron 2 h, matrix por volcán, timeout 50 min. Reprocesos de historia en la máquina de Nicolás
  (`scripts/run_pipeline.py --profile X --volcano Y --start ... --end ...`), nunca full-history en Actions.
  `data/` JSON commiteado; L1B/HDF nunca.

## Skill triggers (OBLIGATORIO invocar antes de actuar)

| Situación | Skill / regla |
|---|---|
| Bug, FP/FN inesperado, anomalía, regresión | `superpowers-systematic-debugging` |
| Fix de >20 líneas en `pipeline/`, experimento nuevo | `writing-plans` (+ `test-driven-development`) |
| Paso atrás metodológico | `superpowers-brainstorming` |
| Ejecutar un plan escrito | `executing-plans` |
| Editar `pipeline/process_*.py` o `scan_geometry.py` | `test-driven-development` |
| Declarar listo, pushear a main, cerrar item | `verification-before-completion` |
| `enable_*: true` en `mirova_equivalent.yaml` | `superpowers-brainstorming` + R2 pixel-level (`docs/PROCESS_RULES_S33.md`) |
| A/B con «mejora» >30 % | debugging + R3 audit independiente (`experiments/76_audit_independent.py`) |
| Tocar `pipeline/audit_metrics.py` | R1 + R7: tests sintéticos antes (`tests/test_audit_metrics.py`) |
| 2+ investigaciones independientes | `dispatching-parallel-agents` |
| «automatiza X», «cada vez que Y» | `update-config` |
| DataFrames/HDF grandes; script >5 min | `pandas-pro`; `python-performance-optimization` |
| A/B con profile flag | template `.github/workflows/_archive/reproc-ab-p3-1.yml` + 2 perfiles con `data_subdir` aislado |
| Cerrar sesión con learnings | `revise-claude-md` + `anthropic-skills:consolidate-memory` + `docs/SESSION_CLOSE_CHECKLIST.md` |

Si dudas si una skill aplica, invócala. Todo hallazgo se persiste en el momento, no al cierre.

## Glosario obligatorio

MIROVA es la hoja de respuestas; cada noche-satélite de cada volcán es una pregunta.
- **TP**: ambos detectan. **FP**: sólo nosotros (lago tibio, nube fina, nieve). **FN**: sólo MIROVA, lo más
  grave. **TN**: ninguno.
- **Cluster vs pixel**: ⚠️ S158: MIROVA cuenta y suma **píxeles** alertados, no regiones; el «factor 42» de
  S23 es falso (`docs/AUDIT_S158.md`). (historia: Glosario)
- **Precision** = TP/(TP+FP). **Recall** = TP/(TP+FN), medido contra MIROVA en las dos direcciones (criterio de
  victoria, Nicolás 2026-10-13, `docs/MISSION.md`): ninguna alerta protegida (≥1 MW) se pierde; rige la lectura
  A (D-4, #782); alertas VIIRS 375 ≤0,05 MW cuentan como «MIROVA no vio nada» (D-9, #811). **F1**: media
  armónica. **Ratio ours/mirova**: mediana = sesgo.
- **Tier A/B/C**: ≥30 / 5 a 29 / <5 refs. **vent-path**: un píxel del cráter. **eruption-path**: clúster.
  **σ_bg**: desvío en el anillo. **Path A/B/C**: BT / NTI absoluto (>-0.8) / NTI relativo.

## Regla de publicación en dashboard

Todo cambio que modifique detecciones (perfil, umbral, reproceso, fix en `pipeline/`) se refleja en el
dashboard antes de declararse completo: correr, commitear el JSON en `data/mirova_equivalent/`, verificar que
GitHub Pages publicó. Si es sólo del perfil `experimental`, decirlo y no contaminar la vista operacional.

## Regla de delegación (control de contexto)

Lecturas de archivos >500 líneas o de varios archivos → subagente `Explore` con resumen <500 tokens. Salidas
de auditoría largas → leer el JSON del snapshot. Investigaciones paralelas → `dispatching-parallel-agents`.
Estado entre sesiones → memoria. No re-leer archivos sin cambios.

## Constraints técnicos

- `pyhdf` roto en Windows: MODIS sólo en Actions Linux. LANCE NRT ~3 h. NOAA-20: buscar v2 y v2.1.
- **Credenciales**: el NRT usa `EARTHDATA_TOKEN` (rotación cada 50 días; fecha vigente en `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md`). El par usuario/clave de los secretos
  está VENCIDO y bloquea la cuenta (A71): workflows nuevos sólo por token, copiando el `env` de `nrt.yml`.
- `fetch.py` intenta Standard y cae a `_NRT`; `store.py` auto-upgrade NRT→Standard.
- Encoding Windows: `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`.
- `volcanoes.yaml`: editar con `Edit` (`yaml.safe_dump` destruye comentarios).
- Actions: max-parallel=8, fail-fast=false, cron 2 h, timeout 50 min por paso.
- **Concurrency**: quien hace `git push` a main lleva `group: push-main` **o** su propio retry
  `pull --rebase` + `push`, no ambos; en `nrt.yml` el grupo va a nivel workflow. Contrato:
  `tests/test_guard_declarado_vs_efectivo_s131.py::test_g4_pusher_push_main_o_retry`.
- Geofencing por volcán (`max_hotspot_dist_km`). Refs del scraper son NRT: https://github.com/MendozaVolcanic/Mirova-v1
- Frontend: VIIRS 375 grafica `vrp_mw`, no `vrp_mir_mw` (S12).
- Matrix de fechas sobre el mismo JSON: `max-parallel: 1` o chunks + merge (S25).
- earthaccess: `g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]`.
- `workflow_dispatch` sólo con el yml en `main`. **Norway Problem (A43)**: quotear `"on":`; verificar con
  `python -c "import yaml; print(list(yaml.safe_load(open(<path>)).keys()))"`.

## Estado (puntero, NO duplicar estado acá)

1. `tasks/BLOQUE_ARRANQUE_S<N>.md` más reciente (`sort -V`; desde S151 en `loop/activo`).
2. `MEMORY.md` del proyecto (memoria del agente).
3. Última auditoría: `ls docs/AUDIT_S*.md | sort -V | tail -1` (no hardcodear el número).
4. `docs/MIROVA_DIVERGENCES.md`: catálogo vivo; el estado de cada D está en su encabezado. D9 salió de la lista
   de cerradas en S146 (A23); qué hacer con D11 y si D12 se cierra lo decide Nicolás (S157). (historia: Estado)
5. `docs/SESSION_INDEX_CONSOLIDATED_S80.md`: ancla histórica S1-S80.
6. `docs/SINTOMAS.md` (S157): antes de proponer una palanca, leer el síntoma.

Al cerrar sesión NO escribir estado acá: va al bloque de arranque y a la memoria.
