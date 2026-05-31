# BLOQUE ARRANQUE S94

**Sesión previa S93 (2026-05-30).** Muy larga y productiva. 5 PRs mergeados
(#276-280) + #223 cerrado. 0 cambios al pipeline NRT operacional (todo display /
docs / loader-de-audits). main al día, CI sano, deploys OK.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S94.md
cat docs/AUDIT_S93_artefactos_sobreestimacion.md   # leer COMPLETO incl. §7 corrección
```

## §0.5 — Integridad (vigente S91/S92/S93)
Ningún número a mano: script reproducible = fuente de verdad + verificación
programática antes de commit. **A48 reforzado 2× en S93**: los subagentes y hasta
los tests S86 codificaron convenciones NO verificadas (bug VIIRS750). Verificar
SIEMPRE la convención real (frontend / CSV crudo / palabra de Nicolás) antes de
construir análisis sobre un bucketing/heurística.

## §1 — Qué cerró S93
1. **Detección diurna MODIS** — CERRADO (PR #276): inviable validar (0 alertas
   diurnas con TIF en los 11 Tier A). flag OFF.
2. **Display campo difuso PCC** — HECHO (PR #277): filtro "campo difuso (fondo
   frío)" en las 3 vistas (artefacto A23/D9, t_max+geometría, NO t_bg).
3. **Auditoría artefactos + diagnóstico raíz** (PR #278): el VRP Wooster sobre
   fondo gélido lee contraste nieve↔terreno como fondo↔lava → sobre-estima 20-200×.
4. **F1 display por sensor** (PR #279 + corregido en #280): métricas separadas
   por sensor (VIIRS375 / VIIRS750 / MODIS) en index; las 3 vistas.
5. **Bug VIIRS750 corregido** (PR #280, Nicolás lo detectó): el loader
   `normalize_sensor` mapeaba CSV "VIIRS" (=M-band 750m) como VIIRS375. **MIROVA SÍ
   publica VIIRS750** (158 alertas Tier A; detecta menos que VIIRS375 627, no es 0).
   Fix loader + test + revert exclusión VIIRS750 del display.

## §2 — PENDIENTE PRINCIPAL S94: RE-ANÁLISIS POR SENSOR (con datos correctos)

El bug VIIRS750 (corregido #280) **invalidó la división VIIRS375/VIIRS750** de la
tabla de auditoría S93 (AUDIT_S93 §6; ver §7 corrección). Hay que rehacerla con el
loader ya arreglado. Objetivo (criterio de Nicolás, clon MIROVA):
> MIROVA publica los 3 sensores por separado: no reporta artefactos de campo frío;
> sí reporta toda anomalía volcánica real (por débil que sea); si hay un incendio u
> otro artefacto más fuerte en la pasada, reporta el dominante.

Pasos S94:
1. **Re-correr el análisis por-sensor** (`experiments/_s93_audit/covalidation_impact.py`
   ya usa el loader corregido) — recall/precision/ratio CORRECTOS para MODIS,
   VIIRS375 y VIIRS750 por separado. Hallazgo a explicar: en el frontend, VIIRS750
   daba **recall 0.00** (MIROVA reporta VIIRS750 pero no matcheamos) — ¿perdemos las
   VIIRS750 reales, o las nuestras son artefacto/fuera-de-radio? systematic-debugging.
2. **Replantear el plan F2-F5** con esos números (el plan vive en
   `docs/superpowers/specs/2026-05-30-clon-mirova-por-sensor-design.md`):
   - F2 reproc histórico local (limpia deuda 337/190 MW; NO toca código).
   - F3 co-validación SOLO MODIS (la raíz; sigue candidata — MODIS 79 alertas/77
     Lascar = "solo lo grande"; el bug era del VIIRS, no del MODIS). **A45: tag + OK
     Nicolás + TDD + reproc + R2 antes de tocar process_modis.py.**
   - F4 VIIRS750 (¿por qué recall 0? ¿calibración?). F5 VIIRS375 reportar-foco.

## §3 — Sigue VÁLIDO de S93 (no re-derivar)
- Diagnóstico raíz físico (Wooster sobre fondo gélido). Conclusión MODIS ("solo ve
  lo grande", co-validación-solo-MODIS segura: 74 TP MODIS 100% cubiertos por VIIRS375).
- Cap D9 (5 MW) funciona desde ~05-23 (MODIS+VIIRS); picos viejos = deuda histórica (A18).
- Co-validación GLOBAL descartada (mata 93% recall). Display campo difuso + cirrus OK.

## §4 — Escudo anti-drift (vigente)
NO gate t_bg ciego (S86). Co-validación distingue por COHERENCIA (foco duro), no fondo
frío. NO tocar VIIRS375 detección (recall). NO pipeline sin tag + OK (A45). A47 (no
paralelo sobre data/mirova_equivalent). A48 (verificar convención antes de heurística).

## §5 — Referencias durables
- `docs/AUDIT_S93_artefactos_sobreestimacion.md` (incl. §7 corrección bug VIIRS750).
- `docs/superpowers/specs/2026-05-30-clon-mirova-por-sensor-design.md` (plan 5 fases).
- Memoria: [[reference_s93_clon_mirova_por_sensor]] (con corrección), [[reference_s91_warmscene_pcc_closed]].
- Scripts: `experiments/_s93_audit/` (loader corregido — re-correr).

## §6 — Comunicación
Geólogo: fenómeno físico → mecanismo → fórmula al final. Provenance para el paper.
