# Probe S143: qué recupera las 12 noches que perdió el A/B S135

> Criterio escrito el 2026-09-17 **antes** de correr. Decisión de Nicolás del mismo día: opción A
> (probe barato antes del A/B de ~160 h). Scripts: `seleccionar.py` (elige pasadas desde los artefactos
> locales de S135), `probe.py` (seis variantes, sólo CI), `analizar.py` (se escribe antes de bajar los
> artefactos). Workflow: `.github/workflows/probe-s143-12-noches.yml`.

## El fenómeno y la pregunta

En un cono nevado, de noche, el cráter con un foco débil está más frío que el valle. El brazo D de
S135 (sin `keep_peak`, segundo pase condicionado) perdió 12 noches que MIROVA publica: el Test 1
integrado encontraba la señal, pero sus píxeles se intersectan con la máscara contextual, y esa
máscara exige `bt > t_bg + 3 K`. Los brazos del A/B S143 quitan la compuerta sólo en el primer pase.

**Pregunta:** sobre esas mismas pasadas, ¿qué cambio devuelve las noches, y qué cuesta en pasadas
donde MIROVA miró y no vio nada?

## Muestra (`pasadas.json`, `seleccion_resumen.json`)

61 pasadas VIIRS 375 nocturnas de Isluga, Lastarria, Planchón-Peteroa y Tupungatito, elegidas desde
los artefactos de S135 con el predicado del dashboard (node) y la referencia de
`experiments/_s143_preregistro/_dl_referencia`:

| clase | qué es | n |
|---|---|---|
| `perdida` | pasada de una de las 12 noches, con cualquier etiqueta, que A publica y D no | 41 (cubren las 12 noches) |
| `neg_artefacto` | `neg_limpio` que A publica y D no (el artefacto que D quitó), 3 por volcán, semilla 143 | 12 |
| `neg_quieta` | `neg_limpio` que ni A ni D publican, 2 por volcán, semilla 143 | 8 |

**Por qué cualquier etiqueta.** S135 confirmó cada noche con CUALQUIER publicación del control que pasara
la cota, no sólo con la pasada pareada a ±2 min. Con sólo `pos`, el ensayo del analizador (abajo) dejaba 2
noches de Planchón-Peteroa sin su pasada confirmada (cota 0,76 y 1,07 km).

**Ensayo del instrumento, antes de correr.** Con los records de S135 disfrazados de variantes (control = A,
`s135_d` = D), `analizar.py` da control 12 de 12 y `s135_d` 0 de 12, igual que `resultado_final.json`. Con los
records del brazo B (sin `keep_peak`, segundo pase suelto) da 10 de 12 con cota: S135 le contaba 0 pérdidas
sin cota en el brazo, así que 2 noches las "retenía" con otro objeto (hallazgo 2 del verificador del
pre-registro). El ensayo no dice nada de las variantes nuevas: sólo prueba el instrumento.

## Variantes (`probe.py`)

| variante | perfil | compuerta en máscara contextual | filtro contextual del Test 1 |
|---|---|---|---|
| `control` | `_s142_ab_control` | sí | sí (con `keep_peak`) |
| `s135_d` | `_s135_ab_d_ambos` | sí | sí |
| `s135_d_sin_compuerta_ctx` | `_s135_ab_d_ambos` | **no** | sí |
| `literal` | `_s142_ab_literal` | sí | sí |
| `literal_sin_compuerta_ctx` | `_s142_ab_literal` | **no** | sí |
| `literal_t1_sin_filtro` | `_s142_ab_literal` | sí | **no** (Test 1 como camino propio, D23) |

## Correcciones del verificador con contexto limpio (antes de correr)

`VERIFICADOR_PRE_CORRIDA.md` dio CORREGIR ANTES; las cinco quedaron aplicadas:

1. Quitar la compuerta de la máscara contextual puede además apagar el filtro del Test 1 (por
   `only_test1_source`, `process_viirs.py:1747-1751`), o sea recuperar la noche por el mismo mecanismo
   que `literal_t1_sin_filtro`. Ahora el probe cuenta las llamadas al filtro y sus píxeles de entrada y
   salida, y guarda `diag_n_dnti_ctx_path`, así que las dos causas se distinguen en la salida.
2. El probe llama a `store.append_record` con la escritura anulada, como en producción: el predicado
   del dashboard lee campos que sólo existen después de ese paso.
3. La matriz de volcanes sale de un input JSON, no de un `if:` por paso: un job saltado por `if`
   termina verde sin datos.
4. Timeout de 350 min (el job de Planchón-Peteroa procesa 17 pasadas por seis variantes).
5. El control del envoltorio no exige las 61 pasadas (el bloque contextual puede no correr en alguna):
   exige que haya corrido en al menos el 90 % y que nunca corra donde la variante no lo declara.

## Medidas (definidas antes de correr)

- **Publica** = predicado del dashboard (`frontend/index.html`) ejecutado con node sobre el record de la
  variante (`banco_paridad.correr_node`, mismo `inner` del HTML).
- **Recupera la noche** = alguna pasada `perdida` de esa noche publica **un objeto que pasa la cota de
  mismo objeto** de S135 contra la distancia de MIROVA de esa noche: radio del centroide del
  `primary_cluster` medido desde `mirova_center` contra cada `Distancia_km` de MIROVA de la noche,
  diferencia ≤ 0,55 km (`experiments/_s135_ab_d1d2/evaluar_ab.py`, `PRESUPUESTO_COTA_KM`). Se reporta
  también la versión sin cota.
- **Costo** = pasadas `neg_artefacto` y `neg_quieta` que la variante publica.

## Control de instrumento (si falla, el probe es INCONCLUSO y no se interpreta)

1. Las 61 pasadas procesadas con `ok` en las seis variantes (el job sale con código 2 si falta alguna).
2. `control` recupera al menos **11 de 12** noches y `s135_d` recupera como máximo **1 de 12**: el
   código de hoy reproduce la pérdida de S135.
3. En las variantes `*_sin_compuerta_ctx`, el envoltorio de la máscara se llamó al menos una vez por
   pasada; en las demás, cero.
4. `control` publica al menos 11 de las 12 `neg_artefacto` (es lo que A publicaba).

## Lectura pre-registrada

| resultado | qué se hace con el A/B |
|---|---|
| `literal` recupera ≥ 11 de 12 | los brazos actuales sí ponen a prueba H1; la v2 del pre-registro corrige el resto de los hallazgos y se corre tal cual |
| `literal` < 11 y `literal_sin_compuerta_ctx` ≥ 11 | la compuerta de la máscara es la causa; se propone a Nicolás cablear D22 también ahí (código, A45) y agregar ese brazo |
| sólo `literal_t1_sin_filtro` ≥ 11 | la causa es el filtro contextual del Test 1 (S99, no está en el paper); se propone un brazo con `enable_test1_contextual_filter: false` (sólo perfil) |
| ambas ≥ 11 | se comparan por costo en negativos; la de menor costo va al A/B y la otra como ablación |
| `literal_sin_compuerta_ctx` ≥ 11 **y** sus pasadas con filtro del Test 1 caen a ~0 | la compuerta no "arregla" el filtro: lo apaga por `only_test1_source`; entonces el frente es el filtro (S99), no la compuerta, y se propone el brazo de perfil |
| ninguna ≥ 11 | el mecanismo está en otra parte; se investiga pasada por pasada antes de cualquier A/B |

**Costo en negativos** (no decide solo, acompaña): se reporta por variante el número de `neg_artefacto`
y `neg_quieta` publicados. Una variante que recupere las noches publicando las 8 `neg_quieta` no se
propone sin discutirlo: estaría fabricando publicaciones donde hoy no hay ninguna.

**Límites.** 61 pasadas no estiman tasas: el probe responde "qué mecanismo", no "cuánto". Las 12 noches
son en muestra (nacieron de S135). Las tasas las mide el A/B.
