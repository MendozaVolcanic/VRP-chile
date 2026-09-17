# Pre-registro del A/B de D22 y D25 (VIIRS 375 m), con segundo pase condicionado y keep_peak

> **Estado: BORRADOR v1, escrito el 2026-09-17 ANTES de correr nada. NO CORRER.** El verificador con
> contexto limpio dio **CORREGIR ANTES** (18 hallazgos, `docs/PREREGISTRO_AB_D22_D25_S143_VERIFICADOR.md`).
> El de mayor gravedad (5): en los seis brazos la compuerta de temperatura sigue puesta en la máscara
> contextual que filtra el camino del Test 1 (decisión del dueño en el ajuste S142, punto 2 del plan),
> que es justo la ruta de las 12 pérdidas de S135; así H1 no se puede poner a prueba con estos brazos.
> Falta además el evaluador. Este texto se conserva como v1; la v2 va después de la decisión de Nicolás.
> Ningún número de este documento se escribió a mano: los denominadores salen de
> `experiments/_s143_preregistro/denominadores.json` y los resultados de S135 de
> `experiments/_s135_ab_d1d2/resultado_final.json`.
>
> Plan de origen: `docs/superpowers/plans/2026-09-15-flags-d22-d25.md` (Tarea 10). Criterios base:
> `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md` §5 y §6. Plantilla y
> decisión vigente de Nicolás (cero pérdidas): `docs/PREREGISTRO_AB_D1_D2_S135.md`.

## 1. El fenómeno, primero

En un cono nevado, de noche, el cráter con un foco sub-píxel suele estar **más frío** en el
infrarrojo medio que el valle sin nieve que lo rodea. Cuatro reglas del pipeline deciden, juntas,
si ese foco se ve y con cuánta energía:

1. **La compuerta de temperatura (D22).** Los Tests 2 y 3 exigen además `bt > t_bg + 3 K`. El
   paper (Coppola et al. 2016a, SP426.5, p. 7, fórmula de los Tests 2 y 3) no tiene condición de
   temperatura. En la figura A6 del propio paper, esa compuerta elimina el cráter de Villarrica
   (S137).
2. **El fondo del VRP (D25).** Usamos la mediana de un anillo regional de 5 a 25 km; el paper
   (p. 8, ec. 6) y siete textos más del grupo usan la media de los píxeles que rodean al alertado.
   Con valle tibio en el anillo, el exceso sale negativo y el cráter queda en 0,0 MW.
3. **El segundo pase (D2).** Corre aunque el primero no haya detectado nada y sin restringirse a la
   vecindad; el paper pone las dos condiciones.
4. **`keep_peak` (D19).** Conserva el píxel más caliente del disco del Test 1 aunque el filtro
   contextual no deje nada; en nevados ese píxel suele ser el borde del disco, no el cráter.

**Lo que ya se sabe (A/B S135, misma ventana y mismo sensor).** Quitar `keep_peak` y condicionar el
segundo pase juntos (brazo D de S135, el más fiel entonces) elimina el 100 % del nivel base falso,
pero **pierde 12 noches que MIROVA publica**: Isluga 2026-07-01, 07-16 y 08-19; Lastarria 07-02 y
08-28; Planchón-Peteroa 06-22, 06-26, 07-24, 08-09 y 08-24; Tupungatito 07-07 y 08-01. Las cinco
investigadas son un solo mecanismo: el primer pase entrega 0 a 2 píxeles mientras el Test 1
integrado encuentra la señal.

## 2. La hipótesis y lo que la refutaría

**H1.** Esas pérdidas son de la compuerta y del fondo, no del segundo pase ni de `keep_peak`: sin la
compuerta, el primer pase conserva los píxeles del cráter que hoy descarta por fríos, y con el fondo
de los vecinos su energía deja de recortarse a cero. Si H1 es cierta, el brazo **literal** (los
cuatro puntos del paper a la vez) recupera las 12 noches y mantiene la eliminación del artefacto.

**Predicciones escritas antes de correr**, por brazo y en la dirección del efecto:

| brazo | noches perdidas vs control | publicación en negativos limpios | magnitud (mediana por pasada) |
|---|---|---|---|
| `literal` | 0 (recupera las 12 de S135) | baja | sube hacia 1 |
| `lit_sin_fondo` | 0 | baja | igual o menor que `literal` |
| `lit_con_compuerta` | > 0 (vuelven las de S135) | baja | sube |
| `lit_sp_suelto` | 0 | baja menos que `literal` | parecida a `literal` |
| `lit_keep_peak` | 0 | baja menos que `literal` (el artefacto vuelve) | parecida a `literal` |

**H1 queda refutada** si `literal` pierde alguna de las 12 noches de S135, o si `lit_con_compuerta`
no pierde más noches que `literal`. **El riesgo que se mide a la par:** quitar la compuerta puede
dejar pasar más ruido topográfico en negativos limpios (A69), así que la publicación en negativos
limpios **puede subir** en vez de bajar; eso también se reporta como resultado, no como fallo del
instrumento.

## 3. Los brazos

Perfiles ya creados y probados (cada uno lee lo que declara: `tests/test_flags_d22_d25_perfil_s142.py`):

| brazo | D22 sin compuerta | D25 fondo por vecinos | D2 segundo pase condicionado | D19 `keep_peak` |
|---|---|---|---|---|
| `_s142_ab_control` | off | off | off | on |
| `_s142_ab_literal` | on | on | on | off |
| `_s142_ab_lit_sin_fondo` | on | off | on | off |
| `_s142_ab_lit_con_compuerta` | off | on | on | off |
| `_s142_ab_lit_sp_suelto` | on | on | off | off |
| `_s142_ab_lit_keep_peak` | on | on | on | on |

Todos: sólo VIIRS 375, `vrp_bg_neighbor_max_half_px = 3`, conectiva `min` (S136 abierta), corona
Eq. 6 apagada, `data_subdir` aislado. **Ningún parámetro se ajusta después de ver los datos.**

## 4. Universo y ventana

**Ventana: 2026-06-01 a 2026-08-31**, reprocesada con el código de hoy en los seis brazos. La línea
base es el **brazo control reprocesado**, no los records guardados: esos mezclan el régimen anterior
a #535 (A104) y compararlos introduce diferencias ajenas al A/B.

**Volcanes: ocho.** Los seis de S135 más dos nevados. Denominadores en la ventana (VIIRS 375, pasadas
nocturnas, etiquetas de `scripts/banco_paridad.py`; estratos de `scripts/build_c2ab_windows.py:41-42`):

| volcán | estrato | noches con alerta nocturna de MIROVA | pasadas en negativo limpio |
|---|---|---|---|
| Isluga | focal | 74 | 21 |
| Láscar | focal | 61 | 50 |
| Lastarria | focal | 50 | 52 |
| Planchón-Peteroa | focal | 28 | 145 |
| Puyehue-Cordón Caulle | focal | 37 | 146 |
| Tupungatito | nevado | 29 | 122 |
| Villarrica | nevado | 11 | 218 |
| Nevados de Chillán | nevado | 5 | 198 |

**Por qué estos ocho.** Los seis de S135 son los que tienen noches con alerta suficientes para el
criterio 1 y permiten comparar directamente con las 12 pérdidas. Pero con la partición del código
el estrato nevado quedaba con un solo volcán (Tupungatito), y los focales de S135 casi no tienen
negativos limpios (Isluga 21), que es justo donde se mide la sobre-publicación. Villarrica y Nevados
de Chillán suman negativos al estrato nevado, tienen alertas reales (lago de lava; actividad de 2026)
y Nevados de Chillán es el caso con artefacto topográfico conocido (A69, D11), donde quitar la
compuerta tiene más riesgo. Quedan fuera por costo Chaitén (14 noches, 221 negativos), Llaima (0
noches) y Copahue (3 noches).

## 5. Criterios pre-registrados

Unidades del objeto (A91): noche de volcán para recall, pasada para publicación y magnitud.

### Control previo: cobertura pareja (spec §5.5)

Antes de cualquier número, los seis brazos deben haber procesado **las mismas pasadas** por volcán
(clave `(datetime_utc, sensor)`). Un volcán con cobertura despareja se **excluye** del veredicto, se
lista aparte y se reprocesa ese job; no se compara con huecos (S135: un corte de NASA dejó 149
pasadas contra 203 y fabricó 4 "pérdidas").

### Criterio 1: cero noches perdidas (decisión de Nicolás del 2026-09-07)

- **Noche confirmada** = (volcán, fecha UTC) con alerta nocturna de MIROVA en VIIRS 375 (CONS u OCR)
  que el control publica en el cráter, con el filtro de mismo objeto de
  `experiments/_s135_ab_d1d2/evaluar_ab.py` (radios desde `mirova_center`, cota 0,55 km) y sin
  pasadas diurnas (`is_nighttime`).
- **Pérdida** = noche confirmada que el control publica y el brazo no, en VIIRS 375.
- **Umbral: 0**, en cada estrato y en cada volcán. Una pérdida **no descarta** el brazo: abre la
  investigación por pasada de S135 (nos falta algo de MIROVA / la fila es diurna / la entrada
  difiere). "MIROVA lo revisó a mano" no es explicación válida para el canal NRT.
- **Secundario, no decide:** la misma medida con cualquier sensor (MODIS y VIIRS 750 de producción
  cubren la noche), y las **ganancias**: noches con alerta que el brazo publica y el control no.
- **Chequeo explícito de H1:** estado de cada una de las 12 noches de S135 en cada brazo.

### Criterio 2: baja la publicación en negativos limpios (spec §5.2)

- **Negativo limpio** = etiqueta `neg_limpio` de `banco_paridad.etiquetar`; **publica** = predicado
  del dashboard ejecutado con node (`frontend/index.html`).
- **Estadístico:** diferencia de tasa (brazo menos control) sobre **las mismas pasadas**, total y por
  estrato.
- **Intervalo:** bootstrap percentil 95 % con **remuestreo por noche de volcán** (las pasadas de una
  misma noche no son independientes), B = 10.000, semilla 143.
- **Cumple** si el intervalo **total** queda entero bajo cero **y** la diferencia puntual no es
  positiva en ningún estrato.
- **Referencia de terminado, no decide:** distancia a la banda (focal 10 %, nevado 15 %).

### Criterio 3: la magnitud se acerca a 1 (spec §5.3)

- **Razón** = magnitud que ve el operador (`mirovaEqVrpDisplay`, que en VIIRS 375 usa
  `f5_core_vrp_mw`) dividida por el VRP de MIROVA, en pasadas `pos` que el brazo publica, pareadas a
  ±120 s (`banco_paridad.TOL_S`).
- **Cumple** si `|mediana_brazo − 1| ≤ |mediana_control − 1|` en el total **y** en ningún volcán con
  n ≥ 30 pares `|mediana − 1|` empeora más de 0,05 respecto del control.

### Criterio 4: desarrollo y prueba (spec §5.4, desviación declarada)

El spec pide desarrollar en enero-mayo y juzgar en junio-septiembre. Aquí **no hay nada que
desarrollar**: los flags ya existen y ningún parámetro se ajusta. Por eso toda la ventana es de
prueba. **Si después de ver resultados se ajusta cualquier cosa** (por ejemplo `max_half_px`), el
brazo ajustado se juzga en una ventana nueva sin mirar (2026-09-01 en adelante), nunca en esta.

### Criterio 5 y 6

Cobertura pareja (arriba). Resultado anotado el mismo día en `docs/HYPOTHESIS_LOG.md` y revisado por
un verificador con contexto limpio **antes** de proponer adopción.

## 6. Regla de decisión

1. **Paridad manda.** Sólo compiten los brazos que cumplen 1, 2 y 3.
2. **Fidelidad desempata:** `literal` antes que cualquier ablación; entre ablaciones no hay orden
   automático, decide Nicolás con el informe del mecanismo.
3. **Si ninguno cumple**, no se adopta nada y el informe dice qué factor explica cada falla
   (diferencia `literal` menos cada ablación, con su intervalo). Ese resultado vale igual: reordena
   el siguiente frente.
4. **La adopción** en `mirova_equivalent.yaml` es otra decisión: tag defensivo, confirmación de
   Nicolás (A45) y reproceso de los once volcanes antes del flip.

## 7. Lo que este A/B no decide

- MODIS y VIIRS 750 (fases 2 y 3 del plan).
- La conectiva `min` contra `max` de los Tests 2 y 3 (D26, pregunta al correo a Coppola).
- El recorte a cero del exceso negativo (pregunta 4 del correo).
- Los tres volcanes fuera del universo, que se miden después si algo se adopta.
- El camino B del Test 1 (NTI > K1, D23), que D22 no toca.

## 8. Costo y lo que necesita Nicolás

- **8 volcanes × 6 brazos × 2 tramos = 96 jobs** en GitHub Actions, un volcán y un brazo por job,
  cada uno escribiendo en su `data_subdir` (A47), sin commitear: los JSON quedan como artefactos 14
  días. Referencia de S135 (60 jobs): 48 y 53 horas de runner por tramo, 72 a 153 min por job. Estimado
  aquí: **~160 horas de runner**, un día de reloj por tramo con 6 en paralelo. Repo público: sin costo
  de minutos; el costo es carga sobre NASA y convivencia con el cron NRT.
- **Riesgo operacional:** ninguno sobre producción (perfiles aislados, sin commit). El token de
  Earthdata vence el 2026-10-03: el A/B debe terminar antes.
- **Pregunta a Nicolás:** ¿autorizas la escala (96 jobs) o prefieres los seis volcanes de S135 (72
  jobs), sacrificando el estrato nevado?

## 9. Límites conocidos

- La cota de mismo objeto es inferior (A93): descarta lo distinto con seguridad, puede aceptar como
  igual algo que no lo es.
- La referencia de magnitud cubre parcialmente la ventana (D2 del catálogo).
- `max_half_px = 3` es una decisión abierta (plan §5.1); no se barre aquí para no multiplicar brazos.
- El helper de vecinos no se midió en CPU sobre records eruptivos (plan §6); un job lento se ve en el
  primer tramo.
