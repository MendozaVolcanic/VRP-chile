# A/B de magnitud S125 — criterio PRE-REGISTRADO

> Escrito **antes** de crear los perfiles y **antes** de mirar ningún resultado.
> Razón: en S124 el veredicto se formó mirando los números y por eso tres
> auditorías adversariales lo tumbaron en dos puntos. El criterio se fija primero
> o no vale.
>
> Tag defensivo: `pre-s125-magnitud-ab` (A45). Confirmación explícita de Nicolás
> obtenida antes de tocar nada.

## La hipótesis

La auditoría S125 (`docs/AUDIT_S125_PROFUNDA.md` §0) encontró que la física de la
magnitud es correcta —coeficientes de Wooster, unidades y área nadir verificados
aritméticamente— y que el sub-reporte viene de **dos reducciones aplicadas aguas
abajo de la Eq. 8**, sobre la suma final del cluster:

- **R1** `cluster_focal_vrp_mw` — suma sólo los píxeles contextualmente anómalos;
  si ninguno lo es, colapsa al píxel pico. **60,9 % de los records focales
  degradados a 1 píxel.**
- **R2** `apply_single_pixel_mode` — si `vrp < 5 MW` y `n_pixels <= 3`, reemplaza
  la suma por el **máximo**. **15 % de los records con efecto real.**

Ambas nacieron como parche a un sesgo real **hacia arriba**: el fondo se estima
en un anillo regional de 5-25 km (`detection_context.py:945`) cuando la Eq. 6 de
Coppola 2016a pide el entorno **inmediato** del cluster. El parche se aplica sobre
la suma, no sobre el fondo que lo causa, así que cuando la causa no aplica sigue
mordiendo.

**Hipótesis**: si se corrige el fondo en su origen (Eq. 6 literal, la corona del
cluster contiguo — `cluster_corona_background`, ya escrita y testeada, hoy
apagada), las dos reducciones dejan de ser necesarias y la magnitud converge sin
ellas.

**Hipótesis nula que hay que poder aceptar**: el fondo por corona NO alcanza, las
reducciones están compensando otra cosa, y apagarlas sobre-estima. Si los datos
dicen esto, se reporta y no se adopta.

## Los cuatro brazos

Tres correcciones que se pueden componer exigen aislar (A66: A/B de 3+ brazos con
criterio pre-registrado; apilar dos correcciones sin aislarlas fue el error que
S102 evitó justamente así).

| brazo | R1 focal | R2 single-pixel | corona (Eq. 6) | qué contesta |
|---|---|---|---|---|
| **control** | ON | ON | OFF | el operacional de hoy, con `data_subdir` aislado |
| **A** | ON | ON | **ON** | ¿la corona sola mueve algo, con los parches puestos? |
| **B** | **OFF** | **OFF** | OFF | ¿cuánto sube sin parches, con el fondo regional? |
| **C** | **OFF** | **OFF** | **ON** | **la Eq. 6 fiel completa — el candidato** |

El brazo **B** es el control interno decisivo: si B ya entra en banda, la corona
es irrelevante y el problema era sólo el recorte. Si B se dispara por encima de
la banda y C entra, la corona es la que hace el trabajo y la conclusión física es
la que la hipótesis predice.

## Métrica

Ratio `pc.vrp_mw` nuestro / VRP de MIROVA (A10: `primary_cluster.vrp_mw`, **nunca**
`record.vrp_mw`), sobre la **intersección de pasadas** (`datetime_utc` + `sensor`),
nunca sobre conteos de series completas.

Ground truth: **CONS ∪ OCR** (A11), con el diccionario de alias **completo** —
incluyendo `"Puyehue-Cordon Caulle"` con guion y `PlanchonPeteroa` sin guion. Un
alias faltante escondió PCC entero de la tabla del veredicto en S124.

Se reporta **distribución, no mediana sola**: n, cuartiles, cuántos suben y
cuántos bajan, y los extremos. Una mediana de 0,000 puede ser "sin efecto" o
"efectos opuestos que se cancelan" (T3).

Banda de paridad para la **mediana por volcán**: **[0,7 – 1,4]** (la de la mediana,
no la de una detección suelta — el error que S124 corrigió).

## Criterios de adopción — los cuatro se cumplen o no se adopta

1. **Mejora global.** La mediana global del ratio pasa de ≈0,75 a la banda
   [0,7-1,4], y **más volcanes dentro de banda** que el control.
2. **Sin daño colateral, con el control interno que al brazo B de F70 le faltó.**
   Ningún volcán que hoy está **dentro** de banda puede salirse. Este criterio
   nació de que PCC (0,75 ✓ → 0,64) estaba escondido de la tabla por un bug de
   alias y era el único daño real. **Los 11 Tier A se listan explícitamente**,
   PCC incluido, o el veredicto no se emite.
3. **Poder estadístico.** IC bootstrap (5000, `05_poder_estadistico.py`) del brazo
   y del control **que no se solapen**. Una mediana sin intervalo no decide nada
   (T8).
4. **Sin falsos negativos nuevos.** Ninguna alerta de MIROVA que hoy
   reproducimos puede perderse. R1 y R2 son de magnitud, no de detección, así que
   en principio no deberían generar FN — pero A67 mostró que un cambio de escala
   puede apagar el Test 1 para señales borderline, así que **se verifica a nivel
   record (`triggered_test1`), no se asume**.

## Verificaciones obligatorias antes de leer nada

```bash
# (a) los flags de CADA brazo estan donde el codigo los lee — T2, trampa del nivel
VRP_PROFILE=_s125_mag_c python -c "import pipeline.profile as p; print(p.ENABLE_FOCAL_CLUSTER_MAGNITUDE, p.ENABLE_SINGLE_PIXEL_SUB_MW_MODE, p.ENABLE_LOCAL_CLUSTER_MAGNITUDE)"
```

Los tres `enable_*_magnitude` van bajo `paths:`; `enable_single_pixel_sub_mw_mode`
va en la **raíz**. Verificado en `profile.py:451,467,476,665`.

```bash
# (b) el reproceso toco la data — T4, el run puede cerrar VERDE sin tocar nada
python experiments/_s124_ndc_focus/05_verificar_reproceso.py data/<subdir>/<Vol>.json
```

## Qué NO se hace

- No se toca `pipeline/profiles/mirova_equivalent.yaml`. Los cuatro brazos usan
  `data_subdir` aislado.
- No se adopta nada en esta sesión. El flip es una decisión de Nicolás, y exige
  `superpowers-brainstorming` + R2 pixel-level (regla S33).
- No se apaga ningún flag del operacional por lo que diga esta auditoría sin que
  el A/B lo respalde.
