# S16 E2 — Revertir MODIS vent-path a S9 (solo si E1 no cierra el gap)

> Plan condicional: ejecutar SOLO si E1 (s9_vent_permissive) no sube Lascar
> recall MODIS al nivel S9. E1 es la primera línea de ataque.

## Pregunta pivotal E2

E1 revirtió el vent-path sigma-gating VIIRS a S9 (threshold fijo 1K).
Si eso NO recupera MODIS Lascar recall (que era 0.83 en S9), probablemente
la causa es H2 (MODIS vent threshold S12: 2.5K + floor 0.3 MW), no H1.

## Config S9 MODIS vent (git show ecb5d66)

- `enable_vent_path_modis: true` (default, no flag separado).
- `modis_vent_threshold_k`: no existe como flag separado → usa `vent_threshold_k=1.0`.
- `modis_vent_vrp_floor_mw`: no existe → sin floor.

## Config S15 MODIS vent actual

```yaml
enable_vent_path_modis: true     # S12 E1 reactivó
modis_vent_threshold_k: 2.5      # S12: 2.5x más estricto que S9 (1.0)
modis_vent_vrp_floor_mw: 0.3     # S12: nuevo, sin equivalente S9
```

## Propuesta E2 — profile `s9_modis_vent_permissive.yaml`

Extensión de `s9_vent_permissive` (E1) agregando cambio MODIS:

```yaml
paths:
  enable_vent_path_modis: true
  modis_vent_threshold_k: 1.0      # revertir a S9 default
  modis_vent_vrp_floor_mw: 0.0     # sin floor, como S9
```

Mantener TODO lo demás (P3.1, P3.2, bbox, sigma-cap, n_sigma_vent=0 de E1).

## Volcanes target E2

Solo MODIS-relevantes (Lascar es el canario). El reproceso requiere MODIS
processing → **NO corre en Windows local por pyhdf**. Opciones:

1. Esperar que NRT en GitHub Actions lo corra con el perfil (requiere push a
   main) — demasiado riesgoso antes de validación.
2. Crear CI workflow dedicado para E2 reproceso MODIS-only usando Docker.
   Más esfuerzo.
3. Validar E2 solo con métricas post-push E1+E2 vs baseline S15.

## Criterios éxito E2

- Lascar MODIS recall sube a ≥0.70 (S9 era 0.83; admitimos que filtros S15
  quiten algo).
- Precision no cae debajo de 0.50.
- FPs Chaitén MODIS no aumentan más de 30% vs E1.

## Por qué E2 es condicional

Si E1 ya cierra Tupungatito y Chaitén (ambos VIIRS-dominantes), el problema
MODIS es marginal — los 11 volcanes MIROVA-monitoreados tienen la mayoría
de refs en VIIRS, no MODIS. E2 se activaría si:

1. Lascar MODIS recall post-E1 < 0.50.
2. O si la discusión con usuario revela que MODIS recall es operacionalmente
   crítico (no solo VIIRS).

## Anti-patrón evitar

- **No ejecutar E1+E2 simultáneamente** — stackear cambios imposibilita
  atribuir mejoras.
- **Primero E1**, medir, solo entonces decidir E2.

## Estado actual

Pendiente ejecución E1 (en curso). Plan E2 preparado para no perder tiempo
si hace falta.
