# S23 T10 — Audit experimental.yaml vs mirova_equivalent.yaml

**Fecha**: 2026-04-26 (S23 audit followup)
**Objetivo**: documentar diferencias y decidir si experimental.yaml está obsoleto
o sigue activo.

## Diferencias por parámetro

| Parámetro | mirova_equivalent | experimental | Sentido divergencia |
|---|---|---|---|
| `data_subdir` | `mirova_equivalent` | `experimental` | Outputs separados (esperado) |
| `enable_dnti_contextual_path` (Path D) | `true` | **`false`** | mirova usa Path D (P3.2 S15); experimental NO |
| `enable_dnti_dual_roi` (P3.1) | `true` | **`false`** | idem (P3.1 S15) |
| `enable_nti_relative_path` (Path C) | **`false`** | `true` | experimental prueba Path C; mirova NO |
| `max_vent_sigma_contrib_k` | `3.0` | **`5.0`** | experimental cap más laxo |
| `min_vent_pixels` | `1` | **`2`** | experimental requiere 2+ pixels (S12 E4) |
| `min_vrp_mw_modis` | `0.27` | `0.0` | mirova tiene piso S12; experimental sin piso |
| `nti_rel_min_floor` | `0.005` | **`0.008`** | experimental piso NTI más alto |
| `nti_rel_n_sigma` | `3.0` | **`5.0`** | experimental N·σ NTI más estricto |

## Conclusión: experimental.yaml NO está obsoleto

Es un **laboratorio activo** con divergencia intencional documentada en el header
del archivo:

> "Experimental laboratory profile. Designed to probe weaker signals and try
> new detection methods without affecting the operational product."

### Filosofía de los dos profiles

**mirova_equivalent** (operacional, Tier A): clon MIROVA con Path D dNTI
contextual (Coppola 2016a) y Path C OFF. Pisos S12 calibrados contra MIROVA refs.

**experimental** (laboratorio, todos los volcanes): explora Path C NTI-relativo
(MIROVA-style contextual detection) con thresholds más estrictos para evitar FPs.
Path D OFF para aislar efecto de Path C. Sin pisos (todas las detecciones se
muestran).

## Decisión

✅ **MANTENER ambos profiles activos**. NO archivar experimental.yaml.

✅ **Documentar la filosofía** en CLAUDE.md sección "Arquitectura" o nueva
sección "Profiles" para que futuros agentes entiendan la divergencia.

## Validación de continuidad

```bash
# Profiles válidos (deben aparecer ambos en VALID_PROFILES):
python -c "from pipeline.profile import VALID_PROFILES; print(VALID_PROFILES)"
# Expected: incluye 'mirova_equivalent' y 'experimental'

# data/experimental/ debe existir y poblarse del cron NRT:
ls data/experimental/*.json | wc -l
# Expected: 45 (todos los volcanes activos en YAML)
```

## Items derivados (no necesariamente S24)

1. **A/B test cuantitativo Path C vs Path D**: ¿captura distinto sub-set de
   detecciones? ¿qué passes captura uno y otro NO? Sirve para validar que
   ambos enfoques son complementarios.
2. **Convergencia futura**: si A/B muestra que Path D es estrictamente superior
   (o viceversa), considerar simplificar a un solo profile.
