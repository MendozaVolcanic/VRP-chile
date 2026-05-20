# Experimento 126 — Audit Lastarria path D cirrus (S70-2 T4)

## Pregunta
Nicolás reportó "MW altos 20 en dashboard Lastarria". Diagnóstico previo identificó que 32 records summit Lastarria con eqVrp>5 MW disparan **solo** por path D dNTI contextual. ¿Son señal volcánica real o FPs causados por cirrus alto frío?

## Método
Cross-check de los 32 records contra MIROVA NRT (CSV consolidado + OCR universe, tolerancia ±10 min).
Para cada record nuestro, buscar match temporal en MIROVA y clasificar:
- ALERTA (MIROVA también detecta): TP
- RUTINA o sin match: FP candidato

## Resultados

| Verdict | Count | % |
|---|---|---|
| Total records eqVrp>5 summit | 32 | 100% |
| MIROVA reporta ALERTA (cons o OCR) | 10 | 31.2% |
| MIROVA NO reporta | 22 | 68.8% |
| - de los cuales: RUTINA explícita | 6 | 18.8% |
| - de los cuales: sin record MIROVA | 16 | 50.0% |
| - FALSO_POSITIVO explícito MIROVA | 0 | 0% |

**Hallazgos clave**:
- 100% de los 32 records disparan SOLO por path D (BT path=0, NTI path=0).
- 91% de los FPs (20/22) tienen t_bg < 270K (cirrus alto frío).
- 10/32 TPs reales pero amplificados 21-150× sobre MIROVA (ratio mediano 62×).

## Conclusión
Path D tiene doble modo de falla en cirrus alto:
1. Firing espurio (FPs por heterogeneidad de campo enfriado por nube).
2. Amplificación en TPs (suma pixels marginales que MIROVA descarta).

Documentado como D9 en `docs/MIROVA_DIVERGENCES.md` + H_S70_PATH_D_CIRRUS_FP en `docs/HYPOTHESIS_LOG.md`.

## Cómo reproducir

El script lee paths relativos a CWD. Correr desde el worktree root:

```bash
cd C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70

# Copiar el JSON de records al CWD (el script lo lee como ./lastarria_high_summit.json)
cp experiments/126_lastarria_pathd_audit/lastarria_high_summit.json ./lastarria_high_summit.json

python experiments/126_lastarria_pathd_audit/audit_cross_check.py
```

Lee `lastarria_high_summit.json` (lista de 32 records pre-extraídos del JSON) + CSVs MIROVA en `data/mirova_reference/`, genera resultados en stdout. La salida persistida está en `results.json`.

## Archivos
- `audit_cross_check.py` — script de cross-check (renombrado de `cross_check.py`).
- `lastarria_high_summit.json` — 32 records summit eqVrp>5 extraídos de `data/mirova_equivalent/Lastarria.json`.
- `results.json` — resultados completos del cross-check con verdict por record.

## Pendiente S71
Brainstorming + A/B test profile flag con una de las 3 opciones de gate atmosférico propuestas en D9.
