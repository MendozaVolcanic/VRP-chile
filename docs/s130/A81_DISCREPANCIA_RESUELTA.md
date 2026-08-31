# S130 · La discrepancia de A81: 2.527 contra 9.196

El bloque de arranque S130 marcaba esto como **bloqueante**: *«A81 contó 2.527 records
y hoy son 9.181. Resolver eso ANTES de proponer nada ahí.»* Con razón — un número que
se triplica sin explicación invalida cualquier razonamiento que se apoye en él.

**Está resuelto, y no hubo cambio de comportamiento del pipeline. Cambió el denominador.**

## Qué se midió

Definición verbatim de `docs/S113_A46_COHERENCE_GUARD.md:24`, sin reinterpretar:

```
far→summit = distance_class == "far"
             AND primary_cluster.vrp_mw > 0
             AND primary_cluster.centroid_dist_km <= inner_radius_km
```

Es decir: el clúster **sí** es crateriano, pero un píxel lejano —un salar, un incendio,
un glaciar— le robó el `final_hotspot` y la etiqueta quedó en `far`.

Script: `experiments/_s130_a81/medir_far_summit.py`. Los once Tier A, toda la data.
Se verificó antes que los `inner_radius_km` de `volcanoes.yaml` (la fuente de verdad que
usó S113) coinciden uno a uno con la tabla de `CLAUDE.md`, para descartar que la
diferencia viniera de ahí.

## El resultado

| | |
|---|---|
| far→summit hoy | **9.196** |
| de esos, anteriores al 30-jun-2026 | **8.038** |
| posteriores | 1.158 |
| declarado en S113 | 2.527 |

El primer renglón mata la explicación fácil: **no es corpus nuevo hacia adelante**. Si
S113 hubiera medido lo mismo sobre lo que ya existía, habría contado ~8.038.

Y la tasa mensual no tiene un solo quiebre:

```
2025-02  15,1 %     2025-09  16,2 %     2026-04  16,1 %
2025-03  15,9 %     2025-10  15,8 %     2026-05  15,9 %
2025-04  15,2 %     2025-11  16,6 %     2026-06  16,6 %
2025-05  16,4 %     2025-12  17,2 %     2026-07  16,6 %
2025-06  16,1 %     2026-01  16,6 %     2026-08  15,8 %
2025-07  15,3 %     2026-02  15,0 %
2025-08  16,0 %     2026-03  15,8 %
```

## La causa

El corpus **creció hacia atrás**, no hacia adelante. S113 corrió a fines de junio de
2026 sobre data que arrancaba en febrero de ese año — unos cinco meses. El backfill
histórico de 2025 entró en **S120, entre el 2 y el 16 de julio de 2026**:

```
2d5345fcc  2026-07-15  data(backfill): Villarrica 2025-02-15..2025-05-15 (S120)
324517597  2026-07-15  data(backfill): Lascar     2025-02-15..2025-05-15 (S120)
cb44d8cae  2026-07-02  data(backfill): PCC        2025-05-15..2025-08-15 (S120)
        … y sus hermanos por volcán
```

Reconstruyendo la ventana que S113 **pudo** ver —febrero a junio de 2026, con junio a
dos tercios porque corrió alrededor del día 20—: **2.579** contra los **2.527**
declarados. Un 2 % de diferencia, dentro de lo que explica no saber el día exacto de
corte.

## Lo que esto ata

**9.192 de los 9.196 son MODIS.** Cuatro son VIIRS. Sobre 11.711 records MODIS, eso es
el **78,5 %**.

Ese número es la contracara exacta de otra medición de esta misma sesión, hecha por un
camino independiente (`experiments/_s130_piso_vrp/paridad_por_sensor.py`): contra las
noches que MIROVA declaró ALERTA en MODIS, **el pipeline encuentra el cráter el 97,6 %
de las veces y el dashboard cuenta el 12,2 %**.

No son dos hallazgos. Es el mismo, visto desde dos lados: en MODIS la etiqueta
`distance_class` casi nunca sigue al clúster, porque el `final_hotspot` —que se elige
por MIR absoluto— se va a un salar o a un valle tibio (**A69**). El clúster
vent-anchored sí queda en el cráter.

## Qué NO cambia

**A81 y A82 siguen en pie tal como están.** El fenómeno no se movió: sólo se midió sobre
más data. Nada de esto reabre el far→summit MODIS, que S114 cerró con evidencia
convergente tras descartar ocho discriminantes, los umbrales N·σ de la Tabla 1 y tres
ejes ortogonales. El único aviso del bloque —resolver la discrepancia antes de proponer
nada— queda cumplido, y la conclusión es que **no había nada que proponer**.

Lo que sí conviene registrar es la lección de método.

## La lección

Un conteo absoluto sobre un corpus que crece **no es comparable consigo mismo entre
sesiones**, y falla en silencio: nadie recibe un error, sólo un número distinto que
parece un hallazgo. La tasa (15-17 %) era estable todo el tiempo; la cuenta se triplicó.

Es el mismo problema de denominador que `scripts/libro_de_cuentas.py` ya documenta en
`flags_true` y que apareció otra vez hoy al registrar `recall_v750_dash`. La regla que
sale de las tres: **una afirmación numérica sin su denominador no es una afirmación**.
Cuando el número cuente elementos de un corpus vivo, registrar la **proporción** además
del total, o la ventana temporal junto al conteo.
