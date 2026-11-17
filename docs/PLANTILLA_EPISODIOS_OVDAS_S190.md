# Plantilla: tabla de episodios OVDAS para validar el laboratorio (D4 de `docs/PLAN_EXPERIMENTAL_S190.md`)

**Para qué sirve.** El laboratorio busca calor real que MIROVA no publica. Para saber si lo que encuentra es volcánico
hace falta una vara que no sea MIROVA. La más importante es lo que el OVDAS sabe que pasó en cada volcán, y hoy no
existe como dato en el repo (`docs/audit_s149/plan_final/FRENTE_F_EXPERIMENTAL.md`, F-3). Esta tabla la llena
Nicolás desde los RAV y los cambios de alerta técnica.

**Dónde guardarla.** `docs/referencia_ovdas/episodios_tier_a.csv` (UTF-8, separador coma). Va en `docs/` y no en
`data/` para que no la copie ni la dispare el deploy de Pages.

**Alcance.** Los 11 Tier A, desde el 2026-02-01 hasta hoy. Cordón Caulle se puede anotar aunque quede fuera de la
primera tanda (D6). Una fila por episodio. Si un volcán no tuvo nada en el período, una fila con `tipo = sin_episodios`
y las fechas del período: así se distingue «revisado y tranquilo» de «no revisado».

## Columnas

| columna | qué va | ejemplo |
|---|---|---|
| `volcan` | nombre como en `volcanoes.yaml` | `Villarrica` |
| `inicio` | fecha del primer día del episodio, AAAA-MM-DD | `2026-03-10` |
| `fin` | último día; vacío si sigue | `2026-04-02` |
| `tipo` | uno de: `incandescencia`, `lago_lava`, `desgasificacion`, `fumarolica`, `explosiva`, `efusiva`, `domo`, `cambio_alerta`, `sin_episodios`, `otro` | `incandescencia` |
| `termico_esperado` | `si`, `no` o `no_se`: si el fenómeno debería verse en el infrarrojo nocturno | `si` |
| `lugar` | dónde, en palabras (cráter principal, flanco N, Lazufre) | `cráter principal` |
| `alerta_tecnica` | color vigente durante el episodio | `amarilla` |
| `fuente` | RAV o documento, con número o fecha | `RAV Villarrica 2026-03` |
| `nota` | cualquier cosa útil, corta | `visto en cámara IP` |

## Ejemplo (inventado, sólo para mostrar el formato)

```csv
volcan,inicio,fin,tipo,termico_esperado,lugar,alerta_tecnica,fuente,nota
Villarrica,2026-03-10,2026-04-02,incandescencia,si,cráter principal,amarilla,RAV Villarrica 2026-03,ejemplo
Lastarria,2026-02-01,2026-11-17,sin_episodios,no_se,,verde,RAV Lastarria 2026,ejemplo
```

## Cómo se va a usar

Para cada noche en que el laboratorio publica en la zona A y producción no, se mira si cae dentro de un episodio con
`termico_esperado = si` en ese volcán, y se compara esa proporción con la de las noches sin publicación (el mismo
esquema del pareo con NHI, §6 del plan). Lastarria, que no tiene serie SWIR en NHI-v1, depende sólo de esta tabla y
de la persistencia.
