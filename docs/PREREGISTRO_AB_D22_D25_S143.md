# Pre-registro del A/B de D22 y D25 (VIIRS 375 m), v2

> **Estado: v2 del 2026-09-17, escrita ANTES de correr el A/B.** Corrige los 18 hallazgos del
> verificador con contexto limpio (`PREREGISTRO_AB_D22_D25_S143_VERIFICADOR.md`) sobre la v1, que
> queda en el historial de git (commit `cefeaeb00`). **Falta para poder correr**: (a) el resultado del
> probe de las 12 noches, que decide los brazos (§3); (b) dos decisiones de Nicolás (§8); (c) el sha
> del evaluador en §6 cuando se congele la corrida.
>
> Plan: `docs/superpowers/plans/2026-09-15-flags-d22-d25.md`. Criterios base: spec
> `2026-09-13-plan-definitivo-paridad-design.md` §5 y §6. Decisión vigente de cero pérdidas:
> `docs/PREREGISTRO_AB_D1_D2_S135.md`. Evaluador: `experiments/_s143_evaluador/` con sus parámetros
> congelados en `parametros.json`. Probe previo: `experiments/_s143_probe_12_noches/`.
> Ningún número de este documento está escrito a mano: salen de
> `experiments/_s143_preregistro/denominadores.json`, `experiments/_s135_ab_d1d2/resultado_final.json`
> y `experiments/_s143_preregistro/verificador/proxy_c1.py`.

## 1. El fenómeno

En un cono nevado, de noche, el cráter con un foco sub-píxel suele estar **más frío** en el infrarrojo
medio que el valle sin nieve que lo rodea. Cuatro reglas del pipeline deciden juntas si ese foco se ve
y con cuánta energía:

1. **La compuerta de temperatura (D22).** Los Tests 2 y 3 exigen `bt > t_bg + 3 K`; el paper
   (Coppola et al. 2016a, SP426.5, p. 7, renderizada y leída por el verificador) no tiene condición de
   temperatura. **Corrección respecto de la v1**: el caso A6 de Villarrica **no** lo pierde la
   compuerta sino el fondo; el catálogo ya lo había corregido en S138 (`docs/MIROVA_DIVERGENCES.md`
   D22, encabezado). La compuerta además **no está sólo en el primer pase**: la máscara contextual del
   camino D también la aplica, y esa máscara filtra el camino del Test 1 (`process_viirs.py:1063-1081`
   y `:1839-1850`).
2. **El fondo del VRP (D25).** El paper (p. 8, ec. 6, renderizada) usa la media aritmética de los
   píxeles que rodean al activo; nosotros usamos la mediana de un anillo regional. **Corrección
   respecto de la v1**: no es un solo fondo para todos. En el bloque contextual, 4 de los volcanes del
   universo (Lastarria, Planchón-Peteroa, Puyehue-Cordón Caulle, Villarrica) ya usan kernel 3x3 local
   (`volcanoes.yaml`, `local_kernel_bg`), y en el camino del Test 1 el fondo puede ser el anillo
   intermedio de 1,5 a 3 km o el global (Láscar, Lastarria, Nevados de Chillán tienen
   `lbg_global_compatible`). Lo que la ablación de D25 quita **no es lo mismo en cada volcán**, y por
   eso el informe da siempre el desglose por volcán.
3. **El segundo pase (D2)**, que corre sin detección previa y sin restringirse a la vecindad, contra
   las dos condiciones del paper (p. 7, renderizada).
4. **`keep_peak` (D19)**, que conserva el píxel más caliente del disco del Test 1 aunque el filtro
   contextual no deje nada.

## 2. Lo que ya se sabe, y de dónde viene la hipótesis

**A/B S135** (misma ventana y sensor): quitar `keep_peak` y condicionar el segundo pase juntos
elimina el 100 % del nivel base falso pero **pierde 12 noches** que MIROVA publica (Isluga 3,
Lastarria 2, Planchón-Peteroa 5, Tupungatito 2). El mecanismo investigado: el primer pase entrega 0 a
2 píxeles y el Test 1 integrado sí encuentra la señal.

**H1 (hipótesis, en muestra).** Esas pérdidas son de la compuerta y del fondo. **Se comprueba primero
con el probe barato** de `experiments/_s143_probe_12_noches/`, no con el A/B: el probe corre seis
variantes sobre esas mismas pasadas y dice cuál las recupera. Está declarado que este chequeo es **en
muestra** (H1 nació de esas 12 noches) y que la magnitud del efecto la mide el A/B, no el probe.

## 3. Brazos (se cierran con el resultado del probe)

Los seis perfiles existen y cada uno lee lo que declara (`tests/test_flags_d22_d25_perfil_s142.py`):

| brazo | D22 sin compuerta (primer pase) | D25 fondo por vecinos | D2 segundo pase condicionado | D19 `keep_peak` |
|---|---|---|---|---|
| `_s142_ab_control` | off | off | off | on |
| `_s142_ab_literal` | on | on | on | off |
| `_s142_ab_lit_sin_fondo` | on | off | on | off |
| `_s142_ab_lit_con_compuerta` | off | on | on | off |
| `_s142_ab_lit_sp_suelto` | on | on | off | off |
| `_s142_ab_lit_keep_peak` | on | on | on | on |

**Declarado (hallazgo 1 del verificador):** en los seis, la compuerta **sigue puesta** en la máscara
contextual del camino D, por decisión del dueño (plan, ajuste S142 punto 2). Por eso un resultado
negativo del brazo `literal` **no** se puede atribuir a "la compuerta no era": la compuerta de esa
ruta nunca se quitó.

**BRAZOS CERRADOS con el probe de las 12 noches (2026-09-17, `experiments/_s143_probe_12_noches/`).**
Se corren **estos seis, sin agregar ninguno**. Razón: el probe midió que D22 y D25 solos, tal como
están en el brazo `literal`, recuperan **10 de las 12 noches** que perdía S135, y ese número es firme
frente al campo de posición. Las variantes que recuperaban 11 o 12 ganaban esa diferencia por un
campo que el verificador mostró frágil (con `final_hotspot`, la posición que la regla del proyecto
manda para records `test1_roi`, las tres empatan en 10 y el propio control cae a 10), y la de 12
apaga el filtro contextual del Test 1 publicando los 12 artefactos, o sea deshace lo que S135 ganó.
Cambiar los brazos por esa diferencia **no está habilitado** por el probe
(`VERIFICADOR_POST_CORRIDA.md`). Queda anotado para después del A/B: el filtro contextual del Test 1
(S99, que no está en el paper, D23) es el frente siguiente si la paridad lo pide.

En todos: `vrp_bg_neighbor_max_half_px = 3`, conectiva `min`, corona apagada, sólo VIIRS 375,
`data_subdir` aislado.

## 4. Universo y ventana

**Ventana 2026-06-01 a 2026-08-31**, reprocesada con el código de hoy en todos los brazos; la línea
base es el **control reprocesado** (los records guardados mezclan el régimen anterior a #535, A104).
**Tramo de confirmación fuera de muestra** (hallazgo 8): 2026-09-01 a 2026-09-15, régimen posterior a
#571, que el brazo ganador también debe pasar antes de proponerse para adopción.

**Volcanes: nueve** (hallazgo 12; la v1 decía ocho y justificaba mal la selección). Denominadores de
`denominadores.json` y noches confirmadas proxy de `proxy_c1.py` (régimen mixto, sólo para dimensionar):

| volcán | estrato | noches con alerta (referencia) | noches confirmadas proxy | pasadas en negativo limpio |
|---|---|---|---|---|
| Isluga | focal | 74 | 70 | 21 |
| Láscar | focal | 61 | 55 | 50 |
| Lastarria | focal | 50 | 36 | 52 |
| Planchón-Peteroa | focal | 28 | 27 | 145 |
| Puyehue-Cordón Caulle | focal | 37 | 30 | 146 |
| Tupungatito | nevado | 29 | 26 | 122 |
| Chaitén | nevado | 14 | 12 | 221 |
| Villarrica | nevado | 11 | 9 | 218 |
| Nevados de Chillán | nevado | 5 | 3 | 198 |

**Por qué estos nueve.** Los seis de S135 permiten comparar con sus 12 pérdidas. El estrato nevado
necesitaba más de un volcán y más negativos: Chaitén entra porque tiene el mayor denominador de
negativos (221) y porque su magnitud hoy se pasa **arriba** de 1 (1,35), o sea es el contraejemplo
natural de un cambio de fondo que sube la magnitud; Villarrica aporta el lago de lava; Nevados de
Chillán aporta el caso de artefacto topográfico conocido (A69), donde quitar la compuerta es más
riesgoso. Quedan fuera Llaima (0 noches con alerta) y Copahue (3). **Nevados de Chillán entra al
criterio 1 con 3 noches**: se reporta pero no decide por sí solo.

**Estratos**: partición de `scripts/build_c2ab_windows.py:41-42`. **Declarado** (hallazgo 13): S135
usaba otra partición (`FOCALES = {Láscar, Lastarria}`), así que sus "focales 2, nevados 10" no son
comparables fila a fila con los de acá; por eso el informe da siempre el desglose por volcán.

## 5. Criterios (los aplica `experiments/_s143_evaluador/evaluar.py`, con `parametros.json` congelado)

### Control previo: cobertura pareja

Diferencia **simétrica** de claves `(datetime_utc, sensor)` entre cada brazo y el control, más
`product_version` (hallazgo 15). Volcán desparejo: se excluye del veredicto, se lista y se repite el
job.

### Control de instrumento sobre la línea base (hallazgo 16)

El control reprocesado debe publicar en negativos limpios en el rango del régimen actual (S135 dio
0,938 sobre 535 en 6 volcanes; la línea base post #571 es 0,871). Si cae fuera de 0,80 a 0,97, algo
del reproceso o del evaluador está mal y **no se interpreta** el A/B hasta explicarlo.

### Criterio 1: cero noches perdidas

- **Noche confirmada** = (volcán, fecha UTC) con alerta nocturna de MIROVA en VIIRS 375 que el control
  publica **con un objeto que pasa la cota de mismo objeto** (0,55 km, radios desde `mirova_center`).
- **Pérdida** = noche confirmada en que el brazo no publica un objeto que pase **la misma cota**
  (hallazgo 2). Se reporta también la versión sin cota en el brazo.
- **Umbral 0**, por estrato y por volcán. **Toda pérdida cuenta** (hallazgo 7): la investigación
  informa el paso siguiente, no cambia el conteo. Cualquier regla de exclusión se escribe antes y vale
  para todos los brazos.
- **Declarado** (hallazgo 9d): la pérdida se mide **sólo en VIIRS 375**, que es más estricto que el
  "cualquier sensor" del spec, porque el A/B no reprocesa MODIS ni VIIRS 750 y mezclarlos compararía
  brazos contra records de producción. La versión "cualquier sensor" se reporta como acompañante.
- **Efecto medido de la cota dura** (decisión 1 de §8): sobre los artefactos de S135, el brazo D pasa
  de 12 a 28 pérdidas y el B de 0 a 14.
- **Campo de posición de la cota** (sub-decisión 1b, **DECIDIDA por Nicolás el 2026-09-18**: manda
  `final_hotspot` cuando la fuente es `test1_roi`, centroide en el resto; congelada en
  `parametros.json`). Antes la cota usaba el centroide del `primary_cluster`, como S135. Para records cuya fuente es `test1_roi`, la regla del proyecto (S106,
  A84) dice que la posición del record es `final_hotspot`, y los dos campos separan 1,06 km de mediana
  en esos records (probe S143). **El evaluador debe reportar el criterio 1 con los dos campos**, y la
  decisión de cuál manda se toma antes de mirar el veredicto, no después.

### Criterio 2: baja la publicación en negativos limpios

- Diferencia de tasa (brazo menos control) sobre las mismas pasadas, total y por estrato.
- **Bootstrap estratificado por volcán** (hallazgo 14), remuestreando noches dentro de cada volcán,
  B = 10.000, semilla 143, y se reporta cuántas pasadas deciden el signo por estrato.
- **Cumple** si el intervalo total queda entero bajo cero y la diferencia puntual no sube en ningún
  estrato.
- **Acompañante obligatorio** (hallazgo 10): tasa de artefacto del display (`art`) y tasa previa al
  display. Si el brazo baja la publicación subiendo `art`, el veredicto lo dice: eso es el display
  escondiendo, no el algoritmo arreglando (A72).

### Criterio 3: la magnitud se acerca a 1

- Razón magnitud del operador sobre VRP de MIROVA, en pasadas `pos` publicadas **por ambos**
  (decisivo) y por cada brazo (informativo); n ≥ 30 contado sobre las `pos` del control; una fila de
  MIROVA por pasada, CONS antes que OCR (hallazgo 4).
- **Cumple** si `|mediana − 1|` no empeora en el total y no empeora más de 0,05 en ningún volcán con
  n ≥ 30.

### Criterio 4: desarrollo y prueba

No hay parámetros que ajustar, así que la ventana de junio a agosto es de prueba. **Declarado**: el
chequeo de las 12 noches es **en muestra**. El tramo 2026-09-01 a 2026-09-15 queda como confirmación
fuera de muestra. Si después de ver resultados se ajusta cualquier cosa, el brazo ajustado se juzga
sólo en ese tramo.

## 6. Regla de decisión

1. **Paridad manda**: sólo compiten los brazos que cumplen 1, 2 y 3.
2. **Fidelidad desempata**: `literal` antes que cualquier ablación; entre ablaciones no hay orden
   automático.
3. **Si ninguno cumple**, no se adopta nada y el informe atribuye cada falla al factor
   correspondiente (`literal` menos cada ablación, con su intervalo).
4. **Adopción**: decisión aparte, con tag defensivo, confirmación de Nicolás (A45) y reproceso de los
   once volcanes antes del flip.
5. El veredicto se anota el mismo día en `docs/HYPOTHESIS_LOG.md` (y se corre la suite después de
   editarlo: un test lo lee) y lo revisa un verificador con contexto limpio antes de proponer nada.

## 7. Lo que este A/B no decide

MODIS y VIIRS 750 (fases 2 y 3); la conectiva `min` contra `max` (D26); el recorte a cero del exceso
negativo, que es **confusor declarado** de la magnitud (plan, ajuste S142 punto 4, y el traspaso S143
lo pedía como brazo: **no** se incluye, para no multiplicar brazos; hallazgo 9b); el barrido de
`max_half_px` 1 contra 3 (hallazgo 9c: el parámetro existe para eso, pero se fija en 3); los dos
volcanes fuera del universo; y el camino B del Test 1 (D23), que D22 no toca.

**Declarado** (hallazgo 9a): el spec pedía correr los brazos "que el probe justifique" y el probe v2
de S141 quedó como "no justifica A/B". Este A/B no nace de aquel probe sino del frente D22/D25 del
plan S142 y del probe de las 12 noches de S143.

## 8. Decisiones de Nicolás antes de correr

| # | pregunta | estado |
|---|---|---|
| **1 y 1b** | cota de mismo objeto exigida también al brazo, y medida con `final_hotspot` en los records del Test 1 | **DECIDIDAS por Nicolás el 2026-09-18, las dos como recomendadas.** Quedan congeladas en `experiments/_s143_evaluador/parametros.json` y vigiladas por `tests/test_evaluador_ab_s143.py`. Efecto medido sobre S135: con la cota en el brazo, el brazo D pasa de 12 a 28 pérdidas (21 con la posición decidida) y el B de 0 a 14 |
| 1 (histórico) | **La cota de mismo objeto, ¿se le exige también al brazo?** Con la cota floja, un brazo "conserva" una noche publicando otro objeto en otro punto del disco. Medido: el brazo D de S135 pasa de 12 a 28 pérdidas y el B de 0 a 14 | **Sí, cota dura.** Es lo que hace honesto el criterio de cero pérdidas que aprobaste: la noche cuenta sólo si publicamos el objeto que MIROVA vio |
| 1b (histórico) | **¿Qué campo de posición usa la cota?** | recomendado y **aceptado**: `final_hotspot` cuando la fuente es `test1_roi`, centroide en el resto |
| 2 | **Escala de la corrida**: 9 volcanes × 6 brazos × 2 tramos = 108 jobs, más el tramo de confirmación | **Correr los dos tramos primero** (108 jobs, ~180 h de runner, repo público sin costo de minutos) y el de confirmación sólo para el brazo ganador |

## 9. Costo, riesgos y límites

- **108 jobs** de reproceso, un volcán y un brazo por job, `data_subdir` aislado, sin commitear; los
  JSON quedan como artefactos 14 días (referencia S135: 72 a 153 min por job).
- **Código y referencia fijos** (hallazgo 11): los dos tramos se despachan con `--ref <tag>` sobre el
  mismo tag defensivo, no sobre `main`, y el evaluador usa los sha de referencia de
  `denominadores.json`. Los tramos **no se superponen** (6 en paralelo más el cron NRT caben en el
  tope de 20 jobs).
- **Token de Earthdata**: vence el 2026-10-03; el A/B tiene que terminar antes.
- La cota de mismo objeto es **inferior** (A93): descarta con seguridad lo distinto, puede aceptar
  como igual algo que no lo es.
- El helper del fondo por vecinos no está medido en CPU sobre records eruptivos; un job lento se ve en
  el primer tramo.
- La referencia de magnitud cubre parcialmente la ventana (D2 del catálogo).
