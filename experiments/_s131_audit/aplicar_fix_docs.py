# -*- coding: utf-8 -*-
"""S131 - Correcciones documentales del eje T9 (declarado vs efectivo).

POR QUE. La auditoria S131 (docs/s131/agentes/DECLARADO_VS_EFECTIVO.md) midio 16
afirmaciones FALSAS y 13 OBSOLETAS en los documentos vinculantes, cuatro de ellas en
la ficha legal publicable (Res. CPLT 372). Regla de salida del protocolo: lo FALSO se
corrige citando la evidencia y conservando el texto original; lo OBSOLETO se marca con
la sesion en que dejo de valer. Este script aplica exactamente eso, reemplazo por
reemplazo, exigiendo que cada texto viejo exista UNA vez; si no, aborta sin tocar nada.

Los cierres por guard (regla B) viven en tests/test_guard_declarado_vs_efectivo_s131.py.
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WS = os.path.abspath(os.path.join(ROOT, "..", ".."))

R = []  # (archivo, viejo, nuevo)

# ---------------- FICHA SDA (documento legal) ----------------
F = "docs/FICHA_SDA_VRP_CHILE.md"
R.append((F,
 "Radiancia/temperatura de brillo de sensores MODIS (MOD14/MYD14) y VIIRS.",
 "Radiancia y temperatura de brillo de los productos calibrados de nivel 1B: MODIS "
 "`MOD021KM`/`MYD021KM` con su geolocalización `MOD03`/`MYD03`, y VIIRS "
 "`VNP02IMG`/`VJ102IMG`/`VJ202IMG` (375 m) y `VNP02MOD`/`VJ102MOD`/`VJ202MOD` (750 m) con "
 "sus geolocalizaciones. El sistema calcula las anomalías térmicas a partir de la "
 "radiancia; no consume el producto de incendios MOD14/MYD14."))
R.append((F,
 "Mitigación: filtros de contexto, zonas de exclusión y degradación explícita a fondo regional.",
 "Mitigación: filtros de contexto y degradación explícita a fondo regional."))
R.append((F,
 "en los métodos que usan radiancia infrarroja media (MIR) absoluta; mitigado normalizando por índice térmico (NTI).",
 "en los métodos que usan radiancia infrarroja media (MIR) absoluta. El sistema no aplica hoy "
 "una corrección para este sesgo: la normalización por índice térmico (NTI) en la integral "
 "del Test 1 está implementada pero desactivada en el perfil operacional, y la posición "
 "estimada del foco puede desplazarse hasta ~1 km respecto del cráter en los volcanes de "
 "cumbre nevada. El límite está caracterizado y documentado (A69)."))
R.append((F,
 "| v1.4 | 2026-08-30 |",
 "| v1.5 | 2026-09-02 | **Corrección de tres afirmaciones falsas detectadas por auditoría "
 "(sin cambios de lógica).** (1) La entrada declarada era el producto de incendios "
 "MOD14/MYD14; el sistema consume radiancias L1B (`MOD021KM`/`MYD021KM`, `VNP02IMG`/`VNP02MOD` "
 "y equivalentes NOAA-20/21) y calcula las anomalías por sí mismo. (2) Las «zonas de "
 "exclusión» figuraban como mitigación y están desactivadas desde S27 "
 "(`ENABLE_EXCLUDE_ZONES=False`). (3) El sesgo topográfico figuraba como «mitigado "
 "normalizando por NTI» y esa normalización está desactivada "
 "(`ENABLE_TEST1_NTI_INTEGRAL=False`); se declara ahora como límite caracterizado sin "
 "mitigación activa. Además, los módulos con cabecera FICHA son 16 (se suman `regrid.py` "
 "y `vrp_regimes.py`, cuya cabecera nombraba también MOD14 y fue corregida). Los tres "
 "puntos quedan cubiertos por guards ejecutables "
 "(`tests/test_guard_declarado_vs_efectivo_s131.py`). Fuente: `docs/AUDIT_S131.md`. | "
 "`docs/s131/agentes/DECLARADO_VS_EFECTIVO.md` |\n| v1.4 | 2026-08-30 |"))

# ---------------- MISSION ----------------
M = "docs/MISSION.md"
R.append((M,
 "| Pisos VRP por sensor | Coppola 2023 dice \"floor ~1 MW\" genérico, no por sensor | ⚠️ **SIGUEN ACTIVOS** (corregido S124).",
 "| Pisos VRP por sensor | Coppola 2023 dice \"floor ~1 MW\" genérico, no por sensor | ✅ **RETIRADOS S130** (PR #571, ciclo A45 completo): los tres pisos valen `0.0` en `mirova_equivalent.yaml`; el helper `_apply_vrp_floor` (`pipeline/store.py:72-103`) sigue existiendo y se llama en `store.py:489`, pero con piso 0 no actúa. Medido al retirarlo: 0 noches MIROVA-confirmadas perdidas, VIIRS750 recall 82,52 → 84,55 %, 582 records invisibles → 0; el piso de MODIS nunca actuó (0 de 11.717). Texto anterior, por historia: ⚠️ ~~SIGUEN ACTIVOS~~ (corregido S124)."))
R.append((M,
 "| ⚠️ **SIGUE ACTIVA en VIIRS 375 (corregido S125).** La perilla del perfil existe y está neutra (`CLOUD_MASK_BT_K = 0.0`, que apaga la máscara en MODIS y V750), pero `process_viirs.py:674` tiene `CLOUD_BT_THRESHOLD = 260.0` **hardcodeado**,",
 "| ✅ **RETIRADA S126 (PR #535).** El umbral sale del perfil (`process_viirs.py:786`: `CLOUD_BT_THRESHOLD = CLOUD_MASK_BT_K`) y `cloud_mask_bt_k` vale `0.0`, así que la máscara está apagada en los tres sensores; el cambio de una línea que esta fila pedía ya se hizo. Texto anterior, por historia: ⚠️ ~~SIGUE ACTIVA en VIIRS 375 (corregido S125)~~. La perilla del perfil existe y está neutra (`CLOUD_MASK_BT_K = 0.0`, que apaga la máscara en MODIS y V750), pero `process_viirs.py:674` tenía `CLOUD_BT_THRESHOLD = 260.0` **hardcodeado**,"))
R.append((M,
 "el bloque está vivo y **sin flag** en los 3 procesadores (`process_viirs.py:1502-1568`, `process_modis.py:1167-1204`, `process_viirs_mod.py:1055`)",
 "el bloque está vivo en los 3 procesadores (`process_viirs.py:1642-1710`, `process_modis.py:1196-1230`, `process_viirs_mod.py:1069`; líneas actualizadas S131) y está **parcialmente gateado**: la rama de clúster rival débil depende de `ENABLE_TEST1_PRIORITY_WEAK_CLUSTER` (`process_viirs.py:1695`), el resto no tiene flag"))
R.append((M,
 "   - **Abiertas**: D2 cobertura CSV ground truth · D3 FP explícito MIROVA ·\n",
 "   - **Abiertas**: (⚠️ S131: esta enumeración quedó congelada en S105 y omitía D13, D17 y D18. "
 "**El catálogo `docs/MIROVA_DIVERGENCES.md` es la lista viva; esta sección no la duplica** — "
 "para el estado de hoy, leer los encabezados de cada D en ese archivo. Lo que sigue se conserva por historia.) "
 "D2 cobertura CSV ground truth · D3 FP explícito MIROVA ·\n"))

# ---------------- CLAUDE.md ----------------
C = "CLAUDE.md"
R.append((C,
 "- **`radius_km = 25 km` uniforme** para volcanes chilenos — replica grilla\n  MIROVA UTM 51×51 km (radio inscrito 25.5 km).",
 "- **`radius_km = 25 km` en los 11 Tier A** — replica grilla MIROVA UTM 51×51 km\n  (radio inscrito 25.5 km). Los 34 volcanes restantes quedan en 5 km (`volcanoes.yaml`:\n  `{25: 11, 5: 34}`, verificado S131; el texto anterior decía «uniforme» y era falso)."))
R.append((C,
 "- `volcanoes.yaml` (45 configurados, 11 con data, 34 sin pull)",
 "- `volcanoes.yaml` (45 configurados · 11 Tier A con serie continua desde 2025-02 · 34 con\n  una ventana corta de abril-2026 (67-94 records c/u) en `data/mirova_equivalent/`, fuera del\n  cron NRT — corregido S131: antes decía «11 con data, 34 sin pull»)"))
R.append((C,
 "  → magnitud 8-15× MIROVA. Vols con ΔT >20K (Lascar 21.6K, Isluga ~20K) calibrados\n  naturalmente sin fix.",
 "  → magnitud 8-15× MIROVA. Vols con ΔT >20K (Lascar 21.6K, Isluga ~20K) calibrados\n  naturalmente sin fix. ⚠️ **El ejemplo es FALSO — medido S128, marcado S131.** Los ΔT\n  reales son Láscar **16,9 K** e Isluga **8,3 K** (`scripts/libro_de_cuentas.py`, ids\n  `A12_dT_lascar` / `A12_dT_isluga`). Isluga cae debajo del propio corte de 12 K, o sea\n  pertenece a la clase que la regla dice que necesita kernel-bg. La lección de método\n  (el patrón térmico decide, validar por A/B — A19) sigue; los dos números no."))
R.append((C,
 "  (887 filas). `scripts/build_c2ab_windows.py:55` consume el congelado. Texto original:",
 "  (887 filas). ~~`scripts/build_c2ab_windows.py:55` consume el congelado~~ (⚠️ S131: ya\n  no — `build_c2ab_windows.py:64` apunta al snapshot vivo y el comentario de la l. 55\n  documenta el fix; el split de archivos sí sigue existiendo). Texto original:"))
R.append((C,
 "    `process_viirs.py:958`** — `process_modis.py:674` y `process_viirs_mod.py:665`\n    importan únicamente `compute_test1_mir`, sin alternativa.",
 "    `process_viirs.py:206/1070`** (era 958) — `process_modis.py:59` y `process_viirs_mod.py:153`\n    (eran 674/665; líneas actualizadas S131) importan únicamente `compute_test1_mir`, sin alternativa."))
R.append((C,
 "  repo (el docstring de `process_viirs_mod.py:409` nombraba los 5 volcanes opt-in desde",
 "  repo (el docstring de `process_viirs_mod.py:416` —era 409— nombraba los 5 volcanes opt-in desde"))
R.append((C,
 "  = lo que MIROVA reporta. Dashboard (frontend/index.html:680) usa pc.vrp_mw. Audits con",
 "  = lo que MIROVA reporta. Dashboard (`mirovaEqVrp`/`isValidDetection` en frontend/index.html,\n  ~l. 1372; el `:680` original hoy es una fila de la lista de volcanes) usa pc.vrp_mw. Audits con"))
R.append((C,
 "- **Concurrency (S123)**: los 6 workflows que hacen `git push` a main comparten\n  `group: push-main` con `cancel-in-progress: false` — nrt, nrt-retry,\n  sync-mirova-csv, audit-weekly, backfill y reproc. Un yml nuevo que pushee a\n  main declara ese mismo grupo **salvo que implemente su propio retry de push**,\n  que es la defensa real contra la carrera de `git push` que el PR #502 cerró.\n  **Verificado S127: hay 3 excepciones deliberadas**, cada una con su razón en el\n  comentario — `reproc-s124-ndc-focus`, `reproc-s124-villarrica-op-ab` y el job\n  `merge` de `reproc-chunked` (#546). Todas tienen `pull --rebase` + `push` con 5\n  reintentos y backoff.",
 "- **Concurrency (S123, reescrito S131)**: un workflow que hace `git push` a main debe tener\n  **o** `group: push-main` (`cancel-in-progress: false`), **o** su propio bucle de reintento\n  `pull --rebase` + `push` (5 intentos con backoff) — la defensa real contra la carrera que\n  el PR #502 cerró. **No se mantiene acá la lista de cuáles son**: envejece sola (S123 decía\n  «6 workflows / 3 excepciones» y al medir en S131 eran 9 pushers, 5 en el grupo y 4 con\n  retry propio — `nrt-retry` no pushea y `audit-weekly` sí, con retry). La condición la mide\n  el guard `tests/test_guard_declarado_vs_efectivo_s131.py::test_g4_pusher_push_main_o_retry`\n  derivando la lista de los yml, y ese es el contrato."))
R.append((C,
 "   **abiertas D2 y D3** (ambas congeladas desde S27, sin plan activo; D2 quedó\n   mitigada de facto por el loader CONS∪OCR de S86 pero el doc nunca se actualizó)",
 "   (⚠️ S131: no duplicar acá la lista de abiertas — quedó congelada en S123 y omitía\n   D13, D17 y D18; el estado vivo son los encabezados de cada D en el catálogo) ~~**abiertas\n   D2 y D3**~~ (ambas congeladas desde S27, sin plan activo; D2 quedó mitigada de facto por el\n   loader CONS∪OCR de S86 — medida en 79,2 % en S128 y anotada en el doc en S131)"))

# ---------------- README ----------------
RM = "README.md"
R.append((RM,
 "- **Detection anchored to the physical crater** (`vent_lat/lon`), while the 50×50 km\n  grid uses the official MIROVA grid center — these are decoupled on purpose",
 "- **Detection anchored to the physical crater** (`vent_lat/lon`). The ROI is currently\n  built around the configured volcano coordinates, **not** around the official MIROVA grid\n  center — see divergence D17 in `docs/MIROVA_DIVERGENCES.md` (`get_grid_center()` exists\n  but is not wired into production; `ENABLE_UTM_REGRID=False`)"))
R.append((RM,
 "- **TIR VRP** (VIIRS I05, 11.45 µm): Stefan-Boltzmann (Aveni et al. 2024, TIRVolcH)\n",
 "- **TIR VRP** (VIIRS I05, 11.45 µm, Stefan-Boltzmann, Aveni et al. 2024) — implemented,\n  currently **disabled** in the operational profile (`ENABLE_VRP_TIR_OUTPUT=False`); the\n  published `vrp_tir_mw` field is 0\n"))
R.append((RM,
 "34 additional volcanoes are configured under the `experimental` profile (outside the\noperational dashboard).",
 "34 additional volcanoes are configured but outside the NRT cron; they carry a short\nApril-2026 backfill window in `data/mirova_equivalent/` and are not part of the\noperational dashboard selection."))
R.append((RM, "### Dashboard (frontend — 3 standalone views)", "### Dashboard (frontend — 3 live views + 1 preview)"))
R.append((RM, "|-- frontend/                     3 standalone views (see above)",
          "|-- frontend/                     3 live views + comparacion.html (preview, see above)"))

# ---------------- MIROVA_DIVERGENCES ----------------
D = "docs/MIROVA_DIVERGENCES.md"
R.append((D,
 "**Hallazgo Nicolás 2026-04-29**: el CSV scrapeado de `latest.php` NO está al 100%.\nCobertura estimada: **~70% para VIIRS** (375m y 750m).",
 "> **Actualización S128/S131.** La cobertura medida es **79,2 %**, no ~70 %\n> (`docs/AUDIT_S128.md` §4), y el loader canónico CONS ∪ OCR (S86, `experiments/_s126_lib.py::cargar_mirova`)\n> ya la mitiga de facto: las métricas del proyecto se calculan sobre esa unión. El\n> «re-scrapear» pendiente de abajo quedó superado por `sync-mirova-csv.yml` (cron 1 h).\n> Esta sección se conserva como quedó escrita el 2026-04-29.\n\n**Hallazgo Nicolás 2026-04-29**: el CSV scrapeado de `latest.php` NO está al 100%.\nCobertura estimada: **~70% para VIIRS** (375m y 750m)."))
R.append((D,
 "### D3 — MIROVA distingue FP explícito; nuestros JSONs no\n",
 "### D3 — MIROVA distingue FP explícito; nuestros JSONs no\n\n> **S131**: los conteos de abajo (13.378 RUTINA, 407 Muy Bajo, 165 Bajo, 253 FP) son del\n> 2026-04-29 y **no tienen instrumento que los recompute** (no hay entrada en\n> `scripts/libro_de_cuentas.py`). Son conteos absolutos sobre un corpus vivo (A90): se\n> conservan como fotografía de esa fecha; **no usar como línea base** sin volver a medir.\n"))
R.append((D,
 "`mirovaEqVrp` del frontend desde S33). Siguen ON en `mirova_equivalent.yaml`.",
 "`mirovaEqVrp` del frontend desde S33). ~~Siguen ON en `mirova_equivalent.yaml`~~ → **OFF desde S118** (flip PR #474, verificado S119 y S131; ver bloque «RESUELTO S118» más abajo)."))
R.append((D,
 "por volcán — **ABIERTA (medida, sin A/B)** S129",
 "por volcán — **ABIERTA (A/B corrido S130 → NO ADOPTAR; divergencia de fidelidad literal, prioridad baja)** S129/S130"))

# ---------------- INDEX ----------------
I = "docs/INDEX.md"
R.append((I,
 "| **AUDIT_S127.md** | **Última — eje «declarado ≠ efectivo» (T9): 4 afirmaciones falsas, 3 guards** | **S127** |",
 "| AUDIT_S131.md | Resultados + dashboard + utilidad OVDAS; 6 ejes (magnitud/ATBD, dashboard, T9, pendientes, TIF por pasada, otro sensor) | S131 |\n| AUDIT_S128.md | Evidencia exógena: ángulo de vista, grilla desde KMZ, D2 medida, GAP #A reabierto | S128 |\n| AUDIT_S127.md | Eje «declarado ≠ efectivo» (T9): 4 afirmaciones falsas, 3 guards | S127 |"))

# ---------------- pipeline: solo comentarios/docstrings ----------------
SG = "pipeline/scan_geometry.py"
R.append((SG,
 "Polar-orbiting cross-track scanners (MODIS, VIIRS) project a wider IFOV onto\nthe ground as the scan angle increases. Without correction, VRP values use the\nnadir pixel area and underestimate radiative power at off-nadir pixels.\n",
 "**Nota operacional (S131)**: el pipeline usa área de píxel **nadir-fija** en los tres\nsensores (`ENABLE_NADIR_FIXED_PIXEL_AREA_{MODIS,VIIRS}=True`, A66/A67) — las ramas sec³ y\nde corrección leve de abajo NO se ejecutan en producción. Lo que sigue describe la\ngeometría; el estado real lo da `pipeline.profile`. Sobre el sub-reporte con el ángulo que\nel área nadir-fija sin remuestreo produce, ver `docs/s131/REMUESTREO_LEY_DE_AREA.md`.\n\nPolar-orbiting cross-track scanners (MODIS, VIIRS) project a wider IFOV onto\nthe ground as the scan angle increases. Without correction, VRP values use the\nnadir pixel area and underestimate radiative power at off-nadir pixels.\n"))
R.append((SG,
 "    MIROVA publica detecciones en esas esquinas (Llaima Conguillio a 28 km\n    del vent, en esquina NE del bbox). Cambiar a bbox recupera esas refs.\n",
 "    MIROVA publica detecciones en esas esquinas (Llaima Conguillio a 28 km\n    del vent, en esquina NE del bbox).\n\n    Uso actual (S131): el flag `enable_roi1_box_paper` (OFF, A/B S130 → NO ADOPTAR)\n    aplica esta función con `half_km = ROI1_BOX_HALF_KM = 2.5` para la caja 5×5 del\n    ROI1 (D18); el ROI exterior sigue siendo el círculo de `radius_km`.\n"))
R.append((SG,
 "    sample distance regardless of scan angle. Empirical aggregated I-band\n    pixel area varies only between ~0.32 and ~0.6 km^2 across the full\n    swath (Cao et al. 2014, JGR Atmospheres 119), not the sec^3 ~25x that\n    a non-aggregated scanner would produce.\n",
 "    sample distance regardless of scan angle.\n\n    ⚠️ S131: la cifra que seguía acá («~0.32 a ~0.6 km², Cao 2014») está MAL. Contra el\n    ATBD de geolocalización VIIRS (423-ATBD-002, Tabla 2.2-1) el HSI de I4 va de\n    0.371×0.388 km (nadir) a 0.80×0.789 km (fin de swath): área 0.144 → 0.631 km²,\n    **4.38×**. El «approximately 2» del ATBD es POR EJE; el área es el producto. El tope\n    de 2.0× de abajo hereda esa lectura y sub-corrige; la rama está muerta en producción\n    (nadir_fixed=True). Ver `docs/s131/REMUESTREO_LEY_DE_AREA.md`. Texto original:\n    «Empirical aggregated I-band\n    pixel area varies only between ~0.32 and ~0.6 km^2 across the full\n    swath (Cao et al. 2014, JGR Atmospheres 119), not the sec^3 ~25x that\n    a non-aggregated scanner would produce.»\n"))
PV = "pipeline/process_viirs.py"
R.append((PV,
 "        # valid_mask = cloud_free (S112 review MEDIUM): igualar el criterio del fondo\n        # global (excluye nubes I05<260K) para no inflar la magnitud con topes de nube\n        # fríos dentro del anillo en noches de cirrus.\n",
 "        # valid_mask = cloud_free (S112 review MEDIUM): mantiene el mismo criterio que\n        # el fondo global. S131: desde S126 (#535) la máscara de nube está apagada\n        # (`cloud_mask_bt_k: 0.0`), así que cloud_free es todo-True y NO excluye nada;\n        # el comentario original decía «excluye nubes I05<260K» y ya no aplica.\n"))

# ---------------- MAPA_WORKSPACE (workspace, fuera del repo) ----------------
MW = os.path.join(WS, "MAPA_WORKSPACE.md")
R.append((MW,
 "     │ \U0001f534 CAÍDO     │  │ VegStress│ │  NHI   │ │ esqueleto│",
 "     │ \U0001f7e2 VIVO      │  │ VegStress│ │  NHI   │ │ esqueleto│"))
R.append((MW,
 "Latente en VRP-chile (5 de 6 sin grupo de concurrency)",
 "~~Latente en VRP-chile (5 de 6 sin grupo de concurrency)~~ (S131: los 9 workflows de VRP-chile que pushean a main tienen `push-main` o retry propio ×5 — cubierto, con guard)"))


def main():
    cambios = 0
    textos = {}
    for f, old, new in R:
        p = f if os.path.isabs(f) else os.path.join(ROOT, f)
        s = textos.get(p) or open(p, encoding="utf-8").read()
        c = s.count(old)
        if c != 1:
            print(f"ABORT {f}: {c} ocurrencias de {old[:110]!r}")
            return 1
        textos[p] = s.replace(old, new)
        cambios += 1
    for p, s in textos.items():
        open(p, "w", encoding="utf-8", newline="\n").write(s)
        print("ok", os.path.relpath(p, ROOT))
    print(f"total reemplazos: {cambios}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
